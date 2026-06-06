"""
02c_shuffle_master.py
=====================
Produce master_tasks_shuffled.csv: a fixed-seed random permutation of
master_tasks.csv. This becomes the input for BOTH (a) the pre-run validation
pool and (b) the full production run, so that nothing is wasted:

  - Because the rows are randomly ordered, ANY prefix of the file is a
    representative random sample of the corpus. Scoring the first chunk now
    (until the available credit runs out) yields the stratified Tier-2 human
    validity sample.
  - The SAME file is the full-run input. Re-running the scorer on it after a
    top-up resumes from the checkpoint and finishes the remaining tasks, so the
    validation-pool scores are simply the first part of the full run — not a
    throwaway. The 100 rated tasks therefore carry their FINAL scores (they are
    never re-scored).

Row order has no effect on any result: scores are keyed by task_id and the index
is aggregated per occupation afterwards. Shuffling only changes the sequence in
which tasks are sent to the API.

Reproducible: fixed seed. Re-running reproduces byte-identical output.

Author: Aaryan Mehta. Created 06 June 2026.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from pathlib import Path

SEED = 20260606  # fixed for reproducibility (date-based, arbitrary)

ROOT = Path(__file__).resolve().parent.parent
src = ROOT / "data" / "processed" / "master_tasks.csv"
dst = ROOT / "data" / "processed" / "master_tasks_shuffled.csv"

df = pd.read_csv(src)
shuffled = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

# Sanity: it must be a pure permutation — same rows, same task_ids, nothing lost.
assert len(shuffled) == len(df), "row count changed"
assert set(shuffled["task_id"]) == set(df["task_id"]), "task_id set changed"
assert sorted(shuffled.columns) == sorted(df.columns), "columns changed"

shuffled.to_csv(dst, index=False, encoding="utf-8")

print(f"Wrote {dst.name}")
print(f"  rows: {len(shuffled)}  (permutation of {src.name}, seed={SEED})")
print(f"  columns: {list(shuffled.columns)}")
print(f"  first 8 task_ids in run order: {list(shuffled['task_id'].head(8))}")
print(f"  occupations represented in first 700 rows: "
      f"{shuffled.head(700)['occupation_title'].nunique()} of {df['occupation_title'].nunique()}")
