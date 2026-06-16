"""
07_aggregate_occupations.py
===========================
Occupation-level aggregation of the task-level Generative AI Exposure Index
(Outputs A, B, C of Section 3.6), from data/processed/scored_master_tasks_shuffled.csv.

For each of the 923 occupations:
  - Output A: exposure score = IM-weighted mean of task composite scores.
              (Analyst-coded tasks already carry the within-occupation mean IM,
               im_weight_imputed=Y; the 29 all-analyst occupations therefore get
               an effectively unweighted mean — flagged via weighting_mode.)
  - Output B: within-occupation dispersion = IM-weighted SD of composites.
  - Output C: barrier decomposition — IM-weighted share gated by Information
              Sufficiency (physical) vs. Capability Match (capability), and the
              mean Objective-Verifiability / Contextual-Independence modulation
              among non-gated tasks.
  - Data-quality flags: task counts, gated counts, analyst-imputed counts,
              survey N / date, small-occupation flag (<=6 tasks), weighting_mode.
Plus a robustness exposure recomputed WITHOUT analyst-imputed tasks (Section 6.10).

im_suppress == 'Y' tasks are excluded from weighting (Section 3.7). TERMINAL_FAILURE
tasks are excluded from the index (there are none in this run).

Output: data/processed/occupation_exposure_index.csv (923 rows). Author: Aaryan Mehta.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data" / "processed" / "scored_master_tasks_shuffled.csv")

# --- index inclusion rules ------------------------------------------------
d = d[d["scoring_status"] != "TERMINAL_FAILURE"].copy()      # exclude failures (none here)
d["composite_score"] = d["composite_score"].astype(float)
d["im_weight"] = d["im_weight"].astype(float)
d["_use"] = d["im_suppress"].astype(str).str.upper() != "Y"  # exclude suppressed from weighting
d["_analyst"] = d["im_weight_imputed"].astype(str).str.upper() == "Y"
d["_is_gate"] = d["information_sufficiency_score"] == 0
d["_cm_gate"] = d["capability_match_score"] == 0
d["_pass"] = d["scoring_status"] == "PASS"


def wmean(x, w):
    w = np.asarray(w, float); x = np.asarray(x, float)
    return np.nan if w.sum() == 0 else np.average(x, weights=w)


def wsd(x, w):
    w = np.asarray(w, float); x = np.asarray(x, float)
    if w.sum() == 0 or len(x) < 2:
        return np.nan
    m = np.average(x, weights=w)
    return float(np.sqrt(np.average((x - m) ** 2, weights=w)))


rows = []
for soc, g in d.groupby("onet_soc_code"):
    gu = g[g["_use"]]                      # tasks used in weighting
    w, x = gu["im_weight"], gu["composite_score"]
    pass_g = gu[gu["_pass"]]
    # robustness: exposure without analyst-imputed tasks
    gna = gu[~gu["_analyst"]]
    rows.append({
        "onet_soc_code": soc,
        "occupation_title": g["occupation_title"].iloc[0],
        "n_tasks": len(g),
        "exposure_score": wmean(x, w),
        "dispersion_sd": wsd(x, w),
        "weighting_mode": g["weighting_mode"].iloc[0],
        # Output C — gates (IM-weighted share); IS=0 and CM=0 overlap heavily, so
        # also report the "pure capability gate": digital yet beyond capability.
        "share_gated": wmean((gu["composite_score"] == 0).astype(float), w),
        "share_phys_gate": wmean(gu["_is_gate"].astype(float), w),
        "share_capability_gate_digital": wmean((~gu["_is_gate"] & gu["_cm_gate"]).astype(float), w),
        # Output C — modulators among non-gated tasks (0..2; lower = pulls exposure down more)
        "passtasks": len(pass_g),
        "mean_objverif_pass": wmean(pass_g["objective_verifiability_score"], pass_g["im_weight"]) if len(pass_g) else np.nan,
        "mean_ctxindep_pass": wmean(pass_g["contextual_independence_score"], pass_g["im_weight"]) if len(pass_g) else np.nan,
        # robustness
        "exposure_no_analyst": wmean(gna["composite_score"], gna["im_weight"]) if len(gna) else np.nan,
        # data-quality flags
        "n_gated": int((g["composite_score"] == 0).sum()),
        "n_analyst_imputed": int(g["_analyst"].sum()),
        "n_suppressed": int((~g["_use"]).sum()),
        "survey_n": g["survey_n"].iloc[0],
        "survey_date": g["survey_date"].iloc[0],
        "small_occ_flag": len(g) <= 6,
    })

occ = pd.DataFrame(rows).sort_values("exposure_score", ascending=False).reset_index(drop=True)
occ["exposure_rank"] = range(1, len(occ) + 1)
out = ROOT / "data" / "processed" / "occupation_exposure_index.csv"
cols = ["exposure_rank", "onet_soc_code", "occupation_title", "exposure_score", "dispersion_sd",
        "n_tasks", "passtasks", "share_gated", "share_phys_gate", "share_capability_gate_digital",
        "mean_objverif_pass", "mean_ctxindep_pass", "exposure_no_analyst", "weighting_mode",
        "n_gated", "n_analyst_imputed", "n_suppressed", "small_occ_flag", "survey_n", "survey_date"]
occ[cols].to_csv(out, index=False, encoding="utf-8")

# ============================ REPORT ============================
print("=" * 74)
print(f"OCCUPATION-LEVEL EXPOSURE INDEX  —  {len(occ)} occupations")
print("=" * 74)
es = occ["exposure_score"]
print(f"exposure: mean {es.mean():.3f}  median {es.median():.3f}  sd {es.std():.3f}  "
      f"min {es.min():.3f}  max {es.max():.3f}")
print(f"weighting_mode: {occ.weighting_mode.value_counts().to_dict()}")
print(f"small occupations (<=6 tasks): {int(occ.small_occ_flag.sum())}  | "
      f"occupations with analyst-imputed tasks: {int((occ.n_analyst_imputed>0).sum())}")
print()
print("TOP 15 — most AI-exposed occupations")
for _, r in occ.head(15).iterrows():
    print(f"  {r.exposure_rank:3d}. {r.exposure_score:.3f}  {r.occupation_title[:52]}")
print()
print("BOTTOM 15 — least exposed")
for _, r in occ.tail(15).iterrows():
    print(f"  {r.exposure_rank:3d}. {r.exposure_score:.3f}  {r.occupation_title[:52]}")
print()
print("HIGHEST within-occupation dispersion (mixed exposure profiles)")
for _, r in occ.sort_values("dispersion_sd", ascending=False).head(8).iterrows():
    print(f"  sd={r.dispersion_sd:.3f} exp={r.exposure_score:.3f}  {r.occupation_title[:48]}")
print()
print("ROBUSTNESS — exposure with vs without analyst-imputed tasks")
both = occ.dropna(subset=["exposure_no_analyst"])
rho = both["exposure_score"].corr(both["exposure_no_analyst"], method="spearman")
both = both.assign(delta=(both.exposure_score - both.exposure_no_analyst).abs())
print(f"  Spearman rho(full, no-analyst) = {rho:.4f}  over {len(both)} occupations with non-analyst tasks")
print(f"  occupations excluded entirely (all-analyst): {len(occ)-len(both)}")
print(f"  mean |delta| = {both.delta.mean():.4f}  | occupations moving >0.05: {int((both.delta>0.05).sum())}")
print()
print("BARRIER MIX (corpus, IM-weighted occupation means)")
print(f"  mean share physically gated (IS=0):           {occ.share_phys_gate.mean():.3f}")
print(f"  mean share capability-gated while digital:    {occ.share_capability_gate_digital.mean():.3f}")
print(f"  among non-gated tasks: mean ObjVerif {occ.mean_objverif_pass.mean():.2f}/2, "
      f"mean CtxIndep {occ.mean_ctxindep_pass.mean():.2f}/2")
print()
print(f"Written: {out}")
