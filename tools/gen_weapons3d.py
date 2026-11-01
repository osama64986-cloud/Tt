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
    "dawn_dagger": {"fp": {**TRIDENT_FP, "scale": 0.9}, "tp": {**TRIDENT_TP, "scale": 0.9}},
    "ember_cleaver": {"fp": {**TRIDENT_FP, "scale": 0.82}, "tp": {**TRIDENT_TP, "scale": 0.82}},
    "shadow_blade": {"fp": {**TRIDENT_FP, "scale": 0.82}, "tp": {**TRIDENT_TP, "scale": 0.82}},
    "shadow_claws": {"fp": {**TRIDENT_FP, "scale": 0.95}, "tp": {**TRIDENT_TP, "scale": 0.95}},
    "stone_maul": {"fp": {**TRIDENT_FP, "scale": 0.74}, "tp": {**TRIDENT_TP, "scale": 0.74}},
    "sunset_spear": {"fp": {**TRIDENT_FP, "scale": 0.68}, "tp": {**TRIDENT_TP, "scale": 0.68}},
    "silver_oath": {"fp": {**TRIDENT_FP, "scale": 0.8}, "tp": {**TRIDENT_TP, "scale": 0.8}},
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
    """كاتانا حقيقية نحيفة: نصل رفيع بانحناء خفيف (سوري) وحد واحد بخط تموج (هامون) بنفسجي،
    رأس مائل (كيساكي)، طوق ذهبي (هاباكي)، حارس دائري (تسوبا)، قبضة طويلة بلف معيّن (إيتو) وغطاء نهاية (كاشيرا)."""
    w = Weapon("dark_katana")
    MUNE, STEEL, STEEL_HI = (22, 22, 40), (46, 44, 78), (78, 74, 120)
    HAMON, HAMON_HI, EDGE_W = (150, 110, 240), (205, 180, 255), (238, 230, 255)
    ITO, ITO_HI, SAME = (24, 22, 46), (44, 40, 82), (214, 206, 226)
    GOLD, GOLD_HI = (220, 178, 60), (255, 232, 140)
    TSUBA, TSUBA_HI = (30, 28, 44), (70, 66, 96)
    # كاشيرا + قبضة طويلة بلف معيّن: قطاعات غامقة وبينها مثلثات بيضاء (جلد السمكة) على الوجهين
    w.box(0, 5.4, 0, 1.9, 1.0, 1.5, TSUBA, top=GOLD)
    for k in range(8):
        y = 6.4 + k * 1.4
        w.box(0, y, 0, 1.6, 1.42, 1.25, ITO if k % 2 == 0 else ITO_HI)
        for sz in (-1, 1):
            w.box(0, y + 0.35, sz * 0.665, 0.55, 0.7, 0.08, SAME)
    for k in (2, 5):   # مينوكي ذهبي تحت اللف
        w.box(0.0, 6.4 + k * 1.4 + 0.2, 0.685, 0.8, 0.5, 0.12, GOLD)
        w.box(0.0, 6.4 + k * 1.4 + 0.2, -0.685, 0.8, 0.5, 0.12, GOLD)
    w.box(0, 17.6, 0, 1.8, 0.5, 1.45, GOLD, top=GOLD_HI)          # فوتشي
    # تسوبا دائرية رفيعة (مثمنة) بحافة ذهب
    w.box(0, 18.1, 0, 4.4, 0.6, 3.0, TSUBA, top=TSUBA_HI)
    w.box(0, 18.1, 0, 3.0, 0.6, 4.4, TSUBA, top=TSUBA_HI)
    w.box(0, 18.1, 0, 3.8, 0.6, 3.8, TSUBA, top=TSUBA_HI)
    for (x, z) in ((2.2, 0), (-2.2, 0), (0, 2.2), (0, -2.2)):
        w.box(x, 18.1, z, 0.35 if x else 1.2, 0.62, 1.2 if x else 0.35, GOLD)
    w.box(0, 18.7, 0, 1.3, 1.3, 1.0, GOLD, top=GOLD_HI)            # هاباكي
    # النصل: رفيع (عرض 1.5 ← 1.1)، سمك 0.6، انحناء خفيف، الحد (يمين) بخط هامون متموج
    y0, L, n = 20.0, 27.0, 18
    h = L / n
    for k in range(n):
        t = k / (n - 1)
        off = 1.6 * t * t
        wd = 1.5 - 0.4 * t
        yy = y0 + k * h
        mune = wd * 0.45
        w.box(off - wd / 2 + mune / 2, yy, 0, mune, h * 1.03, 0.62, lerp(MUNE, STEEL, 0.3 + 0.4 * t), top=STEEL_HI)
        ham = 0.32 + 0.12 * math.sin(k * 1.7)
        w.box(off + wd / 2 - (wd - mune) / 2, yy, 0, wd - mune, h * 1.03, 0.5, STEEL)
        w.box(off + wd / 2 - ham / 2 - 0.05, yy, 0, ham, h * 1.03, 0.54, HAMON if k % 3 else HAMON_HI)
        w.box(off + wd / 2 - 0.06, yy, 0, 0.12, h * 1.03, 0.4, EDGE_W)
    # كيساكي: الرأس المائل
    tx = 1.6
    w.box(tx - 0.15, y0 + L, 0, 1.0, 0.8, 0.55, STEEL_HI)
    w.box(tx + 0.1, y0 + L + 0.8, 0, 0.6, 0.7, 0.45, HAMON_HI)
    w.box(tx + 0.25, y0 + L + 1.5, 0, 0.3, 0.5, 0.35, EDGE_W)
    # خط الشيناغي (حافة لامعة على ظهر النصل)
    for k in range(0, n, 2):
        t = k / (n - 1)
        w.box(1.6 * t * t - 0.55, y0 + k * h, 0, 0.12, h * 2, 0.66, STEEL_HI)
    w.save()
    return w


# ───────────────────────── خنجر الفجر (منحني مثل الأيقونة) ─────────────────────────
def dagger():
    """خنجر حقيقي صغير: نصل مستقيم قصير بحدين وخط وسطي، حارس صغير، قبضة قصيرة ملفوفة، ورأس قبضة ذهبي بجوهرة الفجر."""
    w = Weapon("dawn_dagger")
    GOLD, GOLD_HI, GOLD_LO = (226, 178, 62), (255, 232, 140), (150, 108, 30)
    STEEL, STEEL_HI, STEEL_LO = (226, 222, 210), (255, 252, 240), (170, 166, 156)
    SUN_A, SUN_B = (255, 98, 52), (255, 190, 100)
    LEATHER_A, LEATHER_B = (118, 76, 44), (78, 48, 28)
    # رأس القبضة: جوهرة شروق بإطار ذهب
    w.box(0, 7.2, 0, 2.0, 0.6, 2.0, GOLD, top=GOLD_HI)
    w.box(0, 7.8, 0, 1.6, 1.2, 1.6, SUN_A, top=SUN_B)
    w.box(0, 9.0, 0, 1.9, 0.5, 1.9, GOLD)
    wrap(w, 9.5, 4, 1.1, 1.5, LEATHER_A, LEATHER_B)                     # قبضة قصيرة
    # حارس صغير مستقيم بأطراف منحنية للنصل
    w.box(0, 13.9, 0, 4.6, 0.8, 1.5, GOLD, top=GOLD_HI)
    for sx in (-1, 1):
        w.box(sx * 2.3, 14.5, 0, 0.7, 0.9, 1.2, GOLD_LO)
    w.box(0, 14.0, 0.8, 0.9, 0.7, 0.2, SUN_A); w.box(0, 14.0, -0.8, 0.9, 0.7, 0.2, SUN_A)
    # النصل: 10 بكسل، حدين يضيقون لرأس حاد، وخط وسطي (fuller)
    y0, L, n = 14.7, 10.0, 8
    h = L / n
    for k in range(n):
        t = k / (n - 1)
        wd = 2.4 - 0.5 * t - (1.2 * (t - 0.6) / 0.4 if t > 0.6 else 0)
        wd = max(0.5, wd)
        yy = y0 + k * h
        off = 1.3 * t * t                                   # ميلان خفيف للطرف
        w.box(off, yy, 0, wd, h * 1.03, 0.55, STEEL, top=STEEL_HI)
        for sx in (-1, 1):
            w.box(off + sx * (wd / 2 + 0.1), yy, 0, 0.2, h * 1.03, 0.4, STEEL_HI)   # الحدين: جنب النصل مو داخله
        if t < 0.75:
            w.box(off, yy, 0.31, 0.35, h * 1.03, 0.07, STEEL_LO if k % 2 else lerp(STEEL_LO, SUN_B, 0.4))
            w.box(off, yy, -0.31, 0.35, h * 1.03, 0.07, STEEL_LO if k % 2 else lerp(STEEL_LO, SUN_B, 0.4))
    w.box(1.3, y0 + L, 0, 0.3, 0.6, 0.3, STEEL_HI)
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
    """مخالب يد حقيقية: واقي ساعد جلدي بصفائح وأحزمة يلبس على اليد، صفيحة مفاصل بجواهر،
    وثلاث شفرات متوازية تطلع من المفاصل وتنحني مثل خطاف بالطرف (منحنية للأمام)."""
    w = Weapon("shadow_claws")
    LEATH, LEATH_HI = (58, 44, 52), (84, 64, 74)
    PLATE, PLATE_HI = (40, 36, 58), (76, 70, 104)
    STRAP, BUCKLE = (100, 60, 150), (200, 170, 255)
    BLD, BLD_HI, EDGE_W = (62, 50, 100), (150, 120, 230), (236, 228, 255)
    GEM = (170, 110, 255)
    # واقي الساعد (يغطي مكان اليد)
    w.box(0, 4.0, 0, 3.6, 10.0, 2.6, LEATH, top=LEATH_HI)
    for yy in (5.0, 8.4, 11.8):                       # أحزمة بإبزيم
        w.box(0, yy, 0, 3.9, 0.8, 2.9, STRAP)
        w.box(1.95, yy - 0.1, 0, 0.3, 1.0, 1.0, BUCKLE)
    for yy in (6.2, 9.6):                             # صفائح معدن على الظهر
        w.box(0, yy, 1.35, 3.2, 1.8, 0.3, PLATE, top=PLATE_HI)
    # صفيحة المفاصل: عريضة، عليها 3 جواهر، ومنها تطلع الشفرات
    w.box(0, 14.0, 0, 5.4, 1.6, 3.0, PLATE, top=PLATE_HI)
    w.box(0, 15.6, 0, 5.0, 0.6, 2.4, PLATE_HI)
    for x in (-1.8, 0.0, 1.8):
        w.box(x, 14.4, 1.55, 0.9, 0.8, 0.3, GEM)
        w.box(x, 16.2, 0, 1.1, 0.9, 1.3, PLATE)      # قاعدة كل شفرة
    # الشفرات: متوازية، طويلة، تنحني للأمام (z) وتضيق لرأس خطافي
    for x, L in ((-1.8, 12.5), (0.0, 14.5), (1.8, 12.5)):
        n = 11
        h = L / n
        for k in range(n):
            t = k / (n - 1)
            z = -2.6 * t ** 2.2                          # انحناء الخطاف
            wd = 0.85 - 0.45 * t
            yy = 17.1 + k * h - 1.2 * t ** 3            # الطرف ينزل شوية مع الانحناء
            w.box(x, yy, z + 0.2, wd, h * 1.05, 0.55, lerp(BLD, BLD_HI, 0.3 + 0.5 * t))
            w.box(x, yy, z - 0.22, wd * 0.8, h * 1.05, 0.3, EDGE_W if k % 3 == 1 else BLD_HI)   # الحد الداخلي
        w.box(x, 17.1 + L - 1.2, -2.9, 0.35, 0.7, 0.5, EDGE_W)
    w.save()
    return w


# ───────────────────────── مطرقة الصخر ─────────────────────────
def maul():
    """مطرقة حرب على شبكة بكسل مضبوطة وبدون أي تداخل بين المكعبات (كل قطعة جنب الثانية مو داخلها):
    عصا خشب بقطاعات، لف قماش وأطواق حديد كقطاعات مستقلة، رأس صخري طويل بالعرض،
    حزامين حديد، وجهين ضاربين حديد، زمرد بإطار برونزي على الجنبين، طحلب وشوكة فوق."""
    w = Weapon("stone_maul")
    ST, ST_HI = (122, 124, 120), (156, 158, 152)
    MOSS = (82, 126, 66)
    WOOD_A, WOOD_B = (92, 60, 36), (64, 42, 26)
    IRON, IRON_HI, IRON_LO = (70, 70, 80), (124, 124, 138), (44, 44, 52)
    CLOTH_A, CLOTH_B = (150, 56, 48), (196, 78, 64)
    EM, EM_HI, EM_W, BRONZE, BRONZE_HI = (40, 200, 90), (110, 245, 150), (220, 255, 230), (170, 120, 50), (225, 175, 90)
    # العصا: كل قطاع بمكانه (بدون تداخل). الخشب عرضه 2، الأطواق 3، القماش 3
    w.box(0, 0, 0, 4, 2, 4, IRON, top=IRON_HI)                       # رأس العصا السفلي
    y = 2
    for kind, h in (("w", 2), ("r", 1), ("w", 2), ("c", 1), ("c", 1), ("c", 1), ("c", 1), ("c", 1), ("c", 1), ("r", 1),
                    ("w", 2), ("w", 2), ("w", 2), ("r", 1), ("w", 2), ("w", 2)):
        if kind == "w":
            w.box(0, y, 0, 2, h, 2, WOOD_A if (y // 2) % 2 == 0 else WOOD_B)
        elif kind == "r":
            w.box(0, y, 0, 3, h, 3, IRON, top=IRON_HI)
        else:
            w.box(0, y, 0, 3, h, 3, CLOTH_A if y % 2 == 0 else CLOTH_B)
        y += h
    w.box(0, y, 0, 4, 1, 4, IRON, top=IRON_HI)                       # جلبة تحت الرأس
    hy = y + 1                                                       # بداية الرأس
    # الرأس: قطاعات على محور X جنب بعض: وجه | حزام | صخر | حزام | وجه
    w.box(0, hy, 0, 10, 7, 6, ST, top=ST_HI)                         # الصخر x -5..5
    for sx in (-1, 1):
        w.box(sx * 5.5, hy - 0.5, 0, 1, 8, 7, IRON, top=IRON_HI)     # حزام x 5..6
        w.box(sx * 7.0, hy + 0.5, 0, 2, 6, 5, IRON_LO, top=IRON)    # الوجه الضارب x 6..8
        w.box(sx * 8.25, hy + 1.5, 0, 0.5, 4, 3, IRON_HI)            # لمعة الوجه x 8..8.5
    # الزمرد: طبقات فوق وجه الصخر (برا الوجه، مو داخله)
    for sz in (-1, 1):
        w.box(0, hy + 2, sz * 3.25, 4, 3, 0.5, BRONZE, top=BRONZE_HI)  # إطار z 3..3.5
        w.box(0, hy + 2.5, sz * 3.75, 2, 2, 0.5, EM, top=EM_HI)       # جوهرة z 3.5..4
        w.box(-0.5, hy + 3.5, sz * 4.125, 0.5, 0.5, 0.25, EM_W)       # لمعة z 4..4.25
    # طحلب فوق الصخر (طبقة فوق السطح) + شوكة
    w.box(-3, hy + 7, 1.5, 2, 0.5, 2, MOSS)
    w.box(3, hy + 7, -1.5, 2, 0.5, 2, MOSS)
    w.box(0, hy + 7, 0, 2, 1, 2, IRON, top=IRON_HI)
    w.box(0, hy + 8, 0, 1, 1, 1, IRON_HI)
    # هالة خضراء خفيفة (بعيدة عن الرأس)
    shards(w, [(-10, hy + 5, 1, 0.5), (10, hy + 2, -1, 0.5), (0.5, hy + 11, 0.5, 0.5), (-4, hy + 10, -2.5, 0.5), (4.5, hy + 9.5, 2.5, 0.5)],
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


# ───────────────────────── سيف النور (Oath of Light): سيف فضي ببريق، عكس كاتانا الهاوية ─────────────────────────
def silver_oath():
    """سيف طويل فضي لامع: نصل عريض مستقيم بحدين وحافة وسطية مرتفعة، حارس فضي بأطراف ذهبية شاحبة
    وجوهرة بيضاء، قبضة جلد أبيض ملفوفة، رأس قبضة دائري، وبريق أبيض (نجيمات صغيرة) يطفو حوله."""
    w = Weapon("silver_oath")
    SIL, SIL_HI, SIL_LO = (196, 204, 220), (244, 248, 255), (140, 148, 168)
    RIDGE, WHITE = (226, 232, 246), (255, 255, 255)
    PGOLD, PGOLD_HI = (214, 196, 140), (246, 232, 180)
    GRIP_A, GRIP_B = (232, 228, 220), (190, 184, 174)
    GEM, GEM_HI = (220, 240, 255), (255, 255, 255)
    LIGHT, LIGHT_HI = (255, 226, 140), (255, 246, 200)
    # تفاصيل النور الصغيرة (كلها لاصقة على الوجوه، مو داخلها):
    # بلورة نور تحت رأس القبضة، أشعة ذهب حول جوهرة الحارس، ريشتين بكل طرف من الحارس، نقاط ذهب على النصل، وبريق دافئ
    w.box(0, 3.9, 0, 0.7, 0.7, 0.7, LIGHT_HI)
    # رأس قبضة دائري (مثمن) + قبضة جلد أبيض
    w.box(0, 4.6, 0, 2.6, 1.6, 1.8, SIL, top=SIL_HI)
    w.box(0, 4.6, 0, 1.8, 1.6, 2.6, SIL, top=SIL_HI)
    w.box(0, 6.2, 0, 1.6, 0.6, 1.6, PGOLD)
    wrap(w, 6.8, 7, 1.4, 1.7, GRIP_A, GRIP_B)
    w.box(0, 16.6, 0, 2.2, 0.6, 2.2, PGOLD, top=PGOLD_HI)
    # الحارس: عارضة فضية مستقيمة بأطراف ذهبية تنحني للنصل، وجوهرة بيضاء بالنص
    w.box(0, 17.2, 0, 9.0, 1.2, 2.0, SIL, top=SIL_HI)
    for sx in (-1, 1):
        w.box(sx * 5.0, 17.2, 0, 1.0, 1.2, 2.2, PGOLD, top=PGOLD_HI)
        w.box(sx * 5.0, 18.4, 0, 1.0, 1.0, 1.6, PGOLD_HI)
    w.box(0, 17.3, 1.1, 1.4, 1.0, 0.2, GEM)
    w.box(0, 17.3, -1.1, 1.4, 1.0, 0.2, GEM)
    for sz in (-1, 1):                                                 # أشعة صغيرة حول الجوهرة
        for sx in (-1, 1):
            w.box(sx * 1.05, 17.35, sz * 1.05, 0.3, 0.3, 0.1, LIGHT)
            w.box(sx * 1.05, 17.95, sz * 1.05, 0.3, 0.3, 0.1, LIGHT_HI)
    for sx in (-1, 1):                                                 # ريشتين صغار بأطراف الحارس
        w.box(sx * 5.9, 18.6, 0, 0.8, 0.5, 1.2, LIGHT_HI)
        w.box(sx * 6.5, 19.1, 0, 0.6, 0.5, 1.0, WHITE)
    w.box(0, 18.4, 0, 1.6, 0.8, 1.4, SIL_LO)                          # ريكاسو
    # النصل: عريض مستقيم، حدين لامعين جنب النصل، وحافة وسطية بيضاء (على الوجهين، برا الوجه)
    y0, L, n = 19.2, 26.0, 13
    h = L / n
    for k in range(n):
        t = k / (n - 1)
        wd = 3.2 - 0.6 * t - (2.0 * (t - 0.8) / 0.2 if t > 0.8 else 0)
        wd = max(0.6, wd)
        yy = y0 + k * h
        w.box(0, yy, 0, wd, h, 0.8, lerp(SIL_LO, SIL, 0.5 + 0.4 * t), top=SIL_HI)
        for sx in (-1, 1):
            w.box(sx * (wd / 2 + 0.15), yy, 0, 0.3, h, 0.5, SIL_HI if k % 3 else WHITE)
        for sz in (-1, 1):
            w.box(0, yy, sz * 0.45, 0.5, h, 0.1, RIDGE if k % 2 else WHITE)
    w.box(0, y0 + L, 0, 0.5, 0.8, 0.5, WHITE)
    for k, yy in enumerate((20.2, 22.0, 23.8)):                        # نقاط ذهب صغيرة قرب قاعدة النصل
        for sz in (-1, 1):
            for sx in (-1, 1):
                w.box(sx * 0.6, yy, sz * 0.45, 0.3, 0.3, 0.1, LIGHT if k % 2 else LIGHT_HI)
    # بريق: نجيمات صغيرة (+) تطفو حول النصل، بيض ودافئة
    for i, (x, y, z) in enumerate(((-3.6, 25, 0.8), (3.8, 30, -0.8), (-3.0, 36, -0.6), (3.2, 41, 0.9), (0.0, 47.5, 0.0))):
        c = WHITE if i % 2 == 0 else LIGHT_HI
        w.box(x, y, z, 0.9, 0.3, 0.3, c)
        w.box(x, y - 0.3, z, 0.3, 0.9, 0.3, c)
    w.save()
    return w


ALL = [katana, dagger, cleaver, shadow_blade, claws, maul, spear, silver_oath]

if __name__ == "__main__":
    ws = [fn() for fn in ALL]
    save_animations()
    outdir = os.environ.get("PREVIEW_DIR", "/tmp")
    preview(ws[:4], os.path.join(outdir, "weapons3d_a.png"))
    preview(ws[4:], os.path.join(outdir, "weapons3d_b.png"))
    for w in ws:
        print(f"{w.ident:14} cubes={len(w.cubes):3} colors={len(w.palette)}")
    print("preview", outdir)
