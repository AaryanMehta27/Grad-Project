import pandas as pd
import scipy.stats as stats
from pathlib import Path

RESULTS_DIR = Path(r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\results")
maei_path = RESULTS_DIR / 'maei_2026_with_deltas.csv'

maei_df = pd.read_csv(maei_path)
maei_df['Base_SOC'] = maei_df['ONET_SOC_Code'].astype(str).str.split('.').str[0]
maei_scored = maei_df[maei_df['Score_Source'] != 'insufficient_data'].copy()

url = "https://github.com/AIOE-Data/AIOE/raw/main/AIOE_DataAppendix.xlsx"
aioe_df = pd.read_excel(url, sheet_name='Appendix A')
aioe_df['Base_SOC'] = aioe_df['SOC Code'].astype(str).str.strip()

merged = pd.merge(maei_scored, aioe_df, on='Base_SOC', how='inner').dropna(subset=['MAEI_2026_Score', 'AIOE'])

sp_anchored, _ = stats.spearmanr(merged['MAEI_2026_Score'], merged['AIOE'])
sp_pure, _ = stats.spearmanr(merged['MAEI_Pure_2026'], merged['AIOE'])
sp_fo, _ = stats.spearmanr(merged['Hist_Ref_2013'], merged['AIOE'])

print(f"Correlation AIOE vs Anchored MAEI: {sp_anchored:.3f}")
print(f"Correlation AIOE vs Pure 2026 MAEI: {sp_pure:.3f}")
print(f"Correlation AIOE vs Hist F&O 2013: {sp_fo:.3f}")
