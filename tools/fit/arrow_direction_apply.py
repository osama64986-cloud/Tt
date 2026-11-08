import sys, json, copy, numpy as np
src = open(sys.argv[1]).read()
exec(src.split("# الهدف: رأس الريش")[0].replace("exec(open(sys.argv[1]).read()", "exec(open(sys.argv[2]).read()"))
k = json.load(open(sys.argv[3]))
a, b = np.array(k["0.45"], float), np.array(k["0.72"], float)
for t in ("0.6", "0.68"):
    f = (float(t) - 0.45) / 0.27
    k[t] = [round(x, 1) for x in (a + (b - a) * f)]
path = RP + "/animations/sh.animation.json"
ANIM = json.load(open(path))
D = ANIM["animations"]["animation.sh_archer.draw"]
D["bones"]["hand_arrow"]["rotation"] = {t: v for t, v in sorted(k.items(), key=lambda x: float(x[0]))}
OB = ["head", "body", "cape_b", "cape_r", "cape_f"]
res = {t: hits(pose(D, t), ["hand_arrow"], OB if t > 0.5 else ["head"]) for t in (0.32, 0.38, 0.45, 0.5, 0.55, 0.6, 0.64, 0.68, 0.7, 0.72)}
print(res)
if sum(res.values()) == 0:
    json.dump(ANIM, open(path, "w"), indent=1); print("انكتب:", D["bones"]["hand_arrow"]["rotation"])
