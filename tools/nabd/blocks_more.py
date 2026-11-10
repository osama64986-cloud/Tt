"""The rest of the overworld: redstone machines, copper extras, rails, bars,
translucent blocks, mangrove roots, sculk, froglights and cave plants."""
import numpy as np

from . import painters as P
from .blocks_plants import Sprite
from .blocks_village import IRON, DARK_IRON, door, frame_panel, has_holes, hole, trapdoor
from .core import (N, STATS, Tex, dashes, fbm, make_ramp, mix, norm01, paint, paint_idx, plane, rng_of, shift,
                   stack_frames, vbase, vramp, white)

yy, xx = np.mgrid[0:N, 0:N]
STAGES = ["", "exposed_", "weathered_", "oxidized_"]
STAGE_METAL = {"": (235, 70), "exposed_": (190, 110), "weathered_": (120, 150), "oxidized_": (60, 185)}


def frames_of(name):
    w, h = STATS[name]["size"]
    return max(1, h // w)


def put(out, name, tex):
    if name in STATS:
        out[name] = tex


def rail(kind, powered=False, turned=False):
    t = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=120, bump=1.0)
    wood = make_ramp((132, 96, 58), 5, 0.3)
    metal = {"normal": IRON, "golden": make_ramp((230, 180, 50), 5, 0.3), "detector": IRON,
             "activator": IRON}[kind]
    emis = np.zeros((N, N))
    met = np.zeros((N, N))

    def px(x, y, c, h=0.6, m=0, e=0):
        if 0 <= x < N and 0 <= y < N:
            t.rgb[y, x] = c
            t.alpha[y, x] = 255
            t.height[y, x] = h
            met[y, x] = m
            emis[y, x] = e
    if not turned:
        for y in (1, 5, 9, 13):                              # sleepers
            for x in range(1, 15):
                px(x, y, wood[3], 0.4)
                px(x, y + 1, wood[1], 0.35)
        for x0 in (3, 11):                                   # the two rails
            for y in range(N):
                px(x0, y, metal[4], 0.9, 220)
                px(x0 + 1, y, metal[1], 0.85, 220)
        if kind != "normal":                                 # powered strip down the middle
            col = {"golden": (200, 40, 30), "detector": (170, 40, 40), "activator": (170, 40, 40)}[kind]
            lit = (255, 80, 60)
            for y in range(N):
                if kind == "golden" or y % 4 in (1, 2):
                    px(7, y, lit if powered else col, 0.5, 0, 200 if powered else 0)
                    px(8, y, lit if powered else shift(col, dv=-0.1), 0.5, 0, 200 if powered else 0)
            if kind == "detector":                           # pressure plate
                for y in range(6, 10):
                    for x in range(5, 11):
                        px(x, y, (200, 60, 50) if powered else DARK_IRON[2], 0.7, 100, 180 if powered else 0)
    else:                                                    # quarter turn from the bottom edge to the right edge
        for i in range(4):
            a = np.pi / 2 * (i + 0.5) / 4
            cx, cy = 15 - np.cos(a) * 9, 15 - np.sin(a) * 9
            for k in range(-6, 7):
                x, y = int(round(cx - np.cos(a) * k * 0.9)), int(round(cy - np.sin(a) * k * 0.9))
                px(x, y, wood[3] if k % 2 else wood[1], 0.4)
        for rad, in ((4.5,), (12.5,)):
            for a in np.linspace(0, np.pi / 2, 60):
                x, y = int(round(15.5 - np.cos(a) * rad)), int(round(15.5 - np.sin(a) * rad))
                px(x, y, metal[4], 0.9, 220)
                px(x + 1, y, metal[1], 0.85, 220)
    t.emis, t.metal = emis, met
    return t


def bars(ramp, metal=220):
    t = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=90, metal=metal)
    for x0 in (1, 5, 9, 13):
        t.rgb[:, x0] = ramp[4]
        t.rgb[:, x0 + 1] = ramp[1]
        t.alpha[:, x0:x0 + 2] = 255
        t.height[:, x0:x0 + 2] = 0.9
    for y0 in (0, 7, 14):
        t.rgb[y0] = ramp[3]
        t.rgb[y0 + 1] = ramp[0]
        t.alpha[y0:y0 + 2] = 255
        t.height[y0:y0 + 2] = 1.0
    return t


def machine_body(out):
    return out["furnace_side"].copy()


def build(out, flip, variations):
    oak = vramp("planks_oak", 5, contrast=0.24)
    stone = vramp("cobblestone", 6, contrast=0.36)

    # ---------------------------------------------------------------- piston
    side = P.cells("piston_body", stone, 9)
    side.rgb[0:4] = P.planks("piston_head", oak, boards=1, nails=False).rgb[0:4]
    side.rgb[3] = oak[0]
    side.rgb[4] = DARK_IRON[3]
    side.rgb[5] = DARK_IRON[1]
    side.height[0:4] = 0.9
    side.height[4:6] = 1.0
    out["piston_side"] = side

    def head(sticky):
        t = P.planks("piston_top", oak, boards=4, nails=False)
        frame_panel(t, oak, 0, 0, 15, 15, sunk=False)
        for (x, y) in ((1, 1), (13, 1), (1, 13), (13, 13)):
            t.rgb[y:y + 2, x:x + 2] = IRON[3]
            t.rgb[y + 1, x + 1] = IRON[1]
            t.height[y:y + 2, x:x + 2] = 1.0
        if sticky:
            slime = make_ramp((120, 200, 90), 5, 0.3)
            m = fbm(rng_of("sticky"), ((3, 1.0),)) > 0.4
            m &= (xx > 2) & (xx < 13) & (yy > 2) & (yy < 13)
            t.rgb = np.where(m[..., None], paint(np.where(np.roll(m, 1, 0) & np.roll(m, 1, 1), 0.5, 0.85), slime), t.rgb)
            t.height = np.where(m, 1.0, t.height)
            t.rough = np.where(m, 40, 205)
        return t
    out["piston_top_normal"] = head(False)
    out["piston_top_sticky"] = head(True)
    pb = P.cells("piston_bottom", stone, 9)
    frame_panel(pb, stone, 5, 5, 10, 10)
    pb.rgb[6:10, 6:10] = (30, 30, 34)
    out["piston_bottom"] = pb
    pi = P.cells("piston_bottom", stone, 9)
    pi.rgb[4:12, 4:12] = P.planks("piston_inner", oak, boards=2, nails=False).rgb[4:12, 4:12]
    frame_panel(pi, oak, 4, 4, 11, 11, sunk=False)
    out["piston_inner"] = pi

    # --------------------------------------------------- dispenser & dropper
    def port(kind, vertical):
        t = machine_body(out) if not vertical else out["furnace_top"].copy()
        if kind == "dispenser":
            m = np.hypot(xx - 7.5, yy - 8.5) < 3.3
        else:
            m = (xx >= 4) & (xx <= 11) & (yy >= 7) & (yy <= 10)
        rim = np.zeros((N, N), bool)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rim |= np.roll(np.roll(m, dy, 0), dx, 1)
        rim &= ~m
        t.rgb = np.where(rim[..., None], np.array(DARK_IRON[3], np.uint8), t.rgb)
        t.rgb = np.where((rim & (yy + xx > 16))[..., None], np.array(DARK_IRON[1], np.uint8), t.rgb)
        t.rgb = np.where(m[..., None], np.array((22, 20, 22), np.uint8), t.rgb)
        t.height = np.where(m, 0.0, np.where(rim, 1.0, t.height))
        if kind == "dispenser" and not vertical:             # two bolt "eyes" above the mouth
            for x in (4, 11):
                t.rgb[3, x] = IRON[4]
                t.rgb[4, x] = IRON[1]
        return t
    for kind in ("dispenser", "dropper"):
        out[f"{kind}_front_horizontal"] = port(kind, False)
        out[f"{kind}_front_vertical"] = port(kind, True)

    # -------------------------------------------------------------- observer
    ob = vramp("observer_side", 5, contrast=0.4)
    body = P.bricks("observer", ob, [shift(ob[0], dv=-0.04), ob[0]], rows=2, cols=1)

    def arrow(t, up=True):
        for i in range(4):
            for x in range(7 - i, 9 + i):
                t.rgb[(4 + i) if up else (11 - i), x] = IRON[4 if x < 8 else 2]
        t.rgb[8:12, 7:9] = IRON[3]
        return t
    out["observer_side"] = arrow(body.copy())
    out["observer_top"] = arrow(P.slab_face("observer_top", vramp("observer_top", 5, contrast=0.36), border=1, vary=0.14))
    fr = body.copy()
    for x0 in (3, 10):
        fr.rgb[4:7, x0:x0 + 3] = (20, 20, 24)
        fr.rgb[5, x0 + 1] = (120, 30, 30)
        fr.height[4:7, x0:x0 + 3] = 0.05
    fr.rgb[10:12, 4:12] = (20, 20, 24)
    fr.height[10:12, 4:12] = 0.05
    out["observer_front"] = fr
    for nm, lit in (("observer_back", False), ("observer_back_lit", True)):
        t = body.copy()
        t.rgb[6:10, 6:10] = (255, 60, 40) if lit else (90, 20, 20)
        frame_panel(t, DARK_IRON, 5, 5, 10, 10)
        t.emis = np.where((xx >= 6) & (xx < 10) & (yy >= 6) & (yy < 10), 230 if lit else 0, 0)
        out[nm] = t

    # ----------------------------------------------------- daylight detector
    for nm, base in (("daylight_detector_top", (206, 190, 150)), ("daylight_detector_inverted_top", (150, 170, 196))):
        r = make_ramp(base, 5, 0.3)
        t = Tex(paint(np.where((xx % 4 == 0) | (yy % 4 == 0), 0.3, np.where((xx % 4 == 1) | (yy % 4 == 1), 0.85, 0.55)), r),
                np.where((xx % 4 == 0) | (yy % 4 == 0), 0.2, 0.7), rough=60, bump=0.8)
        out[nm] = t
    ds = P.planks("daylight_side", vramp("daylight_detector_side", 5, contrast=0.3), boards=2, nails=False)
    out["daylight_detector_side"] = ds

    # ------------------------------------------------------- cage & jellies
    cage = P.metal_block("mob_spawner", make_ramp((44, 56, 76), 5, 0.5), "rough", metal=200, rough=110)
    for x0 in range(1, 14, 4):
        for y0 in range(1, 14, 4):
            hole(cage, x0 + 1, y0 + 1, x0 + 2, y0 + 2, make_ramp((44, 56, 76), 5, 0.5))
    out["mob_spawner"] = cage

    def jelly(name, base, alpha, rough=30):
        r = make_ramp(base, 5, 0.26)
        tone = np.where((xx == 0) | (yy == 0), 0.9, np.where((xx == 15) | (yy == 15), 0.15, 0.5))
        inner = (xx >= 3) & (xx <= 12) & (yy >= 3) & (yy <= 12)
        tone = np.where(inner, 0.3, tone)
        tone = np.where(inner & ((xx == 3) | (yy == 3)), 0.1, tone)
        t = Tex(paint(tone, r), np.where(inner, 0.4, 0.7), alpha=np.full((N, N), alpha, np.uint8), rough=rough, sss=120, bump=0.6)
        for (x, y) in ((5, 5), (6, 5), (5, 6)):
            t.rgb[y, x] = r[4]
        return t
    out["slime"] = jelly("slime", vbase("slime"), STATS["slime"]["alpha"][0])
    for part in ("bottom", "side", "top"):
        out[f"honey_{part}"] = jelly("honey", vbase(f"honey_{part}"), STATS[f"honey_{part}"]["alpha"][0])

    # ------------------------------------------------------------ farm leftovers
    kelp = vramp("dried_kelp_side_a", 5, contrast=0.4)
    for nm in ("dried_kelp_side_a", "dried_kelp_side_b"):
        t = P.stripped(nm, kelp, rough=220)
        for y0 in (4, 11):
            t.rgb[y0] = (150, 130, 80)
            t.rgb[y0 + 1] = (100, 86, 50)
            t.height[y0:y0 + 2] = 0.95
        out[nm] = t
    out["dried_kelp_top"] = P.cells("dried_kelp_top", vramp("dried_kelp_top", 6, contrast=0.4), 9, dome=0.3)
    comp = vramp("composter_side", 5, contrast=0.3)
    cs = P.planks("composter_side", comp, boards=4, nails=False, vertical=True)
    for y0 in (0, 14):
        cs.rgb[y0] = comp[4]
        cs.rgb[y0 + 1] = comp[0]
    out["composter_side"] = cs
    out["composter_bottom"] = P.planks("composter_bottom", vramp("composter_bottom", 5, contrast=0.3), boards=4, nails=False)
    ct = P.planks("composter_top", vramp("composter_top", 5, contrast=0.3), boards=4, nails=False)
    frame_panel(ct, comp, 0, 0, 15, 15, sunk=False)
    ct.alpha[2:14, 2:14] = 0                       # open top: only the 2 px rim is solid
    out["composter_top"] = ct

    # ---------------------------------------------------- deepslate & roots
    deep = out["deepslate/deepslate"].copy()
    frame_panel(deep, IRON, 0, 0, 15, 15, sunk=False)
    frame_panel(deep, IRON, 3, 3, 12, 12)
    out["reinforced_deepslate_side"] = deep
    for nm in ("reinforced_deepslate_top", "reinforced_deepslate_bottom"):
        t = out["deepslate/deepslate_top"].copy()
        frame_panel(t, IRON, 0, 0, 15, 15, sunk=False)
        out[nm] = t
    rootr = vramp("mangrove_roots_side", 5, contrast=0.4)

    def roots(name, cover):
        r = rng_of(name)
        t = Tex(np.zeros((N, N, 3), np.uint8), np.zeros((N, N)), alpha=np.zeros((N, N), np.uint8), rough=215, bump=1.3)
        for _ in range(int(cover * 16)):
            x, y = int(r.integers(N)), 0
            for y in range(N):
                if r.random() < 0.4:
                    x = (x + int(r.choice([-1, 1]))) % N
                t.rgb[y, x] = rootr[3]
                t.rgb[y, (x + 1) % N] = rootr[1]
                t.alpha[y, x] = t.alpha[y, (x + 1) % N] = 255
                t.height[y, x] = 0.9
        return t
    rs, rt = roots("mangrove_roots_side", 0.5), roots("mangrove_roots_top", 0.35)
    out["mangrove_roots_side"], out["mangrove_roots_top"] = rs, rt
    for nm, src in (("muddy_mangrove_roots_side", rs), ("muddy_mangrove_roots_top", rt)):
        mud = P.soil("mud", vramp("mud", 5, contrast=0.22), pebbles=0, rough=90)
        mud.rgb = np.where((src.alpha > 0)[..., None], src.rgb, mud.rgb)
        mud.height = np.where(src.alpha > 0, 0.9, mud.height)
        out[nm] = mud

    # ---------------------------------------------------------------- lights
    for kind in ("ochre", "verdant", "pearlescent"):
        if f"{kind}_froglight_side" not in STATS:
            continue
        r = vramp(f"{kind}_froglight_side", 6, contrast=0.2)
        s = P.cells(f"{kind}_froglight", r, 7, dome=0.5)
        s.emis, s.rough = 210, 100
        out[f"{kind}_froglight_side"] = s
        tp = P.slab_face(f"{kind}_froglight_top", vramp(f"{kind}_froglight_top", 5, contrast=0.2), border=2, inset=5, vary=0.08)
        tp.emis, tp.rough = 220, 100
        out[f"{kind}_froglight_top"] = tp
    if "beacon" in STATS:
        b = P.glass("beacon", [(120, 190, 200), (170, 230, 236), (230, 250, 252)], (255, 255, 255), body=(150, 232, 226),
                    body_alpha=255, frame_alpha=255)
        core = (xx >= 5) & (xx <= 10) & (yy >= 5) & (yy <= 10)
        b.rgb = np.where(core[..., None], np.array((236, 255, 252), np.uint8), b.rgb)
        b.emis = np.where(core, 255, 90)
        out["beacon"] = b
    # sculk: near-black teal with slowly twinkling motes
    sk = make_ramp((14, 34, 42), 5, 0.6)
    base = P.rock("sculk", sk, "grain", cracks=0, rough=120)
    r = rng_of("sculk_motes")
    motes = [(int(r.integers(N)), int(r.integers(N)), int(r.integers(0, 4))) for _ in range(10)]
    n = frames_of("sculk")
    fr = []
    for f in range(n):
        t = base.copy()
        emis = np.zeros((N, N))
        for (x, y, ph) in motes:
            lvl = [0, 1, 2, 1][(f + ph) % 4] if n >= 4 else 2
            t.rgb[y, x] = [(20, 90, 110), (40, 170, 190), (150, 240, 240)][lvl]
            emis[y, x] = [60, 150, 240][lvl]
        t.emis = emis
        fr.append(t)
    out["sculk"] = stack_frames(fr)

    # ------------------------------------------------------- shelves & tables
    cb = P.planks("chiseled_shelf", oak, boards=4, nails=False)
    frame_panel(cb, oak, 0, 0, 15, 15, sunk=False)
    out["chiseled_bookshelf_top"] = cb.copy()
    out["chiseled_bookshelf_side"] = cb.copy()
    spines = [make_ramp(c, 4, 0.3) for c in ((180, 50, 44), (50, 100, 180), (56, 150, 76), (206, 170, 64), (130, 76, 160), (210, 210, 200))]
    for nm, full in (("chiseled_bookshelf_empty", False), ("chiseled_bookshelf_occupied", True)):
        t = cb.copy()
        k = 0
        for y0 in (2, 9):
            for x0 in (2, 6, 10):
                t.rgb[y0:y0 + 5, x0:x0 + 4] = (40, 28, 18)
                t.height[y0:y0 + 5, x0:x0 + 4] = 0.1
                if full:
                    sp = spines[k % len(spines)]
                    t.rgb[y0 + 1:y0 + 5, x0:x0 + 4] = sp[2]
                    t.rgb[y0 + 1:y0 + 5, x0] = sp[3]
                    t.rgb[y0 + 2, x0:x0 + 4] = sp[0]
                    t.height[y0 + 1:y0 + 5, x0:x0 + 4] = 0.6
                k += 1
        out[nm] = t
    obs = make_ramp((30, 22, 46), 5, 0.55, warm=0.02)
    out["enchanting_table_bottom"] = P.slab_face("ench_bottom", obs, border=1, vary=0.2, rough=50)
    cloth = make_ramp((176, 40, 54), 5, 0.3)
    et = P.wool("ench_cloth", cloth)
    gem = [(60, 190, 200), (150, 240, 240)]
    for (x, y) in ((1, 1), (13, 1), (1, 13), (13, 13)):
        et.rgb[y:y + 2, x:x + 2] = gem[0]
        et.rgb[y, x] = gem[1]
    frame_panel(et, obs, 0, 0, 15, 15, sunk=False)
    out["enchanting_table_top"] = et
    es = P.slab_face("ench_side", obs, border=1, vary=0.2, rough=50)
    es.rgb[4:7] = paint(np.where(yy[4:7] == 4, 0.85, np.where(yy[4:7] == 6, 0.2, 0.5)), cloth)
    for x in (2, 7, 12):
        es.rgb[9:12, x:x + 2] = gem[0]
        es.rgb[9, x] = gem[1]
    es.alpha[0:4, :] = 0                          # the table is 12 px tall
    out["enchanting_table_side"] = es

    # ------------------------------------------------------------- bamboo
    if "bamboo_mosaic" in STATS:
        bp = vramp("bamboo_mosaic", 5, contrast=0.24)
        h = P.planks("bamboo_mosaic_h", bp, boards=8, nails=False)
        v = P.planks("bamboo_mosaic_v", bp, boards=8, nails=False, vertical=True)
        chk = ((xx // 8) + (yy // 8)) % 2 == 0
        out["bamboo_mosaic"] = Tex(np.where(chk[..., None], h.rgb, v.rgb), np.where(chk, h.height, v.height), rough=205)
        out["bamboo_block_top"] = P.log_top("bamboo_top", vramp("bamboo_block_top", 5, contrast=0.3), vramp("bamboo_block", 5, contrast=0.3))
        st = vramp("stripped_bamboo_block_top", 5, contrast=0.26)
        out["stripped_bamboo_block_top"] = P.log_top("bamboo_top", st, st)

    # ------------------------------------------------------------- copper
    for pre in STAGES:
        base_name = "copper_block" if pre == "" else pre + "copper"
        ramp = vramp(base_name, 5, contrast=0.28)
        metal, rough = STAGE_METAL[pre]
        ch = P.slab_face("chiseled_copper", vramp(pre + "chiseled_copper", 5, contrast=0.28), border=1, inset=4, vary=0.1)
        ch.metal, ch.rough = metal, rough
        put(out, pre + "chiseled_copper", ch)
        gr = P.metal_block("copper_grate", ramp, "sheet", metal=metal, rough=rough)
        for x0 in (2, 6, 10):
            for y0 in (2, 6, 10):
                hole(gr, x0 + 1, y0 + 1, x0 + 2, y0 + 2, ramp)
        put(out, pre + "copper_grate", gr)
        for lit in (False, True):
            for pw in (False, True):
                nm = pre + "copper_bulb" + ("_lit" if lit else "") + ("_powered" if pw else "")
                b = P.metal_block("copper_bulb", ramp, "sheet", metal=metal, rough=rough)
                frame_panel(b, ramp, 3, 3, 12, 12)
                lamp = (xx >= 4) & (xx <= 11) & (yy >= 4) & (yy <= 11)
                glow = make_ramp((255, 200, 110) if lit else (120, 70, 50), 4, 0.3)
                b.rgb = np.where(lamp[..., None], paint(np.where((xx + yy) % 4 < 2, 0.7, 0.4), glow), b.rgb)
                b.emis = np.where(lamp, 235 if lit else 0, 0)
                if pw:
                    b.rgb[7:9, 7:9] = (255, 60, 40)
                    b.emis = np.where((xx >= 7) & (xx <= 8) & (yy >= 7) & (yy <= 8), 240, b.emis)
                put(out, nm, b)
        du, dl = pre + "copper_door_top", pre + "copper_door_bottom"
        if du in STATS:
            u, l = door(pre + "copper", ramp, "panes", has_holes(du))
            for t in (u, l):
                t.metal, t.rough = metal, rough
            out[du], out[dl] = u, l
        tr = pre + "copper_trapdoor"
        if tr in STATS:
            t = trapdoor(pre + "copper", ramp, "grid", has_holes(tr))
            t.metal, t.rough = metal, rough
            out[tr] = t
        put(out, pre + "copper_bars", bars(ramp, metal))
    put(out, "iron_bars", bars(IRON))

    # ------------------------------------------------- new stone families
    for fam in ("sulfur", "cinnabar"):
        if fam not in STATS:
            continue
        r = vramp(fam, 5, contrast=0.3)
        out[fam] = P.rock(fam, r, "grain", cracks=2)
        br = vramp(f"{fam}_bricks", 5, contrast=0.28)
        put(out, f"{fam}_bricks", P.bricks(f"{fam}_bricks", br, [shift(br[0], dv=-0.05), br[0]], rows=2, cols=1))
        put(out, f"polished_{fam}", P.slab_face(f"polished_{fam}", vramp(f"polished_{fam}", 5, contrast=0.24), border=1, vary=0.16))
        put(out, f"chiseled_{fam}", P.slab_face(f"chiseled_{fam}", vramp(f"chiseled_{fam}", 5, contrast=0.26), border=1, inset=4, vary=0.1))
    if "potent_sulfur" in STATS:
        ps = P.cells("potent_sulfur", vramp("potent_sulfur", 6, contrast=0.3), 9, dome=0.5)
        ps.emis = 40
        out["potent_sulfur"] = ps
    if "chiseled_resin_bricks" in STATS:
        rr = vramp("chiseled_resin_bricks", 5, contrast=0.26)
        out["chiseled_resin_bricks"] = P.slab_face("chiseled_resin", rr, border=1, inset=4, vary=0.1, rough=80)

    # ---------------------------------------------------------------- rails
    out["rail_normal"] = rail("normal")
    out["rail_normal_turned"] = rail("normal", turned=True)
    for kind in ("golden", "detector", "activator"):
        out[f"rail_{kind}"] = rail(kind)
        out[f"rail_{kind}_powered"] = rail(kind, powered=True)

    # --------------------------------------------------------- moss & azalea
    put(out, "pale_moss", P.turf("pale_moss", vramp("pale_moss", 5, contrast=0.3), sss=60, blades=34))
    az = vramp("azalea_top", 5, contrast=0.4)
    at = P.turf("azalea_top", az, sss=80, blades=40)
    out["azalea_top"] = at
    ft = at.copy()
    r = rng_of("azalea_top_flowers")
    pink = [(214, 96, 186), (240, 150, 220), (255, 214, 246)]
    for _ in range(5):
        x, y = int(r.integers(1, 14)), int(r.integers(1, 14))
        for dx, dy, c in ((0, 0, 2), (1, 0, 1), (0, 1, 1), (-1, 0, 1), (0, -1, 0)):
            ft.rgb[y + dy, x + dx] = pink[c]
    out["flowering_azalea_top"] = ft

    # ----------------------------------------------------------- cave plants
    s = Sprite()
    r = rng_of("glow_lichen")
    lich = make_ramp((120, 150, 136), 5, 0.36)
    field = fbm(r, ((3, 1.0), (6, 0.6)))
    for y in range(N):
        for x in range(N):
            if field[y, x] > 0.56:
                s.px(x, y, lich[2 + (field[y, x] > 0.7) + (field[y, x] > 0.82)], 0.6, emis=50 + 120 * (field[y, x] > 0.7))
    out["glow_lichen"] = s.tex(sss=40)
    s = Sprite()
    rootc = make_ramp((176, 130, 104), 5, 0.3)
    for (x, ln, lean) in ((3, 9, 0.5), (6, 13, -0.3), (9, 11, 0.4), (12, 8, -0.6), (7, 6, 0.8)):
        for k in range(ln):
            s.px(x + lean * (k / 4.0) ** 1.4, k, rootc[3 if k < ln // 2 else 2], 0.6)
        s.px(x + lean * (ln / 4.0) ** 1.4, ln, rootc[1], 0.5)
    out["hanging_roots"] = s.tex(sss=0)
    cv = make_ramp((92, 130, 44), 5, 0.42)
    for nm, tip, berries in (("cave_vines_body", False, False), ("cave_vines_body_berries", False, True),
                             ("cave_vines_head", True, False), ("cave_vines_head_berries", True, True)):
        s = Sprite()
        r = rng_of("cave_vines" + ("_tip" if tip else ""))
        for x0 in (5, 10):
            x = x0
            for y in range(12 if tip else 16):
                if r.random() < 0.3:
                    x = int(np.clip(x + r.choice([-1, 1]), 2, 13))
                s.px(x, y, cv[1 if y % 2 else 2], 0.5)
                if y % 3 == 1:
                    d = 1 if (y // 3 + x0) % 2 else -1
                    s.px(x + d, y, cv[3], 0.8)
                    s.px(x + 2 * d, y, cv[4], 0.85)
                    s.px(x + d, y + 1, cv[2], 0.7)
            if berries:
                bx, by = x - 1, (9 if tip else 7)
                for dx, dy, c in ((0, 0, (255, 190, 60)), (1, 0, (240, 140, 30)), (0, 1, (240, 140, 30)), (1, 1, (200, 96, 20))):
                    s.px(bx + dx, by + dy, c, 1.0, emis=200)
                s.px(bx, by, (255, 240, 170), 1.0, emis=240)
        out[nm] = s.tex(sss=80)
    s = Sprite()
    r = rng_of("frogspawn")
    for _ in range(13):
        x, y = int(r.integers(1, 14)), int(r.integers(1, 14))
        s.px(x, y, (40, 36, 40), 0.9)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if not s.alpha[y + dy, x + dx]:
                s.px(x + dx, y + dy, (206, 196, 186), 0.6)
    out["frogspawn"] = s.tex(sss=60)

    # --------------------------------------------------------- small plants
    for st in (0, 1):
        nm = f"torchflower_crop_stage_{st}"
        if nm in STATS:
            s = Sprite()
            g = make_ramp((40, 130, 90), 5, 0.42)
            h = 4 + st * 5
            s.stem(7, 15 - h, 15, ramp=g[:4])
            for k in range(1, h, 2):
                s.leaf(7, 15 - k, 1 if (k // 2) % 2 else -1, g, ln=2 + st)
            if st:
                s.shape(6, 15 - h - 2, [".3.", "232", ".1."], [(110, 40, 150), (226, 90, 30), (255, 160, 40), (255, 230, 120)], 0.9)
            out[nm] = s.tex()

    def bush(name, ramp, fireflies=False):
        s = Sprite()
        r = rng_of(name)
        d = np.hypot((xx - 7.5) / 7.0, (yy - 10.5) / 5.5)
        for y in range(N):
            for x in range(N):
                if d[y, x] < 1 - 0.18 * r.random():
                    tone = 2 + (1 if (x + y * 2) % 5 == 0 else 0) + (1 if y < 8 and x < 9 and r.random() < 0.4 else 0) - (1 if y > 12 else 0)
                    s.px(x, y, ramp[int(np.clip(tone, 0, 4))], 0.5 + 0.1 * tone)
        if fireflies:
            for _ in range(5):
                x, y = int(r.integers(2, 14)), int(r.integers(5, 14))
                s.px(x, y, (255, 240, 120), 1.0, emis=240)
        return s.tex()
    if "bush" in STATS:
        out["bush"] = bush("bush", vramp("bush", 5, grey=True, contrast=0.4))
    if "firefly_bush" in STATS:
        out["firefly_bush"] = bush("firefly_bush", make_ramp((80, 104, 50), 5, 0.42), fireflies=True)
    if "golden_dandelion" in STATS:
        s = Sprite()
        s.stem(7, 9, 15)
        s.leaf(7, 14, -1, ln=3)
        s.leaf(7, 13, 1, ln=2)
        s.shape(5, 5, [".232.", "23432", "12321", ".121."], [(170, 96, 10), (226, 150, 20), (255, 200, 40), (255, 236, 120), (255, 252, 210)], 0.9, emis=40)
        out["golden_dandelion"] = s.tex()
    for nm, tip in (("pale_hanging_moss_middle", False), ("pale_hanging_moss_tip", True)):
        if nm in STATS:
            s = Sprite()
            r = rng_of(nm)
            pm = vramp(nm, 5, contrast=0.4)
            for x in range(1, 15, 2):
                ln = int(r.integers(5, 12)) if tip else 16
                xi = x + int(r.integers(0, 2))
                for y in range(ln):
                    s.px(xi, y, pm[2 if y % 2 else 3], 0.6)
                if tip:
                    s.px(xi, ln, pm[4], 0.8)
            out[nm] = s.tex(sss=60)
