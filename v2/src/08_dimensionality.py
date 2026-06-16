"""
08_dimensionality.py
====================
Output D (Section 3.6): is the four-criterion structure empirically separable?
Run on the full 18,796-task corpus. Diagnostics:
  1. Spearman correlation matrix (full corpus, and PASS subset where criteria modulate)
  2. PCA on the four criterion scores (eigenvalues / variance explained / PC1 loadings)
  3. Gate-attribution stability (single vs multi-criterion gating among gated tasks)
The per-criterion human/LLM disagreement (diagnostic 4) is in the Tier-2 analysis
(src/06_analyze_validation.py); referenced, not recomputed here.

This is diagnostic and reported, NOT a model-selection trigger (Section 5.20).
Read-only. Author: Aaryan Mehta.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data" / "processed" / "scored_master_tasks_shuffled.csv")
d = d[d["scoring_status"] != "TERMINAL_FAILURE"].copy()
CRIT = ["information_sufficiency_score", "objective_verifiability_score",
        "contextual_independence_score", "capability_match_score"]
S = {"information_sufficiency_score": "IS", "objective_verifiability_score": "OV",
     "contextual_independence_score": "CtxI", "capability_match_score": "CM"}


def pca_report(df, label):
    X = df[CRIT].astype(float).values
    # PCA on the correlation matrix (standardised) -> eigenvalues sum to 4
    R = np.corrcoef(X, rowvar=False)
    evals, evecs = np.linalg.eigh(R)
    order = np.argsort(evals)[::-1]
    evals = evals[order]; evecs = evecs[:, order]
    var = evals / evals.sum()
    print(f"  PCA ({label}, n={len(df)}):")
    print("    eigenvalues:      " + "  ".join(f"{e:.2f}" for e in evals))
    print("    % variance:       " + "  ".join(f"{v*100:4.1f}" for v in var))
    print("    cumulative %:     " + "  ".join(f"{c*100:4.1f}" for c in np.cumsum(var)))
    pc1 = evecs[:, 0]
    print("    PC1 loadings:     " + "  ".join(f"{S[c]}={l:+.2f}" for c, l in zip(CRIT, pc1)))


print("=" * 74)
print("OUTPUT D — CRITERION DIMENSIONALITY (full corpus, 18,796 tasks)")
print("=" * 74)

print("\n[1] SPEARMAN CORRELATION MATRIX")
print("  Full corpus:")
print(d[CRIT].corr(method="spearman").round(2).rename(index=S, columns=S).to_string().replace("\n", "\n  "))
pas = d[d["scoring_status"] == "PASS"]
print("\n  PASS subset (where the criteria actually modulate the composite):")
print(pas[CRIT].corr(method="spearman").round(2).rename(index=S, columns=S).to_string().replace("\n", "\n  "))

print("\n[2] PRINCIPAL COMPONENT ANALYSIS")
pca_report(d, "full corpus")
print()
pca_report(pas, "PASS subset")

print("\n[3] GATE-ATTRIBUTION STABILITY (among gated tasks)")
g = d[d["scoring_status"] == "GATED"].copy()
is0 = g["information_sufficiency_score"] == 0
cm0 = g["capability_match_score"] == 0
print(f"  gated tasks: {len(g)}")
print(f"    Information Sufficiency = 0 only (physical, model could attempt if digital): {int((is0 & ~cm0).sum())}")
print(f"    Capability Match = 0 only (digital but beyond capability):                  {int((~is0 & cm0).sum())}")
print(f"    BOTH gates fire (physical AND beyond capability):                           {int((is0 & cm0).sum())}")
nz = (g[CRIT] == 0).sum(axis=1)
print(f"  criteria simultaneously 0 per gated task: mean {nz.mean():.2f}  "
      f"(=1:{int((nz==1).sum())}  =2:{int((nz==2).sum())}  =3:{int((nz==3).sum())}  =4:{int((nz==4).sum())})")

print("\n[4] per-criterion reliability — see Tier-2 analysis (src/06_analyze_validation.py):")
print("    most consistent: Information Sufficiency; noisiest: Contextual Independence & Capability Match.")

print("\nINTERPRETATION")
print("  Full-corpus correlations are inflated by the gate (gated tasks pile up at 0 on")
print("  several criteria at once), so the PASS subset is the honest test of separability.")
