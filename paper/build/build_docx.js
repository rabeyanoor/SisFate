// Build a submission-style .docx from paper/manuscript.md with figures embedded after their legends.
// Usage: node build_docx.js   (run from paper/build)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, AlignmentType, Footer, PageNumber,
  LineNumberRestartFormat, PageBreak,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const md = fs.readFileSync(path.join(ROOT, "paper", "manuscript.md"), "utf8");
const FIG = path.join(ROOT, "results", "figures", "paper");
const FIGMAP = {
  "Figure 1": "Fig1_design_data.png", "Figure 2": "Fig2_predictability.png", "Figure 3": "Fig3_fitness_confound.png",
  "Figure 4": "Fig4_biology.png", "Figure 5": "Fig5_ceiling.png", "Figure 6": "Fig6_external_clinical.png",
  "Figure 7": "Fig7_schaff_multitreatment.png",
  "Figure 8": "Fig8_control_free.png",
  "Figure S1": "FigS1_typicality.png", "Figure S2": "FigS2_marker_panel.png", "Figure S3": "FigS3_gnn_ablation.png",
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
let inLegends = false, inRefs = false;
for (const block of blocks) {
  const line = block.replace(/\n/g, " ");
  if (line.startsWith("# ")) {
    children.push(new Paragraph({ heading: HeadingLevel.TITLE, alignment: AlignmentType.LEFT, children: runs(line.slice(2)) }));
    continue;
  }
  if (line.startsWith("## ")) {
    const h = line.slice(3);
    inLegends = h === "Figure legends";
    inRefs = h === "References";
    if (inLegends || inRefs) children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(h) }));
    continue;
  }
  if (line.startsWith("### ")) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(line.slice(4)) }));
    continue;
  }
  if (inLegends) {
    const key = (line.match(/^\*\*(Figure S?\d+)\./) || [])[1];
    if (key && FIGMAP[key] && fs.existsSync(path.join(FIG, FIGMAP[key]))) {
      const img = pngSize(path.join(FIG, FIGMAP[key]));
      const width = 620; // px at 96 dpi, ~6.5 in
      children.push(new Paragraph({
        keepNext: true, spacing: { before: 240 },
        children: [new ImageRun({ type: "png", data: img.data, transformation: { width, height: Math.round(width * img.h / img.w) } })],
      }));
    }
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
  const out = path.join(ROOT, "paper", "manuscript.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length, "bytes");
});
