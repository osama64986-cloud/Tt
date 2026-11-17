"""Third refresh pass: the nether stones (netherrack, soul sand and soil,
blackstone and basalt families), end stone, the quartz family, amethyst,
sculk, snow, stone bricks and clay bricks.

Same house style as the other refresh passes: bright, readable shapes, light
from the top-left, crisp but not heavy outlines.  Our own pixel art; vanilla
is used for colour references and sizes only."""
import math

import numpy as np

from .blocks_refresh import bevel, chiseled_bricks, crack, dots, facets, natural, polished, q
from .core import N, Tex, fbm, make_ramp, paint_idx, rng_of, shift, stack_frames, vbase

yy, xx = np.mgrid[0:N, 0:N]
TAU = 2 * math.pi


def brick_wall(name, base, *, rows=2, width=16, mortar=None, light_mortar=False, cracked=0, moss=None, contrast=0.34):
    """Bricks of any size: mortar lines, each brick lit along its top and left edge and
    shaded along its bottom, a little wear on the faces."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast)
    g = fbm(r, ((4, 1.0), (8, 0.5)))
    rh = N // rows
    row = yy // rh
    bx = (xx + (row % 2) * (width // 2)) % width
    is_m = ((yy % rh) == rh - 1) | (bx == width - 1)
    brick_id = row * 16 + ((xx + (row % 2) * (width // 2)) // width) % (N // width + 1)
    tone = r.choice([-1, 0, 0, 1], size=int(brick_id.max()) + 1)
    idx = 3 + tone[brick_id] + (q(g, 3) - 1)
    idx[((yy % rh) == 0) & ~is_m] += 1
    idx[(bx == 0) & ~is_m] += 1
    idx[((yy % rh) == rh - 2) & ~is_m] -= 1
    idx = dots(r, idx, 4, -1, mask=~is_m)
    for _ in range(cracked):
        crack(r, idx, int(r.integers(4, 8)))
    rgb = paint_idx(idx, ramp)
    m_rgb = mortar if mortar is not None else (shift(base, dv=0.18, ds=-0.15) if light_mortar else shift(base, dv=-0.32))
    rgb[is_m] = m_rgb
    hgt = np.where(is_m, 0.2, 0.7 + (g - 0.5) * 0.1)
    if moss is not None:
        mg = fbm(r, ((2, 1.0), (4, 0.6)))
        mm = (mg > 0.6) & is_m
        mm |= (mg > 0.8)
        rgb[mm] = paint_idx(np.clip(((mg[mm] - 0.58) * 10).astype(int) + 1, 0, 4), moss)
        hgt[mm] = 0.6
    return Tex(rgb, hgt, rough=190, bump=1.0)


def columns(name, base, *, width=4, contrast=0.40, polished_=False):
    """Basalt side: upright columns, each lit on its left edge with a dark seam on its right."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast)
    jitter = r.integers(0, 2, size=N)
    col = (xx + jitter[yy // 4 * 0]) // width
    lx = (xx + jitter[0]) % width
    g = fbm(r, ((2, 0.5), (8, 1.0)), sx=1, sy=8)
    tone = r.choice([-1, 0, 1], size=N)
    idx = 3 + tone[col] + (0 if polished_ else (q(g, 3) - 1))
    idx[lx == 0] += 2
    idx[lx == width - 1] = 1
    if not polished_:
        for _ in range(4):                                 # chips across the columns
            x, y = int(r.integers(0, N)), int(r.integers(0, N))
            idx[y, x] = 1
            idx[(y + 1) % N, x] = 5
    hgt = np.where(lx == width - 1, 0.2, 0.7)
    return Tex(paint_idx(idx, ramp), hgt, rough=150 if polished_ else 200, bump=1.0)


def rings(name, base, *, contrast=0.38, n=3):
    """Column top: concentric rings around the middle."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast)
    d = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))
    band = (d // (8 / n)).astype(int)
    idx = 4 - (band % 2)
    edge = (np.abs(xx - 7.5) == d) & (xx < 7.5) | (np.abs(yy - 7.5) == d) & (yy < 7.5)
    idx[edge & ((d % (8 / n)) < 1)] += 1
    idx = bevel(idx, 1, -2)
    idx = dots(r, idx, 3, -1)
    return Tex(paint_idx(idx, ramp), 0.7 - band * 0.08, rough=170, bump=0.9)


def fluted(name, base, *, contrast=0.26):
    """Quartz pillar side: smooth vertical flutes."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast)
    lx = xx % 4
    idx = np.select([lx == 0, lx == 1, lx == 3], [5, 4, 2], 3)
    idx = idx + (fbm(r, ((2, 1.0),)) > 0.7)
    idx[0, :] += 1
    idx[N - 1, :] -= 1
    return Tex(paint_idx(idx, ramp), np.where(lx == 3, 0.3, 0.7), rough=120, bump=0.8)


def veined(name, base, *, contrast=0.24, veins=2):
    """Polished quartz: a calm surface with one or two soft veins and a bevel."""
    t = polished(name, base, contrast=contrast)
    r = rng_of(name + "v")
    ramp = make_ramp(base, 7, contrast)
    for _ in range(veins):
        x, y = int(r.integers(2, 13)), 1
        while y < N - 1:
            t.rgb[y, x % N] = ramp[3]
            x += int(r.choice([-1, 0, 1]))
            y += 1
    return t


def soul_sand(name, base):
    """Dark grains with soft hollows - a few of them look like little faces."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, 0.40)
    g = fbm(r, ((4, 1.0), (8, 0.6)))
    idx = q(g, 3) + 2
    for _ in range(3):
        x, y = int(r.integers(1, 13)), int(r.integers(1, 13))
        idx[y, x] = 0
        idx[y, (x + 2) % N] = 0                            # two eyes
        idx[(y + 2) % N, (x + 1) % N] = 1                  # a mouth
        idx[(y + 1) % N, x] = max(idx[(y + 1) % N, x], 4)
    idx = dots(r, idx, 5, +1)
    return Tex(paint_idx(idx, ramp), g, rough=230, bump=1.0)


def sparkle(name, base, *, contrast=0.22, count=6, light=None):
    """Snow: soft white drifts with tiny cold sparkles."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast)
    g = fbm(r, ((2, 1.0), (4, 0.5)))
    idx = q(0.5 + (g - 0.5) * 0.7, 3) + 2
    rgb = paint_idx(idx, ramp)
    for _ in range(count):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        rgb[y, x] = light or (255, 255, 255)
        rgb[(y + 1) % N, x] = ramp[2]
    return Tex(rgb, 0.5 + (g - 0.5) * 0.3, rough=200, bump=0.6)


def sculk(base):
    """Dark living stone with veins of glowing specks that pulse (4 frames)."""
    r = rng_of("sculk3")
    ramp = make_ramp(base, 7, 0.45)
    g = fbm(r, ((3, 1.0), (8, 0.6)))
    idx = q(g, 3) + 1
    spots = [(int(r.integers(0, N)), int(r.integers(0, N))) for _ in range(9)]
    frames = []
    for f in range(4):
        rgb = paint_idx(idx, ramp)
        emis = np.zeros((N, N))
        for k, (x, y) in enumerate(spots):
            on = (k + f) % 4
            c = [(30, 150, 160), (60, 200, 210), (120, 240, 240), (60, 200, 210)][on]
            rgb[y, x] = c
            emis[y, x] = [60, 140, 220, 140][on]
        frames.append(Tex(rgb, 0.4 + g * 0.3, rough=200, emis=emis, bump=0.8))
    return stack_frames(frames)


def build(out, flip, variations):
    # ----- nether
    out["netherrack"] = facets("netherrack3", shift(vbase("netherrack"), dv=0.06, ds=0.05), count=10, keep=0.6, cracks=0,
                               pits=6, light=(3, 1), dark=(2, 1), contrast=0.42, seam_dark=1)
    out["soul_sand"] = soul_sand("soul_sand3", shift(vbase("soul_sand"), dv=0.05))
    out["soul_soil"] = natural("soul_soil3", shift(vbase("soul_soil"), dv=-0.02, ds=0.04), cracks=0, spread=0.7, light=(4, 1),
                               dark=(6, 2), contrast=0.40)
    bs = shift(vbase("blackstone"), dv=0.06, ds=0.04)
    out["blackstone"] = facets("blackstone3", bs, count=7, keep=0.6, cracks=1, light=(5, 1), contrast=0.48, seam_dark=1)
    out["blackstone_top"] = facets("blackstone_top3", bs, count=6, keep=0.8, cracks=0, light=(4, 1), contrast=0.48)
    pbs = shift(vbase("polished_blackstone"), dv=0.06)
    out["polished_blackstone"] = polished("polished_blackstone3", pbs, frame=2, contrast=0.40)
    out["polished_blackstone_bricks"] = brick_wall("pbs_bricks3", pbs, rows=4, width=8, contrast=0.42)
    out["cracked_polished_blackstone_bricks"] = brick_wall("pbs_bricks3", pbs, rows=4, width=8, cracked=4, contrast=0.42)
    out["chiseled_polished_blackstone"] = chiseled_bricks("chiseled_pbs3", pbs)
    bb = shift(vbase("basalt_side"), dv=0.06)
    out["basalt_side"] = columns("basalt_side3", bb)
    out["basalt_top"] = rings("basalt_top3", shift(vbase("basalt_top"), dv=0.06))
    pb = shift(vbase("polished_basalt_side"), dv=0.06)
    out["polished_basalt_side"] = columns("polished_basalt_side3", pb, width=8, polished_=True, contrast=0.34)
    out["polished_basalt_top"] = rings("polished_basalt_top3", shift(vbase("polished_basalt_top"), dv=0.06), n=2)
    # ----- end
    out["end_stone"] = natural("end_stone3", shift(vbase("end_stone"), dv=0.04, ds=0.04), cracks=0, pits=18,
                               light=(4, 1), dark=(3, 1), spread=0.6, contrast=0.38)
    # ----- quartz
    qz = shift(vbase("quartz_block_side"), dv=0.02)
    out["quartz_block_side"] = veined("quartz_side3", qz)
    out["quartz_block_top"] = veined("quartz_top3", qz, veins=1)
    out["quartz_block_bottom"] = veined("quartz_bottom3", shift(qz, dv=-0.04), veins=3)
    out["quartz_block_chiseled"] = chiseled_bricks("quartz_chiseled3", qz)
    out["quartz_block_chiseled_top"] = chiseled_bricks("quartz_chiseled_top3", qz)
    out["quartz_block_lines"] = fluted("quartz_lines3", qz)
    out["quartz_block_lines_top"] = rings("quartz_lines_top3", qz, contrast=0.24, n=2)
    out["quartz_bricks"] = brick_wall("quartz_bricks3", qz, rows=4, width=8, contrast=0.24,
                                      mortar=shift(qz, dv=-0.16))
    # ----- crystals and living stone
    am = shift(vbase("amethyst_block"), dv=0.06, ds=0.05)
    out["amethyst_block"] = facets("amethyst3", am, count=9, keep=0.9, cracks=0, light=(5, 1), dark=(0, 1),
                                   edge_light=2, contrast=0.50, rough=60)
    bud = facets("amethyst3", am, count=9, keep=0.9, cracks=0, light=(5, 1), dark=(0, 1), edge_light=2,
                 contrast=0.50, rough=60)
    r = rng_of("budding3")
    for _ in range(5):                                     # little crystal buds
        x, y = int(r.integers(1, 15)), int(r.integers(1, 15))
        bud.rgb[y, x] = (250, 220, 255)
        bud.rgb[(y + 1) % N, x] = (170, 110, 230)
        bud.rgb[y, (x - 1) % N] = (90, 50, 150)
    out["budding_amethyst"] = bud
    out["sculk"] = sculk(shift(vbase("sculk"), dv=0.03))
    # ----- snow
    out["snow"] = sparkle("snow3", (236, 244, 252), count=7, light=(255, 255, 255))
    # ----- bricks
    sb = shift(vbase("stonebrick"), dv=0.04)
    out["stonebrick"] = brick_wall("stonebrick3", sb)
    out["nabd/stonebrick_v1"] = brick_wall("stonebrick3_v1", sb)
    out["nabd/stonebrick_v2"] = brick_wall("stonebrick3_v2", sb, cracked=1)
    variations["stone_bricks"] = ["stonebrick", "nabd/stonebrick_v1", "nabd/stonebrick_v2"]
    out["stonebrick_mossy"] = brick_wall("stonebrick3", sb, moss=make_ramp((74, 118, 42), 5, 0.32))
    out["stonebrick_cracked"] = brick_wall("stonebrick3", sb, cracked=5)
    out["stonebrick_carved"] = chiseled_bricks("stonebrick_carved3", sb)
    out["brick"] = brick_wall("brick3", shift(vbase("brick"), dv=0.05, ds=0.04), rows=4, width=8, light_mortar=True,
                              contrast=0.36)
