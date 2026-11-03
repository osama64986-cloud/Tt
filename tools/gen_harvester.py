"""الحاصد الأجوف (sh:hollow_harvester، رتبة Cursed): فزّاعة ملعونة تتحرك مثل دمية خيوط.
الموديل + التكستشر (عادي، ومحروق لما يشتعل: ضعفه النار) + أيقونة المنجل وأيتمه (المنجل يسقط منه بس).
الشكل: راس كيس خيش مربوط بحبل، عيون محروقة تتوهج بنفسجي وفم مخيط، قبعة قش عريضة مايلة بريشة غراب،
معطف طويل ممزق مفتوح من قدام (قميص خيش وقش طالع منه)، حزام حبل، رقع، أكمام ممزقة وإيدين حزم قش،
رجلين بنطلون خيش مرقع ينتهي بقش وأوتاد خشب، المنجل الكبير بإيده اليمين (جزء من الموديل: عظمة scythe)،
وفوق راسه صليب دمية خشبي عائم (بدون أحد ماسكه) نازلة منه 3 خيوط للكتفين والقبعة.
العظام: root > body > (head > hat)، arm_l، arm_r > scythe، control | leg_l، leg_r. القدام = -z، الأرض y=0.
التشغيل: python3 tools/gen_harvester.py"""
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_grim_monsters import Rig, RP  # noqa: E402
import gen_icons2d as I2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")

MATS = {
    "burlap": ("cloth", (168, 136, 90), (124, 98, 62)),
    "burlap_dk": ("cloth", (128, 100, 66), (96, 72, 46)),
    "straw": ("wool", (226, 192, 98), (150, 116, 46)),
    "hat": ("wool", (198, 162, 82), (126, 96, 42)),
    "band": ("cloth", (66, 32, 44), (42, 20, 30)),
    "feather": ("flat", (30, 24, 40), (30, 24, 40)),
    "coat": ("cloth", (74, 62, 84), (44, 36, 52)),
    "coat_dk": ("cloth", (50, 42, 60), (32, 26, 40)),
    "patch": ("cloth", (124, 74, 52), (88, 50, 36)),
    "patch2": ("cloth", (84, 98, 72), (54, 64, 46)),
    "rope": ("wool", (160, 132, 86), (108, 86, 52)),
    "wood": ("fur", (96, 72, 52), (62, 46, 34)),
    "metal": ("metal", (108, 110, 124), (168, 170, 184)),
    "edge": ("flat", (206, 208, 220), (206, 208, 220)),
    "rust": ("rock", (126, 66, 36), (86, 44, 24)),
    "eye": ("glow", (170, 70, 255), (252, 236, 255)),
    "curse": ("glow", (136, 46, 220), (226, 186, 255)),
    "stitch": ("flat", (40, 26, 20), (40, 26, 20)),
    "mouth": ("flat", (16, 10, 16), (16, 10, 16)),
    "string": ("flat", (232, 224, 204), (232, 224, 204)),
}
# محروق (لما يشتعل): خيش متفحم، قش أسود بأطراف جمر، وعيون برتقالية مثل الجمر
SCORCHED = {
    "burlap": ("cloth", (84, 62, 46), (52, 38, 28)),
    "burlap_dk": ("cloth", (62, 46, 34), (40, 28, 20)),
    "straw": ("lava", (70, 44, 24), (255, 150, 40)),
    "hat": ("lava", (72, 50, 28), (255, 132, 36)),
    "coat": ("cloth", (46, 38, 48), (28, 22, 30)),
    "coat_dk": ("cloth", (34, 28, 38), (22, 18, 26)),
    "rope": ("wool", (86, 64, 40), (52, 38, 24)),
    "eye": ("glow", (255, 120, 30), (255, 240, 190)),
    "curse": ("glow", (255, 90, 30), (255, 220, 160)),
}


def harvester():
    R = Rig("sh_hollow_harvester", MATS, seed=131)
    R.bone("root", pivot=(0, 0, 0))
    # ── الرجلين: بنطلون خيش مرقع، قش عند الكاحل، وتد خشب كقدم ──
    for nm, x in (("leg_l", 2.3), ("leg_r", -2.3)):
        R.bone(nm, "root", (x, 17, 0))
        R.box(nm, (x - 1.6, 3.0, -1.6), (3.2, 14.0, 3.2), "burlap_dk", top="burlap")
        R.box(nm, (x - 1.8, 1.6, -1.8), (3.6, 1.8, 3.6), "straw")                          # قش الكاحل
        for k, (dx, dz, h) in enumerate(((-1.9, -0.6, 2.2), (1.5, 0.9, 1.9), (0.3, -2.1, 2.0), (-0.6, 1.6, 1.7))):
            R.box(nm, (x + dx - 0.3, 0.6 + (k % 2) * 0.3, dz - 0.3), (0.6, h, 0.6), "straw")    # قشات طالعة
        R.box(nm, (x - 0.8, 0.0, -0.8), (1.6, 1.8, 1.6), "wood")                           # الوتد (القدم)
        R.box(nm, (x - 1.0, 10.0, -1.6), (2.0, 2.2, 3.2), "rope")                          # ربطة حبل على الركبة
        if nm == "leg_l":
            R.box(nm, (x - 0.9, 5.6, -1.8), (1.8, 2.4, 0.2), "patch")                       # رقعة
        else:
            R.box(nm, (x - 1.8, 12.4, -0.9), (0.2, 2.2, 1.8), "patch2")
    # ── الجذع: قميص خيش، معطف مفتوح من قدام بذيل ممزق، حزام حبل، ياقة مرفوعة، قش طالع ──
    R.bone("body", "root", (0, 17, 0))
    R.box("body", (-3.6, 17.0, -2.0), (7.2, 13.6, 4.0), "burlap")                          # القميص
    R.box("body", (-4.6, 12.6, 0.9), (9.2, 18.4, 1.5), "coat")                             # ظهر المعطف
    R.box("body", (2.2, 12.6, -2.5), (2.4, 18.4, 3.4), "coat")                             # جانب يسار
    R.box("body", (-4.6, 12.6, -2.5), (2.4, 18.4, 3.4), "coat")                            # جانب يمين
    R.box("body", (-4.8, 29.2, -2.7), (9.6, 1.8, 5.4), "coat_dk")                          # كتف المعطف
    for sx in (-1, 1):                                                                      # ياقة مرفوعة
        R.box("body", (sx * 3.2 - 1.2, 30.8, -1.8), (2.4, 2.4, 3.8), "coat_dk")
    # ذيل ممزق: شرائط بأطوال مختلفة تحت المعطف (ورا وعلى الجانبين)
    for x, L in ((-4.2, 2.6), (-2.5, 1.2), (-0.8, 3.0), (0.9, 1.6), (2.6, 2.4)):
        R.box("body", (x, 12.6 - L, 1.0), (1.6, L, 1.3), "coat_dk")
    for sx in (-1, 1):
        for k, (dx, L) in enumerate(((0.0, 2.2), (1.2, 3.2))):
            x0 = 2.3 + dx if sx > 0 else -4.5 + dx
            R.box("body", (x0, 12.6 - L, -2.4 + k * 1.6), (1.1, L, 1.5), "coat_dk")
    R.box("body", (-4.75, 18.0, -2.65), (9.5, 1.0, 5.2), "rope")                           # حزام الحبل
    R.box("body", (-0.8, 17.2, -2.95), (1.6, 1.8, 0.4), "rope")                            # العقدة
    R.box("body", (-0.7, 14.6, -2.9), (0.5, 2.6, 0.35), "rope")
    R.box("body", (0.3, 15.2, -2.9), (0.5, 2.0, 0.35), "rope")
    R.box("body", (2.5, 22.0, -2.7), (1.9, 2.2, 0.2), "patch")                             # رقع المعطف
    R.box("body", (-4.8, 14.6, -1.0), (0.2, 2.4, 2.0), "patch2")
    R.box("body", (-3.0, 24.0, 2.4), (2.2, 2.6, 0.2), "patch")
    R.box("body", (-0.8, 24.4, -2.15), (1.6, 1.6, 0.15), "curse")                          # قلب ملعون يضوي من ورا الخيش
    for x, y in ((-1.2, 26.4), (0.6, 21.0), (-1.6, 20.0)):                                  # قش طالع من فتحة القميص
        R.box("body", (x, y, -2.3), (0.6, 2.0, 0.6), "straw", rot=[0, 0, 25 if x < 0 else -25])
    R.box("body", (-2.2, 30.4, -2.2), (4.4, 1.2, 4.4), "straw")                            # قش الرقبة
    # ── الإيدين: كم معطف ممزق وكف من حزمة قش بأصابع قش ──
    for nm, sx in (("arm_l", 1), ("arm_r", -1)):
        x = sx * 5.65
        R.bone(nm, "body", (x, 30.0, 0))
        R.box(nm, (x - 1.45, 18.6, -1.5), (2.9, 11.6, 3.0), "coat")
        R.box(nm, (x - 1.65, 18.0, -1.7), (3.3, 1.4, 3.4), "coat_dk")                     # الكفة
        R.box(nm, (x - 1.3, 16.4, -1.6), (1.0, 1.6, 1.2), "coat_dk")                      # شريطة ممزقة
        R.box(nm, (x - 1.05, 14.2, -1.0), (2.1, 4.0, 2.0), "straw")                       # الكف
        for k, (dx, dz) in enumerate(((-0.8, -0.8), (0.1, -1.0), (0.8, -0.4), (-0.4, 0.6))):
            R.box(nm, (x + dx - 0.25, 12.4 + (k % 2) * 0.4, dz - 0.25), (0.5, 2.0, 0.5), "straw")   # أصابع قش
        R.box(nm, (x - 1.5, 26.0, -1.6), (1.6, 1.8, 0.2) if sx > 0 else (1.8, 1.6, 0.2), "patch2" if sx > 0 else "patch")
    # ── المنجل بالإيد اليمين: عصا عمودية تمر بالكف، والنصل فوق لقدام (-z) وحده المقعر لتحت ──
    R.bone("scythe", "arm_r", (-5.65, 16.0, -1.0))
    sx0, sz0 = -5.65, -1.0
    R.box("scythe", (sx0 - 0.75, 1.4, sz0 - 0.75), (1.5, 1.2, 1.5), "metal")              # غطاء أسفل العصا
    for k in range(13):                                                                    # العصا بقطاعات (لون واحد، الحبوب من التكستشر)
        R.box("scythe", (sx0 - 0.6, 2.6 + k * 2.9, sz0 - 0.6), (1.2, 2.9, 1.2), "wood")
    top = 2.6 + 13 * 2.9                                                                   # ~40.3
    for k in range(4):                                                                     # لف حبل عند القبضة (تحت الكف وفوقه)
        R.box("scythe", (sx0 - 0.75, 11.6 + k * 1.3 + (5.0 if k >= 2 else 0), sz0 - 0.75), (1.5, 0.8, 1.5), "rope")
    R.box("scythe", (sx0 - 0.5, 24.0, sz0 + 0.6), (1.0, 1.0, 2.6), "wood")                # المقبض الجانبي (لورا)
    R.box("scythe", (sx0 - 0.95, top - 2.4, sz0 - 0.95), (1.9, 3.2, 1.9), "metal")        # جلبة الراس
    R.box("scythe", (sx0 - 1.0, top - 1.2, sz0 - 1.0), (2.0, 0.6, 2.0), "rust")
    R.box("scythe", (sx0 - 1.08, top - 0.8, sz0 - 0.4), (0.12, 0.8, 0.8), "curse")       # عين الجلبة
    R.box("scythe", (sx0 + 0.96, top - 0.8, sz0 - 0.4), (0.12, 0.8, 0.8), "curse")
    R.box("scythe", (sx0 - 0.4, top - 1.4, sz0 + 0.9), (0.8, 0.9, 1.8), "metal")         # شوكة خلفية
    n, seg = 16, 1.35

    def spine(t):
        return top + 1.6 + 1.6 * math.sin(math.pi * min(1.0, t * 1.8)) * (1 - t) - 10.5 * t ** 2.0

    def width(t):
        return 5.6 * (1 - t) ** 0.8 + 0.45
    for i in range(n):
        t = i / (n - 1)
        z1 = sz0 - 0.9 - i * seg                                                           # النصل يمتد لقدام (-z)
        y_top, wd = spine(t), width(t)
        th = 1.0 - 0.45 * t
        sp = min(0.6, wd * 0.25)
        ed = max(0.3, wd * 0.28)
        body = wd - sp - ed
        R.box("scythe", (sx0 - th / 2, y_top - sp, z1 - seg), (th, sp, seg), "metal")
        if body > 0.05:
            R.box("scythe", (sx0 - th * 0.46, y_top - sp - body, z1 - seg), (th * 0.92, body, seg), "rust" if i in (3, 9) else "metal")
        R.box("scythe", (sx0 - th * 0.35, y_top - wd, z1 - seg), (th * 0.7, ed, seg), "edge")
        if i < n - 1:
            R.box("scythe", (sx0 - th * 0.22, y_top - wd - 0.3, z1 - seg), (th * 0.44, 0.3, seg), "curse")
    # ── الراس: كيس خيش مربوط، عيون متوهجة غير متساوية، فم مخيط مبتسم، أنف غرزة، رقعة، قش طالع ──
    R.bone("head", "body", (0, 31.0, 0))
    R.box("head", (-4.0, 31.6, -4.0), (8.0, 8.4, 8.0), "burlap", top="burlap_dk")
    R.box("head", (-2.8, 31.0, -2.8), (5.6, 1.2, 5.6), "rope")                             # ربطة الرقبة
    R.box("head", (0.9, 35.3, -4.25), (2.0, 1.9, 0.25), "eye")                             # العين اليسار (أكبر)
    R.box("head", (-2.9, 35.0, -4.25), (1.7, 1.5, 0.25), "eye")                            # العين اليمين (أوطى وأصغر)
    for (x, y) in ((0.6, 37.4), (2.9, 37.2), (0.7, 35.0), (-3.2, 36.7), (-1.1, 36.7)):      # غرز حول العيون
        R.box("head", (x, y, -4.2), (0.35, 0.35, 0.18), "stitch")
    R.box("head", (-2.9, 33.0, -4.15), (5.8, 0.6, 0.15), "mouth")                          # الفم
    for k in range(7):                                                                     # غرز الفم
        R.box("head", (-2.55 + k * 0.85, 32.5, -4.3), (0.3, 1.5, 0.15), "stitch")
    for sx in (-1, 1):
        R.box("head", (sx * 3.15 - 0.3, 33.5, -4.15), (0.6, 0.6, 0.15), "mouth")         # طرفين الابتسامة
    R.box("head", (-0.35, 34.2, -4.2), (0.7, 0.7, 0.2), "stitch")                         # الأنف
    R.box("head", (-3.6, 37.5, -4.18), (1.6, 1.6, 0.18), "patch2")                        # رقعة
    for (x, z, h, r) in ((3.9, -1.2, 2.2, -20), (-4.4, 1.0, 2.0, 22), (3.8, 2.2, 1.6, -15)):
        R.box("head", (x, 37.4, z), (0.5, h, 0.5), "straw", rot=[0, 0, r])
    # ── القبعة: حافة عريضة، تاج بحزام وريشة غراب، مايلة شوية، وقش نازل من تحتها ──
    R.bone("hat", "head", (0, 40.0, 0), rotation=[0, 0, -7])
    R.box("hat", (-6.6, 39.8, -6.6), (13.2, 0.8, 13.2), "hat")
    R.box("hat", (-3.6, 40.6, -3.6), (7.2, 4.2, 7.2), "hat")
    R.box("hat", (-3.7, 40.6, -3.7), (7.4, 1.1, 7.4), "band")
    R.box("hat", (-2.6, 44.8, -2.6), (5.2, 0.6, 5.2), "hat")
    R.box("hat", (3.75, 41.0, -1.4), (0.4, 3.6, 1.2), "feather", rot=[0, 0, -18], pivot=[3.9, 41.0, -0.8])
    R.box("hat", (-6.4, 39.0, -6.8), (4.0, 0.8, 1.2), "hat")                               # طرف الحافة نازل
    for (x, z, h) in ((5.0, -5.4, 2.4), (-5.6, -3.0, 1.8), (5.8, 3.4, 2.0), (-4.4, 5.6, 2.2), (1.8, -6.2, 1.6)):
        R.box("hat", (x - 0.25, 39.8 - h, z - 0.25), (0.5, h, 0.5), "straw")
    # ── صليب الدمية العائم فوق راسه + 3 خيوط نازلة للكتفين وأعلى القبعة ──
    R.bone("control", "body", (0, 56.0, 0))
    R.box("control", (-7.6, 55.5, -0.5), (15.2, 1.0, 1.0), "wood")
    R.box("control", (-0.5, 55.5, -4.6), (1.0, 1.0, 9.2), "wood")
    R.box("control", (-0.8, 56.5, -0.8), (1.6, 0.4, 1.6), "curse")
    for x in (-6.95, 6.95):                                                               # برا حافة القبعة، على طرف الكتف
        R.box("control", (x - 0.15, 30.0, -0.15), (0.3, 25.5, 0.3), "string")
        R.box("control", (x - 0.35, 55.0, -0.35), (0.7, 0.5, 0.7), "rope")
    R.box("control", (-0.15, 45.4, -0.15), (0.3, 10.1, 0.3), "string")
    return R


# ───────────────────────── أيقونة المنجل (32×32) ─────────────────────────
def scythe_icon():
    WOOD_A, WOOD_B = (104, 78, 56), (70, 52, 38)
    TWINE, TWINE_HI = (170, 140, 90), (210, 182, 124)
    IRON, IRON_HI = (84, 86, 98), (140, 142, 156)
    SPINE, BODY, EDGE, EDGE_HI = (58, 58, 70), (112, 114, 128), (196, 198, 212), (246, 246, 255)
    CURSE, CURSE_HI = (150, 70, 230), (220, 170, 255)
    fr = I2.Frame(12.5, 30.5, 74)                                    # العصا من تحت لفوق (مايلة شوية لليمين)
    parts = [I2.rect_part(fr, 0.0, 25.0, -0.9, 0.9, WOOD_A, WOOD_B)]
    parts.append(I2.rect_part(fr, -1.0, 0.6, -1.2, 1.2, IRON, IRON_HI))
    for a in (4.0, 5.6, 7.2):
        parts.append(I2.rect_part(fr, a, a + 0.9, -1.2, 1.2, TWINE, TWINE_HI))
    parts.append(I2.rect_part(fr, 22.4, 25.4, -1.5, 1.5, IRON, IRON_HI))
    ax, ay = fr.x0 + fr.ux * 24.0, fr.y0 + fr.uy * 24.0                # مكان ربط النصل (راس العصا)
    L = ax - 1.6                                                      # طول النصل لليسار لحد حافة الأيقونة

    def spine(t):                                                     # الظهر: يرتفع شوية ثم ينحني لتحت للطرف
        return ay - 1.6 - 1.6 * math.sin(math.pi * min(1.0, t * 1.5)) * (1 - t) + 7.0 * t ** 2

    def width(t):
        return 4.6 * (1 - t) ** 0.75 + 0.6

    def blade(x, y):
        t = (ax + 0.8 - x) / L
        if t < 0 or t > 1:
            return None
        y0 = spine(t); w = width(t)
        if y < y0 or y > y0 + w:
            return None
        f = (y - y0) / w
        if f < 0.22:
            return SPINE
        if f > 0.7:
            return EDGE_HI if t > 0.15 and (int(x) % 4 == 1) else EDGE
        return BODY

    def curse_line(x, y):
        t = (ax + 0.8 - x) / L
        if t < 0.06 or t > 0.93:
            return None
        yb = spine(t) + width(t)
        if yb - 0.55 <= y <= yb + 0.45:
            return CURSE_HI if int(x) % 3 == 0 else CURSE
        return None
    parts += [blade, curse_line]
    parts.append(I2.rect_part(fr, 23.2, 24.4, -0.5, 0.5, CURSE, CURSE_HI))
    return I2.render(parts, "scythe")


def scythe_item():
    item = {"format_version": "1.21.60", "minecraft:item": {
        "description": {"identifier": "sh:harvest_scythe", "menu_category": {"category": "equipment"}},
        "components": {"minecraft:icon": {"textures": {"default": "sh_scythe"}}, "minecraft:max_stack_size": 1,
                       "minecraft:hand_equipped": True, "minecraft:display_name": {"value": "§5Harvester's Scythe"}}}}
    with open(os.path.join(BP, "items", "sh_harvest_scythe.json"), "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, ensure_ascii=False)
        f.write("\n")
    p = os.path.join(RP, "textures", "item_texture.json")
    d = json.load(open(p, encoding="utf-8"))
    d["texture_data"]["sh_scythe"] = {"textures": "textures/items/sh_scythe"}
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    R = harvester()
    n = R.save(3.7, hot=SCORCHED, width=4)
    scythe_icon()
    scythe_item()
    print("hollow harvester cubes:", n, "zfixed:", R.zfixed)
    prev = os.environ.get("PREVIEW_DIR")
    if prev:
        im = Image.open(os.path.join(RP, "textures", "items", "sh_scythe.png"))
        im.resize((320, 320), Image.NEAREST).save(os.path.join(prev, "scythe_icon.png"))


if __name__ == "__main__":
    main()
