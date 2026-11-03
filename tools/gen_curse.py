"""لعنة القرويين (v1.39، MOD_GUIDE §56 بند 10): نادراً كلش قروي ينلعن، تطلع بجسمه بقع سودة تكبر على 3 مراحل،
ولما تكثر يتحول لوحش برتبة.

الشكل: كيان sh:cursed_villager يرسم نفسه بالضبط مثل قروي ماينكرافت (نفس الموديل geometry.villager_v2 ونفس تكستشرات
البيئة والمهنة ونفس مواد الرسم villager_v2 / villager_v2_masked، كلها من اللعبة بالاسم بدون نسخ)، والمهنة والبيئة
تنقل من القروي الأصلي بخصائص الكيان (sh:prof، sh:biome). وفوقها طبقة رابعة: تكستشر البقع السود (شفاف إلا البقع) بنفس
طريقة طبقة شارة المستوى بالقروي الأصلي. البقع مرسومة على خريطة UV الحقيقية للقروي (الراس، الوجه، الأنف، الروب،
الإيدين المتشابكة، أسفل الرجلين)، وكل مرحلة نفس البقع بس أكبر + بقع جديدة + عروق، وبالمرحلة الثالثة العيون تصير بنفسجي.
يكتب: textures/entity/sh_curse_1..3.png، الكيان BP و RP، متحكمات الرسم، أنميشن الارتجاف، النصوص.
التشغيل: python3 tools/gen_curse.py [مجلد_معاينة]"""
import json
import math
import os
import random
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")

# وجوه موديل القروي الظاهرة (u, v, عرض, ارتفاع) من geometry.villager_v2 (bedrock-samples): box UV القياسي
FACES = {
    "head_top": (8, 0, 8, 8), "head_e": (0, 8, 8, 10), "face": (8, 8, 8, 10), "head_w": (16, 8, 8, 10), "head_back": (24, 8, 8, 10),
    "nose": (26, 2, 2, 4), "nose_e": (24, 2, 2, 4), "nose_w": (28, 2, 2, 4),
    "robe_top": (6, 38, 8, 6), "robe_e": (0, 44, 6, 18), "robe_front": (6, 44, 8, 18), "robe_w": (14, 44, 6, 18), "robe_back": (20, 44, 8, 18),
    "arms_top": (44, 38, 8, 4), "arms_front": (44, 42, 8, 4), "arms_e": (40, 42, 4, 4), "arms_w": (52, 42, 4, 4),
    "arm_top": (48, 22, 4, 4), "arm_e": (44, 26, 4, 8), "arm_front": (48, 26, 4, 8), "arm_w": (52, 26, 4, 8), "arm_back": (56, 26, 4, 8),
    "leg_e": (0, 32, 4, 6), "leg_front": (4, 32, 4, 6), "leg_w": (8, 32, 4, 6), "leg_back": (12, 32, 4, 6),   # بس النص اللي يطلع تحت الروب
}
EYES = {"white": [(9, 14), (14, 14)], "iris": [(10, 14), (13, 14)], "brow": [(x, 13) for x in range(9, 15)]}
CORE, EDGE, VEIN, GLOW = (16, 10, 22), (38, 18, 52), (28, 15, 38), (176, 84, 255)


def spots(seed=1777):
    """البقع: كل بقعة (وجه، مركز، نصف قطر أساسي، مرحلة ظهورها). نفس البقع تكبر من مرحلة لمرحلة."""
    rnd = random.Random(seed)
    out = []
    weights = {"face": 2, "robe_front": 6, "robe_back": 5, "robe_e": 3, "robe_w": 3, "head_e": 2, "head_w": 2, "head_back": 3, "head_top": 2,
               "arms_front": 2, "arm_front": 1, "arm_e": 1, "arm_w": 1, "leg_front": 1, "leg_back": 1, "nose": 1, "robe_top": 1, "arms_top": 1}
    for name, n in weights.items():
        u, v, w, h = FACES[name]
        for i in range(n):
            born = 1 if i == 0 else rnd.choice((1, 2, 2, 3))
            out.append({"face": name, "cx": u + rnd.uniform(0.8, w - 0.8), "cy": v + rnd.uniform(0.8, h - 0.8),
                        "r": rnd.uniform(0.9, 1.6) if w > 3 else 0.8, "born": born, "seed": rnd.randint(0, 1 << 30)})
    return out


def in_face(x, y):
    for name, (u, v, w, h) in FACES.items():
        if u <= x < u + w and v <= y < v + h:
            return name
    return None


def curse_texture(stage, sp):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()
    grow = {1: 1.0, 2: 1.7, 3: 2.6}[stage]
    eyes_safe = set(EYES["white"] + EYES["iris"] + EYES["brow"])
    for s in sp:
        if s["born"] > stage:
            continue
        u, v, w, h = FACES[s["face"]]
        r = s["r"] * (grow if s["born"] == 1 else grow * (0.75 if s["born"] == 2 else 0.6))
        rnd = random.Random(s["seed"])
        jit = [rnd.uniform(-0.35, 0.35) for _ in range(16)]
        for y in range(v, v + h):
            for x in range(u, u + w):
                if stage < 3 and (x, y) in eyes_safe:
                    continue
                dx, dy = x + 0.5 - s["cx"], y + 0.5 - s["cy"]
                a = int(((math.atan2(dy, dx) + math.pi) / (2 * math.pi)) * 16) % 16
                d = math.hypot(dx, dy) - jit[a] * r                                   # حافة غير منتظمة (بقعة مو دائرة)
                if d < r - 0.85:
                    px[x, y] = (*CORE, 255)
                elif d < r and px[x, y][3] == 0:
                    px[x, y] = (*EDGE, 255)
        # عروق من المرحلة الثانية: خطوط رفيعة تمشي من البقعة (داخل نفس الوجه)
        if stage >= 2 and s["born"] <= 2:
            for k in range(1 if stage == 2 else 2):
                ang = rnd.uniform(0, 2 * math.pi)
                L = int(r * (2.2 if stage == 2 else 3.4))
                x, y = s["cx"], s["cy"]
                for _ in range(L):
                    ang += rnd.uniform(-0.6, 0.6)
                    x += math.cos(ang); y += math.sin(ang)
                    ix, iy = int(x), int(y)
                    if not (u <= ix < u + w and v <= iy < v + h):
                        break
                    if stage < 3 and (ix, iy) in eyes_safe:
                        continue
                    if px[ix, iy][3] == 0:
                        px[ix, iy] = (*VEIN, 255)
    if stage >= 3:                                                                   # العيون: بنفسجي يضوي، والأبيض يسود
        for (x, y) in EYES["iris"]:
            px[x, y] = (*GLOW, 255)
        for (x, y) in EYES["white"]:
            px[x, y] = (*CORE, 255)
        for k, (x, y) in enumerate(EYES["brow"]):
            px[x, y] = (*CORE, 255)
        rnd = random.Random(99)                                                      # نقاط لعنة صغيرة تضوي بين البقع
        cores = [(x, y) for y in range(64) for x in range(64) if px[x, y][:3] == CORE and in_face(x, y) not in (None, "face")]
        for (x, y) in rnd.sample(cores, min(10, len(cores))):
            px[x, y] = (110, 40, 170, 255)
    return img


BIOMES = ["plains", "desert", "jungle", "savanna", "snow", "swamp", "taiga"]
PROFS = ["unskilled", "farmer", "fisherman", "shepherd", "fletcher", "librarian", "cartographer", "cleric", "armorer", "weapon_smith",
         "tool_smith", "butcher", "leatherworker", "stonemason", "nitwit"]
PROF_FILE = {"tool_smith": "toolsmith", "weapon_smith": "weaponsmith"}


def write_entities():
    tex = {"base": "textures/entity/villager2/villager"}
    for b in BIOMES:
        tex[b] = f"textures/entity/villager2/biomes/biome_{b}"
    for p in PROFS:
        tex[p] = f"textures/entity/villager2/professions/{PROF_FILE.get(p, p)}"
    for s in (1, 2, 3):
        tex[f"curse{s}"] = f"textures/entity/sh_curse_{s}"
    rp = {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": "sh:cursed_villager",
        "materials": {"default": "villager_v2", "masked": "villager_v2_masked"},
        "textures": tex,
        "geometry": {"default": "geometry.villager_v2"},
        "animations": {"general": "animation.villager.general", "look_at_target": "animation.common.look_at_target", "move": "animation.villager.move",
                       "twitch": "animation.sh_cursed_villager.twitch", "convulse": "animation.sh_cursed_villager.convulse"},
        "scripts": {"scale": "0.9375", "animate": ["general", {"look_at_target": "query.property('sh:shake') == 0"}, {"move": "query.modified_move_speed"},
                                                   "twitch", {"convulse": "query.property('sh:shake') == 1"}]},
        "render_controllers": ["controller.render.sh_cursed_villager_base", "controller.render.sh_cursed_villager_masked", "controller.render.sh_cursed_villager_curse"],
        "spawn_egg": {"base_color": "#563c2c", "overlay_color": "#1a0f22"}}}}
    with open(os.path.join(RP, "entity", "sh_cursed_villager.entity.json"), "w", encoding="utf-8") as f:
        json.dump(rp, f, indent=2, ensure_ascii=False)
    rc = {"format_version": "1.8.0", "render_controllers": {
        "controller.render.sh_cursed_villager_base": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.base"]},
        "controller.render.sh_cursed_villager_masked": {
            "arrays": {"textures": {"Array.biomes": [f"Texture.{b}" for b in BIOMES], "Array.professions": [f"Texture.{p}" for p in PROFS]}},
            "geometry": "Geometry.default",
            "materials": [{"*": "query.property('sh:prof') == 0 ? Material.default : Material.masked"}],
            "textures": ["Array.biomes[query.property('sh:biome')]", "Array.professions[query.property('sh:prof')]"]},
        "controller.render.sh_cursed_villager_curse": {                              # مثل طبقة شارة المستوى بالقروي الأصلي
            "arrays": {"textures": {"Array.curse": ["Texture.curse1", "Texture.curse1", "Texture.curse2", "Texture.curse3"]}},
            "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
            "textures": ["Array.curse[query.property('sh:stage')]"]}}}
    with open(os.path.join(RP, "render_controllers", "sh_curse.render_controllers.json"), "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=2, ensure_ascii=False)
    LT = "query.life_time"
    S = "query.property('sh:stage')"
    anim = {"format_version": "1.8.0", "animations": {
        # ارتجاف يزيد ويا المرحلة: راس يرجف ويميل فجأة كل كم ثانية، وجسم يتمايل
        "animation.sh_cursed_villager.twitch": {"loop": True, "bones": {
            "head": {"rotation": [f"math.sin({LT}*1700)*0.7*{S} + (math.mod({LT}, 3.2 - {S}*0.6) < 0.12 ? 6 + {S}*5 : 0)", 0,
                                  f"math.sin({LT}*37)*2.2*{S}"]},
            "body": {"rotation": [0, 0, f"math.sin({LT}*53)*0.8*{S}"]}}},
        # التحول: يتشنج، الإيدين ترتفع، الراس لورا
        "animation.sh_cursed_villager.convulse": {"loop": True, "bones": {
            "head": {"rotation": [f"-28 + math.sin({LT}*2200)*6", f"math.sin({LT}*1300)*14", f"math.sin({LT}*1700)*10"]},
            "arms": {"rotation": [f"-60 + math.sin({LT}*1900)*14", 0, 0]},
            "body": {"rotation": [f"-6 + math.sin({LT}*2100)*3", 0, f"math.sin({LT}*1500)*4"], "position": [0, f"math.abs(math.sin({LT}*900))*0.6", 0]}}}}}
    with open(os.path.join(RP, "animations", "sh_curse.animation.json"), "w", encoding="utf-8") as f:
        json.dump(anim, f, indent=2, ensure_ascii=False)
    bp = {"format_version": "1.21.50", "minecraft:entity": {
        "description": {"identifier": "sh:cursed_villager", "is_spawnable": True, "is_summonable": True, "is_experimental": False,
                        "properties": {"sh:prof": {"type": "int", "range": [0, 14], "default": 0, "client_sync": True},
                                       "sh:biome": {"type": "int", "range": [0, 6], "default": 0, "client_sync": True},
                                       "sh:stage": {"type": "int", "range": [0, 3], "default": 1, "client_sync": True},
                                       "sh:shake": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}},
        "components": {
            "minecraft:type_family": {"family": ["sh_cursed_villager", "mob"]},
            "minecraft:health": {"value": 20, "max": 20},
            "minecraft:collision_box": {"width": 0.6, "height": 1.9},
            "minecraft:movement": {"value": 0.42},
            "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "can_pass_doors": True, "can_open_doors": True},
            "minecraft:movement.basic": {}, "minecraft:jump.static": {}, "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
            "minecraft:persistent": {},
            "minecraft:nameable": {},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.6},
            "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8},
            "minecraft:behavior.random_look_around": {"priority": 8},
            "minecraft:ambient_sound_interval": {"value": 8.0, "range": 12.0, "event_name": "ambient"}}}}
    with open(os.path.join(BP, "entities", "sh_cursed_villager.json"), "w", encoding="utf-8") as f:
        json.dump(bp, f, indent=1, ensure_ascii=False)
    lang = os.path.join(RP, "texts", "en_US.lang")
    txt = open(lang, encoding="utf-8").read()
    for line in ("entity.sh:cursed_villager.name=Cursed Villager", "item.spawn_egg.entity.sh:cursed_villager.name=Cursed Villager Egg"):
        if line not in txt:
            txt = txt.rstrip("\n") + "\n" + line + "\n"
    open(lang, "w", encoding="utf-8").write(txt)


def main():
    sp = spots()
    for s in (1, 2, 3):
        curse_texture(s, sp).save(os.path.join(RP, "textures", "entity", f"sh_curse_{s}.png"))
    write_entities()
    print("curse ok:", len(sp), "spots")


if __name__ == "__main__":
    main()
