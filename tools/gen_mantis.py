"""السرعوف المصلّي (sh:prayer_mantis، رتبة Cursed): موديل + 3 تكستشرات (عادي، بعد الانسلاخ، تمويه شبه شفاف).
الشكل: صدر طويل مرفوع ومايل لقدام، راس مثلث بعيون مركبة بنفسجية متوهجة وقرون استشعار، ذراعين مفترسة مطوية بوضعية الصلاة
(حرقفة نازلة، فخذ ثخين مرفوع بأشواك، ساق مطوية بحافة نصل وخطاف)، 4 أرجل طويلة مثل العنكبوت، بطن مقسم يرتفع شوي بالآخر،
وجناحين ورقيين فوق البطن بعرق وسطي وعين ملعونة متوهجة على كل جناح.
العظام: root > body > (abdomen > wing_l/wing_r)، leg_ml/leg_mr/leg_bl/leg_br، thorax > head > ant_l/ant_r، arm_l > fore_l > claw_l (ونفسها يمين).
القدام = -z، الأرض y=0. التشغيل: python3 tools/gen_mantis.py"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_grim_monsters import Rig, RP, TILE  # noqa: E402

MATS = {
    "shell": ("chitin", (104, 176, 70), (60, 118, 40)),
    "shell_dk": ("chitin", (66, 128, 48), (32, 72, 28)),
    "belly": ("flat", (182, 216, 120), (182, 216, 120)),
    "wing": ("leaf", (150, 204, 92), (66, 122, 46)),
    "wing_dk": ("leaf", (122, 180, 74), (52, 100, 38)),
    "joint": ("flat", (38, 70, 32), (38, 70, 32)),
    "blade": ("bone", (226, 238, 190), (150, 168, 112)),
    "spine": ("obsidian", (44, 32, 58), (120, 84, 160)),
    "eye": ("glow", (190, 70, 255), (250, 222, 255)),
    "pupil": ("flat", (34, 10, 48), (34, 10, 48)),
    "curse": ("glow", (150, 50, 230), (236, 196, 255)),
    "mouth": ("flat", (92, 60, 40), (92, 60, 40)),
}
# بعد الانسلاخ (الجلد الجديد): أخضر أفتح مايل للزيتي، وعيون وعلامات اللعنة أقوى (وردي بنفسجي)
MOLT = {
    "shell": ("chitin", (150, 210, 110), (84, 150, 64)),
    "shell_dk": ("chitin", (96, 160, 74), (48, 96, 40)),
    "wing": ("leaf", (160, 214, 112), (70, 132, 54)),
    "wing_dk": ("leaf", (120, 184, 86), (56, 110, 44)),
    "eye": ("glow", (255, 70, 200), (255, 230, 250)),
    "curse": ("glow", (230, 60, 210), (255, 214, 250)),
    "blade": ("bone", (250, 222, 255), (180, 120, 210)),
}


def mantis():
    R = Rig("sh_prayer_mantis", MATS, seed=77)
    R.sc = (1.25, 1.25, 1.25)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 17, 1))
    # ── الصدر الخلفي (بين الأرجل) ──
    R.box("body", (-3.0, 14.4, -3.4), (6.0, 5.2, 8.4), "shell", bottom="belly")
    R.box("body", (-2.4, 19.6, -2.8), (4.8, 0.6, 7.2), "shell_dk")
    for z in (-1.0, 3.5):                                                     # مفاصل الأرجل على الجانبين
        for sx in (-1, 1):
            R.box("body", (sx * 3.0 - 0.9 + (0.9 if sx > 0 else -0.9) * 0, 15.2, z - 0.9), (1.8, 1.8, 1.8), "joint")
    # ── البطن: 6 حلقات تكبر ثم تصغر وترتفع شوي لورا، بطن فاتح تحت ──
    R.bone("abdomen", "body", (0, 17, 4.6))
    ws = (7.0, 8.4, 9.2, 8.8, 7.6, 5.6)
    hs = (5.6, 6.2, 6.6, 6.2, 5.4, 4.2)
    for k, (w, h) in enumerate(zip(ws, hs)):
        z0 = 4.6 + k * 3.0
        cy = 17.0 + k * 0.35 + (k * k) * 0.06
        R.box("abdomen", (-w / 2, cy - h / 2, z0), (w, h, 3.0), "shell" if k % 2 == 0 else "shell_dk", bottom="belly")
        R.box("abdomen", (-w / 2 + 0.6, cy - h / 2 - 0.4, z0 + 0.3), (w - 1.2, 0.4, 2.4), "belly")      # حزام البطن الفاتح
    R.box("abdomen", (-1.8, 18.2, 22.6), (3.6, 2.8, 1.6), "shell_dk")                              # طرف البطن
    for sx in (-1, 1):
        R.box("abdomen", (sx * 1.2 - 0.3, 18.8, 24.0), (0.6, 0.6, 2.2), "joint")                  # زوائد ذيلية (cerci)
    # ── الجناحين: ورقتين فوق البطن (اليمين فوق اليسار مثل السرعوف الحقيقي)، عرق وسطي، وعين ملعونة متوهجة ──
    def top_at(z):                                                             # ارتفاع ظهر البطن عند z (حتى الجناح يلبس فوقه)
        k = max(0.0, min(5.0, (z - 4.6) / 3.0 - 0.5))
        i = int(k); t = k - i; j = min(5, i + 1)
        tops = [17.0 + q * 0.35 + q * q * 0.06 + hs[q] / 2 for q in range(6)]
        return tops[i] + (tops[j] - tops[i]) * t
    prof = (2.6, 4.0, 5.0, 5.7, 6.1, 6.2, 6.0, 5.4, 4.4, 3.0, 1.4)
    for nm, sx, lift in (("wing_l", 1, 0.0), ("wing_r", -1, 0.45)):
        R.bone(nm, "abdomen", (sx * 0.6, 20.6, 3.2))
        for k, w in enumerate(prof):
            z0 = 3.0 + k * 2.0
            y0 = top_at(z0 + 1.0) + 0.1 + lift
            x0 = -0.4 if sx > 0 else -w + 0.4
            R.box(nm, (x0, y0, z0), (w, 0.7, 2.0), "wing" if k % 3 else "wing_dk", bottom="wing_dk")
        for k in range(10):                                                    # العرق الوسطي (أغمق) على طول الجناح
            z0 = 3.4 + k * 2.0
            R.box(nm, (sx * 2.6 - 0.3, top_at(z0 + 1.0) + 0.8 + lift, z0), (0.6, 0.2, 2.0), "joint")
        R.box(nm, (sx * 3.0 - 1.3, top_at(13.0) + 0.85 + lift, 11.8), (2.6, 0.25, 2.6), "curse")     # عين ملعونة على الجناح
        R.box(nm, (sx * 3.0 - 0.45, top_at(13.0) + 1.0 + lift, 12.65), (0.9, 0.2, 0.9), "pupil")
    # ── 4 أرجل طويلة: فخذ يطلع لفوق ولبرا لركبة عالية، ساق تنزل للأرض، وقدم ──
    for nm, sx, z, yaw in (("leg_ml", 1, -1.0, -24), ("leg_mr", -1, -1.0, 24), ("leg_bl", 1, 3.5, 26), ("leg_br", -1, 3.5, -26)):
        R.bone(nm, "body", (sx * 3.0, 16.0, z), rotation=[0, yaw, 0])
        fl = 9.6 if nm.startswith("leg_m") else 10.6
        ang = 38
        kx, ky = sx * (3.0 + fl * math.cos(math.radians(ang))), 16.0 + fl * math.sin(math.radians(ang))
        if sx > 0:
            R.box(nm, (3.0, 15.3, z - 0.7), (fl, 1.4, 1.4), "shell", rot=[0, 0, ang], pivot=[3.0, 16.0, z])
        else:
            R.box(nm, (-3.0 - fl, 15.3, z - 0.7), (fl, 1.4, 1.4), "shell", rot=[0, 0, -ang], pivot=[-3.0, 16.0, z])
        R.box(nm, (kx - 0.8, ky - 0.8, z - 0.8), (1.6, 1.6, 1.6), "joint")                        # الركبة
        tl = ky - 1.0
        tilt = 9
        R.box(nm, (kx - 0.55, ky - tl, z - 0.55), (1.1, tl, 1.1), "shell_dk", rot=[0, 0, sx * tilt], pivot=[kx, ky, z])
        fx = kx + sx * tl * math.sin(math.radians(tilt))
        R.box(nm, (fx - 0.6 if sx > 0 else fx - 1.6, 0.0, z - 0.6), (2.2, 0.7, 1.2), "joint")   # القدم على الأرض (لبرا)
    # ── الصدر الأمامي الطويل (prothorax): مصمم عمودي ثم مايل 32° لقدام ──
    R.bone("thorax", "body", (0, 18.0, -2.4), rotation=[32, 0, 0])
    R.box("thorax", (-2.3, 17.0, -4.6), (4.6, 6.4, 4.2), "shell", bottom="belly")
    R.box("thorax", (-1.8, 23.2, -4.3), (3.6, 6.4, 3.6), "shell")
    R.box("thorax", (-2.5, 29.4, -4.9), (5.0, 4.0, 4.4), "shell", top="shell_dk")
    R.box("thorax", (-1.0, 18.0, -4.95), (2.0, 11.0, 0.4), "belly")                                # بطن الرقبة الفاتح
    R.box("thorax", (-0.6, 18.4, -0.5), (1.2, 14.6, 0.6), "shell_dk")                              # حافة الظهر
    for k in range(3):                                                                              # رونات اللعنة على ظهر الرقبة
        R.box("thorax", (-0.45, 20.0 + k * 3.6, 0.0), (0.9, 1.4, 0.3), "curse")
    # ── الراس المثلث: عريض فوق بعيون مركبة كبيرة على الزوايا، يضيق للفم ──
    R.bone("head", "thorax", (0, 33.2, -2.6), rotation=[-30, 0, 0])
    R.box("head", (-4.0, 35.4, -5.2), (8.0, 3.0, 4.6), "shell", top="shell_dk")
    R.box("head", (-3.0, 33.0, -5.5), (6.0, 2.6, 4.2), "shell")
    R.box("head", (-2.0, 31.2, -5.7), (4.0, 2.0, 3.6), "belly")
    R.box("head", (-1.3, 30.0, -5.9), (2.6, 1.4, 3.0), "belly")
    for sx in (-1, 1):
        R.box("head", (sx * 5.4 - 1.6, 35.0, -5.6), (3.2, 3.8, 3.6), "eye")                     # عين مركبة
        R.box("head", (sx * 5.4 - 0.55 + sx * 0.3, 36.2, -5.9), (1.1, 1.2, 0.35), "pupil")       # الحدقة الكاذبة
        R.box("head", (sx * 0.9 - 0.6, 29.0, -6.0), (1.2, 1.6, 1.2), "mouth")                    # فكين
        R.box("head", (sx * 1.9 - 0.3, 29.4, -5.6), (0.6, 1.8, 0.6), "joint")                    # ملامس
    for x in (-1.0, 0.0, 1.0):
        R.box("head", (x - 0.3, 37.3 + (0.4 if x == 0 else 0), -5.45), (0.6, 0.6, 0.3), "curse")  # 3 عيون بسيطة
    for nm, sx in (("ant_l", 1), ("ant_r", -1)):
        R.bone(nm, "head", (sx * 1.1, 38.2, -4.4), rotation=[-20, 0, -sx * 18])
        R.box(nm, (sx * 1.1 - 0.2, 38.2, -4.6), (0.4, 6.0, 0.4), "joint")
        R.box(nm, (sx * 1.1 - 0.15, 44.0, -4.55), (0.3, 4.6, 0.3), "joint", rot=[-28, 0, 0], pivot=[sx * 1.1, 44.0, -4.4])
    # ── الذراعين المفترسة: حرقفة نازلة قدام الرقبة، فخذ ثخين مرفوع بأشواك ونصل، ساق مطوية بحافة نصل وخطاف ──
    for sx, a, f, c in ((1, "arm_l", "fore_l", "claw_l"), (-1, "arm_r", "fore_r", "claw_r")):
        x = sx * 2.7
        R.bone(a, "thorax", (x, 30.6, -4.8), rotation=[-46, 0, -sx * 6])
        R.box(a, (x - 1.2, 22.4, -7.3), (2.4, 8.8, 2.6), "shell", bottom="joint")                 # الحرقفة (طويلة)
        R.box(a, (x - 1.0, 30.0, -6.9), (2.0, 1.4, 2.2), "joint")
        R.bone(f, a, (x, 24.0, -6.2), rotation=[30, 0, 0])
        R.box(f, (x - 1.3, 23.0, -9.8), (2.6, 10.6, 2.8), "shell", bottom="joint")                # الفخذ (ثخين)
        R.box(f, (x - 0.9, 24.0, -10.1), (1.8, 8.6, 0.35), "blade")                              # حافة الفخذ الداخلية
        for k in range(4):                                                                         # أشواك الفخذ
            R.box(f, (x - 0.3 + (0.45 if k % 2 else -0.45), 24.6 + k * 2.1, -11.2), (0.6, 0.7, 1.15), "spine")
        R.box(f, (x - 1.0, 33.2, -9.4), (2.0, 1.2, 2.0), "joint")                                 # الركبة
        R.bone(c, f, (x, 33.6, -10.4))
        R.box(c, (x - 0.9, 25.8, -12.6), (1.8, 8.0, 1.7), "shell_dk")                             # الساق (المنجل)
        R.box(c, (x - 0.7, 26.2, -12.95), (1.4, 7.2, 0.35), "blade")                              # حافة النصل لقدام
        for k in range(3):                                                                         # أشواك الساق (لجهة الفخذ)
            R.box(c, (x - 0.25, 27.0 + k * 2.2, -11.0), (0.5, 0.6, 0.8), "spine")
        R.box(c, (x - 0.8, 24.4, -12.3), (1.6, 1.6, 1.4), "spine")                                # الخطاف
        R.box(c, (x - 0.6, 23.6, -11.6), (1.2, 1.2, 1.3), "spine", rot=[38, 0, 0], pivot=[x, 24.4, -11.6])
        R.box(c, (x - 0.35, 25.0, -13.1), (0.7, 1.6, 0.4), "curse")                               # لمعة لعنة على طرف المنجل
    return R


def camo_texture(R):
    """التمويه: نفس الـUV بس شبه شفاف (ألفا 96 ≈ 38%)، والعيون والعلامات الملعونة تبقى أوضح (ألفا 190)"""
    src = os.path.join(RP, "textures", "entity", "sh_prayer_mantis.png")
    img = Image.open(src).convert("RGBA")
    keep = {R._tile(m) for m in ("eye", "curse", "pupil")}
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            tile = ((x // TILE) * TILE, (y // TILE) * TILE)
            px[x, y] = (r, g, b, 190 if tile in keep else 96)
    img.save(os.path.join(RP, "textures", "entity", "sh_prayer_mantis_camo.png"))


def main():
    R = mantis()
    n = R.save(3.0, hot=MOLT, width=4)
    camo_texture(R)
    print("prayer mantis cubes:", n, "zfixed:", R.zfixed)


if __name__ == "__main__":
    main()
