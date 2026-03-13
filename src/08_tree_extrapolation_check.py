"""
08_tree_extrapolation_check.py
===============================
Tree Extrapolation Analysis: Check whether tree-based models (XGBoost, RF)
saturate on extreme multiplied feature values compared to linear models (Ridge).

Compares per-occupation prediction deltas across model architectures. If tree
models compress deltas (slope < 1.0 vs. Ridge), this reveals a structural
limitation that should be acknowledged in the dissertation.

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

logger = setup_logging("08_tree_extrapolation_check")

# Import shared adjustment logic from production pipeline
import importlib
maei_calc = importlib.import_module("03_maei_calculation")
apply_adjustments = maei_calc.apply_adjustments
detect_no_data_occupations = maei_calc.detect_no_data_occupations

# Models that were trained on scaled input (from 02_baseline_modeling.py)
SCALED_MODELS = {'Ridge', 'SVR (RBF)', 'Neural Network', 'GP Regression'}
# Models trained on unscaled input
UNSCALED_MODELS = {'Random Forest', 'XGBoost'}
# Stacked Ensemble: production code passes unscaled (03_maei_calculation.py line 362)
# even though it was trained on scaled. We match production behavior.


def compute_deltas(model_name, model, X_orig, X_adj, scaler):
    """
    Compute per-occupation delta (pred_adjusted - pred_original).
    Applies scaling only for models that were trained on scaled data.
    """
    if model_name in SCALED_MODELS:
        orig_input = scaler.transform(X_orig)
        adj_input = scaler.transform(X_adj)
    else:
        # XGBoost, RF, and Stacked Ensemble: unscaled (matching production)
        orig_input = X_orig.values if hasattr(X_orig, 'values') else X_orig
        adj_input = X_adj.values if hasattr(X_adj, 'values') else X_adj

    pred_orig = model.predict(orig_input)
    pred_adj = model.predict(adj_input)

    return pred_adj - pred_orig


def main():
    logger.info("=" * 70)
    logger.info("TREE EXTRAPOLATION ANALYSIS")
    logger.info("Do tree-based models saturate on extreme multiplier values?")
    logger.info("=" * 70)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load artifacts
    # ------------------------------------------------------------------
    logger.info("\nLoading model artifact and dataset...")
    data = joblib.load(DATA_PROCESSED / "modeling_dataset.pkl")
    full_dataset = data['full_dataset']
    model_artifact = joblib.load(MODELS_DIR / 'baseline_model.pkl')

    selected_features = model_artifact['selected_features']
    scaler = model_artifact['scaler']
    all_models = model_artifact['all_models']

    logger.info(f"  Available models: {list(all_models.keys())}")

    # ------------------------------------------------------------------
    # Prepare feature matrices
    # ------------------------------------------------------------------
    X_original = full_dataset[selected_features].fillna(0)
    X_adjusted = apply_adjustments(X_original, selected_features)

    # Filter out no-data occupations
    no_data_codes = detect_no_data_occupations(full_dataset, selected_features)
    valid_mask = ~full_dataset.index.isin(no_data_codes)

    X_orig_valid = X_original[valid_mask]
    X_adj_valid = X_adjusted[valid_mask]
    valid_titles = full_dataset.loc[valid_mask, 'ONET_Title'] if 'ONET_Title' in full_dataset.columns else pd.Series(full_dataset.index[valid_mask])

    logger.info(f"  Valid occupations: {valid_mask.sum()} / {len(full_dataset)}")

    # ------------------------------------------------------------------
    # Compute deltas for each model architecture
    # ------------------------------------------------------------------
    models_to_analyze = ['Ridge', 'XGBoost', 'Random Forest', 'Stacked Ensemble']
    if 'SVR (RBF)' in all_models:
        models_to_analyze.append('SVR (RBF)')

    deltas = {}
    for model_name in models_to_analyze:
        if model_name not in all_models:
            logger.warning(f"  Skipping '{model_name}' — not found in all_models")
            continue

        model = all_models[model_name]
        try:
            delta = compute_deltas(
                model_name, model, X_orig_valid, X_adj_valid, scaler
            )
            deltas[model_name] = delta
            logger.info(f"  {model_name:20s}: mean Δ = {delta.mean():+6.2f}, "
                         f"std = {delta.std():5.2f}, "
                         f"range = [{delta.min():.1f}, {delta.max():.1f}]")
        except Exception as e:
            logger.warning(f"  {model_name}: prediction failed — {e}")

    if 'Ridge' not in deltas:
        logger.error("  Ridge model required as linear reference. Aborting.")
        return

    # ------------------------------------------------------------------
    # Correlation analysis: Ridge as linear reference
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 50)
    logger.info("DELTA CORRELATIONS (Ridge = linear reference)")
    logger.info("=" * 50)

    ridge_d = deltas['Ridge']
    correlation_results = []

    for model_name, model_d in deltas.items():
        if model_name == 'Ridge':
            continue
        pearson_r, pearson_p = stats.pearsonr(ridge_d, model_d)
        spearman_r, spearman_p = stats.spearmanr(ridge_d, model_d)

        # Best-fit slope
        slope = np.polyfit(ridge_d, model_d, 1)[0]

        correlation_results.append({
            'Model': model_name,
            'Pearson_r': round(pearson_r, 4),
            'Spearman_rho': round(spearman_r, 4),
            'Best_Fit_Slope': round(slope, 4),
        })

        logger.info(f"  Ridge vs {model_name:20s}: "
                     f"Pearson r = {pearson_r:.4f}, "
                     f"Spearman ρ = {spearman_r:.4f}, "
                     f"Slope = {slope:.3f}")

    # ------------------------------------------------------------------
    # Top 10 occupations with largest discrepancy
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 50)
    logger.info("TOP 10: LARGEST RIDGE vs XGBOOST DELTA DISCREPANCY")
    logger.info("=" * 50)

    delta_df = pd.DataFrame(deltas, index=X_orig_valid.index)
    delta_df['Title'] = valid_titles.values

    if 'XGBoost' in deltas:
        delta_df['Ridge_XGB_Gap'] = np.abs(deltas['Ridge'] - deltas['XGBoost'])
        top_disc = delta_df.nlargest(10, 'Ridge_XGB_Gap')
        for _, row in top_disc.iterrows():
            title = str(row['Title'])[:45]
            logger.info(f"  {title:45s} | Ridge: {row['Ridge']:+6.1f} | "
                         f"XGB: {row['XGBoost']:+6.1f} | "
                         f"Gap: {row['Ridge_XGB_Gap']:.1f}")

    # ------------------------------------------------------------------
    # Delta range compression (saturation diagnostic)
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 50)
    logger.info("DELTA RANGE COMPRESSION (Saturation Check)")
    logger.info("=" * 50)
    for model_name, model_d in deltas.items():
        d_range = model_d.max() - model_d.min()
        iqr = np.percentile(model_d, 75) - np.percentile(model_d, 25)
        logger.info(f"  {model_name:20s}: range = {d_range:6.1f}, IQR = {iqr:5.2f}")

    # ------------------------------------------------------------------
    # Generate 2-panel scatter figure
    # ------------------------------------------------------------------
    logger.info("\nGenerating scatter plot...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    def plot_panel(ax, x_deltas, y_deltas, x_label, y_label, title_suffix, color):
        r, _ = stats.pearsonr(x_deltas, y_deltas)
        slope, intercept = np.polyfit(x_deltas, y_deltas, 1)

        ax.scatter(x_deltas, y_deltas, alpha=0.4, s=12, c=color, edgecolors='none')

        # Identity line
        lims = [min(x_deltas.min(), y_deltas.min()) - 3,
                max(x_deltas.max(), y_deltas.max()) + 3]
        ax.plot(lims, lims, 'r--', linewidth=1.5, alpha=0.6, label='y = x (perfect agreement)')

        # Best-fit line
        x_fit = np.linspace(lims[0], lims[1], 100)
        ax.plot(x_fit, slope * x_fit + intercept, 'k-', linewidth=1.2, alpha=0.7,
                label=f'Best fit (slope = {slope:.2f})')

        ax.set_xlabel(x_label, fontsize=11)
        ax.set_ylabel(y_label, fontsize=11)
        ax.set_title(f'{title_suffix}\n(Pearson r = {r:.3f}, slope = {slope:.2f})',
                     fontsize=12)
        ax.legend(fontsize=9, loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(lims)
        ax.set_ylim(lims)

    # Panel A: Ridge vs XGBoost
    if 'XGBoost' in deltas:
        plot_panel(axes[0], deltas['Ridge'], deltas['XGBoost'],
                   'Ridge Delta (Linear)', 'XGBoost Delta (Tree)',
                   'A. Ridge vs XGBoost', 'steelblue')

    # Panel B: Ridge vs Stacked Ensemble
    if 'Stacked Ensemble' in deltas:
        plot_panel(axes[1], deltas['Ridge'], deltas['Stacked Ensemble'],
                   'Ridge Delta (Linear)', 'Stacked Ensemble Delta',
                   'B. Ridge vs Stacked Ensemble (Production)', 'teal')

    plt.suptitle('Tree Extrapolation Check: Do Tree Models Saturate\n'
                 'on Extreme Feature Multiplier Values?',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig_path = FIGURES_DIR / 'tree_extrapolation_comparison.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"  Saved: {fig_path}")

    # ------------------------------------------------------------------
    # Save text report
    # ------------------------------------------------------------------
    report_lines = [
        "TREE EXTRAPOLATION ANALYSIS REPORT",
        "=" * 55,
        "",
        "PURPOSE: Check whether tree-based models (XGBoost, RF)",
        "saturate on extreme feature multiplier values compared",
        "to the linear Ridge model.",
        "",
        "DELTA STATISTICS:",
    ]
    for model_name, model_d in deltas.items():
        report_lines.append(
            f"  {model_name:20s}: mean={model_d.mean():+.2f}, "
            f"std={model_d.std():.2f}, "
            f"range=[{model_d.min():.1f}, {model_d.max():.1f}]"
        )

    report_lines.extend(["", "CORRELATIONS WITH RIDGE:"])
    for cr in correlation_results:
        report_lines.append(
            f"  vs {cr['Model']:20s}: Pearson r = {cr['Pearson_r']:.4f}, "
            f"Slope = {cr['Best_Fit_Slope']:.4f}"
        )

    report_lines.extend([
        "",
        "INTERPRETATION:",
        "  - Slope < 1.0: tree models compress deltas (saturation effect)",
        "  - Slope ~ 1.0: tree models agree with linear extrapolation",
        "  - Slope > 1.0: tree models amplify deltas (unlikely)",
        "  - High correlation (r > 0.8) with slope < 1.0 means tree models",
        "    preserve relative ordering but are conservative in magnitude.",
        "  - This is acceptable because the MAEI is validated on RANK",
        "    correlation (Spearman), not absolute score magnitude.",
    ])

    report_path = RESULTS_DIR / 'tree_extrapolation_report.txt'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"  Saved: {report_path}")

    logger.info("\n" + "=" * 70)
    logger.info("TREE EXTRAPOLATION ANALYSIS COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
