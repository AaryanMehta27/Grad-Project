# Professor Meeting: MAEI Project Presentation Guide

This guide is designed to help you confidently present your project's methodology, rigorous algorithmic updates, and macroeconomic insights to your professor. 

It is structured chronologically, mapping to the **4 most important files** you should open on your computer and physically walk through during the meeting.

---

## 1. The Core Methodology & Optimization
**File to Open:** `src/02_baseline_modeling.py`

**The Narrative:**
*   "We started by using the 2013 Frey & Osborne probabilities as a baseline truth to train a machine-learning model against 130+ distinct O\*NET human capability features (skills, abilities, work contexts)."
*   "To ensure academic rigor, I didn't just guess the model architecture. I implemented a **5-Fold Cross-Validated Randomized Search**, testing 75 different hyperparameter configurations."
*   "Our mathematically tuned XGBoost algorithm achieved a **Test R² of 0.6366** (vastly outperforming our baseline target of 0.50). This proves the algorithm has successfully learned the underlying latent 'shape' of automation risk."

---

## 2. The MAEI Index & The 'AI Uplift' Shift
**File to Open:** `results/figures/risk_tiers_corrected.png`
*(Alternatively, you can briefly flash `results/maei_2026_with_deltas.csv`)*

**The Narrative:**
*   "Once the model learned baseline automation risk, we applied an **'AI-Exposure Uplift Calculus'**."
*   "F&O (2013) couldn't predict Generative AI. So, we adjusted the baseline predictions by isolating specific O\*NET text and coding skills that have been structurally compromised by Large Language Models since 2013."
*   "On average, the algorithm shifted occupations **+6.47 points more exposed** than the 2013 baseline. Explain that this graph visibly demonstrates how the mass of the workforce index has shifted towards higher cognitive exposure."

---

## 3. The Macreconomic Shock (Wages vs. Automation)
**File to Open:** `Labor_Simulations/figures/wage_vs_exposure_scatter.png`

**The Narrative:**
*   "To prove this index works in the real world, I merged our MAEI exposure scores with the Bureau of Labor Statistics (BLS) May 2023 dataset, capturing 194.4 Million workers and $13.37 Trillion in wages."
*   "Show the scatter plot. Note the massive, statistically significant **negative correlation (-0.491)** between Median Wage and MAEI Score."
*   "This visualization proves the paradigm shift: Unlike the blue-collar automation of the 1990s, the Generative AI wave structurally targets the lower-to-middle cognitive class. Exposure drops exponentially only once you reach the highest wage tiers."

---

## 4. Empirical Market Insights ("The Human Premium")
**File to Open:** `Labor_Simulations/SIMULATION_INSIGHTS.md`

**The Narrative:**
*   "Finally, I ran an Ordinary Least Squares (OLS) regression against the entire U.S. labor market to see how the free market prices 'safe' human traits."
*   "The algorithm proved **The Human Premium**: Jobs requiring *Originality* command a **+24.4%** wage premium per standard deviation. The market intensely rewards unique creativity that AI cannot derive."
*   "The algorithm also proved a **Market Failure**: Jobs requiring *Assisting and Caring for Others* face an **-8.8%** systemic wage penalty. Despite being structurally immune to AI automation, the market chronically undervalues physical caregiving labor."
*   *Conclusion:* End with the **Reskilling "Constraint Trap"**—show how mathematically optimal transitions (like a displaced Tax Preparer becoming a Credit Counselor) exist, but the lack of cognitive safe-havens requires office workers to consider manual labor, creating immense structural friction. 
