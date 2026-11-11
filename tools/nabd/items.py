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


def exact(rows, groups, checker=False, extra=None, metal=None, emis=None):
    """Hand-placed pixels.  Characters: 0-4 = main material tones (dark to
    light), a-e = trim tones, v-z = handle tones, P-T = a second body colour,
    '.' = empty.  A soft dark outline is added around the finished sprite."""
    rows = [r.ljust(N, ".")[:N] for r in rows] + ["." * N] * (N - len(rows))
    rgb = np.zeros((N, N, 3), np.uint8)
    alpha = np.zeros((N, N), np.uint8)
    hgt = np.zeros((N, N))
    em = np.zeros((N, N))
    mt = np.zeros((N, N))
    dark = np.zeros((N, N, 3), np.uint8)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch.isdigit():
                grp, tone = "M", int(ch)
            elif ch in "abcde":
                grp, tone = "A", ord(ch) - 97
            elif ch in "vwxyz":
                grp, tone = "V", ord(ch) - 118
            elif ch in "PQRST":                              # a second body colour (belly, filling, pages...)
                grp, tone = "P", ord(ch) - 80
            else:
                raise ValueError(f"bad sprite character {ch!r}")
            ramp = groups[grp]
            if checker and grp == "M" and (x + y) % 2 == 0 and 0 < tone:
                tone -= 1                                    # chain links
            rgb[y, x] = ramp[tone]
            dark[y, x] = mix(ramp[0], (20, 16, 26), 0.5)
            alpha[y, x] = 255
            hgt[y, x] = 0.45 + tone * 0.12
            if metal and grp in metal:
                mt[y, x] = metal[grp]
            if emis and grp in emis:
                em[y, x] = emis[grp]
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


# Weapons, tools and armour are placed pixel by pixel: a lit edge, a body
# tone and a shaded edge on every blade and plate, seams and belts on armour.
X_SWORD = ["", ".............43.", "............431.", "...........431..", "..........431...", ".........431....", "........431.....",
           ".......431......", "..dc..431.......", "...dc431........", "....dcb.........", "...xwdcb........", "..xw..dc........",
           ".cb.............", ".ba............."]
X_PICK = ["", ".....4444443....", "...4433333332...", "..43.....32221..", "..3.......xw21..", ".........xw.21..", "........xw..21..",
          ".......xw...11..", "......xw....10..", ".....xw.....0...", "....xw..........", "...xw...........", "..xw............",
          ".xw.............", ".w.............."]
X_AXE = ["", ".............xw.", ".........443xw..", ".......4433xw...", ".....44333xw2...", "....44333xw21...", "....4333xw1.....",
         "....433xw.......", "....32xw........", ".....xw.........", "....xw..........", "...xw...........", "..xw............",
         ".xw............."]            # crescent blade hugging the haft, small poll behind, haft tip showing above
X_SHOVEL = ["", "...........443..", "..........44332.", ".........443321.", ".........43321..", "........x3321...", ".......xw21.....",
            "......xw........", ".....xw.........", "....xw..........", "...xw...........", "..xw............", ".xw.............",
            ".w.............."]
X_HOE = ["", "......4444443...", "......33333321..", "......31...xw...", "......1...xw....", ".........xw.....", "........xw......",
         ".......xw.......", "......xw........", ".....xw.........", "....xw..........", "...xw...........", "..xw............",
         ".xw.............", ".w.............."]
X_HELMET = ["", "", ".....444444.....", "...4443333332...", "..443333333321..", "..433333333321..", "..abbbbbbbbbba..",
            "..432.3221.321..", "..432..31..321..", "..432..21..321..", "..322......221..", "..21........10.."]
X_CHEST = ["", "..443......443..", ".44332....44332.", ".433332aa433321.", ".43333bbbb33321.", ".43214333321321.", ".32114333321211.",
           "....43333321....", "....42222221....", "....43333321....", "....43333321....", "....42222221....", "....abbbbbba....",
           ".....322221....."]
X_LEGS = ["", "...abbbbbbbba...", "...4333cc3321...", "...4333333321...", "...4333223321...", "...4332..4321...", "...4332..4321...",
          "...4332..4321...", "...4222..4221...", "...4332..4321...", "...4332..4321...", "...4332..4321...", "...3321..3321...",
          "...2211..2210..."]
X_BOOTS = ["", "", "", "", "...abb....abb...", "...432....432...", "...432....432...", "...432....432...", "...432....432...",
           "..4332....4332..", ".43322....43322.", ".00000....00000."]


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
        mt = {"M": metal_of.get(m, 0), "A": metal_of.get(m, 0)}
        grp = {"M": ramp, "V": STICK, "A": STICK if m in ("wood", "stone") else R(shift(ramp[1], dv=-0.08), 0.4)}
        for part, rows in (("pickaxe", X_PICK), ("axe", X_AXE), ("shovel", X_SHOVEL), ("hoe", X_HOE), ("sword", X_SWORD)):
            put(f"{m}_{part}", exact(rows, grp, metal=mt))
    # ------------------------------------------------------------ armour
    trims = {"leather": R((96, 56, 30)), "chainmail": R((96, 100, 110), 0.36), "iron": R((150, 156, 168), 0.3),
             "gold": R((214, 130, 30)), "diamond": R((40, 150, 160)), "netherite": R((190, 150, 70), 0.36),
             "copper": R((150, 80, 52), 0.36)}
    for m, ramp in {"leather": LEATHER, "chainmail": CHAIN, "iron": IRON, "gold": GOLD, "diamond": DIAMOND,
                    "netherite": NETHERITE, "copper": COPPER}.items():
        mt = {"M": metal_of.get(m, 150 if m == "chainmail" else 0)}
        for part, rows in (("helmet", X_HELMET), ("chestplate", X_CHEST), ("leggings", X_LEGS), ("boots", X_BOOTS)):
            put(f"{m}_{part}", exact(rows, {"M": ramp, "A": trims[m]}, checker=(m == "chainmail"), metal=mt))
    put("turtle_helmet", exact(X_HELMET, {"M": R((70, 160, 70)), "A": R((40, 110, 60))}))
    # ------------------------------------------------------- ingots & co
    for name, ramp, m in (("iron_ingot", IRON, 220), ("gold_ingot", GOLD, 240), ("copper_ingot", COPPER, 210),
                          ("netherite_ingot", NETHERITE, 220), ("brick", R((180, 90, 70), 0.3), 0),
                          ("netherbrick", R((90, 40, 46), 0.4), 0), ("resin_brick", R((226, 110, 40), 0.3), 0)):
        put(name, exact(X_INGOT, {"M": ramp}, metal={"M": m}))
    for name, ramp, m in (("iron_nugget", IRON, 220), ("gold_nugget", GOLD, 240), ("copper_nugget", COPPER, 210)):
        put(name, exact(X_NUGGET, {"M": ramp}, metal={"M": m}))
    white = (255, 255, 255)
    put("diamond", exact(X_GEM, {"M": DIAMOND}, extra=[(5, 4, white)]))
    put("ruby", exact(X_GEM, {"M": R((226, 40, 70))}, extra=[(5, 4, white)]))
    put("emerald", exact(X_EMERALD, {"M": EMERALD}, extra=[(5, 4, (236, 255, 240))]))
    for name, ramp, glow in (("quartz", QUARTZ, 0), ("amethyst_shard", AMETHYST, 0), ("echo_shard", ECHO, 40), ("prismarine_shard", PRISM, 0)):
        put(name, exact(X_SHARD, {"M": ramp}, emis={"M": glow}))
    put("flint", exact(X_FLINT, {"M": R((76, 76, 86), 0.5)}))
    put("prismarine_crystals", exact(X_PILE, {"M": R((190, 236, 226), 0.3)}, extra=[(6, 6, white), (10, 5, white)]))
    for name, ramp, specks in (("coal", COAL, None), ("charcoal", R((70, 56, 46), 0.55), None), ("netherite_scrap", R((96, 70, 62), 0.5), (206, 170, 150)),
                               ("raw_iron", R((190, 150, 130), 0.34), (236, 204, 180)), ("raw_gold", R((224, 164, 40), 0.36), (255, 236, 130)),
                               ("raw_copper", R((196, 104, 70), 0.36), (120, 200, 160)), ("clay_ball", R((160, 166, 180), 0.2), None),
                               ("dye_powder_blue", LAPIS, (130, 170, 255))):
        ex = [(x, y, specks) for (x, y) in ((6, 5), (10, 6), (5, 8), (9, 9))] if specks else None
        put(name, exact(X_LUMP, {"M": ramp}, extra=ex))
    put("leather", exact(X_HIDE, {"M": LEATHER}))
    put("rabbit_hide", exact(X_HIDE, {"M": R((196, 160, 120), 0.3)}))
    put("rotten_flesh", exact(X_STEAK, {"M": R((170, 90, 60), 0.4), "P": R((110, 130, 70), 0.3)}))
    for name, ramp, glow in (("redstone_dust", REDSTONE, 40), ("glowstone_dust", R((250, 210, 90)), 120), ("gunpowder", R((110, 110, 116), 0.4), 0),
                             ("sugar", R((244, 244, 246), 0.12), 0), ("blaze_powder", R((250, 160, 30)), 100)):
        put(name, exact(X_PILE, {"M": ramp}, emis={"M": glow}, extra=[(6, 6, ramp[4]), (10, 5, ramp[3]), (8, 4, ramp[4])]))
    for name, col in DYES.items():                           # dyes stay as they were
        g = disc(grid(), "D", 7.5, 8.5, 4.6)
        t = render(g, {"D": R(col, 0.36)}, extra=[(6, 6, R(col, 0.36)[4])])
        if name != "blue":
            put(f"dye_powder_{name}", t)
        put(f"dye_powder_{name}_new", t)
    put("dye_powder_glow", render(disc(grid(), "D", 7.5, 8.5, 4.6), {"D": R((60, 210, 190))}, emis={"D": 160}))
    # ------------------------------------------------------- balls & rods
    for name, col, glow in (("slimeball", (120, 200, 90), 0), ("snowball", (240, 246, 250), 0), ("ender_pearl", (30, 110, 100), 0),
                            ("magma_cream", (230, 150, 50), 60), ("fireball", (230, 90, 30), 150), ("heartofthesea_closed", (40, 130, 200), 60),
                            ("wind_charge", (190, 210, 240), 0)):
        put(name, exact(X_BALL, {"M": R(col, 0.36)}, extra=[(5, 5, white)], emis={"M": glow}))
    for name, col in (("egg", (236, 220, 190)), ("blue_egg", (130, 190, 220)), ("brown_egg", (176, 124, 90))):
        put(name, exact(X_EGG, {"M": R(col, 0.3)}, extra=[(5, 5, white)]))
    put("ender_eye", exact(X_BALL, {"M": R((60, 170, 110))},
                           extra=[(7, y, (16, 40, 34)) for y in (5, 6, 7, 8, 9)] + [(8, y, (30, 70, 56)) for y in (6, 7, 8)] + [(5, 5, (200, 255, 220))]))
    rod = [""] * 3 + ["." * (15 - y) + "43" for y in range(3, 14)]
    stick = [""] * 3 + ["." * (15 - y) + "xw" for y in range(3, 14)]
    put("stick", exact(stick, {"V": STICK}))
    put("blaze_rod", exact(rod, {"M": R((250, 190, 40))}, emis={"M": 120}))
    put("breeze_rod", exact(rod, {"M": R((170, 190, 236), 0.3)}, emis={"M": 40}))
    put("bone", exact(X_BONE, {"M": BONE}))
    put("arrow", exact(X_ARROW, {"M": STONE, "V": STICK, "A": R((236, 236, 240), 0.14)}))
    put("bow_standby", exact(X_BOW, {"V": WOOD, "A": R((230, 230, 224), 0.12)}))
    # ------------------------------------------------------------ misc
    for name, fill, glow in (("bucket_empty", R((70, 74, 84), 0.3), 0), ("bucket_water", WATER, 0), ("bucket_lava", LAVA, 180),
                             ("bucket_milk", MILK, 0), ("bucket_powder_snow", R((246, 250, 254), 0.08), 0)):
        put(name, exact(X_BUCKET, {"M": IRON, "P": fill}, metal={"M": 220}, emis={"P": glow}))
    for name, cover, ex, glow in (("book_normal", (150, 80, 44), None, 0), ("book_writable", (150, 80, 44), [(8, 6, (236, 236, 240)), (9, 5, (236, 236, 240)), (7, 7, (40, 40, 60))], 0),
                                  ("book_written", (120, 50, 130), [(6, 6, (250, 214, 90)), (7, 6, (250, 214, 90)), (6, 7, (250, 214, 90)), (7, 7, (250, 214, 90))], 0),
                                  ("book_enchanted", (120, 50, 160), [(6, 6, (150, 240, 255)), (8, 7, (150, 240, 255)), (7, 8, (150, 240, 255))], 60)):
        put(name, exact(X_BOOK, {"M": R(cover), "A": PAPER}, extra=ex, emis={"M": glow}))
    put("paper", exact(X_PAPER, {"M": PAPER}))
    put("map_empty", exact(X_PAPER, {"M": R((226, 208, 170), 0.16)}))
    put("bowl", exact(X_BOWL, {"M": WOOD, "P": R((96, 64, 36), 0.3)}))
    for name, col in (("mushroom_stew", (190, 150, 120)), ("beetroot_soup", (180, 40, 60)), ("rabbit_stew", (200, 140, 80)),
                      ("suspicious_stew", (150, 190, 110))):
        put(name, exact(X_BOWL, {"M": WOOD, "P": R(col, 0.24)}))
    put("string", exact(X_STRING, {"M": R((236, 236, 232), 0.14)}))
    put("feather", exact(X_FEATHER, {"M": R((240, 240, 244), 0.14), "A": R((150, 150, 160), 0.2)}))
    # ------------------------------------------------------------ food
    def fruit(col, glow=0):                                  # the apple stays as it was
        g = disc(grid(), "A", 7.5, 9.0, 4.8)
        stamp(g, ["T", "T"], 7, 2)
        stamp(g, ["LL", "LL."], 8, 2)
        return render(g, {"A": R(col, 0.36), "T": STICK, "L": GREEN}, extra=[(5, 7, (255, 255, 255))], emis={"A": glow})
    put("apple", fruit((214, 40, 40)))
    put("apple_golden", fruit((250, 206, 56), glow=40))
    put("bread", exact(X_BREAD, {"M": BREAD}))
    for name, col in (("potato", (200, 160, 90)), ("potato_baked", (214, 150, 70)), ("potato_poisonous", (170, 180, 90))):
        put(name, exact(X_POTATO, {"M": R(col, 0.3)}))
    put("carrot", exact(X_CARROT, {"M": R((240, 130, 30), 0.36), "A": GREEN}))
    put("carrot_golden", exact(X_CARROT, {"M": GOLD, "A": GREEN}, metal={"M": 120}))
    put("beetroot", exact(X_BEET, {"M": R((170, 30, 60)), "A": GREEN}))
    fat, fat_c = R((250, 226, 220), 0.12), R((226, 180, 120), 0.2)
    put("beef_raw", exact(X_STEAK, {"M": R((214, 70, 70), 0.34), "P": fat}))
    put("beef_cooked", exact(X_STEAK, {"M": R((150, 84, 50), 0.4), "P": fat_c}))
    put("hoglin_meat_raw", exact(X_STEAK, {"M": R((190, 60, 90), 0.34), "P": fat}))
    put("hoglin_meat_cooked", exact(X_STEAK, {"M": R((140, 76, 60), 0.4), "P": fat_c}))
    put("porkchop_raw", exact(X_CHOP, {"M": R((240, 150, 150), 0.3), "P": fat, "A": BONE}))
    put("porkchop_cooked", exact(X_CHOP, {"M": R((196, 140, 90), 0.34), "P": fat_c, "A": BONE}))
    put("mutton_raw", exact(X_SLICE, {"M": R((226, 96, 96), 0.34), "A": BONE}))
    put("mutton_cooked", exact(X_SLICE, {"M": R((160, 96, 60), 0.4), "A": BONE}))
    put("chicken_raw", exact(X_DRUM, {"M": R((244, 196, 176), 0.24), "A": BONE}))
    put("chicken_cooked", exact(X_DRUM, {"M": R((204, 136, 60), 0.36), "A": BONE}))
    put("rabbit_raw", exact(X_DRUM, {"M": R((236, 170, 160), 0.26), "A": BONE}))
    put("rabbit_cooked", exact(X_DRUM, {"M": R((184, 124, 76), 0.36), "A": BONE}))
    eye = R((30, 30, 36), 0.4)
    for name, col, belly in (("fish_raw", (96, 140, 170), (214, 226, 230)), ("fish_cooked", (176, 140, 104), (236, 226, 204)),
                             ("fish_salmon_raw", (220, 96, 80), (244, 200, 186)), ("fish_salmon_cooked", (214, 140, 100), (240, 214, 190))):
        put(name, exact(X_FISH, {"M": R(col, 0.36), "P": R(belly, 0.14), "A": eye}, extra=[(11, 5, (255, 255, 255))]))
    stripes = [(x, y, (250, 250, 250)) for x in (5, 9) for y in (6, 7, 8)]
    put("fish_clownfish_raw", exact(X_FISH, {"M": R((244, 130, 40), 0.36), "P": R((250, 190, 120), 0.2), "A": eye},
                                    extra=stripes + [(11, 5, (255, 255, 255))]))
    put("fish_pufferfish_raw", exact(X_PUFFER, {"M": R((240, 204, 60), 0.36), "P": R((250, 240, 200), 0.12), "A": eye}))
    put("cookie", exact(X_BALL, {"M": R((204, 144, 72), 0.3)}, extra=[(6, 6, (84, 52, 30)), (9, 7, (84, 52, 30)), (7, 9, (84, 52, 30)), (10, 9, (84, 52, 30)), (5, 8, (84, 52, 30))]))
    put("melon", exact(X_MELON, {"M": R((232, 64, 64), 0.3), "A": GREEN}, extra=[(5, 6, (44, 30, 30)), (8, 7, (44, 30, 30)), (10, 6, (44, 30, 30))]))
    put("pumpkin_pie", exact(X_PIE, {"M": R((232, 140, 40), 0.3), "A": BREAD}))
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
    put("chorus_fruit", exact(X_BALL, {"M": R((150, 110, 170), 0.34)}, extra=[(6, 7, (214, 190, 226)), (9, 6, (214, 190, 226)), (8, 9, (110, 70, 130))]))
    put("chorus_fruit_popped", exact(X_BALL, {"M": R((196, 156, 214), 0.3)}, extra=[(6, 7, (240, 226, 246)), (9, 6, (240, 226, 246)), (7, 9, (240, 226, 246))]))
    put("spider_eye", exact(X_BALL, {"M": R((170, 30, 50))}, extra=[(7, 6, (30, 8, 16)), (8, 6, (30, 8, 16)), (7, 7, (30, 8, 16)), (8, 7, (30, 8, 16)), (5, 5, (255, 190, 190))]))
    put("honeycomb", exact(X_INGOT, {"M": R((240, 170, 40), 0.34)}, extra=[(6, 6, (190, 110, 20)), (9, 6, (190, 110, 20)), (7, 7, (190, 110, 20))]))
    put("nether_star", exact(X_STAR, {"M": R((244, 244, 226), 0.2)}, emis={"M": 200}))
    put("ghast_tear", exact(X_TEAR, {"M": R((220, 240, 244), 0.2)}, extra=[(6, 6, white)]))
    put("totem", exact(X_TOTEM, {"M": GOLD, "A": EMERALD}, metal={"M": 200}))


# ------------------------------------------------------------------ pixel maps
X_INGOT = ["", "", "", "", "", ".....444444444", "....4333333331", "...43333333321", "...2222222221", "...111111110"]
X_NUGGET = ["", "", "", "", "", "", "......443", ".....44332", ".....433321", "......3221", ".......21"]
X_GEM = ["", "", "", "....44443333", "...4443333322", "..443333333221", "...3333332221", "....33322211", ".....332211", "......3211",
         ".......21"]
X_EMERALD = ["", "", ".....444443", "....44333332", "...4333333321", "...4343333221", "...4343333221", "...4343333221", "...4343333221",
             "...4332222221", "....33222211", ".....222211"]
X_SHARD = ["", "...........43", "..........4432", ".........44332", "........443321", ".......443321", "......443321", ".....443321",
           "....443321", "...443321", "...33221", "....221"]
X_FLINT = ["", "", "", "......443", ".....44332", "....4433321", "...44333321", "...43333321", "....3332221", ".....22211", "......211"]
X_LUMP = ["", "", "", "......44443", "....44333332", "...4433233332", "..44333333321", "..43323333321", "..33333332221", "...332222211",
          ".....222111"]
X_HIDE = ["", "", "..44......44", "..4333..33332", "...433333332", "...433333332", "..4333333332", "..4333333332", "...333333321",
          "...332..2221", "..332....221", "..22......11"]
X_PILE = ["", "", "", "", "", "", "", "", ".......43", ".....443332", "...4433333321", "..443333333221", "..222222222211"]
X_BALL = ["", "", "", "......4443", "....44433332", "...4443333332", "...4433333322", "...4333333322", "...3333333221", "...3333332221",
          "....33222211", "......2211"]
X_EGG = ["", "", "......443", ".....44332", "....4433332", "....4333332", "...443333322", "...433333322", "...433333221", "...333332221",
         "....3322221", ".....22211"]
X_BONE = ["", "", "............44", "..........4432", "..........432", ".........43", "........43", ".......43", "......43", ".....43",
          "....43", "...43", ".4432", ".322"]
X_ARROW = ["", "...........443", "..........x432", ".........x..2", "........x", ".......x", "......x", ".....x", "....x", "...x",
           "..x", ".ccx", "..dc", "...d"]
X_BOW = ["", "......xxwa", "....xxw..a", "...xw....a", "..xw.....a", "..xw.....a", "..yw.....a", "..yw.....a", "..yw.....a", "..xw.....a",
         "..xw.....a", "...xw....a", "....xxw..a", "......xxwa"]
X_BUCKET = ["", "", "", "....44444444", "...4RRRRRRRR2", "...4433333322", "....43333332", "....43333332", "....43333321",
            ".....3333321", ".....3322221", "......22211"]
X_BOOK = ["", "", "...444444444", "..2433333333d", "..2433333333d", "..2433333333d", "..2433333333d", "..2433333333d", "..2433333333d",
          "..2433333332d", "..2dddddddddc", "...2222222221"]
X_PAPER = ["", "", "....44444444", "...4433333332", "...4322222232", "...4333333332", "...4322222232", "...4333333332", "...4322223332",
           "...4333333332", "...4333333321", "....3333322"]
X_BOWL = ["", "", "", "", "", "", "..444444444443", "..4RRRRRRRRRR2", "...4333333332", "....33333321", ".....332221", "......2211"]
X_STRING = ["", "", "", "", ".....4444", "...44....33", "..4...44...3", "..4..4..3..2", "..3...33...2", "...33....22", ".....2222..1",
            "..........21", "............1"]
X_FEATHER = ["", "...........443", ".........44332", "........44332b", ".......4433b2", "......443b32", ".....443b322", "....443b322",
             "....43b322", "...43b22", "...3b2", "..b", ".b"]
X_BREAD = ["", "", "", "", "", "....44444444", "..443333333332", ".44331331331332", ".43333333333322", ".33333333333221", "..222222222211"]
X_POTATO = ["", "", "", "", ".....44443", "...4433333332", "..443323333332", "..433333332332", "..333233333321", "...3333333221",
            ".....222211"]
X_CARROT = ["", "..........c.d", "...........dc", "..........443", ".........4332", "........4332", ".......4332", "......4332",
            ".....4332", "....432", "...432", "..32", "..2"]
X_BEET = ["", "......c..d", ".......cdc", "........b", "......4443", ".....443332", "....44333332", "....43333332", "....33333321",
          ".....333221", ".......21", "........1"]
X_STEAK = ["", "", "", "", ".....RRRRRR", "...RR333333RR", "..R3333333333R", "..333323333332", "..333333323332", "..233333333321",
           "...2233333221", ".....222211"]
X_CHOP = ["", "", "", "......RRRRR", "....RR33333R", "...R33333333R", "..cR333333332", "..cb33333332", "..cb2333332", "..cbb22222",
          "...cbbb", "....ccb"]
X_SLICE = ["", "", "", ".....444433", "...4433333332", "..433333333332", "..4333bccb3332", "..3333caac3331", "..3333bccb3321",
           "..233333333321", "...2233333221", ".....222211"]
X_DRUM = ["", ".........4443", ".......44333332", "......4333333332", "......4333333332", "......3333333321", "......333333321",
          ".....c33333221", "....cb.2222", "...cb", "..cb", ".ccb", ".b.b"]
X_FISH = ["", "", "", "........443", "......443333", ".4..4433333332", ".4333333333a32", "..2RRRRRRRRRR1", ".322RRRRRRRR1",
          ".2..22222221", "......2211"]
X_PUFFER = ["", "", ".......4", "....4.4443.3", ".....443333", "..4.44333a32.2", "....43333332", "...3RRRRRRRR1", "....2RRRRRR1",
            "..2..222211..1", "....2..1...1"]
X_MELON = ["", "", "", "", "", "..444444444443", "..433333333332", "...3333333332", "....33333322", "....dccccccb", ".....bbbbba"]
X_PIE = ["", "", "", "", "", "", "..dddddddddddc", "..c3d3d3d3d3db", "..c3333333333b", "...cbbbbbbbba", "....aaaaaaaa"]
X_STAR = ["", ".......43", ".......43", "......4432", "......4332", "....44433322", ".44443333332221", ".33333333322211", "....33322211",
          "......3221", "......3221", ".......21", ".......21"]
X_TEAR = ["", "", ".......4", "......443", "......433", ".....44332", "....4433332", "....4333332", "....3333322", "....3333221",
          ".....32221", "......211"]
# a small winged idol: square head with gem eyes, outstretched wings, belted body, two feet
X_TOTEM = ["", "......4443", ".....443332", ".....4c33c2", ".....433332", "......3112", "..44.433332.43", "..433333333321",
           "...2243333221", ".....433332", ".....43bb32", ".....433332", "......3222", "......21.21"]
