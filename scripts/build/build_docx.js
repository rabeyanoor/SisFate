// Build a submission-style .docx from a markdown file in new_paper/. Each figure is embedded where its legend
// sits in the markdown (right after the paragraph that first cites it), image first, legend underneath.
// Usage: node build_docx.js          the whole paper in one file: paper.md, then supplementary_information.md
//                                     on a new page -> new_paper/hi.docx
//        node build_docx.js <name>   a single new_paper/<name>.md -> new_paper/<name>.docx
// Environment: GB=1 Genome Biology layout (double spacing, no page breaks); NOFIG=1 legends only, no images
// (the journal takes figures as separate files). Web links (https://...) become clickable hyperlinks.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, AlignmentType, Footer, PageNumber,
  LineNumberRestartFormat, PageBreak, ExternalHyperlink,
} = require("docx");
const GB = process.env.GB === "1";
const NOFIG = process.env.NOFIG === "1";

const ROOT = path.resolve(__dirname, "..", "..");
const NAME = process.argv[2] || "hi";
const read = (n) => fs.readFileSync(path.join(ROOT, "new_paper", n + ".md"), "utf8");
const md = NAME === "hi" ? read("paper") + "\n\n" + read("supplementary_information") : read(NAME);
const FIG = path.join(ROOT, "results", "figures", "paper");
const FIGMAP = {
  "1": "Fig1_design_data.png", "2": "Fig2_predictability.png", "3": "Fig3_fitness_confound.png",
  "4": "Fig4_biology.png", "5": "Fig5_ceiling.png", "6": "Fig6_schaff_multitreatment.png",
  "7": "Fig7_external_clinical.png",
  "S1": "FigS1_gnn_ablation.png", "S2": "FigS2_typicality.png", "S3": "FigS3_marker_panel.png",
  "S4": "FigS4_control_free.png", "S5": "FigS5_simulation.png",
};

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

// TeX math is written as a placeholder run here; docx_math.py then swaps each one for Word's own equation
// markup (OMML) converted by pandoc, so equations stay editable in Word.
const MATH = [];
function mathRun(tex, display, base) {
  MATH.push({ tex, display });
  return new TextRun({ text: `@@MATH${MATH.length - 1}@@`, ...base });
}

// a web link, without trailing punctuation (a closing parenthesis is kept only when the link opened one)
const URL_RE = /https?:\/\/[^\s<>]+/g;
function trimUrl(u) {
  while (/[.,;:]$/.test(u) || (u.endsWith(")") && (u.match(/\(/g) || []).length < (u.match(/\)/g) || []).length)) u = u.slice(0, -1);
  return u;
}
function link(url, base) {
  return new ExternalHyperlink({ link: url, children: [new TextRun({ text: url, ...base, color: "0563C1", underline: {} })] });
}
// plain text with its web links made clickable
function textRuns(text, base) {
  const out = [];
  let last = 0, m;
  URL_RE.lastIndex = 0;
  while ((m = URL_RE.exec(text)) !== null) {
    const u = trimUrl(m[0]);
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    out.push(link(u, base));
    last = m.index + u.length;
    URL_RE.lastIndex = last;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

// inline markdown: $math$, **bold**, *italic*, `code`, ^superscript^ (numbered citations)
function runs(text, base = {}) {
  const out = [];
  const re = /(\$[^$]+\$|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\^[^\s^]+\^)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(...textRuns(text.slice(last, m.index), base));
    const t = m[0];
    if (t.startsWith("$")) out.push(mathRun(t.slice(1, -1), false, base));
    else if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("*")) out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else if (t.startsWith("^")) out.push(new TextRun({ text: t.slice(1, -1), superScript: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(...textRuns(text.slice(last), base));
  return out;
}

const children = [];
const blocks = md.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
let inRefs = false;
for (const block of blocks) {
  const line = block.replace(/\n/g, " ");
  if (line.startsWith("# ")) {
    if (children.length && !GB) children.push(new Paragraph({ children: [new PageBreak()] }));  // supplement starts a new page
    children.push(new Paragraph({ heading: HeadingLevel.TITLE, alignment: AlignmentType.LEFT, children: runs(line.slice(2)) }));
    continue;
  }
  if (line.startsWith("## ")) {
    const h = line.slice(3);
    inRefs = h === "References";
    if (inRefs && !GB) children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(h) }));
    continue;
  }
  if (line.startsWith("### ")) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(line.slice(4)) }));
    continue;
  }
  if (line.startsWith("$$") && line.endsWith("$$")) {  // a displayed equation
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
      children: [mathRun(line.slice(2, -2).trim(), true, {})] }));
    continue;
  }
  // "**Fig. 1 | Title.**" (master), "**Fig. 1** **Title.**" or "**Fig. S1** ..." (Genome Biology)
  const fm = line.match(/^\*\*(Supplementary )?Fig\. (S?)(\d+)(?: \||\*\*)/);
  if (fm) {  // a legend: the figure goes above it, and the legend is set smaller underneath
    const key = (fm[1] || fm[2]) ? "S" + fm[3] : fm[3];
    if (!NOFIG && FIGMAP[key] && fs.existsSync(path.join(FIG, FIGMAP[key]))) {
      const img = pngSize(path.join(FIG, FIGMAP[key]));
      const width = 620; // px at 96 dpi, ~6.5 in
      children.push(new Paragraph({
        keepNext: true, spacing: { before: 240 },
        children: [new ImageRun({ type: "png", data: img.data, transformation: { width, height: Math.round(width * img.h / img.w) } })],
      }));
    }
    children.push(new Paragraph({ spacing: { after: 280, line: GB ? 480 : 276 }, alignment: AlignmentType.JUSTIFIED, children: runs(line, { size: GB ? 22 : 19 }) }));
    continue;
  }
  children.push(new Paragraph({
    spacing: { after: 160, line: GB ? 480 : (inRefs ? 276 : 360) },
    alignment: inRefs ? AlignmentType.LEFT : AlignmentType.JUSTIFIED,
    children: runs(line, inRefs ? { size: 20 } : {}),
  }));
}

const doc = new Document({
  creator: "Rabeya Noor",
  title: "Growth fitness, not drug tolerance, explains most pre-treatment prediction of cancer cell fate",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 32, bold: true }, paragraph: { spacing: { after: 240 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true }, paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, italics: true }, paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      lineNumbers: { countBy: 1, restart: LineNumberRestartFormat.CONTINUOUS },
    },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "new_paper", NAME + ".docx");
  fs.writeFileSync(out, buf);
  fs.writeFileSync(out.replace(/\.docx$/, ".math.json"), JSON.stringify(MATH));
  console.log("wrote", out, buf.length, "bytes,", MATH.length, "equations to convert with docx_math.py");
});
