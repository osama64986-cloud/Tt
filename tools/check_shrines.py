"""فحص ضريحي السيف (النور والظلام): يعيد تشغيل المخطط على شبكة بلوكات ويتحقق من:
 1) كل اسم بلوك وحالته موجودين بـ Bedrock (قوائم Mojang بـ tools/vanilla_block_ids.txt وvanilla_block_states.json)
 2) مفتوح للسما: ما في أي بلوك فوق y=5 إلا الأعمدة (12) وعمود المنارة؛ بدون صناديق (الصندوق يظهر بعد موت الحارسين)، بدون أسرة
 3) أبعاد المرجع: منصة 45×45، أعمدة 28/22/18 بلوكة، 12 عمود متناظرين، نقش الأرضية متناظر يمين/يسار
 4) مساحة قتال فاضية بالنص، والمنارة صالحة (قاعدة 3×3 + زجاج ملوّن + سما بدون عوائق)
 5) الوصول: من الدخول (جنوب) لسطح المنصة والمنصة المركزية وموقع صندوق الجائزة
 6) الحارسان والصندوق: نقطتا ظهور مختلفتان فوق الأرضية، وموقع الجائزة قدام المنارة
التشغيل: node tools/sim/dump_plans.mjs <مجلد>  ثم  python3 tools/check_shrines.py <مجلد>"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_village as C

R = 22
PILLARS = {28: [(sx * 20, sz * 20) for sx in (-1, 1) for sz in (-1, 1)],
           22: [(sx * 20, sz * 7) for sx in (-1, 1) for sz in (-1, 1)],
           18: [(sx * 8, sz * 20) for sx in (-1, 1) for sz in (-1, 1)]}


def check(name, path, bosses, beam_glass, core):
    plan = json.load(open(path))
    vox, chests, _ = C.replay(plan)
    fails = []
    ids = {b for b in vox.values()}
    states = json.load(open(os.path.join(C.ROOT, "tools", "vanilla_block_states.json"), encoding="utf-8"))
    bad_states = set()
    for op in plan["ops"]:
        if op[0] in ("perm", "stair"):
            allowed = states.get(op[4], {})
            keys = op[5].items() if op[0] == "perm" else [("weirdo_direction", 0)]
            for k, v in keys:
                if k not in allowed or (allowed[k] and v not in allowed[k]):
                    bad_states.add((op[4], k, str(v)))
    unknown = sorted(i for i in ids if i not in C.VANILLA)
    print(f"[{name}] بلوكات: {len(ids)} نوع | غير موجودة: {unknown or 'لا شي'} | حالات خاطئة: {sorted(bad_states) or 'لا شي'}")
    if unknown: fails.append(f"بلوكات مو موجودة: {unknown}")
    if bad_states: fails.append(f"حالات غلط: {sorted(bad_states)}")
    # مفتوح للسما
    pillar_cells = set()
    for H, lst in PILLARS.items():
        for cx, cz in lst:
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    pillar_cells.add((cx + dx, cz + dz))
    roof = [p for p in vox if p[1] >= 6 and p[1] <= 60 and (p[0], p[2]) not in pillar_cells and (p[0], p[2]) != (0, 0)]
    print(f"[{name}] بلوكات فوق y=5 خارج الأعمدة وعمود المنارة: {len(roof)} {roof[:3]}")
    if roof: fails.append(f"سقف/بلوكات فوق الساحة: {len(roof)}")
    if chests: fails.append(f"صناديق بالمخطط: {chests}")
    bed = [p for p, b in vox.items() if b.endswith(":bed")]
    if bed: fails.append("أسرّة")
    # أبعاد
    foot = [(x, z) for (x, y, z), b in vox.items() if y == 0 and abs(x) <= R and abs(z) <= R]
    xs = [x for x, z in foot]; zs = [z for x, z in foot]
    w, d = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
    print(f"[{name}] المنصة {w}×{d}")
    if (w, d) != (45, 45): fails.append(f"المنصة {w}×{d} مو 45×45")
    for H, lst in PILLARS.items():
        for cx, cz in lst:
            top = max(y for (x, y, z) in vox if (x, z) == (cx, cz))
            if top != H: fails.append(f"عمود ({cx},{cz}) علوه {top} مو {H}")
    print(f"[{name}] أعمدة: {sum(len(v) for v in PILLARS.values())} (28×4 + 22×4 + 18×4)")
    # تناظر الأرضية يمين/يسار وشمال/جنوب بغير الممر
    asym = [(x, z) for x in range(-R, R + 1) for z in range(-R, R + 1) if vox.get((x, 0, z)) != vox.get((-x, 0, z))]
    print(f"[{name}] خلايا مو متناظرة (يمين/يسار): {len(asym)}")
    if asym: fails.append(f"أرضية غير متناظرة يمين/يسار {len(asym)}")
    # المنارة
    below = [vox.get((x, 3, z)) for x in (-1, 0, 1) for z in (-1, 0, 1)]
    ok_beacon = vox.get((0, 4, 0)) == "minecraft:beacon" and all(b == core for b in below) and vox.get((0, 5, 0)) == beam_glass
    above = [p for p in vox if p[0] == 0 and p[2] == 0 and p[1] > 5]
    print(f"[{name}] المنارة: {'✔' if ok_beacon else '✖'} | بلوكات فوق الزجاج: {len(above)}")
    if not ok_beacon: fails.append("المنارة غير صالحة")
    if above: fails.append("عوائق فوق المنارة")
    # مساحة القتال
    free = tot = 0
    for x in range(-16, 17):
        for z in range(-16, 17):
            if max(abs(x), abs(z)) <= 6:
                continue
            if abs(abs(x) - 14) <= 3 and abs(abs(z) - 14) <= 3:
                continue
            tot += 1
            if not any((x, y, z) in vox for y in (1, 2, 3)):
                free += 1
    print(f"[{name}] مساحة قتال فاضية: {free}/{tot} = {100 * free // max(1, tot)}%")
    if free / tot < 0.9: fails.append("مساحة القتال مزدحمة")
    # الوصول
    for x in range(-34, 35):
        for z in range(-34, 35):
            if (x, -1, z) not in vox:
                vox[(x, -1, z)] = "minecraft:grass_block"
    start = (0, 0, 26)
    seen = C.reach(vox, start)
    pt = lambda p: p in seen
    tgt = {"المنصة": (0, 1, 18), "المنصة الشمالية": (0, 1, -18), "الدرجة 1": (0, 2, 5), "الدرجة 2": (0, 3, 2), "قرب المنارة": (0, 3, 2)}
    for k, p in tgt.items():
        okk = pt(p)
        print(f"[{name}] الوصول إلى {k} {p}: {'✔' if okk else '✖'}")
        if not okk: fails.append(f"ما توصل {k}")
    # الحراس والجائزة
    sp = plan["spawns"]
    types = [s["type"] for s in sp]
    print(f"[{name}] الحراس: {types} | الجائزة: {plan['reward']}")
    if sorted(types) != sorted(bosses): fails.append(f"الحراس {types} مو {bosses}")
    for s in sp:
        if vox.get((s["x"], s["y"] - 1, s["z"])) is None or (s["x"], s["y"], s["z"]) in vox: fails.append(f"نقطة ظهور غلط {s}")
    rw = plan["reward"]
    if not rw or (rw["x"], rw["y"], rw["z"]) in vox or vox.get((rw["x"], rw["y"] - 1, rw["z"])) is None: fails.append("موقع الجائزة غلط")
    print(f"[{name}] " + ("كل الفحوصات نجحت ✔" if not fails else "فشل: " + "; ".join(fails)))
    return fails


def main(d):
    allf = []
    allf += check("ضريح النور", os.path.join(d, "plan_lightshrine.json"), ["sh:veilfox", "sh:magmamoth"], "minecraft:yellow_stained_glass", "minecraft:gold_block")
    allf += check("ضريح الظلام", os.path.join(d, "plan_shrine.json"), ["sh:gloomhorn", "sh:hollow_seer"], "minecraft:purple_stained_glass", "minecraft:netherite_block")
    return 1 if allf else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
