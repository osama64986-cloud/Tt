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
// مؤقتات كيانات المؤثرات (minecraft:timer بملفات BP، sh:fx_*): باللعبة الكيان يختفي لما يخلص المؤقت، فالمحاكي يسوي نفس الشي
const FX_TIMERS = {};
function loadFxTimers(root) {
  try {
    const dir = path.join(root, "AnimePowers/BP/entities");
    for (const f of fs.readdirSync(dir)) {
      if (!f.startsWith("sh_fx_")) continue;
      const e = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"))["minecraft:entity"];
      const t = e.components["minecraft:timer"];
      if (t && !t.looping) FX_TIMERS[e.description.identifier] = Math.round(t.time * 20);
    }
  } catch (err) { /* */ }
}
function advance(n) {
  for (let i = 0; i < n; i++) {
    tick++;
    for (const e of entities) if (e._dieAt !== undefined && e._valid && e._dieAt <= tick) e._valid = false;
    for (const [id, t] of [...tasks]) {
      if (!tasks.has(id) || t.next > tick) continue;
      try { t.fn(); } catch (e) { globalThis.__swallow && globalThis.__swallow(e); }
      if (t.once) tasks.delete(id); else t.next = tick + t.every;
    }
  }
}

// ───── أنواع ─────
export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; } }
export class MolangVariableMap {
  constructor() { this.v = {}; }
  setFloat(k, x) { this.v[k] = x; }
  setColorRGB(k, c) { this.v[k + ".r"] = c.red; this.v[k + ".g"] = c.green; this.v[k + ".b"] = c.blue; }
  setColorRGBA(k, c) { this.v[k + ".r"] = c.red; this.v[k + ".g"] = c.green; this.v[k + ".b"] = c.blue; this.v[k + ".a"] = c.alpha; }
  setVector3(k, c) { this.v[k + ".x"] = c.x; this.v[k + ".y"] = c.y; this.v[k + ".z"] = c.z; }
  setSpeedAndDirection(k, sp, d) { this.v[k + ".speed"] = sp; this.v[k + ".direction.x"] = d.x; this.v[k + ".direction.y"] = d.y; this.v[k + ".direction.z"] = d.z; }
}
export const EntityDamageCause = new Proxy({}, { get: (t, k) => String(k) });
export const BlockPermutation = { resolve: () => ({}) };
export class BlockVolume { constructor(a, b) { this.a = a; this.b = b; } }
export const GameMode = new Proxy({}, { get: (t, k) => String(k) });
export const HudElement = { PaperDoll: 0, Armor: 1, ToolTips: 2, TouchControls: 3, Crosshair: 4, Hotbar: 5, Health: 6, ProgressBar: 7, Hunger: 8, AirBubbles: 9, HorseHealth: 10, StatusEffects: 11, ItemText: 12 };
export const HudVisibility = { Hide: 0, Reset: 1 };
export const EquipmentSlot = { Head: "Head", Chest: "Chest", Legs: "Legs", Feet: "Feet", Mainhand: "Mainhand", Offhand: "Offhand" };

// تسجيل: لما rec.on يسجل كل جزيء انطلب (النوع والمكان والمتغيرات) وتحرك كل كيان، حتى تنرسم النتيجة الحقيقية بدل مشاهد مرسومة باليد
export const rec = { on: false, particles: [], frames: [] };
export const stats = { particles: 0, sounds: 0, spawned: 0, soundIds: new Set(), actionBars: [], messages: [] };
let effectLog = [];

// ───── كيانات ─────
let idc = 1;
function mkEntity(typeId, loc, dim, hp = 40) {
  const props = {}, dyn = {}, tags = new Set();
  const e = {
    _props: props,
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
    teleport(l, o) { this.location = { x: l.x, y: l.y, z: l.z }; if (o && o.facingLocation) { this._yaw = (Math.atan2(-(o.facingLocation.x - l.x), o.facingLocation.z - l.z) * 180) / Math.PI; } else if (o && o.rotation) this._yaw = o.rotation.y; }, remove() { this._valid = false; }, kill() { this._valid = false; },
    setProperty(k, v) { if (process.env.SH_TRACE && k === "sh:state" && typeId === "sh:hollow_seer") console.log("   [trace] tick", tick, this.id, "state", v); props[k] = v; if (typeId === "sh:fx_shape" && k === "sh:v") { stats.shapeV = stats.shapeV || {}; stats.shapeV[v] = (stats.shapeV[v] || 0) + 1; } }, getProperty(k) { return props[k]; }, triggerEvent() {}, setOnFire() {},
    setRotation(r) { if (r) this._yaw = r.y; }, getRotation() { return { x: 0, y: this._yaw || 0 }; }, getVelocity() { return { x: 0, y: 0, z: 0 }; },
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
    spawnParticle(id, loc, vars) {
      // سبرايت colored_flame_particle سماوي أصلاً: تلوينه بلون دافئ (أحمر/برتقالي/ذهبي) يطلعه أخضر زيتوني. للدافئ نستعمل small_flame_particle أو glow_particle
      if (id === "minecraft:colored_flame_particle" && vars && vars.v) { const r = vars.v["variable.color.r"], g = vars.v["variable.color.g"], b = vars.v["variable.color.b"]; if (r > 0.6 && b < 0.5 && r >= g * 0.9) { stats.badTint = stats.badTint || {}; const k = [r, g, b].map((x) => x.toFixed(2)).join(","); stats.badTint[k] = (stats.badTint[k] || 0) + 1; } }
      if (rec.on && loc) rec.particles.push({ t: tick, id, x: loc.x, y: loc.y, z: loc.z, v: vars && vars.v ? { ...vars.v } : {} }); stats.particles++; stats.pById = stats.pById || {}; stats.pById[id] = (stats.pById[id] || 0) + 1; },
    playSound(s) { stats.sounds++; stats.soundIds.add(s); },
    spawnEntity(type, loc) { stats.spawned++; const e = mkEntity(type, loc, d, 10); if (FX_TIMERS[type]) e._dieAt = tick + FX_TIMERS[type]; entities.push(e); return e; },
    spawnItem(it) { (stats.items = stats.items || []).push(it.typeId); },
    getBlock(l) { const solid = Math.floor(l.y) <= 63; const b = { x: Math.floor(l.x), y: Math.floor(l.y), z: Math.floor(l.z), typeId: solid ? "minecraft:dirt" : "minecraft:air", isAir: !solid, isLiquid: false, location: l, dimension: d, getComponent: (n) => n === 'minecraft:inventory' ? { container: { size: 27, setItem(i, it) { (stats.chestItems = stats.chestItems || []).push(it && it.typeId); }, getItem() {} } } : undefined, setType(t) { stats.blockSets = (stats.blockSets || 0) + 1; this.typeId = t; } }; return b; },
    isChunkLoaded() { return true; },
    getEntities(q = {}) {
      return entities.filter((e) => e._valid && (!e.dimension || e.dimension === d) && (!q.type || e.typeId === q.type) && (!q.tags || q.tags.every((t) => e._tags.has(t))) && (!q.families || q.families.every((f) => ({ sh_rank0: ['sh:ember_imp','sh:rust_guard','sh:shadow_hound','sh:sand_scorpion'], sh_rank1: ['sh:gloomhorn','sh:hollow_seer','sh:veilfox','sh:magmamoth'], sh_rank2: ['sh:magmamoth','sh:grey_bear'], sh_rank3: ['sh:prayer_mantis'], sh_monster: ['sh:ember_imp','sh:rust_guard','sh:shadow_hound','sh:sand_scorpion','sh:gloomhorn','sh:hollow_seer','sh:veilfox','sh:magmamoth','sh:grey_bear','sh:bear_cub','sh:prayer_mantis'] }[f] || [e.typeId]).includes(e.typeId))) && (!q.type || e.typeId === q.type) && !(q.excludeTypes || []).includes(e.typeId) && !((q.excludeFamilies || []).includes("inanimate") && e.typeId.startsWith("sh:fx_"))
        && (!q.location || !q.maxDistance || Math.hypot(e.location.x - q.location.x, e.location.z - q.location.z) <= q.maxDistance));
    },
    getPlayers(q) {      // بالتسجيل بس نحترم فلتر المسافة مثل اللعبة (باقي الاختبارات تبقى تضرب دائماً حتى تتأكد المهارة تطلع)
      if (rec.on && q && q.location && q.maxDistance !== undefined) { const dx = player.location.x - q.location.x, dy = (player.location.y + 1) - q.location.y, dz = player.location.z - q.location.z; return Math.hypot(dx, dy, dz) <= q.maxDistance ? [player] : []; }
      return [player];
    },
    getTopmostBlock(l) { const b = { x: Math.floor(l.x), y: 63, z: Math.floor(l.z), typeId: "minecraft:grass_block", location: { x: l.x, y: 63, z: l.z }, isAir: false, isLiquid: false, dimension: d, above: () => ({ isAir: true }), below: () => ({ isAir: false, isLiquid: false }), getComponent: () => undefined, setType(t) { stats.blockSets = (stats.blockSets || 0) + 1; this.typeId = t; } }; return b; },
    fillBlocks() {}, setBlockType(l, t) { (stats.setTypes = stats.setTypes || []).push([Math.floor(l.x), Math.floor(l.y), Math.floor(l.z), t]); }, setBlockPermutation() {}, runCommand(c) { if (/^setblock .* air destroy$/.test(c)) stats.broken = (stats.broken || 0) + 1; return { successCount: 1 }; }, runCommandAsync: async () => ({}),
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
  // الشاشة: فوق يسار = شريط الأكشن، فوق الهوت بار = العنوان. actionBars يسجل الشاشة كاملة (فوق + تحت) حتى الاختبارات القديمة تلقى كل الكتابات،
  // وstats.top / stats.bottom كل قسم لحاله حتى نتأكد وين انكتبت كل شغلة.
  onScreenDisplay: {
    setActionBar(t) { stats.top = String(t); stats.actionBars.push(stats.top + (stats.bottom ? "\n" + stats.bottom : "")); },
    setTitle(t, o) { (stats.titles = stats.titles || []).push(t); stats.bottom = String(t); stats.titleOpts = o; stats.actionBars.push((stats.top || "") + "\n" + stats.bottom); },
    clearTitle() { stats.bottom = ""; },
    setHudVisibility(v, els) { stats.hudHidden = v === 0 ? els : []; },
  },
  sendMessage(m) { stats.messages.push(String(m)); }, playSound(s) { stats.sounds++; stats.soundIds.add(s); },
  runCommand() { return { successCount: 1 }; }, runCommandAsync: async () => ({}),
  getRotation() { return { x: 0, y: 0 }; },
  inputInfo: { getMovementVector: () => player._mv || { x: 0, y: 0 } },
  getVelocity: () => player._vel || { x: 0, y: 0, z: 0 },
  getEntitiesFromViewDirection() { return entities.filter((e) => e._valid && e.typeId.startsWith("minecraft:zombie")).map((e, i) => ({ entity: e, distance: 4 + i })); },
  getBlockFromViewDirection() { return { block: { location: { x: 0, y: 63, z: 8 } }, faceLocation: { x: 0.5, y: 1, z: 0.5 } }; },
  getComponent(n) {
    if (n === "minecraft:inventory") return { container: { size: 36, getItem: (i) => inventory[i], setItem: (i, it) => { inventory[i] = it; }, addItem(it) { const i = inventory.findIndex((x) => !x); if (i >= 0) inventory[i] = it; }, } };
    return mkEntity.prototype ? Object.getPrototypeOf(this) === null ? undefined : player._base.getComponent.call(this, n) : undefined;
  },
});
player._base = mkEntity("x", { x: 0, y: 0, z: 0 }, dims.overworld);
player.getComponent = ((orig) => function (n) {
  if (n === "minecraft:inventory") return orig.call(this, n);
  if (n === "minecraft:equippable") return { getEquipment: (slot) => (player._equip || {})[slot] };
  if (n === "minecraft:health") { const s = this; return { get currentValue() { return s._hp; }, get effectiveMax() { return s._max; }, setCurrentValue(v) { s._hp = v; }, resetToMaxValue() { s._hp = s._max; } }; }
  return player._base.getComponent.call(this, n);
})(player.getComponent);

export const world = {
  afterEvents: evProxy(), beforeEvents: evProxy(),
  getAllPlayers: () => [player], getPlayers: () => [player],
  getEntity: (id) => entities.find((e) => e.id === id && e._valid),
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

function snapFrame() {
  const list = [];
  for (const e of entities) if (e._valid) list.push({ id: e.id, type: e.typeId, x: e.location.x, y: e.location.y, z: e.location.z, yaw: e._yaw || 0, props: { ...(e._props || {}) } });
  list.push({ id: player.id, type: "player", x: player.location.x, y: player.location.y, z: player.location.z, yaw: player._yaw || 0, props: {} });
  rec.frames.push({ t: tick, ents: list });
}
export const __sim = {
  rec, snapFrame, advance, entities, mkEntity, dims, player, get tick() { return tick; },
  fire, useItem, setState, baseState, spawnZombies, hold, cdReset: () => system_cd_reset(),
  stats, failures, get failuresArr() { return failures; },
  async runScenario(sc, root) {
    loadFxTimers(root);
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
    // تلفيل الأسلحة: بـLv1 المهارة الثانية مقفولة
    {
      player.setDynamicProperty("sh_wlv", undefined);
      spawnZombies(4, true); player.isSneaking = true;
      const d0 = stats.damage || 0; await useItem("sh:ember_cleaver"); advance(60); player.isSneaking = false;
      const locked = Math.round((stats.damage || 0) - d0);
      // خبرة من الضرب والقتل ترفع الليفل
      hold("sh:ember_cleaver"); spawnZombies(1, true); const z = entities[0]; z._hp = 4000; z._max = 4000;
      for (let i = 0; i < 40; i++) { fire("entityHitEntity", { damagingEntity: player, hitEntity: z }); advance(11); }
      const lvHit = JSON.parse(player.getDynamicProperty("sh_wlv") || "{}")["sh:ember_cleaver"];
      fire("entityDie", { deadEntity: mkEntity("sh:rust_guard", { x: 0, y: 64, z: 2 }, dims.overworld, 40), damageSource: { damagingEntity: player } });
      const lvKill = JSON.parse(player.getDynamicProperty("sh_wlv") || "{}")["sh:ember_cleaver"];
      // ضرر الضربة العادية يكبر مع الليفل
      const hitDmg = async (lv) => { player.setDynamicProperty("sh_wlv", JSON.stringify({ "sh:ember_cleaver": { lv, xp: 0 } })); const d = stats.damage || 0; fire("entityHitEntity", { damagingEntity: player, hitEntity: z }); advance(1); return Math.round((stats.damage || 0) - d); };
      const dm1 = await hitDmg(1), dm5 = await hitDmg(5);
      const p0 = stats.particles; advance(40); const aura = stats.particles - p0;
      console.log(`\nتلفيل الأسلحة: مهارة 2 بـLv1 = ${locked > 0 ? "مفتوحة ✖" : "مقفولة ✔"} | بعد 40 ضربة: Lv${lvHit && lvHit.lv} (${lvHit && lvHit.xp} XP) | بعد قتلة: Lv${lvKill && lvKill.lv} | ضرر الضربة Lv1=${dm1} Lv5=${dm5} | هالة Lv5 جزيئات=${aura}`);
      if (locked > 0) failures.push("المهارة الثانية للسلاح مفتوحة بـLv1");
      if (!lvHit || lvHit.lv < 2) failures.push("السلاح ما يتلفل من الضرب");
      if (!(dm5 > dm1)) failures.push("ضرر السلاح ما يكبر مع الليفل");
      if (aura < 5) failures.push("هالة السلاح ما تطلع");
      hold("");
      const all = {}; for (const id of ["sh:dawn_dagger", "sh:ember_cleaver", "sh:shadow_blade", "sh:shadow_claws", "sh:stone_maul", "sh:sunset_spear", "sh:silver_oath"]) all[id] = { lv: 5, xp: 0 };
      player.setDynamicProperty("sh_wlv", JSON.stringify(all)); system_cd_reset();
    }
    console.log("\nالأسلحة (مهارة 1 | مهارة 2):");
    for (const wid of ["sh:dark_katana", "sh:dawn_dagger", "sh:ember_cleaver", "sh:shadow_blade", "sh:shadow_claws", "sh:stone_maul", "sh:sunset_spear", "sh:silver_oath"]) {
      const row = [];
      for (const sneak of [false, true]) {
        spawnZombies(4, true); player.isSneaking = sneak;
        const p0 = stats.particles, s0 = stats.sounds, d0 = stats.damage || 0, f0 = stats.spawned, b0 = stats.broken || 0;
        await useItem(wid); advance(120);
        const dmg = Math.round((stats.damage || 0) - d0), shapes = stats.spawned - f0;
        row.push(`شكل ${shapes} ضرر ${dmg}${(stats.broken || 0) - b0 ? " بلوكات " + ((stats.broken || 0) - b0) : ""}`);
        if (dmg <= 0) failures.push(`${wid} مهارة ${sneak ? 2 : 1}: بدون ضرر`);
        if (shapes === 0 && stats.particles - p0 < 20) failures.push(`${wid} مهارة ${sneak ? 2 : 1}: بدون مؤثرات (لا أشكال ولا جزيئات)`);
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
      fire("scriptEventReceive", { id: "sh:rift", message: "close", sourceEntity: player }); advance(80); // صدع طبيعي ممكن يغير بلوكات بنص القياس
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
    // الواجهة البسيطة (sh_hud_plain): لازم تطلع بدون خطأ وبدون رموز مرسومة
    {
      player._tags.add("sh_hud_plain"); hold(""); stats.actionBars.length = 0; advance(40);
      const plainBar = stats.actionBars[stats.actionBars.length - 1] || "";
      const okPlain = plainBar.includes("Lv") && !/[\uE000-\uF8FF]/.test(plainBar);
      console.log(`  الواجهة البسيطة: ${okPlain ? "✔" : "✖"} | ${plainBar.split("\n")[0].replace(/§./g, "")}`);
      if (!okPlain) failures.push("الواجهة البسيطة (sh_hud_plain) ما تطلع");
      player._tags.delete("sh_hud_plain");
    }
    // v1.35.1: اللوحة فوق يسار = الأشرطة وشريط المهارات بس؛ معلومات الأيتم بإيدك فوق الهوت بار (كتابة صغيرة بدون خلفية)
    {
      hold("sh:skill_meteor"); stats.actionBars.length = 0; advance(20);
      const top = stats.top || "", low = stats.bottom || "";
      const ok = /Skills/.test(top) && !/Level \d/.test(top) && /Level \d/.test(low) && stats.titleOpts && stats.titleOpts.fadeInDuration === 0;
      console.log(`  المكان: الأشرطة فوق يسار + معلومات المهارة فوق الهوت بار ${ok ? "✔" : "✖"} | فوق الهوت بار: ${low.replace(/§./g, "").replace(/\n/g, " ⏎ ")}`);
      if (!ok) failures.push("معلومات الأيتم مو فوق الهوت بار (أو اللوحة فوق يسار بيها كتابات)");
      hold(""); advance(30);
      const cleared = !(stats.bottom || "").includes("Level");
      if (!cleared) failures.push("الكتابة فوق الهوت بار ما تنمسح لما تنزل الأيتم");
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
      const mons = entities.filter((e) => ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion", "sh:gloomhorn", "sh:hollow_seer", "sh:veilfox", "sh:magmamoth"].includes(e.typeId));
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
      const wcount = inventory.filter((i) => i && ["sh:dark_katana", "sh:dawn_dagger", "sh:ember_cleaver", "sh:shadow_blade", "sh:shadow_claws", "sh:stone_maul", "sh:sunset_spear", "sh:silver_oath"].includes(i.typeId)).length;
      const idx = inventory.findIndex((i) => i && i.typeId === "sh:skill_scroll");
      console.log("\nأمر الأسلحة: أسلحة =", wcount, "| لفائف =", idx >= 0 ? inventory[idx].amount : 0);
      if (wcount !== 8) failures.push("sh:weapons ما أعطى 8 أسلحة");
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
    // لاعب جديد كلياً: معبد النجمة يطلع قربه، يدوس على البلورة ← سحب بألوان الندرة ← قدرة
    {
      player.setDynamicProperty("sh", undefined); world._dyn = {}; entities.length = 0; stats.items = []; for (let i = 0; i < inventory.length; i++) inventory[i] = undefined;
      player.location = { x: 0, y: 64, z: 0 };
      fire("playerSpawn", { player, initialSpawn: true });
      advance(1500); await new Promise((r) => setTimeout(r, 30));
      let st = JSON.parse(player.getDynamicProperty("sh") || "{}");
      const mons = entities.filter((e) => ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"].includes(e.typeId)).length;
      const reg = world._dyn.sh_structs ? JSON.parse(world._dyn.sh_structs) : [];
      const temple = reg.find((r) => r.type === "temple");
      console.log("\nلاعب جديد بعد دقيقة و15ث: قدرة =", st.power, "| معبد =", temple ? `${temple.x},${temple.y},${temple.z}` : "لا", "| وحوش بداية =", mons, "| بنايات =", reg.length, "| كتاب =", inventory.some((i) => i && i.typeId === "sh:evolution_book"));
      if (st.power) failures.push("اللاعب الجديد ياخذ قدرة بدون المعبد");
      if (!temple) failures.push("معبد النجمة ما انبنى");
      if (mons < 1) failures.push("ما ظهرت وحوش بداية");
      if (temple) {
        player.location = { x: temple.x + 0.5, y: temple.y + 8, z: temple.z + 30 }; advance(120);
        const crystal0 = entities.find((e) => e.typeId === "sh:fx_shape" && e._valid && e.getProperty("sh:v") >= 58 && e.getProperty("sh:v") <= 64);
        if (!crystal0) failures.push("بلورة المعبد ما ظهرت");
        // يدوس على اللوحة الذهبية (نشيل وحوش البداية حتى ما يقتلون اللاعب الوهمي بنص السحب)
        entities.forEach((e) => { if (e.typeId !== "sh:fx_shape" && e.typeId !== "minecraft:player") e._valid = false; });
        player._hp = 400; player._valid = true;
        player.location = { x: temple.x + 0.5, y: temple.y + 1, z: temple.z + 0.5 };
        const seen = new Set();
        for (let i = 0; i < 5; i++) { advance(8); for (const e of entities) if (e.typeId === "sh:fx_shape" && e._valid) { const v = e.getProperty("sh:v"); if (v >= 58 && v <= 64) seen.add(v); } }
        st = JSON.parse(player.getDynamicProperty("sh") || "{}");
        if (st.power) failures.push("السحب خلص بدون أنيميشن");
        for (let i = 0; i < 20; i++) { advance(8); for (const e of entities) if (e.typeId === "sh:fx_shape" && e._valid) { const v = e.getProperty("sh:v"); if (v >= 58 && v <= 64) seen.add(v); } }
        player.location = { x: temple.x + 3.5, y: temple.y + 1, z: temple.z + 3.5 };
        advance(300); await new Promise((r) => setTimeout(r, 30));
        st = JSON.parse(player.getDynamicProperty("sh") || "{}");
        console.log("بعد الدوس على البلورة: قدرة =", st.power, "| ألوان البلورة اللي ظهرت =", [...seen].sort().join(","));
        if (!st.power && !st.powerless) { failures.push("الدوس على البلورة ما أعطى قدرة"); console.log("  رسائل:", stats.messages.slice(-6).map((m) => m.replace(/§./g, "")).join(" || ")); }
        if (seen.size < 3) failures.push("لون البلورة ما يتغير أثناء السحب");
        // الدوس مرة ثانية ما يغير القدرة
        const keep = st.power;
        player.location = { x: temple.x + 0.5, y: temple.y + 1, z: temple.z + 0.5 }; advance(300);
        if (JSON.parse(player.getDynamicProperty("sh")).power !== keep) failures.push("البلورة غيرت قدرة موجودة");
      }
      // بلا قدرة (Unbound): قوة وسرعة
      const effs0 = effectLog.length;
      fire("scriptEventReceive", { id: "sh:power", message: "unbound", sourceEntity: player }); advance(120);
      st = JSON.parse(player.getDynamicProperty("sh") || "{}");
      const effs = effectLog.slice(effs0);
      console.log("Unbound:", st.powerless, "| تأثيرات =", [...new Set(effs)].join(" "));
      if (!st.powerless) failures.push("Unbound ما تفعّل");
      if ((!effs.includes("strength") || !effs.includes("speed"))) failures.push("Unbound ما ياخذ قوة وسرعة");
      player.location = { x: 0, y: 64, z: 0 };
      player.selectedSlotIndex = 0;
    }
    // ميزات النجمة الساقطة: الكوكبة، سقوط النجوم، الصاعد، الرد النجمي، والـHUD المرسوم
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
      // الصدع: يفتح، يفسد الأرض، 3 موجات، زعيم، ينسد ويعطي مكافآت
      fire("scriptEventReceive", { id: "sh:rift", message: "close", sourceEntity: player }); advance(40);
      entities.length = 0; stats.items = [];
      fire("scriptEventReceive", { id: "sh:rift", message: "violet", sourceEntity: player });
      let rs = JSON.parse(world._dyn.sh_rift || "null");
      console.log("\nالصدع:", rs && rs.tier, rs && Math.round(Math.hypot(rs.x, rs.z)), "بلوكة");
      if (!rs) failures.push("الصدع ما انفتح");
      else {
        const b0 = stats.blockSets || 0;
        advance(40); stats.actionBars.length = 0; advance(10);
        const hud = stats.actionBars[stats.actionBars.length - 1] || "";
        if (!hud.includes("Violet Rift")) failures.push("الصدع ما طلع بالـHUD");
        // v1.35.1: سطر الصدع والإعلانات فوق الهوت بار (العنوان)، مو باللوحة فوق يسار (شريط الأكشن)
        const riftLow = (stats.bottom || "").includes("Violet Rift") && !(stats.top || "").includes("Violet Rift");
        const openBanner = (stats.titles || []).some((t) => t.includes("VIOLET RIFT"));
        console.log(`  مكان الكتابة: سطر الصدع فوق الهوت بار ${riftLow ? "✔" : "✖"} | إعلان فتح الصدع فوق الهوت بار ${openBanner ? "✔" : "✖"}`);
        if (!riftLow || !openBanner) failures.push("كتابات الصدع مو فوق الهوت بار");
        stats.titles = [];
        console.log("  فساد الأرض: بلوكات =", (stats.blockSets || 0) - b0, "| HUD:", (hud.split("\n").find((l) => l.includes("Rift")) || "").replace(/§./g, "").replace(/[\uE500-\uE5FF]/g, "◆"));
        if ((stats.blockSets || 0) - b0 < 10) failures.push("الصدع ما فسد الأرض");
        // شكل الصدع 3D ودائرته لازم يبقون ظاهرين طول الوقت (مع مؤقتات BP: الشكل 60 ثانية، الدائرة 30) وبدون تكرار
        {
          const SHR = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/shapes.js"), "utf8");
          const vRift = Number((SHR.match(/"rift_violet": (\d+)/) || [])[1]);
          let minS = 99, maxS = 0, minC = 99, maxC = 0, rOk = true;
          for (let k = 0; k < 75; k++) {
            advance(20);
            const sh = entities.filter((e) => e._valid && e.typeId === "sh:fx_shape" && e.getProperty("sh:v") === vRift);
            const ci = entities.filter((e) => e._valid && e.typeId === "sh:fx_circle" && e._tags.has("sh_rift_fx"));
            minS = Math.min(minS, sh.length); maxS = Math.max(maxS, sh.length); minC = Math.min(minC, ci.length); maxC = Math.max(maxC, ci.length);
            if (sh.some((e) => !(e.getProperty("sh:r") > 1))) rOk = false;
          }
          const ok = minS === 1 && maxS === 1 && minC === 1 && maxC === 1 && rOk;
          console.log(`  شكل الصدع 3D خلال 75 ثانية: أقل ${minS} / أكثر ${maxS} | الدائرة الرونية: أقل ${minC} / أكثر ${maxC} | الحجم ${rOk ? "✔" : "✖"} ${ok ? "✔" : "✖"}`);
          if (!ok) failures.push("شكل الصدع أو دائرته يختفي أو يتكرر");
        }
        player.location = { x: rs.x + 4, y: 64, z: rs.z };
        const waves = [];
        for (let w = 1; w <= 3; w++) {
          // ننتظر لحد ما تطلع الموجة كاملة (توقيت فحص الصدع كل 20 تك يختلف حسب اللي قبله)
          let mobs = [];
          for (let k = 0, seen = -1; k < 30; k++) {
            advance(20);
            mobs = entities.filter((e) => e._valid && e._tags.has("sh_rift"));
            if (mobs.length && (w < 3 || mobs.some((e) => e._tags.has("sh_rift_boss")))) { if (seen < 0) seen = k; else if (k - seen >= 3) break; }
          }
          const boss = mobs.find((e) => e._tags.has("sh_rift_boss"));
          waves.push(`موجة ${w}: ${mobs.length} وحش${boss ? " + زعيم «" + boss.nameTag.replace(/§./g, "") + "»" : ""}`);
          if (!mobs.length) { failures.push(`موجة ${w} ما طلعت`); break; }
          if (w === 3 && !boss) failures.push("الزعيم ما طلع بالموجة 3");
          if (w === 1) {
            // خطأ قديم: لما تموت/تبتعد ووحوش الموجة تختفي (تحميل أو اختفاء)، الصدع كان يعبر للموجة اللي بعدها. هسه لازم يبقى بنفس الموجة ويرجع الوحوش
            const back = { ...player.location };
            player.location = { x: rs.x + 300, y: 64, z: rs.z }; mobs.forEach((e) => { e._valid = false; }); advance(200);
            player.location = back; advance(220);
            const st1 = JSON.parse(world._dyn.sh_rift || "null"), again = entities.filter((e) => e._valid && e._tags.has("sh_rift"));
            console.log("  بعد ما ترجع للصدع (الوحوش اختفت): الموجة =", st1 && st1.wave, "| وحوش رجعت =", again.length);
            if (!st1 || st1.wave !== 1) failures.push("الصدع عبر الموجة لما اللاعب ابتعد/مات (لازم يبقى بنفس الموجة)");
            if (!again.length) failures.push("الصدع ما رجّع وحوش الموجة اللي اختفت");
            mobs = again;
          }
          if (w < 3) mobs.forEach((e) => { fire("entityDie", { deadEntity: e, damageSource: { damagingEntity: player } }); e._valid = false; });
          else if (boss) { advance(200); fire("entityDie", { deadEntity: boss, damageSource: { damagingEntity: player } }); boss._valid = false; }
        }
        console.log("  " + waves.join("\n  "));
        const waveBanners = [1, 2].every((n) => (stats.titles || []).some((t) => t.includes(`WAVE ${n}/3`))) && (stats.titles || []).some((t) => t.includes("THE WARDEN"));
        advance(40);
        const sealBanner = (stats.titles || []).some((t) => t.includes("RIFT SEALED"));
        console.log(`  إعلانات الموجات والزعيم فوق الهوت بار ${waveBanners ? "✔" : "✖"} | إعلان سد الصدع ${sealBanner ? "✔" : "✖"}`);
        if (!waveBanners || !sealBanner) failures.push("إعلانات الصدع (الموجات/الزعيم/السد) ما طلعت فوق الهوت بار");
        const sealed = !JSON.parse(world._dyn.sh_rift || "null");
        const loot = (stats.items || []).filter((t) => t.startsWith("sh:") || t.startsWith("minecraft:"));
        console.log("  انسد =", sealed, "| مكافآت:", loot.join(", "));
        if (!sealed) failures.push("الصدع ما انسد بعد قتل الزعيم");
        if (!loot.includes("sh:xp_scroll_big")) failures.push("مكافآت الصدع ما نزلت");
      }
    }
    // الصد المثالي: سنيك بلحظة الضربة = الضرر يرجع + الوحش يتشل + ضربة مضادة
    {
      setState({ ...baseState("iron"), rank: 1 }); hold(""); player.isSneaking = false; advance(30);
      spawnZombies(1, true); const z = entities[0]; z._hp = 400; z._max = 400; player._max = 20;
      const hitPlayer = (d) => { player._hp -= d; fire("entityHurt", { hurtEntity: player, damage: d, damageSource: { damagingEntity: z, cause: "entityAttack" } }); };
      const res = [];
      // بالتوقيت: سنيك ثم ضربة بعد 3 تكات
      player._hp = 20; player.isSneaking = true; advance(3); hitPlayer(6); advance(1); player.isSneaking = false;
      const restored = player._hp; res.push(`صد بالتوقيت: صحة ${restored}/20`);
      if (restored < 20) failures.push("الصد المثالي ما رجع الضرر");
      const d0 = stats.damage || 0; fire("entityHitEntity", { damagingEntity: player, hitEntity: z }); advance(1);
      const counter = Math.round((stats.damage || 0) - d0); res.push(`ضربة مضادة: ${counter}`);
      if (counter <= 0) failures.push("الضربة المضادة ما صارت");
      // متأخر: سنيك ثم ضربة بعد 15 تك = ما ينحسب
      advance(40); player._hp = 20; player.isSneaking = true; advance(15); hitPlayer(6); advance(1); player.isSneaking = false;
      res.push(`صد متأخر: صحة ${player._hp}/20`);
      if (player._hp >= 20) failures.push("الصد اشتغل بتوقيت متأخر");
      // سبام: ضغطات متكررة ما تنفع
      advance(40); player._hp = 20; player.isSneaking = true; advance(2); player.isSneaking = false; advance(2); player.isSneaking = true; advance(2); hitPlayer(6); player.isSneaking = false;
      res.push(`سبام سنيك: صحة ${player._hp}/20`);
      // Novice ما عنده الصد
      setState({ ...baseState("iron"), rank: 0 }); advance(40); player._hp = 20; player.isSneaking = true; advance(3); hitPlayer(6); player.isSneaking = false;
      res.push(`Novice: صحة ${player._hp}/20`);
      if (player._hp >= 20) failures.push("الصد اشتغل قبل رتبة Trainee");
      player._hp = 20; player._valid = true; advance(60); // الضربة المضادة تنتهي
      console.log("\nالصد المثالي:\n  " + res.join("\n  "));
    }
    // ضربة الإيقاع: ضربات بإيقاع ثابت (من رتبة Elite)
    {
      setState({ ...baseState("iron"), rank: 2 }); hold("");
      spawnZombies(1, true); const z = entities[0]; z._hp = 2000; z._max = 2000;
      const hitAt = () => fire("entityHitEntity", { damagingEntity: player, hitEntity: z });
      const res = [];
      const run = (beats, gaps) => { const d0 = stats.damage || 0; hitAt(); for (let i = 0; i < beats; i++) { advance(gaps[i % gaps.length]); hitAt(); } advance(2); return Math.round((stats.damage || 0) - d0); };
      // قبل Elite: ما تشتغل
      { const d = run(4, [10]); res.push(`رتبة Warrior بإيقاع صح: ضرر ${d}`); if (d > 0) failures.push("ضربة الإيقاع اشتغلت قبل رتبة Elite"); }
      advance(80); setState({ ...baseState("iron"), rank: 3 }); advance(20);
      // إيقاع غلط (فروقات عشوائية): ما تصير
      { const d = run(6, [10, 16, 8, 14, 7, 18]); res.push(`إيقاع مخربط: ضرر ${d}`); if (d > 0) failures.push("ضربة الإيقاع صارت بإيقاع غلط"); }
      advance(80);
      // إيقاع ثابت كل 10 تكات: الضربة 4 = Rhythm، 7 = Crescendo، 10 = Finale
      const hats0 = stats.soundIds.has("note.hat");
      const tiers = [];
      { const d0 = stats.damage || 0; hitAt(); advance(10); hitAt();
        for (let i = 1; i <= 9; i++) { advance(10); const dd = stats.damage || 0; hitAt(); const got = Math.round((stats.damage || 0) - dd); if (got > 0) tiers.push(`${i}:${got}`); } }
      res.push(`إيقاع ثابت (كل 0.5ث): ضربات قوية بعد ${tiers.join(" ")}`);
      if (tiers.length !== 3) failures.push("ضربة الإيقاع ما طلعت 3 مرات (الضربة 4، 7، 10)");
      if (!stats.soundIds.has("note.pling")) failures.push("نوتات الإيقاع ما طلعت");
      if (!stats.soundIds.has("note.hat")) failures.push("تك المترونوم ما طلع");
      // ضربة متأخرة شوية (±1 تك) تنحسب، وتوقف يقطع الإيقاع
      advance(80);
      { const d = run(3, [12, 13, 11]); res.push(`إيقاع بشري (12،13،11): ضرر ${d}`); if (d <= 0) failures.push("ضربة الإيقاع صعبة زيادة (ما تقبل فرق تكة)"); }
      advance(80);
      { const d0 = stats.damage || 0; hitAt(); advance(10); hitAt(); advance(10); hitAt(); advance(40); hitAt(); advance(2); const d = Math.round((stats.damage || 0) - d0); res.push(`توقف بنص الإيقاع: ضرر ${d}`); if (d > 0) failures.push("الإيقاع ما انقطع بعد التوقف"); }
      console.log("\nضربة الإيقاع:\n  " + res.join("\n  "));
    }
    // الوحوش: كل وحش يستعمل مهارته الخاصة الجديدة ويضرب
    {
      const SH = (await import("node:fs")).readFileSync(path.join(root, "AnimePowers/BP/scripts/shapes.js"), "utf8");
      const sid = (n) => Number((SH.match(new RegExp('"' + n + '": (\\d+)')) || [])[1]);
      const cases = [["sh:ember_imp", 9, "fireball"], ["sh:rust_guard", 9, "rock_chunk"], ["sh:shadow_hound", 7, "fang_jaw"], ["sh:sand_scorpion", 8, "particle:minecraft:splash_spell_emitter"]];   // العقرب: انفجار السم صار رشة جرعة حقيقية (جزيء) مو شكل
      console.log("\nمهارات الوحوش الخاصة:");
      for (const [type, dist, shape] of cases) {
        entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 400; player._max = 400; player._valid = true;
        const m = mkEntity(type, { x: 0, y: 64, z: dist }, dims.overworld, 60); entities.push(m);
        const d0 = stats.damage || 0; let seen = 0; const zones0 = stats.spawned;
        const pid = shape.startsWith("particle:") ? shape.slice(9) : null, pc0 = pid ? ((stats.pById || {})[pid] || 0) : 0;
        const keepRange = type === "sh:ember_imp";                                // العفريت لو انقض أول مرة يقرب ويبقى قريب وما يرمي كرة النار (اختبار عشوائي): نرجعه للمسافة
        for (let t = 0; t < 1500; t += 2) { advance(2); if (pid ? ((stats.pById || {})[pid] || 0) > pc0 : entities.some((e) => e._valid && e.typeId === "sh:fx_shape" && e.getProperty("sh:v") === sid(shape))) seen++; player.location = { x: 0, y: 64, z: 0 }; if (keepRange && !seen) m.location = { x: 0, y: 64, z: dist }; }
        const dmg = Math.round((stats.damage || 0) - d0);
        console.log(`  ${type.padEnd(18)} مسافة ${dist}: شكل ${shape} ${seen ? "✔" : "✖"} | ضرر للاعب ${dmg} | كيانات ${stats.spawned - zones0}`);
        if (!seen) failures.push(`${type}: المهارة الخاصة (${shape}) ما طلعت`);
        if (dmg <= 0) failures.push(`${type}: ما ضرب اللاعب`);
      }
      player._hp = 20; player._max = 20;
      // الرامي: تصويب ← سحب ← إطلاق (والسهم يطلع بنفس لحظة الإطلاق) ← تصويب
      entities.length = 0; player._valid = true; player.location = { x: 0, y: 64, z: 0 };
      const a = mkEntity("sh:training_archer", { x: 0, y: 64, z: 8 }, dims.overworld, 14); entities.push(a);
      const seq = []; let arrowsAtRelease = 0, arrows = 0;
      for (let t = 0; t < 200; t += 2) {
        advance(2);
        const v = a.getProperty("sh:state");
        if (seq[seq.length - 1] !== v) seq.push(v);
        const n = entities.filter((e) => e.typeId === "minecraft:arrow").length;
        if (n > arrows && v === 2) arrowsAtRelease++;
        arrows = n;
      }
      console.log("  الرامي: تسلسل الحالات", seq.join("→"), "| أسهم =", arrows, "| أسهم طلعت لحظة الإطلاق =", arrowsAtRelease);
      if (!seq.includes(3) || !seq.includes(1) || !seq.includes(2)) failures.push("الرامي ما يمر بالتصويب والسحب والإطلاق");
      if (arrows < 2 || arrowsAtRelease !== arrows) failures.push("سهم الرامي مو متزامن ويا حركة الإطلاق");
    }
    // وحوش رتبة Grim: كل مهارة من الثلاث تطلع وتضرب
    {
      console.log("\nوحوش Grim:");
      const want = { "sh:gloomhorn": { 3: "نبض القلب", 2: "الاندفاع والنطح", 4: "روح الغزال" }, "sh:hollow_seer": { 1: "الشعاع البرتقالي", 2: "جذور الأرض", 3: "زفير التجميد" }, "sh:veilfox": { 1: "ثعبان نار الثعلب", 2: "دوّامة المرايا", 3: "مطر الشمس", 4: "رفع القمر" }, "sh:magmamoth": { 1: "دكة الشقوق", 2: "كنس الجحيم", 3: "اندفاع الأنياب", 4: "القصف البركاني", 5: "درع الماغما" } , "sh:grey_bear": { 1: "عناق الدب", 4: "الخرمشة", 5: "نداء الجراء", 6: "السبات" } };
      const plans = { "sh:gloomhorn": [[2.5, 400], [9, 2400]], "sh:hollow_seer": [[4, 2800], [7, 2000], [14, 1200]], "sh:veilfox": [[4, 3600], [12, 3600]], "sh:magmamoth": [[4, 3600], [12, 4200]], "sh:grey_bear": [[2.5, 3600], [8, 3600]] };
      const SHP = JSON.parse(fs.readFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), "../../../scripts/shapes.js"), "utf8").match(/SHAPE = (\{.*?\});/)[1]);
      const wantShapes = { "sh:gloomhorn": ["spirit_stag"], "sh:hollow_seer": ["root_spike", "soul_orb"], "sh:veilfox": ["foxfire"], "sh:magmamoth": ["fireball"], "sh:grey_bear": [] };
      for (const type of Object.keys(want)) {
        const seenStates = new Set(); let dmgNear = 0, dmgFar = 0;
        stats.shapeV = {}; stats.pById = {};
        for (const [dist, ticks] of plans[type]) {
          entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true;
          const m = mkEntity(type, { x: 0, y: 64, z: dist }, dims.overworld, type === "sh:veilfox" ? 40 : type === "sh:magmamoth" ? 160 : type === "sh:grey_bear" ? 120 : 90); if (type === "sh:veilfox" || type === "sh:magmamoth" || type === "sh:grey_bear") m._max = type === "sh:veilfox" ? 90 : type === "sh:grey_bear" ? 300 : 260; entities.push(m);
          const d0 = stats.damage || 0;
          for (let t = 0; t < ticks; t += 2) {
            advance(2); seenStates.add(m.getProperty("sh:state"));
            player.location = { x: 0, y: 64, z: 0 };
            if (Math.hypot(m.location.x, m.location.z - dist) > 0.01 && t % 60 === 0) m.location = { x: 0, y: 64, z: dist };   // يرجع لمكانه (الاندفاع والمرآة يحركونه)
          }
          const dmg = Math.round((stats.damage || 0) - d0);
          if (dist < 5) dmgNear = dmg; else dmgFar = dmg;
        }
        const names = Object.entries(want[type]).map(([k, v]) => `${v} ${seenStates.has(Number(k)) ? "✔" : "✖"}`).join(" | ");
        console.log(`  ${type.padEnd(16)} ${names} | ضرر قريب ${dmgNear} بعيد ${dmgFar}`);
        for (const [k, v] of Object.entries(want[type])) if (!seenStates.has(Number(k))) failures.push(`${type}: مهارة ${v} ما طلعت`);
        const shp = wantShapes[type].map((n) => `${n}×${stats.shapeV[SHP[n]] || 0}`).join(" ");
        console.log(`  ${"".padEnd(16)} أشكال انرسمت: ${shp}`);
        for (const n of wantShapes[type]) if (!stats.shapeV[SHP[n]]) failures.push(`${type}: الشكل ${n} ما انرسم`);
        if (type === "sh:hollow_seer") {
          const pb = stats.pById || {};
          const beamFlame = (pb["minecraft:small_flame_particle"] || 0) + (pb["minecraft:colored_flame_particle"] || 0);
          console.log(`  ${"".padEnd(16)} شعاع الجزيئات: لهب×${beamFlame} خيوط×${pb["minecraft:glow_particle"] || 0} شرر×${pb["minecraft:electric_spark_particle"] || 0}`);
          if (!beamFlame || !pb["minecraft:glow_particle"]) failures.push("الشعاع: جزيئات الشعاع ما انرسمت");
        }
        if (dmgNear <= 0 || dmgFar <= 0) failures.push(`${type}: ما ضرب اللاعب`);
      }
      {
        entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true;
        const sets0 = stats.blockSets || 0, d0 = stats.damage || 0;
        advance(120);                                                        // ننتظر نزف الدب (5 ثواني) يخلص حتى ما ينحسب ضرر على الزفير
        const m = mkEntity("sh:hollow_seer", { x: 0, y: 64, z: 3 }, dims.overworld, 90); entities.push(m);
        let breathSeen = false;
        for (let t = 0; t < 3000 && !breathSeen; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (m.getProperty("sh:state") === 3) breathSeen = true; }
        const dBefore = stats.damage || 0; const _tr = []; const _sq = []; for (let q = 0; q < 30; q++) { const d00 = stats.damage || 0; advance(2); _sq.push(m.getProperty("sh:state")); if ((stats.damage || 0) > d00) _tr.push(`t${q * 2}:state${m.getProperty("sh:state")}:+${Math.round((stats.damage || 0) - d00)}`); } if (process.env.SH_DEBUG && _tr.length) console.log("   تتبع الضرر:", _tr.join(" "), "حالات:", _sq.join(""));
        const snowSet = (stats.blockSets || 0) - sets0, breathDmg = Math.round((stats.damage || 0) - dBefore);
        console.log(`  زفير التجميد: ثلج ناعم انحط = ${snowSet > 0 ? "✔" : "✖"} | ضرر وقت الزفير ${breathDmg}`);
        if (breathSeen && snowSet === 0) failures.push("زفير التجميد ما جمّد الشاشة (ثلج ناعم)");
        if (breathDmg > 0) failures.push("زفير التجميد صار يضر (لازم بس يبطئ)");
        entities.length = 0; advance(120);
      }
      player._hp = 20; player._max = 20; player._valid = true; entities.length = 0;
    }
    // الدب الرمادي: المسكة والرمية، النزف، الجراء والغضب، السبات والصحوة الغاضبة، الجلد الثخين
    {
      console.log("\nالدب الرمادي:");
      const clear = () => { entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true; };
      const bear = (hp, z = 2.5) => { const b = mkEntity("sh:grey_bear", { x: 0, y: 64, z }, dims.overworld, hp); b._max = 300; b._yaw = 180; entities.push(b); return b; };
      // 1) المسكة: نخلي اللاعب ثابت لحد ما يمسكه، بعدها الدب يتحكم بمكانه، ثم الرمية (knockback)
      clear(); let b = bear(300);
      let held = false, heldNear = false, thrown = false, k0 = 0;
      for (let t = 0; t < 4000 && !thrown; t += 2) {
        advance(2);
        const sNow = b.getProperty("sh:state");
        if (sNow === 2 && !held) { held = true; k0 = stats.knock || 0; }
        if (held && sNow === 2) heldNear = heldNear || Math.hypot(player.location.x - b.location.x, player.location.z - b.location.z) < 1.6;
        if (held && (stats.knock || 0) > k0) thrown = true;
        if (!held) { player.location = { x: 0, y: 64, z: 0 }; if (Math.hypot(b.location.x, b.location.z - 2.5) > 0.5 && t % 40 === 0) b.location = { x: 0, y: 64, z: 2.5 }; }
      }
      // 2) الإفلات بالضرب: نمسك مرة ثانية ونضربه 3 مرات
      clear(); b = bear(300);
      let grabbed2 = false, freed = false;
      for (let t = 0; t < 4000 && !freed; t += 2) {
        advance(2);
        const sNow = b.getProperty("sh:state");
        if (sNow === 2 && !grabbed2) { grabbed2 = true; }
        if (grabbed2 && sNow === 2) b._hp -= 5;                                 // ضربة كل تكين
        if (grabbed2 && sNow === 0) freed = true;
        if (!grabbed2) { player.location = { x: 0, y: 64, z: 0 }; if (Math.hypot(b.location.x, b.location.z - 2.5) > 0.5 && t % 40 === 0) b.location = { x: 0, y: 64, z: 2.5 }; }
      }
      // 3) الخرمشة + النزف: بعد ما يخرمش نشيل الدب ونشوف النزف يستمر
      clear(); b = bear(300, 3);
      let scratched = false;
      for (let t = 0; t < 4000 && !scratched; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (b.getProperty("sh:state") === 4 && (stats.pById || {})["minecraft:critical_hit_emitter"]) scratched = true; }
      advance(40); b._valid = false;
      const d0 = stats.damage || 0; advance(60); const bleedDmg = (stats.damage || 0) - d0;
      // 4) الجراء: ينادي جروين، يتعلقون باللاعب (بطء)، ولما يموت جرو الدب يغضب
      clear(); b = bear(300, 8);
      let cubs = [];
      const seenB = new Set();
      for (let t = 0; t < 5000 && cubs.length < 2; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; seenB.add(b.getProperty("sh:state")); if (b.getProperty("sh:state") === 0 && Math.hypot(b.location.x, b.location.z) < 6) b.location = { x: 0, y: 64, z: 8 }; cubs = entities.filter((x) => x._valid && x.typeId === "sh:bear_cub"); }
      if (process.env.SH_DEBUG) console.log("   [bear states]", [...seenB].join(","), "valid", b._valid, "hp", b._hp, "loc", JSON.stringify(b.location), "spawned", entities.filter((x) => x.typeId === "sh:bear_cub").length);
      const slow0 = (stats.effects || {}).slowness || 0;
      for (let t = 0; t < 120; t += 2) { advance(2); for (const c of cubs) if (c._valid && Math.hypot(c.location.x, c.location.z) > 1.2) c.location = { x: 0.5, y: 64, z: 0.5 }; }
      const clung = ((stats.effects || {}).slowness || 0) > slow0;
      const cub = cubs[0];
      if (cub) { cub._valid = false; fire("entityDie", { deadEntity: cub, damageSource: {} }); }
      advance(4);
      const enraged = b.getProperty("sh:hot") === 1;
      // 5) السبات: صحة قليلة → ينام ويتعافى؛ نضربه → يصحى بغضب ويدفع
      clear(); b = bear(110, 6);
      let slept = false, healed = false, woke = false; let hpS = 0;
      for (let t = 0; t < 5000 && !woke; t += 2) {
        advance(2); player.location = { x: 0, y: 64, z: 0 };
        const sNow = b.getProperty("sh:state");
        if (sNow === 6 && !slept) { slept = true; hpS = b._hp; }
        if (slept && sNow === 6 && b._hp > hpS + 1) healed = true;
        if (slept && healed && sNow === 6) { const k1 = stats.knock || 0; b._hp -= 8; advance(6); woke = b.getProperty("sh:hot") === 1 && (stats.knock || 0) >= k1; }
      }
      // 6) الجلد الثخين: ضربة من قدام ترجع 30%، ومن ورا تزيد 20%
      clear(); b = bear(300, 3);
      b._yaw = 180;                                                              // يباوع للاعب (−z)
      const hit = (from) => { const before = b._hp; player.location = from; b._hp -= 10; fire("entityHurt", { hurtEntity: b, damage: 10, damageSource: { damagingEntity: player } }); return before - b._hp; };
      const front = hit({ x: 0, y: 64, z: 0 }), back = hit({ x: 0, y: 64, z: 6 });
      console.log(`  المسكة ${held ? "✔" : "✖"} (اللاعب بحضنه ${heldNear ? "✔" : "✖"}) | الرمية ${thrown ? "✔" : "✖"} | الإفلات بـ3 ضربات ${freed ? "✔" : "✖"} | الخرمشة ${scratched ? "✔" : "✖"} | النزف بعدها ${Math.round(bleedDmg)} ${bleedDmg > 0 ? "✔" : "✖"}`);
      if (process.env.SH_DEBUG) console.log('   [bear debug]', JSON.stringify({ cubs: cubs.length, clung, enraged, hot: b.getProperty('sh:hot') }));
      console.log(`  جراء ${cubs.length} ${cubs.length === 2 ? "✔" : "✖"} | تعلق بالرجل (بطء) ${clung ? "✔" : "✖"} | غضب بموت الجرو ${enraged ? "✔" : "✖"} | سبات ${slept ? "✔" : "✖"} تعافي ${healed ? "✔" : "✖"} صحوة غاضبة ${woke ? "✔" : "✖"} | جلد: قدام ${front.toFixed(1)} ورا ${back.toFixed(1)} ${front < 10 && back > 10 ? "✔" : "✖"}`);
      if (!held || !heldNear) failures.push("الدب: المسكة ما اشتغلت");
      if (!thrown) failures.push("الدب: الرمية ما صارت");
      if (!freed) failures.push("الدب: ما تفلت بالضرب");
      if (!scratched || bleedDmg <= 0) failures.push("الدب: الخرمشة أو النزف ما اشتغل");
      if (cubs.length !== 2 || !clung || !enraged) failures.push("الدب: الجراء أو الغضب ما اشتغل");
      if (!slept || !healed || !woke) failures.push("الدب: السبات أو الصحوة الغاضبة ما اشتغلت");
      if (!(front < 10 && back > 10)) failures.push("الدب: الجلد الثخين ما اشتغل");
      clear(); player._hp = 20; player._max = 20;
    }
    // السرعوف المصلّي: وضعية الصلاة والرد المضاعف، التمويه والطعنة، قفل المقص (وكسره بالداش)، الانسلاخ وانفجار القشرة
    {
      console.log("\nالسرعوف المصلّي:");
      const SHP = JSON.parse(fs.readFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), "../../../scripts/shapes.js"), "utf8").match(/SHAPE = (\{.*?\});/)[1]);
      const clear = () => { entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true; stats.shapeV = {}; };
      const mantis = (hp, z) => { const m = mkEntity("sh:prayer_mantis", { x: 0, y: 64, z }, dims.overworld, hp); m._max = 340; m._yaw = 180; entities.push(m); return m; };
      const waitState = (m, want, z, maxT = 6000) => { for (let t = 0; t < maxT; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (m.getProperty("sh:state") === want) return true; if (m.getProperty("sh:state") === 0 && t % 40 === 0) m.location = { x: 0, y: 64, z }; } return false; };
      // 1) وضعية الصلاة: ضربة 10 → السرعوف ما ينقص، والضارب ياخذ 20
      clear(); let m = mantis(340, 3);
      const stance = waitState(m, 1, 3); advance(4);
      const hp0 = m._hp; m._hp -= 10; const dmg0 = stats.damage || 0;
      fire("entityHurt", { hurtEntity: m, damage: 10, damageSource: { damagingEntity: player } });
      const parried = m._hp >= hp0 - 0.01, countered = m.getProperty("sh:state") === 6;
      advance(20);
      const back = Math.round((stats.damage || 0) - dmg0);
      const haloN = stats.shapeV[SHP.prayer_halo] || 0, xN = stats.shapeV[SHP.scythe_x] || 0;
      // 2) التمويه: شبه شفاف + بدون اسم، يقرب ويطعن، وينكشف
      clear(); m = mantis(340, 9);
      const camo = waitState(m, 2, 9); advance(4);
      const transparent = m.getProperty("sh:camo") === 1 && m.hasTag("sh_camo");
      advance(40); const noName = m.nameTag === "";
      m.location = { x: 0, y: 64, z: 2 }; const dmg1 = stats.damage || 0;
      let stabbed = false; for (let t = 0; t < 40 && !stabbed; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (m.getProperty("sh:state") === 3) stabbed = true; }
      advance(6);
      const stabDmg = Math.round((stats.damage || 0) - dmg1), revealed = m.getProperty("sh:camo") === 0;
      const swirlN = stats.shapeV[SHP.leaf_swirl] || 0, thrustN = stats.shapeV[SHP.scythe_thrust] || 0;
      const leaves = (stats.pById || {})["minecraft:biome_tinted_leaves_particle"] || 0;
      // 3) قفل المقص: يمسك ويثبت اللاعب، وبعد 1.5 ثانية قصة؛ وبالمرة الثانية الداش يكسره
      clear(); m = mantis(340, 2.5);
      let locked = false; for (let t = 0; t < 8000 && !locked; t += 2) { advance(2); const s = m.getProperty("sh:state"); if (s === 4) locked = true; else { player.location = { x: 0, y: 64, z: 0 }; if (s === 0 && t % 40 === 0) m.location = { x: 0, y: 64, z: 2.5 }; } }
      const dmg2 = stats.damage || 0; let pinned = true;
      for (let t = 0; t < 34; t += 2) { advance(2); if (m.getProperty("sh:state") === 4 && Math.hypot(player.location.x - m.location.x, player.location.z - m.location.z) > 2.6) pinned = false; }
      const snip = Math.round((stats.damage || 0) - dmg2), lockN = stats.shapeV[SHP.scissor_lock] || 0;
      clear(); m = mantis(340, 2.5);
      let locked2 = false; for (let t = 0; t < 8000 && !locked2; t += 2) { advance(2); const s = m.getProperty("sh:state"); if (s === 4) locked2 = true; else { player.location = { x: 0, y: 64, z: 0 }; if (s === 0 && t % 40 === 0) m.location = { x: 0, y: 64, z: 2.5 }; } }
      advance(4); player.location = { x: 3.2, y: 64, z: player.location.z }; const dmg3 = stats.damage || 0; advance(4);
      const broke = m.getProperty("sh:state") === 0; advance(40); const noSnip = (stats.damage || 0) - dmg3 < 6;
      // 4) الانسلاخ: صحة النص → قشرة + جلد جديد + انفجار + سرعة
      clear(); m = mantis(160, 6); const sp0 = (stats.effects || {}).speed || 0;
      const molt = waitState(m, 5, 6, 200); const dmg4 = stats.damage || 0;
      player.location = { x: 0, y: 64, z: 5 };
      for (let t = 0; t < 90; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 5 }; }
      const newSkin = m.getProperty("sh:hot") === 1, huskN = stats.shapeV[SHP.molt_husk] || 0, burstN = stats.shapeV[SHP.husk_burst] || 0;
      const boom = Math.round((stats.damage || 0) - dmg4), faster = ((stats.effects || {}).speed || 0) > sp0;
      console.log(`  وضعية الصلاة ${stance ? "✔" : "✖"} | صد ${parried ? "✔" : "✖"} | رد ${countered ? "✔" : "✖"} ضرر راجع ${back} ${back >= 20 ? "✔" : "✖"} | هالة×${haloN} منجلين X×${xN}`);
      console.log(`  تمويه ${camo ? "✔" : "✖"} شبه شفاف ${transparent ? "✔" : "✖"} بدون اسم ${noName ? "✔" : "✖"} | طعنة ${stabbed ? "✔" : "✖"} ضرر ${stabDmg} | انكشف ${revealed ? "✔" : "✖"} | دوامة أوراق×${swirlN} طعنة×${thrustN} أوراق شجر×${leaves}`);
      console.log(`  قفل المقص ${locked ? "✔" : "✖"} تثبيت ${pinned ? "✔" : "✖"} قصة ${snip} ${snip > 0 ? "✔" : "✖"} مقص×${lockN} | الداش يكسره ${locked2 && broke && noSnip ? "✔" : "✖"}`);
      console.log(`  انسلاخ ${molt ? "✔" : "✖"} جلد جديد ${newSkin ? "✔" : "✖"} قشرة×${huskN} انفجار×${burstN} ضرر ${boom} | أسرع ${faster ? "✔" : "✖"}`);
      if (!stance || !parried || !countered || back < 20 || !haloN || !xN) failures.push("السرعوف: وضعية الصلاة أو الرد المضاعف ما اشتغل");
      if (!camo || !transparent || !noName || !stabbed || stabDmg <= 0 || !revealed || !swirlN || !thrustN || !leaves) failures.push("السرعوف: التمويه أو الطعنة ما اشتغلت");
      if (!locked || !pinned || snip <= 0 || !lockN) failures.push("السرعوف: قفل المقص ما اشتغل");
      if (!(locked2 && broke && noSnip)) failures.push("السرعوف: الداش ما يكسر قفل المقص");
      if (!molt || !newSkin || !huskN || !burstN || boom <= 0 || !faster) failures.push("السرعوف: الانسلاخ ما اشتغل");
      clear(); player._hp = 20; player._max = 20;
    }
    // ضريحا السيف: حارسان يظهران، وموتهما (الاثنين) يطلّع صندوق السيف المناسب
    {
      console.log("\nضريحا السيف:");
      for (const [type, bosses, sword] of [["lightshrine", ["sh:veilfox", "sh:magmamoth"], "sh:silver_oath"], ["shrine", ["sh:gloomhorn", "sh:hollow_seer"], "sh:dark_katana"]]) {
        entities.forEach((x) => (x._valid = false)); entities.length = 0;
        player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true;
        world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 14, y: 64, z: 14, type, rot: 0, seed: 7, v: 2, ok: 1 }]));
        stats.setTypes = []; stats.chestItems = [];
        advance(420);
        const alive = (t) => entities.filter((e) => e._valid && e.typeId === t && e._tags.has("sh_boss")).length;      // نعد الحراس بس (وحوش الطبيعة من نفس النوع ما تحسب)
        const spawned = bosses.every((t) => alive(t) === 1);
        advance(420);
        const noDup = bosses.every((t) => alive(t) === 1);              // ما يتكرر ظهورهم
        const chest0 = stats.setTypes.some((q) => q[3] === "minecraft:chest");
        const kill = (t) => { const e = entities.find((x) => x._valid && x.typeId === t && x._tags.has("sh_boss")); e._valid = false; fire("entityDie", { deadEntity: e, damageSource: {} }); };
        kill(bosses[0]);
        const afterOne = stats.setTypes.some((q) => q[3] === "minecraft:chest");
        advance(420);                                                    // الأول ما يرجع، الثاني يبقى
        const respawnDead = alive(bosses[0]) > 0;
        kill(bosses[1]);
        const chest = stats.setTypes.filter((q) => q[3] === "minecraft:chest");
        const gotSword = stats.chestItems.includes(sword);
        const wr = JSON.parse(world.getDynamicProperty("sh_structs"))[0];
        console.log(`  ${type.padEnd(12)} حارسان ${spawned ? "✔" : "✖"} | بدون تكرار ${noDup ? "✔" : "✖"} | صندوق قبل الموت ${chest0 || afterOne ? "✖" : "✔(ما في)"} | الميت ما يرجع ${respawnDead ? "✖" : "✔"} | صندوق بعد موتهما ${chest.length === 1 ? "✔" : "✖"} (${chest[0] ? chest[0].slice(0, 3).join(",") : "-"}) | السيف ${gotSword ? "✔" : "✖"} (${sword}) | ختم مكسور ${wr.c ? "✔" : "✖"}`);
        if (!spawned) failures.push(`${type}: الحارسان ما ظهروا`);
        if (!noDup) failures.push(`${type}: الحراس يتكررون`);
        if (chest0 || afterOne) failures.push(`${type}: صندوق ظهر قبل موت الاثنين`);
        if (respawnDead) failures.push(`${type}: حارس ميت رجع`);
        if (chest.length !== 1) failures.push(`${type}: الصندوق ما ظهر (أو تكرر) بعد موتهما`);
        if (!gotSword) failures.push(`${type}: السيف ${sword} مو بالصندوق`);
      }
      entities.forEach((x) => (x._valid = false)); entities.length = 0; world.setDynamicProperty("sh_structs", "[]");
      player._hp = 20; player._max = 20; player._valid = true;
    }
    // برج الهاوية: وحوش كل طابق تطلع أول ما يوصله اللاعب (مرة وحدة)، والطابق السابع وحوش عالية؛ موتهم يطلّع صندوق القمة
    {
      console.log("\nبرج الهاوية:");
      entities.forEach((x) => (x._valid = false)); entities.length = 0;
      player._hp = 2000; player._max = 2000; player._valid = true;
      world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 200, y: 64, z: 200, type: "tower", rot: 1, seed: 11, v: 2, ok: 1 }]));
      stats.setTypes = []; stats.chestItems = [];
      const LOW = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"], GRIM = ["sh:gloomhorn", "sh:hollow_seer", "sh:veilfox"], HIGH = ["sh:magmamoth", "sh:grey_bear", "sh:prayer_mantis"];
      const tagged = () => entities.filter((e) => e._valid && e._tags.has("sh_tower"));
      const counts = [];
      let ok13 = true, ok46 = true, once = true, sealOn = false, sealOff = false, orbs = false, hudFloor = "", hudClear = "";
      for (let k = 0; k < 6; k++) {
        const before = tagged().length;
        player.location = { x: 201.5, y: 64 + k * 7, z: 199.5 }; advance(20);
        const neu = tagged().slice(before);
        counts.push(neu.length);
        if (k <= 2 && (neu.length !== 3 + k || !neu.every((e) => LOW.includes(e.typeId)))) ok13 = false;
        if (k === 0) {                                                       // ختم الدرج: زجاج بنفسجي لحد ما ينظف الطابق، وينكسر بموتهم
          sealOn = stats.setTypes.some((q) => q[3] === "minecraft:purple_stained_glass" && q[1] === 64 + 6);
          hudFloor = (stats.actionBars[stats.actionBars.length - 1] || "").replace(/§./g, "");
          const xp0 = entities.filter((e) => e.typeId === "minecraft:xp_orb").length;
          for (const e of neu) { e._valid = false; fire("entityDie", { deadEntity: e, damageSource: {} }); }
          advance(20);
          sealOff = stats.setTypes.filter((q) => q[3] === "minecraft:air" && q[1] === 64 + 6).length >= 4;
          orbs = entities.filter((e) => e.typeId === "minecraft:xp_orb").length > xp0;
          hudClear = (stats.actionBars[stats.actionBars.length - 1] || "").replace(/§./g, "");
        }
        if (k >= 3 && (neu.length < 3 || !neu.some((e) => GRIM.includes(e.typeId)))) ok46 = false;
        advance(20); if (k > 0 && tagged().length !== before + neu.length) once = false;          // ما يتكرر
        neu.forEach((e) => (e._valid = false));
      }
      player.location = { x: 200.5, y: 64 + 42, z: 200.5 }; advance(20);
      const tops = entities.filter((e) => e._valid && e._tags.has("sh_tower_top"));
      const topOk = tops.length >= 1 && tops.length <= 2 && tops.every((e) => HIGH.includes(e.typeId));
      const chest0 = stats.setTypes.some((q) => q[3] === "minecraft:chest");
      // تبخروا (بدون موت) ← يرجعون لما اللاعب بالطابق
      const types0 = tops.map((e) => e.typeId).sort().join(",");
      tops.forEach((e) => (e._valid = false)); advance(20);
      const back = entities.filter((e) => e._valid && e._tags.has("sh_tower_top"));
      const respawned = back.map((e) => e.typeId).sort().join(",") === types0;
      for (const e of back) { e._valid = false; fire("entityDie", { deadEntity: e, damageSource: {} }); }
      advance(20);
      const chest = stats.setTypes.filter((q) => q[3] === "minecraft:chest");
      const loot = stats.chestItems.filter(Boolean);
      const wr = JSON.parse(world.getDynamicProperty("sh_structs"))[0];
      console.log(`  الطوابق 1-6: ${counts.join("، ")} وحش | 1-3 Lowly بالعدد ${ok13 ? "✔" : "✖"} | 4-6 أقوى (Grim) ${ok46 ? "✔" : "✖"} | مرة وحدة ${once ? "✔" : "✖"}`);
      console.log(`  الطابق 7: ${types0} ${topOk ? "✔" : "✖"} | يرجعون إذا تبخروا ${respawned ? "✔" : "✖"} | صندوق قبل القتل ${chest0 ? "✖" : "✔(ما في)"} | صندوق بعد القتل ${chest.length === 1 ? "✔" : "✖"} (${chest[0] ? chest[0].slice(0, 3).join(",") : "-"}) | غنائم ${loot.length} | مكتمل ${wr.c ? "✔" : "✖"}`);
      console.log(`  ختم الدرج ${sealOn ? "✔" : "✖"} | ينكسر لما ينظف الطابق ${sealOff ? "✔" : "✖"} | خبرة ${orbs ? "✔" : "✖"} | الـHUD: "${hudFloor.split("\n").find((l) => l.includes("Abyss")) || "-"}" ثم "${hudClear.split("\n").find((l) => l.includes("Abyss")) || "-"}"`);
      if (!sealOn || !sealOff || !orbs || !/Floor 1\/7/.test(hudFloor) || !/Cleared/.test(hudClear)) failures.push("البرج: الختم أو الـHUD أو جوائز الطابق ما تشتغل");
      if (!ok13 || !ok46 || !once) failures.push("البرج: وحوش الطوابق 1-6 غلط أو تتكرر");
      if (!topOk || !respawned) failures.push("البرج: وحوش الطابق السابع ما ظهرت أو ما رجعت");
      if (chest0 || chest.length !== 1 || loot.length < 3 || !wr.c) failures.push("البرج: صندوق القمة ما ظهر صح");
      entities.forEach((x) => (x._valid = false)); entities.length = 0; world.setDynamicProperty("sh_structs", "[]");
      player._hp = 20; player._max = 20; player._valid = true; player.location = { x: 0, y: 64, z: 0 };
    }
    // v1.35: مواد الوحوش، الدروع، المانا والجرعات، البرج المختوم، الخيميائي
    {
      console.log("\nالعتاد والمانا والجرعات:");
      entities.forEach((x) => (x._valid = false)); entities.length = 0;
      player._hp = 40; player._max = 40; player._valid = true; player.location = { x: 0, y: 64, z: 0 };
      // 1) مواد الوحوش
      stats.items = [];
      const kill = (t) => { const m = mkEntity(t, { x: 2, y: 64, z: 2 }, dims.overworld, 10); entities.push(m); m._valid = false; fire("entityDie", { deadEntity: m, damageSource: { damagingEntity: player } }); };
      for (let i = 0; i < 4; i++) { kill("sh:grey_bear"); kill("sh:prayer_mantis"); }
      for (let i = 0; i < 12; i++) kill("sh:shadow_hound");                  // 55% لكل وحدة: 12 قتلة حتى ما يفشل الاختبار بالصدفة
      const dropped = new Set(stats.items);
      const dropsOk = ["sh:bear_hide", "sh:mantis_chitin", "sh:shadow_pelt"].every((x) => dropped.has(x));
      // 2) المانا: مهارة غالية تنعاد بدون تصفير كولداون لحد ما تخلص المانا
      setState(baseState("star")); spawnZombies(); system_cd_reset();
      const msgs0 = stats.actionBars.length; let blocked = false, used = 0;
      for (let i = 0; i < 16 && !blocked; i++) {
        const before = stats.damage || 0;
        fire("scriptEventReceive", { id: "sh:cdreset_cd_only", message: "", sourceEntity: player });
        await useItem("sh:skill_meteor"); advance(5);                                  // دورة HUD كاملة (كل 5 تكات) حتى الرسالة أكيد تنعرض
        const bar = (stats.bottom || "") + " " + stats.actionBars.slice(-4).join(" ");
        if (/Not enough mana/.test(bar)) blocked = true; else used++;
        advance(30);
      }
      advance(200);
      const hudMana = (stats.actionBars[stats.actionBars.length - 1] || "");
      const manaShown = /\/1[0-9]{2}/.test(hudMana.replace(/§./g, ""));
      // 3) الجرعات: كل جرعة تنشرب (itemCompleteUse)
      const eff0 = { ...(stats.effects || {}) };
      for (const pid of ["sh:potion_vitality", "sh:potion_mana", "sh:potion_might", "sh:potion_bulwark", "sh:potion_focus", "sh:potion_swift"]) fire("itemCompleteUse", { source: player, itemStack: new ItemStack(pid) });
      advance(25);
      const eff = stats.effects || {};
      const potOk = (eff.regeneration || 0) > (eff0.regeneration || 0) && (eff.strength || 0) > (eff0.strength || 0) && (eff.resistance || 0) > (eff0.resistance || 0) && (eff.speed || 0) > (eff0.speed || 0);
      const buffs = JSON.parse(player.getDynamicProperty("sh_buffs") || "{}");
      const buffsOk = ["might", "bulwark", "focus", "swift"].every((k) => buffs[k] > 0);
      advance(10);
      const hudBuff = stats.actionBars[stats.actionBars.length - 1] || "";
      // التركيز: كولداون أقصر (المهارة تنعاد أسرع)
      system_cd_reset(); await useItem("sh:skill_meteor"); advance(2);
      // 4) طقم الدرع: 4 قطع صياد = سرعة وقفز
      const sp0 = (stats.effects || {}).jump_boost || 0;
      player._equip = { Head: new ItemStack("sh:hunter_helmet"), Chest: new ItemStack("sh:hunter_chestplate"), Legs: new ItemStack("sh:hunter_leggings"), Feet: new ItemStack("sh:hunter_boots") };
      advance(90);
      const setOk = ((stats.effects || {}).jump_boost || 0) > sp0 && stats.actionBars.some((b) => /Set bonus/.test(b));
      // طقم السرعوف: الرد على الضربات (20%)
      player._equip = { Head: new ItemStack("sh:mantis_helmet"), Chest: new ItemStack("sh:mantis_chestplate"), Legs: new ItemStack("sh:mantis_leggings"), Feet: new ItemStack("sh:mantis_boots") };
      advance(50);
      const foe = mkEntity("minecraft:zombie", { x: 1, y: 64, z: 1 }, dims.overworld, 500); entities.push(foe);
      const fh0 = foe._hp;
      for (let i = 0; i < 60; i++) fire("entityHurt", { hurtEntity: player, damage: 4, damageSource: { damagingEntity: foe, cause: "entityAttack" } });
      const countered = foe._hp < fh0;
      player._equip = {};
      // 5) الخيميائي: يظهر بالقرية، ويطبخ جرعة لما تكون عندك المواد
      world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 300, y: 64, z: 300, type: "village", rot: 0, seed: 5, v: 2, ok: 1 }]));
      player.location = { x: 300, y: 64, z: 320 };
      advance(420);
      const alch = entities.find((e) => e._valid && e.typeId === "sh:alchemist");
      inventory.fill(undefined);
      inventory[3] = new ItemStack("sh:shadow_pelt", 5); inventory[4] = new ItemStack("sh:spirit_fur", 2);
      const ui = (await import("@minecraft/server-ui")).sim;
      ui.nextSelection = 0; ui.formsShown.length = 0;
      if (alch) fire("playerInteractWithEntity", { player, target: alch });
      await new Promise((r) => setTimeout(r, 20)); advance(2);
      const brewed = inventory.some((it) => it && it.typeId === "sh:potion_vitality");
      const paid = (inventory[3] && inventory[3].amount) === 2;
      world.setDynamicProperty("sh_structs", "[]"); inventory.fill(undefined);
      console.log(`  مواد الوحوش ${dropsOk ? "✔" : "✖"} (${[...dropped].filter((x) => x.includes("hide") || x.includes("chitin") || x.includes("pelt") || x.includes("scythe") || x.includes("claw")).join(", ")})`);
      console.log(`  المانا: مهارة غالية انعادت ${used} مرات ثم ${blocked ? "انقفلت (مانا ما تكفي) ✔" : "ما انقفلت ✖"} | المانا بالـHUD ${manaShown ? "✔" : "✖"}`);
      console.log(`  الجرعات: تأثيرات ${potOk ? "✔" : "✖"} | تقويات محفوظة ${buffsOk ? "✔" : "✖"} (${Object.keys(buffs).join(",")}) | أيقونات بالـHUD ${/[-]/.test(hudBuff) ? "✔" : "✖"}`);
      console.log(`  طقم الصياد (بونص) ${setOk ? "✔" : "✖"} | رد طقم السرعوف ${countered ? "✔" : "✖"}`);
      console.log(`  الخيميائي ظهر بالقرية ${alch ? "✔" : "✖"} | طبخ جرعة ${brewed ? "✔" : "✖"} | أخذ المواد ${paid ? "✔" : "✖"}`);
      if (!dropsOk) failures.push("مواد الوحوش ما طاحت");
      if (!blocked || used < 2 || !manaShown) failures.push("المانا ما تشتغل صح");
      if (!potOk || !buffsOk) failures.push("الجرعات ما تشتغل");
      if (!setOk || !countered) failures.push("بونص طقم الدرع ما يشتغل");
      if (!alch || !brewed || !paid) failures.push("الخيميائي ما يشتغل");
      entities.forEach((x) => (x._valid = false)); entities.length = 0; system_cd_reset();
      player._hp = 20; player._max = 20; player.location = { x: 0, y: 64, z: 0 };
      fire("scriptEventReceive", { id: "sh:clearbuffs", message: "", sourceEntity: player });
    }
    // الداش: ضغطتين على يمين/يسار/خلف
    {
      console.log("\nالداش:");
      const tap = (v, n = 3) => { player._mv = v; advance(n); };
      const idle = (n = 3) => { player._mv = { x: 0, y: 0 }; advance(n); };
      const dbl = (v) => { tap(v); idle(); tap(v); idle(10); };       // ضغطة، إفلات، ضغطة، ثم نخلي الداش يخلص
      const at = () => ({ x: player.location.x, z: player.location.z });
      const reset = () => { player.location = { x: 0, y: 64, z: 0 }; };
      const s0 = stats.particles;
      // مقفول عند الرتبة 0 (Novice)
      setState({ ...baseState("star"), rank: 0 }); player.setDynamicProperty("sh_dash", undefined); reset(); advance(14);
      let a = at(); dbl({ x: 1, y: 0 }); let b = at();
      const lockedOk = Math.hypot(b.x - a.x, b.z - a.z) < 0.5;
      // أول رتبة (Trainee) تفتحه ويجي إشعار، والعلم يبقى
      const m0 = stats.messages.length;
      setState({ ...baseState("star"), rank: 1 }); advance(14);
      const unlockMsg = stats.messages.slice(m0).some((q) => /Dash unlocked/.test(q)) && player.getDynamicProperty("sh_dash") === 1;
      reset(); advance(40);
      a = at(); dbl({ x: 1, y: 0 }); b = at();
      const dx1 = b.x - a.x, dz1 = b.z - a.z;
      const side1 = Math.abs(Math.abs(dx1) - 3) < 0.3 && Math.abs(dz1) < 0.5;
      reset(); a = at(); dbl({ x: 1, y: 0 }); b = at();                  // ضمن الكول داون (1.8 ثانية): ما يشتغل
      const blocked = Math.hypot(b.x - a.x, b.z - a.z) < 0.5;
      advance(60); reset(); a = at(); dbl({ x: 0, y: -1 }); b = at();
      const back = Math.abs(b.z - a.z + 3) < 0.3 && Math.abs(b.x - a.x) < 0.5;     // خلف = عكس اتجاه البصر (+z)
      advance(60);
      // معايرة: جهاز x موجب عنده = يمين (السرعة تبين يمين لما x موجب)
      reset(); player._vel = { x: -0.2, y: 0, z: 0 }; tap({ x: 1, y: 0 }, 14); player._vel = { x: 0, y: 0, z: 0 }; idle(40);
      reset(); a = at(); dbl({ x: 1, y: 0 }); b = at();
      const calibrated = b.x - a.x < -2.7;                                // يمين (نسبة للبصر +z) = -x
      player._mv = { x: 0, y: 0 };
      // الكول داون حسب الرتبة: Trainee ثانيتين (40 تك)، Master 0.9 ثانية (18 تك).
      // الداش الأول يبدأ بالضغطة الثانية ويبقى بعده 12 تك؛ الضغطة السريعة (تك، تك، تك) ضغطتها الثانية بالتك 3 → الفاصل = 12 + انتظار + 3
      const quick = (v) => { tap(v, 1); idle(1); tap(v, 1); idle(10); };
      const cdTry = (rank, wait) => { setState({ ...baseState("star"), rank }); advance(80); reset(); dbl({ x: 1, y: 0 }); advance(wait); reset(); const p0 = at(); quick({ x: 1, y: 0 }); const p1 = at(); return Math.hypot(p1.x - p0.x, p1.z - p0.z) > 2.5; };
      const tr1 = cdTry(1, 20), tr2 = cdTry(1, 26), ms1 = cdTry(6, 0), ms2 = cdTry(6, 4);
      const cdOk = !tr1 && tr2 && !ms1 && ms2;
      console.log(`  الكول داون بالرتبة: Trainee (35 تك ممنوع ${tr1 ? "✖" : "✔"}، 41 تك يشتغل ${tr2 ? "✔" : "✖"}) | Master (15 تك ممنوع ${ms1 ? "✖" : "✔"}، 19 تك يشتغل ${ms2 ? "✔" : "✖"})`);
      if (!cdOk) failures.push("كول داون الداش حسب الرتبة غلط");
      // دائم: حتى لو رجعت الرتبة 0 (مثلاً ريسيت) يبقى الداش
      setState({ ...baseState("star"), rank: 0 }); advance(60); reset(); a = at(); dbl({ x: 0, y: -1 }); b = at();
      const forever = Math.abs(b.z - a.z + 3) < 0.3;
      advance(60); reset(); const fa = at(); dbl({ x: 0, y: 1 }); const fb = at();
      const noForward = Math.hypot(fb.x - fa.x, fb.z - fa.z) < 0.3;                     // للأمام ماكو داش
      if (!noForward) failures.push("الداش اشتغل للأمام");
      console.log(`  مقفول قبل أول رتبة ${lockedOk ? "✔" : "✖"} | ينفتح بأول رتبة + إشعار ${unlockMsg ? "✔" : "✖"} | يبقى للأبد ${forever ? "✔" : "✖"}`);
      if (!lockedOk) failures.push("الداش اشتغل قبل أول رتبة");
      if (!unlockMsg) failures.push("الداش ما انفتح بأول رتبة (أو ما جاء إشعار)");
      if (!forever) failures.push("الداش اختفى بعد ما انفتح");
      console.log(`  يمين/يسار بالافتراضي: إزاحة ${dx1.toFixed(1)},${dz1.toFixed(1)} ${side1 ? "✔" : "✖"} | ضمن الكول داون ممنوع ${blocked ? "✔" : "✖"} | خلف ${back ? "✔" : "✖"} (${(b.z - a.z).toFixed(1)}) | معايرة الإشارة ${calibrated ? "✔" : "✖"} | للأمام ماكو ${noForward ? "✔" : "✖"} | بدون جزيئات ${/spawnParticle|MolangVariableMap/.test(fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/dash.js"), "utf8")) ? "✖" : "✔"}`);
      if (!side1) failures.push(`الداش جانبي ما اشتغل أو المسافة غلط (${dx1.toFixed(1)},${dz1.toFixed(1)})`);
      if (!blocked) failures.push("الداش اشتغل ضمن الكول داون");
      if (!back) failures.push("داش الخلف ما اشتغل");
      if (!calibrated) failures.push("معايرة اتجاه الداش ما اشتغلت");
      const dashSrc = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/dash.js"), "utf8");
      if (/spawnParticle|MolangVariableMap/.test(dashSrc)) failures.push("الداش لازم بدون جزيئات");
      reset();
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
