// إثيريا: بناء مدينة Aetheria بالعالم: مرة وحدة بكل عالم، بمكان ثابت بعيد عن نقطة البداية (1900..2400 بلوكة).
// الطريقة (بعد البحث بوثائق Microsoft الرسمية لـ @minecraft/server 2.10، المود يستعمله على 1.26.50):
//   1) الموقع: اتجاه عشوائي ومسافة بعيدة؛ 9 نقاط عينة كل وحدة بمنطقة تكتك صغيرة
//      (world.tickingAreaManager.createTickingArea يرجع Promise لما تتحمل القطع). نرفض البحر والنهر (getBiome + الماء)
//      ونفضل الأرض المستوية، والارتفاع = الوسيط. الموقع ينحفظ بخاصية العالم sh_city وما يتغير أبداً (ولا تنبني نسخة ثانية).
//   2) المخطط (city_plan.js) يتحول لشبكة بلوكات (city_raster.js) بخطوات صغيرة (system.runJob) حتى ما يعلق اللعب.
//   3) 16 مربع (≤ 64×64؛ حد البنية 64×384×64): لكل مربع منطقة تكتك، تنظيف فوق وأساس تحت (fillBlocks بشرائح ≤ 32 ألف،
//      الأساس يملي بس الفراغ والماء والنباتات)، بنية بالذاكرة (structureManager.createEmpty + setBlockPermutation) تنحط
//      مرة وحدة (place) بحركة طبقات، فحص عينات، تعبئة الصناديق، إظهار الشخصيات، مسح البنية وشيل المنطقة. كل مربع ينحفظ إنه خلص.
//   4) احتياط: إذا الفحص فشل (البنية ما انحطت) نكتب بلوكات المربع مباشرة.
// ما نبني مربع ولاعب قريب منه (حتى ما يعلق بالبلوكات)، وما نبدي إلا بعد دقيقة من فتح العالم.
import { world, system, BlockPermutation, BlockVolume, ItemStack, StructureSaveMode, StructureAnimationMode } from "@minecraft/server";
import { planCity, CITY_SIZE, CITY_YMIN, CITY_YMAX } from "./city_plan.js";
import { rasterize, RY, ridx, tiles } from "./city_raster.js";

const KEY = "sh_city", SEED = 20260601, VER = 1;
const DIST_MIN = 1900, DIST_MAX = 2400, HALF = CITY_SIZE / 2;
export const CITY_NPC = { guard: "sh:city_guard", king: "sh:aetheria_king", woman: "sh:townswoman", man: "sh:townsman" };
let say = () => {};
export function setCitySay(fn) { if (typeof fn === "function") say = fn; }

function load() {
  try { const r = world.getDynamicProperty(KEY); return typeof r === "string" ? JSON.parse(r) : undefined; } catch (e) { return undefined; }
}
function save(s) { try { world.setDynamicProperty(KEY, JSON.stringify(s)); } catch (e) { /* */ } }
let infoCache, infoRaw;
// مكان المدينة (للبوصلة والبنايات الثانية والوحوش): undefined قبل ما ينختار الموقع
export function cityInfo() {
  let raw;
  try { raw = world.getDynamicProperty(KEY); } catch (e) { return undefined; }
  if (raw === infoRaw) return infoCache;
  infoRaw = raw;
  const s = load();
  infoCache = s && typeof s.ox === "number" ? { x: s.ox + HALF, z: s.oz + HALF, y: s.y0, ox: s.ox, oz: s.oz, built: s.st === "built" } : undefined;
  return infoCache;
}
// النقطة داخل المدينة (مع هامش)؟
export function inCity(x, z, margin = 0) {
  const c = cityInfo();
  return !!c && x >= c.ox - margin && x < c.ox + CITY_SIZE + margin && z >= c.oz - margin && z < c.oz + CITY_SIZE + margin;
}

const wait = (ticks) => new Promise((res) => system.runTimeout(res, ticks));
// يشغل مولّد بـ runJob (أجزاء صغيرة كل تكة) ويرجع Promise لما يخلص
function runJobAsync(gen) {
  return new Promise((res, rej) => {
    system.runJob((function* () { try { yield* gen; res(); } catch (e) { rej(e); } })());
  });
}

// ───────────────────────── مناطق التكتك ─────────────────────────
const TA = () => world.tickingAreaManager;
async function loadArea(id, dim, from, to) {
  const tm = TA();
  try { if (tm.hasTickingArea(id)) tm.removeTickingArea(id); } catch (e) { /* */ }
  const opt = { dimension: dim, from, to };
  for (let i = 0; i < 30; i++) {
    let cap = false;
    try { cap = tm.hasCapacity(opt); } catch (e) { /* */ }
    if (cap) { await tm.createTickingArea(id, opt); return true; }
    await wait(100);                                                    // مشغولة (حزمة ثانية أو بناية ثانية): ننتظر
  }
  return false;
}
function freeArea(id) { try { if (TA().hasTickingArea(id)) TA().removeTickingArea(id); } catch (e) { /* */ } }

// ───────────────────────── الأرض ─────────────────────────
// فوق الأرض الحقيقية: نباتات، أوراق، جذوع، ثلج خفيف... ننزل منها لحد أول بلوكة أرض
const OVERGROWTH = /leaves|_log$|_wood$|stem$|hyphae|short_grass|tall_grass|fern|flower|tulip|poppy|dandelion|orchid|allium|bluet|daisy|cornflower|lily_of|rose_bush|peony|lilac|sunflower|bush|vine|snow_layer|mushroom|sapling|propagule|bamboo|cactus|reeds|sugar_cane|kelp|seagrass|pumpkin|melon_block|pitcher|torchflower|petals|wildflowers|leaf_litter|moss_carpet|azalea|dripleaf|roots|bee_nest|cocoa|pointed_dripstone/;
function groundAt(dim, x, z) {
  const top = dim.getTopmostBlock({ x, z });
  if (!top) return undefined;
  let y = top.y;
  for (let i = 0; i < 48; i++) {
    const b = dim.getBlock({ x, y, z });
    if (!b) return undefined;
    const id = b.typeId;
    if (/water|lava/.test(id)) return { y, water: true };
    if (!b.isAir && !OVERGROWTH.test(id)) return { y, water: false };
    y--;
  }
  return { y, water: false };
}
// تنملي تحت المدينة بس هذني (الأرض الطبيعية الصلبة تبقى)
const REPLACEABLE = { includeTypes: ["minecraft:air", "minecraft:water", "minecraft:flowing_water", "minecraft:lava", "minecraft:flowing_lava", "minecraft:short_grass", "minecraft:tall_grass",
  "minecraft:fern", "minecraft:large_fern", "minecraft:snow_layer", "minecraft:seagrass", "minecraft:kelp", "minecraft:vine", "minecraft:oak_leaves", "minecraft:spruce_leaves",
  "minecraft:birch_leaves", "minecraft:jungle_leaves", "minecraft:acacia_leaves", "minecraft:dark_oak_leaves", "minecraft:mangrove_leaves", "minecraft:cherry_leaves",
  "minecraft:azalea_leaves", "minecraft:azalea_leaves_flowered", "minecraft:pale_oak_leaves", "minecraft:deadbush", "minecraft:bush"] };

// ───────────────────────── اختيار الموقع ─────────────────────────
async function probe(dim, ox, oz) {
  const hs = [];
  let wet = 0;
  for (const fx of [0.08, 0.5, 0.92]) for (const fz of [0.08, 0.5, 0.92]) {
    const x = Math.floor(ox + fx * CITY_SIZE), z = Math.floor(oz + fz * CITY_SIZE), id = "sh:city_probe";
    if (!(await loadArea(id, dim, { x: x - 1, y: 0, z: z - 1 }, { x: x + 1, y: 0, z: z + 1 }))) { freeArea(id); return undefined; }
    try {
      const g = groundAt(dim, x, z);
      let biome = "";
      try { biome = dim.getBiome({ x, y: g ? g.y + 1 : 64, z }).id; } catch (e) { /* */ }
      if (!g || g.water || /ocean|river|beach|swamp/.test(biome)) wet++;
      else hs.push(g.y);
    } catch (e) { wet++; }
    freeArea(id);
  }
  if (wet > 1 || hs.length < 8) return undefined;                       // بحر أو نهر أو بحيرة: نرفض
  hs.sort((a, b) => a - b);
  return { y0: Math.max(-36, Math.min(250, hs[Math.floor(hs.length / 2)] + 1)), range: hs[hs.length - 1] - hs[0] };
}
async function chooseSite() {
  const dim = world.getDimension("overworld");
  const sp = world.getDefaultSpawnLocation();
  let best;
  for (let t = 0; t < 10; t++) {
    const a = Math.random() * Math.PI * 2, d = DIST_MIN + Math.random() * (DIST_MAX - DIST_MIN);
    const cx = Math.floor(sp.x + Math.cos(a) * d), cz = Math.floor(sp.z + Math.sin(a) * d);
    if (world.getAllPlayers().some((p) => Math.hypot(p.location.x - cx, p.location.z - cz) < 420)) continue;   // مو جنب لاعب
    const r = await probe(dim, cx - HALF, cz - HALF);
    if (!r) continue;
    if (!best || r.range < best.range) best = { ox: cx - HALF, oz: cz - HALF, y0: r.y0, range: r.range };
    if (r.range <= 14) break;                                            // مستوية بما يكفي
  }
  return best;
}
function announce(s) {
  const cx = s.ox + HALF, cz = s.oz + HALF;
  for (const p of world.getAllPlayers()) {
    try {
      const dx = cx - p.location.x, dz = cz - p.location.z;
      const dirs = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"];
      const dir = dirs[((Math.round((Math.atan2(dz, dx) * 180) / Math.PI / 45) % 8) + 8) % 8];
      say(p, `§6[Explore] §fTravellers speak of §eAetheria§f, the walled royal city, about ${Math.round(Math.hypot(dx, dz) / 100) * 100} blocks to the ${dir}. §7The Explorer's Compass knows the way.`);
    } catch (e) { /* */ }
  }
}

// ───────────────────────── البناء ─────────────────────────
function* fillSlices(dim, x1, y1, z1, x2, y2, z2, block, filter) {
  if (y2 < y1) return;
  const area = (x2 - x1 + 1) * (z2 - z1 + 1), layer = Math.max(1, Math.floor(32000 / area));
  for (let y = y1; y <= y2; y += layer) {
    const v = new BlockVolume({ x: x1, y, z: z1 }, { x: x2, y: Math.min(y2, y + layer - 1), z: z2 });
    dim.fillBlocks(v, block, filter ? { blockFilter: filter } : undefined);
    yield;
  }
}
function resolvePalette(P) {
  return P.pal.map((p) => {
    if (!p || p.id === "minecraft:air") return null;
    try { return BlockPermutation.resolve(p.id, p.st || undefined); } catch (e) {
      try { return BlockPermutation.resolve(p.id); } catch (e2) { return null; }
    }
  });
}
const inTile = (x, z, T) => x >= T.x0 && x < T.x0 + T.w && z >= T.z0 && z < T.z0 + T.d;
function playerNear(s, T, m) {
  const x1 = s.ox + T.x0 - m, x2 = s.ox + T.x0 + T.w + m, z1 = s.oz + T.z0 - m, z2 = s.oz + T.z0 + T.d + m;
  return world.getAllPlayers().some((p) => p.dimension.id === "minecraft:overworld" && p.location.x >= x1 && p.location.x <= x2 && p.location.z >= z1 && p.location.z <= z2);
}
// شرائط حافة المدينة (5 بلوكات) داخل هالمربع: أساسها حجر خشن (يبين مثل جدار سند إذا الأرض واطية برا)
function edgeStrips(s, T) {
  const out = [], S = CITY_SIZE, E = 5;
  const clip = (a, b, c, d) => {
    const x1 = Math.max(a, T.x0), z1 = Math.max(b, T.z0), x2 = Math.min(c, T.x0 + T.w - 1), z2 = Math.min(d, T.z0 + T.d - 1);
    if (x1 <= x2 && z1 <= z2) out.push([s.ox + x1, s.oz + z1, s.ox + x2, s.oz + z2]);
  };
  clip(0, 0, S - 1, E - 1); clip(0, S - E, S - 1, S - 1); clip(0, E, E - 1, S - E - 1); clip(S - E, E, S - 1, S - E - 1);
  return out;
}
function verify(dim, P, g, s, T, want) {
  let ok = 0, tot = 0;
  for (let k = 0; k < want * 8 && tot < want; k++) {
    const x = Math.floor(Math.random() * T.w), z = Math.floor(Math.random() * T.d), y = CITY_YMIN + Math.floor(Math.random() * 10);
    const p = P.pal[g[ridx(T.x0 + x, y, T.z0 + z)]];
    if (!p || p.id === "minecraft:air") continue;
    tot++;
    try { const b = dim.getBlock({ x: s.ox + T.x0 + x, y: s.y0 + y, z: s.oz + T.z0 + z }); if (b && b.typeId === p.id) ok++; } catch (e) { /* */ }
  }
  return tot === 0 || ok / tot >= 0.9;
}
function* writeDirect(dim, perms, g, s, T) {
  let n = 0;
  for (let y = CITY_YMIN; y <= CITY_YMAX; y++) for (let z = 0; z < T.d; z++) {
    const base = ridx(T.x0, y, T.z0 + z);
    for (let x = 0; x < T.w; x++) {
      const pm = perms[g[base + x]];
      if (!pm) continue;
      try { dim.setBlockPermutation({ x: s.ox + T.x0 + x, y: s.y0 + y, z: s.oz + T.z0 + z }, pm); } catch (e) { /* */ }
      if ((++n & 511) === 0) yield;
    }
  }
}
async function buildTile(P, g, perms, s, T, i) {
  const dim = world.getDimension("overworld");
  const x1 = s.ox + T.x0, z1 = s.oz + T.z0, x2 = x1 + T.w - 1, z2 = z1 + T.d - 1, id = `sh:city_${i}`;
  if (!(await loadArea(id, dim, { x: x1 - 1, y: s.y0, z: z1 - 1 }, { x: x2 + 1, y: s.y0, z: z2 + 1 }))) return false;
  try {
    // 1) أعلى وأوطأ أرض بالمربع (25 عينة)
    let lo = s.y0 - 1, hi = s.y0 - 1;
    for (let a = 0; a < 5; a++) for (let b = 0; b < 5; b++) {
      const gr = groundAt(dim, x1 + Math.floor((a * (T.w - 1)) / 4), z1 + Math.floor((b * (T.d - 1)) / 4));
      if (gr) { lo = Math.min(lo, gr.y); hi = Math.max(hi, gr.y); }
    }
    // 2) تنظيف فوق (هواء لحد أعلى أرض/أشجار) وأساس تحت (حافة حجر خشن، والباقي تراب)
    const top = Math.min(s.y0 + 110, Math.max(s.y0 + CITY_YMAX + 6, hi + 16));
    await runJobAsync(fillSlices(dim, x1, s.y0, z1, x2, top, z2, "minecraft:air"));
    const bot = Math.max(s.y0 - 28, lo - 1);
    if (bot <= s.y0 - 2) {
      for (const [a, b, c, d] of edgeStrips(s, T)) await runJobAsync(fillSlices(dim, a, bot, b, c, s.y0 - 2, d, "minecraft:cobblestone", REPLACEABLE));
      await runJobAsync(fillSlices(dim, x1, bot, z1, x2, s.y0 - 2, z2, "minecraft:dirt", REPLACEABLE));
    }
    // 3) البنية بالذاكرة (الخلايا الفاضية "بدون بلوكة" فتبقى هواء التنظيف) وتنحط مرة وحدة بحركة طبقات
    const sid = `sh:aetheria_${i}`;
    try { world.structureManager.delete(sid); } catch (e) { /* */ }
    const st = world.structureManager.createEmpty(sid, { x: T.w, y: RY, z: T.d }, StructureSaveMode.Memory);
    await runJobAsync((function* () {
      let n = 0;
      for (let y = 0; y < RY; y++) for (let z = 0; z < T.d; z++) {
        const base = ridx(T.x0, y + CITY_YMIN, T.z0 + z);
        for (let x = 0; x < T.w; x++) {
          const pm = perms[g[base + x]];
          if (!pm) continue;
          st.setBlockPermutation({ x, y, z }, pm);
          if ((++n & 1023) === 0) yield;
        }
      }
    })());
    world.structureManager.place(st, dim, { x: x1, y: s.y0 + CITY_YMIN, z: z1 }, { animationMode: StructureAnimationMode.Layers, animationSeconds: 5, includeEntities: false });
    await wait(5 * 20 + 40);
    // 4) فحص عينات؛ إذا البنية ما انحطت نكتب المربع مباشرة
    if (!verify(dim, P, g, s, T, 40)) await runJobAsync(writeDirect(dim, perms, g, s, T));
    try { world.structureManager.delete(sid); } catch (e) { /* */ }
    // 5) الصناديق والشخصيات بهالمربع
    for (const c of P.chests) if (inTile(c.x, c.z, T)) fillChest(dim.getBlock({ x: s.ox + c.x, y: s.y0 + c.y, z: s.oz + c.z }), c.loot);
    P.posts.forEach((p, k) => { if (inTile(p.x, p.z, T)) spawnPost(dim, s, p, k); });
    return true;
  } catch (e) {
    console.warn(`[Aetheria] tile ${i}: ${e}`);
    return false;
  } finally { freeArea(id); }
}

let job = false;
async function buildCity() {
  if (job) return;
  job = true;
  try {
    let s = load();
    if (!s) {
      const site = await chooseSite();
      if (!site) return;                                                 // ما لكينا أرض (عالم بحر؟): نحاول بعدين
      if (load()) return;                                                // (احتياط: ما نكتب فوق موقع انحفظ)
      s = { v: VER, st: "site", ox: site.ox, oz: site.oz, y0: site.y0, seed: SEED, done: 0 };
      save(s);
      announce(s);
    }
    if (s.st === "built") return;
    const P = planCity(s.seed || SEED), out = {};
    await runJobAsync(rasterize(P, out, 20000));
    const g = out.grid, perms = resolvePalette(P), T = tiles(64);
    const site = [s.ox, s.oz];
    // الحالة لازم تبقى نفس الموقع طول البناء (احتياط: إذا انمسحت أو تغيرت نوقف، والفحص الجاي يكمل من الحالة المحفوظة)
    const same = (q) => !!q && q.ox === site[0] && q.oz === site[1];
    for (let i = 0; i < T.length; i++) {
      s = load();
      if (!same(s)) return;
      if (s.done & (1 << i)) continue;
      let fails = 0;
      for (;;) {
        while (playerNear(s, T[i], 40)) await wait(200);
        if (await buildTile(P, g, perms, s, T[i], i)) break;
        await wait(Math.min(6000, 600 * ++fails));
        if (!same(load())) return;
      }
      s = load();
      if (!same(s)) return;
      s.done |= 1 << i;
      save(s);
    }
    s = load();
    if (!same(s)) return;
    s.st = "built";
    s.posts = P.posts.map((p) => [p.type, p.x, p.y, p.z]);                     // أماكن الشخصيات (للصيانة بدون إعادة حساب المخطط)
    save(s);
  } catch (e) {
    console.warn(`[Aetheria] ${e}`);
  } finally { job = false; }
}

// ───────────────────────── الصناديق ─────────────────────────
// غنائم معتدلة (المدينة ملجأ آمن، مو مكان كنوز): أكل وأدوات وزمرد، والنادر بنسبة قليلة
const POT = "pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift";
const CITY_LOOT = {
  city_house: [["minecraft:bread", 2, 5, 0.9], ["minecraft:apple", 1, 3, 0.7], ["minecraft:torch", 4, 10, 0.6], ["minecraft:emerald", 1, 3, 0.4], ["minecraft:string", 2, 5, 0.3], ["sh:xp_scroll_small", 1, 1, 0.25], [POT, 1, 1, 0.04]],
  city_market: [["minecraft:emerald", 2, 6, 0.9], ["minecraft:bread", 2, 6, 0.7], ["minecraft:white_wool", 2, 6, 0.5], ["minecraft:leather", 1, 4, 0.5], ["minecraft:arrow", 6, 16, 0.4], ["minecraft:pumpkin_pie", 1, 3, 0.4], ["sh:explorer_compass", 1, 1, 0.15]],
  city_inn: [["minecraft:bread", 3, 7, 0.9], ["minecraft:cooked_beef", 2, 5, 0.8], ["minecraft:honey_bottle", 1, 3, 0.6], ["minecraft:cake", 1, 1, 0.3], ["minecraft:emerald", 2, 5, 0.6], [POT, 1, 1, 0.08]],
  city_king: [["minecraft:emerald", 6, 14, 1.0], ["minecraft:gold_ingot", 4, 9, 0.9], ["minecraft:golden_apple", 1, 2, 0.6], ["sh:xp_scroll_big", 1, 1, 0.6], ["minecraft:diamond", 1, 3, 0.45], [POT, 1, 2, 0.4], ["minecraft:enchanted_golden_apple", 1, 1, 0.05]],
  city_academy: [["minecraft:book", 2, 6, 0.9], ["minecraft:paper", 4, 10, 0.8], ["minecraft:lapis_lazuli", 3, 8, 0.6], ["sh:xp_scroll_small", 1, 3, 0.8], ["sh:monster_book", 1, 1, 0.5], ["minecraft:experience_bottle", 2, 6, 0.4], [POT, 1, 1, 0.1]],
  city_hall: [["minecraft:paper", 4, 10, 0.9], ["minecraft:empty_map", 1, 2, 0.6], ["minecraft:compass", 1, 1, 0.5], ["minecraft:emerald", 3, 7, 0.8], ["sh:explorer_compass", 1, 1, 0.5]],
  city_smith: [["minecraft:iron_ingot", 3, 8, 0.9], ["minecraft:coal", 4, 12, 0.9], ["minecraft:gold_ingot", 1, 3, 0.4], ["minecraft:shield", 1, 1, 0.3], ["minecraft:iron_sword", 1, 1, 0.2], ["sh:raw_dawnsteel", 1, 2, 0.15]],
  city_barracks: [["minecraft:arrow", 8, 20, 0.8], ["minecraft:bread", 2, 5, 0.8], ["minecraft:iron_ingot", 1, 4, 0.5], ["minecraft:leather_helmet", 1, 1, 0.25], ["minecraft:leather_chestplate", 1, 1, 0.2], ["minecraft:shield", 1, 1, 0.15]],
  city_barn: [["minecraft:wheat", 4, 12, 0.9], ["minecraft:wheat_seeds", 4, 12, 0.8], ["minecraft:carrot", 2, 6, 0.6], ["minecraft:potato", 2, 6, 0.6], ["minecraft:leather", 1, 4, 0.5], ["minecraft:lead", 1, 2, 0.3], ["minecraft:saddle", 1, 1, 0.15]],
};
function fillChest(block, key) {
  try {
    const cont = block && block.getComponent("minecraft:inventory").container;
    if (!cont) return;
    const slots = Array.from({ length: cont.size }, (_, i) => i).sort(() => Math.random() - 0.5);
    let n = 0;
    for (const [id, lo, hi, chance] of CITY_LOOT[key] || CITY_LOOT.city_house) {
      if (Math.random() > chance) continue;
      let item = id;
      if (id.startsWith("pick:")) { const list = id.slice(5).split("|"); item = list[Math.floor(Math.random() * list.length)]; }
      try { cont.setItem(slots[n++], new ItemStack(item, lo + Math.floor(Math.random() * (hi - lo + 1)))); } catch (e) { /* */ }
    }
  } catch (e) { /* */ }
}

// ───────────────────────── الشخصيات (حراس، الملك، امرأة ورجل) ─────────────────────────
function postLoc(s, p) { return { x: s.ox + p.x + 0.5, y: s.y0 + p.y, z: s.oz + p.z + 0.5 }; }
function spawnPost(dim, s, p, k) {
  try {
    const loc = postLoc(s, p);
    if (!dim.isChunkLoaded(loc)) return false;
    if (dim.getEntities({ tags: [`sh_post_${k}`], location: loc, maxDistance: 96 }).length) return false;   // ما نكرر
    const e = dim.spawnEntity(CITY_NPC[p.type], loc);
    e.addTag("sh_city"); e.addTag(`sh_post_${k}`);
    return true;
  } catch (e) { return false; }
}
// الحارس اللي مات (وحوش الليل) يجي بداله حارس جديد، بس بعيد عن عين اللاعب (40+ بلوكة) وبعد 3 دقايق
const lost = new Map();
function maintain() {
  const s = load();
  if (!s || s.st !== "built" || !Array.isArray(s.posts)) return;
  const dim = world.getDimension("overworld"), players = world.getAllPlayers().filter((p) => p.dimension.id === "minecraft:overworld");
  if (!players.some((p) => inCity(p.location.x, p.location.z, 96))) return;
  const now = system.currentTick;
  s.posts.forEach(([type, x, y, z], k) => {
    const p = { type, x, y, z };
    const loc = postLoc(s, p);
    if (!dim.isChunkLoaded(loc)) return;
    let have = false;
    try { have = dim.getEntities({ tags: [`sh_post_${k}`], location: loc, maxDistance: 96 }).length > 0; } catch (e) { return; }
    if (have) { lost.delete(k); return; }
    if (!lost.has(k)) { lost.set(k, now); return; }
    if (now - lost.get(k) < 3600) return;
    if (players.some((pl) => Math.hypot(pl.location.x - loc.x, pl.location.z - loc.z) < 40)) return;
    if (spawnPost(dim, s, p, k)) lost.delete(k);
  });
}

// ───────────────────────── كلام الشخصيات ─────────────────────────
const LINES = {
  "sh:aetheria_king": ["Welcome to Aetheria, traveller. These walls have stood for three hundred years.", "My guards keep the streets safe. Beyond the walls, the rifts grow bolder each night.",
    "If you seek strength, the Academy keeps old books on every monster of these lands.", "Rest at the Golden Lantern inn, and trade at the market. Aetheria welcomes the brave."],
  "sh:city_guard": ["Move along, citizen. The streets are safe while we stand watch.", "Monsters? Not inside these walls. Not on my watch.", "The King holds court in the castle at the end of the great avenue.",
    "We patrol the walls day and night. Use the ladders in the towers if you want the view."],
  "sh:townswoman": ["Fresh bread at the bakery this morning! The market opens at dawn.", "Have you seen the pond in the park? The lilies bloom all year.",
    "The tailor's awnings are purple, the baker's orange. You cannot get lost in our market.", "My brother works at the farms by the south gate. Best carrots in the kingdom."],
  "sh:townsman": ["The forge never sleeps. Iron, coal and steel: that is the smith's life.", "Watch the anvil, friend. It bites.",
    "The stables are just past the carpenter's workshop, if you need them.", "I heard there is strange ore deep below the hills. Dawnsteel, they call it."],
};
const talkIdx = new Map();
function talk(p, e) {
  const lines = LINES[e.typeId];
  if (!lines) return;
  const k = `${p.id}:${e.id}`, i = (talkIdx.get(k) || 0) % lines.length;
  talkIdx.set(k, i + 1);
  const who = { "sh:aetheria_king": "King Aldric", "sh:city_guard": "City Guard", "sh:townswoman": "Mira", "sh:townsman": "Tomas" }[e.typeId];
  say(p, `§e${who}: §f${lines[i]}`);
}

// ───────────────────────── التشغيل ─────────────────────────
const welcomed = new Set();
export function setupCity() {
  // البداية بعد دقيقة من فتح العالم وبوجود لاعب، وبعدها كل 10 ثواني نتأكد إن البناء ماشي (يكمل بعد إعادة الفتح)
  system.runTimeout(() => {
    system.runInterval(() => {
      if (job || !world.getAllPlayers().length) return;
      const s = load();
      if (s && s.st === "built") return;
      buildCity();
    }, 200);
  }, 1200);
  system.runInterval(() => { try { maintain(); } catch (e) { /* */ } }, 600);
  // ترحيب أول ما يدخل اللاعب المدينة
  system.runInterval(() => {
    const c = cityInfo();
    if (!c || !c.built) return;
    for (const p of world.getAllPlayers()) {
      if (p.dimension.id !== "minecraft:overworld" || welcomed.has(p.id)) continue;
      if (!inCity(p.location.x, p.location.z, -6)) continue;
      welcomed.add(p.id);
      say(p, "§6[Explore] §fYou reached §eAetheria§f, the royal city.\n§7Guards keep the streets safe. Visit the market, the Academy and the King in the castle.");
      try { p.setDynamicProperty("sh_city_seen", true); } catch (e) { /* */ }
    }
  }, 40);
  world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
    try { if (ev.target && LINES[ev.target.typeId]) talk(ev.player, ev.target); } catch (e) { /* */ }
  });
}
