/**
 * build_prompt_pdf.js
 * ===================
 * Renders the EXACT system prompt + user message + request configuration that is
 * sent to GPT-4o for every task, from docs/_prompt_payload.json (extracted
 * directly from src/rubric_prompt.py and src/03_score_tasks.py). The system
 * prompt is rendered verbatim in a monospace code block so there is no ambiguity
 * that it is the literal text. Output: docs/LLM_Prompt_Exact_v3.2.docx
 */
const path = require("path");
const fs = require("fs");
const docxPath = "C:/Users/aarya/AppData/Roaming/npm/node_modules/docx";
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Footer,
    AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber } = require(docxPath);

const C = { primary: "1E3A5F", accent: "2E75B6", muted: "595959", border: "CCCCCC", code: "F4F5F7" };
const F = { body: "Calibri", head: "Calibri", mono: "Consolas" };
const CONTENT = 9026;
const payload = JSON.parse(fs.readFileSync(path.join(__dirname, "_prompt_payload.json"), "utf-8"));

function txt(t, o = {}) { return new TextRun({ text: t, font: o.font || F.body, size: o.size || 22, bold: !!o.bold, italics: !!o.italics, color: o.color || "000000" }); }
function p(c, o = {}) { const r = Array.isArray(c) ? c : [c]; return new Paragraph({ children: r.map(x => typeof x === "string" ? txt(x, o) : x), spacing: { before: o.before || 100, after: o.after || 100, line: 290 }, alignment: o.align || AlignmentType.LEFT }); }
function h1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text: t, font: F.head, size: 30, bold: true, color: C.primary })] }); }

// Render text verbatim as a monospace "code block": one shaded cell, one
// paragraph per source line (blank lines preserved), nothing reflowed.
function codeBlock(text, size = 17) {
    const lines = text.split("\n");
    const paras = lines.map(line => new Paragraph({
        spacing: { before: 0, after: 0, line: 250 },
        children: [new TextRun({ text: line.length ? line : " ", font: F.mono, size })],
    }));
    const b = { style: BorderStyle.SINGLE, size: 2, color: C.border };
    return new Table({
        width: { size: CONTENT, type: WidthType.DXA }, columnWidths: [CONTENT],
        rows: [new TableRow({ children: [new TableCell({
            width: { size: CONTENT, type: WidthType.DXA },
            borders: { top: b, bottom: b, left: b, right: b },
            shading: { fill: C.code, type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 160, right: 160 },
            children: paras,
        })] })],
    });
}
function kvTable(rows) {
    const cw = [3000, 6026];
    const b = { style: BorderStyle.SINGLE, size: 1, color: C.border };
    const cb = { top: b, bottom: b, left: b, right: b };
    return new Table({ width: { size: CONTENT, type: WidthType.DXA }, columnWidths: cw,
        rows: rows.map((r, i) => new TableRow({ children: r.map((cell, ci) => new TableCell({
            width: { size: cw[ci], type: WidthType.DXA }, borders: cb,
            shading: { fill: i % 2 ? "F8F9FA" : "FFFFFF", type: ShadingType.CLEAR },
            margins: { top: 60, bottom: 60, left: 110, right: 110 },
            children: [new Paragraph({ children: [ci === 0 ? txt(cell, { bold: true, size: 20 }) : txt(cell, { font: F.mono, size: 20 })] })],
        })) })),
    });
}

const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 60 }, children: [new TextRun({ text: "Exact LLM Prompt", font: F.head, size: 44, bold: true, color: C.primary })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Generative AI Exposure Index — locked rubric v3.2", font: F.head, size: 24, italics: true, color: C.muted })] }));
ch.push(p([txt("This document reproduces, verbatim, the exact system prompt and user message sent to GPT-4o for every one of the 18,796 task statements, together with the request configuration. It is generated directly from the project source files (", {}), txt("src/rubric_prompt.py", { font: F.mono, size: 20 }), txt(", ", {}), txt("src/03_score_tasks.py", { font: F.mono, size: 20 }), txt("), so it is guaranteed to match what the model actually receives. The same wording is reproduced in the Rater Guide so that the human validity raters and the model judge against identical instructions.", {})]));
ch.push(p([txt("Aaryan Mehta · FLAME University · 6 June 2026", { italics: true, color: C.muted, size: 20 })], { align: AlignmentType.CENTER, before: 40, after: 120 }));

ch.push(h1("Request configuration"));
ch.push(kvTable([
    ["Model", String(payload.config.model)],
    ["Temperature", String(payload.config.temperature)],
    ["Seed", String(payload.config.seed)],
    ["Max output tokens", String(payload.config.max_tokens)],
    ["Response format", String(payload.config.response_format)],
    ["Prompt cache key", String(payload.config.prompt_cache_key)],
    ["System prompt size", "~" + payload.sys_tokens_approx.toLocaleString() + " tokens"],
]));

ch.push(h1("System prompt (verbatim)"));
ch.push(p([txt("Sent as the ", {}), txt("system", { font: F.mono, size: 20 }), txt(" message on every request:", {})], { after: 60 }));
ch.push(codeBlock(payload.system_prompt));

ch.push(h1("User message (verbatim — example with one task filled in)"));
ch.push(p([txt("Sent as the ", {}), txt("user", { font: F.mono, size: 20 }), txt(" message; only the task text and occupation title change per task:", {})], { after: 60 }));
ch.push(codeBlock(payload.user_example));

ch.push(h1("Structured output (enforced by the API)"));
ch.push(p("The model must return a JSON object with exactly these nine fields, in this order; each reasoning field is one sentence and each score field is an integer in {0, 1, 2}. The structure is enforced by the API's strict structured-output mode, so malformed output is impossible by construction:"));
ch.push(codeBlock(payload.schema_fields.map((f, i) => (i + 1) + ". " + f).join("\n"), 18));

const doc = new Document({
    creator: "Aaryan Mehta", title: "Exact LLM Prompt — GenAI Exposure Index v3.2",
    styles: { default: { document: { run: { font: F.body, size: 22 } } },
        paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: F.head, size: 30, bold: true, color: C.primary }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } }] },
    sections: [{
        properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
        footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [txt("Exact LLM Prompt (v3.2) · Page ", { size: 18, color: C.muted }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: C.muted })] })] }) },
        children: ch,
    }],
});
const outFile = path.join(__dirname, "LLM_Prompt_Exact_v3.2.docx");
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(outFile, buf); console.log(`Wrote: ${outFile}  (${(buf.length / 1024).toFixed(1)} KB)`); });
