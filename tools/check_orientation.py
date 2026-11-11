#!/usr/bin/env python3
"""Compares the *direction* of every painted texture with the game's own:
which way stripes run, whether the picture is top- or bottom-heavy, and where
the opaque pixels of a sprite sit.  Only these neutral measurements are
taken from the reference pack - no pixels.

    python3 tools/check_orientation.py /path/to/bedrock-samples/resource_pack
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAN = os.path.join(sys.argv[1], "textures")
OURS = os.path.join(ROOT, "pack", "textures")


def load(base):
    for e in (".tga", ".png"):
        if os.path.exists(base + e):
            a = np.array(Image.open(base + e).convert("RGBA")).astype(float)
            w = a.shape[1]
            return a[:w] if a.shape[0] > w else a          # first frame of a strip
    return None


def measure(a):
    al = a[..., 3] > 0
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    cover = al.mean()
    out = {"cover": cover}
    if cover < 0.97 and al.any():                            # sprite: where does it sit?
        ys, xs = np.nonzero(al)
        h, w = al.shape
        out["cy"], out["cx"] = ys.mean() / h, xs.mean() / w
        out["top"], out["bottom"] = al[: h // 4].mean(), al[-(h // 4):].mean()
        out["left"], out["right"] = al[:, : w // 4].mean(), al[:, -(w // 4):].mean()
    l = np.where(al, lum, lum[al].mean() if al.any() else 0)
    rv, cv = l.mean(1).var(), l.mean(0).var()                # stripes: rows vs columns
    out["stripe"] = "H" if rv > 2.2 * cv + 4 else ("V" if cv > 2.2 * rv + 4 else "-")
    out["strength"] = max(rv, cv)
    h = l.shape[0]
    out["tb"] = l[: h // 2].mean() - l[h // 2:].mean()      # top brighter (+) or bottom brighter (-)
    return out


issues = []
for kind in ("blocks",):
    for d, _, fs in os.walk(os.path.join(OURS, kind)):
        for f in fs:
            if not f.endswith(".texture_set.json"):
                continue
            rel = os.path.relpath(os.path.join(d, f[:-17]), os.path.join(OURS, kind))
            if rel.startswith("nabd/"):
                continue
            a, b = load(os.path.join(VAN, kind, rel)), load(os.path.join(OURS, kind, rel))
            if a is None or b is None or a.shape != b.shape:
                continue
            va, ob = measure(a), measure(b)
            why = []
            if va["stripe"] != "-" and ob["stripe"] != "-" and va["stripe"] != ob["stripe"] and va["strength"] > 30:
                why.append(f"stripes run {va['stripe']} in the game but {ob['stripe']} in ours")
            if "cy" in va and "cy" in ob:
                if abs(va["cy"] - ob["cy"]) > 0.2:
                    why.append(f"sprite sits at y={va['cy']:.2f} in the game but y={ob['cy']:.2f} in ours")
                if abs(va["cx"] - ob["cx"]) > 0.2:
                    why.append(f"sprite sits at x={va['cx']:.2f} in the game but x={ob['cx']:.2f} in ours")
                for side in ("top", "bottom", "left", "right"):
                    if va[side] > 0.25 and ob[side] < 0.03:
                        why.append(f"the game's picture touches the {side} edge, ours does not")
                    if va[side] < 0.01 and ob[side] > 0.3:
                        why.append(f"ours fills the {side} edge, the game's stays clear of it")
            if abs(va["tb"]) > 14 and abs(ob["tb"]) > 8 and np.sign(va["tb"]) != np.sign(ob["tb"]):
                why.append("light/dark half is upside down compared with the game (%+.0f vs %+.0f)" % (va["tb"], ob["tb"]))
            if why:
                issues.append((rel, why))
for rel, why in sorted(issues):
    print(f"{rel}: " + "; ".join(why))
print(len(issues), "textures to look at")
