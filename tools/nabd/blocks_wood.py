"""Trees: planks, logs, stripped logs, leaves and a few carpentry blocks."""
import numpy as np

from . import painters as P
from .core import N, STATS, Tex, emboss, fbm, make_ramp, mix, norm01, paint, rng_of, shift, vbase, vramp, white

#        key        planks              log side            log top             stripped side              stripped top                 leaves
SPECIES = [
    ("oak",      "planks_oak",       "log_oak",          "log_oak_top",      "stripped_oak_log",        "stripped_oak_log_top",       "leaves_oak"),
    ("spruce",   "planks_spruce",    "log_spruce",       "log_spruce_top",   "stripped_spruce_log",     "stripped_spruce_log_top",    "leaves_spruce"),
    ("birch",    "planks_birch",     "log_birch",        "log_birch_top",    "stripped_birch_log",      "stripped_birch_log_top",     "leaves_birch"),
    ("jungle",   "planks_jungle",    "log_jungle",       "log_jungle_top",   "stripped_jungle_log",     "stripped_jungle_log_top",    "leaves_jungle"),
    ("acacia",   "planks_acacia",    "log_acacia",       "log_acacia_top",   "stripped_acacia_log",     "stripped_acacia_log_top",    "leaves_acacia"),
    ("dark_oak", "planks_big_oak",   "log_big_oak",      "log_big_oak_top",  "stripped_dark_oak_log",   "stripped_dark_oak_log_top",  "leaves_big_oak"),
    ("cherry",   "cherry_planks",    "cherry_log_side",  "cherry_log_top",   "stripped_cherry_log_side", "stripped_cherry_log_top",   "cherry_leaves"),
    ("mangrove", "mangrove_planks",  "mangrove_log_side", "mangrove_log_top", "stripped_mangrove_log_side", "stripped_mangrove_log_top", "mangrove_leaves"),
    ("pale_oak", "pale_oak_planks",  "pale_oak_log_side", "pale_oak_log_top", "stripped_pale_oak_log_side", "stripped_pale_oak_log_top", "pale_oak_leaves"),
    ("poplar",   "poplar_planks",    "poplar_log_side",  "poplar_log_top",   "stripped_poplar_log_side", "stripped_poplar_log_top",   None),
]
LEAF_STYLE = {
    "oak": dict(count=30, density=0.76), "spruce": dict(count=40, density=0.8, needles=True),
    "birch": dict(count=34, density=0.72), "jungle": dict(count=20, density=0.8),
    "acacia": dict(count=26, density=0.64), "dark_oak": dict(count=24, density=0.86),
    "cherry": dict(count=30, density=0.8), "mangrove": dict(count=22, density=0.78),
    "pale_oak": dict(count=26, density=0.74),
}
BARK_STYLE = {"oak": dict(ridges=8), "spruce": dict(ridges=6), "jungle": dict(ridges=10), "acacia": dict(ridges=7),
              "dark_oak": dict(ridges=6), "cherry": dict(ridges=10), "mangrove": dict(ridges=9),
              "pale_oak": dict(ridges=7), "poplar": dict(ridges=9)}


def leaf_set(out, base, key, style, ramp_grey_or_col, tinted):
    """Writes <base>, <base>_opaque and <base>_carried when the game has them."""
    t = P.leaves("leaves_" + key, ramp_grey_or_col, **style)
    out[base] = t
    if base + "_opaque" in STATS:
        o = t.copy()
        o.rgb = np.where((t.alpha == 0)[..., None], np.array(ramp_grey_or_col[0], np.uint8), t.rgb)
        o.alpha[:] = 255
        out[base + "_opaque"] = o
    if base + "_carried" in STATS:
        cr = vramp(base + "_carried", 5, contrast=0.4)
        out[base + "_carried"] = P.leaves("leaves_" + key, cr, **style)


def build(out, flip, variations):
    for key, planks, log, top, strip, strip_top, lv in SPECIES:
        if planks not in STATS:
            continue
        pr = vramp(planks, 5, contrast=0.24)
        out[planks] = P.planks("planks_" + key, pr)
        wood = vramp(strip, 5, contrast=0.2)
        if key == "birch":
            br = make_ramp(vbase(log), 5, 0.16)
            out[log] = P.bark("log_birch", br, ridges=5, bump=0.7, horizontal_marks=11,
                              mark_color=[(44, 42, 40), (64, 60, 56), (30, 30, 30)])
        else:
            br = vramp(log, 5, contrast=0.34)
            out[log] = P.bark("log_" + key, br, **BARK_STYLE.get(key, {}))
        out[top] = P.log_top("top_" + key, wood, br)
        out[strip] = P.stripped("strip_" + key, wood)
        out[strip_top] = P.log_top("top_" + key, wood, wood)
        if lv:
            tinted = lum_grey(lv)
            ramp = vramp(lv, 5, grey=True, contrast=0.4) if tinted else vramp(lv, 5, contrast=0.4)
            leaf_set(out, lv, key, LEAF_STYLE[key], ramp, tinted)
    if "stripped_poplar_side_log" in STATS:
        out["stripped_poplar_side_log"] = out["stripped_poplar_log_side"]
    for col in ("yellow", "orange", "red"):
        nm = f"{col}_poplar_leaves"
        if nm in STATS:
            leaf_set(out, nm, "poplar_" + col, dict(count=32, density=0.74), vramp(nm, 5, contrast=0.36), False)

    # azalea (coloured, not tinted)
    az = vramp("azalea_leaves", 5, contrast=0.4)
    out["azalea_leaves"] = P.leaves("leaves_azalea", az, count=30, density=0.78)
    o = out["azalea_leaves"].copy()
    o.rgb = np.where((o.alpha == 0)[..., None], np.array(az[0], np.uint8), o.rgb)
    o.alpha[:] = 255
    out["azalea_leaves_opaque"] = o
    fl = out["azalea_leaves"].copy()
    r = rng_of("azalea_flowers")
    pink = [(214, 96, 186), (240, 150, 220), (255, 214, 246)]
    for _ in range(7):
        x, y = int(r.integers(N)), int(r.integers(N))
        for dx, dy, c in ((0, 0, 2), (1, 0, 1), (0, 1, 1), (-1, 0, 1), (0, -1, 0)):
            fl.rgb[(y + dy) % N, (x + dx) % N] = pink[c]
            fl.alpha[(y + dy) % N, (x + dx) % N] = 255
    out["azalea_leaves_flowers"] = fl
    fo = fl.copy()
    fo.rgb = np.where((fl.alpha == 0)[..., None], np.array(az[0], np.uint8), fl.rgb)
    fo.alpha[:] = 255
    out["azalea_leaves_flowers_opaque"] = fo

    # ------------------------------------------------------------- carpentry
    oak = vramp("planks_oak", 5, contrast=0.24)
    dark = make_ramp(shift(vbase("planks_oak"), dv=-0.22), 5, 0.26)

    # bookshelf: two shelves of books framed by oak
    r = rng_of("bookshelf")
    b = P.planks("bookshelf_frame", oak, boards=4, nails=False)
    spines = [make_ramp(c, 4, 0.3) for c in ((170, 46, 40), (44, 96, 170), (52, 140, 70), (196, 160, 60),
                                             (120, 70, 150), (200, 200, 190), (60, 60, 70))]
    for (y0, y1) in ((1, 7), (9, 15)):
        b.rgb[y0:y1, 1:15] = dark[0]
        b.height[y0:y1, 1:15] = 0.15
        x = 1
        while x < 15:
            w = int(r.choice([1, 2, 2, 3]))
            w = min(w, 15 - x)
            hgt_b = int(r.choice([4, 5, 5, 6]))
            sp = spines[int(r.integers(len(spines)))]
            top = y1 - hgt_b
            for xx in range(x, x + w):
                for yy in range(top, y1):
                    c = sp[2]
                    if xx == x:
                        c = sp[3]
                    if xx == x + w - 1 and w > 1:
                        c = sp[1]
                    if yy == top + 1 and hgt_b > 4:
                        c = sp[0]
                    b.rgb[yy, xx] = c
                    b.height[yy, xx] = 0.6
            x += w
    out["bookshelf"] = b

    # crafting table
    top = P.planks("crafting_top", oak, boards=4, nails=False)
    yy, xx = np.mgrid[0:N, 0:N]
    frame = (yy < 2) | (yy > 13) | (xx < 2) | (xx > 13)
    top.rgb = np.where(frame[..., None], paint(np.where((yy == 0) | (xx == 0), 0.8, np.where((yy == 15) | (xx == 15), 0.15, 0.45)), dark), top.rgb)
    grid = ((yy == 5) | (yy == 10) | (xx == 5) | (xx == 10)) & ~frame
    top.rgb = np.where(grid[..., None], np.array(dark[0], np.uint8), top.rgb)
    top.height = np.where(frame, 0.9, np.where(grid, 0.2, 0.6))
    out["crafting_table_top"] = top
    steel = make_ramp((150, 156, 164), 5, 0.3)

    def table_side(seed, tools):
        s = P.planks(seed, oak, boards=4, nails=False, vertical=True)
        s.rgb[0:3] = paint(np.where(yy[0:3] == 0, 0.8, np.where(yy[0:3] == 2, 0.12, 0.45)), dark)
        s.height[0:3] = 0.9
        for col in (0, 15):
            s.rgb[3:, col] = dark[1]
        for (kind, x0, y0) in tools:
            if kind == "saw":
                for i in range(6):
                    s.rgb[y0 + i, x0 + i // 2] = steel[3]
                    s.rgb[y0 + i, x0 + i // 2 + 1] = steel[1]
                s.rgb[y0 - 1, x0] = dark[0]
                s.rgb[y0 - 1, x0 + 1] = dark[1]
            if kind == "hammer":
                s.rgb[y0, x0:x0 + 4] = steel[2]
                s.rgb[y0 + 1, x0:x0 + 4] = steel[0]
                for i in range(2, 8):
                    s.rgb[y0 + i, x0 + 1] = dark[3]
                    s.rgb[y0 + i, x0 + 2] = dark[1]
            if kind == "shears":
                for i in range(5):
                    s.rgb[y0 + i, x0 + i] = steel[4]
                    s.rgb[y0 + i, x0 + 4 - i] = steel[2]
                s.rgb[y0 + 5, x0] = dark[0]
                s.rgb[y0 + 5, x0 + 4] = dark[0]
        return s
    out["crafting_table_front"] = table_side("craft_front", [("saw", 3, 6), ("hammer", 9, 5)])
    out["crafting_table_side"] = table_side("craft_side", [("shears", 3, 6), ("hammer", 10, 5)])

    # ladder (alpha)
    lad = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=210)
    for x in (2, 3, 12, 13):
        lad.rgb[:, x] = oak[3] if x in (2, 12) else oak[1]
        lad.alpha[:, x] = 255
        lad.height[:, x] = 0.8
    for y in (2, 6, 10, 14):
        lad.rgb[y, 1:15] = oak[4]
        lad.rgb[y + 1, 1:15] = oak[0]
        lad.alpha[y:y + 2, 1:15] = 255
        lad.height[y:y + 2, 1:15] = 1.0
    out["ladder"] = lad


def lum_grey(name):
    m = STATS[name]["mean"]
    return abs(m[0] - m[1]) < 8 and abs(m[1] - m[2]) < 8
