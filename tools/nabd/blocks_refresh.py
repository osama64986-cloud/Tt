"""Refresh pass: natural stones, polished stones, concrete, concrete powder,
wool, clay, mud, obsidian and the nether brick family, redrawn in the house
cartoon style - bright colour, clear shapes, depth from light and shadow.

Our own pixel art; only the vanilla median colour of each block is used as a
colour reference.  Everything tiles."""
import math

import numpy as np

from .core import N, Tex, cell_edges, fbm, make_ramp, paint_idx, rng_of, shift, vbase, voronoi

yy, xx = np.mgrid[0:N, 0:N]
TAU = 2 * math.pi


def q(field, levels):
    return np.clip(np.floor(np.clip(field, 0, 0.9999) * levels), 0, levels - 1).astype(int)


def dots(r, idx, count, delta, size=1, lit=False, shadow=False, mask=None):
    """little specks; `lit` adds a bright pixel below-right (a pit catching light),
    `shadow` a dark one above-left (a bump)"""
    for _ in range(count):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        if mask is not None and not mask[y, x]:
            continue
        for dy in range(size):
            for dx in range(size):
                idx[(y + dy) % N, (x + dx) % N] += delta
        if lit:
            idx[(y + size) % N, (x + size) % N] += 1
        if shadow:
            idx[(y - 1) % N, (x - 1) % N] -= 1
    return idx


def crack(r, idx, length, x=None, y=None):
    """a short wandering crack: dark line with a lit pixel on its lower side"""
    x = int(r.integers(0, N)) if x is None else x
    y = int(r.integers(0, N)) if y is None else y
    dx = int(r.choice([-1, 1]))
    for _ in range(length):
        idx[y % N, x % N] = 0
        idx[(y + 1) % N, x % N] = max(idx[(y + 1) % N, x % N], 4)
        if r.random() < 0.6:
            x += dx
        else:
            y += 1
    return idx


def bevel(idx, top=1, bottom=-1, r0=0, r1=N - 1, c0=0, c1=N - 1):
    idx = idx.copy()
    idx[r0, c0:c1 + 1] += top
    idx[r0:r1 + 1, c0] += top
    idx[r1, c0:c1 + 1] += bottom
    idx[r0:r1 + 1, c1] += bottom
    return idx


# ------------------------------------------------------------------ natural stones
def natural(name, base, *, levels=3, scale=((3, 1.0), (6, 0.6)), spread=0.55, cracks=2, crack_len=(3, 6),
            light=(0, 1), dark=(0, 1), pits=0, streak=0.0, swirl=0.0, contrast=0.30, rough=195, sat=None):
    """Soft blotchy stone with readable features: cracks, pale and dark flecks,
    pits, vertical grain (`streak`) or smooth swirls (`swirl`)."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast) if sat is None else make_ramp(base, 7, contrast, sat=sat)
    g = fbm(r, scale)
    if streak:
        g = g * (1 - streak) + fbm(r, ((2, 0.5), (8, 1.0)), sx=1, sy=8) * streak
    if swirl:
        p = TAU * (xx + yy) / 16 + (fbm(r, ((2, 1.0),)) - 0.5) * 6
        g = g * (1 - swirl) + (0.5 + 0.5 * np.sin(p)) * swirl
    idx = q(0.5 + (g - 0.5) * spread * 2, levels) + (3 - levels // 2)
    for _ in range(cracks):
        crack(r, idx, int(r.integers(*crack_len)))
    idx = dots(r, idx, light[0], +2, size=light[1])
    idx = dots(r, idx, dark[0], -2, size=dark[1])
    idx = dots(r, idx, pits, -2, lit=True)
    hgt = 0.5 + (g - 0.5) * 0.4
    return Tex(paint_idx(idx, ramp), hgt, rough=rough, bump=1.0)


def facets(name, base, *, count=7, keep=0.65, tone_var=1, cracks=1, light=(3, 1), dark=(2, 1), pits=0,
           contrast=0.32, edge_light=1, seam_dark=2, rough=195, sat=None):
    """Chunky rock: soft facets, each lit along its top-left edge with a shadow
    seam on its lower-right edge.  Only some seams are drawn (`keep`), so it reads
    as one rock face, not as cobblestone."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast) if sat is None else make_ramp(base, 7, contrast, sat=sat)
    ids, f1, f2, pts = voronoi(r, count)
    offs = r.choice([-1, 0, 0, 1], size=len(pts)) if tone_var else np.zeros(len(pts), int)
    g = fbm(r, ((4, 1.0), (8, 0.5)))
    idx = 3 + offs[ids] + (q(g, 3) - 1) * (r.random() < 2)
    show = fbm(r, ((2, 1.0),)) < keep + 0.2
    seam = cell_edges(ids) & show
    top_edge = ((ids != np.roll(ids, 1, 1)) | (ids != np.roll(ids, 1, 0))) & ~cell_edges(ids) & show
    idx[top_edge] += edge_light
    idx[seam] -= seam_dark
    for _ in range(cracks):
        crack(r, idx, int(r.integers(3, 6)))
    idx = dots(r, idx, light[0], +2, size=light[1])
    idx = dots(r, idx, dark[0], -2, size=dark[1])
    idx = dots(r, idx, pits, -2, lit=True)
    hgt = np.clip(0.75 - f1 / 8.0, 0.2, 0.8)
    hgt[seam] = 0.15
    return Tex(paint_idx(idx, ramp), hgt, rough=rough, bump=1.1)


def polished(name, base, *, panels=1, frame=1, contrast=0.26, rough=150, vertical=False):
    """Smooth cut stone: a calm surface with a soft light sweep and a crisp bevel."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast)
    g = fbm(r, ((2, 1.0), (4, 0.4)))
    sweep = (xx + yy) / 30.0                              # light from the top-left
    idx = q(0.55 - sweep * 0.35 + (g - 0.5) * 0.35, 2) + 3
    idx = dots(r, idx, 2, -1)
    if panels == 1:
        for f in range(frame):
            idx = bevel(idx, 1, -1, f, N - 1 - f, f, N - 1 - f)
    else:
        h = N // panels
        for p in range(panels):
            if vertical:
                idx = bevel(idx, 1, -1, 0, N - 1, p * h, p * h + h - 1)
            else:
                idx = bevel(idx, 1, -1, p * h, p * h + h - 1)
    return Tex(paint_idx(idx, ramp), 0.6 + (g - 0.5) * 0.08, rough=rough, bump=0.8)


# ------------------------------------------------------------------ dyed families
def concrete(name, base):
    """Poured and set: an almost even surface, a soft light sweep, a few pores and a neat edge."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.22)
    g = fbm(r, ((2, 1.0), (4, 0.3)))
    idx = q(0.5 + (g - 0.5) * 0.12 - (xx + yy - 15) / 60.0, 2) + 3
    idx = dots(r, idx, 4, -1)                            # air pores
    idx = bevel(idx, 1, -1)
    return Tex(paint_idx(idx, ramp), 0.6 + (g - 0.5) * 0.05, rough=160, bump=0.6)


def powder(name, base):
    """Loose powder: soft rounded clumps, each lit on its top-left, with dusty gaps."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.30)
    g = fbm(r, ((4, 1.0), (8, 0.7)))
    idx = q(g, 3) + 2
    lit = np.roll(g, 1, axis=0) < g - 0.08                # tops of the clumps
    idx[lit] += 1
    idx = dots(r, idx, 6, -1)
    idx = dots(r, idx, 5, +1)
    return Tex(paint_idx(idx, ramp), g, rough=235, bump=1.0)


def wool(name, base):
    """Knitted columns of 'V' stitches: each stitch lit on its upper half, a dark seam between columns."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.30)
    col = xx // 4
    lx = xx % 4
    ly = (yy + (col % 2) * 2) % 4                          # neighbouring columns offset by half a stitch
    v = np.where(lx < 2, ly - lx, ly - (3 - lx))           # chevron shape
    idx = np.where(v <= 0, 4, np.where(v == 1, 3, 2))
    idx[lx == 0] = np.minimum(idx[lx == 0], 3)
    g = fbm(r, ((2, 1.0), (4, 0.5)))
    idx = idx + (q(g, 2) - 1)
    idx = dots(r, idx, 3, +1)                              # stray fibres
    hgt = np.where(v <= 0, 0.7, np.where(v == 1, 0.55, 0.35))
    return Tex(paint_idx(idx, ramp), hgt, rough=240, sss=40, bump=1.0)


# ------------------------------------------------------------------ bricks
def bricks(name, base, *, mortar_dv=-0.22, cracked=0, rows=4, offset=4):
    """Rows of small bricks: dark mortar, each brick lit on its top and left edge."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.34)
    g = fbm(r, ((4, 1.0), (8, 0.5)))
    rh = N // rows
    row = yy // rh
    bx = (xx + (row % 2) * offset) % 8
    mortar = ((yy % rh) == rh - 1) | (bx == 7)
    idx = q(0.5 + (g - 0.5) * 0.5, 2) + 3
    idx[((yy % rh) == 0) & ~mortar] += 1                  # lit top edge
    idx[(bx == 0) & ~mortar] += 1                          # lit left edge
    idx[((yy % rh) == rh - 2) & ~mortar] -= 1             # shaded lower edge
    idx[mortar] = 0
    idx = dots(r, idx, 3, -1, mask=~mortar)
    for _ in range(cracked):
        crack(r, idx, int(r.integers(3, 6)))
    hgt = np.where(mortar, 0.2, 0.7 + (g - 0.5) * 0.1)
    return Tex(paint_idx(idx, ramp), hgt, rough=190, bump=1.0)


def chiseled_bricks(name, base):
    """A framed tile with an original carved diamond knot."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.34)
    g = fbm(r, ((3, 1.0),))
    idx = q(0.5 + (g - 0.5) * 0.4, 2) + 3
    idx = bevel(idx, 2, -2)
    idx = bevel(idx, -1, 1, 2, 13, 2, 13)                 # sunken inner frame
    d = np.abs(xx - 7.5) + np.abs(yy - 7.5)
    knot = (np.abs(d - 4.5) < 0.6) | (np.abs(d - 1.5) < 0.6)
    idx[knot] = 1
    below = np.zeros_like(knot)
    below[1:, 1:] = knot[:-1, :-1] & ~knot[1:, 1:]
    idx[below] = 6
    return Tex(paint_idx(idx, ramp), np.where(knot, 0.3, 0.65), rough=185, bump=1.0)


COLORS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "silver", "cyan",
          "purple", "blue", "brown", "green", "red", "black"]


def stone_set(out, variations):
    """stone and its variants (called early, before the ores are painted on top)"""
    b = shift(vbase("stone"), dv=0.05)
    kw = dict(count=6, keep=0.35, cracks=1, light=(4, 1), dark=(3, 1), pits=1, contrast=0.32, seam_dark=1, edge_light=0)
    out["stone"] = facets("stone", b, **kw)
    out["nabd/stone_v1"] = facets("stone_v1", b, **kw)
    out["nabd/stone_v2"] = facets("stone_v2", b, **kw)
    variations["flattened_stone"] = ["stone", "nabd/stone_v1", "nabd/stone_v2"]


def slate(name, base, *, count=9, stretch=0.42, contrast=0.55, top=False):
    """Deepslate: stacked slate plates.  Plates are long and upright on the side
    (short and squarish on the top), each with a lit upper edge, a dark seam
    below it and a fine grain running along it."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast, sat=1.15)
    pts = np.stack([r.random(count) * N, r.random(count) * N], 1)
    dx = np.abs(xx[..., None] + 0.5 - pts[:, 0])
    dy = np.abs(yy[..., None] + 0.5 - pts[:, 1])
    dx = np.minimum(dx, N - dx)
    dy = np.minimum(dy, N - dy)
    sy = 1.0 if top else stretch                      # squash the vertical distance: tall plates
    d = np.hypot(dx, dy * sy)
    order = np.argsort(d, axis=-1)
    ids = order[..., 0]
    ds = np.sort(d, axis=-1)
    edge = ds[..., 1] - ds[..., 0]
    off = r.choice([-1, 0, 0, 1], size=count)
    grain = fbm(r, ((2, 0.5), (8, 1.0)), sx=1, sy=1 if top else 6)
    idx = 3 + off[ids] + (grain > 0.68) - (grain < 0.25)
    seam = cell_edges(ids)
    lit = ((ids != np.roll(ids, 1, 0)) | (ids != np.roll(ids, 1, 1))) & ~seam
    idx[lit & (edge > 0.4)] += 2
    idx[seam] = 0
    idx = dots(r, idx, 4, +2)
    hgt = np.clip(edge / 2.5, 0, 1) * 0.7 + 0.1
    hgt[seam] = 0.05
    return Tex(paint_idx(idx, ramp), hgt, rough=190, bump=1.1)


def strata(name, base, *, top=False, contrast=0.80):
    """Deepslate: flat lens-shaped slabs laid in staggered rows over a dark bed.
    Each slab is drawn on its own as a small pixel ellipse: a lit rim along its top,
    a light upper half, a shaded lower edge and darker tapered ends, so it reads as
    a stone lying in the wall.  Where slabs do not meet, the dark blue-grey bed
    shows through.  The top face is the end of the stack: rounder slabs, lit from
    their middle, packed loosely instead of in rows."""
    if top:
        return strata_top(name, base, contrast=contrast)
    r = rng_of(name)
    r2 = rng_of(name + "_fine")                            # extra touches, without moving the layout
    ramp = make_ramp(base, 8, contrast, sat=1.0, warm=0.0)
    idx = np.full((N, N), 1)
    bed = fbm(r, ((4, 1.0), (8, 0.5)), sx=3, sy=1)
    idx = idx + (bed > 0.7) - (bed < 0.25)
    slab = np.full((N, N), -1)
    rows = 5
    k = 0
    for row in range(rows):
        cy = (row + 0.5) * N / rows + r.normal(0, 0.35)
        x = r.random() * N
        end = x + N
        while x < end - 2:
            w = float(r.integers(6, 11))
            w = min(w, end - x + 0.5)
            h = float(r.choice([3.0, 3.6, 4.2]))
            a, b = w / 2, h / 2
            cx = x + a
            tone = 4 + int(r.choice([-1, 0, 0, 1]))
            cy_s = cy + r2.normal(0, 0.25)                 # a hair of unevenness in the row
            dx = (xx + 0.5 - cx + N / 2) % N - N / 2
            dy = (yy + 0.5 - cy_s + N / 2) % N - N / 2
            m = (dx / a) ** 2 + (dy / b) ** 2 <= 1.0
            rel_y = dy / b
            rel_x = np.abs(dx / a)
            soft = r2.random() < 0.2                       # some slabs are flatter, less banded
            t = np.full((N, N), tone) + (rel_y < -0.3) - ((rel_y > 0.45) & (not soft)) - (rel_x > 0.75)
            idx[m] = t[m]
            slab[m] = k
            k += 1
            x += w + float(r.choice([0, 0, 1]))
    top_edge = (slab >= 0) & (np.roll(slab, 1, 0) != slab)
    bot_edge = (slab >= 0) & (np.roll(slab, -1, 0) != slab)
    side_edge = (slab >= 0) & (np.roll(slab, -1, 1) != slab) & (np.roll(slab, -1, 1) >= 0)
    idx[top_edge] += 1
    idx[bot_edge] -= 1
    idx[side_edge & ~top_edge & (r2.random((N, N)) < 0.4)] -= 1   # now and then a soft joint where two slabs touch
    grain = fbm(r, ((4, 0.6), (16, 1.0)), sx=6, sy=1)
    inside = slab >= 0
    idx = idx + ((grain > 0.8) & inside) - ((grain < 0.16) & inside)
    speck = r2.random((N, N))
    idx = idx + ((speck > 0.95) & inside)                  # a light sprinkle of grit
    rgb = paint_idx(idx, ramp).astype(float)
    cool = ~inside | (idx <= 1)
    rgb[cool, 2] += 10                                     # the bed and the deep shadows lean blue
    rgb[cool, 0] -= 3
    for _ in range(4):                                     # mica flecks
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        if inside[y, x]:
            rgb[y, x] = ramp[-1]
    hgt = np.where(inside, 0.4 + 0.1 * (idx - 3), 0.08)
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.clip(hgt, 0, 1), rough=190, bump=1.1)


def strata_top(name, base, contrast=0.80):
    """Top of deepslate: the cut ends of the slabs - rounded plates of mixed size,
    packed loosely with no rows, each lit on its upper-left and darker towards its
    lower-right, with the cool dark bed between them."""
    r = rng_of(name + "_v2")
    ramp = make_ramp(base, 8, contrast, sat=1.0, warm=0.0)
    idx = np.full((N, N), 1)
    bed = fbm(r, ((4, 1.0), (8, 0.5)))
    idx = idx + (bed > 0.7) - (bed < 0.25)
    slab = np.full((N, N), -1)
    k = 0
    placed = []
    tries = 0
    while k < 14 and tries < 600:
        tries += 1
        w = float(r.choice([4.2, 5.0, 5.8, 6.6]))
        h = float(r.choice([3.6, 4.2, 5.0]))
        cx, cy = r.random() * N, r.random() * N
        ok = True
        for (px, py, pw, ph) in placed:                   # keep plates from piling up
            ddx = min(abs(cx - px), N - abs(cx - px))
            ddy = min(abs(cy - py), N - abs(cy - py))
            if (ddx / ((w + pw) / 2 * 0.82)) ** 2 + (ddy / ((h + ph) / 2 * 0.82)) ** 2 < 1:
                ok = False
                break
        if not ok:
            continue
        placed.append((cx, cy, w, h))
        a, b = w / 2, h / 2
        tone = 4 + int(r.choice([-1, 0, 0, 1, 1]))
        dx = (xx + 0.5 - cx + N / 2) % N - N / 2
        dy = (yy + 0.5 - cy + N / 2) % N - N / 2
        m = (dx / a) ** 2 + (dy / b) ** 2 <= 1.0
        diag = (dx / a + dy / b) / 2                       # -1 upper-left .. 1 lower-right
        t = np.full((N, N), tone) + (diag < -0.25) - (diag > 0.35)
        idx[m] = t[m]
        slab[m] = k
        k += 1
    inside = slab >= 0
    ul = inside & ((np.roll(slab, 1, 0) != slab) | (np.roll(slab, 1, 1) != slab))
    lr = inside & ((np.roll(slab, -1, 0) != slab) | (np.roll(slab, -1, 1) != slab))
    idx[ul & ~lr] += 1
    idx[lr & ~ul] -= 1
    grain = fbm(r, ((4, 0.6), (16, 1.0)), sx=2, sy=2)
    idx = idx + ((grain > 0.8) & inside) - ((grain < 0.16) & inside)
    rgb = paint_idx(idx, ramp).astype(float)
    cool = ~inside | (idx <= 1)
    rgb[cool, 2] += 10
    rgb[cool, 0] -= 3
    for _ in range(3):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        if inside[y, x]:
            rgb[y, x] = ramp[-1]
    hgt = np.where(inside, 0.4 + 0.1 * (idx - 3), 0.08)
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.clip(hgt, 0, 1), rough=190, bump=1.1)


def strata_top_mixed(name, base, contrast=0.80):
    """Top of deepslate, option B: the same lens slabs as the side, seen from above -
    some lying east-west, some north-south, packed loosely, each lit along its top
    and left rims, the cool dark bed between."""
    r = rng_of(name + "_mixed")
    ramp = make_ramp(base, 8, contrast, sat=1.0, warm=0.0)
    idx = np.full((N, N), 1)
    bed = fbm(r, ((4, 1.0), (8, 0.5)))
    idx = idx + (bed > 0.7) - (bed < 0.25)
    slab = np.full((N, N), -1)
    placed, k, tries = [], 0, 0
    while k < 16 and tries < 900:
        tries += 1
        long_, short = float(r.choice([5.0, 6.0, 7.0, 8.0])), float(r.choice([3.0, 3.6, 4.2]))
        w, h = (long_, short) if r.random() < 0.55 else (short, long_)
        cx, cy = r.random() * N, r.random() * N
        bad = False
        for (px, py, pw, ph) in placed:
            ddx = min(abs(cx - px), N - abs(cx - px))
            ddy = min(abs(cy - py), N - abs(cy - py))
            if (ddx / ((w + pw) / 2 * 0.9)) ** 2 + (ddy / ((h + ph) / 2 * 0.9)) ** 2 < 1:
                bad = True
                break
        if bad:
            continue
        placed.append((cx, cy, w, h))
        a, b = w / 2, h / 2
        tone = 4 + int(r.choice([-1, 0, 0, 1]))
        dx = (xx + 0.5 - cx + N / 2) % N - N / 2
        dy = (yy + 0.5 - cy + N / 2) % N - N / 2
        m = (dx / a) ** 2 + (dy / b) ** 2 <= 1.0
        t = np.full((N, N), tone) + ((dy / b) < -0.3) - ((dy / b) > 0.5)
        idx[m] = t[m]
        slab[m] = k
        k += 1
    inside = slab >= 0
    ul = inside & ((np.roll(slab, 1, 0) != slab) | (np.roll(slab, 1, 1) != slab))
    lr = inside & ((np.roll(slab, -1, 0) != slab) | (np.roll(slab, -1, 1) != slab))
    idx[ul & ~lr] += 1
    idx[lr & ~ul] -= 1
    grain = fbm(r, ((4, 0.6), (16, 1.0)), sx=2, sy=2)
    idx = idx + ((grain > 0.8) & inside) - ((grain < 0.16) & inside)
    rgb = paint_idx(idx, ramp).astype(float)
    cool = ~inside | (idx <= 1)
    rgb[cool, 2] += 10
    rgb[cool, 0] -= 3
    for _ in range(3):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        if inside[y, x]:
            rgb[y, x] = ramp[-1]
    hgt = np.where(inside, 0.4 + 0.1 * (idx - 3), 0.08)
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.clip(hgt, 0, 1), rough=190, bump=1.1)


def strata_top_rows(name, base, contrast=0.80):
    """Top of deepslate, option C: the side's slab rows with shorter, taller slabs
    (the look from the earlier favoured sheet), calmer than the side."""
    r = rng_of(name)
    ramp = make_ramp(base, 8, contrast, sat=1.0, warm=0.0)
    idx = np.full((N, N), 1)
    bed = fbm(r, ((4, 1.0), (8, 0.5)), sx=3, sy=1)
    idx = idx + (bed > 0.7) - (bed < 0.25)
    slab = np.full((N, N), -1)
    k = 0
    for row in range(4):
        cy = (row + 0.5) * N / 4 + r.normal(0, 0.35)
        x = r.random() * N
        end = x + N
        while x < end - 2:
            w = min(float(r.integers(4, 7)), end - x + 0.5)
            h = float(r.choice([3.6, 4.2, 5.0]))
            a, b = w / 2, h / 2
            tone = 4 + int(r.choice([-1, 0, 0, 1]))
            dx = (xx + 0.5 - (x + a) + N / 2) % N - N / 2
            dy = (yy + 0.5 - cy + N / 2) % N - N / 2
            m = (dx / a) ** 2 + (dy / b) ** 2 <= 1.0
            rel_y, rel_x = dy / b, np.abs(dx / a)
            t = np.full((N, N), tone) + (rel_y < -0.3) - (rel_y > 0.45) - (rel_x > 0.75)
            idx[m] = t[m]
            slab[m] = k
            k += 1
            x += w + float(r.choice([0, 0, 1]))
    inside = slab >= 0
    idx[inside & (np.roll(slab, 1, 0) != slab)] += 1
    idx[inside & (np.roll(slab, -1, 0) != slab)] -= 1
    grain = fbm(r, ((4, 0.6), (16, 1.0)), sx=2, sy=1)
    idx = idx + ((grain > 0.8) & inside) - ((grain < 0.16) & inside)
    rgb = paint_idx(idx, ramp).astype(float)
    cool = ~inside | (idx <= 1)
    rgb[cool, 2] += 10
    rgb[cool, 0] -= 3
    for _ in range(4):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        if inside[y, x]:
            rgb[y, x] = ramp[-1]
    hgt = np.where(inside, 0.4 + 0.1 * (idx - 3), 0.08)
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.clip(hgt, 0, 1), rough=190, bump=1.1)


def bedrock(name, base):
    """Bedrock: a jumble of broken rock chips in strong light and dark - pale grey
    chips, near-black chips and everything between, packed tight, each chip lit on
    its top-left edge with a hard black crack on its lower-right.  Nothing like the
    calm layers of deepslate."""
    r = rng_of(name)
    ramp = make_ramp(base, 8, 0.95, sat=1.0, warm=0.0)
    pts = r.random((30, 2)) * N
    ddx = np.abs(xx[..., None] + 0.5 - pts[:, 0])
    ddy = np.abs(yy[..., None] + 0.5 - pts[:, 1])
    ddx = np.minimum(ddx, N - ddx)
    ddy = np.minimum(ddy, N - ddy)
    d = np.hypot(ddx * 0.55, ddy)                          # chips lie flat, wider than tall
    ids = np.argmin(d, axis=-1)
    ds = np.sort(d, axis=-1)
    edge = ds[..., 1] - ds[..., 0]
    n = len(pts)
    tone = r.choice([1, 2, 3, 4, 4, 5, 5, 6], size=n)
    idx = tone[ids].copy()
    up = (np.roll(ids, 1, 0) != ids) | (np.roll(ids, 1, 1) != ids)
    down = (np.roll(ids, -1, 0) != ids) | (np.roll(ids, -1, 1) != ids)
    idx[up] += 1
    idx[down & (r.random((N, N)) < 0.4)] = 0
    w = r.random((N, N))
    idx = idx + (w > 0.9) - (w < 0.1)
    rgb = paint_idx(idx, ramp)
    hgt = np.clip(edge / 2.0, 0, 1) * 0.5 + tone[ids] / 14.0
    hgt[idx <= 0] = 0.0
    return Tex(rgb, hgt, rough=210, bump=1.3)


def deepslate_set(out):
    b = shift(vbase("deepslate/deepslate"), dv=-0.01, ds=0.02)       # close to the game's own tone
    out["deepslate/deepslate"] = strata("deepslate", b)
    out["deepslate/deepslate_top"] = strata("deepslate_top", b, top=True)


def build(out, flip, variations):
    # natural stones
    out["stone_granite"] = natural("granite", shift(vbase("stone_granite"), ds=0.06, dv=0.04), cracks=0, spread=0.7,
                                   light=(10, 1), dark=(9, 1), contrast=0.38)
    out["stone_diorite"] = natural("diorite", shift(vbase("stone_diorite"), dv=0.02), cracks=0, spread=0.6,
                                   light=(4, 1), dark=(14, 1), contrast=0.34)
    out["stone_andesite"] = facets("andesite", shift(vbase("stone_andesite"), dv=0.04), count=8, keep=0.3, cracks=0, seam_dark=1, edge_light=0,
                                   light=(7, 1), dark=(2, 1), contrast=0.32)
    out["calcite"] = facets("calcite", shift(vbase("calcite"), dv=0.02), count=5, keep=0.55, cracks=0,
                            light=(2, 1), dark=(4, 1), contrast=0.22)
    out["tuff"] = facets("tuff", shift(vbase("tuff"), ds=0.05, dv=0.05), count=8, keep=0.5, cracks=0, pits=8,
                         light=(3, 1), dark=(0, 1), contrast=0.32)
    out["smooth_basalt"] = natural("smooth_basalt", shift(vbase("smooth_basalt"), dv=0.06), cracks=0, swirl=0.25,
                                   spread=0.7, light=(4, 1), dark=(3, 1), contrast=0.36)
    out["clay"] = natural("clay", shift(vbase("clay"), ds=0.05, dv=0.04), cracks=0, levels=2, spread=0.45,
                          light=(5, 1), dark=(3, 1), contrast=0.22, rough=140)
    out["mud"] = natural("mud", shift(vbase("mud"), dv=0.05), cracks=0, levels=3, light=(6, 1), dark=(3, 2),
                         contrast=0.32, rough=60)
    out["obsidian"] = facets("obsidian", (46, 28, 78), count=7, keep=0.8, cracks=0,
                             light=(4, 1), dark=(0, 1), edge_light=2, contrast=0.55, rough=40)
    # polished / cut stones
    out["stone_granite_smooth"] = polished("granite_smooth", shift(vbase("stone_granite_smooth"), ds=0.05, dv=0.04))
    out["stone_diorite_smooth"] = polished("diorite_smooth", shift(vbase("stone_diorite_smooth"), dv=0.02))
    out["stone_andesite_smooth"] = polished("andesite_smooth", shift(vbase("stone_andesite_smooth"), dv=0.04))
    out["polished_tuff"] = polished("polished_tuff", shift(vbase("polished_tuff"), dv=0.04), frame=2)
    out["deepslate/polished_deepslate"] = polished("polished_deepslate", shift(vbase("deepslate/deepslate"), dv=-0.02, ds=0.02), contrast=0.40)
    out["stone_slab_top"] = polished("smooth_stone_top", shift(vbase("stone_slab_top"), dv=0.04), frame=2)
    out["stone_slab_side"] = polished("smooth_stone_side", shift(vbase("stone_slab_side"), dv=0.04), panels=2)
    # dyed families
    for c in COLORS:
        cb = vbase(f"concrete_{c}")
        out[f"concrete_{c}"] = concrete(f"concrete_{c}", shift(cb, dv=0.08) if c in ("black", "gray") else cb)
        out[f"concrete_powder_{c}"] = powder(f"concrete_powder_{c}", vbase(f"concrete_powder_{c}"))
        out[f"wool_colored_{c}"] = wool(f"wool_colored_{c}", vbase(f"wool_colored_{c}"))
    # nether bricks
    nb = shift(vbase("nether_brick"), dv=0.1, ds=0.06)
    out["nether_brick"] = bricks("nether_brick", nb)
    out["cracked_nether_bricks"] = bricks("cracked_nether_bricks", nb, cracked=4)
    out["chiseled_nether_bricks"] = chiseled_bricks("chiseled_nether_bricks", nb)
    out["red_nether_brick"] = bricks("red_nether_brick", shift(vbase("red_nether_brick"), dv=0.08, ds=0.04))
