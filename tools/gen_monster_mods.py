"""تحسينات خفيفة لمجسمات الوحوش (قرون، أشواك، عيون متوهجة، دروع، لهب) بدون ما نخرب الموديلات الأصلية.
المصدر الأصلي محفوظ بـ tools/monster_src (نسخة قبل التعديل)، والسكربت يبني منها كل مرة (آمن لإعادة التشغيل).
الإضافات مكعبات UV لكل وجه تشير لشريط ألوان يُلصق أسفل التكستشر (يزيد 16 بكسل بالارتفاع).
التشغيل: python3 tools/gen_monster_mods.py
"""
import json
import os
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "monster_src")
GEO = os.path.join(ROOT, "AnimePowers", "RP", "models", "entity")
TEX = os.path.join(ROOT, "AnimePowers", "RP", "textures", "entity")


class Mod:
    def __init__(self, name):
        self.name = name
        with open(os.path.join(SRC, f"sh_{name}.geo.json"), encoding="utf-8") as f:
            self.geo = json.load(f)
        self.g = self.geo["minecraft:geometry"][0]
        self.tex = Image.open(os.path.join(SRC, f"sh_{name}.png")).convert("RGBA")
        self.w, self.h = self.tex.size
        self.palette = []
        self.bones = {b["name"]: b for b in self.g["bones"]}

    def _uv(self, rgb):
        rgb = tuple(int(v) for v in rgb[:3])
        if rgb not in self.palette:
            assert len(self.palette) < 256
            self.palette.append(rgb)
        i = self.palette.index(rgb)
        return {"uv": [i % 16, self.h + i // 16], "uv_size": [1, 1]}

    def box(self, bone, x, y, z, w, h, d, color, top=None):
        """مكعب بزاوية دنيا (x,y,z) داخل عظمة موجودة."""
        m = self._uv(color)
        t = self._uv(top) if top else m
        cube = {"origin": [round(x, 3), round(y, 3), round(z, 3)], "size": [w, h, d],
                "uv": {"north": m, "south": m, "east": m, "west": m, "up": t, "down": m}}
        self.bones[bone].setdefault("cubes", []).append(cube)

    def save(self):
        strip_h = 16
        out = Image.new("RGBA", (self.w, self.h + strip_h), (0, 0, 0, 0))
        out.paste(self.tex, (0, 0))
        for i, c in enumerate(self.palette):
            out.putpixel((i % 16, self.h + i // 16), (*c, 255))
        self.g["description"]["texture_height"] = self.h + strip_h
        out.save(os.path.join(TEX, f"sh_{self.name}.png"))
        with open(os.path.join(GEO, f"sh_{self.name}.geo.json"), "w", encoding="utf-8") as f:
            json.dump(self.geo, f, separators=(",", ":"))
        return len(self.palette)


# ───────────── عفريت الرماد: قرون منحنية، عيون جمر، أشواك ظهر، لهب بالذيل ─────────────
def imp():
    m = Mod("imp")
    HORN, HORN_HI, EMB, EMB_HI, EMB_W = (226, 212, 180), (255, 246, 220), (255, 120, 28), (255, 190, 60), (255, 240, 170)
    ROCK = (58, 52, 62)
    # قرون كبيرة تنحني للخارج والأعلى (3 قطع لكل قرن)
    for sx in (-1, 1):
        m.box("head", sx * 2.9 - 0.8, 21.2, -1.4, 1.6, 2.0, 1.6, HORN, top=HORN_HI)
        m.box("head", sx * 3.8 - 0.65, 22.9, -1.3, 1.3, 1.9, 1.3, HORN)
        m.box("head", sx * 4.5 - 0.5, 24.5, -1.2, 1.0, 1.8, 1.0, HORN_HI)
        m.box("head", sx * 4.9 - 0.35, 26.0, -1.1, 0.7, 1.4, 0.7, EMB_HI)
    # (العيون المضافة انشالت بطلب اللاعب: العيون من التكستشر الأصلي)
    # تاج جمر صغير فوق الراس
    m.box("head", -0.6, 21.5, -0.2, 1.2, 1.4, 1.2, EMB)
    m.box("head", -0.35, 22.9, 0.0, 0.7, 1.0, 0.7, EMB_HI)
    # أشواك صخرية متوهجة على الظهر
    for k, (y, hh) in enumerate(((10.6, 1.6), (12.2, 2.0), (13.9, 1.8))):
        m.box("body", -0.6, y, 2.6, 1.2, hh, 1.5, ROCK, top=EMB)
        m.box("body", -0.3, y + 0.2, 4.0, 0.6, hh * 0.7, 0.6, EMB)
    # لهب نهاية الذيل
    m.box("tail3", -0.8, 12.3, 13.4, 1.6, 2.6, 1.6, EMB)
    m.box("tail3", -0.5, 14.7, 13.7, 1.0, 1.8, 1.0, EMB_HI)
    m.box("tail3", -0.3, 16.3, 13.9, 0.6, 1.2, 0.6, EMB_W)
    # صخور جمر على الأكتاف
    for sx in (-1, 1):
        m.box("body", sx * 5.2 - 1.0, 15.2, -1.2, 2.0, 1.6, 2.4, ROCK, top=EMB)
    return m.save()


# ───────────── حارس الصخر (غولم حجري طحلبي ببلورات تركواز): بلورات كتف، عين، قلب مضيء، أعمدة ظهر ─────────────
def guard():
    m = Mod("guard")
    STONE, STONE_HI, STONE_LO = (96, 100, 94), (140, 146, 136), (52, 56, 52)
    MOSS = (78, 124, 62)
    TEAL, TEAL_HI, TEAL_W = (70, 220, 190), (150, 255, 232), (232, 255, 248)
    # بلورات تركواز على الأكتاف (3 لكل كتف، الوسطى أطول)
    for sx in (-1, 1):
        for k, (dx, hh) in enumerate(((-2.6, 3.0), (0.0, 4.6), (2.6, 3.2))):
            cx = sx * 9.6 + dx
            m.box("body", cx - 0.8, 27.4, -0.8, 1.6, hh, 1.6, TEAL, top=TEAL_HI)
            m.box("body", cx - 0.4, 27.4 + hh, -0.4, 0.8, 1.4, 0.8, TEAL_W)
    # عين متوهجة (شق أفقي)
    m.box("head", -2.6, 28.4, -3.75, 5.2, 0.9, 0.5, TEAL)
    m.box("head", -1.6, 28.45, -3.85, 3.2, 0.6, 0.3, TEAL_W)
    # قلب مضيء بالصدر بإطار حجري
    m.box("body", -2.8, 19.6, -4.8, 5.6, 5.6, 0.5, STONE_HI)
    m.box("body", -2.1, 20.3, -5.05, 4.2, 4.2, 0.4, TEAL)
    m.box("body", -1.1, 21.3, -5.3, 2.2, 2.2, 0.3, TEAL_W)
    # أعمدة بلورية بالظهر مع قواعد حجرية
    for sx in (-1, 1):
        m.box("body", sx * 3.6 - 1.3, 20.0, 6.7, 2.6, 2.0, 2.6, STONE_LO, top=STONE_HI)
        m.box("body", sx * 3.6 - 0.8, 22.0, 7.2, 1.6, 6.5, 1.6, TEAL, top=TEAL_HI)
        m.box("body", sx * 3.6 - 0.4, 28.5, 7.6, 0.8, 1.6, 0.8, TEAL_W)
    # حزام حجري بمسامير طحلبية
    m.box("body", -6.8, 13.0, -4.3, 13.6, 1.2, 0.6, STONE_LO)
    for x in (-5.5, -2.0, 1.5, 5.0):
        m.box("body", x, 13.2, -4.6, 0.8, 0.8, 0.4, MOSS)
    return m.save()


# ───────────── ذئب الظل: عرف شبحي، عيون بنفسجية، آذان شفرة، لهب بالذيل ─────────────
def hound():
    m = Mod("hound")
    BLK, BLK_HI = (24, 20, 40), (52, 44, 84)
    VIO, VIO_HI, VIO_W = (130, 80, 240), (180, 130, 255), (232, 214, 255)
    # عرف شبحي: أشواك تكبر باتجاه الكتفين
    for k, (z, hh) in enumerate(((-6.4, 2.0), (-4.4, 2.8), (-2.4, 3.2), (-0.4, 2.8), (1.6, 2.2), (3.4, 1.6))):
        m.box("body", -0.6, 12.6, z, 1.2, hh, 1.2, BLK_HI, top=VIO)
        m.box("body", -0.35, 12.6 + hh, z + 0.25, 0.7, 0.9, 0.7, VIO_HI)
    # (العيون المضافة انشالت بطلب اللاعب: العيون من التكستشر الأصلي)
    # آذان شفرة
    for sx in (-1, 1):
        m.box("head", sx * 1.9 - 0.6, 14.1, -8.6, 1.2, 2.4, 0.9, BLK_HI)
        m.box("head", sx * 2.0 - 0.4, 16.3, -8.5, 0.8, 1.6, 0.7, VIO)
    # طوق أشواك بالرقبة
    for sx in (-1, 1):
        m.box("body", sx * 3.5 - 0.5, 9.6, -6.4, 1.0, 1.6, 1.0, VIO_HI)
        m.box("body", sx * 3.7 - 0.4, 8.2, -6.0, 0.8, 1.4, 0.8, VIO)
    # لهب شبحي بنهاية الذيل
    m.box("tail3", -0.9, 13.4, 14.6, 1.8, 2.8, 1.8, VIO)
    m.box("tail3", -0.55, 16.0, 14.9, 1.1, 2.0, 1.1, VIO_HI)
    m.box("tail3", -0.3, 17.8, 15.1, 0.6, 1.2, 0.6, VIO_W)
    return m.save()


# ───────────── عقرب الرمل: عيون خضراء، صفائح ظهر، سم متوهج بالإبرة، أشواك الكماشة ─────────────
def scorpion():
    m = Mod("scorpion")
    CHI, CHI_HI, CHI_LO = (112, 82, 44), (170, 130, 70), (62, 44, 26)
    VEN, VEN_HI, VEN_W = (110, 235, 70), (180, 255, 110), (236, 255, 190)
    # (العيون المضافة انشالت: العيون من التكستشر الأصلي)
    # صفائح ظهر مسننة
    for k, z in enumerate((-4.4, -1.6, 1.2, 3.8)):
        m.box("body", -1.0 - 0.0, 6.2, z, 2.0, 1.2 + (k % 2) * 0.4, 1.6, CHI_LO, top=CHI_HI)
        m.box("body", -0.5, 7.2 + (k % 2) * 0.4, z + 0.3, 1.0, 0.9, 1.0, CHI_HI)
    # إبرة بسم متوهج وقطرات
    m.box("sting", -0.5, 22.9, 6.1, 1.0, 1.4, 1.0, VEN_HI)
    m.box("sting", -0.3, 24.1, 6.3, 0.6, 0.9, 0.6, VEN_W)
    m.box("sting", -0.6, 19.3, 7.4, 1.2, 1.2, 1.2, VEN)
    m.box("sting", -0.4, 17.4, 8.6, 0.8, 1.0, 0.8, VEN_HI)
    # أشواك على الكماشتين
    for bone, sx in (("claw_l", 1), ("claw_r", -1)):
        m.box(bone, sx * 3.5 - 0.4, 3.6, -14.0, 0.8, 1.2, 0.8, CHI_LO)
        m.box(bone, sx * 4.8 - 0.4, 4.4, -12.6, 0.8, 1.4, 0.8, CHI_HI)
        m.box(bone, sx * 3.5 - 0.3, 5.4, -11.2, 0.6, 1.0, 0.6, CHI_LO)
    # عقد الذيل: حلقات بارزة
    for b in ("tail2", "tail3", "tail4"):
        bb = m.bones[b]
        c = bb["cubes"][0]
        ox, oy, oz = c["origin"]; sx, sy, sz = c["size"]
        m.box(b, ox - 0.35, oy + sy * 0.35, oz - 0.35, sx + 0.7, 0.8, sz + 0.7, CHI_HI)
    return m.save()


if __name__ == "__main__":
    for fn in (imp, guard, hound, scorpion):
        print(fn.__name__, "colors:", fn())
