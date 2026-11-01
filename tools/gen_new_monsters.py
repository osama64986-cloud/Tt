"""تعريفات الوحشين الجديدين: شوكاني (Quillback، Lowly) وثعلب الحجاب (Veilfox، Grim).
يكتب: كيان BP، كيان RP، الأنميشن، متحكمات الأنميشن، النصوص. (الموديل والتكستشر من gen_grim_monsters.py)
التشغيل: python3 tools/gen_new_monsters.py"""
import copy
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
    "quillback": dict(ident="sh:quillback", name="Quillback", rank="sh_rank0", hp=34, speed=0.26, atk=4, w=1.2, h=1.1, kb=0.2, xp=6,
                      egg=("#3a2a32", "#ff9628"), states=3),
    "veilfox": dict(ident="sh:veilfox", name="Veilfox", rank="sh_rank1", hp=78, speed=0.34, atk=6, w=1.0, h=1.7, kb=0.4, xp=12,
                    egg=("#2a2640", "#8c64ff"), states=3),
}


def bp_entity(m):
    d = load(os.path.join(BP, "entities", "sh_gloomhorn.json"))
    e = d["minecraft:entity"]
    e["description"]["identifier"] = m["ident"]
    e["description"]["properties"]["sh:state"]["range"] = [0, m["states"]]
    c = e["components"]
    c["minecraft:type_family"]["family"] = ["sh_monster", m["rank"]]
    c["minecraft:health"] = {"value": m["hp"], "max": m["hp"]}
    c["minecraft:collision_box"] = {"width": m["w"], "height": m["h"]}
    c["minecraft:movement"] = {"value": m["speed"]}
    c["minecraft:attack"] = {"damage": m["atk"]}
    c["minecraft:knockback_resistance"] = {"value": m["kb"]}
    c["minecraft:experience_reward"] = {"on_death": f"query.last_hit_by_player ? {m['xp']} : 0"}
    save(os.path.join(BP, "entities", f"sh_{m['ident'].split(':')[1]}.json"), d)


def rp_entity(key, m, anims):
    d = load(os.path.join(RP, "entity", "sh_gloomhorn.entity.json"))
    cd = d["minecraft:client_entity"]["description"]
    cd["identifier"] = m["ident"]
    cd["textures"]["default"] = f"textures/entity/sh_{key}"
    cd["geometry"]["default"] = f"geometry.sh_{key}"
    cd["animations"] = {"idle": f"animation.sh_{key}.idle", "walk": f"animation.sh_{key}.walk", "state": f"controller.animation.sh_{key}.state", "look": "animation.sh.look"}
    for a in anims:
        cd["animations"][a] = f"animation.sh_{key}.{a}"
    cd["spawn_egg"] = {"base_color": m["egg"][0], "overlay_color": m["egg"][1]}
    save(os.path.join(RP, "entity", f"sh_{key}.entity.json"), d, indent=2)


def controller(key, names):
    """names = [(اسم الحالة, رقم sh:state)] مثل gloomhorn: default + حالات تنتقل لبعض حسب الخاصية."""
    states = {"default": {"transitions": [{n: f"query.property('sh:state') == {i}"} for n, i in names], "blend_transition": 0.18}}
    for n, i in names:
        tr = [{"default": "query.property('sh:state') == 0"}] + [{n2: f"query.property('sh:state') == {i2}"} for n2, i2 in names if n2 != n]
        states[n] = {"animations": [n], "transitions": tr, "blend_transition": 0.12}
    return {"initial_state": "default", "states": states}


def walk(legs, amp=32, k=38, body=0.6):
    t = f"query.modified_distance_moved*{k}"
    ms = "query.modified_move_speed"
    pairs = {legs[0]: 1, legs[1]: -1, legs[2]: -1, legs[3]: 1}
    bones = {n: {"rotation": [f"{'-' if s < 0 else ''}math.cos({t})*{amp}*{ms}", 0, 0]} for n, s in pairs.items()}
    bones["body"] = {"position": [0, f"math.abs(math.sin({t}))*{body}*{ms}", 0]}
    return {"loop": True, "bones": bones}


def build():
    A = load(os.path.join(RP, "animations", "sh_grim.animation.json"))
    C = load(os.path.join(RP, "animation_controllers", "sh_grim.ac.json"))
    for k in [k for k in A["animations"] if k.startswith(("animation.sh_quillback.", "animation.sh_veilfox."))]:
        del A["animations"][k]
    lt = "query.life_time"
    # ───────── شوكاني ─────────
    q = A["animations"]
    q["animation.sh_quillback.idle"] = {"loop": True, "bones": {
        "body": {"position": [0, f"math.sin({lt}*100)*0.25", 0]},
        "head": {"rotation": [f"math.sin({lt}*70)*3", f"math.sin({lt}*40)*8", 0]},
        "spines": {"rotation": [0, 0, f"math.sin({lt}*90)*1.5"]},
        "tail": {"rotation": [f"math.sin({lt}*120)*8", 0, 0]}}}
    q["animation.sh_quillback.walk"] = walk(["leg_fl", "leg_fr", "leg_bl", "leg_br"], 36, 46, 0.4)
    q["animation.sh_quillback.walk"]["bones"]["head"] = {"rotation": ["math.sin(query.modified_distance_moved*92)*4*query.modified_move_speed + 5", 0, 0]}
    q["animation.sh_quillback.volley"] = {"loop": True, "bones": {                       # يرفع الشوك ويهز جسمه (1)
        "spines": {"scale": [1, f"1.3 + math.sin({lt}*900)*0.08", 1], "rotation": [0, 0, f"math.sin({lt}*1100)*3"]},
        "body": {"rotation": [-8, 0, 0], "position": [0, -0.4, 0]},
        "head": {"rotation": [-22, 0, 0]},
        "leg_fl": {"rotation": [-18, 0, 0]}, "leg_fr": {"rotation": [-18, 0, 0]},
        "tail": {"rotation": [-30, 0, 0]}}}
    q["animation.sh_quillback.roll"] = {"loop": True, "bones": {                         # يتكور ويلف (2)
        "body": {"rotation": [f"{lt}*1100", 0, 0], "position": [0, 0.6, 0]},
        "head": {"rotation": [55, 0, 0]},
        "leg_fl": {"rotation": [-60, 0, 0]}, "leg_fr": {"rotation": [-60, 0, 0]},
        "leg_bl": {"rotation": [60, 0, 0]}, "leg_br": {"rotation": [60, 0, 0]},
        "tail": {"rotation": [70, 0, 0]}, "spines": {"scale": [1.15, 1.0, 1.15]}}}
    q["animation.sh_quillback.burst"] = {"loop": "hold_on_last_frame", "animation_length": 1.2, "bones": {      # ينتفخ وينفض الشوك (3)
        "spines": {"scale": {"0.0": [1, 1, 1], "0.3": [1.7, 1.5, 1.7], "0.5": [1.9, 1.7, 1.9], "1.2": [1.5, 1.3, 1.5]}},
        "body": {"position": {"0.0": [0, 0, 0], "0.3": [0, -0.8, 0], "0.5": [0, 0.8, 0], "1.2": [0, 0, 0]}, "rotation": {"0.0": [0, 0, 0], "0.3": [6, 0, 0], "0.5": [-10, 0, 0], "1.2": [0, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.3": [18, 0, 0], "0.5": [-18, 0, 0], "1.2": [0, 0, 0]}}}}
    C["animation_controllers"]["controller.animation.sh_quillback.state"] = controller("quillback", [("volley", 1), ("roll", 2), ("burst", 3)])
    # ───────── ثعلب الحجاب ─────────
    f = A["animations"]
    tails = {}
    for i, n in enumerate("abc"):
        for k in range(5):
            tails[f"tail_{n}{k}"] = {"rotation": [f"math.sin({lt}*140 - {k * 55} + {i * 70})*{5 + k * 1.5}", f"math.sin({lt}*110 - {k * 60} + {i * 70})*{4 + k}", 0]}
    f["animation.sh_veilfox.idle"] = {"loop": True, "bones": {
        "body": {"position": [0, f"math.sin({lt}*90)*0.2", 0]},
        "head": {"rotation": [f"math.sin({lt}*60)*2", f"math.sin({lt}*35)*10", 0]},
        "ear_l": {"rotation": [0, 0, f"-math.sin({lt}*140)*4 - (math.mod({lt},3.7)<0.2 ? math.sin(math.mod({lt},3.7)*1800)*14 : 0)"]},
        "ear_r": {"rotation": [0, 0, f"math.sin({lt}*140)*4 + (math.mod({lt}+1.3,4.4)<0.2 ? math.sin(math.mod({lt}+1.3,4.4)*1800)*14 : 0)"]},
        "orbs": {"rotation": [0, f"{lt}*70", 0], "position": [0, f"math.sin({lt}*120)*0.5", 0]}, **tails}}
    f["animation.sh_veilfox.walk"] = walk(["leg_fl", "leg_fr", "leg_bl", "leg_br"], 38, 40, 0.7)
    f["animation.sh_veilfox.walk"]["bones"]["neck"] = {"rotation": ["math.sin(query.modified_distance_moved*80)*3*query.modified_move_speed", 0, 0]}
    f["animation.sh_veilfox.volley"] = {"loop": True, "bones": {                         # يرفع أذياله وراسه (1)
        "head": {"rotation": [-24, 0, 0]}, "neck": {"rotation": [-16, 0, 0]},
        "body": {"rotation": [-6, 0, 0], "position": [0, 0.3, 0]},
        "orbs": {"rotation": [0, f"{lt}*420", 0]},
        "tail_a": {"rotation": [18, -14, 0]}, "tail_b": {"rotation": [22, 0, 0]}, "tail_c": {"rotation": [18, 14, 0]}}}
    f["animation.sh_veilfox.pounce"] = {"loop": True, "bones": {                         # ينحني وينطلق (2)
        "body": {"position": [0, -3.5, 0], "rotation": [10, 0, 0]},
        "head": {"rotation": [18, 0, 0]}, "neck": {"rotation": [16, 0, 0]},
        "leg_fl": {"rotation": [-40, 0, 0]}, "leg_fr": {"rotation": [-40, 0, 0]},
        "leg_bl": {"rotation": [48, 0, 0]}, "leg_br": {"rotation": [48, 0, 0]},
        "tail_a": {"rotation": [-34, -16, 0]}, "tail_b": {"rotation": [-40, 0, 0]}, "tail_c": {"rotation": [-34, 16, 0]}}}
    f["animation.sh_veilfox.storm"] = {"loop": True, "bones": {                          # يوقف على رجليه الورا والأذيال تنفرش وتدور (3)
        "body": {"rotation": [-28, 0, 0], "position": [0, 2.2, 0]},
        "leg_fl": {"rotation": [-65, 0, 0]}, "leg_fr": {"rotation": [-65, 0, 0]},
        "leg_bl": {"rotation": [28, 0, 0]}, "leg_br": {"rotation": [28, 0, 0]},
        "head": {"rotation": [-24, 0, 0]},
        "tail_a": {"rotation": [-10, f"-46 + math.sin({lt}*500)*20", 0]}, "tail_b": {"rotation": [-6, f"math.sin({lt}*500 + 90)*24", 0]},
        "tail_c": {"rotation": [-10, f"46 + math.sin({lt}*500 + 180)*20", 0]},
        "orbs": {"rotation": [0, f"{lt}*900", 0]}}}
    C["animation_controllers"]["controller.animation.sh_veilfox.state"] = controller("veilfox", [("volley", 1), ("pounce", 2), ("storm", 3)])
    save(os.path.join(RP, "animations", "sh_grim.animation.json"), A)
    save(os.path.join(RP, "animation_controllers", "sh_grim.ac.json"), C)
    for key, m in MON.items():
        bp_entity(m)
    rp_entity("quillback", MON["quillback"], ["volley", "roll", "burst", "state"][:3])
    rp_entity("veilfox", MON["veilfox"], ["volley", "pounce", "storm"])
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
