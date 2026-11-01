"""أيقونات 32x32 (سيف الظل، خنجر الفجر، مخالب الظل). سيف الظل: سيف طويل أزرق مستقيم (قطري)، حارس فضي مجنح بجوهرة، خط نور بالنص، وشرائط ريح.
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


def _save(px, out):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for (x, y), c in px.items():
        img.putpixel((x, y), (*c, 255))
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < 32 and 0 <= q[1] < 32 and q not in px:
                img.putpixel(q, (*EDGE, 255))
    img.save(out)
    print("icon ok:", out)


def dagger_icon():
    """خنجر قصير مستقيم بحدين (قطري)، حارس ذهبي صغير، قبضة جلد قصيرة، ورأس قبضة بجوهرة الفجر."""
    ST, ST_HI, ST_LO = (226, 222, 210), (255, 252, 240), (160, 156, 146)
    GOLD, GOLD_HI = (226, 178, 62), (255, 232, 140)
    LA, LB = (118, 76, 44), (78, 48, 28)
    SUN = (255, 98, 52)
    px = {}
    put = lambda x, y, c: px.__setitem__((x, y), c) if 0 <= x < 32 and 0 <= y < 32 else None
    for i in range(11):                         # النصل من (13,18) إلى (23,8)
        x, y = 13 + i, 18 - i
        put(x, y, ST_LO if i < 8 else ST)
        put(x - 1, y - 1 if i < 9 else y, ST_HI)
        put(x + 1, y + 1, ST)
    put(24, 7, ST_HI); put(25, 6, ST_HI)
    for k in range(-3, 4):                      # حارس
        put(11 + k, 19 + k, GOLD if abs(k) < 3 else GOLD_HI)
    put(11, 19, SUN)
    for i in range(4):                          # قبضة
        put(10 - i, 21 + i, LA if i % 2 else LB); put(9 - i, 21 + i, LB); put(10 - i, 22 + i, LB)
    put(6, 25, GOLD); put(5, 26, GOLD_HI); put(6, 26, SUN); put(5, 25, GOLD)
    _save(px, os.path.join(ROOT, "AnimePowers", "RP", "textures", "items", "sh_dagger.png"))


def claws_icon():
    """واقي ساعد بأحزمة (أسفل يسار) وثلاث شفرات منحنية تطلع من المفاصل لفوق يمين وتنحني بالطرف."""
    LE, LE_HI = (58, 44, 52), (90, 70, 80)
    STRAP, PLATE, GEM = (110, 66, 160), (60, 54, 86), (180, 120, 255)
    B, B_HI, W = (90, 70, 150), (160, 130, 240), (240, 232, 255)
    px = {}
    put = lambda x, y, c: px.__setitem__((x, y), c) if 0 <= x < 32 and 0 <= y < 32 else None
    for i in range(9):                          # الساعد قطري (مملي بدون فراغات)
        for j in range(-2, 3):
            c = STRAP if i in (2, 5) else (LE_HI if j == 0 else LE)
            put(4 + i + j, 27 - i + j, c); put(5 + i + j, 27 - i + j, c)
    for j in range(-3, 4):                      # صفيحة المفاصل
        put(13 + j, 18 + j, PLATE); put(14 + j, 18 + j, PLATE)
    for j in (-2, 0, 2):
        put(13 + j, 18 + j, GEM)
    for j, L in ((-2, 9), (0, 11), (2, 9)):     # ثلاث شفرات تنحني
        for i in range(L):
            bend = (i * i) // 34
            x, y = 15 + j + i, 17 + j - i + bend
            put(x, y, B if i < L - 3 else B_HI)
            put(x, y - 1, B_HI if i % 3 else W)
        put(15 + j + L, 17 + j - L + ((L * L) // 34), W)
    _save(px, os.path.join(ROOT, "AnimePowers", "RP", "textures", "items", "sh_claws.png"))


def silver_icon():
    """سيف فضي طويل قطري بحارس بأطراف ذهبية شاحبة، قبضة بيضاء، وبريق أبيض حواليه."""
    S, S_HI, S_LO, WH = (196, 204, 220), (244, 248, 255), (130, 138, 160), (255, 255, 255)
    PG, GRIP_A, GRIP_B = (214, 196, 140), (232, 228, 220), (170, 164, 156)
    px = {}
    put = lambda x, y, c: px.__setitem__((x, y), c) if 0 <= x < 32 and 0 <= y < 32 else None
    for i in range(17):
        x, y = 11 + i, 20 - i
        put(x, y, WH if i % 4 == 0 else S_HI)
        put(x - 1, y, S_LO); put(x, y + 1, S); put(x + 1, y + 1, S_HI if i > 13 else S)
    put(28, 3, WH); put(29, 2, WH)
    for k in range(-4, 5):
        put(9 + k, 21 + k, PG if abs(k) >= 3 else S)
    put(9, 21, (220, 240, 255))
    for i in range(6):
        put(8 - i, 23 + i, GRIP_A if i % 2 else GRIP_B); put(7 - i, 23 + i, GRIP_B)
    put(1, 30, S); put(2, 29, S_HI); put(1, 29, PG)
    for (x, y) in ((18, 7), (25, 13), (14, 11)):
        put(x, y, WH); put(x - 1, y, WH); put(x + 1, y, WH); put(x, y - 1, WH); put(x, y + 1, WH)
    _save(px, os.path.join(ROOT, "AnimePowers", "RP", "textures", "items", "sh_silver.png"))


if __name__ == "__main__":
    main()
    dagger_icon()
    claws_icon()
    silver_icon()
