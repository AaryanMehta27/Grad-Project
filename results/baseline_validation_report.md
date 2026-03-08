# Baseline Model Validation Report

Generated: 2026-02-26

## Dataset Summary
- Features used: 100

## Model Comparison

| Model | CV R² | Val R² | Val RMSE | Val MAE |
|-------|-------|--------|----------|---------|
| Random Forest | 0.6699±0.0358 | 0.7174 | 19.28 | 14.44 |
| XGBoost | 0.6798±0.0334 | 0.7281 | 18.91 | 13.99 |
| Ridge | 0.6021±0.0727 | 0.6936 | 20.07 | 15.49 |
| SVR (RBF) | 0.6527±0.0285 | 0.7053 | 19.68 | 13.90 |
| Neural Network | 0.5726±0.0671 | 0.5973 | 23.01 | 17.89 |
| GP Regression | -0.0839±0.0835 | -0.0000 | 36.26 | 33.88 |
| Stacked Ensemble ← BEST | 0.6794±0.0367 | 0.7344 | 18.69 | 13.55 |

## Test Set Results (Stacked Ensemble)
- **R²**: 0.6433
- **RMSE**: 21.14
- **MAE**: 15.90

## Top 20 Most Important Features

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Abilities_Fluency of Ideas | 0.2177 |
| 2 | Abilities_Originality | 0.1919 |
| 3 | Job Zone | 0.0569 |
| 4 | Skills_Instructing | 0.0478 |
| 5 | Skills_Active Learning | 0.0372 |
| 6 | Abilities_Deductive Reasoning | 0.0326 |
| 7 | Skills_Systems Analysis | 0.0227 |
| 8 | Abilities_Speech Recognition | 0.0194 |
| 9 | Skills_Critical Thinking | 0.0152 |
| 10 | Skills_Learning Strategies | 0.0139 |
| 11 | Skills_Judgment and Decision Making | 0.0135 |
| 12 | Skills_Time Management | 0.0133 |
| 13 | Skills_Management of Personnel Resources | 0.0110 |
| 14 | Abilities_Oral Comprehension | 0.0106 |
| 15 | Knowledge_Sociology and Anthropology | 0.0101 |
| 16 | Work_Activities_Assisting and Caring for Others | 0.0099 |
| 17 | Skills_Persuasion | 0.0091 |
| 18 | Skills_Systems Evaluation | 0.0086 |
| 19 | Interest_Social | 0.0079 |
| 20 | Skills_Complex Problem Solving | 0.0074 |

## Interpretation

The Stacked Ensemble model achieves R²=0.6433 on the held-out test set, 
meaning it explains 64.3% of the variance in F&O automation scores.
The top features align with theoretical expectations: occupation characteristics
related to routine/manual tasks are associated with higher AI exposure,
while social, creative, and complex cognitive tasks predict lower risk.