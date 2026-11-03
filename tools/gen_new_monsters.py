"""تعريفات وحوش: ثعلب الحجاب (Veilfox، Grim)، ماغماموث (Magmamoth، Vile)، الدب الرمادي (Grey Bear، Vile) وجروه (Bear Cub)،
السرعوف المصلّي والحاصد الأجوف (Cursed).
يكتب: كيان BP، كيان RP، متحكم الرسم (للماموث: تكستشر حار)، الأنميشن، متحكمات الأنميشن، النصوص.
(الموديل والتكستشر من gen_grim_monsters.py)   التشغيل: python3 tools/gen_new_monsters.py"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, d, indent=1):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=indent, ensure_ascii=False)


MON = {
    "veilfox": dict(ident="sh:veilfox", name="Veilfox", rank="sh_rank1", hp=95, speed=0.34, atk=6, w=1.1, h=1.8, kb=0.4, xp=12,
                    egg=("#2a2640", "#8c64ff"), states=4, props=None),
    "magmamoth": dict(ident="sh:magmamoth", name="Magmamoth", rank="sh_rank2", hp=260, speed=0.24, atk=12, w=3.4, h=4.0, kb=0.95, xp=40,
                      egg=("#2c2a30", "#ff7a1c"), states=6, props={"sh:hot": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}),
    "grey_bear": dict(ident="sh:grey_bear", name="Grey Bear", rank="sh_rank2", hp=300, speed=0.27, atk=11, w=1.6, h=3.2, kb=0.9, xp=40,
                      egg=("#5e5a58", "#d8d6d0"), states=6, props={"sh:hot": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}),
    "prayer_mantis": dict(ident="sh:prayer_mantis", name="Prayer Mantis", rank="sh_rank3", hp=340, speed=0.3, atk=13, w=1.5, h=2.9, kb=0.85, xp=60,
                          egg=("#4c8a32", "#c060ff"), states=6,
                          props={"sh:hot": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True},
                                 "sh:camo": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}),
    "hollow_harvester": dict(ident="sh:hollow_harvester", name="Hollow Harvester", rank="sh_rank3", hp=320, speed=0.27, atk=12, w=1.1, h=2.9, kb=0.8, xp=60,
                             egg=("#4a3c58", "#e2b85c"), states=5,
                             props={"sh:hot": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}),
    "bear_cub": dict(ident="sh:bear_cub", name="Bear Cub", rank="sh_cub", hp=12, speed=0.36, atk=1, w=0.6, h=1.2, kb=0.1, xp=2,
                     egg=("#7a7672", "#d8d6d0"), states=1, props=None),
}


def bp_entity(key, m):
    d = load(os.path.join(BP, "entities", "sh_gloomhorn.json"))
    e = d["minecraft:entity"]
    e["description"]["identifier"] = m["ident"]
    e["description"]["properties"]["sh:state"]["range"] = [0, m["states"]]
    if m["props"]:
        e["description"]["properties"].update(m["props"])
    c = e["components"]
    c["minecraft:type_family"]["family"] = ["sh_monster", m["rank"]]
    c["minecraft:health"] = {"value": m["hp"], "max": m["hp"]}
    c["minecraft:collision_box"] = {"width": m["w"], "height": m["h"]}
    c["minecraft:movement"] = {"value": m["speed"]}
    c["minecraft:attack"] = {"damage": m["atk"]}
    c["minecraft:knockback_resistance"] = {"value": m["kb"]}
    c["minecraft:experience_reward"] = {"on_death": f"query.last_hit_by_player ? {m['xp']} : 0"}
    if key == "magmamoth":
        c["minecraft:fire_immune"] = {}
        c["minecraft:behavior.melee_attack"]["speed_multiplier"] = 1.15
        c["minecraft:nameable"] = {}
    if key == "grey_bear":
        c["minecraft:behavior.melee_attack"]["speed_multiplier"] = 1.2
        c["minecraft:nameable"] = {}
    if key == "prayer_mantis":                              # السرعوف: سريع الانقضاض، ما يطيح من العالي
        c["minecraft:behavior.melee_attack"]["speed_multiplier"] = 1.3
        c["minecraft:nameable"] = {}
        c["minecraft:damage_sensor"] = {"triggers": [{"cause": "fall", "deals_damage": "yes", "damage_multiplier": 0.2}]}   # ضرر السقوط 20% (المكون الرسمي، مثل الماعز)
    if key == "hollow_harvester":                           # الحاصد: فزاعة قش، ضعفه النار (المكون الرسمي damage_sensor)
        c["minecraft:behavior.melee_attack"]["speed_multiplier"] = 1.2
        c["minecraft:nameable"] = {}
        c["minecraft:damage_sensor"] = {"triggers": [
            {"cause": "fall", "deals_damage": "yes", "damage_multiplier": 0.5},
            {"cause": "fire", "deals_damage": "yes", "damage_multiplier": 3.0},
            {"cause": "fire_tick", "deals_damage": "yes", "damage_multiplier": 3.0},
            {"cause": "lava", "deals_damage": "yes", "damage_multiplier": 2.0}]}
    if key == "bear_cub":                                   # الجرو: موديل خاص صغير (1.2 بلوكة)، ما يكون حارس ولا زعيم صدع
        c["minecraft:type_family"]["family"] = ["sh_monster", "sh_cub", "monster"]
        c["minecraft:behavior.melee_attack"]["speed_multiplier"] = 1.5
        c["minecraft:despawn"] = {"despawn_from_distance": {"min_distance": 32, "max_distance": 48}}
        e.pop("component_groups", None); e.pop("events", None)
    save(os.path.join(BP, "entities", f"sh_{key}.json"), d)


def rp_entity(key, m, anims):
    d = load(os.path.join(RP, "entity", "sh_gloomhorn.entity.json"))
    cd = d["minecraft:client_entity"]["description"]
    cd["identifier"] = m["ident"]
    cd["textures"] = {"default": f"textures/entity/sh_{key}"}
    cd["geometry"]["default"] = f"geometry.sh_{key}"
    cd["animations"] = {"idle": f"animation.sh_{key}.idle", "walk": f"animation.sh_{key}.walk", "state": f"controller.animation.sh_{key}.state", "look": "animation.sh.look"}
    for a in anims:
        cd["animations"][a] = f"animation.sh_{key}.{a}"
    animate = ["idle", "walk", "state", "look"]
    if key in ("magmamoth", "grey_bear"):
        cd["textures"]["hot"] = f"textures/entity/sh_{key}_hot"
        cd["render_controllers"] = ["controller.render.sh_mammoth"]
        cd["scale"] = None
        animate.append("attack")
    if key == "hollow_harvester":                           # تكستشرين: عادي، ومحروق لما يشتعل (sh:hot)
        cd["textures"]["hot"] = f"textures/entity/sh_{key}_hot"
        cd["render_controllers"] = ["controller.render.sh_mammoth"]
        animate.append("attack")
    if key == "prayer_mantis":                              # 3 تكستشرات: عادي، بعد الانسلاخ (hot)، تمويه شبه شفاف بمادة alphablend
        cd["textures"]["hot"] = f"textures/entity/sh_{key}_hot"
        cd["textures"]["camo"] = f"textures/entity/sh_{key}_camo"
        cd["materials"] = {"default": "entity_alphatest", "camo": "entity_alphablend"}
        cd["render_controllers"] = ["controller.render.sh_mantis"]
        animate.append("attack")
    if key == "bear_cub":
        cd["textures"] = {"default": "textures/entity/sh_bear_cub"}
        cd["geometry"]["default"] = "geometry.sh_bear_cub"
        cd["animations"] = {"idle": "animation.sh_grey_bear.idle", "walk": "animation.sh_grey_bear.walk", "attack": "animation.sh_grey_bear.attack", "look": "animation.sh.look"}
        animate = ["idle", "walk", "look", "attack"]
    cd["scripts"]["animate"] = animate
    cd.pop("scale", None)
    cd["spawn_egg"] = {"base_color": m["egg"][0], "overlay_color": m["egg"][1]}
    save(os.path.join(RP, "entity", f"sh_{key}.entity.json"), d, indent=2)


def controller(names, death=False):
    """names = [(اسم الحالة, رقم sh:state)]. death = حالة موت تلقائية لما is_alive = 0."""
    dth = [{"death": "!query.is_alive"}] if death else []
    states = {"default": {"transitions": dth + [{n: f"query.property('sh:state') == {i}"} for n, i in names], "blend_transition": 0.18}}
    for n, i in names:
        tr = dth + [{"default": "query.property('sh:state') == 0"}] + [{n2: f"query.property('sh:state') == {i2}"} for n2, i2 in names if n2 != n]
        states[n] = {"animations": [n], "transitions": tr, "blend_transition": 0.12}
    if death:
        states["death"] = {"animations": ["death"], "blend_transition": 0.1}
    return {"initial_state": "default", "states": states}


def walk(legs, amp=32, k=38, body=0.6, pairs=(1, -1, -1, 1)):
    t = f"query.modified_distance_moved*{k}"
    ms = "query.modified_move_speed"
    bones = {n: {"rotation": [f"{'-' if s < 0 else ''}math.cos({t})*{amp}*{ms}", 0, 0]} for n, s in zip(legs, pairs)}
    bones["body"] = {"position": [0, f"math.abs(math.sin({t}))*{body}*{ms}", 0]}
    return {"loop": True, "bones": bones}


LT = "query.life_time"
LEGS = ["leg_fl", "leg_fr", "leg_bl", "leg_br"]


def fox_anims(A):
    tails = {}
    for i, n in enumerate("abcde"):
        for k in range(6):
            tails[f"tail_{n}{k}"] = {"rotation": [f"math.sin({LT}*140 - {k * 50} + {i * 60})*{4 + k * 1.4}", f"math.sin({LT}*110 - {k * 55} + {i * 60})*{3 + k}", 0]}
    A["animation.sh_veilfox.idle"] = {"loop": True, "bones": {
        "body": {"position": [0, f"math.sin({LT}*90)*0.2", 0]},
        "head": {"rotation": [f"math.sin({LT}*60)*2", f"math.sin({LT}*35)*10", 0]},
        "mane": {"scale": [1, f"1 + math.sin({LT}*420)*0.14", 1]},
        "ear_l": {"rotation": [0, 0, f"-math.sin({LT}*140)*4 - (math.mod({LT},3.7)<0.2 ? math.sin(math.mod({LT},3.7)*1800)*14 : 0)"]},
        "ear_r": {"rotation": [0, 0, f"math.sin({LT}*140)*4 + (math.mod({LT}+1.3,4.4)<0.2 ? math.sin(math.mod({LT}+1.3,4.4)*1800)*14 : 0)"]},
        "orbs": {"rotation": [0, f"{LT}*70", 0], "position": [0, f"math.sin({LT}*120)*0.5", 0]}, **tails}}
    A["animation.sh_veilfox.walk"] = walk(LEGS, 38, 40, 0.7)
    A["animation.sh_veilfox.walk"]["bones"]["neck"] = {"rotation": ["math.sin(query.modified_distance_moved*80)*3*query.modified_move_speed", 0, 0]}
    A["animation.sh_veilfox.volley"] = {"loop": True, "bones": {                         # يرفع راسه وأذياله والكرات تدور بسرعة (1)
        "head": {"rotation": [-24, 0, 0]}, "neck": {"rotation": [-16, 0, 0]},
        "body": {"rotation": [-6, 0, 0], "position": [0, 0.3, 0]},
        "orbs": {"rotation": [0, f"{LT}*420", 0]},
        "tail_a": {"rotation": [18, -16, 0]}, "tail_b": {"rotation": [20, -8, 0]}, "tail_c": {"rotation": [24, 0, 0]},
        "tail_d": {"rotation": [20, 8, 0]}, "tail_e": {"rotation": [18, 16, 0]}}}
    A["animation.sh_veilfox.pounce"] = {"loop": True, "bones": {                         # ينحني وينطلق (2)
        "body": {"position": [0, -3.5, 0], "rotation": [10, 0, 0]},
        "head": {"rotation": [18, 0, 0]}, "neck": {"rotation": [16, 0, 0]},
        "leg_fl": {"rotation": [-40, 0, 0]}, "leg_fr": {"rotation": [-40, 0, 0]},
        "leg_bl": {"rotation": [48, 0, 0]}, "leg_br": {"rotation": [48, 0, 0]},
        "tail_a": {"rotation": [-30, -18, 0]}, "tail_b": {"rotation": [-36, -9, 0]}, "tail_c": {"rotation": [-40, 0, 0]},
        "tail_d": {"rotation": [-36, 9, 0]}, "tail_e": {"rotation": [-30, 18, 0]}}}
    A["animation.sh_veilfox.storm"] = {"loop": True, "bones": {                          # يوقف على رجليه الورا والأذيال تنفرش وتدور (3)
        "body": {"rotation": [-28, 0, 0], "position": [0, 2.2, 0]},
        "leg_fl": {"rotation": [-65, 0, 0]}, "leg_fr": {"rotation": [-65, 0, 0]},
        "leg_bl": {"rotation": [28, 0, 0]}, "leg_br": {"rotation": [28, 0, 0]},
        "head": {"rotation": [-24, 0, 0]}, "orbs": {"rotation": [0, f"{LT}*900", 0]},
        "tail_a": {"rotation": [-14, f"-60 + math.sin({LT}*500)*20", 0]}, "tail_b": {"rotation": [-10, f"-30 + math.sin({LT}*500 + 70)*22", 0]},
        "tail_c": {"rotation": [-6, f"math.sin({LT}*500 + 140)*24", 0]}, "tail_d": {"rotation": [-10, f"30 + math.sin({LT}*500 + 210)*22", 0]},
        "tail_e": {"rotation": [-14, f"60 + math.sin({LT}*500 + 280)*20", 0]}}}
    A["animation.sh_veilfox.veil"] = {"loop": True, "bones": {                           # العرش: يقف عالياً وكل أذياله تشع لفوق والكرات تلف (4)
        "body": {"rotation": [-20, 0, 0], "position": [0, 1.4, 0]},
        "leg_fl": {"rotation": [-34, 0, 0]}, "leg_fr": {"rotation": [-34, 0, 0]},
        "head": {"rotation": [-32, f"math.sin({LT}*180)*10", 0]}, "neck": {"rotation": [-10, 0, 0]},
        "orbs": {"rotation": [0, f"{LT}*1200", 0], "position": [0, 2, 0]},
        "mane": {"scale": [1, f"1.5 + math.sin({LT}*800)*0.2", 1]},
        "tail_a": {"rotation": [24, -30, 0]}, "tail_b": {"rotation": [30, -15, 0]}, "tail_c": {"rotation": [36, 0, 0]},
        "tail_d": {"rotation": [30, 15, 0]}, "tail_e": {"rotation": [24, 30, 0]}}}


def mammoth_anims(A):
    S = "animation.sh_magmamoth."
    A[S + "idle"] = {"loop": True, "bones": {
        "body": {"position": [0, f"math.sin({LT}*80)*0.45", 0], "rotation": [f"math.sin({LT}*60)*0.7", 0, 0]},
        "head": {"rotation": [f"math.sin({LT}*50)*2.5", f"math.sin({LT}*30)*7", 0]},
        "trunk0": {"rotation": [f"math.sin({LT}*70)*4", 0, 0]}, "trunk1": {"rotation": [f"math.sin({LT}*70 - 40)*5", 0, 0]},
        "trunk2": {"rotation": [f"math.sin({LT}*70 - 80)*5", 0, 0]}, "trunk3": {"rotation": [f"math.sin({LT}*70 - 120)*6", 0, 0]},
        "ear_l": {"rotation": [0, f"math.sin({LT}*130)*5", 0]}, "ear_r": {"rotation": [0, f"-math.sin({LT}*130 + 40)*5", 0]},
        "tail": {"rotation": [f"math.sin({LT}*90)*10", f"math.sin({LT}*55)*14", 0]}}}
    A[S + "walk"] = walk(LEGS, 24, 30, 1.0, pairs=(1, -1, -1, 1))
    w = A[S + "walk"]["bones"]
    w["body"]["rotation"] = [0, 0, "math.cos(query.modified_distance_moved*30)*1.6*query.modified_move_speed"]
    w["head"] = {"rotation": ["math.sin(query.modified_distance_moved*60)*3*query.modified_move_speed", 0, 0]}
    w["trunk0"] = {"rotation": ["math.sin(query.modified_distance_moved*30)*8*query.modified_move_speed", 0, 0]}
    w["ear_l"] = {"rotation": [0, "math.sin(query.modified_distance_moved*60)*8*query.modified_move_speed", 0]}
    w["ear_r"] = {"rotation": [0, "-math.sin(query.modified_distance_moved*60)*8*query.modified_move_speed", 0]}
    g = f"{LT}*1000"
    A[S + "run"] = {"loop": True, "bones": {                                              # جري عنيف: الراس منخفض والأنياب لقدام (3)
        "leg_fl": {"rotation": [f"math.cos({g})*42", 0, 0]}, "leg_fr": {"rotation": [f"math.cos({g} + 40)*42", 0, 0]},
        "leg_bl": {"rotation": [f"-math.cos({g} + 20)*38", 0, 0]}, "leg_br": {"rotation": [f"-math.cos({g} + 60)*38", 0, 0]},
        "body": {"position": [0, f"math.abs(math.sin({g}))*2.4", 0], "rotation": [f"6 + math.sin({g})*2", 0, 0]},
        "head": {"rotation": [30, 0, 0]}, "trunk0": {"rotation": [34, 0, 0]}, "trunk1": {"rotation": [24, 0, 0]},
        "ear_l": {"rotation": [0, 28, 0]}, "ear_r": {"rotation": [0, -28, 0]}, "tail": {"rotation": [-34, 0, 0]}}}
    A[S + "attack"] = {"loop": True, "bones": {                                           # الضربة العادية (variable.attack_time)
        "head": {"rotation": ["math.sin(variable.attack_time*180)*30", 0, 0]},
        "trunk0": {"rotation": ["-math.sin(variable.attack_time*180)*50", 0, 0]},
        "body": {"rotation": ["math.sin(variable.attack_time*180)*5", 0, 0]},
        "leg_fl": {"rotation": ["-math.sin(variable.attack_time*180)*24", 0, 0]}}}
    A[S + "stomp"] = {"loop": "hold_on_last_frame", "animation_length": 1.7, "bones": {      # يرفع رجله الأمامية ويدك الأرض (1)
        "leg_fr": {"rotation": {"0.0": [0, 0, 0], "0.5": [-72, 0, 0], "0.72": [-82, 0, 0], "0.82": [18, 0, 0], "1.1": [6, 0, 0], "1.7": [0, 0, 0]}},
        "leg_fl": {"rotation": {"0.0": [0, 0, 0], "0.8": [0, 0, 0], "0.84": [8, 0, 0], "1.7": [0, 0, 0]}},
        "body": {"rotation": {"0.0": [0, 0, 0], "0.5": [-9, 0, 0], "0.72": [-12, 0, 0], "0.82": [6, 0, 0], "1.1": [2, 0, 0], "1.7": [0, 0, 0]},
                 "position": {"0.0": [0, 0, 0], "0.72": [0, 3, 0], "0.82": [0, -3, 0], "1.1": [0, -1, 0], "1.7": [0, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.6": [-14, 0, 0], "0.82": [14, 0, 0], "1.7": [0, 0, 0]}},
        "trunk0": {"rotation": {"0.0": [0, 0, 0], "0.6": [-30, 0, 0], "0.82": [20, 0, 0], "1.7": [0, 0, 0]}}}}
    ramp = f"math.min(1, {LT}*3)"
    A[S + "breath"] = {"loop": True, "bones": {                                           # يرفع خرطومه وينفخ (2)
        "trunk0": {"rotation": [f"-62*{ramp}", 0, 0]}, "trunk1": {"rotation": [f"-30*{ramp}", 0, 0]}, "trunk2": {"rotation": [f"-22*{ramp}", 0, 0]},
        "trunk3": {"rotation": [f"-16*{ramp}", 0, 0]}, "trunk4": {"rotation": [f"-10*{ramp} + math.sin({LT}*1400)*3", 0, 0]},
        "head": {"rotation": [f"-16*{ramp}", 0, 0]}, "body": {"rotation": [f"-3*{ramp}", 0, 0], "position": [0, f"math.sin({LT}*1100)*0.3", 0]},
        "ear_l": {"rotation": [0, 18, 0]}, "ear_r": {"rotation": [0, -18, 0]}}}
    A[S + "lower"] = {"loop": True, "bones": {                                            # ينزل راسه ويحك الأرض قبل الاندفاع (6)
        "head": {"rotation": [38, 0, 0]}, "trunk0": {"rotation": [42, 0, 0]}, "trunk1": {"rotation": [20, 0, 0]},
        "body": {"rotation": [7, 0, 0], "position": [0, -1.5, 0]},
        "leg_fl": {"rotation": [f"math.sin({LT}*900)*34", 0, 0]}, "leg_fr": {"rotation": [f"-math.sin({LT}*900)*34", 0, 0]},
        "ear_l": {"rotation": [0, 24, 0]}, "ear_r": {"rotation": [0, -24, 0]}, "tail": {"rotation": [-26, 0, 0]}}}
    A[S + "eruption"] = {"loop": "hold_on_last_frame", "animation_length": 2.2, "bones": {      # يرفع الاثنين وينزل بكل وزنه (4)
        "leg_fl": {"rotation": {"0.0": [0, 0, 0], "0.6": [-78, 0, 0], "0.9": [-86, 0, 0], "1.0": [20, 0, 0], "1.4": [8, 0, 0], "2.2": [0, 0, 0]}},
        "leg_fr": {"rotation": {"0.0": [0, 0, 0], "0.6": [-78, 0, 0], "0.9": [-86, 0, 0], "1.0": [20, 0, 0], "1.4": [8, 0, 0], "2.2": [0, 0, 0]}},
        "body": {"rotation": {"0.0": [0, 0, 0], "0.6": [-14, 0, 0], "0.9": [-18, 0, 0], "1.0": [10, 0, 0], "1.4": [3, 0, 0], "2.2": [0, 0, 0]},
                 "position": {"0.0": [0, 0, 0], "0.9": [0, 4.5, 0], "1.0": [0, -4, 0], "1.4": [0, -1, 0], "2.2": [0, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.8": [-22, 0, 0], "1.0": [20, 0, 0], "1.5": [6, 0, 0], "2.2": [0, 0, 0]}},
        "trunk0": {"rotation": {"0.0": [0, 0, 0], "0.8": [-60, 0, 0], "1.0": [30, 0, 0], "2.2": [0, 0, 0]}}}}
    A[S + "armor"] = {"loop": True, "bones": {                                            # زئير: الراس لفوق والخرطوم مرفوع وجسمه يرتج (5)
        "head": {"rotation": [f"-26 + math.sin({LT}*1200)*1.5", 0, 0]},
        "trunk0": {"rotation": [-50, 0, 0]}, "trunk1": {"rotation": [-25, 0, 0]}, "trunk2": {"rotation": [-15, 0, 0]},
        "body": {"rotation": [-5, 0, 0], "position": [0, f"math.sin({LT}*1500)*0.6", 0]},
        "leg_fl": {"rotation": [-8, 0, 0]}, "leg_fr": {"rotation": [-8, 0, 0]},
        "ear_l": {"rotation": [0, 30, 0]}, "ear_r": {"rotation": [0, -30, 0]}}}
    A[S + "death"] = {"loop": "hold_on_last_frame", "animation_length": 1.0, "bones": {  # يتهاوى للقدام
        "body": {"position": {"0.0": [0, 0, 0], "0.7": [0, -9, 0], "1.0": [0, -13, 0]}, "rotation": {"0.0": [0, 0, 0], "0.7": [14, 0, 4], "1.0": [20, 0, 8]}},
        "leg_fl": {"rotation": {"0.0": [0, 0, 0], "1.0": [-38, 0, 0]}}, "leg_fr": {"rotation": {"0.0": [0, 0, 0], "1.0": [-30, 0, 0]}},
        "leg_bl": {"rotation": {"0.0": [0, 0, 0], "1.0": [32, 0, 0]}}, "leg_br": {"rotation": {"0.0": [0, 0, 0], "1.0": [28, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "1.0": [50, 0, 0]}}, "trunk0": {"rotation": {"0.0": [0, 0, 0], "1.0": [28, 0, 0]}},
        "ear_l": {"rotation": {"0.0": [0, 0, 0], "1.0": [0, 34, 0]}}, "ear_r": {"rotation": {"0.0": [0, 0, 0], "1.0": [0, -34, 0]}},
        "tail": {"rotation": {"0.0": [0, 0, 0], "1.0": [-40, 0, 0]}}}}



def bear_anims(A):
    S = "animation.sh_grey_bear."
    D = "query.modified_distance_moved"
    MS = "query.modified_move_speed"
    A[S + "idle"] = {"loop": True, "bones": {
        "body": {"position": [0, f"math.sin({LT}*90)*0.25", 0]},
        "chest": {"rotation": [f"math.sin({LT}*90)*1.5", f"math.sin({LT}*40)*3", 0]},
        "head": {"rotation": [f"math.sin({LT}*55)*3", f"math.sin({LT}*32)*12", 0]},
        "jaw": {"rotation": [f"math.max(0, math.sin({LT}*45))*4", 0, 0]},
        "arm_l": {"rotation": [f"math.sin({LT}*90)*3", 0, f"-math.sin({LT}*60)*2"]},
        "arm_r": {"rotation": [f"math.sin({LT}*90 + 40)*3", 0, f"math.sin({LT}*60)*2"]},
        "tail": {"rotation": [0, f"math.sin({LT}*140)*12", 0]}}}
    A[S + "walk"] = {"loop": True, "bones": {                                             # مشي ثقيل على رجلين: تمايل جانبي والذراعين عكس الأرجل
        "leg_l": {"rotation": [f"math.cos({D}*24)*30*{MS}", 0, 0]},
        "leg_r": {"rotation": [f"-math.cos({D}*24)*30*{MS}", 0, 0]},
        "arm_l": {"rotation": [f"-math.cos({D}*24)*20*{MS}", 0, 0]},
        "arm_r": {"rotation": [f"math.cos({D}*24)*20*{MS}", 0, 0]},
        "body": {"rotation": [0, 0, f"math.cos({D}*24)*4*{MS}"], "position": [0, f"math.abs(math.sin({D}*24))*0.8*{MS}", 0]},
        "chest": {"rotation": [0, f"math.cos({D}*24)*6*{MS}", 0]},
        "head": {"rotation": [f"math.sin({D}*48)*2*{MS}", f"-math.cos({D}*24)*5*{MS}", 0]}}}
    at = "variable.attack_time*180"
    A[S + "attack"] = {"loop": True, "bones": {                                           # ضربة عادية: لطمة بالكف اليمين
        "arm_r": {"rotation": [f"-math.sin({at})*95", 0, f"math.sin({at})*25"]},
        "fore_r": {"rotation": [f"-math.sin({at})*20", 0, 0]},
        "chest": {"rotation": [f"math.sin({at})*8", f"math.sin({at})*22", 0]},
        "jaw": {"rotation": [f"math.sin({at})*18", 0, 0]}}}
    A[S + "hug_open"] = {"loop": "hold_on_last_frame", "animation_length": 0.7, "bones": {    # يوقف عالي ويفتح ذراعيه (1)
        "chest": {"rotation": {"0.0": [0, 0, 0], "0.5": [-14, 0, 0], "0.7": [-10, 0, 0]}},
        "body": {"position": {"0.0": [0, 0, 0], "0.5": [0, 1.2, 0]}},
        "arm_l": {"rotation": {"0.0": [0, 0, 0], "0.5": [-18, 28, 56], "0.7": [-20, 30, 60]}},       # ذراعين مفتوحة على الجانبين بعلو الكتف (مقاسة)
        "arm_r": {"rotation": {"0.0": [0, 0, 0], "0.5": [-18, -28, -56], "0.7": [-20, -30, -60]}},
        "fore_l": {"rotation": {"0.0": [0, 0, 0], "0.6": [-20, 0, 0]}}, "fore_r": {"rotation": {"0.0": [0, 0, 0], "0.6": [-20, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.5": [-14, 0, 0]}}, "jaw": {"rotation": {"0.0": [0, 0, 0], "0.5": [26, 0, 0]}}}}
    sq = f"math.max(0, math.sin({LT}*720))"
    A[S + "hug_hold"] = {"loop": True, "bones": {                                         # العناق: الذراعين مسكرة قدامه ويعصر (2)
        "chest": {"rotation": [f"10 + {sq}*6", 0, 0]},
        "arm_l": {"rotation": [f"-30 - {sq}*4", -20, f"40 + {sq}*6"]},                       # الذراعين مسكرة قدام الصدر (يعصر)
        "arm_r": {"rotation": [f"-30 - {sq}*4", 20, f"-40 - {sq}*6"]},
        "fore_l": {"rotation": [f"-60 - {sq}*8", 0, 0]}, "fore_r": {"rotation": [f"-60 - {sq}*8", 0, 0]},
        "head": {"rotation": [f"-8 + {sq}*6", 0, 0]}, "jaw": {"rotation": [f"10 + {sq}*12", 0, 0]}}}
    A[S + "throw"] = {"loop": "hold_on_last_frame", "animation_length": 0.6, "bones": {        # يلف جسمه ويرمي (3)
        "chest": {"rotation": {"0.0": [10, 0, 0], "0.25": [0, -70, 0], "0.4": [-6, 45, 0], "0.6": [0, 0, 0]}},
        "arm_l": {"rotation": {"0.0": [-30, -20, 40], "0.25": [-110, 0, 20], "0.4": [-150, 0, -10], "0.6": [-20, 0, 0]}},
        "arm_r": {"rotation": {"0.0": [-30, 20, -40], "0.25": [-110, 0, -20], "0.4": [-150, 0, 10], "0.6": [-20, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.3": [-20, 0, 0], "0.6": [0, 0, 0]}}, "jaw": {"rotation": {"0.0": [10, 0, 0], "0.4": [30, 0, 0], "0.6": [0, 0, 0]}}}}
    sw = f"math.mod({LT}, 0.4) / 0.4"
    A[S + "scratch"] = {"loop": True, "bones": {                                          # خرمشة: لطمات بالمخالب يمين/يسار بالتناوب (4)
        "arm_r": {"rotation": [f"math.mod({LT}, 0.8) < 0.4 ? -140 + {sw}*170 : -20", f"math.mod({LT}, 0.8) < 0.4 ? -20 + {sw}*30 : 0", 20]},
        "arm_l": {"rotation": [f"math.mod({LT}, 0.8) >= 0.4 ? -140 + {sw}*170 : -20", f"math.mod({LT}, 0.8) >= 0.4 ? 20 - {sw}*30 : 0", -20]},
        "fore_r": {"rotation": [-25, 0, 0]}, "fore_l": {"rotation": [-25, 0, 0]},
        "chest": {"rotation": [f"8 + math.sin({LT}*900)*3", f"math.sin({LT}*450)*20", 0]},
        "head": {"rotation": [-6, f"-math.sin({LT}*450)*10", 0]}, "jaw": {"rotation": [f"16 + math.sin({LT}*900)*6", 0, 0]}}}
    A[S + "roar"] = {"loop": True, "bones": {                                              # زئير: الراس لفوق والفك مفتوح والذراعين مفتوحة (5)
        "chest": {"rotation": [f"-16 + math.sin({LT}*1500)*1.5", 0, 0]},
        "head": {"rotation": [f"-28 + math.sin({LT}*1800)*2", 0, 0]}, "jaw": {"rotation": [f"34 + math.sin({LT}*2000)*4", 0, 0]},
        "arm_l": {"rotation": [-25, 40, 55]}, "arm_r": {"rotation": [-25, -40, -55]},
        "fore_l": {"rotation": [-40, 0, 0]}, "fore_r": {"rotation": [-40, 0, 0]}}}
    br = f"math.sin({LT}*60)"
    A[S + "sleep"] = {"loop": True, "bones": {                                             # سبات: قاعد على مؤخرته منحني ومحتضن ركبه (6)
        "body": {"position": [0, -13, 1], "rotation": [-10, 0, 0]},
        "leg_l": {"rotation": [-82, -12, 0]}, "leg_r": {"rotation": [-82, 12, 0]},
        "chest": {"rotation": [f"30 + {br}*3", 0, 0]},
        "head": {"rotation": [f"26 + {br}*2", 0, 0]}, "jaw": {"rotation": [0, 0, 0]},
        "arm_l": {"rotation": [-15, -20, 35]}, "arm_r": {"rotation": [-15, 20, -35]},
        "fore_l": {"rotation": [-50, 0, 0]}, "fore_r": {"rotation": [-50, 0, 0]}}}
    A[S + "death"] = {"loop": "hold_on_last_frame", "animation_length": 1.2, "bones": {      # يتهاوى لورا على ظهره
        "root": {"rotation": {"0.0": [0, 0, 0], "0.5": [12, 0, 0], "1.0": [80, 0, 6], "1.2": [86, 0, 6]},
                 "position": {"0.0": [0, 0, 0], "1.0": [0, 0, 6], "1.2": [0, 0, 7]}},
        "arm_l": {"rotation": {"0.0": [0, 0, 0], "1.0": [-30, 0, 50]}}, "arm_r": {"rotation": {"0.0": [0, 0, 0], "1.0": [-30, 0, -50]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "1.0": [-30, 20, 0]}}, "jaw": {"rotation": {"0.0": [0, 0, 0], "1.0": [22, 0, 0]}},
        "leg_l": {"rotation": {"0.0": [0, 0, 0], "1.0": [-30, 0, 0]}}, "leg_r": {"rotation": {"0.0": [0, 0, 0], "1.0": [-14, 0, 0]}}}}

def mantis_anims(A):
    S = "animation.sh_prayer_mantis."
    D = "query.modified_distance_moved"
    MS = "query.modified_move_speed"
    A[S + "idle"] = {"loop": True, "bones": {                                             # تمايل مثل ورقة بالهوا + راس يميل + قرون ترتجف
        "body": {"rotation": [0, 0, f"math.sin({LT}*70)*1.8"], "position": [0, f"math.sin({LT}*90)*0.2", 0]},
        "thorax": {"rotation": [f"math.sin({LT}*60)*2.5", f"math.sin({LT}*25)*5", 0]},
        "head": {"rotation": [f"math.sin({LT}*40)*4", f"math.sin({LT}*30)*14", f"math.sin({LT}*45)*9"]},
        "ant_l": {"rotation": [f"math.sin({LT}*210)*6", 0, f"math.sin({LT}*150)*4"]},
        "ant_r": {"rotation": [f"math.sin({LT}*190 + 50)*6", 0, f"-math.sin({LT}*160)*4"]},
        "arm_l": {"rotation": [f"math.sin({LT}*60)*3", 0, 0]}, "arm_r": {"rotation": [f"math.sin({LT}*60 + 20)*3", 0, 0]},
        "claw_l": {"rotation": [f"math.max(0, math.sin({LT}*35))*-8", 0, 0]},
        "abdomen": {"rotation": [f"math.sin({LT}*50)*1.5", 0, 0]}}}
    A[S + "walk"] = {"loop": True, "bones": {                                             # مشي متمايل (يهز جسمه قدام وورا مثل غصن)
        "leg_ml": {"rotation": [f"math.cos({D}*30)*24*{MS}", 0, 0]},
        "leg_br": {"rotation": [f"math.cos({D}*30)*24*{MS}", 0, 0]},
        "leg_mr": {"rotation": [f"-math.cos({D}*30)*24*{MS}", 0, 0]},
        "leg_bl": {"rotation": [f"-math.cos({D}*30)*24*{MS}", 0, 0]},
        "body": {"rotation": [f"math.sin({D}*30)*2*{MS}", 0, f"math.cos({D}*30)*3*{MS}"], "position": [0, f"math.abs(math.sin({D}*30))*0.6*{MS}", 0]},
        "thorax": {"rotation": [f"-math.sin({D}*30)*4*{MS}", 0, 0]}}}
    at = "variable.attack_time*180"
    A[S + "attack"] = {"loop": True, "bones": {                                           # ضربة عادية: المنجل اليمين ينفتح ويضرب لقدام
        "thorax": {"rotation": [f"math.sin({at})*16", 0, 0]},
        "arm_r": {"rotation": [f"-math.sin({at})*70", 0, 0]},
        "fore_r": {"rotation": [f"math.sin({at})*30", 0, 0]},
        "claw_r": {"rotation": [f"-math.sin({at})*95", 0, 0]}}}
    sway = f"math.sin({LT}*120)"
    A[S + "stance"] = {"loop": True, "bones": {                                           # وضعية الصلاة المضادة: يوقف عالي، المناجل مرفوعة ومفتوحة، الأجنحة منفوشة (1)
        "body": {"rotation": [f"-8 + {sway}*1.5", 0, 0], "position": [0, 1.5, 0]},
        "thorax": {"rotation": [-16, f"{sway}*6", 0]},
        "head": {"rotation": [14, 0, f"{sway}*6"]},
        "arm_l": {"rotation": [f"-38 + {sway}*4", 0, 32]}, "arm_r": {"rotation": [f"-38 - {sway}*4", 0, -32]},
        "fore_l": {"rotation": [10, 0, 0]}, "fore_r": {"rotation": [10, 0, 0]},
        "claw_l": {"rotation": [-92, 0, 0]}, "claw_r": {"rotation": [-92, 0, 0]},
        "wing_l": {"rotation": [f"34 + {sway}*3", 0, 26]}, "wing_r": {"rotation": [f"34 + {sway}*3", 0, -26]},
        "abdomen": {"rotation": [-8, 0, 0]}}}
    A[S + "camo"] = {"loop": True, "bones": {                                             # التمويه: ينخفض وتنطوي المناجل ويتمايل مثل ورقة (2)
        "body": {"rotation": [0, 0, f"math.sin({LT}*90)*3"]},
        "thorax": {"rotation": [22, 0, f"math.sin({LT}*90)*2"]},
        "head": {"rotation": [-14, 0, 0]},
        "arm_l": {"rotation": [26, 0, 0]}, "arm_r": {"rotation": [26, 0, 0]},
        "claw_l": {"rotation": [8, 0, 0]}, "claw_r": {"rotation": [8, 0, 0]},
        "abdomen": {"rotation": [-5, 0, 0]}}}
    A[S + "stab"] = {"loop": "hold_on_last_frame", "animation_length": 0.6, "bones": {    # طعنة من التمويه: المنجلين ينطلقون لقدام وينسدون (3)
        "thorax": {"rotation": {"0.0": [22, 0, 0], "0.12": [46, 0, 0], "0.35": [40, 0, 0], "0.6": [10, 0, 0]}},
        "arm_l": {"rotation": {"0.0": [26, 0, 0], "0.12": [-96, 0, -6], "0.35": [-90, 0, -6], "0.6": [-20, 0, 0]}},
        "arm_r": {"rotation": {"0.0": [26, 0, 0], "0.12": [-96, 0, 6], "0.35": [-90, 0, 6], "0.6": [-20, 0, 0]}},
        "fore_l": {"rotation": {"0.0": [0, 0, 0], "0.12": [40, 0, 0], "0.6": [0, 0, 0]}},
        "fore_r": {"rotation": {"0.0": [0, 0, 0], "0.12": [40, 0, 0], "0.6": [0, 0, 0]}},
        "claw_l": {"rotation": {"0.0": [8, 0, 0], "0.1": [-110, 0, 0], "0.2": [0, 0, 0], "0.6": [0, 0, 0]}},
        "claw_r": {"rotation": {"0.0": [8, 0, 0], "0.1": [-110, 0, 0], "0.2": [0, 0, 0], "0.6": [0, 0, 0]}}}}
    sq = f"math.max(0, math.sin({LT}*900))"
    A[S + "lock"] = {"loop": True, "bones": {                                             # قفل المقص: المنجلين قدامه مسكرين على الضحية ويعصرون (4)
        "thorax": {"rotation": [24, 0, 0]}, "head": {"rotation": [18, 0, f"math.sin({LT}*300)*5"]},
        "arm_l": {"rotation": [-84, 0, -14]}, "arm_r": {"rotation": [-84, 0, 14]},
        "fore_l": {"rotation": [36, 0, 0]}, "fore_r": {"rotation": [36, 0, 0]},
        "claw_l": {"rotation": [f"-26 + {sq}*12", 0, 0]}, "claw_r": {"rotation": [f"-26 + {sq}*12", 0, 0]},
        "ant_l": {"rotation": [-20, 0, 0]}, "ant_r": {"rotation": [-20, 0, 0]}}}
    sh = f"math.sin({LT}*2400)"
    A[S + "molt"] = {"loop": True, "bones": {                                             # الانسلاخ: يتقوس لورا ويرتجف، الأجنحة مفتوحة والمناجل للسما (5)
        "body": {"rotation": [f"-10 + {sh}*3", 0, f"{sh}*2"], "position": [0, 1, 0]},
        "thorax": {"rotation": [f"-26 + {sh}*2", 0, 0]}, "head": {"rotation": [-26, 0, f"{sh}*6"]},
        "arm_l": {"rotation": [-140, 0, 30]}, "arm_r": {"rotation": [-140, 0, -30]},
        "claw_l": {"rotation": [-60, 0, 0]}, "claw_r": {"rotation": [-60, 0, 0]},
        "wing_l": {"rotation": [f"56 + {sh}*6", 0, 48]}, "wing_r": {"rotation": [f"56 + {sh}*6", 0, -48]},
        "abdomen": {"rotation": [f"-14 + {sh}*3", 0, 0]}}}
    A[S + "counter"] = {"loop": "hold_on_last_frame", "animation_length": 0.7, "bones": {  # الرد: المنجلين فوق راسه وينزلون بشكل X (6)
        "thorax": {"rotation": {"0.0": [-16, 0, 0], "0.15": [-24, 0, 0], "0.3": [34, 0, 0], "0.7": [10, 0, 0]}},
        "arm_l": {"rotation": {"0.0": [-38, 0, 32], "0.15": [-150, 0, 20], "0.3": [-40, 0, -34], "0.7": [-20, 0, 0]}},
        "arm_r": {"rotation": {"0.0": [-38, 0, -32], "0.15": [-150, 0, -20], "0.3": [-40, 0, 34], "0.7": [-20, 0, 0]}},
        "claw_l": {"rotation": {"0.0": [-92, 0, 0], "0.15": [-100, 0, 0], "0.3": [-110, 0, 0], "0.7": [0, 0, 0]}},
        "claw_r": {"rotation": {"0.0": [-92, 0, 0], "0.15": [-100, 0, 0], "0.3": [-110, 0, 0], "0.7": [0, 0, 0]}},
        "wing_l": {"rotation": {"0.0": [34, 0, 26], "0.3": [50, 0, 40], "0.7": [0, 0, 0]}},
        "wing_r": {"rotation": {"0.0": [34, 0, -26], "0.3": [50, 0, -40], "0.7": [0, 0, 0]}}}}
    A[S + "death"] = {"loop": "hold_on_last_frame", "animation_length": 1.1, "bones": {   # يطيح على جنبه والأرجل تنطوي
        "root": {"rotation": {"0.0": [0, 0, 0], "0.6": [0, 0, 60], "1.1": [0, 0, 84]}, "position": {"0.0": [0, 0, 0], "1.1": [-6, 2, 0]}},
        "leg_ml": {"rotation": {"0.0": [0, 0, 0], "1.1": [0, 0, -40]}}, "leg_bl": {"rotation": {"0.0": [0, 0, 0], "1.1": [0, 0, -46]}},
        "leg_mr": {"rotation": {"0.0": [0, 0, 0], "1.1": [0, 0, 36]}}, "leg_br": {"rotation": {"0.0": [0, 0, 0], "1.1": [0, 0, 40]}},
        "arm_l": {"rotation": {"0.0": [0, 0, 0], "1.1": [30, 0, 0]}}, "arm_r": {"rotation": {"0.0": [0, 0, 0], "1.1": [40, 0, 0]}},
        "claw_l": {"rotation": {"0.0": [0, 0, 0], "1.1": [12, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "1.1": [20, 0, -20]}},
        "ant_l": {"rotation": {"0.0": [0, 0, 0], "1.1": [30, 0, 0]}}, "ant_r": {"rotation": {"0.0": [0, 0, 0], "1.1": [30, 0, 0]}}}}


def harvester_anims(A):
    """الحاصد الأجوف: يتحرك مثل دمية خيوط (رجات مفاجئة، راس يتدلى ويميل، صليب الدمية فوقه يتأرجح).
    الإيد اليمين ماسكة المنجل: لما ترتفع الإيد، عظمة المنجل تلف بعكسها حتى النصل يبقى فوق (ارتفاع فوق الراس ثم حصدة لتحت)."""
    S = "animation.sh_hollow_harvester."
    D = "query.modified_distance_moved"
    MS = "query.modified_move_speed"
    jerk = f"(math.mod({LT}, 3.4) < 0.16 ? 18 : 0)"                                       # رجة راس مفاجئة كل ~3 ثواني
    A[S + "idle"] = {"loop": True, "bones": {
        "body": {"rotation": [f"5 + math.sin({LT}*40)*2", 0, f"math.sin({LT}*52)*3"]},
        "head": {"rotation": [f"6 + math.sin({LT}*33)*4", 0, f"math.sin({LT}*41)*8 + {jerk}"]},
        "hat": {"rotation": [0, 0, f"math.sin({LT}*41)*2"]},
        "arm_l": {"rotation": [f"math.sin({LT}*47)*6", 0, f"5 + math.sin({LT}*39)*4"]},
        "arm_r": {"rotation": [f"math.sin({LT}*47 + 40)*3", 0, -3]},
        "leg_l": {"rotation": [f"math.sin({LT}*47)*2", 0, 0]}, "leg_r": {"rotation": [f"-math.sin({LT}*47)*2", 0, 0]},
        "control": {"position": [0, f"math.sin({LT}*60)*0.5", 0], "rotation": [0, f"math.sin({LT}*25)*5", 0]}}}
    A[S + "walk"] = {"loop": True, "bones": {                                             # مشية دمية: رجلين متيبسة وقفزات صغيرة كأن الخيوط ترفعه
        "leg_l": {"rotation": [f"math.cos({D}*26)*34*{MS}", 0, 0]},
        "leg_r": {"rotation": [f"-math.cos({D}*26)*34*{MS}", 0, 0]},
        "body": {"position": [0, f"math.abs(math.sin({D}*26))*1.4*{MS}", 0], "rotation": [f"6*{MS}", 0, f"math.sin({D}*26)*5*{MS}"]},
        "arm_l": {"rotation": [f"-math.cos({D}*26)*26*{MS}", 0, 0]},
        "arm_r": {"rotation": [f"-math.cos({D}*26)*8*{MS}", 0, 0]},
        "head": {"rotation": [0, 0, f"math.sin({D}*52)*7*{MS}"]},
        "control": {"position": [0, f"math.abs(math.sin({D}*26))*0.8*{MS}", 0]}}}
    at = "variable.attack_time*180"
    A[S + "attack"] = {"loop": True, "bones": {                                           # ضربة عادية: ترفع المنجل وتقطع لقدام
        "arm_r": {"rotation": [f"-math.sin({at})*100", 0, f"math.sin({at})*12"]},
        "scythe": {"rotation": [f"math.sin({at})*120", 0, 0]},
        "body": {"rotation": [f"math.sin({at})*8", f"-math.sin({at})*20", 0]}}}
    A[S + "strings"] = {"loop": True, "bones": {                                          # خيوط الدمية (1): الإيد اليسار تأشر عليك وترتجف
        "arm_l": {"rotation": [f"-82 + math.sin({LT}*1400)*2", -10, -8]},
        "body": {"rotation": [-6, -14, 0]}, "head": {"rotation": [4, 0, 16]},
        "arm_r": {"rotation": [6, 0, -4]}, "control": {"rotation": [14, 0, 0]}}}
    A[S + "yank"] = {"loop": "hold_on_last_frame", "animation_length": 0.5, "bones": {    # السحبة (2): الإيد ترجع بقوة والصليب ينسحب
        "arm_l": {"rotation": {"0.0": [-82, -10, -8], "0.12": [30, 0, -14], "0.5": [10, 0, -5]}},
        "body": {"rotation": {"0.0": [-6, -14, 0], "0.12": [-14, 12, 0], "0.5": [0, 0, 0]}},
        "head": {"rotation": {"0.0": [4, 0, 16], "0.12": [-10, 0, -8], "0.5": [0, 0, 0]}},
        "control": {"rotation": {"0.0": [14, 0, 0], "0.12": [-22, 0, 0], "0.5": [0, 0, 0]}}}}
    A[S + "stare"] = {"loop": True, "bones": {                                            # النظرة الجوفاء (3): الراس مايل كلش ويرتجف
        "head": {"rotation": [f"12 + math.sin({LT}*1800)*1.2", 0, f"34 + math.sin({LT}*1500)*1.5"]},
        "body": {"rotation": [12, 0, 0]}, "arm_l": {"rotation": [8, 0, 8]}, "arm_r": {"rotation": [6, 0, -6]},
        "control": {"rotation": [0, 0, -10], "position": [0, -1, 0]}}}
    A[S + "reap"] = {"loop": "hold_on_last_frame", "animation_length": 1.1, "bones": {    # المنجل الخاتم (4): يرفعه فوق راسه ثم حصدة قوية لقدام
        "arm_r": {"rotation": {"0.0": [0, 0, 0], "0.45": [-150, 0, -16], "0.55": [-154, 0, -16], "0.72": [-40, 0, 34], "0.9": [-22, 0, 20], "1.1": [0, 0, 0]}},
        "scythe": {"rotation": {"0.0": [0, 0, 0], "0.45": [120, 0, 0], "0.55": [122, 0, 0], "0.72": [110, 0, 0], "0.9": [60, 0, 0], "1.1": [0, 0, 0]}},
        "body": {"rotation": {"0.0": [0, 0, 0], "0.45": [-10, 30, 0], "0.55": [-10, 32, 0], "0.72": [16, -35, 0], "1.1": [0, 0, 0]}},
        "arm_l": {"rotation": {"0.0": [0, 0, 0], "0.45": [-30, 0, 20], "0.72": [10, 0, 10], "1.1": [0, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.5": [-8, 0, 0], "0.72": [14, 0, 0], "1.1": [0, 0, 0]}},
        "control": {"rotation": {"0.0": [0, 0, 0], "0.5": [-12, 0, 0], "0.72": [18, 0, 0], "1.1": [0, 0, 0]}}}}
    A[S + "burn"] = {"loop": True, "bones": {                                             # يحترق (5): يتخبط ويهز إيديه وراسه
        "arm_l": {"rotation": [f"-60 + math.sin({LT}*900)*50", 0, f"20 + math.sin({LT}*700)*15"]},
        "arm_r": {"rotation": [f"-40 + math.sin({LT}*900 + 90)*30", 0, -15]},
        "head": {"rotation": [f"math.sin({LT}*1100)*10", f"math.sin({LT}*800)*20", f"math.sin({LT}*1300)*12"]},
        "body": {"rotation": [f"math.sin({LT}*1000)*4", f"math.sin({LT}*600)*10", 0]},
        "control": {"rotation": [f"math.sin({LT}*900)*10", 0, f"math.sin({LT}*700)*10"]}}}
    A[S + "death"] = {"loop": "hold_on_last_frame", "animation_length": 1.4, "bones": {   # الخيوط تنقطع: يطيح كومة، القبعة تطيح، والصليب يرتفع ويبتعد
        "root": {"position": {"0.0": [0, 0, 0], "0.5": [0, -8, 0], "1.0": [0, -13, 0]}},
        "leg_l": {"rotation": {"0.0": [0, 0, 0], "0.5": [-80, 0, -10], "1.0": [-90, 0, -15]}},
        "leg_r": {"rotation": {"0.0": [0, 0, 0], "0.5": [-80, 0, 10], "1.0": [-90, 0, 15]}},
        "body": {"rotation": {"0.0": [0, 0, 0], "0.6": [20, 0, 0], "1.0": [55, 0, 8], "1.4": [60, 0, 10]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.8": [30, 0, 30], "1.4": [35, 0, 40]}},
        "arm_l": {"rotation": {"0.0": [0, 0, 0], "1.0": [-20, 0, 30]}},
        "arm_r": {"rotation": {"0.0": [0, 0, 0], "1.0": [-10, 0, -20]}},
        "scythe": {"rotation": {"0.0": [0, 0, 0], "0.6": [0, 0, 0], "1.0": [60, 0, -10]}},
        "hat": {"position": {"0.0": [0, 0, 0], "0.7": [2, 2, -1], "1.4": [5, -14, -6]}, "rotation": {"0.0": [0, 0, 0], "0.7": [0, 0, -20], "1.4": [-40, 0, -70]}},
        "control": {"position": {"0.0": [0, 0, 0], "0.5": [0, 6, 0], "1.4": [0, 22, 0]}, "rotation": {"0.0": [0, 0, 0], "1.4": [0, 90, 0]}}}}


def build():
    A = load(os.path.join(RP, "animations", "sh_grim.animation.json"))
    C = load(os.path.join(RP, "animation_controllers", "sh_grim.ac.json"))
    for k in [k for k in A["animations"] if k.startswith(("animation.sh_quillback.", "animation.sh_veilfox.", "animation.sh_magmamoth.", "animation.sh_grey_bear.", "animation.sh_prayer_mantis.", "animation.sh_hollow_harvester."))]:
        del A["animations"][k]
    for k in [k for k in C["animation_controllers"] if "quillback" in k]:
        del C["animation_controllers"][k]
    fox_anims(A["animations"])
    mammoth_anims(A["animations"])
    bear_anims(A["animations"])
    mantis_anims(A["animations"])
    harvester_anims(A["animations"])
    C["animation_controllers"]["controller.animation.sh_hollow_harvester.state"] = controller(
        [("strings", 1), ("yank", 2), ("stare", 3), ("reap", 4), ("burn", 5)], death=True)
    C["animation_controllers"]["controller.animation.sh_prayer_mantis.state"] = controller(
        [("stance", 1), ("camo", 2), ("stab", 3), ("lock", 4), ("molt", 5), ("counter", 6)], death=True)
    C["animation_controllers"]["controller.animation.sh_grey_bear.state"] = controller(
        [("hug_open", 1), ("hug_hold", 2), ("throw", 3), ("scratch", 4), ("roar", 5), ("sleep", 6)], death=True)
    C["animation_controllers"]["controller.animation.sh_veilfox.state"] = controller([("volley", 1), ("pounce", 2), ("storm", 3), ("veil", 4)])
    C["animation_controllers"]["controller.animation.sh_magmamoth.state"] = controller(
        [("stomp", 1), ("breath", 2), ("run", 3), ("eruption", 4), ("armor", 5), ("lower", 6)], death=True)
    save(os.path.join(RP, "animations", "sh_grim.animation.json"), A)
    save(os.path.join(RP, "animation_controllers", "sh_grim.ac.json"), C)
    for key, m in MON.items():
        bp_entity(key, m)
    rp_entity("veilfox", MON["veilfox"], ["volley", "pounce", "storm", "veil"])
    rp_entity("magmamoth", MON["magmamoth"], ["stomp", "breath", "run", "eruption", "armor", "lower", "death", "attack"])
    rp_entity("grey_bear", MON["grey_bear"], ["hug_open", "hug_hold", "throw", "scratch", "roar", "sleep", "death", "attack"])
    rp_entity("bear_cub", MON["bear_cub"], [])
    rp_entity("prayer_mantis", MON["prayer_mantis"], ["stance", "camo", "stab", "lock", "molt", "counter", "death", "attack"])
    rp_entity("hollow_harvester", MON["hollow_harvester"], ["strings", "yank", "stare", "reap", "burn", "death", "attack"])
    rc = {"format_version": "1.8.0", "render_controllers": {"controller.render.sh_mammoth": {
        "arrays": {"textures": {"Array.t": ["Texture.default", "Texture.hot"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.t[query.property('sh:hot')]"]}}}
    rc["render_controllers"]["controller.render.sh_mantis"] = {                 # السرعوف: التمويه يبدل المادة (alphablend) والتكستشر (شبه شفاف)
        "arrays": {"textures": {"Array.t": ["Texture.default", "Texture.hot", "Texture.camo"]},
                   "materials": {"Array.m": ["Material.default", "Material.camo"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Array.m[query.property('sh:camo')]"}],
        "textures": ["Array.t[query.property('sh:camo') == 1 ? 2 : query.property('sh:hot')]"]}
    save(os.path.join(RP, "render_controllers", "sh_mammoth.render_controllers.json"), rc)
    lang = os.path.join(RP, "texts", "en_US.lang")
    txt = open(lang, encoding="utf-8").read()
    for key, m in MON.items():
        for line in (f"entity.{m['ident']}.name={m['name']}", f"item.spawn_egg.entity.{m['ident']}.name={m['name']} Egg"):
            if line not in txt:
                txt = txt.rstrip("\n") + "\n" + line + "\n"
    open(lang, "w", encoding="utf-8").write(txt)
    print("ok")


if __name__ == "__main__":
    build()
