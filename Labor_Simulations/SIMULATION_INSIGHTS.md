# Economic Simulations & Macro Insights
*A living document recording empirical findings, statistics, and examples derived from joining the Modern AI Exposure Index (MAEI) with Bureau of Labor Statistics (BLS) Occupational Employment and Wage Statistics (OEWS).*

---

## 1. Macroeconomic Baseline Vulnerability
*Calculated by merging MAEI capability overlap scores with May 2023 National BLS Wage & Employment data.*

### The Scope
*   **Total Occupations Analyzed:** 942
*   **Total U.S. Workforce Captured:** 194.4 Million workers
*   **Total Annual Wages Captured:** $13.37 Trillion

### The "Highly Exposed" Shock Scenario
Defining "Highly Exposed" as any occupation sitting in the top 25% (upper quartile, MAEI $\geq$ 82.0) of the capability overlap distribution:
*   **Highly Exposed Workers:** **58.8 Million workers** (30.3% of the U.S. workforce)
*   **Gross Wages Exposed:** **$2.42 Trillion** (18.2% of total U.S. wages)
*   *Insight:* The fact that 30.3% of the workforce commands only 18.2% of total wages in this exposure quartile proves that the most intense structural vulnerabilities to Generative AI disproportionately target lower-to-median wage cognitive or clerical roles, rather than the highest earners.

---

## 2. Wage & Exposure Distribution
*Analyzing the relationship between market compensation and structural automation risk.*

### Macro Correlations
*   **Pearson Correlation (Wage vs. MAEI):** **-0.491** 
*   *Insight:* A massive, statistically robust negative correlation. This confirms the paradigm shift of the 2020s: Unlike physical automation that destroyed middle-class manufacturing, cognitive automation (GenAI) exposure *drops* steadily as occupational wages *increase*.

### Quartile Breakdown
Segmenting the US workforce into 4 equal wage tiers reveals a steep, linear drop-off in AI exposure:
1.  **Low Wage Tier** (Avg MAEI: **70.9**) - 69.8M Workers
2.  **Lower-Mid Wage Tier** (Avg MAEI: **65.3**) - 26.8M Workers
3.  **Upper-Mid Wage Tier** (Avg MAEI: **41.5**) - 39.2M Workers
4.  **High Wage Tier** (Avg MAEI: **30.2**) - 58.5M Workers

### Concrete Examples
*   **The Anomaly Zone (Highly Exposed but Highly Paid):**
    *   *Compensation and Benefits Managers* - Wage: $136,380 | MAEI: 100.0 | Workers: 18,690
    *   *Administrative Services Managers* - Wage: $106,470 | MAEI: 89.5 | Workers: 242,520
*   **The Protected Floor (Least Exposed & Low Paid):**
    *   *Preschool Teachers* - Wage: $37,130 | MAEI: 1.38 | Workers: 430,240
    *   *Craft Artists* - Wage: $36,600 | MAEI: 3.69 | Workers: 5,830
    *   *Childcare Workers* - Wage: $30,370 | MAEI: 6.43 | Workers: 497,450
*   **The Mass Employment Shock Targets (>$1M Workers):**
    *   *Retail Salespersons* - Wage: $33,680 | MAEI: 95.9 | Workers: 3.68 Million
    *   *Fast Food and Counter Workers* - Wage: $29,540 | MAEI: 88.8 | Workers: 3.67 Million
    *   *Cashiers* - Wage: $29,720 | MAEI: 94.6 | Workers: 3.29 Million

---

## 3. The "Human Premium" Regression Analysis
*An Ordinary Least Squares (OLS) regression across all 942 occupations, measuring the shift in Log-Median Wage associated with a 1 Standard Deviation (Std-Dev) increase in O\*NET "human-centric" capability scores.*

### Statistically Significant Wage Premiums (+)
These traits provide structural protection against AI *and* command a statistically powerful wage premium in the free market:
*   **Originality:** A 1 Std-Dev increase $\rightarrow$ **+24.4% shift** in median wage (***)
    *   *Insight:* Validates the "Creator Economy" hypothesis; the market heavily rewards unique human creativity over generative derivation.
*   **Therapy and Counseling:** A 1 Std-Dev increase $\rightarrow$ **+7.7% shift** in median wage (***)
*   **Instructing/Teaching:** A 1 Std-Dev increase $\rightarrow$ **+7.4% shift** in median wage (***)

### Statistically Significant Wage Penalties (-)
These traits successfully protect occupations from AI automation (they are physically or socially irreplaceable), but the market paradoxically *punishes* these traits in compensation:
*   **Fine Arts Knowledge:** A 1 Std-Dev increase $\rightarrow$ **-11.2% shift** in median wage (***)
    *   *Insight:* The "Starving Artist" paradox. High human authenticity, structurally safe from true autonomous production, but highly undervalued economically.
*   **Assisting and Caring for Others:** A 1 Std-Dev increase $\rightarrow$ **-8.8% shift** in median wage (***)
    *   *Insight:* The "Underpaid Caregiver" paradox. Systemic market failure to properly compensate the immense physiological and social labor required for nursing aides, childcare workers, and home health assistants, despite the impossibility of automating their core tasks.

### Stagnant / Non-Significant Traits
*   **Social Perceptiveness:** +2.0% shift (Not Significant)
*   **Negotiation:** +2.3% shift (Not Significant)
*   *Insight:* These traits are often required baselines for employment rather than specialized skills that command exponential wage growth independently.


## 4. Algorithmic Reskilling Networks ('Lifeboats')
*Comparing the latent O\*NET capability vectors (130+ dimensions of human skills, abilities, and knowledge) via Cosine Similarity to find efficient transition pathways from Highly Exposed to Protected occupations.*

### Example Displacements and Optimal Transitions
*   **Automotive Body and Related Repairers** (MAEI: 89.7): The algorithmic lifeboat recommendation is **Plumbers, Pipefitters, and Steamfitters** (Similarity: 0.46, Wage Shift: +26.3%).
*   **Compensation and Benefits Managers** (MAEI: 100.0): The algorithmic lifeboat recommendation is **Human Resources Managers** (Similarity: 0.72, Wage Shift: -0.0%).
*   **Tax Preparers** (MAEI: 100.0): The algorithmic lifeboat recommendation is **Credit Counselors** (Similarity: 0.48, Wage Shift: -0.9%).
*   **Occupational Health and Safety Technicians** (MAEI: 40.7): The algorithmic lifeboat recommendation is **Occupational Health and Safety Specialists** (Similarity: 0.59, Wage Shift: +40.1%).
