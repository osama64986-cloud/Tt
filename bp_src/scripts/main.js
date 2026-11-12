// Nabd extras: night sight + shoulder camera.
//
// Night sight
//   Night vision on every player, particles off, topped up long before it runs
//   low (night vision flickers in its last ten seconds).  The resource pack
//   hides its icon.  Night vision lifts the night sky towards its day colour,
//   so a deep navy fog ("nabd:night_air", in the resource pack) is pushed onto
//   each player in the Overworld after sunset and removed at sunrise.
//
// Shoulder camera ("fourth view")
//   The game's own follow_orbit camera, shifted to the side so the character
//   stands a little left or right and the middle of the screen is free.
//   The presets live in cameras/presets; the side shift and height are applied
//   here so they can be changed in the settings menu.  A small aim marker is
//   drawn where the hit or click will land (the game hides its crosshair in
//   third person).  Purely visual: reach, damage and aiming are the game's own.
//
// Controls (no cheats needed)
//   /nabd:camera            switch the shoulder camera on / off
//   /nabd:camera left|right put it over the left / right shoulder
//   /nabd:settings          menu: camera, distance, side, height, marker, night sight
//   Look straight up and crouch twice quickly: switch the camera on / off.
import {
  world, system, MolangVariableMap,
  CommandPermissionLevel, CustomCommandParamType, CustomCommandStatus,
} from "@minecraft/server";
import { ModalFormData } from "@minecraft/server-ui";

// ---------------------------------------------------------------- settings
const DEFAULTS = {
  "nabd:cam": false,        // shoulder camera on
  "nabd:cam_side": 1,       // 1 right shoulder, -1 left shoulder
  "nabd:cam_x": 8,          // side shift, tenths of a block
  "nabd:cam_y": 2,          // raise, tenths of a block
  "nabd:cam_dist": 1,       // 0 near, 1 middle, 2 far
  "nabd:cam_free": false,   // false: classic controls, true: character turns to where it walks
  "nabd:aim": true,         // aim marker
  "nabd:nv": true,          // night sight
};
const DISTANCE_NAMES = ["near", "mid", "far"];

function get(player, key) {
  try {
    const v = player.getDynamicProperty(key);
    return v === undefined ? DEFAULTS[key] : v;
  } catch { return DEFAULTS[key]; }
}
function set(player, key, value) {
  try { player.setDynamicProperty(key, value); } catch {}
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

// ---------------------------------------------------------------- shoulder camera
function presetFor(player) {
  const d = DISTANCE_NAMES[get(player, "nabd:cam_dist")] || "mid";
  return `nabd:shoulder_${d}${get(player, "nabd:cam_free") ? "_free" : ""}`;
}

function applyCamera(player) {
  if (!get(player, "nabd:cam")) return;
  const side = get(player, "nabd:cam_side") >= 0 ? 1 : -1;
  const x = side * get(player, "nabd:cam_x") / 10;
  const y = get(player, "nabd:cam_y") / 10;
  try {
    player.camera.setCamera(presetFor(player), {
      viewOffset: { x, y },
      entityOffset: { x: 0, y: 0.55, z: 0 },
    });
  } catch {
    // older game versions or a preset that failed to load: fall back to the plain one
    try { player.camera.setCamera(presetFor(player)); } catch {}
  }
}

function setShoulder(player, on, quiet) {
  set(player, "nabd:cam", on);
  if (on) applyCamera(player);
  else { try { player.camera.clear(); } catch {} }
  if (!quiet) say(player, on ? "Shoulder camera: ON" : "Shoulder camera: OFF");
}

// aim marker: where the hit / click from the player's eyes lands
const ENTITY_REACH = 3.0;
const FAR = 48;

function drawAim(player) {
  const head = player.getHeadLocation();
  const dir = player.getViewDirection();
  let dist = FAR;
  let onMob = false;
  try {
    const hits = player.getEntitiesFromViewDirection({ maxDistance: FAR });
    for (const h of hits) {
      if (h.entity.id === player.id) continue;
      dist = h.distance;
      onMob = h.distance <= ENTITY_REACH;
      break;
    }
  } catch {}
  try {
    const b = player.getBlockFromViewDirection({ maxDistance: FAR, includePassableBlocks: true, includeLiquidBlocks: false });
    if (b) {
      const p = { x: b.block.location.x + b.faceLocation.x, y: b.block.location.y + b.faceLocation.y, z: b.block.location.z + b.faceLocation.z };
      const d = Math.hypot(p.x - head.x, p.y - head.y, p.z - head.z);
      if (d < dist) { dist = d; onMob = false; }
    }
  } catch {}
  const back = Math.min(0.12, dist * 0.1);  // sit just in front of the surface
  const at = { x: head.x + dir.x * (dist - back), y: head.y + dir.y * (dist - back), z: head.z + dir.z * (dist - back) };
  const radius = [2.6, 3.6, 4.8][get(player, "nabd:cam_dist")] || 3.6;
  const vars = new MolangVariableMap();
  vars.setFloat("variable.size", Math.max(0.035, 0.012 * (dist + radius)));
  vars.setFloat("variable.red", 1.0);
  vars.setFloat("variable.green", onMob ? 0.32 : 1.0);
  vars.setFloat("variable.blue", onMob ? 0.3 : 1.0);
  player.spawnParticle("nabd:aim", at, vars);
}

// gesture: look straight up and crouch twice within half a second
const sneakState = new Map();   // id -> { was, last }
function checkGesture(player, tick) {
  let s = sneakState.get(player.id);
  if (!s) { s = { was: false, last: -100 }; sneakState.set(player.id, s); }
  const now = player.isSneaking;
  if (now && !s.was) {
    const lookingUp = player.getRotation().x < -55;
    if (lookingUp && tick - s.last <= 10) {
      setShoulder(player, !get(player, "nabd:cam"));
      s.last = -100;
    } else {
      s.last = lookingUp ? tick : -100;
    }
  }
  s.was = now;
}

// ---------------------------------------------------------------- settings menu
function openSettings(player, tries = 0) {
  const form = new ModalFormData()
    .title("Nabd settings")
    .toggle("Shoulder camera (4th view)", { defaultValue: !!get(player, "nabd:cam") })
    .dropdown("Shoulder", ["Right shoulder", "Left shoulder"], { defaultValueIndex: get(player, "nabd:cam_side") >= 0 ? 0 : 1 })
    .dropdown("Distance", ["Near", "Middle", "Far"], { defaultValueIndex: get(player, "nabd:cam_dist") })
    .slider("Side shift (tenths of a block)", 0, 15, { valueStep: 1, defaultValue: get(player, "nabd:cam_x") })
    .slider("Height (tenths of a block)", -5, 15, { valueStep: 1, defaultValue: get(player, "nabd:cam_y") })
    .toggle("Free turning (character faces where it walks)", { defaultValue: !!get(player, "nabd:cam_free") })
    .toggle("Aim marker", { defaultValue: !!get(player, "nabd:aim") })
    .toggle("Night sight", { defaultValue: !!get(player, "nabd:nv") })
    .submitButton("Save");
  form.show(player).then((r) => {
    if (r.canceled) {
      // the chat screen may still be closing: try again a moment later
      if (r.cancelationReason === "UserBusy" && tries < 40) system.runTimeout(() => openSettings(player, tries + 1), 5);
      return;
    }
    const [cam, side, dist, x, y, free, aim, nv] = r.formValues || [];
    set(player, "nabd:cam_side", side === 1 ? -1 : 1);
    set(player, "nabd:cam_dist", dist);
    set(player, "nabd:cam_x", x);
    set(player, "nabd:cam_y", y);
    set(player, "nabd:cam_free", !!free);
    set(player, "nabd:aim", !!aim);
    const nvBefore = !!get(player, "nabd:nv");
    set(player, "nabd:nv", !!nv);
    if (nvBefore && !nv) nightSightOff(player);
    setShoulder(player, !!cam, true);
    say(player, "Nabd settings saved");
  }).catch(() => {});
}

// ---------------------------------------------------------------- commands
system.beforeEvents.startup.subscribe((ev) => {
  const reg = ev.customCommandRegistry;
  reg.registerEnum("nabd:camera_mode", ["on", "off", "left", "right"]);
  reg.registerCommand({
    name: "nabd:camera",
    description: "Shoulder camera: on, off, left or right (no option switches it on/off)",
    permissionLevel: CommandPermissionLevel.Any,
    cheatsRequired: false,
    optionalParameters: [{ type: CustomCommandParamType.Enum, name: "nabd:camera_mode" }],
  }, (origin, mode) => {
    const player = origin.sourceEntity;
    if (!player || player.typeId !== "minecraft:player") return { status: CustomCommandStatus.Failure, message: "Players only" };
    system.run(() => {
      if (mode === "left" || mode === "right") {
        set(player, "nabd:cam_side", mode === "left" ? -1 : 1);
        setShoulder(player, true);
      } else if (mode === "on" || mode === "off") {
        setShoulder(player, mode === "on");
      } else {
        setShoulder(player, !get(player, "nabd:cam"));
      }
    });
    return { status: CustomCommandStatus.Success };
  });
  reg.registerCommand({
    name: "nabd:settings",
    description: "Open the Nabd settings (shoulder camera, aim marker, night sight)",
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
    applyCamera(player);
  }

  system.runInterval(() => {
    const night = isNight();
    for (const player of world.getAllPlayers()) {
      if (!get(player, "nabd:nv")) continue;
      try { keepNightVision(player); } catch {}
      try { keepNightSky(player, night && player.dimension.id === "minecraft:overworld"); } catch {}
    }
  }, 20);                         // once a second is plenty

  system.runInterval(() => {
    const tick = system.currentTick;
    for (const player of world.getAllPlayers()) {
      // (the look-up gesture was removed: the shoulder view now comes from the resource pack settings)
      if (get(player, "nabd:cam") && get(player, "nabd:aim")) {
        try { drawAim(player); } catch {}
      }
    }
  }, 1);
});

world.afterEvents.playerSpawn.subscribe((ev) => {
  const player = ev.player;
  if (ev.initialSpawn) {
    // a player who joins may still carry the fog from an earlier session
    command(player, `fog @s remove ${FOG_TAG}`);
    fogOn.delete(player.id);
  }
  // cameras reset on joining and sometimes on respawn: put the shoulder view back
  system.runTimeout(() => applyCamera(player), 2);
});

world.afterEvents.playerDimensionChange.subscribe((ev) => {
  system.runTimeout(() => applyCamera(ev.player), 2);
});

world.afterEvents.playerLeave.subscribe((ev) => {
  fogOn.delete(ev.playerId);
  sneakState.delete(ev.playerId);
});
