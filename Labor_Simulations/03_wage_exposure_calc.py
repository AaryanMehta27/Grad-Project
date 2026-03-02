import pandas as pd
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(message)s')
def main():
    """
    Calculate the total macroscopic economic impact of AI exposure across the US 
    labor market, quantifying the number of workers and aggregate annual wages 
    falling into the 'Highly Exposed' (top quartile) category.
    """
    DATA_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\data\maei_with_wages.csv"
    
    logging.info("Loading merged wage dataset...")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=['A_MEDIAN', 'TOT_EMP', 'MAEI_2026_Score'])
    
    # Calculate Total US Wage Economy (for the occupations we matched)
    df['Total_Annual_Wages'] = df['A_MEDIAN'] * df['TOT_EMP']
    total_us_wages = df['Total_Annual_Wages'].sum()
    
    # Define "Highly Exposed" as the top 25% (upper quartile) of MAEI scores
    q75 = df['MAEI_2026_Score'].quantile(0.75)
    
    highly_exposed_df = df[df['MAEI_2026_Score'] >= q75]
    exposed_wages = highly_exposed_df['Total_Annual_Wages'].sum()
    exposed_workers = highly_exposed_df['TOT_EMP'].sum()
    
    logging.info("="*60)
    logging.info(" [US MACROECONOMIC AI EXPOSURE SUMMARY]")
    logging.info("="*60)
    logging.info(f"Total Occupations Analyzed: {len(df):,}")
    logging.info(f"Total Employment Captured: {df['TOT_EMP'].sum():,.0f} workers")
    logging.info(f"Total Annual Wages Captured: ${total_us_wages:,.0f}")
    logging.info("-" * 60)
    logging.info(f"Threshold for Top Quartile (Highly Exposed): MAEI >= {q75:.1f}")
    logging.info(f"Number of Highly Exposed Occupations: {len(highly_exposed_df):,}")
    logging.info(f"Number of Highly Exposed Workers: {exposed_workers:,.0f} ({(exposed_workers/df['TOT_EMP'].sum())*100:.1f}% of workforce)")
    logging.info(f"Total Gross Wages in Highly Exposed Tier: ${exposed_wages:,.0f} ({(exposed_wages/total_us_wages)*100:.1f}% of total wages)")
    logging.info("=" * 60)
    
if __name__ == "__main__":
    main()
