"""Storage blocks (the nine-item blocks): each mineral gets its own cartoon
identity inside the same bevelled frame, so they are told apart at a glance."""
import numpy as np

from .core import N, STATS, Tex, fbm, make_ramp, paint_idx, rng_of, shift, vbase, vramp

yy, xx = np.mgrid[0:N, 0:N]
EDGE0 = (yy == 0) | (xx == 0)
EDGE1 = (yy == N - 1) | (xx == N - 1)
INNER = (xx >= 2) & (xx <= 13) & (yy >= 2) & (yy <= 13)


def framed(ramp):
    """5-tone ramp -> index map with a raised bevelled frame and a flat field."""
    idx = np.full((N, N), 2)
    idx = np.where(EDGE0, 4, idx)
    idx = np.where(EDGE1, 0, idx)
    idx[0, N - 1] = idx[N - 1, 0] = 2
    ring0 = ((yy == 1) | (xx == 1)) & (xx >= 1) & (yy >= 1) & (xx <= 14) & (yy <= 14)
    ring1 = ((yy == 14) | (xx == 14)) & (xx >= 1) & (yy >= 1) & (xx <= 14) & (yy <= 14)
    idx = np.where(ring0 & ~EDGE0 & ~EDGE1, 3, idx)
    idx = np.where(ring1 & ~EDGE0 & ~EDGE1, 1, idx)
    hgt = np.where(INNER, 0.6, 0.95)
    return idx, hgt


def finish(idx, hgt, ramp, metal, rough, emis=0, extra=None):
    t = Tex(paint_idx(idx, ramp), hgt, metal=metal, rough=rough, bump=1.1)
    t.emis = emis
    if extra:
        for (x, y, c) in extra:
            t.rgb[y, x] = c
    return t


def glints(idx, spots):
    """Short diagonal shine strokes: the cartoon sign of polished metal."""
    for (x, y, ln) in spots:
        for i in range(ln):
            idx[y - i, x + i] = 4
    return idx


def build(out, flip, variations):
    # iron: riveted plate with one long sheen
    r = vramp("iron_block", 5, contrast=0.3)
    idx, hgt = framed(r)
    idx = glints(idx, [(4, 9, 4), (6, 10, 3)])
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        idx[y, x], idx[y + 1, x], hgt[y, x] = 4, 1, 1.0
    idx[8, 3:13] = np.where(idx[8, 3:13] == 2, 1, idx[8, 3:13])
    idx[7, 3:13] = np.where(idx[7, 3:13] == 2, 3, idx[7, 3:13])
    out["iron_block"] = finish(idx, hgt, r, 240, 70)

    # gold: three stacked ingots
    r = vramp("gold_block", 5, contrast=0.36)
    idx, hgt = framed(r)
    for y0 in (2, 6, 10):
        x0 = 2 if y0 != 6 else 3
        idx[y0, x0:x0 + 11] = 4
        idx[y0 + 1:y0 + 3, x0:x0 + 11] = 3
        idx[y0 + 3, x0:x0 + 11] = 0
        idx[y0:y0 + 3, x0 + 10] = 1
        idx[y0 + 1, x0 + 1:x0 + 4] = 4
        hgt[y0:y0 + 3, x0:x0 + 11] = 0.9
        hgt[y0 + 3, x0:x0 + 11] = 0.3
    out["gold_block"] = finish(idx, hgt, r, 250, 50)

    # diamond: a calm polished plate - raised inner panel, one soft diagonal
    # sheen and a single small sparkle
    r = vramp("diamond_block", 5, contrast=0.3)
    idx, hgt = framed(r)
    panel = (xx >= 3) & (xx <= 12) & (yy >= 3) & (yy <= 12)
    idx = np.where(panel & ((yy == 3) | (xx == 3)), 3, idx)
    idx = np.where(panel & ((yy == 12) | (xx == 12)), 1, idx)
    sheen = panel & ~((yy == 3) | (xx == 3) | (yy == 12) | (xx == 12)) & (((xx + yy) == 13) | ((xx + yy) == 14))
    idx = np.where(sheen, 3, idx)
    idx = np.where(panel & ((xx + yy) == 17) & (xx > 4) & (xx < 12) & (yy > 4) & (yy < 12), 3, idx)
    hgt = np.where(panel, 0.8, hgt)
    out["diamond_block"] = finish(idx, hgt, r, 60, 25, extra=[(5, 5, (255, 255, 255)), (6, 5, r[4]), (5, 6, r[4])])

    # emerald: step cut - nested rectangles
    r = vramp("emerald_block", 5, contrast=0.42)
    idx, hgt = framed(r)
    for inset, sunk in ((3, False), (5, True)):
        a, b = inset, 15 - inset
        box = (xx >= a) & (xx <= b) & (yy >= a) & (yy <= b)
        ring = box & ((xx == a) | (xx == b) | (yy == a) | (yy == b))
        lit = ring & ((yy == a) | (xx == a))
        idx = np.where(ring, 1 if not sunk else 4, idx)
        idx = np.where(lit, 4 if not sunk else 1, idx)
        idx = np.where(box & ~ring, 3 if not sunk else 2, idx)
        hgt = np.where(box, 0.9 if not sunk else 0.5, hgt)
    idx[7, 7] = idx[7, 8] = 4
    out["emerald_block"] = finish(idx, hgt, r, 60, 30)

    # lapis: deep blue stone with soft paler veins (no flecks)
    r = vramp("lapis_block", 5, contrast=0.36)
    idx, hgt = framed(r)
    g = fbm(rng_of("lapis_block"), ((3, 1.0), (5, 0.6)))
    idx = np.where(INNER & (g > 0.66), 3, idx)
    idx = np.where(INNER & (g < 0.3), 1, idx)
    out["lapis_block"] = finish(idx, hgt, r, 0, 120)

    # redstone: glowing circuit cross with a bright core
    r = vramp("redstone_block", 5, contrast=0.42)
    idx, hgt = framed(r)
    cross = INNER & ((np.abs(xx - 7.5) < 1) | (np.abs(yy - 7.5) < 1))
    core = (np.abs(xx - 7.5) < 2.6) & (np.abs(yy - 7.5) < 2.6)
    idx = np.where(cross, 3, idx)
    idx = np.where(core, 3, idx)
    idx = np.where(core & ((np.abs(xx - 7.5) < 1.6) & (np.abs(yy - 7.5) < 1.6)), 4, idx)
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        idx[y, x] = 4
    emis = np.where(idx >= 3, 130, 20) * INNER
    out["redstone_block"] = finish(idx, hgt, r, 0, 110, emis=emis)

    # coal: chunky black facets
    r = make_ramp((44, 44, 50), 5, 0.6, sat=1.0, lift=0.0)
    idx, hgt = framed(r)
    cell = ((xx - 2) // 4 + (yy - 2) // 4 * 3) % 5
    idx = np.where(INNER, np.array([1, 2, 1, 3, 2])[cell], idx)
    idx = np.where(INNER & (((xx - 2) % 4 == 0) | ((yy - 2) % 4 == 0)), 0, idx)
    idx = np.where(INNER & ((xx - 2) % 4 == 1) & ((yy - 2) % 4 == 1), 4, idx)
    out["coal_block"] = finish(idx, hgt, r, 0, 150)

    # netherite: heavy dark forged slab, warm rim, four big studs, anvil mark
    r = make_ramp((74, 66, 70), 5, 0.5, sat=1.0, lift=0.0)
    idx, hgt = framed(r)
    for (x, y) in ((3, 3), (11, 3), (3, 11), (11, 11)):
        idx[y:y + 2, x:x + 2] = 3
        idx[y, x] = 4
        idx[y + 1, x + 1] = 1
        idx[y + 2, x:x + 2] = 0
        hgt[y:y + 2, x:x + 2] = 1.0
    panel = (xx >= 6) & (xx <= 9) & (yy >= 6) & (yy <= 9)
    idx = np.where(panel, 1, idx)
    idx = np.where(panel & ((yy == 6) | (xx == 6)), 0, idx)
    idx = np.where(panel & ((yy == 9) | (xx == 9)), 3, idx)
    warm = [(x, y, (150, 110, 96)) for x, y in ((1, 1), (14, 1), (1, 14), (14, 14))]
    out["netherite_block"] = finish(idx, hgt, r, 235, 85, extra=warm)

    # copper in four ages: sheet with a cross seam, patina creeping in
    for stage, metal, rough, patina in (("copper_block", 235, 70, 0.0), ("exposed_copper", 190, 110, 0.25),
                                        ("weathered_copper", 120, 150, 0.5), ("oxidized_copper", 60, 185, 0.0)):
        r = vramp(stage, 5, contrast=0.3)
        idx, hgt = framed(r)
        seam = INNER & ((xx == 8) | (yy == 8))
        idx = np.where(seam, 1, idx)
        idx = np.where(INNER & ((xx == 9) | (yy == 9)) & ~seam, 3, idx)
        idx = glints(idx, [(3, 6, 3), (11, 14, 3)]) if stage == "copper_block" else idx
        t = finish(idx, hgt, r, metal, rough)
        if patina:
            g = fbm(rng_of("patina"), ((3, 1.0), (6, 0.6)))
            pm = INNER & (g > 1 - patina)
            pr = vramp("oxidized_copper", 5, contrast=0.3)
            t.rgb = np.where(pm[..., None], np.array(pr[2], np.uint8), t.rgb)
            t.rgb = np.where((pm & ~np.roll(pm, 1, 0))[..., None], np.array(pr[3], np.uint8), t.rgb)
        out[stage] = t

    # amethyst: easy on the eye - a flat purple face with a handful of
    # small crystal facets (lit corner, shaded corner), low contrast
    for nm in ("amethyst_block", "budding_amethyst"):
        if nm not in STATS:
            continue
        r = vramp(nm, 5, contrast=0.26)
        idx = np.full((N, N), 2)
        hgt = np.full((N, N), 0.5)
        for (x, y) in ((2, 2), (9, 1), (13, 6), (5, 7), (1, 11), (9, 11), (13, 13)):
            for dx, dy, tone in ((1, 0, 3), (0, 1, 3), (1, 1, 2), (2, 1, 1), (1, 2, 1)):
                idx[(y + dy) % N, (x + dx) % N] = tone
                hgt[(y + dy) % N, (x + dx) % N] = 0.8
        t = Tex(paint_idx(idx, r), hgt, metal=30, rough=40, bump=1.0)
        if nm == "budding_amethyst":
            for (x, y) in ((4, 4), (11, 9)):
                for dx, dy, v in ((0, 0, 0), (1, 0, 1), (0, 1, 1), (-1, 0, 4), (0, -1, 4)):
                    t.rgb[y + dy, x + dx] = r[v]
        out[nm] = t
