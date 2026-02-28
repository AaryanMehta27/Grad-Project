import pandas as pd

def main():
    DATA_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\data\maei_with_wages.csv"
    
    print("Loading merged wage dataset...")
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
    
    print("="*60)
    print(" [US MACROECONOMIC AI EXPOSURE SUMMARY]")
    print("="*60)
    print(f"Total Occupations Analyzed: {len(df):,}")
    print(f"Total Employment Captured: {df['TOT_EMP'].sum():,.0f} workers")
    print(f"Total Annual Wages Captured: ${total_us_wages:,.0f}")
    print("-"*60)
    print(f"Threshold for Top Quartile (Highly Exposed): MAEI >= {q75:.1f}")
    print(f"Number of Highly Exposed Occupations: {len(highly_exposed_df):,}")
    print(f"Number of Highly Exposed Workers: {exposed_workers:,.0f} ({(exposed_workers/df['TOT_EMP'].sum())*100:.1f}% of workforce)")
    print(f"Total Gross Wages in Highly Exposed Tier: ${exposed_wages:,.0f} ({(exposed_wages/total_us_wages)*100:.1f}% of total wages)")
    print("="*60)
    
if __name__ == "__main__":
    main()
