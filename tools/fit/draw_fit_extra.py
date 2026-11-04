import sys, json, numpy as np
src = open(sys.argv[1]).read()
exec(src.split("# 1) الإمساك")[0].replace("exec(open(sys.argv[1]).read()", "exec(open(sys.argv[3]).read()"))
saved = json.load(open(sys.argv[2]))
keys = {k: (v["arm_r"], v["fore_r"]) for k, v in saved.items()}
OB = ["head", "body", "cape_b", "cape_r", "cape_f", "quiver"]
def pen_over(an, ts): return sum(hits(pose(an, t), ["hand_arrow"], OB) for t in ts)
best = None
for rx in range(-200, -59, 15):
    for ry in range(-30, 151, 20):
        for rz in range(-60, 61, 30):
            for f in range(-100, 11, 25):
                k2 = dict(keys); k2["0.68"] = ([rx, ry, rz], f)
                an = mk(k2)
                pe = pen_over(an, (0.62, 0.65, 0.68, 0.7, 0.72, 0.74))
                if best is None or pe < best[0]: best = (pe, [rx, ry, rz], f)
                if best[0] == 0: break
print("0.68:", best)
keys["0.68"] = (best[1], best[2])
an = mk(keys)
print({t: hits(pose(an, t), ["hand_arrow"], OB) for t in (0.32, 0.45, 0.55, 0.6, 0.65, 0.68, 0.7, 0.72, 0.74)})
json.dump({k: {"arm_r": v[0], "fore_r": v[1]} for k, v in sorted(keys.items(), key=lambda x: float(x[0]))}, open(sys.argv[2], "w"))
