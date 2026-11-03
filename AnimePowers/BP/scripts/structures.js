// هياكل الاستكشاف: بيوت يابانية، قصر، خرائب معبد. تنبني بالسكربت قرب اللاعب وهو يتحرك.
import { world, system, BlockPermutation, BlockVolume, ItemStack } from "@minecraft/server";
import { buildSakuraVillage, SAKURA_HALF } from "./sakura.js";
import { buildLightShrine, buildDarkShrine, SHRINE_HALF } from "./shrines.js";

// ───────────────────────── مساعدات الأوامر ─────────────────────────
// op: ["box",x1,y1,z1,x2,y2,z2,id] | ["set",x,y,z,id] | ["stair",x,y,z,id,dir,upside] | ["perm",x,y,z,id,states]
//     ["chest",x,y,z,lootKey] | ["mob",x,y,z,typeId] (نقطة ظهور حارس، تسجل ولا تبنى)
// الإحداثيات محلية: y=0 أول بلوك فوق الأرض، y=-1 سطح الأرض، x شرق، z جنوب (تدور عشوائياً عند البناء).
// العمارة مأخوذة من اليابان التقليدية: توري، توْرو (فوانيس حجر)، إنغاوا (شرفة)، سقف إيريموية، تشوزويا (حوض التطهير)،
// حديقة كاريسانسوي، باغودا بسقوف متراكبة، خندق وأبراج قلعة، وأشجار الساكورا.
const AIR = "minecraft:air";
const WATER = "minecraft:water";

function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

class Plan {
  constructor(seed) { this.ops = []; this.spawns = []; this.r = rng(seed); this.occ = new Set(); }
  // خلايا محجوزة (أبنية، مسارات، ماء): الزهور والأشجار تتجنبها
  reserve(x1, z1, x2, z2) { for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) for (let z = Math.min(z1, z2); z <= Math.max(z1, z2); z++) this.occ.add(`${x},${z}`); }
  free(x, z) { return !this.occ.has(`${x},${z}`); }
  // سرير: القدم (fx,y,fz) والراس (hx,y,hz). التنفيذ يجرب اتجاهات الحالة حتى يثبت الزوج
  bed(fx, y, fz, hx, hz) { this.ops.push(["bed", fx, y, fz, hx, hz]); }
  box(x1, y1, z1, x2, y2, z2, id) { this.ops.push(["box", x1, y1, z1, x2, y2, z2, id]); }
  set(x, y, z, id) { this.ops.push(["set", x, y, z, id]); }
  stair(x, y, z, id, dir, upside = false) { this.ops.push(["stair", x, y, z, id, dir, upside]); }
  perm(x, y, z, id, states) { this.ops.push(["perm", x, y, z, id, states]); }
  chest(x, y, z, key) { this.ops.push(["chest", x, y, z, key]); }
  mob(x, y, z, type) { this.spawns.push({ x, y, z, type }); }
  // موقع صندوق الجائزة: ما ينبني وقت البناء، بس يظهر لما يموت الحراس (إسم مفتاح الغنائم)
  reward(x, y, z, key) { this.rewardAt = { x, y, z, key }; }
  hang(x, y, z, id = "minecraft:lantern") { this.perm(x, y, z, id, { hanging: true }); }

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

  // حلقة سقف واحدة تبرز بلوكة للخارج (للباغودا والأبراج)
  eave(x1, z1, x2, z2, y, stairId, slabId) {
    const a = x1 - 1, b = z1 - 1, c = x2 + 1, d = z2 + 1;
    this.box(a, y, b, c, y, d, slabId);
    for (let x = a + 1; x <= c - 1; x++) { this.stair(x, y, b, stairId, "s"); this.stair(x, y, d, stairId, "n"); }
    for (let z = b + 1; z <= d - 1; z++) { this.stair(a, y, z, stairId, "e"); this.stair(c, y, z, stairId, "w"); }
    this.box(a + 1, y + 1, b + 1, c - 1, y + 1, d - 1, slabId);
  }

  // بيت ياباني: أرضية y=-1، جدران y=0..3، عارضة y=4، سقف من y=5. opts: wall, post, beam, loot, roof
  house(x1, z1, x2, z2, doorSide, opts = {}) {
    const wall = opts.wall || "minecraft:white_concrete";
    const post = opts.post || "minecraft:dark_oak_log";
    const beam = opts.beam || "minecraft:dark_oak_planks";
    const roof = opts.roof || ["minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:deepslate_tile_slab"];
    this.box(x1 - 1, -1, z1 - 1, x2 + 1, -1, z2 + 1, "minecraft:stone_bricks");
    this.box(x1, -1, z1, x2, -1, z2, "minecraft:dark_oak_planks");
    this.box(x1, 0, z1, x2, 3, z2, AIR);
    // جدران + أعمدة
    this.box(x1, 0, z1, x2, 3, z1, wall); this.box(x1, 0, z2, x2, 3, z2, wall);
    this.box(x1, 0, z1, x1, 3, z2, wall); this.box(x2, 0, z1, x2, 3, z2, wall);
    for (const x of [x1, x2]) for (const z of [z1, z2]) this.box(x, 0, z, x, 3, z, post);
    for (let x = x1 + 3; x < x2; x += 3) { this.box(x, 0, z1, x, 3, z1, post); this.box(x, 0, z2, x, 3, z2, post); }
    for (let z = z1 + 3; z < z2; z += 3) { this.box(x1, 0, z, x1, 3, z, post); this.box(x2, 0, z, x2, 3, z, post); }
    // شوجي: نوافذ ورقية بيضاء
    const shoji = "minecraft:white_stained_glass_pane";
    for (let x = x1 + 1; x < x2; x++) if ((x - x1) % 3 !== 0) for (const z of [z1, z2]) { this.set(x, 1, z, shoji); this.set(x, 2, z, shoji); }
    for (let z = z1 + 1; z < z2; z++) if ((z - z1) % 3 !== 0) for (const x of [x1, x2]) { this.set(x, 1, z, shoji); this.set(x, 2, z, shoji); }
    // باب + إنغاوا (شرفة خشبية) + درجات حجر
    const cx = Math.floor((x1 + x2) / 2), cz = Math.floor((z1 + z2) / 2);
    if (doorSide === "s") { this.box(cx, 0, z2, cx, 2, z2, AIR); this.engawaZ(x1, x2, z2 + 1, 1); }
    if (doorSide === "n") { this.box(cx, 0, z1, cx, 2, z1, AIR); this.engawaZ(x1, x2, z1 - 1, -1); }
    if (doorSide === "e") { this.box(x2, 0, cz, x2, 2, cz, AIR); this.engawaX(z1, z2, x2 + 1, 1); }
    if (doorSide === "w") { this.box(x1, 0, cz, x1, 2, cz, AIR); this.engawaX(z1, z2, x1 - 1, -1); }
    // عارضة
    this.box(x1 - 1, 4, z1 - 1, x2 + 1, 4, z1 - 1, beam); this.box(x1 - 1, 4, z2 + 1, x2 + 1, 4, z2 + 1, beam);
    this.box(x1 - 1, 4, z1 - 1, x1 - 1, 4, z2 + 1, beam); this.box(x2 + 1, 4, z1 - 1, x2 + 1, 4, z2 + 1, beam);
    this.box(x1, 4, z1, x2, 4, z2, beam);
    // سقف إيريموية مبسط: طبقتان مائلتان + قمة
    this.roof(x1, z1, x2, z2, 5, 3, roof[0], roof[1], roof[2]);
    // داخل: تاتامي (سجاد أخضر بإطار)، طاولة منخفضة، فانوس معلق
    this.box(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:green_carpet");
    this.set(cx, 0, cz, "minecraft:dark_oak_fence");
    this.set(cx, 1, cz, "minecraft:dark_oak_pressure_plate");
    this.hang(cx, 3, cz);
    if (opts.loot) this.chest(x1 + 1, 0, z1 + 1, opts.loot);
  }
  // شرفة على محور X (باب شرقي/غربي): d=+1 شرق، -1 غرب
  engawaX(z1, z2, x, d) {
    this.box(x, -1, z1, x + d, -1, z2, "minecraft:dark_oak_planks");
    const xo = x + d;
    this.box(xo, 0, z1, xo, 0, z2, "minecraft:dark_oak_fence");
    this.box(x, 0, z1, xo, 0, z1, "minecraft:dark_oak_fence"); this.box(x, 0, z2, xo, 0, z2, "minecraft:dark_oak_fence");
    const cz = Math.floor((z1 + z2) / 2);
    this.box(xo, 0, cz - 1, xo, 0, cz + 1, AIR);
    this.stair(xo + d, -1, cz, "minecraft:stone_brick_stairs", d > 0 ? "w" : "e");
  }
  engawaZ(x1, x2, z, d) {
    this.box(x1, -1, z, x2, -1, z + d, "minecraft:dark_oak_planks");
    const zo = z + d;
    this.box(x1, 0, zo, x2, 0, zo, "minecraft:dark_oak_fence");
    this.box(x1, 0, z, x1, 0, zo, "minecraft:dark_oak_fence"); this.box(x2, 0, z, x2, 0, zo, "minecraft:dark_oak_fence");
    const cx = Math.floor((x1 + x2) / 2);
    this.box(cx - 1, 0, zo, cx + 1, 0, zo, AIR);
    this.stair(cx, -1, zo + d, "minecraft:stone_brick_stairs", d > 0 ? "n" : "s");
  }

  // توْرو: فانوس حجري (قاعدة، عمود، فانوس، غطاء)
  toro(x, z) {
    this.set(x, 0, z, "minecraft:stone_bricks");
    this.set(x, 1, z, "minecraft:stone_brick_wall");
    this.set(x, 2, z, "minecraft:lantern");
    this.set(x, 3, z, "minecraft:stone_brick_slab");
  }
  stoneLantern(x, z) { this.toro(x, z); }

  // توري: عمودان أحمران، عارضة سفلية، كاساغي أسود علوي بنهايات مرفوعة
  torii(cx, z, half, h, black = false) {
    const light = black === "light";
    const col = light ? "minecraft:white_concrete" : black ? "minecraft:polished_blackstone_bricks" : "minecraft:red_concrete";
    const top = light ? "minecraft:gold_block" : black ? "minecraft:polished_blackstone_bricks" : "minecraft:black_concrete";
    const slab = light ? "minecraft:quartz_block" : black ? "minecraft:polished_blackstone_brick_slab" : "minecraft:black_concrete";
    this.box(cx - half, 0, z, cx - half, h, z, col);
    this.box(cx + half, 0, z, cx + half, h, z, col);
    this.set(cx - half, 0, z, "minecraft:stone_bricks"); this.set(cx + half, 0, z, "minecraft:stone_bricks");
    this.box(cx - half, h - 2, z, cx + half, h - 2, z, col);
    this.box(cx - half - 1, h + 1, z, cx + half + 1, h + 1, z, top);
    this.box(cx - half - 2, h + 2, z, cx + half + 2, h + 2, z, slab);
    this.set(cx - half - 3, h + 3, z, slab); this.set(cx + half + 3, h + 3, z, slab);
    this.hang(cx, h - 3, z, black && !light ? "minecraft:soul_lantern" : "minecraft:lantern");
  }

  // شجرة ساكورا: جذع مائل بفروع وتاج مدوّر وبتلات على الأرض
  cherry(x, z, h = 6) {
    const L = "minecraft:cherry_leaves";
    const disc = (y, r) => {
      this.box(x - r, y, z - r + 1, x + r, y, z + r - 1, L);
      this.box(x - r + 1, y, z - r, x + r - 1, y, z + r, L);
    };
    disc(h - 2, 3); disc(h - 1, 3); disc(h, 2); this.box(x - 1, h + 1, z - 1, x + 1, h + 1, z + 1, L);
    disc(h - 3, 2);
    this.box(x - 1, h - 4, z - 1, x + 1, h - 4, z + 1, L);
    this.box(x, 0, z, x, h, z, "minecraft:cherry_log");
    this.set(x + 1, h - 2, z, "minecraft:cherry_log"); this.set(x - 1, h - 3, z, "minecraft:cherry_log");
    for (const [dx, dz] of [[2, 1], [-2, 2], [1, -3], [-3, -1], [3, -2], [0, 3]]) {
      if (this.r() < 0.8) this.set(x + dx, 0, z + dz, "minecraft:pink_petals");
    }
  }

  // تشوزويا: حوض ماء للتطهير تحت مظلة
  chozuya(cx, cz) {
    this.box(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, "minecraft:stone_bricks");
    this.set(cx, 0, cz, WATER);
    for (const [dx, dz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) this.box(cx + dx, 1, cz + dz, cx + dx, 2, cz + dz, "minecraft:dark_oak_fence");
    this.box(cx - 1, 3, cz - 1, cx + 1, 3, cz + 1, "minecraft:dark_oak_slab");
    this.set(cx, 1, cz - 1, "minecraft:bamboo_block");
    this.hang(cx, 2, cz);
  }

  // بركة كوي بحافة حجر وزنابق ماء
  pond(x1, z1, x2, z2) {
    this.box(x1, -1, z1, x2, -1, z2, "minecraft:mossy_cobblestone");
    this.box(x1 + 1, -2, z1 + 1, x2 - 1, -1, z2 - 1, WATER);
    for (let i = 0; i < Math.floor(((x2 - x1) * (z2 - z1)) / 9); i++) {
      this.set(x1 + 2 + Math.floor(this.r() * (x2 - x1 - 3)), 0, z1 + 2 + Math.floor(this.r() * (z2 - z1 - 3)), "minecraft:waterlily");
    }
  }
  // جسر خشبي بدرابزين أحمر على محور X
  bridgeX(x1, x2, z) {
    this.box(x1, 0, z - 1, x2, 0, z + 1, "minecraft:dark_oak_planks");
    this.box(x1, 1, z - 1, x2, 1, z - 1, "minecraft:dark_oak_fence"); this.box(x1, 1, z + 1, x2, 1, z + 1, "minecraft:dark_oak_fence");
    for (const x of [x1, x2]) for (const dz of [-1, 1]) { this.box(x, 1, z + dz, x, 2, z + dz, "minecraft:red_concrete"); this.set(x, 3, z + dz, "minecraft:lantern"); }
    this.stair(x1 - 1, 0, z, "minecraft:stone_brick_stairs", "e");
    this.stair(x2 + 1, 0, z, "minecraft:stone_brick_stairs", "w");
  }
  // كاريسانسوي: حديقة حصى مخططة بأحجار
  karesansui(x1, z1, x2, z2) {
    for (let x = x1; x <= x2; x++) this.box(x, -1, z1, x, -1, z2, x % 2 === 0 ? "minecraft:gravel" : "minecraft:light_gray_concrete_powder");
    this.box(x1 - 1, -1, z1 - 1, x2 + 1, -1, z1 - 1, "minecraft:stone_bricks"); this.box(x1 - 1, -1, z2 + 1, x2 + 1, -1, z2 + 1, "minecraft:stone_bricks");
    this.box(x1 - 1, -1, z1, x1 - 1, -1, z2, "minecraft:stone_bricks"); this.box(x2 + 1, -1, z1, x2 + 1, -1, z2, "minecraft:stone_bricks");
    for (let i = 0; i < 3; i++) {
      const x = x1 + 1 + Math.floor(this.r() * (x2 - x1 - 1)), z = z1 + 1 + Math.floor(this.r() * (z2 - z1 - 1));
      this.set(x, 0, z, "minecraft:andesite"); if (this.r() < 0.6) this.set(x + 1, 0, z, "minecraft:cobblestone"); this.set(x, 1, z, "minecraft:moss_carpet");
    }
  }
  // كشك سوق بمظلة مخططة
  stall(x1, z1, x2, z2) {
    for (const x of [x1, x2]) for (const z of [z1, z2]) this.box(x, 0, z, x, 2, z, "minecraft:dark_oak_fence");
    for (let x = x1; x <= x2; x++) this.box(x, 3, z1, x, 3, z2, x % 2 === 0 ? "minecraft:red_wool" : "minecraft:white_wool");
    this.box(x1 + 1, 0, z2, x2 - 1, 0, z2, "minecraft:barrel");
    this.set(x1 + 1, 1, z2, "minecraft:melon_block"); this.set(x2 - 1, 1, z2, "minecraft:pumpkin");
    this.set(Math.floor((x1 + x2) / 2), 0, z1 + 1, "minecraft:hay_block");
  }
  // باغودا متعددة الطبقات
  pagoda(cx, cz, half, tiers) {
    this.box(cx - half - 1, -1, cz - half - 1, cx + half + 1, 0, cz + half + 1, "minecraft:stone_bricks");
    let y = 1;
    for (let t = 0; t < tiers; t++) {
      const s = half - t;
      this.box(cx - s, y, cz - s, cx + s, y + 2, cz + s, AIR);
      this.box(cx - s, y, cz - s, cx + s, y + 2, cz - s, "minecraft:white_concrete"); this.box(cx - s, y, cz + s, cx + s, y + 2, cz + s, "minecraft:white_concrete");
      this.box(cx - s, y, cz - s, cx - s, y + 2, cz + s, "minecraft:white_concrete"); this.box(cx + s, y, cz - s, cx + s, y + 2, cz + s, "minecraft:white_concrete");
      for (const dx of [-s, s]) for (const dz of [-s, s]) this.box(cx + dx, y, cz + dz, cx + dx, y + 2, cz + dz, "minecraft:dark_oak_log");
      for (const [dx, dz] of [[0, -s], [0, s], [-s, 0], [s, 0]]) { this.set(cx + dx, y + 1, cz + dz, "minecraft:white_stained_glass_pane"); }
      this.eave(cx - s, cz - s, cx + s, cz + s, y + 3, "minecraft:red_nether_brick_stairs", "minecraft:red_nether_brick_slab");
      y += 4;
    }
    this.box(cx, y, cz, cx, y + 3, cz, "minecraft:iron_bars");
    this.set(cx, y + 4, cz, "minecraft:gold_block");
    this.box(cx, 1, cz - half, cx, 2, cz - half, AIR);       // مدخل
    this.stair(cx, 0, cz - half - 2, "minecraft:stone_brick_stairs", "s");
    this.chest(cx, 1, cz, "ruins_small");
  }
  // برج قلعة صغير (ياغورا)
  tower(x1, z1, x2, z2) {
    this.box(x1, 0, z1, x2, 5, z2, AIR);
    this.box(x1, 0, z1, x2, 5, z1, "minecraft:white_concrete"); this.box(x1, 0, z2, x2, 5, z2, "minecraft:white_concrete");
    this.box(x1, 0, z1, x1, 5, z2, "minecraft:white_concrete"); this.box(x2, 0, z1, x2, 5, z2, "minecraft:white_concrete");
    for (const x of [x1, x2]) for (const z of [z1, z2]) this.box(x, 0, z, x, 5, z, "minecraft:dark_oak_log");
    const cx = Math.floor((x1 + x2) / 2), cz = Math.floor((z1 + z2) / 2);
    for (const [x, z] of [[cx, z1], [cx, z2], [x1, cz], [x2, cz]]) { this.set(x, 2, z, "minecraft:white_stained_glass_pane"); this.set(x, 3, z, "minecraft:white_stained_glass_pane"); }
    this.box(x1 - 1, 6, z1 - 1, x2 + 1, 6, z2 + 1, "minecraft:dark_oak_planks");
    this.roof(x1, z1, x2, z2, 7, 2, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:deepslate_tile_slab");
    this.set(cx, 10, cz, "minecraft:gold_block");
    this.hang(cx, 5, cz);
  }
}

// ───────────────────────── المخططات ─────────────────────────
export const STRUCTURES = {
  temple: { name: "Star Temple", weight: 0, half: 12, guards: 0, lore: "The fallen star's heart rests in this crystal. Step on the golden plate to awaken your power." },
  village: { name: "Sakura Village", half: SAKURA_HALF, weight: 0.3, guards: 0, lore: "The Order of Dawn's first home, where the story began." },
  palace: { name: "Sunset Palace", half: 26, weight: 0.2, guards: 4, lore: "The last light fell here before the palace fell." },
  ruins: { name: "Temple Ruins", half: 14, weight: 0.35, guards: 3, lore: "The ancient temple, where the first shard landed." },
  shrine: { name: "Dark Sword Shrine", half: SHRINE_HALF, weight: 0.15, guards: 0, bosses: ["sh:gloomhorn", "sh:hollow_seer"], unique: true, lore: "The Abyss sleeps beneath this stone. Defeat its two guardians to break the seal." },
  tower: { name: "Abyss Tower", half: 11, weight: 0.3, guards: 0, tower: true, lore: "Seven floors of black stone and violet light. Every floor holds the Abyss's spawn, and the strongest waits at the top." },
  lightshrine: { name: "Light Sword Shrine", half: SHRINE_HALF, weight: 0.12, guards: 0, bosses: ["sh:veilfox", "sh:magmamoth"], unique: true, lore: "The light the Abyss could never swallow sleeps beneath this beam. Defeat its two guardians to break the seal." },
};

// قرية الساكورا (77×77) من صورة المرجع: التفاصيل بـ sakura.js
export function planVillage(seed) {
  const P = new Plan(seed);
  buildSakuraVillage(P);
  return P;
}

// قصر الغروب: خندق ماء، جسر، سور بأبراج ياغورا، 3 طبقات، حدائق حصى، توري
export function planPalace(seed) {
  const P = new Plan(seed);
  P.ground(-26, -26, 26, 26, 28);
  // منصة الساحة
  P.box(-18, -1, -18, 18, -1, 18, "minecraft:stone_bricks");
  P.box(-17, -1, -17, 17, -1, 17, "minecraft:polished_andesite");
  P.box(-1, -1, -18, 1, -1, 18, "minecraft:stone_bricks");
  // خندق ماء (عرض 3) حول المنصة + جسر عند البوابة الجنوبية
  P.box(-21, -2, -21, 21, -1, -19, WATER); P.box(-21, -2, 19, 21, -1, 21, WATER);
  P.box(-21, -2, -18, -19, -1, 18, WATER); P.box(19, -2, -18, 21, -1, 18, WATER);
  P.box(-2, -1, 19, 2, -1, 21, "minecraft:dark_oak_planks");
  for (const z of [19, 21]) for (const x of [-2, 2]) { P.box(x, 0, z, x, 1, z, "minecraft:red_concrete"); P.set(x, 2, z, "minecraft:lantern"); }
  P.box(-2, 0, 20, -2, 0, 20, "minecraft:dark_oak_fence"); P.box(2, 0, 20, 2, 0, 20, "minecraft:dark_oak_fence");
  // سور
  for (const [a, b, c, d] of [[-18, -18, 18, -18], [-18, 18, 18, 18], [-18, -18, -18, 18], [18, -18, 18, 18]]) P.box(a, 0, b, c, 1, d, "minecraft:stone_brick_wall");
  P.box(-2, 0, 18, 2, 1, 18, AIR);
  // أبراج الأركان (ياغورا)
  P.tower(-18, -18, -14, -14); P.tower(14, -18, 18, -14); P.tower(-18, 14, -14, 18); P.tower(14, 14, 18, 18);
  P.torii(0, 24, 3, 6);
  P.box(-1, -1, 22, 1, -1, 23, "minecraft:grass_path");
  // القاعة الرئيسية (3 طبقات)
  const h = (x1, z1, x2, z2, y0, wallH) => {
    P.box(x1, y0, z1, x2, y0 + wallH, z2, AIR);
    P.box(x1, y0, z1, x2, y0 + wallH, z1, "minecraft:white_concrete"); P.box(x1, y0, z2, x2, y0 + wallH, z2, "minecraft:white_concrete");
    P.box(x1, y0, z1, x1, y0 + wallH, z2, "minecraft:white_concrete"); P.box(x2, y0, z1, x2, y0 + wallH, z2, "minecraft:white_concrete");
    for (const x of [x1, x2]) for (const z of [z1, z2]) P.box(x, y0, z, x, y0 + wallH, z, "minecraft:dark_oak_log");
    for (let x = x1 + 3; x < x2; x += 3) { P.box(x, y0, z1, x, y0 + wallH, z1, "minecraft:dark_oak_log"); P.box(x, y0, z2, x, y0 + wallH, z2, "minecraft:dark_oak_log"); }
    for (let z = z1 + 3; z < z2; z += 3) { P.box(x1, y0, z, x1, y0 + wallH, z, "minecraft:dark_oak_log"); P.box(x2, y0, z, x2, y0 + wallH, z, "minecraft:dark_oak_log"); }
    for (let x = x1 + 1; x < x2; x++) if ((x - x1) % 3 !== 0) for (const z of [z1, z2]) { P.set(x, y0 + 2, z, "minecraft:white_stained_glass_pane"); P.set(x, y0 + 3, z, "minecraft:white_stained_glass_pane"); }
    const yb = y0 + wallH + 1;
    P.box(x1 - 1, yb, z1 - 1, x2 + 1, yb, z2 + 1, "minecraft:dark_oak_planks");
    P.roof(x1, z1, x2, z2, yb + 1, 3, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:deepslate_tile_slab");
    return yb + 5;
  };
  const top1 = h(-9, -7, 9, 7, 0, 4);
  P.box(-1, 0, 7, 1, 3, 7, AIR); // مدخل
  const top2 = h(-5, -4, 5, 4, top1 - 1, 3);
  const top3 = h(-2, -2, 2, 2, top2 - 1, 2);
  P.set(0, top3 + 1, 0, "minecraft:lightning_rod");
  P.set(-1, top3 - 1, -1, "minecraft:gold_block"); P.set(1, top3 - 1, 1, "minecraft:gold_block");
  // داخل القاعة
  P.box(-1, 0, -6, 1, 0, 6, "minecraft:red_carpet");
  for (const z of [-5, -2, 1, 4]) for (const x of [-5, 5]) { P.box(x, 0, z, x, 3, z, "minecraft:dark_oak_log"); P.hang(x, 3, z); }
  P.box(-2, 0, -6, 2, 0, -6, "minecraft:gold_block");
  P.stair(0, 1, -6, "minecraft:quartz_stairs", "s");
  P.chest(-7, 0, -6, "palace"); P.chest(7, 0, -6, "palace"); P.chest(0, 0, -4, "palace");
  // ساحة: حدائق حصى جانبية + فوانيس + أشجار
  P.karesansui(-15, 9, -5, 15); P.karesansui(5, 9, 15, 15);
  for (const z of [10, 14]) { P.toro(-3, z); P.toro(3, z); }
  for (const [x, z] of [[-14, 0], [14, 0], [-14, -12], [14, -12], [-23, -4], [23, -4], [-23, 12], [23, 12]]) P.cherry(x, z);
  P.mob(-6, 0, 12, "sh:rust_guard"); P.mob(6, 0, 12, "sh:rust_guard");
  P.mob(-4, 0, 3, "sh:ember_imp"); P.mob(4, 0, 3, "sh:ember_imp");
  return P;
}

// خرائب المعبد: منصة مكسورة، توري مهدم، باغودا متهدمة، أحجار طحلبية، مذبح
// خرائب المعبد v2: قاعة معبد قديمة متهدمة ومغطاة بالطحلب (بدل غابة الأعمدة العشوائية القديمة).
// قاعدة حجرية بطبقتين (حجر مكسور ومطحلب)، درج من كل الجهات (بعضه ناقص)، صفين أعمدة منتظمة (بعضها كامل بعارضة، بعضها مكسور، وواحد ساقط على الأرض)،
// بقايا سقف بلاط فوق الصف اليسار، جدار خلفي مسنن بنافذة، بقايا جدران جانبية منخفضة، دكة وسطى بحافة منقوشة ومذبح، توري مهدم بالمدخل،
// شجرة أزالية قديمة نابتة من الزاوية، أكوام حطام، أعشاب وطحلب وبيوت عنكبوت. كل البلوكات أسماء Bedrock حقيقية.
export function planRuins(seed) {
  const P = new Plan(seed);
  const r = P.r;
  const pick = (opts) => { let v = r(), acc = 0; for (const [p, id] of opts) { acc += p; if (v < acc) return id; } return opts[opts.length - 1][1]; };
  const FLOOR = [[0.48, "minecraft:stone_bricks"], [0.22, "minecraft:mossy_stone_bricks"], [0.18, "minecraft:cracked_stone_bricks"], [0.07, "minecraft:mossy_cobblestone"], [0.05, "minecraft:moss_block"]];
  const SHAFT = [[0.5, "minecraft:stone_bricks"], [0.3, "minecraft:mossy_stone_bricks"], [0.2, "minecraft:cracked_stone_bricks"]];
  const floor = (x1, z1, x2, z2, y, opts = FLOOR) => { for (let x = x1; x <= x2; x++) for (let z = z1; z <= z2; z++) P.set(x, y, z, pick(opts)); };
  P.ground(-14, -14, 14, 14, 12);
  // 1) القاعدة: ساحة خارجية (y=-1) ومنصة داخلية مرفوعة بلوكة (y=0) بحافة درج من كل الجهات، بعض الدرجات ناقصة
  floor(-12, -12, 12, 12, -1);
  floor(-9, -9, 9, 9, 0, [[0.42, "minecraft:stone_bricks"], [0.2, "minecraft:cracked_stone_bricks"], [0.2, "minecraft:mossy_stone_bricks"], [0.18, "minecraft:polished_andesite"]]);
  for (let k = -9; k <= 9; k++) {
    if (Math.abs(k) <= 2 || r() < 0.7) P.stair(k, 0, 10, "minecraft:stone_brick_stairs", "n");
    if (r() < 0.55) P.stair(k, 0, -10, "minecraft:mossy_stone_brick_stairs", "s");
    if (r() < 0.55) P.stair(-10, 0, k, "minecraft:stone_brick_stairs", "e");
    if (r() < 0.55) P.stair(10, 0, k, "minecraft:mossy_stone_brick_stairs", "w");
  }
  // 2) الدكة الوسطى بحافة حجر منقوش، ودرج لها من الجنوب
  P.box(-3, 1, -4, 3, 1, 2, "minecraft:polished_andesite");
  for (let x = -3; x <= 3; x++) { P.set(x, 1, -4, "minecraft:chiseled_stone_bricks"); P.set(x, 1, 2, "minecraft:chiseled_stone_bricks"); }
  for (let z = -4; z <= 2; z++) { P.set(-3, 1, z, "minecraft:chiseled_stone_bricks"); P.set(3, 1, z, "minecraft:chiseled_stone_bricks"); }
  for (const x of [-1, 0, 1]) P.stair(x, 1, 3, "minecraft:stone_brick_stairs", "n");
  // 3) صفين أعمدة منتظمة (x = ±6): كامل بتاج وعارضة، مكسور، وواحد ساقط على الأرض
  const column = (x, z, h) => {
    P.set(x, 1, z, "minecraft:chiseled_stone_bricks");
    if (h > 1) P.box(x, 2, z, x, h, z, "minecraft:stone_bricks");
    for (let y = 2; y <= h; y++) P.set(x, y, z, pick(SHAFT));
    if (h >= 6) P.set(x, h + 1, z, "minecraft:chiseled_stone_bricks");
    else if (h >= 2 && r() < 0.6) P.set(x, h + 1, z, "minecraft:stone_brick_slab");
  };
  const LEFT = [[-7, 7], [-3, 7], [1, 3], [5, 2]], RIGHT = [[-7, 7], [-3, 5], [1, 7], [5, 1]];
  for (const [z, h] of LEFT) column(-6, z, h);
  for (const [z, h] of RIGHT) column(6, z, h);
  P.box(-6, 9, -7, -6, 9, -3, "minecraft:stone_bricks");                 // عارضة فوق عمودين كاملين باليسار
  P.box(6, 9, -7, 6, 9, -5, "minecraft:cracked_stone_bricks");           // عارضة مكسورة باليمين
  for (let z = 6; z <= 9; z++) P.set(6, 1, z, z === 9 ? "minecraft:chiseled_stone_bricks" : pick(SHAFT));   // العمود الساقط ممدود على الأرض
  // بقايا السقف: بلاط ديبسليت فوق الصف اليسار بحافة مكسورة، وبلاطات طايحة بالأرض
  for (let x = -9; x <= -3; x++) for (let z = -9; z <= -1; z++) {
    if (x === -9 || z === -1 || z === -9) { if (r() < 0.55) P.set(x, 10, z, "minecraft:deepslate_tile_slab"); }
    else if (r() < 0.82) P.set(x, 10, z, "minecraft:deepslate_tiles");
  }
  for (let i = 0; i < 9; i++) P.set(-8 + Math.floor(r() * 7), 1, -1 + Math.floor(r() * 5), r() < 0.5 ? "minecraft:deepslate_tile_slab" : "minecraft:cobbled_deepslate_slab");
  // 4) الجدار الخلفي (z=-11): قطع متصلة (كل قطعة 2-4 بلوكات بنفس الارتفاع) تنزل للأطراف، بفجوتين، ونافذة بالنص بإطار منقوش
  for (let x = -11; x <= 11;) {
    const run = 2 + Math.floor(r() * 3), base = 6 - Math.floor(Math.abs(x + run / 2) / 2.4);
    const hgt = Math.max(0, base + (r() < 0.35 ? -1 : 0));
    for (let k = 0; k < run && x <= 11; k++, x++) {
      if (x === -8 || x === 9) continue;
      for (let y = 0; y <= hgt; y++) P.set(x, y, -11, pick(SHAFT));
      if (hgt >= 2 && r() < 0.25) P.set(x, hgt + 1, -11, "minecraft:stone_brick_slab");
    }
  }
  P.box(-1, 3, -11, 1, 4, -11, AIR);
  for (const x of [-2, 2]) for (const y of [3, 4]) P.set(x, y, -11, "minecraft:chiseled_stone_bricks");
  P.stair(-1, 5, -11, "minecraft:stone_brick_stairs", "e", true); P.stair(1, 5, -11, "minecraft:stone_brick_stairs", "w", true);
  // 5) بقايا الجدران الجانبية (x=±11): قطع جدار متصلة (3-6 بلوكات، ارتفاع 1-2) بفجوات 1-3، ودعامات زوايا أعلى
  for (const x of [-11, 11]) {
    for (let z = -10; z <= 10;) {
      const run = 3 + Math.floor(r() * 4), hgt = 1 + Math.floor(r() * 2);
      for (let k = 0; k < run && z <= 10; k++, z++) for (let y = 0; y <= hgt - (k === run - 1 && r() < 0.5 ? 1 : 0); y++) P.set(x, y, z, pick(SHAFT));
      z += 1 + Math.floor(r() * 3);
    }
  }
  for (const [x, z] of [[-11, -11], [11, -11], [-11, 11], [11, 11]]) { P.box(x, 0, z, x, 4, z, "minecraft:stone_bricks"); P.set(x, 5, z, "minecraft:chiseled_stone_bricks"); }
  // 6) توري مهدم بالمدخل (z=12): عمود قائم، والثاني ساقط بالعشب، والعارضة مكسورة
  P.box(-3, 0, 12, -3, 5, 12, "minecraft:red_concrete");
  P.set(-3, 0, 12, "minecraft:stone_bricks");
  P.box(-4, 6, 12, -1, 6, 12, "minecraft:black_concrete");
  P.set(3, 0, 12, "minecraft:stone_bricks");
  P.box(4, 0, 13, 7, 0, 13, "minecraft:red_concrete");
  P.set(1, 0, 13, "minecraft:black_concrete");
  // 7) المذبح على الدكة: قاعدة منقوشة، صندوق، فوانيس روح، وفانوسين حجر على جانبي الدرج
  P.box(-1, 2, -2, 1, 2, -2, "minecraft:chiseled_stone_bricks");
  P.chest(0, 3, -2, "altar");
  P.set(-1, 3, -2, "minecraft:soul_lantern"); P.set(1, 3, -2, "minecraft:soul_lantern");
  P.set(-2, 2, 1, "minecraft:soul_lantern"); P.set(2, 2, 1, "minecraft:soul_lantern");
  for (const x of [-4, 4]) { P.set(x, 0, 6, "minecraft:stone_bricks"); P.set(x, 1, 6, "minecraft:stone_brick_wall"); P.set(x, 2, 6, "minecraft:lantern"); P.set(x, 3, 6, "minecraft:stone_brick_slab"); }
  // 8) شجرة أزالية قديمة نابتة من الزاوية الشمالية الغربية (جذع بلوط غامق وأوراق أزالية مزهرة)
  P.box(-10, -1, -9, -10, 6, -9, "minecraft:dark_oak_log");
  P.set(-9, 4, -9, "minecraft:dark_oak_log"); P.set(-10, 5, -8, "minecraft:dark_oak_log");
  for (const [y, rr] of [[5, 2], [6, 3], [7, 2], [8, 1]]) for (let dx = -rr; dx <= rr; dx++) for (let dz = -rr; dz <= rr; dz++) {
    if (Math.abs(dx) + Math.abs(dz) > rr + 1 || (dx === 0 && dz === 0 && y < 7)) continue;
    P.perm(-10 + dx, y, -9 + dz, r() < 0.3 ? "minecraft:azalea_leaves_flowered" : "minecraft:azalea_leaves", { persistent_bit: true });   // أوراق ثابتة ما تذبل
  }
  // 9) حطام ونباتات: أكوام حجر وحصى، طحلب، أعشاب، أزاليا صغيرة، وبيوت عنكبوت بين الأعمدة
  for (let i = 0; i < 7; i++) {
    const x = -12 + Math.floor(r() * 25), z = -12 + Math.floor(r() * 25);
    if (Math.abs(x) <= 9 && Math.abs(z) <= 9) continue;
    P.set(x, 0, z, pick([[0.4, "minecraft:mossy_cobblestone"], [0.35, "minecraft:cobblestone"], [0.25, "minecraft:gravel"]]));
    if (r() < 0.5) P.set(x + (r() < 0.5 ? 1 : -1), 0, z, "minecraft:stone_brick_slab");
  }
  for (let i = 0; i < 34; i++) {
    const x = -12 + Math.floor(r() * 25), z = -12 + Math.floor(r() * 25);
    const onPlat = Math.abs(x) <= 9 && Math.abs(z) <= 9, y = onPlat ? 1 : 0;
    if (onPlat && Math.abs(x) <= 3 && z >= -4 && z <= 3) continue;
    if (Math.abs(x) === 6) continue;
    P.set(x, y, z, pick([[0.45, "minecraft:moss_carpet"], [0.25, "minecraft:short_grass"], [0.15, "minecraft:fern"], [0.15, "minecraft:azalea"]]));
  }
  for (const [x, y, z] of [[-6, 6, -5], [6, 4, -5], [-6, 4, 3], [-5, 2, -8], [5, 7, 0]]) P.set(x, y, z, "minecraft:web");
  P.chest(-8, 1, 7, "ruins"); P.chest(8, 1, -8, "ruins"); P.chest(-7, 1, -8, "ruins");
  P.mob(-3, 1, 5, "sh:rust_guard"); P.mob(3, 1, -6, "sh:ember_imp"); P.mob(4, 1, 6, "sh:ember_imp");
  return P;
}

// ضريحا السيف: ساحتا قتال 45×45 مفتوحتان للسما (التفاصيل بـ shrines.js). بدون صناديق: الصندوق يظهر لما يموت الحارسان.
export function planShrine(seed) { const P = new Plan(seed); buildDarkShrine(P); return P; }
export function planLightShrine(seed) { const P = new Plan(seed); buildLightShrine(P); return P; }

// ───────────────────────── معبد النجمة: مكان سحب القدرة ─────────────────────────
// قاعة 15×15 بارتفاع 6 فوق منصة حجرية: أرضية مصقولة، ممر للمركز بين قناتي ماء، أعمدة بفوانيس معلقة وأماثيست،
// فتحة سماوية فوق البلورة، وبالنص لوحة ضغط ذهبية فوقها بلورة كبيرة (كيان 3D) يتغير لونها حسب ندرة القدرة.
// معبد النجمة الكبير (31×31 + ساحة قدام): قاعة 23×23 بعلو 8، شرفة بأعمدة حواليها، سقف ياباني بسبع طبقات،
// شبابيك بألوان الندرات الست (أبيض، أخضر، أزرق، بنفسجي، ذهبي، أحمر)، خندق ماء مضيء حول البلورة بأربع جسور،
// أعمدة أميثست بالزوايا، مكتبة ومذبح بالصدر، وفتحة سماوية فوق البلورة. المدخل جنوب (+z) ويتوجه للاعب وقت البناء.
export function planTemple(seed) {
  const P = new Plan(seed);
  P.ground(-17, -17, 17, 21, 18, "minecraft:grass_block");
  // القاعدة والشرفة
  P.box(-14, -1, -14, 14, -1, 14, "minecraft:stone_bricks");
  P.box(-13, 0, -13, 13, 0, 13, "minecraft:polished_deepslate");
  P.box(-14, 0, -14, 14, 0, -14, "minecraft:stone_brick_slab"); P.box(-14, 0, 14, 14, 0, 14, "minecraft:stone_brick_slab");
  P.box(-14, 0, -14, -14, 0, 14, "minecraft:stone_brick_slab"); P.box(14, 0, -14, 14, 0, 14, "minecraft:stone_brick_slab");
  for (let x = -3; x <= 3; x++) { P.stair(x, 0, 14, "minecraft:stone_brick_stairs", "n"); P.stair(x, -1, 15, "minecraft:stone_brick_stairs", "n"); }
  P.box(-3, -1, 16, 3, -1, 21, "minecraft:polished_andesite");
  P.box(-1, -1, 16, 1, -1, 21, "minecraft:smooth_quartz");
  // أعمدة الشرفة
  for (const k of [-12, -8, -4, 0, 4, 8, 12]) {
    for (const w of [-13, 13]) {
      if (!(w === 13 && Math.abs(k) < 4)) P.box(k, 1, w, k, 8, w, "minecraft:dark_oak_log");
      P.box(w, 1, k, w, 8, k, "minecraft:dark_oak_log");
    }
  }
  P.box(-13, 8, -13, 13, 8, -13, "minecraft:dark_oak_planks"); P.box(-13, 8, 13, 13, 8, 13, "minecraft:dark_oak_planks");
  P.box(-13, 8, -13, -13, 8, 13, "minecraft:dark_oak_planks"); P.box(13, 8, -13, 13, 8, 13, "minecraft:dark_oak_planks");
  // الأرضية الداخلية: كوارتز بخطوط شعاعية غامقة
  P.box(-10, 0, -10, 10, 0, 10, "minecraft:smooth_quartz");
  for (let k = -10; k <= 10; k++) { P.set(k, 0, k, "minecraft:polished_deepslate"); P.set(k, 0, -k, "minecraft:polished_deepslate"); }
  P.box(-1, 0, 7, 1, 0, 13, "minecraft:quartz_bricks");
  // جدران القاعة: كوارتز أبيض بأعمدة بلوط غامق، وشبابيك بألوان الندرات
  P.box(-11, 1, -11, 11, 8, -11, "minecraft:smooth_quartz"); P.box(-11, 1, 11, 11, 8, 11, "minecraft:smooth_quartz");
  P.box(-11, 1, -11, -11, 8, 11, "minecraft:smooth_quartz"); P.box(11, 1, -11, 11, 8, 11, "minecraft:smooth_quartz");
  const cols = [-11, -8, -4, 0, 4, 8, 11];
  for (const v of cols) for (const w of [-11, 11]) { P.box(v, 1, w, v, 8, w, "minecraft:dark_oak_log"); P.box(w, 1, v, w, 8, v, "minecraft:dark_oak_log"); }
  const glass = ["white", "lime", "light_blue", "purple", "yellow", "red"].map((c) => `minecraft:${c}_stained_glass_pane`);
  const gaps = [[-10, -9], [-7, -5], [-3, -1], [1, 3], [5, 7], [9, 10]];
  gaps.forEach(([g1, g2], i) => {
    P.box(-11, 2, g1, -11, 6, g2, glass[i]); P.box(11, 2, -g2, 11, 6, -g1, glass[i]);
    P.box(g1, 2, -11, g2, 6, -11, glass[i]);
    if (i === 0 || i === 1 || i === 4 || i === 5) P.box(g1, 2, 11, g2, 6, 11, glass[i]);
  });
  P.box(-11, 8, -11, 11, 8, 11, "minecraft:dark_oak_planks");
  // المدخل: قوس عريض
  P.box(-2, 1, 11, 2, 5, 11, AIR);
  P.box(-3, 6, 11, 3, 6, 11, "minecraft:dark_oak_planks");
  P.stair(-2, 5, 11, "minecraft:dark_oak_stairs", "e", true); P.stair(2, 5, 11, "minecraft:dark_oak_stairs", "w", true);
  P.hang(0, 5, 12, "minecraft:soul_lantern");
  // الخندق المضيء حول الدكة بأربع جسور
  for (let x = -7; x <= 7; x++) {
    for (let z = -7; z <= 7; z++) {
      const r = Math.hypot(x, z);
      if (r < 4.6 || r > 6.4) continue;
      if (Math.abs(x) <= 1 || Math.abs(z) <= 1) { P.set(x, 0, z, "minecraft:quartz_bricks"); continue; }
      P.set(x, 0, z, WATER); P.set(x, -1, z, "minecraft:sea_lantern");
    }
  }
  for (let a = 0; a < 32; a++) {
    const ang = (a / 32) * Math.PI * 2, x = Math.round(Math.cos(ang) * 7), z = Math.round(Math.sin(ang) * 7);
    if (Math.abs(x) > 1 && Math.abs(z) > 1) P.set(x, 0, z, "minecraft:chiseled_quartz_block");
  }
  // الدكة: أماثيست بالنص ولوحة ذهبية فوقه، وحوله طوب أسود وأعمدة صغيرة بقضبان نور
  P.box(-2, 0, -2, 2, 0, 2, "minecraft:polished_blackstone_bricks");
  P.box(-1, 0, -1, 1, 0, 1, "minecraft:chiseled_polished_blackstone");
  P.set(0, 0, 0, "minecraft:amethyst_block");
  P.set(0, 1, 0, "minecraft:light_weighted_pressure_plate");
  for (const [x, z] of [[-2, -2], [2, -2], [-2, 2], [2, 2]]) { P.set(x, 1, z, "minecraft:polished_blackstone_brick_wall"); P.perm(x, 2, z, "minecraft:end_rod", { facing_direction: 1 }); }
  for (const [x, z] of [[0, -2], [0, 2], [-2, 0], [2, 0]]) P.set(x, 1, z, "minecraft:polished_blackstone_brick_slab");
  // جيود أميثست صغيرة بالزوايا (كانت أعمدة أميثست بطول 7 تغطي القاعة): قاعدة كالسايت وبازلت مثل الجيود الطبيعي،
  // قلب أميثست بطول بلوكتين، وعناقيد وبراعم طالعة من فوق وجوانب
  for (const [x, z] of [[-8, -8], [8, -8], [-8, 8], [8, 8]]) {
    const sx = Math.sign(x), sz = Math.sign(z);
    P.set(x, 1, z, "minecraft:amethyst_block"); P.set(x, 2, z, "minecraft:budding_amethyst");
    P.set(x + sx, 1, z, "minecraft:calcite"); P.set(x, 1, z + sz, "minecraft:calcite"); P.set(x + sx, 1, z + sz, "minecraft:smooth_basalt");
    P.set(x + sx, 2, z + sz, "minecraft:amethyst_block");
    P.perm(x, 3, z, "minecraft:amethyst_cluster", { "minecraft:block_face": "up" });
    P.perm(x + sx, 3, z + sz, "minecraft:large_amethyst_bud", { "minecraft:block_face": "up" });
    P.perm(x - sx, 1, z, "minecraft:medium_amethyst_bud", { "minecraft:block_face": "up" }); P.perm(x, 1, z - sz, "minecraft:small_amethyst_bud", { "minecraft:block_face": "up" });
    P.perm(x + sx, 2, z, "minecraft:amethyst_cluster", { "minecraft:block_face": "up" }); P.perm(x, 2, z + sz, "minecraft:large_amethyst_bud", { "minecraft:block_face": "up" });
    P.hang(x - sx, 7, z - sz, "minecraft:soul_lantern");
  }
  // فوانيس معلقة بسلاسل بحلقة حول البلورة
  for (let a = 0; a < 8; a++) {
    const ang = (a / 8) * Math.PI * 2 + Math.PI / 8, x = Math.round(Math.cos(ang) * 6), z = Math.round(Math.sin(ang) * 6);
    P.set(x, 7, z, "minecraft:iron_chain"); P.hang(x, 6, z, a % 2 ? "minecraft:soul_lantern" : "minecraft:lantern");
  }
  // صدر القاعة (شمال): مذبح بطاولة سحر ومنابر ورفوف كتب وشموع وسجاد بنفسجي
  P.box(-6, 0, -10, 6, 0, -9, "minecraft:polished_blackstone_bricks");
  P.box(-6, 1, -10, 6, 1, -9, "minecraft:purple_carpet");
  P.set(0, 1, -10, "minecraft:enchanting_table");
  P.set(-2, 1, -10, "minecraft:lectern"); P.set(2, 1, -10, "minecraft:lectern");
  for (const x of [-4, -1, 1, 4]) P.perm(x, 1, -9, "minecraft:purple_candle", { candles: 3, lit: true });
  P.box(-10, 1, -10, -7, 4, -10, "minecraft:bookshelf"); P.box(7, 1, -10, 10, 4, -10, "minecraft:bookshelf");
  // جوانب: رفوف كتب تحت الشبابيك وأصص زهور
  for (const w of [-10, 10]) { P.box(w, 1, -6, w, 1, 6, "minecraft:bookshelf"); for (const z of [-6, -2, 2, 6]) P.set(w, 2, z, "minecraft:flower_pot"); }
  for (const [x, z] of [[-10, 10], [10, 10]]) { P.set(x, 1, z, "minecraft:azalea_leaves"); P.set(x, 2, z, "minecraft:azalea_leaves_flowered"); }
  // السقف بطبقتين (مثل المعابد اليابانية): طبقة سفلية عريضة، حلقة أعمدة خشب وزجاج بنفسجي، وطبقة علوية،
  // وزوايا مرفوعة بفوانيس معلقة تحتها، وفتحة سماوية زجاج فوق البلورة، وتاج فانوس ذهبي
  const RS = "minecraft:deepslate_tile_stairs", RT = "minecraft:deepslate_tiles", RH = "minecraft:deepslate_tile_slab";
  P.roof(-13, -13, 13, 13, 9, 3, RS, RT, RH);
  P.box(-11, 9, -11, 11, 9, 11, "minecraft:dark_oak_planks");
  for (let k = -9; k <= 9; k++) for (const w of [-9, 9]) {
    for (const [x, z] of [[k, w], [w, k]]) {
      const post = Math.abs(k) === 9 || k % 3 === 0;
      P.set(x, 12, z, post ? "minecraft:dark_oak_log" : "minecraft:dark_oak_planks");
      P.set(x, 13, z, post ? "minecraft:dark_oak_log" : "minecraft:purple_stained_glass_pane");
    }
  }
  P.roof(-9, -9, 9, 9, 14, 5, RS, RT, RH);
  P.box(-9, 14, -9, 9, 14, 9, "minecraft:dark_oak_planks");
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    P.set(sx * 15, 10, sz * 15, RT); P.hang(sx * 15, 9, sz * 15, "minecraft:lantern");          // زوايا الطبقة السفلية المرفوعة
    P.set(sx * 11, 15, sz * 11, RT); P.hang(sx * 11, 14, sz * 11, "minecraft:soul_lantern");    // زوايا الطبقة العلوية
  }
  P.box(-1, 8, -1, 1, 20, 1, AIR);
  P.box(-1, 9, -1, 1, 19, 1, "minecraft:light_blue_stained_glass");
  P.eave(-2, -2, 2, 2, 20, RS, RH);
  P.box(-1, 22, -1, 1, 22, 1, "minecraft:gold_block");
  P.set(0, 23, 0, "minecraft:lightning_rod");
  // الساحة القدامية: توري، فوانيس حجر، ساكورا
  P.torii(0, 19, 4, 6);
  for (const x of [-5, 5]) { P.toro(x, 17); P.toro(x, 21); }
  for (const [x, z] of [[-15, -15], [15, -15], [-15, 17], [15, 17]]) P.cherry(x, z, 6);
  return P;
}


// ───────────────────────── برج الهاوية (7 طوابق، أسود وبنفسجي) ─────────────────────────
// برج مثمن (15×15) من طابوق البلاكستون المصقول بأحزمة أميثيست عند كل طابق، دعامات أوبسيديان بالزوايا الثمانية،
// شبابيك زجاج بنفسجي، فوانيس أرواح معلقة، درج حلزوني (يتبدل جهة كل طابق)، ونقش أرضي بنفسجي بكل طابق.
// الطوابق 1-3: وحوش Lowly بالعدد، 4-6: أقوى (Grim مع Lowly)، 7: وحش أو اثنين من الرتب العالية؛ موتهم يطلّع صندوق الجائزة بالنص.
export const TOWER_FH = 7, TOWER_FLOORS = 7;
const tw = (z) => Math.min(7, 10 - Math.abs(z));          // نص عرض الصف (الحافة الخارجية للمثمن)
const twi = (z) => Math.min(6, 9 - Math.abs(z));          // نص عرض الداخل
export function planTower(seed) {
  const P = new Plan(seed), FH = TOWER_FH, TOP = FH * TOWER_FLOORS - 1;   // TOP = 48: السطح
  const BR = "minecraft:polished_blackstone_bricks", AM = "minecraft:amethyst_block", OB = "minecraft:obsidian", CO = "minecraft:crying_obsidian";
  P.ground(-11, -11, 11, 11, 12, "minecraft:blackstone");
  for (let z = -8; z <= 8; z++) { const w = Math.min(8, 11 - Math.abs(z)); P.box(-w, -1, z, w, 0, z, "minecraft:polished_blackstone"); }   // قاعدة أعرض
  for (let z = -7; z <= 7; z++) P.box(-tw(z), 0, z, tw(z), TOP, z, BR);                      // جسم البرج
  // أحزمة أميثيست خارجية عند خط كل طابق والسطح
  for (let k = 1; k <= TOWER_FLOORS; k++) { const y = k * FH - 1; for (let z = -7; z <= 7; z++) P.box(-tw(z), y, z, tw(z), y, z, AM); }
  // تآكل: طابوق مشقق وذهب أسود متناثر على الوجه الخارجي
  for (let i = 0; i < 70; i++) {
    const z = Math.floor(P.r() * 15) - 7, sx = P.r() < 0.5 ? -1 : 1, y = 1 + Math.floor(P.r() * (TOP - 2));
    if (y % FH === FH - 1) continue;
    P.set(sx * tw(z), y, z, P.r() < 0.15 ? "minecraft:gilded_blackstone" : "minecraft:cracked_polished_blackstone_bricks");
  }
  P.towerFloors = [];
  for (let k = 0; k < TOWER_FLOORS; k++) {
    const y0 = k * FH;
    for (let z = -6; z <= 6; z++) {
      P.box(-twi(z), y0 - 1, z, twi(z), y0 - 1, z, "minecraft:deepslate_tiles");                  // أرضية
      P.box(-twi(z), y0, z, twi(z), y0 + FH - 2, z, AIR);                                         // الفراغ
    }
    // نقش أرضي: نص كرسي بلاكستون منقوش، صليب أميثيست، وزوايا أوبسيديان باكي (الطابق السابع: حلقة كاملة)
    P.set(0, y0 - 1, 0, "minecraft:chiseled_polished_blackstone");
    for (const [x, z] of [[2, 0], [-2, 0], [0, 2], [0, -2]]) P.set(x, y0 - 1, z, AM);
    for (const [x, z] of [[2, 2], [-2, 2], [2, -2], [-2, -2]]) P.set(x, y0 - 1, z, k === TOWER_FLOORS - 1 ? CO : "minecraft:polished_blackstone");
    if (k === TOWER_FLOORS - 1) for (const [x, z] of [[3, 0], [-3, 0], [0, 3], [0, -3], [1, 3], [-1, 3], [1, -3], [-1, -3], [3, 1], [3, -1], [-3, 1], [-3, -1]]) P.set(x, y0 - 1, z, "minecraft:purpur_block");
    // فوانيس أرواح معلقة بالسقف
    for (const [x, z] of [[3, 3], [-3, 3], [3, -3], [-3, -3]]) P.perm(x, y0 + FH - 2, z, "minecraft:soul_lantern", { hanging: true });
    // شبابيك: زجاج بنفسجي بالجهات الأربعة، وشقوق زجاج أسود بالجهات المايلة
    for (const [x, z] of [[7, 0], [-7, 0], [0, -7], [0, 7]]) {
      if (k === 0 && z === 7) continue;                                                            // المدخل
      for (let y = y0 + 1; y <= y0 + 3; y++) P.set(x, y, z, "minecraft:purple_stained_glass_pane");
    }
    for (const [x, z] of [[5, 5], [-5, 5], [5, -5], [-5, -5]]) for (let y = y0 + 2; y <= y0 + 3; y++) P.set(x, y, z, "minecraft:black_stained_glass_pane");
    // شموع بنفسجية بزوايا الطابق
    for (const [x, z] of [[-4, 4], [4, -4]]) P.perm(x, y0, z, "minecraft:purple_candle", { candles: 2, lit: true });
    P.towerFloors.push({ y: y0, pts: [[3, 0], [-3, 0], [0, 3], [0, -3], [2, 2], [-2, -2], [2, -2], [-2, 2]] });
  }
  // الدرج بحلقة ثانية بعد ما تنبني كل الطوابق (حتى أرضية الطابق الجاي ما تسد الفتحة والدرجة الأخيرة)
  for (let k = 0; k < TOWER_FLOORS - 1; k++) {
    const y0 = k * FH;
    // الدرج للطابق الجاي (7 درجات = ارتفاع الطابق): الزوجي على الجدار الشرقي يصعد شمالاً، والفردي على الغربي يصعد جنوباً.
    // آخر درجة بمستوى أرضية الطابق الجاي، وفوق الدرجتين 4 و5 فتحة بالأرضية للراس، وسياج حول الفتحة فوق
    {
      const east = k % 2 === 0, xs = east ? [5, 6] : [-6, -5], dir = east ? "n" : "s", sz = east ? -1 : 1;
      for (let i = 0; i < FH; i++) {
        const z = (east ? 3 : -3) + sz * i;
        for (const x of xs) {
          if (i > 0) P.box(x, y0, z, x, y0 + i - 1, z, BR);
          P.stair(x, y0 + i, z, "minecraft:polished_blackstone_brick_stairs", dir);
        }
      }
      const h1 = (east ? 3 : -3) + sz * 4, h2 = (east ? 3 : -3) + sz * 5;
      P.box(xs[0], y0 + FH - 1, Math.min(h1, h2), xs[1], y0 + FH - 1, Math.max(h1, h2), AIR);    // فتحة الراس
      const rx = east ? 4 : -4;
      for (const z of [h1, h2]) P.set(rx, y0 + FH, z, "minecraft:polished_blackstone_brick_wall");
      for (const x of xs) P.set(x, y0 + FH, (east ? 3 : -3) + sz * 3, "minecraft:polished_blackstone_brick_wall");
    }
  }
  // المدخل (جنوب +z): فتحة 3×3 بإطار بربر وعتبة بلاكستون منقوش، وممر ومشاعل أرواح
  P.box(-1, 0, 6, 1, 2, 7, AIR);
  for (const x of [-2, 2]) P.box(x, 0, 8, x, 3, 8, "minecraft:purpur_pillar");
  P.box(-2, 4, 8, 2, 4, 8, "minecraft:chiseled_polished_blackstone");
  P.set(0, 5, 8, CO);
  P.box(-1, -1, 8, 1, -1, 11, "minecraft:polished_blackstone_bricks");
  for (const x of [-3, 3]) { P.set(x, 0, 11, "minecraft:blackstone_wall"); P.set(x, 1, 11, "minecraft:soul_lantern"); }
  // دعامات أوبسيديان بالزوايا الثمانية، بخطوط أوبسيديان باكي، وتاج بربر وعنقود أميثيست
  for (const [x, z] of [[8, 3], [8, -3], [-8, 3], [-8, -3], [3, 8], [-3, 8], [3, -8], [-3, -8]]) {
    P.box(x, -1, z, x, TOP + 2, z, OB);
    for (let y = 3; y < TOP; y += 9 + Math.floor(P.r() * 5)) P.box(x, y, z, x, y + 1, z, CO);
    P.set(x, TOP + 3, z, "minecraft:purpur_pillar");
    P.perm(x, TOP + 4, z, "minecraft:amethyst_cluster", { "minecraft:block_face": "up" });
  }
  // السطح: شرفات حول الحافة وبرج بلوري بالنص (أوبسيديان ← بربر ← أميثيست ← أوبسيديان باكي ← قضيب إندر يضوي)
  for (let z = -7; z <= 7; z++) {
    const w = tw(z);
    if (Math.abs(z) === 7) { for (let x = -w; x <= w; x += 2) P.set(x, TOP + 1, z, "minecraft:polished_blackstone_brick_wall"); }
    else if ((z + 7) % 2 === 0) { P.set(w, TOP + 1, z, "minecraft:polished_blackstone_brick_wall"); P.set(-w, TOP + 1, z, "minecraft:polished_blackstone_brick_wall"); }
  }
  P.box(-2, TOP + 1, -2, 2, TOP + 2, 2, OB);
  P.box(-1, TOP + 3, -1, 1, TOP + 5, 1, "minecraft:purpur_block");
  for (const [x, z] of [[2, 2], [-2, 2], [2, -2], [-2, -2]]) P.perm(x, TOP + 3, z, "minecraft:amethyst_cluster", { "minecraft:block_face": "up" });
  P.set(0, TOP + 6, 0, AM); P.set(0, TOP + 7, 0, AM); P.set(0, TOP + 8, 0, CO);
  P.perm(0, TOP + 9, 0, "minecraft:end_rod", { facing_direction: 1 });
  P.reward(0, (TOWER_FLOORS - 1) * FH, 0, "tower");
  return P;
}

const PLANNERS = { tower: planTower, village: planVillage, palace: planPalace, ruins: planRuins, shrine: planShrine, temple: planTemple, lightshrine: planLightShrine };
// يرجع أقرب معبد مسجل (أو لا شي)
export function findTemple(pos, maxD = 1e9) {
  let best, bd = maxD;
  for (const s of loadReg()) {
    if (s.type !== "temple") continue;
    const d = Math.hypot(s.x - pos.x, s.z - pos.z);
    if (d < bd) { bd = d; best = s; }
  }
  return best;
}
// يبني المعبد مرة وحدة بالعالم، قريب من اللاعب (المدخل على بعد ~6-12 بلوكة) ومتوجه له
export const TEMPLE_HALF = 18;
export function buildTemple(p, onDone) {
  const dim = p.dimension;
  const reg0 = loadReg();
  const free = (st) => st && !reg0.some((r) => Math.hypot(r.x - st.x, r.z - st.z) < 55);
  let site;
  for (let i = 0; i < 6 && !site; i++) { const st = pickSite(dim, p.location, 22, i < 3 ? 27 : 36, i < 3 ? TEMPLE_HALF : TEMPLE_HALF - 2); if (free(st)) site = st; }
  if (!site) {
    const v = p.getViewDirection(), l = Math.hypot(v.x, v.z) || 1;
    const x = Math.floor(p.location.x + (v.x / l) * 24), z = Math.floor(p.location.z + (v.z / l) * 24);
    let y = Math.floor(p.location.y);
    try { const top = dim.getTopmostBlock({ x, z }); if (top) y = top.y + 1; } catch (e) { /* */ }
    site = { x, y, z };
  }
  // المدخل (+z بالخطة) يتوجه للاعب: rot0 = +z، rot1 = -x، rot2 = -z، rot3 = +x
  const dx = p.location.x - site.x, dz = p.location.z - site.z;
  const rot = Math.abs(dz) >= Math.abs(dx) ? (dz > 0 ? 0 : 2) : (dx < 0 ? 1 : 3);
  const reg = loadReg();
  const seed = Math.floor(Math.random() * 1e9);
  const rec = { x: site.x, y: site.y, z: site.z, type: "temple", rot, seed };
  reg.push(rec);
  saveReg(reg);
  try { world.setDynamicProperty("sh_temple_built", true); } catch (e) { /* */ }
  const gen = execute(dim, site.x, site.y, site.z, rot, planTemple(seed), fillChest);
  system.runJob((function* () { try { yield* gen; } finally { try { if (onDone) onDone(rec); } catch (e) { /* */ } } })());
  return rec;
}

// ───────────────────────── الغنائم ─────────────────────────
// "pick:a|b|c" = يختار واحد عشوائي من القائمة.
// ملاحظة: لفائف تطور المهارات ما تنحط بالصناديق (من المدرب أو الكرييتف بس).
const LOOT = {
  // الأسلحة صارت نادرة: المضمون بس صندوق معبد القرية الصغير (سلاح عشوائي) وضريح السيف (الكاتانا)
  house: [["pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift", 1, 1, 0.05], ["sh:xp_scroll_small", 1, 2, 1.0], ["sh:monster_book", 1, 1, 0.15], ["sh:explorer_compass", 1, 1, 0.3], ["minecraft:bread", 2, 5, 0.9], ["minecraft:apple", 1, 3, 0.7], ["minecraft:torch", 4, 8, 0.6]],
  pantry: [["pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift", 1, 1, 0.06], ["minecraft:bread", 3, 6, 0.9], ["minecraft:cooked_chicken", 2, 4, 0.7], ["minecraft:apple", 2, 4, 0.8], ["minecraft:carrot", 3, 6, 0.6], ["minecraft:potato", 3, 6, 0.6], ["minecraft:honey_bottle", 1, 2, 0.3]],
  hokora: [["pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift", 1, 1, 0.15], ["pick:sh:dawn_dagger|sh:shadow_blade|sh:shadow_claws|sh:ember_cleaver|sh:sunset_spear|sh:stone_maul", 1, 1, 1.0], ["sh:xp_scroll_small", 2, 3, 1.0], ["sh:explorer_compass", 1, 1, 0.5], ["minecraft:golden_apple", 1, 1, 0.4]],
  ruins_small: [["sh:xp_scroll_small", 1, 2, 1.0], ["pick:sh:ember_cleaver|sh:sunset_spear", 1, 1, 0.08], ["minecraft:iron_ingot", 2, 5, 0.7]],
  ruins: [["pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift", 1, 1, 0.06], ["sh:xp_scroll_small", 1, 2, 1.0], ["sh:monster_book", 1, 1, 0.25], ["sh:explorer_compass", 1, 1, 0.3], ["pick:sh:ember_cleaver|sh:sunset_spear|sh:stone_maul", 1, 1, 0.12], ["minecraft:iron_ingot", 2, 5, 0.7], ["minecraft:cooked_porkchop", 2, 4, 0.6], ["minecraft:torch", 4, 8, 0.5]],
  palace: [["pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift", 1, 1, 0.12], ["pick:sh:stone_maul|sh:sunset_spear|sh:ember_cleaver|sh:dawn_dagger|sh:shadow_blade|sh:shadow_claws", 1, 1, 0.15], ["sh:xp_scroll_big", 1, 1, 0.8], ["sh:explorer_compass", 1, 1, 0.5], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.5], ["minecraft:cooked_beef", 4, 8, 0.9], ["minecraft:emerald", 3, 6, 0.8], ["minecraft:iron_ingot", 4, 8, 0.7]],
  lightshrine: [["sh:silver_oath", 1, 1, 1.0], ["sh:xp_scroll_big", 1, 2, 1.0], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.8], ["minecraft:diamond", 1, 2, 0.5]],
  shrine: [["sh:dark_katana", 1, 1, 1.0], ["sh:xp_scroll_big", 1, 2, 1.0], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.6], ["minecraft:diamond", 1, 2, 0.5]],
  // صندوق قمة برج الهاوية (بعد قتل وحوش الطابق السابع)
  tower: [["pick:sh:potion_vitality|sh:potion_mana|sh:potion_might|sh:potion_bulwark|sh:potion_focus|sh:potion_swift", 1, 2, 0.85], ["pick:sh:magma_scale|sh:bear_hide|sh:mantis_chitin", 2, 4, 0.7], ["sh:xp_scroll_big", 2, 3, 1.0], ["sh:xp_scroll_small", 3, 5, 1.0], ["pick:sh:dawn_dagger|sh:shadow_blade|sh:shadow_claws|sh:stone_maul|sh:sunset_spear|sh:ember_cleaver", 1, 1, 0.35], ["minecraft:diamond", 2, 4, 0.85], ["minecraft:golden_apple", 1, 2, 0.9], ["minecraft:enchanted_golden_apple", 1, 1, 0.12], ["minecraft:ender_pearl", 2, 4, 0.5], ["minecraft:netherite_scrap", 1, 1, 0.15], ["minecraft:amethyst_shard", 4, 9, 0.7], ["sh:explorer_compass", 1, 1, 0.3], ["sh:monster_book", 1, 1, 0.2]],
  altar: [["sh:xp_scroll_big", 1, 2, 1.0], ["pick:sh:dawn_dagger|sh:shadow_blade|sh:shadow_claws|sh:stone_maul|sh:sunset_spear|sh:ember_cleaver", 1, 1, 0.25], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.8], ["minecraft:diamond", 1, 2, 0.5]],
};

function fillChest(block, key) {
  try {
    const cont = block.getComponent("minecraft:inventory").container;
    const slots = Array.from({ length: cont.size }, (_, i) => i).sort(() => Math.random() - 0.5);
    let n = 0;
    for (const [id, lo, hi, chance] of LOOT[key] || []) {
      if (Math.random() > chance) continue;
      const amt = lo + Math.floor(Math.random() * (hi - lo + 1));
      let item = id;
      if (id.startsWith("pick:")) { const list = id.slice(5).split("|"); item = list[Math.floor(Math.random() * list.length)]; }
      cont.setItem(slots[n++], new ItemStack(item, amt));
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

// fillBlocks يقبل حجم محدود (~32 ألف بلوك): نقسم الصناديق الكبيرة على طبقات y
function fillBig(dim, from, to, id) {
  const w = to.x - from.x + 1, d = to.z - from.z + 1, h = to.y - from.y + 1;
  const layer = Math.max(1, Math.floor(30000 / Math.max(1, w * d)));
  for (let y = from.y; y <= to.y; y += layer) {
    dim.fillBlocks(new BlockVolume({ x: from.x, y, z: from.z }, { x: to.x, y: Math.min(to.y, y + layer - 1), z: to.z }), id);
  }
}

function setPerm(dim, at, perm) {
  if (typeof dim.setBlockPermutation === "function") dim.setBlockPermutation(at, perm);
  else { const blk = dim.getBlock(at); if (blk) blk.setPermutation(perm); }
}

function* execute(dim, ox, oy, oz, rot, plan, onChest) {
  let count = 0;
  for (const op of plan.ops) {
    try {
      if (op[0] === "box") {
        const [ax, az] = rotXZ(op[1], op[3], rot), [bx, bz] = rotXZ(op[4], op[6], rot);
        const from = { x: ox + Math.min(ax, bx), y: oy + op[2], z: oz + Math.min(az, bz) };
        const to = { x: ox + Math.max(ax, bx), y: oy + op[5], z: oz + Math.max(az, bz) };
        fillBig(dim, from, to, op[7]);
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
      } else if (op[0] === "perm") {
        const [x, z] = rotXZ(op[1], op[3], rot);
        const perm = BlockPermutation.resolve(op[4], op[5]);
        const at = { x: ox + x, y: oy + op[2], z: oz + z };
        if (typeof dim.setBlockPermutation === "function") dim.setBlockPermutation(at, perm);
        else { const blk = dim.getBlock(at); if (blk) blk.setPermutation(perm); }
      } else if (op[0] === "bed") {
        const [fx, fz] = rotXZ(op[1], op[3], rot), [hx, hz] = rotXZ(op[4], op[5], rot);
        const F = { x: ox + fx, y: oy + op[2], z: oz + fz }, Hh = { x: ox + hx, y: oy + op[2], z: oz + hz };
        const ddx = hx - fx, ddz = hz - fz;
        const guess = ddz > 0 ? 0 : ddx < 0 ? 1 : ddz < 0 ? 2 : 3;     // الراس جنوباً=0، غرباً=1، شمالاً=2، شرقاً=3 (وإذا ما ثبت نجرب الباقي)
        for (let k = 0; k < 4; k++) {
          const d = (guess + k) % 4;
          setPerm(dim, F, BlockPermutation.resolve("minecraft:bed", { direction: d, head_piece_bit: false, occupied_bit: false }));
          setPerm(dim, Hh, BlockPermutation.resolve("minecraft:bed", { direction: d, head_piece_bit: true, occupied_bit: false }));
          yield; yield; yield;
          const a1 = dim.getBlock(F), b1 = dim.getBlock(Hh);
          if (a1 && b1 && a1.typeId === "minecraft:bed" && b1.typeId === "minecraft:bed") break;
          dim.setBlockType(F, AIR); dim.setBlockType(Hh, AIR);
        }
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
  for (let tries = 0; tries < 16; tries++) {
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
    if (mx - mn > (half >= 20 ? 6 : 5)) continue;
    hs.sort((p, q) => p - q);
    return { x: cx, y: hs[Math.floor(hs.length / 2)] + 1, z: cz };
  }
  return undefined;
}

// ───────────────────────── السجل والتشغيل ─────────────────────────
let migrating = false;
function loadReg() {
  try {
    const raw = world.getDynamicProperty("sh_structs");
    if (typeof raw === "string") { const r = JSON.parse(raw); if (!migrating) { migrating = true; try { return migrateReg(r); } finally { migrating = false; } } return r; }
  } catch (e) { /* */ }
  return [];
}
function saveReg(r) {
  try { world.setDynamicProperty("sh_structs", JSON.stringify(r)); } catch (e) { /* */ }
  try { towerCache.tick = -999; } catch (e) { /* */ }                          // سطر البرج بالـHUD يتحدث فوراً
}
// الضريحان القديمان (قبل 1.28.0: بحجم 27×27 وصندوق جاهز) ننساهن من السجل حتى ينبنون الجداد 45×45 بحراسهم (المباني القديمة تبقى بالعالم)
function migrateReg(r) {
  const out = r.filter((s) => !((s.type === "shrine" || s.type === "lightshrine") && !s.v));
  if (out.length !== r.length) saveReg(out);
  return out;
}
function markBuilt(x, z, type) {
  const reg = loadReg();
  const e = reg.find((s) => s.x === x && s.z === z && s.type === type);
  if (e) { e.ok = 1; saveReg(reg); }
}
let guardHook;
// الحارسان القويان: نظهر اللي ما انقتل وما هو موجود (إذا تبخر بالبعد نعيده). النوع يتحدد من خطة الضريح (plan.spawns)
function ensureBosses(p, s) {
  const plan = PLANNERS[s.type](s.seed);
  const dim = p.dimension, centre = { x: s.x, y: s.y + 1, z: s.z }, dead = s.kt || [];
  for (const sp of plan.spawns) {
    if (dead.includes(sp.type)) continue;
    if (dim.getEntities({ type: sp.type, tags: ["sh_boss"], location: centre, maxDistance: 45 }).length) continue;
    const [x, z] = rotXZ(sp.x, sp.z, s.rot);
    const loc = { x: s.x + x + 0.5, y: s.y + sp.y, z: s.z + z + 0.5 };
    if (!dim.isChunkLoaded(loc)) continue;
    const e = dim.spawnEntity(sp.type, loc);
    try { e.addTag("sh_boss"); } catch (e4) { /* */ }               // نميّز الحارس عن وحوش الطبيعة من نفس النوع
    try { if (guardHook) guardHook(e, p); } catch (e5) { /* */ }
  }
}
// يستدعيه main.js لما يموت أي وحش: إذا كان من حراس ضريح قريب نسجله، ولما يموت الاثنان يظهر صندوق السيف بمكان الجائزة
export function onShrineBossDeath(typeId, loc, dim, tagged = true) {
  if (!tagged || !dim || dim.id !== "minecraft:overworld") return;
  const reg = loadReg();
  for (const s of reg) {
    const spec = STRUCTURES[s.type];
    if (!spec || !spec.bosses || s.c || !spec.bosses.includes(typeId)) continue;
    if (Math.hypot(s.x - loc.x, s.z - loc.z) > 36) continue;
    s.kt = s.kt || [];
    if (s.kt.includes(typeId)) continue;
    s.kt.push(typeId);
    if (s.kt.length >= spec.bosses.length) { s.c = 1; saveReg(reg); openSeal(dim, s); }
    else {
      saveReg(reg);
      for (const p of dim.getPlayers({ location: { x: s.x, y: s.y, z: s.z }, maxDistance: 70 })) { try { p.sendMessage("§6[Shrine] §fOne guardian has fallen. §7The seal still holds: defeat the other one."); } catch (e) { /* */ } }
    }
    return;
  }
}
// الختم ينكسر: صندوق السيف يظهر قدام المنارة، مع أصوات وجزيئات ماينكرافت
function openSeal(dim, s) {
  const plan = PLANNERS[s.type](s.seed), rw = plan.rewardAt;
  if (!rw) return;
  const [x, z] = rotXZ(rw.x, rw.z, s.rot);
  const loc = { x: s.x + x, y: s.y + rw.y, z: s.z + z };
  dim.setBlockType(loc, "minecraft:chest");
  const b = dim.getBlock(loc);
  if (b) fillChest(b, rw.key);
  const c = { x: loc.x + 0.5, y: loc.y + 0.6, z: loc.z + 0.5 };
  try {
    dim.spawnParticle("minecraft:large_explosion", c);
    dim.spawnParticle("minecraft:totem_particle", c);
    dim.playSound("random.levelup", c, { volume: 1.2, pitch: 0.8 });
    dim.playSound("random.totem", c, { volume: 1.0, pitch: 1.0 });
  } catch (e) { /* */ }
  const sword = s.type === "lightshrine" ? "Oath of Light" : "Abyss Katana";
  for (const p of dim.getPlayers({ location: { x: s.x, y: s.y, z: s.z }, maxDistance: 80 })) {
    try { p.sendMessage(`§6[Shrine] §fBoth guardians are defeated. §eThe seal breaks!\n§7A chest appeared before the beam: it holds the §f${sword}§7.`); } catch (e) { /* */ }
  }
}

let building = false;
const announced = new Set();

// الضريح نادر وسيفه مهم، فإذا بُنيت 3 بنايات بدون ضريح نضمنه بالجاية (حتى ما يقعد اللاعب يدور عليه للأبد)
const SHRINE_PITY = 2;
function chooseType(reg = []) {
  const has = (t) => reg.some((s) => s.type === t);
  if (!has("shrine") && reg.length >= SHRINE_PITY) return "shrine";
  if (!has("lightshrine") && has("shrine") && reg.length >= SHRINE_PITY + 2) return "lightshrine";
  const total = Object.values(STRUCTURES).reduce((a, v) => a + (v.weight || 0), 0);
  const roll = Math.random() * total;
  let acc = 0;
  for (const [k, v] of Object.entries(STRUCTURES)) {
    acc += v.weight;
    if (roll < acc) return v.unique && has(k) ? "village" : k;   // الضريحين مرة وحدة بالعالم
  }
  return "village";
}


// ───────────────────────── برج الهاوية: وحوش الطوابق وصندوق القمة ─────────────────────────
// كل طابق تطلع وحوشه أول ما يوصله لاعب (مرة وحدة). الطابق السابع: 1-2 وحش عالي الرتبة؛ إذا تبخروا (اللاعب بعد) يرجعون لما يرجع،
// ولما ينقتلون كلهم يطلع صندوق الجائزة بنص الطابق.
const TOWER_LOWLY = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"];
const TOWER_GRIM = ["sh:gloomhorn", "sh:hollow_seer", "sh:veilfox"];
const TOWER_HIGH = ["sh:magmamoth", "sh:grey_bear", "sh:prayer_mantis"];
const pickOf = (a) => a[Math.floor(Math.random() * a.length)];
export function towerFloorMobs(k) {
  if (k <= 2) return Array.from({ length: 3 + k }, () => pickOf(TOWER_LOWLY));                        // 1-3: Lowly بالعدد (3، 4، 5)
  if (k <= 5) {                                                                                     // 4-6: أقوى ومتوازن
    const grim = [2, 2, 3][k - 3], low = [1, 2, 1][k - 3];
    return [...Array.from({ length: grim }, () => pickOf(TOWER_GRIM)), ...Array.from({ length: low }, () => pickOf(TOWER_LOWLY))];
  }
  const pool = [...TOWER_HIGH].sort(() => Math.random() - 0.5);                                     // 7: وحش أو اثنين عاليين (مختلفين)
  return pool.slice(0, Math.random() < 0.5 ? 1 : 2);
}
function towerSpawn(dim, s, plan, k, types, p, top) {
  const fl = plan.towerFloors[k];
  types.forEach((type, i) => {
    const [px, pz] = fl.pts[i % fl.pts.length];
    const [x, z] = rotXZ(px, pz, s.rot);
    const loc = { x: s.x + x + 0.5, y: s.y + fl.y, z: s.z + z + 0.5 };
    try {
      if (!dim.isChunkLoaded(loc)) return;
      const e = dim.spawnEntity(type, loc);
      try { e.addTag("sh_tower"); e.addTag(`sh_tf${k}`); if (top) e.addTag("sh_tower_top"); } catch (e2) { /* */ }
      try { if (guardHook) guardHook(e, p); } catch (e3) { /* */ }
    } catch (e1) { /* */ }
  });
}
// ختم الدرج: زجاج بنفسجي يسد فتحة الدرج فوق الطابق k لحد ما تنظفه (k = 0..5)
function towerSealCells(s, k) {
  const y0 = k * TOWER_FH, east = k % 2 === 0, xs = east ? [5, 6] : [-6, -5], sz = east ? -1 : 1;
  const out = [];
  for (const i of [4, 5]) for (const x of xs) { const [rx, rz] = rotXZ(x, (east ? 3 : -3) + sz * i, s.rot); out.push({ x: s.x + rx, y: s.y + y0 + TOWER_FH - 1, z: s.z + rz }); }
  return out;
}
function towerSeal(dim, s, k, on) {
  for (const c of towerSealCells(s, k)) { try { dim.setBlockType(c, on ? "minecraft:purple_stained_glass" : "minecraft:air"); } catch (e) { /* */ } }
}
// الطابق k انتهى: الختم ينكسر + جوائز (خبرة، وبالطوابق 3 و6 لفافة وأحياناً جرعة)
function towerFloorCleared(dim, s, k) {
  const fl = { x: s.x + 0.5, y: s.y + k * TOWER_FH + 0.5, z: s.z + 0.5 };
  if (k < TOWER_FLOORS - 1) {
    towerSeal(dim, s, k, false);
    try {
      for (let i = 0; i < 3 + k; i++) dim.spawnEntity("minecraft:xp_orb", { x: fl.x + (Math.random() - 0.5) * 2, y: fl.y + 0.5, z: fl.z + (Math.random() - 0.5) * 2 });
      if (k === 2 || k === 5) {
        dim.spawnItem(new ItemStack("sh:xp_scroll_small", 1), fl);
        if (Math.random() < 0.35) dim.spawnItem(new ItemStack(pickOf(POTION_IDS), 1), fl);
      }
      dim.spawnParticle("minecraft:totem_particle", { x: fl.x, y: fl.y + 1, z: fl.z });
      dim.playSound("random.levelup", fl, { volume: 0.9, pitch: 1.1 });
      dim.playSound("random.glass", fl, { volume: 0.8, pitch: 0.7 });
    } catch (e) { /* */ }
    for (const p of dim.getPlayers({ location: fl, maxDistance: 30 })) { try { p.sendMessage(`§5[Abyss Tower] §aFloor ${k + 1} cleared! §7The seal on the stairs breaks.`); } catch (e) { /* */ } }
  }
}
// مكان الخيميائي بخطة القرية (مسار حصى مفتوح للسما، فحص check_village)
export const ALCHEMIST_SPOT = [2, 0, 17];
const POTION_IDS = ["sh:potion_vitality", "sh:potion_mana", "sh:potion_might", "sh:potion_bulwark", "sh:potion_focus", "sh:potion_swift"];
function towerTick() {
  let reg;
  for (const p of world.getAllPlayers()) {
    try {
      if (p.dimension.id !== "minecraft:overworld") continue;
      reg = reg || loadReg();
      for (const s of reg) {
        if (s.type !== "tower" || !s.ok) continue;
        if (Math.hypot(p.location.x - s.x - 0.5, p.location.z - s.z - 0.5) > 7.2) continue;      // جوه البرج بس
        const ly = p.location.y - s.y;
        if (ly < -0.5 || ly >= TOWER_FH * TOWER_FLOORS) continue;
        const k = Math.max(0, Math.min(TOWER_FLOORS - 1, Math.floor((ly + 0.2) / TOWER_FH)));
        const plan = planTower(s.seed), dim = p.dimension, top = k === TOWER_FLOORS - 1;
        s.fl = s.fl || 0; s.ft = s.ft || {}; s.cl = s.cl || 0;
        if (!(s.fl & (1 << k))) {
          s.fl |= 1 << k;
          const types = towerFloorMobs(k);
          s.ft[k] = [...types];
          s.fn = s.fn || {}; s.fn[k] = types.length;                         // عدد وحوش الطابق (لسطر Floor فوق الهوت بار)
          if (top) { s.top = types; s.kt = []; }
          saveReg(reg);
          towerSpawn(dim, s, plan, k, types, p, top);
          if (!top) towerSeal(dim, s, k, true);
          try {
            p.sendMessage(top ? `§5[Abyss Tower] §dFloor 7: the master of the tower awakens! §7(${types.length === 2 ? "two of them" : "one of them"}; defeat it to claim the treasure)` : `§5[Abyss Tower] §fFloor ${k + 1} §7— ${types.length} monsters. §8The stairs stay sealed until the floor is cleared.`);
            p.playSound(top ? "mob.wither.spawn" : "mob.evocation_illager.prepare_attack", { volume: top ? 0.6 : 0.8, pitch: top ? 1.2 : 0.8 });
          } catch (e4) { /* */ }
        } else if (s.ft[k] && s.ft[k].length && !(s.cl & (1 << k))) {
          // وحوش الطابق تبخرت (اللاعب بعد): نرجع اللي ما انقتل لما يرجع للطابق
          const c = { x: s.x, y: s.y + plan.towerFloors[k].y, z: s.z };
          const alive = dim.getEntities({ location: c, maxDistance: 14, tags: [`sh_tf${k}`] }).length + (top ? dim.getEntities({ location: c, maxDistance: 14, tags: ["sh_tower_top"] }).length : 0);
          if (!alive) towerSpawn(dim, s, plan, k, s.ft[k], p, top);
        } else if (top && !s.c && s.top && !s.ft[k]) {
          // برج قديم (قبل 1.35): الطابق السابع بالطريقة القديمة
          const c = { x: s.x, y: s.y + plan.towerFloors[k].y, z: s.z };
          const alive = dim.getEntities({ location: c, maxDistance: 14, tags: ["sh_tower_top"] }).length;
          if (!alive) {
            const left = [...s.top];
            for (const t of s.kt || []) { const i = left.indexOf(t); if (i >= 0) left.splice(i, 1); }
            if (left.length) towerSpawn(dim, s, plan, k, left, p, true);
          }
        }
      }
    } catch (e) { /* */ }
  }
}
function towerChest(dim, s) {
  const plan = planTower(s.seed), rw = plan.rewardAt;
  const [x, z] = rotXZ(rw.x, rw.z, s.rot);
  const at = { x: s.x + x, y: s.y + rw.y, z: s.z + z };
  dim.setBlockType(at, "minecraft:chest");
  const b = dim.getBlock(at);
  if (b) fillChest(b, rw.key);
  const c = { x: at.x + 0.5, y: at.y + 0.6, z: at.z + 0.5 };
  try {
    dim.spawnParticle("minecraft:large_explosion", c);
    dim.spawnParticle("minecraft:totem_particle", c);
    dim.playSound("random.levelup", c, { volume: 1.2, pitch: 0.8 });
    dim.playSound("random.totem", c, { volume: 1.0, pitch: 1.1 });
  } catch (e3) { /* */ }
  for (const p of dim.getPlayers({ location: c, maxDistance: 60 })) { try { p.sendMessage("§5[Abyss Tower] §dThe tower is conquered! §7A treasure chest appeared in the middle of the top floor."); } catch (e4) { /* */ } }
}
// يستدعيه main.js لما يموت وحش بالبرج: نشيله من قائمة طابقه، ولما يخلص الطابق ينكسر الختم (أو يطلع صندوق القمة)
export function onTowerMobDeath(e) {
  try {
    if (!e.hasTag("sh_tower")) return;
    const reg = loadReg(), loc = e.location, dim = e.dimension;
    const s = reg.find((t) => t.type === "tower" && Math.hypot(t.x - loc.x, t.z - loc.z) < 14);
    if (!s) return;
    let k = -1;
    for (let i = 0; i < TOWER_FLOORS; i++) if (e.hasTag(`sh_tf${i}`)) k = i;
    if (k < 0 && e.hasTag("sh_tower_top")) k = TOWER_FLOORS - 1;
    if (k < 0) return;
    const top = k === TOWER_FLOORS - 1;
    if (top && s.c) return;
    if (s.ft && s.ft[k]) {
      const i = s.ft[k].indexOf(e.typeId);
      if (i >= 0) s.ft[k].splice(i, 1);
      if (s.ft[k].length) {
        saveReg(reg);
        if (top) for (const p of dim.getPlayers({ location: loc, maxDistance: 40 })) { try { p.sendMessage("§5[Abyss Tower] §fOne master has fallen. §7Another still stands."); } catch (e2) { /* */ } }
        return;
      }
      if (s.cl & (1 << k)) return;
      s.cl = (s.cl || 0) | (1 << k);
      if (top) s.c = 1;
      saveReg(reg);
      if (top) towerChest(dim, s); else towerFloorCleared(dim, s, k);
      return;
    }
    if (!top || !s.top) return;                                                    // برج قديم: الطابق السابع بالطريقة القديمة
    s.kt = s.kt || [];
    s.kt.push(e.typeId);
    const left = [...s.top];
    for (const t of s.kt) { const i = left.indexOf(t); if (i >= 0) left.splice(i, 1); }
    if (left.length) { saveReg(reg); return; }
    s.c = 1; saveReg(reg);
    towerChest(dim, s);
  } catch (e) { /* */ }
}
// سطر الـHUD داخل البرج: رقم الطابق وكم وحش باقي
var towerCache = { tick: -999, reg: [] };
export function towerHudLine(p, plain) {
  try {
    if (system.currentTick - towerCache.tick > 20) { towerCache.reg = loadReg().filter((s) => s.type === "tower" && s.ok); towerCache.tick = system.currentTick; }
    for (const s of towerCache.reg) {
      if (Math.hypot(p.location.x - s.x - 0.5, p.location.z - s.z - 0.5) > 7.5) continue;
      const ly = p.location.y - s.y;
      if (ly < -0.5 || ly >= TOWER_FH * TOWER_FLOORS) continue;
      const k = Math.max(0, Math.min(TOWER_FLOORS - 1, Math.floor((ly + 0.2) / TOWER_FH)));
      // سطر فوق الهوت بار: كلمة Floor + رقم الطابق + شكد خلصت منه (شريط + قتلت/الكل)
      const left = s.ft && s.ft[k] ? s.ft[k].length : 0;
      const done = (s.cl || 0) & (1 << k) || (k === TOWER_FLOORS - 1 && s.c);
      const total = Math.max(left, (s.fn && s.fn[k]) || (s.ft && s.ft[k] ? left : 0)), killed = done ? total : total - left;
      const n = Math.max(0, Math.min(8, Math.round(total ? (killed / total) * 8 : done ? 8 : 0))), ch = plain ? "|" : "█";
      const bar = (done ? "§a" : "§d") + ch.repeat(n) + "§8" + ch.repeat(8 - n);
      const tail = done ? (k === TOWER_FLOORS - 1 ? "  §dConquered ✔" : "  §aCleared, climb! ✔") : "";
      return `§dFloor §f${k + 1}§7/${TOWER_FLOORS}  ${bar}${total ? `  §f${killed}§7/${total}` : ""}${tail}`;
    }
  } catch (e) { /* */ }
  return "";
}

export function setupStructures(onGuardSpawn) {
  guardHook = onGuardSpawn;
  system.runInterval(towerTick, 10);
  // بناء هيكل جديد قرب اللاعب (بعيد عن الهياكل الموجودة)
  system.runInterval(() => {
    if (building) return;
    for (const p of world.getAllPlayers()) {
      try {
        if (p.dimension.id !== "minecraft:overworld") continue;
        const reg = loadReg();
        // أول بناية تنبني بسرعة (حتى ما يحس اللاعب العالم فاضي)، وبعدها بوتيرة هادئة
        if (reg.length > 0 && Math.random() > 0.35) continue;
        const type = chooseType(reg);
        const spec = STRUCTURES[type];
        // لا نكثّر: حد أقصى 3 بنايات ضمن 170 بلوكة من اللاعب
        if (reg.filter((s) => Math.hypot(s.x - p.location.x, s.z - p.location.z) < 170).length >= 3) continue;
        const site = pickSite(p.dimension, p.location, 48, 95, spec.half);
        if (!site) continue;
        if (reg.some((s) => Math.hypot(s.x - site.x, s.z - site.z) < 125)) continue;
        const seed = Math.floor(Math.random() * 1e9);
        const rot = Math.floor(Math.random() * 4);
        const plan = PLANNERS[type](seed);
        reg.push({ x: site.x, y: site.y, z: site.z, type, rot, seed, v: 2 });
        saveReg(reg);
        // نخبر اللاعب وين طلعت البناية (حتى ما يدور بدون فايدة)
        try {
          const dx = site.x - p.location.x, dz = site.z - p.location.z;
          const dirs = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"];
          const dir = dirs[((Math.round((Math.atan2(dz, dx) * 180) / Math.PI / 45) % 8) + 8) % 8];
          p.sendMessage(`§6[Explore] §fA structure appeared nearby: §e${spec.name}§f, ${Math.round(Math.hypot(dx, dz))} blocks to the ${dir}. §7Use the Explorer's Compass.`);
          if (!p.getDynamicProperty("sh_ctarget")) p.setDynamicProperty("sh_ctarget", type);
        } catch (e6) { /* */ }
        building = true;
        const gen = execute(p.dimension, site.x, site.y, site.z, rot, plan, fillChest);
        const job = system.runJob((function* () { try { yield* gen; } finally { building = false; markBuilt(site.x, site.z, type); } })());
        return;
      } catch (e) { building = false; }
    }
  }, 400);

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
          try { p.sendMessage(`§6[Explore] §fYou reached ${STRUCTURES[s.type].name}\n§7${STRUCTURES[s.type].lore}`); } catch (e) { /* */ }
        }
        if (s.type === "village" && s.ok && d < 60) {                        // الخيميائي: شيخ واحد بكل قرية ساكورا (على المسار)
          try {
            const centre = { x: s.x, y: s.y + 1, z: s.z };
            if (!p.dimension.getEntities({ type: "sh:alchemist", location: centre, maxDistance: 80 }).length) {
              const [ax, az] = rotXZ(ALCHEMIST_SPOT[0], ALCHEMIST_SPOT[2], s.rot);
              const loc = { x: s.x + ax + 0.5, y: s.y + ALCHEMIST_SPOT[1], z: s.z + az + 0.5 };
              if (p.dimension.isChunkLoaded(loc)) { const e = p.dimension.spawnEntity("sh:alchemist", loc); try { e.addTag("sh_alchemist"); } catch (e2) { /* */ } }
            }
          } catch (e) { /* */ }
          continue;
        }
        if (STRUCTURES[s.type].tower) continue;                              // البرج: وحوشه بالطوابق (towerTick)
        if (STRUCTURES[s.type].bosses) {                                    // الضريحان: حارسان قويان فقط لحد ما ينكسر الختم
          if (s.ok && !s.c && d < 50) { try { ensureBosses(p, s); } catch (e) { /* */ } }
          continue;
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
              try { if (onGuardSpawn) onGuardSpawn(e, p); } catch (e5) { /* */ }
            }
          } catch (e) { /* */ }
        }
      }
    }
  }, 400);
}
