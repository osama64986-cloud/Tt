// إثيريا: تحويل مخطط المدينة (ops) لشبكة بلوكات بالذاكرة (Uint16 لكل خلية = رقم باللوحة، 0 = فراغ ما ينحط).
// نفس الكود يشتغل باللعبة (city.js) وبأدوات الفحص والرسم (node)، فالفحص يفحص اللي ينبني بالضبط.
// بعد التطبيق نحسب اتصالات الألواح والقضبان والجدران (بيدروك يخزنها كحالات بالبلوكة؛ بالبنية ما تنحسب لوحدها).
import { CITY_SIZE, CITY_YMIN, CITY_YMAX, hash3 } from "./city_plan.js";

export const RX = CITY_SIZE, RZ = CITY_SIZE, RY = CITY_YMAX - CITY_YMIN + 1;
export const ridx = (x, y, z) => ((y - CITY_YMIN) * RZ + z) * RX + x;

// مولّد: يطبق العمليات ويرجع (yield) كل شوية حتى ما يعلق اللعبة. النتيجة بـ out.grid
export function* rasterize(plan, out, budget = 40000) {
  const g = new Uint16Array(RX * RY * RZ);
  out.grid = g;
  let work = 0;
  const clip = (a, lo, hi) => (a < lo ? lo : a > hi ? hi : a);
  for (const op of plan.ops) {
    if (op[0] === 1) {
      const [, x, y, z, k] = op;
      if (x >= 0 && x < RX && z >= 0 && z < RZ && y >= CITY_YMIN && y <= CITY_YMAX) g[ridx(x, y, z)] = k;
      if (++work >= budget) { work = 0; yield; }
      continue;
    }
    const x1 = clip(op[1], 0, RX - 1), y1 = clip(op[2], CITY_YMIN, CITY_YMAX), z1 = clip(op[3], 0, RZ - 1);
    const x2 = clip(op[4], 0, RX - 1), y2 = clip(op[5], CITY_YMIN, CITY_YMAX), z2 = clip(op[6], 0, RZ - 1);
    if (op[1] > RX - 1 || op[4] < 0 || op[3] > RZ - 1 || op[6] < 0 || op[2] > CITY_YMAX || op[5] < CITY_YMIN) continue;
    if (op[0] === 0) {
      const k = op[7];
      for (let y = y1; y <= y2; y++) for (let z = z1; z <= z2; z++) {
        const base = ridx(0, y, z);
        for (let x = x1; x <= x2; x++) g[base + x] = k;
        work += x2 - x1 + 1;
        if (work >= budget) { work = 0; yield; }
      }
    } else {
      const ks = op[7], cum = op[8], salt = op[9];
      for (let y = y1; y <= y2; y++) for (let z = z1; z <= z2; z++) {
        const base = ridx(0, y, z);
        for (let x = x1; x <= x2; x++) {
          const h = hash3(x, y, z, salt);
          let i = 0;
          while (i < cum.length - 1 && h >= cum[i]) i++;
          g[base + x] = ks[i];
        }
        work += x2 - x1 + 1;
        if (work >= budget) { work = 0; yield; }
      }
    }
  }
  yield* connect(plan, g, budget);
}

const NONSOLID = /air$|water|lava|slab|stairs|fence|door|carpet|lantern|torch|ladder|:bed$|chest|poppy|dandelion|daisy|bluet|allium|cornflower|lily_of|tulip|short_grass|tall_grass|fern|sapling|pressure_plate|button|campfire|bell|anvil|lectern|cauldron|brewing|grindstone|enchanting|composter|lightning_rod|chain|flower_pot|wheat|carrots|potatoes|beetroot|bush|vine|grass_path|farmland|stonecutter|waterlily|reeds|peony|rose_bush|lilac|sunflower|cake|leaves|pumpkin|melon/;
// يحسب حالات الاتصال (بيدروك 1.26 يخزنها بالبلوكة؛ البنية ما تحسبها): ألواح الزجاج وقضبان الحديد، الجدران، والسياج
// 1 = لوح/قضبان (يتصل بلوح وجدار وبلوكة صلبة)، 2 = جدار (لوح، جدار، بوابة بنفس الاتجاه، صلب)، 4 = سياج خشب (سياج، بوابة بنفس الاتجاه، صلب)
// 5 = بوابة سياج (ما عندها حالات اتصال؛ بس السياج والجدار يتصلون بيها)، 3 = بلوكة صلبة كاملة
function* connect(plan, g, budget) {
  const kind = plan.pal.map((p) => {
    if (!p) return 0;
    if (/glass_pane$|iron_bars$/.test(p.id)) return 1;
    if (/_wall$/.test(p.id)) return 2;
    if (/fence_gate$/.test(p.id)) return 5;
    if (/_fence$/.test(p.id)) return 4;
    return NONSOLID.test(p.id) ? 0 : 3;
  });
  // محور البوابة: وجهها شمال/جنوب = ممتدة على x (تتصل شرق/غرب)
  const gateX = plan.pal.map((p) => !!(p && p.st && /north|south/.test(p.st["minecraft:cardinal_direction"] || "")));
  const cache = new Map();
  const at = (x, y, z) => (x < 0 || x >= RX || z < 0 || z >= RZ || y < CITY_YMIN || y > CITY_YMAX ? 0 : g[ridx(x, y, z)]);
  let work = 0;
  for (let y = CITY_YMIN; y <= CITY_YMAX; y++) for (let z = 0; z < RZ; z++) {
    const base = ridx(0, y, z);
    for (let x = 0; x < RX; x++) {
      const k = g[base + x];
      if (!k) continue;
      const t = kind[k];
      if (t !== 1 && t !== 2 && t !== 4) continue;
      const nk = [at(x + 1, y, z), at(x - 1, y, z), at(x, y, z - 1), at(x, y, z + 1)];  // شرق، غرب، شمال، جنوب
      const link = nk.map((q, i) => {
        const qt = q ? kind[q] : 0;
        if (qt === 3) return true;
        if (qt === 5) return t !== 1 && gateX[q] === i < 2;
        if (t === 4) return qt === 4;
        return qt === 1 || qt === 2;
      });
      const id = plan.pal[k].id;
      let st;
      if (t === 1 || t === 4) st = { "minecraft:connection_east": link[0], "minecraft:connection_west": link[1], "minecraft:connection_north": link[2], "minecraft:connection_south": link[3] };
      else {
        const above = at(x, y + 1, z), straight = (link[0] && link[1] && !link[2] && !link[3]) || (!link[0] && !link[1] && link[2] && link[3]);
        const post = !straight || (above && kind[above] !== 0) || (above && /lantern|torch/.test(plan.pal[above].id));
        const c = (b) => (b ? "short" : "none");
        st = { wall_connection_type_east: c(link[0]), wall_connection_type_west: c(link[1]), wall_connection_type_north: c(link[2]), wall_connection_type_south: c(link[3]), wall_post_bit: !!post };
      }
      const key = id + JSON.stringify(st);
      let nk2 = cache.get(key);
      if (nk2 === undefined) { nk2 = plan.k(id, st); cache.set(key, nk2); kind[nk2] = t; gateX[nk2] = false; }   // الجار اللي انحسب قبل يبقى بنفس النوع
      g[base + x] = nk2;
      if (++work >= budget) { work = 0; yield; }
    }
  }
}

// تقطيع لمربعات (≤ 64×64): يرجع حدود كل مربع
export function tiles(ts = 64) {
  const out = [];
  for (let z0 = 0; z0 < RZ; z0 += ts) for (let x0 = 0; x0 < RX; x0 += ts) out.push({ x0, z0, w: Math.min(ts, RX - x0), d: Math.min(ts, RZ - z0) });
  return out;
}
