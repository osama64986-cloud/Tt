// إثيريا (Aetheria): مخطط المدينة 248×248 بلوكة بالضبط (مع السور). ما بيه أي استدعاء للعبة: بس يبني قائمة عمليات (ops)
// بإحداثيات المدينة: x من 0 (غرب) لـ 247 (شرق)، z من 0 (شمال) لـ 247 (جنوب)، y: -1 = سطح الأرض، 0 = أول بلوكة فوقها.
// city.js يحول العمليات لشبكة بلوكات (raster) ويقطعها مربعات ≤ 64×64 (حد بنية بيدروك 64×384×64) ويحطها بالعالم.
// كل الحالات (اتجاه الدرج والأبواب والأسرة والصناديق...) بأسماء بيدروك الحقيقية (tools/vanilla_block_states.json يفحصها).

export const CITY_SIZE = 248;
export const CITY_YMIN = -1;
export const CITY_YMAX = 46;
const M = (n) => "minecraft:" + n;
const AIR = M("air");

function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}
// تشويش ثابت لكل خلية (حتى نفس البذرة تعطي نفس المدينة بعد إعادة التشغيل)
export function hash3(x, y, z, s) {
  let h = (x * 374761393 + y * 668265263 + z * 2147483647 + s * 1442695041) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

// اتجاهات بيدروك (نفس اللي تحقق منها بالبنايات السابقة)
const SEQ = ["e", "s", "w", "n"];
const STAIR = { e: 0, w: 1, s: 2, n: 3 };                       // weirdo_direction = الجهة العالية (ظهر الدرجة)
const CARD = { e: "east", s: "south", w: "west", n: "north" };
const BED = { s: 0, w: 1, n: 2, e: 3 };                         // اتجاه الراس من القدم
const LADDER = { n: 2, s: 3, w: 4, e: 5 };                      // facing_direction = الجهة اللي يباوع لها السلم
const DV = { e: [1, 0], w: [-1, 0], s: [0, 1], n: [0, -1] };
const OPP = { e: "w", w: "e", s: "n", n: "s" };

// ───────────────────────── المخطط ─────────────────────────
export class CityPlan {
  constructor(seed) {
    this.seed = seed >>> 0;
    this.r = rng(seed);
    this.ops = [];
    this.pal = [null];                                          // 0 = فراغ (ما ينحط شي)
    this.palIdx = new Map();
    this.posts = [];                                            // أماكن الشخصيات: {type, x, y, z, r}
    this.chests = [];                                           // {x, y, z, loot}
    this.beds = [];                                             // {fx, y, fz, hx, hz}
    this.lights = 0;
    this.marks = {};
    this.used = new Uint8Array(CITY_SIZE * CITY_SIZE);          // خريطة إشغال: 1 = بناء فوق الأرض، 2 = طريق/رصيف، 4 = محجوز (ساحة فاضية)
  }
  mark(x1, z1, x2, z2, bit = 1) {
    const a = Math.max(0, Math.min(x1, x2)), b = Math.min(CITY_SIZE - 1, Math.max(x1, x2));
    const c = Math.max(0, Math.min(z1, z2)), d = Math.min(CITY_SIZE - 1, Math.max(z1, z2));
    for (let z = c; z <= d; z++) for (let x = a; x <= b; x++) this.used[z * CITY_SIZE + x] |= bit;
  }
  // المساحة فاضية (عشب بس)؟ يستعملها توزيع الأشجار والزهور حتى ما تغطي بناية أو طريق
  free(x1, z1, x2, z2, lo = 8, hi = CITY_SIZE - 9) {
    if (x1 < lo || z1 < lo || x2 > hi || z2 > hi) return false;
    for (let z = z1; z <= z2; z++) for (let x = x1; x <= x2; x++) if (this.used[z * CITY_SIZE + x]) return false;
    return true;
  }
  k(id, st) {
    const key = st ? id + JSON.stringify(st) : id;
    let i = this.palIdx.get(key);
    if (i === undefined) { i = this.pal.length; this.pal.push({ id, st: st || null }); this.palIdx.set(key, i); }
    return i;
  }
  box(x1, y1, z1, x2, y2, z2, id, st) {
    this.ops.push([0, Math.min(x1, x2), Math.min(y1, y2), Math.min(z1, z2), Math.max(x1, x2), Math.max(y1, y2), Math.max(z1, z2), this.k(id, st)]);
    if (Math.max(y1, y2) >= 0) this.mark(x1, z1, x2, z2, 1);
  }
  set(x, y, z, id, st) { this.ops.push([1, x, y, z, this.k(id, st)]); if (y >= 0) this.mark(x, z, x, z, 1); }
  // صندوق بخليط بلوكات (أوزان): كل خلية تختار حسب تشويش ثابت (حجر بطوب مكسور وطحلب...)
  mix(x1, y1, z1, x2, y2, z2, ids, weights, salt = 0) {
    const ks = ids.map((i) => (Array.isArray(i) ? this.k(i[0], i[1]) : this.k(i)));
    let tot = 0; const cum = weights.map((w) => (tot += w));
    this.ops.push([2, Math.min(x1, x2), Math.min(y1, y2), Math.min(z1, z2), Math.max(x1, x2), Math.max(y1, y2), Math.max(z1, z2), ks, cum.map((c) => c / tot), salt]);
    if (Math.max(y1, y2) >= 0) this.mark(x1, z1, x2, z2, 1);
  }
  frame(ox, oz, rot = 0) { return new Frame(this, ox, oz, rot); }
  post(type, x, y, z, r = 8) { this.posts.push({ type, x, y, z, r }); }
}

// إطار محلي لبناية (u شرق، v جنوب) مع دوران 0..3 (كل وحدة 90° مع عقارب الساعة)
export class Frame {
  constructor(P, ox, oz, rot) { this.P = P; this.ox = ox; this.oz = oz; this.rot = ((rot % 4) + 4) % 4; }
  xz(u, v) {
    switch (this.rot) {
      case 1: return [this.ox - v, this.oz + u];
      case 2: return [this.ox - u, this.oz - v];
      case 3: return [this.ox + v, this.oz - u];
      default: return [this.ox + u, this.oz + v];
    }
  }
  d(l) { return SEQ[(SEQ.indexOf(l) + this.rot) % 4]; }
  axis(a) { return a === "y" ? "y" : this.rot % 2 === 0 ? a : a === "x" ? "z" : "x"; }
  box(u1, y1, v1, u2, y2, v2, id, st) { const [a, b] = this.xz(u1, v1), [c, d] = this.xz(u2, v2); this.P.box(a, y1, b, c, y2, d, id, st); }
  mix(u1, y1, v1, u2, y2, v2, ids, w, salt) { const [a, b] = this.xz(u1, v1), [c, d] = this.xz(u2, v2); this.P.mix(a, y1, b, c, y2, d, ids, w, salt); }
  set(u, y, v, id, st) { const [x, z] = this.xz(u, v); this.P.set(x, y, z, id, st); }
  air(u1, y1, v1, u2, y2, v2) { this.box(u1, y1, v1, u2, y2, v2, AIR); }
  stair(u, y, v, id, dir, top = false) { this.set(u, y, v, id, { weirdo_direction: STAIR[this.d(dir)], upside_down_bit: !!top }); }
  slab(u, y, v, id, top = false) { this.set(u, y, v, id, { "minecraft:vertical_half": top ? "top" : "bottom" }); }
  slabs(u1, y, v1, u2, v2, id, top = false) { this.box(u1, y, v1, u2, y, v2, id, { "minecraft:vertical_half": top ? "top" : "bottom" }); }
  log(u, y, v, id, a = "y") { this.set(u, y, v, id, { pillar_axis: this.axis(a) }); }
  logs(u1, y1, v1, u2, y2, v2, id, a = "y") { this.box(u1, y1, v1, u2, y2, v2, id, { pillar_axis: this.axis(a) }); }
  card(u, y, v, id, dir, extra = {}) { this.set(u, y, v, id, { "minecraft:cardinal_direction": CARD[this.d(dir)], ...extra }); }
  door(u, y, v, id, out) {
    const c = CARD[this.d(out)];
    this.set(u, y, v, id, { "minecraft:cardinal_direction": c, door_hinge_bit: false, open_bit: false, upper_block_bit: false });
    this.set(u, y + 1, v, id, { "minecraft:cardinal_direction": c, door_hinge_bit: false, open_bit: false, upper_block_bit: true });
  }
  bed(u, y, v, head, color = "red") {
    const [du, dv] = DV[head], hu = u + du, hv = v + dv, wd = this.d(head);
    this.set(u, y, v, M("bed"), { direction: BED[wd], head_piece_bit: false, occupied_bit: false });
    this.set(hu, y, hv, M("bed"), { direction: BED[wd], head_piece_bit: true, occupied_bit: false });
    const [fx, fz] = this.xz(u, v), [hx, hz] = this.xz(hu, hv);
    this.P.beds.push({ fx, y, fz, hx, hz, color });
  }
  chest(u, y, v, face, loot) {
    this.card(u, y, v, M("chest"), face);
    const [x, z] = this.xz(u, v); this.P.chests.push({ x, y, z, loot });
  }
  barrel(u, y, v) { this.set(u, y, v, M("barrel"), { facing_direction: 1, open_bit: false }); }
  lantern(u, y, v, hanging = false, soul = false) { this.set(u, y, v, M(soul ? "soul_lantern" : "lantern"), { hanging }); this.P.lights++; }
  trap(u, y, v, id, top = true) { this.set(u, y, v, id, { direction: 0, open_bit: false, upside_down_bit: !!top }); }
  ladder(u, y1, y2, v, face) { for (let y = y1; y <= y2; y++) this.set(u, y, v, M("ladder"), { facing_direction: LADDER[this.d(face)] }); }
  leaves(u1, y1, v1, u2, y2, v2, id = M("oak_leaves")) { this.box(u1, y1, v1, u2, y2, v2, id, { persistent_bit: true, update_bit: false }); }
  post(type, u, y, v, r) { const [x, z] = this.xz(u, v); this.P.post(type, x, y, z, r); }
  flower(u, v, kind) { this.set(u, 0, v, M(kind)); }
  pot(u, y, v) { this.set(u, y, v, M("flower_pot"), { update_bit: false }); }
}

// ───────────────────────── المواد (لوحة القرون الوسطى من الصورة المرجعية) ─────────────────────────
const STONE = [M("stone_bricks"), M("mossy_stone_bricks"), M("cracked_stone_bricks"), M("andesite")];
const STONE_W = [70, 12, 10, 8];
const COBBLE = [M("cobblestone"), M("mossy_cobblestone"), M("andesite"), M("stone")];
const COBBLE_W = [60, 18, 14, 8];
const SB = M("stone_bricks"), SBS = M("stone_brick_stairs"), SBSL = M("stone_brick_slab"), CSB = M("chiseled_stone_bricks");
const PAND = M("polished_andesite"), SPR = M("spruce_planks"), SPL = M("spruce_log"), SST = M("spruce_stairs"), SSL = M("spruce_slab");
const DOK = M("dark_oak_planks"), DOS = M("dark_oak_stairs"), DSL = M("dark_oak_slab"), DLOG = M("dark_oak_log");
const DT = M("deepslate_tiles"), DTS = M("deepslate_tile_stairs"), DTSL = M("deepslate_tile_slab");
const SFENCE = M("spruce_fence"), STRAP = M("spruce_trapdoor"), SDOOR = M("spruce_door"), GPANE = M("glass_pane");
const SSPR = M("stripped_spruce_log");

// ───────────────────────── الأرض والطرق ─────────────────────────
function ground(P) {
  P.mix(0, -1, 0, 247, -1, 247, [[M("grass_block")], [M("grass_block")]], [1, 1], 1);
  // عشب وزهور بسيطة توزع بعدين بالحدائق؛ هنا الأرض بس
}
// رصف طريق: نمط "main" (طوب حجري بحواف أندسايت)، "cobble"، "dirt" (ممر ترابي)
function pave(P, x1, z1, x2, z2, style = "main", salt = 0) {
  if (style === "main") {
    P.mix(x1, -1, z1, x2, -1, z2, [SB, M("cracked_stone_bricks"), M("mossy_stone_bricks"), PAND], [74, 10, 6, 10], 11 + salt);
  } else if (style === "cobble") {
    P.mix(x1, -1, z1, x2, -1, z2, [M("cobblestone"), M("andesite"), M("gravel"), M("stone"), M("mossy_cobblestone")], [46, 22, 12, 12, 8], 21 + salt);
  } else if (style === "dirt") {
    P.mix(x1, -1, z1, x2, -1, z2, [M("grass_path"), M("coarse_dirt"), M("gravel")], [70, 18, 12], 31 + salt);
  } else if (style === "plaza") {
    P.mix(x1, -1, z1, x2, -1, z2, [PAND, M("smooth_stone"), SB], [50, 30, 20], 41 + salt);
  } else if (style === "market") {
    P.mix(x1, -1, z1, x2, -1, z2, [M("cobblestone"), SB, M("andesite"), M("mossy_cobblestone"), PAND], [40, 26, 16, 8, 10], 51 + salt);
  } else if (style === "walk") {                                                    // ممشى حديقة: حصى وتراب مدكوك
    P.mix(x1, -1, z1, x2, -1, z2, [M("gravel"), M("grass_path"), M("coarse_dirt")], [55, 35, 10], 61 + salt);
  }
  P.mark(x1, z1, x2, z2, 2);
}
// شارع رئيسي بحواف: الوسط حجر، الحافة بلوكة أندسايت مصقول، والكتف ممر ترابي
function street(P, x1, z1, x2, z2, salt = 0) {
  pave(P, x1, z1, x2, z2, "main", salt);
  if (x2 - x1 > z2 - z1) { P.box(x1, -1, z1, x2, -1, z1, PAND); P.box(x1, -1, z2, x2, -1, z2, PAND); }
  else { P.box(x1, -1, z1, x1, -1, z2, PAND); P.box(x2, -1, z1, x2, -1, z2, PAND); }
}

// عمود إنارة: قاعدة حجر، سياج، فانوس معلق تحت ذراع
function lamp(P, x, z, armDir = "e") {
  const F = P.frame(x, z, 0);
  F.set(0, 0, 0, M("stone_bricks"));
  F.box(0, 1, 0, 0, 3, 0, SFENCE);
  F.set(0, 4, 0, SPL, { pillar_axis: "y" });
  const [du, dv] = DV[armDir];
  F.set(du, 4, dv, SFENCE);
  F.lantern(du, 3, dv, true);
}
// شجرة: oak (تاج دائري)، spruce (مخروط)، birch (رفيعة)، bloom (أزاليا مزهرة للبساتين)
function tree(P, x, z, kind = "oak", h = 5) {
  const F = P.frame(x, z, 0);
  if (kind === "spruce") {
    F.logs(0, 0, 0, 0, h + 2, 0, SPL, "y");
    const L = M("spruce_leaves");
    for (let k = 0; k < 4; k++) {
      const y = h - 2 + k * 1, r = Math.max(0, 2 - Math.floor(k / 2));
      F.leaves(-r, y, -r, r, y, r, L);
      if (r >= 2) { F.air(-r, y, -r, -r, y, -r); F.air(r, y, -r, r, y, -r); F.air(-r, y, r, -r, y, r); F.air(r, y, r, r, y, r); }
    }
    F.leaves(0, h + 2, 0, 0, h + 3, 0, L);
    F.logs(0, 0, 0, 0, h + 1, 0, SPL, "y");
    return;
  }
  if (kind === "bigoak") {
    // بلوط كبير للحدائق: تاج عريض (نص قطر 3) بطبقات، وفروع قصيرة
    const L = M("oak_leaves"), LOG = M("oak_log");
    F.leaves(-3, h - 1, -2, 3, h + 1, 2, L); F.leaves(-2, h - 1, -3, 2, h + 1, 3, L);
    F.leaves(-2, h + 2, -2, 2, h + 2, 2, L); F.leaves(-1, h + 3, -1, 1, h + 3, 1, L);
    F.leaves(-1, h - 2, -1, 1, h - 2, 1, L);
    for (const [u, v] of [[-3, -2], [3, -2], [-3, 2], [3, 2], [-2, -3], [2, -3], [-2, 3], [2, 3]]) if (hash3(x + u, h, z + v, 77) < 0.5) F.air(u, h + 1, v, u, h + 1, v);
    F.logs(0, 0, 0, 0, h + 1, 0, LOG, "y");
    F.logs(1, h, 0, 2, h, 0, LOG, "x"); F.logs(-2, h - 1, 0, -1, h - 1, 0, LOG, "x"); F.logs(0, h, -2, 0, h, -1, LOG, "z");
    return;
  }
  const log = kind === "birch" ? M("birch_log") : M("oak_log");
  const L = kind === "birch" ? M("birch_leaves") : kind === "bloom" ? M("azalea_leaves_flowered") : M("oak_leaves");
  F.leaves(-2, h - 1, -2, 2, h, 2, L);
  F.air(-2, h, -2, -2, h, -2); F.air(2, h, -2, 2, h, -2); F.air(-2, h, 2, -2, h, 2); F.air(2, h, 2, 2, h, 2);
  // تاج طبيعي: شيل بعض زوايا الطبقة السفلى حسب تشويش ثابت (مو كل الأشجار نفس المكعب)
  for (const [u, v] of [[-2, -2], [2, -2], [-2, 2], [2, 2]]) if (hash3(x + u, h, z + v, 78) < 0.45) F.air(u, h - 1, v, u, h - 1, v);
  F.leaves(-1, h + 1, -1, 1, h + 1, 1, L);
  F.leaves(0, h + 2, 0, 0, h + 2, 0, L);
  if (kind !== "birch") { F.leaves(-1, h - 2, -1, 1, h - 2, 1, L); }
  F.logs(0, 0, 0, 0, h, 0, log, "y");
}
// حوض زهور مرتب (مثل الحدائق الرسمية): كل صف لون واحد على طول الحوض
const BED_SETS = [["red_tulip", "white_tulip", "pink_tulip"], ["cornflower", "oxeye_daisy", "allium"], ["poppy", "azure_bluet", "dandelion"], ["orange_tulip", "lily_of_the_valley", "red_tulip"]];
function flowerBed(P, x1, z1, x2, z2, salt = 0) {
  const S = BED_SETS[Math.abs(salt) % BED_SETS.length], alongX = x2 - x1 >= z2 - z1;
  for (let x = x1; x <= x2; x++) for (let z = z1; z <= z2; z++) P.set(x, 0, z, M(S[(alongX ? z - z1 : x - x1) % S.length]));
}
// حقل زهور (مزرعة زهور): شرائط عرض 2 كل شريط نوع، وبينها ممر ترابي
function flowerField(P, x1, z1, x2, z2, kinds) {
  for (let x = x1; x <= x2; x++) {
    if ((x - x1) % 3 === 2) { pave(P, x, z1, x, z2, "dirt", x); continue; }
    const k = kinds[Math.floor((x - x1) / 3) % kinds.length];
    for (let z = z1; z <= z2; z++) P.set(x, 0, z, M(k));
  }
}
// زهرة طويلة (بلوكتين): فاونيا، ورد، ليلك، دوار الشمس
function tallFlower(P, x, z, kind) { P.set(x, 0, z, M(kind), { upper_block_bit: false }); P.set(x, 1, z, M(kind), { upper_block_bit: true }); }
function hedge(P, x1, z1, x2, z2, h = 1) {
  P.box(x1, 0, z1, x2, h - 1, z2, M("oak_leaves"), { persistent_bit: true, update_bit: false });
}
// مقعد: درجة متجهة + جانبين ترابدور
function bench(P, x, z, face, len = 3) {
  const F = P.frame(x, z, 0), [du, dv] = DV[face], along = face === "n" || face === "s" ? [1, 0] : [0, 1];
  for (let i = 0; i < len; i++) F.stair(along[0] * i, 0, along[1] * i, SST, OPP[face]);
  F.set(-along[0], 0, -along[1], STRAP, { direction: 0, open_bit: false, upside_down_bit: true });
  F.set(along[0] * len, 0, along[1] * len, STRAP, { direction: 0, open_bit: false, upside_down_bit: true });
}

// ───────────────────────── السور والأبراج والبوابة ─────────────────────────
const WALL_H = 8;      // جسم السور y=0..7، الممشى فوقه (y=8)
function wallSide(P, axis, fixed, a1, a2, inward) {
  // axis "x": السور ممتد على x، z ثابت؛ inward = +1 (للجنوب) أو -1. ثخانة 4 من fixed باتجاه الداخل
  const W = (o) => fixed + inward * o;
  const box = (a, b, o1, o2, y1, y2, id, st) => (axis === "x" ? P.box(a, y1, W(o1), b, y2, W(o2), id, st) : P.box(W(o1), y1, a, W(o2), y2, b, id, st));
  const mix = (a, b, o1, o2, y1, y2, ids, w, s) => (axis === "x" ? P.mix(a, y1, W(o1), b, y2, W(o2), ids, w, s) : P.mix(W(o1), y1, a, W(o2), y2, b, ids, w, s));
  const set = (a, o, y, id, st) => (axis === "x" ? P.set(a, y, W(o), id, st) : P.set(W(o), y, a, id, st));
  mix(a1, a2, 0, 3, 0, WALL_H - 1, STONE, STONE_W, 61);                          // الجسم
  mix(a1, a2, 0, 0, 0, 1, COBBLE, COBBLE_W, 62);                                 // قاعدة حجر خشن (الوجه الخارجي)
  box(a1, a2, 0, 0, 5, 5, PAND);                                                  // حزام حجري بارز للعين (خط أفقي)
  box(a1, a2, 0, 3, WALL_H - 1, WALL_H - 1, M("smooth_stone"));                   // أرضية الممشى فوق
  // شرفات (merlons) بالحافة الخارجية: بلوكة وغطاء نص، وفتحة بينها
  for (let a = a1; a <= a2; a++) {
    if ((a - a1) % 2 === 0) { set(a, 0, WALL_H, SB); set(a, 0, WALL_H + 1, SBSL, { "minecraft:vertical_half": "bottom" }); }
    set(a, 3, WALL_H, SBSL, { "minecraft:vertical_half": "bottom" });            // درابزين واطي من جوه
  }
  // دعامات (buttresses) على الوجه الداخلي كل 8 بلوكات: عمق وظل، وراسها درجة
  for (let a = a1 + 4; a <= a2 - 4; a += 8) {
    mix(a, a, 4, 4, 0, WALL_H - 2, STONE, STONE_W, 63);
    const dir = axis === "x" ? (inward > 0 ? "n" : "s") : inward > 0 ? "w" : "e";
    set(a, 4, WALL_H - 1, SBS, { weirdo_direction: STAIR[dir], upside_down_bit: false });
    // فانوس فوق الدرابزين على بلوكة صلبة كل دعامتين
    if (((a - a1 - 4) / 8) % 2 === 0) { set(a, 3, WALL_H, SB); set(a, 3, WALL_H + 1, M("lantern"), { hanging: false }); P.lights++; }
  }
}
// برج مربع: (cx,cz) المركز، hw نص العرض، h الارتفاع، roof: "spire" | "flat"، doors: [{dir, y}] فتحات
function tower(P, cx, cz, hw, h, roof = "flat", doors = [], salt = 0) {
  const x1 = cx - hw, x2 = cx + hw, z1 = cz - hw, z2 = cz + hw;
  P.mix(x1, 0, z1, x2, h - 1, z2, STONE, STONE_W, 70 + salt);
  P.mix(x1, 0, z1, x2, 1, z2, COBBLE, COBBLE_W, 71 + salt);
  P.box(x1 + 1, 0, z1 + 1, x2 - 1, h - 1, z2 - 1, AIR);                          // جوه فاضي
  // زوايا حجر مصقول (quoins) وأحزمة
  for (const [x, z] of [[x1, z1], [x2, z1], [x1, z2], [x2, z2]]) for (let y = 2; y < h; y += 2) P.set(x, y, z, PAND);
  P.box(x1, 6, z1, x2, 6, z2, CSB); P.box(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, AIR);
  // طوابق خشب: على مستوى ممشى السور (y=7) وكل 5 بعدها، بفتحة للسلم
  for (let y = 7; y < h - 1; y += 5) { P.box(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, SPR); P.box(x1 + 1, y, z1 + 1, x1 + 1, y, z1 + 1, AIR); }
  P.box(x1 + 1, h - 1, z1 + 1, x2 - 1, h - 1, z2 - 1, SPR);
  P.box(x1 + 1, h - 1, z1 + 1, x1 + 1, h - 1, z1 + 1, AIR);
  const F = P.frame(0, 0, 0);
  F.ladder(x1 + 1, 0, h - 1, z1 + 1, "s");
  // شقوق سهام (1×2) بكل وجه: قضبان حديد (تبين فتحة بس ما يعبر منها أحد من برا)
  const mid = [cx, cz], BARS = M("iron_bars");
  for (let y = 3; y < h - 2; y += 5) {
    P.box(mid[0], y, z1, mid[0], y + 1, z1, BARS); P.box(mid[0], y, z2, mid[0], y + 1, z2, BARS);
    P.box(x1, y, mid[1], x1, y + 1, mid[1], BARS); P.box(x2, y, mid[1], x2, y + 1, mid[1], BARS);
  }
  // فتحات الأبواب (للمدينة أو لممشى السور): off = إزاحة على طول الوجه، w = العرض
  for (const d of doors) {
    const [dx, dz] = DV[d.dir], off = d.off || 0, wd = d.w || 1;
    const ex = dx > 0 ? x2 : dx < 0 ? x1 : cx + off, ez = dz > 0 ? z2 : dz < 0 ? z1 : cz + off;
    const ex2 = dx !== 0 ? ex : ex + wd - 1, ez2 = dz !== 0 ? ez : ez + wd - 1;
    P.box(ex, d.y, ez, ex2, d.y + (d.h || 2) - 1, ez2, AIR);
    if (d.door) F.door(ex, d.y, ez, SDOOR, d.dir);
  }
  // فوانيس جوه: تحت، وفوق كل طابق (حتى ما يبقى طابق مظلم تطلع بيه وحوش)
  P.set(cx, h - 2, cz, M("lantern"), { hanging: true }); P.set(cx, 3, cz, M("lantern"), { hanging: true }); P.lights += 2;
  for (let y = 7; y < h - 1; y += 5) { P.set(x2 - 1, y + 1, z2 - 1, M("lantern"), { hanging: false }); P.lights++; }
  // الراس: شرفات + سطح، أو سقف مدبب
  const top = h;
  P.mix(x1, top, z1, x2, top, z2, STONE, STONE_W, 72 + salt);
  P.box(x1 + 1, top, z1 + 1, x2 - 1, top, z2 - 1, AIR);
  for (let x = x1; x <= x2; x++) for (let z = z1; z <= z2; z++) {
    const edge = x === x1 || x === x2 || z === z1 || z === z2;
    if (!edge) continue;
    if ((x + z) % 2 === 0) P.set(x, top + 1, z, SB);
  }
  if (roof === "spire") {
    // سقف هرمي غامق (بلاط ديب سليت) يبدأ فوق الشرفات بأعمدة خشب
    // أعمدة السقف على زوايا الشرفات الخارجية (فوق فتحة السلم يبقى فاضي)
    for (const [x, z] of [[x1, z1], [x2, z1], [x1, z2], [x2, z2]]) P.box(x, top + 1, z, x, top + 2, z, SPL, { pillar_axis: "y" });
    let a = x1, b = z1, c = x2, d = z2, y = top + 3;
    while (a <= c && b <= d) {
      if (a === c || b === d) { P.box(a, y, b, c, y, d, DT); break; }
      P.box(a, y, b, c, y, d, DT); P.box(a + 1, y, b + 1, c - 1, y, d - 1, AIR);
      for (let x = a + 1; x < c; x++) { P.set(x, y, b, DTS, { weirdo_direction: STAIR.s, upside_down_bit: false }); P.set(x, y, d, DTS, { weirdo_direction: STAIR.n, upside_down_bit: false }); }
      for (let z = b + 1; z < d; z++) { P.set(a, y, z, DTS, { weirdo_direction: STAIR.e, upside_down_bit: false }); P.set(c, y, z, DTS, { weirdo_direction: STAIR.w, upside_down_bit: false }); }
      a++; b++; c--; d--; y++;
    }
    P.set(cx, y + 1, cz, M("lightning_rod"), { facing_direction: 1 });
  } else {
    // سارية علم: سياج وصوف أزرق (علم إثيريا) بشريط ذهبي
    P.box(cx, top, cz, cx, top + 4, cz, SFENCE);
    P.box(cx + 1, top + 2, cz, cx + 2, top + 4, cz, M("blue_wool")); P.set(cx + 1, top + 3, cz, M("yellow_wool"));
  }
}
function gatehouse(P) {
  // البوابة الرئيسية بالجنوب: فتحة 5 عرض و6 ارتفاع بقوس، برجين 9×9 بسقوف مدببة، وأعلام زرقة مثل الصورة
  const cx = 124, z2 = 247, z1 = 236;
  P.mix(115, 0, z1, 133, 11, z2, STONE, STONE_W, 80);
  P.mix(115, 0, z1, 133, 1, z2, COBBLE, COBBLE_W, 81);
  P.box(122, 0, z1, 126, 6, z2, AIR);                                               // الممر
  P.box(121, 0, z1 + 2, 121, 5, z2 - 2, PAND); P.box(127, 0, z1 + 2, 127, 5, z2 - 2, PAND);
  // قوس: درجات مقلوبة بزوايا الفتحة (الوجهين)
  for (const z of [z1, z2]) {
    P.set(122, 6, z, SBS, { weirdo_direction: STAIR.w, upside_down_bit: true }); P.set(126, 6, z, SBS, { weirdo_direction: STAIR.e, upside_down_bit: true });
    P.box(122, 7, z, 126, 7, z, CSB);
  }
  // شبكة البوابة المرفوعة (حديد) فوق الممر
  P.box(122, 6, z1 + 5, 126, 6, z1 + 5, M("iron_bars"));
  // غرفة الحراسة فوق الممر + فتحات
  P.box(116, 8, z1 + 1, 132, 10, z2 - 1, AIR); P.box(116, 7, z1 + 1, 132, 7, z2 - 1, SPR);
  for (const x of [118, 124, 130]) { P.box(x, 9, z2, x, 10, z2, AIR); P.box(x, 9, z1, x, 10, z1, AIR); }
  // شرفات فوق
  for (let x = 115; x <= 133; x++) for (const z of [z1, z2]) if ((x - 115) % 2 === 0) { P.set(x, 12, z, SB); P.set(x, 13, z, SBSL, { "minecraft:vertical_half": "bottom" }); }
  P.box(115, 11, z1, 133, 11, z2, M("smooth_stone"));
  P.box(116, 11, z1 + 1, 132, 11, z2 - 1, SPR);
  // البرجين
  tower(P, 111, 242, 4, 15, "spire", [{ dir: "n", y: 0, door: true }, { dir: "e", y: 8 }, { dir: "w", y: 8, off: 3, w: 2 }], 5);
  tower(P, 137, 242, 4, 15, "spire", [{ dir: "n", y: 0, door: true }, { dir: "w", y: 8 }, { dir: "e", y: 8, off: 3, w: 2 }], 6);
  // أعلام زرقة طويلة (صوف) على وجه البرجين الداخلي والخارجي
  for (const x of [111, 137]) for (const z of [236, 246]) {
    const zz = z === 236 ? 235 : 247;
    if (zz === 247) continue;                                                      // ما نطلع برا حدود المدينة
    P.box(x, 6, zz, x, 11, zz, M("blue_wool")); P.set(x, 9, zz, M("yellow_wool")); P.set(x, 5, zz, M("blue_carpet"));
  }
  // فوانيس على جانبي الممر من جوه
  P.set(121, 3, z1 - 1, M("lantern"), { hanging: false }); P.set(127, 3, z1 - 1, M("lantern"), { hanging: false });
  P.set(121, 2, z1 - 1, SB); P.set(127, 2, z1 - 1, SB);
  P.box(121, 0, z1 - 1, 121, 1, z1 - 1, SB); P.box(127, 0, z1 - 1, 127, 1, z1 - 1, SB);
  P.lights += 2;
  // حراس البوابة
  P.post("guard", 120, 0, 233, 4); P.post("guard", 128, 0, 233, 4);
  P.post("guard", 112, 15, 241, 2); P.post("guard", 136, 15, 241, 2);
  P.marks.gate = { x: 124, z: 245 };
}
function walls(P) {
  // أربعة جوانب، ثخانة 4. الزوايا تغطيها أبراج كبيرة 9×9
  wallSide(P, "x", 0, 0, 247, 1);          // شمال
  wallSide(P, "x", 247, 0, 114, -1);       // جنوب (قسمين حول البوابة)
  wallSide(P, "x", 247, 134, 247, -1);
  wallSide(P, "z", 0, 0, 247, 1);          // غرب
  wallSide(P, "z", 247, 0, 247, -1);       // شرق
  // أبراج الزوايا (سقوف مدببة) وأبراج الجدران (سطوح بأعلام)
  // أبراج الزوايا 9×9 (سقوف مدببة): باب أرضي للمدينة، وفتحتين على ممشى السورين (حارة الممشى = 1..2 أو 245..246)
  const corner = [[4, 4, "s", "e"], [243, 4, "s", "w"], [4, 243, "n", "e"], [243, 243, "n", "w"]];
  corner.forEach(([x, z, inZ, inX], i) => {
    const laneZ = z < 124 ? 1 : 245, laneX = x < 124 ? 1 : 245;
    tower(P, x, z, 4, 16, "spire", [{ dir: inZ, y: 0, door: true }, { dir: inX, y: 8, off: laneZ - z, w: 2 }, { dir: inZ, y: 8, off: laneX - x, w: 2 }], 10 + i);
    P.post("guard", x + (x < 124 ? 1 : -1), 16, z + (z < 124 ? 1 : -1), 2);
  });
  // أبراج الجدران 7×7: الممشى يمر من جوه البرج (فتحتين بالجهتين)، وباب للمدينة
  const mids = [[82, 3, "x", "s"], [165, 3, "x", "s"], [82, 244, "x", "n"], [165, 244, "x", "n"], [3, 82, "z", "e"], [3, 165, "z", "e"], [244, 82, "z", "w"], [244, 165, "z", "w"]];
  mids.forEach(([x, z, ax, inn], i) => {
    const lane = (ax === "x" ? z : x) < 124 ? 1 : 245, c = ax === "x" ? z : x, off = lane - c;
    const side = ax === "x" ? [{ dir: "e", y: 8, off, w: 2 }, { dir: "w", y: 8, off, w: 2 }] : [{ dir: "n", y: 8, off, w: 2 }, { dir: "s", y: 8, off, w: 2 }];
    tower(P, x, z, 3, 13, "flat", [{ dir: inn, y: 0, door: true }, ...side], 20 + i);
    if (i % 2 === 0) P.post("guard", x + (inn === "e" ? 1 : inn === "w" ? -1 : 0), 13, z + (inn === "s" ? 1 : inn === "n" ? -1 : 0), 2);
  });
  gatehouse(P);
}

// ───────────────────────── البيوت (3 أحجام مثل الصورة) ─────────────────────────
// سقوف متنوعة (مثل المدن المبنية باليد): بلوط غامق، سبروس، بلاط ديب سليت، طابوق أحمر
const ROOFS = {
  dark: [DOS, DOK, DSL],
  spruce: [SST, SPR, SSL],
  slate: [DTS, DT, DTSL],
  brick: [M("brick_stairs"), M("brick_block"), M("brick_slab")],
};
const CALC = M("calcite");                                                         // جص أبيض للطابق الفوقاني (نصف خشب)
const pickW = (h, ws) => { let t = 0; const tot = ws.reduce((a, b) => a + b, 0); for (let i = 0; i < ws.length; i++) { t += ws[i] / tot; if (h < t) return i; } return ws.length - 1; };
// طراز بيت ثابت حسب رقمه: سقف، جدار تحت، جدار فوق، سجاد
function houseStyle(i, floors, salt = 0) {
  const h = (k) => hash3(i, k, salt, 808);
  return {
    floors,
    roofKind: ["dark", "spruce", "slate", "brick"][pickW(h(1), [32, 30, 20, 18])],
    lower: floors > 1 ? (h(2) < 0.55 ? "stone" : "cobble") : ["cobble", "stone", "plank", "plaster"][pickW(h(2), [34, 22, 22, 22])],
    upper: h(3) < 0.55 ? "plaster" : SPR,
    carpet: ["brown_carpet", "red_carpet", "green_carpet", "light_gray_carpet", "blue_carpet", "cyan_carpet"][Math.floor(h(4) * 6)],
    carpet2: ["red_carpet", "brown_carpet", "lime_carpet", "light_blue_carpet"][Math.floor(h(5) * 4)],
  };
}
// إطار البيت المحلي: الباب على الجهة "s" (v = d-1)، العرض w على u، العمق d على v. floors 1..2
function house(P, x, z, rot, w, d, opts = {}) {
  const F = P.frame(x, z, rot), floors = opts.floors || 1, wallH = 4;
  const [roofS, roofB, roofL] = ROOFS[opts.roofKind || "dark"];
  const lower = opts.lower || "cobble", plaster = opts.upper === "plaster", upper = plaster ? CALC : opts.upper || SPR;
  const top = floors * (wallH + 1);                                                  // ارتفاع الجدران الكلي
  const du = Math.floor(w / 2), dv = Math.floor(d / 2);
  // أساس حجر (درجة تحت الأرضية)
  F.mix(-1, -1, -1, w, -1, d, COBBLE, COBBLE_W, 90 + x + z);
  F.box(0, -1, 0, w - 1, -1, d - 1, SPR);
  // الطابق الأول: حجر خشن، طوب، خشب على قاعدة حجر، أو جص على قاعدة حجر
  if (lower === "cobble") F.mix(0, 0, 0, w - 1, wallH, d - 1, COBBLE, COBBLE_W, 91 + x);
  else if (lower === "stone") F.mix(0, 0, 0, w - 1, wallH, d - 1, STONE, STONE_W, 92 + x);
  else { F.box(0, 0, 0, w - 1, wallH, d - 1, lower === "plaster" ? CALC : SPR); F.mix(0, 0, 0, w - 1, 0, d - 1, COBBLE, COBBLE_W, 93 + x); }
  if (floors > 1) F.box(0, wallH + 1, 0, w - 1, top - 1, d - 1, upper);
  F.air(1, 0, 1, w - 2, top - 1, d - 2);
  // جذوع الزوايا وعارضة كل طابق (ظل وعمق)
  for (const [u, v] of [[0, 0], [w - 1, 0], [0, d - 1], [w - 1, d - 1]]) F.logs(u, 0, v, u, top - 1, v, SPL, "y");
  for (let y = wallH; y < top; y += wallH + 1) { F.logs(0, y, 0, w - 1, y, 0, SPL, "x"); F.logs(0, y, d - 1, w - 1, y, d - 1, SPL, "x"); F.logs(0, y, 0, 0, y, d - 1, SPL, "z"); F.logs(w - 1, y, 0, w - 1, y, d - 1, SPL, "z"); }
  if (floors > 1) { F.logs(0, top - 1, 0, w - 1, top - 1, 0, SPL, "x"); F.logs(0, top - 1, d - 1, w - 1, top - 1, d - 1, SPL, "x"); F.logs(0, top - 1, 0, 0, top - 1, d - 1, SPL, "z"); F.logs(w - 1, top - 1, 0, w - 1, top - 1, d - 1, SPL, "z"); }
  // نصف خشب: أعمدة جذوع متناظرة حول الوسط (كل 4) على الجدران الخشب/الجص
  const timber = [];
  if (floors > 1) timber.push([wallH + 1, top - 2]);
  if (lower === "plank" || lower === "plaster") timber.push([1, wallH - 1]);
  for (const [ya, yb] of timber) {
    for (let u = 1; u <= w - 2; u++) if (Math.abs(u - du) % 4 === 0) { if (!(ya === 1 && u === du)) F.logs(u, ya, d - 1, u, yb, d - 1, SPL, "y"); F.logs(u, ya, 0, u, yb, 0, SPL, "y"); }
    for (let v = 1; v <= d - 2; v++) if (Math.abs(v - dv) % 4 === 0) { F.logs(0, ya, v, 0, yb, v, SPL, "y"); F.logs(w - 1, ya, v, w - 1, yb, v, SPL, "y"); }
  }
  // أرضية الطابق الثاني
  if (floors > 1) F.box(1, wallH, 1, w - 2, wallH, d - 2, SPR);
  // نوافذ (زجاج 1×2) متناظرة: بعد 2 من الوسط ثم كل 4، وشجيرة أزاليا تحت شبابيك الواجهة
  for (let fl = 0; fl < floors; fl++) {
    const y = fl * (wallH + 1) + 1;
    for (let u = 1; u <= w - 2; u++) {
      if (Math.abs(u - du) % 4 !== 2) continue;
      F.box(u, y, 0, u, y + 1, 0, GPANE); F.box(u, y, d - 1, u, y + 1, d - 1, GPANE);
      if (fl === 0) F.leaves(u, 0, d, u, 0, d, M("azalea_leaves"));
    }
    for (let v = 1; v <= d - 2; v++) if (Math.abs(v - dv) % 4 === 2) { F.box(0, y, v, 0, y + 1, v, GPANE); F.box(w - 1, y, v, w - 1, y + 1, v, GPANE); }
  }
  // الباب (الجهة s) مع عتبة ودرجة وفانوس
  F.air(du, 0, d - 1, du, 1, d - 1);
  F.door(du, 0, d - 1, SDOOR, "s");
  F.stair(du, -1, d, M("stone_stairs"), "n");
  F.lantern(du + 1, 2, d, false); F.set(du + 1, 1, d, SFENCE); F.set(du + 1, 0, d, SFENCE);
  // سقف جملوني (gable) على محور u، بروز بلوكة، وطرفيه مثلث من مادة الطابق الفوقاني بشباك صغير
  const ry = top, half = Math.ceil((d + 2) / 2);
  for (let k = 0; k < half; k++) {
    const y = ry + k, v1 = -1 + k, v2 = d - k;
    if (v1 > v2) break;
    if (v1 === v2) { F.slabs(-1, y, v1, w, v1, roofL); break; }
    for (let u = -1; u <= w; u++) { F.stair(u, y, v1, roofS, "s"); F.stair(u, y, v2, roofS, "n"); }
    if (v2 - v1 >= 2) { F.box(0, y, v1 + 1, w - 1, y, v2 - 1, roofB); F.air(1, y, v1 + 1, w - 2, y, v2 - 1); F.box(0, y, v1 + 1, 0, y, v2 - 1, upper); F.box(w - 1, y, v1 + 1, w - 1, y, v2 - 1, upper); }
  }
  if (half >= 4) F.box(0, ry + 1, dv, 0, ry + 2, dv, GPANE);
  // مدخنة حجر خارج الجدار الجانبي (بروز) مع نار مخيم (دخان) فوق القمة
  if (opts.chimney !== false) {
    F.mix(w, 0, dv, w, ry + half, dv, COBBLE, COBBLE_W, 95 + x);
    F.card(w, ry + half + 1, dv, M("campfire"), "s", { extinguished: false });
  }
  furnishHouse(F, w, d, floors, wallH, opts);
}
// أثاث: تحت (معيشة أو دكان)، وفوق (نوم). السجاد ينحط قبل الأثاث حتى ما يغطيه
function furnishHouse(F, w, d, floors, wallH, opts) {
  if (opts.kind === "stable") return furnishStable(F, w, d, wallH, opts);
  const big = w >= 11, du = Math.floor(w / 2), up = wallH + 1;
  if (opts.shop) furnishShop(F, w, d, opts.shop);
  else {
    F.box(1, 0, 1, w - 2, 0, d - 2, M(opts.carpet || "brown_carpet"));
    F.air(du, 0, d - 2, du, 0, d - 2);                                              // مدخل نظيف
    F.card(w - 2, 0, d - 3, M("furnace"), "w"); F.set(w - 2, 0, d - 4, M("crafting_table"));
    if (d - 5 >= 5 || floors === 1) F.barrel(w - 2, 0, Math.max(2, d - 5));
    const tu = du, tv = Math.floor(d / 2) - (floors > 1 ? 1 : 0);
    F.set(tu, 0, tv, SFENCE); F.set(tu, 1, tv, M("spruce_pressure_plate"));
    F.stair(tu - 1, 0, tv, SST, "w"); F.stair(tu + 1, 0, tv, SST, "e");
    F.set(1, 0, d - 2, M("bookshelf")); F.set(1, 1, d - 2, M("bookshelf")); F.pot(1, 2, d - 2);
    F.lantern(tu, wallH - 1, tv, true);
  }
  if (floors > 1) {
    F.box(1, up, 1, w - 2, up, d - 2, M(opts.carpet2 || "red_carpet"));
    // درج للطابق الثاني على الجدار الشرقي (يبدأ من v=1 ويطلع للجنوب)، وفتحة بالأرضية فوقه
    // 5 درجات (y 0..4): الأخيرة بمستوى أرضية الطابق الثاني فالطلعة سلسة بدون قفزة
    for (let i = 0; i <= wallH; i++) { F.stair(w - 2, i, 1 + i, SST, "s"); F.air(w - 2, i + 1, 1 + i, w - 2, i + 2, 1 + i); }
    F.air(w - 2, wallH, 1, w - 2, wallH, wallH);                                    // فتحة بالأرضية فوق الدرج
    F.air(w - 2, up, 1, w - 2, up, wallH + 1);
    F.box(w - 3, up, 1, w - 3, up, wallH, SFENCE);                                   // درابزين على جنب الفتحة
    F.set(w - 3, up, d - 2, M("bookshelf")); F.card(w - 4, up, d - 2, M("lectern"), "n", { powered_bit: false });
    F.lantern(du, wallH * 2 - 1, Math.floor(d / 2), true);
  }
  const bedY = floors > 1 ? up : 0;
  F.bed(1, bedY, 2, "n", opts.bed || "red");
  if (big) F.bed(3, bedY, 2, "n", "blue");
  F.chest(big ? 5 : 3, bedY, 1, "s", opts.loot || "city_house");
  if (floors > 1) { F.barrel(big ? 6 : 4, up, 1); F.pot(1, up, d - 2); }
}
// إسطبل/حظيرة: مرابط بقواطع سياج وبوابات، قش ومعالف ماء، ممر عريض قدام، وواجهة مفتوحة بين الأعمدة
function furnishStable(F, w, d, wallH, opts) {
  const du = Math.floor(w / 2);
  F.mix(1, -1, 1, w - 2, -1, d - 2, [M("coarse_dirt"), M("spruce_planks"), M("dirt")], [50, 35, 15], 97);
  const sv = Math.min(4, d - 5);                                                     // عمق المرابط
  for (let u = 1; u + 3 <= w - 2; u += 4) {
    if (u > 1) F.box(u - 1, 0, 1, u - 1, 0, sv, SFENCE);
    F.set(u, 0, 1, M("hay_block"), { deprecated: 0, pillar_axis: "y" });
    F.set(u + 2, 0, 1, M("cauldron"), { cauldron_liquid: "water", fill_level: 6 });
    F.box(u, 0, sv + 1, u + 2, 0, sv + 1, SFENCE);
    F.card(u + 1, 0, sv + 1, M("spruce_fence_gate"), "s", { in_wall_bit: false, open_bit: false });
    F.lantern(u + 1, wallH - 1, sv + 2, true);
  }
  F.set(w - 2, 0, d - 2, M("composter"), { composter_fill_level: 5 });
  F.chest(w - 2, 0, d - 3, "w", opts.loot || "city_barn");
  F.set(1, 0, d - 2, M("hay_block"), { deprecated: 0, pillar_axis: "y" }); F.set(1, 1, d - 2, M("hay_block"), { deprecated: 0, pillar_axis: "y" }); F.set(2, 0, d - 2, M("hay_block"), { deprecated: 0, pillar_axis: "y" });
  // واجهة مفتوحة: نشيل الجدار بين الأعمدة (كل 4) بالطابق الأرضي، والباب يبقى بالنص
  for (let u = 1; u <= w - 2; u++) if (u % 4 !== 0 && Math.abs(u - du) > 1) F.air(u, 0, d - 1, u, 2, d - 1);
  for (let u = 4; u <= w - 2; u += 4) F.logs(u, 0, d - 1, u, wallH - 1, d - 1, SPL, "y");
}
// دكان بالطابق الأول: منضدة عرضية، بضاعة على الجدار الخلفي، ممر للدرج (u = w-3)
const SHOPS = {
  bakery: { color: "orange", goods: ["smoker", "smoker", "hay_block", "barrel"], counter: "cake" },
  tailor: { color: "purple", goods: ["loom", "white_wool", "red_wool", "light_blue_wool"], counter: "white_carpet" },
  scribe: { color: "blue", goods: ["bookshelf", "cartography_table", "bookshelf", "bookshelf"], counter: "lectern" },
  fletcher: { color: "lime", goods: ["fletching_table", "target", "hay_block", "barrel"], counter: "flower_pot" },
  apothecary: { color: "magenta", goods: ["brewing_stand", "cauldron", "bookshelf", "barrel"], counter: "flower_pot" },
  butcher: { color: "red", goods: ["smoker", "barrel", "barrel", "hay_block"], counter: "lantern" },
  toolsmith: { color: "gray", goods: ["smithing_table", "grindstone", "anvil", "barrel"], counter: "lantern" },
  grocer: { color: "yellow", goods: ["pumpkin", "melon_block", "hay_block", "composter"], counter: "flower_pot" },
};
function good(F, u, y, v, g) {
  if (g === "smoker" || g === "pumpkin" || g === "anvil") F.card(u, y, v, M(g), "s");
  else if (g === "hay_block") F.set(u, y, v, M(g), { deprecated: 0, pillar_axis: "y" });
  else if (g === "barrel") F.barrel(u, y, v);
  else if (g === "loom") F.set(u, y, v, M(g), { direction: 0 });
  else if (g === "grindstone") F.set(u, y, v, M(g), { attachment: "standing", direction: 0 });
  else if (g === "brewing_stand") F.set(u, y, v, M(g), { brewing_stand_slot_a_bit: false, brewing_stand_slot_b_bit: false, brewing_stand_slot_c_bit: false });
  else if (g === "cauldron") F.set(u, y, v, M(g), { cauldron_liquid: "water", fill_level: 6 });
  else if (g === "composter") F.set(u, y, v, M(g), { composter_fill_level: 4 });
  else if (g === "cake") F.set(u, y, v, M(g), { bite_counter: 0 });
  else if (g === "lectern") F.card(u, y, v, M(g), "s", { powered_bit: false });
  else if (g === "flower_pot") F.pot(u, y, v);
  else if (g === "lantern") F.lantern(u, y, v, false);
  else F.set(u, y, v, M(g));
}
function furnishShop(F, w, d, kind) {
  const S = SHOPS[kind] || SHOPS.grocer, cv = Math.floor(d / 2);
  for (let u = 1; u <= w - 4; u++) F.slab(u, 0, cv, SSL, true);                     // المنضدة (نص بلوكة فوق)
  F.barrel(1, 0, cv);
  good(F, 2, 1, cv, S.counter);
  S.goods.forEach((g, i) => { if (1 + i <= w - 4) good(F, 1 + i, 0, 1, g); });
  F.chest(w - 4, 0, 2, "w", "city_market");
  F.set(1, 0, d - 2, M("barrel"), { facing_direction: 1, open_bit: false }); F.pot(1, 1, d - 2);
  F.lantern(Math.floor(w / 2) - 1, 3, cv + 1, true);
}
// دكان السوق: بيت طابقين 9×9 + مظلة صوف مقلمة قدام الباب على أعمدة سياج
function shop(P, ox, oz, rot, kind, i) {
  const w = 9, d = 9, st = houseStyle(i, 2, 7);
  house(P, ox, oz, rot, w, d, { ...st, shop: kind, lower: i % 2 ? "stone" : "cobble" });
  const F = P.frame(ox, oz, rot), col = (SHOPS[kind] || SHOPS.grocer).color;
  for (let u = 1; u <= w - 2; u++) for (let v = d; v <= d + 1; v++) F.set(u, 3, v, M((u % 2 ? col : "white") + "_wool"));
  F.box(1, 0, d + 1, 1, 2, d + 1, SFENCE); F.box(w - 2, 0, d + 1, w - 2, 2, d + 1, SFENCE);
  good(F, 2, 0, d + 1, (SHOPS[kind] || SHOPS.grocer).goods[0] === "smoker" ? "barrel" : (SHOPS[kind] || SHOPS.grocer).goods[2]);
}

// ───────────────────────── القلعة (الملك) ─────────────────────────
function castle(P) {
  const F = P.frame(0, 0, 0);
  const x1 = 104, x2 = 143, z1 = 12, z2 = 41, H = 14;                               // القاعة الكبيرة 40×30
  F.mix(x1, 0, z1, x2, H - 1, z2, STONE, STONE_W, 120);
  F.mix(x1, 0, z1, x2, 1, z2, COBBLE, COBBLE_W, 121);
  F.box(x1 + 1, 0, z1 + 1, x2 - 1, H - 2, z2 - 1, AIR);
  F.box(x1 + 1, -1, z1 + 1, x2 - 1, -1, z2 - 1, M("polished_andesite"));
  // أعمدة جانبية (عمق) كل 5 وعارضات
  for (let x = x1 + 3; x < x2; x += 5) for (const z of [z1, z2]) F.mix(x, 0, z + (z === z1 ? -1 : 1), x, H - 2, z + (z === z1 ? -1 : 1), STONE, STONE_W, 122);
  F.box(x1, 9, z1, x2, 9, z2, CSB); F.box(x1 + 1, 9, z1 + 1, x2 - 1, 9, z2 - 1, AIR);
  // أرضية الطابق الثاني (فوق قاعة العرش من الخلف بس: بلكونة)، والقاعة عالية 9
  F.box(x1 + 1, 9, z1 + 1, x2 - 1, 9, z1 + 10, DOK);
  // نوافذ طويلة زجاج ملون (أزرق وأصفر) بأقواس
  for (let x = x1 + 5; x < x2 - 2; x += 5) for (const z of [z1, z2]) {
    F.box(x, 2, z, x + 1, 6, z, M("blue_stained_glass_pane")); F.box(x, 7, z, x + 1, 7, z, M("yellow_stained_glass_pane"));
  }
  for (let z = z1 + 5; z < z2 - 2; z += 5) for (const x of [x1, x2]) { F.box(x, 2, z, x, 6, z + 1, M("blue_stained_glass_pane")); F.box(x, 7, z, x, 7, z + 1, M("yellow_stained_glass_pane")); }
  // المدخل الكبير جنوب (5 عرض × 7) بقوس ودرجات
  const ex = 124;
  F.air(ex - 2, 0, z2, ex + 2, 6, z2);
  F.set(ex - 2, 6, z2, SBS, { weirdo_direction: STAIR.w, upside_down_bit: true }); F.set(ex + 2, 6, z2, SBS, { weirdo_direction: STAIR.e, upside_down_bit: true });
  F.box(ex - 3, 7, z2 + 1, ex + 3, 8, z2 + 1, CSB);                                   // جبهة بارزة فوق الباب
  F.mix(ex - 4, 0, z2 + 1, ex - 3, 8, z2 + 1, STONE, STONE_W, 123); F.mix(ex + 3, 0, z2 + 1, ex + 4, 8, z2 + 1, STONE, STONE_W, 124);
  for (let i = 0; i < 3; i++) F.box(ex - 3, -1 + 0, z2 + 2 + i, ex + 3, -1, z2 + 2 + i, SB);
  F.box(ex - 2, -1, z2 + 1, ex + 2, -1, z2 + 1, PAND);
  // أعلام الملك الزرقة على الواجهة
  for (const x of [ex - 6, ex + 6]) { F.box(x, 4, z2 + 1, x, 11, z2 + 1, M("blue_wool")); F.box(x, 8, z2 + 1, x, 8, z2 + 1, M("yellow_wool")); }
  // قاعة العرش: سجادة حمرة من الباب للعرش، أعمدة، ثريات، منصة وعرش ذهبي
  F.box(ex - 1, 0, z1 + 6, ex + 1, 0, z2 - 1, M("red_carpet"));
  for (let z = z1 + 7; z <= z2 - 3; z += 5) for (const x of [ex - 7, ex + 7]) {
    F.box(x, 0, z, x, 8, z, M("quartz_pillar"), { pillar_axis: "y" }); F.set(x, 0, z, CSB); F.set(x, 8, z, CSB);
    F.set(x, 7, z + 1, M("lantern"), { hanging: false }); F.set(x, 6, z + 1, SB);
  }
  for (let z = z1 + 10; z <= z2 - 4; z += 8) { F.box(ex, 8, z, ex, 8, z, SFENCE); F.box(ex - 1, 7, z, ex + 1, 7, z, SFENCE); F.lantern(ex - 1, 6, z, true); F.lantern(ex + 1, 6, z, true); F.lantern(ex, 7, z - 1, false); F.set(ex, 6, z - 1, AIR); }
  // المنصة (دكة بدرجتين) والعرش
  F.box(ex - 5, 0, z1 + 1, ex + 5, 0, z1 + 4, M("smooth_quartz")); F.box(ex - 4, 1, z1 + 1, ex + 4, 1, z1 + 3, M("smooth_quartz"));
  for (let x = ex - 5; x <= ex + 5; x++) F.set(x, 0, z1 + 5, M("quartz_stairs"), { weirdo_direction: STAIR.n, upside_down_bit: false });
  for (let x = ex - 4; x <= ex + 4; x++) F.set(x, 1, z1 + 4, M("quartz_stairs"), { weirdo_direction: STAIR.n, upside_down_bit: false });
  F.set(ex, 2, z1 + 2, M("quartz_stairs"), { weirdo_direction: STAIR.n, upside_down_bit: false });     // مقعد العرش
  F.box(ex, 2, z1 + 1, ex, 4, z1 + 1, M("gold_block")); F.set(ex, 5, z1 + 1, M("gold_block"));
  F.set(ex - 1, 2, z1 + 2, M("gold_block")); F.set(ex + 1, 2, z1 + 2, M("gold_block"));
  F.set(ex - 1, 3, z1 + 2, M("red_carpet")); F.set(ex + 1, 3, z1 + 2, M("red_carpet"));
  F.box(ex - 3, 2, z1 + 1, ex - 3, 6, z1 + 1, M("blue_wool")); F.box(ex + 3, 2, z1 + 1, ex + 3, 6, z1 + 1, M("blue_wool"));
  F.set(ex - 3, 4, z1 + 1, M("yellow_wool")); F.set(ex + 3, 4, z1 + 1, M("yellow_wool"));
  F.lantern(ex - 2, 2, z1 + 1, false); F.lantern(ex + 2, 2, z1 + 1, false);
  P.post("king", ex, 2, z1 + 3, 2);
  P.post("guard", ex - 4, 0, z1 + 7, 3); P.post("guard", ex + 4, 0, z1 + 7, 3);
  // جوانب القاعة: موائد ولائم طويلة، رفوف، مشاعل (نار مخيم بقدر)
  for (const sx of [x1 + 3, x2 - 3]) {
    for (let z = z1 + 10; z <= z2 - 6; z++) { F.set(sx, 0, z, SFENCE); F.set(sx, 1, z, M("spruce_pressure_plate")); }
    for (let z = z1 + 10; z <= z2 - 6; z += 2) { F.stair(sx - 1, 0, z, SST, "w"); F.stair(sx + 1, 0, z, SST, "e"); }
    F.box(sx + (sx < ex ? -2 : 2), 0, z1 + 8, sx + (sx < ex ? -2 : 2), 2, z1 + 8, M("bookshelf"));
  }
  // درج حجري للبلكونة (الطابق الثاني) بالزاوية الشمالية الشرقية، وغرفة نوم الملك فوق
  for (let i = 0; i < 10; i++) F.set(x2 - 2, i, z1 + 20 - i, SBS, { weirdo_direction: STAIR.n, upside_down_bit: false });
  F.box(x1 + 1, 10, z1 + 1, x2 - 1, 10, z1 + 9, M("red_carpet"));
  F.box(x1 + 1, 10, z1 + 10, x2 - 1, 10, z1 + 10, M("dark_oak_fence"));
  F.air(x2 - 2, 10, z1 + 10, x2 - 2, 10, z1 + 10);
  // (البرج الشمالي الغربي ياكل زاوية القاعة لحد x1+3، فغرفة النوم تبدأ بعده)
  F.bed(x1 + 6, 10, z1 + 2, "n", "red"); F.bed(x1 + 7, 10, z1 + 2, "n", "red");
  F.chest(x1 + 9, 10, z1 + 1, "s", "city_king"); F.barrel(x1 + 10, 10, z1 + 1); F.barrel(x1 + 11, 10, z1 + 1);
  F.card(x1 + 13, 10, z1 + 2, M("lectern"), "s", { powered_bit: false });
  F.box(x1 + 15, 10, z1 + 1, x1 + 18, 12, z1 + 1, M("bookshelf"));
  F.set(x2 - 5, 10, z1 + 4, M("enchanting_table"));
  F.lantern(x1 + 6, 12, z1 + 5, true); F.lantern(x2 - 8, 12, z1 + 5, true);
  // السقف: جملوني كبير بلاط غامق فوق القاعة (محور x)، مع شرفات حول الحافة
  const ry = H, half = Math.ceil((z2 - z1 + 3) / 2);
  for (let k = 0; k < half; k++) {
    const y = ry + k, a = z1 - 1 + k, b = z2 + 1 - k;
    if (a > b) break;
    if (a === b) { F.box(x1 - 1, y, a, x2 + 1, y, a, DTSL, { "minecraft:vertical_half": "bottom" }); break; }
    for (let x = x1 - 1; x <= x2 + 1; x++) { F.set(x, y, a, DTS, { weirdo_direction: STAIR.s, upside_down_bit: false }); F.set(x, y, b, DTS, { weirdo_direction: STAIR.n, upside_down_bit: false }); }
    if (b - a >= 2) { F.mix(x1, y, a + 1, x1, y, b - 1, STONE, STONE_W, 125); F.mix(x2, y, a + 1, x2, y, b - 1, STONE, STONE_W, 126); }
  }
  // فوانيس بالعلية فوق السقف الداخلي (مكان مغلق ومظلم: حتى ما تطلع بيه وحوش)
  for (let x = x1 + 4; x < x2; x += 9) P.set(x, H, 26, M("lantern"), { hanging: false });
  // برج وسطي فوق القاعة (معلم يبين من كل المدينة): جسم حجر بشبابيك زرقة، شرفات، ومستدق بلاط
  {
    const tc = ex, tz = 26, hw = 4, y0 = H, y1 = 36;                                // الجسم y 14..36 (السقف يغطي لحد ~29)
    P.mix(tc - hw, y0, tz - hw, tc + hw, y1, tz + hw, STONE, STONE_W, 128);
    P.box(tc - hw + 1, y0, tz - hw + 1, tc + hw - 1, y1 - 1, tz + hw - 1, AIR);
    for (const [x, z] of [[tc - hw, tz - hw], [tc + hw, tz - hw], [tc - hw, tz + hw], [tc + hw, tz + hw]]) for (let y = y0 + 1; y <= y1; y += 2) P.set(x, y, z, PAND);
    P.box(tc - hw, 29, tz - hw, tc + hw, 29, tz + hw, CSB); P.box(tc - hw + 1, 29, tz - hw + 1, tc + hw - 1, 29, tz + hw - 1, AIR);   // حزام فوق خط السقف
    for (const d of [-hw, hw]) {
      P.box(tc - 1, 30, tz + d, tc + 1, 33, tz + d, M("blue_stained_glass_pane")); P.box(tc - 1, 34, tz + d, tc + 1, 34, tz + d, M("yellow_stained_glass_pane"));
      P.box(tc + d, 30, tz - 1, tc + d, 33, tz + 1, M("blue_stained_glass_pane")); P.box(tc + d, 34, tz - 1, tc + d, 34, tz + 1, M("yellow_stained_glass_pane"));
    }
    P.set(tc, y1 - 1, tz, M("lantern"), { hanging: true }); P.set(tc, y0 + 6, tz, M("lantern"), { hanging: false }); P.box(tc, y0, tz, tc, y0 + 5, tz, SB); P.lights += 2;
    for (let x = tc - hw; x <= tc + hw; x++) for (let z = tz - hw; z <= tz + hw; z++) if ((x === tc - hw || x === tc + hw || z === tz - hw || z === tz + hw) && (x + z) % 2 === 0) P.set(x, y1 + 1, z, SB);
    let a = tc - hw, b = tz - hw, c = tc + hw, d = tz + hw, y = y1 + 2;
    while (a <= c && b <= d) {
      if (a === c || b === d) { P.box(a, y, b, c, y, d, DT); break; }
      P.box(a, y, b, c, y, d, DT); P.box(a + 1, y, b + 1, c - 1, y, d - 1, AIR);
      for (let x = a + 1; x < c; x++) { P.set(x, y, b, DTS, { weirdo_direction: STAIR.s, upside_down_bit: false }); P.set(x, y, d, DTS, { weirdo_direction: STAIR.n, upside_down_bit: false }); }
      for (let z = b + 1; z < d; z++) { P.set(a, y, z, DTS, { weirdo_direction: STAIR.e, upside_down_bit: false }); P.set(c, y, z, DTS, { weirdo_direction: STAIR.w, upside_down_bit: false }); }
      a++; b++; c--; d--; y++;
    }
    P.set(tc, y + 1, tz, M("lightning_rod"), { facing_direction: 1 });
    P.box(tc, y + 2, tz, tc, y + 2, tz, AIR);
  }
  // أبراج القلعة الأربعة (أطول وسقوف مدببة = معلم من بعيد) + برج المدخل
  tower(P, x1 - 1, z1 - 1, 4, 22, "spire", [{ dir: "e", y: 10, off: 2 }, { dir: "s", y: 0, door: true }], 31);   // فتحة على البلكونة (z1+1)
  tower(P, x2 + 1, z1 - 1, 4, 22, "spire", [{ dir: "w", y: 10, off: 2 }, { dir: "s", y: 0, door: true }], 32);
  tower(P, x1 - 1, z2 + 1, 4, 20, "spire", [{ dir: "n", y: 0 }, { dir: "e", y: 0, door: true }], 33);
  tower(P, x2 + 1, z2 + 1, 4, 20, "spire", [{ dir: "n", y: 0 }, { dir: "w", y: 0, door: true }], 34);
  P.marks.castle = { x: ex, z: z2 + 4 };
  // الفناء الأمامي: نافورة صغيرة وأحواض زهور وتماثيل حجر
  pave(P, x1 - 6, z2 + 2, x2 + 6, z2 + 16, "plaza", 5);
  for (const sx of [ex - 12, ex + 12]) { hedge(P, sx - 3, z2 + 6, sx + 3, z2 + 6); flowerBed(P, sx - 3, z2 + 7, sx + 3, z2 + 9, sx); hedge(P, sx - 3, z2 + 10, sx + 3, z2 + 10); }
  for (const sx of [ex - 5, ex + 5]) { F.set(sx, 0, z2 + 12, CSB); F.set(sx, 1, z2 + 12, M("stone_brick_wall")); F.set(sx, 2, z2 + 12, M("lantern"), { hanging: false }); P.lights++; }
  P.post("guard", ex - 3, 0, z2 + 3, 3); P.post("guard", ex + 3, 0, z2 + 3, 3);
}

// ───────────────────────── الأكاديمية ─────────────────────────
function academy(P) {
  const F = P.frame(0, 0, 0), x1 = 14, x2 = 59, z1 = 12, z2 = 41, H = 11;
  F.mix(x1, 0, z1, x2, H - 1, z2, STONE, STONE_W, 140);
  F.box(x1 + 1, 0, z1 + 1, x2 - 1, H - 2, z2 - 1, AIR);
  F.box(x1 + 1, -1, z1 + 1, x2 - 1, -1, z2 - 1, M("dark_oak_planks"));
  F.box(x1 + 1, 5, z1 + 1, x2 - 1, 5, z2 - 1, M("spruce_planks"));                  // الطابق الثاني
  for (let x = x1; x <= x2; x += 5) for (const z of [z1, z2]) F.logs(x, 0, z, x, H - 1, z, DLOG, "y");
  F.logs(x1, 5, z1, x2, 5, z1, DLOG, "x"); F.logs(x1, 5, z2, x2, 5, z2, DLOG, "x");
  for (let x = x1 + 2; x < x2; x += 5) for (const z of [z1, z2]) { F.box(x, 1, z, x + 2, 3, z, GPANE); F.box(x, 7, z, x + 2, 8, z, GPANE); }
  for (let z = z1 + 3; z < z2; z += 6) for (const x of [x1, x2]) { F.box(x, 1, z, x, 3, z + 2, GPANE); F.box(x, 7, z, x, 8, z + 2, GPANE); }
  // مدخل جنوبي بدرجات وعمودين
  const ex = 36;
  F.air(ex - 1, 0, z2, ex + 1, 3, z2); F.door(ex - 1, 0, z2, SDOOR, "s"); F.door(ex + 1, 0, z2, SDOOR, "s"); F.air(ex, 0, z2, ex, 2, z2);
  F.box(ex - 3, -1, z2 + 1, ex + 3, -1, z2 + 3, SB);
  for (const x of [ex - 3, ex + 3]) F.box(x, 0, z2 + 1, x, 4, z2 + 1, M("quartz_pillar"), { pillar_axis: "y" });
  F.box(ex - 3, 5, z2 + 1, ex + 3, 5, z2 + 1, CSB);
  // سقف جملوني على محور x
  const ry = H, half = Math.ceil((z2 - z1 + 3) / 2);
  for (let k = 0; k < half; k++) {
    const y = ry + k, a = z1 - 1 + k, b = z2 + 1 - k;
    if (a > b) break;
    if (a === b) { F.box(x1 - 1, y, a, x2 + 1, y, a, DSL, { "minecraft:vertical_half": "bottom" }); break; }
    for (let x = x1 - 1; x <= x2 + 1; x++) { F.set(x, y, a, DOS, { weirdo_direction: STAIR.s, upside_down_bit: false }); F.set(x, y, b, DOS, { weirdo_direction: STAIR.n, upside_down_bit: false }); }
    if (b - a >= 2) { F.box(x1, y, a + 1, x1, y, b - 1, SPR); F.box(x2, y, a + 1, x2, y, b - 1, SPR); }
  }
  for (let x = x1 + 4; x < x2; x += 9) P.set(x, H, 26, M("lantern"), { hanging: false });   // فوانيس العلية المغلقة
  // برج المرصد (قبة زجاج) بالزاوية
  tower(P, x2 + 4, z1 + 4, 4, 20, "flat", [{ dir: "s", y: 0, door: true }], 41);
  F.box(x2, 21, z1, x2 + 8, 21, z1 + 8, M("smooth_stone"));
  F.box(x2 + 1, 22, z1 + 1, x2 + 7, 24, z1 + 7, M("light_blue_stained_glass"));
  F.box(x2 + 2, 22, z1 + 2, x2 + 6, 24, z1 + 6, AIR);
  F.box(x2 + 2, 25, z1 + 2, x2 + 6, 25, z1 + 6, M("light_blue_stained_glass"));
  F.set(x2 + 4, 22, z1 + 4, M("enchanting_table"));
  // جوه: مكتبة (رفوف للسقف) بالجهة الغربية، صف دراسي (مقاعد ومناضد) بالشرق، ومختبر جرعات فوق
  for (let z = z1 + 2; z <= z2 - 2; z++) { if ((z - z1) % 4 === 0) continue; F.box(x1 + 1, 0, z, x1 + 1, 4, z, M("bookshelf")); }
  for (let x = x1 + 4; x <= x1 + 14; x += 4) for (let z = z1 + 3; z <= z2 - 4; z++) if ((z - z1) % 6 !== 0) F.box(x, 0, z, x, 3, z, M("bookshelf"));
  F.card(x1 + 6, 0, z1 + 2, M("lectern"), "s", { powered_bit: false }); F.card(x1 + 10, 0, z1 + 2, M("lectern"), "s", { powered_bit: false });
  // صف: 4 صفوف مقاعد (درجة) ومنضدة (ترابدور فوق سياج)
  for (let r = 0; r < 4; r++) for (let x = x1 + 22; x <= x2 - 4; x += 3) {
    const z = z1 + 6 + r * 5;
    F.set(x, 0, z, SFENCE); F.trap(x, 1, z, STRAP, false); F.air(x, 1, z, x, 1, z); F.set(x, 1, z, M("spruce_pressure_plate"));
    F.stair(x, 0, z + 1, SST, "s");
  }
  F.box(x1 + 30, 0, z1 + 1, x1 + 36, 2, z1 + 1, M("black_concrete"));            // سبورة
  F.card(x1 + 33, 0, z1 + 3, M("lectern"), "s", { powered_bit: false });
  // فوق: مختبر
  for (let x = x1 + 3; x <= x2 - 3; x += 6) { F.set(x, 6, z1 + 2, M("brewing_stand"), { brewing_stand_slot_a_bit: false, brewing_stand_slot_b_bit: false, brewing_stand_slot_c_bit: false }); F.set(x + 1, 6, z1 + 2, M("cauldron"), { cauldron_liquid: "water", fill_level: 6 }); F.set(x + 2, 6, z1 + 2, M("bookshelf")); }
  F.chest(x2 - 2, 6, z2 - 2, "w", "city_academy");
  // درج داخلي
  for (let i = 0; i < 5; i++) F.set(x2 - 2, i, z2 - 8 + i, SST, { weirdo_direction: STAIR.s, upside_down_bit: false });
  F.air(x2 - 2, 5, z2 - 8, x2 - 2, 5, z2 - 4);
  for (let x = x1 + 6; x < x2; x += 10) { F.lantern(x, 4, z1 + 14, true); F.lantern(x, 9, z1 + 14, true); }
  // حديقة الأكاديمية
  pave(P, x1, z2 + 4, x2, z2 + 6, "cobble", 3);
  for (let x = x1 + 3; x < x2; x += 8) tree(P, x, z2 + 12, x % 16 === 1 ? "birch" : "oak", 5);
  flowerBed(P, x1 + 2, z2 + 8, x2 - 2, z2 + 9, 7);
  P.marks.academy = { x: ex, z: z2 + 3 };
}

// ───────────────────────── دار البلدية (برج الجرس) ─────────────────────────
function townHall(P) {
  const F = P.frame(0, 0, 0), x1 = 186, x2 = 229, z1 = 14, z2 = 39, H = 10;
  F.mix(x1, 0, z1, x2, H - 1, z2, STONE, STONE_W, 160);
  F.box(x1 + 1, 0, z1 + 1, x2 - 1, H - 2, z2 - 1, AIR);
  F.box(x1 + 1, -1, z1 + 1, x2 - 1, -1, z2 - 1, M("polished_andesite"));
  for (let x = x1; x <= x2; x += 6) for (const z of [z1, z2]) F.logs(x, 0, z, x, H - 1, z, SPL, "y");
  for (let x = x1 + 2; x < x2 - 1; x += 6) for (const z of [z1, z2]) F.box(x, 2, z, x + 2, 6, z, GPANE);
  // جملوني
  const ry = H, half = Math.ceil((z2 - z1 + 3) / 2);
  for (let k = 0; k < half; k++) {
    const y = ry + k, a = z1 - 1 + k, b = z2 + 1 - k;
    if (a > b) break;
    if (a === b) { F.box(x1 - 1, y, a, x2 + 1, y, a, DTSL, { "minecraft:vertical_half": "bottom" }); break; }
    for (let x = x1 - 1; x <= x2 + 1; x++) { F.set(x, y, a, DTS, { weirdo_direction: STAIR.s, upside_down_bit: false }); F.set(x, y, b, DTS, { weirdo_direction: STAIR.n, upside_down_bit: false }); }
    if (b - a >= 2) { F.box(x1, y, a + 1, x1, y, b - 1, SPR); F.box(x2, y, a + 1, x2, y, b - 1, SPR); }
  }
  for (let x = x1 + 4; x < x2; x += 9) P.set(x, H, 26, M("lantern"), { hanging: false });   // فوانيس العلية المغلقة
  // برج الجرس بالواجهة (جنوب الوسط) بساعة حجرية وجرس معلق
  const bx = 207;
  F.mix(bx - 3, 0, z2 - 2, bx + 3, 22, z2 + 4, STONE, STONE_W, 161);
  F.box(bx - 2, 0, z2 - 1, bx + 2, 21, z2 + 3, AIR);
  F.air(bx - 1, 0, z2 - 2, bx + 1, 3, z2 - 2);                                       // ممر من البرج للقاعة
  F.air(bx - 1, 0, z2 + 4, bx + 1, 4, z2 + 4); F.door(bx - 1, 0, z2 + 4, SDOOR, "s"); F.door(bx + 1, 0, z2 + 4, SDOOR, "s"); F.air(bx, 0, z2 + 4, bx, 3, z2 + 4);
  F.box(bx - 1, 12, z2 + 4, bx + 1, 14, z2 + 4, M("smooth_quartz")); F.set(bx, 13, z2 + 4, M("gold_block")); F.set(bx, 14, z2 + 4, M("gold_block"));   // وجه الساعة
  F.air(bx - 3, 18, z2 - 2, bx + 3, 20, z2 + 4); F.box(bx - 2, 18, z2 - 1, bx + 2, 18, z2 + 3, SPR);
  for (const [u, v] of [[bx - 3, z2 - 2], [bx + 3, z2 - 2], [bx - 3, z2 + 4], [bx + 3, z2 + 4]]) F.box(u, 18, v, u, 20, v, SB);
  F.box(bx - 3, 21, z2 - 2, bx + 3, 21, z2 + 4, SB);
  F.set(bx, 20, z2 + 1, M("bell"), { attachment: "hanging", direction: 2, toggle_bit: false });
  for (let k = 0; k < 4; k++) { F.box(bx - 3 + k, 22 + k, z2 - 2 + k, bx + 3 - k, 22 + k, z2 + 4 - k, DT); F.box(bx - 2 + k, 22 + k, z2 - 1 + k, bx + 2 - k, 22 + k, z2 + 3 - k, AIR); }
  F.set(bx, 26, z2 + 1, M("lightning_rod"), { facing_direction: 1 });
  F.ladder(bx + 2, 0, 17, z2 - 1, "s");
  // جوه: قاعة المجلس (طاولة مستديرة بمقاعد)، أرشيف (براميل ورفوف)
  const cx = 198, cz = 26;
  for (let x = cx - 3; x <= cx + 3; x++) for (let z = cz - 2; z <= cz + 2; z++) {
    const edge = Math.abs(x - cx) === 3 || Math.abs(z - cz) === 2;
    if (edge) { F.set(x, 0, z, SFENCE); F.set(x, 1, z, M("spruce_pressure_plate")); }
  }
  for (let x = cx - 3; x <= cx + 3; x += 2) { F.stair(x, 0, cz - 3, SST, "n"); F.stair(x, 0, cz + 3, SST, "s"); }
  F.set(cx, 1, cz, M("lectern"), { "minecraft:cardinal_direction": "south", powered_bit: false }); F.set(cx, 0, cz, M("chiseled_stone_bricks"));
  for (let z = z1 + 2; z <= z2 - 2; z += 2) { F.barrel(x2 - 2, 0, z); F.barrel(x2 - 2, 1, z); F.set(x2 - 3, 0, z, M("bookshelf")); }
  F.chest(x2 - 2, 0, z1 + 1, "w", "city_hall");
  F.set(x1 + 2, 0, z1 + 2, M("cartography_table")); F.set(x1 + 3, 0, z1 + 2, M("loom"), { direction: 0 });
  for (let x = x1 + 6; x < x2; x += 10) F.lantern(x, H - 3, cz, true);
  // ساحة أمامية من باب برج الجرس للشارع الشمالي، وأحواض زهور وسياج شجيرات على الجانبين
  pave(P, bx - 3, z2 + 5, bx + 3, 57, "plaza", 6);
  for (const [a, b] of [[x1 + 1, bx - 6], [bx + 6, x2 - 1]]) { hedge(P, a, 45, b, 45); flowerBed(P, a, 46, b, 49, a); hedge(P, a, 50, b, 50); }
  for (const x of [bx - 4, bx + 4]) lamp(P, x, 52, x < bx ? "e" : "w");
  P.marks.hall = { x: bx, z: z2 + 6 };
  P.post("guard", bx - 3, 0, z2 + 6, 3);
}

// ───────────────────────── الساحة المركزية + النافورة ─────────────────────────
function plaza(P) {
  const cx = 124, cz = 124, R = 21;
  for (let x = cx - R; x <= cx + R; x++) for (let z = cz - R; z <= cz + R; z++) {
    const d = Math.hypot(x - cx, z - cz);
    if (d > R + 0.4) continue;
    const ring = Math.floor(d);
    const id = ring % 6 === 0 ? PAND : ring % 6 === 3 ? M("smooth_stone") : hash3(x, 0, z, 77) < 0.12 ? M("cracked_stone_bricks") : SB;
    P.set(x, -1, z, id); P.mark(x, z, x, z, 2);
  }
  // نافورة بطبقتين: حوض r=5 بحافة، عمود منحوت، وماء ينزل من القمة للحوض
  const F = P.frame(cx, cz, 0);
  for (let x = -6; x <= 6; x++) for (let z = -6; z <= 6; z++) {
    const d = Math.hypot(x, z);
    if (d <= 5.4) { F.set(x, -1, z, SB); F.set(x, 0, z, M("water")); }
    else if (d <= 6.5) { F.set(x, 0, z, SB); F.slab(x, 1, z, SBSL); }
  }
  F.box(-1, -1, -1, 1, 3, 1, CSB); F.box(0, 0, 0, 0, 4, 0, M("quartz_pillar"), { pillar_axis: "y" });
  F.box(-1, 4, -1, 1, 4, 1, SBSL, { "minecraft:vertical_half": "top" });
  F.set(0, 5, 0, M("water"));
  // أربعة أشجار بأحواض، مقاعد، أعمدة إنارة، أحواض زهور
  for (const [dx, dz] of [[-13, -13], [13, -13], [-13, 13], [13, 13]]) {
    F.box(dx - 1, 0, dz - 1, dx + 1, 0, dz + 1, SB); F.box(dx, 0, dz, dx, 0, dz, M("grass_block"));
    tree(P, cx + dx, cz + dz, "oak", 6); P.set(cx + dx, 0, cz + dz, M("oak_log"), { pillar_axis: "y" });
  }
  bench(P, cx - 2, cz - 10, "s"); bench(P, cx - 2, cz + 10, "n"); bench(P, cx - 10, cz - 2, "e"); bench(P, cx + 10, cz - 2, "w");
  for (const [dx, dz] of [[-8, -8], [8, -8], [-8, 8], [8, 8], [-18, 0], [18, 0], [0, -18], [0, 18]]) lamp(P, cx + dx, cz + dz, dx >= 0 ? "w" : "e");
  for (const [dx, dz] of [[-17, -10], [12, -17], [-17, 7], [12, 14]]) flowerBed(P, cx + dx, cz + dz, cx + dx + 4, cz + dz + 2, dx + dz);
  P.post("guard", cx - 5, 0, cz + 19, 6); P.post("guard", cx + 5, 0, cz - 19, 6);

  P.marks.plaza = { x: cx, z: cz };
}

// ───────────────────────── السوق (أكشاك بمظلات صوف ملونة) + النزل ─────────────────────────
function stall(P, x, z, rot, color, goods) {
  const F = P.frame(x, z, rot);
  for (const [u, v] of [[0, 0], [4, 0], [0, 3], [4, 3]]) F.box(u, 0, v, u, 2, v, SFENCE);
  for (let u = 0; u <= 4; u++) for (let v = 0; v <= 3; v++) F.set(u, 3, v, M((u % 2 === 0 ? color : "white") + "_wool"));
  F.slabs(-1, 3, -1, 5, -1, SSL); F.slabs(-1, 3, 4, 5, 4, SSL); F.slabs(-1, 3, 0, -1, 3, SSL); F.slabs(5, 3, 0, 5, 3, SSL);
  for (let u = 1; u <= 3; u++) F.trap(u, 0, 3, STRAP, true);                         // منضدة البيع لقدام
  F.set(0, 0, 3, M("barrel"), { facing_direction: 1, open_bit: false });
  goods.forEach((g, i) => { if (g) F.set(1 + i, 0, 1, M(g), g === "hay_block" ? { deprecated: 0, pillar_axis: "y" } : undefined); });
  F.lantern(2, 2, 0, true);
}
function market(P) {
  // ساحة السوق (أصغر من قبل): رصف مخلوط بحافة طوب، يقطعها الشارع العرضي (z 120..128)
  pave(P, 158, 79, 224, 151, "market", 9);
  P.box(158, -1, 79, 224, -1, 79, SB); P.box(158, -1, 151, 224, -1, 151, SB); P.box(158, -1, 79, 158, -1, 151, SB); P.box(224, -1, 79, 224, -1, 151, SB);
  // دكاكين حول الساحة (طابقين، مظلات ملونة): صف شمالي أبوابه للجنوب، وصف جنوبي أبوابه للشمال
  const kinds = ["bakery", "tailor", "scribe", "fletcher", "apothecary", "butcher", "toolsmith", "grocer"];
  let i = 0;
  for (const x of [160, 172, 184, 200, 212]) shop(P, x, 66, 0, kinds[i % 8], i++);
  for (const x of [160, 172, 184, 200, 212]) shop(P, x + 8, 162, 2, kinds[(i + 3) % 8], i++);
  for (const x of [160, 172, 184, 200, 212]) { pave(P, x + 3, 76, x + 5, 78, "cobble", x); pave(P, x + 3, 152, x + 5, 152, "cobble", x + 1); }
  // الشرق: النزل "الفانوس الذهبي" (كبير، طابقين) وبيت التجار، أبوابهم للغرب على الساحة
  house(P, 237, 92, 1, 15, 12, { floors: 2, lower: "stone", upper: "plaster", roofKind: "brick", carpet: "red_carpet", carpet2: "green_carpet", loot: "city_inn" });
  house(P, 237, 133, 1, 13, 11, { floors: 2, lower: "stone", upper: SPR, roofKind: "slate", carpet: "blue_carpet", carpet2: "light_gray_carpet", loot: "city_market" });
  // أكشاك بمظلات ملونة: صفين بالنص الشمالي حول البئر وصفين بالنص الجنوبي
  const colors = ["red", "blue", "yellow", "green", "orange", "purple", "light_blue", "lime", "cyan", "magenta", "brown", "pink"];
  const goodsList = [["pumpkin", "melon_block", "hay_block"], ["barrel", "crafting_table", "barrel"], ["hay_block", "hay_block", "composter"], ["melon_block", "pumpkin", "barrel"],
    ["bookshelf", "barrel", "bookshelf"], ["barrel", "barrel", "hay_block"], ["pumpkin", "barrel", "melon_block"], ["hay_block", "barrel", "pumpkin"]];
  let j = 0;
  for (const x of [164, 172, 202, 210]) stall(P, x, 86, 0, colors[j % 12], goodsList[j++ % 8]);
  for (const x of [168, 176, 206, 214]) stall(P, x, 114, 2, colors[j % 12], goodsList[j++ % 8]);
  for (const x of [168, 176, 206, 214]) stall(P, x, 137, 2, colors[j % 12], goodsList[j++ % 8]);
  for (const x of [164, 172, 202, 210]) stall(P, x, 141, 0, colors[j % 12], goodsList[j++ % 8]);
  // بئر بالنص الشمالي، وحوله مقاعد وأشجار بأحواض
  const F = P.frame(191, 99, 0);
  F.mix(-2, -1, -2, 2, 0, 2, COBBLE, COBBLE_W, 170); F.box(-1, -1, -1, 1, 0, 1, M("water"));
  for (const [u, v] of [[-2, -2], [2, -2], [-2, 2], [2, 2]]) F.box(u, 1, v, u, 2, v, SFENCE);
  F.box(-2, 3, -2, 2, 3, 2, SSL, { "minecraft:vertical_half": "bottom" }); F.set(0, 3, 0, SPR); F.lantern(0, 2, 0, true);
  bench(P, 189, 93, "s"); bench(P, 189, 105, "n");
  for (const [x, z] of [[183, 91], [199, 91], [183, 107], [199, 107]]) { P.box(x - 1, 0, z - 1, x + 1, 0, z + 1, SB); P.set(x, 0, z, M("grass_block")); tree(P, x, z, "oak", 5); P.set(x, 0, z, M("oak_log"), { pillar_axis: "y" }); }
  // أعمدة إنارة على حافة الساحة، ونافورة صغيرة بالنص الجنوبي
  for (const [x, z] of [[160, 81], [222, 81], [160, 149], [222, 149], [191, 81], [191, 149]]) lamp(P, x, z, x < 191 ? "e" : "w");
  smallFountain(P, 191, 140);
  P.post("woman", 191, 0, 104, 18);
  P.marks.market = { x: 191, z: 116 };
}
// نافورة صغيرة: حوض 5×5 بحافة نص بلوكة، عمود طوب وماء فوقه ينزل للحوض
function smallFountain(P, cx, cz) {
  const F = P.frame(cx, cz, 0);
  F.box(-2, -1, -2, 2, -1, 2, SB);
  F.box(-2, 0, -2, 2, 0, 2, SB); F.box(-1, 0, -1, 1, 0, 1, M("water"));
  for (let u = -2; u <= 2; u++) for (const v of [-2, 2]) { F.slab(u, 1, v, SBSL); F.slab(v, 1, u, SBSL); }
  F.set(0, 0, 0, CSB); F.set(0, 1, 0, M("stone_brick_wall")); F.set(0, 2, 0, CSB); F.set(0, 3, 0, M("water"));
}

// ───────────────────────── الحي السكني ─────────────────────────
function residential(P) {
  // شوارع ترابية/حجر بين صفوف البيوت
  for (const z of [80, 113, 159, 192]) pave(P, 10, z, 100, z + 2, "dirt", z);
  for (const x of [30, 64, 96]) { pave(P, x, 66, x + 2, 118, "dirt", x); pave(P, x, 130, x + 2, 196, "dirt", x + 1); }
  const sizes = [[9, 8, 1], [11, 9, 1], [13, 10, 2]];                               // صغير، وسط، كبير (طابقين) مثل الصورة
  const lots = [];
  // [أعلى z للصف، الدوران]: 0 = الباب للجنوب، 2 = الباب للشمال (يطل على الشارع)
  for (const [zr, rot] of [[66, 0], [85, 2], [99, 0], [131, 2], [145, 0], [164, 2], [178, 0]]) {
    for (const [xa, xb] of [[12, 28], [34, 62], [68, 94]]) {
      let x = xa;
      while (x < xb - 8) {
        const s = sizes[Math.floor(hash3(x, 1, zr, 55) * 3)], w = s[0], d = s[1];
        if (x + w - 1 > xb) break;
        lots.push({ x, z: zr, w, d, floors: s[2], rot });
        x += w + 3;
      }
    }
  }
  lots.forEach((L, i) => {
    const d = Math.min(L.d, 11), st = houseStyle(i, L.floors, 1);
    if (L.rot === 0) house(P, L.x, L.z, 0, L.w, d, st);
    else house(P, L.x + L.w - 1, L.z + d - 1, 2, L.w, d, st);
  });
  // سياج شجيرات بين الحدائق الخلفية (الصفوف ظهر لظهر)، وأعمدة إنارة على الأزقة
  for (const z of [97, 143, 176]) for (const [xa, xb] of [[11, 29], [33, 63], [67, 95]]) hedge(P, xa, z, xb, z);
  for (let z = 70; z < 196; z += 14) { if (z > 114 && z < 132) continue; lamp(P, 29, z, "w"); lamp(P, 63, z, "w"); lamp(P, 95, z, "w"); }
  P.marks.homes = { x: 48, z: 130 };
  return lots.length;
}

// ───────────────────────── المزارع والحدائق ─────────────────────────
function farms(P) {
  const crops = [["wheat", 7], ["carrots", 7], ["potatoes", 7], ["beetroot", 3]];
  let k = 0;
  for (let fx = 150; fx <= 194; fx += 22) for (let fz = 172; fz <= 214; fz += 22) {
    const F = P.frame(fx, fz, 0), W = 17, D = 15, [crop, g] = crops[k % 4]; k++;
    F.box(-1, 0, -1, W, 0, -1, SFENCE); F.box(-1, 0, D, W, 0, D, SFENCE); F.box(-1, 0, -1, -1, 0, D, SFENCE); F.box(W, 0, -1, W, 0, D, SFENCE);
    F.card(Math.floor(W / 2), 0, D, M("spruce_fence_gate"), "s", { in_wall_bit: false, open_bit: false });
    for (let v = 0; v < D; v++) {
      if (v % 4 === 3) { F.box(0, -1, v, W - 1, -1, v, M("water")); continue; }
      F.box(0, -1, v, W - 1, -1, v, M("farmland"), { moisturized_amount: 7 });
      F.box(0, 0, v, W - 1, 0, v, M(crop), { growth: g });
    }
    F.lantern(-1, 1, -1, false); F.lantern(W, 1, D, false);
    P.mark(fx - 1, fz - 1, fx + W, fz + D, 1);                                        // الحقل كله (حتى سواقي الماء) مشغول
  }
  // حظيرة كبيرة (قش، معالف، أدوات)
  house(P, 232, 170, 1, 13, 12, { floors: 1, lower: "plank", roofKind: "spruce", chimney: false, kind: "stable", loot: "city_barn" });
  for (let i = 0; i < 6; i++) P.set(222 + (i % 3), 0, 188 + Math.floor(i / 3), M("hay_block"), { deprecated: 0, pillar_axis: "y" });
  P.set(226, 0, 188, M("composter"), { composter_fill_level: 3 });
  // بستان أزاليا مزهر + خلايا نحل + زهور
  for (let x = 152; x <= 232; x += 8) tree(P, x, 236, "bloom", 4);
  for (const x of [156, 176, 196, 216]) P.set(x, 0, 233, M("beehive"), { direction: 0, honey_level: 3 });
  flowerField(P, 216, 196, 236, 226, ["red_tulip", "orange_tulip", "white_tulip", "pink_tulip", "cornflower", "allium", "oxeye_daisy"]);
  P.marks.farms = { x: 190, z: 200 };
}

// ───────────────────────── الحداد والورشة + ثكنة الحرس ─────────────────────────
function blacksmith(P) {
  const F = P.frame(0, 0, 0), x1 = 18, x2 = 35, z1 = 204, z2 = 216;
  F.mix(x1, 0, z1, x2, 5, z2, COBBLE, COBBLE_W, 180);
  F.box(x1 + 1, 0, z1 + 1, x2 - 1, 5, z2 - 1, AIR);
  F.box(x1 + 1, -1, z1 + 1, x2 - 1, -1, z2 - 1, M("stone"));
  F.air(x1 + 1, 0, z2, x2 - 1, 3, z2);                                               // واجهة مفتوحة بأعمدة خشب
  for (let x = x1; x <= x2; x += 4) F.logs(x, 0, z2, x, 4, z2, SPL, "y");
  F.logs(x1, 4, z2, x2, 4, z2, SPL, "x");
  // سقف مائل خشب
  for (let k = 0; k < 8; k++) for (let x = x1 - 1; x <= x2 + 1; x++) { F.set(x, 6 + Math.floor(k / 2), z1 - 1 + k, SST, { weirdo_direction: STAIR.s, upside_down_bit: false }); }
  F.box(x1 - 1, 6, z1 + 7, x2 + 1, 9, z2 + 1, AIR);
  for (let k = 0; k < 8; k++) for (let x = x1 - 1; x <= x2 + 1; x++) F.set(x, 9 - Math.floor(k / 2), z1 + 7 + k, SST, { weirdo_direction: STAIR.n, upside_down_bit: false });
  F.box(x1, 6, z1, x2, 9, z1 + 6, SPR); F.box(x1 + 1, 6, z1 + 1, x2 - 1, 8, z1 + 6, AIR);
  // الكور (فرن عالي) ومدخنة، سندان، طاولة حدادة، حجر شحذ، قدر حمم (يضوي)، براميل
  F.mix(x1 + 1, 0, z1 + 1, x1 + 3, 13, z1 + 2, [M("brick_block"), M("cobblestone")], [70, 30], 181);
  F.card(x1 + 2, 0, z1 + 3, M("blast_furnace"), "s"); F.card(x1 + 4, 0, z1 + 1, M("blast_furnace"), "s");
  F.card(x1 + 2, 14, z1 + 1, M("campfire"), "s", { extinguished: false });
  F.set(x1 + 6, 0, z1 + 5, M("anvil"), { "minecraft:cardinal_direction": "east" }); F.set(x1 + 8, 0, z1 + 5, M("smithing_table"));
  F.set(x1 + 10, 0, z1 + 2, M("grindstone"), { attachment: "standing", direction: 0 });
  F.set(x1 + 12, 0, z1 + 1, M("cauldron"), { cauldron_liquid: "lava", fill_level: 6 });
  F.barrel(x2 - 2, 0, z1 + 1); F.barrel(x2 - 2, 1, z1 + 1); F.barrel(x2 - 3, 0, z1 + 1);
  F.chest(x2 - 1, 0, z1 + 4, "w", "city_smith");
  F.lantern(x1 + 8, 4, z1 + 6, true); F.lantern(x2 - 4, 4, z1 + 6, true);
  // ورشة النجار والحظيرة الصغيرة
  house(P, 44, 202, 0, 11, 9, { floors: 1, lower: "cobble", carpet: "light_gray_carpet" });
  P.set(47, 0, 207, M("stonecutter_block"), { "minecraft:cardinal_direction": "south" }); P.set(48, 0, 207, M("loom"), { direction: 0 }); P.set(46, 0, 207, M("fletching_table"));
  for (let i = 0; i < 6; i++) F.logs(18 + i, 0, 222, 18 + i, 1, 222, SPL, "z");             // كومة جذوع
  pave(P, 14, 196, 70, 198, "dirt", 4); pave(P, 14, 218, 70, 220, "dirt", 5);
  P.post("man", 28, 0, 219, 10);
  P.marks.smith = { x: 27, z: 219 };
}
function barracks(P) {
  const F = P.frame(0, 0, 0), x1 = 80, x2 = 106, z1 = 206, z2 = 224;
  F.mix(x1, 0, z1, x2, 6, z2, STONE, STONE_W, 190);
  F.box(x1 + 1, 0, z1 + 1, x2 - 1, 6, z2 - 1, AIR);
  F.box(x1 + 1, -1, z1 + 1, x2 - 1, -1, z2 - 1, M("spruce_planks"));
  for (let x = x1; x <= x2; x += 2) if ((x - x1) % 4 === 0) { F.set(x, 7, z1, SB); F.set(x, 7, z2, SB); }
  F.box(x1, 7, z1, x2, 7, z2, M("smooth_stone")); F.box(x1 + 1, 7, z1 + 1, x2 - 1, 7, z2 - 1, SPR);
  for (let x = x1 + 3; x < x2; x += 5) for (const z of [z1, z2]) F.box(x, 2, z, x, 3, z, M("iron_bars"));
  const ex = 93; F.air(ex - 1, 0, z2, ex + 1, 2, z2); F.door(ex, 0, z2, SDOOR, "s"); F.box(ex - 1, 0, z2, ex - 1, 2, z2, SB); F.box(ex + 1, 0, z2, ex + 1, 2, z2, SB);
  // أسرّة الحرس (صفين) وصناديق وطاولة خرائط ومنطقة تدريب
  for (let x = x1 + 2; x <= x2 - 2; x += 3) { F.bed(x, 0, z1 + 2, "n", "blue"); F.chest(x + 1, 0, z1 + 1, "s", "city_barracks"); }
  F.set(x1 + 2, 0, z2 - 2, M("cartography_table")); F.set(x1 + 3, 0, z2 - 2, M("crafting_table"));
  F.set(x2 - 2, 0, z2 - 2, M("grindstone"), { attachment: "standing", direction: 0 }); F.set(x2 - 3, 0, z2 - 2, M("anvil"), { "minecraft:cardinal_direction": "north" });
  for (let x = x1 + 4; x < x2; x += 8) F.lantern(x, 5, z1 + 9, true);
  // دمى تدريب: قش + سياج + يقطين محفور
  for (const x of [84, 90, 96, 102]) { P.set(x, 0, 230, SFENCE); P.set(x, 1, 230, M("hay_block"), { deprecated: 0, pillar_axis: "y" }); P.set(x, 2, 230, M("carved_pumpkin"), { "minecraft:cardinal_direction": "north" }); }
  pave(P, 80, 226, 108, 234, "dirt", 8);
  P.post("guard", 93, 0, 228, 6); P.post("guard", 100, 0, 228, 6);
}

// ───────────────────────── بيوت الشارع الرئيسي (أبوابها للشارع) ─────────────────────────
function avenueHouses(P) {
  const sizes = [[9, 9, 1], [11, 9, 2], [9, 9, 2], [11, 9, 1]];
  let i = 100;
  const rows = [{ side: "w", z1: 66, z2: 100 }, { side: "w", z1: 150, z2: 200 }, { side: "e", z1: 150, z2: 228 }];
  for (const R of rows) {
    let z = R.z1;
    for (;;) {
      const sz = sizes[Math.floor(hash3(z, 3, R.side === "w" ? 1 : 2, 57) * 4)], w = sz[0], d = sz[1];
      if (z + w - 1 > R.z2) break;
      const st = houseStyle(i++, sz[2], 2);
      if (R.side === "w") {
        // دوران 3: x = 108 + v (108..116)، z = oz - u؛ الباب للشرق (x = 117)
        const oz = z + w - 1, dz = oz - Math.floor(w / 2);
        house(P, 108, oz, 3, w, d, st);
        pave(P, 118, dz, 119, dz, "cobble", z);
      } else {
        // دوران 1: x = 142 - v (134..142)، z = 150.. + u؛ الباب للغرب (x = 133)
        const dz = z + Math.floor(w / 2);
        house(P, 142, z, 1, w, d, st);
        pave(P, 129, dz, 132, dz, "cobble", z);
      }
      z += w + 3;
    }
  }
}

// ───────────────────────── الحديقة العامة: بركة وجسر وكشك ─────────────────────────
function park(P) {
  const cx = 143, cz = 78, rx = 6.5, rz = 8.5;
  const ell = (x, z) => Math.hypot((x - cx) / rx, (z - cz) / rz);
  // ممشى حصى حول البركة (حلقة) وممرين للشارع الرئيسي والشارع الشمالي
  for (let x = 131; x <= 156; x++) for (let z = 64; z <= 100; z++) {
    const e = ell(x, z);
    if (e > 1.33 && e <= 1.62) pave(P, x, z, x, z, "walk", 1);
  }
  pave(P, 129, cz, 134, cz + 1, "walk", 2); pave(P, cx, 63, cx + 1, 68, "walk", 3); pave(P, cx, 88, cx + 1, 92, "walk", 4);
  // البركة: ماء (عمق بلوكة)، حافة حجر وطحلب، زنابق ماء وقصب
  for (let x = 134; x <= 152; x++) for (let z = 67; z <= 89; z++) {
    const e = ell(x, z);
    if (e <= 1) { P.set(x, -1, z, M("water")); P.mark(x, z, x, z, 1); if (e < 0.8 && hash3(x, 0, z, 450) < 0.08) P.set(x, 0, z, M("waterlily")); }
    else if (e <= 1 + 1.1 / rx) {
      const h = hash3(x, 1, z, 451);
      P.set(x, -1, z, h < 0.45 ? M("mossy_cobblestone") : h < 0.7 ? M("cobblestone") : M("grass_block")); P.mark(x, z, x, z, 1);
      if (h >= 0.7 && hash3(x, 2, z, 452) < 0.5) { P.set(x, 0, z, M("reeds"), { age: 0 }); if (hash3(x, 3, z, 453) < 0.6) P.set(x, 1, z, M("reeds"), { age: 0 }); }
    }
  }
  // جسر خشب فوق نص البركة (عرض 3، درابزين سياج)
  const F = P.frame(0, 0, 0), bz = cz;
  for (let x = cx - 8; x <= cx + 8; x++) {
    F.slabs(x, 0, bz - 1, x, bz + 1, SSL);
    F.set(x, 0, bz - 2, SPR); F.set(x, 1, bz - 2, SFENCE); F.set(x, 0, bz + 2, SPR); F.set(x, 1, bz + 2, SFENCE);
  }
  for (const x of [cx - 8, cx + 8]) { F.air(x, 1, bz - 2, x, 1, bz - 2); F.air(x, 1, bz + 2, x, 1, bz + 2); F.lantern(x, 1, bz - 2); F.lantern(x, 1, bz + 2); }
  // الكشك (gazebo) 7×7 جنوب البركة: أرضية حجر، أعمدة، سقف هرمي، مقاعد وفانوس معلق
  const gx = cx, gz = 96, G = P.frame(gx, gz, 0);
  G.box(-3, -1, -3, 3, -1, 3, M("smooth_stone")); G.box(-2, -1, -2, 2, -1, 2, M("polished_andesite"));
  for (const [u, v] of [[-3, -3], [3, -3], [-3, 3], [3, 3]]) G.logs(u, 0, v, u, 2, v, SSPR, "y");
  for (let k = 0; k <= 3; k++) {
    const r = 4 - k, y = 3 + k;
    if (r <= 1) { G.box(-1, y, -1, 1, y, 1, SPR); G.slab(0, y + 1, 0, SSL); break; }
    G.box(-r, y, -r, r, y, r, SPR); G.air(-r + 1, y, -r + 1, r - 1, y, r - 1);
    for (let t = -r + 1; t <= r - 1; t++) { G.stair(t, y, -r, SST, "s"); G.stair(t, y, r, SST, "n"); G.stair(-r, y, t, SST, "e"); G.stair(r, y, t, SST, "w"); }
  }
  G.box(-3, 3, -3, 3, 3, 3, SPR); G.air(-2, 3, -2, 2, 3, 2);
  G.lantern(0, 4, 0, true); G.box(0, 5, 0, 0, 5, 0, SPR);
  for (const t of [-1, 0, 1]) { G.stair(t, 0, -2, SST, "n"); G.stair(t, 0, 2, SST, "s"); }
  // أحواض زهور وأشجار كبيرة حول الحديقة، ومقاعد على الممشى
  flowerBed(P, 133, 92, 138, 94, 1); flowerBed(P, 148, 92, 153, 94, 2);
  for (const [x, z, k] of [[133, 99, "bloom"], [153, 99, "bloom"], [154, 67, "bigoak"], [132, 67, "bigoak"]]) if (P.free(x - 3, z - 3, x + 3, z + 3, 0, 247)) tree(P, x, z, k, k === "bigoak" ? 6 : 4);
  bench(P, cx - 1, 66, "s", 3);
  P.marks.park = { x: cx, z: cz };
}

// ───────────────────────── حدائق القلعة الرسمية (parterre) ─────────────────────────
function parterre(P, x1, z1, x2, z2, salt) {
  const cx = Math.floor((x1 + x2) / 2), cz = Math.floor((z1 + z2) / 2);
  // ممشى حصى حول الحديقة وممرين متقاطعين بالنص (عرض 3)
  pave(P, x1, z1, x2, z1, "walk", salt); pave(P, x1, z2, x2, z2, "walk", salt + 1); pave(P, x1, z1, x1, z2, "walk", salt + 2); pave(P, x2, z1, x2, z2, "walk", salt + 3);
  pave(P, cx - 1, z1, cx + 1, z2, "walk", salt + 4); pave(P, x1, cz - 1, x2, cz + 1, "walk", salt + 5);
  // أربع أحواض: سياج شجيرات بفتحة، زهور مرتبة جوه، وشجرة مزهرة بزاوية كل حوض
  const quads = [[x1 + 1, z1 + 1, cx - 2, cz - 2], [cx + 2, z1 + 1, x2 - 1, cz - 2], [x1 + 1, cz + 2, cx - 2, z2 - 1], [cx + 2, cz + 2, x2 - 1, z2 - 1]];
  quads.forEach(([a, b, c, d], q) => {
    hedge(P, a, b, c, b); hedge(P, a, d, c, d); hedge(P, a, b, a, d); hedge(P, c, b, c, d);
    const mz = Math.floor((b + d) / 2), mx = Math.floor((a + c) / 2);
    P.box(q % 2 ? a : c, 0, mz, q % 2 ? a : c, 0, mz, AIR);                          // فتحة على الممر الوسطي
    P.box(mx, 0, q < 2 ? d : b, mx, 0, q < 2 ? d : b, AIR);
    flowerBed(P, a + 1, b + 1, c - 1, d - 1, salt + q);
    // نافورة صغيرة أو شجرة مزهرة بنص كل حوض (تكسر تكرار الزهور)
    P.box(mx - 1, 0, mz - 1, mx + 1, 0, mz + 1, M("grass_block"));
    if (q % 2 === 0) { P.set(mx, -1, mz, M("grass_block")); tree(P, mx, mz, "bloom", 4); }
    else { P.box(mx - 1, 0, mz - 1, mx + 1, 0, mz + 1, M("oak_leaves"), { persistent_bit: true, update_bit: false }); P.set(mx, 1, mz, M("oak_leaves"), { persistent_bit: true, update_bit: false }); }
  });
  smallFountain(P, cx, cz);
  for (const [x, z] of [[cx - 3, z1 + 2], [cx + 3, z2 - 2], [x1 + 2, cz + 3], [x2 - 2, cz - 3]]) lamp(P, x, z, x < cx ? "e" : "w");
  bench(P, cx - 1, cz - 4, "s"); bench(P, cx - 1, cz + 4, "n");
}
function castleGardens(P) {
  parterre(P, 69, 13, 96, 53, 500);
  parterre(P, 152, 13, 182, 53, 520);
  P.marks.gardens = { x: 82, z: 33 };
}

// ───────────────────────── إسطبل وبيوت ريفية بالجنوب الغربي ─────────────────────────
function stables(P) {
  house(P, 58, 202, 0, 20, 12, { floors: 1, lower: "plank", roofKind: "spruce", chimney: false, kind: "stable", loot: "city_barn" });
  // حظيرة خيول (paddock) جنوب الطريق: سياج وبوابة، قش ومعلف ماء
  const x1 = 58, z1 = 223, x2 = 77, z2 = 236;
  P.box(x1, 0, z1, x2, 0, z1, SFENCE); P.box(x1, 0, z2, x2, 0, z2, SFENCE); P.box(x1, 0, z1, x1, 0, z2, SFENCE); P.box(x2, 0, z1, x2, 0, z2, SFENCE);
  P.set(67, 0, z1, M("spruce_fence_gate"), { "minecraft:cardinal_direction": "north", in_wall_bit: false, open_bit: false });
  P.box(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, AIR); P.mark(x1, z1, x2, z2, 4);
  P.set(x1 + 2, 0, z2 - 2, M("hay_block"), { deprecated: 0, pillar_axis: "y" }); P.set(x1 + 3, 0, z2 - 2, M("hay_block"), { deprecated: 0, pillar_axis: "y" });
  P.set(x2 - 2, 0, z1 + 2, M("cauldron"), { cauldron_liquid: "water", fill_level: 6 });
  P.set(x1, 1, z1, M("lantern"), { hanging: false }); P.set(x2, 1, z2, M("lantern"), { hanging: false }); P.lights += 2;
  pave(P, 66, 214, 68, 217, "dirt", 7); pave(P, 66, 221, 68, 222, "dirt", 8);
  // بيوت ريفية (طابق واحد) جنوب الطريق، أبوابها للشمال
  let i = 300;
  for (const [x, w] of [[10, 9], [26, 9], [42, 11]]) {
    const d = 9, st = houseStyle(i++, 1, 3);
    house(P, x + w - 1, 224 + d - 1, 2, w, d, st);
    const dx = x + w - 1 - Math.floor(w / 2);
    pave(P, dx, 221, dx, 222, "dirt", x);
  }
}

// ───────────────────────── خضرة: أشجار وعشب وزهور برية على كل العشب الفاضي ─────────────────────────
function greenery(P) {
  const S = CITY_SIZE;
  for (let gz = 10; gz < S - 10; gz += 7) for (let gx = 10; gx < S - 10; gx += 7) {
    const x = gx + Math.floor(hash3(gx, 1, gz, 901) * 5) - 2, z = gz + Math.floor(hash3(gx, 2, gz, 902) * 5) - 2;
    const edge = Math.min(x, z, S - 1 - x, S - 1 - z) < 18;
    if (hash3(x, 3, z, 903) > (edge ? 0.88 : 0.72)) continue;
    if (!P.free(x - 3, z - 3, x + 3, z + 3)) continue;
    const r = hash3(x, 4, z, 904), h = 4 + Math.floor(hash3(x, 5, z, 905) * 3);
    const kind = edge ? (r < 0.45 ? "spruce" : r < 0.8 ? "oak" : "birch") : r < 0.5 ? "oak" : r < 0.72 ? "birch" : r < 0.82 ? "spruce" : r < 0.9 ? "bloom" : "bigoak";
    if (kind === "bigoak" && !P.free(x - 4, z - 4, x + 4, z + 4)) { tree(P, x, z, "oak", h); continue; }
    tree(P, x, z, kind, kind === "bigoak" ? 6 : h);
  }
  // شجيرات صغيرة (أزاليا/بلوط) تملي الفراغات بين الأشجار، بعيدة عن الطرق والأبواب
  for (let gz = 9; gz < S - 9; gz += 4) for (let gx = 9; gx < S - 9; gx += 4) {
    const x = gx + Math.floor(hash3(gx, 6, gz, 906) * 3) - 1, z = gz + Math.floor(hash3(gx, 7, gz, 907) * 3) - 1;
    if (hash3(x, 8, z, 908) > 0.42 || !P.free(x - 1, z - 1, x + 1, z + 1)) continue;
    const r = hash3(x, 9, z, 909), L = r < 0.4 ? M("azalea_leaves") : r < 0.65 ? M("azalea_leaves_flowered") : M("oak_leaves");
    P.set(x, 0, z, L, { persistent_bit: true, update_bit: false });
    if (r > 0.82) P.set(x, 1, z, L, { persistent_bit: true, update_bit: false });
  }
  const wild = ["poppy", "dandelion", "oxeye_daisy", "azure_bluet", "cornflower"];
  for (let z = 8; z < S - 8; z++) for (let x = 8; x < S - 8; x++) {
    if (P.used[z * S + x]) continue;
    const h = hash3(x, 9, z, 910);
    if (h < 0.085) P.set(x, 0, z, M("short_grass"));
    else if (h < 0.1) P.set(x, 0, z, M("fern"));
    else if (h < 0.112) P.set(x, 0, z, M(wild[Math.floor(hash3(x, 8, z, 911) * wild.length)]));
    else if (h < 0.115 && x > 9 && z > 9 && !P.used[z * S + x + 1]) tallFlower(P, x, z, ["rose_bush", "peony", "lilac"][Math.floor(hash3(x, 7, z, 912) * 3)]);
  }
}

// ───────────────────────── تجميع المدينة ─────────────────────────
export function planCity(seed = 20260601) {
  const P = new CityPlan(seed);
  ground(P);
  // ممر الحراس داخل السور (pomerium)
  pave(P, 4, 4, 243, 7, "dirt", 1); pave(P, 4, 240, 243, 243, "dirt", 2); pave(P, 4, 4, 7, 243, "dirt", 3); pave(P, 240, 4, 243, 243, "dirt", 4);
  // الشارع الرئيسي من البوابة للقلعة، والشارع العرضي عبر الساحة
  street(P, 120, 56, 128, 239, 1);
  street(P, 8, 120, 240, 128, 2);
  street(P, 30, 58, 218, 62, 3);                                                     // شارع الشمال (أكاديمية ← قلعة ← بلدية)
  for (let z = 64; z <= 232; z += 12) { if (Math.abs(z - 124) < 26) continue; lamp(P, 119, z, "e"); lamp(P, 129, z, "w"); }
  for (let x = 12; x <= 236; x += 14) if (Math.abs(x - 124) > 24) { lamp(P, x, 119, "s"); lamp(P, x, 129, "n"); }
  castle(P); academy(P); townHall(P); plaza(P); market(P);
  const homes = residential(P);
  farms(P); blacksmith(P); barracks(P);
  avenueHouses(P); park(P); castleGardens(P); stables(P);
  walls(P);
  greenery(P);                                                                       // آخر شي: يملي العشب الفاضي بس
  P.homes = homes;
  return P;
}

// قائمة البنايات للفحص والتوثيق (مكانها التقريبي)
export const CITY_DISTRICTS = ["gate", "castle", "academy", "hall", "plaza", "market", "homes", "farms", "smith"];
