// Nabd extras: night sight.
//
//   Night vision on every player, particles off, topped up long before it runs
//   low (night vision flickers in its last ten seconds).  The resource pack
//   hides its icon.  Night vision lifts the night sky towards its day colour,
//   so a deep navy fog ("nabd:night_air", in the resource pack) is pushed onto
//   each player in the Overworld after sunset and removed at sunrise.
//
//   /nabd:settings   switch night sight on or off for yourself (no cheats needed)
import {
  world, system,
  CommandPermissionLevel, CustomCommandStatus,
} from "@minecraft/server";
import { ModalFormData } from "@minecraft/server-ui";

const NV_KEY = "nabd:nv";       // per player, default on
const OLD_CAMERA_KEY = "nabd:cam"; // left over from an older version of this pack

function nightSightOn(player) {
  try {
    const v = player.getDynamicProperty(NV_KEY);
    return v === undefined ? true : !!v;
  } catch { return true; }
}

function say(player, text) {
  try { player.onScreenDisplay.setActionBar(text); } catch {}
}

// ---------------------------------------------------------------- night sight
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

function command(player, text) {
  try { player.runCommand(text); return true; } catch { return false; }
}

function keepNightVision(player) {
  const fx = player.getEffect("night_vision");
  if (fx && fx.duration > TOP_UP_BELOW) return;
  player.addEffect("night_vision", LONG, { amplifier: 0, showParticles: false });
}

function keepNightSky(player, want) {
  const has = fogOn.has(player.id);
  if (want && !has) {
    if (command(player, `fog @s push ${FOG_ID} ${FOG_TAG}`)) fogOn.add(player.id);
  } else if (!want && has) {
    command(player, `fog @s remove ${FOG_TAG}`);
    fogOn.delete(player.id);
  }
}

function nightSightOff(player) {
  try {
    const fx = player.getEffect("night_vision");
    if (fx && fx.duration > TOP_UP_BELOW) player.removeEffect("night_vision");
  } catch {}
  keepNightSky(player, false);
}

// an older version of this pack could set a custom camera: make sure nobody is left in it
function clearOldCamera(player) {
  try {
    if (player.getDynamicProperty(OLD_CAMERA_KEY)) {
      player.setDynamicProperty(OLD_CAMERA_KEY, false);
      player.camera.clear();
    }
  } catch {}
}

// ---------------------------------------------------------------- settings menu
function openSettings(player, tries = 0) {
  new ModalFormData()
    .title("Nabd settings")
    .toggle("Night sight", { defaultValue: nightSightOn(player) })
    .submitButton("Save")
    .show(player).then((r) => {
      if (r.canceled) {
        // the chat screen may still be closing: try again a moment later
        if (r.cancelationReason === "UserBusy" && tries < 40) system.runTimeout(() => openSettings(player, tries + 1), 5);
        return;
      }
      const [nv] = r.formValues || [];
      const before = nightSightOn(player);
      try { player.setDynamicProperty(NV_KEY, !!nv); } catch {}
      if (before && !nv) nightSightOff(player);
      say(player, nv ? "Night sight: ON" : "Night sight: OFF");
    }).catch(() => {});
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.customCommandRegistry.registerCommand({
    name: "nabd:settings",
    description: "Nabd settings (night sight)",
    permissionLevel: CommandPermissionLevel.Any,
    cheatsRequired: false,
  }, (origin) => {
    const player = origin.sourceEntity;
    if (!player || player.typeId !== "minecraft:player") return { status: CustomCommandStatus.Failure, message: "Players only" };
    system.run(() => openSettings(player));
    return { status: CustomCommandStatus.Success };
  });
});

// ---------------------------------------------------------------- loops
system.run(() => {
  // clean-up from the light-block versions of this pack
  try {
    for (const k of JSON.parse(String(world.getDynamicProperty(OLD_LIGHTS) || "[]"))) {
      const [d, x, y, z] = k.split("|");
      try {
        const b = world.getDimension(d).getBlock({ x: +x, y: +y, z: +z });
        if (b && b.typeId && b.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air");
      } catch {}
    }
    world.setDynamicProperty(OLD_LIGHTS, "[]");
  } catch {}
  for (const player of world.getAllPlayers()) {
    // the game remembers pushed fogs across saves: start from a clean slate
    command(player, `fog @s remove ${FOG_TAG}`);
    clearOldCamera(player);
  }

  system.runInterval(() => {
    const night = isNight();
    for (const player of world.getAllPlayers()) {
      if (!nightSightOn(player)) continue;
      try { keepNightVision(player); } catch {}
      try { keepNightSky(player, night && player.dimension.id === "minecraft:overworld"); } catch {}
    }
  }, 20);                         // once a second is plenty
});

world.afterEvents.playerSpawn.subscribe((ev) => {
  const player = ev.player;
  if (ev.initialSpawn) {
    // a player who joins may still carry the fog from an earlier session
    command(player, `fog @s remove ${FOG_TAG}`);
    fogOn.delete(player.id);
    clearOldCamera(player);
  }
});

world.afterEvents.playerLeave.subscribe((ev) => {
  fogOn.delete(ev.playerId);
});
