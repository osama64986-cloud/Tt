# إضافة v1.1: وحشين من الرتبة الأولى + سلاحين. لا يغيّر الـ UUIDs الموجودة.
import json, math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE + "/AnimePowers"
BP = ROOT + "/BP"
RP = ROOT + "/RP"
random.seed(11)
np.random.seed(11)

src = open(HERE + "/build.py", encoding="utf-8").read()


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# نعيد استخدام أدوات الموديلات والأصوات من build.py بدون إعادة تشغيله
a = src.index("# ───────────────────────── نظام الموديلات")
b = src.index("# ───────── المدرّب")
exec(src[a:b])
a = src.index("SR = 44100")
b = src.index("# ختم الرقم")
exec(src[a:b])

# ───────────────────────── عفريت الرماد (رتبة 1، سريع وصغير) ─────────────────────────
CHAR = (44, 40, 48); CHAR2 = (66, 58, 62); EMB = (255, 120, 30); EMB2 = (255, 190, 70); HORN = (214, 200, 176)


def imp_face(px, regions):
    x0, y0, w, h = regions["front"]
    for yy in range(h):
        for xx in range(w):
            px_set(px, x0 + xx, y0 + yy, CHAR2)
    for ex in (1, w - 3):
        px_set(px, x0 + ex, y0 + 2, EMB2)
        px_set(px, x0 + ex + 1, y0 + 2, EMB2)
    for xx in range(1, w - 1, 2):
        px_set(px, x0 + xx, y0 + h - 2, HORN)


def cracks(px, regions):
    x0, y0, w, h = regions["front"]
    x = x0 + 1
    for yy in range(h):
        px_set(px, x, y0 + yy, EMB)
        x = max(x0, min(x0 + w - 1, x + random.choice((-1, 0, 1))))


sh_i = Sheet(64, 64)
imp_bones = [
    {"name": "body", "pivot": [0, 7, 0], "cubes": [
        {"origin": [-3, 7, -2], "size": [6, 7, 4], "colors": {"all": CHAR}, "detail": cracks}]},
    {"name": "head", "parent": "body", "pivot": [0, 14, 0], "cubes": [
        {"origin": [-3.5, 14, -3.5], "size": [7, 6, 7], "colors": {"all": CHAR2}, "detail": imp_face},
        {"origin": [-3.5, 20, -1], "size": [1.5, 3, 1.5], "colors": {"all": HORN}},
        {"origin": [2, 20, -1], "size": [1.5, 3, 1.5], "colors": {"all": HORN}}]},
    {"name": "arm_l", "parent": "body", "pivot": [3.5, 13, 0], "cubes": [
        {"origin": [3, 3, -1.5], "size": [3, 10, 3], "colors": {"all": CHAR}},
        {"origin": [2.5, 1, -2], "size": [4, 3, 4], "colors": {"all": EMB}}]},
    {"name": "arm_r", "parent": "body", "pivot": [-3.5, 13, 0], "cubes": [
        {"origin": [-6, 3, -1.5], "size": [3, 10, 3], "colors": {"all": CHAR}},
        {"origin": [-6.5, 1, -2], "size": [4, 3, 4], "colors": {"all": EMB}}]},
    {"name": "leg_l", "parent": "body", "pivot": [1.5, 7, 0], "cubes": [
        {"origin": [0, 0, -1.5], "size": [3, 7, 3], "colors": {"all": CHAR2}}]},
    {"name": "leg_r", "parent": "body", "pivot": [-1.5, 7, 0], "cubes": [
        {"origin": [-3, 0, -1.5], "size": [3, 7, 3], "colors": {"all": CHAR2}}]},
    {"name": "tail", "parent": "body", "pivot": [0, 9, 2], "cubes": [
        {"origin": [-1, 8, 2], "size": [2, 2, 6], "colors": {"all": CHAR}},
        {"origin": [-1.5, 7.5, 7.5], "size": [3, 3, 2], "colors": {"all": EMB}}]},
]
wjson(RP + "/models/entity/sh_imp.geo.json",
      build_model("geometry.sh_imp", imp_bones, sh_i, RP + "/textures/entity/sh_imp.png", vis=(2, 2, 0.8)))

# ───────────────────────── حارس الصدأ (رتبة 1، بطيء وثقيل) ─────────────────────────
RUST = (122, 70, 44); RUST2 = (92, 52, 34); PLATE = (150, 98, 62); CORE = (110, 240, 230); IRON = (70, 66, 72)


def guard_face(px, regions):
    x0, y0, w, h = regions["front"]
    for yy in range(h):
        for xx in range(w):
            px_set(px, x0 + xx, y0 + yy, IRON)
    for xx in range(1, w - 1):
        px_set(px, x0 + xx, y0 + 3, (14, 12, 16))
    px_set(px, x0 + w // 2 - 1, y0 + 3, CORE)
    px_set(px, x0 + w // 2, y0 + 3, CORE)


def core_chest(px, regions):
    x0, y0, w, h = regions["front"]
    cx, cy = x0 + w // 2, y0 + h // 2
    for dx in range(-2, 2):
        for dy in range(-2, 2):
            px_set(px, cx + dx, cy + dy, CORE)
    for xx in range(w):
        px_set(px, x0 + xx, y0, PLATE)


sh_g = Sheet(128, 64)
guard_bones = [
    {"name": "body", "pivot": [0, 14, 0], "cubes": [
        {"origin": [-6, 14, -3.5], "size": [12, 12, 7], "colors": {"all": RUST}, "detail": core_chest},
        {"origin": [-7, 24, -4], "size": [14, 3, 8], "colors": {"all": PLATE}}]},
    {"name": "head", "parent": "body", "pivot": [0, 27, 0], "cubes": [
        {"origin": [-4, 27, -4], "size": [8, 7, 8], "colors": {"all": IRON}, "detail": guard_face},
        {"origin": [-4.5, 33, -4.5], "size": [9, 2, 9], "colors": {"all": RUST2}}]},
    {"name": "arm_l", "parent": "body", "pivot": [8, 25, 0], "cubes": [
        {"origin": [6, 10, -2.5], "size": [5, 15, 5], "colors": {"all": RUST2}},
        {"origin": [5.5, 6, -3.5], "size": [6, 5, 7], "colors": {"all": PLATE}}]},
    {"name": "arm_r", "parent": "body", "pivot": [-8, 25, 0], "cubes": [
        {"origin": [-11, 10, -2.5], "size": [5, 15, 5], "colors": {"all": RUST2}},
        {"origin": [-11.5, 6, -3.5], "size": [6, 5, 7], "colors": {"all": PLATE}}]},
    {"name": "leg_l", "parent": "body", "pivot": [3, 14, 0], "cubes": [
        {"origin": [0.5, 0, -2.5], "size": [5, 14, 5], "colors": {"all": IRON}}]},
    {"name": "leg_r", "parent": "body", "pivot": [-3, 14, 0], "cubes": [
        {"origin": [-5.5, 0, -2.5], "size": [5, 14, 5], "colors": {"all": IRON}}]},
]
wjson(RP + "/models/entity/sh_guard.geo.json",
      build_model("geometry.sh_guard", guard_bones, sh_g, RP + "/textures/entity/sh_guard.png", vis=(2, 3, 1.2)))

# ───────────────────────── الأنيميشن ─────────────────────────
def walk(speed, leg, arm):
    return {
        "leg_l": {"rotation": [f"math.cos(query.modified_distance_moved * {speed}) * {leg} * query.modified_move_speed", 0, 0]},
        "leg_r": {"rotation": [f"math.cos(query.modified_distance_moved * {speed}) * -{leg} * query.modified_move_speed", 0, 0]},
        "arm_l": {"rotation": [f"math.cos(query.modified_distance_moved * {speed}) * -{arm} * query.modified_move_speed", 0, 0]},
        "arm_r": {"rotation": [f"math.cos(query.modified_distance_moved * {speed}) * {arm} * query.modified_move_speed", 0, 0]},
    }


wjson(RP + "/animations/sh2.animation.json", {
    "format_version": "1.8.0",
    "animations": {
        "animation.sh_imp.walk": {"loop": True, "bones": {**walk(45, 55, 45),
            "tail": {"rotation": [0, "math.sin(query.life_time * 400) * 25", 0]}}},
        "animation.sh_guard.walk": {"loop": True, "bones": walk(30, 28, 22)},
    },
})

for ident, geo, tex, anim, color, over, anims in [
    ("sh:ember_imp", "sh_imp", "sh_imp", "animation.sh_imp.walk", "#2c2830", "#ff781e", ["walk", "look"]),
    ("sh:rust_guard", "sh_guard", "sh_guard", "animation.sh_guard.walk", "#7a462c", "#6ef0e6", ["walk", "look"]),
]:
    short = ident.split(":")[1]
    wjson(RP + f"/entity/{short}.entity.json", {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": ident,
            "materials": {"default": "entity_alphatest"},
            "textures": {"default": f"textures/entity/{tex}"},
            "geometry": {"default": f"geometry.{geo}"},
            "animations": {"walk": anim, "look": "animation.sh.look"},
            "scripts": {"animate": anims},
            "render_controllers": ["controller.render.sh_default"],
            "spawn_egg": {"base_color": color, "overlay_color": over},
        }},
    })


def melee_entity(ident, hp, move, dmg, w, h, kb_res=0.0, speed_mult=1.2):
    comps = {
        "minecraft:type_family": {"family": ["sh_monster", "sh_rank0"]},
        "minecraft:health": {"value": hp, "max": hp},
        "minecraft:collision_box": {"width": w, "height": h},
        "minecraft:movement": {"value": move},
        "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "can_pass_doors": True},
        "minecraft:movement.basic": {},
        "minecraft:jump.static": {},
        "minecraft:physics": {},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
        "minecraft:attack": {"damage": dmg},
        "minecraft:despawn": {"despawn_from_distance": {"min_distance": 48, "max_distance": 64}},
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": speed_mult, "track_target": True},
        "minecraft:behavior.hurt_by_target": {"priority": 1},
        "minecraft:behavior.nearest_attackable_target": {"priority": 2, "must_see": False, "entity_types": [
            {"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 20}]},
        "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.8},
        "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8},
        "minecraft:behavior.random_look_around": {"priority": 8},
    }
    if kb_res:
        comps["minecraft:knockback_resistance"] = {"value": kb_res}
    wjson(BP + f"/entities/{ident.split(':')[1]}.json", {
        "format_version": "1.21.50",
        "minecraft:entity": {"description": {"identifier": ident, "is_spawnable": True, "is_summonable": True, "is_experimental": False},
                             "components": comps},
    })


melee_entity("sh:ember_imp", 18, 0.32, 3, 0.6, 1.3, 0.0, 1.3)
melee_entity("sh:rust_guard", 40, 0.2, 5, 0.9, 2.0, 0.5, 1.0)

# ───────────────────────── السلاحين ─────────────────────────
def weapon(ident, tex, name):
    wjson(BP + f"/items/{tex}.json", {
        "format_version": "1.21.60",
        "minecraft:item": {"description": {"identifier": ident, "menu_category": {"category": "equipment"}},
                           "components": {"minecraft:icon": {"textures": {"default": tex}},
                                          "minecraft:max_stack_size": 1,
                                          "minecraft:hand_equipped": True,
                                          "minecraft:display_name": {"value": name}}},
    })


weapon("sh:dawn_dagger", "sh_dagger", "§6خنجر الفجر")
weapon("sh:ember_cleaver", "sh_cleaver", "§cساطور الجمر")

try:
    FONT = ImageFont.load_default(size=14)
except TypeError:
    FONT = ImageFont.load_default()

# خنجر: نصل ذهبي رفيع مائل
im = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.polygon([(27, 3), (29, 5), (13, 21), (10, 18)], fill=(255, 224, 140, 255), outline=(255, 250, 220, 255))
d.polygon([(27, 3), (29, 5), (22, 12), (20, 10)], fill=(255, 250, 235, 255))
d.line([(8, 16), (16, 24)], fill=(120, 70, 30, 255), width=3)
d.line([(6, 26), (11, 21)], fill=(60, 36, 20, 255), width=4)
d.ellipse([3, 25, 8, 30], fill=(255, 190, 70, 255))
im.save(RP + "/textures/items/sh_dagger.png")

# ساطور: نصل عريض ثقيل بتوهج جمر
im = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.polygon([(14, 4), (29, 6), (27, 22), (12, 20)], fill=(70, 62, 72, 255), outline=(30, 26, 34, 255))
d.polygon([(26, 6), (29, 6), (27, 22), (24, 21)], fill=(255, 120, 30, 255))
for p in [(17, 9), (20, 13), (18, 17), (23, 10)]:
    d.line([p, (p[0] + 2, p[1] + 3)], fill=(255, 170, 60, 255), width=1)
d.line([(12, 20), (5, 28)], fill=(100, 60, 34, 255), width=3)
d.rectangle([3, 26, 8, 30], fill=(60, 36, 20, 255))
im.save(RP + "/textures/items/sh_cleaver.png")

tex = json.load(open(RP + "/textures/item_texture.json", encoding="utf-8"))
tex["texture_data"]["sh_dagger"] = {"textures": "textures/items/sh_dagger"}
tex["texture_data"]["sh_cleaver"] = {"textures": "textures/items/sh_cleaver"}
wjson(RP + "/textures/item_texture.json", tex)

# ───────────────────────── أصوات الأسلحة ─────────────────────────
save_ogg("dagger_hit", place(0.3, [(0, sweep(2400, 900, 0.12, 0.45)), (0, noise_burst(0.05, 0.5, 0.9, 60)), (0.02, bell(1760, 0.25, 0.4, 14))]))
save_ogg("cleaver_hit", place(0.6, [(0, sweep(220, 60, 0.3, 0.9)), (0, noise_burst(0.3, 0.7, 0.3, 14)), (0.03, bell(140, 0.5, 0.5, 8))]))
sd = json.load(open(RP + "/sounds/sound_definitions.json", encoding="utf-8"))
for key, ident in [("dagger_hit", "sh.dagger_hit"), ("cleaver_hit", "sh.cleaver_hit")]:
    sd["sound_definitions"][ident] = {"category": "player", "min_distance": 4, "max_distance": 32,
                                      "sounds": [{"name": f"sounds/sh/{key}", "volume": 1.0}]}
wjson(RP + "/sounds/sound_definitions.json", sd)

# ───────────────────────── Lang + manifests ─────────────────────────
add = ["entity.sh:ember_imp.name=عفريت الرماد", "entity.sh:rust_guard.name=حارس الصدأ",
       "item.spawn_egg.entity.sh:ember_imp.name=بيضة عفريت الرماد", "item.spawn_egg.entity.sh:rust_guard.name=بيضة حارس الصدأ", ""]
for lg in ("en_US", "ar_SA"):
    p = RP + f"/texts/{lg}.lang"
    s = open(p, encoding="utf-8").read().rstrip("\n")
    if "ember_imp" not in s:
        open(p, "w", encoding="utf-8").write(s + "\n" + "\n".join(add))

for m in (BP + "/manifest.json", RP + "/manifest.json"):
    j = json.load(open(m, encoding="utf-8"))
    j["header"]["version"] = [1, 1, 0]
    wjson(m, j)

print("extend ok")
