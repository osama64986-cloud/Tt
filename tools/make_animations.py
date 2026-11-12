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


# ---------------------------------------------------------------- attack helpers
SWORDS = ", ".join(f"'minecraft:{m}_sword'" for m in ("wooden", "stone", "iron", "golden", "diamond", "netherite", "copper"))
SW = f"(query.is_item_name_any('slot.weapon.mainhand', {SWORDS}) ? 1.0 : 0.0)"
P_ = "variable.attack_time"


def ease(k):
    """smoothstep of a 0..1 Molang expression"""
    return f"(({k}) * ({k}) * (3.0 - 2.0 * ({k})))"


K1 = ease(f"math.clamp({P_} / 0.25, 0.0, 1.0)")              # wind-up
K2 = ease(f"math.clamp(({P_} - 0.25) / 0.3, 0.0, 1.0)")       # strike
K3 = ease(f"math.clamp(({P_} - 0.55) / 0.45, 0.0, 1.0)")      # recovery


def slash(windup, strike):
    """0 -> wind-up value -> strike value -> 0, eased between the phases"""
    return f"math.lerp(math.lerp(math.lerp(0.0, {windup}, {K1}), {strike}, {K2}), 0.0, {K3})"


J1 = ease(f"math.clamp({P_} / 0.3, 0.0, 1.0)")                 # punch: out ...
J2 = ease(f"math.clamp(({P_} - 0.3) / 0.7, 0.0, 1.0)")         # ... and back


SWING_KEYS = (0.25, 0.48, 0.62)       # wind-up, strike, follow-through; back to rest at 1.0


# swimming stroke: u is the place in the stroke (0..1), one stroke every 1.1 s
def _u(offset):
    return f"math.mod(query.life_time * 0.9 + {offset}, 1.0)"


def SWIM_X(offset):
    # -175 (reaching forward) -> -5 (at the hip) -> back to -175, smooth all the way
    return f"math.lerp(0.0, -90.0 - 85.0 * math.cos(({_u(offset)}) * 360.0), variable.swim_amount)"


def SWIM_Z(offset, side):
    # the arm swings out to the side only on the way back over the top
    return f"math.lerp(0.0, {side} * 70.0 * math.max(0.0, -math.sin(({_u(offset)}) * 360.0)), variable.swim_amount)"


def keys(windup, strike, follow):
    """rest -> wind-up -> strike -> follow-through -> rest, eased between keys"""
    t1, t2, t3 = SWING_KEYS
    e1 = ease(f"math.clamp({P_} / {t1}, 0.0, 1.0)")
    e2 = ease(f"math.clamp(({P_} - {t1}) / {t2 - t1}, 0.0, 1.0)")
    e3 = ease(f"math.clamp(({P_} - {t2}) / {t3 - t2}, 0.0, 1.0)")
    e4 = ease(f"math.clamp(({P_} - {t3}) / {1.0 - t3}, 0.0, 1.0)")
    return (f"math.lerp(math.lerp(math.lerp(math.lerp(0.0, {windup}, {e1}), {strike}, {e2}), {follow}, {e3}), 0.0, {e4})")


def jab(peak):
    return f"math.lerp(math.lerp(0.0, {peak}, {J1}), 0.0, {J2})"


def pick(sword, punch):
    return f"({SW} * {sword} + (1.0 - {SW}) * {punch})"


anims = {
    # ------------------------------------------------- walking, running, jumping
    "animation.player.move.arms": {
        "loop": True,
        "bones": {
            "leftarm": {"rotation": [
                f"math.clamp({GROUND} * (variable.tcos0 * (1.05 + {SPRINT} * 0.15) - {SPRINT} * 14.0), -66.0, 52.0)"
                f" - {UP} * 38.0 - {DOWN} * 18.0 - {TOP} * 12.0",
                0.0,
                f"-({GROUND} * ({STRIDE} * 0.06 + 2.0) + {UP} * 12.0 + {DOWN} * 52.0 + {TOP} * 30.0)"]},
            "rightarm": {"rotation": [
                f"math.clamp({GROUND} * (-variable.tcos0 * (1.05 + {SPRINT} * 0.15) - {SPRINT} * 14.0), -66.0, 52.0)"
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
                f"math.clamp({GROUND} * variable.tcos0 * -(1.4 + {SPRINT} * 0.05), -62.0, 62.0) - {UP} * 42.0 - {DOWN} * 10.0 - {TOP} * 20.0",
                -0.1,
                f"-0.1 - {DOWN} * 7.0 - {TOP} * 3.0"]},
            "rightleg": {"rotation": [
                f"math.clamp({GROUND} * variable.tcos0 * (1.4 + {SPRINT} * 0.05), -62.0, 62.0) + {UP} * 16.0 - {DOWN} * 16.0 - {TOP} * 4.0",
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
    # body / head / root offsets are what the game's camera and hit box expect;
    # on top: hands held low and ready, knees apart, a soft sway while creeping
    "animation.player.sneaking": {
        "loop": True,
        "bones": {
            "body": {"position": [0.0, -2.0, 0.0]},
            "head": {"position": [0.0, -1.0, 0.0]},
            "leftarm": {"rotation": ["-20.0 + variable.tcos0 * 0.35", 0.0, "-7.0 - math.abs(variable.tcos0) * 0.05"]},
            "rightarm": {"rotation": ["-20.0 - variable.tcos0 * 0.35", 0.0, "7.0 + math.abs(variable.tcos0) * 0.05"]},
            "leftleg": {"rotation": [-28.0, -0.1, -2.5]},
            "rightleg": {"rotation": [-28.0, 0.1, 2.5]},
            "waist": {"rotation": [0.0, "variable.tcos0 * 0.1", 0.0]},
            "root": {"position": [0.0, 1.25, 9.0], "rotation": ["28.0 - this", 0.0, 0.0]},
        },
    },
    # ----------------------------------------------------------------- attack
    # sword: wind-up high and back, a fast diagonal slash across the body, an
    # unhurried recovery; the body turns with the blade and the free arm
    # comes forward for balance.  Anything else: a short forward jab.
    "animation.player.attack.rotations": {
        "loop": True,
        "bones": {
            "body": {"rotation": [pick(keys("0.0", "6.0", "3.0"), "0.0"), pick(keys("22.0", "-24.0", "-30.0"), jab("-10.0")), 0.0]},
            "rightarm": {"rotation": [
                pick(keys("-155.0", "-50.0", "-22.0"), jab("-85.0")),
                pick(keys("5.0", "-55.0", "-65.0"), jab("10.0")),
                pick(keys("42.0", "2.0", "-5.0"), jab("0.0"))]},
            # the blade itself turns in the fist: back over the shoulder, then down through the cut
            "rightitem": {"rotation": [pick(keys("-45.0", "55.0", "62.0"), "0.0"), 0.0, 0.0]},
            "leftarm": {"rotation": [pick(keys("-18.0", "12.0", "8.0"), jab("12.0")), 0.0,
                                     pick(keys("-12.0", "-6.0", "-4.0"), jab("-4.0"))]},
        },
    },
    # --------------------------------------------------------------- swimming
    # front crawl: each arm reaches far forward, pulls down under the body to
    # the hip, then swings back over the top out to the side; the arms are half
    # a stroke apart and the body rolls a little towards the pulling arm
    "animation.player.swim": {
        "loop": True,
        "override_previous_animation": True,
        "bones": {
            "rightarm": {"rotation": [SWIM_X("0.0"), 0.0, SWIM_Z("0.0", "1.0")]},
            "leftarm": {"rotation": [SWIM_X("0.5"), 0.0, SWIM_Z("0.5", "-1.0")]},
            "body": {"rotation": [0.0, "math.lerp(0.0, math.sin(query.life_time * 324.0) * 9.0, variable.swim_amount)", 0.0]},
            "head": {"rotation": [0.0, "math.lerp(0.0, math.sin(query.life_time * 324.0) * 14.0, variable.swim_amount)", 0.0]},
        },
    },
    "animation.player.swim.no_right_arm": {
        "loop": True,
        "override_previous_animation": True,
        "bones": {
            "leftarm": {"rotation": [SWIM_X("0.5"), 0.0, SWIM_Z("0.5", "-1.0")]},
            "body": {"rotation": [0.0, "math.lerp(0.0, math.sin(query.life_time * 324.0) * 9.0, variable.swim_amount)", 0.0]},
        },
    },
    "animation.player.swim.legs": {
        "loop": True,
        "override_previous_animation": True,
        "bones": {
            "leftleg": {"rotation": ["math.lerp(0.0, math.cos(query.life_time * 420.0 + 180.0) * 23.0, variable.swim_amount)", -0.1, -1.5]},
            "rightleg": {"rotation": ["math.lerp(0.0, math.cos(query.life_time * 420.0) * 23.0, variable.swim_amount)", 0.1, 1.5]},
        },
    },
    # ----------------------------------------------------------- first person
    # the hand you see: a sword is drawn up and to the right, then cut down and
    # across; an empty hand or a block gives a short punch forward
    "animation.player.first_person.attack_rotation": {
        "loop": True,
        "bones": {
            "rightarm": {
                "position": [
                    pick(keys("2.0", "-6.0", "-7.0"), jab("-3.0")),
                    pick(keys("4.0", "-5.0", "-4.0"), jab("-2.0")) + " + variable.short_arm_offset_right",
                    pick(keys("-2.0", "3.0", "2.0"), jab("4.0"))],
                "rotation": [
                    pick(keys("-20.0", "30.0", "20.0"), jab("-30.0")),
                    pick(keys("15.0", "-30.0", "-35.0"), jab("10.0")),
                    pick(keys("-12.0", "25.0", "28.0"), jab("8.0"))]},
        },
    },
    "animation.player.first_person.walk": {
        "loop": True,
        "bones": {
            "leftarm": {
                "position": ["math.sin(-query.walk_distance * 180.0) * variable.hand_bob * (11.5 + (query.is_sprinting ? 4.0 : 0.0))",
                             "-math.abs(math.cos(-query.walk_distance * 180.0)) * variable.hand_bob * (17.0 + (query.is_sprinting ? 6.0 : 0.0)) + variable.short_arm_offset_left",
                             0.0],
                "rotation": [0.0, 0.0, "math.sin(-query.walk_distance * 180.0) * variable.hand_bob * (22.0 + (query.is_sprinting ? 10.0 : 0.0))"]},
            "rightarm": {
                "position": ["math.sin(-query.walk_distance * 180.0) * variable.hand_bob * (11.5 + (query.is_sprinting ? 4.0 : 0.0))",
                             "-math.abs(math.cos(-query.walk_distance * 180.0)) * variable.hand_bob * (17.0 + (query.is_sprinting ? 6.0 : 0.0)) + variable.short_arm_offset_right",
                             0.0],
                "rotation": [0.0, 0.0, "math.sin(-query.walk_distance * 180.0) * variable.hand_bob * (22.0 + (query.is_sprinting ? 10.0 : 0.0))"]},
        },
    },
    "animation.player.first_person.breathing_bob": {
        "loop": True,
        "override_previous_animation": False,
        "bones": {
            "rightitem": {
                "position": ["variable.bob_animation * math.cos(query.life_time * 31.0) * 0.25",
                             "variable.bob_animation * math.sin(query.life_time * 45.0) * 0.65",
                             0.0],
                "rotation": [f"variable.bob_animation * math.sin(query.life_time * 45.0 + 20.0) * 1.6",
                             f"variable.bob_animation * math.cos(query.life_time * 31.0) * 1.2",
                             f"variable.bob_animation * {SW} * math.sin(query.life_time * 38.0) * 1.4"]},
        },
    },
}

out = os.path.join(ROOT, "pack_src", "animations", "nabd_player.animation.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump({"format_version": "1.8.0", "animations": anims}, open(out, "w"), indent=2)
print("wrote", out, len(anims), "animations")
