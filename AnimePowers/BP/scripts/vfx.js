// ═════════════════════ مكتبة المؤثرات: جزيئات ماينكرافت الأصلية بس ═════════════════════
// كل جزيء هنا معرفه "minecraft:..." بتعريف موجانغ نفسه (حجمه، عمره، حركته، تكستشره). المود ما يصنع جزيئات.
// الجودة تجي من التركيب: حلقات، موجات صدمة، لولب، أعمدة، أقواس شطر، خطوط، انضمام لنقطة، وتوقيت (تمهيد ← ضربة ← أثر).
// كل قدرة إلها مفردات بصرية خاصة (THEME) حتى المهارات ما تتشابه:
//   الحديد: شرر معدن + نفخات صدمة | الريح: دوامات الريح الحقيقية (wind charge) | الصدى: حلقات Warden والسكلك والنوتات
//   البلور: لمعات End Rod + انفجار عين الإندر | المحاسب: حروف طاولة السحر + شرار ذهبي | المسافة: جزيئات البوابة ونَفَس التنين
//   القوانين: حروف السحر + أعمدة نور | النجوم: End Rod + شرار ملوّن + انفجارات كبيرة | الصفات: غبار الحصى، دم، ريح، عين
import { world, system, MolangVariableMap } from "@minecraft/server";

// ───────────── معرفات الجزيئات (كلها موجودة بقائمة موجانغ الرسمية: tools/sim/vanilla_particle_ids.txt) ─────────────
export const PT = {
  spark: "minecraft:electric_spark_particle",       // شرارة بيضا قصيرة (حك النحاس): direction
  glow: "minecraft:glow_particle",                  // نقطة متوهجة تقبل أي لون: color + direction
  endrod: "minecraft:endrod",                       // لمعة End Rod بيضا تومض وتطفو
  wax: "minecraft:wax_particle",                    // نجمة صغيرة ملونة: color + direction
  crit: "minecraft:critical_hit_emitter",           // شرر الضربة الحرجة: particle_count
  magicCrit: "minecraft:magic_critical_hit_emitter",
  basicCrit: "minecraft:basic_crit_particle",       // شرارة حرجة وحدة: direction
  gust: "minecraft:wind_explosion_emitter",         // انفجار شحنة الريح (دوامات gust)
  bigGust: "minecraft:breeze_wind_explosion_emitter", // انفجار ريح البريز الكبير (±4 بلوكات)
  smallGust: "minecraft:wind_charged_emitter",      // دوامتين ريح صغار
  sonic: "minecraft:sonic_explosion",               // حلقة صدمة الـWarden
  shriek: "minecraft:shriek_particle",              // حلقات الـShrieker تصعد (4 ثواني)
  note: "minecraft:note_particle",                  // نوتة موسيقية: note_color
  sculk: "minecraft:sculk_charge_particle",         // شحنة سكلك: direction
  sculkPop: "minecraft:sculk_charge_pop_particle",
  sculkSoul: "minecraft:sculk_soul_particle",       // روح السكلك: direction
  soul: "minecraft:soul_particle",                  // روح رمل الأرواح: direction
  portal: "minecraft:basic_portal_particle",        // جزيء البوابة البنفسجي
  portalIn: "minecraft:portal_directional",         // جزيء بوابة ينضم لنقطة: direction = مكان بدايته
  portalUp: "minecraft:portal_reverse_particle",
  breath: "minecraft:dragon_breath_trail",          // نَفَس التنين البنفسجي الواكف
  breathCloud: "minecraft:dragon_breath_lingering", // سحابة نَفَس التنين على الأرض: cloud_radius × particle_multiplier
  ender: "minecraft:eyeofender_death_explode_particle", // انفجار عين الإندر البنفسجي الوردي
  glyph: "minecraft:enchanting_table_particle",     // حروف طاولة السحر: تنضم لنقطة من direction
  conduit: "minecraft:conduit_particle",
  totem: "minecraft:totem_particle",                // انفجار التوتم الأخضر الذهبي
  happy: "minecraft:villager_happy",
  angry: "minecraft:villager_angry",
  heart: "minecraft:heart_particle",
  roar: "minecraft:knockback_roar_particle",        // نفخات زئير الـRavager البيضا
  puff: "minecraft:explosion_particle",             // نفخة دخان: velocity
  boom: "minecraft:large_explosion",
  hugeBoom: "minecraft:huge_explosion_emitter",
  dragonBoom: "minecraft:dragon_death_explosion_emitter",
  poof: "minecraft:death_explosion_emitter",        // نفخة موت الموب: aabb
  egg: "minecraft:egg_destroy_emitter",
  smoke: "minecraft:basic_smoke_particle",
  whiteSmoke: "minecraft:white_smoke_particle",
  campfire: "minecraft:campfire_smoke_particle",    // دخان النار الكبير (5 ثواني)
  flame: "minecraft:small_flame_particle",          // لهب المشعل: direction + particle_initial_speed
  bigFlame: "minecraft:mobflame_single",            // لهب الكيان المحترق (0.5 بلوكة)
  lava: "minecraft:lava_particle",
  soulFlame: "minecraft:small_soul_fire_flame",
  blueFlame: "minecraft:blue_flame_particle",
  cflame: "minecraft:colored_flame_particle",       // لهب ملوّن (سبرايته سماوي: للبارد بس)
  sparkler: "minecraft:sparkler_emitter",           // شرارة ملونة تومض: color
  spell: "minecraft:mobspell_emitter",              // دوامة جرعة ملونة: color
  splash: "minecraft:splash_spell_emitter",
  gravel: "minecraft:falling_dust_gravel_particle", // غبار حصى ينزل
  redDust: "minecraft:redstone_wire_dust_particle",
  snow: "minecraft:snowflake_particle",
  ink: "minecraft:squid_ink_bubble",
  tear: "minecraft:obsidian_tear_particle",
  crop: "minecraft:crop_growth_emitter",
};

// ───────────── الميزانية والكاميرا ─────────────
// حد عام لكل تك (مشترك مع كل المود) حتى ما يثقل على الموبايل، وما نرسم جزيء لاصق بعين اللاعب (يغطي الشاشة)
export const VFX_LIMIT = 260;
let used = 0;
system.runInterval(() => { used = 0; }, 1);
export const budgetLeft = () => VFX_LIMIT - used;
const eyes = [];
system.runInterval(() => {
  eyes.length = 0;
  for (const p of world.getAllPlayers()) { try { const h = p.getHeadLocation(); eyes.push({ d: p.dimension.id, x: h.x, y: h.y, z: h.z }); } catch (e) { /* */ } }
}, 2);
export function nearEye(dim, loc, r) {
  for (const c of eyes) {
    if (c.d !== dim.id) continue;
    const dx = c.x - loc.x, dy = c.y - loc.y, dz = c.z - loc.z;
    if (dx * dx + dy * dy + dz * dz < r * r) return true;
  }
  return false;
}
export const later = (t, fn) => system.runTimeout(() => { try { fn(); } catch (e) { /* */ } }, Math.max(1, Math.round(t)));

// ───────────── الإطلاق الأساسي ─────────────
// o: { c: لون [r,g,b] (variable.color)، a: شفافية، d: اتجاه (variable.direction)، v: سرعة (variable.velocity لنفخة الدخان)،
//      sp: سرعة ابتدائية (لهب المشعل)، n: عدد (منبعثات الشرر)، note: لون النوتة، f: {اسم: رقم} متغيرات إضافية، eye: نصف قطر تجنب العين (0 = بدون) }
export function P(dim, loc, id, o) {
  if (used >= VFX_LIMIT) return false;
  const eye = o && o.eye !== undefined ? o.eye : 0.9;
  if (eye > 0 && nearEye(dim, loc, eye)) return false;
  used++;
  try {
    const m = new MolangVariableMap();
    const c = (o && o.c) || [1, 1, 1];
    m.setColorRGBA("variable.color", { red: c[0], green: c[1], blue: c[2], alpha: o && o.a !== undefined ? o.a : 1 });
    m.setVector3("variable.direction", (o && o.d) || { x: 0, y: 0, z: 0 });
    if (o) {
      if (o.v) m.setVector3("variable.velocity", o.v);
      if (o.sp !== undefined) m.setFloat("variable.particle_initial_speed", o.sp);
      if (o.n !== undefined) m.setFloat("variable.particle_count", o.n);
      if (o.note) m.setColorRGB("variable.note_color", { red: o.note[0], green: o.note[1], blue: o.note[2] });
      if (o.f) for (const k of Object.keys(o.f)) m.setFloat("variable." + k, o.f[k]);
    }
    dim.spawnParticle(id, loc, m);
    return true;
  } catch (e) { return false; }
}

// ───────────── رياضيات صغيرة ─────────────
const TAU = Math.PI * 2;
export const add = (a, b, k = 1) => ({ x: a.x + b.x * k, y: a.y + b.y * k, z: a.z + b.z * k });
export const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
export const len = (a) => Math.hypot(a.x, a.y, a.z);
export const norm = (a) => { const l = len(a) || 1; return { x: a.x / l, y: a.y / l, z: a.z / l }; };
export const cross = (a, b) => ({ x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x });
export const lerp = (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t });
const scale = (a, k) => ({ x: a.x * k, y: a.y * k, z: a.z * k });
// قاعدة متعامدة لمستوى عموده n: ترجع u, v
export function basis(n) {
  const N = norm(n);
  const ref = Math.abs(N.y) < 0.95 ? { x: 0, y: 1, z: 0 } : { x: 1, y: 0, z: 0 };
  const u = norm(cross(ref, N));
  return { u, v: cross(N, u) };
}
export const rnd = (a, b) => a + Math.random() * (b - a);
export const rndUnit = () => { const a = Math.random() * TAU, z = Math.random() * 2 - 1, r = Math.sqrt(1 - z * z); return { x: Math.cos(a) * r, y: z, z: Math.sin(a) * r }; };

// ───────────── الموتيفات ─────────────
// حلقة: n نقطة على دائرة نصف قطرها r حول c (المستوى عموده o.normal، افتراضي أفقي). o.ph طور الزاوية.
// o.out: سرعة للخارج (للجزيئات اللي تقبل direction)، o.vout: سرعة للخارج لنفخة الدخان (velocity)، o.up: ارتفاع السرعة.
export function ring(dim, c, r, n, id, o = {}) {
  const { u, v } = o.normal ? basis(o.normal) : { u: { x: 1, y: 0, z: 0 }, v: { x: 0, y: 0, z: 1 } };
  const ph = o.ph || 0;
  for (let i = 0; i < n; i++) {
    const a = ph + (i / n) * TAU, ca = Math.cos(a), sa = Math.sin(a);
    const dir = { x: u.x * ca + v.x * sa, y: u.y * ca + v.y * sa, z: u.z * ca + v.z * sa };
    const q = { ...o };
    if (o.out !== undefined) q.d = { x: dir.x * o.out, y: dir.y * o.out + (o.up || 0), z: dir.z * o.out };
    if (o.vout !== undefined) q.v = { x: dir.x * o.vout, y: dir.y * o.vout + (o.up || 0), z: dir.z * o.vout };
    if (o.ids) { P(dim, add(c, dir, r), o.ids[i % o.ids.length], q); continue; }
    P(dim, add(c, dir, r), id, q);
  }
}
// قوس: من الزاوية a0 للزاوية a1 (راديان) بمستوى عموده normal، والزاوية 0 = اتجاه ref
export function arc(dim, c, normal, ref, r, a0, a1, n, id, o = {}) {
  const N = norm(normal), U = norm(sub(ref, scale(N, ref.x * N.x + ref.y * N.y + ref.z * N.z))), V = cross(N, U);
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0.5 : i / (n - 1), a = a0 + (a1 - a0) * t, ca = Math.cos(a), sa = Math.sin(a);
    const dir = { x: U.x * ca + V.x * sa, y: U.y * ca + V.y * sa, z: U.z * ca + V.z * sa };
    const rr = o.taper ? r * (1 - o.taper * Math.abs(t - 0.5) * 2) : r;
    const q = { ...o };
    if (o.out !== undefined) q.d = scale(dir, o.out);
    if (o.tan !== undefined) { const tg = { x: -U.x * sa + V.x * ca, y: -U.y * sa + V.y * ca, z: -U.z * sa + V.z * ca }; q.d = scale(tg, o.tan * Math.sign(a1 - a0)); }
    P(dim, add(c, dir, rr), o.ids ? o.ids[i % o.ids.length] : id, q);
  }
}
// خط منقط من a لـ b بخطوة step، مع رجفة j
export function line(dim, a, b, step, id, o = {}) {
  const L = len(sub(b, a)), n = Math.max(1, Math.round(L / step));
  for (let i = 0; i <= n; i++) {
    const p = lerp(a, b, i / n);
    if (o.j) { p.x += rnd(-o.j, o.j); p.y += rnd(-o.j, o.j); p.z += rnd(-o.j, o.j); }
    P(dim, p, o.ids ? o.ids[i % o.ids.length] : id, o);
  }
}
// لولب يصعد: strands خيوط، turns لفات، من c.y لـ c.y+h
export function helix(dim, c, r, h, turns, n, id, o = {}) {
  const strands = o.strands || 1, ph = o.ph || 0;
  for (let s = 0; s < strands; s++) {
    for (let i = 0; i < n; i++) {
      const t = i / Math.max(1, n - 1), a = ph + (s / strands) * TAU + t * turns * TAU, rr = r * (o.taper ? 1 - o.taper * t : 1);
      P(dim, { x: c.x + Math.cos(a) * rr, y: c.y + t * h, z: c.z + Math.sin(a) * rr }, o.ids ? o.ids[(i + s) % o.ids.length] : id, o);
    }
  }
}
// عمود من c لفوق بارتفاع h (رجفة أفقية j)
export function column(dim, c, h, n, id, o = {}) {
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0 : i / (n - 1);
    P(dim, { x: c.x + (o.j ? rnd(-o.j, o.j) : 0), y: c.y + t * h, z: c.z + (o.j ? rnd(-o.j, o.j) : 0) }, o.ids ? o.ids[i % o.ids.length] : id, o);
  }
}
// انضمام لنقطة: جزيئات (البوابة/حروف السحر/الكوندويت) تبدأ على كرة نصف قطرها r وتنسحب لـ c بنفسها (هذا تعريفها الأصلي)
export function converge(dim, c, r, n, kind = "portal", o = {}) {
  for (let i = 0; i < n; i++) {
    const u = rndUnit();
    if (o.flat) u.y *= 0.25;
    const off = scale(norm(u), r * (o.rmin ? rnd(o.rmin, 1) : 1));
    if (kind === "conduit") P(dim, c, PT.conduit, { ...o, f: { direction_x: off.x, direction_y: off.y, direction_z: off.z } });
    else P(dim, c, kind === "glyph" ? PT.glyph : PT.portalIn, { ...o, d: off });
  }
}
// انفجار كروي: جزيء يقبل direction ينطلق للخارج بسرعة speed
export function sphereOut(dim, c, n, id, speed, o = {}) {
  for (let i = 0; i < n; i++) {
    const u = rndUnit();
    if (o.flat) u.y = Math.abs(u.y) * o.flat;
    P(dim, c, id, { ...o, d: scale(u, speed * rnd(0.6, 1)) });
  }
}
// موجة صدمة تكبر مع الوقت: من r0 لـ r1 خلال ticks، كل step تكات حلقة (كثافة density نقطة لكل بلوكة محيط)
export function shockwave(dim, c, r0, r1, ticks, o = {}) {
  const step = o.step || 2, density = o.density || 1.6, ids = o.ids || [PT.puff], y = o.y ?? 0.15;
  for (let t = 0; t <= ticks; t += step) {
    later(t, () => {
      const k = ticks ? t / ticks : 1, ease = 1 - (1 - k) * (1 - k), r = r0 + (r1 - r0) * ease;
      const n = Math.max(6, Math.min(o.max || 48, Math.round(TAU * r * density)));
      ring(dim, { x: c.x, y: c.y + y, z: c.z }, r, n, ids[0], { ...o, ids, ph: Math.random() });
    });
  }
}
// دوامة أرضية تنسحب للداخل: أذرع لولبية من r للمركز
export function spiralIn(dim, c, r, arms, n, id, o = {}) {
  const ph = o.ph || 0, tw = o.twist ?? 1.6;
  for (let a = 0; a < arms; a++) {
    for (let i = 0; i < n; i++) {
      const t = i / n, rr = r * (1 - t), ang = ph + (a / arms) * TAU + t * tw * Math.PI;
      P(dim, { x: c.x + Math.cos(ang) * rr, y: c.y + (o.lift ? o.lift * t : 0), z: c.z + Math.sin(ang) * rr }, o.ids ? o.ids[(i + a) % o.ids.length] : id, o);
    }
  }
}
// غبار أرضي ينطلق للخارج (نفخات دخان بسرعة velocity): حلقة صدمة على الأرض
export function dustRing(dim, c, r, n, speed, o = {}) {
  ring(dim, { x: c.x, y: c.y + (o.y ?? 0.15), z: c.z }, r, n, PT.puff, { vout: speed, up: o.up ?? 0.04, ph: Math.random(), eye: o.eye });
}
// شرر حرج بعدد: particle_count
export const critBurst = (dim, c, n = 16, magic = false) => P(dim, c, magic ? PT.magicCrit : PT.crit, { n: Math.min(32, n), eye: 1.1 });
// تسلسل: fn(i) كل every تك لـ count مرة
export function seq(count, every, fn) { for (let i = 0; i < count; i++) later(i * every + 1, () => fn(i)); }
