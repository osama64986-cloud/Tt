#!/usr/bin/env python3
"""World mood: soft distance haze + more cheerful biome greens.

    python3 tools/make_world.py /path/to/bedrock-samples/resource_pack

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
HAZE = {"fog_start": 0.42, "fog_end": 1.0, "fog_color": "#C3E2FF", "render_distance_type": "render"}
VOLUME = {                                   # Vibrant Visuals: thin ground mist that fades with height
    "density": {"air": {"max_density": 0.04, "zero_density_height": 150.0, "max_density_height": 62.0}},
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
    # only touch the plain daylight air fog (the default and the biomes that
    # repeat it); caves, nether, end, swamps and the pale garden keep theirs
    if not (is_default or (air and air.get("fog_color", "").upper() == "#ABD2FF")):
        continue
    fs.setdefault("distance", {})["air"] = dict(HAZE)
    if is_default:
        fs["volumetric"] = VOLUME
    json.dump(j, open(os.path.join(OUT, "fogs", f), "w"), indent=2)
    n += 1
print(n, "fog settings")

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
