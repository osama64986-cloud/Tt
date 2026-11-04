#!/usr/bin/env python3
"""إثيريا V1: قاموس العربي.

1) يستخرج كل النصوص اللي يشوفها اللاعب من سكربتات المود (نصوص "..." و `...` مع ${...}):
   كل سطر (بين \\n) يصير مفتاح، والـ${...} تصير خانات {0} {1}...، والقوالب الداخلية تنستخرج لوحدها.
2) يدمجها ويا الترجمات الموجودة بـ tools/i18n/ar.json (المفتاح الإنكليزي ← العربي).
3) يكتب AnimePowers/BP/scripts/lang_ar.js (بس المترجم) ويطبع شنو باقي بدون ترجمة.

التشغيل:  python3 tools/gen_i18n.py            (يبني lang_ar.js ويطبع الناقص)
          python3 tools/gen_i18n.py --missing  (يكتب tools/i18n/missing.json بكل الناقص بالترتيب)
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "AnimePowers", "BP", "scripts")
I18N = os.path.join(ROOT, "tools", "i18n")
FILES = ["main.js", "structures.js", "achievements.js", "gear.js", "dash.js", "story.js"]

# نصوص مو للاعب (معرّفات، مسارات، أحداث، جزيئات، أصوات...)
SKIP_RE = re.compile(
    r"^(minecraft:|sh:|sh\.|textures/|animation\.|controller\.|geometry\.|random\.|note\.|mob\.|block\.|ambient\.|"
    r"dig\.|step\.|use\.|item\.|game\.|fall\.|damage\.|liquid\.|fire\.|beacon\.|armor\.|bucket\.|bottle\.|"
    r"variable\.|query\.|q\.|v\.|math\.|#|@|\.\/|https?:)"
)
ID_RE = re.compile(r"^[a-z0-9_:./-]*$")


def js_strings(src):
    """يرجع (نوع، نص) لكل نص بالملف: q = "..." أو '...'، t = `...` (مع ${} كما هي)."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in "\"'":
            j, buf = i + 1, []
            while j < n and src[j] != ch:
                if src[j] == "\\" and j + 1 < n:
                    buf.append(src[j:j + 2])
                    j += 2
                    continue
                if src[j] == "\n":
                    break
                buf.append(src[j])
                j += 1
            out.append(("q", unescape("".join(buf), ch)))
            i = j + 1
            continue
        if ch == "`":
            j, depth, buf = i + 1, 0, []
            while j < n:
                c = src[j]
                if c == "\\" and j + 1 < n:
                    buf.append(src[j:j + 2])
                    j += 2
                    continue
                if depth == 0 and c == "`":
                    break
                if c == "$" and j + 1 < n and src[j + 1] == "{":
                    depth += 1
                    buf.append("${")
                    j += 2
                    continue
                if c == "}" and depth > 0:
                    depth -= 1
                if c == "`" and depth > 0:                       # قالب داخل ${...}: نقفز عليه كامل
                    k = j + 1
                    d2 = 0
                    while k < n:
                        if src[k] == "\\":
                            k += 2
                            continue
                        if src[k] == "$" and k + 1 < n and src[k + 1] == "{":
                            d2 += 1
                        elif src[k] == "}" and d2 > 0:
                            d2 -= 1
                        elif src[k] == "`" and d2 == 0:
                            break
                        k += 1
                    buf.append(src[j:k + 1])
                    j = k + 1
                    continue
                buf.append(c)
                j += 1
            out.append(("t", "".join(buf)))
            i = j + 1
            continue
        i += 1
    return out


def unescape(s, quote='"'):
    """نص JS بين علامتين ← النص الحقيقي (\\n سطر، \\" علامة...)"""
    if quote != '"':
        s = re.sub(r'(?<!\\)"', '\\"', s.replace("\\'", "'"))
    try:
        return json.loads('"' + s + '"')
    except Exception:
        return s


def split_template(t):
    """`نص ${a} نص ${`داخلي ${b}`}` ← (قالب بخانات، [قوالب/نصوص داخلية])"""
    out, inner, k, i = [], [], 0, 0
    while i < len(t):
        if t.startswith("${", i):
            depth, j = 1, i + 2
            while j < len(t) and depth:
                if t[j] == "`":                                   # قالب داخلي
                    e = j + 1
                    d2 = 0
                    while e < len(t):
                        if t[e] == "\\":
                            e += 2
                            continue
                        if t.startswith("${", e):
                            d2 += 1
                            e += 2
                            continue
                        if t[e] == "}" and d2:
                            d2 -= 1
                        elif t[e] == "`" and not d2:
                            break
                        e += 1
                    inner.append(("t", t[j + 1:e]))
                    j = e + 1
                    continue
                if t[j] in "\"'":
                    q, e = t[j], j + 1
                    while e < len(t) and t[e] != q:
                        e += 2 if t[e] == "\\" else 1
                    inner.append(("q", unescape(t[j + 1:e])))
                    j = e + 1
                    continue
                if t[j] == "{":
                    depth += 1
                elif t[j] == "}":
                    depth -= 1
                j += 1
            out.append("{%d}" % k)
            k += 1
            i = j
            continue
        if t[i] == "\\" and i + 1 < len(t):
            out.append(unescape(t[i:i + 2]))
            i += 2
            continue
        out.append(t[i])
        i += 1
    return "".join(out), inner


def user_facing(line):
    s = line.strip()
    if len(re.sub(r"§.|\{\d\}", "", s)) < 2:
        return False
    if SKIP_RE.match(s) or ID_RE.match(s):
        return False
    plain = re.sub(r"§.|\{\d\}", "", s)
    if not re.search(r"[A-Za-z]{2}", plain):
        return False
    if re.fullmatch(r"[a-z_]+(\.[a-z_]+)+", plain):              # أسماء خصائص/أحداث
        return False
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", plain) and plain[0].islower():   # كلمة وحدة بحروف صغيرة = معرّف
        return False
    return True


def renumber(line):
    """خانات السطر تبدي من {0} (بعد التقطيع على \\n)"""
    seen = {}

    def f(m):
        k = m.group(1)
        if k not in seen:
            seen[k] = len(seen)
        return "{%d}" % seen[k]
    return re.sub(r"\{(\d+)\}", f, line)


def collect():
    keys, order = {}, []

    def add(line, where):
        line = renumber(line)
        if re.search(r"\{\d{2,}\}", line):
            return
        for piece in [line, line.strip()]:
            if user_facing(piece):
                if piece not in keys:
                    keys[piece] = where
                    order.append(piece)
                break

    def walk(kind, text, where):
        if kind == "q":
            for ln in text.split("\n"):
                add(ln, where)
            return
        tpl, inner = split_template(text)
        for ln in tpl.split("\n"):
            add(ln, where)
        for k2, t2 in inner:
            walk(k2, t2, where)

    for f in FILES:
        p = os.path.join(SCRIPTS, f)
        if not os.path.exists(p):
            continue
        src = open(p, encoding="utf-8").read()
        if f == "story.js":                                       # بيانات بلغتين: العربي جاهز، ما يحتاج قاموس
            continue
        for kind, text in js_strings(src):
            walk(kind, text, f)
    return keys, order


def main():
    os.makedirs(I18N, exist_ok=True)
    keys, order = collect()
    ar_path = os.path.join(I18N, "ar.json")
    ar = json.load(open(ar_path, encoding="utf-8")) if os.path.exists(ar_path) else {}
    # نتأكد إن خانات الترجمة نفس خانات الإنكليزي
    bad = [k for k, v in ar.items() if sorted(re.findall(r"\{\d\}", k)) != sorted(re.findall(r"\{\d\}", v))]
    for k in bad:
        print("خانات مو متطابقة:", json.dumps(k, ensure_ascii=False), "→", json.dumps(ar[k], ensure_ascii=False))
    used = {k: v for k, v in ar.items() if v and k not in bad}
    missing = [k for k in order if k not in ar]
    with open(os.path.join(SCRIPTS, "lang_ar.js"), "w", encoding="utf-8") as f:
        f.write("// يتولد تلقائياً من tools/gen_i18n.py و tools/i18n/ar.json — لا تعدله يدوياً\n")
        f.write("export const AR = " + json.dumps(used, ensure_ascii=False, indent=0, sort_keys=True) + ";\n")
    print(f"i18n: {len(order)} نص للاعب | مترجم {len([k for k in order if k in used])} | ناقص {len(missing)} | ترجمات بالقاموس {len(used)}")
    if "--missing" in sys.argv:
        json.dump({k: "" for k in missing}, open(os.path.join(I18N, "missing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("كتبت tools/i18n/missing.json")
    if "--list" in sys.argv:
        for k in missing:
            print(json.dumps(k, ensure_ascii=False))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
