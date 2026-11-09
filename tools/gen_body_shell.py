"""قشرة الجسم المتحولة (جسد الحديد وصفة الصخر): كيان sh:fx_body يتبع اللاعب ويغطيه بدرع حديد/حجر.
يولد: كيان BP + كيان RP + موديل humanoid متضخم + تكستشر 64x64 (حديد وحجر) + حركة + render controller.
التشغيل: python3 tools/gen_body_shell.py
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
INF = 0.55  # تضخيم يغطي طبقات السكن

# صناديق بنفس تخطيط سكن ماينكرافت 64x64: (اسم العظمة، origin، size، uv)
BOXES = {
    "head": [([-4, 24, -4], [8, 8, 8], [0, 0])],
    "body": [([-4, 12, -2], [8, 12, 4], [16, 16])],
    "arm_r": [([-8, 12, -2], [4, 12, 4], [40, 16])],
    "arm_l": [([4, 12, -2], [4, 12, 4], [32, 48])],
    "leg_r": [([-3.9, 0, -2], [4, 12, 4], [0, 16])],
    "leg_l": [([-0.1, 0, -2], [4, 12, 4], [16, 48])],
}
PIVOT = {"head": [0, 24, 0], "body": [0, 24, 0], "arm_r": [-5, 22, 0], "arm_l": [5, 22, 0], "leg_r": [-1.9, 12, 0], "leg_l": [1.9, 12, 0]}


def face_rects(u, v, w, h, d):
    return {
        "north": (u + d, v + d, w, h), "south": (u + 2 * d + w, v + d, w, h),
        "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h),
        "up": (u + d, v, w, d), "down": (u + d + w, v, w, d),
    }


def clamp(c):
    return tuple(max(0, min(255, int(v))) for v in c[:3])


def paint(img, name, boxes, style, rnd):
    px = img.load()
    for (_o, size, uv) in boxes:
        w, h, d = [int(round(v)) for v in size]
        for fname, (rx, ry, rw, rh) in face_rects(int(uv[0]), int(uv[1]), w, h, d).items():
            for y in range(rh):
                for x in range(rw):
                    px[rx + x, ry + y] = (*clamp(style(name, fname, x, y, rw, rh, rnd)), 255)


def iron_style(name, face, x, y, w, h, rnd):
    t = y / max(1, h - 1)
    base = (150 - 40 * t, 156 - 40 * t, 168 - 38 * t)
    v = rnd.uniform(-6, 6)
    c = [base[0] + v, base[1] + v, base[2] + v]
    # خطوط صفائح كل 4 بكسل + مسامير بالزوايا
    if (y % 6 == 0) or (x % 8 == 0 and face in ("north", "south")):
        c = [c[0] * 0.62, c[1] * 0.62, c[2] * 0.66]
    if (x % 8 == 1 and y % 6 == 1):
        c = [c[0] + 34, c[1] + 34, c[2] + 38]
    if face == "up":
        c = [c[0] + 16, c[1] + 16, c[2] + 18]
    if face == "down":
        c = [c[0] * 0.7, c[1] * 0.7, c[2] * 0.75]
    if name == "head" and face == "north":
        if 2 <= y <= 3 and 1 <= x <= w - 2:           # شق الخوذة (مظلم + عيون مضيئة)
            c = (24, 28, 40)
            if x in (2, 3, w - 4, w - 3):
                c = (170, 230, 255)
        if x == w // 2 - 1 or x == w // 2:
            c = [c[0] + 20, c[1] + 20, c[2] + 24]       # ضلع الخوذة
    if name == "body" and face == "north":
        if abs(x - w / 2 + 0.5) < 1 and y > 1:
            c = [c[0] + 24, c[1] + 24, c[2] + 28]       # ضلع الصدر
        if y == 5 and 1 < x < w - 2:
            c = (190, 120, 40)                          # حزام نحاسي
    if name.startswith("arm") and y >= h - 3:
        c = [c[0] * 0.8, c[1] * 0.8, c[2] * 0.85]       # قفاز
    return c


def stone_style(name, face, x, y, w, h, rnd):
    t = y / max(1, h - 1)
    g = 118 - 30 * t + rnd.uniform(-10, 10)
    c = [g, g + 2, g - 4]
    if rnd.random() < 0.07:
        c = [g * 0.7, g * 0.7, g * 0.7]                 # شقوق
    if rnd.random() < 0.06:
        c = [70 + rnd.uniform(0, 20), 120 + rnd.uniform(0, 25), 60]  # طحلب
    if (y % 6 == 0) or (x % 7 == 0 and face in ("north", "south")):
        c = [c[0] * 0.7, c[1] * 0.7, c[2] * 0.7]
    if name == "head" and face == "north" and 2 <= y <= 3 and x in (2, 3, w - 4, w - 3):
        c = (255, 170, 60)
    if name == "body" and face == "north" and 4 <= y <= 7 and w // 2 - 2 <= x <= w // 2 + 1:
        c = (110, 255, 190) if (x + y) % 2 else (60, 190, 140)   # قلب رون أخضر
    return c


def make_texture(style, seed):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for name, boxes in BOXES.items():
        paint(img, name, boxes, style, rnd)
    return img


def geometry():
    bones = [{"name": "root", "pivot": [0, 0, 0]}]
    for name, boxes in BOXES.items():
        cubes = [{"origin": o, "size": s, "uv": uv, "inflate": INF} for (o, s, uv) in boxes]
        if name == "head":
            cubes.append({"origin": [-0.7, 32.3, -4.9], "size": [1.4, 1.2, 9.8], "uv": [0, 0], "inflate": 0.2})   # عرف الخوذة
        if name == "body":
            cubes.append({"origin": [-5.2, 22.0, -2.8], "size": [10.4, 2.6, 5.6], "uv": [16, 16]})                # أطواق الكتف
        if name in ("arm_r", "arm_l"):
            sx = -8.9 if name == "arm_r" else 3.7
            cubes.append({"origin": [sx, 21.0, -3.1], "size": [5.2, 3.0, 6.2], "uv": [40, 16]})                    # كتفية
        if name in ("leg_r", "leg_l"):
            sx = -4.5 if name == "leg_r" else -0.5
            cubes.append({"origin": [sx, 5.0, -2.9], "size": [5.0, 2.4, 5.8], "uv": [0, 16]})                      # ركبة
        bones.append({"name": name, "parent": "root", "pivot": PIVOT[name], "cubes": cubes})
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.sh_fx_body", "texture_width": 64, "texture_height": 64,
                        "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
        "bones": bones}]}


def write(path, data, indent=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, separators=None if indent else (",", ":"))


def main():
    make_texture(iron_style, 7).save(os.path.join(RP, "textures", "entity", "sh_fx_body_0.png"))
    make_texture(stone_style, 9).save(os.path.join(RP, "textures", "entity", "sh_fx_body_1.png"))
    write(os.path.join(RP, "models", "entity", "sh_fx_body.geo.json"), geometry())
    write(os.path.join(BP, "entities", "sh_fx_body.json"), {
        "format_version": "1.21.50",
        "minecraft:entity": {
            "description": {
                "identifier": "sh:fx_body", "is_spawnable": False, "is_summonable": True, "is_experimental": False,
                "properties": {
                    "sh:v": {"type": "int", "range": [0, 3], "default": 0, "client_sync": True},
                    "sh:p": {"type": "int", "range": [-180, 180], "default": 0, "client_sync": True},
                    "sh:mv": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True},
                    "sh:r": {"type": "int", "range": [0, 4000], "default": 0, "client_sync": True},   # v1.43: بالمئة
                    # v1.43: 1 بس عند صاحب الدرع (setPropertyOverrideForEntity): راس الدرع يختفي من عنده لما الكاميرا جواه (منظور أول)
                    "sh:fp": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True},
                },
            },
            "component_groups": {"sh:gone": {"minecraft:instant_despawn": {}}},
            "components": {
                "minecraft:type_family": {"family": ["sh_fx", "inanimate"]},
                "minecraft:collision_box": {"width": 0.1, "height": 0.1},
                "minecraft:physics": {"has_gravity": False, "has_collision": False},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                "minecraft:timer": {"time": 40, "looping": False, "time_down_event": {"event": "sh:die"}},
                "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]},
            },
            "events": {"sh:die": {"add": {"component_groups": ["sh:gone"]}}},
        },
    }, indent=1)
    write(os.path.join(RP, "entity", "sh_fx_body.entity.json"), {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": "sh:fx_body",
            "materials": {"default": "entity_alphatest"},
            "textures": {"v0": "textures/entity/sh_fx_body_0", "v1": "textures/entity/sh_fx_body_1"},
            "geometry": {"default": "geometry.sh_fx_body"},
            "animations": {"fx": "animation.sh_fx.body"},
            "scripts": {"animate": ["fx"]},
            "render_controllers": ["controller.render.sh_fx_body"],
        }},
    }, indent=1)
    # render controller
    rc_path = os.path.join(RP, "render_controllers", "sh_fx.render_controllers.json")
    rc = json.load(open(rc_path, encoding="utf-8"))
    rc["render_controllers"]["controller.render.sh_fx_body"] = {
        "arrays": {"textures": {"Array.t": ["Texture.v0", "Texture.v1", "Texture.v0", "Texture.v1"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.t[query.property('sh:v')]"],
        # المنظور الأول: الكاميرا (عين اللاعب ~1.6 بلوكة فوق رجله) تصير جوه راس الدرع وتسد الشاشة، فنخفي الراس بس عند صاحبه
        # ولما الكاميرا قريبة. بالمنظور الثالث الكاميرا أبعد من 2.6 فيبين الدرع كامل، والباقين يشوفونه كامل دائماً.
        "part_visibility": [{"*": True}, {"head": "!(query.property('sh:fp') == 1 && query.distance_from_camera < 2.6)"}],
    }
    write(rc_path, rc, indent=1)
    # animation: الرأس يتبع الميل، الأطراف تتأرجح مع الحركة، والحجم يظهر بنبضة
    an_path = os.path.join(RP, "animations", "sh_fx.animation.json")
    an = json.load(open(an_path, encoding="utf-8"))
    sw = "math.cos(query.life_time * 560.0)"
    an["animations"]["animation.sh_fx.body"] = {
        "loop": True,
        "bones": {
            "root": {"scale": "(query.property('sh:r') * 0.01)"},
            "head": {"rotation": ["query.property('sh:p')", 0, 0]},
            "arm_r": {"rotation": [f"{sw} * 55.0 * query.property('sh:mv')", 0, 0]},
            "arm_l": {"rotation": [f"-{sw} * 55.0 * query.property('sh:mv')", 0, 0]},
            "leg_r": {"rotation": [f"-{sw} * 60.0 * query.property('sh:mv')", 0, 0]},
            "leg_l": {"rotation": [f"{sw} * 60.0 * query.property('sh:mv')", 0, 0]},
        },
    }
    write(an_path, an, indent=1)
    print("body shell ok")


if __name__ == "__main__":
    main()
