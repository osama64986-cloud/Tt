// ضريحا السيف (النور والظلام): ساحتا قتال مفتوحتان للسما بحجم 45×45، مبنيتان من صورة المرجع.
// الخطة المحلية: y=0 سطح المنصة، x شرق، z جنوب (المدخل جنوباً +z)، المركز (0,0). المنصة ±22 (45 بلوكة) على أساس صلب لين y=-10.
//   • 12 عمود: 4 بالأركان (28 بلوكة)، 4 بجنب الأضلاع (22)، 4 جنب المدخل والخلف (18)، كل واحد قاعدة 5×5 وجذع 3×3 وأطواق وتاج.
//   • المركز: منصة ثلاث درجات (11×11 ثم 7×7 ثم 3×3) وفوقها منارة (beacon) يطلع منها عمود نور للسما (ذهبي للنور، بنفسجي للظلام)
//   • أرضية بنقوش: إطار خارجي، حلقات ماسية (diamond) حول المركز، محاور، ممر دخول جنوب، وأربع برك (النور) أو أقواس أميثست (الظلام) بالأركان.
//   • بدون سقف ولا غرف ولا بيوت ولا أسرة ولا صناديق: الصندوق يظهر لما يموت الحارسان (انظر structures.js).
// كل البلوكات أسماء Bedrock حقيقية (يفحصها tools/check_shrines.py ضد قوائم Mojang).
const AIR = "minecraft:air";
const WATER = "minecraft:water";
export const SHRINE_HALF = 23;               // نصف عرض المنطقة المطلوبة (المنصة ±22 + بلوكة تنظيف)
const R = 22;                                // نصف عرض المنصة

const abs = Math.abs;
// حلقة (فارغة) 5×5 بالارتفاع y حول (cx,cz)
function ring5(P, cx, cz, y, id) {
  P.box(cx - 2, y, cz - 2, cx + 2, y, cz - 2, id); P.box(cx - 2, y, cz + 2, cx + 2, y, cz + 2, id);
  P.box(cx - 2, y, cz - 1, cx - 2, y, cz + 1, id); P.box(cx + 2, y, cz - 1, cx + 2, y, cz + 1, id);
}
// يحول دالة (x,z)→بلوك لصفوف boxes (أقل عدد أوامر)
function floorRows(P, fn, y = 0) {
  for (let z = -R; z <= R; z++) {
    let x = -R;
    while (x <= R) {
      const id = fn(x, z);
      let x2 = x;
      while (x2 + 1 <= R && fn(x2 + 1, z) === id) x2++;
      P.box(x, y, z, x2, y, z, id);
      x = x2 + 1;
    }
  }
}
// هاش ثابت (لتوزيع بلوكات متشققة)
const hash = (x, z) => (((x * 73856093) ^ (z * 19349663)) >>> 0) % 17;

// ───────────── الأعمدة ─────────────
// T = {p1, p2, pc, shaft, dots, collar, band, capA, capB, capC, glow}
function pillar(P, cx, cz, H, T) {
  P.box(cx - 2, 1, cz - 2, cx + 2, 1, cz + 2, T.p1);                         // قاعدة 5×5
  P.box(cx - 2, 2, cz - 2, cx + 2, 2, cz + 2, T.p2);
  for (const [dx, dz] of [[-2, -2], [2, -2], [-2, 2], [2, 2]]) P.set(cx + dx, 2, cz + dz, T.pc);   // زوايا القاعدة
  P.box(cx - 1, 3, cz - 1, cx + 1, H - 4, cz + 1, T.shaft);                  // الجذع 3×3
  for (let y = 6; y <= H - 7; y += 6) ring5(P, cx, cz, y, T.collar);         // أطواق كل 6 بلوكات
  if (T.dots) for (let y = 4; y <= H - 6; y += 4) for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) P.set(cx + dx, y, cz + dz, T.dots);   // نقاط مضيئة بمنتصف الأوجه
  P.box(cx - 2, H - 3, cz - 2, cx + 2, H - 3, cz + 2, T.capA);                // تاج: طوق 5×5
  P.box(cx - 1, H - 2, cz - 1, cx + 1, H - 2, cz + 1, T.capB);
  P.box(cx - 1, H - 1, cz - 1, cx + 1, H - 1, cz + 1, T.capC);
  P.set(cx, H - 1, cz, T.glow);                                              // قلب مضيء
  if (T.tip) P.perm(cx, H, cz, T.tip, T.tipStates);
}

// ───────────── المنصة المركزية + المنارة ─────────────
// T = {t1, t1e, t2, t2e, core, post, postTop, stairs1, stairs2, glass}
function pedestal(P, T) {
  P.box(-5, 1, -5, 5, 1, 5, T.t1);                                            // الدرجة 1: 11×11
  for (let i = -5; i <= 5; i++) for (const [x, z] of [[i, -5], [i, 5], [-5, i], [5, i]]) P.set(x, 1, z, T.t1e);
  P.box(-3, 2, -3, 3, 2, 3, T.t2);                                            // الدرجة 2: 7×7
  for (let i = -3; i <= 3; i++) for (const [x, z] of [[i, -3], [i, 3], [-3, i], [3, i]]) P.set(x, 2, z, T.t2e);
  P.box(-1, 3, -1, 1, 3, 1, T.core);                                          // قاعدة المنارة 3×3
  P.set(0, 4, 0, "minecraft:beacon");
  P.set(0, 5, 0, T.glass);                                                    // زجاج ملوّن فوقها يلوّن العمود
  P.box(0, 6, 0, 0, 120, 0, AIR);                                             // سما مفتوحة فوق المنارة (حتى ما يوقفها شي)
  for (const [x, z] of [[-3, -3], [3, -3], [-3, 3], [3, 3]]) { P.box(x, 3, z, x, 4, z, T.post); P.set(x, 5, z, T.postTop); }   // أعمدة صغيرة بزوايا الدرجة 2
  for (let i = -2; i <= 2; i++) {                                             // درجات الصعود من الجهات الأربع
    P.stair(i, 1, 6, T.stairs1, "n"); P.stair(i, 1, -6, T.stairs1, "s"); P.stair(6, 1, i, T.stairs1, "w"); P.stair(-6, 1, i, T.stairs1, "e");
  }
  for (let i = -1; i <= 1; i++) {
    P.stair(i, 2, 4, T.stairs2, "n"); P.stair(i, 2, -4, T.stairs2, "s"); P.stair(4, 2, i, T.stairs2, "w"); P.stair(-4, 2, i, T.stairs2, "e");
  }
}

// عمود إنارة جنب الممر: جذع 3 بلوكات + ضوء
function lampPost(P, x, z, shaft, top) {
  P.box(x, 1, z, x, 3, z, shaft); P.set(x, 4, z, top);
}

function clearAndFoundation(P, base) {
  P.box(-R - 1, -1, -R - 1, R + 1, 40, R + 1, AIR);                          // ننضف الأشجار والتلال فوق المنطقة
  P.box(-R, -10, -R, R, -1, R, base);                                         // أساس صلب (يخفي فروق الأرض)
}

// ═════════════════════════════ ضريح سيف النور ═════════════════════════════
export function buildLightShrine(P) {
  const QB = "minecraft:quartz_bricks", SQ = "minecraft:smooth_quartz", QZ = "minecraft:quartz_block", CQ = "minecraft:chiseled_quartz_block";
  const GOLD = "minecraft:gold_block", SEA = "minecraft:sea_lantern", MOSS = "minecraft:moss_block";
  clearAndFoundation(P, SQ);
  const pools = [[-14, -14], [14, -14], [-14, 14], [14, 14]];
  // برك الماء 5×5 بالأركان: قاع فانوس بحري يضيء الماء من تحت
  for (const [cx, cz] of pools) {
    P.box(cx - 2, -2, cz - 2, cx + 2, -2, cz + 2, SEA);
    P.box(cx - 2, -1, cz - 2, cx + 2, -1, cz + 2, WATER);
  }
  const floor = (x, z) => {
    const ax = abs(x), az = abs(z), r = Math.max(ax, az), m = ax + az;
    for (const [cx, cz] of pools) {                                          // البرك وإطارها 7×7 (زوايا ذهب، وأطراف كوارتز منقوش)
      const dx = abs(x - cx), dz = abs(z - cz);
      if (dx <= 2 && dz <= 2) return WATER;
      if (dx <= 3 && dz <= 3) return dx === 3 && dz === 3 ? GOLD : CQ;
    }
    if (z >= 6 && ax <= 2) return ax === 2 ? QB : (ax === 0 && z % 2 === 0 ? CQ : SQ);   // ممر الدخول (جنوب)
    if (r === R) return GOLD;                                                // الحافة الخارجية
    if (r === 21) return QZ;
    if (r === 20) return (ax + az) % 4 === 0 ? GOLD : SQ;
    if (r === 19) return QZ;
    if (r === 18) return MOSS;
    if (r === 17) return SQ;
    if ((ax === 0 || az === 0) && m >= 6) return r % 2 === 0 ? CQ : QB;     // المحاور (صليب أبيض)
    if (m <= 5) return GOLD;
    if (m <= 18) return [QB, GOLD, SQ, m % 2 === 0 ? SEA : SQ, MOSS, SQ, GOLD, CQ, SQ, MOSS, SQ, GOLD, GOLD, SQ, MOSS, SQ, GOLD][m - 6];   // حلقات ماسية (diamond) ذهب/كوارتز/أخضر مثل المرجع
    if (ax % 6 === 0 && az % 6 === 0) return GOLD;                           // نقاط ذهب بالساحة
    return QZ;
  };
  floorRows(P, floor);
  // الأعمدة: 4 أركان 28، 4 جوانب 22، 4 قدام وخلف 18
  const T = { p1: SQ, p2: QB, pc: GOLD, shaft: "minecraft:quartz_pillar", collar: GOLD, capA: GOLD, capB: GOLD, capC: GOLD, glow: SEA, tip: "minecraft:end_rod", tipStates: { facing_direction: 1 } };
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    pillar(P, sx * 20, sz * 20, 28, T);
    pillar(P, sx * 20, sz * 7, 22, T);
    pillar(P, sx * 8, sz * 20, 18, T);
  }
  pedestal(P, { t1: SQ, t1e: QB, t2: QB, t2e: CQ, core: GOLD, post: "minecraft:quartz_pillar", postTop: SEA, stairs1: "minecraft:quartz_stairs", stairs2: "minecraft:quartz_stairs", glass: "minecraft:yellow_stained_glass" });
  for (const z of [8, 12, 16, 20]) for (const x of [-3, 3]) lampPost(P, x, z, "minecraft:quartz_pillar", SEA);   // أعمدة إنارة جنب الممر
  for (let x = -3; x <= 3; x++) P.stair(x, 0, 23, "minecraft:quartz_stairs", "n");                                   // درجة الدخول
  P.mob(-8, 1, -6, "sh:veilfox"); P.mob(8, 1, -6, "sh:magmamoth");
  P.reward(0, 3, 2, "lightshrine");
  return P;
}

// ═════════════════════════════ ضريح سيف الظلام ═════════════════════════════
export function buildDarkShrine(P) {
  const DB = "minecraft:deepslate_bricks", CDB = "minecraft:cracked_deepslate_bricks", DT = "minecraft:deepslate_tiles", CDT = "minecraft:cracked_deepslate_tiles";
  const PB = "minecraft:polished_blackstone", OBS = "minecraft:obsidian", CRY = "minecraft:crying_obsidian", AME = "minecraft:amethyst_block", PW = "minecraft:purple_wool";
  clearAndFoundation(P, DB);
  const floor = (x, z) => {
    const ax = abs(x), az = abs(z), r = Math.max(ax, az), m = ax + az;
    // أقواس أميثست بالأركان (على شكل L متجهة للمركز) مكان البرك بضريح النور
    if (ax >= 11 && ax <= 17 && az >= 11 && az <= 17) {                       // قوس L بالزاوية: ذراعين بعرض 2 على الحافتين الخارجيتين، والكوع بلور باكي
      if (ax >= 16 && az >= 16) return CRY;
      if (ax >= 16 || az >= 16) return AME;
      return ax === 11 || az === 11 ? OBS : DT;
    }
    if (z >= 6 && ax <= 2) return ax === 2 ? (z % 4 === 0 ? CRY : PW) : PB;     // ممر الدخول
    if (r === R) return OBS;                                                    // الحافة الخارجية
    if (r === 21) return DB;
    if (r === 20) return (ax + az) % 6 === 0 ? CRY : PB;
    if (r === 19) return DB;
    if (r === 18) return CDB;
    if (r === 17) return DT;
    if ((ax === 0 || az === 0) && m >= 6) return r % 3 === 0 ? CRY : PW;        // المحاور
    if (m <= 5) return CRY;
    if (m <= 18) return [OBS, AME, AME, OBS, PW, PW, OBS, AME, OBS, PW, OBS, AME, AME, OBS, PW, OBS, AME][m - 6];   // حلقات ماسية: أوبسيديان/أميثست/صوف بنفسجي
    if (ax % 6 === 0 && az % 6 === 0) return CRY;                            // بلورات تتوهج بالساحة
    return hash(ax, az) === 0 ? CDT : DT;
  };
  floorRows(P, floor);
  const T = { p1: DB, p2: PB, pc: CRY, shaft: DB, dots: AME, collar: OBS, capA: OBS, capB: AME, capC: CRY, glow: AME, tip: "minecraft:amethyst_cluster", tipStates: { "minecraft:block_face": "up" } };
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    pillar(P, sx * 20, sz * 20, 28, T);
    pillar(P, sx * 20, sz * 7, 22, T);
    pillar(P, sx * 8, sz * 20, 18, T);
  }
  pedestal(P, { t1: DB, t1e: PB, t2: PB, t2e: OBS, core: "minecraft:netherite_block", post: OBS, postTop: CRY, stairs1: "minecraft:deepslate_brick_stairs", stairs2: "minecraft:polished_blackstone_brick_stairs", glass: "minecraft:purple_stained_glass" });
  for (const z of [8, 12, 16, 20]) for (const x of [-3, 3]) lampPost(P, x, z, DB, CRY);
  for (let x = -3; x <= 3; x++) P.stair(x, 0, 23, "minecraft:deepslate_brick_stairs", "n");
  P.mob(-8, 1, -6, "sh:gloomhorn"); P.mob(8, 1, -6, "sh:hollow_seer");
  P.reward(0, 3, 2, "shrine");
  return P;
}
