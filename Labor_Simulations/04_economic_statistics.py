import pandas as pd
import numpy as np
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(message)s')
def main():
    """
    Produce descriptive macroeconomic statistics, including wage quartile analysis, 
    wage-exposure correlations, and concrete examples of highly exposed vs. 
    highly protected occupations.
    """
    DATA_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\data\maei_with_wages.csv"
    
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=['A_MEDIAN', 'TOT_EMP', 'MAEI_2026_Score'])
    
    logging.info("\n--- MACRO WAGE & EXPOSURE CORRELATIONS ---")
    corr_wage = df['MAEI_2026_Score'].corr(df['A_MEDIAN'])
    corr_emp = df['MAEI_2026_Score'].corr(df['TOT_EMP'])
    logging.info(f"Correlation between MAEI and Median Wage: {corr_wage:.3f}")
    
    
    logging.info("\n--- QUARTILE ANALYSIS ---")
    df['Wage_Quartile'] = pd.qcut(df['A_MEDIAN'], 4, labels=['Low Wage', 'Lower-Mid Wage', 'Upper-Mid Wage', 'High Wage'])
    
    wage_q_summary = df.groupby('Wage_Quartile').agg(
        Avg_MAEI=('MAEI_2026_Score', 'mean'),
        Total_Workers=('TOT_EMP', 'sum'),
        Occupations=('Occupation', 'count')
    ).reset_index()
    logging.info(wage_q_summary.to_string(index=False))
    
    
    logging.info("\n--- CONCRETE EXAMPLES: TOP 5 HIGHLY EXPOSED & HIGHLY PAID OCCUPATIONS ---")
    # High wage = > $100k, sort by MAEI
    high_paid_exposed = df[df['A_MEDIAN'] > 100000].sort_values(by='MAEI_2026_Score', ascending=False).head(5)
    for idx, row in high_paid_exposed.iterrows():
        logging.info(f"* {row['Occupation']} - Wage: ${row['A_MEDIAN']:,.0f} | MAEI: {row['MAEI_2026_Score']} | Workers: {row['TOT_EMP']:,.0f}")
        
        
    logging.info("\n--- CONCRETE EXAMPLES: TOP 5 LEAST EXPOSED & LOW PAID OCCUPATIONS ---")
    # Low wage = < $40k, sort by MAEI asc
    low_paid_protected = df[df['A_MEDIAN'] < 40000].sort_values(by='MAEI_2026_Score', ascending=True).head(5)
    for idx, row in low_paid_protected.iterrows():
        logging.info(f"* {row['Occupation']} - Wage: ${row['A_MEDIAN']:,.0f} | MAEI: {row['MAEI_2026_Score']} | Workers: {row['TOT_EMP']:,.0f}")

    logging.info("\n--- CONCRETE EXAMPLES: MASS EMPLOYMENT (Over 1 Million Workers) ---")
    mass_employment = df[df['TOT_EMP'] > 1000000].sort_values(by='TOT_EMP', ascending=False).head(5)
    for idx, row in mass_employment.iterrows():
        logging.info(f"* {row['Occupation']} - Wage: ${row['A_MEDIAN']:,.0f} | MAEI: {row['MAEI_2026_Score']} ({row['Risk_Level']}) | Workers: {row['TOT_EMP']:,.0f}")


if __name__ == "__main__":
    main()
