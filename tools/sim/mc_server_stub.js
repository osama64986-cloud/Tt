// عالم ماينكرافت وهمي بالحد الأدنى لتشغيل سكربتات المود خارج اللعبة
import fs from "node:fs";
import path from "node:path";

const subs = {};
const ev = (name) => ({ subscribe: (fn) => { (subs[name] = subs[name] || []).push(fn); return fn; }, unsubscribe() {} });
const evProxy = () => new Proxy({}, { get: (t, k) => (t[k] = t[k] || ev(String(k))) });

// ───── مجدول التكات ─────
let tick = 0, nextId = 1;
const tasks = new Map();
export const system = {
  get currentTick() { return tick; },
  runInterval(fn, every = 1) { const id = nextId++; tasks.set(id, { fn, every, next: tick + every }); return id; },
  runTimeout(fn, delay = 1) { const id = nextId++; tasks.set(id, { fn, once: true, next: tick + Math.max(1, delay) }); return id; },
  clearRun(id) { tasks.delete(id); },
  runJob(gen) { const id = nextId++; tasks.set(id, { fn: () => { const r = gen.next(); if (r.done) tasks.delete(id); }, every: 1, next: tick + 1 }); return id; },
  afterEvents: evProxy(), beforeEvents: evProxy(),
};
function advance(n) {
  for (let i = 0; i < n; i++) {
    tick++;
    for (const [id, t] of [...tasks]) {
      if (!tasks.has(id) || t.next > tick) continue;
      try { t.fn(); } catch (e) { globalThis.__swallow && globalThis.__swallow(e); }
      if (t.once) tasks.delete(id); else t.next = tick + t.every;
    }
  }
}

// ───── أنواع ─────
export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; } }
export class MolangVariableMap { constructor() { this.v = {}; } setFloat(k, x) { this.v[k] = x; } setColorRGB() {} setVector3() {} }
export const EntityDamageCause = new Proxy({}, { get: (t, k) => String(k) });
export const BlockPermutation = { resolve: () => ({}) };
export class BlockVolume { constructor(a, b) { this.a = a; this.b = b; } }
export const GameMode = new Proxy({}, { get: (t, k) => String(k) });
export const HudElement = { PaperDoll: 0, Armor: 1, ToolTips: 2, TouchControls: 3, Crosshair: 4, Hotbar: 5, Health: 6, ProgressBar: 7, Hunger: 8, AirBubbles: 9, HorseHealth: 10, StatusEffects: 11, ItemText: 12 };
export const HudVisibility = { Hide: 0, Reset: 1 };

export const stats = { particles: 0, sounds: 0, spawned: 0, soundIds: new Set(), actionBars: [], messages: [] };
let effectLog = [];

// ───── كيانات ─────
let idc = 1;
function mkEntity(typeId, loc, dim, hp = 40) {
  const props = {}, dyn = {}, tags = new Set();
  const e = {
    id: "e" + idc++, typeId, nameTag: "", location: { ...loc }, dimension: dim, _valid: true, _hp: hp, _max: hp, _tags: tags,
    isValid() { return this._valid; },
    getComponent(n) {
      if (n === "minecraft:health") { const s = this; return { get currentValue() { return s._hp; }, get effectiveMax() { return s._max; }, setCurrentValue(v) { s._hp = v; }, resetToMaxValue() { s._hp = s._max; } }; }
      if (n === "minecraft:type_family") return { hasTypeFamily: (f) => f === "monster" };
      return undefined;
    },
    applyDamage(a) { this._hp -= a; stats.damage = (stats.damage || 0) + a; if (this._hp <= 0) { this._valid = false; } return true; },
    applyKnockback() { stats.knock = (stats.knock || 0) + 1; }, applyImpulse() {},
    addEffect(id, dur, o) { effectLog.push(id); stats.effects = stats.effects || {}; stats.effects[id] = (stats.effects[id] || 0) + 1; if (id === 'health_boost') stats.lastBoost = o && o.amplifier; }, removeEffect() {}, getEffect() { return undefined; },
    teleport(l) { this.location = { x: l.x, y: l.y, z: l.z }; }, remove() { this._valid = false; }, kill() { this._valid = false; },
    setProperty(k, v) { props[k] = v; }, getProperty(k) { return props[k]; }, triggerEvent() {}, setOnFire() {},
    setRotation() {}, getRotation() { return { x: 0, y: 0 }; }, getVelocity() { return { x: 0, y: 0, z: 0 }; },
    getDynamicProperty(k) { return dyn[k]; }, setDynamicProperty(k, v) { dyn[k] = v; },
    hasTag(t) { return tags.has(t); }, addTag(t) { tags.add(t); }, removeTag(t) { tags.delete(t); },
    getHeadLocation() { return { x: this.location.x, y: this.location.y + 1.62, z: this.location.z }; },
    getViewDirection() { return { x: 0, y: 0, z: 1 }; },
  };
  return e;
}

const entities = [];
function mkDim(id) {
  const d = {
    id,
    spawnParticle() { stats.particles++; },
    playSound(s) { stats.sounds++; stats.soundIds.add(s); },
    spawnEntity(type, loc) { stats.spawned++; const e = mkEntity(type, loc, d, 10); entities.push(e); return e; },
    spawnItem(it) { (stats.items = stats.items || []).push(it.typeId); },
    getBlock(l) { const solid = Math.floor(l.y) <= 63; const b = { x: Math.floor(l.x), y: Math.floor(l.y), z: Math.floor(l.z), typeId: solid ? "minecraft:dirt" : "minecraft:air", isAir: !solid, isLiquid: false, location: l, dimension: d, getComponent: (n) => n === 'minecraft:inventory' ? { container: { size: 27, setItem() {}, getItem() {} } } : undefined, setType(t) { stats.blockSets = (stats.blockSets || 0) + 1; this.typeId = t; } }; return b; },
    isChunkLoaded() { return true; },
    getEntities(q = {}) {
      return entities.filter((e) => e._valid && (!q.families || !q.families.includes('sh_rank0') || ['sh:ember_imp','sh:rust_guard','sh:shadow_hound','sh:sand_scorpion'].includes(e.typeId)) && (!q.type || e.typeId === q.type) && !(q.excludeTypes || []).includes(e.typeId)
        && (!q.location || !q.maxDistance || Math.hypot(e.location.x - q.location.x, e.location.z - q.location.z) <= q.maxDistance));
    },
    getPlayers() { return [player]; },
    getTopmostBlock(l) { const b = { x: Math.floor(l.x), y: 63, z: Math.floor(l.z), typeId: "minecraft:grass_block", location: { x: l.x, y: 63, z: l.z }, isAir: false, isLiquid: false, dimension: d, above: () => ({ isAir: true }), below: () => ({ isAir: false, isLiquid: false }), getComponent: () => undefined, setType(t) { stats.blockSets = (stats.blockSets || 0) + 1; this.typeId = t; } }; return b; },
    fillBlocks() {}, setBlockType() {}, setBlockPermutation() {}, runCommand(c) { if (/^setblock .* air destroy$/.test(c)) stats.broken = (stats.broken || 0) + 1; return { successCount: 1 }; }, runCommandAsync: async () => ({}),
  };
  return d;
}
const dims = { overworld: mkDim("minecraft:overworld"), nether: mkDim("minecraft:nether"), the_end: mkDim("minecraft:the_end") };

// ───── اللاعب ─────
const inventory = Array(36).fill(undefined);
const player = mkEntity("minecraft:player", { x: 0, y: 64, z: 0 }, dims.overworld, 20);
Object.assign(player, {
  id: "player1", selectedSlotIndex: 0, isSneaking: false, name: "Tester",
  camera: { fade() {} },
  onScreenDisplay: { setActionBar(t) { stats.actionBars.push(t); }, setTitle(t) { (stats.titles = stats.titles || []).push(t); }, setHudVisibility(v, els) { stats.hudHidden = v === 0 ? els : []; } },
  sendMessage(m) { stats.messages.push(String(m)); }, playSound(s) { stats.sounds++; stats.soundIds.add(s); },
  runCommand() { return { successCount: 1 }; }, runCommandAsync: async () => ({}),
  getRotation() { return { x: 0, y: 0 }; },
  getEntitiesFromViewDirection() { return entities.filter((e) => e._valid && e.typeId.startsWith("minecraft:zombie")).map((e, i) => ({ entity: e, distance: 4 + i })); },
  getBlockFromViewDirection() { return { block: { location: { x: 0, y: 63, z: 8 } }, faceLocation: { x: 0.5, y: 1, z: 0.5 } }; },
  getComponent(n) {
    if (n === "minecraft:inventory") return { container: { size: 36, getItem: (i) => inventory[i], setItem: (i, it) => { inventory[i] = it; }, addItem(it) { const i = inventory.findIndex((x) => !x); if (i >= 0) inventory[i] = it; }, } };
    return mkEntity.prototype ? Object.getPrototypeOf(this) === null ? undefined : player._base.getComponent.call(this, n) : undefined;
  },
});
player._base = mkEntity("x", { x: 0, y: 0, z: 0 }, dims.overworld);
player.getComponent = ((orig) => function (n) { if (n === "minecraft:inventory") return orig.call(this, n); return player._base.getComponent.call(this, n); })(player.getComponent);

export const world = {
  afterEvents: evProxy(), beforeEvents: evProxy(),
  getAllPlayers: () => [player], getPlayers: () => [player],
  getDimension: (n) => dims[String(n).replace("minecraft:", "")] || dims.overworld,
  getDynamicProperty(k) { return world._dyn[k]; }, setDynamicProperty(k, v) { world._dyn[k] = v; }, _dyn: {},
  sendMessage() {}, getDefaultSpawnLocation: () => ({ x: 0, y: 64, z: 0 }),
};

const fire = (name, payload) => { for (const fn of subs[name] || []) fn(payload); };

// ───── السيناريو ─────
const failures = [];
function setState(st) { player.setDynamicProperty("sh", JSON.stringify(st)); }
function baseState(power) {
  return { power, level: 5, xp: 0, rank: 1, training: power ? { [power]: { status: "done", kills: 3 } } : {}, gotBook: true, skills: {}, plevel: 10, pxp: 0, kills: {}, rolledRank: 1 };
}
function hold(typeId) { inventory[0] = typeId ? new ItemStack(typeId) : undefined; player.selectedSlotIndex = 0; }
function addVillager() { const v = mkEntity('minecraft:villager_v2', { x: 0.5, y: 64, z: 3 }, dims.overworld, 20); v._types = ['villager']; const gc = v.getComponent.bind(v); v.getComponent = (n) => n === 'minecraft:type_family' ? { hasTypeFamily: (f) => f === 'villager' } : gc(n); entities.push(v); return v; }
function spawnZombies(n = 4, near = false) {
  entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 20;
  for (let i = 0; i < n; i++) { const z = mkEntity("minecraft:zombie", near ? { x: (i - 1.5) * 0.8, y: 64, z: 3 + i * 0.9 } : { x: (i - 1.5) * 2, y: 64, z: 5 + i * 1.5 }, dims.overworld, 40); entities.push(z); }
}
async function useItem(typeId) {
  hold(typeId);
  fire("itemUse", { source: player, itemStack: new ItemStack(typeId) });
  await Promise.resolve();
}

export const __sim = {
  stats, failures, get failuresArr() { return failures; },
  async runScenario(sc, root) {
    const main = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/main.js"), "utf8");
    const skills = [...main.matchAll(/mk\("([a-z]+)", "([a-z]+)", "[^"]+", "(sh:skill_[a-z]+)"/g)].map((m) => ({ id: m[1], power: m[2], item: m[3] }));
    const powers = [...new Set(skills.map((s) => s.power))];
    console.log(`مهارات: ${skills.length} | قدرات: ${powers.length}`);
    advance(80); // تشغيل intervals الأولية
    fire("playerSpawn", { player, initialSpawn: true });
    advance(100);
    const results = [];
    for (const pw of powers) {
      for (const s of skills.filter((x) => x.power === pw)) {
        setState(baseState(pw)); spawnZombies(); player.isSneaking = false;
        const p0 = stats.particles, s0 = stats.sounds, d0 = stats.damage || 0, f0 = stats.spawned;
        await useItem(s.item);
        advance(260);
        // نختبر شفت لمهارة الشظايا
        if (s.id === "shards") { player.isSneaking = true; spawnZombies(); await useItem(s.item); advance(60); player.isSneaking = false; }
        if (s.id === "spacerewind") { await useItem(s.item); advance(10); }
        results.push({ id: s.id, power: pw, fx: stats.spawned - f0, particles: stats.particles - p0, sounds: stats.sounds - s0, damage: (stats.damage || 0) - d0 });
        system_cd_reset();
      }
    }
    console.log("\nالمهارة          جزيئات  كيانات  أصوات  ضرر");
    for (const r of results) {
      console.log(`${r.id.padEnd(16)} ${String(r.particles).padStart(6)} ${String(r.fx).padStart(7)} ${String(r.sounds).padStart(6)} ${String(Math.round(r.damage)).padStart(5)}`);
      if (r.particles === 0 && r.fx === 0) failures.push(`${r.id}: بدون مؤثرات بصرية`);
      if (r.sounds === 0) failures.push(`${r.id}: بدون صوت`);
    }
    // الأسلحة: كل سلاح مهارتين (استعمال / سنيك + استعمال)
    setState(baseState("star")); player.setDynamicProperty("sh_kat", JSON.stringify({ lv: 5, xp: 0 }));
    console.log("\nالأسلحة (مهارة 1 | مهارة 2):");
    for (const wid of ["sh:dark_katana", "sh:dawn_dagger", "sh:ember_cleaver", "sh:shadow_blade", "sh:shadow_claws", "sh:stone_maul", "sh:sunset_spear"]) {
      const row = [];
      for (const sneak of [false, true]) {
        spawnZombies(4, true); player.isSneaking = sneak;
        const p0 = stats.particles, s0 = stats.sounds, d0 = stats.damage || 0, f0 = stats.spawned, b0 = stats.broken || 0;
        await useItem(wid); advance(120);
        const dmg = Math.round((stats.damage || 0) - d0), shapes = stats.spawned - f0;
        row.push(`شكل ${shapes} ضرر ${dmg}${(stats.broken || 0) - b0 ? " بلوكات " + ((stats.broken || 0) - b0) : ""}`);
        if (dmg <= 0) failures.push(`${wid} مهارة ${sneak ? 2 : 1}: بدون ضرر`);
        if (shapes === 0) failures.push(`${wid} مهارة ${sneak ? 2 : 1}: بدون أشكال`);
        if (stats.sounds - s0 === 0) failures.push(`${wid} مهارة ${sneak ? 2 : 1}: بدون صوت`);
        if (wid === "sh:stone_maul" && (stats.broken || 0) - b0 === 0) failures.push(`المطرقة ما كسرت بلوكات (مهارة ${sneak ? 2 : 1})`);
        system_cd_reset();
      }
      player.isSneaking = false;
      console.log(`  ${wid.padEnd(18)} ${row.join(" | ")}`);
    }
    // الأصدقاء: القروي ما ينضرب
    {
      setState(baseState("star")); spawnZombies(3, true); const v = addVillager(); const hp0 = v._hp;
      player.setDynamicProperty("sh_kat", JSON.stringify({ lv: 5, xp: 0 }));
      for (const it of ["sh:skill_supernova", "sh:dark_katana"]) { await useItem(it); advance(120); system_cd_reset(); }
      console.log("\nالقروي بعد المهارات:", v._hp, "من", hp0);
      if (v._hp !== hp0) failures.push("القروي انضرب بمهارة!");
    }
    // تكسير الأرض
    {
      const bz = stats.blockSets || 0; setState(baseState("star")); spawnZombies(); await useItem("sh:skill_meteor"); advance(120); system_cd_reset();
      console.log("بلوكات تلونت بدون تفعيل (لازم 0):", (stats.blockSets || 0) - bz);
      if ((stats.blockSets || 0) - bz !== 0) failures.push("الأرض تتلون وهي مطفية");
      world._dyn.sh_scars_on = true;
      const b0 = stats.blockSets || 0; spawnZombies(); await useItem("sh:skill_meteor"); advance(120); system_cd_reset();
      await useItem("sh:skill_supernova"); advance(200); system_cd_reset();
      console.log("بلوكات تغيرت بالتكسير:", (stats.blockSets || 0) - b0);
      if ((stats.blockSets || 0) - b0 < 20) failures.push("تكسير الأرض ما غيّر بلوكات");
      advance(1200);
      console.log("بعد الانتظار، ترجع البلوكات (محاولات ترميم):", stats.blockSets - b0);
      world._dyn.sh_scars_on = undefined;
    }
    // تقدم الرتب: كم قتلة لكل رتبة (وحوش الرتبة 0 فقط)
    {
      setState({ ...baseState("iron"), level: 1, xp: 0, rank: 0 });
      const types = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"];
      let kills = 0, lastRank = 0; const marks = [];
      for (let i = 0; i < 4000 && marks.length < 6; i++) {
        const z = mkEntity(types[i % 4], { x: 0, y: 64, z: 3 }, dims.overworld); z.setDynamicProperty("sh_tier", lastRank);
        fire("entityDie", { deadEntity: z, damageSource: { damagingEntity: player } }); kills++;
        const st = JSON.parse(player.getDynamicProperty("sh"));
        if (st.rank !== lastRank) { marks.push(`رتبة ${st.rank} بعد ${kills} قتلة (ليفل ${st.level})`); lastRank = st.rank; }
      }
      console.log("\nتقدم الرتب بقتل وحوش الرتبة 0 فقط:\n  " + (marks.join("\n  ") || "ما ارتقى"));
      if (marks.length < 3) failures.push("الرتب ما تزداد بشكل كافي");
      advance(110);
      console.log("health_boost مطبّق:", stats.effects && stats.effects.health_boost, "amp:", stats.lastBoost);
      if (!(stats.effects && stats.effects.health_boost)) failures.push("health_boost ما انطبق مع الرتبة");
    }
    // تطور القدرة: ليفل اللاعب العالي يرفع القدرة، والقتل يكمل
    {
      setState({ ...baseState("crystal"), level: 44, rank: 2, plevel: 2, pxp: 105 });
      fire("scriptEventReceive", { id: "sh:xp", message: "5", sourceEntity: player });
      let st = JSON.parse(player.getDynamicProperty("sh"));
      console.log("\nتطور القدرة: لاعب ليفل 44 كان عالق Lv2 → صار Lv", st.plevel);
      if (st.plevel < 6) failures.push("ليفل القدرة ما لحق بليفل اللاعب");
      setState({ ...baseState("crystal"), level: 3, rank: 0, plevel: 1, pxp: 0 });
      let kills = 0;
      for (; kills < 60; kills++) {
        const z = mkEntity("sh:shadow_hound", { x: 0, y: 64, z: 3 }, dims.overworld);
        fire("entityDie", { deadEntity: z, damageSource: { damagingEntity: player } });
        st = JSON.parse(player.getDynamicProperty("sh"));
        if (st.plevel >= 4) break;
      }
      console.log("  من Lv1 إلى Lv4 بـ", kills + 1, "قتلة");
      if (st.plevel < 4) failures.push("تطور القدرة بطيء جداً");
      const sk = { ...baseState("crystal"), skills: { shards: { lvl: 12, xp: 0 } } };
      setState(sk); spawnZombies(); await useItem("sh:skill_shards"); advance(60);
      st = JSON.parse(player.getDynamicProperty("sh"));
      if (st.skills.shards.lvl > 12) failures.push("المهارة عبرت الحد الأقصى 12");
      system_cd_reset();
    }
    // خبرة الكاتانا
    hold("sh:dark_katana"); player.setDynamicProperty("sh_kat", JSON.stringify({ lv: 1, xp: 0 }));
    for (let i = 0; i < 6; i++) { const z = mkEntity("sh:sand_scorpion", { x: 0, y: 64, z: 3 }, dims.overworld); fire("entityDie", { deadEntity: z, damageSource: { damagingEntity: player } }); }
    const kat = JSON.parse(player.getDynamicProperty("sh_kat"));
    console.log("  بعد 6 قتلات عقرب:", kat);
    if (kat.lv < 2) failures.push("خبرة الكاتانا ما رفعت الليفل");
    // بوصلة
    console.log("\nبوصلة:");
    world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 120, y: 64, z: 40, type: "village" }, { x: -300, y: 64, z: 500, type: "shrine" }]));
    for (let sel = 0; sel < 6; sel++) {
      const ui = (await import("@minecraft/server-ui")).sim; ui.nextSelection = sel; stats.actionBars.length = 0;
      await useItem("sh:explorer_compass"); advance(10);
      const sh = player.getDynamicProperty("sh_ctarget");
      hold("sh:explorer_compass"); advance(140);
      const bar = stats.actionBars[stats.actionBars.length - 1] || "";
      const line = bar.split("\n").filter((l) => l.includes("◎"))[0] || "(بدون سطر بوصلة)";
      console.log(`  اختيار ${sel} → ${sh} | ${line.replace(/§./g, "")}`);
    }
    player.isSneaking = true; await useItem("sh:explorer_compass"); advance(5); player.isSneaking = false;
    // HUD
    console.log("\nعينات الـHUD:");
    setState(baseState("star")); spawnZombies();
    for (const it of ["sh:skill_meteor", "sh:dark_katana", "sh:evolution_book", ""]) {
      hold(it); stats.actionBars.length = 0; advance(130);
      console.log("---", it || "(يد فاضية)", "\n" + (stats.actionBars[stats.actionBars.length - 1] || "").replace(/§./g, ""));
    }
    // كتاب + نافذة الحالة
    const ui = (await import("@minecraft/server-ui")).sim;
    ui.nextSelection = 99; ui.formsShown.length = 0; await useItem("sh:evolution_book"); advance(3);
    ui.nextSelection = 99; await Promise.resolve();
    const book = ui.formsShown[0];
    console.log("\nكتاب التطور: أزرار", book ? book.buttons.length : 0);
    const last = book ? book.buttons.length - 1 : 0;
    ui.nextSelection = last - 1; ui.formsShown.length = 0; await useItem("sh:evolution_book"); advance(5); await new Promise((r) => setTimeout(r, 20));
    const status = ui.formsShown.find((f) => f.title === "Status Window");
    console.log(status ? "نافذة الحالة تفتح ✔" : "نافذة الحالة ما فتحت");
    if (!status) failures.push("نافذة الحالة ما فتحت");
    else console.log(status.body.replace(/§./g, "").split("\n").slice(0, 14).join("\n"));
    // حكاية العالم
    {
      ui.nextSelection = 99; ui.formsShown.length = 0; await useItem("sh:evolution_book"); advance(5); await new Promise((r) => setTimeout(r, 30));
      const lore = ui.formsShown.find((f) => f.title === "The Tale of the Fallen Star");
      console.log(lore ? "حكاية العالم تفتح ✔ (" + lore.buttons.length + " فصول)" : "حكاية العالم ما فتحت");
      if (!lore) failures.push("حكاية العالم ما فتحت");
      ui.nextSelection = 0;
    }
    // الظهور المتدرج
    {
      setState({ ...baseState("iron"), rank: 4, level: 60 }); entities.length = 0;
      advance(7200);
      const mons = entities.filter((e) => ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"].includes(e.typeId));
      const tiers = mons.map((e) => e.getDynamicProperty("sh_tier"));
      console.log("وحوش ظهرت خلال 7200 تك (6 دقائق، الحد 3):", mons.length, "درجاتها:", tiers.join(","));
      if (mons.length === 0) failures.push("ما ظهرت وحوش بـ6 دقائق");
      if (mons.length > 3) failures.push("ظهور سريع: " + mons.length);
      if (mons.some((e) => e.getDynamicProperty("sh_tier") !== 4)) failures.push("الوحوش ما تدرجت برتبة اللاعب");
    }
    // لفافة تطور المهارة + أمر كل الأسلحة
    {
      const ui2 = (await import("@minecraft/server-ui")).sim;
      setState(baseState("iron")); ui2.nextSelection = 0; inventory[0] = undefined;
      fire("scriptEventReceive", { id: "sh:weapons", message: "", sourceEntity: player });
      const wcount = inventory.filter((i) => i && ["sh:dark_katana", "sh:dawn_dagger", "sh:ember_cleaver", "sh:shadow_blade", "sh:shadow_claws", "sh:stone_maul", "sh:sunset_spear"].includes(i.typeId)).length;
      const idx = inventory.findIndex((i) => i && i.typeId === "sh:skill_scroll");
      console.log("\nأمر الأسلحة: أسلحة =", wcount, "| لفائف =", idx >= 0 ? inventory[idx].amount : 0);
      if (wcount !== 7) failures.push("sh:weapons ما أعطى 7 أسلحة");
      player.selectedSlotIndex = idx; fire("itemUse", { source: player, itemStack: inventory[idx] });
      await new Promise((r) => setTimeout(r, 30)); advance(3);
      const st = JSON.parse(player.getDynamicProperty("sh"));
      const lv = st.skills && st.skills.ironskin && st.skills.ironskin.lvl;
      console.log("بعد اللفافة: مستوى جلد الحديد =", lv, "| لفائف باقية =", (inventory.find((i) => i && i.typeId === "sh:skill_scroll") || { amount: 0 }).amount);
      if (lv !== 2) failures.push("لفافة التطور ما رفعت المهارة");
      player.selectedSlotIndex = 0;
    }
    // مكافأة المدرب: أول تدريب = 3 لفائف
    {
      setState({ ...baseState("iron"), training: { iron: { status: "active", kills: 3 } } });
      for (let i = 0; i < inventory.length; i++) inventory[i] = undefined;
      const tr = mkEntity("sh:trainer", { x: 1, y: 64, z: 2 }, dims.overworld); entities.push(tr);
      fire("playerInteractWithEntity", { player, target: tr, beforeItemStack: undefined, itemStack: undefined });
      await new Promise((r) => setTimeout(r, 60)); advance(3);
      const got = inventory.filter((i) => i && i.typeId === "sh:skill_scroll").reduce((a, i) => a + i.amount, 0);
      console.log("\nمكافأة المدرب بأول تدريب: لفائف =", got);
      if (got !== 3) failures.push("المدرب ما أعطى 3 لفائف بأول تدريب");
      // ثاني مرة (قدرة نفسها) ما يعطي زيادة
      const st = JSON.parse(player.getDynamicProperty("sh")); st.training.iron = { status: "active", kills: 3 }; player.setDynamicProperty("sh", JSON.stringify(st));
      fire("playerInteractWithEntity", { player, target: tr }); await new Promise((r) => setTimeout(r, 60)); advance(3);
      const got2 = inventory.filter((i) => i && i.typeId === "sh:skill_scroll").reduce((a, i) => a + i.amount, 0);
      if (got2 !== 3) failures.push("المدرب كرر المكافأة");
    }
    // جسد الحديد: قشرة الجسم تظهر وتتبع اللاعب وتنتهي
    {
      setState(baseState("iron")); entities.length = 0; player.location = { x: 5, y: 64, z: 5 };
      await useItem("sh:skill_ironskin"); advance(6);
      const shell = entities.find((e) => e.typeId === "sh:fx_body");
      const moved = shell && Math.hypot(shell.location.x - 5, shell.location.z - 5) < 0.5;
      console.log("\nجسد الحديد: قشرة =", !!shell, "| تتبع اللاعب =", !!moved, "| نوع =", shell && shell.getProperty("sh:v"));
      if (!shell) failures.push("قشرة جسد الحديد ما ظهرت");
      advance(200);
      if (entities.some((e) => e.typeId === "sh:fx_body" && e._valid)) failures.push("قشرة الحديد ما انتهت");
      player.location = { x: 0, y: 64, z: 0 };
    }
    // لاعب جديد كلياً: شظية تسقط، سحب بالشظية، وحوش بداية، أول بناية بسرعة
    {
      player.setDynamicProperty("sh", undefined); world._dyn = {}; entities.length = 0; stats.items = []; for (let i = 0; i < inventory.length; i++) inventory[i] = undefined;
      fire("playerSpawn", { player, initialSpawn: true });
      advance(1500); await new Promise((r) => setTimeout(r, 30));
      let st = JSON.parse(player.getDynamicProperty("sh") || "{}");
      const mons = entities.filter((e) => ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"].includes(e.typeId)).length;
      const reg = world._dyn.sh_structs ? JSON.parse(world._dyn.sh_structs).length : 0;
      const dropped = (stats.items || []).filter((t) => t === "sh:star_shard").length;
      console.log("\nلاعب جديد بعد دقيقة و15ث: قدرة =", st.power, "| شظية سقطت =", dropped, "| وحوش بداية =", mons, "| بنايات =", reg, "| كتاب =", inventory.some((i) => i && i.typeId === "sh:evolution_book"), "| بوصلة =", inventory.some((i) => i && i.typeId === "sh:explorer_compass"));
      if (st.power) failures.push("اللاعب الجديد ياخذ قدرة بدون شظية");
      if (dropped < 1) failures.push("الشظية ما سقطت");
      if (mons < 1) failures.push("ما ظهرت وحوش بداية");
      if (reg < 1) failures.push("ما انبنت أول بناية بسرعة");
      // يلقط الشظية ويستعملها
      inventory[3] = new ItemStack("sh:star_shard"); player.selectedSlotIndex = 3;
      fire("itemUse", { source: player, itemStack: inventory[3] });
      advance(40);
      st = JSON.parse(player.getDynamicProperty("sh") || "{}");
      if (st.power) failures.push("السحب خلص بدون أنيميشن");
      advance(220); await new Promise((r) => setTimeout(r, 30));
      st = JSON.parse(player.getDynamicProperty("sh") || "{}");
      console.log("بعد السحب: قدرة =", st.power, "| شظية باقية =", inventory.some((i) => i && i.typeId === "sh:star_shard"));
      if (!st.power) failures.push("السحب بالشظية ما أعطى قدرة");
      if (inventory.some((i) => i && i.typeId === "sh:star_shard")) failures.push("الشظية ما انحرقت");
      // استعمال شظية ثانية وانت عندك قدرة ما يغير شي
      inventory[4] = new ItemStack("sh:star_shard"); const keep = st.power;
      fire("itemUse", { source: player, itemStack: inventory[4] }); advance(250);
      if (JSON.parse(player.getDynamicProperty("sh")).power !== keep) failures.push("الشظية غيرت قدرة موجودة");
      player.selectedSlotIndex = 0;
    }
    // ميزات جوجوتسو: الطاقة، الوميض الأسود، التوسع الإقليمي، والـHUD المرسوم
    {
      for (let i = 0; i < inventory.length; i++) inventory[i] = undefined;
      setState({ ...baseState("crystal"), rank: 2, level: 35 });
      advance(110);
      console.log("\nقلوب ماينكرافت مخفية:", JSON.stringify(stats.hudHidden));
      if (!(stats.hudHidden || []).includes(6)) failures.push("قلوب ماينكرافت ما انخفت");
      stats.actionBars.length = 0; hold(""); advance(10);
      const bar = stats.actionBars[stats.actionBars.length - 1] || "";
      const glyphs = [...bar].filter((ch) => ch.charCodeAt(0) >= 0xE500 && ch.charCodeAt(0) <= 0xE5FF).length;
      console.log("رموز مرسومة بالـHUD:", glyphs, "| أسطر:", bar.split("\n").length);
      if (glyphs < 25) failures.push("الـHUD ما يستعمل الرسومات");
      // الوميض الأسود المضمون
      spawnZombies(1, true); const z = entities[0]; const hp0 = z._hp;
      fire("scriptEventReceive", { id: "sh:blackflash", message: "", sourceEntity: player });
      stats.titles = []; const f0 = stats.spawned;
      fire("entityHitEntity", { damagingEntity: player, hitEntity: z }); advance(10);
      console.log("الوميض الأسود: ضرر", hp0 - z._hp, "| أشكال", stats.spawned - f0, "| عنوان", (stats.titles || []).join(","));
      if (!(stats.titles || []).some((t) => t.includes("BLACK"))) failures.push("الوميض الأسود ما اشتغل");
      // التوسع الإقليمي
      fire("scriptEventReceive", { id: "sh:energy", message: "100", sourceEntity: player });
      const has = inventory.some((i) => i && i.typeId === "sh:skill_domain");
      spawnZombies(4, true); stats.titles = []; const d0 = stats.damage || 0, s0 = stats.spawned;
      await useItem("sh:skill_domain"); advance(5);
      const dome = entities.find((e) => e.typeId === "sh:fx_shape" && e._valid && e.getProperty("sh:v") >= 50 && e.getProperty("sh:v") <= 58);
      advance(250);
      console.log("التوسع: أيتم =", has, "| قبة =", !!dome, "| عنوان =", (stats.titles || [])[0], "| ضرر =", Math.round((stats.damage || 0) - d0), "| أشكال =", stats.spawned - s0);
      if (!has) failures.push("أيتم التوسع ما انعطى");
      if (!dome) failures.push("قبة التوسع ما ظهرت");
      if ((stats.damage || 0) - d0 <= 0) failures.push("التوسع ما ضرب");
      // سنيك = تدفق عكسي
      fire("scriptEventReceive", { id: "sh:energy", message: "50", sourceEntity: player });
      player._hp = 5; player.isSneaking = true; await useItem("sh:skill_domain"); player.isSneaking = false; advance(2);
      console.log("التدفق العكسي: صحة", player._hp);
      if (player._hp < 13) failures.push("التدفق العكسي ما شفى");
      for (const pw of ["iron", "wind", "echo", "accountant", "borrower", "distance", "law", "star"]) {
        setState({ ...baseState(pw), rank: 2, level: 35 }); spawnZombies(3, true);
        fire("scriptEventReceive", { id: "sh:energy", message: "100", sourceEntity: player });
        const dd = stats.damage || 0; await useItem("sh:skill_domain"); advance(250);
        if ((stats.damage || 0) - dd <= 0) failures.push(`توسع ${pw} ما ضرب`);
      }
    }
    // أوامر التجربة
    fire("scriptEventReceive", { id: "sh:power", message: "star", sourceEntity: player });
    fire("scriptEventReceive", { id: "sh:unlock", message: "", sourceEntity: player });
    fire("scriptEventReceive", { id: "sh:katlv", message: "3", sourceEntity: player });
    fire("scriptEventReceive", { id: "sh:cdreset", message: "", sourceEntity: player });
    console.log("\nأوامر التجربة تشتغل بدون خطأ.");
  },
};
function system_cd_reset() { fire("scriptEventReceive", { id: "sh:cdreset", message: "", sourceEntity: player }); }
export { advance };
