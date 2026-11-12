// Nabd night sight (light edition).
// Invisible light blocks around each player so you can see at night and
// underground.  No potion effect: the sky keeps its own colours.
//
// Kept light on the device on purpose:
//  - a sparse grid (one light every STEP blocks) on three layers only
//  - the grid is pinned to world coordinates and recomputed only when you
//    step into a new grid cell
//  - at most BUDGET block changes per tick, so walking never causes a spike
//  - in daylight under open sky no lights are used at all
import { world, system, BlockPermutation } from "@minecraft/server";

const LIGHT = 15;            // brightest light a block can give
const STEP = 12;             // distance between lights
const RADIUS = 30;           // how far around you, horizontally
const LAYERS = [-STEP, 0, STEP];
const BUDGET = 6;            // block changes per tick, at most
const SEARCH = [0, 1, -1, 2, -2, 3, -3];
const KEY = "nabd:lights";

let lightPerm;
function lightPermutation() {
  if (lightPerm) return lightPerm;
  try { lightPerm = BlockPermutation.resolve(`minecraft:light_block_${LIGHT}`); }
  catch { lightPerm = BlockPermutation.resolve("minecraft:light_block", { block_light_level: LIGHT }); }
  return lightPerm;
}

const isOurLight = (b) => b && b.typeId && b.typeId.startsWith("minecraft:light_block");
const keyOf = (d, x, y, z) => `${d}|${x}|${y}|${z}`;
const parse = (k) => { const [d, x, y, z] = k.split("|"); return { d, x: +x, y: +y, z: +z }; };

// grid centred on the player's cell; outer lights at ~24 blocks shine on to ~38
const OFFSETS = [];
const K = Math.floor(RADIUS / STEP);
for (let i = -K; i <= K; i++)
  for (let j = -K; j <= K; j++)
    if ((i * STEP) ** 2 + (j * STEP) ** 2 <= RADIUS * RADIUS)
      for (const dy of LAYERS) OFFSETS.push([i * STEP, dy, j * STEP]);

let placed = new Map();      // grid key -> actual light key (null: no air there)
let want = new Map();        // grid key -> {dim, x, y, z}
let lastCells = "";
let tickNo = 0;

function isDaylight() {
  const t = world.getTimeOfDay();            // 0 sunrise, 6000 noon, 12000 sunset, 18000 midnight
  return t < 12300 || t > 23700;
}

function underOpenSky(player) {
  if (player.dimension.id !== "minecraft:overworld") return false;
  try {
    const head = player.getHeadLocation();
    const hit = player.dimension.getBlockFromRay(head, { x: 0, y: 1, z: 0 }, { maxDistance: 96 });
    return !hit;
  } catch { return false; }
}

function remove(actualKey) {
  const p = parse(actualKey);
  try {
    const b = world.getDimension(p.d).getBlock(p);
    if (isOurLight(b)) b.setType("minecraft:air");
  } catch {}
}

function placeNear(dim, x, y, z) {
  for (const oy of SEARCH) {
    try {
      const b = dim.getBlock({ x, y: y + oy, z });
      if (!b) return null;
      if (isOurLight(b)) return keyOf(dim.id, x, y + oy, z);
      if (b.isAir) { b.setPermutation(lightPermutation()); return keyOf(dim.id, x, y + oy, z); }
    } catch { return null; }
  }
  return null;
}

function recompute() {
  const day = isDaylight();
  const next = new Map();
  const cells = [];
  for (const player of world.getAllPlayers()) {
    const dim = player.dimension;
    const l = player.location;
    if (day && underOpenSky(player)) { cells.push(`${player.id}:off`); continue; }
    const cx = Math.round(l.x / STEP) * STEP, cy = Math.round(l.y / STEP) * STEP, cz = Math.round(l.z / STEP) * STEP;
    cells.push(`${player.id}:${dim.id}:${cx}:${cy}:${cz}`);
    for (const [dx, dy, dz] of OFFSETS) {
      const x = cx + dx, y = cy + dy, z = cz + dz;
      next.set(keyOf(dim.id, x, y, z), { dim, x, y, z });
    }
  }
  const sig = cells.join(",");
  const changed = sig !== lastCells;
  lastCells = sig;
  if (changed) want = next;
  return changed;
}

function work() {
  let budget = BUDGET;
  // 1) take away lights nobody needs any more
  for (const [gk, actual] of placed) {
    if (budget <= 0) return;
    if (!want.has(gk)) {
      if (actual) { remove(actual); budget--; }
      placed.delete(gk);
    }
  }
  // 2) add the missing ones
  for (const [gk, w] of want) {
    if (budget <= 0) return;
    if (placed.has(gk)) continue;
    placed.set(gk, placeNear(w.dim, w.x, w.y, w.z));
    budget--;
  }
}

function save() {
  try { world.setDynamicProperty(KEY, JSON.stringify([...placed.values()].filter(Boolean))); } catch {}
}

system.run(() => {
  try { for (const k of JSON.parse(world.getDynamicProperty(KEY) || "[]")) remove(k); } catch {}
  try { world.setDynamicProperty(KEY, "[]"); } catch {}
  system.runInterval(() => {
    tickNo++;
    try {
      if (tickNo % 10 === 0) recompute();                  // twice a second: has anyone stepped into a new cell?
      if (tickNo % 200 === 0)                              // every 10 s: retry spots that were solid
        for (const [gk, actual] of placed) if (!actual) placed.delete(gk);
      work();
      if (tickNo % 40 === 0) save();
    } catch {}
  }, 1);
});
