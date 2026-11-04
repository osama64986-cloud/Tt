// ═══════════════════════════ إثيريا V1: اللغة العربية داخل ماينكرافت ═══════════════════════════
// ماينكرافت بيدروك يرسم النص من اليسار لليمين وكل حرف بشكله المنفصل (ما يشبك الحروف ولا يقلب الاتجاه).
// فهنا نسوي اللي يسويه أي محرر نصوص:
//   1) التشكيل: كل حرف ياخذ شكله (منفصل/أول/وسط/آخر) من «أشكال العرض ب» U+FE70–FEFF، و«لا» تصير حرف واحد.
//      الحركات (الفتحة والشدة...) تنشال لأن الخط يرسمها بحرف مستقل بمكان غلط.
//   2) الاتجاه: السطر ينقلب (من اليمين لليسار)، والكلمات الإنكليزية والأرقام تبقى بترتيبها، والأقواس تنعكس.
//   3) رموز الألوان (§): كل حرف يحفظ لونه، وبعد القلب نرجع نحط الرموز وين يتغير اللون.
//   4) التقطيع: اللعبة تقطع السطر الطويل من جهة اليسار فيخربط الترتيب، فنقطع إحنا قبل القلب حسب عرض كل مكان.
// والترجمة: tr(s) يدور النص الإنكليزي بالقاموس (AR من lang_ar.js): تطابق كامل، أو قالب بخانات {0} {1}
// (الخانات تترجم هي هم إذا كانت أسماء)، وإذا ما لگى يحاول كل قطعة بين رموز الألوان، وإلا يخليه إنكليزي.

import { AR } from "./lang_ar.js";

// ───────── 1) التشكيل ─────────
// [منفصل، آخر، أول، وسط]. الحروف اللي ما تتصل باللي بعدها (ا د ذ ر ز و ة ى أ إ آ ؤ) عندها شكلين بس، والهمزة شكل واحد.
const FORMS = {
  0x0621: [0xFE80], 0x0622: [0xFE81, 0xFE82], 0x0623: [0xFE83, 0xFE84], 0x0624: [0xFE85, 0xFE86], 0x0625: [0xFE87, 0xFE88],
  0x0626: [0xFE89, 0xFE8A, 0xFE8B, 0xFE8C], 0x0627: [0xFE8D, 0xFE8E], 0x0628: [0xFE8F, 0xFE90, 0xFE91, 0xFE92], 0x0629: [0xFE93, 0xFE94],
  0x062A: [0xFE95, 0xFE96, 0xFE97, 0xFE98], 0x062B: [0xFE99, 0xFE9A, 0xFE9B, 0xFE9C], 0x062C: [0xFE9D, 0xFE9E, 0xFE9F, 0xFEA0],
  0x062D: [0xFEA1, 0xFEA2, 0xFEA3, 0xFEA4], 0x062E: [0xFEA5, 0xFEA6, 0xFEA7, 0xFEA8], 0x062F: [0xFEA9, 0xFEAA], 0x0630: [0xFEAB, 0xFEAC],
  0x0631: [0xFEAD, 0xFEAE], 0x0632: [0xFEAF, 0xFEB0], 0x0633: [0xFEB1, 0xFEB2, 0xFEB3, 0xFEB4], 0x0634: [0xFEB5, 0xFEB6, 0xFEB7, 0xFEB8],
  0x0635: [0xFEB9, 0xFEBA, 0xFEBB, 0xFEBC], 0x0636: [0xFEBD, 0xFEBE, 0xFEBF, 0xFEC0], 0x0637: [0xFEC1, 0xFEC2, 0xFEC3, 0xFEC4],
  0x0638: [0xFEC5, 0xFEC6, 0xFEC7, 0xFEC8], 0x0639: [0xFEC9, 0xFECA, 0xFECB, 0xFECC], 0x063A: [0xFECD, 0xFECE, 0xFECF, 0xFED0],
  0x0641: [0xFED1, 0xFED2, 0xFED3, 0xFED4], 0x0642: [0xFED5, 0xFED6, 0xFED7, 0xFED8], 0x0643: [0xFED9, 0xFEDA, 0xFEDB, 0xFEDC],
  0x0644: [0xFEDD, 0xFEDE, 0xFEDF, 0xFEE0], 0x0645: [0xFEE1, 0xFEE2, 0xFEE3, 0xFEE4], 0x0646: [0xFEE5, 0xFEE6, 0xFEE7, 0xFEE8],
  0x0647: [0xFEE9, 0xFEEA, 0xFEEB, 0xFEEC], 0x0648: [0xFEED, 0xFEEE], 0x0649: [0xFEEF, 0xFEF0], 0x064A: [0xFEF1, 0xFEF2, 0xFEF3, 0xFEF4],
};
const TATWEEL = 0x0640;
const LAM = 0x0644;
const LAM_ALEF = { 0x0622: [0xFEF5, 0xFEF6], 0x0623: [0xFEF7, 0xFEF8], 0x0625: [0xFEF9, 0xFEFA], 0x0627: [0xFEFB, 0xFEFC] };
const isHaraka = (c) => (c >= 0x064B && c <= 0x065F) || c === 0x0670;
const joinsNext = (c) => c === TATWEEL || (FORMS[c] && FORMS[c].length === 4);       // يتصل باللي بعده
const joinsPrev = (c) => c === TATWEEL || (FORMS[c] && FORMS[c].length >= 2);        // يتصل باللي قبله
export const hasArabic = (s) => /[؀-ۿﭐ-﷿ﹰ-﻿]/.test(s);

// النص ← خلايا { c: رمز الحرف، st: رموز اللون الفعالة }. ببيدروك: §r يصفّر، §k §l §o تنسيق يبقى مع تغيير اللون،
// وباقي الرموز ألوان (0-9 a-f وألوان المعادن g h i j m n p q s t u v)
function styleAfter(st, k) {
  if (k === "r") return "";
  const fmt = (st.match(/§[klo]/g) || []).join(""), col = (st.match(/§[^klo]/g) || []).slice(-1).join("");
  if ("klo".includes(k)) return fmt.includes(`§${k}`) ? st : fmt + `§${k}` + col;
  return fmt + `§${k}`;
}
function toCells(s, st0 = "") {
  const out = [];
  let st = st0;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch === "§" && i + 1 < s.length) { st = styleAfter(st, s[i + 1].toLowerCase()); i++; continue; }
    const c = s.codePointAt(i);
    if (c > 0xFFFF) i++;
    if (isHaraka(c)) continue;
    out.push({ c, st });
  }
  return { cells: out, st };
}
function shapeCells(cells) {
  const out = [];
  for (let i = 0; i < cells.length; i++) {
    const { c, st } = cells[i];
    const f = FORMS[c];
    if (!f && c !== TATWEEL) { out.push(cells[i]); continue; }
    const prev = i > 0 ? cells[i - 1].c : 0;
    const linkPrev = joinsNext(prev) && joinsPrev(c);
    if (c === LAM && i + 1 < cells.length && LAM_ALEF[cells[i + 1].c]) {          // لا، لأ، لإ، لآ
      out.push({ c: LAM_ALEF[cells[i + 1].c][linkPrev ? 1 : 0], st });
      i++;
      continue;
    }
    if (c === TATWEEL) { out.push(cells[i]); continue; }
    const next = i + 1 < cells.length ? cells[i + 1].c : 0;
    const linkNext = joinsNext(c) && joinsPrev(next);
    const k = linkPrev && linkNext ? 3 : linkPrev ? 1 : linkNext ? 2 : 0;
    out.push({ c: f[Math.min(k, f.length - 1)], st });
  }
  return out;
}

// ───────── 2) الاتجاه (مبسّط من خوارزمية يونيكود ثنائية الاتجاه، والأساس من اليمين) ─────────
const isRTL = (c) => (c >= 0x0590 && c <= 0x08FF) || (c >= 0xFB1D && c <= 0xFDFF) || (c >= 0xFE70 && c <= 0xFEFF);
const isDigit = (c) => c >= 0x30 && c <= 0x39;
const isLTR = (c) => !isRTL(c) && ((c >= 0x41 && c <= 0x5A) || (c >= 0x61 && c <= 0x7A) || isDigit(c) || (c >= 0xC0 && c <= 0x24F));
const MIRROR = { 0x28: 0x29, 0x29: 0x28, 0x5B: 0x5D, 0x5D: 0x5B, 0x7B: 0x7D, 0x7D: 0x7B, 0x3C: 0x3E, 0x3E: 0x3C, 0xAB: 0xBB, 0xBB: 0xAB, 0x2039: 0x203A, 0x203A: 0x2039 };
function reorder(cells) {
  const n = cells.length, dir = new Array(n);
  for (let i = 0; i < n; i++) dir[i] = isRTL(cells[i].c) ? "R" : isLTR(cells[i].c) ? "L" : "N";
  // + - $ # قبل رقم، و % بعد رقم: جزء من الرقم
  for (let i = 0; i < n; i++) {
    if (dir[i] !== "N") continue;
    const c = cells[i].c;
    if ("+-$#".includes(String.fromCharCode(c)) && i + 1 < n && isDigit(cells[i + 1].c)) dir[i] = "L";
    else if ("%°".includes(String.fromCharCode(c)) && i > 0 && isDigit(cells[i - 1].c)) dir[i] = "L";
  }
  // المحايد بين قويين يساريين يصير يساري، والباقي يميني (اتجاه الفقرة)
  for (let i = 0; i < n; ) {
    if (dir[i] !== "N") { i++; continue; }
    let j = i;
    while (j < n && dir[j] === "N") j++;
    const before = i > 0 ? dir[i - 1] : "R", after = j < n ? dir[j] : "R";
    const d = before === "L" && after === "L" ? "L" : "R";
    for (let k = i; k < j; k++) dir[k] = d;
    i = j;
  }
  // نقلب الكل، وبعدين نرجع كل مقطع يساري لترتيبه
  const idx = [...Array(n).keys()].reverse();
  const out = [];
  for (let a = 0; a < n; ) {
    if (dir[idx[a]] !== "L") { const cell = cells[idx[a]]; out.push(MIRROR[cell.c] ? { c: MIRROR[cell.c], st: cell.st } : cell); a++; continue; }
    let b = a;
    while (b < n && dir[idx[b]] === "L") b++;
    for (let k = b - 1; k >= a; k--) out.push(cells[idx[k]]);
    a = b;
  }
  return out;
}
function emit(cells) {
  let s = "", cur = null;
  for (const { c, st } of cells) {
    if (st !== cur) { s += "§r" + st; cur = st; }
    s += String.fromCodePoint(c);
  }
  return s;
}
// سطر عربي (منطقي، بترتيب الكتابة) ← سطر جاهز للعرض باللعبة
export function visualLine(line, st0 = "") {
  if (!hasArabic(line)) return line;
  const { cells } = toCells(line, st0);
  return emit(reorder(shapeCells(cells)));
}

// ───────── 3) العرض والتقطيع ─────────
// عرض تقريبي بالبكسل (خط اللعبة بحجم 1): الحروف العربية ~6.5، اللاتينية 6، المسافة 4، النقاط والحروف الرفيعة 3
function charW(c) {
  if (c === 0x20) return 4;
  if (isRTL(c)) return 6.5;
  if ("il.,:;!'|`".includes(String.fromCharCode(c))) return 3;
  if (c >= 0xE000 && c <= 0xF8FF) return 9;                                          // رموز الـHUD المرسومة
  return 6;
}
export function textWidth(s) {
  let w = 0;
  for (let i = 0; i < s.length; i++) {
    if (s[i] === "§") { i++; continue; }
    const c = s.codePointAt(i);
    if (c > 0xFFFF) i++;
    if (!isHaraka(c)) w += charW(c);
  }
  return w;
}
// يقطع سطر منطقي لأسطر عرضها ≤ max (يكسر عند المسافات)، وكل سطر يكمل بنفس اللون اللي وقف عنده اللي قبله
export function wrapLine(line, max) {
  if (textWidth(line) <= max) return [line];
  const words = line.split(" "), out = [];
  let cur = "", w = 0;
  for (const word of words) {
    const ww = textWidth(word);
    if (cur && w + 4 + ww > max) { out.push(cur); cur = word; w = ww; }
    else { cur = cur ? `${cur} ${word}` : word; w += (w ? 4 : 0) + ww; }
  }
  if (cur) out.push(cur);
  // اللون يكمل بالسطر الجاي
  let st = "";
  return out.map((l) => { const r = st + l; st = toCells(r).st; return r; });
}
// نص كامل (أسطر بـ\n) ← أسطر عرض: كل سطر عربي يتقطع ويتشكل وينقلب، والإنكليزي يبقى
export function visual(text, max = 0) {
  const out = [];
  let st = "";
  for (const raw of String(text).split("\n")) {
    if (!hasArabic(raw)) { out.push(raw); st = toCells(raw, st).st; continue; }
    const parts = max > 0 ? wrapLine(raw, max) : [raw];
    for (const part of parts) out.push(visualLine(part, st));
    st = toCells(raw, st).st;
  }
  return out.join("\n");
}

// ───────── 4) الترجمة ─────────
// القاموس: AR = { "English": "عربي" } والقوالب بخانات {0}..{9} (نفس الأرقام بالطرفين، وممكن يتغير ترتيبها بالعربي)
const exact = new Map(), tpl = [];
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
for (const [en, ar] of Object.entries(AR)) {
  if (!/\{\d\}/.test(en)) { exact.set(en, ar); continue; }
  // قالب كله خانات (بدون كلام) يطابق كل شي: ما نستعمله
  if (!/[A-Za-z]{2}/.test(en.replace(/\{\d\}/g, ""))) continue;
  // خانات لاصقة ({0}{1} = لون + اسم عادةً) تصير خانة وحدة إذا نفس الترتيب بالعربي، حتى الاسم يترجم كامل
  const parts = en.split(/((?:\{\d\})+)/), groups = [];
  let re = "^";
  for (const p of parts) {
    if (!p) continue;
    if (/^(?:\{\d\})+$/.test(p)) {
      if (p.length > 3 && ar.includes(p)) { re += "([\\s\\S]*?)"; groups.push([p]); }
      else for (const one of p.match(/\{\d\}/g)) { re += "([\\s\\S]*?)"; groups.push([one]); }
    } else re += esc(p);
  }
  tpl.push({ re: new RegExp(re + "$"), reG: new RegExp(re.split("*?").join("*") + "$"), groups, ar, lit: en.replace(/\{\d\}|§./g, "").length });
}
tpl.sort((a, b) => b.lit - a.lit);                                                    // الأطول كلاماً أول (أدق)
const cache = new Map();
// كم كلمة إنكليزية باقية (عدا رموز تبقى حتى بالعربي: Lv، XP، S...)
const KEEP_EN = /^(Lv|XP|S|V1|MAX|HUD|OK|X)$/;
function enWords(s) { return (String(s).replace(/§./g, "").match(/[A-Za-z]{2,}/g) || []).filter((w) => !KEEP_EN.test(w)).length; }
function lookup(s, depth) {
  if (s === "" || !/[A-Za-z]/.test(s)) return s;
  const hit = exact.get(s);
  if (hit !== undefined) return hit;
  // نفس النص بدون رموز اللون بالبداية/النهاية
  const m0 = /^((?:§.)*)([\s\S]*?)((?:§.)*)$/.exec(s);
  if (m0 && (m0[1] || m0[3])) { const h2 = exact.get(m0[2]); if (h2 !== undefined) return m0[1] + h2 + m0[3]; }
  // مسافات بالبداية/النهاية
  const sp = /^(\s*)([\s\S]*?)(\s*)$/.exec(s);
  if (sp && (sp[1] || sp[3]) && sp[2]) { const h3 = exact.get(sp[2]); if (h3 !== undefined) return sp[1] + h3 + sp[3]; }
  if (depth > 3) return null;
  for (const t of tpl) {
    const m = t.re.exec(s);
    if (!m) continue;
    const fill = (mm) => { let out = t.ar; t.groups.forEach(([ph], gi) => { out = out.split(ph).join(trPiece(mm[gi + 1], depth + 1)); }); return out; };
    const a = fill(m), mg = t.reG.exec(s);
    if (!mg) return a;
    const b = fill(mg);
    return enWords(b) < enWords(a) ? b : a;
  }
  // رموز/أرقام/مسافات حوالي الكلام (✔ جاهزة، Epic★★★★، (AWAKENED)، 3. اسم): نترجم الكلام اللي بالنص
  const core = /^([^A-Za-z]*)([A-Za-z](?:[\s\S]*[A-Za-z])?)([^A-Za-z]*)$/.exec(s);
  if (core && (core[1] || core[3])) {
    const pun = /^[.!?:]/.test(core[3]) ? core[3][0] : "";
    if (pun) { const h5 = exact.get(core[2] + pun); if (h5 !== undefined) return core[1] + h5 + core[3].slice(1); }
    const h4 = exact.get(core[2]);
    if (h4 !== undefined) return core[1] + h4 + core[3];
  }
  return null;
}
// قطعة (خانة من قالب): إذا ما إلها ترجمة تبقى مثل ما هي (أرقام، أسماء لاعبين...)
function trPiece(s, depth = 0) {
  const r = lookup(s, depth);
  if (r !== null) return r;
  return trSegments(s, depth);
}
// آخر محاولة: كل قطعة بين رموز الألوان، وكل جملة بين ". "
function trSegments(s, depth) {
  const segs = s.split(/(§.)/);
  if (segs.length > 1) {
    let any = false;
    const out = segs.map((g) => { if (/^§.$/.test(g) || !/[A-Za-z]/.test(g)) return g; const r = lookup(g, depth + 1); if (r !== null) { any = true; return r; } return g; });
    if (any) return out.join("");
  }
  return s;
}
// ترجمة نص كامل (يتقطع على \n، وكل سطر يترجم لوحده)
export function trText(s) {
  if (typeof s !== "string" || !s) return s;
  const c = cache.get(s);
  if (c !== undefined) return c;
  const out = s.split("\n").map((line) => { const r = lookup(line, 0); if (r !== null && enWords(r) === 0) return r; const g = trSegments(line, 0); return r !== null && enWords(r) <= enWords(g) ? r : g; }).join("\n");
  if (cache.size > 1500) cache.clear();
  cache.set(s, out);
  return out;
}
// سطور الواجهة المرتبة (أسماء بين رموز ألوان وفواصل): السطر كامل إذا إله ترجمة، وإلا كل قطعة لوحدها (أدق من القوالب هنا)
export function trSeg(s) {
  if (typeof s !== "string" || !s) return s;
  return s.split("\n").map((line) => {
    const e = exact.get(line);
    if (e !== undefined) return e;
    const a = lookup(line, 0), b = trSegments(line, 0);
    return a !== null && enWords(a) <= enWords(b) ? a : b;
  }).join("\n");
}
// نسبة التغطية (للاختبار): كم سطر من النص لگينا إله ترجمة
export function covered(s) { const r = trText(s); return r !== s || !/[A-Za-z]{3}/.test(s); }

// ───────── 5) العرض حسب المكان ─────────
// عرض كل مكان بالبكسل (بحجم خط 1). الفورم بخط عربي أكبر (×1.15) فعرضه أقل.
export const WIDTH = { form: 150, button: 0, chat: 175, title: 240, tracker: 165, hud: 0 };
export const AR_MARK = "§r§r§r";                                                     // علامة بأول الفورم: ملف server_form.json يكبّر الخط العربي
// النص للاعب: en = يرجع مثل ما هو؛ ar = يترجم + يقطع + يشكّل ويقلب
export function show(lang, s, where = "chat") {
  if (lang !== "ar" || typeof s !== "string" || !s) return s;
  if (where === "hud" || where === "seg") return trSeg(s).split("\n").map(segLine).join("\n");
  const t = trText(s);
  return visual(t, WIDTH[where] ?? 0);
}
// الواجهة والسطور المرتبة (أيقونات وفواصل │): ما نقلب السطر كله (تتخربط الأشرطة المرسومة)، بس كل مقطع عربي ينقلب بمكانه
const AR_RUN = /[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF](?:[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF \u060C\u061B\u061F]|§.)*/g;
export function segLine(line) {
  if (!hasArabic(line)) return line;
  let out = "", last = 0, m;
  AR_RUN.lastIndex = 0;
  while ((m = AR_RUN.exec(line))) {
    let run = m[0];
    const trail = /(\s|§.)*$/.exec(run)[0];                                          // مسافات/رموز بآخر المقطع تبقى بمكانها
    run = run.slice(0, run.length - trail.length);
    const st = toCells(line.slice(0, m.index)).st;
    out += line.slice(last, m.index) + visualLine(run, st) + "§r" + toCells(run, st).st + trail;
    last = m.index + m[0].length;
  }
  return out + line.slice(last);
}
// نص بلغتين { en, ar } (الحكاية وطور القصة)
export function pick(lang, o) { return o && typeof o === "object" ? (lang === "ar" ? o.ar : o.en) : o; }
