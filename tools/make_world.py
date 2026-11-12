#!/usr/bin/env python3
"""World mood: soft distance haze + more cheerful biome greens.

    python3 tools/make_world.py /path/to/bedrock-samples/resource_pack

Also writes lighting/: a see-in-the-dark setup for Vibrant Visuals that lifts
ambient light (strongly at night) without touching the sky or fog colours.

Writes into pack_src/ (committed, so the normal build needs no game files):
  fogs/                 our own haze values on top of the game's fog layout
  textures/colormap/    the game's biome colour tables, pushed towards
                        brighter, more saturated greens
"""
import colorsys
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1]
OUT = os.path.join(ROOT, "pack_src")

# ------------------------------------------------------------------- haze
HAZE = {"fog_start": 0.3, "fog_end": 1.0, "fog_color": "#C3E2FF", "render_distance_type": "render"}   # soft haze, clearly visible in the distance
VOLUME = {                                   # Vibrant Visuals: thin ground mist that fades with height
    "density": {"air": {"max_density": 0.03, "zero_density_height": 150.0, "max_density_height": 62.0}},
    "media_coefficients": {"air": {"scattering": [0.045, 0.05, 0.06], "absorption": [0.0, 0.0, 0.0]}},
    "henyey_greenstein_g": {"air": {"henyey_greenstein_g": 0.5}},
}
fdir = os.path.join(SRC, "fogs")
os.makedirs(os.path.join(OUT, "fogs"), exist_ok=True)
n = 0
for f in sorted(os.listdir(fdir)):
    j = json.load(open(os.path.join(fdir, f)))
    fs = j["minecraft:fog_settings"]
    air = fs.get("distance", {}).get("air")
    is_default = fs["description"]["identifier"] == "minecraft:fog_default"
    # every overworld biome gets the haze written into its own file, so it shows
    # whatever the biome; the Nether, the End (fixed-distance fogs) and the
    # pale garden / swamp moods keep their own
    ident = fs["description"]["identifier"]
    special = any(k in ident for k in ("hell", "crimson", "warped", "soulsand", "basalt", "the_end", "pale_garden", "swamp", "mangrove"))
    if special or (air and air.get("render_distance_type") == "fixed"):
        continue
    fs.setdefault("distance", {})["air"] = dict(HAZE)
    if is_default:
        fs["volumetric"] = VOLUME
    json.dump(j, open(os.path.join(OUT, "fogs", f), "w"), indent=2)
    n += 1
print(n, "fog settings")

# ------------------------------------------------------------ night sight
# time_of_day: 0 = noon, 0.5 = midnight.  Ambient light has no direction, so
# it reaches every block face, caves included; the sky is drawn separately
# and keeps its colours.
AMBIENT = {"color": "#FFFFFF",
           "illuminance": {"0.000000": 0.3, "0.240000": 0.3, "0.300000": 1.5, "0.700000": 1.5, "0.760000": 0.3, "1.000000": 0.3}}
ldir = os.path.join(SRC, "lighting")
os.makedirs(os.path.join(OUT, "lighting"), exist_ok=True)
n = 0
for f in sorted(os.listdir(ldir)):
    j = json.load(open(os.path.join(ldir, f)))
    ls = j["minecraft:lighting_settings"]
    ident = ls["description"]["identifier"]
    if "nether" in ident:
        ls["ambient"] = {"color": "#FFFFFF", "illuminance": 1.2}
    elif "end_" in ident:
        ls["ambient"] = {"color": [255, 255, 255], "illuminance": 1.0}
    else:
        ls["ambient"] = AMBIENT
        moon = ls.setdefault("directional_lights", {}).setdefault("orbital", {}).setdefault("moon", {})
        if isinstance(moon.get("illuminance"), dict):
            moon["illuminance"] = {k: (1.0 if v > 0 else 0.0) for k, v in moon["illuminance"].items()}
    json.dump(j, open(os.path.join(OUT, "lighting", f), "w"), indent=2)
    n += 1
print(n, "lighting settings")

# ------------------------------------------------------------ biome colours
cdir = os.path.join(SRC, "textures", "colormap")
os.makedirs(os.path.join(OUT, "textures", "colormap"), exist_ok=True)
for f in sorted(os.listdir(cdir)):
    im = Image.open(os.path.join(cdir, f))
    mode = im.mode
    a = np.array(im.convert("RGBA")).astype(float) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a[..., :3].max(-1), a[..., :3].min(-1)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    dry = f.startswith("dry")
    s2 = np.clip(s * (1 + (0.12 if dry else 0.34) * (1 - s)) + (0.0 if dry else 0.04), 0, 1)   # vivid, never clipped
    v2 = np.clip(v * 1.06 + 0.02, 0, 1)
    # rebuild rgb with the same hue
    k = np.where((mx - mn > 1e-6)[..., None], (a[..., :3] - mn[..., None]) / np.maximum((mx - mn)[..., None], 1e-6), 0)
    rgb = (v2 * (1 - s2))[..., None] + k * (v2 * s2)[..., None]
    out = np.dstack([np.clip(rgb, 0, 1), a[..., 3]])
    Image.fromarray((out * 255).round().astype(np.uint8), "RGBA").convert(mode).save(os.path.join(OUT, "textures", "colormap", f))
    print(f, "mean", (a[..., :3].reshape(-1, 3).mean(0) * 255).round().astype(int).tolist(), "->",
          (rgb.reshape(-1, 3).mean(0) * 255).round().astype(int).tolist())
