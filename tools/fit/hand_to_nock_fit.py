import sys, json, numpy as np
src = open(sys.argv[1]).read()
exec(src.split("# الهدف: رأس الريش")[0].replace("exec(open(sys.argv[1]).read()", "exec(open(sys.argv[2]).read()"))
D0 = copy.deepcopy(json.load(open(RP + "/animations/sh.animation.json"))["animations"]["animation.sh_archer.draw"])
keys = {t: (v, D0["bones"]["fore_r"]["rotation"][t][0]) for t, v in D0["bones"]["arm_r"]["rotation"].items()}
HANDP = [-6, 10.4, 0]
def nock(p, dd): return point_world(p, "bow", [6, 15.0656 + dd, 0])
def fit(t, dd):
    """بحث محلي: يبدي من الزوايا الحالية ويجرب ± خطوة لكل زاوية، والخطوة تصغر (16 ← 8 ← 4 ← 2 ← 1)."""
    def score(v):
        k2 = dict(keys); k2[t] = (v[:3], v[3])
        an = mk(k2); p = pose(an, float(t))
        dist = float(np.linalg.norm(point_world(p, "fore_r", HANDP) - nock(p, dd)))
        pen = hits(p, ["fore_r"], ["head"]) + hits(p, ["arrow"], ["head", "body"])
        return dist + pen * 0.8, dist, pen
    cur = list(keys[t][0]) + [keys[t][1]]
    best = score(cur)
    for step in (16, 8, 4, 2, 1):
        improved = True
        while improved:
            improved = False
            for i in range(4):
                for sg in (-1, 1):
                    v = list(cur); v[i] += sg * step
                    sc = score(v)
                    if sc[0] < best[0] - 1e-6: best, cur, improved = sc, v, True
    return (best[0], best[1], best[2], cur[:3], cur[3])
for t, dd in (("0.73", 0.0), ("1.6", 2.93)):
    print("قبل", t, "بعد الإيد عن الفوق:", round(float(np.linalg.norm(point_world(pose(mk(keys), float(t)), "fore_r", HANDP) - nock(pose(mk(keys), float(t)), dd))), 2))
    b = fit(t, dd); keys[t] = (b[3], b[4])
    print("بعد", t, "مسافة", round(float(b[1]), 2), "اختراق", b[2], "ذراع", b[3], "ساعد", b[4])
json.dump({k: {"arm_r": v[0], "fore_r": v[1]} for k, v in sorted(keys.items(), key=lambda x: float(x[0]))}, open(sys.argv[3], "w"))
