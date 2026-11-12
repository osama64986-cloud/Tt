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

from nabd import blocks_wood, blocks_build, blocks_plants, blocks_village  # noqa: E402
from nabd import blocks_nether_end, blocks_more, blocks_fluids, blocks_minerals, blocks_rest  # noqa: E402
from nabd import items  # noqa: E402

EXTRA = [blocks_wood, blocks_build, blocks_plants, blocks_village, blocks_nether_end, blocks_more, blocks_fluids,
         blocks_minerals, blocks_rest]

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


def write_tex(name, tex, kind="blocks", stats=None):
    """Writes colour (+ same file types the game ships), MERS, height map and
    the texture set that ties them together for Vibrant Visuals."""
    base = os.path.join(PACK, "textures", kind, name)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    st = (core.STATS if stats is None else stats).get(name)
    exts = st["ext"] if st else ["png"]
    img = tex.color_image()
    for ext in exts:
        im = img
        if st and len(exts) > 1:
            # the game ships two files for this texture with different
            # brightness / alpha conventions: honour each one
            pe = st["per_ext"][ext]
            ref = st["per_ext"][exts[-1]]
            k = (sum(pe["mean"]) + 1.0) / (sum(ref["mean"]) + 1.0)
            arr = np.array(img).astype(float)
            if abs(k - 1) > 0.05:
                arr[..., :3] = np.clip(arr[..., :3] * k, 0, 255)
            if pe["alpha"] == [0]:
                arr[..., 3] = 0
            elif pe["alpha"] == [255]:
                arr[..., 3] = 255
            im = Image.fromarray(arr.astype(np.uint8), "RGBA")
        im.save(base + "." + ext)
    stem = os.path.basename(name)
    tex.mers_image().save(base + "_mers.tga")
    # Height map (1-channel): black = pushed in, white = pushed out, 127 = flat.
    # Chosen over a normal map because its meaning is unambiguous in the docs.
    hm = np.clip(127.5 + (tex.height - float(tex.height.mean())) * 150.0 * tex.bump, 0, 255).astype(np.uint8)
    Image.fromarray(hm, "L").save(base + "_heightmap.png")
    ts = {"format_version": "1.21.30",
          "minecraft:texture_set": {"color": stem,
                                    "metalness_emissive_roughness_subsurface": stem + "_mers",
                                    "heightmap": stem + "_heightmap"}}
    json.dump(ts, open(base + ".texture_set.json", "w"), indent=2)


def write_atlas(out, flip, variations):
    td = {}
    for short, names in variations.items():
        td[short] = {"textures": {"variations": [{"path": "textures/blocks/" + n, "weight": 2 if i == 0 else 1}
                                                 for i, n in enumerate(names)]}}
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


def make_icon(out, size=256):
    """Isometric grass block built from our own textures."""
    top, side = out["grass_carried"].rgb, out["grass_side_carried"].rgb
    img = np.zeros((size, size, 4), np.uint8)
    cx, w, hh, sh = size / 2, size * 0.42, size * 0.21, size * 0.46
    y0 = (size - (2 * hh + sh)) / 2
    for y in range(size):
        for x in range(size):
            dx, dy = (x + 0.5 - cx) / w, (y + 0.5 - y0) / hh
            u, v = (dx + dy) / 2, (dy - dx) / 2
            if 0 <= u < 1 and 0 <= v < 1:
                img[y, x, :3] = top[int(v * 16), int(u * 16)]
                img[y, x, 3] = 255
                continue
            if -1 <= dx < 0:
                uu = dx + 1
                vv = (y + 0.5 - (y0 + hh + uu * hh)) / sh
                k = 0.82
            elif 0 <= dx < 1:
                uu = dx
                vv = (y + 0.5 - (y0 + 2 * hh - uu * hh)) / sh
                k = 0.6
            else:
                continue
            if 0 <= vv < 1:
                img[y, x, :3] = (side[int(vv * 16), int(uu * 16)] * k).astype(np.uint8)
                img[y, x, 3] = 255
    bg = np.zeros((size, size, 4), np.uint8)
    yy = np.linspace(0, 1, size)[:, None]
    bg[..., 0] = 28 + 30 * yy
    bg[..., 1] = 34 + 44 * yy
    bg[..., 2] = 58 + 60 * yy
    bg[..., 3] = 255
    a = img[..., 3:4] / 255.0
    bg[..., :3] = (img[..., :3] * a + bg[..., :3] * (1 - a)).astype(np.uint8)
    return Image.fromarray(bg, "RGBA")


def build_number():
    """A number that grows with every commit, so each build installs as an update."""
    import subprocess
    try:
        return int(subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=ROOT, capture_output=True,
                                  text=True, check=True).stdout.strip()) + 1
    except Exception:
        import time
        return int(time.time() // 60) % 100000


def stamp_version(path):
    """Write the build number into a manifest: the pack, its modules and the
    behavior pack's dependency on the resource pack all move together.
    Without a new number the game refuses to import an update over the old pack."""
    m = json.load(open(path))
    v = [1, 0, build_number()]
    m["header"]["version"] = v
    for mod in m.get("modules", []):
        mod["version"] = v
    for dep in m.get("dependencies", []):
        if "uuid" in dep:
            dep["version"] = v
    json.dump(m, open(path, "w"), indent=2, ensure_ascii=False)


def calibrate(tex, target, strength=0.65):
    """Pull an item's average colour towards the colour players know for it
    (only the average colour is used - no pixels)."""
    a = tex.alpha > 0
    if not a.any():
        return
    rgb = tex.rgb.astype(float)
    mean = rgb[a].mean(0)
    gain = np.clip((np.array(target, float) + 8) / (mean + 8), 0.55, 1.8)
    gain = 1 + (gain - 1) * strength
    tex.rgb = np.where(a[..., None], np.clip(rgb * gain, 0, 255), rgb).astype(np.uint8)


def validate(out):
    """Fails the build on anything the game would reject or mis-size."""
    problems = []
    bdir = os.path.join(PACK, "textures", "blocks")
    for name, tex in out.items():
        st = core.STATS.get(name)
        if st and [tex.w, tex.h] != st["size"]:
            problems.append(f"{name}: size {tex.w}x{tex.h} but the game expects {st['size']}")
    for d, _, fs in os.walk(PACK):
        for f in fs:
            p = os.path.join(d, f)
            if f.endswith(".json"):
                try:
                    j = json.load(open(p, encoding="utf-8"))
                except Exception as e:
                    problems.append(f"{p}: {e}")
                    continue
                if f.endswith(".texture_set.json"):
                    for layer, ref in j["minecraft:texture_set"].items():
                        if not any(os.path.exists(os.path.join(d, ref + e)) for e in (".png", ".tga")):
                            problems.append(f"{p}: missing layer {layer} -> {ref}")
    for jf, getter in (("terrain_texture.json", lambda j: [v["path"] for e in j["texture_data"].values() for v in e["textures"]["variations"]]),
                       ("flipbook_textures.json", lambda j: [e["flipbook_texture"] for e in j])):
        p = os.path.join(PACK, "textures", jf)
        if os.path.exists(p):
            for ref in getter(json.load(open(p))):
                if not any(os.path.exists(os.path.join(PACK, ref + e)) for e in (".png", ".tga")):
                    problems.append(f"{jf}: missing {ref}")
    if problems:
        print("\n".join(problems))
        raise SystemExit(f"{len(problems)} validation problem(s)")


def main():
    preview = "--preview" in sys.argv
    out, flip, variations = generate()
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    if os.path.isdir(SRC):
        shutil.copytree(SRC, PACK)
        stamp_version(os.path.join(PACK, "manifest.json"))
    else:
        os.makedirs(PACK)
    for name, tex in out.items():
        write_tex(name, tex)
    item_out = {}
    items.build(item_out)
    # dyeable items (leather armour, dyed wolf armour, firework star) are
    # coloured by the game at run time from a grey base: leave them to the game
    for name in [n for n in item_out if "tga" in items.ISTATS[n]["ext"]]:
        del item_out[name]
    tools = ("_pickaxe", "_axe", "_shovel", "_hoe", "_sword", "_spear", "_helmet", "_chestplate", "_leggings", "_boots")
    for name, tex in item_out.items():
        if not name.endswith(tools) and not name.endswith("_atlas"):     # animated dials keep their own colours
            calibrate(tex, items.ISTATS[name]["mean"])
    for name, tex in item_out.items():
        st = items.ISTATS[name]
        if [tex.w, tex.h] != st["size"]:
            raise SystemExit(f"item {name}: size {tex.w}x{tex.h} but the game expects {st['size']}")
        write_tex(name, tex, kind="items", stats={name: {"ext": st["ext"]}})
    td, fb = write_atlas(out, flip, variations)
    tdir = os.path.join(PACK, "textures")
    if td:
        json.dump({"resource_pack_name": "nabd", "texture_name": "atlas.terrain", "texture_data": td},
                  open(os.path.join(tdir, "terrain_texture.json"), "w"), indent=2)
    if fb:
        json.dump(fb, open(os.path.join(tdir, "flipbook_textures.json"), "w"), indent=2)
    # items live in a subpack so players can pick ours or the game's own
    src_items = os.path.join(PACK, "textures", "items")
    if os.path.isdir(src_items):
        dst = os.path.join(PACK, "subpacks", "nabd_items", "textures", "items")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src_items, dst)
        keep = os.path.join(PACK, "subpacks", "game_items")
        os.makedirs(keep, exist_ok=True)
        open(os.path.join(keep, "README.txt"), "w").write("Empty on purpose: with this option the game shows its own item icons.\n")
    make_icon(out).save(os.path.join(PACK, "pack_icon.png"))
    validate(out)
    print(f"{len(out)} block textures, {len(item_out)} item textures, {len(variations)} variation groups, {len(fb)} flipbooks")
    if preview:
        names = list(out)
        for i in range(0, len(names), 80):
            sheet(out, names[i:i + 80], os.path.join(PREVIEW, f"sheet_{i // 80:02d}.png"))
        inames = list(item_out)
        for i in range(0, len(inames), 120):
            sheet(item_out, inames[i:i + 120], os.path.join(PREVIEW, f"items_{i // 120:02d}.png"), scale=6, cols=15, tile=1)
    if os.path.exists(os.path.join(PACK, "manifest.json")):
        os.makedirs(DIST, exist_ok=True)
        zp = os.path.join(DIST, "Nabd.mcpack")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for d, _, fs in os.walk(PACK):
                for f in sorted(fs):
                    p = os.path.join(d, f)
                    z.write(p, os.path.relpath(p, PACK))
        print("wrote", zp, round(os.path.getsize(zp) / 1e6, 2), "MB")
        # night-sight behavior pack, and one .mcaddon that installs both packs
        bp_src = os.path.join(ROOT, "bp_src")
        bp = os.path.join(DIST, "_bp")
        if os.path.isdir(bp_src):
            if os.path.isdir(bp):
                shutil.rmtree(bp)
            shutil.copytree(bp_src, bp)
            stamp_version(os.path.join(bp, "manifest.json"))
            shutil.copy(os.path.join(PACK, "pack_icon.png"), os.path.join(bp, "pack_icon.png"))
            bz = os.path.join(DIST, "Nabd_NightSight.mcpack")
            with zipfile.ZipFile(bz, "w", zipfile.ZIP_DEFLATED) as z:
                for d, _, fs in os.walk(bp):
                    for f in sorted(fs):
                        z.write(os.path.join(d, f), os.path.relpath(os.path.join(d, f), bp))
            az = os.path.join(DIST, "Nabd.mcaddon")
            with zipfile.ZipFile(az, "w", zipfile.ZIP_DEFLATED) as z:
                for root_dir, prefix in ((PACK, "Nabd"), (bp, "Nabd_NightSight")):
                    for d, _, fs in os.walk(root_dir):
                        for f in sorted(fs):
                            z.write(os.path.join(d, f), os.path.join(prefix, os.path.relpath(os.path.join(d, f), root_dir)))
            print("wrote", bz, "and", az)


if __name__ == "__main__":
    main()
