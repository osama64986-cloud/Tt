// Nabd night sight.
//
// 1) Night vision on every player, particles off, topped up long before it
//    runs low (night vision flickers in its last ten seconds).  The resource
//    pack hides its icon, so nothing shows on screen.
// 2) Night vision lifts the night sky towards its day colour.  To keep nights
//    looking like nights, a deep navy fog ("nabd:night_air", defined in the
//    resource pack) is pushed onto each player in the Overworld after sunset
//    and taken off again at sunrise.  The fog colours the horizon and the far
//    sky, so the scene keeps a night mood while the ground stays visible.
import { world, system } from "@minecraft/server";

const LONG = 20 * 60 * 30;      // 30 minutes
const TOP_UP_BELOW = 20 * 60;   // refresh when under a minute is left
const FOG_ID = "nabd:night_air";
const FOG_TAG = "nabd_night";
const OLD_LIGHTS = "nabd:lights";

const fogOn = new Set();        // players who currently have the night fog

function isNight() {
  const t = world.getTimeOfDay();            // 0 sunrise, 6000 noon, 12000 sunset, 18000 midnight
  return t > 12600 && t < 23400;
}

function keepNightVision(player) {
  const fx = player.getEffect("night_vision");
  if (fx && fx.duration > TOP_UP_BELOW) return;
  player.addEffect("night_vision", LONG, { amplifier: 0, showParticles: false });
}

function command(player, text) {
  try { player.runCommand(text); return true; } catch { return false; }
}

function keepNightSky(player, night) {
  const want = night && player.dimension.id === "minecraft:overworld";
  const has = fogOn.has(player.id);
  if (want && !has) {
    if (command(player, `fog @s push ${FOG_ID} ${FOG_TAG}`)) fogOn.add(player.id);
  } else if (!want && has) {
    command(player, `fog @s remove ${FOG_TAG}`);
    fogOn.delete(player.id);
  }
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
  // the game remembers pushed fogs across saves: start from a clean slate
  for (const player of world.getAllPlayers()) command(player, `fog @s remove ${FOG_TAG}`);

  system.runInterval(() => {
    const night = isNight();
    for (const player of world.getAllPlayers()) {
      try { keepNightVision(player); } catch {}
      try { keepNightSky(player, night); } catch {}
    }
  }, 20);                         // once a second is plenty
});

// a player who joins later may still carry the fog from an earlier session
world.afterEvents.playerSpawn.subscribe((ev) => {
  if (!ev.initialSpawn) return;
  command(ev.player, `fog @s remove ${FOG_TAG}`);
  fogOn.delete(ev.player.id);
});
