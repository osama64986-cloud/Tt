"""Shoulder view for the normal third-person (back) camera - resource pack only.

How it works
  The game's own third-person camera is left exactly as it is: it turns with
  the player at the same instant and sits right behind the player's eyes, so
  the middle of the screen is exactly where hits and clicks land.  Only on the
  local player's own screen, and only in third-person back view, the character
  model is drawn shifted to one side, so the middle of the screen is free.
  Other players see you normally; first person and the inventory doll are
  untouched.  A small crosshair particle sits on the camera's centre line.

  Settings live in the game's own pack settings (Settings > Global Resources >
  Nabd > gear icon): on/off, side, distance, crosshair on/off.

Files written
  pack_src/entity/player.entity.json   vanilla player client entity + our 2 animations
                                       + the crosshair particle (generated from
                                       Mojang's public sample so it follows game updates)
  pack_src/animations/nabd_shoulder.animation.json
  pack_src/animation_controllers/nabd_shoulder.animation_controllers.json
  pack_src/particles/nabd_tp_cross.particle.json, textures/particle/nabd_cross.png
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "pack_src")
VANILLA = os.path.join(os.path.dirname(ROOT), "mojang", "bedrock-samples", "resource_pack", "entity", "player.entity.json")

PX_PER_BLOCK = 16.0 / 0.9375          # player model scale is 0.9375

# 1 when the shoulder view applies: our own player, third person, not the inventory doll
ACTIVE = ("(query.is_local_player && !query.is_first_person && !query.is_in_ui && !variable.map_face_icon"
          " && query.is_pack_setting_enabled('nabd:shoulder')) ? 1.0 : 0.0")
SIDE = "(query.is_pack_setting_selected('nabd:shoulder_side', 'right') ? -1.0 : 1.0)"

PRE = [
    f"variable.nabd_tp = {ACTIVE};",
    # smooth in/out so switching views does not snap
    "variable.nabd_tp_k = query.life_time < 0.05 ? variable.nabd_tp : variable.nabd_tp_k + (variable.nabd_tp - variable.nabd_tp_k) * 0.35;",
    f"variable.nabd_tp_s = variable.nabd_tp_k * {SIDE} * query.get_pack_setting('nabd:shoulder_shift') * {PX_PER_BLOCK / 10:.4f};",
    "variable.nabd_tp_cross = (variable.nabd_tp > 0.5 && query.is_pack_setting_enabled('nabd:crosshair')) ? 1.0 : 0.0;",
]


def animation():
    # The head turns relative to the body by query.target_y_rotation (that is what
    # the game's own look-at animation uses), and the camera follows the head.
    # The side shift is applied along the head's side axis, written in body space.
    a = "query.target_y_rotation"
    j = {
        "format_version": "1.8.0",
        "animations": {
            "animation.nabd.shoulder": {
                "loop": True,
                "bones": {
                    "root": {
                        "position": [f"-variable.nabd_tp_s * math.cos({a})", 0.0, f"variable.nabd_tp_s * math.sin({a})"]
                    }
                },
            }
        },
    }
    os.makedirs(os.path.join(RP, "animations"), exist_ok=True)
    json.dump(j, open(os.path.join(RP, "animations", "nabd_shoulder.animation.json"), "w"), indent=2)


def controller():
    def show(eye):
        return {"particle_effects": [{"effect": "nabd_cross", "pre_effect_script": f"variable.eye = {eye};"}],
                "transitions": [{"off": "variable.nabd_tp_cross < 0.5"}]}
    standing = "!query.is_sneaking && !query.is_swimming && !query.is_crawling && !query.is_gliding && !query.is_sleeping"
    low = "(query.is_swimming || query.is_crawling || query.is_gliding)"
    j = {
        "format_version": "1.10.0",
        "animation_controllers": {
            "controller.animation.nabd.cross": {
                "initial_state": "off",
                "states": {
                    "off": {"transitions": [
                        {"stand": f"variable.nabd_tp_cross > 0.5 && {standing}"},
                        {"sneak": "variable.nabd_tp_cross > 0.5 && query.is_sneaking"},
                        {"low": f"variable.nabd_tp_cross > 0.5 && {low}"},
                    ]},
                    "stand": {**show(1.62), "transitions": [{"off": f"variable.nabd_tp_cross < 0.5 || !({standing})"}]},
                    "sneak": {**show(1.27), "transitions": [{"off": "variable.nabd_tp_cross < 0.5 || !query.is_sneaking"}]},
                    "low": {**show(0.4), "transitions": [{"off": f"variable.nabd_tp_cross < 0.5 || !{low}"}]},
                },
            }
        },
    }
    os.makedirs(os.path.join(RP, "animation_controllers"), exist_ok=True)
    json.dump(j, open(os.path.join(RP, "animation_controllers", "nabd_shoulder.animation_controllers.json"), "w"), indent=2)


def particle():
    # direction the camera looks (Minecraft yaw/pitch: yaw 0 = south, pitch > 0 = down)
    p, y = "query.camera_rotation(0)", "query.camera_rotation(1)"
    d = 0.6
    pos = [f"-math.sin({y}) * math.cos({p}) * {d}",
           f"variable.eye - math.sin({p}) * {d}",
           f"math.cos({y}) * math.cos({p}) * {d}"]
    j = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": "nabd:tp_cross",
                "basic_render_parameters": {"material": "particles_alpha", "texture": "textures/particle/nabd_cross"},
            },
            "components": {
                "minecraft:emitter_local_space": {"position": True, "rotation": False},
                "minecraft:emitter_rate_steady": {"spawn_rate": 40, "max_particles": 1},
                "minecraft:emitter_lifetime_looping": {"active_time": 1},
                "minecraft:emitter_shape_point": {},
                "minecraft:particle_lifetime_expression": {"max_lifetime": 0.25},
                "minecraft:particle_initial_speed": 0,
                "minecraft:particle_motion_parametric": {"relative_position": pos},
                "minecraft:particle_appearance_billboard": {
                    "size": [0.016, 0.016],
                    "facing_camera_mode": "rotate_xyz",
                    "uv": {"texture_width": 16, "texture_height": 16, "uv": [0, 0], "uv_size": [16, 16]},
                },
            },
        },
    }
    os.makedirs(os.path.join(RP, "particles"), exist_ok=True)
    json.dump(j, open(os.path.join(RP, "particles", "nabd_tp_cross.particle.json"), "w"), indent=2)
    # original small plus: white with a dark rim, 16x16
    img = np.zeros((16, 16, 4), np.uint8)
    rim, core = (25, 25, 30, 210), (255, 255, 255, 255)
    for x0, y0, x1, y1, c in ((6, 1, 10, 15, rim), (1, 6, 15, 10, rim), (7, 2, 9, 14, core), (2, 7, 14, 9, core)):
        img[y0:y1, x0:x1] = c
    img[7:9, 7:9] = core
    os.makedirs(os.path.join(RP, "textures", "particle"), exist_ok=True)
    Image.fromarray(img, "RGBA").save(os.path.join(RP, "textures", "particle", "nabd_cross.png"))


def entity():
    v = json.load(open(VANILLA))
    desc = v["minecraft:client_entity"]["description"]
    sc = desc["scripts"]
    sc["initialize"] = sc.get("initialize", []) + ["variable.nabd_tp_k = 0.0;"]
    sc["pre_animation"] = [l for l in sc.get("pre_animation", []) if "nabd_tp" not in l] + PRE
    desc["animations"]["nabd_shoulder"] = "animation.nabd.shoulder"
    desc["animations"]["nabd_cross"] = "controller.animation.nabd.cross"
    sc["animate"] = [a for a in sc["animate"] if a not in ("nabd_shoulder", "nabd_cross")] + ["nabd_shoulder", "nabd_cross"]
    desc.setdefault("particle_effects", {})["nabd_cross"] = "nabd:tp_cross"
    os.makedirs(os.path.join(RP, "entity"), exist_ok=True)
    json.dump(v, open(os.path.join(RP, "entity", "player.entity.json"), "w"), indent=2)


if __name__ == "__main__":
    animation()
    controller()
    particle()
    entity()
    print("shoulder view written")
