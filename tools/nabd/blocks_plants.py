"""Plants drawn as little sprites: grasses, ferns, flowers, saplings, crops,
mushrooms, reeds, vines and lily pads."""
import numpy as np

from . import painters as P
from .core import N, STATS, Tex, make_ramp, mix, rng_of, shift, vbase, vramp

GREEN = make_ramp((72, 140, 52), 5, 0.42)
STEM = make_ramp((58, 120, 44), 4, 0.4)


class Sprite:
    def __init__(self, h=N, w=N):
        self.h, self.w = h, w
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.alpha = np.zeros((h, w), np.uint8)
        self.hgt = np.zeros((h, w))
        self.emis = np.zeros((h, w))

    def px(self, x, y, c, hgt=0.6, emis=0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rgb[y, x] = c
            self.alpha[y, x] = 255
            self.hgt[y, x] = hgt
            self.emis[y, x] = emis

    def shape(self, x0, y0, rows, pal, hgt=0.7, emis=0):
        """rows: strings; digits index `pal`, '.' is empty."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != ".":
                    self.px(x0 + dx, y0 + dy, pal[int(ch)], hgt, emis)

    def stem(self, x, y0, y1, ramp=STEM, lean=0.0, thick=False):
        """vertical stem from y0 (top) down to y1 (bottom)."""
        for y in range(y0, y1 + 1):
            t = (y1 - y) / max(1, y1 - y0)
            xi = x + lean * t * t
            self.px(xi, y, ramp[2 if (y % 3) else 1], 0.5)
            if thick:
                self.px(xi + 1, y, ramp[0], 0.45)

    def leaf(self, x, y, d, ramp=GREEN, ln=3):
        """a small leaf growing sideways (d = -1 left, 1 right) and upward."""
        for i in range(1, ln + 1):
            self.px(x + d * i, y - (i // 2), ramp[min(4, 1 + i)], 0.55)
        self.px(x + d, y + 0, ramp[1], 0.5)

    def tex(self, sss=150, rough=200):
        t = Tex(self.rgb, self.hgt, alpha=self.alpha, rough=rough, sss=sss, bump=0.7)
        t.emis = self.emis
        return t


def grey_ramp(name, contrast=0.36):
    return vramp(name, 5, grey=True, contrast=contrast)


def crop_wheat(stage):
    s = Sprite()
    r = rng_of("wheat")
    young = make_ramp((70, 150, 48), 5, 0.4)
    ripe = make_ramp((206, 170, 70), 5, 0.36)
    t = stage / 7.0
    ramp = [mix(a, b, max(0, (t - 0.45) / 0.55)) for a, b in zip(young, ripe)]
    hgt = 3 + int(round(stage * 1.5))
    for i in range(8):
        x = 1 + i * 2 + int(r.integers(0, 2))
        ln = max(2, hgt - int(r.integers(0, 3)))
        lean = float(r.choice([-0.4, 0, 0, 0.4]))
        for k in range(ln):
            y = 15 - k
            xi = x + lean * (k / 4.0)
            s.px(xi, y, ramp[min(4, 1 + (k * 3) // max(1, ln))], 0.4 + 0.5 * k / ln)
        if stage >= 6:                       # ears of grain
            for k in range(3):
                s.px(x + lean * (ln / 4.0) + (k % 2) * (1 if i % 2 else -1), 15 - ln - k + 1, ramp[4 - (k == 2)], 0.95)
        elif stage >= 4:
            s.px(x + lean * (ln / 4.0), 15 - ln, ramp[4], 0.9)
    return s.tex()


def crop_root(kind, stage, stages=4):
    s = Sprite()
    r = rng_of(kind)
    t = stage / (stages - 1)
    leafr = {"carrot": make_ramp((60, 150, 50), 5, 0.42), "potato": make_ramp((80, 140, 60), 5, 0.4),
             "beet": make_ramp((70, 130, 56), 5, 0.4)}[kind]
    stemc = {"carrot": STEM, "potato": STEM, "beet": make_ramp((150, 40, 60), 4, 0.3)}[kind]
    rootr = {"carrot": make_ramp((236, 130, 30), 4, 0.3), "potato": make_ramp((196, 160, 96), 4, 0.25),
             "beet": make_ramp((150, 30, 56), 4, 0.3)}[kind]
    for (x, base) in ((3, 15), (8, 15), (12, 15)):
        h = 2 + int(round(t * (5 + int(r.integers(0, 3)))))
        for k in range(h):
            s.px(x, base - k, stemc[2 if k % 2 else 1], 0.5)
        top = base - h
        spread = 1 + int(round(t * 2))
        for d in (-1, 1):
            for i in range(1, spread + 1):
                s.px(x + d * i, top + (0 if i < spread else 1), leafr[min(4, 2 + i)], 0.7)
                if kind == "carrot":         # feathery
                    s.px(x + d * i, top - 1 - (i % 2), leafr[3], 0.75)
        s.px(x, top, leafr[4], 0.8)
        if kind != "carrot":
            s.px(x, top - 1, leafr[3], 0.8)
        if stage == stages - 1:              # ripe: root crown peeks out
            s.px(x, 15, rootr[2], 0.9)
            s.px(x - 1, 15, rootr[1], 0.85)
            s.px(x + 1, 15, rootr[3], 0.85)
            s.px(x, 14, rootr[3], 0.9)
    return s.tex()


def sapling(kind):
    s = Sprite()
    trunk = {"birch": make_ramp((214, 210, 200), 4, 0.2), "spruce": make_ramp((70, 46, 26), 4, 0.3),
             "cherry": make_ramp((70, 44, 50), 4, 0.3), "pale_oak": make_ramp((180, 172, 168), 4, 0.2)}.get(kind, make_ramp((110, 84, 50), 4, 0.3))
    leafc = {"oak": (66, 140, 44), "spruce": (50, 96, 62), "birch": (110, 160, 70), "jungle": (48, 150, 40),
             "acacia": (120, 150, 40), "roofed_oak": (44, 110, 34), "cherry": (236, 150, 190), "pale_oak": (150, 160, 150),
             "poplar": (200, 170, 50)}[kind]
    lr = make_ramp(leafc, 5, 0.42)
    for y in range(9, 16):
        s.px(7, y, trunk[2], 0.5)
        s.px(8, y, trunk[0], 0.45)
    if kind == "birch":
        s.px(7, 11, (50, 48, 46)); s.px(8, 13, (50, 48, 46))
    if kind == "spruce":
        rows = ["...4...", "..343..", "..232..", ".23432.", ".12321.", "2343432", "1232321", "..121.."]
        s.shape(4, 1, rows, lr)
    elif kind in ("acacia",):
        rows = [".344443.", "34333432", "23222321", ".12..21."]
        s.shape(4, 4, rows, lr)
        s.px(6, 8, trunk[1]); s.px(9, 8, trunk[1])
    elif kind == "jungle":
        rows = ["..44..", ".3443.", "343343", "232232", "12..21", "1....1"]
        s.shape(5, 3, rows, lr)
    elif kind == "poplar":
        rows = ["..4..", ".343.", ".343.", "23432", "23332", "12321", ".121."]
        s.shape(5, 2, rows, lr)
    else:
        rows = ["..344..", ".34443.", "3443432", "2333321", "2232221", ".12211."]
        s.shape(4, 3, rows, lr)
        if kind == "cherry":
            for (x, y) in ((5, 4), (8, 6), (9, 4)):
                s.px(x, y, (255, 226, 240), 0.9)
    return s.tex()


def flower(kind):
    s = Sprite()
    if kind == "dandelion":
        pal = [(190, 130, 10), (236, 180, 20), (255, 222, 50), (255, 246, 150)]
        s.stem(7, 9, 15)
        s.leaf(7, 14, -1, ln=3); s.leaf(7, 13, 1, ln=2)
        s.shape(6, 6, [".23.", "2332", "1221", ".11."], pal, 0.9)
    elif kind == "poppy":
        pal = [(120, 12, 16), (180, 22, 22), (226, 44, 34), (255, 110, 90), (30, 20, 24)]
        s.stem(7, 9, 15, lean=1.0)
        s.leaf(7, 13, -1, ln=3)
        s.shape(5, 5, [".23.2.", "233321", "124421", ".1221.", "..11.."], pal, 0.9)
    elif kind == "orchid":
        pal = [(30, 120, 190), (50, 170, 230), (130, 220, 255), (236, 250, 255)]
        s.stem(8, 6, 15, lean=-2.0)
        s.leaf(8, 14, 1, ln=3); s.leaf(8, 14, -1, ln=2)
        for (x, y) in ((5, 4), (8, 6), (4, 8)):
            s.shape(x, y, ["23.", "121", ".1."], pal, 0.9)
            s.px(x + 1, y + 1, pal[3], 0.95)
    elif kind == "allium":
        pal = [(110, 50, 150), (150, 80, 196), (190, 124, 236), (232, 190, 255)]
        s.stem(7, 8, 15)
        s.leaf(7, 15, -1, ln=2); s.leaf(7, 15, 1, ln=2)
        s.shape(5, 3, [".232.", "23332", "22321", "12211", ".111."], pal, 0.9)
    elif kind == "bluet":
        pal = [(190, 196, 206), (226, 232, 240), (255, 255, 255), (250, 214, 60)]
        for (x, top) in ((5, 9), (8, 7), (11, 10)):
            s.stem(x, top + 2, 15)
            s.shape(x - 1, top, [".2.", "231", ".1."], pal, 0.9)
        s.leaf(8, 14, 1, ln=2); s.leaf(5, 14, -1, ln=2)
    elif kind.startswith("tulip_"):
        col = {"red": (214, 40, 36), "orange": (240, 130, 30), "white": (236, 236, 240), "pink": (240, 150, 200)}[kind[6:]]
        pal = make_ramp(col, 4, 0.34)
        s.stem(7, 9, 15)
        s.leaf(7, 14, -1, ln=4); s.leaf(7, 14, 1, ln=4)
        s.shape(6, 5, ["3.2.", "3221", "2211", ".11."], pal, 0.9)
    elif kind == "daisy":
        pal = [(196, 200, 208), (232, 236, 242), (255, 255, 255), (246, 200, 40), (200, 140, 20)]
        s.stem(7, 9, 15)
        s.leaf(7, 13, 1, ln=3); s.leaf(7, 14, -1, ln=2)
        s.shape(5, 4, [".2.2.", "22321", ".343.", "12421", ".1.1."], pal, 0.9)
    elif kind == "cornflower":
        pal = [(30, 50, 150), (50, 84, 200), (84, 130, 240), (160, 196, 255)]
        s.stem(7, 8, 15, lean=-1.0)
        s.leaf(7, 13, 1, ln=3)
        s.shape(4, 4, ["3.2.3", ".232.", "22321", ".121.", "..1.."], pal, 0.9)
    elif kind == "lily":
        pal = [(196, 204, 210), (232, 238, 242), (255, 255, 255)]
        s.stem(6, 4, 15, lean=3.0)
        s.leaf(6, 15, -1, ln=4); s.leaf(6, 15, 1, ln=3)
        for (x, y) in ((9, 5), (8, 8), (7, 11)):
            s.shape(x + 1, y, ["21", "10"], pal, 0.9)
    elif kind == "wither":
        pal = [(10, 10, 12), (28, 26, 30), (50, 46, 52), (84, 76, 88)]
        s.stem(7, 9, 15, ramp=make_ramp((40, 60, 36), 4, 0.3))
        s.leaf(7, 13, -1, ramp=make_ramp((44, 64, 40), 5, 0.3), ln=2)
        s.shape(5, 5, [".23.2.", "233321", "121321", ".1221.", "..11.."], pal, 0.9)
    elif kind == "torch":
        pal = [(110, 40, 150), (226, 90, 30), (255, 160, 40), (255, 230, 120)]
        s.stem(7, 9, 15)
        s.leaf(7, 14, -1, ln=3); s.leaf(7, 13, 1, ln=3)
        s.shape(5, 2, ["..3..", ".232.", ".232.", "12321", "01210", ".010."], pal, 0.9, emis=60)
    return s.tex()


def mushroom(col):
    s = Sprite()
    cap = make_ramp(col, 4, 0.34)
    stem = make_ramp((224, 214, 196), 4, 0.16)
    for y in range(12, 16):
        s.px(7, y, stem[2]); s.px(8, y, stem[0])
    s.shape(5, 9, [".2332.", "232221", "111110"], cap, 0.9)
    if col[0] > 160:
        s.px(6, 10, (250, 246, 240), 1.0); s.px(9, 9, (250, 246, 240), 1.0)
    return s.tex(sss=80)


def bush2(top, col=None):
    """Half of a double-tall flowering bush."""
    s = Sprite()
    r = rng_of("bush2:" + str(col) + str(top))
    lr = make_ramp((62, 126, 48), 5, 0.42)
    for x in (4, 7, 10):
        y0 = 2 if top else 0
        s.stem(x + int(r.integers(0, 2)), y0 + int(r.integers(0, 3)), 15)
    for _ in range(14 if top else 18):
        x, y = int(r.integers(2, 14)), int(r.integers(2 if top else 0, 15))
        d = int(r.choice([-1, 1]))
        s.leaf(x, y, d, lr, ln=int(r.integers(2, 4)))
    if col and top:
        pr = make_ramp(col, 4, 0.34)
        for (x, y) in ((3, 3), (9, 2), (6, 7), (11, 8)):
            s.shape(x, y, [".32.", "3221", "2211", ".11."], pr, 0.95)
    return s.tex()


def build(out, flip, variations):
    # ------------------------------------------------- tinted grasses & ferns
    out["tallgrass"] = P.blades("tallgrass", grey_ramp("tallgrass"), count=11, height=(5, 12))
    out["tallgrass_carried"] = P.blades("tallgrass", vramp("tallgrass_carried", 5, contrast=0.4), count=11, height=(5, 12))
    out["double_plant_grass_bottom"] = P.blades("dgrass_b", grey_ramp("double_plant_grass_bottom"), count=13, height=(14, 16))
    out["double_plant_grass_top"] = P.blades("dgrass_t", grey_ramp("double_plant_grass_top"), count=10, height=(5, 13))
    out["double_plant_grass_carried"] = P.blades("dgrass_t", vramp("double_plant_grass_carried", 5, contrast=0.4), count=10, height=(5, 13))

    def fern(name, ramp, h0, tall=False):
        s = Sprite()
        r = rng_of(name)
        for (x, lean) in ((7, 0.0), (5, -2.5), (10, 2.5)) if not tall else ((7, 0.0), (8, 0.5)):
            top = h0 + (0 if lean == 0 else 4)
            for y in range(top, 16):
                t = (15 - y) / max(1, 15 - top)
                xi = x + lean * t * t
                s.px(xi, y, ramp[2], 0.6)
                w = int(round((1 - t) * 3.2 + 1)) if y > top else 0
                if (y % 2) == 0:
                    for i in range(1, w + 1):
                        s.px(xi - i, y + (i // 2), ramp[min(4, 2 + i % 3)], 0.5)
                        s.px(xi + i, y + (i // 2), ramp[min(4, 1 + i % 3)], 0.5)
        return s.tex()
    out["fern"] = fern("fern", grey_ramp("fern"), 3)
    out["fern_carried"] = fern("fern", vramp("fern_carried", 5, contrast=0.4), 3)
    out["double_plant_fern_bottom"] = fern("dfern_b", grey_ramp("double_plant_fern_bottom"), 0, tall=True)
    out["double_plant_fern_top"] = fern("dfern_t", grey_ramp("double_plant_fern_top"), 2)
    out["double_plant_fern_carried"] = fern("dfern_t", vramp("double_plant_fern_carried", 5, contrast=0.4), 2)
    for nm in ("short_dry_grass", "tall_dry_grass"):
        if nm in STATS:
            out[nm] = P.blades(nm, vramp(nm, 5, contrast=0.3), count=6 if nm.startswith("short") else 10,
                               height=(3, 6) if nm.startswith("short") else (7, 13), sss=60)

    # dead bush: bare twigs
    s = Sprite()
    tw = make_ramp((124, 90, 44), 4, 0.34)
    r = rng_of("deadbush")
    for (x, lean, top) in ((7, 0, 4), (7, -3, 7), (8, 3, 6), (7, -5, 11), (8, 5, 10)):
        for y in range(top, 16):
            t = (15 - y) / max(1, 15 - top)
            s.px(x + lean * t, y, tw[1 + (y % 3 == 0) + (lean == 0)], 0.6)
    out["deadbush"] = s.tex(sss=0, rough=220)

    # ---------------------------------------------------------------- flowers
    for name, kind in (("flower_dandelion", "dandelion"), ("flower_rose", "poppy"), ("flower_blue_orchid", "orchid"),
                       ("flower_allium", "allium"), ("flower_houstonia", "bluet"), ("flower_tulip_red", "tulip_red"),
                       ("flower_tulip_orange", "tulip_orange"), ("flower_tulip_white", "tulip_white"),
                       ("flower_tulip_pink", "tulip_pink"), ("flower_oxeye_daisy", "daisy"),
                       ("flower_cornflower", "cornflower"), ("flower_lily_of_the_valley", "lily"),
                       ("flower_wither_rose", "wither"), ("torchflower", "torch")):
        if name in STATS:
            out[name] = flower(kind)
    for name, col in (("double_plant_rose", (214, 40, 46)), ("double_plant_paeonia", (240, 170, 214)),
                      ("double_plant_syringa", (200, 150, 230))):
        out[name + "_bottom"] = bush2(False, col)
        out[name + "_top"] = bush2(True, col)

    for name, kind in (("sapling_oak", "oak"), ("sapling_spruce", "spruce"), ("sapling_birch", "birch"),
                       ("sapling_jungle", "jungle"), ("sapling_acacia", "acacia"), ("sapling_roofed_oak", "roofed_oak"),
                       ("cherry_sapling", "cherry"), ("pale_oak_sapling", "pale_oak"), ("poplar_sapling", "poplar")):
        if name in STATS:
            out[name] = sapling(kind)
    out["mushroom_red"] = mushroom((214, 44, 40))
    out["mushroom_brown"] = mushroom((150, 110, 84))

    # ------------------------------------------------------------------ crops
    for i in range(8):
        out[f"wheat_stage_{i}"] = crop_wheat(i)
    for i in range(4):
        out[f"carrots_stage_{i}"] = crop_root("carrot", i)
        out[f"potatoes_stage_{i}"] = crop_root("potato", i)
        out[f"beetroots_stage_{i}"] = crop_root("beet", i)
    if "carrots_stage3" in STATS:
        out["carrots_stage3"] = out["carrots_stage_3"]

    # ------------------------------------------------------------ sugar cane
    s = Sprite()
    cane = vramp("reeds", 5, contrast=0.3)
    for (x, top) in ((3, 0), (8, 0), (12, 0)):
        for y in range(top, 16):
            node = (y + x) % 5 == 0
            s.px(x, y, cane[1] if node else cane[3], 0.8)
            s.px(x + 1, y, cane[0] if node else cane[2], 0.7)
            if node:
                d = 1 if (y // 5) % 2 else -1
                for i in range(1, 4):
                    s.px(x + (1 if d > 0 else 0) + d * i, y - i // 2, cane[4 - (i == 3)], 0.6)
    out["reeds"] = s.tex()

    # ------------------------------------------------------- vines & lily pad
    def vine(ramp):
        s = Sprite()
        r = rng_of("vine")
        for x in range(0, N, 2):
            ln = int(r.integers(7, 17))
            xi = x + int(r.integers(0, 2))
            for y in range(ln):
                s.px(xi, y, ramp[2 if y % 2 else 1], 0.5)
                if r.random() < 0.55:
                    d = int(r.choice([-1, 1]))
                    s.px(xi + d, y, ramp[4 if r.random() < 0.5 else 3], 0.8)
                    if r.random() < 0.4:
                        s.px(xi + d, y + 1, ramp[2], 0.7)
        return s.tex()
    out["vine"] = vine(grey_ramp("vine", 0.45))
    out["vine_carried"] = vine(vramp("vine_carried", 5, contrast=0.45))

    def lily(ramp):
        s = Sprite()
        yy, xx = np.mgrid[0:N, 0:N]
        d = np.hypot(xx - 7.5, yy - 7.5)
        ang = np.arctan2(yy - 7.5, xx - 7.5)
        pad = (d < 7.2) & ~((np.abs(ang - 0.6) < 0.22) & (d > 1.5))
        for y in range(N):
            for x in range(N):
                if pad[y, x]:
                    v = 2
                    if d[y, x] > 6.0:
                        v = 1 if (x + y) > 15 else 4
                    elif abs(np.sin(ang[y, x] * 3.5)) < 0.16 and d[y, x] > 1.2:
                        v = 3
                    s.px(x, y, ramp[v], 0.6 if v != 3 else 0.8)
        return s.tex(sss=60)
    out["waterlily"] = lily(grey_ramp("waterlily", 0.34))
    out["carried_waterlily"] = lily(vramp("carried_waterlily", 5, contrast=0.36))

    # sweet berry bush
    for st in range(4):
        nm = f"sweet_berry_bush_stage{st}"
        if nm not in STATS:
            continue
        s = Sprite()
        r = rng_of("berry")
        lr = make_ramp((60, 104, 56), 5, 0.4)
        size = 3 + st * 2 if st < 2 else 7
        for _ in range(10 + st * 8):
            x = int(r.integers(8 - size, 8 + size))
            y = int(r.integers(max(1, 15 - size * 2), 16))
            s.leaf(x, y, int(r.choice([-1, 1])), lr, ln=2)
            s.px(x, y, make_ramp((96, 70, 40), 4, 0.3)[1], 0.4)
        if st >= 2:
            for _ in range(3 if st == 2 else 7):
                x, y = int(r.integers(3, 13)), int(r.integers(4, 14))
                s.px(x, y, (214, 40, 50) if st == 3 else (236, 130, 110), 1.0)
                s.px(x + 1, y, (150, 20, 36) if st == 3 else (200, 90, 80), 0.95)
        out[nm] = s.tex()
