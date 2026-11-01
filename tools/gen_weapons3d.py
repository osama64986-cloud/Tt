"""يولد موديلات الأسلحة 3D الأسطورية (Attachables) + تكستشراتها + حركات المسك.

الطريقة (مطابقة لرمح الـTrident الرسمي بماينكرافت):
  * عظمة واحدة اسمها sh_weapon، pivot=[0,24,0]، وبها binding على خانة الأيتم.
  * السلاح مبني بطول المحور Y. منطقة القبضة y=5..16 (تغطي مكان اليد المحتمل) والحارس بعدها.
  * حركة المسك (أول شخص / ثالث شخص) قيمها الأساسية من الـTrident الرسمي، مع scale لكل سلاح.
  * التكستشر لوحة ألوان 16x16، وكل وجه مكعب يشير لبكسل لونه (UV لكل وجه).
  * ملفات الـJSON تنكتب مضغوطة (سطر لكل ملف) حتى ما تتضخم الـdiff بـGitHub.
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
    "dark_katana": {"fp": {**TRIDENT_FP, "scale": 0.78}, "tp": {**TRIDENT_TP, "scale": 0.78}},
    "dawn_dagger": {"fp": {**TRIDENT_FP, "scale": 1.0}, "tp": {**TRIDENT_TP, "scale": 1.0}},
    "ember_cleaver": {"fp": {**TRIDENT_FP, "scale": 0.82}, "tp": {**TRIDENT_TP, "scale": 0.82}},
    "shadow_blade": {"fp": {**TRIDENT_FP, "scale": 0.82}, "tp": {**TRIDENT_TP, "scale": 0.82}},
    "shadow_claws": {"fp": {**TRIDENT_FP, "scale": 0.95}, "tp": {**TRIDENT_TP, "scale": 0.95}},
    "stone_maul": {"fp": {**TRIDENT_FP, "scale": 0.78}, "tp": {**TRIDENT_TP, "scale": 0.78}},
    "sunset_spear": {"fp": {**TRIDENT_FP, "scale": 0.68}, "tp": {**TRIDENT_TP, "scale": 0.68}},
}


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


class Weapon:
    def __init__(self, ident):
        self.ident = ident
        self.cubes = []
        self.palette = []

    def _idx(self, rgb):
        rgba = tuple(int(round(v)) for v in rgb[:3]) + (255,)
        if rgba not in self.palette:
            assert len(self.palette) < 256, "اللوحة ممتلئة"
            self.palette.append(rgba)
        return self.palette.index(rgba)

    def box(self, cx, y0, cz, w, h, d, color, top=None, side=None, rz=None, pivot=None):
        """مكعب مركزه (cx, cz) وقاعدته y0. top/side ألوان بديلة. rz دوران حول Z (للمراوح المتماثلة فقط)."""
        def uv(c):
            i = self._idx(c)
            return {"uv": [i % 16, i // 16], "uv_size": [1, 1]}
        main = uv(color)
        t = uv(top) if top else main
        s = uv(side) if side else main
        cube = {
            "origin": [round(cx - w / 2, 3), round(y0, 3), round(cz - d / 2, 3)],
            "size": [round(w, 3), round(h, 3), round(d, 3)],
            "uv": {"north": main, "south": main, "east": s, "west": s, "up": t, "down": s},
        }
        if rz:
            cube["pivot"] = [round(v, 3) for v in (pivot or (cx, y0, cz))]
            cube["rotation"] = [0, 0, rz]
        self.cubes.append(cube)

    def blade(self, y, length, n, width_fn, thick_fn, off_fn, col_back, col_edge, edge_split=0.45, shine=None, tip=None):
        """نصل من قطاعات: ظهر + حد. الدوال تأخذ t (0..1)."""
        h = length / n
        for k in range(n):
            t = k / max(1, n - 1)
            wd, th, off = width_fn(t), thick_fn(t), off_fn(t)
            edge = wd * edge_split
            back = wd - edge
            cb = col_back(t)
            ce = shine if (shine and k % 4 == 1) else col_edge(t)
            self.box(off - wd / 2 + back / 2, y + k * h, 0, back, h * 1.02, th, cb, top=cb)
            self.box(off + wd / 2 - edge / 2, y + k * h, 0, edge, h * 1.02, th * 0.78, ce, top=ce)
        if tip:
            self.box(off_fn(1) + 0.15, y + length, 0, tip[0], tip[1], tip[2], tip[3])

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
            json.dump(geo, f, separators=(",", ":"))
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
            json.dump(att, f, separators=(",", ":"))


def wrap(w, y0, n, h, width, ca, cb, depth=None):
    """قبضة ملفوفة: قطاعات متبادلة."""
    for k in range(n):
        w.box(0, y0 + k * h, 0, width, h, depth or width, ca if k % 2 == 0 else cb, top=shade(ca, 1.25))


def shards(w, pts, cols):
    """شظايا عائمة حول السلاح (مثل صورة المهارة الفعالة)."""
    for i, (x, y, z, s) in enumerate(pts):
        w.box(x, y, z, s, s, s, cols[i % len(cols)])


# ───────────────────────── كاتانا الهاوية ─────────────────────────
def katana():
    w = Weapon("dark_katana")
    SPINE, MID, EDGE, SHINE = (18, 20, 50), (50, 46, 112), (120, 106, 205), (200, 190, 252)
    GUARD, GUARD_HI = (26, 32, 74), (66, 80, 146)
    GOLD, GOLD_HI = (240, 200, 64), (255, 240, 154)
    WA, WB = (62, 64, 74), (28, 30, 38)
    POM, POM_HI = (34, 60, 132), (90, 130, 214)
    SILK = (58, 96, 190)
    # نهاية القبضة + حبل حرير أزرق
    w.box(0, 5.2, 0, 2.8, 1.6, 2.8, POM, top=POM_HI)
    w.box(0, 6.8, 0, 2.0, 0.5, 2.0, GOLD)
    for k in range(3):
        w.box(1.7 + k * 0.1, 3.2 - k * 1.0, 0.0, 0.7, 1.4, 0.7, SILK)
    w.box(1.9, 0.6, 0.0, 1.0, 1.0, 1.0, POM_HI)
    # القبضة (ito) بقطاعات
    wrap(w, 7.3, 7, 1.5, 1.95, WA, WB)
    for k in (1, 3, 5):                      # مينوكي ذهبي
        w.box(0, 7.9 + k * 1.5, 1.0, 0.7, 0.7, 0.4, GOLD)
        w.box(0, 7.9 + k * 1.5, -1.0, 0.7, 0.7, 0.4, GOLD)
    w.box(0, 17.8, 0, 2.5, 0.7, 2.5, GOLD, top=GOLD_HI)
    # تسوبا (الحارس) بأجنحة مفصصة
    w.box(0, 18.5, 0, 7.0, 1.2, 2.8, GUARD, top=GUARD_HI)
    for sx in (-1, 1):
        w.box(sx * 3.6, 19.7, 0, 1.3, 1.5, 2.2, GUARD)
        w.box(sx * 4.2, 21.0, 0, 0.9, 1.1, 1.7, GUARD_HI)
        w.box(sx * 2.0, 19.7, 0, 1.4, 0.8, 2.4, GUARD_HI)
        w.box(sx * 4.4, 18.5, 0, 0.8, 0.8, 2.0, GOLD)
    for sz in (-1, 1):
        w.box(0, 18.6, sz * 1.5, 1.7, 1.5, 0.5, GOLD, top=GOLD_HI)
        w.box(0, 18.9, sz * 1.8, 0.7, 0.7, 0.3, (255, 250, 200))
    # النصل المنحني بتموج الهامون
    n = 15
    w.blade(19.8, 28, n,
            width_fn=lambda t: 3.7 - 2.2 * t,
            thick_fn=lambda t: 1.3 - 0.45 * t,
            off_fn=lambda t: 2.5 * t * t,
            col_back=lambda t: lerp(SPINE, MID, 0.15 + 0.5 * t),
            col_edge=lambda t: lerp(MID, EDGE, 0.55 + 0.35 * math.sin(t * 14) ** 2),
            shine=SHINE, tip=(1.0, 1.1, 0.8, SHINE))
    # رونات بنفسجية بالنصل
    for k, yy in enumerate((22.5, 25.5, 28.5, 31.5)):
        t = (yy - 19.8) / 28
        for sz in (-1, 1):
            w.box(2.5 * t * t - 0.4, yy, sz * 0.62, 0.5, 1.1, 0.2, (198, 130, 255) if k % 2 else (150, 100, 255))
    shards(w, [(-3.2, 30, 1.0, 0.7), (4.8, 33, -1.2, 0.6), (-2.4, 37, -0.6, 0.55), (6.5, 38, 1.0, 0.5),
               (-4.0, 26, -1.2, 0.5), (5.2, 27, 1.4, 0.6), (-1.0, 42, 1.2, 0.5), (6.0, 43, -0.6, 0.45)],
           [(160, 100, 255), (110, 90, 255), (220, 130, 255), (96, 150, 255)])
    w.save()
    return w


# ───────────────────────── خنجر الفجر (منحني مثل الأيقونة) ─────────────────────────
def dagger():
    w = Weapon("dawn_dagger")
    GOLD, GOLD_HI, GOLD_LO = (226, 178, 62), (255, 232, 140), (150, 108, 30)
    CREAM, WHITE = (255, 246, 214), (255, 253, 240)
    SUN_A, SUN_B = (255, 98, 52), (255, 190, 100)
    LEATHER_A, LEATHER_B = (118, 76, 44), (78, 48, 28)
    # نهاية القبضة: جوهرة شروق برتقالية بغطاء ذهبي
    w.box(0, 5.0, 0, 2.4, 0.8, 2.4, GOLD, top=GOLD_HI)
    w.box(0, 5.8, 0, 2.0, 1.8, 2.0, SUN_A, top=SUN_B)
    w.box(0, 7.6, 0, 2.6, 0.7, 2.6, GOLD, top=GOLD_HI)
    wrap(w, 8.3, 6, 1.3, 1.9, LEATHER_A, LEATHER_B)
    w.box(0, 16.0, 0, 2.6, 0.6, 2.6, GOLD)
    # حارس صغير بأجنحة
    w.box(0, 16.6, 0, 6.4, 1.1, 2.2, GOLD, top=GOLD_HI)
    for sx in (-1, 1):
        w.box(sx * 3.4, 17.1, 0, 1.0, 1.5, 1.8, GOLD_LO)
        w.box(sx * 3.7, 18.4, 0, 0.7, 1.0, 1.4, GOLD)
    w.box(0, 16.9, 1.2, 1.5, 1.3, 0.5, SUN_A)
    w.box(0, 16.9, -1.2, 1.5, 1.3, 0.5, SUN_A)
    # النصل المنحني (قريب من الأيقونة: بطن عريض ثم انحناء للطرف)
    def wd(t): return 3.2 + 1.8 * math.sin(t * math.pi * 0.8) - 2.4 * t ** 2.2
    w.blade(17.7, 16.5, 12,
            width_fn=wd, thick_fn=lambda t: 1.1 - 0.4 * t,
            off_fn=lambda t: 3.6 * t ** 2,
            col_back=lambda t: lerp(GOLD, CREAM, 0.25 + 0.6 * t),
            col_edge=lambda t: lerp(CREAM, WHITE, t),
            edge_split=0.5, shine=WHITE, tip=(0.9, 1.0, 0.7, WHITE))
    for k, yy in enumerate((19.4, 21.4, 23.4, 25.4)):  # مجرى الفجر
        t = (yy - 17.7) / 16.5
        for sz in (-1, 1):
            w.box(3.6 * t * t, yy, sz * 0.52, 0.55, 1.6, 0.2, lerp(SUN_A, SUN_B, k / 3))
    # دوامة ذهب تلتف حول النصل (مثل الصورة)
    for k in range(18):
        a = k * 0.7
        t = k / 17
        cx = 3.6 * t * t
        r = 3.0 - 1.2 * t
        w.box(cx + math.cos(a) * r, 18.4 + k * 0.95, math.sin(a) * r, 0.6, 0.45, 0.6, GOLD_HI if k % 2 else (255, 214, 110))
    shards(w, [(-2.8, 24, 1.4, 0.4), (6.2, 30, -1.2, 0.4)], [WHITE, GOLD_HI])
    w.save()
    return w


# ───────────────────────── ساطور الجمر (قاطع عريض بحد متوهج) ─────────────────────────
def cleaver():
    w = Weapon("ember_cleaver")
    IRON, IRON_HI, IRON_LO = (62, 60, 68), (118, 114, 126), (30, 28, 36)
    EMB, EMB_HI, EMB_W = (255, 104, 24), (255, 176, 56), (255, 232, 140)
    WOOD_A, WOOD_B = (96, 60, 36), (62, 38, 22)
    # حلقة نهاية + قبضة خشب بأطواق حديد
    w.box(0, 4.6, 0, 3.6, 1.2, 3.0, IRON, top=IRON_HI)
    w.box(0, 5.8, 0, 2.2, 0.6, 2.2, EMB)
    wrap(w, 6.4, 7, 1.5, 2.3, WOOD_A, WOOD_B)
    for yy in (8.4, 12.9):
        w.box(0, yy, 0, 2.9, 0.6, 2.9, IRON, top=IRON_HI)
    w.box(0, 16.9, 0, 4.0, 1.3, 3.2, IRON, top=IRON_HI)
    # حارس جمر
    w.box(0, 18.2, 0, 5.4, 1.2, 3.0, IRON_LO, top=IRON)
    w.box(0, 18.4, 1.6, 1.4, 1.0, 0.4, EMB_HI)
    w.box(0, 18.4, -1.6, 1.4, 1.0, 0.4, EMB_HI)
    # شفرة عريضة من أعمدة (محيط منحني: بطن أمامي وقطع مائل بالأعلى)
    cols = 9
    x0 = -3.0
    heights = [11.5, 13.0, 14.3, 15.2, 15.8, 15.6, 14.4, 12.6, 10.2]
    for i in range(cols):
        x = x0 + i * 0.78
        t = i / (cols - 1)
        hh = heights[i]
        base = lerp(IRON_LO, IRON, 0.3 + 0.5 * t)
        w.box(x, 19.4, 0, 0.80, hh, 1.5 - 0.35 * t, base, top=IRON_HI)
        if i >= cols - 3:  # حد الجمر المتوهج
            w.box(x + 0.05, 19.4 + 0.2, 0, 0.7, hh - 0.2, 1.2, lerp(EMB, EMB_HI, (i - (cols - 3)) / 2))
            w.box(x, 19.4 + hh - 0.5, 0, 0.8, 0.6, 1.0, EMB_W)
    # ظهر سميك بمسامير
    w.box(-3.65, 19.2, 0, 1.3, 12.2, 2.6, IRON_LO, top=IRON)
    for yy in (21.0, 25.0, 29.0):
        w.box(-3.65, yy, 1.42, 0.7, 0.7, 0.3, IRON_HI)
        w.box(-3.65, yy, -1.42, 0.7, 0.7, 0.3, IRON_HI)
    # شقوق جمر زجزاج على الوجهين
    zig = [(-1.8, 21.0), (-0.6, 22.8), (-1.9, 24.6), (-0.3, 26.4), (-1.4, 28.2), (0.2, 30.0)]
    for sz in (-1, 1):
        for i, (x, yy) in enumerate(zig):
            w.box(x, yy, sz * 0.84, 0.9, 1.9, 0.26, EMB_HI if i % 2 else EMB)
    # ثقب تعليق + أسنان عند الطرف
    w.box(-0.4, 31.4, 0, 1.3, 1.3, 1.8, (18, 16, 22))
    for sx in (2.2, 3.4):
        w.box(sx, 17.0 + 3.0, 0, 0.8, 1.0, 1.0, EMB_HI)
    # ألسنة لهب ترتفع من الحد والطرف (برتقالي ← ذهبي ← أبيض)
    FL = [(255, 80, 20), (255, 140, 30), (255, 200, 70), (255, 240, 170)]
    for i, (x, base, hh) in enumerate(((0.9, 33.6, 3.2), (1.7, 33.2, 4.2), (2.5, 32.2, 3.4), (3.2, 30.6, 2.6), (-0.2, 34.6, 2.4), (-1.3, 34.0, 2.0))):
        for k in range(4):
            ww = 1.0 - k * 0.2
            w.box(x + math.sin(i + k) * 0.25, base + k * hh / 4, 0, ww, hh / 4 + 0.05, ww * 0.9, FL[k])
    for i, yy in enumerate((22.0, 25.5, 29.0)):
        for k in range(3):
            w.box(3.7 + k * 0.45, yy + k * 0.8, 0, 0.7 - k * 0.15, 0.9, 0.6, FL[k + 1])
    w.save()
    return w


# ───────────────────────── سيف الظل (حد جليدي مضيء) ─────────────────────────
def shadow_blade():
    """سيف طويل مستقيم بحدين: فولاذ أزرق، خط نور سماوي بالنص، حارس مجنح بجوهرة، وشرائط ريح تلتف حول النصل."""
    w = Weapon("shadow_blade")
    STEEL, STEEL_HI, STEEL_LO = (70, 110, 190), (150, 196, 255), (34, 52, 110)
    CORE, CORE_W = (90, 220, 255), (225, 250, 255)
    NAVY, NAVY_HI = (22, 30, 70), (48, 62, 120)
    SILV, SILV_HI = (184, 196, 220), (236, 242, 255)
    GEM, GEM_HI = (40, 140, 255), (160, 220, 255)
    WIND, WIND_HI = (120, 210, 255), (205, 240, 255)
    # الحلق + القبضة الملفوفة
    w.box(0, 4.4, 0, 2.6, 1.0, 2.6, SILV, top=SILV_HI)
    w.box(0, 5.4, 0, 1.8, 1.4, 1.8, GEM, top=GEM_HI)
    w.box(0, 6.8, 0, 2.4, 0.6, 2.4, SILV)
    wrap(w, 7.4, 7, 1.3, 1.8, NAVY, NAVY_HI)
    w.box(0, 16.5, 0, 2.6, 0.7, 2.6, SILV, top=SILV_HI)
    # الحارس: جناحان فضيان ينحنيان للأعلى، وبالنص جوهرة زرقاء على الوجهين
    w.box(0, 17.2, 0, 4.0, 1.5, 2.6, SILV, top=SILV_HI)
    for sx in (-1, 1):
        w.box(sx * 3.0, 17.4, 0, 2.2, 1.1, 2.0, SILV)
        w.box(sx * 4.6, 17.9, 0, 1.6, 1.1, 1.6, SILV_HI)
        w.box(sx * 5.6, 18.7, 0, 1.0, 1.4, 1.2, STEEL_HI)
        w.box(sx * 6.0, 20.0, 0, 0.6, 1.0, 0.8, CORE_W)
    w.box(0, 17.4, 1.35, 1.6, 1.6, 0.4, GEM)
    w.box(0, 17.4, -1.35, 1.6, 1.6, 0.4, GEM)
    w.box(0, 17.8, 1.55, 0.7, 0.7, 0.2, GEM_HI)
    w.box(0, 17.8, -1.55, 0.7, 0.7, 0.2, GEM_HI)
    # النصل: حدين متناظرين يضيقون للطرف، وخط نور بالنص
    y0, L, n = 18.7, 28.0, 16
    h = L / n
    for k in range(n):
        t = k / (n - 1)
        wd = 3.0 - 0.9 * t - (1.4 * (t - 0.82) / 0.18 if t > 0.82 else 0)
        wd = max(0.7, wd)
        yy = y0 + k * h
        w.box(0, yy, 0, wd, h * 1.02, 0.9, lerp(STEEL_LO, STEEL, 0.4 + 0.5 * t), top=STEEL_HI)
        for sx in (-1, 1):
            w.box(sx * (wd / 2 - 0.25), yy, 0, 0.5, h * 1.02, 0.6, STEEL_HI if k % 3 else SILV_HI)
        w.box(0, yy, 0, 0.5, h * 1.02, 1.05, CORE if k % 4 else CORE_W)
    w.box(0, y0 + L, 0, 0.6, 1.1, 0.6, CORE_W)
    # شرائط الريح: لولب من شرائح رفيعة تلتف حول النصل
    for k in range(22):
        a = k * 0.62
        r = 2.6 + 0.5 * math.sin(k * 0.5)
        yy = 20.0 + k * 1.15
        w.box(math.cos(a) * r, yy, math.sin(a) * r, 0.9 if k % 3 else 1.3, 0.35, 0.9 if k % 3 else 1.3, WIND if k % 2 else WIND_HI)
    shards(w, [(-3.6, 30, 1.2, 0.45), (3.8, 36, -1.0, 0.45), (-2.8, 42, -0.8, 0.4), (1.2, 49, 1.0, 0.4)], [WIND_HI, CORE_W])
    w.save()
    return w


# ───────────────────────── مخالب الظل (كاتار بثلاث شفرات) ─────────────────────────
def claws():
    w = Weapon("shadow_claws")
    BLK, BLK_HI = (22, 18, 34), (60, 50, 90)
    LEATH = (66, 48, 52)
    PUR, PUR_HI, GLOW, WHITE = (88, 54, 170), (150, 110, 238), (212, 178, 255), (248, 240, 255)
    SIL = (170, 178, 200)
    # شرائط المعصم
    for sx, d in ((-1.4, 0), (1.4, 0)):
        w.box(sx, 1.6, 0, 0.9, 5.0, 0.6, PUR)
    w.box(0, 6.0, 0, 3.8, 1.2, 2.4, BLK_HI)
    wrap(w, 7.2, 5, 1.5, 3.4, LEATH, BLK, depth=2.2)
    w.box(0, 14.7, 0, 6.2, 1.3, 2.6, BLK_HI, top=SIL)
    # لوحة المفاصل بجواهر
    w.box(0, 16.0, 0, 7.4, 1.8, 2.8, BLK, top=BLK_HI)
    for sx in (-2.6, 0, 2.6):
        w.box(sx, 16.4, 1.45, 1.2, 1.0, 0.4, PUR_HI)
        w.box(sx, 16.4, -1.45, 1.2, 1.0, 0.4, PUR_HI)
    w.box(0, 17.8, 0, 7.0, 0.7, 2.6, SIL)
    # ثلاث شفرات: الوسطى أطول، الجانبية تنفرج للخارج بإزاحة تدريجية (بدون دوران مكعبات حتى يتطابق بكل الإصدارات)
    for sx, spread, length in ((-2.4, -3.4, 13.5), (0.0, 0.0, 17.0), (2.4, 3.4, 13.5)):
        n = 9
        h = length / n
        for k in range(n):
            t = k / (n - 1)
            width = 1.8 - 1.3 * t
            off = sx + spread * t ** 1.3
            c_back = lerp(BLK, PUR, 0.25 + 0.5 * t)
            c_edge = lerp(PUR_HI, WHITE, t)
            yy = 18.5 + k * h
            w.box(off - width * 0.2, yy, 0, width * 0.62, h * 1.03, 1.0, c_back)
            w.box(off + width * 0.32, yy, 0, width * 0.42, h * 1.03, 0.8, c_edge)
        w.box(sx + spread, 18.5 + length, 0, 0.55, 0.8, 0.6, WHITE)
    shards(w, [(-5.0, 27, 0.8, 0.5), (5.0, 29, -0.8, 0.5), (0.0, 38, 1.0, 0.5), (-3.5, 34, -0.6, 0.45), (3.8, 35, 0.8, 0.45)],
           [GLOW, PUR_HI, (120, 190, 255)])
    w.save()
    return w


# ───────────────────────── مطرقة الصخر ─────────────────────────
def maul():
    w = Weapon("stone_maul")
    ST_A, ST_B, ST_C, ST_D = (120, 122, 118), (92, 94, 92), (152, 154, 148), (70, 72, 70)
    CRACK, MOSS, RUNE = (46, 48, 46), (82, 126, 66), (110, 255, 190)
    WOOD_A, WOOD_B = (88, 58, 36), (60, 40, 26)
    IRON, IRON_HI = (66, 66, 76), (110, 110, 124)
    CLOTH = (150, 56, 48)
    w.box(0, 0.0, 0, 3.0, 1.4, 3.0, IRON, top=IRON_HI)
    w.box(0, 1.4, 0, 1.2, 1.0, 1.2, IRON_HI)
    for k in range(16):
        w.box(0, 2.0 + k * 1.5, 0, 1.9, 1.5, 1.9, WOOD_A if k % 2 == 0 else WOOD_B)
    for k in range(5):  # لف قماش عند القبضة
        w.box(0, 8.0 + k * 1.2, 0, 2.5, 0.9, 2.5, CLOTH if k % 2 == 0 else shade(CLOTH, 1.3))
    for yy in (4.5, 14.5, 22.0):
        w.box(0, yy, 0, 2.6, 0.5, 2.6, IRON, top=IRON_HI)
    w.box(0, 26.0, 0, 3.0, 1.2, 3.0, IRON, top=IRON_HI)
    # رأس صخري: كتل متراكبة
    w.box(0, 27.2, 0, 9.4, 7.2, 7.2, ST_A, top=ST_C)
    w.box(0, 26.9, 0, 8.0, 1.0, 6.0, ST_B)
    w.box(0, 34.2, 0, 8.0, 1.6, 6.0, ST_B, top=ST_C)
    w.box(-3.4, 29.0, 3.7, 2.8, 3.8, 0.4, ST_C)
    w.box(3.2, 31.0, -3.7, 3.2, 3.2, 0.4, ST_C)
    w.box(-4.9, 28.5, 0, 0.6, 3.0, 5.0, ST_D)
    w.box(4.9, 28.5, 0, 0.6, 3.0, 5.0, ST_D)
    for sx, yy in ((-1.5, 29.4), (0.8, 30.5), (-0.4, 31.9)):
        w.box(sx, yy, 3.62, 0.5, 2.3, 0.2, CRACK)
        w.box(sx + 0.6, yy + 0.4, -3.62, 0.5, 2.1, 0.2, CRACK)
    w.box(2.8, 34.0, 3.6, 2.6, 0.6, 0.3, MOSS)
    for sx in (-4.95, 4.95):
        w.box(sx, 27.2, 0, 0.5, 7.2, 7.4, IRON, top=IRON_HI)
        w.box(sx, 30.0, 0, 0.9, 1.0, 1.0, IRON_HI)  # أشواك
    for sx in (-5.6, 5.6):
        w.box(sx, 29.4, 0, 0.9, 1.2, 1.2, IRON_HI)
    # بلورات رون خضراء مضيئة
    for (x, yy, z) in ((0.0, 30.6, 3.7), (-2.6, 32.4, 3.7), (2.6, 28.6, 3.7), (1.0, 31.4, -3.7), (-2.4, 29.4, -3.7)):
        w.box(x, yy, z, 1.1, 1.3, 0.35, RUNE)
        w.box(x, yy + 0.2, z * 1.04, 0.5, 0.7, 0.2, (220, 255, 240))
    # جوهرة زمرد كبيرة بإطار برونزي على الوجهين (مثل الصورة) + جواهر صغيرة بالأطراف
    EM, EM_HI, EM_W, BRONZE, BRONZE_HI = (40, 200, 90), (110, 245, 150), (220, 255, 230), (170, 120, 50), (225, 175, 90)
    for sz in (-1, 1):
        w.box(0, 28.9, sz * 3.75, 4.2, 4.2, 0.4, BRONZE, top=BRONZE_HI)
        w.box(0, 29.4, sz * 3.95, 3.2, 3.2, 0.4, EM, top=EM_HI)
        w.box(0, 30.0, sz * 4.15, 2.0, 2.0, 0.3, EM_HI)
        w.box(-0.4, 30.8, sz * 4.3, 0.7, 0.7, 0.2, EM_W)
    for sx in (-1, 1):
        w.box(sx * 5.25, 30.2, 0, 0.4, 1.8, 1.8, EM, top=EM_HI)
    # هالة خضراء: نقاط متوهجة تطفو حول الرأس
    shards(w, [(-6.6, 33, 0.8, 0.6), (6.8, 31, -0.8, 0.6), (0.5, 38.8, 0.4, 0.7), (-3.2, 37.2, -1.6, 0.5), (3.6, 36.6, 1.8, 0.5), (-5.4, 27.4, -1.2, 0.45), (5.8, 27.8, 1.4, 0.45)],
           [EM_HI, EM, EM_W])
    w.save()
    return w


# ───────────────────────── رمح الغروب ─────────────────────────
def spear():
    """رمح طويل: عصا خشب بأطواق ذهب، رأس أبيض عريض برونات حمراء، وشريطة حمراء طويلة تتموج من تحت الرأس."""
    w = Weapon("sunset_spear")
    WOOD_A, WOOD_B = (98, 52, 36), (66, 34, 24)
    RED, RED_HI, RED_LO = (200, 40, 40), (255, 96, 80), (130, 22, 26)
    GOLD, GOLD_HI = (232, 184, 66), (255, 238, 152)
    WHITE, WHITE_HI, WHITE_LO = (236, 232, 226), (255, 255, 250), (196, 192, 188)
    w.box(0, -5.0, 0, 2.4, 1.2, 2.4, GOLD, top=GOLD_HI)
    w.box(0, -3.8, 0, 1.6, 1.0, 1.6, RED)
    for k in range(25):
        w.box(0, -2.8 + k * 1.4, 0, 1.35, 1.4, 1.35, WOOD_A if k % 2 == 0 else WOOD_B)
    for k in range(6):
        w.box(0, 7.5 + k * 1.2, 0, 2.0, 1.0, 2.0, RED if k % 2 == 0 else RED_LO)
    for yy in (3.0, 16.5, 24.0):
        w.box(0, yy, 0, 2.0, 0.5, 2.0, GOLD, top=GOLD_HI)
    top = -2.8 + 25 * 1.4
    w.box(0, top - 0.6, 0, 2.6, 0.7, 2.6, GOLD, top=GOLD_HI)
    w.box(0, top, 0, 3.4, 1.4, 2.4, GOLD, top=GOLD_HI)
    for sx in (-1, 1):
        w.box(sx * 2.2, top + 0.3, 0, 1.2, 1.0, 1.6, GOLD_HI)
    # الرأس الأبيض: ورقة عريضة تضيق للطرف، بحافة فاتحة
    y = top + 1.4
    widths = [2.0, 3.2, 4.2, 4.6, 4.4, 3.8, 3.0, 2.2, 1.4, 0.8]
    for k, wd in enumerate(widths):
        w.box(0, y, 0, wd, 1.5, 1.0, WHITE if k % 2 == 0 else WHITE_HI, top=WHITE_HI)
        for sx in (-1, 1):
            w.box(sx * (wd / 2 - 0.2), y, 0, 0.4, 1.5, 0.7, WHITE_LO)
        y += 1.5
    w.box(0, y, 0, 0.5, 1.0, 0.5, WHITE_HI)
    # رونات حمراء محفورة على الوجهين (خط بالنص وعلامات جانبية)
    ry = top + 1.4
    for sz in (-1, 1):
        for k in range(8):
            w.box(0, ry + 0.3 + k * 1.5, sz * 0.55, 0.45, 1.1, 0.16, RED if k % 2 else RED_HI)
        for (dx, yy, ww, hh) in ((-1.0, 3.4, 0.9, 0.4), (1.0, 3.4, 0.9, 0.4), (-1.2, 6.2, 0.5, 1.2), (1.2, 6.2, 0.5, 1.2), (0.0, 9.6, 1.4, 0.4)):
            w.box(dx, ry + yy, sz * 0.55, ww, hh, 0.16, RED)
    # الشريطة الحمراء: تطلع من تحت الرأس وتتموج لتحت وللجنب
    for k in range(14):
        t = k / 13
        x = 1.6 + t * 3.4 + math.sin(t * 7) * 0.8
        yy = top - 0.4 - k * 1.05
        zz = math.sin(t * 5 + 1) * 0.8
        w.box(x, yy, zz, 1.3 - 0.4 * t, 1.1, 0.25, RED if k % 3 else RED_HI)
        if k % 4 == 1:
            w.box(x + 0.3, yy - 0.2, zz, 0.5, 0.5, 0.3, RED_LO)
    w.save()
    return w


# ───────────────────────── حركات المسك ─────────────────────────
def save_animations():
    anims = {}
    for ident, h in HOLD.items():
        for key in ("fp", "tp"):
            p = h[key]
            anims[f"animation.sh.hold_{ident}_{key}"] = {
                "loop": True,
                "bones": {"sh_weapon": {"position": p["pos"], "rotation": p["rot"], "scale": p["scale"]}},
            }
    os.makedirs(os.path.join(RP, "animations"), exist_ok=True)
    with open(os.path.join(RP, "animations", "sh_hold.animation.json"), "w") as f:
        json.dump({"format_version": "1.10.0", "animations": anims}, f, separators=(",", ":"))


# ───────────────────────── معاينة (إسقاط متوازي) ─────────────────────────
def _rot_z(pts, pivot, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for (x, y, z) in pts:
        dx, dy = x - pivot[0], y - pivot[1]
        out.append((pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c, z))
    return out


def preview(weapons, out, cell=360):
    views = [(0, 0), (90, 0), (35, 16)]
    sheet = Image.new("RGB", (cell * len(views), cell * len(weapons)), (40, 42, 52))
    for r, w in enumerate(weapons):
        mins = np.array([1e9] * 3); maxs = np.array([-1e9] * 3)
        for c in w.cubes:
            o = np.array(c["origin"]); s = np.array(c["size"])
            mins = np.minimum(mins, o); maxs = np.maximum(maxs, o + s)
        ext = max(maxs[1] - mins[1], 1)
        scale = (cell * 0.92) / ext
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
                    if "rotation" in c:
                        pts = _rot_z(pts, c["pivot"], c["rotation"][2])
                    pr = []
                    for (x, y, z) in pts:
                        xr = x * math.cos(ya) + z * math.sin(ya)
                        zr = -x * math.sin(ya) + z * math.cos(ya)
                        yr = y * math.cos(pa) - zr * math.sin(pa)
                        zr2 = y * math.sin(pa) + zr * math.cos(pa)
                        pr.append((xr, yr, zr2))
                    n = np.cross(np.array(pr[1]) - np.array(pr[0]), np.array(pr[3]) - np.array(pr[0]))
                    if n[2] <= 0:
                        continue
                    depth = np.mean([p[2] for p in pr])
                    sh = {"n": 0.88, "s": 0.88, "e": 0.72, "w": 0.72, "u": 1.0, "d": 0.5}[k]
                    quads.append((depth, pr, shade(col[names[k]], sh)))
            quads.sort(key=lambda q: -q[0])
            for _, pr, col in quads:
                pts = [(cell / 2 + p[0] * scale, cell / 2 - (p[1] - cy) * scale) for p in pr]
                d.polygon(pts, fill=col)
            sheet.paste(img, (ci * cell, r * cell))
    sheet.save(out)


ALL = [katana, dagger, cleaver, shadow_blade, claws, maul, spear]

if __name__ == "__main__":
    ws = [fn() for fn in ALL]
    save_animations()
    outdir = os.environ.get("PREVIEW_DIR", "/tmp")
    preview(ws[:4], os.path.join(outdir, "weapons3d_a.png"))
    preview(ws[4:], os.path.join(outdir, "weapons3d_b.png"))
    for w in ws:
        print(f"{w.ident:14} cubes={len(w.cubes):3} colors={len(w.palette)}")
    print("preview", outdir)
