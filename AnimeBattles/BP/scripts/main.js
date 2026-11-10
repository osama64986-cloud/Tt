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
const IGNORE_TYPES = new Set(["ab:vfx", "minecraft:item", "minecraft:xp_orb", "minecraft:arrow", "minecraft:armor_stand", "minecraft:painting",
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
  fire: { red: 1, green: 0.45, blue: 0.08 },
  blood: { red: 0.75, green: 0.02, blue: 0.08 },
  haki: { red: 0.55, green: 0.05, blue: 0.1 },
  nika: { red: 1, green: 0.97, blue: 0.85 },
  steam: { red: 1, green: 0.78, blue: 0.8 },
  ce: { red: 0.35, green: 0.55, blue: 1 },
  death: { red: 0.9, green: 0.3, blue: 0.85 },
  zoro: { red: 0.55, green: 0.95, blue: 0.55 },
};

// ------------------------------------------------------------------ 3D energy entities (beams + balls)
const SLOT = new Map([[C.kameBlue, 0], [C.ssbBlue, 0], [C.galick, 1], [C.ego, 1], [C.flash, 2], [C.bigBang, 3], [C.red, 4], [C.kaioken, 4],
  [C.blue, 5], [C.purple, 6], [C.hakai, 7], [C.kiYellow, 9], [C.gold, 9], [C.silver, 10], [C.white, 10],
  [C.fire, 11], [C.blood, 12], [C.haki, 13], [C.black, 13], [C.nika, 14], [C.ce, 5], [C.death, 15], [C.zoro, 16]]);
const slotOf = (c) => SLOT.get(c) ?? 10;
const vfxAlive = new Map();
function spawnVfx(dim, kind, loc, o) {
  try {
    const v = dim.spawnEntity("ab:vfx", loc);
    v.setProperty("ab:kind", kind);
    v.setProperty("ab:color", o.slot ?? 10);
    v.setProperty("ab:size", clamp(o.size ?? 1, 0, 40));
    v.setProperty("ab:len", 0);
    if (o.dir) orientVfx(v, loc, o.dir);
    vfxAlive.set(v.id, now() + (o.life ?? 200));
    return v;
  } catch (e) { warn("vfx", e); return undefined; }
}
function orientVfx(v, loc, dir) {
  const yaw = (Math.atan2(-dir.x, dir.z) * 180) / Math.PI;
  const pitch = (-Math.asin(clamp(dir.y, -1, 1)) * 180) / Math.PI;
  try { v.teleport(loc, { rotation: { x: 0, y: yaw } }); v.setProperty("ab:pitch", clamp(pitch, -90, 90)); } catch (e) { /* ignore */ }
}
function vset(v, k, val) { try { if (v && v.isValid) v.setProperty(k, val); } catch (e) { /* ignore */ } }
function killVfx(v) { try { if (v && v.isValid) { vfxAlive.delete(v.id); v.remove(); } } catch (e) { /* ignore */ } }
function fadeVfx(v, from, ticks = 5) {
  every(1, ticks, (i) => { vset(v, "ab:size", from * (1 - (i + 1) / ticks)); if (i === ticks - 1) killVfx(v); });
}
function shake(dim, loc, power = 0.25, secs = 0.3) {
  try { dim.runCommand(`camerashake add @a[x=${Math.floor(loc.x)},y=${Math.floor(loc.y)},z=${Math.floor(loc.z)},r=14] ${power} ${secs} positional`); } catch (e) { /* ignore */ }
}

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
// Face expression shown by the render controller: 0 normal (blinks on its own), 1 shout, 2 pain.
function setExpr(e, v, ticks) {
  if (!e || !e.isValid || !FIGHTERS[e.typeId]) return;
  const s = state(e);
  s.exprUntil = now() + ticks;
  if (s.expr !== v) {
    s.expr = v;
    try { e.setProperty("ab:expr", v); } catch (e2) { /* ignore */ }
  }
}
function announce(e, text) {
  setExpr(e, 1, 30);
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
      infinityBrokenUntil: 0, kaiokenUntil: 0, ego: 0, transformUntil: 0, nextTransform: 0, combatSince: 0, lastCombat: 0, meleeCd: 0,
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
  const ball = spawnVfx(dim, 1, pos, { slot: o.slot ?? slotOf(o.color), size: 0.3, life: 40 });
  every(1, 5, (i) => vset(ball, "ab:size", (0.3 + o.radius * 0.28 * (i + 1))));
  later(7, () => fadeVfx(ball, 0.3 + o.radius * 1.4, 5));
  fx(dim, "shock", V.up(pos, -o.radius * 0.4), o.color, o.radius * 3.2, 0.6);
  fx(dim, "flash", pos, C.white, o.radius * 1.8, 0.25);
  fx(dim, "streak", pos, o.color, 1.6 + o.radius * 0.2, 0.5, { count: Math.ceil((14 + o.radius * 4) * fxLevel()), speed: 8 + o.radius * 2 });
  if (o.radius >= 3) shake(dim, pos, Math.min(0.6, 0.12 * o.radius), 0.4);
  burst(dim, pos, o.color, 26 + o.radius * 6, o.radius * 3, 0.5 + o.radius * 0.08, 0.8);
  burst(dim, pos, C.white, 10 + o.radius * 2, o.radius * 1.5, 0.4, 0.5);
  sphereFx(dim, pos, o.radius * 0.6, o.color, 10 + o.radius * 3, 0.9, "orb", 0.5);
  sound(dim, "random.explode", pos, 1 + o.radius * 0.3, o.radius > 4 ? 0.6 : 0.9);
  fx(dim, "orb", pos, C.white, o.radius * 1.1, 0.15);
  every(2, 5, (i) => ring(dim, V.up(pos, -o.radius * 0.3), o.radius * (0.4 + i * 0.35), o.color, 14 + o.radius * 2, 0.45));
  fx(dim, "aura", V.up(pos, -1), { red: 0.35, green: 0.33, blue: 0.3 }, 1.2, 1.2, { count: (10 + o.radius * 3) * fxLevel(), speed: 1 });
  hitArea(src, pos, o.radius, o.dmg, new Set(), { knock: o.knock ?? 1.2, lift: 0.45 });
  carve(dim, pos, o.carve ?? 0);
}

// A beam that grows from the caster toward the target, hitting everything along it once.
function beam(src, target, o) {
  setExpr(src, 1, 26);
  const dim = src.dimension;
  const { pos: start, dir } = handPos(src, target);
  const hit = new Set();
  const len = o.length ?? 45, steps = o.ticks ?? 8, grow = len / steps;
  let reach = 0, ended = false, carved = 0;
  sound(dim, o.sound ?? "mob.wither.shoot", start, 2, o.pitch ?? 0.8);
  const spacing = 0.5 / fxLevel();
  const side = sideOf(dir);
  const up2 = V.norm({ x: dir.y * side.z - dir.z * side.y, y: dir.z * side.x - dir.x * side.z, z: dir.x * side.y - dir.y * side.x });
  const bsize = o.width * 0.85;
  const shaft = spawnVfx(dim, 0, start, { slot: o.slot ?? slotOf(o.color), size: bsize, dir, life: 120 });
  fx(dim, "shock_v", start, o.color, o.width * 3, 0.4);
  const id = system.runInterval(() => {
    try {
      if (!src.isValid || ended) { system.clearRun(id); killVfx(shaft); return; }
      const prev = reach;
      reach = Math.min(len, reach + grow);
      vset(shaft, "ab:len", reach);
      for (let s = prev; s <= reach; s += spacing) {
        const p = V.add(start, V.mul(dir, s));
        if (!griefing() && solidAt(dim, p)) { reach = s; ended = true; vset(shaft, "ab:len", reach); break; }
        if (Math.floor(s * 2) % 3 === 0) fx(dim, "orb", p, o.color, o.width * 1.3, 0.35);
        const a = s * 1.3;
        const off = V.add(V.mul(side, Math.cos(a) * o.width), V.mul(up2, Math.sin(a) * o.width));
        fx(dim, "orb", V.add(p, off), o.color, o.width * 0.45, 0.45);
        fx(dim, "orb", V.sub(p, off), C.white, o.width * 0.3, 0.4);
      }
      fx(dim, "orb", start, o.color, o.width * 2.4, 0.2);
      fx(dim, "orb", start, C.white, o.width * 1.2, 0.15);
      fx(dim, "orb", V.add(start, V.mul(dir, reach)), o.color, o.width * 2.2, 0.2);
      fx(dim, "streak", V.add(start, V.mul(dir, reach)), o.color, 1.2 + o.width * 0.4, 0.3, { count: 4 * fxLevel(), speed: 6 });
      for (let s = prev; s <= reach; s += 1) {
        const p = V.add(start, V.mul(dir, s));
        hitArea(src, p, o.width * 0.8 + 0.7, o.dmg, hit, { knock: 0.8, lift: 0.2 });
        if (o.carve && carved < 600 && Math.floor(s) % 2 === 0) { carve(dim, p, o.carve, 40); carved += 20; }
      }
      if (reach >= len || ended) {
        ended = true;
        system.clearRun(id);
        const tip = V.add(start, V.mul(dir, reach));
        later(8, () => fadeVfx(shaft, bsize, 6));
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
  const ball = o.size >= 0.7 ? spawnVfx(dim, 1, start, { slot: o.slot ?? slotOf(o.color), size: o.size * 0.62, life: 400 }) : undefined;
  const id = system.runInterval(() => {
    try {
      if (done || !src.isValid) { system.clearRun(id); killVfx(ball); return; }
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
      try { if (ball && ball.isValid) ball.teleport(pos); } catch (e) { /* ignore */ }
      if (done) {
        system.clearRun(id);
        killVfx(ball);
        if (o.explode) explosion(src, pos, o.explode);
        o.onEnd?.(pos);
      }
    } catch (e) { warn("projectile", e); system.clearRun(id); }
  }, 1);
}

function chargeOrb(src, target, ticks, color, fromSize, toSize, pose) {
  setPose(src, pose);
  slow(src, ticks + 4, 6);
  const ball = spawnVfx(src.dimension, 1, handPos(src, alive(target) ? target : src).pos, { slot: slotOf(color), size: fromSize * 0.5, life: ticks + 20 });
  every(1, ticks, (i) => {
    if (!src.isValid) { killVfx(ball); return false; }
    const { pos } = handPos(src, alive(target) ? target : src);
    try { if (ball && ball.isValid) ball.teleport(pos); } catch (e) { /* ignore */ }
    vset(ball, "ab:size", (fromSize + (toSize - fromSize) * (i / ticks)) * 0.55);
    if (i === ticks - 1) killVfx(ball);
  });
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
  const calm = e.typeId === "ab:goku" && to === 4;  // Ultra Instinct awakens in silence: no yell, no crouch
  if (e.typeId === "ab:frieza" && to === 1) {  // Golden Frieza is born inside a cocoon of golden light
    const cocoon = spawnVfx(dim, 1, V.up(e.location, 1.1), { slot: 9, size: 1.7, life: 34 });
    later(30, () => killVfx(cocoon));
  }
  if (!calm) setExpr(e, 1, 34);
  s.transformUntil = now() + 32;
  s.nextTransform = now() + (def.transformCd ?? 160);
  // DB-style power-up; Luffy has a move per gear: pump (G2), thumb/arm to the mouth and blow (G3, G4), laugh arms wide (G5)
  setPose(e, e.typeId === "ab:luffy" ? (to === 1 ? 30 : to === 6 ? 27 : 25)
    : e.typeId === "ab:zoro" ? 32      // ties the bandana on
    : e.typeId === "ab:gojo" ? 25      // pulls the blindfold off
    : (e.typeId === "ab:ichigo" && to === 2) ? 25   // drags the Hollow mask down over his face
    : (e.typeId === "ab:naruto_teen" || (e.typeId === "ab:naruto_war" && to === 2)) ? 35   // still, hands in a seal, gathering nature energy
    : calm ? 0
    : 22);
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
    { label: "Ultra Instinct", power: 430, aura: C.silver },
  ],
  thresholds: [0.9, 0.7, 0.5, 0.3],
  transformCd: 80,
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
        // the chant, one syllable at a time while the ki ball grows in his cupped hands
        ["§bKa...", "§bKa... me...", "§bKa... me... ha...", "§bKa... me... ha... me..."].forEach((txt, i) =>
          later(i * 7, () => { if (e.isValid) announce(e, txt); }));
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
        busy(s, 20); setPose(e, 25);  // two fingers to the forehead, lock on to the ki... then vanish
        later(6, () => {
          if (!e.isValid) return;
          setPose(e, 0);
          if (alive(t) && teleportNear(e, t, true)) punches(e, t, 3, 10 * powerOf(e) / 100, C.kiYellow);
        });
      },
    },
    {
      // Cell Games: charge the Kamehameha, vanish with Instant Transmission, fire point-blank from beside the enemy
      id: "itkame", label: "Instant Kamehameha", cd: 520, cost: 300, min: 0, max: 48, weight: 4, cond: (e) => formOf(e) >= 1,
      run(e, s, t) {
        busy(s, 44); face(e, aim(t));
        announce(e, "§bKa... me... ha... me...");
        chargeOrb(e, t, 18, C.kameBlue, 0.3, 1.3, 2);
        later(18, () => { if (e.isValid) setPose(e, 25); });
        later(24, () => {
          if (!e.isValid || !alive(t)) { if (e.isValid) setPose(e, 0); return; }
          afterimage(e);
          teleportNear(e, t, false, 2.2);
          face(e, aim(t)); setPose(e, 1);
          announce(e, "§b§lHAAAAA! §7(Instant Kamehameha)");
          beam(e, t, { color: C.kameBlue, width: 1.5 + 0.25 * formOf(e), length: 30, dmg: 95 * powerOf(e) / 100, carve: 1, blast: 4, ticks: 5 });
          later(16, () => { if (e.isValid) setPose(e, 0); });
        });
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
      cond: () => true,
      run(e, s, t) {
        busy(s, 22); setPose(e, 5);  // a full-body punch, not an open palm
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
      cond: () => true,
      run(e, s, t) {
        busy(s, 100); setPose(e, 3); slow(e, 92, 8);
        announce(e, "§b§lEveryone, lend me your energy!  §f(Spirit Bomb)");
        sound(e.dimension, "beacon.power", e.location, 2, 0.6);
        const ticks = 90;
        const sb = spawnVfx(e.dimension, 1, V.up(e.location, 4.6), { slot: 8, size: 0.6, life: ticks + 10 });
        every(1, ticks, (i) => {
          if (!e.isValid) { killVfx(sb); return false; }
          const r = 0.6 + (2.9 * i) / ticks;
          try { if (sb && sb.isValid) sb.teleport(V.up(e.location, 4 + r)); } catch (err) { /* ignore */ }
          vset(sb, "ab:size", r * 1.25);
          if (i === ticks - 1) killVfx(sb);
        });
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
  transformCd: 80,
  formSound: [null, "mob.enderdragon.growl", "beacon.power", "mob.wither.spawn"],
  abilities: [
    {
      id: "barrage", label: "Ki Barrage", cd: 80, cost: 60, min: 3, max: 32, weight: 3,
      run(e, s, t) {
        busy(s, 18); setPose(e, 11);  // alternating palms, one blast per hand
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
        announce(e, "§dGalick...");
        chargeOrb(e, t, 22, C.galick, 0.3, 1.2, 2);
        later(22, () => {
          if (!e.isValid) return;
          if (alive(t)) face(e, aim(t));
          setPose(e, 1);
          announce(e, "§d§lGUN!! FIRE!!");
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
      cond: () => true,
      run(e, s, t) {
        busy(s, 72); face(e, aim(t));
        announce(e, "§e§lFinal...");
        sound(e.dimension, "beacon.activate", e.location, 2, 0.8);
        chargeOrb(e, t, 45, C.flash, 0.4, 2.0, 1);
        setPose(e, 27);                                      // arms thrown wide while the ki gathers
        later(32, () => { if (e.isValid) setPose(e, 1); });   // ...then the palms snap together in front
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
  busy(s, 24); setPose(e, 26); slow(e, 20, 8);
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
    { label: "Six Eyes", power: 115, aura: null },
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
        const vb = spawnVfx(dim, 1, center, { slot: 5, size: 0.4, life: 60 });
        every(1, 8, (i) => vset(vb, "ab:size", 0.4 + i * 0.18));
        later(38, () => fadeVfx(vb, 1.8, 4));
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
      // Shinjuku: the full incantation doubles the output — Hollow Purple at 200%
      id: "purple200", label: "Hollow Purple 200%", cd: 1400, cost: 900, min: 5, max: 60, weight: 4, technique: true,
      cond: (e) => formOf(e) === 1,
      run(e, s, t) {
        const dim = e.dimension;
        busy(s, 64); face(e, aim(t)); setPose(e, 26); slow(e, 60, 8);
        ["§d§oNine ropes, polarized light...", "§d§o...crow and declaration...", "§d§o...between front and back.", "§5§lHollow Technique: Purple §d§l(200%)"]
          .forEach((txt, i) => later(i * 12, () => { if (e.isValid) announce(e, txt); }));
        chargeOrb(e, t, 44, C.purple, 0.4, 3.2, 4);
        later(48, () => {
          if (!e.isValid) return;
          const tt = alive(t) ? t : e;
          const { pos, dir } = handPos(e, tt);
          sound(dim, "mob.warden.sonic_boom", pos, 3, 0.5);
          shake(dim, pos, 0.7, 0.7);
          projectile(e, pos, dir, { speed: 0.8, maxDist: 70, radius: 4.5, size: 9, color: C.purple, core: C.white, slot: 6,
            pierce: true, carve: 5, dmg: 380 * powerOf(e) / 100 });
          later(14, () => { if (e.isValid) setPose(e, 0); });
        });
      },
    },
    {
      id: "purple", label: "Hollow Purple", cd: 700, cost: 600, min: 5, max: 60, weight: 5, technique: true,
      cond: () => true,
      run(e, s, t) {
        const dim = e.dimension;
        busy(s, 50); face(e, aim(t)); setPose(e, 4); slow(e, 38, 8);  // one hand forward, as in the anime
        announce(e, "§5§lHollow Technique: Purple");
        sound(dim, "beacon.activate", e.location, 2, 0.5);
        const bb = spawnVfx(dim, 1, e.location, { slot: 5, size: 0.7, life: 50 });
        const rb = spawnVfx(dim, 1, e.location, { slot: 4, size: 0.7, life: 50 });
        every(2, 17, (i) => {
          if (!e.isValid) { killVfx(bb); killVfx(rb); return false; }
          const tt0 = alive(t) ? t : e;
          const hp0 = handPos(e, tt0), sd0 = sideOf(hp0.dir), k0 = 1 - i / 16;
          try { bb.teleport(V.add(hp0.pos, V.mul(sd0, 1.6 * k0))); rb.teleport(V.add(hp0.pos, V.mul(sd0, -1.6 * k0))); } catch (err) { /* ignore */ }
          if (i === 16) { killVfx(bb); killVfx(rb); }
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
          projectile(e, pos, dir, { speed: 0.9, maxDist: 60, radius: 2.2 + f, size: 4 + f * 1.5, color: C.purple, core: C.white, slot: 6,
            pierce: true, carve: 2.5 + f, dmg: 220 * powerOf(e) / 100 });
          later(10, () => setPose(e, 0));
        });
      },
    },
    {
      id: "domain", label: "Domain Expansion", cd: 1800, cost: 800, min: 0, max: 13, weight: 6, technique: true,
      cond: () => true,
      run: (e, s) => domain(e, s),
    },
    {
      id: "rct", label: "Reverse Cursed Technique", cd: 400, cost: 300, min: 0, max: 64, weight: 5,
      cond: (e, s, c) => c.hp < 0.95,
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


// ------------------------------------------------------------------ shared helpers for the new characters
function lineHit(src, from, dir, reach, radius, dmg, opt = {}) {
  const hit = new Set();
  for (let s = 0.5; s <= reach; s += 0.6) hitArea(src, V.add(from, V.mul(dir, s)), radius, dmg, hit, opt);
  return hit.size;
}
// Rubber stretch attack: the arm/leg bone is scaled by the animation; the script hits along the line.
function stretch(e, s, t, o) {
  busy(s, o.ticks + 4); face(e, aim(t)); setPose(e, o.pose);
  if (o.say) announce(e, o.say);
  const hits = o.hits ?? 1;
  every(o.every ?? 2, hits, (i) => {
    if (!alive(t) || !e.isValid) return false;
    face(e, aim(t));
    const { pos, dir } = handPos(e, t);
    const reach = Math.max(o.reach, V.dist(pos, aim(t)) + 1.2);
    lineHit(e, pos, dir, reach, o.radius ?? 0.9, o.dmg * powerOf(e) / 100, { knock: o.knock ?? 0.6, lift: o.lift ?? 0.15 });
    const style = e.typeId === "ab:luffy" ? [null, "steam", null, "haki", "haki", "haki", "nika"][formOf(e)] : null;
    for (let k = 1; k <= reach; k += 1.5) {
      const q = V.add(pos, V.mul(dir, k));
      fx(e.dimension, "orb", q, o.trail ?? C.white, 0.25, 0.15);
      if (style === "steam") fx(e.dimension, "aura", V.up(q, -0.9), C.steam, 0.6, 0.5, { count: 2, speed: 1 });
      if (style === "haki") { fx(e.dimension, "orb", q, C.fire, 0.45, 0.25); fx(e.dimension, "orb_solid", q, C.black, 0.3, 0.2); }
    }
    if (style === "nika") { fx(e.dimension, "shock_v", aim(t), C.nika, 3.5, 0.4); for (let k = 0; k < 3; k++) fx(e.dimension, "flash", V.up(aim(t), 0.8 + k * 0.4), C.nika, 0.7, 0.4); }
    if (style === "haki") fx(e.dimension, "streak", aim(t), C.fire, 1.4, 0.35, { count: 10, speed: 9 });
    impact(e, t, o.strong || i === hits - 1, o.color ?? C.white, o.ground ? { ground: true } : undefined);
  });
  later(o.ticks, () => { if (e.isValid) setPose(e, 0); });
}
function slashVfx(dim, pos, dir, color, size, roll) {
  const v = spawnVfx(dim, 2, pos, { slot: slotOf(color), size, dir, life: 30 });
  vset(v, "ab:len", ((roll ?? Math.random() * 360) / 4.5) % 80);
  return v;
}
// Flying Dismantle slash: a thin glowing blade that cuts everything it passes.
function flyingSlash(src, t, o) {
  const dim = src.dimension;
  const { pos, dir } = handPos(src, t);
  const v = slashVfx(dim, pos, dir, o.color, o.size ?? 1.2, o.roll);
  let p = pos, d = 0;
  const hit = new Set();
  every(1, Math.ceil((o.range ?? 20) / 1.6), () => {
    p = V.add(p, V.mul(dir, 1.6)); d += 1.6;
    try { if (v && v.isValid) v.teleport(p); } catch (e) { /* ignore */ }
    fx(dim, "streak", p, o.color, 0.8, 0.2, { count: 2, speed: 3 });
    hitArea(src, p, 1.3, o.dmg, hit, { knock: 0.3 });
    if (o.carve) carve(dim, p, 1, 12);
    if (d >= (o.range ?? 20)) { killVfx(v); return false; }
  });
  later(Math.ceil((o.range ?? 20) / 1.6) + 2, () => killVfx(v));
}
// Cleave / slash marks appearing ON the target.
function slashMarks(e, t, color, n, dmg) {
  every(2, n, (i) => {
    if (!alive(t)) return false;
    const c = aim(t);
    const v = slashVfx(t.dimension, c, V.norm({ x: Math.random() - 0.5, y: Math.random() - 0.5, z: Math.random() - 0.5 }), color, 0.9 + Math.random() * 0.5, i * 47);
    later(4, () => killVfx(v));
    deal(e, t, dmg);
    fx(t.dimension, "flash", c, color, 1.2, 0.15);
    fx(t.dimension, "streak", c, C.white, 1, 0.25, { count: 6, speed: 7 });
  });
}
function conqueror(e, s) {
  busy(s, 16); setPose(e, 22);  // haki pouring out: fists clenched, braced
  const dim = e.dimension, c = V.up(e.location, 1);
  announce(e, "§4§lConqueror's Haki!");
  fx(dim, "shock", e.location, C.haki, 18, 0.8);
  fx(dim, "shock_v", c, C.haki, 10, 0.5);
  for (let k = 0; k < 14; k++) {
    const d = V.randSphere(); const p = V.add(c, V.mul({ x: d.x, y: Math.abs(d.y) * 0.4, z: d.z }, 2 + Math.random() * 6));
    fx(dim, "streak", p, k % 2 ? C.haki : C.black, 2.2, 0.35, { count: 4, speed: 10 });
  }
  shake(dim, c, 0.35, 0.5);
  const mine = powerOf(e);
  let list = [];
  try { list = dim.getEntities({ location: c, maxDistance: 14 }); } catch (err) { /* ignore */ }
  for (const o of list) {
    if (!canHit(e, teamOf(e), o)) continue;
    const ratio = powerOf(o) / mine;
    if (ratio < 0.35 && !isFighter(o)) { deal(e, o, 999, true); continue; }  // weak-willed creatures faint
    if (ratio < 0.8) { if (isFighter(o)) state(o).stunUntil = now() + 30; slow(o, 30, 255); deal(e, o, 20 * mine / 100); }
  }
  later(14, () => setPose(e, 0));
}

// ------------------------------------------------------------------ Itadori Yuji (three versions)
const yujiCommon = (bf) => ({
  id: "blackflash", label: "Black Flash", cd: 260, cost: 120, min: 0, max: 8, weight: 4,
  run(e, s, t) {
    busy(s, 12); setPose(e, 5);
    if (V.dist(e.location, t.location) > 2.2) teleportNear(e, t, false, 1.3);
    later(3, () => {
      if (!alive(t)) return;
      const hitBF = Math.random() < bf;
      deal(e, t, (hitBF ? 2.5 : 1) * 22 * powerOf(e) / 100);
      const c = aim(t);
      fx(e.dimension, "orb_solid", c, C.black, hitBF ? 2.2 : 1, 0.35);
      fx(e.dimension, "streak", c, hitBF ? C.red : C.ce, 1.8, 0.4, { count: hitBF ? 22 : 10, speed: 12 });
      fx(e.dimension, "streak", c, C.black, 1.6, 0.4, { count: hitBF ? 16 : 6, speed: 9 });
      if (hitBF) { fx(e.dimension, "shock_v", c, C.red, 5, 0.35); shake(e.dimension, c, 0.3, 0.3); announce(e, "§0§l§kX§r §4§lBlack Flash §0§l§kX"); }
      try { const n = V.norm(V.sub(t.location, e.location)); t.applyKnockback({ x: n.x * 2.2, z: n.z * 2.2 }, 0.35); } catch (err) { /* ignore */ }
      setPose(e, 0);
    });
  },
});
const divergent = {
  id: "divergent", label: "Divergent Fist", cd: 120, cost: 50, min: 0, max: 5, weight: 4,
  run(e, s, t) {
    busy(s, 14); setPose(e, 5);
    if (V.dist(e.location, t.location) > 2.2) { afterimage(e); teleportNear(e, t, false, 1.4); }
    later(2, () => { if (!alive(t)) return; deal(e, t, 10 * powerOf(e) / 100); impact(e, t, false, C.ce); });
    later(8, () => {  // the delayed cursed-energy impact
      if (!alive(t)) return;
      deal(e, t, 14 * powerOf(e) / 100);
      fx(t.dimension, "shock_v", aim(t), C.ce, 3.5, 0.3);
      fx(t.dimension, "streak", aim(t), C.ce, 1.4, 0.35, { count: 12, speed: 9 });
      setPose(e, 0);
    });
  },
};
const YUJI = {
  name: "Itadori", color: "§d", energy: 600, regen: 10, energyName: "§dCE",
  dodge: () => 0.05,
  forms: [{ label: "Vessel", power: 35 }],
  thresholds: [], formSound: [null],
  abilities: [divergent, yujiCommon(0.2), {
    id: "manji", label: "Manji Kick", cd: 140, cost: 40, min: 0, max: 4, weight: 3,
    run(e, s, t) { stretch(e, s, t, { pose: 7, ticks: 8, reach: 2.6, dmg: 16, color: C.ce, knock: 1.6, strong: true }); },
  }, {
    // cursed energy hits within 0.000001 s of the punch: space bends and the blow lands at 2.5x
    id: "blackflash", label: "Black Flash", cd: 240, cost: 120, min: 0, max: 10, weight: 4,
    run(e, s, t) {
      busy(s, 14); afterimage(e); teleportNear(e, t, false, 1.3); face(e, aim(t)); setPose(e, 5);
      announce(e, "§0§l§kX§r §4§lBlack Flash! §0§l§kX");
      const c = aim(t), dim = e.dimension;
      deal(e, t, 2.5 * 14 * powerOf(e) / 100);
      fx(dim, "orb_solid", c, C.black, 1.8, 0.35);
      fx(dim, "streak", c, C.red, 1.8, 0.4, { count: 18, speed: 12 });
      fx(dim, "shock_v", c, C.red, 3.6, 0.3);
      burst(dim, c, C.black, 16, 4, 0.4, 0.45);
      shake(dim, c, 0.35, 0.35);
      later(8, () => { if (e.isValid) setPose(e, 0); });
    },
  }],
};
const YUJI_FINAL = {
  name: "Itadori", color: "§c", energy: 1200, regen: 22, energyName: "§dCE",
  dodge: () => 0.12,
  forms: [{ label: "Modulo (2086)", power: 154, aura: C.blood }],
  thresholds: [], formSound: [null],
  abilities: [divergent, yujiCommon(0.6), {
    id: "bf7", label: "Black Flash x7", cd: 700, cost: 400, min: 0, max: 10, weight: 5,
    run(e, s, t) {
      busy(s, 30); announce(e, "§0§l§kX§r §4§lBlack Flash x7 §0§l§kX");
      every(4, 7, (i) => {
        if (!alive(t) || !e.isValid) return false;
        if (V.dist(e.location, t.location) > 2.4) teleportNear(e, t, i % 2 === 0, 1.3);
        face(e, aim(t)); setPose(e, i % 2 ? 6 : 5);
        deal(e, t, 2.5 * 9 * powerOf(e) / 100);
        const c = aim(t);
        fx(e.dimension, "orb_solid", c, C.black, 1.6, 0.3);
        fx(e.dimension, "streak", c, C.red, 1.6, 0.35, { count: 14, speed: 11 });
        fx(e.dimension, "shock_v", c, C.red, 3.5, 0.3);
        if (i === 6) { shake(e.dimension, c, 0.4, 0.4); setPose(e, 0); }
      });
    },
  }, {
    id: "dismantle", label: "Dismantle", cd: 120, cost: 120, min: 3, max: 24, weight: 4, technique: true,
    run(e, s, t) {
      busy(s, 14); setPose(e, 19); announce(e, "§c§lDismantle");
      every(3, 3, (i) => { if (!alive(t) || !e.isValid) return false; face(e, aim(t)); flyingSlash(e, t, { color: C.white, dmg: 16 * powerOf(e) / 100, range: 22, roll: 20 + i * 70, carve: true }); });
      later(12, () => setPose(e, 0));
    },
  }, {
    id: "cleave", label: "Cleave", cd: 220, cost: 160, min: 0, max: 4, weight: 4, technique: true,
    run(e, s, t) {
      busy(s, 16); setPose(e, 19); announce(e, "§c§lCleave");
      const h = health(t); const extra = h ? Math.min(8, h.effectiveMax * 0.01) : 0;  // Cleave adjusts to the target's toughness (capped)
      slashMarks(e, t, C.white, 5, (6 * powerOf(e) / 100) + extra);
      later(12, () => setPose(e, 0));
    },
  }, {
    id: "piercing", label: "Piercing Blood", cd: 200, cost: 140, min: 4, max: 40, weight: 3,
    run(e, s, t) {
      busy(s, 22); face(e, aim(t)); announce(e, "§4§lPiercing Blood");
      chargeOrb(e, t, 10, C.blood, 0.2, 0.6, 2);
      later(10, () => { if (!e.isValid) return; setPose(e, 1); beam(e, alive(t) ? t : e, { color: C.blood, width: 0.35, length: 40, dmg: 55 * powerOf(e) / 100, ticks: 3, blast: 1.2, pitch: 1.6 }); later(8, () => setPose(e, 0)); });
    },
  }, {
    id: "supernova", label: "Supernova", cd: 300, cost: 180, min: 3, max: 18, weight: 3,
    run(e, s, t) {
      busy(s, 20); setPose(e, 3); announce(e, "§4§lSupernova");
      const dim = e.dimension;
      const orbs = [0, 1, 2, 3, 4].map((k) => spawnVfx(dim, 1, V.up(e.location, 2.5), { slot: 12, size: 0.35, life: 40 }));
      every(1, 12, (i) => orbs.forEach((o, k) => {
        const a = k * 1.256 + i * 0.4;
        try { if (o && o.isValid) o.teleport(V.add(V.up(e.location, 2.2), { x: Math.cos(a) * 1.4, y: Math.sin(a * 2) * 0.3, z: Math.sin(a) * 1.4 })); } catch (err) { /* ignore */ }
      }));
      later(12, () => {
        orbs.forEach(killVfx); setPose(e, 4);
        for (let k = 0; k < 5; k++) later(k * 2, () => {
          if (!e.isValid) return;
          const tt = alive(t) ? t : e; const { pos, dir } = handPos(e, tt);
          projectile(e, V.add(pos, { x: (Math.random() - 0.5), y: Math.random() * 0.6, z: (Math.random() - 0.5) }), dir,
            { speed: 1.4, maxDist: 24, radius: 0.9, size: 0.7, color: C.blood, slot: 12, explode: { radius: 2, dmg: 14 * powerOf(e) / 100, color: C.blood, knock: 0.8 } });
        });
        later(12, () => setPose(e, 0));
      });
    },
  }, {
    id: "rct", label: "Reverse Cursed Technique", cd: 500, cost: 300, min: 0, max: 64, weight: 5,
    cond: (e, s, c) => c.hp < 0.95,
    run(e, s) { busy(s, 10); const h = health(e); if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + 110)); fx(e.dimension, "aura", e.location, C.heal, 1, 0.8, { count: 22, speed: 2 }); announce(e, "§aItadori: Reverse Cursed Technique"); },
  }, {
    id: "domain", label: "Domain Expansion", cd: 1800, cost: 700, min: 0, max: 12, weight: 6, technique: true,
    cond: () => true,
    run(e, s, t) {
      busy(s, 20); setPose(e, 21); announce(e, "§f§lItadori: Domain Expansion");
      const dim = e.dimension, center = V.up(e.location, 1);
      fx(dim, "shock", e.location, C.white, 26, 1.2);
      every(4, 25, (i) => {
        if (!e.isValid) return false;
        sphereFx(dim, center, 12, { red: 0.95, green: 0.9, blue: 0.75 }, 30, 1.2, "orb", 0.5);
        if (i % 5 === 0) {
          let list = []; try { list = dim.getEntities({ location: center, maxDistance: 12 }); } catch (err) { /* ignore */ }
          for (const o of list) if (canHit(e, teamOf(e), o)) { deal(e, o, 9 * powerOf(e) / 100, true); fx(dim, "flash", aim(o), C.white, 1.4, 0.2); }
        }
        if (i === 24) s.burnoutUntil = now() + 140;
      });
      later(18, () => setPose(e, 0));
    },
  }],
};
function mahoragaWheel(e) {
  if (!e.isValid) return;
  const c = V.up(e.location, 2.9);
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2 + now() * 0.05;
    for (let r = 0.2; r <= 0.8; r += 0.3) fx(e.dimension, "orb", { x: c.x + Math.cos(a) * r, y: c.y, z: c.z + Math.sin(a) * r }, C.gold, 0.18, 0.5);
  }
  fx(e.dimension, "shock", c, C.gold, 2.2, 0.5);
  sound(e.dimension, "block.bell.hit", c, 0.8, 0.6);
}
function worldSlash(e, s, t) {
  busy(s, 34); setPose(e, 21); slow(e, 30, 8);
  announce(e, "§f§lSukuna: §c§lWorld-Cutting Slash");
  const dim = e.dimension;
  later(18, () => {
    if (!e.isValid || !alive(t)) return;
    setPose(e, 19);
    const c = aim(t);
    const dir = V.norm(V.sub(c, aim(e)));
    for (let k = -3; k <= 3; k++) {
      const v = slashVfx(dim, V.add(c, V.mul(dir, k * 1.6)), dir, C.white, 3.2, 10);
      later(10, () => killVfx(v));
    }
    fx(dim, "flash", c, C.white, 6, 0.3);
    fx(dim, "streak", c, C.white, 3, 0.5, { count: 30, speed: 14 });
    shake(dim, c, 0.7, 0.6);
    deal(e, t, 160 * powerOf(e) / 100, true);  // cuts space itself: Infinity cannot stop it
    for (let k = 0; k < 10; k++) carve(dim, V.add(c, V.mul(dir, k - 5)), 1.3, 20);
    later(10, () => setPose(e, 0));
  });
}
const SUKUNA = {
  name: "Sukuna", color: "§4", energy: 1600, regen: 26, energyName: "§dCE",
  dodge: () => 0.1,
  forms: [
    { label: "In Yuji's body", power: 90, aura: C.haki },
    { label: "In Megumi's body (Ten Shadows)", power: 120, aura: C.haki },
    { label: "True Form (Heian)", power: 132, aura: C.blood },
  ],
  thresholds: [0.7, 0.4], transformCd: 120,
  formSound: [null, "mob.wither.spawn", "mob.enderdragon.growl"],
  abilities: [yujiCommon(0.2), {
    id: "dismantle", label: "Dismantle", cd: 90, cost: 100, min: 3, max: 26, weight: 5, technique: true,
    run(e, s, t) {
      busy(s, 16); setPose(e, 19); announce(e, formOf(e) === 2 ? "§4§lDismantle §7(four arms)" : "§4§lDismantle");
      every(2, 5 + formOf(e) * 3, (i) => { if (!alive(t) || !e.isValid) return false; face(e, aim(t)); flyingSlash(e, t, { color: C.white, dmg: 15 * powerOf(e) / 100, range: 24, roll: i * 37, carve: true }); });
      later(12, () => setPose(e, 0));
    },
  }, {
    id: "cleave", label: "Cleave", cd: 180, cost: 140, min: 0, max: 4, weight: 4, technique: true,
    run(e, s, t) { busy(s, 16); setPose(e, 19); announce(e, "§4§lCleave"); const h = health(t); slashMarks(e, t, C.red, 6, 6 * powerOf(e) / 100 + (h ? Math.min(9, h.effectiveMax * 0.012) : 0)); later(12, () => setPose(e, 0)); },
  }, {
    id: "fuga", label: "Fuga", cd: 700, cost: 500, min: 5, max: 40, weight: 4, technique: true,
    cond: () => true,
    run(e, s, t) {
      busy(s, 44); face(e, aim(t)); announce(e, "§6§l■ Open — Fuga");
      setPose(e, 20); slow(e, 30, 8);
      chargeOrb(e, t, 26, C.fire, 0.3, 1.4, 20);
      later(26, () => {
        if (!e.isValid) return;
        const tt = alive(t) ? t : e;
        beam(e, tt, { color: C.fire, width: 0.9 + formOf(e) * 0.4, length: 40, dmg: 120 * powerOf(e) / 100, ticks: 5, blast: 5 + formOf(e), carve: 2, pitch: 0.5 });
        later(6, () => { if (alive(tt)) { try { tt.setOnFire(8, true); } catch (err) { /* ignore */ } } });
        later(10, () => setPose(e, 0));
      });
    },
  }, {
    id: "rct", label: "Reverse Cursed Technique", cd: 400, cost: 250, min: 0, max: 64, weight: 5,
    cond: (e, s, c) => c.hp < 0.95,
    run(e, s) { busy(s, 10); const h = health(e); if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + 150)); fx(e.dimension, "aura", e.location, C.heal, 1, 0.8, { count: 22, speed: 2 }); },
  }, {
    id: "worldslash", label: "World-Cutting Slash", cd: 900, cost: 600, min: 0, max: 30, weight: 6, technique: true,
    cond: (e) => formOf(e) >= 1,
    run: (e, s, t) => worldSlash(e, s, t),
  }, {
    id: "shrine", label: "Malevolent Shrine", cd: 1800, cost: 800, min: 0, max: 14, weight: 7, technique: true,
    cond: () => true,
    run(e, s) {
      busy(s, 24); setPose(e, 21);
      announce(e, "§4§lDomain Expansion: §c§lMalevolent Shrine");
      const dim = e.dimension, center = V.up(e.location, 1), R = 13;
      sound(dim, "mob.warden.sonic_boom", center, 2, 0.4);
      fx(dim, "shock", e.location, C.blood, R * 2.4, 1.4);
      shake(dim, center, 0.5, 1);
      every(3, 40, (i) => {
        if (!e.isValid) return false;
        sphereFx(dim, center, R, C.blood, 16, 1.6, "orb_solid", 0.5);
        for (let k = 0; k < 2; k++) {
          const p = V.add(center, { x: (Math.random() - 0.5) * R * 1.6, y: Math.random() * 3 - 0.5, z: (Math.random() - 0.5) * R * 1.6 });
          const v = slashVfx(dim, p, V.norm({ x: Math.random() - 0.5, y: (Math.random() - 0.5) * 0.4, z: Math.random() - 0.5 }), C.white, 1.4);
          later(4, () => killVfx(v));
          if (Math.random() < 0.3) carve(dim, p, 1.2, 10);
        }
        if (i % 2 === 0) {
          let list = []; try { list = dim.getEntities({ location: center, maxDistance: R }); } catch (err) { /* ignore */ }
          for (const o of list) if (canHit(e, teamOf(e), o)) { deal(e, o, 5 * powerOf(e) / 100, true); fx(dim, "flash", aim(o), C.white, 1, 0.12); }
        }
        if (i === 39) s.burnoutUntil = now() + 140;
      });
      later(20, () => setPose(e, 0));
    },
  }],
};

// ------------------------------------------------------------------ Monkey D. Luffy (all gears)
// forms: 0 base, 1 Gear 2, 2 Gear 3, 3 Gear 4 Boundman, 4 Gear 4 Snakeman, 5 Gear 4 Tankman, 6 Gear 5
const G = (...f) => (e) => f.includes(formOf(e));
const LUFFY = {
  name: "Luffy", color: "§c", energy: 1100, regen: 20, energyName: "§6HAKI",
  dodge: (e) => (formOf(e) === 6 ? 0.15 : formOf(e) === 4 ? 0.2 : 0.08),
  forms: [
    { label: "Base", power: 55 },
    { label: "Gear 2", power: 70, aura: C.steam },
    { label: "Gear 3", power: 76 },
    { label: "Gear 4: Boundman", power: 110, aura: C.steam },
    { label: "Gear 4: Snakeman", power: 115, aura: C.steam },
    { label: "Gear 4: Tankman", power: 100, aura: C.steam },
    { label: "Gear 5", power: 170, aura: C.nika },
  ],
  thresholds: [0.92, 0.82, 0.7, 0.5, 0.5, 0.5],
  transformCd: 70,
  nextForm: (f) => (f === 2 ? 3 + Math.floor(Math.random() * 3) : f >= 3 && f <= 5 ? 6 : f + 1),
  formSound: [null, "random.fizz", "random.fizz", "mob.enderdragon.growl", "mob.enderdragon.growl", "mob.enderdragon.growl", "ambient.weather.thunder"],
  abilities: [
    { id: "pistol", label: "Gum-Gum Pistol", cd: 70, cost: 30, min: 2, max: 7, weight: 4, cond: G(0, 1),
      run(e, s, t) { const jet = formOf(e) === 1; stretch(e, s, t, { pose: 13, ticks: 8, reach: 6.5, dmg: jet ? 22 : 14, color: jet ? C.steam : C.white, knock: 1.4, strong: jet, say: jet ? "§c§lJet Pistol!" : "§c§lGum-Gum Pistol!" }); } },
    { id: "gatling", label: "Gum-Gum Gatling", cd: 130, cost: 60, min: 1, max: 6, weight: 4, cond: G(0, 1, 2),
      run(e, s, t) { const jet = formOf(e) === 1; stretch(e, s, t, { pose: 14, ticks: 22, hits: 10, every: 2, reach: 5, dmg: jet ? 5 : 3.5, color: jet ? C.steam : C.white, knock: 0.15, say: jet ? "§c§lJet Gatling!" : "§c§lGum-Gum Gatling!" }); } },
    { id: "bazooka", label: "Gum-Gum Bazooka", cd: 160, cost: 60, min: 1, max: 5, weight: 3, cond: G(0, 1, 2),
      run(e, s, t) { stretch(e, s, t, { pose: 15, ticks: 10, reach: 4.5, dmg: 20, color: C.white, knock: 3.2, lift: 0.5, strong: true, say: "§c§lGum-Gum Bazooka!" }); } },
    { id: "whip", label: "Gum-Gum Whip", cd: 110, cost: 30, min: 0, max: 5, weight: 3, cond: G(0, 1, 2, 6),
      run(e, s, t) { stretch(e, s, t, { pose: 17, ticks: 8, reach: 4.5, radius: 1.6, dmg: formOf(e) === 6 ? 30 : 13, color: C.white, knock: 2, strong: true, say: formOf(e) === 6 ? "§f§lGum-Gum Dawn Whip!" : "§c§lGum-Gum Whip!" }); } },
    { id: "elephant", label: "Elephant Gun", cd: 220, cost: 150, min: 1, max: 6, weight: 5, cond: G(2),
      run(e, s, t) { stretch(e, s, t, { pose: 16, ticks: 14, reach: 5.5, radius: 2.2, dmg: 48, color: C.haki, knock: 3, lift: 0.4, strong: true, ground: true, say: "§8§lGum-Gum Elephant Gun!" }); } },
    { id: "kong", label: "Kong Gun", cd: 240, cost: 200, min: 1, max: 9, weight: 5, cond: G(3),
      run(e, s, t) {
        stretch(e, s, t, { pose: 16, ticks: 14, reach: 8, radius: 2.4, dmg: 70, color: C.haki, knock: 4, lift: 0.5, strong: true, say: "§4§lGum-Gum Kong Gun!" });
        later(4, () => { if (alive(t)) explosion(e, aim(t), { radius: 3, dmg: 20 * powerOf(e) / 100, color: C.haki, slot: 13, carve: 1, knock: 2 }); });
      } },
    { id: "leo", label: "Leo Bazooka", cd: 200, cost: 150, min: 0, max: 5, weight: 4, cond: G(3),
      run(e, s, t) { stretch(e, s, t, { pose: 15, ticks: 12, reach: 4.5, radius: 1.8, dmg: 45, color: C.haki, knock: 4.5, lift: 0.5, strong: true, say: "§4§lGum-Gum Leo Bazooka!" }); } },
    { id: "bound", label: "Bound", cd: 120, cost: 60, min: 3, max: 18, weight: 3, cond: G(3),
      run(e, s, t) {  // bouncing leap and slam
        busy(s, 16); afterimage(e);
        try { e.applyKnockback({ x: 0, z: 0 }, 1.2); } catch (err) { /* ignore */ }
        later(10, () => { if (!alive(t) || !e.isValid) return; teleportNear(e, t, false, 1.5); explosion(e, t.location, { radius: 3, dmg: 30 * powerOf(e) / 100, color: C.haki, slot: 13, knock: 2.2 }); });
      } },
    { id: "cobra", label: "King Cobra", cd: 220, cost: 180, min: 2, max: 14, weight: 5, cond: G(4),
      run(e, s, t) {
        stretch(e, s, t, { pose: 13, ticks: 10, reach: 12, radius: 1.2, dmg: 60, color: C.haki, knock: 3, strong: true, say: "§4§lGum-Gum King Cobra!" });
        const { pos } = handPos(e, t);
        for (let k = 0; k < 10; k++) fx(e.dimension, "orb", V.add(pos, { x: Math.sin(k * 0.8) * 1.2, y: Math.cos(k * 0.5) * 0.4, z: 0 }), C.haki, 0.6, 0.4);
      } },
    { id: "python", label: "Python", cd: 160, cost: 120, min: 1, max: 10, weight: 4, cond: G(4),
      run(e, s, t) { stretch(e, s, t, { pose: 14, ticks: 18, hits: 6, every: 3, reach: 9, radius: 1.2, dmg: 12, color: C.haki, knock: 0.6, say: "§4§lGum-Gum Black Mamba!" }); } },
    { id: "cannon", label: "Cannonball", cd: 160, cost: 120, min: 2, max: 14, weight: 4, cond: G(5),
      run(e, s, t) { busy(s, 14); afterimage(e); teleportNear(e, t, false, 1.2); later(2, () => { if (alive(t)) explosion(e, t.location, { radius: 3.5, dmg: 45 * powerOf(e) / 100, color: C.haki, slot: 13, knock: 4 }); }); announce(e, "§4§lGum-Gum Cannonball!"); } },
    { id: "conqueror", label: "Conqueror's Haki", cd: 900, cost: 200, min: 0, max: 14, weight: 3, cond: (e) => formOf(e) >= 2,
      run(e, s) { conqueror(e, s); } },
    { id: "bajrang", label: "Bajrang Gun", cd: 500, cost: 400, min: 2, max: 14, weight: 6, cond: G(6),
      run(e, s, t) {
        busy(s, 30); face(e, aim(t)); setPose(e, 18); slow(e, 26, 8);
        announce(e, "§f§lGum-Gum Bajrang Gun!");
        fx(e.dimension, "aura", e.location, C.nika, 1.4, 0.8, { count: 30, speed: 3 });
        later(18, () => {
          if (!alive(t) || !e.isValid) return;
          setPose(e, 16);
          explosion(e, t.location, { radius: 6, dmg: 150 * powerOf(e) / 100, color: C.nika, slot: 14, carve: 3, knock: 4 });
          fx(e.dimension, "shock", t.location, C.nika, 22, 1);
          later(8, () => setPose(e, 0));
        });
      } },
    { id: "lightning", label: "Grab Lightning", cd: 380, cost: 250, min: 5, max: 40, weight: 4, cond: G(6),
      run(e, s, t) {
        busy(s, 24); setPose(e, 3); announce(e, "§e§lLuffy grabs the lightning!");
        sound(e.dimension, "ambient.weather.thunder", e.location, 2, 1.4);
        chargeOrb(e, t, 12, C.flash, 0.4, 1.0, 3);
        later(12, () => { if (!e.isValid) return; setPose(e, 1); beam(e, alive(t) ? t : e, { color: C.flash, width: 0.8, length: 40, dmg: 90 * powerOf(e) / 100, ticks: 3, blast: 3.5, pitch: 1.8 }); later(8, () => setPose(e, 0)); });
      } },
    { id: "rubber", label: "Rubber Ground", cd: 360, cost: 200, min: 0, max: 12, weight: 4, cond: G(6),
      run(e, s) {
        busy(s, 14); setPose(e, 10); announce(e, "§f§lThe ground turns to rubber!");
        const dim = e.dimension;
        fx(dim, "shock", e.location, C.nika, 24, 1.1);
        let list = []; try { list = dim.getEntities({ location: e.location, maxDistance: 12 }); } catch (err) { /* ignore */ }
        for (const o of list) if (canHit(e, teamOf(e), o)) {
          try { o.applyKnockback({ x: 0, z: 0 }, 1.6); } catch (err) { /* ignore */ }
          deal(e, o, 25 * powerOf(e) / 100);
          for (let k = 0; k < 4; k++) fx(dim, "flash", V.up(o.location, 2.4 + k * 0.4), C.nika, 0.8, 0.5);
        }
        later(12, () => setPose(e, 0));
      } },
    { id: "gigant", label: "Gigant", cd: 1400, cost: 300, min: 0, max: 24, weight: 4, cond: G(6),
      run(e, s) {
        busy(s, 10); announce(e, "§f§lLuffy grows giant!");
        try { e.triggerEvent("ab:gigant_on"); } catch (err) { /* ignore */ }
        fx(e.dimension, "shock", e.location, C.nika, 14, 0.8);
        s.gigantUntil = now() + 200;
        later(200, () => { try { if (e.isValid) e.triggerEvent("ab:gigant_off"); } catch (err) { /* ignore */ } });
      } },
  ],
};


// ------------------------------------------------------------------ Roronoa Zoro (Santoryu)
const ZORO = {
  name: "Zoro", color: "§a", energy: 1100, regen: 20, energyName: "§aSTAMINA",
  dodge: () => 0.12,
  forms: [
    { label: "Three Sword Style", power: 95 },
    { label: "King of Hell", power: 146, aura: C.haki },
  ],
  thresholds: [0.6], transformCd: 100,
  formSound: [null, "mob.wither.spawn"],
  abilities: [
    { id: "onigiri", label: "Oni Giri", cd: 120, cost: 60, min: 0, max: 8, weight: 4,
      run(e, s, t) {
        busy(s, 12); announce(e, "§a§lSantoryu: Oni Giri!"); setPose(e, 1); afterimage(e);
        teleportNear(e, t, true, 1.6);
        later(2, () => { if (alive(t)) slashMarks(e, t, formOf(e) ? C.haki : C.zoro, 3, 9 * powerOf(e) / 100); });
        later(10, () => setPose(e, 0));
      } },
    { id: "tatsumaki", label: "Tatsumaki", cd: 220, cost: 120, min: 0, max: 6, weight: 3,
      run(e, s, t) {
        busy(s, 24); announce(e, "§a§lSantoryu: Tatsumaki!"); setPose(e, 24);
        const dim = e.dimension;
        every(2, 11, (i) => {
          if (!e.isValid) return false;
          const c = V.up(e.location, 1);
          for (let k = 0; k < 3; k++) {
            const a = i * 0.9 + k * 2.09;
            const v = slashVfx(dim, V.add(c, { x: Math.cos(a) * 2.2, y: i * 0.25, z: Math.sin(a) * 2.2 }), { x: -Math.sin(a), y: 0.3, z: Math.cos(a) }, C.zoro, 0.8, 0);
            later(3, () => killVfx(v));
          }
          fx(dim, "aura", e.location, C.zoro, 1, 0.5, { count: 10, speed: 3 });
          let list = []; try { list = dim.getEntities({ location: c, maxDistance: 5 }); } catch (err) { /* ignore */ }
          for (const o of list) if (canHit(e, teamOf(e), o)) { deal(e, o, 4 * powerOf(e) / 100); try { o.applyKnockback({ x: 0, z: 0 }, 0.35); } catch (err) { /* ignore */ } }
          if (i === 10) setPose(e, 0);
        });
      } },
    { id: "phoenix", label: "36 Pound Phoenix", cd: 140, cost: 80, min: 0, max: 30, weight: 4,
      run(e, s, t) {
        busy(s, 14); setPose(e, 19); announce(e, "§a§lSanjuroku Pound Ho!");
        flyingSlash(e, t, { color: formOf(e) ? C.haki : C.zoro, dmg: 30 * powerOf(e) / 100, range: 28, roll: 10, carve: true, size: 1.5 });
        later(8, () => { if (e.isValid) flyingSlash(e, t, { color: C.zoro, dmg: 18 * powerOf(e) / 100, range: 26, roll: 170, size: 1.2 }); setPose(e, 0); });
      } },
    { id: "shishi", label: "Shishi Sonson", cd: 160, cost: 70, min: 0, max: 10, weight: 4,
      run(e, s, t) {
        busy(s, 12); announce(e, "§a§lShishi Sonson!"); setPose(e, 19); afterimage(e);
        teleportNear(e, t, true, 2);
        later(1, () => {
          if (!alive(t)) return;
          deal(e, t, 45 * powerOf(e) / 100);
          const v = slashVfx(t.dimension, aim(t), V.norm(V.sub(aim(t), aim(e))), C.white, 2.2, 0);
          later(5, () => killVfx(v));
          fx(t.dimension, "flash", aim(t), C.zoro, 3, 0.2);
          setPose(e, 0);
        });
      } },
    { id: "asura", label: "Kyutoryu Asura", cd: 600, cost: 300, min: 0, max: 12, weight: 5,
      run(e, s, t) {
        busy(s, 34); setPose(e, 21); announce(e, "§2§lKyutoryu: §4§lAsura — Ichibugin!");
        const dim = e.dimension;
        every(2, 8, () => {  // the three-headed, six-armed demon illusion
          if (!e.isValid) return false;
          for (const sx of [-1.4, 0, 1.4]) fx(dim, "orb_solid", V.add(e.location, { x: sx, y: 2.6, z: 0 }), C.haki, 0.9, 0.4);
          for (const sx of [-2, -1.6, -1.2, 1.2, 1.6, 2]) fx(dim, "orb", V.add(e.location, { x: sx, y: 1.6 + Math.abs(sx) * 0.2, z: 0 }), C.zoro, 0.5, 0.4);
          fx(dim, "aura", e.location, C.haki, 1.4, 0.6, { count: 12, speed: 2 });
        });
        later(16, () => {
          if (!e.isValid || !alive(t)) return;
          afterimage(e); teleportNear(e, t, true, 2); setPose(e, 1);
          slashMarks(e, t, C.zoro, 9, 10 * powerOf(e) / 100);
          later(16, () => setPose(e, 0));
        });
      } },
    { id: "rengoku", label: "Purgatory Oni Giri", cd: 280, cost: 180, min: 0, max: 12, weight: 5, cond: (e) => formOf(e) === 1,
      run(e, s, t) {
        busy(s, 16); setPose(e, 1); announce(e, "§4§lSantoryu: Rengoku Oni Giri! §7— Purgatory");
        afterimage(e); teleportNear(e, t, true, 1.8);
        later(2, () => {
          if (!alive(t) || !e.isValid) return;
          setPose(e, 19);
          slashMarks(e, t, C.haki, 3, 15 * powerOf(e) / 100);
          fx(t.dimension, "aura", t.location, C.fire, 1.6, 0.7, { count: 18, speed: 2.5 });   // the slashes leave dark flames behind
          every(8, 4, () => { if (alive(t)) { deal(e, t, 3 * powerOf(e) / 100); fx(t.dimension, "orb_solid", V.up(t.location, 1.2), C.haki, 1.2, 0.5); } });
          later(10, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "sanzen", label: "Three Thousand Worlds", cd: 500, cost: 350, min: 0, max: 20, weight: 6, cond: (e) => formOf(e) === 1,
      run(e, s, t) {
        busy(s, 26); setPose(e, 1); announce(e, "§0§lKing of Hell — §4§lSanzen Sekai!");
        const dim = e.dimension;
        later(10, () => {
          if (!e.isValid || !alive(t)) return;
          const dir = V.norm(V.sub(aim(t), aim(e)));
          afterimage(e); teleportNear(e, t, true, 2.2); setPose(e, 19);  // the cut lands as he dashes through
          for (let k = -2; k <= 2; k++) { const v = slashVfx(dim, V.add(aim(t), V.mul(dir, k * 1.2)), dir, C.haki, 2.6, 30 + k * 25); later(8, () => killVfx(v)); }
          deal(e, t, 120 * powerOf(e) / 100);
          fx(dim, "flash", aim(t), C.white, 5, 0.25);
          fx(dim, "streak", aim(t), C.haki, 2.4, 0.5, { count: 26, speed: 13 });
          shake(dim, aim(t), 0.5, 0.5);
          later(8, () => setPose(e, 0));
        });
      } },
  ],
};

// ------------------------------------------------------------------ Frieza
const FRIEZA = {
  name: "Frieza", color: "§5", energy: 1300, regen: 22, energyName: "§bKI",
  dodge: () => 0.12,
  forms: [
    { label: "Final Form", power: 180 },
    { label: "Golden Frieza", power: 320, aura: C.gold },
  ],
  thresholds: [0.6], transformCd: 100,
  formSound: [null, "beacon.power"],
  abilities: [
    { id: "deathbeam", label: "Death Beam", cd: 60, cost: 40, min: 0, max: 40, weight: 4,
      run(e, s, t) {
        busy(s, 10); face(e, aim(t)); setPose(e, 4);
        beam(e, t, { color: C.death, width: 0.22 + formOf(e) * 0.1, length: 40, dmg: 28 * powerOf(e) / 100, ticks: 2, blast: 1.2, pitch: 2 });
        later(6, () => setPose(e, 0));
      } },
    { id: "barrage", label: "Death Beam Barrage", cd: 160, cost: 120, min: 0, max: 40, weight: 3,
      run(e, s, t) {
        busy(s, 16); setPose(e, 4); announce(e, "§5§lDeath Beam!");
        every(3, 5, () => { if (!alive(t) || !e.isValid) return false; face(e, aim(t)); beam(e, t, { color: C.death, width: 0.2, length: 40, dmg: 14 * powerOf(e) / 100, ticks: 2, blast: 0.8, pitch: 2.2 }); });
        later(15, () => setPose(e, 0));
      } },
    { id: "deathball", label: "Death Ball", cd: 600, cost: 400, min: 0, max: 40, weight: 4,
      run(e, s, t) {
        busy(s, 52); setPose(e, 23); slow(e, 44, 8); announce(e, "§6§lDeath Ball!");
        const dim = e.dimension;
        const ball = spawnVfx(dim, 1, V.up(e.location, 3.4), { slot: 11, size: 0.3, life: 60 });
        every(1, 40, (i) => { if (!e.isValid) { killVfx(ball); return false; } try { ball.teleport(V.up(e.location, 3.2 + i * 0.04)); } catch (err) { /* ignore */ } vset(ball, "ab:size", 0.3 + i * 0.09); });
        later(40, () => {
          killVfx(ball);
          if (!e.isValid) return;
          setPose(e, 4);
          const c = V.up(e.location, 4.8);
          const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 10));
          projectile(e, c, V.norm(V.sub(tgt, c)), { speed: 0.6, maxDist: 50, radius: 2.4, size: 5.6, color: C.fire, slot: 11, homing: t, homingStrength: 0.05,
            explode: { radius: 7, dmg: 220 * powerOf(e) / 100, color: C.fire, carve: 4, knock: 3 } });
          later(10, () => setPose(e, 0));
        });
      } },
    { id: "saucer", label: "Death Saucer", cd: 220, cost: 120, min: 0, max: 30, weight: 3,
      run(e, s, t) {
        busy(s, 14); setPose(e, 23); announce(e, "§d§lDeath Saucer!");
        later(6, () => { if (!e.isValid) return; setPose(e, 4);
          flyingSlash(e, t, { color: C.death, dmg: 40 * powerOf(e) / 100, range: 30, roll: 0, size: 1.3, carve: true });
          later(4, () => { if (e.isValid) flyingSlash(e, t, { color: C.death, dmg: 40 * powerOf(e) / 100, range: 30, roll: 0, size: 1.3 }); setPose(e, 0); }); });
      } },
    { id: "nova", label: "Nova Strike", cd: 200, cost: 150, min: 0, max: 25, weight: 3,
      run(e, s, t) {
        busy(s, 14); announce(e, "§5§lNova Strike!");
        fx(e.dimension, "aura", e.location, C.death, 1.4, 0.6, { count: 20, speed: 3 });
        every(1, 6, (i) => {
          if (!alive(t) || !e.isValid) return false;
          const step = V.add(e.location, V.mul(V.sub(t.location, e.location), 0.4));
          try { e.teleport(step, { facingLocation: aim(t) }); } catch (err) { /* ignore */ }
          fx(e.dimension, "orb", V.up(e.location, 1), C.death, 1.6, 0.4);
          if (i === 5) explosion(e, aim(t), { radius: 3, dmg: 50 * powerOf(e) / 100, color: C.death, slot: 15, knock: 3 });
        });
      } },
    { id: "telekinesis", label: "Telekinesis", cd: 260, cost: 140, min: 0, max: 30, weight: 3,
      run(e, s, t) {
        busy(s, 22); setPose(e, 4); announce(e, "§5Frieza lifts his enemy with telekinesis");
        try { t.applyKnockback({ x: 0, z: 0 }, 1.4); } catch (err) { /* ignore */ }
        every(2, 6, () => { if (alive(t)) fx(t.dimension, "orb", aim(t), C.death, 1.2, 0.3); });
        later(14, () => {
          if (!alive(t)) return;
          try { t.applyKnockback({ x: 0, z: 0 }, -2); } catch (err) { /* ignore */ }
          deal(e, t, 40 * powerOf(e) / 100);
          fx(t.dimension, "shock", t.location, C.death, 6, 0.5);
          setPose(e, 0);
        });
      } },
    { id: "goldbeam", label: "Golden Death Beam", cd: 300, cost: 250, min: 0, max: 45, weight: 5, cond: (e) => formOf(e) === 1,
      run(e, s, t) {
        busy(s, 22); face(e, aim(t)); setPose(e, 4); announce(e, "§6§lGolden Frieza: §5§lDeath Beam!");
        chargeOrb(e, t, 8, C.death, 0.2, 0.6, 4);
        later(8, () => { if (!e.isValid) return; beam(e, alive(t) ? t : e, { color: C.death, width: 0.8, length: 45, dmg: 120 * powerOf(e) / 100, ticks: 3, blast: 4, carve: 1, pitch: 1.6 }); later(8, () => setPose(e, 0)); });
      } },
  ],
};


// ------------------------------------------------------------------ Naruto (style 2: four ages)
function poof(e) {
  if (!e || !e.isValid) return;
  try {
    burst(e.dimension, V.up(e.location, 1), C.white, 18, 2.5, 0.6, 0.6);
    fx(e.dimension, "aura", e.location, C.white, 1.4, 0.7, { count: 14 * fxLevel(), speed: 1.5 });
    sound(e.dimension, "random.pop", e.location, 1, 0.8);
  } catch (err) { /* ignore */ }
  try { e.remove(); } catch (err) { /* ignore */ }
}
// Shadow Clone Jutsu: real fighters on the same team that vanish in smoke at the first hit.
function shadowClones(e, s, n, life = 220) {
  const team = teamOf(e);
  if (!team) return 0;
  s.clones = (s.clones ?? []).filter((c) => c.isValid);
  let made = 0;
  for (let i = 0; i < n && s.clones.length < 3; i++) {
    const a = Math.random() * Math.PI * 2;
    const pos = V.add(e.location, { x: Math.cos(a) * 1.8, y: 0, z: Math.sin(a) * 1.8 });
    let c;
    try { c = e.dimension.spawnEntity(e.typeId, pos); } catch (err) { break; }
    try {
      c.addTag("ab_clone");
      const cs = state(c);
      cs.cloneUntil = now() + life; cs.owner = e.id;
      setTeam(c, team);
      const f = formOf(e);
      if (f) c.triggerEvent(`ab:form_${f}`);
    } catch (err) { /* ignore */ }
    burst(e.dimension, V.up(pos, 1), C.white, 14, 2, 0.6, 0.6);
    s.clones.push(c);
    made++;
  }
  return made;
}
const cloneJutsu = (n, say = "§6§lShadow Clone Jutsu!") => ({
  id: "clones", label: "Shadow Clone Jutsu", cd: 360, cost: 120, min: 0, max: 30, weight: 3,
  run(e, s) {
    busy(s, 14); setPose(e, 35); announce(e, say);
    later(6, () => { if (e.isValid) shadowClones(e, s, n); });
    later(14, () => { if (e.isValid) setPose(e, 0); });
  },
});
function rasengan(e, s, t, o) {
  busy(s, 26); face(e, aim(t)); announce(e, o.say);
  chargeOrb(e, t, 12, o.color, 0.3, o.size, 36);
  later(12, () => {
    if (!e.isValid) return;
    if (!alive(t)) { setPose(e, 0); return; }
    afterimage(e); teleportNear(e, t, false, 1.3); face(e, aim(t)); setPose(e, 5);
    const c = aim(t), dim = e.dimension, pw = powerOf(e) / 100;
    deal(e, t, o.dmg * pw);
    const n = V.norm(V.sub(t.location, e.location));
    try { t.applyKnockback({ x: n.x * (o.knock ?? 2.5), z: n.z * (o.knock ?? 2.5) }, 0.45); } catch (err) { /* ignore */ }
    for (let k = 0; k < 28; k++) {  // the spiralling sphere grinding in
      const a = (k / 28) * Math.PI * 4, r = 0.25 + k * 0.05 * o.size;
      fx(dim, "orb", V.add(c, { x: Math.cos(a) * r, y: Math.sin(a * 0.5) * 0.35, z: Math.sin(a) * r }), o.color, 0.5, 0.4);
    }
    explosion(e, c, { radius: o.radius ?? 2, dmg: o.dmg * 0.25 * pw, color: o.color, knock: 1.5, carve: o.carve ?? 0 });
    later(8, () => { if (e.isValid) setPose(e, 0); });
  });
}
function rasenshuriken(e, s, t, o) {
  busy(s, 34); announce(e, o.say); setPose(e, 23); slow(e, 30, 6);
  const dim = e.dimension;
  const orb = spawnVfx(dim, 1, V.up(e.location, 3.3), { slot: 10, size: 0.3, life: 40 });
  every(1, 18, (i) => {
    if (!e.isValid) { killVfx(orb); return false; }
    const c = V.up(e.location, 3.3);
    try { if (orb && orb.isValid) orb.teleport(c); } catch (err) { /* ignore */ }
    vset(orb, "ab:size", 0.3 + i * 0.05 * o.size);
    for (let k = 0; k < 4; k++) {  // the four screaming wind blades
      const a = i * 0.8 + (k * Math.PI) / 2, r = 0.9 + o.size * 0.5;
      fx(dim, "streak", V.add(c, { x: Math.cos(a) * r, y: 0, z: Math.sin(a) * r }), C.white, 0.7, 0.2);
    }
    if (i === 17) killVfx(orb);
  });
  later(18, () => {
    if (!e.isValid) return;
    setPose(e, 4);
    const start = V.up(e.location, 3.3), pw = powerOf(e) / 100;
    const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 12));
    projectile(e, start, V.norm(V.sub(tgt, start)), {
      speed: 0.9, maxDist: 45, radius: 1.6, size: 1.8 * o.size, color: C.white, slot: 10, trail: true,
      homing: alive(t) ? t : undefined, homingStrength: 0.08,
      explode: { radius: o.radius, dmg: o.dmg * pw, color: C.white, carve: o.carve ?? 1, knock: 2 },
      onEnd: (pos) => {  // the wind sphere keeps slicing for a moment
        const dome = spawnVfx(dim, 1, pos, { slot: 10, size: o.radius * 0.5, life: 30 });
        every(4, 5, () => {
          hitArea(e, pos, o.radius, o.dmg * 0.08 * pw, new Set(), { knock: 0.2 });
          fx(dim, "streak", pos, C.white, 2, 0.3, { count: 10, speed: 9 });
        });
        later(22, () => fadeVfx(dome, o.radius * 0.5, 6));
      },
    });
    later(10, () => { if (e.isValid) setPose(e, 0); });
  });
}
function bijuudama(e, s, t, o) {
  busy(s, 44); face(e, aim(t)); announce(e, "§5§lTailed Beast Bomb!");
  chargeOrb(e, t, 26, C.hakai, 0.4, o.size ?? 3, 1);
  later(26, () => {
    if (!e.isValid) return;
    const { pos } = handPos(e, alive(t) ? t : e);
    const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 12));
    projectile(e, pos, V.norm(V.sub(tgt, pos)), {
      speed: 0.8, maxDist: 50, radius: 2.2, size: (o.size ?? 3) * 1.4, color: C.hakai, slot: 7,
      homing: alive(t) ? t : undefined, homingStrength: 0.05,
      explode: { radius: o.radius ?? 7, dmg: o.dmg * powerOf(e) / 100, color: C.hakai, carve: 3, knock: 3 },
    });
    later(10, () => { if (e.isValid) setPose(e, 0); });
  });
}
function rasenganAbility(id, label, o, cond) {
  return { id, label, cd: o.cd ?? 160, cost: o.cost ?? 90, min: 0, max: 30, weight: o.weight ?? 4, cond,
    run(e, s, t) { rasengan(e, s, t, o); } };
}
function shurikenAbility(id, label, o, cond) {
  return { id, label, cd: o.cd ?? 300, cost: o.cost ?? 220, min: 0, max: 45, weight: o.weight ?? 4, cond,
    run(e, s, t) { rasenshuriken(e, s, t, o); } };
}
const chakraArms = (color, cond) => ({
  id: "arms", label: "Chakra Arms", cd: 160, cost: 100, min: 0, max: 12, weight: 3, cond,
  run(e, s, t) {
    busy(s, 18); announce(e, "§6§lChakra Arms!"); afterimage(e); teleportNear(e, t, false, 2.2);
    punches(e, t, 6, 7 * powerOf(e) / 100, color);
    slashMarks(e, t, color, 3, 5 * powerOf(e) / 100);
  },
});

const NARUTO_KID = {
  name: "Naruto", color: "§6", energy: 600, regen: 12, energyName: "§6CHAKRA",
  dodge: () => 0.08,
  forms: [{ label: "Genin (Part I)", power: 25 }, { label: "Nine-Tails Cloak", power: 45, aura: C.fire }],
  thresholds: [0.6], transformCd: 100, formSound: [null, "mob.enderdragon.growl"],
  abilities: [
    cloneJutsu(2),
    { id: "rendan", label: "Uzumaki Barrage", cd: 220, cost: 90, min: 0, max: 10, weight: 4,
      run(e, s, t) {
        busy(s, 30); announce(e, "§6§lU! ZU! MA! KI! — Naruto Uzumaki Barrage!");
        shadowClones(e, s, 2, 100);
        later(4, () => {
          if (!alive(t) || !e.isValid) return;
          teleportNear(e, t, false, 1.2); setPose(e, 7);
          deal(e, t, 10 * powerOf(e) / 100);
          try { t.applyKnockback({ x: 0, z: 0 }, 1.1); } catch (err) { /* ignore */ }
          burst(e.dimension, aim(t), C.white, 12, 3, 0.4, 0.4);
        });
        later(14, () => {
          if (!alive(t) || !e.isValid) return;
          try { e.teleport(V.up(t.location, 3), { facingLocation: aim(t) }); } catch (err) { /* ignore */ }
          setPose(e, 10);
          deal(e, t, 16 * powerOf(e) / 100);
          try { t.applyKnockback({ x: 0, z: 0 }, -1.6); } catch (err) { /* ignore */ }
          fx(e.dimension, "shock", t.location, C.white, 4, 0.4);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    rasenganAbility("rasengan", "Rasengan", { say: "§b§lRasengan!", color: C.blue, size: 0.8, dmg: 28, radius: 1.6 }),
    { id: "claw", label: "Chakra Claw", cd: 120, cost: 60, min: 0, max: 8, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 12); announce(e, "§c§lThe Nine-Tails' claw!"); afterimage(e); teleportNear(e, t, false, 1.6);
        slashMarks(e, t, C.fire, 3, 9 * powerOf(e) / 100);
      } },
    { id: "roar", label: "Nine-Tails Roar", cd: 260, cost: 120, min: 0, max: 8, weight: 3, cond: G(1),
      run(e, s, t) {
        busy(s, 16); setPose(e, 22); announce(e, "§4§lRAAAAGH!");
        const dim = e.dimension;
        fx(dim, "shock", e.location, C.fire, 8, 0.5); ring(dim, V.up(e.location, 0.2), 4, C.fire, 28, 0.5);
        sound(dim, "mob.enderdragon.growl", e.location, 1.4, 1.3);
        hitArea(e, V.up(e.location, 1), 4.5, 14 * powerOf(e) / 100, new Set(), { knock: 2.5, lift: 0.4 });
        later(14, () => { if (e.isValid) setPose(e, 0); });
      } },
  ],
};

const NARUTO_TEEN = {
  name: "Naruto", color: "§6", energy: 900, regen: 16, energyName: "§6CHAKRA",
  dodge: () => 0.1,
  forms: [{ label: "Shippuden", power: 50 }, { label: "Sage Mode", power: 85, aura: C.kiYellow }],
  thresholds: [0.6], transformCd: 100, formSound: [null, "beacon.power"],
  abilities: [
    cloneJutsu(3, "§6§lMulti Shadow Clone Jutsu!"),
    rasenganAbility("rasengan", "Rasengan", { say: "§b§lRasengan!", color: C.blue, size: 1.0, dmg: 34, radius: 2 }),
    rasenganAbility("odama", "Big Ball Rasengan", { say: "§b§lBig Ball Rasengan!", color: C.blue, size: 1.8, dmg: 52, radius: 3.4, carve: 1, cd: 260, cost: 160 }),
    shurikenAbility("shuriken", "Rasenshuriken", { say: "§f§lSage Art: Rasenshuriken!", size: 1.0, dmg: 80, radius: 4.5, carve: 1 }, G(1)),
    { id: "kumite", label: "Frog Kumite", cd: 140, cost: 70, min: 0, max: 10, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 16); announce(e, "§e§lSage Art: Frog Kumite!"); afterimage(e); teleportNear(e, t, false, 1.6);
        punches(e, t, 5, 8 * powerOf(e) / 100, C.kiYellow);
        later(6, () => { if (alive(t)) hitArea(e, aim(t), 2.6, 8 * powerOf(e) / 100, new Set(), { knock: 1.8, lift: 0.3 }); });
      } },
  ],
};

const NARUTO_WAR = {
  name: "Naruto", color: "§e", energy: 1500, regen: 26, energyName: "§6CHAKRA",
  dodge: () => 0.14,
  forms: [
    { label: "Nine-Tails Chakra Mode", power: 120, aura: C.gold },
    { label: "Kurama Mode", power: 150, aura: C.gold },
    { label: "Six Paths Sage Mode", power: 182, aura: C.gold },
  ],
  thresholds: [0.7, 0.5], transformCd: 80, formSound: [null, "mob.enderdragon.growl", "beacon.power"],
  abilities: [
    cloneJutsu(3, "§6§lMulti Shadow Clone Jutsu!"),
    rasenganAbility("rasengan", "Flash Rasengan", { say: "§e§lRasengan!", color: C.blue, size: 1.4, dmg: 40, radius: 2.6, cd: 140 }),
    shurikenAbility("shuriken", "Rasenshuriken", { say: "§f§lRasenshuriken!", size: 1.2, dmg: 70, radius: 5, carve: 2 }),
    chakraArms(C.gold),
    { id: "bijuu", label: "Tailed Beast Bomb", cd: 520, cost: 380, min: 0, max: 45, weight: 5, cond: G(1, 2),
      run(e, s, t) { bijuudama(e, s, t, { size: 3, radius: 7, dmg: 150 }); } },
    { id: "kclaw", label: "Kurama's Claws", cd: 200, cost: 120, min: 0, max: 12, weight: 4, cond: G(1, 2),
      run(e, s, t) {
        busy(s, 16); announce(e, "§6§lKurama, lend me your power!"); afterimage(e); teleportNear(e, t, false, 2);
        slashMarks(e, t, C.gold, 5, 14 * powerOf(e) / 100);
        fx(e.dimension, "shock", t.location, C.gold, 6, 0.4);
      } },
    { id: "gudo", label: "Truth-Seeking Balls", cd: 260, cost: 200, min: 0, max: 40, weight: 4, cond: G(2),
      run(e, s, t) {
        busy(s, 24); setPose(e, 4); announce(e, "§0§lTruth-Seeking Balls!");
        every(3, 6, (i) => {
          if (!e.isValid || !alive(t)) return false;
          const start = V.add(V.up(e.location, 2.2), { x: Math.cos(i * 1.1) * 1.3, y: Math.sin(i * 1.7) * 0.6, z: Math.sin(i * 1.1) * 1.3 });
          projectile(e, start, V.norm(V.sub(aim(t), start)), { speed: 1.1, maxDist: 40, radius: 1, size: 0.9, color: C.black, slot: 13, solid: true,
            homing: t, homingStrength: 0.12, explode: { radius: 1.6, dmg: 18 * powerOf(e) / 100, color: C.black, knock: 1 } });
        });
        later(20, () => { if (e.isValid) setPose(e, 0); });
      } },
    shurikenAbility("ultra", "Six Paths Ultra Big Ball Rasenshuriken",
      { say: "§e§lSix Paths: Ultra Big Ball Rasenshuriken!", size: 2.6, dmg: 170, radius: 9, carve: 3, cd: 600, cost: 450, weight: 6 }, G(2)),
  ],
};

const NARUTO_ADULT = {
  name: "Naruto", color: "§6", energy: 1600, regen: 28, energyName: "§6CHAKRA",
  dodge: () => 0.14,
  forms: [
    { label: "Seventh Hokage", power: 125 },
    { label: "Kurama Link Mode", power: 165, aura: C.gold },
    { label: "Baryon Mode", power: 230, aura: C.blood },
  ],
  thresholds: [0.7, 0.4], transformCd: 80, formSound: [null, "mob.enderdragon.growl", "mob.wither.spawn"],
  abilities: [
    cloneJutsu(3, "§6§lMulti Shadow Clone Jutsu!"),
    rasenganAbility("rasengan", "Rasengan", { say: "§b§lRasengan!", color: C.blue, size: 1.4, dmg: 42, radius: 2.6, cd: 140 }),
    shurikenAbility("shuriken", "Rasenshuriken", { say: "§f§lRasenshuriken!", size: 1.4, dmg: 85, radius: 5.5, carve: 2 }),
    chakraArms(C.gold, G(1)),
    { id: "bijuu", label: "Tailed Beast Bomb", cd: 520, cost: 380, min: 0, max: 45, weight: 5, cond: G(1),
      run(e, s, t) { bijuudama(e, s, t, { size: 3.2, radius: 7.5, dmg: 160 }); } },
    { id: "baryon", label: "Baryon Punch", cd: 180, cost: 140, min: 0, max: 14, weight: 6, cond: G(2),
      run(e, s, t) {
        busy(s, 22); announce(e, "§c§lBaryon Mode: every blow burns away the enemy's life!");
        afterimage(e); teleportNear(e, t, true, 1.3);
        every(3, 5, (i) => {
          if (!alive(t) || !e.isValid) return false;
          face(e, aim(t)); setPose(e, i % 2 ? 6 : 5);
          deal(e, t, 14 * powerOf(e) / 100);
          fx(t.dimension, "orb", aim(t), C.blood, 1.6, 0.3);
          burst(t.dimension, aim(t), C.blood, 12, 3, 0.4, 0.4);
          if (i === 4) setPose(e, 0);
        });
        every(10, 6, () => {  // the drained life keeps burning
          if (!alive(t)) return false;
          deal(e, t, 4 * powerOf(e) / 100);
          fx(t.dimension, "aura", t.location, C.blood, 1, 0.5, { count: 6, speed: 1 });
        });
      } },
    { id: "baryonrush", label: "Baryon Rush", cd: 240, cost: 160, min: 0, max: 20, weight: 4, cond: G(2),
      run(e, s, t) {
        busy(s, 26); announce(e, "§4§lBaryon Mode!");
        every(4, 6, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.3); setPose(e, [5, 7, 6, 9, 5, 10][i]);
          deal(e, t, 11 * powerOf(e) / 100);
          fx(t.dimension, "shock_v", aim(t), C.blood, 3, 0.3);
          if (i === 5) { shake(t.dimension, aim(t), 0.4, 0.4); setPose(e, 0); }
        });
      } },
  ],
};

// ------------------------------------------------------------------ Sasuke (Shippuden)
const SASUKE = {
  name: "Sasuke", color: "§9", energy: 900, regen: 16, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) === 1 ? 0.18 : 0.14),  // the Sharingan reads the blow before it lands
  forms: [{ label: "Sharingan", power: 70 }, { label: "Mangekyo Sharingan — Susanoo", power: 98, aura: C.purple }],
  thresholds: [0.6], transformCd: 100, formSound: [null, "mob.wither.spawn"],
  abilities: [
    { id: "chidori", label: "Chidori", cd: 140, cost: 90, min: 0, max: 20, weight: 5,
      run(e, s, t) {
        busy(s, 22); face(e, aim(t)); announce(e, "§b§lChidori!");
        chargeOrb(e, t, 10, C.kameBlue, 0.4, 1.1, 4);
        every(2, 5, () => { if (e.isValid) fx(e.dimension, "streak", handPos(e, alive(t) ? t : e).pos, C.white, 0.8, 0.2, { count: 4, speed: 6 }); });
        later(10, () => {
          if (!e.isValid || !alive(t)) return;
          afterimage(e); teleportNear(e, t, false, 1.2); setPose(e, 5);
          const c = aim(t);
          deal(e, t, 34 * powerOf(e) / 100);
          fx(e.dimension, "streak", c, C.kameBlue, 1.8, 0.4, { count: 22, speed: 12 });
          fx(e.dimension, "flash", c, C.white, 3, 0.2);
          burst(e.dimension, c, C.kameBlue, 20, 4, 0.4, 0.4);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "fireball", label: "Great Fireball", cd: 160, cost: 90, min: 0, max: 30, weight: 4,
      run(e, s, t) {
        busy(s, 16); face(e, aim(t)); setPose(e, 21); announce(e, "§6§lFire Style: Great Fireball Technique!");
        later(8, () => {
          if (!e.isValid) return;
          setPose(e, 4);
          const { pos } = handPos(e, alive(t) ? t : e);
          const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 10));
          projectile(e, pos, V.norm(V.sub(tgt, pos)), { speed: 0.9, maxDist: 30, radius: 1.6, size: 2.4, color: C.fire, slot: 11, trail: true,
            explode: { radius: 3.5, dmg: 30 * powerOf(e) / 100, color: C.fire, carve: 1, knock: 1.6 } });
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "nagashi", label: "Chidori Current", cd: 200, cost: 100, min: 0, max: 5, weight: 3,
      run(e, s, t) {
        busy(s, 14); setPose(e, 22); announce(e, "§b§lChidori Current!");
        const dim = e.dimension;
        fx(dim, "shock", e.location, C.kameBlue, 7, 0.4);
        fx(dim, "streak", V.up(e.location, 1), C.white, 2, 0.4, { count: 26, speed: 10 });
        let list = []; try { list = dim.getEntities({ location: e.location, maxDistance: 4 }); } catch (err) { /* ignore */ }
        for (const o of list) {
          if (!canHit(e, teamOf(e), o)) continue;
          deal(e, o, 16 * powerOf(e) / 100);
          if (isFighter(o)) { const os = state(o); os.stunUntil = Math.max(os.stunUntil, now() + 16); }  // paralysed by the current
        }
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "kirin", label: "Kirin", cd: 700, cost: 400, min: 0, max: 40, weight: 5,
      run(e, s, t) {
        busy(s, 34); setPose(e, 23); announce(e, "§b§lKirin! §7— the lightning of the heavens");
        const dim = e.dimension;
        later(22, () => {
          if (!e.isValid || !alive(t)) return;
          const c = t.location;
          for (let y = 30; y > 0; y -= 1.5) fx(dim, "orb", V.add(c, { x: Math.sin(y) * 0.8, y, z: Math.cos(y) * 0.8 }), C.kameBlue, 2.2, 0.4);
          fx(dim, "flash", V.up(c, 2), C.white, 8, 0.3);
          explosion(e, V.up(c, 1), { radius: 5.5, dmg: 120 * powerOf(e) / 100, color: C.kameBlue, carve: 2, knock: 2.5 });
          shake(dim, c, 0.6, 0.6);
          later(6, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "amaterasu", label: "Amaterasu", cd: 400, cost: 220, min: 0, max: 30, weight: 5, cond: G(1),
      run(e, s, t) {
        busy(s, 14); face(e, aim(t)); setPose(e, 26); announce(e, "§0§lAmaterasu! §7— black flames that never go out");
        every(8, 12, () => {
          if (!alive(t)) return false;
          deal(e, t, 7 * powerOf(e) / 100);
          fx(t.dimension, "orb_solid", V.up(t.location, 1 + Math.random()), C.black, 1.6, 0.6);
          fx(t.dimension, "aura", t.location, C.black, 1.2, 0.7, { count: 8, speed: 1.5 });
        });
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "arrow", label: "Susanoo Arrow", cd: 260, cost: 200, min: 0, max: 45, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 20); face(e, aim(t)); setPose(e, 20); announce(e, "§5§lSusanoo!");
        later(10, () => {
          if (!e.isValid) return;
          const { pos } = handPos(e, alive(t) ? t : e);
          const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 12));
          projectile(e, pos, V.norm(V.sub(tgt, pos)), { speed: 2.2, maxDist: 50, radius: 1.4, size: 1.2, color: C.purple, slot: 6, pierce: true, trail: true,
            dmg: 60 * powerOf(e) / 100, explode: { radius: 3, dmg: 20 * powerOf(e) / 100, color: C.purple, knock: 2 } });
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
  ],
};

// ------------------------------------------------------------------ Ichigo Kurosaki (Bleach)
const ICHIGO = {
  name: "Ichigo", color: "§6", energy: 1600, regen: 28, energyName: "§bREIATSU",
  dodge: () => 0.12,
  forms: [
    { label: "Shikai — Zangetsu", power: 90 },
    { label: "Bankai — Tensa Zangetsu", power: 150, aura: C.black },
    { label: "Hollow Mask", power: 200, aura: C.red },
    { label: "Final Getsuga Tensho (Mugetsu)", power: 270, aura: C.black },
  ],
  thresholds: [0.75, 0.55, 0.35], transformCd: 80, formSound: [null, "mob.wither.spawn", "mob.enderdragon.growl", "mob.wither.spawn"],
  abilities: [
    { id: "getsuga", label: "Getsuga Tensho", cd: 110, cost: 70, min: 0, max: 30, weight: 5,
      run(e, s, t) {
        busy(s, 14); setPose(e, 19); announce(e, "§b§lGetsuga... TENSHO!");
        const col = formOf(e) ? C.haki : C.kameBlue;
        flyingSlash(e, t, { color: col, dmg: 30 * powerOf(e) / 100, range: 28, roll: 20, carve: true, size: 1.6 + formOf(e) * 0.3 });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "jujisho", label: "Getsuga Jujisho", cd: 220, cost: 130, min: 0, max: 28, weight: 4, cond: G(1, 2, 3),
      run(e, s, t) {
        busy(s, 16); setPose(e, 1); announce(e, "§4§lGetsuga Jujisho!");
        for (const roll of [45, -45]) flyingSlash(e, t, { color: C.haki, dmg: 28 * powerOf(e) / 100, range: 28, roll, carve: true, size: 1.8 });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "shunpo", label: "Flash Step", cd: 160, cost: 90, min: 0, max: 20, weight: 4, cond: G(1, 2, 3),
      run(e, s, t) {
        busy(s, 20); announce(e, "§f§lBankai speed!");
        every(4, 4, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.4); setPose(e, i % 2 ? 28 : 19);
          slashMarks(e, t, C.haki, 2, 6 * powerOf(e) / 100);
          if (i === 3) setPose(e, 0);
        });
      } },
    { id: "cero", label: "Cero", cd: 260, cost: 180, min: 0, max: 40, weight: 5, cond: G(2),
      run(e, s, t) {
        busy(s, 26); face(e, aim(t)); announce(e, "§4§lCero!");
        chargeOrb(e, t, 12, C.red, 0.3, 1.2, 4);
        later(12, () => {
          if (!e.isValid) return;
          beam(e, alive(t) ? t : e, { color: C.red, width: 1.3, length: 40, dmg: 70 * powerOf(e) / 100, carve: 1, blast: 3.5, ticks: 6 });
          later(14, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "mugetsu", label: "Mugetsu", cd: 900, cost: 700, min: 0, max: 40, weight: 7, cond: G(3),
      run(e, s, t) {
        busy(s, 40); setPose(e, 23); announce(e, "§0§lFinal Getsuga Tensho... §4§lMUGETSU");
        const dim = e.dimension;
        every(2, 10, (i) => { if (e.isValid) fx(dim, "aura", e.location, C.black, 2, 0.8, { count: 18, speed: 3 }); });
        later(20, () => {
          if (!e.isValid) return;
          setPose(e, 19);
          beam(e, alive(t) ? t : e, { color: C.black, width: 3.2, length: 48, dmg: 200 * powerOf(e) / 100, carve: 3, blast: 7, ticks: 10, pitch: 0.5 });
          later(20, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
  ],
};

// ------------------------------------------------------------------ Tanjiro Kamado (Demon Slayer)
const TANJIRO = {
  name: "Tanjiro", color: "§2", energy: 700, regen: 14, energyName: "§bBREATH",
  dodge: () => 0.1,
  forms: [{ label: "Water Breathing", power: 40 }, { label: "Sun Breathing — Demon Slayer Mark", power: 60, aura: C.fire }],
  thresholds: [0.6], transformCd: 100, formSound: [null, "mob.blaze.shoot"],
  abilities: [
    { id: "surface", label: "Water Surface Slash", cd: 90, cost: 40, min: 0, max: 12, weight: 4, cond: G(0),
      run(e, s, t) {
        busy(s, 12); announce(e, "§b§lWater Breathing, First Form: Water Surface Slash!");
        afterimage(e); teleportNear(e, t, false, 1.5); setPose(e, 19);
        const v = slashVfx(e.dimension, aim(t), V.norm(V.sub(aim(t), aim(e))), C.kameBlue, 1.6, 0);
        later(5, () => killVfx(v));
        deal(e, t, 20 * powerOf(e) / 100);
        burst(e.dimension, aim(t), C.kameBlue, 18, 3, 0.4, 0.5);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "wheel", label: "Water Wheel", cd: 130, cost: 60, min: 0, max: 10, weight: 4, cond: G(0),
      run(e, s, t) {
        busy(s, 14); announce(e, "§b§lSecond Form: Water Wheel!");
        afterimage(e); teleportNear(e, t, false, 1.5); setPose(e, 24);
        for (let k = 0; k < 4; k++) { const v = slashVfx(e.dimension, aim(t), { x: 0, y: 1, z: 0 }, C.kameBlue, 1.4, k * 45); later(5, () => killVfx(v)); }
        deal(e, t, 24 * powerOf(e) / 100);
        try { t.applyKnockback({ x: 0, z: 0 }, 0.9); } catch (err) { /* ignore */ }
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "flux", label: "Constant Flux", cd: 260, cost: 140, min: 0, max: 20, weight: 5, cond: G(0),
      run(e, s, t) {
        busy(s, 26); announce(e, "§b§lTenth Form: Constant Flux! §7— the water dragon");
        const dim = e.dimension;
        every(3, 7, (i) => {  // a flowing water dragon that hits harder with every turn
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.6); setPose(e, i % 2 ? 28 : 19);
          const v = slashVfx(dim, aim(t), V.norm(V.sub(aim(t), aim(e))), C.kameBlue, 1.2 + i * 0.15, i * 30);
          later(4, () => killVfx(v));
          deal(e, t, (5 + i * 1.5) * powerOf(e) / 100);
          for (let k = 0; k < 10; k++) fx(dim, "orb", V.add(aim(t), { x: Math.cos(k + i) * 1.4, y: (k - 5) * 0.2, z: Math.sin(k + i) * 1.4 }), C.kameBlue, 0.6, 0.5);
          if (i === 6) setPose(e, 0);
        });
      } },
    { id: "dance", label: "Hinokami Kagura: Dance", cd: 110, cost: 60, min: 0, max: 26, weight: 5, cond: G(1),
      run(e, s, t) {
        busy(s, 14); setPose(e, 19); announce(e, "§6§lHinokami Kagura: Dance!");
        flyingSlash(e, t, { color: C.fire, dmg: 26 * powerOf(e) / 100, range: 20, roll: 30, size: 1.6 });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "bluesky", label: "Clear Blue Sky", cd: 180, cost: 90, min: 0, max: 8, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 16); setPose(e, 24); announce(e, "§6§lHinokami Kagura: Clear Blue Sky!");
        const dim = e.dimension;
        ring(dim, V.up(e.location, 1), 3.5, C.fire, 32, 0.6); fx(dim, "shock", e.location, C.fire, 7, 0.4);
        hitArea(e, V.up(e.location, 1), 4, 24 * powerOf(e) / 100, new Set(), { knock: 1.6, lift: 0.4 });
        later(14, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "sunflower", label: "Sunflower Thrust", cd: 160, cost: 80, min: 0, max: 14, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 12); announce(e, "§6§lHinokami Kagura: Sunflower Thrust!");
        afterimage(e); teleportNear(e, t, false, 1.4); setPose(e, 5);
        deal(e, t, 34 * powerOf(e) / 100);
        fx(e.dimension, "flash", aim(t), C.fire, 3, 0.25); burst(e.dimension, aim(t), C.fire, 24, 5, 0.45, 0.5);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
  ],
};

const KI_CHARGERS = new Set(["ab:goku", "ab:vegeta", "ab:frieza"]);
const FIGHTERS = { "ab:goku": GOKU, "ab:vegeta": VEGETA, "ab:gojo": GOJO, "ab:yuji": YUJI, "ab:yuji_final": YUJI_FINAL, "ab:sukuna": SUKUNA, "ab:luffy": LUFFY, "ab:zoro": ZORO, "ab:frieza": FRIEZA,
  "ab:naruto_kid": NARUTO_KID, "ab:naruto_teen": NARUTO_TEEN, "ab:naruto_war": NARUTO_WAR, "ab:naruto_adult": NARUTO_ADULT,
  "ab:sasuke": SASUKE, "ab:ichigo": ICHIGO, "ab:tanjiro": TANJIRO };

// ------------------------------------------------------------------ melee combos
// Varied chains (jabs, kicks, roundhouse, knee, elbow, uppercut, rush barrage). Gojo blinks behind his target.
const MOVES = {
  jab_r: { pose: 5, t: 3, dmg: 8, kb: 0.3, arc: "punch" },
  jab_l: { pose: 6, t: 3, dmg: 8, kb: 0.3, arc: "punch" },
  kick: { pose: 7, t: 5, dmg: 13, kb: 1.1, lift: 0.25, arc: "front" },
  kick_r: { pose: 8, t: 6, dmg: 16, kb: 1.8, lift: 0.3, strong: true, arc: "right" },
  upper: { pose: 9, t: 5, dmg: 15, kb: 0.4, lift: 0.9, strong: true, arc: "up" },
  axe: { pose: 10, t: 7, dmg: 20, kb: 0.4, lift: -0.6, strong: true, arc: "down", ground: true },
  rush: { pose: 11, t: 16, dmg: 3.5, hits: 8, kb: 0.1, arc: "punch" },
  kick_l: { pose: 12, t: 6, dmg: 16, kb: 1.8, lift: 0.3, strong: true, arc: "left" },
  kiburst: { pose: 4, t: 7, ki: true, dmg: 24, kb: 2.6, strong: true },
  // sword cuts (Zoro): right-hand cut, left-hand cut, and the two-sword X cross-cut
  cut_r: { pose: 19, t: 3, dmg: 8, kb: 0.3, arc: "right", sword: true },
  cut_l: { pose: 28, t: 3, dmg: 8, kb: 0.3, arc: "left", sword: true },
  cut_x: { pose: 1, t: 5, dmg: 15, kb: 0.4, strong: true, arc: "front", sword: true },
  chop: { pose: 19, t: 3, dmg: 8, kb: 0.3, arc: "right", sword: true },  // Sukuna's knife-hand: the cut flies off the palm
  tail: { pose: 33, t: 6, dmg: 16, kb: 1.8, lift: 0.3, strong: true, arc: "left" },  // Frieza's tail lash
  blink: { tp: "behind", t: 3 },
  blinkfront: { tp: "front", t: 3 },
};
const COMBOS = {
  "ab:goku": [["jab_r", "jab_l", "jab_r", "rush", "kick_r", "axe"], ["rush", "kick_l", "kick_r", "upper", "axe"], ["jab_l", "jab_r", "rush", "rush", "kick_l"]],
  "ab:vegeta": [["jab_l", "jab_r", "rush", "kick_l", "kiburst"], ["jab_r", "jab_l", "jab_r", "kick_r", "axe", "kiburst"], ["rush", "axe", "kick_r"]],
  "ab:gojo": [["jab_r", "jab_l", "blink", "kick_l", "blinkfront", "rush", "axe"], ["rush", "blink", "kick_r", "blink", "axe"], ["jab_l", "jab_r", "jab_l", "blink", "kick_l"]],
  "ab:yuji": [["jab_r", "jab_l", "kick", "jab_r"], ["jab_l", "jab_r", "kick_r"], ["rush", "kick_l"]],
  "ab:yuji_final": [["jab_r", "chop", "rush", "kick_l", "upper"], ["jab_l", "jab_r", "chop", "kick_r", "axe"], ["rush", "rush", "kick_r"]],
  "ab:sukuna": [["chop", "kick_l", "rush", "upper"], ["jab_l", "chop", "kick_r", "axe"], ["rush", "kick_l", "kick_r"]],
  "ab:luffy": [["jab_r", "jab_l", "sgatling", "swhip"], ["jab_l", "spistol", "kick_r", "axe"], ["sgatling", "kick_l", "spistol"]],
  "ab:zoro": [["cut_r", "cut_l", "cut_r", "kick_r", "cut_x"], ["cut_l", "cut_r", "cut_l", "kick_l", "cut_x"], ["cut_r", "cut_l", "axe", "cut_x"]],
  "ab:naruto_kid": [["jab_r", "jab_l", "kick", "upper"], ["jab_l", "jab_r", "blink", "axe"], ["kick_r", "jab_r", "jab_l", "kick_l"]],
  "ab:naruto_teen": [["jab_r", "jab_l", "kick_r", "upper"], ["rush", "kick_l", "blink", "axe"], ["jab_l", "jab_r", "kick", "kick_r"]],
  "ab:naruto_war": [["jab_r", "jab_l", "rush", "kick_r", "kiburst"], ["blink", "jab_l", "jab_r", "upper", "axe"], ["rush", "kick_l", "kick_r", "kiburst"]],
  "ab:naruto_adult": [["jab_r", "jab_l", "rush", "kick_r", "kiburst"], ["blink", "jab_r", "kick_l", "upper", "axe"], ["rush", "jab_l", "kick_r", "kiburst"]],
  "ab:sasuke": [["cut_r", "cut_l", "kick_r", "upper"], ["jab_r", "jab_l", "blink", "axe"], ["cut_l", "cut_r", "kick_l", "cut_x"]],
  "ab:ichigo": [["cut_r", "cut_l", "cut_r", "cut_x"], ["cut_l", "blink", "cut_r", "kick_r", "cut_x"], ["cut_r", "cut_l", "axe", "cut_x"]],
  "ab:tanjiro": [["cut_r", "cut_l", "cut_r", "cut_x"], ["cut_l", "cut_r", "kick", "cut_x"], ["cut_r", "cut_l", "cut_l", "kick_r"]],
  "ab:frieza": [["jab_r", "tail", "rush", "kiburst"], ["kick", "jab_l", "jab_r", "axe"], ["rush", "kick_r", "kiburst"]],
};
MOVES.spistol = { pose: 13, t: 5, dmg: 12, kb: 1.4, strong: true, arc: "punch" };
MOVES.sgatling = { pose: 14, t: 16, dmg: 3, hits: 8, kb: 0.1, arc: "punch" };
MOVES.swhip = { pose: 17, t: 6, dmg: 15, kb: 2, lift: 0.3, strong: true, arc: "right" };
const BLACK_FLASH = { "ab:gojo": 0.25, "ab:yuji": 0.2, "ab:yuji_final": 0.45, "ab:sukuna": 0.2 };
const HIT_COLOR = { "ab:goku": C.kiYellow, "ab:vegeta": C.bigBang, "ab:gojo": C.blue, "ab:yuji": C.ce, "ab:yuji_final": C.blood, "ab:sukuna": C.red, "ab:luffy": C.white, "ab:zoro": C.zoro, "ab:frieza": C.death,
  "ab:naruto_kid": C.white, "ab:naruto_teen": C.blue, "ab:naruto_war": C.gold, "ab:naruto_adult": C.gold,
  "ab:sasuke": C.kameBlue, "ab:ichigo": C.kameBlue, "ab:tanjiro": C.kameBlue };

function combo(e, s, t) {
  const list = COMBOS[e.typeId];
  const seq = list[Math.floor(Math.random() * list.length)];
  let delay = 0;
  seq.forEach((k, i) => {
    const mv = MOVES[k];
    const last = i === seq.length - 1;
    later(delay + 1, () => comboStep(e, t, mv, last));
    delay += mv.t;
  });
  busy(s, delay + 4);
  later(delay + 2, () => { if (e.isValid) setPose(e, 0); });
}

function afterimage(e) {
  fx(e.dimension, "aura", e.location, C.white, 0.9, 0.35, { count: 10 * fxLevel(), speed: 0 });
}

// Visual impact: star flash, speed-line streaks, sparks; strong hits add a shockwave ring and camera shake.
function impact(e, t, strong, color, mv) {
  const dim = t.dimension;
  const c = V.add(aim(t), V.mul(V.norm(V.sub(aim(e), aim(t))), 0.45));
  fx(dim, "flash", c, C.white, strong ? 2.6 : 1.3, strong ? 0.22 : 0.14);
  fx(dim, "flash", c, color, strong ? 1.8 : 0.9, 0.18);
  fx(dim, "streak", c, color, strong ? 1.5 : 0.9, 0.35, { count: Math.ceil((strong ? 16 : 7) * fxLevel()), speed: strong ? 11 : 7 });
  burst(dim, c, color, strong ? 14 : 6, strong ? 5 : 3, 0.22, 0.3);
  if (strong) {
    fx(dim, "shock_v", c, color, 3.2, 0.35);
    shake(dim, c, 0.18, 0.2);
  }
  if (mv?.ground) {
    fx(dim, "shock", V.up(t.location, 0.1), color, 6, 0.5);
    fx(dim, "aura", t.location, { red: 0.4, green: 0.37, blue: 0.33 }, 1.2, 1.0, { count: 14 * fxLevel(), speed: 1 });
  }
  sound(dim, "random.anvil_land", c, 0.18, 2);
}

// Swing trails: an arc of light where the fist / leg travels.
function swingArc(e, t, kind, color) {
  if (!kind || kind === "punch") {
    const { pos, dir } = handPos(e, t);
    for (let k = 0; k < 4; k++) fx(e.dimension, "orb", V.add(pos, V.mul(dir, k * 0.35)), color, 0.35 - k * 0.05, 0.18);
    return;
  }
  const base = V.up(e.location, kind === "up" ? 1.2 : kind === "down" ? 1.6 : 0.9);
  const fwd = V.norm({ x: t.location.x - e.location.x, y: 0, z: t.location.z - e.location.z });
  const side = sideOf(fwd);
  for (let k = 0; k <= 10; k++) {
    const a = (k / 10) * Math.PI;
    let p;
    if (kind === "left" || kind === "right") {
      const sgn = kind === "left" ? 1 : -1;
      p = V.add(base, V.add(V.mul(side, Math.cos(a) * 1.3 * sgn), V.mul(fwd, Math.sin(a) * 1.3)));
    } else if (kind === "down") {
      p = V.add(base, V.add(V.mul(fwd, Math.sin(a) * 1.3), { x: 0, y: Math.cos(a) * 1.4, z: 0 }));
    } else {
      p = V.add(base, V.add(V.mul(fwd, Math.sin(a) * 1.2), { x: 0, y: -Math.cos(a) * 1.1, z: 0 }));
    }
    fx(e.dimension, "orb", p, color, 0.45, 0.25);
    if (k % 3 === 0) fx(e.dimension, "orb", p, C.white, 0.22, 0.2);
  }
}

function comboStep(e, t, mv, last) {
  if (!e.isValid || !alive(t)) { if (e.isValid) setPose(e, 0); return; }
  if (mv.tp) {
    afterimage(e);
    teleportNear(e, t, mv.tp === "behind", 1.3);
    return;
  }
  if (last) setExpr(e, 1, 12);  // battle cry on the finisher
  const d = V.dist(e.location, t.location);
  if (d > 2.3) {  // dash in (a fast step, not a teleport)
    afterimage(e);
    const n = V.norm(V.sub(t.location, e.location));
    try { e.tryTeleport(V.sub(t.location, V.mul({ x: n.x, y: 0, z: n.z }, 1.6)), { checkForBlocks: true, facingLocation: aim(t) }); } catch (err) { /* ignore */ }
  }
  face(e, aim(t));
  setPose(e, mv.pose);
  const pw = powerOf(e) / 100;
  const color = HIT_COLOR[e.typeId] ?? C.white;
  const hits = mv.hits ?? 1;
  for (let h = 0; h < hits; h++) {
    later(h * 2 + 1, () => {
      if (!alive(t) || !e.isValid) return;
      if (mv.ki) {
        fx(e.dimension, "orb", aim(t), C.bigBang, 2.2, 0.3);
        burst(e.dimension, aim(t), C.bigBang, 30, 6, 0.5, 0.6);
        sound(e.dimension, "mob.wither.shoot", t.location, 1, 1.4);
      }
      deal(e, t, mv.dmg * pw * (last ? 1.3 : 1));
      swingArc(e, t, mv.arc, color);
      if (mv.sword) {  // a visible blade streak across the target for every sword cut
        const sd = V.norm(V.sub(aim(t), aim(e)));
        for (const roll of mv.pose === 1 ? [45, -45] : [mv.pose === 28 ? -35 : 35]) {
          const sc = e.typeId === "ab:tanjiro" ? (formOf(e) ? C.fire : C.kameBlue) : (formOf(e) && (e.typeId === "ab:zoro" || e.typeId === "ab:ichigo") ? C.haki : color);
          const v = slashVfx(t.dimension, aim(t), sd, sc, 1.0, roll);
          later(4, () => killVfx(v));
        }
      }
      impact(e, t, mv.strong || last, color, mv);
      const n = V.norm(V.sub(t.location, e.location));
      const kb = mv.kb * (last ? 1.8 : 1);
      try { t.applyKnockback({ x: n.x * kb, z: n.z * kb }, Math.max(0, mv.lift ?? 0.08)); } catch (err) { /* ignore */ }
      if (isFighter(t) && !last) { const ts = state(t); ts.stunUntil = Math.max(ts.stunUntil, now() + 6); }
      if (last && Math.random() < (BLACK_FLASH[e.typeId] ?? 0)) {
        deal(e, t, 35 * pw);
        fx(e.dimension, "orb_solid", aim(t), C.black, 1.6, 0.4);
        burst(e.dimension, aim(t), C.red, 24, 5, 0.35, 0.45);
        burst(e.dimension, aim(t), C.black, 16, 4, 0.4, 0.45);
        announce(e, "§0§l§kX§r §4§lBlack Flash §0§l§kX");
      }
    });
  }
}



// ------------------------------------------------------------------ fighter brain
function updateFighter(e, tick) {
  const def = FIGHTERS[e.typeId];
  const s = state(e);
  if (s.cloneUntil && tick >= s.cloneUntil) { poof(e); return; }
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
  if (s.expr && tick >= s.exprUntil) {
    s.expr = 0;
    try { e.setProperty("ab:expr", 0); } catch (e2) { /* ignore */ }
  }
  if (e.typeId === "ab:gojo" && formOf(e) === 1 && team && tick % 50 === 0) {  // the Six Eyes glint
    try {
      const hp = e.getHeadLocation(), vd = e.getViewDirection();
      fx(e.dimension, "flash", { x: hp.x + vd.x * 0.32, y: hp.y + 0.05, z: hp.z + vd.z * 0.32 }, C.blue, 0.35, 0.2);
    } catch (err) { /* ignore */ }
  }
  if (!s.expr && tick % 70 === 0 && team) {  // worn out: below 20% health the fighter winces and staggers now and then
    const hh = health(e);
    if (hh && hh.currentValue < hh.effectiveMax * 0.2) setExpr(e, 2, 10);
  }

  if (!team) return;
  if (tick < s.stunUntil) {
    if (tick % 10 === 0) ring(e.dimension, V.up(e.location, 2.2), 0.5, C.white, 6, 0.15);
    return;
  }
  const target = nearestEnemy(e, team, 48);
  if (!target) return;
  if (tick - s.lastCombat > 100) s.combatSince = tick;
  s.lastCombat = tick;
  const ctx = { dist: V.dist(e.location, target.location), power: powerOf(e), tPower: powerOf(target), hp: hpPct(e),
    targetType: target.typeId, adaptTotal: Object.values(s.adapt ?? {}).reduce((a, b) => a + b, 0) };
  const form = formOf(e);
  // Look at the most the opponent can become, not just their current form.
  const tdef = FIGHTERS[target.typeId];
  const tMax = tdef ? Math.max(...tdef.forms.map((f) => f.power)) * (tdef.ego ? 1.1 : 1) : ctx.tPower;
  const threatened = Math.max(ctx.tPower, tMax) > ctx.power * 0.95;
  // Transform first, even mid-combo, when the opponent is stronger (or when badly hurt).
  if (!s.cloneUntil && form < def.forms.length - 1 && def.thresholds[form] !== undefined && tick >= s.nextTransform && tick >= s.transformUntil &&
      (threatened || (tick - s.combatSince > 40 && ctx.hp < def.thresholds[form]))) {
    let next = def.nextForm ? def.nextForm(form) : form + 1;
    if (threatened) {
      const need = Math.max(ctx.tPower, tMax) * 1.2;
      const match = def.forms.findIndex((f, i) => i > form && f.power >= need);
      next = match >= 0 ? match : def.forms.length - 1;
    }
    const nf = def.forms[next];
    transform(e, s, next, nf.label, nf.aura ?? C.white, def.formSound[next]);
    return;
  }
  if (tick < s.busyUntil) return;
  // Dragon Ball fighters stop to power up when their ki runs low: crouch, yell, aura surging
  if (KI_CHARGERS.has(e.typeId) && s.energy < def.energy * 0.2 && tick >= (s.nextCharge ?? 0)) {
    s.nextCharge = tick + 400;
    busy(s, 30); setPose(e, 22); setExpr(e, 1, 30);
    announce(e, `${def.color}§l${def.name} §r§fis charging ki!`);
    const ac = def.forms[clamp(formOf(e), 0, def.forms.length - 1)].aura ?? C.white;
    every(3, 10, () => {
      if (!e.isValid) return false;
      s.energy = Math.min(def.energy, s.energy + def.energy * 0.035);
      fx(e.dimension, "aura", e.location, ac, 1.3, 0.6, { count: 14 * fxLevel(), speed: 2 });
    });
    later(30, () => { if (e.isValid) setPose(e, 0); });
    return;
  }
  if (ctx.dist <= 6 && tick >= (s.cd.combo ?? 0) && Math.random() < 0.6) {
    s.cd.combo = tick + 45 + Math.floor(Math.random() * 40);
    combo(e, s, target);
    return;
  }
  if (s.cloneUntil || Math.random() > 0.45) return;  // shadow clones only brawl
  const burnt = tick < s.burnoutUntil;
  // Abilities are free to use at any range; close-range ones dash in first.
  const ok = def.abilities.filter((a) => (s.cd[a.id] ?? 0) <= tick && s.energy >= a.cost &&
    !(burnt && a.technique) && (!a.cond || a.cond(e, s, ctx)));
  if (!ok.length) return;
  let r = Math.random() * ok.reduce((n, a) => n + a.weight, 0);
  const pick = ok.find((a) => (r -= a.weight) <= 0) ?? ok[0];
  s.energy -= pick.cost;
  s.cd[pick.id] = tick + pick.cd;
  if (ctx.dist > pick.max) {
    afterimage(e);
    teleportNear(e, target, false, Math.max(1.4, Math.min(pick.max * 0.5, 3)));
    busy(s, 3);
    later(2, () => { if (e.isValid && alive(target)) pick.run(e, s, target, { ...ctx, dist: V.dist(e.location, target.location) }); });
    return;
  }
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
function ebar(pct) {
  const n = 12, full = Math.round(clamp(pct, 0, 1) * n);
  return `§b${"|".repeat(full)}§8${"|".repeat(n - full)}`;
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
    text = `${teamLabel(team)}${def.color}§l${def.name}§r §7(${form})${extra}\n${bar(pct)} §f${hp}§7/${max}\n${def.energyName} ${ebar(s.energy / def.energy)} §f${Math.max(0, Math.floor(s.energy))}`;
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
    if (tick % 20 === 0) {
      let vs = [];
      try { vs = dim.getEntities({ type: "ab:vfx" }); } catch (e) { /* ignore */ }
      for (const v of vs) { const exp = vfxAlive.get(v.id); if (exp === undefined || exp < tick) { vfxAlive.delete(v.id); try { v.remove(); } catch (e) { /* ignore */ } } }
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
    if (!def || cause === EntityDamageCause.fall) return;
    if (v.hasTag("ab_clone")) { ev.cancel = true; system.run(() => poof(v)); return; }  // a shadow clone: one hit and it's smoke
    const s = state(v);
    const attackerP = src && src.isValid && isFighter(src) ? powerOf(src) : 0;
    const defenderP = powerOf(v);
    if (attackerP > 0) {
      // Power decides the fight: a stronger fighter's blows land harder, a weaker one's barely scratch.
      ev.damage *= clamp(Math.pow(attackerP / defenderP, 3), 0.04, 6);
      if (now() < (s.transformUntil ?? 0)) ev.damage *= 0.25;  // the transformation aura pushes blows back
    }
    // Sure-hit techniques (domains, World-Cutting Slash) only force a hit on someone not far stronger.
    const forced = cause === EntityDamageCause.override && !(attackerP > 0 && defenderP > attackerP * 1.1);
    if (forced) { system.run(() => setExpr(v, 2, 10)); return; }
    if (def.infinity && v.hasTag("ab_infinity")) {
      // Infinity stops everything, but holding back stronger attacks costs more cursed energy.
      const attackerPower = src && src.isValid ? powerOf(src) : 50;
      const cost = ev.damage * 1.2 * Math.max(1, Math.pow(attackerPower / 100, 1.5));
      s.energy -= cost;
      if (s.energy >= 0) {
        ev.cancel = true;
        system.run(() => { if (v.isValid) ring(v.dimension, V.up(v.location, 1), 1.1, C.blue, 12, 0.2); });
        return;
      }
      const over = -s.energy / (1.2 * Math.max(1, Math.pow(attackerPower / 100, 1.5)));
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
    if (ev.damage > 1.5) system.run(() => setExpr(v, 2, ev.damage > 25 ? 14 : 8));
    if (def.ego && formOf(v) === def.ego) s.ego = Math.min(0.1, s.ego + ev.damage / 500);
    if (v.typeId === "ab:luffy" && formOf(v) === 5) ev.damage *= 0.5;  // Tankman: rubber fat absorbs blows
    if (v.typeId === "ab:sukuna" && formOf(v) >= 1 && src && src.isValid && !(attackerP > defenderP)) {  // Mahoraga's wheel adapts to each attacker
      s.adapt = s.adapt ?? {};
      const n = (s.adapt[src.id] ?? 0) + 1;
      s.adapt[src.id] = n;
      ev.damage *= 1 - Math.min(0.6, n * 0.03);
      if (n % 6 === 0) system.run(() => { mahoragaWheel(v); announce(v, "§6The wheel turns — Sukuna adapts"); });
    }
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
  if (ui && src && src.isValid && alive(src)) {  // Ultra Instinct: the body answers on its own
    later(2, () => {
      if (!v.isValid || !alive(src)) return;
      face(v, aim(src)); setPose(v, Math.random() < 0.5 ? 5 : 8);
      deal(v, src, 16 * powerOf(v) / 100);
      fx(v.dimension, "flash", aim(src), C.silver, 2.2, 0.2);
      burst(v.dimension, aim(src), C.silver, 14, 3, 0.35, 0.35);
      later(6, () => { if (v.isValid) setPose(v, 0); });
    });
    return;
  }
  const s = state(v);
  if (now() >= s.busyUntil) {  // visible sway, only when not in the middle of a technique
    setPose(v, 29);
    later(6, () => { if (v.isValid && now() >= state(v).busyUntil) setPose(v, 0); });
  }
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
    try { e.triggerEvent("ab:enter_combat"); e.setProperty("ab:stance", true); } catch (err) { /* ignore */ }
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
            try { e.setProperty("ab:stance", false); e.setProperty("ab:expr", 0); } catch (err) { /* ignore */ }
            e.triggerEvent("ab:form_0");
            if (e.typeId === "ab:luffy") e.triggerEvent("ab:gigant_off");
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
    if (def && teamOf(e)) announce(e, `${teamLabel(teamOf(e))}${def.color}§l${def.name} §r§fhas been defeated!`);
    if (def) { try { e.setProperty("ab:expr", 2); e.setProperty("ab:pose", 0); } catch (err) { /* ignore */ } }  // falls with a pained face
    const ds = states.get(e.id);
    if (ds && ds.clones) for (const c of ds.clones) poof(c);  // the original falls: every clone vanishes
    states.delete(e.id);
    // victory: the fighter who landed the last blow raises a fist with a shout
    const k = ev.damageSource && ev.damageSource.damagingEntity;
    if (k && k.isValid && FIGHTERS[k.typeId] && k.id !== e.id) {
      const ks = state(k);
      if (now() >= ks.busyUntil) {
        const vp = VICTORY[k.typeId] ?? 3;
        busy(ks, 22);
        setPose(k, vp);
        // the cool ones keep a straight, smug face; Frieza crosses his arms but laughs ("Ohohoho")
        if (!(vp === 0 || vp === 26 || (vp === 31 && k.typeId !== "ab:frieza"))) setExpr(k, 1, 22);
        later(22, () => { if (k.isValid && formOf(k) >= 0) setPose(k, 0); });
      }
    }
  } catch (err) { /* ignore */ }
});
world.afterEvents.entityRemove.subscribe((ev) => { states.delete(ev.removedEntityId); });

const VICTORY = { "ab:goku": 34, "ab:vegeta": 31, "ab:frieza": 31, "ab:luffy": 27, "ab:gojo": 26, "ab:sukuna": 21, "ab:zoro": 0, "ab:yuji_final": 0, "ab:sasuke": 0, "ab:ichigo": 0 };
// Entrance: a freshly spawned fighter strikes its signature pose with a shout before joining the fight.
const ENTRANCE = { "ab:goku": 22, "ab:vegeta": 22, "ab:frieza": 23, "ab:gojo": 26, "ab:yuji": 5, "ab:yuji_final": 19,
  "ab:sukuna": 21, "ab:luffy": 27, "ab:zoro": 1, "ab:naruto_kid": 35, "ab:naruto_teen": 35, "ab:naruto_war": 35, "ab:naruto_adult": 35,
  "ab:sasuke": 21, "ab:ichigo": 19, "ab:tanjiro": 19 };
world.afterEvents.entitySpawn.subscribe((ev) => {
  try {
    const e = ev.entity;
    if (!e || ENTRANCE[e.typeId] === undefined) return;
    later(4, () => {
      if (!e.isValid || e.hasTag("ab_clone")) return;
      const s = state(e);
      busy(s, 30);
      setPose(e, ENTRANCE[e.typeId]);
      setExpr(e, 1, 26);
      const c = HIT_COLOR[e.typeId] ?? C.white;  // arrival burst in the fighter's own colour
      ring(e.dimension, V.up(e.location, 0.1), 1.6, c, 24, 0.4);
      fx(e.dimension, "aura", e.location, c, 1.3, 0.6, { count: 18 * fxLevel(), speed: 2 });
      later(30, () => { if (e.isValid && now() >= state(e).busyUntil) setPose(e, 0); });
    });
  } catch (err) { /* ignore */ }
});

world.afterEvents.playerSpawn.subscribe((ev) => {
  try {
    const p = ev.player;
    if (!ev.initialSpawn || p.getDynamicProperty("ab:kit")) return;
    p.setDynamicProperty("ab:kit", true);
    const inv = p.getComponent("minecraft:inventory")?.container;
    for (const id of ["ab:team_stick", "ab:kill_stick", "ab:goku_spawn_egg", "ab:vegeta_spawn_egg", "ab:gojo_spawn_egg", "ab:yuji_spawn_egg", "ab:yuji_final_spawn_egg", "ab:sukuna_spawn_egg", "ab:luffy_spawn_egg", "ab:zoro_spawn_egg", "ab:frieza_spawn_egg", "ab:naruto_kid_spawn_egg", "ab:naruto_teen_spawn_egg", "ab:naruto_war_spawn_egg", "ab:naruto_adult_spawn_egg", "ab:sasuke_spawn_egg", "ab:ichigo_spawn_egg", "ab:tanjiro_spawn_egg"]) {
      try { inv?.addItem(new ItemStack(id, 1)); } catch (e) { warn("kit " + id, e); }
    }
    p.sendMessage("§6[Anime Battles] §fTeam Stick: hit = §cRED§f, next hit = §9BLUE§f. Sneak+use = reset.\n§4Kill Stick§f: hit = instant kill. Use = block damage on/off. Sneak+use = effects low/full.");
  } catch (e) { warn("kit", e); }
});

system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id === "ab:griefing") world.setDynamicProperty("ab:griefing", ev.message.trim() !== "off");
  if (ev.id === "ab:fx") world.setDynamicProperty("ab:fx", ev.message.trim() === "low" ? 0.5 : 1);
});
