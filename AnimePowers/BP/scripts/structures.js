// هياكل الاستكشاف: بيوت يابانية، قصر، خرائب معبد. تنبني بالسكربت قرب اللاعب وهو يتحرك.
import { world, system, BlockPermutation, BlockVolume, ItemStack } from "@minecraft/server";

// ───────────────────────── مساعدات الأوامر ─────────────────────────
// op: ["box",x1,y1,z1,x2,y2,z2,id] | ["set",x,y,z,id] | ["stair",x,y,z,id,dir,upside]
//     ["chest",x,y,z,lootKey] | ["mob",x,y,z,typeId] (نقطة ظهور حارس، تسجل ولا تبنى)
const AIR = "minecraft:air";

function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

class Plan {
  constructor(seed) { this.ops = []; this.spawns = []; this.r = rng(seed); }
  box(x1, y1, z1, x2, y2, z2, id) { this.ops.push(["box", x1, y1, z1, x2, y2, z2, id]); }
  set(x, y, z, id) { this.ops.push(["set", x, y, z, id]); }
  stair(x, y, z, id, dir, upside = false) { this.ops.push(["stair", x, y, z, id, dir, upside]); }
  chest(x, y, z, key) { this.ops.push(["chest", x, y, z, key]); }
  mob(x, y, z, type) { this.spawns.push({ x, y, z, type }); }

  // أرضية الموقع: تنظيف الهواء + أساس
  ground(x1, z1, x2, z2, h, surface = "minecraft:grass_block") {
    this.box(x1, -6, z1, x2, -2, z2, "minecraft:dirt");
    this.box(x1, -1, z1, x2, -1, z2, surface);
    this.box(x1, 0, z1, x2, h, z2, AIR);
  }

  // سقف متدرج (hipped) بدرجات متجهة للمركز
  roof(x1, z1, x2, z2, y, layers, stairId, solidId, slabId) {
    for (let k = 0; k < layers; k++) {
      const a = x1 - 1 + k, b = z1 - 1 + k, c = x2 + 1 - k, d = z2 + 1 - k, yy = y + k;
      if (a >= c || b >= d) break;
      this.box(a, yy, b, c, yy, d, solidId);
      this.box(a + 1, yy, b + 1, c - 1, yy, d - 1, solidId);
      for (let x = a + 1; x <= c - 1; x++) {
        this.stair(x, yy, b, stairId, "s"); // الحافة الشمالية: ترتفع نحو الجنوب (المركز)
        this.stair(x, yy, d, stairId, "n");
      }
      for (let z = b + 1; z <= d - 1; z++) {
        this.stair(a, yy, z, stairId, "e");
        this.stair(c, yy, z, stairId, "w");
      }
    }
    const a = x1 + layers - 1, b = z1 + layers - 1, c = x2 - layers + 1, d = z2 - layers + 1;
    if (a <= c && b <= d) this.box(a, y + layers, b, c, y + layers, d, slabId);
  }

  // بيت ياباني: أرضية y=-1، جدران y=0..3، عارضة y=4، سقف من y=5
  house(x1, z1, x2, z2, doorSide, opts = {}) {
    const wall = opts.wall || "minecraft:white_concrete";
    const post = opts.post || "minecraft:dark_oak_log";
    const beam = opts.beam || "minecraft:dark_oak_planks";
    this.box(x1 - 1, -1, z1 - 1, x2 + 1, -1, z2 + 1, "minecraft:stone_bricks");
    this.box(x1, -1, z1, x2, -1, z2, "minecraft:dark_oak_planks");
    this.box(x1, 0, z1, x2, 3, z2, AIR);
    // جدران
    this.box(x1, 0, z1, x2, 3, z1, wall); this.box(x1, 0, z2, x2, 3, z2, wall);
    this.box(x1, 0, z1, x1, 3, z2, wall); this.box(x2, 0, z1, x2, 3, z2, wall);
    // أعمدة
    for (const x of [x1, x2]) for (const z of [z1, z2]) this.box(x, 0, z, x, 3, z, post);
    for (let x = x1 + 3; x < x2; x += 3) { this.box(x, 0, z1, x, 3, z1, post); this.box(x, 0, z2, x, 3, z2, post); }
    for (let z = z1 + 3; z < z2; z += 3) { this.box(x1, 0, z, x1, 3, z, post); this.box(x2, 0, z, x2, 3, z, post); }
    // نوافذ
    for (let x = x1 + 1; x < x2; x++) if ((x - x1) % 3 !== 0) { this.set(x, 1, z1, "minecraft:glass_pane"); this.set(x, 2, z1, "minecraft:glass_pane"); this.set(x, 1, z2, "minecraft:glass_pane"); this.set(x, 2, z2, "minecraft:glass_pane"); }
    for (let z = z1 + 1; z < z2; z++) if ((z - z1) % 3 !== 0) { this.set(x1, 1, z, "minecraft:glass_pane"); this.set(x1, 2, z, "minecraft:glass_pane"); this.set(x2, 1, z, "minecraft:glass_pane"); this.set(x2, 2, z, "minecraft:glass_pane"); }
    // باب (فتحة)
    const cx = Math.floor((x1 + x2) / 2), cz = Math.floor((z1 + z2) / 2);
    if (doorSide === "s") this.box(cx, 0, z2, cx, 2, z2, AIR);
    if (doorSide === "n") this.box(cx, 0, z1, cx, 2, z1, AIR);
    if (doorSide === "e") this.box(x2, 0, cz, x2, 2, cz, AIR);
    if (doorSide === "w") this.box(x1, 0, cz, x1, 2, cz, AIR);
    // عارضة
    this.box(x1 - 1, 4, z1 - 1, x2 + 1, 4, z1 - 1, beam); this.box(x1 - 1, 4, z2 + 1, x2 + 1, 4, z2 + 1, beam);
    this.box(x1 - 1, 4, z1 - 1, x1 - 1, 4, z2 + 1, beam); this.box(x2 + 1, 4, z1 - 1, x2 + 1, 4, z2 + 1, beam);
    this.box(x1, 4, z1, x2, 4, z2, beam);
    // سقف
    this.roof(x1, z1, x2, z2, 5, 3, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:deepslate_tile_slab");
    // داخل: حصير ومائدة وصندوق
    this.box(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:green_carpet");
    this.set(cx, 0, cz, "minecraft:dark_oak_fence");
    this.set(cx, 1, cz, "minecraft:lantern");
    if (opts.loot) this.chest(x1 + 1, 0, z1 + 1, opts.loot);
  }

  stoneLantern(x, z) {
    this.set(x, 0, z, "minecraft:stone_brick_wall");
    this.set(x, 1, z, "minecraft:stone_brick_wall");
    this.set(x, 2, z, "minecraft:lantern");
  }

  torii(cx, z, half, h) {
    this.box(cx - half, 0, z, cx - half, h, z, "minecraft:red_concrete");
    this.box(cx + half, 0, z, cx + half, h, z, "minecraft:red_concrete");
    this.box(cx - half, h - 1, z, cx + half, h - 1, z, "minecraft:red_concrete");
    this.box(cx - half - 1, h + 1, z, cx + half + 1, h + 1, z, "minecraft:black_concrete");
    this.box(cx - half - 2, h + 2, z, cx + half + 2, h + 2, z, "minecraft:black_concrete");
    this.set(cx, h - 2, z, "minecraft:lantern");
  }

  cherry(x, z) {
    this.box(x, 0, z, x, 4, z, "minecraft:cherry_log");
    this.box(x - 2, 3, z - 1, x + 2, 4, z + 1, "minecraft:cherry_leaves");
    this.box(x - 1, 3, z - 2, x + 1, 4, z + 2, "minecraft:cherry_leaves");
    this.box(x - 1, 5, z - 1, x + 1, 5, z + 1, "minecraft:cherry_leaves");
    this.set(x, 3, z, "minecraft:cherry_log");
    this.set(x, 4, z, "minecraft:cherry_log");
  }
}

// ───────────────────────── المخططات ─────────────────────────
export const STRUCTURES = {
  village: { name: "القرية الساكورا", half: 14, weight: 0.3, guards: 0 },
  palace: { name: "قصر الغروب", half: 20, weight: 0.2, guards: 4 },
  ruins: { name: "خرائب المعبد", half: 11, weight: 0.35, guards: 3 },
  shrine: { name: "ضريح السيف المظلم", half: 10, weight: 0.15, guards: 3 },
};

export function planVillage(seed) {
  const P = new Plan(seed);
  P.ground(-14, -13, 14, 13, 14);
  // الطريق الرئيسي + فروع تصل لكل باب بالضبط
  P.box(-1, -1, -13, 1, -1, 13, "minecraft:gravel");
  P.box(-3, -1, -3, -2, -1, -1, "minecraft:gravel");   // بيت 1 (باب شرقي عند z=-2)
  P.box(2, -1, 1, 3, -1, 3, "minecraft:gravel");       // بيت 2 (باب غربي عند z=2)
  P.box(-4, -1, 6, -2, -1, 8, "minecraft:gravel");     // بيت 3 (باب شرقي عند z=7)
  P.torii(0, -12, 3, 5);
  P.stoneLantern(-2, -9); P.stoneLantern(2, -9);
  P.house(-12, -6, -4, 2, "e", { loot: "house" });
  P.house(4, -3, 12, 8, "w", { loot: "house" });
  P.house(-11, 5, -5, 10, "e", { loot: "house" });
  // بئر حجرية
  P.box(6, 0, -10, 8, 0, -8, "minecraft:stone_bricks");
  P.set(7, 0, -9, "minecraft:water");
  for (const [x, z] of [[6, -10], [8, -10], [6, -8], [8, -8]]) { P.box(x, 1, z, x, 2, z, "minecraft:dark_oak_fence"); }
  P.box(6, 3, -10, 8, 3, -8, "minecraft:dark_oak_slab");
  P.stoneLantern(-2, 4); P.stoneLantern(2, 10); P.stoneLantern(-2, 11);
  P.cherry(12, -11); P.cherry(4, 11); P.cherry(-12, -11); P.cherry(13, 11); P.cherry(-13, 1);
  return P;
}

export function planPalace(seed) {
  const P = new Plan(seed);
  P.ground(-20, -20, 20, 20, 26, "minecraft:grass_block");
  // منصة الساحة
  P.box(-18, -1, -18, 18, -1, 18, "minecraft:stone_bricks");
  P.box(-17, -1, -17, 17, -1, 17, "minecraft:polished_andesite");
  P.box(-1, -1, -18, 1, -1, 8, "minecraft:stone_bricks");
  // سور
  for (const [a, b, c, d] of [[-18, -18, 18, -18], [-18, 18, 18, 18], [-18, -18, -18, 18], [18, -18, 18, 18]]) P.box(a, 0, b, c, 1, d, "minecraft:stone_brick_wall");
  P.box(-2, 0, 18, 2, 1, 18, AIR);
  for (const [x, z] of [[-18, -18], [18, -18], [-18, 18], [18, 18]]) { P.box(x, 0, z, x, 2, z, "minecraft:stone_bricks"); P.set(x, 3, z, "minecraft:lantern"); }
  P.torii(0, 19, 3, 5);
  // القاعة الرئيسية (3 طبقات)
  const h = (x1, z1, x2, z2, y0, wallH, pre) => {
    P.box(x1, y0, z1, x2, y0 + wallH, z2, AIR);
    P.box(x1, y0, z1, x2, y0 + wallH, z1, "minecraft:white_concrete"); P.box(x1, y0, z2, x2, y0 + wallH, z2, "minecraft:white_concrete");
    P.box(x1, y0, z1, x1, y0 + wallH, z2, "minecraft:white_concrete"); P.box(x2, y0, z1, x2, y0 + wallH, z2, "minecraft:white_concrete");
    for (const x of [x1, x2]) for (const z of [z1, z2]) P.box(x, y0, z, x, y0 + wallH, z, "minecraft:dark_oak_log");
    for (let x = x1 + 3; x < x2; x += 3) { P.box(x, y0, z1, x, y0 + wallH, z1, "minecraft:dark_oak_log"); P.box(x, y0, z2, x, y0 + wallH, z2, "minecraft:dark_oak_log"); }
    for (let z = z1 + 3; z < z2; z += 3) { P.box(x1, y0, z, x1, y0 + wallH, z, "minecraft:dark_oak_log"); P.box(x2, y0, z, x2, y0 + wallH, z, "minecraft:dark_oak_log"); }
    for (let x = x1 + 1; x < x2; x++) if ((x - x1) % 3 !== 0) for (const z of [z1, z2]) { P.set(x, y0 + 2, z, "minecraft:glass_pane"); P.set(x, y0 + 3, z, "minecraft:glass_pane"); }
    const yb = y0 + wallH + 1;
    P.box(x1 - 1, yb, z1 - 1, x2 + 1, yb, z2 + 1, "minecraft:dark_oak_planks");
    P.roof(x1, z1, x2, z2, yb + 1, 3, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:deepslate_tile_slab");
    return yb + 5;
  };
  const top1 = h(-9, -7, 9, 7, 0, 4, true);
  P.box(-1, 0, 7, 1, 3, 7, AIR); // مدخل
  const top2 = h(-5, -4, 5, 4, top1 - 1, 3, false);
  const top3 = h(-2, -2, 2, 2, top2 - 1, 2, false);
  P.set(0, top3 + 1, 0, "minecraft:lightning_rod");
  // داخل القاعة
  P.box(-1, 0, -6, 1, 0, 6, "minecraft:red_carpet");
  for (const z of [-5, -2, 1, 4]) for (const x of [-5, 5]) { P.box(x, 0, z, x, 3, z, "minecraft:dark_oak_log"); P.set(x, 4, z, "minecraft:lantern"); }
  P.box(-2, 0, -6, 2, 0, -6, "minecraft:gold_block");
  P.stair(0, 1, -6, "minecraft:quartz_stairs", "s");
  P.chest(-7, 0, -6, "palace"); P.chest(7, 0, -6, "palace"); P.chest(0, 0, -4, "palace");
  // ساحة
  P.stoneLantern(-3, 14); P.stoneLantern(3, 14); P.stoneLantern(-3, 10); P.stoneLantern(3, 10);
  P.cherry(-14, 14); P.cherry(14, 14); P.cherry(-14, -14); P.cherry(14, -14);
  P.mob(-6, 0, 12, "sh:rust_guard"); P.mob(6, 0, 12, "sh:rust_guard");
  P.mob(-4, 0, 3, "sh:ember_imp"); P.mob(4, 0, 3, "sh:ember_imp");
  return P;
}

export function planRuins(seed) {
  const P = new Plan(seed);
  const r = P.r;
  P.ground(-11, -11, 11, 11, 9);
  P.box(-9, -1, -9, 9, -1, 9, "minecraft:mossy_stone_bricks");
  for (let x = -9; x <= 9; x++) for (let z = -9; z <= 9; z++) {
    const v = r();
    if (v < 0.22) P.set(x, -1, z, "minecraft:cracked_stone_bricks");
    else if (v < 0.32) P.set(x, -1, z, "minecraft:cobblestone");
  }
  // جدران مكسورة
  for (let i = -9; i <= 9; i++) {
    for (const [x, z] of [[i, -9], [i, 9], [-9, i], [9, i]]) {
      if (r() < 0.35) continue;
      const hgt = 1 + Math.floor(r() * 3);
      P.box(x, 0, z, x, hgt, z, r() < 0.5 ? "minecraft:mossy_stone_bricks" : "minecraft:stone_bricks");
    }
  }
  // أعمدة
  for (const [x, z] of [[-5, -5], [5, -5], [-5, 5], [5, 5]]) {
    const hgt = 2 + Math.floor(r() * 4);
    P.box(x, 0, z, x, hgt, z, "minecraft:mossy_stone_bricks");
    P.set(x, hgt + 1, z, "minecraft:soul_lantern");
  }
  // المذبح
  P.box(-2, 0, -2, 2, 0, 2, "minecraft:stone_bricks");
  P.box(-1, 0, -1, 1, 0, 1, "minecraft:chiseled_stone_bricks");
  P.chest(0, 1, 0, "altar");
  P.set(-1, 1, -1, "minecraft:soul_torch"); P.set(1, 1, 1, "minecraft:soul_torch");
  P.chest(-8, 0, 8, "ruins"); P.chest(8, 0, -8, "ruins"); P.chest(-8, 0, -8, "ruins");
  P.mob(-3, 0, 3, "sh:rust_guard"); P.mob(3, 0, -3, "sh:ember_imp"); P.mob(3, 0, 3, "sh:ember_imp");
  return P;
}

// ضريح السيف المظلم: منصة حجر أسود، بوابة، ودكة بدرجات فيها صندوق كاتانا الهاوية
export function planShrine(seed) {
  const P = new Plan(seed);
  const r = P.r;
  P.ground(-9, -9, 9, 9, 8, "minecraft:coarse_dirt");
  P.box(-8, -1, -8, 8, -1, 8, "minecraft:polished_blackstone_bricks");
  for (let x = -8; x <= 8; x++) for (let z = -8; z <= 8; z++) {
    if (r() < 0.16) P.set(x, -1, z, "minecraft:cracked_polished_blackstone_bricks");
  }
  // ممر من البوابة للدكة بحواف بنفسجية
  P.box(-1, -1, 3, 1, -1, 8, "minecraft:polished_blackstone");
  P.box(-2, -1, 3, -2, -1, 8, "minecraft:purple_concrete");
  P.box(2, -1, 3, 2, -1, 8, "minecraft:purple_concrete");
  // سور واطي مع فتحة البوابة
  for (let i = -8; i <= 8; i++) {
    P.set(i, 0, -8, "minecraft:polished_blackstone_brick_wall");
    P.set(-8, 0, i, "minecraft:polished_blackstone_brick_wall");
    P.set(8, 0, i, "minecraft:polished_blackstone_brick_wall");
    if (Math.abs(i) > 2) P.set(i, 0, 8, "minecraft:polished_blackstone_brick_wall");
  }
  // بوابة (توري) سوداء
  for (const x of [-2, 2]) {
    P.box(x, 0, 8, x, 4, 8, "minecraft:polished_blackstone_bricks");
    P.set(x, 5, 8, "minecraft:polished_blackstone_bricks");
    P.set(x, 6, 8, "minecraft:soul_lantern");
  }
  P.box(-3, 5, 8, 3, 5, 8, "minecraft:polished_blackstone_bricks");
  P.box(-4, 6, 8, 4, 6, 8, "minecraft:polished_blackstone_slab");
  P.set(-2, 6, 8, "minecraft:soul_lantern"); P.set(2, 6, 8, "minecraft:soul_lantern");
  P.box(-1, 4, 8, 1, 4, 8, "minecraft:purple_concrete");
  // دكة بثلاث درجات
  P.box(-3, 0, -3, 3, 0, 3, "minecraft:polished_blackstone_bricks");
  P.box(-2, 1, -2, 2, 1, 2, "minecraft:chiseled_polished_blackstone");
  P.box(-1, 2, -1, 1, 2, 1, "minecraft:crying_obsidian");
  P.chest(0, 3, 0, "shrine");
  // شفرات متوهجة مغروزة حول الصندوق
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) P.box(x, 3, z, x, 4, z, "minecraft:end_rod");
  // أعمدة الأركان بفوانيس
  for (const [x, z] of [[-7, -7], [7, -7], [-7, 7], [7, 7]]) {
    P.box(x, 0, z, x, 3, z, "minecraft:polished_blackstone_brick_wall");
    P.set(x, 4, z, "minecraft:soul_lantern");
  }
  // مواقد
  P.set(-5, 0, 0, "minecraft:soul_campfire"); P.set(5, 0, 0, "minecraft:soul_campfire");
  P.set(-5, 0, -5, "minecraft:soul_torch"); P.set(5, 0, -5, "minecraft:soul_torch");
  P.mob(-4, 0, -4, "sh:shadow_hound"); P.mob(4, 0, -4, "sh:shadow_hound"); P.mob(0, 0, 5, "sh:rust_guard");
  return P;
}

const PLANNERS = { village: planVillage, palace: planPalace, ruins: planRuins, shrine: planShrine };

// ───────────────────────── الغنائم ─────────────────────────
const LOOT = {
  house: [["sh:xp_scroll_small", 1, 2, 1.0], ["sh:monster_book", 1, 1, 0.15], ["sh:explorer_compass", 1, 1, 0.2], ["sh:dawn_dagger", 1, 1, 0.12], ["sh:shadow_blade", 1, 1, 0.08], ["sh:shadow_claws", 1, 1, 0.08], ["minecraft:bread", 2, 5, 0.9], ["minecraft:apple", 1, 3, 0.7], ["minecraft:torch", 4, 8, 0.6]],
  ruins: [["sh:xp_scroll_small", 1, 2, 1.0], ["sh:monster_book", 1, 1, 0.25], ["sh:explorer_compass", 1, 1, 0.3], ["sh:ember_cleaver", 1, 1, 0.15], ["sh:sunset_spear", 1, 1, 0.1], ["minecraft:iron_ingot", 2, 5, 0.7], ["minecraft:cooked_porkchop", 2, 4, 0.6], ["minecraft:torch", 4, 8, 0.5]],
  palace: [["sh:xp_scroll_big", 1, 1, 0.8], ["sh:explorer_compass", 1, 1, 0.5], ["sh:stone_maul", 1, 1, 0.25], ["sh:sunset_spear", 1, 1, 0.25], ["sh:ember_cleaver", 1, 1, 0.25], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.5], ["minecraft:cooked_beef", 4, 8, 0.9], ["minecraft:emerald", 3, 6, 0.8], ["minecraft:iron_ingot", 4, 8, 0.7]],
  shrine: [["sh:dark_katana", 1, 1, 1.0], ["sh:xp_scroll_big", 1, 2, 1.0], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.6], ["minecraft:diamond", 1, 2, 0.5]],
  altar: [["sh:xp_scroll_big", 1, 2, 1.0], ["sh:dawn_dagger", 1, 1, 0.5], ["sh:shadow_blade", 1, 1, 0.5], ["sh:shadow_claws", 1, 1, 0.45], ["sh:stone_maul", 1, 1, 0.4], ["sh:sunset_spear", 1, 1, 0.4], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.8], ["minecraft:diamond", 1, 2, 0.5]],
};

function fillChest(block, key) {
  try {
    const cont = block.getComponent("minecraft:inventory").container;
    const slots = Array.from({ length: cont.size }, (_, i) => i).sort(() => Math.random() - 0.5);
    let n = 0;
    for (const [id, lo, hi, chance] of LOOT[key] || []) {
      if (Math.random() > chance) continue;
      const amt = lo + Math.floor(Math.random() * (hi - lo + 1));
      cont.setItem(slots[n++], new ItemStack(id, amt));
    }
  } catch (e) { /* */ }
}

// ───────────────────────── التنفيذ ─────────────────────────
const SEQ = ["e", "s", "w", "n"];
const DIR_STATE = { e: 0, w: 1, s: 2, n: 3 };

export function rotXZ(x, z, rot) {
  if (rot === 1) return [-z, x];
  if (rot === 2) return [-x, -z];
  if (rot === 3) return [z, -x];
  return [x, z];
}

function* execute(dim, ox, oy, oz, rot, plan, onChest) {
  let count = 0;
  for (const op of plan.ops) {
    try {
      if (op[0] === "box") {
        const [ax, az] = rotXZ(op[1], op[3], rot), [bx, bz] = rotXZ(op[4], op[6], rot);
        const from = { x: ox + Math.min(ax, bx), y: oy + op[2], z: oz + Math.min(az, bz) };
        const to = { x: ox + Math.max(ax, bx), y: oy + op[5], z: oz + Math.max(az, bz) };
        dim.fillBlocks(new BlockVolume(from, to), op[7]);
      } else if (op[0] === "set") {
        const [x, z] = rotXZ(op[1], op[3], rot);
        dim.setBlockType({ x: ox + x, y: oy + op[2], z: oz + z }, op[4]);
      } else if (op[0] === "stair") {
        const [x, z] = rotXZ(op[1], op[3], rot);
        const d = SEQ[(SEQ.indexOf(op[5]) + rot) % 4];
        const perm = BlockPermutation.resolve(op[4], { weirdo_direction: DIR_STATE[d], upside_down_bit: !!op[6] });
        const at = { x: ox + x, y: oy + op[2], z: oz + z };
        if (typeof dim.setBlockPermutation === "function") dim.setBlockPermutation(at, perm);
        else { const blk = dim.getBlock(at); if (blk) blk.setPermutation(perm); }
      } else if (op[0] === "chest") {
        const [x, z] = rotXZ(op[1], op[3], rot);
        const loc = { x: ox + x, y: oy + op[2], z: oz + z };
        dim.setBlockType(loc, "minecraft:chest");
        const b = dim.getBlock(loc);
        if (b) onChest(b, op[4]);
      }
    } catch (e) { /* موضع غير صالح: نكمل */ }
    if (++count % 3 === 0) yield;
  }
}

// ───────────────────────── اختيار الموقع ─────────────────────────
const NATURAL = /grass_block|dirt|sand|stone|snow|gravel|podzol|mycelium|terracotta|moss|mud|clay|coarse|rooted/;

function pickSite(dim, center, minD, maxD, half) {
  for (let tries = 0; tries < 8; tries++) {
    const a = Math.random() * Math.PI * 2;
    const d = minD + Math.random() * (maxD - minD);
    const cx = Math.floor(center.x + Math.cos(a) * d), cz = Math.floor(center.z + Math.sin(a) * d);
    const pts = [[0, 0], [half * 0.7, 0], [-half * 0.7, 0], [0, half * 0.7], [0, -half * 0.7], [half * 0.7, half * 0.7], [-half * 0.7, -half * 0.7], [half * 0.7, -half * 0.7], [-half * 0.7, half * 0.7]];
    const corners = [[half, half], [-half, half], [half, -half], [-half, -half]];
    let ok = true;
    for (const [dx, dz] of corners) {
      if (!dim.isChunkLoaded({ x: cx + dx, y: 64, z: cz + dz })) { ok = false; break; }
    }
    if (!ok) continue;
    const hs = [];
    for (const [dx, dz] of pts) {
      const top = dim.getTopmostBlock({ x: Math.floor(cx + dx), z: Math.floor(cz + dz) });
      if (!top || !NATURAL.test(top.typeId) || /water|lava|ice/.test(top.typeId)) { ok = false; break; }
      hs.push(top.y);
    }
    if (!ok) continue;
    const mx = Math.max(...hs), mn = Math.min(...hs);
    if (mx - mn > 4) continue;
    hs.sort((p, q) => p - q);
    return { x: cx, y: hs[Math.floor(hs.length / 2)] + 1, z: cz };
  }
  return undefined;
}

// ───────────────────────── السجل والتشغيل ─────────────────────────
function loadReg() {
  try {
    const raw = world.getDynamicProperty("sh_structs");
    if (typeof raw === "string") return JSON.parse(raw);
  } catch (e) { /* */ }
  return [];
}
function saveReg(r) {
  try { world.setDynamicProperty("sh_structs", JSON.stringify(r)); } catch (e) { /* */ }
}

let building = false;
const announced = new Set();

// الضريح نادر وسيفه مهم، فإذا بُنيت 3 بنايات بدون ضريح نضمنه بالجاية (حتى ما يقعد اللاعب يدور عليه للأبد)
const SHRINE_PITY = 3;
function chooseType(reg = []) {
  if (STRUCTURES.shrine && !reg.some((s) => s.type === "shrine") && reg.length >= SHRINE_PITY) return "shrine";
  const roll = Math.random();
  let acc = 0;
  for (const [k, v] of Object.entries(STRUCTURES)) { acc += v.weight; if (roll < acc) return k; }
  return "village";
}

export function setupStructures() {
  // بناء هيكل جديد قرب اللاعب (بعيد عن الهياكل الموجودة)
  system.runInterval(() => {
    if (building) return;
    for (const p of world.getAllPlayers()) {
      try {
        if (p.dimension.id !== "minecraft:overworld") continue;
        if (Math.random() > 0.5) continue;
        const reg = loadReg();
        const type = chooseType(reg);
        const spec = STRUCTURES[type];
        const site = pickSite(p.dimension, p.location, 56, 100, spec.half);
        if (!site) continue;
        if (reg.some((s) => Math.hypot(s.x - site.x, s.z - site.z) < 220)) continue;
        const seed = Math.floor(Math.random() * 1e9);
        const rot = Math.floor(Math.random() * 4);
        const plan = PLANNERS[type](seed);
        reg.push({ x: site.x, y: site.y, z: site.z, type, rot, seed });
        saveReg(reg);
        building = true;
        const gen = execute(p.dimension, site.x, site.y, site.z, rot, plan, fillChest);
        const job = system.runJob((function* () { try { yield* gen; } finally { building = false; } })());
        return;
      } catch (e) { building = false; }
    }
  }, 1200);

  // كشف الموقع + إعادة ظهور الحراس
  system.runInterval(() => {
    const reg = loadReg();
    for (const p of world.getAllPlayers()) {
      if (p.dimension.id !== "minecraft:overworld") continue;
      for (let i = 0; i < reg.length; i++) {
        const s = reg[i];
        const d = Math.hypot(s.x - p.location.x, s.z - p.location.z);
        const key = `${p.id}:${i}`;
        if (d < 30 && !announced.has(key)) {
          announced.add(key);
          try { p.sendMessage(`§6[استكشاف] §fوصلت لـ ${STRUCTURES[s.type].name}`); } catch (e) { /* */ }
        }
        if (d < 40 && STRUCTURES[s.type].guards > 0) {
          try {
            const plan = PLANNERS[s.type](s.seed);
            const near = p.dimension.getEntities({ location: { x: s.x, y: s.y, z: s.z }, maxDistance: 24, families: ["sh_rank0"] });
            if (near.length >= STRUCTURES[s.type].guards) continue;
            for (const sp of plan.spawns) {
              if (near.length >= STRUCTURES[s.type].guards) break;
              const [x, z] = rotXZ(sp.x, sp.z, s.rot);
              const loc = { x: s.x + x + 0.5, y: s.y + sp.y, z: s.z + z + 0.5 };
              if (!p.dimension.isChunkLoaded(loc)) continue;
              const e = p.dimension.spawnEntity(sp.type, loc);
              near.push(e);
            }
          } catch (e) { /* */ }
        }
      }
    }
  }, 400);
}
