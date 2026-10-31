"""يولد موديلات الأسلحة 3D (Attachables) + تكستشراتها + حركات المسك بالجوال.

الطريقة (مطابقة لرمح الـTrident الرسمي بماينكرافت):
  * عظمة واحدة اسمها sh_weapon، pivot=[0,24,0]، وبها binding على خانة الأيتم.
  * السلاح مبني بطول المحور Y، ومنتصف القبضة عند y=13 (نفس إطار الـTrident).
  * حركة المسك (أول شخص / ثالث شخص) قيمها الأساسية من الـTrident الرسمي، مع scale لكل سلاح.
  * التكستشر لوحة ألوان 16x16، وكل وجه مكعب يشير لبكسل لونه (UV لكل وجه).
لتعديل مكان السلاح بإيدك: غيّر جدول HOLD تحت (pos / rot / scale) وشغل السكربت.
التشغيل من جذر المشروع:  python3 tools/gen_weapons3d.py
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
FACES = ("north", "south", "east", "west", "up", "down")

# ───────── حركة المسك: القيم الأساسية من vanilla trident.animation.json ─────────
TRIDENT_FP = {"pos": [-7.0, -3.0, -2.0], "rot": [152.0, -9.0, 25.0]}
TRIDENT_TP = {"pos": [1.5, -2.5, -10.5], "rot": [97.0, -1.5, -49.0]}
HOLD = {
    # scale يصغر الموديل الطويل ليناسب اليد. غيّر pos/rot هنا إذا شكل المسك مو مضبوط.
    "dark_katana": {"fp": {**TRIDENT_FP, "scale": 0.80}, "tp": {**TRIDENT_TP, "scale": 0.80}},
    "dawn_dagger": {"fp": {**TRIDENT_FP, "scale": 1.0}, "tp": {**TRIDENT_TP, "scale": 1.0}},
    "ember_cleaver": {"fp": {**TRIDENT_FP, "scale": 0.85}, "tp": {**TRIDENT_TP, "scale": 0.85}},
    "shadow_blade": {"fp": {**TRIDENT_FP, "scale": 0.85}, "tp": {**TRIDENT_TP, "scale": 0.85}},
    "shadow_claws": {"fp": {**TRIDENT_FP, "scale": 1.0}, "tp": {**TRIDENT_TP, "scale": 1.0}},
    "stone_maul": {"fp": {**TRIDENT_FP, "scale": 0.80}, "tp": {**TRIDENT_TP, "scale": 0.80}},
    "sunset_spear": {"fp": {**TRIDENT_FP, "scale": 0.72}, "tp": {**TRIDENT_TP, "scale": 0.72}},
}


class Weapon:
    def __init__(self, ident):
        self.ident = ident
        self.cubes = []
        self.palette = []  # قائمة ألوان RGBA

    def _idx(self, rgba):
        rgba = tuple(int(v) for v in (rgba if len(rgba) == 4 else (*rgba, 255)))
        if rgba not in self.palette:
            assert len(self.palette) < 256, "اللوحة ممتلئة"
            self.palette.append(rgba)
        return self.palette.index(rgba)

    def box(self, cx, y0, cz, w, h, d, color, top=None, side=None):
        """مكعب مركزه (cx, cz) وقاعدته عند y0. top/side ألوان بديلة للأوجه العلوية/الجانبية."""
        def uv(c):
            i = self._idx(c)
            return {"uv": [i % 16, i // 16], "uv_size": [1, 1]}
        main = uv(color)
        t = uv(top) if top else main
        s = uv(side) if side else main
        self.cubes.append({
            "origin": [round(cx - w / 2, 3), round(y0, 3), round(cz - d / 2, 3)],
            "size": [round(w, 3), round(h, 3), round(d, 3)],
            "uv": {"north": main, "south": main, "east": s, "west": s, "up": t, "down": s},
        })

    def save(self):
        tex = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for i, c in enumerate(self.palette):
            tex.putpixel((i % 16, i // 16), c)
        os.makedirs(os.path.join(RP, "textures", "models"), exist_ok=True)
        tex.save(os.path.join(RP, "textures", "models", f"sh_w_{self.ident}.png"))
        geo = {
            "format_version": "1.16.0",
            "minecraft:geometry": [{
                "description": {"identifier": f"geometry.sh_w_{self.ident}", "texture_width": 16, "texture_height": 16,
                                "visible_bounds_width": 4, "visible_bounds_height": 4, "visible_bounds_offset": [0, 1, 0]},
                "bones": [{"name": "sh_weapon", "binding": "q.item_slot_to_bone_name(c.item_slot)", "pivot": [0, 24, 0], "cubes": self.cubes}],
            }],
        }
        os.makedirs(os.path.join(RP, "models", "entity"), exist_ok=True)
        with open(os.path.join(RP, "models", "entity", f"sh_w_{self.ident}.geo.json"), "w") as f:
            json.dump(geo, f, indent=1)
        att = {
            "format_version": "1.10.0",
            "minecraft:attachable": {"description": {
                "identifier": f"sh:{self.ident}",
                "materials": {"default": "entity_alphatest", "enchanted": "entity_alphatest_glint"},
                "textures": {"default": f"textures/models/sh_w_{self.ident}", "enchanted": "textures/misc/enchanted_item_glint"},
                "geometry": {"default": f"geometry.sh_w_{self.ident}"},
                "animations": {"hold_first_person": f"animation.sh.hold_{self.ident}_fp", "hold_third_person": f"animation.sh.hold_{self.ident}_tp"},
                "scripts": {"animate": [{"hold_first_person": "context.is_first_person == 1.0"}, {"hold_third_person": "context.is_first_person == 0.0"}]},
                "render_controllers": ["controller.render.item_default"],
            }},
        }
        os.makedirs(os.path.join(RP, "attachables"), exist_ok=True)
        with open(os.path.join(RP, "attachables", f"sh_{self.ident}.attachable.json"), "w") as f:
            json.dump(att, f, indent=1)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


# ───────────────────────── كاتانا الهاوية ─────────────────────────
def katana():
    w = Weapon("dark_katana")
    SPINE, MID, EDGE, SHINE = (20, 22, 52), (52, 48, 112), (118, 104, 200), (196, 186, 250)
    GUARD, GUARD_HI = (28, 34, 76), (64, 76, 140)
    GOLD, GOLD_HI = (240, 200, 64), (255, 238, 150)
    WA, WB = (60, 62, 72), (30, 32, 40)
    POM, POM_HI = (34, 58, 128), (84, 124, 210)
    # نهاية القبضة
    w.box(0, 6.0, 0, 2.6, 2.4, 2.6, POM, top=POM_HI)
    w.box(0, 8.4, 0, 1.8, 0.4, 1.8, GUARD_HI)
    # القبضة الملفوفة (قطاعات متبادلة)
    for k in range(6):
        w.box(0, 8.8 + k * 1.5, 0, 1.9, 1.5, 1.9, WA if k % 2 == 0 else WB, top=shade(WA, 1.2))
    w.box(0, 17.8, 0, 2.3, 0.6, 2.3, GOLD)
    # الحارس بجناحين
    w.box(0, 18.4, 0, 6.6, 1.2, 2.6, GUARD, top=GUARD_HI)
    for sx in (-1, 1):
        w.box(sx * 3.4, 19.6, 0, 1.2, 1.4, 2.0, GUARD)
        w.box(sx * 3.9, 20.6, 0, 0.8, 1.0, 1.6, GUARD_HI)
        w.box(sx * 2.0, 19.6, 0, 1.2, 0.8, 2.2, GUARD_HI)
    # جوهرة ذهبية على الوجهين
    for sz in (-1, 1):
        w.box(0, 18.5, sz * 1.4, 1.5, 1.4, 0.5, GOLD, top=GOLD_HI)
    # النصل المنحني (قطاعات: ظهر داكن + حد فاتح)
    n, y = 14, 19.6
    for k in range(n):
        t = k / (n - 1)
        h = 1.8 if k < n - 2 else 1.3
        width = 3.6 - 2.1 * t
        off = 2.4 * t * t              # انحناء نحو +x
        back = width * 0.55
        edge = width - back
        thick = 1.2 - 0.4 * t
        c_back = lerp(SPINE, MID, t * 0.6)
        c_edge = lerp(MID, EDGE, 0.55 + 0.4 * t)
        if k % 4 == 1:
            c_edge = SHINE
        w.box(off - width / 2 + back / 2, y, 0, back, h, thick, c_back, top=c_back)
        w.box(off + width / 2 - edge / 2, y, 0, edge, h, thick * 0.8, c_edge, top=SHINE)
        y += h
    # سن النصل
    w.box(2.4 + 0.2, y, 0, 1.0, 1.0, 0.8, SHINE)
    w.save()
    return w


# ───────────────────────── خنجر الفجر ─────────────────────────
def dagger():
    w = Weapon("dawn_dagger")
    GOLD, GOLD_HI, GOLD_LO = (226, 178, 62), (255, 232, 140), (150, 108, 30)
    STEEL, STEEL_HI = (200, 206, 220), (246, 248, 255)
    SUN_A, SUN_B = (255, 120, 40), (255, 214, 120)
    LEATHER_A, LEATHER_B = (110, 70, 40), (74, 46, 26)
    w.box(0, 8.2, 0, 2.8, 1.6, 2.8, GOLD, top=GOLD_HI)
    for k in range(5):
        w.box(0, 9.8 + k * 1.2, 0, 1.8, 1.2, 1.8, LEATHER_A if k % 2 == 0 else LEATHER_B)
    w.box(0, 15.8, 0, 6.2, 1.1, 2.2, GOLD, top=GOLD_HI)
    for sx in (-1, 1):
        w.box(sx * 3.3, 16.4, 0, 1.0, 1.4, 1.8, GOLD_LO)
    w.box(0, 16.4, 1.2, 1.4, 1.2, 0.5, SUN_A)
    w.box(0, 16.4, -1.2, 1.4, 1.2, 0.5, SUN_A)
    y, n = 16.9, 8
    for k in range(n):
        t = k / (n - 1)
        h = 1.6 if k < n - 1 else 1.1
        width = 2.8 - 1.8 * t
        w.box(0, y, 0, width, h, 0.9, STEEL, top=STEEL_HI)
        w.box(0, y, 0, max(0.5, width * 0.28), h, 1.2, lerp(SUN_A, SUN_B, t))  # مجرى الفجر
        y += h
    w.box(0, y, 0, 0.7, 0.9, 0.7, STEEL_HI)
    w.save()
    return w


# ───────────────────────── ساطور الجمر ─────────────────────────
def cleaver():
    w = Weapon("ember_cleaver")
    IRON, IRON_HI, IRON_LO = (58, 56, 62), (104, 100, 110), (30, 28, 34)
    EMB, EMB_HI = (255, 112, 28), (255, 196, 70)
    WOOD_A, WOOD_B = (92, 58, 34), (62, 38, 22)
    # قبضة خشب بحلقة
    w.box(0, 5.5, 0, 3.2, 1.2, 3.2, IRON, top=IRON_HI)
    for k in range(7):
        w.box(0, 6.7 + k * 1.5, 0, 2.2, 1.5, 2.2, WOOD_A if k % 2 == 0 else WOOD_B)
    w.box(0, 17.2, 0, 3.4, 1.2, 3.0, IRON, top=IRON_HI)
    # الرأس العريض: جسم + ظهر سميك + حد
    w.box(0.3, 18.4, 0, 6.4, 13.0, 1.4, IRON, top=IRON_HI)           # الشفرة
    w.box(-3.3, 18.2, 0, 1.6, 13.6, 2.4, IRON_LO, top=IRON)          # الظهر
    w.box(3.7, 19.0, 0, 0.8, 11.6, 0.9, IRON_HI)                      # حافة الحد
    w.box(0.3, 31.2, 0, 6.4, 1.0, 1.4, IRON_HI)                       # أعلى
    w.box(1.8, 32.0, 0, 3.2, 0.8, 1.2, IRON)                          # قطع مائل
    # شقوق الجمر المتوهجة (زجزاج على الوجهين)
    zig = [(-1.2, 20.0), (-0.2, 21.8), (-1.4, 23.6), (0.0, 25.4), (-1.0, 27.2), (0.4, 29.0)]
    for sz in (-1, 1):
        for i, (x, yy) in enumerate(zig):
            w.box(x, yy, sz * 0.78, 1.0, 1.9, 0.3, EMB_HI if i % 2 else EMB)
    # فتحة التعليق (فراغ يظهر بالتبديل)
    w.box(2.2, 27.0, 0, 0.8, 0.8, 1.6, IRON_LO)
    w.save()
    return w


# ───────────────────────── سيف الظل ─────────────────────────
def shadow_blade():
    w = Weapon("shadow_blade")
    BLK, BLK_HI = (22, 18, 34), (52, 44, 78)
    PUR, PUR_HI, PUR_GLOW = (86, 54, 160), (150, 106, 236), (208, 170, 255)
    GEM = (180, 90, 255)
    w.box(0, 7.0, 0, 2.4, 1.6, 2.4, BLK_HI)
    for k in range(7):
        w.box(0, 8.6 + k * 1.2, 0, 1.7, 1.2, 1.7, BLK if k % 2 == 0 else BLK_HI)
    # حارس زاوي (أجنحة مائلة)
    w.box(0, 17.0, 0, 3.0, 1.2, 2.4, BLK_HI)
    for sx in (-1, 1):
        w.box(sx * 2.4, 17.6, 0, 1.8, 1.0, 2.0, BLK)
        w.box(sx * 3.4, 18.4, 0, 1.4, 1.0, 1.6, BLK_HI)
        w.box(sx * 4.2, 19.2, 0, 1.0, 1.0, 1.2, PUR)
    w.box(0, 17.4, 1.3, 1.2, 1.2, 0.5, GEM)
    w.box(0, 17.4, -1.3, 1.2, 1.2, 0.5, GEM)
    y, n = 18.2, 15
    for k in range(n):
        t = k / (n - 1)
        h = 1.6 if k < n - 1 else 1.0
        width = 2.4 - 1.2 * t
        w.box(0, y, 0, width * 0.6, h, 1.0, lerp(BLK, PUR, 0.25 + 0.4 * t))
        w.box(width * 0.4, y, 0, width * 0.4, h, 0.8, PUR_HI if k % 3 else PUR_GLOW)
        w.box(-width * 0.4, y, 0, width * 0.4, h, 0.8, PUR)
        if k % 2 == 1 and k < n - 3:  # أسنان خفيفة على الحد
            w.box(width * 0.8, y + 0.3, 0, 0.5, 0.9, 0.6, PUR_GLOW)
        y += h
    w.box(0, y, 0, 0.7, 0.9, 0.7, PUR_GLOW)
    w.save()
    return w


# ───────────────────────── مخالب الظل ─────────────────────────
def claws():
    w = Weapon("shadow_claws")
    BLK, BLK_HI = (24, 20, 36), (60, 50, 88)
    PUR, PUR_HI, GLOW = (96, 60, 176), (160, 116, 240), (214, 180, 255)
    LEATHER = (60, 44, 44)
    # قبضة قبضة الكف
    w.box(0, 6.5, 0, 4.4, 1.4, 2.4, BLK_HI)
    for k in range(4):
        w.box(0, 8.0 + k * 1.4, 0, 4.0, 1.4, 2.2, LEATHER if k % 2 == 0 else BLK)
    w.box(0, 13.6, 0, 5.6, 1.4, 2.6, BLK_HI, top=PUR)
    # ثلاث شفرات متوازية تنحني للخارج
    for i, sx in enumerate((-2.0, 0.0, 2.0)):
        length = 12 if i == 1 else 10
        y, n = 15.0, 8 if i == 1 else 7
        for k in range(n):
            t = k / (n - 1)
            h = length / n
            width = 1.5 - 1.1 * t
            off = sx + (0.28 * (i - 1)) * k * 0.6 + 0.0
            w.box(off, y, 0, width, h, 0.9, lerp(BLK, PUR, 0.3 + 0.5 * t), top=GLOW)
            w.box(off + width * 0.35, y, 0, width * 0.35, h, 1.1, PUR_HI if k % 3 else GLOW)
            y += h
    w.save()
    return w


# ───────────────────────── مطرقة الصخر ─────────────────────────
def maul():
    w = Weapon("stone_maul")
    ST_A, ST_B, ST_C = (118, 120, 116), (92, 94, 92), (150, 152, 146)
    CRACK, MOSS = (50, 52, 50), (80, 120, 64)
    WOOD_A, WOOD_B = (84, 56, 34), (58, 38, 24)
    IRON = (70, 70, 78)
    w.box(0, 0.0, 0, 2.8, 1.2, 2.8, IRON)
    for k in range(17):
        w.box(0, 1.2 + k * 1.5, 0, 1.8, 1.5, 1.8, WOOD_A if k % 2 == 0 else WOOD_B)
    w.box(0, 26.4, 0, 2.6, 1.0, 2.6, IRON)
    # الرأس الصخري: كتل متراكبة
    w.box(0, 27.4, 0, 9.0, 7.0, 7.0, ST_A, top=ST_C)
    w.box(0, 27.0, 0, 7.6, 1.0, 5.8, ST_B)
    w.box(0, 34.0, 0, 7.4, 1.4, 5.6, ST_B, top=ST_C)
    w.box(-3.2, 29.0, 3.55, 2.6, 3.6, 0.4, ST_C)
    w.box(3.0, 31.0, -3.55, 3.0, 3.0, 0.4, ST_C)
    for sx, yy in ((-1.5, 29.5), (0.8, 30.6), (-0.4, 32.0)):  # شقوق
        w.box(sx, yy, 3.52, 0.5, 2.2, 0.2, CRACK)
        w.box(sx + 0.5, yy + 0.4, -3.52, 0.5, 2.0, 0.2, CRACK)
    w.box(2.8, 33.4, 3.5, 2.4, 0.6, 0.3, MOSS)
    # أطواق حديد على الرأس
    for sx in (-4.65, 4.65):
        w.box(sx, 27.4, 0, 0.5, 7.0, 7.2, IRON)
    w.save()
    return w


# ───────────────────────── رمح الغروب ─────────────────────────
def spear():
    w = Weapon("sunset_spear")
    WOOD_A, WOOD_B = (96, 50, 34), (66, 34, 24)
    RED, RED_HI = (196, 54, 42), (255, 120, 70)
    GOLD, GOLD_HI = (232, 184, 66), (255, 236, 150)
    STEEL, STEEL_HI = (222, 214, 206), (255, 244, 232)
    w.box(0, -5.0, 0, 2.2, 1.0, 2.2, GOLD)
    for k in range(26):
        w.box(0, -4.0 + k * 1.4, 0, 1.3, 1.4, 1.3, WOOD_A if k % 2 == 0 else WOOD_B)
    for k in range(5):                          # لف قماش أحمر عند القبضة
        w.box(0, 9.5 + k * 1.2, 0, 1.8, 1.2, 1.8, RED if k % 2 == 0 else RED_HI)
    top = -4.0 + 26 * 1.4
    w.box(0, top, 0, 2.8, 1.2, 2.8, GOLD, top=GOLD_HI)
    for sx in (-1, 1):                          # شراشيب حمراء
        w.box(sx * 1.6, top - 3.0, 0, 0.7, 3.2, 0.7, RED)
        w.box(sx * 1.9, top - 4.6, 0, 0.6, 1.8, 0.6, RED_HI)
    # رأس الرمح على شكل ورقة (معيّن)
    y = top + 1.2
    widths = [1.8, 3.0, 3.8, 3.6, 3.0, 2.2, 1.4, 0.8]
    for k, wd in enumerate(widths):
        w.box(0, y, 0, wd, 1.5, 0.9, STEEL if k % 2 == 0 else STEEL_HI)
        w.box(0, y, 0, 0.5, 1.5, 1.2, RED if k < 5 else RED_HI)   # مجرى أحمر
        y += 1.5
    w.save()
    return w


# ───────────────────────── حركات المسك ─────────────────────────
def save_animations():
    anims = {}
    for ident, h in HOLD.items():
        for key, tag in (("fp", "fp"), ("tp", "tp")):
            p = h[key]
            anims[f"animation.sh.hold_{ident}_{tag}"] = {
                "loop": True,
                "bones": {"sh_weapon": {"position": p["pos"], "rotation": p["rot"], "scale": p["scale"]}},
            }
    os.makedirs(os.path.join(RP, "animations"), exist_ok=True)
    with open(os.path.join(RP, "animations", "sh_hold.animation.json"), "w") as f:
        json.dump({"format_version": "1.10.0", "animations": anims}, f, indent=1)


# ───────────────────────── معاينة (إسقاط متوازي بسيط) ─────────────────────────
def preview(weapons, out):
    cell = 340
    views = [(0, 0), (90, 0), (35, 18)]
    sheet = Image.new("RGB", (cell * len(views), cell * len(weapons)), (40, 42, 52))
    for r, w in enumerate(weapons):
        # أقصى امتداد
        mins = np.array([1e9] * 3); maxs = np.array([-1e9] * 3)
        for c in w.cubes:
            o = np.array(c["origin"]); s = np.array(c["size"])
            mins = np.minimum(mins, o); maxs = np.maximum(maxs, o + s)
        ext = max(maxs[1] - mins[1], 1)
        scale = (cell * 0.9) / ext
        cy = (maxs[1] + mins[1]) / 2
        for ci, (yaw, pit) in enumerate(views):
            img = Image.new("RGB", (cell, cell), (40, 42, 52))
            d = ImageDraw.Draw(img)
            ya, pa = math.radians(yaw), math.radians(pit)
            quads = []
            for c in w.cubes:
                o = np.array(c["origin"], dtype=float); s = np.array(c["size"], dtype=float)
                x0, y0, z0 = o; x1, y1, z1 = o + s
                col = {f: w.palette[c["uv"][f]["uv"][0] + 16 * c["uv"][f]["uv"][1]][:3] for f in FACES}
                P = {"n": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], "s": [(x1, y1, z1), (x0, y1, z1), (x0, y0, z1), (x1, y0, z1)],
                     "e": [(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)], "w": [(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)],
                     "u": [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], "d": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]}
                names = {"n": "north", "s": "south", "e": "east", "w": "west", "u": "up", "d": "down"}
                for k, pts in P.items():
                    pr = []
                    for (x, y, z) in pts:
                        xr = x * math.cos(ya) + z * math.sin(ya)
                        zr = -x * math.sin(ya) + z * math.cos(ya)
                        yr = y * math.cos(pa) - zr * math.sin(pa)
                        zr2 = y * math.sin(pa) + zr * math.cos(pa)
                        pr.append((xr, yr, zr2))
                    n = np.cross(np.array(pr[1]) - np.array(pr[0]), np.array(pr[3]) - np.array(pr[0]))
                    if n[2] <= 0:  # وجه خلفي
                        continue
                    depth = np.mean([p[2] for p in pr])
                    sh = {"n": 0.85, "s": 0.85, "e": 0.7, "w": 0.7, "u": 1.0, "d": 0.5}[k]
                    quads.append((depth, pr, shade(col[names[k]], sh)))
            quads.sort(key=lambda q: -q[0])
            for _, pr, col in quads:
                pts = [(cell / 2 + p[0] * scale, cell / 2 - (p[1] - cy) * scale) for p in pr]
                d.polygon(pts, fill=col)
            sheet.paste(img, (ci * cell, r * cell))
    sheet.save(out)


if __name__ == "__main__":
    ws = [katana(), dagger(), cleaver(), shadow_blade(), claws(), maul(), spear()]
    save_animations()
    out = os.path.join(os.environ.get("PREVIEW_DIR", "/tmp"), "weapons3d.png")
    preview(ws, out)
    for w in ws:
        print(f"{w.ident:14} cubes={len(w.cubes):3} colors={len(w.palette)}")
    print("preview", out)
