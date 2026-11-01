"""أيقونات الكتب (كتاب التطور وكتاب الوحوش) 32x32: كتاب بمنظور خفيف، صفحات ظاهرة، كعب بحلقات ذهب، زوايا معدن، شعار متوهج وشريطة.
التشغيل: python3 tools/gen_book_icons.py [مجلد_معاينة]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "AnimePowers", "RP", "textures", "items")


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def book(cover, cover_dark, emblem):
    W = 32
    px = {}

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < W:
            px[(x, y)] = c

    GOLD, GOLD_HI, GOLD_LO = (236, 186, 70), (255, 236, 150), (150, 98, 30)
    PAGE, PAGE_LO = (244, 234, 206), (196, 180, 146)
    # الغلاف الخلفي + الصفحات (تطلع يمين وتحت = عمق)
    for y in range(6, 28):
        put(27, y, PAGE if y % 2 else PAGE_LO)
        put(26, y, PAGE)
        put(28, y, cover_dark)
    for x in range(9, 29):
        put(x, 26, PAGE if x % 2 else PAGE_LO)
        put(x, 27, PAGE)
        put(x, 28, cover_dark)
    # الغلاف الأمامي بتدرج
    for y in range(4, 26):
        for x in range(7, 26):
            t = ((x - 7) / 18 + (y - 4) / 21) / 2
            put(x, y, mix(mix(cover, (255, 255, 255), 0.12), cover_dark, t * 0.9))
    # إطار داخلي فاتح
    for x in range(9, 24):
        put(x, 6, mix(cover, GOLD, 0.45)); put(x, 23, mix(cover_dark, GOLD, 0.35))
    for y in range(6, 24):
        put(9, y, mix(cover, GOLD, 0.45)); put(23, y, mix(cover_dark, GOLD, 0.35))
    # الكعب
    for y in range(4, 28):
        for x in range(4, 7):
            put(x, y, mix(cover_dark, (0, 0, 0), 0.25 if x == 4 else 0.05))
        put(7, y, mix(cover_dark, (0, 0, 0), 0.4))
    for y in (7, 14, 21):
        for x in range(4, 7):
            put(x, y, GOLD if x == 5 else GOLD_LO)
        put(5, y - 1, GOLD_HI)
    # زوايا معدن ذهبية
    for (cx, cy, sx, sy) in ((25, 4, -1, 1), (25, 25, -1, -1)):
        for i in range(3):
            for j in range(3 - i):
                put(cx + sx * i, cy + sy * j, GOLD if (i + j) else GOLD_HI)
    # الشعار
    emblem(put)
    # الشريطة
    for y in range(26, 31):
        put(20, y, (200, 40, 50)); put(21, y, (150, 24, 34))
    put(20, 31, (150, 24, 34))
    # حدود غامقة
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    for (x, y), c in px.items():
        img.putpixel((x, y), (*c, 255))
    edge = (24, 14, 30)
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < W and 0 <= q[1] < W and q not in px:
                img.putpixel(q, (*edge, 255))
    return img


def evo_emblem(put):
    """نجمة رباعية بقلب جوهرة متوهجة ونقاط تدور (رمز التطور)."""
    cx, cy = 16, 14
    GOLD, GOLD_HI = (240, 196, 80), (255, 240, 170)
    GEM, GEM_HI, GEM_W = (70, 200, 255), (160, 235, 255), (245, 255, 255)
    for k in range(1, 7):
        w = 1 if k > 2 else 2
        for s in range(-w + 1, w):
            put(cx + k, cy + s, GOLD); put(cx - k, cy + s, GOLD); put(cx + s, cy + k, GOLD); put(cx + s, cy - k, GOLD)
    for k in (1, 2):
        put(cx + k, cy - k, GOLD_HI); put(cx - k, cy + k, GOLD); put(cx + k, cy + k, GOLD); put(cx - k, cy - k, GOLD_HI)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            put(cx + dx, cy + dy, GEM if abs(dx) + abs(dy) == 2 else GEM_HI)
    put(cx, cy, GEM_W); put(cx - 1, cy - 1, GEM_W)
    for (x, y) in ((cx + 5, cy - 5), (cx - 5, cy + 5), (cx + 5, cy + 5), (cx - 5, cy - 5)):
        put(x, y, GEM_HI)
    for x in range(12, 21):
        put(x, 21, GOLD if x % 2 else (200, 150, 60))


def mon_emblem(put):
    """عين وحش بحدقة شق، وثلاث خدوش فوقها وجوهرة حمراء."""
    cx, cy = 16, 14
    SCL, IRIS, IRIS_HI, PUP = (250, 236, 200), (190, 60, 220), (240, 150, 255), (20, 6, 20)
    rows = {-3: 2, -2: 4, -1: 5, 0: 6, 1: 5, 2: 4, 3: 2}
    for dy, w in rows.items():
        for dx in range(-w, w + 1):
            put(cx + dx, cy + dy, SCL)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if abs(dx) + abs(dy) <= 3:
                put(cx + dx, cy + dy, IRIS_HI if dy < 0 and dx < 0 else IRIS)
    for dy in range(-3, 4):
        put(cx, cy + dy, PUP)
    put(cx - 1, cy - 1, (255, 255, 255))
    for dx in range(-6, 7):
        if abs(dx) > 2:
            put(cx + dx, cy - rows.get(-3, 2) - (1 if abs(dx) < 5 else 0) - 1, (60, 20, 30))
    CLAW = (230, 70, 70)
    for i, x0 in enumerate((12, 16, 20)):
        for k in range(4):
            put(x0 - 1 + k // 2, 18 + k, CLAW if k < 3 else (140, 30, 40))
    put(16, 7, (255, 70, 80)); put(15, 8, (200, 30, 50)); put(17, 8, (200, 30, 50)); put(16, 8, (255, 140, 150)); put(16, 9, (150, 20, 40))


def main():
    evo = book((120, 64, 200), (52, 22, 96), evo_emblem)
    mon = book((150, 46, 52), (60, 16, 24), mon_emblem)
    evo.save(os.path.join(OUT, "sh_book.png"))
    mon.save(os.path.join(OUT, "sh_monster_book.png"))
    if len(sys.argv) > 1:
        s = Image.new("RGBA", (560, 260), (60, 60, 70, 255))
        s.paste(evo.resize((256, 256), Image.NEAREST), (0, 0), evo.resize((256, 256), Image.NEAREST))
        s.paste(mon.resize((256, 256), Image.NEAREST), (290, 0), mon.resize((256, 256), Image.NEAREST))
        s.save(os.path.join(sys.argv[1], "books_new.png"))
    print("books ok")


if __name__ == "__main__":
    main()
