# Baseline Model Validation Report

Generated: 2026-02-26

## Dataset Summary
- Features used: 100

## Model Comparison

| Model | CV R² | Val R² | Val RMSE | Val MAE |
|-------|-------|--------|----------|---------|
| Random Forest | 0.6617±0.0533 | 0.7139 | 19.40 | 14.74 |
| XGBoost ← BEST | 0.6777±0.0487 | 0.7401 | 18.49 | 13.13 |
| Ridge | 0.5981±0.0765 | 0.6844 | 20.37 | 15.42 |
| GP Regression | 0.3375±0.3836 | 0.7120 | 19.46 | 14.30 |

## Test Set Results (XGBoost)
- **R²**: 0.6347
- **RMSE**: 21.39
- **MAE**: 16.23

## Top 20 Most Important Features

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Abilities_Fluency of Ideas | 0.2458 |
| 2 | Abilities_Originality | 0.1656 |
| 3 | Skills_Instructing | 0.0702 |
| 4 | Abilities_Deductive Reasoning | 0.0351 |
| 5 | Job Zone | 0.0257 |
| 6 | Skills_Active Learning | 0.0251 |
| 7 | Knowledge_Therapy and Counseling | 0.0225 |
| 8 | Skills_Systems Analysis | 0.0217 |
| 9 | Skills_Judgment and Decision Making | 0.0162 |
| 10 | Abilities_Speech Recognition | 0.0153 |
| 11 | Skills_Learning Strategies | 0.0123 |
| 12 | Skills_Coordination | 0.0114 |
| 13 | Skills_Persuasion | 0.0103 |
| 14 | Skills_Management of Personnel Resources | 0.0099 |
| 15 | Skills_Time Management | 0.0084 |
| 16 | KW_creative_keywords | 0.0083 |
| 17 | Work_Activities_Assisting and Caring for Others | 0.0081 |
| 18 | Abilities_Problem Sensitivity | 0.0070 |
| 19 | Skills_Social Perceptiveness | 0.0068 |
| 20 | Interest_Social | 0.0066 |

## Interpretation

The XGBoost model achieves R²=0.6347 on the held-out test set, 
meaning it explains 63.5% of the variance in F&O automation scores.
The top features align with theoretical expectations: occupation characteristics
related to routine/manual tasks are associated with higher AI exposure,
while social, creative, and complex cognitive tasks predict lower risk.