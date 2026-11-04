#!/usr/bin/env python3
"""Anime Battles add-on builder.

Generates the cube models (geometry), pixel textures, item icons, particle
texture and pack icons, then zips BP + RP into dist/AnimeBattles.mcaddon.

Run:  python3 tools/build.py
"""
import json
import os
import random
import zipfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "RP")
BP = os.path.join(ROOT, "BP")
DIST = os.path.join(ROOT, "dist")

# ---------------------------------------------------------------- palettes
SKIN = (238, 196, 160)
MOUTH = (186, 118, 104)
WHITE_EYE = (250, 250, 250)

GOKU_FORMS = {
    # form name: (geometry, hair colour, iris colour, has eyebrows)
    "base": ("base", (28, 26, 34), (25, 25, 30), True),
    "ssj": ("ssj", (255, 214, 48), (0, 178, 168), True),
    "ssj3": ("ssj3", (255, 206, 40), (0, 178, 168), False),
    "ssb": ("ssj", (44, 176, 255), (36, 132, 240), True),
    "ui": ("base", (208, 214, 230), (176, 182, 202), True),
}
VEGETA_FORMS = {
    "base": ("base", (24, 24, 34), (25, 25, 30), True),
    "ssj": ("base", (255, 214, 48), (0, 178, 168), True),
    "ssb": ("base", (44, 176, 255), (36, 132, 240), True),
    "ue": ("base", (176, 56, 222), (214, 64, 200), True),
}
GOJO_FORMS = {
    "blindfold": ("blindfold", (244, 244, 250), None, False),
    "eyes": ("eyes", (244, 244, 250), (70, 196, 255), True),
}


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ---------------------------------------------------------------- geometry
def humanoid():
    """Standard humanoid body cubes (same layout for every character)."""
    return [
        ("head", "head", [-4, 24, -4], [8, 8, 8], 0),
        ("body", "body", [-4, 12, -2], [8, 12, 4], 0),
        ("rightArm", "rarm", [-8, 12, -2], [4, 12, 4], 0),
        ("leftArm", "larm", [4, 12, -2], [4, 12, 4], 0),
        ("rightLeg", "rleg", [-3.9, 0, -2], [4, 12, 4], 0),
        ("leftLeg", "lleg", [-0.1, 0, -2], [4, 12, 4], 0),
    ]


def spike(x, y, z, widths, ox, oz, step=1.5):
    """A hair spike built as a stair of shrinking cubes (no rotation)."""
    out = []
    for i, w in enumerate(widths):
        out.append(("hair", "hair",
                    [round(x + i * ox - w / 2, 2), round(y + i * step, 2), round(z + i * oz - w / 2, 2)],
                    [w, 2, w], 0))
    return out


def mirrored(x, y, z, widths, ox, oz, step=1.5):
    return spike(x, y, z, widths, ox, oz, step) + spike(-x, y, z, widths, -ox, oz, step)


def cap(inflate=0.5, y=28, h=4):
    return [("hair", "hair", [-4, y, -4], [8, h, 8], inflate)]


def hair_goku_base():
    c = cap()
    c += spike(0, 31, 0, [4, 3, 3, 2, 1], 0, 0.5)
    c += mirrored(-2, 31, -1, [3, 3, 2, 1], -0.8, 0)
    c += mirrored(-3.5, 29.5, 1, [3, 2, 2, 1], -1.0, 0.3)
    c += spike(0, 29.5, 3.5, [3, 3, 2, 1], 0, 1.0, 1.0)
    c += mirrored(-2.2, 29.5, 3.2, [3, 2, 2, 1], -0.5, 0.9, 1.0)
    c += mirrored(-4.2, 27.5, -1, [2, 2, 1], -0.8, 0, 1.0)
    # bangs over the forehead
    c += [("hair", "hair", [-3, 29, -4.7], [2, 2, 1], 0),
          ("hair", "hair", [1, 29, -4.7], [2, 2, 1], 0),
          ("hair", "hair", [-1, 28.5, -4.8], [2, 2, 1], 0)]
    return c


def hair_goku_ssj():
    c = cap()
    c += spike(0, 31, 0, [4, 4, 3, 3, 2, 1], 0, 0.15, 1.6)
    c += mirrored(-2.2, 31, -0.5, [3, 3, 3, 2, 1], -0.35, 0.1, 1.6)
    c += mirrored(-3.6, 30, 0.8, [3, 3, 2, 1], -0.7, 0.2, 1.5)
    c += spike(0, 30.5, 3, [3, 3, 2, 2, 1], 0, 0.5, 1.5)
    c += mirrored(-2.2, 30, 3, [3, 2, 2, 1], -0.4, 0.5, 1.5)
    c += mirrored(-4.2, 28, -0.5, [2, 2, 1], -0.6, 0, 1.2)
    c += [("hair", "hair", [-1.5, 27.5, -4.7], [1, 4, 1], 0)]  # single bang
    return c


def hair_goku_ssj3():
    c = cap()
    c += spike(0, 31, -1, [4, 3, 3, 2, 1], 0, 0.3, 1.4)
    c += mirrored(-2.5, 31, -1.5, [3, 3, 2, 1], -0.5, 0, 1.4)
    # the long mane down the back
    c += [("hair", "hair", [-4.5, 18, 3.5], [9, 12, 3], 0),
          ("hair", "hair", [-4, 12, 4], [8, 6, 2], 0),
          ("hair", "hair", [-3, 8, 4.2], [6, 4, 2], 0),
          ("hair", "hair", [-2, 5, 4.4], [4, 3, 1], 0),
          ("hair", "hair", [-5, 22, 1], [2, 8, 3], 0),
          ("hair", "hair", [3, 22, 1], [2, 8, 3], 0)]
    c += [("hair", "hair", [-3, 29, -4.7], [2, 3, 1], 0),
          ("hair", "hair", [1, 29, -4.7], [2, 3, 1], 0),
          ("hair", "hair", [-1, 28, -4.8], [2, 3, 1], 0)]
    return c


def hair_vegeta():
    c = cap(0.5, 28, 4)
    # tall flame
    c += [("hair", "hair", [-4, 31, -3], [8, 4, 7], 0),
          ("hair", "hair", [-3.5, 34.5, -2.5], [7, 3, 6], 0),
          ("hair", "hair", [-2.5, 37, -2], [5, 3, 5], 0),
          ("hair", "hair", [-1.5, 39.5, -1.5], [3, 3, 3], 0),
          ("hair", "hair", [-0.5, 42, -0.5], [1, 2, 1], 0)]
    c += mirrored(-3.8, 32, -1, [3, 2, 1], -0.4, 0, 1.5)
    c += mirrored(-3, 33, 2, [3, 2, 1], -0.3, 0.3, 1.6)
    # widow's peak
    c += [("hair", "hair", [-1, 29.5, -4.8], [2, 3, 1], 0),
          ("hair", "hair", [-0.5, 28.5, -4.9], [1, 1, 1], 0)]
    return c


def hair_gojo_blindfold():
    c = cap(0.5, 28, 4)
    c += spike(0, 31, 0, [5, 4, 3, 2, 1], 0, 0.1, 1.5)
    c += mirrored(-2.5, 31, -1.5, [3, 3, 2, 1], -0.6, -0.3, 1.4)
    c += mirrored(-2.5, 31, 1.5, [3, 3, 2, 1], -0.6, 0.4, 1.4)
    c += spike(0, 31, -2.5, [3, 3, 2, 1], 0, -0.5, 1.4)
    c += spike(0, 30.5, 3, [3, 3, 2, 1], 0, 0.7, 1.3)
    c += mirrored(-4, 30, 0, [3, 2, 1], -0.8, 0, 1.2)
    return c


def hair_gojo_eyes():
    c = cap(0.6, 27.5, 4.5)
    c += [("hair", "hair", [-4.6, 30, -4.6], [9, 2, 9], 0),
          ("hair", "hair", [-4, 27, -4.8], [2, 4, 1], 0),
          ("hair", "hair", [-2, 27.5, -4.8], [1, 3, 1], 0),
          ("hair", "hair", [-0.5, 26.5, -4.9], [1, 4, 1], 0),
          ("hair", "hair", [1, 27.5, -4.8], [1, 3, 1], 0),
          ("hair", "hair", [2, 27, -4.8], [2, 4, 1], 0),
          ("hair", "hair", [-4, 24.5, 3.8], [8, 7, 1], 0),
          ("hair", "hair", [-4.8, 25.5, -3], [1, 6, 6], 0),
          ("hair", "hair", [3.8, 25.5, -3], [1, 6, 6], 0)]
    c += mirrored(-2, 31.5, 0, [3, 2, 1], -0.5, 0.2, 1.0)
    return c


GEOMETRIES = {
    "goku": {"base": hair_goku_base, "ssj": hair_goku_ssj, "ssj3": hair_goku_ssj3},
    "vegeta": {"base": hair_vegeta},
    "gojo": {"blindfold": hair_gojo_blindfold, "eyes": hair_gojo_eyes},
}

BONES = [
    {"name": "root", "pivot": [0, 0, 0]},
    {"name": "body", "parent": "root", "pivot": [0, 24, 0]},
    {"name": "head", "parent": "body", "pivot": [0, 24, 0]},
    {"name": "hair", "parent": "head", "pivot": [0, 24, 0]},
    {"name": "rightArm", "parent": "body", "pivot": [-5, 22, 0]},
    {"name": "leftArm", "parent": "body", "pivot": [5, 22, 0]},
    {"name": "rightLeg", "parent": "root", "pivot": [-1.9, 12, 0]},
    {"name": "leftLeg", "parent": "root", "pivot": [1.9, 12, 0]},
]


def box_uv_size(size):
    w, h, d = [int(round(s)) for s in size]
    return 2 * d + 2 * w, d + h


def pack(cubes, tex):
    """Shelf-pack box-UV rectangles. Returns list of (u, v) or None if overflow."""
    x = y = shelf = 0
    out = []
    for _, _, _, size, _ in cubes:
        bw, bh = box_uv_size(size)
        if x + bw > tex:
            x, y, shelf = 0, y + shelf, 0
        if y + bh > tex:
            return None
        out.append((x, y))
        x += bw
        shelf = max(shelf, bh)
    return out


def layout(cubes):
    for tex in (64, 128, 256):
        uv = pack(cubes, tex)
        if uv:
            return tex, uv
    raise RuntimeError("texture overflow")


# ---------------------------------------------------------------- painters
def paint_head(ch, form, face, fx, fy, fw, fh, hair, iris, brows):
    if face == "up":
        return hair
    if face == "down":
        return SKIN
    blindfold = ch == "gojo" and form == "blindfold"
    if blindfold and fy in (3, 4):
        return (18, 18, 24) if face != "north" or fx not in (0, 7) else (30, 30, 38)
    if face == "south":
        return hair if fy <= 6 else SKIN
    if face in ("east", "west"):
        return hair if fy <= 2 else SKIN
    # front
    if fy <= 1:
        return hair
    if ch == "vegeta" and fy == 2 and fx in (3, 4):
        return hair
    if fy == 3 and brows and not blindfold:
        if fx in (1, 2, 5, 6):
            return shade(hair, 0.8) if ch != "gojo" else (230, 230, 240)
    if fy == 4 and not blindfold and iris:
        if fx in (1, 6):
            return WHITE_EYE
        if fx in (2, 5):
            return iris
    if ch == "gojo" and form == "eyes" and fy == 5 and fx in (2, 5):
        return (200, 236, 255)
    if fy == 6 and fx in (3, 4):
        return MOUTH
    return SKIN


def paint_body(ch, face, fx, fy, fw, fh):
    if ch == "goku":
        orange, blue = (246, 128, 22), (34, 58, 170)
        if fy == 8 and face != "up":
            return blue
        if face == "north":
            if fy <= 2 and fx in (3, 4):
                return blue
            if fy <= 1 and fx in (2, 5):
                return blue
            if 2 <= fy <= 3 and fx in (5, 6):
                return (20, 20, 20) if (fx, fy) == (6, 3) else (250, 250, 245)
        if face == "south" and 2 <= fy <= 5 and 2 <= fx <= 5:
            return (20, 20, 20) if 3 <= fy <= 4 and 3 <= fx <= 4 else (250, 250, 245)
        if face == "up":
            return blue if 3 <= fx <= 4 else orange
        return orange
    if ch == "vegeta":
        suit, armor, gold = (34, 52, 150), (238, 238, 228), (226, 182, 60)
        if face == "up":
            return armor
        if face == "north" and fy == 0 and fx in (3, 4):
            return suit
        if fy <= 7:
            if face == "north" and fy == 7:
                return gold
            return armor
        return suit
    # gojo
    uni = (26, 29, 44)
    if face == "north" and fy <= 1:
        return (40, 44, 64)
    if face == "north" and fx == 3:
        return (34, 38, 56)
    return uni


def paint_arm(ch, face, fx, fy):
    if ch == "goku":
        if face == "down":
            return SKIN
        if fy <= 2 or face == "up":
            return (34, 58, 170)
        if fy >= 9:
            return (34, 58, 170)
        return SKIN
    if ch == "vegeta":
        if fy >= 9 or face == "down":
            return (240, 240, 236)
        return (34, 52, 150)
    if fy >= 11 or face == "down":
        return SKIN
    return (26, 29, 44)


def paint_leg(ch, face, fx, fy):
    if ch == "goku":
        if fy >= 9 or face == "down":
            if fy == 9 and face == "north":
                return (200, 40, 40)
            return (24, 40, 120)
        return (246, 128, 22)
    if ch == "vegeta":
        if fy >= 8 or face == "down":
            if fy == 11 and face == "north":
                return (226, 182, 60)
            return (240, 240, 236)
        return (34, 52, 150)
    if fy >= 10 or face == "down":
        return (12, 12, 16)
    return (26, 29, 44)


FACE_LIGHT = {"up": 1.1, "down": 0.7, "north": 1.0, "south": 0.85, "east": 0.92, "west": 0.92}


def faces_of(u, v, size):
    w, h, d = [int(round(s)) for s in size]
    return {
        "up": (u + d, v, w, d),
        "down": (u + d + w, v, w, d),
        "east": (u, v + d, d, h),
        "north": (u + d, v + d, w, h),
        "west": (u + d + w, v + d, d, h),
        "south": (u + 2 * d + w, v + d, w, h),
    }


def render_texture(ch, form, cubes, tex, uvs, hair, iris, brows, rng):
    img = Image.new("RGBA", (tex, tex), (0, 0, 0, 0))
    px = img.load()
    for (bone, part, _, size, _), (u, v) in zip(cubes, uvs):
        for face, (x0, y0, fw, fh) in faces_of(u, v, size).items():
            for fy in range(fh):
                for fx in range(fw):
                    if part == "head":
                        c = paint_head(ch, form, face, fx, fy, fw, fh, hair, iris, brows)
                    elif part == "body":
                        c = paint_body(ch, face, fx, fy, fw, fh)
                    elif part in ("rarm", "larm"):
                        c = paint_arm(ch, face, fx, fy)
                    elif part in ("rleg", "lleg"):
                        c = paint_leg(ch, face, fx, fy)
                    else:  # hair
                        c = hair
                        if (fx * 3 + fy * 5) % 7 == 0:
                            c = shade(c, 0.86)
                        if face == "up" or fy == 0:
                            c = shade(c, 1.12)
                    f = FACE_LIGHT[face]
                    if face in ("north", "south", "east", "west") and fh > 2:
                        f *= 1.0 - 0.10 * fy / (fh - 1)
                    f *= 1.0 + rng.uniform(-0.03, 0.03)
                    px[x0 + fx, y0 + fy] = shade(c, f) + (255,)
    return img


def geometry_json(identifier, cubes, tex, uvs):
    bones = {b["name"]: dict(b, cubes=[]) for b in BONES}
    bone_of = {"head": "head", "body": "body", "rarm": "rightArm", "larm": "leftArm",
               "rleg": "rightLeg", "lleg": "leftLeg", "hair": "hair"}
    for (_, part, origin, size, inflate), (u, v) in zip(cubes, uvs):
        cube = {"origin": origin, "size": size, "uv": [u, v]}
        if inflate:
            cube["inflate"] = inflate
        bones[bone_of[part]]["cubes"].append(cube)
    out_bones = []
    for b in BONES:
        bb = bones[b["name"]]
        if not bb["cubes"]:
            del bb["cubes"]
        out_bones.append(bb)
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": identifier,
                "texture_width": tex,
                "texture_height": tex,
                "visible_bounds_width": 3,
                "visible_bounds_height": 4,
                "visible_bounds_offset": [0, 1.5, 0],
            },
            "bones": out_bones,
        }],
    }


def build_characters():
    rng = random.Random(7)
    forms = {"goku": GOKU_FORMS, "vegeta": VEGETA_FORMS, "gojo": GOJO_FORMS}
    for ch, geos in GEOMETRIES.items():
        layouts = {}
        for gname, fn in geos.items():
            cubes = humanoid() + fn()
            tex, uvs = layout(cubes)
            layouts[gname] = (cubes, tex, uvs)
            with open(os.path.join(RP, "models", "entity", f"{ch}_{gname}.geo.json"), "w") as f:
                json.dump(geometry_json(f"geometry.ab.{ch}_{gname}", cubes, tex, uvs), f, indent=1)
        tdir = os.path.join(RP, "textures", "entity", ch)
        os.makedirs(tdir, exist_ok=True)
        for fname, (gname, hair, iris, brows) in forms[ch].items():
            cubes, tex, uvs = layouts[gname]
            img = render_texture(ch, fname, cubes, tex, uvs, hair, iris, brows, rng)
            img.save(os.path.join(tdir, f"{fname}.png"))


# ---------------------------------------------------------------- icons
def stick_icon(path, low, high, tip, glow):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for i in range(12):
        x, y = 2 + i, 13 - i
        col = low if i < 6 else high
        px[x, y] = col + (255,)
        px[x + 1, y] = shade(col, 0.7) + (255,)
        if 0 < i < 11 and i % 3 == 0:
            px[x, y - 1] = shade(col, 1.25) + (255,)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            x, y = 13 + dx, 2 + dy
            px[x, y] = (glow if (dx or dy) else tip) + (255,)
    img.save(path)


def build_icons():
    idir = os.path.join(RP, "textures", "items")
    stick_icon(os.path.join(idir, "kill_stick.png"), (40, 20, 50), (70, 10, 20), (255, 255, 255), (230, 20, 30))
    stick_icon(os.path.join(idir, "team_stick.png"), (40, 80, 230), (225, 40, 40), (255, 255, 255), (250, 210, 80))

    orb = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = orb.load()
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5 / 7.5
            a = max(0.0, 1.0 - d) ** 1.4
            px[x, y] = (255, 255, 255, int(255 * a))
    orb.save(os.path.join(RP, "textures", "particle", "ab_orb.png"))

    # pack icon: Goku / Vegeta / Gojo faces side by side
    icon = Image.new("RGBA", (96, 96), (18, 18, 30, 255))
    faces = [("goku", "ssj", 0), ("vegeta", "ssb", 32), ("gojo", "eyes", 64)]
    for ch, form, ox in faces:
        tex = Image.open(os.path.join(RP, "textures", "entity", ch, f"{form}.png"))
        face = tex.crop((8, 8, 16, 16)).resize((28, 28), Image.NEAREST)
        icon.paste(face, (ox + 2, 34), face)
    for x in range(96):
        for y in range(0, 26):
            r = int(230 - y * 3)
            icon.putpixel((x, y), (r, 40 + y * 2, 60, 255) if x < 48 else (40, 80 + y * 3, 230, 255))
    icon = icon.resize((128, 128), Image.NEAREST)
    icon.save(os.path.join(RP, "pack_icon.png"))
    icon.save(os.path.join(BP, "pack_icon.png"))


def build_zip():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "AnimeBattles.mcaddon")
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for pack, name in ((BP, "AnimeBattles_BP"), (RP, "AnimeBattles_RP")):
            for base, _, files in os.walk(pack):
                for fn in sorted(files):
                    full = os.path.join(base, fn)
                    z.write(full, os.path.join(name, os.path.relpath(full, pack)))
    return out


def validate_json():
    bad = []
    for pack in (BP, RP):
        for base, _, files in os.walk(pack):
            for fn in files:
                if fn.endswith(".json"):
                    p = os.path.join(base, fn)
                    try:
                        with open(p) as f:
                            json.load(f)
                    except Exception as e:  # noqa: BLE001
                        bad.append(f"{p}: {e}")
    if bad:
        raise SystemExit("Invalid JSON:\n" + "\n".join(bad))


# ---------------------------------------------------------------- entities
# name, max HP, per-form (melee damage, speed), form keys (texture, geometry),
# spawn egg colours. Numbers follow the agreed power order: Goku > Vegeta > Gojo.
FIGHTERS = {
    "goku": {
        "hp": 1000,
        "forms": [(14, 0.33), (20, 0.36), (27, 0.38), (40, 0.42), (55, 0.46)],
        "tex": ["base", "ssj", "ssj3", "ssb", "ui"],
        "geo": ["base", "ssj", "ssj3", "ssj", "base"],
        "egg": ("#f6801a", "#223aaa"),
    },
    "vegeta": {
        "hp": 950,
        "forms": [(13, 0.33), (19, 0.36), (37, 0.41), (50, 0.43)],
        "tex": ["base", "ssj", "ssb", "ue"],
        "geo": ["base", "base", "base", "base"],
        "egg": ("#223496", "#eeeee4"),
    },
    "gojo": {
        "hp": 600,
        "forms": [(10, 0.32), (13, 0.34)],
        "tex": ["blindfold", "eyes"],
        "geo": ["blindfold", "eyes"],
        "egg": ("#1a1d2c", "#f4f4fa"),
    },
}

TEAM_FILTER = {
    "any_of": [
        {"all_of": [{"test": "has_tag", "subject": "self", "value": "ab_red"},
                    {"test": "has_tag", "subject": "other", "value": "ab_blue"}]},
        {"all_of": [{"test": "has_tag", "subject": "self", "value": "ab_blue"},
                    {"test": "has_tag", "subject": "other", "value": "ab_red"}]},
    ]
}


def behavior_entity(name, cfg):
    n = len(cfg["forms"])
    groups = {
        "ab:combat": {
            "minecraft:behavior.nearest_attackable_target": {
                "priority": 1, "must_see": False, "reselect_targets": True,
                "within_radius": 48, "scan_interval": 10,
                "entity_types": [{"filters": TEAM_FILTER, "max_dist": 48}],
            },
            "minecraft:behavior.melee_attack": {
                "priority": 2, "speed_multiplier": 1.35, "track_target": True, "reach_multiplier": 1.6,
            },
        }
    }
    events = {
        "minecraft:entity_spawned": {"add": {"component_groups": ["ab:form_0"]}},
        "ab:enter_combat": {"add": {"component_groups": ["ab:combat"]}},
        "ab:leave_combat": {"remove": {"component_groups": ["ab:combat"]}},
    }
    all_forms = [f"ab:form_{i}" for i in range(n)]
    for i, (dmg, speed) in enumerate(cfg["forms"]):
        groups[f"ab:form_{i}"] = {
            "minecraft:attack": {"damage": dmg},
            "minecraft:movement": {"value": speed},
        }
        events[f"ab:form_{i}"] = {"sequence": [
            {"remove": {"component_groups": all_forms}},
            {"add": {"component_groups": [f"ab:form_{i}"]}},
            {"set_property": {"ab:form": i}},
        ]}
    return {
        "format_version": "1.21.60",
        "minecraft:entity": {
            "description": {
                "identifier": f"ab:{name}",
                "is_spawnable": True,
                "is_summonable": True,
                "properties": {
                    "ab:form": {"type": "int", "range": [0, n - 1], "default": 0, "client_sync": True},
                    "ab:pose": {"type": "int", "range": [0, 4], "default": 0, "client_sync": True},
                },
            },
            "component_groups": groups,
            "components": {
                "minecraft:type_family": {"family": ["anime_fighter", f"ab_{name}", "mob"]},
                "minecraft:health": {"value": cfg["hp"], "max": cfg["hp"]},
                "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                "minecraft:physics": {},
                "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
                "minecraft:persistent": {},
                "minecraft:nameable": {"always_show": True, "allow_name_tag_renaming": False},
                "minecraft:knockback_resistance": {"value": 0.75},
                "minecraft:follow_range": {"value": 48, "max": 64},
                "minecraft:movement.basic": {},
                "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_damage_blocks": True, "can_open_doors": True},
                "minecraft:jump.static": {},
                "minecraft:can_climb": {},
                "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
                "minecraft:damage_sensor": {"triggers": [
                    {"cause": "fall", "deals_damage": "no"},
                ]},
                "minecraft:behavior.float": {"priority": 0},
                "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.8},
                "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8},
                "minecraft:behavior.random_look_around": {"priority": 8},
            },
            "events": events,
        },
    }


def client_entity(name, cfg):
    textures = {t: f"textures/entity/{name}/{t}" for t in dict.fromkeys(cfg["tex"])}
    geometry = {g: f"geometry.ab.{name}_{g}" for g in dict.fromkeys(cfg["geo"])}
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": f"ab:{name}",
                "materials": {"default": "entity_alphatest"},
                "textures": textures,
                "geometry": geometry,
                "animations": {
                    "look": "animation.ab.look_at_target",
                    "move": "animation.ab.move",
                    "idle": "animation.ab.idle",
                    "attack": "animation.ab.attack",
                    "pose_beam": "animation.ab.pose_beam",
                    "pose_cup": "animation.ab.pose_cup",
                    "pose_raise": "animation.ab.pose_raise",
                    "pose_point": "animation.ab.pose_point",
                },
                "scripts": {"animate": [
                    "look", "move", "idle",
                    {"attack": "variable.attack_time > 0.0"},
                    {"pose_beam": "query.property('ab:pose') == 1"},
                    {"pose_cup": "query.property('ab:pose') == 2"},
                    {"pose_raise": "query.property('ab:pose') == 3"},
                    {"pose_point": "query.property('ab:pose') == 4"},
                ]},
                "render_controllers": [f"controller.render.ab.{name}"],
                "spawn_egg": {"base_color": cfg["egg"][0], "overlay_color": cfg["egg"][1]},
            }
        },
    }


def render_controllers():
    out = {"format_version": "1.10.0", "render_controllers": {}}
    for name, cfg in FIGHTERS.items():
        out["render_controllers"][f"controller.render.ab.{name}"] = {
            "arrays": {
                "textures": {"Array.skins": [f"Texture.{t}" for t in cfg["tex"]]},
                "geometries": {"Array.geos": [f"Geometry.{g}" for g in cfg["geo"]]},
            },
            "geometry": "Array.geos[query.property('ab:form')]",
            "materials": [{"*": "Material.default"}],
            "textures": ["Array.skins[query.property('ab:form')]"],
        }
    return out


def build_entities():
    for name, cfg in FIGHTERS.items():
        with open(os.path.join(BP, "entities", f"{name}.json"), "w") as f:
            json.dump(behavior_entity(name, cfg), f, indent=1)
        with open(os.path.join(RP, "entity", f"{name}.entity.json"), "w") as f:
            json.dump(client_entity(name, cfg), f, indent=1)
    with open(os.path.join(RP, "render_controllers", "ab.render_controllers.json"), "w") as f:
        json.dump(render_controllers(), f, indent=1)


if __name__ == "__main__":
    build_entities()
    build_characters()
    build_icons()
    validate_json()
    print("built", build_zip())
