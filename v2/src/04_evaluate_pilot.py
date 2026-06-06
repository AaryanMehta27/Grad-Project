"""
04_evaluate_pilot.py
====================
Runs the Pilot Test Evaluation Plan against scored_pilot_tasks.csv:
per-criterion score distributions, composite distribution, per-bucket
behaviour vs pre-locked thresholds, gate-frequency, and inter-criterion
correlation (with N=75 caveats). Also directly inspects the two watch-items
flagged from the smoke test: (1) Decomposability variance, (2) flattening of
digital tasks via Capability Match.

Read-only. Author: Aaryan Mehta. Created 03 June 2026.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data" / "processed" / "scored_pilot_tasks.csv")

CRIT = ["information_sufficiency_score", "objective_verifiability_score",
        "contextual_independence_score", "capability_match_score"]
SHORT = {"information_sufficiency_score": "InfoSuff", "objective_verifiability_score": "ObjVerif",
         "contextual_independence_score": "CtxIndep", "capability_match_score": "CapMatch"}

print("=" * 72)
print(f"PILOT EVALUATION  —  {len(d)} tasks   (PASS={sum(d.scoring_status=='PASS')}, "
      f"GATED={sum(d.scoring_status=='GATED')}, FAIL={sum(d.scoring_status=='TERMINAL_FAILURE')})")
print("=" * 72)

# --- 1. Per-criterion score distribution (the key dimensionality check) ---
print("\n[1] PER-CRITERION SCORE DISTRIBUTION (count of 0 / 1 / 2 across 75 tasks)")
print(f"    {'criterion':10s}   score=0   score=1   score=2    distinct values")
for c in CRIT:
    vc = d[c].value_counts().to_dict()
    n0, n1, n2 = vc.get(0, 0), vc.get(1, 0), vc.get(2, 0)
    distinct = sum(1 for n in (n0, n1, n2) if n > 0)
    flag = "  <-- LOW VARIANCE" if distinct == 1 else ""
    print(f"    {SHORT[c]:10s}   {n0:5d}    {n1:5d}    {n2:5d}        {distinct}{flag}")

# --- 2. Composite score distribution ---
print("\n[2] COMPOSITE SCORE DISTRIBUTION")
comp = d["composite_score"].astype(float)
print(f"    min={comp.min():.3f}  max={comp.max():.3f}  mean={comp.mean():.3f}  median={comp.median():.3f}")
print("    value counts (rounded to 3 dp):")
for val, n in sorted(comp.round(3).value_counts().to_dict().items()):
    bar = "#" * n
    print(f"      {val:.3f} : {n:2d}  {bar}")
distinct_comp = comp.round(3).nunique()
print(f"    distinct composite values: {distinct_comp}")

# --- 3. Per-bucket behaviour vs pre-locked thresholds ---
print("\n[3] PER-BUCKET BEHAVIOUR")
for b in sorted(d["pilot_bucket"].unique()):
    sub = d[d["pilot_bucket"] == b]
    n = len(sub)
    gated = sum(sub.scoring_status == "GATED")
    passed = sum(sub.scoring_status == "PASS")
    mean_c = sub["composite_score"].astype(float).mean()
    is0 = sum(sub["information_sufficiency_score"] == 0)
    hi = sum(sub["composite_score"].astype(float) >= 0.7)
    fp = sum(sub["composite_score"].astype(float) >= 0.5)
    print(f"\n  {b}  (n={n})")
    print(f"    PASS={passed}  GATED={gated}  mean_composite={mean_c:.3f}")
    print(f"    InfoSuff=0: {is0}/{n}   composite>=0.7: {hi}/{n}   composite>=0.5: {fp}/{n}")

# --- 4. Gate attribution: among GATED tasks, which criteria are 0 ---
print("\n[4] GATE ATTRIBUTION (among GATED tasks, how often each criterion = 0)")
gated = d[d.scoring_status == "GATED"]
print(f"    GATED tasks: {len(gated)}")
for c in CRIT:
    n = sum(gated[c] == 0)
    print(f"    {SHORT[c]:10s} = 0 in {n:2d}/{len(gated)} gated tasks")
# co-gating: how many criteria are simultaneously 0 in gated tasks
if len(gated):
    gated_zeros = (gated[CRIT] == 0).sum(axis=1)
    print(f"    criteria simultaneously 0 (per gated task): "
          f"mean={gated_zeros.mean():.2f}  "
          f"(1 only={sum(gated_zeros==1)}, 2={sum(gated_zeros==2)}, "
          f"3={sum(gated_zeros==3)}, 4={sum(gated_zeros==4)})")

# --- 5. Inter-criterion correlation (Spearman), full + bucket C ---
print("\n[5] INTER-CRITERION SPEARMAN CORRELATION")
print("    (N=75 -> wide confidence intervals; bucket-driven inflation in A/B; diagnostic only)")
print("    Full sample:")
corr = d[CRIT].corr(method="spearman")
print(corr.round(2).rename(index=SHORT, columns=SHORT).to_string())
cC = d[d.pilot_bucket == "C_ambiguous"]
if len(cC) >= 5:
    print(f"\n    Bucket C only (n={len(cC)}, the cleanest within-bucket signal):")
    print(cC[CRIT].corr(method="spearman").round(2).rename(index=SHORT, columns=SHORT).to_string())

# --- 6. Watch-item: do digital (un-gated) tasks show any spread? ---
print("\n[6] WATCH-ITEM: spread among NON-GATED (PASS) tasks")
passed = d[d.scoring_status == "PASS"]
print(f"    PASS tasks: {len(passed)}")
print(f"    composite distinct values among PASS: "
      f"{sorted(passed['composite_score'].astype(float).round(3).unique())}")
print(f"    CapMatch distribution among PASS: "
      f"{passed['capability_match_score'].value_counts().to_dict()}")
print(f"    (CapMatch=2 among PASS = {sum(passed.capability_match_score==2)}; "
      f"=1 = {sum(passed.capability_match_score==1)})")
