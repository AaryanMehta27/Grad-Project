"""
01_build_master_file.py
========================

Preprocessing Step 1 — Build the Master Task File

This script merges four O*NET 30.2 input files into a single master task-level
file that serves as the input to the LLM rubric scoring pipeline. The schema
is defined in docs/data_documentation.md, Section 3.7.

Inputs (read from data/raw/onet/):
  - Occupation Data.xlsx              (1,016 rows: occupation reference)
  - Task Statements.xlsx              (18,796 rows: task text and metadata)
  - Task Ratings.xlsx                 (161,559 rows: IM, RT, FT scales)
  - Occupation Level Metadata.xlsx    (32,202 rows: per-occupation provenance)

Outputs (written to data/processed/):
  - master_tasks.csv                  (one row per task, all metadata merged)
  - master_tasks_summary.txt          (human-readable summary log of what was built)

Operations performed (in order):
  1. Load Occupation Data — provides occupation titles and descriptions.
  2. Load Task Statements — the primary table; 18,796 task rows.
  3. Load Task Ratings — extract IM (Importance, 1-5) and RT (Relevance, 0-100)
     scales only. Discard FT (Frequency) which is 7 rows per task and not used
     in the primary index.
  4. Load Occupation Level Metadata — extract Total Completed Questionnaires
     and Date per occupation. Used only as informational columns in the master
     file (per Section 2.5: no sample size or date cutoffs are applied).
  5. Merge all four tables on appropriate keys.
  6. Apply the Recommend Suppress = Y exclusion (O*NET's own data quality flag,
     per Section 2.5 Rule 3): rows with im_suppress = Y are NOT used in
     downstream weighting. We keep them in the master file for audit transparency
     but flag them so the aggregation step excludes them.
  7. Impute IM weights for analyst-coded tasks (Task Type = None) using
     within-occupation mean IM, per Section 3.2 corrected treatment. For the
     29 occupations where every task is analyst-coded (no IM-rated tasks
     anywhere), use corpus-wide mean IM and flag the occupation with
     weighting_mode = "unweighted".
  8. Reorder columns to match the Section 3.7 schema and save.

Imputation logic — three cases:
  Case A — Task has its own IM rating (im_suppress=N): use as-is. im_weight_imputed=N.
  Case B — Task has its own IM rating but suppressed (im_suppress=Y): keep the
          value for audit but the aggregation step excludes these. im_weight_imputed=N.
  Case C — Task has no IM rating at all (analyst-coded, Task Type = None):
          impute with within-occupation mean IM (excluding suppressed rows).
          im_weight_imputed=Y. For the 29 occupations with no IM-rated tasks
          at all, use corpus-wide mean IM and set weighting_mode="unweighted".

The within-occupation mean used for imputation is computed *excluding* suppressed
rows, so suppressed observations do not influence the imputed values.

This script is deterministic. It can be re-run any time and will produce the
same output given the same inputs.

Author: Aaryan Mehta
Created: 10 May 2026
"""

import sys
from pathlib import Path

import pandas as pd

# Ensure UTF-8 output on Windows so the printed log handles all task text correctly
sys.stdout.reconfigure(encoding="utf-8")

# =========================================================================
# Path setup — derive everything from the script location for portability
# =========================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "onet"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "master_tasks.csv"
LOG_FILE = OUT_DIR / "master_tasks_summary.txt"

# We capture every print call into a log so the audit trail is preserved
# alongside the output file. The aggregation script and any downstream
# analysis can refer back to this log for the exact preprocessing state.
log_lines = []


def log(msg: str = "") -> None:
    """Print to console and capture to log."""
    print(msg)
    log_lines.append(msg)


log("=" * 70)
log("Preprocessing Step 1 — Build Master Task File")
log("=" * 70)
log(f"Script: {Path(__file__).name}")
log(f"Project root: {PROJECT_ROOT}")
log(f"Raw data: {RAW_DIR}")
log(f"Output: {OUT_DIR}")
log("")

# =========================================================================
# Step 1 — Load Occupation Data (1,016 occupation reference rows)
# =========================================================================
log("[Step 1] Loading Occupation Data.xlsx ...")
occ = pd.read_excel(RAW_DIR / "Occupation Data.xlsx")
log(f"  Rows loaded: {len(occ):,}")
log(f"  Columns: {list(occ.columns)}")

# Rename to snake_case for consistency throughout the pipeline
occ = occ.rename(columns={
    "O*NET-SOC Code": "onet_soc_code",
    "Title": "occupation_title",
    "Description": "occupation_description",
})
log(f"  After rename: {list(occ.columns)}")
log("")

# =========================================================================
# Step 2 — Load Task Statements (18,796 task rows)
# =========================================================================
log("[Step 2] Loading Task Statements.xlsx ...")
tasks = pd.read_excel(RAW_DIR / "Task Statements.xlsx")
log(f"  Rows loaded: {len(tasks):,}")
log(f"  Unique occupations with tasks: {tasks['O*NET-SOC Code'].nunique():,}")
log(f"  Task Type breakdown:")
for ttype, cnt in tasks["Task Type"].fillna("None").value_counts().items():
    log(f"    {ttype}: {cnt:,}")
log(f"  Domain Source breakdown:")
for ds, cnt in tasks["Domain Source"].value_counts().items():
    log(f"    {ds}: {cnt:,}")

# Rename to snake_case and select only the columns we need
tasks = tasks.rename(columns={
    "O*NET-SOC Code": "onet_soc_code",
    "Task ID": "task_id",
    "Task": "task_text",
    "Task Type": "task_type",
    "Date": "task_date",
    "Domain Source": "domain_source",
})
tasks = tasks[[
    "onet_soc_code", "task_id", "task_text",
    "task_type", "task_date", "domain_source",
]]

# Normalise Task Type so missing values are explicit. The 845 analyst-coded
# tasks have a missing Task Type in the source file. We deliberately use
# "Unrated" (not "None") as the sentinel string because "None" appears in
# pandas' default na_values list — pd.read_csv would silently re-parse it
# back to NaN, defeating the purpose of having an explicit value. "Unrated"
# is descriptive, not in any default null sentinel list, and survives a CSV
# round-trip cleanly. This deviation from O*NET's native representation
# (which uses an empty cell) is documented in data_documentation.md
# Section 1.2 and Section 3.7.
tasks["task_type"] = tasks["task_type"].fillna("Unrated")
log("")

# =========================================================================
# Step 3 — Load Task Ratings, extract IM and RT scales
# =========================================================================
log("[Step 3] Loading Task Ratings.xlsx ...")
ratings = pd.read_excel(RAW_DIR / "Task Ratings.xlsx")
log(f"  Rows loaded: {len(ratings):,}")
log(f"  Scale breakdown:")
for sid, cnt in ratings["Scale ID"].value_counts().items():
    log(f"    {sid}: {cnt:,}")

# Total suppressed rows across all scales (for audit log)
total_suppressed = (ratings["Recommend Suppress"] == "Y").sum()
log(f"  Recommend Suppress = Y (total across scales): {total_suppressed}")

# IM scale — Importance, 1 to 5, one row per task that has been surveyed
im = ratings.loc[
    ratings["Scale ID"] == "IM",
    ["Task ID", "Data Value", "Recommend Suppress"]
].copy()
im = im.rename(columns={
    "Task ID": "task_id",
    "Data Value": "im_weight",
    "Recommend Suppress": "im_suppress",
})
log(f"  IM rows extracted: {len(im):,}")
log(f"    of which suppressed: {(im['im_suppress'] == 'Y').sum():,}")

# RT scale — Relevance of Task, 0 to 100, one row per task that has been surveyed
rt = ratings.loc[
    ratings["Scale ID"] == "RT",
    ["Task ID", "Data Value", "Recommend Suppress"]
].copy()
rt = rt.rename(columns={
    "Task ID": "task_id",
    "Data Value": "rt_value",
    "Recommend Suppress": "rt_suppress",
})
log(f"  RT rows extracted: {len(rt):,}")
log(f"    of which suppressed: {(rt['rt_suppress'] == 'Y').sum():,}")

# FT scale (Frequency) is intentionally NOT extracted. Per Section 1.4 it is a
# distribution across 7 categories per task and is not used in the primary
# index. It would add 7 rows per task and is reserved for a possible
# supplementary analysis only.
log("  FT scale NOT extracted (not used in primary index — see Section 1.4)")
log("")

# =========================================================================
# Step 4 — Load Occupation Level Metadata, extract N and Date
# =========================================================================
log("[Step 4] Loading Occupation Level Metadata.xlsx ...")
metadata = pd.read_excel(RAW_DIR / "Occupation Level Metadata.xlsx")
log(f"  Rows loaded: {len(metadata):,}")
log(f"  Distinct occupations with metadata: {metadata['O*NET-SOC Code'].nunique():,}")

# Filter to the single Item we need: Total Completed Questionnaires.
# This gives one row per occupation with its survey N and Date.
n_data = metadata.loc[
    metadata["Item"] == "Total Completed Questionnaires",
    ["O*NET-SOC Code", "N", "Date"]
].copy()
n_data = n_data.rename(columns={
    "O*NET-SOC Code": "onet_soc_code",
    "N": "survey_n",
    "Date": "survey_date",
})

# In case an occupation has multiple "Total Completed Questionnaires" rows
# (rare but possible — happens when an occupation has been surveyed more
# than once and both records are retained), keep the most recent.
n_data = n_data.sort_values("survey_date").drop_duplicates(
    "onet_soc_code", keep="last"
)
log(f"  Occupations with Total Completed Questionnaires: {len(n_data):,}")
log(f"  Survey N range: {int(n_data['survey_n'].min())} to {int(n_data['survey_n'].max())}")
log(f"  Survey N median: {n_data['survey_n'].median():.1f}")

# Survey dates are MM/YYYY strings. Parse them to a proper datetime so the
# reported range is chronological rather than lexicographic. The string is
# kept in the master file as-is (matches O*NET's native format and the
# Section 3.7 schema), but for log reporting we need correct ordering.
_dates_parsed = pd.to_datetime(n_data["survey_date"], format="%m/%Y", errors="coerce")
log(f"  Survey date range (chronological): "
    f"{_dates_parsed.min().strftime('%m/%Y')} to {_dates_parsed.max().strftime('%m/%Y')}")
log(f"  Survey year distribution:")
_year_counts = _dates_parsed.dt.year.value_counts().sort_index()
for year, cnt in _year_counts.items():
    log(f"    {int(year)}: {cnt}")
log("")

# =========================================================================
# Step 5 — Merge all four tables onto Task Statements as the spine
# =========================================================================
log("[Step 5] Merging all tables ...")

# Start with task statements (the spine: 18,796 rows)
master = tasks.copy()
log(f"  Spine: {len(master):,} task rows")

# Add occupation title and description (left join — every task has an occupation)
master = master.merge(occ, on="onet_soc_code", how="left")
n_missing_occ = master["occupation_title"].isna().sum()
log(f"  After merging Occupation Data: {len(master):,} rows, missing occupation info for {n_missing_occ}")

# Add IM weight (left join — analyst-coded tasks have no row in IM scale)
master = master.merge(im, on="task_id", how="left")
n_with_im = master["im_weight"].notna().sum()
log(f"  After merging IM ratings: {n_with_im:,} tasks have IM weights ({len(master) - n_with_im:,} do not)")

# Add RT value (left join — same pattern)
master = master.merge(rt, on="task_id", how="left")
n_with_rt = master["rt_value"].notna().sum()
log(f"  After merging RT values: {n_with_rt:,} tasks have RT values")

# Add survey N and date (left join — the 45 analyst-only occupations may not have metadata)
master = master.merge(n_data, on="onet_soc_code", how="left")
n_missing_meta = master["survey_n"].isna().sum()
log(f"  After merging Occupation Metadata: missing N/Date for {n_missing_meta:,} task rows")
log("")

# =========================================================================
# Step 6 — IM imputation for analyst-coded tasks
# =========================================================================
log("[Step 6] IM weight imputation ...")
log("  Imputation logic per Section 3.2 (corrected treatment):")
log("  - Tasks with their own IM rating: use as-is")
log("  - Tasks with no IM rating (analyst-coded): impute within-occupation mean IM,")
log("    excluding suppressed rows from the mean calculation")
log("  - Occupations with NO IM-rated tasks at all (29 occupations): fall back to")
log("    corpus-wide mean IM, flag occupation as weighting_mode='unweighted'")
log("")

# Compute within-occupation mean IM, excluding suppressed rows so they do not
# bias the imputation. Suppressed rows are flagged for low data precision —
# their values should not influence the imputed weight either.
non_suppressed_mask = (master["im_suppress"] != "Y") & master["im_weight"].notna()
occ_mean_im = (
    master.loc[non_suppressed_mask]
    .groupby("onet_soc_code")["im_weight"]
    .mean()
)
corpus_mean_im = master.loc[non_suppressed_mask, "im_weight"].mean()
log(f"  Within-occupation mean IM available for {len(occ_mean_im):,} occupations")
log(f"  Corpus-wide mean IM (excluding suppressed): {corpus_mean_im:.4f}")

# Identify occupations with zero IM-rated tasks (these need the corpus-wide fallback)
all_occupations = set(master["onet_soc_code"].unique())
occupations_with_im = set(occ_mean_im.index)
occupations_without_im = sorted(all_occupations - occupations_with_im)
log(f"  Occupations with at least one IM-rated task: {len(occupations_with_im):,}")
log(f"  Occupations with zero IM-rated tasks (require corpus-wide fallback): "
    f"{len(occupations_without_im):,}")

# Set up the imputation flag column: N by default, Y for tasks where we impute
master["im_weight_imputed"] = "N"

# Identify tasks that need imputation: tasks where im_weight is missing
# (these are exactly the analyst-coded tasks with Task Type = None).
# Tasks that are present-but-suppressed (im_suppress=Y) are NOT imputed —
# we keep the suppressed value in im_weight for audit transparency, and
# the aggregation step will exclude them via the im_suppress flag.
needs_imputation = master["im_weight"].isna()
log(f"  Tasks requiring imputation: {needs_imputation.sum():,}")

# Apply imputation
n_within_occ_imputed = 0
n_corpus_fallback_imputed = 0

for soc in master.loc[needs_imputation, "onet_soc_code"].unique():
    sub_mask = needs_imputation & (master["onet_soc_code"] == soc)
    if soc in occ_mean_im.index:
        master.loc[sub_mask, "im_weight"] = occ_mean_im[soc]
        n_within_occ_imputed += sub_mask.sum()
    else:
        master.loc[sub_mask, "im_weight"] = corpus_mean_im
        n_corpus_fallback_imputed += sub_mask.sum()

# Mark these as imputed
master.loc[needs_imputation, "im_weight_imputed"] = "Y"

log(f"  Tasks imputed using within-occupation mean: {n_within_occ_imputed:,}")
log(f"  Tasks imputed using corpus-wide fallback: {n_corpus_fallback_imputed:,}")
log("")

# =========================================================================
# Step 7 — Set weighting_mode flag per occupation
# =========================================================================
log("[Step 7] Setting weighting_mode flag per occupation ...")
log("  Occupations with no IM-rated tasks have weighting_mode='unweighted'")
log("  because every task receives the same imputed weight, making the")
log("  IM-weighted mean mathematically identical to a simple unweighted mean.")
log("")

master["weighting_mode"] = master["onet_soc_code"].map(
    lambda x: "unweighted" if x in occupations_without_im else "IM-weighted"
)
n_unweighted = master[master["weighting_mode"] == "unweighted"]["onet_soc_code"].nunique()
log(f"  Occupations flagged 'unweighted': {n_unweighted}")
log(f"  Occupations flagged 'IM-weighted': "
    f"{master[master['weighting_mode'] == 'IM-weighted']['onet_soc_code'].nunique()}")
log("")

# =========================================================================
# Step 8 — Reorder columns to match the Section 3.7 schema and save
# =========================================================================
log("[Step 8] Reordering columns and saving master file ...")

column_order = [
    "onet_soc_code",
    "occupation_title",
    "occupation_description",
    "task_id",
    "task_text",
    "task_type",
    "domain_source",
    "im_weight",
    "im_weight_imputed",
    "im_suppress",
    "rt_value",
    "rt_suppress",
    "task_date",
    "survey_n",
    "survey_date",
    "weighting_mode",
]
master = master[column_order]

master.to_csv(OUT_FILE, index=False, encoding="utf-8")
log(f"  Master file saved: {OUT_FILE}")
log(f"  Shape: {master.shape[0]:,} rows × {master.shape[1]} columns")
log("")

# =========================================================================
# Final summary — for audit and quick verification
# =========================================================================
log("=" * 70)
log("FINAL SUMMARY")
log("=" * 70)
log(f"Total task rows: {len(master):,}")
log(f"Unique occupations: {master['onet_soc_code'].nunique():,}")
log(f"Unique task IDs: {master['task_id'].nunique():,}")
log("")
log("IM weight status:")
log(f"  Original ratings (im_weight_imputed=N): "
    f"{(master['im_weight_imputed'] == 'N').sum():,}")
log(f"  Imputed (im_weight_imputed=Y): "
    f"{(master['im_weight_imputed'] == 'Y').sum():,}")
log(f"  Suppressed (im_suppress=Y, will be excluded at aggregation): "
    f"{(master['im_suppress'] == 'Y').sum():,}")
log("")
log("Weighting mode by occupation:")
log(f"  IM-weighted occupations: "
    f"{master[master['weighting_mode'] == 'IM-weighted']['onet_soc_code'].nunique():,}")
log(f"  Unweighted (no IM data): "
    f"{master[master['weighting_mode'] == 'unweighted']['onet_soc_code'].nunique():,}")
log("")
log("Task type distribution in final file:")
for ttype, cnt in master["task_type"].value_counts().items():
    log(f"  {ttype}: {cnt:,}")
log("")
log("Domain source distribution in final file:")
for ds, cnt in master["domain_source"].value_counts().items():
    log(f"  {ds}: {cnt:,}")
log("")

# Save the log to disk
LOG_FILE.write_text("\n".join(log_lines), encoding="utf-8")
log(f"Log saved to: {LOG_FILE}")
