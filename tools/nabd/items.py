"""Item sprites, drawn from scratch in the pack's cartoon style.

Every item is a small character map: each letter is a material region.  The
renderer shades each region from its own silhouette (lit top-left, shaded
bottom-right) and wraps the whole sprite in a soft dark outline.  The game
uses this same picture for the inventory icon and for the item held in the
hand, so both always match.
"""
import json
import os

import numpy as np

from .blocks_rest import shade_mask
from .core import N, Tex, make_ramp, mix, rng_of, shift

HERE = os.path.dirname(os.path.abspath(__file__))
ISTATS = json.load(open(os.path.join(HERE, "vanilla_item_stats.json")))


def R(c, contrast=0.42, **kw):
    return make_ramp(c, 5, contrast, **kw)


WOOD, STICK = R((156, 112, 62)), R((128, 92, 52))
STONE, IRON = R((142, 142, 148), 0.36), R((214, 218, 226), 0.3)
GOLD, DIAMOND = R((250, 206, 56)), R((90, 224, 212))
NETHERITE = R((80, 72, 78), 0.5, sat=1.0, lift=0.0)
COPPER, LEATHER, CHAIN = R((228, 130, 86), 0.36), R((150, 92, 52)), R((150, 154, 162), 0.36)
EMERALD, REDSTONE, LAPIS = R((40, 200, 96)), R((220, 30, 24)), R((40, 92, 210))
COAL, BONE, PAPER = R((52, 52, 60), 0.6, sat=1.0, lift=0.0), R((232, 228, 210), 0.2), R((238, 232, 214), 0.16)
QUARTZ, AMETHYST, ECHO, PRISM = R((236, 228, 220), 0.18), R((160, 110, 226)), R((20, 80, 100), 0.5), R((110, 190, 170))
GREEN, RED, MEAT_RAW, MEAT_COOKED = R((80, 170, 60)), R((214, 44, 40)), R((226, 110, 110), 0.34), R((170, 100, 56))
BREAD, WATER, LAVA, MILK = R((196, 140, 64), 0.36), R((70, 130, 240), 0.3), R((250, 130, 30), 0.3), R((244, 244, 240), 0.1)
DYES = {"black": (40, 40, 46), "red": (190, 44, 40), "green": (86, 120, 40), "brown": (124, 78, 44), "blue": (50, 70, 180),
        "purple": (130, 60, 180), "cyan": (40, 140, 150), "silver": (156, 156, 150), "gray": (86, 90, 94),
        "pink": (240, 150, 180), "lime": (120, 200, 50), "yellow": (250, 210, 60), "light_blue": (90, 170, 240),
        "magenta": (200, 80, 190), "orange": (240, 130, 40), "white": (236, 238, 240)}


def grid():
    return [["."] * N for _ in range(N)]


def stamp(g, rows, x0=0, y0=0):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != "." and 0 <= y0 + dy < N and 0 <= x0 + dx < N:
                g[y0 + dy][x0 + dx] = ch
    return g


def diag(g, ch, x0=1, y0=13, length=9, thick=2):
    """A handle running from bottom-left up to the right."""
    for i in range(length):
        for k in range(thick):
            x, y = x0 + i + k, y0 - i
            if 0 <= x < N and 0 <= y < N:
                g[y][x] = ch
    return g


def disc(g, ch, cx, cy, rad, squash=1.0):
    for y in range(N):
        for x in range(N):
            if ((x - cx) ** 2 + ((y - cy) / squash) ** 2) <= rad * rad + 0.3:
                g[y][x] = ch
    return g


def render(g, pal, speck=None, seed="", extra=None, emis=None, metal=None):
    """g: 16x16 chars. pal: {char: 5-tone ramp}. speck: {char: fraction} adds
    one-step grains inside a region. extra: [(x, y, colour)] painted last."""
    chars = np.array(g)
    rgb = np.zeros((N, N, 3), np.uint8)
    alpha = np.zeros((N, N), np.uint8)
    hgt = np.zeros((N, N))
    em = np.zeros((N, N))
    mt = np.zeros((N, N))
    dark = np.zeros((N, N, 3), np.uint8)
    r = rng_of("item:" + seed)
    for ch, ramp in pal.items():
        m = chars == ch
        if not m.any():
            continue
        idx = shade_mask(m)
        if speck and ch in speck:
            flip = (r.random((N, N)) < speck[ch]) & (idx == 2)
            idx = np.where(flip, np.where(r.random((N, N)) < 0.5, 1, 3), idx)
        rgb = np.where(m[..., None], np.array(ramp, np.uint8)[idx], rgb)
        dark = np.where(m[..., None], np.array(mix(ramp[0], (20, 16, 26), 0.5), np.uint8), dark)
        alpha = np.where(m, 255, alpha)
        hgt = np.where(m, 0.45 + idx * 0.12, hgt)
        if emis and ch in emis:
            em = np.where(m, emis[ch], em)
        if metal and ch in metal:
            mt = np.where(m, metal[ch], mt)
    # outline: empty pixels touching the sprite take a darkened neighbour colour
    solid = alpha > 0
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.roll(np.roll(solid, dy, 0), dx, 1)
        nd = np.roll(np.roll(dark, dy, 0), dx, 1)
        edge = nb & ~solid & (alpha == 0)
        if dy == 1:
            edge[0, :] = False
        if dy == -1:
            edge[-1, :] = False
        if dx == 1:
            edge[:, 0] = False
        if dx == -1:
            edge[:, -1] = False
        rgb = np.where(edge[..., None], nd, rgb)
        alpha = np.where(edge, 255, alpha)
        hgt = np.where(edge, 0.3, hgt)
    if extra:
        for (x, y, c) in extra:
            rgb[y, x] = c
            alpha[y, x] = 255
    t = Tex(rgb, hgt, alpha=alpha, rough=np.where(mt > 0, 80, 190), metal=mt, bump=0.8)
    t.emis = em
    return t


# ---------------------------------------------------------------- shapes
PICK = [".HHHHHHH...", "HHHHHHHHH..", "HH.....HHH.", "H.......HHH", ".........HH", ".........HH", "..........H"]
AXE = [".HHH....", "HHHHH...", "HHHHHH..", ".HHHHHH.", "..HHHHHH", "...HHHH.", "....HH.."]       # broad wedge blade across the haft
SHOVEL = ["...HH", "..HHH", ".HHHH", "HHHH.", "HHH..", "HH..."]                                            # pointed spade
HOE = ["HHHHHH", "HHHHHH", "....HH", "....HH"]
SWORD = ["............BB..", "...........BBB..", "..........BBB...", ".........BBB....", "........BBB.....", ".......BBB......",
         "..G...BBB.......", "..GG.BBB........", "...GGBB.........", "....GG..........", "...SSGG.........", "..SS..G.........",
         ".PS.............", ".PP............."]
HELMET = ["....HHHHHHHH....", "...HHHHHHHHHH...", "..HHHHHHHHHHHH..", "..HHHHHHHHHHHH..", "..HHHHHHHHHHHH..", "..HHH......HHH..",
          "..HHH......HHH..", "..HH........HH..", "..HH........HH.."]
CHEST = ["..HH........HH..", ".HHHH......HHHH.", ".HHHHH....HHHHH.", ".HHHHHHHHHHHHHH.", "..HHHHHHHHHHHH..", "...HHHHHHHHHH...",
         "...HHHHHHHHHH...", "...HHHHHHHHHH...", "...HHHHHHHHHH...", "...HHHHHHHHHH...", "...HHHHHHHHHH...", "....HHHHHHHH...."]
LEGS = ["...HHHHHHHHHH...", "...HHHHHHHHHH...", "...HHHHHHHHHH...", "...HHHH..HHHH...", "...HHHH..HHHH...", "...HHH....HHH...",
        "...HHH....HHH...", "...HHH....HHH...", "...HHH....HHH...", "...HHH....HHH...", "...HHH....HHH...", "...HHH....HHH..."]
BOOTS = ["..HHH......HHH..", "..HHH......HHH..", "..HHH......HHH..", "..HHH......HHH..", "..HHH......HHH..", "..HHHH....HHHH..",
         ".HHHHH....HHHHH.", ".HHHHH....HHHHH."]
INGOT = ["......IIIIIIII..", ".....IIIIIIIII..", "....IIIIIIIIII..", "...IIIIIIIIII...", "..IIIIIIIIII....", "..IIIIIIIII.....",
         "..IIIIIIII......"]
NUGGET = ["......NNN.......", ".....NNNNN......", ".....NNNNNN.....", "......NNNNN.....", ".......NNN......"]
GEM = ["....DDDDDDDD....", "...DDDDDDDDDD...", "..DDDDDDDDDDDD..", "..DDDDDDDDDDDD..", "...DDDDDDDDDD...", "....DDDDDDDD....",
       ".....DDDDDD.....", "......DDDD......", ".......DD......."]
HEX = [".....EEEEEE.....", "....EEEEEEEE....", "...EEEEEEEEEE...", "...EEEEEEEEEE...", "...EEEEEEEEEE...", "...EEEEEEEEEE...",
       "...EEEEEEEEEE...", "...EEEEEEEEEE...", "....EEEEEEEE....", ".....EEEEEE....."]
LUMP = ["......CCCC......", "....CCCCCCCC....", "...CCCCCCCCCC...", "...CCCCCCCCCCC..", "..CCCCCCCCCCCC..", "..CCCCCCCCCCC...",
        "...CCCCCCCCCC...", "....CCCCCCC....."]
PILE = [".......DD.......", ".....DDDDDD.....", "....DDDDDDDD....", "...DDDDDDDDDD...", "..DDDDDDDDDDDD.."]
SHARD = ["..........SS....", ".........SSS....", "........SSSS....", ".......SSSS.....", "......SSSS......", ".....SSSS.......",
         "....SSSS........", "...SSSS.........", "...SSS..........", "...SS..........."]
BRICK = ["...IIIIIIIIII...", "..IIIIIIIIIIII..", "..IIIIIIIIIIII..", "..IIIIIIIIIIII..", "..IIIIIIIIIIII..", "...IIIIIIIIII..."]
BUCKET = ["..HHHHHHHHHHHH..", "..HWWWWWWWWWWH..", "..HHHHHHHHHHHH..", "...HHHHHHHHHH...", "...HHHHHHHHHH...", "...HHHHHHHHHH...",
          "....HHHHHHHH....", "....HHHHHHHH....", ".....HHHHHH....."]
BOOK = ["...CCCCCCCCC....", "..CCCCCCCCCCP...", "..CCCCCCCCCCP...", "..CCCCCCCCCCP...", "..CCCCCCCCCCP...", "..CCCCCCCCCCP...",
        "..CCCCCCCCCCP...", "..CCCCCCCCCCP...", "..CCCCCCCCCCP...", "...PPPPPPPPPP..."]
FISH = ["................", ".......FFFF.....", "..F...FFFFFFF...", "..FF.FFFFFFFFF..", "..FFFFFFFFFFFE..", "..FF.FFFFFFFFF..",
        "..F...FFFFFFF...", ".......FFFF....."]
DRUM = ["........MMMM....", ".......MMMMMM...", "......MMMMMMM...", "......MMMMMMM...", ".....MMMMMMM....", "....BMMMMMM.....",
        "...BB.MMMM......", "..BB............", ".BBB............", ".BB............."]
STEAK = ["....MMMMMMM.....", "...MMMMMMMMMM...", "..MMMMFFMMMMMM..", "..MMMFFFFMMMMM..", "..MMMMFFMMMMMM..", "..MMMMMMMMMMM...",
         "...MMMMMMMMM....", ".....MMMMM......"]
BOW = ["......WWW.......", "....WW..S.......", "...W....S.......", "..W.....S.......", "..W.....S.......", "..W.....S.......",
       "..W.....S.......", "..W.....S.......", "...W....S.......", "....WW..S.......", "......WWW......."]


def centred(rows, ch_map=None, y0=None):
    g = grid()
    y0 = (N - len(rows)) // 2 if y0 is None else y0
    stamp(g, rows, 0, y0)
    if ch_map:
        for y in range(N):
            for x in range(N):
                g[y][x] = ch_map.get(g[y][x], g[y][x])
    return g


def tool(head, hx, hy):
    g = diag(grid(), "S")
    return stamp(g, head, hx, hy)


def build(out):
    def put(name, tex):
        if name in ISTATS:
            out[name] = tex

    mats = {"wood": WOOD, "stone": STONE, "iron": IRON, "gold": GOLD, "diamond": DIAMOND, "netherite": NETHERITE, "copper": COPPER}
    metal_of = {"iron": 220, "gold": 240, "netherite": 220, "copper": 210, "diamond": 60}
    # ------------------------------------------------------------ tools
    for m, ramp in mats.items():
        mt = {"H": metal_of.get(m, 0), "B": metal_of.get(m, 0)}
        put(f"{m}_pickaxe", render(tool(PICK, 3, 1), {"S": STICK, "H": ramp}, metal=mt))
        put(f"{m}_axe", render(tool(AXE, 6, 1), {"S": STICK, "H": ramp}, metal=mt))
        put(f"{m}_shovel", render(tool(SHOVEL, 9, 1), {"S": STICK, "H": ramp}, metal=mt))
        put(f"{m}_hoe", render(tool(HOE, 7, 2), {"S": STICK, "H": ramp}, metal=mt))
        guard = STICK if m in ("wood", "stone") else R(shift(ramp[1], dv=-0.1), 0.4)
        put(f"{m}_sword", render(centred(SWORD, y0=1), {"B": ramp, "G": guard, "S": STICK, "P": guard}, metal=mt))
    # ------------------------------------------------------------ armour
    for m, ramp in {"leather": LEATHER, "chainmail": CHAIN, "iron": IRON, "gold": GOLD, "diamond": DIAMOND,
                    "netherite": NETHERITE, "copper": COPPER}.items():
        mt = {"H": metal_of.get(m, 150 if m == "chainmail" else 0)}
        sp = {"H": 0.3} if m == "chainmail" else None
        for part, rows in (("helmet", HELMET), ("chestplate", CHEST), ("leggings", LEGS), ("boots", BOOTS)):
            put(f"{m}_{part}", render(centred(rows), {"H": ramp}, speck=sp, seed=m + part, metal=mt))
    put("turtle_helmet", render(centred(HELMET), {"H": R((70, 160, 70))}, speck={"H": 0.25}, seed="turtle"))
    # ------------------------------------------------------- ingots & co
    for name, ramp, m in (("iron_ingot", IRON, 220), ("gold_ingot", GOLD, 240), ("copper_ingot", COPPER, 210),
                          ("netherite_ingot", NETHERITE, 220)):
        put(name, render(centred(INGOT), {"I": ramp}, metal={"I": m}))
    for name, ramp in (("brick", R((180, 90, 70), 0.3)), ("netherbrick", R((70, 30, 36), 0.4)), ("resin_brick", R((226, 110, 40), 0.3))):
        put(name, render(centred(BRICK), {"I": ramp}))
    for name, ramp, m in (("iron_nugget", IRON, 220), ("gold_nugget", GOLD, 240), ("copper_nugget", COPPER, 210)):
        put(name, render(centred(NUGGET), {"N": ramp}, metal={"N": m}))
    spark = [(5, 5, (255, 255, 255))]
    put("diamond", render(centred(GEM), {"D": DIAMOND}, extra=spark))
    put("ruby", render(centred(GEM), {"D": R((226, 40, 70))}, extra=spark))
    put("emerald", render(centred(HEX), {"E": EMERALD}, extra=[(5, 5, (236, 255, 240))]))
    put("quartz", render(centred(SHARD), {"S": QUARTZ}))
    put("amethyst_shard", render(centred(SHARD), {"S": AMETHYST}))
    put("echo_shard", render(centred(SHARD), {"S": ECHO}, extra=[(8, 7, (70, 220, 230))], emis={"S": 30}))
    put("prismarine_shard", render(centred(SHARD), {"S": PRISM}))
    put("flint", render(centred(SHARD), {"S": R((70, 70, 78), 0.5)}))
    put("prismarine_crystals", render(centred(PILE, y0=7), {"D": R((190, 236, 226), 0.3)}, extra=[(7, 5, (255, 255, 255)), (10, 6, (255, 255, 255))]))
    for name, ramp, sp in (("coal", COAL, 0.3), ("charcoal", R((64, 52, 44), 0.55), 0.3), ("netherite_scrap", R((96, 70, 62), 0.5), 0.35),
                           ("raw_iron", R((214, 176, 150), 0.34), 0.4), ("raw_gold", R((244, 190, 60), 0.36), 0.4),
                           ("raw_copper", R((214, 120, 84), 0.36), 0.4), ("clay_ball", R((160, 166, 180), 0.2), 0.1),
                           ("leather", LEATHER, 0.2), ("rotten_flesh", R((170, 90, 60), 0.4), 0.4)):
        put(name, render(centred(LUMP), {"C": ramp}, speck={"C": sp}, seed=name))
    for name, ramp, glow in (("redstone_dust", REDSTONE, 40), ("glowstone_dust", R((250, 210, 90)), 120), ("gunpowder", R((110, 110, 116), 0.4), 0),
                             ("sugar", R((244, 244, 246), 0.12), 0), ("blaze_powder", R((250, 160, 30)), 100)):
        put(name, render(centred(PILE, y0=7), {"D": ramp}, speck={"D": 0.35}, seed=name, emis={"D": glow},
                         extra=[(6, 5, ramp[4]), (10, 4, ramp[3])]))
    put("dye_powder_blue", render(centred(LUMP), {"C": LAPIS}, speck={"C": 0.3}, seed="lapis"))     # lapis lazuli
    for name, col in DYES.items():
        g = disc(grid(), "D", 7.5, 8.5, 4.6)
        t = render(g, {"D": R(col, 0.36)}, extra=[(6, 6, R(col, 0.36)[4])])
        if name != "blue":
            put(f"dye_powder_{name}", t)
        put(f"dye_powder_{name}_new", t)
    put("dye_powder_glow", render(disc(grid(), "D", 7.5, 8.5, 4.6), {"D": R((60, 210, 190))}, emis={"D": 160}))
    # ------------------------------------------------------- balls & rods
    for name, col, glow in (("slimeball", (120, 200, 90), 0), ("snowball", (240, 246, 250), 0), ("ender_pearl", (30, 110, 100), 0),
                            ("magma_cream", (230, 150, 50), 60), ("fireball", (230, 90, 30), 150), ("heartofthesea_closed", (40, 130, 200), 60),
                            ("wind_charge", (190, 210, 240), 0), ("egg", (236, 220, 190), 0), ("blue_egg", (130, 190, 220), 0),
                            ("brown_egg", (176, 124, 90), 0)):
        egg = name.endswith("egg")
        g = disc(grid(), "D", 7.5, 8.0, 4.8 if not egg else 4.2, squash=1.0 if not egg else 1.3)
        put(name, render(g, {"D": R(col, 0.36)}, extra=[(6, 5, (255, 255, 255))], emis={"D": glow}))
    g = disc(grid(), "D", 7.5, 8.0, 4.8)
    g = disc(g, "P", 7.5, 8.0, 2.0)
    put("ender_eye", render(g, {"D": R((60, 170, 110)), "P": R((20, 50, 40), 0.5)}, extra=[(7, 7, (190, 255, 210))]))
    for name, ramp, glow in (("stick", STICK, 0), ("blaze_rod", R((250, 190, 40)), 120), ("breeze_rod", R((170, 190, 236), 0.3), 40),
                             ("bone", BONE, 0)):
        g = diag(grid(), "S", 2, 13, 11)
        if name == "bone":
            stamp(g, ["BB", "BB"], 1, 13)
            stamp(g, ["BB", "BB"], 12, 2)
        put(name, render(g, {"S": ramp, "B": ramp}, emis={"S": glow}))
    g = diag(grid(), "S", 2, 13, 10, thick=1)
    stamp(g, ["HHH", ".HH", "..H"], 11, 1)
    stamp(g, ["F.", "FF", ".F"], 1, 12)
    put("arrow", render(g, {"S": STICK, "H": STONE, "F": R((236, 236, 240), 0.14)}))
    put("bow_standby", render(centred(BOW), {"W": WOOD, "S": R((230, 230, 224), 0.12)}))
    # ------------------------------------------------------------ misc
    for name, fill in (("bucket_empty", None), ("bucket_water", WATER), ("bucket_lava", LAVA), ("bucket_milk", MILK),
                       ("bucket_powder_snow", R((246, 250, 254), 0.08))):
        pal = {"H": IRON, "W": fill or R((120, 124, 132), 0.3)}
        put(name, render(centred(BUCKET), pal, metal={"H": 220}, emis={"W": 180 if name == "bucket_lava" else 0}))
    put("book_normal", render(centred(BOOK), {"C": R((150, 80, 44)), "P": PAPER}))
    put("book_writable", render(centred(BOOK), {"C": R((150, 80, 44)), "P": PAPER}, extra=[(11, 4, (40, 40, 60)), (12, 3, (236, 236, 240))]))
    put("book_written", render(centred(BOOK), {"C": R((120, 50, 130)), "P": PAPER}, extra=[(6, 7, (250, 214, 90)), (7, 7, (250, 214, 90))]))
    put("book_enchanted", render(centred(BOOK), {"C": R((120, 50, 160)), "P": PAPER}, emis={"C": 60}, extra=[(6, 7, (150, 240, 255)), (7, 8, (150, 240, 255))]))
    g = centred(["...PPPPPPPPP....", "...PPPPPPPPPP...", "..PPPPPPPPPPP...", "..PPPPPPPPPPP...", "..PPPPPPPPPPP...", "..PPPPPPPPPP....",
                 "...PPPPPPPPP...."])
    put("paper", render(g, {"P": PAPER}))
    put("map_empty", render(g, {"P": R((226, 208, 170), 0.16)}))
    g = centred(["..HHHHHHHHHHHH..", "...HHHHHHHHHH...", "....HHHHHHHH....", ".....HHHHHH....."], y0=7)
    put("bowl", render(g, {"H": WOOD}))
    for name, col in (("mushroom_stew", (190, 150, 120)), ("beetroot_soup", (180, 40, 60)), ("rabbit_stew", (200, 140, 80)),
                      ("suspicious_stew", (150, 190, 110))):
        gg = [row[:] for row in g]
        stamp(gg, ["..WWWWWWWWWWWW.."], 0, 6)
        put(name, render(gg, {"H": WOOD, "W": R(col, 0.24)}))
    g = centred(["...SS....SS.....", "..S..S..S..S....", ".S....SS....S...", "..S........S....", "...S......S.....", "....SS..SS......",
                 "......SS........"])
    put("string", render(g, {"S": R((236, 236, 232), 0.12)}))
    g = diag(grid(), "F", 3, 13, 9, thick=3)
    stamp(g, ["FF", "FFF", ".FF"], 11, 2)
    put("feather", render(g, {"F": R((240, 240, 244), 0.14)}, extra=[(3, 13, (150, 150, 156)), (4, 12, (150, 150, 156))]))
    # ------------------------------------------------------------ food
    def fruit(col, leaf=True, glow=0):
        g = disc(grid(), "A", 7.5, 9.0, 4.8)
        stamp(g, ["T", "T"], 7, 2)
        if leaf:
            stamp(g, ["LL", "LL."], 8, 2)
        return render(g, {"A": R(col, 0.36), "T": STICK, "L": GREEN}, extra=[(5, 7, (255, 255, 255))], emis={"A": glow})
    put("apple", fruit((214, 40, 40)))
    put("apple_golden", fruit((250, 206, 56), glow=40))
    g = centred(["....BBBBBBBB....", "..BBBBBBBBBBBB..", ".BBBBBBBBBBBBBB.", ".BBBBBBBBBBBBBB.", "..BBBBBBBBBBBB..", "...BBBBBBBBBB..."])
    put("bread", render(g, {"B": BREAD}, extra=[(5, 6, BREAD[0]), (8, 6, BREAD[0]), (11, 6, BREAD[0])]))
    for name, col in (("potato", (200, 160, 90)), ("potato_baked", (214, 150, 70)), ("potato_poisonous", (170, 180, 90))):
        g = disc(grid(), "A", 7.5, 8.5, 4.6, squash=0.78)
        put(name, render(g, {"A": R(col, 0.3)}, speck={"A": 0.2}, seed=name))
    for name, col in (("carrot", (240, 130, 30)), ("carrot_golden", (250, 206, 56))):
        g = diag(grid(), "C", 2, 13, 8, thick=3)
        stamp(g, ["L.L", ".LL", "LL."], 10, 2)
        put(name, render(g, {"C": R(col, 0.36), "L": GREEN}))
    g = diag(grid(), "C", 3, 12, 6, thick=3)
    stamp(g, ["L.L", ".LL", "LL."], 9, 4)
    put("beetroot", render(disc(g, "C", 6, 10, 3), {"C": R((170, 30, 60)), "L": GREEN}))
    for raw, cooked in (("beef_raw", "beef_cooked"), ("porkchop_raw", "porkchop_cooked"), ("mutton_raw", "mutton_cooked"),
                        ("hoglin_meat_raw", "hoglin_meat_cooked")):
        put(raw, render(centred(STEAK), {"M": MEAT_RAW, "F": R((250, 220, 214), 0.12)}))
        put(cooked, render(centred(STEAK), {"M": MEAT_COOKED, "F": R((220, 170, 110), 0.2)}))
    for raw, cooked in (("chicken_raw", "chicken_cooked"), ("rabbit_raw", "rabbit_cooked")):
        put(raw, render(centred(DRUM), {"M": R((240, 190, 170), 0.24), "B": BONE}))
        put(cooked, render(centred(DRUM), {"M": R((196, 130, 60), 0.34), "B": BONE}))
    for name, col in (("fish_raw", (110, 150, 170)), ("fish_cooked", (190, 150, 110)), ("fish_salmon_raw", (226, 110, 90)),
                      ("fish_salmon_cooked", (220, 150, 110)), ("fish_clownfish_raw", (240, 130, 40)), ("fish_pufferfish_raw", (240, 210, 70))):
        put(name, render(centred(FISH), {"F": R(col, 0.34), "E": R((30, 30, 36), 0.4)}))
    g = disc(grid(), "A", 7.5, 8.0, 5.0)
    put("cookie", render(g, {"A": R((200, 140, 70), 0.3)}, extra=[(5, 6, (80, 50, 30)), (9, 7, (80, 50, 30)), (7, 10, (80, 50, 30)), (10, 10, (80, 50, 30))]))
    g = centred(["..RRRRRRRRRRRR..", "..RRRRRRRRRRRR..", "...RRRRRRRRRR...", "....RRRRRRRR....", ".....GGGGGG....."], y0=6)
    put("melon", render(g, {"R": R((230, 60, 60), 0.3), "G": GREEN}, extra=[(5, 7, (40, 30, 30)), (8, 8, (40, 30, 30)), (10, 7, (40, 30, 30))]))
    g = centred(["..CCCCCCCCCCCC..", "..CCCCCCCCCCCC..", "..PPPPPPPPPPPP..", "..PPPPPPPPPPPP..", "...PPPPPPPPPP..."], y0=6)
    put("pumpkin_pie", render(g, {"C": R((230, 150, 50), 0.3), "P": BREAD}))
    g = grid()
    for x in (3, 6, 9, 12):
        for k in range(9):
            g[13 - k][x + (1 if k > 5 else 0)] = "W"
        stamp(g, ["W", "W", "W"], x - 1, 3)
    put("wheat", render(g, {"W": R((220, 180, 70), 0.34)}))
    for name, col in (("seeds_wheat", (120, 170, 60)), ("seeds_melon", (60, 50, 44)), ("seeds_pumpkin", (230, 220, 180)),
                      ("seeds_beetroot", (180, 150, 120)), ("torchflower_seeds", (230, 130, 50))):
        g = grid()
        for (x, y) in ((4, 5), (9, 4), (6, 9), (11, 9), (4, 12), (9, 12)):
            stamp(g, ["SS", "SS"], x, y)
        put(name, render(g, {"S": R(col, 0.36)}))
    g = disc(grid(), "A", 6, 9, 2.6)
    g = disc(g, "A", 10, 9, 2.6)
    stamp(g, ["T", "T", "T"], 8, 3)
    put("sweet_berries", render(g, {"A": R((200, 30, 50)), "T": GREEN}))
    put("glow_berries", render(g, {"A": R((250, 180, 50)), "T": GREEN}, emis={"A": 160}))
    g = disc(grid(), "A", 7.5, 8, 4.4)
    put("chorus_fruit", render(g, {"A": R((150, 110, 170), 0.34)}, speck={"A": 0.25}, seed="chorus"))
    put("chorus_fruit_popped", render(g, {"A": R((190, 150, 210), 0.3)}, speck={"A": 0.4}, seed="chorus_pop"))
    put("spider_eye", render(disc(disc(grid(), "A", 7.5, 8, 4.4), "P", 7.5, 8, 1.8), {"A": R((170, 30, 50)), "P": R((40, 10, 20), 0.5)}))
    put("honeycomb", render(centred(BRICK), {"I": R((240, 170, 40), 0.34)}, extra=[(5, 7, (190, 110, 20)), (8, 8, (190, 110, 20)), (10, 7, (190, 110, 20))]))
    put("nether_star", render(centred(GEM), {"D": R((240, 240, 220), 0.2)}, emis={"D": 200}, extra=[(7, 6, (255, 255, 255))]))
    put("ghast_tear", render(disc(grid(), "D", 7.5, 9.0, 3.6, squash=1.3), {"D": R((220, 240, 244), 0.2)}, extra=[(6, 7, (255, 255, 255))]))
    put("totem", render(centred(["......GGGG......", ".....GGGGGG.....", ".....GEGGEG.....", "..GG.GGGGGG.GG..", "..GGGGGGGGGGGG..", ".....GGGGGG.....",
                                  ".....GGGGGG.....", ".....GGGGGG.....", "......GGGG......", "......G..G......"]),
                        {"G": GOLD, "E": EMERALD}, metal={"G": 200}))
