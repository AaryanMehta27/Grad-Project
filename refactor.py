import os
import glob
from pathlib import Path

replacements = {
    'AVI_2026_Score': 'MAEI_2026_Score',
    'AVI_2026': 'MAEI_2026',
    'Baseline_Score': 'Hist_Ref_2013',
    'Delta': 'Exposure_Delta',
    'AI_uplift': 'Broad_Exposure_Adj',
    'ai_uplift': 'broad_exposure_adj',
    'avi_2026_with_deltas.csv': 'maei_2026_with_deltas.csv',
    'avi_2026_explanations.csv': 'maei_explanations.csv',
    'automation vulnerability': 'AI-task overlap',
    'automation risk': 'AI exposure',
    'Automation vulnerability': 'AI-task overlap',
    'Automation risk': 'AI exposure',
    'Automation Risk': 'AI Exposure',
    'AVI score': 'MAEI score',
    'AVI': 'MAEI',
    '04_audit_and_explain': '03_maei_calculation'
}

src_dir = Path(r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\src")
for filepath in src_dir.glob("*.py"):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Rename the file 04_audit_and_explain.py to 03_maei_calculation.py
old_file = src_dir / '04_audit_and_explain.py'
if old_file.exists():
    new_file = src_dir / '03_maei_calculation.py'
    os.rename(old_file, new_file)
    print(f"Renamed {old_file.name} to {new_file.name}")

print("Refactoring complete.")
