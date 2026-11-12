"""Shoulder view for the normal third-person (back) camera - resource pack only.

The game's own camera is not touched: it turns with the player instantly and
sits right behind the player's eyes, so the middle of the screen is exactly
where hits and clicks land.  Only on your own screen, only in third person, the
character model is drawn shifted to one side so the middle of the screen is
free.  Other players see you normally; first person and the inventory doll are
untouched.

No player entity file is replaced (that would clash with other add-ons): the
shift rides on "animation.humanoid.base_pose", which the game's player plays in
third person anyway.  It lives in its own file with a recent format version
(pack-setting queries need 1.21.130+); if a game version refused the file, only
the shoulder view would be lost.

A small crosshair is added to the HUD's crosshair layer, so it is also there in
third person (the game hides its own there).

Settings: Settings > Global Resources > Nabd > gear icon.
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "pack_src")
PX_PER_BLOCK = 16.0 / 0.9375          # the player model is drawn at 0.9375 scale

ON = ("(query.is_local_player && !query.is_first_person && !query.is_in_ui"
      " && query.is_pack_setting_enabled('nabd:shoulder'))")
SIDE = "(query.is_pack_setting_selected('nabd:shoulder_side', 'right') ? -1.0 : 1.0)"
SHIFT = f"({ON} ? {SIDE} * query.get_pack_setting('nabd:shoulder_shift') * {PX_PER_BLOCK / 10:.4f} : 0.0)"


def animation():
    """Reads the in-game pack settings into variables; the shift itself is drawn by our
    movement animation (motion.py), which falls back to the defaults if this file is
    not loaded by a game version."""
    setv = ("v.nb_sh_on = query.is_pack_setting_enabled('nabd:shoulder') ? 1.0 : 0.0; "
            "v.nb_sh_side = query.is_pack_setting_selected('nabd:shoulder_side', 'right') ? -1.0 : 1.0; "
            "v.nb_sh_amt = query.get_pack_setting('nabd:shoulder_shift') / 10.0; return 0.0;")
    j = {
        "format_version": "1.21.130",
        "animations": {
            "animation.humanoid.base_pose": {
                "loop": True,
                "bones": {
                    "waist": {"rotation": [0.0, 0.0, 0.0]},
                    "root": {"position": [setv, 0.0, 0.0]},
                },
            }
        },
    }
    json.dump(j, open(os.path.join(RP, "animations", "nabd_shoulder.animation.json"), "w"), indent=2)


def crosshair():
    img = np.zeros((9, 9, 4), np.uint8)
    rim, core = (20, 20, 24, 170), (255, 255, 255, 235)
    img[0:9, 3:6] = rim
    img[3:6, 0:9] = rim
    img[1:8, 4] = core
    img[4, 1:8] = core
    os.makedirs(os.path.join(RP, "textures", "ui"), exist_ok=True)
    Image.fromarray(img, "RGBA").save(os.path.join(RP, "textures", "ui", "nabd_cross.png"))
    ui = {
        "namespace": "hud_crosshair",
        "hud_crosshair_screen": {
            "modifications": [
                {"array_name": "controls", "operation": "insert_back",
                 "value": [{"nabd_cross@hud_crosshair.nabd_cross": {}}]}
            ]
        },
        "nabd_cross": {
            "type": "image", "texture": "textures/ui/nabd_cross", "size": [9, 9],
            "anchor_from": "center", "anchor_to": "center", "layer": 3,
        },
    }
    os.makedirs(os.path.join(RP, "ui"), exist_ok=True)
    json.dump(ui, open(os.path.join(RP, "ui", "hud_crosshair_overlay.json"), "w"), indent=2)


if __name__ == "__main__":
    animation()
    crosshair()
    print("shoulder view written")
