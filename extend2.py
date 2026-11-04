# v1.2: مهارات جديدة (أيقونات+أصوات+ايتمات)، لفائف خبرة، أسلحة مجسمة، حركات الوحوش
import json, math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE + "/AnimePowers"
BP = ROOT + "/BP"
RP = ROOT + "/RP"
random.seed(21)
np.random.seed(21)

src = open(HERE + "/build.py", encoding="utf-8").read()


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def rjson(path):
    return json.load(open(path, encoding="utf-8"))


a = src.index("# ───────────────────────── نظام الموديلات")
b = src.index("# ───────── المدرّب")
exec(src[a:b])
a = src.index("SR = 44100")
b = src.index("# ختم الرقم")
exec(src[a:b])

# ═════════════════════ المهارات: أيقونات + ايتمات ═════════════════════
SK = {  # id: (اسم، لون الاسم §، لون RGB)
    "transfer": ("نقل", "§6", (214, 168, 64)),
    "divide": ("قسمة", "§6", (255, 140, 50)),
    "zero": ("الصفر", "§c", (230, 50, 50)),
    "reflect": ("قانون الانعكاس", "§f", (220, 230, 255)),
    "boundary": ("قانون الحدود", "§5", (160, 80, 240)),
    "absolute": ("القانون المطلق", "§e", (255, 210, 90)),
    "pull": ("تقريب", "§b", (70, 170, 255)),
    "push": ("تبعيد", "§b", (130, 210, 255)),
    "swap": ("تبديل", "§3", (60, 220, 230)),
    "fold": ("طي", "§f", (235, 240, 255)),
    "spacecollapse": ("الانهيار", "§9", (90, 80, 235)),
    "echostrike": ("صدى الضربة", "§3", (60, 230, 215)),
    "echoseal": ("ختم الصدى", "§3", (60, 230, 215)),
    "sonar": ("صدى الكشف", "§3", (60, 230, 215)),
    "echowave": ("موجة الصدى", "§3", (60, 230, 215)),
    "chorus": ("الصدى المطلق", "§b", (120, 255, 235)),
}


def item(ident, name, tex, hidden=True, glint=False):
    comps = {"minecraft:icon": {"textures": {"default": tex}}, "minecraft:max_stack_size": 1 if hidden else 16,
             "minecraft:display_name": {"value": name}}
    if glint:
        comps["minecraft:glint"] = True
    wjson(BP + f"/items/{tex}.json", {
        "format_version": "1.21.60",
        "minecraft:item": {"description": {"identifier": ident, "menu_category": {"category": "none"} if hidden else {"category": "items"}},
                           "components": comps},
    })


def glow_circle(d, cx, cy, r, col):
    for i in range(r, 0, -1):
        al = int(255 * (1 - i / (r + 1)) ** 0.6)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col + (al,))


def lighter(c, k=0.55):
    return tuple(int(v + (255 - v) * k) for v in c) + (255,)


def draw_glyph(d, sid, c):
    L = lighter(c)
    C = c + (255,)
    cx = cy = 16
    if sid == "transfer":
        d.ellipse([4, 12, 11, 19], outline=L, width=2); d.ellipse([21, 12, 28, 19], outline=L, width=2)
        d.line([12, 16, 20, 16], fill=L, width=2); d.polygon([(20, 12), (24, 16), (20, 20)], fill=L)
    elif sid == "divide":
        d.ellipse([6, 6, 26, 26], outline=L, width=2); d.line([16, 6, 16, 26], fill=L, width=2)
        d.ellipse([9, 12, 13, 16], fill=L); d.ellipse([19, 17, 23, 21], fill=L)
    elif sid == "zero":
        d.ellipse([7, 5, 25, 27], outline=L, width=3); d.line([9, 25, 23, 7], fill=(255, 230, 230, 255), width=2)
    elif sid == "reflect":
        d.polygon([(16, 4), (27, 16), (16, 28), (5, 16)], outline=L)
        d.line([8, 24, 16, 16, 24, 24], fill=L, width=2); d.polygon([(21, 22), (25, 25), (21, 27)], fill=L)
    elif sid == "boundary":
        d.rectangle([5, 5, 26, 26], outline=L, width=2)
        for x, y in [(9, 9), (22, 9), (9, 22), (22, 22), (16, 16)]:
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=L)
    elif sid == "absolute":
        d.polygon([(5, 22), (8, 9), (13, 17), (16, 7), (19, 17), (24, 9), (27, 22)], fill=L)
        d.rectangle([5, 22, 27, 25], fill=C)
    elif sid == "pull":
        for ang in (0, 90, 180, 270):
            rad = math.radians(ang)
            x1, y1 = cx + math.cos(rad) * 12, cy + math.sin(rad) * 12
            x2, y2 = cx + math.cos(rad) * 5, cy + math.sin(rad) * 5
            d.line([x1, y1, x2, y2], fill=L, width=2)
            d.ellipse([x2 - 2, y2 - 2, x2 + 2, y2 + 2], fill=L)
        d.ellipse([13, 13, 19, 19], fill=(255, 255, 255, 255))
    elif sid == "push":
        for ang in (45, 135, 225, 315):
            rad = math.radians(ang)
            x1, y1 = cx + math.cos(rad) * 4, cy + math.sin(rad) * 4
            x2, y2 = cx + math.cos(rad) * 13, cy + math.sin(rad) * 13
            d.line([x1, y1, x2, y2], fill=L, width=2)
            d.ellipse([x2 - 2, y2 - 2, x2 + 2, y2 + 2], fill=L)
        d.ellipse([12, 12, 20, 20], outline=L, width=2)
    elif sid == "swap":
        d.ellipse([4, 21, 10, 27], fill=L); d.ellipse([22, 5, 28, 11], fill=L)
        d.arc([4, 5, 28, 27], 200, 330, fill=L, width=2); d.arc([4, 5, 28, 27], 20, 150, fill=L, width=2)
        d.polygon([(26, 14), (29, 18), (23, 18)], fill=L); d.polygon([(6, 18), (3, 14), (9, 14)], fill=L)
    elif sid == "fold":
        pts = [(4, 22), (10, 10), (16, 22), (22, 10), (28, 22)]
        d.line(pts, fill=L, width=3)
        d.line([(4, 26), (28, 26)], fill=C, width=1)
    elif sid == "spacecollapse":
        for r in (13, 9, 5):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=L, width=1)
        d.ellipse([13, 13, 19, 19], fill=(255, 255, 255, 255))
    elif sid == "echostrike":
        d.ellipse([10, 10, 22, 22], fill=L)
        d.arc([5, 5, 27, 27], 300, 60, fill=L, width=2); d.arc([1, 1, 31, 31], 320, 40, fill=C, width=2)
    elif sid == "echoseal":
        d.ellipse([6, 6, 26, 26], outline=L, width=2)
        d.line([(9, 16), (12, 11), (15, 21), (18, 11), (21, 21), (23, 16)], fill=L, width=2)
    elif sid == "sonar":
        d.ellipse([14, 14, 18, 18], fill=L)
        for r in (7, 11, 15):
            d.arc([cx - r, cy - r, cx + r, cy + r], 0, 360, fill=L if r < 15 else C, width=1)
    elif sid == "echowave":
        for i, r in enumerate((6, 10, 14)):
            d.arc([cx - 8 - r // 2, cy - r, cx - 8 + r + 4, cy + r], 300, 60, fill=L if i < 2 else C, width=2)
    elif sid == "chorus":
        for r in (13, 9, 5):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=L, width=2)
        d.polygon([(16, 9), (19, 16), (16, 23), (13, 16)], fill=(255, 255, 255, 255))


os.makedirs(RP + "/textures/items", exist_ok=True)
tex = rjson(RP + "/textures/item_texture.json")
for sid, (name, col, rgb) in SK.items():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    glow_circle(d, 16, 16, 15, rgb)
    d.ellipse([2, 2, 29, 29], outline=lighter(rgb, 0.35), width=1)
    draw_glyph(d, sid, rgb)
    im.save(RP + f"/textures/items/sh_{sid}.png")
    item(f"sh:skill_{sid}", f"{col}{name}", f"sh_{sid}", hidden=True)
    tex["texture_data"][f"sh_{sid}"] = {"textures": f"textures/items/sh_{sid}"}

# لفائف الخبرة
for key, name, base, seal, glint in [("small", "§aلفافة خبرة صغيرة", (222, 206, 160), (70, 190, 90), False),
                                     ("big", "§6لفافة خبرة كبيرة", (236, 214, 150), (230, 170, 40), True)]:
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([5, 9, 27, 23], 3, fill=base + (255,), outline=(120, 90, 50, 255))
    d.ellipse([2, 7, 9, 25], fill=(200, 170, 110, 255), outline=(120, 90, 50, 255))
    d.ellipse([23, 7, 30, 25], fill=(200, 170, 110, 255), outline=(120, 90, 50, 255))
    d.ellipse([12, 11, 21, 21], fill=seal + (255,), outline=(255, 255, 255, 200))
    d.line([13, 16, 20, 16], fill=(255, 255, 255, 255), width=1); d.line([16, 13, 16, 19], fill=(255, 255, 255, 255), width=1)
    im.save(RP + f"/textures/items/sh_scroll_{key}.png")
    item(f"sh:xp_scroll_{key}", name, f"sh_scroll_{key}", hidden=False, glint=glint)
    tex["texture_data"][f"sh_scroll_{key}"] = {"textures": f"textures/items/sh_scroll_{key}"}
wjson(RP + "/textures/item_texture.json", tex)

# ═════════════════════ الأصوات ═════════════════════
def delay_tail(sig, taps):
    out = np.zeros(len(sig) + int(SR * max(t for t, _ in taps)) + 1)
    out[: len(sig)] += sig
    for t, g in taps:
        i = int(t * SR)
        out[i:i + len(sig)] += sig * g
    return out


def vib(f, dur, depth, rate, amp=0.4, decay=3.0):
    t = t_arr(dur)
    ph = 2 * np.pi * f * t + depth * np.sin(2 * np.pi * rate * t)
    return amp * np.sin(ph) * np.exp(-decay * t) * env(len(t), 0.005, 0.1)


S = {}
S["transfer"] = place(0.55, [(0, sweep(500, 1800, 0.25, 0.4)), (0.18, bell(1400, 0.35, 0.45, 7)), (0.28, bell(1050, 0.3, 0.35, 7))])
S["divide"] = place(0.6, [(0, bell(900, 0.3, 0.5, 9)), (0.1, bell(1350, 0.35, 0.42, 8)), (0.1, bell(675, 0.35, 0.42, 8)), (0.0, noise_burst(0.04, 0.5, 0.8, 70))])
S["zero"] = place(1.3, [(0, sweep(500, 30, 0.9, 0.9)), (0, noise_burst(1.0, 0.7, 0.2, 4)), (0.5, bell(55, 0.8, 0.6, 3)), (0.02, bell(90, 0.9, 0.4, 3))])
S["reflect"] = place(0.7, [(0, bell(1900, 0.35, 0.5, 9)), (0.02, noise_burst(0.05, 0.6, 0.9, 60)), (0.15, bell(1250, 0.4, 0.35, 8)), (0.3, sweep(900, 2000, 0.25, 0.25))])
S["boundary"] = place(1.2, [(0, vib(110, 1.1, 3, 8, 0.7, 1.5)), (0.0, sweep(70, 160, 0.8, 0.45, "square")), (0.5, bell(220, 0.6, 0.35, 3)), (0.02, noise_burst(0.5, 0.35, 0.05, 5))])
t = t_arr(1.5)
choir = sum(0.25 * np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * 5 * t)) for f in (261.6, 329.6, 392, 523.3)) * np.sin(np.pi * t / 1.5) ** 1.2
S["absolute"] = place(1.6, [(0, choir), (0, sweep(200, 900, 1.0, 0.3)), (0.9, bell(1568, 0.6, 0.35, 3))])
S["pull"] = place(0.5, [(0, sweep(200, 1600, 0.3, 0.55)), (0.0, noise_burst(0.3, 0.4, 0.5, 6)), (0.28, bell(700, 0.2, 0.35, 12))])
S["push"] = place(0.6, [(0, sweep(1400, 160, 0.4, 0.6)), (0, noise_burst(0.35, 0.5, 0.4, 7)), (0.05, bell(80, 0.45, 0.5, 8))])
S["swap"] = place(0.5, [(0, bell(1700, 0.15, 0.5, 25)), (0.08, bell(1100, 0.15, 0.5, 25)), (0.16, bell(1700, 0.2, 0.4, 20)), (0.0, sweep(300, 2000, 0.18, 0.2))])
S["fold"] = place(0.7, [(0, vib(1200, 0.35, 8, 40, 0.4, 5)), (0.05, sweep(2200, 300, 0.3, 0.4)), (0.28, noise_burst(0.1, 0.7, 0.8, 30)), (0.3, bell(180, 0.3, 0.5, 12))])
S["spacecollapse"] = place(1.6, [(0, noise_burst(0.9, 0.5, 0.04, 0) * np.linspace(0.1, 1, int(SR * 0.9))), (0, sweep(60, 900, 0.9, 0.5)), (0.9, bell(45, 0.7, 0.9, 3)), (0.9, noise_burst(0.5, 0.8, 0.3, 6))])
S["echostrike"] = delay_tail(bell(1100, 0.25, 0.5, 9), [(0.15, 0.55), (0.3, 0.3), (0.45, 0.15)])
S["echoseal"] = delay_tail(bell(1500, 0.2, 0.45, 12), [(0.12, 0.6), (0.24, 0.45), (0.36, 0.3), (0.48, 0.18)])
S["sonar"] = place(1.3, [(0, bell(1200, 0.7, 0.55, 3.5)), (0.5, bell(1200, 0.5, 0.25, 4)), (0.9, bell(1200, 0.4, 0.12, 5)), (0, sweep(400, 1200, 0.2, 0.2))])
S["echowave"] = delay_tail(place(0.5, [(0, sweep(500, 120, 0.3, 0.6)), (0, noise_burst(0.3, 0.45, 0.3, 8))]), [(0.25, 0.5), (0.5, 0.25)])
S["chorus"] = delay_tail(place(0.9, [(0, bell(523, 0.8, 0.4, 2.5)), (0, bell(784, 0.8, 0.35, 2.5)), (0, bell(1047, 0.8, 0.3, 2.5)), (0, sweep(150, 600, 0.4, 0.35))]), [(0.2, 0.5), (0.4, 0.3)])
sd = rjson(RP + "/sounds/sound_definitions.json")
for sid, sig in S.items():
    save_ogg(sid, sig)
    sd["sound_definitions"][f"sh.{sid}"] = {"category": "player", "min_distance": 6, "max_distance": 40,
                                            "sounds": [{"name": f"sounds/sh/{sid}", "volume": 1.0}]}
wjson(RP + "/sounds/sound_definitions.json", sd)

# ═════════════════════ أسلحة مجسمة (attachables) ═════════════════════
STEEL = (210, 214, 224); STEEL2 = (160, 166, 180); GOLD = (214, 168, 64); WOOD = (96, 58, 34); WOOD2 = (62, 38, 24)
EMBER = (255, 120, 30); IRONC = (74, 66, 78); IRON2 = (54, 48, 58)

# إطار الموديل: الجريب عند (0, 9..15, -6) والنصل يمتد على +Y، مع دوران 125 درجة (مثل مثال الويكي)
PIV = [0, 19, -6]
ROT = [125, 0, 0]


def weapon_geo(ident, cubes_spec, tex_path):
    sh = Sheet(64, 64)
    cubes = []
    for (ox, oy, oz), (w, h, d), col in cubes_spec:
        pos = sh.alloc(w, d, h)
        sh.paint_cube(pos, w, d, h, {"all": col})
        cubes.append({"origin": [ox, oy, oz], "size": [w, h, d], "uv": list(pos)})
    sh.img.save(tex_path)
    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {"identifier": ident, "texture_width": 64, "texture_height": 64,
                            "visible_bounds_width": 3, "visible_bounds_height": 4, "visible_bounds_offset": [0, 1, 0]},
            "bones": [{"name": "root", "pivot": PIV, "rotation": ROT,
                       "binding": "q.item_slot_to_bone_name(context.item_slot)", "cubes": cubes}],
        }],
    }


os.makedirs(RP + "/textures/attachables", exist_ok=True)
dagger = [
    ((-0.5, 8.0, -6.7), (1.0, 1.0, 1.4), GOLD),      # نهاية المقبض
    ((-0.5, 9.0, -6.7), (1.0, 5.0, 1.4), WOOD),      # المقبض
    ((-0.7, 14.0, -8.5), (1.4, 1.0, 5.0), GOLD),     # الحارس
    ((-0.3, 15.0, -6.9), (0.6, 10.0, 1.8), STEEL),   # النصل
    ((-0.3, 25.0, -6.6), (0.6, 2.0, 1.2), STEEL2),   # الرأس
    ((-0.2, 15.0, -6.1), (0.4, 9.0, 0.5), (255, 224, 140)),  # حافة ذهبية
]
cleaver = [
    ((-0.6, 7.5, -6.8), (1.2, 1.5, 1.6), IRON2),
    ((-0.6, 9.0, -6.8), (1.2, 6.0, 1.6), WOOD2),
    ((-0.8, 15.0, -8.8), (1.6, 1.0, 5.6), IRONC),
    ((-0.6, 16.0, -9.2), (1.2, 11.0, 6.4), IRONC),
    ((-0.5, 27.0, -8.7), (1.0, 1.0, 5.4), IRON2),
    ((-0.7, 16.0, -3.3), (1.4, 11.0, 0.8), EMBER),   # حافة الجمر
    ((-0.7, 18.0, -8.2), (1.4, 5.0, 0.7), (255, 170, 60)),
]
wjson(RP + "/models/entity/sh_dagger.geo.json", weapon_geo("geometry.sh_dagger", dagger, RP + "/textures/attachables/sh_dagger.png"))
wjson(RP + "/models/entity/sh_cleaver.geo.json", weapon_geo("geometry.sh_cleaver", cleaver, RP + "/textures/attachables/sh_cleaver.png"))

# قيم الإطار من مثال الويكي (ثالث شخص). الأول شخص: قيم تقريبية قابلة للمعايرة.
wjson(RP + "/animations/sh_weapon.animation.json", {
    "format_version": "1.8.0",
    "animations": {
        "animation.sh_weapon.hold_third_person": {"loop": True, "bones": {"root": {"rotation": [-17.5, 0, 0], "position": [-5, -8, 0], "scale": 0.65}}},
        "animation.sh_weapon.hold_first_person": {"loop": True, "bones": {"root": {"rotation": [-20, 20, 0], "position": [3, -7, -2], "scale": 0.7}}},
    },
})
for key, ident in [("sh_dagger", "sh:dawn_dagger"), ("sh_cleaver", "sh:ember_cleaver")]:
    wjson(RP + f"/attachables/{key}.attachable.json", {
        "format_version": "1.10.0",
        "minecraft:attachable": {"description": {
            "identifier": ident,
            "materials": {"default": "entity_alphatest", "enchanted": "entity_alphatest_glint"},
            "textures": {"default": f"textures/attachables/{key}", "enchanted": "textures/misc/enchanted_item_glint"},
            "geometry": {"default": f"geometry.{key}"},
            "animations": {"hold_first_person": "animation.sh_weapon.hold_first_person", "hold_third_person": "animation.sh_weapon.hold_third_person"},
            "scripts": {"animate": [{"hold_first_person": "context.is_first_person == 1.0"}, {"hold_third_person": "context.is_first_person == 0.0"}]},
            "render_controllers": ["controller.render.item_default"],
        }},
    })

# ═════════════════════ حركات مهارات الوحوش ═════════════════════
wjson(RP + "/animations/sh_skills.animation.json", {
    "format_version": "1.8.0",
    "animations": {
        # عفريت: يتهيأ للوثبة (ينكمش ويرجّع ايديه) ثم يوثب
        "animation.sh_imp.windup": {"loop": True, "bones": {
            "body": {"rotation": [28, 0, 0], "position": [0, -2, 0]},
            "arm_l": {"rotation": [70, 0, -20]}, "arm_r": {"rotation": [70, 0, 20]},
            "head": {"rotation": [-15, 0, 0]},
            "tail": {"rotation": [0, "math.sin(query.life_time * 900) * 40", 0]}}},
        "animation.sh_imp.pounce": {"loop": True, "bones": {
            "body": {"rotation": [-30, 0, 0]},
            "arm_l": {"rotation": [-120, 0, 10]}, "arm_r": {"rotation": [-120, 0, -10]},
            "leg_l": {"rotation": [35, 0, 0]}, "leg_r": {"rotation": [-25, 0, 0]}}},
        # حارس: يرفع ايديه فوق راسه ثم يضرب
        "animation.sh_guard.windup": {"loop": True, "bones": {
            "arm_l": {"rotation": [-165, 0, -8]}, "arm_r": {"rotation": [-165, 0, 8]},
            "body": {"rotation": [-8, 0, 0]}}},
        "animation.sh_guard.slam": {"loop": True, "bones": {
            "arm_l": {"rotation": [35, 0, 0]}, "arm_r": {"rotation": [35, 0, 0]},
            "body": {"rotation": [22, 0, 0], "position": [0, -2, 0]}}},
    },
})
for short, geo_anims in [("sh_imp", ("windup", "pounce")), ("sh_guard", ("windup", "slam"))]:
    w, a2 = geo_anims
    wjson(RP + f"/animation_controllers/{short}.ac.json", {
        "format_version": "1.10.0",
        "animation_controllers": {f"controller.animation.{short}.state": {
            "initial_state": "default",
            "states": {
                "default": {"transitions": [{"windup": "query.property('sh:state') == 1"}, {"attack": "query.property('sh:state') == 2"}]},
                "windup": {"animations": ["windup"], "transitions": [{"default": "query.property('sh:state') == 0"}, {"attack": "query.property('sh:state') == 2"}]},
                "attack": {"animations": ["attack"], "transitions": [{"default": "query.property('sh:state') == 0"}, {"windup": "query.property('sh:state') == 1"}]},
            }}},
    })

for ent, short, anim_w, anim_a in [("sh_imp", "sh_imp", "animation.sh_imp.windup", "animation.sh_imp.pounce"),
                                    ("rust_guard", "sh_guard", "animation.sh_guard.windup", "animation.sh_guard.slam")]:
    fname = "ember_imp" if ent == "sh_imp" else "rust_guard"
    path = RP + f"/entity/{fname}.entity.json"
    j = rjson(path)
    d = j["minecraft:client_entity"]["description"]
    d["animations"]["windup"] = anim_w
    d["animations"]["attack"] = anim_a
    d["animations"]["state"] = f"controller.animation.{short}.state"
    d["scripts"]["animate"] = ["walk", "state", "look"]
    wjson(path, j)

    bpath = BP + f"/entities/{fname}.json"
    j = rjson(bpath)
    j["minecraft:entity"]["description"]["properties"] = {
        "sh:state": {"type": "int", "range": [0, 3], "default": 0, "client_sync": True}}
    wjson(bpath, j)

# أصوات المهارات + جزيئات تجهيز
for sid, f in [("imp_windup", None), ("imp_pounce", None), ("guard_windup", None), ("guard_slam", None)]:
    pass
M = {}
M["imp_windup"] = place(0.5, [(0, vib(260, 0.45, 5, 18, 0.45, 2)), (0.05, noise_burst(0.3, 0.25, 0.5, 6))])
M["imp_pounce"] = place(0.5, [(0, sweep(300, 1300, 0.22, 0.5, "square")), (0, noise_burst(0.3, 0.45, 0.5, 8)), (0.2, bell(220, 0.25, 0.3, 14))])
M["guard_windup"] = place(0.9, [(0, sweep(80, 160, 0.8, 0.55)), (0, vib(70, 0.8, 4, 6, 0.5, 1.5))])
M["guard_slam"] = place(1.0, [(0, sweep(180, 35, 0.5, 0.95)), (0, noise_burst(0.7, 0.8, 0.12, 5)), (0.03, bell(55, 0.9, 0.7, 4))])
for sid, sig in M.items():
    save_ogg(sid, sig)
    sd["sound_definitions"][f"sh.{sid}"] = {"category": "hostile", "min_distance": 6, "max_distance": 40,
                                            "sounds": [{"name": f"sounds/sh/{sid}", "volume": 1.0}]}
wjson(RP + "/sounds/sound_definitions.json", sd)

# ═════════════════════ Lang + manifests ═════════════════════
for m in (BP + "/manifest.json", RP + "/manifest.json"):
    j = rjson(m)
    j["header"]["version"] = [1, 2, 0]
    wjson(m, j)
print("extend2 ok")
