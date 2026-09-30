// Spontom pitch-deck kit: reproduces the Spontom Enterprise proposal style
// (cream canvas, navy/teal/coral cards, green logo chip, sectioned headers, cited footnotes).
// Usage: const kit = require("./deck-kit"); kit.build(content, "out.pptx");
// `content` = { meta: {...}, slides: [{ type: "cover" | "problem" | ..., ...fields }] }
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const C = {
  bg: "F6F1E7", navy: "1B3149", navy2: "2A4A63", teal: "12796D", tealLt: "DCEEE8",
  coral: "E8694A", coralLt: "FBE6DE", yellow: "F3CB7A", card: "FFFDF7", line: "DCD5C5",
  text: "1B3149", gray: "6B6B6B", muted: "8A8A8A", white: "FFFFFF", green: "2E7D3A", tealText: "9ED8CC",
};
const F = "Arial";
const W = 13.333, H = 7.5, MX = 0.66;

function tb(slide, text, o) {
  slide.addText(text, Object.assign({ fontFace: F, color: C.text, margin: 0, valign: "top", isTextBox: true }, o));
}
function box(slide, x, y, w, h, fill, lineColor, radius) {
  slide.addShape(radius === 0 ? "rect" : "roundRect", {
    x, y, w, h, fill: { color: fill }, line: lineColor ? { color: lineColor, width: 0.75 } : { type: "none" },
    ...(radius === 0 ? {} : { rectRadius: radius == null ? 0.12 : radius }),
  });
}
function circle(slide, x, y, d, fill, label, fontSize) {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  if (label != null) tb(slide, String(label), { x, y, w: d, h: d, align: "center", valign: "middle", bold: true, color: C.white, fontSize: fontSize || 12 });
}
function pill(slide, x, y, w, h, fill, text, color, fontSize) {
  box(slide, x, y, w, h, fill, null, 0.08);
  tb(slide, text, { x, y, w, h, align: "center", valign: "middle", bold: true, color: color || C.white, fontSize: fontSize || 9, charSpacing: 0.5 });
}

function logoChip(slide, meta, x, y, w, h) {
  box(slide, x, y, w, h, C.green, null, 0);
  slide.addImage({ path: meta.logoPath, x: x + 0.1, y: y + 0.07, w: (h - 0.14) * 1.075, h: h - 0.14 });
  tb(slide, "SPONTOM", { x: x + 0.62, y: y + 0.12, w: w - 0.7, h: 0.16, bold: true, color: C.white, fontSize: 8, charSpacing: 1.5 });
  tb(slide, "ENTERPRISE PRIVATE LIMITED", { x: x + 0.62, y: y + 0.29, w: w - 0.7, h: 0.12, color: C.white, fontSize: 4.5, charSpacing: 0.5 });
}

function frame(pres, meta, s, n) {
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  tb(slide, s.section.toUpperCase(), { x: MX, y: 0.42, w: 8, h: 0.2, bold: true, color: C.teal, fontSize: 9, charSpacing: 2 });
  logoChip(slide, meta, 10.71, 0.22, 1.94, 0.49);
  tb(slide, s.title, { x: MX, y: 0.8, w: 11.9, h: 0.55, bold: true, fontSize: s.titleSize || 30, fit: "shrink" });
  if (s.subtitle) tb(slide, s.subtitle, { x: MX, y: 1.42, w: 11.9, h: 0.25, color: C.gray, fontSize: 12 });
  if (s.footnote) tb(slide, s.footnote, { x: MX, y: 6.86, w: 11.9, h: 0.18, italic: true, color: C.gray, fontSize: 7.5 });
  slide.addShape("line", { x: MX - 0.02, y: 7.14, w: W - 2 * MX + 0.04, h: 0, line: { color: C.line, width: 0.75 } });
  tb(slide, `SPONTOM ENTERPRISE PRIVATE LIMITED  •  ${meta.product.toUpperCase()}`, { x: MX, y: 7.22, w: 6, h: 0.14, color: C.muted, fontSize: 6.5, charSpacing: 1.5 });
  tb(slide, meta.footerRight || "DPIIT RECOGNISED  •  VISAKHAPATNAM", { x: 7.5, y: 7.22, w: 4.7, h: 0.14, align: "right", color: C.muted, fontSize: 6.5, charSpacing: 1.5 });
  tb(slide, String(n), { x: 12.35, y: 7.22, w: 0.32, h: 0.14, align: "right", color: C.muted, fontSize: 6.5 });
  if (s.notes) slide.addNotes(s.notes);
  return slide;
}

// ---------- slide layouts ----------
const L = {};

L.cover = (pres, meta, s) => {
  const slide = pres.addSlide();
  slide.background = { color: C.navy };
  const split = 6.2;
  if (s.image) {
    slide.addImage({ path: s.image, x: split, y: 0, w: W - split, h: H, sizing: { type: "cover", w: W - split, h: H } });
  } else {
    box(slide, split, 0, W - split, H, C.navy2, null, 0);
  }
  box(slide, 0.71, 0.47, 0.84, 0.78, C.green, null, 0.08);
  slide.addImage({ path: meta.logoPath, x: 0.83, y: 0.58, w: 0.6, h: 0.56 });
  tb(slide, "SPONTOM ENTERPRISE PRIVATE LIMITED", { x: 1.75, y: 0.63, w: 4.3, h: 0.2, bold: true, color: C.white, fontSize: 9, charSpacing: 1.5 });
  tb(slide, s.kicker, { x: 1.75, y: 0.9, w: 4.3, h: 0.16, color: "B9C4CF", fontSize: 7 });
  tb(slide, s.product, { x: 0.71, y: 1.55, w: 5.3, h: 1.75, bold: true, color: C.white, fontSize: s.productSize || 40, valign: "top", fit: "shrink" });
  tb(slide, s.tagline, { x: 0.71, y: 3.35, w: 5.2, h: 0.95, bold: true, color: C.yellow, fontSize: 20, fit: "shrink" });
  tb(slide, s.subtitle, { x: 0.71, y: 4.45, w: 5.2, h: 0.62, color: "E4E9EE", fontSize: 12.5, fit: "shrink" });
  (s.pills || []).slice(0, 3).forEach((p, i) => pill(slide, 0.71 + i * 1.5, 5.4, 1.36, 0.34, C.navy2, p.toUpperCase(), "DDE6EC", 7.5));
  tb(slide, s.byline, { x: 0.71, y: 6.55, w: 5.3, h: 0.16, color: "C9D2DA", fontSize: 7.5 });
  tb(slide, s.dateline, { x: 0.71, y: 6.8, w: 5.3, h: 0.14, color: "8FA0B0", fontSize: 6.5 });
  if (s.imageCaption) {
    box(slide, split + 0.25, H - 0.62, W - split - 0.5, 0.36, C.navy, null, 0.06);
    tb(slide, s.imageCaption, { x: split + 0.4, y: H - 0.62, w: W - split - 0.8, h: 0.36, valign: "middle", color: C.white, fontSize: 8.5 });
  }
  if (s.notes) slide.addNotes(s.notes);
};

// Navy story card with 3 stats + 4-step flow with a highlighted gap + focused problem.
L.problem = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  box(slide, 0.67, 1.87, 4.36, 4.63, C.navy, null, 0.1);
  tb(slide, s.card.heading, { x: 1.0, y: 2.25, w: 3.8, h: 0.95, bold: true, color: C.white, fontSize: 21, fit: "shrink" });
  slide.addShape("rect", { x: 1.0, y: 3.35, w: 1.1, h: 0.05, fill: { color: C.coral }, line: { type: "none" } });
  const statColors = [C.tealText, C.tealText, C.yellow];
  s.card.stats.slice(0, 3).forEach((st, i) => {
    const x = 1.0 + i * 1.28;
    tb(slide, st.n, { x, y: 3.7, w: 1.2, h: 0.5, align: "center", bold: true, color: st.color || statColors[i], fontSize: 28, fit: "shrink" });
    tb(slide, st.label, { x, y: 4.25, w: 1.2, h: 0.3, align: "center", bold: true, color: C.white, fontSize: 9, fit: "shrink" });
  });
  tb(slide, s.card.story, { x: 1.0, y: 4.8, w: 3.8, h: 0.9, color: "E4E9EE", fontSize: 12, fit: "shrink" });
  pill(slide, 1.0, 5.85, 1.7, 0.34, C.coral, s.card.pill, C.white, 8);

  const fx = 5.46, fw = 1.49, gap = 0.28;
  s.flow.slice(0, 4).forEach((f, i) => {
    const x = fx + i * (fw + gap);
    box(slide, x, 2.29, fw, 1.47, f.gap ? C.coralLt : C.card, f.gap ? C.coral : C.line, 0.1);
    tb(slide, f.title, { x: x + 0.1, y: 2.55, w: fw - 0.2, h: 0.3, align: "center", bold: true, color: f.gap ? C.coral : C.text, fontSize: 15, fit: "shrink" });
    tb(slide, f.desc, { x: x + 0.1, y: 3.02, w: fw - 0.2, h: 0.55, align: "center", color: C.gray, fontSize: 9.5, fit: "shrink" });
    if (i < 3) tb(slide, "›", { x: x + fw, y: 2.8, w: gap, h: 0.35, align: "center", bold: true, color: C.coral, fontSize: 16 });
  });
  tb(slide, s.focusedLabel || "FOCUSED PROBLEM", { x: fx, y: 4.38, w: 4, h: 0.18, bold: true, color: C.teal, fontSize: 8.5, charSpacing: 2 });
  tb(slide, s.focused, { x: fx, y: 4.85, w: 7.0, h: 0.85, bold: true, fontSize: 21, fit: "shrink" });
  tb(slide, "Consequence", { x: fx, y: 5.95, w: 1.1, h: 0.22, bold: true, color: C.coral, fontSize: 9.5 });
  tb(slide, s.consequence, { x: fx + 1.1, y: 5.93, w: 5.9, h: 0.45, color: C.text, fontSize: 12, fit: "shrink" });
};

// Three numbered cards on the left, a product/output mock card on the right.
L.solution = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  s.steps.slice(0, 3).forEach((st, i) => {
    const y = 1.95 + i * 1.37;
    const hi = st.highlight;
    box(slide, 0.7, y, 5.35, 1.12, hi ? C.tealLt : C.card, hi ? C.teal : C.line, 0.1);
    circle(slide, 0.92, y + 0.19, 0.43, st.coral ? C.coral : C.teal, st.n || String(i + 1).padStart(2, "0"), 10);
    tb(slide, st.title, { x: 1.52, y: y + 0.24, w: 1.75, h: 0.5, bold: true, fontSize: 13, fit: "shrink" });
    tb(slide, st.desc, { x: 3.35, y: y + 0.24, w: 2.55, h: 0.8, color: C.text, fontSize: 10.5, fit: "shrink" });
  });
  const p = s.panel, px = 6.52, pw = 5.98;
  box(slide, px, 1.85, pw, 4.77, C.white, C.navy, 0.06);
  slide.addShape("rect", { x: px, y: 1.85, w: pw, h: 0.64, fill: { color: C.navy }, line: { type: "none" } });
  tb(slide, p.header, { x: px + 0.3, y: 1.85, w: 3.5, h: 0.64, valign: "middle", bold: true, color: C.white, fontSize: 11 });
  if (p.badge) pill(slide, px + pw - 2.05, 2.0, 1.75, 0.34, C.navy2, p.badge.toUpperCase(), C.yellow, 7.5);
  tb(slide, p.title, { x: px + 0.3, y: 2.72, w: pw - 0.6, h: 0.4, bold: true, fontSize: 15, fit: "shrink" });
  const items = p.items.slice(0, 4);
  items.forEach((t, i) => {
    const y = 3.3 + i * 0.52;
    circle(slide, px + 0.3, y, 0.42, C.teal, i + 1, 10);
    tb(slide, t, { x: px + 0.9, y: y + 0.02, w: pw - 1.2, h: 0.4, valign: "middle", fontSize: 10.5, fit: "shrink" });
  });
  if (p.fallback) {
    const y = 3.3 + items.length * 0.52;
    circle(slide, px + 0.3, y, 0.42, C.coral, "↺", 10);
    tb(slide, p.fallback, { x: px + 0.9, y: y + 0.02, w: pw - 1.2, h: 0.4, valign: "middle", bold: true, color: C.coral, fontSize: 10.5, fit: "shrink" });
  }
  slide.addShape("line", { x: px + 0.3, y: 5.9, w: pw - 0.6, h: 0, line: { color: C.line, width: 0.75 } });
  if (p.footer) tb(slide, p.footer, { x: px + 0.3, y: 6.03, w: pw - 2.4, h: 0.38, valign: "middle", bold: true, color: C.teal, fontSize: 10.5, fit: "shrink" });
  if (p.button) pill(slide, px + pw - 1.95, 6.02, 1.65, 0.38, C.coral, p.button.toUpperCase(), C.white, 7.5);
};

// Up to 7-step loop + three tier cards + assumption line.
L.loop = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const steps = s.flow.slice(0, 7), k = steps.length;
  const gap = 0.3, w = (W - 2 * 0.65 - gap * (k - 1)) / k;
  steps.forEach((f, i) => {
    const x = 0.65 + i * (w + gap);
    const hi = s.highlight === i;
    box(slide, x, 2.07, w, 1.52, hi ? C.tealLt : C.card, hi ? C.teal : C.line, 0.1);
    circle(slide, x + 0.14, 2.2, 0.43, i === k - 1 ? C.coral : C.teal, i + 1, 10);
    tb(slide, f.title.toUpperCase(), { x: x + 0.05, y: 2.78, w: w - 0.1, h: 0.25, align: "center", bold: true, fontSize: 11, fit: "shrink" });
    tb(slide, f.desc, { x: x + 0.05, y: 3.12, w: w - 0.1, h: 0.38, align: "center", color: C.gray, fontSize: 8.5, fit: "shrink" });
    if (i < k - 1) tb(slide, "›", { x: x + w, y: 2.55, w: gap, h: 0.3, align: "center", bold: true, color: C.coral, fontSize: 15 });
  });
  const tiers = s.tiers.slice(0, 3), tw = 3.75, tg = 0.3;
  const styles = [
    { fill: C.navy, line: null, pillFill: C.navy2, pillColor: "B9C4CF", text: C.white },
    { fill: C.tealLt, line: C.teal, pillFill: C.teal, pillColor: C.white, text: C.text },
    { fill: C.coralLt, line: C.coral, pillFill: C.coral, pillColor: C.white, text: C.text },
  ];
  tiers.forEach((t, i) => {
    const st = styles[i], x = 0.7 + i * (tw + tg);
    box(slide, x, 4.25, tw, 1.55, st.fill, st.line, 0.08);
    pill(slide, x + 0.25, 4.5, 1.55, 0.34, st.pillFill, t.label.toUpperCase(), st.pillColor, 7);
    tb(slide, t.text, { x: x + 0.25, y: 5.0, w: tw - 0.5, h: 0.65, color: st.text, fontSize: 11, fit: "shrink" });
  });
  if (s.assumption) {
    tb(slide, (s.assumptionLabel || "ASSUMPTION").toUpperCase(), { x: 0.72, y: 6.3, w: 2.0, h: 0.2, bold: true, color: C.teal, fontSize: 8, charSpacing: 1 });
    tb(slide, s.assumption, { x: 2.8, y: 6.24, w: 9.8, h: 0.35, bold: true, fontSize: 12.5, fit: "shrink" });
  }
};

// Image with caption overlay + four people cards + constraint pills.
L.users = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const ix = 0.68, iy = 1.87, iw = 5.03, ih = 4.66;
  if (s.image) slide.addImage({ path: s.image, x: ix, y: iy, w: iw, h: 3.3, sizing: { type: "cover", w: iw, h: 3.3 } });
  else box(slide, ix, iy, iw, 3.3, C.navy2, null, 0);
  slide.addShape("rect", { x: ix, y: iy + 3.3, w: iw, h: ih - 3.3, fill: { color: C.navy }, line: { type: "none" } });
  tb(slide, s.imageLabel.toUpperCase(), { x: ix + 0.3, y: iy + 3.62, w: iw - 0.6, h: 0.2, bold: true, color: C.tealText, fontSize: 10, charSpacing: 1 });
  tb(slide, s.imageCaption, { x: ix + 0.3, y: iy + 3.95, w: iw - 0.6, h: 0.5, bold: true, color: C.white, fontSize: 16, fit: "shrink" });
  s.people.slice(0, 4).forEach((p, i) => {
    const y = 1.88 + i * 1.06, hi = i === 1, last = i === 3;
    box(slide, 6.07, y, 6.52, 0.87, hi ? C.tealLt : C.card, hi ? C.teal : C.line, 0.1);
    circle(slide, 6.28, y + 0.21, 0.43, last ? C.coral : C.teal, String(i + 1).padStart(2, "0"), 10);
    tb(slide, p.name.toUpperCase(), { x: 6.85, y: y + 0.17, w: 1.6, h: 0.22, bold: true, fontSize: 11, fit: "shrink" });
    tb(slide, p.role, { x: 6.85, y: y + 0.47, w: 1.6, h: 0.2, color: C.gray, fontSize: 8.5, fit: "shrink" });
    tb(slide, p.desc, { x: 8.55, y: y + 0.17, w: 3.9, h: 0.6, fontSize: 10, fit: "shrink" });
  });
  tb(slide, (s.constraintsLabel || "CONSTRAINT → DESIGN RESPONSE"), { x: 6.1, y: 6.12, w: 4, h: 0.16, bold: true, color: C.teal, fontSize: 8 });
  (s.constraints || []).slice(0, 3).forEach((c, i) => {
    const x = 6.1 + i * 2.1;
    box(slide, x, 6.37, 1.95, 0.38, C.card, C.line, 0.08);
    tb(slide, c.label.toUpperCase(), { x: x + 0.08, y: 6.4, w: 0.72, h: 0.32, valign: "middle", bold: true, color: C.coral, fontSize: 6.5, fit: "shrink" });
    tb(slide, c.text, { x: x + 0.82, y: 6.4, w: 1.08, h: 0.32, valign: "middle", fontSize: 7.5, fit: "shrink" });
  });
};

// Four step cards + a navy recommendation/outcome panel.
L.journey = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const cw = 2.73, cg = 0.3;
  s.steps.slice(0, 4).forEach((st, i) => {
    const x = 0.68 + i * (cw + cg), hi = st.highlight;
    box(slide, x, 1.92, cw, 1.55, hi ? C.tealLt : C.card, hi ? C.teal : C.line, 0.1);
    tb(slide, st.label.toUpperCase(), { x: x + 0.17, y: 2.14, w: cw - 0.3, h: 0.16, bold: true, color: hi ? C.teal : C.coral, fontSize: 7.5 });
    tb(slide, st.title, { x: x + 0.17, y: 2.47, w: cw - 0.3, h: 0.3, bold: true, fontSize: 12.5, fit: "shrink" });
    tb(slide, st.desc, { x: x + 0.17, y: 2.9, w: cw - 0.3, h: 0.5, fontSize: 9.5, fit: "shrink" });
    if (i < 3) tb(slide, "›", { x: x + cw, y: 2.5, w: cg, h: 0.3, align: "center", bold: true, color: C.coral, fontSize: 15 });
  });
  const p = s.panel;
  box(slide, 0.68, 3.95, 12.03, 2.43, C.navy, null, 0.08);
  tb(slide, (p.kicker || "OUTCOME").toUpperCase(), { x: 0.98, y: 4.26, w: 3, h: 0.16, bold: true, color: C.tealText, fontSize: 8.5, charSpacing: 2 });
  tb(slide, p.headline, { x: 0.98, y: 4.6, w: 3.4, h: 0.9, valign: "bottom", bold: true, color: C.white, fontSize: 20, fit: "shrink" });
  if (p.sub) tb(slide, p.sub, { x: 0.98, y: 5.62, w: 3.4, h: 0.5, color: "D5DDE4", fontSize: 10.5, fit: "shrink" });
  const icons = ["+", "✓", "↗"], iconColors = [C.teal, C.teal, C.coral];
  (p.items || []).slice(0, 3).forEach((t, i) => {
    const x = 4.55 + i * 2.48;
    circle(slide, x, 4.55, 0.44, iconColors[i], icons[i], 11);
    tb(slide, t, { x: x + 0.55, y: 4.53, w: 1.85, h: 0.5, bold: true, color: C.white, fontSize: 11.5, fit: "shrink" });
  });
  if (p.why) {
    tb(slide, (p.whyLabel || "WHY IT MATTERS").toUpperCase(), { x: 4.55, y: 5.62, w: 1.7, h: 0.2, bold: true, color: C.yellow, fontSize: 7.5 });
    tb(slide, p.why, { x: 6.25, y: 5.5, w: 6.2, h: 0.5, color: C.white, fontSize: 11, fit: "shrink" });
  }
};

// Comparison table: header row + rows as cards; last row highlighted (our product).
L.table = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const cols = [{ x: 0.9, w: 2.5 }, { x: 3.1, w: 4.4 }, { x: 7.72, w: 4.8 }];
  s.columns.slice(0, 3).forEach((c, i) => tb(slide, c.toUpperCase(), { x: cols[i].x - 0.18, y: 1.73, w: cols[i].w, h: 0.18, bold: true, color: C.teal, fontSize: 8, charSpacing: 1.5 }));
  const rows = s.rows.slice(0, 5), rh = 0.66, rg = 0.17;
  rows.forEach((r, i) => {
    const y = 2.05 + i * (rh + rg), ours = i === rows.length - 1;
    box(slide, 0.68, y, 12.03, rh, ours ? C.tealLt : (i % 2 ? C.card : "F0ECE3"), ours ? C.teal : C.line, 0.08);
    tb(slide, r[0], { x: 0.9, y: y + 0.08, w: 2.1, h: rh - 0.16, valign: "middle", bold: true, color: ours ? C.teal : C.text, fontSize: 11.5, fit: "shrink" });
    tb(slide, r[1], { x: 3.1, y: y + 0.08, w: 4.4, h: rh - 0.16, valign: "middle", fontSize: 10, fit: "shrink" });
    tb(slide, r[2], { x: 7.72, y: y + 0.08, w: 4.8, h: rh - 0.16, valign: "middle", fontSize: 10, fit: "shrink" });
  });
  if (s.callout) {
    pill(slide, 0.72, 6.39, 1.88, 0.34, C.navy, (s.calloutLabel || "DISTINCTIVE CAPABILITY").toUpperCase(), C.white, 7);
    tb(slide, s.callout, { x: 2.85, y: 6.37, w: 9.8, h: 0.38, valign: "middle", bold: true, fontSize: 14, fit: "shrink" });
  }
};

// Five layered rows + navy panel with bullets + gate/rules card.
L.tech = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  s.rows.slice(0, 5).forEach((r, i) => {
    const y = 1.87 + i * 0.88, hi = r.highlight;
    box(slide, 0.68, y, 7.33, 0.67, hi ? C.tealLt : C.card, hi ? C.teal : C.line, 0.08);
    tb(slide, String(i + 1).padStart(2, "0"), { x: 0.9, y: y + 0.22, w: 0.35, h: 0.16, bold: true, color: C.coral, fontSize: 7.5 });
    tb(slide, r.title.toUpperCase(), { x: 1.35, y: y + 0.18, w: 2.1, h: 0.3, bold: true, fontSize: 11, fit: "shrink" });
    tb(slide, r.desc, { x: 3.55, y: y + 0.12, w: 4.35, h: 0.45, valign: "middle", fontSize: 9.5, fit: "shrink" });
  });
  const nv = s.navy;
  box(slide, 8.38, 1.86, 4.3, 2.2, C.navy, null, 0.08);
  tb(slide, nv.title.toUpperCase(), { x: 8.7, y: 2.1, w: 3.8, h: 0.25, bold: true, color: C.white, fontSize: 12, fit: "shrink" });
  nv.bullets.slice(0, 4).forEach((b, i) => {
    const y = 2.5 + i * 0.33;
    slide.addShape("ellipse", { x: 8.73, y: y + 0.06, w: 0.12, h: 0.12, fill: { color: C.tealText }, line: { type: "none" } });
    tb(slide, b, { x: 8.98, y, w: 3.55, h: 0.26, color: C.white, fontSize: 9.5, fit: "shrink" });
  });
  if (nv.pillLabel) {
    pill(slide, 8.71, 3.68, 0.9, 0.3, C.coral, nv.pillLabel.toUpperCase(), C.white, 6.5);
    tb(slide, nv.pillText, { x: 9.7, y: 3.66, w: 2.85, h: 0.34, valign: "middle", bold: true, color: C.yellow, fontSize: 8.5, fit: "shrink" });
  }
  const g = s.gate;
  box(slide, 8.38, 4.37, 4.3, 1.9, C.card, C.teal, 0.08);
  tb(slide, g.title.toUpperCase(), { x: 8.7, y: 4.62, w: 3.8, h: 0.25, bold: true, color: C.teal, fontSize: 12, fit: "shrink" });
  g.rows.slice(0, 3).forEach((r, i) => {
    const y = 5.08 + i * 0.4;
    tb(slide, r.label, { x: 8.7, y, w: 1.1, h: 0.34, bold: true, color: r.coral ? C.coral : C.text, fontSize: 8.5, fit: "shrink" });
    tb(slide, r.text, { x: 9.9, y, w: 2.65, h: 0.36, fontSize: 8.5, fit: "shrink" });
  });
};

// Private/controls card + do-not-collect card + navy safety list.
L.responsible = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const a = s.left;
  box(slide, 0.68, 1.86, 5.72, 2.03, C.tealLt, C.teal, 0.08);
  pill(slide, 0.95, 2.1, 1.6, 0.34, C.teal, a.pills[0].toUpperCase(), C.white, 7);
  if (a.pills[1]) pill(slide, 2.7, 2.1, 2.9, 0.34, C.navy, a.pills[1].toUpperCase(), "DDE6EC", 7);
  a.rows.slice(0, 2).forEach((r, i) => {
    const y = 2.7 + i * 0.55;
    tb(slide, r.label, { x: 0.95, y: y + 0.05, w: 1.25, h: 0.3, bold: true, fontSize: 10.5, fit: "shrink" });
    tb(slide, r.text, { x: 2.25, y, w: 3.95, h: 0.5, fontSize: 11, fit: "shrink" });
  });
  const d = s.dont;
  box(slide, 0.68, 4.2, 5.72, 1.87, C.coralLt, C.coral, 0.08);
  pill(slide, 0.95, 4.47, 1.6, 0.34, C.coral, d.label.toUpperCase(), C.white, 7);
  d.items.slice(0, 3).forEach((t, i) => {
    const y = 5.0 + i * 0.33;
    slide.addShape("ellipse", { x: 1.0, y: y + 0.05, w: 0.13, h: 0.13, fill: { color: C.coral }, line: { type: "none" } });
    tb(slide, t, { x: 1.28, y, w: 4.95, h: 0.26, bold: true, fontSize: 10.5, fit: "shrink" });
  });
  const sf = s.safety;
  box(slide, 6.73, 1.86, 5.93, 4.21, C.navy, null, 0.08);
  tb(slide, sf.title.toUpperCase(), { x: 7.07, y: 2.12, w: 5, h: 0.3, bold: true, color: C.white, fontSize: 15, fit: "shrink" });
  sf.rows.slice(0, 6).forEach((r, i) => {
    const y = 2.72 + i * 0.54;
    tb(slide, r.label.toUpperCase(), { x: 7.07, y: y + 0.03, w: 1.6, h: 0.3, bold: true, color: i < 3 ? C.yellow : C.tealText, fontSize: 7.5, fit: "shrink" });
    tb(slide, r.text, { x: 8.66, y, w: 3.8, h: 0.46, color: C.white, fontSize: 9.5, fit: "shrink" });
  });
};

// 4-step outcome chain + measure panel + 3 validation gates + ownership card + budget route.
L.outcomes = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const cw = 1.83, cg = 0.27;
  s.chain.slice(0, 4).forEach((c, i) => {
    const x = 0.68 + i * (cw + cg), hi = i === 2;
    box(slide, x, 1.9, cw, 1.6, hi ? C.tealLt : C.card, hi ? C.teal : C.line, 0.1);
    tb(slide, String(i + 1).padStart(2, "0"), { x: x + 0.15, y: 2.14, w: 0.5, h: 0.15, bold: true, color: C.coral, fontSize: 7.5 });
    tb(slide, c.title.toUpperCase(), { x: x + 0.08, y: 2.53, w: cw - 0.16, h: 0.25, align: "center", bold: true, fontSize: 10.5, fit: "shrink" });
    tb(slide, c.desc, { x: x + 0.1, y: 2.95, w: cw - 0.2, h: 0.45, align: "center", color: C.gray, fontSize: 8.5, fit: "shrink" });
    if (i < 3) tb(slide, "›", { x: x + cw, y: 2.5, w: cg, h: 0.3, align: "center", bold: true, color: C.coral, fontSize: 14 });
  });
  const m = s.measure;
  box(slide, 9.15, 1.9, 3.53, 1.6, C.navy, null, 0.08);
  tb(slide, (m.label || "MEASURE WITH").toUpperCase(), { x: 9.43, y: 2.14, w: 3, h: 0.15, bold: true, color: C.tealText, fontSize: 7.5 });
  tb(slide, m.items.slice(0, 4).join("\n"), { x: 9.43, y: 2.45, w: 3.05, h: 0.95, bold: true, color: C.white, fontSize: 9.5, fit: "shrink" });
  tb(slide, (s.gatesLabel || "VALIDATION GATES").toUpperCase(), { x: 0.7, y: 4.02, w: 4, h: 0.16, bold: true, color: C.teal, fontSize: 8 });
  s.gates.slice(0, 3).forEach((g, i) => {
    const x = 0.7 + i * 2.75;
    box(slide, x, 4.38, 2.5, 1.15, C.card, C.line, 0.08);
    circle(slide, x + 0.14, 4.55, 0.43, i === 2 ? C.coral : C.teal, i + 1, 10);
    tb(slide, g.title.toUpperCase(), { x: x + 0.7, y: 4.57, w: 1.72, h: 0.2, bold: true, fontSize: 8.5, fit: "shrink" });
    tb(slide, g.desc, { x: x + 0.7, y: 4.85, w: 1.72, h: 0.6, fontSize: 8, fit: "shrink" });
  });
  if (s.budget) {
    pill(slide, 0.72, 5.94, 1.18, 0.34, C.coral, (s.budget.label || "BUDGET ROUTE").toUpperCase(), C.white, 7);
    tb(slide, s.budget.text, { x: 2.08, y: 5.86, w: 6.6, h: 0.5, valign: "middle", bold: true, fontSize: 11, fit: "shrink" });
  }
  const o = s.ownership;
  box(slide, 9.15, 4.0, 3.53, 2.18, C.tealLt, C.teal, 0.08);
  tb(slide, o.title.toUpperCase(), { x: 9.43, y: 4.23, w: 3, h: 0.25, bold: true, color: C.teal, fontSize: 12, fit: "shrink" });
  o.rows.slice(0, 3).forEach((r, i) => {
    const y = 4.72 + i * 0.47;
    tb(slide, r.label, { x: 9.43, y: y + 0.03, w: 0.85, h: 0.2, bold: true, fontSize: 8.5 });
    tb(slide, r.text, { x: 10.3, y, w: 2.25, h: 0.42, fontSize: 8.5, fit: "shrink" });
  });
};

// Live prototype: up to 2 screenshots + link list + evaluation alignment.
L.live = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  const shots = (s.screens || []).slice(0, 2);
  shots.forEach((sc, i) => {
    const x = 0.68 + i * 3.25;
    box(slide, x, 1.86, 3.05, 2.55, C.white, C.line, 0.06);
    slide.addImage({ path: sc.image, x: x + 0.06, y: 1.92, w: 2.93, h: 2.1, sizing: { type: "cover", w: 2.93, h: 2.1 } });
    tb(slide, sc.caption, { x: x + 0.12, y: 4.07, w: 2.8, h: 0.28, align: "center", bold: true, fontSize: 9, fit: "shrink" });
  });
  box(slide, 0.68, 4.7, 6.3, 1.92, C.navy, null, 0.08);
  tb(slide, (s.linksTitle || "TRY IT").toUpperCase(), { x: 0.98, y: 4.9, w: 5, h: 0.2, bold: true, color: C.tealText, fontSize: 8.5, charSpacing: 2 });
  (s.links || []).slice(0, 4).forEach((l, i) => {
    const y = 5.22 + i * 0.32;
    tb(slide, l.label, { x: 0.98, y, w: 1.6, h: 0.26, bold: true, color: C.yellow, fontSize: 8.5, fit: "shrink" });
    tb(slide, l.url, { x: 2.6, y, w: 4.25, h: 0.26, color: C.white, fontSize: 8.5, fit: "shrink", hyperlink: l.url.startsWith("http") ? { url: l.url } : undefined });
  });
  tb(slide, (s.criteriaTitle || "EVALUATION ALIGNMENT").toUpperCase(), { x: 7.35, y: 1.86, w: 5, h: 0.2, bold: true, color: C.teal, fontSize: 8.5, charSpacing: 2 });
  (s.criteria || []).slice(0, 5).forEach((c, i) => {
    const y = 2.2 + i * 0.88;
    box(slide, 7.33, y, 5.35, 0.74, i === 0 ? C.tealLt : C.card, i === 0 ? C.teal : C.line, 0.08);
    tb(slide, c.weight, { x: 7.48, y: y + 0.12, w: 0.8, h: 0.5, valign: "middle", align: "center", bold: true, color: C.coral, fontSize: 17, fit: "shrink" });
    tb(slide, c.label.toUpperCase(), { x: 8.4, y: y + 0.1, w: 4.1, h: 0.2, bold: true, fontSize: 8.5, fit: "shrink" });
    tb(slide, c.how, { x: 8.4, y: y + 0.32, w: 4.15, h: 0.36, fontSize: 8.5, fit: "shrink" });
  });
};

// Numbered references as cards (up to 4 per slide).
L.references = (pres, meta, s, n) => {
  const slide = frame(pres, meta, s, n);
  s.refs.slice(0, 4).forEach((r, i) => {
    const y = 1.86 + i * 1.22;
    box(slide, 0.7, y, 12.0, 1.02, C.card, C.line, 0.08);
    tb(slide, `[${r.n}]`, { x: 0.92, y: y + 0.28, w: 0.55, h: 0.25, bold: true, color: i % 2 ? C.teal : C.coral, fontSize: 13 });
    tb(slide, r.title, { x: 1.52, y: y + 0.24, w: 3.1, h: 0.45, bold: true, fontSize: 13, fit: "shrink" });
    tb(slide, r.desc, { x: 4.7, y: y + 0.22, w: 6.4, h: 0.5, fontSize: 10, fit: "shrink" });
    if (r.url) tb(slide, (r.tag || "OPEN SOURCE") + " ↗", { x: 10.4, y: y + 0.72, w: 2.1, h: 0.18, align: "right", bold: true, color: "1565C0", underline: { style: "sng" }, fontSize: 7.5, hyperlink: { url: r.url } });
    else if (r.tag) tb(slide, r.tag.toUpperCase(), { x: 10.4, y: y + 0.72, w: 2.1, h: 0.18, align: "right", bold: true, color: C.coral, fontSize: 7.5 });
  });
};

async function build(content, outPath) {
  const meta = Object.assign({ logoPath: path.join(__dirname, "assets", "spontom-mark.png") }, content.meta);
  if (!fs.existsSync(meta.logoPath)) throw new Error("logo not found: " + meta.logoPath);
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Spontom Enterprise Private Limited";
  pres.company = "Spontom Enterprise Private Limited";
  pres.title = `${meta.product}: ${meta.title || "pitch deck"}`;
  content.slides.forEach((s, i) => {
    const fn = L[s.type];
    if (!fn) throw new Error(`unknown slide type "${s.type}" (slide ${i + 1})`);
    fn(pres, meta, s, i + 1);
  });
  await pres.writeFile({ fileName: outPath });
  return outPath;
}

module.exports = { build, layouts: Object.keys(L), colors: C };
