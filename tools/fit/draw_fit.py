"""يحسب مفاتيح حركة سحب السهم (arm_r / fore_r) حتى الإيد توصل لرأس سهم بالجعبة، تسحبه لفوق، تلفه فوق الكتف، وتركبه بالقوس،
بدون ما السهم أو الإيد يخترقون الراس أو الجسم أو العباءة. النتيجة تنكتب بأنيميشن السحب."""
import sys, json, copy, itertools, numpy as np
exec(open(sys.argv[1]).read().split("base_arm, base_bow")[0])
m = R.Model(f"{RP}/models/entity/sh_archer.geo.json", f"{RP}/textures/entity/sh_archer.png")
D0 = copy.deepcopy(A["animation.sh_archer.draw"]); IDLE = A["animation.sh_archer.idle"]

def point_world(pose, bone, pt):
    p = np.array(pt, float)
    for bb in m.chain(bone):
        q = pose.get(bb["name"], {"rot": [0, 0, 0], "pos": [0, 0, 0]})
        rot = [a + b for a, b in zip(bb.get("rotation", [0, 0, 0]), q["rot"])]
        pv = np.array(bb.get("pivot", [0, 0, 0]), float)
        p = (p - pv) @ R.rot_matrix(*rot).T + pv + np.array([q["pos"][0], q["pos"][1], -q["pos"][2]])
    return p

def mk(keys):
    d = copy.deepcopy(D0)
    d["bones"]["arm_r"]["rotation"] = {k: v[0] for k, v in keys.items()}
    d["bones"]["fore_r"]["rotation"] = {k: [v[1], 0, 0] for k, v in keys.items()}
    return d

def pose(anim, t):
    env = {"q": {"modified_distance_moved": 0, "modified_move_speed": 0, "life_time": t, "anim_time": t, "property": lambda *a: 0}}
    return R.pose_from_anims([IDLE, anim], t, env)

OBST = ["head", "body", "cape_b", "cape_l", "cape_r", "cape_f", "quiver"]
def hits(p, bones, obst=OBST, margin=0.0):
    pts = samples(cube_frames(p, bones), 3)
    return inside_count(pts, cube_frames(p, obst), margin)

# الهدف: رأس الريش لسهم بالجعبة (نص المكعب) بوضعية الراحة
p0 = pose(D0, 0.0)
quiv = [c for c in m.bones["quiver"]["cubes"]]
fl = [c for c in quiv if c["size"][1] == 1.3]
top = np.mean([point_world(p0, "quiver", np.array(c["origin"]) + np.array(c["size"]) / 2) for c in fl], 0)
axis = point_world(p0, "quiver", [-3.6, 25, 5.4]) - point_world(p0, "quiver", [-3.6, 15, 5.4]); axis /= np.linalg.norm(axis)
print("رأس السهم بالجعبة:", np.round(top, 1), "| محور الجعبة:", np.round(axis, 2))
HAND = [-6, 10.6, 0]
keys = {"0.0": ([-78, 64, 0], -20), "0.75": ([-84, 70, 0], -24), "1.6": ([-88, 118, 0], 2)}
grid = [(rx, ry, rz, f) for rx in range(-210, -59, 10) for ry in range(-30, 131, 15) for rz in range(-60, 61, 20) for f in range(-100, 11, 15)]

def best_key(t, target, extra_check, w_hit=4.0):
    best = None
    for rx, ry, rz, f in grid:
        k2 = dict(keys); k2[f"{t}"] = ([rx, ry, rz], f)
        an = mk(k2); p = pose(an, t)
        h = point_world(p, "fore_r", HAND)
        dist = np.linalg.norm(h - target) if target is not None else 0
        pen = hits(p, ["arm_r", "fore_r"], ["head"]) + extra_check(an, p)
        sc = dist + pen * w_hit
        if best is None or sc < best[0]: best = (sc, dist, pen, [rx, ry, rz], f)
    return best

# 1) الإمساك (0.3): الإيد عند رأس السهم بالجعبة
b1 = best_key(0.3, top, lambda an, p: 0)
keys["0.3"] = (b1[3], b1[4]); print("إمساك 0.3:", b1[1:])
# 2) السحب (0.45): الإيد فوق الجعبة بطول السهم تقريباً (يطلع السهم كله)، والسهم بالإيد ما يخترق الراس/الجسم
pull = top + axis * 9
b2 = best_key(0.45, pull, lambda an, p: hits(p, ["hand_arrow"], ["head", "body", "cape_b", "cape_r"]))
keys["0.45"] = (b2[3], b2[4]); print("سحب 0.45:", b2[1:])
# 3) اللف (0.6): بدون هدف، أقل اختراق للسهم على طول المسار 0.45 → 0.6 → 0.75
def path_pen(an, p):
    return sum(hits(pose(an, t), ["hand_arrow"], ["head", "body", "cape_b", "cape_r", "cape_f", "quiver"]) for t in (0.5, 0.55, 0.6, 0.65, 0.7, 0.74))
b3 = best_key(0.6, None, path_pen, w_hit=1.0)
keys["0.6"] = (b3[3], b3[4]); print("لف 0.6:", b3[1:])
an = mk(keys)
tot = {t: hits(pose(an, t), ["hand_arrow"], ["head", "body", "cape_b", "cape_r", "cape_f"]) for t in (0.32, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.74)}
print("اختراق السهم بالإيد عبر المسار:", tot)
json.dump({k: {"arm_r": v[0], "fore_r": v[1]} for k, v in sorted(keys.items(), key=lambda x: float(x[0]))}, open(sys.argv[2], "w"))
