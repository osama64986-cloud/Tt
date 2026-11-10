"""Material painters.  Each returns a core.Tex painted from scratch."""
import numpy as np

from .core import (N, Tex, bayer, cell_edges, emboss, fbm, make_ramp, mix, norm01, paint,
                   rng_of, shift, value_noise, voronoi, white)


# ---------------------------------------------------------------------- helpers
def _lit(hgt, light=0.9, base=None, base_w=0.55):
    """Combine a height field with top-left embossing into a 0..1 tone field."""
    e = emboss(hgt, light)
    tone = (hgt if base is None else base) * base_w + 0.5 * (1 - base_w) + e
    return np.clip(tone, 0, 1)


def _strokes(r, count, length=(2, 4), w=N, h=N, horiz=0.5):
    """Short crack-like strokes. Returns a boolean mask."""
    m = np.zeros((h, w), bool)
    for _ in range(count):
        x, y = int(r.integers(w)), int(r.integers(h))
        hz = r.random() < horiz
        for i in range(int(r.integers(length[0], length[1] + 1))):
            m[y % h, x % w] = True
            if hz:
                x += 1
                y += int(r.choice([0, 0, 0, 1, -1]))
            else:
                y += 1
                x += int(r.choice([0, 0, 0, 1, -1]))
    return m


def _speckle(r, density, w=N, h=N):
    return r.random((h, w)) < density


# ------------------------------------------------------------------------- rock
def rock(name, ramp, style="smooth", rough=195, cracks=3, speck=None, speck_ramp=None, bump=1.0,
         seed=None):
    r = rng_of(seed or name)
    if style == "smooth":            # soft blotches + a few hairline cracks
        hgt = fbm(r, ((3, 1.0), (5, 0.55), (8, 0.25)))
    elif style == "strata":          # horizontal layers (deepslate, tuff, sandstone)
        hgt = fbm(r, ((2, 0.5), (8, 1.0), (16, 0.35)), sx=4)
    elif style == "pillars":         # vertical flow (basalt, dripstone)
        hgt = fbm(r, ((2, 0.5), (8, 1.0), (16, 0.35)), sy=4)
    elif style == "grain":           # coarse crystalline rock
        hgt = fbm(r, ((4, 1.0), (8, 0.8), (16, 0.5)))
    elif style == "fine":            # sand-like: calm dunes, sparse grains
        hgt = fbm(r, ((2, 1.0), (4, 0.5)), sx=2)
    else:
        raise ValueError(style)
    tone = _lit(hgt, 0.8)
    if style == "fine":
        tone = 0.5 + (hgt - 0.5) * 0.5
    crack = _strokes(r, cracks, (2, 4)) if cracks else np.zeros((N, N), bool)
    hgt = np.where(crack, hgt * 0.35, hgt)
    tone = np.where(crack, 0.04, tone)
    under = np.roll(crack, 1, 0) & ~crack      # lit lip under each crack
    tone = np.where(under, np.minimum(1, tone + 0.22), tone)
    rgb = paint(tone, ramp, dither=0.0 if style == "fine" else 0.6)
    if speck:
        sp = _speckle(r, speck) & ~crack
        sr = speck_ramp or ramp
        pick = r.integers(0, len(sr), (N, N))
        rgb = np.where(sp[..., None], np.array(sr, np.uint8)[pick], rgb)
        hgt = np.where(sp, np.clip(hgt + 0.12, 0, 1), hgt)
    return Tex(rgb, hgt, rough=rough, bump=bump)


def cells(name, ramp, count=8, gap=None, rough=200, vary=0.28, dome=0.55, bump=1.25, tints=None,
          seed=None, moss=None):
    """Cobble / gravel / raw-ore style: rounded stones separated by dark seams."""
    r = rng_of(seed or name)
    ids, f1, f2, pts = voronoi(r, count)
    edge = cell_edges(ids)
    nc = len(pts)
    off = (r.random(nc) - 0.5) * 2 * vary
    d = norm01(f2 - f1)                       # 0 at seams, 1 in cell centres
    hgt = np.clip(0.35 + dome * np.sqrt(d) + off[ids] * 0.5, 0, 1)
    hgt = np.where(edge, 0.05, hgt)
    tone = np.clip(0.5 + off[ids] + emboss(hgt, 0.75) + (fbm(r, ((8, 1.0),)) - 0.5) * 0.18, 0.12, 1)
    tone = np.where(edge, 0.0, tone)
    rgb = paint(tone, ramp, dither=0.35)
    if tints:                                  # some stones use another ramp
        which = r.integers(0, len(tints) + 1, nc)
        for i, tr in enumerate(tints):
            m = (which[ids] == i + 1) & ~edge
            rgb = np.where(m[..., None], paint(tone, tr, dither=0.35), rgb)
    if gap is not None:
        rgb = np.where(edge[..., None], np.array(gap, np.uint8), rgb)
    t = Tex(rgb, hgt, rough=rough, bump=bump)
    if moss:
        t = add_moss(t, name, moss)
    return t


def add_moss(t, name, moss_ramp, amount=0.42):
    r = rng_of(name + ":moss")
    field = fbm(r, ((3, 1.0), (6, 0.6)))
    low = 1 - norm01(t.height)
    m = (field * 0.6 + low * 0.4) > (1 - amount)
    tone = np.clip(0.45 + emboss(field, 1.2) + (white(r) - 0.5) * 0.25, 0, 1)
    t.rgb = np.where(m[..., None], paint(tone, moss_ramp), t.rgb)
    t.height = np.where(m, np.clip(t.height + 0.18, 0, 1), t.height)
    return t


# ----------------------------------------------------------------------- bricks
def bricks(name, ramp, mortar, rows=4, cols=2, stagger=True, vary=0.22, rough=190, bump=1.3,
           chip=0.05, crack=0, moss=None, bevel=True, seed=None, row_h=None, wear=0.2):
    """Generic masonry. `rows` courses per 16px, `cols` bricks per course."""
    r = rng_of(seed or name)
    rh = N // rows
    cw = N // cols
    hgt = np.zeros((N, N))
    tone = np.zeros((N, N))
    seam = np.zeros((N, N), bool)
    grain = fbm(r, ((8, 1.0), (16, 0.5)), sx=2)
    for row in range(rows):
        y0 = row * rh
        shiftx = (cw // 2) if (stagger and row % 2) else 0
        for col in range(cols):
            x0 = col * cw + shiftx
            o = (r.random() - 0.5) * 2 * vary
            for y in range(y0, y0 + rh):
                for xx in range(x0, x0 + cw):
                    x = xx % N
                    last_row = (y == y0 + rh - 1)
                    last_col = (xx == x0 + cw - 1)
                    if last_row or last_col:
                        seam[y, x] = True
                        continue
                    v = 0.52 + o + (grain[y, x] - 0.5) * wear
                    if bevel:
                        if y == y0 or xx == x0:
                            v += 0.16            # lit top / left edge
                        if y == y0 + rh - 2 or xx == x0 + cw - 2:
                            v -= 0.14            # shaded bottom / right edge
                    tone[y, x] = v
                    hgt[y, x] = 0.72 + o * 0.3 + (grain[y, x] - 0.5) * 0.1
    chips = (r.random((N, N)) < chip) & ~seam
    tone = np.where(chips, tone - 0.22, tone)
    hgt = np.where(chips, hgt - 0.2, hgt)
    if crack:
        c = _strokes(r, crack, (3, 6), horiz=0.3) & ~seam
        tone = np.where(c, 0.02, tone)
        hgt = np.where(c, 0.2, hgt)
    rgb = paint(np.clip(tone, 0, 1), ramp)
    mr = np.array(mortar, np.uint8)
    mpick = (white(r) * len(mortar)).astype(int).clip(0, len(mortar) - 1)
    rgb = np.where(seam[..., None], mr[mpick], rgb)
    hgt = np.where(seam, 0.12, hgt)
    t = Tex(rgb, hgt, rough=rough, bump=bump)
    if moss:
        t = add_moss(t, name, moss, 0.36)
    return t


def slab_face(name, ramp, border=1, rough=150, bump=0.9, inset=None, vary=0.1, seed=None, lines=None):
    """Polished / cut stone: one framed panel with a soft bevel."""
    r = rng_of(seed or name)
    g = fbm(r, ((3, 1.0), (6, 0.5)))
    tone = 0.5 + (g - 0.5) * vary * 2
    hgt = np.full((N, N), 0.7) + (g - 0.5) * 0.08
    yy, xx = np.mgrid[0:N, 0:N]
    for b in range(border):
        tone = np.where((yy == b) | (xx == b), tone + 0.2 - 0.06 * b, tone)
        tone = np.where((yy == N - 1 - b) | (xx == N - 1 - b), tone - 0.24 + 0.06 * b, tone)
        hgt = np.where((yy == b) | (xx == b) | (yy == N - 1 - b) | (xx == N - 1 - b), 0.45 + 0.1 * b, hgt)
    if inset:
        a, bq = inset, N - 1 - inset
        ring = ((yy == a) | (yy == bq) | (xx == a) | (xx == bq)) & (yy >= a) & (yy <= bq) & (xx >= a) & (xx <= bq)
        dark = ring & ((yy == a) | (xx == a))
        light = ring & ~dark
        tone = np.where(dark, tone - 0.26, tone)
        tone = np.where(light, tone + 0.14, tone)
        hgt = np.where(ring, 0.35, hgt)
    if lines:                                  # horizontal cut lines (cut sandstone etc.)
        for y in lines:
            tone[y, :] -= 0.22
            tone[(y + 1) % N, :] += 0.12
            hgt[y, :] = 0.35
    return Tex(paint(np.clip(tone, 0, 1), ramp), hgt, rough=rough, bump=bump)


# ------------------------------------------------------------------------- soil
def soil(name, ramp, pebbles=5, pebble_ramp=None, rough=215, clump=((3, 1.0), (6, 0.8), (12, 0.4)),
         bump=1.0, seed=None, dither=0.7):
    r = rng_of(seed or name)
    hgt = fbm(r, clump)
    tone = _lit(hgt, 1.0)
    rgb = paint(tone, ramp, dither=dither)
    pr = pebble_ramp or ramp
    for _ in range(pebbles):
        x, y = int(r.integers(N)), int(r.integers(N))
        big = r.random() < 0.5
        rgb[y, x] = pr[-1]
        hgt[y, x] = 0.95
        if big:
            rgb[y, (x + 1) % N] = pr[-2]
            hgt[y, (x + 1) % N] = 0.9
        rgb[(y + 1) % N, x] = pr[0]
        if big:
            rgb[(y + 1) % N, (x + 1) % N] = pr[0]
    return Tex(rgb, hgt, rough=rough, bump=bump)


def turf(name, ramp, rough=225, sss=0, blades=26, seed=None, bump=0.9):
    """Short grass seen from above: tufts made of little 2-3px blade strokes."""
    r = rng_of(seed or name)
    base = fbm(r, ((2, 1.0), (4, 0.6)))
    hgt = 0.25 + base * 0.2
    tone = 0.3 + base * 0.22
    for _ in range(blades):
        x, y = int(r.integers(N)), int(r.integers(N))
        ln = int(r.integers(2, 4))
        lean = int(r.choice([-1, 0, 0, 1]))
        for i in range(ln):
            yy, xx = (y - i) % N, (x + (lean if i == ln - 1 else 0)) % N
            v = 0.46 + 0.24 * i + (r.random() - 0.5) * 0.08
            if v > tone[yy, xx]:
                tone[yy, xx] = v
                hgt[yy, xx] = 0.5 + 0.2 * i
    return Tex(paint(np.clip(tone, 0, 1), ramp, dither=0.3), hgt, rough=rough, sss=sss, bump=bump)


def fringe_mask(name, depth=3, extra=2, seed=None):
    """Irregular hanging edge (grass over dirt, snow cap, podzol...)."""
    r = rng_of((seed or name) + ":fringe")
    m = np.zeros((N, N), bool)
    d = depth
    for x in range(N):
        d = int(np.clip(d + r.choice([-1, 0, 0, 1]), depth - 1, depth + extra))
        m[:d, x] = True
    # avoid a visible seam between column 15 and 0
    return m


def top_over(name, base, top, depth=3, extra=2, lip=True, seed=None):
    """Composite a `top` material hanging over `base` (side of grass etc.)."""
    m = fringe_mask(name, depth, extra, seed)
    rgb = np.where(m[..., None], top.rgb, base.rgb)
    hgt = np.where(m, np.clip(top.height * 0.5 + 0.5, 0, 1), base.height * 0.6)
    if lip:                                    # shadow cast on the base right under the fringe
        sh = np.roll(m, 1, 0) & ~m
        sh[0, :] = False
        rgb = np.where(sh[..., None], (rgb * 0.72).astype(np.uint8), rgb)
    t = Tex(rgb, hgt, rough=base.rough, bump=1.1)
    t.mask = m
    return t


# ------------------------------------------------------------------------- wood
def planks(name, ramp, boards=4, rough=205, seed=None, bump=1.1, nails=True, vertical=False):
    r = rng_of(seed or name)
    bh = N // boards
    grain = fbm(r, ((2, 0.5), (16, 1.0)), sx=5)
    tone = np.zeros((N, N))
    hgt = np.zeros((N, N))
    for b in range(boards):
        y0 = b * bh
        o = (r.random() - 0.5) * 0.24
        joint = int(r.integers(2, N - 2)) if boards > 1 else -1
        for y in range(y0, y0 + bh):
            for x in range(N):
                if y == y0 + bh - 1:           # seam under each board
                    tone[y, x], hgt[y, x] = 0.0, 0.1
                    continue
                v = 0.55 + o + (grain[y, x] - 0.5) * 0.42
                if y == y0:
                    v += 0.12
                if x == joint:
                    tone[y, x], hgt[y, x] = 0.05, 0.15
                    continue
                if x == (joint + 1) % N:
                    v += 0.1
                tone[y, x] = v
                hgt[y, x] = 0.7 + o * 0.3 + (grain[y, x] - 0.5) * 0.12
        if nails and joint >= 0 and bh >= 3:
            yy = y0 + (bh - 1) // 2
            for nx in ((joint - 2) % N, (joint + 2) % N):
                tone[yy, nx] = 0.1
                hgt[yy, nx] = 0.5
    t = Tex(paint(np.clip(tone, 0, 1), ramp), hgt, rough=rough, bump=bump)
    if vertical:
        t.rgb = np.ascontiguousarray(np.transpose(t.rgb, (1, 0, 2)))
        t.height = t.height.T.copy()
    return t


def bark(name, ramp, rough=220, seed=None, bump=1.5, ridges=8, horizontal_marks=0, mark_color=None):
    """Log side: vertical ridges that wander, with deep furrows."""
    r = rng_of(seed or name)
    hgt = fbm(r, ((ridges, 1.0), (16, 0.35)), sy=5)
    warp = (value_noise(r, 2, 4) * 3).astype(int)
    yy, xx = np.mgrid[0:N, 0:N]
    hgt = hgt[yy, (xx + warp) % N]
    tone = np.clip(hgt * 0.75 + 0.12 + emboss(hgt, 0.9), 0, 1)
    furrow = hgt < 0.24
    tone = np.where(furrow, 0.0, tone)
    rgb = paint(tone, ramp, dither=0.3)
    if horizontal_marks:                      # birch-like dashes
        mc = np.array(mark_color, np.uint8)
        for _ in range(horizontal_marks):
            x, y = int(r.integers(N)), int(r.integers(N))
            for i in range(int(r.integers(2, 5))):
                rgb[y, (x + i) % N] = mc[int(r.integers(len(mc)))]
                hgt[y, (x + i) % N] = 0.2
    return Tex(rgb, hgt, rough=rough, bump=bump)


def log_top(name, wood_ramp, bark_ramp, rough=210, seed=None, bump=1.1, rings=True):
    r = rng_of(seed or name)
    yy, xx = np.mgrid[0:N, 0:N]
    d = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))      # square-ish rings
    dr = np.hypot(xx - 7.5, yy - 7.5)
    ring = (d * 0.55 + dr * 0.45)
    wob = (fbm(r, ((4, 1.0),)) - 0.5) * 1.2
    band = np.floor(ring + wob).astype(int)
    tone = np.where(band % 2 == 0, 0.62, 0.40) if rings else np.full((N, N), 0.55)
    tone = tone + (white(r) - 0.5) * 0.1
    tone = np.where(band <= 0, 0.25, tone)                    # heart
    hgt = np.where(band % 2 == 0, 0.7, 0.6)
    rgb = paint(np.clip(tone, 0, 1), wood_ramp)
    border = d > 6.6
    bt = np.clip(0.45 + (white(r) - 0.5) * 0.5 + np.where((xx < 1) | (yy < 1), 0.15, -0.1), 0, 1)
    rgb = np.where(border[..., None], paint(bt, bark_ramp), rgb)
    inner = (d > 5.6) & ~border                               # shadow just inside the bark
    rgb = np.where(inner[..., None], (rgb * 0.8).astype(np.uint8), rgb)
    hgt = np.where(border, 0.9, hgt)
    return Tex(rgb, hgt, rough=rough, bump=bump)


def stripped(name, ramp, rough=200, seed=None, bump=0.8):
    r = rng_of(seed or name)
    g = fbm(r, ((8, 1.0), (16, 0.5)), sy=6)
    warp = (value_noise(r, 2, 3) * 2).astype(int)
    yy, xx = np.mgrid[0:N, 0:N]
    g = g[yy, (xx + warp) % N]
    tone = np.clip(0.2 + g * 0.6 + emboss(g, 0.5), 0, 1)
    return Tex(paint(tone, ramp, dither=0.25), 0.5 + g * 0.3, rough=rough, bump=bump)


# ------------------------------------------------------------------------- ores
ORE_SHAPES = {
    # each: list of pixel-offset blobs; drawn as lit, outlined gems
    "chunk":   [[(0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2)], [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (0, 1)]],
    "fleck":   [[(0, 1), (1, 0), (2, 0), (1, 1)], [(0, 0), (1, 0), (1, 1), (2, 1)], [(0, 0), (1, 0)]],
    "nugget":  [[(0, 0), (1, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)], [(0, 0), (0, 1)]],
    "shard":   [[(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)], [(0, 0), (1, 1)]],
    "crystal": [[(0, 0), (0, 1), (1, 1), (0, 2), (1, 2), (1, 3)], [(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (0, 1)]],
    "dots":    [[(0, 0), (2, 1), (1, 2)], [(0, 0), (1, 1)], [(0, 0), (2, 0), (1, 1)], [(0, 0)]],
    "clump":   [[(0, 0), (1, 0), (2, 1), (0, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (2, 2)], [(0, 0), (1, 1)]],
}


def ore_layout(seed, shape, count=6):
    """Pick non-overlapping cluster positions on the torus."""
    r = rng_of(seed)
    shapes = ORE_SHAPES[shape]
    placed, occ = [], np.zeros((N, N), bool)
    tries = 0
    while len(placed) < count and tries < 500:
        tries += 1
        sh = shapes[int(r.integers(len(shapes)))] if len(placed) >= 2 else shapes[len(placed) % 2]
        x, y = int(r.integers(N)), int(r.integers(N))
        px = [((x + dx) % N, (y + dy) % N) for dx, dy in sh]
        halo = [((qx + ox) % N, (qy + oy) % N) for qx, qy in px for ox in (-1, 0, 1) for oy in (-1, 0, 1)]
        if any(occ[qy, qx] for qx, qy in halo):
            continue
        for qx, qy in halo:
            occ[qy, qx] = True
        placed.append(px)
    return placed


def ore(base, clusters, gem, metal=0, gem_rough=110, emis=0, sparkle=None, raised=True, dark=None):
    """Stamp gem clusters into a base rock Tex. `gem` is a dark->light ramp.
    sparkle: optional set of (cluster_index) whose top-left pixel flashes white."""
    t = base.copy()
    metal_p = np.zeros((N, N))
    rough_p = np.full((N, N), float(base.rough) if np.isscalar(base.rough) else 195.0)
    emis_p = np.zeros((N, N))
    gem_mask = np.zeros((N, N), bool)
    for px in clusters:
        for (x, y) in px:
            gem_mask[y, x] = True
    for ci, px in enumerate(clusters):
        s = set(px)
        for (x, y) in px:
            up = ((x, (y - 1) % N) in s)
            left = (((x - 1) % N, y) in s)
            down = ((x, (y + 1) % N) in s)
            right = (((x + 1) % N, y) in s)
            if not up and not left:
                c = gem[-1]
            elif not up or not left:
                c = gem[-2]
            elif not down or not right:
                c = gem[1]
            else:
                c = gem[len(gem) // 2]
            t.rgb[y, x] = c
            t.height[y, x] = 0.95 if raised else 0.15
            metal_p[y, x] = metal
            rough_p[y, x] = gem_rough
            emis_p[y, x] = emis
        for (x, y) in px:                       # drop shadow on the rock, lower-right
            for dx, dy in ((1, 0), (0, 1)):
                qx, qy = (x + dx) % N, (y + dy) % N
                if not gem_mask[qy, qx]:
                    t.rgb[qy, qx] = dark if dark is not None else (t.rgb[qy, qx] * 0.66).astype(np.uint8)
                    t.height[qy, qx] = min(t.height[qy, qx], 0.3)
        if sparkle and ci in sparkle:
            x, y = px[0]
            t.rgb[y, x] = (255, 255, 255)
            emis_p[y, x] = max(emis_p[y, x], 60)
    t.metal, t.rough, t.emis = metal_p, rough_p, emis_p
    t.gem_mask = gem_mask
    return t


# ------------------------------------------------------------------- flat things
def flat(name, ramp, style="smooth", rough=200, metal=0, seed=None, bump=0.6, amount=0.5):
    r = rng_of(seed or name)
    if style == "smooth":          # concrete: big soft tone shifts
        g = fbm(r, ((2, 1.0), (4, 0.5)))
        tone = 0.5 + (g - 0.5) * amount
        hgt = 0.5 + (g - 0.5) * 0.1
        return Tex(paint(np.clip(tone, 0, 1), ramp), hgt, rough=rough, metal=metal, bump=bump)
    if style == "powder":          # concrete powder: grainy
        g = fbm(r, ((4, 0.6), (16, 1.0)))
        tone = np.clip(0.5 + (g - 0.5) * amount * 1.6 + emboss(g, 0.5), 0, 1)
        return Tex(paint(tone, ramp, dither=0.8), g, rough=rough, metal=metal, bump=bump)
    if style == "clay":            # terracotta: faint horizontal trowel strokes
        g = fbm(r, ((2, 0.6), (8, 1.0)), sx=6)
        tone = np.clip(0.5 + (g - 0.5) * amount + emboss(g, 0.3), 0, 1)
        return Tex(paint(tone, ramp), 0.5 + g * 0.15, rough=rough, metal=metal, bump=bump)
    raise ValueError(style)


def wool(name, ramp, rough=235, seed=None):
    """Knitted look: staggered little 'v' stitches."""
    r = rng_of(seed or name)
    yy, xx = np.mgrid[0:N, 0:N]
    row = yy // 2
    xs = (xx + (row % 2) * 2) % 4
    v = np.where(yy % 2 == 0, np.where((xs == 0) | (xs == 3), 0.72, 0.5), np.where((xs == 1) | (xs == 2), 0.66, 0.3))
    g = fbm(r, ((3, 1.0), (6, 0.5)))
    tone = np.clip(v + (g - 0.5) * 0.35 + (white(r) - 0.5) * 0.08, 0, 1)
    hgt = np.clip(v * 0.7 + g * 0.2, 0, 1)
    return Tex(paint(tone, ramp), hgt, rough=rough, sss=40, bump=1.0)


def glass(name, frame, glint, body=None, body_alpha=0, frame_alpha=255, seed=None):
    """Framed pane: 1px frame, a couple of diagonal glints, clear middle."""
    r = rng_of(seed or name)
    rgb = np.zeros((N, N, 3), np.uint8)
    alpha = np.full((N, N), body_alpha, np.uint8)
    if body is not None:
        rgb[:] = body
    yy, xx = np.mgrid[0:N, 0:N]
    fr = (yy == 0) | (xx == 0) | (yy == N - 1) | (xx == N - 1)
    lit = fr & ((yy == 0) | (xx == 0))
    rgb[fr] = frame[1]
    rgb[lit] = frame[2]
    rgb[0, N - 1] = frame[1]
    rgb[N - 1, 0] = frame[1]
    rgb[N - 1, N - 1] = frame[0]
    alpha[fr] = frame_alpha
    # glints: two short diagonals, top-left and a tiny one bottom-right
    for (x, y, ln) in ((3, 6, 4), (5, 7, 3), (11, 12, 2)):
        for i in range(ln):
            px, py = x + i, y - i
            rgb[py, px] = glint
            alpha[py, px] = max(frame_alpha, 200) if body_alpha == 0 else min(255, body_alpha + 70)
    hgt = np.where(fr, 0.7, 0.5)
    return Tex(rgb, hgt, alpha=alpha, rough=12, metal=0, bump=0.5)


# ----------------------------------------------------------------------- foliage
def leaves(name, ramp, density=0.74, seed=None, count=30, sss=140, rough=205, needles=False):
    """Clustered leaflets with see-through gaps. Works for tinted greys too."""
    r = rng_of(seed or name)
    ids, f1, f2, pts = voronoi(r, count, min_dist=0.62 * np.sqrt(N * N / count))
    if needles:                                # conifers: cells stretched into short vertical strokes
        yy, xx = np.mgrid[0:N, 0:N]
        ids = ids[(yy // 2 * 2 + (xx % 2)) % N, xx]
        f1 = f1[(yy // 2 * 2) % N, xx]
        f2 = f2[(yy // 2 * 2) % N, xx]
    nc = len(pts)
    keep = r.random(nc) < density
    off = r.random(nc)
    d = norm01(f2 - f1)
    hgt = np.clip(0.3 + off[ids] * 0.5 + d * 0.25, 0, 1)
    tone = np.clip(0.18 + off[ids] * 0.62 + emboss(hgt, 0.9), 0, 1)
    edge = cell_edges(ids)
    tone = np.where(edge, tone * 0.45, tone)
    alpha = np.where(keep[ids], 255, 0).astype(np.uint8)
    rgb = paint(tone, ramp)
    return Tex(rgb, hgt, alpha=alpha, rough=rough, sss=sss, bump=1.2)


def blades(name, ramp, count=9, height=(6, 14), seed=None, sss=150, base_y=N - 1, spread=6.5, w=N, h=N,
           curl=1.0):
    """Cross-plant sprite: individual grass blades rising from the bottom."""
    r = rng_of(seed or name)
    rgb = np.zeros((h, w, 3), np.uint8)
    alpha = np.zeros((h, w), np.uint8)
    hgt = np.zeros((h, w))
    order = sorted(range(count), key=lambda i: r.random())
    for i in order:
        x = w / 2 - 0.5 + (r.random() - 0.5) * 2 * spread
        ln = int(r.integers(height[0], height[1] + 1))
        lean = (r.random() - 0.5) * 0.9 * curl
        shade = r.random()
        for k in range(ln):
            y = base_y - k
            if y < 0:
                break
            fx = x + lean * (k / 3.0) ** 1.5
            xi = int(round(fx))
            if not (0 <= xi < w):
                break
            t = k / max(1, ln - 1)
            tone = np.clip(0.2 + 0.55 * t + (shade - 0.5) * 0.35, 0, 0.999)
            rgb[y, xi] = ramp[int(tone * len(ramp))]
            alpha[y, xi] = 255
            hgt[y, xi] = 0.4 + 0.5 * t
            if k < ln * 0.45 and 0 <= xi + 1 < w and r.random() < 0.55:   # thicker near the root
                rgb[y, xi + 1] = ramp[max(0, int(tone * len(ramp)) - 1)]
                alpha[y, xi + 1] = 255
                hgt[y, xi + 1] = 0.35
    return Tex(rgb, hgt, alpha=alpha, rough=210, sss=sss, bump=0.8)


# ------------------------------------------------------------------ metal blocks
def metal_block(name, ramp, style="plate", metal=235, rough=70, seed=None, bump=1.0):
    r = rng_of(seed or name)
    yy, xx = np.mgrid[0:N, 0:N]
    g = fbm(r, ((2, 1.0), (4, 0.5)))
    tone = 0.5 + (g - 0.5) * 0.18
    hgt = np.full((N, N), 0.7)
    if style == "plate":            # framed plate with rivets
        fr0 = (yy == 0) | (xx == 0)
        fr1 = (yy == N - 1) | (xx == N - 1)
        tone = np.where(fr0, 0.92, tone)
        tone = np.where(fr1, 0.12, tone)
        inner0 = ((yy == 2) | (xx == 2)) & (yy >= 2) & (xx >= 2) & (yy <= 13) & (xx <= 13)
        inner1 = ((yy == 13) | (xx == 13)) & (yy >= 2) & (xx >= 2) & (yy <= 13) & (xx <= 13)
        tone = np.where(inner0, tone - 0.22, tone)
        tone = np.where(inner1, tone + 0.2, tone)
        hgt = np.where(fr0 | fr1, 0.9, hgt)
        hgt = np.where(inner0 | inner1, 0.45, hgt)
        tone += np.where((xx + yy) % 9 == 0, 0.1, 0) * ((xx > 2) & (xx < 13) & (yy > 2) & (yy < 13))
    elif style == "bars":           # stacked ingots (3 courses)
        row = yy // 5
        ly = yy % 5
        off = np.where(row % 2 == 0, 0, 4)
        lx = (xx + off) % 8
        tone = 0.5 + (g - 0.5) * 0.15
        tone = np.where(ly == 0, 0.9, tone)
        tone = np.where(lx == 0, np.maximum(tone, 0.8), tone)
        tone = np.where((ly == 4) | (yy == 15), 0.08, tone)
        tone = np.where(lx == 7, np.minimum(tone, 0.2), tone)
        hgt = np.where((ly == 4) | (lx == 7) | (yy == 15), 0.2, 0.8)
    elif style == "facets":         # gem block: triangular facets
        d1 = (xx + yy) // 4
        d2 = (xx - yy + 16) // 4
        f = (d1 * 3 + d2 * 5) % 4
        tone = np.array([0.25, 0.5, 0.72, 0.9])[f] + (g - 0.5) * 0.1
        edge = ((xx + yy) % 4 == 0) | ((xx - yy) % 4 == 0)
        tone = np.where(edge, tone - 0.18, tone)
        hgt = np.array([0.4, 0.6, 0.75, 0.9])[f]
        fr0 = (yy == 0) | (xx == 0)
        fr1 = (yy == N - 1) | (xx == N - 1)
        tone = np.where(fr0, 0.95, tone)
        tone = np.where(fr1, 0.1, tone)
    elif style == "rough":          # lapis / coal / redstone: dense mineral
        g2 = fbm(r, ((4, 1.0), (8, 0.8)))
        tone = np.clip(0.2 + g2 * 0.6 + emboss(g2, 1.1), 0, 1)
        hgt = g2
        fr0 = (yy == 0) | (xx == 0)
        fr1 = (yy == N - 1) | (xx == N - 1)
        tone = np.where(fr0, np.minimum(1, tone + 0.2), tone)
        tone = np.where(fr1, tone * 0.5, tone)
    elif style == "sheet":          # copper: big sheet with a seam cross
        tone = 0.5 + (g - 0.5) * 0.3 + (fbm(r, ((8, 1.0),)) - 0.5) * 0.12
        fr0 = (yy == 0) | (xx == 0)
        fr1 = (yy == N - 1) | (xx == N - 1)
        tone = np.where(fr0, tone + 0.25, tone)
        tone = np.where(fr1, tone - 0.3, tone)
        hgt = np.where(fr0 | fr1, 0.5, 0.7)
    return Tex(paint(np.clip(tone, 0, 1), ramp), hgt, metal=metal, rough=rough, bump=bump)


def recolor(tex, mask, ramp):
    """Repaint masked pixels using their brightness order against a new ramp."""
    l = tex.rgb @ np.array([0.299, 0.587, 0.114])
    v = norm01(l)
    out = tex.copy()
    out.rgb = np.where(mask[..., None], paint(v, ramp), tex.rgb)
    return out
