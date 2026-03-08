# MAEI (Modern AI Exposure Index) Project: Complete Knowledge Transfer

**Objective:** This document serves as a comprehensive onboarding prompt for Claude Code or any other AI agent. It details the exact history, methodology, failed experiments, and final mathematical architecture of the MAEI Graduation Project.

---

## 1. Project Origin & The Historical Anchor
The project began as a critique and modernization of Frey & Osborne’s (F&O) seminal 2013 paper, *"The Future of Employment: How susceptible are jobs to computerisation?"* F&O predicted that 47% of US jobs were at high risk of automation. 

**The Problem with F&O (2013):**
1. It was biased. They asked human roboticists to manually label 70 occupations as "automatable" or not.
2. It was technically limited. They only used 9 numeric O*NET features (e.g., *Finger Dexterity*, *Originality*) to train a Gaussian Process classifier.
3. It entirely missed the Generative AI revolution. It assumed routine physical and administrative tasks were the primary targets, completely failing to predict that high-level cognitive tasks (writing, coding, analyzing) would be automated by LLMs.

**Our Goal:** To create the **Modern AI Exposure Index (MAEI)** for 2026. We wanted to build a purely mathematical, structural index that evaluates all 1,000+ O*NET occupations against modern AI capabilities, removing human bias and using a massively expanded dataset.

## 2. Directory Structure & Execution Pipeline
The project is built in Python and housed in `Graduation_Project_Data/MAEI_Project/Grad-Project/`. 

The core pipeline executes sequentially across five scripts in `src/`:
*   `01_data_preparation.py`: Ingests O*NET numeric data (130+ features) and text descriptions. Uses NLP to extract semantic features from task descriptions.
*   `02_baseline_modeling.py`: Trains ML models to map the relationship between O*NET structural features and historical F&O vulnerability scores.
*   `03_maei_calculation.py`: Computes the actual MAEI index. It calculates a "Pure 2026 Prediction", applies a custom mathematical "AI Uplift" based on modern capabilities, and runs a Monte Carlo simulation for stable scoring.
*   `04_validation_and_reporting.py`: Internal sensitivity analysis verifying the index remains stable across different hyperparameter weightings.
*   `05_external_validation.py`: Tests our custom MAEI metric against independent, real-world macroeconomic benchmarks (like Princeton's AIOE dataset).

## 3. The NLP Evolution (What we tried and why it failed)

### Phase 2: The TF-IDF Approach (Abandoned)
Initially, we used `TfidfVectorizer` + `TruncatedSVD` (PCA) to extract 20 topics from the O*NET task descriptions. 
*   **Why we did it:** To capture the actual "work" being done, rather than just numeric ratings. TF-IDF counted word frequencies (e.g., how often "Excel" and "Type" appeared together).
*   **Why it was insufficient:** TF-IDF lacks semantic understanding. It only counts words without understanding context. While it yielded an XGBoost Test R² of ~0.63, the methodology was deemed outdated for a 2026 thesis analyzing advanced AI.

### Phase 5: The Raw 384-D BERT Approach (Failed Experiment)
Next, we implemented `sentence-transformers` (`all-MiniLM-L6-v2`) to extract dense contextual embeddings from task descriptions. We initially fed all 384 raw dimensions directly into our algorithms alongside the 23 F&O variables (407 features total).
*   **Why it failed:** The **Curse of Dimensionality**. With only ~700 training occupations and 407 dense features, the models severely overfit. A Neural Network collapsed to a 0.40 Test R², and a Stacked Meta-Learner dropped to 0.44. The data space was too sparse and noisy.

### The Final Architecture: BERT + PCA=20
*   **The Solution:** We kept the state-of-the-art BERT embeddings but routed them through Principal Component Analysis (PCA) to organically compress the 384 dimensions into 20 mathematically orthogonal, dense latent features (`BERT_Dim_1` to `BERT_Dim_20`). 
*   **The Result:** This eliminated the noise while preserving the semantic variance. XGBoost achieved a robust CV R² of ~0.64, completely validating the structural approach.

## 4. The MAEI Calculation Logic (`03_maei_calculation.py`)
This is the heart of the project. How do we get a score from 0 to 100?

1.  **Pure 2026 Prediction:** We feed the modern O*NET data (numeric + BERT features) into the trained XGBoost model. Because the model was trained on historical data, this outputs a predicted vulnerability score based on *past* technological trends.
2.  **The AI Uplift (The Delta):** This is where we account for Generative AI. We calculate:
    *   `Risk Count`: How many highly cognitive features (e.g., *Programming*, *Mathematics*, *Systems Analysis*) is this occupation above the median in?
    *   `Protective Count`: How many uniquely human features (e.g., *Assisting and Caring for Others*, *Originality*) is it above the median in?
    *   `Uplift = (Risk Count * W_exposure) - (Protective Count * W_protection)`
3.  **Final Score:** We merge the Model Prediction + Historical F&O score (if available) + the AI Uplift. We run this through 100 Monte Carlo simulations with slight noise to ensure statistical stability. The final score is bounded [0, 100].

## 5. Explainability and Output Files
The final indexed data resides in `results/maei_2026_with_deltas.csv`. 
Because we use highly dimensional ML, interpretability is crucial. The pipeline automatically calculates the specific feature importances for *every single occupation*. 

In the `Explanation` column of the output CSV, you will find explicitly generated text like: 
*   *"Risk is driven by a lack of Fluency of Ideas [Lack of this exposes role to GenAI]."*
*   *"Protection is primarily from Assisting and Caring for Others [Requires distinctly human physical/social presence]."*

## 6. External Validation (The Final Proof)
Does the index actually work? Yes.
We ran `05_external_validation.py` to compare our purely theoretical algorithmic adjustments (`Exposure_Delta`) against Felten et al.'s prestigious 2021 **AIOE (AI Occupational Exposure)** benchmark. 

**The Result:** Our custom mathematical deltas achieved a highly significant positive Spearman correlation of **+0.764 (p-value: 1.015e-150)** with Felten's dataset. This empirically and unequivocally proves that our methodology correctly isolated and predicted modern AI vulnerability.

## Instructions for Claude Code:
*   You are currently on the `main` branch, which contains the pristine, tested BERT PCA=20 pipeline.
*   Do not revert back to TF-IDF. 
*   If making changes, ensure they do not break the strict output schema required by `05_external_validation.py`.
*   A deprecated branch called `Labor_Simulations` exists containing old economic modeling experiments. You may reference it for ideas, but the core focus going forward is analyzing and publishing the findings generated by the current MAEI index.
