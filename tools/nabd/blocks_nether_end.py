"""The Nether and the End, painted in the same house style."""
import numpy as np

from . import painters as P
from .blocks_plants import Sprite, mushroom
from .blocks_village import door, frame_panel, trapdoor, has_holes
from .core import (N, STATS, Tex, dashes, fbm, make_ramp, mix, norm01, paint, paint_idx, plane, rng_of, shift,
                   stack_frames, vbase, vramp, white)

yy, xx = np.mgrid[0:N, 0:N]
GOLD = [(160, 104, 16), (214, 156, 28), (246, 204, 52), (255, 232, 110), (255, 250, 190)]
QUARTZ = [(176, 160, 150), (208, 196, 186), (232, 224, 214), (246, 240, 232), (255, 252, 246)]


def frames_of(name):
    w, h = STATS[name]["size"]
    return max(1, h // w)


def netherrack():
    """Chunky rounded lumps with a clear rim light: reads as rock, not noise."""
    t = P.cells("netherrack", vramp("netherrack", 6, contrast=0.5), 8, dome=0.6)
    r = rng_of("netherrack_pits")
    dark = vramp("netherrack", 6, contrast=0.5)[0]
    for _ in range(5):                                   # little heat pits
        x, y = int(r.integers(N)), int(r.integers(N))
        if t.height[y, x] > 0.3:
            t.rgb[y, x] = dark
            t.height[y, x] = 0.15
    return t


def fluted(name, ramp, rough=150, every=4):
    """Pillar face: vertical flutes with a lit left edge."""
    mid = len(ramp) // 2
    idx = np.full((N, N), mid)
    idx = np.where(xx % every == every - 1, mid - 2, idx)
    idx = np.where(xx % every == 0, mid + 1, idx)
    idx = np.where(xx % every == every - 2, mid - 1, idx)
    idx[0, :] = np.minimum(idx[0, :] + 1, len(ramp) - 1)
    idx[15, :] = np.maximum(idx[15, :] - 1, 0)
    hgt = np.where(xx % every == every - 1, 0.2, 0.75)
    return Tex(paint_idx(idx, ramp), hgt, rough=rough, bump=1.1)


def fungus_wood(out, kind, stem_side, stem_top, planks, strip_side, strip_top, door_lo, door_up, trap, glow):
    """Nether wood: spore-pored boards, ridged stems with three glowing veins
    that pulse upwards, and a glowing heart in the cut end."""
    gl = make_ramp(glow, 4, 0.55, sat=1.0, lift=0.0)
    pr = vramp(planks, 5, contrast=0.3)

    def pores(t, ramp, count, seed):
        r = rng_of(seed)
        for _ in range(count):
            x, y = int(r.integers(1, N - 2)), int(r.integers(N))
            if y % 4 == 3:
                continue
            t.rgb[y, x] = ramp[0]
            t.rgb[y, x + 1] = ramp[4]
            t.height[y, x] = 0.15
        return t
    out[planks] = pores(P.planks("planks_" + kind, pr), pr, 9, "pores_" + kind)
    wood = vramp(strip_side, 5, contrast=0.26)
    br = vramp(stem_side, 5, contrast=0.5)
    base = P.bark("stem_" + kind, br, ridges=9)
    r = rng_of("veins_" + kind)
    vein = np.zeros((N, N), bool)
    for x0 in (2, 8, 13):
        half, x = [], x0
        for y in range(N // 2):
            if 0 < y and r.random() < 0.4:
                x = int(np.clip(x + r.choice([-1, 1]), x0 - 2, x0 + 2))
            half.append(x)
        for y, x in enumerate(half + half[::-1]):            # mirrored so the vein tiles vertically
            vein[y, x % N] = True
    shade = np.roll(vein, 1, 1) & ~vein
    n = frames_of(stem_side)
    frames = []
    for f in range(n):
        t = base.copy()
        phase = ((yy + f * (N / n)) % N) / N
        lvl = np.clip((np.sin(phase * 2 * np.pi) * 0.5 + 0.5) * 3.99, 0, 3).astype(int)
        t.rgb = np.where(shade[..., None], np.array(br[0], np.uint8), t.rgb)
        t.rgb = np.where(vein[..., None], np.array(gl, np.uint8)[lvl], t.rgb)
        t.emis = np.where(vein, 90 + lvl * 50, 0)
        t.height = np.where(vein, 0.95, np.where(shade, 0.2, t.height))
        frames.append(t)
    out[stem_side] = stack_frames(frames)
    top = P.log_top("top_" + kind, wood, br)
    heart = (xx >= 6) & (xx <= 9) & (yy >= 6) & (yy <= 9)
    core = (xx >= 7) & (xx <= 8) & (yy >= 7) & (yy <= 8)
    top.rgb = np.where(heart[..., None], np.array(gl[1], np.uint8), top.rgb)
    top.rgb = np.where(core[..., None], np.array(gl[3], np.uint8), top.rgb)
    top.emis = np.where(core, 230, np.where(heart, 120, 0))
    out[stem_top] = top
    out[strip_side] = pores(P.stripped("strip_" + kind, wood), wood, 6, "strip_pores_" + kind)
    out[strip_top] = P.log_top("top_" + kind, wood, wood)
    up, lo = door(kind, pr, "panes" if kind == "crimson" else "lattice", has_holes(door_up))
    tr = trapdoor(kind, pr, "grid" if kind == "crimson" else "lattice", has_holes(trap))
    for t in (up, lo, tr):                                   # glowing studs instead of iron ones
        emis = np.zeros((N, N))
        for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
            t.rgb[y, x] = gl[3]
            emis[y, x] = 220
        t.emis = emis
    out[door_up], out[door_lo], out[trap] = up, lo, tr


def vine(name, ramp, grow_up, tip, glow=None):
    """Nether vines: one wandering strand with paired leaves."""
    s = Sprite()
    r = rng_of(name)
    x = 7
    ys = range(15, -1, -1) if grow_up else range(0, 16)
    for i, y in enumerate(ys):
        if tip and i > 9:
            break
        if r.random() < 0.3:
            x = int(np.clip(x + r.choice([-1, 1]), 4, 11))
        s.px(x, y, ramp[1 if i % 2 else 2], 0.5)
        if i % 3 == 1:
            d = 1 if (i // 3) % 2 else -1
            s.px(x + d, y, ramp[3], 0.8)
            s.px(x + 2 * d, y + (-1 if grow_up else 1), ramp[4], 0.85, emis=40 if glow else 0)
    if tip:
        y = ys[min(9, len(ys) - 1)]
        s.px(x, y, glow or ramp[4], 0.9, emis=120 if glow else 0)
    return s.tex(sss=80)


def build(out, flip, variations):
    # ------------------------------------------------------------- NETHER
    nb = make_ramp(shift(vbase("nether_brick"), dv=0.08, ds=0.06), 5, 0.42)
    nm = [shift(nb[0], dv=-0.03), nb[0]]
    out["nether_brick"] = P.bricks("nether_brick", nb, nm, rows=4, cols=2)
    out["cracked_nether_bricks"] = P.bricks("nether_brick", nb, nm, rows=4, cols=2, crack=4, chip=0.06)
    out["chiseled_nether_bricks"] = P.slab_face("chiseled_nether", nb, border=1, inset=4, vary=0.12, rough=180)
    rb = make_ramp(shift(vbase("red_nether_brick"), dv=0.07), 5, 0.42)
    out["red_nether_brick"] = P.bricks("nether_brick", rb, [shift(rb[0], dv=-0.04), rb[0]], rows=4, cols=2)
    out["nether_wart_block"] = P.cells("nether_wart_block", vramp("nether_wart_block", 6, contrast=0.4), 13, dome=0.6, bump=1.4)
    out["warped_wart_block"] = P.cells("warped_wart_block", vramp("warped_wart_block", 6, contrast=0.4), 13, dome=0.6, bump=1.4)
    out["soul_soil"] = P.soil("soul_soil", vramp("soul_soil", 5, contrast=0.3), pebbles=0)

    rack = netherrack()
    q = P.ore(rack, P.ore_layout("ore:quartz", "chunk", 6), QUARTZ, metal=0, gem_rough=60)
    out["quartz_ore"] = q
    cl = P.ore_layout("ore:nether_gold", "nugget", 6)
    g = P.ore(rack, cl, GOLD, metal=200, gem_rough=70)
    out["nether_gold_ore"] = g
    frames = [P.ore(rack, cl, GOLD, metal=200, gem_rough=70, sparkle={f}) if f < len(cl) else g for f in range(12)]
    out["nabd/nether_gold_ore_shimmer"] = stack_frames(frames)
    flip["nether_gold_ore"] = dict(strip="nabd/nether_gold_ore_shimmer", ticks=5, frames=12)

    qz = make_ramp(shift(vbase("quartz_block_side"), dv=-0.04), 5, 0.22, sat=1.0, lift=0.0)   # readable carving on near-white
    for nm_ in ("quartz_block_side", "quartz_block_top", "quartz_block_bottom"):
        out[nm_] = P.slab_face(nm_, qz, border=1, vary=0.08, rough=90)
    out["quartz_block_chiseled"] = P.slab_face("quartz_chiseled", qz, border=1, inset=4, vary=0.06, rough=90)
    out["quartz_block_chiseled_top"] = P.slab_face("quartz_chiseled_top", qz, border=2, vary=0.06, rough=90)
    out["quartz_block_lines"] = fluted("quartz_lines", qz, rough=90)
    out["quartz_block_lines_top"] = P.slab_face("quartz_lines_top", qz, border=1, inset=2, vary=0.06, rough=90)
    out["quartz_bricks"] = P.bricks("quartz_bricks", qz, [qz[0], shift(qz[0], dv=0.02)], rows=2, cols=1, rough=90, vary=0.08)

    bs = vramp("basalt_side", 5, contrast=0.3)
    out["basalt_side"] = P.bark("basalt_side", bs, ridges=7, bump=1.3)        # cooled columns
    out["basalt_top"] = P.cells("basalt_top", vramp("basalt_top", 6, contrast=0.34), 7, dome=0.4)
    out["polished_basalt_side"] = fluted("polished_basalt", vramp("polished_basalt_side", 5, contrast=0.26), every=8)
    out["polished_basalt_top"] = P.slab_face("polished_basalt_top", vramp("polished_basalt_top", 5, contrast=0.24), border=2, vary=0.14)

    bk = vramp("blackstone", 6, contrast=0.5)
    black = P.cells("blackstone", bk, 8, dome=0.45)
    out["blackstone"] = black
    out["blackstone_top"] = P.rock("blackstone_top", vramp("blackstone_top", 5, contrast=0.4), "smooth", cracks=3)
    pb = vramp("polished_blackstone", 5, contrast=0.36)
    pmort = [shift(pb[0], dv=-0.04), pb[0]]
    out["polished_blackstone"] = P.slab_face("polished_blackstone", pb, border=1, vary=0.16)
    out["polished_blackstone_bricks"] = P.bricks("pb_bricks", pb, pmort, rows=2, cols=1)
    out["cracked_polished_blackstone_bricks"] = P.bricks("pb_bricks", pb, pmort, rows=2, cols=1, crack=4, chip=0.06)
    out["chiseled_polished_blackstone"] = P.slab_face("pb_chiseled", pb, border=1, inset=4, vary=0.12)
    out["gilded_blackstone"] = P.ore(black, P.ore_layout("ore:gilded", "fleck", 7), GOLD, metal=220, gem_rough=60)

    for kind in ("crimson", "warped"):
        top = P.turf(f"{kind}_nylium", vramp(f"{kind}_nylium_top", 5, contrast=0.36), blades=30)
        out[f"{kind}_nylium_top"] = top
        out[f"{kind}_nylium_side"] = P.top_over(f"{kind}_nylium_side", rack, top, depth=4, extra=2)
    fungus_wood(out, "crimson", "huge_fungus/crimson_log_side", "huge_fungus/crimson_log_top", "huge_fungus/crimson_planks",
                "huge_fungus/stripped_crimson_stem_side", "huge_fungus/stripped_crimson_stem_top",
                "huge_fungus/crimson_door_lower", "huge_fungus/crimson_door_top", "huge_fungus/crimson_trapdoor",
                (255, 110, 60))
    fungus_wood(out, "warped", "huge_fungus/warped_stem_side", "huge_fungus/warped_stem_top", "huge_fungus/warped_planks",
                "huge_fungus/stripped_warped_stem_side", "huge_fungus/stripped_warped_stem_top",
                "huge_fungus/warped_door_lower", "huge_fungus/warped_door_top", "huge_fungus/warped_trapdoor",
                (60, 230, 200))

    sh = P.cells("shroomlight", vramp("shroomlight", 6, contrast=0.3), 9, dome=0.5)
    sh.emis = np.clip((sh.height - 0.15) * 300, 0, 255)
    sh.rough = 140
    out["shroomlight"] = sh
    # ancient debris (the netherite ore): dark crusted rock wrapped in pale
    # scrap-metal bands on the side and a bold square spiral on top
    body = [(40, 24, 20), (58, 36, 30), (80, 52, 44), (104, 70, 58), (130, 92, 78)]
    plate = [(124, 88, 76), (168, 128, 112), (204, 168, 152), (236, 208, 194)]
    # side: the familiar idea (dark crust streaked with pale layers), drawn our
    # way - a calm brown face with a few long pale streaks, each with a soft
    # shadow underneath, and two darker grooves
    idx = np.full((N, N), 2)
    hgt = np.full((N, N), 0.5)
    r = rng_of("ancient_debris_side")
    dashes(r, idx, hgt, 3, 1, (4, 8), thick=0.0, lift=-0.15, wobble=0.1)
    streak = np.zeros((N, N), bool)
    for (y, x0, ln) in ((2, 1, 9), (5, 8, 7), (8, 2, 6), (10, 9, 6), (13, 4, 9)):
        for i in range(ln):
            streak[y + (1 if (i > ln // 2 and ln > 6) else 0), (x0 + i) % N] = True
    under = np.roll(streak, 1, 0) & ~streak
    rgb = paint_idx(idx, body)
    rgb = np.where(under[..., None], np.array(body[0], np.uint8), rgb)
    rgb = np.where(streak[..., None], np.array(plate[2], np.uint8), rgb)
    rgb = np.where((streak & ~np.roll(streak, 1, 1))[..., None], np.array(plate[3], np.uint8), rgb)
    hgt = np.where(streak, 0.9, np.where(under, 0.25, hgt))
    t = Tex(rgb, hgt, rough=np.where(streak, 100, 170), metal=np.where(streak, 140, 0), bump=1.2)
    out["ancient_debris_side"] = t
    tp = P.rock("ancient_debris_top", body, "smooth", cracks=0, rough=170)
    met = np.zeros((N, N))
    d = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))
    for rad, gap in ((6.5, (1, 1)), (3.5, (12, 12))):
        ring = np.abs(d - rad) < 0.6
        ring &= ~((np.abs(xx - gap[0]) <= 1) & (np.abs(yy - gap[1]) <= 1))      # each ring is broken once: a spiral
        lit = ring & ((yy < 7.5) | (xx < 7.5)) & ((yy - xx) < 4) & ((xx - yy) < 4 + 99 * (yy < 7.5))
        tp.rgb = np.where(ring[..., None], np.array(plate[1], np.uint8), tp.rgb)
        tp.rgb = np.where((ring & ((d - rad) < 0) & (xx + yy < 15))[..., None], np.array(plate[3], np.uint8), tp.rgb)
        tp.rgb = np.where((ring & (xx + yy > 16))[..., None], np.array(plate[0], np.uint8), tp.rgb)
        tp.height = np.where(ring, 1.0, tp.height)
        met = np.where(ring, 150, met)
    tp.rgb[7:9, 7:9] = plate[2]
    tp.rgb[7, 7] = plate[3]
    met[7:9, 7:9] = 150
    tp.metal = met
    tp.rough = np.where(met > 0, 90, 170)
    out["ancient_debris_top"] = tp

    # respawn anchor: obsidian frame, a charge gauge on the side, a swirling well on top
    ob = make_ramp((44, 30, 70), 5, 0.6, warm=0.02)
    out["respawn_anchor_bottom"] = P.slab_face("anchor_bottom", ob, border=2, vary=0.2, rough=50)
    lit = [(255, 196, 60), (255, 236, 150)]
    for lvl in range(5):
        t = P.slab_face("anchor_side", ob, border=1, vary=0.2, rough=50)
        emis = np.zeros((N, N))
        for k in range(4):
            x0 = 2 + k * 3
            on = k < lvl
            t.rgb[6:10, x0:x0 + 2] = lit[0] if on else ob[0]
            if on:
                t.rgb[6, x0:x0 + 2] = lit[1]
                emis[6:10, x0:x0 + 2] = 220
            t.height[6:10, x0:x0 + 2] = 0.2
        t.emis = emis
        out[f"respawn_anchor_side{lvl}"] = t
    off = P.slab_face("anchor_top", ob, border=2, vary=0.2, rough=50)
    well = (xx >= 3) & (xx <= 12) & (yy >= 3) & (yy <= 12)
    off.rgb = np.where(well[..., None], np.array(ob[0], np.uint8), off.rgb)
    off.height = np.where(well, 0.1, off.height)
    out["respawn_anchor_top_off"] = off
    swirl = make_ramp((130, 50, 230), 5, 0.6)
    a_lo = STATS["respawn_anchor_top"]["alpha"][0]
    n = frames_of("respawn_anchor_top")
    fr = []
    r = rng_of("anchor_swirl")
    f1, f2 = fbm(r, ((2, 1.0), (4, 0.6))), fbm(r, ((3, 1.0), (5, 0.5)))
    for f in range(n):
        ph = f / n * 2 * np.pi
        tone = np.clip(0.5 + 0.3 * np.sin(f1 * 6.28 + ph) + 0.2 * np.sin(f2 * 6.28 - 2 * ph), 0, 0.999)
        t = Tex(paint(tone, swirl), 0.4 + tone * 0.3, alpha=np.full((N, N), a_lo, np.uint8), rough=30, bump=0.5)
        t.emis = 150 + tone * 100
        fr.append(t)
    out["respawn_anchor_top"] = stack_frames(fr)

    ls = vramp("lodestone_side", 5, contrast=0.3)
    t = P.bricks("lodestone", ls, [shift(ls[0], dv=-0.04), ls[0]], rows=2, cols=1)
    t.rgb[7:9] = paint(np.where(yy[7:9] == 7, 0.85, 0.2), make_ramp((150, 154, 162), 5, 0.3))
    t.height[7:9] = 1.0
    out["lodestone_side"] = t
    lt = P.slab_face("lodestone_top", vramp("lodestone_top", 5, contrast=0.28), border=1, inset=4, vary=0.12)
    lt.rgb[7:9, 7:9] = (200, 60, 60)
    out["lodestone_top"] = lt
    go = P.rock("obsidian", make_ramp((60, 8, 20), 5, 0.6, warm=0.02), "smooth", cracks=5, rough=40)
    crack = go.height < 0.3
    go.rgb = np.where(crack[..., None], np.array((255, 90, 40), np.uint8), go.rgb)
    go.emis = np.where(crack, 220, 30)
    out["glowing_obsidian"] = go

    # nether plants
    out["crimson_fungus"] = mushroom((190, 40, 30))
    wf = mushroom((40, 150, 130))
    out["warped_fungus"] = wf
    out["crimson_roots"] = P.blades("crimson_roots", vramp("crimson_roots", 5, contrast=0.5), count=8, height=(6, 13), curl=1.6, sss=60)
    out["warped_roots"] = P.blades("warped_roots", vramp("warped_roots", 5, contrast=0.5), count=8, height=(6, 13), curl=1.6, sss=60)
    out["nether_sprouts"] = P.blades("nether_sprouts", vramp("nether_sprouts", 5, contrast=0.5), count=6, height=(2, 5), curl=1.4, sss=60)
    wart = make_ramp((170, 24, 30), 5, 0.5)
    stalk = make_ramp((90, 20, 24), 4, 0.4)
    for st in range(3):
        sp = Sprite()
        for (x, extra) in ((3, 0), (8, 1), (12, 0)):
            h = 1 + st * 2 + extra
            rad = 1 + st * 0.75
            cy = 15 - h - rad + 0.5
            for k in range(h):
                sp.px(x, 15 - k, stalk[2], 0.5)
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    if dx * dx + dy * dy <= rad * rad + 0.3:
                        tone = 2 + (dx + dy < -rad * 0.5) + (dx + dy < -rad * 1.2) - (dx + dy > rad * 0.7)
                        sp.px(x + dx, cy + dy, wart[int(np.clip(tone, 0, 4))], 0.9)
        out[f"nether_wart_stage_{st}"] = sp.tex(sss=40)
    wv, tv = vramp("weeping_vines_plant", 5, contrast=0.5), vramp("twisting_vines_base", 5, contrast=0.5)
    out["weeping_vines_plant"] = vine("weeping_body", wv, False, False)
    out["weeping_vines_base"] = vine("weeping_body", wv, False, False)
    out["weeping_vines"] = vine("weeping_tip", wv, False, True, glow=(255, 140, 60))
    out["weeping_vines_bottom"] = vine("weeping_tip", wv, False, True, glow=(255, 140, 60))
    out["twisting_vines_base"] = vine("twisting_body", tv, True, False)
    out["twisting_vines_bottom"] = vine("twisting_tip", tv, True, True, glow=(140, 255, 220))

    # ---------------------------------------------------------------- END
    es = vramp("end_stone", 5, contrast=0.3)
    mid = 2

    def cratered(seed, count, rmax=2.7, strokes=True):
        """Pale moon rock: a calm face dimpled with shallow round craters."""
        t = P.rock(seed, es, "smooth", cracks=0, rough=190) if strokes else Tex(paint_idx(np.full((N, N), mid), es), None, rough=190)
        r = rng_of(seed + ":craters")
        for _ in range(count):
            cx, cy, rad = r.random() * N, r.random() * N, r.uniform(1.4, rmax)
            dx = ((xx - cx + N / 2) % N) - N / 2
            dy = ((yy - cy + N / 2) % N) - N / 2
            d = np.hypot(dx, dy)
            pit = d <= rad
            rim = (d > rad) & (d <= rad + 1)
            t.rgb = np.where(pit[..., None], np.array(es[mid - 1], np.uint8), t.rgb)
            t.rgb = np.where((pit & (dx + dy < -rad * 0.35))[..., None], np.array(es[mid - 2], np.uint8), t.rgb)
            t.rgb = np.where((rim & (dx + dy > 0.5))[..., None], np.array(es[mid + 2], np.uint8), t.rgb)
            t.rgb = np.where((rim & (dx + dy < -0.5))[..., None], np.array(es[mid - 1], np.uint8), t.rgb)
            t.height = np.where(pit, 0.15, np.where(rim, 0.75, t.height))
        return t
    out["end_stone"] = cratered("end_stone", 6)
    eb = vramp("end_bricks", 5, contrast=0.3)
    br_ = P.bricks("end_bricks", eb, [shift(eb[0], dv=-0.1), shift(eb[0], dv=-0.06)], rows=2, cols=1, vary=0.1, chip=0.0)
    r = rng_of("end_brick_pits")
    for _ in range(4):                                       # a small crater on some bricks
        x, y = int(r.integers(2, 13)), int(r.choice([2, 3, 10, 11]))
        br_.rgb[y:y + 2, x:x + 2] = eb[1]
        br_.rgb[y, x] = eb[0]
        br_.rgb[y + 2, x:x + 2] = eb[4]
        br_.height[y:y + 2, x:x + 2] = 0.2
    out["end_bricks"] = br_

    pp = vramp("purpur_block", 5, contrast=0.34)
    pb_ = Tex(paint_idx(np.full((N, N), 2), pp), np.full((N, N), 0.6), rough=150, bump=1.1)
    for x0 in (0, 8):                                        # four bevelled tiles, each with an inset
        for y0 in (0, 8):
            frame_panel(pb_, pp, x0, y0, x0 + 7, y0 + 7, sunk=False)
            frame_panel(pb_, pp, x0 + 2, y0 + 2, x0 + 5, y0 + 5, sunk=True)
            pb_.rgb[y0 + 3:y0 + 5, x0 + 3:x0 + 5] = pp[1]
    out["purpur_block"] = pb_
    pil = fluted("purpur_pillar", vramp("purpur_pillar", 5, contrast=0.34))
    for rows_, tones in (((0, 1), (4, 1)), ((14, 15), (3, 0))):     # capital and base bands
        pil.rgb[rows_[0]] = pp[tones[0]]
        pil.rgb[rows_[1]] = pp[tones[1]]
        pil.height[rows_[0]:rows_[1] + 1] = 0.95
    out["purpur_pillar"] = pil
    ptop = Tex(paint_idx(np.full((N, N), 2), pp), np.full((N, N), 0.6), rough=150, bump=1.1)
    for inset in (0, 3, 6):
        frame_panel(ptop, pp, inset, inset, 15 - inset, 15 - inset, sunk=(inset == 3))
    out["purpur_pillar_top"] = ptop

    cp = vramp("chorus_plant", 5, contrast=0.4)
    ch = P.stripped("chorus_plant", cp, rough=170)
    for (x, y) in ((3, 3), (11, 6), (6, 11), (13, 13)):              # pale knuckles
        ch.rgb[y:y + 2, x:x + 2] = cp[3]
        ch.rgb[y, x] = cp[4]
        ch.rgb[y + 2, x:x + 2] = cp[0]
        ch.height[y:y + 2, x:x + 2] = 0.95
    out["chorus_plant"] = ch
    d = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))
    for nm_ in ("chorus_flower", "chorus_flower_dead"):
        fr_ = vramp(nm_, 5, contrast=0.5)
        layer = np.clip((d // 2).astype(int), 0, 3)                    # 0 centre .. 3 outer petals
        idx = 4 - layer
        idx = np.where((d.astype(int) % 2 == 1) & (d > 1), idx - 1, idx)   # each layer steps down at its edge
        idx = np.where(((xx == 7) | (xx == 8) | (yy == 7) | (yy == 8)) & (d > 2), np.maximum(idx - 1, 0), idx)
        t = Tex(paint_idx(idx, fr_), 1.0 - layer * 0.22, rough=160, bump=1.3)
        if nm_ == "chorus_flower":
            t.rgb[7:9, 7:9] = (252, 244, 254)
        out[nm_] = t
    eg = make_ramp((34, 20, 50), 5, 0.6, sat=1.0, lift=0.0)
    cell_x = (xx + (yy // 4 % 2) * 2) % 4
    idx = np.full((N, N), 2)
    idx = np.where(yy % 4 == 3, 0, idx)                                # lower edge of each scale
    idx = np.where((cell_x == 0) & (yy % 4 >= 1), 0, idx)              # side edge
    idx = np.where((yy % 4 == 0) & (cell_x != 0), 3, idx)              # lit crown
    de = Tex(paint_idx(idx, eg), np.where(idx == 0, 0.15, 0.7), rough=60, bump=1.3)
    glint = (yy % 4 == 0) & (cell_x == 1) & (((xx // 4) + (yy // 4)) % 3 == 0)
    de.rgb = np.where(glint[..., None], np.array((170, 90, 240), np.uint8), de.rgb)
    de.emis = np.where(glint, 90, 0)
    out["dragon_egg"] = de

    teal = vramp("endframe_top", 5, contrast=0.34)
    ft = P.slab_face("endframe_top", teal, border=2, vary=0.14, rough=120)
    sock = (xx >= 4) & (xx <= 11) & (yy >= 4) & (yy <= 11)
    ft.rgb = np.where(sock[..., None], np.array(shift(teal[0], dv=-0.08), np.uint8), ft.rgb)
    ft.height = np.where(sock, 0.1, ft.height)
    out["endframe_top"] = ft
    fs = cratered("endframe_side", 3, rmax=2.0)
    fs.rgb[3:7] = paint(np.where(yy[3:7] == 3, 0.85, np.where(yy[3:7] == 6, 0.15, 0.5)), teal)
    fs.height[3:7] = 0.95
    for x in (3, 8, 12):
        fs.rgb[5, x] = teal[4]
    fs.alpha[0:3, :] = 0                         # the frame is 13 px tall
    out["endframe_side"] = fs

    # eye of ender seated in the frame (painted inside the model's layout)
    eye = make_ramp((40, 150, 110), 5, 0.5)
    ey = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=40, bump=1.0)
    mask = np.array([[c == "1" for c in row] for row in STATS["endframe_eye"]["mask"]])
    dd = np.hypot(xx - 7.5, yy - 3.5)                                   # the 8x8 top face
    tone = np.where(dd < 1.2, 0, np.where(dd < 2.4, 4, np.where(dd < 3.6, 3, 2)))
    tone = np.where(yy >= 8, np.where(yy == 8, 3, np.where(yy == 11, 0, 1)), tone)   # side strips
    ey.rgb = np.where(mask[..., None], paint_idx(tone, eye), 0).astype(np.uint8)
    ey.alpha = np.where(mask, 255, 0).astype(np.uint8)
    ey.height = np.where(mask, 0.8, 0.0)
    ey.emis = np.where(mask & (dd < 2.4) & (yy < 8), 120, 0)
    out["endframe_eye"] = ey

    # end rod: a glowing white wand on a small dark foot
    rod = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=60, bump=0.6)
    mask = np.array([[c == "1" for c in row] for row in STATS["end_rod"]["mask"]])
    wand = mask & (xx < 2)
    cap = mask & (xx >= 2) & (yy < 2)
    foot = mask & (xx >= 2) & (yy >= 2)
    rod.rgb = np.where(wand[..., None], np.where((xx == 0)[..., None], np.array((255, 252, 244), np.uint8), np.array((236, 224, 206), np.uint8)), rod.rgb)
    rod.rgb = np.where(cap[..., None], np.array((255, 252, 244), np.uint8), rod.rgb)
    foot_r = make_ramp((132, 108, 140), 5, 0.36)
    ftone = np.where((yy == 2) | (xx == 2), 4, np.where((yy == 7) | (xx == 5), 0, 2))
    rod.rgb = np.where(foot[..., None], paint_idx(ftone, foot_r), rod.rgb)
    rod.alpha = np.where(mask, 255, 0).astype(np.uint8)
    rod.height = np.where(mask, 0.8, 0.0)
    rod.emis = np.where(wand | cap, 235, 0)
    out["end_rod"] = rod

    # ender chest faces & shulker shell tops
    ec = make_ramp((30, 52, 56), 5, 0.6)
    trim = make_ramp((70, 150, 124), 5, 0.4)
    for nm_ in ("ender_chest_front", "ender_chest_side", "ender_chest_top"):
        t = P.slab_face(nm_, ec, border=1, vary=0.2, rough=60)
        if nm_ == "ender_chest_top":
            frame_panel(t, ec, 3, 3, 12, 12)
        else:
            t.rgb[5] = ec[0]                               # lid seam
            t.rgb[6] = ec[4]
            t.height[5] = 0.1
        if nm_ == "ender_chest_front":
            t.rgb[4:8, 7:9] = trim[2]
            t.rgb[4, 7:9] = trim[4]
            t.rgb[7, 7:9] = trim[0]
            t.rgb[5, 7] = (220, 255, 236)
            t.emis = np.where((xx >= 7) & (xx <= 8) & (yy >= 4) & (yy <= 7), 120, 0)
            t.height[4:8, 7:9] = 1.0
        out[nm_] = t
    for c in ("black", "blue", "brown", "cyan", "gray", "green", "light_blue", "lime", "magenta", "orange", "pink",
              "purple", "red", "silver", "white", "yellow", "undyed"):
        nm_ = f"shulker_top_{c}"
        if nm_ not in STATS:
            continue
        sr = vramp(nm_, 5, contrast=0.34)
        t = Tex(paint_idx(np.full((N, N), 2), sr), np.full((N, N), 0.6), rough=120, bump=1.1)
        frame_panel(t, sr, 0, 0, 15, 15, sunk=False)
        frame_panel(t, sr, 3, 3, 12, 12, sunk=True)
        frame_panel(t, sr, 6, 6, 9, 9, sunk=False)
        out[nm_] = t
