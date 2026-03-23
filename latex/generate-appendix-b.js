const fs = require("fs");
const path = require("path");

const CSV_PATH = path.join(__dirname, "..", "results", "maei_2026_with_deltas.csv");
const OUT_PATH = path.join(__dirname, "2-mainmatter", "appendices", "appn-occupation-index.tex");

// CSV parser (handles quoted fields)
function parseCSV(filePath) {
  const text = fs.readFileSync(filePath, "utf-8");
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  function parseLine(line) {
    const result = []; let cur = "", inQ = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') { inQ = !inQ; }
      else if (line[i] === ',' && !inQ) { result.push(cur.trim()); cur = ""; }
      else { cur += line[i]; }
    }
    result.push(cur.trim()); return result;
  }
  const headers = parseLine(lines[0]);
  return lines.slice(1).map(line => {
    const vals = parseLine(line); const obj = {};
    headers.forEach((h, i) => { obj[h] = vals[i] || ""; });
    return obj;
  });
}

// Escape LaTeX special characters
function esc(s) {
  return s.replace(/&/g, "\\&")
          .replace(/%/g, "\\%")
          .replace(/#/g, "\\#")
          .replace(/_/g, "\\_");
}

const data = parseCSV(CSV_PATH);
const valid = data
  .filter(r => r.Data_Flag !== "insufficient_data" && r.MAEI_2026_Score !== "")
  .sort((a, b) => parseFloat(b.MAEI_2026_Score) - parseFloat(a.MAEI_2026_Score));

console.log(`Loaded ${valid.length} valid occupations`);

let tex = `\\chapter{Complete MAEI Occupation Index (${valid.length} Occupations)}
\\label{chap:appendix_b}

{\\small
\\begin{longtable}{rlccc}
\\caption{Complete MAEI Occupation Index --- all ${valid.length} scored occupations sorted by MAEI 2026 Score (descending).} \\label{tab:occupation_index} \\\\
\\toprule
\\textbf{\\#} & \\textbf{Occupation} & \\textbf{MAEI 2026} & \\textbf{Delta} & \\textbf{Risk Tier} \\\\
\\midrule
\\endfirsthead
\\multicolumn{5}{c}{\\textit{Table~\\ref{tab:occupation_index} continued from previous page}} \\\\
\\toprule
\\textbf{\\#} & \\textbf{Occupation} & \\textbf{MAEI 2026} & \\textbf{Delta} & \\textbf{Risk Tier} \\\\
\\midrule
\\endhead
\\midrule
\\multicolumn{5}{r}{\\textit{Continued on next page}} \\\\
\\endfoot
\\bottomrule
\\endlastfoot
`;

valid.forEach((row, i) => {
  const rank = i + 1;
  const occ = esc(row.Occupation);
  const score = parseFloat(row.MAEI_2026_Score).toFixed(1);
  const delta = parseFloat(row.Exposure_Delta) >= 0
    ? `+${parseFloat(row.Exposure_Delta).toFixed(2)}`
    : parseFloat(row.Exposure_Delta).toFixed(2);
  const tier = esc(row.Risk_Tier_2026 || "---");
  tex += `${rank} & ${occ} & ${score} & ${delta} & ${tier} \\\\\n`;
});

tex += `\\end{longtable}
}
`;

fs.writeFileSync(OUT_PATH, tex, "utf-8");
console.log(`Written ${OUT_PATH} (${valid.length} rows)`);
