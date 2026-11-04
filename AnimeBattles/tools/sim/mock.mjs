// Minimal fake of @minecraft/server, enough to run Anime Battles' logic headless.
export const EntityDamageCause = { magic: "magic", override: "override", fall: "fall", entityAttack: "entityAttack" };
export const EquipmentSlot = { Mainhand: "Mainhand" };
export class ItemStack { constructor(typeId, amount) { this.typeId = typeId; this.amount = amount; } }
export class MolangVariableMap {
  constructor() { this.v = {}; }
  setColorRGB(n, c) { if (![c.red, c.green, c.blue].every((x) => typeof x === "number")) throw new Error("bad color " + n); this.v[n] = c; }
  setFloat(n, x) { if (typeof x !== "number" || Number.isNaN(x)) throw new Error("bad float " + n + "=" + x); this.v[n] = x; }
}

export const stats = { particles: {}, sounds: 0, carved: 0, damage: [], events: [], errors: [] };
let tick = 0;
const timers = [];
let nextId = 1;
export const system = {
  get currentTick() { return tick; },
  runInterval(fn, every = 1) { const id = nextId++; timers.push({ id, fn, every, at: tick + every, repeat: true }); return id; },
  runTimeout(fn, delay = 1) { const id = nextId++; timers.push({ id, fn, every: delay, at: tick + delay, repeat: false }); return id; },
  run(fn) { return this.runTimeout(fn, 1); },
  clearRun(id) { const i = timers.findIndex((t) => t.id === id); if (i >= 0) timers.splice(i, 1); },
  afterEvents: { scriptEventReceive: { subscribe() {} } },
};
export function step() {
  tick++;
  for (const t of [...timers]) {
    if (t.at > tick || !timers.includes(t)) continue;
    if (t.repeat) t.at += t.every; else system.clearRun(t.id);
    t.fn();
  }
}

const handlers = {};
const signal = (name) => ({ subscribe(fn) { (handlers[name] ??= []).push(fn); return fn; } });
const dyn = {};
const entities = [];
const blocks = new Map(); // "x,y,z" -> typeId (default: stone below y=0, air above)
const blockAt = (x, y, z) => blocks.get(`${x},${y},${z}`) ?? (y < 0 ? "minecraft:stone" : "minecraft:air");

class Dim {
  constructor(id) { this.id = id; }
  getEntities(o = {}) {
    return entities.filter((e) => e.isValid && e.dimension === this &&
      (!o.families || o.families.every((f) => e.families.includes(f))) &&
      (!o.excludeFamilies || !o.excludeFamilies.some((f) => e.families.includes(f))) &&
      (!o.tags || o.tags.every((t) => e.tags.has(t))) && (!o.type || e.typeId === o.type) &&
      (!o.location || Math.hypot(e.location.x - o.location.x, e.location.y - o.location.y, e.location.z - o.location.z) <= o.maxDistance));
  }
  getPlayers(o) { return this.getEntities(o).filter((e) => e.typeId === "minecraft:player"); }
  spawnParticle(id, loc, m) {
    if (!["ab:orb", "ab:orb_solid", "ab:burst", "ab:aura", "ab:streak", "ab:shock", "ab:shock_v", "ab:flash"].includes(id)) throw new Error("unknown particle " + id);
    for (const k of ["variable.color", "variable.size", "variable.life"]) if (!(k in m.v)) throw new Error("missing var " + k);
    if (![loc.x, loc.y, loc.z].every(Number.isFinite)) throw new Error("bad particle loc");
    stats.particles[id] = (stats.particles[id] ?? 0) + 1;
  }
  playSound() { stats.sounds++; }
  runCommand(c) { stats.cmds = (stats.cmds ?? 0) + 1; return { successCount: 1 }; }
  spawnEntity(id, loc) {
    if (id !== "ab:vfx") throw new Error("unexpected spawn " + id);
    const e = new Entity(id, loc, { families: ["ab_vfx"], hp: 1 });
    e.dimension = this; stats.vfx = (stats.vfx ?? 0) + 1; return e;
  }
  getBlock(p) {
    const self = this;
    return {
      get typeId() { return blockAt(p.x, p.y, p.z); },
      get isAir() { return blockAt(p.x, p.y, p.z) === "minecraft:air"; },
      isLiquid: false,
      setType(t) { blocks.set(`${p.x},${p.y},${p.z}`, t); stats.carved++; void self; },
    };
  }
}
const dims = { overworld: new Dim("overworld"), nether: new Dim("nether"), the_end: new Dim("the_end") };

export class Entity {
  constructor(typeId, loc, opts = {}) {
    this.id = String(nextId++);
    this.typeId = typeId;
    this.location = { ...loc };
    this.dimension = dims.overworld;
    this.families = opts.families ?? [];
    this.tags = new Set();
    this.props = { "ab:form": 0, "ab:pose": 0 };
    this.maxHp = opts.hp ?? 20;
    this.hp = this.maxHp;
    this.isValid = true;
    this.nameTag = "";
    this.isSneaking = false;
    this.held = opts.held;
    this.groups = new Set(["ab:form_0"]);
    this.effects = {};
    this.name = opts.name ?? typeId;
    this.onScreenDisplay = { setActionBar: (t) => { this.actionbar = t; } };
    entities.push(this);
  }
  hasTag(t) { this.#check(); return this.tags.has(t); }
  addTag(t) { this.#check(); this.tags.add(t); return true; }
  removeTag(t) { this.#check(); return this.tags.delete(t); }
  #check() { if (!this.isValid) throw new Error("invalid entity used: " + this.typeId); }
  getComponent(id) {
    this.#check();
    const self = this;
    if (id === "minecraft:health") return {
      get currentValue() { return self.hp; }, get effectiveMax() { return self.maxHp; },
      setCurrentValue(v) { self.hp = v; return true; },
    };
    if (id === "minecraft:equippable") return { getEquipment: () => (self.held ? { typeId: self.held } : undefined) };
    if (id === "minecraft:inventory") return { container: { addItem: (it) => { (self.inv ??= []).push(it.typeId); } } };
    return undefined;
  }
  getProperty(k) { this.#check(); return this.props[k]; }
  setProperty(k, v) {
    this.#check();
    const R = { "ab:pose": [0, 12], "ab:kind": [0, 1], "ab:color": [0, 10], "ab:len": [0, 80], "ab:size": [0, 40], "ab:pitch": [-90, 90] }[k];
    if (R && (typeof v !== "number" || Number.isNaN(v) || v < R[0] || v > R[1])) throw new Error(`property ${k} out of range: ${v}`);
    this.props[k] = v;
  }
  triggerEvent(ev) {
    this.#check();
    stats.events.push(`${this.typeId} ${ev}`);
    const m = /^ab:form_(\d)$/.exec(ev);
    if (m) this.props["ab:form"] = Number(m[1]);
  }
  getHeadLocation() { return { x: this.location.x, y: this.location.y + 1.6, z: this.location.z }; }
  getViewDirection() { return { x: 0, y: 0, z: 1 }; }
  teleport(loc, o) { this.#check(); if (![loc.x, loc.y, loc.z].every(Number.isFinite)) throw new Error("bad tp"); this.location = { ...loc }; void o; }
  tryTeleport(loc, o) { this.teleport(loc, o); return true; }
  applyKnockback(h, v) { this.#check(); if (!Number.isFinite(h.x) || !Number.isFinite(h.z) || !Number.isFinite(v)) throw new Error("bad knockback"); }
  applyImpulse(v) { this.#check(); if (this.typeId === "minecraft:player") throw new Error("impulse on player"); this.location.x += v.x; this.location.z += v.z; }
  addEffect(t, d, o) { this.#check(); if (!Number.isFinite(d)) throw new Error("bad effect duration"); this.effects[t] = d; void o; }
  applyDamage(amount, opts) {
    this.#check();
    if (!Number.isFinite(amount)) throw new Error("bad damage " + amount);
    const ev = { hurtEntity: this, damage: amount, cancel: false, damageSource: { cause: opts?.cause, damagingEntity: opts?.damagingEntity } };
    for (const h of handlers.beforeHurt ?? []) h(ev);
    if (ev.cancel) return false;
    this.hp -= ev.damage;
    stats.damage.push({ from: opts?.damagingEntity?.typeId ?? "-", to: this.typeId, amount: ev.damage });
    if (this.hp <= 0) this.die();
    return true;
  }
  kill() { const ev = { hurtEntity: this, damage: 9999, cancel: false, damageSource: { cause: "selfDestruct" } };
    for (const h of handlers.beforeHurt ?? []) h(ev);
    if (!ev.cancel) this.die(); return !ev.cancel; }
  die() { if (!this.isValid) return; this.hp = 0; for (const h of handlers.die ?? []) h({ deadEntity: this }); this.isValid = false; }
  remove() { this.isValid = false; }
  setDynamicProperty(k, v) { (this.dyn ??= {})[k] = v; }
  getDynamicProperty(k) { return this.dyn?.[k]; }
  sendMessage(m) { this.lastMsg = m; }
}

export const world = {
  getDimension: (id) => dims[id],
  getDynamicProperty: (k) => dyn[k],
  setDynamicProperty: (k, v) => { dyn[k] = v; },
  afterEvents: {
    entityHitEntity: signal("hit"), entityDie: signal("die"), entityRemove: signal("remove"),
    playerSpawn: signal("spawn"), itemUse: signal("use"),
  },
  beforeEvents: { entityHurt: signal("beforeHurt") },
};
export const fire = (name, ev) => { for (const h of handlers[name] ?? []) h(ev); };
export const allEntities = entities;
