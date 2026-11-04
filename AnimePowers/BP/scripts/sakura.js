// قرية الساكورا (مبنية من صورة المرجع): بيوت يابانية من خشب السبروس والكرز بسقوف بلاك ستون، معبد باغودا بالنص،
// بركة حلقية بجسور خشبية، مزرعة، أشجار كرز ضخمة، فوانيس بسلاسل، ومسارات من حصى وحجر.
// كل البلوكات أسماء ماينكرافت Bedrock الحقيقية (مفحوصة بـ tools/check_village.py ضد قائمة بلوكات اللعبة الرسمية).
// الإحداثيات محلية: y=-1 سطح الأرض (عشب)، y=0 أول بلوك فوقه، x شرق، z جنوب. كل بيت يُبنى بوضع قياسي (الباب جنوباً) ويدور.
const AIR = "minecraft:air";
const WATER = "minecraft:water";
const M = (n) => "minecraft:" + n;
const SEQ = ["e", "s", "w", "n"];
const CARD = { e: "east", s: "south", w: "west", n: "north" };
function rotXZ(x, z, rot) {
  if (rot === 1) return [-z, x];
  if (rot === 2) return [-x, -z];
  if (rot === 3) return [z, -x];
  return [x, z];
}

// عرض محلي: يحوّل إحداثيات قياسية (مع مرآة/دوران/رفع) لإحداثيات القرية
class View {
  constructor(P, cx, cz, rot = 0, mirror = false, dy = 0) { this.P = P; this.cx = cx; this.cz = cz; this.rot = rot; this.m = mirror; this.dy = dy; }
  tx(x, z) { if (this.m) x = -x; const [a, b] = rotXZ(x, z, this.rot); return [this.cx + a, this.cz + b]; }
  letter(l) { if (this.m && (l === "e" || l === "w")) l = l === "e" ? "w" : "e"; return SEQ[(SEQ.indexOf(l) + this.rot) % 4]; }
  card(l) { return CARD[this.letter(l)]; }
  box(x1, y1, z1, x2, y2, z2, id) {
    const [a, b] = this.tx(x1, z1), [c, d] = this.tx(x2, z2);
    this.P.box(Math.min(a, c), y1 + this.dy, Math.min(b, d), Math.max(a, c), y2 + this.dy, Math.max(b, d), id);
  }
  set(x, y, z, id) { const [a, b] = this.tx(x, z); this.P.set(a, y + this.dy, b, id); }
  stair(x, y, z, id, dir, up = false) { const [a, b] = this.tx(x, z); this.P.stair(a, y + this.dy, b, id, this.letter(dir), up); }
  perm(x, y, z, id, st) { const [a, b] = this.tx(x, z); this.P.perm(a, y + this.dy, b, id, st); }
  chest(x, y, z, key) { const [a, b] = this.tx(x, z); this.P.chest(a, y + this.dy, b, key); }
  bed(fx, y, fz, hx, hz) { const [a, b] = this.tx(fx, fz), [c, d] = this.tx(hx, hz); this.P.bed(a, y + this.dy, b, c, d); }
  hang(x, y, z, id = M("lantern")) { this.perm(x, y, z, id, { hanging: true }); }
  // سلسلة + فانوس معلق تحت بلوك سقف
  lamp(x, y, z) { this.perm(x, y + 1, z, M("iron_chain"), { pillar_axis: "y" }); this.hang(x, y, z); }
  slab(x, y, z, id, top = false) { this.perm(x, y, z, id, { "minecraft:vertical_half": top ? "top" : "bottom" }); }
  // لوح زجاج بحالات اتصال صريحة (axis: "x" الجدار ممتد على x، "z" على z)
  pane(x, y, z, axis, id = M("glass_pane")) {
    const st = axis === "x" ? { "minecraft:connection_east": true, "minecraft:connection_west": true, "minecraft:connection_north": false, "minecraft:connection_south": false }
      : { "minecraft:connection_east": false, "minecraft:connection_west": false, "minecraft:connection_north": true, "minecraft:connection_south": true };
    if (this.rot % 2 === 1) { const t = { ...st }; st["minecraft:connection_east"] = t["minecraft:connection_north"]; st["minecraft:connection_west"] = t["minecraft:connection_south"]; st["minecraft:connection_north"] = t["minecraft:connection_east"]; st["minecraft:connection_south"] = t["minecraft:connection_west"]; }
    this.perm(x, y, z, id, st);
  }
  door(x, y, z, id, outward) {
    const c = this.card(outward);
    this.perm(x, y, z, id, { "minecraft:cardinal_direction": c, door_hinge_bit: false, open_bit: false, upper_block_bit: false });
    this.perm(x, y + 1, z, id, { "minecraft:cardinal_direction": c, door_hinge_bit: false, open_bit: false, upper_block_bit: true });
  }
  // سقف هرمي أجوف بدرجات بلاك ستون: حلقة لكل طبقة (الزوايا بلوك صلب) وغطاء ألواح. R = نصف قطر الحلقة الأولى
  hip(R, y, layers, stairId, solidId, slabId) {
    for (let k = 0; k < layers; k++) {
      const r = R - k, yy = y + k;
      this.box(-r, yy, -r, r, yy, -r, solidId); this.box(-r, yy, r, r, yy, r, solidId);
      this.box(-r, yy, -r, -r, yy, r, solidId); this.box(r, yy, -r, r, yy, r, solidId);
      for (let i = -r + 1; i <= r - 1; i++) {
        this.stair(i, yy, -r, stairId, "s"); this.stair(i, yy, r, stairId, "n");
        this.stair(-r, yy, i, stairId, "e"); this.stair(r, yy, i, stairId, "w");
      }
    }
    const r = R - layers + 1;
    if (r >= 0) this.box(-r + 0, y + layers, -r, r, y + layers, r, slabId);
  }
}

// ═════════════════════════ بيت الساكورا (قياسي: الباب جنوباً، القدم 9×9، دورين) ═════════════════════════
// الأرضية الداخلية y=-1 (تصير y=0 بعد الرفع)، الجدران y=0..3، سقف الدور الأول/أرضية العلية y=4، علية تحت سقف هرمي بلاك ستون.
function sakuraHouse(V, variant, accent) {
  const SP = M("spruce_planks"), CP = M("cherry_planks"), DL = M("dark_oak_log"), DP = M("dark_oak_planks");
  const BS = M("blackstone_stairs"), BB = M("blackstone"), BSL = M("blackstone_slab"), ST = M("spruce_stairs");
  const CARPET = accent === "white" ? M("white_carpet") : M("pink_carpet");
  // ── الأساس: ساحة حجر بمستوى الأرض + منصة مرفوعة بلوكة ──
  V.box(-7, -2, -7, 7, -2, 7, M("stone_bricks"));
  for (const [x1, z1, x2, z2] of [[-7, -7, 7, -7], [-7, 7, 7, 7], [-7, -7, -7, 7], [7, -7, 7, 7]]) V.box(x1, -2, z1, x2, -2, z2, M("cobblestone"));
  V.box(-6, -1, -6, 6, -1, 6, M("stone_bricks"));
  for (const [x1, z1, x2, z2] of [[-6, -6, 6, -6], [-6, -6, -6, 6], [6, -6, 6, 6]]) V.box(x1, -1, z1, x2, -1, z2, M("cobblestone"));
  V.box(-4, -1, -4, 4, -1, 4, SP);                                                     // أرضية الدور الأول
  for (const [x1, z1, x2, z2] of [[-4, -4, 4, -4], [-4, 4, 4, 4], [-4, -4, -4, 4], [4, -4, 4, 4]]) V.box(x1, -1, z1, x2, -1, z2, DP);
  // ── الجدران: سبروس سفلي، ألواح كرز وردية، عارضة دارك أوك، وأعمدة ──
  for (const [x1, z1, x2, z2] of [[-4, -4, 4, -4], [-4, 4, 4, 4], [-4, -4, -4, 4], [4, -4, 4, 4]]) {
    V.box(x1, 0, z1, x2, 0, z2, SP); V.box(x1, 1, z1, x2, 2, z2, CP); V.box(x1, 3, z1, x2, 3, z2, DP);
  }
  for (const x of [-4, 4]) for (const z of [-4, 4]) V.box(x, 0, z, x, 3, z, DL);
  for (const x of [-1, 1]) V.box(x, 0, 4, x, 3, 4, DL);                                // إطار الباب
  V.box(0, 0, -4, 0, 3, -4, DL); V.box(-4, 0, 0, -4, 3, 0, DL); V.box(4, 0, 0, 4, 3, 0, DL);
  // شبابيك زجاج (حالات اتصال صريحة)
  for (const x of [-3, -2, 2, 3]) { V.pane(x, 1, 4, "x"); V.pane(x, 2, 4, "x"); }
  for (const x of [-3, -2, 2, 3]) { V.pane(x, 1, -4, "x"); V.pane(x, 2, -4, "x"); }
  for (const z of [-3, -2, 2, 3]) for (const x of [-4, 4]) { V.pane(x, 1, z, "z"); V.pane(x, 2, z, "z"); }
  // الباب (سبروس)
  V.box(0, 0, 4, 0, 2, 4, AIR); V.door(0, 0, 4, M("spruce_door"), "s"); V.set(0, 2, 4, CP);
  // ── سقف الدور الأول/أرضية العلية + عارضة الإفريز ──
  for (const [x1, z1, x2, z2] of [[-5, -5, 5, -5], [-5, 5, 5, 5], [-5, -5, -5, 5], [5, -5, 5, 5]]) V.box(x1, 4, z1, x2, 4, z2, DL);
  V.box(-4, 4, -4, 4, 4, 4, DP);
  // سقف هرمي أجوف من بلاك ستون (5 طبقات): الحلقة الأولى R=6 تبرز بلوكتين
  V.hip(6, 4, 5, BS, BB, BSL);
  // فوانيس معلقة بسلاسل من زوايا الإفريز
  for (const [x, z] of [[-6, 6], [6, 6], [-6, -6], [6, -6]]) V.lamp(x, 2, z);
  // ── الشرفة الأمامية + درج + أعمدة وفوانيس ──
  V.box(-3, -1, 5, 3, -1, 6, SP);
  for (const x of [-3, 3]) V.box(x, 0, 6, x, 3, 6, DL);
  for (const x of [-2, 2]) V.set(x, 0, 6, M("spruce_fence"));
  for (const x of [-1, 0, 1]) V.stair(x, -1, 7, ST, "n");
  V.lamp(-1, 2, 6); V.lamp(1, 2, 6);
  // ── الدور الأول: الداخل ──
  V.box(-1, 0, -1, 1, 0, 1, CARPET);
  // السلم (على z=2): من x=-3 للأعلى شرقاً حتى فتحة العلية
  V.stair(-3, 0, 2, ST, "e"); V.set(-2, 0, 2, SP); V.stair(-2, 1, 2, ST, "e");
  V.box(-1, 0, 2, -1, 1, 2, SP); V.stair(-1, 2, 2, ST, "e");
  V.box(0, 0, 2, 0, 2, 2, SP); V.stair(0, 3, 2, ST, "e");
  V.box(1, 0, 2, 1, 3, 2, SP); V.stair(1, 4, 2, ST, "e");
  V.box(-1, 4, 2, 0, 4, 2, AIR);                                                       // فتحة السقف فوق السلم
  // طاولة منخفضة (ألواح كرز) + زوايا جلوس
  for (const x of [-1, 0, 1]) V.slab(x, 0, 0, M("cherry_slab"));
  V.stair(0, 0, -1, M("cherry_stairs"), "n"); V.stair(0, 0, 1, M("cherry_stairs"), "s");
  // مطبخ: طاولة صناعة وفرنين (الركن الشمالي الشرقي)
  V.set(2, 0, -3, M("crafting_table"));
  V.perm(3, 0, -3, M("furnace"), { "minecraft:cardinal_direction": V.card("w") });
  V.perm(3, 0, -2, M("furnace"), { "minecraft:cardinal_direction": V.card("w") });
  V.set(1, 0, -3, M("composter"));
  V.set(3, 1, -3, M("lantern"));
  // مكتبة الجدار الغربي
  V.box(-3, 0, -3, -3, 1, -1, M("bookshelf"));
  V.perm(-3, 0, 0, M("lectern"), { "minecraft:cardinal_direction": V.card("e"), powered_bit: false });
  // سرير الدور الأول (على الجدار الشمالي)
  V.bed(-1, 0, -3, 0, -3);
  // صندوق 1 + زينة (أصيص طحلب بزهرة، أزالية مزهرة)
  V.chest(3, 0, 1, "house");
  V.set(3, 0, 2, M("flowering_azalea"));
  V.set(3, 0, 0, M("moss_block")); V.set(3, 1, 0, M("pink_tulip"));
  V.set(-3, 0, 3, M("moss_block")); V.set(-3, 1, 3, M("pink_tulip"));
  V.lamp(-2, 2, -2); V.lamp(2, 2, 0);
  // ── العلية (تحت السقف): سجادة، سرير، صندوق 2، طاولة خرائط ونول ──
  V.box(-2, 5, -2, 2, 5, 0, CARPET);
  V.bed(-2, 5, -2, -1, -2);
  V.set(-3, 5, 0, M("cartography_table"));
  V.set(-3, 5, 1, M("loom"));
  V.chest(3, 5, -3, "pantry");
  V.set(3, 5, 3, M("moss_block")); V.set(3, 6, 3, M("pink_tulip"));
  V.set(3, 5, -1, M("flowering_azalea"));
  V.lamp(0, 7, 0);
}

// ═════════════════════════ باغودا القاعة الرئيسية ═════════════════════════
function sakuraPagoda(V) {
  const SP = M("spruce_planks"), CP = M("cherry_planks"), DL = M("dark_oak_log"), DP = M("dark_oak_planks");
  const BS = M("blackstone_stairs"), BB = M("blackstone"), BSL = M("blackstone_slab");
  // منصة: ساحة ثم درجات حجر
  V.box(-10, -2, -10, 10, -2, 10, M("stone_bricks"));
  V.box(-9, -1, -9, 9, -1, 9, M("stone_bricks"));
  for (let i = -8; i <= 8; i++) { V.stair(i, -1, -10, M("stone_brick_stairs"), "s"); V.stair(i, -1, 10, M("stone_brick_stairs"), "n"); V.stair(-10, -1, i, M("stone_brick_stairs"), "e"); V.stair(10, -1, i, M("stone_brick_stairs"), "w"); }
  V.box(-9, -1, -9, -9, -1, 9, M("cobblestone")); V.box(9, -1, -9, 9, -1, 9, M("cobblestone")); V.box(-9, -1, -9, 9, -1, -9, M("cobblestone")); V.box(-9, -1, 9, 9, -1, 9, M("cobblestone"));
  const tiers = [{ h: 6, y: 0, wh: 4 }, { h: 5, y: 6, wh: 4 }, { h: 4, y: 12, wh: 4 }, { h: 3, y: 18, wh: 4 }];
  tiers.forEach((t, k) => {
    const h = t.h, y = t.y, top = y + t.wh;           // top = مستوى السقف (بلوك العارضة)
    V.box(-h, y - (k === 0 ? 1 : 0), -h, h, y - (k === 0 ? 1 : 0), h, SP);
    V.box(-h + 1, y, -h + 1, h - 1, top, h - 1, AIR);
    // الجدران: لوح سفلي سبروس، كرز، عارضة
    for (const [x1, z1, x2, z2] of [[-h, -h, h, -h], [-h, h, h, h], [-h, -h, -h, h], [h, -h, h, h]]) {
      V.box(x1, y, z1, x2, y, z2, SP); V.box(x1, y + 1, z1, x2, top - 1, z2, CP); V.box(x1, top, z1, x2, top, z2, DP);
    }
    for (const x of [-h, h]) for (const z of [-h, h]) V.box(x, y, z, x, top, z, DL);
    for (let p = -h + 3; p < h; p += 3) { for (const z of [-h, h]) V.box(p, y, z, p, top, z, DL); for (const x of [-h, h]) V.box(x, y, p, x, top, p, DL); }
    // شبابيك
    for (let p = -h + 1; p < h; p++) {
      if ((p + h) % 3 === 0) continue;
      for (let yy = y + 1; yy <= top - 1; yy++) { if (yy > y + 2) continue; V.pane(p, yy, -h, "x"); if (!(k === 0 && Math.abs(p) <= 0)) V.pane(p, yy, h, "x"); V.pane(-h, yy, p, "z"); V.pane(h, yy, p, "z"); }
    }
    // سقف الطبقة: حلقة أولى (R=h+2) وحلقة ثانية، السقف الداخلي مصمت
    V.box(-h - 1, top, -h - 1, h + 1, top, -h - 1, DL); V.box(-h - 1, top, h + 1, h + 1, top, h + 1, DL);
    V.box(-h - 1, top, -h - 1, -h - 1, top, h + 1, DL); V.box(h + 1, top, -h - 1, h + 1, top, h + 1, DL);
    V.box(-h, top, -h, h, top, h, DP);
    const layers = k === 3 ? 4 : 2;
    V.hip(h + 2, top, layers, BS, BB, BSL);
    if (k < 3) V.box(-h, top + 1, -h, h, top + 1, h, SP);          // أرضية الطبقة التالية
    // فوانيس معلقة بالزوايا
    for (const x of [-h - 2, h + 2]) for (const z of [-h - 2, h + 2]) { V.set(x, top - 1, z, M("dark_oak_fence")); V.lamp(x, top - 2, z); }
  });
  // فتحة الباب الرئيسي + باب مزدوج
  V.box(-1, 0, 6, 1, 2, 6, AIR); V.box(-1, 3, 6, 1, 3, 6, DP);                           // مدخل مفتوح بعرض 3
  // داخل القاعة: سجادة وردية، مذبح من خشب الكرز، فوانيس
  V.box(-3, 0, -5, 3, 0, 4, AIR);
  V.box(-1, -1, -4, 1, -1, 5, M("pink_carpet"));
  V.box(-3, 0, -5, 3, 0, -5, M("cherry_planks")); V.box(-2, 0, -4, 2, 0, -4, M("cherry_slab"));
  V.chest(0, 1, -5, "hokora");
  for (const x of [-3, 3]) { V.set(x, 1, -5, M("lantern")); V.set(x, 0, -3, M("cherry_log")); V.set(x, 1, -3, M("cherry_log")); V.set(x, 2, -3, M("lantern")); }
  for (const x of [-4, 4]) { V.set(x, 0, 2, M("flowering_azalea")); V.set(x, 0, -1, M("moss_block")); V.set(x, 1, -1, M("pink_tulip")); }
  V.lamp(0, 3, 0); V.lamp(-3, 3, 2); V.lamp(3, 3, 2);
  // قمة: عمود دارك أوك وفانوس وجرس
  const ty = tiers[3].y + tiers[3].wh + 4 + 1;
  V.box(0, ty, 0, 0, ty + 3, 0, M("dark_oak_fence")); V.set(0, ty + 4, 0, M("lantern"));
  V.set(0, ty - 1, 0, M("cherry_log"));
}

// ═════════════════════════ جسر خشبي مقوس بدرابزين وفوانيس (قياسي: يمتد على x من 9 إلى 16) ═════════════════════════
function sakuraBridge(V) {
  const SP = M("spruce_planks"), DL = M("dark_oak_log"), SS = M("spruce_stairs");
  V.box(10, -1, -1, 15, -1, 1, SP);
  V.stair(16, -1, -1, SS, "w"); V.stair(16, -1, 0, SS, "w"); V.stair(16, -1, 1, SS, "w");
  V.box(10, 0, -1, 15, 0, 1, AIR);
  V.box(10, 0, -2, 15, 0, -2, M("spruce_fence")); V.box(10, 0, 2, 15, 0, 2, M("spruce_fence"));
  V.box(10, -1, -2, 15, -1, -2, SP); V.box(10, -1, 2, 15, -1, 2, SP);
  for (const x of [10, 15]) for (const z of [-2, 2]) { V.box(x, 0, z, x, 1, z, DL); V.set(x, 2, z, M("lantern")); }
  for (const x of [12, 13]) for (const z of [-2, 2]) V.set(x, 1, z, M("spruce_fence"));
  // أقواس تحت الجسر
  V.box(11, -2, -1, 14, -2, 1, M("spruce_planks"));
}

// ═════════════════════════ مزرعة محاطة بسياج ═════════════════════════
function sakuraFarm(V) {
  V.box(-7, -1, -7, 7, -1, 7, M("grass_block"));
  // صفوف (z): ماء عند -2 و 2، والباقي تربة محروثة بمحاصيل ناضجة
  const rows = { "-4": "wheat", "-3": "wheat", "-1": "carrots", "0": "carrots", "1": "potatoes", "3": "beetroot", "4": "beetroot" };
  for (const [zs, crop] of Object.entries(rows)) {
    const z = Number(zs);
    V.box(-5, -1, z, 5, -1, z, M("dirt"));
    for (let x = -5; x <= 5; x++) { V.perm(x, -1, z, M("farmland"), { moisturized_amount: 7 }); V.perm(x, 0, z, M(crop), { growth: 7 }); }
  }
  for (const z of [-2, 2]) { V.box(-5, -1, z, 5, -1, z, WATER); for (let x = -5; x <= 5; x += 4) V.set(x, 0, z, M("spruce_slab")); }
  // سياج + بوابة غربية + فوانيس
  V.box(-7, 0, -7, 7, 0, -7, M("spruce_fence")); V.box(-7, 0, 7, 7, 0, 7, M("spruce_fence"));
  V.box(-7, 0, -7, -7, 0, 7, M("spruce_fence")); V.box(7, 0, -7, 7, 0, 7, M("spruce_fence"));
  V.box(-7, 0, 0, -7, 0, 0, AIR); V.perm(-7, 0, 0, M("spruce_fence_gate"), { "minecraft:cardinal_direction": V.card("e"), open_bit: false, in_wall_bit: false });
  for (const [x, z] of [[-7, -7], [7, -7], [-7, 7], [7, 7]]) { V.box(x, 0, z, x, 1, z, M("dark_oak_log")); V.set(x, 2, z, M("lantern")); }
  // مخزن: قش وبراميل ومخمرة (زينة)
  V.set(6, 0, -6, M("hay_block")); V.set(6, 1, -6, M("hay_block")); V.set(6, 0, -5, M("hay_block"));
  V.set(-6, 0, -6, M("barrel")); V.set(-6, 0, -5, M("composter"));
  // فزاعة
  V.set(0, -1, -6, M("coarse_dirt")); V.box(0, 0, -6, 0, 1, -6, M("spruce_fence")); V.set(0, 2, -6, M("hay_block"));
  V.set(-1, 1, -6, M("spruce_fence")); V.set(1, 1, -6, M("spruce_fence")); V.set(0, 3, -6, M("carved_pumpkin"));
}

// ═════════════════════════ بوابة دخول القرية (كابوكيمون) ═════════════════════════
function sakuraGate(V) {
  const DL = M("dark_oak_log"), DP = M("dark_oak_planks"), BS = M("blackstone_stairs"), BB = M("blackstone"), BSL = M("blackstone_slab");
  V.box(-5, -1, -2, 5, -1, 2, M("stone_bricks"));
  for (const x of [-4, 4]) for (const z of [-1, 1]) V.box(x, 0, z, x, 6, z, DL);
  V.box(-4, 5, -1, 4, 5, -1, DP); V.box(-4, 5, 1, 4, 5, 1, DP);
  V.box(-4, 6, -1, 4, 6, 1, DP);
  V.box(-5, 7, -2, 5, 7, 2, BB);
  for (let x = -4; x <= 4; x++) { V.stair(x, 7, -3, BS, "s"); V.stair(x, 7, 3, BS, "n"); }
  V.box(-3, 8, -1, 3, 8, 1, BB); V.box(-2, 9, 0, 2, 9, 0, BSL);
  for (const x of [-4, 4]) { V.set(x, 8, -2, BSL); V.set(x, 8, 2, BSL); }
  V.lamp(-2, 3, 0); V.lamp(2, 3, 0);
  V.box(-4, 0, 0, -4, 3, 0, AIR);
}

// ═════════════════════════ شجرة كرز ضخمة: جذع سميك بفروع وتاج من 4 كرات ═════════════════════════
function cherryTree(P, x, z, h, size = 1) {
  const L = M("cherry_leaves");
  const ball = (cx, cy, cz, r) => {
    for (let dy = -r; dy <= r; dy++) {
      const rr = Math.floor(Math.sqrt(r * r - dy * dy + 0.5));
      for (let dz = -rr; dz <= rr; dz++) {
        const w = Math.floor(Math.sqrt(Math.max(0, rr * rr - dz * dz + 0.5)));
        P.box(cx - w, cy + dy, cz + dz, cx + w, cy + dy, cz + dz, L);
      }
    }
  };
  const r0 = size > 1 ? 4 : 3;
  ball(x, h, z, r0); ball(x + 3, h - 1, z + 1, r0 - 1); ball(x - 3, h - 1, z - 1, r0 - 1); ball(x + 1, h + 2, z - 2, r0 - 1);
  if (size > 1) { ball(x - 2, h, z + 3, r0 - 1); ball(x + 2, h - 1, z - 3, r0 - 1); }
  P.box(x, 0, z, x, h, z, M("cherry_log"));
  if (size > 1) { P.box(x + 1, 0, z, x + 1, 3, z, M("cherry_log")); P.box(x, 0, z + 1, x, 2, z + 1, M("cherry_log")); }
  P.box(x + 1, h - 2, z, x + 3, h - 2, z, M("cherry_wood")); P.box(x - 3, h - 3, z, x - 1, h - 3, z, M("cherry_wood"));
  P.box(x, h - 3, z + 1, x, h - 3, z + 3, M("cherry_wood"));
  P.box(x - 1, h, z - 1, x + 1, h + 1, z + 1, M("cherry_log"));
  // بتلات على الأرض
  for (let i = 0; i < 9; i++) {
    const dx = Math.round((P.r() - 0.5) * 9), dz = Math.round((P.r() - 0.5) * 9);
    if (P.free(x + dx, z + dz)) { P.perm(x + dx, 0, z + dz, M("pink_petals"), { growth: Math.floor(P.r() * 4), "minecraft:cardinal_direction": ["south", "west", "north", "east"][Math.floor(P.r() * 4)] }); P.occ.add(`${x + dx},${z + dz}`); }
  }
}

// ═════════════════════════ القرية كاملة (77×77): باغودا بالنص، بركة حلقية بأربع جسور، طريق دائري، 6 بيوت، مزرعة، ساحة وبوابة ═════════════════════════
export const SAKURA_HALF = 38;
export function buildSakuraVillage(P) {
  const H = SAKURA_HALF;
  P.ground(-H, -H, H, H, 36);
  const PATHS = [[M("grass_path"), 0.5], [M("gravel"), 0.28], [M("cobblestone"), 0.12], [M("stone_bricks"), 0.1]];
  const path = (x1, z1, x2, z2) => {
    for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) for (let z = Math.min(z1, z2); z <= Math.max(z1, z2); z++) {
      if (P.occ.has(`${x},${z}`)) continue;
      let roll = P.r(), id = PATHS[0][0];
      for (const [b, w] of PATHS) { if (roll < w) { id = b; break; } roll -= w; }
      P.set(x, -1, z, id); P.occ.add(`${x},${z}`);
    }
  };
  // 1) البركة الحلقية حول الباغودا: ماء من 12 إلى 14، ضفة حجر داخلية عند 11، وضفة طحلب خارجية عند 15
  P.box(-15, -2, -15, 15, -2, 15, M("clay"));
  P.box(-14, -2, -14, 14, -1, 14, WATER);
  P.box(-10, -2, -10, 10, -2, 10, M("dirt")); P.box(-10, -1, -10, 10, -1, 10, M("grass_block"));
  for (const [x1, z1, x2, z2] of [[-15, -15, 15, -15], [-15, 15, 15, 15], [-15, -15, -15, 15], [15, -15, 15, 15]]) P.box(x1, -1, z1, x2, -1, z2, M("mossy_cobblestone"));
  for (const [x1, z1, x2, z2] of [[-11, -11, 11, -11], [-11, 11, 11, 11], [-11, -11, -11, 11], [11, -11, 11, 11]]) P.box(x1, -1, z1, x2, -1, z2, M("stone_bricks"));
  P.reserve(-15, -15, 15, 15);
  // 2) الباغودا (القاعة الرئيسية) + جسور على المحاور الأربعة + زنابق ماء
  sakuraPagoda(new View(P, 0, 0, 0, false, 1));
  for (let i = 0; i < 10; i++) { P.set(-13 + i * 3 - (i % 3), 0, i % 2 ? -13 : 13, M("waterlily")); P.set(i % 2 ? 13 : -13, 0, -12 + i * 2 + (i % 3), M("waterlily")); }
  for (const rot of [0, 1, 2, 3]) sakuraBridge(new View(P, 0, 0, rot, false, 1));
  // 3) البيوت الستة (أبوابها نحو الطريق الدائري)
  const houses = [[-26, -26, 0, "pink", 0], [26, -26, 0, "pink", 1], [0, -26, 0, "white", 0], [-26, 0, 3, "pink", 1], [26, 0, 1, "white", 0], [-26, 26, 2, "pink", 0]];
  for (const [cx, cz, rot, acc, mir] of houses) { P.reserve(cx - 8, cz - 8, cx + 8, cz + 8); sakuraHouse(new View(P, cx, cz, rot, !!mir, 1), 0, acc); }
  // 4) المزرعة (الجنوب الشرقي) + ساحة الدخول + البوابة
  P.reserve(18, 18, 34, 34); sakuraFarm(new View(P, 26, 26, 0, false, 0));
  P.reserve(-6, 19, 6, 33);
  P.box(-6, -1, 19, 6, -1, 33, M("stone_bricks")); P.box(-5, -1, 20, 5, -1, 32, M("polished_andesite"));
  P.chozuya(0, 26);
  for (const [x, z] of [[-5, 20], [5, 20], [-5, 32], [5, 32]]) P.toro(x, z);
  P.reserve(-6, 34, 6, 38); sakuraGate(new View(P, 0, 35, 0, false, 1));
  // 5) المسارات: طريق دائري حول البركة (16-17)، وصلات الأبواب، ومحور الجنوب نحو الساحة، وطريق المزرعة
  path(-17, -17, 17, -16); path(-17, 16, 17, 17); path(-17, -17, -16, 17); path(16, -17, 17, 17);
  path(-1, 18, 1, 19);
  path(-27, -19, -17, -17); path(17, -19, 27, -17); path(-1, -19, 1, -17);              // أبواب الشمال
  path(-19, -1, -17, 1); path(17, -1, 19, 1);                                            // الغرب والشرق
  path(-27, 17, -17, 19);                                                                // الجنوب الغربي
  path(7, 25, 18, 27);                                                                   // طريق المزرعة
  // 6) أشجار كرز ضخمة بين البيوت وحول القرية، وزهور وحشائش
  const trees = [[-13, -27, 8, 2], [13, -27, 8, 2], [-26, -13, 8, 2], [26, -13, 8, 2], [-26, 13, 7, 1], [26, 12, 7, 2], [-14, 28, 7, 1], [14, 31, 7, 1],
    [-36, -10, 7, 1], [-36, 14, 7, 1], [36, -12, 7, 1], [-12, -36, 7, 1], [12, -36, 7, 1], [-36, -36, 7, 1], [36, -36, 7, 1], [-36, 36, 7, 1], [37, 14, 7, 1],
    [-22, -14, 6, 1], [22, -14, 6, 1], [-22, 14, 6, 1], [-14, -21, 6, 1], [14, -21, 6, 1]];
  for (const [x, z, h, size] of trees) { if (P.free(x, z)) { cherryTree(P, x, z, h, size); P.reserve(x - 1, z - 1, x + 1, z + 1); } }
  const FL = [M("pink_tulip"), M("cornflower"), M("allium"), M("azalea"), M("flowering_azalea"), M("short_grass"), M("fern"), M("short_grass"), M("short_grass")];
  for (let i = 0; i < 520; i++) {
    const x = Math.round((P.r() - 0.5) * 2 * (H - 1)), z = Math.round((P.r() - 0.5) * 2 * (H - 1));
    if (!P.free(x, z)) continue;
    const roll = P.r();
    if (roll < 0.14) { P.perm(x, 0, z, M("peony"), { upper_block_bit: false }); P.perm(x, 1, z, M("peony"), { upper_block_bit: true }); }
    else if (roll < 0.22) { P.perm(x, 0, z, M("lilac"), { upper_block_bit: false }); P.perm(x, 1, z, M("lilac"), { upper_block_bit: true }); }
    else if (roll < 0.36) P.perm(x, 0, z, M("pink_petals"), { growth: Math.floor(P.r() * 4) });
    else P.set(x, 0, z, FL[Math.floor(P.r() * FL.length)]);
    P.occ.add(`${x},${z}`);
  }
  // 7) أعمدة فوانيس على الطريق الدائري
  for (const [x, z] of [[-18, -18], [18, -18], [-18, 18], [18, 18], [-18, 0], [18, 0], [0, -18], [0, 18], [-3, 20], [3, 20]]) {
    if (!P.free(x, z) && Math.abs(x) < 16 && Math.abs(z) < 16) continue;
    P.box(x, 0, z, x, 2, z, M("spruce_fence")); P.set(x, 3, z, M("lantern"));
  }
}
