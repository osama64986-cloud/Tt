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


def build_characters():
    import models
    heads = {}
    for ch, forms in models.FORMS.items():
        tdir = os.path.join(RP, "textures", "entity", ch)
        os.makedirs(tdir, exist_ok=True)
        for form in forms:
            geo, img, head = models.export(models.build(ch, form), f"geometry.ab.{ch}_{form}")
            with open(os.path.join(RP, "models", "entity", f"{ch}_{form}.geo.json"), "w") as f:
                json.dump(geo, f, indent=1)
            img.save(os.path.join(tdir, f"{form}.png"))
            x, y, w, h = head
            heads[(ch, form)] = img.crop((x, y, x + w, y + h))
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
    return {
        "format_version": "1.21.60",
        "minecraft:entity": {
            "description": {
                "identifier": f"ab:{name}",
                "is_spawnable": True,
                "is_summonable": True,
                "properties": {
                    "ab:form": {"type": "int", "range": [0, n - 1], "default": 0, "client_sync": True},
                    "ab:pose": {"type": "int", "range": [0, 12], "default": 0, "client_sync": True},
                },
            },
            "component_groups": groups,
            "components": {
                "minecraft:type_family": {"family": ["anime_fighter", f"ab_{name}", "mob"]},
                "minecraft:health": {"value": cfg["hp"], "max": cfg["hp"]},
                "minecraft:scale": {"value": cfg.get("scale", 1.0)},
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


def client_entity(name, cfg):
    textures = {t: f"textures/entity/{name}/{t}" for t in dict.fromkeys(cfg["tex"])}
    geometry = {g: f"geometry.ab.{name}_{g}" for g in dict.fromkeys(cfg["geo"])}
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
                    "attack": "animation.ab.attack",
                    "pose_beam": "animation.ab.pose_beam",
                    "pose_cup": "animation.ab.pose_cup",
                    "pose_raise": "animation.ab.pose_raise",
                    "pose_point": "animation.ab.pose_point",
                    "jab_r": "animation.ab.jab_r", "jab_l": "animation.ab.jab_l", "kick": "animation.ab.kick",
                    "round": "animation.ab.round", "upper": "animation.ab.upper", "knee": "animation.ab.knee",
                    "rush": "animation.ab.rush", "elbow": "animation.ab.elbow",
                },
                "scripts": {"animate": [
                    "look", "move", "idle",
                    {"attack": "variable.attack_time > 0.0"},
                    {"pose_beam": "query.property('ab:pose') == 1"},
                    {"pose_cup": "query.property('ab:pose') == 2"},
                    {"pose_raise": "query.property('ab:pose') == 3"},
                    {"pose_point": "query.property('ab:pose') == 4"},
                ] + [{k: f"query.property('ab:pose') == {i}"} for i, k in
                     enumerate(["jab_r", "jab_l", "kick", "round", "upper", "knee", "rush", "elbow"], start=5)]},
                "render_controllers": [f"controller.render.ab.{name}"],
                "spawn_egg": {"base_color": cfg["egg"][0], "overlay_color": cfg["egg"][1]},
            }
        },
    }


def render_controllers():
    out = {"format_version": "1.10.0", "render_controllers": {}}
    for name, cfg in FIGHTERS.items():
        out["render_controllers"][f"controller.render.ab.{name}"] = {
            "arrays": {
                "textures": {"Array.skins": [f"Texture.{t}" for t in cfg["tex"]]},
                "geometries": {"Array.geos": [f"Geometry.{g}" for g in cfg["geo"]]},
            },
            "geometry": "Array.geos[query.property('ab:form')]",
            "materials": [{"*": "Material.default"}],
            "textures": ["Array.skins[query.property('ab:form')]"],
        }
    return out


def build_entities():
    for name, cfg in FIGHTERS.items():
        with open(os.path.join(BP, "entities", f"{name}.json"), "w") as f:
            json.dump(behavior_entity(name, cfg), f, indent=1)
        with open(os.path.join(RP, "entity", f"{name}.entity.json"), "w") as f:
            json.dump(client_entity(name, cfg), f, indent=1)
    with open(os.path.join(RP, "render_controllers", "ab.render_controllers.json"), "w") as f:
        json.dump(render_controllers(), f, indent=1)


if __name__ == "__main__":
    build_entities()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    HEADS.update(build_characters())
    build_icons()
    validate_json()
    print("built", build_zip())
