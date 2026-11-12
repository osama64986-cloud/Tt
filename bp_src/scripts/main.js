// Nabd night sight.
// A grid of invisible light blocks surrounds every player in all directions
// (about 30 blocks out, above and below too), so the world around you is lit
// at night and underground.  No potion effect is used, so the sky keeps its
// own colours.  Lights are only placed in empty air; the grid is pinned to
// world coordinates, so as you walk only the lights at its edges change.
import { world, system, BlockPermutation } from "@minecraft/server";

const LIGHT = 15;         // brightest light a block can give
const STEP = 10;          // distance between lights: every spot stays bright
const RADIUS = 30;        // how far around you the grid reaches, in blocks
const SEARCH = [0, 1, -1, 2, -2, 3, -3];   // if the grid point is solid, look up/down for air
const KEY = "nabd:lights";
const PERIOD = 10;        // ticks between updates (half a second)

let lightPerm;
function lightPermutation() {
  if (lightPerm) return lightPerm;
  try { lightPerm = BlockPermutation.resolve(`minecraft:light_block_${LIGHT}`); }                        // newer games
  catch { lightPerm = BlockPermutation.resolve("minecraft:light_block", { block_light_level: LIGHT }); }  // older games
  return lightPerm;
}

const isOurLight = (b) => b && b.typeId && b.typeId.startsWith("minecraft:light_block");
const keyOf = (d, x, y, z) => `${d}|${x}|${y}|${z}`;
const parse = (k) => { const [d, x, y, z] = k.split("|"); return { d, x: +x, y: +y, z: +z }; };

// grid offsets inside a sphere of RADIUS
const OFFSETS = [];
for (let dx = -RADIUS; dx <= RADIUS; dx += STEP)
  for (let dy = -RADIUS; dy <= RADIUS; dy += STEP)
    for (let dz = -RADIUS; dz <= RADIUS; dz += STEP)
      if (dx * dx + dy * dy + dz * dz <= (RADIUS + STEP / 2) ** 2) OFFSETS.push([dx, dy, dz]);

let placed = new Map();   // grid key -> actual key of the light block we put there (null: no air found there)
let ticks = 0;

function remove(actualKey) {
  const p = parse(actualKey);
  try {
    const b = world.getDimension(p.d).getBlock(p);
    if (isOurLight(b)) b.setType("minecraft:air");
  } catch { /* not loaded: cleaned up on the next visit or next load */ }
}

function save() {
  try { world.setDynamicProperty(KEY, JSON.stringify([...placed.values()].filter(Boolean))); } catch {}
}

function placeNear(dim, x, y, z) {
  for (const oy of SEARCH) {
    try {
      const b = dim.getBlock({ x, y: y + oy, z });
      if (!b) return null;
      if (isOurLight(b)) return keyOf(dim.id, x, y + oy, z);
      if (b.isAir) {
        b.setPermutation(lightPermutation());
        return keyOf(dim.id, x, y + oy, z);
      }
    } catch { return null; }
  }
  return null;
}

function tick() {
  const want = new Map();     // grid key -> {dim, x, y, z}
  for (const player of world.getAllPlayers()) {
    const dim = player.dimension;
    const l = player.location;
    const cx = Math.round(l.x / STEP) * STEP, cy = Math.round(l.y / STEP) * STEP, cz = Math.round(l.z / STEP) * STEP;
    for (const [dx, dy, dz] of OFFSETS) {
      const x = cx + dx, y = cy + dy, z = cz + dz;
      want.set(keyOf(dim.id, x, y, z), { dim, x, y, z });
    }
    // one light right above the player's head, so you are never in the dark
    const hx = Math.floor(l.x), hy = Math.floor(l.y) + 2, hz = Math.floor(l.z);
    want.set(keyOf(dim.id, hx, hy, hz) + "|head", { dim, x: hx, y: hy, z: hz });
  }
  const next = new Map();
  const retry = ++ticks % 20 === 0;        // every 10 s look again at spots that were solid (you may have dug them out)
  for (const [gk, actual] of placed) {
    if (!want.has(gk)) { if (actual) remove(actual); }
    else if (actual || !retry) next.set(gk, actual);
  }
  for (const [gk, w] of want) {
    if (next.has(gk)) continue;
    next.set(gk, placeNear(w.dim, w.x, w.y, w.z));
  }
  placed = next;
  save();
}

// clean up whatever the last session left behind, then start
system.run(() => {
  try { for (const k of JSON.parse(world.getDynamicProperty(KEY) || "[]")) remove(k); } catch {}
  try { world.setDynamicProperty(KEY, "[]"); } catch {}
  system.runInterval(() => { try { tick(); } catch {} }, PERIOD);
});

// when a player leaves, the next tick drops the lights nobody needs any more
world.afterEvents.playerLeave.subscribe(() => system.run(() => { try { tick(); } catch {} }));
