#!/usr/bin/env python3
"""Builds the Nabd resource pack.

    python3 tools/build.py            -> writes pack/ and dist/Nabd.mcpack
    python3 tools/build.py --preview  -> also writes preview sheets to preview/

Every block texture is painted procedurally by tools/nabd (original art).
Hand-written files (manifest, player animations, ...) live in pack_src/ and are
copied over as-is.
"""
import json
import os
import shutil
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from nabd import core  # noqa: E402
from nabd import blocks_terrain  # noqa: E402

try:
    from nabd import blocks_wood, blocks_build, blocks_plants  # noqa: E402
    EXTRA = [blocks_wood, blocks_build, blocks_plants]
except ImportError as e:  # modules are added progressively
    EXTRA = []
    for m in ("blocks_wood", "blocks_build", "blocks_plants"):
        try:
            EXTRA.append(__import__("nabd." + m, fromlist=[m]))
        except ImportError:
            pass

PACK = os.path.join(ROOT, "pack")
SRC = os.path.join(ROOT, "pack_src")
DIST = os.path.join(ROOT, "dist")
PREVIEW = os.path.join(ROOT, "preview")


def generate():
    out, flip, variations = {}, {}, {}
    blocks_terrain.build(out, flip, variations)
    for m in EXTRA:
        m.build(out, flip, variations)
    return out, flip, variations


def write_tex(name, tex):
    """Writes colour (+ same file types the game ships), MERS, normal and the
    texture set that ties them together for Vibrant Visuals."""
    base = os.path.join(PACK, "textures", "blocks", name)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    st = core.STATS.get(name)
    exts = st["ext"] if st else ["png"]
    img = tex.color_image()
    for ext in exts:
        img.save(base + "." + ext)
    stem = os.path.basename(name)
    tex.mers_image().save(base + "_mers.tga")
    frame_h = tex.w if tex.h > tex.w else None
    tex.normal_image(frame_h).save(base + "_normal.png")
    ts = {"format_version": "1.21.30",
          "minecraft:texture_set": {"color": stem,
                                    "metalness_emissive_roughness_subsurface": stem + "_mers",
                                    "normal": stem + "_normal"}}
    json.dump(ts, open(base + ".texture_set.json", "w"), indent=2)


def write_atlas(out, flip, variations):
    td = {}
    for short, names in variations.items():
        td[short] = {"textures": {"variations": [{"path": "textures/blocks/" + n} for n in names]}}
    fb = []
    for key, f in flip.items():
        short = f.get("short", os.path.basename(key))
        fb.append({"flipbook_texture": "textures/blocks/" + f["strip"], "atlas_tile": short,
                   "ticks_per_frame": f["ticks"], "blend_frames": f.get("blend", False)})
    return td, fb


def lenient_json(path):
    import re
    s = open(path, encoding="utf-8-sig").read()
    s = re.sub(r"//[^\n]*", "", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return json.loads(s)


def sheet(out, names, path, scale=5, cols=10, tile=2):
    cell = core.N * scale * tile
    pad, lab = 6, 12
    rows = (len(names) + cols - 1) // cols
    W = cols * (cell + pad) + pad
    H = rows * (cell + pad + lab) + pad
    im = Image.new("RGB", (W, H), (38, 40, 46))
    d = ImageDraw.Draw(im)
    for i, n in enumerate(names):
        t = out[n]
        rgba = np.dstack([t.rgb, t.alpha])[: t.w]          # first frame only
        bg = np.zeros_like(rgba)
        bg[..., :3] = (70, 110, 150)
        bg[..., 3] = 255
        a = rgba[..., 3:4].astype(float) / 255
        comp = (rgba[..., :3] * a + bg[..., :3] * (1 - a)).astype(np.uint8)
        comp = np.tile(comp, (tile, tile, 1))
        ti = Image.fromarray(comp, "RGB").resize((cell, cell), Image.NEAREST)
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad + lab)
        im.paste(ti, (x, y))
        d.text((x, y + cell), os.path.basename(n)[:26], fill=(220, 220, 220))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    preview = "--preview" in sys.argv
    out, flip, variations = generate()
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    if os.path.isdir(SRC):
        shutil.copytree(SRC, PACK)
    else:
        os.makedirs(PACK)
    for name, tex in out.items():
        write_tex(name, tex)
    td, fb = write_atlas(out, flip, variations)
    tdir = os.path.join(PACK, "textures")
    if td:
        json.dump({"resource_pack_name": "nabd", "texture_name": "atlas.terrain", "texture_data": td},
                  open(os.path.join(tdir, "terrain_texture.json"), "w"), indent=2)
    if fb:
        json.dump(fb, open(os.path.join(tdir, "flipbook_textures.json"), "w"), indent=2)
    print(f"{len(out)} textures, {len(variations)} variation groups, {len(fb)} flipbooks")
    if preview:
        names = list(out)
        for i in range(0, len(names), 80):
            sheet(out, names[i:i + 80], os.path.join(PREVIEW, f"sheet_{i // 80:02d}.png"))
    if os.path.exists(os.path.join(PACK, "manifest.json")):
        os.makedirs(DIST, exist_ok=True)
        zp = os.path.join(DIST, "Nabd.mcpack")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for d, _, fs in os.walk(PACK):
                for f in sorted(fs):
                    p = os.path.join(d, f)
                    z.write(p, os.path.relpath(p, PACK))
        print("wrote", zp, round(os.path.getsize(zp) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
