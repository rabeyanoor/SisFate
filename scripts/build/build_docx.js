// Build a submission-style .docx from a markdown file in new_paper/. Each figure is embedded where its legend
// sits in the markdown (right after the paragraph that first cites it), image first, legend underneath.
// Usage: node build_docx.js          the whole paper in one file: manuscript.md, then supplementary_information.md
//                                     on a new page -> new_paper/hi.docx
//        node build_docx.js <name>   a single new_paper/<name>.md -> new_paper/<name>.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, AlignmentType, Footer, PageNumber,
  LineNumberRestartFormat, PageBreak,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const NAME = process.argv[2] || "hi";
const read = (n) => fs.readFileSync(path.join(ROOT, "new_paper", n + ".md"), "utf8");
const md = NAME === "hi" ? read("manuscript") + "\n\n" + read("supplementary_information") : read(NAME);
const FIG = path.join(ROOT, "results", "figures", "paper");
const FIGMAP = {
  "1": "Fig1_design_data.png", "2": "Fig2_predictability.png", "3": "Fig3_fitness_confound.png",
  "4": "Fig4_biology.png", "5": "Fig5_ceiling.png", "6": "Fig6_schaff_multitreatment.png",
  "7": "Fig7_external_clinical.png",
  "8": "Fig8_control_free.png",
  "9": "Fig9_simulation.png",
  "S1": "FigS1_gnn_ablation.png", "S2": "FigS2_typicality.png", "S3": "FigS3_marker_panel.png",
};

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

// inline markdown: **bold**, *italic*, `code`
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("*")) out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const children = [];
const blocks = md.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
let inRefs = false;
for (const block of blocks) {
  const line = block.replace(/\n/g, " ");
  if (line.startsWith("# ")) {
    if (children.length) children.push(new Paragraph({ children: [new PageBreak()] }));  // supplement starts a new page
    children.push(new Paragraph({ heading: HeadingLevel.TITLE, alignment: AlignmentType.LEFT, children: runs(line.slice(2)) }));
    continue;
  }
  if (line.startsWith("## ")) {
    const h = line.slice(3);
    inRefs = h === "References";
    if (inRefs) children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(h) }));
    continue;
  }
  if (line.startsWith("### ")) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(line.slice(4)) }));
    continue;
  }
  const fm = line.match(/^\*\*(Supplementary )?Fig\. (\d+) \|/);
  if (fm) {  // a legend: the figure goes above it, and the legend is set smaller underneath
    const key = fm[1] ? "S" + fm[2] : fm[2];
    if (FIGMAP[key] && fs.existsSync(path.join(FIG, FIGMAP[key]))) {
      const img = pngSize(path.join(FIG, FIGMAP[key]));
      const width = 620; // px at 96 dpi, ~6.5 in
      children.push(new Paragraph({
        keepNext: true, spacing: { before: 240 },
        children: [new ImageRun({ type: "png", data: img.data, transformation: { width, height: Math.round(width * img.h / img.w) } })],
      }));
    }
    children.push(new Paragraph({ spacing: { after: 280, line: 276 }, alignment: AlignmentType.JUSTIFIED, children: runs(line, { size: 19 }) }));
    continue;
  }
  children.push(new Paragraph({
    spacing: { after: 160, line: inRefs ? 276 : 360 },
    alignment: inRefs ? AlignmentType.LEFT : AlignmentType.JUSTIFIED,
    children: runs(line, inRefs ? { size: 20 } : {}),
  }));
}

const doc = new Document({
  creator: "SisFate",
  title: "Sister-cell fate prediction",
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
  console.log("wrote", out, buf.length, "bytes");
});
