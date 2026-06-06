/**
 * build_prompt_change_doc.js
 * ==========================
 * Generates the prompt-change explanation document (v3 -> v3.1) for the supervisors:
 * why we changed the prompt, what failed in the first pilot, a direct v3-vs-v3.1
 * comparison, and the API-cost impact.
 * Output: docs/Prompt_Change_v3_to_v3.1.docx
 */
const path = require("path");
const fs = require("fs");
const docxPath = "C:/Users/aarya/AppData/Roaming/npm/node_modules/docx";
const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
    ShadingType, PageNumber, LevelFormat,
} = require(docxPath);

const C = { primary: "1E3A5F", accent: "2E75B6", muted: "595959", border: "CCCCCC",
            callout: "FFF4CE", code: "F2F2F2", bad: "C0392B", good: "1E7E34" };
const F = { body: "Calibri", head: "Calibri", mono: "Consolas" };

function txt(t, o = {}) { return new TextRun({ text: t, font: o.font || F.body, size: o.size || 22, bold: o.bold || false, italics: o.italics || false, color: o.color || "000000" }); }
function p(c, o = {}) { const r = Array.isArray(c) ? c : [c]; return new Paragraph({ children: r.map(x => typeof x === "string" ? txt(x, o) : x), spacing: { before: o.before || 100, after: o.after || 100, line: 300 }, alignment: o.alignment || AlignmentType.JUSTIFIED }); }
function h1(t) { return new Paragraph({ children: [new TextRun({ text: t, font: F.head, size: 34, bold: true, color: C.primary })], spacing: { before: 420, after: 220 }, heading: HeadingLevel.HEADING_1, pageBreakBefore: true }); }
function h2(t) { return new Paragraph({ children: [new TextRun({ text: t, font: F.head, size: 27, bold: true, color: C.primary })], spacing: { before: 320, after: 160 }, heading: HeadingLevel.HEADING_2 }); }
function bullet(t) { return new Paragraph({ children: typeof t === "string" ? [txt(t)] : t, bullet: { level: 0 }, spacing: { before: 60, after: 60, line: 280 } }); }
function code(t) { return new Paragraph({ children: [new TextRun({ text: t, font: F.mono, size: 18 })], spacing: { before: 40, after: 40 }, shading: { fill: C.code, type: ShadingType.CLEAR }, indent: { left: 300 } }); }
function callout(lines, fill = C.callout) {
    const b = { style: BorderStyle.SINGLE, size: 4, color: C.accent };
    return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
        rows: [new TableRow({ children: [new TableCell({ width: { size: 9360, type: WidthType.DXA },
            borders: { top: b, bottom: b, left: b, right: b }, shading: { fill, type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 200, right: 200 },
            children: lines.map(l => typeof l === "string" ? new Paragraph({ children: [txt(l, { italics: true })], spacing: { before: 70, after: 70 } }) : l) })] })] });
}
function spacer(h = 120) { return new Paragraph({ children: [txt(" ")], spacing: { before: h, after: 0 } }); }
function table(rows, opts = {}) {
    const cw = opts.colWidths || rows[0].map(() => Math.floor(9360 / rows[0].length));
    const tot = cw.reduce((a, b) => a + b, 0);
    const bd = { style: BorderStyle.SINGLE, size: 1, color: C.border };
    const cb = { top: bd, bottom: bd, left: bd, right: bd };
    return new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: cw,
        rows: rows.map((row, idx) => { const isH = idx === 0 && opts.header !== false;
            return new TableRow({ tableHeader: isH, children: row.map((cell, ci) => {
                const arr = Array.isArray(cell) ? cell : [cell];
                return new TableCell({ width: { size: cw[ci], type: WidthType.DXA }, borders: cb,
                    shading: isH ? { fill: C.primary, type: ShadingType.CLEAR } : { fill: idx % 2 === 0 ? "FFFFFF" : "F8F9FA", type: ShadingType.CLEAR },
                    margins: { top: 70, bottom: 70, left: 110, right: 110 },
                    children: arr.map(x => typeof x === "string" ? new Paragraph({ children: [txt(x, { bold: isH, color: isH ? "FFFFFF" : "000000", size: 19 })], spacing: { before: 30, after: 30, line: 250 } }) : x) }); }) }); }) });
}

const ch = [];

// Cover
ch.push(spacer(2200));
ch.push(new Paragraph({ children: [new TextRun({ text: "Rubric Prompt Changes: v3 → v3.1 → v3.2", font: F.head, size: 42, bold: true, color: C.primary })], spacing: { before: 400, after: 200 }, alignment: AlignmentType.CENTER }));
ch.push(new Paragraph({ children: [new TextRun({ text: "Why the first-pilot criteria failed, what we changed, and the cost impact", font: F.head, size: 24, italics: true, color: C.muted })], spacing: { before: 100, after: 400 }, alignment: AlignmentType.CENTER }));
ch.push(spacer(1000));
ch.push(new Paragraph({ children: [txt("Generative AI Exposure Index", { size: 24, bold: true })], alignment: AlignmentType.CENTER }));
ch.push(new Paragraph({ children: [txt("Aaryan Mehta · FLAME University · 03 June 2026", { size: 22 })], alignment: AlignmentType.CENTER, spacing: { before: 80, after: 400 } }));
ch.push(spacer(600));
ch.push(callout([
    "In one line: the first real pilot showed that three of our four scoring criteria were secretly measuring the same thing (\"is the task physical or digital?\"), which flattened the index to essentially two values. We redesigned the four criteria so each measures a distinct, literature-grounded barrier to AI substitution, and changed how they combine. The cost is essentially unchanged. This document explains exactly what happened and what changed.",
]));

// 1. Summary
ch.push(h1("1. Summary"));
ch.push(p("The scoring rubric asks a large language model to rate each occupational task on four criteria. We tested the rubric on a 75-task pilot (cost: ~£0.39). The pilot was a success in that it caught a serious problem cheaply, before the ~£75 full run: the four criteria were not capturing four different things. Three of them collapsed onto a single “physical vs. digital” distinction, and a fourth (capability) was set to an impossible standard, so the index produced almost no useful gradation — every digital task received an identical score."));
ch.push(p("We have redesigned the four criteria (the rubric moves from version v3 to v3.1) so that each one measures a genuinely distinct reason a task might resist AI substitution, with each reason grounded in the established labour-economics literature on automation. We also adjusted how the four scores combine. The next step is a re-pilot (~£0.40) to confirm the redesign works before the full run."));

// 2. Why the change
ch.push(h1("2. Why we changed it: what the first pilot revealed"));
ch.push(p("The pilot scored 75 tasks with the v3 rubric. Three findings, all from the data, showed the criteria were not working:"));

ch.push(h2("Finding 1 — the index collapsed to three values"));
ch.push(p("Across all 75 tasks, the final composite score took only three distinct values:"));
ch.push(table([
    ["Composite score", "Number of tasks", "What they were"],
    ["0.000", "37", "physical tasks"],
    ["0.750", "1", "a single outlier"],
    ["0.875", "37", "every digital task — all identical"],
], { colWidths: [2200, 2200, 4960] }));
ch.push(p("An index that produces essentially two numbers is a physical/digital classifier, not a graded measure of exposure. It cannot distinguish a highly AI-exposed digital task from a mildly exposed one — they all scored 0.875."));

ch.push(h2("Finding 2 — three criteria were measuring the same thing"));
ch.push(p("The statistical correlation between three of the four criteria (Information Sufficiency, Output Verifiability, and Capability Match) was 0.95–0.99 — near-perfect. Reading the model’s own written reasoning showed why. “Output Verifiability” was supposed to ask whether a task’s success can be checked, but the model scored it on whether the output was a digital file or a physical object:"));
ch.push(callout([
    "Budget Analyst task — Output Verifiability reasoning: “the output… is a digital artifact that can be reviewed and verified.”",
    "Brickmason task — Output Verifiability reasoning: “the cut material requires physical inspection to verify.”",
    "",
    "Both are just restating “digital vs. physical” — the exact same axis as Information Sufficiency.",
], C.code));

ch.push(h2("Finding 3 — one criterion did nothing, and another was set impossibly high"));
ch.push(bullet([txt("“Decomposability” did no independent work. ", { bold: true }), txt("Of the 15 tasks where it scored below 2, all 15 were physical tasks (already handled by Information Sufficiency). On every one of the 60 digital tasks it scored a constant 2. Its reasoning conflated “break into steps” with “break into digital steps,” so it too was secretly measuring physicality.")]));
ch.push(bullet([txt("“Capability Match” never once scored 2 — in 75 tasks. ", { bold: true }), txt("The v3 wording required the AI to be reliable enough to use “without a human re-checking every instance.” That is a perfection standard no human meets either, so the model always found some reason to withhold the top score, pinning every digital task to 1.")]));

ch.push(callout([
    "The diagnosis: the four criteria were not independent. Information Sufficiency, Output Verifiability, and Decomposability all collapsed onto “physical vs. digital,” and Capability Match was stuck at 1 for all cognitive work. The root cause was wording that let the model re-derive “physical vs. digital” inside criteria that were meant to measure something else.",
]));

// 3. The redesign
ch.push(h1("3. The redesign: four distinct, literature-grounded barriers"));
ch.push(p("v3.1 rebuilds the four criteria so each captures a different, well-established bottleneck to automation. The grounding matters — these are not invented; they are the barriers the labour-economics literature has identified over two decades."));
ch.push(table([
    ["Criterion (v3.1)", "The barrier it measures", "Literature basis"],
    ["Information Sufficiency (kept)", "Physical / embodiment — AI cannot act on or sense the physical world", "Frey & Osborne (2013) perception–manipulation bottleneck; Autor, Levy & Murnane (2003) non-routine manual"],
    ["Objective Verifiability (was “Output Verifiability”)", "Whether success is objectively checkable vs. a matter of judgement/opinion", "Brynjolfsson, Mitchell & Rock (2018) “clear feedback”; Frey & Osborne creative-intelligence bottleneck"],
    ["Contextual Independence (replaces “Decomposability”)", "Whether the task needs real-time human relationships or insider/tacit context", "Frey & Osborne social-intelligence bottleneck; Deming (2017) social skills; Autor (2015) / Polanyi’s Paradox"],
    ["Capability Match (recalibrated)", "Whether current AI can do the core work at average-human quality", "Eloundou et al. (2023); Brynjolfsson et al. “long reasoning chains”"],
], { colWidths: [2400, 3400, 3560] }));

ch.push(p("Two wording safeguards prevent the criteria from collapsing again: (1) each criterion now states explicitly what it is NOT about, naming the criterion that owns that axis; (2) the examples in each criterion are deliberately chosen to break surface patterns (e.g. “an inspiring mission statement is digital yet subjective” teaches that digital does not mean verifiable), governed by an instruction telling the model to score by the definition rather than by resemblance to an example — a mitigation of the known tendency of examples to bias LLM scoring (Suri et al. 2024)."));

// 4. Aggregation
ch.push(h1("4. How the four scores now combine (“Design Y”)"));
ch.push(p("Previously, a task scored zero overall if any one of the four criteria was zero. With the redesigned criteria this would wrongly lump “subjective” and “relationship-dependent” digital tasks together with “physically impossible” ones. The new rule distinguishes two kinds of criterion:"));
ch.push(bullet([txt("Gates (can AI even attempt it?): ", { bold: true }), txt("Information Sufficiency and Capability Match. If a task is physical, or beyond current AI, the overall score is zero. These are genuine impossibilities.")]));
ch.push(bullet([txt("Modulators (how good is the substitution?): ", { bold: true }), txt("Objective Verifiability and Contextual Independence. These pull the score down without zeroing it — a subjective or relationship-heavy task is partly substitutable, not impossible.")]));
ch.push(p("This produces the gradation the index was missing:"));
ch.push(table([
    ["Example task", "Overall score", "Why"],
    ["Translate a document", "1.00", "digital, checkable, self-contained, AI-capable"],
    ["Draft a generic mission statement", "0.75", "subjective — modulated down, not gated"],
    ["Negotiate vendor contract terms", "0.50", "relationship-dependent — modulated further"],
    ["Administer an injection / lay pipe", "0.00", "physical — gated"],
    ["Devise a novel mathematical proof", "0.00", "beyond current AI — gated"],
], { colWidths: [3400, 1600, 4360] }));

// 5. Direct comparison
ch.push(h1("5. Direct comparison of the two prompts"));
ch.push(p("Criterion by criterion, here is exactly what changed."));

ch.push(h2("Criterion 1 — Information Sufficiency"));
ch.push(table([
    ["v3", "v3.1"],
    ["“Does completing this task require only information that could be provided in text, images, or structured data — no physical presence?”", "Same core question, kept because it worked. Now explicitly labelled the ONLY criterion that judges physical vs. digital, so the others stop re-deriving it."],
], { colWidths: [4680, 4680] }));

ch.push(h2("Criterion 2 — Output Verifiability → Objective Verifiability"));
ch.push(table([
    ["v3 (“Output Verifiability”)", "v3.1 (“Objective Verifiability”)"],
    ["“Is the expected output something that can be verified or evaluated in digital form (text, numbers, images, code)?” — the model read this as “is the output a digital file,” duplicating Criterion 1.", "“Does the task have a clear, objective standard of success — a checkable right answer — vs. success being subjective?” Explicitly NOT about the medium. A digital output can be subjective. This decouples it from physical/digital and makes it vary among digital tasks."],
], { colWidths: [4680, 4680] }));

ch.push(h2("Criterion 3 — Decomposability → Contextual Independence"));
ch.push(table([
    ["v3 (“Decomposability”)", "v3.1 (“Contextual Independence”)"],
    ["“Can the task be expressed as discrete sub-steps?” — almost everything can, so it scored 2 on all digital tasks and did no useful work.", "“Can the task be done from the task description plus general knowledge, or does it need real-time human interaction or insider/tacit context?” Captures the social + tacit-knowledge barrier — the biggest real-world reason cognitive jobs resist automation, which the old rubric missed entirely."],
], { colWidths: [4680, 4680] }));

ch.push(h2("Criterion 4 — Capability Match (recalibrated)"));
ch.push(table([
    ["v3", "v3.1"],
    ["Bar: “reliable enough to use WITHOUT a human re-checking every instance.” An impossible standard — it never scored 2 in 75 tasks.", "Bar: “at or above an AVERAGE HUMAN WORKER, needing no more review than a human’s work normally gets.” A failure mode counts only if it makes the output worse than an average human’s. The top of the scale is reachable again."],
], { colWidths: [4680, 4680] }));

ch.push(h2("Aggregation"));
ch.push(table([
    ["v3", "v3.1 (Design Y)"],
    ["Any criterion = 0 → overall score 0.", "Gate on Information Sufficiency or Capability Match = 0; otherwise average all four ÷ 2, so Objective Verifiability and Contextual Independence modulate rather than gate."],
], { colWidths: [4680, 4680] }));

// 6. Cost
ch.push(h1("6. Effect on API costs"));
ch.push(p("Essentially none. The cost of scoring is driven mostly by the length of the instructions sent with each task (the “system prompt”) and the length of the model’s reply. The redesign changed the wording but not the overall length:"));
ch.push(table([
    ["", "v3", "v3.1"],
    ["System prompt length", "~1,983 tokens", "~1,895 tokens (slightly shorter)"],
    ["Number of criteria / output fields", "4 / 9", "4 / 9 (unchanged)"],
    ["Measured cost per task (pilot)", "~$0.005", "expected ~$0.005 (re-pilot will confirm)"],
    ["Estimated full-run cost (18,796 tasks)", "~$95 (~£75)", "~$95 (~£75) — unchanged"],
], { colWidths: [3360, 3000, 3000] }));
ch.push(p("The redesign is cost-neutral. It also does not change the earlier, larger cost story (the switch from the discounted Batch service to the standard service, forced by the new account’s rate limits) — that remains as previously communicated and accepted."));
ch.push(p([txt("Sunk cost of the diagnosis: ", { bold: true }), txt("the failed v3 pilot cost ~£0.39, and each subsequent re-pilot (v3.1, then v3.2) cost ~£0.40. Catching the criterion problem at the pilot stage, rather than discovering it after the ~£73 full run, is precisely the value of piloting cheaply first.")]));

// 7. v3.1 re-pilot + v3.2 refinement
ch.push(h1("7. The re-pilot result, and a second small fix (v3.1 → v3.2)"));
ch.push(p("The v3.1 re-pilot (same 75 tasks, £0.30) succeeded on every target: the overall score went from three values to seven; Capability Match reached the top score for the first time; the worst correlation problem (Objective Verifiability) fully resolved; and subjective and relationship-dependent digital tasks correctly landed in the middle band instead of being flattened. Three of the four criteria were working as intended."));
ch.push(p("Reading the model’s reasoning, though, surfaced one over-correction in the new Contextual Independence criterion: it was docking a point whenever a task touched any company-specific context — procedures, files, policies — even when that context is simply a document that could be handed to the model. One task’s reasoning literally argued for the top score (“much of the task can be done with general programming knowledge”) and then gave it the middle score. The effect was a mild but systematic under-scoring of routine digital office work — exactly the work most exposed to Generative AI."));
ch.push(p("The fix (v3.2) is deliberately tiny — one clarifying sentence, not a rewrite. It draws the line in the right place: context that could be written down and supplied is not a barrier; only real-time human interaction (negotiation, counselling) or genuinely tacit, undocumented knowledge is. Everything else in the rubric — the other three criteria, the scoring code — is untouched, so the next re-pilot should move only this one criterion."));
ch.push(callout([
    "Contextual Independence — the one sentence added in v3.2:",
    "“Context that could be written down and supplied — procedures, specifications, files, policies, client requirements — does NOT count as a barrier, because it can be provided to the model; only real-time human interaction or genuinely tacit/undocumented knowledge does.”",
], C.code));

// 8. Isolation / reproducibility check
ch.push(h2("Confirming the change was isolated (cheaply) — the result"));
ch.push(p("Because v3.2 changes only one criterion, we confirmed the other three were genuinely untouched — and incidentally checked whether the model gives stable scores when asked again — without paying for a second run. Criteria 1, 2 and 4 have identical wording in v3.1 and v3.2, so we compared their scores in the new run directly against the previous (v3.1) run."));
ch.push(p([txt("The result: ", { bold: true }), txt("Information Sufficiency was identical on all 75 tasks; Objective Verifiability differed on 4; Capability Match on 2 — six small differences out of 225 scores (2.7%), every one of them a single step, and scattered in both directions (some up, some down). That scatter matters: if our edit had leaked into the other criteria it would push them consistently one way, whereas single-step movement in both directions is the fingerprint of ordinary model randomness. Every task kept the same outcome — 37 pass, 38 gated in both versions. Two things are established at once: the model is stable to within about 3% at this setting, and the edit really did touch only Criterion 3.")]));
ch.push(p([txt("On the model's “temperature”: ", { bold: true }), txt("this also answers a question worth asking of any AI-scored study. Even with the randomness setting at its minimum (temperature 0) and a fixed seed, the model is not perfectly repeatable — about 2–3% of individual scores can shift by one step on a re-run, because the provider's back-end can change between calls. Critically, the overall score distribution and every single pass/gate decision stayed put. We record this as a known, bounded limitation rather than a flaw; it is the expected behaviour of a large language model used as a judge.")]));
ch.push(p([txt("Criterion 3 itself moved exactly as intended: ", { bold: true }), txt("thirteen routine digital tasks rose a step (for example “write supporting code for web applications” and “code documents according to company procedures”), while the genuinely relational tasks — patient care, client-facing work, teaching — all stayed at the floor. The only tasks that moved the other way were physical jobs that are gated out anyway, so their Criterion-3 score never reaches the final index.")]));

// 9. Cost
ch.push(h1("8. What happens next, and total cost so far"));
ch.push(p("v3.2 passed its re-pilot: the routine digital tasks rose as predicted, the genuinely relational tasks stayed low, the other three criteria were undisturbed, and the composite kept its full seven-value spread. The prompt is now locked. The next expenditure is the full production run over all 18,796 tasks; no further rubric changes are planned, and any future change would mean re-running the pilot first."));
ch.push(p("Total spent on all testing so far — the smoke test and every pilot iteration (v3, v3.1, v3.2) combined — is about $1.20 (~£0.95). The full production run remains ~£73. Catching each rubric problem at the ~£0.40 pilot stage, rather than after the ~£73 full run, is the entire point of piloting first."));
ch.push(p([txt("Everything here is recorded in the project’s methodology log ", { }), txt("(data_documentation.md, Decision History 5.23–5.26 and Implementation Log 9.6–9.7)", { italics: true }), txt(", with the literature reasoning for each criterion explained in full in Section 3.2.")]));

ch.push(spacer(320));
ch.push(new Paragraph({ children: [txt("End of document.", { italics: true, color: C.muted })], alignment: AlignmentType.CENTER, spacing: { before: 500, after: 200 } }));
ch.push(new Paragraph({ children: [txt("Aaryan Mehta — 03 June 2026 — FLAME University", { italics: true, color: C.muted, size: 20 })], alignment: AlignmentType.CENTER }));

const doc = new Document({
    creator: "Aaryan Mehta", title: "Rubric Prompt Change v3 to v3.1",
    styles: { default: { document: { run: { font: F.body, size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F.head, size: 34, bold: true, color: C.primary }, paragraph: { spacing: { before: 420, after: 220 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F.head, size: 27, bold: true, color: C.primary }, paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 1 } },
        ] },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
        footers: { default: new Footer({ children: [new Paragraph({ children: [new TextRun({ text: "Prompt Change v3 → v3.1 — ", size: 18, color: C.muted }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: C.muted })], alignment: AlignmentType.CENTER })] }) },
        children: ch }],
});
const outFile = path.join(__dirname, "Prompt_Changes_v3_to_v3.2.docx");
Packer.toBuffer(doc).then(b => { fs.writeFileSync(outFile, b); console.log(`Wrote: ${outFile} (${(b.length/1024).toFixed(1)} KB)`); });
