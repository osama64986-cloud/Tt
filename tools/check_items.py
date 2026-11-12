#!/usr/bin/env python3
"""Flags item icons that players may not recognise.  For each item it compares
our icon with the game's using three neutral numbers only: how much of the
same area the two silhouettes cover, the dominant colour, and brightness.

    python3 tools/check_items.py /path/to/bedrock-samples/resource_pack
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAN = os.path.join(sys.argv[1], "textures", "items")
OURS = os.path.join(ROOT, "pack", "subpacks", "nabd_items", "textures", "items")


def load(base):
    for e in (".png", ".tga"):
        if os.path.exists(base + e):
            return np.array(Image.open(base + e).convert("RGBA")).astype(float)


def dominant(a):
    m = a[..., 3] > 0
    px = a[..., :3][m]
    if len(px) == 0:
        return None
    s = px.max(1) - px.min(1)
    sel = px[s >= np.percentile(s, 60)]                       # most colourful 40 %
    c = sel.mean(0)
    return colorsys.rgb_to_hsv(*(c / 255))


rows = []
for d, _, fs in os.walk(OURS):
    for f in fs:
        if not f.endswith(".texture_set.json"):
            continue
        rel = os.path.relpath(os.path.join(d, f[:-17]), OURS)
        a, b = load(os.path.join(VAN, rel)), load(os.path.join(OURS, rel))
        if a is None or b is None or a.shape != b.shape:
            continue
        ma, mb = a[..., 3] > 0, b[..., 3] > 0
        iou = (ma & mb).sum() / max(1, (ma | mb).sum())
        la = (a[..., :3][ma] @ [0.299, 0.587, 0.114]).mean() if ma.any() else 0
        lb = (b[..., :3][mb] @ [0.299, 0.587, 0.114]).mean() if mb.any() else 0
        da, db = dominant(a), dominant(b)
        dh = 0
        if da and db and da[1] > 0.18 and db[1] > 0.18:
            dh = abs(((da[0] - db[0] + 0.5) % 1) - 0.5) * 360
        sat_gap = (da[1] - db[1]) if da and db else 0
        rows.append((rel, iou, la - lb, dh, sat_gap))
flag = [r for r in rows if r[1] < 0.42 or abs(r[2]) > 28 or r[3] > 30 or abs(r[4]) > 0.3]
for rel, iou, dl, dh, ds in sorted(flag, key=lambda r: r[1]):
    why = []
    if iou < 0.42:
        why.append(f"silhouette overlap {iou:.2f}")
    if abs(dl) > 28:
        why.append(f"{'darker' if dl > 0 else 'brighter'} than the game by {abs(dl):.0f}")
    if dh > 30:
        why.append(f"hue off by {dh:.0f} deg")
    if abs(ds) > 0.3:
        why.append(f"{'greyer' if ds > 0 else 'more saturated'} than the game")
    print(f"{rel}: " + "; ".join(why))
print(len(flag), "of", len(rows), "items to look at")
