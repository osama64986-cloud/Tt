"""Showcase images for the CurseForge page, rendered from the pack's own textures:
an isometric diorama, a block catalogue, the ore line-up, the logo and the
banner.  Output: dist/curseforge/images/."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "pack", "textures", "blocks")
OUT = os.path.join(ROOT, "dist", "curseforge", "images")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
AR_NABD = "ﺾﺒﻧ"          # نبض, joined letter shapes in display order


def tex(name, tint=None):
    p = os.path.join(B, name + ".png")
    if not os.path.exists(p):
        p = os.path.join(B, name + ".tga")
    t = Image.open(p).convert("RGBA")
    t = t.crop((0, 0, t.width, t.width))         # first frame of animated strips
    if t.size != (16, 16):
        t = t.resize((16, 16), Image.NEAREST)
    if tint:
        a = np.array(t).astype(float)
        a[..., :3] = a[..., :3] * np.array(tint) / 255.0
        t = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    return t


def shade(t, k):
    a = np.array(t).astype(float)
    a[..., :3] *= k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


class Iso:
    """Isometric renderer: x to the lower right, z to the lower left, y up."""

    def __init__(self, L=48):
        self.L = L
        self.cubes = []

    def add(self, x, y, z, top, side=None, front=None):
        self.cubes.append((x, y, z, top, side or top, front or side or top))

    def screen(self, x, y, z):
        L = self.L
        return ((x - z) * L * 0.866, (x + z) * L * 0.5 - y * L)

    def face(self, canvas, img, o, u, v, off):
        """map a 16x16 texture onto the parallelogram o + s*u + t*v (s, t in 0..1)"""
        ox, oy = o[0] + off[0], o[1] + off[1]
        xs = [ox, ox + u[0], ox + v[0], ox + u[0] + v[0]]
        ys = [oy, oy + u[1], oy + v[1], oy + u[1] + v[1]]
        x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        w, h = int(math.ceil(max(xs))) - x0 + 1, int(math.ceil(max(ys))) - y0 + 1
        # inverse map: (X, Y) -> (s, t) -> texel
        det = u[0] * v[1] - u[1] * v[0]
        a = v[1] / det * 16
        b = -v[0] / det * 16
        d = -u[1] / det * 16
        e = u[0] / det * 16
        c = -(a * (ox - x0) + b * (oy - y0))
        f = -(d * (ox - x0) + e * (oy - y0))
        big = img.transform((w, h), Image.AFFINE, (a, b, c, d, e, f), resample=Image.NEAREST)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).polygon([(xs[0] - x0, ys[0] - y0), (xs[1] - x0, ys[1] - y0),
                                      (xs[3] - x0, ys[3] - y0), (xs[2] - x0, ys[2] - y0)], fill=255)
        alpha = Image.fromarray(np.minimum(np.array(mask), np.array(big)[..., 3]).astype(np.uint8))
        big.putalpha(alpha)
        canvas.alpha_composite(big, (x0, y0))

    def render(self, size, off, bg):
        canvas = Image.new("RGBA", size, bg)
        L = self.L
        for x, y, z, top, side, front in sorted(self.cubes, key=lambda c: (c[0] + c[2], c[1], c[0])):
            p = self.screen(x, y + 1, z)
            ux = (L * 0.866, L * 0.5)       # +x direction
            uz = (-L * 0.866, L * 0.5)      # +z direction
            down = (0, L)
            self.face(canvas, top, p, ux, uz, off)                                       # top
            px = self.screen(x, y + 1, z + 1)
            self.face(canvas, shade(front, 0.78), px, ux, down, off)                     # +z face (left)
            pz = self.screen(x + 1, y + 1, z)
            self.face(canvas, shade(side, 0.62), pz, uz, down, off)                      # +x face (right)
        return canvas


def diorama():
    grass_top = tex("grass_carried")
    grass_side = tex("grass_side_carried")
    dirt, stone, deep = tex("dirt"), tex("stone"), tex("deepslate/deepslate")
    ores = [tex(n) for n in ("coal_ore", "iron_ore", "gold_ore", "diamond_ore", "emerald_ore", "redstone_ore",
                             "lapis_ore", "copper_ore")]
    deep_ores = [tex(n) for n in ("deepslate/deepslate_diamond_ore", "deepslate/deepslate_gold_ore")]
    iso = Iso(44)
    n = 12
    rng = np.random.default_rng(7)
    height = np.full((n, n), 3)
    for x in range(n):
        for z in range(n):
            height[x, z] = 3 + (1 if (x - 3) ** 2 + (z - 4) ** 2 < 9 else 0) + (1 if x < 2 and z < 3 else 0)
    k = 0
    for x in range(n):
        for z in range(n):
            if 8 <= x and 7 <= z:
                continue                                  # badlands corner below
            if 3 <= x <= 5 and 8 <= z <= 10:
                continue                                  # pond
            h = height[x, z]
            for y in range(h + 1):
                edge = (x == n - 1 or z == n - 1)
                if y == 0:
                    t = deep_ores[k % 2] if edge and rng.random() < 0.35 else deep
                    k += 1
                    iso.add(x, y, z, t)
                elif y < h - 1:
                    t = ores[k % len(ores)] if edge and rng.random() < 0.45 else stone
                    k += 1
                    iso.add(x, y, z, t)
                elif y < h:
                    iso.add(x, y, z, dirt)
                else:
                    iso.add(x, y, z, grass_top, grass_side, grass_side)
    # pond
    water = tex("water_still", tint=(70, 120, 220))
    sand = tex("sand")
    for x in range(3, 6):
        for z in range(8, 11):
            for y in range(0, 2):
                iso.add(x, y, z, stone)
            iso.add(x, 2, z, sand)
            iso.add(x, 3, z, water)
    # badlands corner: terracotta bands and red sand
    bands = ["hardened_clay_stained_orange", "hardened_clay", "hardened_clay_stained_yellow",
             "hardened_clay_stained_white", "hardened_clay_stained_brown", "hardened_clay_stained_red"]
    for x in range(8, n):
        for z in range(7, n):
            top = 5 + (1 if x > 9 and z > 8 else 0)
            for y in range(top):
                iso.add(x, y, z, tex(bands[y % len(bands)]))
            iso.add(x, top, z, tex("red_sand"))
    # a little house: cobblestone base, planks, stone bricks corners, glass window
    planks, cob, sbrick, glass = tex("planks_oak"), tex("cobblestone"), tex("stonebrick"), tex("glass")
    for x in range(6, 9):
        for z in range(1, 4):
            base = height[x, z] + 1
            iso.add(x, base, z, cob)
            for y in (1, 2):
                corner = x in (6, 8) and z in (1, 3)
                t = sbrick if corner else (glass if (y == 2 and x == 7 and z == 3) else planks)
                if x in (6, 8) or z in (1, 3):
                    iso.add(x, base + y, z, t)
            iso.add(x, base + 3, z, planks)
    # a tree
    log, logtop = tex("log_oak"), tex("log_oak_top")
    leaves = tex("leaves_oak_carried")
    tx, tz = 2, 2
    for y in range(4):
        iso.add(tx, height[tx, tz] + 1 + y, tz, logtop, log, log)
    ly = height[tx, tz] + 4
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in (0, 1):
                if dy == 1 and abs(dx) + abs(dz) == 2:
                    continue
                if dx == 0 and dz == 0 and dy == 0:
                    continue
                iso.add(tx + dx, ly + dy, tz + dz, leaves)
    iso.add(tx, ly + 1, tz, leaves)
    img = iso.render((1400, 1000), (700, 380), (0, 0, 0, 0))
    bg = Image.new("RGBA", img.size)
    for y in range(img.height):                        # sky gradient
        t = y / img.height
        ImageDraw.Draw(bg).line([(0, y), (img.width, y)], fill=(int(120 + 70 * t), int(180 + 40 * t), int(240 - 10 * t), 255))
    bg.alpha_composite(img)
    return bg


def text_ar(d, x, y, s, font, fill):
    for ch in s:                                        # one glyph at a time, left to right
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch)


def logo():
    S = 400
    im = Image.new("RGBA", (S, S), (24, 30, 44, 255))
    d = ImageDraw.Draw(im)
    for y in range(S):
        t = y / S
        d.line([(0, y), (S, y)], fill=(int(30 + 30 * t), int(36 + 50 * t), int(60 + 40 * t), 255))
    # a grass block in the middle
    iso = Iso(70)
    iso.add(0, 0, 0, tex("grass_carried"), tex("grass_side_carried"), tex("grass_side_carried"))
    block = iso.render((S, S), (S // 2, 150), (0, 0, 0, 0))
    im.alpha_composite(block)
    # a heartbeat line across it
    pts = [(20, 250), (120, 250), (150, 200), (185, 300), (215, 170), (245, 250), (380, 250)]
    d.line(pts, fill=(255, 255, 255, 255), width=12, joint="curve")
    d.line(pts, fill=(255, 92, 92, 255), width=6, joint="curve")
    f = ImageFont.truetype(FONT, 64)
    d.text((S // 2, 318), "NABD", font=f, fill=(255, 255, 255, 255), anchor="mm")
    return im


def catalogue(names, cols=10, cell=96, title=""):
    rows = (len(names) + cols - 1) // cols
    im = Image.new("RGBA", (cols * (cell + 12) + 12, rows * (cell + 12) + 70), (26, 30, 38, 255))
    d = ImageDraw.Draw(im)
    d.text((14, 18), title, font=ImageFont.truetype(FONT, 28), fill=(255, 255, 255, 255))
    for i, n in enumerate(names):
        t = tex(n).resize((cell, cell), Image.NEAREST)
        x, y = 12 + (i % cols) * (cell + 12), 64 + (i // cols) * (cell + 12)
        im.alpha_composite(t, (x, y))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    dio = diorama()
    dio.save(os.path.join(OUT, "01_diorama.png"))
    lg = logo()
    lg.save(os.path.join(OUT, "logo_400.png"))
    # banner 1920x500
    ban = Image.new("RGBA", (1920, 500), (0, 0, 0, 255))
    crop = dio.resize((1400 * 1920 // 1400, 1000 * 1920 // 1400)).crop((0, 300, 1920, 800))
    ban.alpha_composite(crop)
    d = ImageDraw.Draw(ban)
    d.rectangle([0, 0, 760, 500], fill=(18, 22, 32, 200))
    d.text((60, 120), "NABD", font=ImageFont.truetype(FONT, 120), fill=(255, 255, 255, 255))
    text_ar(d, 490, 120, AR_NABD, ImageFont.truetype(FONT, 110), (255, 120, 120, 255))
    d.text((64, 280), "Bright cartoon textures, new animations,", font=ImageFont.truetype(FONT_R, 34), fill=(230, 236, 245, 255))
    d.text((64, 326), "clear nights - for Minecraft Bedrock", font=ImageFont.truetype(FONT_R, 34), fill=(230, 236, 245, 255))
    ban.save(os.path.join(OUT, "banner_1920x500.png"))
    ores = ["coal_ore", "iron_ore", "copper_ore", "gold_ore", "redstone_ore", "lapis_ore", "diamond_ore", "emerald_ore",
            "deepslate/deepslate_coal_ore", "deepslate/deepslate_iron_ore", "deepslate/deepslate_copper_ore",
            "deepslate/deepslate_gold_ore", "deepslate/deepslate_redstone_ore", "deepslate/deepslate_lapis_ore",
            "deepslate/deepslate_diamond_ore", "deepslate/deepslate_emerald_ore"]
    catalogue(ores, cols=8, cell=128, title="Ores - stone and deepslate").save(os.path.join(OUT, "02_ores.png"))
    terrain = ["grass_carried", "dirt", "coarse_dirt", "stone", "cobblestone", "gravel", "sand", "red_sand",
               "sandstone_normal", "red_sandstone_normal", "stone_granite", "stone_diorite", "stone_andesite",
               "calcite", "tuff", "deepslate/deepslate", "clay", "mud", "snow", "obsidian"]
    catalogue(terrain, cols=10, cell=110, title="Terrain").save(os.path.join(OUT, "03_terrain.png"))
    build = ["stonebrick", "stonebrick_mossy", "brick", "quartz_block_side", "quartz_bricks", "polished_blackstone_bricks",
             "nether_brick", "red_nether_brick", "planks_oak", "planks_spruce", "planks_birch", "planks_jungle",
             "planks_acacia", "planks_big_oak", "cherry_planks", "mangrove_planks", "concrete_red", "concrete_light_blue",
             "concrete_lime", "concrete_yellow", "wool_colored_white", "wool_colored_red", "wool_colored_blue",
             "wool_colored_lime"]
    catalogue(build, cols=8, cell=110, title="Building blocks").save(os.path.join(OUT, "04_building.png"))
    badl = ["hardened_clay_stained_orange", "hardened_clay", "hardened_clay_stained_yellow", "hardened_clay_stained_white",
            "hardened_clay_stained_brown", "hardened_clay_stained_silver", "hardened_clay_stained_red", "red_sandstone_carved"]
    catalogue(badl, cols=8, cell=128, title="Badlands").save(os.path.join(OUT, "05_badlands.png"))
    nether = ["netherrack", "soul_sand", "soul_soil", "blackstone", "basalt_side", "basalt_top", "crying_obsidian",
              "nether_brick", "end_stone", "amethyst_block"]
    catalogue(nether, cols=10, cell=110, title="Nether and End").save(os.path.join(OUT, "06_nether_end.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
