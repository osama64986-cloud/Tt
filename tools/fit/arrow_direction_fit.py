import sys, json, copy, numpy as np
src = open(sys.argv[1]).read()
exec(src.split("# الهدف: رأس الريش")[0].replace("exec(open(sys.argv[1]).read()", "exec(open(sys.argv[2]).read()"))
ANIM = json.load(open(RP + "/animations/sh.animation.json"))
D = ANIM["animations"]["animation.sh_archer.draw"]
def posef(an, t): return pose(an, t)
def tipdir(p):
    a = point_world(p, "hand_arrow", [-6, 10.6, 0]); b = point_world(p, "hand_arrow", [-6, 2.6, 0])
    v = b - a; return v / np.linalg.norm(v)
p0 = posef(D, 0.3)
qa = point_world(p0, "quiver", [-3.6, 25, 5.4]) - point_world(p0, "quiver", [-3.6, 15, 5.4]); qa /= np.linalg.norm(qa)
def bowdir(p):
    a = point_world(p, "bow", [6, 10, 0]); b = point_world(p, "bow", [6, -4, 0]); v = b - a; return v / np.linalg.norm(v)
OB = ["head", "body", "cape_b", "cape_r", "cape_f"]
targets = {"0.31": ("q", -qa), "0.45": ("q", -qa), "0.6": ("free", None), "0.68": ("free", None), "0.72": ("bow", None)}
keys = {}
def set_keys(an, ks):
    an["bones"]["hand_arrow"]["rotation"] = {t: v for t, v in sorted(ks.items(), key=lambda x: float(x[0]))}
def score(t, v):
    ks = dict(keys); ks[t] = v
    an = copy.deepcopy(D); set_keys(an, ks); p = posef(an, float(t))
    kind, tg = targets[t]
    if kind == "bow": tg = bowdir(p)
    ang = 0 if tg is None else float(np.degrees(np.arccos(np.clip(np.dot(tipdir(p), tg), -1, 1))))
    obst = ["head"] if kind == "q" else OB          # وقت السحب من الجعبة السهم طبيعي يكون داخلها/جنب الظهر
    pen = hits(p, ["hand_arrow"], obst)
    return ang * 0.2 + pen * 1.0, ang, pen
for t in ("0.31", "0.45", "0.72", "0.6", "0.68"):
    cur = [0, 0, 0]; best = score(t, cur)
    for step in (40, 20, 10, 5, 2):
        imp = True
        while imp:
            imp = False
            for i in range(3):
                for sg in (-1, 1):
                    v = list(cur); v[i] += sg * step; sc = score(t, v)
                    if sc[0] < best[0] - 1e-6: best, cur, imp = sc, v, True
    keys[t] = cur
    print(t, "زاوية الخطأ", round(best[1], 1), "اختراق", best[2], "دوران", cur)
# فحص المسار كامل
an = copy.deepcopy(D); set_keys(an, keys)
print({t: hits(posef(an, t), ["hand_arrow"], OB if t > 0.5 else ["head"]) for t in (0.32, 0.38, 0.45, 0.52, 0.6, 0.64, 0.68, 0.7, 0.72)})
json.dump(keys, open(sys.argv[3], "w"))
