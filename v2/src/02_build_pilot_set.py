"""
02_build_pilot_set.py
=====================

Builds the curated pilot-test sample (~75 tasks) for validating the rubric
prompt before the full scoring run, per docs/data_documentation.md Section 3.8.

UNLIKE the production scoring or the Tier-2 validity sample, this selection is
DELIBERATELY curated, not random. The pilot's purpose is to stress-test the
prompt on known-difficult cases, so "selection bias" is intentional here.

Four buckets:
  A. Expected uniformly HIGH (20) — clearly digital, decomposable, AI-tractable.
  B. Expected uniformly LOW / zero-gated (20) — physical, embodied, in-person.
  C. Deliberately AMBIGUOUS physical/digital (20) — verbs like monitor/inspect/
     examine/observe/review that test whether the disambiguation rule fires.
  D. MIXED (15) — spread across Core/Supplemental and Incumbent/Analyst and
     a range of survey dates, to surface any systematic misinterpretation.

Reproducible: fixed seed, capped per occupation for variety. Output saved to
data/processed/pilot_tasks.csv with a bucket label and an expected-behaviour
note for each task, so the manual review has a clear baseline to check against.

Author: Aaryan Mehta
Created: 23 May 2026
"""

import sys
import re
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from pathlib import Path

SEED = 20260523
ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "processed" / "master_tasks.csv")
df["task_text"] = df["task_text"].astype(str)
df["occupation_title"] = df["occupation_title"].astype(str)

selected_ids = set()

def occ_match(frame, patterns):
    pat = "|".join(re.escape(p) for p in patterns)
    return frame[frame["occupation_title"].str.contains(pat, case=False, regex=True)]

def firstword_match(frame, verbs):
    pat = r"^\s*(?:" + "|".join(verbs) + r")\b"  # non-capturing group avoids pandas warning
    return frame[frame["task_text"].str.contains(pat, case=False, regex=True)]

def pick(pool, n, cap_per_occ=2):
    """Shuffle (seeded) and greedily pick up to n, capping tasks per occupation."""
    pool = pool[~pool["task_id"].isin(selected_ids)]
    pool = pool.sample(frac=1, random_state=SEED)
    chosen, occ_count = [], {}
    for _, r in pool.iterrows():
        if len(chosen) >= n:
            break
        o = r["occupation_title"]
        if occ_count.get(o, 0) >= cap_per_occ:
            continue
        chosen.append(r)
        occ_count[o] = occ_count.get(o, 0) + 1
        selected_ids.add(r["task_id"])
    return pd.DataFrame(chosen)

# ---- Bucket A: expected HIGH -------------------------------------------------
high_occ = ["Software Developer", "Computer Programmer", "Web Developer",
            "Data Scientist", "Database Administrator", "Database Architect",
            "Statistician", "Accountant", "Auditor", "Financial Analyst",
            "Financial and Investment", "Technical Writer", "Editor",
            "Interpreter", "Translator", "Market Research Analyst", "Actuar",
            "Proofreader", "Bookkeeping", "Budget Analyst", "Credit Analyst",
            "Tax Preparer"]
high_verbs = ["write", "develop", "code", "program", "analyze", "compile",
              "prepare", "draft", "summarize", "translate", "calculate",
              "edit", "proofread", "create", "compute", "review", "compose",
              "generate", "document", "design"]
A = pick(firstword_match(occ_match(df, high_occ), high_verbs), 20, cap_per_occ=2)
A["pilot_bucket"] = "A_expected_high"
A["expected"] = "all four criteria near 2; composite high"

# ---- Bucket B: expected LOW / zero-gated ------------------------------------
phys_occ = ["Surgeon", "Registered Nurse", "Nursing Assistant",
            "Physical Therapist", "Massage Therapist", "Firefighter",
            "Emergency Medical", "Paramedic", "Construction Laborer",
            "Electrician", "Plumber", "Carpenter", "Automotive Service",
            "Welder", "Dental Hygienist", "Dental Assistant",
            "Childcare Worker", "Home Health Aide", "Cook", "Chef",
            "Roofer", "Painter", "Brickmason", "Maintenance and Repair"]
phys_verbs = ["operate", "administer", "lift", "install", "repair", "assemble",
              "clean", "cut", "build", "drive", "apply", "remove", "position",
              "feed", "bathe", "dress", "cook", "weld", "paint", "connect",
              "mount", "perform", "measure", "move", "load"]
B = pick(firstword_match(occ_match(df, phys_occ), phys_verbs), 20, cap_per_occ=2)
B["pilot_bucket"] = "B_expected_low"
B["expected"] = "Information Sufficiency = 0 (physical); composite gated to 0"

# ---- Bucket C: deliberately AMBIGUOUS ---------------------------------------
ambig_verbs = ["Monitor", "Inspect", "Examine", "Observe", "Review",
               "Assess", "Evaluate", "Verify", "Check", "Measure"]
C = pick(firstword_match(df, ambig_verbs), 20, cap_per_occ=1)
C["pilot_bucket"] = "C_ambiguous"
C["expected"] = "disambiguation rule should resolve to digital implementation where plausible"

# ---- Bucket D: MIXED (Core/Supplemental, Incumbent/Analyst, varied dates) ----
remaining = df[~df["task_id"].isin(selected_ids)]
d_unrated = pick(remaining[remaining["task_type"] == "Unrated"], 5, cap_per_occ=1)
d_supp = pick(remaining[remaining["task_type"] == "Supplemental"], 5, cap_per_occ=1)
d_core = pick(remaining[(remaining["task_type"] == "Core") &
                        (remaining["domain_source"] == "Incumbent")], 5, cap_per_occ=1)
D = pd.concat([d_unrated, d_supp, d_core])
D["pilot_bucket"] = "D_mixed"
D["expected"] = "no fixed expectation; checks for systematic misinterpretation"

# ---- Assemble ---------------------------------------------------------------
cols = ["pilot_bucket", "expected", "task_id", "onet_soc_code",
        "occupation_title", "task_text", "task_type", "domain_source",
        "task_date", "survey_date"]
pilot = pd.concat([A, B, C, D])[cols].reset_index(drop=True)

out = ROOT / "data" / "processed" / "pilot_tasks.csv"
pilot.to_csv(out, index=False, encoding="utf-8")

# ---- Summary ----------------------------------------------------------------
print(f"Pilot set built: {len(pilot)} tasks  (seed={SEED})")
print(f"Saved to: {out}")
print()
for b, label in [("A_expected_high", "A  Expected HIGH"),
                 ("B_expected_low", "B  Expected LOW / gated"),
                 ("C_ambiguous", "C  Ambiguous"),
                 ("D_mixed", "D  Mixed")]:
    sub = pilot[pilot["pilot_bucket"] == b]
    print(f"{label}: {len(sub)} tasks, {sub['occupation_title'].nunique()} distinct occupations")
print()
print("Domain source spread:", pilot["domain_source"].value_counts().to_dict())
print("Task type spread:", pilot["task_type"].value_counts().to_dict())
