# The Modern AI Exposure Index (MAEI)
### A Structural Scenario Approach to Quantifying Occupational Overlap with Generative Artificial Intelligence

**Course:** DTSC484 — Graduation Project  
**Student:** Aaryan Mehta  
**Institution:** FLAME University, School of Computing and Data Sciences  
**Supervisor:** Professor Manoranjan Dash  
**Date:** April 2026  

---

## Project Overview

The MAEI is a reproducible, scenario-based index that quantifies the overlap between U.S. occupational tasks and current Generative AI capabilities across 1,016 occupations. It combines a machine learning baseline trained on Frey & Osborne (2017) automation scores, BERT-based NLP feature extraction from O\*NET task descriptions, literature-calibrated capability multipliers, and external validation against the Felten et al. (2021) AI Occupational Exposure index.

---

## Repository Structure

```
DTSC484-Project-MAEI/
├── src/                         # Pipeline scripts (run in order)
│   ├── utils.py                 # Shared paths and helper functions
│   ├── 01_data_preparation.py   # Load, clean, and merge O*NET + F&O data
│   ├── 02_baseline_modeling.py  # Train stacked ensemble on F&O labels
│   ├── 03_maei_calculation.py   # Apply capability multipliers, compute MAEI
│   ├── 04_validation_and_reporting.py  # Internal validation and reports
│   ├── 05_external_validation.py       # Spearman correlation with AIOE
│   ├── 06_multiplier_ablation.py       # Seven-scenario ablation study
│   ├── 07_pca_scree_plot.py            # PCA variance explained plot
│   └── 08_tree_extrapolation_check.py  # Tree saturation analysis
├── data/
│   ├── raw/
│   │   └── F&O/                 # Frey & Osborne supplementary data (included)
│   └── processed/               # Cleaned CSVs ready for modeling
├── results/                     # Output CSVs, reports, and summaries
├── figures/                     # Generated plots (PNG)
├── docs/                        # Supporting methodology notes
├── requirements.txt
└── README.md
```

> **Note:** `data/raw/db_30_1_text/` (O\*NET v30.1) and all `.pkl` files are not stored in this repository due to size. See **Data Access** below.

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/AaryanMehta27/DTSC484-Project-MAEI.git
cd DTSC484-Project-MAEI
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> Python 3.10 or 3.11 recommended. The `sentence-transformers` package will download the `all-MiniLM-L6-v2` model (~90MB) on first run automatically.

---

## Data Access

The raw O\*NET database and binary model files are hosted on Google Drive due to file size:

**[Download data.zip from Google Drive](https://drive.google.com/drive/folders/1_oYixIbVCH8ryBITfhvqoDXA3iEWmN9s?usp=sharing)**

After downloading, extract the archive so your directory structure matches:

```
data/
├── raw/
│   ├── F&O/                    (already in repo)
│   └── db_30_1_text/           ← extract here
├── processed/
│   ├── frey_osborne_fixed.csv  (already in repo)
│   ├── frey_osborne_mapped.csv (already in repo)
│   ├── onet_features_consolidated.csv (already in repo)
│   └── modeling_dataset.pkl    ← extract here
models/
└── baseline_model.pkl          ← extract here
```

The processed CSVs and figures already in the repository are sufficient to reproduce the results from `03_maei_calculation.py` onwards without re-running the full pipeline from scratch.

---

## Execution Guide

Run the scripts from the **project root directory** in numbered order:

```bash
python src/01_data_preparation.py       # Merges O*NET + F&O, generates processed files
python src/02_baseline_modeling.py      # Trains stacked ensemble, saves baseline_model.pkl
python src/03_maei_calculation.py       # Applies multipliers, outputs maei_2026_with_deltas.csv
python src/04_validation_and_reporting.py  # Internal validation, sensitivity analysis
python src/05_external_validation.py    # Validates against AIOE benchmark
python src/06_multiplier_ablation.py    # Runs 7-scenario ablation study
python src/07_pca_scree_plot.py         # Generates PCA variance plot
python src/08_tree_extrapolation_check.py  # Analyses tree saturation
```

**To reproduce results without retraining:** Start from step 3. The pre-computed `baseline_model.pkl` (from Google Drive) and processed CSVs are sufficient.

**Key output:** `results/maei_2026_with_deltas.csv` — the full MAEI scores for all 1,016 occupations.

---

## Key Results

| Metric | Value |
|--------|-------|
| Baseline model test R² | 0.6433 |
| Occupations covered | 1,016 |
| Mean exposure delta | +3.86 pts |
| Occupations with increased exposure | 87.5% |
| External validation (pure delta vs AIOE) | Spearman ρ = +0.764, p < 10⁻¹⁵⁰ |
| Ablation ρ range (7 scenarios) | 0.7636 – 0.7651 |
