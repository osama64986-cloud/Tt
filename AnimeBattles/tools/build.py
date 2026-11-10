#!/usr/bin/env python3
"""Anime Battles add-on builder.

Generates the cube models (geometry), pixel textures, item icons, particle
texture and pack icons, then zips BP + RP into dist/AnimeBattles.mcaddon.

Run:  python3 tools/build.py
"""
import json
import os
import random
import sys
import zipfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "RP")
BP = os.path.join(ROOT, "BP")
DIST = os.path.join(ROOT, "dist")

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


EXPRS = [None, "shout", "hurt", "blink"]
EXPR_MOLANG = ("(query.property('ab:expr') > 0 ? query.property('ab:expr') : "
               "(math.mod(query.life_time + query.property('ab:form') * 0.37, 3.7) < 0.13 ? 3 : 0))")


def build_characters():
    import models
    heads = {}
    for ch, forms in models.FORMS.items():
        tdir = os.path.join(RP, "textures", "entity", ch)
        os.makedirs(tdir, exist_ok=True)
        for form in forms:
            for expr in EXPRS:  # same model, four faces: normal, shout, pain, blink
                models.EXPR = expr
                geo, img, head = models.export(models.build(ch, form), f"geometry.ab.{ch}_{form}")
                if expr is None:
                    with open(os.path.join(RP, "models", "entity", f"{ch}_{form}.geo.json"), "w") as f:
                        json.dump(geo, f, indent=1)
                    img.save(os.path.join(tdir, f"{form}.png"))
                    x, y, w, h = head
                    heads[(ch, form)] = img.crop((x, y, x + w, y + h))
                else:
                    img.save(os.path.join(tdir, f"{form}_{expr}.png"))
            models.EXPR = None
    return heads


# ---------------------------------------------------------------- icons
def stick_icon(path, low, high, tip, glow):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for i in range(12):
        x, y = 2 + i, 13 - i
        col = low if i < 6 else high
        px[x, y] = col + (255,)
        px[x + 1, y] = shade(col, 0.7) + (255,)
        if 0 < i < 11 and i % 3 == 0:
            px[x, y - 1] = shade(col, 1.25) + (255,)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            x, y = 13 + dx, 2 + dy
            px[x, y] = (glow if (dx or dy) else tip) + (255,)
    img.save(path)


HEADS = {}


def build_icons():
    idir = os.path.join(RP, "textures", "items")
    stick_icon(os.path.join(idir, "kill_stick.png"), (40, 20, 50), (70, 10, 20), (255, 255, 255), (230, 20, 30))
    stick_icon(os.path.join(idir, "team_stick.png"), (40, 80, 230), (225, 40, 40), (255, 255, 255), (250, 210, 80))

    orb = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = orb.load()
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5 / 7.5
            a = max(0.0, 1.0 - d) ** 1.4
            px[x, y] = (255, 255, 255, int(255 * a))
    orb.save(os.path.join(RP, "textures", "particle", "ab_orb.png"))

    # pack icon: Goku / Vegeta / Gojo faces side by side
    icon = Image.new("RGBA", (96, 96), (18, 18, 30, 255))
    for x in range(96):
        for y in range(96):
            icon.putpixel((x, y), (230 - y, 40, 60, 255) if x < 48 else (40, 70 + y // 2, 230, 255))
    for (ch, form), ox in ((("goku", "ssj"), 2), (("vegeta", "ssb"), 34), (("gojo", "eyes"), 66)):
        face = HEADS[(ch, form)].resize((28, 28), Image.NEAREST)
        icon.paste(face, (ox, 34), face)
    icon = icon.resize((128, 128), Image.NEAREST)
    icon.save(os.path.join(RP, "pack_icon.png"))
    icon.save(os.path.join(BP, "pack_icon.png"))


def build_zip():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "AnimeBattles.mcaddon")
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for pack, name in ((BP, "AnimeBattles_BP"), (RP, "AnimeBattles_RP")):
            for base, _, files in os.walk(pack):
                for fn in sorted(files):
                    full = os.path.join(base, fn)
                    z.write(full, os.path.join(name, os.path.relpath(full, pack)))
    return out


def validate_json():
    bad = []
    for pack in (BP, RP):
        for base, _, files in os.walk(pack):
            for fn in files:
                if fn.endswith(".json"):
                    p = os.path.join(base, fn)
                    try:
                        with open(p) as f:
                            json.load(f)
                    except Exception as e:  # noqa: BLE001
                        bad.append(f"{p}: {e}")
    if bad:
        raise SystemExit("Invalid JSON:\n" + "\n".join(bad))


# ---------------------------------------------------------------- entities
# name, max HP, per-form (melee damage, speed), form keys (texture, geometry),
# spawn egg colours. Numbers follow the agreed power order: Goku > Vegeta > Gojo.
FIGHTERS = {
    "goku": {
        "hp": 1000,
        "forms": [(14, 0.33), (20, 0.36), (27, 0.38), (40, 0.42), (55, 0.46)],
        "tex": ["base", "ssj", "ssj3", "ssb", "ui"],
        "geo": ["base", "ssj", "ssj3", "ssb", "ui"],
        "egg": ("#f6801a", "#223aaa"),
    },
    "vegeta": {
        "scale": 0.94,  # canon: noticeably shorter than Goku
        "hp": 950,
        "forms": [(13, 0.33), (19, 0.36), (37, 0.41), (50, 0.43)],
        "tex": ["base", "ssj", "ssb", "ue"],
        "geo": ["base", "ssj", "ssb", "ue"],
        "egg": ("#223496", "#eeeee4"),
    },
    "gojo": {
        "hp": 600,
        "forms": [(10, 0.32), (13, 0.34)],
        "tex": ["blindfold", "eyes"],
        "geo": ["blindfold", "eyes"],
        "egg": ("#1a1d2c", "#f4f4fa"),
        "scale": 1.06,
    },
}

FIGHTERS.update({
    "yuji": {"hp": 300, "forms": [(8, 0.35)], "tex": ["base"], "geo": ["base"], "egg": ("#1e2238", "#ee9696")},
    "yuji_final": {"hp": 700, "forms": [(20, 0.39)], "tex": ["base"], "geo": ["base"], "egg": ("#1e2238", "#c41e28")},
    "sukuna": {"hp": 650, "forms": [(18, 0.37), (24, 0.39), (30, 0.4)], "tex": ["yuji", "megumi", "heian"], "geo": ["yuji", "megumi", "heian"],
               "egg": ("#10080c", "#e28c96"), "form_scale": [1.0, 1.0, 1.15]},
    "luffy": {"hp": 950, "forms": [(10, 0.34), (16, 0.42), (22, 0.36), (42, 0.4), (40, 0.44), (36, 0.3), (58, 0.42)],
              "tex": ["base", "g2", "g3", "g4b", "g4s", "g4t", "g5"], "geo": ["base", "g2", "g3", "g4b", "g4s", "g4t", "g5"],
              "egg": ("#ce2226", "#eece68"), "gigant": True},
})

FIGHTERS.update({
    "zoro": {"hp": 700, "forms": [(22, 0.37), (34, 0.39)], "tex": ["base", "king"], "geo": ["base", "king"], "egg": ("#3a5c40", "#78b05c"),
             "scale": 1.03},
    "frieza": {"hp": 900, "forms": [(26, 0.37), (44, 0.42)], "tex": ["final", "golden"], "geo": ["final", "golden"],
               "egg": ("#eeeef6", "#7e40be"), "scale": 0.92},
})

TEAM_FILTER = {
    "any_of": [
        {"all_of": [{"test": "has_tag", "subject": "self", "value": "ab_red"},
                    {"test": "has_tag", "subject": "other", "value": "ab_blue"}]},
        {"all_of": [{"test": "has_tag", "subject": "self", "value": "ab_blue"},
                    {"test": "has_tag", "subject": "other", "value": "ab_red"}]},
    ]
}


def behavior_entity(name, cfg):
    n = len(cfg["forms"])
    groups = {
        "ab:combat": {
            "minecraft:behavior.nearest_attackable_target": {
                "priority": 1, "must_see": False, "reselect_targets": True,
                "within_radius": 48, "scan_interval": 10,
                "entity_types": [{"filters": TEAM_FILTER, "max_dist": 48}],
            },
            "minecraft:behavior.melee_attack": {
                "priority": 2, "speed_multiplier": 1.35, "track_target": True, "reach_multiplier": 1.6,
            },
        }
    }
    events = {
        "minecraft:entity_spawned": {"add": {"component_groups": ["ab:form_0"]}},
        "ab:enter_combat": {"add": {"component_groups": ["ab:combat"]}},
        "ab:leave_combat": {"remove": {"component_groups": ["ab:combat"]}},
    }
    all_forms = [f"ab:form_{i}" for i in range(n)]
    for i, (dmg, speed) in enumerate(cfg["forms"]):
        groups[f"ab:form_{i}"] = {
            "minecraft:attack": {"damage": dmg},
            "minecraft:movement": {"value": speed},
        }
        events[f"ab:form_{i}"] = {"sequence": [
            {"remove": {"component_groups": all_forms}},
            {"add": {"component_groups": [f"ab:form_{i}"]}},
            {"set_property": {"ab:form": i}},
        ]}
    comps_scale = {"minecraft:scale": {"value": cfg.get("scale", 1.0)}}
    if cfg.get("form_scale"):  # size changes with the form (Heian Sukuna towers over Yuji's body)
        for i, sc in enumerate(cfg["form_scale"]):
            groups[f"ab:form_{i}"]["minecraft:scale"] = {"value": sc}
        comps_scale = {}
    if cfg.get("gigant"):
        groups["ab:normal_size"] = {"minecraft:scale": {"value": 1.0}}
        groups["ab:gigant"] = {"minecraft:scale": {"value": 2.4}}
        events["minecraft:entity_spawned"] = {"add": {"component_groups": ["ab:form_0", "ab:normal_size"]}}
        events["ab:gigant_on"] = {"sequence": [{"remove": {"component_groups": ["ab:normal_size"]}}, {"add": {"component_groups": ["ab:gigant"]}}]}
        events["ab:gigant_off"] = {"sequence": [{"remove": {"component_groups": ["ab:gigant"]}}, {"add": {"component_groups": ["ab:normal_size"]}}]}
        comps_scale = {}
    return {
        "format_version": "1.21.60",
        "minecraft:entity": {
            "description": {
                "identifier": f"ab:{name}",
                "is_spawnable": True,
                "is_summonable": True,
                "properties": {
                    "ab:form": {"type": "int", "range": [0, n - 1], "default": 0, "client_sync": True},
                    "ab:pose": {"type": "int", "range": [0, 32], "default": 0, "client_sync": True},
                    "ab:expr": {"type": "int", "range": [0, 3], "default": 0, "client_sync": True},
                    "ab:stance": {"type": "bool", "default": False, "client_sync": True},
                },
            },
            "component_groups": groups,
            "components": {
                "minecraft:type_family": {"family": ["anime_fighter", f"ab_{name}", "mob"]},
                "minecraft:health": {"value": cfg["hp"], "max": cfg["hp"]},
                **comps_scale,
                "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                "minecraft:physics": {},
                "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
                "minecraft:persistent": {},
                "minecraft:nameable": {"always_show": True, "allow_name_tag_renaming": False},
                "minecraft:knockback_resistance": {"value": 0.75},
                "minecraft:follow_range": {"value": 48, "max": 64},
                "minecraft:movement.basic": {},
                "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_damage_blocks": True, "can_open_doors": True},
                "minecraft:jump.static": {},
                "minecraft:can_climb": {},
                "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
                "minecraft:damage_sensor": {"triggers": [
                    {"cause": "fall", "deals_damage": "no"},
                ]},
                "minecraft:behavior.float": {"priority": 0},
                "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.8},
                "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8},
                "minecraft:behavior.random_look_around": {"priority": 8},
            },
            "events": events,
        },
    }


EXTRA_POSES = ["pistol", "gatling", "bazooka", "giant_fist", "whip", "giant_up", "slash", "fuga", "handsign", "powerup", "finger_up", "spin", "two_fingers", "void_sign", "arms_wide", "slash_l", "dodge", "pump", "cross", "tie_bandana"]  # poses 13..32


def extra_animations():
    st = "math.sin(query.life_time * 2400.0)"
    A = {
        "pistol": {"rightArm": {"rotation": [-90, 0, 0], "scale": [1, 7, 1]}, "leftArm": {"rotation": [-30, 0, 20]}, "body": {"rotation": [0, -20, 0]}},
        "gatling": {"rightArm": {"rotation": [f"-90 + {st} * 12", f"{st} * 25", 0], "scale": [1, f"4.5 + {st} * 1.5", 1]},
                    "leftArm": {"rotation": [f"-90 - {st} * 12", f"-{st} * 25", 0], "scale": [1, f"4.5 - {st} * 1.5", 1]}},
        "bazooka": {"rightArm": {"rotation": [-90, -12, 0], "scale": [1, 5, 1]}, "leftArm": {"rotation": [-90, 12, 0], "scale": [1, 5, 1]}},
        "giant_fist": {"rightArm": {"rotation": [-90, 0, 0], "scale": [4.2, 4.2, 4.2]}, "body": {"rotation": [0, -25, 0]}},
        "whip": {"rightLeg": {"rotation": [-80, 0, 70], "scale": [1, 6, 1]}, "body": {"rotation": [0, -30, 0]}},
        "giant_up": {"rightArm": {"rotation": [-175, 0, 0], "scale": [6, 6, 6]}, "leftArm": {"rotation": [-40, 0, 25]}},
        "slash": {"rightArm": {"rotation": [-85, 65, 0]}, "leftArm": {"rotation": [-20, 0, 25]}, "body": {"rotation": [0, -35, 0]}},
        "fuga": {"leftArm": {"rotation": [-90, 0, 0]}, "rightArm": {"rotation": [-90, -55, 0]}, "body": {"rotation": [0, 30, 0]}},
        "handsign": {"rightArm": {"rotation": [-75, -35, 0]}, "leftArm": {"rotation": [-75, 35, 0]}},
        # fighting stance while in a team: fists up, lead hand forward, light bounce on the toes
        "stance": {"rightArm": {"rotation": ["-42 + math.sin(query.life_time * 400.0) * 3", -30, -6]},
                   "leftArm": {"rotation": ["-74 + math.sin(query.life_time * 400.0 + 60) * 3", 8, 0]},
                   "body": {"rotation": [3, 22, 0]},
                   "rightLeg": {"rotation": [10, 0, 4]}, "leftLeg": {"rotation": [-10, 0, -4]}},
        # recoil while the pain face is showing
        "flinch": {"body": {"rotation": [-10, 0, 0]}, "head": {"rotation": [-14, 0, 6]},
                   "rightArm": {"rotation": [-20, 0, 18]}, "leftArm": {"rotation": [-20, 0, -18]},
                   "rightLeg": {"rotation": [6, 0, 0]}, "leftLeg": {"rotation": [-4, 0, 0]}},
        # transformation power-up: crouched, arms driven down and out, fists clenched, head thrown back, trembling
        "powerup": {"root": {"position": ["math.sin(query.life_time * 3100.0) * 0.25", -0.8, "math.cos(query.life_time * 2700.0) * 0.25"]},
                    "body": {"rotation": [-10, 0, 0]}, "head": {"rotation": [-24, 0, 0]},
                    "rightArm": {"rotation": [-12, 0, 28]}, "leftArm": {"rotation": [-12, 0, -28]},
                    "rightLeg": {"rotation": [-8, 0, 10]}, "leftLeg": {"rotation": [-8, 0, -10]}},
        # Frieza's Death Ball: one arm straight up, one finger raised
        "finger_up": {"rightArm": {"rotation": [-178, 0, -6]}, "leftArm": {"rotation": [-10, 0, 12]}, "head": {"rotation": [-12, 0, 0]}},
        # Zoro's Tatsumaki: the whole body whirls with both swords held out
        "spin": {"root": {"rotation": [0, "query.life_time * 1800.0", 0]},
                 "rightArm": {"rotation": [-80, 0, 70]}, "leftArm": {"rotation": [-80, 0, -70]}},
        # Goku's Instant Transmission: index and middle finger to the forehead
        "two_fingers": {"rightArm": {"rotation": [-150, -38, 0]}, "leftArm": {"rotation": [-8, 0, 8]}, "head": {"rotation": [6, 0, 0]}},
        # Gojo's Unlimited Void: one hand raised before the face, fingers crossed
        "void_sign": {"rightArm": {"rotation": [-120, -12, 0]}, "leftArm": {"rotation": [-8, 0, 10]}, "head": {"rotation": [6, 0, 0]}},
        # Vegeta's Final Flash charge: both arms thrown wide before the palms come together
        "arms_wide": {"rightArm": {"rotation": [-8, 0, 88]}, "leftArm": {"rotation": [-8, 0, -88]}, "body": {"rotation": [-6, 0, 0]},
                      "rightLeg": {"rotation": [-6, 0, 8]}, "leftLeg": {"rotation": [-6, 0, -8]}},
        # Luffy's Gear 2: bent low, hands toward the ground, legs pumping the blood
        "pump": {"root": {"position": [0, -1.6, 0]}, "body": {"rotation": [34, 0, 0]}, "head": {"rotation": [-26, 0, 0]},
                 "rightArm": {"rotation": [-38, 0, 10]}, "leftArm": {"rotation": [-38, 0, -10]},
                 "rightLeg": {"rotation": ["math.sin(query.life_time * 1400.0) * 14", 0, 12]},
                 "leftLeg": {"rotation": ["-math.sin(query.life_time * 1400.0) * 14", 0, -12]}},
        # victory "hmph": arms crossed (Vegeta, Frieza)
        "cross": {"rightArm": {"rotation": [-60, -50, 0]}, "leftArm": {"rotation": [-52, 50, 0]}, "head": {"rotation": [-8, 0, 6]}},
        # Zoro getting serious: both hands up behind his head, tying the bandana
        "tie_bandana": {"rightArm": {"rotation": [-165, -32, 0]}, "leftArm": {"rotation": [-165, 32, 0]}, "head": {"rotation": [10, 0, 0]}},
        # signature idles out of combat
        "arms_crossed": {"rightArm": {"rotation": [-60, -50, 0]}, "leftArm": {"rotation": [-52, 50, 0]}, "head": {"rotation": [-4, 0, 0]}},
        "cool_idle": {"head": {"rotation": [-6, 0, 10]}, "rightArm": {"rotation": [6, 0, 4]}, "leftArm": {"rotation": [6, 0, -4]}},
        "hover": {"root": {"position": [0, "2.2 + math.sin(query.life_time * 110.0) * 0.6", 0]},
                   "rightLeg": {"rotation": [6, 0, 0]}, "leftLeg": {"rotation": [-4, 0, 0]}},
        # Gear 5 toon wobble: squash and stretch like rubber
        "toon": {"body": {"scale": ["1 + math.sin(query.life_time * 300.0) * 0.04", "1 - math.sin(query.life_time * 300.0) * 0.05", 1]},
                 "head": {"scale": ["1 - math.sin(query.life_time * 300.0) * 0.03", "1 + math.sin(query.life_time * 300.0) * 0.04", 1]}},
        "tail_sway": {"tail": {"rotation": ["math.sin(query.life_time * 120.0) * 6", "math.sin(query.life_time * 80.0) * 18", 0]}},
    }
    additive = {"stance", "flinch", "arms_crossed", "cool_idle", "tail_sway", "hover", "toon"}  # layered on walk/look, never replacing them
    out = {f"animation.ab.{k}": {"loop": True, "override_previous_animation": k not in additive, "bones": v} for k, v in A.items()}
    # strikes with motion: chamber -> snap out (slight overshoot) -> hold, replayed every time the pose is set
    def strike(bones, length=0.14):
        return {"loop": "hold_on_last_frame", "animation_length": length, "override_previous_animation": True, "bones": bones}
    out["animation.ab.jab_r"] = strike({
        "rightArm": {"rotation": {"0.0": [-30, 0, 0], "0.06": [-102, 0, 0], "0.12": [-94, 0, 0]}},
        "leftArm": {"rotation": {"0.0": [-70, 0, 10], "0.06": [-38, 0, 15]}},
        "body": {"rotation": {"0.0": [0, 14, 0], "0.06": [0, -26, 0], "0.12": [0, -22, 0]}},
        "rightLeg": {"rotation": [-15, 0, 0]}, "leftLeg": {"rotation": [15, 0, 0]}})
    out["animation.ab.jab_l"] = strike({
        "leftArm": {"rotation": {"0.0": [-30, 0, 0], "0.06": [-102, 0, 0], "0.12": [-94, 0, 0]}},
        "rightArm": {"rotation": {"0.0": [-70, 0, -10], "0.06": [-38, 0, -15]}},
        "body": {"rotation": {"0.0": [0, -14, 0], "0.06": [0, 26, 0], "0.12": [0, 22, 0]}},
        "rightLeg": {"rotation": [15, 0, 0]}, "leftLeg": {"rotation": [-15, 0, 0]}})
    out["animation.ab.kick"] = strike({
        "rightLeg": {"rotation": {"0.0": [-25, 0, 0], "0.07": [-102, 0, 0], "0.14": [-92, 0, 0]}},
        "leftLeg": {"rotation": [10, 0, 0]},
        "rightArm": {"rotation": [-30, 0, -25]}, "leftArm": {"rotation": [-30, 0, 25]},
        "body": {"rotation": {"0.0": [0, 0, 0], "0.07": [10, 0, 0]}}}, 0.16)
    out["animation.ab.round"] = strike({
        "rightLeg": {"rotation": {"0.0": [-15, 0, 15], "0.08": [-25, 0, 90], "0.16": [-25, 0, 80]}},
        "leftLeg": {"rotation": [5, 0, -5]},
        "body": {"rotation": {"0.0": [0, 15, 0], "0.08": [0, -42, -10], "0.16": [0, -35, -10]}},
        "rightArm": {"rotation": [-20, 0, 50]}, "leftArm": {"rotation": [-40, 0, -35]}}, 0.18)
    # beam release: from the cupped charge at the hip, thrust both palms forward
    out["animation.ab.pose_beam"] = strike({
        "rightArm": {"rotation": {"0.0": [-55, -30, 0], "0.08": [-96, -8, 0], "0.16": [-90, -6, 0]}},
        "leftArm": {"rotation": {"0.0": [-55, 30, 0], "0.08": [-96, 8, 0], "0.16": [-90, 6, 0]}},
        "body": {"rotation": {"0.0": [0, 20, 0], "0.08": [4, 0, 0]}},
        "rightLeg": {"rotation": [-12, 0, 0]}, "leftLeg": {"rotation": [12, 0, 0]}}, 0.16)
    # sword slash: raised overhead, cut down and across
    out["animation.ab.slash"] = strike({
        "rightArm": {"rotation": {"0.0": [-170, -15, 0], "0.05": [-115, 15, 0], "0.1": [-38, 45, 0], "0.16": [-44, 40, 0]}},
        "leftArm": {"rotation": [-20, 0, 25]},
        "body": {"rotation": {"0.0": [-6, 20, 0], "0.1": [6, -38, 0], "0.16": [4, -35, 0]}}}, 0.16)
    # axe kick (pose 10): leg swung high overhead, then hammered down onto the target
    out["animation.ab.knee"] = strike({
        "rightLeg": {"rotation": {"0.0": [-120, 0, 0], "0.07": [-165, 0, 0], "0.13": [-35, 0, 0], "0.2": [-28, 0, 0]}},
        "leftLeg": {"rotation": [10, 0, 0]},
        "body": {"rotation": {"0.0": [-14, 0, 0], "0.13": [10, 0, 0]}},
        "rightArm": {"rotation": [-30, 0, -35]}, "leftArm": {"rotation": [-30, 0, 35]}}, 0.2)
    # left roundhouse (pose 12), mirror of the right one
    out["animation.ab.elbow"] = strike({
        "leftLeg": {"rotation": {"0.0": [-15, 0, -15], "0.08": [-25, 0, -90], "0.16": [-25, 0, -80]}},
        "rightLeg": {"rotation": [5, 0, 5]},
        "body": {"rotation": {"0.0": [0, -15, 0], "0.08": [0, 42, 10], "0.16": [0, 35, 10]}},
        "leftArm": {"rotation": [-20, 0, -50]}, "rightArm": {"rotation": [-40, 0, 35]}}, 0.18)
    # left-hand sword cut (pose 28), mirror of the right slash
    out["animation.ab.slash_l"] = strike({
        "leftArm": {"rotation": {"0.0": [-170, 15, 0], "0.05": [-115, -15, 0], "0.1": [-38, -45, 0], "0.16": [-44, -40, 0]}},
        "rightArm": {"rotation": [-20, 0, -25]},
        "body": {"rotation": {"0.0": [-6, -20, 0], "0.1": [6, 38, 0], "0.16": [4, 35, 0]}}}, 0.16)
    # dodge (pose 29): a sharp sway away from the blow, then back
    out["animation.ab.dodge"] = strike({
        "body": {"rotation": {"0.0": [0, 0, 0], "0.06": [-8, 0, 24], "0.25": [-4, 0, 12]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.06": [-6, 0, 10]}},
        "rightArm": {"rotation": {"0.0": [0, 0, 0], "0.06": [-30, 0, 30]}},
        "leftArm": {"rotation": {"0.0": [0, 0, 0], "0.06": [-40, 0, -10]}},
        "rightLeg": {"rotation": [0, 0, 10]}, "leftLeg": {"rotation": [0, 0, -4]}}, 0.25)
    # Gum-Gum Pistol: the arm stretches far back behind him, then snaps forward
    out["animation.ab.pistol"] = strike({
        "rightArm": {"rotation": {"0.0": [-30, 0, 0], "0.1": [40, 0, 10], "0.18": [-92, 0, 0], "0.3": [-90, 0, 0]},
                     "scale": {"0.0": [1, 1, 1], "0.1": [1, 3.5, 1], "0.18": [1, 7.5, 1], "0.3": [1, 7, 1]}},
        "leftArm": {"rotation": [-30, 0, 20]},
        "body": {"rotation": {"0.0": [0, 10, 0], "0.1": [0, 25, 0], "0.18": [0, -22, 0]}}}, 0.3)
    # Gum-Gum Bazooka: both arms stretch back, then both palms slam forward
    out["animation.ab.bazooka"] = strike({
        "rightArm": {"rotation": {"0.0": [-60, -12, 0], "0.1": [35, -12, 0], "0.18": [-92, -12, 0], "0.3": [-90, -12, 0]},
                     "scale": {"0.0": [1, 1, 1], "0.1": [1, 3, 1], "0.18": [1, 5.5, 1], "0.3": [1, 5, 1]}},
        "leftArm": {"rotation": {"0.0": [-60, 12, 0], "0.1": [35, 12, 0], "0.18": [-92, 12, 0], "0.3": [-90, 12, 0]},
                    "scale": {"0.0": [1, 1, 1], "0.1": [1, 3, 1], "0.18": [1, 5.5, 1], "0.3": [1, 5, 1]}},
        "body": {"rotation": {"0.0": [0, 0, 0], "0.1": [-8, 0, 0], "0.18": [8, 0, 0]}}}, 0.3)
    out["animation.ab.upper"] = strike({
        "rightArm": {"rotation": {"0.0": [-15, 0, -10], "0.08": [-176, 0, -10], "0.16": [-168, 0, -10]}},
        "leftArm": {"rotation": [-30, 0, 20]},
        "body": {"rotation": {"0.0": [8, 10, 0], "0.08": [-14, -15, 0]}},
        "rightLeg": {"rotation": [-20, 0, 0]}, "leftLeg": {"rotation": [20, 0, 0]}}, 0.18)
    out["animation.ab.bounce"] = {"loop": True, "bones": {"root": {"position": [0, "math.abs(math.sin(query.life_time * 240.0)) * 3.0", 0]}}}
    out["animation.ab.arms2"] = {"loop": True, "bones": {
        "rightArm2": {"rotation": ["math.sin(query.life_time * 120.0) * 12.0 - 10.0", 0, 0]},
        "leftArm2": {"rotation": ["-math.sin(query.life_time * 120.0) * 12.0 - 10.0", 0, 0]}}}
    return out


IDLE_COND = "!query.property('ab:stance') && query.property('ab:pose') == 0 && query.modified_move_speed < 0.1 && variable.attack_time <= 0.0"
CHAR_ANIMS = {
    "luffy": [("bounce", "animation.ab.bounce", "query.property('ab:form') == 3"), ("toon", "animation.ab.toon", "query.property('ab:form') == 6")],
    "sukuna": [("arms2", "animation.ab.arms2", "query.property('ab:form') == 2")],
    "frieza": [("tail_sway", "animation.ab.tail_sway", "1.0"), ("hover", "animation.ab.hover", "query.property('ab:pose') != 24"), ("arms_crossed", "animation.ab.arms_crossed", IDLE_COND)],
    "vegeta": [("arms_crossed", "animation.ab.arms_crossed", IDLE_COND)],
    "gojo": [("cool_idle", "animation.ab.cool_idle", IDLE_COND)],
}


def client_entity(name, cfg):
    textures = {}
    for t in dict.fromkeys(cfg["tex"]):
        textures[t] = f"textures/entity/{name}/{t}"
        for ex in EXPRS[1:]:
            textures[f"{t}_{ex}"] = f"textures/entity/{name}/{t}_{ex}"
    geometry = {g: f"geometry.ab.{name}_{g}" for g in dict.fromkeys(cfg["geo"])}
    out = _client_entity(name, cfg, textures, geometry)
    for key, anim, cond in CHAR_ANIMS.get(name, []):
        d = out["minecraft:client_entity"]["description"]
        d["animations"][key] = anim
        d["scripts"]["animate"].append({key: cond})
    return out


def _client_entity(name, cfg, textures, geometry):
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": f"ab:{name}",
                "materials": {"default": "entity_alphatest"},
                "textures": textures,
                "geometry": geometry,
                "animations": {
                    "look": "animation.ab.look_at_target",
                    "move": "animation.ab.move",
                    "idle": "animation.ab.idle",
                    "stance": "animation.ab.stance",
                    "flinch": "animation.ab.flinch",
                    "attack": "animation.ab.attack",
                    "pose_beam": "animation.ab.pose_beam",
                    "pose_cup": "animation.ab.pose_cup",
                    "pose_raise": "animation.ab.pose_raise",
                    "pose_point": "animation.ab.pose_point",
                    "jab_r": "animation.ab.jab_r", "jab_l": "animation.ab.jab_l", "kick": "animation.ab.kick",
                    "round": "animation.ab.round", "upper": "animation.ab.upper", "knee": "animation.ab.knee",
                    "rush": "animation.ab.rush", "elbow": "animation.ab.elbow",
                    **{k: f"animation.ab.{k}" for k in EXTRA_POSES},
                },
                "scripts": {"animate": [
                    "look", "move", "idle",
                    {"attack": "variable.attack_time > 0.0"},
                    {"stance": "query.property('ab:stance') && query.property('ab:pose') == 0 && variable.attack_time <= 0.0"},
                    {"flinch": "query.property('ab:expr') == 2 && query.property('ab:pose') == 0"},
                    {"pose_beam": "query.property('ab:pose') == 1"},
                    {"pose_cup": "query.property('ab:pose') == 2"},
                    {"pose_raise": "query.property('ab:pose') == 3"},
                    {"pose_point": "query.property('ab:pose') == 4"},
                ] + [{k: f"query.property('ab:pose') == {i}"} for i, k in
                     enumerate(["jab_r", "jab_l", "kick", "round", "upper", "knee", "rush", "elbow"] + EXTRA_POSES, start=5)]},
                "render_controllers": [f"controller.render.ab.{name}"],
                "spawn_egg": {"texture": f"ab_egg_{name}", "texture_index": 0},
            }
        },
    }


def render_controllers():
    out = {"format_version": "1.10.0", "render_controllers": {}}
    for name, cfg in FIGHTERS.items():
        out["render_controllers"][f"controller.render.ab.{name}"] = {
            "arrays": {
                "textures": {"Array.skins": [f"Texture.{t}{'_' + ex if ex else ''}" for t in cfg["tex"] for ex in EXPRS]},
                "geometries": {"Array.geos": [f"Geometry.{g}" for g in cfg["geo"]]},
            },
            "geometry": "Array.geos[query.property('ab:form')]",
            "materials": [{"*": "Material.default"}],
            "textures": ["Array.skins[query.property('ab:form') * 4 + " + EXPR_MOLANG + "]"],
        }
    return out


def build_entities():
    an_path = os.path.join(RP, "animations", "ab.animation.json")
    an = json.load(open(an_path))
    an["animations"].update(extra_animations())
    json.dump(an, open(an_path, "w"), indent=1)
    for name, cfg in FIGHTERS.items():
        with open(os.path.join(BP, "entities", f"{name}.json"), "w") as f:
            json.dump(behavior_entity(name, cfg), f, indent=1)
        with open(os.path.join(RP, "entity", f"{name}.entity.json"), "w") as f:
            json.dump(client_entity(name, cfg), f, indent=1)
    with open(os.path.join(RP, "render_controllers", "ab.render_controllers.json"), "w") as f:
        json.dump(render_controllers(), f, indent=1)


# ---------------------------------------------------------------- 3D VFX entity (beams + energy balls)
VFX_COLORS = [  # (core, edge) per colour slot used by the script
    ((255, 255, 255), (80, 180, 255)),   # 0 Kamehameha
    ((255, 240, 255), (190, 80, 255)),   # 1 Galick Gun
    ((255, 255, 235), (255, 220, 60)),   # 2 Final Flash
    ((255, 255, 255), (150, 215, 255)),  # 3 Big Bang
    ((255, 245, 240), (255, 40, 40)),    # 4 Red
    ((240, 250, 255), (40, 110, 255)),   # 5 Blue
    ((255, 240, 255), (170, 50, 255)),   # 6 Hollow Purple
    ((230, 160, 255), (90, 10, 130)),    # 7 Hakai
    ((255, 255, 255), (110, 200, 255)),  # 8 Spirit Bomb
    ((255, 255, 240), (255, 200, 40)),   # 9 gold
    ((255, 255, 255), (220, 230, 255)),  # 10 white/silver
    ((255, 240, 200), (255, 110, 20)),   # 11 fire (Fuga)
    ((255, 200, 200), (170, 0, 20)),     # 12 blood
    ((255, 120, 120), (30, 0, 6)),       # 13 black-red (haki / black flash / cleave)
    ((255, 255, 255), (255, 240, 200)),  # 14 Nika white
    ((255, 220, 255), (210, 60, 200)),   # 15 Frieza death beam (magenta)
    ((240, 255, 240), (120, 200, 120)),  # 16 Zoro sword aura (green)
]


def vfx_textures():
    from PIL import ImageDraw
    d = os.path.join(RP, "textures", "entity", "vfx")
    os.makedirs(d, exist_ok=True)
    for i, (core, edge) in enumerate(VFX_COLORS):
        core = tuple(int(edge[k] + (255 - edge[k]) * 0.5) for k in range(3))  # tinted core, not pure white
        img = Image.new("RGBA", (32, 32))
        px = img.load()
        for y in range(32):
            for x in range(32):
                r = max(abs(x - 15.5), abs(y - 15.5)) / 16.0  # 0 centre .. 1 edge
                t = min(1.0, r ** 1.1)
                c = tuple(int(core[k] + (edge[k] - core[k]) * t) for k in range(3))
                # streaks of brighter energy
                if (x + y * 3) % 11 == 0:
                    c = tuple(min(255, int(v * 1.15) + 20) for v in c)
                px[x, y] = c + (int(255 * (1 - 0.55 * t)),)
        img.save(os.path.join(d, f"vfx_{i}.png"))
    # particle textures: ring (shockwave) and 4-point star (impact flash)
    ring = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    rp = ring.load()
    for y in range(32):
        for x in range(32):
            dd = ((x - 15.5) ** 2 + (y - 15.5) ** 2) ** 0.5
            a = max(0.0, 1 - abs(dd - 13) / 3.0)
            rp[x, y] = (255, 255, 255, int(255 * a))
    ring.save(os.path.join(RP, "textures", "particle", "ab_ring.png"))
    star = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    sp = star.load()
    for y in range(32):
        for x in range(32):
            dx, dy = abs(x - 15.5) / 16, abs(y - 15.5) / 16
            a = max(0.0, 1 - (dx * dy) ** 0.5 * 4 - (dx * dx + dy * dy) * 0.6)
            sp[x, y] = (255, 255, 255, int(255 * min(1, a)))
    star.save(os.path.join(RP, "textures", "particle", "ab_star.png"))


def _face_uv(size=32):
    f = {"uv": [0, 0], "uv_size": [size, size]}
    return {k: dict(f) for k in ("north", "south", "east", "west", "up", "down")}


def _sphere_slices(r, n, yaws, uv):
    """A round ball out of n horizontal slices (each a square prism) copied at several yaw angles."""
    import math as _m
    cubes = []
    h = 2 * r / n
    for i in range(n):
        y0 = -r + i * h
        ym = y0 + h / 2
        w = 2 * _m.sqrt(max(r * r - ym * ym, 0)) * 0.94 + 0.2
        w = round(w, 3)
        for yaw in yaws:
            c = {"origin": [-w / 2, round(y0, 3), -w / 2], "size": [w, round(h, 3), w], "uv": uv}
            if yaw:
                c["rotation"] = [0, yaw, 0]
                c["pivot"] = [0, 0, 0]
            cubes.append(c)
    return cubes


def vfx_geometry():
    uv = _face_uv()
    beam = {
        "description": {"identifier": "geometry.ab.vfx_beam", "texture_width": 32, "texture_height": 32,
                        "visible_bounds_width": 128, "visible_bounds_height": 128, "visible_bounds_offset": [0, 0, 0]},
        "bones": [
            {"name": "root", "pivot": [0, 0, 0]},
            {"name": "shaft", "parent": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-2, -2, -16], "size": [4, 4, 16], "uv": uv},
            ]},
            {"name": "outer_shaft", "parent": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-5, -5, -16], "size": [10, 10, 16], "uv": uv},
                {"origin": [-5, -5, -16], "size": [10, 10, 16], "uv": uv, "rotation": [0, 0, 45], "pivot": [0, 0, 0]},
            ]},
            {"name": "spiral", "parent": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-7.5, -0.75, -16], "size": [1.5, 1.5, 16], "uv": uv},
                {"origin": [6, -0.75, -16], "size": [1.5, 1.5, 16], "uv": uv},
                {"origin": [-0.75, 6, -16], "size": [1.5, 1.5, 16], "uv": uv},
                {"origin": [-0.75, -7.5, -16], "size": [1.5, 1.5, 16], "uv": uv},
            ]},
            {"name": "muzzle", "parent": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-6, -6, -6], "size": [12, 12, 12], "uv": uv},
                {"origin": [-6, -6, -6], "size": [12, 12, 12], "uv": uv, "rotation": [45, 45, 0], "pivot": [0, 0, 0]},
            ]},
        ],
    }
    orb = {
        "description": {"identifier": "geometry.ab.vfx_orb", "texture_width": 32, "texture_height": 32,
                        "visible_bounds_width": 64, "visible_bounds_height": 64, "visible_bounds_offset": [0, 0, 0]},
        "bones": [
            {"name": "root", "pivot": [0, 0, 0]},
            {"name": "core", "parent": "root", "pivot": [0, 0, 0], "cubes": _sphere_slices(4, 8, (0, 30, 60), uv)},
            {"name": "outer_shell", "parent": "root", "pivot": [0, 0, 0], "cubes": _sphere_slices(8, 6, (0, 45), uv)},
        ],
    }
    slash = {
        "description": {"identifier": "geometry.ab.vfx_slash", "texture_width": 32, "texture_height": 32,
                        "visible_bounds_width": 64, "visible_bounds_height": 64, "visible_bounds_offset": [0, 0, 0]},
        "bones": [
            {"name": "root", "pivot": [0, 0, 0]},
            {"name": "blade", "parent": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-10, -0.3, -1.5], "size": [20, 0.6, 3], "uv": uv},
                {"origin": [-16, -0.25, -1], "size": [8, 0.5, 2], "uv": uv, "rotation": [0, -18, 0], "pivot": [-9, 0, 0]},
                {"origin": [8, -0.25, -1], "size": [8, 0.5, 2], "uv": uv, "rotation": [0, 18, 0], "pivot": [9, 0, 0]},
            ]},
            {"name": "outer_glow", "parent": "root", "pivot": [0, 0, 0], "cubes": [
                {"origin": [-12, -0.6, -2.5], "size": [24, 1.2, 5], "uv": uv},
            ]},
        ],
    }
    return {"format_version": "1.12.0", "minecraft:geometry": [beam, orb, slash]}


def build_vfx():
    vfx_textures()
    with open(os.path.join(RP, "models", "entity", "vfx.geo.json"), "w") as f:
        json.dump(vfx_geometry(), f, indent=1)
    bp = {
        "format_version": "1.21.60",
        "minecraft:entity": {
            "description": {
                "identifier": "ab:vfx", "is_spawnable": False, "is_summonable": True,
                "properties": {
                    "ab:kind": {"type": "int", "range": [0, 2], "default": 0, "client_sync": True},
                    "ab:color": {"type": "int", "range": [0, len(VFX_COLORS) - 1], "default": 0, "client_sync": True},
                    "ab:len": {"type": "float", "range": [0, 80], "default": 0, "client_sync": True},
                    "ab:size": {"type": "float", "range": [0, 40], "default": 1, "client_sync": True},
                    "ab:pitch": {"type": "float", "range": [-90, 90], "default": 0, "client_sync": True},
                },
            },
            "components": {
                "minecraft:type_family": {"family": ["ab_vfx", "inanimate"]},
                "minecraft:collision_box": {"width": 0.01, "height": 0.01},
                "minecraft:physics": {"has_gravity": False, "has_collision": False},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]},
                "minecraft:health": {"value": 1, "max": 1},
                "minecraft:knockback_resistance": {"value": 1},
                "minecraft:fire_immune": True,
            },
        },
    }
    with open(os.path.join(BP, "entities", "vfx.json"), "w") as f:
        json.dump(bp, f, indent=1)
    client = {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": "ab:vfx",
                "materials": {"glow": "entity_alphablend", "blend": "entity_alphablend"},
                "textures": {f"c{i}": f"textures/entity/vfx/vfx_{i}" for i in range(len(VFX_COLORS))},
                "geometry": {"beam": "geometry.ab.vfx_beam", "orb": "geometry.ab.vfx_orb", "slash": "geometry.ab.vfx_slash"},
                "animations": {"beam": "animation.ab.vfx_beam", "orb": "animation.ab.vfx_orb", "slash": "animation.ab.vfx_slash"},
                "scripts": {"animate": [{"beam": "query.property('ab:kind') == 0"}, {"orb": "query.property('ab:kind') == 1"},
                                        {"slash": "query.property('ab:kind') == 2"}]},
                "render_controllers": ["controller.render.ab.vfx"],
            }
        },
    }
    with open(os.path.join(RP, "entity", "vfx.entity.json"), "w") as f:
        json.dump(client, f, indent=1)
    rc_path = os.path.join(RP, "render_controllers", "ab.render_controllers.json")
    rc = json.load(open(rc_path))
    rc["render_controllers"]["controller.render.ab.vfx"] = {
        "arrays": {
            "textures": {"Array.c": [f"Texture.c{i}" for i in range(len(VFX_COLORS))]},
            "geometries": {"Array.g": ["Geometry.beam", "Geometry.orb", "Geometry.slash"]},
        },
        "geometry": "Array.g[query.property('ab:kind')]",
        "materials": [{"*": "Material.glow"}, {"outer*": "Material.blend"}],
        "textures": ["Array.c[query.property('ab:color')]"],
        "ignore_lighting": True,
    }
    json.dump(rc, open(rc_path, "w"), indent=1)
    an_path = os.path.join(RP, "animations", "ab.animation.json")
    an = json.load(open(an_path))
    L, W = "query.property('ab:len')", "query.property('ab:size')"
    an["animations"]["animation.ab.vfx_beam"] = {"loop": True, "bones": {
        "root": {"rotation": ["query.property('ab:pitch')", 0, 0]},
        "shaft": {"scale": [W, W, L]},
        "outer_shaft": {"scale": [W, W, L], "rotation": [0, 0, "query.life_time * 360.0"]},
        "spiral": {"scale": [W, W, L], "rotation": [0, 0, "-query.life_time * 900.0"]},
        "muzzle": {"scale": [f"{W} * (1.0 + math.sin(query.life_time * 1800.0) * 0.12)"] * 3,
                   "rotation": [0, "query.life_time * 500.0", 0]},
    }}
    an["animations"]["animation.ab.vfx_slash"] = {"loop": True, "bones": {
        "root": {"rotation": ["query.property('ab:pitch')", 0, "query.property('ab:len') * 4.5"]},
        "blade": {"scale": [W, W, W]},
        "outer_glow": {"scale": [f"{W} * (1.0 + math.sin(query.life_time * 2000.0) * 0.1)", W, W]},
    }}
    an["animations"]["animation.ab.vfx_orb"] = {"loop": True, "bones": {
        "core": {"scale": [f"{W} * 0.9"] * 3, "rotation": ["query.life_time * 300.0", "query.life_time * 420.0", 0]},
        "outer_shell": {"scale": [f"{W} * (1.0 + math.sin(query.life_time * 1500.0) * 0.06)"] * 3,
                        "rotation": [0, "-query.life_time * 260.0", "query.life_time * 180.0"]},
    }}
    json.dump(an, open(an_path, "w"), indent=1)


def build_egg_icons():
    """Spawn eggs show the fighter's own face (32x32) in a coloured frame."""
    import models
    data = {"ab_kill_stick": {"textures": "textures/items/kill_stick"},
            "ab_team_stick": {"textures": "textures/items/team_stick"}}
    idir = os.path.join(RP, "textures", "items")
    for ch, forms in models.FORMS.items():
        face = HEADS[(ch, "eyes" if ch == "gojo" else forms[0])].convert("RGBA").resize((26, 26), Image.NEAREST)
        base = tuple(int(FIGHTERS[ch]["egg"][0][i:i + 2], 16) for i in (1, 3, 5))
        edge = tuple(int(FIGHTERS[ch]["egg"][1][i:i + 2], 16) for i in (1, 3, 5))
        icon = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                dx, dy = abs(x - 15.5), abs(y - 15.5)
                if max(dx, dy) <= 15.5 and (dx + dy) <= 27:
                    icon.putpixel((x, y), (shade(edge, 0.55) if max(dx, dy) > 14.5 or dx + dy > 26 else base) + (255,))
        icon.paste(face, (3, 3), face)
        icon.save(os.path.join(idir, f"egg_{ch}.png"))
        data[f"ab_egg_{ch}"] = {"textures": f"textures/items/egg_{ch}"}
    with open(os.path.join(RP, "textures", "item_texture.json"), "w") as f:
        json.dump({"resource_pack_name": "anime_battles", "texture_name": "atlas.items", "texture_data": data}, f, indent=1)


if __name__ == "__main__":
    build_entities()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    HEADS.update(build_characters())
    build_vfx()
    build_icons()
    build_egg_icons()
    validate_json()
    print("built", build_zip())
