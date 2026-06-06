"""
03_score_tasks.py
=================

PRODUCTION scoring script for the Generative AI Exposure Index.

This is the FINAL script used for every scoring run — smoke test (10 tasks),
pilot (75 tasks), and full production run (18,796 tasks). The only thing that
changes between runs is the input CSV; the model, prompt, schema, temperature,
seed, retry protocol, and aggregation rule are identical. There is intentionally
no separate "pilot" code path. If anything in this script (or the imported
prompt/schema) is altered after the pilot, the pilot must be re-run on the
revised version before the full production scoring proceeds (per
docs/data_documentation.md Section 3.8).

----------------------------------------------------------------------------
WHY SYNCHRONOUS, NOT BATCH (decision of 03 June 2026)
----------------------------------------------------------------------------
The original design used the OpenAI Batch API for its 50% cost discount. On
inspecting the funded account's actual limits, the account is Usage Tier 1,
whose Batch *enqueued-token* limit for gpt-4o is 90,000 tokens. Our full job
is ~38,300,000 enqueued tokens (18,796 tasks x ~2,036 input tokens) — roughly
425x over the Batch limit. Even the 75-task pilot (~153,000 tokens) exceeds it.
Batch is therefore unusable on this account, and chunking into ~44-task
micro-batches (430+ sequential submissions) is infeasible.

This script instead uses the standard *synchronous* Chat Completions API,
which is governed by the per-minute token limit (30,000 TPM on this account),
not the Batch queue. It paces requests to stay under TPM, backs off on rate
limits, tracks cost, and CHECKPOINTS after every task so a multi-hour run can
be interrupted and resumed without losing or re-paying for completed work.

The full run takes roughly 28-31 hours of run-time at Tier 1 pacing, but is
resumable across sessions. The synchronous API costs more per token than Batch
(no 50% discount), partially offset by automatic prompt caching of the shared
system prompt. See docs/data_documentation.md Section 5.22 for the full
decision record and Section 9.5 for the implementation log.

----------------------------------------------------------------------------
WHAT IT DOES
----------------------------------------------------------------------------
  1. Reads an input CSV with task_id, task_text, occupation_title columns.
  2. For each task, calls the synchronous Chat Completions API with the locked
     v3.2 system prompt (imported from rubric_prompt.py), fixed model version,
     temperature=0, fixed seed, and the JSON Schema response_format (strict).
  3. Paces requests to stay under the account's TPM limit; backs off on 429s.
  4. Parses each response into the nine documented fields, validates them, and
     computes the hard-gate composite score per Section 3.2.
  5. Implements the documented content-failure retry protocol:
       Round 1 -> the request itself (normal prompt)
       Round 2 -> identical retry once (on parse/validation/refusal failure)
       Round 3 -> retry with a clarifying prefix appended to the system prompt
       After Round 3 -> log as terminal failure, exclude from index, count in
                        supplementary materials.
     (Format failures are near-impossible under json_schema strict mode; the
     content-retry rounds defend against rare refusals or truncation. Separate
     from these, *infrastructure* errors — 429 / 5xx / network / timeout — are
     retried with exponential backoff and do NOT consume content-retry rounds.)
  6. CHECKPOINTS: every completed task is appended immediately to a progress
     JSONL file. On restart, already-scored tasks are skipped; terminal
     failures from a prior run are retried.
  7. Tracks cumulative token usage and estimated cost; aborts if a configurable
     safety cap is exceeded (guards against runaway spend).
  8. Writes a scored CSV plus the progress JSONL and a timestamped audit log.

----------------------------------------------------------------------------
USAGE
----------------------------------------------------------------------------
    # 1. Set the API key (never hardcode):
    #    PowerShell:  $env:OPENAI_API_KEY = "sk-..."
    #    bash:        export OPENAI_API_KEY="sk-..."
    #
    # 2. Run against an input CSV:
    #    Quick 2-task pre-flight:
    #      python 03_score_tasks.py --input ../data/processed/smoke_test_tasks.csv --limit 2
    #    Smoke test (10 tasks):
    #      python 03_score_tasks.py --input ../data/processed/smoke_test_tasks.csv
    #    Pilot (75 tasks):
    #      python 03_score_tasks.py --input ../data/processed/pilot_tasks.csv
    #    Full run (18,796 tasks; resumable — re-run the same command to resume):
    #      python 03_score_tasks.py --input ../data/processed/master_tasks.csv

Outputs (written next to the input CSV, named after its base):
    scored_<base>.csv        — final: one row per task, nine fields + composite + status
    progress_<base>.jsonl    — checkpoint: one line per completed task (crash-safe)
    log_<base>.txt           — timestamped audit log of every action

Author: Aaryan Mehta
Created: 23 May 2026 (Batch design). Rewritten for synchronous API: 03 June 2026.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# --- External dependencies -----------------------------------------------
try:
    from openai import (
        OpenAI, RateLimitError, APITimeoutError,
        APIConnectionError, InternalServerError, BadRequestError, APIError,
    )
except ImportError:
    sys.exit(
        "ERROR: the 'openai' package is required (>=1.50.0).\n"
        "Install it with:  pip install \"openai>=1.50.0\""
    )

try:
    import pandas as pd
except ImportError:
    sys.exit("ERROR: the 'pandas' package is required.  pip install pandas")

# --- Import the canonical prompt + schema (single source of truth) -------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rubric_prompt import SYSTEM_PROMPT, RESPONSE_SCHEMA, format_user_message


# Raised when the API reports the account is out of credit (a 429 with code
# insufficient_quota). Unlike an ordinary rate-limit, waiting cannot fix it, so
# the run HALTS CLEANLY instead of churning through retries. Everything scored so
# far is already checkpointed; re-running the same command after a top-up resumes.
class InsufficientCreditsError(Exception):
    pass

# =========================================================================
# Configuration — fixed and deliberate. Changing any of these triggers re-pilot.
# =========================================================================
MODEL = "gpt-4o-2024-11-20"   # FIXED model version, recorded in Section 3.2
TEMPERATURE = 0               # Greedy decoding for reproducibility
SEED = 20260603              # Fixed seed for best-effort determinism (Section 6.3)
MAX_OUTPUT_TOKENS = 600       # CoT output ~250 tokens; 600 guards against truncation
PROMPT_CACHE_KEY = "genai-exposure-index-rubric-v3"  # shared cache routing hint

# Pacing (Tier 1: 30,000 TPM, 500 RPM). Each request reserves
# ~(input + MAX_OUTPUT_TOKENS) ~= 2,636 tokens toward TPM. A 6.0s interval gives
# ~10 req/min ~= 26,360 tokens/min (~88% of TPM) — safe margin. Tunable via CLI
# once the smoke/pilot confirm no 429s occur at this pace.
DEFAULT_PACE_SECONDS = 6.0

# Infrastructure retry/backoff (for 429 / 5xx / network — NOT content failures)
MAX_INFRA_RETRIES = 8         # exponential backoff attempts per request
BASE_BACKOFF_SECONDS = 2.0    # 2, 4, 8, 16, ... capped
MAX_BACKOFF_SECONDS = 120.0

# Content-failure retry rounds (parse / validation / refusal). Per Section 3.2.
# Round 1 = the initial request; this constant is the count of EXTRA rounds.
CONTENT_RETRY_ROUNDS = 2      # Round 2 (identical) + Round 3 (clarifying prefix)
CLARIFYING_PREFIX = (
    "Respond with ONLY a valid JSON object matching the response schema. "
    "Do not include any text outside the JSON object."
)

# Cost tracking (standard sync pricing for gpt-4o-2024-11-20, USD per 1M tokens,
# as of mid-2026; approximate — true cost is read from the API usage field).
PRICE_INPUT_UNCACHED = 2.50
PRICE_INPUT_CACHED = 1.25
PRICE_OUTPUT = 10.00

# Safety cap: abort the run if cumulative estimated cost exceeds this (USD).
# Guards against any runaway. Override with --max-cost-usd.
DEFAULT_MAX_COST_USD = 150.0

CHECKPOINT_LOG_EVERY = 25     # log a progress line every N tasks

# =========================================================================
# Logging
# =========================================================================
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def log(msg, log_file=None):
    line = f"[{now_iso()}] {msg}"
    print(line)
    if log_file is not None:
        log_file.write(line + "\n")
        log_file.flush()

# =========================================================================
# Field / schema constants
# =========================================================================
# Field names match rubric_prompt.py v3.1 schema.
REQUIRED_FIELDS = (
    "information_sufficiency_reasoning", "information_sufficiency_score",
    "objective_verifiability_reasoning", "objective_verifiability_score",
    "contextual_independence_reasoning", "contextual_independence_score",
    "capability_match_what_works", "capability_match_what_might_fail",
    "capability_match_score",
)
SCORE_FIELDS = (
    "information_sufficiency_score", "objective_verifiability_score",
    "contextual_independence_score", "capability_match_score",
)
# The two GATING criteria (Design Y, Section 3.2): categorical inability.
GATE_FIELDS = ("information_sufficiency_score", "capability_match_score")

# =========================================================================
# Aggregation — Design Y (Section 3.2)
# =========================================================================
def compute_composite(parsed):
    """
    Design Y aggregation:
      - GATE (composite = 0) if either categorical-inability criterion is 0:
        Information Sufficiency = 0 (physically impossible for a disembodied model)
        OR Capability Match = 0 (below average-human quality; cannot substitute).
      - Otherwise the four criteria MODULATE: composite = mean(all four) / 2.
    The two quality criteria (Objective Verifiability, Contextual Independence)
    never gate — they scale the score down without zeroing it.
    """
    if parsed["information_sufficiency_score"] == 0 or parsed["capability_match_score"] == 0:
        return 0.0, "GATED"
    scores = [parsed[f] for f in SCORE_FIELDS]
    return sum(scores) / len(scores) / 2.0, "PASS"

def gating_criteria(parsed):
    """Which GATING criterion (or criteria) zeroed the task. Only IS and CM gate."""
    return [f.replace("_score", "") for f in GATE_FIELDS if parsed[f] == 0]

# =========================================================================
# Validation of a parsed response
# =========================================================================
def validate_parsed(parsed):
    """Return None if valid, else an error string."""
    if not isinstance(parsed, dict):
        return "not_a_json_object"
    missing = [f for f in REQUIRED_FIELDS if f not in parsed]
    if missing:
        return f"missing_fields: {missing}"
    bad = [f for f in SCORE_FIELDS if parsed[f] not in (0, 1, 2)]
    if bad:
        return f"invalid_scores: {bad}"
    return None

# =========================================================================
# Single-task scoring with infrastructure backoff + content-retry rounds
# =========================================================================
def score_one_task(client, task_id, task_text, occupation_title, log_file):
    """
    Score a single task. Returns (result_dict, usage_dict).

    result_dict is either a valid parsed response (the nine fields) augmented
    with "_round" (which content round succeeded), or {"_error": str} on terminal
    failure. usage_dict carries token usage for cost tracking (may be partial on
    failure).
    """
    user_msg = format_user_message(task_text, occupation_title)
    cumulative_usage = {"prompt": 0, "cached": 0, "completion": 0}

    # Content rounds: round 0 = normal prompt; round 1 = identical retry;
    # round 2 = clarifying-prefix retry.
    for content_round in range(CONTENT_RETRY_ROUNDS + 1):
        system_prompt = SYSTEM_PROMPT
        if content_round == 2:
            system_prompt = CLARIFYING_PREFIX + "\n\n" + SYSTEM_PROMPT

        # Infrastructure retry loop (429 / 5xx / network) with exponential backoff
        for infra_attempt in range(MAX_INFRA_RETRIES + 1):
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=TEMPERATURE,
                    seed=SEED,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    response_format=RESPONSE_SCHEMA,
                    # Routing hint so all requests share the cache of the identical
                    # ~1,983-token system prompt, maximising prompt-cache hit rate
                    # (the cost mitigation that keeps the sync run within budget).
                    prompt_cache_key=PROMPT_CACHE_KEY,
                )
                # Accumulate usage for cost tracking
                if resp.usage is not None:
                    cumulative_usage["prompt"] += resp.usage.prompt_tokens or 0
                    cumulative_usage["completion"] += resp.usage.completion_tokens or 0
                    details = getattr(resp.usage, "prompt_tokens_details", None)
                    if details is not None:
                        cumulative_usage["cached"] += getattr(details, "cached_tokens", 0) or 0

                message = resp.choices[0].message

                # Structured-outputs refusal handling
                refusal = getattr(message, "refusal", None)
                if refusal:
                    log(f"    task {task_id}: model refusal on content round "
                        f"{content_round}: {str(refusal)[:120]}", log_file)
                    break  # break infra loop -> try next content round

                content = message.content
                if content is None:
                    log(f"    task {task_id}: empty content on round {content_round}", log_file)
                    break

                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    log(f"    task {task_id}: JSON parse failure round "
                        f"{content_round}: {e}", log_file)
                    break  # try next content round

                err = validate_parsed(parsed)
                if err is not None:
                    log(f"    task {task_id}: validation failure round "
                        f"{content_round}: {err}", log_file)
                    break  # try next content round

                # Success
                parsed["_round"] = content_round
                return parsed, cumulative_usage

            except RateLimitError as e:
                # Distinguish "out of credit" from an ordinary rate-limit. An
                # out-of-credit 429 carries code insufficient_quota and cannot be
                # fixed by waiting, so halt the whole run cleanly (resumable after
                # top-up). An ordinary rate-limit is retried with backoff.
                emsg = (str(e) + " " + str(getattr(e, "code", ""))).lower()
                if ("insufficient_quota" in emsg or "exceeded your current quota" in emsg
                        or "billing_hard_limit_reached" in emsg):
                    raise InsufficientCreditsError(str(e)[:200])
                wait = min(BASE_BACKOFF_SECONDS * (2 ** infra_attempt), MAX_BACKOFF_SECONDS)
                log(f"    task {task_id}: 429 rate limit (attempt {infra_attempt+1}/"
                    f"{MAX_INFRA_RETRIES+1}); backing off {wait:.0f}s", log_file)
                time.sleep(wait)
                continue
            except (APITimeoutError, APIConnectionError, InternalServerError) as e:
                wait = min(BASE_BACKOFF_SECONDS * (2 ** infra_attempt), MAX_BACKOFF_SECONDS)
                log(f"    task {task_id}: transient API error ({type(e).__name__}) "
                    f"(attempt {infra_attempt+1}); backing off {wait:.0f}s", log_file)
                time.sleep(wait)
                continue
            except BadRequestError as e:
                # A 400 means the request itself is malformed — retrying will not
                # help. Treat as terminal immediately (do not burn time/money).
                log(f"    task {task_id}: BadRequestError (terminal): {str(e)[:200]}", log_file)
                return {"_error": f"bad_request: {str(e)[:200]}"}, cumulative_usage
            except APIError as e:
                wait = min(BASE_BACKOFF_SECONDS * (2 ** infra_attempt), MAX_BACKOFF_SECONDS)
                log(f"    task {task_id}: APIError ({type(e).__name__}) "
                    f"(attempt {infra_attempt+1}); backing off {wait:.0f}s", log_file)
                time.sleep(wait)
                continue
        else:
            # Exhausted infra retries (persistent 429 / 5xx / network). More
            # content rounds won't fix an API/infrastructure problem, so fail
            # fast and terminally rather than cascading through more attempts.
            # The task is checkpointed as a terminal failure and will be retried
            # automatically on the next resume run.
            log(f"    task {task_id}: exhausted infra retries on content round "
                f"{content_round}; failing fast (will retry on resume)", log_file)
            return {"_error": "infra_retries_exhausted"}, cumulative_usage

    # All content rounds exhausted (persistent content/parse/refusal failure)
    return {"_error": "all_content_rounds_failed"}, cumulative_usage

# =========================================================================
# Cost helper
# =========================================================================
def estimate_cost(total_prompt, total_cached, total_completion):
    uncached = max(total_prompt - total_cached, 0)
    return (
        uncached / 1e6 * PRICE_INPUT_UNCACHED
        + total_cached / 1e6 * PRICE_INPUT_CACHED
        + total_completion / 1e6 * PRICE_OUTPUT
    )

# =========================================================================
# Checkpoint loading
# =========================================================================
def load_checkpoint(progress_path):
    """
    Read the progress JSONL. Returns (done_ids, rows) where done_ids is the set
    of task_ids already SUCCESSFULLY scored (PASS or GATED), and rows is the list
    of all recorded result dicts (used to rebuild the final CSV). Terminal
    failures are NOT added to done_ids, so they are retried on resume.
    """
    done_ids = set()
    rows = []
    if not progress_path.exists():
        return done_ids, rows
    with open(progress_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows.append(rec)
            if rec.get("scoring_status") in ("PASS", "GATED"):
                done_ids.add(int(rec["task_id"]))
    return done_ids, rows

def rebuild_scored_csv(progress_path, scored_csv):
    """Rebuild the scored CSV from the full progress file (all sessions), so the
    CSV reflects every completed task. Dedup keeps the LAST record per task_id (a
    resumed retry supersedes an earlier terminal failure). Called both at normal
    completion and on a clean credit-exhaustion halt. Returns the DataFrame."""
    _, all_rows = load_checkpoint(progress_path)
    by_id = {}
    for r in all_rows:
        by_id[int(r["task_id"])] = r
    out_df = pd.DataFrame(list(by_id.values()))
    preferred = [
        "task_id", "occupation_title", "task_text", "scoring_status",
        "information_sufficiency_reasoning", "information_sufficiency_score",
        "objective_verifiability_reasoning", "objective_verifiability_score",
        "contextual_independence_reasoning", "contextual_independence_score",
        "capability_match_what_works", "capability_match_what_might_fail",
        "capability_match_score", "composite_score", "gated_by",
        "content_round", "error_message",
    ]
    if len(out_df):
        cols = [c for c in preferred if c in out_df.columns] + \
               [c for c in out_df.columns if c not in preferred]
        out_df = out_df[cols]
    out_df.to_csv(scored_csv, index=False, encoding="utf-8")
    return out_df

# =========================================================================
# Main
# =========================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Score O*NET tasks via the synchronous OpenAI API using the locked rubric."
    )
    parser.add_argument("--input", required=True,
                        help="Input CSV with task_id, task_text, occupation_title columns.")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: same directory as input).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Score only the first N not-yet-done tasks (for quick pre-flight).")
    parser.add_argument("--pace", type=float, default=DEFAULT_PACE_SECONDS,
                        help=f"Minimum seconds between requests (default {DEFAULT_PACE_SECONDS}).")
    parser.add_argument("--max-cost-usd", type=float, default=DEFAULT_MAX_COST_USD,
                        help=f"Abort if estimated cost exceeds this (default ${DEFAULT_MAX_COST_USD}).")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        sys.exit(f"ERROR: input file does not exist: {input_path}")

    out_dir = Path(args.output_dir).resolve() if args.output_dir else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    base = input_path.stem

    log_path = out_dir / f"log_{base}.txt"
    progress_path = out_dir / f"progress_{base}.jsonl"
    scored_csv = out_dir / f"scored_{base}.csv"

    log_file = open(log_path, "a", encoding="utf-8")  # append: preserve prior-session logs
    log("=" * 70, log_file)
    log("03_score_tasks.py (synchronous) starting", log_file)
    log(f"Input  : {input_path}", log_file)
    log(f"Output : {out_dir}", log_file)
    log(f"Model  : {MODEL}  Temp: {TEMPERATURE}  Seed: {SEED}  MaxTokens: {MAX_OUTPUT_TOKENS}", log_file)
    log(f"Pace   : {args.pace}s/request   Cost cap: ${args.max_cost_usd}", log_file)

    # --- API client --------------------------------------------------------
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        log("ERROR: OPENAI_API_KEY environment variable is not set.", log_file)
        sys.exit(
            "Set it first:\n"
            "  PowerShell:  $env:OPENAI_API_KEY = 'sk-...'\n"
            "  bash:        export OPENAI_API_KEY='sk-...'"
        )
    client = OpenAI(api_key=api_key)

    # --- input -------------------------------------------------------------
    tasks = pd.read_csv(input_path)
    required_cols = {"task_id", "task_text", "occupation_title"}
    missing_cols = required_cols - set(tasks.columns)
    if missing_cols:
        log(f"ERROR: input is missing required columns: {missing_cols}", log_file)
        sys.exit(2)
    tasks["task_id"] = tasks["task_id"].astype(int)
    log(f"Loaded {len(tasks)} task(s) from {input_path.name}", log_file)

    # --- checkpoint --------------------------------------------------------
    done_ids, prior_rows = load_checkpoint(progress_path)
    if done_ids:
        log(f"Resuming: {len(done_ids)} task(s) already scored in a prior session "
            f"— they will be skipped.", log_file)
    remaining = tasks[~tasks["task_id"].isin(done_ids)].copy()
    if args.limit is not None:
        remaining = remaining.head(args.limit)
    log(f"Tasks to score this session: {len(remaining)}", log_file)

    # --- scoring loop ------------------------------------------------------
    progress_file = open(progress_path, "a", encoding="utf-8")
    tot_prompt = tot_cached = tot_completion = 0
    n_pass = n_gated = n_failed = 0
    last_request_time = 0.0

    for i, (_, t) in enumerate(remaining.iterrows(), 1):
        # Pace: ensure >= args.pace seconds since the last request start
        elapsed = time.time() - last_request_time
        if elapsed < args.pace:
            time.sleep(args.pace - elapsed)
        last_request_time = time.time()

        tid = int(t["task_id"])
        try:
            result, usage = score_one_task(
                client, tid, str(t["task_text"]), str(t["occupation_title"]), log_file
            )
        except InsufficientCreditsError as e:
            # Out of API credit. Everything completed so far is checkpointed.
            # Re-running the SAME command after topping up resumes from here (this
            # task is retried; nothing already done is re-charged).
            log("=" * 70, log_file)
            log(f"OUT OF API CREDIT at task {tid}  ({i-1} task(s) scored this session).", log_file)
            log(f"  Detail: {e}", log_file)
            log("  Stopping cleanly — no churn, no wasted spend. To continue:", log_file)
            log("    1) Add credit at platform.openai.com (Settings -> Billing).", log_file)
            log("    2) Re-run the EXACT SAME command. It resumes from this task.", log_file)
            progress_file.flush()
            os.fsync(progress_file.fileno())
            progress_file.close()
            rebuild_scored_csv(progress_path, scored_csv)
            log(f"  Partial results saved so far: {scored_csv}", log_file)
            log_file.close()
            sys.exit(4)

        tot_prompt += usage["prompt"]
        tot_cached += usage["cached"]
        tot_completion += usage["completion"]

        # Build the output row (carry through any extra input columns, e.g. bucket)
        row = {
            "task_id": tid,
            "occupation_title": t["occupation_title"],
            "task_text": t["task_text"],
        }
        for col in tasks.columns:
            if col not in row and col != "task_id":
                row[col] = t[col]

        if "_error" in result:
            row.update({
                "scoring_status": "TERMINAL_FAILURE",
                "error_message": str(result["_error"]),
                "composite_score": None,
                "gated_by": None,
            })
            n_failed += 1
        else:
            composite, status = compute_composite(result)
            row.update({
                "scoring_status": status,
                "information_sufficiency_reasoning": result["information_sufficiency_reasoning"],
                "information_sufficiency_score": result["information_sufficiency_score"],
                "objective_verifiability_reasoning": result["objective_verifiability_reasoning"],
                "objective_verifiability_score": result["objective_verifiability_score"],
                "contextual_independence_reasoning": result["contextual_independence_reasoning"],
                "contextual_independence_score": result["contextual_independence_score"],
                "capability_match_what_works": result["capability_match_what_works"],
                "capability_match_what_might_fail": result["capability_match_what_might_fail"],
                "capability_match_score": result["capability_match_score"],
                "composite_score": composite,
                "gated_by": ",".join(gating_criteria(result)) if status == "GATED" else None,
                "content_round": result.get("_round", 0),
            })
            if status == "PASS":
                n_pass += 1
            else:
                n_gated += 1

        # CHECKPOINT: append immediately and fsync so a crash cannot lose this task
        progress_file.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        progress_file.flush()
        os.fsync(progress_file.fileno())

        # Periodic progress + cost log; enforce the safety cap
        cost = estimate_cost(tot_prompt, tot_cached, tot_completion)
        if i % CHECKPOINT_LOG_EVERY == 0 or i == len(remaining):
            log(f"  progress {i}/{len(remaining)}  "
                f"PASS={n_pass} GATED={n_gated} FAIL={n_failed}  "
                f"tokens(in/cached/out)={tot_prompt:,}/{tot_cached:,}/{tot_completion:,}  "
                f"est_cost=${cost:.2f}", log_file)
        if cost > args.max_cost_usd:
            log(f"ABORT: estimated cost ${cost:.2f} exceeded cap ${args.max_cost_usd}. "
                f"Completed work is checkpointed; re-run to resume after raising --max-cost-usd.",
                log_file)
            progress_file.close()
            log_file.close()
            sys.exit(3)

    progress_file.close()

    # --- rebuild the final scored CSV from the complete progress file ------
    # (Re-read so the CSV reflects ALL sessions, not just this one.)
    out_df = rebuild_scored_csv(progress_path, scored_csv)

    # --- final summary -----------------------------------------------------
    final_cost = estimate_cost(tot_prompt, tot_cached, tot_completion)
    n_total = len(out_df)
    n_pass_all = int((out_df["scoring_status"] == "PASS").sum())
    n_gated_all = int((out_df["scoring_status"] == "GATED").sum())
    n_fail_all = int((out_df["scoring_status"] == "TERMINAL_FAILURE").sum())
    log("", log_file)
    log("=== FINAL SUMMARY (all sessions) ===", log_file)
    log(f"  Tasks in scored CSV : {n_total}", log_file)
    log(f"  PASS  (non-zero)    : {n_pass_all}", log_file)
    log(f"  GATED (composite 0) : {n_gated_all}", log_file)
    log(f"  TERMINAL_FAILURE    : {n_fail_all}  (excluded from index per Section 3.2)", log_file)
    log(f"  This session tokens (in/cached/out): "
        f"{tot_prompt:,}/{tot_cached:,}/{tot_completion:,}", log_file)
    log(f"  This session est. cost: ${final_cost:.2f}", log_file)
    log(f"  Scored CSV : {scored_csv}", log_file)
    log(f"  Progress   : {progress_path}", log_file)
    if n_fail_all > 0:
        log(f"  NOTE: {n_fail_all} terminal failure(s). Re-run the same command to "
            f"retry them (successful tasks are skipped).", log_file)
    log_file.close()

if __name__ == "__main__":
    main()
