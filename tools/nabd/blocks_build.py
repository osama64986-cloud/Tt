"""Building & decoration blocks: wool, concrete, terracotta, glass, metals,
copper, prismarine, masonry, farm blocks and the nether blocks that show up
in the overworld (ruined portals, ocean magma...)."""
import numpy as np

from . import painters as P
from .core import N, STATS, Tex, emboss, fbm, make_ramp, mix, norm01, paint, plane, rng_of, shift, stack_frames, vbase, vramp, white

COLORS = ["black", "blue", "brown", "cyan", "gray", "green", "light_blue", "lime", "magenta", "orange",
          "pink", "purple", "red", "silver", "white", "yellow"]
yy, xx = np.mgrid[0:N, 0:N]


def frames_of(name):
    w, h = STATS[name]["size"]
    return max(1, h // w)


def build(out, flip, variations):
    # ------------------------------------------------------------ dyed families
    for c in COLORS:
        out[f"wool_colored_{c}"] = P.wool("wool", vramp(f"wool_colored_{c}", 5, contrast=0.22))
        out[f"concrete_{c}"] = P.flat("concrete", vramp(f"concrete_{c}", 5, contrast=0.1), "smooth", rough=150, amount=0.3)
        out[f"concrete_powder_{c}"] = P.flat("powder", vramp(f"concrete_powder_{c}", 5, contrast=0.16), "powder", rough=230)
        out[f"hardened_clay_stained_{c}"] = P.flat("terracotta", vramp(f"hardened_clay_stained_{c}", 5, contrast=0.12), "clay", rough=190, amount=0.3)
        base = vbase(f"glass_{c}")
        fr = [shift(base, dv=-0.12), base, shift(base, dv=0.18, ds=-0.2)]
        out[f"glass_{c}"] = P.glass("glass", fr, shift(base, dv=0.3, ds=-0.45), body=base, body_alpha=118, frame_alpha=190)
        out[f"glass_pane_top_{c}"] = pane_top(vbase(f"glass_pane_top_{c}"))
    out["hardened_clay"] = P.flat("terracotta", vramp("hardened_clay", 5, contrast=0.12), "clay", rough=190, amount=0.3)
    gb = (176, 214, 222)
    out["glass"] = P.glass("glass", [shift(gb, dv=-0.2), gb, (232, 246, 248)], (255, 255, 255))
    out["glass_pane_top"] = pane_top(vbase("glass_pane_top"))
    tb = vbase("tinted_glass")
    tg = P.glass("glass", [shift(tb, dv=-0.08), shift(tb, dv=0.06), shift(tb, dv=0.2)], shift(tb, dv=0.3), body=tb,
                 body_alpha=160, frame_alpha=225)
    out["tinted_glass"] = tg

    # ----------------------------------------------------------------- masonry
    out["brick"] = P.bricks("brick", vramp("brick", 5, contrast=0.24), [(150, 140, 130), (166, 156, 146), (178, 170, 160)],
                            rows=4, cols=2, vary=0.3)
    pm = [(40, 78, 72), (48, 90, 84)]
    out["prismarine_bricks"] = P.bricks("prismarine_bricks", vramp("prismarine_bricks", 5, contrast=0.24), pm, rows=2, cols=2, vary=0.3, rough=120)
    out["prismarine_dark"] = P.bricks("prismarine_dark", vramp("prismarine_dark", 5, contrast=0.28), [(24, 44, 40), (30, 54, 48)],
                                      rows=4, cols=4, stagger=False, vary=0.3, rough=120)
    n = frames_of("prismarine_rough")
    pr_frames = []
    for f in range(n):
        ph = f / n
        base = mix(mix((84, 150, 132), (96, 168, 176), 0.5 + 0.5 * np.sin(ph * 2 * np.pi)), (120, 132, 168), 0.25 + 0.25 * np.cos(ph * 2 * np.pi))
        pr_frames.append(P.cells("prismarine", make_ramp(base, 6, 0.34), 10, rough=120, vary=0.34))
    out["prismarine_rough"] = stack_frames(pr_frames)
    n = frames_of("sea_lantern")
    sl = []
    for f in range(n):
        ph = np.sin(f / n * 2 * np.pi)
        ramp = make_ramp(mix((168, 208, 200), (214, 240, 232), 0.5 + 0.5 * ph), 5, 0.2)
        t = P.cells("sea_lantern", ramp, 8, vary=0.2, dome=0.5)
        fr = (yy == 0) | (xx == 0) | (yy == 15) | (xx == 15)
        t.rgb = np.where(fr[..., None], np.array((70, 110, 108), np.uint8), t.rgb)
        t.emis = np.where(fr, 0, 200)
        t.rough = 90
        sl.append(t)
    out["sea_lantern"] = stack_frames(sl)

    # mineral / storage blocks live in blocks_minerals.py; only cut copper here
    for stage, cut, metal, rough in (("copper_block", "cut_copper", 235, 70), ("exposed_copper", "exposed_cut_copper", 190, 110),
                                     ("weathered_copper", "weathered_cut_copper", 120, 150),
                                     ("oxidized_copper", "oxidized_cut_copper", 60, 185)):
        cr = vramp(cut, 5, contrast=0.26)
        c = P.bricks("cut_copper", cr, [cr[0], shift(cr[0], dv=0.04)], rows=2, cols=2, stagger=False, vary=0.14, chip=0.02)
        c.metal, c.rough = metal, rough
        out[cut] = c

    # ------------------------------------------------- nether guests & obsidian
    out["netherrack"] = P.cells("netherrack", vramp("netherrack", 6, contrast=0.36), 12, vary=0.3, dome=0.4)
    cry = out_obsidian_cry()
    out["crying_obsidian"] = cry
    n = frames_of("magma")
    mg = []
    crust = make_ramp((70, 34, 30), 5, 0.4)
    for f in range(n):
        t = P.cells("magma", crust, 8, vary=0.25, dome=0.5)
        seam = t.height < 0.2
        glow = [(190, 60, 10), (240, 120, 20), (255, 190, 60)]
        r = rng_of("magma")
        fld = fbm(r, ((4, 1.0), (8, 0.5)))
        idx = np.clip(((fld + f / n) % 1.0) * 3, 0, 2.999).astype(int)
        t.rgb = np.where(seam[..., None], np.array(glow, np.uint8)[idx], t.rgb)
        t.emis = np.where(seam, 230, 0)
        t.rough = np.where(seam, 60, 210)
        mg.append(t)
    out["magma"] = stack_frames(mg)
    gs = P.cells("glowstone", vramp("glowstone", 6, contrast=0.4), 10, vary=0.4, dome=0.5)
    gs.emis = np.clip((gs.height - 0.2) * 260, 0, 255)
    gs.rough = 120
    out["glowstone"] = gs
    ssd = P.soil("soul_sand", vramp("soul_sand", 5, contrast=0.3), pebbles=0)
    r = rng_of("soul_faces")
    for _ in range(3):                           # hollow, sunken eyes
        x, y = int(r.integers(1, 12)), int(r.integers(1, 13))
        for dx in (0, 3):
            ssd.rgb[y, x + dx] = vramp("soul_sand", 5, contrast=0.5)[0]
            ssd.rgb[y + 1, x + dx] = vramp("soul_sand", 5, contrast=0.5)[0]
            ssd.height[y:y + 2, x + dx] = 0.05
    out["soul_sand"] = ssd

    # ------------------------------------------------------------- farm & misc
    furnace(out)
    hay = vramp("hay_block_side", 5, contrast=0.3)
    r = rng_of("hay")
    g = fbm(r, ((8, 1.0), (16, 0.8)), sy=6)
    tone = np.clip(0.25 + g * 0.6 + emboss(g, 0.6), 0, 1)
    t = Tex(paint(tone, hay, dither=0.3), 0.4 + g * 0.4, rough=225, sss=40, bump=1.2)
    band = make_ramp((150, 44, 36), 4, 0.3)
    for y0 in (3, 11):
        t.rgb[y0] = band[3]
        t.rgb[y0 + 1] = band[1]
        t.height[y0:y0 + 2] = 0.95
    out["hay_block_side"] = t
    g2 = fbm(r, ((8, 1.0), (16, 0.8)))
    d = np.hypot(xx - 7.5, yy - 7.5)
    tone = np.clip(0.3 + g2 * 0.5 + np.sin(d * 1.6) * 0.12, 0, 1)
    out["hay_block_top"] = Tex(paint(tone, vramp("hay_block_top", 5, contrast=0.3), dither=0.5), g2, rough=225, bump=1.0)

    gourd(out, "melon_side", "melon_top", stripes=True)
    gourd(out, "pumpkin_side", "pumpkin_top", stripes=False)
    for nm, lit in (("pumpkin_face_off", False), ("pumpkin_face_on", True)):
        t = out["pumpkin_side"].copy()
        dark = (48, 26, 8)
        glow = [(255, 236, 120), (255, 190, 50)]
        face = np.zeros((N, N), bool)
        for (x0, y0) in ((3, 4), (10, 4)):          # round eyes
            face[y0:y0 + 3, x0:x0 + 3] = True
            face[y0, x0] = face[y0 + 2, x0 + 2] = False
        face[8, 7:9] = True                           # nose
        for i, x in enumerate(range(3, 13)):         # zig-zag grin
            face[11 + (i % 2), x] = True
            face[12, x] = True
        face[12, 3] = face[12, 12] = False
        t.rgb = np.where(face[..., None], np.array(glow[0] if lit else dark, np.uint8), t.rgb)
        if lit:
            inner = face & np.roll(face, 1, 0)
            t.rgb = np.where(inner[..., None], np.array(glow[1], np.uint8), t.rgb)
            t.emis = np.where(face, 235, 0)
        t.height = np.where(face, 0.05, t.height)
        out[nm] = t

    tnt(out)
    sp = vramp("sponge", 5, contrast=0.3)
    for nm, seed in (("sponge", "sponge"), ("sponge_wet", "sponge")):
        t = P.soil(seed, vramp(nm, 5, contrast=0.3), pebbles=0, clump=((4, 1.0), (8, 0.6)))
        r = rng_of("sponge_holes")
        for _ in range(9):
            x, y = int(r.integers(N)), int(r.integers(N))
            sz = int(r.choice([1, 2, 2]))
            for dx in range(sz):
                for dy in range(sz):
                    t.rgb[(y + dy) % N, (x + dx) % N] = vramp(nm, 5, contrast=0.5)[0]
                    t.height[(y + dy) % N, (x + dx) % N] = 0.0
            t.rgb[(y - 1) % N, x % N] = vramp(nm, 5, contrast=0.3)[4]
        t.rough = 120 if nm.endswith("wet") else 230
        out[nm] = t
    out["bone_block_side"] = P.stripped("bone_side", vramp("bone_block_side", 5, contrast=0.12), rough=150)
    out["bone_block_top"] = P.log_top("bone_top", vramp("bone_block_top", 5, contrast=0.14), vramp("bone_block_side", 5, contrast=0.12), rough=150)
    for c in ("red", "brown"):
        cap = P.flat("mush_" + c, vramp(f"mushroom_block_skin_{c}", 5, contrast=0.16), "smooth", rough=150, amount=0.8)
        if c == "red":
            r = rng_of("mush_spots")
            for _ in range(5):
                x, y = int(r.integers(N)), int(r.integers(N))
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2))[: int(r.integers(3, 7))]:
                    cap.rgb[(y + dy) % N, (x + dx) % N] = (244, 240, 232)
                    cap.height[(y + dy) % N, (x + dx) % N] = 0.8
        out[f"mushroom_block_skin_{c}"] = cap
    out["mushroom_block_skin_stem"] = P.stripped("mush_stem", vramp("mushroom_block_skin_stem", 5, contrast=0.1), rough=200)
    ins = P.soil("mush_inside", vramp("mushroom_block_inside", 5, contrast=0.2), pebbles=0, clump=((8, 1.0), (16, 0.6)))
    out["mushroom_block_inside"] = ins
    for c in ("blue", "pink", "purple", "red", "yellow"):
        for dead in ("", "_dead"):
            nm = f"coral_{c}{dead}"
            ramp = vramp(nm, 5, contrast=0.3)
            t = P.cells("coral_" + c, ramp, 14, vary=0.3, dome=0.6, bump=1.4)
            out[nm] = t
    hc = vramp("honeycomb", 5, contrast=0.3)
    cellx = (xx + (yy // 4 % 2) * 3) % 6
    edge = (yy % 4 == 3) | (cellx == 5)
    tone = np.where(edge, 0.1, 0.55 + 0.25 * (cellx < 2) - 0.15 * (cellx > 3))
    tone = np.where((yy % 4 == 0) & ~edge, tone + 0.15, tone)
    out["honeycomb"] = Tex(paint(np.clip(tone, 0, 1), hc), np.where(edge, 0.9, 0.3), rough=90, bump=1.3)
    out["powder_snow"] = P.rock("powder_snow", make_ramp((244, 250, 254), 5, 0.05, warm=0.02), "fine", cracks=0, speck=0.05, rough=220, bump=0.4)

    if "bamboo_planks" in STATS:
        bp = vramp("bamboo_planks", 5, contrast=0.22)
        out["bamboo_planks"] = P.planks("bamboo_planks", bp, boards=8, nails=False)
        bb = vramp("bamboo_block", 5, contrast=0.26)
        t = P.stripped("bamboo_block", bb)
        for y0 in (4, 12):
            t.rgb[y0] = bb[0]
            t.rgb[(y0 + 1) % N] = bb[4]
            t.height[y0] = 0.2
        out["bamboo_block"] = t
        t = P.stripped("stripped_bamboo_block", vramp("stripped_bamboo_block", 5, contrast=0.2))
        out["stripped_bamboo_block"] = t


def pane_top(base):
    ramp = make_ramp(base, 5, 0.2)
    tone = np.where(xx % 2 == 0, 0.7, 0.4) + np.where(yy % 5 == 0, 0.15, 0)
    return Tex(paint(np.clip(tone, 0, 1), ramp), None, rough=20, bump=0.3)


def out_obsidian_cry():
    ob = make_ramp((30, 22, 46), 5, 0.55, warm=0.02)
    t = P.rock("obsidian", ob, "smooth", cracks=3, rough=40)
    tears = [(120, 40, 220), (170, 80, 250), (220, 170, 255)]
    r = rng_of("crying")
    emis = np.zeros((N, N))
    for _ in range(6):
        x, y = int(r.integers(N)), int(r.integers(N))
        for i in range(int(r.integers(2, 5))):
            t.rgb[(y + i) % N, x] = tears[min(2, i)]
            emis[(y + i) % N, x] = 180
            if r.random() < 0.3:
                x = (x + int(r.choice([-1, 1]))) % N
    t.emis = emis
    return t


def furnace(out):
    body = vramp("furnace_side", 5, contrast=0.3)
    mort = [(58, 58, 62), (68, 68, 72)]
    side = P.bricks("furnace_side", body, mort, rows=4, cols=2, vary=0.2)
    out["furnace_side"] = side
    top = P.slab_face("furnace_top", vramp("furnace_top", 5, contrast=0.26), border=2, vary=0.2, rough=180)
    out["furnace_top"] = top
    for nm, lit in (("furnace_front_off", False), ("furnace_front_on", True)):
        t = side.copy()
        emis = np.zeros((N, N))
        # arched mouth
        mouth = (yy >= 8) & (yy <= 13) & (xx >= 3) & (xx <= 12)
        mouth &= ~((yy == 8) & ((xx == 3) | (xx == 12)))
        rim = np.zeros((N, N), bool)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rim |= np.roll(np.roll(mouth, dy, 0), dx, 1)
        rim &= ~mouth
        t.rgb = np.where(rim[..., None], np.array(body[4], np.uint8), t.rgb)
        t.rgb = np.where((rim & ((yy > 10) | (xx > 9)))[..., None], np.array(body[1], np.uint8), t.rgb)
        t.height = np.where(rim, 1.0, t.height)
        t.rgb = np.where(mouth[..., None], np.array((20, 18, 18), np.uint8), t.rgb)
        t.height = np.where(mouth, 0.0, t.height)
        # vent slot above
        vent = (yy >= 3) & (yy <= 4) & (xx >= 4) & (xx <= 11)
        t.rgb = np.where(vent[..., None], np.array((26, 24, 24), np.uint8), t.rgb)
        t.rgb[5, 4:12] = body[4]
        t.height = np.where(vent, 0.05, t.height)
        # grate bars
        for x in (5, 7, 9, 11):
            bar = mouth[:, x] & (yy[:, x] >= 12)
            t.rgb[bar, x] = (70, 70, 74)
        if lit:
            fire = [(214, 70, 16), (250, 140, 24), (255, 214, 80), (255, 248, 190)]
            r = rng_of("furnace_fire")
            for x in range(4, 12):
                hgt = int(r.integers(1, 4))
                for i in range(hgt + 1):
                    y = 11 - i
                    if mouth[y, x]:
                        t.rgb[y, x] = fire[max(0, 3 - i - int(r.integers(0, 2)))]
                        emis[y, x] = 240
            for y in (3, 4):
                for x in range(4, 12):
                    if r.random() < 0.5:
                        t.rgb[y, x] = fire[0]
                        emis[y, x] = 150
        t.emis = emis
        out[nm] = t


def gourd(out, side_name, top_name, stripes):
    ramp = vramp(side_name, 5, contrast=0.3)
    r = rng_of(side_name)
    g = fbm(r, ((4, 1.0), (8, 0.5)), sy=4)
    rib = np.abs(((xx + 2) % 5) - 2) / 2.0            # 0 centre of rib .. 1 groove
    tone = 0.62 - rib * 0.34 + (g - 0.5) * 0.2
    if stripes:
        tone = np.where(((xx + 2) % 5 == 2) & ((yy + xx) % 7 != 0), tone - 0.22, tone)
    tone = np.where(yy == 0, tone + 0.12, tone)
    tone = np.where(yy == 15, tone - 0.15, tone)
    out[side_name] = Tex(paint(np.clip(tone, 0, 1), ramp), 0.9 - rib * 0.6, rough=150, bump=1.2)
    tr = vramp(top_name, 5, contrast=0.3)
    ang = np.arctan2(yy - 7.5, xx - 7.5)
    d = np.hypot(xx - 7.5, yy - 7.5)
    ribs = np.abs(np.sin(ang * 4))
    tone = 0.35 + ribs * 0.35 + (g - 0.5) * 0.15
    t = Tex(paint(np.clip(tone, 0, 1), tr), 0.4 + ribs * 0.4, rough=150, bump=1.1)
    stem = make_ramp((120, 132, 60), 4, 0.3) if not stripes else make_ramp((150, 140, 90), 4, 0.3)
    core_m = d < 1.6
    t.rgb = np.where(core_m[..., None], paint(np.where((yy < 7.5) | (xx < 7.5), 0.8, 0.3), stem), t.rgb)
    t.height = np.where(core_m, 1.0, t.height)
    out[top_name] = t


FONT = {"T": ["###", ".#.", ".#.", ".#.", ".#."], "N": ["#.#", "###", "###", "#.#", "#.#"]}


def tnt(out):
    red = vramp("tnt_side", 5, contrast=0.3)
    red = make_ramp((196, 44, 30), 5, 0.3)
    stick = np.abs((xx % 4) - 1.5) / 1.5
    tone = 0.7 - stick * 0.4
    t = Tex(paint(np.clip(tone, 0, 1), red), 0.9 - stick * 0.5, rough=170, bump=1.2)
    t.rgb = np.where((xx % 4 == 3)[..., None], np.array(red[0], np.uint8), t.rgb)
    band = (yy >= 5) & (yy <= 11)
    paper = make_ramp((232, 226, 214), 4, 0.1)
    t.rgb = np.where(band[..., None], np.array(paper[2], np.uint8), t.rgb)
    t.rgb[5] = paper[3]
    t.rgb[11] = paper[0]
    t.height = np.where(band, 1.0, t.height)
    for i, ch in enumerate("TNT"):
        for ry, row in enumerate(FONT[ch]):
            for rx, c in enumerate(row):
                if c == "#":
                    t.rgb[6 + ry, 2 + i * 4 + rx] = (36, 30, 30)
    out["tnt_side"] = t
    d = np.hypot((xx % 4) - 1.5, (yy % 4) - 1.5)
    tone = np.clip(0.85 - d * 0.3, 0, 1)
    top = Tex(paint(tone, red), 1 - d * 0.3, rough=170, bump=1.2)
    gap = (xx % 4 == 3) | (yy % 4 == 3)
    top.rgb = np.where(gap[..., None], np.array(red[0], np.uint8), top.rgb)
    out["tnt_bottom"] = top.copy()
    fuse = ((xx % 4 == 1) | (xx % 4 == 2)) & ((yy % 4 == 1) | (yy % 4 == 2)) & (xx > 3) & (xx < 12) & (yy > 3) & (yy < 12)
    top.rgb = np.where(fuse[..., None], np.array((60, 56, 52), np.uint8), top.rgb)
    top.rgb[5, 5] = top.rgb[9, 9] = (220, 210, 200)
    out["tnt_top"] = top
