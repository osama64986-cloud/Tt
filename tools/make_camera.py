"""Shoulder camera data: camera presets for the behavior pack and the aim
marker particle (with its small original texture) for the resource pack.

The presets build on the game's own "follow_orbit" camera.  The side shift
(view offset) and the pivot height are set from the script when the camera is
switched on, so they can be changed in the settings menu without new files.
Only the distance (radius) and the control style have to live in the presets.
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "bp_src")
RP = os.path.join(ROOT, "pack_src")

DISTANCES = {"near": 2.6, "mid": 3.6, "far": 4.8}
CONTROLS = {
    "": "locked_player_relative_strafe",   # classic: the player turns with the mouse / swipe
    "_free": "camera_relative",            # action style: the character turns towards where it walks
}


def presets():
    out = os.path.join(BP, "cameras", "presets")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.startswith("nabd_shoulder"):
            os.remove(os.path.join(out, f))
    for dname, radius in DISTANCES.items():
        for cname, scheme in CONTROLS.items():
            ident = f"nabd:shoulder_{dname}{cname}"
            j = {
                "format_version": "1.21.0",
                "minecraft:camera_preset": {
                    "identifier": ident,
                    "inherit_from": "minecraft:follow_orbit",
                    "radius": radius,
                    "view_offset": [0.75, 0.2],
                    "entity_offset": [0.0, 0.55, 0.0],
                    "control_scheme": scheme,
                    "player_effects": True,
                },
            }
            json.dump(j, open(os.path.join(out, f"nabd_shoulder_{dname}{cname}.json"), "w"), indent=2)


def aim_texture():
    """16x16 marker: a thin light ring with a dark rim and a centre dot.
    It is white so the particle can tint it (white normally, red on a mob in reach)."""
    s = 16
    img = np.zeros((s, s, 4), np.uint8)
    yy, xx = np.mgrid[0:s, 0:s] + 0.5
    r = np.hypot(xx - 8, yy - 8)
    ring = (r > 4.6) & (r < 6.0)
    rim = ((r > 3.6) & (r <= 4.6)) | ((r >= 6.0) & (r < 7.0))
    dot = r < 1.5
    dot_rim = (r >= 1.5) & (r < 2.5)
    for m, c in ((rim, (30, 30, 36, 200)), (dot_rim, (30, 30, 36, 200)), (ring, (255, 255, 255, 255)), (dot, (255, 255, 255, 255))):
        img[m] = c
    # four small gaps so it reads as a sight, not a coin
    for x0, y0 in ((7, 0), (7, 13), (0, 7), (13, 7)):
        img[y0:y0 + 3, x0:x0 + 2] = 0
    out = os.path.join(RP, "textures", "particle")
    os.makedirs(out, exist_ok=True)
    Image.fromarray(img, "RGBA").save(os.path.join(out, "nabd_aim.png"))


def aim_particle():
    j = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": "nabd:aim",
                "basic_render_parameters": {"material": "particles_alpha", "texture": "textures/particle/nabd_aim"},
            },
            "components": {
                "minecraft:emitter_rate_instant": {"num_particles": 1},
                "minecraft:emitter_lifetime_once": {"active_time": 0.05},
                "minecraft:emitter_shape_point": {},
                "minecraft:particle_lifetime_expression": {"max_lifetime": 0.11},
                "minecraft:particle_initial_speed": 0,
                "minecraft:particle_appearance_billboard": {
                    "size": ["variable.size", "variable.size"],
                    "facing_camera_mode": "rotate_xyz",
                    "uv": {"texture_width": 16, "texture_height": 16, "uv": [0, 0], "uv_size": [16, 16]},
                },
                "minecraft:particle_appearance_tinting": {
                    "color": ["variable.red", "variable.green", "variable.blue", 1.0]
                },
            },
        },
    }
    out = os.path.join(RP, "particles")
    os.makedirs(out, exist_ok=True)
    json.dump(j, open(os.path.join(out, "nabd_aim.particle.json"), "w"), indent=2)


if __name__ == "__main__":
    presets()
    aim_texture()
    aim_particle()
    print("camera presets, aim texture and particle written")
