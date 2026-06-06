# Project Data Documentation
## Generative AI Vulnerability Framework — v2

**Maintained by:** Aaryan Mehta
**Started:** May 2026
**Last updated:** May 2026

This document is a living record of every dataset, design choice, and methodological decision made in this project — what it is, why we chose it, what alternatives we considered and rejected, and what we openly acknowledge as a limitation. It is updated at every step. Nothing in this project is assumed; everything is verified, documented, and traceable to its rationale here.

The project measures **Generative AI exposure** at the occupation level — specifically, the degree to which Foundation Models (large language models, vision-language models, and multimodal generative systems) can perform the constituent tasks of an occupation. It does not measure exposure to physical AI systems, robotics, or autonomous embodied systems; this scope decision is documented and defended in Section 3.3. Part 2 of the project (separately planned) will combine the exposure index with an Adaptation Capacity Index built from PIAAC microdata to produce a two-dimensional Generative AI Vulnerability Framework.

The document is structured to be read from start to finish. Section 1 establishes the data we are working with. Section 2 reviews the literature on O*NET data quality and how prior AI exposure papers have used it. Section 3 lays out the full methodology — the rubric, the aggregation rule, the validation strategy, the BERT-based reproducibility analysis, the analytical outputs, and the limitations of the design. Section 4 is a chronological log of decisions. Section 5 documents the alternatives we considered and rejected, with reasoning, so that any reader can reconstruct how we arrived at each choice. Section 6 lists known methodological limitations that we accept. Sections 7 and 8 list pending data acquisitions and immediate next steps.

---

## 1. O*NET 30.2 Database

### Source

**Provider:** National Center for O\*NET Development, U.S. Department of Labor
**Version:** O\*NET 30.2
**Release date:** February 2026
**Downloaded:** 07 May 2026
**Download URL:** https://www.onetcenter.org/database.html
**Official data dictionary:** https://www.onetcenter.org/dictionary/30.2/excel/
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
**Format downloaded:** Microsoft Excel (XLSX), full database zip archive
**Stored at:** `v2/data/raw/onet/`

### What O*NET Is

O\*NET (Occupational Information Network) is the U.S. Department of Labor's primary source of occupational data. It collects information by surveying **incumbent workers** (people currently employed in each occupation) and **occupational experts** (supervisors and domain specialists). Scores represent the **mean of survey responses** — they are aggregated professional judgments, not objective physical measurements. Each occupation in O\*NET is identified by an **O\*NET-SOC Code**, a 10-character code based on the Standard Occupational Classification (SOC) system (e.g., `11-1011.00` = Chief Executives).

The database covers **1,016 occupations**. Not every occupation is resurveyed in every release — O\*NET works through occupations on a rolling cycle, prioritising those with high employment or rapid change. Individual occupation entries therefore carry different survey dates; some were updated in 2025, others in 2020 or earlier. The `Occupation Level Metadata` file records when each occupation was last surveyed and the sample size used.

---

### Files in Use

---

#### 1.1 Occupation Data

**File:** `Occupation Data.xlsx`
**Rows:** 1,016 (one per occupation)
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/occupation_data.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| O\*NET-SOC Code | Character (10) | Unique occupation identifier. Format: `XX-XXXX.XX` |
| Title | Character (≤150) | Official occupational title |
| Description | Character (≤1000) | Plain-language description of the occupation's duties |

**What it is:**
The master list of all 1,016 occupations in the database. Every other file links back to this via the O\*NET-SOC Code.

**Why we are using it:**
Every exposure score we compute will be indexed to an O\*NET-SOC Code. This file is the definitive list of what those codes map to. We will also use the occupation descriptions as supplementary text where needed.

**Important notes from inspection:**
- 1,016 occupations confirmed.
- The SOC structure reflects the 2010 SOC update.
- The `.00` suffix on most codes indicates a single occupation. Codes ending in `.01`, `.02` etc. are O\*NET-specific sub-occupations not in the base SOC.

---

#### 1.2 Task Statements

**File:** `Task Statements.xlsx`
**Rows:** 18,796 tasks across 923 occupations
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/task_statements.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| O\*NET-SOC Code | Character (10) | Occupation identifier |
| Title | Character (≤150) | Occupation title |
| Task ID | Integer | Unique identifier for this task |
| Task | Character (≤1000) | The task description — a sentence describing one thing workers do |
| Task Type | Character (≤12) | `Core`, `Supplemental`, or none — see below |
| Incumbents Responding | Integer | Number of surveyed workers who rated this task |
| Date | Character (7) | When this task's data was last updated (MM/YYYY) |
| Domain Source | Character (≤30) | Who provided the data: `Incumbent`, `Occupational Expert`, `Analyst`, or `Analyst–Transition` |

**Task Type definitions (from official documentation):**
- **Core:** Relevance ≥ 67% AND mean importance rating ≥ 3.0. These are tasks that most workers in the occupation actually perform and consider important.
- **Supplemental:** Either relevance ≥ 67% but importance < 3.0, OR relevance < 67% regardless of importance. These are tasks performed by some workers or considered less central.
- **None (no Task Type assigned):** Tasks that have not yet completed the rating cycle. These tasks are coded by analysts and have no Importance (IM) rating.

In O\*NET's native representation, the third category appears as an empty cell. In the master file built by `src/01_build_master_file.py`, we deliberately replace this empty cell with the explicit string `"Unrated"` rather than leaving it blank or using the literal string `"None"`. The reason is purely operational: `"None"` is in pandas' default `na_values` list, so any CSV round-trip would silently re-parse it back to a missing value, defeating the purpose of having an explicit categorical label. `"Unrated"` is descriptive, not in any default null-sentinel list, and survives reading and writing cleanly. The master file therefore uses values `Core` / `Supplemental` / `Unrated` for `task_type`. The 845 Unrated tasks are the same set as the 845 Analyst-coded tasks in the Domain Source breakdown — these are not separate filters.

**What it is:**
The primary text source for this project. Each row is one task statement — a specific, occupation-level description of something workers do (e.g., *"Prepare financial reports for management review"* for accountants). These task statements are the input text that the LLM-as-judge rubric (Section 3) will score.

**Why we are using it:**
Task statements are the most specific and directly actionable text in O\*NET. They describe concrete work behaviours, which makes them suitable for evaluation against Generative AI capabilities. Unlike broader feature categories (Skills, Abilities), task statements answer the question *"what does this worker actually do?"* — which is the right question for a Generative AI exposure index.

**Important notes from inspection:**
- 18,796 total tasks across 923 occupations. **93 occupations in the master list have no task statements.** These 93 occupations are excluded from the exposure index as a methodological necessity — a task-based exposure index cannot be computed without task text. They are listed in the supplementary materials.
- Tasks per occupation: minimum 4, maximum 40, average 20.4.
- Task type breakdown: Core = 13,643 (72.6%), Supplemental = 4,308 (22.9%), None = 845 (4.5%).
- Domain source breakdown: Incumbent = 13,193 (70.2%), Occupational Expert = 4,413 (23.5%), Analyst = 845 (4.5%), Analyst–Transition = 345 (1.8%).
- The 845 "None" Task Type rows correspond to the 845 Analyst-coded tasks — these have no IM ratings because they have not been surveyed. Treatment of these tasks is detailed in Section 3.2.
- Both Core and Supplemental tasks are used. Supplemental tasks still describe real work behaviours; excluding them would remove nearly a quarter of the task text.

---

#### 1.3 Task Ratings

**File:** `Task Ratings.xlsx`
**Rows:** 161,559 (multiple rating scales per task)
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/task_ratings.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| O\*NET-SOC Code | Character (10) | Occupation identifier |
| Title | Character (≤150) | Occupation title |
| Task ID | Integer | Links back to Task Statements |
| Task | Character (≤1000) | Task description (repeated for convenience) |
| Scale ID | Character | Which scale this row reports — `IM`, `RT`, or `FT` |
| Scale Name | Character | Full name of the scale |
| Category | Integer | For `FT` only: the frequency category (1–7) |
| Data Value | Decimal | The rating value for this scale/category |
| N | Integer | Number of respondents who rated this task |
| Standard Error | Decimal | Standard error of the estimate |
| Lower CI Bound | Decimal | 95% confidence interval lower bound |
| Upper CI Bound | Decimal | 95% confidence interval upper bound |
| Recommend Suppress | Character | `Y` = data precision is too low to report reliably; `N` = safe to use |
| Date | Character (7) | When updated |
| Domain Source | Character (≤30) | Data source |

**Three scales present in this file:**

| Scale ID | Scale Name | Range | What it measures |
|----------|-----------|-------|-----------------|
| `IM` | Importance | 1–5 | How important is this task to performing the job? (1 = Not Important → 5 = Extremely Important). One row per task. |
| `RT` | Relevance of Task | 0–100 | What percentage of surveyed workers actually perform this task? One row per task. |
| `FT` | Frequency of Task | 0–100 per category | Distribution across 7 frequency categories. Seven rows per task (one per category). |

**Frequency of Task categories (Scale ID = FT):**

| Category | Description |
|----------|-------------|
| 1 | Yearly or less |
| 2 | More than yearly |
| 3 | More than monthly |
| 4 | More than weekly |
| 5 | Daily |
| 6 | Several times daily |
| 7 | Hourly or more |

**What it is:**
The ratings file that tells us how important and how widely performed each task is. The `IM` (Importance) score is the primary weighting variable used when aggregating task-level rubric scores to occupation level (Section 3.2). The `RT` (Relevance) score tells us what fraction of workers actually perform the task and may be examined as an alternative weighting in supplementary analysis.

**Why we are using it:**
When task-level rubric scores are aggregated to occupation level, all tasks are not equal. A task rated 4.5 importance (central to the job) should contribute more to the occupation's exposure score than a task rated 2.0 importance (peripheral). The IM scale provides this weighting.

**Important notes from inspection:**
- Scale breakdown: FT = 125,657 rows, IM = 17,951 rows, RT = 17,951 rows. The FT rows are 7× more numerous because each task has 7 frequency category rows.
- `Recommend Suppress = Y`: 940 rows flagged for low data precision across all scales. **These rows are excluded from analysis** following O\*NET's own guidance.
- The IM scale is a simple mean on a 1–5 scale — suitable directly as a weight.
- Sample IM scores for Chief Executives tasks ranged from 4.17 to 4.52, confirming the scale captures genuine variation in task centrality.
- The 845 Analyst-coded tasks (Task Type = None in the Task Statements file) have no rows in the IM scale — they were never surveyed. Their treatment is detailed in Section 3.2.

---

#### 1.4 Task Categories

**File:** `Task Categories.xlsx`
**Rows:** 7 (one per FT frequency category)
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/task_categories.html

**Columns:**

| Column | Description |
|--------|-------------|
| Scale ID | Always `FT` |
| Scale Name | "Frequency of Task (Categories 1–7)" |
| Category | Integer 1–7 |
| Category Description | Plain-language label for each category |

**What it is:**
A small lookup table that decodes the 7 frequency categories in the Task Ratings `FT` scale into human-readable labels.

**Why we are using it:**
Reference document. May be needed if frequency-weighted exposure scores are computed as a supplementary check, or if task frequency distributions are reported in the paper.

---

#### 1.5 Tasks to DWAs

**File:** `Tasks to DWAs.xlsx`
**Rows:** 23,850
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/tasks_to_dwas.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| O\*NET-SOC Code | Character (10) | Occupation identifier |
| Title | Character (≤150) | Occupation title |
| Task ID | Integer | Links to Task Statements |
| Task | Character (≤1000) | Task description |
| DWA ID | Character (≤20) | Detailed Work Activity identifier |
| DWA Title | Character (≤150) | The DWA description |
| Date | Character (7) | When updated |
| Domain Source | Character (≤30) | Data source |

**What it is:**
A crosswalk between occupation-specific task statements and the standardised Detailed Work Activity (DWA) vocabulary. The relationship is many-to-many: one task can map to multiple DWAs, and one DWA can appear in multiple occupations' tasks.

**Why we are retaining this file:**
DWAs provide a standardised, cross-occupation vocabulary of work activities. Where task statements are occupation-specific ("Prepare quarterly earnings reports for the CFO"), DWAs abstract to a standardised form ("Prepare financial documents"). This file is retained for structural reference — it maps the relationship between occupation-specific task language and the broader activity taxonomy — and may be used in supplementary analysis examining how DWA-level concepts cluster across exposure space.

**Role in primary analysis:**
DWAs are not used as primary or fallback scoring text. Task statements are the required input because: (a) DWAs are too abstract to carry the occupation-specific language that distinguishes meaningful exposure differences across occupations; (b) individual DWA titles are too short and general for reliable scoring; (c) each DWA maps to dozens of occupations, destroying the within-occupation signal that task statements preserve. Whether DWA-level information serves any useful quality control function during scoring is an open question to be resolved during execution, not predetermined here.

**Important notes from inspection:**
- 23,850 mapping rows connecting 18,796 tasks to 2,087 DWAs. Confirms many-to-many structure.

---

#### 1.6 DWA Reference

**File:** `DWA Reference.xlsx`
**Rows:** 2,087 (one per DWA)
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/dwa_reference.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| Element ID | Character | O\*NET Content Model position of the parent Work Activity |
| Element Name | Character | Name of the parent Work Activity (e.g., "Getting Information") |
| IWA ID | Character | Intermediate Work Activity identifier |
| IWA Title | Character | IWA description — one level above DWA |
| DWA ID | Character | Unique DWA identifier |
| DWA Title | Character (≤150) | The DWA description statement |

**Hierarchy:** O\*NET organises work activities in three levels:
`Work Activity (broad)` → `Intermediate Work Activity (IWA)` → `Detailed Work Activity (DWA)`
Each DWA belongs to exactly one IWA, which belongs to exactly one Work Activity.

**What it is:**
The master list of all 2,087 Detailed Work Activities — the standardised, cross-occupation task vocabulary.

**Why we are retaining this file:**
Reference document. The DWA taxonomy situates each task within a broader conceptual structure of work activities — useful for interpreting and communicating results. When reporting that a cluster of tasks in a given occupation is highly exposed, we can identify which Intermediate Work Activity (IWA) or Work Activity those tasks belong to, providing theoretical grounding for the finding. DWA titles are not used as primary scoring text.

---

#### 1.7 Emerging Tasks

**File:** `Emerging Tasks.xlsx`
**Rows:** 328 tasks across 235 occupations
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/emerging_tasks.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| O\*NET-SOC Code | Character (10) | Occupation identifier |
| Title | Character (≤150) | Occupation title |
| Task | Character (≤1000) | Description of the new or revised task |
| Category | Character | `New` — entirely new task; `Revision` — updated version of an existing task |
| Original Task ID | Integer | For Revisions only: ID of the task being replaced |
| Original Task | Character (≤1000) | For Revisions only: text of the task being replaced |
| Date | Character (7) | When added (most recent entries: 08/2025) |
| Domain Source | Character (≤30) | Source: Incumbent, Occupational Expert, or research into emerging technologies |

**What it is:**
A record of tasks that are newly appearing in occupations or being revised. These tasks have not yet completed the full O\*NET data collection cycle — they are flagged as emerging, not yet incorporated into the main Task Statements file.

**Why we are retaining this file:**
Emerging tasks represent the frontier of occupational change. However, because they have not completed O*NET's full data collection cycle, they carry no Importance (IM) ratings.

**Treatment in analysis:**
Emerging tasks are **excluded from the primary exposure index computation.** This treatment is distinct from the treatment of analyst-coded tasks (Section 3.2). Emerging tasks have not stabilised in the O*NET corpus and are flagged as speculative additions; analyst-coded tasks have stabilised but lack incumbent ratings. The emerging tasks may be examined in a supplementary check once the primary index is built; the form of any such check is left open.

**Important notes from inspection:**
- 328 total emerging tasks: 275 New (83.8%), 53 Revisions (16.2%).
- Across 235 occupations.
- Most recent date: 08/2025.

---

#### 1.8 Occupation Level Metadata

**File:** `Occupation Level Metadata.xlsx`
**Rows:** 32,202 (multiple items per occupation)
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/occupation_level_metadata.html

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| O\*NET-SOC Code | Character (10) | Occupation identifier |
| Title | Character (≤150) | Occupation title |
| Item | Character | The specific statistic being reported |
| Response | Character | The response category for this item (where applicable) |
| N | Integer | Sample size for this occupation's data collection |
| Percent | Decimal | Percentage in this response category |
| Date | Character (7) | When this occupation's data was collected |

**Items tracked:**
`Data Collection Mode` (Paper vs Web), `Employee Completeness Rate`, `Employee Response Rate`, `Establishment Eligibility Rate`, `Establishment Response Rate`, `How Long at Current Job`, `How Much Experience Performing Work in this Occupation`, `Industry Division`, `NAICS Sector`, `OE Completeness Rate`, `OE Response Rate`, `Occupation Eligibility Rate`, `Total Completed Questionnaires`

**What it is:**
Data quality and provenance information for every occupation's survey data.

**Why we are using it:**
Two purposes. First, to flag occupations with very small sample sizes or old survey dates, so that confidence in their task scores is clearly documented. Second, to report data provenance in the paper.

**Important notes from inspection:**
- 878 occupations have metadata entries; 45 occupations have task statements but no metadata (these are typically analyst-coded occupations).
- Survey dates range from 2004 to 2025. Nearly half (460) of metadata-bearing occupations were last surveyed before 2021.
- Sample sizes range from 19 to 297 respondents. Mean: 65.7. Median: 63.

---

#### 1.9 Scales Reference

**File:** `Scales Reference.xlsx`
**Rows:** 31 (one per scale)
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/scales_reference.html

**Columns:** Scale ID, Scale Name, Minimum, Maximum

**What it is:**
A lookup table defining all 31 measurement scales used across the O\*NET database. For this project, the relevant scales are:
- `IM` — Importance (1–5): the primary weighting scale for tasks
- `RT` — Relevance of Task (0–100): percentage of workers performing the task
- `FT` — Frequency of Task, category distribution (0–100 per category)
- `LV` — Level (0–7): used in Skills, Abilities etc. (not primary for this project)

**Why we are using it:**
Reference document. Consulted whenever we encounter a Scale ID in another file to confirm what the numbers mean and their valid range.

---

#### 1.10 Level Scale Anchors

**File:** `Level Scale Anchors.xlsx`
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/level_scale_anchors.html

**Columns:** Element ID, Element Name, Scale ID, Scale Name, Anchor Value, Anchor Description

**What it is:**
Behavioural anchors for the Level (`LV`) scale. For each O\*NET element that uses the Level scale, this file provides concrete examples of what a score of 2, 4, and 6 looks like in practice.

**Why we are using it:**
Reference document. Consulted if Level-scale variables are used in supplementary analysis.

---

#### 1.11 Content Model Reference

**File:** `Content Model Reference.xlsx`
**Official description:** https://www.onetcenter.org/dictionary/30.2/excel/content_model_reference.html

**Columns:** Element ID, Element Name, Description

**What it is:**
The complete taxonomy of all elements in O\*NET's Content Model.

**Why we are using it:**
Reference document. The authoritative source for understanding what any O\*NET variable actually measures.

---

## 2. Literature Review: O*NET Data Recency and Quality Standards

*Conducted: 08 May 2026. Sources verified via direct web fetch and search.*

### 2.1 How O*NET Updates Work — The Critical Distinction

The O*NET update cycle is more nuanced than its headline figures suggest, and understanding this is essential for making a defensible data quality decision.

**What O*NET updates annually:**
O*NET states that approximately 923 occupations are touched in each annual release. However, the content of those updates varies significantly by type. The following are updated from external sources (job postings, analyst review, machine learning) without new incumbent surveys: technology skills, alternate titles, tools used designations, and related occupation linkages. These can be refreshed for all occupations every year without conducting a single new survey.

**What requires a new incumbent survey:**
Task statements and their ratings (importance, relevance, frequency) are only updated when a new incumbent survey is conducted for that occupation. O*NET conducts approximately 78 full incumbent surveys per annual cycle. This means in any given year, roughly 78 of the 923 occupations receive updated task content from workers; the remaining ~845 retain their previous task data. The `Date` field in the Task Statements and Task Ratings files records the year the incumbent survey was actually conducted — not the year the database entry was last touched for other content types.

**Implication:** An occupation showing a survey date of 2015 in the Task Statements file has task importance and relevance data from 2015. It may have received technology skill updates every year since, but the core task content is 11 years old. This is the correct interpretation of the date field.

### 2.2 O*NET's Prioritisation Logic — Why Older Dates Are Not Random

O*NET does not resurvey occupations at random. Its prioritisation is documented through its Bright Outlook programme and its focus on high-growth, technology-intensive, and rapidly changing occupations. Occupations projected to grow faster than average, or those in high-demand industry clusters, are resurveyed first and most frequently.

**The implication for our project is significant:** Occupations with older survey dates are, in aggregate, the ones O*NET has judged to be more stable — those where task content has not changed enough to justify a new survey. This is not an argument that their data is wrong; it is an argument that their task content has been implicitly judged by O*NET as still approximately valid.

This does not mean older data is as good as newer data. A 2004 survey date predates modern cloud computing, smartphones, and any meaningful AI presence in the workplace. Task content for that occupation has almost certainly shifted. The argument applies most reasonably to occupations surveyed in the 2015–2020 range.

**Source:** O*NET Resource Center, Data Updates page (onetcenter.org/dataUpdates.html); O*NET Data Collection Overview (onetcenter.org/dataCollection.html).

### 2.3 What the Academic Literature Says About O*NET Task Stability

**Consoli et al. (2023), Research Policy:** The task-based labour economics literature has historically assumed that occupational task content changes slowly, treating task requirements as approximately time-invariant. Consoli et al. test this assumption directly and find that within-occupation task reorientation does occur, but primarily over long time horizons (decades), and that it accelerated in the 1990s before decelerating in the 2000s. The conclusion relevant to this project: task content is stable enough over 5–10 year windows for cross-sectional analysis, but not stable indefinitely.

**Handel (2016), Journal for Labour Market Research:** The most comprehensive academic review of O*NET's content model. Handel notes that O*NET was explicitly designed with regular resurveying in mind, and that tasks and work activity ratings are its most reliable data for capturing occupational content. He flags two legitimate concerns: (1) a methodological shift in 2008 where some data collection moved from incumbent self-reports to analyst ratings, creating a comparability issue across that boundary; (2) that O*NET is organised for operational use rather than longitudinal research. Neither concern directly applies to our cross-sectional use of a single database version.

**Source:** Handel, M.J. (2016). The O\*NET content model: strengths and limitations. *Journal for Labour Market Research*, 49(2), 157–176.

### 2.4 What Published AI Exposure Papers Actually Do

A review of the major published AI exposure indices reveals a consistent pattern: **none of them apply survey date cutoffs or minimum sample size thresholds to O*NET task data.**

| Paper | O*NET Version Used | Occupations Included | Quality Filters |
|---|---|---|---|
| Felten et al. (2021), Strategic Management Journal | Not specified | Full dataset | None documented |
| Eloundou et al. (2023), Science | O\*NET 27.2 | All 1,016 | None documented |
| Pew Research Center (2023) | O\*NET 27.3 | ~900 occupations | None documented |
| Anthropic (2025), Labour Market Impacts | Not specified | ~800 occupations | None documented |
| Webb (2020) | Not specified | Full dataset | None documented |

This does not mean quality filtering is wrong — it means the field has not yet standardised on it. Our project aims to be more methodologically explicit than the existing literature, not less.

### 2.5 Decision Reached: Occupation Inclusion Criteria

The literature review establishes that no major published AI exposure paper applies minimum sample size thresholds or survey date cutoffs to O*NET task data. The field standard is to use the full available dataset.

**Rule 1 — Include all occupations with task statements: 923 occupations**
All 923 occupations for which O*NET provides task statements are included in the working set. Survey date and sample size (where available from Occupation Level Metadata) are attached to every occupation in the master file as informational variables.

**Rule 2 — Exclude occupations with no task statements: 93 occupations**
Methodological necessity, not a quality filter. A task-based exposure index cannot be computed without task text. These occupations are listed in supplementary materials.

**Rule 3 — Exclude Recommend Suppress = Y rows from Task Ratings**
O*NET's own data quality flag, not a researcher-imposed threshold. Affects 940 rows out of 161,559 in the Task Ratings file — a negligible proportion.

**Final working set: 923 occupations.**

**Sources consulted:**
- O\*NET Resource Center: onetcenter.org/dataUpdates.html
- O\*NET Data Collection Overview: onetcenter.org/dataCollection.html
- Handel (2016): link.springer.com/article/10.1007/s12651-016-0199-8
- Consoli et al. (2023): sciencedirect.com/science/article/pii/S0048733322001792
- Eloundou et al. (2023): arxiv.org/abs/2303.10130
- Felten et al. (2021): sms.onlinelibrary.wiley.com/doi/full/10.1002/smj.3286
- Anthropic Labour Market Impacts (2025): anthropic.com/research/labor-market-impacts
- Pew Research Center O\*NET Methodology (2023): pewresearch.org/social-trends/2023/07/26/2023-ai-and-jobs-methodology-for-onet-analysis/

---

## 3. Generative AI Exposure Index Methodology

This section lays out the full methodology for the Generative AI Exposure Index — the input text, the rubric, the aggregation rule, the validation strategy, the BERT-based reproducibility analysis, the analytical outputs, the operational protocol, and the limitations of the design. Read in order, it explains exactly what we are building and why.

### 3.1 Why Raw Semantic Similarity Is Insufficient

The most straightforward approach to computing exposure from text is semantic similarity: embed each O*NET task statement and a set of Foundation Model capability descriptions using a sentence-transformer model, then compute cosine similarity between each task and each capability. The occupation-level exposure score would then be the importance-weighted mean of its task similarities.

This approach is transparent and reproducible. However, it has a fundamental problem that is particularly acute for domain-specific text: the **vocabulary gap problem.**

Sentence-transformer models (including the widely used `all-MiniLM` and `all-mpnet` families) are trained primarily on general-domain text corpora. O*NET task statements use an occupational vocabulary — specialised terminology, professional jargon, and domain-specific phrasing — that is under-represented in general training data. Foundation Model capability descriptions in model cards and technical reports use a similarly specialised technical vocabulary. The result is that standard sentence-transformers frequently assign low cosine similarity to tasks and capabilities that are semantically equivalent in meaning but use different surface vocabularies. A task described as *"perform statistical arbitrage"* may score low similarity to *"execute quantitative trading strategies"* not because they are genuinely different in exposure potential, but because of how each phrase distributes in general-domain training corpora.

The practical consequence: raw cosine similarity scores are noisy proxies for actual substitutability. They measure surface lexical proximity, not whether current Foundation Models can actually do the task. For an index whose validity depends on the latter, this is a design-level weakness.

(Note: BERT-based embeddings are still used in this project, but as a methodological characterisation layer on top of the rubric scoring — see Section 3.5 — not as the primary scoring method.)

### 3.2 The LLM-as-Judge Approach with Non-Compensatory Aggregation

The LLM-as-judge methodology, introduced in Eloundou et al. (2023) and independently applied in Anthropic (2025), addresses the vocabulary gap problem directly. Rather than measuring the distance between two text embeddings, it applies a structured rubric to each task statement, asking a large language model to evaluate whether current Foundation Models could perform that task.

**The rubric applied to each O*NET task statement (v3.1).**

A large language model evaluates each task statement against four criteria, each scored 0 / 1 / 2. The criteria are **redesigned in v3.1 (03 June 2026)** so that each captures a *distinct* barrier to AI substitution. The earlier v3 criteria collapsed empirically — three of the four measured the same "physical vs. digital" axis (correlations 0.95–0.99 in the first pilot) and the composite took only three values. The redesign (full evidence and reasoning in Section 5.23) grounds each criterion in a specific, well-established bottleneck to automation from the labour-economics literature, and the reason each citation was chosen is explained below — not merely cited — because the soundness of the construct depends on that grounding.

1. **Information Sufficiency** — *the physical / embodiment barrier.* Can the task be completed using only digitally-conveyable information (text, images, audio, structured data), with no requirement for real-time physical presence, manipulation of physical objects, or embodied sensory perception? *This is the only criterion that judges physical vs. digital; the other three assume digital accessibility.*
   - **Why this criterion, and why it is sound:** Frey & Osborne (2013) identify "perception and manipulation" — physical dexterity in unstructured environments — as the first of three engineering bottlenecks to computerisation, and Autor, Levy & Murnane (2003) classify physical work as "non-routine manual," the task type least susceptible to substitution by information technology. For *Generative* AI specifically the logic is even sharper: Foundation Models are disembodied — they process and emit symbols but cannot act on or sense the physical world in real time — so physical embodiment is a *categorical* impossibility for this technology, not merely a difficulty. That is why this criterion is one of the two hard gates (Design Y, below).

2. **Objective Verifiability** — *the verifiable-feedback barrier.* Does the task have a clear, objective standard of success — a checkable correct answer, a testable output, or measurable criteria — as opposed to success being a matter of subjective judgement, taste, or opinion? *This is not about the medium of the output (Criterion 1 owns physical vs. digital); a fully digital output can be entirely subjective.*
   - **Why this criterion, and why it is sound:** Brynjolfsson, Mitchell & Rock (2018), in the study most directly about machine *learnability* of tasks, place "the task provides clear feedback with well-defined goals and metrics" at the centre of their Suitability-for-Machine-Learning rubric — because a system cannot be trained on, or trusted for, a task whose success cannot be checked. The same logic transfers to substitution by a Foundation Model: if you cannot verify the model's output is correct, you cannot trust it to *replace* the human, because a human would still be needed to judge it. This criterion also absorbs Frey & Osborne's second bottleneck, "creative intelligence" — genuinely original or creative work resists automation precisely because there is no objective standard for a "correct" creative output. (Redefined in v3.1 from the broken "Output Verifiability," which had keyed on output *medium*; see Section 5.23.)

3. **Contextual Independence** — *the social and tacit-knowledge barrier.* Can the task be completed by an agent that has only the task description plus general knowledge, or does it require real-time human interaction (negotiating, persuading, counselling, building trust) or organisation-specific tacit knowledge (relationships, internal history, undocumented local context)? *This is not about physical vs. digital (Criterion 1) and not about whether the model could produce the content (Criterion 4).*
   - **Why this criterion, and why it is sound:** This fuses the two most robust non-physical bottlenecks in the literature. Frey & Osborne's third bottleneck is "social intelligence" (negotiation, persuasion, care), and Deming (2017) shows empirically that social-skill-intensive work has *grown* in labour-market value precisely because it complements rather than competes with automation. Separately, Autor (2015) invokes Polanyi's Paradox — "we know more than we can tell" — to explain why tasks resting on **tacit**, undocumented, context-specific knowledge resist automation: a general-purpose model only has what is written down, so it cannot access the insider context that such tasks require. Both reduce to one operational question — *does success require something beyond the task description plus general knowledge?* — which is why they are combined into a single criterion. (Replaces the broken "Decomposability," which did no independent work — every below-2 score in the first pilot fell on a physical task; see Section 5.23.)
   - **v3.2 refinement (04 June 2026):** The v3.1 re-pilot showed this criterion was *over-applied* — the model docked points for any organisation-specific context (procedures, files, policies) even when that context is documentable and could simply be supplied to the model, which systematically under-scored routine digital cognitive work (the most exposed category). The fix is a single clarifying sentence drawing the line at the right place: *documentable context that could be written down and provided is not a barrier; only real-time human interaction or genuinely tacit/undocumented knowledge is.* This is faithful to the underlying Polanyi/tacit-knowledge construct — the barrier was always meant to be *tacit* knowledge, not merely *specific* knowledge. See Decision History 5.25.

4. **Capability Match** — *the raw current-capability barrier.* Setting aside the other three criteria, can a current frontier Foundation Model produce the core output of this task at a quality at or above that of an average human worker in the role? *The benchmark is the average human worker, not perfection: a competent human's work is also reviewed and corrected, so "would receive normal review" does not lower the score; a failure mode counts only if it makes the output worse than an average human's.*
   - **Why this criterion, and why it is sound:** The three bottleneck criteria above are technology-agnostic — they describe what *any* automation struggles with. Capability Match adds the Generative-AI-specific layer that the older frameworks lack: even where a task is digital, verifiable, and self-contained, today's models may simply not be good enough. Eloundou et al. (2023) operationalise current-LLM capability directly (can the model materially perform the task), and Brynjolfsson, Mitchell & Rock note that tasks requiring "long chains of reasoning or complex planning" exceed current learnability — the kind of capability ceiling this criterion captures. The **human-equivalent recalibration** (v3.1) corrects a v3 error: the v3 bar ("reliable enough to use without per-instance re-checking") was an impossible standard that no human meets either, which is why the model never once scored a 2 in the first pilot (Section 5.23). Because "below average-human capability" means the model genuinely cannot substitute, this criterion is the second hard gate.

Each criterion is scored on a three-point scale (0 = the barrier fully applies; 1 = partial; 2 = the barrier is absent). The exact anchor wording, with deliberately pattern-breaking and domain-diverse examples and an explicit anti-anchoring instruction, is in `src/rubric_prompt.py` and reproduced in the rater guide. **The anti-anchoring instruction** — telling the model that examples illustrate the principle and are not a lookup table, and that tasks must be scored by the underlying property rather than surface resemblance to an example — is a deliberate mitigation of the availability/anchoring bias that examples can induce in LLM evaluators (Suri et al. 2024); it is the same bias-aware design philosophy as the two-field structure of Criterion 4.

**Implementation specifics:**
- Primary scoring model: GPT-4o, fixed version `gpt-4o-2024-11-20` (recorded in supplementary materials with date of scoring run).
- Temperature: T = 0, plus a fixed `seed` (20260603), for best-effort determinism within the model version.
- API channel: OpenAI **synchronous** Chat Completions API, paced under the account's per-minute token limit, with checkpoint/resume. The original design used the Batch API for its 50% discount, but the funded account is Usage Tier 1, whose Batch enqueued-token limit for gpt-4o is only 90,000 tokens — against a ~38.3M-token full job (425× over), making Batch unusable even for the 75-task pilot (~153K tokens). The synchronous API is governed by the 30,000 TPM limit instead of the Batch queue, so it runs on this account today. Cost is higher than Batch (no 50% discount) but partially offset by automatic prompt caching of the identical system prompt. See Section 5.22 for the full decision record and Section 9.5 for the implementation log. The scoring script (`src/03_score_tasks.py`) checkpoints after every task, so the ~28–31-hour full run is resumable across sessions without losing or re-paying for completed work.
- Output format: structured JSON via OpenAI's structured outputs feature (`response_format: {"type": "json_schema", "strict": true, ...}`). The schema requires nine fields per task: a per-criterion reasoning string and integer score for each of the four criteria, with Criterion 4 having two reasoning fields (`capability_match_what_works` and `capability_match_what_might_fail`) instead of one. Schema enforcement guarantees the response is valid JSON with the correct fields; format-related parse failures are eliminated by construction.
- Chain-of-thought reasoning: Each reasoning field appears in the schema *before* its corresponding score field. The model articulates its reasoning before committing to an integer. This is a documented mitigation against both stochastic variance and self-assessment bias — direct zero-shot scoring on multi-dimensional judgements is known to be noisier and more biased than reasoning-first scoring.
- Self-assessment bias mitigation at the prompt level: Criterion 4 (Capability Match) has two reasoning fields rather than one. Both are schema-required: the model cannot leave either empty. The fields are neutrally named (`what_works` and `what_might_fail`) so neither pre-loads any specific content. The prompt instructs the model to bring its own task-specific reasoning to each. This forces balanced consideration without anchoring on specific failure modes that a list in the prompt would induce. Cognitive bias literature (Suri et al. 2024 on LLM anchoring; Echterhoff et al., Itzhak et al. on cognitive biases in LLM evaluation) confirms that listing example failure modes biases scores downward; a schema-enforced two-field structure with neutral semantics avoids both the over-confidence bias and the over-correction bias.
- Disambiguation instruction: the prompt explicitly instructs the LLM to assume the most plausible modern digital implementation when a task's context is ambiguous, with the assumption applying uniformly across all four criteria (not only Information Sufficiency). This avoids contradictory composite scores where the LLM applies a digital interpretation for one criterion and reverts to a physical interpretation for another.
- Logging and checkpointing: every completed task is appended immediately to a progress file (crash-safe, `os.fsync`-flushed), and a timestamped audit log records every action including cumulative token usage and estimated cost. On resume, already-scored tasks are skipped and prior terminal failures are retried.
- Two-layer failure protocol. (a) *Infrastructure* errors — rate-limit (429), 5xx, network, timeout — are retried with exponential backoff (up to 8 attempts, capped at 120 s); if they persist (a sustained API outage), the task fails fast and is retried automatically on the next resume. A malformed-request (400) error is treated as immediately terminal (retrying cannot fix it) to avoid burning time and money. (b) *Content* failures — refusal, JSON parse failure, or schema-validation failure (all near-impossible under json_schema strict mode but defended against) — trigger the documented retry rounds: Round 1 = the request itself; Round 2 = identical retry; Round 3 = retry with a clarifying prefix appended to the system message; after Round 3, the task is logged as a terminal failure, excluded from the IM-weighted index, and counted in supplementary materials.
- Cost safety cap: the script tracks cumulative estimated cost from the API usage field and aborts if a configurable cap is exceeded, guarding against runaway spend. Completed work is checkpointed, so the run can be resumed after raising the cap.
- Pilot test protocol (Section 3.8) is run before the full scoring run.

**Aggregation rule — Design Y: gate on categorical inability, modulate on substitution quality.**

The four criteria are not aggregated by simple arithmetic mean. A simple mean is fully compensatory: high scores on some criteria can offset a zero on another. This produces incoherent results. If a task scores 0 on Information Sufficiency (it requires physical presence and cannot be digitally mediated), a mean of (0 + 2 + 2 + 2) / 4 = 1.5 would classify it as moderately exposed despite being literally impossible for current Foundation Models to perform. The same logic applies to all four criteria: a score of 0 reflects an impossibility condition for that dimension, and no amount of scoring on the other three should rescue the composite.

The aggregation rule, **"Design Y" (adopted 03 June 2026; see Section 5.24)**, is:

> **Gate (composite = 0)** if Information Sufficiency = 0 **OR** Capability Match = 0.
> **Otherwise:** composite = `mean(Information Sufficiency, Objective Verifiability, Contextual Independence, Capability Match) / 2`, in [0, 1].

**The principle, and why it is sound.** The four criteria are not all of the same kind. Two of them — Information Sufficiency and Capability Match — describe whether Generative AI can *attempt the task at all*: a physical task is categorically impossible for a disembodied model, and a task beyond current model capability cannot be substituted. These are genuine *impossibility* conditions, so they act as hard gates, consistent with the conjunctive (non-compensatory) decision rule of Einhorn (1971), under which failure on a necessary condition is disqualifying and cannot be compensated. The other two — Objective Verifiability and Contextual Independence — describe how *cleanly and completely* AI substitutes *given that it can attempt the task*: an unverifiable or relationship-dependent task is harder to substitute, but the model can still do part of it, so these are matters of *degree* and they *modulate* the score (compensatory averaging) rather than zeroing it.

This "gate on categorical inability, modulate on substitution quality" split is the principled answer to the objection that originally led us to reject hierarchical gating as arbitrary (Section 5.5): the choice of which criteria gate is not arbitrary — it follows from which barriers represent an absolute impossibility for the technology versus a reduction in the quality of substitution. The empirical motivation is documented in Section 5.24: the earlier "any criterion = 0 gates" rule, combined with the broken v3 criteria, collapsed the index to three values; Design Y restores a meaningful gradient (a subjective-but-capable digital task scores ~0.75, a subjective-and-relational one ~0.375, a fully-substitutable one 1.0, a physical or beyond-capability one 0).

**Why this is more defensible than raw cosine similarity:**

The rubric directly operationalises a clear theoretical definition of Generative AI exposure: the degree to which current Foundation Models can substitute for a worker on a task. It does not depend on surface vocabulary similarity. An LLM evaluating a task statement can recognise semantic equivalence across vocabulary gaps, apply reasoning about substitutability, and handle contextual judgement that embedding distances cannot.

The Eloundou et al. (2023) result — GPT-4 rubric scoring of O*NET tasks correlating with human expert ratings at κ > 0.70 — demonstrated that LLM-based rubric assessment can produce results consistent with independent human judgement.

**Why this approach is more defensible than raw cosine similarity:**

The rubric directly operationalises a clear theoretical definition of Generative AI exposure: the degree to which current Foundation Models can perform a task at human-equivalent or better proficiency. It does not depend on surface vocabulary similarity. An LLM evaluating a task statement can recognise semantic equivalence across vocabulary gaps, apply reasoning about whether a task is truly substitutable by Foundation Models, and handle the kind of contextual judgement that embedding distances cannot.

The Eloundou et al. (2023) result — GPT-4 rubric scoring of O*NET tasks correlating with human expert ratings at κ > 0.70 — demonstrated that LLM-based rubric assessment can produce results consistent with independent human judgement.

**Occupation-level aggregation.**

For each of the 923 occupations, the occupation-level exposure score is computed as the IM-weighted mean of task-level composite scores across all tasks:

> **Exposure_occ = Σ(IM_i × Score_i) / Σ(IM_i)**

Where the sum runs over all tasks for that occupation with non-suppressed IM values. The IM-weighted mean is the locked baseline; alternative weightings (e.g., dual IM × RT weighting) will be reported as supplementary if they produce materially different rankings.

**Treatment of Analyst-coded tasks (845 tasks, no IM ratings).**

Analyst-coded tasks are not random noise. They are O*NET's mechanism for capturing structural change in occupations between full incumbent survey waves — they are systematically the most technologically current portion of the corpus. Excluding them from the headline aggregate would produce an index biased toward the older, more stable parts of each occupation's task profile, which is exactly the wrong direction of bias for an index measuring Generative AI exposure.

The treatment is therefore:

- **Analyst-coded tasks are scored** with the LLM rubric like any other task (the rubric operates on task text).
- **Analyst-coded tasks are included in the IM-weighted occupation-level aggregate**, with their IM weight imputed as the **within-occupation mean IM** of the IM-rated tasks in the same occupation. This is a "neutral" assumption that treats analyst-coded tasks as of average importance to their occupation, given no other information.
- **Edge case (29 occupations, 3.1% of the corpus):** If an occupation has no IM-rated tasks at all (every task in that occupation has Task Type = None), the within-occupation mean IM cannot be computed. For these 29 occupations, every task receives the same imputed weight, which makes the IM-weighted mean mathematically identical to a simple unweighted mean. We do not pretend otherwise. These 29 occupations are flagged in the master file with a `weighting_mode = "unweighted"` indicator and reported in supplementary materials as having no within-occupation IM differentiation available. This is honest disclosure rather than a methodological choice — the data simply does not support occupation-internal weighting for these specific cases. They are retained in the headline index because excluding them would mean dropping 29 of 923 occupations entirely, which is a worse loss than the loss of weighting precision.
- **Robustness check:** The index is also computed without analyst-coded tasks (the unimputed version) and the two rankings are compared. Material divergence between the two is reported transparently in the paper.

The choice to impute is itself a methodological decision documented in Section 5.13. The reasoning: throwing out the most technologically current portion of the corpus introduces a systematic downward bias that is worse than the unverifiable assumption of within-occupation mean importance. The robustness check addresses the imputation assumption directly by reporting both versions.

**Normalisation.** Composite task scores are already in [0, 1], and the IM-weighted mean of values in [0, 1] is also in [0, 1]. Min-max normalisation across occupations is not applied unless empirical inspection of the distribution makes a strong case for it.

### 3.3 Substitutability Scope: What This Index Measures

This is the most important framing in the entire project. The index measures **direct Generative AI substitutability** — whether current Foundation Models could perform a task at human-equivalent or better proficiency. The construct is bounded in three distinct ways:

**Bound 1: Generative AI, not all AI.**
The index measures exposure to Foundation Models specifically — large language models, vision-language models, and multimodal generative systems. It does *not* measure exposure to:
- Robotics or robotic systems
- Autonomous vehicles or other embodied AI
- Computer vision systems performing physical inspection or sensor-driven tasks
- Industrial automation, supervised learning systems for predictive ML, or pre-Foundation-Model AI more broadly

These are also "AI," they are deployed in the workplace today, and excluding them is a deliberate scope choice. The Information Sufficiency criterion is the operational mechanism for this exclusion: tasks requiring physical presence, real-time sensor data, or embodied interaction are zero-gated. This is consistent because Foundation Models, by their architecture, operate on text, images, structured data, and code — they cannot replace embodied work without robotic actuators that are themselves a different category of AI system.

This bound has an important implication for validation (Section 3.4): our index should *not* correlate strongly with measures of historical AI / supervised ML / patent-based AI exposure (e.g., Webb 2020), because those measures captured a different technology wave. Strong correlation with such measures would actually be a warning sign that our index is failing to capture what is distinctive about Generative AI.

**Bound 2: Substitution, not augmentation.**
The index measures whether Foundation Models can perform a task instead of a human worker, not whether they can help a human worker perform the task more efficiently. Two contrasts in the literature:
- **Eloundou et al. (2023)** measure **speedup** — whether an LLM can reduce task completion time by ≥50%. Their three-tier rubric (E0/E1/E2) does not distinguish between substitution and augmentation. A task where AI doubles a human's productivity (and the human remains required) is classified the same as a task where AI replaces the human entirely. Their measure is broader than ours.
- **Anthropic (2025)** measure **observed exposure** — theoretical capability filtered through actual Claude usage data, with augmentative use (β = 0.5) weighted at half the value of automation use (β = 1). Their measure attempts to capture both substitution and augmentation but downweights the latter.
- **Our index** measures direct substitution only. A task scoring high means current Foundation Models can perform that specific task at human-equivalent proficiency. We make no claim about how much Foundation Models augment human work in lower-scoring tasks.

This is a deliberate scope choice, grounded in the goal of producing an interpretable input to the vulnerability framework that is the second half of this research programme.

**Bound 3: Technical capability, not labour market displacement.**
A task scoring high on the rubric means a Foundation Model can technically do it. It does not mean workers in occupations with high task scores will actually lose their jobs. In the real labour market, a wide range of non-technical factors moderate how technical capability overlap translates into actual displacement: regulatory frameworks (medical diagnosis, legal advice, and financial guidance operate under licensing and liability structures that restrict deployment regardless of capability), professional norms and client trust, the cost of error in high-stakes contexts, and institutional inertia more broadly.

**This project does not attempt to measure or correct for institutional friction.** Doing so at task level would require occupation-specific regulatory data, liability frameworks, and contextual judgements that vary across countries, industries, and time. It is not feasible at this scope and is not part of the research design.

The place in this research design where real-world moderation is partially addressed is the vulnerability framework: **Generative AI Vulnerability = Exposure × (1 − Adaptation Capacity)** (Part 2 of the project). This moderation operates at the individual level (worker characteristics that buffer against exposure). Institutional friction is a separate occupation-level or sector-level moderating layer, distinct from individual adaptation capacity, and remains out of scope.

### 3.4 Validation Strategy

The validation strategy is a six-tier framework structured around four distinct types of check: **within-project reliability** (the rubric is reproducible across evaluators), **within-project validity** (the rubric agrees with human judgement on the same tasks), **convergent validity** (we should agree with measures of the same construct — Generative AI exposure), and **discriminant validity** (we should *disagree* with measures of different constructs — historical AI / supervised ML exposure). Documenting all four is a stronger claim than any single check, because it triangulates across methodologically independent comparisons.

This is a revision from an earlier seven-tier draft. An original Tier 7 — an occupation-level expert spot-check on 25–30 occupations — was dropped on 11 May 2026 following supervisor feedback. The reasoning is documented in Section 5.18: a 25-occupation expert review is time-consuming for what was only ever a supplementary face-validity check, and the rigorous human comparison is already covered by Tier 2 (task-level human-LLM validity sample). Dropping the supplementary tier does not weaken the validation hierarchy.

| Tier | Comparator | Type | Expected result |
|------|------------|------|-----------------|
| 1 | Multi-LLM reliability (GPT-4o vs. Claude 3.5 Sonnet) | Within-project reliability | Cohen's κ ≥ 0.70 supports reliable scoring |
| 2 | Human-LLM agreement on 100 task-level ratings (simple random sample) | **Within-project validity** | Cohen's κ ≥ 0.60 between LLM and average human rating |
| 3 | Eloundou et al. (2023) | **Convergent validity** (same construct: Foundation Model exposure) | Spearman ρ ≥ 0.55 |
| 4 | Anthropic (2025) observed exposure (if available at occupation level) | Convergent validity | Substantial positive ρ |
| 5 | Brynjolfsson, Mitchell, Rock (2019) SML index | Mixed: convergent on cognitive ML, partial discriminant | Moderate positive ρ |
| 6 | Webb (2020) | **Discriminant validity** (different construct: historical AI / supervised ML exposure) | (ρ_Eloundou − ρ_Webb) ≥ 0.15 |

**Tier 1 — Multi-LLM inter-rater reliability (within-project reliability check).**

A stratified random sample of approximately 1,800 tasks (≈10% of the corpus) is scored independently by Claude 3.5 Sonnet using the identical rubric and prompt. Inter-rater reliability between GPT-4o and Claude 3.5 Sonnet is computed using Cohen's κ at the criterion level, Krippendorff's α at the criterion level for cross-validation, and Spearman ρ on composite task and occupation scores. This addresses the model-evaluator dependence problem documented in NBER Working Paper 35110 (2025), which showed that LLM-based exposure indices can vary by up to 3.6× across different evaluator models.

The stratification is by Domain Source (Incumbent / Occupational Expert / Analyst) to ensure representation across the corpus.

**Tier 2 — Within-project human-LLM validity check.**

Inter-LLM reliability addresses *reproducibility* but does not address *validity* — two LLMs can agree while both being systematically wrong. The strongest within-project validity check is direct comparison with human ratings.

**Sampling protocol — simple random (updated 06 June 2026; supersedes the earlier stratified protocol).** A simple random sample of 100 tasks is drawn, with a fixed seed for reproducibility, from the scored corpus. Because the production run is executed over a randomly-ordered file (`master_tasks_shuffled.csv`, Implementation Log 9.8), any prefix of completed tasks is already a representative random sample, so the validity sample can be drawn before the full run finishes. On the supervisors' recommendation the sample is **simple random rather than stratified**: this yields a κ that estimates human–model agreement on a *typical* task at the corpus's actual score distribution (a population-representative validity statement), and it removes analyst choices about strata boundaries and per-stratum counts, so the sample construction itself cannot be argued to shape the result. The trade-off — thinner coverage of sparse score regions, and the influence of the prevalent zero-gated category on Cohen's κ (the prevalence/kappa effect) — is handled at the reporting stage (see "Metrics reported" below and Section 5.27), not by re-stratifying. The original stratified rationale is retained as the record in Section 5.19.

**Rating procedure.** The 100 tasks are independently rated by the researcher and both supervising professors using the same four-criterion rubric. Each rater scores the 100 tasks **blind to the LLM scores**. Before the rating session, all three raters work from a shared rater guide (`docs/rater_guide.md`) that defines the criteria in plain language and includes worked examples; this de-risks the validity check by ensuring all raters interpret the criteria consistently.

**Metrics reported.** (a) Cohen's κ between the LLM scores and the averaged human ratings, per criterion and on the composite (the headline validity statistic); (b) Krippendorff's α across the three human raters (the inter-rater consistency metric, which bounds how high (a) could possibly be); and — because the sample is simple random and the zero-gated category is prevalent — (c) raw percent agreement and the confusion matrix, alongside the sample's composite-score distribution, so κ is read in the context of category prevalence rather than in isolation (the prevalence/kappa effect; Section 5.27). The 100-task sample is tractable (~4–6 hours of human work per rater) and large enough to give a usable confidence interval on κ.

**Anchor reference.** Eloundou et al. (2023) used a similar human-rater validation for their rubric and reported κ > 0.70 against expert raters. The threshold here is κ ≥ 0.60 (Section 6.3); the lower threshold reflects that our rubric is more granular than Eloundou's three-tier scheme (more granularity creates more opportunities for rater disagreement on borderline cases).

**Tier 3 — Convergent validity check against Eloundou et al. (2023).**

Eloundou's index is the most methodologically similar published comparator: same data foundation (O*NET task text), same general approach (LLM-rubric scoring), same broad construct (Foundation Model exposure). Where the two measures diverge, the divergence is interpretable as the impact of (a) our non-compensatory aggregation versus their compensatory categorical scheme, (b) our substitution-only scope versus their broader speedup measure, and (c) our newer O*NET version versus their O*NET 27.2.

This is positioned as convergent validity, not external validation. The two indices share methodological infrastructure (both use O*NET task text and LLM rubric scoring), so high correlation is expected and is evidence of consistency rather than independent verification.

**Tier 4 — Convergent validity check against Anthropic (2025).**

Anthropic's "observed exposure" measure combines Eloundou-style theoretical scoring with actual Claude usage data. If the occupation-level data is publicly accessible at the granularity of the published research, we report Spearman correlation. This tier may be unavailable or partial depending on data release.

**Tier 5 — Brynjolfsson, Mitchell, and Rock (2019) SML Index.**

Their Suitability for Machine Learning index is based on machine learning expert survey judgements applied to O*NET work activities. It targets supervised machine learning capability, which is closer to our construct than Webb's patent-based historical measure but still pre-Foundation-Model. We expect moderate positive correlation: SML captures cognitive task structures that Foundation Models also tend to be exposed to, but does not specifically capture the language-and-content generation capabilities that distinguish Foundation Models. Reported as a mixed convergent / partially discriminant check.

**Tier 6 — Discriminant validity check against Webb (2020).**

Webb's exposure measure uses patent text from approximately 2010–2019, capturing the supervised learning, computer vision, and predictive ML wave that preceded Foundation Models. The labour economics literature has extensively documented that Generative AI affects a fundamentally different demographic and task profile than the prior wave: GenAI hits non-routine cognitive and language-heavy work performed by higher-educated workers, while earlier ML hit routine cognitive and perceptual middle-wage work.

If our index is correctly capturing Generative AI exposure specifically, the correlation with Webb should be **materially lower** than the correlation with Eloundou. This is the discriminant validity hypothesis: ρ(our index, Webb) < ρ(our index, Eloundou). A high correlation with Webb would actually be a warning sign — it would suggest our index is failing to capture what is distinctive about Generative AI and is instead measuring older AI exposure patterns.

The empirical comparison of Tier 3 ρ with Tier 6 ρ is itself a methodological contribution. No published Generative AI exposure paper has explicitly tested this discriminant hypothesis.

**Pre-locked decision criteria.**

To prevent post-hoc interpretation of validation results, the following thresholds are committed in advance and will not be modified after seeing the results:

- Tier 1 (multi-LLM reliability): Cohen's κ ≥ 0.70 supports reliable scoring; κ between 0.50 and 0.70 is reported as moderate; κ < 0.50 triggers methodological investigation and is reported honestly as a reliability concern.
- Tier 2 (human-LLM validity): Cohen's κ ≥ 0.60 between LLM and averaged human ratings supports validity; κ between 0.40 and 0.60 is reported as moderate; κ < 0.40 triggers investigation.
- Tier 3 (Eloundou convergent): Spearman ρ ≥ 0.55 supports convergent validity. ρ between 0.40 and 0.55 is reported as moderate / partial. ρ < 0.40 is reported as a failure of convergent validity and triggers methodological investigation of the divergence.
- Tier 6 (Webb discriminant): (ρ_Eloundou − ρ_Webb) ≥ 0.15 supports discriminant validity. A smaller gap is reported as ambiguous discriminant evidence.

Locking these criteria in advance is itself a methodological contribution — the existing literature does not commit to validation thresholds before running the comparison, which permits post-hoc interpretation.

### 3.5 BERT-Based Reproducibility and Interpretability Analysis

Once the LLM rubric scoring is complete, a BERT-based reproducibility analysis is performed to characterise what the LLM-as-judge is doing. This is a methodological characterisation layer on top of the rubric, not an alternative scoring method. Its purpose is to answer a question that the LLM-as-judge literature has not rigorously addressed: how much of the LLM scoring is "deep" reasoning, and how much is captured by surface text features that simpler embedding-based methods could replicate?

**Pipeline:**

1. **Compute sentence-BERT embeddings** for all 18,796 O*NET task statements using `all-mpnet-base-v2` (a current sentence-transformer producing 768-dimensional embeddings) or a comparable recent variant. This is done once, after preprocessing, before any aggregation.

2. **Train a regression model** that predicts the LLM composite task-level score from the BERT embedding alone. Standard ML setup: 80/20 train/test split with stratification on score quartiles, k-fold cross-validation (k=5) for hyperparameter tuning, gradient-boosted regression or feed-forward neural network depending on what generalises best on the held-out set. Report R², RMSE, and predicted-vs-actual scatter.

3. **Interpret the result based on R²:**

   - **High R² (≥ 0.7):** The LLM's scoring is largely a function of surface text features that BERT can capture without expensive LLM calls. This is interesting because it means the index is reproducible from a much cheaper pipeline, with implications for scalability and reproducibility of similar work in low-resource settings.
   - **Moderate R² (0.4–0.7):** The LLM is balancing semantic features with deeper reasoning. The LLM-as-judge approach is doing meaningful work that simpler embedding methods cannot fully replicate, but a substantial portion of the variance is explained by surface features.
   - **Low R² (< 0.3):** The LLM's scoring relies heavily on context-sensitive reasoning that BERT features cannot capture, validating the use of frontier models over simpler approaches.

   Each of these outcomes is informative. The result is reported regardless of which way it falls.

4. **Residual analysis.** Identify the tasks where the LLM score diverges most from what BERT predicts (largest absolute residuals). These are the tasks where LLM judgement is doing the most work — useful to inspect for understanding what kinds of contextual reasoning the rubric actually captures. The top 50 positive and top 50 negative residual tasks are reported in supplementary materials with manual interpretation.

**Sensitivity to BERT model choice.**

R² may differ depending on which sentence-BERT variant is used. To verify robustness of the conclusion, the analysis is run with at least two embedding models: `all-mpnet-base-v2` (768 dimensions, balanced quality and speed) and `all-MiniLM-L12-v2` (384 dimensions, smaller and faster). Both R² values are reported. Convergent results across models support the conclusion; substantial divergence is itself a finding worth investigating and reporting. Running both costs essentially nothing because both are local models with no API spend.

**Why this is a valuable addition:**

- It directly tests a question the LLM-as-judge literature has not answered: how much of frontier-model scoring is necessary expense and how much is surface-feature replicable. Either result is publishable.
- It produces a quantitative characterisation of the LLM rubric (R² is itself a reported finding) that strengthens the methodological framing of the paper.
- It uses BERT embeddings, which engages the data science / NLP techniques that align with Prof. Dash's expertise without changing the headline methodology.
- Computationally cheap: embeddings for 18,796 short texts on a modern GPU take minutes; the regression is even cheaper. No new API spend.
- It has practical implications for the literature: if the answer is "LLM scoring is highly BERT-replicable," this is a result that affects how others should design similar studies in the future.

**Why this is bounded:**

- It is a single analytical product, not a parallel methodology. The headline exposure scores remain the LLM rubric output.
- It does not require new data acquisition.
- The interpretation depends on the result and is reported transparently regardless of which direction it goes.

This analysis also provides an additional structural validity check on the rubric: if BERT can predict the LLM scores reasonably well, it suggests the LLM is using semantically coherent features rather than noise. If it cannot predict at all, this raises questions about what the LLM is actually doing.

### 3.6 Analytical Outputs

The methodology produces three distinct analytical outputs at the occupation level. The first is the headline exposure score; the second and third are derivative analyses that emerge naturally from the rubric structure and add interpretive depth.

**Output A — Occupation-level Generative AI exposure score.**

The IM-weighted mean of task-level composite scores per occupation, computed as defined in Section 3.2 (with within-occupation mean IM imputed for analyst-coded tasks). 923 occupations × 1 score.

**Output B — Within-occupation exposure dispersion.**

For each occupation, alongside the IM-weighted mean we report the IM-weighted standard deviation of task-level composite scores. Two occupations with the same mean exposure score may have very different internal task structures: one may have all tasks scoring near the mean (low dispersion), the other may have highly exposed tasks alongside fully protected tasks (high dispersion). This distinction is not captured by mean exposure alone but is visible in the within-occupation distribution.

The dispersion measure is computationally trivial — standard weighted statistics on an existing score column — and adds no implementation cost. Its analytical value comes in two forms. First, it provides a richer characterisation of an occupation's exposure profile than a single number. Second, it interfaces directly with Part 2 of the research programme: a high-dispersion occupation gives an adaptive worker the option to specialise into protected tasks; a low-dispersion occupation does not.

For occupations with very few tasks (4 to 6 tasks; the corpus minimum is 4), dispersion estimates are noisy and are flagged as such in supplementary tables.

**Output C — Barrier decomposition (gates and modulators).**

Under Design Y (Section 3.2) the four criteria split into two gates and two modulators, and the decomposition reports both — which is richer than a single-gate story.

*What gated the task (categorical barriers).* A task is zeroed by **Information Sufficiency** (it requires physical embodiment) or **Capability Match** (current Foundation Models cannot perform it at average-human quality). For each occupation we report the IM-weighted proportion of tasks gated by each — distinguishing, for example, a manual occupation protected by physical embodiment from a frontier-research occupation protected by capability limits.

*What modulated the score down (quality barriers).* Among non-gated tasks, we report how much **Objective Verifiability** (subjective vs. checkable success) and **Contextual Independence** (relational / tacit-knowledge dependence) pulled the composite below its maximum. This distinguishes, for example, a data-analysis occupation (high verifiability, context-independent → high exposure) from a client-advisory occupation (capable and digital, but relationship-dependent → moderated exposure).

This two-part decomposition is a free byproduct of the rubric and produces analytical output no published exposure index reports. Eloundou's E0/E1/E2 categories cannot decompose this way because the underlying reasoning is collapsed into a single label; Felten's AIOE does not decompose by barrier type at all.

The interpretive value is policy-relevant and now finer-grained: an Information-Sufficiency-gated occupation faces no near-term GenAI substitution (physical work); a Capability-Match-gated occupation warrants continuous reassessment as models advance; a Contextual-Independence-modulated occupation is exposed in its informational tasks but protected in its relational ones (suggesting task-restructuring rather than wholesale displacement); an Objective-Verifiability-modulated occupation is exposed but with a human-verification overhead.

**Output D — Criterion dimensionality analysis.**

The barrier decomposition (Output C) is only as informative as the criteria are separable. This analysis is no longer hypothetical: the **first pilot (03 June 2026) demonstrated that the original v3 criteria were not separable** — Information Sufficiency, Output Verifiability, and Decomposability correlated at 0.95–0.99 because all three were measuring "physical vs. digital" (Section 5.23). That failure drove the v3.1 redesign, in which each criterion was rebuilt to capture a distinct barrier. The dimensionality analysis below is therefore both a diagnostic *and* the formal test of whether the redesign achieved the separation it was built for; the re-pilot provides the first read, the full corpus the definitive one.

After scoring, four diagnostics test whether the four redesigned criteria (Information Sufficiency, Objective Verifiability, Contextual Independence, Capability Match) are empirically separable:

1. **Criterion correlation matrix.** Spearman correlations between the four criterion scores across all scored tasks, and separately between gate/modulation patterns. The pre-redesign benchmark to beat: the v3 criteria correlated at 0.95–0.99; the redesign targets substantially lower inter-criterion correlation.
2. **Principal component / factor analysis.** PCA on the four criterion scores to test how many latent dimensions underlie them. The redesign predicts four distinguishable dimensions (physical, verifiable, relational, capability); if fewer emerge, that residual overlap is reported honestly as a finding about the structure of AI substitutability.
3. **Gate-attribution stability.** For zero-gated tasks, how often a single criterion uniquely gates the task versus multiple criteria co-gating. If most zero-gated tasks fail several criteria simultaneously, the binding-constraint decomposition is reported with appropriate caution.
4. **Per-criterion inter-rater disagreement.** Using the multi-LLM reliability sample (Section 3.4 Tier 1) and the human validity sample (Tier 2), which criteria are scored most consistently and which are noisiest. This identifies whether any criterion is unusually subjective.

**This analysis is diagnostic and reported, not a model-selection trigger.** The four-criterion structure is held fixed regardless of what the dimensionality analysis shows. The decision to hold Decomposability as a fixed fourth criterion — rather than pre-committing to collapse the model to three criteria if the correlation is high — is documented in Section 5.20. The rationale: a data-dependent decision to drop a criterion would itself invite questioning, and the four-way binding-constraint decomposition has interpretive value worth preserving; if overlap appears, it is reported transparently as a finding rather than used to restructure the index. Framing the whole analysis as *"which dimensions of AI substitutability are empirically separable?"* converts the overlap concern from a vulnerability into a contribution. This subsumes and extends the criterion-correlation limitation noted in Section 6.6.

### 3.7 Master File Schema

The preprocessing step produces a single master file. The schema is:

| Column | Source | Description |
|---|---|---|
| `onet_soc_code` | Occupation Data | 10-character occupation identifier |
| `occupation_title` | Occupation Data | Official title |
| `occupation_description` | Occupation Data | Plain-language description |
| `task_id` | Task Statements | Unique task identifier |
| `task_text` | Task Statements | The task description (rubric input) |
| `task_type` | Task Statements (normalised) | `Core` / `Supplemental` / `Unrated` (the latter replaces the empty cell used by O\*NET for analyst-coded tasks; see Section 1.2) |
| `domain_source` | Task Statements | Incumbent / Occupational Expert / Analyst / Analyst-Transition |
| `im_weight` | Task Ratings (IM) | Importance rating, 1–5; null for analyst-coded tasks (imputed at aggregation time) |
| `im_weight_imputed` | Derived | Y/N flag — Y if the IM weight was imputed (within-occupation mean) for an analyst-coded task |
| `im_suppress` | Task Ratings (IM) | Y/N flag for `Recommend Suppress`; rows with Y excluded from weighting |
| `rt_value` | Task Ratings (RT) | Relevance percentage 0–100; for supplementary analysis |
| `rt_suppress` | Task Ratings (RT) | Y/N flag for `Recommend Suppress` |
| `task_date` | Task Statements | Year/month task data was last updated |
| `survey_n` | Occupation Level Metadata | Total Completed Questionnaires for the occupation |
| `survey_date` | Occupation Level Metadata | When the occupation was last surveyed |

After scoring, the following columns are added:

| Column | Description |
|---|---|
| `score_decomposability` | LLM rubric criterion 1 score (0/1/2) |
| `score_information_sufficiency` | LLM rubric criterion 2 score (0/1/2) |
| `score_output_verifiability` | LLM rubric criterion 3 score (0/1/2) |
| `score_capability_match` | LLM rubric criterion 4 score (0/1/2) |
| `composite_score` | Aggregated task-level composite per Section 3.2 |
| `gated_by` | Which criterion(s) zero-gated the task; null if not gated |
| `flagged_artefact` | Y/N — flagged during post-scoring audit as interpretation artefact (excluded from index if Y) |
| `claude_score_*` | Same four criterion scores from Claude 3.5 Sonnet, populated for the ~10% reliability sample |
| `bert_embedding` | 768-dimensional sentence-BERT embedding of the task text (stored separately due to size) |
| `bert_predicted_score` | LLM composite predicted from BERT embedding via the regression in Section 3.5 |
| `bert_residual` | Difference between actual LLM composite and BERT-predicted score |

An additional column is added at the occupation level:

| Column | Description |
|---|---|
| `weighting_mode` | "IM-weighted" for occupations with at least one IM-rated task; "unweighted" for the 29 occupations with all-analyst tasks (no within-occupation IM differentiation possible) |

A separate occupation-level summary file is built from the master file, with one row per occupation containing: exposure score (IM-weighted mean, or unweighted mean for the 29 flagged occupations), within-occupation dispersion (weighted SD, or unweighted SD), binding constraint distribution (proportion of IM-weight gated by each criterion), data quality flags (survey N, survey date, number of tasks, number of zero-gated tasks, number of artefact-flagged tasks, number of scoring-failure tasks, count of analyst-imputed tasks, and the `weighting_mode` flag).

### 3.8 Pilot Test Protocol

Before the full scoring run, a pilot test of approximately 75 curated tasks is conducted to verify that the rubric prompt produces reliable and interpretable scores. The pilot is curated, not random, because its purpose is to stress-test the rubric on known-difficult cases.

**Pilot composition (target ~75 tasks):**

- **20 tasks expected to score uniformly high:** software development, data analysis, document drafting, financial modelling, language translation, information retrieval. These tasks should score 2 on all four criteria. If they do not, the prompt is failing.
- **20 tasks expected to score uniformly low (zero-gated):** physical care delivery, manual construction, emergency response, hands-on equipment repair, in-person counselling, surgery. These tasks should score 0 on Information Sufficiency. If they do not, the prompt is failing.
- **20 tasks with deliberate physical/digital ambiguity:** "monitor patient vitals," "review documents," "inspect facilities," "examine specimens." These tasks should be evaluated under the most plausible digital implementation per the disambiguation instruction. These are the load-bearing test cases.
- **15 tasks of mixed type:** Core and Supplemental, Incumbent-rated and Analyst-coded, drawn from a range of occupations and survey dates.

**Success criteria:**

1. The 20 uniformly-high tasks score 2 on all four criteria (or 1 on at most one criterion). If this fails, the prompt under-recognises clear Foundation Model capabilities.
2. The 20 uniformly-low tasks score 0 on Information Sufficiency. If this fails, the prompt over-recognises digital implementation possibilities and risks false-positive exposure assignments.
3. The 20 ambiguous tasks score consistently with the disambiguation instruction. Manual review verifies that the LLM is choosing the digital interpretation when one is plausible.
4. The mixed sample produces no obvious systematic patterns indicating misinterpretation.
5. Output JSON is parseable for 100% of tasks. Any parse failures trigger prompt revision.

> **Superseding note (v3.1 redesign, 03 June 2026; v3.2, 04 June 2026).** Success criterion 1 above was written for the v3.0 criteria, under which capable digital tasks were expected to score 2 on all four. The v3.1 redesign deliberately recalibrated Capability Match so that "capable but normally reviewed" work scores 1, not 2 (Section 5.23), and adopted Design Y aggregation. Under that design the uniformly-high bucket lands in a populated **0.75–1.0 band (pilot mean 0.825)**, not a uniform 1.0 — so "score 2 on all four" is no longer the target and would in fact indicate the old collapse. The operative, pre-committed pass criteria from the redesign onward are those in Decision History 5.23–5.26 and this protocol (Section 3.8): a multi-valued composite gradient, all four criteria exercising their range, correct bucket ordering, and the relational/physical floors holding. Criteria 2–5 above are unchanged. The three-pilot revision trail (v3 → v3.1 → v3.2) is itself the logged audit record this protocol requires.

**Trigger for prompt revision:** Failure on any of criteria 1, 2, or 3. Revisions are made until the pilot passes; each revision is logged with the date and the change made. The full final prompt is published verbatim in supplementary materials before scoring begins.

**Defense against pilot-overfitting concerns.**

A reviewer might argue that the pilot tasks are tasks where we already knew the desired answer, so iterating on the prompt risks overfitting to our priors. The defense is threefold: (a) the pilot is designed to catch prompt failures on known-difficult cases (physical-vs-digital ambiguity, embodied tasks, clearly substitutable tasks), not to tune the rubric toward specific numerical scores; (b) once the prompt is locked, it is applied to 18,796 unseen tasks, and the post-scoring audit (Section 3.10) identifies any new failure modes that the pilot did not anticipate; (c) every prompt revision during the pilot is logged with the date and the change made, providing a transparent audit trail. The pilot's purpose is catching systematic failure modes in the rubric, not numerical tuning.

### 3.9 Limitations of the LLM-as-Judge Approach

Five limitations specific to the LLM-as-judge methodology are acknowledged. These are presented separately from the broader methodological limitations of the research design (Section 6), which apply to any task-based exposure index.

**Stochastic variance.** LLM outputs are non-deterministic and may vary across runs even at fixed temperature settings. Fixing the model version and T = 0 addresses most of this. This is a variance problem that can in principle be reduced with consistent experimental conditions.

**LLM self-assessment bias.** Stochastic variance and systematic directional bias are fundamentally different problems and require different fixes. Repeated sampling addresses variance but cannot correct a consistent directional error. RLHF-trained models such as GPT-4o are known to exhibit overconfidence when evaluating AI capabilities: training on human preference feedback rewards confident, capable-sounding responses, creating a systematic tendency to overestimate what AI systems can do. When the same class of model being evaluated is also the evaluator, this is a conflict of interest baked into the measurement process.

The four criteria are not equally susceptible. Criteria 1 through 3 — Information Sufficiency, Objective Verifiability, and Contextual Independence — are structural questions about the task's properties, not claims about the LLM's own capabilities. Criterion 4 — current Foundation Model capability match — is a direct self-assessment and is the criterion most vulnerable to systematic overconfidence. (The two reasoning fields and the average-human-worker calibration on Criterion 4, Section 3.2, are the prompt-level mitigations for exactly this.)

The empirical check for self-assessment bias is external validation against independent human judgement, which the multi-LLM reliability check (Section 3.4 Tier 1) and the within-project human-LLM validity check (Tier 2) provide. Substantial agreement between GPT-4o and Claude 3.5 Sonnet is evidence that any self-assessment bias is bounded across two models with different training pipelines. This does not eliminate the concern, since both models share fundamental architecture and RLHF training paradigms; agreement between them is therefore a lower bound on independence rather than a guarantee of validity.

Self-assessment bias is also mitigated at the **prompt level** in v2 of the rubric. Criterion 4 has two reasoning fields rather than one (`capability_match_what_works` and `capability_match_what_might_fail`), both schema-required, both neutrally named so that neither pre-loads any specific content. The model must articulate, in its own words and specific to the task being evaluated, what about the task is tractable for current Foundation Models *and* what about it might cause underperformance, before it commits to a score. This is a documented behavioural intervention against the RLHF-induced "answer confidently" bias. Importantly, the prompt does *not* list specific failure modes (hallucination, edge cases, lack of training data, etc.) because doing so would create the inverse problem — anchoring the model toward those specific failures and biasing scores downward. The schema-enforced two-field structure with neutral semantics forces balanced consideration without supplying biasing content. The literature on cognitive biases in LLMs (Suri et al. 2024 on anchoring; Echterhoff et al., Itzhak et al. on broader cognitive bias replication in LLMs) supports this design choice.

**Fragility of non-compensatory aggregation.** The non-compensatory gate in Design Y (Section 3.2) — gate on Information Sufficiency = 0 or Capability Match = 0, modulate otherwise — is methodologically superior to a simple mean. It does, however, introduce a vulnerability that a fully compensatory model does not have: it amplifies the consequence of a single interpretation error on a *gating* criterion. Because a zero on Information Sufficiency or Capability Match is terminal, the index is sensitive to how the LLM resolves physical/digital ambiguity in particular (Section 6.5). The two non-gating criteria (Objective Verifiability, Contextual Independence) only modulate, so an error there moves the composite by at most one band rather than zeroing it.

The source of this ambiguity is a property of the data: O*NET task statements often do not specify implementation context. *"Monitor patient vitals"* is plausibly physical or digital; *"Review financial documents"* can mean paper or electronic. The non-compensatory design amplifies the consequence of the LLM's contextual interpretation.

This fragility is mitigated by (1) the disambiguation instruction in the scoring prompt, which directs the LLM to assume the most plausible modern digital implementation when context is ambiguous; (2) the post-scoring audit (Section 3.10) which identifies and excludes interpretation artefacts; and (3) the pilot test (Section 3.8) which is specifically designed to detect prompt failures on ambiguous tasks before full scoring begins.

**Cost and API dependency.** Scoring 18,796 task statements via LLM API is more expensive and slower than embedding-based methods. Estimated cost: ~£73 for the full corpus through the GPT-4o *synchronous* Chat Completions API — the funded account is Usage Tier 1, whose Batch enqueued-token limit makes the Batch API (and its 50% discount) unusable, so synchronous scoring is used (Section 5.22) — plus ~£5–15 for the 10% Claude reliability sample. The pilots logged ~$0.005/task; the full-run figure derives from that measured rate, not an a priori estimate. The run takes ~28–31 hours of wall-clock time at Tier-1 pacing and is fully resumable. Documented and reported.

**Rubric validity.** The four criteria encode a particular view of what makes a task substitutable by Foundation Models. Reasonable experts may disagree with the criteria or their relative weights. Each criterion is grounded in published Foundation Model capability taxonomy (Eloundou et al., 2023). The empirical reliability of the rubric is examined in the multi-LLM reliability check; the validity of the criteria themselves is asserted on theoretical grounds and is open to challenge.

### 3.10 Post-Scoring Audit Protocol

After the full scoring run is complete, all tasks that received a 0 on any criterion are extracted and reviewed as a set. The purpose of this audit is **not** to re-score tasks. It is to identify and document interpretation artefacts.

For each zero-gated task, the audit categorises it as either:

- **Genuine impossibility condition**: the task genuinely fails the gating criterion. Retained in the index with composite score = 0.
- **Interpretation artefact**: the O*NET task description is ambiguous about implementation context, and the LLM applied a physical or pre-digital interpretation that the disambiguation instruction should have prevented but did not. Excluded from the IM-weighted index. The exclusion and the count are reported in supplementary materials.

This protocol replaces an earlier draft of the methodology that proposed re-scoring artefact-flagged tasks. Re-scoring after seeing scores is methodologically problematic and can be construed as p-hacking; exclusion-and-documentation is transparent and defensible. The expected proportion of artefact-flagged tasks should be small (single-digit percentage of zero-gated tasks) if the pilot test is successful.

**Physicality double-count check (non-gated IS = 1 tasks).** A second, separate audit pass targets the hybrid middle that the pilot could not exercise (the pilot scored Information Sufficiency as binary, 38×0 / 37×2, with zero 1s — Section 6.5). Every task scored Information Sufficiency = 1 is extracted (these are *not* gated and so enter the index), and each is flagged where its Contextual Independence or Objective Verifiability reasoning invokes physical-presence language ("physical," "manual," "hands-on," "on-site," "in person") — the signature of the documented instruction leakage in which the physical penalty is counted in a criterion the prompt told the model to judge as if the task were digitally accessible. For the flagged set, the report (a) counts how many exist and what share of all PASS tasks they are, and (b) recomputes their composites with the leaked criterion reassigned to its digitally-accessible value, reporting the resulting sensitivity. Because the prompt is locked (Section 5.26), no task is re-scored via the API; this is a transparent post-hoc sensitivity, not a correction. If the flagged set is negligible, the leakage is confirmed inconsequential at scale; if it is material, the sensitivity quantifies the (conservative, exposure-understating) bias for the limitations section.

### 3.11 Justification for Proceeding with This Design

Despite the limitations in Section 3.9, the LLM-as-judge approach with non-compensatory aggregation, multi-LLM reliability validation, and BERT-based reproducibility analysis is the most defensible methodology available given the constraints of this project: (1) primary survey data collection is not feasible at this scale and timeline; (2) raw semantic similarity is demonstrably insufficient as a standalone scoring method due to the vocabulary gap problem; (3) the LLM-as-judge approach has been validated in a peer-reviewed paper (Eloundou et al., 2023) and independently replicated (Anthropic, 2025); (4) the multi-LLM reliability check, the binding constraint decomposition, the within-occupation dispersion analysis, and the BERT-based reproducibility analysis collectively produce analytical output and methodological rigour beyond what the existing literature provides.

The limitations are real and acknowledged. An imperfect method that is grounded in the literature, transparently documented, and bounded by reliability metrics is more defensible than a methodologically simpler alternative with a weaker theoretical basis.

---

## 4. Decisions Log

This section records every decision made about the data and the methodology, in chronological order with reasoning.

| Date | Decision | Reason |
|------|----------|--------|
| 07 May 2026 | Downloaded O\*NET 30.2 (full Excel archive) rather than individual files | Single authoritative download; all files version-consistent. |
| 07 May 2026 | Selected 12 files for active use; left Abilities, Skills, Knowledge, Work Styles, Work Values, Interests in archive | These are not needed for the LLM-as-judge exposure index. O\*NET cannot be used for the Adaptation Capacity Index in Part 2 (double-counting problem documented in Section 5). Files are retained locally in case a supplementary analysis requires them. |
| 07 May 2026 | Task statements are the primary text for exposure scoring; DWAs are not used as primary or fallback scoring text | Task statements are occupation-specific and carry the fine-grained within-occupation signal needed for meaningful exposure differentiation. |
| 07 May 2026 | Will use IM (Importance) scale from Task Ratings as the primary task weighting variable | IM is a direct mean on a 1–5 scale reflecting how central a task is to the job. Cleanest single weighting variable. |
| 07 May 2026 | Emerging tasks excluded from primary exposure index | Emerging tasks have not stabilised in the O*NET corpus. Distinct from analyst-coded tasks (which have stabilised but lack incumbent ratings). |
| 07 May 2026 | Rows with `Recommend Suppress = Y` in Task Ratings excluded | O\*NET explicitly flags these for low data precision. Following the data provider's guidance. |
| 08 May 2026 | Occupation inclusion follows field standard — no sample size or date cutoffs applied | Literature review of all major published AI exposure papers found that none apply minimum sample size thresholds or survey date cutoffs. Survey date and N are attached as informational variables only. |
| 08 May 2026 | 93 occupations with no task statements excluded | Methodological necessity — a task-based exposure index cannot be computed without task text. |
| 08 May 2026 | Final working set confirmed: 923 occupations | Consistent with Eloundou et al. (2023) and other major papers. |
| 08 May 2026 | LLM-as-judge rubric (Eloundou-style four-criterion framework) adopted as primary exposure scoring method; raw cosine similarity not used as primary | Raw semantic similarity is insufficient as a standalone method due to the vocabulary gap problem. |
| 09 May 2026 | Aggregation rule locked: hard gate at any criterion = 0; mean of criterion scores for non-zero tasks, normalised to [0, 1] | Implements the conjunctive decision rule of Einhorn (1971). Alternatives considered and rejected (minimum function, multiplicative aggregation, bounded gate, hierarchical gate) are documented in Section 5. |
| 09 May 2026 | LLM choice locked: GPT-4o (fixed version), T=0, OpenAI Batch API | Strongest reasoning capability; closest model class to the validated Eloundou GPT-4 methodology; T=0 maximises within-version reproducibility. |
| 09 May 2026 | Multi-LLM reliability check committed: stratified sample of ~10% of tasks scored independently by Claude 3.5 Sonnet | Directly addresses the model-evaluator dependence problem documented in NBER WP 35110 (2025). |
| 09 May 2026 | Re-scoring approach abandoned in favour of exclude-and-document | Re-scoring tasks after seeing scores resembles p-hacking. Tasks identified as interpretation artefacts are excluded from the IM-weighted index with full transparency. |
| 09 May 2026 | Within-occupation exposure dispersion adopted as a reported analytical output | IM-weighted standard deviation of task-level scores per occupation. Provides richer characterisation of occupation profiles than mean alone. |
| 09 May 2026 | Binding constraint decomposition adopted as a reported analytical output | The four-criterion rubric naturally decomposes the exposure score by which structural barrier most often gates an occupation's tasks. |
| 09 May 2026 | Training cutoff acknowledged as an explicit limitation; index framed as indexed to evaluating model's training cutoff rather than calendar date | Honest acknowledgement of this constraint is more defensible than implying the index measures a calendar-date capability snapshot. |
| 10 May 2026 | Project reframed as Generative AI Vulnerability Framework / Generative AI Exposure Index, not "AI Exposure" | The Information Sufficiency criterion explicitly excludes embodied / physical AI (robotics, autonomous vehicles, sensor-driven systems). Calling this an "AI Exposure" index while gating out a major category of deployed AI is a category error. The construct is Generative AI exposure (Foundation Models — LLMs and VLMs); the rubric is sharpened, scope is honest, and the construct distinction strengthens the discriminant validity argument against historical AI measures. |
| 10 May 2026 | Validation hierarchy restructured: Eloundou and Anthropic become convergent validity (same Generative AI construct); Webb (2020) becomes discriminant validity (different historical AI construct, expected lower correlation); Brynjolfsson SML mixed; multi-LLM reliability remains within-project; expert spot-check supplementary | Webb measures a fundamentally different technology wave (supervised learning / computer vision / predictive ML up to ~2019, not Generative AI). The literature documents that Generative AI affects different demographics and tasks than prior AI waves. Therefore correlation with Webb should be materially lower than correlation with Eloundou, and the gap is itself a methodological finding. Documenting both convergent and discriminant validity is stronger than convergent validity alone. |
| 10 May 2026 | Analyst-coded tasks (845 tasks, no IM ratings) included in IM-weighted aggregate via within-occupation mean IM imputation; robustness check reports the unimputed version | Earlier draft excluded analyst-coded tasks from the IM-weighted aggregate. This was reconsidered: analyst-coded tasks are systematically the most technologically current portion of the corpus (O*NET's between-survey updates), and excluding them introduces a systematic downward bias against recent technological change in occupations. Imputation of within-occupation mean IM is the neutral assumption; the robustness check addresses the imputation directly. |
| 10 May 2026 | BERT-based reproducibility and interpretability analysis adopted as a methodological characterisation layer | Trains a regression to predict the LLM composite from sentence-BERT embeddings; reports R² and residual analysis. Directly tests how much of the LLM scoring is "deep" reasoning versus surface text features replicable by simpler embedding methods. Engages NLP / ML techniques aligned with the project's data science requirements. Computationally cheap and produces a finding regardless of which way the result goes. |
| 10 May 2026 | Within-project human-LLM validity check added as Tier 2 of validation hierarchy | Inter-LLM reliability addresses reproducibility but two LLMs can agree while both being wrong. The strongest within-project validity check is direct comparison with human ratings. Stratified 100-task sample rated by researcher + both supervising professors; Cohen's κ computed between LLM and averaged human ratings. ~4–6 hours of human time per rater; produces the strongest validity claim available without external survey data. |
| 10 May 2026 | Pre-locked validation thresholds committed | Tier 1 (multi-LLM): κ ≥ 0.70; Tier 2 (human-LLM): κ ≥ 0.60; Tier 3 (Eloundou convergent): ρ ≥ 0.55; Tier 6 (Webb discriminant): (ρ_Eloundou − ρ_Webb) ≥ 0.15. Locking thresholds in advance prevents post-hoc interpretation and is itself a methodological contribution beyond what existing exposure papers commit to. |
| 10 May 2026 | API failure and parse-failure handling protocol formalised | One automatic retry, then retry with clarifying prefix, then exclude with manual review. Documented in advance prevents ad hoc handling during the scoring run. |
| 10 May 2026 | 29 fully-unrated occupations explicitly handled with `weighting_mode = "unweighted"` flag | These are occupations where every task has Task Type = None. The within-occupation mean IM cannot be computed, so the IM-weighted mean is mathematically identical to an unweighted mean. Honest disclosure rather than pretending IM weighting applies. Occupations remain in the headline index (excluding 3.1% of the corpus is a worse loss than the loss of weighting precision). |
| 10 May 2026 | BERT reproducibility analysis run with multiple sentence-transformer variants | `all-mpnet-base-v2` and `all-MiniLM-L12-v2` to verify sensitivity. Trivial cost (local models). |
| 10 May 2026 | Pilot-overfitting defense added explicitly to documentation | A reviewer might argue the pilot overfits to known answers. Defense: (a) pilot catches systematic failure modes, not numerical tuning; (b) prompt is locked and applied to 18,796 unseen tasks; (c) post-scoring audit catches new failure modes. Logged for the audit trail. |
| 10 May 2026 | Absence of objective ground truth acknowledged as Section 6.9 limitation | Every comparator is a constructed measure. No objective measurement of "true" Generative AI exposure exists. Field-wide situation, mitigated by triangulation across methodologically diverse comparators. Acknowledged honestly rather than left implicit. |
| 10 May 2026 | Master file `task_type` column uses `Unrated` (not `None`) as the sentinel for analyst-coded tasks | Discovered during preprocessing execution. `None` is in pandas' default `na_values` list, so writing it to CSV and reading back silently re-parses it as missing. `Unrated` is descriptive, not in any default null-sentinel list, and survives a CSV round-trip cleanly. Decision recorded for transparency; alternative sentinels (NaN, empty string) all have the same round-trip ambiguity. |
| 10 May 2026 | Rubric prompt v2: chain-of-thought reasoning fields per criterion + two-field balanced structure for Criterion 4 + structured outputs (JSON Schema strict mode) + uniform-scope disambiguation rule | v1 of the prompt used direct zero-shot scoring with strict JSON-only output. v2 adds: (a) per-criterion reasoning fields placed before score fields, mitigating both stochastic variance and self-assessment bias; (b) two reasoning fields for Criterion 4 (`capability_match_what_works` / `capability_match_what_might_fail`) — schema-required, neutrally named — to force balanced consideration without anchoring on specific failure modes; (c) JSON Schema strict mode via OpenAI structured outputs eliminates format parse failures by API construction; (d) disambiguation rule explicitly scoped to all four criteria (v1 inadvertently narrowed it to Information Sufficiency); (e) negative formatting instructions removed (redundant under structured outputs). Backed by literature: chain-of-thought (Wei et al. 2022); LLM anchoring (Suri et al. 2024); LLM cognitive biases (Echterhoff et al., Itzhak et al.). The two-field structure for Criterion 4 specifically addresses the bias-bias trade-off — RLHF over-confidence vs. failure-mode anchoring — by using schema rather than instruction text as the forcing function. Prompt token cost increased from ~1,400 to ~1,668 input tokens per task, total expected API spend now ~£48–52 (still within £60 envelope). |
| 21 May 2026 | Validation Tier 7 (expert occupation-level spot-check) dropped, reducing the hierarchy from seven to six tiers | Supervisor feedback flagged that a 25–30 occupation expert review is time-consuming for a tier that was only ever supplementary face-validity, not load-bearing. The methodologically rigorous human comparison is at Tier 2 (task-level human-LLM validity sample of 100 tasks rated by researcher + both supervisors). Dropping Tier 7 leaves Tier 2 to carry the human-rating contribution. Documented as Decision History entry 5.18. |
| 21 May 2026 | Stratified sampling protocol locked for Tier 2 (within-project human-LLM validity check): four strata of 25 tasks each, defined by LLM composite score quartiles (0, (0, 0.5], (0.5, 0.75], (0.75, 1.0]) | Supervisor feedback raised the concern that a pure random sample over 18,796 tasks would over-represent whichever score region is most populous, inflating or deflating κ for reasons unrelated to actual measurement validity. Stratification by LLM composite score ensures coverage across the full agreement structure — including the zero-gated tasks where the non-compensatory aggregation rule and the disambiguation rule have the most consequential effects. Standard practice in inter-rater reliability literature. Documented as Decision History entry 5.19. |
| 21 May 2026 | Rater guide produced (`docs/rater_guide.md`) for the Tier 2 human validity sample | A one-document reference for the three raters (researcher + both supervisors) that defines the four criteria in plain language, restates the disambiguation rule, walks through four worked examples (clear high, clear low, ambiguous, partial), and describes the rating procedure. Standard practice in inter-rater reliability work: without a shared rater reference, κ falls for reasons unrelated to the rubric or the LLM. Producing the guide before the rating session de-risks the validity check. |
| 23 May 2026 | Criterion 1 (Decomposability) reworded to decouple it from capability (rubric prompt v3) | A criterion-overlap review identified that the v2 Decomposability definition ("sub-steps that a Foundation Model can execute") imported capability into the structural judgement, entangling it with Criterion 4 by construction. v3 reframes Decomposability as a pure task-structure question — is the task a serialisable procedure or an irreducible gestalt — explicitly independent of whether any system can execute the steps. This maximises the criterion's independent variance before it is tested empirically. Documented in Decision History 5.20. |
| 23 May 2026 | Criterion 4 (Capability Match) anchors sharpened to make the task-intrinsic reliability bar explicit | "Production proficiency" now explicitly means reliable enough to use without per-instance human re-checking; output that must be verified each time is assistance (score 1), not substitution (score 2). This captures the task-intrinsic component of error tolerance that the overlap review correctly flagged as underweighted, while keeping the context-dependent component (employer-specific regulatory/liability environment) out of scope. Documented in Decision History 5.21. |
| 23 May 2026 | Exception Sensitivity / Error Tolerance considered as a replacement for Decomposability and not adopted | A reviewer proposed replacing Decomposability with an "Exception Sensitivity" criterion (can the task tolerate occasional AI errors without continuous expert oversight). Not adopted for three reasons: (a) it reverses the documented scope decision to exclude institutional friction / cost of error (Section 5.8) — exception sensitivity is context-dependent and not operationalisable at task level; (b) it changes the construct from technical capability to capability-plus-adoption, breaking comparability with Eloundou / Felten / Webb / Anthropic that the validation hierarchy depends on; (c) it partly double-counts with Capability Match, whose reliability bar was instead sharpened to absorb the task-intrinsic part of the concern. Noted as an excellent basis for a complementary displacement-risk index in future research. Documented in Decision History 5.21. |
| 23 May 2026 | Criterion dimensionality analysis added (Output D, Section 3.6); Decomposability held as a fixed fourth criterion | Four diagnostics (correlation matrix, PCA / factor analysis, gate-attribution stability, per-criterion inter-rater disagreement) test whether the four criteria are empirically separable, reframed as "which dimensions of AI substitutability are empirically separable?" The analysis is diagnostic and reported, NOT a trigger to drop or collapse a criterion. The four-criterion structure is held fixed (per explicit instruction): a data-dependent decision to drop a criterion would itself invite questioning, and the four-way binding-constraint decomposition has interpretive value worth preserving. Documented in Decision History 5.20. |
| 03 Jun 2026 | Scoring switched from the OpenAI Batch API to the synchronous Chat Completions API | The funded account is Usage Tier 1, whose Batch enqueued-token limit for gpt-4o is 90,000 tokens — the full job is ~38.3M enqueued tokens (~425× over), and even the 75-task pilot (~153K tokens) exceeds it, so Batch is unusable on this account and micro-chunking into ~44-task batches (430+ sequential submissions) is infeasible. The synchronous API is bounded by the 30,000 TPM rate limit, not the Batch queue, so it runs today. Trade-off: synchronous pricing has no 50% Batch discount, raising the estimated full-run cost from ~£53 to ~£69 (with prompt caching) up to ~£87; partially mitigated by automatic prompt caching of the identical system prompt (a `prompt_cache_key` routing hint is set). The professor was informed of and accepted the cost change. Script rewritten with paced requests, exponential backoff on rate limits, per-task checkpoint/resume, a cost safety cap, and a fixed `seed`. The prompt, schema, aggregation, and validation are unchanged. Documented in Decision History 5.22 and Implementation Log 9.5. |
| 03 Jun 2026 | First pilot run (75 tasks, gpt-4o); revealed the v3 criteria collapsed the index | The pilot composite took only 3 values (0 / 0.75 / 0.875); every digital task scored 0.875; Information Sufficiency, Output Verifiability, and Decomposability correlated at 0.95–0.99 (all measuring "physical vs digital"); Capability Match never scored 2 (impossible "no re-checking" bar). The pilot did its job — caught a construct failure for ~£0.39 before the ~£75 full run. Evidence in Implementation Log 9.6 and Decision History 5.23. |
| 03 Jun 2026 | Criteria redesigned to v3.1: four distinct, literature-grounded barriers | Information Sufficiency (kept; physical barrier — Frey & Osborne 2013; Autor-Levy-Murnane 2003); Output Verifiability → **Objective Verifiability** (checkable-success barrier — Brynjolfsson-Mitchell-Rock 2018; Frey & Osborne creative-intelligence bottleneck); Decomposability → **Contextual Independence** (social + tacit-knowledge barrier — Frey & Osborne social-intelligence bottleneck; Deming 2017; Autor 2015 / Polanyi's Paradox); Capability Match recalibrated to a human-equivalent bar (Eloundou et al. 2023). Each criterion now states what it is NOT about (anti-leakage), and anchors use minimal, domain-diverse, pattern-breaking examples under an explicit anti-anchoring instruction (Suri et al. 2024). Reverses 5.20 (Decomposability held as fixed) and the v3 reliability bar in 5.21. Documented in Decision History 5.23. |
| 03 Jun 2026 | Aggregation changed to Design Y (gate on impossibility, modulate on quality) | Gate (composite 0) if Information Sufficiency = 0 OR Capability Match = 0 (categorical impossibilities — no body / beyond capability, per Einhorn 1971 conjunctive logic); otherwise composite = mean(all four)/2, so Objective Verifiability and Contextual Independence modulate without zeroing. Resolves the "arbitrary" objection that rejected hierarchical gating in 5.5: the gating criteria are exactly the ones representing absolute impossibility for the technology. Restores a meaningful gradient (subjective-capable digital ≈ 0.75; subjective-relational ≈ 0.375; fully-substitutable = 1.0). Documented in Decision History 5.24; supersedes 5.5's choice. |
| 03 Jun 2026 | Schema field renames | `output_verifiability_*` → `objective_verifiability_*`; `decomposability_*` → `contextual_independence_*`, in `rubric_prompt.py` and `03_score_tasks.py`. Capability Match retains its two reasoning fields (`what_works` / `what_might_fail`). Nine fields total, unchanged count. |
| 03 Jun 2026 | v3 scoring outputs archived to `data/processed/archive/v3/` | The first pilot's outputs (scored CSV, progress JSONL, log, for both the pilot and the smoke test) were moved out of the live `data/processed/` folder into a new `archive/v3/` subfolder, with a README. Reason: (a) preserve the v3 results for direct comparison against the v3.1 re-pilot and the methodological record; (b) operational necessity — the scoring script resumes from any `progress_*.jsonl` in the live folder, so a leftover v3 progress file would make the v3.1 re-pilot skip already-scored tasks and return stale v3 scores. Input files (pilot_tasks.csv, smoke_test_tasks.csv, master_tasks.csv) are version-independent and were left in place. |
| 04 Jun 2026 | v3.1 re-pilot succeeded; one over-correction found in Criterion 3 | The v3.1 re-pilot produced a 7-value composite gradient, Capability Match reached 2 (8 tasks), and Objective Verifiability fully decoupled (correlations −0.16 to 0.29). But reading the reasoning showed Contextual Independence was over-applied — docking points for documentable organisation-specific context (procedures, files, policies) that could simply be supplied, systematically under-scoring routine digital cognitive work. The IS–CM 0.96 correlation was confirmed a genuine one-directional property (IS=0 ⟹ CM=0; IS=2 ⇏ CM=2), kept and reported, not a defect. Evidence in Implementation Log 9.7. |
| 04 Jun 2026 | v3.2: single surgical refinement to Criterion 3 (Contextual Independence) | Added one clarifying sentence — documentable context (procedures, specifications, files, policies, client requirements) that could be supplied to the model is NOT a barrier; only real-time human interaction or genuinely tacit/undocumented knowledge is — plus a sharpened score-2 anchor ("coding to a documented company style guide → 2"). Criteria 1, 2, 4, the schema field names, the scoring code, and Design Y are byte-for-byte unchanged, so the re-pilot should affect only Criterion 3. Chosen minimal (one sentence) rather than a full rewrite to avoid introducing new failure modes. Documented in Decision History 5.25. |
| 04 Jun 2026 | Determinism/isolation check via the unchanged criteria (no second run) | Rather than pay for a dedicated twice-run, the v3.2 re-pilot is run once and criteria 1, 2, and 4 — whose wording is byte-identical to v3.1 — are compared against the archived v3.1 scores. If those three are unchanged, the model is behaving stably AND the Criterion-3 edit is confirmed isolated, in one comparison. This bundles two effects it cannot fully separate (pure run-to-run stochasticity at T=0, and any indirect "ripple" from changing the surrounding prompt text), but for the practical question — *did the edit disturb the other criteria?* — that bundle is exactly what should be near-zero. Only if criteria 1/2/4 move materially would a dedicated identical-prompt twice-run be needed to disentangle the two. Cheaper and sufficient. |
| 04 Jun 2026 | **v3.2 re-pilot passed; prompt v3.2 LOCKED for the full run** | Single run, $0.39. Unchanged criteria held to within the temperature-0 floor: Information Sufficiency 0/75 changed, Objective Verifiability 4/75, Capability Match 2/75 — 6/225 (2.7%) scores, all ±1 except one and bidirectional (noise, not edit ripple); gate set identical (75/75, 37 PASS/38 GATED). Criterion 3 moved exactly as intended (13 routine documentable-context tasks rose; PASS-task Contextual-Independence 2-count 15→24); the genuine relational floor held 8/8; the only "fallers" were gated physical tasks whose Contextual-Independence score never enters the composite (harmless, recorded). Composite kept its 7-value gradient (mean 0.395). No further rubric changes planned — any future change restarts the pilot. Cumulative pilot spend ≈ $1.20 (≈ £0.95). Full evidence in Decision History 5.26 and Implementation Log 9.7. |
| 06 Jun 2026 | Pre-run operational changes for incremental funding and early validity (no re-pilot needed) | (a) `03_score_tasks.py` now halts cleanly on out-of-credit (`insufficient_quota`) instead of churning, so the full run can be funded in increments and resumed; (b) the full-run input is now `master_tasks_shuffled.csv`, a fixed-seed permutation of `master_tasks.csv`, so the pre-run validation pool is the run's first chunk (zero re-scoring); (c) the Tier-2 human validity check is brought forward — score the shuffled prefix with the remaining ≈ $3.80, draw a random 100, rate before the full run; (d) the rater guide's criteria are now **verbatim-identical** to the system prompt (28/28 phrases verified) to remove any wording confound, and a verbatim exact-prompt PDF was produced for the supervisors. None of these touch the locked rubric/schema/model/temperature/aggregation. Details in Implementation Log 9.8. |
| 06 Jun 2026 | Tier-2 validity sample changed from stratified to **simple random** | On the supervisors' recommendation, the 100-task human-validity sample is now a simple random draw (fixed seed) rather than 25 per composite-score band. Rationale: a population-representative κ (agreement on a *typical* task), and no analyst degrees of freedom in sample construction. Trade-off (sparse-region coverage; the prevalent zero-gated category depressing Cohen's κ — the prevalence/kappa effect) is handled by also reporting percent agreement, the confusion matrix, per-criterion κ, and the sample's score distribution — not by re-stratifying. Threshold κ ≥ 0.60 retained. Supersedes 5.19; documented in Decision History 5.27 and Section 3.4. |

---

## 5. Decision History: Alternatives Considered and Rejected

This section documents the methodological alternatives that were considered during the design phase and the reasons each was rejected. Its purpose is to enable any reader — particularly the supervising professors — to reconstruct the reasoning behind every design choice. The Decisions Log (Section 4) records what was decided. This section records what was *not* chosen and why.

### 5.1 The Decision to Restart from MAEI v1

The original MAEI (Modern AI Exposure Index) was scrapped after the methodological audit identified twelve construct validity and design issues. The most serious were:

- **Frey & Osborne (2013) used as ground truth Y variable.** Their automation probabilities were expert judgements at the occupational level for 700 occupations, not measured outcomes. Using them as ground truth for a 2026 prediction task assumes both that they were correct in 2013 and that automation potential has not changed since. Both assumptions are weak.
- **Multipliers applied to already-modern O*NET features.** The MAEI multiplied O*NET features by hand-tuned multipliers chosen by sensitivity analysis on training data, not theoretically motivated. An ablation study showed they barely changed the final ranking (Spearman ρ across 7 ablation scenarios ranged 0.7636–0.7651), demonstrating that the multipliers were not doing work.
- **Hardcoded keyword lists, single-author task taxonomy, and no inter-rater protocol.** All would fail peer review.
- **Train/test split on Frey & Osborne–scored occupations only.** The model was trained and tested on the same 711 occupations — a classic case of evaluation on the same population as training.

The decision was to abandon MAEI v1 entirely and rebuild. The rebuild dropped F&O as Y entirely (no Y variable in the new design — exposure is measured directly via the rubric, not predicted from features) and replaced the multiplier-based feature engineering with a text-based LLM rubric.

### 5.2 Why Semantic Similarity Was Considered and Rejected as Primary Scoring

The first plan for the rebuild used sentence-transformer embeddings to compute cosine similarity between O*NET task statements and Foundation Model capability descriptions. This was rejected for two reasons:

- **The vocabulary gap problem.** Sentence-transformer models trained on general-domain text do not reliably preserve semantic equivalence between specialised occupational vocabulary and specialised technical vocabulary.
- **The construct mismatch.** Cosine similarity measures lexical proximity in embedding space. Our construct of interest is whether Foundation Models can perform a task — a different thing entirely.

Semantic similarity is not used as a parallel scoring method. However, BERT-based embeddings *are* used in this project for reproducibility analysis (Section 3.5) — characterising what the LLM rubric is doing rather than acting as an alternative scoring channel. This is a different role for the same technique.

### 5.3 Why DWAs Were Considered and Rejected as Fallback Scoring Text

An earlier draft proposed using Detailed Work Activities as fallback scoring text. Rejected:

- **DWAs are too abstract.** The contextual signal is stripped.
- **DWAs are too short.** Most DWA titles are five to ten words — too little text for a four-criterion rubric.
- **DWAs are cross-occupational.** Each DWA maps to dozens of occupations, destroying the within-occupation signal.

DWAs are retained as structural reference material only.

### 5.4 Why O*NET Cannot Be Used for the Adaptation Capacity Index (Part 2)

If we constructed an Adaptation Capacity Index from O*NET features (Active Learning, Adaptability, Learning Strategies, Initiative), those variables would simultaneously reduce exposure AND increase adaptation capacity — i.e., they would reduce vulnerability twice. This is a construct validity failure. The fix: use a completely independent data source (PIAAC) for the ACI in Part 2.

### 5.5 Aggregation Rule Alternatives Considered

> **Superseding note (03 June 2026):** Alternative 4 below (hierarchical gating) was rejected here as "arbitrary," and Alternative 5 (hard gate on all four) was adopted. After the first pilot, the aggregation was changed to **Design Y** — a hierarchical gate with a principled basis (gate on categorical impossibility, modulate on substitution quality). The reasoning that resolves the "arbitrary" objection is in Section 5.24; this section is retained as the original record.

Five non-compensatory aggregation rules were evaluated. The original choice was the hard gate + mean for non-zero tasks (later superseded by Design Y).

**Alternative 1 — Minimum function (composite = min(c1, c2, c3, c4) / 2).** Rejected. With a 3-point scoring scale (0/1/2), the minimum function produces only three possible task-level composites: 0, 0.5, and 1.0. Tasks scoring (1, 2, 2, 2) and (1, 1, 1, 1) become indistinguishable. This discards substantial information from three of the four criteria.

**Alternative 2 — Multiplicative aggregation (composite = (c1 × c2 × c3 × c4) / 16).** Rejected. Produces hard-gate behaviour at zero and rich differentiation in the non-zero range, but the penalty asymmetry is hard to defend. A score of (1, 2, 2, 2) yields composite = 8/16 = 0.5, which feels disproportionately severe. Non-linear relationship between raw scores and composite is hard to explain intuitively.

**Alternative 3 — Bounded gate (any criterion = 0 → composite capped at, e.g., 0.1).** Rejected. The cap value is entirely arbitrary and lacks principled justification. A reviewer would ask "why 0.1 and not 0.05?" with no answer grounded in theory.

**Alternative 4 — Hierarchical gate (only certain criteria gate).** Rejected. The asymmetry across criteria is itself a design judgement that invites further questioning. If Decomposability = 0 truly means "this task has no decomposable structure whatsoever," it is hard to argue this should not gate.

**Alternative 5 (chosen) — Hard gate + mean for non-zero tasks.** Adopted. Implements Einhorn's (1971) conjunctive rule directly. Mixes two logics (gating then compensatory mean), but the gating logic identifies absolute failures while the mean is applied within the space of acceptable tasks. Sequential procedure, not logical contradiction.

### 5.6 Why Eloundou's E0/E1/E2 Framework Was Considered and Modified

Eloundou et al. (2023) define their three exposure tiers based on ≥50% task completion time reduction. We adopted the LLM-as-judge approach in general but did not adopt their specific rubric:

- **Speedup vs. substitution mismatch.** Their construct is "can an LLM cut task time in half." Ours is "can current Foundation Models perform this task at human-equivalent proficiency." A task where AI doubles a human's productivity scores E1 in their framework. We want to distinguish this from cases where AI replaces the human entirely.
- **Three-tier categorical vs. four-criterion structured.** Their categorical scheme cannot decompose by structural reason. Our four-criterion structure produces this decomposition as a natural byproduct.
- **κ > 0.70 inter-rater agreement.** Their result validates their rubric, not ours specifically. We cite it as evidence that the LLM-as-judge approach can produce results consistent with human judgement, not as direct external validation of our specific rubric.

### 5.7 Why Anthropic's β = 0.5 Augmentation Weighting Was Not Adopted

Anthropic (2025) downweights augmentative use at β = 0.5 relative to fully automated use at β = 1. Our rubric does not include such a weighting:

- **Scope difference.** Anthropic captures both substitution and augmentation in a single index. Our scope decision is to measure substitution only.
- **No usage data.** Anthropic's β = 0.5 is grounded in observed Claude usage patterns. We do not have access to comparable data.
- **Interpretive cleanliness for Part 2.** The vulnerability framework benefits from a substitution-only exposure measure.

### 5.8 Why Institutional Friction Was Not Added to the Index

A rubric criterion measuring regulatory and liability barriers was considered as a fifth criterion. Rejected:

- **Operationalisation problems.** Institutional friction varies by country, industry, time period, and individual employer.
- **Subjectivity beyond the other criteria.**
- **Field practice.** No published exposure paper attempts to measure institutional friction at task level.

Institutional friction is documented in Section 3.3 as out of scope and listed in Section 6 as a known methodological limitation.

### 5.9 Why Re-Scoring Was Considered and Replaced with Exclude-and-Document

An earlier draft proposed re-scoring tasks identified as interpretation artefacts. Replaced because re-scoring after seeing scores resembles p-hacking. Exclude-and-document is more transparent.

### 5.10 Why Mean-IM Imputation for Emerging Tasks Was Deprecated (and Why Analyst-Coded Tasks Are Treated Differently)

A previous version proposed including emerging tasks in a robustness check via within-occupation mean-IM imputation. This was deprecated for emerging tasks, but the same imputation logic *is* applied to analyst-coded tasks. The two cases are not parallel:

- **Emerging tasks** (Section 1.7) have not completed the O*NET data collection cycle. They are flagged as speculative additions whose status in the occupation is uncertain. Imputing weights for them implicitly assumes they will stabilise as currently described, which is exactly the assumption O*NET is testing by leaving them in the emerging set. Imputation here is unjustified.
- **Analyst-coded tasks** (Section 1.2) have stabilised in the O*NET corpus. They are O*NET's editorial updates between waves to capture structural change. The only thing missing is the IM rating, because incumbents have not yet been re-surveyed for that occupation. Imputing within-occupation mean IM is a neutral assumption: in the absence of a specific signal, we treat them as average-importance tasks for that occupation.

The two cases use different reasoning because their data-quality status is different, even though both lack IM ratings.

### 5.11 Why Date and Sample Size Cutoffs Were Considered and Rejected

The literature review (Section 2.4) revealed that no major published exposure paper applies such cutoffs. The field standard is to use the full O*NET dataset with quality variables attached as informational only. We follow the field standard.

### 5.12 Why Webb (2020) Was Repositioned from Convergent to Discriminant Validator

An earlier draft of the validation strategy positioned Webb (2020) as the primary external validator (Tier 2 convergent validity). This was reconsidered:

- Webb's exposure measure uses patent text from approximately 2010–2019, capturing the supervised learning / computer vision / predictive ML wave that *preceded* Generative AI.
- The labour economics literature documents that Generative AI affects a fundamentally different task and demographic profile than the prior AI wave.
- If our index correctly captures Generative AI specifically, correlation with Webb should be **lower** than correlation with same-construct measures (Eloundou, Anthropic). Strong correlation with Webb would be a warning sign that our index is failing to capture what is distinctive about Generative AI.

Webb is therefore repositioned as a discriminant validity check (Tier 5 in Section 3.4): we expect materially lower correlation than with Eloundou, and the gap between the two correlations is itself the empirical finding. This reframing produces a stronger validity argument than convergent validity alone — it demonstrates construct specificity, not just consistency with prior work.

### 5.13 Why Analyst-Coded Tasks Are Imputed and Included (Not Excluded)

An earlier draft proposed excluding the 845 analyst-coded tasks from the IM-weighted aggregate because they lack IM ratings (the "score-only" approach). This was reconsidered:

- **Analyst-coded tasks are not random noise.** They are O*NET's mechanism for capturing structural change between full incumbent survey waves — systematically the most technologically current portion of the corpus.
- **Excluding them from the headline aggregate creates systematic bias.** The aggregate would be computed only on older, incumbent-surveyed tasks. For an occupation that recently changed and acquired five highly exposed analyst tasks, the headline index would ignore them entirely.
- **The bias direction is wrong for our index.** A measure of Generative AI exposure that systematically underweights the most recent technological updates is biased *against* its own construct.

The corrected approach: impute within-occupation mean IM for analyst-coded tasks (the neutral assumption — average importance for that occupation), include them in the IM-weighted aggregate, and report a robustness check without imputation. The unverifiable assumption introduced by imputation is much smaller than the systematic bias introduced by exclusion. The robustness check addresses the imputation directly by reporting both versions.

This is one of the most consequential corrections in the methodology design. The earlier draft had it backwards: the "exclude these tasks because we cannot weight them" framing treated the absence of an IM rating as a quality problem, when in reality it is a survey timing problem.

### 5.14 Why Felten Was Considered and Rejected as Primary External Validator

Felten et al. (2021) is widely cited but uses O*NET work activities crossed with AI progress benchmarks. Their data foundation overlaps substantially with ours. Webb is more independent. Webb is the primary discriminant validator; Felten is retained as supplementary comparison and is honestly framed as sharing more methodological infrastructure with us than Webb does.

### 5.15 Why the Project Was Reframed from "AI Exposure" to "Generative AI Exposure"

An earlier draft used the term "AI Exposure Index" throughout. The Information Sufficiency criterion explicitly excludes physical AI: tasks requiring embodiment, real-time sensor data, or physical interaction are zero-gated regardless of how the task scores on the other three criteria.

This is consistent if and only if the index is understood to measure **Generative AI** specifically — i.e., Foundation Models (LLMs, VLMs, multimodal generative systems) that operate on text, images, structured data, and code. It is *not* consistent with a general "AI Exposure" framing, because robotics, autonomous vehicles, computer vision-based physical inspection, and industrial automation are also AI, are also deployed in the workplace, and would be systematically scored as zero by our rubric.

The reframing to "Generative AI Vulnerability Framework" (project) and "Generative AI Exposure Index" (Part 1 deliverable) is therefore not a stylistic choice. It is required for the methodology to be internally consistent. The rubric is sharpened to specifically reference Foundation Models in Criterion 4. Section 3.3 explicitly states what the index does and does not cover.

This reframing also strengthens the project's positioning: it clearly distinguishes our work from older AI exposure measures (Webb 2020) and aligns with the trajectory of the labour economics literature since 2023, which has increasingly differentiated Generative AI from prior AI waves as a distinct technological and economic phenomenon.

### 5.16 Why the Rubric Prompt Was Revised from v1 to v2

The first draft of the scoring prompt (v1, 10 May 2026 morning) used direct zero-shot scoring: the LLM was instructed to output only the four integer scores in JSON form, with no intermediate reasoning. After review, five issues were identified that prompted a substantial revision to v2 (10 May 2026 afternoon):

1. **No chain-of-thought reasoning.** The prompt banned intermediate reasoning ("respond with ONLY a single valid JSON object"). For multi-dimensional occupational judgements, direct zero-shot scoring is known to produce noisier and more biased outputs than reasoning-first scoring. The chain-of-thought literature (Wei et al. 2022 and follow-ups) is unambiguous on this for reasoning-heavy tasks. v2 adds per-criterion reasoning fields placed before score fields in the schema, forcing the model to articulate its logic before committing to an integer.

2. **Disambiguation rule scope was confused.** v1 instructed the LLM to assume a digital implementation when ambiguous, but then said "Only score Information Sufficiency as 0 when..." — which inadvertently implied the digital assumption applied only to that one criterion. The model could have applied a digital interpretation for IS but reverted to a physical interpretation for the other three criteria, producing contradictory composite scores. v2 explicitly scopes the disambiguation rule to apply uniformly across all four criteria.

3. **No prompt-level mitigation for self-assessment bias.** Section 3.9 documents that Criterion 4 (Capability Match) is the most vulnerable to RLHF-induced overconfidence: the LLM is essentially being asked whether models like itself can do the task, and RLHF training rewards confident-sounding answers. v1 did nothing to mitigate this at the prompt level — it relied entirely on the multi-LLM reliability check downstream.

4. **Listing failure modes would create the inverse bias.** An obvious "fix" for issue 3 is to instruct the model to first identify failure modes (hallucination, edge cases, training-data gaps, etc.) before scoring Criterion 4. This was considered and rejected, because the cognitive bias literature (Suri et al. 2024 on anchoring; Echterhoff et al., Itzhak et al. on broader LLM cognitive biases) shows that listing examples in evaluation prompts disproportionately shapes the resulting evaluations. Listing failure modes would induce **availability bias** toward those listed failures, biasing scores downward — the inverse of the original problem rather than a fix.

   The v2 solution avoids both biases by using the schema as the forcing function: Criterion 4 has *two* reasoning fields, `capability_match_what_works` and `capability_match_what_might_fail`, both schema-required, both neutrally named, neither containing pre-loaded content. The model is instructed in the prompt to bring its own task-specific reasoning to each field. Schema enforcement is more reliable than instruction text — the LLM cannot leave either field empty. Neither field name primes specific content. Balanced reasoning is structurally enforced, not example-driven.

5. **Operational issues:** The v1 cost math was inconsistent with its own self-test output (the comment said ~500 tokens per task while the self-test reported ~1,355). v1 also used `response_format: {"type": "json_object"}` and added negative formatting instructions ("do not wrap in code fences"), both of which are redundant or potentially confusing under OpenAI's stricter `json_schema` mode. v2 corrects the math, switches to `json_schema` strict mode (which eliminates format parse failures by API construction), and removes the negative formatting instructions.

The v2 prompt is documented in `src/rubric_prompt.py`. It remains a draft until pilot-tested per Section 3.8.

### 5.17 Why a BERT-Based Reproducibility Layer Was Added

The project's data science / NLP content was previously thin. The LLM rubric is applied NLP, but the methodological focus was on the rubric design and aggregation logic rather than on text representation methods themselves. Adding a BERT-based reproducibility analysis (Section 3.5) addresses this by:

- Producing a quantitative answer to a question the LLM-as-judge literature has not rigorously addressed: how much of the LLM scoring is "deep" reasoning versus surface text features replicable by simpler embedding methods.
- Engaging Prof. Dash's expertise in BERT, NLP, and ML directly.
- Producing a reportable finding (R² and residual analysis) regardless of which direction the result falls.

The addition is bounded: it is a single subsection of the methodology, computationally cheap, and does not change the headline scoring approach.

### 5.18 Why the Expert Occupation-Level Spot-Check (Tier 7) Was Dropped

An earlier draft of the validation hierarchy included a seventh tier: a domain-expert review of 25–30 occupations spanning the score range, with the supervising professors and possibly additional labour-economics colleagues judging whether the occupation-level scores looked intuitively correct. This was supplementary face validity at the occupation level, distinct from Tier 2 (which is task-level human-LLM rating).

On 11 May 2026, the supervising professors flagged two concerns with this tier. First, a 25-occupation expert review is genuinely time-consuming — each occupation requires reading the task list and forming a holistic judgement, and asking three busy domain experts to do this for 25 occupations is several hours of work per reviewer for evidence that was always positioned as supplementary. Second, the rigorous human-rating contribution to the validation framework already comes from Tier 2, which has the same people rating 100 tasks against the same rubric in a quantitative way. Tier 2 produces a Cohen's κ; Tier 7 produced only qualitative agreement at the extremes.

The decision was to drop Tier 7. The argument for keeping it would be that occupation-level intuition and task-level intuition test different things — a human might agree task-by-task while disagreeing on the overall occupation score, or vice versa. This is conceptually true but practically marginal: in the validation chain, what is load-bearing is the task-level κ at Tier 2 plus the external comparisons at Tiers 3 through 6. The occupation-level spot-check would add a small qualitative footnote, not a meaningful additional check.

The validation hierarchy is therefore six tiers (Section 3.4). Tier 2's sampling protocol is documented in Section 5.19 (originally stratified; changed to simple random on 06 June 2026 — Section 5.27).

### 5.19 Why Stratified Sampling Was Chosen Over Pure Random for the Tier 2 Validity Sample

> **Superseded (06 June 2026):** On the supervisors' recommendation, the Tier 2 sample was changed from the stratified design described here to **simple random sampling**. The reasoning for the change — population-representativeness, removal of analyst degrees of freedom, and the reporting safeguards that address this section's "saturating on easy cases" concern — is in Section 5.27. This entry is retained as the original record of why stratification was first chosen.

The Tier 2 validity sample is 100 tasks rated by three humans and compared against the LLM. The initial draft of the protocol said only "stratified random sample of 100 tasks" without specifying the strata. On 11 May 2026, the supervising professors raised the question explicitly: random or stratified, and if stratified, by what variable?

**Why pure random was rejected.** The corpus of 18,796 tasks is not uniformly distributed across LLM scores. After scoring, the distribution will be heavy-tailed: many clearly-digital tasks scoring near the top, many physically-gated tasks scoring zero, fewer tasks in the middle ranges. A pure random sample of 100 tasks would over-represent whichever score region happens to be most populous, and the resulting κ would tell us about agreement on the dominant region but say little about agreement on the boundary regions where human judgement is actually most likely to disagree with the LLM. In the worst case, a random sample could inflate κ by saturating on easy cases where everyone agrees, giving a misleadingly positive validity claim.

**The stratification chosen.** Four strata of 25 tasks each, defined by LLM composite task-level score:

- Stratum 1: tasks with composite score = 0 (zero-gated tasks) — 25 tasks
- Stratum 2: tasks with composite score in (0, 0.5] — 25 tasks
- Stratum 3: tasks with composite score in (0.5, 0.75] — 25 tasks
- Stratum 4: tasks with composite score in (0.75, 1.0] — 25 tasks

Within each stratum, tasks are sampled uniformly at random. Sample size of 25 per stratum gives reasonable statistical power within each region; total of 100 is tractable for three raters (~4–6 hours each).

**Why these strata in particular.** Stratifying by LLM composite score ensures coverage across the full agreement structure. Stratum 1 contains the zero-gated tasks — exactly the cases most affected by the non-compensatory aggregation rule and the disambiguation rule, and exactly where human disagreement with the LLM would be most informative. Strata 2–4 cover the non-zero range. The choice of (0.5, 0.75] and (0.75, 1.0] as the upper-quartile split (rather than (0.5, 0.67] and (0.67, 1.0], say) is anchored on the composite-score arithmetic: 0.5 corresponds to a task scoring all 1s in non-zero criteria; 0.75 corresponds to averaging the equivalent of three 2s and one 1; 1.0 is all 2s.

**Alternative stratifications considered and not chosen as primary.** Stratification by Domain Source (Incumbent / OE / Analyst) was considered as a secondary check on data-quality-type effects, and stratification by Task Type (Core / Supplemental / Unrated) was considered as a secondary check on rating-completeness effects. Both are useful sub-analyses but are not the primary stratification because the LLM-score distribution is the variable that most directly affects how κ should be interpreted. Both can be reported as supplementary tables if useful.

**Defence against the post-hoc stratification concern.** Locking the stratification protocol in writing before any task is selected for the sample is itself the defence. Stratification on the LLM composite score is justified by the methodological argument above, not chosen after seeing which stratification produces the highest κ.

A rater guide (`docs/rater_guide.md`, produced 21 May 2026) accompanies the protocol: it defines the criteria in plain language for the three human raters, restates the disambiguation rule, walks through four worked examples, and describes the rating procedure. The guide is also the defence against the second concern raised by the professors — that without a shared reference, κ would fall for reasons unrelated to the rubric or the LLM. Without a rater guide, three intelligent people interpreting a four-criterion rubric will produce three different interpretations.

### 5.20 Why Decomposability Was Reworded to Decouple It from Capability (and Held as a Fixed Criterion)

> **Superseded (03 June 2026):** Decomposability was *replaced* by Contextual Independence in v3.1 after the first pilot showed it did no independent work (every below-2 score fell on a physical task; it was constant on all digital tasks). See Section 5.23. This entry is retained as the original record of why it was held as a fixed criterion — a decision the pilot evidence reversed.


A detailed criterion-overlap review on 23 May 2026 made two correct observations about Decomposability. First, the v2 definition of the criterion — *"can the task be broken into discrete sub-steps that a Foundation Model can execute?"* — imported capability directly into the structural judgement through the phrase "that a Foundation Model can execute." This entangled Decomposability with Criterion 4 (Capability Match) by construction, not merely as an evaluator-psychology artefact: the definition itself instructed the model to consider FM capability when scoring task structure. Second, decomposability is in any case partly capability-dependent in the world — a sufficiently capable agent system can impose decomposition structure on a task that looks holistic to a bare model — which makes it the least naturally orthogonal of the four criteria.

**The rewording (v3).** Decomposability is reframed as a pure question about task *structure*: can the task be expressed as a sequence or graph of discrete sub-steps with well-defined intermediate inputs and outputs, independent of whether any system (AI or human) can perform the steps? Capability is explicitly excluded and assessed only in Criterion 4. The worked examples in the rater guide were updated to reflect this — most visibly, "administer intramuscular injections" now scores Decomposability 2 (the procedure is structurally a defined sequence) rather than the v2 score of 1, with the task still correctly zeroed by Information Sufficiency and Capability Match. This makes the decoupling concrete for human raters.

**Why Decomposability was held as a fixed fourth criterion rather than collapsed.** The review proposed, as one option, pre-committing to collapse the rubric to three criteria if the post-scoring dimensionality analysis showed Decomposability and Capability Match loading on a single factor. This was considered and explicitly rejected (per supervisor instruction). The four-criterion structure is held fixed regardless of what the dimensionality analysis (Output D, Section 3.6) shows. The reasoning: a data-dependent decision to drop a criterion after seeing the correlations would itself be a model-selection step that a reviewer could question ("you dropped it because the numbers told you to — would you have kept it if they had come out differently?"); the four-way binding-constraint decomposition has interpretive value worth preserving; and reporting any overlap honestly as a finding is more defensible than restructuring the index around it. The dimensionality analysis is therefore diagnostic and reported, not a trigger.

**Why not replace Decomposability entirely.** See Section 5.21 for the specific proposal (Exception Sensitivity) that was considered as a replacement and rejected.

### 5.21 Why Exception Sensitivity / Error Tolerance Was Considered and Not Adopted

> **Partially superseded (03 June 2026):** The v3 Capability Match "reliability bar" described at the end of this entry — "production proficiency = no per-instance re-checking" — was the source of a calibration failure (Capability Match never scored 2 in the first pilot) and was recalibrated to a *human-equivalent* bar in v3.1. See Sections 5.23 and 3.2. The decision *not* to adopt Exception Sensitivity as a separate criterion still stands.

The criterion-overlap review proposed replacing Decomposability with a new criterion, **Exception Sensitivity** (or Error Tolerance): *"Can the task tolerate occasional AI errors without requiring continuous expert human oversight or creating disproportionate downstream harm?"* The argument for it is genuinely strong: firms automate not purely on capability but on error cost, oversight burden, and recoverability, and Exception Sensitivity captures real adoption asymmetries (coding assistance and marketing copy move fast because errors are cheap and reversible; medicine and aviation move slowly despite capability because errors are catastrophic).

The proposal was considered seriously and not adopted for this index, for three independent reasons.

1. **It reverses a documented scope decision.** Section 5.8 records that institutional friction / cost of error was deliberately excluded as a criterion because it varies by country, industry, time period, and individual employer and cannot be operationalised reliably at the task level. Exception Sensitivity has exactly this problem: the same O*NET task ("draft legal documents") has wildly different error tolerance for a template NDA versus a merger agreement, and that context is not in the task statement. It is the institutional-friction concern re-entering through a different door.

2. **It changes the construct and breaks comparability.** This index measures technical substitutability, the same broad construct as Eloundou, Felten, Webb, and Anthropic. The entire convergent / discriminant validation hierarchy (Tiers 3–6) depends on measuring the same construct so the correlations are interpretable. Folding adoption-readiness into the index would make it no longer comparable to Eloundou at Tier 3, undermining the validation strategy.

3. **It partly double-counts with Capability Match.** Our Capability Match criterion already references "production settings where errors have real consequences." The strongest example offered for Exception Sensitivity — "AI drafts contracts well but errors are catastrophic" — under our rubric scores Capability Match 1, not 2, precisely because output that needs a lawyer to check every line is not at production proficiency. A separate Exception Sensitivity criterion would overlap with Capability Match on this axis.

**What was done instead.** The legitimate signal the reviewer identified — that task-intrinsic error tolerance was underweighted — was absorbed into Capability Match by sharpening its definition: "production proficiency" now explicitly means reliable enough to use without per-instance human re-checking (Section 3.2, v3). The task-intrinsic component of error tolerance therefore has a clear home; the context-dependent component remains out of scope.

**Where Exception Sensitivity belongs.** It is an excellent basis for a *complementary* index measuring adoption-likelihood or displacement-risk, distinct from technical exposure. This is noted as a future-research direction: a displacement-risk index would combine this project's technical-exposure scores with an error-tolerance / oversight-burden layer to predict actual labour-market displacement, which technical exposure alone does not.

### 5.22 Why Scoring Switched from the Batch API to the Synchronous API

The entire scoring pipeline was originally designed around the OpenAI **Batch API**, chosen for its 50% cost discount and asynchronous convenience — appropriate, in principle, for a one-shot job of 18,796 requests. When the funding professor created the API account and shared the key (03 June 2026), an inspection of the account's actual rate limits revealed that the original design could not run on it.

**The problem.** OpenAI gates API usage by **usage tier**, and a newly created account is **Tier 1**. The Batch API is limited not only by file size (200 MB) but by an **enqueued-token limit** — the maximum number of input tokens that can sit in the batch queue at once. For gpt-4o on Tier 1, that limit is **90,000 tokens**. Our figures:

- Full run: 18,796 tasks × ~2,036 input tokens ≈ **38,300,000 enqueued tokens** — about **425× over** the 90,000 limit.
- Even the 75-task pilot (~153,000 tokens) **exceeds** the limit.

Batch is therefore unusable on this account. The only way to use Batch at Tier 1 would be to split the corpus into ~44-task micro-batches and submit ~430 of them sequentially (each waiting for the previous to complete and release its enqueued tokens). With Batch's up-to-24-hour SLA per job, this is operationally infeasible, and if the 90,000 figure is interpreted as a daily cap rather than an at-once cap, Batch is dead entirely.

**Why not wait for a higher tier.** Tier 1 → Tier 2 requires $50 cumulative spend **and** 7 days since account creation, after which the Batch limit rises substantially. But reaching $50 of spend requires running roughly half the corpus at full price first, so the Batch discount could only ever apply to the remainder — a saving of roughly $9 for a week's delay and considerable added complexity. Not worth it.

**The decision: synchronous Chat Completions API.** The synchronous (non-batch) endpoint is governed by the per-minute rate limits (30,000 TPM, 500 RPM on Tier 1), not the Batch enqueued-token queue. Pacing requests under 30,000 TPM, the script processes ~10 tasks/minute, completing the full run in roughly **28–31 hours of run-time**, made resumable across sessions by per-task checkpointing. This runs on the Tier 1 account immediately, with no waiting.

**The cost trade-off, accepted.** Synchronous pricing is double Batch pricing (no 50% discount), which would raise the full-run estimate from ~£53 to ~£105 at face value. However, the system prompt (~1,983 tokens) is identical on every request, so OpenAI's automatic **prompt caching** discounts ~97% of input tokens by 50%, pulling the realistic estimate down to **~£69 (≈ $87)**, with a worst case of ~£105 if caching underperforms. A fixed `prompt_cache_key` is set on every request to maximise the cache hit rate. The funding professor was informed of the approach change and the higher cost ceiling and accepted it before any spend.

**What changed and what did not.** Only the *execution layer* changed: paced synchronous requests, exponential backoff on rate-limit and transient errors, per-task checkpoint/resume, a cost safety cap, and a fixed `seed`. The rubric prompt, the response schema, the hard-gate aggregation, the validation strategy, and every methodological decision are **unchanged**. The same single script (`src/03_score_tasks.py`) is used identically for the smoke test, the pilot, and the full run — the "pilot = final" rule is preserved.

**Reproducibility note.** Switching from Batch to synchronous does not affect reproducibility claims: the model version, temperature, seed, prompt, and schema are all still fixed and recorded. If anything, adding a fixed `seed` (which the Batch design had not specified) marginally strengthens determinism.

### 5.23 Why the Four Criteria Were Redesigned (v3 → v3.1) After the First Pilot

The first real pilot — 75 tasks scored by gpt-4o-2024-11-20 on 03 June 2026 — was the moment the rubric met data, and it revealed that the v3 criteria did not work. This entry records the evidence and the redesign, because a reviewer will rightly ask how we know the new criteria are better than the old.

**The evidence of failure.** Three findings, all from the pilot:

1. **The index collapsed to three values.** Across 75 tasks the composite took only the values 0.000 (37 tasks), 0.750 (1 task), and 0.875 (37 tasks). *Every* digital task scored the identical 0.875. An index that produces essentially two values is a binary physical/digital classifier, not a graded exposure measure.

2. **Three of the four criteria were measuring the same thing.** Spearman correlations among the criterion scores were 0.95–0.99 between Information Sufficiency, Output Verifiability, and Capability Match. Reading the model's own reasoning showed why: Output Verifiability was scored on whether the *output was a digital file or a physical object* ("the output is a digital artifact... verifiable"; "the cut material requires physical inspection"), which is the same physical-vs-digital axis as Information Sufficiency. The criteria were redundant by construction.

3. **Decomposability did no independent work, and Capability Match was mis-calibrated.** Of the 15 tasks where Decomposability scored below 2, *all 15 were physical* (Information Sufficiency = 0) — i.e. Decomposability only varied where another criterion already gated, and was a constant 2 on every digital task. Its reasoning conflated "decompose into sub-steps" with "decompose into *digital* sub-steps," so it too was secretly measuring physicality. Separately, Capability Match scored 1 on every one of the 38 digital tasks and **never once scored 2** in 75 tasks — because the v3 bar ("reliable enough to use without per-instance human re-checking") is a perfection standard no task and no human meets, so the model always found a "nuance" reason to withhold the 2.

**The diagnosis.** The four criteria were not orthogonal: Information Sufficiency, Output Verifiability, and Decomposability all collapsed onto a single "physical vs. digital" axis, and Capability Match was pinned at 1 for all cognitive work. The construct, not the calibration alone, was broken — and the cause was wording that let the model re-derive "physical vs. digital" inside criteria that were meant to measure something else.

**The redesign (v3.1).** Each criterion was rebuilt to capture a *distinct, literature-grounded* barrier (the full justification, with the reason each citation was chosen, is in Section 3.2):

- **Information Sufficiency** — kept (it worked: all physical tasks gated correctly). It is now explicitly named as the *only* criterion that judges physical vs. digital.
- **Output Verifiability → Objective Verifiability** — redefined from "is the output a digital file" to "does the task have an objective, checkable standard of success vs. subjective judgement" (Brynjolfsson, Mitchell & Rock 2018; Frey & Osborne's creative-intelligence bottleneck). This decouples it from physicality — a digital output can be subjective — and gives it independent signal that varies among digital tasks.
- **Decomposability → Contextual Independence** — replaced. The replacement captures the social and tacit-knowledge barrier (Frey & Osborne's social-intelligence bottleneck; Deming 2017; Autor 2015 / Polanyi's Paradox) — the single biggest real-world reason digital, capable, well-defined cognitive jobs resist automation, which the old rubric missed entirely.
- **Capability Match** — recalibrated from the impossible "no per-instance re-checking" bar to a **human-equivalent** bar ("at or above average-human quality, needing no more review than a human's work normally gets"), so the top of the scale becomes reachable again.

**Wording safeguards against re-collapse.** Two design features address the root cause directly: (a) each criterion now states explicitly *what it is NOT about*, naming the criterion that owns that axis, to stop cross-criterion leakage; (b) the anchors carry minimal, domain-diverse, deliberately *pattern-breaking* examples (e.g., "an inspiring mission statement is digital yet subjective → Objective Verifiability 0") governed by an anti-anchoring instruction (Suri et al. 2024), so the examples teach the construct boundary rather than a surface pattern.

**This reverses two earlier decisions.** Section 5.20 (decoupling Decomposability as a "pure structure" criterion and holding it as a fixed fourth criterion) and the relevant part of Section 5.21 (the v3 Capability Match reliability bar) are **superseded** by this entry. We followed the evidence: Decomposability was held as fixed on the expectation that it carried independent signal; the pilot showed it does not, so it was replaced. This is the pilot performing exactly its intended function — surfacing a design failure for ~£0.39 before the ~£75 full run.

### 5.24 Why the Aggregation Changed to Design Y (Gate-on-Impossibility, Modulate-on-Quality)

The criterion redesign (5.23) was paired with an aggregation change, because the two are coupled. Under the old "any criterion = 0 → composite 0" rule, the redesigned Objective Verifiability and Contextual Independence — which legitimately score 0 for subjective and relationship-dependent tasks — would have gated those tasks to zero, lumping "subjective digital judgement" and "relationship-dependent work" together with "physically impossible," and re-flattening the index.

**Design Y** resolves this by distinguishing two kinds of criterion:
- **Gates (categorical inability):** Information Sufficiency and Capability Match. Can GenAI attempt the task at all? No if it is physical (disembodied model) or beyond current capability. These zero the composite.
- **Modulators (quality of substitution):** Objective Verifiability and Contextual Independence. *Given* the model can attempt the task, how cleanly does it substitute? These scale the score down (via the mean) without zeroing it.

This was discussed as an option when the aggregation alternatives were first weighed (Section 5.5), where *hierarchical gating* was rejected as "arbitrary — choosing which criteria gate is itself a judgement call." That objection is now answered on principled grounds: the gating criteria are exactly the ones representing an *absolute impossibility for the technology* (no body, insufficient capability), whereas the modulating criteria represent a *reduction in the completeness or trustworthiness of substitution*. The split is therefore derived from the nature of each barrier, not chosen for convenience. Section 5.5's rejection of hierarchical gating is **superseded** for this reason, and the empirical motivation (the v3 collapse) is recorded in 5.23.

The gradient Design Y produces is documented in Section 3.2 and was the explicit goal: subjective-but-capable digital tasks land around 0.75, subjective-and-relational around 0.375, fully-substitutable at 1.0, physical or beyond-capability at 0 — a meaningful spread rather than three values. Whether this holds on real data is exactly what the re-pilot tests.

### 5.25 Why Criterion 3 Was Refined Again (v3.1 → v3.2): A Single, Minimal Wording Change

The v3.1 re-pilot (04 June 2026) was a clear success — the index produced a seven-value composite gradient (0, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0), Capability Match reached 2 for the first time (8 of 75 tasks), Objective Verifiability fully decoupled from the physical/digital axis (correlations −0.16 to 0.29), and subjective and relational digital tasks correctly landed in the middle band instead of gating. Three of the four criteria were working as designed.

**The one problem, found by reading the reasoning.** Contextual Independence was over-applied. The criterion was meant to fire only for **real-time human interaction** or **genuinely tacit knowledge that cannot be written down**, but the model was docking a point (scoring 1 instead of 2) whenever a task touched *any* organisation-specific context — even documentable context that could simply be supplied. The clearest evidence: the task "Write supporting code for Web applications" scored Contextual Independence = 1 with the reasoning *"much of the task can be completed with general programming knowledge and the task description"* — reasoning that argues for a 2, then scores 1. Several routine tasks ("code documents according to company procedures," "review and update credit and loan files," "arrange insurance coverage") were docked for needing "specific company procedures/policies," which are documents that can be provided, not tacit knowledge that cannot. The effect was a systematic mild **under-scoring of routine digital cognitive work** — precisely the category most exposed to Generative AI, so the wrong direction of error for an exposure index.

**Why a minimal change, not a rewrite.** The criterion's construct (Polanyi's tacit-knowledge / social-interaction barrier) was correct; only its *boundary* was being read too broadly. A large rewrite risked introducing new failure modes for no benefit. The fix is therefore one clarifying sentence — *"Context that could be written down and supplied (procedures, specifications, files, policies, client requirements) does NOT count as a barrier, because it can be provided to the model; only real-time human interaction or genuinely tacit/undocumented knowledge does"* — plus a sharpened score-2 anchor ("coding to a documented company style guide → 2"). The question stem, both "NOT about…" guards, and anchors 0 and 1 are unchanged. This is faithful to the original construct: the barrier was always *tacit* knowledge, and this simply stops the model from treating merely *specific* (but documentable) knowledge as tacit.

**Scope of the change.** Criteria 1, 2, and 4, the schema field names, and the scoring code are byte-for-byte unchanged. The re-pilot should therefore move only Criterion 3 (expected: ~10–15 routine digital tasks rise from Contextual Independence 1 → 2, lifting their composites from ~0.625–0.75 to ~0.75–0.875), while genuinely relational tasks (live negotiation, counselling, client-facing work) stay at 0. This isolation is verified cheaply *without a second run*: because criteria 1, 2, and 4 have identical wording to v3.1, their scores in the v3.2 run are compared directly against the archived v3.1 scores — if they are unchanged, the model is stable and the edit is confirmed isolated to Criterion 3 in a single comparison (see Implementation Log 9.7 for the result).

### 5.26 v3.2 Re-Pilot Outcome and the Temperature-0 Reproducibility Check (04 June 2026)

The v3.2 re-pilot (75 tasks, single run, $0.39) passed all three pre-registered checks. The composite distribution stayed healthy and near-identical to v3.1 — seven distinct values (0, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0), mean 0.395 (v3.1: 0.373), buckets ordered correctly (A_expected_high mean 0.825 all PASS; B_expected_low all gated at 0; C_ambiguous split 11 PASS / 9 gated; D_mixed 6/9).

**Check 1 — Criterion 3 moved as predicted.** Contextual Independence changed on 17 of 75 tasks: 13 rose, 4 fell. The 13 that rose are exactly the documentable-context tasks the fix targeted — "Write supporting code for Web applications" (1→2), "code documents according to company procedures" (1→2), "review and update credit and loan files" (1→2), "arrange insurance coverage" (1→2), "review or draft risk disclosures" (1→2), plus Software Developers and Biostatisticians review tasks. Where it counts — among PASS tasks, the only place Contextual Independence enters the composite — the score-2 count rose from 15 to 24 and score-1 fell from 18 to 11, with Information Sufficiency held constant at 2: the intended upward re-rating of routine digital cognitive work, and proof the criterion still varies independently rather than collapsing onto Information Sufficiency. Thirteen composites rose into the 0.75–1.0 band.

**Check 2 — the three unchanged criteria, and the temperature-0 reproducibility floor.** Criteria 1, 2, and 4 have byte-identical wording in v3.1 and v3.2, so their scores were compared directly against the archived v3.1 run. Information Sufficiency: **0 of 75** changed. Objective Verifiability: 4 of 75. Capability Match: 2 of 75. In total **6 of 225 unchanged-criterion scores (2.7%) differed** — all by ±1 except one, and crucially **bidirectional** (two up / two down on Objective Verifiability; one up / one down on Capability Match). A systematic ripple from editing the surrounding prompt would push one direction; scattered ±1 movement is the signature of stochastic noise, not contamination. The **gate set was identical** — 75/75 tasks held the same PASS/GATED status (both 37 PASS / 38 GATED), so no drift crossed a gate boundary. Net composite effect was negligible and partly self-cancelling (e.g. Financial Risk Specialists: Objective Verifiability −1 offset Contextual Independence +1, composite unchanged). This 2.7% is therefore an **upper bound on the temperature-0 reproducibility floor** (it also absorbs any edit ripple): even at `temperature = 0` with a fixed `seed`, the OpenAI API does not guarantee bit-exact output because the server-side `system_fingerprint` can change between calls. A ~2–3% per-criterion flip rate, ±1, with a stable distribution and a stable gate set, is the expected and acceptable reproducibility profile for an LLM judge — recorded as a known bound (Section 6), not a defect.

**Check 3 — the relational floor held.** Of the genuinely interpersonal tasks scored 0 in v3.1 (patient care, client-facing real-estate work, teaching sensory-impaired students), **8 of 8 held at Contextual Independence = 0**. The four v3.1 zero-scores that moved up were all **non-relational review/retrieval** tasks that had been over-gated — peer review ("review papers or serve on editorial boards," 0→1), film review (0→2), microfilm document retrieval (0→1), transportation-impact analysis (0→1). These are corrections in the intended direction, not erosion of the relational barrier.

**One harmless artifact, recorded not fixed.** On three *gated* physical construction tasks (painters, cabinetmakers, carpenters), v3.2 reads Contextual Independence as 0 with the reasoning "requires physical presence" — leaking Criterion 1's physical/digital axis into Criterion 3. Because these tasks are already gated by Information Sufficiency = 0 (and Capability Match = 0), **their Contextual Independence score never enters the composite; the effect on the index is exactly zero.** Its only visible trace is a mechanically inflated *full-sample* Contextual-Independence ↔ Information-Sufficiency correlation (0.54 → 0.71): gated tasks now pile up at 0 on both criteria. This is why inter-criterion correlations are reported on the **PASS subset**, where Contextual Independence varies independently (0/1/2 = 2/11/24). Fixing the conflation would require a further Criterion-3 edit and another re-pilot for no change to any score; it is documented and left in place. The same gate-structure effect inflates the full-sample Information-Sufficiency ↔ Capability-Match correlation (0.96), already established (Decision 04-Jun) as a genuine one-directional property (Information Sufficiency = 0 ⟹ Capability Match = 0; the converse does not hold).

**Verdict.** v3.2 passes on dimensionality (all four criteria use their full range), gradient (seven composite values), correct ordering (buckets and relational/physical floors), and isolation/reproducibility (unchanged criteria stable to within the temperature-0 floor; gate set identical). **Prompt v3.2 is locked for the full production run (18,796 tasks).** No further rubric changes are planned; any future change would restart the pilot.

### 5.27 Why the Tier 2 Validity Sample Was Changed from Stratified to Simple Random (06 June 2026)

The Tier 2 human-validity sample (Section 3.4) was originally specified as a stratified random sample — 25 tasks from each of four LLM-composite-score bands (Section 5.19). On reviewing the plan before the validation run, the funding supervisor recommended a **simple random sample** instead, and the researcher agreed. The change is adopted; it affects only how the 100 validation tasks are drawn, not the rubric, the scoring, or any threshold.

**Why simple random is preferred here.**
- **Population-representativeness.** A simple random sample gives a κ that estimates human–model agreement on a *typical* task drawn from the corpus's actual score distribution. That is the quantity a reader most naturally wants from a validity check ("how often does the model agree with humans on a real task?"). A stratified κ, by contrast, is computed over a deliberately re-balanced distribution and must be re-weighted before it can be read at the population level.
- **Fewer researcher degrees of freedom.** Random sampling makes no analyst choices about strata boundaries or per-stratum counts. There is therefore no way to argue that the sample was constructed (consciously or not) to produce a favourable κ. For a validity claim, that credibility matters more than the within-region precision stratification buys.
- **Simplicity and reproducibility.** "100 tasks drawn at random with a fixed seed" is immediately understandable and exactly reproducible. Because the run input is the shuffled master file, the draw is trivial (a seeded random subset of the completed tasks).

**The trade-off, and how it is handled (not by re-stratifying).** A simple random sample under-covers sparse score regions (e.g. the thin mid band), so per-region confidence intervals are wider; and because roughly 40–50% of the corpus gates to composite 0, that single category is prevalent, which can *depress* Cohen's κ even when raw agreement is high (the well-documented prevalence/kappa paradox). This is exactly the concern Section 5.19 raised in favour of stratification. Rather than re-balance the sample, it is addressed at the reporting stage: alongside κ we report (a) raw percent agreement and the full confusion matrix, (b) κ per criterion (each criterion has a different category balance) as well as on the composite, and (c) the sample's composite-score distribution, so κ is interpreted in the light of category prevalence. Krippendorff's α among the three human raters is unaffected by this. The pre-locked headline threshold (κ ≥ 0.60) is retained. Supersedes the sampling choice in Section 5.19.

---

## 6. Known Methodological Limitations

This section documents limitations that are inherent to the research design and cannot be resolved with available data. These are not flaws — they are constraints shared by the entire task-based exposure literature and our specific design.

### 6.1 Task Bundling and Interdependence

The exposure index treats each O*NET task statement as an independent unit of analysis. An occupation's overall exposure score is computed as an importance-weighted mean of its individual task scores, as if each task could in principle be substituted independently of all others.

This assumption is methodologically convenient but economically simplified. Occupations are not lists of independent tasks — they are bundles of interdependent activities. A paralegal's task *"research relevant case law"* and task *"summarise findings for the supervising attorney"* are not independent: the output of the first is the direct input of the second.

**Why this matters:** If tasks cluster into co-dependent bundles, additive aggregation may overstate or understate occupation-level exposure.

**What the literature does:** No published task-based exposure paper applies any correction for task interdependence. Felten et al. (2021), Eloundou et al. (2023), Pew (2023), Webb (2020), and Anthropic (2025) all use additive aggregation. Autor (2013) acknowledges this limitation but argues the task-based approach remains the best available tool.

**How handled:** Documented here and in the paper. No correction applied. The index measures the extent to which an occupation's constituent task text overlaps with Foundation Model capabilities, not whether the occupation will be fully substituted as a whole.

**Source:** Autor, D. (2013). The "task approach" to labor markets: an overview. *Journal for Labour Market Research*, 46(3), 185–199.

### 6.2 Substitution-Only, Foundation-Model-Only Scope

The exposure index measures direct Foundation Model substitutability and does not measure: AI augmentation or assistability, exposure to physical AI / robotics / autonomous systems, or labour market displacement probability.

**Implication:** The index is bounded in three ways simultaneously. The total economic effect of AI on occupations is broader than what this index captures. Tasks where Foundation Models substantially help a human worker but cannot replace them score 0 in our index even though they are economically affected. Robotic and physical AI deployments are entirely out of scope. Institutional friction (Section 3.3) is out of scope.

**Why this is acceptable:** The scope choices produce cleaner construct validity for the vulnerability framework and a more interpretable result. The bounds are explicit and consistent with the field's framing of Generative AI as a distinct technological phenomenon.

### 6.3 Training Cutoff Bounds the "Current Foundation Model Capability" Criterion

Criterion 4 of the rubric asks the LLM to evaluate whether current Foundation Models can perform the task. The evaluating LLM (GPT-4o) has a training cutoff. It does not directly know about Foundation Model capabilities developed after that cutoff.

**Implication:** The exposure index measures Foundation Model capabilities as of the evaluating model's training cutoff, not as of the calendar date of scoring.

**Mitigation:** Use the most recent available model version. Document the model and cutoff explicitly. Note that subsequent advances may have moved certain tasks across capability thresholds the model was unaware of.

**Source:** Documented in the broader LLM literature (NAACL 2025, arXiv 2504.00042: "Beyond the Reported Cutoff: Where Large Language Models Fall Short").

### 6.4 Model-Evaluator Dependence

NBER Working Paper 35110 (2025) documented that running the same exposure rubric through different frontier LLMs produces dramatically different results: 3.6× divergence in mean exposure scores across Claude, ChatGPT-5, Gemini, and GPT-4 on identical tasks; agreement on individual task classifications as low as 57%. The authors conclude: *"the scores are not fixed properties of occupations but joint products of the occupation and the model."*

**Implication:** Any single-LLM exposure index is partly a measurement of the LLM, not just of the underlying occupational content.

**Mitigation:** Multi-LLM reliability check (Section 3.4, Tier 1). Reporting empirical reliability bounds is more than the existing literature provides. This is a lower bound, not a complete solution — both GPT-4o and Claude 3.5 Sonnet share RLHF training and architectural assumptions, so agreement between them does not rule out shared bias.

The framing in the paper: we report empirical reliability bounds across two evaluators, which is more than the existing literature provides; we do not claim to have solved model-evaluator dependence.

### 6.5 Implementation Context Ambiguity and the Physical/Digital Boundary

O*NET task statements often do not specify implementation context. Under Design Y (Section 3.2) this matters most for **Criterion 1 (Information Sufficiency)**, because IS = 0 is one of the two gates: a task read under a physical interpretation gates the composite to 0, while the same task read under a digital interpretation can score anywhere up to 1. The disambiguation instruction ("when a task could plausibly be performed using digital tools in a contemporary workplace, evaluate it under that digital implementation") is the primary control.

**Pilot evidence (v3.2, 75 tasks).** Information Sufficiency was scored *binary* — 38 tasks at 0, 37 at 2, and **zero at 1**. The model resolves the physical/digital boundary decisively rather than hedging: a task is treated either as physically embodied (IS = 0, gated) or as digitally completable (IS = 2). All 38 IS = 0 tasks also scored Capability Match = 0 (the IS = 0 ⟹ CM = 0 property, Section 5.26), so physical tasks are reliably double-gated.

**The physical-presence leakage, and why it is contained.** Reading the reasoning shows the model frequently invokes physical-presence language ("requires physical presence / manual operation") not only in Criterion 1 but also in Criterion 3 (Contextual Independence — 28 of 75 tasks) and Criterion 4's failure field (36 of 75) — even though the prompt explicitly instructs that "the other three [criteria] assume the task is digitally accessible … do not re-judge physicality in them." This is genuine instruction leakage. In the pilot it is **harmless**: every task where physical-presence language appears in a non-gate criterion is already gated by IS = 0 (0 of 37 PASS tasks contain such language in Objective Verifiability or Contextual Independence; 0 contradictions where IS = 2 yet the model claims physical presence). The gate makes the leaked judgement irrelevant to the composite.

**Residual concern for the full run.** The leakage is contained *only because IS is binary in the pilot*. The danger zone is **IS = 1** — a genuinely hybrid task ("inspect a site and file a digital report," telehealth triage, sample collection plus digital analysis) that does *not* gate on IS. If the full corpus produces IS = 1 tasks and the physical penalty also bleeds into Contextual Independence (→ 0) and Capability Match, the physical nature is counted two or three times, depressing those composites below what the single-criterion design intends. The direction of this error is **conservative** — it understates exposure on hybrid tasks, never overstates it — and IS = 1 tasks are expected to be a small minority, so the occupation-level impact should be limited. It is monitored directly: the post-scoring audit (Section 3.10) carries a **physicality double-count check** — for every IS = 1 task, flag any case where Contextual Independence or Objective Verifiability reasoning invokes physical presence, count them, and report the composite sensitivity of reassigning the leaked criterion to its "digitally-accessible" value. Because the prompt is locked (Section 5.26), this is a reported post-hoc diagnostic, not a further prompt edit.

**Irreducible residue:** some tasks are genuinely ambiguous in ways prompt engineering cannot resolve; these contribute irreducible noise.

### 6.6 Inter-Criterion Correlation and Binding-Constraint Informativeness

The binding-constraint decomposition (Output C) depends on how strongly the four criteria correlate across the corpus. This was first flagged before scoring; the pilots now give empirical estimates that supersede the earlier expectation (which was framed around the v3.0 criteria *Decomposability* and *Output Verifiability*, both replaced in the v3.1 redesign — Section 5.23). The current four criteria are Information Sufficiency, Objective Verifiability, Contextual Independence, and Capability Match.

**What the pilot shows (v3.2, 75 tasks, full-sample Spearman).** Information Sufficiency ↔ Capability Match = 0.96; Information Sufficiency ↔ Contextual Independence = 0.71; Contextual Independence ↔ Capability Match = 0.73; Objective Verifiability is largely independent of all three (−0.12 to 0.25).

**Two of these correlations are structural, not redundancy.** (1) The IS ↔ CM 0.96 is a genuine *one-directional* property: IS = 0 ⟹ CM = 0 (a task the model cannot access, it cannot produce), but IS = 2 ⇏ CM = 2 (a digital task can still exceed current capability). This yields a clean factor structure — one "can-the-model-attempt-it" gate factor plus independent quality dimensions — and is reported as a property, not corrected (Section 5.26). (2) The IS ↔ CtxI 0.71 is partly an *artefact of the gate structure*: gated tasks sit at 0 on several criteria at once (mean 2.95 of four criteria are 0 on a gated task), and on physical tasks the model additionally mis-scores Contextual Independence as 0 for physical-presence reasons (Section 6.5). Both effects inflate the *full-sample* correlation without implying the criteria are redundant where it matters.

**Reporting decision.** Because the gate mechanically inflates full-sample inter-criterion correlation, the criterion-separability analysis (Output D, Section 3.6 — correlation matrix, PCA / factor analysis, gate-attribution stability, per-criterion inter-rater disagreement) is reported on the **PASS subset**, the tasks where the criteria actually modulate the composite. There, with Information Sufficiency fixed at 2, Contextual Independence still varies across 0/1/2 (pilot: 2/11/24) and Objective Verifiability remains independent — confirming the criteria are not collapsing onto one axis (the failure mode that killed v3.0, Section 5.23). Where a correlation remains high, the binding-constraint decomposition is framed as "constraint pressure" rather than a clean causal attribution. The four-criterion structure is held fixed regardless of the result; the analysis is diagnostic, not a model-selection trigger.

### 6.7 Within-Occupation Dispersion Is Noisy for Small-Task Occupations

Minimum tasks per occupation is 4. For occupations with 4 to 6 tasks, IM-weighted standard deviation estimates are statistically noisy and are flagged in supplementary tables.

### 6.8 Multi-LLM Reliability Is a Lower Bound, Not a Validity Guarantee

Both GPT-4o and Claude 3.5 Sonnet are RLHF-trained frontier transformer-based LLMs. They share architectural assumptions, training paradigms, and substantial pre-training data. Agreement between them is necessary but not sufficient evidence of measurement validity.

**Mitigation:** The Webb (2020) discriminant validity check and the Eloundou convergent validity check together triangulate. The honest framing: inter-LLM reliability is reliability across two state-of-the-art evaluators, not a guarantee of validity.

### 6.9 No External Objective Ground Truth Exists for Generative AI Exposure

Every comparator in the validation hierarchy — Eloundou, Anthropic, Brynjolfsson SML, Webb, the human ratings — is itself a constructed measure of exposure, not an independent ground truth. We are validating our construction against other constructions. A reviewer could legitimately argue this is partly circular: there is no objective measurement of "true" Generative AI exposure that any of these measures is approximating.

This is the field's situation, not unique to our project. Eloundou et al. (2023) validated their rubric against human expert ratings, but those ratings themselves were judgements about an inherently abstract construct. Webb (2020) validated against historical employment outcomes, which is the closest the literature comes to objective grounding — but the outcomes lag the patents by years and the causal chain from technology to employment is contested.

**How handled:** Acknowledged here and in the paper's limitations section. The validation strategy mitigates the circularity concern by combining multiple comparators with methodologically diverse foundations: human task-level ratings (Tier 2), LLM rubric scoring (Tier 3–4), expert survey (Tier 5), and patent text analysis (Tier 6). Convergence across these methodologically diverse comparators is stronger evidence than agreement with any single comparator. We do not claim to have solved the ground-truth problem; we claim to have triangulated as far as available data permits.

### 6.10 Analyst-Task Imputation Introduces an Unverifiable Assumption

The within-occupation mean IM imputation for analyst-coded tasks (Section 3.2) is a neutral assumption — analyst-coded tasks are treated as of average importance to their occupation. This cannot be validated without incumbent survey data.

**Mitigation:** The robustness check (index recomputed without analyst-coded tasks) reports the sensitivity directly. If rankings move materially between the two versions, this is a finding worth investigating per occupation. If they do not move materially, the imputation assumption is empirically inconsequential.

The bias from imputation (treating non-average tasks as average) is bounded and symmetrical. The bias from exclusion (systematically dropping the most technologically current tasks) is unbounded and directional. The chosen approach has the smaller risk profile.

---

## 7. Pending Data Acquisition

Data not yet obtained. Required for Part 2 of the project. Listed for transparency, not as a Part 1 dependency.

| Data | Purpose | When needed |
|------|---------|-------------|
| U.S. PIAAC public-use microdata | Adaptation Capacity Index (ACI) | After exposure index (Part 1) is finalised and approved |
| ISCO-08 to SOC 2018 crosswalk (BLS) | Linking PIAAC respondents to O\*NET occupations | Same as above |
| BLS OEWS employment counts | Employment-weighted vulnerability statistics | After exposure and ACI are both complete |

Foundation Model capability descriptions (model cards, HELM, MMLU, HumanEval task descriptions) are not required for the LLM-as-judge methodology, which uses the LLM's own parametric knowledge of Foundation Model capabilities. They were listed in earlier drafts under the rejected semantic similarity approach.

---

## 8. Next Steps

The methodology is now fully specified. The remaining steps to produce the Generative AI Exposure Index are operational.

| Step | Description | Status |
|------|-------------|--------|
| Data preprocessing | Build master task file from Task Statements + Task Ratings (IM, RT) + Occupation Data + Occupation Level Metadata, per the schema in Section 3.7 | **Complete (10 May 2026)** — see Section 9.1 |
| Compute within-occupation mean IM | For each of the 923 occupations, compute the within-occupation mean IM across IM-rated tasks. Used to impute weights for analyst-coded tasks. | **Complete (10 May 2026)** — see Section 9.1 |
| Rubric prompt construction | Write the full LLM scoring prompt with disambiguation instruction and Foundation-Model-specific framing per Section 3.2 specifications | **Complete** — v1 (10 May), v2/v3 (criterion-overlap review), redesigned to v3.1 then refined to v3.2 after the pilots; see Sections 9.2–9.7. `src/rubric_prompt.py`. |
| Pilot test | Run the curated 75-task pilot per Section 3.8. Manual review. Revise prompt if any success criterion fails. Iterate until pilot passes. | **Complete (04 June 2026)** — three iterations (v3 → v3.1 → v3.2); v3.2 passed all checks. Sections 9.6–9.7, 5.23–5.26. |
| Lock prompt | Once pilot passes, freeze prompt text. All subsequent changes require a new pilot. | **Complete (04 June 2026)** — frozen at v3.2; any change re-triggers the pilot. |
| Full GPT-4o scoring run | Submit all 18,796 task statements via the OpenAI **synchronous** Chat Completions API (Section 5.22) at T = 0, fixed seed. Log every prompt and response. Resumable. | **Ready** — prompt locked; awaiting go-ahead. ~£73, ~28–31 h. |
| Claude 3.5 Sonnet reliability sample | Score stratified random sample of ~1,800 tasks using identical prompt. Log all responses. | Pending — after GPT-4o scoring complete |
| Post-scoring audit | Review all zero-gated tasks. Categorise as genuine impossibility or interpretation artefact per Section 3.10. | Pending — after full scoring |
| Reliability metrics | Compute Cohen's κ at criterion level, Krippendorff's α at criterion level, Spearman ρ at task and occupation levels, between GPT-4o and Claude scores. Apply Tier 1 pre-locked threshold (κ ≥ 0.70). | Pending — after audit |
| Human-LLM validity sample | Simple random sample of 100 tasks (fixed seed; Section 5.27) rated independently by researcher and both supervising professors. Compute κ between LLM and averaged human ratings; compute inter-human κ. Apply Tier 2 pre-locked threshold (κ ≥ 0.60). | Brought forward (06 June 2026) — drawn from the pre-run pool; see Implementation Log 9.8 |
| BERT embedding computation | Compute sentence-BERT embeddings for all 18,796 task statements using `all-mpnet-base-v2` and `all-MiniLM-L12-v2`. | Pending — independent of scoring; can run in parallel |
| BERT-based reproducibility analysis | Train regression to predict LLM composite from BERT embeddings (both models). Report R², RMSE, residual analysis per Section 3.5. | Pending — after both scoring and BERT embeddings complete |
| Aggregation and analytical outputs | Compute occupation-level exposure scores (with analyst-task IM imputation), within-occupation dispersion, binding constraint decomposition. Generate occupation-level summary file. | Pending — after audit |
| Robustness check (no analyst tasks) | Recompute the index without analyst-coded tasks. Compare rankings. Report material divergences. | Pending — alongside aggregation |
| External validation | Spearman ρ vs. Eloundou (Tier 3 convergent), Webb (Tier 6 discriminant). Apply pre-locked thresholds: ρ_Eloundou ≥ 0.55 and (ρ_Eloundou − ρ_Webb) ≥ 0.15. Report Brynjolfsson SML and Anthropic where data is available. | Pending — after aggregation |
| Distribution and case study review | Examine the score distribution. Manual review of top 15 and bottom 15 occupations. Mid-range spot checks. | Pending — after aggregation |
| Expert spot-check | Domain-expert review of 25–30 occupations spanning the range. | Pending — after distribution review |
| Part 1 deliverable | Validated Generative AI Exposure Index, occupation-level summary file, reliability report, BERT reproducibility analysis. Submit to supervising professors for review before Part 2 begins. | Pending |

Part 2 (Adaptation Capacity Index from PIAAC, and the Generative AI Vulnerability Framework) is not addressed in this document beyond the brief reference in Section 3.3. It will be planned separately once Part 1 is complete and reviewed.

---

## 9. Implementation Log

This section records what was actually executed, when, what was produced, and what was observed. It complements the Decisions Log (Section 4) and Decision History (Section 5): those record what was *decided*; this records what was *done*. New entries are appended as the project progresses.

### 9.1 Master File Construction (10 May 2026)

**Script:** `src/01_build_master_file.py`
**Output:** `data/processed/master_tasks.csv`, `data/processed/master_tasks_summary.txt`
**Inputs:** four O\*NET 30.2 Excel files from `data/raw/onet/` (Occupation Data, Task Statements, Task Ratings, Occupation Level Metadata).

**What was done.** The script merges the four input files into a single task-level master file with 16 columns following the Section 3.7 schema. It applies the IM-imputation rule from Section 3.2 (within-occupation mean for analyst-coded tasks; corpus-wide mean for the 29 fully-unrated occupations) and assigns the `weighting_mode` flag per occupation. Every operation is logged to `master_tasks_summary.txt` for the audit trail.

**What was produced.**

| Quantity | Value |
|---|---|
| Total task rows | 18,796 |
| Unique occupations | 923 |
| Unique task IDs | 18,796 (no duplicates) |
| Tasks with original IM rating (`im_weight_imputed = N`) | 17,951 |
| Tasks with imputed IM (`im_weight_imputed = Y`) | 845 |
| ↳ within-occupation mean imputation | 285 (across 57 mixed occupations) |
| ↳ corpus-wide mean fallback | 560 (across 29 fully-unrated occupations) |
| Tasks with `im_suppress = Y` (excluded at aggregation) | 6 |
| Tasks with `rt_suppress = Y` | 74 |
| Occupations with `weighting_mode = "IM-weighted"` | 894 |
| Occupations with `weighting_mode = "unweighted"` | 29 |
| Corpus-wide mean IM (excluding suppressed rows) | 3.9945 |
| Final IM weight range across all tasks | 1.4400 to 5.0000 |

**Sanity checks performed and passed.**
- All 18,796 tasks have non-null `im_weight` after imputation. No missing weights downstream.
- The 845 tasks with `task_type = "Unrated"` are exactly the 845 tasks with `domain_source = "Analyst"`. The two filters identify the same set.
- All tasks in the 29 unweighted occupations share the same imputed `im_weight = 3.9945` (the corpus-wide mean). Within those occupations, the IM-weighted mean is therefore mathematically identical to a simple unweighted mean — as documented in Section 3.2 and flagged in `weighting_mode`.
- Survey N range confirmed: 19 to 297 (median 63, mean ~65.7) across 878 occupations with metadata. Matches the literature review numbers in Section 1.8.
- Survey date range confirmed: 12/2004 to 08/2025 across 878 occupations. The corpus is concentrated in 2015–2025 (roughly 80% of metadata-bearing occupations); pre-2015 surveys are 12.5% of the metadata set. This matches the rolling-update behaviour documented in Section 2.1–2.2.

**Decisions that emerged during execution.**
- The `task_type` column for analyst-coded tasks was originally going to use the literal string `"None"`. During verification, we discovered that `"None"` is in pandas' default `na_values` list and gets silently converted back to NaN on CSV read. The sentinel was changed to `"Unrated"`, which survives the round-trip cleanly. Documented in Section 1.2 and the Decisions Log (10 May 2026 entry).
- The script's first version reported the `survey_date` range using string-sort order (which is wrong because `MM/YYYY` strings sort lexicographically). The script was updated to parse dates for log reporting only — the master file still stores `survey_date` as the native O\*NET `MM/YYYY` string, matching the Section 3.7 schema. Downstream code that needs date arithmetic should parse the column with `pd.to_datetime(col, format="%m/%Y")`.

**Implications for next steps.**
- The 29 fully-unrated occupations are now formally identifiable via `weighting_mode = "unweighted"`. The aggregation step (next pipeline stage) must filter or treat these separately when reporting per-occupation scores. They are kept in the headline index but flagged.
- The 6 IM-suppressed rows must be excluded before computing the IM-weighted mean. The `im_suppress = Y` filter is the canonical way to do this.
- The corpus-wide mean IM (3.9945) is recorded here so any future re-run produces an identical fallback value if the data has not changed. If a future O\*NET version changes the underlying IM distribution, this number will shift and should be re-computed.
- The master file is ready for the LLM rubric scoring pipeline. The next operational step is rubric prompt construction (per Section 3.2 and 3.8), followed by pilot test, then full GPT-4o scoring run.

### 9.2 Rubric Prompt Construction — Draft v2 (10 May 2026)

**File:** `src/rubric_prompt.py`
**Status:** Draft v2. Not yet pilot-tested. Awaits pilot per Section 3.8 before being locked for the production scoring run.
**Revision history:** v1 written and reviewed earlier on 10 May 2026; v2 written the same day after reviewer feedback identified five issues (documented in Section 5.16 of this document).

**What was done.** The full LLM scoring prompt is written as a Python module containing three parts: (a) `SYSTEM_PROMPT`, the static system message defining the role, scope, criteria, reasoning instructions, and output structure; (b) `RESPONSE_SCHEMA`, the JSON Schema definition passed to OpenAI's structured outputs feature; (c) `USER_MESSAGE_TEMPLATE`, the per-task message containing the task text and occupation title, formatted via `format_user_message()`. The module also documents the API call structure and failure protocol.

**What v2 changes relative to v1.** Five revisions, each addressing a documented issue:

1. **Per-criterion chain-of-thought reasoning.** The output schema now requires the model to articulate one-sentence reasoning before assigning each score. For Criteria 1, 2, and 3 there is one reasoning field per criterion. For Criterion 4 there are two (see #2 below). The reasoning fields appear *before* the score fields in the schema's required-fields list, forcing the model to commit to its reasoning before its integer score.

2. **Two-field balanced structure for Criterion 4.** Criterion 4 (Capability Match) is the criterion most susceptible to RLHF-induced self-assessment bias, since the model is being asked whether models like itself can perform the task. Rather than instructing the model to "first identify failure modes" — which would induce anchoring toward those listed failures — v2 uses two schema-required reasoning fields with neutral semantics: `capability_match_what_works` and `capability_match_what_might_fail`. The model brings its own task-specific reasoning to each. Schema enforcement is more reliable than instruction text. Backed by the cognitive bias literature on anchoring effects in LLMs (Suri et al. 2024) and broader cognitive biases in LLM evaluation (Echterhoff et al., Itzhak et al.).

3. **Disambiguation rule explicitly scoped to all four criteria.** v1 inadvertently narrowed the digital-implementation assumption to Information Sufficiency only. v2 states clearly that the assumption applies uniformly across all four criteria, preventing contradictory composite scores.

4. **Structured outputs with strict mode.** v2 uses OpenAI's `response_format: {"type": "json_schema", "strict": true, ...}` mode. The schema enforces: nine required fields, integer scores constrained to {0, 1, 2}, no additional properties allowed. Format-related parse failures are eliminated by API construction. The retry protocol in Section 3.2 still applies for non-format failures (refusals, network errors, rate limits), but in practice these are rare for occupational text.

5. **Negative formatting instructions removed.** v1 contained instructions like "do not wrap in code fences" and "do not produce any text before or after this JSON object." Under structured outputs in strict mode these are redundant and could occasionally confuse the model. v2 removes them.

**Output schema (the nine fields, in order).**

```
1. decomposability_reasoning            (string, ≤1 sentence)
2. decomposability_score                (integer ∈ {0, 1, 2})
3. information_sufficiency_reasoning    (string)
4. information_sufficiency_score        (integer)
5. output_verifiability_reasoning       (string)
6. output_verifiability_score           (integer)
7. capability_match_what_works          (string)
8. capability_match_what_might_fail     (string)
9. capability_match_score               (integer)
```

**Token and cost estimate (v2).**

| | |
|---|---|
| System prompt characters | 6,460 |
| System prompt tokens (estimate) | ~1,615 |
| User message tokens per task | ~53 |
| Total input per task | ~1,668 |
| Output tokens per task (CoT + 9 fields) | ~180 |
| Total input across 18,796 tasks | ~31.4M tokens |
| Total output across 18,796 tasks | ~3.4M tokens |

At GPT-4o Batch API pricing (~$1.25/M input, ~$5/M output, 50% batch discount applied):

- Primary GPT-4o run: ~$39 input + ~$17 output = **~$56 USD ≈ £44**
- Claude 3.5 Sonnet reliability sample (1,800 tasks): ~**$6 USD ≈ £5**
- **Total expected API spend: approximately £48–£52**, within the £60 envelope.

The cost increased modestly from v1 (~£37) to v2 (~£49) because the system prompt is longer (CoT instructions and Criterion 4 detail) and the output is longer (9 fields with reasoning instead of 4 integers). The increase is justified by the substantial methodological improvement; v2 is a more rigorous prompt by every measure that the literature flags as important for LLM-as-judge evaluation.

**Decisions encoded in the prompt (v2).**
- Occupation title IS included in the user message. Occupation description is NOT included (kept short to reduce token cost).
- Each criterion description follows the exact framing in Section 3.2 of this documentation.
- The prompt is self-contained: it specifies what is in scope, what is out of scope, the disambiguation rule, the rubric, the reasoning instructions, and points to the output structure (which is enforced by the schema).
- No few-shot calibration examples are included in v2. If the pilot reveals systematic miscalibration, anchored examples can be added in v3.

**What is required next before this prompt is used in production.**
- Pilot test per Section 3.8: 75 curated tasks scored by this v2 prompt. Manual review of all 75 results. The prompt is locked only after the pilot success criteria are met.
- The pilot itself requires API access (and therefore funding).

**Implications for next steps.**
- All work that does not require API access is now complete: the master file is built, the prompt v2 is drafted, the methodology and operational protocols are fully documented. The project state is a clean checkpoint.
- The next step that requires funding is the pilot test. The pilot's API cost is trivial (under £0.50 for 75 tasks at v2 lengths). The full scoring run is approximately £44–49.
- This is the natural pause point for funding decisions. The work resumes with the pilot test once funding is approved.

### 9.3 Methodology Refinement Following Supervisor Feedback (21 May 2026)

**Inputs:** Comments returned by Prof. Manoranjan Dash and Dr. Shreya Mukherjee after reading the project brief.
**Outputs:** Updated Sections 3.4, 4 (Decisions Log), 5.18, 5.19 of this document; updated `build_professor_brief.js`; new file `docs/rater_guide.md`.

**Two supervisor comments addressed.**

The supervisors returned two substantive comments after reading the project brief produced on 10 May 2026. Both were accepted and have been integrated into the methodology.

**Comment 1 — On the expert occupation-level spot-check.** The supervisors flagged that achieving an expert spot-check on 25–30 occupations would take a long time for what was always positioned as a supplementary face-validity tier. The decision was to drop this tier (the original Tier 7 of the validation hierarchy). The validation hierarchy is now six tiers, with Tier 2 (task-level human-LLM rating with quantitative κ) carrying the human-rating contribution. Documented in Decision History 5.18.

**Comment 2 — On sampling for the human validity check.** The supervisors raised the question of how the 100-task sample for Tier 2 should be selected — random or stratified — flagging the concern that without careful sampling, κ might fall short of the pre-locked 0.60 threshold for reasons unrelated to actual measurement validity. The decision was to lock a stratified sampling protocol: four strata of 25 tasks each, defined by LLM composite score quartile (0; (0, 0.5]; (0.5, 0.75]; (0.75, 1.0]). Stratification by LLM composite score is the variable that most directly affects how κ should be interpreted — ensuring the sample covers the boundary regions where human-LLM disagreement is most informative, rather than over-representing whichever score region happens to be most populous in the corpus. Alternative stratification variables (Domain Source, Task Type) are noted as available secondary sub-analyses. Documented in Decision History 5.19.

**Companion artefact: rater guide.** A one-document rater guide (`docs/rater_guide.md`) was produced on 11 May 2026 to accompany the validity sample. The guide defines the four criteria in plain language for the three human raters, restates the disambiguation rule, walks through four worked examples (clear high, clear low, ambiguous physical/digital, partial exposure with gating effect), and describes the rating procedure including time estimates. Without a shared rater reference, three raters interpreting a four-criterion rubric will produce three different interpretations and inter-human agreement collapses; the rater guide is the standard defence against this in inter-rater reliability work.

**Threshold not changed.** The supervisors mentioned a 0.75 κ figure in their comments; the locked threshold remains κ ≥ 0.60. The locked threshold is consistent with Landis & Koch (1977) "substantial agreement" and is the standard interpretation cut in inter-rater reliability work for ordinal rubrics. Raising to 0.75 ("near-perfect agreement") would risk an unattainable bar for a genuinely ambiguous task domain and could artificially flag the validity check as a failure. The threshold remains pre-locked and will be reported transparently; the actual κ value will be reported alongside it regardless of whether it crosses any specific bar.

**Implications for next steps.**
- The project's pre-funding state now includes all of: the master file, the rubric prompt v2, the documented methodology (including these refinements), the project brief for supervisors, the rater guide, and the source-of-truth living document.
- No further refinements are pending that do not require API access. The next operational step remains the pilot test, conditional on the funding decision discussed in the brief.

### 9.4 Rubric Refinement After Criterion-Overlap Review (23 May 2026)

**Inputs:** A detailed reviewer critique of criterion overlap, focused on the risk that the four rubric criteria would correlate in practice — most strongly Decomposability with Capability Match, secondarily Information Sufficiency with Output Verifiability — and that Decomposability was the weakest criterion. The critique also proposed replacing Decomposability with a new "Exception Sensitivity / Error Tolerance" criterion.
**Outputs:** rubric prompt v3 (`src/rubric_prompt.py`); updated rater guide (`docs/rater_guide.md`); new Output D (criterion dimensionality analysis) in Section 3.6; Decision History 5.20 and 5.21; updated Sections 3.2, 6.6; updated project brief; this log entry.

**Three changes accepted.**

1. **Decomposability reworded to decouple it from capability.** The critique correctly identified that the v2 definition referenced "sub-steps that a Foundation Model can execute," entangling the criterion with Capability Match by construction. v3 reframes it as a pure task-structure question. This is the single most important fix because the entanglement was definitional, not just statistical. (Section 5.20.)

2. **Criterion dimensionality analysis added (Output D).** Four diagnostics — correlation matrix, PCA / factor analysis, gate-attribution stability, per-criterion inter-rater disagreement — test whether the four criteria are empirically separable, reframed as the reportable question "which dimensions of AI substitutability are empirically separable?" This converts the overlap concern from a vulnerability into a finding. (Section 3.6 Output D.)

3. **Capability Match reliability bar sharpened.** The task-intrinsic component of error tolerance (which the critique correctly flagged as underweighted) is now explicit in Capability Match: "production proficiency" means reliable enough to use without per-instance human re-checking. (Section 3.2, Section 5.21.)

**One proposal rejected, with reasoning.** The critique's headline proposal — replace Decomposability with Exception Sensitivity — was considered seriously and not adopted. Exception Sensitivity reverses the documented scope decision to exclude institutional friction (Section 5.8), changes the construct in a way that breaks comparability with the literature the validation hierarchy depends on, and partly double-counts with the (now-sharpened) Capability Match. The task-intrinsic part of its concern was absorbed into Capability Match; the context-dependent part stays out of scope. Exception Sensitivity is recorded as an excellent basis for a complementary displacement-risk index in future research. (Section 5.21.)

**One decision made by explicit instruction.** Decomposability is held as a fixed fourth criterion. The dimensionality analysis is diagnostic and reported, not a trigger to collapse the model to three criteria. (Section 5.20.)

**Cost impact.** The v2→v3 criterion rewording lengthened the system prompt from ~1,615 to ~1,983 tokens, raising the estimated total API spend from ~£48–52 to ~£55–58. Still no budget threshold is imposed; the figure is recorded for transparency and will be measured precisely at the pilot.

**Implications for next steps.** The rubric is now at v3 and remains a draft pending the pilot test. No further pre-API refinements are outstanding. The operational sequence (pilot → full scoring → reliability sample → human validity sample → audit → aggregation → BERT → validation → deliverable) is unchanged.

### 9.5 Scoring Pipeline Rewritten for the Synchronous API (03 June 2026)

**Trigger:** The funding professor (Prof. Dash) created the OpenAI API account, funded it, and shared the key. On checking the account's actual rate limits before any spend, the account was found to be Usage Tier 1 with a Batch enqueued-token limit of 90,000 tokens — far below the ~38.3M-token full job. The Batch-based design could not run. (Full reasoning: Decision History 5.22.)

**What was done.**
- `src/03_score_tasks.py` was rewritten from a Batch-API orchestrator into a **synchronous** scorer: paced requests (default 6.0 s/request, ~10/min, ~88% of the 30,000 TPM limit), exponential backoff on 429/5xx/network errors, immediate-terminal handling of malformed-request (400) errors, the documented three-round content-retry protocol, per-task checkpoint/resume via a `progress_*.jsonl` file flushed with `os.fsync`, a configurable cost safety cap, and a fixed `seed`. A `prompt_cache_key` is set to maximise prompt-cache hit rate.
- The prompt (`rubric_prompt.py`), the response schema, the hard-gate aggregation, and the validation strategy were **not** changed. The same script is used for smoke / pilot / full run.

**Verification performed before any API spend.**
- Python syntax compiles cleanly.
- `openai` SDK installed (v2.40.0). All imported exception classes (`RateLimitError`, `APITimeoutError`, `APIConnectionError`, `InternalServerError`, `BadRequestError`, `APIError`) confirmed to exist in v2.40.
- `chat.completions.create` confirmed to accept every parameter used: `model`, `messages`, `temperature`, `seed`, `max_tokens`, `response_format`, `prompt_cache_key`. (`max_tokens` still valid for gpt-4o; the `max_completion_tokens` rename only affects the o1 family.)
- `RESPONSE_SCHEMA` confirmed well-formed: `json_schema` type, `strict: true`, 9 required fields, `additionalProperties: false`.
- All pure-logic functions unit-tested with mock data: `compute_composite` and `gating_criteria` (PASS/GATED cases, hard-gate behaviour, multi-criterion gating), `validate_parsed` (valid / missing-field / out-of-range-score), `estimate_cost` (cached/uncached split), and `load_checkpoint` (confirmed terminal failures are NOT skipped on resume — they are retried, while PASS/GATED are skipped).
- All three input CSVs (smoke, pilot, master) confirmed to contain the required `task_id` / `task_text` / `occupation_title` columns; pilot bucket-label columns confirmed to carry through to the scored output for the evaluation plan.

**What could NOT be tested without spend:** the live API round-trip itself (auth, real structured-output response, real prompt caching, real rate-limit behaviour). This is exactly what the 2-task pre-flight (`--limit 2`, ~£0.01) and the 10-task smoke test are for — they are the first real spend and validate the live path before the pilot.

**Cost position.** Estimated full-run cost rose from ~£53 (Batch) to ~£69 (synchronous, with prompt caching), worst case ~£105. Within the credit the professor loaded; he was informed and accepted the change.

**Implications for next steps.** The operational sequence is unchanged except that "Batch submission" becomes "paced synchronous run." Immediate next action: set `OPENAI_API_KEY`, run the 2-task pre-flight, then the 10-task smoke test, then the 75-task pilot, evaluate per the Pilot Test Evaluation Plan, lock or revise, then the full resumable run.

### 9.6 First Pilot, Failure Diagnosis, and the v3.1 Redesign (03 June 2026)

**What was run.** After the pre-flight (2 tasks) and smoke test (10 tasks) confirmed the synchronous pipeline works end-to-end at $0.05 total, the 75-task pilot was run with the v3 rubric: gpt-4o-2024-11-20, T=0, seed fixed, 75/75 scored, 0 failures, $0.39. Per-task cost ~$0.005, confirming the full-run estimate (~£75).

**What the pilot revealed (the v3 failure).** Evaluation against the Pilot Test Evaluation Plan surfaced a construct failure, not a pipeline failure:
- The composite took **only three values** (0.000 × 37, 0.750 × 1, 0.875 × 37). Every digital task scored an identical 0.875.
- **Inter-criterion Spearman correlations were 0.95–0.99** among Information Sufficiency, Output Verifiability, and Capability Match. Reading the model's reasoning showed all three were scoring "physical vs. digital": Output Verifiability keyed on whether the *output was a digital file*; Decomposability keyed on whether the task broke into *digital* sub-steps.
- **Decomposability did no independent work**: all 15 of its below-2 scores fell on physical tasks (already gated by Information Sufficiency); it was a constant 2 on all 60 digital tasks.
- **Capability Match never scored 2** in 75 tasks — the v3 "no per-instance re-checking" bar is a perfection standard the model always found a reason to withhold.

**The redesign (v3.1), run by the user and implemented this session.** Four criteria rebuilt as distinct, literature-grounded barriers (Decision History 5.23; Section 3.2): Information Sufficiency (kept), Output Verifiability → Objective Verifiability, Decomposability → Contextual Independence, Capability Match recalibrated to a human-equivalent bar. Aggregation changed to Design Y — gate on Information Sufficiency or Capability Match (categorical impossibility), modulate on Objective Verifiability and Contextual Independence (Decision History 5.24; Section 3.2). Wording safeguards added against re-collapse: each criterion names what it is NOT about; anchors use minimal, domain-diverse, pattern-breaking examples under an anti-anchoring instruction.

**Verification performed before any re-pilot spend.**
- `rubric_prompt.py` v3.1 loads cleanly; system prompt ~1,895 tokens (unchanged from v3, so cost is stable).
- Schema and scorer field names confirmed identical (9 required fields).
- `compute_composite` Design Y logic unit-tested against 8 mock cases: confirmed Information Sufficiency = 0 and Capability Match = 0 gate to 0; Objective Verifiability = 0 and Contextual Independence = 0 *modulate* (do not gate); the documented gradient (1.0 / 0.875 / 0.75 / 0.5 / 0.375 / 0) reproduces exactly.

**Files changed this session:** `src/rubric_prompt.py` (v3.1 prompt + renamed schema), `src/03_score_tasks.py` (field constants, Design Y `compute_composite`, gating logic, output columns), `docs/rater_guide.md` (criteria + worked examples), `docs/data_documentation.md` (Section 3.2 criteria + aggregation with explained citations, Section 3.6 Output C/D, Decisions Log, Decision History 5.23–5.24 and supersession notes on 5.5/5.20/5.21, this entry). A standalone prompt-change comparison document was produced for the supervisors.

**Archiving.** The v3 scoring outputs (pilot + smoke: scored CSV, progress JSONL, log) were moved to `data/processed/archive/v3/` (with a README), leaving the live `data/processed/` folder clean of prior-version outputs. This is both a comparison record and an operational necessity — the script resumes from any `progress_*.jsonl` in the live folder, so the v3.1 re-pilot would otherwise skip already-scored tasks. The live folder is now ready for the v3.1 re-pilot with no manual file moves required.

**Implications for next steps.** v3.1 is a draft pending the **re-pilot** (same 75 tasks, ~£0.40). With the live folder already cleaned, the re-pilot is a single command (`python src\03_score_tasks.py --input data\processed\pilot_tasks.csv`). The re-pilot must show: (a) the composite spans more than three values; (b) Capability Match now reaches 2 on clearly-capable tasks; (c) inter-criterion correlations fall well below the 0.95–0.99 of v3; (d) subjective/relational digital tasks land in the middle band rather than gating. If those hold, the prompt locks and the full run proceeds; if not, iterate (each re-pilot ~£0.40).

### 9.7 v3.1 Re-Pilot Result, the Criterion-3 Refinement (v3.2), and the Determinism Check (04 June 2026)

**v3.1 re-pilot (75 tasks, $0.37).** The redesign succeeded on every target:

| Check | v3 (failed) | v3.1 (re-pilot) |
|---|---|---|
| Distinct composite values | 3 | **7** (0, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0) |
| Capability Match = 2 | 0 / 75 | **8** tasks |
| Objective Verifiability correlation with others | part of the 0.95–0.99 cluster | **−0.16 / 0.29 / −0.07** (fully decoupled) |
| Subjective/relational digital tasks | all flattened to 0.875 | land in a populated **0.375–0.75 band** |

Per-criterion value use: Information Sufficiency {0:38, 2:37}; Objective Verifiability {0:7, 1:15, 2:53}; Contextual Independence {0:33, 1:20, 2:22}; Capability Match {0:38, 1:29, 2:8}. The reasoning was task-specific and sound (e.g., "evaluate consequences of legislative proposals," wrongly 0.875 in v3, now correctly 0.375 as a subjective forecast).

**The IS–CM 0.96 correlation, characterised.** Confirmed a genuine one-directional property: all 38 IS=0 tasks had CM=0 (a task AI cannot physically access, it cannot produce), while the 37 IS=2 tasks split CM {1:29, 2:8} (a digital task can still be beyond AI). IS=0 ⟹ CM=0, but IS=2 ⇏ CM=2. Kept and reported as a structural property (it produces a clean factor structure: one "can-AI-attempt-it" gate factor plus two independent quality dimensions), not treated as a defect.

**The one over-correction, and the v3.2 fix.** Reading the reasoning surfaced that Contextual Independence was over-applied — docking points for documentable organisation-specific context that could be supplied to the model (full evidence and the minimal one-sentence fix in Decision History 5.25). The fix touches Criterion 3 only; criteria 1/2/4, the schema, and the scoring code are unchanged.

**Archiving.** The v3.1 outputs (scored CSV, progress JSONL, log) were moved to `data/processed/archive/v3.1/`, leaving the live folder clean for the v3.2 re-pilot.

**Determinism/isolation check (single run) — result.** The v3.2 prompt was run once and criteria 1, 2, and 4 (identical wording to v3.1) compared against the archived v3.1 scores. **Information Sufficiency: 0/75 changed; Objective Verifiability: 4/75; Capability Match: 2/75 — 6 of 225 unchanged-criterion scores (2.7%), all ±1 except one, and bidirectional** (scattered up/down, i.e. stochastic noise, not one-directional edit ripple). The **gate set was identical (75/75 same PASS/GATED; 37/38 both versions)**. This 2.7% is an upper bound on the OpenAI `temperature = 0` reproducibility floor (the `system_fingerprint` can change server-side even at fixed seed). Criterion 3 moved as predicted — 13 routine documentable-context tasks rose (PASS-task Contextual-Independence 2-count 15 → 24); the genuine relational floor held (8/8); and the only "fallers" were gated physical tasks whose Contextual-Independence score never enters the composite. v3.2 passes; **the prompt is locked.** Full evidence in Decision History 5.26.

**Cost to date (smoke + all pilots).** Pre-flight + smoke (10 tasks) ≈ $0.05; v3 pilot $0.39; v3.1 re-pilot $0.37; v3.2 re-pilot $0.39 (actual); total spent so far ≈ **$1.20 (≈ £0.95)**. No further pilot spend is planned: the prompt is locked, so the next expenditure is the full production run (18,796 tasks, ≈ £73).

### 9.8 Pre-Run Operational Changes for Incremental Funding and Early Validity (06 June 2026)

Following supervisor requests (the funding professor wishes to add API credit in small increments — initially only $5 total — and to run the Tier-2 human validity check *before* committing to the full run), four operational changes were made. None alters the locked rubric, schema, model, temperature, or aggregation, so none requires re-piloting.

- **Clean halt on credit exhaustion (`03_score_tasks.py`).** Previously an out-of-credit `429 insufficient_quota` was treated as an ordinary rate-limit and retried with backoff, churning before each task was marked terminal. Now it is detected (`InsufficientCreditsError`) and the run **stops cleanly**, writing partial results and a clear resume message; re-running the same command after a top-up resumes from the checkpoint. This makes incremental funding of the long full run practical. The change touches only error handling — no score can change — and the gating/aggregation logic was re-verified by unit test after the edit.
- **Run-order randomisation (`02c_shuffle_master.py` → `master_tasks_shuffled.csv`).** The full-run input is now a fixed-seed (20260606) random permutation of `master_tasks.csv`. Because any prefix of a shuffled file is a representative random sample, the first chunk scored under the limited pre-run budget doubles as the stratified Tier-2 validity pool *and* as the opening segment of the full run — nothing is re-scored or wasted, and the rated tasks carry their final scores. Row order does not affect results (scores are keyed by `task_id`; aggregation is per-occupation).
- **Tier-2 brought forward (early human validity).** With ≈ $3.80 of credit remaining (≈ 700–730 tasks at the pilot's logged ~$0.0052/task), the plan is to score the shuffled prefix now, draw a **simple random sample of 100** from the completed tasks (fixed seed; simple random rather than stratified, on the supervisors' recommendation — Section 5.27), and have the three raters score them blind. This yields the validity read (κ vs. the model; α among raters) *before* the £73 run — the same de-risking logic as the pilot. (κ is reported with raw percent agreement, the confusion matrix, per-criterion breakdowns, and the sample's score distribution, so the prevalent zero-gated category does not distort interpretation — Section 5.27.)
- **Rater-guide / prompt wording parity.** Per a supervisor instruction to remove any wording confound from the validity check, the rater guide's construct, disambiguation rule, and all four criterion definitions and anchors were made **verbatim-identical** to `SYSTEM_PROMPT` in `rubric_prompt.py`. A build-time check confirms 28/28 distinctive prompt phrases appear word-for-word in both `rater_guide.md` and `Rater_Guide.docx`. The worked examples remain as human-only calibration, explicitly flagged as not shown to the model. A verbatim PDF of the exact system prompt, user message, and request configuration (`LLM_Prompt_Exact_v3.2.docx`/`.pdf`) was generated directly from source for the supervisors.

**Deliverables refreshed/added this session:** `LLM_Prompt_Exact_v3.2.pdf` (exact prompt, for the professor), updated `Rater_Guide.docx`/`rater_guide.md` (verbatim parity), `GenAI_Exposure_Index_PreRun_Briefing.docx`/`.pdf` (meeting briefing), `master_tasks_shuffled.csv` (run input). The blind rating spreadsheet is deferred until the pool is scored and the 100 tasks drawn.

---

## 10. Literature References

Full citations for the works underpinning the methodology. The *reasoning* for why each was chosen is given inline where it is used (principally Section 3.2 for the criteria and Section 5 for the decision history); this list provides traceability.

**Task-based automation framework and bottlenecks (underpin the four criteria, Section 3.2):**
- Autor, D. H., Levy, F., & Murnane, R. J. (2003). The skill content of recent technological change: An empirical exploration. *Quarterly Journal of Economics*, 118(4), 1279–1333. — *The foundational routine/non-routine task framework; the manual/analytic/interactive trichotomy underpinning Information Sufficiency and Contextual Independence.*
- Autor, D. H. (2015). Why are there still so many jobs? The history and future of workplace automation. *Journal of Economic Perspectives*, 29(3), 3–30. — *Polanyi's Paradox and tacit knowledge; underpins the tacit-context half of Contextual Independence.*
- Frey, C. B., & Osborne, M. A. (2013/2017). The future of employment: How susceptible are jobs to computerisation? *Technological Forecasting and Social Change*, 114, 254–280. — *The three engineering bottlenecks (perception/manipulation, creative intelligence, social intelligence) mapped to Information Sufficiency, Objective Verifiability, and Contextual Independence respectively.*
- Brynjolfsson, E., Mitchell, T., & Rock, D. (2018). What can machines learn, and what does it mean for occupations and the economy? *AEA Papers and Proceedings*, 108, 43–47. — *The Suitability-for-Machine-Learning rubric; "clear feedback / objective metrics" underpins Objective Verifiability, "long chains of reasoning" underpins Capability Match.*
- Deming, D. J. (2017). The growing importance of social skills in the labor market. *Quarterly Journal of Economics*, 132(4), 1593–1640. — *Empirical evidence that social-skill tasks resist automation and complement it; underpins the social half of Contextual Independence.*

**Generative-AI exposure and LLM-as-judge (underpin the method and Capability Match):**
- Eloundou, T., Manning, S., Mishkin, P., & Rock, D. (2023/2024). GPTs are GPTs: An early look at the labor market impact potential of large language models. arXiv:2303.10130; *Science* (2024). — *Validated LLM-as-judge exposure scoring (κ > 0.70 vs human raters); the speedup-vs-substitution distinction; underpins Capability Match.*
- Anthropic (2025). Labor market impacts of AI: A new measure and early evidence. — *Observed-exposure measure; augmentation half-weighting.*
- Felten, E., Raj, M., & Seamans, R. (2021). Occupational, industry, and geographic exposure to AI. *Strategic Management Journal*. — *AIOE; validation comparator.*
- Webb, M. (2020). The impact of artificial intelligence on the labor market. SSRN. — *Patent-based historical-AI exposure; the discriminant-validity comparator (Section 3.4).*

**Methodology design (aggregation, prompting, bias):**
- Einhorn, H. J. (1971). Use of nonlinear, noncompensatory models as a function of task and amount of information. *Organizational Behavior and Human Performance*, 6, 1–27. — *Conjunctive (non-compensatory) decision rule; underpins the Design Y gates.*
- Wei, J., et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS*. — *Reasoning-before-scoring design.*
- Suri, G., et al. (2024); Echterhoff, J., et al.; Itzhak, I., et al. — *Anchoring and cognitive biases in LLM evaluators; underpin the two-field Capability Match structure and the anti-anchoring instruction governing the anchor examples.*

**O*NET data quality and stability (Section 2):**
- Handel, M. J. (2016). The O*NET content model: strengths and limitations. *Journal for Labour Market Research*, 49(2), 157–176.
- Consoli, D., et al. (2023). Routinization and within-occupation task change. *Research Policy*.
- Autor, D. (2013). The "task approach" to labor markets: an overview. *Journal for Labour Market Research*, 46(3), 185–199. — *Underpins the task-interdependence limitation (Section 6.1).*

**Methodological reliability (limitations):**
- NBER Working Paper 35110 (2025). How (un)stable are LLM occupational exposure scores? — *Motivates the multi-LLM reliability check (Section 3.4 Tier 1; limitation 6.4).*

---

*Document created: 07 May 2026. Major revisions: Section 2 Literature Review added 08 May 2026; Section 3 Methodology and Section 6 Limitations added 08 May 2026; full methodology lock, multi-LLM reliability, binding constraint decomposition, dispersion analysis, validation strategy, master file schema, pilot protocol, and Section 5 Decision History added 09 May 2026; project reframed as Generative AI Vulnerability Framework, validation hierarchy restructured around convergent / discriminant validity distinction, analyst-coded task treatment corrected to imputed-and-included, BERT-based reproducibility analysis added 10 May 2026; pre-locked validation thresholds, within-project human-LLM validity check, API failure protocol, pilot overfitting defense, BERT model sensitivity, and Section 6.9 ground-truth limitation added 10 May 2026; master file built and Section 9.1 added 10 May 2026; rubric prompt v1 drafted, then revised to v2 with chain-of-thought reasoning, two-field balanced structure for Criterion 4, structured outputs (JSON Schema strict mode), uniform-scope disambiguation, and corrected cost math 10 May 2026; following supervisor feedback, validation hierarchy reduced from seven tiers to six (occupation-level expert spot-check dropped), stratified sampling protocol locked for the Tier 2 human validity check, and a rater guide produced 21 May 2026; following a criterion-overlap review, rubric revised to v3 (Decomposability decoupled from capability, Capability Match reliability bar sharpened), criterion dimensionality analysis added as Output D, Exception Sensitivity considered and rejected, and Decomposability held as a fixed fourth criterion 23 May 2026; scoring pipeline rewritten from the Batch API to the synchronous Chat Completions API after the funded account was found to be Usage Tier 1 (Batch enqueued-token limit far below the job size), with Section 5.22 and Implementation Log 9.5 added 03 June 2026; first pilot run 03 June 2026 revealed the v3 criteria collapsed the index (three of four criteria correlated 0.95–0.99, Capability Match never scored 2), prompting the **v3.1 criterion redesign** — four distinct literature-grounded barriers (Information Sufficiency, Objective Verifiability replacing Output Verifiability, Contextual Independence replacing Decomposability, recalibrated Capability Match) — and the **Design Y aggregation** (gate on impossibility, modulate on quality), with Decision History 5.23–5.24, supersession notes on 5.5/5.20/5.21, and Implementation Log 9.6 added 03 June 2026; the v3.1 re-pilot succeeded (7-value gradient, Capability Match reaching 2, Objective Verifiability decoupled) but revealed Contextual Independence was over-applied to documentable context, prompting a single-sentence **v3.2 refinement** of Criterion 3, with a temperature-0 determinism check, Decision History 5.25–5.26, and Implementation Log 9.7 added 04 June 2026. All content based on direct file inspection and verified web sources. No assumptions made without citation.*
