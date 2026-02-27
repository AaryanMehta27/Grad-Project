"""
04_validation_and_reporting.py
Purpose:
  1. Run Sensitivity Analysis on AI parameters (W_exposure, W_protection)
  2. Generate Heatmap of exposure by SOC Major Group
  3. Generate Scatter plot comparison

Author: Aarya
Date: 2026-02-27
"""

import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    setup_logging, DATA_PROCESSED, MODELS_DIR, RESULTS_DIR, FIGURES_DIR
)

import importlib
maei_calc = importlib.import_module("03_maei_calculation")
calculate_maei = maei_calc.calculate_maei

logger = setup_logging("04_validation_and_reporting")

# Map 2-digit SOC to human readable cluster (simplified)
SOC_GROUP_MAP = {
    '11': 'Management', '13': 'Business/Financial', '15': 'Computer/Math',
    '17': 'Architecture/Eng', '19': 'Life/Physical/Soc Sci', '21': 'Community/Social',
    '23': 'Legal', '25': 'Education', '27': 'Arts/Design/Media',
    '29': 'Healthcare Practitioners', '31': 'Healthcare Support', '33': 'Protective Service',
    '35': 'Food Prep/Serving', '37': 'Building/Grounds Cleaning', '39': 'Personal Care',
    '41': 'Sales', '43': 'Office/Admin Support', '45': 'Farming/Fishing/Forestry',
    '47': 'Construction/Extraction', '49': 'Installation/Maintenance', '51': 'Production',
    '53': 'Transportation/Material Moving', '55': 'Military'
}

def run_sensitivity_analysis(full_dataset, model_artifact):
    logger.info("=" * 70)
    logger.info("SENSITIVITY ANALYSIS")
    logger.info("=" * 70)
    
    configs = [
        (6, 2),
        (8, 3),
        (10, 3), # Base
        (12, 4),
        (14, 5)
    ]
    
    sensitivity_results = []
    
    for w, p in configs:
        logger.info(f"Testing Config: W={w}, P={p}")
        res_df = calculate_maei(full_dataset, model_artifact, W_exposure=float(w), W_protection=float(p))
        
        # Only use valid scored ones
        scored = res_df[res_df['Score_Source'] != 'insufficient_data']
        
        mean_delta = scored['Exposure_Delta'].mean()
        perc_increase = (scored['Exposure_Delta'] > 0).mean() * 100
        
        sensitivity_results.append({
            'W_exposure': w,
            'W_protection': p,
            'Mean_Delta': mean_delta,
            'Percent_Increase': perc_increase
        })
        
    sens_df = pd.DataFrame(sensitivity_results)
    sens_df.to_csv(RESULTS_DIR / 'sensitivity_analysis.csv', index=False)
    
    logger.info("Sensitivity Analysis Complete:")
    logger.info("\n" + sens_df.to_string())
    
def generate_heatmap(results_df):
    """Generate heatmap of exposure by major SOC group"""
    logger.info("Generating SOC Group Heatmap...")
    scored = results_df[results_df['Score_Source'] != 'insufficient_data'].copy()
    
    scored['SOC_Name'] = scored['SOC_Major_Group'].map(SOC_GROUP_MAP).fillna('Unknown')
    
    heatmap_data = scored.groupby('SOC_Name')[['Hist_Ref_2013', 'MAEI_2026_Score', 'Exposure_Delta']].mean().sort_values('Exposure_Delta', ascending=False)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=True, cmap="coolwarm", center=0, fmt=".1f")
    plt.title('Average AI Exposure by Occupation Family')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'exposure_heatmap.png', dpi=150)
    plt.close()
    
def generate_scatter(results_df):
    logger.info("Generating Scatter Plot...")
    scored = results_df[results_df['Score_Source'] != 'insufficient_data']
    
    plt.figure(figsize=(10, 8))
    plt.scatter(scored['Hist_Ref_2013'], scored['MAEI_2026_Score'], alpha=0.5, c=scored['Exposure_Delta'], cmap="coolwarm")
    plt.plot([0, 100], [0, 100], 'k--', zorder=3)
    plt.colorbar(label='Exposure Delta')
    plt.title("Historical Reference (2013) vs MAEI (2026)")
    plt.xlabel("Historical Reference 2013")
    plt.ylabel("Modern AI Exposure Index (MAEI 2026)")
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'scatter_hist_vs_maei.png', dpi=150)
    plt.close()

def generate_ablation_plot(results_df):
    logger.info("Generating Ablation Study Plot...")
    scored = results_df[results_df['Score_Source'] != 'insufficient_data']
    
    plt.figure(figsize=(10, 8))
    plt.scatter(scored['MAEI_Pure_2026'], scored['MAEI_2026_Score'], alpha=0.5, c=scored['Anchor_Bias'], cmap="coolwarm")
    plt.plot([0, 100], [0, 100], 'k--', zorder=3, label="Perfect Alignment")
    plt.colorbar(label='Anchor Bias (Anchored - Pure)')
    plt.title("Ablation Study: Pure 2026 Model vs. F&O 2013 Anchored")
    plt.xlabel("Pure MAEI 2026 (No F&O Anchor)")
    plt.ylabel("Anchored MAEI 2026")
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'ablation_pure_vs_anchored.png', dpi=150)
    plt.close()

if __name__ == "__main__":
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    data = joblib.load(DATA_PROCESSED / "modeling_dataset.pkl")
    full_dataset = data['full_dataset']
    model_artifact = joblib.load(MODELS_DIR / 'baseline_model.pkl')
    
    # Apply SVD compression if the model was trained with it
    svd = model_artifact.get('svd', None)
    if svd is not None:
        tfidf_cols = [c for c in full_dataset.columns if c.startswith('TFIDF_')]
        if len(tfidf_cols) > 0:
            NLP_TOPIC_NAMES = [
                'NLP_Topic_Equipment_Materials',
                'NLP_Topic_Tools_Machines',
                'NLP_Topic_Medical_Patients',
                'NLP_Topic_Education_Students',
                'NLP_Topic_Customer_Service_Food',
                'NLP_Topic_Maintenance_Repair',
                'NLP_Topic_Production_Manufacturing',
                'NLP_Topic_Sales_Systems',
                'NLP_Topic_Food_Environmental',
                'NLP_Topic_Data_Software'
            ]
            topic_names = NLP_TOPIC_NAMES[:svd.n_components]
            topics = pd.DataFrame(
                svd.transform(full_dataset[tfidf_cols].fillna(0)),
                index=full_dataset.index, columns=topic_names
            )
            full_dataset = full_dataset.drop(columns=tfidf_cols)
            for col in topic_names:
                full_dataset[col] = topics[col]
                
    run_sensitivity_analysis(full_dataset, model_artifact)
    
    # Run with standard W=10, P=3 to generate plots
    res_df = calculate_maei(full_dataset, model_artifact, 10.0, 3.0)
    generate_heatmap(res_df)
    generate_scatter(res_df)
    generate_ablation_plot(res_df)
    
    logger.info("Validation & Reporting Complete.")
