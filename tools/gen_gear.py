"""العتاد الجديد (v1.35): مواد الوحوش، الجرعات الست، ودروع الوحوش الثلاث.
يولد: أيقونات (بكسل 16×16 بأسلوب ماينكرافت، مكبرة لـ32×32)، ملفات الأيتمات (BP/items)، item_texture.json،
تكستشرات الدروع على تخطيط ماينكرافت القياسي 64×32 (رسم أصلي: فرو/درع حشرة/جلد)، الـattachables (موديلات الدروع
الأصلية geometry.humanoid.armor.* مثل الحديد بالضبط)، ووصفات الصناعة (BP/recipes).
التشغيل: python3 tools/gen_gear.py [مجلد_معاينة]"""
import json
import math
import os
import random
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
OUT = (20, 14, 24)

# ───────────────────────── مواد الوحوش ─────────────────────────
# (المعرف، الاسم، اللون، الوحش، الشكل، ألوان)
MATERIALS = [
    ("shadow_pelt", "Shadow Pelt", "§5", "Shadow Hound", "hide", ((46, 34, 70), (86, 62, 130), (24, 16, 38), (150, 110, 230))),
    ("ember_horn", "Ember Horn", "§6", "Ember Imp", "horn", ((226, 214, 190), (255, 150, 40), (120, 100, 80), (255, 230, 120))),
    ("sand_carapace", "Sand Carapace", "§e", "Sand Scorpion", "carapace", ((196, 156, 96), (232, 200, 140), (122, 88, 48), (70, 50, 28))),
    ("rust_core", "Rust Core", "§3", "Rust Guard", "core", ((104, 108, 100), (90, 136, 70), (60, 62, 58), (80, 230, 210))),
    ("gloom_antler", "Gloom Antler", "§b", "Gloomhorn", "antler", ((176, 170, 196), (220, 216, 236), (110, 104, 132), (110, 220, 255))),
    ("hollow_lens", "Hollow Lens", "§6", "Hollow Seer", "lens", ((230, 180, 60), (255, 140, 40), (40, 20, 30), (255, 250, 220))),
    ("spirit_fur", "Spirit Fur", "§d", "Veilfox", "fur", ((236, 232, 244), (255, 255, 255), (186, 176, 210), (200, 120, 255))),
    ("magma_scale", "Magma Scale", "§c", "Magmamoth", "scale", ((58, 50, 52), (96, 84, 84), (30, 26, 28), (255, 130, 30))),
    ("bear_hide", "Grey Bear Hide", "§7", "Grey Bear", "hide", ((112, 108, 104), (170, 166, 160), (66, 62, 60), (214, 212, 206))),
    ("bear_claw", "Grey Bear Claw", "§f", "Grey Bear", "claw", ((232, 226, 210), (255, 252, 240), (150, 140, 124), (70, 60, 56))),
    ("mantis_chitin", "Mantis Chitin", "§a", "Prayer Mantis", "chitin", ((100, 176, 70), (160, 220, 110), (52, 108, 40), (180, 80, 255))),
    ("mantis_scythe", "Mantis Scythe", "§a", "Prayer Mantis", "scythe", ((210, 232, 180), (246, 255, 230), (110, 150, 90), (44, 32, 58))),
]

# ───────────────────────── الجرعات ─────────────────────────
POTIONS = [
    ("potion_vitality", "Potion of Vitality", "§c", (220, 40, 60), "Heals half your health at once and regenerates for 5 s."),
    ("potion_mana", "Mana Elixir", "§9", (60, 110, 255), "Refills your mana completely."),
    ("potion_might", "Potion of Might", "§6", (255, 140, 30), "8 minutes: your skills and weapons hit 25% harder."),
    ("potion_bulwark", "Potion of Bulwark", "§7", (140, 160, 184), "8 minutes: Resistance I (20% less damage)."),
    ("potion_focus", "Potion of Focus", "§d", (170, 80, 255), "6 minutes: skill cooldowns 30% shorter and mana regenerates twice as fast."),
    ("potion_swift", "Potion of Swiftness", "§a", (90, 230, 120), "6 minutes: Speed II and Jump Boost I."),
]

# ───────────────────────── الدروع ─────────────────────────
# (مفتاح، اسم، لون، مادتين (أساسية، ثانوية)، الحماية [خوذة، صدر، رجلين، جزمة]، المتانة، ألوان التكستشر، نقشة)
ARMOR_SETS = [
    ("hunter", "Shadow Hunter", "§5", ("sh:shadow_pelt", "sh:sand_carapace"), (2, 6, 5, 2), 260,
     dict(base=(48, 36, 72), light=(88, 64, 132), dark=(26, 18, 40), accent=(200, 160, 96), accent2=(150, 110, 230)), "pelt"),
    ("grizzly", "Grizzly", "§7", ("sh:bear_hide", "sh:bear_claw"), (3, 7, 6, 3), 420,
     dict(base=(108, 104, 100), light=(176, 172, 166), dark=(62, 58, 56), accent=(236, 230, 214), accent2=(120, 84, 52)), "pelt"),
    ("mantis", "Mantis", "§a", ("sh:mantis_chitin", "sh:mantis_scythe"), (3, 8, 6, 3), 520,
     dict(base=(96, 170, 66), light=(160, 220, 108), dark=(46, 98, 36), accent=(230, 244, 200), accent2=(170, 80, 250)), "chitin"),
]
PIECES = [
    ("helmet", "Hood", "slot.armor.head", "armor_head", "geometry.humanoid.armor.helmet", "helmet_layer_visible", 1),
    ("chestplate", "Chestguard", "slot.armor.chest", "armor_torso", "geometry.humanoid.armor.chestplate", "chest_layer_visible", 1),
    ("leggings", "Leggings", "slot.armor.legs", "armor_legs", "geometry.humanoid.armor.leggings", "leg_layer_visible", 2),
    ("boots", "Boots", "slot.armor.feet", "armor_feet", "geometry.humanoid.armor.boots", "boot_layer_visible", 1),
]
SET_BONUS = {
    "hunter": "Full set: Speed I and Jump Boost I.",
    "grizzly": "Full set: Resistance I, and 4 golden hearts (Absorption) every 30 s.",
    "mantis": "Full set: Speed I, Strength I, and 20% of melee hits are countered back at the attacker.",
}


# ───────────────────────── رسم بكسل 16×16 ─────────────────────────
class Px:
    def __init__(self):
        self.p = {}

    def put(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16 and c is not None:
            self.p[(int(x), int(y))] = tuple(int(v) for v in c[:3])

    def fill(self, inside, color):
        for y in range(16):
            for x in range(16):
                if inside(x + 0.5, y + 0.5):
                    self.put(x, y, color(x, y))

    def outline(self, col=OUT):
        add = []
        for y in range(16):
            for x in range(16):
                if (x, y) in self.p:
                    continue
                if any((x + dx, y + dy) in self.p for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    add.append((x, y))
        for q in add:
            self.p[q] = col
        return self

    def image(self, scale=2):
        img = Image.new("RGBA", (16 * scale, 16 * scale), (0, 0, 0, 0))
        for (x, y), c in self.p.items():
            for dy in range(scale):
                for dx in range(scale):
                    img.putpixel((x * scale + dx, y * scale + dy), (*c, 255))
        return img


def stable(v):
    """هاش ثابت بين التشغيلات (hash() بالبايثون يتغير كل مرة)"""
    return sum(ord(c) * (i + 1) for i, c in enumerate(str(v))) & 0xFFFF


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def icon_material(shape, pal):
    base, light, dark, acc = pal
    P = Px()
    rnd = random.Random(stable(shape))
    if shape == "hide":                                              # جلد مفرود: جسم وسطي + 4 أرجل + راس وذيل، فرو بخصل
        def inside(x, y):
            body = 3 <= x <= 13 and 3.5 <= y <= 12.5 and not ((x < 4 or x > 12) and (y < 4.5 or y > 11.5))
            legs = any(abs(x - cx) < 1.6 and abs(y - cy) < 1.6 for cx, cy in ((2.5, 3.5), (13.5, 3.5), (2.5, 12.5), (13.5, 12.5)))
            head = 6 <= x <= 10 and 1.5 <= y <= 3.5
            tail = 7 <= x <= 9 and 12 <= y <= 14.5
            return body or legs or head or tail
        P.fill(inside, lambda x, y: light if (x * 3 + y) % 7 == 0 else dark if (x + y * 5) % 9 == 0 else mix(base, light, (8 - abs(x - 8)) / 16))
        for x, y in ((6, 6), (9, 8), (7, 10), (10, 5)):
            P.put(x, y, acc)
    elif shape == "horn":                                            # قرن مقوس: قاعدة عظم تتحول لطرف متوهج
        for i in range(40):
            t = i / 39
            cx, cy = 3 + 9 * t + 2 * math.sin(t * 3.1) * 0.3, 13 - 10 * t ** 0.8
            r = 2.2 * (1 - t) + 0.5
            for y in range(16):
                for x in range(16):
                    if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                        P.put(x, y, mix(base, light, t * 1.3) if t > 0.55 else (mix(base, dark, 0.3) if (x + y) % 4 == 0 else base))
        P.put(12, 3, acc); P.put(11, 4, acc)
    elif shape == "carapace":                                        # صفيحة مقوسة بأحزمة
        P.fill(lambda x, y: ((x - 8) / 6.2) ** 2 + ((y - 9) / 5.2) ** 2 <= 1 and y >= 4,
               lambda x, y: acc if y in (6, 9, 12) else (light if y in (5, 8, 11) else base))
        for x in (7, 8):
            P.put(x, 3, dark); P.put(x, 2, dark)
    elif shape == "core":                                            # كتلة حجر بطحلب وبلورة تركواز بالنص
        P.fill(lambda x, y: abs(x - 8) + abs(y - 8.5) <= 7.5 and 2 <= y <= 14.5 and 1.5 <= x <= 14.5,
               lambda x, y: light if y <= 4 else (dark if (x * 7 + y * 3) % 5 == 0 else base))
        for y in range(5, 12):
            w = 2 - abs(y - 8.5) * 0.6
            for x in range(16):
                if abs(x + 0.5 - 8) <= w:
                    P.put(x, y, mix(acc, (255, 255, 255), 0.5 if abs(x + 0.5 - 8) < 0.8 else 0))
    elif shape == "antler":                                          # قرن غزال متفرع
        def line(x0, y0, x1, y1, w, col):
            for i in range(30):
                t = i / 29
                cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                for y in range(16):
                    for x in range(16):
                        if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (w * (1 - 0.5 * t)) ** 2:
                            P.put(x, y, col)
        line(4, 14, 11, 2, 1.6, base)
        line(6.5, 10, 2.5, 5, 1.1, light)
        line(8.6, 6.5, 13.5, 6, 1.0, light)
        line(10, 4, 7.5, 1, 0.9, light)
        P.put(4, 13, dark); P.put(5, 12, dark)
        P.put(13, 6, acc); P.put(11, 2, acc)
    elif shape == "lens":                                            # عدسة/عين: حافة ذهب، قزحية برتقالية، بؤبؤ، لمعة
        P.fill(lambda x, y: (x - 8) ** 2 + (y - 8) ** 2 <= 6.3 ** 2,
               lambda x, y: base if (x - 8) ** 2 + (y - 8) ** 2 > 4.6 ** 2 else (light if (x - 8) ** 2 + (y - 8) ** 2 > 2.0 ** 2 else dark))
        P.put(6, 6, acc); P.put(7, 6, acc); P.put(6, 7, acc)
    elif shape == "fur":                                             # خصلة فرو روحي بطرف لهب بنفسجي
        def inside(x, y):
            t = (14.5 - y) / 12
            if t < 0 or t > 1:
                return False
            w = 4.2 * math.sin(math.pi * min(1, t * 1.15)) + 0.6
            cx = 8 + 2.2 * math.sin(t * 4)
            return abs(x - cx) <= w
        P.fill(inside, lambda x, y: acc if y <= 5 else (light if (x + y) % 3 == 0 else (dark if (x * 3 + y) % 7 == 0 else base)))
    elif shape == "scale":                                           # حرشفة بازلت مدببة بشقوق حمم
        P.fill(lambda x, y: abs(x - 8) <= 6 * min(1, (y - 1) / 6) and abs(x - 8) <= 6 * (14.5 - y) / 7 + 0.5 and y >= 1.5,
               lambda x, y: light if (x + y) % 6 == 0 else base)
        for x, y in ((8, 4), (8, 5), (7, 6), (7, 7), (8, 8), (9, 9), (9, 10), (6, 9), (5, 10), (10, 7), (11, 7)):
            P.put(x, y, acc)
    elif shape == "claw":                                            # مخلب معقوف
        for i in range(40):
            t = i / 39
            a = math.pi * 0.95 * t
            cx, cy = 8 - 5 * math.cos(a) + 1, 13 - 9 * math.sin(a * 0.9)
            r = 2.6 * (1 - t) + 0.45
            for y in range(16):
                for x in range(16):
                    if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                        P.put(x, y, acc if t < 0.12 else (light if (x - y) % 5 == 0 else base))
    elif shape == "chitin":                                          # صفيحة ورقية بعرق وسطي وعين بنفسجية
        P.fill(lambda x, y: abs(x - 8) <= 5.5 * math.sin(math.pi * max(0, min(1, (y - 1) / 14))) + 0.3,
               lambda x, y: dark if abs(x - 8) < 0.7 else (light if (x + y) % 4 == 0 else base))
        for x, y in ((10, 7), (11, 7), (10, 8), (11, 8)):
            P.put(x, y, acc)
    elif shape == "scythe":                                          # منجل: نصل مقوس بأشواك جوه ومفصل بالقاعدة
        for i in range(44):
            t = i / 43
            a = -0.2 + 2.6 * t
            cx, cy = 8 + 5.5 * math.cos(a) - 1, 9 - 6 * math.sin(a)
            r = 1.8 * math.sin(math.pi * min(1, 0.1 + t)) + 0.4
            for y in range(16):
                for x in range(16):
                    if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                        P.put(x, y, light if t > 0.2 else base)
        for x, y in ((12, 11), (12, 12), (13, 12), (13, 13)):
            P.put(x, y, dark)                                          # المفصل
        for x, y in ((6, 6), (5, 8), (6, 10)):
            P.put(x, y, acc)                                           # أشواك
    return P.outline()


def icon_potion(color):
    P = Px()
    glass = (210, 226, 236)
    P.fill(lambda x, y: (x - 8) ** 2 + (y - 10.5) ** 2 <= 5.2 ** 2,
           lambda x, y: (mix(color, (255, 255, 255), 0.35) if (x - 6) ** 2 + (y - 9) ** 2 < 2.2 else (mix(color, (0, 0, 0), 0.25) if y >= 13 else color)) if y >= 8 else glass)
    for y in range(3, 6):
        for x in (7, 8):
            P.put(x, y, glass)
    for x in (6, 7, 8, 9):
        P.put(x, 2, (140, 98, 58))
    P.put(7, 1, (110, 76, 44)); P.put(8, 1, (110, 76, 44))
    P.put(10, 9, (255, 255, 255)); P.put(5, 11, mix(color, (255, 255, 255), 0.6))
    return P.outline()


def icon_armor(piece, pal, pattern):
    P = Px()
    b, l, d, a, a2 = pal["base"], pal["light"], pal["dark"], pal["accent"], pal["accent2"]
    def shade(x, y):
        if pattern == "chitin":
            return d if y % 3 == 0 else (l if y % 3 == 1 else b)
        return l if (x * 3 + y) % 7 == 0 else (d if (x + y * 5) % 9 == 0 else b)
    if piece == "helmet":
        P.fill(lambda x, y: 2.5 <= x <= 13.5 and 3 <= y <= 11.5 and not (5 <= x <= 11 and y >= 8.5) and ((x - 8) ** 2 / 36 + (y - 7) ** 2 / 25 <= 1.2), shade)
        for x in range(4, 13):
            P.put(x, 8, a)
    elif piece == "chestplate":
        P.fill(lambda x, y: (2 <= x <= 14 and 2.5 <= y <= 13.5) and not (6 <= x <= 10 and y <= 4) and not ((x <= 4.5 or x >= 11.5) and y >= 8.5), shade)
        for y in range(5, 13):
            P.put(8, y, a)
        P.put(7, 6, a2); P.put(9, 6, a2)
    elif piece == "leggings":
        P.fill(lambda x, y: (3 <= x <= 13 and 2.5 <= y <= 5.5) or ((3 <= x <= 7 or 9 <= x <= 13) and 5 <= y <= 14.5), shade)
        for x in range(3, 13):
            P.put(x, 3, a)
    elif piece == "boots":
        P.fill(lambda x, y: ((2 <= x <= 6.5 or 9.5 <= x <= 14) and 6.5 <= y <= 13.5) and not ((x <= 3.5 and y <= 9) or (x >= 12.5 and y <= 9)) or ((1 <= x <= 6.5 or 9.5 <= x <= 15) and 11.5 <= y <= 13.5), shade)
        for x in (3, 4, 5, 10, 11, 12):
            P.put(x, 7, a)
    return P.outline()


# ───────────────────────── تكستشر الدرع (تخطيط ماينكرافت القياسي 64×32) ─────────────────────────
def box_faces(u, v, w, h, d):
    """مناطق UV لصندوق (box UV): يرجع dict اسم_الوجه -> (x0, y0, w, h)"""
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
            "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


def paint_armor(set_key, pal, pattern, layer):
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    b, l, d, a, a2 = pal["base"], pal["light"], pal["dark"], pal["accent"], pal["accent2"]
    rnd = random.Random(stable((set_key, layer)))

    def tex(x, y, fy=0):
        if pattern == "chitin":
            k = (y + fy) % 4
            col = d if k == 0 else (l if k == 1 else b)
            return mix(col, (0, 0, 0), 0.06) if (x // 2 + y) % 5 == 0 else col
        n = rnd.random()
        col = l if n < 0.14 else (d if n < 0.30 else b)
        return col

    def region(rect, fn):
        x0, y0, w, h = rect
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                c = fn(x - x0, y - y0, w, h)
                if c is not None:
                    img.putpixel((x, y), (*[int(v) for v in c], 255))

    if layer == 1:
        # الخوذة: صندوق الراس (0,0) 8×8×8 — الوجه مفتوح بالنص (العين والخشم) والحافة بلون مميز
        for name, rect in box_faces(0, 0, 8, 8, 8).items():
            def f(x, y, w, h, name=name):
                if name == "front" and 2 <= x <= 5 and 2 <= y <= 6:
                    return None
                if name == "bottom":
                    return None
                if name in ("front", "right", "left", "back") and y == h - 1:
                    return a
                if set_key == "grizzly" and name == "front" and y <= 1:
                    return a if x in (1, 2, 5, 6) else tex(x, y)          # أسنان/مخالب على جبين قلنسوة الدب
                if set_key == "mantis" and name in ("right", "left") and 2 <= y <= 3 and 3 <= x <= 4:
                    return a2                                              # عين بنفسجية على الجوانب
                return tex(x, y)
            region(rect, f)
        # الصدر: صندوق الجسم (16,16) 8×12×4
        for name, rect in box_faces(16, 16, 8, 12, 4).items():
            def f(x, y, w, h, name=name):
                if name in ("top", "bottom"):
                    return tex(x, y)
                if name == "front" and x in (3, 4) and 1 <= y <= 10:
                    return a                                               # شريط وسطي
                if name in ("front", "back") and y == h - 2:
                    return a2                                              # حزام
                if name == "front" and set_key == "mantis" and y in (3, 6) and x in (1, 6):
                    return a2
                return tex(x, y)
            region(rect, f)
        # الأكمام: صندوق الذراع (40,16) 4×12×4 — بس الكتف والعضد (8 صفوف)، والكتافة بلون مميز
        for name, rect in box_faces(40, 16, 4, 12, 4).items():
            def f(x, y, w, h, name=name):
                if name == "top":
                    return a if set_key != "hunter" else mix(a, b, 0.3)
                if name == "bottom":
                    return None
                if y >= 8:
                    return None
                if y <= 1:
                    return a if set_key != "mantis" else mix(a, b, 0.35)
                return tex(x, y)
            region(rect, f)
        # الجزمة: صندوق الرجل (0,16) 4×12×4 — بس آخر 4 صفوف + الأسفل
        for name, rect in box_faces(0, 16, 4, 12, 4).items():
            def f(x, y, w, h, name=name):
                if name == "top":
                    return None
                if name == "bottom":
                    return mix(d, (0, 0, 0), 0.3)
                if y < 8:
                    return None
                if y == 8:
                    return a
                return tex(x, y)
            region(rect, f)
    else:
        # البنطرون: الحزام من صندوق الجسم (16,16) آخر 3 صفوف + صندوق الرجل (0,16) أول 9 صفوف
        for name, rect in box_faces(16, 16, 8, 12, 4).items():
            def f(x, y, w, h, name=name):
                if name in ("top", "bottom"):
                    return tex(x, y) if name == "bottom" else None
                if y < 9:
                    return None
                if y == 9:
                    return a2
                return tex(x, y)
            region(rect, f)
        for name, rect in box_faces(0, 16, 4, 12, 4).items():
            def f(x, y, w, h, name=name):
                if name in ("top", "bottom"):
                    return tex(x, y) if name == "top" else None
                if y > 9:
                    return None
                if name == "front" and y == 4 and set_key != "hunter":
                    return a                                               # واقي الركبة
                return tex(x, y)
            region(rect, f)
    return img


# ───────────────────────── الكتابة ─────────────────────────
def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def item_json(ident, name, icon, comps):
    c = {"minecraft:icon": {"textures": {"default": icon}}, "minecraft:display_name": {"value": name}}
    c.update(comps)
    return {"format_version": "1.21.60", "minecraft:item": {"description": {"identifier": ident, "menu_category": {"category": "items"}}, "components": c}}


def main():
    prev = sys.argv[1] if len(sys.argv) > 1 else None
    tex_dir = os.path.join(RP, "textures", "items")
    itp = os.path.join(RP, "textures", "item_texture.json")
    it = json.load(open(itp, encoding="utf-8"))
    td = it["texture_data"]
    sheet = []
    for ident, name, col, mob, shape, pal in MATERIALS:
        img = icon_material(shape, pal).image()
        img.save(os.path.join(tex_dir, f"sh_{ident}.png")); sheet.append(img)
        td[f"sh_{ident}"] = {"textures": f"textures/items/sh_{ident}"}
        wjson(os.path.join(BP, "items", f"sh_{ident}.json"), item_json(f"sh:{ident}", f"{col}{name}", f"sh_{ident}", {"minecraft:max_stack_size": 64}))
    for ident, name, col, color, desc in POTIONS:
        img = icon_potion(color).image()
        img.save(os.path.join(tex_dir, f"sh_{ident}.png")); sheet.append(img)
        td[f"sh_{ident}"] = {"textures": f"textures/items/sh_{ident}"}
        wjson(os.path.join(BP, "items", f"sh_{ident}.json"), item_json(f"sh:{ident}", f"{col}{name}", f"sh_{ident}", {
            "minecraft:max_stack_size": 8,
            "minecraft:food": {"nutrition": 0, "saturation_modifier": 0, "can_always_eat": True},
            "minecraft:use_animation": "drink",
            "minecraft:use_modifiers": {"use_duration": 1.2, "movement_modifier": 0.35},
            "minecraft:glint": True,
        }))
    recipes = os.path.join(BP, "recipes")
    os.makedirs(recipes, exist_ok=True)
    PAT = {"helmet": ["ABA", "A A"], "chestplate": ["A A", "ABA", "AAA"], "leggings": ["ABA", "A A", "A A"], "boots": ["A A", "B B"]}
    for key, sname, col, (ma, mb), prot, dur, pal, pattern in ARMOR_SETS:
        for layer in (1, 2):
            paint_armor(key, pal, pattern, layer).save(os.path.join(RP, "textures", "models", "armor", f"sh_{key}_{layer}.png") if os.path.isdir(os.path.join(RP, "textures", "models", "armor")) else _mk_armor_dir(key, layer, pal, pattern))
        for (piece, pname, slot, ench, geo, vis, layer), p in zip(PIECES, prot):
            ident = f"sh:{key}_{piece}"
            img = icon_armor(piece, pal, pattern).image()
            img.save(os.path.join(tex_dir, f"sh_{key}_{piece}.png")); sheet.append(img)
            td[f"sh_{key}_{piece}"] = {"textures": f"textures/items/sh_{key}_{piece}"}
            wjson(os.path.join(BP, "items", f"sh_{key}_{piece}.json"), item_json(ident, f"{col}{sname} {pname}", f"sh_{key}_{piece}", {
                "minecraft:max_stack_size": 1,
                "minecraft:wearable": {"slot": slot, "protection": p},
                "minecraft:durability": {"max_durability": dur},
                "minecraft:enchantable": {"slot": ench, "value": 12},
                "minecraft:repairable": {"repair_items": [{"items": [ma], "repair_amount": "context.other->query.remaining_durability + 0.25 * context.other->query.max_durability"}]},
                "minecraft:tags": {"tags": ["minecraft:is_armor"]},
            }))
            wjson(os.path.join(RP, "attachables", f"sh_{key}_{piece}.json"), {"format_version": "1.8.0", "minecraft:attachable": {"description": {
                "identifier": ident,
                "materials": {"default": "armor", "enchanted": "armor_enchanted"},
                "textures": {"default": f"textures/models/armor/sh_{key}_{layer}", "enchanted": "textures/misc/enchanted_actor_glint"},
                "geometry": {"default": geo},
                "scripts": {"parent_setup": f"variable.{vis} = 0.0;"},
                "render_controllers": ["controller.render.armor"]}}})
            wjson(os.path.join(recipes, f"sh_{key}_{piece}.json"), {"format_version": "1.20.10", "minecraft:recipe_shaped": {
                "description": {"identifier": f"sh:craft_{key}_{piece}"}, "tags": ["crafting_table"],
                "pattern": PAT[piece], "key": {"A": {"item": ma}, "B": {"item": mb}},
                "unlock": [{"item": ma}], "result": {"item": ident}}})
    wjson(itp, it)
    # بيانات للسكربت (نفس الأسماء والأوصاف بالضبط)
    gear = {
        "materials": {f"sh:{i}": {"name": f"{c}{n}", "mob": mob} for i, n, c, mob, _s, _p in MATERIALS},
        "potions": {f"sh:{i}": {"name": f"{c}{n}", "desc": d} for i, n, c, _col, d in POTIONS},
        "sets": {k: {"name": f"{c}{sn}", "pieces": [f"sh:{k}_{pc[0]}" for pc in PIECES], "mats": [ma, mb], "bonus": SET_BONUS[k]} for k, sn, c, (ma, mb), *_r in ARMOR_SETS},
    }
    with open(os.path.join(BP, "scripts", "gear.js"), "w", encoding="utf-8") as f:
        f.write("// يتولد تلقائياً من tools/gen_gear.py — لا تعدله يدوياً\n")
        f.write("export const GEAR = " + json.dumps(gear, ensure_ascii=False, indent=1) + ";\n")
    print("gear ok:", len(MATERIALS), "materials,", len(POTIONS), "potions,", len(ARMOR_SETS) * 4, "armor pieces")
    if prev:
        os.makedirs(prev, exist_ok=True)
        cols = 6
        rows = math.ceil(len(sheet) / cols)
        big = Image.new("RGBA", (cols * 96, rows * 96), (46, 48, 56, 255))
        for i, im in enumerate(sheet):
            big.paste(im.resize((80, 80), Image.NEAREST), ((i % cols) * 96 + 8, (i // cols) * 96 + 8), im.resize((80, 80), Image.NEAREST))
        big.save(os.path.join(prev, "gear_icons.png"))
        arm = Image.new("RGBA", (64 * 6, 32 * 2 * 6), (46, 48, 56, 255))
        for i, (key, *_r) in enumerate(ARMOR_SETS):
            for layer in (1, 2):
                im = Image.open(os.path.join(RP, "textures", "models", "armor", f"sh_{key}_{layer}.png")).resize((384, 192), Image.NEAREST)
                arm.paste(im, (0, (i * 2 + layer - 1) * 192), im)
        arm.save(os.path.join(prev, "armor_textures.png"))


def _mk_armor_dir(key, layer, pal, pattern):
    os.makedirs(os.path.join(RP, "textures", "models", "armor"), exist_ok=True)
    return os.path.join(RP, "textures", "models", "armor", f"sh_{key}_{layer}.png")


if __name__ == "__main__":
    main()
