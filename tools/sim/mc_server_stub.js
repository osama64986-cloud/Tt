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
// v1.43: تعريفات خصائص الكيانات من ملفات BP: setProperty بالمحاكي يرمي خطأ مثل اللعبة (خاصية مو معرّفة، نوع غلط، برا المدى)
const PROP_DEFS = {};
function loadPropDefs(root) {
  try {
    const dir = path.join(root, "AnimePowers/BP/entities");
    for (const f of fs.readdirSync(dir)) {
      const e = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"))["minecraft:entity"];
      if (e && e.description && e.description.properties) PROP_DEFS[e.description.identifier] = e.description.properties;
    }
  } catch (err) { /* */ }
}
function checkProp(typeId, k, v) {
  const defs = PROP_DEFS[typeId];
  if (!defs) return;
  const d = defs[k];
  if (!d) throw new Error(`setProperty: ${typeId} has no property ${k}`);
  if (d.type === "int" && !Number.isInteger(v)) throw new Error(`setProperty: ${typeId} ${k} needs an int, got ${v}`);
  if ((d.type === "int" || d.type === "float") && (typeof v !== "number" || v < d.range[0] || v > d.range[1])) throw new Error(`setProperty: ${typeId} ${k}=${v} outside ${JSON.stringify(d.range)}`);
}
function loadFxTimers(root) {
  loadPropDefs(root);
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

// عرض السطر بالبكسل مثل ماينكرافت (خط default: أغلب الحروف 6 مع الفراغ، الضيقة أقل، العريض +1، رموز glyph_E5 حسب رسمها)
const MC_NARROW = { " ": 4, "!": 2, "'": 2, ",": 2, ".": 2, ":": 2, ";": 2, "|": 2, i: 2, l: 3, I: 4, t: 4, "[": 4, "]": 4, "(": 5, ")": 5, f: 5, k: 5, "<": 5, ">": 5, "*": 5, "{": 5, "}": 5, '"': 5, "`": 3, "@": 7, "~": 7 };
const GLYPH_W = {0: 8.5, 1: 8.5, 2: 8.5, 3: 8.5, 4: 7.5, 5: 7.5, 6: 8.5, 7: 8.5, 8: 8.5, 9: 8.5, 10: 8.5, 11: 8.5, 12: 7.5, 13: 8.5, 14: 8.5, 16: 8.5, 17: 8.0, 18: 8.0, 19: 8.0, 20: 8.0, 21: 9.0, 22: 9.0, 32: 8.0, 33: 8.0, 34: 7.5, 35: 7.0, 36: 8.5, 37: 7.5, 38: 9.0, 39: 9.0, 40: 9.0, 48: 9.0, 49: 9.0, 50: 9.0, 51: 7.5, 52: 8.5, 53: 9.0, 54: 9.0, 55: 5.0, 56: 8.5, 57: 8.5, 58: 8.0, 59: 8.0, 60: 8.0, 61: 8.0, 62: 8.0};
// شريط أعلى الشاشة (Boss bar): كيان sh:hud_bar / sh:hud_bar_near — عنوانه اسمه، وامتلاؤه صحته من 1000
function bossBar(type = "sh:hud_bar") {
  const e = entities.find((x) => x._valid && x.typeId === type);
  return e ? { name: (e.nameTag || "").replace(/§./g, ""), fill: e._hp / 1000, e } : null;
}
export function mcWidth(line) {
  let w = 0, bold = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === "§") { const c = line[i + 1] || ""; i++; if (c === "l") bold = true; else if (c === "r" || /[0-9a-f]/.test(c)) bold = false; continue; }
    const cp = ch.codePointAt(0);
    if (cp >= 0xE500 && cp <= 0xE5FF) { w += GLYPH_W[cp - 0xE500] ?? 9; continue; }
    w += (cp > 127 ? 9 : (MC_NARROW[ch] ?? 6)) + (bold ? 1 : 0);
  }
  return w;
}

// ───── أنواع ─────
export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; } getComponent() { return undefined; } }
export class MolangVariableMap {
  constructor() { this.v = {}; }
  setFloat(k, x) { this.v[k] = x; }
  setColorRGB(k, c) { this.v[k + ".r"] = c.red; this.v[k + ".g"] = c.green; this.v[k + ".b"] = c.blue; }
  setColorRGBA(k, c) { this.v[k + ".r"] = c.red; this.v[k + ".g"] = c.green; this.v[k + ".b"] = c.blue; this.v[k + ".a"] = c.alpha; }
  setVector3(k, c) { this.v[k + ".x"] = c.x; this.v[k + ".y"] = c.y; this.v[k + ".z"] = c.z; }
  setSpeedAndDirection(k, sp, d) { this.v[k + ".speed"] = sp; this.v[k + ".direction.x"] = d.x; this.v[k + ".direction.y"] = d.y; this.v[k + ".direction.z"] = d.z; }
}
export const EntityDamageCause = new Proxy({}, { get: (t, k) => String(k) });
export const BlockPermutation = { resolve: (id, st) => ({ id, st, type: { id } }) };
export const StructureSaveMode = { Memory: "Memory", World: "World" };
export const StructureAnimationMode = { None: "None", Layers: "Layers", Blocks: "Blocks" };
// v1.42: بلوكات انحطت بالعالم (بنايات structureManager.place أو setBlockPermutation): getBlock يرجعها حتى الفحص يشتغل مثل اللعبة
const placed = new Map();
const bkey = (x, y, z) => ((Math.floor(x) + 50000) * 4096 + (Math.floor(y) + 2048)) * 100000 + (Math.floor(z) + 50000);
export class BlockVolume { constructor(a, b) { this.a = a; this.b = b; } }
export const GameMode = new Proxy({}, { get: (t, k) => String(k) });
export const HudElement = { PaperDoll: 0, Armor: 1, ToolTips: 2, TouchControls: 3, Crosshair: 4, Hotbar: 5, Health: 6, ProgressBar: 7, Hunger: 8, AirBubbles: 9, HorseHealth: 10, StatusEffects: 11, ItemText: 12 };
export const HudVisibility = { Hide: 0, Reset: 1 };
export const ItemLockMode = { inventory: "inventory", none: "none", slot: "slot" };
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
      if (n === "minecraft:onfire") return this._fire > tick ? { onFireTicksRemaining: this._fire - tick } : undefined;   // v1.39: مشتعل؟
      return undefined;
    },
    applyDamage(a) { this._hp -= a; stats.damage = (stats.damage || 0) + a; if (this._hp <= 0) { this._valid = false; } return true; },
    applyKnockback() { stats.knock = (stats.knock || 0) + 1; }, applyImpulse() {},
    addEffect(id, dur, o) { effectLog.push(id); (this._effs = this._effs || {})[id] = { dur, amp: o && o.amplifier }; stats.effects = stats.effects || {}; stats.effects[id] = (stats.effects[id] || 0) + 1; if (id === 'health_boost') stats.lastBoost = o && o.amplifier; }, removeEffect() {}, getEffect() { return undefined; },
    teleport(l, o) { this.location = { x: l.x, y: l.y, z: l.z }; if (o && o.facingLocation) { this._yaw = (Math.atan2(-(o.facingLocation.x - l.x), o.facingLocation.z - l.z) * 180) / Math.PI; } else if (o && o.rotation) this._yaw = o.rotation.y; }, remove() { this._valid = false; }, kill() { this._valid = false; },
    setProperty(k, v) { checkProp(typeId, k, v); if (process.env.SH_TRACE && k === "sh:state" && typeId === "sh:hollow_seer") console.log("   [trace] tick", tick, this.id, "state", v); props[k] = v; if (typeId === "sh:fx_shape" && k === "sh:v") { stats.shapeV = stats.shapeV || {}; stats.shapeV[v] = (stats.shapeV[v] || 0) + 1; } }, getProperty(k) { return props[k]; }, triggerEvent() {}, setOnFire(sec) { this._fire = tick + Math.round((sec || 0) * 20); stats.fires = (stats.fires || 0) + 1; },
    setRotation(r) { if (r) this._yaw = r.y; }, getRotation() { return { x: 0, y: this._yaw || 0 }; }, getVelocity() { return { x: 0, y: 0, z: 0 }; }, clearVelocity() {},
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
    spawnEntity(type, loc) { stats.spawned++; (stats.spawnedTypes = stats.spawnedTypes || {})[type] = (stats.spawnedTypes[type] || 0) + 1; const e = mkEntity(type, loc, d, 10); if (FX_TIMERS[type]) e._dieAt = tick + FX_TIMERS[type]; entities.push(e); return e; },
    spawnItem(it) { (stats.items = stats.items || []).push(it.typeId); },
    getBlock(l) { const pid = placed.get(bkey(l.x, l.y, l.z)); const solid = pid ? pid !== "minecraft:air" : Math.floor(l.y) <= 63; const b = { x: Math.floor(l.x), y: Math.floor(l.y), z: Math.floor(l.z), typeId: pid || (solid ? "minecraft:dirt" : "minecraft:air"), isAir: !solid, isLiquid: false, location: l, dimension: d, getComponent: (n) => n === 'minecraft:inventory' ? { container: { size: 27, setItem(i, it) { (stats.chestItems = stats.chestItems || []).push(it && it.typeId); }, getItem() {} } } : undefined, setType(t) { stats.blockSets = (stats.blockSets || 0) + 1; this.typeId = t; } }; return b; },
    isChunkLoaded() { return !globalThis.__unloaded; },
    getEntities(q = {}) {
      return entities.filter((e) => e._valid && (!e.dimension || e.dimension === d) && (!q.type || e.typeId === q.type) && (!q.tags || q.tags.every((t) => e._tags.has(t))) && (!q.families || q.families.every((f) => ({ sh_rank0: ['sh:ember_imp','sh:rust_guard','sh:shadow_hound','sh:sand_scorpion'], sh_rank1: ['sh:gloomhorn','sh:hollow_seer','sh:veilfox','sh:magmamoth'], sh_rank2: ['sh:magmamoth','sh:grey_bear'], sh_rank3: ['sh:prayer_mantis'], sh_rank4: ['sh:hollow_harvester'], sh_monster: ['sh:ember_imp','sh:rust_guard','sh:shadow_hound','sh:sand_scorpion','sh:gloomhorn','sh:hollow_seer','sh:veilfox','sh:magmamoth','sh:grey_bear','sh:bear_cub','sh:prayer_mantis','sh:hollow_harvester'] }[f] || [e.typeId]).includes(e.typeId))) && (!q.type || e.typeId === q.type) && !(q.excludeTypes || []).includes(e.typeId) && !((q.excludeFamilies || []).includes("inanimate") && e.typeId.startsWith("sh:fx_"))
        && (!q.location || !q.maxDistance || Math.hypot(e.location.x - q.location.x, e.location.z - q.location.z) <= q.maxDistance));
    },
    getPlayers(q) {      // بالتسجيل بس نحترم فلتر المسافة مثل اللعبة (باقي الاختبارات تبقى تضرب دائماً حتى تتأكد المهارة تطلع)
      if (rec.on && q && q.location && q.maxDistance !== undefined) { const dx = player.location.x - q.location.x, dy = (player.location.y + 1) - q.location.y, dz = player.location.z - q.location.z; return Math.hypot(dx, dy, dz) <= q.maxDistance ? [player] : []; }
      return [player];
    },
    getTopmostBlock(l) { const b = { x: Math.floor(l.x), y: 63, z: Math.floor(l.z), typeId: "minecraft:grass_block", location: { x: l.x, y: 63, z: l.z }, isAir: false, isLiquid: false, dimension: d, above: () => ({ isAir: true }), below: () => ({ isAir: false, isLiquid: false }), getComponent: () => undefined, setType(t) { stats.blockSets = (stats.blockSets || 0) + 1; this.typeId = t; } }; return b; },
    getBiome() { return { id: globalThis.__biome || "minecraft:plains" }; },
    fillBlocks(v, b, o) { stats.fills = (stats.fills || 0) + 1; const a = v.a, c = v.b; const n = (Math.abs(c.x - a.x) + 1) * (Math.abs(c.y - a.y) + 1) * (Math.abs(c.z - a.z) + 1); stats.fillMax = Math.max(stats.fillMax || 0, n); if (o && o.blockFilter) stats.filteredFills = (stats.filteredFills || 0) + 1; },
    setBlockType(l, t) { (stats.setTypes = stats.setTypes || []).push([Math.floor(l.x), Math.floor(l.y), Math.floor(l.z), t]); }, setBlockPermutation(l, pm) { stats.directWrites = (stats.directWrites || 0) + 1; if (Math.abs(l.x) > 1000 || Math.abs(l.z) > 1000) stats.farWrites = (stats.farWrites || 0) + 1; if (pm && pm.id) placed.set(bkey(l.x, l.y, l.z), pm.id); }, runCommand(c) { if (/^setblock .* air destroy$/.test(c)) stats.broken = (stats.broken || 0) + 1; return { successCount: 1 }; }, runCommandAsync: async () => ({}),
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
  getGameMode() { return "Survival"; },                                          // مثل الـAPI الحقيقي (GameMode)
  playAnimation(id, opts) { (stats.anims = stats.anims || []).push(id); if (opts && opts.controller === "sh_act") stats.animOpts = opts; else stats.moveOpts = opts; },   // v1.39: أنميشن اللاعب (V1: sh_move للوقوف/المشي/الركض)
  // الشاشة: فوق يسار = شريط الأكشن، فوق الهوت بار = العنوان. actionBars يسجل الشاشة كاملة (فوق + تحت) حتى الاختبارات القديمة تلقى كل الكتابات،
  // وstats.top / stats.bottom كل قسم لحاله حتى نتأكد وين انكتبت كل شغلة.
  onScreenDisplay: {
    setActionBar(t) { stats.top = String(t); stats.actionBars.push(stats.top + (stats.bottom ? "\n" + stats.bottom : "")); seenText(t); },
    // v1.43: كود شريط المهارات (رموز تنسيق تبدي بـ §k وتخلص بـ §r§f) ما ينرسم باللعبة: ينفصل هنا بـ stats.barCode والباقي هو الكتابة الظاهرة
    setTitle(t, o) {
      let s = String(t);
      stats.barCode = "";
      if (s.startsWith("§k")) { const k = s.indexOf("§r§f"); if (k >= 0) { stats.barCode = s.slice(0, k + 4); s = s.slice(k + 4); } }
      (stats.barCodes = stats.barCodes || []).push(stats.barCode);
      (stats.titles = stats.titles || []).push(s); stats.bottom = s; stats.titleOpts = o; stats.actionBars.push((stats.top || "") + "\n" + stats.bottom); seenText(s); if (o && o.subtitle) seenText(o.subtitle);
    },
    clearTitle() { stats.bottom = ""; stats.barCode = ""; },
    setHudVisibility(v, els) { stats.hudHidden = v === 0 ? els : []; },
  },
  sendMessage(m) { stats.messages.push(String(m)); seenText(m); }, playSound(s) { stats.sounds++; stats.soundIds.add(s); },
  // v1.43: قيمة خاصة باللاعب لخاصية كيان (مثل الـAPI: لازم الخاصية موجودة ونوعها ومداها صح)
  setPropertyOverrideForEntity(e, k, v) { checkProp(e.typeId, k, v); (stats.overrides = stats.overrides || []).push([e.typeId, k, v]); },
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
  sendMessage() {}, getDefaultSpawnLocation: () => ({ x: 0, y: 32767, z: 0 }),
  // v1.42: مدير البنايات (بالذاكرة) ومناطق التكتك، بنفس توقيعات الـAPI الرسمي
  structureManager: {
    _reg: new Map(),
    createEmpty(id, size) {
      if (this._reg.has(id)) throw new Error(`structure ${id} exists`);
      const blocks = new Map(), sx = size.x, sy = size.y;
      const st = { id, size, isValid: true, blocks, setBlockPermutation(l, pm) { if (l.x < 0 || l.y < 0 || l.z < 0 || l.x >= size.x || l.y >= size.y || l.z >= size.z) throw new Error("out of bounds"); blocks.set(l.x + sx * (l.y + sy * l.z), pm ? pm.id : undefined); } };
      this._reg.set(id, st); stats.structCreated = (stats.structCreated || 0) + 1; return st;
    },
    get(id) { return this._reg.get(id); },
    delete(s0) { const id = typeof s0 === "string" ? s0 : s0 && s0.id; const st = this._reg.get(id); if (st) st.isValid = false; return this._reg.delete(id); },
    place(s0, dim, loc, opts) {
      const st = typeof s0 === "string" ? this._reg.get(s0) : s0;
      if (!st || !st.isValid) throw new Error("invalid structure");
      const sx = st.size.x, sy = st.size.y;
      for (const [k, id] of st.blocks) { if (!id) continue; const x = k % sx, y = Math.floor(k / sx) % sy, z = Math.floor(k / (sx * sy)); placed.set(bkey(loc.x + x, loc.y + y, loc.z + z), id); }
      (stats.placements = stats.placements || []).push({ x: loc.x, y: loc.y, z: loc.z, n: st.blocks.size, opts });
    },
  },
  tickingAreaManager: {
    _areas: new Map(), maxChunkCount: 400,
    get chunkCount() { let n = 0; for (const o of this._areas.values()) n += (Math.floor(Math.abs(o.to.x - o.from.x) / 16) + 2) * (Math.floor(Math.abs(o.to.z - o.from.z) / 16) + 2); return n; },
    hasCapacity(o) { return !globalThis.__noCapacity && Math.abs(o.to.x - o.from.x) / 16 < 255; },
    hasTickingArea(id) { return this._areas.has(id); },
    // القطع البعيدة "تتحمل" بس من يبدي اختبار المدينة (globalThis.__cityGo)، حتى بناء المدينة ما يتداخل ويا اختبارات المهارات
    createTickingArea(id, o) {
      if (this._areas.has(id)) return Promise.reject(new Error("exists"));
      this._areas.set(id, o); stats.areasMade = (stats.areasMade || 0) + 1; stats.areaMax = Math.max(stats.areaMax || 0, this._areas.size);
      if (globalThis.__cityGo) return Promise.resolve();
      return new Promise((res) => (globalThis.__pendingAreas = globalThis.__pendingAreas || []).push(res));
    },
    removeTickingArea(id) { this._areas.delete(typeof id === "string" ? id : id && id.identifier); },
    getAllTickingAreas() { return [...this._areas.keys()].map((identifier) => ({ identifier })); },
  },
};

const fire = (name, payload) => { for (const fn of subs[name] || []) fn(payload); };
// V1: كل نص طلع للاعب (دردشة، واجهة، عناوين، قوائم) حتى نقيس تغطية الترجمة العربية بآخر المحاكي
globalThis.__allText = globalThis.__allText || new Set();
function seenText(t) { if (typeof t === "string" && globalThis.__allText.size < 60000) for (const ln of t.split("\n")) if (ln.trim()) globalThis.__allText.add(ln); }

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
    // V1: طور القصة يعطي خبرة لما تخلص خطواته؛ بباقي الاختبارات نخليه منتهي حتى ما يغيّر المستوى/الرتبة بنصها (اختباره لوحده تحت)
    const STORY_DONE = JSON.stringify({ i: 99, base: 0, hide: true, ann: 99 });
    player.setDynamicProperty("sh_story", STORY_DONE);
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
    // V1: سجن البلورات حبس حقيقي: المكان ينقفل (حتى لو انضرب أو اندفع) ومهارات الوحش الخاصة توقف لحد ما ينكسر
    {
      setState(baseState("crystal")); spawnZombies(1); system_cd_reset();
      const z = entities[0]; await useItem("sh:skill_prison"); advance(2);
      const at0 = { ...z.location };
      z.location = { x: at0.x + 3, y: at0.y, z: at0.z + 2 }; advance(4);
      const locked = Math.hypot(z.location.x - at0.x, z.location.z - at0.z) < 0.2;
      advance(120); z.location = { x: at0.x + 3, y: at0.y, z: at0.z + 2 }; advance(4);
      const freed = Math.hypot(z.location.x - at0.x, z.location.z - at0.z) > 1;
      // وحش Grim محبوس: ما يستعمل مهارات خلال الحبس، ويرجع يستعملها بعده
      entities.length = 0; system_cd_reset(); player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000;
      const g = mkEntity("sh:gloomhorn", { x: 0, y: 64, z: 5 }, dims.overworld, 90); entities.push(g);
      const gv = player.getEntitiesFromViewDirection; player.getEntitiesFromViewDirection = () => [{ entity: g, distance: 5 }];
      await useItem("sh:skill_prison"); player.getEntitiesFromViewDirection = gv;
      let skillIn = false, skillAfter = false, gd0 = stats.damage || 0;
      for (let t = 0; t < 96; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (g.getProperty("sh:state")) skillIn = true; }
      const dmgIn = Math.round((stats.damage || 0) - gd0);
      for (let t = 0; t < 1200 && !skillAfter; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (g.getProperty("sh:state")) skillAfter = true; }
      console.log(`\nسجن البلورات: المكان مقفول ${locked ? "✔" : "✖"} | ينفك بعده ${freed ? "✔" : "✖"} | وحش محبوس بدون مهارات ${!skillIn && dmgIn === 0 ? "✔" : "✖"} | يرجع بعد الحبس ${skillAfter ? "✔" : "✖"}`);
      if (!locked) failures.push("سجن البلورات: الوحش يطلع من مكانه");
      if (!freed) failures.push("سجن البلورات: الوحش بقى مقفول بعد ما انتهى");
      if (skillIn || dmgIn) failures.push("سجن البلورات: الوحش المحبوس استعمل مهارته");
      if (!skillAfter) failures.push("سجن البلورات: الوحش ما رجع يستعمل مهاراته بعد الحبس");
      entities.length = 0; player._hp = 20; player._max = 20; system_cd_reset();
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
      console.log(`\nتلفيل الأسلحة: مهارة 2 بـLv1 = ${locked > 0 ? "مفتوحة ✖" : "مقفولة ✔"} | بعد 40 ضربة: Lv${lvHit && lvHit.lv} (${lvHit && lvHit.xp} XP) | بعد قتلة: Lv${lvKill && lvKill.lv} | ضرر الضربة Lv1=${dm1} Lv4=${dm5} | هالة Lv4 جزيئات=${aura}`);
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
        // v1.37: ولا سلاح يكسر أو يغير بلوكات (المطرقة خصوصاً، طلب اللاعب)
        const setT = (stats.setTypes || []).length;
        if ((stats.broken || 0) - b0 > 0) failures.push(`${wid} مهارة ${sneak ? 2 : 1}: كسرت بلوكات (لازم ما تكسر)`);
        if (wid === "sh:stone_maul" && (stats.setTypes || []).length !== setT) failures.push("المطرقة غيرت بلوكات");
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
      // v1.43: ليفل القدرة يصعد ليفل واحد بكل مرة خبرة (حتى لو كان متأخر عن ليفل اللاعب) فالمهارات تنفتح وحدة وحدة
      setState({ ...baseState("crystal"), level: 44, rank: 2, plevel: 2, pxp: 105 });
      const steps = [];
      for (let i = 0; i < 4; i++) { fire("scriptEventReceive", { id: "sh:xp", message: "5", sourceEntity: player }); steps.push(JSON.parse(player.getDynamicProperty("sh")).plevel); }
      let st = JSON.parse(player.getDynamicProperty("sh"));
      console.log("\nتطور القدرة: لاعب ليفل 44 كان عالق Lv2 → بكل خبرة:", steps.join(" → "));
      if (st.plevel < 6) failures.push("ليفل القدرة ما لحق بليفل اللاعب");
      if (steps.some((v, i) => v - (i ? steps[i - 1] : 2) > 1)) failures.push("ليفل القدرة قفز أكثر من ليفل بمرة وحدة");
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
      // v1.43: شريط المهارات صار تحت يمين (كود بأول العنوان)، فاللوحة فوق يسار ما بيها أيقونات المهارات بعد
      setState({ ...baseState("star"), sel: "meteor" }); hold("sh:power_sigil"); stats.actionBars.length = 0; advance(20);
      const top = stats.top || "", low = stats.bottom || "";
      const ok = !/[\uE530\uE531\uE532\uE533]/.test(top) && !/Level \d/.test(top) && /Meteor/.test(low) && /Level \d/.test(low) && /^§k§l§8/.test(stats.barCode || "")
        && stats.titleOpts && stats.titleOpts.fadeInDuration === 0;
      console.log(`  المكان: الأشرطة فوق يسار + المهارة المختارة فوق الهوت بار + الشريط تحت يمين ${ok ? "✔" : "✖"} | فوق الهوت بار: ${low.replace(/§./g, "").replace(/\n/g, " ⏎ ")}`);
      if (!ok) failures.push("معلومات الأيتم مو فوق الهوت بار (أو اللوحة فوق يسار بيها كتابات)");
      hold(""); advance(30);
      const cleared = !(stats.bottom || "").includes("Level");
      // v1.36: اللوحة فوق يسار ضيقة حتى ما توصل لأزرار الإيقاف/الشات/الإيموت بأعلى الشاشة باللمس: أسوأ حالة
      // (رتبة Commander، ليفل 120، صحة 120، كل المهارات بكولداون، 4 تقويات، مانا 3 أرقام) وأعرض سطر ≤ 120 بكسل، و8 قلوب
      {
        const s0 = baseState("star"); s0.rank = 4; s0.level = 120; s0.xp = 0; s0.plevel = 10; setState(s0);
        player._hp = 120; player._max = 120; system_cd_reset();
        for (const sk of skills.filter((x) => x.power === "star")) { await useItem(sk.item); advance(1); }
        for (const pid of ["sh:potion_might", "sh:potion_bulwark", "sh:potion_focus", "sh:potion_swift"]) fire("itemCompleteUse", { source: player, itemStack: new ItemStack(pid) });
        hold(""); advance(10);
        const widths = {};
        for (const pl of [false, true]) {
          if (pl) player._tags.add("sh_hud_plain"); else player._tags.delete("sh_hud_plain");
          advance(10);
          widths[pl ? "plain" : "art"] = (stats.top || "").split("\n").map((l) => [mcWidth(l), l.replace(/§./g, "").replace(/[\uE500-\uE5FF]/g, "◆")]);
        }
        player._tags.delete("sh_hud_plain");
        const maxArt = Math.max(...widths.art.map((x) => x[0])), maxPlain = Math.max(...widths.plain.map((x) => x[0]));
        const hearts = widths.art.find((x) => x[1].includes("120/120")), nHearts = hearts ? (hearts[1].match(/◆/g) || []).length : 0;
        const okW = maxArt <= 120 && maxPlain <= 120 && nHearts === 8 && widths.art.length >= 6;
        console.log(`  عرض اللوحة فوق يسار (أسوأ حالة): أعرض سطر ${maxArt} بكسل (البسيطة ${maxPlain})، أسطر ${widths.art.length}، قلوب ${nHearts} ${okW ? "✔" : "✖"}`);
        for (const [w, l] of widths.art) console.log(`    ${String(w).padStart(5)} │ ${l}`);
        if (!okW) failures.push("اللوحة فوق يسار عريضة (توصل لأزرار الإيقاف/الشات باللمس) أو القلوب مو 8");
        player._hp = 20; player._max = 20; system_cd_reset(); fire("scriptEventReceive", { id: "sh:clearbuffs", message: "", sourceEntity: player });
      }
      if (!cleared) failures.push("الكتابة فوق الهوت بار ما تنمسح لما تنزل الأيتم");
    }
    // v1.43: صولجان القدرة + شريط المهارات تحت يمين + المهارات تنفتح وحدة وحدة
    {
      console.log("\nصولجان القدرة وشريط المهارات (v1.43):");
      const SIG = "sh:power_sigil";
      const CODE_RE = /^(§k(§l§[0-8]|§o§[0-6]|§[0-6]§[a-d]|§m§[0-6]§[1-9]|§n§[0-6]§[0-9]|§p§[0-6]§[1-8]|§q§1))+§r§f$/;
      // نفك الكود بنفس قواعد tools/gen_skillbar_ui.py: لكل خانة الحالة والرقم، والمختارة، والقدرة
      const decode = (c) => {
        const out = { power: -1, sel: -1, slots: {} };
        for (const m of c.matchAll(/§k(§l§([0-8])|§o§([0-6])|§([0-6])§([a-d])|§m§([0-6])§([1-9])|§n§([0-6])§([0-9]))/g)) {
          if (m[2] !== undefined) out.power = +m[2];
          else if (m[3] !== undefined) out.sel = +m[3];
          else if (m[4] !== undefined) (out.slots[m[4]] = out.slots[m[4]] || { n: 0 }).x = m[5];
          else if (m[6] !== undefined) (out.slots[m[6]] = out.slots[m[6]] || { n: 0 }).n += 10 * +m[7];
          else if (m[8] !== undefined) (out.slots[m[8]] = out.slots[m[8]] || { n: 0 }).n += +m[9];
        }
        return out;
      };
      const stNow = () => JSON.parse(player.getDynamicProperty("sh"));
      const invIds = () => inventory.filter(Boolean).map((x) => x.typeId);
      // 1) لاعب قديم عنده أيتمات مهارات: بأول دخول تنشال ويجيه الصولجان (مرة وحدة)
      for (let i = 0; i < 36; i++) inventory[i] = undefined;
      inventory[3] = new ItemStack("sh:skill_meteor"); inventory[4] = new ItemStack("sh:skill_orbit");
      setState({ ...baseState("star"), plevel: 3, pxp: 0 });
      stats.messages.length = 0; fire("playerSpawn", { player, initialSpawn: true }); advance(60);
      const migr = invIds().includes(SIG) && !invIds().some((t) => t.startsWith("sh:skill_")) && stNow().sigilV === 1 && stNow().sel === "meteor";
      const sigStack = inventory.find((x) => x && x.typeId === SIG);
      const kept = !!(sigStack && sigStack.keepOnDeath === true && sigStack.lockMode === "inventory");
      console.log(`  ترحيل اللاعب القديم: أيتمات المهارات انشالت والصولجان وصل ${migr ? "✔" : "✖"} | يبقى بعد الموت وما ينرمي ${kept ? "✔" : "✖"}`);
      if (!migr) failures.push("الترحيل: أيتمات المهارات ما انشالت أو الصولجان ما وصل");
      if (!kept) failures.push("الصولجان مو keepOnDeath/lockMode inventory");
      // بعد الموت (respawn): إذا ضاع يرجع
      for (let i = 0; i < 36; i++) inventory[i] = undefined;
      fire("playerSpawn", { player, initialSpawn: false }); advance(20);
      const back = invIds().includes(SIG);
      console.log(`  بعد الموت إذا ضاع الصولجان يرجع ${back ? "✔" : "✖"}`);
      if (!back) failures.push("الصولجان ما رجع بعد الموت");
      // 2) قدرة جديدة: ليفل 1، المختارة أول مهارة، والصولجان
      for (let i = 0; i < 36; i++) inventory[i] = undefined;
      setState({ ...baseState(null), power: null, plevel: 7, pxp: 0 });
      fire("scriptEventReceive", { id: "sh:power", message: "star", sourceEntity: player }); advance(5);
      let st = stNow();
      const fresh = st.power === "star" && st.plevel === 1 && st.sel === "meteor" && invIds().includes(SIG);
      console.log(`  قدرة جديدة تبدي ليفل 1 والمختارة أول مهارة ويجي الصولجان ${fresh ? "✔" : "✖"} (ليفل ${st.plevel})`);
      if (!fresh) failures.push("القدرة الجديدة ما تبدي من ليفل 1 / ما يجي الصولجان");
      // 3) الكود: كله رموز تنسيق، ونفس القواعد، والمقفولة بيها ليفل فتحها، والمختارة صح
      hold(SIG); system_cd_reset(); fire("scriptEventReceive", { id: "sh:clearbuffs", message: "", sourceEntity: player }); advance(10);
      let code = stats.barCode || "", d = decode(code);
      const starN = skills.filter((x) => x.power === "star").length;
      const locks = Object.entries(d.slots).filter(([, v]) => v.x === "c").map(([k, v]) => `${k}:${v.n}`);
      const okCode = CODE_RE.test(code) && d.power === 8 && d.sel === starN - 1 && Object.keys(d.slots).length === starN && locks.length === starN - 1
        && Object.values(d.slots).filter((v) => v.x === "c").every((v) => v.n >= 2);
      console.log(`  الكود: ${okCode ? "✔" : "✖"} قدرة ${d.power}، المختارة خانة ${d.sel}، مقفولة (خانة:ليفل) ${locks.join(" ")} | طول ${code.length}`);
      if (!okCode) failures.push("كود شريط المهارات غلط: " + code.replace(/§/g, "&"));
      const allTitles = (stats.titles || []).concat(stats.bottom || "");
      if (allTitles.some((t) => t.includes("§k"))) failures.push("كتابة فوق الهوت بار بيها §k (تخرب بحث الواجهة)");
      if ((stats.barCodes || []).some((c) => c && !CODE_RE.test(c))) failures.push("كود شريط بصيغة غلط انرسل");
      // 4) الفتح وحدة وحدة: خبرة كبيرة كلش (500) كل مرة = ليفل واحد ومهارة وحدة بالأكثر
      const opened = [];
      for (let i = 0; i < 12; i++) {
        fire("scriptEventReceive", { id: "sh:xp", message: "500", sourceEntity: player }); advance(6);
        d = decode(stats.barCode || "");
        opened.push(Object.values(d.slots).filter((v) => v.x !== "c").length);
      }
      st = stNow();
      const oneByOne = opened.every((v, i) => v - (i ? opened[i - 1] : 1) <= 1) && opened[opened.length - 1] === starN && st.plevel === 10;
      console.log(`  الفتح وحدة وحدة (خبرة 500 كل مرة) — المفتوحة: 1 → ${opened.join(" → ")} ${oneByOne ? "✔" : "✖"}`);
      if (!oneByOne) failures.push("المهارات تنفتح أكثر من وحدة بمرة وحدة");
      // 5) الصولجان يرمي المختارة، وضغطة سنيك قصيرة (وهو بإيدك) = المهارة الجاية
      system_cd_reset(); fire("scriptEventReceive", { id: "sh:clearbuffs", message: "", sourceEntity: player });
      setState({ ...stNow(), sel: "meteor" }); spawnZombies(); hold(SIG);
      await useItem(SIG); advance(6);
      d = decode(stats.barCode || "");
      const castOk = d.slots[String(starN - 1)] && d.slots[String(starN - 1)].x === "b" && d.slots[String(starN - 1)].n > 0;
      const tap = (dt = 2) => { fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Pressed" }); advance(dt); fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Released" }); advance(6); };
      d = decode(stats.barCode || "");
      const cdStep = (stats.barCode || "").match(new RegExp(`§k§p§${starN - 1}§([1-8])`));
      if (!cdStep || +cdStep[1] < 7) failures.push("ظل الكولداون بالشريط (§k§p) ما يبين أو مو بأوله: " + (cdStep ? cdStep[1] : "ماكو"));
      tap(); const s1 = stNow().sel; tap(); const s2 = stNow().sel;
      d = decode(stats.barCode || "");
      const cycOk = s1 === "gravwell" && s2 === "orbit" && d.sel === starN - 3;
      tap(20); const longHold = stNow().sel === "orbit";                          // سنيك طويل (تمشي متخفي) ما يبدل
      fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Pressed" }); await useItem(SIG); advance(1);
      fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Released" }); advance(6);
      const sneakUse = stNow().sel === "orbit";                                   // سنيك + استعمال ما يبدل
      hold("sh:dark_katana"); tap(); const otherItem = stNow().sel === "orbit"; hold(SIG);   // بدون الصولجان ما يبدل
      for (let i = 0; i < 5; i++) tap();
      const wrap = stNow().sel === "meteor";                                      // يلف من الأخيرة للأولى
      console.log(`  الصولجان يرمي المختارة (كولداون بالشريط) ${castOk ? "✔" : "✖"} | سنيك قصير يبدل ${cycOk ? "✔" : "✖"} (${s1}, ${s2}) | سنيك طويل ما يبدل ${longHold ? "✔" : "✖"} | سنيك+استعمال ما يبدل ${sneakUse ? "✔" : "✖"} | بدون الصولجان ما يبدل ${otherItem ? "✔" : "✖"} | يلف ${wrap ? "✔" : "✖"}`);
      if (!castOk) failures.push("الصولجان ما رمى المهارة المختارة");
      if (!cycOk || !longHold || !sneakUse || !otherItem || !wrap) failures.push("تبديل المهارات بالسنيك ما يشتغل صح");
      // 5ب) v1.44: سنيك + استعمال الصولجان = شاشة المهارات (مثل الحقيبة): 8 بطاقات بأيقونات، تكبس على مهارة = تنختار، وما ترمي شي
      {
        const ui2 = (await import("@minecraft/server-ui")).sim;
        system_cd_reset(); fire("scriptEventReceive", { id: "sh:clearbuffs", message: "", sourceEntity: player });
        setState({ ...stNow(), plevel: 10, sel: "meteor" }); hold(SIG);
        ui2.formsShown.length = 0; ui2.queue.length = 0; ui2.nextSelection = 3;
        player.isSneaking = true; fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Pressed" });
        await useItem(SIG); advance(2); await new Promise((r) => setTimeout(r, 10));
        fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Released" }); player.isSneaking = false; advance(8);
        const fm = ui2.formsShown.find((f) => typeof f.title === "string" && f.title.startsWith("§t§s§q§r"));
        const starIds = skills.filter((x) => x.power === "star").map((x) => x.id);
        const okForm = !!fm && fm.buttons.length === 8 && fm.icons.slice(0, starN).every((ic, i) => ic === `textures/items/sh_${starIds[i]}`)
          && fm.buttons[starN] === "§k§e§r" && /^§k§s§r/.test(fm.buttons[0]) && fm.buttons.every((b) => /^(§k§[scbde])*§r/.test(b));
        const picked = stNow().sel === starIds[3];
        d = decode(stats.barCode || "");
        const noCast = !Object.values(d.slots).some((v) => v.x === "b");
        // مقفولة من الشاشة ما تنختار
        setState({ ...stNow(), plevel: 1, sel: "meteor" }); stats.messages.length = 0;
        ui2.nextSelection = 5; player.isSneaking = true; fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Pressed" });
        await useItem(SIG); advance(2); await new Promise((r) => setTimeout(r, 10));
        fire("playerButtonInput", { player, button: "Sneak", newButtonState: "Released" }); player.isSneaking = false; advance(8);
        const fm2 = ui2.formsShown[ui2.formsShown.length - 1];
        const lockedOk = stNow().sel === "meteor" && fm2 && /^§k§c§r/.test(fm2.buttons[5]) && /\uE532 Lv \d+/.test(fm2.buttons[5]);
        console.log(`  شاشة المهارات (سنيك + استعمال): تنفتح بـ8 بطاقات وأيقونات ${okForm ? "✔" : "✖"} | تكبس = تنختار (${stNow().sel === "meteor" ? "meteor" : stNow().sel}) ${picked ? "✔" : "✖"} | ما رمت مهارة ${noCast ? "✔" : "✖"} | المقفولة ما تنختار ${lockedOk ? "✔" : "✖"}`);
        if (!okForm) failures.push("شاشة المهارات: البطاقات أو الأيقونات أو الرموز غلط: " + JSON.stringify(fm && fm.buttons).replace(/§/g, "&").slice(0, 400));
        if (!picked) failures.push("شاشة المهارات: الاختيار ما غيّر المهارة المختارة");
        if (!noCast) failures.push("شاشة المهارات: سنيك + استعمال رمى مهارة");
        if (!lockedOk) failures.push("شاشة المهارات: المقفولة انختارت أو ما عليها القفل");
        ui2.nextSelection = 0; ui2.formsShown.length = 0;                          // نرجع الاختيار الافتراضي للاختبارات اللي بعدها
      }
      // 6) المقفولة ما تنختار بالسنيك (قدرة ليفل 1 = مهارة وحدة)
      setState({ ...stNow(), plevel: 1, sel: "meteor" }); stats.messages.length = 0; tap();
      const onlyOne = stNow().sel === "meteor";
      if (!onlyOne) failures.push("السنيك اختار مهارة مقفولة");
      // 7) سحب القدرة من جديد (sh:redraw) يشيل الصولجان
      fire("scriptEventReceive", { id: "sh:redraw", message: "", sourceEntity: player }); advance(5);
      const gone = !invIds().includes(SIG) && !stNow().power;
      d = decode(stats.barCode || "");
      console.log(`  مقفولة ما تنختار ${onlyOne ? "✔" : "✖"} | سحب القدرة يشيل الصولجان ${gone ? "✔" : "✖"} | الشريط ينطفي بدون قدرة ${!stats.barCode ? "✔" : "✖"}`);
      if (!gone) failures.push("سحب القدرة ما شال الصولجان");
      if (stats.barCode) failures.push("شريط المهارات باقي بدون قدرة");
      setState(baseState("star")); system_cd_reset(); hold("");
    }
    // كتاب + نافذة الحالة
    const ui = (await import("@minecraft/server-ui")).sim;
    ui.nextSelection = 99; ui.formsShown.length = 0; await useItem("sh:evolution_book"); advance(3);
    ui.nextSelection = 99; await Promise.resolve();
    const book = ui.formsShown[0];
    console.log("\nكتاب التطور: أزرار", book ? book.buttons.length : 0);
    const btn = (txt) => (book ? book.buttons.findIndex((b) => b.includes(txt)) : -1);           // الأزرار بأسمائها (الأخير صار [Achievements])
    ui.nextSelection = btn("[Status window"); ui.formsShown.length = 0; await useItem("sh:evolution_book"); advance(5); await new Promise((r) => setTimeout(r, 20));
    const status = ui.formsShown.find((f) => f.title === "Status Window");
    console.log(status ? "نافذة الحالة تفتح ✔" : "نافذة الحالة ما فتحت");
    if (!status) failures.push("نافذة الحالة ما فتحت");
    else console.log(status.body.replace(/§./g, "").split("\n").slice(0, 14).join("\n"));
    // حكاية العالم
    {
      ui.nextSelection = btn("[World Story]"); ui.formsShown.length = 0; ui.cancelWhenEmpty = false; await useItem("sh:evolution_book"); advance(5); await new Promise((r) => setTimeout(r, 30));
      const lore = ui.formsShown.find((f) => f.title === "The Chronicle of Etheria");
      console.log(lore ? "سجلّ إثيريا يفتح ✔ (" + lore.buttons.length + " فصول)" : "سجلّ إثيريا ما فتح");
      if (!lore) failures.push("حكاية العالم ما فتحت");
      else if (lore.buttons.length !== 8) failures.push("سجلّ إثيريا لازم 8 (مقدمة + 7 فصول)");
      ui.nextSelection = 0;
      // اختيار "آخر زر" بالكتاب يوصل للإعدادات ويبدل لوحة الواجهة مرات كثيرة (لحد حد السلسلة): نرجعها شغالة حتى الاختبارات اللي بعدها ما تتأثر
      try { player.removeTag("sh_hud_off"); } catch (e) { /* */ }
    }
    // V1: طور القصة: المتتبع فوق يمين (العنوان الفرعي)، «اكتملت المهمة» ثم يختفي ثم الجاية، والمكافأة؛ ولاعب قديم ينحسبله اللي خلصه بدون مكافأة
    {
      const subOf = () => (stats.titleOpts && stats.titleOpts.subtitle) || "";
      player.setDynamicProperty("sh_story", undefined); player.setDynamicProperty("sh_lang", undefined);
      setState({ ...baseState(null), power: null, training: {} }); advance(30);
      const sub0 = subOf().replace(/§./g, "");
      const xp0 = JSON.parse(player.getDynamicProperty("sh")).xp || 0;
      setState({ ...JSON.parse(player.getDynamicProperty("sh")), power: "iron" });
      let flash = "", gap = false, next = "";
      for (let t = 0; t < 200 && !next; t += 5) { advance(5); const sb = subOf().replace(/§./g, ""); if (/Mission complete/.test(sb)) flash = sb; else if (flash && sb.trim() === "") gap = true; else if (flash && gap && /Trainer/.test(sb)) next = sb; }
      const xp1 = JSON.parse(player.getDynamicProperty("sh")).xp || 0, stS = JSON.parse(player.getDynamicProperty("sh_story"));
      // لاعب قديم: عنده قدرة وخلص التدريب ورتبته محارب: الخطوات اللي مو «من لحظة الفتح» تنحسب بهدوء
      player.setDynamicProperty("sh_story", undefined);
      setState({ ...baseState("iron"), rank: 2, level: 30 }); const xpOld0 = JSON.parse(player.getDynamicProperty("sh")).xp || 0;
      advance(30);
      const stOld = JSON.parse(player.getDynamicProperty("sh_story")), xpOld1 = JSON.parse(player.getDynamicProperty("sh")).xp || 0;
      console.log(`\nطور القصة: المتتبع "${sub0.replace(/\n/g, " / ")}" ${/Awaken your power/.test(sub0) ? "✔" : "✖"} | اكتملت ${flash ? "✔" : "✖"} ثم اختفت ${gap ? "✔" : "✖"} ثم الجاية ${next ? "✔" : "✖"} | مكافأة +${xp1 - xp0} ${xp1 > xp0 ? "✔" : "✖"} | خطوة ${stS.i}`);
      console.log(`  لاعب قديم: وقف عند الخطوة ${stOld.i} (${stOld.i === 2 ? "✔ اصطاد الوحوش" : "✖"}) بدون مكافأة ${xpOld1 === xpOld0 ? "✔" : "✖"}`);
      if (!/Awaken your power/.test(sub0)) failures.push("طور القصة: المتتبع ما يعرض أول مهمة");
      if (!flash || !gap || !next) failures.push("طور القصة: اكتملت المهمة/الاختفاء/المهمة الجاية ما اشتغلت");
      if (!(xp1 > xp0) || stS.i !== 1) failures.push("طور القصة: الخطوة ما انحسبت أو بدون مكافأة");
      if (stOld.i !== 2 || xpOld1 !== xpOld0) failures.push("طور القصة: اللاعب القديم ما انحسب صح");
      player.setDynamicProperty("sh_story", STORY_DONE); setState(baseState("iron"));
    }
    // V1: اللغة العربية من الإعدادات (نفس طريق اللاعب: الكتاب ← الإعدادات ← اللغة): تتشكل (أشكال العرض FE70-FEFF، بدون حروف منفصلة)
    // بالقوائم والدردشة والمتتبع، وترجع إنكليزي
    {
      const isShaped = (t) => /[\uFE70-\uFEFF]/.test(t) && !/[\u0621-\u064A]/.test(t.replace(/§./g, ""));
      player.setDynamicProperty("sh_story", undefined);
      const openBook = async (queue) => { ui.formsShown.length = 0; ui.queue = [...queue]; ui.cancelWhenEmpty = true; await useItem("sh:evolution_book"); advance(5); await new Promise((r) => setTimeout(r, 40)); return ui.formsShown; };
      const en = (await openBook([]))[0] || { buttons: [] };
      const sIdx = en.buttons.findIndex((b) => /Settings/.test(b));
      await openBook([sIdx, 0]);
      const langNow = player.getDynamicProperty("sh_lang");
      const bk = (await openBook([]))[0] || { body: "", buttons: [] };
      stats.messages.length = 0; advance(40);
      const chat = stats.messages.join("\n"), trk = (stats.titleOpts && stats.titleOpts.subtitle) || "";
      await openBook([sIdx, 0]);
      const back = player.getDynamicProperty("sh_lang");
      const okForm = bk.body.startsWith("§r§r§r") && bk.buttons.some(isShaped);
      console.log(`العربي: الإعدادات تحوّل للعربي ${langNow === "ar" ? "✔" : "✖"} | الكتاب بخط أكبر ومتشكل ${okForm ? "✔" : "✖"} | زر الإعدادات ${sIdx >= 0 ? "✔" : "✖"} | الدردشة متشكلة ${isShaped(chat) ? "✔" : "✖"} | المتتبع ${trk.startsWith("§r§r§r") && isShaped(trk) ? "✔" : "✖"} | يرجع إنكليزي ${back === "en" ? "✔" : "✖"}`);
      if (langNow !== "ar") failures.push("العربي: زر اللغة بالإعدادات ما حوّل للعربي");
      if (!okForm) failures.push("العربي: الكتاب ما تشكّل أو بدون علامة الخط الأكبر");
      if (sIdx < 0) failures.push("العربي: زر الإعدادات ما موجود");
      if (!isShaped(chat)) failures.push("العربي: رسائل الدردشة ما تشكّلت");
      if (!(trk.startsWith("§r§r§r") && isShaped(trk))) failures.push("العربي: متتبع القصة ما تشكّل");
      if (back !== "en") failures.push("العربي: الإعدادات ما ترجّع الإنكليزي");
      player.setDynamicProperty("sh_story", STORY_DONE); ui.queue = []; ui.nextSelection = 0; ui.cancelWhenEmpty = false;
      try { player.removeTag("sh_hud_off"); } catch (e) { /* */ }
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
        // V1: معبد الاستيقاظ مرة وحدة: أمر التجربة ما يبني ثاني، ولو ضاع من السجل يرجع من sh_temple_at بدل ما ينبني جديد
        const temples = () => { const raw = (world._dyn.sh_structs || "[]") + Array.from({ length: world._dyn.sh_structs_n || 0 }, (_, i) => world._dyn[`sh_structs_${i + 1}`] || "").join(""); return JSON.parse(raw).filter((r) => r.type === "temple"); };
        const builtOk = temples()[0] && temples()[0].ok === 1 && temples()[0].pi === undefined;
        fire("scriptEventReceive", { id: "sh:temple", message: "here", sourceEntity: player }); advance(40);
        const afterCmd = temples().length;
        const st2 = JSON.parse(player.getDynamicProperty("sh")); const pw = st2.power; st2.power = null; st2.powerless = false; player.setDynamicProperty("sh", JSON.stringify(st2));
        world.setDynamicProperty("sh_structs", JSON.stringify(JSON.parse(world._dyn.sh_structs).filter((r) => r.type !== "temple")));
        fire("playerSpawn", { player, initialSpawn: false }); advance(400);
        const healed = temples();
        st2.power = pw; player.setDynamicProperty("sh", JSON.stringify(st2));
        console.log(`  معبد الاستيقاظ: كامل ok ${builtOk ? "✔" : "✖"} | بعد أمر التجربة عدد المعابد ${afterCmd} ${afterCmd === 1 ? "✔" : "✖"} | ضاع من السجل ورجع بنفس المكان ${healed.length === 1 && healed[0].x === temple.x && healed[0].z === temple.z ? "✔" : "✖"}`);
        if (!builtOk) failures.push("معبد الاستيقاظ ما انعلم كامل (ok) بعد البناء");
        if (afterCmd !== 1) failures.push("أمر التجربة بنى معبد استيقاظ ثاني");
        if (!(healed.length === 1 && healed[0].x === temple.x && healed[0].z === temple.z)) failures.push("معبد الاستيقاظ انبنى مرة ثانية بعد ما ضاع من السجل");
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
      // مكان الصدع عشوائي: إذا طلع قريب من اللاعب تبدي الموجة فوراً، فنبعد اللاعب شوية (برا مسافة البدء) حتى نفحص شريط "قبل المعركة"
      if (rs && Math.hypot(rs.x - player.location.x, rs.z - player.location.z) < 30) {
        const d = Math.hypot(rs.x, rs.z) || 1;
        player.location = { x: rs.x - (rs.x / d) * 40, y: 64, z: rs.z - (rs.z / d) * 40 };
      }
      if (!rs) failures.push("الصدع ما انفتح");
      else {
        const b0 = stats.blockSets || 0;
        advance(40); stats.actionBars.length = 0; advance(10);
        const hud = stats.actionBars[stats.actionBars.length - 1] || "";
        // v1.36: الصدع بشريط أعلى الشاشة (مثل الغارة): "Violet Rift (Vile) · spreading"، وما ينكتب بالواجهة
        const bb0 = bossBar();
        if (!bb0 || !/^Violet Rift · Grade 2 \(Medium\)$/.test(bb0.name) || hud.includes("Violet Rift")) failures.push("شريط الصدع بأعلى الشاشة ما طلع (أو الصدع بعده مكتوب بالواجهة)");
        // v1.35.1: سطر الصدع والإعلانات فوق الهوت بار (العنوان)، مو باللوحة فوق يسار (شريط الأكشن)
        const openBanner = (stats.titles || []).some((t) => t.includes("GRADE 2 RIFT"));
        console.log(`  شريط أعلى الشاشة قبل المعركة: "${bb0 ? bb0.name : "-"}" (${bb0 ? Math.round(bb0.fill * 100) : 0}%) | إعلان فتح الصدع فوق الهوت بار ${openBanner ? "✔" : "✖"}`);
        if (!openBanner) failures.push("إعلان فتح الصدع ما طلع فوق الهوت بار");
        stats.titles = [];
        console.log("  فساد الأرض: بلوكات =", (stats.blockSets || 0) - b0, "| HUD:", (hud.split("\n").find((l) => l.includes("Rift")) || "").replace(/§./g, "").replace(/[\uE500-\uE5FF]/g, "◆"));
        if ((stats.blockSets || 0) - b0 < 10) failures.push("الصدع ما فسد الأرض");
        // شكل الصدع 3D ودائرته لازم يبقون ظاهرين طول الوقت (مع مؤقتات BP: الشكل 60 ثانية، الدائرة 30) وبدون تكرار
        {
          const SHR = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/shapes.js"), "utf8");
          // v1.37.1: الصدع يختار واحد من 4 أشكال عشوائياً، والشكل يبقى نفسه بكل تجديد لحد ما يخلص الصدع
          const vRifts = new Set([...SHR.matchAll(/"rift_violet(?:_[bcd])?": (\d+)/g)].map((m) => Number(m[1])));
          const seenForms = new Set();
          let minS = 99, maxS = 0, minC = 99, maxC = 0, rOk = true;
          for (let k = 0; k < 75; k++) {
            advance(20);
            const sh = entities.filter((e) => e._valid && e.typeId === "sh:fx_shape" && vRifts.has(e.getProperty("sh:v")));
            for (const e of sh) seenForms.add(e.getProperty("sh:v"));
            const ci = entities.filter((e) => e._valid && e.typeId === "sh:fx_circle" && e._tags.has("sh_rift_fx"));
            minS = Math.min(minS, sh.length); maxS = Math.max(maxS, sh.length); minC = Math.min(minC, ci.length); maxC = Math.max(maxC, ci.length);
            if (sh.some((e) => !(e.getProperty("sh:r") > 1))) rOk = false;
          }
          const ok = minS === 1 && maxS === 1 && minC === 1 && maxC === 1 && rOk && vRifts.size === 4 && seenForms.size === 1;
          console.log(`  شكل الصدع 3D خلال 75 ثانية: أقل ${minS} / أكثر ${maxS} | الدائرة الرونية: أقل ${minC} / أكثر ${maxC} | الحجم ${rOk ? "✔" : "✖"} | أشكال ${vRifts.size}، نفس الرسمة طول عمره ${seenForms.size === 1 ? "✔" : "✖"} ${ok ? "✔" : "✖"}`);
          if (!ok) failures.push("شكل الصدع أو دائرته يختفي أو يتكرر");
        }
        player.location = { x: rs.x + 4, y: 64, z: rs.z };
        const waves = [], waveLines = [];
        const lowWave = () => { const b = bossBar(); return b ? `${b.name} [${Math.round(b.fill * 100)}%]` : ""; };
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
          if (w === 3 && boss && !["sh:magmamoth", "sh:grey_bear"].includes(boss.typeId)) failures.push(`حارس صدع الدرجة 2 لازم يكون وحش Vile (طلع ${boss.typeId})`);
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
          advance(5); waveLines.push(lowWave());
          if (w < 3) {
            mobs.forEach((e) => { fire("entityDie", { deadEntity: e, damageSource: { damagingEntity: player } }); e._valid = false; });
            advance(25); waveLines.push(lowWave());
          }
          else if (boss) { advance(200); fire("entityDie", { deadEntity: boss, damageSource: { damagingEntity: player } }); boss._valid = false; }
        }
        console.log("  " + waves.join("\n  "));
        // سطر Wave فوق الهوت بار: كلمة Wave + رقم الموجة + شكد خلصت (قتلت/الكل)، ويكمل لما تقتلهم
        // شريط الموجة بأعلى الشاشة: "Wave 1/3 · 5 left" ممتلي، بعد القتل "Cleared ✔" فارغ، ثم الموجة 2 و3 (وحوشها + الزعيم)
        const [s1, e1, s2, e2, s3] = waveLines;
        const waveOk = /^Wave 1\/3 · \d+ left \[100%\]$/.test(s1 || "") && /^Wave 1\/3 · Cleared ✔ \[0%\]$/.test(e1 || "") && /^Wave 2\/3 · \d+ left \[100%\]$/.test(s2 || "")
          && /^Wave 2\/3 · Cleared ✔/.test(e2 || "") && /^Wave 3\/3 · [3-9] left/.test(s3 || "") && !(stats.titles || []).some((t) => /WAVE \d\/3/.test(t))
          && !(stats.bottom || "").includes("Wave") && !(stats.top || "").includes("Wave");
        console.log(`  شريط الموجة بأعلى الشاشة ${waveOk ? "✔" : "✖"}: ${waveLines.map((l) => `"${l}"`).join(" → ")}`);
        if (!waveOk) failures.push("شريط الموجة بأعلى الشاشة (Wave رقم + الباقي) ما يشتغل صح");
        // بداية كل موجة: بوق الغارة الأصلي + سطر قصير فوق الهوت بار
        const horn = stats.soundIds.has("raid.horn"), waveNote = [1, 2].every((n) => (stats.titles || []).some((t) => new RegExp(`Wave ${n}/3 §7· \\d+ monsters`).test(t))) && (stats.titles || []).some((t) => /Wave 3\/3 §7· the warden/.test(t));
        console.log(`  بداية الموجة: بوق الغارة ${horn ? "✔" : "✖"} | سطر فوق الهوت بار ${waveNote ? "✔" : "✖"}`);
        if (!horn || !waveNote) failures.push("بداية الموجة (بوق + سطر) ما تطلع");
        advance(40);
        const sealBanner = (stats.titles || []).some((t) => t.includes("RIFT SEALED"));
        if (!sealBanner) failures.push("إعلان سد الصدع ما طلع فوق الهوت بار");
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
      const extraLow = { "sh:shadow_hound": ["shade_portal"], "sh:sand_scorpion": ["sand_mound", "sand_stinger"] };   // V1: أشكال 3D لمهارات الوحوش
      for (const [type, dist, shape] of cases) {
        stats.shapeV = {};
        entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 400; player._max = 400; player._valid = true;
        const m = mkEntity(type, { x: 0, y: 64, z: dist }, dims.overworld, 60); entities.push(m);
        const d0 = stats.damage || 0; let seen = 0; const zones0 = stats.spawned;
        const pid = shape.startsWith("particle:") ? shape.slice(9) : null, pc0 = pid ? ((stats.pById || {})[pid] || 0) : 0;
        const keepRange = type === "sh:ember_imp";                                // العفريت لو انقض أول مرة يقرب ويبقى قريب وما يرمي كرة النار (اختبار عشوائي): نرجعه للمسافة
        for (let t = 0; t < 1500; t += 2) { advance(2); if (pid ? ((stats.pById || {})[pid] || 0) > pc0 : entities.some((e) => e._valid && e.typeId === "sh:fx_shape" && e.getProperty("sh:v") === sid(shape))) seen++; player.location = { x: 0, y: 64, z: 0 }; if (keepRange && !seen) m.location = { x: 0, y: 64, z: dist }; }
        const dmg = Math.round((stats.damage || 0) - d0);
        const ex = (extraLow[type] || []).map((n) => `${n}×${stats.shapeV[sid(n)] || 0}`).join(" ");
        console.log(`  ${type.padEnd(18)} مسافة ${dist}: شكل ${shape} ${seen ? "✔" : "✖"} | ضرر للاعب ${dmg} | كيانات ${stats.spawned - zones0}${ex ? " | " + ex : ""}`);
        for (const n of extraLow[type] || []) if (!stats.shapeV[sid(n)]) failures.push(`${type}: الشكل ${n} ما انرسم`);
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
      const wantShapes = { "sh:gloomhorn": ["spirit_stag", "spirit_antlers", "soul_wave", "soul_chain"], "sh:hollow_seer": ["root_spike", "soul_orb", "seer_beam"], "sh:veilfox": ["foxfire", "fox_moon"], "sh:magmamoth": ["fireball", "magma_ring", "magma_fissure", "magma_geyser", "magma_plates"], "sh:grey_bear": ["bear_claws", "roar_wave", "bear_grip", "sleep_z"] };
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
        {                                                                     // V1: الوحش يموت بنص مهارة: أشكال الحالة (قرون، كفوف، Z، سلاسل) تنشال
          const LIVE = ["spirit_antlers", "soul_chain", "bear_grip", "sleep_z", "hollow_eyes", "puppet_string"].map((n) => SHP[n]);
          const liveNow = () => entities.filter((e) => e._valid && e.typeId === "sh:fx_shape" && LIVE.includes(e.getProperty("sh:v"))).length;
          const mm = entities.find((e) => e._valid && e.typeId === type);
          let leak = -1;
          if (mm) { for (let t = 0; t < 1200 && !liveNow(); t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; }
            if (liveNow()) { mm._valid = false; fire("entityDie", { deadEntity: mm, damageSource: { damagingEntity: player } }); advance(6); leak = liveNow(); } }
          if (leak > 0) failures.push(`${type}: شكل مهارة بقى معلق بعد موت الوحش (${leak})`);
          if (leak >= 0) console.log(`  ${"".padEnd(16)} موت بنص المهارة: أشكال معلقة ${leak}`);
        }
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
    // v1.39 الحاصد الأجوف: خيوط الدمية (سحبة، والداش يقطعها)، النظرة الجوفاء (بطء I بس بدون ظلام، واللي يلف وجهه ينجو)،
    // المنجل الخاتم (يقفل بس الأيتم اللي بإيدك 8 ثواني)، ضعف النار (يتخبط ويتفحم وتتوقف مهاراته)، والمنجل يسقط دائماً + مهارتين المنجل
    {
      console.log("\nالحاصد الأجوف:");
      const clear = () => { entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true; player._effs = {}; };
      const harv = (z) => { const m = mkEntity("sh:hollow_harvester", { x: 0, y: 64, z }, dims.overworld, 320); m._max = 320; m._yaw = 180; entities.push(m); return m; };
      const waitState = (m, want, z, maxT = 6000) => { for (let t = 0; t < maxT; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; if (m.getProperty("sh:state") === want) return true; if (m.getProperty("sh:state") === 0 && t % 40 === 0) m.location = { x: 0, y: 64, z }; } return false; };
      const heard = (id) => stats.soundIds.has(id);
      const SHH = JSON.parse(fs.readFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), "../../../scripts/shapes.js"), "utf8").match(/SHAPE = (\{.*?\});/)[1]);
      stats.shapeV = {};
      // 0) V1.1: رتبته Dread (فوق الملعونة) وتبين بالاسم فوقه
      clear(); let m = harv(9); advance(24); const dreadTag = /\[Dread/.test(m.nameTag || "");
      if (!dreadTag) failures.push(`الحاصد: لازم رتبته Dread فوق الملعونة (الاسم: ${m.nameTag})`);
      console.log(`  الرتبة Dread فوق الملعونة ${dreadTag ? "✔" : "✖"} (${m.nameTag})`);
      // 1) الخيوط تسحب
      clear(); m = harv(9); stats.soundIds.clear();
      const strings = waitState(m, 1, 9); const k0 = stats.knock || 0, d0 = stats.damage || 0;
      let yanked = false; for (let t = 0; t < 30 && !yanked; t += 2) { advance(2); if (m.getProperty("sh:state") === 2) yanked = true; }
      const pulled = (stats.knock || 0) > k0 && (stats.damage || 0) > d0, strSnd = heard("sh.harv_string_cast") && heard("sh.harv_yank");
      // 2) الداش يقطع الخيط قبل السحبة
      clear(); m = harv(9);
      const strings2 = waitState(m, 1, 9); advance(2);
      player.location = { x: 3.2, y: 64, z: 0 }; let snapped = false, yank2 = false;
      for (let t = 0; t < 20; t += 2) { advance(2); player.location = { x: 3.2, y: 64, z: 0 }; if (m.getProperty("sh:state") === 2) yank2 = true; if (m.getProperty("sh:state") === 0) snapped = true; }
      const snapSnd = heard("sh.harv_snap");
      // 3) النظرة: تباوع عليه = Slowness I (amplifier 0) بدون ظلام؛ تلف وجهك = ما يصير شي
      clear(); m = harv(6);
      const stare = waitState(m, 3, 6); for (let t = 0; t < 16; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; }
      const slow = player._effs.slowness, stareOk = !!slow && slow.amp === 0 && !player._effs.darkness && !player._effs.blindness;
      clear(); m = harv(6); const gv = player.getViewDirection; player.getViewDirection = () => ({ x: 0, y: 0, z: -1 });
      const stare2 = waitState(m, 3, 6); for (let t = 0; t < 16; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; }
      const dodged = !player._effs.slowness; player.getViewDirection = gv;
      // 4) المنجل الخاتم: يقفل الساطور اللي بإيدك 8 ثواني بس، وباقي الأيتمات تشتغل
      clear(); hold("sh:ember_cleaver"); m = harv(2.5); const d1 = stats.damage || 0;
      const reap = waitState(m, 4, 2.5); for (let t = 0; t < 16; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; }
      const reapDmg = Math.round((stats.damage || 0) - d1);
      const harvShapes = ["puppet_string", "hollow_eyes", "reap_arc", "seal_sigil"].map((n) => [n, stats.shapeV[SHH[n]] || 0]);   // V1: أشكال 3D لمهارات الفزاعة
      m._valid = false; stats.actionBars = []; stats.titles = [];
      fire("itemUse", { source: player, itemStack: new ItemStack("sh:ember_cleaver") }); advance(10);
      const blocked = stats.actionBars.concat(stats.titles || []).some((t) => /SEALED/.test(t));
      stats.actionBars = []; stats.titles = []; hold("sh:stone_maul");
      fire("itemUse", { source: player, itemStack: new ItemStack("sh:stone_maul") }); advance(10);
      const otherFree = !stats.actionBars.concat(stats.titles || []).some((t) => /Stone Maul is SEALED/.test(t));
      advance(170); stats.actionBars = []; stats.titles = []; hold("sh:ember_cleaver");
      fire("itemUse", { source: player, itemStack: new ItemStack("sh:ember_cleaver") }); advance(10);
      const freed = !stats.actionBars.concat(stats.titles || []).some((t) => /SEALED/.test(t));
      hold(undefined);
      // 5) النار: يتخبط (حالة 5) ويتفحم (sh:hot) وما يستعمل مهارات، وبعد ما تنطفي يرجع
      clear(); m = harv(9); advance(4); m.setOnFire(3); let burnState = false, hot = false, skillWhileBurning = false;
      for (let t = 0; t < 56; t += 2) { advance(2); player.location = { x: 0, y: 64, z: 0 }; const st = m.getProperty("sh:state"); if (st === 5) burnState = true; if (st >= 1 && st <= 4) skillWhileBurning = true; if (m.getProperty("sh:hot") === 1) hot = true; }
      for (let t = 0; t < 30; t += 2) advance(2);
      const recovered = m.getProperty("sh:state") !== 5; advance(80); const cooled = m.getProperty("sh:hot") === 0;
      // 6) المنجل يسقط بنسبة نادرة كلش (V1: 5%)
      clear(); stats.items = [];
      const NK = 600;
      for (let i = 0; i < NK; i++) { const h = mkEntity("sh:hollow_harvester", { x: 2, y: 64, z: 2 }, dims.overworld, 10); entities.push(h); h._valid = false; fire("entityDie", { deadEntity: h, damageSource: { damagingEntity: player } }); }
      const scythes = stats.items.filter((x) => x === "sh:harvest_scythe").length, scyRate = scythes / NK;
      // 7) سلاح المنجل: الحصدة العريضة، وخيوط الدمية (Lv2) تسحب الأعداء، والحصاد (+50%) على عدو صحته واطية
      clear(); spawnZombies(4, true); player._hp = 2000; stats.soundIds.clear(); hold("sh:harvest_scythe"); const d2 = stats.damage || 0;
      stats.shapeV = {};
      fire("itemUse", { source: player, itemStack: new ItemStack("sh:harvest_scythe") }); advance(6);
      const arcDmg = Math.round((stats.damage || 0) - d2), arcSnd = heard("sh.scythe_swing"), arcShape = (stats.shapeV[SHH.reap_arc] || 0) > 0;   // V1.1: هلال 3D
      player.setDynamicProperty("sh_wlv", JSON.stringify({ "sh:harvest_scythe": { lv: 2, xp: 0 } }));
      player.isSneaking = true; const k1 = stats.knock || 0, d3 = stats.damage || 0;
      fire("itemUse", { source: player, itemStack: new ItemStack("sh:harvest_scythe") }); advance(20); player.isSneaking = false;
      const strPulled = (stats.knock || 0) - k1 >= 1 && (stats.damage || 0) > d3, strShapes = stats.shapeV[SHH.puppet_string] || 0;   // V1.1: خيط 3D لكل عدو
      const low = mkEntity("minecraft:zombie", { x: 0, y: 64, z: 2 }, dims.overworld, 40); low._hp = 6; entities.push(low); stats.actionBars = []; stats.titles = [];
      fire("entityHitEntity", { damagingEntity: player, hitEntity: low }); advance(10);
      const reaped = stats.actionBars.concat(stats.titles || []).some((t) => /Reaped!/.test(t));
      hold(undefined); player.setDynamicProperty("sh_wlv", "{}");
      console.log(`  خيوط ${strings ? "✔" : "✖"} سحبة ${yanked && pulled ? "✔" : "✖"} صوت ${strSnd ? "✔" : "✖"} | الداش يقطعها ${strings2 && snapped && !yank2 ? "✔" : "✖"} صوت ${snapSnd ? "✔" : "✖"}`);
      console.log(`  نظرة ${stare ? "✔" : "✖"} بطء I بدون ظلام ${stareOk ? "✔" : "✖"} | لف وجهك ينجيك ${stare2 && dodged ? "✔" : "✖"}`);
      console.log(`  المنجل الخاتم ${reap ? "✔" : "✖"} ضرر ${reapDmg} | الساطور مختوم ${blocked ? "✔" : "✖"} | المطرقة حرة ${otherFree ? "✔" : "✖"} | بعد 8 ثواني ينفك ${freed ? "✔" : "✖"}`);
      console.log(`  النار: يتخبط ${burnState ? "✔" : "✖"} يتفحم ${hot ? "✔" : "✖"} بدون مهارات ${!skillWhileBurning ? "✔" : "✖"} يرجع ${recovered ? "✔" : "✖"} ينطفي التفحم ${cooled ? "✔" : "✖"} | المنجل نادر ${(scyRate * 100).toFixed(1)}% (${scythes}/${NK}) ${scyRate > 0.015 && scyRate < 0.1 ? "✔" : "✖"}`);
      console.log(`  سلاح المنجل: حصدة ضرر ${arcDmg} صوت ${arcSnd ? "✔" : "✖"} هلال 3D ${arcShape ? "✔" : "✖"} | خيوط تسحب ${strPulled ? "✔" : "✖"} خيوط 3D ×${strShapes} | حصاد الضعيف ${reaped ? "✔" : "✖"}`);
      console.log(`  أشكال المهارات: ${harvShapes.map(([n, c]) => `${n}×${c}`).join(" ")}`);
      for (const [n, c] of harvShapes) if (!c) failures.push(`الحاصد: الشكل ${n} ما انرسم`);
      if (!strings || !yanked || !pulled || !strSnd) failures.push("الحاصد: خيوط الدمية ما سحبت");
      if (!strings2 || !snapped || yank2) failures.push("الحاصد: الداش ما يقطع الخيوط");
      if (!stare || !stareOk) failures.push("الحاصد: النظرة الجوفاء لازم Slowness I بس وبدون ظلام");
      if (!stare2 || !dodged) failures.push("الحاصد: اللي يلف وجهه لازم ينجو من النظرة");
      if (!reap || reapDmg <= 0 || !blocked || !otherFree || !freed) failures.push("الحاصد: المنجل الخاتم (قفل الأيتم بالإيد 8 ثواني) ما اشتغل صح");
      if (!burnState || !hot || skillWhileBurning || !recovered || !cooled) failures.push("الحاصد: ضعف النار ما اشتغل");
      if (!(scyRate > 0.015 && scyRate < 0.1)) failures.push("الحاصد: المنجل لازم يسقط بنسبة نادرة (~5%)");
      if (arcDmg <= 0 || !arcSnd || !strPulled || !reaped) failures.push("منجل الحاصد: مهاراته أو الحصاد ما اشتغلت");
      if (!arcShape || strShapes < 1) failures.push("منجل الحاصد: لازم الحصدة تطلع هلال 3D والخيوط تطلع خيط 3D لكل عدو");
      clear(); player._hp = 20; player._max = 20;
    }
    // v1.39 لعنة القرويين: أمر التجربة يلعن أقرب قروي (سريع ×20)، البقع تكبر 1→2→3، يتشنج ويتحول لوحش برتبة، وقتله قبل التحول ينهي اللعنة
    {
      console.log("\nلعنة القرويين:");
      const RANKED = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion", "sh:gloomhorn", "sh:hollow_seer", "sh:veilfox", "sh:magmamoth", "sh:grey_bear", "sh:prayer_mantis", "sh:hollow_harvester"];
      const clear = () => { entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 }; player._hp = 2000; player._max = 2000; player._valid = true; };
      const vil = () => { const v = mkEntity("minecraft:villager_v2", { x: 2, y: 64, z: 2 }, dims.overworld, 20); entities.push(v); return v; };
      clear(); let v0 = vil(); stats.soundIds.clear();
      fire("scriptEventReceive", { id: "sh:curse", message: "fast", sourceEntity: player }); advance(2);
      let cv = entities.find((e) => e._valid && e.typeId === "sh:cursed_villager");
      const replaced = !!cv && !v0._valid;
      const stages = new Set(); let shook = false;
      for (let t = 0; t < 600 && cv && cv._valid; t += 2) { advance(2); stages.add(cv.getProperty("sh:stage")); if (cv.getProperty("sh:shake") === 1) shook = true; }
      const turned = entities.filter((e) => e._valid && RANKED.includes(e.typeId) && Math.hypot(e.location.x - 2, e.location.z - 2) < 2);   // الوحوش الطبيعية تطلع بعيد
      const gone = cv && !cv._valid, sndTurn = stats.soundIds.has("sh.curse_turn") && stats.soundIds.has("sh.curse_burst") && stats.soundIds.has("sh.curse_mark");
      // قتله قبل التحول
      clear(); v0 = vil(); stats.soundIds.clear(); setState(baseState(null));
      fire("scriptEventReceive", { id: "sh:curse", message: "fast", sourceEntity: player }); advance(40);
      cv = entities.find((e) => e._valid && e.typeId === "sh:cursed_villager");
      if (cv) { cv._valid = false; fire("entityDie", { deadEntity: cv, damageSource: { damagingEntity: player } }); }
      advance(600);
      const noMonster = !entities.some((e) => e._valid && RANKED.includes(e.typeId) && Math.hypot(e.location.x - 2, e.location.z - 2) < 2);   // الوحوش الطبيعية تطلع بعيد
      const freed = stats.soundIds.has("sh.curse_free"), counted = ((JSON.parse(player.getDynamicProperty("sh")).kills || {})["sh:cursed_villager"] || 0) === 1;
      console.log(`  انلعن وانبدل ${replaced ? "✔" : "✖"} | مراحل ${[...stages].sort().join("→")} ${stages.has(1) && stages.has(2) && stages.has(3) ? "✔" : "✖"} | تشنج ${shook ? "✔" : "✖"} | تحول لوحش ${turned.length === 1 && gone ? "✔" : "✖"} (${turned.map((e) => e.typeId).join(",")}) | أصوات ${sndTurn ? "✔" : "✖"}`);
      console.log(`  قتله قبل التحول: ما طلع وحش ${noMonster ? "✔" : "✖"} | صوت فك اللعنة ${freed ? "✔" : "✖"} | انحسب بكتاب الوحوش ${counted ? "✔" : "✖"}`);
      if (!replaced || !(stages.has(1) && stages.has(2) && stages.has(3)) || !shook || turned.length !== 1 || !gone || !sndTurn) failures.push("لعنة القرويين: المراحل أو التحول ما اشتغلت");
      if (!noMonster || !freed || !counted) failures.push("لعنة القرويين: قتله قبل التحول لازم ينهي اللعنة");
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
    // V1: البنايات الفريدة والسجل: كل ضريح مرة وحدة بالعالم، السجل على أجزاء، والبناء المقطوع يكمل من وين وقف
    {
      console.log("\nالبنايات الفريدة والسجل:");
      const ST = await import(new URL("../../../scripts/structures.js", import.meta.url).href);
      let dupe = 0;
      const both = [{ type: "village" }, { type: "shrine" }, { type: "lightshrine" }, { type: "tower" }, { type: "temple" }];
      for (let i = 0; i < 4000; i++) { const t = ST.chooseType(both); if (t === "shrine" || t === "lightshrine" || t === "temple") dupe++; }
      const pity1 = ST.chooseType([{ type: "village" }, { type: "tower" }]) === "shrine";
      const pity2 = ST.chooseType([{ type: "village" }, { type: "tower" }, { type: "shrine" }, { type: "ruins" }]) === "lightshrine";
      // سجل كبير (900 بناية) على أجزاء: ينقرى كامل، ويضيف بناية وينحفظ أجزاء كل وحدة أقل من 30 ألف حرف
      const big = Array.from({ length: 900 }, (_, i) => ({ x: 5000 + i * 200, y: 64, z: 5000, type: "tower", rot: 0, seed: i, v: 2, ok: 1, fl: 127, cl: 63, ft: { 0: [], 1: [] }, fn: { 0: 3, 1: 4 } }));
      const txt = JSON.stringify(big); world._dyn = { ...world._dyn };
      const parts = []; for (let i = 0; i < txt.length; i += 30000) parts.push(txt.slice(i, i + 30000));
      parts.forEach((q, i) => world.setDynamicProperty(i ? `sh_structs_${i}` : "sh_structs", q)); world.setDynamicProperty("sh_structs_n", parts.length - 1);
      const readBack = ST.structList().length;
      world.setDynamicProperty("sh_temple_at", JSON.stringify({ x: 7, y: 64, z: 7, rot: 0, seed: 3 }));
      ST.findTemple({ x: 0, y: 64, z: 0 });                                       // ما بالسجل معبد: يرجع من sh_temple_at وينحفظ
      const n2 = world._dyn.sh_structs_n || 0, saved = [world._dyn.sh_structs, ...Array.from({ length: n2 }, (_, i) => world._dyn[`sh_structs_${i + 1}`])];
      const partsOk = saved.every((q) => typeof q === "string" && q.length <= 30000), total = JSON.parse(saved.join("")).length;
      // البناء المقطوع: خرائب تنبني، المنطقة تنشال بنصها (اللاعب بعد) فتوقف وتحفظ التقدم، وترجع تكمل من نفس المكان لما يرجع
      world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 40, y: 64, z: 0, type: "ruins", rot: 0, seed: 9, v: 2, pi: 0 }])); world.setDynamicProperty("sh_structs_n", 0);
      world.setDynamicProperty("sh_temple_at", undefined);
      entities.forEach((x) => (x._valid = false)); entities.length = 0; player.location = { x: 0, y: 64, z: 0 };
      const reg1 = () => JSON.parse(world._dyn.sh_structs)[0];
      let started = false; for (let t = 0; t < 200 && !started; t += 2) { advance(2); started = (reg1().pi || 0) > 0; }
      globalThis.__unloaded = true; advance(60);
      const paused = reg1(), pausedAt = paused.pi;
      advance(300); const still = reg1().pi === pausedAt && !reg1().ok;          // وهي مقطوعة ما تتحرك
      globalThis.__unloaded = false;
      let done = false; for (let t = 0; t < 20000 && !done; t += 10) { advance(10); done = reg1().ok === 1; }
      const fin = reg1();
      console.log(`  الضريحين ما يتكررون (4000 اختيار) ${dupe === 0 ? "✔" : "✖ " + dupe} | ضمان الضريح المظلم ${pity1 ? "✔" : "✖"} ثم المضيء ${pity2 ? "✔" : "✖"}`);
      console.log(`  سجل 900 بناية على ${parts.length} أجزاء: انقرى ${readBack} ${readBack === 900 ? "✔" : "✖"} | انحفظ ${total} بأجزاء ≤30000 ${partsOk && total === 901 ? "✔" : "✖"}`);
      console.log(`  بناء مقطوع: بدى ${started ? "✔" : "✖"} | وقف عند ${pausedAt} بدون ok ${!paused.ok && pausedAt > 0 ? "✔" : "✖"} | ما يتحرك وهو مقطوع ${still ? "✔" : "✖"} | كمل وخلص ${fin.ok === 1 && fin.pi === undefined ? "✔" : "✖"}`);
      if (dupe) failures.push(`الضريح أو المعبد ممكن يتكرر (${dupe} مرة من 4000)`);
      if (!pity1 || !pity2) failures.push("ضمان ظهور الضريحين ما يشتغل");
      if (readBack !== 900 || !partsOk || total !== 901) failures.push("سجل البنايات على أجزاء ما ينقرى أو ينحفظ صح");
      if (!started || paused.ok || !(pausedAt > 0) || !still || fin.ok !== 1 || fin.pi !== undefined) failures.push("البناء المقطوع ما يكمل من وين وقف");
      globalThis.__unloaded = false; entities.forEach((x) => (x._valid = false)); entities.length = 0;
      world.setDynamicProperty("sh_structs", "[]"); world.setDynamicProperty("sh_structs_n", 0);
    }
    // برج الهاوية: وحوش كل طابق تطلع أول ما يوصله اللاعب (مرة وحدة)، والطابق السابع وحوش عالية؛ موتهم يطلّع صندوق القمة
    {
      console.log("\nبرج الهاوية:");
      entities.forEach((x) => (x._valid = false)); entities.length = 0;
      player._hp = 2000; player._max = 2000; player._valid = true;
      world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 200, y: 64, z: 200, type: "tower", rot: 1, seed: 11, v: 2, ok: 1 }]));
      stats.setTypes = []; stats.chestItems = [];
      const LOW = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"], GRIM = ["sh:gloomhorn", "sh:hollow_seer", "sh:veilfox"], HIGH = ["sh:magmamoth", "sh:grey_bear", "sh:prayer_mantis", "sh:hollow_harvester"];
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
          advance(10); hudFloor = (bossBar("sh:hud_bar_near") || { name: "" }).name;
          if (!(stats.titles || []).some((t) => /Abyss Tower §7· §dFloor 1\/7 §7· monsters left: 3/.test(t))) failures.push("البرج: سطر الطابق (الرقم وعدد الوحوش) ما طلع فوق الهوت بار");
          const xp0 = entities.filter((e) => e.typeId === "minecraft:xp_orb").length;
          for (const e of neu) { e._valid = false; fire("entityDie", { deadEntity: e, damageSource: {} }); }
          advance(20);
          sealOff = stats.setTypes.filter((q) => q[3] === "minecraft:air" && q[1] === 64 + 6).length >= 4;
          orbs = entities.filter((e) => e.typeId === "minecraft:xp_orb").length > xp0;
          hudClear = (bossBar("sh:hud_bar_near") || { name: "" }).name;
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
      console.log(`  ختم الدرج ${sealOn ? "✔" : "✖"} | ينكسر لما ينظف الطابق ${sealOff ? "✔" : "✖"} | خبرة ${orbs ? "✔" : "✖"} | شريط أعلى الشاشة: "${hudFloor || "-"}" ثم "${hudClear || "-"}"`);
      if (!sealOn || !sealOff || !orbs || !/^Abyss Tower · Floor 1\/7 · 3 left$/.test(hudFloor) || !/^Abyss Tower · Floor 1\/7 · Cleared ✔ climb$/.test(hudClear)) failures.push("البرج: الختم أو شريط الطابق بأعلى الشاشة أو جوائز الطابق ما تشتغل");
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
      // v1.37: مواد الرتب العالية نادرة كلش (الدب 5%، السرعوف 3%)، والجواهر نادرة كلش: 300 قتلة لكل واحد حتى نقيس النسبة
      const N = 300;
      for (let i = 0; i < N; i++) { kill("sh:grey_bear"); kill("sh:prayer_mantis"); }
      for (let i = 0; i < 12; i++) kill("sh:shadow_hound");                  // 55% لكل وحدة: 12 قتلة حتى ما يفشل الاختبار بالصدفة
      const dropped = new Set(stats.items), cnt = (id) => stats.items.filter((x) => x === id).length;
      // v1.38: الوحوش تسقط بس شعلات الروح، والدب كمان جلده ومخلبه (لدرعه). ماكو ولا مادة ثانية
      const rate = { hide: cnt("sh:bear_hide") / N, chitin: cnt("sh:bear_claw") / N, ebear: cnt("sh:soul_silver") / N, emantis: cnt("sh:soul_verdant") / N };
      const onlyFlames = [...dropped].every((id) => /^sh:soul_|^sh:bear_(hide|claw)$/.test(id));
      if (!onlyFlames) console.log("   [drops غلط]", [...dropped].join(", "));
      const dropsOk = onlyFlames && rate.hide > 0 && rate.hide <= 0.1 && rate.chitin > 0 && rate.chitin <= 0.07 && rate.ebear > 0 && rate.ebear <= 0.09 && rate.emantis > 0 && rate.emantis <= 0.1;
      console.log(`  ندرة: جلد الدب ${(rate.hide * 100).toFixed(1)}% | مخلب الدب ${(rate.chitin * 100).toFixed(1)}% | شعلة فضية (الدب) ${(rate.ebear * 100).toFixed(1)}% | شعلة خضرة (السرعوف) ${(rate.emantis * 100).toFixed(1)}% (من ${N} قتلة)`);
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
      // 4) طقم الدرع (v1.38): 4 قطع Dawnsteel = Haste وسرعة
      const sp0 = (stats.effects || {}).haste || 0;
      player._equip = { Head: new ItemStack("sh:dawnsteel_helmet"), Chest: new ItemStack("sh:dawnsteel_chestplate"), Legs: new ItemStack("sh:dawnsteel_leggings"), Feet: new ItemStack("sh:dawnsteel_boots") };
      advance(90);
      const setOk = ((stats.effects || {}).haste || 0) > sp0 && stats.actionBars.some((b) => /Set bonus/.test(b));
      // طقم Abyssium: قوة ورؤية ليلية والرد على الضربات (20%)
      const nv0 = (stats.effects || {}).night_vision || 0;
      player._equip = { Head: new ItemStack("sh:abyssium_helmet"), Chest: new ItemStack("sh:abyssium_chestplate"), Legs: new ItemStack("sh:abyssium_leggings"), Feet: new ItemStack("sh:abyssium_boots") };
      advance(50);
      const foe = mkEntity("minecraft:zombie", { x: 1, y: 64, z: 1 }, dims.overworld, 500); entities.push(foe);
      const fh0 = foe._hp;
      for (let i = 0; i < 60; i++) fire("entityHurt", { hurtEntity: player, damage: 4, damageSource: { damagingEntity: foe, cause: "entityAttack" } });
      const countered = foe._hp < fh0 && ((stats.effects || {}).night_vision || 0) > nv0;
      player._equip = {};
      // 4ب) الخامات (v1.38): معول بالدرجة الصح يطيح الخام، معول أضعف ما يطيح شي، Silk Touch يطيح البلوكة نفسها
      const breakOre = (bid, tool) => fire("playerBreakBlock", { player, block: { location: { x: 5, y: 20, z: 5 }, dimension: dims.overworld }, brokenBlockPermutation: { type: { id: bid } }, itemStackBeforeBreak: tool });
      const silkPick = { typeId: "minecraft:diamond_pickaxe", amount: 1, getComponent: (n) => (n === "minecraft:enchantable" ? { getEnchantment: (id) => (id === "silk_touch" ? { level: 1 } : undefined) } : undefined) };
      stats.items = [];
      breakOre("sh:dawnsteel_ore", new ItemStack("minecraft:stone_pickaxe"));
      breakOre("sh:deepslate_abyssium_ore", new ItemStack("minecraft:stone_pickaxe"));   // يحتاج حديد: ما يطيح
      breakOre("sh:abyssium_ore", new ItemStack("minecraft:iron_pickaxe"));
      breakOre("sh:dawnsteel_ore", new ItemStack("minecraft:wooden_pickaxe"));          // خشب: ما يطيح
      breakOre("sh:deepslate_dawnsteel_ore", silkPick);
      const ores = stats.items.slice();
      const oresOk = ores.length === 3 && ores[0] === "sh:raw_dawnsteel" && ores[1] === "sh:raw_abyssium" && ores[2] === "sh:deepslate_dawnsteel_ore";
      console.log(`  الخامات: معول صح يطيح الخام، أضعف ما يطيح، Silk Touch البلوكة ${oresOk ? "✔" : "✖"} (${ores.join(", ")})`);
      if (!oresOk) failures.push("إسقاط الخامات غلط");
      // 5) الخيميائي: يظهر بالقرية، ويطبخ جرعة لما تكون عندك المواد
      world.setDynamicProperty("sh_structs", JSON.stringify([{ x: 300, y: 64, z: 300, type: "village", rot: 0, seed: 5, v: 2, ok: 1 }]));
      player.location = { x: 300, y: 64, z: 320 };
      advance(420);
      const alch = entities.find((e) => e._valid && e.typeId === "sh:alchemist");
      inventory.fill(undefined);
      // v1.37.2: شاشة مستوحاة من طاولة السحر: 15 زر بترتيب ثابت (0..2 صفوف الطبخ، 3 خانة الماء، 4 خانة الشعلة، 5 الوصفات، 6..14 الحقيبة)
      inventory[3] = new ItemStack("sh:bear_hide", 5); inventory[4] = new ItemStack("sh:soul_crimson", 3); inventory[5] = new ItemStack("sh:soul_amber", 2); inventory[6] = new ItemStack("minecraft:potion", 2);
      const ui = (await import("@minecraft/server-ui")).sim;
      // حط الماء (الحقيبة 6) ← حط الأحمر (الحقيبة 6 بعد ما راح الماء) ← اطبخ ×1 ← طلّع الشعلة (خانة 4) ← حط البرتقالي (الحقيبة 7) ← اطبخ ×1
      ui.formsShown.length = 0; ui.queue = [6, 6, 0, 4, 7, 0]; ui.cancelWhenEmpty = true;
      if (alch) fire("playerInteractWithEntity", { player, target: alch });
      await new Promise((r) => setTimeout(r, 30)); advance(2);
      const F = ui.formsShown, f0 = F[0] || { buttons: [], icons: [] }, f2 = F[2] || { buttons: [], icons: [] };
      const layoutOk = /§a§l§c§h/.test(f0.title || "") && f0.buttons.length === 15 && f0.buttons.slice(0, 3).every((b) => b.startsWith("§l§r"))
        && !f0.icons[3] && !f0.icons[4] && /potion_bottle/.test(f0.icons[6] || "") && /sh_soul_crimson/.test(f0.icons[7] || "") && /sh_soul_amber/.test(f0.icons[8] || "")
        && f2.buttons[0].startsWith("§k§r") && f2.buttons[1].startsWith("§o§r") && /potion_bottle/.test(f2.icons[3] || "") && /sh_soul_crimson/.test(f2.icons[4] || "")
        && /sh_potion_vitality/.test(f2.icons[0] || "") && !(f2.icons.slice(6).some((x) => /potion_bottle|soul_crimson/.test(x || "")));
      const got = (id) => inventory.filter((it) => it && it.typeId === id).reduce((a, it) => a + it.amount, 0);
      const brewed = got("sh:potion_vitality") === 1 && got("sh:potion_might") === 1;
      const paid = got("sh:soul_crimson") === 1 && got("sh:soul_amber") === 0 && got("minecraft:potion") === 0 && got("sh:bear_hide") === 5;
      inventory.fill(undefined); ui.formsShown.length = 0; ui.queue = [];
      advance(12); if (alch) fire("playerInteractWithEntity", { player, target: alch });
      await new Promise((r) => setTimeout(r, 30)); advance(2);
      const fe = ui.formsShown[0] || { buttons: [], body: "" };
      const runesOk = fe.buttons.length === 15 && fe.buttons.slice(0, 3).every((b) => b.startsWith("§l§r")) && /no water bottles/.test(fe.body || "");
      ui.cancelWhenEmpty = false;
      world.setDynamicProperty("sh_structs", "[]"); inventory.fill(undefined);
      console.log(`  مواد الوحوش ${dropsOk ? "✔" : "✖"} (${[...dropped].filter((x) => x.includes("hide") || x.includes("chitin") || x.includes("pelt") || x.includes("scythe") || x.includes("claw")).join(", ")})`);
      console.log(`  المانا: مهارة غالية انعادت ${used} مرات ثم ${blocked ? "انقفلت (مانا ما تكفي) ✔" : "ما انقفلت ✖"} | المانا بالـHUD ${manaShown ? "✔" : "✖"}`);
      console.log(`  الجرعات: تأثيرات ${potOk ? "✔" : "✖"} | تقويات محفوظة ${buffsOk ? "✔" : "✖"} (${Object.keys(buffs).join(",")}) | أيقونات بالـHUD ${/[-]/.test(hudBuff) ? "✔" : "✖"}`);
      console.log(`  طقم Dawnsteel (Haste) ${setOk ? "✔" : "✖"} | طقم Abyssium (رد الضربات + رؤية ليلية) ${countered ? "✔" : "✖"}`);
      console.log(`  الخيميائي ظهر بالقرية ${alch ? "✔" : "✖"} | ترتيب الشاشة ${layoutOk ? "✔" : "✖"} | حط بالخانات من الحقيبة وطبخ جرعتين ${brewed ? "✔" : "✖"} | أخذ المواد ${paid ? "✔" : "✖"} | بدون شعلة = رونز ${runesOk ? "✔" : "✖"}`);
      // 6) الإنجازات (v1.36): تنفتح من حالة اللاعب ومن الأحداث، تعطي خبرة، وشاشاتها بالكتاب بصور (المقفول ??? وصورة _x)
      {
        const ACHJS = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/achievements.js"), "utf8");
        const achIds = [...ACHJS.matchAll(/"id": "([a-z0-9_]+)"/g)].map((m) => m[1]);
        const mainJs = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/main.js"), "utf8");
        const checkBlock = mainJs.slice(mainJs.indexOf("const ACH_CHECK = {"), mainJs.indexOf("function achCheck(p)"));
        const noCheck = achIds.filter((id) => !new RegExp(`\\b${id}:`).test(checkBlock));
        const ui2 = (await import("@minecraft/server-ui")).sim;
        player.setDynamicProperty("sh_ach", undefined); stats.titles = []; stats.messages.length = 0;
        const s0 = baseState("star"); s0.rank = 1; setState(s0);
        const xp0 = s0.xp || 0;
        advance(45);
        const achU = () => (JSON.parse(player.getDynamicProperty("sh_ach") || "{}").u || {});
        const auto = ["star_touched", "first_lesson", "rank_trainee"].every((id) => achU()[id]);
        const xpUp = JSON.parse(player.getDynamicProperty("sh")).xp > xp0 || JSON.parse(player.getDynamicProperty("sh")).level > s0.level;
        const shown = (stats.titles || []).some((t) => /Achievement: /.test(t)) && stats.messages.some((m) => /\[Achievement\]/.test(m));
        for (const pid of ["sh:potion_vitality", "sh:potion_mana", "sh:potion_might", "sh:potion_bulwark", "sh:potion_focus", "sh:potion_swift"]) fire("itemCompleteUse", { source: player, itemStack: new ItemStack(pid) });
        for (let i = 0; i < 16 && !achU().mana_dry; i++) { fire("scriptEventReceive", { id: "sh:cdreset_cd_only", message: "", sourceEntity: player }); await useItem("sh:skill_meteor"); advance(6); }
        ui2.queue = []; ui2.cancelWhenEmpty = true;
        await useItem("sh:explorer_compass"); await new Promise((r) => setTimeout(r, 20)); advance(45);
        const events = ["potion_six", "mana_dry", "pathfinder"].filter((id) => !achU()[id]);
        // الشاشات: الكتاب ← [Achievements] ← Journey ← أول إنجاز (تفاصيل)
        ui2.formsShown.length = 0; ui2.queue = []; ui2.cancelWhenEmpty = true;
        await useItem("sh:evolution_book"); await new Promise((r) => setTimeout(r, 20));
        const book = ui2.formsShown[0] || { buttons: [] };
        const bi = book.buttons.findIndex((b) => b.includes("[Achievements]"));
        ui2.formsShown.length = 0; ui2.queue = [bi, 0, 1];
        await useItem("sh:evolution_book"); for (let i = 0; i < 6; i++) await new Promise((r) => setTimeout(r, 10));
        const [fb, fc, fl, fd] = ui2.formsShown;
        const catsOk = fc && fc.title === "Achievements" && fc.buttons.length === 7 && fc.icons.every((ic) => /^textures\/ui\/sh_ach\/cat_/.test(ic || ""));
        const listOk = fl && fl.title === "Journey" && fl.icons[0] === "textures/ui/sh_ach/star_touched" && /✔ Star-Touched/.test(fl.buttons[0])
          && fl.icons[1] === "textures/ui/sh_ach/unbound_x" && /^§8\?\?\?/.test(fl.buttons[1]) && /A secret/.test(fl.buttons[1]);
        const detailOk = fd && fd.title === "???" && /secret/.test(fd.body);
        ui2.queue = []; ui2.cancelWhenEmpty = false;
        const iconsOk = achIds.every((id) => fs.existsSync(path.join(root, `AnimePowers/RP/textures/ui/sh_ach/${id}.png`)) && fs.existsSync(path.join(root, `AnimePowers/RP/textures/ui/sh_ach/${id}_x.png`)));
        const achOk = achIds.length >= 40 && !noCheck.length && auto && xpUp && shown && !events.length && bi >= 0 && catsOk && listOk && detailOk && iconsOk;
        console.log(`  الإنجازات: ${achIds.length} إنجاز | شرط لكل واحد ${noCheck.length ? "✖ " + noCheck.join(",") : "✔"} | تنفتح لحالها + خبرة + إعلان ${auto && xpUp && shown ? "✔" : "✖"} | أحداث (جرعات، مانا، بوصلة) ${events.length ? "✖ " + events.join(",") : "✔"} | شاشات الكتاب بالصور ${bi >= 0 && catsOk && listOk && detailOk ? "✔" : "✖"} | الصور موجودة ${iconsOk ? "✔" : "✖"}`);
        if (!achOk) failures.push("الإنجازات ما تشتغل صح");
        player.setDynamicProperty("sh_ach", undefined);
      }
      // 7) المهمات (v1.37): بالتسلسل، تخلص وحدة تنفتح اللي بعدها، كل وحدة إلها جائزة، والصفحة بالكتاب
      {
        const ui3 = (await import("@minecraft/server-ui")).sim;
        player.setDynamicProperty("sh_mis", undefined); player.setDynamicProperty("sh_ach", undefined); stats.titles = []; stats.messages.length = 0;
        const s0 = baseState(null); s0.level = 1; s0.rank = 0; s0.training = {}; s0.kills = {}; setState(s0);
        const misI = () => (JSON.parse(player.getDynamicProperty("sh_mis") || "{}").i || 0);
        advance(45); const i0 = misI();
        const s1 = JSON.parse(player.getDynamicProperty("sh")); s1.level = 5; setState(s1); advance(45); const i1 = misI();
        const scrollGot = inventory.some((it) => it && it.typeId === "sh:xp_scroll_small");
        const kill = (t) => { const m = mkEntity(t, { x: 2, y: 64, z: 2 }, dims.overworld, 10); entities.push(m); m._valid = false; fire("entityDie", { deadEntity: m, damageSource: { damagingEntity: player } }); };
        for (let k = 0; k < 4; k++) kill("sh:shadow_hound"); advance(45); const i2a = misI();
        kill("sh:shadow_hound"); advance(45); const i2 = misI();
        const shown = (stats.titles || []).some((t) => /Mission complete: §fFirst Hunt/.test(t)) && stats.messages.some((m) => /\[Mission 2\/24\]/.test(m));
        ui3.formsShown.length = 0; ui3.queue = []; ui3.cancelWhenEmpty = true;
        await useItem("sh:evolution_book"); await new Promise((r) => setTimeout(r, 20));
        const bk = ui3.formsShown[0] || { buttons: [] }, mi = bk.buttons.findIndex((b) => b.includes("[Missions]"));
        ui3.formsShown.length = 0; ui3.queue = [mi];
        await useItem("sh:evolution_book"); for (let k = 0; k < 4; k++) await new Promise((r) => setTimeout(r, 10));
        const page = ui3.formsShown.find((f) => f.title === "Missions");
        const pageOk = !!page && /Mission 3\/24/.test(page.body) && /The Fallen Star/.test(page.body) && /^§2✔ First Steps/.test(page.buttons[0]) && /▶ The Fallen Star/.test(page.buttons[2]) && /locked/.test(page.buttons[5]) && /_x$/.test(page.icons[5]);
        ui3.queue = []; ui3.cancelWhenEmpty = false;
        const misOk = i0 === 0 && i1 === 1 && scrollGot && i2a === 1 && i2 === 2 && shown && mi >= 0 && pageOk;
        console.log(`  المهمات: تبدي من الأولى ${i0 === 0 ? "✔" : "✖"} | ليفل 5 ← تخلص الأولى + جائزة ${i1 === 1 && scrollGot ? "✔" : "✖"} | 4 قتلات ما تكفي ${i2a === 1 ? "✔" : "✖"} والخامسة تخلصها ${i2 === 2 ? "✔" : "✖"} | إعلان ${shown ? "✔" : "✖"} | صفحة الكتاب ${mi >= 0 && pageOk ? "✔" : "✖"}`);
        if (!misOk) failures.push("المهمات ما تشتغل صح");
        player.setDynamicProperty("sh_mis", undefined); inventory.fill(undefined);
      }
      if (!dropsOk) failures.push("مواد الوحوش ما طاحت");
      if (!blocked || used < 2 || !manaShown) failures.push("المانا ما تشتغل صح");
      if (!potOk || !buffsOk) failures.push("الجرعات ما تشتغل");
      if (!setOk || !countered) failures.push("بونص طقم الدرع ما يشتغل");
      if (!alch || !brewed || !paid || !layoutOk || !runesOk) failures.push("الخيميائي ما يشتغل");
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
      const side1 = Math.abs(Math.abs(dx1) - 3.5) < 0.3 && Math.abs(dz1) < 0.5;
      reset(); a = at(); dbl({ x: 1, y: 0 }); b = at();                  // ضمن الكول داون (1.8 ثانية): ما يشتغل
      const blocked = Math.hypot(b.x - a.x, b.z - a.z) < 0.5;
      advance(60); reset(); a = at(); dbl({ x: 0, y: -1 }); b = at();
      const back = Math.abs(b.z - a.z + 3.5) < 0.3 && Math.abs(b.x - a.x) < 0.5;     // خلف = عكس اتجاه البصر (+z)
      advance(60);
      // معايرة: جهاز x موجب عنده = يمين (السرعة تبين يمين لما x موجب)
      reset(); player._vel = { x: -0.2, y: 0, z: 0 }; tap({ x: 1, y: 0 }, 14); player._vel = { x: 0, y: 0, z: 0 }; idle(40);
      reset(); a = at(); dbl({ x: 1, y: 0 }); b = at();
      const calibrated = b.x - a.x < -3.2;                                // يمين (نسبة للبصر +z) = -x
      player._mv = { x: 0, y: 0 };
      // الكول داون حسب الرتبة: Trainee ثانيتين (40 تك)، Master 0.9 ثانية (18 تك).
      // الداش الأول يبدأ بالضغطة الثانية ويبقى بعده 12 تك؛ الضغطة السريعة (تك، تك، تك) ضغطتها الثانية بالتك 3 → الفاصل = 12 + انتظار + 3
      const quick = (v) => { tap(v, 1); idle(1); tap(v, 1); idle(10); };
      const cdTry = (rank, wait) => { setState({ ...baseState("star"), rank }); advance(80); reset(); dbl({ x: 1, y: 0 }); advance(wait); reset(); const p0 = at(); quick({ x: 1, y: 0 }); const p1 = at(); return Math.hypot(p1.x - p0.x, p1.z - p0.z) > 2.5; };
      const tr1 = cdTry(1, 20), tr2 = cdTry(1, 26), cm1 = cdTry(4, 0);
      // Legend/Master: شحنتين (داشين ورا بعض، الثالث ممنوع لحد ما ترجع شحنة)
      const mTry = () => {                                               // 3 داشات سريعة (كل 7 تكات): الأول والثاني يشتغلون، الثالث (قبل 18 تك) ممنوع
        setState({ ...baseState("star"), rank: 6 }); advance(80);
        const fast = () => { reset(); const p0 = at(); tap({ x: 1, y: 0 }, 1); idle(1); tap({ x: 1, y: 0 }, 1); idle(4); const p1 = at(); return Math.hypot(p1.x - p0.x, p1.z - p0.z) > 2.5; };
        const first = fast(), second = fast(), third = fast();
        advance(40); const after = fast();
        return { second: first && second, third, after };
      };
      const mt = mTry();
      const cdOk = !tr1 && tr2 && !cm1 && mt.second && !mt.third && mt.after;
      console.log(`  الكول داون بالرتبة: Trainee (35 تك ممنوع ${tr1 ? "✖" : "✔"}، 41 تك يشتغل ${tr2 ? "✔" : "✖"}) | Commander شحنة وحدة (فوراً ممنوع ${cm1 ? "✖" : "✔"}) | Master شحنتين (الثاني فوراً ${mt.second ? "✔" : "✖"}، الثالث ممنوع ${mt.third ? "✖" : "✔"}، وبعد الكول داون يرجع ${mt.after ? "✔" : "✖"})`);
      if (!cdOk) failures.push("كول داون الداش حسب الرتبة (أو الشحنتين) غلط");
      // حصانة لحظية وقت الداش + مؤشر الشحنات باللوحة (فاتح جاهز، غامق يشحن)
      setState({ ...baseState("star"), rank: 2 }); advance(80); reset();
      const res0 = (stats.effects || {}).resistance || 0;
      advance(5); const readyGlyph = (stats.top || "").includes("\uE53F");
      dbl({ x: 1, y: 0 }); const iframes = ((stats.effects || {}).resistance || 0) > res0;
      advance(5); const cdGlyph = (stats.top || "").includes("\uE52F") && !(stats.top || "").includes("\uE53F");
      console.log(`  حصانة وقت الداش ${iframes ? "✔" : "✖"} | مؤشر باللوحة: جاهز ${readyGlyph ? "✔" : "✖"} ← يشحن ${cdGlyph ? "✔" : "✖"}`);
      if (!iframes || !readyGlyph || !cdGlyph) failures.push("حصانة الداش أو مؤشره باللوحة ما يشتغل");
      // دائم: حتى لو رجعت الرتبة 0 (مثلاً ريسيت) يبقى الداش
      setState({ ...baseState("star"), rank: 0 }); advance(60); reset(); a = at(); dbl({ x: 0, y: -1 }); b = at();
      const forever = Math.abs(b.z - a.z + 3.5) < 0.3;
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
    // ═══ v1.42: مدينة Aetheria: موقع واحد بعيد، 16 مربع كل واحد مرة، الشخصيات بأماكنها بدون تكرار، ومحمية من وحوش المود ═══
    {
      const flush = () => new Promise((r) => setImmediate(r));
      const S = () => { const r = world._dyn.sh_city; return typeof r === "string" ? JSON.parse(r) : undefined; };
      player.location = { x: 0, y: 64, z: 0 };
      globalThis.__cityGo = true; for (const r of globalThis.__pendingAreas || []) r();
      let guard = 0;
      while ((!S() || S().st !== "built") && guard < 60000) { advance(10); guard += 10; await flush(); await flush(); }
      const s = S();
      const ok = !!s && s.st === "built";
      const dist = s ? Math.hypot(s.ox + 124, s.oz + 124) : 0;
      const plc = stats.placements || [];
      const tilesOk = s && s.done === 0xffff && plc.length === 16 && new Set(plc.map((q) => `${q.x},${q.z}`)).size === 16;
      const layers = plc.every((q) => q.opts && q.opts.animationMode === "Layers" && q.opts.includeEntities === false);
      const clean = world.tickingAreaManager._areas.size === 0 && world.structureManager._reg.size === 0;
      const T = stats.spawnedTypes || {};
      const npc = { guard: T["sh:city_guard"] || 0, king: T["sh:aetheria_king"] || 0, woman: T["sh:townswoman"] || 0, man: T["sh:townsman"] || 0 };
      console.log(`\nمدينة Aetheria: انبنت ${ok ? "✔" : "✖"} بعد ${guard} تك | البعد عن البداية ${Math.round(dist)} (1900..2400 ${dist >= 1880 && dist <= 2420 ? "✔" : "✖"}) | y0=${s && s.y0}`);
      console.log(`  16 مربع كل واحد مرة ${tilesOk ? "✔" : "✖"} (وضعات ${plc.length}) | حركة طبقات بدون كيانات ${layers ? "✔" : "✖"} | مناطق التكتك والبنايات انشالت ${clean ? "✔" : "✖"} (أكثر وقت ${stats.areaMax} منطقة) | أكبر fillBlocks ${stats.fillMax} (≤ 32768 ${stats.fillMax <= 32768 ? "✔" : "✖"}) | كتابة مباشرة (احتياط) ${stats.farWrites || 0}`);
      console.log(`  الشخصيات: حراس ${npc.guard}، الملك ${npc.king}، امرأة ${npc.woman}، رجل ${npc.man} | صناديق انعبت: ${(stats.chestItems || []).length} غرض`);
      if (!ok) failures.push("مدينة Aetheria ما خلصت بالمحاكي");
      if (!(dist >= 1880 && dist <= 2420)) failures.push(`المدينة مو بعيدة صح عن البداية (${Math.round(dist)})`);
      if (!tilesOk) failures.push("مربعات المدينة ما انحطت كلها مرة وحدة");
      if (!layers) failures.push("وضع البنية مو بحركة طبقات أو بيه كيانات");
      if (!clean) failures.push("بقت مناطق تكتك أو بنايات بالذاكرة بعد البناء");
      if (!(stats.fillMax <= 32768)) failures.push("fillBlocks أكبر من الحد");
      const want = (S().posts || []).reduce((o, [t]) => ((o[t] = (o[t] || 0) + 1), o), {});
      if (npc.guard !== want.guard || npc.king !== 1 || npc.woman !== 1 || npc.man !== 1 || npc.guard < 12) failures.push(`عدد شخصيات المدينة غلط ${JSON.stringify(npc)} (المفروض ${JSON.stringify(want)})`);
      if (stats.farWrites) failures.push(`بنية مربع ما انحطت (انكتب احتياط ${stats.farWrites} بلوكة)`);
      if (!(stats.chestItems || []).length) failures.push("صناديق المدينة فاضية");
      // مرة وحدة: بعد ما تخلص ما ينختار موقع ثاني ولا تنحط بنية ثانية
      const p0 = plc.length, site0 = JSON.stringify([s.ox, s.oz]);
      for (let i = 0; i < 300; i++) { advance(10); await flush(); }
      const once = (stats.placements || []).length === p0 && JSON.stringify([S().ox, S().oz]) === site0;
      // الصيانة: الشخصيات موجودة = ما ينضاف شي؛ حارس واحد ينقتل = يرجع واحد بس (بعد 3 دقايق وبعيد عن عين اللاعب)
      entities.length = 0;
      const posts = S().posts || [];
      posts.forEach(([type, x, y, z], k) => { const e = mkEntity({ guard: "sh:city_guard", king: "sh:aetheria_king", woman: "sh:townswoman", man: "sh:townsman" }[type], { x: s.ox + x + 0.5, y: s.y0 + y, z: s.oz + z + 0.5 }, dims.overworld, 20); e.addTag("sh_city"); e.addTag(`sh_post_${k}`); entities.push(e); });
      player.location = { x: s.ox + 124, y: s.y0, z: s.oz + 124 };
      const before = { ...(stats.spawnedTypes || {}) };
      const cityN = (o) => ["sh:city_guard", "sh:aetheria_king", "sh:townswoman", "sh:townsman"].map((k) => o[k] || 0).join(",");
      for (let i = 0; i < 500; i++) { advance(10); await flush(); }
      const noDup = cityN(stats.spawnedTypes) === cityN(before);
      const far = posts.findIndex(([t, x, y, z]) => t === "guard" && Math.hypot(x - 124, z - 124) > 60);
      const victim = entities.find((e) => e.hasTag(`sh_post_${far}`)); if (victim) victim._valid = false;
      for (let i = 0; i < 450; i++) { advance(10); await flush(); }
      const back = (stats.spawnedTypes["sh:city_guard"] || 0) - (before["sh:city_guard"] || 0);
      // وحوش المود ما تطلع حول لاعب جوه المدينة
      const mon0 = Object.entries(stats.spawnedTypes).filter(([k]) => /^sh:(ember_imp|rust_guard|shadow_hound|sand_scorpion|gloomhorn|hollow_seer|veilfox|magmamoth|grey_bear|prayer_mantis|hollow_harvester)$/.test(k)).reduce((a, [, v]) => a + v, 0);
      for (let i = 0; i < 400; i++) { advance(10); await flush(); }
      const mon1 = Object.entries(stats.spawnedTypes).filter(([k]) => /^sh:(ember_imp|rust_guard|shadow_hound|sand_scorpion|gloomhorn|hollow_seer|veilfox|magmamoth|grey_bear|prayer_mantis|hollow_harvester)$/.test(k)).reduce((a, [, v]) => a + v, 0);
      const welcome = stats.messages.some((m) => /You reached .*Aetheria/.test(m));
      const news = stats.messages.filter((m) => /Travellers speak of .*Aetheria/.test(m)).length;
      if (news !== 1) failures.push(`خبر المدينة لازم يطلع مرة وحدة لما تكمل (طلع ${news})`);
      console.log(`  مرة وحدة بالعالم ${once ? "✔" : "✖"} | ما تتكرر الشخصيات ${noDup ? "✔" : "✖"} | الحارس الميت يرجع واحد ${back === 1 ? "✔" : "✖"} (${back}) | وحوش المود جوه المدينة ${mon1 - mon0} ${mon1 === mon0 ? "✔" : "✖"} | ترحيب ${welcome ? "✔" : "✖"}`);
      if (!once) failures.push("المدينة انبنت أكثر من مرة أو تغير موقعها");
      if (!noDup) failures.push("شخصيات المدينة تكررت");
      if (back !== 1) failures.push(`الحارس الميت ما رجع واحد بالضبط (${back})`);
      if (mon1 !== mon0) failures.push("وحوش المود طلعت جوه المدينة");
      if (!welcome) failures.push("ترحيب المدينة ما طلع");
      entities.length = 0; player.location = { x: 0, y: 64, z: 0 };
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
