"""يحسب وضعية القوس اللي ما تخترق العباءة ولا الجسم خلال كل دورة المشي، ويختار الأطبع (قوس عمودي جنب الجسم وقدامه شوية)."""
import sys, json, glob, itertools, math
import numpy as np
sys.path.insert(0, '/home/user/Tt/tools')
import render as R
RP = '/home/user/Tt/AnimePowers/RP'
A = {}
for f in glob.glob(RP + '/animations/*.json'): A.update(json.load(open(f))['animations'])
m = R.Model(f"{RP}/models/entity/sh_archer.geo.json", f"{RP}/textures/entity/sh_archer.png")

def cube_frames(pose, bones):
    """لكل مكعب بالعظام المطلوبة: (نقطة الأصل، 3 متجهات الأضلاع) بالعالم"""
    out = []
    for name in bones:
        b = m.bones[name]
        for c in b.get("cubes", []):
            o = np.array(c["origin"], float); s = np.array(c["size"], float)
            pts = np.array([o, o + [s[0], 0, 0], o + [0, s[1], 0], o + [0, 0, s[2]]])
            if "rotation" in c:
                pv = np.array(c.get("pivot", [0, 0, 0]), float); Rm = R.rot_matrix(*c["rotation"]); pts = (pts - pv) @ Rm.T + pv
            for bb in m.chain(name):
                p = pose.get(bb["name"], {"rot": [0, 0, 0], "pos": [0, 0, 0]})
                rot = [a + b2 for a, b2 in zip(bb.get("rotation", [0, 0, 0]), p["rot"])]
                pv = np.array(bb.get("pivot", [0, 0, 0]), float); Rm = R.rot_matrix(*rot)
                pts = (pts - pv) @ Rm.T + pv + np.array([p["pos"][0], p["pos"][1], -p["pos"][2]])
            out.append((pts[0], np.stack([pts[1] - pts[0], pts[2] - pts[0], pts[3] - pts[0]], 1)))
    return out

def samples(frames, n=3):
    pts = []
    for o, M in frames:
        for u, v, w in itertools.product(*[np.linspace(0.05, 0.95, n)] * 3):
            pts.append(o + M @ np.array([u, v, w]))
    return np.array(pts)

def inside_count(pts, frames, margin=0.15):
    k = 0
    for o, M in frames:
        try: Mi = np.linalg.inv(M)
        except np.linalg.LinAlgError: continue
        L = (pts - o) @ Mi.T
        sz = np.linalg.norm(M, axis=0)
        mg = margin / np.maximum(sz, 1e-6)
        ins = np.all((L > -mg) & (L < 1 + mg), axis=1)
        k += int(ins.sum())
    return k

ANIMS = [A['animation.sh_archer.idle'], A['animation.sh_archer.walk'], A['animation.sh_archer.move']]
def pose_at(t, arm, bow, speed=1.0):
    env = {"q": {"modified_distance_moved": t * 4, "modified_move_speed": speed, "life_time": t, "anim_time": t, "property": lambda *a: 0}}
    p = R.pose_from_anims(ANIMS, t, env)
    for bn, rot in (("arm_l", arm), ("bow", bow)):
        q = p.setdefault(bn, {"rot": [0, 0, 0], "pos": [0, 0, 0]})
        q["rot"] = [a + b for a, b in zip(q["rot"], rot)]
    return p

BODY = ["body", "cape_b", "cape_l", "cape_r", "cape_f", "leg_l", "leg_r", "head"]
def evaluate(arm, bow):
    worst = 0
    up_err = 0; front = 0
    for t in np.linspace(0, 1.6, 9):
        for spd in (0.0, 1.0):
            p = pose_at(t, arm, bow, spd)
            bowf = cube_frames(p, ["bow"])
            hits = inside_count(samples(bowf), cube_frames(p, BODY))
            worst = max(worst, hits)
    # طبيعية: محور ذراعي القوس (من الطرف للطرف) قريب من العمودي، والقوس قدام/جنب الجسم
    p = pose_at(0, arm, bow, 0)
    fr = cube_frames(p, ["bow"])
    tips = [o + M @ np.array([.5, .5, .5]) for o, M in fr]
    a, b = tips[4], tips[7]          # الطرفين (حسب ترتيب مكعبات القوس)
    v = (b - a) / (np.linalg.norm(b - a) + 1e-9)
    up_err = 1 - abs(v[1])
    center = np.mean(tips, 0)
    return worst, up_err, center

base_arm, base_bow = [-12, -6, -12], [88, 0, 0]
print("الحالي:", evaluate(base_arm, base_bow)[:2])
best = None
for ax in (-30, -20, -12, -5, 0):
    for az in (-24, -18, -12, -6):
        for ay in (-15, 0, 15):
            for bx in (70, 80, 90, 100):
                for bz in (-20, -10, 0, 10):
                    worst, upe, c = evaluate([ax, ay, az], [bx, 0, bz])
                    score = worst * 10 + upe * 6 + abs(ax) * 0.01 + abs(az + 10) * 0.02
                    if best is None or score < best[0]:
                        best = (score, worst, upe, [ax, ay, az], [bx, 0, bz], c)
print("الأفضل: اختراق", best[1], "| بعد عن العمودي", round(best[2], 3), "| ذراع", best[3], "| قوس", best[4], "| مركز", np.round(best[5], 1))
json.dump({"arm_l": best[3], "bow": best[4]}, open(sys.argv[1], "w"))

# ── بحث ثاني أوسع + تفصيل الاختراق حسب الجزء ──
def breakdown(arm, bow):
    res = {}
    for t in np.linspace(0, 1.6, 9):
        for spd in (0.0, 1.0):
            p = pose_at(t, arm, bow, spd)
            pts = samples(cube_frames(p, ["bow"]))
            for part in BODY:
                k = inside_count(pts, cube_frames(p, [part]))
                res[part] = max(res.get(part, 0), k)
    return {k: v for k, v in res.items() if v}
best2 = None
for ax in (-25, -15, -8, 0, 8):
    for az in (-44, -38, -32, -26):
        for ay in (-20, -8, 0, 8):
            for bx in (80, 88, 96):
                for bz in (-30, -15, 0, 15):
                    worst, upe, c = evaluate([ax, ay, az], [bx, 0, bz])
                    score = worst * 10 + upe * 6 + abs(az + 20) * 0.03 + abs(ax) * 0.01
                    if best2 is None or score < best2[0]:
                        best2 = (score, worst, upe, [ax, ay, az], [bx, 0, bz], c)
print("بحث أوسع: اختراق", best2[1], "| بعد عن العمودي", round(best2[2], 3), "| ذراع", best2[3], "| قوس", best2[4])
print("تفصيل:", breakdown(best2[3], best2[4]))
json.dump({"arm_l": best2[3], "bow": best2[4]}, open(sys.argv[1], "w"))
