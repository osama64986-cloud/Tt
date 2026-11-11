"""Village & utility blocks: doors, trapdoors, work stations, lamps, archaeology
sand, glazed terracotta, cactus, crystals and a few leftovers."""
import numpy as np

from . import painters as P
from .core import (N, STATS, Tex, emboss, fbm, make_ramp, mix, norm01, paint, plane, rng_of, shift, stack_frames,
                   vbase, vramp, white)

yy, xx = np.mgrid[0:N, 0:N]
IRON = make_ramp((150, 154, 162), 5, 0.32)
DARK_IRON = make_ramp((70, 72, 80), 5, 0.34)

WOODS = [  # key, planks stat name, trapdoor name, door (upper, lower)
    ("oak", "planks_oak", "trapdoor", ("door_wood_upper", "door_wood_lower")),
    ("spruce", "planks_spruce", "spruce_trapdoor", ("door_spruce_upper", "door_spruce_lower")),
    ("birch", "planks_birch", "birch_trapdoor", ("door_birch_upper", "door_birch_lower")),
    ("jungle", "planks_jungle", "jungle_trapdoor", ("door_jungle_upper", "door_jungle_lower")),
    ("acacia", "planks_acacia", "acacia_trapdoor", ("door_acacia_upper", "door_acacia_lower")),
    ("dark_oak", "planks_big_oak", "dark_oak_trapdoor", ("door_dark_oak_upper", "door_dark_oak_lower")),
    ("cherry", "cherry_planks", "cherry_trapdoor", ("cherry_door_top", "cherry_door_bottom")),
    ("mangrove", "mangrove_planks", "mangrove_trapdoor", ("mangrove_door_top", "mangrove_door_bottom")),
    ("pale_oak", "pale_oak_planks", "pale_oak_trapdoor", ("pale_oak_door_top", "pale_oak_door_bottom")),
    ("poplar", "poplar_planks", "poplar_trapdoor", ("poplar_door_top", "poplar_door_bottom")),
    ("bamboo", "bamboo_planks", "bamboo_trapdoor", ("bamboo_door_top", "bamboo_door_bottom")),
]
DOOR_STYLE = {"oak": "panes", "spruce": "bands", "birch": "cross", "jungle": "lattice", "acacia": "slats",
              "dark_oak": "arch", "cherry": "round", "mangrove": "twin", "pale_oak": "panes", "poplar": "cross",
              "bamboo": "slats"}
TRAP_STYLE = {"oak": "grid", "spruce": "solid", "birch": "frame", "jungle": "lattice", "acacia": "slats",
              "dark_oak": "solid", "cherry": "frame", "mangrove": "grid", "pale_oak": "frame", "poplar": "grid",
              "bamboo": "slats"}


def has_holes(name):
    return name in STATS and 0 in STATS[name]["alpha"]


def frame_panel(t, ramp, x0, y0, x1, y1, sunk=True):
    """Bevelled rectangle (inclusive coords): sunk panel or raised plate."""
    hi, lo = (ramp[0], ramp[4]) if sunk else (ramp[4], ramp[0])
    t.rgb[y0, x0:x1 + 1] = hi
    t.rgb[y0:y1 + 1, x0] = hi
    t.rgb[y1, x0:x1 + 1] = lo
    t.rgb[y0:y1 + 1, x1] = lo
    t.height[y0:y1 + 1, x0:x1 + 1] = 0.35 if sunk else 0.95


def hole(t, x0, y0, x1, y1, rim):
    t.alpha[y0:y1 + 1, x0:x1 + 1] = 0
    t.height[y0:y1 + 1, x0:x1 + 1] = 0.0
    for x in range(x0 - 1, x1 + 2):
        for y in (y0 - 1, y1 + 1):
            if 0 <= x < N and 0 <= y < N and t.alpha[y, x]:
                t.rgb[y, x] = rim[0] if y < y0 else rim[4]
    for y in range(y0, y1 + 1):
        for x in (x0 - 1, x1 + 1):
            if 0 <= x < N and t.alpha[y, x]:
                t.rgb[y, x] = rim[0] if x < x0 else rim[4]


def door(key, ramp, style, holes):
    up = P.planks("door_u_" + key, ramp, boards=4, nails=False, vertical=True)
    lo = P.planks("door_l_" + key, ramp, boards=4, nails=False, vertical=True)
    dark = [shift(c, dv=-0.1) for c in ramp]
    for t in (up, lo):                         # outer stiles
        t.rgb[:, 0] = ramp[4]
        t.rgb[:, 15] = ramp[0]
        t.height[:, [0, 15]] = 0.9
    up.rgb[0, :] = ramp[4]
    lo.rgb[15, :] = ramp[0]

    def window(x0, y0, x1, y1):
        if holes:
            hole(up, x0, y0, x1, y1, ramp)
        else:
            up.rgb[y0:y1 + 1, x0:x1 + 1] = dark[0]
            frame_panel(up, ramp, x0, y0, x1, y1)
    if style == "panes":
        for (x0, y0) in ((3, 3), (9, 3), (3, 9), (9, 9)):
            window(x0, y0, x0 + 3, y0 + 3)
        frame_panel(lo, ramp, 3, 2, 6, 12)
        frame_panel(lo, ramp, 9, 2, 12, 12)
    elif style == "bands":
        for t in (up, lo):
            for y in (3, 11):
                t.rgb[y, 1:15] = DARK_IRON[3]
                t.rgb[y + 1, 1:15] = DARK_IRON[1]
                t.height[y:y + 2, 1:15] = 1.0
                for x in (3, 8, 12):
                    t.rgb[y, x] = IRON[4]
        window(6, 6, 9, 8)
    elif style == "cross":
        window(3, 3, 6, 12)
        window(9, 3, 12, 12)
        frame_panel(lo, ramp, 3, 2, 12, 12)
    elif style == "lattice":
        for (x0, y0) in ((3, 2), (7, 2), (11, 2), (5, 6), (9, 6), (3, 10), (7, 10), (11, 10)):
            window(x0, y0, x0 + 1, y0 + 1)
        frame_panel(lo, ramp, 3, 3, 12, 6)
        frame_panel(lo, ramp, 3, 9, 12, 12)
    elif style == "slats":                     # upright bars, as these doors have in the game
        for x in (3, 6, 9, 12):
            window(x, 2, x, 12)
        for x in (4, 8, 12):
            lo.rgb[2:13, x] = ramp[0]
            lo.rgb[2:13, x - 1] = ramp[4]
            lo.height[2:13, x] = 0.2
    elif style == "arch":
        frame_panel(up, ramp, 3, 3, 12, 15)
        up.rgb[3, 3] = up.rgb[3, 12] = ramp[2]
        frame_panel(lo, ramp, 3, 0, 12, 12)
        for t in (up, lo):
            for (x, y) in ((1, 2), (14, 2), (1, 13), (14, 13)):
                t.rgb[y, x] = IRON[4]
                t.height[y, x] = 1.0
    elif style == "round":
        m = (np.hypot(xx - 7.5, yy - 6.5) < 3.6)
        if holes:
            up.alpha = np.where(m, 0, up.alpha).astype(np.uint8)
        else:
            up.rgb = np.where(m[..., None], np.array(dark[0], np.uint8), up.rgb)
        ring = (np.hypot(xx - 7.5, yy - 6.5) < 4.6) & ~m
        up.rgb = np.where(ring[..., None], np.array(ramp[0], np.uint8), up.rgb)
        up.rgb = np.where((ring & (yy + xx > 15))[..., None], np.array(ramp[4], np.uint8), up.rgb)
        frame_panel(lo, ramp, 3, 2, 12, 12)
    elif style == "twin":
        window(3, 3, 5, 7)
        window(10, 3, 12, 7)
        frame_panel(lo, ramp, 3, 3, 12, 12)
    # handle on the lower-left of the upper half / upper-left of the lower half
    for t, y in ((up, 14), (lo, 1)):
        t.rgb[y, 2] = IRON[4]
        t.rgb[y, 3] = IRON[1]
        t.height[y, 2:4] = 1.0
    return up, lo


def trapdoor(key, ramp, style, holes):
    t = P.planks("trap_" + key, ramp, boards=4, nails=False)
    fr = (yy == 0) | (xx == 0) | (yy == 15) | (xx == 15)
    t.rgb = np.where(fr[..., None], np.array(ramp[1], np.uint8), t.rgb)
    t.rgb[0, :] = ramp[4]
    t.rgb[:, 0] = ramp[4]
    t.rgb[15, :] = ramp[0]
    t.rgb[:, 15] = ramp[0]
    t.height = np.where(fr, 0.95, t.height)

    def cut(x0, y0, x1, y1):
        if holes:
            hole(t, x0, y0, x1, y1, ramp)
        else:
            frame_panel(t, ramp, x0, y0, x1, y1)
    if style == "grid":
        for x0 in (3, 9):
            for y0 in (3, 9):
                cut(x0, y0, x0 + 3, y0 + 3)
    elif style == "frame":
        cut(3, 3, 12, 12)
    elif style == "lattice":
        for x0 in (2, 6, 10):
            for y0 in (2, 6, 10):
                cut(x0 + 1, y0 + 1, x0 + 2, y0 + 2)
    elif style == "slats":
        for y in (3, 6, 9, 12):
            cut(2, y, 13, y)
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):       # corner studs / hinges
        t.rgb[y, x] = IRON[3]
        t.height[y, x] = 1.0
    return t


def glazed(color_name):
    """Our own pinwheel tile: an 8x8 motif rotated into the four quadrants."""
    r = rng_of("glazed:" + color_name)
    base = vbase(f"glazed_terracotta_{color_name}")
    ramp = make_ramp(base, 5, 0.34)
    accent = make_ramp(mix(base, (250, 246, 236), 0.75), 3, 0.12)
    second = make_ramp(shift(base, dh=0.08 + 0.1 * r.random(), dv=0.05), 4, 0.3)
    q = np.full((8, 8), 2)
    kind = int(r.integers(0, 4))
    for y in range(8):
        for x in range(8):
            d = x + y
            if kind == 0:                       # diagonal bands
                q[y, x] = [1, 2, 3, 2, 5, 2, 6, 3][d % 8]
            elif kind == 1:                     # nested corner squares
                q[y, x] = [5, 1, 3, 3, 6, 2, 2, 1][max(x, y)]
            elif kind == 2:                     # petals
                q[y, x] = 5 if abs(x - y) <= 1 and d > 2 else (6 if (x * y) % 5 == 0 else 2 + (d % 2))
            else:                               # chevrons
                q[y, x] = [3, 1, 5, 2, 6, 2, 3, 1][(x + (7 - y)) % 8] if x >= y else [2, 3, 1, 5][(y - x) % 4]
    q[0, :] = 1
    q[:, 0] = 1
    q[7, 7] = 5
    full = np.zeros((N, N), int)
    full[:8, :8] = q
    full[:8, 8:] = np.rot90(q, -1)
    full[8:, 8:] = np.rot90(q, -2)
    full[8:, :8] = np.rot90(q, -3)
    pal = np.array([ramp[0], ramp[1], ramp[2], ramp[3], ramp[4], accent[2], second[2]], np.uint8)
    rgb = pal[full]
    hgt = np.array([0.2, 0.3, 0.5, 0.6, 0.7, 0.9, 0.8])[full]
    return Tex(rgb, hgt, rough=40, bump=0.6)


def build(out, flip, variations):
    for key, planks, trap, (du, dl) in WOODS:
        if planks not in STATS:
            continue
        ramp = vramp(planks, 5, contrast=0.26)
        if trap in STATS:
            out[trap] = trapdoor(key, ramp, TRAP_STYLE[key], has_holes(trap))
        if du in STATS and dl in STATS:
            u, l = door(key, ramp, DOOR_STYLE[key], has_holes(du))
            out[du], out[dl] = u, l
    # iron door & trapdoor
    it = P.metal_block("iron_trap", IRON, "plate", metal=235, rough=80)
    for x0 in (3, 9):
        for y0 in (3, 9):
            hole(it, x0, y0, x0 + 3, y0 + 3, IRON) if has_holes("iron_trapdoor") else frame_panel(it, IRON, x0, y0, x0 + 3, y0 + 3)
    out["iron_trapdoor"] = it
    iu = P.metal_block("iron_door_u", IRON, "plate", metal=235, rough=80)
    il = P.metal_block("iron_door_l", IRON, "plate", metal=235, rough=80)
    for (x0, y0) in ((3, 3), (9, 3), (3, 9), (9, 9)):
        hole(iu, x0, y0, x0 + 3, y0 + 3, IRON) if has_holes("door_iron_upper") else frame_panel(iu, IRON, x0, y0, x0 + 3, y0 + 3)
    frame_panel(il, IRON, 3, 3, 12, 12)
    out["door_iron_upper"], out["door_iron_lower"] = iu, il

    oak = vramp("planks_oak", 5, contrast=0.24)
    spruce = vramp("planks_spruce", 5, contrast=0.24)
    dark = make_ramp(shift(vbase("planks_oak"), dv=-0.22), 5, 0.26)

    # ----------------------------------------------------------------- barrel
    side = P.planks("barrel_side", spruce, boards=4, nails=False, vertical=True)
    for y0 in (2, 12):
        side.rgb[y0] = DARK_IRON[3]
        side.rgb[y0 + 1] = DARK_IRON[1]
        side.height[y0:y0 + 2] = 1.0
        side.metal = np.where((yy == y0) | (yy == y0 + 1), 200, 0) if np.isscalar(side.metal) else np.where((yy == y0) | (yy == y0 + 1), 200, side.metal)
    out["barrel_side"] = side

    def lid(open_):
        t = P.planks("barrel_lid", spruce, boards=4, nails=False)
        d = np.hypot(xx - 7.5, yy - 7.5)
        rim = d > 6.4
        t.rgb = np.where(rim[..., None], paint(np.where(xx + yy < 15, 0.75, 0.3), DARK_IRON), t.rgb)
        t.height = np.where(rim, 1.0, t.height)
        if open_:
            inner = d < 5.4
            t.rgb = np.where(inner[..., None], np.array((34, 24, 16), np.uint8), t.rgb)
            t.rgb = np.where((inner & (d > 4.4) & (xx + yy < 15))[..., None], np.array((20, 14, 10), np.uint8), t.rgb)
            t.height = np.where(inner, 0.0, t.height)
        else:
            t.rgb[7:9, 7:9] = DARK_IRON[1]
        return t
    out["barrel_top"] = lid(False)
    out["barrel_top_open"] = lid(True)
    out["barrel_bottom"] = lid(False)

    # ------------------------------------------------------ smoker / blast furnace
    def oven(prefix, body_ramp, mortar, trim, metal_body=0):
        side = P.bricks(prefix + "_side", body_ramp, mortar, rows=4, cols=2, vary=0.2)
        if trim:
            for rows_, c0, c1 in (((0, 1), trim[4], trim[1]), ((14, 15), trim[3], trim[0])):
                side.rgb[rows_[0]] = c0
                side.rgb[rows_[1]] = c1
                side.height[rows_[0]:rows_[1] + 1] = 0.95
        side.metal = metal_body
        out[prefix + "_side"] = side
        top = P.slab_face(prefix + "_top", body_ramp, border=2, vary=0.2, rough=160)
        vent = (yy >= 5) & (yy <= 10) & (xx >= 5) & (xx <= 10) & ((xx + yy) % 2 == 0)
        top.rgb = np.where(vent[..., None], np.array((24, 22, 22), np.uint8), top.rgb)
        top.height = np.where(vent, 0.0, top.height)
        top.metal = metal_body
        out[prefix + "_top"] = top
        if prefix + "_bottom" in STATS:
            out[prefix + "_bottom"] = P.slab_face(prefix + "_bottom", body_ramp, border=1, vary=0.2, rough=180)
        def front(lit, phase=0):
            t = side.copy()
            emis = np.zeros((N, N))
            door_m = (yy >= 4) & (yy <= 12) & (xx >= 3) & (xx <= 12)
            t.rgb = np.where(door_m[..., None], np.array(DARK_IRON[1], np.uint8), t.rgb)
            frame_panel(t, DARK_IRON, 3, 4, 12, 12, sunk=False)
            t.height = np.where(door_m, 0.9, t.height)
            for y in (6, 8, 10):                     # grille slots
                t.rgb[y, 5:11] = (22, 20, 20)
                t.height[y, 5:11] = 0.1
                if lit:
                    for x in range(5, 11):
                        t.rgb[y, x] = [(240, 110, 20), (255, 180, 50), (255, 230, 120)][(x + y + phase) % 3]
                        emis[y, x] = 235
            t.emis = emis
            t.metal = np.where(door_m, 200, metal_body)
            t.rough = plane(side.rough)
            return t
        out[prefix + "_front_off"] = front(False)
        w, h = STATS[prefix + "_front_on"]["size"]      # the lit face is an animation strip in the game
        out[prefix + "_front_on"] = stack_frames([front(True, f) for f in range(max(1, h // w))])
    oven("smoker", vramp("smoker_side", 5, contrast=0.3), [(52, 50, 50), (62, 60, 60)], spruce)
    oven("blast_furnace", vramp("blast_furnace_side", 5, contrast=0.3), [(46, 46, 50), (56, 56, 60)], None, metal_body=120)

    # --------------------------------------------------------- job site tables
    def table(prefix, top_names, wood, decorate_top, sides):
        top = P.planks(prefix + "_top", wood, boards=4, nails=False)
        decorate_top(top)
        out[top_names] = top
        for nm, deco in sides.items():
            if nm not in STATS:
                continue
            s = P.planks(nm, wood, boards=4, nails=False, vertical=True)
            s.rgb[0:2] = paint(np.where(yy[0:2] == 0, 0.8, 0.2), wood)
            s.height[0:2] = 0.95
            deco(s)
            out[nm] = s

    # smithing table: dark plate on wood
    def sm_top(t):
        t.rgb[:] = paint(np.clip(0.5 + (fbm(rng_of("smith"), ((4, 1.0),)) - 0.5) * 0.3, 0, 1), DARK_IRON)
        frame_panel(t, DARK_IRON, 0, 0, 15, 15, sunk=False)
        frame_panel(t, DARK_IRON, 3, 3, 12, 12)
        t.metal, t.rough = 220, 90

    def sm_side(tools):
        def f(s):
            s.rgb[0:4] = paint(np.where(yy[0:4] == 0, 0.85, np.where(yy[0:4] == 3, 0.15, 0.5)), DARK_IRON)
            s.height[0:4] = 1.0
            if tools:
                for i in range(6):                    # hammer
                    s.rgb[7 + i, 4] = oak[3]
                s.rgb[6, 3:7] = IRON[3]
                s.rgb[7, 3:7] = IRON[1]
                for i in range(5):                    # tongs
                    s.rgb[7 + i, 10 + (i % 2)] = IRON[2]
        return f
    table("smithing", "smithing_table_top", dark, sm_top,
          {"smithing_table_front": sm_side(True), "smithing_table_side": sm_side(False)})
    out["smithing_table_bottom"] = P.planks("smithing_bottom", dark, boards=4, nails=False)

    # cartography table: a map pinned on dark wood
    paper = make_ramp((224, 208, 170), 5, 0.14)

    def ca_top(t):
        t.rgb[2:14, 2:14] = paint(np.clip(0.5 + (fbm(rng_of("map"), ((4, 1.0),)) - 0.5) * 0.4, 0, 1), paper)[2:14, 2:14]
        t.height[2:14, 2:14] = 0.9
        r = rng_of("map_ink")
        land = fbm(r, ((3, 1.0), (6, 0.5))) > 0.55
        ink = land & (xx > 2) & (xx < 13) & (yy > 2) & (yy < 13)
        t.rgb = np.where(ink[..., None], np.array((120, 150, 96), np.uint8), t.rgb)
        for (x, y) in ((4, 4), (10, 9)):
            t.rgb[y, x] = (190, 50, 40)

    def ca_side(n):
        def f(s):
            if n >= 1:
                s.rgb[5:12, 3:13] = paper[2]
                s.rgb[5, 3:13] = paper[4]
                s.rgb[11, 3:13] = paper[0]
                for y in (7, 9):
                    s.rgb[y, 5:11] = (150, 130, 100)
            if n == 2:
                s.rgb[6:11, 9:12] = (70, 90, 150)
        return f
    table("cartography", "cartography_table_top", dark, ca_top,
          {"cartography_table_side1": ca_side(1), "cartography_table_side2": ca_side(2), "cartography_table_side3": ca_side(0)})

    # fletching table: target rings on top, arrows on the side
    birch = vramp("planks_birch", 5, contrast=0.22)

    def fl_top(t):
        d = np.hypot(xx - 7.5, yy - 7.5)
        ring = ((d > 2.2) & (d < 3.4)) | ((d > 5.0) & (d < 6.0))
        t.rgb = np.where(ring[..., None], np.array((176, 60, 50), np.uint8), t.rgb)
        t.rgb[7:9, 7:9] = (220, 190, 80)

    def fl_side(s):
        for x0 in (4, 10):
            for i in range(8):
                s.rgb[4 + i, x0] = oak[1]
            s.rgb[3, x0] = IRON[4]
            s.rgb[4, x0 - 1] = IRON[2]
            s.rgb[4, x0 + 1] = IRON[2]
            for y in (10, 11):
                s.rgb[y, x0 - 1] = (236, 236, 240)
                s.rgb[y, x0 + 1] = (200, 200, 208)
    table("fletching", "fletcher_table_top", birch, fl_top,
          {"fletcher_table_side1": fl_side, "fletcher_table_side2": fl_side})

    # loom
    def lo_top(t):
        frame_panel(t, oak, 2, 2, 13, 13)

    def lo_front(s):
        s.rgb[3:13, 2:14] = dark[0]
        for y in range(4, 13, 2):                 # the warp runs sideways across the frame
            s.rgb[y, 3:13] = [(226, 220, 204), (196, 188, 170)][(y // 2) % 2]
        for y in (9, 10, 11):
            s.rgb[y, 3:9] = [(190, 60, 60), (70, 110, 180), (224, 190, 70)][y - 9]
        s.height[3:13, 2:14] = 0.3

    def lo_side(s):
        frame_panel(s, oak, 3, 4, 12, 12)
    table("loom", "loom_top", oak, lo_top, {"loom_front": lo_front, "loom_side": lo_side})
    out["loom_bottom"] = P.planks("loom_bottom", oak, boards=4, nails=False)

    # note block & jukebox
    nb = P.planks("noteblock", dark, boards=4, nails=False)
    frame_panel(nb, dark, 0, 0, 15, 15, sunk=False)
    note = ["..33..", "..3.3.", "..3...", "..3...", "333...", "333..."]
    for dy, row in enumerate(note):
        for dx, ch in enumerate(row):
            if ch != ".":
                nb.rgb[5 + dy, 5 + dx] = (30, 22, 16)
                nb.height[5 + dy, 5 + dx] = 0.2
    out["noteblock"] = nb
    js = P.planks("jukebox_side", dark, boards=4, nails=False)
    frame_panel(js, dark, 0, 0, 15, 15, sunk=False)
    js.rgb[3:5, 2:14] = (24, 18, 14)
    js.height[3:5, 2:14] = 0.1
    out["jukebox_side"] = js
    jt = P.planks("jukebox_top", dark, boards=4, nails=False)
    frame_panel(jt, dark, 0, 0, 15, 15, sunk=False)
    d = np.hypot(xx - 7.5, yy - 7.5)
    jt.rgb = np.where((d < 5.5)[..., None], np.array((26, 26, 30), np.uint8), jt.rgb)
    jt.rgb = np.where(((d > 2.5) & (d < 3.5))[..., None], np.array((60, 60, 68), np.uint8), jt.rgb)
    jt.rgb = np.where((d < 1.5)[..., None], np.array((200, 60, 60), np.uint8), jt.rgb)
    jt.height = np.where(d < 5.5, 0.3, jt.height)
    out["jukebox_top"] = jt

    # redstone lamp
    for nm, lit in (("redstone_lamp_off", False), ("redstone_lamp_on", True)):
        base = (118, 70, 40) if not lit else (232, 170, 80)
        t = P.cells("redstone_lamp", make_ramp(base, 6, 0.4), 9, vary=0.3, dome=0.5)
        fr = (yy == 0) | (xx == 0) | (yy == 15) | (xx == 15)
        bars = fr | (((yy == 7) | (xx == 7)) & True)
        t.rgb = np.where(bars[..., None], paint(np.where((yy == 0) | (xx == 0) | (yy == 7) | (xx == 7), 0.6, 0.2), make_ramp((84, 44, 30), 5, 0.3)), t.rgb)
        t.height = np.where(bars, 1.0, t.height * 0.6)
        t.emis = np.where(bars, 0, 220 if lit else 0)
        t.rough = 110
        out[nm] = t

    # target
    hay = vramp("target_side", 5, contrast=0.2)
    tt = P.rock("target", make_ramp((226, 210, 180), 5, 0.14), "fine", cracks=0, speck=0.05, rough=220)
    ring = ((d > 2.0) & (d < 3.6)) | ((d > 5.4) & (d < 6.9))
    tt.rgb = np.where(ring[..., None], paint(np.clip(0.5 + (white(rng_of("target")) - 0.5) * 0.4, 0, 1), make_ramp((206, 70, 56), 5, 0.2)), tt.rgb)
    tt.rgb = np.where((d < 1.2)[..., None], np.array((206, 70, 56), np.uint8), tt.rgb)
    out["target_top"] = tt
    ts = tt.copy()
    for y0 in (0, 13):
        ts.rgb[y0:y0 + 3] = paint(np.clip(0.3 + fbm(rng_of("target_hay"), ((8, 1.0),), sy=4) * 0.6, 0, 1), make_ramp((206, 170, 76), 5, 0.3))[y0:y0 + 3]
    out["target_side"] = ts

    # bee hive (crafted) & bee nest (natural)
    hv = P.planks("beehive", oak, boards=4, nails=False)
    out["beehive_side"] = hv
    out["beehive_top"] = P.planks("beehive_top", oak, boards=2, nails=True)
    for nm, honey in (("beehive_front", False), ("beehive_front_honey", True)):
        t = hv.copy()
        t.rgb[9:12, 4:12] = (36, 24, 14)
        t.height[9:12, 4:12] = 0.05
        if honey:
            t.rgb[10:12, 4:12] = (236, 160, 30)
            for x in (5, 8, 10):
                t.rgb[12:14, x] = (250, 190, 50)
            t.emis = np.where((yy >= 10) & (yy < 12) & (xx >= 4) & (xx < 12), 30, 0)
        out[nm] = t
    nest_r = vramp("bee_nest_side", 5, contrast=0.3)
    ns = P.rock("bee_nest", nest_r, "strata", cracks=0, rough=210)
    out["bee_nest_side"] = ns
    out["bee_nest_top"] = P.rock("bee_nest_top", vramp("bee_nest_top", 5, contrast=0.26), "smooth", cracks=2, rough=210)
    out["bee_nest_bottom"] = P.rock("bee_nest_bottom", vramp("bee_nest_bottom", 5, contrast=0.26), "smooth", cracks=2, rough=210)
    for nm, honey in (("bee_nest_front", False), ("bee_nest_front_honey", True)):
        t = ns.copy()
        m = np.hypot(xx - 7.5, (yy - 8.5) * 1.3) < 3.2
        t.rgb = np.where(m[..., None], np.array((40, 26, 12) if not honey else (236, 160, 30), np.uint8), t.rgb)
        t.height = np.where(m, 0.05, t.height)
        if honey:
            for x in (6, 9):
                t.rgb[11:14, x] = (250, 190, 50)
        out[nm] = t

    # ---------------------------------------------------------- archaeology
    for kind, base_name in (("sand", "sand"), ("gravel", "gravel")):
        for st in range(4):
            nm = f"suspicious_{kind}_{st}"
            if nm not in STATS:
                continue
            if kind == "sand":
                t = P.rock("sand", vramp("sand", 5, contrast=0.13), "fine", cracks=0, speck=0.07, rough=220, bump=0.7)
                dug = make_ramp(shift(vbase("sand"), dv=-0.2), 5, 0.2)
            else:
                gv = vramp("gravel", 6, contrast=0.34)
                t = P.cells("gravel", gv, 17, vary=0.35, dome=0.5, bump=1.1)
                dug = make_ramp(shift(vbase("gravel"), dv=-0.22), 5, 0.24)
            r = rng_of("sus_" + kind)
            spots = [(int(r.integers(2, 13)), int(r.integers(2, 13))) for _ in range(6)]
            for i, (x, y) in enumerate(spots[: 2 + st]):
                sz = 1 + st // 2 + (i % 2)
                m = np.hypot(xx - x, yy - y) <= sz
                t.rgb = np.where(m[..., None], paint(np.clip(0.3 + white(r) * 0.5, 0, 1), dug), t.rgb)
                rimm = (np.hypot(xx - x, yy - y) <= sz + 1) & ~m & (yy > y)
                t.rgb = np.where(rimm[..., None], np.minimum(255, t.rgb.astype(int) + 22).astype(np.uint8), t.rgb)
                t.height = np.where(m, 0.1, t.height)
            out[nm] = t

    # ----------------------------------------------------- glazed terracotta
    for c in ("black", "blue", "brown", "cyan", "gray", "green", "light_blue", "lime", "magenta", "orange",
              "pink", "purple", "red", "silver", "white", "yellow"):
        out[f"glazed_terracotta_{c}"] = glazed(c)

    # ----------------------------------------------------------------- cactus
    cr = vramp("cactus_side", 5, contrast=0.3)
    rib = np.abs(((xx - 1) % 4) - 1.5) / 1.5
    tone = np.clip(0.68 - rib * 0.38 + (fbm(rng_of("cactus"), ((8, 1.0),), sy=4) - 0.5) * 0.14, 0, 1)
    side = Tex(paint(tone, cr), 0.9 - rib * 0.6, rough=170, sss=60, bump=1.2)
    spine = (236, 232, 200)
    for y in range(1, N, 3):
        for x in (3, 7, 11):
            side.rgb[y, x + (y % 2)] = spine
    side.alpha[:, 0] = 0
    side.alpha[:, 15] = 0
    for y in range(2, N, 4):                       # spikes poke out past the body
        side.rgb[y, 0] = spine
        side.alpha[y, 0] = 255
        side.rgb[(y + 2) % N, 15] = spine
        side.alpha[(y + 2) % N, 15] = 255
    out["cactus_side"] = side
    for nm in ("cactus_top", "cactus_bottom"):
        d2 = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))
        tone = np.clip(0.75 - d2 * 0.05 + ((xx + yy) % 4 == 0) * 0.1, 0, 1) if nm == "cactus_top" else np.clip(0.45 + (white(rng_of(nm)) - 0.5) * 0.2, 0, 1)
        t = Tex(paint(tone, vramp(nm, 5, contrast=0.3)), 0.5 + (7.5 - d2) * 0.04, rough=170, bump=1.0)
        t.alpha[[0, 15], :] = 0
        t.alpha[:, [0, 15]] = 0
        if nm == "cactus_top":
            t.rgb[7:9, 7:9] = vramp(nm, 5, contrast=0.4)[0]
        out[nm] = t

    # --------------------------------------------------------------- crystals
    am = make_ramp((150, 100, 220), 5, 0.4)
    for nm, hgt, cnt in (("small_amethyst_bud", 4, 2), ("medium_amethyst_bud", 6, 3), ("large_amethyst_bud", 9, 4),
                         ("amethyst_cluster", 13, 5)):
        if nm not in STATS:
            continue
        t = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=30, bump=1.0)
        r = rng_of(nm)
        xs = np.linspace(4, 11, cnt).astype(int) if cnt > 1 else [7]
        for i, x in enumerate(xs):
            h = max(2, hgt - abs(i - cnt // 2) * 2 - int(r.integers(0, 2)))
            for k in range(h):
                y = 15 - k
                w = 1 if k > h - 3 else 2
                for dx in range(w):
                    c = am[4] if dx == 0 and k > 0 else am[2]
                    if k == h - 1:
                        c = (244, 232, 255)
                    if dx == w - 1 and w > 1:
                        c = am[1]
                    t.rgb[y, x + dx] = c
                    t.alpha[y, x + dx] = 255
                    t.height[y, x + dx] = 0.9
        t.emis = np.where(t.alpha > 0, 25, 0)
        out[nm] = t

    # ---------------------------------------------------------------- extras
    if "pale_moss_block" in STATS:
        out["pale_moss_block"] = P.turf("pale_moss", vramp("pale_moss_block", 5, contrast=0.3), sss=60, blades=34)
    if "resin_block" in STATS:
        out["resin_block"] = P.flat("resin", vramp("resin_block", 5, contrast=0.24), "smooth", rough=60, amount=0.8)
        rr = vramp("resin_bricks", 5, contrast=0.26)
        out["resin_bricks"] = P.bricks("resin_bricks", rr, [rr[0], shift(rr[0], dv=0.05)], rows=4, cols=2, rough=80)
    for i in range(4):
        nm = f"frosted_ice_{i}"
        if nm in STATS:
            t = P.rock("frosted_ice", make_ramp((150, 190, 250), 5, 0.14, warm=0.02), "smooth", cracks=3 + i * 4, rough=25, bump=0.6)
            out[nm] = t
    # cobweb: four spokes and two thin diamond-shaped rings
    wb = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=160, bump=0.4)
    silk = [(206, 210, 218), (236, 240, 246), (255, 255, 255)]
    spokes = (xx == yy) | (xx == 15 - yy) | (xx == 7) | (yy == 8)
    man = np.abs(xx - 7) + np.abs(yy - 8)
    rings = (man == 6) & ~((xx == 7) | (yy == 8))
    wb.rgb = np.where(rings[..., None], np.array(silk[0], np.uint8), wb.rgb)
    wb.rgb = np.where(spokes[..., None], np.array(silk[1], np.uint8), wb.rgb)
    wb.rgb = np.where((spokes & rings)[..., None], np.array(silk[2], np.uint8), wb.rgb)
    wb.alpha = np.where(spokes | rings, 255, 0).astype(np.uint8)
    wb.height = np.where(spokes | rings, 0.7, 0.0)
    out["web"] = wb
