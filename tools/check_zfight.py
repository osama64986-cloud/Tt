"""يكشف الوجوه المتطابقة الظاهرة (z-fighting = بكسلات متداخلة تومض) بموديلات الأسلحة:
وجهين من مكعبين مختلفين بنفس المستوى ونفس الاتجاه ويتداخلون بمساحة، ومو مغطيين بمكعب ثالث.
التشغيل: python3 tools/check_zfight.py [-v] [اسم_دالة_السلاح...]
"""
import sys, itertools
sys.path.insert(0, "/home/user/Tt/tools")
import gen_weapons3d as G
G.Weapon.save = lambda self: None
E = 1e-4
def faces(c):
    o, s = c["origin"], c["size"]
    for ax in range(3):
        for sign in (-1, 1):
            pos = o[ax] + (s[ax] if sign > 0 else 0)
            rng = [(o[i], o[i] + s[i]) for i in range(3) if i != ax]
            yield ax, sign, pos, rng
def inside(pt, c):
    return all(c["origin"][i] + E < pt[i] < c["origin"][i] + c["size"][i] - E for i in range(3))
def zf(w, show=False):
    cs = [c for c in w.cubes if "rotation" not in c]
    n = 0; area = 0; where = []
    for ia, ib in itertools.combinations(range(len(cs)), 2):
        a, b = cs[ia], cs[ib]
        fa = list(faces(a))
        for ax, sg, pos, r in faces(b):
            for ax2, sg2, pos2, r2 in fa:
                if ax == ax2 and sg == sg2 and abs(pos - pos2) < E:
                    lo = [max(r[i][0], r2[i][0]) for i in range(2)]; hi = [min(r[i][1], r2[i][1]) for i in range(2)]
                    if hi[0] - lo[0] <= E or hi[1] - lo[1] <= E: continue
                    # نقاط عينة على المنطقة المشتركة، مزاحة شوية للخارج: إذا كلها داخل مكعب ثالث = مخفية
                    vis = 0
                    for u in (0.25, 0.5, 0.75):
                        for v in (0.25, 0.5, 0.75):
                            q = [lo[0] + (hi[0] - lo[0]) * u, lo[1] + (hi[1] - lo[1]) * v]
                            pt = q[:ax] + [pos + sg * 0.01] + q[ax:]
                            if not any(inside(pt, c) for k, c in enumerate(cs) if k not in (ia, ib)): vis += 1
                    if vis:
                        n += 1; area += (hi[0] - lo[0]) * (hi[1] - lo[1]) * vis / 9
                        if show: where.append((round(pos, 2), "xyz"[ax], sg, ia, ib))
    return n, area, where
names = [a for a in sys.argv[1:] if a != "-v"] or [f.__name__ for f in G.ALL]
for fn in G.ALL:
    if fn.__name__ not in names: continue
    w = fn(); n, a, where = zf(w, True)
    print(f"{w.ident:14} وجوه متطابقة ظاهرة={n:3} مساحة={a:7.2f}")
    if "-v" in sys.argv:
        for x in where[:12]: print("   ", x)
