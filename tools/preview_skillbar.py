"""معاينة شريط المهارات (تحت يمين) من ملف RP/ui/hud_screen.json نفسه: تقرا عناصر sh_skillbar وتحسب ظهور كل عنصر
بنفس معادلة الواجهة (طرح النص) لكود معين، وترسم شاشة HUD تقريبية (هوت بار + الشريط) مكبرة.
مو محرك ماينكرافت: الهدف التأكد من الترتيب والأماكن والصور. الأرقام بخط بكسل مشابه لخط ماينكرافت.

التشغيل: python3 tools/preview_skillbar.py <ملف_الصورة.png> [touch]
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
W, H, K = 427, 240, 3                 # شاشة GUI صغيرة (1280x720 بمقياس 3)

DIGITS = {  # خط ماينكرافت للأرقام (5x7)
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "11111"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10001", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00011", "00101", "01001", "10001", "11111", "00001", "00001"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "10001", "00001", "00010", "00100", "00100", "00100"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}


def visible(ctl, raw):
    vis = ctl.get("visible", True)
    for b in ctl.get("bindings", []):
        if b.get("target_property_name") == "#visible":
            m = re.match(r"\(not \(\(#sh_raw - '(.*)'\) = #sh_raw\)\)$", b["source_property_name"])
            vis = bool(m) and m.group(1) in raw
    return vis


def gray(ctl, raw):
    for b in ctl.get("bindings", []):
        if b.get("target_property_name") == "#grayscale":
            m = re.match(r"\(not \(\(#sh_raw - '(.*)'\) = #sh_raw\)\)$", b["source_property_name"])
            return bool(m) and m.group(1) in raw
    return False


def anchor_pos(anchor, x, y, w, h):
    """أسماء المراسي ببيدروك: top_left ... left_middle, center, right_middle ... bottom_right."""
    fx, fy = 0.5, 0.5
    for part in anchor.split("_"):
        if part == "left":
            fx = 0
        elif part == "right":
            fx = 1
        elif part == "top":
            fy = 0
        elif part == "bottom":
            fy = 1
    return x + w * fx, y + h * fy


def place(parent, ctl):
    px, py, pw, ph = parent
    w, h = ctl["size"]
    af, at = ctl.get("anchor_from", "center"), ctl.get("anchor_to", "center")
    fx, fy = anchor_pos(af, px, py, pw, ph)
    tx, ty = anchor_pos(at, 0, 0, w, h)
    ox, oy = ctl.get("offset", [0, 0])
    return fx - tx + ox, fy - ty + oy, w, h


def tex(path):
    p = os.path.join(RP, path + ".png")
    im = Image.open(p).convert("RGBA")
    return im


def render(raw, touch=False):
    hud = json.load(open(os.path.join(RP, "ui", "hud_screen.json"), encoding="utf-8"))
    img = Image.new("RGBA", (W, H), (110, 150, 200, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, H * 0.62, W, H], fill=(96, 140, 70, 255))
    hx = W // 2 - 91
    d.rectangle([hx, H - 22, hx + 181, H - 1], fill=(40, 40, 40, 200), outline=(20, 20, 20, 255))
    for i in range(9):
        d.rectangle([hx + 1 + i * 20, H - 21, hx + 20 + i * 20, H - 2], outline=(140, 140, 140, 255))
    bar = hud["sh_skillbar"]
    size = bar["size"]
    off = bar["$sh_sb_off|default"]
    if touch:
        off = bar["variables"][0]["$sh_sb_off"]
        d.ellipse([W - 52, H - 52, W - 12, H - 12], outline=(255, 255, 255, 160), width=2)   # زر القفز تقريباً
    bx, by, bw, bh = place((0, 0, W, H), {"size": size, "anchor_from": "bottom_right", "anchor_to": "bottom_right", "offset": off})
    layers = []
    for s in range(7):
        sl = hud[f"sh_sb_slot{s}"]
        rect = place((bx, by, bw, bh), sl)
        for c in sl["controls"]:
            (name, ctl), = c.items()
            if not visible(ctl, raw):
                continue
            r = place(rect, ctl)
            layers.append((ctl.get("layer", 0), name, ctl, r))
    for _, name, ctl, (x, y, w, h) in sorted(layers, key=lambda t: t[0]):
        if ctl["type"] == "image":
            im = tex(ctl["texture"]).resize((int(w), int(h)), Image.NEAREST)
            if gray(ctl, raw):
                g = im.convert("LA").convert("RGBA")
                g.putalpha(im.getchannel("A"))
                im = g
            img.alpha_composite(im, (int(round(x)), int(round(y))))
        else:
            ch = ctl["text"]
            gx, gy = int(round(x + w - 6)), int(round(y))
            for col, dx in (((63, 63, 63, 255), 1), ((255, 255, 255, 255), 0)):
                for yy, row in enumerate(DIGITS[ch]):
                    for xx, b in enumerate(row):
                        if b == "1":
                            img.putpixel((min(W - 1, gx + xx + dx), min(H - 1, gy + yy + dx)), col)
    return img.resize((W * K, H * K), Image.NEAREST)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "skillbar_preview.png"
    touch = len(sys.argv) > 2 and sys.argv[2] == "touch"
    # مثال: قدرة النجوم (8)، المختارة Orbit، Meteor كولداون 4 ثواني، Gravity Well مانا ما تكفي، Constellation كولداون 12، الباقي مقفولة
    raw = ("§k§l§8§k§6§b§k§n§6§4§k§5§d§k§o§4§k§4§a§k§3§b§k§m§3§1§k§n§3§2§k§2§c§k§n§2§7"
           "§k§1§c§k§n§1§9§k§0§c§k§m§0§1§k§n§0§0§r§f")
    render(raw, touch).save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
