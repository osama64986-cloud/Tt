// ═════════════════════ مؤثرات المهارات: كل قدرة بهوية بصرية خاصة (جزيئات ماينكرافت الأصلية بس) ═════════════════════
// هذا الملف بصري بالكامل: ما يغير ضرر ولا تبريد ولا منطق. main.js ينادي هذي الدوال بنفس توقيت المهارة.
// كل مهارة إلها: تمهيد (anticipation) ← لحظة الفعل ← ضربة (impact) ← أثر يبقى شوي (residue)، وبجزيئات تناسب طبيعتها.
import { system } from "@minecraft/server";
import { PT, P, ring, arc, line, helix, column, converge, sphereOut, shockwave, spiralIn, dustRing, critBurst, seq, later, add, sub, norm, len, lerp, rnd, cross } from "./vfx.js";

const ok = (e) => { try { return !!e && (typeof e.isValid === "function" ? e.isValid() : !!e.isValid); } catch (err) { return false; } };
const up = (c, y) => ({ x: c.x, y: c.y + y, z: c.z });
const flat = (d) => { const l = Math.hypot(d.x, d.z) || 1; return { x: d.x / l, y: 0, z: d.z / l }; };
const right = (d) => ({ x: -d.z, y: 0, z: d.x });
const chest = (e) => { try { return up(e.location, 1.0); } catch (err) { return undefined; } };

// ألوان كل قدرة (للجزيئات اللي تقبل تلوين: wax, glow, sparkler, spell, note)
export const PAL = {
  steel: [0.82, 0.86, 0.95], hot: [1, 0.72, 0.35],
  teal: [0.2, 0.95, 0.85], aqua: [0.35, 0.8, 1], deep: [0.25, 0.4, 1], violetNote: [0.75, 0.45, 1],
  pink: [1, 0.55, 0.85], lilac: [0.85, 0.6, 1],
  gold: [1, 0.82, 0.25], paleGold: [1, 0.93, 0.6], loss: [1, 0.3, 0.25],
  space: [0.62, 0.35, 1], spaceBlue: [0.45, 0.6, 1],
  law: [0.7, 0.45, 1], lawGold: [1, 0.85, 0.4], ink: [0.12, 0.1, 0.18],
  star: [0.6, 0.78, 1], starGold: [1, 0.86, 0.45], white: [1, 1, 1], void: [0.4, 0.15, 0.7],
  rock: [0.62, 0.58, 0.5], blood: [0.85, 0.08, 0.1], wind: [0.75, 1, 0.85],
};

// ═══════════════ الحديد: شرر معدن مطروق + نفخات صدمة ═══════════════
export const IRON = {
  // التحول: حلقة شرر تصعد من الرجل للراس (الدرع يتكون)، وبالأخير رنة: شرر حرج + رشة شرر للخارج
  skinForm(dim, at) {
    dustRing(dim, at, 0.5, 12, 0.22);
    seq(9, 1, (i) => ring(dim, up(at, 0.1 + i * 0.24), 0.62 - Math.abs(i - 4) * 0.025, 12, PT.spark, { d: { x: 0.3, y: 0.3, z: 0.3 }, ph: i * 0.5, eye: 0.7 }));
    later(10, () => {
      critBurst(dim, up(at, 1.9), 22);
      ring(dim, up(at, 1.1), 0.5, 12, PT.basicCrit, { out: 1, up: 0.5, eye: 0.7 });
    });
  },
  // لمعة صغيرة على الجسم والدرع شغال
  skinTick(dim, at) {
    for (let i = 0; i < 2; i++) P(dim, { x: at.x + rnd(-0.35, 0.35), y: at.y + rnd(0.3, 1.8), z: at.z + rnd(-0.35, 0.35) }, PT.spark, { d: { x: 0.2, y: 0.2, z: 0.2 }, eye: 0.8 });
  },
  // ضربة على الدرع: رشة شرر من جهة الضربة
  skinHit(dim, at) {
    critBurst(dim, up(at, 1.7), 14);
    sphereOut(dim, up(at, 1.1), 8, PT.basicCrit, 1, { eye: 0.7 });
  },
  // نهاية الدرع: الصفائح تتقشر (غبار حصى ينزل) + حلقة شرر
  skinEnd(dim, at) {
    for (let i = 0; i < 10; i++) P(dim, { x: at.x + rnd(-0.4, 0.4), y: at.y + rnd(0.4, 1.9), z: at.z + rnd(-0.4, 0.4) }, PT.gravel, { eye: 0.7 });
    ring(dim, up(at, 1), 0.6, 10, PT.spark, { d: { x: 0.4, y: 0.4, z: 0.4 }, eye: 0.7 });
  },
  // القبضة: شحنة عند الانطلاق، أثر دخان وشرر بالطيران
  fistLaunch(dim, at, d) {
    ring(dim, at, 0.55, 10, PT.spark, { normal: d, d: { x: 0.2, y: 0.2, z: 0.2 } });
    P(dim, at, PT.puff, { v: { x: d.x * 0.3, y: 0.02, z: d.z * 0.3 } });
  },
  fistTrail(dim, at, d) {
    P(dim, at, PT.whiteSmoke, { eye: 0.6 });
    P(dim, add(at, d, -0.6), PT.spark, { d: { x: 0.25, y: 0.25, z: 0.25 }, eye: 0.6 });
  },
  // الضربة: نفخات زئير بيضا + مخروط شرر باتجاه اللكمة + حلقة غبار أرضية + موجة صدمة
  fistImpact(dim, c, d, ground) {
    P(dim, c, PT.roar, { eye: 1.5 });
    critBurst(dim, up(c, 0.7), 28);
    for (let i = 0; i < 12; i++) P(dim, c, PT.basicCrit, { d: { x: d.x + rnd(-0.45, 0.45), y: d.y + rnd(-0.1, 0.6), z: d.z + rnd(-0.45, 0.45) }, eye: 1.0 });
    ring(dim, c, 0.9, 14, PT.spark, { normal: d, d: { x: 0.5, y: 0.5, z: 0.5 } });
    dustRing(dim, ground, 0.6, 18, 0.45);
    shockwave(dim, ground, 0.6, 3.2, 6, { ids: [PT.puff], density: 1.4, step: 2, vout: 0.12, up: 0.03 });
  },
};

// ═══════════════ الريح: دوامات شحنة الريح الحقيقية + دخان أبيض ═══════════════
export const WIND = {
  runStart(dim, at) {
    P(dim, up(at, 0.5), PT.gust, { eye: 1.2 });
    ring(dim, up(at, 0.3), 1.0, 6, PT.smallGust, { eye: 1.0 });
    dustRing(dim, at, 0.4, 10, 0.25);
  },
  // أثر الركض: دوامة صغيرة ورا رجلك ودخان أبيض بين الرجلين
  runTrail(dim, at, d, big) {
    P(dim, { x: at.x - d.x * 0.7, y: at.y + 0.35, z: at.z - d.z * 0.7 }, PT.smallGust, { eye: 1.0 });
    for (let i = 0; i < 2; i++) P(dim, { x: at.x - d.x * rnd(0.3, 1.1) + rnd(-0.25, 0.25), y: at.y + rnd(0.1, 0.6), z: at.z - d.z * rnd(0.3, 1.1) + rnd(-0.25, 0.25) }, PT.whiteSmoke, { eye: 1.0 });
    if (big) P(dim, { x: at.x - d.x * 1.2, y: at.y + 0.6, z: at.z - d.z * 1.2 }, PT.gust, { eye: 1.4 });
  },
  leapLaunch(dim, at) {
    P(dim, up(at, 0.3), PT.gust, { eye: 1.2 });
    dustRing(dim, at, 0.4, 14, 0.4);
    ring(dim, up(at, 0.2), 0.9, 5, PT.smallGust, { eye: 1.0 });
  },
  leapTrail(dim, at) {
    P(dim, up(at, 0.4), PT.smallGust, { eye: 1.0 });
    P(dim, { x: at.x + rnd(-0.3, 0.3), y: at.y + rnd(0.1, 1.2), z: at.z + rnd(-0.3, 0.3) }, PT.whiteSmoke, { eye: 1.0 });
  },
  // العاصفة: انفجار ريح البريز بالمنتصف، حلقة وحدة من 7 انفجارات شحنة ريح على بعد 3، ودوامات صغار على بعد 5.5، وغبار أرضي ودخان
  // (قبل كانت 24 انفجار تغطي الشاشة؛ هسه 8 انفجارات تبين العاصفة بدون ما تعمي اللاعب)
  gale(dim, at) {
    P(dim, up(at, 1.0), PT.bigGust, { eye: 0 });
    dustRing(dim, at, 0.6, 24, 0.65);
    later(2, () => ring(dim, up(at, 0.8), 3.0, 7, PT.gust, { ph: Math.random(), eye: 1.8 }));
    later(4, () => ring(dim, up(at, 0.6), 5.5, 10, PT.smallGust, { ph: Math.random(), eye: 1.2 }));
    later(3, () => ring(dim, up(at, 0.3), 2.6, 14, PT.whiteSmoke, { eye: 1.0 }));
  },
  galeHit(dim, c) { P(dim, c, PT.smallGust, { eye: 1.0 }); P(dim, c, PT.whiteSmoke, { eye: 1.0 }); },
};

// ═══════════════ الصدى: حلقات الـWarden (الموجة الصوتية الأساسية)، حلقات الـShrieker، السكلك، والنوتات للتفاصيل ═══════════════
// حلقة الـsonic_explosion سبرايت 1.5 بلوكة يكبر ويختفي خلال 0.8 ثانية: هي حامل "الصوت" المقروء من بعيد؛ النوتات والسكلك صغار فهم تفاصيل بس.
const NOTE = (k) => [PAL.teal, PAL.aqua, PAL.deep, PAL.violetNote][((k % 4) + 4) % 4];
export const ECHO = {
  // تفعيل صدى الضربة: حلقة Warden عليك + حلقات الـShrieker تصعد وراك (تبين إن القدرة جاهزة) + نوتات تلف حولك
  strikeArm(dim, at) {
    P(dim, up(at, 1.0), PT.sonic, { eye: 0.6 });
    P(dim, up(at, 0.1), PT.shriek, { eye: 0 });
    ring(dim, up(at, 1.2), 0.9, 8, PT.note, { note: PAL.teal, eye: 0.8 });
    ring(dim, up(at, 0.15), 0.8, 10, PT.sculk, { eye: 0.8 });
  },
  // لحظة الضربة الأصلية: شحنات سكلك على الهدف (الصدى جاي)
  strikeMark(dim, c) { for (let i = 0; i < 5; i++) P(dim, { x: c.x + rnd(-0.35, 0.35), y: c.y + rnd(-0.4, 0.5), z: c.z + rnd(-0.35, 0.35) }, PT.sculk, { eye: 1.0 }); P(dim, c, PT.sculkPop, { eye: 1.0 }); },
  // الصدى نفسه بعد ثانية: حلقتين Warden (الثانية أعلى بشوي بعد تكين) + رشة نوتات + أرواح سكلك تصعد
  echo(dim, c, k = 0) {
    P(dim, c, PT.sonic, { eye: 1.2 });
    later(2, () => P(dim, up(c, 0.5), PT.sonic, { eye: 1.2 }));
    for (let i = 0; i < 8; i++) P(dim, { x: c.x + rnd(-0.6, 0.6), y: c.y + rnd(-0.3, 0.7), z: c.z + rnd(-0.6, 0.6) }, PT.note, { note: NOTE(k + i), eye: 1.0 });
    for (let i = 0; i < 4; i++) P(dim, { x: c.x + rnd(-0.3, 0.3), y: c.y + rnd(0, 0.5), z: c.z + rnd(-0.3, 0.3) }, PT.sculkSoul, { eye: 1.0 });
  },
  // قذيفة صوتية: حلقة Warden تمشي بخط لحد الهدف (كل تك حلقة جديدة، فيبين أثر حلقات) + سكلك ونوتات
  pulseTo(dim, a, b, onArrive) {
    const L = len(sub(b, a)), n = Math.max(2, Math.ceil(L / 1.5));
    for (let i = 1; i <= n; i++) later(i, () => {
      const p = lerp(a, b, i / n);
      P(dim, p, PT.sonic, { eye: 1.4 });
      P(dim, p, PT.sculk, { eye: 1.0 });
      if (i % 2 === 0) P(dim, p, PT.note, { note: PAL.teal, eye: 1.0 });
    });
    if (onArrive) later(n + 1, onArrive);
    return n + 1;
  },
  // علامة الختم: كل 5 تكات شحنات سكلك تلف حول صدر الهدف، وكل 20 تك "نبضة قلب" (حلقة Warden صغيرة)
  sealTick(dim, c, t) { ring(dim, c, 0.75, 6, PT.sculk, { ph: t * 0.25, eye: 1.0 }); if (t % 20 === 0) P(dim, c, PT.sonic, { eye: 1.2 }); },
  sealMark(dim, c) { P(dim, up(c, -1.0), PT.shriek, { eye: 0 }); ECHO.strikeMark(dim, c); P(dim, c, PT.sonic, { eye: 1.2 }); },
  // الختم ينفجر: عمود 3 حلقات Warden + حلقة 8 حلقات Warden حوله + نوتات بكل الاتجاهات + أرواح
  sealBlast(dim, c) {
    [0, 2, 4].forEach((t, i) => later(t + 1, () => P(dim, up(c, -0.5 + i * 0.7), PT.sonic, { eye: 1.2 })));
    later(3, () => ring(dim, c, 1.4, 8, PT.sonic, { eye: 1.4 }));
    for (let i = 0; i < 14; i++) P(dim, { x: c.x + rnd(-1, 1), y: c.y + rnd(-0.6, 1.0), z: c.z + rnd(-1, 1) }, PT.note, { note: NOTE(i), eye: 1.0 });
    for (let i = 0; i < 6; i++) P(dim, { x: c.x + rnd(-0.6, 0.6), y: c.y + rnd(-0.4, 0.4), z: c.z + rnd(-0.6, 0.6) }, PT.sculkSoul, { eye: 1.0 });
    critBurst(dim, up(c, 0.7), 20, true);
  },
  // موجة الصدى: جبهة موجة (قوس 80°) من حلقات Warden تتقدم 0.9 بلوكة/تك (جبهة كل تكين)، ونوتات وسكلك على الجبهة
  wave(dim, c, d, rmax, k) {
    const steps = Math.ceil(rmax / 0.9);
    for (let i = 1; i <= steps; i++) later(i, () => {
      const r = i * 0.9, cc = up(c, 1.1);
      if (i % 2 === 1) arc(dim, cc, { x: 0, y: 1, z: 0 }, d, r, -0.7, 0.7, Math.max(2, Math.round(r * 0.5)), PT.sonic, { eye: 1.6 });
      arc(dim, up(cc, 0.3), { x: 0, y: 1, z: 0 }, d, r, -0.72, 0.72, Math.max(3, Math.round(r * 0.8)), PT.note, { note: NOTE(k + i), eye: 1.2 });
      arc(dim, up(cc, -0.7), { x: 0, y: 1, z: 0 }, d, r, -0.6, 0.6, Math.max(2, Math.round(r * 0.6)), PT.sculk, { eye: 1.2 });
    });
  },
  hit(dim, c, k) { P(dim, c, PT.sculkPop, { eye: 1.0 }); P(dim, c, PT.sonic, { eye: 1.2 }); for (let i = 0; i < 3; i++) P(dim, { x: c.x + rnd(-0.4, 0.4), y: c.y + rnd(0, 0.6), z: c.z + rnd(-0.4, 0.4) }, PT.note, { note: NOTE(k + i), eye: 1.0 }); },
  // الجوقة: كل نبضة = حلقة Warden عليك + موجة أرضية من حلقات Warden تتوسع لحد r، ونوتات بلون النبضة على الموجة
  chorusPulse(dim, at, r, i) {
    P(dim, up(at, 1.1), PT.sonic, { eye: 0 });
    if (i === 0) P(dim, up(at, 0.1), PT.shriek, { eye: 0 });
    shockwave(dim, at, 1.2, r, 8, { ids: [PT.sonic], density: 0.3, y: 0.8 + i * 0.25, max: 24, eye: 1.4 });
    shockwave(dim, at, 1.2, r, 8, { ids: [PT.note, PT.sculk], note: NOTE(i), density: 0.7, y: 0.5 + i * 0.3, max: 36, eye: 1.2 });
  },
  chorusHit(dim, c, i) { for (let k = 0; k < 3; k++) P(dim, { x: c.x + rnd(-0.3, 0.3), y: c.y + rnd(0, 0.4), z: c.z + rnd(-0.3, 0.3) }, PT.sculkSoul, { eye: 1.0 }); P(dim, c, PT.note, { note: NOTE(i), eye: 1.0 }); },
};

// ═══════════════ البلور: لمعات End Rod، نجوم وردية، وانفجار عين الإندر ═══════════════
export const CRYSTAL = {
  muzzle(dim, at, d) {
    for (let i = 0; i < 6; i++) P(dim, add(at, { x: d.x + rnd(-0.3, 0.3), y: d.y + rnd(-0.3, 0.3), z: d.z + rnd(-0.3, 0.3) }, rnd(0.2, 0.7)), PT.wax, { c: PAL.pink, eye: 1.0 });
    P(dim, add(at, d, 0.5), PT.spark, { d: { x: 0.4, y: 0.4, z: 0.4 }, eye: 1.0 });
  },
  // أثر الشظية: الشظية تقطع 2.4 بلوكة بكل تك، فنرسم 3 نقاط على طول المقطع (نجوم وردية) ولمعة End Rod كل خطوتين
  shardTrail(dim, at, i, d) {
    for (let k = 0; k < 3; k++) P(dim, d ? add(at, d, -k * 0.8) : at, PT.wax, { c: (i + k) % 2 ? PAL.pink : PAL.lilac, eye: 1.0 });
    if (i % 2 === 0) P(dim, at, PT.endrod, { eye: 1.2 });
  },
  shardHit(dim, c) {
    P(dim, c, PT.ender, { eye: 1.0 }); P(dim, up(c, 0.3), PT.ender, { eye: 1.0 });
    ring(dim, c, 0.5, 10, PT.wax, { c: PAL.pink, eye: 1.0 });
    for (let i = 0; i < 3; i++) P(dim, { x: c.x + rnd(-0.4, 0.4), y: c.y + rnd(-0.2, 0.6), z: c.z + rnd(-0.4, 0.4) }, PT.endrod, { eye: 1.0 });
    critBurst(dim, up(c, 0.7), 12, true);
  },
  // الرمح البلوري: نَفَس تنين بنفسجي واكف على كل المسار + لولب لمعات End Rod حوله
  lanceTrail(dim, a, d, L) {
    const b = add(a, d, L);
    line(dim, a, b, 0.55, PT.breath, { eye: 1.2 });
    const { x: rx, z: rz } = right(flat(d));
    for (let i = 0; i < Math.round(L * 2); i++) {
      const t = i / (L * 2), ang = t * L * 2.2, p = add(a, d, t * L);
      P(dim, { x: p.x + Math.cos(ang) * 0.4 * rx, y: p.y + Math.sin(ang) * 0.4, z: p.z + Math.cos(ang) * 0.4 * rz }, PT.endrod, { eye: 1.2 });
    }
  },
  // خطوة طيران الرمح: نَفَس تنين واكف من النقطة السابقة للحالية + نقطتين End Rod بلولب حول المسار
  lanceStep(dim, a, b, d, i) {
    line(dim, a, b, 0.6, PT.breath, { eye: 1.2 });
    const r = right(flat(d));
    for (const ph of [0, Math.PI]) { const ang = i * 1.1 + ph, cs = Math.cos(ang) * 0.42, sn = Math.sin(ang) * 0.42; P(dim, { x: b.x + r.x * cs, y: b.y + sn, z: b.z + r.z * cs }, PT.endrod, { eye: 1.2 }); }
  },
  lanceHit(dim, c) {
    P(dim, c, PT.ender, { eye: 1.0 }); P(dim, up(c, 0.4), PT.ender, { eye: 1.0 });
    sphereOut(dim, c, 10, PT.spark, 0.6, { eye: 1.0 });
    critBurst(dim, up(c, 0.7), 18, true);
  },
  // الدرع: لولب نجوم وردية ولمعات يصعد حولك، لمعة على الدروع، وتكسر الدروع بالنهاية
  shieldForm(dim, at) {
    helix(dim, at, 1.15, 2.2, 1.5, 12, PT.wax, { strands: 2, ids: [PT.wax, PT.endrod], c: PAL.pink, eye: 0.9 });
    ring(dim, up(at, 0.1), 1.2, 14, PT.wax, { c: PAL.lilac, eye: 0.9 });
  },
  shieldGlint(dim, p) { P(dim, p, PT.endrod, { eye: 1.1 }); P(dim, p, PT.wax, { c: PAL.pink, eye: 1.1 }); },
  shatter(dim, p) { P(dim, p, PT.ender, { eye: 1.0 }); sphereOut(dim, p, 5, PT.spark, 0.5, { eye: 1.0 }); },
  // السجن: حلقات بلور تصعد من الأرض حول الهدف (القفص ينمو)، لمعات وهو محبوس، وتكسره
  prisonGrow(dim, at, r) {
    seq(6, 1, (i) => ring(dim, up(at, 0.15 + i * 0.4), r * (1 - i * 0.06), 10, PT.wax, { ids: [PT.wax, PT.spark], c: i % 2 ? PAL.pink : PAL.lilac, d: { x: 0.2, y: 0.2, z: 0.2 }, ph: i * 0.3, eye: 1.0 }));
  },
  prisonTick(dim, at, r) { P(dim, { x: at.x + rnd(-r, r) * 0.7, y: at.y + rnd(0.2, 2.2), z: at.z + rnd(-r, r) * 0.7 }, PT.endrod, { eye: 1.1 }); },
  prisonBreak(dim, c) {
    P(dim, c, PT.ender, { eye: 1.0 }); P(dim, up(c, 0.6), PT.ender, { eye: 1.0 });
    shockwave(dim, up(c, -0.9), 0.4, 2.2, 4, { ids: [PT.wax], c: PAL.pink, density: 2, y: 0.3 });
  },
  // التفجير: خط إشارة من اللاعب لكل بلورة، وبعدها انفجار وردي حسب عدد البلورات
  detonateLink(dim, a, b) { line(dim, a, b, 0.6, PT.breath, { eye: 1.2 }); },
  detonate(dim, c, n) {
    for (let k = 0; k <= Math.min(3, n); k++) P(dim, { x: c.x + rnd(-0.3, 0.3), y: c.y + rnd(-0.2, 0.5), z: c.z + rnd(-0.3, 0.3) }, PT.ender, { eye: 1.0 });
    sphereOut(dim, c, 10, PT.spark, 0.8, { eye: 1.0 });
    shockwave(dim, up(c, -0.9), 0.5, 2.0 + n * 0.4, 5, { ids: [PT.wax, PT.endrod], c: PAL.pink, density: 1.8, y: 0.35 });
    critBurst(dim, up(c, 0.7), 16 + n * 4, true);
  },
};

// ═══════════════ المحاسب: حروف طاولة السحر (حسابات) + شرار ذهبي + انفجار التوتم ═══════════════
export const ACCOUNT = {
  // الحروف تنضم للراس والرقم يتختم عليه
  // الختم: شعاع ذهبي ينزل من فوق الراس عليه (مثل ختم)، حلقتين ذهب (وحدة بالراس ووحدة بالأرض)، وحروف السحر تنضم للراس
  stamp(dim, head) {
    line(dim, up(head, 2.6), up(head, 0.2), 0.22, PT.wax, { c: PAL.gold, eye: 1.0 });
    ring(dim, up(head, 0.3), 0.7, 14, PT.wax, { c: PAL.gold, eye: 1.0 });
    ring(dim, up(head, -1.6), 0.9, 14, PT.wax, { c: PAL.paleGold, eye: 1.0 });
    converge(dim, head, 1.7, 14, "glyph", { eye: 0.8 });
    critBurst(dim, up(head, 0.6), 14);
  },
  shotTrail(dim, at, i) { P(dim, at, PT.wax, { c: i % 2 ? PAL.gold : PAL.paleGold, eye: 1.0 }); P(dim, at, PT.glow, { c: PAL.gold, eye: 1.0 }); },
  // الطرح: حلقة حمرا تطلع من الرقم للخارج (خسارة) وغبار أحمر ينزل + شرر
  minus(dim, head) {
    ring(dim, up(head, 0.4), 0.55, 12, PT.wax, { c: PAL.loss, eye: 1.0 });
    for (let i = 0; i < 14; i++) P(dim, { x: head.x + rnd(-0.5, 0.5), y: head.y + rnd(0.1, 0.7), z: head.z + rnd(-0.5, 0.5) }, PT.redDust, { eye: 1.0 });
    critBurst(dim, up(head, 0.5), 10);
  },
  // النقل: الرقم يطير بأثر ذهبي ويوصل للهدف الجديد بحلقة ذهب وحروف تنضم عليه
  arrive(dim, head) { converge(dim, head, 1.4, 12, "glyph", { eye: 0.8 }); ring(dim, up(head, 0.3), 0.65, 12, PT.wax, { c: PAL.gold, eye: 1.0 }); critBurst(dim, up(head, 0.6), 12); },
  // القسمة: خط قطع عمودي من فوق الراس للرجل، ورشتين ذهبية يمين ويسار
  split(dim, feet, head, toward) {
    line(dim, up(head, 0.8), up(feet, 0.05), 0.18, PT.spark, { d: { x: 0.1, y: 0.1, z: 0.1 }, eye: 1.0 });
    const r = right(flat(toward));
    for (const s of [-1, 1]) for (let i = 0; i < 6; i++) P(dim, { x: head.x + r.x * s * rnd(0.2, 0.9), y: head.y - rnd(0, 1.2), z: head.z + r.z * s * rnd(0.2, 0.9) }, PT.wax, { c: PAL.gold, eye: 1.0 });
  },
  // الصفر: حروف تنسحب بطريق الصفر النازل، وبالسحقة: انفجار التوتم (عملات ذهب وخضر) + نفخات + غبار + حلقة ذهب
  zeroFall(dim, at) { P(dim, at, PT.glyph, { d: { x: rnd(-0.6, 0.6), y: 1.2, z: rnd(-0.6, 0.6) }, eye: 1.0 }); P(dim, at, PT.wax, { c: PAL.gold, eye: 1.0 }); },
  zeroSlam(dim, at) {
    P(dim, up(at, 1.0), PT.totem, { eye: 0 });
    dustRing(dim, at, 0.6, 18, 0.45);
    shockwave(dim, at, 0.5, 3.2, 6, { ids: [PT.wax], c: PAL.gold, density: 1.8, y: 0.2 });
    critBurst(dim, up(at, 1.4), 24);
  },
  // الانهيار (الرقم وصل صفر): الحروف تنسحب لداخل ثم انفجار ذهبي
  collapse(dim, c) {
    P(dim, c, PT.totem, { eye: 0 });
    P(dim, c, PT.boom, { eye: 1.6 });
    sphereOut(dim, c, 12, PT.basicCrit, 1, { eye: 1.0 });
    ring(dim, up(c, -0.9), 1.2, 16, PT.wax, { c: PAL.gold, eye: 1.0 });
    converge(dim, c, 2.2, 16, "glyph", { eye: 0.8 });
  },
};

// ═══════════════ المسافة: جزيئات البوابة، نَفَس التنين، وانضمام/انفلاق المكان ═══════════════
// سحابة نَفَس تنين على الأرض (dragon_breath_lingering: عدد الجزيئات = نصف القطر² × المضاعف)
const breathCloud = (dim, c, r, mult = 7) => P(dim, up(c, 0.1), PT.breathCloud, { f: { cloud_radius: r, cloud_lifetime: 0.1, particle_multiplier: mult }, eye: 0 });
// نفخة انتقال مثل الإندرمان: جزيئات بوابة بحجم الجسم (عرض 0.6، ارتفاع 2)
const teleportPuff = (dim, at, n = 26) => { for (let i = 0; i < n; i++) P(dim, { x: at.x + rnd(-0.45, 0.45), y: at.y + rnd(0, 2.0), z: at.z + rnd(-0.45, 0.45) }, PT.portal, { eye: 0.9 }); };
export const SPACE = {
  breathCloud, teleportPuff,
  // شق مكاني: حلقة عمودية من جزيئات البوابة ونَفَس التنين تواجه اتجاه face، تتجدد كل 3 تكات لمدة ticks
  rift(dim, c, face, r, ticks) {
    const f = flat(face);
    for (let t = 0; t < ticks; t += 3) later(t + 1, () => {
      ring(dim, up(c, 1.0), r, 14, PT.portal, { normal: f, ids: [PT.portal, PT.breath], ph: t * 0.3, eye: 1.0 });
      if (t % 6 === 0) converge(dim, up(c, 1.0), r * 1.3, 4, "portal", { eye: 1.0 });
    });
  },
  implode(dim, c, r, n) { converge(dim, c, r, n, "portal", { eye: 0.9 }); },
  // حبل مكاني من نقطة لنقطة (نَفَس تنين واكف)
  tether(dim, a, b) { line(dim, a, b, 0.5, PT.breath, { j: 0.06, eye: 1.0 }); },
  arriveBurst(dim, c) {
    teleportPuff(dim, up(c, -1.0), 22);
    ring(dim, up(c, -0.9), 0.8, 10, PT.endrod, { eye: 1.0 });
    breathCloud(dim, up(c, -1.0), 1.2, 8);
  },
  // الدفع: حلقات بوابة متتالية تكبر (كبش مكاني) باتجاه الدفع، ونفخة بيضا
  ram(dim, c, d) {
    seq(4, 1, (i) => ring(dim, add(c, d, i * 0.35), 0.35 + i * 0.35, 10 + i * 2, PT.portal, { normal: d, ids: [PT.breath, PT.endrod], eye: 1.0 }));
    for (let i = 0; i < 6; i++) P(dim, c, PT.puff, { v: { x: d.x * rnd(0.3, 0.6), y: rnd(0, 0.1), z: d.z * rnd(0.3, 0.6) } });
    teleportPuff(dim, up(c, -1.0), 14);
    critBurst(dim, up(c, 0.7), 12, true);
  },
  // التبديل: لولب مزدوج (بوابة + End Rod) بين المكانين + انضمام بالمكانين
  swap(dim, a, b) {
    const A = up(a, 1), B = up(b, 1), d = norm(sub(B, A)), L = len(sub(B, A)), r = right(flat(d)), n = Math.max(8, Math.round(L * 2.2));
    for (let i = 0; i <= n; i++) {
      const t = i / n, p = lerp(A, B, t), ang = t * Math.PI * 4;
      for (const [ph, id] of [[0, PT.portal], [Math.PI, PT.endrod]]) {
        const cs = Math.cos(ang + ph) * 0.45, sn = Math.sin(ang + ph) * 0.45;
        P(dim, { x: p.x + r.x * cs, y: p.y + sn, z: p.z + r.z * cs }, id, { eye: 1.0 });
      }
    }
    SPACE.implode(dim, A, 1.6, 10); SPACE.implode(dim, B, 1.6, 10);
    teleportPuff(dim, a); teleportPuff(dim, b);
    breathCloud(dim, a, 1.3, 8); breathCloud(dim, b, 1.3, 8);
  },
  // الطي: مكانك ينطوي (انضمام)، خط تجعيدة أبيض بين المكانين، وانفلاق عند الهدف
  fold(dim, from, to, hitC) {
    SPACE.implode(dim, up(from, 1), 1.8, 16);
    teleportPuff(dim, from); breathCloud(dim, from, 1.2, 8);
    line(dim, up(from, 1), up(to, 1), 0.3, PT.spark, { d: { x: 0.15, y: 0.15, z: 0.15 }, eye: 1.0 });
    line(dim, up(from, 0.9), up(to, 0.9), 0.7, PT.breath, { eye: 1.0 });
    SPACE.arriveBurst(dim, up(to, 1));
    if (hitC) { critBurst(dim, up(hitC, 0.7), 18, true); ring(dim, hitC, 0.7, 12, PT.portal, { normal: norm(sub(hitC, to)), eye: 1.0 }); }
  },
  // الانهيار: كرة بوابة كبيرة تنسحب لنقطة على 3 دفعات + أذرع نَفَس تنين تلف للداخل، وبعدين انفجار التنين
  collapseCharge(dim, c) {
    [0, 5, 10].forEach((t, i) => later(t + 1, () => { SPACE.implode(dim, up(c, 1.2), 5.5 - i * 1.3, 20); spiralIn(dim, up(c, 0.2), 5 - i, 4, 9, PT.breath, { ph: t * 0.4, eye: 1.0 }); }));
  },
  collapseBoom(dim, c) {
    P(dim, up(c, 1.0), PT.dragonBoom, { eye: 0 });
    breathCloud(dim, c, 3.2, 6);
    shockwave(dim, c, 0.8, 4.5, 6, { ids: [PT.endrod, PT.portal], density: 1.6, y: 0.4 });
    critBurst(dim, up(c, 1.6), 28, true);
  },
  // الارتداد: علامة المكان المحفوظ (حلقة End Rod تنبض) ورجوع (انضمام هنا، لولب بوابة هناك، وحبل بينهم)
  anchorPulse(dim, at) { ring(dim, up(at, 0.08), 0.9, 10, PT.endrod, { eye: 1.0 }); P(dim, up(at, 0.5), PT.portalUp, { eye: 1.0 }); },
  rewind(dim, from, to) {
    SPACE.implode(dim, up(from, 1), 1.6, 16);
    teleportPuff(dim, from); teleportPuff(dim, to);
    helix(dim, to, 0.8, 2.4, 2, 14, PT.portal, { strands: 2, ids: [PT.portal, PT.endrod], eye: 0.9 });
    SPACE.tether(dim, up(from, 1), up(to, 1));
  },
};

// ═══════════════ القوانين: حروف السحر + هوية لكل قانون ═══════════════
export const LAW = {
  // حدود كل قانون (كل 10 تكات جزء من الدائرة) بجزيء يناسبه
  border(dim, kind, c, r, t) {
    const n = Math.round(Math.min(26, r * 3));
    if (kind === "weight") {
      ring(dim, up(c, 0.4), r, n, PT.gravel, { ph: t * 0.05, eye: 1.0 });
      for (let i = 0; i < 3; i++) { const a = Math.random() * 6.283, rr = Math.random() * r * 0.85; P(dim, { x: c.x + Math.cos(a) * rr, y: c.y + 1.3, z: c.z + Math.sin(a) * rr }, PT.glyph, { d: { x: 0, y: 1.2, z: 0 }, eye: 1.0 }); }
    } else if (kind === "silence") {
      ring(dim, up(c, 0.3), r, n, PT.smoke, { ph: t * 0.05, eye: 1.0 });
      ring(dim, up(c, 0.9), r, Math.round(n / 2), PT.ink, { ph: t * 0.07, d: { x: 0, y: 0.6, z: 0 }, eye: 1.0 });
    } else if (kind === "reflect") {
      ring(dim, up(c, 0.2), r, Math.round(n * 0.6), PT.endrod, { ph: t * 0.05, eye: 1.0 });
    } else if (kind === "boundary") {
      for (const [y, id] of [[0.25, PT.portal], [1.4, PT.endrod], [2.6, PT.portal]]) ring(dim, up(c, y), r, n, id, { ph: t * 0.05 + y, eye: 1.0 });
    } else {
      ring(dim, up(c, 0.2), r, n, PT.glow, { c: PAL.law, ph: t * 0.05, eye: 1.0 });
    }
  },
  // الثقل: الحديدة تسحق: نفخات زئير + غبار أرضي + موجة حصى
  weightSlam(dim, c, r) {
    P(dim, up(c, 0.6), PT.roar, { eye: 0 });
    dustRing(dim, c, 0.8, 22, 0.55);
    shockwave(dim, c, 1, r, 8, { ids: [PT.gravel, PT.puff], density: 1.3, y: 0.4, vout: 0.05 });
    critBurst(dim, up(c, 1.2), 20);
  },
  weightPulse(dim, c) { P(dim, up(c, 1.6), PT.gravel, { eye: 1.0 }); P(dim, up(c, 1.9), PT.gravel, { eye: 1.0 }); },
  // الصمت: موجة حبر ودخان تطفي المكان
  silenceCast(dim, c, r) { shockwave(dim, c, 1, r, 8, { ids: [PT.smoke, PT.ink], density: 1.2, y: 0.5, d: { x: 0, y: 0.5, z: 0 } }); },
  silenced(dim, head) { P(dim, up(head, 0.3), PT.angry, { eye: 1.0 }); },
  // الانعكاس: هالة لمعات ولولب شرر، ولما ينعكس الضرر: خط شرر من الضحية للمهاجم
  reflectCast(dim, at) { ring(dim, up(at, 1.1), 1.7, 16, PT.endrod, { eye: 1.0 }); helix(dim, at, 1.0, 2.2, 1.2, 10, PT.spark, { strands: 2, d: { x: 0.2, y: 0.2, z: 0.2 }, eye: 0.9 }); },
  reflectHit(dim, a, b) { line(dim, a, b, 0.3, PT.spark, { d: { x: 0.2, y: 0.2, z: 0.2 }, eye: 1.0 }); critBurst(dim, up(b, 0.7), 16); P(dim, b, PT.endrod, { eye: 1.0 }); },
  // الحدود: حروف تنضم لقاعدة كل عمود رون
  pillarRise(dim, base) { converge(dim, up(base, 0.6), 1.5, 6, "glyph", { eye: 1.0 }); P(dim, base, PT.puff, { v: { x: 0, y: 0.15, z: 0 } }); },
  bounce(dim, at) { for (let i = 0; i < 6; i++) P(dim, { x: at.x + rnd(-0.4, 0.4), y: at.y + rnd(0.3, 1.8), z: at.z + rnd(-0.4, 0.4) }, PT.portal, { eye: 1.0 }); },
  // الزمن: حروف تلف وتنسحب للساعة، ثلج على المتجمدين، ونبضة "تك" كل ثانية
  timeCast(dim, clock, at, r) {
    converge(dim, clock, 3.0, 24, "glyph", { eye: 0.8 });
    shockwave(dim, at, 1, r, 8, { ids: [PT.endrod, PT.snow], density: 1.0, y: 0.3 });
  },
  frozen(dim, head) { for (let i = 0; i < 3; i++) P(dim, { x: head.x + rnd(-0.4, 0.4), y: head.y + rnd(-0.6, 0.4), z: head.z + rnd(-0.4, 0.4) }, PT.snow, { eye: 1.0 }); },
  tick(dim, at, r) { ring(dim, up(at, 0.15), r * 0.5, 14, PT.endrod, { eye: 1.0 }); },
  // القانون المطلق: مطرقة القاضي تختم: نفخات + حروف + حلقات نور
  gavelSlam(dim, at) {
    P(dim, up(at, 0.5), PT.roar, { eye: 0 });
    converge(dim, up(at, 0.8), 2.2, 18, "glyph", { eye: 0.8 });
    shockwave(dim, at, 0.8, 6.5, 10, { ids: [PT.endrod, PT.glyph], density: 1.0, y: 0.2, d: { x: 0, y: 1, z: 0 } });
    critBurst(dim, up(at, 1.2), 24);
  },
  absoluteLaw(dim, kind, at) {
    if (kind === 0) P(dim, up(at, 1.2), PT.totem, { eye: 0 });
    else if (kind === 2) helix(dim, at, 0.9, 2.2, 2, 14, PT.wax, { strands: 2, c: PAL.gold, eye: 0.9 });
  },
  heavyOn(dim, head) { for (let i = 0; i < 5; i++) P(dim, { x: head.x + rnd(-0.4, 0.4), y: head.y + rnd(0.2, 0.9), z: head.z + rnd(-0.4, 0.4) }, PT.gravel, { eye: 1.0 }); },
};

// ═══════════════ النجوم: End Rod (نجوم)، شرار ملوّن، نار النيزك، وانفجارات ماينكرافت الكبيرة ═══════════════
export const STAR = {
  // النيزك: ذيل نار حقيقي (لهب كيان محترق + لهب مشعل) ودخان نار يبقى بالسما
  meteorTrail(dim, at, d, i) {
    P(dim, at, PT.bigFlame, { eye: 1.2 });
    P(dim, at, PT.flame, { d: { x: -d.x, y: -d.y, z: -d.z }, sp: 0.4, eye: 1.2 });
    if (i % 2 === 0) P(dim, add(at, d, -0.6), PT.campfire, { eye: 1.6 });
    if (i % 3 === 0) P(dim, at, PT.lava, { eye: 1.2 });
  },
  meteorImpact(dim, c) {
    P(dim, up(c, 0.8), PT.hugeBoom, { eye: 0 });
    P(dim, up(c, 0.5), PT.boom, { eye: 1.6 });
    for (let i = 0; i < 16; i++) { const a = (i / 16) * 6.283; P(dim, { x: c.x + Math.cos(a) * 1.3, y: c.y + 0.2, z: c.z + Math.sin(a) * 1.3 }, PT.flame, { d: { x: Math.cos(a), y: 0.6, z: Math.sin(a) }, sp: 1.6, eye: 1.2 }); }
    for (let i = 0; i < 8; i++) P(dim, up(c, 0.3), PT.lava, { eye: 1.2 });
    dustRing(dim, c, 1.0, 24, 0.65);
    for (let i = 0; i < 3; i++) P(dim, { x: c.x + rnd(-0.6, 0.6), y: c.y + 0.4, z: c.z + rnd(-0.6, 0.6) }, PT.campfire, { eye: 1.6 });
    critBurst(dim, up(c, 1.4), 28);
  },
  // بئر الجاذبية: أذرع لولبية من لمعات زرقا تدور وتنسحب للمركز، ونجم صغير بالنص
  wellTick(dim, c, t) {
    spiralIn(dim, up(c, 0.25), 7, 3, 9, PT.glow, { ph: -t * 0.22, twist: 1.4, c: PAL.star, eye: 1.0 });
    if (t % 4 === 0) { converge(dim, up(c, 1.2), 3.2, 6, "portal", { eye: 1.0 }); P(dim, up(c, 1.2), PT.endrod, { eye: 1.0 }); P(dim, up(c, 1.2), PT.sparkler, { c: PAL.starGold, eye: 1.0 }); }
  },
  wellEnd(dim, c) {
    P(dim, up(c, 1.0), PT.boom, { eye: 1.6 });
    shockwave(dim, c, 0.5, 6.5, 8, { ids: [PT.endrod, PT.glow], c: PAL.star, density: 1.0, y: 0.5 });
    critBurst(dim, up(c, 1.6), 20, true);
  },
  // نجم مداري (بدل الشكل): نواة لمعات + شرار ذهبي، ويترك ذيل End Rod يرسم المدار
  orbTick(dim, at, i) {
    P(dim, at, PT.endrod, { eye: 1.1 });
    P(dim, at, PT.sparkler, { c: i % 2 ? PAL.starGold : PAL.star, eye: 1.1 });
    P(dim, at, PT.wax, { c: PAL.starGold, eye: 1.1 });
  },
  orbCast(dim, at) { ring(dim, up(at, 1.0), 2.3, 18, PT.endrod, { eye: 1.0 }); ring(dim, up(at, 0.1), 1.0, 10, PT.sparkler, { c: PAL.starGold, eye: 1.0 }); },
  orbHit(dim, c) { critBurst(dim, up(c, 0.7), 12); for (let i = 0; i < 4; i++) P(dim, c, PT.sparkler, { c: PAL.starGold, eye: 1.0 }); },
  // الكوكبة: نجمة فوق كل عدو (لمعات تومض) وخطوط منقطة بينهم، وبالأخير صاعقة نجمية من فوق
  starMark(dim, head) { P(dim, up(head, 0.6), PT.endrod, { eye: 1.0 }); P(dim, up(head, 0.6), PT.sparkler, { c: PAL.white, eye: 1.0 }); ring(dim, up(head, 0.6), 0.22, 4, PT.wax, { c: PAL.star, eye: 1.0 }); },
  starLine(dim, a, b, bright) { line(dim, a, b, bright ? 0.35 : 0.7, bright ? PT.spark : PT.endrod, { d: { x: 0.1, y: 0.1, z: 0.1 }, eye: 1.0 }); },
  starfall(dim, c) {
    line(dim, up(c, 7), c, 0.45, PT.spark, { d: { x: 0.15, y: 0.15, z: 0.15 }, eye: 1.0 });
    later(2, () => { ring(dim, c, 0.8, 12, PT.endrod, { eye: 1.0 }); critBurst(dim, up(c, 0.7), 16, true); for (let i = 0; i < 4; i++) P(dim, c, PT.sparkler, { c: PAL.starGold, eye: 1.0 }); });
  },
  // الومضة النجمية: ذيل مذنب (End Rod واكف + شرار ذهبي وأزرق + دخان أبيض)
  dash(dim, from, to) {
    const A = up(from, 1.0), B = up(to, 1.0);
    line(dim, A, B, 0.45, PT.endrod, { j: 0.12, eye: 1.0 });
    line(dim, A, B, 0.9, PT.sparkler, { c: PAL.starGold, j: 0.25, eye: 1.0 });
    line(dim, up(from, 0.4), up(to, 0.4), 1.2, PT.whiteSmoke, { j: 0.2, eye: 1.0 });
    ring(dim, A, 0.7, 10, PT.endrod, { normal: norm(sub(B, A)), eye: 1.0 });
  },
  dashEnd(dim, at) { sphereOut(dim, up(at, 1), 10, PT.spark, 0.6, { eye: 1.0 }); ring(dim, up(at, 0.1), 1.0, 12, PT.endrod, { eye: 1.0 }); },
  dashHit(dim, c) { critBurst(dim, up(c, 0.7), 14); P(dim, c, PT.sparkler, { c: PAL.starGold, eye: 1.0 }); P(dim, c, PT.sparkler, { c: PAL.star, eye: 1.0 }); },
  // الثقب الأسود: قرص تراكم (نَفَس تنين يلف للداخل) + جزيئات بوابة تنسحب، وبالانهيار: انفجار التنين + موجة
  holeTick(dim, c, t) {
    spiralIn(dim, c, 4.2, 4, 8, PT.breath, { ph: t * 0.3, twist: 1.2, eye: 1.2 });
    if (t % 4 === 0) converge(dim, c, 7, 8, "portal", { eye: 1.2 });
  },
  holeCollapse(dim, c) { converge(dim, c, 8.5, 40, "portal", { eye: 1.2 }); converge(dim, c, 4, 12, "glyph", { eye: 1.2 }); },
  holeBoom(dim, c, g) {
    P(dim, c, PT.dragonBoom, { eye: 0 });
    P(dim, c, PT.hugeBoom, { eye: 0 });
    shockwave(dim, g, 0.8, 9.5, 12, { ids: [PT.breath, PT.endrod], density: 1.1, y: 0.5, max: 56 });
    critBurst(dim, up(c, 0.8), 32, true);
  },
  // المستعر الأعظم: شحن (بوابة تنسحب لك + لولب شرار ذهبي وأزرق + حلقة لمعات تكبر)، ثم انفجار هائل بثلاث موجات
  novaCharge(dim, at, k, t) {
    const core = up(at, 3.2);
    converge(dim, core, 10 * (1 - k) + 1.5, 5, "portal", { eye: 1.2 });
    helix(dim, at, 1.4 - k * 0.5, 3.0, 0.5, 4, PT.sparkler, { strands: 2, ph: t * 0.35, ids: [PT.sparkler], c: t % 4 ? PAL.starGold : PAL.star, eye: 0.9 });
    for (let i = 0; i < 1 + Math.round(k * 3); i++) P(dim, { x: core.x + rnd(-0.3, 0.3) * (0.4 + k), y: core.y + rnd(-0.3, 0.3) * (0.4 + k), z: core.z + rnd(-0.3, 0.3) * (0.4 + k) }, PT.endrod, { eye: 1.2 });
    if (t % 6 === 0) ring(dim, up(at, 0.15), 1 + 3 * k, 14, PT.endrod, { ph: t * 0.4, eye: 1.0 });
  },
  novaBoom(dim, at) {
    const c = up(at, 1.5);
    P(dim, up(at, 2.5), PT.dragonBoom, { eye: 0 });
    P(dim, c, PT.hugeBoom, { eye: 0 });
    shockwave(dim, at, 1, 14, 12, { ids: [PT.puff], density: 0.9, y: 0.2, vout: 0.15, up: 0.03, max: 60 });
    shockwave(dim, at, 1, 12, 12, { ids: [PT.endrod], density: 0.7, y: 1.2, max: 52 });
    later(3, () => shockwave(dim, at, 1, 10, 10, { ids: [PT.sparkler], c: PAL.starGold, density: 0.7, y: 2.2, max: 44 }));
    sphereOut(dim, c, 14, PT.basicCrit, 1, { eye: 0 });
  },
};

// ═══════════════ مستعير الصفات: كل صفة بجزيئات طبيعتها ═══════════════
export const TRAIT = {
  rock(dim, at) {
    for (let i = 0; i < 12; i++) P(dim, { x: at.x + rnd(-0.5, 0.5), y: at.y + rnd(0.2, 2.0), z: at.z + rnd(-0.5, 0.5) }, PT.gravel, { eye: 0.8 });
    dustRing(dim, at, 0.5, 16, 0.35);
    critBurst(dim, up(at, 1.7), 12);
  },
  fangs(dim, at, front) {
    for (let i = 0; i < 10; i++) P(dim, { x: front.x + rnd(-0.4, 0.4), y: front.y + rnd(-0.4, 0.4), z: front.z + rnd(-0.4, 0.4) }, PT.redDust, { eye: 1.0 });
    critBurst(dim, up(front, 0.6), 12);
  },
  fangsBite(dim, c, healer) {
    for (let i = 0; i < 6; i++) P(dim, { x: c.x + rnd(-0.35, 0.35), y: c.y + rnd(-0.3, 0.4), z: c.z + rnd(-0.35, 0.35) }, PT.redDust, { eye: 1.0 });
    if (healer) P(dim, up(healer, 2.1), PT.heart, { eye: 0.9 });
  },
  wings(dim, at) {
    P(dim, up(at, 0.4), PT.gust, { eye: 1.2 });
    ring(dim, up(at, 0.2), 0.9, 5, PT.smallGust, { eye: 1.0 });
    dustRing(dim, at, 0.4, 12, 0.35);
  },
  // عين الصياد: نبضة رادار ذهبية تتوسع، وعمود لمعات على كل عدو انعلّم
  eyeScan(dim, at) { shockwave(dim, at, 1, 9, 10, { ids: [PT.wax, PT.endrod], c: PAL.gold, density: 0.9, y: 0.4, max: 40 }); },
  eyeMark(dim, c) { column(dim, up(c, -0.6), 1.8, 5, PT.wax, { c: PAL.gold, eye: 1.0 }); critBurst(dim, up(c, 0.8), 8); },
  eyeBonus(dim, c) { P(dim, c, PT.wax, { c: PAL.gold, eye: 1.0 }); P(dim, c, PT.basicCrit, { d: { x: 0, y: 1, z: 0 }, eye: 1.0 }); },
  // الدمج: لولبين بلوني الصفتين يلتفون ببعض، وانفجار شرار بلونيهم
  fuse(dim, at, c1, c2) {
    helix(dim, at, 0.9, 2.3, 1.5, 12, PT.spell, { c: c1, ph: 0, eye: 0.9 });
    helix(dim, at, 0.9, 2.3, 1.5, 12, PT.spell, { c: c2, ph: Math.PI, eye: 0.9 });
    later(6, () => { for (let i = 0; i < 6; i++) { P(dim, up(at, 1.2), PT.sparkler, { c: c1, eye: 0.9 }); P(dim, up(at, 1.2), PT.sparkler, { c: c2, eye: 0.9 }); } critBurst(dim, up(at, 1.9), 16); });
  },
};
export const TRAIT_COLOR = { rock: PAL.rock, fangs: PAL.blood, wings: PAL.wind, eye: PAL.gold };

// ═══════════════ الأسلحة: شطرات هلالية من جزيئات ماينكرافت (بدل أشكال الأقواس المصنوعة) ═══════════════
// slash: هلال حقيقي: قوس خارجي كامل + قوس داخلي أقصر ومزاح لقدام (فيطلع سميك بالنص ونحيف بالأطراف)، يترسم على 3 تكات من جهة لجهة (حركة).
// d = اتجاه الشطرة، roll = ميلان مستوى الشطرة حوالين d (0 أفقي، 90 عمودي)، span = زاوية القوس، side = جهة البداية (1 من اليسار، -1 من اليمين)
function slash(dim, c, d, r, span, roll, ids, o = {}) {
  const f = flat(d), rr = (roll * Math.PI) / 180;
  const normal = { x: -f.z * Math.sin(rr), y: Math.cos(rr), z: f.x * Math.sin(rr) };
  const side = o.side || 1, steps = o.steps ?? 3, n = o.n || Math.round(r * span * 7);
  const a0 = (-span / 2) * side, a1 = (span / 2) * side;
  const inner = add(c, f, r * 0.14);
  for (let k = 0; k < steps; k++) {
    later(k + (o.delay || 0), () => {
      const s0 = a0 + ((a1 - a0) * k) / steps, s1 = a0 + ((a1 - a0) * (k + 1)) / steps, m = Math.max(2, Math.round(n / steps));
      arc(dim, c, normal, f, r, s0, s1, m, ids[0], { ...o, ids: [ids[0]], tan: o.tan });
      if (ids[1]) arc(dim, inner, normal, f, r * 0.8, s0 * 0.75, s1 * 0.75, Math.max(2, Math.round(m * 0.7)), ids[1], { ...o, ids: [ids[1]], tan: o.tan });
      if (ids[2] && k === 1) arc(dim, c, normal, f, r * 1.04, s0, s1, 2, ids[2], { ...o, ids: [ids[2]] });
    });
  }
}
// علامات مخالب: 3 خطوط متوازية مايلة على الهدف
function claws(dim, c, face, tilt, ids, o = {}) {
  const f = flat(face), r = right(f), t = (tilt * Math.PI) / 180;
  const dirv = { x: r.x * Math.cos(t), y: Math.sin(t), z: r.z * Math.cos(t) };
  const perp = { x: -r.x * Math.sin(t) * 0.22, y: Math.cos(t) * 0.22, z: -r.z * Math.sin(t) * 0.22 };
  const base = add(c, f, -0.45);
  for (let k = -1; k <= 1; k++) {
    const mid = add(base, perp, k);
    line(dim, add(mid, dirv, -0.55), add(mid, dirv, 0.55), 0.12, ids[0], { ...o, ids });
  }
}
export const WEAPON = {
  slash, claws,
  // ساطور الجمر: هلال نار حقيقي (لهب المشعل يتحرك مع الشطرة) + ألسنة لهب كبيرة على القوس + جمرات
  emberArc(dim, o, d) {
    const c = { x: o.x + d.x * 0.6, y: o.y + 1.0, z: o.z + d.z * 0.6 };
    slash(dim, c, d, 2.6, 2.2, 8, [PT.flame, PT.glow], { c: PAL.hot, tan: 0.5, sp: 0.5, eye: 1.2 });
    slash(dim, up(c, -0.35), d, 3.1, 2.0, -6, [PT.flame], { tan: 0.4, sp: 0.4, delay: 2, eye: 1.2 });
    for (let i = 0; i < 4; i++) later(1 + i, () => { const a = -0.9 + i * 0.6, f = flat(d); const p = { x: c.x + (f.x * Math.cos(a) - f.z * Math.sin(a)) * 2.6, y: c.y - 0.4, z: c.z + (f.z * Math.cos(a) + f.x * Math.sin(a)) * 2.6 }; P(dim, p, PT.bigFlame, { eye: 1.2 }); P(dim, p, PT.lava, { eye: 1.2 }); });
    later(3, () => { P(dim, add(c, flat(d), 2.4), PT.campfire, { eye: 1.6 }); critBurst(dim, add(up(c, 0.6), flat(d), 2.2), 14); });
  },
  // دوامة الجحيم: حلقتين نار تلف بعكس بعض حولك (تترسم كل تك) + حلقة لهب أرضية + ألسنة كبيرة
  infernoSpin(dim, at, t) {
    const a0 = t * 0.9;
    for (const [y, r, dir] of [[1.0, 2.6, 1], [0.5, 2.2, -1]]) {
      const pts = 6;
      for (let i = 0; i < pts; i++) {
        const a = dir * (a0 + i * 0.16), p = { x: at.x + Math.cos(a) * r, y: at.y + y, z: at.z + Math.sin(a) * r };
        P(dim, p, PT.flame, { d: { x: -Math.sin(a) * dir, y: 0.1, z: Math.cos(a) * dir }, sp: 0.6, eye: 1.2 });
      }
      P(dim, { x: at.x + Math.cos(dir * a0) * r, y: at.y + y, z: at.z + Math.sin(dir * a0) * r }, PT.bigFlame, { eye: 1.2 });
    }
  },
  infernoBurst(dim, at) {
    for (let i = 0; i < 18; i++) { const a = (i / 18) * 6.283; P(dim, { x: at.x + Math.cos(a) * 1.4, y: at.y + 0.2, z: at.z + Math.sin(a) * 1.4 }, PT.flame, { d: { x: Math.cos(a), y: 0.3, z: Math.sin(a) }, sp: 1.6, eye: 1.2 }); }
    dustRing(dim, at, 0.8, 18, 0.5);
    for (let i = 0; i < 6; i++) P(dim, up(at, 0.4), PT.lava, { eye: 1.2 });
  },
  // خنجر الفجر: سلاسل نور ذهبية تلف (لولب نجوم) + طعنات بهلالات ذهبية صغيرة + ضربة الفجر الأخيرة
  sunBind(dim, feet) { helix(dim, feet, 0.85, 1.9, 2.5, 18, PT.wax, { strands: 3, c: PAL.gold, eye: 1.0 }); ring(dim, up(feet, 0.1), 1.0, 14, PT.endrod, { eye: 1.0 }); },
  stab(dim, c, from, i, last) {
    const d = norm(sub(c, from));
    slash(dim, c, d, last ? 1.3 : 0.75, 1.6, (i * 67) % 180 - 90, [PT.wax, PT.glow], { c: last ? PAL.paleGold : PAL.gold, steps: 1, n: last ? 16 : 9, eye: 1.0 });
    critBurst(dim, up(c, 0.7), last ? 20 : 8);
    if (last) { for (let k = 0; k < 10; k++) P(dim, c, PT.sparkler, { c: k % 2 ? PAL.gold : PAL.white, eye: 1.0 }); ring(dim, c, 0.9, 14, PT.wax, { normal: d, c: PAL.gold, eye: 1.0 }); P(dim, c, PT.endrod, { eye: 1.0 }); }
  },
  // سيف القسم الفضي: هلال نور (لمعات End Rod تبقى + شرر أبيض) وأثر خطوة فضية
  oathCleave(dim, o, d) {
    const c = { x: o.x + d.x * 0.8, y: o.y + 1.0, z: o.z + d.z * 0.8 };
    slash(dim, c, d, 2.8, 2.3, 4, [PT.endrod, PT.spark], { d: { x: 0.15, y: 0.15, z: 0.15 }, eye: 1.2 });
    slash(dim, up(c, -0.25), d, 3.3, 2.0, -8, [PT.wax], { c: PAL.white, delay: 2, eye: 1.2 });
  },
  silverStep(dim, from, to) {
    line(dim, up(from, 1), up(to, 1), 0.4, PT.endrod, { j: 0.1, eye: 1.0 });
    line(dim, up(from, 0.9), up(to, 0.9), 0.5, PT.spark, { d: { x: 0.2, y: 0.2, z: 0.2 }, eye: 1.0 });
    ring(dim, up(from, 0.1), 1.0, 12, PT.endrod, { eye: 1.0 }); ring(dim, up(to, 0.1), 1.0, 12, PT.spark, { d: { x: 0.2, y: 0.2, z: 0.2 }, eye: 1.0 });
  },
  silverCut(dim, c, from, k) { slash(dim, c, norm(sub(c, from)), 1.0, 1.8, k % 2 ? 40 : -40, [PT.endrod, PT.spark], { steps: 1, n: 12, d: { x: 0.1, y: 0.1, z: 0.1 }, eye: 1.0 }); critBurst(dim, up(c, 0.7), 10); },
  // ضربة رمح النور (light_lance): حلقة نور ولمعات وشرر أبيض
  lanceHit(dim, at) { ring(dim, up(at, 0.1), 1.3, 14, PT.endrod, { eye: 1.0 }); sphereOut(dim, up(at, 0.4), 8, PT.spark, 0.5, { eye: 1.0 }); critBurst(dim, up(at, 1.0), 14); },
  // سيف الظل: انتقال بنفخة ظل (حبر + بوابة)، شطرات بنفسجية غامقة (نَفَس تنين + توهج بنفسجي)
  shadowPuff(dim, at) {
    for (let i = 0; i < 14; i++) P(dim, { x: at.x + rnd(-0.4, 0.4), y: at.y + rnd(0, 1.9), z: at.z + rnd(-0.4, 0.4) }, i % 2 ? PT.ink : PT.portal, { d: { x: 0, y: 0.3, z: 0 }, eye: 0.9 });
    P(dim, up(at, 1.0), PT.poof, { f: { "aabb.x": 0.3, "aabb.y": 1.0, "aabb.z": 0.3 }, eye: 0 });
  },
  shadowCut(dim, c, from, roll) { slash(dim, c, norm(sub(c, from)), 1.1, 1.9, roll, [PT.breath, PT.glow], { c: [0.45, 0.2, 0.75], steps: 2, n: 14, eye: 1.0 }); critBurst(dim, up(c, 0.7), 12, true); },
  ghostLand(dim, at) { ring(dim, up(at, 0.1), 0.9, 10, PT.breath, { eye: 1.0 }); for (let i = 0; i < 5; i++) P(dim, { x: at.x + rnd(-0.4, 0.4), y: at.y + rnd(0.2, 1.2), z: at.z + rnd(-0.4, 0.4) }, PT.ink, { d: { x: 0, y: 0.5, z: 0 }, eye: 1.0 }); critBurst(dim, up(at, 0.9), 8, true); },
  shadowWave(dim, at) { shockwave(dim, at, 0.8, 5, 8, { ids: [PT.breath, PT.ink], density: 1.4, y: 0.3, d: { x: 0, y: 0.4, z: 0 } }); },
  // مخالب الظل: 3 خطوط مخالب (توهج بنفسجي + دم) + سم أخضر
  rake(dim, c, face, tilt) { claws(dim, c, face, tilt, [PT.glow, PT.redDust], { c: [0.7, 0.4, 1] , eye: 1.0 }); P(dim, c, PT.spell, { c: [0.35, 0.85, 0.25], eye: 1.0 }); critBurst(dim, up(c, 0.7), 8); },
  clawStorm(dim, c, face, tilt) { claws(dim, c, face, tilt, [PT.glow], { c: [0.75, 0.45, 1], eye: 1.0 }); },
  // مطرقة الصخر: دكة (نفخات زئير + غبار + موجة حصى) وشق الأرض (غبار وحصى على طول الشق)
  quake(dim, at, r) { P(dim, up(at, 0.6), PT.roar, { eye: 0 }); dustRing(dim, at, 0.8, 22, 0.6); shockwave(dim, at, 0.8, r, 6, { ids: [PT.puff, PT.gravel], density: 1.6, y: 0.3, vout: 0.08 }); critBurst(dim, up(at, 1.2), 18); },
  fissure(dim, at) { for (let i = 0; i < 3; i++) P(dim, { x: at.x + rnd(-0.4, 0.4), y: at.y + 0.2, z: at.z + rnd(-0.4, 0.4) }, PT.puff, { v: { x: rnd(-0.05, 0.05), y: rnd(0.15, 0.3), z: rnd(-0.05, 0.05) } }); for (let i = 0; i < 4; i++) P(dim, { x: at.x + rnd(-0.5, 0.5), y: at.y + rnd(0.3, 1.0), z: at.z + rnd(-0.5, 0.5) }, PT.gravel, { eye: 1.0 }); },
  // رمح الغروب: أثر نار وجمر ورا الرمح، وضربة مطر الرماح: حلقة لهب + حمم + غبار
  spearTrail(dim, at, d) { P(dim, at, PT.flame, { d: { x: -d.x, y: -d.y, z: -d.z }, sp: 0.3, eye: 1.0 }); P(dim, add(at, d, -0.7), PT.glow, { c: PAL.hot, eye: 1.0 }); if (Math.random() < 0.3) P(dim, at, PT.lava, { eye: 1.0 }); },
  spearLand(dim, at) { P(dim, up(at, 0.5), PT.bigFlame, { eye: 1.2 }); for (let i = 0; i < 8; i++) { const a = (i / 8) * 6.283; P(dim, up(at, 0.1), PT.flame, { d: { x: Math.cos(a), y: 0.4, z: Math.sin(a) }, sp: 1.2, eye: 1.2 }); } P(dim, up(at, 0.2), PT.lava, { eye: 1.2 }); dustRing(dim, at, 0.4, 10, 0.3); },
  // كاتانا الهاوية: هلال طاير (نَفَس تنين + بوابة + توهج بنفسجي) وشطرة X وإعدام بسيف شبح
  abyssStep(dim, pos, dir, roll, rad) {
    const f = flat(dir), rr = (roll * Math.PI) / 180, normal = { x: -f.z * Math.sin(rr), y: Math.cos(rr), z: f.x * Math.sin(rr) };
    arc(dim, pos, normal, f, rad, -1.0, 1.0, 7, PT.breath, { eye: 1.2 });
    arc(dim, add(pos, f, 0.2), normal, f, rad * 0.8, -0.75, 0.75, 5, PT.glow, { c: [0.7, 0.35, 1], eye: 1.2 });
    P(dim, pos, PT.portal, { eye: 1.2 });
  },
  abyssHit(dim, c) { P(dim, c, PT.ender, { eye: 1.0 }); critBurst(dim, up(c, 0.7), 12, true); for (let i = 0; i < 4; i++) P(dim, { x: c.x + rnd(-0.4, 0.4), y: c.y + rnd(-0.3, 0.5), z: c.z + rnd(-0.4, 0.4) }, PT.breath, { eye: 1.0 }); },
  // ضربات الأسلحة الخاصة (بدون مهارة): لمعة القسم الفضي، شق الساطور، رجّة المطرقة، الضربة المزدوجة لسيف الظل
  glint(dim, head) { for (let i = 0; i < 7; i++) P(dim, { x: head.x + rnd(-0.45, 0.45), y: head.y + rnd(-0.4, 0.4), z: head.z + rnd(-0.45, 0.45) }, i % 2 ? PT.endrod : PT.spark, { d: { x: 0.2, y: 0.2, z: 0.2 }, eye: 1.0 }); critBurst(dim, up(head, 0.6), 12); },
  cleaveHit(dim, c) { for (let i = 0; i < 4; i++) P(dim, { x: c.x + rnd(-0.3, 0.3), y: c.y + rnd(-0.3, 0.3), z: c.z + rnd(-0.3, 0.3) }, PT.flame, { d: { x: rnd(-1, 1), y: 0.6, z: rnd(-1, 1) }, sp: 0.6, eye: 1.0 }); P(dim, c, PT.lava, { eye: 1.0 }); },
  shockHit(dim, at) { dustRing(dim, at, 0.6, 14, 0.35); for (let i = 0; i < 3; i++) P(dim, { x: at.x + rnd(-0.6, 0.6), y: at.y + 0.3, z: at.z + rnd(-0.6, 0.6) }, PT.gravel, { eye: 1.0 }); },
  doubleHit(dim, c) { P(dim, c, PT.smallGust, { eye: 1.0 }); critBurst(dim, up(c, 0.7), 8); },
  // هالة السلاح (Lv3+ وتشتغل بقوة بلحظة المهارة): كل سلاح بجزيء يناسبه بدل النقاط الملونة
  aura(dim, id, b, t, i) {
    const j = (k) => ({ x: b.x + rnd(-k, k), y: b.y + rnd(-k, k), z: b.z + rnd(-k, k) });
    switch (id) {
      case "sh:dawn_dagger": { const a = t * 0.5 + i * 2.1; P(dim, { x: b.x + Math.cos(a) * 0.2, y: b.y + 0.08, z: b.z + Math.sin(a) * 0.2 }, PT.wax, { c: i % 2 ? PAL.gold : PAL.paleGold, eye: 0.7 }); break; }
      case "sh:ember_cleaver": P(dim, j(0.08), PT.flame, { d: { x: 0, y: 1, z: 0 }, sp: 0.12, eye: 0.7 }); if (Math.random() < 0.15) P(dim, b, PT.lava, { eye: 0.7 }); break;
      case "sh:silver_oath": P(dim, j(0.15), Math.random() < 0.6 ? PT.endrod : PT.spark, { d: { x: 0.1, y: 0.1, z: 0.1 }, eye: 0.7 }); break;
      case "sh:shadow_blade": { const a = t * 0.9 + i * 2.1; P(dim, { x: b.x + Math.cos(a) * 0.3, y: b.y + 0.05, z: b.z + Math.sin(a) * 0.3 }, PT.glow, { c: [0.55, 0.85, 1], d: { x: -Math.sin(a), y: 0.2, z: Math.cos(a) }, eye: 0.7 }); if (Math.random() < 0.08) P(dim, b, PT.smallGust, { eye: 0.9 }); break; }
      case "sh:stone_maul": P(dim, j(0.25), PT.happy, { eye: 0.7 }); break;
      case "sh:sunset_spear": P(dim, j(0.1), PT.redDust, { eye: 0.7 }); if (Math.random() < 0.3) P(dim, b, PT.glow, { c: [1, 0.35, 0.25], eye: 0.7 }); break;
      case "sh:shadow_claws": P(dim, j(0.25), PT.breath, { eye: 0.7 }); break;
      case "sh:dark_katana": P(dim, j(0.12), Math.random() < 0.5 ? PT.breath : PT.portal, { eye: 0.7 }); if (Math.random() < 0.3) P(dim, b, PT.glow, { c: [0.7, 0.35, 1], eye: 0.7 }); break;
      default: P(dim, b, PT.glow, { eye: 0.7 });
    }
  },
  xCut(dim, c, from, roll, big) { slash(dim, c, norm(sub(c, from)), big ? 1.8 : 1.4, 2.0, roll, [PT.breath, PT.glow], { c: [0.7, 0.35, 1], steps: 2, n: big ? 22 : 16, eye: 1.0 }); critBurst(dim, up(c, 0.7), big ? 24 : 14, true); },
};

// ═══════════════ وحوش الرتبة الدنيا: كل وحش بجزيئات طبيعته (بدل نقاط ملونة وأشكال أقواس) ═══════════════
const VENOM_C = [0.45, 0.95, 0.3], ROCK_TEAL = [0.35, 1, 0.85];
const splash = (dim, at, col, range = 2) => P(dim, at, PT.splash, { c: col, f: { splash_range: range }, eye: 0 });
export const MONSTER = {
  // عفريت الرماد: نار حقيقية
  impAmbient(dim, L) { if (Math.random() < 0.55) P(dim, { x: L.x + rnd(-0.3, 0.3), y: L.y + rnd(0.5, 1.4), z: L.z + rnd(-0.3, 0.3) }, PT.flame, { d: { x: 0, y: 1, z: 0 }, sp: 0.15, eye: 1.0 }); if (Math.random() < 0.08) P(dim, up(L, 1.2), PT.lava, { eye: 1.0 }); },
  impCharge(dim, L) { for (let i = 0; i < 2; i++) P(dim, { x: L.x + rnd(-0.4, 0.4), y: L.y + 0.1, z: L.z + rnd(-0.4, 0.4) }, PT.flame, { d: { x: 0, y: 1, z: 0 }, sp: 0.5, eye: 1.0 }); },
  impLeap(dim, L) { ring(dim, up(L, 0.15), 0.7, 12, PT.flame, { out: 1, up: 0.3, sp: 0.8, eye: 1.0 }); dustRing(dim, L, 0.4, 10, 0.3); P(dim, up(L, 0.5), PT.lava, { eye: 1.0 }); },
  impTrail(dim, L) { P(dim, up(L, 0.6), PT.flame, { d: { x: 0, y: 0.5, z: 0 }, sp: 0.1, eye: 1.0 }); P(dim, up(L, 0.9), PT.bigFlame, { eye: 1.2 }); },
  fireHit(dim, c) { for (let i = 0; i < 6; i++) P(dim, c, PT.flame, { d: { x: rnd(-1, 1), y: rnd(0.2, 1), z: rnd(-1, 1) }, sp: 0.9, eye: 1.0 }); P(dim, c, PT.lava, { eye: 1.0 }); critBurst(dim, up(c, 0.7), 10); },
  fireSwipe(dim, c, face, i) { slash(dim, c, face, 0.9, 1.7, i % 2 ? 40 : -40, [PT.flame, PT.glow], { c: PAL.hot, steps: 1, n: 12, tan: 0.4, sp: 0.4, eye: 1.0 }); },
  emberBoom(dim, b) {
    P(dim, up(b, 0.5), PT.boom, { eye: 1.6 });
    for (let i = 0; i < 12; i++) { const a = (i / 12) * 6.283; P(dim, up(b, 0.15), PT.flame, { d: { x: Math.cos(a), y: 0.5, z: Math.sin(a) }, sp: 1.3, eye: 1.2 }); }
    for (let i = 0; i < 4; i++) P(dim, up(b, 0.3), PT.lava, { eye: 1.2 });
    P(dim, up(b, 0.3), PT.campfire, { eye: 1.6 });
  },
  // حارس الصدأ: صخر وغبار ولمعات رون تركوازية
  guardAmbient(dim, L) { if (Math.random() < 0.25) P(dim, { x: L.x + rnd(-0.6, 0.6), y: L.y + rnd(0.6, 2.4), z: L.z + rnd(-0.6, 0.6) }, PT.gravel, { eye: 1.0 }); if (Math.random() < 0.25) P(dim, { x: L.x + rnd(-0.5, 0.5), y: L.y + rnd(0.3, 2.0), z: L.z + rnd(-0.5, 0.5) }, PT.glow, { c: ROCK_TEAL, eye: 1.0 }); },
  guardSlam(dim, L) { P(dim, up(L, 0.6), PT.roar, { eye: 0 }); dustRing(dim, L, 0.9, 22, 0.6); shockwave(dim, L, 0.8, 4.5, 8, { ids: [PT.puff, PT.gravel], density: 1.4, y: 0.3, vout: 0.06 }); critBurst(dim, up(L, 1.3), 18); for (let i = 0; i < 8; i++) P(dim, { x: L.x + rnd(-2, 2), y: L.y + 0.4, z: L.z + rnd(-2, 2) }, PT.glow, { c: ROCK_TEAL, eye: 1.0 }); },
  guardSwipe(dim, c, face) { slash(dim, c, face, 1.4, 1.9, 75, [PT.glow, PT.gravel], { c: ROCK_TEAL, steps: 2, n: 16, eye: 1.0 }); dustRing(dim, add(up(c, -1.2), flat(face), 0.4), 0.4, 10, 0.3); },
  rockImpact(dim, b) { dustRing(dim, b, 0.8, 20, 0.55); for (let i = 0; i < 8; i++) P(dim, { x: b.x + rnd(-1, 1), y: b.y + rnd(0.2, 1.2), z: b.z + rnd(-1, 1) }, PT.gravel, { eye: 1.0 }); critBurst(dim, up(b, 1.0), 16); },
  // ذئب الظل: جزيئات بوابة وحبر، وعواء بنفخات زئير وموجة ظل
  houndAmbient(dim, L) { if (Math.random() < 0.5) P(dim, { x: L.x + rnd(-0.4, 0.4), y: L.y + rnd(0.4, 1.1), z: L.z + rnd(-0.4, 0.4) }, PT.portal, { eye: 1.0 }); if (Math.random() < 0.08) P(dim, up(L, 0.6), PT.ink, { d: { x: 0, y: 0.4, z: 0 }, eye: 1.0 }); },
  houndCharge(dim, L) { for (let i = 0; i < 3; i++) P(dim, { x: L.x + rnd(-0.5, 0.5), y: L.y + 0.1, z: L.z + rnd(-0.5, 0.5) }, PT.portal, { eye: 1.0 }); P(dim, up(L, 0.3), PT.ink, { d: { x: 0, y: 0.6, z: 0 }, eye: 1.0 }); },
  howl(dim, L) {
    P(dim, up(L, 1.6), PT.roar, { eye: 0 });
    shockwave(dim, L, 1, 11, 16, { ids: [PT.breath, PT.ink], density: 0.9, y: 0.6, d: { x: 0, y: 0.4, z: 0 }, max: 56 });
    for (let i = 0; i < 3; i++) P(dim, { x: L.x + rnd(-0.4, 0.4), y: L.y + 2.0, z: L.z + rnd(-0.4, 0.4) }, PT.angry, { eye: 1.0 });
  },
  houndBite(dim, c, face, k) { claws(dim, c, face, k % 2 ? 25 : -25, [PT.glow], { c: [0.6, 0.35, 1], eye: 1.0 }); critBurst(dim, up(c, 0.7), 10); },
  // عقرب الرمل: رمل وسم أخضر (رشة جرعة السم الحقيقية)
  scorpAmbient(dim, L) { if (Math.random() < 0.2) P(dim, up(L, 1.3), PT.spell, { c: VENOM_C, eye: 1.0 }); },
  scorpCharge(dim, L, t) { P(dim, up(L, 1.7 + t * 0.02), PT.glow, { c: VENOM_C, eye: 1.0 }); ring(dim, up(L, 0.1), 1.1, 8, PT.spell, { c: VENOM_C, ph: t * 0.2, eye: 1.0 }); },
  venomSplash(dim, c) { splash(dim, c, VENOM_C, 1.6); critBurst(dim, up(c, 0.7), 10); },
  venomSwipe(dim, c, face) { slash(dim, c, face, 0.9, 1.6, -30, [PT.spell, PT.glow], { c: VENOM_C, steps: 1, n: 12, eye: 1.0 }); },
  venomTrail(dim, at) { P(dim, at, PT.glow, { c: VENOM_C, eye: 1.0 }); P(dim, at, PT.spell, { c: [0.3, 0.7, 0.2], eye: 1.0 }); },
  sandMark(dim, L) { for (let i = 0; i < 2; i++) P(dim, { x: L.x + rnd(-0.8, 0.8), y: L.y + 0.15, z: L.z + rnd(-0.8, 0.8) }, PT.puff, { v: { x: 0, y: rnd(0.04, 0.1), z: 0 } }); P(dim, { x: L.x + rnd(-0.6, 0.6), y: L.y + 0.6, z: L.z + rnd(-0.6, 0.6) }, PT.sand, { eye: 1.0 }); },
  burrowDig(dim, L) { dustRing(dim, L, 0.5, 14, 0.4); for (let i = 0; i < 6; i++) P(dim, { x: L.x + rnd(-0.6, 0.6), y: L.y + rnd(0.2, 1.0), z: L.z + rnd(-0.6, 0.6) }, PT.sand, { eye: 1.0 }); },
  burrowErupt(dim, L) { dustRing(dim, L, 0.6, 20, 0.6); for (let i = 0; i < 10; i++) P(dim, { x: L.x + rnd(-1, 1), y: L.y + rnd(0.3, 1.8), z: L.z + rnd(-1, 1) }, PT.sand, { eye: 1.0 }); splash(dim, up(L, 0.4), VENOM_C, 1.8); },
};

// ═══════════════ أنظمة عامة: كشف القدرة بالمعبد، الصدع، ضربة الإيقاع، الصد المثالي، الرد ═══════════════
export const SYS = {
  // كشف القدرة: انفجار شرار بلون الندرة يكبر مع الندرة، وحلقة نجوم بلونها، والأسطورية/الخرافية: انفجار التوتم + End Rod، والخرافية: انفجار التنين
  reveal(dim, c, col, idx) {
    const top = up(c, 2.2);
    for (let i = 0; i < 8 + idx * 6; i++) P(dim, top, PT.sparkler, { c: i % 3 ? col : PAL.white, eye: 0 });
    shockwave(dim, c, 0.8, 3 + idx * 0.8, 8, { ids: [PT.wax], c: col, density: 1.4, y: 0.3 });
    helix(dim, c, 1.0, 3.0, 2, 10 + idx * 3, PT.wax, { strands: 2, c: col, eye: 0 });
    critBurst(dim, up(top, 0.7), 16 + idx * 4, idx >= 2);
    if (idx >= 3) for (let i = 0; i < 8; i++) P(dim, { x: top.x + rnd(-1, 1), y: top.y + rnd(-1, 1), z: top.z + rnd(-1, 1) }, PT.endrod, { eye: 0 });
    if (idx >= 4) P(dim, top, PT.totem, { eye: 0 });
    if (idx >= 5) P(dim, top, PT.dragonBoom, { eye: 0 });
  },
  // بلا قدرة: البلورة تنطفي: دخان أسود وحبر ونفخة
  unbound(dim, c) { for (let i = 0; i < 3; i++) P(dim, { x: c.x + rnd(-0.4, 0.4), y: c.y + 1.6, z: c.z + rnd(-0.4, 0.4) }, PT.campfire, { eye: 0 }); for (let i = 0; i < 12; i++) P(dim, { x: c.x + rnd(-0.6, 0.6), y: c.y + rnd(1.4, 2.6), z: c.z + rnd(-0.6, 0.6) }, PT.ink, { d: { x: 0, y: 0.3, z: 0 }, eye: 0 }); P(dim, up(c, 2), PT.poof, { f: { "aabb.x": 0.5, "aabb.y": 1, "aabb.z": 0.5 }, eye: 0 }); },
  // موجة صدع جديدة: البوابة تنضم وتنفجر بلون الصدع
  riftWave(dim, c) { converge(dim, up(c, 2.2), 3, 18, "portal", { eye: 1.2 }); later(4, () => { P(dim, up(c, 2.2), PT.ender, { eye: 0 }); critBurst(dim, up(c, 2.9), 20, true); }); },
  riftClose(dim, c) { P(dim, c, PT.dragonBoom, { eye: 0 }); for (let i = 0; i < 10; i++) P(dim, c, PT.endrod, { eye: 0 }); },
  // ضربة الإيقاع: نوتات بثلاث درجات (كل مرتبة أعلى = نوتات أكثر وموجة أكبر)
  rhythm(dim, c, tier, r) {
    ring(dim, c, 0.8, 8 + tier * 4, PT.note, { note: tier === 1 ? [0.3, 0.9, 1] : tier === 2 ? [0.9, 0.4, 1] : [1, 0.85, 0.3], eye: 1.0 });
    if (tier >= 2) shockwave(dim, up(c, -0.9), 0.8, r, 6, { ids: [PT.puff], density: 1.4, y: 0.2, vout: 0.08 });
  },
  // الصد المثالي: شرر معدن بين اللاعب والمهاجم + لمعة
  parry(dim, c) { ring(dim, c, 0.5, 10, PT.spark, { d: { x: 0.3, y: 0.3, z: 0.3 }, eye: 0.8 }); sphereOut(dim, c, 10, PT.basicCrit, 1, { eye: 0.8 }); P(dim, c, PT.endrod, { eye: 0.8 }); },
  // الرد (Counter): هلال ذهبي سريع على الهدف
  counter(dim, c, from) { WEAPON.slash(dim, c, norm(sub(c, from)), 1.1, 1.8, 30, [PT.wax, PT.glow], { c: PAL.gold, steps: 1, n: 14, eye: 1.0 }); },
};
// هلال القمر (ثعلب الحجاب): قوس لمعات End Rod (يبقى ويرسم الهلال) + توهج بنفسجي
MONSTER.moonStep = (dim, pos, dir) => {
  const f = norm(dir), side = right(flat(f)), normal = cross(f, side);
  arc(dim, add(pos, f, -1.2), normal.x || normal.y || normal.z ? normal : { x: 0, y: 1, z: 0 }, f, 1.5, -1.0, 1.0, 7, PT.endrod, { eye: 1.2 });
  P(dim, pos, PT.glow, { c: [0.8, 0.5, 1], eye: 1.2 });
};

// ═══════════════ الماغماموث: بركان يمشي — لهب المشعل، لهب الكيان، حمم، دخان النار الكبير، غبار وحصى (v1.31) ═══════════════
const fireUp = (dim, p, n, s0, s1, j = 0.15, eye = 1.0) => { for (let q = 0; q < n; q++) P(dim, { x: p.x + rnd(-0.3, 0.3), y: p.y, z: p.z + rnd(-0.3, 0.3) }, PT.flame, { d: { x: rnd(-j, j), y: 1, z: rnd(-j, j) }, sp: rnd(s0, s1), eye }); };
Object.assign(MONSTER, {
  // الدكّة: انفجار + موجة غبار وحصى تكبر + أعمدة دخان بركاني حوالين الرجل + حمم تنط
  mamStomp(dim, C) {
    P(dim, up(C, 0.6), PT.boom, { eye: 0 });
    shockwave(dim, C, 1.0, 5.2, 8, { ids: [PT.puff, PT.gravel], density: 1.3, y: 0.25, vout: 0.07, max: 40 });
    for (let i = 0; i < 4; i++) { const a = i * 1.571 + 0.4; P(dim, { x: C.x + Math.cos(a) * 1.6, y: C.y + 0.3, z: C.z + Math.sin(a) * 1.6 }, PT.campfire, { eye: 0 }); }
    for (let i = 0; i < 8; i++) P(dim, up(C, 0.5), PT.lava, { eye: 0 });
  },
  // شق ماغما يتوهج قبل ما ينفجر: جمرة + لهب واطي + خيط دخان
  mamCrack(dim, p) {
    P(dim, up(p, 0.15), PT.lava, { eye: 1.0 });
    for (let q = 0; q < 2; q++) P(dim, { x: p.x + rnd(-0.25, 0.25), y: p.y + 0.1, z: p.z + rnd(-0.25, 0.25) }, PT.flame, { d: { x: 0, y: 1, z: 0 }, sp: 0.3, eye: 1.0 });
    P(dim, up(p, 0.3), PT.smoke, { eye: 1.0 });
  },
  // نافورة ماغما من الشق: عمود لهب سريع لفوق + لسانين كبار + حمم، والنقاط الكبيرة انفجار ودخان بركاني
  mamErupt(dim, p, big) {
    fireUp(dim, up(p, 0.15), 7, 2.2, 4.2);
    P(dim, up(p, 0.3), PT.bigFlame, { eye: 1.0 }); P(dim, up(p, 1.0), PT.bigFlame, { eye: 1.0 });
    P(dim, up(p, 0.4), PT.lava, { eye: 1.0 }); P(dim, up(p, 0.4), PT.lava, { eye: 1.0 });
    if (big) { P(dim, up(p, 0.6), PT.boom, { eye: 1.2 }); P(dim, up(p, 0.5), PT.campfire, { eye: 1.2 }); }
  },
  // دخان من الخرطوم أثناء النفخ (حرارة)
  mamSnort(dim, M) { P(dim, M, PT.smoke, { eye: 1.2 }); },
  // حك الأرض قبل الاندفاع: حصى وغبار ينرمي لورا + بخار من الخرطوم
  mamPaw(dim, L, d) {
    const f = flat(d), foot = { x: L.x + f.x * 1.6, y: L.y + 0.2, z: L.z + f.z * 1.6 };
    for (let i = 0; i < 3; i++) P(dim, { x: foot.x + rnd(-0.6, 0.6), y: foot.y + rnd(0, 0.5), z: foot.z + rnd(-0.6, 0.6) }, PT.gravel, { eye: 1.0 });
    for (let i = 0; i < 3; i++) P(dim, foot, PT.puff, { v: { x: -f.x * 0.18 + rnd(-0.06, 0.06), y: 0.06, z: -f.z * 0.18 + rnd(-0.06, 0.06) }, eye: 1.0 });
    P(dim, { x: L.x + f.x * 3.4, y: L.y + 2.2, z: L.z + f.z * 3.4 }, PT.whiteSmoke, { eye: 1.0 });
  },
  // انطلاقة الاندفاع: زئير (نفخات زئير الـRavager) + حلقة غبار
  mamCharge(dim, L, d) { const f = flat(d); P(dim, { x: L.x + f.x * 3, y: L.y + 2.4, z: L.z + f.z * 3 }, PT.roar, { eye: 1.6 }); dustRing(dim, L, 1.4, 16, 0.35); },
  // أثر الاندفاع: غبار يطلع من الجنبين + لهب ورا
  mamTrail(dim, L, d) {
    const f = flat(d), r = right(f);
    for (const s of [-1, 1]) P(dim, { x: L.x + r.x * s * 1.5, y: L.y + 0.3, z: L.z + r.z * s * 1.5 }, PT.puff, { v: { x: r.x * s * 0.12, y: 0.05, z: r.z * s * 0.12 }, eye: 1.0 });
    P(dim, { x: L.x - f.x * 2, y: L.y + 0.4, z: L.z - f.z * 2 }, PT.bigFlame, { eye: 1.0 });
  },
  // رفعة الأنياب: عمود لهب ينفجر من تحت الهدف + شرر + حمم
  mamToss(dim, at) { fireUp(dim, up(at, 0.1), 12, 2.5, 5, 0.2, 1.2); P(dim, up(at, 0.5), PT.boom, { eye: 1.4 }); critBurst(dim, up(at, 1.2), 20); for (let i = 0; i < 4; i++) P(dim, up(at, 0.3), PT.lava, { eye: 1.2 }); },
  // اصطدام بجدار: انفجار + موجة غبار وحصى + حصى يتساقط
  mamCrash(dim, at) {
    P(dim, up(at, 1.2), PT.boom, { eye: 0 });
    shockwave(dim, at, 0.8, 3.5, 6, { ids: [PT.puff, PT.gravel], density: 1.4, y: 0.3, vout: 0.06 });
    for (let i = 0; i < 8; i++) P(dim, { x: at.x + rnd(-1.5, 1.5), y: at.y + rnd(0.5, 3), z: at.z + rnd(-1.5, 1.5) }, PT.gravel, { eye: 0 });
  },
  // ثوران التاج (قصف بركاني): عمود لهب عالي + حمم كثيرة + عمود دخان بركاني
  mamEruptCrown(dim, top) {
    fireUp(dim, top, 16, 3, 6, 0.25, 0);
    for (let i = 0; i < 10; i++) P(dim, top, PT.lava, { eye: 0 });
    for (let i = 0; i < 4; i++) P(dim, { x: top.x + rnd(-0.5, 0.5), y: top.y + i * 0.6, z: top.z + rnd(-0.5, 0.5) }, PT.campfire, { eye: 0 });
    P(dim, top, PT.boom, { eye: 0 });
  },
  // ذيل الصخرة النارية: دخان أسود وجمرة (كل ثالث نقطة دخان بركاني كبير)
  mamBombTrail(dim, pos, k) { P(dim, pos, k % 3 === 0 ? PT.campfire : PT.smoke, { eye: 1.0 }); if (k % 2 === 0) P(dim, pos, PT.lava, { eye: 1.0 }); },
  // سقوط الصخرة: انفجار + موجة غبار وحصى صغيرة + دخان + حمم
  mamBombHit(dim, to) {
    P(dim, up(to, 0.6), PT.boom, { eye: 1.4 });
    shockwave(dim, to, 0.6, 2.6, 4, { ids: [PT.puff, PT.gravel], density: 1.4, y: 0.2, vout: 0.05, max: 24 });
    P(dim, up(to, 0.3), PT.campfire, { eye: 1.4 });
    for (let i = 0; i < 3; i++) P(dim, up(to, 0.3), PT.lava, { eye: 1.2 });
  },
  // شحن درع الماغما: لهب ينسحب من حواليه لجسمه + دخان
  mamArmorCharge(dim, L) {
    for (let i = 0; i < 6; i++) { const a = Math.random() * 6.283; P(dim, { x: L.x + Math.cos(a) * 3.2, y: L.y + rnd(0.4, 3.2), z: L.z + Math.sin(a) * 3.2 }, PT.flame, { d: { x: -Math.cos(a), y: 0.1, z: -Math.sin(a) }, sp: 1.6, eye: 1.0 }); }
    P(dim, up(L, rnd(1, 3)), PT.smoke, { eye: 1.0 });
  },
  // اشتعال الدرع: انفجار ضخم + حلقتين لهب تنطلق لبرا + حمم
  mamArmor(dim, L) {
    P(dim, up(L, 2), PT.hugeBoom, { eye: 0 });
    ring(dim, up(L, 0.3), 2.4, 28, PT.flame, { out: 1.0, up: 0.15, sp: 1.6, eye: 1.0 });
    ring(dim, up(L, 1.8), 2.2, 20, PT.flame, { out: 1.0, up: 0.3, sp: 1.2, eye: 1.0 });
    for (let i = 0; i < 10; i++) P(dim, up(L, 2.5), PT.lava, { eye: 0 });
  },
});

// ═══════════════ ثعلب الحجاب: نار الثعلب (لهب الأرواح) + توهج بنفسجي + بوابة + لمعات القمر (v1.31) ═══════════════
const FOX_V = [0.7, 0.45, 1], FOX_C = [0.4, 0.85, 1];
Object.assign(MONSTER, {
  // استدعاء الثعبان: حلقة لهب أرواح عند رجليه + جزيئات بوابة تنضم
  foxSummon(dim, L) { ring(dim, up(L, 0.1), 1.3, 14, PT.soulFlame, { eye: 1.0 }); converge(dim, up(L, 1.2), 2.2, 10, "portal", { eye: 1.0 }); },
  // لسان نار الثعلب يزحف: لهب الأرواح، والرأس (أول لسان) يترك روح طالعة وتوهج بنفسجي
  foxWisp(dim, p, i) {
    P(dim, up(p, -0.3), PT.soulFlame, { eye: 1.0 });
    if (i === 0) { P(dim, p, PT.glow, { c: FOX_V, eye: 1.0 }); P(dim, up(p, -0.2), PT.soul, { d: { x: 0, y: 0.4, z: 0 }, eye: 1.0 }); }
    else if (i % 3 === 0) P(dim, p, PT.glow, { c: FOX_C, eye: 1.0 });
    if (i % 2 === 1) P(dim, up(p, -0.1), PT.breath, { eye: 1.0 });            // ذيل بنفسجي (نَفَس التنين) بين الألسنة
  },
  // إصابة بنار الثعلب: شرر سحري + حلقة لهب أرواح صغيرة تنفتح + لمعة
  foxHit(dim, c) { critBurst(dim, c, 14, true); ring(dim, up(c, -0.6), 0.6, 8, PT.soulFlame, { out: 0.6, sp: 0.4, eye: 1.0 }); P(dim, c, PT.endrod, { eye: 1.0 }); },
  // انقسام الظلال: انفجار عين الإندر + غيمة بوابة
  foxSplit(dim, L) { P(dim, up(L, 1), PT.ender, { eye: 0 }); for (let i = 0; i < 14; i++) P(dim, { x: L.x + rnd(-0.6, 0.6), y: L.y + rnd(0, 1.8), z: L.z + rnd(-0.6, 0.6) }, PT.portal, { eye: 0.9 }); },
  // أثر الدوران: طيف بوابة + لهب أرواح (الأصلي بنفسجي)
  foxAfter(dim, p, j) { P(dim, up(p, 0.8), PT.portal, { eye: 1.0 }); if (j === 0) P(dim, up(p, 1.2), PT.glow, { c: FOX_V, eye: 1.0 }); else P(dim, up(p, 0.1), PT.soulFlame, { eye: 1.0 }); },
  // الانهيار: حلقة صدمة + انفجار إندر + موجة لهب أرواح وتوهج تتوسع + لمعات قمر
  foxCollapse(dim, C) {
    P(dim, up(C, 1.2), PT.sonic, { eye: 0 }); P(dim, up(C, 1.0), PT.ender, { eye: 0 });
    shockwave(dim, C, 0.6, 3.2, 6, { ids: [PT.soulFlame, PT.glow], c: FOX_V, density: 1.6, y: 0.15, max: 36 });
    for (let i = 0; i < 8; i++) { const u = { x: rnd(-1, 1), y: rnd(0, 1), z: rnd(-1, 1) }; P(dim, { x: C.x + u.x * 1.4, y: C.y + 0.6 + u.y * 1.6, z: C.z + u.z * 1.4 }, PT.endrod, { eye: 1.0 }); }
    critBurst(dim, up(C, 1.4), 24, true);
  },
  // تبخر الظل: نفخة موت + بوابة
  foxVanish(dim, L) { P(dim, up(L, 0.8), PT.poof, { f: { "aabb.x": 0.4, "aabb.y": 0.6, "aabb.z": 0.4 }, eye: 0.9 }); for (let i = 0; i < 8; i++) P(dim, { x: L.x + rnd(-0.5, 0.5), y: L.y + rnd(0.2, 1.4), z: L.z + rnd(-0.5, 0.5) }, PT.portal, { eye: 0.9 }); },
  // غيمة مطر الشمس: سحابة نَفَس التنين البنفسجية فوق المنطقة
  foxCloud(dim, c, r) { P(dim, c, PT.breathCloud, { f: { cloud_radius: r, cloud_lifetime: 0.1, particle_multiplier: 3 }, eye: 0 }); },
  // قطرة نار ثعلب تنزل: لهب أرواح ينزل نقطة نقطة (خط مطر)
  foxRain(dim, x, y, z) { seq(5, 1, (i) => P(dim, { x, y: y + 5.2 - i * 1.05, z }, PT.soulFlame, { eye: 1.0 })); },
  // نزول القطرة: حلقة لهب أرواح صغيرة + روح سكلك طالعة + توهج
  foxDrop(dim, p) { ring(dim, up(p, 0.1), 0.45, 6, PT.soulFlame, { out: 0.5, sp: 0.3, eye: 1.0 }); P(dim, up(p, 0.2), PT.sculkSoul, { d: { x: 0, y: 0.6, z: 0 }, eye: 1.0 }); P(dim, up(p, 0.3), PT.glow, { c: FOX_C, eye: 1.0 }); },
  // رفع القمر: هالة قمر فوقه (لمعات End Rod + توهج بنفسجي) وانفجار إندر بنصها
  foxMoonRise(dim, L) { ring(dim, up(L, 4.2), 1.6, 20, PT.endrod, { eye: 0 }); ring(dim, up(L, 4.2), 1.15, 14, PT.glow, { c: FOX_V, eye: 0 }); P(dim, up(L, 4.2), PT.ender, { eye: 0 }); critBurst(dim, up(L, 1.5), 20, true); },
  // الضحية تنرفع: لولب لمعات قمر حواليها + حلقة لهب أرواح تحتها
  foxLift(dim, at) { helix(dim, at, 0.8, 2.4, 1.5, 12, PT.endrod, { strands: 2, eye: 1.2 }); ring(dim, up(at, 0.1), 1.0, 10, PT.soulFlame, { eye: 1.0 }); },
  // إصابة الهلال: شرر سحري ولمعات
  foxMoonHit(dim, c) { critBurst(dim, c, 16, true); for (let i = 0; i < 4; i++) P(dim, { x: c.x + rnd(-0.6, 0.6), y: c.y + rnd(-0.4, 0.6), z: c.z + rnd(-0.6, 0.6) }, PT.endrod, { eye: 1.0 }); },
});

// ═══════════════ الدب الرمادي: قوة خام — زئير الـRavager، غبار وحصى، شرر حرج، خدوش بلون العظم ودم (v1.31) ═══════════════
const BONE_C = [0.96, 0.94, 0.86], BLOOD_C = [0.75, 0.05, 0.06];
Object.assign(MONSTER, {
  // زئير: نفخات زئير الـRavager من الفم (40 نفخة) — ما ترسم إذا الفم لاصق بعين لاعب
  bearRoar(dim, L, f) { P(dim, { x: L.x + f.x * 1.4, y: L.y + 2.7, z: L.z + f.z * 1.4 }, PT.roar, { eye: 1.6 }); },
  // المسكة: غبار تحت الرجلين + شرر
  bearGrab(dim, hold) { dustRing(dim, up(hold, -0.7), 0.6, 12, 0.25); critBurst(dim, up(hold, 0.6), 10); },
  // العصرة: حلقة غبار تنضغط على الخصر + شرر حرج + طقطقة عظم (شرر أبيض)
  bearCrush(dim, at) {
    ring(dim, up(at, 0.55), 1.1, 12, PT.puff, { vout: -0.1, eye: 0.6 });
    P(dim, up(at, 0.6), PT.crit, { n: 18, eye: 0.6 });
    for (let i = 0; i < 6; i++) P(dim, { x: at.x + rnd(-0.4, 0.4), y: at.y + rnd(0.4, 1.0), z: at.z + rnd(-0.4, 0.4) }, PT.spark, { d: { x: rnd(-0.4, 0.4), y: rnd(0, 0.3), z: rnd(-0.4, 0.4) }, eye: 0.6 });
  },
  // فلت من المسكة / ترنح: غبار وشرر
  bearBreak(dim, c) { dustRing(dim, up(c, -0.9), 0.6, 14, 0.3); critBurst(dim, c, 12); },
  // لطمة مخالب: 3 أهلّة متوازية (لمعات بلون العظم + شرر أبيض) تنرسم من فوق لتحت خلال تكين
  bearSwipe(dim, L, f, side) {
    const c = { x: L.x + f.x * 1.1, y: L.y + 1.95, z: L.z + f.z * 1.1 }, s = side || 1;
    for (let k = -1; k <= 1; k++) slash(dim, up(c, k * 0.26), f, 1.25 + k * 0.08, 1.8, s * 55, [PT.wax, PT.spark], { c: BONE_C, steps: 2, n: 12, side: s, d: { x: 0, y: -0.15, z: 0 }, eye: 1.0 });
    later(2, () => P(dim, add(up(c, -1.6), flat(f), 0.8), PT.puff, { v: { x: f.x * 0.1, y: 0.02, z: f.z * 0.1 }, eye: 1.0 }));
  },
  // خدوش على جسم اللاعب: 3 خطوط مخالب بلون العظم وفوقها خطوط دم، وقطرات دم تنزل
  bearClaw(dim, at, from, side, top = 1.35) {
    const f = flat(sub(at, from)), c = { x: at.x, y: at.y + top - 0.5, z: at.z };
    claws(dim, c, f, side * 38, [PT.wax], { c: BONE_C, eye: 0.5 });
    claws(dim, add(c, f, -0.04), f, side * 38, [PT.glow], { c: BLOOD_C, eye: 0.5 });
    P(dim, c, PT.crit, { n: 10, eye: 0.6 });
    for (let i = 0; i < 3; i++) P(dim, { x: at.x + rnd(-0.3, 0.3), y: at.y + rnd(0.5, 1.0), z: at.z + rnd(-0.3, 0.3) }, PT.glow, { c: BLOOD_C, d: { x: 0, y: -0.6, z: 0 }, eye: 0.5 });
  },
  // نداء الجراء: زئير + حلقة غبار
  bearCall(dim, L, f) { MONSTER.bearRoar(dim, L, f); dustRing(dim, L, 1.2, 18, 0.35); },
  // ظهور جرو: نفخة موت صغيرة (عكسها) + غبار
  bearCubPop(dim, pos) { P(dim, up(pos, 0.4), PT.poof, { f: { "aabb.x": 0.3, "aabb.y": 0.4, "aabb.z": 0.3 }, eye: 0.8 }); dustRing(dim, pos, 0.4, 8, 0.2); },
  // السبات: نبتات تكبر (رشة سماد العظم) = تعافي
  bearHeal(dim, L) { P(dim, up(L, 0.8), PT.crop, { eye: 0 }); for (let i = 0; i < 3; i++) P(dim, { x: L.x + rnd(-1, 1), y: L.y + rnd(0.6, 2.2), z: L.z + rnd(-1, 1) }, PT.happy, { eye: 0 }); },
  // صحوة الغضب: زئير + موجة غبار وحصى + شرر + غضب فوق راسه
  bearWrath(dim, L, f) {
    MONSTER.bearRoar(dim, L, f);
    shockwave(dim, L, 1.0, 5.5, 8, { ids: [PT.puff, PT.gravel], density: 1.3, y: 0.25, vout: 0.07, max: 40 });
    critBurst(dim, up(L, 2.4), 20);
    for (let i = 0; i < 4; i++) P(dim, { x: L.x + rnd(-0.6, 0.6), y: L.y + 3.4, z: L.z + rnd(-0.6, 0.6) }, PT.angry, { eye: 0 });
  },
});
