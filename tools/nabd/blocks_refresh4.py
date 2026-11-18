"""Fourth refresh pass: glowstone, granite / diorite / andesite (and their
polished forms keep theirs), and the ice family.

Same approach as the deepslate redraw: keep the character people know from the
game (glowing crystal clusters, speckled igneous stone, clear cracked ice) but
draw it ourselves.  Our own pixel art; vanilla gives colour references only."""
import numpy as np

from .core import N, Tex, fbm, make_ramp, paint_idx, rng_of, shift, vbase, voronoi

yy, xx = np.mgrid[0:N, 0:N]


# ------------------------------------------------------------------ speckled stone
def igneous(name, base, grains, *, contrast=0.30, count=34, blobs=4, flow=1):
    """Granite, diorite, andesite: a softly mottled ground scattered with mineral
    grains.  `grains` is a list of (colour, share, lit) - each grain is 1-3 px,
    a lit grain gets a bright pixel on its upper-left, a dark one a soft shadow on
    its lower-right, so the surface looks rough and crystalline, not printed."""
    r = rng_of(name)
    ramp = make_ramp(base, 7, contrast, sat=1.05, warm=0.0)
    m = fbm(r, ((3, 1.0), (6, 0.6), (12, 0.3)), sx=flow, sy=1)
    idx = 3 + (m > 0.62) + (m > 0.82) - (m < 0.32) - (m < 0.14)
    rgb = paint_idx(idx, ramp).astype(float)
    hgt = 0.4 + 0.2 * m
    # a few larger soft blobs of a second tone
    for _ in range(blobs):
        cx, cy = r.random() * N, r.random() * N
        a, b = r.uniform(1.6, 2.8), r.uniform(1.2, 2.2)
        dx = (xx + 0.5 - cx + N / 2) % N - N / 2
        dy = (yy + 0.5 - cy + N / 2) % N - N / 2
        mm = (dx / a) ** 2 + (dy / b) ** 2 <= 1
        rgb[mm] = rgb[mm] * 0.6 + np.array(ramp[2 if r.random() < 0.5 else 4]) * 0.4
    shares = np.array([g[1] for g in grains], float)
    shares /= shares.sum()
    for _ in range(count):
        g = grains[int(r.choice(len(grains), p=shares))]
        col, lit = np.array(g[0], float), g[2]
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        shape = [(0, 0)] + [[(1, 0)], [(0, 1)], [(1, 0), (0, 1)], []][int(r.integers(0, 4))]
        for ox, oy in shape:
            rgb[(y + oy) % N, (x + ox) % N] = rgb[(y + oy) % N, (x + ox) % N] * 0.35 + col * 0.65
            hgt[(y + oy) % N, (x + ox) % N] = 0.7 if lit else 0.2
        if lit:
            rgb[y % N, x % N] = np.minimum(col * 1.08 + 6, 255)
        else:
            sy, sx = (y + 1) % N, (x + 1) % N
            if (sx, sy) not in [((x + ox) % N, (y + oy) % N) for ox, oy in shape]:
                rgb[sy, sx] = rgb[sy, sx] * 0.86
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.clip(hgt, 0, 1), rough=200, bump=1.0)


def stones(out):
    g = shift(vbase("stone_granite"), dv=0.02, ds=0.02)
    out["stone_granite"] = igneous("granite4", g, [
        (shift(g, dv=-0.20, ds=0.04), 4, False),          # dark mica
        (shift(g, dv=0.12, ds=-0.10), 3, True),           # pale feldspar
        (shift(g, dh=-0.02, ds=0.08, dv=0.05), 3, True),  # rosy grains
    ], contrast=0.28, count=30)
    d = shift(vbase("stone_diorite"), dv=0.03)
    out["stone_diorite"] = igneous("diorite4", d, [
        (shift(d, dv=-0.30), 5, False),                   # the grey-black flecks diorite is known for
        (shift(d, dv=-0.16), 4, False),
        ((248, 248, 246), 2, True),
    ], contrast=0.22, count=28, blobs=6)
    a = shift(vbase("stone_andesite"), dv=0.03)
    out["stone_andesite"] = igneous("andesite4", a, [
        (shift(a, dv=-0.14), 4, False),
        (shift(a, dv=0.10), 3, True),
    ], contrast=0.26, count=20, blobs=2, flow=4)        # andesite has a soft sideways flow


# ------------------------------------------------------------------ glowstone
def glowstone(name, base):
    """Glowstone: a cluster of glowing crystals.  Every crystal is a bright cell,
    hottest (almost white-yellow) in its middle, cooling to amber and then to a
    burnt orange rim; dark brown gaps sit between the crystals.  The light map
    follows the heat, so it glows from inside in every graphics mode."""
    r = rng_of(name)
    hot = [(110, 62, 30), (170, 98, 40), (214, 142, 58), (240, 186, 86), (252, 222, 130), (255, 244, 196)]
    ids, f1, f2, pts = voronoi(r, 11)
    edge = f2 - f1
    n = len(pts)
    off = r.choice([-1, 0, 0, 1], size=n)
    heat = np.clip(edge / 2.6, 0, 1)
    idx = np.clip((heat * 4.2).astype(int) + 1 + off[ids], 1, 5)
    up = (np.roll(ids, 1, 0) != ids) | (np.roll(ids, 1, 1) != ids)
    down = (np.roll(ids, -1, 0) != ids) | (np.roll(ids, -1, 1) != ids)
    idx[up & (edge > 0.4)] = np.minimum(idx[up & (edge > 0.4)] + 1, 5)
    gap = edge < 0.85
    idx[gap] = 0
    idx[down & ~gap & (edge < 1.0)] = np.maximum(idx[down & ~gap & (edge < 1.0)] - 1, 1)
    w = r.random((N, N))
    idx = np.where(~gap & (w > 0.93), np.minimum(idx + 1, 5), idx)        # sparkles
    rgb = paint_idx(idx, hot)
    emis = np.where(gap, 40, 120 + idx * 27).clip(0, 255)
    t = Tex(rgb, np.where(gap, 0.05, 0.3 + 0.12 * idx), rough=110, bump=1.0)
    t.emis = emis
    return t


# ------------------------------------------------------------------ ice
def ice(name, base, *, alpha=None, cracks=4, plates=0, contrast=0.16, streaks=5):
    """Ice: a calm, clear blue face with long diagonal light streaks (reflections),
    a few fine white cracks with a darker line beside them, and on packed / blue
    ice the faint outlines of frozen plates."""
    r = rng_of(name)
    ramp = make_ramp(base, 6, contrast, sat=1.0, warm=0.0)
    m = fbm(r, ((2, 1.0), (4, 0.4)))
    idx = 2 + (m > 0.55) + (m > 0.8) - (m < 0.2)
    if plates:
        ids, f1, f2, pts = voronoi(r, plates)
        e = f2 - f1
        idx[e < 0.5] -= 1
        idx[((np.roll(ids, 1, 0) != ids) | (np.roll(ids, 1, 1) != ids)) & (e >= 0.5)] += 1
    for _ in range(streaks):                               # reflections: short diagonal lines
        x, y, ln = int(r.integers(0, N)), int(r.integers(0, N)), int(r.integers(2, 6))
        for k in range(ln):
            idx[(y - k) % N, (x + k) % N] = max(idx[(y - k) % N, (x + k) % N], 4 if k % 3 else 5)
    for _ in range(cracks):                                # fine cracks
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        dx, dy = (1, 1) if r.random() < 0.5 else (1, -1)
        for k in range(int(r.integers(4, 9))):
            idx[y % N, x % N] = 5
            idx[(y + 1) % N, x % N] = max(0, min(idx[(y + 1) % N, x % N], 1))
            if r.random() < 0.65:
                x += dx
            else:
                y += dy
    rgb = paint_idx(idx, ramp)
    t = Tex(rgb, 0.5 + 0.08 * (idx - 2), rough=25, bump=0.5)
    if alpha is not None:
        t.alpha[:] = alpha
    return t


def ices(out):
    out["ice"] = ice("ice4", (150, 192, 238), alpha=200, cracks=4, streaks=6, contrast=0.16)
    out["ice_packed"] = ice("ice_packed4", shift(vbase("ice_packed"), ds=-0.04), cracks=3, plates=7, streaks=4,
                            contrast=0.18)
    out["blue_ice"] = ice("blue_ice4", shift(vbase("blue_ice"), dv=-0.02, ds=0.02), cracks=3, plates=5, streaks=5,
                          contrast=0.22)


def build(out, flip, variations):
    stones(out)
    out["glowstone"] = glowstone("glowstone4", vbase("glowstone"))
    ices(out)
