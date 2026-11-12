#!/usr/bin/env python3
"""Writes pack_src/animations/nabd_player.animation.json.

These are our own motion curves.  They are registered under the animation
names the game's player already plays, so they take over without replacing the
player entity file (keeps skins, capes, armour and future updates working).

Conventions measured from the game's skeleton:
  +x on a limb swings its tip backwards, -x raises it forwards
  +z on the right arm / -z on the left arm lifts it away from the body
  `variable.tcos0` is the stride swing in degrees, already scaled by speed
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1 while jumping / falling freely, 0 otherwise
AIR = "(query.is_on_ground || query.is_in_water || query.is_riding || query.is_gliding || query.is_sleeping ? 0.0 : 1.0)"
# query.vertical_speed is in metres per second: a jump starts near +8, a long fall goes far below -10
UP = f"({AIR} * math.clamp(query.vertical_speed / 6.0, 0.0, 1.0))"         # 0..1 while rising
DOWN = f"({AIR} * math.clamp(-query.vertical_speed / 9.0, 0.0, 1.0))"      # 0..1 while falling
TOP = f"({AIR} * (1.0 - math.clamp(math.abs(query.vertical_speed) / 3.0, 0.0, 1.0)))"   # near the top of the arc
DRY = "(query.is_swimming ? 0.0 : 1.0)"
SPRINT = "(query.is_sprinting && query.is_on_ground ? 1.0 : 0.0)"
STRIDE = "math.abs(variable.tcos0)"
T = "variable.attack_time"
SWING = "math.sin((1.0 - math.pow(1.0 - variable.attack_time, 3.0)) * 180.0)"
ARC = "math.sin(variable.attack_time * 180.0)"
GROUND = f"(1.0 - {AIR})"

anims = {
    # ------------------------------------------------- walking, running, jumping
    "animation.player.move.arms": {
        "loop": True,
        "bones": {
            "leftarm": {"rotation": [
                f"math.clamp({GROUND} * (variable.tcos0 * (1.05 + {SPRINT} * 0.15) - {SPRINT} * 14.0), -78.0, 70.0)"
                f" - {UP} * 38.0 - {DOWN} * 18.0 - {TOP} * 12.0",
                0.0,
                f"-({GROUND} * ({STRIDE} * 0.06 + 2.0) + {UP} * 12.0 + {DOWN} * 52.0 + {TOP} * 30.0)"]},
            "rightarm": {"rotation": [
                f"math.clamp({GROUND} * (-variable.tcos0 * (1.05 + {SPRINT} * 0.15) - {SPRINT} * 14.0), -78.0, 70.0)"
                f" - {UP} * 30.0 - {DOWN} * 18.0 - {TOP} * 12.0",
                0.0,
                f"{GROUND} * ({STRIDE} * 0.06 + 2.0) + {UP} * 12.0 + {DOWN} * 52.0 + {TOP} * 30.0"]},
            # the torso dips on each footfall, turns against the legs, leans into a run,
            # leans back as the jump starts and forward as you drop
            "waist": {
                "rotation": [
                    f"{DRY} * ({GROUND} * (1.5 + {STRIDE} * 0.035 + {SPRINT} * 8.0) - {UP} * 6.0 + {DOWN} * 7.0)",
                    f"{DRY} * {GROUND} * variable.tcos0 * 0.14",
                    0.0],
                "position": [0.0, f"{DRY} * {GROUND} * -{STRIDE} * 0.022", 0.0]},
        },
    },
    "animation.player.move.legs": {
        "loop": True,
        "bones": {
            "leftleg": {"rotation": [
                f"math.clamp({GROUND} * variable.tcos0 * -(1.4 + {SPRINT} * 0.05), -80.0, 80.0) - {UP} * 42.0 - {DOWN} * 10.0 - {TOP} * 20.0",
                -0.1,
                f"-0.1 - {DOWN} * 7.0 - {TOP} * 3.0"]},
            "rightleg": {"rotation": [
                f"math.clamp({GROUND} * variable.tcos0 * (1.4 + {SPRINT} * 0.05), -80.0, 80.0) + {UP} * 16.0 - {DOWN} * 16.0 - {TOP} * 4.0",
                0.1,
                f"0.1 + {DOWN} * 7.0 + {TOP} * 3.0"]},
        },
    },
    # ------------------------------------------------------- idle / breathing
    "animation.player.bob": {
        "loop": True,
        "bones": {
            "leftarm": {"rotation": ["math.sin(query.life_time * 62.0) * 1.7", 0.0,
                                     "-(math.cos(query.life_time * 88.0) * 2.3 + 3.1)"]},
            "rightarm": {"rotation": ["-math.sin(query.life_time * 62.0 + 40.0) * 1.7", 0.0,
                                      "math.cos(query.life_time * 88.0 + 25.0) * 2.3 + 3.1"]},
            "waist": {"rotation": ["math.sin(query.life_time * 88.0) * 0.55", 0.0, 0.0]},
            "head": {"position": [0.0, "math.sin(query.life_time * 88.0 - 30.0) * 0.1", 0.0]},
        },
    },
    # --------------------------------------------------------------- sneaking
    # body / head / root offsets are the ones the game's camera and hit box
    # expect; the arm and leg pose is ours (hands held ready, knees apart).
    "animation.player.sneaking": {
        "loop": True,
        "bones": {
            "body": {"position": [0.0, -2.0, 0.0]},
            "head": {"position": [0.0, -1.0, 0.0]},
            "leftarm": {"rotation": [-11.0, 0.0, -5.0]},
            "rightarm": {"rotation": [-11.0, 0.0, 5.0]},
            "leftleg": {"rotation": [-28.0, -0.1, -1.6]},
            "rightleg": {"rotation": [-28.0, 0.1, 1.6]},
            "root": {"position": [0.0, 1.25, 9.0], "rotation": ["28.0 - this", 0.0, 0.0]},
        },
    },
    # ----------------------------------------------------------------- attack
    "animation.player.attack.rotations": {
        "loop": True,
        "bones": {
            "body": {"rotation": [0.0, f"math.sin(360.0 * math.sqrt({T})) * 9.0", 0.0]},
            "leftarm": {"rotation": [f"{ARC} * 13.0", 0.0, f"-{ARC} * 4.0"]},
            "rightarm": {"rotation": [f"-({SWING} * 64.0 + {ARC} * 16.0)", f"{SWING} * 34.0", f"-{ARC} * 10.0"]},
        },
    },
    # --------------------------------------------------------------- swimming
    "animation.player.swim.legs": {
        "loop": True,
        "override_previous_animation": True,
        "bones": {
            "leftleg": {"rotation": ["math.lerp(0.0, math.cos(query.life_time * 420.0 + 180.0) * 23.0, variable.swim_amount)", -0.1, -1.5]},
            "rightleg": {"rotation": ["math.lerp(0.0, math.cos(query.life_time * 420.0) * 23.0, variable.swim_amount)", 0.1, 1.5]},
        },
    },
    # ----------------------------------------------------------- first person
    "animation.player.first_person.walk": {
        "loop": True,
        "bones": {
            "leftarm": {
                "position": ["math.sin(-query.walk_distance * 180.0) * variable.hand_bob * 11.5",
                             "-math.abs(math.cos(-query.walk_distance * 180.0)) * variable.hand_bob * 17.0 + variable.short_arm_offset_left",
                             0.0],
                "rotation": [0.0, 0.0, "math.sin(-query.walk_distance * 180.0) * variable.hand_bob * 22.0"]},
            "rightarm": {
                "position": ["math.sin(-query.walk_distance * 180.0) * variable.hand_bob * 11.5",
                             "-math.abs(math.cos(-query.walk_distance * 180.0)) * variable.hand_bob * 17.0 + variable.short_arm_offset_right",
                             0.0],
                "rotation": [0.0, 0.0, "math.sin(-query.walk_distance * 180.0) * variable.hand_bob * 22.0"]},
        },
    },
    "animation.player.first_person.breathing_bob": {
        "loop": True,
        "override_previous_animation": False,
        "bones": {
            "rightitem": {"position": ["variable.bob_animation * math.cos(query.life_time * 31.0) * 0.22",
                                       "variable.bob_animation * math.sin(query.life_time * 45.0) * 0.62",
                                       0.0]},
        },
    },
}

out = os.path.join(ROOT, "pack_src", "animations", "nabd_player.animation.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump({"format_version": "1.8.0", "animations": anims}, open(out, "w"), indent=2)
print("wrote", out, len(anims), "animations")
