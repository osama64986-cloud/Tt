"""أيقونة سيف الظل الجديدة 32x32: سيف طويل أزرق مستقيم (قطري)، حارس فضي مجنح بجوهرة، خط نور بالنص، وشرائط ريح.
التشغيل: python3 tools/gen_blade_icon.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "AnimePowers", "RP", "textures", "items", "sh_shadow.png")
STEEL, STEEL_HI, STEEL_LO = (70, 110, 190), (150, 196, 255), (34, 52, 110)
CORE, CORE_W = (90, 220, 255), (235, 252, 255)
NAVY, NAVY_HI = (22, 30, 70), (58, 72, 130)
SILV, SILV_HI = (184, 196, 220), (240, 245, 255)
GEM = (40, 140, 255)
WIND = (150, 220, 255)
EDGE = (14, 16, 34)


def main():
    px = {}

    def put(x, y, c):
        if 0 <= x < 32 and 0 <= y < 32:
            px[(x, y)] = c
    # النصل: من (11,20) إلى (28,3) قطري، عرضه 3 بكسل (ظهر، نور، حد)
    for i in range(18):
        x, y = 11 + i, 20 - i
        put(x, y, CORE if i % 4 else CORE_W)
        put(x - 1, y, STEEL_LO if i < 14 else STEEL)
        put(x, y + 1, STEEL_HI)
        put(x + 1, y + 1, STEEL if i < 16 else STEEL_HI)
        put(x - 1, y - 1, STEEL)
    put(29, 2, CORE_W); put(28, 2, STEEL_HI); put(29, 3, STEEL_HI)
    # الحارس المجنح (عمودي على النصل)
    for k in range(-4, 5):
        put(9 + k, 21 + k, SILV if abs(k) < 3 else SILV_HI)
        put(10 + k, 21 + k, SILV)
    put(4, 15, SILV_HI); put(15, 26, SILV_HI)
    put(9, 21, GEM); put(10, 21, GEM); put(9, 22, GEM)
    # القبضة الملفوفة + الحلق
    for i in range(6):
        put(8 - i, 23 + i, NAVY if i % 2 else NAVY_HI)
        put(7 - i, 23 + i, NAVY)
        put(8 - i, 24 + i, NAVY)
    put(1, 30, SILV); put(2, 29, SILV_HI); put(1, 29, GEM)
    # شرائط ريح حول النصل
    for (x, y) in ((16, 10), (17, 10), (18, 11), (22, 6), (23, 6), (24, 7), (13, 15), (14, 14), (25, 11), (26, 10), (20, 15), (21, 14)):
        if (x, y) not in px:
            put(x, y, WIND)
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for (x, y), c in px.items():
        img.putpixel((x, y), (*c, 255))
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < 32 and 0 <= q[1] < 32 and q not in px:
                img.putpixel(q, (*EDGE, 255))
    img.save(OUT)
    print("icon ok:", OUT)


if __name__ == "__main__":
    main()
