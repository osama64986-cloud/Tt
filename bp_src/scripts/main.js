// Nabd night sight.
// Gives every player night vision with its particles switched off, and keeps
// it topped up long before it runs low (night vision flickers in its last
// ten seconds, so it never gets there).  Milk, death or a server reset only
// interrupt it for a moment.  The matching resource pack hides the effect
// icon, so nothing shows on screen.
//
// Earlier versions placed invisible light blocks; any left in the world are
// removed once when the world loads.
import { world, system } from "@minecraft/server";

const LONG = 20 * 60 * 30;      // 30 minutes
const TOP_UP_BELOW = 20 * 60;   // refresh when under a minute is left (flicker starts at 10 s)
const OLD_LIGHTS = "nabd:lights";

function keepNightVision(player) {
  const fx = player.getEffect("night_vision");
  if (fx && fx.duration > TOP_UP_BELOW) return;
  player.addEffect("night_vision", LONG, { amplifier: 0, showParticles: false });
}

system.run(() => {
  // clean-up from the light-block versions of this pack
  try {
    for (const k of JSON.parse(world.getDynamicProperty(OLD_LIGHTS) || "[]")) {
      const [d, x, y, z] = k.split("|");
      try {
        const b = world.getDimension(d).getBlock({ x: +x, y: +y, z: +z });
        if (b && b.typeId && b.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air");
      } catch {}
    }
    world.setDynamicProperty(OLD_LIGHTS, "[]");
  } catch {}

  system.runInterval(() => {
    for (const player of world.getAllPlayers()) {
      try { keepNightVision(player); } catch {}
    }
  }, 20);                         // once a second is plenty
});
