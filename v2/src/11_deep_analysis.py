"""
11_deep_analysis.py
===================
Deeper inferences on the occupation ranking, leveraging the 4-criterion
decomposition. Read-only exploratory analysis feeding the findings in
Section 3.6 / Section 6. Sections:
  1. Exposure by SOC major group (which sectors)
  2. Exposure vs wage & employment (the GenAI 'high-skill' signature, vs robots)
  3. Latent / ungated cuts:
       (a) capability-frontier tasks  (IS=2 & CM=0): digital but beyond-now
       (b) embodiment-only-protected  (IS=0 & CM>=1): only the body protects them
  4. Barrier typology — dominant protective mechanism per occupation
  5. Technically-exposed but relationally-protected occupations
  6. Contextual-Independence immeasurability triangulation (alpha / kappa / R^2)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data" / "processed" / "scored_master_tasks_shuffled.csv")
d = d[d.scoring_status != "TERMINAL_FAILURE"].copy()
occ = pd.read_csv(ROOT / "data" / "processed" / "occupation_exposure_index.csv")
auto = pd.read_csv(ROOT / "data" / "raw" / "external" / "eloundou" / "data" / "autoScores.csv").drop_duplicates("simpleOcc")

SOC = {"11": "Management", "13": "Business & Financial", "15": "Computer & Math",
       "17": "Architecture & Engineering", "19": "Life/Physical/Social Science",
       "21": "Community & Social Service", "23": "Legal", "25": "Education & Library",
       "27": "Arts/Design/Media", "29": "Healthcare Practitioners", "31": "Healthcare Support",
       "33": "Protective Service", "35": "Food Prep & Serving", "37": "Building/Grounds Cleaning",
       "39": "Personal Care & Service", "41": "Sales", "43": "Office & Admin Support",
       "45": "Farming/Fishing/Forestry", "47": "Construction & Extraction",
       "49": "Installation/Maint/Repair", "51": "Production", "53": "Transportation & Moving"}
occ["grp"] = occ.onet_soc_code.str[:2].map(SOC)

print("=" * 78)
print("[1] EXPOSURE BY SOC MAJOR GROUP")
print("=" * 78)
g = occ.groupby("grp").agg(n=("exposure_score", "size"), mean=("exposure_score", "mean"),
                           sd=("exposure_score", "std")).sort_values("mean", ascending=False)
for grp, r in g.iterrows():
    print(f"  {r['mean']:.3f}  (sd {r['sd']:.2f}, n {int(r['n']):3d})  {grp}")

print("\n" + "=" * 78)
print("[2] EXPOSURE vs WAGE & EMPLOYMENT  (the GenAI high-skill signature)")
print("=" * 78)
occ["soc6"] = occ.onet_soc_code.str[:7]
w = occ.merge(auto[["simpleOcc", "a_mean", "tot_emp", "pct_robot", "pct_ai"]],
              left_on="soc6", right_on="simpleOcc", how="inner").dropna(subset=["a_mean"])
print(f"  n with wage data: {len(w)}")
print(f"  rho(our exposure, mean wage)      = {spearmanr(w.exposure_score, w.a_mean)[0]:+.3f}")
print(f"  rho(Webb-robots,  mean wage)      = {spearmanr(w.pct_robot, w.a_mean)[0]:+.3f}   (contrast: old automation)")
print(f"  rho(our exposure, employment)     = {spearmanr(w.exposure_score, w.tot_emp)[0]:+.3f}")
# employment-weighted exposure and share of employment in high-exposure jobs
ew = np.average(w.exposure_score, weights=w.tot_emp)
hi = w[w.exposure_score >= 0.6]
print(f"  employment-weighted mean exposure = {ew:.3f}  (unweighted {w.exposure_score.mean():.3f})")
print(f"  share of employment in exposure>=0.6 occupations = {hi.tot_emp.sum()/w.tot_emp.sum()*100:.1f}%  "
      f"({len(hi)} occupations)")
# wage quintiles
w["wage_q"] = pd.qcut(w.a_mean, 5, labels=["Q1 low", "Q2", "Q3", "Q4", "Q5 high"])
print("  mean exposure by wage quintile:")
for q, r in w.groupby("wage_q", observed=True).exposure_score.mean().items():
    print(f"     {q:8s}: {r:.3f}")

print("\n" + "=" * 78)
print("[3] LATENT / UNGATED CUTS")
print("=" * 78)
d["ungated"] = (d[["information_sufficiency_score", "objective_verifiability_score",
                   "contextual_independence_score", "capability_match_score"]].sum(axis=1)) / 8
fr = d[(d.information_sufficiency_score == 2) & (d.capability_match_score == 0)]
em = d[(d.information_sufficiency_score == 0) & (d.capability_match_score >= 1)]
print(f"(a) Capability-FRONTIER tasks (digital, IS=2, but beyond current model, CM=0): {len(fr)} "
      f"({len(fr)/len(d)*100:.1f}%)")
print("    these flip from gated->exposed as models improve. Examples:")
for _, r in fr.sample(min(6, len(fr)), random_state=1).iterrows():
    print(f"      {str(r.occupation_title)[:28]}: {str(r.task_text)[:52]}")
print(f"    top occupations by frontier-task count:")
for soc, c in fr.occupation_title.value_counts().head(5).items():
    print(f"      {c}x  {soc[:40]}")
print(f"\n(b) EMBODIMENT-ONLY-protected tasks (physical IS=0 but model could do output, CM>=1): {len(em)} "
      f"({len(em)/len(d)*100:.1f}%)")
print("    only the physical requirement protects these; vulnerable if the body is offloaded. Examples:")
for _, r in em.sample(min(6, len(em)), random_state=1).iterrows():
    print(f"      ungated={r.ungated:.2f}  {str(r.occupation_title)[:26]}: {str(r.task_text)[:46]}")
print("    occupations most reliant on embodiment-only protection:")
emo = em.occupation_title.value_counts().head(6)
for soc, c in emo.items():
    print(f"      {c}x  {soc[:42]}")

print("\n" + "=" * 78)
print("[4] BARRIER TYPOLOGY — dominant reason each occupation is NOT fully exposed")
print("=" * 78)
# decompose exposure loss per occupation
rows = []
for soc, grp in d.groupby("onet_soc_code"):
    gu = grp[grp.im_suppress.astype(str).str.upper() != "Y"]
    w_ = gu.im_weight.astype(float)
    phys = np.average((gu.information_sufficiency_score == 0).astype(float), weights=w_)
    cap = np.average(((gu.information_sufficiency_score != 0) & (gu.capability_match_score == 0)).astype(float), weights=w_)
    pas = gu[gu.scoring_status == "PASS"]
    ov_loss = ctx_loss = 0.0
    if len(pas):
        wp = pas.im_weight.astype(float)
        ov_loss = np.average((2 - pas.objective_verifiability_score) / 8, weights=wp) * (len(pas)/len(gu))
        ctx_loss = np.average((2 - pas.contextual_independence_score) / 8, weights=wp) * (len(pas)/len(gu))
    losses = {"physical gate": phys, "capability gate": cap, "verifiability": ov_loss, "relational": ctx_loss}
    dominant = max(losses, key=losses.get)
    exp = occ.loc[occ.onet_soc_code == soc, "exposure_score"].iloc[0]
    rows.append({"soc": soc, "title": grp.occupation_title.iloc[0], "exposure": exp,
                 "dominant_barrier": dominant if exp < 0.85 else "(little protection / exposed)"})
typ = pd.DataFrame(rows)
print("  occupations by dominant protective barrier:")
print(typ.dominant_barrier.value_counts().to_string())

print("\n" + "=" * 78)
print("[5] TECHNICALLY EXPOSED but RELATIONALLY PROTECTED  (PASS, high IS+CM, low CtxI)")
print("=" * 78)
po = d[d.scoring_status == "PASS"].groupby("onet_soc_code").agg(
    title=("occupation_title", "first"), n=("composite_score", "size"),
    IS=("information_sufficiency_score", "mean"), CM=("capability_match_score", "mean"),
    CtxI=("contextual_independence_score", "mean"))
po = po[(po.n >= 5) & (po.IS >= 1.9) & (po.CM >= 1.2) & (po.CtxI <= 0.9)].sort_values("CtxI")
print(f"  {len(po)} occupations are digitally-capable yet relationship-protected. Top examples:")
for _, r in po.head(12).iterrows():
    print(f"      CtxI={r.CtxI:.2f} CM={r.CM:.2f}  {str(r.title)[:46]}")

print("\n" + "=" * 78)
print("[6] CONTEXTUAL-INDEPENDENCE IMMEASURABILITY — triangulation")
print("=" * 78)
print("  Three independent signals all flag CtxI as the least measurable dimension:")
print("    human-human agreement (Krippendorff alpha): IS 0.67 | OV 0.40 | CtxI 0.40 | CM 0.68")
print("    human-model agreement (Cohen kappa):        IS ~0.60| OV ~0.39| CtxI ~0.18| CM ~0.24")
print("    text-decodability (BERT R^2):               IS 0.61 | OV 0.63 | CtxI 0.46 | CM 0.60")
print("  -> CtxI is jointly the noisiest across raters AND the least surface-predictable: the")
print("     social/tacit barrier (Polanyi/Autor 2015) is intrinsically hard to measure, which is")
print("     itself a finding about where the automation frontier genuinely sits.")
