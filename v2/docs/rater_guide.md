# Rater Guide

## Generative AI Exposure Index — Tier 2 Human Validity Sample

**For:** Aaryan Mehta (researcher), Prof. Manoranjan Dash (supervisor), Dr. Shreya Mukherjee (supervisor)
**Purpose:** independent task-level rating of 100 O*NET tasks for comparison against the LLM scores
**Created:** 21 May 2026
**Revised:** 06 June 2026 — rubric **v3.2**, and the construct, disambiguation rule, and four criterion definitions/anchors below are now **reproduced verbatim from the system prompt given to GPT-4o** (see the boxed note in §2). Earlier revisions paraphrased them; this version removes any wording difference so that human–model disagreement is genuine, not an artefact of different instructions.
**Status:** Use as-is for the rating session. Any clarifications can be added in the margins; revisions to the guide itself trigger a new rating round.

---

## 1. What you are doing

You will independently rate 100 O*NET task statements against the same four-criterion rubric that GPT-4o is using. After all three of us have completed our ratings (blind to each other and to the LLM scores), the three sets of human ratings are averaged per criterion and compared to the LLM's scores. The headline statistic is Cohen's κ between the averaged human rating and the LLM rating, with κ ≥ 0.60 set as the pre-locked threshold for the within-project validity check.

The 100 tasks are a **simple random sample** drawn (with a fixed seed) from the scored corpus. Because the corpus is roughly 40–50% zero-gated, a sizeable share of your ratings will be of tasks the LLM gated to 0 — and you'll judge whether you agree they really should be zero — while the rest spread across the non-zero range in proportion to how often each score actually occurs.

You do **not** see the LLM scores while rating. Each rater works blind.

---

## 2. The construct you are measuring

> **Verbatim-parity note.** The construct below, the disambiguation rule (§3), and the four criterion definitions and anchors (§4) are **reproduced word-for-word from the system prompt given to GPT-4o.** This is deliberate: you and the model judge against identical wording, so any disagreement reflects genuine human-vs-model judgement rather than a difference in instructions. The model is given **only** these definitions and anchors; the worked examples in §5 are additional calibration for human raters and are *not* shown to the model.

You are evaluating whether current frontier Foundation Models — large language models (LLMs), vision-language models (VLMs), and multimodal generative systems — can substitute for the human worker on a given occupational task at human-equivalent or better proficiency.

You are NOT evaluating:

- Robotics, autonomous vehicles, or any AI requiring physical embodiment, actuators, or real-world sensors. These are out of scope.
- AI augmentation where the human worker remains required.
- Whether workers will actually lose their jobs (regulation, liability, and deployment cost are out of scope).
- Future or projected AI capabilities — evaluate against current frontier Foundation Models only, as they exist today.

---

## 3. The disambiguation rule (read carefully — this is the load-bearing rule)

O*NET task descriptions often do not specify implementation context. When a task could plausibly be performed using digital tools in a contemporary workplace, evaluate it under that digital implementation. This rule resolves ambiguity for Criterion 1 (Information Sufficiency); it does not change the other three criteria.

*Illustration (for raters; not part of the model's prompt): "Monitor patient vitals" could mean physical bedside observation or remote review of a digital telemetry dashboard; "review financial documents" could mean paper files or an electronic system. Where a digital implementation is plausible, evaluate that one.*

---

## 4. The four criteria (v3.2)

You will score the task on FOUR independent criteria, each on a 0 / 1 / 2 scale. The criteria are deliberately distinct: each captures a different reason a task might resist AI substitution. Score each criterion ONLY for the property it names, and do not let your judgement on one criterion leak into another. Each criterion states explicitly what it is NOT about — respect those boundaries.

The examples in each criterion illustrate the underlying principle; they are NOT a lookup table. Score every task by the criterion's definition. A task that resembles an example on the surface but differs in the underlying property must be scored by the property, not the resemblance. A task unlike any example is scored from the definition alone.

### Criterion 1 — Information Sufficiency

Can the task be completed using only information that can be received and acted on digitally (text, images, audio, structured data), with no requirement for real-time physical presence, manipulation of physical objects, or embodied sensory perception?

This is the ONLY criterion that judges physical vs. digital. The other three assume the task is digitally accessible and judge different barriers — do not re-judge physicality in them.

| Score | Meaning |
|---|---|
| 0 | Fundamentally requires physical presence, manual manipulation, or real-time embodied sensing. Example: positioning and welding steel beams. |
| 1 | Mostly digital but with a genuine physical component that cannot be separated out. Example: diagnosing a machine fault that needs both remote telemetry and a hands-on inspection. |
| 2 | Completable entirely through digital information and outputs. Example: reconciling figures in a financial spreadsheet. |

### Criterion 2 — Objective Verifiability

Does the task have a clear, objective standard of success — a checkable correct answer, a testable output, or measurable criteria — as opposed to success being a matter of subjective judgement, taste, or opinion?

This is NOT about whether the output is digital or physical (Criterion 1 owns that). A fully digital output can be entirely subjective. Judge only: can you objectively determine whether the result is correct?

| Score | Meaning |
|---|---|
| 0 | Success is inherently subjective or contested — there is no objective right answer. Example: writing an inspiring company mission statement (fluent and digital, but whether it is "good" is a matter of opinion). |
| 1 | Some objective elements, but success also depends on judgement that reasonable experts could dispute. Example: recommending which of several viable budgets to approve. |
| 2 | Objectively checkable — there is a correct answer, a testable result, or measurable criteria. Example: translating a document (fidelity is checkable), or extracting figures from invoices. |

### Criterion 3 — Contextual Independence

Can the task be completed by an agent that has only (a) the task description and (b) general knowledge — OR does it require real-time human interaction (negotiating, persuading, counselling, building trust, reading and responding to people) or organisation-specific tacit knowledge (relationships, internal history, undocumented local context) that a general-purpose model would not possess?

This is NOT about physical vs. digital (Criterion 1), and NOT about whether the model could produce the content (Criterion 4). A model might draft an excellent message yet be unable to BE the trusted human in a live negotiation. Judge only: does success require human-relational embedding or insider context? Context that could be written down and supplied — procedures, specifications, files, policies, client requirements — does NOT count as a barrier, because it can be provided to the model; only real-time human interaction or genuinely tacit/undocumented knowledge does.

| Score | Meaning |
|---|---|
| 0 | Success fundamentally depends on real-time interpersonal interaction, or on insider/relationship/tacit context the model cannot access. Example: counselling a grieving family member. |
| 1 | Benefits from such context, but a substantial portion could be done from the task description plus general knowledge. Example: preparing a client briefing that draws partly on the firm's prior dealings. |
| 2 | Self-contained — completable from the task description, any relevant documents, and general knowledge, even if it relies on company-specific procedures or files (which can be supplied). Example: summarising a research report; coding to a documented company style guide. |

### Criterion 4 — Capability Match

Setting aside the other three criteria, can a current frontier Foundation Model produce the core output of this task at a quality at or above that of an average human worker in the role?

Calibration: the benchmark is the AVERAGE HUMAN WORKER, not perfection. A competent human's work is also reviewed and occasionally corrected, so the fact that the model's output would receive normal review does NOT lower the score. A failure mode counts against the score only if it would make the output WORSE than an average human's. Do not lower this score because the task needs a human relationship or insider context — that is Criterion 3.

Before scoring, briefly consider both directions: what about this specific task is tractable for a current frontier Foundation Model, and what about it might make the model's output worse than an average human's. *(The model records these as two short reasoning notes before it scores; you can simply hold both in mind.)*

| Score | Meaning |
|---|---|
| 0 | Clearly below average-human quality on the core — frequently wrong, superficial, or a human must essentially redo it. Example: devising a novel mathematical proof. |
| 1 | Useful but below average-human quality — meaningfully assists, but a human must substantially complete or rework the core. Example: producing a first-draft analysis of a complex, unusual legal case. |
| 2 | At or above average-human-worker quality on the core, needing no more review than a human's work normally gets. Example: drafting routine business correspondence. |

**How the four combine (Design Y) — for your understanding; you do not compute this.** A task scores **0 overall** if Information Sufficiency = 0 OR Capability Match = 0 (the two "can AI even attempt it?" gates). Otherwise the overall score is the average of all four criteria ÷ 2, so Objective Verifiability and Contextual Independence pull the score down without zeroing it. Just score the four criteria; the overall number is derived. It helps to know that a subjective or relationship-heavy digital task lands in the *middle*, not at zero.

---

## 5. Worked examples

> These worked examples are **calibration for human raters and are not shown to the model** (the model receives only the definitions and anchors in §4). They illustrate the full gradient Design Y produces — including the two cases (subjective and relational) the redesign is specifically about.

### Example 1 — Fully exposed (everything aligns)

**Task:** *"Write Python code to extract data from a SQL database based on user-specified queries."*
**Occupation:** Data Analyst

| Criterion | Score | Reasoning |
|---|---|---|
| Information Sufficiency | 2 | Pure text and code; entirely digital. |
| Objective Verifiability | 2 | Code either runs and returns the right data or it does not — objectively checkable. |
| Contextual Independence | 2 | Self-contained; needs only the query spec and general knowledge. |
| Capability Match | 2 | Current models write this kind of code at or above average-analyst quality. |

**Overall: 1.0.** No gate; all four high.

### Example 2 — Gated (physical)

**Task:** *"Administer intramuscular injections to patients."*
**Occupation:** Registered Nurse

| Criterion | Score | Reasoning |
|---|---|---|
| Information Sufficiency | 0 | Requires real-time physical presence with the patient — no digital implementation. |
| Objective Verifiability | — | (not reached) |
| Contextual Independence | — | (not reached) |
| Capability Match | 0 | No current Foundation Model performs physical actions on a patient. |

**Overall: 0 (GATED).** Information Sufficiency = 0 is one of the two gates — physical embodiment is a categorical impossibility for a Foundation Model. You can stop scoring once a gate hits 0, though noting Capability Match = 0 too is fine.

### Example 3 — Subjective digital → modulated to the MIDDLE, not gated *(this is the redesign's point)*

**Task:** *"Write an inspiring vision statement for the organization."*
**Occupation:** Public Relations Manager

| Criterion | Score | Reasoning |
|---|---|---|
| Information Sufficiency | 2 | Entirely digital — text in, text out. |
| Objective Verifiability | 0 | There is no objective "correct" vision statement; whether it is inspiring is a matter of opinion. |
| Contextual Independence | 2 | Can be drafted from a description of the organisation and general knowledge. |
| Capability Match | 2 | Current models write fluent, polished vision statements at average-human quality. |

**Overall: mean(2,0,2,2)/2 = 0.75.** **Teaching point:** the task is subjective (Objective Verifiability = 0) but that does NOT gate it to zero — it modulates it down to 0.75. The AI can genuinely produce the deliverable; subjectivity just means there's no objective standard to certify it against. This is exactly the case the old rubric mishandled.

### Example 4 — Relational digital → modulated low, not gated

**Task:** *"Negotiate contract terms with a vendor."*
**Occupation:** Purchasing Manager

Assume a modern setting (negotiation by email / video is plausible, so not physically gated).

| Criterion | Score | Reasoning |
|---|---|---|
| Information Sufficiency | 2 | Can be conducted digitally (email, video). |
| Objective Verifiability | 1 | Some terms are objective (price, dates), but "a good deal" involves disputable judgement. |
| Contextual Independence | 0 | Success depends on a real-time human relationship — reading the counterparty, building trust, adapting live. |
| Capability Match | 1 | A model can draft strong negotiating positions, but cannot *be* the trusted human in the live exchange — a human must run the negotiation. |

**Overall: mean(2,1,0,1)/2 = 0.5.** **Teaching point:** Contextual Independence = 0 (the relational barrier) pulls the score down to 0.5 without zeroing it — the informational parts (preparing positions, drafting terms) are exposed, the relational part is not. Note we did NOT lower Capability Match because the task needs a relationship — that belongs in Contextual Independence (Criterion 3), not Criterion 4.

---

## 6. Procedure

1. **Open the rating sheet** (a spreadsheet with one row per task, columns for task ID, task text, occupation, and four blank score columns).
2. **Read the task and the occupation title** carefully.
3. **Apply the disambiguation rule** if the context is ambiguous.
4. **Score each criterion independently** on the 0/1/2 scale. Don't let one criterion influence another.
5. **Score blind to the LLM and to other raters** — do not look at anyone else's scores until all three of us have finished.
6. **Flag rather than guess** if a task is genuinely too ambiguous to score. We will discuss flagged tasks after the rating session and decide whether to retain or drop them from the analysis.
7. **Don't go back and revise** earlier ratings based on later ones. Consistency within each rater matters more than internal recalibration.

---

## 7. Time and pacing

Realistic estimate: about **2–3 minutes per task** once you've settled into the rubric, so roughly **3–5 hours total** per rater. Splitting into two or three sessions is fine; just try to keep each session's pacing consistent. Take breaks before fatigue starts to shift your scoring.

---

## 8. After the rating

Once all three of us have submitted independent ratings:

- **Inter-rater agreement** among the three of us is computed using Krippendorff's α (appropriate for three raters on ordinal data).
- **Validity** is computed as Cohen's κ between the averaged human rating and the LLM's score, per criterion and on the composite.
- **Both numbers are reported**, regardless of whether either crosses the 0.60 threshold. The threshold was locked in advance precisely so that the result can be reported transparently rather than reinterpreted post-hoc.

Tasks flagged as "too ambiguous" during rating are listed separately in supplementary materials with the reason. They are not used to compute κ.

---

*If anything in this guide is unclear before the rating session begins, raise it and the guide can be revised. Once rating starts, the guide is frozen for that round.*
