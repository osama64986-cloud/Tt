"""Second refresh pass: all ores (stone and deepslate, with their shimmer),
cobblestone and mossy cobblestone, gravel, crying obsidian and tall grass.
Our own pixel art; vanilla is used for colour references and sizes only."""
import math

import numpy as np

from . import painters as P
from .blocks_terrain import GEMS
from .core import N, Tex, cell_edges, fbm, make_ramp, paint_idx, rng_of, shift, stack_frames, vbase, voronoi

yy, xx = np.mgrid[0:N, 0:N]


def shape(rows):
    return [(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"]


# hand-drawn ore pieces (each ore picks from its own set)
PIECES = {
    "coal":     [shape([".##.", "####", ".###"]), shape(["##.", "###", ".#."]), shape([".#", "##"])],
    "iron":     [shape([".#.", "###", "##."]), shape(["##", "##"]), shape([".##", "##."])],
    "copper":   [shape(["##.", "###", ".##"]), shape(["##", ".#"]), shape([".#.", "###"])],
    "gold":     [shape([".##", "###", "##."]), shape(["##", "##"]), shape(["#.", "##"])],
    "redstone": [shape(["#.#", "...", ".#."]), shape(["#", ".", "#"]), shape(["#.", ".#"])],
    "lapis":    [shape(["#..", ".##", "..#"]), shape(["##.", ".##"]), shape([".#", "#."])],
    "diamond":  [shape(["..#..", ".###.", "#####", ".###.", "..#.."]), shape([".#.", "###", ".#."])],
    "emerald":  [shape([".#.", "###", "###", "###", ".#."]), shape([".##.", "####", "####", ".##."])],
}
VEINS = {"coal": 5, "iron": 5, "copper": 5, "gold": 5, "redstone": 6, "lapis": 6, "diamond": 4, "emerald": 4}


# diamond and emerald: a few big gems spread evenly over the face (one in each
# part of the block, never touching), instead of many small ones
SPREAD = {
    "diamond": [((1, 1), 0), ((9, 3), 0), ((3, 9), 0), ((11, 11), 1)],
    "emerald": [((2, 1), 0), ((10, 4), 1), ((4, 9), 1), ((11, 10), 0)],
}


def spread_layout(ore):
    r = rng_of("ore3:" + ore)
    clusters = []
    for (x0, y0), k in SPREAD[ore]:
        x0 += int(r.integers(0, 2))
        y0 += int(r.integers(0, 2))
        clusters.append([((x0 + x) % N, (y0 + y) % N) for x, y in PIECES[ore][k]])
    return clusters


def layout(ore):
    """Veins spread over the face (wrapping), each 1-3 pieces close together."""
    if ore in SPREAD:
        return spread_layout(ore)
    r = rng_of("ore2:" + ore)
    pieces = PIECES[ore]
    taken = np.zeros((N, N), bool)
    clusters = []
    centres = []
    tries = 0
    while len(clusters) < VEINS[ore] and tries < 600:
        tries += 1
        cx, cy = int(r.integers(0, N)), int(r.integers(0, N))
        if any(min(abs(cx - a), N - abs(cx - a)) + min(abs(cy - b), N - abs(cy - b)) < 6 for a, b in centres):
            continue
        cl = []
        for k in range(int(r.integers(1, 3)) if ore not in ("redstone",) else 1):
            pc = pieces[0 if k == 0 else int(r.integers(1, len(pieces)))]
            ox, oy = (cx + (0 if k == 0 else int(r.integers(-3, 4)))) % N, (cy + (0 if k == 0 else int(r.integers(2, 4)))) % N
            pts = [((ox + x) % N, (oy + y) % N) for x, y in pc]
            if any(taken[y, x] for x, y in pts):
                continue
            for x, y in pts:
                taken[y, x] = True
            cl.extend(pts)
        if cl:
            clusters.append(cl)
            centres.append((cx, cy))
    return clusters


def socket(t, mask):
    """darken the rock all around each piece a little: the ore sits in a pocket"""
    ring = np.zeros_like(mask)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ring |= np.roll(np.roll(mask, dy, 0), dx, 1)
    ring &= ~mask
    t.rgb[ring] = (t.rgb[ring].astype(float) * 0.82).astype(np.uint8)
    return t


def ores(out, flip):
    for ore, g in GEMS.items():
        cl = layout(ore)
        mask = np.zeros((N, N), bool)
        for c in cl:
            for x, y in c:
                mask[y, x] = True
        for base_key, key, fname in (("stone", f"{ore}_ore", f"{ore}_ore"),
                                     ("deepslate/deepslate", f"deepslate/deepslate_{ore}_ore", f"deepslate_{ore}_ore")):
            base = socket(out[base_key].copy(), mask)
            t = P.ore(base, cl, g["ramp"], metal=g["metal"], gem_rough=g["rough"], emis=g.get("emis", 0))
            out[key] = t
            if key in flip:                                  # shimmer: a glint travels over the veins
                steps = 12
                frames = [P.ore(base, cl, g["ramp"], metal=g["metal"], gem_rough=g["rough"], emis=g.get("emis", 0),
                                sparkle={f}) if f < len(cl) else t for f in range(steps)]
                strip = f"nabd/{fname}_shimmer"
                out[strip] = stack_frames(frames)
                flip[key] = dict(strip=strip, ticks=5, frames=steps)


# ------------------------------------------------------------------ stones on the ground
def pebbles(name, ramp_sets, count, gap=None, dome=True, moss=None):
    """Rounded stones with dark gaps; each stone lit on its top-left, shaded on its lower-right."""
    r = rng_of(name)
    ids, f1, f2, pts = voronoi(r, count)
    edge = f2 - f1                                          # small near a gap
    n = len(pts)
    which = r.integers(0, len(ramp_sets), size=n)
    off = r.choice([-1, 0, 0, 1], size=n)
    # light: compare with the pixel up-left (inside the same stone)
    up = np.roll(np.roll(ids, 1, 0), 1, 1) != ids
    down = np.roll(np.roll(ids, -1, 0), -1, 1) != ids
    idx = 3 + off[ids]
    idx = np.where(edge < 1.4, idx - 1, idx)               # rounded rims
    idx[up & (edge >= 0.7)] += 2
    idx[down & (edge >= 0.7)] -= 1
    g = fbm(r, ((8, 1.0),))
    idx = idx + (g > 0.72) - (g < 0.22)
    gap_m = edge < 0.75
    rgb = np.zeros((N, N, 3), np.uint8)
    for k, ramp in enumerate(ramp_sets):
        sel = which[ids] == k
        rgb[sel] = paint_idx(idx, ramp)[sel]
    rgb[gap_m] = gap if gap is not None else ramp_sets[0][0]
    hgt = np.clip(edge / 3.0, 0, 1) * 0.8
    hgt[gap_m] = 0.05
    if moss is not None:
        mg = fbm(r, ((2, 1.0), (4, 0.6)))
        m = (mg > 0.55) & (edge < 1.6)                   # moss grows in the gaps and along stone rims
        m |= (mg > 0.78) & (edge < 2.4)
        rgb[m] = paint_idx(np.clip(((mg[m] - 0.55) * 10).astype(int) + 1, 0, 4), moss)
        hgt[m] = 0.6
    return Tex(rgb, hgt, rough=200, bump=1.2)


def crying(out):
    """Obsidian with glowing cracks that branch through the stone."""
    t = out["obsidian"].copy()
    r = rng_of("crying2")
    glow = [(110, 30, 200), (168, 70, 246), (214, 150, 255), (246, 220, 255)]
    emis = np.zeros((N, N))
    crack = np.zeros((N, N), int)                           # 0 none, 1 rim, 2 core
    for _ in range(3):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        dx, dy = int(r.choice([-1, 1])), 1
        for step in range(int(r.integers(9, 14))):
            crack[y % N, x % N] = 2
            if r.random() < 0.25:                           # a short branch
                bx, by = x, y
                bdx = -dx
                for _b in range(int(r.integers(2, 4))):
                    bx += bdx
                    by += int(r.integers(0, 2))
                    crack[by % N, bx % N] = max(crack[by % N, bx % N], 2)
            if r.random() < 0.55:
                x += dx
            else:
                y += dy
    core = crack == 2
    rim = np.zeros_like(core)
    for ddy, ddx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        rim |= np.roll(np.roll(core, ddy, 0), ddx, 1)
    rim &= ~core
    t.rgb[rim] = (np.array(t.rgb[rim], float) * 0.5 + np.array(glow[0]) * 0.5).astype(np.uint8)
    t.rgb[core] = glow[2]
    # the brightest pixels where cracks meet or turn
    nb = sum(np.roll(np.roll(core, a, 0), b, 1).astype(int) for a, b in ((0, 1), (1, 0), (0, -1), (-1, 0)))
    t.rgb[core & (nb >= 3)] = glow[3]
    t.rgb[core & (nb <= 1)] = glow[1]
    emis[core] = 210
    emis[rim] = 60
    t.height = np.where(core, 0.1, t.height)
    t.emis = emis
    out["crying_obsidian"] = t


# ------------------------------------------------------------------ grass
def grass_blades(ramp, height, count, seed, top_part=None, w=N):
    """A tidy clump: blades rise from a narrow base and fan outwards with curved
    tips of different lengths, centre blades tallest.  For tall grass the same
    blades run through both halves (`height` 32, top_part picks the half)."""
    r = rng_of(seed)
    H = height
    rgb = np.zeros((H, w, 3), np.uint8)
    alpha = np.zeros((H, w), np.uint8)
    hgt = np.zeros((H, w))
    roots = np.linspace(5.0, 10.0, count) + r.uniform(-0.3, 0.3, count)
    order = np.argsort(np.abs(roots - 7.5))[::-1]          # outer blades behind, centre in front
    for n_, i in enumerate(order):
        x0 = roots[i]
        spread = (x0 - 7.5) / 2.5                            # -1 .. 1
        ln = int(H * (0.55 + 0.45 * (1 - abs(spread) ** 1.5)) * r.uniform(0.82, 1.0))
        out_lean = spread * 6.0 + r.uniform(-0.6, 0.6)       # how far the tip moves sideways
        for k in range(ln):
            t = k / max(1, ln - 1)
            y = H - 1 - k
            x = int(round(x0 + out_lean * t ** 1.8))
            if not 0 <= x < w:
                break
            tone = min(len(ramp) - 1, int(1 + t * (len(ramp) - 1.3)))
            if n_ % 2:
                tone = max(0, tone - 1)                      # alternate blades a shade darker
            rgb[y, x] = ramp[tone]
            alpha[y, x] = 255
            hgt[y, x] = 0.4 + 0.5 * t
    if top_part is not None:
        sl = slice(0, N) if top_part else slice(N, 2 * N)
        rgb, alpha, hgt = rgb[sl], alpha[sl], hgt[sl]
    return Tex(rgb, hgt, alpha=alpha, rough=210, sss=150, bump=0.8)


def grasses(out):
    from .blocks_plants import grey_ramp
    from .core import vramp
    tg = grey_ramp("tallgrass")
    out["tallgrass"] = grass_blades(tg, N, 7, "grass2")
    out["tallgrass_carried"] = grass_blades(vramp("tallgrass_carried", 5, contrast=0.4), N, 7, "grass2")
    dg = grey_ramp("double_plant_grass_bottom")
    out["double_plant_grass_bottom"] = grass_blades(dg, 2 * N, 8, "dgrass2", top_part=False)
    out["double_plant_grass_top"] = grass_blades(dg, 2 * N, 8, "dgrass2", top_part=True)
    out["double_plant_grass_carried"] = grass_blades(vramp("double_plant_grass_carried", 5, contrast=0.4), 2 * N, 8,
                                                     "dgrass2", top_part=True)


def suspicious(out):
    """Suspicious sand / gravel on top of the new ground textures: a brushed hollow
    that deepens each stage, with a hint of something buried glinting in it."""
    for kind, base_key in (("sand", "sand"), ("gravel", "gravel")):
        for stage in range(4):
            t = out[base_key].copy()
            d = np.hypot(xx - 7.5, yy - 8.5)
            rad = 2.5 + stage * 1.4
            hole = d < rad
            rim = (d >= rad) & (d < rad + 1)
            t.rgb[hole] = (t.rgb[hole].astype(float) * (0.78 - 0.04 * stage)).astype(np.uint8)
            t.rgb[rim & (yy > 8)] = np.clip(t.rgb[rim & (yy > 8)].astype(int) + 22, 0, 255).astype(np.uint8)
            t.height = np.where(hole, 0.2, t.height)
            if stage >= 1:                                   # something buried: a small warm glint
                t.rgb[9, 7] = (230, 196, 120)
                t.rgb[9, 8] = (196, 150, 84)
                if stage >= 2:
                    t.rgb[10, 7] = (160, 118, 64)
                    t.rgb[8, 8] = (255, 236, 180)
            out[f"suspicious_{kind}_{stage}"] = t


def darker_deepslate_family(out):
    """the whole deepslate family follows the darker deepslate"""
    for k in list(out):
        if k.startswith("deepslate/") and "_ore" not in k and k not in ("deepslate/deepslate", "deepslate/deepslate_top"):
            t = out[k]
            t.rgb = (t.rgb.astype(float) * 0.84).astype(np.uint8)


def build(out, flip, variations):
    darker_deepslate_family(out)
    ores(out, flip)
    # cobblestone: rounded stones, three slightly different greys, clean gaps
    cb = shift(vbase("cobblestone"), dv=0.06)
    sets = [make_ramp(cb, 7, 0.42), make_ramp(shift(cb, dv=0.07, dh=0.02, ds=0.03), 7, 0.42),
            make_ramp(shift(cb, dv=-0.07), 7, 0.42)]
    gap = shift(cb, dv=-0.36)
    out["cobblestone"] = pebbles("cobblestone2", sets, 9, gap=gap)
    out["nabd/cobblestone_v1"] = pebbles("cobblestone2_v1", sets, 9, gap=gap)
    variations["cobblestone"] = ["cobblestone", "nabd/cobblestone_v1"]
    moss = make_ramp((74, 118, 42), 5, 0.32)
    out["cobblestone_mossy"] = pebbles("cobblestone2", sets, 9, gap=gap, moss=moss)
    # gravel: many small mixed pebbles
    gb = shift(vbase("gravel"), dv=0.04)
    grey = (128, 126, 124)
    gsets = [make_ramp(grey, 7, 0.44), make_ramp((150, 132, 116), 7, 0.44),
             make_ramp((176, 172, 166), 7, 0.40), make_ramp((104, 104, 112), 7, 0.44)]
    ggap = (62, 58, 56)
    out["gravel"] = pebbles("gravel2", gsets, 22, gap=ggap)
    out["nabd/gravel_v1"] = pebbles("gravel2_v1", gsets, 22, gap=ggap)
    variations["gravel"] = ["gravel", "nabd/gravel_v1"]
    crying(out)
    grasses(out)
    suspicious(out)
