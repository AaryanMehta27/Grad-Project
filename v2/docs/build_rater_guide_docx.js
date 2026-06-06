/**
 * build_rater_guide_docx.js
 * =========================
 *
 * Converts rater_guide.md (v3.2) into a Word document for the three raters.
 *
 * IMPORTANT — verbatim parity: the construct (section 2), the disambiguation rule
 * (section 3), and the four criterion definitions and anchors (section 4) are
 * reproduced WORD-FOR-WORD from SYSTEM_PROMPT in src/rubric_prompt.py, so human
 * raters and the model judge against identical wording. If the prompt ever
 * changes, these strings must be re-synced and verified (see the parity check in
 * the build pipeline). Output: docs/Rater_Guide.docx
 */

const path = require("path");
const fs = require("fs");
const docxPath = "C:/Users/aarya/AppData/Roaming/npm/node_modules/docx";
const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
    ShadingType, PageNumber, LevelFormat,
} = require(docxPath);

const COLORS = { primary: "1E3A5F", accent: "2E75B6", muted: "595959", border: "CCCCCC", callout: "FFF4CE", code: "F2F2F2" };
const FONTS = { body: "Calibri", heading: "Calibri", mono: "Consolas" };

function txt(t, o = {}) { return new TextRun({ text: t, font: o.font || FONTS.body, size: o.size || 22, bold: o.bold || false, italics: o.italics || false, color: o.color || "000000" }); }
function p(c, o = {}) { const r = Array.isArray(c) ? c : [c]; return new Paragraph({ children: r.map(x => typeof x === "string" ? txt(x, o) : x), spacing: { before: o.before || 100, after: o.after || 100, line: 300 }, alignment: o.alignment || AlignmentType.JUSTIFIED }); }
function h1(t) { return new Paragraph({ children: [new TextRun({ text: t, font: FONTS.heading, size: 36, bold: true, color: COLORS.primary })], spacing: { before: 480, after: 240 }, heading: HeadingLevel.HEADING_1, pageBreakBefore: true }); }
function h2(t) { return new Paragraph({ children: [new TextRun({ text: t, font: FONTS.heading, size: 28, bold: true, color: COLORS.primary })], spacing: { before: 360, after: 180 }, heading: HeadingLevel.HEADING_2 }); }
function bullet(t, level = 0) { return new Paragraph({ children: typeof t === "string" ? [txt(t)] : t, bullet: { level }, spacing: { before: 60, after: 60, line: 280 } }); }
function numbered(t) { return new Paragraph({ children: typeof t === "string" ? [txt(t)] : t, numbering: { reference: "default-numbering", level: 0 }, spacing: { before: 80, after: 80, line: 280 } }); }
function blockquote(s) { return new Paragraph({ children: [txt(s, { italics: true })], spacing: { before: 80, after: 80, line: 300 }, indent: { left: 360 }, shading: { fill: "F8F9FA", type: ShadingType.CLEAR } }); }
function callout(lines, color = COLORS.callout) {
    const border = { style: BorderStyle.SINGLE, size: 4, color: COLORS.accent };
    const cb = { top: border, bottom: border, left: border, right: border };
    const paras = lines.map(l => Array.isArray(l) ? new Paragraph({ children: l, spacing: { before: 80, after: 80, line: 290 } }) : (typeof l === "string" ? new Paragraph({ children: [txt(l, { italics: true })], spacing: { before: 80, after: 80 } }) : l));
    return new Table({ width: { size: 9026, type: WidthType.DXA }, columnWidths: [9026],
        rows: [new TableRow({ children: [new TableCell({ width: { size: 9026, type: WidthType.DXA }, borders: cb, shading: { fill: color, type: ShadingType.CLEAR }, margins: { top: 120, bottom: 120, left: 200, right: 200 }, children: paras })] })] });
}
function spacer(h = 120) { return new Paragraph({ children: [txt(" ")], spacing: { before: h, after: 0 } }); }
function scoreTable(rows, opts = {}) {
    const cw = opts.colWidths || rows[0].map(() => Math.floor(9026 / rows[0].length));
    const total = cw.reduce((a, b) => a + b, 0);
    const border = { style: BorderStyle.SINGLE, size: 1, color: COLORS.border };
    const cb = { top: border, bottom: border, left: border, right: border };
    const trows = rows.map((row, idx) => {
        const isH = idx === 0 && opts.header !== false;
        return new TableRow({ tableHeader: isH,
            children: row.map((cell, ci) => {
                const arr = Array.isArray(cell) ? cell : [cell];
                const ps = [new Paragraph({ children: arr.map(x => typeof x === "string" ? txt(x, { bold: isH, color: isH ? "FFFFFF" : "000000", size: 20 }) : x), spacing: { before: 40, after: 40, line: 260 } })];
                return new TableCell({ width: { size: cw[ci], type: WidthType.DXA }, borders: cb,
                    shading: isH ? { fill: COLORS.primary, type: ShadingType.CLEAR } : { fill: idx % 2 === 0 ? "FFFFFF" : "F8F9FA", type: ShadingType.CLEAR },
                    margins: { top: 80, bottom: 80, left: 120, right: 120 }, children: ps });
            }),
        });
    });
    return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: cw, rows: trows });
}

const children = [];

// COVER
children.push(spacer(2000));
children.push(new Paragraph({ children: [new TextRun({ text: "Rater Guide", font: FONTS.heading, size: 56, bold: true, color: COLORS.primary })], spacing: { before: 480, after: 240 }, alignment: AlignmentType.CENTER }));
children.push(new Paragraph({ children: [new TextRun({ text: "Generative AI Exposure Index — Tier 2 Human Validity Sample", font: FONTS.heading, size: 24, italics: true, color: COLORS.muted })], spacing: { before: 120, after: 480 }, alignment: AlignmentType.CENTER }));
children.push(spacer(800));
children.push(p([txt("For: ", { bold: true }), txt("Aaryan Mehta (researcher), Prof. Manoranjan Dash (supervisor), Dr. Shreya Mukherjee (supervisor)")]));
children.push(p([txt("Purpose: ", { bold: true }), txt("independent task-level rating of 100 O*NET tasks for comparison against the LLM scores")]));
children.push(p([txt("Created: ", { bold: true }), txt("21 May 2026")]));
children.push(p([txt("Revised: ", { bold: true }), txt("06 June 2026 — rubric v3.2, with the construct, disambiguation rule, and all four criterion definitions and anchors reproduced verbatim from the system prompt given to GPT-4o, so raters and the model judge against identical wording.")]));
children.push(p([txt("Status: ", { bold: true }), txt("Use as-is for the rating session. Any clarifications can be added in the margins; revisions to the guide itself trigger a new rating round.")]));

// 1. WHAT YOU ARE DOING
children.push(h1("1. What you are doing"));
children.push(p("You will independently rate 100 O*NET task statements against the same four-criterion rubric that GPT-4o is using. After all three of us have completed our ratings (blind to each other and to the LLM scores), the three sets of human ratings are averaged per criterion and compared to the LLM's scores. The headline statistic is Cohen's κ between the averaged human rating and the LLM rating, with κ ≥ 0.60 set as the pre-locked threshold for the within-project validity check."));
children.push(p([txt("The 100 tasks are a "), txt("simple random sample", { bold: true }), txt(" drawn (with a fixed seed) from the scored corpus. Because the corpus is roughly 40–50% zero-gated, a sizeable share of your ratings will be of tasks the LLM gated to 0 — and you'll judge whether you agree they really should be zero — while the rest spread across the non-zero range in proportion to how often each score actually occurs.")]));
children.push(p([txt("You do "), txt("not", { bold: true }), txt(" see the LLM scores while rating. Each rater works blind.")]));

// 2. CONSTRUCT (verbatim)
children.push(h1("2. The construct you are measuring"));
children.push(callout([
    [txt("Verbatim-parity note. ", { bold: true }), txt("The construct below, the disambiguation rule (§3), and the four criterion definitions and anchors (§4) are reproduced word-for-word from the system prompt given to GPT-4o. You and the model judge against identical wording, so any disagreement reflects genuine human-vs-model judgement, not a difference in instructions. The model is given only these definitions and anchors; the worked examples in §5 are additional calibration for human raters and are not shown to the model.")],
]));
children.push(p("You are evaluating whether current frontier Foundation Models — large language models (LLMs), vision-language models (VLMs), and multimodal generative systems — can substitute for the human worker on a given occupational task at human-equivalent or better proficiency."));
children.push(p([txt("You are NOT evaluating:", { bold: true })]));
children.push(bullet("Robotics, autonomous vehicles, or any AI requiring physical embodiment, actuators, or real-world sensors. These are out of scope."));
children.push(bullet("AI augmentation where the human worker remains required."));
children.push(bullet("Whether workers will actually lose their jobs (regulation, liability, and deployment cost are out of scope)."));
children.push(bullet("Future or projected AI capabilities — evaluate against current frontier Foundation Models only, as they exist today."));

// 3. DISAMBIGUATION (verbatim)
children.push(h1("3. The disambiguation rule (read carefully — this is the load-bearing rule)"));
children.push(p("O*NET task descriptions often do not specify implementation context. When a task could plausibly be performed using digital tools in a contemporary workplace, evaluate it under that digital implementation. This rule resolves ambiguity for Criterion 1 (Information Sufficiency); it does not change the other three criteria."));
children.push(p([txt("Illustration (for raters; not part of the model's prompt): \"Monitor patient vitals\" could mean physical bedside observation or remote review of a digital telemetry dashboard; \"review financial documents\" could mean paper files or an electronic system. Where a digital implementation is plausible, evaluate that one.", { italics: true, color: COLORS.muted })]));

// 4. THE FOUR CRITERIA (verbatim)
children.push(h1("4. The four criteria (v3.2)"));
children.push(p("You will score the task on FOUR independent criteria, each on a 0 / 1 / 2 scale. The criteria are deliberately distinct: each captures a different reason a task might resist AI substitution. Score each criterion ONLY for the property it names, and do not let your judgement on one criterion leak into another. Each criterion states explicitly what it is NOT about — respect those boundaries."));
children.push(p("The examples in each criterion illustrate the underlying principle; they are NOT a lookup table. Score every task by the criterion's definition. A task that resembles an example on the surface but differs in the underlying property must be scored by the property, not the resemblance. A task unlike any example is scored from the definition alone."));

children.push(h2("Criterion 1 — Information Sufficiency"));
children.push(blockquote("Can the task be completed using only information that can be received and acted on digitally (text, images, audio, structured data), with no requirement for real-time physical presence, manipulation of physical objects, or embodied sensory perception?"));
children.push(p([txt("This is the ONLY criterion that judges physical vs. digital. The other three assume the task is digitally accessible and judge different barriers — do not re-judge physicality in them.")]));
children.push(scoreTable([
    ["Score", "Meaning"],
    ["0", "Fundamentally requires physical presence, manual manipulation, or real-time embodied sensing. Example: positioning and welding steel beams."],
    ["1", "Mostly digital but with a genuine physical component that cannot be separated out. Example: diagnosing a machine fault that needs both remote telemetry and a hands-on inspection."],
    ["2", "Completable entirely through digital information and outputs. Example: reconciling figures in a financial spreadsheet."],
], { colWidths: [800, 8226] }));

children.push(h2("Criterion 2 — Objective Verifiability"));
children.push(blockquote("Does the task have a clear, objective standard of success — a checkable correct answer, a testable output, or measurable criteria — as opposed to success being a matter of subjective judgement, taste, or opinion?"));
children.push(p([txt("This is NOT about whether the output is digital or physical (Criterion 1 owns that). A fully digital output can be entirely subjective. Judge only: can you objectively determine whether the result is correct?")]));
children.push(scoreTable([
    ["Score", "Meaning"],
    ["0", "Success is inherently subjective or contested — there is no objective right answer. Example: writing an inspiring company mission statement (fluent and digital, but whether it is \"good\" is a matter of opinion)."],
    ["1", "Some objective elements, but success also depends on judgement that reasonable experts could dispute. Example: recommending which of several viable budgets to approve."],
    ["2", "Objectively checkable — there is a correct answer, a testable result, or measurable criteria. Example: translating a document (fidelity is checkable), or extracting figures from invoices."],
], { colWidths: [800, 8226] }));

children.push(h2("Criterion 3 — Contextual Independence"));
children.push(blockquote("Can the task be completed by an agent that has only (a) the task description and (b) general knowledge — OR does it require real-time human interaction (negotiating, persuading, counselling, building trust, reading and responding to people) or organisation-specific tacit knowledge (relationships, internal history, undocumented local context) that a general-purpose model would not possess?"));
children.push(p([txt("This is NOT about physical vs. digital (Criterion 1), and NOT about whether the model could produce the content (Criterion 4). A model might draft an excellent message yet be unable to BE the trusted human in a live negotiation. Judge only: does success require human-relational embedding or insider context? Context that could be written down and supplied — procedures, specifications, files, policies, client requirements — does NOT count as a barrier, because it can be provided to the model; only real-time human interaction or genuinely tacit/undocumented knowledge does.")]));
children.push(scoreTable([
    ["Score", "Meaning"],
    ["0", "Success fundamentally depends on real-time interpersonal interaction, or on insider/relationship/tacit context the model cannot access. Example: counselling a grieving family member."],
    ["1", "Benefits from such context, but a substantial portion could be done from the task description plus general knowledge. Example: preparing a client briefing that draws partly on the firm's prior dealings."],
    ["2", "Self-contained — completable from the task description, any relevant documents, and general knowledge, even if it relies on company-specific procedures or files (which can be supplied). Example: summarising a research report; coding to a documented company style guide."],
], { colWidths: [800, 8226] }));

children.push(h2("Criterion 4 — Capability Match"));
children.push(blockquote("Setting aside the other three criteria, can a current frontier Foundation Model produce the core output of this task at a quality at or above that of an average human worker in the role?"));
children.push(p([txt("Calibration: the benchmark is the AVERAGE HUMAN WORKER, not perfection. A competent human's work is also reviewed and occasionally corrected, so the fact that the model's output would receive normal review does NOT lower the score. A failure mode counts against the score only if it would make the output WORSE than an average human's. Do not lower this score because the task needs a human relationship or insider context — that is Criterion 3.")]));
children.push(p([txt("Before scoring, briefly consider both directions: what about this specific task is tractable for a current frontier Foundation Model, and what about it might make the model's output worse than an average human's. ", {}), txt("(The model records these as two short reasoning notes before it scores; you can simply hold both in mind.)", { italics: true, color: COLORS.muted })]));
children.push(scoreTable([
    ["Score", "Meaning"],
    ["0", "Clearly below average-human quality on the core — frequently wrong, superficial, or a human must essentially redo it. Example: devising a novel mathematical proof."],
    ["1", "Useful but below average-human quality — meaningfully assists, but a human must substantially complete or rework the core. Example: producing a first-draft analysis of a complex, unusual legal case."],
    ["2", "At or above average-human-worker quality on the core, needing no more review than a human's work normally gets. Example: drafting routine business correspondence."],
], { colWidths: [800, 8226] }));

children.push(callout([
    [txt("How the four combine (Design Y) — for your understanding; you do not compute this. ", { bold: true }), txt("A task scores 0 overall if Information Sufficiency = 0 OR Capability Match = 0 (the two \"can AI even attempt it?\" gates). Otherwise the overall score is the average of all four criteria ÷ 2, so Objective Verifiability and Contextual Independence pull the score down without zeroing it. Just score the four criteria; the overall number is derived. It helps to know that a subjective or relationship-heavy digital task lands in the middle, not at zero.")],
]));

// 5. WORKED EXAMPLES
children.push(h1("5. Worked examples"));
children.push(callout([
    [txt("These worked examples are calibration for human raters and are not shown to the model", { bold: true }), txt(" (the model receives only the definitions and anchors in §4). They illustrate the full gradient Design Y produces — including the two cases (subjective and relational) the redesign is specifically about.")],
], COLORS.code));

children.push(h2("Example 1 — Fully exposed (everything aligns)"));
children.push(p([txt("Task: ", { bold: true }), txt("\"Write Python code to extract data from a SQL database based on user-specified queries.\"", { italics: true })]));
children.push(p([txt("Occupation: ", { bold: true }), txt("Data Analyst")]));
children.push(scoreTable([
    ["Criterion", "Score", "Reasoning"],
    ["Information Sufficiency", "2", "Pure text and code; entirely digital."],
    ["Objective Verifiability", "2", "Code either runs and returns the right data or it does not — objectively checkable."],
    ["Contextual Independence", "2", "Self-contained; needs only the query spec and general knowledge."],
    ["Capability Match", "2", "Current models write this kind of code at or above average-analyst quality."],
], { colWidths: [2400, 800, 5826] }));
children.push(p([txt("Overall: 1.0.", { bold: true }), txt(" No gate; all four high.")]));

children.push(h2("Example 2 — Gated (physical)"));
children.push(p([txt("Task: ", { bold: true }), txt("\"Administer intramuscular injections to patients.\"", { italics: true })]));
children.push(p([txt("Occupation: ", { bold: true }), txt("Registered Nurse")]));
children.push(scoreTable([
    ["Criterion", "Score", "Reasoning"],
    ["Information Sufficiency", "0", "Requires real-time physical presence with the patient — no digital implementation."],
    ["Objective Verifiability", "—", "(not reached)"],
    ["Contextual Independence", "—", "(not reached)"],
    ["Capability Match", "0", "No current Foundation Model performs physical actions on a patient."],
], { colWidths: [2400, 800, 5826] }));
children.push(p([txt("Overall: 0 (GATED).", { bold: true }), txt(" Information Sufficiency = 0 is one of the two gates — physical embodiment is a categorical impossibility for a Foundation Model. You can stop scoring once a gate hits 0, though noting Capability Match = 0 too is fine.")]));

children.push(h2("Example 3 — Subjective digital → modulated to the MIDDLE, not gated"));
children.push(p([txt("Task: ", { bold: true }), txt("\"Write an inspiring vision statement for the organization.\"", { italics: true })]));
children.push(p([txt("Occupation: ", { bold: true }), txt("Public Relations Manager")]));
children.push(scoreTable([
    ["Criterion", "Score", "Reasoning"],
    ["Information Sufficiency", "2", "Entirely digital — text in, text out."],
    ["Objective Verifiability", "0", "There is no objective \"correct\" vision statement; whether it is inspiring is a matter of opinion."],
    ["Contextual Independence", "2", "Can be drafted from a description of the organisation and general knowledge."],
    ["Capability Match", "2", "Current models write fluent, polished vision statements at average-human quality."],
], { colWidths: [2400, 800, 5826] }));
children.push(p([txt("Overall: mean(2,0,2,2)/2 = 0.75. ", { bold: true }), txt("Teaching point:", { bold: true }), txt(" the task is subjective (Objective Verifiability = 0) but that does NOT gate it to zero — it modulates it down to 0.75. The AI can genuinely produce the deliverable; subjectivity just means there's no objective standard to certify it against. This is exactly the case the old rubric mishandled.")]));

children.push(h2("Example 4 — Relational digital → modulated low, not gated"));
children.push(p([txt("Task: ", { bold: true }), txt("\"Negotiate contract terms with a vendor.\"", { italics: true })]));
children.push(p([txt("Occupation: ", { bold: true }), txt("Purchasing Manager")]));
children.push(p([txt("Assume a modern setting (negotiation by email / video is plausible, so not physically gated).")]));
children.push(scoreTable([
    ["Criterion", "Score", "Reasoning"],
    ["Information Sufficiency", "2", "Can be conducted digitally (email, video)."],
    ["Objective Verifiability", "1", "Some terms are objective (price, dates), but \"a good deal\" involves disputable judgement."],
    ["Contextual Independence", "0", "Success depends on a real-time human relationship — reading the counterparty, building trust, adapting live."],
    ["Capability Match", "1", "A model can draft strong negotiating positions, but cannot be the trusted human in the live exchange — a human must run the negotiation."],
], { colWidths: [2400, 800, 5826] }));
children.push(p([txt("Overall: mean(2,1,0,1)/2 = 0.5. ", { bold: true }), txt("Teaching point:", { bold: true }), txt(" Contextual Independence = 0 (the relational barrier) pulls the score down to 0.5 without zeroing it — the informational parts (preparing positions, drafting terms) are exposed, the relational part is not. Note we did NOT lower Capability Match because the task needs a relationship — that belongs in Contextual Independence (Criterion 3), not Criterion 4.")]));

// 6. PROCEDURE
children.push(h1("6. Procedure"));
children.push(numbered([txt("Open the rating sheet", { bold: true }), txt(" (a spreadsheet with one row per task, columns for task ID, task text, occupation, and four blank score columns).")]));
children.push(numbered([txt("Read the task and the occupation title", { bold: true }), txt(" carefully.")]));
children.push(numbered([txt("Apply the disambiguation rule", { bold: true }), txt(" if the context is ambiguous.")]));
children.push(numbered([txt("Score each criterion independently", { bold: true }), txt(" on the 0/1/2 scale. Don't let one criterion influence another.")]));
children.push(numbered([txt("Score blind to the LLM and to other raters", { bold: true }), txt(" — do not look at anyone else's scores until all three of us have finished.")]));
children.push(numbered([txt("Flag rather than guess", { bold: true }), txt(" if a task is genuinely too ambiguous to score. We will discuss flagged tasks after the rating session and decide whether to retain or drop them from the analysis.")]));
children.push(numbered([txt("Don't go back and revise", { bold: true }), txt(" earlier ratings based on later ones. Consistency within each rater matters more than internal recalibration.")]));

// 7. TIME AND PACING
children.push(h1("7. Time and pacing"));
children.push(p([txt("Realistic estimate: about "), txt("2–3 minutes per task", { bold: true }), txt(" once you've settled into the rubric, so roughly "), txt("3–5 hours total", { bold: true }), txt(" per rater. Splitting into two or three sessions is fine; just try to keep each session's pacing consistent. Take breaks before fatigue starts to shift your scoring.")]));

// 8. AFTER RATING
children.push(h1("8. After the rating"));
children.push(p("Once all three of us have submitted independent ratings:"));
children.push(bullet([txt("Inter-rater agreement", { bold: true }), txt(" among the three of us is computed using Krippendorff's α (appropriate for three raters on ordinal data).")]));
children.push(bullet([txt("Validity", { bold: true }), txt(" is computed as Cohen's κ between the averaged human rating and the LLM's score, per criterion and on the composite.")]));
children.push(bullet([txt("Both numbers are reported", { bold: true }), txt(", regardless of whether either crosses the 0.60 threshold. The threshold was locked in advance precisely so that the result can be reported transparently rather than reinterpreted post-hoc.")]));
children.push(p("Tasks flagged as \"too ambiguous\" during rating are listed separately in supplementary materials with the reason. They are not used to compute κ."));

children.push(spacer(240));
children.push(p([txt("If anything in this guide is unclear before the rating session begins, raise it and the guide can be revised. Once rating starts, the guide is frozen for that round.", { italics: true, color: COLORS.muted })]));

const doc = new Document({
    creator: "Aaryan Mehta",
    title: "Rater Guide",
    description: "Tier 2 Human Validity Sample",
    styles: {
        default: { document: { run: { font: FONTS.body, size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONTS.heading, size: 36, bold: true, color: COLORS.primary }, paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONTS.heading, size: 28, bold: true, color: COLORS.primary }, paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 1 } },
        ],
    },
    numbering: {
        config: [{ reference: "default-numbering", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }],
    },
    sections: [{
        properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
        footers: { default: new Footer({ children: [new Paragraph({ children: [new TextRun({ text: "Rater Guide — ", size: 18, color: COLORS.muted }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: COLORS.muted })], alignment: AlignmentType.CENTER })] }) },
        children,
    }],
});

const outFile = path.join(__dirname, "Rater_Guide.docx");
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(outFile, buf); console.log(`Wrote: ${outFile}  (${(buf.length / 1024).toFixed(1)} KB)`); });
