import pandas as pd
import numpy as np
import statsmodels.api as sm
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(message)s')
def main():
    """
    Run an Ordinary Least Squares (OLS) regression between an occupation's median 
    annual wage and its presence of intensely human-centric traits (such as Originality, 
    Therapy, and Persuasion). This tests the 'Human Premium' hypothesis.
    """
    WAGE_DATA_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\data\maei_with_wages.csv"
    ONET_FEATURES_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\data\processed\onet_features_consolidated.csv"
    
    # Load Wage Data
    logging.info("Loading Wage Data...")
    wage_df = pd.read_csv(WAGE_DATA_PATH)
    wage_df = wage_df.dropna(subset=['A_MEDIAN'])
    # Normalize Join_SOC 
    wage_df['Join_SOC'] = wage_df['ONET_SOC_Code'].astype(str).str.extract(r'(\d{2}-\d{4})')
    
    # Load O*NET raw features
    logging.info("Loading Raw O*NET Features...")
    onet_df = pd.read_csv(ONET_FEATURES_PATH)
    # Different O*NET sources use different SOC columns, let's grab the first one that looks like SOC
    soc_col = [c for c in onet_df.columns if 'SOC' in c][0]
    onet_df['Join_SOC'] = onet_df[soc_col].astype(str).str.extract(r'(\d{2}-\d{4})')
    
    logging.info("Merging Data...")
    # Group by Join_SOC in ONET data (in case there are multiple detailed occupation codes for a single major code)
    # Average the numeric features first.
    numeric_cols = onet_df.select_dtypes(include=[np.number]).columns.tolist()
    onet_agg = onet_df.groupby('Join_SOC')[numeric_cols].mean().reset_index()
    
    merged_df = pd.merge(wage_df, onet_agg, on='Join_SOC', how='inner')
    
    # Identify the exact column names for the 'Human Premium' traits
    # We will search the columns for specific keywords
    keywords = [
        'Originality', 
        'Social Perceptiveness', 
        'Assisting and Caring for Others', 
        'Therapy and Counseling', 
        'Fine Arts',
        'Persuasion',
        'Negotiation',
        'Instructing'
    ]
    
    feature_columns = []
    for kw in keywords:
        matches = [c for c in merged_df.columns if kw.lower() in c.lower() and 'value' not in c.lower()] # Often O*NET has IM (Importance) and LV (Level) or Value. Let's just pick any column matching exactly if available.
        # Fallback to precise matching if possible, otherwise take the first match
        exact = [c for c in matches if c == kw]
        if exact:
            feature_columns.append(exact[0])
        elif matches:
            feature_columns.append(matches[0])
            
    logging.info(f"\nFound Human Premium Features: {feature_columns}")
    
    # Prepare Regression Data
    # Dependent Variable: log(Median Wage)
    # We use log-wage because wages are classically log-normally distributed in econometrics
    merged_df['Log_Wage'] = np.log(merged_df['A_MEDIAN'])
    
    # Independent Variables (X)
    X = merged_df[feature_columns].copy()
    
    # Standardize X for easy coefficient interpretation (Standard Deviation change)
    X_std = (X - X.mean()) / X.std()
    
    # Add a constant (intercept)
    X_std = sm.add_constant(X_std)
    y = merged_df['Log_Wage']
    
    # Drop NaNs
    reg_data = pd.concat([X_std, y], axis=1).dropna()
    
    logging.info("\n" + "="*80)
    logging.info(" THE HUMAN PREMIUM: OLS REGRESSION (Log-Wage vs. Human Traits)")
    logging.info("="*80)
    
    # Run OLS Regression
    model = sm.OLS(reg_data['Log_Wage'], reg_data.drop(columns=['Log_Wage'])).fit()
    logging.info(model.summary())
    
    logging.info("\n" + "="*80)
    logging.info(" INTERPRETATION:")
    logging.info("="*80)
    for index, row in model.params.items():
        if index != 'const':
            p_val = model.pvalues[index]
            sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else "not sig"
            
            # Since dependent is a log, a coefficient of 0.10 means a 1 standard deviation increase in that trait 
            # is associated with approximately a 10% increase in median wage.
            pct_change = (np.exp(row) - 1) * 100
            logging.info(f"* {index}: a 1 Std-Dev increase is associated with a {pct_change:+.1f}% shift in median wage. ({sig})")

if __name__ == "__main__":
    main()
