"""
02b_build_smoke_set.py
======================

Builds the 10-task smoke-test set used to validate the scoring pipeline
end-to-end before spending real money on the pilot.

The smoke test exists to confirm: the API key works, the JSONL is built
correctly, the Batch submission and polling work, the output downloads,
the JSON parses against the schema, the retry logic fires correctly on
any induced failure, and the scored CSV is written cleanly. It does NOT
evaluate prompt quality — that is the pilot's job.

To avoid any overlap between smoke and pilot (which would make the
pilot's blind review slightly less clean), tasks already selected for
the pilot are excluded. A fixed seed makes the selection reproducible.
Per-occupation cap of 1 ensures variety.

Author: Aaryan Mehta
Created: 23 May 2026
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from pathlib import Path

SEED = 20260524  # one off the pilot's seed; ensures independent draw
ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"

df = pd.read_csv(PROC / "master_tasks.csv")
pilot = pd.read_csv(PROC / "pilot_tasks.csv")

# Exclude any task already in the pilot
remaining = df[~df["task_id"].isin(pilot["task_id"])]

# Shuffle and greedily pick 10 with a per-occupation cap of 1 for variety
shuffled = remaining.sample(frac=1, random_state=SEED)
chosen, seen_occ = [], set()
for _, r in shuffled.iterrows():
    if len(chosen) >= 10:
        break
    if r["occupation_title"] in seen_occ:
        continue
    chosen.append(r)
    seen_occ.add(r["occupation_title"])

smoke = pd.DataFrame(chosen)[
    ["task_id", "onet_soc_code", "occupation_title", "task_text",
     "task_type", "domain_source", "task_date"]
].reset_index(drop=True)

out = PROC / "smoke_test_tasks.csv"
smoke.to_csv(out, index=False, encoding="utf-8")
print(f"Smoke-test set written: {out}  ({len(smoke)} tasks, seed={SEED})")
print()
for _, r in smoke.iterrows():
    print(f"  task_id={r.task_id}  [{r.occupation_title}]")
    print(f"    {r.task_text}")
