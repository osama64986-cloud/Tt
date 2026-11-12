"""Item sprites, drawn from scratch in the pack's cartoon style.

Every item is a small character map: each letter is a material region.  The
renderer shades each region from its own silhouette (lit top-left, shaded
bottom-right) and wraps the whole sprite in a soft dark outline.  The game
uses this same picture for the inventory icon and for the item held in the
hand, so both always match.
"""
import colorsys
import json
import os

import numpy as np

from .blocks_rest import shade_mask
from .core import N, Tex, make_ramp, mix, rng_of, shift

HERE = os.path.dirname(os.path.abspath(__file__))
ISTATS = json.load(open(os.path.join(HERE, "vanilla_item_stats.json")))


def R(c, contrast=0.42, **kw):
    """Item ramp, six tones (0 = deepest shadow ... 5 = specular glint).
    Shadows slide towards violet and gain saturation, lights slide towards
    warm yellow and wash out: the classic hand-pixelled look."""
    h, sat, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    k = contrast / 0.42
    grey = sat < 0.08
    # (classic look: keep the material's own saturation)
    out = []
    for vm, sm, cool, warm in ((1 - 0.55 * k, 1.08, 0.025, 0), (1 - 0.37 * k, 1.05, 0.015, 0), (1 - 0.18 * k, 1.02, 0.006, 0),
                               (1.0, 1.0, 0, 0), (None, 0.80, 0, 0.012), (None, 0.45, 0, 0.020)):
        if vm is None:
            vv = v + (1 - v) * (0.38 if sm > 0.6 else 0.66)
        else:
            vv = max(0.04, v * max(0.12, vm))
        hh, ss = h, sat * sm
        if grey:
            if cool:
                hh, ss = 0.66, sat + (0.12 if cool > 0.05 else 0.08 if cool > 0.03 else 0.04)
            elif warm:
                hh, ss = 0.12, sat + 0.02
        elif cool:
            d = ((0.72 - h + 0.5) % 1.0) - 0.5
            hh = (h + max(-cool, min(cool, d))) % 1.0
        elif warm:
            d = ((0.14 - h + 0.5) % 1.0) - 0.5
            hh = (h + max(-warm, min(warm, d))) % 1.0
        r_, g_, b_ = colorsys.hsv_to_rgb(hh, min(1.0, ss), min(1.0, vv))
        out.append((int(round(r_ * 255)), int(round(g_ * 255)), int(round(b_ * 255))))
    return out


def _outline(rgb, alpha, hgt, base):
    """Soft cartoon outline.  `base` holds each pixel's darkest material tone.
    The outline is lighter where it faces the light (top / left) and deep on
    the shadow side, so sprites look rounded instead of stamped."""
    solid = alpha > 0
    deep = (base * 0.55).astype(np.uint8)
    soft = (base * 0.72).astype(np.uint8)
    for dy, dx, col in ((-1, 0, soft), (0, -1, soft), (1, 0, deep), (0, 1, deep)):
        nb = np.roll(np.roll(solid, dy, 0), dx, 1)
        nd = np.roll(np.roll(col, dy, 0), dx, 1)
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
    return rgb, alpha, hgt


WOOD, STICK = R((156, 112, 62)), R((128, 92, 52))
STONE, IRON = R((124, 120, 116), 0.4), R((236, 236, 238), 0.34)
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
        rgb = np.where(m[..., None], np.array(ramp, np.uint8)[np.array([1, 2, 3, 4, 5])[idx]], rgb)   # 3 = base tone
        dark = np.where(m[..., None], np.array(ramp[0], np.uint8), dark)
        alpha = np.where(m, 255, alpha)
        hgt = np.where(m, 0.45 + idx * 0.12, hgt)
        if emis and ch in emis:
            em = np.where(m, emis[ch], em)
        if metal and ch in metal:
            mt = np.where(m, metal[ch], mt)
    # outline: empty pixels touching the sprite take a darkened neighbour colour
    rgb, alpha, hgt = _outline(rgb, alpha, hgt, dark)
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
            elif ch in "abcdef":
                grp, tone = "A", ord(ch) - 97
            elif ch in "vwxyz":
                grp, tone = "V", ord(ch) - 117                # v = 1 ... z = 5: handles stay warm, never black
            elif ch in "PQRSTU":                             # a second body colour (belly, filling, pages...)
                grp, tone = "P", ord(ch) - 80
            else:
                raise ValueError(f"bad sprite character {ch!r}")
            ramp = groups[grp]
            if checker and grp == "M" and (x + y) % 2 == 0 and 0 < tone:
                tone -= 1                                    # chain links
            rgb[y, x] = ramp[tone]
            dark[y, x] = ramp[0]
            alpha[y, x] = 255
            hgt[y, x] = 0.4 + tone * 0.11
            if metal and grp in metal:
                mt[y, x] = metal[grp]
            if emis and grp in emis:
                em[y, x] = emis[grp]
    rgb, alpha, hgt = _outline(rgb, alpha, hgt, dark)
    if extra:
        for (x, y, c) in extra:
            rgb[y, x] = c
            alpha[y, x] = 255
    t = Tex(rgb, hgt, alpha=alpha, rough=np.where(mt > 0, 80, 190), metal=mt, bump=0.8)
    t.emis = em
    return t


# Weapons, tools and armour are placed pixel by pixel: a lit edge, a body
# tone and a shaded edge on every blade and plate, seams and belts on armour.
X_SWORD = ["", "..............5.", "............531.", "...........431..", "..........431...", ".........531....", "........431.....", "..e....431......", "..dc..531.......", "...dc431........", "....Scb.........", "...ywdcb........", "..xv..dcb.......", ".dc....b........", ".cb............."]
X_PICK = ["", ".....5444443....", "...5433333332...", "..53.....32221..", "..2.......ba21..", ".........xw.21..", "........yw..21..", ".......xw...11..", "......xw....10..", ".....yw.....0...", "....xw..........", "...xw...........", "..yw............", ".xv.............", ".v.............."]
X_AXE = ["", ".............xw.", ".........553xw..", ".......5443ba...", ".....54333xw2...", "....54332xw21...", "....5432xw1.....", "....432yw.......", "....31xw........", ".....xw.........", "....yw..........", "...xw...........", "..xw............", ".xv............."]
X_SHOVEL = ["", "...........543..", "..........54332.", ".........543321.", ".........43321..", "........b3321...", ".......xa21.....", "......yw........", ".....xw.........", "....xw..........", "...yw...........", "..xw............", ".xv.............", ".v.............."]
X_HOE = ["", "......5444443...", "......43333321..", "......31...ba...", "......1...xw....", ".........yw.....", "........xw......", ".......xw.......", "......yw........", ".....xw.........", "....xw..........", "...yw...........", "..xw............", ".xv.............", ".v.............."]
X_HELMET = ["", ".......54.......", ".....554444.....", "...5544333332...", "..544333333221..", "..543333333321..", "..cdedddddedcb..", "..532.4321.321..", "..432..31..321..", "..432..21..321..", "..322......221..", "..21........10.."]
X_CHEST = ["", "..554......544..", ".54332....54332.", ".543332cc433321.", ".43333cddc33321.", ".43214433331321.", ".32114333321211.", "....54333321....", "....42222221....", "....54333321....", "....43333321....", "....42222221....", "....bccddccb....", ".....322221....."]
X_LEGS = ["", "...bccccccccb...", "...5433dd3321...", "...5433333321...", "...4333223321...", "...5432..4321...", "...4332..4321...", "...4332..4321...", "...4222..4221...", "...5432..4321...", "...4332..4321...", "...4332..4321...", "...3321..3321...", "...2211..2210..."]
X_BOOTS = ["", "", "", "", "...bcc....bcc...", "...542....542...", "...432....432...", "...432....432...", "...432....432...", "..5432....5432..", ".54322....54322.", ".00000....00000."]


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
        trim = R((120, 84, 50)) if m in ("wood", "stone") else R((200, 150, 60) if m in ("iron", "diamond", "netherite") else shift(ramp[1], dv=-0.08), 0.4)
        gem = {"wood": (120, 84, 50), "stone": (120, 120, 130), "iron": (220, 50, 60), "gold": (226, 40, 70), "diamond": (250, 250, 255),
               "netherite": (220, 60, 50), "copper": (60, 200, 150)}[m]
        grp = {"M": ramp, "V": STICK, "A": trim, "P": R(gem)}
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
                          ("netherite_ingot", NETHERITE, 220)):
        put(name, exact(INGOTS[name], {"M": ramp}, metal={"M": m}))
    for name, ramp, m in (("brick", R((180, 90, 70), 0.3), 0),
                          ("netherbrick", R((90, 40, 46), 0.4), 0), ("resin_brick", R((226, 110, 40), 0.3), 0)):
        put(name, exact(X_INGOT, {"M": ramp}, metal={"M": m}))
    for name, ramp, m in (("iron_nugget", IRON, 220), ("gold_nugget", GOLD, 240), ("copper_nugget", COPPER, 210)):
        put(name, exact(NUGGETS[name], {"M": ramp}, metal={"M": m}))
    white = (255, 255, 255)
    put("diamond", exact(X_GEM, {"M": DIAMOND}, extra=[(5, 4, white)]))
    put("ruby", exact(X_GEM, {"M": R((226, 40, 70))}, extra=[(5, 4, white)]))
    put("emerald", exact(X_EMERALD, {"M": EMERALD}, extra=[(5, 4, (236, 255, 240))]))
    put("quartz", exact(X_CLUSTER, {"M": QUARTZ}))
    for name, ramp, glow in (("amethyst_shard", AMETHYST, 0), ("echo_shard", ECHO, 40), ("prismarine_shard", PRISM, 0)):
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
    put("rotten_flesh", exact(X_ROTTEN, {"M": R((176, 92, 60), 0.4), "P": R((110, 140, 70), 0.34)}))
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
    # meats: one cut per animal, so you know where it came from at a glance
    bone, fat, crisp = R((240, 232, 214), 0.2), R((250, 236, 226), 0.14), R((214, 170, 120), 0.24)
    put("beef_raw", exact(X_STEAK, {"M": R((200, 50, 56), 0.36), "P": fat}))                 # cow: marbled steak
    put("beef_cooked", exact(X_STEAK, {"M": R((140, 76, 44), 0.42), "P": crisp}))
    put("porkchop_raw", exact(X_CHOP, {"M": R((244, 150, 150), 0.3), "P": fat}))             # pig: chop with bone and fat band
    put("porkchop_cooked", exact(X_CHOP, {"M": R((204, 144, 88), 0.36), "P": crisp}))
    put("mutton_raw", exact(X_RACK, {"M": R((226, 90, 92), 0.36), "P": bone}))               # sheep: rack of ribs
    put("mutton_cooked", exact(X_RACK, {"M": R((158, 92, 56), 0.42), "P": bone}))
    put("chicken_raw", exact(X_DRUM, {"M": R((246, 200, 180), 0.24), "P": bone}))            # chicken: round drumstick
    put("chicken_cooked", exact(X_DRUM, {"M": R((214, 140, 56), 0.38), "P": bone}))
    put("rabbit_raw", exact(X_HIND, {"M": R((236, 166, 156), 0.28), "P": bone}))             # rabbit: slim hind leg
    put("rabbit_cooked", exact(X_HIND, {"M": R((186, 122, 72), 0.38), "P": bone}))
    put("hoglin_meat_raw", exact(X_SLAB, {"M": R((180, 56, 90), 0.36), "P": bone}))          # hoglin: big slab, bone ring
    put("hoglin_meat_cooked", exact(X_SLAB, {"M": R((140, 72, 58), 0.42), "P": bone}))
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
        for (x, y) in ((6, 6), (9, 8), (5, 10), (10, 11), (7, 12)):
            stamp(g, ["S", "S"] if name != "seeds_pumpkin" else ["SS"], x, y)
        put(name, render(g, {"S": R(col, 0.36)}))
    g = disc(grid(), "A", 6, 9, 2.6)
    g = disc(g, "A", 10, 9, 2.6)
    stamp(g, ["T", "T", "T"], 8, 3)
    put("sweet_berries", render(g, {"A": R((200, 30, 50)), "T": GREEN}))
    put("glow_berries", render(g, {"A": R((250, 180, 50)), "T": GREEN}, emis={"A": 160}))
    put("chorus_fruit", exact(X_BALL, {"M": R((150, 110, 170), 0.34)}, extra=[(6, 7, (214, 190, 226)), (9, 6, (214, 190, 226)), (8, 9, (110, 70, 130))]))
    put("chorus_fruit_popped", exact(X_BALL, {"M": R((196, 156, 214), 0.3)}, extra=[(6, 7, (240, 226, 246)), (9, 6, (240, 226, 246)), (7, 9, (240, 226, 246))]))
    put("spider_eye", exact(X_EGG, {"M": R((150, 24, 50))}, extra=[(7, 7, (24, 6, 12)), (8, 7, (24, 6, 12)), (7, 8, (24, 6, 12)), (6, 5, (255, 190, 200)),
                                                                     (9, 11, (100, 14, 30)), (9, 12, (100, 14, 30))]))
    put("honeycomb", exact(X_INGOT, {"M": R((240, 170, 40), 0.34)}, extra=[(6, 6, (190, 110, 20)), (9, 6, (190, 110, 20)), (7, 7, (190, 110, 20))]))
    put("nether_star", exact(X_STAR, {"M": R((244, 244, 226), 0.2)}, emis={"M": 200}))
    put("ghast_tear", exact(X_TEAR, {"M": R((220, 240, 244), 0.2)}, extra=[(6, 6, white)]))
    put("totem", exact(X_TOTEM, {"M": GOLD, "A": EMERALD, "P": R((150, 90, 30))}, metal={"M": 200}))
    build_more(out)


def tint(name, ds=0.22, dv=0.06):
    """A lively version of the colour the game uses for this item."""
    st = ISTATS[name]
    return shift(tuple(st.get("dom", st["mean"])), ds=ds * 0.5, dv=dv * 0.5)


def hue_of(name):
    """Stable colour picked from a name (labels on music discs)."""
    h = (sum(ord(c) * (i + 3) for i, c in enumerate(name)) % 360) / 360.0
    r_, g_, b_ = colorsys.hsv_to_rgb(h, 0.7, 0.95)
    return (int(r_ * 255), int(g_ * 255), int(b_ * 255))


EFFECT = {   # one clear colour per effect, the colour players associate with it
    "heal": (226, 40, 46), "harm": (110, 30, 120), "poison": (60, 170, 40), "regeneration": (230, 110, 200),
    "moveSpeed": (110, 200, 240), "moveSlowdown": (90, 100, 140), "damageBoost": (190, 50, 40), "weakness": (110, 110, 120),
    "fireResistance": (240, 140, 40), "waterBreathing": (40, 90, 220), "nightVision": (40, 60, 200), "invisibility": (190, 200, 220),
    "jump": (140, 240, 90), "slowFall": (246, 226, 200), "turtleMaster": (120, 110, 70), "luck": (60, 160, 60),
    "absorption": (40, 90, 200), "blindness": (40, 40, 50), "confusion": (130, 50, 110), "digSlowdown": (80, 80, 50),
    "digSpeed": (220, 200, 60), "healthBoost": (240, 120, 40), "hunger": (100, 120, 60), "levitation": (220, 220, 250),
    "resistance": (130, 120, 160), "saturation": (220, 40, 40), "wither": (60, 50, 50), "infested": (140, 150, 140),
    "oozing": (120, 220, 140), "weaving": (120, 100, 80), "windCharged": (190, 210, 250),
}


def effect_colour(name):
    for k, c in EFFECT.items():
        if name.endswith(k) or name.endswith(k + "_"):
            return c
    return (90, 110, 220)                                   # water / awkward / mundane


def build_more(out):
    """Families that share one drawing and differ by colour."""
    def put(name, tex):
        if name in ISTATS and ISTATS[name]["size"] == [16, 16]:
            out[name] = tex
    glass = R((196, 214, 226), 0.3)
    cork = R((170, 124, 76))
    # ---- potions: three bottle shapes, liquid coloured per effect
    for name in ISTATS:
        if not name.startswith("potion_bottle_"):
            continue
        empty = name.endswith("empty")
        liquid = R((214, 232, 240), 0.2) if empty else R(effect_colour(name), 0.4)
        rows = X_SPLASH if "splash" in name else X_LINGER if "lingering" in name else X_BOTTLE
        put(name, exact(rows, {"M": liquid, "A": glass, "V": cork}, emis={"M": 0 if empty else 30}))
    for name, col, glow in (("honey_bottle", (240, 160, 30), 0), ("experience_bottle", (170, 240, 60), 140),
                            ("dragons_breath", (230, 110, 210), 100), ("ominous_bottle", (50, 70, 130), 0)):
        put(name, exact(X_BOTTLE, {"M": R(col), "A": glass, "V": cork}, emis={"M": glow}))
    # ---- spawn eggs: one egg, two colours per creature
    for name in ISTATS:
        if name.startswith("egg_") and name not in ("egg_template", "egg_null", "egg_mask"):
            base = tint(name, ds=0.18, dv=0.1)
            spot, pale = shift(base, dv=-0.28, ds=0.1), shift(base, dv=0.2, ds=-0.2)
            ex = [(x, y, spot) for (x, y) in ((6, 5), (7, 5), (9, 7), (5, 8), (6, 8), (8, 10), (9, 10))] + [(5, 4, pale)]
            put(name, exact(X_EGG, {"M": R(base, 0.34)}, extra=ex))
    # ---- wood families: boats, signs, doors
    for name in ISTATS:
        if "boat" in name or name.endswith("_raft"):
            wood = R(tint(name, ds=0.12, dv=0.08))
            rows = X_BOAT_CHEST if "chest" in name else X_BOAT
            put(name, exact(rows, {"M": wood, "P": R((170, 120, 60)), "A": IRON}))
        elif name.endswith("hanging_sign"):
            put(name, exact(X_HANG, {"M": R(tint(name, ds=0.12, dv=0.08)), "A": R((96, 100, 112), 0.4)}))
        elif name == "sign" or name.startswith("sign_") or name.endswith("_sign"):
            put(name, exact(X_SIGN, {"M": R(tint(name, ds=0.12, dv=0.1)), "V": STICK}))
        elif (name.startswith("door_") or name.endswith("_door")) and "trap" not in name:
            metal = "iron" in name or "copper" in name
            put(name, exact(X_DOOR, {"M": R(tint(name, ds=0.12, dv=0.08)), "P": R((150, 200, 230), 0.3), "A": GOLD},
                            metal={"M": 200} if metal else None))
    # ---- minecarts
    for name, load in (("minecart_normal", None), ("minecart_chest", (170, 120, 60)), ("minecart_furnace", (130, 130, 136)),
                       ("minecart_hopper", (80, 80, 90)), ("minecart_tnt", (214, 50, 40)), ("minecart_command_block", (214, 140, 90))):
        rows = X_CART if load is None else X_CART_LOAD
        put(name, exact(rows, {"M": IRON, "A": R((60, 60, 70), 0.5), "P": R(load or (0, 0, 0))}, metal={"M": 220}))
    # ---- music discs
    vinyl = R((58, 56, 66), 0.6)
    for name in ISTATS:
        if name.startswith("record_") or name.startswith("music_disc_"):
            put(name, exact(X_DISC, {"M": vinyl, "P": R(tint(name, ds=0.3, dv=0.2))}))
    # ---- bow being drawn: the string pulls back and the arrow slides with it
    for k in range(3):
        rows = [list(r.ljust(N, ".")) for r in X_BOW] + [list("." * N)] * 2
        for y in range(1, 14):
            if rows[y][9] == "a":
                rows[y][9] = "."
        for y in range(1, 14):
            x = 9 + int(round((k + 1) * 1.3 * (1 - abs(y - 7) / 6.0)))
            rows[y][min(14, x)] = "a"
        nock = min(14, 9 + int(round((k + 1) * 1.3)))
        for x in range(1, nock):
            rows[7][x] = "x" if rows[7][x] in ".xwy" else rows[7][x]
        rows[7][1], rows[6][2], rows[8][2] = "4", "3", "3"
        put(f"bow_pulling_{k}", exact(["".join(r) for r in rows], {"V": WOOD, "A": R((230, 230, 224), 0.12), "M": STONE}))
    put("shears", exact(X_SHEARS, {"M": IRON, "A": R((90, 90, 100), 0.4), "P": R((200, 50, 50))}, metal={"M": 220}))
    rod = [list(("." * (15 - y) + "xw").ljust(N, ".")) if 3 <= y <= 13 else list("." * N) for y in range(N)]
    for y in range(4, 10):
        rod[y][13] = "c"
    rod[10][12], rod[10][13], rod[9][11] = "b", "c", "b"
    put("fishing_rod_uncast", exact(["".join(r) for r in rod], {"V": STICK, "A": R((226, 226, 230), 0.14)}))
    build_extra(out)


def mirror(left):
    """Build a symmetric sprite from its left half (8 columns)."""
    return [(r.ljust(8, ".")[:8]) + (r.ljust(8, ".")[:8])[::-1] for r in left]


def build_extra(out):
    def put(name, tex):
        if name in ISTATS and ISTATS[name]["size"] == [16, 16]:
            out[name] = tex
    face = R((240, 236, 222), 0.14)
    put("compass_item", exact(X_COMPASS, {"M": R((150, 150, 160), 0.4), "P": face, "A": R((220, 40, 40))}, metal={"M": 200}))
    put("clock_item", exact(X_CLOCK, {"M": GOLD, "P": face, "A": R((50, 50, 60), 0.5)}, metal={"M": 220}))
    put("lodestonecompass_item", exact(X_COMPASS, {"M": R((110, 96, 150), 0.4), "P": face, "A": R((60, 200, 220))}, metal={"M": 200}))
    put("recovery_compass_item", exact(X_COMPASS, {"M": R((20, 90, 110), 0.5), "P": R((40, 60, 70), 0.3), "A": R((90, 230, 240))}, emis={"A": 150}))
    for name in ISTATS:                                                   # tipped arrows: the head takes the effect colour
        if name == "tipped_arrow" or (name.startswith("tipped_arrow_") and name not in ("tipped_arrow_base", "tipped_arrow_head")):
            put(name, exact(X_ARROW, {"M": R(tint(name, ds=0.35, dv=0.12)), "V": STICK, "A": R((236, 236, 240), 0.14)}))
    for dye, col in DYES.items():
        put(f"bed_{dye}", exact(X_BED, {"M": R(col, 0.36), "P": R((240, 240, 236), 0.12), "V": WOOD}))
        put(f"{dye}_cushion", exact(X_CUSHION, {"M": R(col, 0.36)}))
    put("light_gray_cushion", exact(X_CUSHION, {"M": R(DYES["silver"], 0.36)}))
    for m, ramp in (("iron", IRON), ("gold", GOLD), ("diamond", DIAMOND), ("leather", LEATHER), ("copper", COPPER), ("netherite", NETHERITE)):
        put(f"{m}_horse_armor", exact(X_BARD, {"M": ramp}, metal={"M": 200 if m != "leather" else 0}))
    put("saddle", exact(X_SADDLE, {"M": R((150, 84, 44)), "A": IRON}))
    put("lead", exact(X_STRING, {"M": R((176, 140, 90), 0.34)}))
    put("name_tag", exact(X_TAG, {"M": PAPER, "A": R((226, 226, 230), 0.14)}))
    put("flint_and_steel", exact(X_FLINTSTEEL, {"M": IRON, "P": R((70, 70, 80), 0.5)}, metal={"M": 220}))
    put("mace", exact(X_MACE, {"M": R((120, 124, 136), 0.44), "V": STICK}, metal={"M": 220}))
    put("elytra", exact(mirror(X_WING), {"M": R((150, 140, 176), 0.36)}))
    put("broken_elytra", exact(mirror(X_WING), {"M": R((120, 112, 130), 0.36)}, extra=[(4, 8, (30, 26, 40)), (5, 9, (30, 26, 40)), (11, 7, (30, 26, 40))]))
    put("phantom_membrane", exact(mirror(X_WING), {"M": R((200, 190, 160), 0.3)}))
    put("shulker_shell", exact(X_SHELL, {"M": R((150, 104, 150), 0.34)}))
    put("armadillo_scute", exact(X_EMERALD, {"M": R((190, 110, 90), 0.34)}))
    put("turtle_shell_piece", exact(X_EMERALD, {"M": R((70, 170, 80), 0.36)}))
    put("nautilus", exact(X_BALL, {"M": R((226, 200, 170), 0.3)}, extra=[(7, 7, (150, 90, 60)), (8, 7, (150, 90, 60)), (9, 8, (150, 90, 60)),
                                                                       (8, 9, (150, 90, 60)), (6, 8, (150, 90, 60)), (7, 6, (190, 120, 80))]))
    put("sea_pickle", exact(["", "", "", "", "", "........e.......", ".......5c.......", "......5443......", "......4332......", "......4332......",
                             "......4332......", "......4332......", "......3221......", ".......21......."], {"M": R((110, 140, 60), 0.4), "A": R((230, 250, 160))},
                            emis={"A": 200}))
    put("cake", exact(X_CAKE, {"M": R((176, 112, 64), 0.34), "P": R((252, 244, 240), 0.1), "A": R((214, 44, 50))}))
    for name, glow in (("lantern", (255, 190, 70)), ("soul_lantern", (90, 220, 236)), ("copper_lantern", (120, 236, 160)),
                       ("exposed_copper_lantern", (120, 236, 160)), ("weathered_copper_lantern", (120, 236, 160)),
                       ("oxidized_copper_lantern", (120, 236, 160))):
        frame_c = (70, 72, 84) if "copper" not in name else tint(name, ds=0.1)
        put(name, exact(X_LANTERN, {"M": R(frame_c, 0.44), "P": R(glow, 0.3), "A": R((96, 100, 112), 0.4)}, emis={"P": 220}, metal={"M": 180}))
    put("painting", exact(X_PAINTING, {"V": WOOD, "P": R((150, 200, 240), 0.2), "A": GREEN}))
    put("item_frame", exact(X_FRAME, {"V": WOOD, "P": R((170, 120, 70), 0.24)}))
    put("glow_item_frame", exact(X_FRAME, {"V": R((190, 170, 90)), "P": R((200, 170, 90), 0.24)}, emis={"V": 80}))
    stone = R((130, 134, 146), 0.36)
    marks = {0: [(6, 5), (7, 6), (8, 7), (9, 8), (9, 5), (6, 8)], 1: [(6, 5), (7, 5), (8, 5), (9, 5), (6, 8), (7, 8), (8, 8), (9, 8), (6, 6), (9, 7)],
             2: [(7, 5), (6, 6), (8, 6), (7, 7), (9, 7), (8, 8)], 3: [(6, 5), (9, 5), (7, 6), (8, 7), (6, 8), (9, 8), (7, 7)]}
    for name in ISTATS:
        k = sum(map(ord, name)) % 4
        if name.endswith("smithing_template"):                            # carved tablet, emblem coloured per pattern
            put(name, exact(X_TABLET, {"M": stone, "P": R(tint(name), 0.3)}))
        elif name.endswith("pottery_sherd"):                              # clay fragment, one of four scratched motifs
            put(name, exact(X_SHERD, {"M": R((180, 100, 70), 0.34)}, extra=[(x, y, (96, 46, 30)) for (x, y) in marks[k]]))
        elif name.endswith("banner_pattern") or name == "banner_pattern":
            col = hue_of(name)
            put(name, exact(X_PAPER, {"M": PAPER}, extra=[(x, y, col) for x in (6, 7, 8, 9) for y in (5, 6, 7, 8)] + [(7, 6, (255, 255, 255))]))
        elif name.startswith("map_") and name not in ("map_empty",):
            col = hue_of(name) if name not in ("map_filled", "map_locked") else (70, 150, 80)
            ex = [(x, y, (110, 170, 90)) for (x, y) in ((5, 5), (6, 5), (6, 6), (9, 8), (10, 8), (9, 9), (7, 9))] + \
                 [(x, y, (90, 150, 220)) for (x, y) in ((9, 5), (10, 5), (10, 6), (5, 9))] + [(8, 7, col), (8, 6, col)]
            put(name, exact(X_PAPER, {"M": R((226, 208, 170), 0.16)}, extra=ex))
    put("nether_wart", render(disc(disc(disc(grid(), "A", 5, 10, 2.2), "A", 10, 10, 2.2), "A", 7.5, 6, 2.4), {"A": R((180, 26, 36))}))
    g = grid()
    for x in (4, 8, 11):
        for y in range(2, 14):
            g[y][x], g[y][x + 1] = "C", "C"
    build_last(out)
    build_animated(out)
    build_layers(out)
    build_plants(out)
    put("reeds", render(g, {"C": R((150, 200, 90), 0.36)}, extra=[(4, 5, (90, 140, 50)), (5, 5, (90, 140, 50)), (8, 8, (90, 140, 50)),
                                                                 (9, 8, (90, 140, 50)), (11, 4, (90, 140, 50)), (12, 4, (90, 140, 50)), (4, 10, (90, 140, 50)), (5, 10, (90, 140, 50))]))


def canvas():
    return [["."] * N for _ in range(N)]


def line(g, x0, y0, x1, y1, ch):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x, y = int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n))
        if 0 <= x < N and 0 <= y < N:
            g[y][x] = ch
    return g


def rows_of(g):
    return ["".join(r) for r in g]


def from_block(name, tint_col=None):
    """Item icons that are simply the block's own sprite reuse our block art."""
    base = os.path.join(os.path.dirname(os.path.dirname(HERE)), "pack", "textures", "blocks", name)
    for ext in (".tga", ".png"):
        if os.path.exists(base + ext):
            from PIL import Image
            a = np.array(Image.open(base + ext).convert("RGBA"))[:N, :N]
            rgb = a[..., :3].astype(float)
            if tint_col is not None:
                rgb = rgb * np.array(tint_col) / 255.0
            return Tex(rgb.astype(np.uint8), None, alpha=a[..., 3], rough=200)
    return None


def build_last(out):
    def put(name, tex):
        if tex is not None and name in ISTATS and ISTATS[name]["size"] == [16, 16]:
            out[name] = tex
    glass, cork = R((196, 214, 226), 0.3), R((170, 124, 76))
    # ---- the newer per-creature spawn eggs
    for name in ISTATS:
        if name.startswith("spawn_eggs/") or name in ("spawn_egg", "spawn_egg_sulfur_cube"):
            base = tint(name, ds=0.18, dv=0.1)
            spot, pale = shift(base, dv=-0.28, ds=0.1), shift(base, dv=0.2, ds=-0.2)
            k = sum(map(ord, name)) % 3                      # three spot patterns so they are not all alike
            spots = (((6, 5), (7, 5), (9, 7), (5, 8), (6, 8), (8, 10), (9, 10)), ((5, 6), (8, 5), (9, 5), (7, 8), (10, 8), (6, 10)),
                     ((6, 4), (9, 6), (10, 6), (5, 9), (8, 9), (7, 11)))[k]
            put(name, exact(X_EGG, {"M": R(base, 0.34)}, extra=[(x, y, spot) for (x, y) in spots] + [(5, 4, pale)]))
    # ---- candles, bundles, harnesses: one drawing, sixteen colours
    wax = dict(DYES)
    wax["light_gray"] = DYES["silver"]
    for dye, col in wax.items():
        put(f"candles/{dye}_candle", exact(X_CANDLE, {"M": R(col, 0.34), "A": R((40, 36, 40), 0.4)}))
        put(f"bundle_{dye}", exact(X_BUNDLE, {"M": R(col, 0.36), "A": R((226, 214, 190), 0.2)}))
        hn = f"harness/harness_{dye}"
        put(hn, exact(X_SADDLE, {"M": R(col, 0.36), "A": IRON}))
    put("candles/candle", exact(X_CANDLE, {"M": R((236, 204, 150), 0.3), "A": R((40, 36, 40), 0.4)}))
    put("bundle", exact(X_BUNDLE, {"M": R((150, 84, 44)), "A": R((226, 214, 190), 0.2)}))
    # ---- spears and the trident
    for m, ramp in (("wood", WOOD), ("stone", STONE), ("iron", IRON), ("gold", GOLD), ("diamond", DIAMOND), ("netherite", NETHERITE),
                    ("copper", COPPER)):
        put(f"spear/{m}_spear", exact(X_SPEAR, {"M": ramp, "V": STICK, "A": R((96, 60, 36))}, metal={"M": 200}))
    g = canvas()
    for i in range(7):
        g[13 - i][2 + i], g[13 - i][3 + i] = "4", "2"
    line(g, 9, 6, 13, 2, "4")                      # middle prong
    line(g, 7, 6, 10, 3, "4")                      # upper prong
    line(g, 10, 9, 13, 6, "3")                     # lower prong
    line(g, 7, 6, 10, 9, "3")                      # the bar that joins them
    g[1][14], g[2][11], g[5][14] = "5", "5", "5"   # the three points
    put("trident", exact(rows_of(g), {"M": R((70, 190, 170), 0.4)}, metal={"M": 160}))
    # ---- crossbow: stock, limbs and a string that pulls back
    def crossbow(pull, load=None):
        g = canvas()
        for i in range(10):
            g[13 - i][2 + i], g[13 - i][3 + i] = "x", "w"
        for k in range(-4, 5):
            g[6 + k][9 + k] = "y" if abs(k) < 4 else "x"
        nx, ny = 8 - pull, 7 + pull
        line(g, 5, 2, nx, ny, "c")
        line(g, 13, 10, nx, ny, "c")
        if load:
            line(g, nx + 1, ny - 1, 12, 3, "x")
            g[2][13], g[3][13], g[2][12] = load, load, load
        return rows_of(g)
    limb = {"V": WOOD, "A": R((226, 226, 230), 0.14), "M": STONE, "P": R((220, 50, 50))}
    put("crossbow_standby", exact(crossbow(0), limb))
    for k in range(3):
        put(f"crossbow_pulling_{k}", exact(crossbow(k + 1), limb))
    put("crossbow_arrow", exact(crossbow(3, "4"), limb))
    put("crossbow_firework", exact(crossbow(3, "S"), limb))
    # ---- buckets with a passenger
    for name, col in (("bucket_cod", (150, 130, 110)), ("bucket_salmon", (214, 90, 80)), ("bucket_pufferfish", (240, 204, 60)),
                      ("bucket_tropical", (244, 130, 40)), ("bucket_axolotl", (250, 160, 190)), ("bucket_tadpole", (96, 70, 50)),
                      ("bucket_sulfur_cube", (214, 220, 80))):
        dk = shift(col, dv=-0.25)
        ex = [(6, 4, col), (7, 4, col), (8, 4, col), (9, 4, dk), (7, 3, col), (8, 3, shift(col, dv=0.15)), (10, 3, dk), (10, 5, dk), (6, 3, (20, 20, 26))]
        put(name, exact(X_BUCKET, {"M": IRON, "P": WATER}, metal={"M": 220}, extra=ex))
    # ---- chains
    for name, ramp in (("chain", R((70, 76, 96), 0.5)), ("copper_chain", COPPER), ("exposed_copper_chain", R((176, 124, 104), 0.36)),
                       ("weathered_copper_chain", R((110, 160, 120), 0.36)), ("oxidized_copper_chain", R((84, 170, 140), 0.36))):
        g = canvas()
        for k, cy in enumerate((2, 6, 10)):                     # alternating front / side links, straight down
            if k % 2 == 0:
                for (dx, dy, t) in ((0, 0, "5"), (1, 0, "4"), (-1, 1, "4"), (2, 1, "2"), (-1, 2, "3"), (2, 2, "1"), (0, 3, "2"), (1, 3, "1")):
                    g[cy + dy][7 + dx] = t
            else:
                for dy, t in ((0, "4"), (1, "3"), (2, "3"), (3, "2")):
                    g[cy + dy][7] = t
                    g[cy + dy][8] = "1"
        g[14][7], g[14][8] = "3", "1"
        put(name, exact(rows_of(g), {"M": ramp}, metal={"M": 200}))
    # ---- redstone bits and furniture
    red = R((230, 40, 30))
    put("lever", exact(X_LEVER, {"M": STONE, "V": STICK, "A": R((150, 110, 70))}))
    put("repeater", exact(X_REPEATER, {"M": STONE, "A": red, "V": STICK}, emis={"A": 120}))
    put("comparator", exact(X_COMPARATOR, {"M": STONE, "A": red, "V": STICK, "P": QUARTZ}, emis={"A": 120}))
    put("hopper", exact(X_HOPPER, {"M": R((84, 86, 96), 0.5)}, metal={"M": 200}))
    put("cauldron", exact(X_CAULDRON, {"M": R((84, 86, 96), 0.5), "P": R((36, 38, 48), 0.3)}, metal={"M": 200}))
    put("brewing_stand", exact(X_STAND, {"M": STONE, "A": R((250, 196, 50)), "P": glass}, emis={"A": 160}))
    put("flower_pot", exact(X_POT, {"M": R((176, 90, 60), 0.36)}))
    put("campfire", exact(X_CAMPFIRE, {"V": WOOD, "A": R((255, 150, 30))}, emis={"A": 220}))
    put("soul_campfire", exact(X_CAMPFIRE, {"V": WOOD, "A": R((70, 210, 230))}, emis={"A": 220}))
    put("armor_stand", exact(X_ARMORSTAND, {"V": WOOD, "M": STONE}))
    put("villagebell", exact(X_BELL, {"M": GOLD, "V": WOOD}, metal={"M": 220}))
    put("fireworks", exact(X_ROCKET, {"M": R((220, 50, 50)), "P": R((244, 244, 246), 0.12), "V": STICK}))
    put("fireworks_charge", exact(X_BALL, {"M": R(tuple(ISTATS["fireworks_charge"]["mean"]) if "fireworks_charge" in ISTATS else (120, 120, 120), 0.36, )}))
    for name, col, glow in (("trial_key", (226, 150, 70), 0), ("ominous_trial_key", (60, 150, 190), 60)):
        put(name, exact(X_KEY, {"M": R(col)}, metal={"M": 200}, emis={"M": glow}))
    put("end_crystal", exact(X_GEM, {"M": R((240, 120, 230))}, emis={"M": 160}, extra=[(5, 4, (255, 255, 255))]))
    put("dragon_fireball", exact(X_BALL, {"M": R((170, 60, 220))}, emis={"M": 140}, extra=[(5, 5, (255, 220, 255))]))
    put("spider_eye_fermented", exact(X_BALL, {"M": R((150, 80, 70))}, extra=[(7, 6, (40, 20, 20)), (8, 6, (40, 20, 20)), (7, 7, (40, 20, 20)), (9, 9, (200, 180, 120))]))
    put("melon_speckled", exact(X_MELON, {"M": R((232, 64, 64), 0.3), "A": GREEN}, metal={"M": 80},
                                extra=[(x, y, (255, 226, 90)) for (x, y) in ((5, 6), (8, 7), (10, 6), (6, 8), (9, 8))]))
    put("rabbit_foot", exact(X_DRUM, {"M": R((214, 180, 130), 0.3), "P": R((240, 232, 214), 0.2)}))
    put("goat_horn", exact(X_HORN, {"M": R((196, 180, 150), 0.4)}))
    put("brush", exact(X_SHOVEL, {"M": R((226, 200, 150), 0.3), "V": STICK, "A": COPPER}))
    put("spyglass", exact([""] * 3 + ["." * (14 - y) + "543" for y in range(3, 13)], {"M": R((214, 150, 70))}, metal={"M": 200},
                          extra=[(12, 3, (150, 220, 250)), (13, 3, (220, 245, 255))]))
    put("disc_fragment_5", exact([r[:8] for r in X_DISC], {"M": R((58, 56, 66), 0.6), "P": R((60, 200, 170))}))
    put("sniffer_egg", exact(X_EGG, {"M": R((170, 70, 60), 0.36)}, extra=[(x, y, (70, 130, 80)) for (x, y) in ((6, 5), (7, 6), (9, 8), (5, 9), (8, 10))]))
    put("turtle_egg", exact(X_EGG, {"M": R((236, 236, 220), 0.2)}, extra=[(x, y, (120, 190, 170)) for (x, y) in ((6, 5), (9, 7), (6, 9))]))
    put("dried_kelp", exact(X_INGOT, {"M": R((60, 84, 50), 0.44)}))
    put("book_portfolio", exact(X_BOOK, {"M": R((60, 110, 190)), "A": PAPER}))
    for name in ("chalkboard_small", "chalkboard_medium", "chalkboard_large"):
        put(name, exact(X_FRAME, {"V": WOOD, "P": R((50, 110, 80), 0.3)}))
    put("wolf_armor", exact(X_BARD, {"M": R((190, 130, 90), 0.36)}))
    for m, ramp in (("copper", COPPER), ("diamond", DIAMOND), ("gold", GOLD), ("iron", IRON), ("netherite", NETHERITE)):
        put(f"nautilus_armor/{m}_nautilus_armor", exact(X_BARD, {"M": ramp}, metal={"M": 200}))
    # ---- rods with something on the end
    for name, col in (("fishing_rod_cast", None), ("carrot_on_a_stick", (240, 130, 30)), ("warped_fungus_on_a_stick", (40, 170, 150))):
        g = [list(("." * (15 - y) + "xw").ljust(N, ".")) if 3 <= y <= 13 else list("." * N) for y in range(N)]
        for y in range(4, 8):
            g[y][13] = "c"
        ex = [] if col is None else [(12, 8, col), (13, 8, shift(col, dv=-0.2)), (12, 9, col), (13, 9, shift(col, dv=-0.2)), (13, 10, shift(col, dv=-0.3)),
                                     (12, 7, (80, 170, 60))]
        put(name, exact(rows_of(g), {"V": STICK, "A": R((226, 226, 230), 0.14)}, extra=ex))
    # ---- icons that are just the block's own sprite
    green = (120, 200, 90)
    for name, tc in (("hanging_roots", None), ("bush", green), ("firefly_bush", None), ("resin_clump", None), ("nether_sprouts", None),
                     ("mangrove_propagule", None), ("kelp", None)):
        src = {"kelp": "kelp_top"}.get(name, name)
        put(name, from_block(src, tc))


# ------------------------------------------------------------------ pixel maps
X_INGOT = ["", "", "", "", "", ".....445544444", "....4335533331", "...43333333321", "...2222222221", "...111111110"]
X_NUGGET = ["", "", "", "", "", "", "......543", ".....54332", ".....433321", "......3221", ".......21"]
X_GEM = ["", "", "", "....55443333", "...5544333322", "..544323333221", "...3332332221", "....33323211", ".....332211", "......3211", ".......21"]
X_EMERALD = ["", "", ".....554443", "....54333332", "...5433333321", "...4354333221", "...4343333221", "...4343333221", "...4343333221", "...4332222221", "....33222211", ".....222211"]
X_SHARD = ["", "............5", "..........5432", ".........54332", "........543321", ".......543321", "......443321", ".....543321", "....443321", "...443321", "...33221", "....221"]
X_FLINT = ["", "", "", "......443", ".....44332", "....4433321", "...44333321", "...43333321", "....3332221", ".....22211", "......211"]
X_LUMP = ["", "", "", "......44443", "....44333332", "...4433233332", "..44333333321", "..43323333321", "..33333332221", "...332222211",
          ".....222111"]
X_HIDE = ["", "", "..44......44", "..4333..33332", "...433333332", "...433333332", "..4333333332", "..4333333332", "...333333321",
          "...332..2221", "..332....221", "..22......11"]
X_PILE = ["", "", "", "", "", "", "", "", ".......43", ".....443332", "...4433333321", "..443333333221", "..222222222211"]
X_BALL = ["", "", "", "......5543", "....55433332", "...5543333332", "...4433333322", "...4333333322", "...3333333221", "...3333332221", "....33222211", "......2211"]
X_EGG = ["", "", "......543", ".....54332", "....5433332", "....4333332", "...443333322", "...433333322", "...433333221", "...333332221", "....3322221", ".....22211"]
X_BONE = ["", "", "............44", "..........4432", "..........432", ".........43", "........43", ".......43", "......43", ".....43",
          "....43", "...43", ".4432", ".322"]
X_ARROW = ["", ".........44445", "...........432", "...........x32", "..........x..2", ".........x...1", "........x", ".......x", "......x", ".....x", "....x", ".ccx", "..dc", "...d"]
X_BOW = ["", "..........xxw...", "........xxw.a...", "......xyw..a....", "....xxw...a.....", "...xw.....a.....", "..xw.....a......", "..xw....a.......", ".xw....a........", ".xw...a.........", ".xw..a..........", "..wwa...........", "...a............", ""]
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
X_STEAK = ["", "", "", "....RSSSSSSR....", "..RS44444444SR..", "..S4433333334S..", "..R43TTTTT333R..", "..R4322T22333R..", "..R3333T33332R..", "..Q3333T33322Q..", "...Q33333322Q...", "....Q222221Q....", "......QQQQ......"]
X_CHOP = ["", "", "......RSSSR.....", "....RS44444SR...", "...T444333334S..", "..TT4333333334S.", "..TS4333333333S.", "..TS3333333332R.", "..TR3333333322R.", "..TTR33333222R..", ".TT.RR222222R...", ".ST...RRRRRR....", ".SS............."]
X_RACK = ["", "", "....T...T...T...", "....S...S...S...", "....T...T...T...", "...4TSSSTSSST2..", "..5443333333332.", "..4333333333332.",
          "..4333333333322.", "..3333333333221.", "...33322222221..", ".....2222211...."]
X_CHICKEN = ["", "", "", "..TS........ST..", "...44......44...", "....43....34....", "....44333344....", "...4433333332...",
             "..443333333332..", ".34333333333323.", "..433333333322..", "..333333333221..", "...3322222211...", ".....222211....."]
X_LEG = ["", ".........44443..", ".......44433332.", "......443333332.", ".....4433333332.", ".....433SS33332.", ".....4333SS3322.",
         ".....3333333322.", "......333333221.", ".....T2222222...", "....TS.221......", "...TS...........", "..TS............",
         ".TTS............", ".ST............."]
X_ROTTEN = ["", "", "", ".....443........", "...4433332.44...", "..443R33333332..", "..4333333RR332..", "...33.3333R3321.", "..433333333332..",
            "..33R333.33322..", "...2222232221...", ".....21..211...."]
X_DRUM = ["", ".........5444...", ".......54433332.", "......543333332.", "......433333332.", "......433333322.", "......33333322..", ".....T3333222...", "....TS.2222.....", "...TS...........", "..TS............", ".TTS............", ".ST............."]
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
# a small winged idol: broad head with gem eyes and a grin, feathered wings,
# a jewel on the chest, a belt and two feet
X_TOTEM = ["", ".....544443.....", "....54433332....", "....4ec33ec2....", "....43322332....", "....43100132....", ".....332222.....",
           ".54..433332..54.", ".443343dd323322.", "..32.433332.21..", ".....433332.....", ".....bccccb.....", ".....433332.....",
           "......3222......", ".....32..21....."]
X_BOTTLE = ["", ".......xw", ".......xw", "......cddb", ".......dc", ".......dc", "......d44c", "....dd5443cc", "...d55443332c",
            "...d54433332b", "...d44333332b", "...c43333322b", "....c333222b", "......bbbb"]
X_SPLASH = ["", "......xyyw", ".......xw", "......cddb", ".......dc", "......d44c", ".....d5443c", ".....d44332c", "....d5443332c",
            "....d4433332b", "...d544333322b", "...d443333222b", "...cbbbbbbbbbb"]
X_LINGER = ["", "....e.....e", ".......xw.e", "......cddb", "......d44c", ".....d5443c", ".....d54332c", ".....d44332c", ".....d43332b",
            ".....d43332b", ".....c43322b", ".....c33222b", "......bbbb"]
X_BOAT = ["", "", "", "", "", "", ".4............4.", ".43..........32.", ".43333333333332.", "..333333333322..", "...2222222221...",
          "....11111110...."]
X_BOAT_CHEST = ["", "", "", "", ".....TTTTTS", ".....TSeeSR", ".4...TSSSSR...4.", ".43..SRRRRQ..32.", ".43333333333332.",
                "..333333333322..", "...2222222221...", "....11111110...."]
X_SIGN = ["", "", "..444444444443", "..433333333332", "..432222222232", "..433333333332", "..432222223332", "..433333333332",
          "..222222222221", ".......xw", ".......xw", ".......xw", ".......xw", ".......xv"]
X_HANG = ["", "...b......b", "...c......c", "...b......b", "..444444444443", "..433333333332", "..432222222232", "..433333333332",
          "..432222223332", "..433333333332", "..222222222221"]
X_DOOR = ["", "....44444443", "....43333332", "....4RR3RR32", "....4RR3RR32", "....43333332", "....4RR3RR32", "....4RR3RR32",
          "....43333332", "....432232e2", "....43222232", "....43222232", "....43222232", "....43333332", "....22222221"]
X_CART = ["", "", "", "", "", "", "", "..444444444443", "..433333333332", "...3333333332", "...2222222221", "....ba....ba"]
X_CART_LOAD = ["", "", "", ".....TTTTTS", ".....TSSSSR", ".....TSSSSR", ".....SRRRRQ", "..444444444443", "..433333333332",
               "...3333333332", "...2222222221", "....ba....ba"]
X_DISC = ["", "", "......2222", "....22333322", "...2343333332", "..234333333331", "..2333TSSR3331", "..2333S00R3331", "..2333S00R3331",
          "..2333RRRQ3331", "..233333333431", "...2333333331", "....11333311", "......1111"]
X_SHEARS = ["", "...5.......5", "...45.....54", "....43...34", ".....43.34", "......4334", ".......bb", ".....SR..SR", "...S..R.S..R",
            "...S..R.S..R", "....RR...RR"]
X_COMPASS = ["", "", "......4444......", "....44333322....", "...43RRRRRR21...", "..43RRRcRRRR21..", "..43RRRbRRRR21..", "..43RRRSRRRR21..",
             "..43RRRQRRRR21..", "..43RRRQRRRR21..", "...43RRRRRR21...", "....33222211....", "......1111......"]
X_CLOCK = ["", "", "......4444......", "....44333322....", "...43RRRRRR21...", "..43RRRaRRRR21..", "..43RRRaRRRR21..", "..43RRRaaaRR21..",
           "..43RRRRRRRR21..", "..43RRRRRRRR21..", "...43RRRRRR21...", "....33222211....", "......1111......"]
X_BED = ["", "", "", "", "", "", "..SSS444444444..", "..SRR4333333332.", "..RRQ3333333322.", "..xxxxxxxxxxxxw.", "..xw.........xw.",
         "..xv.........xv."]
X_CUSHION = ["", "", "", "", "", "....44444444....", "..544333333332..", ".54333333333332.", ".43333333333322.", ".33333333333221.",
             "..222222222211.."]
X_BARD = ["", "", "", "", "..44............", "..4344444444....", "..433333333332..", "..433333333332..", "...33333333322..",
          "...3322..33221..", "...322....221...", "...21......11..."]
X_SADDLE = ["", "", "", "", "....44444444....", "...4433333332...", "..443333333332..", "..43322..22332..", "..432......232..",
            "..32........21..", "..a..........a..", ".bcb........bcb."]
X_TAG = ["", "", "", "", "..a.............", "...a............", "....444444444...", "...43333333332..", "..43.333333332..", "...43333333332..", "....222222221..."]
X_FLINTSTEEL = ["", "", "", "..54443.........", "..4...32........", "..4....2........", "..43...2........", "...3221.........",
                "........TTS.....", ".......TSSRR....", ".......SSRRQ....", "........RRQ....."]
X_MACE = ["", "........54443...", "........43332...", "........43332...", "........43322...", "........32221...", ".......xw.......",
          "......xw........", ".....xw.........", "....xw..........", "...xw...........", "..xw............", ".xv............."]
X_WING = ["", "", "....443.", "...4433.", "..44333.", "..43332.", ".443332.", ".43332..", ".4332...", ".332....", ".32.....", ".2......"]
X_SHELL = ["", "", "", "", ".....444443.....", "...4433333332...", "..443333333332..", "..433333333332..", "..333333333322..",
           "..222222222221.."]
X_CAKE = ["", "", "", "", "", "...SSSSSSSSSS...", "..STTTcTTcTTTS..", "..SSRSSRSSRSSR..", "..433333333332..", "..4cccccccccc2..",
          "..433333333332..", "..222222222221.."]
X_LANTERN = ["", ".......aa.......", ".......aa.......", ".....444443.....", "....43333332....", "....3STTTTS2....", "....3TUUTTS2....",
             "....3TUTTTS2....", "....3TTTTSS2....", "....3STTSSR2....", "....43333332....", ".....222221....."]
X_PAINTING = ["", "", "", "..xxxxxxxxxxxw..", "..xTTTTTTTTTTw..", "..xTTTTTUUTTTw..", "..xTTTTTUUTTTw..", "..xTTccTTTTTTw..",
              "..xTccccTTccTw..", "..xccccccccccw..", "..xbbbbbbbbbbw..", "..wwwwwwwwwwwv.."]
X_FRAME = ["", "", "", "..yyyyyyyyyyyx..", "..yRRRRRRRRRRx..", "..yRSSSSSSSRRx..", "..yRSSSSSSSRRx..", "..yRSSSSSSSRRx..",
           "..yRSSSSSSSRRx..", "..yRRRRRRRRRQx..", "..yRRRRRRRRQQx..", "..xxxxxxxxxxxw.."]
X_TABLET = ["", "", "...4444444443...", "...4333333332...", "...43SSSSSS32...", "...43SRRRRS32...", "...43SRSSRS32...", "...43SRRRRS32...",
            "...43SSSSSS32...", "...4333333332...", "...4332222332...", "...4333333332...", "...2222222221..."]
X_SHERD = ["", "", "", "....4444443.....", "...443333332....", "..44333333332...", "..43333333321...", "..43333333321...",
           "...3333333321...", "...33333333221..", "....3322222211..", "......222111...."]
X_CANDLE = ["", "", "", "", ".......a", ".......a", "......5443", "......4332", "......4332", "......4332", "......4332", "......4332",
            "......4332", "......3221"]
X_BUNDLE = ["", "", "......cddc", ".....dccccd", "......b33b", ".....543332", "....54333332", "...5433333332", "...4333333332",
            "...4333333322", "...3333333221", "....33322221", "......2211"]
X_SPEAR = ["", ".............5", "............54", "...........54", "..........543", ".........5432", ".........a32", "........xa", "......xw", ".....xw", "....xw", "...xw", "..xw", ".xv"]
X_LEVER = ["", "", "", "", "", "........e.......", "........x.......", "........x.......", "........x.......", "........x.......", "........x.......", "......44444.....", "......33332.....", "......22221....."]
X_REPEATER = ["", "", "", "", "", "", "", "....e.....e", "....w.....w", "..444444444443", "..433333333332", "..222222222221"]
X_COMPARATOR = ["", "", "", "", "", "", "", "....e..S..e", "....w..R..w", "..444444444443", "..433333333332", "..222222222221"]
X_HOPPER = ["", "", "", "..444444444443", "..433333333332", "...4333333332", "....43333332", "....43333332", ".....433332",
            "......4332", "......3221", ".......21"]
X_CAULDRON = ["", "", "", "", "..444444444443", "..4RRRRRRRRRR2", "..433333333332", "..433333333332", "..433333333332",
              "..333333333322", "..21..2222..21", "..21........21"]
X_STAND = ["", "", ".......dc", ".......dc", ".......dc", "....S..dc..S", "...STS.dc.STS", "...SRS.dc.SRS", "....R..dc..R", ".......dc",
           "..44444dc44443", "..333333333332", "...2222222221"]
X_POT = ["", "", "", "", "", "", "..444444444443", "..433333333332", "...4333333332", "...4333333332", "....33333322", "....22222221"]
X_CAMPFIRE = ["", "", ".......e", "......ede", "......dedc", ".....cdeedc", ".....cddddc", "......cccc", "..yyyyyyyyyyyx",
              "..xxxxxxxxxxxw", "..wwvwwwwvwwwv"]
X_ARMORSTAND = ["", "......yyyx", "......yxxw", "......xwww", "...yyyyyyyyyx", ".......xw", ".......xw", ".......xw", ".......xw",
                ".......xw", ".....yyyyyx", ".....x...w", ".....x...w", "...4444444443"]
X_BELL = ["", "", "......xxxx", ".......44", "......5443", ".....544332", ".....443332", "....54333322", "....44333322",
          "...4433333221", "...2222222221", ".......21"]
X_ROCKET = ["", ".......54", "......5443", "......4332", "......TSSR", "......4332", "......4332", "......TSSR", "......3221", ".......xw",
            ".......xw", ".......xw", ".......xv"]
X_KEY = ["", "", "", "...4443", "..43..32", "..4....2", "..43..32", "...4332", ".....43", "......43", ".......43", "........432",
         ".........3.2"]


# ---------------------------------------------------------------- v2 shapes


def _blank():
    return [["."] * N for _ in range(N)]


def _out(g):
    return ["".join(r) for r in g]


def handle(g, top_y=2, bottom_y=14, bind=()):
    # diagonal haft: pair (x, x+1) with x = 15 - y
    for y in range(top_y, bottom_y + 1):
        x = 15 - y
        g[y][x] = "x" if (y % 3) else "y"
        if x + 1 < N:
            g[y][x + 1] = "w"
    for y in bind:
        x = 15 - y
        g[y][x], g[y][x + 1] = "b", "a"
    g[bottom_y][15 - bottom_y] = "v"


def axe():
    g = _blank()
    handle(g, 3, 14, bind=(4,))
    rows = {1: (7, 10), 2: (5, 12), 3: (4, 11), 4: (3, 10), 5: (3, 9), 6: (4, 8), 7: (5, 7)}
    for y, (x0, x1) in rows.items():
        for x in range(x0, x1 + 1):
            if g[y][x] != ".":
                continue
            if x == x0:
                t = "5" if y <= 4 else "4"          # bright cutting edge
            elif x == x0 + 1:
                t = "4" if y <= 4 else "3"
            elif y == 1 or y == 2:
                t = "4"
            elif y >= 6:
                t = "2"
            elif x >= x1 - 1:
                t = "2"
            else:
                t = "3"
            g[y][x] = t
    g[7][7], g[6][8] = "1", "1"
    return _out(g)


def diamond():          # brilliant cut: flat crown on top, V pavilion to a point
    return ["", "", "", "....45555443....", "...4555444433...", "..454444333332..", "..333333332221..", "...3332322221...",
            "....33222211....", ".....332211.....", "......3211......", ".......21.......", ""]


def emerald():          # tall step-cut crystal
    return ["", ".......54.......", "......5443......", ".....544332.....", ".....543332.....", ".....543332.....", ".....543332.....",
            ".....543332.....", ".....543332.....", ".....543332.....", ".....443322.....", "......3322......", ".......21......."]


def iron_ingot():       # long thin bar, seen from above at an angle
    return ["", "", "", "", "", "", ".......5555554..", ".....554444443..", "...55444444432..", "..443333333322..", "..3333333322....",
            "..22222221......"]


def gold_ingot():       # chunky bullion bar, wide base, stamped panel on top
    return ["", "", "", "", "", ".....55555543...", "....5444444432..", "...5445555443...", "..544433334432..", "..443333333321..",
            "..433333333221..", "..222222222211.."]


def copper_ingot():     # rounded bar with dents
    return ["", "", "", "", "", "", "......544443....", "....5444434432..", "...54433433332..", "...43333333321..", "....3332333221..",
            "......222211...."]


def netherite_ingot():  # heavy dark bar with a raised ridge
    return ["", "", "", "", "", ".....44444443...", "....4555555543..", "...433333333332.", "...444444444432.", "...333333333322.",
            "...222222222221.", "...111111111110."]


def iron_nugget():      # two small pebbles
    return ["", "", "", "", "", "", ".....54.........", "....5443........", "....4332..543...", ".....321.54432..", "........43321...",
            ".........221...."]


def gold_nugget():      # one round shiny nugget
    return ["", "", "", "", "", "", "......5543......", ".....544433.....", ".....4543332....", ".....4433322....", "......33221.....",
            ".......221......"]


def copper_nugget():    # angular chip
    return ["", "", "", "", "", "", ".......54.......", "......5443......", ".....54333......", "....5433322.....", ".....33221......",
            "......221......."]


# meats --------------------------------------------------------------
# beef: thick steak, marbled with white streaks, fat rim along the top edge
def steak():
    return ["", "", "", ".....PPPPP......", "...PP4444PPP....", "..P44333444PP...", "..43335P33344P..", "..4333355333432.",
            "..3335333353332.", "..33333355333321", "...33333333321..", "....222222211...", "......1111......"]


# pork: chop with a curved bone handle on the left and a thick fat band
def chop():
    return ["", "", "......PPPPPP....", "....PP444444P...", "...P4433333342..", "..TP43333333332.", "..TP43333333332.", ".TSP33333333322.",
            ".TS.P333333322..", ".TS..PP22222....", ".SS....PPP......", "..R.............", ""]


# mutton: rack of ribs, three bone tips sticking up
def rack():
    return ["", "", "...T...T...T....", "...S...S...S....", "...S...S...S....", "..44444444444...", ".4433333333332..", ".4333333333332..",
            ".3333333333322..", ".3333333333221..", "..22222222221...", "...111111111....", ""]


# chicken: big round drumstick, knuckle bone at the end
def drumstick():
    return ["", "......54443.....", ".....5443332....", "....544333332...", "....443333332...", "....433333322...", "....33333322....",
            ".....3332221....", "......T221......", ".....TS.........", "....TS..........", "...TTS..........", "...SS...........", ""]


# rabbit: small, slim hind leg - long and narrow, little bone
def hind_leg():
    return ["", "", ".........544....", "........5433....", ".......54332....", ".......43332....", "......43332.....", "......3332......",
            ".....3322.......", "....T221........", "...TS...........", "..TS............", "..S.............", ""]


# hoglin: big slab with a round bone cross-section in the middle
def slab():
    return ["", "", "", "...4444444443...", "..443333333332..", ".44333TTT333332.", ".4333TSSST33332.", ".4333TS.ST33322.",
            ".3333TSSST33322.", ".33333TTT333221.", "..333333333221..", "...2222222221...", "....11111111...."]



X_AXE = axe()
X_GEM = diamond()
X_EMERALD = emerald()
INGOTS = {"iron_ingot": iron_ingot(), "gold_ingot": gold_ingot(), "copper_ingot": copper_ingot(), "netherite_ingot": netherite_ingot()}
NUGGETS = {"iron_nugget": iron_nugget(), "gold_nugget": gold_nugget(), "copper_nugget": copper_nugget()}
X_STEAK, X_CHOP, X_RACK, X_DRUM, X_HIND, X_SLAB = steak(), chop(), rack(), drumstick(), hind_leg(), slab()
X_HORN = ["", "", "..........54....", ".........5443...", "........54332...", "...4....4332....", "..443..4332.....", "..43334332......", "...3333322......", "....22221.......", "......1.........", ""]
X_CLUSTER = ["", "", "........5.......", "....5..543......", "...54..433..5...", "...43.4433.54...", "..443.4332.43...", "..432.4332443...", "..3324332243....", "...3222222322...", "....22222211....", "......1111......", ""]


# ---------------------------------------------------------------- v3: spear and totem


def _spear():
    """Diagonal spear: a long wooden haft and a broad leaf-shaped head with a
    raised centre ridge, a wrapped collar where they meet and a capped butt."""
    g = [["."] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            along = (x - y) / 2.0                     # 7.5 at the top-right tip, -7.5 at the bottom-left
            perp = (x + y - 15) / 2.0                 # 0 on the haft line, - towards the top-left (lit side)
            tip = 7.5 - along
            if 0 <= tip <= 6.2:                       # head: a pointed leaf
                width = min(tip * 0.62, (6.2 - tip) * 0.9 + 0.3, 1.9)
                if abs(perp) <= width + 0.01:
                    if abs(perp) < 0.3:
                        t = "5" if tip < 3.5 else "4"         # bright centre ridge
                    elif perp < 0:
                        t = "4" if perp > -1.2 else "3"       # lit half
                    else:
                        t = "2" if perp < 1.2 else "1"        # shaded half
                    g[y][x] = t
            elif 6.2 < tip <= 7.3 and -0.1 <= perp <= 0.6:   # wrapped collar
                g[y][x] = "b" if perp < 0.25 else "a"
            elif tip > 7.3 and -0.1 <= perp <= 0.6:          # haft
                g[y][x] = ("y" if int(tip) % 3 == 0 else "x") if perp < 0.25 else "w"
    g[14][0] = "c"
    return ["".join(r) for r in g]


X_TOTEM = [
    "................",
    "......5544......",
    ".....544443.....",
    ".....4ec4ec.....",
    ".....443332.....",
    ".....43RR32.....",
    "......3322......",
    ".55444443333322.",
    "..44..4432..21..",
    "......4dd2......",
    "......4332......",
    "......SSSS......",
    ".....443322.....",
    ".....432.221....",
    ".....32...21....",
    "................",
]
assert all(len(r) == N for r in X_TOTEM)

X_SPEAR = _spear()


# ---------------------------------------------------------------- animated compass and clock
def _dial(rim, face):
    """Round dial: rim ramp, face ramp. Returns (rows-like grid of chars)."""
    g = [["."] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if d <= 6.6:
                if d > 5.2:
                    g[y][x] = "4" if (x + y) < 15 else ("2" if (x + y) > 16 else "3")
                else:
                    g[y][x] = "S" if (x + y) < 13 else "R"
    return g


def compass_frames(rim, face, needle, tail, frames=32, start=180.0):
    import math
    from .core import stack_frames
    out = []
    for f in range(frames):
        ang = math.radians((start + f * 360.0 / frames) % 360)        # 0 = up, clockwise
        g = _dial(rim, face)
        dx, dy = math.sin(ang), -math.cos(ang)
        for k in range(1, 5):                                          # needle point
            x, y = int(round(7.5 + dx * k)), int(round(7.5 + dy * k))
            g[y][x] = "e" if k > 1 else "d"
        for k in range(1, 4):                                          # tail
            x, y = int(round(7.5 - dx * k)), int(round(7.5 - dy * k))
            g[y][x] = "x"
        g[7][7], g[8][8] = "0", "0"
        out.append(exact(["".join(r) for r in g], {"M": rim, "P": face, "A": needle, "V": tail}, metal={"M": 200}))
    return stack_frames(out)


def clock_frames(frames=64):
    import math
    from .core import stack_frames
    sky, night, sun, moon = R((90, 170, 240), 0.3), R((24, 34, 80), 0.4), (255, 230, 90), (236, 240, 250)
    out = []
    for f in range(frames):
        day_dir = f * 360.0 / frames                                   # where the daylight half faces (0 = up)
        g = _dial(GOLD, sky)
        extra = []
        for y in range(N):
            for x in range(N):
                d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
                if d <= 5.2:
                    a = math.degrees(math.atan2(x - 7.5, -(y - 7.5))) % 360
                    diff = abs(((a - day_dir + 180) % 360) - 180)
                    if diff > 90:
                        extra.append((x, y, night[2] if (x + y) < 15 else night[1]))
        r = math.radians(day_dir)
        sx, sy = int(round(7.5 + math.sin(r) * 3.2)), int(round(7.5 - math.cos(r) * 3.2))
        mx, my = int(round(7.5 - math.sin(r) * 3.2)), int(round(7.5 + math.cos(r) * 3.2))
        extra += [(sx, sy, sun), (mx, my, moon)]
        extra += [(7, 1, (60, 40, 20)), (8, 1, (60, 40, 20))]          # fixed pointer at the top
        out.append(exact(["".join(r_) for r_ in g], {"M": GOLD, "P": sky}, metal={"M": 220}, extra=extra))
    return stack_frames(out)


def build_animated(out):
    face = R((240, 236, 222), 0.14)
    red, grey = R((220, 40, 40)), R((120, 124, 132), 0.4)
    if "compass_atlas" in ISTATS:
        out["compass_atlas"] = compass_frames(R((150, 150, 160), 0.4), face, red, grey)
    if "lodestonecompass_atlas" in ISTATS:
        out["lodestonecompass_atlas"] = compass_frames(R((110, 96, 150), 0.4), face, R((60, 200, 220)), grey)
    if "recovery_compass_atlas" in ISTATS:
        t = compass_frames(R((20, 90, 110), 0.5), R((40, 60, 70), 0.3), R((90, 230, 240)), R((30, 60, 70), 0.4))
        t.emis = np.where(t.alpha > 0, 30, 0)
        out["recovery_compass_atlas"] = t
    if "watch_atlas" in ISTATS:
        out["watch_atlas"] = clock_frames(ISTATS["watch_atlas"]["size"][1] // 16)


# ---------------------------------------------------------------- layered UI icons
def from_mask(name, ramp, metal=None):
    """Paint an icon inside the layout the game composes it from."""
    from .blocks_rest import shade_mask
    m = np.array([[c == "1" for c in row] for row in ISTATS[name]["mask"]])
    idx = np.clip(shade_mask(m) + 1, 0, 5)
    rgb = np.where(m[..., None], np.array(ramp, np.uint8)[idx], 0).astype(np.uint8)
    t = Tex(rgb, np.where(m, 0.4 + idx * 0.1, 0.0), alpha=np.where(m, 255, 0).astype(np.uint8), rough=200, bump=0.7)
    if metal:
        t.metal = np.where(m, metal, 0)
    return t


def build_layers(out):
    wax = dict(DYES)
    wax["light_gray"] = DYES["silver"]
    for name in ISTATS:
        if "mask" not in ISTATS[name]:
            continue
        if name.startswith("bundle"):
            dye = name[len("bundle_"):].split("_open")[0] if name.startswith("bundle_") and not name.startswith("bundle_open") else None
            col = wax.get(dye, (150, 84, 44)) if dye else (150, 84, 44)
            ramp = R(col, 0.36)
            if name.endswith("_open_back"):
                ramp = R(shift(col, dv=-0.25), 0.4)              # inside of the bag, in shadow
            out[name] = from_mask(name, ramp)
        elif name.startswith("empty_armor_slot"):
            out[name] = from_mask(name, R((150, 150, 160), 0.3))


def build_plants(out):
    def put(name, tex):
        if name in ISTATS and ISTATS[name]["size"] == [16, 16]:
            out[name] = tex
    leaf = R((90, 150, 50))
    put("bamboo", exact(["", "", "...........e....", "..........ed....", "..........43....", ".........43.....", ".........32.....",
                         "........43......", "........32......", ".......43.......", ".......32.......", "......43........",
                         "......32........", ".....43.........", ".....32.........", ""], {"M": R((120, 170, 50), 0.4), "A": leaf}))
    put("pink_petals", exact(["", "", "....SS..........", "...STTS...SS....", "....SS...STTS...", "..........SS....", "......SS........",
                              ".....STTS.......", "......SS..SS....", "..........STS...", "...SS......S....", "..STTS..........",
                              "...SS...........", ""], {"P": R((240, 160, 200), 0.36)}))
    put("wildflowers", exact(["", "", "....e.....e.....", "...ede...ede....", "....e.....e.....", "....3.....3.......", "....3..e..3.....",
                              "....3.ede.3.....", "....3..e..3.....", "....3..3..3.....", "....3..3..3.....", "...333.3.333....",
                              "..33..333...3...", ""], {"M": R((80, 140, 50), 0.4), "A": R((250, 214, 80))}))
    put("leaf_litter", exact(["", "", "", "....443.........", "...44332...43...", "....332...4432..", "........SS.332..", ".......STTS.....",
                              "...43...SS......", "..44322.....43..", "...3321....4432.", "...........32...", ""],
                             {"M": R((170, 110, 50), 0.4), "P": R((150, 80, 40), 0.4)}))
    put("pitcher_pod", exact(["", "", ".......ee.......", "......edde......", ".......cc.......", "......5443......", ".....544332.....",
                              ".....443332.....", ".....433322.....", ".....333221.....", "......3221......", ".......21.......", ""],
                             {"M": R((120, 84, 64), 0.4), "A": R((90, 150, 140))}))
    put("quiver", exact(["", "........e.e.....", "........d.d.....", "........x.x.....", "......544443....", ".....54333332...",
                         ".....43333332...", ".....4bbbbbb2...", ".....43333332...", ".....43333322...", ".....33333221...",
                         "......332221....", ".......2211.....", ""], {"M": LEATHER, "A": R((236, 236, 240), 0.14), "V": STICK}))
    put("straw_bed", exact(["", "", "", "", "", "", "....5544444443..", "...544433333332.", "..5433333333332.", "..4333333333322.",
                            "..3333333333221.", "...22222222221..", ""], {"M": R((214, 180, 80), 0.36)}))
