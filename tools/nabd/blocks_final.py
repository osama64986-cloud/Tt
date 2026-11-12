"""The last overworld blocks: pottery faces, dripleaf, azalea, petals and
wildflowers, pitcher crop, bamboo pieces, shelves, dried ghast, bubble
columns and a few leftovers.  Model-bound textures are painted inside the
model's layout mask (only the layout is taken from the game, never pixels)."""
import math

import numpy as np

from . import painters as P
from .blocks_plants import Sprite
from .blocks_rest import shaded
from .core import N, STATS, Tex, fbm, make_ramp, mix, paint, paint_idx, rng_of, shift, stack_frames, vbase, vramp

yy, xx = np.mgrid[0:N, 0:N]

# our own pottery motifs, picked per pattern name
def motif(kind, w, h):
    m = np.zeros((h, w), bool)
    Y, X = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2, (h - 1) / 2 + 1
    d = np.hypot(X - cx, Y - cy)
    a = np.arctan2(Y - cy, X - cx)
    if kind == 0:   m = (np.abs(d - 3.2) < 0.6)                                   # ring
    elif kind == 1: m = (np.abs(np.abs(X - cx) - (Y - cy + 3)) < 0.6) & (Y > cy - 4) & (Y < cy + 2)   # chevron
    elif kind == 2: m = ((np.abs(X - cx) < 0.6) | (np.abs(Y - cy) < 0.6)) & (d < 4)                    # cross
    elif kind == 3: m = (np.abs(((a * 3 / math.pi) % 2) - 1) < 0.35) & (d < 4) & (d > 1)             # star
    elif kind == 4: m = (np.abs(np.sin(X * 0.9) * 1.5 + cy - Y) < 0.6)                                # wave
    elif kind == 5: m = (np.abs(d - 1.5) < 0.6) | (np.abs(d - 3.8) < 0.5)                              # double ring
    elif kind == 6: m = (np.abs((d - a * 0.9) % 2.4 - 1.2) < 0.45) & (d < 4.5)                       # spiral
    else:           m = ((X + Y) % 3 == 0) & (d < 4)                                                     # dots
    return m


def build(out, flip, variations):
    def put(name, tex):
        if name in STATS and tex is not None:
            out[name] = tex

    clay = make_ramp((176, 96, 64), 5, 0.36)
    ink = (84, 40, 26)
    pats = sorted(k for k in STATS if k.endswith("_pottery_pattern"))
    for i, nm in enumerate(pats):
        t = shaded(nm, clay, rough=200)
        h, w = t.mask.shape
        m = motif(i % 8, w, h) & t.mask & (t.idx == 2)
        t.rgb = np.where(m[..., None], np.array(ink, np.uint8), t.rgb)
        t.height = np.where(m, 0.2, t.height)
        out[nm] = t

    leaf = make_ramp((90, 160, 60), 5, 0.42)
    stem = make_ramp((70, 120, 50), 5, 0.4)
    for nm in ("big_dripleaf_top", "big_dripleaf_side1", "big_dripleaf_side2", "small_dripleaf_top", "small_dripleaf_side"):
        put(nm, shaded(nm, leaf, sss=120) if nm in STATS else None)
    for nm in ("big_dripleaf_stem", "small_dripleaf_stem_bottom", "small_dripleaf_stem_top"):
        put(nm, shaded(nm, stem, sss=80) if nm in STATS else None)

    az = vramp("azalea_leaves", 5, contrast=0.4)
    pink = [(214, 96, 186), (240, 150, 220), (255, 214, 246)]
    for nm in ("azalea_side", "azalea_plant", "potted_azalea_bush_side", "potted_azalea_bush_top", "potted_azalea_bush_plant",
               "flowering_azalea_side", "potted_flowering_azalea_bush_side", "potted_flowering_azalea_bush_top",
               "potted_flowering_azalea_bush_plant"):
        if nm not in STATS:
            continue
        t = shaded(nm, az if "plant" not in nm else make_ramp((110, 90, 60), 5, 0.4), sss=100)
        if "flowering" in nm and "plant" not in nm:
            r = rng_of(nm)
            for _ in range(6):
                x, y = int(r.integers(0, t.w)), int(r.integers(0, t.h))
                if t.mask[y, x]:
                    t.rgb[y, x] = pink[int(r.integers(0, 3))]
        out[nm] = t
    for nm, col in (("crimson_roots_pot", (150, 20, 50)), ("warped_roots_pot", (30, 150, 130))):
        put(nm, shaded(nm, make_ramp(col, 5, 0.45)) if nm in STATS else None)

    for nm, col in (("pink_petals", (240, 160, 200)), ("wildflowers", (250, 214, 80)), ("leaf_litter", None)):
        if nm not in STATS:
            continue
        ramp = make_ramp(col, 5, 0.36) if col else vramp(nm, 5, grey=True, contrast=0.4)
        t = shaded(nm, ramp, sss=60)
        if nm == "wildflowers":
            r = rng_of("wild")
            for _ in range(8):
                x, y = int(r.integers(0, N)), int(r.integers(0, N))
                if t.mask[y, x]:
                    t.rgb[y, x] = [(240, 240, 250), (170, 120, 230), (255, 140, 60)][int(r.integers(0, 3))]
        out[nm] = t
    for nm in ("pink_petals_stem", "wildflowers_stem", "eyeblossom_stem_blooming"):
        put(nm, shaded(nm, stem) if nm in STATS else None)
    if "eyeblossom_eyes_blooming" in STATS:
        t = shaded("eyeblossom_eyes_blooming", make_ramp((255, 150, 40), 5, 0.3))
        t.emis = np.where(t.mask, 230, 0)
        out["eyeblossom_eyes_blooming"] = t
    for nm in ("spore_blossom", "spore_blossom_base"):
        put(nm, shaded(nm, make_ramp((230, 110, 170), 5, 0.4) if nm == "spore_blossom" else make_ramp((70, 120, 50), 5, 0.4), sss=100) if nm in STATS else None)
    put("mangrove_propagule_hanging", shaded("mangrove_propagule_hanging", leaf) if "mangrove_propagule_hanging" in STATS else None)

    teal, pod = make_ramp((70, 150, 150), 5, 0.42), make_ramp((150, 110, 200), 5, 0.4)
    for nm in [k for k in STATS if k.startswith("pitcher_crop")]:
        t = shaded(nm, teal, sss=100)
        if "top" in nm or "stage_4" in nm:
            r = rng_of(nm)
            for _ in range(5):
                x, y = int(r.integers(0, t.w)), int(r.integers(0, t.h // 2))
                if t.mask[y, x]:
                    t.rgb[y, x] = pod[3]
        out[nm] = t

    bam = vramp("bamboo_block", 5, contrast=0.36)
    bamleaf = make_ramp((110, 170, 60), 5, 0.42)
    if "bamboo_stem" in STATS:
        t = P.stripped("bamboo_stem", bam)
        for y0 in (5, 12):
            t.rgb[y0] = bam[1]
            t.rgb[y0 + 1] = bam[4]
        out["bamboo_stem"] = t
    for nm in ("bamboo_leaf", "bamboo_singleleaf", "bamboo_small_leaf", "bamboo_sapling"):
        put(nm, shaded(nm, bamleaf, sss=120) if nm in STATS else None)
    for nm in ("bamboo_fence", "bamboo_fence_gate"):
        put(nm, shaded(nm, vramp("bamboo_planks", 5, contrast=0.32)) if nm in STATS else None)

    # shelves: opaque 32x32 plank sheets in each wood's colour
    woods = {"oak": "planks_oak", "spruce": "planks_spruce", "birch": "planks_birch", "jungle": "planks_jungle",
             "acacia": "planks_acacia", "dark_oak": "planks_big_oak", "cherry": "cherry_planks", "mangrove": "mangrove_planks",
             "pale_oak": "pale_oak_planks", "poplar": "poplar_planks", "bamboo": "bamboo_planks",
             "crimson": "huge_fungus/crimson_planks", "warped": "huge_fungus/warped_planks"}
    for w, pl in woods.items():
        nm = f"{w}_shelf"
        if nm in STATS and pl in STATS:
            a = P.planks(nm + "_a", vramp(pl, 5, contrast=0.28), boards=4, nails=False)
            b = P.planks(nm + "_b", vramp(pl, 5, contrast=0.28), boards=4, nails=False)
            rgb = np.vstack([np.hstack([a.rgb, b.rgb]), np.hstack([b.rgb, a.rgb])])
            hgt = np.vstack([np.hstack([a.height, b.height]), np.hstack([b.height, a.height])])
            out[nm] = Tex(rgb, hgt, rough=205)
    for nm, col in (("shelf_mushroom_large", (170, 120, 80)), ("shelf_mushroom_small", (190, 140, 96))):
        if nm in STATS:
            w, h = STATS[nm]["size"]
            if "mask" in STATS[nm]:
                out[nm] = shaded(nm, make_ramp(col, 5, 0.36))

    # dried ghast: pale, sleepy little ghast faces
    ghost = make_ramp((214, 206, 196), 5, 0.3)
    for nm in [k for k in STATS if k.startswith("dried_ghast_state_")]:
        if "mask" not in STATS[nm] and STATS[nm]["size"] != [16, 16]:
            continue
        t = shaded(nm, ghost, rough=200) if "mask" in STATS[nm] else Tex(paint_idx(np.full((N, N), 2), ghost), None)
        if nm.endswith("_front") and "mask" in STATS[nm]:
            ys, xs = np.nonzero(t.mask)
            if len(xs):
                cy, x0, x1 = int(ys.mean()) - 1, xs.min(), xs.max()
                for ex in (x0 + (x1 - x0) // 3, x0 + 2 * (x1 - x0) // 3):          # closed eyes
                    for k in (-1, 0, 1):
                        if 0 <= ex + k < t.w and t.mask[cy, ex + k]:
                            t.rgb[cy, ex + k] = (90, 84, 80)
        out[nm] = t

    # bubble columns: our own rising bubbles, one loop per strip
    def bubbles(nm, rising=True):
        w, h = STATS[nm]["size"]
        n = h // w
        r = rng_of(nm)
        seeds = [(r.random() * w, r.random() * w, 0.8 + r.random() * 1.2) for _ in range(max(3, w // 4))]
        fr = []
        for f in range(n):
            rgb = np.zeros((w, w, 3), np.uint8)
            al = np.zeros((w, w), np.uint8)
            for (bx, by, rad) in seeds:
                y = (by - (f / n) * w * (1 if rising else -1)) % w
                Y, X = np.mgrid[0:w, 0:w]
                d = np.hypot(X - bx, Y - y)
                ring = np.abs(d - rad) < 0.6
                rgb[ring] = (220, 240, 255)
                al[ring] = 200
                hi = (np.abs(X - (bx - rad * 0.5)) < 0.5) & (np.abs(Y - (y - rad * 0.5)) < 0.5)
                rgb[hi] = (255, 255, 255)
                al[hi] = 255
            fr.append(Tex(rgb, None, alpha=al, rough=20))
        return stack_frames(fr)
    for nm in [k for k in STATS if k.startswith("bubble_column_")]:
        out[nm] = bubbles(nm, rising="down" not in nm)

    for nm in ("stonecutter2_side", "stonecutter2_saw"):
        put(nm, shaded(nm, make_ramp((140, 144, 154), 5, 0.4), metal=200) if nm in STATS and "mask" in STATS[nm] else None)
    if "straw_bed" in STATS and "mask" in STATS["straw_bed"]:
        out["straw_bed"] = shaded("straw_bed", make_ramp((214, 180, 80), 5, 0.36))
    if "barrier" in STATS:
        t = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=100)
        d = np.hypot(xx - 7.5, yy - 7.5)
        ring = (np.abs(d - 6) < 0.9) | ((np.abs(xx - yy) < 1) & (d < 6))
        t.rgb[ring] = (220, 40, 40)
        t.alpha[ring] = 255
        out["barrier"] = t


# ------------------------------------------------------------------ lanterns
# The lantern model reads four regions from its texture: cap (rows 0-1,
# x1-4), side (rows 2-8, x0-5), top/bottom (rows 9-14, x0-5) and the hanger
# (x11-13).  Each region is drawn on its own: dark metal frame, glowing glass.
def lantern_frame(frame_ramp, glow, level):
    rgb = np.zeros((N, N, 3), np.uint8)
    al = np.zeros((N, N), np.uint8)
    emis = np.zeros((N, N))
    hgt = np.zeros((N, N))

    def px(x, y, c, e=0, h=0.6):
        rgb[y, x] = c
        al[y, x] = 255
        emis[y, x] = e
        hgt[y, x] = h
    fr = frame_ramp
    for x in range(1, 5):                                  # cap
        px(x, 0, fr[4] if x < 4 else fr[3], h=0.9)
        px(x, 1, fr[2] if x < 4 else fr[1], h=0.8)
    for y in range(2, 9):                                  # side: frame and glass
        for x in range(0, 6):
            edge = x in (0, 5) or y in (2, 8)
            if edge:
                c = fr[3] if (x == 0 or y == 2) else fr[1]
                px(x, y, c, h=0.9)
            else:
                g = glow[min(3, max(0, level + (1 if (x in (2, 3) and y in (4, 5, 6)) else 0) - (1 if y == 7 else 0)))]
                px(x, y, g, e=230, h=0.5)
    for y in range(9, 15):                                 # top and bottom plate
        for x in range(0, 6):
            ring = x in (0, 5) or y in (9, 14)
            if ring:
                px(x, y, fr[3] if (x == 0 or y == 9) else fr[1], h=0.9)
            elif x in (2, 3) and y in (11, 12):
                px(x, y, glow[min(3, level + 1)], e=200, h=0.5)         # glow seen through the plate
            else:
                px(x, y, fr[2], h=0.7)
    for (x, y) in ((11, 1), (12, 1), (13, 1), (11, 2), (13, 2), (11, 3), (13, 3), (11, 4), (12, 4), (13, 4),
                   (11, 6), (13, 6), (11, 7), (12, 7), (13, 7), (11, 10), (12, 10), (13, 10), (11, 11), (13, 11)):
        px(x, y, fr[3] if x == 11 else fr[1], h=0.8)       # hanger links
    t = Tex(rgb, hgt, alpha=al, rough=110, metal=np.where(emis > 0, 0, 200), bump=0.8)
    t.emis = emis
    return t


_build_final = build


def build(out, flip, variations):          # noqa: F811
    _build_final(out, flip, variations)
    warm = [(214, 120, 30), (250, 170, 50), (255, 214, 110), (255, 246, 190)]
    cool = [(30, 130, 150), (70, 200, 220), (150, 240, 245), (225, 255, 255)]
    green = [(40, 150, 90), (90, 210, 140), (160, 245, 190), (225, 255, 235)]
    dark = make_ramp((64, 66, 80), 5, 0.5)
    for nm, glow, metal in [("lantern", warm, dark), ("soul_lantern", cool, dark)] + \
            [(p + "copper_lantern", green, vramp("copper_block" if p == "" else p + "copper", 5, contrast=0.36))
             for p in ("", "exposed_", "weathered_", "oxidized_")]:
        if nm in STATS:
            n = STATS[nm]["size"][1] // N
            out[nm] = stack_frames([lantern_frame(metal, glow, [1, 2, 1, 0][f % 4]) for f in range(n)])

    # shelves: upper half is the plank top, lower half the shelf front with two recessed slots
    woods = {"oak": "planks_oak", "spruce": "planks_spruce", "birch": "planks_birch", "jungle": "planks_jungle",
             "acacia": "planks_acacia", "dark_oak": "planks_big_oak", "cherry": "cherry_planks", "mangrove": "mangrove_planks",
             "pale_oak": "pale_oak_planks", "poplar": "poplar_planks", "bamboo": "bamboo_planks",
             "crimson": "huge_fungus/crimson_planks", "warped": "huge_fungus/warped_planks"}
    for w, pl in woods.items():
        nm = f"{w}_shelf"
        if nm not in STATS or pl not in STATS:
            continue
        ramp = vramp(pl, 5, contrast=0.3)
        a = P.planks(nm + "_a", ramp, boards=4, nails=False)
        b = P.planks(nm + "_b", ramp, boards=4, nails=False)
        top = np.hstack([a.rgb, b.rgb])
        front = np.hstack([b.rgb, a.rgb]).copy()
        hf = np.full((16, 32), 0.7)
        for y0, y1 in ((0, 6), (8, 14)):                  # two recessed slots
            front[y0:y1 + 1, 1:31] = (np.array(ramp[0]) * 0.55).astype(np.uint8)
            front[y0, 1:31] = (np.array(ramp[0]) * 0.4).astype(np.uint8)       # shadow under the lip
            hf[y0:y1 + 1, 1:31] = 0.1
            front[y1 + 1, :] = ramp[4]                                         # lit shelf lip
            hf[y1 + 1, :] = 1.0
        for x in (0, 31):
            front[:, x] = ramp[1]
        rgb = np.vstack([top, front])
        hgt = np.vstack([np.hstack([a.height, b.height]), hf])
        out[nm] = Tex(rgb, hgt, rough=205)

    # pitcher crop: veined teal leaves; flowering stages carry a pink-violet bloom
    for nm in [k for k in STATS if k.startswith("pitcher_crop")]:
        t = shaded(nm, make_ramp((70, 150, 150), 5, 0.42), sss=100)
        h, w = t.mask.shape
        Y, X = np.mgrid[0:h, 0:w]
        vein = t.mask & (t.idx == 2) & ((X + Y) % 4 == 0)
        t.rgb = np.where(vein[..., None], np.array((44, 104, 104), np.uint8), t.rgb)
        if "top" in nm or "stage_4" in nm or "stage_3" in nm:
            bloom = t.mask & (Y < h // 2) & ((X * 3 + Y) % 5 == 0)
            t.rgb = np.where(bloom[..., None], np.array((190, 110, 220), np.uint8), t.rgb)
        out[nm] = t


_build_final2 = build


def build(out, flip, variations):          # noqa: F811
    _build_final2(out, flip, variations)
    # 32x32 opaque sheets: shelf mushrooms and the dried ghast's tentacles
    def sheet32(seed, ramp, count, dome=0.5):
        a = P.cells(seed + "a", ramp, count, dome=dome)
        b = P.cells(seed + "b", ramp, count, dome=dome)
        rgb = np.vstack([np.hstack([a.rgb, b.rgb]), np.hstack([b.rgb, a.rgb])])
        hgt = np.vstack([np.hstack([a.height, b.height]), np.hstack([b.height, a.height])])
        return Tex(rgb, hgt, rough=200)
    for nm, col in (("shelf_mushroom_large", (176, 120, 76)), ("shelf_mushroom_small", (196, 146, 98))):
        if nm in STATS and STATS[nm]["size"] == [32, 32]:
            out[nm] = sheet32(nm, make_ramp(col, 6, 0.4), 8)
    ghost = make_ramp((214, 206, 196), 6, 0.3)
    for st in range(1, 5):
        nm = f"dried_ghast_state_{st}_tentacles"
        if nm in STATS and STATS[nm]["size"] == [32, 32]:
            t = sheet32(nm, ghost, 6, dome=0.3)
            for x in range(2, 32, 4):                            # soft vertical folds
                t.rgb[:, x] = (t.rgb[:, x] * 0.85).astype(np.uint8)
            out[nm] = t
    # fireflies: tiny glowing specks that blink in and out
    if "firefly_bush_firefly" in STATS:
        w, h = STATS["firefly_bush_firefly"]["size"]
        n = h // w
        r = rng_of("fireflies")
        flies = [(int(r.integers(1, w - 1)), int(r.integers(1, w - 1)), int(r.integers(0, n))) for _ in range(4)]
        fr = []
        for f in range(n):
            rgb = np.zeros((w, w, 3), np.uint8)
            al = np.zeros((w, w), np.uint8)
            for (x, y, ph) in flies:
                lvl = (f - ph) % n
                if lvl < 4:
                    rgb[y, x] = [(255, 250, 170), (255, 240, 120), (240, 210, 80), (200, 170, 60)][lvl]
                    al[y, x] = 255
            t = Tex(rgb, None, alpha=al, rough=255)
            t.emis = np.where(al > 0, 255, 0)
            fr.append(t)
        out["firefly_bush_firefly"] = stack_frames(fr)


_build_final3 = build


def bamboo_end(ramp):
    """Cut end of a bundle of canes: a 3x3 grid of hollow cane ends."""
    idx = np.full((N, N), 1)
    hgt = np.full((N, N), 0.3)
    for cy in (2.5, 7.5, 12.5):
        for cx in (2.5, 7.5, 12.5):
            d = np.hypot(xx - cx, yy - cy)
            wall = (d <= 2.4) & (d > 1.2)
            hole = d <= 1.2
            lit = wall & ((xx - cx) + (yy - cy) < 0)
            idx = np.where(wall, 3, idx)
            idx = np.where(lit, 4, idx)
            idx = np.where(hole, 0, idx)
            hgt = np.where(wall, 0.9, np.where(hole, 0.1, hgt))
    return Tex(paint_idx(idx, ramp), hgt, rough=180, bump=1.2)


def build(out, flip, variations):          # noqa: F811
    _build_final3(out, flip, variations)
    if "bamboo_block_top" in STATS:
        out["bamboo_block_top"] = bamboo_end(vramp("bamboo_block", 5, contrast=0.4))
    if "stripped_bamboo_block_top" in STATS:
        out["stripped_bamboo_block_top"] = bamboo_end(vramp("stripped_bamboo_block", 5, contrast=0.36))
