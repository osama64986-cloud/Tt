#!/usr/bin/env python3
"""Evaluates every Molang expression of our animations for a set of typical
player states (tiny Molang -> Python translation) so wrong signs or runaway
angles show up without launching the game."""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = json.load(open(os.path.join(ROOT, "pack_src", "animations", "nabd_player.animation.json")))["animations"]
FN = {"dsin": lambda d: math.sin(math.radians(d)), "dcos": lambda d: math.cos(math.radians(d)), "abs": abs,
      "clamp": lambda x, a, b: max(a, min(b, x)), "pow": pow, "sqrt": lambda x: math.sqrt(max(0, x)),
      "lerp": lambda a, b, t: a + (b - a) * t, "max": max, "math_fmod": math.fmod}


def ev(expr, env):
    if not isinstance(expr, str):
        return float(expr)
    e = re.sub(r"\bq\.", "query.", expr)
    e = re.sub(r"query\.is_item_name_any\([^)]*\)", str(env.get("_sword", 0)), e)
    e = re.sub(r"\(([^()?]+)\?([^():]+):([^()]+)\)", r"((\2) if (\1) else (\3))", e)   # ternaries first
    for k in sorted(env, key=len, reverse=True):
        e = e.replace(k, f"({env[k]})")
    for a, b in (("math.sin(", "dsin("), ("math.cos(", "dcos("), ("math.abs(", "abs("), ("math.clamp(", "clamp("),
                 ("math.pow(", "pow("), ("math.sqrt(", "sqrt("), ("math.lerp(", "lerp("), ("math.max(", "max("), ("math.mod(", "math_fmod("), ("&&", " and "), ("||", " or ")):
        e = e.replace(a, b)
    return eval(e, dict(FN))


BASE = {"query.is_in_water": 0, "query.is_riding": 0, "query.is_gliding": 0, "query.is_sleeping": 0,
        "query.is_swimming": 0, "variable.attack_time": 0, "query.life_time": 3.3, "variable.swim_amount": 1,
        "query.walk_distance": 1.3, "variable.hand_bob": 0.08, "variable.short_arm_offset_left": 0,
        "variable.short_arm_offset_right": 0, "variable.bob_animation": 1, "this": 5,
        "variable.tcos0": 0, "query.is_sprinting": 0, "query.is_on_ground": 1, "query.vertical_speed": 0, "query.target_x_rotation": 0}
STATES = {
    "idle": {},
    "swimming (crawl stroke)": {"query.is_swimming": 1, "query.is_in_water": 1, "query.life_time": 0.4},
    "walk (stride peak)": {"variable.tcos0": 40},
    "sprint": {"variable.tcos0": -57, "query.is_sprinting": 1},
    "jump start": {"variable.tcos0": 20, "query.is_on_ground": 0, "query.vertical_speed": 8.0},
    "top of jump": {"query.is_on_ground": 0, "query.vertical_speed": 0.3},
    "falling": {"query.is_on_ground": 0, "query.vertical_speed": -9.0},
    "sprint jump": {"variable.tcos0": -50, "query.is_sprinting": 1, "query.is_on_ground": 0, "query.vertical_speed": 6.0},
    "punch 30%": {"variable.attack_time": 0.3},
    "sword wind-up 25%": {"variable.attack_time": 0.25, "_sword": 1},
    "sword strike 48%": {"variable.attack_time": 0.48, "_sword": 1},
    "sword follow 62%": {"variable.attack_time": 0.62, "_sword": 1},
    "sword recover 80%": {"variable.attack_time": 0.8, "_sword": 1},
    "sneaking walk": {"variable.tcos0": 30},
    "swimming": {"query.is_swimming": 1, "query.is_in_water": 1, "query.is_on_ground": 0, "variable.tcos0": 30},
}
def main():
    worst = 0.0
    for sn, st in STATES.items():
        env = dict(BASE)
        env.update(st)
        print("==", sn)
        for an, ad in A.items():
            row = []
            for bone, ch in ad["bones"].items():
                for c, vals in ch.items():
                    v = [ev(x, env) for x in vals]
                    worst = max(worst, max(abs(x) for x in v) if c == "rotation" else 0)
                    if any(abs(x) > 0.05 for x in v):
                        row.append(f"{bone}.{c[:3]}=[{', '.join('%.1f' % x for x in v)}]")
            if row:
                print("  ", an.split("player.")[1].ljust(26), "  ".join(row))
    print("largest rotation seen: %.1f deg" % worst)
    sys.exit(0 if worst < 180 else 1)   # sword wind-up (150) and swim reach (175) lift the arm overhead


if __name__ == "__main__":
    main()
