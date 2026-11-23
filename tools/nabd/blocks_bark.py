"""Log sides redrawn as even bark plates.

The old bark scattered its strokes at random, so one half of a log could be busy
and the other half almost bare.  Here the whole face is laid out on purpose:
deep furrows at fairly even spacing across the full width, the bark between
them broken into plates by short cross-cracks, each plate lit along one edge
and shaded along the other, with a fine grain inside.  Every log keeps the
grain direction of the game's own texture (some files are stored turned on
their side).  Birch keeps its pale bark with evenly spread dark marks."""
import os

import numpy as np
from PIL import Image

from .core import N, Tex, fbm, make_ramp, paint_idx, rng_of, shift, vbase

VAN = "/home/user/mojang/bedrock-samples/resource_pack/textures/blocks/"


def grain_is_horizontal(name):
    for ext in (".png", ".tga"):
        if os.path.exists(VAN + name + ext):
            a = np.array(Image.open(VAN + name + ext).convert("L")).astype(float)[:N]
            return np.abs(np.diff(a, axis=0)).mean() > np.abs(np.diff(a, axis=1)).mean()
    return False


def widths(r, total, choices):
    out = []
    while sum(out) < total:
        out.append(int(r.choice(choices)))
    over = sum(out) - total
    out[-1] -= over
    if out[-1] < min(choices) and len(out) > 1:     # fold a too-thin last plate into its neighbour
        v = out.pop()
        out[-1] += v
    if out[-1] <= 0:
        out.pop()
    return out


def bark_plates(name, ramp, plate=(2, 3, 3, 4), seg=(6, 8, 10, 12, 16), furrow_dark=0, cracks=False, sway=False):
    """Vertical layout (transpose for logs stored on their side).  ramp: 6 tones."""
    r = rng_of(name + "_plates")
    idx = np.zeros((N, N), int)
    x0 = int(r.integers(0, N))
    x = x0
    for w in widths(r, N, plate):
        cols = [(x + k) % N for k in range(w)]
        furrow = cols[-1]                            # the last column of each plate is the furrow
        body = cols[:-1]
        y = int(r.integers(0, N))
        for L in widths(r, N, seg):
            tone = 3 + int(r.choice([-1, 0, 0, 0, 1]))
            rows = [(y + k) % N for k in range(L)]
            for yy in rows:
                for j, cx in enumerate(body):
                    t = tone
                    if j == 0:
                        t += 1                       # lit edge
                    elif j == len(body) - 1 and len(body) > 1:
                        t -= 1                       # shaded edge
                    idx[yy, cx] = t
            if cracks:                               # a short cross-crack ends the plate
                cy = rows[-1]
                for cx in body:
                    idx[cy, cx] = max(1, idx[cy, cx] - 2)
            y = (y + L) % N
        for yy in range(N):
            idx[yy, furrow] = furrow_dark + (1 if r.random() < 0.18 else 0)
        x = (x + w) % N
    # a gentle sway: each row slides sideways by up to a pixel, so furrows wander
    ph = r.uniform(0, 2 * np.pi)
    for yy in (range(N) if sway else []):
        sft = int(np.round(0.9 * np.sin(2 * np.pi * yy / N + ph)))
        idx[yy] = np.roll(idx[yy], sft)
    g = fbm(r, ((2, 1.0), (16, 0.6)), sx=1, sy=6)
    idx = idx + ((g > 0.8) & (idx >= 2)) - ((g < 0.15) & (idx >= 2))
    hgt = np.clip(0.2 + 0.15 * idx, 0, 1)
    return paint_idx(np.clip(idx, 0, len(ramp) - 1), ramp), hgt


def birch_bark(name):
    """Pale bark with soft vertical shading and dark lenticel marks spread
    evenly over the whole face (rows every three or four pixels, staggered)."""
    r = rng_of(name + "_birch")
    pale = make_ramp((232, 230, 222), 5, 0.16)
    dark = [(40, 38, 36), (70, 66, 60), (104, 98, 88)]
    g = fbm(r, ((4, 1.0), (16, 0.4)), sx=1, sy=6)
    idx = np.clip(2 + (g > 0.62) - (g < 0.3), 0, 4)
    rgb = paint_idx(idx, pale).astype(float)
    hgt = np.full((N, N), 0.6)
    y = int(r.integers(0, 3))
    row = 0
    while y < N:
        x = (row * 7 + int(r.integers(0, 6))) % N
        n_marks = int(r.choice([1, 1, 2]))
        for _ in range(n_marks):
            ln = int(r.choice([2, 3, 4, 5]))
            for k in range(ln):
                cx = (x + k) % N
                rgb[y, cx] = dark[0] if 0 < k < ln - 1 else dark[1]
                hgt[y, cx] = 0.2
                if 0 < k < ln - 1 and r.random() < 0.45:
                    rgb[(y + 1) % N, cx] = dark[1]      # marks are two pixels deep in the middle
                elif r.random() < 0.3:
                    rgb[(y + 1) % N, cx] = dark[2]
            x = (x + ln + int(r.integers(3, 6))) % N
        y += int(r.choice([3, 4, 4]))
        row += 1
    return rgb, hgt


def detail_balance(rgb):
    """how evenly the detail is spread: compare the busiest and calmest quarter"""
    l = rgb.astype(float) @ [0.3, 0.59, 0.11]
    e = np.abs(np.diff(l, axis=1, append=l[:, :1])) + np.abs(np.diff(l, axis=0, append=l[:1]))
    q = [e[:8, :8].mean(), e[:8, 8:].mean(), e[8:, :8].mean(), e[8:, 8:].mean(),
         e[:, :8].mean(), e[:, 8:].mean()]
    return max(q) / max(1e-6, min(q)), e.mean()


def even_oak():
    """The oak bark in its original style (same painter, same tones, same number
    of ridges), with the layout picked so both halves carry the same amount of
    detail - no busy half next to a bare one."""
    from . import painters as P
    from .core import vramp
    br = vramp("log_oak", 5, contrast=0.34)
    ref = P.bark("log_oak", br, ridges=8)
    _, ref_e = detail_balance(ref.rgb)
    best = None
    for k in range(400):
        t = P.bark(f"log_oak_even{k}", br, ridges=8)
        bal, e = detail_balance(t.rgb)
        score = bal + 2.0 * abs(e - ref_e) / ref_e
        if best is None or score < best[0]:
            best = (score, t)
    return best[1]


BARK_CONTRAST = 0.40      # a touch crisper than the original 0.34: same drawing, clearer ridges

OTHER_LOGS = {"spruce": ("log_spruce", 6), "jungle": ("log_jungle", 10), "acacia": ("log_acacia", 7),
              "dark_oak": ("log_big_oak", 6), "cherry": ("cherry_log_side", 10), "mangrove": ("mangrove_log_side", 9),
              "pale_oak": ("pale_oak_log_side", 7), "poplar": ("poplar_log_side", 9)}


def build(out, flip, variations):
    from . import painters as P
    from .core import STATS, vramp
    # keep each log's own drawing and direction exactly; only make the ridges a touch clearer
    for key, (nm, ridges) in OTHER_LOGS.items():
        if nm in out:
            t = out[nm]
            rgb = t.rgb.astype(float)
            mean = rgb.reshape(-1, 3).mean(0)
            t.rgb = np.clip(mean + (rgb - mean) * 1.18, 0, 255).astype(np.uint8)
    oak = even_oak()
    rgb = oak.rgb.astype(float)
    mean = rgb.reshape(-1, 3).mean(0)
    oak.rgb = np.clip(mean + (rgb - mean) * 1.18, 0, 255).astype(np.uint8)
    out["log_oak"] = oak
    rgb, hgt = birch_bark("log_birch")
    out["log_birch"] = Tex(np.clip(rgb, 0, 255).astype(np.uint8), hgt, rough=210, bump=1.1)
