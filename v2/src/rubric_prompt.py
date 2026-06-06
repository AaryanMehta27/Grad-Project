"""
rubric_prompt.py
================

The rubric prompt for the LLM-as-judge scoring of O*NET task statements.

This file defines the exact prompt and response schema sent to GPT-4o (and to a
second model for the reliability sample) when scoring each O*NET task statement.
Three components:

  1. SYSTEM_PROMPT — role, scope, the four criteria, anti-anchoring instruction.
  2. RESPONSE_SCHEMA — the JSON Schema passed to OpenAI structured outputs (strict).
  3. USER_MESSAGE_TEMPLATE — the per-task message (task text + occupation title).

Full methodology: docs/data_documentation.md, principally Section 3.2 (criteria,
aggregation), Section 3.3 (scope), Section 3.8 (pilot), Section 5 (decision history).

Once the pilot test passes, this file is FROZEN. Any change requires re-piloting.

Author: Aaryan Mehta
Status: LOCKED v3.2 (04 June 2026). The v3.2 re-pilot passed all checks
(determinism within the temperature-0 floor; Criterion 3 moved as intended;
relational and physical floors held — see data_documentation.md Section 5.26).
Frozen for the full production run. Any edit re-triggers the pilot.

v3.2 change (04 June 2026) — a single, surgical refinement to Criterion 3
(Contextual Independence) only. The v3.1 re-pilot worked (7-value gradient,
Capability Match reaching 2, criteria mostly separable), but reading the
reasoning showed Contextual Independence was over-applied: it docked points
for any organisation-specific context (procedures, files, policies) even when
that context is documentable and could be supplied to the model — one task's
reasoning even argued for a 2 ("much can be done with general knowledge") then
scored 1. This systematically under-scored routine digital cognitive work, the
most GenAI-exposed category. The fix adds one clarifying sentence (documentable
context is not a barrier; only real-time human interaction or genuinely tacit
knowledge is) and sharpens the score-2 anchor. Criteria 1, 2, and 4 and the
schema field names are byte-for-byte unchanged. See Decision History 5.25.

----------------------------------------------------------------------------
Changes in v3.1 (03 June 2026) — the criterion redesign
----------------------------------------------------------------------------
The first real pilot (75 tasks, gpt-4o) revealed that the v3 criteria collapsed:
the index took only THREE composite values (0, 0.75, 0.875), because three of the
four criteria were all secretly measuring the same axis — "physical vs digital."
Information Sufficiency, Output Verifiability, and Decomposability correlated at
0.95-0.99; Capability Match never once scored 2 (an impossible "no re-checking"
bar). See docs/data_documentation.md Section 5.23 and the prompt-change document
for the full evidence.

v3.1 redesigns the four criteria so each captures a DISTINCT, literature-grounded
barrier to AI substitution (the bottlenecks identified by Frey & Osborne 2013;
Autor, Levy & Murnane 2003; Autor 2015 on Polanyi's Paradox; Brynjolfsson,
Mitchell & Rock 2018; Deming 2017):

  1. Information Sufficiency  — physical / embodiment barrier        (kept)
  2. Objective Verifiability  — no checkable success criterion       (redefined from "Output Verifiability")
  3. Contextual Independence  — social + tacit-knowledge barrier     (replaces "Decomposability")
  4. Capability Match         — raw current-model capability         (recalibrated to a human-equivalent bar)

Aggregation also changes to "Design Y" (gate on categorical inability — IS or CM
= 0; modulate on substitution quality — mean of all four / 2 otherwise). See
Section 5.5 and 5.24.

Each criterion now (a) states explicitly what it is NOT about, naming the
criterion that owns that axis, to prevent the cross-criterion leakage that caused
the collapse; and (b) carries minimal, domain-diverse, deliberately
pattern-breaking examples, governed by an anti-anchoring instruction, to calibrate
the LLM without inducing availability/anchoring bias (Suri et al. 2024).

Earlier history: v1 (direct scoring) -> v2 (chain-of-thought + two-field Criterion
4 + structured outputs) -> v3 (Decomposability decoupled, Capability Match
sharpened) -> v3.1 (this criterion redesign).
"""

# =========================================================================
# SYSTEM PROMPT
# =========================================================================

SYSTEM_PROMPT = """You are an expert evaluator of how current Generative AI systems can substitute for human workers on specific occupational tasks.

# What you are evaluating

You are evaluating whether current frontier Foundation Models — large language models (LLMs), vision-language models (VLMs), and multimodal generative systems — can substitute for the human worker on a given occupational task at human-equivalent or better proficiency.

You are NOT evaluating:
- Robotics, autonomous vehicles, or any AI requiring physical embodiment, actuators, or real-world sensors. These are out of scope.
- AI augmentation where the human worker remains required.
- Whether workers will actually lose their jobs (regulation, liability, and deployment cost are out of scope).
- Future or projected AI capabilities — evaluate against current frontier Foundation Models only, as they exist today.

# How to use the criteria and the examples

You will score the task on FOUR independent criteria, each on a 0 / 1 / 2 scale. The criteria are deliberately distinct: each captures a different reason a task might resist AI substitution. Score each criterion ONLY for the property it names, and do not let your judgement on one criterion leak into another. Each criterion states explicitly what it is NOT about — respect those boundaries.

The examples in each criterion illustrate the underlying principle; they are NOT a lookup table. Score every task by the criterion's definition. A task that resembles an example on the surface but differs in the underlying property must be scored by the property, not the resemblance. A task unlike any example is scored from the definition alone.

# Disambiguation rule

O*NET task descriptions often do not specify implementation context. When a task could plausibly be performed using digital tools in a contemporary workplace, evaluate it under that digital implementation. This rule resolves ambiguity for Criterion 1 (Information Sufficiency); it does not change the other three criteria.

# The four criteria

## Criterion 1 — Information Sufficiency
Can the task be completed using only information that can be received and acted on digitally (text, images, audio, structured data), with no requirement for real-time physical presence, manipulation of physical objects, or embodied sensory perception?
This is the ONLY criterion that judges physical vs. digital. The other three assume the task is digitally accessible and judge different barriers — do not re-judge physicality in them.
- 0: Fundamentally requires physical presence, manual manipulation, or real-time embodied sensing. Example: positioning and welding steel beams.
- 1: Mostly digital but with a genuine physical component that cannot be separated out. Example: diagnosing a machine fault that needs both remote telemetry and a hands-on inspection.
- 2: Completable entirely through digital information and outputs. Example: reconciling figures in a financial spreadsheet.

## Criterion 2 — Objective Verifiability
Does the task have a clear, objective standard of success — a checkable correct answer, a testable output, or measurable criteria — as opposed to success being a matter of subjective judgement, taste, or opinion?
This is NOT about whether the output is digital or physical (Criterion 1 owns that). A fully digital output can be entirely subjective. Judge only: can you objectively determine whether the result is correct?
- 0: Success is inherently subjective or contested — there is no objective right answer. Example: writing an inspiring company mission statement (fluent and digital, but whether it is "good" is a matter of opinion).
- 1: Some objective elements, but success also depends on judgement that reasonable experts could dispute. Example: recommending which of several viable budgets to approve.
- 2: Objectively checkable — there is a correct answer, a testable result, or measurable criteria. Example: translating a document (fidelity is checkable), or extracting figures from invoices.

## Criterion 3 — Contextual Independence
Can the task be completed by an agent that has only (a) the task description and (b) general knowledge — OR does it require real-time human interaction (negotiating, persuading, counselling, building trust, reading and responding to people) or organisation-specific tacit knowledge (relationships, internal history, undocumented local context) that a general-purpose model would not possess?
This is NOT about physical vs. digital (Criterion 1), and NOT about whether the model could produce the content (Criterion 4). A model might draft an excellent message yet be unable to BE the trusted human in a live negotiation. Judge only: does success require human-relational embedding or insider context? Context that could be written down and supplied — procedures, specifications, files, policies, client requirements — does NOT count as a barrier, because it can be provided to the model; only real-time human interaction or genuinely tacit/undocumented knowledge does.
- 0: Success fundamentally depends on real-time interpersonal interaction, or on insider/relationship/tacit context the model cannot access. Example: counselling a grieving family member.
- 1: Benefits from such context, but a substantial portion could be done from the task description plus general knowledge. Example: preparing a client briefing that draws partly on the firm's prior dealings.
- 2: Self-contained — completable from the task description, any relevant documents, and general knowledge, even if it relies on company-specific procedures or files (which can be supplied). Example: summarising a research report; coding to a documented company style guide.

## Criterion 4 — Capability Match
Setting aside the other three criteria, can a current frontier Foundation Model produce the core output of this task at a quality at or above that of an average human worker in the role?
Calibration: the benchmark is the AVERAGE HUMAN WORKER, not perfection. A competent human's work is also reviewed and occasionally corrected, so the fact that the model's output would receive normal review does NOT lower the score. A failure mode counts against the score only if it would make the output WORSE than an average human's. Do not lower this score because the task needs a human relationship or insider context — that is Criterion 3.

For this criterion, fill TWO reasoning fields before the score, each one sentence:
- capability_match_what_works: what about this specific task is tractable for a current frontier Foundation Model. Be specific to the task; do not list generic model capabilities.
- capability_match_what_might_fail: what about this specific task might make the model's output worse than an average human's. Be specific to the task; do not list generic model limitations.

Both fields are required and must engage the task on its own merits, not mirror each other. Then assign the score:
- 0: Clearly below average-human quality on the core — frequently wrong, superficial, or a human must essentially redo it. Example: devising a novel mathematical proof.
- 1: Useful but below average-human quality — meaningfully assists, but a human must substantially complete or rework the core. Example: producing a first-draft analysis of a complex, unusual legal case.
- 2: At or above average-human-worker quality on the core, needing no more review than a human's work normally gets. Example: drafting routine business correspondence.

# Output

Produce a JSON object with these nine fields, in this order: information_sufficiency_reasoning, information_sufficiency_score, objective_verifiability_reasoning, objective_verifiability_score, contextual_independence_reasoning, contextual_independence_score, capability_match_what_works, capability_match_what_might_fail, capability_match_score. Reasoning fields are one sentence specific to the task; score fields are integers in {0, 1, 2}. The structure is enforced by the API's structured-output mode."""


# =========================================================================
# RESPONSE SCHEMA  (OpenAI structured outputs, strict)
# =========================================================================

def _reason(desc):
    return {"type": "string", "description": desc}

def _score():
    return {"type": "integer", "enum": [0, 1, 2]}

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "rubric_scoring",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "information_sufficiency_reasoning": _reason(
                    "One sentence: does this task require physical presence / "
                    "embodiment, or can it be done with digital information only?"),
                "information_sufficiency_score": _score(),
                "objective_verifiability_reasoning": _reason(
                    "One sentence: does this task have an objective, checkable "
                    "standard of success, or is success a matter of judgement? "
                    "(Not about digital vs physical.)"),
                "objective_verifiability_score": _score(),
                "contextual_independence_reasoning": _reason(
                    "One sentence: can this task be done from the task description "
                    "plus general knowledge, or does it need real-time human "
                    "interaction or insider/tacit context?"),
                "contextual_independence_score": _score(),
                "capability_match_what_works": _reason(
                    "One sentence, task-specific: what about this task is tractable "
                    "for a current frontier Foundation Model?"),
                "capability_match_what_might_fail": _reason(
                    "One sentence, task-specific: what might make the model's output "
                    "worse than an average human's?"),
                "capability_match_score": _score(),
            },
            "required": [
                "information_sufficiency_reasoning", "information_sufficiency_score",
                "objective_verifiability_reasoning", "objective_verifiability_score",
                "contextual_independence_reasoning", "contextual_independence_score",
                "capability_match_what_works", "capability_match_what_might_fail",
                "capability_match_score",
            ],
            "additionalProperties": False,
        },
    },
}


# =========================================================================
# USER MESSAGE TEMPLATE
# =========================================================================
# Occupation title is included because the same task verb means different things
# across occupations. The full occupation description is omitted to keep the
# message focused (revisit if the pilot shows the title alone is insufficient).

USER_MESSAGE_TEMPLATE = """Score the following O*NET task statement.

Task: {task_text}
Occupation: {occupation_title}"""


def format_user_message(task_text: str, occupation_title: str) -> str:
    """Format the per-task user message."""
    return USER_MESSAGE_TEMPLATE.format(
        task_text=task_text,
        occupation_title=occupation_title,
    )


# =========================================================================
# Reference: API call structure (synchronous Chat Completions API)
# =========================================================================
# Used by src/03_score_tasks.py. The account is Usage Tier 1, whose Batch
# enqueued-token limit (90,000) is far below the job size, so the synchronous
# endpoint is used (bounded by the 30,000 TPM rate limit). See
# data_documentation.md Section 5.22.
#
#   from rubric_prompt import SYSTEM_PROMPT, RESPONSE_SCHEMA, format_user_message
#
#   resp = client.chat.completions.create(
#       model="gpt-4o-2024-11-20",        # fixed version, recorded for reproducibility
#       messages=[
#           {"role": "system", "content": SYSTEM_PROMPT},
#           {"role": "user",   "content": format_user_message(task_text, occupation_title)},
#       ],
#       temperature=0,
#       seed=20260603,                     # fixed seed for best-effort determinism
#       max_tokens=600,                    # CoT output ~250 tokens; 600 guards truncation
#       response_format=RESPONSE_SCHEMA,
#       prompt_cache_key="genai-exposure-index-rubric-v3",  # cache routing hint (cost)
#   )
#
# AGGREGATION (Design Y, Section 3.2):
#   composite = 0.0                                  if IS == 0 or CapabilityMatch == 0
#   composite = mean(IS, ObjVerif, CtxIndep, CM) / 2 otherwise
#
# Cost estimate (v3.1): the redesigned system prompt is ~1,895 tokens —
# essentially unchanged from v3 (~1,983), so cost is stable. Per task ~1,950
# input + ~200 output tokens. Full run (18,796 tasks) ~36.6M input + ~3.8M output.
# Synchronous gpt-4o pricing $2.50/$10 per 1M (in/out), roughly halved on the
# input side by prompt caching of the identical system prompt. The v3 pilot
# logged ~$0.005/task; full run therefore ~$95 (~£75). The definitive per-task
# cost comes from the re-pilot's logged usage, not this estimate.


if __name__ == "__main__":
    import json
    sample_task = ("Direct or coordinate an organization's financial or budget "
                   "activities to fund operations, maximize investments, or "
                   "increase efficiency.")
    sample_occupation = "Chief Executives"
    print("=" * 70)
    print("SYSTEM PROMPT")
    print("=" * 70)
    print(SYSTEM_PROMPT)
    print()
    print("=" * 70)
    print("RESPONSE SCHEMA")
    print("=" * 70)
    print(json.dumps(RESPONSE_SCHEMA, indent=2))
    print()
    print("=" * 70)
    print("USER MESSAGE (sample)")
    print("=" * 70)
    print(format_user_message(sample_task, sample_occupation))
    print()
    print("=" * 70)
    sys_chars = len(SYSTEM_PROMPT)
    print(f"System prompt chars: {sys_chars:,}   approx tokens (chars/4): {sys_chars // 4:,}")
    n_required = len(RESPONSE_SCHEMA["json_schema"]["schema"]["required"])
    print(f"Schema required fields: {n_required}")
    print("=" * 70)
