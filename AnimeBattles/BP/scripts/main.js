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
const IGNORE_TYPES = new Set(["ab:vfx", "ab:summon", "minecraft:item", "minecraft:xp_orb", "minecraft:arrow", "minecraft:armor_stand", "minecraft:painting",
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
    v.setProperty("ab:size", clamp((o.size ?? 1) * VFX_SCALE, 0, 40));
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
// Giant summons (ab:summon): 0 Perfect Susanoo, 1 Kurama avatar, 2 Gamabunta. They grow out of a burst of chakra,
// act (pose 1 swing, 2 aim, 3 leap) and fade away; the cleanup loop removes any that outlive their time.
// kinds: 0 Perfect Susanoo, 1 Kurama, 2 Gamabunta, 3 Susanoo ribcage, 4 armoured Susanoo, 5 Muzan's giant infant form
const SUMMON_COLOR = [C.purple, C.gold, C.white, C.purple, C.purple, C.blood, C.white, C.blue];
function spawnSummon(dim, kind, at, dir, size, life) {
  const v = dim.spawnEntity("ab:summon", at);
  try { v.teleport(at, { facingLocation: V.add(at, V.mul(dir, 10)) }); } catch (err) { /* ignore */ }
  v.setProperty("ab:kind", kind);
  v.setProperty("ab:size", 0);
  vfxAlive.set(v.id, now() + life + 30);
  every(1, 10, (i) => vset(v, "ab:size", (size * (i + 1)) / 10));           // it grows out of the chakra
  fx(dim, "aura", V.up(at, 3), SUMMON_COLOR[kind], 2 + size, 1.1, { count: 50 * fxLevel(), speed: 3 });
  burst(dim, V.up(at, 2), SUMMON_COLOR[kind], 30, 3 + size, 0.5, 0.7);
  if (size >= 3) shake(dim, at, 0.3, 0.5);
  return v;
}
function summonGiant(e, kind, t, o = {}) {
  try {
    let dir = alive(t) ? V.sub(t.location, e.location) : e.getViewDirection();
    dir = V.norm({ x: dir.x, y: 0, z: dir.z });
    const at = o.at ?? V.add(e.location, V.mul(dir, -(o.behind ?? 2.5)));
    const life = o.life ?? 60, size = o.size ?? 3;
    const v = spawnSummon(e.dimension, kind, at, dir, size, life);
    if (o.pose) later(o.poseAt ?? 0, () => vset(v, "ab:pose", o.pose));
    later(life, () => fadeVfx(v, size, 8));
    return v;
  } catch (err) { warn("summon", err); return undefined; }
}
// The Susanoo stays with Sasuke for as long as he holds a Susanoo form, wrapped round him or towering behind him.
const SUSANOO_SIZE = { 3: 1.05, 4: 2.3, 0: 5, 7: 5.2 }, SUSANOO_BACK = { 3: 0, 4: 0.3, 0: 3.5, 7: 3.8 };
function susanooStage(e) {
  const f = formOf(e);
  if (e.typeId === "ab:sasuke") return f === 2 ? 3 : -1;
  if (e.typeId === "ab:sasuke_war") return f === 0 ? 4 : 0;
  if (e.typeId === "ab:sasuke_adult") return f === 1 ? 0 : -1;
  if (e.typeId === "ab:madara") return f === 1 ? 7 : -1;
  return -1;
}
function updateSusanoo(e, s) {
  const stage = e.hasTag("ab_clone") ? -1 : susanooStage(e);
  if (s.susanoo && (!s.susanoo.isValid || s.susanooStage !== stage)) {
    if (s.susanoo.isValid) fadeVfx(s.susanoo, SUSANOO_SIZE[s.susanooStage] ?? 1, 8);
    s.susanoo = undefined;
  }
  if (stage < 0) return;
  let yaw = 0;
  try { yaw = e.getRotation().y; } catch (err) { /* ignore */ }
  const fwd = { x: -Math.sin((yaw * Math.PI) / 180), y: 0, z: Math.cos((yaw * Math.PI) / 180) };
  const at = V.add(e.location, V.mul(fwd, -SUSANOO_BACK[stage]));
  try {
    if (!s.susanoo) {
      s.susanoo = spawnSummon(e.dimension, stage, at, fwd, SUSANOO_SIZE[stage], 40);
      s.susanooStage = stage;
      sound(e.dimension, "mob.wither.spawn", e.location, 1, 1.4);
    } else {
      s.susanoo.teleport(at, { rotation: { x: 0, y: yaw } });
      vfxAlive.set(s.susanoo.id, now() + 40);
    }
  } catch (err) { s.susanoo = undefined; }
}
function susanooPose(e, pose, ticks) {
  const v = state(e).susanoo;
  if (!v || !v.isValid) return;
  vset(v, "ab:pose", pose);
  later(ticks, () => vset(v, "ab:pose", 0));
}
const perfectSusanoo = (e) => (e.typeId === "ab:sasuke_war" && formOf(e) >= 1) || (e.typeId === "ab:sasuke_adult" && formOf(e) === 1);
const kuramaAvatar = (e) => (e.typeId === "ab:naruto_war" && formOf(e) >= 1) || (e.typeId === "ab:naruto_adult" && formOf(e) === 2);
function shake(dim, loc, power = 0.25, secs = 0.3) {
  try { dim.runCommand(`camerashake add @a[x=${Math.floor(loc.x)},y=${Math.floor(loc.y)},z=${Math.floor(loc.z)},r=14] ${power} ${secs} positional`); } catch (e) { /* ignore */ }
}

// ------------------------------------------------------------------ effects
const VFX_SCALE = 1.3;  // every technique drawn bigger and clearer
function fx(dim, kind, loc, color, size, life, extra) {
  try {
    const m = new MolangVariableMap();
    m.setColorRGB("variable.color", color);
    m.setFloat("variable.size", size * VFX_SCALE);
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
function announce(e, text) {  // the fighter shouts (face only) — no text is ever shown on screen
  void text;
  setExpr(e, 1, 30);
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
      try { o.applyKnockback({ x: d.x * opt.knock, z: d.z * opt.knock }, lowLift(opt.lift ?? 0.4)); } catch (e) { /* ignore */ }
    }
    n++;
  }
  return n;
}
function carve(dim, center, r, budget = 160) {
  if (!griefing() || r <= 0) return;
  if (r >= 1.5 && Math.random() < 0.4) rubble(dim, center, Math.round(4 + r * 3), 5 + r);
  const R = Math.ceil(r), r2 = r * r;
  let n = 0;
  for (let x = -R; x <= R; x++) for (let y = -R; y <= R; y++) for (let z = -R; z <= R; z++) {
    if (x * x + y * y + z * z > r2) continue;
    try {
      const b = dim.getBlock({ x: Math.floor(center.x + x), y: Math.floor(center.y + y), z: Math.floor(center.z + z) });
      if (!b || b.isAir || b.isLiquid || UNBREAKABLE.has(b.typeId) || DOME_BLOCKS.has(b.typeId)) continue;
      if (b.getComponent("minecraft:inventory")) continue;  // never break chests and other containers
      scar(dim, b);
      b.setType("minecraft:air");
      if (++n >= budget) return;
    } catch (e) { /* unloaded */ }
  }
}
// ------------------------------------------------------------------ arena memory (Jujutsu Craft mob-battle style)
// Fights tear the ground apart (trenches, craters, cut lines); every broken block is remembered and the arena
// rebuilds itself block by block once the fighting has stopped (or right after a team wins). /scriptevent ab:regen off
const SCARS = [];
let lastScar = 0;
const regenOn = () => setting("ab:regen", true);
function scar(dim, b) {
  if (SCARS.length >= 30000) return;
  SCARS.push({ dim, loc: { x: b.location.x, y: b.location.y, z: b.location.z }, perm: b.permutation });
  lastScar = now();
}
function healArenaSoon(ticks = 60) { lastScar = Math.min(lastScar, now() - 600 + ticks); }
system.runInterval(() => {
  if (!SCARS.length || !regenOn()) return;
  if (now() - lastScar < 600) return;  // only once the ground has been left alone for 30 s (or a team has won)
  for (let k = 0; k < 48 && SCARS.length; k++) {
    const sc = SCARS.pop();
    try {
      const b = sc.dim.getBlock(sc.loc);
      if (!b || !b.isAir) continue;  // something else is there now: leave it
      const c = { x: sc.loc.x + 0.5, y: sc.loc.y + 0.5, z: sc.loc.z + 0.5 };
      if (sc.dim.getEntities({ location: c, maxDistance: 1.2 }).some((o) => !IGNORE_TYPES.has(o.typeId))) { SCARS.unshift(sc); continue; }
      b.setPermutation(sc.perm);
      if (k % 6 === 0) fx(sc.dim, "aura", c, DUST, 0.6, 0.5, { count: 3, speed: 1 });
    } catch (e) { /* chunk unloaded: drop it */ }
  }
}, 1);
// A trench torn along the ground under a fighter sliding back from a hit.
function groundTear(dim, loc, r = 1.1) {
  const g = { x: loc.x, y: Math.floor(loc.y) - 0.5, z: loc.z };
  if (!solidAt(dim, g)) return;
  rubble(dim, g, Math.round(5 + r * 6), 4 + r * 2.5);
  if (r >= 2.2) sound(dim, "ab.boom", g, 1.5, 0.9 + Math.random() * 0.2);
  carve(dim, g, r, 14);
}
// Chunks of the ground thrown up and bouncing back down — textured with the block that broke.
function rubble(dim, loc, count, speed) {
  let earthy = false;
  try { const b = dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) }); earthy = !!b && /dirt|grass|mud|podzol|mycelium|farmland|sand|gravel/.test(b.typeId); } catch (e) { /* ignore */ }
  const tone = earthy ? { red: 0.95, green: 0.9, blue: 0.85 } : { red: 0.9, green: 0.9, blue: 0.9 };
  fx(dim, earthy ? "rubble_dirt" : "rubble", V.up(loc, 0.6), tone, 0.32, 1.6, { count: Math.ceil(count * fxLevel()), speed, radius: 0.5 });
}

// ------------------------------------------------------------------ domain barrier (a real dome of blocks)
// Like Jujutsu Craft: the barrier closes from the ground up into a full dome that traps both fighters, then
// shatters when the domain ends or loses a clash. Only air is ever replaced, and it all turns back to air.
const DOME_BLOCKS = new Set(["minecraft:black_concrete", "minecraft:sea_lantern", "minecraft:obsidian", "minecraft:crying_obsidian",
  "minecraft:white_concrete", "minecraft:pearlescent_froglight", "minecraft:polished_blackstone", "minecraft:polished_blackstone_bricks",
  "minecraft:red_nether_brick", "minecraft:nether_wart_block", "minecraft:bone_block"]);
const DOMES = new Map();
function buildDome(e, center, R, shell, star, ticks) {
  const dim = e.dimension;
  const cells = [];
  const Ri = Math.ceil(R + 0.5);
  for (let x = -Ri; x <= Ri; x++) for (let y = -Ri; y <= Ri; y++) for (let z = -Ri; z <= Ri; z++) {
    const d = Math.sqrt(x * x + y * y + z * z);
    if (d >= R - 0.5 && d < R + 0.5) cells.push({ x: Math.floor(center.x) + x, y: Math.floor(center.y) + y, z: Math.floor(center.z) + z });
  }
  cells.sort((a, b) => a.y - b.y);  // it rises from the ground and seals at the top
  const rec = { dim, placed: [], open: true };
  breakDome(e.id, false);
  sound(dim, "ab.domain", center, 3, 1);
  DOMES.set(e.id, rec);
  const slices = 10, per = Math.ceil(cells.length / slices);
  let bodies = [];
  try { bodies = dim.getEntities({ location: center, maxDistance: R + 3 }).filter((o) => !IGNORE_TYPES.has(o.typeId)).map((o) => o.location); } catch (err) { /* ignore */ }
  every(1, slices, (i) => {
    if (!rec.open) return false;
    for (const c of cells.slice(i * per, (i + 1) * per)) {
      if (bodies.some((p) => Math.abs(p.x - c.x - 0.5) < 1.4 && Math.abs(p.z - c.z - 0.5) < 1.4 && c.y >= p.y - 1 && c.y <= p.y + 2.5)) continue;
      try {
        const b = dim.getBlock(c);
        if (!b || !b.isAir) continue;
        const t = Math.random() < 0.07 ? star : shell;
        b.setType(t); rec.placed.push({ c, t });
      } catch (err) { /* unloaded */ }
    }
    if (i === slices - 1) {
      sound(dim, "random.door_close", center, 2, 0.4); sound(dim, "block.end_portal.spawn", center, 1, 0.8);
      screenFade(dim, center, R + 10, 0.05, 0.25, 0.45, [0, 0, 0]);
      shake(dim, center, 0.5, 0.5);
    }
  });
  later(ticks, () => breakDome(e.id, true));
}
function breakDome(id, shatter) {
  const rec = DOMES.get(id);
  if (!rec) return;
  DOMES.delete(id);
  rec.open = false;
  const list = rec.placed;
  const per = Math.ceil(list.length / 6);
  every(1, 6, (i) => {
    for (const { c, t } of list.slice(i * per, (i + 1) * per)) {
      try {
        const b = rec.dim.getBlock(c);
        if (b && b.typeId === t) b.setType("minecraft:air");
        if (shatter && Math.random() < 0.05) fx(rec.dim, "burst", { x: c.x + 0.5, y: c.y + 0.5, z: c.z + 0.5 }, C.black, 0.4, 0.6, { count: 4, speed: 3, radius: 0.2 });
      } catch (err) { /* ignore */ }
    }
  });
  if (shatter && list.length) sound(rec.dim, "random.glass", list[Math.floor(list.length / 2)].c, 3, 0.5);
}
// Raise a temporary structure (list of {c, t}) from the ground up over `slices` ticks; it crumbles after `ticks`.
function raise(key, dim, cells, slices, ticks) {
  breakDome(key, false);
  const rec = { dim, placed: [], open: true };
  DOMES.set(key, rec);
  cells.sort((a, b) => a.c.y - b.c.y);
  const per = Math.ceil(cells.length / slices);
  every(1, slices, (i) => {
    if (!rec.open) return false;
    let bodies = [];
    try { bodies = dim.getEntities({ location: cells[0].c, maxDistance: 24 }).filter((o) => !IGNORE_TYPES.has(o.typeId)).map((o) => o.location); } catch (err) { /* ignore */ }
    for (const { c, t } of cells.slice(i * per, (i + 1) * per)) {
      if (bodies.some((p) => Math.abs(p.x - c.x - 0.5) < 1.3 && Math.abs(p.z - c.z - 0.5) < 1.3 && c.y >= p.y - 1 && c.y <= p.y + 2.5)) continue;
      try { const b = dim.getBlock(c); if (b && b.isAir) { b.setType(t); rec.placed.push({ c, t }); } } catch (err) { /* unloaded */ }
    }
  });
  later(ticks, () => breakDome(key, true));
}
// Malevolent Shrine: Sukuna's open domain — no barrier, but the shrine itself rises behind him: a blackstone
// platform heaped with bones, red pillars, a fanged mouth of flesh and a three-tier roof with upturned eaves.
function shrineCells(e) {
  const f = V.norm({ x: e.getViewDirection().x, y: 0, z: e.getViewDirection().z });
  const back = V.mul(f, -1), side = sideOf(f);
  const o = V.add(e.location, V.mul(back, 4));
  const y0 = Math.floor(e.location.y);
  const cells = [], seen = new Set();
  const put = (u, w, y, t) => {
    const c = V.add(o, V.add(V.mul(side, u), V.mul(back, w)));
    const k = { x: Math.floor(c.x), y: y0 + y, z: Math.floor(c.z) };
    const id = `${k.x},${k.y},${k.z}`;
    if (seen.has(id)) return;
    seen.add(id); cells.push({ c: k, t });
  };
  const BS = "minecraft:polished_blackstone", BB = "minecraft:polished_blackstone_bricks", RN = "minecraft:red_nether_brick",
    FL = "minecraft:nether_wart_block", BO = "minecraft:bone_block", BK = "minecraft:black_concrete";
  // pillars and mouth first so the platform never overwrites them
  for (const u of [-3, 3]) for (const w of [0, 4]) for (let y = 1; y <= 5; y++) put(u, w, y, RN);
  for (const u of [-2, 2]) for (let y = 1; y <= 4; y++) put(u, 1, y, FL);
  for (const u of [-1, 0, 1]) { put(u, 1, 4, u === 0 ? FL : BO); put(u, 1, 1, u === 0 ? BK : BO); }
  for (const u of [-1, 0, 1]) for (let y = 2; y <= 3; y++) put(u, 1, y, BK);
  put(-1, 1, 3, BO); put(1, 1, 2, BO);  // fangs
  for (let u = -2; u <= 2; u++) for (let y = 1; y <= 5; y++) put(u, 4, y, FL);
  for (let u = -4; u <= 4; u++) for (let w = -1; w <= 5; w++) {
    put(u, w, 0, (u + w) % 3 === 0 ? BB : BS);
    if ((Math.abs(u) === 4 || w === -1 || w === 5) && (u * 7 + w * 3) % 3 !== 0) put(u, w, 1, BO);
  }
  for (let u = -4; u <= 4; u++) for (let w = -1; w <= 5; w++) put(u, w, 6, BS);
  for (let u = -3; u <= 3; u++) for (let w = 0; w <= 4; w++) put(u, w, 7, BB);
  for (let u = -2; u <= 2; u++) for (let w = 1; w <= 3; w++) put(u, w, 8, BS);
  for (let u = -1; u <= 1; u++) put(u, 2, 9, RN);
  for (const u of [-5, 5]) for (const w of [-2, 6]) { put(u, w, 6, RN); put(u, w, 7, RN); }  // upturned eaves
  return cells;
}
// Cinematic shot (the "cinematic ultimates" of the Java anime mods): watching players' cameras swing round the
// fighter for a couple of seconds, then cut back through black. Each player at most once every ~14 s.
// /scriptevent ab:cinema off
const cinemaOn = () => setting("ab:cinema", true);
const camBusy = new Map();
const xyz = (p) => `${p.x.toFixed(2)} ${p.y.toFixed(2)} ${p.z.toFixed(2)}`;
function cinematic(focus, ticks = 44, dist = 7) {
  if (!alive(focus)) return;
  cinematicAt(focus.dimension, focus.location, ticks, dist);
}
function cinematicAt(dim, f, ticks = 44, dist = 7, look = V.up(f, 1.3)) {
  if (!cinemaOn()) return;
  let players = [];
  try { players = dim.getPlayers({ location: f, maxDistance: 48 }); } catch (e) { return; }
  const ang = Math.random() * Math.PI * 2;
  const at = (a, r, h) => ({ x: f.x + Math.cos(a) * r, y: f.y + h, z: f.z + Math.sin(a) * r });
  const p0 = at(ang, dist * 0.7, 0.6), p1 = at(ang + 1.2, dist * 1.3, dist * 0.45);
  for (const p of players) {
    if ((camBusy.get(p.id) ?? 0) > now()) continue;
    camBusy.set(p.id, now() + ticks + 240);
    try { p.runCommand(`camera @s set minecraft:free pos ${xyz(p0)} facing ${xyz(look)}`); } catch (e) { continue; }
    later(1, () => { try { if (p.isValid) p.runCommand(`camera @s set minecraft:free ease ${((ticks - 6) / 20).toFixed(2)} in_out_sine pos ${xyz(p1)} facing ${xyz(look)}`); } catch (e) { /* ignore */ } });
    later(ticks - 4, () => { try { if (p.isValid) p.runCommand("camera @s fade time 0.15 0.1 0.3 color 0 0 0"); } catch (e) { /* ignore */ } });
    later(ticks, () => { try { if (p.isValid) p.runCommand("camera @s clear"); } catch (e) { /* ignore */ } });
  }
}
// Pull enemies standing at the edge inside the barrier before it closes.
function drawInside(e, center, R) {
  let list = [];
  try { list = e.dimension.getEntities({ location: center, maxDistance: R + 6 }); } catch (err) { return; }
  for (const o of list) {
    if (!canHit(e, teamOf(e), o)) continue;
    const d = { x: o.location.x - center.x, y: 0, z: o.location.z - center.z };
    const L = Math.hypot(d.x, d.z);
    if (L < R - 3) continue;
    const to = V.add({ x: center.x, y: o.location.y, z: center.z }, V.mul(V.norm(d), R - 4));
    try { o.tryTeleport(to, { checkForBlocks: true }); } catch (err) { /* ignore */ }
  }
}
// A cinematic flash of colour over the screens of players watching nearby (no text).
function screenFade(dim, loc, r, fin, hold, fout, rgb) {
  try {
    dim.runCommand(`camera @a[x=${Math.floor(loc.x)},y=${Math.floor(loc.y)},z=${Math.floor(loc.z)},r=${Math.round(r)}] fade time ${fin} ${hold} ${fout} color ${rgb[0]} ${rgb[1]} ${rgb[2]}`);
  } catch (e) { /* ignore */ }
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

// Beam struggle: two beams fired at each other meet in the middle; the stronger side pushes the clash
// point onto the weaker one and it blows up there.
const activeBeams = new Map();
function beamClash(a, b, color) {
  const dim = a.dimension;
  announce(a, "§e§lBEAM STRUGGLE!");
  const winner = powerOf(a) >= powerOf(b) ? a : b;
  const loser = winner === a ? b : a;
  every(2, 12, (i) => {
    if (!a.isValid || !b.isValid) return false;
    const pa = aim(a), pb = aim(b);
    const t = 0.5 + (winner === a ? 1 : -1) * i * 0.03;
    const mid = V.add(pa, V.mul(V.sub(pb, pa), t));
    fx(dim, "flash", mid, C.white, 3 + (i % 3), 0.2);
    fx(dim, "orb", mid, color, 4, 0.2);
    fx(dim, "streak", mid, C.white, 1.6, 0.3, { count: 8, speed: 9 });
    if (i % 3 === 0) shake(dim, mid, 0.3, 0.2);
  });
  later(26, () => {
    if (winner.isValid && alive(loser)) explosion(winner, aim(loser), { radius: 3, dmg: 30 * powerOf(winner) / 100, color, knock: 2 });
  });
}

// Fighters with a signature beam answer an incoming beam with their own — and the two collide.
const COUNTER_BEAM = { "ab:goku": ["§b§lKAMEHAMEHA!", C.kameBlue], "ab:vegeta": ["§d§lGALICK GUN!", C.galick],
  "ab:frieza": ["§5§lDeath Beam!", C.death], "ab:ichigo": ["§4§lCero!", C.red] };
function counterBeam(d, src) {
  const cb = COUNTER_BEAM[d.typeId];
  if (!cb || !alive(d) || !alive(src) || d.hasTag("ab_clone")) return;
  if (d.typeId === "ab:ichigo" && formOf(d) !== 3 && formOf(d) !== 4) return;  // Cero needs the Hollow mask
  const ds = state(d);
  if (now() < ds.busyUntil || now() < (ds.cd.counterBeam ?? 0) || ds.energy < 150 || Math.random() > 0.5) return;
  ds.cd.counterBeam = now() + 400;
  ds.energy -= 150;
  busy(ds, 26);
  later(3, () => {
    if (!alive(d) || !alive(src)) return;
    face(d, aim(src)); setPose(d, 1); announce(d, cb[0]);
    beam(d, src, { color: cb[1], width: 1.2, length: 40, dmg: 45 * powerOf(d) / 100, blast: 2.5, ticks: 6 });
    later(18, () => { if (d.isValid) setPose(d, 0); });
  });
}

// A beam that grows from the caster toward the target, hitting everything along it once.
function beam(src, target, o) {
  setExpr(src, 1, 26);
  if (target && target.isValid && target !== src) {
    const other = activeBeams.get(target.id);
    activeBeams.set(src.id, { target: target.id, until: now() + 30 });
    if (other && other.target === src.id && now() < other.until && isFighter(target)) beamClash(src, target, o.color);
    else counterBeam(target, src);
  }
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
  const hpc = health(e);  // the surge of a new form restores a little strength
  if (hpc) try { hpc.setCurrentValue(Math.min(hpc.effectiveMax, hpc.currentValue + hpc.effectiveMax * 0.06)); } catch (err) { /* ignore */ }
  const calm = e.typeId === "ab:goku" && to === 5;  // Ultra Instinct awakens in silence: no yell, no crouch
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
    : (e.typeId === "ab:ichigo" && to === 3) ? 25   // drags the Hollow mask down over his face
    : (e.typeId === "ab:naruto_teen" && to === 3) || (e.typeId === "ab:naruto_war" && to === 2) || (e.typeId === "ab:naruto_adult" && to === 1) ? 35   // still, hands in a seal, gathering nature energy
    : calm ? 0
    : 22);
  slow(e, 30, 8);
  if (to === def.forms.length - 1 && !e.hasTag("ab_clone")) cinematic(e, 34, 5);
  sound(dim, "ambient.weather.thunder", e.location, 1.5, 1.2);
  every(4, 7, (i) => {
    if (!e.isValid) return false;
    fx(dim, "aura", e.location, color, 1.2, 0.8, { count: 18 * fxLevel(), speed: 2 });
    implode(dim, V.up(e.location, 1), color, 4, 10);
    if (i === 6) {
      try { e.triggerEvent(`ab:form_${to}`); } catch (err) { warn("transform", err); }
      if (!calm) groundTear(dim, e.location, to === def.forms.length - 1 ? 2.8 : 1.8);
      setPose(e, 0);
      burst(dim, V.up(e.location, 1), color, 60, 6, 0.6, 0.9);
      burst(dim, V.up(e.location, 1), C.white, 30, 4, 0.4, 0.6);
      ring(dim, V.up(e.location, 0.1), 3, color, 24, 0.6);
      sound(dim, extraSound ?? "random.explode", e.location, 1.5, 0.7);
      hitArea(e, e.location, 4, 0, null, { knock: 1.5, lift: 0.3 });
      const line = (TRANSFORM_LINES[e.typeId] ?? [])[to];
      announce(e, line ? `${line} §r§7(${label})` : `§l${def.color}${def.name} §r§f→ §l${label}`);
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
const G = (...f) => (e) => f.includes(formOf(e));
// Signature-move helpers for the roster additions
const SIG = {
  beam: (id, label, o) => ({ id, label, cd: o.cd ?? 320, cost: o.cost ?? 220, min: 0, max: o.max ?? 42, weight: o.weight ?? 5, cond: o.cond,
    run(e, s, t) {
      const ch = o.charge ?? 14;
      busy(s, ch + 16); face(e, aim(t)); announce(e, o.say);
      chargeOrb(e, t, ch, o.color, 0.4, o.orb ?? 1.6, o.pose ?? 2);
      if (o.aura) every(2, Math.ceil(ch / 2), () => { if (e.isValid) fx(e.dimension, "aura", e.location, o.aura, 1.7, 0.6, { count: 16, speed: 2.5 }); });
      later(ch, () => {
        if (!e.isValid) return;
        beam(e, alive(t) ? t : e, { color: o.color, width: o.width ?? 1.6, length: o.length ?? 44, dmg: o.dmg * powerOf(e) / 100, carve: o.carve ?? 1, blast: o.blast ?? 4, ticks: 7 });
        later(14, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  ball: (id, label, o) => ({ id, label, cd: o.cd ?? 200, cost: o.cost ?? 120, min: 0, max: o.max ?? 36, weight: o.weight ?? 4, cond: o.cond,
    run(e, s, t) {  // one or more energy balls, optionally homing
      const ch = o.charge ?? 8, n = o.count ?? 1;
      busy(s, ch + n * 2 + 10); face(e, aim(t)); announce(e, o.say);
      chargeOrb(e, t, ch, o.color, 0.3, o.size ?? 1, o.pose ?? 4);
      later(ch, () => {
        if (!e.isValid) return;
        every(2, n, (i) => {
          if (!e.isValid) return false;
          const { pos } = handPos(e, alive(t) ? t : e);
          const tgt = alive(t) ? V.add(aim(t), { x: (Math.random() - 0.5) * (o.spread ?? 0), y: 0, z: (Math.random() - 0.5) * (o.spread ?? 0) }) : V.add(pos, e.getViewDirection());
          projectile(e, pos, V.norm(V.sub(tgt, pos)), { speed: o.speed ?? 1.3, maxDist: 40, radius: 1.3, size: o.size ?? 1, color: o.color, trail: true,
            homing: o.homing && alive(t) ? t : undefined, homingStrength: 0.1,
            explode: { radius: o.radius ?? 2.4, dmg: o.dmg * powerOf(e) / 100, color: o.color, knock: o.knock ?? 1.6, carve: o.carve ?? 0 } });
        });
        later(n * 2 + 8, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  drop: (id, label, o) => ({ id, label, cd: o.cd ?? 500, cost: o.cost ?? 320, min: 0, max: o.max ?? 40, weight: o.weight ?? 5, cond: o.cond,
    run(e, s, t) {  // a giant sphere raised overhead, then hurled down on the target
      busy(s, 30); setPose(e, 23); announce(e, o.say);
      const dim = e.dimension;
      const ball = spawnVfx(dim, 1, V.up(e.location, 5), { slot: slotOf(o.color), size: 0.4, life: 50 });
      every(1, 20, (i) => { vset(ball, "ab:size", 0.4 + i * (o.grow ?? 0.1)); try { if (ball?.isValid && e.isValid) ball.teleport(V.up(e.location, 5)); } catch (err) { /* ignore */ } });
      later(20, () => {
        killVfx(ball);
        if (!e.isValid) return;
        const start = V.up(e.location, 5);
        const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 10));
        projectile(e, start, V.norm(V.sub(tgt, start)), { speed: 0.9, maxDist: 50, radius: 2.4, size: o.size ?? 3, color: o.color,
          explode: { radius: o.radius ?? 6, dmg: o.dmg * powerOf(e) / 100, color: o.color, carve: 3, knock: 3 } });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  wave: (id, label, o) => ({ id, label, cd: o.cd ?? 220, cost: o.cost ?? 100, min: 0, max: o.max ?? 7, weight: o.weight ?? 4, cond: o.cond,
    run(e, s, t) {  // a burst of power all around
      busy(s, 14); setPose(e, o.pose ?? 22); setExpr(e, 1, 12); announce(e, o.say);
      const dim = e.dimension;
      fx(dim, "shock", e.location, o.color, (o.radius ?? 5) * 1.8, 0.5); ring(dim, V.up(e.location, 0.3), o.radius ?? 5, o.color, 32, 0.5);
      fx(dim, "flash", V.up(e.location, 1), o.color, 4, 0.2);
      hitArea(e, V.up(e.location, 1), o.radius ?? 5, o.dmg * powerOf(e) / 100, new Set(), { knock: o.knock ?? 2.8, lift: 0.5 });
      later(12, () => { if (e.isValid) setPose(e, 0); });
    } }),
  slash: (id, label, o) => ({ id, label, cd: o.cd ?? 160, cost: o.cost ?? 90, min: 0, max: o.max ?? 28, weight: o.weight ?? 4, cond: o.cond,
    run(e, s, t) {  // flying slashes, one or several
      const n = o.count ?? 1;
      busy(s, n * 4 + 10); announce(e, o.say);
      every(4, n, (i) => {
        if (!e.isValid) return false;
        setPose(e, i % 2 ? 28 : (o.pose ?? 19));
        flyingSlash(e, t, { color: o.color, dmg: o.dmg * powerOf(e) / 100, range: o.range ?? 28, roll: (o.roll ?? 0) + i * 40, carve: true, size: o.size ?? 1.8 });
      });
      later(n * 4 + 8, () => { if (e.isValid) setPose(e, 0); });
    } }),
  rush: (id, label, o) => ({ id, label, cd: o.cd ?? 200, cost: o.cost ?? 120, min: 0, max: o.max ?? 18, weight: o.weight ?? 5, cond: o.cond,
    run(e, s, t) {
      const n = o.hits ?? 5;
      busy(s, n * 4 + 10); announce(e, o.say);
      every(4, n, (i) => {
        if (!alive(t) || !e.isValid) return false;
        afterimage(e); teleportNear(e, t, i % 2 === 0, 1.3); face(e, aim(t));
        setPose(e, (o.poses ?? [5, 6, 7, 9])[i % (o.poses ?? [5, 6, 7, 9]).length]);
        deal(e, t, (i === n - 1 ? (o.finisher ?? o.dmg * 2.5) : o.dmg) * powerOf(e) / 100);
        fx(t.dimension, "shock_v", aim(t), o.color, 2.2 + (i === n - 1 ? 2 : 0), 0.3);
        burst(t.dimension, aim(t), o.color, 12, 3, 0.4, 0.4);
        if (i === n - 1) { if (o.slam) { try { t.applyKnockback({ x: 0, z: 0 }, lowLift(-1.6)); } catch (err) { /* ignore */ } fx(t.dimension, "shock", t.location, o.color, 6, 0.4); }
          later(6, () => { if (e.isValid) setPose(e, 0); }); }
      });
    } }),
};

const GOKU = {
  name: "Goku", color: "§6", energy: 1000, regen: 15, energyName: "§bKI",
  dodge: (e, s) => (formOf(e) === 5 ? 0.6 : 0.1),
  forms: [
    { label: "Base", power: 150 },
    { label: "Super Saiyan", power: 220, aura: C.gold },
    { label: "Super Saiyan 3", power: 300, aura: C.gold },
    { label: "Super Saiyan God", power: 420, aura: C.red },
    { label: "Super Saiyan Blue", power: 560, aura: C.ssbBlue },
    { label: "Ultra Instinct", power: 850, aura: C.silver },
  ],
  thresholds: [0.9, 0.75, 0.6, 0.45, 0.3],
  transformCd: 80,
  formSound: [null, "mob.enderdragon.growl", "mob.enderdragon.growl", "beacon.power", "beacon.power", "beacon.activate"],
  abilities: [
    SIG.wave("kiai", "Kiai", { say: "§e§lHAA! §7— a shout that blows everything away", color: C.white, radius: 6, dmg: 12, cd: 200 }),
    SIG.ball("kivolley", "Ki Barrage", { say: "§e§lHaa-haa-haa-haa! §7— a storm of ki blasts", color: C.kiYellow, count: 8, size: 0.8, dmg: 7, spread: 2, cd: 180 }),
    SIG.beam("godkame", "God Kamehameha", { cond: (e) => formOf(e) === 3, say: "§c§lThe power of a god... §4§lKAMEHAMEHA!", color: C.red, aura: C.red, width: 2.4, dmg: 120, charge: 16, cd: 520 }),
    SIG.beam("uikame", "Ultra Instinct Kamehameha", { cond: (e) => formOf(e) === 5, say: "§f§l(silent) §7— a silver Kamehameha", color: C.silver, aura: C.silver, width: 3.0, dmg: 190, charge: 12, cd: 600, cost: 500 }),
    { id: "dragonthrow", label: "Dragon Throw", cd: 220, cost: 80, min: 0, max: 6, weight: 4,
      run(e, s, t) {  // grabs the tail/arm, spins round and hurls
        busy(s, 20); announce(e, "§6§lDragon Throw!");
        afterimage(e); teleportNear(e, t, true, 1.2); setPose(e, 24);
        every(2, 6, () => { if (e.isValid) ring(e.dimension, V.up(e.location, 1), 2.2, C.gold, 16, 0.3); });
        later(12, () => { if (!alive(t) || !e.isValid) return; deal(e, t, 26 * powerOf(e) / 100); launch(e, t, 1.25); setPose(e, 0); });
      } },
    { id: "afterimage", label: "Afterimage Technique", cd: 260, cost: 60, min: 0, max: 8, weight: 3,
      run(e, s, t) {  // leaves an image behind and strikes from the blind spot
        busy(s, 12); announce(e, "§f§lAfterimage! §7— he was never there");
        afterimage(e); afterimage(e); teleportNear(e, t, true, 1.3); setPose(e, 8);
        later(3, () => { if (alive(t)) { deal(e, t, 22 * powerOf(e) / 100); launch(e, t, 1); } if (e.isValid) later(6, () => setPose(e, 0)); });
      } },
    { id: "solarflare", label: "Solar Flare", cd: 320, cost: 60, min: 0, max: 14, weight: 4,
      run(e, s, t) {  // a blinding flash: everyone looking at him loses sight of him
        busy(s, 10); setPose(e, 3); announce(e, "§e§lSOLAR FLARE! §7— Taiyoken!");
        fx(e.dimension, "flash", V.up(e.location, 1.8), C.white, 12, 0.5);
        let list = []; try { list = e.dimension.getEntities({ location: e.location, maxDistance: 14 }); } catch (err) { /* ignore */ }
        for (const x of list) if (canHit(e, teamOf(e), x) && isFighter(x)) { const xs = state(x); xs.stunUntil = Math.max(xs.stunUntil, now() + 24); }
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    SIG.beam("superkame", "10x Kaioken Kamehameha", { cond: (e) => formOf(e) === 4, say: "§c§lKaioken times TEN! §b§lKAMEHAMEHA!", color: C.ssbBlue, aura: C.kaioken, width: 2.8, dmg: 150, charge: 18, cd: 700, cost: 520 }),
    SIG.rush("meteor", "Meteor Smash", { cond: (e) => formOf(e) >= 1, say: "§6§lMeteor Smash!", color: C.gold, dmg: 8, finisher: 30, hits: 5, poses: [5, 6, 7, 9, 10], slam: true }),
    SIG.rush("silverdragon", "Silver Dragon Flash", { cond: (e) => formOf(e) === 5, say: "§f§l(silence) §7— Silver Dragon Flash", color: C.silver, dmg: 14, finisher: 46, hits: 6, poses: [5, 7, 6, 9, 8, 5], cd: 260 }),
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
      cond: (e, s, c) => (formOf(e) === 0 || formOf(e) === 4) && s.kaiokenUntil < now() && c.tPower >= c.power * 0.85,
      run(e, s) {
        busy(s, 10); s.kaiokenUntil = now() + 240;
        burst(e.dimension, V.up(e.location, 1), C.kaioken, 40, 5, 0.5, 0.7);
        sound(e.dimension, "mob.enderdragon.growl", e.location, 1, 1.4);
        announce(e, formOf(e) === 4 ? "§9Super Saiyan Blue §c§lKaioken!" : "§c§lKaioken!");
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
  ego: 4,
  forms: [
    { label: "Base", power: 140 },
    { label: "Super Saiyan", power: 210, aura: C.gold },
    { label: "Super Saiyan God", power: 400, aura: C.red },
    { label: "Super Saiyan Blue", power: 520, aura: C.ssbBlue },
    { label: "Ultra Ego", power: 680, aura: C.ego },
  ],
  thresholds: [0.85, 0.7, 0.5, 0.35],
  transformCd: 80,
  formSound: [null, "mob.enderdragon.growl", "beacon.power", "beacon.power", "mob.wither.spawn"],
  abilities: [
    SIG.beam("finalgalick", "Final Galick Cannon", { cond: (e) => formOf(e) >= 3, say: "§9§lFINAL GALICK CANNON!", color: C.galick, aura: C.ssbBlue, width: 2.8, dmg: 150, charge: 18, pose: 1, cd: 600, cost: 480 }),
    SIG.beam("atomic", "Atomic Blast", { cond: (e) => formOf(e) >= 1, say: "§e§lAtomic Blast!", color: C.kiYellow, width: 1.8, dmg: 70, charge: 10, pose: 1, cd: 300 }),
    SIG.drop("galaxy", "Galaxy Breaker", { cond: (e) => formOf(e) >= 3, say: "§9§lGALAXY BREAKER!", color: C.ssbBlue, dmg: 140, cd: 700, cost: 480 }),
    SIG.wave("barrier", "Energy Barrier", { say: "§e§lHaaa! §7— a dome of ki bursts out of him", color: C.kiYellow, radius: 5, dmg: 16, cd: 240 }),
    { id: "finalimpact", label: "Final Impact", cd: 300, cost: 200, min: 0, max: 16, weight: 5, cond: (e) => formOf(e) >= 3,
      run(e, s, t) {  // all his ki packed into one punch
        busy(s, 18); setPose(e, 22); announce(e, "§9§lFINAL IMPACT!");
        chargeOrb(e, t, 8, C.ssbBlue, 0.4, 1.4, 22);
        later(8, () => {
          if (!e.isValid || !alive(t)) return;
          afterimage(e); teleportNear(e, t, false, 1.3); setPose(e, 5);
          deal(e, t, 60 * powerOf(e) / 100);
          explosion(e, aim(t), { radius: 3.5, dmg: 20 * powerOf(e) / 100, color: C.ssbBlue, knock: 2.8 });
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    SIG.beam("gammaburst", "Gamma Burst Flash", { cond: (e) => formOf(e) >= 3, say: "§e§lGamma Burst Flash!", color: C.flash, aura: C.ssbBlue, width: 2.6, dmg: 140, charge: 16, pose: 1, cd: 600, cost: 460 }),
    SIG.rush("egorush", "Ultra Ego: Destruction Barrage", { cond: (e) => formOf(e) === 4, say: "§5§lThe more you hit me, the stronger I get!", color: C.ego, dmg: 12, finisher: 40, hits: 6, poses: [5, 6, 5, 6, 9, 10] }),
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
      cond: (e) => formOf(e) === 4,
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
              // Destruction fails on someone stronger than the God of Destruction's student: it only scorches them
              if (alive(t) && V.dist(aim(t), p) < 3) deal(e, t, 210 * powerOf(e) / 100 * (powerOf(t) > powerOf(e) ? 0.3 : 1));
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

// Domain clash (Shinjuku): two domains opened against each other push at their boundary;
// the stronger one holds and the other shatters.
const activeDomains = new Map();
function domainOpened(e) {
  for (const [id, d] of activeDomains) if (now() > d.until || !alive(d.e)) activeDomains.delete(id);
  for (const d of activeDomains.values()) {
    const o = d.e;
    if (o !== e && teamOf(o) && teamOf(o) !== teamOf(e) && V.dist(o.location, e.location) < 40) {
      activeDomains.set(e.id, { e, until: now() + 120 });
      domainClash(e, o);
      return;
    }
  }
  activeDomains.set(e.id, { e, until: now() + 120 });
  counterDomain(e);
}
function counterDomain(e) {
  let list = [];
  try { list = e.dimension.getEntities({ location: e.location, maxDistance: 30, families: ["anime_fighter"] }); } catch (err) { return; }
  for (const o of list) {
    if (o === e || !alive(o) || o.hasTag("ab_clone") || !teamOf(o) || teamOf(o) === teamOf(e)) continue;
    const os = state(o);
    if (now() < os.busyUntil || Math.random() > 0.6) continue;
    if (o.typeId === "ab:gojo" && os.energy >= 400 && now() >= os.burnoutUntil) {
      os.energy -= 400; later(4, () => { if (alive(o)) domain(o, os); }); return;
    }
    if (o.typeId === "ab:sukuna") {
      const shrine = FIGHTERS["ab:sukuna"].abilities.find((a) => a.id === "shrine");
      if (shrine && os.energy >= shrine.cost) { os.energy -= shrine.cost; later(4, () => { if (alive(o)) shrine.run(o, os); }); return; }
    }
  }
}
function domainClash(a, b) {
  const dim = a.dimension;
  announce(a, "§5§lDOMAIN CLASH! §7— the two domains push against each other");
  const winner = powerOf(a) >= powerOf(b) ? a : b;
  const loser = winner === a ? b : a;
  every(3, 10, (i) => {
    if (!a.isValid || !b.isValid) return false;
    const pa = a.location, pb = b.location;
    const mid = V.up(V.add(pa, V.mul(V.sub(pb, pa), 0.5 + (winner === a ? 1 : -1) * i * 0.02)), 1.5);
    fx(dim, "flash", mid, C.white, 4, 0.25);
    fx(dim, "shock_v", mid, C.purple, 6, 0.3);
    fx(dim, "streak", mid, i % 2 ? C.blood : C.void, 2, 0.4, { count: 12, speed: 10 });
    shake(dim, mid, 0.4, 0.25);
  });
  later(32, () => {
    if (!alive(loser)) return;
    state(loser).domainBroken = now() + 200;
    breakDome(loser.id, true); breakDome(`shrine${loser.id}`, true);
    screenFade(dim, loser.location, 40, 0.02, 0.05, 0.3, [255, 255, 255]);
    announce(loser, "§c§lThe domain shatters!");
    burst(dim, V.up(loser.location, 2), C.white, 40, 6, 0.4, 0.6);
    sound(dim, "random.glass", loser.location, 2, 0.6);
  });
}

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
  drawInside(e, center, R);
  cinematic(e, 40, 6);
  buildDome(e, center, R + 1, "minecraft:black_concrete", "minecraft:sea_lantern", 124);
  domainOpened(e);
  every(4, 30, (i) => {
    if (!e.isValid || (state(e).domainBroken ?? 0) > now()) return false;
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
    SIG.beam("maxred", "Reversal Red: Maximum", { cond: G(1), say: "§c§lReversal: §4§lRed — Maximum Output", color: C.red, width: 2.2, dmg: 110, charge: 10, pose: 25, cd: 420, cost: 280 }),
    SIG.ball("blueorbs", "Lapse Blue: Orbs", { say: "§9§lBlue. §7— three points of attraction", color: C.blue, count: 3, size: 1.1, dmg: 16, homing: true, cd: 220, pose: 25 }),
    SIG.rush("infinityrush", "Infinity Barrage", { say: "§b§lUntouchable. §7— he hits; nothing touches him", color: C.blue, dmg: 8, finisher: 30, hits: 6, poses: [5, 6, 7, 5, 6, 9] }),
    { id: "maxblue", label: "Lapse Blue: Maximum Output", cd: 360, cost: 240, min: 0, max: 20, weight: 5, cond: G(1),
      run(e, s, t) {  // everything nearby is dragged into one point and crushed
        busy(s, 26); setPose(e, 4); announce(e, "§9§lCursed Technique Lapse: §1§lBlue — Maximum Output");
        const dim = e.dimension;
        const c = alive(t) ? V.up(t.location, 1.5) : V.add(e.location, V.mul(e.getViewDirection(), 6));
        const ball = spawnVfx(dim, 1, c, { slot: 5, size: 1.2, life: 40 });
        every(2, 12, () => {
          let list = []; try { list = dim.getEntities({ location: c, maxDistance: 12 }); } catch (err) { /* ignore */ }
          for (const x of list) if (canHit(e, teamOf(e), x)) { const d = V.norm(V.sub(c, x.location)); try { x.applyKnockback({ x: d.x * 1.0, z: d.z * 1.0 }, lowLift(0.2)); } catch (err) { /* ignore */ } }
          implode(dim, c, C.blue, 6, 14);
        });
        later(24, () => { killVfx(ball); explosion(e, c, { radius: 4, dmg: 60 * powerOf(e) / 100, color: C.blue, knock: 0.5, carve: 2 }); setPose(e, 0); });
      } },
    SIG.rush("gojobf", "Black Flash", { say: "§0§lBLACK FLASH! §7— Gojo's fist distorts space", color: C.haki, dmg: 10, finisher: 46, hits: 3, poses: [5, 6, 5] }),
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
            try { o.applyKnockback({ x: n.x * 0.6, z: n.z * 0.6 }, lowLift(clamp(n.y * 0.4, 0, 0.3))); } catch (err) { /* ignore */ }
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
// Two Conqueror's Haki users release at once: black lightning crackles between them without touching;
// the weaker will buckles and is frozen for a moment.
function hakiClash(a, b) {
  const dim = a.dimension;
  announce(a, "§0§lCONQUEROR'S HAKI CLASH! §4§l— the sky splits");
  const winner = powerOf(a) >= powerOf(b) ? a : b;
  const loser = winner === a ? b : a;
  every(2, 12, (i) => {
    if (!a.isValid || !b.isValid) return false;
    const pa = aim(a), pb = aim(b);
    for (let k = 0; k <= 8; k++) {
      const t = k / 8, j = (k % 2 ? 1 : -1) * 0.4 * Math.sin(i + k);
      fx(dim, "orb_solid", V.add(V.add(pa, V.mul(V.sub(pb, pa), t)), { x: j, y: Math.cos(i * 2 + k) * 0.4, z: -j }), k % 3 ? C.haki : C.red, 0.7, 0.25);
    }
    if (i % 3 === 0) { fx(dim, "flash", V.add(pa, V.mul(V.sub(pb, pa), 0.5)), C.red, 3, 0.2); shake(dim, pa, 0.3, 0.2); }
  });
  later(26, () => {
    if (!alive(loser)) return;
    const ls = state(loser);
    ls.stunUntil = Math.max(ls.stunUntil, now() + 30);
    announce(loser, "§7...overwhelmed by the stronger will.");
  });
}
function conqueror(e, s) {
  busy(s, 16); setPose(e, 22);  // haki pouring out: fists clenched, braced
  const dim = e.dimension, c = V.up(e.location, 1);
  announce(e, "§4§lConqueror's Haki!");
  try {  // a rival Conqueror (Zoro, King of Hell) answers in kind
    for (const o of dim.getEntities({ location: e.location, maxDistance: 25, families: ["anime_fighter"] })) {
      if (o.typeId === "ab:zoro" && formOf(o) === 1 && alive(o) && teamOf(o) && teamOf(o) !== teamOf(e)) {
        later(4, () => { if (alive(o) && e.isValid) { setPose(o, 22); hakiClash(e, o); later(18, () => { if (o.isValid) setPose(o, 0); }); } });
        break;
      }
    }
  } catch (err) { /* ignore */ }
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
      const zone = (s.zoneUntil ?? 0) > now();
      const hitBF = Math.random() < (zone ? Math.min(0.75, bf * 2.2) : bf);
      if (hitBF) { s.zoneUntil = now() + 200; every(5, 40, () => { if (!alive(e) || (s.zoneUntil ?? 0) < now()) return false; fx(e.dimension, "streak", aim(e), Math.random() < 0.5 ? C.black : C.red, 0.7, 0.25, { count: 3, speed: 4 }); }); }
      deal(e, t, (hitBF ? 2.5 : 1) * 22 * powerOf(e) / 100);
      const c = aim(t);
      fx(e.dimension, "orb_solid", c, C.black, hitBF ? 2.2 : 1, 0.35);
      fx(e.dimension, "streak", c, hitBF ? C.red : C.ce, 1.8, 0.4, { count: hitBF ? 22 : 10, speed: 12 });
      fx(e.dimension, "streak", c, C.black, 1.6, 0.4, { count: hitBF ? 16 : 6, speed: 9 });
      if (hitBF) { fx(e.dimension, "shock_v", c, C.red, 5, 0.35); shake(e.dimension, c, 0.3, 0.3); screenFade(e.dimension, c, 30, 0.02, 0.06, 0.2, [70, 0, 0]); sound(e.dimension, "ab.blackflash", c, 2, 0.95 + Math.random() * 0.1); announce(e, "§0§l§kX§r §4§lBlack Flash §0§l§kX"); }
      try { const n = V.norm(V.sub(t.location, e.location)); t.applyKnockback({ x: n.x * 2.2, z: n.z * 2.2 }, lowLift(0.35)); } catch (err) { /* ignore */ }
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
  abilities: [
    SIG.rush("lariat", "Lariat", { say: "§d§lLARIAT!", color: C.white, dmg: 6, finisher: 22, hits: 2, poses: [11, 31] }),
    SIG.rush("bfchain", "Black Flash Chain", { say: "§0§lBLACK FLASH! §c§lx4 — in the zone", color: C.haki, dmg: 12, finisher: 26, hits: 4, poses: [5, 6, 5, 9], cd: 400, cost: 200 }),
    SIG.rush("divergentrush", "Divergent Fist Barrage", { say: "§d§lDivergent Fist! §7— the cursed energy lands a beat late", color: C.ce, dmg: 6, finisher: 18, hits: 5, poses: [5, 6, 5, 6, 5] }),
    SIG.rush("slaughter", "Slaughter Demon", { say: "§c§lSlaughter Demon! §7— the knife from Nanami", color: C.blood, dmg: 6, finisher: 18, hits: 4, poses: [19, 28, 19, 5] }),divergent, yujiCommon(0.2), {
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
  abilities: [
    SIG.rush("flowingred", "Flowing Red Scale", { say: "§c§lFlowing Red Scale! §7— his blood races", color: C.blood, dmg: 10, finisher: 34, hits: 5, poses: [5, 7, 6, 8, 9] }),
    SIG.ball("bloodmeteor", "Blood Meteorite", { say: "§4§lBlood Meteorite!", color: C.blood, count: 4, size: 1.0, dmg: 14, spread: 1.5, cd: 260 }),divergent, yujiCommon(0.6), {
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
      drawInside(e, center, 12);
      cinematic(e, 40, 6);
      buildDome(e, center, 13, "minecraft:white_concrete", "minecraft:pearlescent_froglight", 104);
      domainOpened(e);
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
  abilities: [
    SIG.slash("web", "Dismantle: Web", { say: "§c§lDismantle: Web §7— the ground is cut in a net", color: C.red, count: 4, dmg: 14, size: 2.2, roll: 20, cd: 300, cost: 200 }),
    SIG.wave("maxelephant", "Max Elephant", { cond: G(1), say: "§9§lTen Shadows: Max Elephant! §7— a flood pours down", color: C.blue, radius: 6, dmg: 30, cd: 400, cost: 220 }),
    SIG.slash("dismantlebarrage", "Dismantle Barrage", { say: "§c§lDismantle. §7— cut after cut after cut", color: C.red, count: 6, dmg: 9, size: 1.6, cd: 240 }),
    { id: "mahoraga", label: "Ten Shadows: Mahoraga", cd: 1200, cost: 600, min: 0, max: 26, weight: 7, cond: G(1, 2),
      run(e, s, t) {  // the strongest shikigami of the Ten Shadows, wheel turning above its head
        busy(s, 34); setPose(e, 21); announce(e, "§f§lWith this treasure I summon... §lEight-Handled Sword Divergent Sila Divine General MAHORAGA!");
        const v = summonGiant(e, 6, t, { size: 2.8, behind: 3, life: 70 });
        const dim = e.dimension;
        later(14, () => {  // the Sword of Extermination
          vset(v, "ab:pose", 1);
          if (alive(t)) { flyingSlash(e, t, { color: C.white, dmg: 50 * powerOf(e) / 100, range: 20, roll: 80, size: 3.4 }); shake(dim, t.location, 0.5, 0.4); }
        });
        later(36, () => {  // the wheel turns: it has adapted — a heavy blow
          vset(v, "ab:pose", 5);
          sound(dim, "random.anvil_land", e.location, 2, 0.5);
          if (alive(t)) { hitArea(e, V.up(t.location, 1), 4, 34 * powerOf(e) / 100, new Set(), { knock: 3, lift: 0.6 }); fx(dim, "shock", t.location, C.white, 8, 0.5); }
        });
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "nue", label: "Ten Shadows: Nue", cd: 260, cost: 140, min: 0, max: 36, weight: 4, cond: G(1, 2),
      run(e, s, t) {  // the owl shikigami dives out of the sky wreathed in lightning
        busy(s, 16); setPose(e, 21); announce(e, "§b§lNue! §7— the shikigami dives, crackling with lightning");
        later(10, () => {
          if (!e.isValid || !alive(t)) return;
          const c = t.location;
          for (let y = 16; y > 0; y -= 1) fx(e.dimension, "orb", V.add(c, { x: Math.sin(y) * 0.6, y, z: Math.cos(y * 2) * 0.6 }), C.kameBlue, 1.4, 0.3);
          explosion(e, V.up(c, 1), { radius: 3, dmg: 34 * powerOf(e) / 100, color: C.kameBlue, knock: 1.6 });
          if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 10); }
          setPose(e, 0);
        });
      } },
    SIG.rush("dogs", "Divine Dogs", { cond: G(1), say: "§8§lDivine Dogs! §7— the black and white wolves tear in", color: C.white, dmg: 7, finisher: 20, hits: 4, poses: [34, 34, 34, 34] }),yujiCommon(0.2), {
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
      raise(`shrine${e.id}`, dim, shrineCells(e), 8, 126);
      sound(dim, "ab.domain", center, 3, 0.8);
      cinematic(e, 44, 9);
      screenFade(dim, center, 40, 0.05, 0.2, 0.5, [90, 0, 0]);
      domainOpened(e);
      every(3, 40, (i) => {
        if (!e.isValid || (state(e).domainBroken ?? 0) > now()) return false;
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
    { id: "jetpistol", label: "Jet Pistol", cd: 140, cost: 70, min: 0, max: 12, weight: 4, cond: G(1),
      run(e, s, t) { stretch(e, s, t, { pose: 13, ticks: 6, reach: 6, radius: 2, dmg: 34, color: C.white, knock: 2.6, strong: true, say: "§c§lGum-Gum JET PISTOL!" }); } },
    { id: "giantpistol", label: "Giant Pistol", cd: 220, cost: 140, min: 0, max: 12, weight: 4, cond: G(2),
      run(e, s, t) { stretch(e, s, t, { pose: 16, ticks: 14, reach: 7, radius: 3, dmg: 60, color: C.haki, knock: 3, strong: true, say: "§c§lGum-Gum GIANT PISTOL!" }); } },
    { id: "kongorgan", label: "Kong Organ", cd: 320, cost: 200, min: 0, max: 12, weight: 5, cond: G(3),
      run(e, s, t) {
        busy(s, 24); announce(e, "§8§lGum-Gum KONG ORGAN! §7— a barrage of giant haki fists");
        every(3, 6, (i) => { if (alive(t) && e.isValid) { setPose(e, i % 2 ? 13 : 16); deal(e, t, 12 * powerOf(e) / 100); fx(t.dimension, "shock_v", aim(t), C.haki, 3, 0.3); if (i === 5) launch(e, t, 1.25); } });
        later(20, () => { if (e.isValid) setPose(e, 0); });
      } },
    SIG.slash("dawnwhip", "Dawn Whip", { cond: G(6), say: "§f§lGum-Gum DAWN WHIP! §7— his leg stretches into a cartoon whip", color: C.nika, count: 2, dmg: 30, size: 2.6, cd: 260, pose: 17 }),
    SIG.rush("dawnrocket", "Dawn Rocket", { cond: G(6), say: "§f§lGum-Gum DAWN ROCKET!", color: C.nika, dmg: 14, finisher: 48, hits: 3, poses: [9, 9, 18] }),
    { id: "redhawk", label: "Red Hawk", cd: 200, cost: 120, min: 0, max: 10, weight: 5, cond: G(1),
      run(e, s, t) { stretch(e, s, t, { pose: 13, ticks: 10, reach: 6, radius: 2.2, dmg: 46, color: C.fire, knock: 2.6, strong: true, say: "§c§lGum-Gum RED HAWK!" });
        later(8, () => { if (alive(t)) explosion(e, aim(t), { radius: 2.5, dmg: 14 * powerOf(e) / 100, color: C.fire, knock: 1 }); }); } },
    SIG.rush("jetgatling", "Jet Gatling", { cond: G(1), say: "§c§lGum-Gum JET GATLING!", color: C.white, dmg: 5, finisher: 14, hits: 7, poses: [14, 14, 14, 14] }),
    { id: "culverin", label: "Culverin", cd: 220, cost: 140, min: 0, max: 12, weight: 5, cond: G(3),
      run(e, s, t) { stretch(e, s, t, { pose: 13, ticks: 12, reach: 7, radius: 2.4, dmg: 60, color: C.haki, knock: 3, strong: true, say: "§8§lGum-Gum CULVERIN! §7— the punch that bends" }); } },
    SIG.rush("rhino", "Rhino Schneider", { cond: G(3), say: "§8§lGum-Gum RHINO SCHNEIDER!", color: C.haki, dmg: 10, finisher: 44, hits: 3, poses: [7, 12, 7], slam: true }),
    SIG.rush("blackmamba", "Black Mamba", { cond: G(4), say: "§8§lGum-Gum BLACK MAMBA! §7— punches that chase you round corners", color: C.haki, dmg: 6, finisher: 22, hits: 8, poses: [13, 14, 13, 14] }),
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
        try { e.applyKnockback({ x: 0, z: 0 }, lowLift(1.2)); } catch (err) { /* ignore */ }
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
          try { o.applyKnockback({ x: 0, z: 0 }, lowLift(1.6)); } catch (err) { /* ignore */ }
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
    SIG.slash("pound108", "108 Pound Cannon", { say: "§a§lThree Sword Style: 108 POUND CANNON!", color: C.zoro, count: 1, dmg: 44, size: 3.0, range: 32, cd: 260, cost: 160, pose: 1 }),
    SIG.rush("toragari", "Tiger Hunt", { say: "§a§lThree Sword Style: TIGER HUNT!", color: C.zoro, dmg: 10, finisher: 40, hits: 2, poses: [3, 10], slam: true }),
    SIG.rush("ushibari", "Bull Needle", { say: "§a§lThree Sword Style: BULL NEEDLE!", color: C.zoro, dmg: 8, finisher: 36, hits: 2, poses: [11, 5] }),
    { id: "hiryu", label: "Flying Dragon Blaze", cd: 200, cost: 110, min: 0, max: 10, weight: 5,
      run(e, s, t) {  // a rising slash that sets the cut ablaze
        busy(s, 16); announce(e, "§a§lOne Sword Style: §6§lFlying Dragon Blaze! §7— Hiryu Kaen");
        afterimage(e); teleportNear(e, t, false, 1.4); setPose(e, 9);
        const v = slashVfx(e.dimension, aim(t), { x: 0, y: 1, z: 0 }, C.fire, 2, 90); later(5, () => killVfx(v));
        deal(e, t, 30 * powerOf(e) / 100);
        try { t.applyKnockback({ x: 0, z: 0 }, lowLift(1.0)); } catch (err) { /* ignore */ }
        every(8, 6, () => { if (!alive(t)) return false; deal(e, t, 3 * powerOf(e) / 100); fx(t.dimension, "aura", t.location, C.fire, 1, 0.5, { count: 8, speed: 1.4 }); });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "kokujo", label: "Black Rope Dragon Twister", cd: 280, cost: 160, min: 0, max: 8, weight: 5, cond: G(1),
      run(e, s, t) {  // a tornado of black haki slashes
        busy(s, 22); setPose(e, 24); announce(e, "§0§lNine Sword Style... §2§lBlack Rope Great Dragon Twister!");
        const dim = e.dimension;
        every(3, 6, (i) => { if (!e.isValid) return false; ring(dim, V.up(e.location, i * 0.6), 2 + i * 0.6, i % 2 ? C.haki : C.zoro, 24, 0.5); });
        hitArea(e, V.up(e.location, 1), 5.5, 40 * powerOf(e) / 100, new Set(), { knock: 1.6, lift: 1.2 });
        later(18, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "yakkodori", label: "Yakkodori", cd: 140, cost: 70, min: 0, max: 26, weight: 4,
      run(e, s, t) {
        busy(s, 12); setPose(e, 19); announce(e, "§a§lOne Sword Style: Yakkodori!");
        flyingSlash(e, t, { color: C.zoro, dmg: 26 * powerOf(e) / 100, range: 26, roll: 0, size: 1.6 });
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
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
          for (const o of list) if (canHit(e, teamOf(e), o)) { deal(e, o, 4 * powerOf(e) / 100); try { o.applyKnockback({ x: 0, z: 0 }, lowLift(0.35)); } catch (err) { /* ignore */ } }
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
    { label: "Golden Frieza", power: 480, aura: C.gold },
  ],
  thresholds: [0.6], transformCd: 100,
  formSound: [null, "beacon.power"],
  abilities: [
    SIG.slash("deathwave", "Death Wave", { say: "§5§lDeath Wave. §7— a flick of the finger", color: C.death, count: 2, dmg: 24, size: 2.0, pose: 4 }),
    SIG.wave("deathstorm", "Death Storm", { say: "§5§lDeath Storm! §7— the ground explodes all round him", color: C.death, radius: 6, dmg: 26, cd: 300 }),
    SIG.ball("deathchaser", "Death Chaser", { say: "§5§lYou can run... §7— a homing ball of death", color: C.death, count: 2, size: 1.2, dmg: 24, homing: true, cd: 240 }),
    { id: "supernova", label: "Supernova", cd: 700, cost: 500, min: 0, max: 40, weight: 6, cond: G(1),
      run(e, s, t) {  // a giant golden-orange sun raised on one finger
        busy(s, 34); setPose(e, 23); announce(e, "§6§lSUPERNOVA! §7— this planet ends here");
        const dim = e.dimension;
        const ball = spawnVfx(dim, 1, V.up(e.location, 5), { slot: 11, size: 0.4, life: 60 });
        every(1, 22, (i) => { vset(ball, "ab:size", 0.4 + i * 0.12); try { if (ball?.isValid && e.isValid) ball.teleport(V.up(e.location, 5)); } catch (err) { /* ignore */ } });
        later(22, () => {
          killVfx(ball);
          if (!e.isValid) return;
          const start = V.up(e.location, 5);
          const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 12));
          projectile(e, start, V.norm(V.sub(tgt, start)), { speed: 0.8, maxDist: 50, radius: 2.6, size: 3.6, color: C.fire, slot: 11,
            explode: { radius: 7, dmg: 150 * powerOf(e) / 100, color: C.fire, carve: 3, knock: 3 } });
          later(10, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "psychobomb", label: "Death Psycho Bomb", cd: 260, cost: 140, min: 0, max: 24, weight: 4,
      run(e, s, t) {  // a pointed finger plants the energy inside the target — then it detonates
        busy(s, 12); face(e, aim(t)); setPose(e, 4); announce(e, "§5§lDeath Psycho Bomb. §7— you're already a bomb");
        if (!alive(t)) return;
        every(3, 6, () => { if (alive(t)) fx(t.dimension, "aura", t.location, C.death, 1.2, 0.5, { count: 10, speed: 1 }); });
        later(18, () => { if (alive(t)) explosion(e, aim(t), { radius: 2.8, dmg: 56 * powerOf(e) / 100, color: C.death, knock: 2 }); if (e.isValid) setPose(e, 0); });
      } },
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
        try { t.applyKnockback({ x: 0, z: 0 }, lowLift(1.4)); } catch (err) { /* ignore */ }
        every(2, 6, () => { if (alive(t)) fx(t.dimension, "orb", aim(t), C.death, 1.2, 0.3); });
        later(14, () => {
          if (!alive(t)) return;
          try { t.applyKnockback({ x: 0, z: 0 }, lowLift(-2)); } catch (err) { /* ignore */ }
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
// Valley of the End: Sasuke meets a Rasengan with a Chidori; the two collide halfway and the stronger pushes through.
function rasenganVsChidori(n, sk, o) {
  const ns = state(n), ss = state(sk);
  busy(ns, 30); busy(ss, 30);
  announce(n, "§b§lRASENGAN! §f§l— §b§lCHIDORI!");
  chargeOrb(n, sk, 12, C.blue, 0.3, o.size, 36);
  chargeOrb(sk, n, 12, C.kameBlue, 0.4, 1.1, 4);
  later(12, () => {
    if (!alive(n) || !alive(sk)) return;
    const a = n.location, b = sk.location;
    const mid = V.add(a, V.mul(V.sub(b, a), 0.5));
    try { n.teleport(V.add(a, V.mul(V.sub(b, a), 0.38)), { facingLocation: aim(sk) }); } catch (err) { /* ignore */ }
    try { sk.teleport(V.add(b, V.mul(V.sub(a, b), 0.38)), { facingLocation: aim(n) }); } catch (err) { /* ignore */ }
    setPose(n, 5); setPose(sk, 5);
    const dim = n.dimension, c = V.up(mid, 1.2);
    every(2, 8, (i) => {
      fx(dim, "flash", c, C.white, 3 + i * 0.4, 0.2);
      fx(dim, "orb", V.add(c, { x: -0.6, y: 0, z: 0 }), C.blue, 2.2, 0.2);
      fx(dim, "orb", V.add(c, { x: 0.6, y: 0, z: 0 }), C.kameBlue, 2.2, 0.2);
      fx(dim, "streak", c, C.white, 1.8, 0.3, { count: 10, speed: 10 });
      if (i % 2 === 0) shake(dim, c, 0.35, 0.2);
    });
    later(16, () => {
      const winner = powerOf(n) >= powerOf(sk) ? n : sk;
      const loser = winner === n ? sk : n;
      if (winner.isValid) explosion(winner, c, { radius: 3.5, dmg: 34 * powerOf(winner) / 100, color: winner === n ? C.blue : C.kameBlue, knock: 2.5, carve: 1 });
      if (alive(loser)) deal(winner, loser, 10 * powerOf(winner) / 100);
      for (const f of [n, sk]) if (f.isValid) later(6, () => setPose(f, 0));
    });
  });
}
function rasengan(e, s, t, o) {
  if (SASUKES.has(t.typeId) && !t.hasTag("ab_clone") && !e.hasTag("ab_clone")) {
    const ts = state(t);
    if (now() >= ts.busyUntil && ts.energy >= 90 && Math.random() < 0.6) {
      ts.energy -= 90;
      rasenganVsChidori(e, t, o);
      return;
    }
  }
  busy(s, 26); face(e, aim(t)); announce(e, o.say);
  chargeOrb(e, t, 12, o.color, 0.3, o.size, 36);
  later(12, () => {
    if (!e.isValid) return;
    if (!alive(t)) { setPose(e, 0); return; }
    afterimage(e); teleportNear(e, t, false, 1.3); face(e, aim(t)); setPose(e, 5);
    const c = aim(t), dim = e.dimension, pw = powerOf(e) / 100;
    deal(e, t, o.dmg * pw);
    const n = V.norm(V.sub(t.location, e.location));
    try { t.applyKnockback({ x: n.x * (o.knock ?? 2.5), z: n.z * (o.knock ?? 2.5) }, lowLift(0.45)); } catch (err) { /* ignore */ }
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
  if (o.color === C.hakai && kuramaAvatar(e)) summonGiant(e, 1, t, { size: 4, behind: 6, life: 40, pose: 2, poseAt: 6 });
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
      speed: 0.9, maxDist: 45, radius: 1.6, size: 1.8 * o.size, color: o.color ?? C.white, slot: o.color ? slotOf(o.color) : 10, trail: true, core: o.color ? C.white : undefined,
      homing: alive(t) ? t : undefined, homingStrength: 0.08,
      explode: { radius: o.radius, dmg: o.dmg * pw, color: o.color ?? C.white, carve: o.carve ?? 1, knock: 2 },
      onEnd: (pos) => {  // the wind sphere keeps slicing for a moment
        const dome = spawnVfx(dim, 1, pos, { slot: o.color ? slotOf(o.color) : 10, size: o.radius * 0.5, life: 30 });
        every(4, 5, () => {
          hitArea(e, pos, o.radius, o.dmg * 0.08 * pw, new Set(), { knock: 0.2 });
          fx(dim, "streak", pos, o.color ?? C.white, 2, 0.3, { count: 10, speed: 9 });
          if (o.burn) fx(dim, "aura", pos, o.color, o.radius * 0.5, 0.8, { count: 12, speed: 2 });
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

// Summoning: Gamabunta lands on the battlefield, crushes the ground and spits a water bullet.
const summonToad = (cond) => ({ id: "gamabunta", label: "Summoning: Gamabunta", cd: 900, cost: 300, min: 0, max: 30, weight: 5, cond,
  run(e, s, t) {
    busy(s, 30); setPose(e, 35); announce(e, "§a§lSummoning Jutsu! §6— §lGamabunta!");
    const dim = e.dimension;
    later(8, () => {
      if (!e.isValid) return;
      const c = alive(t) ? t.location : e.location;
      fx(dim, "aura", V.up(c, 2), C.white, 5, 1.2, { count: 60 * fxLevel(), speed: 3 });   // the summoning smoke
      const toDir = V.norm({ x: c.x - e.location.x, y: 0, z: c.z - e.location.z });
      const toad = summonGiant(e, 2, t, { at: V.sub(c, V.mul(toDir, 3)), size: 4, life: 64, pose: 3 });
      later(18, () => {  // the dosu comes down
        vset(toad, "ab:pose", 1);
        if (alive(t)) { flyingSlash(e, t, { color: C.white, dmg: 30 * powerOf(e) / 100, range: 14, roll: 80, size: 3 }); shake(dim, t.location, 0.4, 0.3); }
      });
      later(34, () => {  // Water Style: Water Gun — straight from its mouth
        vset(toad, "ab:pose", 4);
        if (!alive(t) || !toad?.isValid) return;
        const mouth = V.up(toad.location, 4.4);
        projectile(e, mouth, V.norm(V.sub(aim(t), mouth)), { speed: 1.6, maxDist: 30, radius: 1.8, size: 2.6, color: C.kameBlue, trail: true,
          explode: { radius: 3.6, dmg: 30 * powerOf(e) / 100, color: C.kameBlue, knock: 2.4 } });
      });
      later(6, () => {
        if (!e.isValid) return;
        fx(dim, "shock", c, { red: 0.55, green: 0.25, blue: 0.15 }, 10, 0.6);
        shake(dim, c, 0.6, 0.5);
        hitArea(e, V.up(c, 1), 5, 34 * powerOf(e) / 100, new Set(), { knock: 2.4, lift: 0.6 });
        later(8, () => { if (e.isValid) setPose(e, 0); });
      });
    });
  } });
const rasenRendan = (cond, o = {}) => ({ id: "rendan2", label: o.label ?? "Rasengan Barrage", cd: 300, cost: 200, min: 0, max: 16, weight: 5, cond,
  run(e, s, t) {
    busy(s, 30); announce(e, o.say ?? "§b§lRasengan Barrage!");
    shadowClones(e, s, 3, 80);
    every(6, 4, (i) => {
      if (!alive(t) || !e.isValid) return false;
      afterimage(e); teleportNear(e, t, i % 2 === 0, 1.3); setPose(e, 36);
      deal(e, t, (o.dmg ?? 16) * powerOf(e) / 100);
      const c = aim(t);
      for (let k = 0; k < 14; k++) { const a = (k / 14) * Math.PI * 4; fx(e.dimension, "orb", V.add(c, { x: Math.cos(a) * 0.7, y: 0, z: Math.sin(a) * 0.7 }), o.color ?? C.blue, 0.5, 0.3); }
      fx(e.dimension, "shock_v", c, o.color ?? C.blue, 2.5, 0.3);
      if (i === 3) later(6, () => { if (e.isValid) setPose(e, 0); });
    });
  } });
const kuramaBomb = (cond, o = {}) => ({ id: o.id ?? "bijuu", label: o.label ?? "Tailed Beast Bomb", cd: o.cd ?? 520, cost: o.cost ?? 380, min: 0, max: 45, weight: o.weight ?? 5, cond,
  run(e, s, t) {
    if (kuramaAvatar(e)) { summonGiant(e, 1, t, { size: 4, behind: 6, life: 50, pose: 2, poseAt: 6 }); announce(e, "§6§lKurama! §7— the giant fox rises behind him"); }
    bijuudama(e, s, t, { size: o.size ?? 3, radius: o.radius ?? 7, dmg: o.dmg ?? 150 });
  } });
const kuramaAssault = (cond) => ({ id: "kassault", label: "Kurama Avatar Assault", cd: 700, cost: 420, min: 0, max: 24, weight: 6, cond,
  run(e, s, t) {
    busy(s, 30); setPose(e, 22); announce(e, "§6§lKurama! §7— the giant fox rises and attacks");
    const k = summonGiant(e, 1, t, { size: 4, behind: 5, life: 70 });
    const dim = e.dimension;
    later(10, () => {  // a sweep of the claw
      vset(k, "ab:pose", 5);
      if (alive(t)) { slashMarks(e, t, C.gold, 3, 14 * powerOf(e) / 100); fx(dim, "shock", t.location, C.gold, 7, 0.4); }
    });
    later(28, () => {  // the nine tails lash round
      vset(k, "ab:pose", 6);
      if (alive(t)) hitArea(e, V.up(t.location, 1), 6, 28 * powerOf(e) / 100, new Set(), { knock: 3, lift: 0.7 });
      ring(dim, V.up(e.location, 1), 7, C.gold, 40, 0.6);
    });
    later(46, () => {  // and the jaws close on the target
      vset(k, "ab:pose", 4);
      if (alive(t)) { deal(e, t, 50 * powerOf(e) / 100); sphereFx(dim, aim(t), 2, C.gold, 24, 0.6, "orb", 0.4); sound(dim, "mob.ravager.bite", t.location, 2, 0.5); }
    });
    later(14, () => { if (e.isValid) setPose(e, 0); });
  } });
const sixPathsHeal = (cond) => ({ id: "yang", label: "Six Paths: Yang Power", cd: 700, cost: 200, min: 0, max: 60, weight: 8, cond: (e, s, c) => cond(e) && c.hp < 0.45,
  run(e, s) {
    busy(s, 14); setPose(e, 35); announce(e, "§e§lSix Paths Yang Power! §7— the life force mends his wounds");
    const h = health(e);
    if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + h.effectiveMax * 0.12));
    fx(e.dimension, "aura", e.location, C.gold, 1.4, 0.8, { count: 26, speed: 2 });
    ring(e.dimension, V.up(e.location, 0.2), 2.5, C.gold, 24, 0.5);
    later(12, () => { if (e.isValid) setPose(e, 0); });
  } });

const NARUTO_KID = {
  name: "Naruto", color: "§6", energy: 600, regen: 12, energyName: "§6CHAKRA",
  dodge: () => 0.08,
  forms: [{ label: "Genin (Part I)", power: 25 }, { label: "Nine-Tails Cloak", power: 45, aura: C.fire }],
  thresholds: [0.6], transformCd: 100, formSound: [null, "mob.enderdragon.growl"],
  abilities: [
    SIG.ball("kunai", "Kunai & Shuriken Barrage", { say: "§6§lShadow Clone Shuriken! §7— kunai from every clone", color: C.silver, count: 6, size: 0.4, dmg: 4, spread: 2, cd: 160, charge: 2, speed: 2 }),
    SIG.rush("clonebody", "Clone Body Blow", { say: "§6§lClones — dogpile!", color: C.white, dmg: 5, finisher: 16, hits: 4, poses: [5, 7, 6, 10], slam: true }),
    cloneJutsu(2),
    { id: "rendan", label: "Uzumaki Barrage", cd: 220, cost: 90, min: 0, max: 10, weight: 4,
      run(e, s, t) {
        busy(s, 30); announce(e, "§6§lU! ZU! MA! KI! — Naruto Uzumaki Barrage!");
        shadowClones(e, s, 2, 100);
        later(4, () => {
          if (!alive(t) || !e.isValid) return;
          teleportNear(e, t, false, 1.2); setPose(e, 7);
          deal(e, t, 10 * powerOf(e) / 100);
          try { t.applyKnockback({ x: 0, z: 0 }, lowLift(1.1)); } catch (err) { /* ignore */ }
          burst(e.dimension, aim(t), C.white, 12, 3, 0.4, 0.4);
        });
        later(14, () => {
          if (!alive(t) || !e.isValid) return;
          try { e.teleport(V.up(t.location, 3), { facingLocation: aim(t) }); } catch (err) { /* ignore */ }
          setPose(e, 10);
          deal(e, t, 16 * powerOf(e) / 100);
          try { t.applyKnockback({ x: 0, z: 0 }, lowLift(-1.6)); } catch (err) { /* ignore */ }
          fx(e.dimension, "shock", t.location, C.white, 4, 0.4);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    rasenganAbility("rasengan", "Rasengan", { say: "§b§lRasengan!", color: C.blue, size: 0.8, dmg: 28, radius: 1.6 }),
    summonToad(),
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
  name: "Naruto", color: "§6", energy: 1000, regen: 18, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) === 3 ? 0.14 : 0.1),  // Sage Mode senses every attack coming
  forms: [{ label: "Shippuden", power: 50 }, { label: "Version 1 — Three Tails", power: 60, aura: C.fire },
    { label: "Four-Tails (Version 2)", power: 70, aura: C.blood },
    { label: "Sage Mode", power: 88, aura: C.kiYellow }, { label: "Eight-Tails Form", power: 106, aura: C.blood }],
  thresholds: [0.85, 0.7, 0.5, 0.3], transformCd: 90, formSound: [null, "mob.enderdragon.growl", "mob.enderdragon.growl", "beacon.power", "mob.enderdragon.growl"],
  abilities: [
    SIG.ball("kunai", "Shadow Clone Kunai Barrage", { cond: G(0, 3), say: "§6§lMulti Shadow Clone — kunai!", color: C.silver, count: 8, size: 0.4, dmg: 4, spread: 2, cd: 160, charge: 2, speed: 2 }),
    rasenRendan(G(3), { label: "Sage Art: Big Ball Rasengan Barrage", say: "§e§lSage Art: Super Big Ball Rasen-Rengan!", dmg: 22 }),
    { id: "shroudrush", label: "Chakra Shroud Rush", cd: 130, cost: 70, min: 0, max: 14, weight: 5, cond: G(1),
      run(e, s, t) {
        busy(s, 18); announce(e, "§c§l(on all fours, the shroud boiling — he pounces)");
        every(4, 4, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.3); setPose(e, 34);
          slashMarks(e, t, C.fire, 2, 6 * powerOf(e) / 100);
          fx(t.dimension, "aura", t.location, C.fire, 1.2, 0.5, { count: 10, speed: 2 });
          if (i === 3) later(4, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    cloneJutsu(3, "§6§lMulti Shadow Clone Jutsu!"),
    rasenganAbility("rasengan", "Rasengan", { say: "§b§lRasengan!", color: C.blue, size: 1.0, dmg: 34, radius: 2 }, G(0, 3)),
    rasenganAbility("odama", "Big Ball Rasengan", { say: "§b§lBig Ball Rasengan!", color: C.blue, size: 1.8, dmg: 52, radius: 3.4, carve: 1, cd: 260, cost: 160 }, G(0, 3)),
    rasenganAbility("wind", "Wind Style: Rasenshuriken", { say: "§f§lWind Style: Rasenshuriken! §7— driven home by hand", color: C.white, size: 1.6, dmg: 64, radius: 3.6, carve: 1, cd: 420, cost: 260 }, G(0)),
    summonToad(G(0, 3)),
    { id: "v2arms", label: "Chakra Arm Stretch", cd: 150, cost: 80, min: 0, max: 14, weight: 5, cond: G(1, 2, 4),
      run(e, s, t) {
        busy(s, 16); setPose(e, 13); announce(e, "§4§l(a chakra arm lashes out across the field)");
        afterimage(e); teleportNear(e, t, false, 2.2);
        punches(e, t, 4, 9 * powerOf(e) / 100, C.blood);
        slashMarks(e, t, C.blood, 3, 6 * powerOf(e) / 100);
      } },
    { id: "v2roar", label: "Chakra Roar", cd: 240, cost: 120, min: 0, max: 8, weight: 4, cond: G(1, 2, 4),
      run(e, s, t) {
        busy(s, 16); setPose(e, 22); announce(e, "§4§lGRRRAAAAH!");
        const dim = e.dimension;
        fx(dim, "shock", e.location, C.blood, 9, 0.5); ring(dim, V.up(e.location, 0.2), 4.5, C.blood, 30, 0.5);
        sound(dim, "mob.enderdragon.growl", e.location, 1.5, 1.1);
        hitArea(e, V.up(e.location, 1), 5, 18 * powerOf(e) / 100, new Set(), { knock: 2.8, lift: 0.5 });
        later(14, () => { if (e.isValid) setPose(e, 0); });
      } },
    kuramaBomb(G(2), { id: "minibijuu", label: "Mini Tailed Beast Bomb", size: 1.4, radius: 4, dmg: 70, cd: 400, cost: 260 }),
    kuramaBomb(G(4), { label: "Tailed Beast Bomb", size: 2.6, radius: 6.5, dmg: 120 }),
    shurikenAbility("shuriken", "Sage Art: Rasenshuriken", { say: "§f§lSage Art: Wind Style Rasenshuriken!", size: 1.0, dmg: 80, radius: 4.5, carve: 1 }, G(3)),
    rasenRendan(G(3), { label: "Sage Art: Rasengan Barrage", say: "§e§lSage Art: Rasengan Barrage!", dmg: 16 }),
    { id: "kumite", label: "Frog Kumite", cd: 140, cost: 70, min: 0, max: 10, weight: 4, cond: G(3),
      run(e, s, t) {
        busy(s, 16); announce(e, "§e§lSage Art: Frog Kumite!"); afterimage(e); teleportNear(e, t, false, 1.6);
        punches(e, t, 5, 8 * powerOf(e) / 100, C.kiYellow);
        later(6, () => { if (alive(t)) hitArea(e, aim(t), 2.6, 8 * powerOf(e) / 100, new Set(), { knock: 1.8, lift: 0.3 }); });
      } },
  ],
};

const NARUTO_WAR = {
  name: "Naruto", color: "§e", energy: 1700, regen: 28, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) >= 2 ? 0.18 : 0.14),
  forms: [
    { label: "Nine-Tails Chakra Mode", power: 140, aura: C.gold },
    { label: "Kurama Mode", power: 165, aura: C.gold },
    { label: "Sage + Kurama Mode", power: 190, aura: C.gold },
    { label: "Six Paths Sage Mode", power: 240, aura: C.gold },
  ],
  thresholds: [0.75, 0.55, 0.35], transformCd: 80, formSound: [null, "mob.enderdragon.growl", "beacon.power", "beacon.activate"],
  abilities: [
    SIG.rush("kuramafist", "Kurama Mode Fists", { cond: G(1, 2, 3), say: "§6§lTailed Beast fists! §7— chakra arms pound the ground", color: C.gold, dmg: 12, finisher: 44, hits: 5, poses: [5, 6, 16, 6, 16], slam: true }),
    SIG.ball("tbballs", "Mini Tailed Beast Bomb Barrage", { cond: G(1, 2, 3), say: "§5§lMini Tailed Beast Bombs!", color: C.hakai, count: 4, size: 1.2, dmg: 30, spread: 1.5, cd: 380, cost: 260 }),
    kuramaAssault(G(1, 2, 3)),
    cloneJutsu(3, "§6§lMulti Shadow Clone Jutsu!"),
    rasenganAbility("rasengan", "Flash Rasengan", { say: "§e§lRasengan!", color: C.blue, size: 1.4, dmg: 40, radius: 2.6, cd: 140 }),
    shurikenAbility("shuriken", "Rasenshuriken", { say: "§f§lRasenshuriken!", size: 1.2, dmg: 70, radius: 5, carve: 2 }),
    rasenRendan(G(0, 1, 2, 3), { label: "Rasengan Barrage", say: "§e§lMulti Rasengan Barrage!", dmg: 18 }),
    chakraArms(C.gold),
    kuramaBomb(G(1, 2, 3), { dmg: 150 }),
    shurikenAbility("bijuushuriken", "Tailed Beast Rasenshuriken", { say: "§5§lTailed Beast Rasenshuriken!", size: 1.8, dmg: 130, radius: 7, carve: 3, color: C.hakai, cd: 560, cost: 400, weight: 5 }, G(1, 2, 3)),
    { id: "kclaw", label: "Kurama's Claws", cd: 200, cost: 120, min: 0, max: 12, weight: 4, cond: G(1, 2, 3),
      run(e, s, t) {
        busy(s, 16); announce(e, "§6§lKurama, lend me your power!"); afterimage(e); teleportNear(e, t, false, 2);
        slashMarks(e, t, C.gold, 5, 14 * powerOf(e) / 100);
        fx(e.dimension, "shock", t.location, C.gold, 6, 0.4);
      } },
    rasenganAbility("sageodama", "Sage Art: Super Big Ball Rasengan", { say: "§e§lSage Art: Super Big Ball Rasengan!", color: C.blue, size: 2.6, dmg: 90, radius: 4.5, carve: 2, cd: 360, cost: 260 }, G(2, 3)),
    { id: "gudo", label: "Truth-Seeking Balls", cd: 260, cost: 200, min: 0, max: 40, weight: 4, cond: G(3),
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
    shurikenAbility("lava", "Lava Release: Rasenshuriken", { say: "§6§lSix Paths: Lava Release Rasenshuriken!", size: 1.6, dmg: 120, radius: 6, carve: 2, color: C.fire, burn: true, cd: 480, cost: 320 }, G(3)),
    rasenganAbility("magnet", "Magnet Release: Rasengan", { say: "§0§lSix Paths: Magnet Release Rasengan!", color: C.black, size: 1.6, dmg: 80, radius: 3.4, cd: 300, cost: 200 }, G(3)),
    rasenganAbility("planetary", "Planetary Rasengan", { say: "§b§lPlanetary Rasengan!", color: C.blue, size: 2.2, dmg: 110, radius: 4, carve: 2, cd: 420, cost: 300, weight: 5 }, G(3)),
    sixPathsHeal(G(3)),
    shurikenAbility("ultra", "Six Paths Ultra Big Ball Rasenshuriken",
      { say: "§e§lSix Paths: Ultra Big Ball Rasenshuriken!", size: 2.6, dmg: 170, radius: 9, carve: 3, cd: 600, cost: 450, weight: 6 }, G(3)),
  ],
};

const NARUTO_ADULT = {
  name: "Naruto", color: "§6", energy: 1800, regen: 30, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) === 1 ? 0.17 : 0.14),
  forms: [
    { label: "Seventh Hokage", power: 150 },
    { label: "Sage Mode", power: 175, aura: C.kiYellow },
    { label: "Kurama Link Mode", power: 210, aura: C.gold },
    { label: "Baryon Mode", power: 290, aura: C.blood },
  ],
  thresholds: [0.8, 0.6, 0.35], transformCd: 80, formSound: [null, "beacon.power", "mob.enderdragon.growl", "mob.wither.spawn"],
  abilities: [
    SIG.rush("hokagecombo", "Hokage Clone Combo", { say: "§6§lShadow Clones — taijutsu!", color: C.white, dmg: 8, finisher: 30, hits: 5, poses: [5, 7, 6, 12, 10], slam: true }),
    SIG.ball("tbballs", "Mini Tailed Beast Bomb Barrage", { cond: G(2, 3), say: "§5§lMini Tailed Beast Bombs!", color: C.hakai, count: 4, size: 1.2, dmg: 32, spread: 1.5, cd: 380, cost: 260 }),
    kuramaAssault(G(2)),
    cloneJutsu(3, "§6§lMulti Shadow Clone Jutsu!"),
    rasenganAbility("rasengan", "Rasengan", { say: "§b§lRasengan!", color: C.blue, size: 1.4, dmg: 42, radius: 2.6, cd: 140 }),
    rasenganAbility("odama", "Big Ball Rasengan", { say: "§b§lBig Ball Rasengan!", color: C.blue, size: 2.0, dmg: 60, radius: 3.6, carve: 1, cd: 260, cost: 160 }, G(0, 1)),
    shurikenAbility("shuriken", "Rasenshuriken", { say: "§f§lRasenshuriken!", size: 1.4, dmg: 85, radius: 5.5, carve: 2 }),
    rasenRendan(G(1, 2), { label: "Sage Art: Rasengan Barrage", say: "§e§lSage Art: Rasengan Barrage!", dmg: 20 }),
    { id: "kumite", label: "Frog Kumite", cd: 140, cost: 70, min: 0, max: 10, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 16); announce(e, "§e§lSage Art: Frog Kumite!"); afterimage(e); teleportNear(e, t, false, 1.6);
        punches(e, t, 5, 9 * powerOf(e) / 100, C.kiYellow);
      } },
    chakraArms(C.gold, G(2)),
    kuramaBomb(G(2), { size: 3.2, radius: 7.5, dmg: 160 }),
    shurikenAbility("bijuushuriken", "Tailed Beast Rasenshuriken", { say: "§5§lTailed Beast Rasenshuriken!", size: 2.0, dmg: 140, radius: 7.5, carve: 3, color: C.hakai, cd: 560, cost: 400, weight: 5 }, G(2)),
    { id: "baryon", label: "Baryon Punch", cd: 180, cost: 140, min: 0, max: 14, weight: 6, cond: G(3),
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
    { id: "baryonrush", label: "Baryon Rush", cd: 240, cost: 160, min: 0, max: 20, weight: 4, cond: G(3),
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

// ------------------------------------------------------------------ Sasuke Uchiha (Part I, Shippuden, War, Adult)
// One move library, four versions: each version picks the techniques he really had at that age.
const SASUKES = new Set(["ab:sasuke_kid", "ab:sasuke", "ab:sasuke_war", "ab:sasuke_adult"]);
const SAS = {
  chidori: (o = {}) => ({ id: o.id ?? "chidori", label: o.label ?? "Chidori", cd: 140, cost: 90, min: 0, max: 20, weight: 5, cond: o.cond,
    run(e, s, t) {
      const col = o.color ?? C.kameBlue;
      busy(s, 22); face(e, aim(t)); announce(e, o.say ?? "§b§lChidori!");
      later(8, () => susanooPose(e, 5, 14));      // his Susanoo swings with him
      chargeOrb(e, t, 10, col, 0.4, 1.1, 4);
      every(2, 5, () => { if (e.isValid) fx(e.dimension, "streak", handPos(e, alive(t) ? t : e).pos, C.white, 0.8, 0.2, { count: 4, speed: 6 }); });
      later(10, () => {
        if (!e.isValid || !alive(t)) return;
        afterimage(e); teleportNear(e, t, false, 1.2); setPose(e, 5);
        const c = aim(t);
        deal(e, t, (o.dmg ?? 34) * powerOf(e) / 100);
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 8); }  // the lightning locks the muscles
        fx(e.dimension, "streak", c, col, 1.8, 0.4, { count: 22, speed: 12 });
        fx(e.dimension, "flash", c, C.white, 3, 0.2);
        burst(e.dimension, c, col, 20, 4, 0.4, 0.4);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  fireball: (o = {}) => ({ id: "fireball", label: "Great Fireball", cd: 160, cost: 90, min: 0, max: 30, weight: 4, cond: o.cond,
    run(e, s, t) {
      busy(s, 16); face(e, aim(t)); setPose(e, 21); announce(e, "§6§lFire Style: Great Fireball Technique!");
      later(8, () => {
        if (!e.isValid) return;
        setPose(e, 4);
        const { pos } = handPos(e, alive(t) ? t : e);
        const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 10));
        projectile(e, pos, V.norm(V.sub(tgt, pos)), { speed: 0.9, maxDist: 30, radius: 1.6, size: (o.size ?? 2.4), color: C.fire, slot: 11, trail: true,
          explode: { radius: 3.5, dmg: 30 * powerOf(e) / 100, color: C.fire, carve: 1, knock: 1.6 } });
        later(8, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  phoenix: () => ({ id: "phoenix", label: "Phoenix Flower", cd: 150, cost: 70, min: 0, max: 26, weight: 4,
    run(e, s, t) {
      busy(s, 16); face(e, aim(t)); setPose(e, 21); announce(e, "§6§lFire Style: Phoenix Flower Technique!");
      later(6, () => {
        if (!e.isValid) return;
        setPose(e, 4);
        const { pos } = handPos(e, alive(t) ? t : e);
        const base = V.norm(V.sub(alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 10)), pos));
        const side = { x: -base.z, y: 0, z: base.x };
        for (let k = -2; k <= 2; k++) {  // five fireballs fanning out, each hiding a shuriken
          const d = V.norm(V.add(base, V.mul(side, k * 0.12)));
          later(Math.abs(k) * 2, () => projectile(e, pos, d, { speed: 1.1, maxDist: 26, radius: 1.1, size: 0.9, color: C.fire, slot: 11, trail: true,
            explode: { radius: 1.6, dmg: 9 * powerOf(e) / 100, color: C.fire, knock: 0.6 } }));
        }
        later(10, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  lion: () => ({ id: "lion", label: "Lion Combo", cd: 170, cost: 70, min: 0, max: 8, weight: 4,
    run(e, s, t) {
      busy(s, 22); announce(e, "§9§lLion Combo! §7— the move he copied from Lee");
      afterimage(e); teleportNear(e, t, false, 1.2); setPose(e, 9);
      deal(e, t, 8 * powerOf(e) / 100);
      try { t.applyKnockback({ x: 0, z: 0 }, lowLift(1.1)); } catch (err) { /* ignore */ }
      later(8, () => {  // shadow of the leaf: behind him in the air, then the crushing heel
        if (!e.isValid || !alive(t)) return;
        try { e.teleport(V.up(t.location, 1.6), { facingLocation: aim(t) }); } catch (err) { /* ignore */ }
        setPose(e, 7); deal(e, t, 8 * powerOf(e) / 100);
        later(4, () => {
          if (!e.isValid || !alive(t)) return;
          setPose(e, 10); deal(e, t, 18 * powerOf(e) / 100);
          try { t.applyKnockback({ x: 0, z: 0 }, lowLift(-1.6)); } catch (err) { /* ignore */ }
          fx(t.dimension, "shock", t.location, C.white, 5, 0.4);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      });
    } }),
  nagashi: (o = {}) => ({ id: "nagashi", label: "Chidori Current", cd: 200, cost: 100, min: 0, max: 5, weight: 3, cond: o.cond,
    run(e, s, t) {
      busy(s, 14); setPose(e, 22); announce(e, "§b§lChidori Current!");
      const dim = e.dimension;
      fx(dim, "shock", e.location, C.kameBlue, 7, 0.4);
      fx(dim, "streak", V.up(e.location, 1), C.white, 2, 0.4, { count: 26, speed: 10 });
      let list = []; try { list = dim.getEntities({ location: e.location, maxDistance: 4 }); } catch (err) { /* ignore */ }
      for (const x of list) {
        if (!canHit(e, teamOf(e), x)) continue;
        deal(e, x, 16 * powerOf(e) / 100);
        if (isFighter(x)) { const xs = state(x); xs.stunUntil = Math.max(xs.stunUntil, now() + 16); }  // paralysed by the current
      }
      later(12, () => { if (e.isValid) setPose(e, 0); });
    } }),
  spear: () => ({ id: "spear", label: "Chidori Spear", cd: 150, cost: 80, min: 0, max: 16, weight: 4,
    run(e, s, t) {
      busy(s, 14); face(e, aim(t)); setPose(e, 4); announce(e, "§b§lChidori Sharp Spear!");
      beam(e, alive(t) ? t : e, { color: C.kameBlue, width: 0.45, length: 16, dmg: 30 * powerOf(e) / 100, blast: 1.2, ticks: 3, sound: "random.anvil_land", pitch: 1.6 });
      later(10, () => { if (e.isValid) setPose(e, 0); });
    } }),
  senbon: () => ({ id: "senbon", label: "Chidori Senbon", cd: 160, cost: 80, min: 0, max: 22, weight: 3,
    run(e, s, t) {
      busy(s, 14); face(e, aim(t)); setPose(e, 27); announce(e, "§b§lChidori Senbon!");
      later(4, () => {
        if (!e.isValid) return;
        const { pos } = handPos(e, alive(t) ? t : e);
        for (let k = 0; k < 6; k++) {
          const tgt = alive(t) ? V.add(aim(t), { x: (Math.random() - 0.5) * 1.2, y: (Math.random() - 0.5) * 1.2, z: (Math.random() - 0.5) * 1.2 }) : V.add(pos, e.getViewDirection());
          later(k, () => projectile(e, pos, V.norm(V.sub(tgt, pos)), { speed: 2.2, maxDist: 24, radius: 0.8, size: 0.35, color: C.kameBlue,
            explode: { radius: 0.8, dmg: 6 * powerOf(e) / 100, color: C.kameBlue, knock: 0.2 } }));
        }
        later(10, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  kirin: () => ({ id: "kirin", label: "Kirin", cd: 700, cost: 400, min: 0, max: 40, weight: 5,
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
    } }),
  genjutsu: (o = {}) => ({ id: "genjutsu", label: o.label ?? "Sharingan Genjutsu", cd: 380, cost: 160, min: 0, max: 14, weight: 4, cond: o.cond,
    run(e, s, t) {
      busy(s, 12); face(e, aim(t)); setPose(e, 26); announce(e, o.say ?? "§c§l(the Sharingan turns) §7— look into my eyes");
      if (!alive(t)) return;
      fx(t.dimension, "flash", V.up(t.location, 1.6), C.red, 2.4, 0.3);
      ring(t.dimension, V.up(t.location, 1.7), 1.2, C.red, 18, 0.4);
      if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + (o.stun ?? 30)); }
      deal(e, t, (o.dmg ?? 8) * powerOf(e) / 100);
      later(12, () => { if (e.isValid) setPose(e, 0); });
    } }),
  amaterasu: (o = {}) => ({ id: "amaterasu", label: "Amaterasu", cd: 400, cost: 220, min: 0, max: 30, weight: 5, cond: o.cond,
    run(e, s, t) {
      busy(s, 14); face(e, aim(t)); setPose(e, 26); announce(e, "§0§lAmaterasu! §7— black flames that never go out");
      every(8, 12, () => {
        if (!alive(t)) return false;
        deal(e, t, 7 * powerOf(e) / 100);
        fx(t.dimension, "orb_solid", V.up(t.location, 1 + Math.random()), C.black, 1.6, 0.6);
        fx(t.dimension, "aura", t.location, C.black, 1.2, 0.7, { count: 8, speed: 1.5 });
      });
      later(12, () => { if (e.isValid) setPose(e, 0); });
    } }),
  kagutsuchi: (o = {}) => ({ id: "kagutsuchi", label: "Blaze Release: Kagutsuchi", cd: 300, cost: 180, min: 0, max: 26, weight: 4, cond: o.cond,
    run(e, s, t) {
      busy(s, 18); setPose(e, 19); announce(e, "§0§lBlaze Release: §4§lKagutsuchi's Sword!");
      flyingSlash(e, t, { color: C.black, dmg: 34 * powerOf(e) / 100, range: 26, roll: 30, size: 2.2 });
      every(8, 6, () => {  // the shaped black flame keeps burning where it cut
        if (!alive(t)) return false;
        deal(e, t, 4 * powerOf(e) / 100);
        fx(t.dimension, "aura", t.location, C.black, 1.1, 0.6, { count: 8, speed: 1.4 });
      });
      later(10, () => { if (e.isValid) setPose(e, 0); });
    } }),
  arrow: (o = {}) => ({ id: "arrow", label: "Susanoo Arrow", cd: 260, cost: 200, min: 0, max: 45, weight: 4, cond: o.cond,
    run(e, s, t) {
      busy(s, 20); face(e, aim(t)); setPose(e, 20); announce(e, o.say ?? "§5§lSusanoo: Arrow!");
      susanooPose(e, 2, 22);
      later(10, () => {
        if (!e.isValid) return;
        const { pos } = handPos(e, alive(t) ? t : e);
        const tgt = alive(t) ? aim(t) : V.add(e.location, V.mul(e.getViewDirection(), 12));
        projectile(e, pos, V.norm(V.sub(tgt, pos)), { speed: 2.2, maxDist: 50, radius: 1.4, size: o.size ?? 1.2, color: o.color ?? C.purple, slot: 6, pierce: true, trail: true,
          dmg: (o.dmg ?? 60) * powerOf(e) / 100, explode: { radius: 3, dmg: 20 * powerOf(e) / 100, color: o.color ?? C.purple, knock: 2 } });
        later(8, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  susSword: (o = {}) => ({ id: "susSword", label: "Susanoo Sword", cd: 240, cost: 180, min: 0, max: 30, weight: 5, cond: o.cond,
    run(e, s, t) {
      busy(s, 20); setPose(e, 23); announce(e, "§5§lSusanoo! §7— the great blade comes down");
      later(4, () => susanooPose(e, 1, 20));
      later(8, () => {
        if (!e.isValid) return;
        setPose(e, 19);
        flyingSlash(e, t, { color: C.purple, dmg: (o.dmg ?? 56) * powerOf(e) / 100, range: 30, roll: 85, carve: true, size: 3.4 });
        if (alive(t)) { fx(t.dimension, "shock", t.location, C.purple, 6, 0.4); shake(t.dimension, t.location, 0.35, 0.3); }
        later(10, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  indra: () => ({ id: "indra", label: "Indra's Arrow", cd: 1000, cost: 700, min: 0, max: 50, weight: 8, cond: G(2),
    run(e, s, t) {
      busy(s, 44); setPose(e, 20); face(e, aim(t)); announce(e, "§5§lIndra's Arrow! §7— the chakra of all nine tailed beasts in one shot");
      susanooPose(e, 2, 42);
      const dim = e.dimension;
      chargeOrb(e, t, 22, C.purple, 0.5, 2.6, 20);
      every(2, 11, () => { if (e.isValid) { fx(dim, "streak", V.up(e.location, 1.5), C.kameBlue, 2, 0.3, { count: 8, speed: 10 }); fx(dim, "aura", e.location, C.purple, 2.2, 0.8, { count: 16, speed: 3 }); } });
      later(22, () => {
        if (!e.isValid) return;
        beam(e, alive(t) ? t : e, { color: C.purple, width: 3.4, length: 52, dmg: 220 * powerOf(e) / 100, carve: 3, blast: 7.5, ticks: 8, pitch: 0.5 });
        later(18, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  ameno: (o = {}) => ({ id: "ameno", label: "Amenotejikara", cd: 150, cost: 80, min: 0, max: 30, weight: 5, cond: o.cond,
    run(e, s, t) {
      busy(s, 12); announce(e, "§5§l(Rinnegan) §d§lAmenotejikara! §7— they've switched places");
      if (!alive(t)) return;
      const a = e.location, b = t.location;
      fx(e.dimension, "flash", V.up(a, 1), C.purple, 2, 0.15); fx(e.dimension, "flash", V.up(b, 1), C.purple, 2, 0.15);
      try { e.teleport(V.add(b, V.mul(V.norm(V.sub(a, b)), -1.4)), { facingLocation: aim(t) }); } catch (err) { /* ignore */ }
      setPose(e, 19);
      later(2, () => {
        if (!e.isValid || !alive(t)) return;
        slashMarks(e, t, C.kameBlue, 2, 14 * powerOf(e) / 100);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
  raiha: () => ({ id: "raiha", label: "Yin Release: Lightning", cd: 260, cost: 160, min: 0, max: 36, weight: 5,
    run(e, s, t) {
      busy(s, 20); setPose(e, 23); announce(e, "§5§lYin Release Lightning! §7— purple bolts from the Rinnegan");
      const dim = e.dimension;
      every(5, 3, () => {
        if (!e.isValid || !alive(t)) return false;
        const c = t.location;
        for (let y = 14; y > 0; y -= 1) fx(dim, "orb", V.add(c, { x: Math.sin(y * 2) * 0.5, y, z: Math.cos(y * 3) * 0.5 }), C.purple, 1.4, 0.3);
        explosion(e, V.up(c, 0.6), { radius: 2.5, dmg: 22 * powerOf(e) / 100, color: C.purple, knock: 1 });
      });
      later(18, () => { if (e.isValid) setPose(e, 0); });
    } }),
  blackChidori: () => ({ id: "blackChidori", label: "Chidori (Cursed Seal)", cd: 160, cost: 110, min: 0, max: 20, weight: 6, cond: (e) => formOf(e) >= 1,
    run(e, s, t) {
      busy(s, 24); face(e, aim(t)); announce(e, "§0§lChidori! §5§l— blackened by the Cursed Seal");
      chargeOrb(e, t, 12, C.hakai, 0.4, 1.4, 4);
      later(12, () => {
        if (!e.isValid || !alive(t)) return;
        afterimage(e); teleportNear(e, t, false, 1.2); setPose(e, 5);
        const c = aim(t);
        deal(e, t, 44 * powerOf(e) / 100);
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 10); }
        fx(e.dimension, "streak", c, C.hakai, 2, 0.4, { count: 24, speed: 12 });
        explosion(e, c, { radius: 2.2, dmg: 10 * powerOf(e) / 100, color: C.hakai, knock: 1.6 });
        later(8, () => { if (e.isValid) setPose(e, 0); });
      });
    } }),
};
SAS.dragonFlame = () => ({ id: "dragonflame", label: "Dragon Flame Jutsu", cd: 220, cost: 110, min: 0, max: 22, weight: 4,
  run(e, s, t) {  // a stream of fire racing along a line to the target
    busy(s, 18); face(e, aim(t)); setPose(e, 21); announce(e, "§6§lFire Style: Dragon Flame Jutsu!");
    later(6, () => {
      if (!e.isValid) return;
      setPose(e, 4);
      const { pos } = handPos(e, alive(t) ? t : e);
      const d = V.norm(V.sub(alive(t) ? aim(t) : V.add(pos, e.getViewDirection()), pos));
      every(1, 8, (i) => projectile(e, pos, d, { speed: 1.4, maxDist: 24, radius: 1.2, size: 1.4 + i * 0.1, color: C.fire, slot: 11,
        explode: i === 7 ? { radius: 3, dmg: 24 * powerOf(e) / 100, color: C.fire, knock: 1.4 } : undefined, dmg: 3 * powerOf(e) / 100, pierce: i < 7 }));
      later(12, () => { if (e.isValid) setPose(e, 0); });
    });
  } });
SAS.fuma = () => ({ id: "fuma", label: "Demon Wind Shuriken", cd: 160, cost: 50, min: 0, max: 24, weight: 3,
  run(e, s, t) {  // the giant folding shuriken, with a second one hidden in its shadow
    busy(s, 14); face(e, aim(t)); setPose(e, 13); announce(e, "§7§lDemon Wind Shadow Shuriken! §8— a second one hides in its shadow");
    const { pos } = handPos(e, alive(t) ? t : e);
    const d = V.norm(V.sub(alive(t) ? aim(t) : V.add(pos, e.getViewDirection()), pos));
    for (const k of [0, 4]) later(k, () => projectile(e, pos, d, { speed: 1.3, maxDist: 26, radius: 1.2, size: 1.0, color: C.silver, trail: true,
      explode: { radius: 1.6, dmg: 12 * powerOf(e) / 100, color: C.silver, knock: 0.6 } }));
    later(10, () => { if (e.isValid) setPose(e, 0); });
  } });
SAS.katana = () => SIG.rush("chidorikatana", "Chidori Katana", { say: "§b§lChidori Katana! §7— lightning runs down the Kusanagi", color: C.kameBlue, dmg: 10, finisher: 34, hits: 4, poses: [19, 28, 19, 5] });
SAS.onslaught = () => ({ id: "onslaught", label: "Susanoo Onslaught", cd: 420, cost: 260, min: 0, max: 26, weight: 6, cond: (e) => !!state(e).susanoo,
  run(e, s, t) {  // the Susanoo itself fights: the sword, the fist, then the bow
    busy(s, 40); setPose(e, 26); announce(e, "§5§lSusanoo! §7— sword, fist, arrow");
    later(4, () => { susanooPose(e, 1, 16); if (alive(t)) { flyingSlash(e, t, { color: C.purple, dmg: 40 * powerOf(e) / 100, range: 30, roll: 85, size: 3.4 }); } });
    later(20, () => { susanooPose(e, 5, 14); if (alive(t)) { hitArea(e, V.up(t.location, 1), 4, 26 * powerOf(e) / 100, new Set(), { knock: 3, lift: 0.5 }); fx(e.dimension, "shock", t.location, C.purple, 7, 0.4); } });
    later(34, () => {
      susanooPose(e, 2, 16);
      if (!alive(t) || !e.isValid) return;
      const start = V.up(e.location, 4);
      projectile(e, start, V.norm(V.sub(aim(t), start)), { speed: 2.4, maxDist: 50, radius: 1.5, size: 1.6, color: C.purple, slot: 6, pierce: true, trail: true,
        dmg: 50 * powerOf(e) / 100, explode: { radius: 3.4, dmg: 20 * powerOf(e) / 100, color: C.purple, knock: 2 } });
    });
    later(40, () => { if (e.isValid) setPose(e, 0); });
  } });
const SASUKE_KID = {
  name: "Sasuke", color: "§9", energy: 520, regen: 10, energyName: "§6CHAKRA",
  dodge: (e) => 0.12,
  forms: [{ label: "Sharingan", power: 24 }, { label: "Cursed Seal Level 1", power: 34, aura: C.hakai }, { label: "Cursed Seal Level 2", power: 50, aura: C.purple }],
  thresholds: [0.7, 0.45], transformCd: 90, formSound: [null, "mob.wither.ambient", "mob.wither.spawn"],
  abilities: [SAS.fireball({ size: 1.8 }), SAS.phoenix(), SAS.lion(), SAS.chidori({ cond: G(0) }), SAS.blackChidori(), SAS.fuma(), SAS.dragonFlame()],
};
const SASUKE = {
  name: "Sasuke", color: "§9", energy: 900, regen: 16, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) === 2 ? 0.18 : 0.14),  // the Sharingan reads the blow before it lands
  forms: [{ label: "Sharingan", power: 70 }, { label: "Cursed Seal Level 2", power: 80, aura: C.hakai }, { label: "Mangekyo Sharingan — Susanoo", power: 98, aura: C.purple }],
  thresholds: [0.7, 0.45], transformCd: 100, formSound: [null, "mob.wither.ambient", "mob.wither.spawn"],
  abilities: [SAS.katana(), SAS.dragonFlame(), SAS.onslaught(), SAS.chidori(), SAS.fireball(), SAS.nagashi(), SAS.spear(), SAS.senbon(), SAS.kirin(), SAS.genjutsu({ cond: G(0, 1) }),
    SAS.blackChidori(), SAS.amaterasu({ cond: G(2) }), SAS.kagutsuchi({ cond: G(2) }), SAS.arrow({ cond: G(2) })],
};
const SASUKE_WAR = {
  name: "Sasuke", color: "§5", energy: 1500, regen: 26, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) === 2 ? 0.2 : 0.17),
  forms: [{ label: "Eternal Mangekyo — Susanoo", power: 150, aura: C.purple }, { label: "Perfect Susanoo", power: 175, aura: C.purple },
    { label: "Rinnegan — Six Paths chakra", power: 210, aura: C.galick }],
  thresholds: [0.6, 0.35], transformCd: 100, formSound: [null, "mob.wither.spawn", "beacon.activate"],
  abilities: [SAS.katana(), SAS.dragonFlame(), SAS.onslaught(), SAS.chidori({ dmg: 40 }), SAS.spear(), SAS.senbon(), SAS.nagashi(), SAS.kirin(), SAS.fireball({ size: 3 }), SAS.amaterasu(), SAS.kagutsuchi(),
    SAS.arrow({ say: "§5§lSusanoo: Yasaka Magatama!", dmg: 70 }), SAS.susSword({ cond: G(1, 2) }), SAS.indra(),
    SAS.ameno({ cond: G(2) }), SAS.chidori({ id: "susChidori", label: "Susanoo Chidori", say: "§5§lSusanoo Chidori!", color: C.purple, dmg: 60, cond: G(1, 2) })],
};
const SASUKE_ADULT = {
  name: "Sasuke", color: "§5", energy: 1500, regen: 28, energyName: "§6CHAKRA",
  dodge: (e) => 0.19,
  forms: [{ label: "Rinnegan", power: 160, aura: C.galick }, { label: "Perfect Susanoo", power: 190, aura: C.purple }],
  thresholds: [0.5], transformCd: 100, formSound: [null, "mob.wither.spawn"],
  abilities: [SAS.katana(), SAS.onslaught(), SAS.chidori({ dmg: 42 }), SAS.spear(), SAS.kirin(), SAS.amaterasu(), SAS.kagutsuchi(), SAS.ameno(), SAS.raiha(),
    SAS.genjutsu({ label: "Rinnegan Genjutsu", say: "§5§l(the Rinnegan glows) §7— you are already in my genjutsu", stun: 34, dmg: 12 }),
    SAS.arrow({ cond: G(1), dmg: 76 }), SAS.susSword({ cond: G(1), dmg: 64 })],
};

// ------------------------------------------------------------------ Ichigo Kurosaki (Bleach)
// Getsuga colour per form: Shikai/Fullbring blue, Bankai black-red, Hollow/Vasto red, Mugetsu black, True Bankai blue-white
const ICH_GETSUGA = [C.kameBlue, C.kameBlue, C.haki, C.red, C.red, C.black, C.bigBang];
const ICHIGO = {
  name: "Ichigo", color: "§6", energy: 1600, regen: 28, energyName: "§bREIATSU",
  dodge: (e) => [0.12, 0.14, 0.15, 0.15, 0.17, 0.15, 0.16][formOf(e)] ?? 0.12,  // Bankai/Sonido speed
  forms: [
    { label: "Shikai — Zangetsu", power: 90 },
    { label: "Complete Fullbring", power: 125, aura: C.white },
    { label: "Bankai — Tensa Zangetsu", power: 150, aura: C.black },
    { label: "Hollow Mask", power: 200, aura: C.red },
    { label: "Vasto Lorde", power: 250, aura: C.haki },
    { label: "Final Getsuga Tensho (Mugetsu)", power: 300, aura: C.black },
    { label: "True Bankai — Zangetsu", power: 360, aura: C.bigBang },
  ],
  thresholds: [0.85, 0.72, 0.6, 0.48, 0.36, 0.25], transformCd: 80,
  formSound: [null, "beacon.activate", "mob.wither.spawn", "mob.enderdragon.growl", "mob.enderdragon.growl", "mob.wither.spawn", "beacon.power"],
  abilities: [
    SIG.slash("getsugabarrage", "Getsuga Tensho Barrage", { cond: G(2, 3, 6), say: "§4§lGetsuga — Getsuga — GETSUGA TENSHO!", color: C.haki, count: 3, dmg: 26, size: 2.2, cd: 300, cost: 200 }),
    SIG.slash("cerogetsuga", "Cero Getsuga", { cond: G(3, 4), say: "§4§lA Getsuga Tensho soaked in Cero!", color: C.red, count: 1, dmg: 60, size: 3.2, cd: 320, cost: 220 }),
    { id: "getsuga", label: "Getsuga Tensho", cd: 110, cost: 70, min: 0, max: 30, weight: 5, cond: G(0, 1, 2, 3, 6),
      run(e, s, t) {
        busy(s, 14); setPose(e, 19); announce(e, formOf(e) === 3 ? "§4§lGetsuga... TENSHO! §7(the mask's red reiatsu)" : "§b§lGetsuga... TENSHO!");
        const f = formOf(e), col = ICH_GETSUGA[f];
        flyingSlash(e, t, { color: col, dmg: 30 * powerOf(e) / 100, range: 28, roll: 20, carve: true, size: 1.6 + f * 0.2 });
        if (f >= 2) flyingSlash(e, t, { color: C.white, dmg: 0, range: 28, roll: 20, size: 1.1 + f * 0.15 });  // the bright edge
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "clothswing", label: "Zangetsu: Cloth Swing", cd: 150, cost: 60, min: 0, max: 5, weight: 4, cond: G(0),
      run(e, s, t) {
        busy(s, 18); setPose(e, 24); announce(e, "§f§lZangetsu! §7— swung round by its cloth");
        const dim = e.dimension, hit = new Set();
        every(3, 5, (i) => {
          if (!e.isValid) return false;
          ring(dim, V.up(e.location, 1), 3.6, C.white, 22, 0.4);
          const v = slashVfx(dim, V.up(e.location, 1), { x: Math.cos(i * 1.3), y: 0, z: Math.sin(i * 1.3) }, C.kameBlue, 1.8, 90);
          later(3, () => killVfx(v));
          if (i === 2) hitArea(e, V.up(e.location, 1), 4.2, 26 * powerOf(e) / 100, hit, { knock: 1.6, lift: 0.4 });
        });
        later(16, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "bringer", label: "Bringer Light", cd: 140, cost: 80, min: 0, max: 22, weight: 5, cond: G(1),
      run(e, s, t) {
        busy(s, 20); announce(e, "§f§lFullbring: Bringer Light!");
        every(4, 4, (i) => {
          if (!alive(t) || !e.isValid) return false;
          fx(e.dimension, "streak", V.up(e.location, 1), C.white, 1.4, 0.4, { count: 12, speed: 8 });
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.4); setPose(e, i % 2 ? 28 : 19);
          slashMarks(e, t, C.kameBlue, 2, 6 * powerOf(e) / 100);
          if (i === 3) setPose(e, 0);
        });
      } },
    { id: "fbgetsuga", label: "Fullbring Getsuga Tensho", cd: 200, cost: 120, min: 0, max: 30, weight: 4, cond: G(1),
      run(e, s, t) {
        busy(s, 18); setPose(e, 1); announce(e, "§b§lFullbring... §f§lGetsuga Tensho!");
        flyingSlash(e, t, { color: C.kameBlue, dmg: 40 * powerOf(e) / 100, range: 30, roll: 0, carve: true, size: 2.4 });
        flyingSlash(e, t, { color: C.white, dmg: 0, range: 30, roll: 0, size: 1.5 });
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "jujisho", label: "Getsuga Jujisho", cd: 220, cost: 130, min: 0, max: 28, weight: 4, cond: G(2, 3, 6),
      run(e, s, t) {
        busy(s, 16); setPose(e, 1); announce(e, "§4§lGetsuga Jujisho!");
        const col = ICH_GETSUGA[formOf(e)];
        for (const roll of [45, -45]) flyingSlash(e, t, { color: col, dmg: 28 * powerOf(e) / 100, range: 28, roll, carve: true, size: 1.8 });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "kuroi", label: "Kuroi Getsuga", cd: 300, cost: 180, min: 0, max: 34, weight: 5, cond: G(2, 3),
      run(e, s, t) {
        busy(s, 22); setPose(e, 22); announce(e, "§0§lKuroi... §4§lGetsuga! §7— the black moon fang");
        every(2, 5, () => { if (e.isValid) fx(e.dimension, "aura", e.location, C.black, 1.6, 0.6, { count: 14, speed: 2.5 }); });
        later(10, () => {
          if (!e.isValid) return;
          setPose(e, 19);
          flyingSlash(e, t, { color: C.black, dmg: 48 * powerOf(e) / 100, range: 34, roll: 10, carve: true, size: 3.0 });
          flyingSlash(e, t, { color: C.haki, dmg: 0, range: 34, roll: 10, size: 3.4 });
          shake(e.dimension, e.location, 0.3, 0.3);
          later(10, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "shunpo", label: "Flash Step", cd: 160, cost: 90, min: 0, max: 20, weight: 4, cond: G(2, 3, 6),
      run(e, s, t) {
        busy(s, 20); announce(e, "§f§lFlash Step!");
        every(4, 4, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.4); setPose(e, i % 2 ? 28 : 19);
          slashMarks(e, t, formOf(e) === 6 ? C.bigBang : C.haki, 2, 6 * powerOf(e) / 100);
          if (i === 3) setPose(e, 0);
        });
      } },
    { id: "cero", label: "Cero", cd: 260, cost: 180, min: 0, max: 40, weight: 5, cond: G(3),
      run(e, s, t) {
        busy(s, 26); face(e, aim(t)); announce(e, "§4§lCero!");
        chargeOrb(e, t, 12, C.red, 0.3, 1.2, 4);
        later(12, () => {
          if (!e.isValid) return;
          beam(e, alive(t) ? t : e, { color: C.red, width: 1.3, length: 40, dmg: 70 * powerOf(e) / 100, carve: 1, blast: 3.5, ticks: 6 });
          later(14, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "regen", label: "Instant Regeneration", cd: 600, cost: 120, min: 0, max: 60, weight: 8, cond: (e, s, c) => (formOf(e) === 3 || formOf(e) === 4) && c.hp < 0.5,
      run(e, s) {
        busy(s, 12); setPose(e, 22); announce(e, "§4§l(the Hollow's flesh knits back together)");
        const h = health(e);
        if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + h.effectiveMax * 0.12));
        fx(e.dimension, "aura", e.location, C.white, 1.2, 0.8, { count: 22, speed: 2 });
        burst(e.dimension, V.up(e.location, 1), C.red, 14, 2, 0.3, 0.4);
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "sonido", label: "Sonido Claws", cd: 140, cost: 80, min: 0, max: 22, weight: 5, cond: G(4),
      run(e, s, t) {
        busy(s, 22); announce(e, "§4§l(Sonido — he is simply there)");
        every(4, 5, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.2); setPose(e, i % 2 ? 34 : 9);
          slashMarks(e, t, C.haki, 1, 9 * powerOf(e) / 100);
          fx(t.dimension, "shock_v", aim(t), C.red, 2, 0.3);
          if (i === 4) setPose(e, 0);
        });
      } },
    { id: "hornCero", label: "Cero (Vasto Lorde)", cd: 320, cost: 220, min: 0, max: 44, weight: 6, cond: G(4),
      run(e, s, t) {
        busy(s, 30); face(e, aim(t)); announce(e, "§0§lCero... §4§lfrom between the horns");
        chargeOrb(e, t, 16, C.haki, 0.4, 1.8, 2);
        every(2, 8, () => { if (e.isValid) fx(e.dimension, "orb", V.up(e.location, 2.4), C.black, 1.4, 0.2); });
        later(16, () => {
          if (!e.isValid) return;
          beam(e, alive(t) ? t : e, { color: C.haki, width: 2.2, length: 46, dmg: 110 * powerOf(e) / 100, carve: 2, blast: 5, ticks: 7, pitch: 0.6 });
          later(16, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "mugetsu", label: "Mugetsu", cd: 900, cost: 700, min: 0, max: 40, weight: 7, cond: G(5),
      run(e, s, t) {
        busy(s, 40); setPose(e, 23); announce(e, "§0§lFinal Getsuga Tensho... §4§lMUGETSU");
        const dim = e.dimension;
        every(2, 10, () => { if (e.isValid) fx(dim, "aura", e.location, C.black, 2, 0.8, { count: 18, speed: 3 }); });
        later(20, () => {
          if (!e.isValid) return;
          setPose(e, 19);
          beam(e, alive(t) ? t : e, { color: C.black, width: 3.2, length: 48, dmg: 200 * powerOf(e) / 100, carve: 3, blast: 7, ticks: 10, pitch: 0.5 });
          later(20, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "barehand", label: "One Hand", cd: 150, cost: 60, min: 0, max: 18, weight: 5, cond: G(5),
      run(e, s, t) {  // Final Getsuga Ichigo stops the blade with a bare hand, then one blow ends it
        busy(s, 18); announce(e, "§0§l(he catches it bare-handed)");
        afterimage(e); teleportNear(e, t, false, 1.3); setPose(e, 13);
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 10); }
        later(8, () => {
          if (!e.isValid || !alive(t)) return;
          setPose(e, 5);
          deal(e, t, 50 * powerOf(e) / 100);
          fx(t.dimension, "shock", t.location, C.black, 6, 0.4); fx(t.dimension, "flash", aim(t), C.white, 3, 0.2);
          try { t.applyKnockback({ x: 0, z: 0 }, lowLift(0.8)); } catch (err) { /* ignore */ }
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "trueGetsuga", label: "Getsuga Tensho — True Bankai", cd: 260, cost: 200, min: 0, max: 40, weight: 6, cond: G(6),
      run(e, s, t) {
        busy(s, 24); setPose(e, 22); announce(e, "§b§lZangetsu... §f§lGETSUGA TENSHO! §7— both blades at once");
        every(2, 5, () => { if (e.isValid) fx(e.dimension, "aura", e.location, C.bigBang, 1.8, 0.6, { count: 14, speed: 3 }); });
        later(10, () => {
          if (!e.isValid) return;
          setPose(e, 1);
          flyingSlash(e, t, { color: C.bigBang, dmg: 70 * powerOf(e) / 100, range: 40, roll: 0, carve: true, size: 3.6 });
          flyingSlash(e, t, { color: C.white, dmg: 0, range: 40, roll: 0, size: 2.4 });
          flyingSlash(e, t, { color: C.black, dmg: 20 * powerOf(e) / 100, range: 34, roll: 90, size: 1.8 });  // the short blade's black fang
          shake(e.dimension, e.location, 0.4, 0.4);
          later(12, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
  ],
};

// ------------------------------------------------------------------ Tanjiro Kamado (Demon Slayer)
const TANJIRO = {
  name: "Tanjiro", color: "§2", energy: 700, regen: 14, energyName: "§bBREATH",
  dodge: () => 0.1,
  forms: [{ label: "Water Breathing", power: 40 }, { label: "Hinokami Kagura (Sun Breathing)", power: 50, aura: C.fire },
    { label: "Demon Slayer Mark — Crimson Blade", power: 62, aura: C.fire }],
  thresholds: [0.75, 0.45], transformCd: 100, formSound: [null, "mob.blaze.shoot", "mob.blaze.shoot"],
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
        try { t.applyKnockback({ x: 0, z: 0 }, lowLift(0.9)); } catch (err) { /* ignore */ }
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
    { id: "nezuko", label: "Nezuko: Exploding Blood", cd: 900, cost: 0, min: 0, max: 10, weight: 9, cond: (e, s, c) => c.hp < 0.4,
      run(e, s, t) {
        busy(s, 16); setPose(e, 1); announce(e, "§d§lNezuko! §5§lBlood Demon Art: Exploding Blood!");
        const dim = e.dimension, c = V.up(e.location, 1), pink = { red: 1, green: 0.35, blue: 0.6 };
        burst(dim, V.up(e.location, 1.6), pink, 30, 4, 0.5, 0.6);   // she bursts out of the box on his back
        fx(dim, "shock", e.location, pink, 9, 0.5);
        ring(dim, V.up(e.location, 0.3), 4, pink, 30, 0.5);
        hitArea(e, c, 4.5, 18 * powerOf(e) / 100, new Set(), { knock: 1.4, lift: 0.3 });
        every(8, 6, () => {  // the blood keeps burning on the enemies around him
          if (!e.isValid) return false;
          let list = []; try { list = dim.getEntities({ location: e.location, maxDistance: 5 }); } catch (err) { /* ignore */ }
          for (const o of list) if (canHit(e, teamOf(e), o)) { deal(e, o, 3 * powerOf(e) / 100); fx(dim, "aura", o.location, pink, 1, 0.5, { count: 6, speed: 1.5 }); }
        });
        later(14, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "calm", label: "Dead Calm", cd: 300, cost: 120, min: 0, max: 8, weight: 3, cond: G(0),
      run(e, s, t) {
        busy(s, 40); setPose(e, 19); announce(e, "§b§lEleventh Form: Dead Calm §7— every blow is turned aside");
        s.calmUntil = now() + 40;
        every(4, 10, () => { if (e.isValid) ring(e.dimension, V.up(e.location, 0.1), 1.6, C.kameBlue, 18, 0.35); });
        later(40, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "dance", label: "Hinokami Kagura: Dance", cd: 110, cost: 60, min: 0, max: 26, weight: 5, cond: G(1, 2),
      run(e, s, t) {
        busy(s, 14); setPose(e, 19); announce(e, "§6§lHinokami Kagura: Dance!");
        flyingSlash(e, t, { color: C.fire, dmg: 26 * powerOf(e) / 100, range: 20, roll: 30, size: 1.6 });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "bluesky", label: "Clear Blue Sky", cd: 180, cost: 90, min: 0, max: 8, weight: 4, cond: G(1, 2),
      run(e, s, t) {
        busy(s, 16); setPose(e, 24); announce(e, "§6§lHinokami Kagura: Clear Blue Sky!");
        const dim = e.dimension;
        ring(dim, V.up(e.location, 1), 3.5, C.fire, 32, 0.6); fx(dim, "shock", e.location, C.fire, 7, 0.4);
        hitArea(e, V.up(e.location, 1), 4, 24 * powerOf(e) / 100, new Set(), { knock: 1.6, lift: 0.4 });
        later(14, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "sunflower", label: "Sunflower Thrust", cd: 160, cost: 80, min: 0, max: 14, weight: 4, cond: G(1, 2),
      run(e, s, t) {
        busy(s, 12); announce(e, "§6§lHinokami Kagura: Sunflower Thrust!");
        afterimage(e); teleportNear(e, t, false, 1.4); setPose(e, 5);
        deal(e, t, 34 * powerOf(e) / 100);
        fx(e.dimension, "flash", aim(t), C.fire, 3, 0.25); burst(e.dimension, aim(t), C.fire, 24, 5, 0.45, 0.5);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "flowing", label: "Flowing Dance", cd: 140, cost: 60, min: 0, max: 10, weight: 4, cond: G(0),
      run(e, s, t) {
        busy(s, 18); announce(e, "§b§lWater Breathing, Third Form: Flowing Dance!");
        every(3, 4, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.5); setPose(e, i % 2 ? 28 : 19);
          const v = slashVfx(e.dimension, aim(t), V.norm(V.sub(aim(t), aim(e))), C.kameBlue, 1.3, i * 50); later(4, () => killVfx(v));
          deal(e, t, 7 * powerOf(e) / 100);
          if (i === 3) setPose(e, 0);
        });
      } },
    { id: "tide", label: "Striking Tide", cd: 170, cost: 80, min: 0, max: 10, weight: 4, cond: G(0),
      run(e, s, t) {
        busy(s, 18); announce(e, "§b§lFourth Form: Striking Tide!");
        afterimage(e); teleportNear(e, t, false, 1.5);
        slashMarks(e, t, C.kameBlue, 4, 6 * powerOf(e) / 100);
        every(2, 4, (i) => { if (alive(t)) fx(t.dimension, "shock_v", aim(t), C.kameBlue, 2 + i * 0.4, 0.3); });
        later(10, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "ripple", label: "Drop Ripple Thrust", cd: 120, cost: 50, min: 0, max: 8, weight: 3, cond: G(0),
      run(e, s, t) {
        busy(s, 10); announce(e, "§b§lSeventh Form: Drop Ripple Thrust!");
        afterimage(e); teleportNear(e, t, false, 1.4); setPose(e, 5);
        deal(e, t, 24 * powerOf(e) / 100);
        ring(e.dimension, aim(t), 1.4, C.kameBlue, 20, 0.4); fx(e.dimension, "flash", aim(t), C.white, 2, 0.15);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "basin", label: "Waterfall Basin", cd: 160, cost: 70, min: 0, max: 8, weight: 4, cond: G(0),
      run(e, s, t) {
        busy(s, 16); announce(e, "§b§lEighth Form: Waterfall Basin!");
        if (alive(t)) { try { e.teleport(V.up(t.location, 3), { facingLocation: aim(t) }); } catch (err) { /* ignore */ } }
        setPose(e, 10);
        later(4, () => {
          if (!e.isValid || !alive(t)) return;
          for (let y = 3; y > 0; y -= 0.5) fx(e.dimension, "orb", V.up(t.location, y), C.kameBlue, 1.4, 0.4);
          deal(e, t, 30 * powerOf(e) / 100);
          fx(e.dimension, "shock", t.location, C.kameBlue, 5, 0.4);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "headbutt", label: "Headbutt", cd: 220, cost: 30, min: 0, max: 4, weight: 3,
      run(e, s, t) {  // the hardest head in the Demon Slayer Corps
        busy(s, 12); announce(e, "§2§lTanjiro's HEADBUTT! §7— his skull is harder than a rock");
        afterimage(e); teleportNear(e, t, false, 1.0); setPose(e, 11);
        deal(e, t, 20 * powerOf(e) / 100);
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 14); }
        ring(t.dimension, V.up(t.location, 2.2), 0.6, C.kiYellow, 10, 0.5);
        fx(t.dimension, "flash", V.up(t.location, 1.6), C.white, 1.6, 0.15);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "firewheel", label: "Fire Wheel", cd: 150, cost: 70, min: 0, max: 10, weight: 4, cond: G(1, 2),
      run(e, s, t) {
        busy(s, 14); announce(e, "§6§lHinokami Kagura: Fire Wheel!");
        if (alive(t)) { try { e.teleport(V.up(t.location, 2.6), { facingLocation: aim(t) }); } catch (err) { /* ignore */ } }
        setPose(e, 24);
        for (let k = 0; k < 4; k++) { const v = slashVfx(e.dimension, V.up(e.location, 1), { x: 1, y: 0, z: 0 }, C.fire, 1.6, k * 45); later(5, () => killVfx(v)); }
        later(4, () => {
          if (!e.isValid || !alive(t)) return;
          deal(e, t, 30 * powerOf(e) / 100);
          fx(e.dimension, "shock", t.location, C.fire, 5, 0.4);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "halo", label: "Dragon Sun Halo Head Dance", cd: 260, cost: 140, min: 0, max: 20, weight: 5, cond: G(1, 2),
      run(e, s, t) {
        busy(s, 26); announce(e, "§6§lHinokami Kagura: Dragon Sun Halo Head Dance! §7— a dragon of fire");
        const dim = e.dimension;
        every(3, 7, (i) => {  // the fiery dragon coils round the target while he slashes
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.6); setPose(e, i % 2 ? 28 : 19);
          for (let k = 0; k < 12; k++) {
            const a = k * 0.5 + i;
            fx(dim, "orb", V.add(aim(t), { x: Math.cos(a) * 1.6, y: (k - 6) * 0.18, z: Math.sin(a) * 1.6 }), C.fire, 0.8, 0.5);
          }
          deal(e, t, 8 * powerOf(e) / 100);
          if (i === 6) setPose(e, 0);
        });
      } },
    { id: "bones", label: "Burning Bones Summer Sun", cd: 200, cost: 100, min: 0, max: 8, weight: 4, cond: G(2),
      run(e, s, t) {
        busy(s, 14); setPose(e, 24); announce(e, "§6§lBurning Bones, Summer Sun!");
        const dim = e.dimension;
        ring(dim, V.up(e.location, 1), 3.2, C.fire, 30, 0.5); ring(dim, V.up(e.location, 1.4), 2.4, C.flash, 24, 0.4);
        hitArea(e, V.up(e.location, 1), 3.8, 30 * powerOf(e) / 100, new Set(), { knock: 1.4, lift: 0.3 });
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "setting", label: "Setting Sun Transformation", cd: 220, cost: 110, min: 0, max: 10, weight: 4, cond: G(2),
      run(e, s, t) {
        busy(s, 14); announce(e, "§6§lSetting Sun Transformation!");
        afterimage(e); teleportNear(e, t, true, 1.4); setPose(e, 28);
        const v = slashVfx(e.dimension, aim(t), { x: 0, y: -1, z: 0 }, C.fire, 2, 90); later(5, () => killVfx(v));
        deal(e, t, 36 * powerOf(e) / 100);
        burst(e.dimension, aim(t), C.fire, 22, 4, 0.45, 0.5);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "thirteenth", label: "Hinokami Kagura: Thirteenth Form", cd: 900, cost: 400, min: 0, max: 14, weight: 7, cond: G(2),
      run(e, s, t) {  // all twelve forms linked in one endless circle — the form that was made to kill Muzan
        busy(s, 44); announce(e, "§c§lSun Breathing, Thirteenth Form! §7— all twelve dances linked without end");
        const dim = e.dimension;
        every(3, 12, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.5); setPose(e, [19, 28, 24, 5, 19, 28, 10, 24, 19, 28, 5, 1][i]);
          const v = slashVfx(dim, aim(t), V.norm({ x: Math.cos(i), y: Math.sin(i * 0.7), z: Math.sin(i) }), i % 3 ? C.fire : C.flash, 1.6, i * 30);
          later(4, () => killVfx(v));
          deal(e, t, 8 * powerOf(e) / 100);
          if (i === 11) { explosion(e, aim(t), { radius: 3.5, dmg: 30 * powerOf(e) / 100, color: C.fire, knock: 2 }); setPose(e, 0); }
        });
      } },
  ],
};

// ------------------------------------------------------------------ Demon Slayer: the demons
// A lash of flesh: a curved line of particles from the hand to the target, then the cut.
function whipLash(e, t, color, dmg, o = {}) {
  if (!alive(t)) return;
  const dim = e.dimension;
  const { pos } = handPos(e, t);
  const end = aim(t);
  const side = sideOf(V.norm(V.sub(end, pos)));
  const bend = (o.bend ?? 1.6) * (Math.random() < 0.5 ? -1 : 1);
  for (let k = 0; k <= 16; k++) {
    const u = k / 16, arc = Math.sin(u * Math.PI) * bend;
    fx(dim, "orb", V.add(V.add(pos, V.mul(V.sub(end, pos), u)), V.add(V.mul(side, arc), { x: 0, y: arc * 0.4, z: 0 })), color, 0.5, 0.3);
  }
  const v = slashVfx(dim, end, V.norm(V.sub(end, pos)), color, 1.2, Math.random() * 360);
  later(4, () => killVfx(v));
  deal(e, t, dmg);
  burst(dim, end, color, 10, 3, 0.35, 0.4);
}
const regenAbility = (label, say, pct, cond, cd = 600) => ({ id: "regen", label, cd, cost: 100, min: 0, max: 60, weight: 8, cond: (e, s, c) => (!cond || cond(e)) && c.hp < 0.5,
  run(e, s) {
    busy(s, 10); setPose(e, 22); announce(e, say);
    const h = health(e);
    if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + h.effectiveMax * pct));
    fx(e.dimension, "aura", e.location, C.blood, 1.2, 0.8, { count: 24, speed: 2 });
    burst(e.dimension, V.up(e.location, 1), C.blood, 16, 2, 0.35, 0.5);
    later(10, () => { if (e.isValid) setPose(e, 0); });
  } });

const TANJIRO_DEMON = {
  name: "Tanjiro", color: "§4", energy: 900, regen: 18, energyName: "§4BLOOD",
  dodge: () => 0.12,
  forms: [{ label: "Demon (feral)", power: 66, aura: C.blood }, { label: "Demon King — the sun conquered", power: 80, aura: C.fire }],
  thresholds: [0.55], transformCd: 100, formSound: [null, "mob.enderdragon.growl"],
  abilities: [
    { id: "claws", label: "Feral Claws", cd: 100, cost: 40, min: 0, max: 10, weight: 5,
      run(e, s, t) {
        busy(s, 16); announce(e, "§4§l(a feral snarl — he lunges)");
        every(3, 4, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.2); setPose(e, 34);
          slashMarks(e, t, C.blood, 1, 7 * powerOf(e) / 100);
          if (i === 3) later(4, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "roar", label: "Demon Roar", cd: 220, cost: 90, min: 0, max: 8, weight: 4,
      run(e, s, t) {
        busy(s, 14); setPose(e, 22); setExpr(e, 1, 20); announce(e, "§4§lGRRAAAAAH!");
        const dim = e.dimension;
        fx(dim, "shock", e.location, C.blood, 8, 0.5); ring(dim, V.up(e.location, 0.3), 4, C.blood, 28, 0.5);
        sound(dim, "mob.ravager.roar", e.location, 1.6, 1.2);
        hitArea(e, V.up(e.location, 1), 4.6, 16 * powerOf(e) / 100, new Set(), { knock: 2.6, lift: 0.5 });
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "bite", label: "Demon Bite", cd: 160, cost: 60, min: 0, max: 6, weight: 4,
      run(e, s, t) {
        busy(s, 12); announce(e, "§4§l(he bites down — the blood heals him)");
        afterimage(e); teleportNear(e, t, false, 1.0); setPose(e, 11); setExpr(e, 1, 12);
        deal(e, t, 24 * powerOf(e) / 100);
        const h = health(e); if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + 30));
        burst(e.dimension, aim(t), C.blood, 18, 3, 0.4, 0.5);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "headbutt", label: "Demon Headbutt", cd: 220, cost: 30, min: 0, max: 4, weight: 3,
      run(e, s, t) {
        busy(s, 12); announce(e, "§4§lDEMON HEADBUTT! §7— even harder than before");
        afterimage(e); teleportNear(e, t, false, 1.0); setPose(e, 11);
        deal(e, t, 26 * powerOf(e) / 100);
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 16); }
        ring(t.dimension, V.up(t.location, 2.2), 0.6, C.kiYellow, 10, 0.5);
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "tendrils", label: "Flesh Tendrils", cd: 180, cost: 100, min: 0, max: 14, weight: 5, cond: G(1),
      run(e, s, t) {
        busy(s, 18); setPose(e, 27); announce(e, "§4§lThe Demon King's blood! §7— tendrils burst from his back");
        every(3, 5, () => { if (e.isValid && alive(t)) whipLash(e, t, C.blood, 8 * powerOf(e) / 100, { bend: 2.4 }); });
        later(16, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "sunrush", label: "Sun-Proof Rampage", cd: 260, cost: 140, min: 0, max: 18, weight: 5, cond: G(1),
      run(e, s, t) {
        busy(s, 24); announce(e, "§6§lHe walks in the sunlight! §4§l— nothing can stop him now");
        every(4, 5, (i) => {
          if (!alive(t) || !e.isValid) return false;
          afterimage(e); teleportNear(e, t, i % 2 === 0, 1.2); setPose(e, [34, 5, 7, 34, 10][i]);
          deal(e, t, 9 * powerOf(e) / 100);
          fx(t.dimension, "shock_v", aim(t), C.fire, 2.6, 0.3);
          if (i === 4) later(6, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    regenAbility("Nigh-Absolute Regeneration", "§4§l(his wounds close almost instantly — he regrows what was cut)", 0.11, null, 600),
  ],
};

const MUZAN = {
  name: "Muzan", color: "§4", energy: 1300, regen: 24, energyName: "§4BLOOD",
  dodge: (e) => (formOf(e) ? 0.16 : 0.13),
  forms: [{ label: "Muzan Kibutsuji", power: 72, aura: C.blood }, { label: "Final Form — the Progenitor", power: 90, aura: C.blood }],
  thresholds: [0.65], transformCd: 100, formSound: [null, "mob.wither.spawn"],
  abilities: [
    { id: "whips", label: "Arm Whips", cd: 110, cost: 50, min: 0, max: 14, weight: 5,
      run(e, s, t) {
        busy(s, 18); setPose(e, 17); announce(e, "§d§l(his arms become flesh whips sharp as swords)");
        every(3, 4, (i) => { if (e.isValid && alive(t)) { setPose(e, i % 2 ? 17 : 28); whipLash(e, t, { red: 0.95, green: 0.5, blue: 0.6 }, 9 * powerOf(e) / 100); } });
        later(16, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "brambles", label: "Black Blood: Brambles", cd: 200, cost: 110, min: 0, max: 18, weight: 5,
      run(e, s, t) {
        busy(s, 18); face(e, aim(t)); setPose(e, 4); announce(e, "§4§lBlack Blood, Brambles! §7— Kokketsu Kikyoku");
        if (!alive(t)) return;
        const c = t.location, dim = e.dimension;
        every(2, 6, (i) => {  // thorny black-red tendrils erupt round the target and entangle it
          for (let k = 0; k < 6; k++) {
            const a = k + i * 0.9;
            for (let y = 0; y < 2.6; y += 0.4) fx(dim, "orb", V.add(c, { x: Math.cos(a) * (1.4 - y * 0.4), y, z: Math.sin(a) * (1.4 - y * 0.4) }), i % 2 ? C.black : C.blood, 0.45, 0.4);
          }
          if (alive(t)) deal(e, t, 5 * powerOf(e) / 100);
        });
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 18); }
        later(14, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "predator", label: "Indiscriminate Predator", cd: 240, cost: 120, min: 0, max: 8, weight: 4,
      run(e, s, t) {  // the arm swells into a huge mouth full of eyes and devours
        busy(s, 16); announce(e, "§4§l(his arm becomes a monstrous maw — it devours)");
        afterimage(e); teleportNear(e, t, false, 1.5); setPose(e, 16);
        later(4, () => {
          if (!e.isValid || !alive(t)) return;
          deal(e, t, 30 * powerOf(e) / 100);
          const h = health(e); if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + 25));
          sphereFx(e.dimension, aim(t), 1.4, C.blood, 20, 0.6, "orb", 0.4);
          sound(e.dimension, "mob.ravager.bite", t.location, 1.4, 0.7);
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    { id: "blood", label: "Demon King's Blood", cd: 320, cost: 140, min: 0, max: 10, weight: 4,
      run(e, s, t) {  // his blood floods the body and destroys the cells from inside
        busy(s, 12); announce(e, "§4§lMy blood will destroy your cells.");
        afterimage(e); teleportNear(e, t, false, 1.3); setPose(e, 5);
        deal(e, t, 12 * powerOf(e) / 100);
        every(10, 8, () => {
          if (!alive(t)) return false;
          deal(e, t, 4 * powerOf(e) / 100);
          fx(t.dimension, "aura", t.location, C.blood, 1, 0.6, { count: 8, speed: 1 });
        });
        if (t.typeId === "ab:tanjiro_demon" && isFighter(t)) {  // a demon of his blood: he seizes its cells
          const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 30);
          announce(e, "§4§lYou are a demon of MY blood. §7— your cells obey me");
        }
        later(8, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "backwhips", label: "Nine Back Whips", cd: 180, cost: 120, min: 0, max: 16, weight: 6, cond: G(1),
      run(e, s, t) {
        busy(s, 22); setPose(e, 27); announce(e, "§4§l(nine bladed whips tear out of his back)");
        every(2, 9, () => { if (e.isValid && alive(t)) whipLash(e, t, C.blood, 6 * powerOf(e) / 100, { bend: 3 }); });
        later(20, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "suction", label: "Mouths: Suction", cd: 220, cost: 120, min: 0, max: 16, weight: 4, cond: G(1),
      run(e, s, t) {  // the mouths on his whips suck the target in to be sliced apart
        busy(s, 20); setPose(e, 27); announce(e, "§4§l(the mouths on his whips inhale — everything is dragged in)");
        const dim = e.dimension;
        every(2, 6, () => {
          if (!alive(t) || !e.isValid) return false;
          const d = V.norm(V.sub(e.location, t.location));
          try { t.applyKnockback({ x: d.x * 1.2, z: d.z * 1.2 }, lowLift(0.1)); } catch (err) { /* ignore */ }
          implode(dim, V.up(e.location, 1), C.blood, 4, 10);
        });
        later(12, () => { if (e.isValid && alive(t)) { slashMarks(e, t, C.blood, 4, 7 * powerOf(e) / 100); } });
        later(18, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "maw", label: "Chest Maw Shockwave", cd: 260, cost: 160, min: 0, max: 10, weight: 5, cond: G(1),
      run(e, s, t) {  // his torso splits into a giant mouth and blasts out a shockwave
        busy(s, 16); setPose(e, 27); setExpr(e, 1, 14); announce(e, "§4§l(his torso opens into a giant maw)");
        const dim = e.dimension;
        later(6, () => {
          if (!e.isValid) return;
          fx(dim, "shock", e.location, C.blood, 10, 0.5); fx(dim, "shock_v", V.up(e.location, 1.2), C.blood, 5, 0.4);
          sound(dim, "mob.ravager.roar", e.location, 2, 0.6);
          hitArea(e, V.up(e.location, 1), 6, 28 * powerOf(e) / 100, new Set(), { knock: 3, lift: 0.6 });
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
    regenAbility("Regeneration (five brains, seven hearts)", "§4§l(his flesh knits back — five brains, seven hearts)", 0.06, null, 800),
    { id: "infant", label: "Giant Infant Form", cd: 2000, cost: 0, min: 0, max: 20, weight: 10, cond: (e, s, c) => formOf(e) === 1 && c.hp < 0.3,
      run(e, s, t) {  // at the very end, to hide from the dawn, he swells into a gigantic infant of flesh
        busy(s, 40); setPose(e, 22); announce(e, "§4§lMuzan swells into a GIANT INFANT of flesh! §7— he will not die");
        const dim = e.dimension;
        const v = summonGiant(e, 5, t, { size: 3.2, behind: 3, life: 60, pose: 3, poseAt: 12 });
        later(36, () => { vset(v, "ab:pose", 4); if (alive(t)) { deal(e, t, 30 * powerOf(e) / 100); sound(dim, "mob.ravager.bite", t.location, 2, 0.4); } });
        later(22, () => {  // it crashes down on everything in front of it
          if (!e.isValid) return;
          const c = alive(t) ? t.location : e.location;
          fx(dim, "shock", c, C.blood, 12, 0.6); shake(dim, c, 0.7, 0.6);
          hitArea(e, V.up(c, 1), 7, 60 * powerOf(e) / 100, new Set(), { knock: 3, lift: 0.8 });
          const h = health(e); if (h) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + h.effectiveMax * 0.05));
          later(10, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
  ],
};

// ------------------------------------------------------------------ Broly (Dragon Ball Super)
const BG = C.zoro;  // Broly's green ki
const BROLY = {
  name: "Broly", color: "§a", energy: 2200, regen: 40, energyName: "§aKI",
  dodge: (e) => (formOf(e) >= 2 ? 0.1 : 0.06),
  ego: 3, egoMax: 0.24,  // the angrier he gets, the stronger: every blow he takes feeds his rage (+24% at most)
  forms: [{ label: "Base", power: 160 }, { label: "Wrathful", power: 300, aura: C.red },
    { label: "Super Saiyan", power: 470, aura: C.gold }, { label: "Legendary Super Saiyan — Full Power", power: 640, aura: BG }],
  thresholds: [0.85, 0.65, 0.45], transformCd: 120, formSound: [null, "mob.enderdragon.growl", "mob.enderdragon.growl", "mob.wither.spawn"],
  abilities: [
    SIG.wave("roar", "Gigantic Roar", { say: "§a§lRAAAAAAAGH! §7— the roar alone flattens the ground", color: BG, radius: 7, dmg: 18, cd: 220 }),
    SIG.ball("eraser", "Eraser Cannon", { say: "§a§lEraser Cannon!", color: BG, size: 1.8, dmg: 44, radius: 3.6, charge: 10, cd: 200 }),
    SIG.ball("blastermeteor", "Blaster Meteor", { cond: (e) => formOf(e) >= 1, say: "§a§lBlaster Meteor! §7— green ki rains everywhere", color: BG, count: 10, size: 1.0, dmg: 10, spread: 4, cd: 300, cost: 220 }),
    SIG.rush("giganticrush", "Gigantic Rush", { say: "§a§lGigantic Rush!", color: BG, dmg: 9, finisher: 38, hits: 6, poses: [5, 6, 5, 6, 9, 16], cd: 180 }),
    SIG.rush("hammer", "Gigantic Hammer", { say: "§a§lGigantic Hammer! §7— both fists brought down", color: BG, dmg: 10, finisher: 46, hits: 2, poses: [3, 10], slam: true, cd: 220 }),
    SIG.rush("press", "Gigantic Press", { cond: (e) => formOf(e) >= 1, say: "§a§l(he grabs them by the head and drives them into the ground)", color: BG, dmg: 8, finisher: 50, hits: 3, poses: [13, 13, 10], slam: true, cd: 260 }),
    SIG.rush("wrath", "Wrathful Rampage", { cond: G(1), say: "§4§lRAAAGH! §7— blind rage, blow after blow", color: C.red, dmg: 11, finisher: 40, hits: 7, poses: [5, 6, 7, 6, 5, 8, 16], cd: 260 }),
    SIG.beam("eraserblow", "Eraser Blow", { cond: (e) => formOf(e) >= 2, say: "§a§lERASER BLOW!", color: BG, aura: BG, width: 2.6, dmg: 130, charge: 14, pose: 1, cd: 480, cost: 400 }),
    SIG.drop("omega", "Omega Blaster", { cond: G(3), say: "§a§lOMEGA BLASTER! §7— a green sun hurled down", color: BG, size: 3.6, radius: 8, dmg: 170, grow: 0.14, cd: 800, cost: 600 }),
    { id: "impact", label: "Gigantic Impact", cd: 360, cost: 260, min: 0, max: 18, weight: 6, cond: (e) => formOf(e) >= 2,
      run(e, s, t) {  // a charging fist that detonates on contact
        busy(s, 20); setPose(e, 22); announce(e, "§a§lGIGANTIC IMPACT!");
        chargeOrb(e, t, 10, BG, 0.5, 1.6, 22);
        later(10, () => {
          if (!e.isValid || !alive(t)) return;
          afterimage(e); teleportNear(e, t, false, 1.3); setPose(e, 16);
          deal(e, t, 60 * powerOf(e) / 100); launch(e, t, 1.2);
          explosion(e, aim(t), { radius: 4.5, dmg: 24 * powerOf(e) / 100, color: BG, knock: 1, carve: 2 });
          later(8, () => { if (e.isValid) setPose(e, 0); });
        });
      } },
  ],
};

// ------------------------------------------------------------------ Madara Uchiha (Naruto)
const MADARA = {
  name: "Madara", color: "§c", energy: 2000, regen: 34, energyName: "§6CHAKRA",
  dodge: (e) => (formOf(e) === 2 ? 0.2 : 0.16),
  forms: [{ label: "Reanimated — Rinnegan", power: 160, aura: C.purple }, { label: "Perfect Susanoo", power: 195, aura: C.blue },
    { label: "Ten-Tails Jinchuriki — Six Paths", power: 260, aura: C.white }],
  thresholds: [0.65, 0.4], transformCd: 140, formSound: [null, "mob.wither.spawn", "beacon.activate"],
  abilities: [
    SIG.ball("annihilation", "Great Fire Annihilation", { say: "§6§lFire Style: Great Fire Annihilation! §7— a sea of flame", color: C.fire, count: 9, size: 1.8, dmg: 14, spread: 6, radius: 3, cd: 260, cost: 200, pose: 21 }),
    SIG.beam("destroyer", "Majestic Destroyer Flame", { say: "§6§lFire Style: Majestic Destroyer Flame!", color: C.fire, width: 2.6, dmg: 90, charge: 10, pose: 21, cd: 340, cost: 240 }),
    { id: "deepforest", label: "Wood Release: Deep Forest Emergence", cd: 280, cost: 200, min: 0, max: 30, weight: 5,
      run(e, s, t) {  // trees and thorned roots erupt round the target and pin it
        busy(s, 18); setPose(e, 35); announce(e, "§2§lWood Release: Deep Forest Emergence!");
        if (!alive(t)) return;
        const c = t.location, dim = e.dimension, wood = { red: 0.45, green: 0.32, blue: 0.18 };
        every(2, 8, (i) => {
          for (let k = 0; k < 6; k++) {
            const a = k + i * 0.7;
            for (let y = 0; y < 3.5; y += 0.5) fx(dim, "orb", V.add(c, { x: Math.cos(a) * (2 - y * 0.4), y, z: Math.sin(a) * (2 - y * 0.4) }), i % 2 ? wood : C.zoro, 0.6, 0.6);
          }
          if (alive(t)) deal(e, t, 5 * powerOf(e) / 100);
        });
        if (isFighter(t)) { const ts2 = state(t); ts2.stunUntil = Math.max(ts2.stunUntil, now() + 20); }
        later(16, () => { if (e.isValid) setPose(e, 0); });
      } },
    SIG.ball("wooddragon", "Wood Release: Wood Dragon", { say: "§2§lWood Dragon! §7— it drains chakra as it bites", color: { red: 0.45, green: 0.32, blue: 0.18 }, size: 2.0, dmg: 48, homing: true, cd: 260 }),
    { id: "meteor", label: "Tengai Shinsei", cd: 1000, cost: 700, min: 0, max: 50, weight: 7,
      run(e, s, t) {  // two meteors — the second hidden behind the first
        busy(s, 30); setPose(e, 23); announce(e, "§c§lTengai Shinsei! §7— a meteorite falls from the sky... and a second behind it");
        if (!alive(t)) return;
        const rock = { red: 0.5, green: 0.38, blue: 0.3 };
        for (const delay of [10, 34]) later(delay, () => {
          if (!e.isValid || !alive(t)) return;
          const c = t.location, start = V.add(c, { x: 8, y: 34, z: 4 });
          projectile(e, start, V.norm(V.sub(V.up(c, 0.5), start)), { speed: 1.4, maxDist: 60, radius: 3, size: 4.5, color: rock, slot: 12, solid: true, trail: true,
            explode: { radius: 8, dmg: 110 * powerOf(e) / 100, color: C.fire, carve: 4, knock: 2 } });
          shake(e.dimension, c, 0.7, 1.0);
        });
        later(36, () => { if (e.isValid) setPose(e, 0); });
      } },
    SIG.wave("shinra", "Shinra Tensei", { say: "§5§lShinra Tensei! §7— everything is repelled", color: C.purple, radius: 7, dmg: 22, knock: 3.4, cd: 260 }),
    { id: "uchihareturn", label: "Uchiha Return", cd: 320, cost: 120, min: 0, max: 10, weight: 4, cond: G(0, 1),
      run(e, s, t) {  // the gunbai catches the blow and sends it straight back
        busy(s, 30); setPose(e, 19); announce(e, "§c§lUchiha Return! §7— the war fan turns every blow back");
        s.calmUntil = now() + 40;
        every(4, 9, () => { if (e.isValid) ring(e.dimension, V.up(e.location, 1), 1.8, C.fire, 18, 0.35); });
        later(30, () => { if (e.isValid) setPose(e, 0); });
      } },
    { id: "pssword", label: "Susanoo Sword", cd: 240, cost: 180, min: 0, max: 32, weight: 6, cond: G(1),
      run(e, s, t) {
        busy(s, 20); setPose(e, 23); announce(e, "§9§lPerfect Susanoo — the blade that splits mountains");
        later(4, () => susanooPose(e, 1, 18));
        later(10, () => { if (alive(t)) { flyingSlash(e, t, { color: C.blue, dmg: 64 * powerOf(e) / 100, range: 34, roll: 85, carve: true, size: 3.8 }); shake(e.dimension, t.location, 0.5, 0.4); } if (e.isValid) setPose(e, 0); });
      } },
    { id: "limbo", label: "Limbo: Border Jail", cd: 260, cost: 200, min: 0, max: 24, weight: 6, cond: G(2),
      run(e, s, t) {  // invisible shadows in another dimension beat the target from every side
        busy(s, 14); setPose(e, 35); announce(e, "§8§lLimbo: Border Jail §7— shadows no one can see");
        every(3, 6, () => { if (alive(t)) slashMarks(e, t, C.void, 1, 9 * powerOf(e) / 100); });
        later(12, () => { if (e.isValid) setPose(e, 0); });
      } },
    SIG.ball("gudo", "Truth-Seeking Balls", { cond: G(2), say: "§0§lTruth-Seeking Balls! §7— they erase ninjutsu itself", color: C.black, count: 6, size: 1.0, dmg: 20, homing: true, cd: 260 }),
    { id: "chibaku", label: "Six Paths: Chibaku Tensei", cd: 500, cost: 360, min: 0, max: 30, weight: 6, cond: G(2),
      run(e, s, t) {  // a black core drags everything in and crushes it under rock
        busy(s, 30); setPose(e, 23); announce(e, "§8§lSix Paths: Chibaku Tensei!");
        const dim = e.dimension;
        const c = alive(t) ? V.up(t.location, 3) : V.add(e.location, V.mul(e.getViewDirection(), 8));
        const ball = spawnVfx(dim, 1, c, { slot: 13, size: 0.8, life: 50 });
        every(2, 14, () => {
          let list = []; try { list = dim.getEntities({ location: c, maxDistance: 14 }); } catch (err) { /* ignore */ }
          for (const x of list) if (canHit(e, teamOf(e), x)) { const d = V.norm(V.sub(c, x.location)); try { x.applyKnockback({ x: d.x * 1.1, z: d.z * 1.1 }, lowLift(0.1)); } catch (err) { /* ignore */ } }
          implode(dim, c, { red: 0.5, green: 0.42, blue: 0.34 }, 8, 18);
        });
        later(28, () => { killVfx(ball); explosion(e, c, { radius: 6, dmg: 90 * powerOf(e) / 100, color: C.void, knock: 1, carve: 3 }); if (e.isValid) setPose(e, 0); });
      } },
    { id: "tsukuyomi", label: "Infinite Tsukuyomi", cd: 2000, cost: 900, min: 0, max: 60, weight: 9, cond: G(2),
      run(e, s, t) {  // the moon turns red: everyone caught in the dream
        busy(s, 30); setPose(e, 23); announce(e, "§4§lINFINITE TSUKUYOMI! §7— the moon blazes red; the world sleeps");
        const dim = e.dimension;
        fx(dim, "flash", V.up(e.location, 12), C.red, 30, 1.2);
        ring(dim, V.up(e.location, 0.5), 16, C.red, 60, 0.8);
        let list = []; try { list = dim.getEntities({ location: e.location, maxDistance: 32 }); } catch (err) { /* ignore */ }
        for (const x of list) if (canHit(e, teamOf(e), x)) {
          deal(e, x, 30 * powerOf(e) / 100);
          if (isFighter(x) && powerOf(x) < powerOf(e) * 1.1) { const xs = state(x); xs.stunUntil = Math.max(xs.stunUntil, now() + 50); }
          fx(dim, "aura", x.location, C.red, 1.2, 1, { count: 12, speed: 1 });
        }
        later(26, () => { if (e.isValid) setPose(e, 0); });
      } },
    regenAbility("Rinnegan: Preta Path", "§5§l(the Rinnegan absorbs the chakra thrown at him)", 0.1, null, 600),
  ],
};

const KI_CHARGERS = new Set(["ab:goku", "ab:vegeta", "ab:frieza", "ab:broly"]);
// what each fighter shouts as the transformation lands (by target form)
const TRANSFORM_LINES = {
  "ab:ichigo": [null, "§f§lFullbring! §7— the badge burns white", "§f§lBAN... §4§lKAI! §f§lTensa Zangetsu!", "§4§l(the Hollow mask slams over his face)",
    "§4§l(a roar that shakes the sky) §f§lVasto Lorde!", "§0§lThis is the Final Getsuga Tensho... §4§lMUGETSU.", "§b§lBankai! §f§lZangetsu — §7both of you are my power."],
  "ab:naruto_kid": [null, "§4§l(the Nine-Tails' red chakra boils over)"],
  "ab:naruto_teen": [null, "§c§l(the Nine-Tails' chakra wraps him — three tails)", "§4§l(four tails of red chakra boil out of him)", "§6§lSage Mode! §7— nature energy, gathered", "§4§l(eight tails... the Nine-Tails' bones form round him)"],
  "ab:naruto_war": [null, "§6§lLet's go, Kurama!", "§6§lSage Mode and Kurama — together!", "§e§lSix Paths Sage Mode!"],
  "ab:naruto_adult": [null, "§6§lSage Mode. §7— the toads taught me well", "§6§lKurama, let's do this!", "§4§lBaryon Mode! §7— it's burning our lives away"],
  "ab:sasuke_kid": [null, "§5§l(the Cursed Seal spreads over his skin)", "§5§lCursed Seal... §0§lLevel Two!"],
  "ab:sasuke": [null, "§5§lCursed Seal Level Two! §7— the wings tear free", "§c§lMangekyo Sharingan... §5§lSusanoo!"],
  "ab:sasuke_war": [null, "§5§lPerfect Susanoo! §7— a giant with wings", "§5§l(the Rinnegan opens) §7— I'll be the one to change the world"],
  "ab:sasuke_adult": [null, "§5§lSusanoo. §7— Perfect form"],
  "ab:tanjiro": [null, "§6§lHinokami Kagura! §7— his father's dance of fire", "§c§lThe Demon Slayer Mark blazes! §7— the blade turns crimson"],
  "ab:tanjiro_demon": [null, "§6§l(the third mark burns on his head) §4§l— he has conquered the sun"],
  "ab:broly": [null, "§4§lRAAAAAGH! §7— the wrath of the Legendary Saiyan", "§e§lSuper Saiyan! §7— his hair blazes gold-green", "§a§lLEGENDARY SUPER SAIYAN! §7— full power"],
  "ab:madara": [null, "§9§lPerfect Susanoo. §7— now, dance with me", "§f§lSix Paths... §7— I am the Ten-Tails' jinchuriki"],
  "ab:muzan": [null, "§4§lI am the Progenitor of all demons. §7— his hair turns white, mouths open all over his body"],
  "ab:goku": [null, "§e§lHAAAAAAA! §6§lSuper Saiyan!", "§e§l...and this is to go even further beyond!", "§c§lThe power of a god... §4§lSuper Saiyan God!",
    "§b§lSuper Saiyan God Super Saiyan!", "§7§l(silence) §f§lUltra Instinct"],
  "ab:vegeta": [null, "§e§lI am the Prince of all Saiyans!", "§c§lA god's red ki... §4§lSuper Saiyan God!", "§b§lSuper Saiyan Blue!", "§5§lUltra Ego! §7— destruction is my pride"],
  "ab:frieza": [null, "§6§lThis is Golden Frieza!"],
  "ab:zoro": [null, "§0§lI am... §4§lthe King of Hell."],
};
const SWORDSMEN = new Set(["ab:zoro", "ab:ichigo", "ab:tanjiro", "ab:sasuke", "ab:sasuke_war", "ab:sasuke_adult"]);
const FIGHTERS = { "ab:goku": GOKU, "ab:vegeta": VEGETA, "ab:gojo": GOJO, "ab:yuji": YUJI, "ab:yuji_final": YUJI_FINAL, "ab:sukuna": SUKUNA, "ab:luffy": LUFFY, "ab:zoro": ZORO, "ab:frieza": FRIEZA,
  "ab:naruto_kid": NARUTO_KID, "ab:naruto_teen": NARUTO_TEEN, "ab:naruto_war": NARUTO_WAR, "ab:naruto_adult": NARUTO_ADULT,
  "ab:tanjiro_demon": TANJIRO_DEMON, "ab:muzan": MUZAN, "ab:broly": BROLY, "ab:madara": MADARA, "ab:sasuke_kid": SASUKE_KID, "ab:sasuke": SASUKE, "ab:sasuke_war": SASUKE_WAR, "ab:sasuke_adult": SASUKE_ADULT, "ab:ichigo": ICHIGO, "ab:tanjiro": TANJIRO };

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
  "ab:sasuke_kid": [["jab_r", "jab_l", "kick", "upper"], ["kick_r", "jab_r", "blink", "axe"], ["jab_l", "kick_l", "kick_r"]],
  "ab:sasuke_war": [["cut_r", "cut_l", "kick_r", "upper"], ["jab_r", "jab_l", "blink", "axe"], ["cut_l", "cut_r", "kick_l", "cut_x"]],
  "ab:sasuke_adult": [["cut_r", "cut_l", "kick_r", "upper"], ["jab_r", "jab_l", "blink", "axe"], ["cut_l", "cut_r", "kick_l", "cut_x"]],
  "ab:ichigo": [["cut_r", "cut_l", "cut_r", "cut_x"], ["cut_l", "blink", "cut_r", "kick_r", "cut_x"], ["cut_r", "cut_l", "axe", "cut_x"]],
  "ab:tanjiro": [["cut_r", "cut_l", "cut_r", "cut_x"], ["cut_l", "cut_r", "kick", "cut_x"], ["cut_r", "cut_l", "cut_l", "kick_r"]],
  "ab:tanjiro_demon": [["jab_r", "jab_l", "kick", "upper"], ["jab_l", "jab_r", "blink", "axe"], ["kick_r", "jab_r", "jab_l", "kick_l"]],
  "ab:muzan": [["jab_r", "jab_l", "kick_r", "upper"], ["blink", "jab_r", "kick_l", "axe"], ["jab_l", "jab_r", "kick", "kick_r"]],
  "ab:broly": [["jab_r", "jab_l", "rush", "kick_r", "kiburst"], ["jab_l", "jab_r", "upper", "axe"], ["rush", "kick_l", "kick_r", "kiburst"]],
  "ab:madara": [["jab_r", "jab_l", "kick_r", "upper"], ["blink", "jab_r", "kick_l", "axe"], ["jab_l", "kick", "kick_r"]],
  "ab:frieza": [["jab_r", "tail", "rush", "kiburst"], ["kick", "jab_l", "jab_r", "axe"], ["rush", "kick_r", "kiburst"]],
};
MOVES.spistol = { pose: 13, t: 5, dmg: 12, kb: 1.4, strong: true, arc: "punch" };
MOVES.sgatling = { pose: 14, t: 16, dmg: 3, hits: 8, kb: 0.1, arc: "punch" };
MOVES.swhip = { pose: 17, t: 6, dmg: 15, kb: 2, lift: 0.3, strong: true, arc: "right" };
const BLACK_FLASH = { "ab:gojo": 0.25, "ab:yuji": 0.2, "ab:yuji_final": 0.45, "ab:sukuna": 0.2 };
const HIT_COLOR = { "ab:goku": C.kiYellow, "ab:vegeta": C.bigBang, "ab:gojo": C.blue, "ab:yuji": C.ce, "ab:yuji_final": C.blood, "ab:sukuna": C.red, "ab:luffy": C.white, "ab:zoro": C.zoro, "ab:frieza": C.death,
  "ab:naruto_kid": C.white, "ab:naruto_teen": C.blue, "ab:naruto_war": C.gold, "ab:naruto_adult": C.gold,
  "ab:sasuke": C.kameBlue, "ab:sasuke_kid": C.kameBlue, "ab:sasuke_war": C.purple, "ab:sasuke_adult": C.purple, "ab:ichigo": C.kameBlue, "ab:tanjiro": C.kameBlue, "ab:tanjiro_demon": C.blood, "ab:muzan": C.blood, "ab:broly": BG, "ab:madara": C.fire };

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
  if ((lastWhoosh.get(e.id) ?? -99) + 8 > now()) return;  // a rush of blinks is one whoosh, not a buzz
  lastWhoosh.set(e.id, now());
  sound(e.dimension, "ab.whoosh", e.location, 0.9, 0.9 + Math.random() * 0.3);
}
const lastWhoosh = new Map();

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
      if (mv.sword && SWORDSMEN.has(t.typeId) && Math.random() < 0.2) {  // blade lock between two swordsmen
        const c = V.add(aim(e), V.mul(V.sub(aim(t), aim(e)), 0.5));
        fx(e.dimension, "flash", c, C.white, 2.6, 0.2);
        fx(e.dimension, "streak", c, C.kiYellow, 1.4, 0.35, { count: 16, speed: 9 });
        sound(e.dimension, "random.anvil_land", c, 0.6, 1.6);
        announce(e, "§f§lBlade lock!");
        const n2 = V.norm(V.sub(t.location, e.location));
        try { e.applyKnockback({ x: -n2.x * 0.8, z: -n2.z * 0.8 }, lowLift(0.15)); } catch (err) { /* ignore */ }
        try { t.applyKnockback({ x: n2.x * 0.8, z: n2.z * 0.8 }, lowLift(0.15)); } catch (err) { /* ignore */ }
      }
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
      try { t.applyKnockback({ x: n.x * kb, z: n.z * kb }, lowLift(Math.max(0, mv.lift ?? 0.08))); } catch (err) { /* ignore */ }
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
  if (SASUKES.has(e.typeId) || e.typeId === "ab:madara") updateSusanoo(e, s);
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
  // Transformations climb ONE step at a time, never straight to the last form: a fighter powers up when the
  // opponent's current form outclasses theirs (answered quickly), when badly hurt, or after a long even exchange.
  const outmatched = ctx.tPower > ctx.power * 1.02;
  const inForm = tick - (s.formSince ?? s.combatSince);
  const hold = outmatched ? 20 : 200;
  if (!s.cloneUntil && form < def.forms.length - 1 && def.thresholds[form] !== undefined && tick >= s.transformUntil &&
      tick - s.combatSince > (outmatched ? 20 : 40) && inForm >= hold && (outmatched || tick >= s.nextTransform) &&
      (outmatched || ctx.hp < def.thresholds[form] || (inForm > 400 && ctx.tPower > ctx.power * 0.8))) {
    let next = def.nextForm ? def.nextForm(form) : form + 1;
    if (outmatched) {  // answer the opponent's CURRENT form with the first form that matches it — not the last one
      const match = def.forms.findIndex((f, i) => i > form && f.power * (def.ego && i === def.ego ? 1.05 : 1) >= ctx.tPower * 1.05);
      next = match >= 0 ? match : def.forms.length - 1;
    }
    s.formSince = tick;
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
  // Up close they still fight with their powers: a combo only some of the time, techniques the rest.
  if (ctx.dist <= 6 && tick >= (s.cd.combo ?? 0) && Math.random() < (s.cloneUntil ? 0.7 : 0.32)) {
    s.cd.combo = tick + 50 + Math.floor(Math.random() * 40);
    const tst = isFighter(target) ? state(target) : undefined;
    if (tst && !s.cloneUntil && now() < tst.busyUntil && (tst.lastCombo ?? 0) > now() - 6 && Math.random() < 0.5) { fistClash(e, target); return; }
    s.lastCombo = now();
    combo(e, s, target);
    return;
  }
  if (s.cloneUntil || Math.random() > 0.8) return;  // shadow clones only brawl
  // Read the fight: when the opponent is winding up a big technique from range, slip aside first.
  const ts = isFighter(target) ? state(target) : undefined;
  if (ts && now() < ts.busyUntil && ctx.dist > 5 && Math.random() < 0.25 && tick >= (s.cd.sidestep ?? 0)) {
    s.cd.sidestep = tick + 80;
    afterimage(e);
    const side = V.mul(sideOf(V.norm(V.sub(e.location, target.location))), Math.random() < 0.5 ? 3 : -3);
    try { e.tryTeleport(V.add(e.location, side), { checkForBlocks: true, facingLocation: aim(target) }); } catch (err) { /* ignore */ }
    return;
  }
  const burnt = tick < s.burnoutUntil;
  // Abilities are free to use at any range; close-range ones dash in first.
  const ok = def.abilities.filter((a) => (s.cd[a.id] ?? 0) <= tick && s.energy >= a.cost &&
    !(burnt && a.technique) && (!a.cond || a.cond(e, s, ctx)));
  if (!ok.length) return;
  // favour techniques not used for a while, and the big ones when the opponent is strong or we are hurt
  const wt = (a) => a.weight * (1 + Math.min(2, (tick - (s.lastUsed?.[a.id] ?? 0)) / 400)) * (a.cost >= 300 && (ctx.hp < 0.6 || ctx.tPower >= ctx.power) ? 1.6 : 1);
  let r = Math.random() * ok.reduce((n, a) => n + wt(a), 0);
  const pick = ok.find((a) => (r -= wt(a)) <= 0) ?? ok[0];
  (s.lastUsed ??= {})[pick.id] = tick;
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
    if (s.ego > 0.01) extra += e.typeId === "ab:broly" ? ` §a[Rage +${Math.round(s.ego * 100)}%]` : ` §5[Ego +${Math.round(s.ego * 100)}%]`;
    if (e.hasTag("ab_infinity")) extra += " §b[Infinity]";
    if (s.burnoutUntil > now()) extra += " §7[Burnout]";
    if (s.stunUntil > now()) extra += " §f[Stunned]";
    void form; void extra;
    text = `${team === RED ? "§c" : team === BLUE ? "§9" : "§7"}▌${bar(pct)}`;
  } else if (team) {
    text = `${team === RED ? "§c" : "§9"}▌${bar(pct)}`;
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
      try { vs = [...dim.getEntities({ type: "ab:vfx" }), ...dim.getEntities({ type: "ab:summon" })]; } catch (e) { /* ignore */ }
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
      ev.damage *= clamp(Math.pow(attackerP / defenderP, 2.2), 0.08, 4);
      if (now() < (s.transformUntil ?? 0)) ev.damage *= 0.25;  // the transformation aura pushes blows back
    }
    ev.damage /= TOUGHNESS;  // fighters are tough: battles last, nobody folds in a few hits
    if ((v.typeId === "ab:sasuke" && formOf(v) === 2) || v.typeId === "ab:sasuke_war" || (v.typeId === "ab:sasuke_adult" && formOf(v) === 1)) {  // Susanoo takes part of every blow
      ev.damage *= 0.85;
      system.run(() => { if (v.isValid) fx(v.dimension, "flash", V.up(v.location, 1.2), C.purple, 2.2, 0.2); });
    }
    if (now() < (s.calmUntil ?? 0) && src && src.isValid) {  // Tanjiro's Dead Calm: parry and counter
      ev.damage *= 0.3;
      system.run(() => {
        if (!v.isValid || !alive(src)) return;
        face(v, aim(src));
        const cv = slashVfx(v.dimension, aim(src), V.norm(V.sub(aim(src), aim(v))), C.kameBlue, 1.2, Math.random() * 90);
        later(4, () => killVfx(cv));
        deal(v, src, 8 * powerOf(v) / 100);
      });
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
    // Guard (Dragon Ball: Re style): arms crossed, the blow mostly absorbed — unless the attacker is far stronger.
    if (now() >= s.busyUntil && attackerP > 0 && now() >= (s.guardCd ?? 0) && Math.random() < 0.18 + (hpPct(v) < 0.4 ? 0.1 : 0)) {
      s.guardCd = now() + 50;
      const broken = attackerP > defenderP * 1.3;
      ev.damage *= broken ? 0.8 : 0.35;
      system.run(() => guardFx(v, src, broken));
    }
    if (now() >= s.busyUntil || (v.typeId === "ab:goku" && formOf(v) === 5)) {
      const chance = def.dodge(v, s);
      if (chance > 0 && Math.random() < chance) {
        ev.cancel = true;
        system.run(() => dodgeFx(v, src));
        return;
      }
    }
    if (ev.damage > 1.5) system.run(() => setExpr(v, 2, ev.damage > 25 ? 14 : 8));
    // A heavy blow sends the target flying (about seven blocks) with a trail and a crash where it lands.
    if (attackerP > 0 && src && src.isValid && now() >= (s.launchedUntil ?? 0)) {
      const hp = health(v);
      if (hp && ev.damage >= hp.effectiveMax * 0.035) {
        s.launchedUntil = now() + 30;
        const strength = clamp(ev.damage / (hp.effectiveMax * 0.06), 0.8, 1.25);
        system.run(() => launch(src, v, strength));
      }
    }
    if (def.ego && formOf(v) === def.ego) s.ego = Math.min(def.egoMax ?? 0.1, s.ego + ev.damage / (def.egoMax ? 260 : 500));
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
const TOUGHNESS = 6.5;
// Launch: a heavy blow drives the target back about seven blocks ALONG THE GROUND (no flying): fast at first,
// then slowing, dust ploughed up behind, a dust shockwave where it stops (or where it hits a wall).
const DUST = { red: 0.6, green: 0.55, blue: 0.48 };
function lowLift(v) { return Math.min(v, 0.12); }
function launch(src, v, strength = 1) {
  if (!alive(v) || !src || !src.isValid) return;
  const d = V.norm({ x: v.location.x - src.location.x, y: 0, z: v.location.z - src.location.z });
  const total = 7 * clamp(strength, 0.85, 1.2), steps = 8, tri = (steps * (steps + 1)) / 2;
  const dim = v.dimension;
  impactFrame(src, v);
  fx(dim, "shock_v", aim(v), C.white, 2.4, 0.3);
  sound(dim, "random.explode", v.location, 0.5, 1.6);
  if (isFighter(v)) { const vs = state(v); vs.stunUntil = Math.max(vs.stunUntil, now() + 12); }
  if (isFighter(src) && Math.random() < 0.35) later(9, () => {  // vanish chase: reappear where they land and keep going
    if (!alive(v) || !alive(src) || now() < state(src).busyUntil) return;
    afterimage(src); teleportNear(src, v, Math.random() < 0.5, 1.4); face(src, aim(v)); setPose(src, [7, 10, 9][Math.floor(Math.random() * 3)]);
    deal(src, v, 10 * powerOf(src) / 100);
    fx(dim, "shock_v", aim(v), C.white, 2.2, 0.25);
    later(6, () => { if (src.isValid) setPose(src, 0); });
  });
  every(1, steps, (i) => {
    if (!alive(v)) return false;
    const next = V.add(v.location, V.mul(d, (total * (steps - i)) / tri));
    let ok = false;
    try { ok = v.tryTeleport(next, { checkForBlocks: true, keepVelocity: false }); } catch (e) { ok = false; }
    fx(dim, "aura", v.location, DUST, 0.9, 0.6, { count: 5 * fxLevel(), speed: 1 });
    fx(dim, "streak", aim(v), C.white, 0.7, 0.25, { count: 2, speed: 2 });
    if (i % 2 === 1) groundTear(dim, v.location, 1.0);
    if (!ok || i === steps - 1) {
      if (!ok) {  // slammed into a wall: the wall caves in around them
        const wall = V.up(V.add(v.location, V.mul(d, 1.2)), 1);
        rubble(dim, wall, 14, 6); carve(dim, wall, 1.6, 30);
        sound(dim, "ab.boom", wall, 1.2, 1.2); shake(dim, wall, 0.4, 0.4);
      }
      fx(dim, "shock", v.location, DUST, 4, 0.5);
      burst(dim, V.up(v.location, 0.3), DUST, 16, 3, 0.4, 0.5);
      groundTear(dim, v.location, strength >= 1.1 ? 2.2 : 1.6);
      if (!ok) sound(dim, "random.anvil_land", v.location, 0.4, 0.6);
      return false;
    }
  });
}
function guardFx(v, src, broken) {
  if (!v.isValid) return;
  const s = state(v);
  busy(s, 8); setPose(v, 31);
  const c = V.up(v.location, 1.2);
  if (broken) {  // guard break: the arms are knocked apart, a burst of shards, a long stagger
    burst(v.dimension, c, C.white, 26, 5, 0.4, 0.5); fx(v.dimension, "shock_v", c, C.white, 3, 0.3);
    sound(v.dimension, "random.break", v.location, 1, 0.6);
    s.stunUntil = Math.max(s.stunUntil, now() + 16);
  } else {
    fx(v.dimension, "streak", c, C.kiYellow, 1, 0.25, { count: 8, speed: 6 }); ring(v.dimension, c, 0.9, C.white, 12, 0.25);
    sound(v.dimension, "random.anvil_land", v.location, 0.5, 1.8);
  }
  later(8, () => { if (v.isValid) setPose(v, 0); });
}
// Impact frame: on a heavy hit both fighters freeze for an instant, a white flash, the screen shakes.
function impactFrame(src, v) {
  for (const x of [src, v]) { if (alive(x)) { slow(x, 4, 10); if (isFighter(x)) busy(state(x), Math.max(0, state(x).busyUntil - now()) + 3); } }
  if (!alive(v)) return;
  const c = aim(v);
  fx(v.dimension, "flash", c, C.white, 5, 0.12); sphereFx(v.dimension, c, 1.2, C.white, 14, 0.5, "orb", 0.2);
  sound(v.dimension, "ab.impact", c, 1.4, 0.9 + Math.random() * 0.2);
  shake(v.dimension, v.location, 0.35, 0.25);
}
// Fist clash: two fighters swinging at the same instant meet in the middle — a shockwave, both slide back.
function fistClash(a, b) {
  const c = V.add(aim(a), V.mul(V.sub(aim(b), aim(a)), 0.5));
  const dim = a.dimension;
  for (const x of [a, b]) { setPose(x, 5); busy(state(x), 12); }
  fx(dim, "flash", c, C.white, 4, 0.15); fx(dim, "shock_v", c, C.kiYellow, 4, 0.3); fx(dim, "shock", V.up(c, -1), C.white, 7, 0.4);
  burst(dim, c, C.white, 30, 6, 0.4, 0.5); shake(dim, c, 0.45, 0.35);
  sound(dim, "ab.impact", c, 1.6, 0.75);
  sound(dim, "random.explode", c, 0.8, 1.4);
  later(3, () => {
    for (const [x, y] of [[a, b], [b, a]]) {
      if (!alive(x) || !alive(y)) continue;
      const d = V.norm({ x: x.location.x - y.location.x, y: 0, z: x.location.z - y.location.z });
      try { x.tryTeleport(V.add(x.location, V.mul(d, 2.5)), { checkForBlocks: true, facingLocation: aim(y) }); } catch (err) { /* ignore */ }
      setPose(x, 0);
    }
  });
}
function dodgeFx(v, src) {
  if (!v.isValid) return;
  const ui = v.typeId === "ab:goku" && formOf(v) === 5;
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
  if (src && src.isValid && alive(src) && Math.random() < 0.45) {  // Perfect Counter: vanish behind the attacker and strike
    later(3, () => {
      if (!v.isValid || !alive(src)) return;
      afterimage(v); teleportNear(v, src, true, 1.3); face(v, aim(src)); setPose(v, Math.random() < 0.5 ? 5 : 8);
      deal(v, src, 14 * powerOf(v) / 100);
      fx(v.dimension, "flash", aim(src), C.white, 2, 0.15);
      later(6, () => { if (v.isValid) setPose(v, 0); });
    });
    return;
  }
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
    if (def && !e.hasTag("ab_clone")) {  // the finishing blow: the fallen fighter is slammed into a crater, their domain breaks
      const dim = e.dimension, at = e.location;
      breakDome(e.id, true); breakDome(`shrine${e.id}`, true);
      groundTear(dim, at, 2.6);
      fx(dim, "shock", at, DUST, 9, 0.7); fx(dim, "flash", V.up(at, 1), C.white, 6, 0.2);
      burst(dim, V.up(at, 0.5), DUST, 40, 6, 0.5, 0.8);
      sound(dim, "ab.boom", at, 2, 0.85); shake(dim, at, 0.6, 0.6);
    }
    if (def && teamOf(e)) later(10, () => checkWinner(e.dimension, teamOf(e)));
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
// Victory screen: when one side has no fighters left standing, the winners' names and forms fill the screen.
function checkWinner(dim, losingTeam) {
  try {
    const left = (tag) => dim.getEntities({ tags: [tag], families: [FIGHTER_FAMILY] }).filter((x) => alive(x) && !x.hasTag("ab_clone"));
    if (left(losingTeam).length) return;
    const winTeam = losingTeam === RED ? BLUE : RED;
    const winners = left(winTeam);
    if (!winners.length) return;
    const w = winners[0], wd = FIGHTERS[w.typeId];
    healArenaSoon(80);
    later(6, () => cinematic(w, 56, 6));
    screenFade(dim, w.location, 60, 0.05, 0.1, 0.6, [255, 255, 255]);
    const title = winTeam === RED ? "§c§lRED TEAM WINS!" : "§9§lBLUE TEAM WINS!";
    for (const p of world.getPlayers()) {
      try { p.onScreenDisplay.setTitle(title, { fadeInDuration: 5, stayDuration: 60, fadeOutDuration: 15 }); } catch (err) { /* ignore */ }
      sound(p.dimension, "random.levelup", p.location, 1, 1);
    }
    fx(dim, "flash", V.up(w.location, 2), wd.forms[clamp(formOf(w), 0, wd.forms.length - 1)].aura ?? C.gold, 6, 0.6);
    ring(dim, V.up(w.location, 0.2), 4, C.gold, 40, 0.6);
  } catch (err) { /* ignore */ }
}
// Instant battles from chat: /scriptevent ab:vs goku vegeta  — or /scriptevent ab:random
function startBattle(p, a, b) {
  const ida = "ab:" + a, idb = "ab:" + b;
  if (!FIGHTERS[ida] || !FIGHTERS[idb]) { p.sendMessage(`§c[Anime Battles] unknown fighter. Names: ${Object.keys(FIGHTERS).map((k) => k.slice(3)).join(", ")}`); return; }
  const d = V.norm({ x: p.getViewDirection().x, y: 0, z: p.getViewDirection().z });
  const mid = V.add(p.location, V.mul(d, 14));
  const side = sideOf(d);
  for (const [id, team, off] of [[ida, RED, -7], [idb, BLUE, 7]]) {
    try {
      const f = p.dimension.spawnEntity(id, V.add(mid, V.mul(side, off)));
      later(25, () => { if (f.isValid) setTeam(f, team); });
    } catch (err) { warn("vs", err); }
  }
  later(6, () => cinematicAt(p.dimension, mid, 40, 11, V.up(mid, 1.2)));  // face-off: the camera sweeps past both fighters

}

// Team war (Mob Battle Mod style): two lines of fighters face each other across the field. Fighters are drawn at
// random, then dealt out strongest-first in a snake draft (1-2-2-1...) so the two sides come out about even.
function startWar(p, n) {
  const ids = Object.keys(FIGHTERS);
  const pick = [];
  while (pick.length < n * 2 && pick.length < ids.length) {
    const id = ids[Math.floor(Math.random() * ids.length)];
    if (!pick.includes(id)) pick.push(id);
  }
  const peak = (id) => { const f = FIGHTERS[id].forms; return f[f.length - 1].power * (1 + (FIGHTERS[id].egoMax ?? 0)); };
  pick.sort((a, b) => peak(b) - peak(a));
  const red = [], blue = [];
  pick.forEach((id, i) => ((i % 4 === 0 || i % 4 === 3) ? red : blue).push(id));
  const d = V.norm({ x: p.getViewDirection().x, y: 0, z: p.getViewDirection().z });
  const mid = V.add(p.location, V.mul(d, 18));
  const side = sideOf(d);
  later(4, () => cinematicAt(p.dimension, mid, 50, 16, V.up(mid, 1.2)));
  for (const [list, team, off] of [[red, RED, -10], [blue, BLUE, 10]]) {
    list.forEach((id, k) => {
      later(k * 6, () => {
        try {
          const at = V.add(V.add(mid, V.mul(side, off)), V.mul(d, (k - (list.length - 1) / 2) * 4));
          const f = p.dimension.spawnEntity(id, at);
          later(30, () => { if (f.isValid) setTeam(f, team); });
        } catch (err) { warn("war", err); }
      });
    });
  }
}

const VICTORY = { "ab:goku": 34, "ab:vegeta": 31, "ab:frieza": 31, "ab:luffy": 27, "ab:gojo": 26, "ab:sukuna": 21, "ab:zoro": 0, "ab:yuji_final": 0, "ab:sasuke": 0, "ab:sasuke_kid": 0, "ab:sasuke_war": 0, "ab:sasuke_adult": 0, "ab:ichigo": 0 };
const ENTRANCE_LINES = {
  "ab:goku": "§6§lHey, it's me, Goku! §7Let's fight!", "ab:vegeta": "§9§lKakarot! §7The Prince of all Saiyans is here.",
  "ab:frieza": "§5§lOhohoho... §7you should be honoured.", "ab:gojo": "§b§lThroughout heaven and earth, I alone am the honoured one.",
  "ab:sukuna": "§c§lKnow your place, fool.", "ab:yuji": "§d§lI'll save as many people as I can!", "ab:yuji_final": "§c§l...",
  "ab:luffy": "§c§lI'm Luffy! §7The man who'll become King of the Pirates!", "ab:zoro": "§a§lNothing happened.",
  "ab:naruto_kid": "§6§lBelieve it! §7I'm gonna be Hokage!", "ab:naruto_teen": "§6§lI never go back on my word — that's my ninja way!",
  "ab:naruto_war": "§e§lKurama and I will end this war!", "ab:naruto_adult": "§6§lThe Seventh Hokage is here. §7Believe it.",
  "ab:sasuke_kid": "§9§lI'm an avenger. §7I have to kill a certain man.", "ab:sasuke": "§9§lI have only one goal.",
  "ab:sasuke_war": "§5§lI will become Hokage — and change the shinobi world.", "ab:sasuke_adult": "§5§lI'm the shadow that supports the Hokage.", "ab:ichigo": "§6§lI'm Ichigo Kurosaki, Substitute Soul Reaper.",
  "ab:tanjiro": "§2§lI'll turn Nezuko back into a human!", "ab:tanjiro_demon": "§4§l(a low growl — his eyes are slits)",
  "ab:muzan": "§4§lI am the closest thing to perfection. §7— Muzan Kibutsuji",
  "ab:broly": "§a§lKa... ka... KAKAROT! §7— no: Broly", "ab:madara": "§c§lWake up to reality! §7— Madara Uchiha",
};
// Entrance: a freshly spawned fighter strikes its signature pose with a shout before joining the fight.
const ENTRANCE = { "ab:goku": 22, "ab:vegeta": 22, "ab:frieza": 23, "ab:gojo": 26, "ab:yuji": 5, "ab:yuji_final": 19,
  "ab:sukuna": 21, "ab:luffy": 27, "ab:zoro": 1, "ab:naruto_kid": 35, "ab:naruto_teen": 35, "ab:naruto_war": 35, "ab:naruto_adult": 35,
  "ab:tanjiro_demon": 22, "ab:muzan": 0, "ab:broly": 22, "ab:madara": 23, "ab:sasuke": 21, "ab:sasuke_kid": 21, "ab:sasuke_war": 21, "ab:sasuke_adult": 0, "ab:ichigo": 19, "ab:tanjiro": 19 };
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
      if (ENTRANCE_LINES[e.typeId]) announce(e, ENTRANCE_LINES[e.typeId]);
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
    giveKit(p);
  } catch (e) { warn("kit", e); }
});

function giveKit(p) {
    const inv = p.getComponent("minecraft:inventory")?.container;
    for (const id of ["ab:team_stick", "ab:kill_stick", "ab:goku_spawn_egg", "ab:vegeta_spawn_egg", "ab:gojo_spawn_egg", "ab:yuji_spawn_egg", "ab:yuji_final_spawn_egg", "ab:sukuna_spawn_egg", "ab:luffy_spawn_egg", "ab:zoro_spawn_egg", "ab:frieza_spawn_egg", "ab:naruto_kid_spawn_egg", "ab:naruto_teen_spawn_egg", "ab:naruto_war_spawn_egg", "ab:naruto_adult_spawn_egg", "ab:sasuke_kid_spawn_egg", "ab:sasuke_spawn_egg", "ab:sasuke_war_spawn_egg", "ab:sasuke_adult_spawn_egg", "ab:ichigo_spawn_egg", "ab:tanjiro_spawn_egg", "ab:tanjiro_demon_spawn_egg", "ab:muzan_spawn_egg", "ab:broly_spawn_egg", "ab:madara_spawn_egg"]) {
      try { inv?.addItem(new ItemStack(id, 1)); } catch (e) { warn("kit " + id, e); }
    }
}
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id === "ab:griefing") world.setDynamicProperty("ab:griefing", ev.message.trim() !== "off");
  if (ev.id === "ab:fx") world.setDynamicProperty("ab:fx", ev.message.trim() === "low" ? 0.5 : 1);
  if (ev.id === "ab:vs" || ev.id === "ab:random") {
    const p = ev.sourceEntity && ev.sourceEntity.typeId === "minecraft:player" ? ev.sourceEntity : world.getPlayers()[0];
    if (!p) return;
    const ids = Object.keys(FIGHTERS).map((k) => k.slice(3));
    let [a, b] = ev.message.trim().toLowerCase().split(/\s+/);
    if (ev.id === "ab:random" || !a || !b) { a = ids[Math.floor(Math.random() * ids.length)]; do { b = ids[Math.floor(Math.random() * ids.length)]; } while (b === a); }
    startBattle(p, a, b);
  }
  if (ev.id === "ab:regen") world.setDynamicProperty("ab:regen", ev.message.trim() !== "off");
  if (ev.id === "ab:cinema") world.setDynamicProperty("ab:cinema", ev.message.trim() !== "off");
  if (ev.id === "ab:war") {  // team war: /scriptevent ab:war 4  (4 against 4, random fighters, fair teams)
    const p = ev.sourceEntity && ev.sourceEntity.typeId === "minecraft:player" ? ev.sourceEntity : world.getPlayers()[0];
    if (p) startWar(p, clamp(parseInt(ev.message, 10) || 3, 2, 6));
  }
  if (ev.id === "ab:kit") {  // every stick and spawn egg again: /scriptevent ab:kit
    for (const p of world.getPlayers()) giveKit(p);
  }
});
