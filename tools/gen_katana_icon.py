"""يرسم أيقونة كاتانا الهاوية (32x32) على شكل الصورة المرجعية: نصل أسود بنفسجي منحني،
حارس بجناحين، جوهرة ذهبية، قبضة ملفوفة، ونهاية زرقاء. يشغل من جذر المشروع:
    python3 tools/gen_katana_icon.py
"""
import math
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "AnimePowers/RP/textures/items/sh_katana.png")
N = 32

OUTLINE = (8, 8, 22, 255)
BLADE_SPINE = (22, 24, 58)
BLADE_MID = (58, 52, 120)
BLADE_EDGE = (126, 110, 205)
BLADE_SHINE = (190, 180, 245)
GUARD = (30, 36, 78)
GUARD_HI = (66, 78, 140)
GOLD = (245, 205, 70)
GOLD_HI = (255, 240, 150)
WRAP_A = (58, 60, 70)
WRAP_B = (30, 32, 40)
POMMEL = (36, 60, 130)
POMMEL_HI = (80, 120, 205)


def build():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = img.load()
    # محور السيف: من القاع اليسار (x0,y0) إلى أعلى اليمين
    x0, y0 = 3.2, 28.6
    ux, uy = 0.7071, -0.7071  # الاتجاه على طول السيف
    vx, vy = 0.7071, 0.7071   # العرض (يمين-أسفل)
    blade_len = 24.5
    blade_start = 11.2

    def shape(a, b):
        """يرجع لون البكسل أو None. a: على طول المحور، b: عرضياً."""
        # نهاية القبضة
        if -1.6 <= a < 1.2 and abs(b) <= 1.7:
            return POMMEL_HI if b < -0.4 else POMMEL
        # القبضة الملفوفة
        if 1.2 <= a < 8.2:
            w = 1.55
            if abs(b) <= w:
                stripe = int((a + 40) * 1.0) % 3 == 0
                c = WRAP_A if stripe else WRAP_B
                if b < -0.5:
                    c = tuple(min(255, int(v * 1.35)) for v in c)
                return c
            return None
        # الحارس: جناحان للأعلى والأسفل
        if 8.2 <= a < 11.4:
            reach = 5.0 - abs(a - 9.7) * 2.1
            if abs(b) <= reach:
                c = GUARD_HI if (b < -1 and a < 10.2) else GUARD
                if abs(b) < 1.5 and 9.0 <= a <= 10.6:
                    return GOLD_HI if (b < -0.2 and a < 9.9) else GOLD
                return c
            return None
        # النصل
        if blade_start <= a <= blade_start + blade_len:
            t = (a - blade_start) / blade_len
            curve = 2.2 * (t ** 2)
            half = 1.2 * (1 - t) ** 0.45 + 0.3
            if t > 0.93:
                half = max(0.25, (1 - t) * 8)
            bb = b + curve
            if abs(bb) <= half:
                f = (bb + half) / (2 * half)  # 0 = ظهر النصل ، 1 = حافة الحد
                if f > 0.86:
                    return BLADE_SHINE if (int(a) % 4 != 0) else BLADE_EDGE
                if f > 0.66:
                    return BLADE_EDGE if (int(a) % 3 != 0) else BLADE_MID
                if f > 0.38:
                    return BLADE_MID
                return BLADE_SPINE
            return None
        return None

    cols = {}
    for y in range(N):
        for x in range(N):
            # نأخذ 4 عينات داخل البكسل لتنعيم الحواف مع بقاء الشكل بكسلياً
            hits = []
            for dx in (0.25, 0.75):
                for dy in (0.25, 0.75):
                    rx, ry = x + dx - x0, y + dy - y0
                    a = rx * ux + ry * uy
                    b = rx * vx + ry * vy
                    c = shape(a, b)
                    if c:
                        hits.append(c)
            if len(hits) >= 2:
                cols[(x, y)] = max(set(hits), key=hits.count)

    for (x, y), c in cols.items():
        px[x, y] = (*c, 255)
    # حد خارجي داكن
    for (x, y) in list(cols):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < N and 0 <= ny < N and (nx, ny) not in cols and px[nx, ny][3] == 0:
                px[nx, ny] = OUTLINE
    return img


if __name__ == "__main__":
    im = build()
    im.save(OUT)
    prev = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "katana_preview.png")
    bg = Image.new("RGBA", (N, N), (120, 120, 126, 255))
    bg.alpha_composite(im)
    bg.resize((N * 12, N * 12), Image.NEAREST).save(prev)
    print("saved", OUT, "preview", prev)
