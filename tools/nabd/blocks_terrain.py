"""Overworld terrain: stone family, soils, sand, snow/ice, ores."""
import numpy as np

from . import painters as P
from .core import N, Tex, emboss, fbm, make_ramp, mix, norm01, paint, rng_of, shift, stack_frames, vbase, vramp, white

GREY_MORTAR = [(70, 70, 74), (82, 82, 86), (92, 92, 96)]


def moss_ramp():
    return vramp("moss_block", 5, contrast=0.34)


# ----------------------------------------------------------------- ore palettes
# Our own gem palettes (dark -> light).
GEMS = {
    "coal":     dict(ramp=[(18, 18, 22), (38, 38, 44), (58, 58, 66), (84, 84, 94), (120, 120, 132)], shape="chunk", metal=0, rough=140),
    "iron":     dict(ramp=[(128, 92, 70), (176, 134, 106), (214, 172, 140), (236, 204, 176), (252, 236, 216)], shape="fleck", metal=120, rough=110),
    "copper":   dict(ramp=[(132, 60, 34), (186, 92, 52), (226, 128, 78), (244, 168, 112), (255, 208, 160)], shape="clump", metal=120, rough=105),
    "gold":     dict(ramp=[(160, 104, 16), (214, 156, 28), (246, 204, 52), (255, 232, 110), (255, 250, 190)], shape="nugget", metal=200, rough=70),
    "redstone": dict(ramp=[(104, 6, 6), (164, 14, 12), (218, 30, 24), (255, 70, 56), (255, 150, 130)], shape="dots", metal=0, rough=120, emis=18),
    "lapis":    dict(ramp=[(16, 40, 120), (28, 66, 168), (44, 96, 210), (84, 136, 236), (150, 190, 255)], shape="clump", metal=0, rough=120),
    "diamond":  dict(ramp=[(24, 120, 128), (48, 176, 180), (96, 220, 216), (160, 244, 236), (228, 255, 250)], shape="shard", metal=0, rough=40),
    "emerald":  dict(ramp=[(8, 96, 44), (16, 148, 62), (36, 200, 88), (104, 236, 136), (196, 255, 208)], shape="crystal", metal=0, rough=45),
}
ORE_COUNT = {"coal": 6, "iron": 6, "copper": 6, "gold": 6, "redstone": 7, "lapis": 7, "diamond": 5, "emerald": 5}


def build(out, flip, variations):
    """out[name] = Tex; flip[name] = dict(strip, ticks); variations[atlas key] = [names].
    Variation keys must be atlas entries that hold ONE texture in the game
    (flattened_stone, cobblestone, ...) - never the legacy indexed lists."""
    # ------------------------------------------------------------------- stone
    st = vramp("stone", 5, contrast=0.2)
    out["stone"] = P.rock("stone", st, "smooth", cracks=3)
    for i in (1, 2):
        out[f"nabd/stone_v{i}"] = P.rock(f"stone_v{i}", st, "smooth", cracks=2 + i)
    variations["flattened_stone"] = ["stone", "nabd/stone_v1", "nabd/stone_v2"]

    cb = vramp("cobblestone", 6, contrast=0.36)
    out["cobblestone"] = P.cells("cobblestone", cb, 9)
    out["nabd/cobblestone_v1"] = P.cells("cobblestone_v1", cb, 10)
    variations["cobblestone"] = ["cobblestone", "nabd/cobblestone_v1"]
    out["cobblestone_mossy"] = P.cells("cobblestone", cb, 9, moss=moss_ramp())

    out["stone_andesite"] = P.rock("andesite", vramp("stone_andesite", 5, contrast=0.22), "grain", cracks=0,
                                   speck=0.06, speck_ramp=[(96, 98, 98), (176, 178, 176)])
    out["stone_diorite"] = P.rock("diorite", vramp("stone_diorite", 5, contrast=0.2), "grain", cracks=0,
                                  speck=0.09, speck_ramp=[(112, 112, 116), (140, 140, 144), (236, 236, 238)])
    out["stone_granite"] = P.rock("granite", vramp("stone_granite", 5, contrast=0.22), "grain", cracks=0,
                                  speck=0.08, speck_ramp=[(110, 72, 60), (206, 160, 142), (226, 208, 200)])
    for k in ("andesite", "diorite", "granite"):
        out[f"stone_{k}_smooth"] = P.slab_face(f"{k}_smooth", vramp(f"stone_{k}_smooth", 5, contrast=0.2), vary=0.22)

    sb = vramp("stonebrick", 5, contrast=0.26)
    out["stonebrick"] = P.bricks("stonebrick", sb, GREY_MORTAR, rows=2, cols=1, chip=0.03)
    for i in (1, 2):
        out[f"nabd/stonebrick_v{i}"] = P.bricks(f"stonebrick_v{i}", sb, GREY_MORTAR, rows=2, cols=1, chip=0.04 + 0.02 * i)
    variations["stone_bricks"] = ["stonebrick", "nabd/stonebrick_v1", "nabd/stonebrick_v2"]
    out["stonebrick_mossy"] = P.bricks("stonebrick", sb, GREY_MORTAR, rows=2, cols=1, chip=0.03, moss=moss_ramp())
    out["stonebrick_cracked"] = P.bricks("stonebrick", sb, GREY_MORTAR, rows=2, cols=1, chip=0.05, crack=4)
    out["stonebrick_carved"] = P.slab_face("stonebrick_carved", sb, border=1, inset=4, vary=0.12, rough=180)
    out["stone_slab_top"] = P.slab_face("stone_slab_top", vramp("stone_slab_top", 5, contrast=0.16), vary=0.2, rough=170)
    ss = P.slab_face("stone_slab_side", vramp("stone_slab_side", 5, contrast=0.18), vary=0.15, rough=170, lines=[7])
    out["stone_slab_side"] = ss

    # --------------------------------------------------------------- deepslate
    ds = vramp("deepslate/deepslate", 5, contrast=0.3)
    out["deepslate/deepslate"] = P.rock("deepslate", ds, "strata", cracks=2, rough=190)
    out["deepslate/deepslate_top"] = P.rock("deepslate_top", ds, "smooth", cracks=2, rough=190)
    out["deepslate/cobbled_deepslate"] = P.cells("cobbled_deepslate", vramp("deepslate/cobbled_deepslate", 6, contrast=0.36), 9)
    out["deepslate/polished_deepslate"] = P.slab_face("polished_deepslate", vramp("deepslate/polished_deepslate", 5, contrast=0.24), vary=0.2)
    dm = [(34, 34, 38), (42, 42, 46), (50, 50, 54)]
    db = vramp("deepslate/deepslate_bricks", 5, contrast=0.26)
    out["deepslate/deepslate_bricks"] = P.bricks("deepslate_bricks", db, dm, rows=2, cols=1)
    out["deepslate/cracked_deepslate_bricks"] = P.bricks("deepslate_bricks", db, dm, rows=2, cols=1, crack=4, chip=0.06)
    dt = vramp("deepslate/deepslate_tiles", 5, contrast=0.26)
    out["deepslate/deepslate_tiles"] = P.bricks("deepslate_tiles", dt, dm, rows=4, cols=2, vary=0.16)
    out["deepslate/cracked_deepslate_tiles"] = P.bricks("deepslate_tiles", dt, dm, rows=4, cols=2, vary=0.16, crack=4, chip=0.06)
    out["deepslate/chiseled_deepslate"] = P.slab_face("chiseled_deepslate", db, border=1, inset=4, vary=0.12, rough=180)

    # ------------------------------------------------------ other natural rock
    out["tuff"] = P.rock("tuff", vramp("tuff", 5, contrast=0.26), "strata", cracks=1, speck=0.04)
    out["polished_tuff"] = P.slab_face("polished_tuff", vramp("polished_tuff", 5, contrast=0.2), vary=0.22)
    tm = [(62, 66, 62), (72, 76, 72)]
    out["tuff_bricks"] = P.bricks("tuff_bricks", vramp("tuff_bricks", 5, contrast=0.24), tm, rows=2, cols=1)
    out["chiseled_tuff"] = P.slab_face("chiseled_tuff", vramp("chiseled_tuff", 5, contrast=0.24), border=1, lines=[5, 10], vary=0.14)
    out["chiseled_tuff_top"] = P.slab_face("chiseled_tuff_top", vramp("chiseled_tuff_top", 5, contrast=0.22), border=1, inset=3, vary=0.14)
    out["chiseled_tuff_bricks"] = P.slab_face("chiseled_tuff_bricks", vramp("chiseled_tuff_bricks", 5, contrast=0.24), border=1, inset=4, vary=0.14)
    out["chiseled_tuff_bricks_top"] = P.slab_face("chiseled_tuff_bricks_top", vramp("chiseled_tuff_bricks_top", 5, contrast=0.22), border=2, vary=0.14)
    out["calcite"] = P.rock("calcite", vramp("calcite", 5, contrast=0.14), "smooth", cracks=2, rough=170)
    out["dripstone_block"] = P.rock("dripstone_block", vramp("dripstone_block", 5, contrast=0.28), "pillars", cracks=2, speck=0.03)
    out["smooth_basalt"] = P.rock("smooth_basalt", vramp("smooth_basalt", 5, contrast=0.24), "smooth", cracks=1)
    out["bedrock"] = P.cells("bedrock", vramp("bedrock", 6, contrast=0.55), 7, vary=0.5, dome=0.4)
    ob = make_ramp((30, 22, 46), 5, 0.55, warm=0.02)
    t = P.rock("obsidian", ob, "smooth", cracks=3, rough=40)
    out["obsidian"] = t

    # ------------------------------------------------------------- sand/gravel
    out["sand"] = P.rock("sand", vramp("sand", 5, contrast=0.13), "fine", cracks=0, speck=0.07, rough=220, bump=0.7)
    out["nabd/sand_v1"] = P.rock("sand_v1", vramp("sand", 5, contrast=0.13), "fine", cracks=0, speck=0.08, rough=220, bump=0.7)
    variations["flattened_sand"] = ["sand", "nabd/sand_v1"]
    out["red_sand"] = P.rock("red_sand", vramp("red_sand", 5, contrast=0.15), "fine", cracks=0, speck=0.07, rough=220, bump=0.7)
    gv = vramp("gravel", 6, contrast=0.34)
    warm = make_ramp((132, 116, 104), 6, 0.3)
    cool = make_ramp((112, 116, 126), 6, 0.3)
    out["gravel"] = P.cells("gravel", gv, 17, vary=0.35, dome=0.5, tints=[warm, cool], bump=1.1)
    out["nabd/gravel_v1"] = P.cells("gravel_v1", gv, 18, vary=0.35, dome=0.5, tints=[warm, cool], bump=1.1)
    variations["gravel"] = ["gravel", "nabd/gravel_v1"]
    for pre in ("sandstone", "red_sandstone"):
        rp = vramp(f"{pre}_normal", 5, contrast=0.16)
        out[f"{pre}_top"] = P.rock(f"{pre}_top", vramp(f"{pre}_top", 5, contrast=0.12), "fine", cracks=0, speck=0.05, rough=200, bump=0.6)
        out[f"{pre}_bottom"] = P.rock(f"{pre}_bottom", vramp(f"{pre}_bottom", 5, contrast=0.14), "smooth", cracks=2, rough=200)
        side = P.rock(f"{pre}_side", rp, "strata", cracks=0, rough=200, bump=0.8)
        tone_top = make_ramp(mix(vbase(f"{pre}_normal"), (255, 255, 255), 0.12), 5, 0.14)
        side.rgb[0:3] = paint(np.clip(0.55 + (white(rng_of(pre)) - 0.5) * 0.3, 0, 1), tone_top)[0:3]
        side.rgb[3] = (side.rgb[3] * 0.8).astype(np.uint8)
        side.height[3] = 0.25
        out[f"{pre}_normal"] = side
        out[f"{pre}_smooth"] = P.slab_face(f"{pre}_smooth", rp, border=1, lines=[5, 10], vary=0.12, rough=170)
        out[f"{pre}_carved"] = P.slab_face(f"{pre}_carved", rp, border=1, inset=4, vary=0.12, rough=170)
    out["clay"] = P.flat("clay", vramp("clay", 5, contrast=0.12), "smooth", rough=150, amount=0.7)

    # -------------------------------------------------------------------- soil
    dirt_r = vramp("dirt", 5, contrast=0.3)
    stone_peb = make_ramp((150, 140, 132), 5, 0.3)
    out["dirt"] = P.soil("dirt", dirt_r, pebbles=5, pebble_ramp=stone_peb)
    for i in (1, 2):
        out[f"nabd/dirt_v{i}"] = P.soil(f"dirt_v{i}", dirt_r, pebbles=3 + 2 * i, pebble_ramp=stone_peb)
    variations["flattened_dirt"] = ["dirt", "nabd/dirt_v1", "nabd/dirt_v2"]
    out["coarse_dirt"] = P.soil("coarse_dirt", vramp("coarse_dirt", 5, contrast=0.3), pebbles=16, pebble_ramp=stone_peb,
                                clump=((4, 1.0), (8, 1.0), (16, 0.6)))
    out["mud"] = P.soil("mud", vramp("mud", 5, contrast=0.22), pebbles=0, rough=90, clump=((2, 1.0), (4, 0.6)), dither=0.3)
    out["packed_mud"] = P.soil("packed_mud", vramp("packed_mud", 5, contrast=0.2), pebbles=6,
                               pebble_ramp=make_ramp((190, 160, 110), 5, 0.2), rough=200)
    out["mud_bricks"] = P.bricks("mud_bricks", vramp("mud_bricks", 5, contrast=0.2),
                                 [shift(vbase("mud_bricks"), dv=-0.2), shift(vbase("mud_bricks"), dv=-0.15)], rows=4, cols=2)
    rooted = P.soil("dirt", dirt_r, pebbles=2, pebble_ramp=stone_peb)
    rr = make_ramp((176, 150, 120), 4, 0.25)
    r = rng_of("roots")
    for _ in range(5):
        x, y = int(r.integers(N)), int(r.integers(N))
        for i in range(int(r.integers(4, 8))):
            rooted.rgb[y % N, x % N] = rr[2 + (i % 2)]
            rooted.rgb[(y + 1) % N, x % N] = (rooted.rgb[(y + 1) % N, x % N] * 0.75).astype(np.uint8)
            rooted.height[y % N, x % N] = 0.9
            x += int(r.choice([1, 1, 0]))
            y += int(r.choice([1, 0, -1]))
    out["dirt_with_roots"] = rooted

    for wet in ("dry", "wet"):
        fr = vramp(f"farmland_{wet}", 5, contrast=0.3)
        rw = rng_of("farmland")
        g = fbm(rw, ((8, 1.0), (16, 0.6)), sx=4)
        yy = np.arange(N)[:, None] * np.ones((1, N), int)
        furrow = (yy % 4 == 3)
        ridge = (yy % 4 == 0)
        tone = np.clip(0.45 + (g - 0.5) * 0.4 + ridge * 0.2 - furrow * 0.45, 0, 1)
        hgt = np.clip(0.55 + ridge * 0.25 - furrow * 0.4 + (g - 0.5) * 0.1, 0, 1)
        out[f"farmland_{wet}"] = Tex(paint(tone, fr, dither=0.4), hgt, rough=120 if wet == "wet" else 215, bump=1.3)

    # grass (top is biome tinted -> pure grey ramp at the vanilla brightness)
    g_grey = vramp("grass_top", 5, grey=True, contrast=0.3)
    out["grass_top"] = P.turf("grass_top", g_grey, sss=60)
    g_green = vramp("grass_carried", 5, contrast=0.32)
    out["grass_carried"] = P.turf("grass_top", g_green, sss=60)

    dirt = out["dirt"]
    side = P.top_over("grass_side", dirt, P.turf("grass_side_fr", g_grey), depth=3, extra=2)
    side.alpha = np.where(side.mask, 255, 0).astype(np.uint8)      # alpha marks the tinted part
    out["grass_side"] = side
    out["grass_side_carried"] = P.top_over("grass_side", dirt, P.turf("grass_side_fr", g_green), depth=3, extra=2)

    snow_r = make_ramp((236, 244, 250), 5, 0.09, warm=0.03)
    snow = P.rock("snow", snow_r, "fine", cracks=0, rough=150, bump=0.5)
    snow.sss = 90
    out["snow"] = snow
    snowed = P.top_over("grass_side_snow", dirt, snow, depth=3, extra=2)
    out["grass_side_snowed"] = snowed
    out["grass_block_snow"] = snowed

    pod_top = P.soil("podzol_top", vramp("dirt_podzol_top", 5, contrast=0.34), pebbles=7,
                     pebble_ramp=make_ramp((150, 110, 50), 5, 0.3), clump=((4, 1.0), (8, 0.9)))
    out["dirt_podzol_top"] = pod_top
    out["dirt_podzol_side"] = P.top_over("podzol_side", dirt, pod_top, depth=3, extra=1)
    myc = P.soil("mycelium_top", vramp("mycelium_top", 5, contrast=0.2), pebbles=9,
                 pebble_ramp=make_ramp((176, 160, 186), 5, 0.2), clump=((4, 1.0), (8, 0.9), (16, 0.5)))
    out["mycelium_top"] = myc
    out["mycelium_side"] = P.top_over("mycelium_side", dirt, myc, depth=3, extra=2)
    path = P.soil("grass_path_top", vramp("grass_path_top", 5, contrast=0.2), pebbles=8,
                  pebble_ramp=make_ramp((176, 150, 96), 5, 0.2), clump=((4, 1.0), (8, 0.7)))
    out["grass_path_top"] = path
    ps = P.top_over("grass_path_side", dirt, path, depth=2, extra=1)
    ps.alpha[:1, :] = 0                    # path blocks are 15px tall: keep the top row clear
    ps.rgb[1:] = ps.rgb[:-1].copy()
    out["grass_path_side"] = ps
    moss = P.turf("moss_block", moss_ramp(), sss=80, blades=34)
    out["moss_block"] = moss

    # --------------------------------------------------------------- ice family
    ice_r = make_ramp((150, 190, 250), 5, 0.14, warm=0.02)
    ice = P.rock("ice", ice_r, "smooth", cracks=4, rough=20, bump=0.6)
    ice.alpha[:] = 190
    out["ice"] = ice
    out["ice_packed"] = P.rock("ice_packed", vramp("ice_packed", 5, contrast=0.12), "smooth", cracks=5, rough=45, bump=0.6)
    out["blue_ice"] = P.rock("blue_ice", vramp("blue_ice", 5, contrast=0.14), "smooth", cracks=6, rough=25, bump=0.6)

    # -------------------------------------------------------------------- ores
    stone_base = out["stone"]
    deep_base = out["deepslate/deepslate"]
    for ore, g in GEMS.items():
        cl = P.ore_layout("ore:" + ore, g["shape"], ORE_COUNT[ore])
        for base, key, fname in ((stone_base, f"{ore}_ore", f"{ore}_ore"),
                                 (deep_base, f"deepslate/deepslate_{ore}_ore", f"deepslate_{ore}_ore")):
            t = P.ore(base, cl, g["ramp"], metal=g["metal"], gem_rough=g["rough"], emis=g.get("emis", 0))
            out[key] = t
            if ore in ("diamond", "emerald", "gold", "redstone", "lapis"):
                # shimmer: a white glint travels over the clusters
                frames = []
                steps = 12
                for f in range(steps):
                    if f < len(cl):
                        frames.append(P.ore(base, cl, g["ramp"], metal=g["metal"], gem_rough=g["rough"],
                                            emis=g.get("emis", 0), sparkle={f}))
                    else:
                        frames.append(t)
                strip_name = f"nabd/{fname}_shimmer"
                out[strip_name] = stack_frames(frames)
                flip[key] = dict(strip=strip_name, ticks=5, frames=steps)
    # raw ore blocks: nuggety cells
    out["raw_iron_block"] = P.cells("raw_iron_block", vramp("raw_iron_block", 6, contrast=0.3), 9, rough=150)
    out["raw_gold_block"] = P.cells("raw_gold_block", vramp("raw_gold_block", 6, contrast=0.3), 9, rough=110)
    out["raw_copper_block"] = P.cells("raw_copper_block", vramp("raw_copper_block", 6, contrast=0.3), 9, rough=140,
                                      tints=None)
    for nm in ("raw_iron_block", "raw_gold_block", "raw_copper_block"):
        out[nm].metal = 110
