"""The Nether and the End, painted in the same house style."""
import numpy as np

from . import painters as P
from .blocks_plants import Sprite, mushroom
from .blocks_village import door, trapdoor, has_holes
from .core import (N, STATS, Tex, dashes, fbm, make_ramp, mix, norm01, paint, paint_idx, plane, rng_of, shift,
                   stack_frames, vbase, vramp, white)

yy, xx = np.mgrid[0:N, 0:N]
GOLD = [(160, 104, 16), (214, 156, 28), (246, 204, 52), (255, 232, 110), (255, 250, 190)]
QUARTZ = [(176, 160, 150), (208, 196, 186), (232, 224, 214), (246, 240, 232), (255, 252, 246)]


def frames_of(name):
    w, h = STATS[name]["size"]
    return max(1, h // w)


def netherrack():
    return P.cells("netherrack", vramp("netherrack", 6, contrast=0.36), 12, vary=0.3, dome=0.4)


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
    pr = vramp(planks, 5, contrast=0.26)
    out[planks] = P.planks("planks_" + kind, pr)
    wood = vramp(strip_side, 5, contrast=0.22)
    br = vramp(stem_side, 5, contrast=0.36)
    # the stem's veins pulse: same bark every frame, vein brightness travels upward
    base = P.bark("stem_" + kind, br, ridges=7)
    r = rng_of("veins_" + kind)
    vein = np.zeros((N, N), bool)
    for _ in range(6):
        x, y = int(r.integers(N)), int(r.integers(N))
        for i in range(int(r.integers(4, 9))):
            vein[(y + i) % N, x] = True
            if r.random() < 0.25:
                x = (x + int(r.choice([-1, 1]))) % N
    gl = make_ramp(glow, 4, 0.5)
    n = frames_of(stem_side)
    frames = []
    for f in range(n):
        t = base.copy()
        phase = ((yy + f * (N // n)) % N) / N
        lvl = np.clip((np.sin(phase * 2 * np.pi) * 0.5 + 0.5) * 3.99, 0, 3).astype(int)
        t.rgb = np.where(vein[..., None], np.array(gl, np.uint8)[lvl], t.rgb)
        t.emis = np.where(vein, 60 + lvl * 55, 0)
        t.height = np.where(vein, 0.9, t.height)
        frames.append(t)
    out[stem_side] = stack_frames(frames)
    out[stem_top] = P.log_top("top_" + kind, wood, br)
    out[strip_side] = P.stripped("strip_" + kind, wood)
    out[strip_top] = P.log_top("top_" + kind, wood, wood)
    up, lo = door(kind, pr, "panes" if kind == "crimson" else "lattice", has_holes(door_up))
    out[door_up], out[door_lo] = up, lo
    out[trap] = trapdoor(kind, pr, "grid" if kind == "crimson" else "lattice", has_holes(trap))


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
    nb = vramp("nether_brick", 5, contrast=0.36)
    nm = [shift(nb[0], dv=-0.03), nb[0]]
    out["nether_brick"] = P.bricks("nether_brick", nb, nm, rows=4, cols=2)
    out["cracked_nether_bricks"] = P.bricks("nether_brick", nb, nm, rows=4, cols=2, crack=4, chip=0.06)
    out["chiseled_nether_bricks"] = P.slab_face("chiseled_nether", nb, border=1, inset=4, vary=0.12, rough=180)
    rb = vramp("red_nether_brick", 5, contrast=0.36)
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
    out["basalt_side"] = P.rock("basalt_side", bs, "pillars", cracks=2)
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
    ad = vramp("ancient_debris_side", 5, contrast=0.4)
    out["ancient_debris_side"] = P.rock("ancient_debris_side", ad, "strata", cracks=3, rough=160)
    out["ancient_debris_top"] = P.log_top("ancient_debris_top", vramp("ancient_debris_top", 5, contrast=0.4), ad, rough=160)
    out["netherite_block"] = P.metal_block("netherite_block", vramp("netherite_block", 5, contrast=0.4), "plate", metal=230, rough=90)

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
    wart = make_ramp((150, 20, 26), 5, 0.5)
    for st in range(3):
        s = Sprite()
        for x in (3, 7, 11):
            h = 2 + st * 3
            for k in range(h):
                s.px(x, 15 - k, wart[1], 0.5)
                s.px(x + 1, 15 - k, wart[0], 0.45)
            w = 1 + st
            for dx in range(-w + 1, w + 1):
                for dy in range(w):
                    s.px(x + dx, 15 - h - dy, wart[3 if (dx <= 0 and dy == w - 1) else 2], 0.9)
            s.px(x - w + 1, 15 - h - w + 1, wart[4], 1.0)
        out[f"nether_wart_stage_{st}"] = s.tex(sss=40)
    wv, tv = vramp("weeping_vines_plant", 5, contrast=0.5), vramp("twisting_vines_base", 5, contrast=0.5)
    out["weeping_vines_plant"] = vine("weeping_body", wv, False, False)
    out["weeping_vines_base"] = vine("weeping_body", wv, False, False)
    out["weeping_vines"] = vine("weeping_tip", wv, False, True, glow=(255, 140, 60))
    out["weeping_vines_bottom"] = vine("weeping_tip", wv, False, True, glow=(255, 140, 60))
    out["twisting_vines_base"] = vine("twisting_body", tv, True, False)
    out["twisting_vines_bottom"] = vine("twisting_tip", tv, True, True, glow=(140, 255, 220))

    # ---------------------------------------------------------------- END
    es = vramp("end_stone", 6, contrast=0.22)
    out["end_stone"] = P.cells("end_stone", es, 9, dome=0.4, vary=0.2)
    eb = vramp("end_bricks", 5, contrast=0.2)
    out["end_bricks"] = P.bricks("end_bricks", eb, [shift(eb[0], dv=-0.06), shift(eb[0], dv=-0.03)], rows=4, cols=2, vary=0.14)
    pp = vramp("purpur_block", 5, contrast=0.24)
    out["purpur_block"] = P.bricks("purpur_block", pp, [shift(pp[0], dv=-0.05), pp[0]], rows=2, cols=2, vary=0.16)
    out["purpur_pillar"] = fluted("purpur_pillar", vramp("purpur_pillar", 5, contrast=0.24))
    out["purpur_pillar_top"] = P.slab_face("purpur_pillar_top", vramp("purpur_pillar_top", 5, contrast=0.24), border=1, inset=3, vary=0.1)
    cp = vramp("chorus_plant", 5, contrast=0.36)
    t = P.bark("chorus_plant", cp, ridges=6, bump=1.0)
    r = rng_of("chorus_dots")
    for _ in range(9):
        x, y = int(r.integers(N)), int(r.integers(N))
        t.rgb[y, x] = (214, 190, 220)
    out["chorus_plant"] = t
    for nm_ in ("chorus_flower", "chorus_flower_dead"):
        c = P.cells(nm_, vramp(nm_, 6, contrast=0.34), 8, dome=0.5)
        if nm_ == "chorus_flower":
            c.rgb[7:9, 7:9] = (250, 240, 252)
        out[nm_] = c
    de = P.cells("dragon_egg", make_ramp((30, 18, 44), 6, 0.6), 9, dome=0.5)
    r = rng_of("egg_dots")
    for _ in range(8):
        x, y = int(r.integers(N)), int(r.integers(N))
        de.rgb[y, x] = (150, 70, 220)
    out["dragon_egg"] = de
    teal = vramp("endframe_top", 5, contrast=0.34)
    ft = P.slab_face("endframe_top", teal, border=2, vary=0.14, rough=120)
    sock = (xx >= 4) & (xx <= 11) & (yy >= 4) & (yy <= 11)
    ft.rgb = np.where(sock[..., None], np.array(shift(teal[0], dv=-0.08), np.uint8), ft.rgb)
    ft.height = np.where(sock, 0.1, ft.height)
    out["endframe_top"] = ft
    fs = out["end_stone"].copy()
    fs.rgb[3:7] = paint(np.where(yy[3:7] == 3, 0.85, np.where(yy[3:7] == 6, 0.15, 0.5)), teal)
    fs.height[3:7] = 0.95
    for x in (3, 8, 12):
        fs.rgb[5, x] = teal[4]
    fs.alpha[0:3, :] = 0                         # the frame is 13 px tall
    out["endframe_side"] = fs
