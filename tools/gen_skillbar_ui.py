"""شريط المهارات (v1.43) تحت يمين الشاشة + صولجان القدرة.

المهارات ما تنحط بالحقيبة بعد: أيتم واحد (صولجان القدرة sh:power_sigil) يرمي المهارة المختارة،
وضغطة سنيك قصيرة وانت ماسكه تبدل للمهارة الجاية. الشريط يبين كل مهارات قدرتك: المختارة، الكولداون، المقفولة.

شلون الواجهة تعرف حالة المهارات؟ السكربت يحط "كود" بأول نص العنوان (title) اللي ينكتب فوق الهوت بار.
الكود كله رموز تنسيق ماينكرافت (§ + حرف) فما ينرسم بالشاشة أبداً، وحتى لو الواجهة ما اشتغلت ما يطلع شي غريب.
ملف RP/ui/hud_screen.json يدور على كل رمز بطرح النص (نفس طريقة علامة العربي §r§r§r المجربة بالمود)
ويرسم الأيقونات. صورة الأيقونة ثابتة لكل مهارة (textures/items/sh_<id>).

قواعد الكود (لازم تطابق skillBarCode بـ main.js):
  §k§l§P        القدرة: P = رقمها بـ POWER_KEYS
  §k§o§S        الخانة المختارة
  §k§S§X        حالة الخانة S: a جاهزة، b كولداون، c مقفولة، d المانا ما تكفي (الخانة الفاضية بلا رمز)
  §k§m§S§T      عشرات الرقم (1-9، تنحذف إذا صفر)
  §k§n§S§U      آحاد الرقم (ثواني الكولداون، أو ليفل القدرة اللي تنفتح بيه المقفولة)
  §r§f          نهاية الكود (§r يصفّر التنسيق، و§f حتى ما يتكون §r§r§r بالغلط ويا الكتابة الإنكليزية)
كل رمز يبدي بـ §k وما بداخله §k ثاني، والكتابة العادية ما بيها §k أبداً (السم يفحص)، فكل بحث يطابق رمز واحد بس.
الخانة 0 تحت بالزاوية والخانات تصعد فوق؛ أول مهارة بالقدرة بأعلى خانة (S = عدد المهارات - 1 - ترتيبها).

التشغيل: python3 tools/gen_skillbar_ui.py [--check]
  --check: ما يكتب شي، بس يتأكد إن الملفات مطابقة (يستعمله tools/check.py).
"""
import json
import math
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
MAIN = os.path.join(BP, "scripts", "main.js")
HUD = os.path.join(RP, "ui", "hud_screen.json")
UI_DIR = os.path.join(RP, "textures", "ui", "sh_sk")
SIGIL_ID = "sh:power_sigil"
SIGIL_TEX = "sh_power_sigil"

SLOT, PITCH, MAX_SLOTS = 18, 19, 7
OFF_PC, OFF_TOUCH = [-2, -2], [-72, -2]          # باللمس نبعد عن زر القفز (تحت يمين)
RAW = "#sh_raw"

DARK, GOLD, GOLD2, VIOLET = (8, 6, 12, 230), (214, 164, 64, 255), (255, 226, 140, 255), (170, 90, 255, 255)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


# ───────────────────────── قراءة المهارات من السكربت ─────────────────────────
def read_skills():
    src = open(MAIN, encoding="utf-8").read()
    m = re.search(r"const POWER_KEYS = \[([^\]]*)\]", src)
    powers = re.findall(r'"([a-z]+)"', m.group(1))
    skills = []
    for sid, power, name, item in re.findall(r'mk\("([a-z]+)", "([a-z]+)", "([^"]+)", "(sh:skill_[a-z]+)"', src):
        skills.append({"id": sid, "power": power, "name": name, "item": item})
    by_power = {p: [s for s in skills if s["power"] == p] for p in powers}
    for p, lst in by_power.items():
        n = len(lst)
        if n > MAX_SLOTS:
            raise SystemExit(f"القدرة {p} بيها {n} مهارات، الشريط بس {MAX_SLOTS} خانات")
        for i, s in enumerate(lst):
            s["pi"] = powers.index(p)
            s["slot"] = n - 1 - i
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


# ───────────────────────── الرسومات ─────────────────────────
def slot_png():
    """خلفية الخانة 18x18: حافة غامقة، داخل كحلي شبه شفاف (نفس لون لوحة الـHUD) ولمعة خفيفة فوق يسار."""
    im = Image.new("RGBA", (SLOT, SLOT), (0, 0, 0, 0))
    for y in range(SLOT):
        for x in range(SLOT):
            if x in (0, SLOT - 1) or y in (0, SLOT - 1):
                c = DARK
            else:
                c = (*mix((30, 23, 52), (10, 8, 20), y / (SLOT - 1)), 175)
                if x == 1 or y == 1:
                    c = (58, 46, 92, 200)
                elif x == SLOT - 2 or y == SLOT - 2:
                    c = (6, 4, 12, 200)
            im.putpixel((x, y), c)
    for (x, y) in ((0, 0), (SLOT - 1, 0), (0, SLOT - 1), (SLOT - 1, SLOT - 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    return im


def sel_png():
    """إطار المهارة المختارة 20x20 (يطلع بكسل برا الخانة): ذهب فاتح برا، ذهب جوا، وجوهرة بنفسجية بالزوايا."""
    W = SLOT + 2
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    for i in range(W):
        for (x, y) in ((i, 0), (i, W - 1), (0, i), (W - 1, i)):
            im.putpixel((x, y), GOLD2)
        for (x, y) in ((i, 1), (i, W - 2), (1, i), (W - 2, i)):
            if 1 <= x <= W - 2 and 1 <= y <= W - 2:
                im.putpixel((x, y), GOLD)
    for (x, y) in ((0, 0), (W - 1, 0), (0, W - 1), (W - 1, W - 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    for (x, y) in ((1, 1), (W - 2, 1), (1, W - 2), (W - 2, W - 2)):
        im.putpixel((x, y), VIOLET)
    return im


def arrow_png():
    """سهم صغير 4x7 يأشر على المختارة (يمين)."""
    rows = ["#...", "##..", "#O#.", "#OO#", "#O#.", "##..", "#..."]
    im = Image.new("RGBA", (4, 7), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                im.putpixel((x, y), GOLD)
            elif ch == "O":
                im.putpixel((x, y), GOLD2)
    return im


def fill_png(c):
    return Image.new("RGBA", (16, 16), c)


def lock_png():
    """المقفولة: ظل خفيف + قفل صغير فوق يسار (الرقم تحت يمين = ليفل القدرة اللي تنفتح بيه)."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 105))
    pad = [".OOO.", "O...O", "O...O", "#####", "#GgG#", "#G.G#", "#GGG#", "#####"]
    pal = {"O": (200, 200, 214, 255), "#": (40, 26, 8, 255), "G": GOLD, "g": GOLD2, ".": None}
    for y, row in enumerate(pad):
        for x, ch in enumerate(row):
            c = pal.get(ch)
            if c:
                im.putpixel((1 + x, 1 + y), c)
    im.putpixel((3, 6), (20, 12, 4, 255))
    return im


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
    # نجمة رباعية بالنص
    for k in range(-3, 4):
        a = 255 if abs(k) < 3 else 200
        im.putpixel((int(cx + 0.5) + k, int(cy)), (255, 244, 255, a) if abs(k) < 2 else (230, 190, 255, a))
        im.putpixel((int(cx + 0.5), int(cy) + k), (255, 244, 255, a) if abs(k) < 2 else (230, 190, 255, a))
    im.putpixel((int(cx + 0.5), int(cy)), (255, 255, 255, 255))
    # حلقة التعليق
    for (x, y) in ((7, 0), (8, 0), (6, 1), (9, 1), (6, 2), (9, 2)):
        im.putpixel((x, y), GOLD)
    for (x, y) in ((7, 1), (8, 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    im.putpixel((5, 5), (255, 250, 230, 255))
    return im


# ───────────────────────── الواجهة (JSON UI) ─────────────────────────
def has(tok):
    return f"(not (({RAW} - '{tok}') = {RAW}))"


def binds(*views):
    b = [{"binding_name": "#hud_title_text_string", "binding_name_override": RAW, "binding_type": "global"}]
    for target, expr in views:
        b.append({"binding_type": "view", "source_property_name": expr, "target_property_name": target})
    return b


def img(tex, size, layer, tok, anchor="center", offset=(0, 0), extra=None):
    c = {"type": "image", "texture": tex, "size": list(size), "layer": layer, "anchor_from": anchor, "anchor_to": anchor,
         "offset": list(offset), "bindings": binds(("#visible", has(tok)) if isinstance(tok, str) else tok, *(extra or []))}
    return c


def digit(d, s, tens):
    tok = f"§k§m§{s}§{d}" if tens else f"§k§n§{s}§{d}"
    return {"type": "label", "text": str(d), "localize": False, "shadow": True, "color": [1, 1, 1], "font_scale_factor": 1.0,
            "size": [6, 8], "text_alignment": "right", "layer": 8, "anchor_from": "bottom_right", "anchor_to": "bottom_right",
            "offset": [-5 if tens else 1, 1], "bindings": binds(("#visible", has(tok)))}


def build_ui(powers, skills, icons):
    ui = {}
    bar_h = MAX_SLOTS * PITCH - (PITCH - SLOT)
    ui["sh_skillbar"] = {
        "type": "panel", "anchor_from": "bottom_right", "anchor_to": "bottom_right", "size": [SLOT, bar_h], "layer": 4,
        "$sh_sb_off|default": OFF_PC,
        "variables": [{"requires": "$touch", "$sh_sb_off": OFF_TOUCH}],
        "offset": "$sh_sb_off",
        "controls": [{f"s{s}@hud.sh_sb_slot{s}": {}} for s in range(MAX_SLOTS)],
    }
    for s in range(MAX_SLOTS):
        ctl = []
        ctl.append({"bg": img("textures/ui/sh_sk/slot", (SLOT, SLOT), 1, f"§k§{s}§")})
        for sk in [k for k in skills if k["slot"] == s]:
            tex = icons[sk["item"]]
            ctl.append({f"ic_{sk['id']}": img(tex, (16, 16), 2, f"§k§l§{sk['pi']}", extra=[("#grayscale", has(f"§k§{s}§c"))])})
        ctl.append({"cool": img("textures/ui/sh_sk/shade", (16, 16), 4, f"§k§{s}§b")})
        ctl.append({"mana": img("textures/ui/sh_sk/mana", (16, 16), 4, f"§k§{s}§d")})
        ctl.append({"lock": img("textures/ui/sh_sk/lock", (16, 16), 5, f"§k§{s}§c")})
        ctl.append({"sel": img("textures/ui/sh_sk/sel", (SLOT + 2, SLOT + 2), 6, f"§k§o§{s}")})
        ctl.append({"arrow": img("textures/ui/sh_sk/arrow", (4, 7), 6, f"§k§o§{s}", anchor="left_middle", offset=(-6, 0))})
        for d in range(1, 10):
            ctl.append({f"t{d}": digit(d, s, True)})
        for d in range(10):
            ctl.append({f"u{d}": digit(d, s, False)})
        ui[f"sh_sb_slot{s}"] = {"type": "panel", "size": [SLOT, SLOT], "anchor_from": "bottom_right", "anchor_to": "bottom_right",
                                "offset": [0, -PITCH * s], "controls": ctl}
    return ui


def merge_hud(ui):
    hud = json.load(open(HUD, encoding="utf-8"))
    for k in [k for k in hud if k == "sh_skillbar" or k.startswith("sh_sb_")]:
        del hud[k]
    hud.update(ui)
    mods = hud["root_panel"]["modifications"]
    ins = mods[0]["value"]
    if not any("sh_skillbar@hud.sh_skillbar" in c for c in ins):
        ins.append({"sh_skillbar@hud.sh_skillbar": {}})
    return hud


def sigil_item():
    return {"format_version": "1.21.60", "minecraft:item": {
        "description": {"identifier": SIGIL_ID, "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:icon": {"textures": {"default": SIGIL_TEX}},
            "minecraft:max_stack_size": 1,
            "minecraft:glint": True,
            "minecraft:display_name": {"value": "§dPower Sigil"},
        }}}


def outputs():
    powers, skills = read_skills()
    icons = icon_paths()
    missing = [s["item"] for s in skills if s["item"] not in icons]
    if missing:
        raise SystemExit(f"مهارات بلا أيقونة: {missing}")
    files = {
        os.path.join(UI_DIR, "slot.png"): slot_png(),
        os.path.join(UI_DIR, "sel.png"): sel_png(),
        os.path.join(UI_DIR, "arrow.png"): arrow_png(),
        os.path.join(UI_DIR, "shade.png"): fill_png((0, 0, 0, 140)),
        os.path.join(UI_DIR, "mana.png"): fill_png((30, 64, 200, 110)),
        os.path.join(UI_DIR, "lock.png"): lock_png(),
        os.path.join(RP, "textures", "items", SIGIL_TEX + ".png"): sigil_png(),
    }
    js = {
        HUD: merge_hud(build_ui(powers, skills, icons)),
        os.path.join(BP, "items", "sh_power_sigil.json"): sigil_item(),
    }
    tex = json.load(open(os.path.join(RP, "textures", "item_texture.json"), encoding="utf-8"))
    tex["texture_data"][SIGIL_TEX] = {"textures": "textures/items/" + SIGIL_TEX}
    js[os.path.join(RP, "textures", "item_texture.json")] = tex
    return powers, skills, files, js


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + "\n"


def main():
    check = "--check" in sys.argv
    powers, skills, files, js = outputs()
    bad = []
    for path, im in files.items():
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
    per = {p: [s["id"] for s in sorted([k for k in skills if k["power"] == p], key=lambda k: -k["slot"])] for p in powers}
    print("skill bar ok:", len(skills), "مهارة،", sum(len(v) for v in per.values()), "أيقونة")
    for p, ids in per.items():
        print(f"  {powers.index(p)} {p}: {', '.join(ids)}")


if __name__ == "__main__":
    main()
