"""
06_multiplier_ablation.py
=========================
Multiplier Ablation Study: Prove AIOE correlation is robust under
drastically different multiplier regimes — not just ±10% Monte Carlo noise.

Tests 7 scenarios ranging from halved to doubled to random multipliers.
If the Spearman correlation with Felten's AIOE remains significant across
all regimes, the MAEI's relative ordering is structurally robust.

Author: Aarya
Date:   2026-03-08
"""
import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.stats as stats
import joblib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import setup_logging, DATA_PROCESSED, MODELS_DIR, RESULTS_DIR, FIGURES_DIR

logger = setup_logging("06_multiplier_ablation")

# ---------------------------------------------------------------------------
# Import shared constants from production pipeline
# ---------------------------------------------------------------------------
import importlib
maei_calc = importlib.import_module("03_maei_calculation")
FEATURE_ADJUSTMENTS_2026 = maei_calc.FEATURE_ADJUSTMENTS_2026
detect_no_data_occupations = maei_calc.detect_no_data_occupations

# Protective feature set (must match 03_maei_calculation.py lines 384-411)
PROTECTIVE_FEATURES = {
    'Abilities_Originality', 'Abilities_Fluency of Ideas',
    'Work_Activities_Thinking Creatively',
    'KW_creative_keywords', 'KW_creative_keywords_norm',
    'Skills_Social Perceptiveness', 'Skills_Negotiation',
    'Skills_Persuasion', 'Skills_Instructing', 'Skills_Coordination',
    'Skills_Service Orientation', 'Knowledge_Therapy and Counseling',
    'Knowledge_Psychology', 'Knowledge_Sociology and Anthropology',
    'KW_social_keywords', 'KW_social_keywords_norm',
    'Work_Activities_Assisting and Caring for Others',
    'Work_Activities_Establishing and Maintaining Interpersonal Relationships',
    'Work_Activities_Resolving Conflicts and Negotiating with Others',
    'Work_Activities_Coaching and Developing Others',
    'Work_Activities_Training and Teaching Others',
    'Work_Activities_Performing for or Working Directly with the Public',
    'Work_Activities_Guiding, Directing, and Motivating Subordinates',
    'Abilities_Manual Dexterity', 'Abilities_Finger Dexterity',
    'Abilities_Arm-Hand Steadiness', 'Abilities_Control Precision',
    'Abilities_Spatial Orientation', 'Abilities_Far Vision',
    'Abilities_Depth Perception',
    'KW_physical_keywords', 'KW_physical_keywords_norm',
    'Work_Activities_Handling and Moving Objects',
    'Work_Activities_Performing General Physical Activities',
    'Work_Activities_Operating Vehicles, Mechanized Devices, or Equipment',
    'Interest_Social', 'Interest_Artistic',
}
RISK_FEATURES = set(FEATURE_ADJUSTMENTS_2026.keys()) - PROTECTIVE_FEATURES


# ---------------------------------------------------------------------------
# Scenario multiplier generator
# ---------------------------------------------------------------------------
def build_scenario_adjustments(scenario_name):
    """Return a modified multiplier dict for the given scenario."""
    base = dict(FEATURE_ADJUSTMENTS_2026)

    if scenario_name == 'baseline':
        return base

    elif scenario_name == 'halved_risk':
        # Halve the distance from 1.0: 3.5 → 2.25
        return {k: (1 + (v - 1) * 0.5 if k in RISK_FEATURES else v)
                for k, v in base.items()}

    elif scenario_name == 'doubled_risk':
        # Double the distance from 1.0: 3.5 → 6.0
        return {k: (1 + (v - 1) * 2.0 if k in RISK_FEATURES else v)
                for k, v in base.items()}

    elif scenario_name == 'uniform_risk':
        # All risk multipliers set to a flat 2.0
        return {k: (2.0 if k in RISK_FEATURES else v)
                for k, v in base.items()}

    elif scenario_name == 'no_protective':
        # Remove all protective multipliers (set to 1.0)
        return {k: (1.0 if k in PROTECTIVE_FEATURES else v)
                for k, v in base.items()}

    elif scenario_name == 'doubled_protective':
        # Double the protective distance from 1.0: 1.10 → 1.20
        return {k: (1 + (v - 1) * 2.0 if k in PROTECTIVE_FEATURES else v)
                for k, v in base.items()}

    elif scenario_name == 'random_multipliers':
        rng = np.random.RandomState(42)
        return {k: (rng.uniform(1.5, 4.0) if k in RISK_FEATURES
                     else rng.uniform(1.0, 1.15))
                for k in base}

    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")


# ---------------------------------------------------------------------------
# Apply adjustments with custom multipliers (same gating as production)
# ---------------------------------------------------------------------------
def apply_adjustments_scenario(features_df, selected_features, adjustments):
    """
    Apply feature adjustments using the SAME percentile gating logic
    as 03_maei_calculation.py: 30th percentile for risk, 85th for protective.
    """
    adjusted = features_df.copy()
    pctl_risk = features_df.quantile(0.30)
    pctl_protect = features_df.quantile(0.85)

    for feature, multiplier in adjustments.items():
        if feature in adjusted.columns and feature in selected_features:
            if feature in PROTECTIVE_FEATURES:
                mask = features_df[feature] >= pctl_protect[feature]
            else:
                mask = features_df[feature] >= pctl_risk[feature]
            adjusted.loc[mask, feature] = (
                features_df.loc[mask, feature] * multiplier
            )
    return adjusted


# ---------------------------------------------------------------------------
# Run a single ablation scenario end-to-end
# ---------------------------------------------------------------------------
def run_scenario(scenario_name, X_original, selected_features, model,
                 full_dataset, no_data_codes,
                 W_exposure=10.0, W_protection=3.0):
    """
    Compute per-occupation Exposure_Delta for a given multiplier scenario.
    Mirrors the logic in 03_maei_calculation.py calculate_maei().
    """
    adjustments = build_scenario_adjustments(scenario_name)

    X_adjusted = apply_adjustments_scenario(
        X_original, selected_features, adjustments
    )

    # Predictions — unscaled, matching production pipeline (line 362)
    pred_baseline = np.clip(model.predict(X_original), 0, 100)
    pred_2026 = np.clip(model.predict(X_adjusted), 0, 100)

    # Uplift — identical formula to 03_maei_calculation.py lines 413-437
    medians = X_original.median()
    risk_count = pd.Series(0.0, index=full_dataset.index)
    protect_count = pd.Series(0.0, index=full_dataset.index)
    risk_total, protect_total = 0, 0

    for f in RISK_FEATURES:
        if f in X_original.columns and f in selected_features:
            risk_count += (X_original[f] >= medians[f]).astype(float)
            risk_total += 1
    for f in PROTECTIVE_FEATURES:
        if f in X_original.columns and f in selected_features:
            protect_count += (X_original[f] >= medians[f]).astype(float)
            protect_total += 1

    risk_frac = risk_count / max(risk_total, 1)
    protect_frac = protect_count / max(protect_total, 1)
    broad_exposure_adj = risk_frac * W_exposure - protect_frac * W_protection

    model_delta = (pred_2026 - pred_baseline) + broad_exposure_adj.values

    # Build results (scored occupations only)
    results = []
    for i, (onet_code, row) in enumerate(full_dataset.iterrows()):
        if onet_code in no_data_codes:
            continue
        results.append({
            'ONET_SOC_Code': onet_code,
            'Exposure_Delta': float(model_delta[i]),
        })

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Load AIOE benchmark
# ---------------------------------------------------------------------------
def load_aioe():
    """Download and prepare Felten AIOE data for merging."""
    aioe_url = "https://github.com/AIOE-Data/AIOE/raw/main/AIOE_DataAppendix.xlsx"
    logger.info(f"  Downloading AIOE from {aioe_url}...")

    try:
        aioe_df = pd.read_excel(aioe_url, sheet_name='Appendix A')
    except Exception as e:
        logger.warning(f"  Primary URL failed ({e}), trying alternative...")
        aioe_url_alt = "https://raw.githubusercontent.com/AIOE-Data/AIOE/main/AIOE_DataAppendix.xlsx"
        aioe_df = pd.read_excel(aioe_url_alt, sheet_name='Appendix A')

    # Find SOC code column
    soc_col = None
    for col in aioe_df.columns:
        if 'SOC' in str(col).upper() or 'CODE' in str(col).upper():
            soc_col = col
            break
    if soc_col is None:
        soc_col = aioe_df.columns[0]

    aioe_df['Base_SOC'] = aioe_df[soc_col].astype(str).str.strip()

    # Find AIOE score column
    score_col = None
    for col in aioe_df.columns:
        if 'AIOE' in str(col).upper() and 'RANK' not in str(col).upper():
            score_col = col
            break
    if score_col is None:
        raise ValueError("Cannot find AIOE score column in dataset")

    logger.info(f"  AIOE loaded: {len(aioe_df)} occupations, score column = '{score_col}'")
    return aioe_df, score_col


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 70)
    logger.info("MULTIPLIER ABLATION STUDY")
    logger.info("Testing AIOE correlation robustness across 7 multiplier regimes")
    logger.info("=" * 70)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Load artifacts
    logger.info("\nLoading model artifact and dataset...")
    data = joblib.load(DATA_PROCESSED / "modeling_dataset.pkl")
    full_dataset = data['full_dataset']
    model_artifact = joblib.load(MODELS_DIR / 'baseline_model.pkl')
    model = model_artifact['model']
    selected_features = model_artifact['selected_features']

    X_original = full_dataset[selected_features].fillna(0)
    no_data_codes = detect_no_data_occupations(full_dataset, selected_features)
    logger.info(f"  Dataset: {len(full_dataset)} occupations, {len(selected_features)} features")
    logger.info(f"  No-data occupations excluded: {len(no_data_codes)}")

    # Load AIOE
    aioe_df, aioe_score_col = load_aioe()

    # Define scenarios
    scenarios = [
        ('baseline',          'Baseline (Current)'),
        ('halved_risk',       'Halved Risk Multipliers'),
        ('doubled_risk',      'Doubled Risk Multipliers'),
        ('uniform_risk',      'Uniform Risk (all = 2.0)'),
        ('no_protective',     'No Protective Multipliers'),
        ('doubled_protective','Doubled Protective'),
        ('random_multipliers','Random (seed=42)'),
    ]

    ablation_results = []

    for scenario_key, scenario_label in scenarios:
        logger.info(f"\n{'─' * 50}")
        logger.info(f"  Scenario: {scenario_label}")
        logger.info(f"{'─' * 50}")

        scenario_df = run_scenario(
            scenario_key, X_original, selected_features,
            model, full_dataset, no_data_codes
        )

        # Merge with AIOE
        scenario_df['Base_SOC'] = scenario_df['ONET_SOC_Code'].apply(
            lambda x: str(x).split('.')[0]
        )
        merged = pd.merge(scenario_df, aioe_df, on='Base_SOC', how='inner')
        merged = merged.dropna(subset=['Exposure_Delta', aioe_score_col])

        rho, p_val = stats.spearmanr(
            merged['Exposure_Delta'], merged[aioe_score_col]
        )

        mean_delta = scenario_df['Exposure_Delta'].mean()
        pct_increased = (scenario_df['Exposure_Delta'] > 0).mean() * 100

        ablation_results.append({
            'Scenario': scenario_label,
            'Spearman_Rho': round(rho, 4),
            'P_Value': f"{p_val:.2e}",
            'N_Overlapping': len(merged),
            'Mean_Delta': round(mean_delta, 2),
            'Pct_Increased': round(pct_increased, 1),
        })

        logger.info(f"  Spearman rho = {rho:.4f} (p = {p_val:.2e})")
        logger.info(f"  Mean delta   = {mean_delta:+.2f}")
        logger.info(f"  % increased  = {pct_increased:.1f}%")
        logger.info(f"  N overlapping= {len(merged)}")

    # -----------------------------------------------------------------------
    # Save results table
    # -----------------------------------------------------------------------
    results_table = pd.DataFrame(ablation_results)
    csv_path = RESULTS_DIR / 'multiplier_ablation_results.csv'
    results_table.to_csv(csv_path, index=False)
    logger.info(f"\nSaved: {csv_path}")

    # -----------------------------------------------------------------------
    # Generate figure: horizontal bar chart of AIOE correlations
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 6))

    labels = results_table['Scenario'].tolist()
    rhos = results_table['Spearman_Rho'].astype(float).tolist()

    colors = ['#2ecc71' if r > 0.5 else '#f39c12' if r > 0.2 else '#e74c3c'
              for r in rhos]

    y_pos = range(len(labels))
    bars = ax.barh(y_pos, rhos, color=colors, edgecolor='black', linewidth=0.5,
                   height=0.6)

    # Annotate each bar
    for i, (rho_val, p_str) in enumerate(zip(rhos, results_table['P_Value'])):
        p_float = float(p_str)
        sig = '***' if p_float < 0.001 else '**' if p_float < 0.01 else '*' if p_float < 0.05 else 'n.s.'
        offset = 0.015 if rho_val >= 0 else -0.08
        ax.text(rho_val + offset, i, f'ρ = {rho_val:.3f} {sig}',
                va='center', fontsize=9, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Spearman Correlation with AIOE (Exposure Delta)', fontsize=11)
    ax.set_title('Multiplier Ablation Study:\n'
                 'AIOE Correlation Robustness Across 7 Multiplier Regimes',
                 fontsize=13, fontweight='bold')
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlim(-0.1, max(rhos) + 0.15)
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    fig_path = FIGURES_DIR / 'multiplier_ablation_aioe.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {fig_path}")

    # -----------------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info("ABLATION STUDY SUMMARY")
    logger.info("=" * 70)
    print("\n" + results_table.to_string(index=False))

    # Interpretation
    min_rho = min(rhos)
    all_significant = all(float(p) < 0.001 for p in results_table['P_Value'])
    logger.info(f"\n  Minimum rho across all scenarios: {min_rho:.4f}")
    logger.info(f"  All scenarios significant (p < 0.001): {all_significant}")

    if min_rho > 0.3 and all_significant:
        logger.info("  CONCLUSION: The MAEI's relative ordering of occupations is")
        logger.info("  ROBUST to multiplier specification. The AIOE correlation is")
        logger.info("  structurally inherent, not an artifact of calibration.")
    else:
        logger.info("  WARNING: Some scenarios show weak or non-significant correlations.")
        logger.info("  Further investigation required.")

    logger.info("\n" + "=" * 70)
    logger.info("MULTIPLIER ABLATION STUDY COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
