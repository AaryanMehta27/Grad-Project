import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

def main():
    """
    Generate a scatter plot visualizing the relationship between Median Annual Wage
    and the MAEI 2026 Score. The visualization sizes points by total employment
    and prevents label overlap using adjustText.
    """
    DATA_PATH = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\data\maei_with_wages.csv"
    OUTPUT_DIR = r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\Grad-Project\Labor_Simulations\figures"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logging.info("Loading merged dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # Drop rows without wage or employment data
    df = df.dropna(subset=['A_MEDIAN', 'TOT_EMP', 'MAEI_2026_Score'])
    
    # Filter out extreme outliers in wage for a better plot (e.g. > $250k) 
    # or keep them but use a log scale. Let's use linear but cap x at 250k.
    df = df[df['A_MEDIAN'] <= 250000]

    logging.info("Generating Wage vs Exposure Scatter Plot...")
    
    plt.figure(figsize=(14, 10))
    
    # Create the scatter plot. 
    # X = Wage, Y = MAEI, Size = Employment
    scatter = plt.scatter(
        df['A_MEDIAN'], 
        df['MAEI_2026_Score'], 
        s=df['TOT_EMP'] / 5000,  # Scale down sizes for visibility
        alpha=0.6,
        c=df['MAEI_2026_Score'], # Color by exposure
        cmap='coolwarm',
        edgecolors='white',
        linewidth=0.5
    )
    
    plt.axhline(y=df['MAEI_2026_Score'].median(), color='black', linestyle='--', alpha=0.5, label='Median Exposure')
    plt.axvline(x=df['A_MEDIAN'].median(), color='black', linestyle=':', alpha=0.5, label='Median Wage')
    
    # Formatting
    plt.title('Occupational AI Exposure (MAEI) vs. Median Annual Wage', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('Median Annual Wage (USD)', fontsize=14, fontweight='bold')
    plt.ylabel('MAEI 2026 Capability Overlap Score', fontsize=14, fontweight='bold')
    
    # Format X axis as currency
    current_values = plt.gca().get_xticks()
    plt.gca().set_xticklabels(['${:,.0f}'.format(x) for x in current_values])
    
    plt.colorbar(scatter, label='MAEI Score')
    plt.grid(True, alpha=0.3)
    
    # Annotate some top occupations
    texts = []
    
    # Highest Exposure
    top_exposed = df.nlargest(5, 'MAEI_2026_Score')
    for idx, row in top_exposed.iterrows():
        texts.append(plt.text(row['A_MEDIAN'], row['MAEI_2026_Score'], row['Occupation'][:35], fontsize=9, alpha=0.9, weight='bold'))
                     
    # Highest Employment
    top_jobs = df.nlargest(5, 'TOT_EMP')
    for idx, row in top_jobs.iterrows():
        texts.append(plt.text(row['A_MEDIAN'], row['MAEI_2026_Score'], row['Occupation'][:35], fontsize=9, alpha=0.9, color='darkblue', weight='bold'))
        
    # Highest Wage (To show the far right of the plot)
    top_wage = df.nlargest(5, 'A_MEDIAN')
    for idx, row in top_wage.iterrows():
        texts.append(plt.text(row['A_MEDIAN'], row['MAEI_2026_Score'], row['Occupation'][:35], fontsize=9, alpha=0.9, color='darkred', weight='bold'))

    # Safely adjust text to prevent overlaps
    from adjustText import adjust_text
    adjust_text(texts, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "wage_vs_exposure_scatter.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logging.info(f"Saved figure to {output_path}")

if __name__ == "__main__":
    main()
