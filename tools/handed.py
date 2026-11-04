#!/usr/bin/env python3
"""إثيريا V1.1: تصحيح يمين/يسار للموديلات والأنيميشن اللي انضبطت بالمعاينة القديمة.

المشكلة: tools/render.py القديم (game=False) كان يرسم ملف البيدروك كما هو، بس اللعبة (مثل Blockbench و tools/fit/hand_sim.py)
تقلب x الداخلي (x_int = -x) وتطبق الدوران Euler(-rx, -ry, rz) والإزاحة (-tx, ty, tz). النتيجة: المعاينة القديمة = مراية
للعبة بس ويا إشارات دوران Y وZ مقلوبة. فكل وضعية انضبطت بعين المعاينة القديمة تطلع باللعبة غلط
(مثلاً: إيد الرامي اليمين ممدودة لبرا بدل ما تسحب الوتر، حضنة الدب معكوسة، رجلين السرعوف متكسرة).

الحل: نقلب إشارة دوران Y وZ (للعظام والمكعبات والأنيميشن) وإشارة إزاحة Z بالأنيميشن. باللعبة بعدها يطلع بالضبط مراية
المعاينة المعتمدة: كل العلاقات (الإيد على الوتر، الحضنة، الضربة لقدام) ترجع صح. والأنيميشن المربوطة بجهة باللعب
(داش يسار/يمين) تتبادل أسماءها بعد القلب لأن المراية تقلب الجهة.

ما ينقلب: الحاصد الأجوف (انضبط بحساب اللعبة الصحيح)، الأسلحة والدروع بالإيد (hand_sim صحيح)، أشكال FX، animation.sh.look،
وأنيميشن الفانيلا.

ما يقلب مرتين: tools/handed.lock.json يحفظ بصمة كل عنصر بعد القلب؛ العنصر اللي بصمته نفسها ينترك. أي مولّد يرجع يكتب
القيم القديمة (المضبوطة بالمعاينة القديمة) تتغير بصمته فينقلب من جديد.
التشغيل:  python3 tools/handed.py            (يقلب اللي يحتاج ويحدّث القفل)
          python3 tools/handed.py --check    (بس يفحص؛ يرجع 1 إذا أكو عنصر ما انقلب) — check.py يستعمله
          python3 tools/handed.py --accept KEY (عنصر عدلته يدوياً بحساب اللعبة الصحيح: نسجل بصمته بدون قلب)
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
LOCK = os.path.join(ROOT, "tools", "handed.lock.json")

GEO_TARGETS = ["sh_imp", "sh_guard", "sh_hound", "sh_scorpion", "sh_archer", "sh_trainer", "sh_alchemist", "sh_gloomhorn",
               "sh_hollow_seer", "sh_veilfox", "sh_magmamoth", "sh_grey_bear", "sh_bear_cub", "sh_prayer_mantis"]
ANIM_PREFIXES = ["animation.sh_imp.", "animation.sh_guard.", "animation.sh_hound.", "animation.sh_scorpion.", "animation.sh_archer.",
                 "animation.sh_trainer.", "animation.sh_gloomhorn.", "animation.sh_hollow_seer.", "animation.sh_veilfox.",
                 "animation.sh_magmamoth.", "animation.sh_grey_bear.", "animation.sh_prayer_mantis.", "animation.sh.player."]
# بعد القلب (مراية) الجهة تنقلب: نبادل محتوى الأزواج المربوطة بجهة باللعب
SWAP_PAIRS = [("animation.sh.player.dash_left", "animation.sh.player.dash_right")]


def neg(v):
    if isinstance(v, (int, float)):
        r = -v
        return 0 if r == 0 else r
    if isinstance(v, str):
        s = v.strip()
        if s in ("0", "0.0"):
            return v
        m = re.fullmatch(r"-\((.*)\)", s)
        if m and balanced(m.group(1)):
            return m.group(1)
        return f"-({s})"
    return v


def balanced(s):
    d = 0
    for ch in s:
        d += ch == "("
        d -= ch == ")"
        if d < 0:
            return False
    return d == 0


def flip_vec(v, idx):
    """يقلب مكونات معينة من [x,y,z] (أرقام أو تعابير Molang)"""
    if isinstance(v, list) and len(v) == 3:
        return [neg(c) if i in idx else c for i, c in enumerate(v)]
    return v


def flip_channel(ch, idx):
    if isinstance(ch, list):
        return flip_vec(ch, idx)
    if isinstance(ch, dict):
        out = {}
        for t, kf in ch.items():
            if isinstance(kf, list):
                out[t] = flip_vec(kf, idx)
            elif isinstance(kf, dict):
                out[t] = {k: (flip_vec(v, idx) if k in ("pre", "post") else v) for k, v in kf.items()}
            else:
                out[t] = kf
        return out
    return ch                                                    # قيمة وحدة لكل المحاور (نادر): ما تنقلب


def flip_anim(a):
    a = json.loads(json.dumps(a))
    for b in a.get("bones", {}).values():
        if "rotation" in b:
            b["rotation"] = flip_channel(b["rotation"], (1, 2))
        if "position" in b:
            b["position"] = flip_channel(b["position"], (2,))
    return a


def flip_geo(g):
    g = json.loads(json.dumps(g))
    for b in g.get("bones", []):
        if "rotation" in b:
            b["rotation"] = flip_vec(b["rotation"], (1, 2))
        if "bind_pose_rotation" in b:
            b["bind_pose_rotation"] = flip_vec(b["bind_pose_rotation"], (1, 2))
        for c in b.get("cubes", []):
            if "rotation" in c:
                c["rotation"] = flip_vec(c["rotation"], (1, 2))
    return g


def digest(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def load_lock():
    return json.load(open(LOCK, encoding="utf-8")) if os.path.exists(LOCK) else {}


def run(mode="apply", accept=None):
    lock = load_lock()
    pending, changed = [], []
    # ── الهندسة ──
    for name in GEO_TARGETS:
        p = os.path.join(RP, "models", "entity", f"{name}.geo.json")
        if not os.path.exists(p):
            continue
        data = json.load(open(p, encoding="utf-8"))
        dirty = False
        for i, g in enumerate(data.get("minecraft:geometry", [])):
            key = f"geo:{name}:{g['description']['identifier']}"
            if accept == key:
                lock[key] = digest(g); continue
            if lock.get(key) == digest(g):
                continue
            pending.append(key)
            if mode == "apply":
                ng = flip_geo(g)
                data["minecraft:geometry"][i] = ng
                lock[key] = digest(ng); dirty = True; changed.append(key)
        if dirty:
            save(p, data)
    # ── الأنيميشن ──
    adir = os.path.join(RP, "animations")
    for fn in sorted(os.listdir(adir)):
        p = os.path.join(adir, fn)
        data = json.load(open(p, encoding="utf-8"))
        A = data.get("animations", {})
        todo = [k for k in A if any(k.startswith(px) for px in ANIM_PREFIXES)]
        dirty = False
        fresh = {}
        for k in todo:
            key = f"anim:{fn}:{k}"
            if accept == key:
                lock[key] = digest(A[k]); continue
            if lock.get(key) == digest(A[k]):
                continue
            pending.append(key)
            fresh[k] = flip_anim(A[k])
        if mode == "apply" and fresh:
            for a, b in SWAP_PAIRS:                              # الزوج لازم ينقلب سوا (المولّد يكتبهم سوا)
                if (a in fresh) != (b in fresh) and (a in A and b in A):
                    sys.exit(f"handed: {a} و {b} لازم ينقلبون سوا (واحد بس رجع جديد) — شغل مولّده من جديد")
                if a in fresh and b in fresh:
                    fresh[a], fresh[b] = fresh[b], fresh[a]
            for k, v in fresh.items():
                A[k] = v
                lock[f"anim:{fn}:{k}"] = digest(v); dirty = True; changed.append(f"anim:{fn}:{k}")
        if dirty:
            save(p, data)
    if mode == "apply" or accept:
        json.dump(lock, open(LOCK, "w", encoding="utf-8"), indent=1, sort_keys=True)
        open(LOCK, "a").write("\n")
    return pending, changed


def save(p, data):
    """يحفظ بنفس تنسيق الملف الأصلي (مضغوط أو بمسافات بنفس العرض) حتى الفرق بـ git يبقى بس اللي تغير"""
    old = open(p, encoding="utf-8").read()
    lines = old.split("\n", 2)
    with open(p, "w", encoding="utf-8") as f:
        if len(lines) < 2 or not lines[1].strip():
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        else:
            ind = len(lines[1]) - len(lines[1].lstrip(" "))
            json.dump(data, f, indent=ind or 1, ensure_ascii=False)
        if old.endswith("\n"):
            f.write("\n")


if __name__ == "__main__":
    if "--check" in sys.argv:
        pending, _ = run("check")
        if pending:
            print("handed: هالعناصر ما انقلبت لحساب اللعبة (شغل python3 tools/handed.py):")
            for k in pending:
                print("  ", k)
            sys.exit(1)
        print("handed: كل الموديلات والأنيميشن بحساب اللعبة الصحيح")
        sys.exit(0)
    if "--accept" in sys.argv:
        key = sys.argv[sys.argv.index("--accept") + 1]
        run("accept", accept=key)
        print("handed: سجلت", key)
        sys.exit(0)
    pending, changed = run("apply")
    print(f"handed: قلبت {len(changed)} عنصر (هندسة + أنيميشن)")
