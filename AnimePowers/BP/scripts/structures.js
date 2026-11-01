// هياكل الاستكشاف: بيوت يابانية، قصر، خرائب معبد. تنبني بالسكربت قرب اللاعب وهو يتحرك.
import { world, system, BlockPermutation, BlockVolume, ItemStack } from "@minecraft/server";

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
  constructor(seed) { this.ops = []; this.spawns = []; this.r = rng(seed); }
  box(x1, y1, z1, x2, y2, z2, id) { this.ops.push(["box", x1, y1, z1, x2, y2, z2, id]); }
  set(x, y, z, id) { this.ops.push(["set", x, y, z, id]); }
  stair(x, y, z, id, dir, upside = false) { this.ops.push(["stair", x, y, z, id, dir, upside]); }
  perm(x, y, z, id, states) { this.ops.push(["perm", x, y, z, id, states]); }
  chest(x, y, z, key) { this.ops.push(["chest", x, y, z, key]); }
  mob(x, y, z, type) { this.spawns.push({ x, y, z, type }); }
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
    const col = black ? "minecraft:polished_blackstone_bricks" : "minecraft:red_concrete";
    const top = black ? "minecraft:polished_blackstone_bricks" : "minecraft:black_concrete";
    const slab = black ? "minecraft:polished_blackstone_brick_slab" : "minecraft:black_concrete";
    this.box(cx - half, 0, z, cx - half, h, z, col);
    this.box(cx + half, 0, z, cx + half, h, z, col);
    this.set(cx - half, 0, z, "minecraft:stone_bricks"); this.set(cx + half, 0, z, "minecraft:stone_bricks");
    this.box(cx - half, h - 2, z, cx + half, h - 2, z, col);
    this.box(cx - half - 1, h + 1, z, cx + half + 1, h + 1, z, top);
    this.box(cx - half - 2, h + 2, z, cx + half + 2, h + 2, z, slab);
    this.set(cx - half - 3, h + 3, z, slab); this.set(cx + half + 3, h + 3, z, slab);
    this.hang(cx, h - 3, z, black ? "minecraft:soul_lantern" : "minecraft:lantern");
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
  village: { name: "Sakura Village", half: 22, weight: 0.3, guards: 0, lore: "The Order of Dawn's first home, where the story began." },
  palace: { name: "Sunset Palace", half: 26, weight: 0.2, guards: 4, lore: "The last light fell here before the palace fell." },
  ruins: { name: "Temple Ruins", half: 14, weight: 0.35, guards: 3, lore: "The ancient temple, where the first shard landed." },
  shrine: { name: "Dark Sword Shrine", half: 13, weight: 0.15, guards: 3, lore: "The Abyss sleeps beneath this stone." },
};

// قرية الساكورا (45×45): توري، شارع رئيسي، 6 بيوت بشرفات، ساحة تشوزويا، معبد صغير، بركة كوي وجسر، حديقة حصى، باغودا، أكشاك سوق
export function planVillage(seed) {
  const P = new Plan(seed);
  P.ground(-22, -22, 22, 22, 17);
  const PATH = "minecraft:dirt_path";
  // الشارع الرئيسي + فروع تصل لكل باب
  P.box(-1, -1, -21, 1, -1, 17, PATH);
  for (const [x1, z1, x2, z2] of [[-6, -16, -2, -14], [2, -15, 6, -13], [-6, -4, -2, -2], [2, -3, 6, -1], [-6, 7, -2, 9], [2, 8, 6, 10]]) P.box(x1, -1, z1, x2, -1, z2, PATH);
  // بوابة توري كبيرة + درج حجري
  P.torii(0, -21, 3, 6);
  P.stair(-1, -1, -22, "minecraft:stone_brick_stairs", "s"); P.stair(0, -1, -22, "minecraft:stone_brick_stairs", "s"); P.stair(1, -1, -22, "minecraft:stone_brick_stairs", "s");
  for (const z of [-19, -11, 3, 11]) { P.toro(-2, z); P.toro(2, z); }
  // البيوت (باب كل بيت يواجه الشارع)
  P.house(-17, -19, -7, -10, "e", { loot: "house" });
  P.house(7, -19, 17, -9, "w", { loot: "house" });
  P.house(-15, -6, -7, 1, "e", { loot: "house" });
  P.house(7, -5, 14, 1, "w", { loot: "house", wall: "minecraft:smooth_quartz" });
  P.house(-14, 5, -7, 11, "e", { loot: "house" });
  P.house(7, 6, 16, 12, "w", { loot: "house", wall: "minecraft:smooth_quartz" });
  // أكشاك السوق قرب المدخل
  P.stall(3, -9, 5, -7); P.stall(-5, -9, -3, -7);
  // ساحة بحجر وتشوزويا وبنشات
  P.box(-5, -1, 12, 5, -1, 17, "minecraft:stone_bricks");
  P.box(-4, -1, 13, 4, -1, 16, "minecraft:polished_andesite");
  P.chozuya(0, 14);
  P.stair(-3, 0, 16, "minecraft:dark_oak_stairs", "n"); P.stair(3, 0, 16, "minecraft:dark_oak_stairs", "n");
  P.toro(-5, 12); P.toro(5, 12); P.toro(-5, 17); P.toro(5, 17);
  // معبد صغير (هوكورا) نهاية الشارع: درج، 4 أعمدة حمراء، سقف أحمر، صندوق قرابين
  P.box(-4, -1, 18, 4, -1, 22, "minecraft:stone_bricks");
  for (const x of [-1, 0, 1]) P.stair(x, 0, 18, "minecraft:stone_brick_stairs", "s");
  P.box(-3, 0, 19, 3, 0, 22, "minecraft:stone_bricks");
  for (const [x, z] of [[-2, 20], [2, 20], [-2, 22], [2, 22]]) P.box(x, 1, z, x, 4, z, "minecraft:red_concrete");
  P.box(-2, 1, 22, 2, 3, 22, "minecraft:dark_oak_planks");
  P.box(-2, 1, 20, -2, 3, 22, "minecraft:dark_oak_planks"); P.box(2, 1, 20, 2, 3, 22, "minecraft:dark_oak_planks");
  P.box(-1, 1, 21, 1, 3, 21, AIR);
  P.roof(-2, 20, 2, 22, 5, 2, "minecraft:red_nether_brick_stairs", "minecraft:red_nether_brick_slab", "minecraft:red_nether_brick_slab");
  P.chest(0, 1, 22, "hokora");
  P.hang(0, 3, 21);
  // بركة كوي + جسر + شجرة فوقها
  P.pond(9, 14, 20, 21);
  P.bridgeX(8, 21, 17);
  P.cherry(21, 13); P.toro(8, 13); P.toro(8, 21);
  // حديقة حصى + باغودا
  P.karesansui(-9, 14, -6, 20);
  P.pagoda(-16, 17, 3, 3);
  // أشجار ساكورا موزعة
  for (const [x, z] of [[-4, -17], [4, -17], [-4, 5], [4, 5], [-20, -8], [20, -6], [-20, 7], [20, 4], [-20, -20], [20, -20]]) P.cherry(x, z);
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
  P.box(-1, -1, 22, 1, -1, 23, "minecraft:dirt_path");
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
export function planRuins(seed) {
  const P = new Plan(seed);
  const r = P.r;
  P.ground(-14, -14, 14, 14, 10);
  P.box(-11, -1, -11, 11, -1, 11, "minecraft:mossy_stone_bricks");
  for (let x = -11; x <= 11; x++) for (let z = -11; z <= 11; z++) {
    const v = r();
    if (v < 0.22) P.set(x, -1, z, "minecraft:cracked_stone_bricks");
    else if (v < 0.34) P.set(x, -1, z, "minecraft:mossy_cobblestone");
    else if (v < 0.4) P.set(x, -1, z, "minecraft:moss_block");
  }
  // جدران مكسورة بارتفاعات مختلفة
  for (let i = -11; i <= 11; i++) {
    for (const [x, z] of [[i, -11], [i, 11], [-11, i], [11, i]]) {
      if (r() < 0.38) continue;
      P.box(x, 0, z, x, 1 + Math.floor(r() * 3), z, r() < 0.5 ? "minecraft:mossy_stone_bricks" : "minecraft:stone_bricks");
    }
  }
  // درج للمنصة المرتفعة + أعمدة (بعضها مكسور)
  P.box(-5, 0, -5, 5, 0, 5, "minecraft:stone_bricks");
  for (const x of [-1, 0, 1]) P.stair(x, 0, 6, "minecraft:stone_brick_stairs", "n");
  for (const [x, z] of [[-5, -5], [5, -5], [-5, 5], [5, 5]]) {
    const hgt = 2 + Math.floor(r() * 4);
    P.box(x, 1, z, x, hgt, z, "minecraft:mossy_stone_bricks");
    if (r() < 0.5) P.set(x, hgt + 1, z, "minecraft:soul_lantern");
  }
  // توري مهدم: عمود قائم وآخر ساقط وكاساغي مكسور
  P.box(-3, 0, -10, -3, 5, -10, "minecraft:red_concrete");
  P.box(3, 0, -10, 6, 0, -10, "minecraft:red_concrete");
  P.box(-3, 6, -10, -1, 6, -10, "minecraft:black_concrete");
  P.set(4, 1, -10, "minecraft:black_concrete");
  // باغودا متهدمة بالزاوية: طابقان ونصف
  P.box(-12, -1, 7, -8, 0, 11, "minecraft:mossy_stone_bricks");
  P.box(-12, 1, 7, -8, 2, 11, "minecraft:stone_bricks"); P.box(-11, 1, 8, -9, 2, 10, AIR);
  P.box(-12, 3, 7, -8, 3, 8, "minecraft:mossy_stone_bricks"); P.box(-12, 3, 7, -11, 4, 11, "minecraft:mossy_stone_bricks");
  P.set(-10, 0, 10, "minecraft:azalea"); P.set(-9, 0, 8, "minecraft:flowering_azalea");
  // أعشاب ونباتات
  for (let i = 0; i < 26; i++) P.set(-10 + Math.floor(r() * 21), 0, -10 + Math.floor(r() * 21), r() < 0.5 ? "minecraft:moss_carpet" : "minecraft:azalea");
  // المذبح
  P.box(-2, 0, -2, 2, 0, 2, "minecraft:stone_bricks");
  P.box(-1, 1, -1, 1, 1, 1, "minecraft:chiseled_stone_bricks");
  P.chest(0, 2, 0, "altar");
  P.set(-1, 2, -1, "minecraft:soul_torch"); P.set(1, 2, 1, "minecraft:soul_torch");
  P.chest(-9, 0, 9, "ruins"); P.chest(9, 0, -9, "ruins"); P.chest(-9, 0, -9, "ruins");
  P.mob(-3, 0, 3, "sh:rust_guard"); P.mob(3, 0, -3, "sh:ember_imp"); P.mob(3, 0, 3, "sh:ember_imp");
  return P;
}

// ضريح السيف المظلم: منصات متدرجة من حجر أسود، توريان أسودان، بركتان، أعمدة فوانيس، دكة الكاتانا
export function planShrine(seed) {
  const P = new Plan(seed);
  const r = P.r;
  const BB = "minecraft:polished_blackstone_bricks", BW = "minecraft:polished_blackstone_brick_wall";
  P.ground(-13, -13, 13, 13, 10, "minecraft:coarse_dirt");
  P.box(-12, -1, -12, 12, -1, 12, BB);
  for (let x = -12; x <= 12; x++) for (let z = -12; z <= 12; z++) if (r() < 0.16) P.set(x, -1, z, "minecraft:cracked_polished_blackstone_bricks");
  // ممر بحواف بنفسجية
  P.box(-1, -1, 4, 1, -1, 12, "minecraft:polished_blackstone");
  P.box(-2, -1, 4, -2, -1, 12, "minecraft:purple_concrete"); P.box(2, -1, 4, 2, -1, 12, "minecraft:purple_concrete");
  // بركتان عاكستان على جانبي الممر
  for (const sx of [-1, 1]) {
    P.box(sx * 6 - 2, -1, 5, sx * 6 + 2, -1, 10, "minecraft:blackstone");
    P.box(sx * 6 - 1, -2, 6, sx * 6 + 1, -1, 9, WATER);
    P.set(sx * 6, 0, 7, "minecraft:soul_lantern");
  }
  // سور واطي مع فتحة البوابة
  for (let i = -12; i <= 12; i++) {
    P.set(i, 0, -12, BW); P.set(-12, 0, i, BW); P.set(12, 0, i, BW);
    if (Math.abs(i) > 2) P.set(i, 0, 12, BW);
  }
  // توريان أسودان (خارجي كبير وداخلي أصغر)
  P.torii(0, 12, 3, 6, true);
  P.torii(0, 8, 2, 5, true);
  // درجان للمنصة المركزية ثم الدكة
  P.box(-5, 0, -5, 5, 0, 5, BB);
  P.box(-4, 1, -4, 4, 1, 4, "minecraft:polished_blackstone");
  P.box(-3, 2, -3, 3, 2, 3, "minecraft:chiseled_polished_blackstone");
  for (const x of [-1, 0, 1]) { P.stair(x, 0, 6, "minecraft:polished_blackstone_brick_stairs", "n"); P.stair(x, 1, 5, "minecraft:polished_blackstone_brick_stairs", "n"); }
  P.box(-1, 3, -1, 1, 3, 1, "minecraft:crying_obsidian");
  P.chest(0, 4, 0, "shrine");
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) P.box(x, 4, z, x, 6, z, "minecraft:end_rod");
  // أعمدة الأركان بفوانيس الروح + أعمدة المنصة
  for (const [x, z] of [[-11, -11], [11, -11], [-11, 11], [11, 11]]) { P.box(x, 0, z, x, 4, z, BW); P.set(x, 5, z, "minecraft:soul_lantern"); }
  for (const [x, z] of [[-5, -5], [5, -5], [-5, 5], [5, 5]]) { P.box(x, 1, z, x, 4, z, "minecraft:polished_blackstone_brick_wall"); P.set(x, 5, z, "minecraft:soul_lantern"); }
  // فوانيس حجر أسود على جانبي الممر + أعمدة بلور بنفسجي حول الدكة
  for (const z of [5, 7, 9, 11]) for (const x of [-3, 3]) { P.set(x, 0, z, BB); P.set(x, 1, z, BW); P.set(x, 2, z, "minecraft:soul_lantern"); P.set(x, 3, z, "minecraft:polished_blackstone_brick_slab"); }
  for (const [x, z] of [[-3, -3], [3, -3], [-3, 3], [3, 3]]) P.box(x, 3, z, x, 5, z, "minecraft:purple_stained_glass");
  // مجامر ومواقد
  P.set(-8, 0, 0, "minecraft:soul_campfire"); P.set(8, 0, 0, "minecraft:soul_campfire");
  for (const z of [-8, 0]) { P.set(-8, 0, z, "minecraft:soul_torch"); P.set(8, 0, z, "minecraft:soul_torch"); }
  P.mob(-4, 0, -4, "sh:shadow_hound"); P.mob(4, 0, -4, "sh:shadow_hound"); P.mob(0, 0, 8, "sh:rust_guard");
  return P;
}

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
  // أعمدة أميثست بالزوايا (تتوهج بعناقيد)
  for (const [x, z] of [[-8, -8], [8, -8], [-8, 8], [8, 8]]) {
    P.box(x, 1, z, x, 7, z, "minecraft:amethyst_block");
    P.set(x, 1, z - Math.sign(z), "minecraft:amethyst_cluster"); P.set(x - Math.sign(x), 1, z, "minecraft:amethyst_cluster");
    P.set(x, 4, z - Math.sign(z), "minecraft:large_amethyst_bud"); P.set(x - Math.sign(x), 4, z, "minecraft:large_amethyst_bud");
    P.hang(x - Math.sign(x), 7, z - Math.sign(z), "minecraft:soul_lantern");
  }
  // فوانيس معلقة بسلاسل بحلقة حول البلورة
  for (let a = 0; a < 8; a++) {
    const ang = (a / 8) * Math.PI * 2 + Math.PI / 8, x = Math.round(Math.cos(ang) * 6), z = Math.round(Math.sin(ang) * 6);
    P.set(x, 7, z, "minecraft:chain"); P.hang(x, 6, z, a % 2 ? "minecraft:soul_lantern" : "minecraft:lantern");
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
  for (const [x, z] of [[-10, 10], [10, 10]]) { P.set(x, 1, z, "minecraft:azalea_leaves"); P.set(x, 2, z, "minecraft:flowering_azalea_leaves"); }
  // السقف: سبع طبقات، فتحة سماوية زجاج فوق البلورة وقبة فانوس ذهبية
  P.roof(-13, -13, 13, 13, 9, 7, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:deepslate_tile_slab");
  P.box(-11, 9, -11, 11, 9, 11, "minecraft:dark_oak_planks");
  P.box(-1, 8, -1, 1, 17, 1, AIR);
  P.box(-1, 9, -1, 1, 16, 1, "minecraft:light_blue_stained_glass");
  P.eave(-2, -2, 2, 2, 17, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tile_slab");
  P.box(-1, 19, -1, 1, 19, 1, "minecraft:gold_block");
  P.set(0, 20, 0, "minecraft:lightning_rod");
  // الساحة القدامية: توري، فوانيس حجر، ساكورا
  P.torii(0, 19, 4, 6);
  for (const x of [-5, 5]) { P.toro(x, 17); P.toro(x, 21); }
  for (const [x, z] of [[-15, -15], [15, -15], [-15, 17], [15, 17]]) P.cherry(x, z, 6);
  return P;
}

const PLANNERS = { village: planVillage, palace: planPalace, ruins: planRuins, shrine: planShrine, temple: planTemple };
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
  house: [["sh:xp_scroll_small", 1, 2, 1.0], ["sh:monster_book", 1, 1, 0.15], ["sh:explorer_compass", 1, 1, 0.3], ["minecraft:bread", 2, 5, 0.9], ["minecraft:apple", 1, 3, 0.7], ["minecraft:torch", 4, 8, 0.6]],
  hokora: [["pick:sh:dawn_dagger|sh:shadow_blade|sh:shadow_claws|sh:ember_cleaver|sh:sunset_spear|sh:stone_maul", 1, 1, 1.0], ["sh:xp_scroll_small", 2, 3, 1.0], ["sh:explorer_compass", 1, 1, 0.5], ["minecraft:golden_apple", 1, 1, 0.4]],
  ruins_small: [["sh:xp_scroll_small", 1, 2, 1.0], ["pick:sh:ember_cleaver|sh:sunset_spear", 1, 1, 0.08], ["minecraft:iron_ingot", 2, 5, 0.7]],
  ruins: [["sh:xp_scroll_small", 1, 2, 1.0], ["sh:monster_book", 1, 1, 0.25], ["sh:explorer_compass", 1, 1, 0.3], ["pick:sh:ember_cleaver|sh:sunset_spear|sh:stone_maul", 1, 1, 0.12], ["minecraft:iron_ingot", 2, 5, 0.7], ["minecraft:cooked_porkchop", 2, 4, 0.6], ["minecraft:torch", 4, 8, 0.5]],
  palace: [["pick:sh:stone_maul|sh:sunset_spear|sh:ember_cleaver|sh:dawn_dagger|sh:shadow_blade|sh:shadow_claws", 1, 1, 0.15], ["sh:xp_scroll_big", 1, 1, 0.8], ["sh:explorer_compass", 1, 1, 0.5], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.5], ["minecraft:cooked_beef", 4, 8, 0.9], ["minecraft:emerald", 3, 6, 0.8], ["minecraft:iron_ingot", 4, 8, 0.7]],
  shrine: [["sh:dark_katana", 1, 1, 1.0], ["sh:xp_scroll_big", 1, 2, 1.0], ["sh:xp_scroll_small", 2, 3, 1.0], ["minecraft:golden_apple", 1, 1, 0.6], ["minecraft:diamond", 1, 2, 0.5]],
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
const SHRINE_PITY = 2;
function chooseType(reg = []) {
  if (STRUCTURES.shrine && !reg.some((s) => s.type === "shrine") && reg.length >= SHRINE_PITY) return "shrine";
  const roll = Math.random();
  let acc = 0;
  for (const [k, v] of Object.entries(STRUCTURES)) { acc += v.weight; if (roll < acc) return k; }
  return "village";
}

export function setupStructures(onGuardSpawn) {
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
        reg.push({ x: site.x, y: site.y, z: site.z, type, rot, seed });
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
        const job = system.runJob((function* () { try { yield* gen; } finally { building = false; } })());
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
