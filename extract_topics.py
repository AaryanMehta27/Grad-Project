import joblib
import pandas as pd
from pathlib import Path

DATA_PROCESSED = Path(r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\data\processed")
MODELS_DIR = Path(r"c:\Users\aarya\OneDrive\Desktop\Graduation_Project_Data\MAEI_Project\models")

data = joblib.load(DATA_PROCESSED / "modeling_dataset.pkl")
model_artifact = joblib.load(MODELS_DIR / "baseline_model.pkl")

svd = model_artifact['svd']
feature_cols = data['feature_cols']

tfidf_cols = [c for c in feature_cols if c.startswith('TFIDF_')]
print(f"Loaded {len(tfidf_cols)} TF-IDF features.")

topic_mapping = {}

for i, comp in enumerate(svd.components_):
    terms_comp = zip(tfidf_cols, comp)
    sorted_terms = sorted(terms_comp, key=lambda x: x[1], reverse=True)[:7]
    print(f"NLP_Topic_{i+1}:")
    for term, weight in sorted_terms:
        print(f"  {term.replace('TFIDF_', '')} ({weight:.3f})")
    
    # Simple generation heuristics based on top 2 words
    # You would manually refine this mapping
    words = [t[0].replace('TFIDF_', '') for t in sorted_terms[:3]]
    topic_mapping[f"NLP_Topic_{i+1}"] = f"NLP_Topic_{'_'.join(words)}"

print("\nSuggested Variable Replacements:")
for old, new in topic_mapping.items():
    print(f"'{old}': '{new}',")

