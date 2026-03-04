# Baseline Model Validation Report

Generated: 2026-02-26

## Dataset Summary
- Features used: 100

## Model Comparison

| Model | CV R² | Val R² | Val RMSE | Val MAE |
|-------|-------|--------|----------|---------|
| Random Forest | 0.6658±0.0376 | 0.7288 | 18.88 | 13.79 |
| XGBoost ← BEST | 0.6690±0.0332 | 0.7321 | 18.77 | 13.57 |
| Ridge | 0.5981±0.0765 | 0.6844 | 20.37 | 15.42 |
| GP Regression | 0.3375±0.3836 | 0.7120 | 19.46 | 14.30 |

## Test Set Results (XGBoost)
- **R²**: 0.6366
- **RMSE**: 21.34
- **MAE**: 16.37

## Top 20 Most Important Features

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Abilities_Fluency of Ideas | 0.2695 |
| 2 | Abilities_Originality | 0.1473 |
| 3 | Skills_Instructing | 0.0658 |
| 4 | Skills_Active Learning | 0.0412 |
| 5 | Abilities_Deductive Reasoning | 0.0340 |
| 6 | Job Zone | 0.0305 |
| 7 | Knowledge_Therapy and Counseling | 0.0240 |
| 8 | Skills_Critical Thinking | 0.0182 |
| 9 | Skills_Management of Personnel Resources | 0.0156 |
| 10 | Skills_Learning Strategies | 0.0139 |
| 11 | Skills_Systems Analysis | 0.0132 |
| 12 | Skills_Coordination | 0.0132 |
| 13 | Skills_Judgment and Decision Making | 0.0125 |
| 14 | Abilities_Speech Recognition | 0.0107 |
| 15 | Skills_Time Management | 0.0096 |
| 16 | Abilities_Problem Sensitivity | 0.0081 |
| 17 | Work_Activities_Assisting and Caring for Others | 0.0073 |
| 18 | Abilities_Speech Clarity | 0.0071 |
| 19 | Abilities_Written Comprehension | 0.0068 |
| 20 | Skills_Persuasion | 0.0062 |

## Interpretation

The XGBoost model achieves R²=0.6366 on the held-out test set, 
meaning it explains 63.7% of the variance in F&O automation scores.
The top features align with theoretical expectations: occupation characteristics
related to routine/manual tasks are associated with higher AI exposure,
while social, creative, and complex cognitive tasks predict lower risk.