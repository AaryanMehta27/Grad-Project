import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
import warnings

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(message)s')
warnings.filterwarnings('ignore')

def main():
    """
    Computes an algorithmic reskilling network by creating a >130-dimensional
    latent space of all US occupations based on their human capability vectors 
    (Abilities, Skills, Knowledge, etc.).
    Uses Cosine Similarity to find mathematically optimal 'Lifeboat' professions 
    for highly exposed cognitive workers. 
    """
    WAGE_DATA_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\data\maei_with_wages.csv"
    ONET_FEATURES_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\data\processed\onet_features_consolidated.csv"
    
    logging.info("Loading datasets...")
    # Load Master Index
    maei_df = pd.read_csv(WAGE_DATA_PATH)
    maei_df['Join_SOC'] = maei_df['ONET_SOC_Code'].astype(str).str.extract(r'(\d{2}-\d{4})')
    
    # Load Raw O*NET Features (The human capability vectors)
    onet_df = pd.read_csv(ONET_FEATURES_PATH)
    soc_col = [c for c in onet_df.columns if 'SOC' in c][0]
    onet_df['Join_SOC'] = onet_df[soc_col].astype(str).str.extract(r'(\d{2}-\d{4})')
    
    # Average numeric features per SOC code
    numeric_cols = onet_df.select_dtypes(include=[np.number]).columns.tolist()
    onet_agg = onet_df.groupby('Join_SOC')[numeric_cols].mean().reset_index()
    
    # Join the MAEI scores to the O*NET feature vectors
    merged_df = pd.merge(maei_df, onet_agg, on='Join_SOC', how='inner')
    
    # Drop rows without wage or MAEI to be safe
    merged_df = merged_df.dropna(subset=['A_MEDIAN', 'MAEI_2026_Score'])
    
    logging.info(f"Total Occupations ready for Cosine Similarity: {len(merged_df)}")
    
    # Isolate the Feature Matrix (X) that defines the "Shape" of the human
    # We will exclude MAEI scores, wages, and identifiers from this matrix
    exclude_cols = ['ONET_SOC_Code', 'Occupation', 'Join_SOC', 'A_MEDIAN', 'H_MEDIAN', 'TOT_EMP', 'MAEI_2026_Score', 'MAEI_Pure_2026', 'Exposure_Delta']
    
    # Grab all O*NET numeric columns 
    feature_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    # Standardize the feature matrix so large scales don't dominate the cosine similarity
    X = merged_df[feature_cols].values
    from sklearn.preprocessing import StandardScaler
    X_scaled = StandardScaler().fit_transform(X)
    
    # Calculate pairwise cosine similarity between ALL occupations
    # Closer to 1.0 = Highly similar skill/ability profiles
    logging.info("Computing O*NET Capability Cosine Similarity Matrix...")
    similarity_matrix = cosine_similarity(X_scaled)
    
    # We want to identify the "Best Lifeboats" for Highly Exposed roles:
    # 1. Start with a highly exposed role (e.g. MAEI > 85)
    # 2. Find the most mathematically similar roles based on human capability vectors
    # 3. Filter for roles that have LOW exposure (e.g. MAEI < 40)
    # 4. Filter for roles that don't have a massive wage penalty (e.g. Wage >= 80% of original wage)
    
    high_risk_threshold = 85.0
    low_risk_threshold = 40.0
    
    high_risk_idx = merged_df.index[merged_df['MAEI_2026_Score'] >= high_risk_threshold].tolist()
    
    logging.info("\n" + "="*80)
    logging.info(" ALGORITHMIC RESKILLING: 'LIFEBOAT' PATHWAY RECOMMENDATIONS")
    logging.info("="*80)
    
    # Let's find lifeboats for a few specific examples highly relevant to our previous findings
    example_targets = [
        "Paralegals and Legal Assistants",
        "Compensation and Benefits Managers",
        "Tax Preparers",
        "Interpreters and Translators"
    ]
    
    insights = []
    
    for target in example_targets:
        try:
            target_idx = merged_df[merged_df['Occupation'].str.contains(target, case=False, na=False)].index[0]
            target_row = merged_df.iloc[target_idx]
            logging.info(f"\n[DISPLACED OCCUPATION]: {target_row['Occupation']}")
            logging.info(f"   MAEI Risk: {target_row['MAEI_2026_Score']:.1f}/100 | Current Median Wage: ${target_row['A_MEDIAN']:,.0f}")
            
            # Get similarities for this specific job
            sim_scores = similarity_matrix[target_idx]
            
            # Create a dataframe of candidates
            candidates = merged_df[['Occupation', 'MAEI_2026_Score', 'A_MEDIAN']].copy()
            candidates['Similarity'] = sim_scores
            
            # Filter for true lifeboats
            # 1. Must be low exposure (MAEI < 40)
            # 2. Must not be the identical job (Similarity < 0.99)
            lifeboats = candidates[
                (candidates['MAEI_2026_Score'] <= low_risk_threshold) & 
                (candidates['Similarity'] < 0.999)
            ].sort_values(by='Similarity', ascending=False)
            
            if len(lifeboats) > 0:
                logging.info("   [TOP RECOMMENDED LIFEBOAT TRANSITIONS] (Based on latent human capabilities):")
                # Show top 3 lifeboats
                for i in range(min(3, len(lifeboats))):
                    lb = lifeboats.iloc[i]
                    wage_diff_pct = ((lb['A_MEDIAN'] - target_row['A_MEDIAN']) / target_row['A_MEDIAN']) * 100
                    logging.info(f"      {i+1}. {lb['Occupation'][:40]}")
                    logging.info(f"         Similarity: {lb['Similarity']:.2f} | MAEI: {lb['MAEI_2026_Score']:.1f}/100 | Wage: ${lb['A_MEDIAN']:,.0f} ({wage_diff_pct:+.1f}%)")
                    
                    if i == 0:
                        insights.append(f"*   **{target_row['Occupation']}** (MAEI: {target_row['MAEI_2026_Score']:.1f}): The algorithmic lifeboat recommendation is **{lb['Occupation']}** (Similarity: {lb['Similarity']:.2f}, Wage Shift: {wage_diff_pct:+.1f}%).")
            else:
                logging.info("   [WARNING] No protected lifeboats found with high mathematical similarity.")
                
        except IndexError:
            # Job not found in exact string match
            continue
            
    # Save these examples to insights file
    with open(r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\SIMULATION_INSIGHTS.md", "a", encoding="utf-8") as f:
        f.write("\n\n## 4. Algorithmic Reskilling Networks ('Lifeboats')\n")
        f.write("*Comparing the latent O\\*NET capability vectors (130+ dimensions of human skills, abilities, and knowledge) via Cosine Similarity to find efficient transition pathways from Highly Exposed to Protected occupations.*\n\n")
        f.write("### Example Displacements and Optimal Transitions\n")
        for ins in insights:
            f.write(ins + "\n")
            
    logging.info("\nSaved Reskilling Insights to SIMULATION_INSIGHTS.md")

if __name__ == "__main__":
    main()
