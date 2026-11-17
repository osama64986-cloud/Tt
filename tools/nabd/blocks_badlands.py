"""Badlands family, redrawn: red sand, red and yellow sandstone (all faces) and
every terracotta colour.  Our own pixel art in the house cartoon style: bright
colour, clear shapes, a 1px bevel where a block should read as a block.

Everything tiles: noise comes from the tileable core helpers and every wave is
periodic over 16 pixels.  Only the vanilla median colour of each block is used
as a colour reference."""
import math

import numpy as np

from .core import N, Tex, fbm, make_ramp, paint_idx, rng_of, shift, vbase, white

yy, xx = np.mgrid[0:N, 0:N]
TAU = 2 * math.pi


def q(field, levels):
    """0..1 field -> integer tone 0..levels-1"""
    return np.clip(np.floor(np.clip(field, 0, 0.9999) * levels), 0, levels - 1).astype(int)


def bevel(idx, top=1, bottom=-1, rows=None):
    """lighter top row / left column, darker bottom row / right column"""
    idx = idx.copy()
    r0, r1 = rows if rows else (0, N - 1)
    idx[r0, :] += top
    idx[r0:r1 + 1, 0] += top
    idx[r1, :] += bottom
    idx[r0:r1 + 1, N - 1] += bottom
    return idx


def specks(r, idx, count, delta, sizes=(1, 1, 2), avoid=None):
    for _ in range(count):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        s = int(r.choice(sizes))
        for dy in range(s):
            for dx in range(s if s == 1 else 1 + int(r.integers(0, 2))):
                yy_, xx_ = (y + dy) % N, (x + dx) % N
                if avoid is not None and avoid[yy_, xx_]:
                    continue
                idx[yy_, xx_] += delta
    return idx


# ------------------------------------------------------------------ sand
def sand(name, base):
    """Fine grains with a few thin wind ripples (periodic), pebbles and pale quartz specks."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.32)
    g = fbm(r, ((4, 1.0), (8, 0.7)))
    wob = (fbm(r, ((2, 1.0), (4, 0.4))) - 0.5) * 2.4
    p = TAU * (xx + 2 * yy) / 16 + wob
    c = np.cos(p)
    idx = q(0.5 + (g - 0.5) * 0.6, 3) + 2              # grain 2..4
    idx[c > 0.9] += 1                                    # thin bright crest
    idx[(c < -0.9)] -= 1                                 # soft trough shadow
    idx = specks(r, idx, 4, -2, sizes=(1, 1, 2))         # pebbles
    idx = specks(r, idx, 5, +2, sizes=(1,))              # quartz glints
    hgt = 0.5 + 0.15 * c + (g - 0.5) * 0.2
    return Tex(paint_idx(idx, ramp), hgt, rough=225, bump=0.8)


# ------------------------------------------------------------------ sandstone
def strata_side(name, base):
    """Side: a smooth cap with a crisp shadow under it, then wavy rock layers of
    different tones, little erosion pits and fine grain."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.36)
    g = fbm(r, ((4, 1.0), (8, 0.5)))
    # wavy layer boundaries, periodic across the block
    def edge(row, amp, k, ph):
        return row + amp * np.sin(TAU * k * xx / 16 + ph)
    e1 = edge(7.0, 0.7, 1, r.uniform(0, TAU))
    e2 = edge(10.5, 0.8, 2, r.uniform(0, TAU))
    e3 = edge(13.5, 0.6, 1, r.uniform(0, TAU))
    layer = np.select([yy < 3, yy < e1, yy < e2, yy < e3], [0, 1, 2, 3], 4)
    tone_of = np.array([5, 3, 2, 4, 3])                 # cap light, then mid / dark / light / mid
    idx = tone_of[layer] + q(g, 3) - 1
    idx[0] += 1                                           # sunlit lip
    idx[3] = np.minimum(idx[3], 1)                        # shadow under the cap
    # chips in the cap lip
    for _ in range(3):
        x = int(r.integers(0, N))
        idx[2, x] = 1
    # a darker 1px line on top of each lower boundary gives each layer an edge
    for e in (e1, e2, e3):
        line = (yy == np.floor(e).astype(int))
        idx[line & (yy > 3)] -= 1
    idx = specks(r, idx, 5, -2, sizes=(1, 2))             # erosion pits
    hgt = 0.6 - layer * 0.06 + (g - 0.5) * 0.15
    hgt[:3] = 0.8
    return Tex(paint_idx(idx, ramp), hgt, rough=205, bump=0.9)


def stone_face(name, base, dark=0.0, cracks=0, panels=1, bev=True):
    r = rng_of(name)
    ramp = make_ramp(shift(base, dv=dark), 7, 0.32)
    g = fbm(r, ((3, 1.0), (8, 0.5)))
    idx = q(0.5 + (g - 0.5) * 0.5, 3) + 2
    idx = specks(r, idx, 4, -1)
    if bev:
        if panels == 1:
            idx = bevel(idx)
        else:
            h = N // panels
            for p in range(panels):
                idx = bevel(idx, rows=(p * h, p * h + h - 1))
    for _ in range(cracks):                               # weathered pits: a dark dot with a lit lower edge
        x, y = int(r.integers(1, 14)), int(r.integers(1, 14))
        idx[y, x] = 1
        idx[y, (x + 1) % N] = min(idx[y, (x + 1) % N], 2)
        idx[(y + 1) % N, x] = 5
    return Tex(paint_idx(idx, ramp), 0.5 + (g - 0.5) * 0.2, rough=200, bump=0.8)


def chiseled(name, base):
    """Carved face: a raised frame and an original sun emblem cut into the stone."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.34)
    g = fbm(r, ((3, 1.0), (8, 0.4)))
    idx = q(0.5 + (g - 0.5) * 0.4, 2) + 3
    idx = bevel(idx, 2, -2)
    # inner frame (raised ring of 1px at distance 2 from the edge)
    ring = ((xx == 2) | (xx == 13) | (yy == 2) | (yy == 13)) & (xx >= 2) & (xx <= 13) & (yy >= 2) & (yy <= 13)
    idx[ring] = 5
    idx[((xx == 13) | (yy == 13)) & ring] = 2
    # sun: disc + 8 rays, carved (dark) with a lit lower-right rim
    cx = cy = 7.5
    d = np.hypot(xx - cx, yy - cy)
    a = np.arctan2(yy - cy, xx - cx)
    disc = d < 2.3
    rays = (d > 3.0) & (d < 5.0) & (np.abs(((a / (TAU / 8)) % 1) - 0.5) > 0.32)
    cut = disc | rays
    idx[cut] = 1
    rim = np.zeros_like(cut)
    rim[:-1, :-1] = cut[1:, 1:] & ~cut[:-1, :-1]         # pixels just above-left of the cut: shadow edge
    idx[rim & ~ring] = np.minimum(idx[rim & ~ring], 2)
    lit = np.zeros_like(cut)
    lit[1:, 1:] = cut[:-1, :-1] & ~cut[1:, 1:]            # just below-right: catches the light
    idx[lit & ~ring] = 6
    idx[(np.abs(xx - cx) < 1) & (np.abs(yy - cy) < 1)] = 6  # bright centre
    hgt = np.where(cut, 0.3, 0.65)
    return Tex(paint_idx(idx, ramp), hgt, rough=195, bump=1.0)


# ------------------------------------------------------------------ terracotta
def terracotta(name, base):
    """Fired clay: gentle mottling, faint trowel smears, fine grit; a light top row
    and a dark bottom row, so stacked layers read like the bands of a badlands cliff."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.28)
    mott = fbm(r, ((2, 1.0), (4, 0.6)))
    smear = fbm(r, ((2, 0.5), (8, 1.0)), sx=6)
    t = 0.5 + (mott - 0.5) * 0.3 + (smear - 0.5) * 0.35
    idx = q(t, 3) + 2                                     # 2..4
    idx = specks(r, idx, 4, +1)                          # pale grit
    idx = specks(r, idx, 4, -1)                          # dark grit
    idx[0, :] += 1
    idx[N - 1, :] -= 1
    hgt = 0.55 + (smear - 0.5) * 0.15
    hgt[N - 1] = 0.4
    return Tex(paint_idx(idx, ramp), hgt, rough=195, bump=0.7)


COLORS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "silver", "cyan",
          "purple", "blue", "brown", "green", "red", "black"]


def build(out, flip, variations):
    # red sand / sand
    out["red_sand"] = sand("red_sand", shift(vbase("red_sand"), ds=0.05, dv=0.04))
    out["sand"] = sand("sand", shift(vbase("sand"), dv=0.03))
    out["nabd/sand_v1"] = sand("sand_v1", shift(vbase("sand"), dv=0.03))
    variations["flattened_sand"] = ["sand", "nabd/sand_v1"]
    # sandstone families (red and yellow share the design)
    for pre in ("red_sandstone", "sandstone"):
        b = shift(vbase(f"{pre}_normal"), ds=0.06, dv=0.03)
        out[f"{pre}_normal"] = strata_side(f"{pre}_normal", b)
        out[f"{pre}_top"] = stone_face(f"{pre}_top", shift(vbase(f"{pre}_top"), ds=0.05, dv=0.04), bev=False, cracks=2)
        out[f"{pre}_bottom"] = stone_face(f"{pre}_bottom", b, dark=-0.08, cracks=4, bev=False)
        out[f"{pre}_smooth"] = stone_face(f"{pre}_smooth", b, panels=2)
        out[f"{pre}_carved"] = chiseled(f"{pre}_carved", b)
    # terracotta, every colour
    out["hardened_clay"] = terracotta("hardened_clay", vbase("hardened_clay"))
    for c in COLORS:
        n = f"hardened_clay_stained_{c}"
        out[n] = terracotta(n, vbase(n))
