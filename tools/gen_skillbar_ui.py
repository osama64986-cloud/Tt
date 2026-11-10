"""واجهة القدرة (v1.44): عمود المهارات تحت يمين الشاشة + شاشة المهارات (مثل الحقيبة بس للمهارات) + صولجان القدرة.

1) عمود المهارات (RP/ui/hud_screen.json): لوحة مزخرفة بنفس ستايل لوحة الـHUD فوق يسار، شعار القدرة بدائرة فوقها،
   وخانات المهارات (أول مهارة فوق). المختارة بإطار ذهبي وسهم واسمها بجنبها (إنكليزي أو عربي حسب لغة اللاعب)،
   الكولداون ظل ينزل بـ8 خطوات + الثواني، المانا ما تكفي ظل أزرق، المقفولة رمادية بقفل وليفل فتحها.
   الشلون: السكربت يحط "كود" بأول نص العنوان (اللي فوق الهوت بار). الكود كله رموز تنسيق (§ + حرف) فما ينرسم أبداً.
   الواجهة تدور على كل رمز بطرح النص (نفس طريقة علامة العربي §r§r§r المجربة). الطريقة اشتغلت باللعبة (شاف الشريط القديم).
   قواعد الكود (لازم تطابق skillBarCode بـ main.js):
     §k§l§P        القدرة: P = رقمها بـ POWER_KEYS
     §k§o§S        الخانة المختارة
     §k§S§X        حالة الخانة S: a جاهزة، b كولداون، c مقفولة، d المانا ما تكفي (الخانة الفاضية بلا رمز)
     §k§m§S§T      عشرات الرقم (1-9)          §k§n§S§U   آحاد الرقم (ثواني الكولداون أو ليفل القدرة اللي تفتحها)
     §k§p§S§F      كم باقي من الكولداون: F من 1 لـ8 (الظل ينزل خطوة خطوة)
     §k§q§1        لغة اللاعب عربي (اسم المهارة المختارة يطلع بالعربي)
     §r§f          نهاية الكود
   كل رمز يبدي بـ §k وما بداخله §k ثاني، والكتابة العادية ما بيها §k (السم يفحص)، فكل بحث يطابق رمز واحد بس.
   الخانة 0 تحت بالزاوية والخانات تصعد؛ أول مهارة بالقدرة بأعلى خانة (S = عدد المهارات - 1 - ترتيبها).

2) شاشة المهارات (RP/ui/server_form.json): شاشة ActionForm مرسومة (نفس طريقة شاشة الخيميائي): عنوانها يبدي بالعلامة §t§s§q§r،
   8 بطاقات (صفين × 4) مثل خانات الحقيبة: أيقونة كبيرة 32، اسم المهارة وحالتها. تكبس على مهارة = تنختار.
   رموز أول نص كل زر: §k§s مختارة، §k§c مقفولة، §k§b كولداون، §k§d مانا ما تكفي، §k§e خانة فاضية، وبعدها §r.
   تنفتح بـ: سنيك + استعمال صولجان القدرة.

التشغيل: python3 tools/gen_skillbar_ui.py [--check]
  --check: ما يكتب شي، بس يتأكد إن الملفات مطابقة (يستعمله tools/check.py).
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
MAIN = os.path.join(BP, "scripts", "main.js")
HUD = os.path.join(RP, "ui", "hud_screen.json")
FORM = os.path.join(RP, "ui", "server_form.json")
UI_DIR = os.path.join(RP, "textures", "ui", "sh_sk")
UI_TEX = "textures/ui/sh_sk/"
SIGIL_ID = "sh:power_sigil"
SIGIL_TEX = "sh_power_sigil"
ALC_MARK = "§a§l§c§h"
SKILL_MARK = "§t§s§q§r"                                 # لازم تطابق SKILL_SCREEN بـ main.js

sys.path.insert(0, HERE)
import gen_hud_art as HA  # noqa: E402  (شعارات القدرات نفسها اللي بلوحة الـHUD)

# عمود المهارات
SLOT, PITCH, ICON, MAX_SLOTS = 20, 21, 16, 7
PAD, EMB, RAIL_W = 3, 22, 28
OFF_PC, OFF_TOUCH = [-2, -2], [-72, -2]                 # باللمس نبعد عن زر القفز (تحت يمين)
RAW = "#sh_raw"
# شاشة المهارات
CARD_W, CARD_H, CARD_PITCH = 54, 66, 58
ROW_Y = (34, 104)
FOOT_Y = ROW_Y[1] + CARD_H + 4                       # خط الذيل، وتحته المستوى والمانا والتلميح
FW, FH = 8 + 4 * CARD_PITCH - 4 + 8, FOOT_Y + 26

DARK, GOLD, GOLD2, VIOLET = (8, 6, 12, 235), (214, 164, 64, 255), (255, 226, 140, 255), (170, 90, 255, 255)
GOLD_D = (120, 86, 40, 255)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def rail_h(n):
    return PAD + n * PITCH - 1 + 3 + EMB + 3


# ───────────────────────── قراءة المهارات من السكربت ─────────────────────────
def read_skills():
    src = open(MAIN, encoding="utf-8").read()
    m = re.search(r"const POWER_KEYS = \[([^\]]*)\]", src)
    powers = re.findall(r'"([a-z]+)"', m.group(1))
    skills = []
    for sid, power, name, item in re.findall(r'mk\("([a-z]+)", "([a-z]+)", "([^"]+)", "(sh:skill_[a-z]+)"', src):
        skills.append({"id": sid, "power": power, "name": name, "item": item})
    for p in powers:
        lst = [s for s in skills if s["power"] == p]
        n = len(lst)
        if n > MAX_SLOTS:
            raise SystemExit(f"القدرة {p} بيها {n} مهارات، الشريط بس {MAX_SLOTS} خانات")
        for i, s in enumerate(lst):
            s["pi"] = powers.index(p)
            s["slot"] = n - 1 - i
            s["n"] = n
    return powers, skills


def icon_paths():
    tex = json.load(open(os.path.join(RP, "textures", "item_texture.json"), encoding="utf-8"))["texture_data"]
    out = {}
    for fn in os.listdir(os.path.join(BP, "items")):
        if not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(BP, "items", fn), encoding="utf-8"))["minecraft:item"]
        ident = d["description"]["identifier"]
        key = d.get("components", {}).get("minecraft:icon", {}).get("textures", {}).get("default")
        if key and key in tex:
            out[ident] = tex[key]["textures"]
    return out


def arabic_names(names):
    """أسماء المهارات بالعربي جاهزة للعرض (مترجمة ومشكّلة ومقلوبة) من scripts/i18n.js نفسه. None إذا ماكو node."""
    node = shutil.which("node")
    if not node:
        return None
    js = ("import { show } from " + json.dumps("file://" + os.path.join(BP, "scripts", "i18n.js")) + ";"
          "const n = JSON.parse(process.env.SH_NAMES); console.log(JSON.stringify(n.map((x) => show('ar', x, 'hud'))));")
    r = subprocess.run([node, "--input-type=module", "-e", js], capture_output=True, env={**os.environ, "SH_NAMES": json.dumps(names)})
    if r.returncode != 0:
        raise SystemExit("ترجمة الأسماء فشلت: " + r.stderr.decode("utf-8", "replace")[-400:])
    return json.loads(r.stdout.decode("utf-8"))


# ───────────────────────── الرسومات ─────────────────────────
def nine(w, fill_top, fill_bot, a_fill, border, inner=None, gem=True):
    """صورة nine-slice: حافة غامقة، خط ذهب، (خط داخلي)، وتعبئة متدرجة."""
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    for y in range(w):
        for x in range(w):
            im.putpixel((x, y), (*mix(fill_top, fill_bot, y / (w - 1)), a_fill))
    for i in range(w):
        for (x, y) in ((i, 0), (i, w - 1), (0, i), (w - 1, i)):
            im.putpixel((x, y), DARK)
        for (x, y) in ((i, 1), (i, w - 2), (1, i), (w - 2, i)):
            if 1 <= x <= w - 2 and 1 <= y <= w - 2:
                im.putpixel((x, y), border)
        if inner:
            for (x, y) in ((i, 3), (i, w - 4), (3, i), (w - 4, i)):
                if 3 <= x <= w - 4 and 3 <= y <= w - 4:
                    im.putpixel((x, y), inner)
    for (x, y) in ((0, 0), (w - 1, 0), (0, w - 1), (w - 1, w - 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    if gem:
        for (x, y) in ((1, 1), (w - 2, 1), (1, w - 2), (w - 2, w - 2)):
            im.putpixel((x, y), GOLD2)
    return im


def slot_png(size):
    """خانة: حافة غامقة، شطفة ذهبية (فوق يسار فاتح، تحت يمين غامق)، وداخل كحلي متدرج."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            if x in (0, size - 1) or y in (0, size - 1):
                col = DARK
            elif x == 1 or y == 1:
                col = (196, 150, 70, 255)
            elif x == size - 2 or y == size - 2:
                col = (92, 64, 30, 255)
            else:
                d = math.hypot(x - c, y - c) / (size / 2)
                col = (*mix((44, 34, 74), (10, 8, 20), min(1, d)), 228)
            im.putpixel((x, y), col)
    for (x, y) in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    return im


def sel_png(size):
    """إطار المختارة: هالة ذهبية خفيفة برا، خطين ذهب، وجواهر بنفسجية بالزوايا. النص فاضي."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for i in range(size):
        for (x, y) in ((i, 0), (i, size - 1), (0, i), (size - 1, i)):
            im.putpixel((x, y), (255, 226, 140, 110))
        for (x, y) in ((i, 1), (i, size - 2), (1, i), (size - 2, i)):
            if 1 <= x <= size - 2 and 1 <= y <= size - 2:
                im.putpixel((x, y), GOLD2)
        for (x, y) in ((i, 2), (i, size - 3), (2, i), (size - 3, i)):
            if 2 <= x <= size - 3 and 2 <= y <= size - 3:
                im.putpixel((x, y), GOLD)
    for (x, y) in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    for (x, y) in ((1, 1), (size - 2, 1), (1, size - 2), (size - 2, size - 2)):
        im.putpixel((x, y), (255, 250, 230, 255))
    for (x, y) in ((2, 2), (size - 3, 2), (2, size - 3), (size - 3, size - 3)):
        im.putpixel((x, y), VIOLET)
    return im


def arrow_png():
    rows = ["#...", "##..", "#O#.", "#OO#", "#O#.", "##..", "#..."]
    im = Image.new("RGBA", (4, 7), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                im.putpixel((x, y), GOLD)
            elif ch == "O":
                im.putpixel((x, y), GOLD2)
    return im


def cd_png(step, size=16):
    """الكولداون: ظل خفيف على كل الأيقونة + ظل غامق يغطي الباقي (step/8 من تحت)، وخط فاتح على حافته."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 60))
    h = max(1, round(size * step / 8))
    for y in range(size - h, size):
        for x in range(size):
            im.putpixel((x, y), (6, 4, 14, 165))
    if h < size:
        for x in range(size):
            im.putpixel((x, size - h - 1), (255, 236, 180, 120))
    return im


def tint_png(c, size=16):
    return Image.new("RGBA", (size, size), c)


def padlock(im, ox, oy, k=1):
    pad = [".OOO.", "O...O", "O...O", "#####", "#GgG#", "#G.G#", "#GGG#", "#####"]
    pal = {"O": (200, 200, 214, 255), "#": (40, 26, 8, 255), "G": GOLD, "g": GOLD2}
    for y, row in enumerate(pad):
        for x, ch in enumerate(row):
            c = (20, 12, 4, 255) if (ch == "." and y == 5) else pal.get(ch)
            if c:
                for a in range(k):
                    for b in range(k):
                        im.putpixel((ox + x * k + a, oy + y * k + b), c)


def lock_png(size=16, big=False):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 120))
    if big:
        padlock(im, (size - 10) // 2, (size - 16) // 2, 2)
    else:
        padlock(im, 1, 1, 1)
    return im


def emblem_png(key):
    """شعار القدرة بدائرة 22×22: حلقة غامقة، حلقة ذهب، قرص داكن بتوهج خفيف، والشعار (نفس رسمة لوحة الـHUD) بالنص."""
    S = EMB
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    c = (S - 1) / 2
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - c, y - c)
            if d <= 10.9:
                if d > 9.9:
                    col = DARK
                elif d > 8.9:
                    col = GOLD2 if (x + y) % 6 else GOLD
                elif d > 8.0:
                    col = GOLD_D
                else:
                    col = (*mix((58, 44, 96), (12, 9, 24), d / 8.0), 245)
                im.putpixel((x, y), col)
    cell = HA.emblem(key)
    for (x, y), col in cell.px.items():
        im.putpixel((x + 3, y + 3), col if len(col) == 4 else (*col, 255))
    return im


def card_png(fill_top, fill_bot, border):
    """بطاقة المهارة بالشاشة (nine-slice 12، شرائح 4)."""
    return nine(12, fill_top, fill_bot, 240, border, gem=False)


def sigil_png():
    """أيقونة صولجان القدرة 16x16: ميدالية ذهبية بيها جوهرة بنفسجية ونجمة رباعية، وحلقة تعليق فوق."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    cx, cy = 7.5, 8.5
    OUT = (22, 12, 30, 255)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            if d <= 6.6:
                if d > 5.6:
                    im.putpixel((x, y), OUT)
                elif d > 4.4:
                    t = (x - cx + y - cy) / 10 + 0.5
                    im.putpixel((x, y), mix(GOLD2, GOLD, max(0, min(1, t))) if (x + y) % 5 else GOLD2)
                else:
                    t = d / 4.4
                    im.putpixel((x, y), (*mix((196, 120, 255), (70, 24, 130), t), 255))
    for k in range(-3, 4):
        a = 255 if abs(k) < 3 else 200
        im.putpixel((int(cx + 0.5) + k, int(cy)), (255, 244, 255, a) if abs(k) < 2 else (230, 190, 255, a))
        im.putpixel((int(cx + 0.5), int(cy) + k), (255, 244, 255, a) if abs(k) < 2 else (230, 190, 255, a))
    im.putpixel((int(cx + 0.5), int(cy)), (255, 255, 255, 255))
    for (x, y) in ((7, 0), (8, 0), (6, 1), (9, 1), (6, 2), (9, 2)):
        im.putpixel((x, y), GOLD)
    for (x, y) in ((7, 1), (8, 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    im.putpixel((5, 5), (255, 250, 230, 255))
    return im


# ───────────────────────── عمود المهارات (hud_screen.json) ─────────────────────────
def has(tok, var=RAW):
    return f"(not (({var} - '{tok}') = {var}))"


def hasnt(tok, var=RAW):
    return f"(({var} - '{tok}') = {var})"


def binds(*views):
    b = [{"binding_name": "#hud_title_text_string", "binding_name_override": RAW, "binding_type": "global"}]
    for target, expr in views:
        b.append({"binding_type": "view", "source_property_name": expr, "target_property_name": target})
    return b


def img(tex, size, layer, vis, anchor="center", offset=(0, 0), extra=None, anchor_to=None):
    return {"type": "image", "texture": tex, "size": list(size), "layer": layer, "anchor_from": anchor, "anchor_to": anchor_to or anchor,
            "offset": list(offset), "bindings": binds(("#visible", vis), *(extra or []))}


def digit(d, s, tens):
    tok = f"§k§m§{s}§{d}" if tens else f"§k§n§{s}§{d}"
    return {"type": "label", "text": str(d), "localize": False, "shadow": True, "color": [1, 1, 1], "font_scale_factor": 1.0,
            "size": [6, 8], "text_alignment": "right", "layer": 8, "anchor_from": "bottom_right", "anchor_to": "bottom_right",
            "offset": [-5 if tens else 1, 1], "bindings": binds(("#visible", has(tok)))}


def name_tag(text, vis, ar):
    """اسم المختارة يسار الخانة: خلفية tooltip تكبر ويا الكتابة (نفس طريقة خلفية عنوان ماينكرافت: 100%sm)."""
    return {"type": "panel", "size": ["100%cm", "100%cm"], "anchor_from": "left_middle", "anchor_to": "right_middle", "offset": [-8, 0],
            "layer": 7, "bindings": binds(("#visible", vis)),
            "controls": [
                {"bg": {"type": "image", "texture": UI_TEX + "namebg", "size": ["100%sm + 8px", "100%sm + 4px"], "layer": 1}},
                {"tx": {"type": "label", "text": text, "localize": False, "shadow": True, "color": [1.0, 0.9, 0.58],
                        "font_scale_factor": 1.0 if ar else 0.8, "layer": 2}},
            ]}


def build_hud(powers, skills, icons, ar_names):
    ui = {}
    ui["sh_skillbar"] = {
        "type": "panel", "anchor_from": "bottom_right", "anchor_to": "bottom_right", "size": [RAIL_W, rail_h(MAX_SLOTS)], "layer": 4,
        "$sh_sb_off|default": OFF_PC,
        "variables": [{"requires": "$touch", "$sh_sb_off": OFF_TOUCH}],
        "offset": "$sh_sb_off",
        "controls": [],
    }
    ctl = ui["sh_skillbar"]["controls"]
    for pi, key in enumerate(powers):
        n = len([s for s in skills if s["power"] == key])
        ctl.append({f"rail_{key}": img("textures/ui/sh_hud_panel", (RAIL_W, rail_h(n)), 1, has(f"§k§l§{pi}"), anchor="bottom_middle")})
        ctl.append({f"emb_{key}": img(UI_TEX + "emb_" + key, (EMB, EMB), 3, has(f"§k§l§{pi}"), anchor="bottom_middle",
                                      offset=(0, -(PAD + n * PITCH - 1 + 3)))})
    for s in range(MAX_SLOTS):
        ctl.append({f"s{s}@hud.sh_sb_slot{s}": {}})
    for s in range(MAX_SLOTS):
        c = []
        c.append({"bg": img(UI_TEX + "slot", (SLOT, SLOT), 2, has(f"§k§{s}§"))})
        for sk in [k for k in skills if k["slot"] == s]:
            c.append({f"ic_{sk['id']}": img(icons[sk["item"]], (ICON, ICON), 3, has(f"§k§l§{sk['pi']}"), extra=[("#grayscale", has(f"§k§{s}§c"))])})
        for f in range(1, 9):
            c.append({f"cd{f}": img(UI_TEX + f"cd{f}", (ICON, ICON), 4, has(f"§k§p§{s}§{f}"))})
        c.append({"mana": img(UI_TEX + "mana", (ICON, ICON), 4, has(f"§k§{s}§d"))})
        c.append({"lock": img(UI_TEX + "lock", (ICON, ICON), 5, has(f"§k§{s}§c"))})
        c.append({"sel": img(UI_TEX + "sel", (SLOT + 4, SLOT + 4), 6, has(f"§k§o§{s}"))})
        c.append({"arrow": img(UI_TEX + "arrow", (4, 7), 6, has(f"§k§o§{s}"), anchor="left_middle", offset=(-7, 0))})
        for d in range(1, 10):
            c.append({f"t{d}": digit(d, s, True)})
        for d in range(10):
            c.append({f"u{d}": digit(d, s, False)})
        for sk in [k for k in skills if k["slot"] == s]:
            both = f"{has('§k§l§' + str(sk['pi']))} and {has('§k§o§' + str(s))}"
            c.append({f"nm_{sk['id']}": name_tag(sk["name"], f"({both} and {hasnt('§k§q§1')})", False)})
            if ar_names:
                c.append({f"nmar_{sk['id']}": name_tag(ar_names[sk["id"]], f"({both} and {has('§k§q§1')})", True)})
        ui[f"sh_sb_slot{s}"] = {"type": "panel", "size": [SLOT, SLOT], "anchor_from": "bottom_middle", "anchor_to": "bottom_middle",
                                "offset": [0, -(PAD + PITCH * s)], "controls": c}
    return ui


def merge_hud(ui):
    hud = json.load(open(HUD, encoding="utf-8"))
    for k in [k for k in hud if k == "sh_skillbar" or k.startswith("sh_sb_")]:
        del hud[k]
    hud.update(ui)
    ins = hud["root_panel"]["modifications"][0]["value"]
    if not any("sh_skillbar@hud.sh_skillbar" in c for c in ins):
        ins.append({"sh_skillbar@hud.sh_skillbar": {}})
    return hud


# ───────────────────────── شاشة المهارات (server_form.json) ─────────────────────────
BT = "#form_button_text"


def cbind(name, override=None):
    b = {"binding_name": name, "binding_type": "collection", "binding_collection_name": "form_buttons"}
    if override:
        b["binding_name_override"] = override
    return b


def tok_vis(tok, neg=False):
    return {"binding_type": "view", "source_property_name": hasnt(tok, BT) if neg else has(tok, BT), "target_property_name": "#visible"}


def card():
    """بطاقة مهارة (54×66): زر بخلفية بطاقة، خانة كبيرة 36 بيها أيقونة المهارة 32، وتحتها اسمها وحالتها (من نص الزر)."""
    def frame(tex):
        return {"type": "image", "texture": UI_TEX + tex, "layer": 1, "size": ["100%", "100%"]}
    return {
        "type": "panel", "size": [CARD_W, CARD_H], "anchor_from": "top_left", "anchor_to": "top_left",
        "controls": [
            {"sh_btn@common.button": {
                "size": ["100%", "100%"], "$pressed_button_name": "button.form_button_click", "layer": 1,
                "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
                "controls": [{"default": frame("card")}, {"hover": frame("card_hover")}, {"pressed": frame("card_pressed")}],
            }},
            {"sh_slot": {"type": "image", "texture": UI_TEX + "bigslot", "size": [36, 36], "anchor_from": "top_middle", "anchor_to": "top_middle",
                         "offset": [0, 3], "layer": 3}},
            {"sh_icon": {"type": "image", "size": [32, 32], "anchor_from": "top_middle", "anchor_to": "top_middle", "offset": [0, 5], "layer": 4,
                         "bindings": [cbind("#form_button_texture", "#texture"), cbind("#form_button_texture_file_system", "#texture_file_system"),
                                      cbind(BT),
                                      {"binding_type": "view", "source_property_name": "(not ((#texture = '') or (#texture = 'loading')))",
                                       "target_property_name": "#visible"},
                                      {"binding_type": "view", "source_property_name": has("§k§c", BT), "target_property_name": "#grayscale"}]}},
            {"sh_cool": {"type": "image", "texture": UI_TEX + "bigcool", "size": [32, 32], "anchor_from": "top_middle", "anchor_to": "top_middle",
                         "offset": [0, 5], "layer": 5, "bindings": [cbind(BT), tok_vis("§k§b")]}},
            {"sh_mana": {"type": "image", "texture": UI_TEX + "bigmana", "size": [32, 32], "anchor_from": "top_middle", "anchor_to": "top_middle",
                         "offset": [0, 5], "layer": 5, "bindings": [cbind(BT), tok_vis("§k§d")]}},
            {"sh_lock": {"type": "image", "texture": UI_TEX + "biglock", "size": [32, 32], "anchor_from": "top_middle", "anchor_to": "top_middle",
                         "offset": [0, 5], "layer": 6, "bindings": [cbind(BT), tok_vis("§k§c")]}},
            {"sh_sel": {"type": "image", "texture": UI_TEX + "bigsel", "size": [40, 40], "anchor_from": "top_middle", "anchor_to": "top_middle",
                        "offset": [0, 1], "layer": 7, "bindings": [cbind(BT), tok_vis("§k§s")]}},
            {"sh_empty": {"type": "image", "texture": UI_TEX + "empty", "size": [CARD_W, CARD_H], "layer": 8,
                          "bindings": [cbind(BT), tok_vis("§k§e")]}},
            {"sh_text": {"type": "label", "text": BT, "size": [CARD_W - 2, "default"], "anchor_from": "top_middle", "anchor_to": "top_middle",
                         "offset": [0, 41], "text_alignment": "center", "font_scale_factor": 0.7, "color": [1, 1, 1], "shadow": True,
                         "localize": False, "layer": 9, "bindings": [cbind(BT), tok_vis("§k§e", neg=True)]}},
        ],
    }


def build_form(form):
    form = dict(form)
    # القائمة العادية تختفي إذا العنوان بيه علامة الخيميائي أو علامة شاشة المهارات
    lf = form["long_form"]["modifications"][0]["value"]
    lf[1]["source_property_name"] = f"({hasnt(ALC_MARK, '#title_text')} and {hasnt(SKILL_MARK, '#title_text')})"
    ms = form["main_screen_content"]["modifications"][0]["value"]
    if not any("sh_skills_factory" in c for c in ms):
        ms.append({"sh_skills_factory": {"type": "panel", "factory": {"name": "server_form_factory", "control_ids": {"long_form": "@server_form.sh_sk_form"}}}})
    for k in [k for k in form if k.startswith("sh_sk_")]:
        del form[k]

    def row(y, first):
        return {"type": "grid", "collection_name": "form_buttons", "grid_dimensions": [first + 4, 1],
                "size": [(first + 4) * CARD_PITCH, CARD_H + 2], "offset": [8 - first * CARD_PITCH, y],
                "anchor_from": "top_left", "anchor_to": "top_left", "layer": 3,
                "controls": [{f"sh_card_{first + i}@server_form.sh_sk_card": {"grid_position": [first + i, 0]}} for i in range(4)]}

    def body(ar):
        return {"type": "label", "text": "#form_text", "size": [FW - 20, "default"], "anchor_from": "top_left", "anchor_to": "top_left",
                "offset": [10, FOOT_Y + 3], "color": [0.86, 0.84, 0.92], "shadow": True, "localize": False, "layer": 3,
                "text_alignment": "right" if ar else "left", "font_scale_factor": 0.9 if ar else 0.75,
                "bindings": [{"binding_name": "#form_text"},
                             {"binding_type": "view", "source_property_name": has("§r§r§r", "#form_text") if ar else hasnt("§r§r§r", "#form_text"),
                              "target_property_name": "#visible"}]}

    form["sh_sk_form"] = {
        "type": "panel", "size": [FW, FH], "anchor_from": "center", "anchor_to": "center", "layer": 2,
        "bindings": [{"binding_name": "#title_text"},
                     {"binding_type": "view", "source_property_name": has(SKILL_MARK, "#title_text"), "target_property_name": "#visible"}],
        "controls": [
            {"sh_bg": {"type": "image", "texture": UI_TEX + "win", "size": ["100%", "100%"], "layer": 1}},
            {"sh_title": {"type": "label", "text": "#title_text", "size": [FW - 40, "default"], "offset": [10, 9], "anchor_from": "top_left",
                          "anchor_to": "top_left", "color": [1, 1, 1], "shadow": True, "localize": False, "layer": 3,
                          "bindings": [{"binding_name": "#title_text"}]}},
            {"close@common.close_button": {}},
            {"sh_line": {"type": "image", "texture": UI_TEX + "line", "size": [FW - 16, 1], "offset": [8, 26], "anchor_from": "top_left",
                         "anchor_to": "top_left", "layer": 2}},
            {"sh_row_a": row(ROW_Y[0], 0)},
            {"sh_row_b": row(ROW_Y[1], 4)},
            {"sh_line2": {"type": "image", "texture": UI_TEX + "line", "size": [FW - 16, 1], "offset": [8, FOOT_Y], "anchor_from": "top_left",
                          "anchor_to": "top_left", "layer": 2}},
            {"sh_body_en": body(False)},
            {"sh_body_ar": body(True)},
        ],
    }
    form["sh_sk_card"] = card()
    return form


def sigil_item():
    return {"format_version": "1.21.60", "minecraft:item": {
        "description": {"identifier": SIGIL_ID, "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:icon": {"textures": {"default": SIGIL_TEX}},
            "minecraft:max_stack_size": 1,
            "minecraft:glint": True,
            "minecraft:display_name": {"value": "§dPower Sigil"},
        }}}


def nine_json(slice_, base):
    return {"nineslice_size": slice_, "base_size": [base, base]}


def outputs(need_ar=True):
    powers, skills = read_skills()
    icons = icon_paths()
    missing = [s["item"] for s in skills if s["item"] not in icons]
    if missing:
        raise SystemExit(f"مهارات بلا أيقونة: {missing}")
    ar = None
    if need_ar:
        lst = arabic_names([s["name"] for s in skills])
        ar = dict(zip([s["id"] for s in skills], lst)) if lst else None
    files = {
        "slot": slot_png(SLOT), "sel": sel_png(SLOT + 4), "arrow": arrow_png(),
        "mana": tint_png((30, 64, 200, 110)), "lock": lock_png(),
        "bigslot": slot_png(36), "bigsel": sel_png(40), "bigcool": tint_png((6, 4, 14, 150), 32),
        "bigmana": tint_png((30, 64, 200, 110), 32), "biglock": lock_png(32, True),
        "namebg": nine(9, (24, 18, 40), (10, 8, 20), 215, (150, 110, 50, 230), gem=False),
        "win": nine(16, (30, 23, 52), (12, 9, 24), 250, GOLD, inner=GOLD_D),
        "card": card_png((40, 31, 66), (20, 15, 36), (76, 58, 112, 255)),
        "card_hover": card_png((58, 45, 92), (30, 22, 52), GOLD),
        "card_pressed": card_png((18, 13, 32), (12, 9, 22), GOLD2),
        "empty": card_png((14, 11, 24), (10, 8, 18), (40, 32, 58, 255)),
        "line": Image.new("RGBA", (4, 1), GOLD),
    }
    for f in range(1, 9):
        files[f"cd{f}"] = cd_png(f)
    for key in powers:
        files["emb_" + key] = emblem_png(key)
    imgs = {os.path.join(UI_DIR, k + ".png"): v for k, v in files.items()}
    imgs[os.path.join(RP, "textures", "items", SIGIL_TEX + ".png")] = sigil_png()
    js = {
        os.path.join(UI_DIR, "namebg.json"): nine_json(3, 9),
        os.path.join(UI_DIR, "win.json"): nine_json(5, 16),
        os.path.join(UI_DIR, "card.json"): nine_json(4, 12),
        os.path.join(UI_DIR, "card_hover.json"): nine_json(4, 12),
        os.path.join(UI_DIR, "card_pressed.json"): nine_json(4, 12),
        os.path.join(UI_DIR, "empty.json"): nine_json(4, 12),
        os.path.join(BP, "items", "sh_power_sigil.json"): sigil_item(),
        FORM: build_form(json.load(open(FORM, encoding="utf-8"))),
    }
    if need_ar:
        js[HUD] = merge_hud(build_hud(powers, skills, icons, ar))
    tex = json.load(open(os.path.join(RP, "textures", "item_texture.json"), encoding="utf-8"))
    tex["texture_data"][SIGIL_TEX] = {"textures": "textures/items/" + SIGIL_TEX}
    js[os.path.join(RP, "textures", "item_texture.json")] = tex
    return powers, skills, imgs, js


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + "\n"


def main():
    check = "--check" in sys.argv
    need_ar = bool(shutil.which("node"))
    if not need_ar:
        print("gen_skillbar_ui: ماكو node، ما نقدر نترجم الأسماء للعربي؛ عمود المهارات ما ينفحص/ينكتب هالمرة")
    powers, skills, imgs, js = outputs(need_ar)
    bad = []
    if not check:
        old = [f for f in os.listdir(UI_DIR)] if os.path.isdir(UI_DIR) else []
        keep = {os.path.basename(p) for p in list(imgs) + list(js)}
        for f in old:
            if f not in keep:
                os.remove(os.path.join(UI_DIR, f))
    for path, im in imgs.items():
        if check:
            if not os.path.exists(path) or Image.open(path).convert("RGBA").tobytes() != im.convert("RGBA").tobytes():
                bad.append(path)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            im.save(path)
    for path, d in js.items():
        if check:
            if not os.path.exists(path) or json.load(open(path, encoding="utf-8")) != json.loads(dump(d)):
                bad.append(path)
        else:
            open(path, "w", encoding="utf-8").write(dump(d))
    if check:
        if bad:
            print("gen_skillbar_ui: ملفات مو مطابقة (شغل python3 tools/gen_skillbar_ui.py):", *[os.path.relpath(b, ROOT) for b in bad])
            sys.exit(1)
        print("gen_skillbar_ui: مطابق")
        return
    print("skill rail + skills screen ok:", len(skills), "مهارة،", len(powers), "قدرات")


if __name__ == "__main__":
    main()
