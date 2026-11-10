"""معاينة واجهة القدرة من ملفات الواجهة نفسها (RP/ui/hud_screen.json و server_form.json):
- عمود المهارات تحت يمين لكود معين (نفس قواعد skillBarCode)، شاشة كمبيوتر وشاشة لمس.
- شاشة المهارات (مثل الحقيبة) بأزرار تجريبية.
رسام صغير يفهم الأشياء اللي نستعملها بس: panel/image/label/grid، المراسي، nine-slice، 100%cm/100%sm، والظهور بطرح النص.
مو محرك ماينكرافت: الخط تقريبي (خط PIL)، والهدف نتأكد من الأماكن والصور والحالات.

التشغيل: python3 tools/preview_skillbar.py <مجلد_الصور>
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
FONT = ImageFont.load_default()
GLYPHS = {0xE530: "v", 0xE531: "~", 0xE532: "#", 0xE520: "*"}


def to_py(expr):
    e = re.sub(r"\(not \(\((#\w+) - '([^']*)'\) = \1\)\)", lambda m: f"({m.group(2)!r} in R[{m.group(1)!r}])", expr)
    e = re.sub(r"\(\((#\w+) - '([^']*)'\) = \1\)", lambda m: f"({m.group(2)!r} not in R[{m.group(1)!r}])", e)
    return e


def visible(ctl, R):
    vis = ctl.get("visible", True)
    for b in ctl.get("bindings", []):
        if b.get("target_property_name") == "#visible":
            src = b["source_property_name"]
            if src.startswith("(not ((#texture"):
                vis = bool(R.get("#texture"))
            else:
                vis = bool(eval(to_py(src), {"R": R}))
    return vis


def flag(ctl, R, target):
    for b in ctl.get("bindings", []):
        if b.get("target_property_name") == target:
            return bool(eval(to_py(b["source_property_name"]), {"R": R}))
    return False


def anchor_pos(anchor, x, y, w, h):
    fx, fy = 0.5, 0.5
    for part in anchor.split("_"):
        fx = 0 if part == "left" else 1 if part == "right" else fx
        fy = 0 if part == "top" else 1 if part == "bottom" else fy
    return x + w * fx, y + h * fy


def plain(t):
    t = re.sub(r"§.", "", t)
    return "".join(GLYPHS.get(ord(c), "*" if 0xE500 <= ord(c) <= 0xE5FF else c) for c in t)


def text_size(t, k):
    lines = plain(t).split("\n") if t else [""]
    w = max(FONT.getbbox(ln)[2] if ln else 0 for ln in lines)
    return w * k, 9 * len(lines) * k


def size_of(ctl, pw, ph, sib=(0, 0), R=None):
    sz = ctl.get("size", ["100%", "100%"] if ctl.get("type") != "label" else ["default", "default"])
    out = []
    for i, v in enumerate(sz):
        full = pw if i == 0 else ph
        if isinstance(v, (int, float)):
            out.append(v)
        elif v == "default":
            out.append(text_size(label_text(ctl, R), ctl.get("font_scale_factor", 1.0))[i])
        elif "%sm" in v:
            m = re.match(r"100%sm(?: \+ (\d+)px)?", v)
            out.append(sib[i] + int(m.group(1) or 0))
        elif "%cm" in v:
            out.append(None)
        else:
            m = re.match(r"(\d+)%(?: ([+-]) (\d+)px)?", v)
            val = full * int(m.group(1)) / 100
            if m.group(2):
                val += int(m.group(3)) * (1 if m.group(2) == "+" else -1)
            out.append(val)
    return out


def label_text(ctl, R):
    t = ctl.get("text", "")
    return R.get(t, "") if isinstance(t, str) and t.startswith("#") else t


def draw_image(canvas, tex, x, y, w, h, gray=False):
    p = os.path.join(RP, tex + ".png")
    im = Image.open(p).convert("RGBA")
    js = os.path.join(RP, tex + ".json")
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    if os.path.exists(js):
        n = json.load(open(js))["nineslice_size"]
        bw, bh = im.size
        out = Image.new("RGBA", (w, h))
        cols = [(0, n, 0, n), (n, bw - n, n, w - n), (bw - n, bw, w - n, w)]
        rows = [(0, n, 0, n), (n, bh - n, n, h - n), (bh - n, bh, h - n, h)]
        for sx0, sx1, dx0, dx1 in cols:
            for sy0, sy1, dy0, dy1 in rows:
                if dx1 > dx0 and dy1 > dy0:
                    out.paste(im.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST), (dx0, dy0))
        im = out
    else:
        im = im.resize((w, h), Image.NEAREST)
    if gray:
        g = im.convert("LA").convert("RGBA")
        g.putalpha(im.getchannel("A"))
        im = g
    canvas.alpha_composite(im, (int(round(x)), int(round(y))))


def draw_label(canvas, ctl, R, x, y, w):
    t = label_text(ctl, R)
    k = ctl.get("font_scale_factor", 1.0)
    col = tuple(int(c * 255) for c in ctl.get("color", [1, 1, 1]))
    for i, ln in enumerate(plain(t).split("\n")):
        lw, _ = text_size(ln, k)
        tmp = Image.new("RGBA", (int(lw / k) + 2, 11), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        if ctl.get("shadow"):
            d.text((1, 1), ln, font=FONT, fill=(40, 40, 40, 255))
        d.text((0, 0), ln, font=FONT, fill=(*col, 255))
        tmp = tmp.resize((max(1, int(tmp.width * k)), max(1, int(tmp.height * k))), Image.NEAREST)
        al = ctl.get("text_alignment", "left")
        lx = x + (w - lw) / 2 if al == "center" else x + w - lw if al == "right" else x
        canvas.alpha_composite(tmp, (int(lx), int(y + i * 9 * k)))


def render(canvas, defs, ns, ctl, rect, R, layers, item_of=None, gidx=None, sib_in=(0, 0)):
    if ref := ctl.get("__ref__"):
        base = dict(defs[ref])
        base.update({k: v for k, v in ctl.items() if k != "__ref__"})
        ctl = base
    if not visible(ctl, R):
        return
    px, py, pw, ph = rect
    sib = (0, 0)
    kids = []
    for c in ctl.get("controls", []):
        (name, sub), = c.items()
        if "@" in name:
            nm, ref = name.split("@")
            refns, refname = ref.split(".")
            if refns in (ns,) and refname in defs:
                sub = {**sub, "__ref__": refname}
            elif ref == "common.button":
                sub = {**sub, "controls": [x for x in sub.get("controls", []) if "default" in x]}
            else:
                continue
        kids.append((name, sub))
    # 100%cm: أكبر ابن
    w, h = size_of(ctl, pw, ph, sib_in, R=R)
    if w is None or h is None:
        lab = [s for n, s in kids if s.get("type") == "label"]
        if lab:
            lw, lh = text_size(label_text(lab[0], R), lab[0].get("font_scale_factor", 1.0))
            sib = (lw, lh)
            imgs = [s for n, s in kids if s.get("type") == "image"]
            if imgs:
                w2, h2 = size_of(imgs[0], 0, 0, sib, R)
                w, h = (w if w is not None else w2), (h if h is not None else h2)
            else:
                w, h = lw, lh
    af, at = ctl.get("anchor_from", "center"), ctl.get("anchor_to", "center")
    fx, fy = anchor_pos(af, px, py, pw, ph)
    tx, ty = anchor_pos(at, 0, 0, w, h)
    off = ctl.get("offset", [0, 0])
    if isinstance(off, str):
        off = ctl.get("$sh_off_preview", [0, 0])
    x, y = fx - tx + off[0], fy - ty + off[1]
    layer = ctl.get("layer", 0)
    t = ctl.get("type")
    if t == "image":
        tex = ctl.get("texture")
        if tex == "#texture" or tex is None:
            tex = R.get("#texture")
        if tex:
            layers.append((layer, "img", (tex, x, y, w, h, flag(ctl, R, "#grayscale"))))
    elif t == "label":
        layers.append((layer, "lab", (ctl, dict(R), x, y, w)))
    if t == "grid":
        cols, rows = ctl["grid_dimensions"]
        cw, ch = w / cols, h / rows
        for name, sub in kids:
            gx, gy = sub.get("grid_position", [0, 0])
            idx = gy * cols + gx
            R2 = dict(R)
            if item_of:
                R2.update(item_of(idx))
            render(canvas, defs, ns, sub, (x + gx * cw, y + gy * ch, cw, ch), R2, layers, item_of, idx)
        return
    for name, sub in kids:
        render(canvas, defs, ns, sub, (x, y, w, h), R, layers, item_of, gidx, sib)


def flush(canvas, layers):
    for layer, kind, data in sorted(layers, key=lambda q: q[0]):
        if kind == "img":
            draw_image(canvas, *data)
        else:
            draw_label(canvas, *data)


def hud_preview(code, touch=False, W=427, H=240):
    hud = json.load(open(os.path.join(RP, "ui", "hud_screen.json"), encoding="utf-8"))
    img = Image.new("RGBA", (W, H), (110, 150, 200, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, H * 0.62, W, H], fill=(96, 140, 70, 255))
    hx = W // 2 - 91
    d.rectangle([hx, H - 22, hx + 181, H - 1], fill=(40, 40, 40, 200), outline=(20, 20, 20, 255))
    for i in range(9):
        d.rectangle([hx + 1 + i * 20, H - 21, hx + 20 + i * 20, H - 2], outline=(140, 140, 140, 255))
    bar = dict(hud["sh_skillbar"])
    bar["$sh_off_preview"] = bar["variables"][0]["$sh_sb_off"] if touch else bar["$sh_sb_off|default"]
    if touch:
        d.ellipse([W - 52, H - 52, W - 12, H - 12], outline=(255, 255, 255, 160), width=2)
    layers = []
    render(img, hud, "hud", bar, (0, 0, W, H), {"#sh_raw": code}, layers)
    flush(img, layers)
    return img


def form_preview(title, body, buttons, W=427, H=240):
    sf = json.load(open(os.path.join(RP, "ui", "server_form.json"), encoding="utf-8"))
    img = Image.new("RGBA", (W, H), (60, 70, 90, 255))
    layers = []

    def item_of(i):
        if i >= len(buttons):
            return {"#form_button_text": "", "#texture": None}
        t, icon = buttons[i]
        return {"#form_button_text": t, "#texture": icon}
    R = {"#title_text": title, "#form_text": body}
    render(img, sf, "server_form", sf["sh_sk_form"], (0, 0, W, H), R, layers, item_of)
    flush(img, layers)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    # قدرة النجوم (8): المختارة Orbit، Meteor كولداون 4 ث (نص الظل)، Gravity Well مانا ما تكفي، Constellation كولداون 12، الباقي مقفولة
    code = ("§k§l§8§k§6§b§k§p§6§3§k§n§6§4§k§5§d§k§o§4§k§4§a§k§3§b§k§p§3§7§k§m§3§1§k§n§3§2§k§2§c§k§n§2§7"
            "§k§1§c§k§n§1§9§k§0§c§k§m§0§1§k§n§0§0§r§f")
    K = 3
    for name, im in (("rail_pc", hud_preview(code)), ("rail_touch", hud_preview(code, True)),
                     ("rail_iron", hud_preview("§k§l§0§k§1§b§k§p§1§8§k§n§1§9§k§o§0§k§0§a§r§f"))):
        im.resize((im.width * K, im.height * K), Image.NEAREST).save(os.path.join(out, name + ".png"))
        im.crop((im.width - 160, im.height - 200, im.width, im.height)).resize((160 * 4, 200 * 4), Image.NEAREST).save(os.path.join(out, name + "_zoom.png"))
    star = [("meteor", "§k§b", "§fMeteor", "§c~ 4s"), ("gravwell", "§k§d", "§fGravity Well", "§9✦24"),
            ("orbit", "§k§s", "§eStar Orbit", "§av Selected"), ("constellation", "§k§b", "§fConstellation", "§c~ 12s"),
            ("stardash", "§k§c", "§7Star Dash", "§8# Lv 7"), ("blackhole", "§k§c", "§7Black Hole", "§8# Lv 9"),
            ("supernova", "§k§c", "§7Supernova", "§8# Lv 10")]
    btns = [(f"{tok}§r{nm}\n{st}", f"textures/items/sh_{sid}") for sid, tok, nm, st in star] + [("§k§e§r", None)]
    im = form_preview("§t§s§q§r§f* §9Star Weaver", "§dPower level 5/10 §8· §9Mana 98/120\n§7Tap a skill to select it, then use the Sigil to cast it.", btns)
    im.resize((im.width * K, im.height * K), Image.NEAREST).save(os.path.join(out, "skills_screen.png"))
    print("saved previews to", out)


if __name__ == "__main__":
    main()
