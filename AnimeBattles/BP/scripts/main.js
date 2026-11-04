// Anime Battles — Goku, Vegeta, Gojo
// Team Stick: hit = red, next hit = blue (alternates). Use = switch next team. Sneak + use = reset all teams.
// Kill Stick: hit = instant permanent kill (any mob, even the Warden). Use = toggle block damage. Sneak + use = effects quality.
import { world, system, MolangVariableMap, EntityDamageCause, EquipmentSlot, ItemStack } from "@minecraft/server";

// ------------------------------------------------------------------ settings
const RED = "ab_red";
const BLUE = "ab_blue";
const FIGHTER_FAMILY = "anime_fighter";
const DIMENSIONS = ["overworld", "nether", "the_end"];
const UNBREAKABLE = new Set([
  "minecraft:bedrock", "minecraft:barrier", "minecraft:command_block", "minecraft:chain_command_block",
  "minecraft:repeating_command_block", "minecraft:structure_block", "minecraft:jigsaw", "minecraft:end_portal_frame",
  "minecraft:end_portal", "minecraft:portal", "minecraft:light_block", "minecraft:allow", "minecraft:deny", "minecraft:border_block",
]);
const IGNORE_TYPES = new Set(["minecraft:item", "minecraft:xp_orb", "minecraft:arrow", "minecraft:armor_stand", "minecraft:painting",
  "minecraft:leash_knot", "minecraft:fishing_hook", "minecraft:falling_block", "minecraft:tnt", "minecraft:boat", "minecraft:minecart"]);

function setting(key, fallback) {
  const v = world.getDynamicProperty(key);
  return v === undefined ? fallback : v;
}
const griefing = () => setting("ab:griefing", true);
const fxLevel = () => setting("ab:fx", 1); // 1 = full, 0.5 = low (for weaker phones)

// ------------------------------------------------------------------ math
const V = {
  add: (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z }),
  sub: (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }),
  mul: (a, s) => ({ x: a.x * s, y: a.y * s, z: a.z * s }),
  len: (a) => Math.hypot(a.x, a.y, a.z),
  dist: (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z),
  norm(a) { const l = Math.hypot(a.x, a.y, a.z) || 1; return { x: a.x / l, y: a.y / l, z: a.z / l }; },
  up: (a, y) => ({ x: a.x, y: a.y + y, z: a.z }),
  randSphere() {
    const u = Math.random() * 2 - 1, t = Math.random() * Math.PI * 2, s = Math.sqrt(1 - u * u);
    return { x: s * Math.cos(t), y: u, z: s * Math.sin(t) };
  },
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const now = () => system.currentTick;

const warned = new Set();
function warn(tag, e) {
  if (warned.has(tag)) return;
  warned.add(tag);
  console.warn(`[AnimeBattles] ${tag}: ${e}`);
}
function later(ticks, fn) {
  system.runTimeout(() => { try { fn(); } catch (e) { warn("later", e); } }, Math.max(1, Math.round(ticks)));
}
function every(ticks, count, fn) {
  let i = 0;
  const id = system.runInterval(() => {
    try {
      if (fn(i) === false || ++i >= count) system.clearRun(id);
    } catch (e) { warn("every", e); system.clearRun(id); }
  }, ticks);
}

// ------------------------------------------------------------------ colours
const C = {
  white: { red: 1, green: 1, blue: 1 },
  kiYellow: { red: 1, green: 0.93, blue: 0.55 },
  kameBlue: { red: 0.35, green: 0.75, blue: 1 },
  gold: { red: 1, green: 0.85, blue: 0.2 },
  ssbBlue: { red: 0.2, green: 0.7, blue: 1 },
  silver: { red: 0.85, green: 0.88, blue: 1 },
  kaioken: { red: 1, green: 0.15, blue: 0.1 },
  galick: { red: 0.75, green: 0.3, blue: 1 },
  bigBang: { red: 0.6, green: 0.85, blue: 1 },
  flash: { red: 1, green: 0.95, blue: 0.4 },
  ego: { red: 0.75, green: 0.2, blue: 0.95 },
  hakai: { red: 0.45, green: 0.05, blue: 0.6 },
  blue: { red: 0.15, green: 0.45, blue: 1 },
  red: { red: 1, green: 0.12, blue: 0.12 },
  purple: { red: 0.7, green: 0.2, blue: 1 },
  void: { red: 0.04, green: 0.04, blue: 0.1 },
  black: { red: 0.02, green: 0.02, blue: 0.02 },
  heal: { red: 0.6, green: 1, blue: 0.8 },
  team: { [RED]: { red: 1, green: 0.2, blue: 0.2 }, [BLUE]: { red: 0.2, green: 0.45, blue: 1 } },
};

// ------------------------------------------------------------------ effects
function fx(dim, kind, loc, color, size, life, extra) {
  try {
    const m = new MolangVariableMap();
    m.setColorRGB("variable.color", color);
    m.setFloat("variable.size", size);
    m.setFloat("variable.life", life);
    m.setFloat("variable.count", extra?.count ?? 1);
    m.setFloat("variable.speed", extra?.speed ?? 0);
    m.setFloat("variable.radius", extra?.radius ?? 0);
    dim.spawnParticle(`ab:${kind}`, loc, m);
  } catch (e) { /* chunk not loaded or particle missing */ }
}
function sound(dim, id, loc, volume = 1, pitch = 1) {
  try { dim.playSound(id, loc, { volume, pitch }); } catch (e) { /* ignore */ }
}
function burst(dim, loc, color, count, speed, size = 0.35, life = 0.6) {
  fx(dim, "burst", loc, color, size, life, { count: Math.ceil(count * fxLevel()), speed, radius: 0.2 });
}
function implode(dim, loc, color, radius, count) {
  fx(dim, "burst", loc, color, 0.3, 0.5, { count: Math.ceil(count * fxLevel()), speed: -radius * 2, radius });
}
function ring(dim, center, radius, color, points = 16, size = 0.3) {
  const n = Math.ceil(points * fxLevel());
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    fx(dim, "orb", { x: center.x + Math.cos(a) * radius, y: center.y, z: center.z + Math.sin(a) * radius }, color, size, 0.5);
  }
}
function sphereFx(dim, center, radius, color, points, size, kind = "orb", life = 0.4) {
  const n = Math.ceil(points * fxLevel());
  for (let i = 0; i < n; i++) fx(dim, kind, V.add(center, V.mul(V.randSphere(), radius)), color, size, life);
}

// ------------------------------------------------------------------ entity helpers
function alive(e) {
  try {
    if (!e || !e.isValid) return false;
    const h = e.getComponent("minecraft:health");
    return !h || h.currentValue > 0;
  } catch (e2) { return false; }
}
function health(e) {
  try { return e.getComponent("minecraft:health"); } catch (e2) { return undefined; }
}
function hpPct(e) {
  const h = health(e);
  return h ? h.currentValue / h.effectiveMax : 1;
}
function teamOf(e) {
  try {
    if (e.hasTag(RED)) return RED;
    if (e.hasTag(BLUE)) return BLUE;
  } catch (e2) { /* invalid */ }
  return undefined;
}
const enemyOf = (team) => (team === RED ? BLUE : RED);
const isFighter = (e) => !!FIGHTERS[e.typeId];
function aim(e) { return V.up(e.location, 1.0); }
function face(e, loc) {
  try { e.teleport(e.location, { facingLocation: loc }); } catch (e2) { /* ignore */ }
}
function setPose(e, pose) {
  try { e.setProperty("ab:pose", pose); } catch (e2) { /* ignore */ }
}
function formOf(e) {
  try { return e.getProperty("ab:form") ?? 0; } catch (e2) { return 0; }
}
function handPos(e, target) {
  const head = e.getHeadLocation();
  const dir = V.norm(V.sub(aim(target), head));
  return { pos: V.add(V.add(head, V.mul(dir, 0.9)), { x: 0, y: -0.45, z: 0 }), dir };
}
function sideOf(dir) { return V.norm({ x: -dir.z, y: 0, z: dir.x }); }
function slow(e, ticks, amp = 4) {
  try { e.addEffect("slowness", Math.max(1, ticks), { amplifier: amp, showParticles: false }); } catch (e2) { /* ignore */ }
}
function nearbyPlayers(dim, loc, r = 64) {
  try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch (e) { return []; }
}
function announce(e, text) {
  for (const p of nearbyPlayers(e.dimension, e.location)) {
    try { p.onScreenDisplay.setActionBar(text); } catch (e2) { /* ignore */ }
  }
}
function prettyType(id) {
  return id.replace(/^.*:/, "").split("_").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
}

function nearestEnemy(e, team, range) {
  let best, bestD = range;
  let list = [];
  try { list = e.dimension.getEntities({ location: e.location, maxDistance: range, tags: [enemyOf(team)] }); } catch (err) { return undefined; }
  for (const o of list) {
    if (o.id === e.id || !alive(o)) continue;
    const d = V.dist(o.location, e.location);
    if (d < bestD) { bestD = d; best = o; }
  }
  return best;
}

// Who can be hit by an ability from `src`: enemies, and un-teamed mobs caught in the blast.
// Players are only hit when they joined a team. Allies are never hit.
function canHit(src, srcTeam, o) {
  if (!o.isValid || o.id === src.id || IGNORE_TYPES.has(o.typeId)) return false;
  const t = teamOf(o);
  if (t && t === srcTeam) return false;
  if (o.typeId === "minecraft:player" && !t) return false;
  return alive(o);
}

// ------------------------------------------------------------------ fighter state
const states = new Map();
function state(e) {
  let s = states.get(e.id);
  if (!s) {
    const def = FIGHTERS[e.typeId];
    s = {
      energy: def ? def.energy : 0, cd: {}, busyUntil: 0, stunUntil: 0, burnoutUntil: 0,
      infinityBrokenUntil: 0, kaiokenUntil: 0, ego: 0, nextTransform: 0, combatSince: 0, lastCombat: 0, meleeCd: 0,
    };
    states.set(e.id, s);
  }
  return s;
}

function powerOf(e) {
  const def = FIGHTERS[e.typeId];
  if (def) {
    const s = state(e);
    const f = def.forms[clamp(formOf(e), 0, def.forms.length - 1)];
    let p = f.power;
    if (s.kaiokenUntil > now()) p *= 1.5;
    p *= 1 + s.ego;
    return p;
  }
  const h = health(e);
  return h ? Math.max(5, Math.sqrt(h.effectiveMax) * 3) : 5;
}

// ------------------------------------------------------------------ damage
// cause "override" is used for sure-hit damage (Domain Expansion) that Infinity and dodging cannot stop.
function deal(src, v, amount, sureHit = false) {
  if (!alive(v) || amount <= 0) return;
  try {
    const opts = { cause: sureHit ? EntityDamageCause.override : EntityDamageCause.magic };
    if (src && src.isValid) opts.damagingEntity = src;
    v.applyDamage(amount, opts);
  } catch (e) { warn("deal", e); }
}
function hitArea(src, center, radius, dmg, hitSet, opt = {}) {
  const team = teamOf(src);
  let list = [];
  try { list = src.dimension.getEntities({ location: center, maxDistance: radius }); } catch (e) { return 0; }
  let n = 0;
  for (const o of list) {
    if (hitSet && hitSet.has(o.id)) continue;
    if (!canHit(src, team, o)) continue;
    hitSet?.add(o.id);
    deal(src, o, dmg, opt.sureHit);
    if (opt.knock) {
      const d = V.norm(V.sub(o.location, center));
      try { o.applyKnockback({ x: d.x * opt.knock, z: d.z * opt.knock }, opt.lift ?? 0.4); } catch (e) { /* ignore */ }
    }
    n++;
  }
  return n;
}
function carve(dim, center, r, budget = 160) {
  if (!griefing() || r <= 0) return;
  const R = Math.ceil(r), r2 = r * r;
  let n = 0;
  for (let x = -R; x <= R; x++) for (let y = -R; y <= R; y++) for (let z = -R; z <= R; z++) {
    if (x * x + y * y + z * z > r2) continue;
    try {
      const b = dim.getBlock({ x: Math.floor(center.x + x), y: Math.floor(center.y + y), z: Math.floor(center.z + z) });
      if (!b || b.isAir || b.isLiquid || UNBREAKABLE.has(b.typeId)) continue;
      b.setType("minecraft:air");
      if (++n >= budget) return;
    } catch (e) { /* unloaded */ }
  }
}
function solidAt(dim, p) {
  try {
    const b = dim.getBlock({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) });
    return !!b && !b.isAir && !b.isLiquid;
  } catch (e) { return false; }
}
function explosion(src, pos, o) {
  const dim = src.dimension;
  burst(dim, pos, o.color, 26 + o.radius * 6, o.radius * 3, 0.5 + o.radius * 0.08, 0.8);
  burst(dim, pos, C.white, 10 + o.radius * 2, o.radius * 1.5, 0.4, 0.5);
  sphereFx(dim, pos, o.radius * 0.6, o.color, 10 + o.radius * 3, 0.9, "orb", 0.5);
  sound(dim, "random.explode", pos, 1 + o.radius * 0.3, o.radius > 4 ? 0.6 : 0.9);
  hitArea(src, pos, o.radius, o.dmg, new Set(), { knock: o.knock ?? 1.2, lift: 0.45 });
  carve(dim, pos, o.carve ?? 0);
}

// A beam that grows from the caster toward the target, hitting everything along it once.
function beam(src, target, o) {
  const dim = src.dimension;
  const { pos: start, dir } = handPos(src, target);
  const hit = new Set();
  const len = o.length ?? 45, steps = o.ticks ?? 8, grow = len / steps;
  let reach = 0, ended = false, carved = 0;
  sound(dim, o.sound ?? "mob.wither.shoot", start, 2, o.pitch ?? 0.8);
  const spacing = 0.5 / fxLevel();
  const id = system.runInterval(() => {
    try {
      if (!src.isValid || ended) { system.clearRun(id); return; }
      const prev = reach;
      reach = Math.min(len, reach + grow);
      for (let s = prev; s <= reach; s += spacing) {
        const p = V.add(start, V.mul(dir, s));
        if (!griefing() && solidAt(dim, p)) { reach = s; ended = true; break; }
        fx(dim, "orb", p, C.white, o.width * 0.7, 0.5);
        fx(dim, "orb", p, o.color, o.width * 1.6, 0.6);
      }
      for (let s = 0; s < prev; s += 1.6) fx(dim, "orb", V.add(start, V.mul(dir, s)), o.color, o.width * 1.5, 0.35);
      for (let s = prev; s <= reach; s += 1) {
        const p = V.add(start, V.mul(dir, s));
        hitArea(src, p, o.width * 0.8 + 0.7, o.dmg, hit, { knock: 0.8, lift: 0.2 });
        if (o.carve && carved < 600 && Math.floor(s) % 2 === 0) { carve(dim, p, o.carve, 40); carved += 20; }
      }
      if (reach >= len || ended) {
        ended = true;
        system.clearRun(id);
        const tip = V.add(start, V.mul(dir, reach));
        explosion(src, tip, { radius: o.blast ?? 2.5, dmg: o.dmg * 0.35, color: o.color, carve: o.carve ? o.carve + 1 : 0 });
      }
    } catch (e) { warn("beam", e); system.clearRun(id); }
  }, 1);
}

// A moving energy ball. Pierce = keeps going through everything (Hollow Purple).
function projectile(src, start, dir, o) {
  const dim = src.dimension;
  let pos = start, travelled = 0, done = false;
  const hit = new Set();
  const team = teamOf(src);
  const sub = Math.max(1, Math.ceil(o.speed));
  const id = system.runInterval(() => {
    try {
      if (done || !src.isValid) { system.clearRun(id); return; }
      if (o.homing && alive(o.homing)) dir = V.norm(V.add(dir, V.mul(V.norm(V.sub(aim(o.homing), pos)), o.homingStrength ?? 0.08)));
      for (let i = 0; i < sub && !done; i++) {
        pos = V.add(pos, V.mul(dir, o.speed / sub));
        travelled += o.speed / sub;
        fx(dim, o.solid ? "orb_solid" : "orb", pos, o.color, o.size, 0.25);
        if (o.core) fx(dim, "orb", pos, o.core, o.size * 0.55, 0.2);
        if (o.trail && i === 0) fx(dim, "orb", pos, o.color, o.size * 0.6, 0.6);
        if (o.pierce) {
          hitArea(src, pos, o.radius, o.dmg, hit, { knock: 0.6 });
          if (o.carve) carve(dim, pos, o.carve, 90);
        } else {
          let list = [];
          try { list = dim.getEntities({ location: pos, maxDistance: o.radius }); } catch (e) { /* ignore */ }
          const struck = list.some((x) => canHit(src, team, x));
          if (struck || solidAt(dim, pos)) done = true;
        }
        if (travelled >= o.maxDist) done = true;
      }
      if (done) {
        system.clearRun(id);
        if (o.explode) explosion(src, pos, o.explode);
        o.onEnd?.(pos);
      }
    } catch (e) { warn("projectile", e); system.clearRun(id); }
  }, 1);
}

function chargeOrb(src, target, ticks, color, fromSize, toSize, pose) {
  setPose(src, pose);
  slow(src, ticks + 4, 6);
  every(2, Math.ceil(ticks / 2), (i) => {
    if (!src.isValid) return false;
    const t = alive(target) ? target : src;
    const { pos } = handPos(src, t);
    const k = (i * 2) / ticks;
    fx(src.dimension, "orb", pos, C.white, (fromSize + (toSize - fromSize) * k) * 0.6, 0.15);
    fx(src.dimension, "orb", pos, color, fromSize + (toSize - fromSize) * k, 0.15);
    if (i % 3 === 0) implode(src.dimension, pos, color, 2.5, 6);
  });
}
function busy(s, ticks) { s.busyUntil = now() + ticks; }

function teleportNear(src, target, behind = true, dist = 1.6) {
  try {
    let dir;
    try { dir = target.getViewDirection(); } catch (e) { dir = V.norm(V.sub(target.location, src.location)); }
    const flat = V.norm({ x: dir.x, y: 0, z: dir.z });
    const spot = V.add(target.location, V.mul(flat, behind ? -dist : dist));
    burst(src.dimension, V.up(src.location, 1), C.white, 10, 2, 0.3, 0.3);
    if (!src.tryTeleport(spot, { checkForBlocks: true, facingLocation: aim(target) })) {
      src.teleport(V.up(target.location, 0.2), { facingLocation: aim(target) });
    }
    sound(src.dimension, "mob.endermen.portal", spot, 1, 1.6);
    burst(src.dimension, V.up(spot, 1), C.white, 10, 2, 0.3, 0.3);
    return true;
  } catch (e) { return false; }
}
function punches(src, target, count, dmg, color) {
  every(3, count, () => {
    if (!alive(target) || !src.isValid) return false;
    face(src, aim(target));
    deal(src, target, dmg);
    burst(src.dimension, aim(target), color, 8, 3, 0.3, 0.3);
    sound(src.dimension, "random.anvil_land", target.location, 0.4, 1.8);
  });
}

// ------------------------------------------------------------------ transformations
function transform(e, s, to, label, color, extraSound) {
  const dim = e.dimension;
  const def = FIGHTERS[e.typeId];
  busy(s, 32);
  s.nextTransform = now() + 160;
  setPose(e, 3);
  slow(e, 30, 8);
  sound(dim, "ambient.weather.thunder", e.location, 1.5, 1.2);
  every(4, 7, (i) => {
    if (!e.isValid) return false;
    fx(dim, "aura", e.location, color, 1.2, 0.8, { count: 18 * fxLevel(), speed: 2 });
    implode(dim, V.up(e.location, 1), color, 4, 10);
    if (i === 6) {
      try { e.triggerEvent(`ab:form_${to}`); } catch (err) { warn("transform", err); }
      setPose(e, 0);
      burst(dim, V.up(e.location, 1), color, 60, 6, 0.6, 0.9);
      burst(dim, V.up(e.location, 1), C.white, 30, 4, 0.4, 0.6);
      ring(dim, V.up(e.location, 0.1), 3, color, 24, 0.6);
      sound(dim, extraSound ?? "random.explode", e.location, 1.5, 0.7);
      hitArea(e, e.location, 4, 0, null, { knock: 1.5, lift: 0.3 });
      announce(e, `§l${def.color}${def.name} §r§f→ §l${label}`);
    }
  });
}

function aura(e, s, def) {
  const form = formOf(e);
  const c = def.forms[form]?.aura;
  if (s.kaiokenUntil > now()) fx(e.dimension, "aura", e.location, C.kaioken, 1.0, 0.6, { count: 6 * fxLevel(), speed: 1.5 });
  if (c) fx(e.dimension, "aura", e.location, c, 1.0, 0.6, { count: 5 * fxLevel(), speed: 1.5 });
  if (e.typeId === "ab:gojo" && e.hasTag("ab_infinity") && Math.random() < 0.25) {
    fx(e.dimension, "orb", V.add(V.up(e.location, 1), V.mul(V.randSphere(), 0.9)), C.blue, 0.15, 0.4);
  }
}

// ------------------------------------------------------------------ characters
const GOKU = {
  name: "Goku", color: "§6", energy: 1000, regen: 15, energyName: "§bKI",
  dodge: (e, s) => (formOf(e) === 4 ? 0.6 : 0.1),
  forms: [
    { label: "Base", power: 150 },
    { label: "Super Saiyan", power: 200, aura: C.gold },
    { label: "Super Saiyan 3", power: 260, aura: C.gold },
    { label: "Super Saiyan Blue", power: 330, aura: C.ssbBlue },
    { label: "Ultra Instinct", power: 400, aura: C.silver },
  ],
  thresholds: [0.9, 0.7, 0.5, 0.3],
  formSound: [null, "mob.enderdragon.growl", "mob.enderdragon.growl", "beacon.power", "beacon.activate"],
  abilities: [
    {
      id: "ki", label: "Ki Blast", cd: 60, cost: 40, min: 3, max: 32, weight: 3,
      run(e, s, t) {
        busy(s, 12); setPose(e, 4);
        every(2, 5, () => {
          if (!alive(t) || !e.isValid) return false;
          face(e, aim(t));
          const { pos, dir } = handPos(e, t);
          projectile(e, pos, dir, { speed: 1.5, maxDist: 34, radius: 0.9, size: 0.5, color: C.kiYellow, core: C.white,
            explode: { radius: 1.3, dmg: 7 * powerOf(e) / 100, color: C.kiYellow, knock: 0.5 } });
          sound(e.dimension, "mob.blaze.shoot", pos, 0.6, 1.6);
        });
        later(12, () => setPose(e, 0));
      },
    },
    {
      id: "kame", label: "Kamehameha", cd: 240, cost: 220, min: 5, max: 45, weight: 4,
      run(e, s, t) {
        busy(s, 52); face(e, aim(t));
        sound(e.dimension, "beacon.activate", e.location, 1.5, 1.4);
        announce(e, "§bKa... me... ha... me...");
        chargeOrb(e, t, 30, C.kameBlue, 0.3, 1.4, 2);
        later(30, () => {
          if (!e.isValid) return;
          if (alive(t)) face(e, aim(t));
          setPose(e, 1);
          announce(e, "§b§lHAAAAA!");
          const f = formOf(e);
          beam(e, alive(t) ? t : e, { color: C.kameBlue, width: 1.1 + 0.25 * f, dmg: 65 * powerOf(e) / 100, carve: f >= 3 ? 2 : 1, blast: 3 + f * 0.5 });
          later(20, () => setPose(e, 0));
        });
      },
    },
    {
      id: "it", label: "Instant Transmission", cd: 140, cost: 70, min: 8, max: 48, weight: 3,
      run(e, s, t) {
        busy(s, 14);
        if (teleportNear(e, t, true)) punches(e, t, 3, 10 * powerOf(e) / 100, C.kiYellow);
      },
    },
    {
      id: "kaioken", label: "Kaioken", cd: 900, cost: 120, min: 0, max: 48, weight: 2,
      cond: (e, s, c) => (formOf(e) === 0 || formOf(e) === 3) && s.kaiokenUntil < now() && c.tPower >= c.power * 0.85,
      run(e, s) {
        busy(s, 10); s.kaiokenUntil = now() + 240;
        burst(e.dimension, V.up(e.location, 1), C.kaioken, 40, 5, 0.5, 0.7);
        sound(e.dimension, "mob.enderdragon.growl", e.location, 1, 1.4);
        announce(e, formOf(e) === 3 ? "§9Super Saiyan Blue §c§lKaioken!" : "§c§lKaioken!");
      },
    },
    {
      id: "dragonfist", label: "Dragon Fist", cd: 500, cost: 320, min: 2, max: 14, weight: 3,
      cond: (e) => formOf(e) >= 2,
      run(e, s, t) {
        busy(s, 22); setPose(e, 4);
        announce(e, "§6§lDragon Fist!");
        sound(e.dimension, "mob.enderdragon.growl", e.location, 2, 0.8);
        every(1, 6, (i) => {
          if (!alive(t) || !e.isValid) return false;
          const d = V.sub(t.location, e.location);
          const step = V.add(e.location, V.mul(d, 0.35));
          try { e.teleport(step, { facingLocation: aim(t) }); } catch (err) { /* ignore */ }
          const c = V.up(e.location, 1);
          for (let k = 0; k < 6; k++) {
            const a = i * 1.2 + k;
            fx(e.dimension, "orb", V.add(c, { x: Math.cos(a) * 1.2, y: Math.sin(a) * 1.2, z: 0 }), C.gold, 0.7, 0.6);
          }
          if (i === 5) {
            deal(e, t, 130 * powerOf(e) / 100);
            explosion(e, aim(t), { radius: 3, dmg: 30 * powerOf(e) / 100, color: C.gold, carve: 2, knock: 2.5 });
            setPose(e, 0);
          }
        });
      },
    },
    {
      id: "spiritbomb", label: "Spirit Bomb", cd: 1800, cost: 0, min: 6, max: 40, weight: 3,
      cond: (e, s, c) => c.hp < 0.5 && now() - s.combatSince > 200,
      run(e, s, t) {
        busy(s, 100); setPose(e, 3); slow(e, 92, 8);
        announce(e, "§b§lEveryone, lend me your energy!  §f(Spirit Bomb)");
        sound(e.dimension, "beacon.power", e.location, 2, 0.6);
        const ticks = 90;
        every(3, ticks / 3, (i) => {
          if (!e.isValid) return false;
          const r = 0.6 + (2.9 * i * 3) / ticks;
          const c = V.up(e.location, 4 + r);
          sphereFx(e.dimension, c, r, C.kameBlue, 10 + r * 6, 0.8, "orb", 0.3);
          fx(e.dimension, "orb", c, C.white, r * 1.6, 0.2);
          implode(e.dimension, c, C.kameBlue, 10, 8);
        });
        later(ticks, () => {
          if (!e.isValid) return;
          setPose(e, 1);
          const c = V.up(e.location, 7.4);
          const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 10));
          projectile(e, c, V.norm(V.sub(tgt, c)), { speed: 0.55, maxDist: 60, radius: 2.5, size: 6, color: C.kameBlue, core: C.white,
            homing: t, homingStrength: 0.05,
            explode: { radius: 7, dmg: 280, color: C.kameBlue, carve: 4, knock: 3 } });
          later(15, () => setPose(e, 0));
        });
      },
    },
  ],
};

const VEGETA = {
  name: "Vegeta", color: "§9", energy: 1000, regen: 14, energyName: "§bKI",
  dodge: () => 0.08,
  ego: 3,
  forms: [
    { label: "Base", power: 140 },
    { label: "Super Saiyan", power: 190, aura: C.gold },
    { label: "Super Saiyan Blue", power: 310, aura: C.ssbBlue },
    { label: "Ultra Ego", power: 360, aura: C.ego },
  ],
  thresholds: [0.85, 0.6, 0.35],
  formSound: [null, "mob.enderdragon.growl", "beacon.power", "mob.wither.spawn"],
  abilities: [
    {
      id: "barrage", label: "Ki Barrage", cd: 80, cost: 60, min: 3, max: 32, weight: 3,
      run(e, s, t) {
        busy(s, 18); setPose(e, 1);
        every(2, 8, () => {
          if (!alive(t) || !e.isValid) return false;
          face(e, aim(t));
          const { pos, dir } = handPos(e, t);
          const jit = { x: (Math.random() - 0.5) * 0.15, y: (Math.random() - 0.5) * 0.1, z: (Math.random() - 0.5) * 0.15 };
          projectile(e, pos, V.norm(V.add(dir, jit)), { speed: 1.6, maxDist: 34, radius: 0.9, size: 0.5, color: C.kiYellow, core: C.white,
            explode: { radius: 1.3, dmg: 6 * powerOf(e) / 100, color: C.kiYellow, knock: 0.4 } });
          sound(e.dimension, "mob.blaze.shoot", pos, 0.5, 1.7);
        });
        later(18, () => setPose(e, 0));
      },
    },
    {
      id: "galick", label: "Galick Gun", cd: 220, cost: 210, min: 5, max: 45, weight: 4,
      run(e, s, t) {
        busy(s, 44); face(e, aim(t));
        announce(e, "§d§lGalick Gun!");
        chargeOrb(e, t, 22, C.galick, 0.3, 1.2, 2);
        later(22, () => {
          if (!e.isValid) return;
          if (alive(t)) face(e, aim(t));
          setPose(e, 1);
          beam(e, alive(t) ? t : e, { color: C.galick, width: 1.1 + 0.2 * formOf(e), dmg: 62 * powerOf(e) / 100, carve: 1, blast: 3 });
          later(18, () => setPose(e, 0));
        });
      },
    },
    {
      id: "bigbang", label: "Big Bang Attack", cd: 260, cost: 240, min: 4, max: 40, weight: 3,
      run(e, s, t) {
        busy(s, 20); face(e, aim(t)); setPose(e, 4);
        announce(e, "§b§lBig Bang Attack!");
        chargeOrb(e, t, 10, C.bigBang, 0.4, 1.2, 4);
        later(10, () => {
          if (!e.isValid) return;
          const tt = alive(t) ? t : e;
          const { pos, dir } = handPos(e, tt);
          sound(e.dimension, "mob.wither.shoot", pos, 1.5, 1);
          projectile(e, pos, dir, { speed: 1.1, maxDist: 42, radius: 1.3, size: 1.4, color: C.bigBang, core: C.white, trail: true,
            explode: { radius: 4.5, dmg: 85 * powerOf(e) / 100, color: C.bigBang, carve: 2, knock: 2 } });
          later(8, () => setPose(e, 0));
        });
      },
    },
    {
      id: "finalflash", label: "Final Flash", cd: 600, cost: 420, min: 6, max: 48, weight: 4,
      cond: (e) => formOf(e) >= 1,
      run(e, s, t) {
        busy(s, 72); face(e, aim(t));
        announce(e, "§e§lFinal...");
        sound(e.dimension, "beacon.activate", e.location, 2, 0.8);
        chargeOrb(e, t, 45, C.flash, 0.4, 2.0, 1);
        later(45, () => {
          if (!e.isValid) return;
          if (alive(t)) face(e, aim(t));
          announce(e, "§e§lFLASH!!");
          const f = formOf(e);
          beam(e, alive(t) ? t : e, { color: C.flash, width: 2.0 + 0.3 * f, length: 48, dmg: 150 * powerOf(e) / 100, carve: 2, blast: 5, ticks: 10, pitch: 0.6 });
          later(24, () => setPose(e, 0));
        });
      },
    },
    {
      id: "hakai", label: "Hakai", cd: 700, cost: 450, min: 2, max: 12, weight: 4,
      cond: (e) => formOf(e) === 3,
      run(e, s, t) {
        busy(s, 24); face(e, aim(t)); setPose(e, 4);
        announce(e, "§5§lHakai!");
        sound(e.dimension, "mob.wither.ambient", e.location, 1.5, 0.6);
        later(8, () => {
          if (!e.isValid) return;
          const tt = alive(t) ? t : e;
          const { pos, dir } = handPos(e, tt);
          projectile(e, pos, dir, { speed: 0.9, maxDist: 16, radius: 1.2, size: 1.0, color: C.hakai, core: C.ego, solid: true, homing: t,
            onEnd(p) {
              if (alive(t) && V.dist(aim(t), p) < 3) deal(e, t, 210 * powerOf(e) / 100);
              for (let k = 0; k < 3; k++) sphereFx(e.dimension, p, 1 + k * 0.6, k % 2 ? C.ego : C.hakai, 14, 0.5, "orb_solid", 0.9);
              sound(e.dimension, "mob.wither.death", p, 0.8, 1.6);
            } });
          later(8, () => setPose(e, 0));
        });
      },
    },
    {
      id: "dash", label: "Dash", cd: 120, cost: 50, min: 10, max: 48, weight: 3,
      run(e, s, t) {
        busy(s, 12);
        if (teleportNear(e, t, false, 1.4)) punches(e, t, 2, 12 * powerOf(e) / 100, C.ssbBlue);
      },
    },
  ],
};

function domain(e, s) {
  const dim = e.dimension;
  const center = V.up(e.location, 1);
  const R = 14;
  busy(s, 24); setPose(e, 3); slow(e, 20, 8);
  if (formOf(e) === 0) { try { e.triggerEvent("ab:form_1"); } catch (err) { /* ignore */ } }
  announce(e, "§b§lDomain Expansion: §f§lUnlimited Void");
  sound(dim, "mob.warden.sonic_boom", center, 2, 0.5);
  sound(dim, "ambient.weather.thunder", center, 1, 0.5);
  later(20, () => setPose(e, 0));
  const gojoPower = powerOf(e);
  const team = teamOf(e);
  every(4, 30, (i) => {
    if (!e.isValid) return false;
    sphereFx(dim, center, R, C.void, 40, 1.6, "orb_solid", 0.5);
    sphereFx(dim, center, R * 0.85, C.white, 12, 0.2, "orb", 0.6);
    if (i % 5 === 0) {
      let list = [];
      try { list = dim.getEntities({ location: center, maxDistance: R }); } catch (err) { /* ignore */ }
      for (const o of list) {
        if (!canHit(e, team, o)) continue;
        const ratio = clamp(gojoPower / powerOf(o), 0.25, 1);
        const ticks = Math.round(24 * ratio);
        if (isFighter(o)) { const os = state(o); os.stunUntil = Math.max(os.stunUntil, now() + ticks); setPose(o, 0); }
        slow(o, ticks, 255);
        try { o.addEffect("weakness", ticks, { amplifier: 255, showParticles: false }); } catch (err) { /* ignore */ }
        try { if (o.typeId === "minecraft:player") o.addEffect("darkness", 40, { amplifier: 0, showParticles: false }); } catch (err) { /* ignore */ }
        deal(e, o, 8 * gojoPower / 100, true);
        fx(dim, "orb", aim(o), C.white, 0.6, 0.6);
      }
    }
    if (i === 29) {
      s.burnoutUntil = now() + 160;
      announce(e, "§7Gojo: domain ended — §cburnout§7 (no techniques for 8s)");
    }
  });
}

const GOJO = {
  name: "Gojo", color: "§b", energy: 1500, regen: 25, energyName: "§dCE",
  infinity: true,
  dodge: () => 0,
  forms: [
    { label: "Blindfold", power: 100 },
    { label: "Six Eyes", power: 120, aura: null },
  ],
  thresholds: [0.75],
  formSound: [null, "beacon.activate"],
  abilities: [
    {
      id: "blue", label: "Blue", cd: 160, cost: 140, min: 3, max: 30, weight: 4, technique: true,
      run(e, s, t) {
        busy(s, 14); face(e, aim(t)); setPose(e, 4);
        announce(e, "§9§lCursed Technique Lapse: Blue");
        const dim = e.dimension;
        const center = V.up(t.location, 1.2);
        const team = teamOf(e);
        sound(dim, "mob.endermen.portal", center, 2, 0.5);
        carve(dim, center, 2);
        later(10, () => setPose(e, 0));
        every(2, 20, (i) => {
          if (!e.isValid) return false;
          fx(dim, "orb", center, C.blue, 1.4, 0.2);
          fx(dim, "orb", center, C.white, 0.6, 0.2);
          for (let k = 0; k < 4; k++) {
            const a = i * 0.7 + k * (Math.PI / 2);
            fx(dim, "orb", V.add(center, { x: Math.cos(a) * 2, y: Math.sin(a * 0.5) * 0.6, z: Math.sin(a) * 2 }), C.blue, 0.35, 0.3);
          }
          implode(dim, center, C.blue, 5, 6);
          let list = [];
          try { list = dim.getEntities({ location: center, maxDistance: 7 }); } catch (err) { /* ignore */ }
          for (const o of list) {
            if (!canHit(e, team, o)) continue;
            const d = V.sub(center, o.location);
            const n = V.norm(d);
            try { o.applyKnockback({ x: n.x * 0.6, z: n.z * 0.6 }, clamp(n.y * 0.4, 0, 0.3)); } catch (err) { /* ignore */ }
            if (i % 2 === 0) deal(e, o, 5 * powerOf(e) / 100);
          }
          if (i === 19) burst(dim, center, C.blue, 30, -3, 0.4, 0.5);
        });
      },
    },
    {
      id: "red", label: "Red", cd: 200, cost: 180, min: 3, max: 28, weight: 4, technique: true,
      run(e, s, t) {
        busy(s, 18); face(e, aim(t)); setPose(e, 4);
        announce(e, "§c§lReversed Cursed Technique: Red");
        chargeOrb(e, t, 10, C.red, 0.2, 0.7, 4);
        later(10, () => {
          if (!e.isValid) return;
          const tt = alive(t) ? t : e;
          const { pos, dir } = handPos(e, tt);
          sound(e.dimension, "mob.wither.shoot", pos, 1.5, 1.5);
          projectile(e, pos, dir, { speed: 1.8, maxDist: 32, radius: 1.1, size: 0.8, color: C.red, core: C.white, trail: true,
            explode: { radius: 3.5, dmg: 75 * powerOf(e) / 100, color: C.red, carve: 2, knock: 3.5 } });
          later(6, () => setPose(e, 0));
        });
      },
    },
    {
      id: "purple", label: "Hollow Purple", cd: 700, cost: 600, min: 5, max: 60, weight: 5, technique: true,
      cond: (e, s, c) => c.hp < 0.85 || c.tPower > c.power,
      run(e, s, t) {
        const dim = e.dimension;
        busy(s, 50); face(e, aim(t)); setPose(e, 1); slow(e, 38, 8);
        announce(e, "§5§lHollow Technique: Purple");
        sound(dim, "beacon.activate", e.location, 2, 0.5);
        every(2, 17, (i) => {
          if (!e.isValid) return false;
          const tt = alive(t) ? t : e;
          const { pos, dir } = handPos(e, tt);
          const side = sideOf(dir);
          const k = 1 - i / 16;
          fx(dim, "orb", V.add(pos, V.mul(side, 1.6 * k)), C.blue, 0.9, 0.15);
          fx(dim, "orb", V.add(pos, V.mul(side, -1.6 * k)), C.red, 0.9, 0.15);
          if (i === 16) { fx(dim, "orb", pos, C.purple, 2.5, 0.4); burst(dim, pos, C.purple, 30, 3, 0.5, 0.5); }
        });
        later(36, () => {
          if (!e.isValid) return;
          const tt = alive(t) ? t : e;
          const { pos, dir } = handPos(e, tt);
          const f = formOf(e);
          sound(dim, "mob.warden.sonic_boom", pos, 2, 0.7);
          projectile(e, pos, dir, { speed: 0.9, maxDist: 60, radius: 2.2 + f, size: 4 + f * 1.5, color: C.purple, core: C.white,
            pierce: true, carve: 2.5 + f, dmg: 220 * powerOf(e) / 100 });
          later(10, () => setPose(e, 0));
        });
      },
    },
    {
      id: "domain", label: "Domain Expansion", cd: 1800, cost: 800, min: 0, max: 13, weight: 6, technique: true,
      cond: (e, s, c) => c.hp < 0.6 || c.tPower > c.power * 1.2,
      run: (e, s) => domain(e, s),
    },
    {
      id: "rct", label: "Reverse Cursed Technique", cd: 400, cost: 300, min: 0, max: 64, weight: 5,
      cond: (e, s, c) => c.hp < 0.5,
      run(e, s) {
        busy(s, 10);
        const h = health(e);
        if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + 140));
        fx(e.dimension, "aura", e.location, C.heal, 1, 0.8, { count: 25 * fxLevel(), speed: 2 });
        sound(e.dimension, "random.levelup", e.location, 1, 1.4);
        announce(e, "§aGojo: Reverse Cursed Technique");
      },
    },
    {
      id: "tp", label: "Teleport", cd: 100, cost: 40, min: 12, max: 48, weight: 3, technique: true,
      run(e, s, t) { busy(s, 6); teleportNear(e, t, Math.random() < 0.5, 2); },
    },
  ],
};

const FIGHTERS = { "ab:goku": GOKU, "ab:vegeta": VEGETA, "ab:gojo": GOJO };

// ------------------------------------------------------------------ fighter brain
function updateFighter(e, tick) {
  const def = FIGHTERS[e.typeId];
  const s = state(e);
  s.energy = Math.min(def.energy, s.energy + def.regen / 4);
  const team = teamOf(e);

  if (def.infinity) {
    const on = s.energy > 60 && tick >= s.burnoutUntil && tick >= s.infinityBrokenUntil;
    if (on && !e.hasTag("ab_infinity")) e.addTag("ab_infinity");
    if (!on && e.hasTag("ab_infinity")) e.removeTag("ab_infinity");
    if (on && team) s.energy -= 1.5;
  }
  if (s.kaiokenUntil > tick && tick % 20 === 0) deal(undefined, e, 2);
  aura(e, s, def);

  if (!team) return;
  if (tick < s.stunUntil) {
    if (tick % 10 === 0) ring(e.dimension, V.up(e.location, 2.2), 0.5, C.white, 6, 0.15);
    return;
  }
  const target = nearestEnemy(e, team, 48);
  if (!target) return;
  if (tick - s.lastCombat > 100) s.combatSince = tick;
  s.lastCombat = tick;
  if (tick < s.busyUntil) return;

  const ctx = { dist: V.dist(e.location, target.location), power: powerOf(e), tPower: powerOf(target), hp: hpPct(e) };
  const form = formOf(e);
  if (form < def.forms.length - 1 && tick >= s.nextTransform && tick - s.combatSince > 40 &&
      (ctx.hp < def.thresholds[form] || ctx.tPower > ctx.power * 0.95)) {
    const nf = def.forms[form + 1];
    transform(e, s, form + 1, nf.label, nf.aura ?? C.white, def.formSound[form + 1]);
    return;
  }
  if (Math.random() > 0.45) return;
  const burnt = tick < s.burnoutUntil;
  const ok = def.abilities.filter((a) => (s.cd[a.id] ?? 0) <= tick && s.energy >= a.cost && ctx.dist >= a.min && ctx.dist <= a.max &&
    !(burnt && a.technique) && (!a.cond || a.cond(e, s, ctx)));
  if (!ok.length) return;
  let r = Math.random() * ok.reduce((n, a) => n + a.weight, 0);
  const pick = ok.find((a) => (r -= a.weight) <= 0) ?? ok[0];
  s.energy -= pick.cost;
  s.cd[pick.id] = tick + pick.cd;
  pick.run(e, s, target, ctx);
}

// Vanilla mobs put on a team get a simple fighting brain: walk at the nearest enemy and hit it.
const VANILLA_DMG = { "minecraft:warden": 30, "minecraft:iron_golem": 15, "minecraft:ravager": 12, "minecraft:wither": 12,
  "minecraft:ender_dragon": 15, "minecraft:vindicator": 9, "minecraft:piglin_brute": 10, "minecraft:hoglin": 6, "minecraft:zoglin": 6 };
function updateVanilla(e, tick) {
  if (e.typeId === "minecraft:player" || isFighter(e)) return;
  const team = teamOf(e);
  const target = nearestEnemy(e, team, 24);
  if (!target) return;
  const s = state(e);
  const d = V.dist(e.location, target.location);
  if (d > 2.6) {
    const n = V.norm(V.sub(target.location, e.location));
    try { e.applyImpulse({ x: n.x * 0.2, y: 0, z: n.z * 0.2 }); } catch (err) { /* ignore */ }
  } else if (tick >= s.meleeCd) {
    s.meleeCd = tick + 20;
    face(e, aim(target));
    deal(e, target, VANILLA_DMG[e.typeId] ?? 4);
  }
}

// ------------------------------------------------------------------ name tags with health bars
function bar(pct) {
  const n = 20, full = Math.round(clamp(pct, 0, 1) * n);
  const col = pct > 0.6 ? "§a" : pct > 0.3 ? "§e" : "§c";
  return `${col}${"|".repeat(full)}§8${"|".repeat(n - full)}`;
}
function teamLabel(team) {
  return team === RED ? "§c[RED] " : team === BLUE ? "§9[BLUE] " : "";
}
function updateTag(e) {
  const h = health(e);
  if (!h) return;
  const team = teamOf(e);
  const def = FIGHTERS[e.typeId];
  const hp = Math.max(0, Math.ceil(h.currentValue));
  const max = Math.round(h.effectiveMax);
  const pct = h.currentValue / h.effectiveMax;
  let text;
  if (def) {
    const s = state(e);
    const form = def.forms[clamp(formOf(e), 0, def.forms.length - 1)].label;
    let extra = "";
    if (s.kaiokenUntil > now()) extra += " §c[Kaioken]";
    if (s.ego > 0.01) extra += ` §5[Ego +${Math.round(s.ego * 100)}%]`;
    if (e.hasTag("ab_infinity")) extra += " §b[Infinity]";
    if (s.burnoutUntil > now()) extra += " §7[Burnout]";
    if (s.stunUntil > now()) extra += " §f[Stunned]";
    text = `${teamLabel(team)}${def.color}§l${def.name}§r §7(${form})${extra}\n${bar(pct)} §f${hp}§7/${max}\n${def.energyName} §f${Math.max(0, Math.floor(s.energy))}`;
  } else if (team) {
    text = `${teamLabel(team)}§f${prettyType(e.typeId)}\n${bar(pct)} §f${hp}§7/${max}`;
  } else return;
  if (e.nameTag !== text) e.nameTag = text;
}

// ------------------------------------------------------------------ main loop
system.runInterval(() => {
  const tick = now();
  for (const id of DIMENSIONS) {
    let dim;
    try { dim = world.getDimension(id); } catch (e) { continue; }
    let fighters = [];
    try { fighters = dim.getEntities({ families: [FIGHTER_FAMILY] }); } catch (e) { continue; }
    for (const f of fighters) {
      try {
        if (!alive(f)) continue;
        updateFighter(f, tick);
        if (tick % 10 === 0) updateTag(f);
      } catch (e) { warn("fighter", e); }
    }
    if (tick % 10 === 0) {
      for (const tag of [RED, BLUE]) {
        let list = [];
        try { list = dim.getEntities({ tags: [tag], excludeFamilies: [FIGHTER_FAMILY] }); } catch (e) { continue; }
        for (const v of list) {
          try {
            if (!alive(v)) continue;
            updateVanilla(v, tick);
            if (v.typeId !== "minecraft:player") updateTag(v);
          } catch (e) { warn("vanilla", e); }
        }
      }
    }
  }
}, 5);

// ------------------------------------------------------------------ damage rules (Infinity, dodges, Ultra Ego, sticks)
function heldItem(p) {
  try { return p.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Mainhand)?.typeId; } catch (e) { return undefined; }
}
const killing = new Set(); // Kill Stick targets: nothing may save them
world.beforeEvents.entityHurt.subscribe((ev) => {
  try {
    const v = ev.hurtEntity;
    if (killing.has(v.id)) return;
    const src = ev.damageSource.damagingEntity;
    const cause = ev.damageSource.cause;
    if (src && src.typeId === "minecraft:player") {
      const item = heldItem(src);
      if (item === "ab:team_stick" || item === "ab:kill_stick") { ev.cancel = true; return; }
    }
    const def = FIGHTERS[v.typeId];
    if (!def || cause === EntityDamageCause.override || cause === EntityDamageCause.fall) return;
    const s = state(v);
    if (def.infinity && v.hasTag("ab_infinity")) {
      // Infinity stops everything, but holding back stronger attacks costs more cursed energy.
      const attackerPower = src && src.isValid ? powerOf(src) : 50;
      const cost = ev.damage * 1.2 * Math.max(1, attackerPower / 100);
      s.energy -= cost;
      if (s.energy >= 0) {
        ev.cancel = true;
        system.run(() => { if (v.isValid) ring(v.dimension, V.up(v.location, 1), 1.1, C.blue, 12, 0.2); });
        return;
      }
      const over = -s.energy / (1.2 * Math.max(1, attackerPower / 100));
      s.energy = 0;
      s.infinityBrokenUntil = now() + 120;
      ev.damage = over;
      system.run(() => { if (v.isValid) { burst(v.dimension, V.up(v.location, 1), C.blue, 30, 4); announce(v, "§cGojo's Infinity was overwhelmed!"); } });
    }
    if (now() >= s.busyUntil || formOf(v) === 4) {
      const chance = def.dodge(v, s);
      if (chance > 0 && Math.random() < chance) {
        ev.cancel = true;
        system.run(() => dodgeFx(v, src));
        return;
      }
    }
    if (def.ego && formOf(v) === def.ego) s.ego = Math.min(0.6, s.ego + ev.damage / 500);
  } catch (e) { warn("hurt", e); }
});
function dodgeFx(v, src) {
  if (!v.isValid) return;
  const ui = v.typeId === "ab:goku" && formOf(v) === 4;
  const color = ui ? C.silver : C.white;
  fx(v.dimension, "aura", v.location, color, 1, 0.4, { count: 12 * fxLevel(), speed: 0 });
  const from = src && src.isValid ? src.location : V.add(v.location, { x: 1, y: 0, z: 0 });
  const side = V.mul(sideOf(V.norm(V.sub(v.location, from))), Math.random() < 0.5 ? 1.6 : -1.6);
  try { v.tryTeleport(V.add(v.location, side), { checkForBlocks: true }); } catch (e) { /* ignore */ }
  sound(v.dimension, "mob.endermen.portal", v.location, 0.6, 2);
}

// Gojo's Black Flash: a rare melee hit with distorted cursed energy.
world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const a = ev.damagingEntity, t = ev.hitEntity;
    if (a.typeId === "minecraft:player") { onStickHit(a, t); return; }
    if (a.typeId === "ab:gojo" && alive(t) && Math.random() < 0.1) {
      deal(a, t, 35 * powerOf(a) / 100);
      fx(a.dimension, "orb_solid", aim(t), C.black, 1.4, 0.4);
      burst(a.dimension, aim(t), C.red, 20, 4, 0.3, 0.4);
      burst(a.dimension, aim(t), C.black, 14, 3, 0.4, 0.4);
      sound(a.dimension, "random.explode", t.location, 0.6, 1.6);
      announce(a, "§0§l§kX§r §4§lBlack Flash §0§l§kX");
    }
  } catch (e) { warn("hit", e); }
});

// ------------------------------------------------------------------ sticks
const nextTeam = new Map();
function setTeam(e, team) {
  e.removeTag(RED);
  e.removeTag(BLUE);
  e.addTag(team);
  if (isFighter(e)) {
    try { e.triggerEvent("ab:enter_combat"); } catch (err) { /* ignore */ }
  }
  const c = C.team[team];
  ring(e.dimension, V.up(e.location, 0.1), 1.2, c, 20, 0.35);
  fx(e.dimension, "aura", e.location, c, 0.8, 0.6, { count: 14, speed: 1.5 });
  updateTag(e);
}
function onStickHit(p, t) {
  const item = heldItem(p);
  if (item === "ab:team_stick") {
    if (!t.isValid) return;
    const team = nextTeam.get(p.id) ?? RED;
    setTeam(t, team);
    nextTeam.set(p.id, enemyOf(team));
    const name = FIGHTERS[t.typeId]?.name ?? (t.typeId === "minecraft:player" ? t.name : prettyType(t.typeId));
    sound(p.dimension, "random.orb", p.location, 1, team === RED ? 0.8 : 1.3);
    p.onScreenDisplay.setActionBar(`${teamLabel(team)}§f${name}   §7next: ${teamLabel(enemyOf(team))}`);
  } else if (item === "ab:kill_stick") {
    if (!t.isValid || t.typeId === "minecraft:player") return;
    const dim = t.dimension, loc = aim(t);
    fx(dim, "orb_solid", loc, C.black, 2, 0.5);
    burst(dim, loc, C.red, 30, 4, 0.4, 0.6);
    sound(dim, "mob.warden.sonic_boom", loc, 1, 1.4);
    states.delete(t.id);
    killing.add(t.id);
    later(4, () => killing.delete(t.id));
    try { t.kill(); } catch (e) { /* ignore */ }
    later(2, () => { if (t.isValid) { try { t.remove(); } catch (e) { /* ignore */ } } });
  }
}
function resetTeams(p) {
  let n = 0;
  for (const id of DIMENSIONS) {
    let dim;
    try { dim = world.getDimension(id); } catch (e) { continue; }
    for (const tag of [RED, BLUE]) {
      let list = [];
      try { list = dim.getEntities({ tags: [tag] }); } catch (e) { continue; }
      for (const e of list) {
        try {
          e.removeTag(RED); e.removeTag(BLUE);
          if (isFighter(e)) {
            e.triggerEvent("ab:leave_combat");
            e.triggerEvent("ab:form_0");
            setPose(e, 0);
            states.delete(e.id);
            updateTag(e);
          } else if (e.typeId !== "minecraft:player") e.nameTag = "";
          n++;
        } catch (err) { /* ignore */ }
      }
    }
  }
  nextTeam.set(p.id, RED);
  p.onScreenDisplay.setActionBar(`§aTeams cleared (${n}). §7Next hit: §c[RED]`);
}
world.afterEvents.itemUse.subscribe((ev) => {
  try {
    const p = ev.source, id = ev.itemStack?.typeId;
    if (id === "ab:team_stick") {
      if (p.isSneaking) { resetTeams(p); return; }
      const team = enemyOf(nextTeam.get(p.id) ?? RED);
      nextTeam.set(p.id, team);
      p.onScreenDisplay.setActionBar(`§fNext hit joins ${teamLabel(team)}§r §7(sneak + use = reset)`);
    } else if (id === "ab:kill_stick") {
      if (p.isSneaking) {
        const v = fxLevel() === 1 ? 0.5 : 1;
        world.setDynamicProperty("ab:fx", v);
        p.onScreenDisplay.setActionBar(`§fEffects: ${v === 1 ? "§aFULL" : "§eLOW (for weak phones)"}`);
      } else {
        const g = !griefing();
        world.setDynamicProperty("ab:griefing", g);
        p.onScreenDisplay.setActionBar(`§fAbilities break blocks: ${g ? "§aON" : "§cOFF"}`);
      }
    }
  } catch (e) { warn("use", e); }
});

// ------------------------------------------------------------------ misc
world.afterEvents.entityDie.subscribe((ev) => {
  try {
    const e = ev.deadEntity;
    const def = FIGHTERS[e.typeId];
    states.delete(e.id);
    if (def && teamOf(e)) announce(e, `${teamLabel(teamOf(e))}${def.color}§l${def.name} §r§fhas been defeated!`);
  } catch (err) { /* ignore */ }
});
world.afterEvents.entityRemove.subscribe((ev) => { states.delete(ev.removedEntityId); });

world.afterEvents.playerSpawn.subscribe((ev) => {
  try {
    const p = ev.player;
    if (!ev.initialSpawn || p.getDynamicProperty("ab:kit")) return;
    p.setDynamicProperty("ab:kit", true);
    const inv = p.getComponent("minecraft:inventory")?.container;
    for (const id of ["ab:team_stick", "ab:kill_stick", "ab:goku_spawn_egg", "ab:vegeta_spawn_egg", "ab:gojo_spawn_egg"]) {
      try { inv?.addItem(new ItemStack(id, 1)); } catch (e) { warn("kit " + id, e); }
    }
    p.sendMessage("§6[Anime Battles] §fTeam Stick: hit = §cRED§f, next hit = §9BLUE§f. Sneak+use = reset.\n§4Kill Stick§f: hit = instant kill. Use = block damage on/off. Sneak+use = effects low/full.");
  } catch (e) { warn("kit", e); }
});

system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id === "ab:griefing") world.setDynamicProperty("ab:griefing", ev.message.trim() !== "off");
  if (ev.id === "ab:fx") world.setDynamicProperty("ab:fx", ev.message.trim() === "low" ? 0.5 : 1);
});
