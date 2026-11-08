import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from mobkit import *

RP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AnimePowers", "RP")
GEO = RP + "/models/entity/{}.geo.json"
TEX = RP + "/textures/entity/{}.png"


# ═════════════ شيطان الجمر (Ember Imp): جلد أسود، جمر برتقالي ═════════════
def build_imp():
    m = Mob("geometry.sh_imp", 96, 96, seed=11)
    SKIN = (44, 42, 52); SKIN2 = (66, 62, 78); DARK = (24, 22, 30); BONE = (222, 208, 176)
    EMBER = (255, 140, 40); EYE = (255, 200, 60)

    def sheen(img, regs):
        for f in ("up", "north", "east", "west"):
            patches(img, regs[f], m.rng, SKIN2, density=0.2, seed_scale=2)

    def torso(img, regs):
        sheen(img, regs)
        x0, y0, w, h = regs["north"]
        for yy in range(1, h - 1):
            for xx in range(1, w - 1):
                if xx == w // 2 or (yy % 3 == 0):
                    cur = tuple(int(v) for v in img[y0 + yy, x0 + xx][:3])
                    put(img, x0 + xx, y0 + yy, mul(cur, 0.62))
        for yy in range(2, h - 1, 3):
            for xx in (2, w - 3):
                put(img, x0 + xx, y0 + yy, mix(SKIN2, EMBER, 0.75))
        cracks(img, regs["north"], m.rng, EMBER, n=1, length=4, halo=False)
        cracks(img, regs["south"], m.rng, EMBER, n=2, length=5, halo=False)

    def face(img, regs):
        sheen(img, regs)
        x0, y0, w, h = regs["north"]
        for dx, dy in ((1, 3), (2, 3), (3, 4)):
            glow_px(img, x0 + dx, y0 + dy, EYE)
        for dx, dy in ((w - 2, 3), (w - 3, 3), (w - 4, 4)):
            glow_px(img, x0 + dx, y0 + dy, EYE)
        for dx in range(1, 4): put(img, x0 + dx, y0 + 2, DARK)
        for dx in range(w - 4, w - 1): put(img, x0 + dx, y0 + 2, DARK)
        for xx in range(2, w - 2): put(img, x0 + xx, y0 + h - 2, (14, 6, 8))
        for xx in range(2, w - 2, 2): put(img, x0 + xx, y0 + h - 3, BONE)
        for r in ("east", "west", "south"):
            cracks(img, regs[r], m.rng, EMBER, n=1, length=2, halo=False)

    def limb(img, regs):
        sheen(img, regs)
        cracks(img, regs["north"], m.rng, EMBER, n=1, length=3, halo=False)

    def tail_tip(img, regs):
        for x0, y0, w, h in regs.values():
            for yy in range(h):
                for xx in range(w):
                    put(img, x0 + xx, y0 + yy, mix(EMBER, (255, 225, 130), (yy / max(1, h - 1)) * 0.7))

    m.bone("body", [0, 8, 0])
    m.cube("body", [-3, 6.5, -2], [6, 2, 4], DARK, key="hip", grad=0.1)
    m.cube("body", [-3.5, 8, -2.3], [7, 3.5, 4.6], SKIN, key="abs", detail=torso, grad=0.2)
    m.cube("body", [-4.6, 11.3, -2.8], [9.2, 4, 5.6], SKIN, key="chest", detail=torso, grad=0.22)
    m.cube("body", [-4.2, 11.6, -3.5], [3.8, 2.6, 1.2], SKIN2, key="pec", detail=sheen, grad=0.2)
    m.cube("body", [0.4, 11.6, -3.5], [3.8, 2.6, 1.2], SKIN2, key="pec", detail=sheen, grad=0.2)
    m.cube("body", [-6.2, 13.4, -2.6], [3.4, 2.6, 5.2], DARK, key="deltL", detail=sheen, grad=0.2)
    m.cube("body", [2.8, 13.4, -2.6], [3.4, 2.6, 5.2], DARK, key="deltR", detail=sheen, grad=0.2)
    m.cube("body", [-5.6, 15.6, -0.8], [1.0, 2.4, 1.0], BONE, key="shsp", rot=[0, 0, 18], pivot=[-5.6, 15.6, -0.3], grad=0.25, noise=2)
    m.cube("body", [4.6, 15.6, -0.8], [1.0, 2.4, 1.0], BONE, key="shsp", rot=[0, 0, -18], pivot=[5.1, 15.6, -0.3], grad=0.25, noise=2)
    for i, (yy, s) in enumerate(((13.4, 2.4), (11.4, 2.8), (9.4, 2.2), (7.8, 1.6))):
        m.cube("body", [-0.6, yy, 2.2], [1.2, s, 1.5], BONE, key="spine%d" % i, grad=0.1, noise=2)

    m.bone("head", [0, 15.5, -0.5], "body")
    m.cube("head", [-3.5, 15.4, -3.5], [7, 6, 6], SKIN, key="skull", detail=face, grad=0.2)
    m.cube("head", [-3, 14.8, -4.2], [6, 2, 1.2], DARK, key="jaw", grad=0.1)
    m.cube("head", [-1.6, 15.0, -5.6], [3.2, 1.8, 1.8], SKIN, key="snout", detail=sheen, grad=0.2)
    m.cube("head", [-1.3, 14.2, -5.4], [0.7, 1.2, 0.7], BONE, key="fang", grad=0.2, noise=2)
    m.cube("head", [0.6, 14.2, -5.4], [0.7, 1.2, 0.7], BONE, key="fang", grad=0.2, noise=2)
    for i, z in enumerate((-2.5, -0.5, 1.5)):
        m.cube("head", [-0.5, 21.4 - i * 0.3, z], [1, 1.8, 1.2], EMBER, key="mane%d" % i, grad=0.05, noise=3)
    m.cube("head", [-3.6, 20.5, -1.5], [1.6, 3, 1.6], BONE, key="horn_a", rot=[-15, 0, 12], pivot=[-3, 20.5, -1], grad=0.28)
    m.cube("head", [2.0, 20.5, -1.5], [1.6, 3, 1.6], BONE, key="horn_a", rot=[-15, 0, -12], pivot=[3, 20.5, -1], grad=0.28)
    m.cube("head", [-4.8, 21.8, -0.8], [1.1, 2.2, 1.1], BONE, key="horn_b", rot=[-25, 0, 22], pivot=[-4, 21.5, -0.5], grad=0.28)
    m.cube("head", [3.7, 21.8, -0.8], [1.1, 2.2, 1.1], BONE, key="horn_b", rot=[-25, 0, -22], pivot=[4, 21.5, -0.5], grad=0.28)
    m.cube("head", [-5.5, 17.2, -0.5], [2, 2.6, 0.9], DARK, key="ear", rot=[0, 0, 28], pivot=[-3.5, 18, 0], grad=0.1)
    m.cube("head", [3.5, 17.2, -0.5], [2, 2.6, 0.9], DARK, key="ear", rot=[0, 0, -28], pivot=[3.5, 18, 0], grad=0.1)

    for s, nm in ((1, "arm_l"), (-1, "arm_r")):
        px = 5.6 * s
        m.bone(nm, [px, 14, 0], "body")
        m.cube(nm, [px - 1.7, 9.6, -1.7], [3.4, 4.4, 3.4], SKIN, key="uarm", detail=limb, grad=0.2)
        m.cube(nm, [px - 2.0, 5.8, -2.0], [4.0, 4.0, 4.0], SKIN, key="farm", detail=limb, grad=0.2)
        m.cube(nm, [px - 0.5, 8.6, 1.6], [1.0, 1.0, 2.0], BONE, key="elbspike", grad=0.2, noise=2)
        m.cube(nm, [px - 2.1, 4.4, -2.1], [4.2, 1.6, 4.2], DARK, key="fist", grad=0.15)
        for k in (-1, 0, 1):
            m.cube(nm, [px - 0.45 + k * 1.15, 2.4, -2.2], [0.9, 2.4, 0.9], BONE, key="claw", grad=0.25, noise=2)

    for s, nm in ((1, "leg_l"), (-1, "leg_r")):
        px = 2.2 * s
        m.bone(nm, [px, 7, 0], "body")
        m.cube(nm, [px - 1.8, 3.4, -2.0], [3.6, 4.0, 4.0], SKIN, key="thigh", detail=limb, grad=0.2)
        m.cube(nm, [px - 1.2, 3.0, -2.8], [2.4, 1.4, 1.2], BONE, key="kneecap", grad=0.2, noise=2)
        m.cube(nm, [px - 1.3, 0.6, -1.3], [2.6, 3, 2.6], DARK, key="shin", grad=0.15)
        m.cube(nm, [px - 1.9, 0, -3.2], [3.8, 1.2, 4.4], DARK, key="foot", grad=0.15)
        m.cube(nm, [px - 0.5, 0, -4.0], [1, 0.9, 1], BONE, key="toeclaw", grad=0.2, noise=2)

    # ذيل من 3 عظام (حركة موجية) مع أشواك ونهاية متوهجة
    m.bone("tail", [0, 9, 2.5], "body")
    m.cube("tail", [-1.1, 8.0, 2.5], [2.2, 2.2, 3.8], SKIN, key="tail1", detail=limb, grad=0.2)
    m.cube("tail", [-0.4, 10.2, 3.2], [0.8, 1.2, 1.2], BONE, key="tsp", grad=0.2, noise=2)
    m.bone("tail2", [0, 9, 6.2], "tail")
    m.cube("tail2", [-0.9, 8.1, 6.2], [1.8, 1.8, 3.6], SKIN, key="tail2", detail=limb, grad=0.2)
    m.cube("tail2", [-0.4, 9.9, 7.0], [0.8, 1.2, 1.2], BONE, key="tsp", grad=0.2, noise=2)
    m.bone("tail3", [0, 9, 9.7], "tail2")
    m.cube("tail3", [-0.7, 8.3, 9.7], [1.4, 1.4, 3.0], DARK, key="tail3", grad=0.2)
    m.cube("tail3", [-1.5, 7.5, 12.5], [3.0, 3.0, 3.0], EMBER, key="tailtip", detail=tail_tip, grad=0.05, noise=3)
    return m


# ═════════════ حارس الصخر (Stone Guard): غولم صخري عليه طحالب ═════════════
def build_guard():
    m = Mob("geometry.sh_guard", 160, 160, seed=31)
    ROCK = (112, 114, 108); ROCK2 = (146, 148, 140); ROCKD = (66, 68, 66)
    MOSS = (72, 122, 48); MOSS2 = (104, 160, 62)
    GLOW = (110, 255, 205)

    def stone(img, regs, moss_up=0.9, moss_side=0.16):
        for f in regs:
            patches(img, regs[f], m.rng, ROCK2, density=0.25, seed_scale=3)
            patches(img, regs[f], m.rng, ROCKD, density=0.3, seed_scale=3)
        patches(img, regs["up"], m.rng, MOSS, density=moss_up, seed_scale=3)
        patches(img, regs["up"], m.rng, MOSS2, density=moss_up * 0.4, seed_scale=2)
        for f in ("north", "south", "east", "west"):
            x0, y0, w, h = regs[f]
            patches(img, (x0, y0, w, max(2, h // 3)), m.rng, MOSS, density=moss_side * 2.2, seed_scale=2)
            patches(img, regs[f], m.rng, MOSS, density=moss_side * 0.5, seed_scale=1)

    def stone_nm(img, regs):
        stone(img, regs, 0.5, 0.06)

    def chest(img, regs):
        stone(img, regs, 0.9, 0.14)
        x0, y0, w, h = regs["north"]
        cx, cy = x0 + w // 2, y0 + h // 2 - 1
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                d = abs(dx) + abs(dy)
                if d <= 4:
                    put(img, cx + dx, cy + dy, mix(GLOW, (230, 255, 240), 0.8) if d <= 1 else mix(GLOW, (20, 70, 60), d * 0.16))
        for ang in range(8):
            for r in range(5, 9):
                dx = int(round(r * [1, .7, 0, -.7, -1, -.7, 0, .7][ang]))
                dy = int(round(r * [0, .7, 1, .7, 0, -.7, -1, -.7][ang]))
                if x0 <= cx + dx < x0 + w and y0 <= cy + dy < y0 + h and (r % 2):
                    put(img, cx + dx, cy + dy, mix(ROCKD, GLOW, 0.8))
        cracks(img, regs["south"], m.rng, GLOW, n=2, length=10)
        cracks(img, regs["east"], m.rng, GLOW, n=1, length=7)

    def head(img, regs):
        stone(img, regs, 0.9, 0.12)
        x0, y0, w, h = regs["north"]
        for xx in range(1, 3):
            for yy in range(h // 2 - 1, h // 2 + 1):
                glow_px(img, x0 + xx, y0 + yy, GLOW, halo=0.5)
                glow_px(img, x0 + w - 1 - xx, y0 + yy, GLOW, halo=0.5)
        for yy in range(0, h // 2 - 2):
            put(img, x0 + w // 2, y0 + yy, mix(ROCKD, GLOW, 0.9))
        for xx in range(w // 2 - 2, w // 2 + 3):
            put(img, x0 + xx, y0 + h - 2, ROCKD)

    def fist(img, regs):
        stone(img, regs, 0.6, 0.1)
        for f in ("north", "south", "east", "west"):
            x0, y0, w, h = regs[f]
            for xx in range(w): put(img, x0 + xx, y0 + h - 1, mul(ROCKD, 0.7))

    def crystal(img, regs):
        for x0, y0, w, h in regs.values():
            for yy in range(h):
                for xx in range(w):
                    k = 0.65 + 0.35 * (yy / max(1, h - 1))
                    put(img, x0 + xx, y0 + yy, mul(mix(GLOW, (230, 255, 240), 0.35), 1.0 - 0.45 * (1 - k)))

    def mossy(img, regs):
        for x0, y0, w, h in regs.values():
            for yy in range(h):
                for xx in range(w):
                    put(img, x0 + xx, y0 + yy, MOSS if (xx + yy) % 3 else MOSS2)

    m.bone("body", [0, 14, 0])
    m.cube("body", [-6.5, 14, -4], [13, 7, 8], ROCK, key="chest", detail=chest, grad=0.2)
    m.cube("body", [-7.2, 20.5, -4.6], [14.4, 5.5, 9.2], ROCK, key="upper", detail=stone, grad=0.2)
    m.cube("body", [-4.5, 12.3, -3.2], [9, 2.2, 6.4], ROCKD, key="belly", detail=stone_nm, grad=0.15)
    m.cube("body", [-5, 15.5, 3.6], [10, 9, 3], ROCK, key="hump", detail=stone, grad=0.2, rot=[0, 0, 4], pivot=[0, 20, 5])
    for (cx, cy, rz, key) in ((-3, 24.0, -14, "cr1"), (0.5, 25.2, 0, "cr2"), (3.6, 23.6, 16, "cr3")):
        m.cube("body", [cx - 0.9, cy, 4.2], [1.8, 4.6, 1.8], GLOW, key=key, detail=crystal, rot=[-8, 0, rz], pivot=[cx, cy, 4.8], grad=0.05, noise=3)
    m.cube("body", [-6, 26.0, -2.0], [4.5, 1.0, 4.5], MOSS, key="mossB1", detail=mossy, grad=0.1, noise=6)
    m.cube("body", [1.5, 26.0, -1.0], [3.5, 1.0, 3.5], MOSS, key="mossB2", detail=mossy, grad=0.1, noise=6)

    m.bone("head", [0, 26, 0], "body")
    m.cube("head", [-3.5, 26, -3.5], [7, 6, 7], ROCK, key="head", detail=head, grad=0.2)
    m.cube("head", [-4.1, 29.4, -4.1], [8.2, 1.8, 2.2], ROCKD, key="brow", detail=stone_nm, grad=0.15)
    m.cube("head", [-3.0, 25.0, -4.0], [6, 1.6, 1.6], ROCK, key="jaw", detail=stone_nm, grad=0.15)
    m.cube("head", [-3.2, 32.0, -3.2], [4.0, 0.9, 4.0], MOSS, key="mossH", detail=mossy, grad=0.1, noise=6)
    m.cube("head", [0.6, 31.8, -0.4], [3.2, 1.0, 3.2], MOSS2, key="mossH2", detail=mossy, grad=0.1, noise=6)

    for s, nm in ((1, "arm_l"), (-1, "arm_r")):
        px = 9.6 * s
        m.bone(nm, [px, 25, 0], "body")
        m.cube(nm, [px - 4.4, 22.0, -4.4], [8.8, 5.6, 8.8], ROCK, key="shoulder", detail=stone, grad=0.2)
        m.cube(nm, [px - 3.2, 12.5, -3.2], [6.4, 10, 6.4], ROCK, key="arm", detail=stone, grad=0.18)
        m.cube(nm, [px - 4.4, 3.6, -4.4], [8.8, 9.5, 8.8], ROCK, key="fist", detail=fist, grad=0.2)
        m.cube(nm, [px - 1.8, 27.6, -2.6], [3.6, 1.2, 3.6], MOSS, key="mossS", detail=mossy, grad=0.1, noise=6)
        m.cube(nm, [px + (-5.4 if s > 0 else 4.4), 17.0, -3.6], [1.0, 5.0, 1.0], MOSS, key="vine", detail=mossy, grad=0.1, noise=6)
        m.cube(nm, [px + (4.4 if s > 0 else -5.4), 19.0, 2.6], [1.0, 3.5, 1.0], MOSS, key="vine", detail=mossy, grad=0.1, noise=6)
        m.cube(nm, [px - 0.8, 27.6, 0.0], [1.6, 3.4, 1.6], GLOW, key="crsh", detail=crystal, rot=[0, 0, 12 * s], pivot=[px, 27.6, 0.8], grad=0.05, noise=3)
    for s, nm in ((1, "leg_l"), (-1, "leg_r")):
        px = 3.6 * s
        m.bone(nm, [px, 14, 0], "body")
        m.cube(nm, [px - 3.2, 5.4, -3.2], [6.4, 8.6, 6.4], ROCK, key="leg", detail=stone, grad=0.18)
        m.cube(nm, [px - 3.9, 0, -5.0], [7.8, 5.6, 9.4], ROCK, key="foot", detail=stone, grad=0.2)
        m.cube(nm, [px - 2.0, 13.4, -2.0], [4.0, 0.9, 4.0], MOSS, key="mossL", detail=mossy, grad=0.1, noise=6)
    return m


if __name__ == "__main__":
    which = sys.argv[1:] or ["imp", "guard"]
    if "imp" in which:
        build_imp().save(GEO.format("sh_imp"), TEX.format("sh_imp"))
    if "guard" in which:
        build_guard().save(GEO.format("sh_guard"), TEX.format("sh_guard"))
