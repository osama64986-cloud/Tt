"""تعريفات وحشين: ثعلب الحجاب (Veilfox، Grim) وماغماموث (Magmamoth، Vile).
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
    "magmamoth": dict(ident="sh:magmamoth", name="Magmamoth", rank="sh_rank2", hp=260, speed=0.24, atk=12, w=3.4, h=3.7, kb=0.95, xp=40,
                      egg=("#2c2a30", "#ff7a1c"), states=6, props={"sh:hot": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}),
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
    if key == "magmamoth":
        cd["textures"]["hot"] = "textures/entity/sh_magmamoth_hot"
        cd["render_controllers"] = ["controller.render.sh_mammoth"]
        cd["scale"] = None
        animate.append("attack")
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


def build():
    A = load(os.path.join(RP, "animations", "sh_grim.animation.json"))
    C = load(os.path.join(RP, "animation_controllers", "sh_grim.ac.json"))
    for k in [k for k in A["animations"] if k.startswith(("animation.sh_quillback.", "animation.sh_veilfox.", "animation.sh_magmamoth."))]:
        del A["animations"][k]
    for k in [k for k in C["animation_controllers"] if "quillback" in k]:
        del C["animation_controllers"][k]
    fox_anims(A["animations"])
    mammoth_anims(A["animations"])
    C["animation_controllers"]["controller.animation.sh_veilfox.state"] = controller([("volley", 1), ("pounce", 2), ("storm", 3), ("veil", 4)])
    C["animation_controllers"]["controller.animation.sh_magmamoth.state"] = controller(
        [("stomp", 1), ("breath", 2), ("run", 3), ("eruption", 4), ("armor", 5), ("lower", 6)], death=True)
    save(os.path.join(RP, "animations", "sh_grim.animation.json"), A)
    save(os.path.join(RP, "animation_controllers", "sh_grim.ac.json"), C)
    for key, m in MON.items():
        bp_entity(key, m)
    rp_entity("veilfox", MON["veilfox"], ["volley", "pounce", "storm", "veil"])
    rp_entity("magmamoth", MON["magmamoth"], ["stomp", "breath", "run", "eruption", "armor", "lower", "death", "attack"])
    rc = {"format_version": "1.8.0", "render_controllers": {"controller.render.sh_mammoth": {
        "arrays": {"textures": {"Array.t": ["Texture.default", "Texture.hot"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.t[query.property('sh:hot')]"]}}}
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
