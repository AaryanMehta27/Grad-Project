"""
10_bert_reproducibility.py
==========================
Output / Section 3.5: how much of the LLM's scoring is recoverable from cheap
sentence embeddings (surface text features) vs genuine context-sensitive
reasoning? Embed all task texts with sentence-BERT (all-mpnet-base-v2, 768-d),
then predict the LLM scores from the embeddings alone and read R^2.

  - Full composite R^2 (includes the physical/digital gate, which is text-obvious)
  - PASS-subset composite R^2 (the modulated gradient — the harder, "reasoning" part)
  - Gate classification (gated vs not) — how text-predictable is the gate?
  - Per-criterion R^2 — which criteria are surface-decodable vs reasoning-driven?

Models: Ridge (linear baseline) and HistGradientBoosting (non-linear). 80/20
split stratified on composite band; 5-fold CV for the headline number. Fixed seed.
Interpretation bands (Section 3.5): R^2 >= 0.7 surface; 0.4-0.7 mixed; < 0.3 reasoning.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import RidgeCV, LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, roc_auc_score, accuracy_score

ROOT = Path(__file__).resolve().parent.parent
SEED = 20260616
d = pd.read_csv(ROOT / "data" / "processed" / "scored_master_tasks_shuffled.csv")
d = d[d["scoring_status"] != "TERMINAL_FAILURE"].reset_index(drop=True)

# ---- embeddings (cached) ----
emb_path = ROOT / "data" / "processed" / "bert_embeddings_mpnet.npy"
if emb_path.exists():
    X = np.load(emb_path)
    print(f"loaded cached embeddings {X.shape}")
else:
    from sentence_transformers import SentenceTransformer
    print("embedding 18,796 task texts with all-mpnet-base-v2 (GPU)...")
    model = SentenceTransformer("all-mpnet-base-v2", device="cuda")
    X = model.encode(d["task_text"].astype(str).tolist(), batch_size=256,
                     show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
    np.save(emb_path, X)
    print(f"saved embeddings {X.shape}")

comp = d["composite_score"].astype(float).values
band = pd.cut(comp, [-0.01, 0.001, 0.5, 0.75, 1.01], labels=[0, 1, 2, 3]).astype(int)


def evaluate(X, y, strat, label, classify=False):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=strat)
    sc = StandardScaler().fit(Xtr)
    Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    if classify:
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr, ytr)
        p = clf.predict_proba(Xte)[:, 1]
        print(f"  {label:34s}: acc={accuracy_score(yte, clf.predict(Xte)):.3f}  AUC={roc_auc_score(yte, p):.3f}  (n={len(y)})")
        return
    ridge = RidgeCV(alphas=np.logspace(-1, 4, 12)).fit(Xtr, ytr)
    r2_ridge = r2_score(yte, ridge.predict(Xte))
    hgb = HistGradientBoostingRegressor(random_state=SEED, max_iter=300, learning_rate=0.08).fit(Xtr, ytr)
    r2_hgb = r2_score(yte, hgb.predict(Xte))
    rmse = np.sqrt(mean_squared_error(yte, ridge.predict(Xte)))
    print(f"  {label:34s}: R2_ridge={r2_ridge:.3f}  R2_gbm={r2_hgb:.3f}  RMSE={rmse:.3f}  (n={len(y)})")
    return max(r2_ridge, r2_hgb)


print("\n" + "=" * 74)
print("BERT REPRODUCIBILITY — predicting LLM scores from task-text embeddings")
print("=" * 74)

print("\n[1] COMPOSITE")
r_full = evaluate(X, comp, band, "full composite (incl. gate)")
pmask = (d["scoring_status"] == "PASS").values
r_pass = evaluate(X[pmask], comp[pmask],
                  pd.cut(comp[pmask], [0.001, 0.5, 0.75, 1.01], labels=[0, 1, 2]).astype(int),
                  "PASS-subset composite (the gradient)")

print("\n[2] GATE (is the task gated to 0?) — classification")
evaluate(X, (comp == 0).astype(int), (comp == 0).astype(int), "gate (gated vs not)", classify=True)

print("\n[3] PER-CRITERION (0/1/2 score predicted from text)")
crit = {"information_sufficiency_score": "Information Sufficiency",
        "objective_verifiability_score": "Objective Verifiability",
        "contextual_independence_score": "Contextual Independence",
        "capability_match_score": "Capability Match"}
for c, name in crit.items():
    y = d[c].astype(float).values
    evaluate(X, y, d[c].astype(int).values, name)

print("\n[4] 5-FOLD CV (headline, full composite, Ridge)")
sc = StandardScaler().fit_transform(X)
ridge = RidgeCV(alphas=np.logspace(-1, 4, 12))
cv = cross_val_score(ridge, sc, comp, cv=StratifiedKFold(5, shuffle=True, random_state=SEED).split(sc, band),
                     scoring="r2")
print(f"  composite R2 (5-fold) = {cv.mean():.3f} +/- {cv.std():.3f}")

print("\nINTERPRETATION (Section 3.5 bands: >=0.7 surface | 0.4-0.7 mixed | <0.3 reasoning)")
print(f"  full composite R2 ~ {r_full:.2f}; PASS-only gradient R2 ~ {r_pass:.2f}")
