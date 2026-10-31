"""يرسم أيقونات 2D (32x32) لـ: مخالب الظل، رمح الغروب، ساطور الجمر — بنفس جودة الكاتانا.
الرسم بتنعيم 2x2 مع حد خارجي مقفول بالكامل (8 اتجاهات) حتى ما يبقى بكسل ناقص بالحدود.
التشغيل: python3 tools/gen_icons2d.py
"""
import math
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "AnimePowers/RP/textures/items")
N = 32
OUTLINE = (8, 8, 22)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


class Frame:
    """إطار موضعي: نقطة بداية + اتجاه (بالدرجات، 0 = يمين، 90 = أعلى)."""
    def __init__(self, x0, y0, deg):
        a = math.radians(deg)
        self.x0, self.y0 = x0, y0
        self.ux, self.uy = math.cos(a), -math.sin(a)       # طول (للأعلى = y سالب)
        self.vx, self.vy = -self.uy * -1, 0                 # placeholder (يُحسب تحت)
        self.vx, self.vy = math.sin(a), math.cos(a)         # عرض (يمين السهم)

    def to_local(self, x, y):
        rx, ry = x - self.x0, y - self.y0
        return rx * self.ux + ry * self.uy, rx * self.vx + ry * self.vy


def render(parts, name, preview_dir=None):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = img.load()
    cols = {}
    for y in range(N):
        for x in range(N):
            hits = []
            for dx in (0.25, 0.75):
                for dy in (0.25, 0.75):
                    c = None
                    for part in parts:  # الرسام: اللاحق يغطي السابق
                        r = part(x + dx, y + dy)
                        if r is not None:
                            c = r
                    if c is not None:
                        hits.append(tuple(int(v) for v in c))
            if len(hits) >= 2:
                cols[(x, y)] = max(set(hits), key=hits.count)
    for (x, y), c in cols.items():
        px[x, y] = (*c, 255)
    for (x, y) in list(cols):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx or dy) and 0 <= nx < N and 0 <= ny < N and (nx, ny) not in cols and px[nx, ny][3] == 0:
                    px[nx, ny] = (*OUTLINE, 255)
    img.save(os.path.join(OUTDIR, f"sh_{name}.png"))
    return img


def blade_part(fr, a0, length, w0, w1, c_back, c_edge, c_tip, edge_split=0.5, curve=0.0):
    """نصل متناقص العرض داخل إطار."""
    def f(x, y):
        a, b = fr.to_local(x, y)
        if a < a0 or a > a0 + length:
            return None
        t = (a - a0) / length
        half = (w0 + (w1 - w0) * t) / 2
        bb = b - curve * t * t
        if abs(bb) > half:
            return None
        f_ = (bb + half) / (2 * half)
        if t > 0.9:
            return c_tip
        if f_ > 1 - edge_split * 0.35:
            return lerp(c_edge, c_tip, t)
        if f_ > 1 - edge_split:
            return c_edge
        return lerp(c_back, c_edge, 0.25 * t)
    return f


def rect_part(fr, a0, a1, b0, b1, col, col2=None):
    def f(x, y):
        a, b = fr.to_local(x, y)
        if a0 <= a <= a1 and b0 <= b <= b1:
            if col2 is not None and b < b0 + (b1 - b0) * 0.35:
                return col2
            return col
        return None
    return f


# ───────────────────────── مخالب الظل ─────────────────────────
def claws():
    BLK, BLK_HI = (30, 24, 48), (70, 58, 104)
    LEATH, LEATH_HI = (88, 62, 64), (130, 96, 96)
    PUR, PUR_HI = (92, 58, 176), (160, 120, 246)
    SIL = (176, 184, 208)
    WHITE, GLOW = (250, 244, 255), (214, 184, 255)
    fr = Frame(4.0, 28.0, 45)            # محور الكاتار
    parts = []
    # شرائط المعصم
    parts.append(rect_part(fr, -2.0, 4.0, -1.0, 0.6, PUR))
    parts.append(rect_part(fr, -1.0, 3.0, 0.8, 2.2, shade(PUR, 0.7)))
    # قبضة جلد
    parts.append(rect_part(fr, 2.0, 9.0, -2.1, 2.1, LEATH, LEATH_HI))
    # لوحة المفاصل الواسعة بحافة فضية وجواهر
    parts.append(rect_part(fr, 8.5, 12.5, -5.8, 5.8, BLK, BLK_HI))
    parts.append(rect_part(fr, 12.0, 13.4, -5.8, 5.8, SIL, WHITE))
    for b in (-3.6, 0.0, 3.6):
        parts.append(rect_part(fr, 9.4, 11.4, b - 0.9, b + 0.9, PUR_HI, GLOW))
    # ثلاث شفرات: وسطى أطول، جانبيتان تنفرجان
    for bo, deg, ln in ((-4.4, 68, 14.5), (0.0, 45, 18.5), (4.4, 22, 14.5)):
        a_dir = math.radians(45)
        # نقطة البداية على حافة اللوحة
        sx = fr.x0 + fr.ux * 13.0 + fr.vx * bo
        sy = fr.y0 + fr.uy * 13.0 + fr.vy * bo
        bf = Frame(sx, sy, deg)
        parts.append(blade_part(bf, 0, ln, 2.5, 0.0, BLK, PUR_HI, WHITE, edge_split=0.55))
    return render(parts, "claws")


# ───────────────────────── رمح الغروب ─────────────────────────
def spear():
    WOOD_A, WOOD_B = (118, 64, 44), (76, 40, 30)
    RED, RED_HI, RED_LO = (200, 52, 44), (255, 124, 76), (122, 28, 30)
    GOLD, GOLD_HI = (236, 188, 70), (255, 240, 160)
    STEEL, STEEL_HI = (206, 212, 226), (252, 252, 255)
    fr = Frame(2.5, 29.5, 45)
    parts = []
    # عمود الرمح (لونين بالعرض)
    parts.append(rect_part(fr, 0, 24.5, -0.9, 0.9, WOOD_A, WOOD_B))
    parts.append(rect_part(fr, -1.4, 0.4, -1.3, 1.3, GOLD, GOLD_HI))          # نهاية ذهبية
    parts.append(rect_part(fr, 6.0, 11.0, -1.4, 1.4, RED, RED_HI))            # لف قماش
    parts.append(rect_part(fr, 12.0, 12.8, -1.4, 1.4, GOLD, GOLD_HI))
    # طوق ذهبي + هلالان جانبيان
    parts.append(rect_part(fr, 22.5, 24.6, -2.0, 2.0, GOLD, GOLD_HI))
    parts.append(rect_part(fr, 23.2, 25.8, -3.4, -2.0, GOLD))
    parts.append(rect_part(fr, 23.2, 25.8, 2.0, 3.4, GOLD))
    # شراشيب حمراء متدلية
    parts.append(rect_part(fr, 19.2, 22.6, -2.6, -1.7, RED))
    parts.append(rect_part(fr, 19.2, 22.6, 1.7, 2.6, RED))
    parts.append(rect_part(fr, 17.4, 19.4, -2.9, -2.1, RED_LO))
    parts.append(rect_part(fr, 17.4, 19.4, 2.1, 2.9, RED_LO))
    # رأس ورقي: عرض يرتفع ثم يضيق، مع مجرى أحمر
    def head(x, y):
        a, b = fr.to_local(x, y)
        a0, ln = 24.4, 8.4
        if a < a0 or a > a0 + ln:
            return None
        t = (a - a0) / ln
        half = 1.9 * math.sin(math.pi * min(1.0, t * 0.8 + 0.12)) ** 0.9 * (1 - t ** 3) + 0.2
        if abs(b) > half:
            return None
        if abs(b) < 0.45 and t < 0.8:
            return RED if t < 0.5 else RED_HI
        return STEEL_HI if b < 0 else STEEL
    parts.append(head)
    return render(parts, "spear")


# ───────────────────────── ساطور الجمر ─────────────────────────
def cleaver():
    IRON, IRON_HI, IRON_LO = (70, 68, 78), (128, 124, 138), (34, 32, 42)
    EMB, EMB_HI, EMB_W = (255, 108, 26), (255, 178, 58), (255, 236, 150)
    WOOD_A, WOOD_B = (122, 78, 46), (78, 48, 28)
    fr = Frame(3.0, 29.0, 45)
    parts = []
    parts.append(rect_part(fr, -1.5, 0.8, -2.0, 2.0, IRON, IRON_HI))              # حلقة النهاية
    parts.append(rect_part(fr, 0.6, 11.0, -1.6, 1.6, WOOD_A, WOOD_B))              # قبضة
    for a in (3.4, 7.2):
        parts.append(rect_part(fr, a, a + 0.9, -1.7, 1.7, IRON, IRON_HI))
    parts.append(rect_part(fr, 10.6, 12.6, -4.0, 4.0, IRON_LO, IRON))              # حارس
    parts.append(rect_part(fr, 11.0, 12.2, -0.9, 0.9, EMB_HI, EMB_W))              # جوهرة
    # الشفرة العريضة: ظهر داكن (b سالب) + حد متوهج (b موجب)، وقطع مائل بالأعلى
    def blade(x, y):
        a, b = fr.to_local(x, y)
        if a < 12.6 or b < -7.2 or b > 5.2:
            return None
        top = 28.6 - 0.22 * (b + 7.2) * 1.0 - (0.8 if b > 3.0 else 0)  # قطع مائل
        if a > top:
            return None
        # حد الجمر
        if b > 3.0:
            return EMB_HI if b > 4.2 else EMB
        if b < -5.2:
            return IRON_LO if b < -6.2 else IRON
        t = (a - 12.6) / 16.0
        base = lerp(IRON, IRON_HI, 0.15 + 0.35 * (b + 5.2) / 8.2)
        return base
    parts.append(blade)
    # شقوق جمر زجزاج داخل الشفرة
    def cracks(x, y):
        a, b = fr.to_local(x, y)
        if not (14.0 < a < 26.5) or not (-4.6 < b < 2.6):
            return None
        zz = -1.6 + 1.5 * math.sin((a - 14.0) * 0.95)
        if abs(b - zz) < 0.45:
            return EMB_HI if int(a * 1.7) % 2 else EMB
        return None
    parts.append(cracks)
    # مسامير على الظهر
    for a in (15.0, 20.0, 25.0):
        parts.append(rect_part(fr, a, a + 1.0, -6.4, -5.4, IRON_HI))
    return render(parts, "cleaver")


# ───────────────────────── لفائف الخبرة (لفافة ورق ملفوفة بشريط وختم) ─────────────────────────
def scroll(name, big):
    PAPER_HI, PAPER, PAPER_LO, PAPER_DK = (250, 238, 196), (232, 208, 150), (186, 154, 100), (132, 102, 62)
    ROD, ROD_HI = ((170, 126, 52), (240, 200, 96)) if big else ((120, 78, 46), (176, 124, 76))
    RIB, RIB_HI = ((196, 40, 52), (255, 110, 100)) if big else ((46, 150, 82), (130, 230, 150))
    SEAL, SEAL_HI = ((255, 150, 40), (255, 226, 130)) if big else ((236, 196, 70), (255, 244, 170))
    half = 4.4 if big else 3.7
    L0, L1 = 3.5, 22.5 if big else 21.5
    fr = Frame(3.0 if big else 4.0, 29.0 if big else 28.0, 45)
    parts = []
    # أعواد الطرفين
    parts.append(rect_part(fr, 0.2, L0 + 0.5, -1.4, 1.4, ROD, ROD_HI))
    parts.append(rect_part(fr, -1.0, 0.8, -2.0, 2.0, ROD_HI, ROD_HI))
    parts.append(rect_part(fr, L1 - 0.5, L1 + 3.0, -1.4, 1.4, ROD, ROD_HI))
    parts.append(rect_part(fr, L1 + 2.2, L1 + 4.0, -2.0, 2.0, ROD_HI, ROD_HI))
    # جسم الورق (أسطوانة): تدرج بالعرض
    def body(x, y):
        a, b = fr.to_local(x, y)
        if a < L0 or a > L1 or abs(b) > half:
            return None
        t = (b + half) / (2 * half)       # 0 فوق-يسار (فاتح) .. 1 تحت-يمين (داكن)
        if t < 0.18: return PAPER_HI
        if t < 0.55: return PAPER
        if t < 0.85: return PAPER_LO
        return PAPER_DK
    parts.append(body)
    # نهاية اللف الحلزوني على الطرفين (حلقات)
    def cap(a_end, direction):
        def f(x, y):
            a, b = fr.to_local(x, y)
            d = (a - a_end) * direction
            if d < -0.1 or d > 1.8: return None
            r = math.sqrt(max(0.0, 1 - (b / half) ** 2)) * 1.8
            if d > r or abs(b) > half: return None
            ring = int((math.hypot(b / half, d / 1.8) * 5)) % 2
            return PAPER_DK if ring else PAPER_LO
        return f
    parts.append(cap(L0, -1))
    parts.append(cap(L1, +1))
    # الشريط بالنص (يلف الورق) + عقدة
    mid = 12.6 if big else 12.0
    parts.append(rect_part(fr, mid - 1.5, mid + 1.5, -half - 0.5, half + 0.5, RIB, RIB_HI))
    if big:
        parts.append(rect_part(fr, 7.4, 8.6, -half - 0.3, half + 0.3, RIB, RIB_HI))
        parts.append(rect_part(fr, 16.8, 18.0, -half - 0.3, half + 0.3, RIB, RIB_HI))
    # ختم شمع مع نجمة/نقطة
    def seal(x, y):
        a, b = fr.to_local(x, y)
        r = math.hypot(a - mid, b)
        if r > 2.4: return None
        if r < 0.9: return SEAL_HI
        if (a - mid) + b * 0.0 < -0.6 and r > 1.4: return SEAL_HI
        return SEAL
    parts.append(seal)
    return render(parts, name)


if __name__ == "__main__":
    ims = [claws(), spear(), cleaver(), scroll("scroll_small", False), scroll("scroll_big", True)]
    prev = os.environ.get("PREVIEW_DIR", "/tmp")
    S = 14
    sheet = Image.new("RGBA", (len(ims) * (N * S + 10), N * S + 10), (118, 118, 126, 255))
    for i, im in enumerate(ims):
        sheet.alpha_composite(im.resize((N * S, N * S), Image.NEAREST), (i * (N * S + 10) + 5, 5))
    sheet.save(os.path.join(prev, "icons2d_new.png"))
    print("ok")
