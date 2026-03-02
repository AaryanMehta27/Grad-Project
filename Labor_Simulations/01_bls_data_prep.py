import pandas as pd
import numpy as np
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')# Paths
MAEI_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\results\maei_2026_with_deltas.csv"
BLS_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Labor_Simulations\data\oesm23nat\national_M2023_dl.xlsx"
OUTPUT_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Labor_Simulations\data\maei_with_wages.csv"

def main():
    """
    Merge the calculated MAEI 2026 exposure scores with the Bureau of Labor Statistics 
    (BLS) Occupational Employment and Wage Statistics (OEWS) May 2023 dataset.
    This creates the foundational dataset for all subsequent downstream economic 
    and labor market simulations.
    """
    logging.info("Loading MAEI Data...")
    maei_df = pd.read_csv(MAEI_PATH)

    logging.info("Loading BLS OEWS 2023 Data... (This takes a moment due to Excel size)")
    bls_df = pd.read_excel(BLS_PATH)

    # Clean SOC codes for joining
    # MAEI uses SOC Code like '11-1011.00', '11-1011'
    # BLS uses OCC_CODE like '11-1011'
    maei_df['Join_SOC'] = maei_df['ONET_SOC_Code'].astype(str).str.extract(r'(\d{2}-\d{4})')
    bls_df['Join_SOC'] = bls_df['OCC_CODE'].astype(str).str.extract(r'(\d{2}-\d{4})')
    
    # Filter BLS data to detailed occupations (O_GROUP = 'detailed' or level=0, just taking exact matches usually suffices)
    # BLS has total employment (TOT_EMP) and median wage (A_MEDIAN)
    bls_subset = bls_df[['Join_SOC', 'OCC_TITLE', 'TOT_EMP', 'A_MEDIAN', 'H_MEDIAN']].copy()

    # Some SOC codes in BLS might be duplicated if they have broader groups, let's keep the one where it matches detailed occupations.
    # Actually, OCC_CODE is unique per group level in national data. If a code is repeated, it might not be.
    bls_subset = bls_subset.drop_duplicates(subset=['Join_SOC'])

    # BLS represents missing/withheld data with '*' or '#' or '**'
    bls_subset.replace({'*': np.nan, '#': np.nan, '**': np.nan}, inplace=True)
    
    # Convert wage and employment columns to numeric, replacing errors with NaN
    bls_subset['TOT_EMP'] = pd.to_numeric(bls_subset['TOT_EMP'], errors='coerce')
    bls_subset['A_MEDIAN'] = pd.to_numeric(bls_subset['A_MEDIAN'], errors='coerce')

    logging.info("Merging datasets on SOC code...")
    merged_df = pd.merge(maei_df, bls_subset, on='Join_SOC', how='left')

    # Drop the temporary join key
    merged_df.drop(columns=['Join_SOC'], inplace=True)

    logging.info(f"Total MAEI occupations evaluated: {len(maei_df)}")
    logging.info(f"Successfully matched with BLS Employment Data: {merged_df['TOT_EMP'].notna().sum()}")
    logging.info(f"Successfully matched with BLS Annual Wage Data: {merged_df['A_MEDIAN'].notna().sum()}")
    
    logging.info(f"Total employed workers evaluated: {merged_df['TOT_EMP'].sum():,.0f}")

    merged_df.to_csv(OUTPUT_PATH, index=False)
    logging.info(f"Saved merged dataset to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
