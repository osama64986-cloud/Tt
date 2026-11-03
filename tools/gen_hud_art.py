"""رسومات الـHUD: ورقة رموز (glyph_E5) تنحط داخل نص الأكشن بار + إطار مزخرف للوحة + إطار لمجسم اللاعب.
الرموز: قلوب، أشرطة مرسومة (رتبة/خبرة/قدرة)، شارات الرتب السبع، شعارات القدرات التسع، أيقونات حالة المهارة،
الصدع (أيقونة، موجة مضوية/مطفية، جمجمة الزعيم، أرض فاسدة) وعدسة الأطلس. الرمز رقم i = الحرف U+E500+i.
التشغيل: python3 tools/gen_hud_art.py [مجلد_معاينة]
"""
import math
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
C = 16  # حجم الخلية
OUTLINE = (16, 10, 20, 255)

# أرقام الرموز (لازم تطابق GLYPH بالسكربت)
G = {
    "heart": 0, "heart_half": 1, "heart_empty": 2, "rift": 3,
    "wave_on": 4, "wave_off": 5, "gold_full": 6, "gold_empty": 7, "xp_full": 8, "xp_empty": 9,
    "pw_full": 10, "pw_empty": 11, "boss": 12, "hp_full": 13, "hp_empty": 14,
    "rank0": 16, "power0": 32, "ready": 48, "cool": 49, "lock": 50, "held": 51, "sword": 52, "lens": 53, "rift_ring": 54, "sep": 55,
    "mana_full": 56, "mana_empty": 57, "mana": 58, "buff_might": 59, "buff_bulwark": 60, "buff_focus": 61, "buff_swift": 62,
    "dash": 63, "dash_cd": 47,
    # شاشة الخيميائي (v1.37.1): خانة القدر الفاضية، قنينة الماء، 6 شعلات روح، 6 جرعات، سهم، وعلامة "ما تمتزج"
    "alc_slot": 64, "alc_water": 65, "alc_flame0": 66, "alc_potion0": 72, "alc_arrow": 78, "alc_none": 79,
}
POWER_ORDER = ["iron", "wind", "echo", "crystal", "accountant", "borrower", "distance", "law", "star"]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


class Cell:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c):
        if 0 <= x < C and 0 <= y < C:
            self.px[(int(x), int(y))] = c if len(c) == 4 else (*c, 255)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def mask(self, rows, pal, ox=0, oy=0, k=1):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in pal:
                    for a in range(k):
                        for b in range(k):
                            self.put(ox + x * k + a, oy + y * k + b, pal[ch])

    def outline(self):
        out = dict(self.px)
        for (x, y) in self.px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if 0 <= q[0] < C and 0 <= q[1] < C and q not in self.px:
                    out[q] = OUTLINE
        self.px = out
        return self


HEART = [
    "..XXX...XXX..",
    ".XHHXX.XXXXX.",
    "XHHXXXXXXXXXX",
    "XHXXXXXXXXXXX",
    "XXXXXXXXXXXXX",
    "XXXXXXXXXXXXD",
    ".XXXXXXXXXXD.",
    "..XXXXXXXXD..",
    "...XXXXXXD...",
    "....XXXXD....",
    ".....XXD.....",
    "......D......",
]


def heart(kind):
    c = Cell()
    full = {"X": (226, 32, 52), "H": (255, 160, 170), "D": (150, 14, 32)}
    empty = {"X": (64, 34, 42), "H": (96, 60, 66), "D": (44, 22, 28)}
    for y, row in enumerate(HEART):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            pal = full if (kind == "full" or (kind == "half" and x < 6)) else empty
            c.put(1 + x, 2 + y, pal[ch])
    return c.outline()


def seg(base, hi, lo, filled=True, glow=False):
    """قطعة شريط مايلة (متوازي أضلاع) بتدرج ولمعة."""
    c = Cell()
    for y in range(4, 12):
        sh = (11 - y) // 3
        for x in range(1 + sh, 15 + sh - 3):
            if not filled:
                col = mix((34, 28, 44), (52, 44, 66), (y - 4) / 7)
            else:
                t = (y - 4) / 7
                col = mix(hi, lo, t) if y > 5 else hi
                if glow and (x + y) % 5 == 0:
                    col = (255, 255, 255)
            c.put(x, y, col)
    return c.outline()


def rift_icon():
    """شق متعرج عمودي: حافة متوهجة بنفسجية-زرقاء وقلب أسود."""
    c = Cell()
    xs = [8, 7, 6, 7, 9, 10, 9, 7, 6, 7, 8, 9, 8]
    for i, x in enumerate(xs):
        y = 1 + i
        w = 1 if i in (0, 12) else (2 if i in (1, 11) else 3)
        for dx in range(-w, w + 1):
            col = (20, 6, 40) if abs(dx) < w - 0 and w > 1 and abs(dx) <= w - 2 else ((150, 90, 255) if abs(dx) == w else (110, 200, 255))
            c.put(x + dx, y, col)
    for (x, y) in ((3, 4), (13, 9), (4, 11), (12, 3)):
        c.put(x, y, (190, 150, 255))
    return c.outline()


def wave_glyph(on):
    c = Cell()
    rows = ["X......X", "XX....XX", ".XX..XX.", "..XXXX..", "...XX..."]
    c.mask(rows, {"X": (255, 110, 60) if on else (60, 52, 70)}, 4, 5)
    if on:
        c.put(7, 9, (255, 220, 160)); c.put(8, 9, (255, 220, 160))
    return c.outline()


def skull_glyph():
    c = Cell()
    rows = [".XXXXXXX.", "XXXXXXXXX", "XXXXXXXXX", "XRRXXXRRX", "XRRXXXRRX", "XXXX.XXXX", ".XXXXXXX.", "..X.X.X..", "..XXXXX.."]
    c.mask(rows, {"X": (236, 230, 214), "R": (230, 30, 40)}, 3, 3)
    return c.outline()


def crest(rank):
    c = Cell()
    BR, BR2 = (196, 120, 54), (240, 170, 96)
    IR, IR2 = (150, 156, 170), (210, 216, 228)
    SI, SI2 = (196, 204, 220), (250, 252, 255)
    GO, GO2, GOD = (236, 180, 50), (255, 236, 140), (160, 100, 20)
    CR = (190, 30, 50)
    VI = (170, 90, 255)
    if rank == 0:  # ميدالية برونز
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 8)
                if d < 6:
                    c.put(x, y, BR2 if d < 2 or (x < 7 and y < 7 and d > 4) else BR)
        return c.outline()
    shield = ["XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX",
              ".XXXXXXXXX.", ".XXXXXXXXX.", "..XXXXXXX..", "...XXXXX...", "....XXX....", ".....X....."]
    body, hi = {1: (IR, IR2), 2: (SI, SI2), 3: (GO, GO2), 4: (GO, GO2), 5: (CR, (240, 90, 100))}.get(rank, (GO, GO2))
    if rank == 6:  # نجمة مشعة بجوهرة
        for i in range(8):
            a = i * math.pi / 4
            for r in range(1, 8 if i % 2 == 0 else 5):
                c.put(round(7.5 + math.cos(a) * r), round(8 + math.sin(a) * r), GO2 if r > 4 else GO)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                c.put(8 + dx, 8 + dy, VI if abs(dx) + abs(dy) < 2 else (120, 50, 200))
        c.put(7, 7, (240, 220, 255))
        return c.outline()
    for y, row in enumerate(shield):
        for x, ch in enumerate(row):
            if ch == "X":
                c.put(2 + x, 2 + y, hi if x < 2 or y < 1 else body)
    cx = 7
    if rank == 1:
        for k in range(4):
            c.put(cx - k, 6 + k, (60, 64, 76)); c.put(cx + k, 6 + k, (60, 64, 76))
    elif rank == 2:
        for k in range(7):
            c.put(cx - 3 + k, 4 + k, (70, 74, 90)); c.put(cx + 3 - k, 4 + k, (70, 74, 90))
    elif rank in (3, 4):
        star = [".....", "..X..", "XXXXX", ".XXX.", ".X.X."]
        c.mask(star, {"X": (255, 255, 255)}, cx - 2, 5)
        if rank == 4:
            c.mask(["X.X.X", "XXXXX"], {"X": GO2}, cx - 2, 0)
    elif rank == 5:
        for k in range(5):
            c.put(0, 4 + k, GO2); c.put(1, 3 + k, GO); c.put(15, 4 + k, GO2); c.put(14, 3 + k, GO)
        c.mask([".X.", "XXX", ".X."], {"X": GO2}, cx - 1, 6)
    return c.outline()


def emblem(key):
    c = Cell()
    if key == "iron":   # قبضة حديد
        rows = ["..XXXXXXXX..", ".XHXHXHXHXX.", ".XXXXXXXXXX.", ".XXXXXXXXXX.", "XXXXXXXXXXX.", "XXXXXXXXXXX.", ".XXXXXXXXX..", "..BBBBBBB...", "..BBBBBBB...", "..XXXXXXX..."]
        c.mask(rows, {"X": (160, 166, 180), "H": (225, 230, 240), "B": (205, 132, 52)}, 2, 3)
    elif key == "wind":  # دوامة ريح
        for i in range(40):
            t = i / 39
            a = t * math.pi * 3.2
            r = 1 + t * 6
            c.put(round(7.5 + math.cos(a) * r), round(8 + math.sin(a) * r * 0.8), mix((240, 255, 245), (60, 200, 110), t))
    elif key == "echo":  # أقواس صوت
        for r, col in ((2, (235, 255, 255)), (4.5, (120, 250, 240)), (7, (40, 190, 200))):
            for i in range(30):
                a = -1.0 + i / 29 * 2.0
                c.put(round(4 + math.cos(a) * r), round(8 + math.sin(a) * r), col)
        c.rect(2, 7, 3, 9, (235, 255, 255))
    elif key == "crystal":
        rows = ["....X....", "...XWX...", "..XWPPX..", "..XWPPX..", ".XWPPPDX.", ".XWPPPDX.", ".XPPPPDX.", "..XPPDX..", "..XPPDX..", "...XDX...", "....X...."]
        c.mask(rows, {"X": (196, 50, 150), "W": (255, 235, 250), "P": (255, 120, 200), "D": (200, 70, 160)}, 3, 2)
    elif key == "accountant":  # عملة بالرقم
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 8)
                if d < 6.5:
                    c.put(x, y, (255, 236, 140) if d > 5.3 else (236, 180, 50))
        c.mask(["XXX", "..X", "XXX", "..X", "XXX"], {"X": (130, 80, 10)}, 6, 6)
    elif key == "borrower":  # أثر مخلب
        c.mask(["..X.X.X..", ".XXXXXXX.", ".XXXXXXX.", "..XXXXX..", "...XXX..."], {"X": (255, 175, 40)}, 3, 7)
        for x in (4, 7, 10):
            c.rect(x, 3, x + 1, 5, (255, 220, 120))
    elif key == "distance":  # بوابة
        for i in range(60):
            a = i / 60 * math.pi * 2
            c.put(round(7.5 + math.cos(a) * 6), round(8 + math.sin(a) * 6.5), (70, 160, 255) if i % 6 else (230, 245, 255))
            c.put(round(7.5 + math.cos(a) * 3), round(8 + math.sin(a) * 3.3), (25, 70, 170))
    elif key == "law":  # ميزان
        c.rect(7, 3, 8, 13, (215, 170, 255))
        c.rect(3, 4, 12, 4, (215, 170, 255))
        c.rect(5, 13, 10, 13, (170, 90, 255))
        for sx in (3, 12):
            c.rect(sx - 2, 8, sx + 2, 8, (236, 180, 50)); c.put(sx - 1, 7, (236, 180, 50)); c.put(sx + 1, 7, (236, 180, 50))
            c.put(sx - 1, 5, (200, 200, 220)); c.put(sx + 1, 6, (200, 200, 220))
    elif key == "star":
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 7 if i % 2 == 0 else 3
            x1, y1 = 7.5 + math.cos(a) * r, 8 + math.sin(a) * r
            for k in range(12):
                t = k / 11
                c.put(round(7.5 + (x1 - 7.5) * t), round(8 + (y1 - 8) * t), (255, 214, 90) if t > 0.4 else (255, 250, 225))
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if abs(dx) + abs(dy) < 3:
                    c.put(8 + dx, 8 + dy, (255, 236, 140))
    return c.outline()


def icon(kind):
    c = Cell()
    if kind == "ready":
        c.mask(["...X...", "..XWX..", ".XWGGX.", "XWGGGGX", ".XGGDX.", "..XDX..", "...X..."], {"X": (30, 160, 70), "W": (220, 255, 230), "G": (80, 230, 120), "D": (40, 170, 80)}, 1, 1, 2)
    elif kind == "cool":
        c.mask(["XXXXXXX", ".XSSSX.", "..XSX..", "...X...", "..X.X..", ".XSSSX.", "XXXXXXX"], {"X": (220, 140, 60), "S": (255, 220, 140)}, 1, 1, 2)
    elif kind == "lock":
        c.mask(["..XXX..", ".X...X.", ".X...X.", "XXXXXXX", "XLLKLLX", "XLLKLLX", "XXXXXXX"], {"X": (110, 110, 124), "L": (160, 160, 176), "K": (40, 40, 50)}, 1, 1, 2)
    elif kind == "held":
        c.mask(["X...", "XX..", "XXX.", "XXXX", "XXX.", "XX..", "X..."], {"X": (255, 220, 80)}, 4, 1, 2)
    elif kind == "sword":
        for k in range(9):
            c.put(4 + k, 11 - k, (230, 236, 250)); c.put(5 + k, 11 - k, (160, 170, 200))
        c.rect(3, 10, 6, 10, (236, 180, 50)); c.rect(4, 9, 4, 12, (236, 180, 50)); c.put(2, 13, (120, 60, 30)); c.put(3, 12, (120, 60, 30))
    elif kind == "lens":  # عدسة: حلقة نحاس وزجاج سماوي بيه أرض صغيرة، ومقبض
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 6.5, y - 6.5)
                if d < 5.6:
                    c.put(x, y, (205, 150, 60) if d > 4.4 else ((90, 200, 120) if y > 7 else (120, 220, 255)))
        c.put(5, 4, (240, 255, 255)); c.put(4, 5, (240, 255, 255)); c.put(8, 9, (60, 150, 90))
        for k in range(5):
            c.put(10 + k, 10 + k, (120, 80, 40)); c.put(11 + k, 10 + k, (90, 56, 28))
    elif kind == "rift_ring":  # أرض فاسدة
        c.rect(1, 9, 14, 12, (40, 20, 70))
        for x in range(1, 15, 2):
            c.put(x, 9, (150, 90, 255)); c.put(x + 1, 8, (110, 200, 255))
    elif kind == "sep":
        c.mask(["X", "X", "X", "X", "X", "X", "X", "X"], {"X": (120, 100, 70)}, 7, 4)
        c.put(7, 3, (236, 180, 50)); c.put(7, 12, (236, 180, 50))
        return c
    return c.outline()


def mana_icon():
    """بلورة مانا زرقة (معين بلمعة)"""
    c = Cell()
    for y in range(2, 14):
        w = 5 - abs(y - 7.5) * 0.75
        for x in range(16):
            if abs(x + 0.5 - 8) <= w:
                t = (y - 2) / 11
                col = mix((150, 190, 255), (40, 70, 200), t)
                if x + 0.5 < 8 and y < 8:
                    col = mix(col, (230, 240, 255), 0.45)
                c.put(x, y, col)
    return c.outline()


def _from_px(px):
    """أيقونة 16×16 من gen_gear (Px) إلى خلية خط"""
    c = Cell()
    for (x, y), col in px.p.items():
        c.put(x, y, col)
    return c


def alchemy_cells():
    """رموز شاشة الخيميائي: نفس رسمات الأيتمات بالضبط (شعلات الروح والجرعات) + خانة وقنينة ماء وسهم"""
    import gen_gear as GG
    out = {}
    slot = Cell()
    for i in range(1, 15):
        for j in (1, 14):
            slot.put(i, j, (110, 96, 140)); slot.put(j, i, (110, 96, 140))
    for i in range(2, 14):
        for j in range(2, 14):
            slot.put(i, j, (30, 24, 44, 200))
    out[G["alc_slot"]] = slot
    out[G["alc_water"]] = _from_px(GG.icon_potion((70, 120, 230)))
    for i, fl in enumerate(GG.SOUL_FLAMES):
        out[G["alc_flame0"] + i] = _from_px(GG.icon_soul_flame(fl[4]))
    for i, po in enumerate(GG.POTIONS):
        out[G["alc_potion0"] + i] = _from_px(GG.icon_potion(po[3]))
    arrow = Cell()
    for x in range(2, 13):                                                     # سهم لليمين: ساق + راس مثلث
        arrow.put(x, 7, (240, 220, 160)); arrow.put(x, 8, (240, 220, 160))
    for k in range(5):
        arrow.put(13 - k, 7 - k, (240, 220, 160)); arrow.put(13 - k, 8 + k, (240, 220, 160))
        arrow.put(12 - k, 7 - k, (200, 170, 100)); arrow.put(12 - k, 8 + k, (200, 170, 100))
    out[G["alc_arrow"]] = arrow
    none = Cell()
    for k in range(3, 13):
        for t in (0, 1):
            none.put(k + t, k, (230, 70, 70)); none.put(15 - k - t, k, (230, 70, 70))
    out[G["alc_none"]] = none
    return out


def dash_icon(on):
    """شحنة الداش: سهمين » (فاتح ذهبي-أبيض = جاهز، رمادي غامق = يشحن)"""
    c = Cell()
    hi, lo = ((255, 246, 200), (240, 190, 70)) if on else ((96, 96, 110), (60, 60, 72))
    for ox in (1, 7):
        for k in range(6):
            for t in range(3):
                x = ox + k + t
                c.put(x, 2 + k, hi if t == 0 else lo)
                c.put(x, 13 - k, hi if t == 0 else lo)
    return c.outline()


def bottle(col):
    """قنينة جرعة صغيرة (أيقونة التقوية الشغالة)"""
    c = Cell()
    glass = (210, 226, 236)
    for y in range(16):
        for x in range(16):
            if (x + 0.5 - 8) ** 2 + (y + 0.5 - 10) ** 2 <= 4.6 ** 2:
                c.put(x, y, mix(col, (255, 255, 255), 0.35) if (x - 6) ** 2 + (y - 9) ** 2 < 2 else (col if y >= 8 else glass))
    c.rect(7, 3, 8, 5, glass)
    c.rect(6, 2, 9, 2, (140, 98, 58))
    return c.outline()


def build_sheet():
    cells = {}
    cells[G["heart"]] = heart("full"); cells[G["heart_half"]] = heart("half"); cells[G["heart_empty"]] = heart("empty")
    cells[G["rift"]] = rift_icon()
    cells[G["wave_on"]] = wave_glyph(True)
    cells[G["wave_off"]] = wave_glyph(False)
    cells[G["boss"]] = skull_glyph()
    cells[G["gold_full"]] = seg((236, 180, 50), (255, 236, 140), (170, 110, 20))
    cells[G["gold_empty"]] = seg(None, None, None, filled=False)
    cells[G["xp_full"]] = seg((70, 210, 255), (170, 240, 255), (30, 120, 200))
    cells[G["xp_empty"]] = seg(None, None, None, filled=False)
    cells[G["pw_full"]] = seg((255, 90, 210), (255, 170, 235), (170, 40, 140))
    cells[G["pw_empty"]] = seg(None, None, None, filled=False)
    cells[G["hp_full"]] = seg((226, 32, 52), (255, 130, 140), (140, 10, 30))
    cells[G["hp_empty"]] = seg(None, None, None, filled=False)
    cells[G["mana_full"]] = seg((70, 110, 255), (160, 190, 255), (30, 50, 170))
    cells[G["mana_empty"]] = seg(None, None, None, filled=False)
    cells[G["mana"]] = mana_icon()
    for k, col in (("might", (255, 140, 30)), ("bulwark", (140, 160, 184)), ("focus", (170, 80, 255)), ("swift", (90, 230, 120))):
        cells[G["buff_" + k]] = bottle(col)
    for k, cell in alchemy_cells().items():
        cells[k] = cell
    cells[G["dash"]] = dash_icon(True)
    cells[G["dash_cd"]] = dash_icon(False)
    for r in range(7):
        cells[G["rank0"] + r] = crest(r)
    for i, k in enumerate(POWER_ORDER):
        cells[G["power0"] + i] = emblem(k)
    for k in ("ready", "cool", "lock", "held", "sword", "lens", "rift_ring", "sep"):
        cells[G[k]] = icon(k)
    sheet = Image.new("RGBA", (C * 16, C * 16), (0, 0, 0, 0))
    for idx, cell in cells.items():
        ox, oy = (idx % 16) * C, (idx // 16) * C
        for (x, y), col in cell.px.items():
            sheet.putpixel((ox + x, oy + y), col)
    return sheet, cells


def panel():
    """إطار اللوحة (nine-slice 16x16، الشرائح 4 بكسل، v1.36.1): خلفية كحلية شبه شفافة، حافة غامقة، خط ذهب، ولمعة بالزوايا.
    كان 32x32 بشرائح 7 بكسل (إطار ثخين)؛ صار أرفع ويا تصغير خط اللوحة 0.75."""
    W = 16
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    for y in range(W):
        for x in range(W):
            im.putpixel((x, y), (*mix((26, 20, 44), (10, 8, 20), y / (W - 1)), 178))
    GOLD, GOLD2, DARK = (214, 164, 64, 255), (255, 226, 140, 255), (8, 6, 12, 235)
    for i in range(W):
        for (x, y) in ((i, 0), (i, W - 1), (0, i), (W - 1, i)):
            im.putpixel((x, y), DARK)
        for (x, y) in ((i, 1), (i, W - 2), (1, i), (W - 2, i)):
            if 1 <= x <= W - 2 and 1 <= y <= W - 2:
                im.putpixel((x, y), GOLD)
    for (cx, cy, fx, fy) in ((1, 1, 1, 1), (W - 2, 1, -1, 1), (1, W - 2, 1, -1), (W - 2, W - 2, -1, -1)):
        for k in range(3):
            im.putpixel((cx + fx * k, cy), GOLD2); im.putpixel((cx, cy + fy * k), GOLD2)
        im.putpixel((cx + fx, cy + fy), (170, 90, 255, 255))
    return im


def panel_old():
    """الإطار القديم (nine-slice 32x32)، باقي للمقارنة."""
    W = 32
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    for y in range(W):
        for x in range(W):
            t = y / (W - 1)
            im.putpixel((x, y), (*mix((26, 20, 44), (10, 8, 20), t), 178))
    GOLD, GOLD2, DARK = (214, 164, 64, 255), (255, 226, 140, 255), (8, 6, 12, 235)
    for i in range(W):
        for (x, y) in ((i, 0), (i, W - 1), (0, i), (W - 1, i)):
            im.putpixel((x, y), DARK)
        for (x, y) in ((i, 1), (i, W - 2), (1, i), (W - 2, i)):
            if 1 <= x <= W - 2 and 1 <= y <= W - 2:
                im.putpixel((x, y), GOLD)
        for (x, y) in ((i, 3), (i, W - 4), (3, i), (W - 4, i)):
            if 3 <= x <= W - 4 and 3 <= y <= W - 4:
                im.putpixel((x, y), (120, 86, 40, 200))
    orn = ["XXXXX", "XWW..", "XW...", "X....", "X...."]
    for (cx, cy, fx, fy) in ((1, 1, 1, 1), (W - 2, 1, -1, 1), (1, W - 2, 1, -1), (W - 2, W - 2, -1, -1)):
        for y, row in enumerate(orn):
            for x, ch in enumerate(row):
                if ch == "X":
                    im.putpixel((cx + fx * x, cy + fy * y), GOLD2)
                elif ch == "W":
                    im.putpixel((cx + fx * x, cy + fy * y), (255, 250, 220, 255))
        im.putpixel((cx + fx * 2, cy + fy * 2), (170, 90, 255, 255))
    return im


def portrait():
    """إطار مجسم اللاعب 36x50: خلفية متدرجة بنفسجية، إطار ذهبي، زوايا وجوهرة تحت."""
    W, H = 36, 50
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - W / 2) / W, (y - H * 0.45) / H)
            im.putpixel((x, y), (*mix((70, 40, 120), (12, 8, 24), min(1, d * 2.2)), 190))
    GOLD, GOLD2, DARK = (214, 164, 64, 255), (255, 226, 140, 255), (8, 6, 12, 240)
    for x in range(W):
        for y in (0, H - 1):
            im.putpixel((x, y), DARK)
        for y in (1, H - 2):
            im.putpixel((x, y), GOLD)
    for y in range(H):
        for x in (0, W - 1):
            im.putpixel((x, y), DARK)
        for x in (1, W - 2):
            im.putpixel((x, y), GOLD)
    for (cx, cy, fx, fy) in ((2, 2, 1, 1), (W - 3, 2, -1, 1), (2, H - 3, 1, -1), (W - 3, H - 3, -1, -1)):
        for k in range(4):
            im.putpixel((cx + fx * k, cy), GOLD2); im.putpixel((cx, cy + fy * k), GOLD2)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if abs(dx) + abs(dy) <= 2:
                im.putpixel((W // 2 + dx, H - 2 + min(dy, 1)), (170, 90, 255, 255) if abs(dx) + abs(dy) < 2 else GOLD2)
    return im


def main():
    os.makedirs(os.path.join(RP, "font"), exist_ok=True)
    os.makedirs(os.path.join(RP, "textures", "ui"), exist_ok=True)
    sheet, cells = build_sheet()
    sheet.save(os.path.join(RP, "font", "glyph_E5.png"))
    panel().save(os.path.join(RP, "textures", "ui", "sh_hud_panel.png"))
    with open(os.path.join(RP, "textures", "ui", "sh_hud_panel.json"), "w") as f:
        f.write('{ "nineslice_size": 4, "base_size": [ 16, 16 ] }\n')
    portrait().save(os.path.join(RP, "textures", "ui", "sh_hud_portrait.png"))
    print("hud art ok:", len(cells), "رمز")
    if len(sys.argv) > 1:
        preview(sheet, sys.argv[1])


def nine(img, w, h, k=7):
    """رسم nine-slice مثل اللعبة."""
    W, H = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs = [(0, k, 0, k), (k, W - k, k, w - k), (W - k, W, w - k, w)]
    ys = [(0, k, 0, k), (k, H - k, k, h - k), (H - k, H, h - k, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            out.paste(img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST), (dx0, dy0))
    return out


def preview(sheet, out):
    """معاينة تقريبية للـHUD بحجم وحدات الواجهة ×3."""
    from PIL import ImageDraw, ImageFont
    S = 3
    img = Image.new("RGBA", (330 * S, 62 * S), (104, 150, 92, 255))
    gl = lambda i: sheet.crop(((i % 16) * C, (i // 16) * C, (i % 16) * C + C, (i // 16) * C + C)).resize((8 * S, 8 * S), Image.NEAREST)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 7 * S)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
    lines = [
        [("g", G["rank0"] + 2), ("t", " Warrior ", (255, 200, 60)), *[("g", G["gold_full"])] * 4, *[("g", G["gold_empty"])] * 2, ("t", " 7/15  ", (170, 170, 170)), *[("g", G["heart"])] * 7, ("g", G["heart_half"]), *[("g", G["heart_empty"])] * 2, ("t", " 31/40", (255, 90, 90))],
        [("t", "Lv 44 ", (90, 220, 255)), *[("g", G["xp_full"])] * 2, *[("g", G["xp_empty"])] * 3, ("t", " 7%  ", (170, 170, 170)), ("g", G["power0"] + 3), ("t", " Crystal Lord ", (255, 120, 220)), ("t", "Lv6/6 ", (255, 120, 255)), *[("g", G["pw_full"])] * 5],
        [("g", G["rift"]), ("t", " Violet Rift ", (200, 120, 255)), ("t", "(Vile) 64m ↗  ", (170, 170, 170)), ("g", G["wave_on"]), ("g", G["wave_on"]), ("g", G["wave_off"]), ("t", " Wave 2/3  ", (255, 140, 90)), ("g", G["boss"])],
        [("t", "Skills ", (170, 170, 170)), ("g", G["held"]), ("g", G["ready"]), ("t", "1  ", (90, 255, 90)), ("g", G["cool"]), ("t", "2 3.4  ", (255, 90, 90)), ("g", G["ready"]), ("t", "3  ", (90, 255, 90)), ("g", G["lock"]), ("t", "4", (120, 120, 120))],
    ]
    d = ImageDraw.Draw(img)
    rows = []
    for ln in lines:
        x = 0
        for item in ln:
            x += (8 * S + S) if item[0] == "g" else int(d.textlength(item[1], font=font))
        rows.append(x)
    pw = max(rows) // S + 18
    img.alpha_composite(nine(panel(), pw * S // S, 4 * 11 + 9).resize((pw * S, (4 * 11 + 9) * S), Image.NEAREST), (39 * S, 2 * S))
    img.alpha_composite(portrait().resize((36 * S, 50 * S), Image.NEAREST), (2 * S, 2 * S))
    y = 7 * S
    for ln in lines:
        x = 47 * S
        for item in ln:
            if item[0] == "g":
                img.alpha_composite(gl(item[1]), (x, y)); x += 8 * S + S
            else:
                d.text((x + S, y + S), item[1], fill=(40, 40, 40, 255), font=font)
                d.text((x, y), item[1], fill=(*item[2], 255), font=font); x += int(d.textlength(item[1], font=font))
        y += 11 * S
    img.save(os.path.join(out, "hud_preview.png"))
    sheet.resize((512, 512), Image.NEAREST).save(os.path.join(out, "glyph_sheet.png"))


if __name__ == "__main__":
    main()
