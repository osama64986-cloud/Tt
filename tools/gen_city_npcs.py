#!/usr/bin/env python3
"""سكان مدينة Aetheria (إثيريا 1.42): أربع شخصيات بشرية عادية بدون قدرات.
  sh:city_guard      حارس المدينة (كثير منهم): خوذة فولاذ بريشة زرقة، زرد، رداء أزرق بشعار ذهبي، رمح بعلم، ترس.
                     يحارب الوحوش (عائلة monster و sh_monster) وما يأذي اللاعب، ويرجع لمكانه (minecraft:home).
  sh:aetheria_king   الملك ألدرك: تاج ذهب بجواهر، لحية شيبة، عباءة حمرة بفرو أبيض (إرمين)، صولجان بكرة زرقة. واقف بقاعة العرش.
  sh:townswoman      ميرا: شعر كستنائي بضفيرة وورد، صدرية خضرة وقميص كريمي، تنورة واسعة ومريلة، سلة تفاح.
  sh:townsman        توماس الحداد: لحية قصيرة، قميص كتان مطوي الأكمام، مريلة جلد، مطرقة بإيده.
نفس عظام المدرب والخيميائي (body/head/arm_l/arm_r/leg_l/leg_r) فيشتغل بأنميشن المدرب (idle/walk) + النظر.
الأرقام هنا بحساب اللعبة مباشرة (arm_r = اليد اليمنى، الوجه = -z): هالموديلات مو بقائمة tools/handed.py.
التشغيل: python3 tools/gen_city_npcs.py [مجلد_معاينة]"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_grim_monsters import Rig, RP  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")

FACE = {
    "skin": ("flat", (226, 180, 146), (226, 180, 146)),
    "skin_dk": ("flat", (196, 146, 112), (196, 146, 112)),
    "eye": ("flat", (46, 34, 28), (46, 34, 28)),
    "white": ("flat", (242, 242, 238), (242, 242, 238)),
    "mouth": ("flat", (150, 84, 74), (150, 84, 74)),
}


def mx(o, s):
    return (-(o[0] + s[0]), o[1], o[2])


def humanoid(ident, mats, seed):
    R = Rig(ident, {**FACE, **mats}, seed=seed)
    R.bone("body", None, (0, 12, 0))
    R.bone("head", "body", (0, 24, 0))
    R.bone("arm_l", "body", (5, 22, 0))
    R.bone("arm_r", "body", (-5, 22, 0))
    R.bone("leg_l", "body", (2, 12, 0))
    R.bone("leg_r", "body", (-2, 12, 0))
    return R


def sym(R, bone, o, s, mat, **kw):
    R.box(bone, o, s, mat, **kw)
    R.box(bone, mx(o, s), s, mat, **kw)


def arms(R, fn):
    """fn(b, side): يرسم ذراع (b = دالة مكعب بإحداثيات الذراع اليسرى، تنعكس للذراع اليمنى)"""
    for nm, sx in (("arm_l", 1), ("arm_r", -1)):
        def b(o, s, m, _nm=nm, _sx=sx, **kw):
            R.box(_nm, o if _sx > 0 else mx(o, s), s, m, **kw)
        fn(b, sx)


def legs(R, fn):
    for nm, sx in (("leg_l", 1), ("leg_r", -1)):
        def b(o, s, m, _nm=nm, _sx=sx, **kw):
            R.box(_nm, o if _sx > 0 else mx(o, s), s, m, **kw)
        fn(b, sx)


def face(R, brow="brow", lashes=False, mouth=True):
    R.box("head", (-4, 24, -4), (8, 8, 8), "skin")
    sym(R, "head", (1.1, 27.4, -4.1), (1.8, 1.1, 0.15), "white")                      # بياض العين
    sym(R, "head", (1.15, 27.4, -4.2), (0.8, 1.1, 0.15), "eye")                       # الحدقة لجهة الخشم
    sym(R, "head", (0.9, 28.8, -4.2), (2.4, 0.55, 0.25), brow)                        # الحاجب
    if lashes:
        sym(R, "head", (1.0, 28.45, -4.22), (2.0, 0.3, 0.15), "eye")                  # رموش (خط غامق فوق العين)
    R.box("head", (-0.6, 26.2, -4.5), (1.2, 1.6, 0.55), "skin_dk")                    # الخشم
    if mouth:
        R.box("head", (-1.1, 25.2, -4.15), (2.2, 0.45, 0.15), "mouth")


# ═══════════════════════════ حارس المدينة ═══════════════════════════
def guard():
    R = humanoid("sh_city_guard", {
        "brow": ("flat", (70, 48, 34), (70, 48, 34)),
        "steel": ("metal", (176, 182, 192), (176, 182, 192)),
        "steel_dk": ("metal", (112, 118, 130), (112, 118, 130)),
        "mail": ("chitin", (120, 124, 132), (172, 176, 186)),
        "tabard": ("cloth", (40, 70, 168), (40, 70, 168)),
        "tabard_dk": ("cloth", (28, 48, 118), (28, 48, 118)),
        "gold": ("metal", (226, 182, 70), (226, 182, 70)),
        "plume": ("cloth", (52, 96, 214), (52, 96, 214)),
        "leather": ("pelt", (98, 64, 38), (132, 90, 56)),
        "pants": ("cloth", (56, 56, 64), (56, 56, 64)),
        "boots": ("pelt", (52, 36, 24), (76, 52, 34)),
        "wood": ("pelt", (110, 78, 46), (140, 104, 64)),
    }, 411)
    face(R)
    # خوذة: قبة فولاذ بحافة، واقي أنف، واقيات خدود، عرف، ريشة زرقة، وزرد على الرقبة من ورا
    R.box("head", (-4.5, 28.9, -4.5), (9, 3.6, 9), "steel")
    R.box("head", (-5.2, 28.5, -5.2), (10.4, 0.7, 10.4), "steel_dk")
    R.box("head", (-0.5, 26.0, -4.85), (1.0, 3.0, 0.5), "steel")
    sym(R, "head", (3.7, 24.6, -4.7), (0.9, 4.2, 4.6), "steel")
    R.box("head", (-0.5, 32.4, -3.6), (1.0, 1.0, 7.2), "steel_dk")
    R.box("head", (-0.7, 33.2, -1.2), (1.4, 2.4, 3.8), "plume", rot=(-18, 0, 0), pivot=(0, 33.2, 0))
    R.box("head", (-4.3, 24.0, 1.6), (8.6, 4.2, 2.9), "mail")
    # الجسم: زرد، رداء أزرق (قدام وورا) ينزل تحت الحزام، شعار الشمس الذهبي، حزام وإبزيم
    R.box("body", (-4, 12, -2), (8, 12, 4), "mail")
    R.box("body", (-3.3, 9.0, -2.4), (6.6, 14.6, 0.45), "tabard")
    R.box("body", (-3.3, 9.0, 1.95), (6.6, 14.6, 0.45), "tabard")
    R.box("body", (-3.35, 9.0, -2.45), (6.7, 0.55, 0.5), "gold"); R.box("body", (-3.35, 9.0, 1.95), (6.7, 0.55, 0.5), "gold")
    R.box("body", (-0.5, 14.8, -2.7), (1.0, 5.6, 0.3), "gold"); R.box("body", (-2.2, 17.1, -2.7), (4.4, 1.0, 0.3), "gold")
    R.box("body", (-1.2, 16.4, -2.75), (2.4, 2.4, 0.3), "gold", rot=(0, 0, 45), pivot=(0, 17.6, -2.6))
    R.box("body", (-4.3, 12.2, -2.4), (8.6, 1.3, 4.8), "leather"); R.box("body", (-0.8, 12.1, -2.65), (1.6, 1.5, 0.3), "gold")
    R.box("body", (-3.3, 21.6, -2.5), (6.6, 0.6, 0.5), "tabard_dk")
    # الذراعين: زرد، كتافات فولاذ بحافة، قفازات
    def arm(b, sx):
        b((4, 12, -2), (4, 12, 4), "mail")
        b((3.6, 20.6, -2.5), (4.8, 3.6, 5.0), "steel")
        b((3.5, 20.4, -2.6), (5.0, 0.6, 5.2), "steel_dk")
        b((3.8, 12, -2.2), (4.4, 3.6, 4.4), "steel")
        b((3.75, 15.3, -2.25), (4.5, 0.5, 4.5), "steel_dk")
    arms(R, arm)
    # الرمح باليد اليمنى (عمودي، كعبه فوق الأرض) وعلم أزرق صغير، والترس الأزرق على الذراع اليسرى
    R.box("arm_r", (-6.5, 0.6, -1.0), (1, 34.4, 1), "wood")
    R.box("arm_r", (-7.0, 34.6, -1.5), (2, 1.2, 2), "steel_dk")
    R.box("arm_r", (-6.75, 35.8, -1.25), (1.5, 3.4, 1.5), "steel")
    R.box("arm_r", (-6.5, 39.2, -1.0), (1, 1.4, 1), "steel")
    R.box("arm_r", (-6.3, 29.8, 0.0), (0.4, 3.6, 4.4), "plume")
    R.box("arm_r", (-6.32, 31.3, 0.0), (0.44, 0.7, 4.4), "gold")
    R.box("arm_l", (8.1, 10.2, -3.5), (1.0, 10.6, 7), "tabard")
    R.box("arm_l", (8.15, 8.6, -2.2), (0.9, 1.8, 4.4), "tabard")
    for o, s in (((8.05, 20.4, -3.6), (1.1, 0.6, 7.2)), ((8.05, 10.1, -3.6), (1.1, 0.5, 7.2)), ((8.05, 10.1, -3.6), (1.1, 10.8, 0.5)), ((8.05, 10.1, 3.1), (1.1, 10.8, 0.5))):
        R.box("arm_l", o, s, "steel_dk")
    R.box("arm_l", (9.05, 11.5, -0.5), (0.3, 8.0, 1.0), "gold"); R.box("arm_l", (9.05, 15.6, -2.6), (0.3, 1.0, 5.2), "gold")
    # الرجلين: سروال، واقيات ساق، ركبة، جزمة
    def leg(b, sx):
        b((0, 2, -2), (4, 10, 4), "pants")
        b((0.1, 2.0, -2.3), (3.8, 5.0, 0.6), "steel")
        b((0.2, 6.6, -2.45), (3.6, 1.8, 0.8), "steel_dk")
        b((-0.05, 0, -2.4), (4.1, 2.4, 4.6), "boots", top="boots")
    legs(R, leg)
    return R


# ═══════════════════════════ الملك ألدرك ═══════════════════════════
def king():
    R = humanoid("sh_aetheria_king", {
        "brow": ("fur", (206, 204, 198), (150, 146, 140)),
        "beard": ("fur", (214, 212, 206), (156, 152, 146)),
        "crown": ("metal", (236, 192, 72), (236, 192, 72)),
        "gem_r": ("glow", (200, 30, 50), (255, 170, 180)),
        "gem_b": ("glow", (50, 100, 240), (190, 215, 255)),
        "velvet": ("cloth", (150, 26, 38), (150, 26, 38)),
        "velvet_dk": ("cloth", (104, 16, 26), (104, 16, 26)),
        "ermine": ("bone", (242, 240, 234), (24, 22, 26)),
        "tunic": ("cloth", (44, 64, 156), (44, 64, 156)),
        "belt": ("pelt", (60, 40, 26), (86, 58, 38)),
        "boots": ("pelt", (48, 32, 22), (72, 48, 32)),
    }, 512)
    face(R, mouth=False)
    # لحية طويلة شيبة وشوارب وسوالف، وشعر من ورا
    R.box("head", (-3.7, 21.6, -4.7), (7.4, 4.4, 1.8), "beard")
    R.box("head", (-2.5, 19.6, -4.6), (5.0, 2.2, 1.5), "beard")
    R.box("head", (-1.3, 18.4, -4.5), (2.6, 1.4, 1.3), "beard")
    R.box("head", (-2.9, 25.3, -4.62), (5.8, 0.9, 0.5), "beard")
    sym(R, "head", (3.35, 24.3, -4.3), (0.85, 4.0, 3.2), "beard")
    R.box("head", (-4.25, 24.0, 1.0), (8.5, 7.4, 3.3), "beard")
    sym(R, "head", (3.6, 26.5, -3.0), (0.7, 4.5, 4.5), "beard")
    # التاج: حزام ذهب، 8 أسنان، جواهر، ومخدة مخمل
    R.box("head", (-4.4, 30.8, -4.4), (8.8, 2.0, 8.8), "crown")
    R.box("head", (-3.7, 32.4, -3.7), (7.4, 0.9, 7.4), "velvet")
    for x in (-3.9, -0.6, 2.7):
        R.box("head", (x, 32.8, -4.4), (1.2, 1.8, 0.6), "crown"); R.box("head", (x, 32.8, 3.8), (1.2, 1.8, 0.6), "crown")
    for z in (-0.6,):
        R.box("head", (-4.4, 32.8, z), (0.6, 1.8, 1.2), "crown"); R.box("head", (3.8, 32.8, z), (0.6, 1.8, 1.2), "crown")
    R.box("head", (-0.55, 31.3, -4.65), (1.1, 1.1, 0.3), "gem_r")
    sym(R, "head", (2.2, 31.45, -4.62), (0.8, 0.8, 0.25), "gem_b")
    R.box("head", (-0.4, 34.6, -0.4), (0.8, 0.8, 0.8), "gem_r")
    # الجسم: قميص أزرق، سلسلة ذهب بقلادة، حزام، عباءة حمرة طويلة من ورا بحافة فرو، ياقة فرو، وثوب طويل لتحت
    R.box("body", (-4, 12, -2), (8, 12, 4), "tunic")
    R.box("body", (-3.0, 21.0, -2.35), (6.0, 0.6, 0.4), "crown")
    R.box("body", (-0.8, 18.6, -2.5), (1.6, 2.2, 0.4), "crown"); R.box("body", (-0.45, 19.1, -2.7), (0.9, 0.9, 0.3), "gem_b")
    R.box("body", (-4.3, 13.4, -2.35), (8.6, 1.1, 4.7), "belt"); R.box("body", (-0.8, 13.2, -2.6), (1.6, 1.5, 0.3), "crown")
    R.box("body", (-4.7, 0.4, 2.0), (9.4, 23.6, 1.2), "velvet")
    R.box("body", (-4.75, 0.4, 1.95), (9.5, 1.3, 1.3), "ermine")
    R.box("body", (-4.9, 21.4, 1.85), (9.8, 3.2, 1.0), "ermine")
    sym(R, "body", (1.6, 21.4, -2.65), (3.4, 3.0, 0.7), "ermine")
    R.box("body", (-4.4, 0.5, -2.45), (8.8, 12.6, 4.6), "velvet")
    R.box("body", (-4.45, 0.5, -2.5), (8.9, 1.3, 4.7), "ermine")
    R.box("body", (-1.2, 1.8, -2.65), (2.4, 11.2, 0.2), "tunic")
    sym(R, "body", (1.2, 1.8, -2.7), (0.5, 11.2, 0.25), "crown")
    # الذراعين: أكمام مخمل بأساور فرو وكتف فرو، والكف
    def arm(b, sx):
        b((4, 13.6, -2), (4, 10.4, 4), "velvet")
        b((3.8, 13.0, -2.2), (4.4, 1.7, 4.4), "ermine")
        b((3.75, 21.2, -2.4), (4.5, 2.8, 4.8), "ermine")
        b((4.3, 10.8, -1.7), (3.4, 2.4, 3.4), "skin")
    arms(R, arm)
    # الصولجان باليمنى: عصا ذهب وكرة زرقة وصليب صغير
    R.box("arm_r", (-6.5, 3.8, -1.5), (1, 16.4, 1), "crown")
    R.box("arm_r", (-7.0, 6.0, -2.0), (2, 0.8, 2), "crown")
    R.box("arm_r", (-7.25, 20.0, -2.25), (2.5, 2.5, 2.5), "gem_b")
    R.box("arm_r", (-6.5, 22.4, -1.5), (1, 1.6, 1), "crown"); R.box("arm_r", (-7.1, 22.9, -1.5), (2.2, 0.5, 1), "crown")
    def leg(b, sx):
        b((0, 1.5, -2), (4, 10.5, 4), "velvet_dk")
        b((-0.05, 0, -2.4), (4.1, 1.8, 4.6), "boots", top="boots")
    legs(R, leg)
    return R


# ═══════════════════════════ ميرا (امرأة) ═══════════════════════════
def woman():
    R = humanoid("sh_townswoman", {
        "brow": ("flat", (96, 56, 32), (96, 56, 32)),
        "hair": ("fur", (126, 74, 40), (86, 48, 26)),
        "mouth": ("flat", (196, 96, 96), (196, 96, 96)),
        "bodice": ("cloth", (54, 108, 62), (54, 108, 62)),
        "bodice_dk": ("cloth", (36, 76, 44), (36, 76, 44)),
        "blouse": ("cloth", (238, 228, 208), (238, 228, 208)),
        "blouse_dk": ("cloth", (206, 194, 170), (206, 194, 170)),
        "skirt": ("cloth", (126, 58, 42), (126, 58, 42)),
        "skirt_dk": ("cloth", (90, 40, 30), (90, 40, 30)),
        "apron": ("cloth", (244, 240, 230), (244, 240, 230)),
        "lace": ("flat", (70, 46, 30), (70, 46, 30)),
        "flower": ("flat", (220, 64, 80), (220, 64, 80)),
        "yellow": ("flat", (240, 210, 70), (240, 210, 70)),
        "wicker": ("pelt", (176, 136, 76), (204, 166, 100)),
        "apple": ("flat", (200, 40, 40), (200, 40, 40)),
        "shoes": ("pelt", (82, 52, 32), (106, 70, 44)),
    }, 613)
    face(R, lashes=True)
    # الشعر: قبة، غرة، جوانب تأطر الوجه، والطويل من ورا (جزء بالراس وجزء على الجسم ينزل على الظهر) وضفيرة بشريطة
    R.box("head", (-4.25, 30.6, -4.25), (8.5, 1.9, 8.5), "hair")
    R.box("head", (-4.25, 29.6, -4.4), (8.5, 1.2, 1.4), "hair")
    sym(R, "head", (3.35, 24.6, -4.35), (1.0, 6.6, 5.6), "hair")
    R.box("head", (-4.25, 24.0, 1.3), (8.5, 7.2, 3.0), "hair")
    R.box("body", (-4.0, 16.0, 2.0), (8.0, 8.0, 1.6), "hair")
    R.box("body", (-1.0, 12.2, 3.0), (2.0, 4.2, 1.4), "hair")
    R.box("body", (-0.8, 9.0, 3.0), (1.6, 3.4, 1.3), "hair")
    R.box("body", (-1.2, 12.0, 2.95), (2.4, 0.6, 1.5), "flower")
    sym(R, "head", (3.55, 30.1, -2.4), (1.2, 1.2, 1.2), "flower")
    R.box("head", (4.75, 30.5, -2.0), (0.2, 0.4, 0.4), "yellow")
    # الجسم: قميص كريمي، صدرية خضرة برباط، أكتاف القميص منفوخة، تنورة واسعة (فوق وتحت أعرض) بحافة، مريلة بيضة
    R.box("body", (-4, 12, -2), (8, 12, 4), "blouse")
    R.box("body", (-4.1, 12.8, -2.2), (8.2, 7.4, 4.4), "bodice")
    R.box("body", (-3.2, 18.4, -2.55), (6.4, 1.8, 0.5), "bodice")
    R.box("body", (-0.2, 13.4, -2.5), (0.4, 6.4, 0.25), "lace")
    for y in (14.2, 15.8, 17.4):
        R.box("body", (-1.0, y, -2.5), (2.0, 0.3, 0.25), "lace")
    R.box("body", (-4.15, 20.1, -2.25), (8.3, 0.5, 4.5), "bodice_dk")
    R.box("body", (-4.5, 6.0, -2.6), (9.0, 7.2, 5.2), "skirt")
    R.box("body", (-5.0, 0.4, -3.3), (10.0, 5.8, 6.6), "skirt")
    R.box("body", (-5.05, 0.4, -3.35), (10.1, 0.9, 6.7), "skirt_dk")
    R.box("body", (-3.1, 2.8, -3.5), (6.2, 10.0, 0.35), "apron")
    R.box("body", (-4.6, 12.4, -2.75), (9.2, 1.0, 5.5), "apron")
    # الذراعين: كم منفوخ، طية، والكف؛ وسلة تفاح باليسرى
    def arm(b, sx):
        b((4, 14, -2), (4, 10, 4), "blouse")
        b((3.7, 19.6, -2.3), (4.6, 4.4, 4.6), "blouse")
        b((3.85, 14.0, -2.15), (4.3, 0.9, 4.3), "blouse_dk")
        b((4.1, 12, -1.9), (3.8, 2.0, 3.8), "skin")
    arms(R, arm)
    R.box("arm_l", (7.7, 7.0, -2.8), (3.6, 3.2, 5.6), "wicker")
    R.box("arm_l", (8.9, 10.2, -0.35), (0.7, 2.6, 0.7), "wicker")
    for o in ((8.0, 9.9, -2.2), (9.6, 10.0, -0.6), (8.2, 10.0, 1.0)):
        R.box("arm_l", o, (1.3, 1.3, 1.3), "apple")
    def leg(b, sx):
        b((0.2, 1.0, -1.9), (3.6, 9.0, 3.6), "blouse")
        b((0.0, 0, -2.4), (4.0, 1.5, 4.6), "shoes", top="shoes")
    legs(R, leg)
    return R


# ═══════════════════════════ توماس (رجل، الحداد) ═══════════════════════════
def man():
    R = humanoid("sh_townsman", {
        "skin": ("flat", (206, 152, 112), (206, 152, 112)),
        "skin_dk": ("flat", (176, 124, 90), (176, 124, 90)),
        "brow": ("flat", (54, 36, 26), (54, 36, 26)),
        "hair": ("fur", (64, 42, 28), (40, 26, 18)),
        "shirt": ("cloth", (224, 214, 192), (224, 214, 192)),
        "shirt_dk": ("cloth", (190, 178, 152), (190, 178, 152)),
        "apron": ("pelt", (112, 74, 44), (144, 100, 62)),
        "apron_dk": ("pelt", (74, 48, 28), (98, 66, 40)),
        "belt": ("pelt", (54, 36, 22), (76, 52, 32)),
        "pants": ("cloth", (88, 78, 66), (88, 78, 66)),
        "boots": ("pelt", (50, 34, 22), (74, 50, 32)),
        "iron": ("metal", (150, 154, 162), (150, 154, 162)),
        "wood": ("pelt", (112, 80, 48), (140, 104, 64)),
    }, 714)
    face(R, mouth=False)
    # شعر قصير، لحية قصيرة وشوارب وسوالف
    R.box("head", (-4.2, 30.7, -4.2), (8.4, 1.8, 8.4), "hair")
    R.box("head", (-4.2, 30.0, -4.35), (8.4, 0.9, 1.3), "hair")
    R.box("head", (-4.2, 25.6, 1.8), (8.4, 6.0, 2.6), "hair")
    sym(R, "head", (3.4, 26.8, -3.6), (0.9, 4.6, 6.0), "hair")
    R.box("head", (-3.6, 23.9, -4.5), (7.2, 2.3, 1.0), "hair")
    R.box("head", (-2.3, 22.9, -4.4), (4.6, 1.2, 1.0), "hair")
    R.box("head", (-2.2, 25.5, -4.55), (4.4, 0.8, 0.5), "hair")
    sym(R, "head", (3.35, 24.2, -4.3), (0.85, 3.4, 2.6), "hair")
    # الجسم: قميص كتان بفتحة رقبة، مريلة جلد من الصدر للركبة بحمالات وجيب، حزام
    R.box("body", (-4, 12, -2), (8, 12, 4), "shirt")
    R.box("body", (-1.0, 21.4, -2.15), (2.0, 2.6, 0.2), "skin")
    R.box("body", (-3.4, 5.6, -2.45), (6.8, 15.0, 0.5), "apron")
    sym(R, "body", (1.9, 20.4, -2.45), (1.1, 3.6, 0.5), "apron_dk")
    R.box("body", (-3.0, 13.6, 2.0), (6.0, 0.6, 0.35), "apron_dk", rot=(0, 0, 30), pivot=(0, 13.9, 2.1))
    R.box("body", (-3.0, 13.6, 2.0), (6.0, 0.6, 0.35), "apron_dk", rot=(0, 0, -30), pivot=(0, 13.9, 2.1))
    R.box("body", (-2.0, 8.6, -2.65), (4.0, 2.6, 0.25), "apron_dk")
    R.box("body", (-4.3, 12.2, -2.3), (8.6, 1.0, 4.6), "belt"); R.box("body", (-0.7, 12.0, -2.55), (1.4, 1.4, 0.3), "iron")
    # الذراعين: أكمام مطوية، ساعد مكشوف، وواقي جلد على الساعد الأيسر
    def arm(b, sx):
        b((4, 17, -2), (4, 7, 4), "shirt")
        b((3.85, 16.2, -2.15), (4.3, 1.3, 4.3), "shirt_dk")
        b((4.05, 12, -1.95), (3.9, 4.4, 3.9), "skin")
    arms(R, arm)
    R.box("arm_l", (3.9, 12.6, -2.1), (4.2, 2.4, 4.2), "apron_dk")
    # المطرقة باليمنى (نازلة)
    R.box("arm_r", (-6.5, 4.4, -1.0), (1, 9.0, 1), "wood")
    R.box("arm_r", (-7.6, 2.6, -2.4), (3.2, 2.0, 3.4), "iron")
    R.box("arm_r", (-7.7, 2.5, -2.5), (3.4, 0.4, 3.6), "apron_dk")
    def leg(b, sx):
        b((0, 2.6, -2), (4, 9.4, 4), "pants")
        b((-0.05, 0, -2.4), (4.1, 3.0, 4.6), "boots", top="boots")
    legs(R, leg)
    return R


# ═══════════════════════════ الأنيميشن والملفات ═══════════════════════════
ANIMS = {
    "format_version": "1.8.0",
    "animations": {
        # ضربة الحارس: الرمح يندفع لقدام (يتحرك ويا variable.attack_time اللي تعطيه اللعبة للوحوش اللي تهاجم)
        "animation.sh_city.attack": {"loop": True, "bones": {
            "arm_r": {"rotation": ["-math.sin(variable.attack_time*180)*80", 0, 0]},
            "body": {"rotation": [0, "math.sin(variable.attack_time*180)*10", 0]}}},
        # مشي بتنورة طويلة: خطوة أقصر حتى الرجلين ما تطلع من التنورة
        "animation.sh_city.walk_skirt": {"loop": True, "bones": {
            "leg_l": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*16*query.modified_move_speed", 0, 0]},
            "leg_r": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*-16*query.modified_move_speed", 0, 0]},
            "arm_l": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*-18*query.modified_move_speed", 0, 0]},
            "arm_r": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*18*query.modified_move_speed", 0, 0]}}},
    },
}

NPCS = [
    # (المعرف، الموديل، الاسم، ألوان البيضة، أنيميشن المشي، هجوم؟)
    ("sh:city_guard", "sh_city_guard", "City Guard", ("#2846a8", "#c8ccd6"), "animation.sh_trainer.walk", True),
    ("sh:aetheria_king", "sh_aetheria_king", "King Aldric", ("#961a26", "#ecc048"), "animation.sh_trainer.walk", False),
    ("sh:townswoman", "sh_townswoman", "Mira", ("#366c3e", "#eee4d0"), "animation.sh_city.walk_skirt", False),
    ("sh:townsman", "sh_townsman", "Tomas", ("#704a2c", "#e0d6c0"), "animation.sh_trainer.walk", False),
]


def client(ident, model, egg, walk, attack):
    anims = {"idle": "animation.sh_trainer.idle", "walk": walk, "look": "animation.sh.look"}
    if attack:
        anims["attack"] = "animation.sh_city.attack"
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": ident, "materials": {"default": "entity_alphatest"}, "textures": {"default": f"textures/entity/{model}"},
        "geometry": {"default": f"geometry.{model}"}, "animations": anims, "scripts": {"animate": list(anims.keys())},
        "render_controllers": ["controller.render.sh_default"], "spawn_egg": {"base_color": egg[0], "overlay_color": egg[1]}}}}


MONSTERS = {"any_of": [{"test": "is_family", "subject": "other", "value": "monster"}, {"test": "is_family", "subject": "other", "value": "sh_monster"}]}
TALK = {"interactions": [{"on_interact": {"filters": {"all_of": [{"test": "is_family", "subject": "other", "value": "player"}]}, "event": "sh:talk"}, "interact_text": "Talk"}]}


def behavior(ident):
    c = {
        "minecraft:type_family": {"family": ["sh_npc", "npc", "sh_city"]},
        "minecraft:collision_box": {"width": 0.6, "height": 1.9},
        "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "can_pass_doors": True, "can_open_doors": True, "avoid_damage_blocks": True},
        "minecraft:movement.basic": {},
        "minecraft:jump.static": {},
        "minecraft:can_climb": {},
        "minecraft:physics": {},
        "minecraft:persistent": {},
        "minecraft:nameable": {},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.look_at_player": {"priority": 8, "look_distance": 8, "probability": 0.6},
        "minecraft:behavior.random_look_around": {"priority": 9},
        "minecraft:interact": TALK,
    }
    if ident == "sh:city_guard":
        # حارس: صحة 40، ضربة 6، يطارد الوحوش القريبة (20 بلوكة) ويرجع لمكانه، اللاعب ما يقدر يأذيه وهو ما يرد على اللاعب
        c["minecraft:type_family"]["family"].append("city_guard")
        c.update({
            "minecraft:health": {"value": 40, "max": 40},
            "minecraft:attack": {"damage": 6},
            "minecraft:movement": {"value": 0.27},
            "minecraft:home": {"restriction_radius": 18, "restriction_type": "random_movement"},
            "minecraft:behavior.hurt_by_target": {"priority": 1, "entity_types": {"filters": {"none_of": [{"test": "is_family", "subject": "other", "value": "player"}, {"test": "is_family", "subject": "other", "value": "sh_city"}]}}},
            "minecraft:behavior.nearest_attackable_target": {"priority": 2, "must_see": True, "reselect_targets": True, "within_radius": 20,
                                                             "entity_types": [{"filters": MONSTERS, "max_dist": 20}]},
            "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.25, "track_target": True},
            "minecraft:behavior.move_towards_home_restriction": {"priority": 5, "speed_multiplier": 1.0},
            "minecraft:behavior.random_stroll": {"priority": 7, "speed_multiplier": 0.7, "xz_dist": 6},
            "minecraft:damage_sensor": {"triggers": [
                {"on_damage": {"filters": {"any_of": [{"test": "is_family", "subject": "other", "value": "player"}, {"test": "is_family", "subject": "other", "value": "sh_city"}]}}, "deals_damage": "no"},
                {"cause": "fall", "deals_damage": "no"}]},
        })
    elif ident == "sh:aetheria_king":
        # الملك: واقف قدام العرش (ما يمشي)، ما يتأذى
        c.update({
            "minecraft:health": {"value": 100, "max": 100},
            "minecraft:movement": {"value": 0.0},
            "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]},
        })
        c["minecraft:behavior.look_at_player"] = {"priority": 1, "look_distance": 10, "probability": 1.0}
    else:
        # الناس: يتمشون قرب مكانهم، يهربون من الوحوش، وما يتأذون
        c.update({
            "minecraft:health": {"value": 20, "max": 20},
            "minecraft:movement": {"value": 0.22},
            "minecraft:home": {"restriction_radius": 12, "restriction_type": "random_movement"},
            "minecraft:behavior.avoid_mob_type": {"priority": 1, "entity_types": [{"filters": MONSTERS, "max_dist": 8, "walk_speed_multiplier": 1.1, "sprint_speed_multiplier": 1.35}]},
            "minecraft:behavior.move_towards_home_restriction": {"priority": 4, "speed_multiplier": 0.9},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.6, "xz_dist": 6},
            "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]},
        })
    return {"format_version": "1.21.50", "minecraft:entity": {
        "description": {"identifier": ident, "is_spawnable": True, "is_summonable": True, "is_experimental": False},
        "components": c, "events": {"sh:talk": {}}}}


def write_json(path, obj, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)
        f.write("\n")


def lang():
    p = os.path.join(RP, "texts", "en_US.lang")
    lines = open(p, encoding="utf-8").read().splitlines()
    keep = [l for l in lines if not any(l.startswith(f"entity.{i}.name=") or l.startswith(f"item.spawn_egg.entity.{i}.name=") for i, *_ in NPCS)]
    for ident, _m, name, *_ in NPCS:
        keep += [f"entity.{ident}.name={name}", f"item.spawn_egg.entity.{ident}.name={name} Egg"]
    open(p, "w", encoding="utf-8").write("\n".join(keep) + "\n")


def main():
    builders = {"sh_city_guard": guard, "sh_aetheria_king": king, "sh_townswoman": woman, "sh_townsman": man}
    rigs = {}
    for ident, model, name, egg, walk, attack in NPCS:
        R = builders[model]()
        n = R.save(2.6 if model != "sh_city_guard" else 2.8, width=2)
        rigs[model] = R
        print(f"{name}: {n} cubes, zfixed {R.zfixed}")
        write_json(os.path.join(RP, "entity", f"{model}.entity.json"), client(ident, model, egg, walk, attack))
        write_json(os.path.join(BP, "entities", f"{model}.json"), behavior(ident))
    write_json(os.path.join(RP, "animations", "sh_city.animation.json"), ANIMS)
    lang()
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        import render as RR
        os.makedirs(out, exist_ok=True)
        for _i, model, name, *_ in NPCS:
            m = RR.Model(os.path.join(RP, "models", "entity", f"{model}.geo.json"), os.path.join(RP, "textures", "entity", f"{model}.png"))
            RR.contact_sheet(m, [(name, {})], views=((0, 10), (35, 10), (150, 10), (270, 10)), size=320, game=True).save(os.path.join(out, f"{model}.png"))
        print("معاينة:", out)


if __name__ == "__main__":
    main()
