/** Results & Analysis report for the supervisors (16 June 2026). Balanced, detailed. */
const path = require("path"), fs = require("fs");
const docx = require("C:/Users/aarya/AppData/Roaming/npm/node_modules/docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Footer, Header,
        AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, LevelFormat } = docx;

const C = { primary:"1E3A5F", accent:"2E75B6", good:"2E7D32", warn:"B23B3B", muted:"595959", border:"CCCCCC", soft:"F4F7FB", callout:"FFF4CE" };
const F = { body:"Calibri", head:"Calibri", mono:"Consolas" };
const W = 9026;
const t = (s,o={})=>new TextRun({text:s,font:o.mono?F.mono:F.body,size:o.size||21,bold:!!o.bold,italics:!!o.italics,color:o.color||"000000"});
const p = (c,o={})=>new Paragraph({children:Array.isArray(c)?c.map(x=>typeof x==="string"?t(x,o):x):[typeof c==="string"?t(c,o):c],spacing:{before:o.before||90,after:o.after||90,line:288},alignment:o.align||AlignmentType.JUSTIFIED});
const h1=s=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:360,after:160},pageBreakBefore:true,children:[t(s,{size:30,bold:true,color:C.primary})]});
const h2=s=>new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:240,after:120},children:[t(s,{size:24,bold:true,color:C.accent})]});
const bullet=(c)=>new Paragraph({numbering:{reference:"b",level:0},spacing:{before:50,after:50,line:284},children:Array.isArray(c)?c.map(x=>typeof x==="string"?t(x):x):[t(c)]});
const spacer=(h=120)=>new Paragraph({children:[t(" ")],spacing:{before:h,after:0}});
function box(lines,fill){const b={style:BorderStyle.SINGLE,size:4,color:C.accent};
  const ps=lines.map(l=>Array.isArray(l)?new Paragraph({children:l,spacing:{before:60,after:60,line:286}}):new Paragraph({children:[t(l)],spacing:{before:60,after:60}}));
  return new Table({width:{size:W,type:WidthType.DXA},columnWidths:[W],rows:[new TableRow({children:[new TableCell({width:{size:W,type:WidthType.DXA},borders:{top:b,bottom:b,left:b,right:b},shading:{fill:fill||C.callout,type:ShadingType.CLEAR},margins:{top:120,bottom:120,left:160,right:160},children:ps})]})]});}
function table(rows,cw,opts={}){const bd={style:BorderStyle.SINGLE,size:1,color:C.border};const cb={top:bd,bottom:bd,left:bd,right:bd};
  return new Table({width:{size:cw.reduce((a,b)=>a+b),type:WidthType.DXA},columnWidths:cw,rows:rows.map((r,i)=>new TableRow({tableHeader:i===0,children:r.map((cell,j)=>new TableCell({width:{size:cw[j],type:WidthType.DXA},borders:cb,shading:i===0?{fill:C.primary,type:ShadingType.CLEAR}:{fill:i%2?"FFFFFF":C.soft,type:ShadingType.CLEAR},margins:{top:55,bottom:55,left:100,right:100},children:[new Paragraph({alignment:(opts.center&&j>0)?AlignmentType.CENTER:AlignmentType.LEFT,children:[t(String(cell),{size:opts.size||18,bold:i===0,color:i===0?"FFFFFF":"000000"})],spacing:{before:26,after:26,line:244}})]}))}))});}

const ch=[];
// COVER
ch.push(spacer(900));
ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:80},children:[t("Generative AI Exposure Index",{size:40,bold:true,color:C.primary})]}));
ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:160},children:[t("Results & Analysis Report",{size:30,bold:true,color:C.accent})]}));
ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:60},children:[t("From the full production run to the compiled index, its validation, and what it tells us",{size:22,italics:true,color:C.muted})]}));
ch.push(spacer(500));
ch.push(p([t("Prepared for: ",{bold:true}),t("Prof. Manoranjan Dash  ·  Dr. Shreya Mukherjee")],{align:AlignmentType.CENTER}));
ch.push(p([t("Prepared by: ",{bold:true}),t("Aaryan Mehta — FLAME University")],{align:AlignmentType.CENTER}));
ch.push(p([t("Date: ",{bold:true}),t("16 June 2026")],{align:AlignmentType.CENTER}));

// 1. EXEC SUMMARY
ch.push(h1("1. Executive summary"));
ch.push(p([t("Prof. Dash executed the full scoring run on the college API key, scoring all "),t("18,796 O*NET task statements",{bold:true}),t(" with GPT-4o on the locked v3.2 rubric, with zero failures. From that output we compiled the occupation-level Generative AI Exposure Index (923 occupations) and ran the complete validation and analysis programme. This report documents every step since the run completed.")]));
ch.push(p([t("In plain terms: the index is internally coherent and externally credible. ",{bold:true}),t("It is face-valid (clerical and analytical work at the top, physical and care work at the bottom), it agrees with the only comparable published measure of generative-AI exposure (Eloundou et al., Spearman ρ = 0.86), it is corroborated by our own blind human ratings at the composite level (ρ = 0.85), and — most informatively — it correlates negatively with the older, methodologically independent automation measures (industrial robots, computerisation), which is the evidence that it captures something specific to generative AI rather than generic automatability.")]));
ch.push(p([t("Stated without varnish, two things are weaker and are reported as such: ",{bold:true}),t("agreement at the level of the four individual criteria is moderate-to-low (the composite is what is validated, not each component), and the index rests on a single evaluating model (GPT-4o). The first is explained below and is, in large part, intrinsic to the questions the criteria ask; the second is the one genuinely open validation step (a second-model reliability check), which is planned. Neither undermines the headline composite result, but both must be stated honestly in any publication.")]));

// 2. FROM RUN TO INDEX
ch.push(h1("2. From the production run to the compiled index"));
ch.push(h2("2.1  Receiving and verifying the run"));
ch.push(p([t("The run was returned as a progress file (one record per task). Before using it we verified completeness and integrity: all "),t("18,796",{bold:true}),t(" tasks present, every O*NET task ID covered exactly once (no gaps, duplicates, or extra rows), "),t("zero terminal failures and zero content retries",{bold:true}),t(", and every scored row carrying all nine fields (four criterion scores plus their reasoning). The published per-task index was rebuilt directly from this file.")]));
ch.push(p([t("Because the run was executed on a different account from our pilot pool, we could also check reproducibility across accounts. For the 100 tasks common to both, the two runs differed on only "),t("15 of 400 criterion scores (3.8%)",{bold:true}),t(" — consistent with the temperature-0 noise floor we had measured earlier — and on "),t("none of the 100 gate decisions",{bold:true}),t(". The index is therefore stable: it is a property of the tasks and the rubric, not of one machine, account, or session.")]));
ch.push(h2("2.2  How a task becomes a score (the aggregation method)"));
ch.push(p([t("Each task carries four criterion scores (0/1/2): Information Sufficiency (is it physically/digitally doable), Objective Verifiability (is success objectively checkable), Contextual Independence (does it need a real human relationship or insider knowledge), and Capability Match (can a current model produce the output at average-human quality). These combine by the pre-registered "),t("“Design Y”",{bold:true}),t(" rule: a task scores 0 if Information Sufficiency = 0 or Capability Match = 0 (the two “can AI even attempt it?” gates), otherwise the composite is the mean of all four divided by two. The gates encode categorical impossibility (no body; beyond current capability); the other two only modulate.")]));
ch.push(p([t("Occupation scores are the "),t("importance-weighted mean",{bold:true}),t(" of their task composites, using O*NET’s task-importance ratings as weights. Analyst-coded tasks (which lack an importance rating) are given their occupation’s mean importance; the 29 occupations made up entirely of such tasks receive an unweighted mean; six tasks flagged “recommend-suppress” are excluded from weighting. We also report each occupation’s within-occupation dispersion (importance-weighted standard deviation) and a barrier decomposition (what share of its importance-weight is gated by the physical vs. the capability gate, and how far Objective Verifiability and Contextual Independence pull its non-gated tasks down).")]));
ch.push(box([[t("Robustness of the imputation. ",{bold:true}),t("The one judgement call in aggregation is treating analyst-coded tasks as of average importance. Recomputing the entire index without those tasks changes the occupation ranking by essentially nothing — Spearman ρ = 0.9995, mean absolute change 0.0016. The imputation is empirically inconsequential.")]],C.soft));

// 3. THE INDEX
ch.push(h1("3. The occupation-level index"));
ch.push(p([t("The index spans 0 to 0.978 (mean 0.320, median 0.277). No occupation is fully exposed. About 55% of individual tasks are gated to 0 — overwhelmingly physical work — so the distribution has a large mass at the bottom and a long spread above it.")]));
ch.push(h2("3.1  Most and least exposed occupations"));
ch.push(table([
  ["Most exposed","Score","Least exposed (0.00)"],
  ["Bookkeeping, Accounting & Auditing Clerks","0.98","Orderlies"],
  ["Payroll & Timekeeping Clerks","0.92","Stonemasons"],
  ["Insurance Claims & Policy Processing Clerks","0.92","Surgical Assistants"],
  ["Data Entry Keyers","0.90","Agricultural Equipment Operators"],
  ["Logistics Analysts","0.88","Painting/Coating Workers"],
  ["Order Clerks / Correspondence Clerks","0.87","Carpet & Floor Layers"],
  ["Medical Records Specialists","0.87","Prosthodontists"],
],[3700,900,4426],{size:17}));
ch.push(p([t("The ordering is what the task-based literature would predict, and is a basic face-validity check: routine cognitive and clerical work is most substitutable; physically embodied and hands-on care work is least. The presence of skilled physical professions (surgeons, prosthodontists) at the floor reflects the design choice that physical embodiment gates a task regardless of its cognitive sophistication.",{})]));
ch.push(h2("3.2  By sector (SOC major group)"));
ch.push(table([
  ["Most-exposed sectors","Mean","Least-exposed sectors","Mean"],
  ["Computer & Mathematical","0.70","Construction & Extraction","0.08"],
  ["Office & Administrative Support","0.66","Food Preparation & Serving","0.13"],
  ["Business & Financial Operations","0.58","Farming, Fishing & Forestry","0.13"],
  ["Architecture & Engineering","0.56","Installation/Maintenance/Repair","0.13"],
  ["Legal / Management","0.48 / 0.47","Production","0.14"],
],[3100,900,3326,700],{size:17}));
ch.push(p([t("Computer & Mathematical occupations are the single most-exposed group — a notable inversion of earlier automation waves, which largely spared programming and analytical work. Two groups (Office & Administrative Support; Healthcare Practitioners) show the widest internal spread, meaning they contain both highly exposed and fully protected occupations (e.g., medical-records specialists vs. surgeons).")]));

// 4. VALIDATION
ch.push(h1("4. Validation of the index"));
ch.push(p([t("We validated on three independent fronts, each with thresholds committed in advance to prevent post-hoc interpretation.")]));
ch.push(h2("4.1  Human validity (our blind ratings)"));
ch.push(p([t("Method. ",{bold:true}),t("A simple random sample of 100 tasks (fixed seed) was rated independently and blind by the researcher and Dr. Mukherjee, using a guide whose criterion definitions are reproduced verbatim from the model’s prompt (so any disagreement reflects judgement, not different wording). Prof. Dash was unable to allocate the rating time, so this was completed with two raters rather than three — a documented deviation; the analysis re-runs with his ratings if added later.")]));
ch.push(p([t("Result. ",{bold:true}),t("At the level the index actually publishes — the composite — human agreement is strong: Spearman ρ = 0.85 against the averaged human composite (0.847 with Dr. Mukherjee, 0.710 with the researcher), and the gate (exposed vs. not) agreed on 77–87% of tasks. Agreement at the level of the four individual criteria is weaker (pooled Cohen’s κ 0.30–0.44). This gap is examined in §6.3; in short, the criteria that pose genuinely contestable questions show low agreement even between the two humans (inter-rater α = 0.63), so it is partly a property of the questions, not of the model.")]));
ch.push(box([[t("On two raters. ",{bold:true}),t("With n = 2 (one of whom is the researcher), the inter-rater statistic has wide uncertainty and the independent-human signal rests largely on Dr. Mukherjee — whose agreement with the index is the stronger of the two. This is stated as a limitation, not smoothed over; a third rater would strengthen it.")]],C.soft));
ch.push(h2("4.2  Convergent validity — Eloundou et al. (2023)"));
ch.push(p([t("Method. ",{bold:true}),t("We correlated our occupation scores against Eloundou et al.’s published occupation exposure (their human-labelled “E1” measure), obtained from their public replication data and matched on O*NET-SOC code across all 923 occupations.")]));
ch.push(p([t("Result. ",{bold:true}),t("Spearman ρ = 0.858 (pre-registered threshold ≥ 0.55). This is a strong agreement, but we report it as "),t("consistency rather than independent proof",{italics:true}),t(": both measures use O*NET task text scored by an LLM rubric, so they share method and high agreement is partly expected. Where we diverge is interpretable — we score clerical work higher because our rule assumes modern software (matching their separate “with-tools” measure at ρ = 0.87), and we protect relational/care work more because we model it explicitly.")]));
ch.push(h2("4.3  Discriminant validity — Webb (2020) and older measures"));
ch.push(p([t("Method. ",{bold:true}),t("If the index measures generative-AI exposure specifically, it should agree with the other GenAI measure (Eloundou) and "),t("disagree",{italics:true}),t(" with measures of earlier automation. We correlated against Webb’s (2020) patent-based exposure to the pre-LLM AI/ML wave, his robot and software measures, and Frey-Osborne computerisation — all built by entirely different methods (patent text, expert surveys).")]));
ch.push(table([
  ["Comparator","Method","ρ with our index","Reading"],
  ["Eloundou E1 (human)","O*NET + LLM rubric","+0.858","convergent (same construct)"],
  ["Webb – AI (patents)","patent text","+0.176","weak — different wave"],
  ["Webb – software","patent text","−0.171","negative"],
  ["Webb – robots","patent text","−0.637","strongly negative (manual)"],
  ["Frey-Osborne","expert survey","−0.235","negative"],
],[2300,1900,1500,3326],{size:16}));
ch.push(p([t("The pre-registered discriminant gap — ρ(Eloundou) minus ρ(Webb-AI) — is "),t("0.69",{bold:true}),t(" (threshold ≥ 0.15). This is the most informative validation result, because the discriminant comparators share none of our machinery: that our index points the opposite way from robot and computerisation exposure, measured from patents and surveys, is genuine external evidence that it captures generative-AI substitution rather than generic automatability. (One comparator, Brynjolfsson’s machine-learning suitability index, came out mildly negative at −0.16 rather than the moderate-positive we had expected; it measures supervised-ML/perception suitability, which includes physical work we gate out, so it behaved as a discriminant. We report this as it is, not as a pass.)")]));

// 5. REPRODUCIBILITY
ch.push(h1("5. Reproducibility: what the model adds over cheap text features"));
ch.push(p([t("Method. ",{bold:true}),t("We embedded every task’s text with a sentence-transformer model and tested how well the LLM’s scores can be predicted from the embeddings alone (a regression). The question: is the expensive LLM doing genuine reasoning, or mostly sophisticated keyword-matching a cheap model could replicate?")]));
ch.push(p([t("Result. ",{bold:true}),t("At the task level, embeddings recover R² ≈ 0.62 of the composite — the “mixed” outcome: roughly 60% of the per-task signal is in the surface text, and ~40% requires context the embeddings cannot see. Reading the residuals, that 40% is concretely the model "),t("resolving physical/digital ambiguity the wording disguises",{bold:true}),t(" — scoring “monitor gauges” or “mark frames” as exposed (digital despite physical-sounding words) and “scan records into electronic format” as gated (a physical action behind clerical words). At the occupation level the embedding model reaches ρ = 0.96 with the index — but this is "),t("distillation, not redundancy",{italics:true}),t(": the regression is trained on the LLM’s own labels and cannot exist without first running the LLM. The honest reading is that the index, once built, can be cheaply extended to new tasks or O*NET versions — not that the LLM was unnecessary. Notably, Contextual Independence is the least text-predictable criterion (R² 0.46), consistent with it being the most reasoning-dependent and least measurable dimension (§6.3).")]));

// 6. WHAT IT TELLS US
ch.push(h1("6. What the results tell us"));
ch.push(h2("6.1  Generative AI inverts the skill-bias of past automation"));
ch.push(p([t("Exposure rises with wages: it correlates "),t("+0.48 with occupation mean wage",{bold:true}),t(" and increases monotonically across wage quintiles (lowest 0.17 → highest 0.45). The contrast is the point — Webb’s robot exposure correlates "),t("−0.49",{bold:true}),t(" with wage. Where industrial automation pressed on low- and middle-wage manual and routine work, generative-AI exposure concentrates in higher-wage cognitive work. Around 21% of US employment sits in high-exposure (≥ 0.6) occupations. This is consistent with Eloundou’s and Webb’s own findings and is the most policy-relevant result.")]));
ch.push(h2("6.2  The protective barrier is overwhelmingly the human body"));
ch.push(p([t("Decomposing why each occupation is not fully exposed, "),t("845 of 923 (92%) are protected primarily by physical embodiment",{bold:true}),t(", not by capability limits or relationships. The “capability frontier” — digital tasks the model judges itself unable to do — is just 39 tasks (0.2%). In other words, the model believes it can attempt almost all digital work; what stands between it and most occupations is the requirement for a physical presence. This has a clear forward-looking implication: that moat erodes as robotics and tele-operation advance, and a band of 427 tasks we identify are “embodiment-only-protected” — cognitively tractable work shielded only by an in-person convention (e.g., classroom teaching, on-site client consultation). This directly motivates Part 2.")]));
ch.push(h2("6.3  The relational/tacit barrier is intrinsically hard to measure — and that is itself a finding"));
ch.push(p([t("The Contextual Independence criterion — “does this need a real human relationship or tacit insider knowledge?” — is, on three independent measures, the least measurable of the four: lowest agreement between the two human raters (α 0.40), lowest agreement between humans and the model (κ 0.18), and lowest predictability from text (R² 0.46). We argue this is not a wording flaw but a substantive result. It operationalises the social-intelligence / tacit-knowledge bottleneck that the automation literature (Autor 2015 on Polanyi’s Paradox; Frey & Osborne 2013; Deming 2017) identifies as the hardest to formalise. Whether a task truly requires a human relationship is a question without ground truth, so reasonable people — and a model — disagree. A criterion measuring an immeasurable construct should look immeasurable. Crucially, our design "),t("isolates",{italics:true}),t(" this dimension instead of folding it into one number (as single-label measures do), which is exactly what lets us see and report it: the frontier of non-automatability is, by its nature, the frontier of non-measurability.")]));

// 7. LIMITATIONS
ch.push(h1("7. Limitations, stated plainly"));
ch.push(p([t("These are real, and most are constraints the entire task-based exposure literature shares and has not solved. We state each, why it is not disqualifying, and how we position it.")]));
ch.push(table([
  ["Limitation","Position"],
  ["Single evaluating model (GPT-4o)","The one genuinely open item. Universal to LLM-as-judge work (NBER WP 35110). Addressed next by a second-model (Claude) reliability check; until then, claims are framed as 'GPT-4o-assessed'."],
  ["Weak criterion-level agreement","The composite is validated, not each criterion. The weak criteria pose genuinely contestable questions (low even between humans). Report the barrier decomposition as 'constraint pressure', not certified attribution."],
  ["Capability Match is a self-assessment","The feared over-confidence did not appear — the model was if anything more conservative than the human raters (a bounded, exposure-understating direction)."],
  ["Substitution only (ignores augmentation)","A deliberate scope choice for construct clarity; augmentation is a separate, broader question. Stated explicitly, not hidden."],
  ["Over half of tasks gate to 0","Inherent to a physical/digital cut; we recover sub-structure via the latent-task analyses (frontier and embodiment-only tasks)."],
  ["Occupation = weighted mean of tasks","Ignores task interdependence; no published index corrects for this (Autor 2013)."],
],[2700,6326],{size:16}));

// 8. PUBLICATION STANDPOINT
ch.push(h1("8. Publication standpoint"));
ch.push(p([t("Our read, without optimism or pessimism: the work is at a publishable standard for the composite index, with a clear and defensible framing, provided the limitations are stated rather than glossed.")]));
ch.push(p([t("What we would lead with: ",{bold:true}),t("(1) a validated, reproducible, occupation-level generative-AI substitution index built on a transparent, pre-registered four-criterion rubric; (2) the discriminant result — strong agreement with the other GenAI measure and negative agreement with pre-LLM automation — as the central validity evidence; (3) the wage-inversion finding; and (4) two methodological contributions the field does not currently offer: the decomposition into separable barriers (which makes the relational-barrier immeasurability visible and reportable), and the demonstration that the index is cheaply distillable for extension.")]));
ch.push(p([t("What a reviewer will press on, and our answer: ",{bold:true}),t("“you agree with Eloundou because you share method” — conceded, which is why the discriminant test (independent methods) carries the validity claim, not the convergent one; “your criteria don’t validate” — the composite does, and the criterion-level weakness is located in genuinely contested constructs and reported honestly; “it’s one model” — the reliability check is the planned next step and the field has no better standard; “a cheap model reproduces it” — that is distillation of our labels, a contribution, not a refutation. Each objection has a literature-backed response already written into the methodology.")]));
ch.push(p([t("What we should not claim: ",{bold:true}),t("model-independence (before the reliability check), a validated four-way causal attribution of what protects each occupation (report it as pressure), or that “low exposure” means “safe” (we measure substitution, not augmentation or displacement).")]));

// 9. NEXT STEPS
ch.push(h1("9. Next steps"));
ch.push(bullet([t("Second-model reliability check (closes the main open item). ",{bold:true}),t("Score a ~1,800-task sample with Claude on the identical prompt and report inter-model agreement. Needs an Anthropic API key (~$5–15). This is the highest-value remaining step for Part 1.")]));
ch.push(bullet([t("Optional: a broader zero-gate spot-audit ",{}),t("to confirm the small expected rate of interpretation artefacts, and a second embedding model for the reproducibility check.")]));
ch.push(bullet([t("Part 2 — the vulnerability framework. ",{bold:true}),t("Add an Adaptation-Capacity dimension from PIAAC (individual skills/learning data), linked via the BLS occupation crosswalk, to move from “exposure” to a two-dimensional “vulnerability” measure. This is the larger contribution the project is building toward; it requires acquiring the PIAAC microdata.")]));
ch.push(bullet([t("Synthesis write-up ",{}),t("of Part 1 (index + validation + reproducibility + findings) for your review before Part 2 begins.")]));
ch.push(spacer(160));
ch.push(p([t("All numbers, methods, and decisions in this report are recorded in full in the project’s living methodology document (with the per-occupation index, the validation scripts, and the analysis code), available on request.",{italics:true,color:C.muted})]));
ch.push(spacer(200));
ch.push(new Paragraph({alignment:AlignmentType.CENTER,children:[t("Aaryan Mehta  ·  FLAME University  ·  16 June 2026",{italics:true,color:C.muted,size:19})]}));

const doc=new Document({creator:"Aaryan Mehta",title:"GenAI Exposure Index — Results & Analysis Report",
  numbering:{config:[{reference:"b",levels:[{level:0,format:LevelFormat.BULLET,text:"•",alignment:AlignmentType.START,style:{paragraph:{indent:{left:420,hanging:240}}}}]}]},
  styles:{default:{document:{run:{font:F.body,size:21}}},paragraphStyles:[
    {id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,run:{font:F.head,size:30,bold:true,color:C.primary},paragraph:{spacing:{before:360,after:160},outlineLevel:0}},
    {id:"Heading2",name:"Heading 2",basedOn:"Normal",next:"Normal",quickFormat:true,run:{font:F.head,size:24,bold:true,color:C.accent},paragraph:{spacing:{before:240,after:120},outlineLevel:1}}]},
  sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:1440,right:1440,bottom:1440,left:1440}}},
    headers:{default:new Header({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[t("GenAI Exposure Index — Results & Analysis Report",{size:15,italics:true,color:C.muted})]})]})},
    footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[t("Page ",{size:17,color:C.muted}),new TextRun({children:[PageNumber.CURRENT],size:17,color:C.muted}),t("  ·  Confidential — for supervisory review",{size:17,color:C.muted})]})]})},
    children:ch}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync(path.join(__dirname,"GenAI_Exposure_Index_Results_Report.docx"),b);console.log("wrote docx");});
