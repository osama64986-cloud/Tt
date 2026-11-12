// Nabd night sight.
// Invisible light blocks follow every player, so the world around you is lit
// at night and underground.  Nothing else changes: no potion effect, so the
// sky keeps its own colours.  Lights are only ever placed in empty air and
// are removed again as soon as you move on.
import { world, system, BlockPermutation } from "@minecraft/server";

const LIGHT = 15;              // brightest light a block can give
const SPREAD = 7;              // extra lights this far around you, so the whole area is lit
const OFFSETS = [[0, 1, 0], [SPREAD, 1, 0], [-SPREAD, 1, 0], [0, 1, SPREAD], [0, 1, -SPREAD]];
const KEY = "nabd:lights";     // remembered across saves so nothing is left behind

let lightPerm;
function lightPermutation() {
  if (lightPerm) return lightPerm;
  try { lightPerm = BlockPermutation.resolve(`minecraft:light_block_${LIGHT}`); }                        // newer games
  catch { lightPerm = BlockPermutation.resolve("minecraft:light_block", { block_light_level: LIGHT }); }  // older games
  return lightPerm;
}

const placed = new Map();      // player id -> [{dim, x, y, z}]

function isOurLight(block) {
  return block && block.typeId && block.typeId.startsWith("minecraft:light_block");
}

function clear(list) {
  for (const p of list) {
    try {
      const block = world.getDimension(p.dim).getBlock(p);
      if (isOurLight(block)) block.setType("minecraft:air");
    } catch { /* chunk not loaded: cleaned up next time */ }
  }
}

function save() {
  const all = [];
  for (const list of placed.values()) all.push(...list);
  try { world.setDynamicProperty(KEY, JSON.stringify(all)); } catch {}
}

function update(player) {
  const dim = player.dimension;
  const base = player.location;
  const want = OFFSETS.map(([dx, dy, dz]) => ({
    dim: dim.id, x: Math.floor(base.x) + dx, y: Math.floor(base.y) + dy, z: Math.floor(base.z) + dz,
  }));
  const same = (a, b) => a.dim === b.dim && a.x === b.x && a.y === b.y && a.z === b.z;
  const old = placed.get(player.id) || [];
  clear(old.filter((o) => !want.some((w) => same(o, w))));
  const now = [];
  for (const w of want) {
    try {
      const block = dim.getBlock(w);
      if (!block) continue;
      if (block.isAir) block.setPermutation(lightPermutation());
      if (isOurLight(block)) now.push(w);
    } catch { /* outside the world or not loaded */ }
  }
  placed.set(player.id, now);
}

// leftovers from the last session
system.run(() => {
  try {
    const left = JSON.parse(world.getDynamicProperty(KEY) || "[]");
    clear(left);
  } catch {}
  world.setDynamicProperty(KEY, "[]");
});

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    try { update(player); } catch {}
  }
  save();
}, 4);

world.beforeEvents.playerLeave.subscribe((ev) => {
  const list = placed.get(ev.player.id) || [];
  placed.delete(ev.player.id);
  system.run(() => { clear(list); save(); });
});
