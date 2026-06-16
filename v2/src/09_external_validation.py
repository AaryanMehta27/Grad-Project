"""
09_external_validation.py
=========================
Validation tiers 3/5/6 (Section 3.4): correlate the occupation-level Generative
AI Exposure Index against published comparators, all sourced from Eloundou et
al.'s replication repo (data/raw/external/eloundou/):
  - Tier 3 (convergent): Eloundou et al. 2023 exposure (occ_level.csv;
    human_rating_beta = E1 human-labelled, dv_rating_beta = E1 model-labelled,
    *_gamma = E2 with-tools). Pre-locked: Spearman rho >= 0.55.
  - Tier 5 (mixed): Brynjolfsson-Mitchell-Rock SML (autoScores.csv: mSML).
  - Tier 6 (discriminant): Webb 2020 patent-based exposure (pct_ai/robot/software).
    Pre-locked: rho(Eloundou) - rho(Webb-AI) >= 0.15, computed on the common set.
  - Reference: Felten AIOE (felten_raj_seamans), Frey-Osborne (freyOsborne).
Spearman, unweighted across occupations, per the pre-registered design. Read-only.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "data" / "raw" / "external" / "eloundou" / "data"
ours = pd.read_csv(ROOT / "data" / "processed" / "occupation_exposure_index.csv")
ours["soc6"] = ours.onet_soc_code.str[:7]
elo = pd.read_csv(EXT / "occ_level.csv")
auto = pd.read_csv(EXT / "autoScores.csv").drop_duplicates("simpleOcc")

d = ours.merge(elo, left_on="onet_soc_code", right_on="O*NET-SOC Code", how="left")
d = d.merge(auto, left_on="soc6", right_on="simpleOcc", how="left")

COMP = [
    ("Eloundou E1 (human-labelled)", "human_rating_beta", "Tier 3 convergent"),
    ("Eloundou E1 (model-labelled)", "dv_rating_beta", "Tier 3 convergent"),
    ("Eloundou E2 with-tools (human)", "human_rating_gamma", "Tier 3 convergent"),
    ("Brynjolfsson SML", "mSML", "Tier 5 mixed"),
    ("Felten AIOE", "felten_raj_seamans", "reference"),
    ("Frey-Osborne computerisation", "freyOsborne", "reference"),
    ("Webb AI (patent, pre-LLM)", "pct_ai", "Tier 6 discriminant"),
    ("Webb software", "pct_software", "Tier 6 discriminant"),
    ("Webb robots", "pct_robot", "Tier 6 discriminant"),
]


def rho(a, b):
    m = pd.concat([a, b], axis=1).dropna()
    if len(m) < 10:
        return np.nan, np.nan, len(m)
    r, p = spearmanr(m.iloc[:, 0], m.iloc[:, 1])
    return r, p, len(m)


print("=" * 78)
print("EXTERNAL VALIDATION — occupation-level Spearman rho vs published comparators")
print("=" * 78)
print(f"{'comparator':32s} {'tier':20s} {'rho':>6s} {'n':>5s}  {'p':>9s}")
results = {}
for name, col, tier in COMP:
    if col not in d:
        print(f"{name:32s} {tier:20s}   MISSING COLUMN"); continue
    r, p, n = rho(ours.set_index("onet_soc_code").exposure_score.reindex(d.onet_soc_code).reset_index(drop=True), d[col])
    results[name] = (r, n)
    print(f"{name:32s} {tier:20s} {r:6.3f} {n:5d}  {p:9.2e}")

print("\n" + "-" * 78)
print("PRE-LOCKED DECISION CRITERIA")
print("-" * 78)
elo_full = results["Eloundou E1 (human-labelled)"][0]
print(f"  Tier 3 (convergent): rho(Eloundou E1 human) = {elo_full:.3f}   "
      f"[threshold >= 0.55  -> {'PASS' if elo_full>=0.55 else 'FAIL'}]")

# discriminant gap on the COMMON occupation set (where both Eloundou & Webb-AI exist)
common = d.dropna(subset=["human_rating_beta", "pct_ai"]).copy()
exp = ours.set_index("onet_soc_code").exposure_score
ce = exp.reindex(common.onet_soc_code).values
r_elo_c, _, _ = rho(pd.Series(ce), common["human_rating_beta"].reset_index(drop=True))
r_webb_c, _, _ = rho(pd.Series(ce), common["pct_ai"].reset_index(drop=True))
gap = r_elo_c - r_webb_c
print(f"  Tier 6 (discriminant), common set n={len(common)}:")
print(f"     rho(Eloundou)={r_elo_c:.3f}  rho(Webb-AI)={r_webb_c:.3f}  gap={gap:.3f}   "
      f"[threshold >= 0.15  -> {'PASS' if gap>=0.15 else 'FAIL'}]")

print("\n" + "-" * 78)
print("LARGEST DISAGREEMENTS vs Eloundou (rank difference) — for the 'why' analysis")
print("-" * 78)
dd = d.dropna(subset=["human_rating_beta"]).copy()
dd["our_rank"] = dd["exposure_score"].rank(ascending=False)
dd["elo_rank"] = dd["human_rating_beta"].rank(ascending=False)
dd["rank_gap"] = dd["our_rank"] - dd["elo_rank"]
print("  WE score MUCH higher than Eloundou (we say exposed, they don't):")
for _, r in dd.nsmallest(6, "rank_gap").iterrows():
    print(f"    ours={r.exposure_score:.2f} elo_E1={r.human_rating_beta:.2f}  {str(r.occupation_title)[:44]}")
print("  ELOUNDOU scores much higher than us:")
for _, r in dd.nlargest(6, "rank_gap").iterrows():
    print(f"    ours={r.exposure_score:.2f} elo_E1={r.human_rating_beta:.2f}  {str(r.occupation_title)[:44]}")

# save a tidy results table
pd.DataFrame([(n, results[n][0], results[n][1], t) for n, c, t in COMP if n in results],
             columns=["comparator", "spearman_rho", "n", "tier"]).to_csv(
    ROOT / "data" / "processed" / "external_validation_results.csv", index=False)
print("\nWritten: data/processed/external_validation_results.csv")
