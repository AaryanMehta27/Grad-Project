/**
 * build_prerun_briefing.js
 * ========================
 * Pre-run briefing for the supervisors (Prof. Dash, Dr. Mukherjee): the full
 * chronological story of the smoke test, the three pilot iterations, the
 * Batch->synchronous infrastructure change, the obstacles and fixes, and the
 * road ahead — before the full master-file scoring run.
 *
 * Output: docs/GenAI_Exposure_Index_PreRun_Briefing.docx
 */

const path = require("path");
const fs = require("fs");
const docxPath = "C:/Users/aarya/AppData/Roaming/npm/node_modules/docx";
const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    Footer, Header, AlignmentType, HeadingLevel, BorderStyle, WidthType,
    ShadingType, PageNumber, LevelFormat,
} = require(docxPath);

const C = { primary: "1E3A5F", accent: "2E75B6", good: "2E7D32", bad: "B23B3B", muted: "595959", border: "CCCCCC", callout: "FFF4CE", soft: "F4F7FB", code: "F2F2F2" };
const F = { body: "Calibri", head: "Calibri", mono: "Consolas" };
const CONTENT = 9026; // A4 width (11906) minus 2x 1440 margins

function txt(t, o = {}) { return new TextRun({ text: t, font: o.font || F.body, size: o.size || 22, bold: o.bold || false, italics: o.italics || false, color: o.color || "000000" }); }
function p(c, o = {}) { const r = Array.isArray(c) ? c : [c]; return new Paragraph({ children: r.map(x => typeof x === "string" ? txt(x, o) : x), spacing: { before: o.before || 100, after: o.after || 100, line: 300 }, alignment: o.align || AlignmentType.JUSTIFIED }); }
function h1(t) { return new Paragraph({ children: [new TextRun({ text: t, font: F.head, size: 32, bold: true, color: C.primary })], spacing: { before: 420, after: 200 }, heading: HeadingLevel.HEADING_1, pageBreakBefore: true }); }
function h2(t) { return new Paragraph({ children: [new TextRun({ text: t, font: F.head, size: 26, bold: true, color: C.primary })], spacing: { before: 320, after: 160 }, heading: HeadingLevel.HEADING_2 }); }
function h3(t) { return new Paragraph({ children: [new TextRun({ text: t, font: F.head, size: 23, bold: true, color: C.accent })], spacing: { before: 220, after: 110 }, heading: HeadingLevel.HEADING_3 }); }
function bullet(t, level = 0) { return new Paragraph({ children: typeof t === "string" ? [txt(t)] : t, bullet: { level }, spacing: { before: 50, after: 50, line: 285 } }); }
function numbered(t, ref = "n") { return new Paragraph({ children: typeof t === "string" ? [txt(t)] : t, numbering: { reference: ref, level: 0 }, spacing: { before: 60, after: 60, line: 285 } }); }
function spacer(h = 120) { return new Paragraph({ children: [txt(" ")], spacing: { before: h, after: 0 } }); }

function callout(lines, color) {
    const border = { style: BorderStyle.SINGLE, size: 4, color: C.accent };
    const cb = { top: border, bottom: border, left: border, right: border };
    const paras = lines.map(l => Array.isArray(l) ? new Paragraph({ children: l, spacing: { before: 70, after: 70, line: 290 } }) : (typeof l === "string" ? new Paragraph({ children: [txt(l)], spacing: { before: 70, after: 70, line: 290 } }) : l));
    return new Table({ width: { size: CONTENT, type: WidthType.DXA }, columnWidths: [CONTENT],
        rows: [new TableRow({ children: [new TableCell({ width: { size: CONTENT, type: WidthType.DXA }, borders: cb, shading: { fill: color || C.callout, type: ShadingType.CLEAR }, margins: { top: 120, bottom: 120, left: 200, right: 200 }, children: paras })] })] });
}

function table(rows, opts = {}) {
    const cw = opts.colWidths || rows[0].map(() => Math.floor(CONTENT / rows[0].length));
    const total = cw.reduce((a, b) => a + b, 0);
    const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
    const cb = { top: border, bottom: border, left: border, right: border };
    const trows = rows.map((row, idx) => {
        const isH = idx === 0 && opts.header !== false;
        return new TableRow({ tableHeader: isH,
            children: row.map((cell, ci) => {
                const mkPara = (kids) => new Paragraph({ children: kids, spacing: { before: 36, after: 36, line: 250 }, alignment: opts.align || AlignmentType.LEFT });
                // String cell -> one paragraph; array cell -> one paragraph holding its TextRuns
                // (a raw TextRun is NOT a valid TableCell child and renders empty, so always wrap).
                const ps = Array.isArray(cell)
                    ? [mkPara(cell.map(x => typeof x === "string" ? txt(x, { bold: isH, color: isH ? "FFFFFF" : "000000", size: opts.size || 19 }) : x))]
                    : [mkPara([txt(cell, { bold: isH, color: isH ? "FFFFFF" : "000000", size: opts.size || 19 })])];
                return new TableCell({ width: { size: cw[ci], type: WidthType.DXA }, borders: cb,
                    shading: isH ? { fill: C.primary, type: ShadingType.CLEAR } : { fill: idx % 2 === 0 ? "FFFFFF" : C.soft, type: ShadingType.CLEAR },
                    margins: { top: 60, bottom: 60, left: 110, right: 110 }, children: ps });
            }),
        });
    });
    return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: cw, rows: trows });
}

const ch = [];

// ============================ COVER ============================
ch.push(spacer(1400));
ch.push(new Paragraph({ children: [new TextRun({ text: "Generative AI Exposure Index", font: F.head, size: 52, bold: true, color: C.primary })], alignment: AlignmentType.CENTER, spacing: { after: 120 } }));
ch.push(new Paragraph({ children: [new TextRun({ text: "Pre-Run Briefing", font: F.head, size: 40, bold: true, color: C.accent })], alignment: AlignmentType.CENTER, spacing: { after: 200 } }));
ch.push(new Paragraph({ children: [new TextRun({ text: "Pipeline validation, three pilot iterations, the obstacles we hit and fixed, and the path to scoring all 18,796 tasks", font: F.head, size: 24, italics: true, color: C.muted })], alignment: AlignmentType.CENTER, spacing: { after: 600 } }));
ch.push(spacer(500));
ch.push(p([txt("Prepared for: ", { bold: true }), txt("Prof. Manoranjan Dash  ·  Dr. Shreya Mukherjee")], { align: AlignmentType.CENTER }));
ch.push(p([txt("Prepared by: ", { bold: true }), txt("Aaryan Mehta — FLAME University")], { align: AlignmentType.CENTER }));
ch.push(p([txt("Date: ", { bold: true }), txt("6 June 2026")], { align: AlignmentType.CENTER }));
ch.push(p([txt("Status: ", { bold: true }), txt("Scoring prompt locked at v3.2. Pilot passed. Awaiting go-ahead for the full run.", { bold: true, color: C.good })], { align: AlignmentType.CENTER }));

// ============================ HOW TO READ ============================
ch.push(spacer(700));
ch.push(callout([
    [txt("How to read this. ", { bold: true }), txt("If you have ten minutes, read §1 (where we are), §5–§8 (the pilot story and the rubric problem we caught and fixed), and §10 (what the full run and validation look like). Everything else is supporting detail, data, and worked examples. The headline: piloting on 75 tasks for under £1 caught a rubric flaw that would have invalidated the entire £73 run — which is exactly what a pilot is for.")],
], C.callout));

// ============================ 1. WHERE WE ARE ============================
ch.push(h1("1. Where we are, in one page"));
ch.push(p("Since the API credits were funded we have done four things, in order: (a) validated the full scoring pipeline end-to-end on a tiny set of tasks; (b) discovered that the funded account could not run the originally-planned Batch API and re-engineered the pipeline to a synchronous one with no change to the science; (c) run the 75-task pilot, which revealed that the scoring rubric had a fundamental construct flaw; and (d) redesigned the rubric, re-piloted twice, characterised the model's run-to-run stability, and locked the final prompt. We then ran a pre-run audit of the whole project before committing to the expensive run."));
ch.push(p([txt("The pilot did precisely the job it exists to do. ", { bold: true }), txt("It cost about £0.95 in total across three iterations and caught a problem that, undetected, would have produced a meaningless index from the full £73 run. We are now ready to score all 18,796 task statements.")]));
ch.push(spacer(60));
ch.push(table([
    ["Milestone", "Outcome", "Cost"],
    ["Pre-flight + smoke test (12 tasks)", "Pipeline validated end-to-end; 100% parse; no errors", "~$0.05"],
    ["Pilot 1 — rubric v3 (75 tasks)", "FAILED as designed — index collapsed to 3 values; root cause diagnosed", "$0.39"],
    ["Pilot 2 — rubric v3.1 (75 tasks)", "Redesign succeeded; 7-value gradient; one over-correction found", "$0.37"],
    ["Pilot 3 — rubric v3.2 (75 tasks)", "PASSED all checks; prompt LOCKED; stability characterised", "$0.39"],
    ["Pre-run audit", "Whole-project review; methodology documentation reconciled before the run", "—"],
    ["Full run (18,796 tasks)", "Ready to begin on your go-ahead", "~£73"],
], { colWidths: [3000, 4626, 1400], size: 19 }));

// ============================ 2. METHOD REFRESHER ============================
ch.push(h1("2. The method, briefly (and the final locked criteria)"));
ch.push(p([txt("The index scores each O*NET task statement with a large language model acting as an expert judge ("), txt("LLM-as-judge", { italics: true }), txt(", the approach validated by Eloundou et al. 2023 and replicated by Anthropic 2025). GPT-4o (fixed version "), txt("gpt-4o-2024-11-20", { font: F.mono, size: 20 }), txt(", temperature 0, fixed random seed, structured-output mode) reads each task and the occupation it belongs to, then scores it on four criteria, each 0 / 1 / 2. A composite exposure score in [0, 1] is then computed by a deliberate aggregation rule. These are the four criteria as finally locked (v3.2):")]));
ch.push(spacer(60));
ch.push(table([
    ["Criterion (0/1/2)", "The barrier it measures", "Grounding"],
    [[txt("1. Information Sufficiency", { bold: true, size: 19 })], "Can the task be done with digitally-conveyable information, or does it need physical presence / embodiment? (The only physical-vs-digital criterion.)", "Frey & Osborne 2013; Autor, Levy & Murnane 2003"],
    [[txt("2. Objective Verifiability", { bold: true, size: 19 })], "Is success objectively checkable, or a matter of subjective judgement / taste?", "Brynjolfsson, Mitchell & Rock 2018"],
    [[txt("3. Contextual Independence", { bold: true, size: 19 })], "Can it be done from the task description + general knowledge, or does it need real-time human interaction or genuinely tacit insider context?", "Autor 2015 (Polanyi); Deming 2017"],
    [[txt("4. Capability Match", { bold: true, size: 19 })], "Can a current frontier model produce the core output at or above an average human worker's quality?", "Eloundou et al. 2023"],
], { colWidths: [2300, 5026, 1700], size: 19 }));
ch.push(spacer(80));
ch.push(p([txt("Aggregation — “Design Y”. ", { bold: true }), txt("The composite is 0 (“gated”) if Information Sufficiency = 0 OR Capability Match = 0 — these are the two categorical “can the model even attempt it?” conditions (a disembodied model cannot do a physical task; a task beyond current capability cannot be substituted). Otherwise the composite is the mean of all four criteria ÷ 2, so the other two criteria pull the score down without zeroing it. This follows the conjunctive (non-compensatory) decision rule of Einhorn (1971): failure on a genuinely necessary condition cannot be compensated by strength elsewhere.")]));

// ============================ 3. SMOKE ============================
ch.push(h1("3. Pipeline validation: pre-flight and smoke test"));
ch.push(p("Before spending meaningfully, we confirmed the machinery works. A 2-task pre-flight checked that the API key authenticates, the structured-output schema is accepted, the response parses into the nine expected fields, the per-task checkpoint file is written, and the cost meter reads from the live usage figures. A 10-task smoke test then exercised the same path at slightly larger scale."));
ch.push(p([txt("Result: clean. ", { bold: true }), txt("100% of responses parsed and validated, no rate-limit or network errors at the chosen pacing, checkpoint-and-resume worked, and the cost meter tracked correctly. Total spend for pre-flight + smoke was approximately $0.05. This confirmed that any subsequent problem would be a "), txt("rubric", { italics: true }), txt(" problem, not a plumbing problem — which matters, because that is exactly the distinction the next stage turned on.")]));

// ============================ 4. BATCH -> SYNC ============================
ch.push(h1("4. The infrastructure change: Batch → synchronous API"));
ch.push(p([txt("This is an engineering footnote rather than a scientific change, but it is worth recording because it changed the cost and the runtime. ", {}), txt("The pipeline was originally built around OpenAI’s Batch API", { bold: true }), txt(", which offers a 50% discount and is the natural choice for a one-shot job of ~18,800 requests.")]));
ch.push(p([txt("The obstacle. ", { bold: true }), txt("When the account was funded and we inspected its actual limits, it was a new "), txt("Usage Tier 1", { bold: true }), txt(" account. The Batch API on Tier 1 caps the number of input tokens that can sit in the queue at once — the "), txt("enqueued-token limit", { italics: true }), txt(" — at 90,000 tokens for GPT-4o. Our numbers made Batch unusable:")]));
ch.push(spacer(50));
ch.push(table([
    ["Quantity", "Tokens", "vs. the 90,000 Batch limit"],
    ["Full job (18,796 tasks × ~2,036 input tokens)", "~38,300,000", "~425× over the limit"],
    ["Even the 75-task pilot", "~153,000", "~1.7× over the limit"],
], { colWidths: [4626, 2200, 2200], size: 19 }));
ch.push(spacer(70));
ch.push(p([txt("The fix. ", { bold: true }), txt("We re-engineered the scorer to use the standard "), txt("synchronous", { italics: true }), txt(" Chat Completions API, which is governed by a per-minute rate limit (30,000 tokens/minute on this account) rather than the batch queue. The script paces itself to stay under that limit, backs off exponentially on any rate-limit or transient error, and — crucially — "), txt("checkpoints after every single task", { bold: true }), txt(", so a multi-hour run can be interrupted (closed laptop, lost Wi-Fi) and resumed with the same command, never re-scoring or re-paying for completed work.")]));
ch.push(spacer(40));
ch.push(callout([
    [txt("What changes, and what does not. ", { bold: true }), txt("Changes: cost rises from roughly £53 to roughly £73 (no 50% batch discount; partially offset by automatic prompt-caching of the shared instruction text), and the run takes ~28–31 hours of wall-clock time instead of an overnight batch — but it is fully resumable. Does NOT change: the model, the prompt, the schema, the temperature, the seed, the four criteria, and the aggregation rule are all identical. The same script is used for the smoke test, the pilots, and the full run, so the pilot validates exactly what the full run executes.")],
], C.soft));

// ============================ 5. PILOT 1 (v3 failure) ============================
ch.push(h1("5. Pilot 1 (rubric v3): the failure the pilot was built to catch"));
ch.push(p([txt("The pilot is 75 tasks, deliberately ", {}), txt("curated, not random", { bold: true }), txt(", because its job is to stress-test the rubric on known-difficult cases rather than to estimate a population average. It is built from four buckets:")]));
ch.push(spacer(40));
ch.push(table([
    ["Bucket", "n", "What it tests"],
    ["A — expected high", "20", "Clearly digital, capable tasks (coding, analysis, drafting) — should score high"],
    ["B — expected low", "20", "Clearly physical / embodied tasks (care, construction, repair) — should gate to 0"],
    ["C — ambiguous", "20", "Physical/digital ambiguity (“inspect”, “monitor”, “review”) — the load-bearing cases"],
    ["D — mixed", "15", "A spread of task types, sources, and dates"],
], { colWidths: [2200, 700, 6126], size: 19 }));
ch.push(spacer(70));
ch.push(p([txt("The result was a clear failure — and a useful one. ", { bold: true }), txt("The composite score took only "), txt("three distinct values across all 75 tasks", { bold: true }), txt(": 0, 0.75, and 0.875. Every digital task collapsed onto 0.875. An index that can only say “0, 0.75, or 0.875” cannot rank occupations.")]));
ch.push(h3("Diagnosis"));
ch.push(bullet([txt("Three of the four criteria were secretly measuring the same thing. ", { bold: true }), txt("Information Sufficiency, the old “Output Verifiability”, and the old “Decomposability” correlated at "), txt("0.95–0.99", { bold: true }), txt(". Reading the model’s written reasoning showed why: all three had quietly reduced to “is this physical or digital?” — e.g. Output Verifiability keyed on whether the output was a digital file; Decomposability keyed on whether the task split into digital sub-steps.")]));
ch.push(bullet([txt("Capability Match never once scored 2. ", { bold: true }), txt("Its definition set an impossible bar (“reliable enough to use with no per-instance human re-checking”), so even tasks GPT-4o does excellently were capped at 1.")]));
ch.push(bullet([txt("A concrete symptom: ", { bold: true }), txt("the task "), txt("“Evaluate transportation-related consequences of legislative proposals”", { italics: true }), txt(" scored 0.875 — treated as almost fully substitutable — when it is a subjective forecast that should land in the middle of the range. The rubric had no way to express “capable but subjective.”")]));
ch.push(p([txt("Cost of this discovery: $0.39. ", { bold: true }), txt("Had the same flaw been discovered after the full run, it would have cost £73 and a fortnight of compute — and produced an unusable index. This is the entire economic argument for piloting.")]));

// ============================ 6. REDESIGN v3.1 ============================
ch.push(h1("6. The redesign (v3.1): four distinct, literature-grounded barriers"));
ch.push(p("Rather than patch the wording, we redesigned the four criteria so that each captures a genuinely different reason a task resists AI substitution — mapping onto the established bottlenecks in the automation literature — and added explicit “this criterion is NOT about X” guards so the model could not re-derive “physical vs digital” inside a criterion meant to measure something else."));
ch.push(spacer(40));
ch.push(table([
    ["v3 (collapsed)", "v3.1 (redesigned)", "What changed"],
    ["Information Sufficiency", "Information Sufficiency (kept)", "Now the ONLY physical-vs-digital criterion"],
    ["Output Verifiability", "Objective Verifiability", "From “is the output a digital file?” to “is success objectively checkable vs subjective?” — a digital output can be subjective"],
    ["Decomposability", "Contextual Independence", "Replaced entirely — now captures the social / tacit-knowledge barrier (live negotiation, counselling, insider context) the old rubric missed"],
    ["Capability Match", "Capability Match (recalibrated)", "Benchmark is now the average human worker; output that gets normal review still scores 2"],
], { colWidths: [2100, 2300, 4626], size: 18 }));
ch.push(spacer(70));
ch.push(p([txt("We also fixed the aggregation. ", { bold: true }), txt("The original rule gated the composite to 0 if "), txt("any", { italics: true }), txt(" criterion was 0 — which, combined with the broken criteria, is what crushed the index to three values. “Design Y” (§2) instead gates only on the two criteria that represent categorical impossibility (Information Sufficiency and Capability Match) and lets the other two "), txt("modulate", { italics: true }), txt(" the score. This restores a meaningful gradient: a capable-but-subjective digital task now lands around 0.75, a capable-but-relational one around 0.5, a fully-substitutable one at 1.0, and a physical or beyond-capability one at 0.")]));

// ============================ 7. PILOT 2 (v3.1) ============================
ch.push(h1("7. Pilot 2 (rubric v3.1): the redesign worked — with one over-correction"));
ch.push(p("Re-running the identical 75-task pilot on the redesigned rubric ($0.37) succeeded on every target the failure had set:"));
ch.push(spacer(40));
ch.push(table([
    ["Check", "v3 (failed)", "v3.1 (re-pilot)"],
    ["Distinct composite values", "3  (0, 0.75, 0.875)", "7  (0, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)"],
    ["Capability Match = 2", "0 of 75 tasks", "8 tasks (the bar is now reachable)"],
    ["Objective Verifiability correlation with the others", "part of the 0.95–0.99 cluster", "−0.16 to 0.29 (fully decoupled)"],
    ["Subjective / relational digital tasks", "all flattened to 0.875", "land in a populated 0.375–0.75 middle band"],
], { colWidths: [3000, 2700, 3326], size: 18 }));
ch.push(spacer(70));
ch.push(p([txt("The IS–Capability Match correlation (0.96) is real, and we keep it. ", { bold: true }), txt("It is a "), txt("one-directional", { italics: true }), txt(" property, not redundancy: every task that fails Information Sufficiency (= 0, physical) also fails Capability Match (a model cannot produce a physical output), but the reverse does not hold — a digital task can still be beyond the model. So IS = 0 ⇒ CM = 0, while IS = 2 does not imply CM = 2. We report this as a structural property of the index, not a defect.")]));
ch.push(h3("The one problem, found by reading the reasoning"));
ch.push(p([txt("Contextual Independence was being over-applied. ", { bold: true }), txt("The model docked a point (scoring 1 instead of 2) whenever a task touched "), txt("any", { italics: true }), txt(" organisation-specific context — even context that could simply be written down and handed to the model. The clearest example: ")]));
ch.push(callout([
    [txt("Task: ", { bold: true }), txt("“Write supporting code for Web applications or Web sites”", { italics: true }), txt("  (Web Developers)")],
    [txt("v3.1 scored Contextual Independence = ", {}), txt("1", { bold: true }), txt(", with the reasoning “much of the task can be completed with general programming knowledge and the task description” — reasoning that argues for a "), txt("2", { bold: true }), txt(", then records a 1.")],
], C.soft));
ch.push(p([txt("This systematically under-scored routine digital cognitive work — which is precisely the category most exposed to Generative AI, so the error ran in the worst possible direction for an exposure index.")]));

// ============================ 8. v3.2 + LOCK ============================
ch.push(h1("8. The minimal fix (v3.2), the stability check, and the lock"));
ch.push(p([txt("Because the criterion’s "), txt("construct", { italics: true }), txt(" was correct and only its boundary was being read too broadly, we made the smallest possible change rather than another rewrite (a rewrite risks introducing new failure modes). We added "), txt("one clarifying sentence", { bold: true }), txt(" to Criterion 3 — documentable context (procedures, files, policies, client requirements that can be supplied to the model) is not a barrier; only real-time human interaction or genuinely tacit knowledge is — and sharpened the “score 2” anchor. "), txt("Criteria 1, 2, and 4, the response schema, and the scoring code were left byte-for-byte unchanged.", { bold: true })]));
ch.push(h3("Confirming the change was isolated, and checking the model’s stability"));
ch.push(p([txt("Because three criteria were untouched, we could check both isolation and run-to-run stability "), txt("without paying for a second run", { italics: true }), txt(": we compared the three unchanged criteria’s scores in the v3.2 run against the v3.1 run. If they barely move, the edit was clean and the model is stable. The result:")]));
ch.push(spacer(40));
ch.push(table([
    ["Unchanged criterion", "Tasks whose score changed (of 75)"],
    ["Information Sufficiency", "0"],
    ["Objective Verifiability", "4"],
    ["Capability Match", "2"],
    ["Total", "6 of 225 scores = 2.7%, all by one step, in both directions"],
], { colWidths: [4000, 5026], size: 19 }));
ch.push(spacer(70));
ch.push(p([txt("Two things follow. ", { bold: true }), txt("First, the change was clean: a leak from editing one criterion would push the others consistently in one direction, whereas these six differences are single-step and scattered both ways — the signature of ordinary model noise, not contamination. Every task kept the same pass/gate outcome (37 pass, 38 gated in both versions). Second, this is our measured answer to a question worth asking of any AI-scored study: "), txt("even at temperature 0 with a fixed seed, GPT-4o is not perfectly repeatable", { bold: true }), txt(" — about 2–3% of individual scores can shift by one step on a re-run, because OpenAI’s back-end can change between calls. The overall distribution and every gate decision were stable. We document this ~2.7% as a known, bounded reproducibility floor, not a flaw.")]));
ch.push(h3("Did the fix do what it was meant to?"));
ch.push(bullet([txt("Yes, in the right place: ", { bold: true }), txt("13 routine documentable-context tasks rose a step on Criterion 3 (e.g. “write supporting code for web applications”, “code documents per company procedures”, “review and update credit and loan files”). Among the tasks that actually reach the composite, the count scoring Contextual Independence = 2 rose from 15 to 24.")]));
ch.push(bullet([txt("The relational floor held: ", { bold: true }), txt("of the genuinely interpersonal tasks (patient care, client-facing work, teaching), 8 of 8 stayed at 0. The fix lifted documentable desk work without eroding the real social barrier.")]));
ch.push(bullet([txt("The composite kept its full 7-value gradient", { bold: true }), txt(" (mean 0.395). The prompt was then "), txt("LOCKED", { bold: true, color: C.good }), txt(": any future change re-triggers the pilot.")]));
ch.push(spacer(40));
ch.push(p([txt("Per-criterion score usage in the final (v3.2) pilot, for reference — all four criteria now use their full range:")]));
ch.push(spacer(30));
ch.push(table([
    ["Criterion", "score 0", "score 1", "score 2"],
    ["Information Sufficiency", "38", "0", "37"],
    ["Objective Verifiability", "7", "14", "54"],
    ["Contextual Independence", "33", "13", "29"],
    ["Capability Match", "38", "29", "8"],
], { colWidths: [3626, 1800, 1800, 1800], size: 19, align: AlignmentType.LEFT }));
ch.push(spacer(60));
ch.push(p([txt("Behaviour by pilot bucket (v3.2) confirms the ordering is correct: ", {}), txt("A (expected-high)", { bold: true }), txt(" mean 0.825, all 20 passed; "), txt("B (expected-low)", { bold: true }), txt(" all 20 gated to 0; "), txt("C (ambiguous)", { bold: true }), txt(" split 11 pass / 9 gated, mean 0.381; "), txt("D (mixed)", { bold: true }), txt(" 6 pass / 9 gated, mean 0.367.")]));

// ============================ 9. COST ============================
ch.push(h1("9. Cost to date, and what remains"));
ch.push(table([
    ["Item", "Cost"],
    ["Pre-flight + smoke test", "~$0.05"],
    ["Pilot 1 (v3)", "$0.39"],
    ["Pilot 2 (v3.1)", "$0.37"],
    ["Pilot 3 (v3.2)", "$0.39"],
    ["Total spent piloting", "~$1.20  (~£0.95)"],
    ["Full scoring run (18,796 tasks)", "~£73"],
    ["Claude reliability sample (~1,800 tasks, later)", "~£5–15"],
], { colWidths: [6026, 3000], size: 19 }));
ch.push(spacer(60));
ch.push(p([txt("The whole point of the three-iteration pilot loop is in those numbers: ", {}), txt("we spent under £1 to de-risk a £73 run", { bold: true }), txt(", and we now know exactly what the full run will produce and where its residual uncertainties lie.")]));

// ============================ 10. THE ROAD AHEAD ============================
ch.push(h1("10. What the full run looks like, and the validation ahead"));
ch.push(p([txt("The run itself. ", { bold: true }), txt("One command scores all 18,796 tasks with the locked v3.2 prompt: ~28–31 hours of wall-clock time, fully resumable, with a hard cost cap as a runaway guard. We expect a clean exposure gradient in which the Information-Sufficiency / Capability-Match gate does most of the structural work (physical and care occupations cluster near 0), a populated cognitive middle (roughly 0.5–0.875), and a sparse ceiling at 1.0 (the genuinely fully-substitutable tasks: data extraction, translation, routine drafting).")]));
ch.push(p([txt("Immediately after, a post-scoring audit", { bold: true }), txt(" reviews every zero-gated task (genuine impossibility vs. a misread of an ambiguous task). Then the index is validated against independent measures, with every threshold committed in advance:")]));
ch.push(spacer(40));
ch.push(table([
    ["Validation tier", "Type", "Pre-locked threshold"],
    ["Claude 3.5 Sonnet on ~1,800 tasks", "Reliability across two different models", "Cohen’s κ ≥ 0.70"],
    ["The three of us rate 100 tasks by hand", "Human validity (this is where your ratings come in)", "κ ≥ 0.60 vs. the model"],
    ["Eloundou et al. 2023", "Convergent (same construct)", "Spearman ρ ≥ 0.55"],
    ["Webb 2020 (patent-based)", "Discriminant (different construct)", "ρ(Eloundou) − ρ(Webb) ≥ 0.15"],
], { colWidths: [3200, 3326, 2500], size: 18 }));
ch.push(spacer(70));
ch.push(p([txt("A BERT-based analysis", { bold: true }), txt(" then asks how much of the model’s scoring can be reproduced from cheap text embeddings alone — a methodological characterisation the LLM-as-judge literature has not done. And this whole exposure index is "), txt("Part 1", { bold: true }), txt(". Part 2 adds an Adaptation Capacity dimension (from PIAAC) to turn structural exposure into a two-dimensional "), txt("vulnerability", { italics: true }), txt(" framework — the larger contribution the project is building toward.")]));

// ============================ 11. ASK ============================
ch.push(h1("11. In summary"));
ch.push(p("The pipeline is validated, the rubric problem the pilot existed to catch was caught and fixed for under £1, the model’s run-to-run stability is measured and documented, the scoring prompt is locked, and the project’s documentation has been reconciled to the final design. The one residual measurement risk is understood, bounded, conservative in direction, and instrumented with a post-run check."));
ch.push(p([txt("We are ready to begin the full scoring run on your go-ahead.", { bold: true })]));
ch.push(spacer(200));
ch.push(p([txt("Supporting detail for every point above — the exact reasoning excerpts, the full decision history, and the literature justifications — is in the project’s living methodology document and the prompt-change record, available on request.", { italics: true, color: C.muted })], { align: AlignmentType.LEFT }));
ch.push(spacer(300));
ch.push(new Paragraph({ children: [txt("Aaryan Mehta  ·  FLAME University  ·  6 June 2026", { italics: true, color: C.muted, size: 20 })], alignment: AlignmentType.CENTER }));

// ============================ DOC ============================
const doc = new Document({
    creator: "Aaryan Mehta",
    title: "Generative AI Exposure Index — Pre-Run Briefing",
    description: "Smoke test, pilot iterations, and the path to the full run",
    styles: {
        default: { document: { run: { font: F.body, size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F.head, size: 32, bold: true, color: C.primary }, paragraph: { spacing: { before: 420, after: 200 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F.head, size: 26, bold: true, color: C.primary }, paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 1 } },
            { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F.head, size: 23, bold: true, color: C.accent }, paragraph: { spacing: { before: 220, after: 110 }, outlineLevel: 2 } },
        ],
    },
    numbering: { config: [{ reference: "n", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, style: { paragraph: { indent: { left: 620, hanging: 320 } } } }] }] },
    sections: [{
        properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
        headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [txt("Generative AI Exposure Index — Pre-Run Briefing", { size: 16, color: C.muted, italics: true })] })] }) },
        footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [txt("Page ", { size: 18, color: C.muted }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: C.muted }), txt("  ·  Confidential — for supervisory review", { size: 18, color: C.muted })] })] }) },
        children: ch,
    }],
});

const outFile = path.join(__dirname, "GenAI_Exposure_Index_PreRun_Briefing.docx");
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(outFile, buf); console.log(`Wrote: ${outFile}  (${(buf.length / 1024).toFixed(1)} KB)`); });
