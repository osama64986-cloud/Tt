"""1.22: twenty-four new fighters — two more for every anime, and every Hashira Demon Slayer was missing.

Built on the helpers of models.py and chars_extra.py (same house style: 8x8 head, 32 px faces, clean cel pixel art,
strand hair, flat 2D sword sprites). Imported at the very end of chars_extra.py, which chains FORMS and build().
"""
import math

import models as M
import sculpt as SC
from models import SIDES, SKIN, _put, both_arms, both_legs, base_body, dark, head_paint, layered, light, lines, mix, shell, solid
from chars_extra import _shell_strands, _strip_ears, akatsuki_cloud, arm_paint, region, skin_swap

FORMS = {}
BUILDERS = {}


def fighter(name, forms):
    """Register a builder: FORMS[name] = forms, build(name, form) -> fn(m, form)."""
    def deco(fn):
        FORMS[name] = list(forms)
        BUILDERS[name] = fn
        return fn
    return deco


def build(char, form):
    m = M.Model()
    BUILDERS[char](m, form)
    return m


# ==================================================================================
# faces: custom marks on the 32 px face (x 0..31 left to right as the viewer sees it; x >= 16 is the character's LEFT)
# ==================================================================================
MARKS = {}


def mark(*names):
    def deco(fn):
        for n in names:
            MARKS[n] = fn
        return fn
    return deco


class _Face:
    """What a mark painter gets: put/both helpers, the expression state and the face's palette."""
    def __init__(self, px, W, H, spec, hair, iris, skin):
        self.px, self.W, self.H, self.spec, self.hair, self.iris, self.skin = px, W, H, spec, hair, iris, tuple(skin)
        self.k = W / 32.0
        self.expr = M.EXPR
        self.open = M.EXPR not in ("blink", "hurt")
        self.mouth_free = M.EXPR in (None, "blink")      # shout / hurt paint their own mouths
        self.sr = M.ramp(skin)
        self.marks = spec.get("marks", [])

    def put(self, x, y, c):
        k = self.k
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < self.W and 0 <= yy < self.H:
                    self.px[xx, yy] = tuple(c[:3]) + (255,)

    def both(self, x, y, c):
        self.put(x, y, c)
        self.put(31 - x, y, c)

    def get(self, x, y):
        return self.px[min(self.W - 1, int(x * self.k)), min(self.H - 1, int(y * self.k))][:3]

    def art(self, x0, y0, rows, pal, mirror=False):
        """Pixel art from strings: '.' = leave, any other char looks up pal. mirror: also at 31-x."""
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch != "." and ch in pal:
                    self.put(x0 + c, y0 + r, pal[ch])
                    if mirror:
                        self.put(31 - (x0 + c), y0 + r, pal[ch])

    def wipe_eyes(self, y0=14, y1=22, x0=5, x1=14):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.both(x, y, self.sr[2])


_face32_prev22 = M.face32


def face32_new22(px, W, H, spec, hair, iris, skin):
    _face32_prev22(px, W, H, spec, hair, iris, skin)
    marks = spec.get("marks", [])
    if not any(mk in MARKS for mk in marks):
        return
    F = _Face(px, W, H, spec, hair, iris, skin)
    done = set()
    for mk in marks:
        fn = MARKS.get(mk)
        if fn and fn not in done:
            done.add(fn)
            fn(F)


M.face32 = face32_new22
INK = (20, 12, 14)
WHITE_E = (250, 250, 250)


def eye_iris(F, cx, rows, cols, top=None, low=None, pupil=None, glint=True, side=0):
    """Repaint one eye's iris (cx = left column of the iris on the viewer's left eye; side 0 both, -1 right eye only,
    1 left eye only). cols: list of colours per row from top to bottom."""
    if not F.open:
        return
    for i, y in enumerate(rows):
        c = cols[min(i, len(cols) - 1)]
        for dx in range(3):
            if side <= 0:
                F.put(cx + dx, y, c)
            if side >= 0:
                F.put(31 - (cx + 2) + dx, y, c)
    if pupil:
        for y in pupil[1]:
            if side <= 0:
                F.put(cx + 1, y, pupil[0])
            if side >= 0:
                F.put(31 - (cx + 1), y, pupil[0])
    if glint:
        if side <= 0:
            F.put(cx, rows[0] + 1 if len(rows) > 2 else rows[0], WHITE_E)
        if side >= 0:
            F.put(31 - (cx + 2), rows[0] + 1 if len(rows) > 2 else rows[0], WHITE_E)


# ---------------------------------------------------------------- shared painters
def vstripes(c1, c2, n=6, faces=SIDES):
    """Clean vertical stripes (Obanai's haori)."""
    def f(face, px, w, h, base):
        if face not in faces:
            return
        s = max(1, w // n) if face in ("north", "south") else max(1, w // max(2, n // 2))
        for y in range(h):
            for x in range(w):
                c = c1 if (x // s) % 2 == 0 else c2
                _put(px, w, h, x, y, c if face in ("north", "east") else dark(c, 0.88))
    return f


def hstripes(c1, c2, y0, y1, n=3):
    def f(face, px, w, h, base):
        if face not in SIDES:
            return
        a, b = int(h * y0), int(h * y1)
        s = max(1, (b - a) // (2 * n))
        for y in range(a, b):
            for x in range(w):
                _put(px, w, h, x, y, c1 if ((y - a) // s) % 2 == 0 else c2)
    return f


def gradient(cols, y0=0.0, y1=1.0, faces=SIDES):
    """A smooth vertical colour gradient through `cols` (top to bottom) between y0 and y1 of the face."""
    def f(face, px, w, h, base):
        if face not in faces:
            return
        a, b = int(h * y0), max(int(h * y0) + 1, int(h * y1))
        for y in range(a, b):
            t = (y - a) / max(1, b - a - 1) * (len(cols) - 1)
            i = min(len(cols) - 2, int(t))
            c = mix(cols[i], cols[i + 1], t - i)
            for x in range(w):
                _put(px, w, h, x, y, c if face in ("north", "east") else dark(c, 0.9))
    return f


def buttons(col=(230, 196, 90), y0=0.12, y1=0.7, step=None, x=0.5):
    def f(face, px, w, h, base):
        if face != "north":
            return
        st = step or max(3, h // 6)
        for y in range(int(h * y0), int(h * y1), st):
            _put(px, w, h, int(w * x), y, col)
            _put(px, w, h, int(w * x), y + 1, dark(col, 0.7))
    return f


def glyph(rows, col, cx=0.5, cy=0.3, faces=("south",), scale=1):
    """Pixel glyph (kanji on a haori) centred at (cx, cy) of the face."""
    def f(face, px, w, h, base):
        if face not in faces:
            return
        gw, gh = len(rows[0]) * scale, len(rows) * scale
        x0, y0 = int(w * cx - gw / 2), int(h * cy - gh / 2)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == "#":
                    for dx in range(scale):
                        for dy in range(scale):
                            _put(px, w, h, x0 + c * scale + dx, y0 + r * scale + dy, col)
    return f


def painter_on(paint, extra):
    """Run extra detail drawers (f(face, px, w, h, base)) after a painter."""
    def p(face, img):
        paint(face, img)
        px = img.load()
        for f in extra:
            f(face, px, img.size[0], img.size[1], None)
    return p


def head_band(paint, y0, y1, col, faces=("east", "west", "south"), lines_col=None):
    """Paint a band round the sides and back of a head (bandages, a mask, a head-wrap) between model heights y0..y1."""
    def p(face, img):
        paint(face, img)
        if face not in faces:
            return
        px = img.load()
        w, h = img.size
        a, b = int((32 - y1) / 8 * h), int((32 - y0) / 8 * h)
        for y in range(max(0, a), min(h, b)):
            for x in range(w):
                c = col
                if lines_col and (x + y) % 6 == 0:
                    c = lines_col
                px[x, y] = c + (255,)
    return p


def plain_head(skin, faces_paint, top=None, back=None):
    """A head with no hair painted on the sides/back (bald heads, helmets, masks): the face from faces_paint,
    the other faces skin (or `top` / `back` colours)."""
    def p(face, img):
        if face == "north":
            faces_paint(face, img)
            return
        c = skin
        if face == "up" and top:
            c = top
        elif face == "south" and back:
            c = back
        elif face == "down":
            c = dark(skin, 0.8)
        M.pixel_mat(img, c, face)
    return p


# ---------------------------------------------------------------- 2D blade sprites (Nichirin swords and others)
def nichirin_shape(st, hf):
    """A Nichirin katana seen flat: kashira, diamond-wrapped tsuka, a thin guard bar (the guard's face is a separate
    plate), habaki, then the coloured blade: dark spine, coloured body, bright edge, optional engraved kanji band,
    optional serpent waves (Obanai) or a straight thin stinger (Shinobu)."""
    wrap, dia, metal = st["wrap"], st["diamond"], st.get("metal", (40, 40, 46))
    blade, edge, spine = st["blade"], st["edge"], st.get("spine", dark(st["blade"], 0.55))
    curve, wave, thin = st.get("curve", 0.06), st.get("wave", 0.0), st.get("thin", False)
    g1 = hf + 0.018

    def f(xf, u):
        dx = xf - 0.5
        if u < hf * 0.07:
            return metal if abs(dx) < 0.16 else None
        if u < hf:
            if abs(dx) > 0.13:
                return None
            k = ((u - hf * 0.07) / (hf * 0.93)) * 8
            dd = abs(dx) / 0.13 + abs((k % 1) - 0.5) * 2
            return dia if dd < 0.75 else wrap
        if u < g1:
            return st.get("tsuba", (40, 40, 46)) if abs(dx) < 0.42 else None
        t = (u - g1) / (1 - g1)
        if t < 0.035:
            return metal if abs(dx) < 0.16 else None
        cx = 0.5 + curve * t * t + wave * math.sin(t * math.pi * 7) * min(1.0, t * 6)
        half = (0.09 if thin else 0.14) * (1.0 if t < 0.88 else max(0.0, 1 - (t - 0.88) / 0.12))
        if thin and t < 0.2:
            half *= 0.75 + t
        if abs(xf - cx) > half:
            return None
        q = (xf - (cx - half)) / max(1e-6, 2 * half)
        if q < 0.22:
            return spine
        if q > 0.74:
            return edge
        if st.get("kanji") and 0.08 < t < 0.2 and 0.35 < q < 0.65 and int(t * 60) % 2 == 0:
            return st["kanji"]
        return blade
    return f


def tsuba_paint(shape, col, inner=None, res=24):
    """The guard seen face-on (a plate across the blade): shape(dx, dy) in [-1,1]^2 -> 'r' rim, 'i' inner, None."""
    def p(face, img):
        if face not in ("up", "down"):
            return
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                s = shape((x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1)
                if s == "r":
                    px[x, y] = col + (255,)
                elif s == "i" and inner:
                    px[x, y] = inner + (255,)
                elif s == "e":
                    px[x, y] = dark(col, 0.55) + (255,)
    return p


def _hex(dx, dy, frame=True):
    r = max(abs(dy) * 1.0 + abs(dx) * 0.5, abs(dx))
    if r > 0.95:
        return None
    if r > 0.82:
        return "e"
    if frame and r < 0.5:
        return None if r > 0.18 else "i"
    return "r"


TSUBA = {
    "hex": lambda dx, dy: _hex(dx, dy, True),                                       # Giyu: a hexagonal frame
    "round": lambda dx, dy: (None if dx * dx + dy * dy > 0.9 else "e" if dx * dx + dy * dy > 0.7 else "r"),
    "flower": lambda dx, dy: (lambda a, r: None if r > 0.62 + 0.3 * abs(math.cos(a * 2)) else "r" if r > 0.22 else "i")(math.atan2(dy, dx), math.hypot(dx, dy)),
    "clover": lambda dx, dy: (lambda a, r: None if r > 0.5 + 0.42 * abs(math.cos(a * 2)) ** 0.5 else ("e" if r > 0.42 + 0.42 * abs(math.cos(a * 2)) ** 0.5 else "r") if r > 0.2 else "i")(math.atan2(dy, dx) + math.pi / 4, math.hypot(dx, dy)),
    "square": lambda dx, dy: None if max(abs(dx), abs(dy)) > 0.8 else "e" if max(abs(dx), abs(dy)) > 0.66 else "r",
}


def nichirin(m, st, bone="rightArm", hand=(6, 12.2, -1.2), direction=(0, 0.1, -1), length=14.0, grip=1.2, hilt=4.4, width=2.6):
    """A Nichirin sword in the hand: the flat sprite plus the guard plate face-on."""
    L = length + 1.3
    M.flat_blade(m, bone, hand, direction, hilt, L, width, nichirin_shape(st, hilt / (hilt + L)), grip=grip)
    d = M.norm(direction)
    g = [hand[i] + d[i] * grip for i in range(3)]            # the guard sits where the hilt meets the blade
    gs = st.get("guard", 2.2)
    m.box(bone, [g[0] - gs / 2, g[1], g[2] - gs / 2], [gs, 0, gs], tsuba_paint(TSUBA[st.get("tsuba_shape", "round")], st.get("tsuba", (40, 40, 46)), st.get("tsuba_in")),
          rot=M._rot_for(d), pivot=list(g))
    m.cubes[-1]["hires"] = 4


def saya(m, st, top=(-4.6, 12.4, -1.6), direction=(0.05, -0.55, 1), length=12):
    M.sheath(m, top, direction, length, dict(saya=st.get("saya", (30, 30, 34)), saya_band=st.get("saya_band", (200, 200, 200))))


# ---------------------------------------------------------------- Demon Slayer Corps uniform
def ds_body(m, head, uni, pants=None, *, sleeve="long", hand=SKIN, wraps=(236, 234, 228), wrap_line=(200, 198, 190),
            tabi=None, strap=(40, 40, 70), chest=None, baggy=True, belt=True, collar=True, undershirt=True, skirt=None,
            torso_extra=(), arm_extra=(), leg_extra=(), button_col=(232, 196, 96)):
    """The Demon Slayer Corps uniform: stand-up collar with the white undershirt collar, gold buttons, white belt,
    baggy tattsuke-hakama tucked into kyahan leg wraps, tabi socks and zori sandals.
    sleeve: long | rolled (to the elbow, bare forearms) | none (sleeveless, bare arms) | wide (kimono sleeves).
    chest: None | 'open' (V of skin) | 'unbuttoned' (open to the belt) | 'window' (Mitsuri) | 'purple' (Gyomei)."""
    pants = pants or uni
    tabi = tabi or dark(uni, 0.85)
    tor = [buttons(button_col)] if chest not in ("unbuttoned", "purple") else []
    tor.append(region((0.48, 0, 0.52, 1), dark(uni, 0.82), faces=("north",)))
    if chest == "unbuttoned":   # jacket and shirt open from collar to belt: chest and abs on show
        def openv(face, px, w, h, base):
            if face != "north":
                return
            for y in range(h):
                half = int(w * (0.26 if y < h * 0.55 else 0.26 - 0.1 * (y - h * 0.55) / (h * 0.45)))
                for x in range(w // 2 - half, w // 2 + half):
                    c = SKIN if abs(x - w // 2) < half - 1 else (236, 236, 232)
                    if c == SKIN and (y in (int(h * 0.36), int(h * 0.56), int(h * 0.74)) and abs(x - w // 2) < half - 2):
                        c = dark(SKIN, 0.84)                           # the line of the abs
                    if c == SKIN and x == w // 2 and h * 0.4 < y < h * 0.95:
                        c = dark(SKIN, 0.86)
                    _put(px, w, h, x, y, c)
        tor = [openv]
    if chest == "purple":       # Gyomei: the jacket open on a purple kimono with a white collar
        def kimono(face, px, w, h, base):
            if face != "north":
                return
            for y in range(int(h * 0.85)):
                half = int(w * 0.3 * (1 - y / (h * 0.95)))
                for x in range(w // 2 - half - 1, w // 2 + half + 1):
                    edge = abs(x - w // 2) >= half - 1
                    _put(px, w, h, x, y, (240, 238, 232) if edge else (120, 70, 150))
        tor = [kimono, buttons(button_col, y0=0.8, y1=0.9)]
    if chest == "window":       # Mitsuri: the jacket and shirt open over the chest
        def window(face, px, w, h, base):
            if face != "north":
                return
            for y in range(int(h * 0.05), int(h * 0.42)):
                t = (y - h * 0.05) / (h * 0.37)
                half = int(w * 0.22 * math.sin(math.pi * min(1, t * 1.1)) + 1)
                for x in range(w // 2 - half - 1, w // 2 + half + 1):
                    edge = abs(x - w // 2) >= half
                    _put(px, w, h, x, y, (240, 238, 234) if edge else SKIN)
        tor = [window, buttons(button_col, y0=0.48, y1=0.75)]
    if chest == "open":
        def vee(face, px, w, h, base):
            if face != "north":
                return
            for y in range(int(h * 0.3)):
                half = int(w * 0.16 * (1 - y / (h * 0.3)))
                for x in range(w // 2 - half, w // 2 + half + 1):
                    _put(px, w, h, x, y, (240, 238, 232) if abs(x - w // 2) == half else SKIN)
        tor = [vee, buttons(button_col, y0=0.34, y1=0.75)]
    torso = layered(uni, tor + list(torso_extra))
    if sleeve == "none":
        arm = layered(hand, list(arm_extra))
    elif sleeve == "rolled":
        arm = layered(uni, [region((0, 0.42, 1, 1), hand), region((0, 0.36, 1, 0.44), (238, 236, 230))] + list(arm_extra))
    else:
        arm = layered(uni, [region((0, 0.86, 1, 1), hand), region((0, 0.82, 1, 0.87), (238, 236, 230))] + list(arm_extra))
    foot = [region((0, 0.86, 1, 0.95), tabi), region((0, 0.95, 1, 1), (238, 236, 230)),
            lines((("north",), [[(0.2, 0.86), (0.5, 0.95)], [(0.8, 0.86), (0.5, 0.95)]]), strap)]
    legp = [region((0, 0.36, 1, 0.86), wraps)] + ([lines((SIDES, [[(0, 0.48), (1, 0.5)], [(0, 0.6), (1, 0.62)], [(0, 0.72), (1, 0.74)]]), wrap_line)] if wrap_line else []) + foot
    leg = layered(pants, legp + list(leg_extra))
    base_body(m, torso, arm, leg, head)
    if skirt:  # a short pleated skirt instead of hakama
        m.box("body", [-4.5, 8.8, -2.5], [9.0, 3.8, 5.0], layered(skirt, [lines((SIDES, [[(x, 0.1), (x, 1)] for x in (0.15, 0.32, 0.5, 0.68, 0.85)]), dark(skirt, 0.7))]))
    elif baggy:
        both_legs(m, [-0.7, 4.6, -2.7], [5.1, 7.6, 5.4], layered(pants, [lines((SIDES, [[(0.3, 0), (0.25, 1)], [(0.7, 0), (0.75, 1)]]), dark(pants, 0.8))]))
    if belt:
        m.box("body", [-4.4, 11.6, -2.5], [8.8, 1.3, 5.0], layered((240, 240, 236), [region((0.42, 0.1, 0.58, 0.9), (170, 172, 180), faces=("north",))]))
    if collar:
        m.box("body", [-2.3, 22.6, -2.45], [4.6, 1.9, 4.9], layered(uni, [region((0, 0, 1, 0.22), (240, 238, 232))] if undershirt else []))
    if sleeve == "wide":
        both_arms(m, [3.4, 13.4, -2.8], [5.2, 10.8, 5.6], layered(uni, [region((0, 0.9, 1, 1), dark(uni, 0.8))]))


def haori(m, back, front_r, front_l=None, sleeve_r=None, sleeve_l=None, y0=5.5, sleeve_len=10.6, sleeves=True, lining=None):
    """A haori over the uniform: back panel, two front panels and wide sleeves (each its own painter)."""
    front_l = front_l or front_r
    sleeve_r = sleeve_r or front_r
    sleeve_l = sleeve_l or sleeve_r
    h = 24.2 - y0
    m.box("body", [-4.6, y0, 2.1], [9.2, h, 0.5], back)
    m.box("body", [2.2, y0, -2.6], [2.4, h, 0.5], front_r)
    m.box("body", [-4.6, y0, -2.6], [2.4, h, 0.5], front_l)
    m.box("body", [4.1, y0, -2.6], [0.5, h, 5.2], front_r)       # the sides close the coat
    m.box("body", [-4.6, y0, -2.6], [0.5, h, 5.2], front_l)
    if sleeves:
        top = 24.2
        m.box("rightArm", [3.5, top - sleeve_len, -2.7], [5.0, sleeve_len, 5.4], sleeve_r)
        if sleeve_l != "none":
            m.box("leftArm", [-8.5, top - sleeve_len, -2.7], [5.0, sleeve_len, 5.4], sleeve_l)
        if lining:
            m.box("rightArm", [3.6, top - sleeve_len - 0.01, -2.6], [4.8, 0.3, 5.2], solid(lining))
            if sleeve_l != "none":
                m.box("leftArm", [-8.4, top - sleeve_len - 0.01, -2.6], [4.8, 0.3, 5.2], solid(lining))


def split_painter(right, left):
    """A haori back panel split down the middle: the character's right half in `right`, the left half in `left`
    (both painters). From behind the character's right is on the viewer's right."""
    def p(face, img):
        w, h = img.size
        a = img.copy()
        b = img.copy()
        right(face, a)
        left(face, b)
        if face in ("south",):          # seen from behind: left half of the image is the character's left
            img.paste(b.crop((0, 0, w // 2, h)), (0, 0))
            img.paste(a.crop((w // 2, 0, w, h)), (w // 2, 0))
        elif face in ("north", "up", "down"):
            img.paste(a.crop((0, 0, w // 2, h)), (0, 0))
            img.paste(b.crop((w // 2, 0, w, h)), (w // 2, 0))
        elif face == "east":
            img.paste(a, (0, 0))
        else:
            img.paste(b, (0, 0))
    return p


# ==================================================================================
# DEMON SLAYER — the Hashira
# ==================================================================================
M.FACE32.update({
    "giyu": dict(eye="narrow", brow="fine", mouth="neutral", marks=["giyu_eyes"]),
    "giyu_mark": dict(eye="narrow", brow="angled", mouth="neutral", marks=["giyu_eyes", "giyu_mark"]),
    "shinobu": dict(eye="round", brow="fine", mouth="smile", marks=["shinobu_eyes", "pink_lips"]),
    "shinobu_final": dict(eye="round", brow="angled", mouth="neutral", marks=["shinobu_eyes", "pink_lips"]),
    "tengen": dict(eye="narrow", brow="fine", mouth="smirk", marks=["tengen_eyes", "tengen_makeup"]),
    "tengen_score": dict(eye="narrow", brow="angled", mouth="smirk", marks=["tengen_eyes", "tengen_makeup"]),
    "mitsuri": dict(eye="round", brow="fine", mouth="smile", marks=["mitsuri_eyes", "mitsuri_moles", "pink_lips"]),
    "mitsuri_mark": dict(eye="round", brow="angled", mouth="neutral", marks=["mitsuri_eyes", "mitsuri_moles", "pink_lips"]),
    "muichiro": dict(eye="round", brow="fine", mouth="neutral", marks=["mui_eyes"]),
    "muichiro_mark": dict(eye="round", brow="angled", mouth="neutral", marks=["mui_eyes", "mui_mark"]),
    "gyomei": dict(eye="narrow", brow="none", mouth="neutral", marks=["gyomei_face"]),
    "gyomei_mark": dict(eye="narrow", brow="none", mouth="clench", marks=["gyomei_face"]),
    "obanai": dict(eye="narrow", brow="fine", mouth="none", marks=["obanai_eyes", "bandage_mouth"]),
    "obanai_mark": dict(eye="narrow", brow="sharp", mouth="none", marks=["obanai_eyes", "bandage_mouth"]),
    "sanemi": dict(eye="round", brow="sharp", mouth="smirk", marks=["sanemi_face"]),
    "sanemi_mark": dict(eye="round", brow="sharp", mouth="grin", marks=["sanemi_face", "sanemi_mark"]),
})


@mark("giyu_eyes")
def _giyu_eyes(F):  # lapis-blue irises that lighten at the bottom
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 20, (110, 150, 230))


@mark("giyu_mark")
def _giyu_mark(F):  # a blood-red, fluid, water-like mark on his left cheek, three dots
    R, D = (200, 36, 40), (150, 20, 28)
    F.art(18, 14, [
        "..........R.",
        ".........RR.",
        ".........R..",
        "..........R.",
        "..........R.",
        ".........RR.",
        "........RR..",
        ".......RR...",
        "..RRRRRR....",
        ".R......R...",
        "R..RRR...R..",
        "R.R...R..R..",
        "R.R.RR...R..",
        ".R.R....R...",
        "..R.RRRR....",
        "...R.......D",
        "D.......D...",
    ], {"R": R, "D": D})


@mark("shinobu_eyes")
def _shinobu_eyes(F):  # big pupil-less insect eyes: hazy purple darkening toward the bottom, white glints at the top
    if not F.open:
        return
    cols = [(214, 190, 240), (176, 140, 220), (140, 100, 196), (110, 70, 170), (84, 50, 140), (70, 40, 120)]
    for i, y in enumerate(range(16, 22)):
        for x in range(8, 12):
            F.both(x, y, cols[i])
    F.both(8, 16, (246, 246, 252))
    F.put(9, 16, (246, 246, 252)); F.put(22, 16, (246, 246, 252))
    for x in (6, 13):
        F.both(x, 15, INK)
    F.both(5, 16, INK)


@mark("pink_lips")
def _pink_lips(F):
    if not F.mouth_free:
        return
    for x in range(12, 21):
        if F.get(x, 27) == (130, 62, 56):
            F.put(x, 27, (214, 110, 130))
        if F.get(x, 26) == (130, 62, 56):
            F.put(x, 26, (214, 110, 130))


@mark("tengen_eyes")
def _tengen_eyes(F):  # thin dark fuchsia eyes, each with one long lash sweeping out to the side
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (150, 30, 90))
            F.both(x, 19, (190, 50, 120))
            F.both(x, 20, (170, 40, 110))
        F.both(10, 19, (60, 10, 40))
    for x, y in ((4, 17), (3, 16), (2, 16)):
        F.both(x, y, INK)


@mark("tengen_makeup")
def _tengen_makeup(F):  # red make-up round his LEFT eye: big and small dots alternating, sweeping in to the corner
    R = (210, 36, 46)
    for i, (x, y, big) in enumerate(((19, 13, 0), (21, 12, 1), (24, 12, 0), (26, 13, 1), (28, 16, 0), (27, 18, 1),
                                     (28, 21, 0), (26, 22, 1), (24, 24, 0))):
        F.put(x, y, R)
        if big:
            F.put(x + 1, y, R); F.put(x, y + 1, R); F.put(x + 1, y + 1, dark(R, 0.85))


@mark("mitsuri_eyes")
def _mitsuri_eyes(F):  # big round pale-green eyes with a darker green centre and white sparkles
    if not F.open:
        return
    for y in range(16, 22):
        for x in range(8, 12):
            c = (176, 236, 150)
            if 17 <= y <= 20 and 9 <= x <= 10:
                c = (70, 150, 80)
            F.both(x, y, c)
    for x, y in ((8, 16), (9, 16), (11, 20)):
        F.put(x, y, WHITE_E); F.put(31 - x, y, WHITE_E)
    F.both(6, 15, INK); F.both(5, 16, INK)


@mark("mitsuri_moles")
def _mitsuri_moles(F):
    F.put(9, 23, (150, 90, 90)); F.put(22, 23, (150, 90, 90))


@mark("mui_eyes")
def _mui_eyes(F):  # large, empty turquoise eyes with teal centres and no glint
    if not F.open:
        return
    for y in range(16, 22):
        for x in range(8, 12):
            c = (110, 220, 210)
            if 17 <= y <= 20 and 9 <= x <= 10:
                c = (40, 140, 146)
            if y == 16:
                c = (70, 170, 170)
            F.both(x, y, c)


@mark("mui_mark")
def _mui_mark(F):  # three carmine cloud shapes: both cheeks and the left side of the forehead
    C = (176, 30, 48)
    cloud = [".CC.CC.", "CCCCCCC", ".CC..CC"]
    F.art(3, 23, cloud, {"C": C})
    F.art(22, 23, cloud, {"C": C})
    F.art(21, 12, [".CCC.", "CC.CC"], {"C": C})


@mark("gyomei_face")
def _gyomei_face(F):  # blind white eyes, tears, the stitched scar across his forehead, a heavy brow
    sh = F.sr[0]
    for x in range(6, 14):
        F.both(x, 15, sh)                               # brow ridge shadow
    for x in range(7, 13):
        F.both(x, 14, (40, 30, 30))                     # dark brows
    for x in range(5, 27):
        F.put(x, 12, (164, 104, 92))                    # the scar
    for x in range(6, 27, 3):
        F.put(x, 11, (164, 104, 92)); F.put(x, 13, (164, 104, 92))
    if F.open:
        for y in (18, 19, 20):
            for x in range(7, 13):
                F.both(x, y, (244, 244, 240) if y > 18 else (214, 214, 220))
    T = (150, 200, 250)
    end = 24 if F.expr == "shout" else 28
    for y in range(21, end):
        F.both(12, y, T)
    F.both(12, end, (190, 225, 255))


@mark("obanai_eyes")
def _obanai_eyes(F):  # heterochromia: right eye yellow, left eye teal (lighter at the lower rim)
    if not F.open:
        return
    for y, c in ((18, (220, 170, 40)), (19, (240, 200, 60)), (20, (250, 216, 90))):
        for x in (9, 10, 11):
            F.put(x, y, c)
    F.put(10, 19, (20, 14, 10))
    for y, c in ((18, (20, 120, 120)), (19, (30, 160, 160)), (20, (100, 210, 200))):
        for x in (20, 21, 22):
            F.put(x, y, c)
    F.put(21, 19, (10, 40, 40))


@mark("bandage_mouth")
def _bandage_mouth(F):  # white bandages over his nose and mouth
    B, L = (238, 236, 228), (204, 200, 192)
    for y in range(23, 32):
        for x in range(32):
            F.put(x, y, L if (x + 2 * y) % 9 == 0 or y == 23 else B)


@mark("sanemi_face")
def _sanemi_face(F):  # small purple irises in wide eyes, dark rings under them, the scars on his right side
    if F.open:
        for y in range(17, 21):
            for x in range(9, 12):
                F.both(x, y, WHITE_E)
        for x, y in ((10, 18), (11, 18), (10, 19), (11, 19)):
            F.both(x, y, (150, 96, 190))
        F.both(10, 19, (60, 30, 80)); F.put(10, 18, (250, 250, 250))
    for x in range(7, 13):
        F.both(x, 22, F.sr[0])
    S = (206, 128, 116)
    for x, y in ((5, 12), (6, 12), (7, 13), (8, 13), (9, 13), (10, 14), (11, 14), (12, 15), (13, 15)):
        F.put(x, y, S)                                          # forehead to the centre
    for i in range(5):
        F.put(3 + i, 12 + i, S); F.put(7 - i, 12 + i, S)        # the X over his right temple and brow
    for x, y in ((3, 21), (4, 21), (5, 22), (6, 22), (7, 22), (8, 22), (9, 22), (10, 22), (11, 21), (12, 21), (13, 21), (14, 21), (15, 21), (16, 21), (17, 21)):
        F.put(x, y, S)                                          # across the cheekbone and the bridge of the nose


@mark("sanemi_mark")
def _sanemi_mark(F):  # a green paper windmill on his right cheek, a dot each side
    G, D = (60, 160, 80), (30, 100, 50)
    F.art(3, 22, [
        "GGG....",
        ".GG..D.",
        "..GXDD.",
        ".DDXG..",
        ".D..GG.",
        "....GGG",
    ], {"G": G, "D": D, "X": (240, 240, 230)})
    F.put(1, 24, G); F.put(11, 25, G)


# ---------------------------------------------------------------- the swords
ST_GIYU = dict(wrap=(236, 236, 240), diamond=(40, 50, 96), metal=(60, 60, 70), blade=(40, 96, 210), edge=(150, 210, 255),
               spine=(20, 30, 76), kanji=(220, 230, 255), tsuba=(208, 64, 120), tsuba_in=(120, 30, 70), tsuba_shape="hex",
               saya=(26, 28, 40), saya_band=(180, 180, 190))
ST_SHINOBU = dict(wrap=(236, 236, 240), diamond=(110, 60, 150), metal=(200, 170, 90), blade=(120, 220, 200), edge=(240, 255, 252),
                  spine=(50, 150, 130), tsuba=(226, 100, 70), tsuba_in=(240, 200, 120), tsuba_shape="clover", thin=True, curve=0.0,
                  saya=(60, 40, 90), saya_band=(200, 200, 210))
ST_MUI = dict(wrap=(30, 70, 76), diamond=(150, 220, 214), metal=(60, 70, 76), blade=(214, 222, 228), edge=(250, 252, 255),
              spine=(130, 140, 150), tsuba=(64, 84, 92), tsuba_in=(150, 200, 200), tsuba_shape="round", saya=(28, 46, 52), saya_band=(170, 200, 200))
ST_OBANAI = dict(wrap=(36, 36, 70), diamond=(170, 150, 200), metal=(190, 160, 70), blade=(150, 120, 190), edge=(230, 214, 250),
                 spine=(70, 50, 100), tsuba=(200, 168, 70), tsuba_in=(120, 90, 30), tsuba_shape="round", wave=0.05, curve=0.0,
                 saya=(36, 36, 70), saya_band=(200, 200, 210))
ST_OBANAI_RED = dict(ST_OBANAI, blade=(200, 30, 40), edge=(255, 150, 140), spine=(110, 10, 20))
ST_SANEMI = dict(wrap=(30, 56, 36), diamond=(160, 220, 160), metal=(50, 60, 54), blade=(60, 170, 90), edge=(210, 255, 220),
                 spine=(20, 80, 40), tsuba=(40, 70, 50), tsuba_in=(140, 200, 150), tsuba_shape="flower",
                 saya=(70, 72, 76), saya_band=(190, 194, 200))
ST_MITSURI = dict(wrap=(240, 236, 240), diamond=(220, 90, 150), metal=(210, 170, 90), tsuba=(236, 110, 170), tsuba_in=(255, 220, 120),
                  tsuba_shape="clover", saya=(80, 40, 70), saya_band=(220, 200, 210))
WATER, MIST_C = (60, 150, 255), (220, 230, 236)


# ---------------------------------------------------------------- hair
@M.smooth_hair
def giyu_hair(m):
    """Messy raven-black hair: choppy bangs, spikes flaring at the sides, a ponytail at the nape fanning down his back."""
    col = (26, 26, 36)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6, sideburn=False, teeth=0.9)
    for x, tilt in ((-2.8, -0.3), (-1.0, -0.1), (0.8, 0.12), (2.6, 0.3)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.35], 3.2, 2.2, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        for k, (y, z) in enumerate(((30.6, -2.4), (29.6, -0.2), (30.8, 1.6))):
            m.strand([s_ * 4.2, y, z], [s_ * 0.9, -0.5 - 0.15 * k, 0.2], 3.6 + k * 0.4, 2.2, hp, bone="hair", thick=0.6)
    for x, z in ((-2.4, -1.6), (0.0, -2.0), (2.4, -1.6), (-1.6, 1.4), (1.6, 1.4), (0.0, 2.6)):
        m.strand([x, 31.8, z], [x * 0.5, 0.25, z * 0.45 + (0.5 if z > 0 else -0.2)], 3.0, 2.8, hp, bone="hair", thick=0.7, bend=(0, -0.25, 0))
    for x in (-1.2, 0.0, 1.2):  # the low ponytail fanning out down his back
        m.strand([x * 0.6, 26.6, 4.3], [x * 0.25, -1, 0.35], 8.0, 2.6, hp, bone="hair", thick=0.7)
    m.box("hair", [-1.0, 26.2, 3.9], [2.0, 1.0, 1.0], solid((60, 60, 80)))   # the tie


def kikko(face, px, w, h, base):
    """Sabito's half of the haori: interlocking rhombi of green, dark green, yellow and orange."""
    if face in ("up", "down"):
        return
    sw, sh = 6.0, 10.0
    for y in range(h):
        for x in range(w):
            a, b = math.floor(x / sw + y / sh), math.floor(x / sw - y / sh)
            green = (a + b) % 2 == 0
            xc = (a + b + 1) / 2 * sw
            left = x < xc
            c = ((60, 150, 70) if left else (26, 88, 48)) if green else ((236, 196, 70) if left else (224, 128, 40))
            if face not in ("north", "east"):
                c = dark(c, 0.88)
            px[x, y] = c + (255,)


@fighter("giyu", ["water", "mark"])
def giyu(m, form):
    """Giyu Tomioka, the Water Hashira: the charcoal-blue uniform, his haori split down the middle (his right half
    plain carmine, his sister's; his left half Sabito's rhombi in green and yellow), messy black hair with a low
    ponytail, calm lapis eyes, the blue-bladed Nichirin with its hexagonal pink guard. Mark: the red water mark on
    his left cheek."""
    mk = form == "mark"
    head = head_paint((26, 26, 36), (56, 92, 196), True, "giyu_mark" if mk else "giyu")
    uni = (42, 46, 62)
    ds_body(m, head, uni, tabi=(36, 40, 70), strap=(40, 50, 110))
    red = solid((156, 40, 62))
    pat = layered((60, 150, 70), [kikko])
    haori(m, split_painter(red, pat), red, pat, red, pat, lining=(120, 30, 46))
    giyu_hair(m)
    nichirin(m, ST_GIYU)
    saya(m, ST_GIYU)


@M.smooth_hair
def shinobu_hair(m):
    """Raven-black hair fading to purple at the ends: curtain bangs, chin-length locks before the ears, a flat bun at the
    back of the head fastened with a white butterfly ornament."""
    col, tip = (28, 24, 40), (120, 70, 170)
    hp, tp = M.hair_paint(col), M.hair_paint(tip)
    shell(m, col, hairline=30.8, sideburn=False, teeth=0.6)
    for s_ in (1, -1):
        m.strand([s_ * 1.6, 31.8, -4.2], [s_ * 0.6, -0.9, -0.2], 3.4, 2.4, hp, bone="hair", thick=0.7)   # curtain bangs
        m.strand([s_ * 3.4, 31.2, -3.8], [s_ * 0.3, -1, -0.1], 3.2, 2.0, hp, bone="hair", thick=0.7)
        m.strand([s_ * 3.6, 28.4, -3.4], [s_ * 0.1, -1, -0.1], 1.8, 1.6, tp, bone="hair", segs=2, thick=0.7)
        m.strand([s_ * 4.3, 30.4, -1.6], [s_ * 0.05, -1, 0.0], 4.4, 1.8, hp, bone="hair", thick=0.6)    # locks before the ears
        m.strand([s_ * 4.3, 26.6, -1.6], [s_ * 0.05, -1, 0.0], 1.8, 1.4, tp, bone="hair", segs=2, thick=0.6)
    for x in (-2.4, 0.0, 2.4):
        m.strand([x, 30.4, 4.1], [x * 0.1, -1, 0.15], 3.2, 2.8, hp, bone="hair", thick=0.7)
        m.strand([x * 1.05, 27.4, 4.5], [x * 0.1, -1, 0.15], 1.8, 2.0, tp, bone="hair", segs=2, thick=0.7)
    m.box("hair", [-2.2, 28.6, 3.8], [4.4, 2.6, 1.4], hp)                                  # the flat bun
    wing = M._sprite(lambda xf, u: None if ((abs(xf - 0.5) - 0.02) ** 2 / 0.25 + ((u - (0.7 if abs(xf - 0.5) > 0.12 else 0.5)) ** 2) / 0.09) > 1
                     else ((150, 90, 200) if abs(xf - 0.5) > 0.4 else (90, 200, 200) if u > 0.82 else (250, 250, 252)))
    m.box("hair", [-4.9, 30.6, 0.6], [0, 3.0, 4.2], wing, rot=[0, 0, -12], pivot=[-4.9, 32.1, 2.7])   # the butterfly ornament, on her left side
    m.cubes[-1]["hires"] = 4


def butterfly_haori(face, px, w, h, base):
    """Kanae's haori, patterned like a monarch's wings: white fading to pale turquoise and then pink, black veins,
    a black hem with pale turquoise spots in a neat row."""
    if face in ("up", "down"):
        return
    for y in range(h):
        t = y / max(1, h - 1)
        c = mix((250, 250, 252), (150, 220, 214), min(1, t / 0.55)) if t < 0.55 else mix((150, 220, 214), (236, 130, 170), min(1, (t - 0.55) / 0.33))
        for x in range(w):
            cc = c
            if t > 0.88:
                cc = (24, 20, 28)
                if 0.91 < t < 0.97 and (x % 6) in (2, 3):
                    cc = (170, 230, 226)
            px[x, y] = (cc if face in ("north", "east") else dark(cc, 0.9)) + (255,)


@fighter("shinobu", ["insect", "final"])
def shinobu(m, form):
    """Shinobu Kocho, the Insect Hashira: small and slight, the dark purple uniform, her sister's butterfly-wing haori
    (white to turquoise to pink, black hem with turquoise spots), black hair fading to purple with the butterfly
    ornament, big pupil-less purple eyes, butterfly kyahan; her needle-thin stinger sword with a four-lobed guard."""
    final = form == "final"
    head = head_paint((28, 24, 40), (150, 110, 200), True, "shinobu_final" if final else "shinobu")
    uni = (40, 30, 54)
    ds_body(m, head, uni, pants=(68, 46, 108), tabi=(60, 40, 90), strap=(120, 70, 160), wraps=(236, 236, 240), wrap_line=None,
            leg_extra=[gradient([(236, 240, 240), (150, 220, 214), (236, 140, 170)], 0.4, 0.86)])
    hp = layered((250, 250, 252), [butterfly_haori])
    haori(m, hp, hp, sleeve_len=11.4, lining=(230, 230, 236))
    shinobu_hair(m)
    nichirin(m, ST_SHINOBU, length=10.0)
    saya(m, ST_SHINOBU, length=9)


TEN_SKIN = (238, 192, 150)


def tengen_wrap(m):
    """The white head-wrap, the pale grey headband with six pink gems, chains of pale blue gems at the sides, a thin
    white ponytail behind."""
    wrap = layered((244, 244, 246), [lines((SIDES + ("up",), [[(0, 0.3), (1, 0.45)], [(0, 0.7), (1, 0.6)]]), (214, 214, 222))])
    m.box("hair", [-4.4, 29.0, -4.4], [8.8, 3.4, 8.8], wrap)
    m.box("hair", [-3.6, 32.2, -3.6], [7.2, 0.8, 7.2], wrap)

    def gems(face, px, w, h, base):
        if face != "north":
            return
        P, D = (246, 170, 190), (200, 110, 140)
        for gx in (0.36, 0.5, 0.64):          # three large gems in a row
            cx, cy, r = int(w * gx), h // 2, max(1, w // 20)
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    _put(px, w, h, x, y, P if (x - cx) + (y - cy) < 1 else D)
        for gx, gy in ((0.8, 0.35), (0.88, 0.35), (0.84, 0.7)):   # three small ones in a triangle on his left
            _put(px, w, h, int(w * gx), int(h * gy), P)
            _put(px, w, h, int(w * gx) + 1, int(h * gy), D)
    m.box("hair", [-4.5, 28.9, -4.55], [9.0, 1.7, 0.5], layered((200, 204, 212), [gems]))
    blue = SC.swatch((170, 214, 240))
    for s_ in (1, -1):  # the dangling chains of pale blue gems
        for k in range(4):
            m.box("hair", [s_ * 4.35 - 0.3, 27.6 - k * 0.9, -3.6], [0.6, 0.6, 0.6], blue if k % 2 == 0 else SC.swatch((220, 236, 250)))
    m.strand([0, 30.0, 4.5], [0, -1, 0.3], 6.0, 1.2, M.hair_paint((236, 236, 240)), bone="hair", segs=3, thick=0.6)


def cleaver_shape(blade=(150, 156, 172), edge=(236, 240, 248), spine=(40, 40, 48), wrap=(170, 30, 40), wrap2=(240, 220, 220)):
    """One of Tengen's Nichirin cleavers seen flat: a red-wrapped hilt, a round guard, a broad straight blade with a
    slanted tip."""
    hf = 0.26

    def f(xf, u):
        if u < hf:
            if abs(xf - 0.25) > 0.11:
                return None
            return wrap if int(u * 50) % 3 else wrap2
        if u < hf + 0.03:
            return (200, 170, 70) if abs(xf - 0.28) < 0.2 else None
        t = (u - hf - 0.03) / (1 - hf - 0.03)
        if t > 0.86 + 0.14 * (1 - xf) or xf < 0.12 or xf > 0.96:
            return None
        if xf < 0.22:
            return spine
        if xf > 0.84:
            return edge
        return blade
    return f


@fighter("tengen", ["sound", "score"])
def tengen(m, form):
    """Tengen Uzui, the Sound Hashira: very tall and muscular, the sleeveless dark turquoise uniform, thick gold arm
    rings, purple fingerless gloves, burgundy calf wraps, the white head-wrap with the gem headband, red make-up round
    his left eye, gold cuff earrings; a huge Nichirin cleaver in each hand, a chain hanging from each pommel."""
    sc = form == "score"
    head = skin_swap(head_paint((240, 240, 244), (190, 50, 120), True, "tengen_score" if sc else "tengen"), TEN_SKIN)
    uni = (34, 96, 104)
    gold = (236, 194, 64)
    ds_body(m, head, uni, sleeve="none", hand=TEN_SKIN, wraps=(130, 30, 46), wrap_line=(96, 20, 34), tabi=(30, 86, 92),
            strap=(240, 240, 240), undershirt=True,
            arm_extra=[region((0, 0.22, 1, 0.38), gold), region((0, 0.72, 1, 1), (110, 60, 150)), region((0, 0.7, 1, 0.74), gold)])
    for bone, x0 in (("rightArm", 3.9), ("leftArm", -8.1)):   # the sleeveless jacket's shoulders
        m.box(bone, [x0, 21.6, -2.1], [4.2, 2.6, 4.2], solid(uni))
    for s_ in (1, -1):                                         # gold cuff earrings
        m.box("head", [s_ * 4.1 - 0.35, 25.4, -0.6], [0.7, 0.9, 0.9], solid(gold))
    tengen_wrap(m)
    for bone, hx in (("rightArm", 6.0), ("leftArm", -6.0)):
        M.flat_blade(m, bone, (hx, 12.2, -1.2), (0, 0.2, -1), 4.0, 12.0, 3.6, cleaver_shape(), grip=0.8)
        for k in range(5):                                      # the chain from the pommel
            m.box(bone, [hx - 0.25, 12.0 - k * 0.6, 2.4 + k * 0.4], [0.5, 0.5, 0.5], SC.swatch((150, 150, 160) if k % 2 else (90, 90, 100)))
    if sc:  # the Musical Score: notes of light round him
        note = SC.swatch((255, 230, 120), 220)
        for k in range(5):
            a = math.pi * (0.15 + 0.7 * k / 4)
            SC.box_at(m, "body", [math.cos(a) * 6.0, 26 + (k % 2) * 1.5, math.sin(a) * 2.5 + 1.5], [0.9, 0.9, 0.2], note)
            SC.box_at(m, "body", [math.cos(a) * 6.0 + 0.4, 27.2 + (k % 2) * 1.5, math.sin(a) * 2.5 + 1.5], [0.2, 2.2, 0.2], note)


@M.smooth_hair
def mitsuri_hair(m):
    """Thick pink hair fading to lime green halfway down, in three braids (two over the shoulders, one down the back),
    five choppy bangs with green tips."""
    pink, lime = (244, 140, 180), (170, 220, 80)
    pp, lp = M.hair_paint(pink), M.hair_paint(lime)
    shell(m, pink, hairline=30.8, sideburn=False, teeth=0.7)
    for x, tilt in ((-3.0, -0.3), (-1.5, -0.12), (0.0, 0.0), (1.5, 0.12), (3.0, 0.3)):
        m.strand([x, 31.8, -4.2], [tilt, -1, -0.3], 2.6, 2.0, pp, bone="hair", segs=3, thick=0.7)
        m.strand([x * 1.04, 29.6, -4.6], [tilt, -1, -0.2], 1.4, 1.4, lp, bone="hair", segs=2, thick=0.7)
    braid = layered(pink, [lines((SIDES, [[(0, 0.2), (1, 0.4)], [(0, 0.6), (1, 0.8)]]), dark(pink, 0.8))])
    braid_g = layered(lime, [lines((SIDES, [[(0, 0.2), (1, 0.4)], [(0, 0.6), (1, 0.8)]]), dark(lime, 0.8))])
    for s_ in (1, -1):  # the two thick braids falling forward over the shoulders onto her chest
        for k in range(7):
            y = 27.4 - k * 2.1
            c = braid if k < 3 else braid_g
            w = 2.4 - k * 0.1
            x, z = s_ * (4.3 - min(k, 3) * 0.3), -3.4 - min(k, 2) * 0.35
            m.box("hair", [x - w / 2, y - 2.2, z - w / 2], [w, 2.4, w], c, rot=[0, 45, 0], pivot=[x, y - 1.1, z])
    for k in range(7):  # the third braid down her back
        y = 28.0 - k * 2.2
        c = braid if k < 3 else braid_g
        m.box("hair", [-1.2, y - 2.2, 4.3], [2.4, 2.4, 2.0], c, rot=[0, 45, 0], pivot=[0, y - 1.1, 5.3])


def whip_shape(col=(240, 120, 170), edge=(255, 210, 230), hf=0.12):
    """Mitsuri's whip-sword seen flat: a short hilt, then a ribbon-thin pink blade swinging in a long S-curve."""
    def f(xf, u):
        if u < hf:
            return (240, 236, 240) if abs(xf - 0.5) < 0.05 else None
        t = (u - hf) / (1 - hf)
        cx = 0.5 + 0.4 * math.sin(t * math.pi * 1.6) * t
        half = 0.034 * (1 - 0.6 * t) + 0.01
        if abs(xf - cx) > half:
            return None
        return edge if xf > cx else col
    return f


@fighter("mitsuri", ["love", "mark"])
def mitsuri(m, form):
    """Mitsuri Kanroji, the Love Hashira: pink hair turning lime green in three thick braids, big green eyes with a
    beauty mark under each, the plum uniform open over her chest, a short pleated skirt, green ribbed thigh-high
    stockings, a long white haori; her whip-thin pink blade. Mark: a pink heart-shaped mark at her throat."""
    mk = form == "mark"
    head = head_paint((244, 140, 180), (100, 190, 100), True, "mitsuri_mark" if mk else "mitsuri")
    uni = (62, 40, 62)
    sock = (120, 196, 90)
    ds_body(m, head, uni, chest="window", skirt=uni, baggy=False, wraps=sock, wrap_line=None, tabi=(232, 110, 160), strap=(240, 240, 240),
            leg_extra=[region((0, 0.0, 1, 0.3), SKIN), region((0, 0.3, 1, 0.86), sock), region((0, 0.3, 1, 0.38), (40, 110, 140)),
                       lines((SIDES, [[(x, 0.38), (x, 0.86)] for x in (0.25, 0.5, 0.75)]), dark(sock, 0.8))],
            torso_extra=[(lambda f, px, w, h, b: [_put(px, w, h, x, y, (230, 90, 140)) for x, y in ((int(w * 0.6), 1), (int(w * 0.6) + 1, 1), (int(w * 0.6), 2))] if (f == "north" and mk) else None)])
    white = layered((246, 246, 248), [region((0, 0.95, 1, 1), (220, 220, 226))])
    haori(m, white, white, sleeve_len=11.0, lining=(230, 230, 236))
    mitsuri_hair(m)
    M.flat_blade(m, "rightArm", (6, 12.2, -1.2), (0, 0.15, -1), 2.2, 20.0, 6.0, whip_shape(), grip=0.8, res=3)
    nichirin_guard = M.norm((0, 0.15, -1))
    g = [6 + nichirin_guard[0] * 0.8, 12.2 + nichirin_guard[1] * 0.8, -1.2 + nichirin_guard[2] * 0.8]
    m.box("rightArm", [g[0] - 1.1, g[1], g[2] - 1.1], [2.2, 0, 2.2], tsuba_paint(TSUBA["clover"], (236, 110, 170), (255, 220, 120)),
          rot=M._rot_for(nichirin_guard), pivot=g)
    m.cubes[-1]["hires"] = 4


@M.smooth_hair
def muichiro_hair(m):
    """Straight waist-length hair, raven black turning turquoise toward the ends: unruly bangs, a clump sticking out on
    each side, a long fall down his back."""
    col, tip = (24, 30, 40), (80, 200, 190)
    hp, tp = M.hair_paint(col), M.hair_paint(tip)
    shell(m, col, hairline=30.4, sideburn=False, teeth=0.9)
    for x, tilt in ((-2.8, -0.35), (-1.2, -0.1), (0.4, 0.05), (2.0, 0.2), (3.2, 0.4)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.3], 3.0, 2.0, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.2, -2.6], [s_ * 0.1, -1, -0.1], 5.0, 2.0, hp, bone="hair", thick=0.6)     # framing the face
        m.strand([s_ * 4.3, 25.4, -2.8], [s_ * 0.1, -1, -0.1], 2.4, 1.6, tp, bone="hair", segs=2, thick=0.6)
        m.strand([s_ * 4.2, 29.6, 0.6], [s_ * 1.0, -0.2, 0.1], 2.6, 2.0, hp, bone="hair", segs=2, thick=0.6)  # the side clumps
    m.box("hair", [-4.3, 14.0, 3.9], [8.6, 14.6, 1.4], gradient_hair(col, tip, 0.55))
    for x in (-3.0, 0.0, 3.0):
        m.strand([x, 15.0, 4.7], [x * 0.05, -1, 0.2], 3.0, 2.6, tp, bone="hair", segs=2, thick=0.6)


def gradient_hair(col, tip, at=0.6):
    """A flat fall of long hair turning from `col` to `tip` toward the ends, with soft strand lines."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            t = y / max(1, h - 1)
            c = col if t < at else mix(col, tip, min(1, (t - at) / (1 - at) * 1.6))
            for x in range(w):
                cc = c
                if face in SIDES and x % 5 == 0:
                    cc = dark(c, 0.82)
                if face in ("east", "south"):
                    cc = dark(cc, 0.9)
                px[x, y] = cc + (255,)
    return p


@fighter("muichiro", ["mist", "mark"])
def muichiro(m, form):
    """Muichiro Tokito, the Mist Hashira: a slight boy in the dark teal uniform with long, loose kimono sleeves and
    umanori hakama, waist-length black hair turning turquoise, large empty turquoise eyes; a pale mist-grey blade.
    Mark: three carmine clouds on his cheeks and forehead; mist curls round him."""
    mk = form == "mark"
    head = head_paint((24, 30, 40), (60, 170, 170), True, "muichiro_mark" if mk else "muichiro")
    uni = (30, 58, 62)
    ds_body(m, head, uni, sleeve="wide", wraps=uni, wrap_line=None, tabi=(30, 58, 62), strap=(60, 160, 160),
            torso_extra=[glyph(METSU, (226, 226, 230), cy=0.3, scale=1)])
    muichiro_hair(m)
    nichirin(m, ST_MUI, length=13.0)
    saya(m, ST_MUI)


GYO_SKIN = (226, 178, 136)


@M.smooth_hair
def gyomei_hair(m):
    """Medium spiky black hair on top, the sides shaved short."""
    col = (24, 22, 28)
    hp = M.hair_paint(col)
    shell(m, col, hairline=31.2, sideburn=False, teeth=0.4)
    for x in (-2.6, -0.9, 0.9, 2.6):
        for z in (-2.2, 0.4, 2.6):
            m.strand([x, 32.0, z], [x * 0.18, 1, z * 0.15], 2.4, 2.4, hp, bone="hair", segs=3, thick=0.7)
    for x in (-2.0, 0.0, 2.0):
        m.strand([x, 31.8, -4.0], [x * 0.1, 0.3, -1], 2.0, 2.0, hp, bone="hair", segs=2, thick=0.7)


def kanji_patches(face, px, w, h, base):
    """Gyomei's happi: white paper-like patches, each with a short black stroke of the Buddha's chant."""
    if face in ("up", "down"):
        return
    pw, ph = 5, 7
    for j, y0 in enumerate(range(2, h - ph, ph + 4)):
        for i, x0 in enumerate(range(1 + (j % 2) * 3, w - pw, pw + 4)):
            for y in range(y0, y0 + ph):
                for x in range(x0, x0 + pw):
                    _put(px, w, h, x, y, (240, 238, 226))
            g = CHANT[(i + j * 3) % len(CHANT)]
            for r, row in enumerate(g):
                for c, ch in enumerate(row):
                    if ch == "#":
                        _put(px, w, h, x0 + 1 + c, y0 + 1 + r, (30, 26, 30))


def flail_shape():
    """Gyomei's hand-axe seen flat: a dark wooden haft and a crescent blade."""
    def f(xf, u):
        if u < 0.6:
            return (90, 70, 50) if abs(xf - 0.3) < 0.07 else None
        t = (u - 0.6) / 0.4
        r = math.hypot((xf - 0.25) / 0.75, (t - 0.5) / 0.55)
        if r > 1 or xf < 0.25:
            return (90, 70, 50) if abs(xf - 0.3) < 0.07 and t < 0.85 else None
        return (230, 234, 240) if r > 0.8 else (110, 114, 126)
    return f


@fighter("gyomei", ["stone", "mark"])
def gyomei(m, form):
    """Gyomei Himejima, the Stone Hashira: a towering, slightly tanned giant; the dark grey uniform open on a purple
    kimono, sleeves rolled up over huge forearms, an olive happi covered in the Buddha's chant, a big red-beaded
    necklace and red prayer beads, white blind eyes streaming tears, the scar across his forehead; the spiked iron
    flail on its chain in his right hand, the hand-axe in his left. Mark: cracked-earth fissures over his forearms."""
    mk = form == "mark"
    head = skin_swap(head_paint((24, 22, 28), (240, 240, 240), True, "gyomei_mark" if mk else "gyomei"), GYO_SKIN)
    uni = (56, 56, 62)

    def fissures(face, px, w, h, base):
        if face not in SIDES or not mk:
            return
        D = (110, 60, 40)
        for x0 in (int(w * 0.25), int(w * 0.7)):
            x = x0
            for y in range(int(h * 0.5), int(h * 0.95)):
                _put(px, w, h, x, y, D)
                if y % 4 == 0:
                    x += 1 if (y // 4) % 2 else -1
                    _put(px, w, h, x + 2, y, D)
    ds_body(m, head, uni, sleeve="rolled", hand=GYO_SKIN, chest="purple", wraps=(240, 240, 236), wrap_line=(206, 204, 198),
            tabi=GYO_SKIN, strap=(120, 120, 130), arm_extra=[fissures])
    happi = layered((150, 150, 50), [kanji_patches])
    haori(m, happi, happi, sleeves=False)
    for bone, x0 in (("rightArm", 3.6), ("leftArm", -8.4)):   # the happi's short sleeves over the shoulders
        m.box(bone, [x0, 19.0, -2.6], [4.8, 5.4, 5.2], happi)
    bead = SC.swatch((200, 40, 50))
    for k in range(14):  # the big red-bead necklace
        a = 2 * math.pi * k / 14
        SC.box_at(m, "body", [math.cos(a) * 3.6, 23.6 - abs(math.sin(a)) * 0.0 - (1.6 if math.sin(a) < -0.3 else 0), math.sin(a) * 2.6], [1.1, 1.1, 1.1], bead)
    for k in range(8):   # prayer beads looped over his left hand
        SC.box_at(m, "leftArm", [-6.0 + math.cos(k * 0.8) * 1.6, 13.0 - k * 0.35, math.sin(k * 0.8) * 1.6], [0.6, 0.6, 0.6], bead)
    gyomei_hair(m)
    chain = SC.swatch((150, 150, 160))
    for k in range(9):   # the chain hanging from his right fist to the spiked iron ball
        SC.box_at(m, "rightArm", [6.0, 11.6 - k * 0.75, -1.0 - k * 0.12], [0.5, 0.7, 0.5] if k % 2 else [0.7, 0.5, 0.7], chain)
    ball = SC.swatch((80, 82, 92))
    SC.blob(m, "rightArm", [6.0, 3.6, -2.2], [1.9, 1.9, 1.9], ball, slices=5)
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (0.7, 0.7, 0), (-0.7, 0.7, 0), (0.7, -0.7, 0), (-0.7, -0.7, 0)):
        SC.blade(m, "rightArm", [6.0 + d[0] * 1.6, 3.6 + d[1] * 1.6, -2.2 + d[2] * 1.6], d, 1.2, 0.8, 0.8, SC.swatch((60, 62, 70)))
    M.flat_blade(m, "leftArm", (-6.0, 12.2, -1.2), (0, 0.3, -1), 1.0, 7.0, 3.4, flail_shape(), grip=0.2)


@M.smooth_hair
def obanai_hair(m):
    """Straight raven-black hair of uneven lengths, the longest to his shoulders, two strands between his eyes."""
    col = (24, 24, 34)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6, sideburn=False, teeth=0.8)
    for x, tilt in ((-2.8, -0.2), (-0.6, -0.05), (0.6, 0.05), (2.8, 0.2)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.25], 4.6 if abs(x) < 1 else 3.6, 1.8, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.6, -2.6], [s_ * 0.08, -1, 0], 6.0, 2.2, hp, bone="hair", thick=0.6)
        m.strand([s_ * 4.3, 30.6, 0.4], [s_ * 0.1, -1, 0.1], 7.4, 2.4, hp, bone="hair", thick=0.6)
    for x in (-2.6, 0.0, 2.6):
        m.strand([x, 30.6, 4.1], [x * 0.06, -1, 0.15], 7.6, 2.8, hp, bone="hair", thick=0.6)


def kaburamaru(m, red_eye=True):
    """Kaburamaru, the white snake draped round Obanai's neck and shoulders."""
    w = SC.swatch((244, 244, 240))
    pts = [[3.6, 22.4, -2.8], [1.2, 23.6, -3.2], [-1.6, 23.4, -3.0], [-3.8, 22.6, -1.8], [-4.2, 22.4, 0.8], [-2.6, 23.4, 2.8],
           [0.4, 23.6, 3.0], [3.2, 23.0, 2.0], [4.4, 22.0, -0.4]]
    SC.curve_tube(m, "body", pts, 0.62, 0.45, [w, w], n=2)
    SC.blob(m, "body", [4.6, 22.8, -3.0], [0.75, 0.6, 1.0], w, slices=3)
    SC.box_at(m, "body", [4.9, 23.1, -3.7], [0.3, 0.3, 0.2], SC.swatch((210, 30, 40)))


@fighter("obanai", ["serpent", "mark"])
def obanai(m, form):
    """Obanai Iguro, the Serpent Hashira: short and lean, the deep indigo uniform, a black-and-white vertically striped
    haori with horizontal stripes on the hem and cuffs, white bandages over his mouth and on his shins, heterochromatic
    eyes (right yellow, left teal), straight black hair; Kaburamaru the white snake round his neck; his serpentine
    wavy blade. Mark: lavender snake patterns up his left arm, and the blade turns crimson."""
    mk = form == "mark"
    head = head_band(head_paint((24, 24, 34), (220, 180, 50), True, "obanai_mark" if mk else "obanai"), 24.0, 26.4,
                     (238, 236, 228), lines_col=(206, 202, 194))
    uni = (36, 36, 72)

    def snake_mark(face, px, w, h, base):
        if not mk or face not in SIDES:
            return
        L = (190, 150, 230)
        for k in range(3):
            for y in range(h):
                x = int(w * (0.25 + 0.25 * k) + math.sin(y / h * math.pi * 4 + k) * w * 0.1)
                _put(px, w, h, x, y, L)
    ds_body(m, head, uni, tabi=(36, 36, 72), strap=(80, 80, 180), wraps=(240, 240, 236), wrap_line=(206, 204, 198))
    if mk:  # the mark on his left arm, painted over the uniform sleeve (the haori sleeve is rolled back)
        m.box("leftArm", [-8.05, 12.6, -2.05], [4.1, 11.0, 4.1], layered(SKIN, [snake_mark]))
    stripe = layered((240, 240, 236), [vstripes((240, 240, 236), (26, 26, 32), 8), hstripes((240, 240, 236), (26, 26, 32), 0.9, 1.0, 2)])
    haori(m, stripe, stripe, sleeve_r=layered((240, 240, 236), [vstripes((240, 240, 236), (26, 26, 32), 6), hstripes((240, 240, 236), (26, 26, 32), 0.75, 1.0, 2)]),
          sleeve_l="none" if mk else None, sleeve_len=12.4, lining=(30, 30, 36))
    if mk:  # his left sleeve pushed up to the shoulder: the snake mark shows on the bare arm
        m.box("leftArm", [-8.5, 21.0, -2.7], [5.0, 3.2, 5.4], stripe)
    kaburamaru(m)
    obanai_hair(m)
    st = ST_OBANAI_RED if mk else ST_OBANAI
    nichirin(m, st, length=13.0)
    saya(m, ST_OBANAI)


@M.smooth_hair
def sanemi_hair(m):
    """Spiky, ruffled silver-white hair: bangs over the forehead, spikes flaring every way."""
    col = (232, 232, 236)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.8, sideburn=False, teeth=0.9)
    for x, z, dx, dz in ((-2.6, -2.2, -0.6, -0.4), (0, -2.6, 0.0, -0.5), (2.6, -2.2, 0.6, -0.4), (-3.6, 0.4, -0.9, 0.1),
                         (3.6, 0.4, 0.9, 0.1), (-1.8, 1.8, -0.4, 0.6), (1.8, 1.8, 0.4, 0.6), (0, 3.0, 0, 0.8), (-3.2, 2.6, -0.8, 0.6), (3.2, 2.6, 0.8, 0.6)):
        m.strand([x, 31.4, z], [dx * 1.6, 0.6, dz * 1.6], 3.6, 2.6, hp, bone="hair", thick=0.7, bend=(dx * 0.1, -0.15, dz * 0.1))
    for x, tilt in ((-2.4, -0.4), (-0.8, -0.1), (1.6, 0.3)):  # two bangs on his left, one in the middle
        m.strand([x, 31.8, -4.2], [tilt, -1, -0.4], 3.0, 2.0, hp, bone="hair", thick=0.7)


METSU = ["#....#..#.", ".#...####.", "....#.#...", "#...######", ".#.#.#..#.", "...#.#.##.", ".#.#.#.#..", "#.#.#.#.#.", "..#...#..#"]  # 滅
CHANT = [["###", ".#.", "###", "#.#", "###"], ["#.#", "###", "#.#", "###", "#.#"], ["##.", "#.#", "###", "..#", "###"],
         [".#.", "###", ".#.", "#.#", "#.#"], ["#.#", "#.#", "###", ".#.", "###"], ["###", "..#", ".##", "..#", "###"]]
KILL = [".#...#..###.", "..#.#...#.#.", "...#...#..##", "..#.#.......", "######.####.", "..##....#.#.",
        ".#.#.#...#..", "#..#..#.#.#.", "...#...#...#", "...#........"]   # 殺 (kill)


@fighter("sanemi", ["wind", "mark"])
def sanemi(m, form):
    """Sanemi Shinazugawa, the Wind Hashira: tall and scarred, the dark green uniform open to the belt over a scarred
    chest and abs, sleeves rolled to the elbows, a long white haori with 'Kill' (殺) on the back, white buckled leg
    straps, spiky silver-white hair, wide bloodshot purple eyes; the green-bladed Nichirin. Mark: a green paper
    windmill on his right cheek."""
    mk = form == "mark"
    head = head_paint((232, 232, 236), (150, 96, 190), True, "sanemi_mark" if mk else "sanemi")
    uni = (30, 54, 40)

    def chest_scars(face, px, w, h, base):
        if face != "north":
            return
        S = (206, 128, 116)
        for i in range(6):
            _put(px, w, h, w // 2 - 3 + i, int(h * 0.16) + i, S); _put(px, w, h, w // 2 + 2 - i, int(h * 0.16) + i, S)
        for i in range(8):
            _put(px, w, h, w // 2 - 4 + i, int(h * 0.55) + i // 2, S)
    ds_body(m, head, uni, sleeve="rolled", chest="unbuttoned", wraps=(240, 240, 236), wrap_line=(150, 150, 160), tabi=(30, 54, 40),
            strap=(60, 140, 80), torso_extra=[chest_scars])
    white = layered((246, 246, 246), [region((0, 0.96, 1, 1), (220, 220, 226))])
    back = layered((246, 246, 246), [glyph(KILL, (24, 22, 26), cy=0.32, scale=2)])
    haori(m, back, white, sleeve_len=12.0, lining=(230, 230, 236))
    sanemi_hair(m)
    nichirin(m, ST_SANEMI, length=14.0)
    saya(m, ST_SANEMI)


# ==================================================================================
# DRAGON BALL — Piccolo, Perfect Cell
# ==================================================================================
PIC_SKIN, PIC_ORANGE = (112, 178, 64), (236, 146, 52)
M.FACE32.update({
    "piccolo": dict(eye="narrow", brow="none", mouth="corner", marks=["namek_face"]),
    "piccolo_battle": dict(eye="narrow", brow="none", mouth="neutral", marks=["namek_face"]),
    "piccolo_orange": dict(eye="narrow", brow="none", mouth="clench", marks=["namek_face"]),
    "cell": dict(eye="narrow", brow="none", mouth="smirk", marks=["cell_face"]),
    "cell_super": dict(eye="narrow", brow="none", mouth="smirk", marks=["cell_face", "cell_glow"]),
})


@mark("namek_face")
def _namek_face(F):  # a heavy hairless brow ridge, dark lids, black pupils in white eyes, the lips a darker line
    sh, sh2 = F.sr[0], F.sr[1]
    for x in range(4, 15):
        F.both(x, 15, sh2)
        F.both(x, 16, sh)
    for x in (5, 6, 7):
        F.both(x, 14, sh2)
    if F.open:
        for x in (9, 10, 11):
            for y in (18, 19, 20):
                F.both(x, y, WHITE_E)
        F.both(10, 19, (16, 16, 18)); F.both(10, 18, (16, 16, 18))
    for y in (22, 23, 24):
        F.put(16, y, sh2)
    F.put(15, 24, sh); F.put(17, 24, sh)


@mark("cell_face")
def _cell_face(F):  # pale face framed by the black of his carapace, purple stripes down the cheeks, magenta eyes
    B = (34, 30, 46)
    for y in range(12, 31):
        for x in (0, 1, 2):
            F.both(x, y, B)
    for x in range(3, 29):
        F.put(x, 12, B)
    for x in range(5, 14):
        F.both(x, 15, F.sr[1])
    P = (150, 70, 170)
    for y in range(21, 30):
        F.both(6, y, P); F.both(7, y, P)
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (170, 50, 150)); F.both(x, 19, (220, 90, 200)); F.both(x, 20, (240, 140, 220))
        F.both(10, 19, (40, 10, 40))
    if F.mouth_free:
        for x in range(13, 19):
            F.put(x, 27, (120, 60, 110))


@mark("cell_glow")
def _cell_glow(F):
    if F.open:
        F.both(9, 18, (255, 240, 120))


def namek_arm(skin, patch=(236, 150, 164), border=(200, 60, 70), line=(150, 80, 90)):
    """A bare Namekian arm with the pink muscle patches (red border, thin dark lines across them)."""
    def f(face, px, w, h, base):
        if face not in SIDES:
            return
        for (y0, y1) in ((0.08, 0.36), (0.5, 0.8)):
            a, b = int(h * y0), int(h * y1)
            for y in range(a, b):
                for x in range(1, w - 1):
                    edge = y in (a, b - 1) or x in (1, w - 2)
                    c = border if edge else (line if (y - a) % 4 == 2 else patch)
                    _put(px, w, h, x, y, c if face in ("north", "east") else dark(c, 0.9))
    return layered(skin, [f])


def namek_ears(m, skin):
    _strip_ears(m)
    sw, inner = SC.swatch(skin), SC.swatch(dark(skin, 0.78))
    for s_ in (1, -1):  # big pointed Namekian ears sticking out to the sides and sweeping up
        SC.blade(m, "head", [s_ * 3.9, 26.6, 0.2], [s_ * 0.85, 0.75, 0.25], 4.6, 2.4, 0.7, sw, width_dir=[0, 0.3, 1])
        SC.blade(m, "head", [s_ * 4.1, 26.8, 0.0], [s_ * 0.85, 0.75, 0.25], 3.0, 1.2, 0.8, inner, width_dir=[0, 0.3, 1])


def antennae(m, skin, y=30.2):
    sw = SC.swatch(skin)
    for s_ in (1, -1):  # two antennae from the forehead, curving back over the head, a bulb at each tip
        SC.curve_tube(m, "head", [[s_ * 1.2, y, -4.1], [s_ * 1.5, y + 2.4, -3.8], [s_ * 1.7, y + 4.0, -2.6], [s_ * 1.8, y + 4.6, -1.2]], 0.32, 0.26, [sw, sw], n=2)
        SC.blob(m, "head", [s_ * 1.8, y + 4.6, -1.0], [0.45, 0.45, 0.45], sw, slices=2)


@fighter("piccolo", ["cape", "battle", "orange"])
def piccolo(m, form):
    """Piccolo: a tall green Namekian — pointed ears, antennae on his forehead, pink muscle patches on his bare arms,
    the dark violet gi, a sky-blue obi and pointed brown shoes. Cape: the white turban with its purple top and the
    weighted white cape with its big shoulder pads. Battle: weights off. Orange Piccolo (Super Hero): orange skin,
    cream patches, a bulkier body, a black obi and a torn gi."""
    orange = form == "orange"
    skin = PIC_ORANGE if orange else PIC_SKIN
    key = {"cape": "piccolo", "battle": "piccolo_battle", "orange": "piccolo_orange"}[form]
    head = plain_head(skin, skin_swap(head_paint(skin, (20, 20, 20), False, key), skin))
    gi = (104, 54, 150)
    obi = (40, 40, 46) if orange else (100, 180, 236)
    arm = namek_arm(skin, *(((236, 206, 150), (220, 110, 40), (200, 150, 90)) if orange else ()))

    def neck(face, px, w, h, base):  # the gi's wide neckline showing his chest
        if face != "north":
            return
        for y in range(int(h * 0.34)):
            half = int(w * 0.2 * (1 - y / (h * 0.36))) + 1
            for x in range(w // 2 - half, w // 2 + half):
                _put(px, w, h, x, y, skin)
    torn = [lines((SIDES, [[(0.1, 0.96), (0.3, 0.9), (0.5, 0.97), (0.7, 0.9), (0.9, 0.96)]]), dark(gi, 0.6))] if orange else []
    base_body(m, layered(gi, [neck] + torn), arm, layered(gi, [region((0, 0.86, 1, 1), (150, 100, 56))] + torn), head)
    namek_ears(m, skin)
    both_legs(m, [-0.6, 3.6, -2.6], [4.9, 8.4, 5.2], layered(gi, [lines((SIDES, [[(0.3, 0), (0.26, 1)], [(0.7, 0), (0.74, 1)]]), dark(gi, 0.78))]))
    both_legs(m, [0.3, 0, -3.4], [3.3, 1.4, 4.6], solid((150, 100, 56)))                     # pointed shoes
    m.box("body", [-4.5, 10.8, -2.6], [9.0, 2.2, 5.2], layered(obi, [region((0.62, 0.0, 0.78, 1), dark(obi, 0.8), faces=("north",))]))
    m.box("body", [1.4, 7.4, -2.75], [1.6, 3.6, 0.4], solid(obi))                             # the knot's hanging ends
    if orange:  # a bulkier, top-heavy body
        m.box("body", [-4.8, 16.4, -2.6], [9.6, 7.8, 5.2], layered(gi, [neck]))
        both_arms(m, [3.8, 15.6, -2.4], [4.8, 8.6, 4.8], arm)
    if form != "cape":
        antennae(m, skin)
        return
    turban = layered((244, 244, 244), [lines((SIDES, [[(0, 0.25), (1, 0.45)], [(0, 0.6), (1, 0.8)]]), (214, 214, 220))])
    m.box("head", [-4.6, 28.8, -4.6], [9.2, 3.6, 9.2], turban)
    m.box("head", [-3.6, 32.2, -3.6], [7.2, 1.2, 7.2], solid((90, 60, 140)))
    m.box("head", [-2.6, 33.2, -2.6], [5.2, 0.6, 5.2], solid((90, 60, 140)))
    cape = layered((244, 244, 246), [region((0, 0.97, 1, 1), (210, 210, 220))])
    for s_ in (1, -1):  # the big padded shoulders
        m.box("body", [s_ * 5.9 - 3.1, 21.4, -3.0], [6.2, 3.4, 6.0], layered((244, 244, 246), [region((0, 0.8, 1, 1), (214, 214, 224))]))
    m.box("body", [-6.0, 2.6, 2.6], [12.0, 21.6, 0.6], cape)
    for s_ in (1, -1):
        m.box("body", [s_ * 6.0 - 0.3, 4.0, -2.2], [0.6, 18.6, 4.8], cape)
        m.box("body", [s_ * 4.6 - 1.4, 8.0, -3.4], [2.8, 14.4, 0.5], cape)                 # the cape's front edges


def cell_skin(base=(126, 200, 70), spot=(44, 110, 40), seed=0):
    """Cell's insect hide: bright green with dark green spots in a regular, clean scatter."""
    def f(face, px, w, h, b):
        if face == "down":
            return
        for j in range(0, h, 5):
            for i in range(0, w, 6):
                if (i // 6 * 7 + j // 5 * 3 + seed) % 5 in (1, 3):
                    cx, cy = i + 2 + (j // 5 % 2) * 2, j + 2
                    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (2, 1)):
                        _put(px, w, h, cx + dx, cy + dy, spot if face in ("north", "east", "up") else dark(spot, 0.85))
    return layered(base, [f])


@fighter("cell", ["perfect", "super"])
def cell(m, form):
    """Perfect Cell: a pale face framed by the green crest of his carapace — two tall prongs and the black dome between
    them — purple stripes down his cheeks, magenta eyes; black shoulders and chest plate, green spotted hide on his
    arms, belly and thighs, white hands, black shins, yellow-orange feet; his black wings folded down his back like a
    long split cape. Super Perfect: the same body with a golden glow in the eyes (and the SSJ2-like lightning aura)."""
    sup = form == "super"
    G, SP, BLK = (126, 200, 70), (44, 110, 40), (40, 36, 58)
    face = head_paint(G, (220, 90, 200), False, "cell_super" if sup else "cell")
    head = plain_head((236, 234, 230), face)

    def crest(face_, img):  # the green carapace on the top, sides and back of the head
        if face_ == "north":
            head(face_, img)
            return
        cell_skin(G, SP, 2)(face_, img)
    torso = painter_on(cell_skin(G, SP, 1), [region((0, 0, 1, 0.42), BLK), lines((("north",), [[(0.5, 0.42), (0.5, 1)]]), SP)])
    arm = painter_on(cell_skin(G, SP, 3), [region((0, 0, 1, 0.24), BLK), region((0, 0.86, 1, 1), (240, 240, 236))])
    leg = painter_on(cell_skin(G, SP, 4), [region((0, 0.42, 1, 0.9), BLK), region((0, 0.9, 1, 1), (240, 188, 40))])
    base_body(m, torso, arm, leg, crest)
    _strip_ears(m)
    both_arms(m, [3.6, 20.4, -2.4], [4.8, 3.9, 4.8], solid(BLK))                              # black shoulder caps
    m.box("body", [-1.2, 10.6, -2.3], [2.4, 2.6, 0.5], solid(BLK))                           # the dark codpiece
    both_legs(m, [0.2, 0, -3.2], [3.5, 1.2, 1.4], solid((240, 188, 40)))                      # pointed feet
    green, rim = SC.swatch(G), SC.swatch((30, 28, 40))
    for s_ in (1, -1):  # the crest: two tall prongs rising from the top of his head, edged in black
        SC.blade(m, "head", [s_ * 2.7, 31.4, 0.4], [s_ * 0.2, 1, 0.12], 7.0, 4.4, 2.4, rim, width_dir=[0, 0, 1])
        SC.blade(m, "head", [s_ * 2.7, 31.6, 0.2], [s_ * 0.2, 1, 0.12], 6.4, 3.6, 2.8, green, width_dir=[0, 0, 1])
    SC.blob(m, "head", [0, 32.3, 0.9], [2.0, 1.5, 2.4], SC.swatch((44, 42, 60)), slices=3)    # the black dome
    wing = layered((40, 36, 60), [region((0, 0, 0.12, 1), (70, 64, 100)), region((0.88, 0, 1, 1), (70, 64, 100))])
    for s_ in (1, -1):  # the folded wings down his back
        m.box("body", [s_ * 2.6 - 2.5, 3.0, 2.2], [5.0, 20.6, 0.6], wing, rot=[4, 0, s_ * 6], pivot=[s_ * 2.6, 23.4, 2.5])


# ==================================================================================
# JUJUTSU KAISEN — Toji Fushiguro, Mahito
# ==================================================================================
M.FACE32.update({
    "toji": dict(eye="narrow", brow="fine", mouth="smirk", marks=["toji_scar"]),
    "toji_res": dict(eye="narrow", brow="fine", mouth="neutral", marks=["toji_scar", "black_sclera"]),
    "mahito": dict(eye="narrow", brow="fine", mouth="smile", marks=["mahito_face"]),
    "mahito_true": dict(eye="narrow", brow="none", mouth="none", marks=["mahito_true"]),
})


@mark("toji_scar")
def _toji_scar(F):  # the scar across the right corner of his lips
    S = (200, 120, 112)
    for x, y in ((11, 24), (12, 25), (12, 26), (13, 27), (13, 28), (14, 29)):
        F.put(x, y, S)
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 19, (60, 150, 90))
        F.both(10, 19, (20, 60, 30))


@mark("black_sclera")
def _black_sclera(F):  # resurrected: the whites of his eyes turn pitch black
    if not F.open:
        return
    for y in (18, 19, 20):
        for x in range(7, 13):
            c = F.get(x, y)
            if c == WHITE_E or c == (252, 252, 252) or sum(c) > 690:
                F.both(x, y, (14, 12, 16))
    for x in (9, 10, 11):
        F.both(x, 19, (60, 150, 90))


@mark("mahito_face")
def _mahito_face(F):  # a patchwork face: stitched seams, heterochromia (left eye dark blue, right eye grey)
    S, T = (120, 90, 100), (90, 60, 70)
    seam = [(22, 12), (21, 13), (20, 14), (19, 15), (18, 16), (17, 21), (16, 22), (15, 23), (14, 24), (13, 25), (12, 26), (11, 27), (10, 28)]
    for x, y in seam:
        F.put(x, y, S)
    for x, y in seam[::2]:
        F.put(x - 1, y - 1, T); F.put(x + 1, y + 1, T)
    for x in range(18, 27):                      # the seam under his left eye
        F.put(x, 23, S)
        if x % 2 == 0:
            F.put(x, 22, T); F.put(x, 24, T)
    if F.open:
        for y, c in ((18, (130, 136, 146)), (19, (170, 176, 186)), (20, (190, 196, 206))):
            for x in (9, 10, 11):
                F.put(x, y, c)
        for y, c in ((18, (20, 40, 110)), (19, (40, 70, 170)), (20, (70, 100, 200))):
            for x in (20, 21, 22):
                F.put(x, y, c)
        F.put(10, 19, (40, 40, 50)); F.put(21, 19, (10, 16, 50))


@mark("mahito_true")
def _mahito_true(F):  # the Instant Spirit Body: a dark plate over the lower face with jagged teeth, white slit eyes
    D, E = (40, 42, 56), (230, 236, 250)
    for y in range(22, 32):
        for x in range(32):
            F.put(x, y, D)
    for x in range(3, 29):
        F.put(x, 22 + (x % 3 == 0), (90, 96, 120))
    for x in range(8, 24, 2):
        F.put(x, 26, E); F.put(x + 1, 27, E)
    for x in range(6, 14):
        F.both(x, 18, (24, 24, 34))
    if F.open:
        for x in range(7, 13):
            F.both(x, 19, E)


def isoh_shape():
    """The Inverted Spear of Heaven seen flat: a dark red-brown hilt, a chunky steel guard, a straight blade forked
    into two prongs with a rectangular hole near the base."""
    def f(xf, u):
        if u < 0.34:
            return (110, 40, 30) if abs(xf - 0.42) < 0.08 else None
        if u < 0.42:
            return (190, 190, 176) if abs(xf - 0.45) < 0.2 else None
        t = (u - 0.42) / 0.58
        main = abs(xf - 0.4) < 0.1 * (1 if t < 0.85 else (1 - t) / 0.15)
        side = t < 0.62 and 0.56 < xf < 0.66 and not (t < 0.08 and xf > 0.6)
        if t < 0.12 and 0.5 <= xf <= 0.56:
            side = True
        if main and 0.1 < t < 0.2 and abs(xf - 0.4) < 0.04:
            return (40, 40, 48)
        if main or side:
            return (236, 240, 246) if xf > 0.46 and main else (196, 202, 214)
        return None
    return f


def playful_cloud(m, bone="rightArm", hand=(6.0, 12.2, -1.2)):
    """Playful Cloud: three red rods with black caps joined by short chains."""
    red, cap, ch = solid((196, 40, 44)), solid((30, 30, 34)), SC.swatch((150, 150, 160))
    x, y, z = hand
    m.box(bone, [x - 0.4, y - 0.4, z - 6.5], [0.8, 0.8, 6.8], red)                     # the rod in his hand, pointing forward
    m.box(bone, [x - 0.45, y - 0.45, z - 6.9], [0.9, 0.9, 0.6], cap)
    for k in range(3):
        SC.box_at(m, bone, [x, y - 0.6 - k * 0.5, z - 7.1 - k * 0.2], [0.35, 0.5, 0.35], ch)
    m.box(bone, [x - 0.4, y - 8.2, z - 8.2], [0.8, 6.6, 0.8], red, rot=[-20, 0, 0], pivot=[x, y - 2.0, z - 7.6])  # the middle rod hanging
    m.box(bone, [x - 0.45, y - 8.6, z - 8.25], [0.9, 0.6, 0.9], cap, rot=[-20, 0, 0], pivot=[x, y - 2.0, z - 7.6])


def inventory_curse(m):
    """The Inventory: a fat, segmented purple-brown worm curse coiled round his shoulders."""
    a, b = SC.swatch((120, 80, 96)), SC.swatch((96, 60, 76))
    pts = [[4.2, 23.0, -2.6], [2.0, 24.6, -3.2], [-1.0, 24.4, -3.0], [-3.8, 23.4, -2.0], [-4.8, 23.2, 0.6], [-3.2, 24.2, 3.0],
           [0.0, 24.4, 3.4], [3.2, 23.8, 2.6], [4.8, 22.6, 0.0], [5.2, 21.0, -2.0]]
    SC.curve_tube(m, "body", pts, 1.05, 0.9, [a, b], n=3)


@M.smooth_hair
def toji_hair(m):
    """Mid-length straight black hair to his ears, messy, a few strands on the forehead."""
    col = (24, 24, 30)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6, sideburn=True, teeth=0.8)
    for x, tilt in ((-2.6, -0.3), (-0.8, -0.1), (1.0, 0.15), (2.8, 0.35)):
        m.strand([x, 31.8, -4.2], [tilt, -1, -0.4], 2.8, 2.2, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.6, -1.6], [s_ * 0.2, -1, 0.1], 3.6, 2.4, hp, bone="hair", thick=0.6)
        m.strand([s_ * 3.6, 31.6, 2.0], [s_ * 0.5, -0.6, 0.6], 3.4, 2.6, hp, bone="hair", thick=0.6)
    for x, z in ((-1.8, -1.4), (1.8, -1.4), (0.0, 0.6), (-2.0, 2.4), (2.0, 2.4)):
        m.strand([x, 31.9, z], [x * 0.3, 0.3, z * 0.25 + 0.3], 2.8, 2.8, hp, bone="hair", thick=0.7, bend=(0, -0.2, 0))


@fighter("toji", ["sorcerer", "resurrected"])
def toji(m, form):
    """Toji Fushiguro, the Sorcerer Killer: a tall, muscular man with straight black hair, green eyes and the scar at the
    right corner of his lips. Sorcerer Killer: a tight black shirt, baggy white training pants with a dark sash knot,
    black slippers, the Inventory curse coiled round his shoulders, the Inverted Spear of Heaven in his hand.
    Resurrected (Shibuya): the loose white sweater and black trousers, pitch-black sclera, Playful Cloud."""
    res = form == "resurrected"
    head = head_paint((24, 24, 30), (60, 150, 90), True, "toji_res" if res else "toji")
    if res:
        top, pants = (232, 232, 236), (30, 30, 36)
        torso = layered(top, [region((0.36, 0, 0.64, 0.08), dark(top, 0.85), faces=("north",)),
                              lines((("north",), [[(0.2, 0.3), (0.3, 0.9)], [(0.8, 0.3), (0.7, 0.9)]]), dark(top, 0.9))])
        arm = layered(top, [region((0, 0.86, 1, 1), SKIN), region((0, 0.8, 1, 0.86), dark(top, 0.88))])
        leg = layered(pants, [region((0, 0.9, 1, 1), (20, 20, 24))])
        base_body(m, torso, arm, leg, head)
        m.box("body", [-4.4, 9.6, -2.4], [8.8, 3.0, 4.8], layered(top, [region((0, 0.7, 1, 1), dark(top, 0.88))]))   # the loose hem
        playful_cloud(m)
    else:
        blk, pants = (30, 30, 36), (222, 222, 226)

        def muscles(face, px, w, h, base):
            if face != "north":
                return
            for x in range(1, w - 1):
                _put(px, w, h, x, int(h * 0.36), (52, 52, 62))
            for y in range(int(h * 0.42), int(h * 0.95), max(2, h // 8)):
                for x in range(w // 2 - 3, w // 2 + 3):
                    _put(px, w, h, x, y, (50, 50, 60))
            for y in range(int(h * 0.38), h):
                _put(px, w, h, w // 2, y, (50, 50, 60))
        base_body(m, layered(blk, [muscles]), layered(SKIN, [region((0, 0, 1, 0.32), blk)]),
                  layered(pants, [region((0, 0.9, 1, 1), (24, 24, 28))]), head)
        both_legs(m, [-0.9, 1.4, -2.9], [5.5, 10.8, 5.8], layered(pants, [lines((SIDES, [[(0.3, 0), (0.24, 1)], [(0.7, 0), (0.76, 1)]]), dark(pants, 0.86)),
                                                                          region((0, 0.92, 1, 1), dark(pants, 0.9))]))
        m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.2, 5.0], solid((36, 40, 66)))              # the dark sash
        m.box("body", [-0.8, 6.4, -2.75], [1.6, 5.2, 0.4], solid((36, 40, 66)))              # its knot hanging in front
        inventory_curse(m)
        M.flat_blade(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 3.2, 7.0, 2.4, isoh_shape(), grip=0.6)
    toji_hair(m)


@M.smooth_hair
def mahito_hair(m, true=False):
    """Long greyish-blue hair in three big strands tied at the ends: one over his right shoulder, two down his back."""
    col = (150, 166, 196)
    hp = M.hair_paint(col)
    if true:  # the Instant Spirit Body: a crest of blade-like spikes
        crest = SC.swatch((190, 200, 226))
        for k, (x, z) in enumerate(((0, -3.0), (-1.6, -1.6), (1.6, -1.6), (-2.6, 0.4), (2.6, 0.4), (0, -0.6), (-1.4, 2.0), (1.4, 2.0))):
            SC.blade(m, "head", [x, 31.6, z], [x * 0.16, 1, z * 0.1 + 0.25], 5.0 - abs(x) * 0.4, 1.6, 0.6, crest, width_dir=[0, 0, 1])
        return
    shell(m, col, hairline=30.4, sideburn=False, teeth=0.8)
    for x, tilt in ((-2.8, -0.35), (-1.0, -0.1), (1.0, 0.1), (2.8, 0.35)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.35], 3.4, 2.2, hp, bone="hair", thick=0.7)
    tie = solid((60, 60, 80))
    m.strand([3.6, 29.8, -2.4], [0.25, -1, -0.35], 12.0, 2.8, hp, bone="hair", thick=0.7)        # over his right shoulder
    m.box("hair", [4.9, 19.4, -5.8], [1.6, 0.8, 1.6], tie)
    for x in (-1.8, 1.8):                                                                         # two down his back
        m.strand([x, 29.6, 4.0], [x * 0.06, -1, 0.25], 11.0, 2.8, hp, bone="hair", thick=0.7)
        m.box("hair", [x - 0.8, 19.8, 5.8], [1.6, 0.8, 1.6], tie)


def quilt(col, line):
    """A few clean patchwork seams across dark cloth."""
    def f(face, px, w, h, base):
        if face not in SIDES:
            return
        for fy in (0.34, 0.68):
            for x in range(w):
                _put(px, w, h, x, int(h * fy), line)
        for x0 in (int(w * 0.35),):
            for y in range(int(h * 0.34), int(h * 0.68)):
                _put(px, w, h, x0, y, line)
    return f


@fighter("mahito", ["spirit", "true"])
def mahito(m, form):
    """Mahito: a human-looking cursed spirit — long greyish-blue hair in three tied strands, a stitched patchwork face,
    one dark blue and one grey eye, stitches across his arms, a black quilted shawl whose left sleeve hangs in three
    strips, black trousers and white shoes. True form (Instant Spirit Body of Distorted Killing): a tall grey-blue body
    with a crest of blades, a dark plate over the lower face, black legs, blades on his forearms and a long curved
    tail."""
    true = form == "true"
    if true:
        skin = (124, 136, 176)
        head = plain_head(skin, skin_swap(head_paint(skin, (230, 236, 250), False, "mahito_true"), skin))

        def body_lines(face, px, w, h, base):
            if face != "north":
                return
            for x in range(1, w - 1):
                _put(px, w, h, x, int(h * 0.34), dark(skin, 0.72))
            for y in range(int(h * 0.36), h):
                _put(px, w, h, w // 2, y, dark(skin, 0.72))
            for y in (int(h * 0.55), int(h * 0.72)):
                for x in range(w // 2 - 4, w // 2 + 4):
                    _put(px, w, h, x, y, dark(skin, 0.75))
        base_body(m, layered(skin, [body_lines]), layered(skin, [region((0, 0.8, 1, 1), dark(skin, 0.8))]),
                  layered((40, 42, 56), [region((0, 0.9, 1, 1), skin)]), head)
        _strip_ears(m)
        bl = SC.swatch((34, 36, 48))
        for bone, s_ in (("rightArm", 1), ("leftArm", -1)):  # long curved blades off his forearms
            SC.curve_tube(m, bone, [[s_ * 6.6, 16.0, 1.6], [s_ * 7.6, 12.0, -1.0], [s_ * 7.8, 9.0, -6.0], [s_ * 7.0, 8.4, -10.0]], 0.5, 0.12, [bl, bl], n=2)
        tail = SC.swatch((150, 160, 196))
        SC.curve_tube(m, "body", [[0, 11.5, 2.2], [0.6, 7.0, 7.0], [1.4, 4.0, 12.0], [2.2, 6.0, 16.0], [2.6, 10.0, 17.0]], 1.2, 0.2, [tail, tail], n=3)
        mahito_hair(m, True)
        return
    head = head_paint((150, 166, 196), (40, 70, 170), True, "mahito")
    blk = (30, 30, 38)

    def stitches(face, px, w, h, base):
        if face not in SIDES:
            return
        S = (120, 90, 100)
        y = int(h * 0.62)
        for x in range(w):
            _put(px, w, h, x, y, S)
            if x % 2 == 0:
                _put(px, w, h, x, y - 1, S); _put(px, w, h, x, y + 1, S)
    shawl = layered(blk, [quilt(blk, (54, 52, 66))])
    base_body(m, shawl, layered(SKIN, [stitches, region((0, 0, 1, 0.3), blk)]), layered(blk, [region((0, 0.88, 1, 1), (240, 240, 244))]), head)
    m.box("body", [-4.6, 9.0, -2.6], [9.2, 15.2, 5.2], layered(blk, [quilt(blk, (54, 52, 66))]))     # the loose quilted shawl
    for k in range(3):  # its left sleeve hanging in three strips
        m.box("leftArm", [-8.5, 18.4 - k * 2.6, -2.5], [4.6, 1.6, 5.0], shawl)
    m.box("rightArm", [3.6, 18.6, -2.5], [4.6, 5.6, 5.0], shawl)
    mahito_hair(m)


# ==================================================================================
# ONE PIECE — Kaido, Shanks
# ==================================================================================
KAI_SKIN, KAI_BLUE = (204, 150, 108), (168, 184, 232)
M.FACE32.update({
    "kaido": dict(eye="narrow", brow="none", mouth="neutral", brow_col=(30, 20, 20), marks=["kaido_face"]),
    "kaido_hybrid": dict(eye="narrow", brow="none", mouth="clench", marks=["kaido_face", "kaido_fangs"]),
    "shanks": dict(eye="narrow", brow="fine", mouth="smile", marks=["shanks_face"]),
    "shanks_haki": dict(eye="narrow", brow="angled", mouth="neutral", marks=["shanks_face"]),
})


@mark("kaido_face")
def _kaido_face(F):  # a heavy hairless brow ridge, small yellow irises in bloodshot eyes, crow's feet, a frown
    sh, sh2 = F.sr[0], F.sr[1]
    for x in range(4, 15):
        F.both(x, 15, sh2)
        F.both(x, 16, sh)
    for x in (5, 7, 9):
        F.both(x, 13, sh2)                       # forehead lines
    for x in range(6, 12):
        F.both(x, 12, sh2)
    if F.open:
        for x in range(8, 13):
            for y in (18, 19, 20):
                F.both(x, y, (246, 236, 230))
        F.both(10, 19, (236, 200, 40)); F.both(11, 19, (236, 200, 40)); F.both(10, 18, (200, 160, 30))
        F.both(8, 20, (220, 120, 110))           # bloodshot
    F.both(4, 21, sh); F.both(3, 22, sh); F.both(4, 22, sh)    # crow's feet
    for y in (22, 23, 24):
        F.put(17, y, sh2)
    F.put(18, 24, sh); F.put(15, 24, sh)          # the hook of his nose
    if F.mouth_free:
        for x in range(11, 21):
            F.put(x, 27, (110, 50, 46))
        F.put(10, 28, (110, 50, 46)); F.put(21, 28, (110, 50, 46))


@mark("kaido_fangs")
def _kaido_fangs(F):
    F.put(12, 26, (250, 250, 246)); F.put(19, 26, (250, 250, 246))


@mark("shanks_face")
def _shanks_face(F):  # three parallel scars down over his left eye, the thin ring of stubble, plain black eyes
    S = (176, 100, 90)
    for i in range(3):
        for y in range(12, 26):
            x = 19 + i * 2 + (y - 12) // 4
            if 17 <= y <= 21 and 18 <= x <= 25:
                continue                          # the eye itself is untouched
            F.put(x, y, S)
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 19, (30, 24, 24))
        F.both(10, 18, (30, 24, 24))
    B = mix(F.skin, (110, 40, 36), 0.45)
    for x in range(13, 19):
        F.put(x, 25, B)                           # moustache stubble
    for x in range(11, 21):
        F.put(x, 30, B)
    for y in range(27, 30):
        F.both(9, y, B)
    F.both(10, 30, B)


def scale_paint(base, line, size=4):
    """Clean overlapping dragon scales (scallops) in rows."""
    def f(face, px, w, h, b):
        if face == "down":
            return
        for y in range(h):
            for x in range(w):
                row = y // size
                xx = (x + (size // 2 if row % 2 else 0)) % size
                yy = y % size
                if yy == size - 1 and xx not in (0,) or (xx == 0 and yy > size // 2):
                    _put(px, w, h, x, y, line if face in ("north", "east", "up") else dark(line, 0.9))
    return layered(base, [f])


def kanabo(m, bone="rightArm", hand=(6.0, 12.2, -1.2), L=19.0):
    """Hassaikai, Kaido's kanabo: a long black iron club thickening toward the end, studded with rows of spikes."""
    x, y, z = hand
    iron, stud = solid((40, 40, 46)), SC.swatch((150, 150, 160))
    m.box(bone, [x - 0.5, y - 0.5, z - 5.0], [1.0, 1.0, 6.0], solid((70, 50, 40)))             # the grip
    m.box(bone, [x - 1.1, y - 1.1, z - L], [2.2, 2.2, L - 5.0], iron)                           # the head of the club
    m.box(bone, [x - 1.3, y - 1.3, z - L - 0.4], [2.6, 2.6, 0.6], iron)
    for k in range(7):
        zz = z - 6.5 - k * (L - 7.5) / 6
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            SC.box_at(m, bone, [x + dx * 1.35, y + dy * 1.35, zz], [0.6 + abs(dy) * 0.0, 0.6, 0.6], stud)
    m.box(bone, [x - 0.15, y - 0.15, z - L - 2.4], [0.3, 0.3, 2.0], solid((150, 150, 160)))       # the ring at the end


@fighter("kaido", ["human", "hybrid"])
def kaido(m, form):
    """Kaido of the Beasts: huge and top-heavy — a wild black mane, two great grey-white horns curving forward and up,
    a heavy brow, small yellow eyes, a long Fu Manchu moustache and a spiked goatee; bare chest with the X scar right
    of his abs, the red scale tattoo down his left arm ending in a white skull, spiked bracelets, the blue-purple
    feathered coat on his shoulders, the shimenawa rope belt with its white shide, lavender flaps with gold chains,
    grey-green trousers in black boots, the kanabo Hassaikai. Hybrid: azure dragon scales over his arms and face,
    lavender horns and antlers, clawed hands, and a long dragon tail."""
    hyb = form == "hybrid"
    skin = KAI_SKIN
    face_skin = (176, 188, 228) if hyb else skin
    head = skin_swap(head_paint((26, 24, 30), (236, 200, 40), True, "kaido_hybrid" if hyb else "kaido"), face_skin)

    def chest(face, px, w, h, base):
        if face != "north":
            return
        sh = dark(skin, 0.8)
        for x in range(2, w - 2):
            _put(px, w, h, x, int(h * 0.34), sh)
        for y in range(int(h * 0.36), h):
            _put(px, w, h, w // 2, y, sh)
        for y in (int(h * 0.52), int(h * 0.68), int(h * 0.84)):
            for x in range(w // 2 - 4, w // 2 + 4):
                _put(px, w, h, x, y, sh)
        X = (150, 96, 70)                                      # the X scar right of his abs (his right = image left)
        for i in range(8):
            _put(px, w, h, 3 + i, int(h * 0.3) + i * 2, X); _put(px, w, h, 10 - i, int(h * 0.3) + i * 2, X)
        R, O = (170, 60, 46), (236, 140, 60)                    # the scale tattoo on his left pec
        for j in range(3):
            for i in range(3):
                cx, cy = w - 5 - i * 3 - (j % 2), 2 + j * 3
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    _put(px, w, h, cx + dx, cy + dy, R)
                _put(px, w, h, cx - 1, cy, O); _put(px, w, h, cx, cy - 1, O)

    def tattoo_arm(face, px, w, h, base):
        if face not in ("north", "west", "east"):
            return
        R, O = (170, 60, 46), (236, 140, 60)
        for j in range(0, int(h * 0.62), 3):
            for i in range(0, w, 3):
                cx, cy = i + (j // 3 % 2), j
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    _put(px, w, h, cx + dx, cy + dy, R)
                _put(px, w, h, cx + 2, cy, O); _put(px, w, h, cx, cy + 2, O)
        if face == "north":                                    # the white skull on the forearm
            sk = [".###.", "#####", "#.#.#", "#####", ".#.#."]
            for r, row in enumerate(sk):
                for c, ch in enumerate(row):
                    if ch == "#":
                        _put(px, w, h, w // 2 - 2 + c, int(h * 0.66) + r, (244, 244, 240))
                    elif ch == ".":
                        pass
    bracelet = [region((0, 0.8, 1, 0.88), (30, 30, 34))]
    if hyb:
        arm_r = scale_paint(KAI_BLUE, (120, 136, 196))
        arm_l = arm_r
    else:
        arm_r = layered(skin, bracelet)
        arm_l = layered(skin, [tattoo_arm] + bracelet)
    legs = layered((104, 116, 96), [region((0, 0.6, 1, 1), (26, 26, 30))])
    base_body(m, layered(skin, [chest]), arm_r, legs, head)
    for c in m.cubes:
        if c["bone"] == "leftArm":
            c["paint"] = arm_l
    both_arms(m, [3.6, 15.0, -2.4], [4.8, 9.2, 4.8], arm_r)                                    # thick shoulders and arms
    m.box("leftArm", [-8.4, 15.0, -2.4], [4.8, 9.2, 4.8], arm_l)
    m.cubes[:] = [c for i, c in enumerate(m.cubes) if not (c["bone"] == "leftArm" and c["size"] == [4.75, 9.25, 4.75] and c["paint"] is arm_r)]
    m.box("body", [-4.6, 17.0, -2.5], [9.2, 7.2, 5.0], layered(skin, [chest]))                 # the broad chest
    for bone, x in (("rightArm", 6.0), ("leftArm", -6.0)):  # spiked bracelets
        m.box(bone, [x - 2.5, 13.8, -2.5], [5.0, 1.2, 5.0], solid((30, 30, 34)))
        for k in range(4):
            a = k * math.pi / 2
            SC.blade(m, bone, [x + math.cos(a) * 2.5, 14.4, math.sin(a) * 2.5], [math.cos(a), 0, math.sin(a)], 0.9, 0.6, 0.4, SC.swatch((230, 190, 60)))
    both_legs(m, [-0.6, 3.4, -2.7], [5.0, 8.8, 5.4], layered((104, 116, 96), [lines((SIDES, [[(0.3, 0), (0.24, 1)], [(0.7, 0), (0.76, 1)]]), (84, 94, 78))]))
    both_legs(m, [-0.2, 0, -2.4], [4.3, 4.0, 4.8], solid((28, 28, 32)))                       # black boots
    # the shimenawa: a thick laid rope round his waist, white zigzag shide hanging in front
    rope = layered((236, 230, 210), [lines((SIDES, [[(x, 0), (x + 0.25, 1)] for x in (-0.2, 0.05, 0.3, 0.55, 0.8)]), (196, 186, 160))])
    m.box("body", [-5.0, 10.4, -3.0], [10.0, 2.6, 6.0], rope)
    shide = M._sprite(lambda xf, u: (250, 250, 250) if abs(xf - (0.5 + 0.22 * (1 if int((1 - u) * 4) % 2 else -1) * (((1 - u) * 4) % 1 - 0.5) * 2)) < 0.2 else None)
    for x in (-1.6, 1.6):
        m.box("body", [x - 1.0, 5.6, -3.15], [2.0, 4.8, 0], shide)
        m.cubes[-1]["hires"] = 3
    lav = layered((170, 150, 210), [region((0, 0.9, 1, 1), (130, 110, 170))])
    for s_ in (1, -1):  # lavender flaps with golden chains, red ribbons between them
        m.box("body", [s_ * 3.4 - 1.8, 5.8, -3.1], [3.6, 4.8, 0.5], lav)
        gc = SC.swatch((230, 190, 60))
        SC.curve_tube(m, "body", [[s_ * 3.4 - 1.4, 6.0, -3.35], [s_ * 3.4, 4.8, -3.4], [s_ * 3.4 + 1.4, 6.0, -3.35]], 0.3, 0.3, [gc, gc], n=2)
    for x in (-0.6, 0.0, 0.6):
        m.box("body", [x - 0.15, 7.0, -3.2], [0.3, 3.4, 0.2], solid((200, 40, 40)))
    # the feathered blue-purple coat draped on his shoulders
    fur = (66, 58, 140)

    def feathers(face, px, w, h, base):
        if face not in SIDES:
            return
        for x in range(w):
            cut = int(h * 0.06 * (1 + math.sin(x * 1.7)))
            for y in range(h - cut, h):
                px[x, y] = (0, 0, 0, 0)
            if x % 5 == 0:
                for y in range(int(h * 0.1), h - cut - 2):
                    _put(px, w, h, x, y, light(fur, 0.12))
    coat = layered(fur, [feathers])
    m.box("body", [-7.6, 2.0, 2.4], [15.2, 22.8, 1.0], coat)
    for s_ in (1, -1):
        m.box("body", [s_ * 7.0 - 0.6, 2.0, -2.8], [1.2, 22.8, 5.4], coat)
        m.box("body", [s_ * 5.6 - 2.2, 21.6, -3.4], [4.4, 3.8, 6.8], layered(fur, [lines((SIDES + ("up",), [[(x, 0), (x, 1)] for x in (0.2, 0.45, 0.7, 0.9)]), light(fur, 0.15))]))
    m.box("body", [-4.2, 23.6, 1.6], [8.4, 2.6, 2.4], layered(fur, []))                       # the collar behind his neck
    # horns
    hc = (200, 180, 220) if hyb else (226, 224, 214)
    hs = SC.swatch(hc)
    for s_ in (1, -1):
        SC.curve_tube(m, "head", [[s_ * 4.0, 29.4, -0.4], [s_ * 6.4, 30.4, -1.6], [s_ * 7.6, 33.6, -1.4], [s_ * 7.2, 37.4, -0.2]], 1.1, 0.15, [hs, hs], n=3)
        if hyb:  # the dragon's antlers branching from the crown
            ant = SC.swatch((176, 150, 206))
            SC.curve_tube(m, "head", [[s_ * 1.6, 32.0, 0.6], [s_ * 2.4, 35.0, 1.4], [s_ * 3.0, 38.4, 1.2]], 0.55, 0.12, [ant, ant], n=2)
            SC.curve_tube(m, "head", [[s_ * 2.4, 35.0, 1.4], [s_ * 4.0, 36.4, 2.4]], 0.35, 0.1, [ant, ant], n=1)
    # hair: a wild black mane of flat locks swept back to his mid-back
    col = (26, 24, 30)
    hp = M.hair_paint(col)
    shell(m, col, hairline=31.2, sideburn=True, teeth=0.6)
    for k, x in enumerate((-3.4, -1.7, 0.0, 1.7, 3.4)):
        m.strand([x, 31.6, 1.0], [x * 0.12, -0.6, 1], 10.0 + (k % 2) * 2, 3.0, hp, bone="hair", thick=0.6)
        m.strand([x * 1.1, 30.4, 4.0], [x * 0.1, -1, 0.35], 11.0, 3.0, hp, bone="hair", thick=0.6)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.6, -1.6], [s_ * 0.4, -1, -0.1], 6.0, 2.6, hp, bone="hair", thick=0.6)
        m.strand([s_ * 3.0, 32.2, -1.2], [s_ * 0.6, 0.9, 0.1], 3.6, 2.6, hp, bone="hair", thick=0.6)
    # the long Fu Manchu moustache and the spiked goatee
    mo = SC.swatch((24, 22, 28))
    for s_ in (1, -1):
        SC.curve_tube(m, "head", [[s_ * 1.2, 25.4, -4.3], [s_ * 2.6, 24.4, -4.6], [s_ * 3.2, 20.0, -5.0], [s_ * 3.0, 14.0, -4.4]], 0.32, 0.18, [mo, mo], n=3)
    SC.blade(m, "head", [0, 24.4, -4.2], [0, -1, -0.25], 3.0, 1.6, 0.6, mo, width_dir=[1, 0, 0])
    if hyb:
        tail, belly = SC.swatch(KAI_BLUE), SC.swatch((240, 214, 150))
        pts = [[0, 10.0, 2.6], [0.4, 6.0, 7.0], [1.6, 2.0, 12.0], [3.4, 1.0, 17.0], [5.6, 2.4, 21.0]]
        SC.curve_tube(m, "body", pts, 2.2, 0.3, [tail, tail], n=3)
        SC.curve_tube(m, "body", [[p[0], p[1] - 0.9, p[2]] for p in pts], 1.6, 0.2, [belly, belly], n=3)
        for k in range(6):  # black mane flames along the tail's spine
            p = pts[min(4, k)]
            SC.blade(m, "body", [p[0], p[1] + 1.6, p[2] + 0.5], [0.1, 1, 0.5], 2.2, 1.2, 0.4, SC.swatch((30, 28, 34)))
        claw = SC.swatch((240, 236, 220))
        for bone, x in (("rightArm", 6.0), ("leftArm", -6.0)):
            for k in range(4):
                SC.blade(m, bone, [x + (k - 1.5) * 0.9, 12.0, -2.1], [0, -1, -0.6], 1.4, 0.5, 0.4, claw)
    kanabo(m)


def gryphon_shape(haki=False):
    """Gryphon seen flat: a dark teal-wrapped hilt, a silver ring guard, a slender gently curved saber blade."""
    def f(xf, u):
        if u < 0.2:
            return (40, 90, 100) if abs(xf - 0.45) < 0.08 else None
        if u < 0.25:
            r = math.hypot((xf - 0.45) / 0.4, (u - 0.225) / 0.04)
            return (226, 226, 230) if 0.55 < r < 1.0 or abs(xf - 0.45) < 0.1 else None
        t = (u - 0.25) / 0.75
        cx = 0.45 + 0.1 * t * t
        half = 0.09 * (1 if t < 0.86 else (1 - t) / 0.14)
        if abs(xf - cx) > half:
            return None
        if haki:
            return (200, 30, 40) if xf > cx + half * 0.5 else (24, 20, 26)
        return (250, 250, 255) if xf > cx + half * 0.4 else (196, 200, 212)
    return f


@M.smooth_hair
def shanks_hair(m):
    """Deep crimson hair, wavy and slicked back, a few strands falling down the sides of his face."""
    col = (168, 30, 40)
    hp = M.hair_paint(col)
    shell(m, col, hairline=31.0, sideburn=True, teeth=0.6)
    for x in (-2.8, -1.0, 1.0, 2.8):
        m.strand([x, 32.0, -2.6], [x * 0.08, 0.3, 1], 6.0, 2.8, hp, bone="hair", thick=0.7, bend=(0, -0.2, 0))
    for s_ in (1, -1):
        m.strand([s_ * 3.6, 31.4, -3.8], [s_ * 0.3, -1, -0.1], 5.0, 1.8, hp, bone="hair", thick=0.6)
        m.strand([s_ * 4.2, 30.6, 0.6], [s_ * 0.2, -1, 0.3], 5.6, 2.2, hp, bone="hair", thick=0.6)
    for x in (-2.0, 0.0, 2.0):
        m.strand([x, 30.0, 4.1], [x * 0.1, -1, 0.3], 5.0, 2.6, hp, bone="hair", thick=0.6)


@fighter("shanks", ["captain", "conqueror"])
def shanks(m, form):
    """Red-Haired Shanks: crimson hair, the three scars over his left eye, a thin ring of stubble; a white shirt
    half-open on his chest, a red sash holding Gryphon, below-the-knee brown trousers with gold buttons, sandals; the
    long black high-collared cape (grey inside) draped over his shoulders — and no left arm below the shoulder.
    Conqueror: Gryphon coated black with Conqueror's Haki, a red edge."""
    haki = form == "conqueror"
    head = head_paint((168, 30, 40), (30, 24, 24), True, "shanks_haki" if haki else "shanks")
    shirt = (244, 244, 240)

    def open_shirt(face, px, w, h, base):
        if face != "north":
            return
        for y in range(int(h * 0.62)):
            half = int(w * 0.18 * (1 - y / (h * 0.66))) + 1
            for x in range(w // 2 - half, w // 2 + half):
                _put(px, w, h, x, y, SKIN)
    pants = (126, 100, 74)
    leg = layered(pants, [region((0, 0.56, 1, 1), SKIN), region((0, 0.92, 1, 1), (110, 80, 50)),
                          lines((("east", "west"), [[(0.5, 0.05), (0.5, 0.5)]]), (220, 180, 70))])
    base_body(m, layered(shirt, [open_shirt]), layered(shirt, [region((0, 0.86, 1, 1), SKIN), region((0, 0.82, 1, 0.86), dark(shirt, 0.9))]), leg, head)
    m.cubes[:] = [c for c in m.cubes if c["bone"] != "leftArm"]                              # the lost left arm
    m.box("leftArm", [-7.8, 20.6, -1.8], [3.8, 3.4, 3.6], layered(shirt, [region((0, 0.8, 1, 1), dark(shirt, 0.85))]))  # the stump in its sleeve
    both_legs(m, [-0.5, 5.2, -2.6], [4.9, 7.0, 5.2], layered(pants, [lines((SIDES, [[(0.3, 0), (0.26, 1)]]), dark(pants, 0.8))]))
    m.box("body", [-4.4, 10.8, -2.5], [8.8, 1.8, 5.0], solid((190, 40, 40)))                  # the red sash
    cape, inner = (24, 24, 28), (110, 110, 118)
    cp = layered(cape, [region((0, 0, 1, 1), inner, faces=("north",))])
    m.box("body", [-6.4, 1.6, 2.4], [12.8, 22.8, 0.6], layered(cape, []))
    for s_ in (1, -1):
        m.box("body", [s_ * 6.2 - 0.3, 1.6, -2.6], [0.6, 22.8, 5.2], cp)
        m.box("body", [s_ * 5.0 - 2.0, 22.0, -3.0], [4.0, 2.6, 6.0], layered(cape, []))       # over the shoulders
    m.box("body", [-4.4, 23.6, 1.8], [8.8, 3.2, 1.0], layered(cape, [region((0, 0, 1, 1), inner, faces=("north",))]))  # the high collar
    m.box("body", [-6.6, 1.6, -2.7], [2.6, 21.0, 0.5], layered(cape, []))                     # the cape falls over his left side
    shanks_hair(m)
    M.flat_blade(m, "rightArm", (6, 12.2, -1.2), (0, 0.15, -1), 3.4, 13.0, 2.4, gryphon_shape(haki), grip=0.8)


# ==================================================================================
# NARUTO — Pain (the Deva Path), Minato Namikaze
# ==================================================================================
M.FACE32.update({
    "pain": dict(eye="narrow", brow="fine", brow_col=(230, 110, 30), mouth="neutral", marks=["rinnegan_both", "pain_piercings"]),
    "pain_six": dict(eye="narrow", brow="sharp", brow_col=(230, 110, 30), mouth="neutral", marks=["rinnegan_both", "pain_piercings"]),
    "minato": dict(eye="anime", brow="fine", brow_col=(220, 180, 40), mouth="neutral", marks=[]),
    "minato_kcm": dict(eye="anime", brow="angled", brow_col=(120, 70, 20), mouth="neutral", marks=["minato_kcm"]),
})


@mark("pain_piercings")
def _pain_piercings(F):  # three studs each side down the bridge of the nose, two under the lower lip
    S, H = (52, 52, 60), (150, 150, 160)
    for x in (13, 18):
        for y in (20, 22, 24):
            F.put(x, y, S)
    for x in (14, 17):
        F.put(x, 29, S); F.put(x, 30, S)


@mark("minato_kcm")
def _minato_kcm(F):
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (240, 140, 40)); F.both(x, 19, (250, 190, 60)); F.both(x, 20, (250, 210, 90))
        F.both(10, 19, (60, 30, 10))
    for x in range(4, 9):          # the dark rims round the eyes of the chakra mode
        F.both(x, 16, (90, 50, 10))


def rain_plate(face, px, w, h, base):
    """The Amegakure plate: four vertical strokes, cut through by one horizontal scratch."""
    if face != "north":
        return
    D = (40, 40, 48)
    for gx in (0.32, 0.44, 0.56, 0.68):
        for y in range(int(h * 0.2), int(h * 0.8)):
            _put(px, w, h, int(w * gx), y, D)
    for x in range(int(w * 0.2), int(w * 0.8)):
        _put(px, w, h, x, h // 2, D)


@M.smooth_hair
def pain_hair(m):
    """Bright orange hair in short, sharp spikes all over."""
    col = (250, 128, 34)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6, sideburn=False, teeth=0.8)
    for k in range(11):
        a = 2 * math.pi * k / 11
        dx, dz = math.sin(a), -math.cos(a)
        m.strand([dx * 2.6, 31.6, dz * 2.6], [dx * 0.8, 0.85, dz * 0.8], 4.2, 2.6, hp, bone="hair", thick=0.7)
    for x in (-1.4, 0.0, 1.4):
        m.strand([x, 31.8, 0.0], [x * 0.2, 1, 0.1], 4.6, 2.8, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 3.6, 30.4, -3.4], [s_ * 0.5, -0.8, -0.3], 3.0, 1.8, hp, bone="hair", thick=0.6)


@fighter("pain", ["deva", "six"])
def pain(m, form):
    """Pain, the Deva Path: spiky orange hair, the Rinnegan in both eyes, black piercings down his nose and under his
    lip, studs along his ears, the Amegakure headband scratched through, the Akatsuki cloak with red clouds and its
    high collar. Six Paths: black chakra receiver rods in his hands."""
    six = form == "six"
    head = head_paint((250, 128, 34), (200, 190, 230), True, "pain_six" if six else "pain")
    cloak, lining = (24, 24, 30), (150, 24, 30)
    torso = layered(cloak, [akatsuki_cloud(0.3, 0.55, 0.16, ("north",)), akatsuki_cloud(0.62, 0.3, 0.14, ("south",)),
                            akatsuki_cloud(0.5, 0.5, 0.22, ("east", "west")), region((0, 0, 1, 1), lining, faces=("down",))])
    arm = layered(cloak, [akatsuki_cloud(0.5, 0.3, 0.3, ("east", "west")), region((0, 0.86, 1, 1), SKIN)])
    base_body(m, torso, arm, layered((110, 110, 120), [region((0, 0.86, 1, 1), (40, 60, 120))]), head)
    for s_ in (1, -1):
        m.box("body", [s_ * 2.35 - 2.05, 2.4, -2.75], [4.1, 9.8, 0.5], layered(cloak, [akatsuki_cloud(0.5 - s_ * 0.1, 0.45, 0.22, ("north",)),
                                                                                  region((0, 0, 1, 1), lining, faces=("south",))]))
        m.box("body", [s_ * 4.5 - 0.3, 2.4, -2.4], [0.6, 9.8, 4.8], layered(cloak, [akatsuki_cloud(0.5, 0.5, 0.3, ("east", "west"))]))
    m.box("body", [-4.6, 2.4, 2.25], [9.2, 9.8, 0.5], layered(cloak, [akatsuki_cloud(0.35, 0.4, 0.17, ("south",)), akatsuki_cloud(0.72, 0.68, 0.13, ("south",))]))
    m.box("body", [-4.4, 23.6, -2.7], [8.8, 2.6, 5.4], layered(cloak, [region((0, 0, 1, 1), lining, faces=("up",)),
                                                                      region((0.4, 0, 0.6, 1), lining, faces=("north",))]))
    m.box("head", [-4.3, 28.8, -4.3], [8.6, 1.8, 8.6], solid((34, 36, 50)))                  # the headband
    m.box("head", [-2.4, 28.6, -4.6], [4.8, 2.2, 0.35], layered((196, 200, 212), [rain_plate]))
    stud = SC.swatch((48, 48, 56))
    for s_ in (1, -1):  # studs along the rims of his ears
        for k in range(4):
            SC.box_at(m, "head", [s_ * 4.85, 26.2 + k * 0.6, 0.6 - k * 0.15], [0.3, 0.3, 0.3], stud)
    pain_hair(m)
    if six:
        rod = solid((26, 24, 30))
        for bone, x in (("rightArm", 6.0), ("leftArm", -6.0)):
            m.box(bone, [x - 0.25, 11.6, -9.0], [0.5, 0.5, 9.0], rod)                          # a chakra receiver in each hand
            m.box(bone, [x - 0.45, 11.4, -9.6], [0.9, 0.9, 0.8], rod)


MIN_HAIR = (252, 214, 60)


@M.smooth_hair
def minato_hair(m, col=MIN_HAIR):
    """Spiky blond hair, the spikes swept back, with long jaw-length bangs framing both sides of his face."""
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.8, sideburn=False, teeth=0.8)
    crown = [(0, -2.0, 0.0, 5.0), (2.2, -1.2, 0.5, 4.6), (-2.2, -1.2, -0.5, 4.6), (3.0, 0.8, 0.9, 4.4), (-3.0, 0.8, -0.9, 4.4),
             (1.4, 2.6, 0.4, 4.4), (-1.4, 2.6, -0.4, 4.4), (0, 0.6, 0, 4.6)]
    for x, z, lean, ln in crown:
        m.strand([x, 32.0, z], [lean, 0.7, z * 0.3 + 0.35], ln, 3.0, hp, bone="hair", thick=0.8, bend=(x * 0.03, -0.08, 0.05))
    for x in (-2.4, 0.0, 2.4):
        m.strand([x, 30.4, 3.9], [x * 0.18, -0.4, 1], 4.4, 2.8, hp, bone="hair", thick=0.75)
    for x, tilt in ((-1.6, -0.2), (0.2, 0.0), (1.8, 0.2)):
        m.strand([x, 31.6, -4.1], [tilt, 0.6, -0.6], 3.0, 2.0, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):  # the long bangs down to his jaw
        m.strand([s_ * 3.7, 31.4, -3.9], [s_ * 0.12, -1, -0.12], 7.2, 2.0, hp, bone="hair", thick=0.6)


def kunai_shape():
    """The Flying Thunder God kunai seen flat: the ring, a wrapped grip, and three prongs (a long central blade)."""
    def f(xf, u):
        if u < 0.12:
            r = math.hypot((xf - 0.5) / 0.3, (u - 0.06) / 0.06)
            return (180, 180, 190) if 0.5 < r < 1.0 else None
        if u < 0.4:
            return (236, 236, 236) if abs(xf - 0.5) < 0.07 else None
        t = (u - 0.4) / 0.6
        if abs(xf - 0.5) < 0.13 * (1 - t):
            return (210, 214, 226)
        for s_ in (-1, 1):
            if t < 0.45 and abs(xf - (0.5 + s_ * (0.18 + 0.22 * t))) < 0.05 * (1 - t / 0.45):
                return (190, 194, 206)
        return None
    return f


def flames_hem(face, px, w, h, base):
    """The Hokage haori's hem: red flames licking up from the bottom."""
    if face not in SIDES:
        return
    for x in range(w):
        top = int(h * (0.7 + 0.12 * math.sin(x * 0.9 + (1 if face == "south" else 0))))
        for y in range(top, h):
            _put(px, w, h, x, y, (220, 50, 40) if y > top + 1 else (250, 120, 60))


HOKAGE = ["..####..", ".#....#.", "#.#..#.#", "#..##..#", "########", "..#..#..",           # 四
          "........", ".#.###..", "#..#.#..", ".#.##...", ".#.#..#.", ".#.#..#.",            # 代
          "........", "..####..", "..#..#..", "..####..", "..#..#..", "..####..",              # 目
          "........", "#..#..#.", ".#.#.#..", "...#....", "..#.#...", "##...##.",             # 火
          "........", "###.#.#.", "###..#..", "#.#.#.#.", "###...#.", "#.#.##.."]             # 影


@fighter("minato", ["hokage", "kcm"])
def minato(m, form):
    """Minato Namikaze, the Fourth Hokage: spiky blond hair with long bangs, blue eyes, the blue forehead protector, the
    green flak jacket over the navy uniform, bandages on his right shin, blue sandals, and the white short-sleeved
    Hokage haori with red flames on the hem and 'Fourth Hokage' down the back; the Flying Thunder God kunai.
    Nine-Tails Chakra Mode: Kurama's golden chakra cloak with black seal lines, flame-like hair."""
    kcm = form == "kcm"
    if kcm:
        gold, mk = (255, 196, 60), (40, 26, 10)
        head = skin_swap(head_paint(gold, (250, 190, 60), True, "minato_kcm"), gold)

        def seals(face, px, w, h, base):
            if face == "north":
                for i in range(6):
                    a = math.pi * (0.15 + 0.7 * i / 5)
                    _put(px, w, h, int(w / 2 + math.cos(a) * w * 0.36), int(h * 0.05 + math.sin(a) * h * 0.2), mk)
                for y in range(int(h * 0.28), h):
                    _put(px, w, h, int(w * 0.3), y, mk); _put(px, w, h, int(w * 0.7), y, mk)
                for x in range(int(w * 0.3), int(w * 0.71)):
                    _put(px, w, h, x, int(h * 0.62), mk)
            if face == "south":
                for y in range(int(h * 0.1), int(h * 0.9)):
                    _put(px, w, h, w // 2, y, mk)
        base_body(m, layered(gold, [seals]), layered(gold, [region((0, 0.6, 1, 0.66), mk), region((0, 0.88, 1, 1), mk)]),
                  layered(gold, [lines((("north",), [[(0.5, 0), (0.5, 1)]]), mk), region((0, 0.86, 1, 1), mk)]), head)
        g2 = light(gold, 0.15)
        hem = region((0, 0.84, 1, 1), mk)
        m.box("body", [-4.6, 5.0, 2.1], [9.2, 19.2, 0.5], layered(g2, [hem]))
        for x0 in (-4.6, 1.7):
            m.box("body", [x0, 5.0, -2.6], [2.9, 19.2, 0.5], layered(g2, [hem]))
        minato_hair(m, (255, 210, 80))
        for s_ in (1, -1):
            m.strand([s_ * 1.9, 32.2, -0.6], [s_ * 0.25, 1, 0.05], 4.4, 2.4, M.hair_paint((255, 210, 80)), bone="hair", segs=3, thick=0.75)
        m.box("head", [-4.3, 28.6, -4.3], [8.6, 1.8, 8.6], solid((60, 40, 20)))
    else:
        head = head_paint(MIN_HAIR, (60, 110, 220), True, "minato")
        navy, vest = (40, 50, 100), (96, 120, 70)

        def flak(face, px, w, h, base):
            if face != "north":
                return
            for y in range(int(h * 0.12), int(h * 0.45)):          # the two scroll pockets
                for x in list(range(2, w // 2 - 2)) + list(range(w // 2 + 2, w - 2)):
                    _put(px, w, h, x, y, (110, 136, 82))
            for y in range(h):
                _put(px, w, h, w // 2, y, (60, 76, 44))
            for x in range(w // 2 - 2, w // 2 + 2):
                _put(px, w, h, x, 0, navy); _put(px, w, h, x, 1, navy)
        base_body(m, layered(vest, [flak]), layered(navy, [region((0, 0.86, 1, 1), SKIN), region((0, 0.0, 1, 0.3), (110, 114, 124))]),
                  layered(navy, [region((0, 0.86, 1, 1), (40, 70, 150))]), head)
        m.box("rightLeg", [-0.2, 2.0, -2.2], [4.2, 3.6, 4.4], layered((236, 236, 232), [lines((SIDES, [[(0, 0.3), (1, 0.4)], [(0, 0.7), (1, 0.8)]]), (200, 200, 196))]))
        m.box("head", [-4.3, 28.6, -4.3], [8.6, 1.8, 8.6], solid((40, 60, 140)))             # the blue forehead protector
        from chars_extra import leaf_plate
        m.box("head", [-2.4, 28.4, -4.6], [4.8, 2.2, 0.35], layered((196, 202, 212), [leaf_plate]))
        white = (246, 246, 244)
        back = layered(white, [flames_hem, glyph(HOKAGE, (30, 30, 36), cy=0.4, scale=1)])
        front = layered(white, [flames_hem])
        haori(m, back, front, sleeve_len=6.0, lining=(230, 230, 232))
        m.box("body", [-0.2, 12.6, -2.7], [0.4, 9.0, 0.2], solid((240, 140, 40)))           # the thin orange rope
        minato_hair(m)
    M.flat_blade(m, "rightArm", (6, 12.2, -1.2), (0, 0.15, -1), 2.2, 4.4, 2.4, kunai_shape(), grip=0.6)


# ==================================================================================
# BLEACH — Kenpachi Zaraki, Ulquiorra Cifer
# ==================================================================================
KEN_SKIN, ULQ_SKIN = (236, 204, 170), (244, 244, 240)
M.FACE32.update({
    "kenpachi": dict(eye="narrow", brow="none", mouth="smirk", marks=["ken_face", "ken_patch"]),
    "kenpachi_free": dict(eye="narrow", brow="none", mouth="grin", marks=["ken_face", "ken_fangs"]),
    "kenpachi_bankai": dict(eye="narrow", brow="none", mouth="grin", marks=["ken_face", "ken_fangs", "ken_demon"]),
    "ulquiorra": dict(eye="narrow", brow="flat", mouth="neutral", marks=["ulq_face"]),
    "ulquiorra_res": dict(eye="narrow", brow="flat", mouth="neutral", marks=["ulq_face", "ulq_heavy"]),
})


@mark("ken_face")
def _ken_face(F):  # hairless brow ridges, grey eyes, the long thin scar down the left side of his face
    sh = F.sr[0]
    for x in range(5, 14):
        F.both(x, 15, F.sr[1]); F.both(x, 16, sh)
    S = (180, 110, 100) if "ken_demon" not in F.marks else (90, 10, 14)
    for y in range(11, 30):
        x = 23 + (1 if y > 24 else 0)
        if 17 <= y <= 21:
            continue
        F.put(x, y, S)
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 19, (150, 156, 166))
        F.both(10, 19, (40, 40, 46))


@mark("ken_patch")
def _ken_patch(F):  # the black eyepatch over his right eye, its strap running to the side
    P = (20, 18, 22)
    for y in range(15, 23):
        for x in range(5, 15):
            if not ((x in (5, 14)) and (y in (15, 22))):
                F.put(x, y, P)
    for x in range(0, 5):
        F.put(x, 16, P)
    F.put(12, 17, (120, 110, 60))                    # a glint on its rim


@mark("ken_fangs")
def _ken_fangs(F):
    if F.expr in (None, "blink", "shout"):
        F.put(12, 26 if F.expr != "shout" else 25, (250, 250, 246)); F.put(19, 26 if F.expr != "shout" else 25, (250, 250, 246))


@mark("ken_demon")
def _ken_demon(F):  # Bankai: the eyes burn white, dark lines across the red face
    if F.open:
        for x in range(8, 13):
            for y in (18, 19, 20):
                F.both(x, y, (255, 250, 230))
    D = (110, 14, 20)
    for x, y in ((3, 22), (4, 23), (5, 24), (28, 22), (27, 23), (26, 24), (15, 12), (16, 12), (15, 13)):
        F.put(x, y, D)


@mark("ulq_face")
def _ulq_face(F):  # green cat-slit eyes, teal lines running down from them, a black upper lip
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (30, 150, 100)); F.both(x, 19, (60, 210, 140)); F.both(x, 20, (90, 230, 160))
        F.both(10, 18, (10, 30, 20)); F.both(10, 19, (10, 30, 20)); F.both(10, 20, (10, 30, 20))
    heavy = "ulq_heavy" in F.marks
    T = (40, 150, 140)
    for y in range(21, 30):
        F.both(9, y, T)
        if heavy:
            F.both(8, y, T)
    if F.mouth_free:
        for x in range(13, 19):
            F.put(x, 26, (24, 22, 28)); F.put(x, 27, (150, 120, 120))


def jagged_shape(blade=(150, 152, 160), edge=(214, 216, 224), spine=(70, 70, 78), wrap=(40, 36, 40), dia=(170, 160, 140)):
    """Kenpachi's battered zanpakuto seen flat: a plain wrapped hilt, a small guard, a long blade full of notches and
    chips along its edge."""
    hf = 0.2

    def f(xf, u):
        if u < hf:
            if abs(xf - 0.5) > 0.13:
                return None
            return dia if int(u * 70) % 3 == 0 else wrap
        if u < hf + 0.02:
            return (60, 60, 66) if abs(xf - 0.5) < 0.34 else None
        t = (u - hf - 0.02) / (1 - hf - 0.02)
        cx = 0.5 + 0.05 * t * t
        half = 0.14 * (1 if t < 0.9 else (1 - t) / 0.1)
        nick = 0.05 if (int(t * 23) % 4 == 1) else 0.0
        if xf < cx - half or xf > cx + half - nick:
            return None
        q = (xf - (cx - half)) / (2 * half)
        return spine if q < 0.2 else edge if q > 0.72 else blade
    return f


def nozarashi_shape(col=(70, 70, 80), edge=(220, 220, 226), red=False):
    """Nozarashi, the Shikai: a huge wedge-shaped cleaver blade on a long hilt, a tassel at the end."""
    hf = 0.28

    def f(xf, u):
        if u < hf:
            return ((120, 20, 24) if red else (40, 36, 40)) if abs(xf - 0.3) < 0.06 else None
        t = (u - hf) / (1 - hf)
        top = 0.3 + 0.58 * min(1, t / 0.35)
        if t > 0.96 - 0.3 * max(0, xf - 0.3):
            return None
        if xf < 0.24 or xf > top:
            return None
        return edge if xf > top - 0.08 else col
    return f


@M.smooth_hair
def kenpachi_hair(m, bells=True):
    """Stringy black hair styled into stiff spikes all round, a little bell tied to each tip."""
    col = (24, 24, 30)
    hp = M.hair_paint(col)
    shell(m, col, hairline=31.0, sideburn=True, teeth=0.6)
    tips = []
    spikes = [(0, -2.6, 0.0, 0.8, -0.5), (2.4, -1.6, 0.7, 0.7, -0.4), (-2.4, -1.6, -0.7, 0.7, -0.4), (3.6, 0.6, 1.0, 0.4, 0.1),
              (-3.6, 0.6, -1.0, 0.4, 0.1), (2.2, 2.4, 0.6, 0.4, 0.8), (-2.2, 2.4, -0.6, 0.4, 0.8), (0, 2.8, 0, 0.5, 1.0),
              (3.4, 2.6, 1.0, 0.0, 0.6), (-3.4, 2.6, -1.0, 0.0, 0.6), (1.2, 0.0, 0.3, 1.0, 0.0), (-1.2, 0.0, -0.3, 1.0, 0.0)]
    for x, z, dx, dy, dz in spikes:
        L = 5.4
        m.strand([x, 31.4, z], [dx, dy, dz], L, 2.6, hp, bone="hair", thick=0.7)
        n = SC.norm([dx, dy, dz])
        tips.append([x + n[0] * L * 1.0, 31.4 + n[1] * L * 1.0, z + n[2] * L * 1.0])
    for x in (-2.0, 0.0, 2.0):
        m.strand([x, 29.4, 4.2], [x * 0.1, -1, 0.5], 6.0, 2.6, hp, bone="hair", thick=0.7)
    if bells:
        bell = SC.swatch((236, 196, 70))
        for p in tips[:10]:
            SC.blob(m, "hair", p, [0.45, 0.45, 0.45], bell, slices=2)


ELEVEN = ["..#.......", "..#.......", "#####.####", "..#.......", "..#......."]   # 十一


@fighter("kenpachi", ["patch", "nozarashi", "bankai"])
def kenpachi(m, form):
    """Kenpachi Zaraki, captain of the 11th Division: very tall, stiff spiky black hair with bells on the tips, the black
    eyepatch over his right eye, the long scar down the left side of his face, fangs; the black shihakusho over white
    bandages, the ragged short-sleeved captain's haori with the 11 on the back, a battered, notched sword. Nozarashi:
    eyepatch off, the Shikai a giant cleaver. Bankai: his skin turns blood red, eyes white, the haori torn away."""
    bank = form == "bankai"
    skin = (196, 44, 44) if bank else KEN_SKIN
    key = {"patch": "kenpachi", "nozarashi": "kenpachi_free", "bankai": "kenpachi_bankai"}[form]
    head = skin_swap(head_paint((24, 24, 30), (150, 156, 166), True, key), skin)
    if form == "patch":
        head = head_band(head, 27.6, 28.2, (20, 18, 22))
    blk = (28, 28, 34)

    def kimono(face, px, w, h, base):
        if face != "north":
            return
        for y in range(int(h * 0.6)):
            half = int(w * 0.22 * (1 - y / (h * 0.64))) + 1
            for x in range(w // 2 - half, w // 2 + half):
                edge = abs(x - w // 2) >= half - 1
                c = (240, 240, 236) if edge else ((236, 232, 224) if (y // 2) % 2 and not bank else skin)
                _put(px, w, h, x, y, c)
    if bank:
        def muscles(face, px, w, h, base):
            if face != "north":
                return
            D = (110, 14, 20)
            for x in range(1, w - 1):
                _put(px, w, h, x, int(h * 0.34), D)
            for y in range(int(h * 0.36), int(h * 0.85)):
                _put(px, w, h, w // 2, y, D)
            for y in (int(h * 0.52), int(h * 0.68)):
                for x in range(w // 2 - 4, w // 2 + 4):
                    _put(px, w, h, x, y, D)
        torso = layered(skin, [muscles, region((0, 0.86, 1, 1), blk)])
        arm = layered(skin, [lines((SIDES, [[(0.3, 0.1), (0.4, 0.9)]]), (110, 14, 20))])
    else:
        torso = layered(blk, [kimono])
        arm = layered(blk, [region((0, 0.86, 1, 1), skin)])
    base_body(m, torso, arm, layered(blk, [region((0, 0.9, 1, 1), (236, 234, 228))]), head)
    both_legs(m, [-0.7, 1.4, -2.7], [5.1, 10.8, 5.4], layered(blk, [lines((SIDES, [[(0.3, 0), (0.26, 1)], [(0.7, 0), (0.74, 1)]]), (44, 44, 52))]))
    m.box("body", [-4.4, 11.2, -2.5], [8.8, 1.4, 5.0], solid((236, 232, 224)))
    if not bank:
        def ragged(face, px, w, h, base):
            if face not in SIDES:
                return
            for x in range(w):
                cut = int(h * 0.05 * (1 + ((x * 7) % 5) / 2))
                for y in range(h - cut, h):
                    px[x, y] = (0, 0, 0, 0)
        hao = layered((244, 244, 240), [ragged])
        back = layered((244, 244, 240), [ragged, glyph(ELEVEN, (24, 24, 30), cy=0.3, scale=2)])
        haori(m, back, hao, y0=3.0, sleeve_len=5.8)
    kenpachi_hair(m, bells=not bank)
    if form == "patch":
        M.flat_blade(m, "rightArm", (6, 12.2, -1.2), (0, 0.15, -1), 4.0, 17.0, 2.6, jagged_shape(), grip=1.0)
    else:
        M.flat_blade(m, "rightArm", (6, 12.2, -1.2), (0, 0.2, -1), 5.0, 17.0, 6.0, nozarashi_shape(red=bank), grip=1.0)


@M.smooth_hair
def ulquiorra_hair(m, long_=False):
    col = (24, 24, 30)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6, sideburn=True, teeth=0.8)
    for x, tilt in ((-2.6, -0.3), (-0.4, 0.0), (0.8, 0.1), (2.6, 0.3)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.3], 4.0 if abs(x) < 1 else 3.0, 2.0, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.4, -1.4], [s_ * 0.2, -1, 0.1], 3.6 if not long_ else 9.0, 2.2, hp, bone="hair", thick=0.6)
    if long_:
        m.box("hair", [-4.4, 9.0, 4.0], [8.8, 19.0, 1.4], gradient_hair(col, col))
    else:
        for x in (-2.0, 0.0, 2.0):
            m.strand([x, 30.0, 4.2], [x * 0.1, -1, 0.3], 3.6, 2.6, hp, bone="hair", thick=0.6)


@fighter("ulquiorra", ["espada", "murcielago", "segunda"])
def ulquiorra(m, form):
    """Ulquiorra Cifer, the 4th Espada: pale white skin, messy black hair, green slit-pupiled eyes with teal lines down
    his cheeks, a black upper lip; the broken horned helmet of his Hollow mask on the left of his head; the long-tailed
    white Arrancar coat with a high collar, black sash, white hakama. Murcielago: long black hair, a white helmet with
    two horns, a long white robe and huge black bat wings. Segunda Etapa: the white chest with its Hollow hole, black
    fur from the waist down, black arms, longer horns, the wings and a long thin tail."""
    head = skin_swap(head_paint((24, 24, 30), (60, 210, 140), True, "ulquiorra" if form == "espada" else "ulquiorra_res"), ULQ_SKIN)
    white, blk = (244, 244, 242), (24, 22, 28)
    bone_w = SC.swatch((244, 242, 236))
    if form == "espada":
        def coat(face, px, w, h, base):
            if face == "north":
                for y in range(h):
                    _put(px, w, h, w // 2, y, (200, 200, 204))
        base_body(m, layered(white, [coat]), layered(white, [region((0, 0.86, 1, 1), ULQ_SKIN)]),
                  layered(white, [region((0, 0.9, 1, 1), blk)]), head)
        both_legs(m, [-0.6, 2.0, -2.6], [4.9, 10.2, 5.2], layered(white, [lines((SIDES, [[(0.3, 0), (0.26, 1)]]), (210, 210, 214))]))
        m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.2, 5.0], solid(blk))
        m.box("body", [-4.5, 2.0, 2.0], [9.0, 10.0, 0.5], layered(white, [region((0, 0.94, 1, 1), (40, 40, 46))]))   # the long coattails
        m.box("body", [-2.6, 22.6, -2.6], [5.2, 2.6, 5.2], layered(white, [region((0, 0, 1, 1), (220, 220, 224), faces=("up",))]))  # the high collar
        SC.blob(m, "head", [-2.6, 31.2, -0.4], [2.6, 1.6, 3.6], bone_w, slices=3)                 # the broken helmet on his left
        SC.curve_tube(m, "head", [[-4.2, 31.4, -0.8], [-6.2, 32.4, -1.4], [-7.2, 34.0, -1.0]], 0.8, 0.2, [bone_w, bone_w], n=2)
        M.sheath(m, (-4.6, 12.4, -1.6), (0.05, -0.55, 1), 11, dict(saya=(40, 40, 46), saya_band=(60, 150, 110)))
        ulquiorra_hair(m)
        return
    seg = form == "segunda"
    if seg:
        def chest(face, px, w, h, base):
            if face != "north":
                return
            cx, cy, r = w // 2, int(h * 0.3), max(2, w // 7)
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                        _put(px, w, h, x, y, (10, 10, 12))
        base_body(m, layered(ULQ_SKIN, [chest, region((0, 0.7, 1, 1), blk)]), layered(blk, [region((0, 0, 1, 0.15), ULQ_SKIN)]),
                  layered(blk, [lines((SIDES, [[(x, 0), (x, 1)] for x in (0.25, 0.5, 0.75)]), (44, 42, 52))]), head)
        both_legs(m, [-0.8, 1.6, -2.8], [5.3, 10.6, 5.6], layered(blk, [lines((SIDES, [[(x, 0), (x - 0.05, 1)] for x in (0.2, 0.45, 0.7, 0.95)]), (50, 48, 60))]))
        claw = SC.swatch((40, 40, 46))
        for bone, x in (("rightLeg", 1.9), ("leftLeg", -1.9)):
            for k in (-1, 0, 1):
                SC.blade(m, bone, [x + k * 1.0, 0.4, -2.6], [k * 0.2, -0.1, -1], 1.6, 0.5, 0.4, claw)
        tail = SC.swatch((30, 28, 36))
        SC.curve_tube(m, "body", [[0, 11.0, 2.6], [0.8, 6.0, 7.0], [2.0, 2.0, 12.0], [3.6, 1.0, 17.0], [5.0, 2.0, 21.0]], 0.5, 0.15, [tail, tail], n=3)
    else:
        robe = (246, 246, 244)
        base_body(m, layered(robe, [region((0.48, 0.3, 0.52, 1), (214, 214, 218), faces=("north",))]), layered(robe, [region((0, 0.86, 1, 1), ULQ_SKIN)]),
                  layered(robe, [region((0, 0.92, 1, 1), blk)]), head)
        m.box("body", [-4.8, 0.2, -2.8], [9.6, 12.2, 5.6], layered(robe, [region((0.48, 0, 0.52, 1), (214, 214, 218), faces=("north",))]))   # the long robe to the ground
        m.box("body", [-5.2, 0.2, -3.1], [10.4, 2.4, 6.2], solid(robe))
        m.box("body", [-2.8, 22.4, -2.8], [5.6, 2.8, 5.6], solid(robe))
    # the helmet with two horns, long hair, the black bat wings
    SC.blob(m, "head", [0, 31.4, 0.2], [4.4, 1.8, 4.4], bone_w, slices=3)
    for s_ in (1, -1):
        L = 1.25 if seg else 1.0
        SC.curve_tube(m, "head", [[s_ * 3.6, 31.8, 0.0], [s_ * 5.6 * L, 33.4, -0.6], [s_ * 6.2 * L, 36.0 * (1.0 if not seg else 1.04), 0.0], [s_ * 5.4 * L, 38.0 * (1.0 if not seg else 1.06), 0.8]],
                      0.9, 0.2, [bone_w, bone_w], n=2)
    ulquiorra_hair(m, long_=True)
    def scallops(face, px, w, h, base):  # the membrane hangs in arcs between the wing's fingers
        if face not in ("north", "south"):
            return
        for x in range(w):
            u = (x % (w // 3)) / (w // 3)
            cut = int(h * 0.22 * math.sin(math.pi * u))
            for y in range(h - cut, h):
                px[x, y] = (0, 0, 0, 0)
    wing_m = layered((22, 20, 28), [lines((("north", "south"), [[(0.0, 0.0), (0.33, 1.0)], [(0.33, 0.0), (0.66, 1.0)], [(1.0, 0.0), (1.0, 1.0)]]), (50, 46, 60)), scallops])
    for s_ in (1, -1):  # the black bat wings, membrane between long fingers
        m.box("body", [s_ * 9.0 - 6.0, 10.0, 2.6], [12.0, 16.0, 0.4], wing_m, rot=[0, s_ * 18, s_ * -12], pivot=[s_ * 2.0, 22.0, 2.6])
        for k in range(3):
            SC.curve_tube(m, "body", [[s_ * 2.0, 22.0, 2.8], [s_ * (6 + k * 2.5), 25.0 - k * 2, 4.0 + k], [s_ * (10 + k * 3), 12.0 - k * 2, 4.6 + k]], 0.35, 0.15,
                          [SC.swatch((14, 12, 18)), SC.swatch((14, 12, 18))], n=2)


# ==================================================================================
# MY HERO ACADEMIA — Endeavor, Tomura Shigaraki
# ==================================================================================
END_SKIN = (238, 190, 150)
M.FACE32.update({
    "endeavor": dict(eye="narrow", brow="none", mouth="none", marks=["endeavor_face"]),
    "endeavor_prom": dict(eye="narrow", brow="none", mouth="none", marks=["endeavor_face", "endeavor_white"]),
    "shigaraki": dict(eye="narrow", brow="none", mouth="none", marks=["shiga_face", "father_hand"]),
    "shigaraki_awake": dict(eye="narrow", brow="none", mouth="smirk", marks=["shiga_face", "shiga_cracks"]),
})


@mark("endeavor_face")
def _endeavor_face(F):  # turquoise eyes in a mask of flame, a flaming beard and moustache, the scar over his left eye
    white = "endeavor_white" in F.marks
    O, Y, R = ((250, 250, 240), (200, 230, 255), (250, 210, 120)) if white else ((250, 140, 30), (255, 220, 80), (210, 50, 20))
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (30, 160, 180)); F.both(x, 19, (60, 210, 220)); F.both(x, 20, (110, 230, 236))
        F.both(10, 19, (10, 50, 60))
    for x in range(3, 15):                               # flame brows rising off the brow line
        F.both(x, 15, O)
        if x % 3 == 0:
            F.both(x, 14, O); F.both(x, 13, Y)
    for x in range(2, 30):                               # the flaming beard: tongues of fire along his jaw
        top = 24 + (1 if 11 <= x <= 20 else 0) - int(1.6 * abs(math.sin(x * 0.9)))
        for y in range(top, 32):
            d = y - top
            c = R if d == 0 else O if d < 3 else Y if (x % 4 in (1, 2)) else O
            F.put(x, y, c)
    for x in range(12, 20):                              # the moustache of flame under his nose
        F.put(x, 24, O)
    if F.expr == "shout":
        for y in range(26, 30):
            for x in range(13, 19):
                F.put(x, y, (90, 20, 20))
    S = (170, 100, 90)
    for i in range(11):
        x, y = 18 + i // 2, 13 + i
        if 17 <= y <= 21 and 18 <= x <= 25:
            continue
        F.put(x, y, S)


@mark("shiga_face")
def _shiga_face(F):  # red eyes ringed with dark, dry cracked skin round the eyes and lips, a scar over his right eye
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (150, 20, 30)); F.both(x, 19, (220, 40, 50)); F.both(x, 20, (240, 80, 80))
        F.both(10, 19, (40, 0, 6))
    for x in range(6, 14):
        F.both(x, 21, F.sr[0])
    C = (190, 120, 120)
    for x, y in ((6, 22), (7, 23), (5, 23), (25, 22), (24, 23), (26, 23), (13, 27), (18, 27), (14, 28), (17, 28)):
        F.put(x, y, C)
    for y in (13, 14, 15, 16, 22, 23):
        F.put(10, y, (200, 130, 130))
    if F.mouth_free:
        for x in range(13, 19):
            F.put(x, 27, (150, 90, 96))
        F.put(12, 26, (200, 130, 130))


@mark("shiga_cracks")
def _shiga_cracks(F):  # awakened: the skin cracking over the whole face
    C = (150, 60, 70)
    for pts in (((3, 13), (4, 14), (4, 15), (5, 16), (5, 17)), ((28, 13), (27, 14), (27, 15), (26, 16)), ((6, 24), (6, 25), (7, 26), (7, 27)),
                ((25, 24), (25, 25), (24, 26)), ((15, 12), (16, 13), (16, 14))):
        for x, y in pts:
            F.put(x, y, C)


@mark("father_hand")
def _father_hand(F):  # 'Father': a severed grey hand gripping his face, the fingers spread over it, eyes peering through
    H, D = (222, 216, 214), (110, 100, 104)
    for y in range(22, 32):                              # the palm over his mouth and chin
        for x in range(8, 24):
            F.put(x, y, D if x in (8, 23) or y == 31 else H)
    for fx in (8, 13, 18, 23):                           # four fingers spread up over the face between and beside the eyes
        x = fx if fx < 16 else fx - 1
        for y in range(12, 22):
            if 17 <= y <= 20 and (7 <= x <= 12 or 19 <= x <= 24):
                continue
            F.put(x, y, H); F.put(x + 1, y, D if y in (12,) else H)
        F.put(x, 12, D); F.put(x + 1, 12, D)
    for y in range(24, 29):                               # the thumb along his cheek
        F.put(4, y, H); F.put(5, y, H)
    F.put(4, 23, D); F.put(5, 23, D)


def hand_on(m, bone, center, d=(0, 0, -1), size=1.0, col=(216, 208, 206)):
    """One of the severed hands Shigaraki wears: a palm with four fingers gripping the body."""
    sw, sh = SC.swatch(col), SC.swatch(dark(col, 0.8))
    x, y, z = center
    SC.box_at(m, bone, [x, y, z], [1.6 * size, 1.4 * size, 0.4], sw)
    for k in range(4):
        SC.box_at(m, bone, [x - 0.6 * size + k * 0.4 * size, y + 1.3 * size, z], [0.3 * size, 1.4 * size, 0.35], sh if k % 2 else sw)
    SC.box_at(m, bone, [x + 1.0 * size, y - 0.3 * size, z], [0.9 * size, 0.35 * size, 0.35], sw)


@fighter("endeavor", ["hero", "prominence"])
def endeavor(m, form):
    """Endeavor, the No.1 Hero: a big man with spiky red hair and turquoise eyes, his face masked in Hellflame — flame
    brows, a flaming beard and moustache — the scar over his left eye; the dark navy hero suit with silver bracers,
    belt and boot tops, flames pouring from his shoulders. Prominence Burn: the flames burn white-hot."""
    prom = form == "prominence"
    head = skin_swap(head_paint((200, 40, 30), (60, 210, 220), True, "endeavor_prom" if prom else "endeavor"), END_SKIN)
    navy, silver = (34, 40, 76), (200, 204, 214)

    def suit(face, px, w, h, base):
        if face != "north":
            return
        for x in range(2, w - 2):
            _put(px, w, h, x, int(h * 0.34), (52, 60, 104))
        for y in range(int(h * 0.36), h):
            _put(px, w, h, w // 2, y, (24, 28, 56))
    base_body(m, layered(navy, [suit]), layered(navy, [region((0, 0.55, 1, 0.86), silver), region((0, 0.86, 1, 1), END_SKIN)]),
              layered(navy, [region((0, 0.6, 1, 0.68), silver)]), head)
    m.box("body", [-4.4, 11.2, -2.5], [8.8, 1.6, 5.0], layered(silver, [region((0.4, 0.1, 0.6, 0.9), (150, 154, 170), faces=("north",))]))
    m.box("body", [-2.6, 22.8, -2.6], [5.2, 1.6, 5.2], solid((24, 28, 56)))
    fl = SC.swatch((255, 250, 230) if prom else (255, 140, 30), 215)
    fl2 = SC.swatch((200, 230, 255) if prom else (255, 220, 80), 200)
    for s_ in (1, -1):  # Hellflame pouring off his shoulders
        for k in range(4):
            SC.blade(m, "body", [s_ * (4.6 + k * 0.9), 24.0, -1.4 + k * 0.9], [s_ * 0.35, 1, 0.25], 5.0 - k * 0.7, 2.2, 0.6, fl if k % 2 == 0 else fl2)
    for k in range(5):  # the flames of his beard licking up round the jaw
        a = math.pi * (0.1 + 0.8 * k / 4)
        SC.blade(m, "head", [math.cos(a) * 3.8, 24.4, -math.sin(a) * 3.8 - 0.4], [math.cos(a) * 0.3, 0.6, -math.sin(a) * 0.6], 2.0, 1.4, 0.4, fl)
    col = (200, 40, 30)
    hp = M.hair_paint(col)
    shell(m, col, hairline=31.0, sideburn=False, teeth=0.7)
    for k in range(9):
        a = math.pi * (0.1 + 0.8 * k / 8) + math.pi
        m.strand([math.cos(a) * 2.6, 31.8, -math.sin(a) * 2.6 - 0.6], [math.cos(a) * 0.4, 0.9, -math.sin(a) * 0.5 + 0.3], 3.6, 2.6, hp, bone="hair", thick=0.7)
    if prom:
        for bone, x in (("rightArm", 6.0), ("leftArm", -6.0)):
            for k in range(3):
                SC.blade(m, bone, [x + (k - 1) * 1.2, 14.0, 2.2], [0, 0.5, 1], 3.0, 1.2, 0.4, fl)


@M.smooth_hair
def shigaraki_hair(m, col):
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.4, sideburn=True, teeth=0.9)
    for x, tilt in ((-2.8, -0.4), (-1.2, -0.1), (0.6, 0.1), (2.4, 0.3)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.4], 4.2, 2.0, hp, bone="hair", thick=0.6)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.6, -1.6], [s_ * 0.3, -1, 0.0], 6.0, 2.2, hp, bone="hair", thick=0.6)
        m.strand([s_ * 3.6, 31.4, 2.4], [s_ * 0.6, -0.8, 0.6], 6.4, 2.4, hp, bone="hair", thick=0.6)
    for x in (-2.0, 0.0, 2.0):
        m.strand([x, 30.4, 4.2], [x * 0.15, -1, 0.4], 6.0, 2.6, hp, bone="hair", thick=0.6)


@fighter("shigaraki", ["league", "awakened"])
def shigaraki(m, form):
    """Tomura Shigaraki: messy pale blue-grey hair, red eyes ringed with dark, dry cracked skin and the scars on his
    lips and over his right eye; 'Father' gripping his face, more severed hands on his arms, chest and neck; a black
    V-neck long-sleeved top, black trousers, red sneakers. Awakened (Paranormal Liberation War): white hair, the cracks
    spreading, no hands, a long black coat."""
    awake = form == "awakened"
    hair = (236, 236, 240) if awake else (176, 196, 214)
    head = skin_swap(head_paint(hair, (220, 40, 50), True, "shigaraki_awake" if awake else "shigaraki"), (238, 214, 200))
    blk = (34, 34, 40)

    def vneck(face, px, w, h, base):
        if face != "north":
            return
        for y in range(int(h * 0.2)):
            half = int(w * 0.14 * (1 - y / (h * 0.22))) + 1
            for x in range(w // 2 - half, w // 2 + half):
                _put(px, w, h, x, y, (238, 214, 200))
    base_body(m, layered(blk, [vneck]), layered(blk, [region((0, 0.86, 1, 1), (238, 214, 200))]),
              layered(blk, [region((0, 0.86, 1, 1), (210, 40, 40)), region((0, 0.96, 1, 1), (240, 240, 240))]), head)
    shigaraki_hair(m, hair)
    if awake:
        coat = layered((26, 26, 30), [region((0, 0.96, 1, 1), (40, 40, 46))])
        m.box("body", [-4.6, 2.4, 2.1], [9.2, 21.8, 0.5], coat)
        for x0 in (-4.6, 2.6):
            m.box("body", [x0, 2.4, -2.6], [2.0, 21.8, 0.5], coat)
        for s_ in (1, -1):
            m.box("body", [s_ * 4.3 - 0.3, 2.4, -2.6], [0.6, 21.8, 5.2], coat)
        both_arms(m, [3.6, 12.6, -2.4], [4.8, 11.6, 4.8], coat)
        return
    hand_on(m, "rightArm", [6.0, 15.0, -2.25])                    # hands gripping his forearms
    hand_on(m, "leftArm", [-6.0, 15.0, -2.25])
    hand_on(m, "body", [-2.0, 18.4, -2.25], size=1.1)              # one on his chest
    hand_on(m, "body", [0.0, 21.4, 2.25], size=1.1)                # one at the back of his neck


# ==================================================================================
# HUNTER x HUNTER — Isaac Netero, Meruem
# ==================================================================================
NET_SKIN = (238, 204, 172)
MER_G, MER_D, MER_FACE = (110, 170, 130), (40, 94, 72), (196, 224, 204)
M.FACE32.update({
    "netero": dict(eye="narrow", brow="none", mouth="none", marks=["netero_face"]),
    "netero_serious": dict(eye="narrow", brow="none", mouth="none", marks=["netero_face", "netero_open"]),
    "meruem": dict(eye="narrow", brow="none", mouth="neutral", marks=["meruem_face"]),
    "meruem_awake": dict(eye="narrow", brow="none", mouth="neutral", marks=["meruem_face", "meruem_glow"]),
})


@mark("netero_face")
def _netero_face(F):  # an old face: forehead lines, narrow smiling eyes, a long white moustache over the mouth
    sh = F.sr[1]
    for x in range(6, 26, 1):
        if x % 4:
            F.put(x, 12, sh)
    for x in range(8, 24):
        if x % 5:
            F.put(x, 14, sh)
    W, Wd = (246, 246, 244), (214, 214, 218)
    for x in range(5, 14):                                  # long white brows drooping outward
        F.both(x, 15 + (1 if x < 8 else 0), W)
    F.both(4, 17, W); F.both(3, 18, W)
    if F.open and "netero_open" not in F.marks:
        for x in range(7, 13):
            F.both(x, 18, F.sr[2]); F.both(x, 19, F.sr[2]); F.both(x, 20, F.sr[2])
        for x in range(7, 13):
            F.both(x, 19 + (1 if x in (7, 12) else 0), (40, 30, 30))   # eyes narrowed to smiling arcs
    if F.open and "netero_open" in F.marks:
        for x in (9, 10, 11):
            F.both(x, 19, (110, 70, 40))
    for x in range(10, 22):                                 # the moustache
        F.put(x, 25, W)
        F.put(x, 26, W if 11 <= x <= 20 else Wd)
    for y in range(27, 31):
        F.both(10, y, W); F.both(11, y, Wd)
    for x in range(12, 20):                                 # the beard from the chin
        for y in range(28, 32):
            F.put(x, y, W if (x + y) % 4 else Wd)


@mark("meruem_face")
def _meruem_face(F):  # the King: a mint face under the dark green helmet, which comes to a point between his eyes
    D = MER_D
    for y in range(12, 17):
        for x in range(32):
            if abs(x - 15.5) < 16 - (y - 12) * 2.6:
                F.put(x, y, D)
    for y in range(12, 31):
        for x in (0, 1):
            F.both(x, y, D)
    for x in range(4, 14):
        F.both(x, 17, (60, 110, 86))
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 18, (110, 40, 120)); F.both(x, 19, (170, 70, 180)); F.both(x, 20, (200, 120, 210))
        F.both(10, 19, (30, 6, 30))
    for x, y in ((6, 22), (7, 23), (25, 22), (24, 23)):
        F.put(x, y, (120, 170, 140))


@mark("meruem_glow")
def _meruem_glow(F):
    if F.open:
        F.both(9, 18, (255, 220, 255))


@fighter("netero", ["chairman", "bodhisattva"])
def netero(m, form):
    """Isaac Netero, Chairman of the Hunter Association: an old, wiry man, bald with a white topknot, long drooping white
    brows, a long white moustache and beard, long earlobes; the white T-shirt with 心 ('heart') on the chest, light grey
    trousers, sandals. 100-Type Guanyin Bodhisattva: his eyes open, a ring of golden light behind his head."""
    bod = form == "bodhisattva"
    face = skin_swap(head_paint(NET_SKIN, (110, 70, 40), False, "netero_serious" if bod else "netero"), NET_SKIN)
    head = plain_head(NET_SKIN, face)
    tee, pants = (246, 246, 244), (190, 190, 196)
    KOKORO = [".#.....", "..#..#.", "...#..#", "#.....#", "#.#...#", "#..#..#", ".##.##."]
    base_body(m, layered(tee, [glyph(KOKORO, (20, 20, 24), cy=0.36, scale=2, faces=("north",))]),
              layered(NET_SKIN, [region((0, 0, 1, 0.3), tee)]), layered(pants, [region((0, 0.9, 1, 1), (70, 50, 40))]), head)
    _strip_ears(m)
    for s_ in (1, -1):  # long earlobes
        m.box("head", [s_ * 4.0 - (0.75 if s_ < 0 else 0), 24.8, -0.75], [0.75, 3.8, 1.5], solid(NET_SKIN))
    both_legs(m, [-0.6, 2.0, -2.6], [4.9, 10.2, 5.2], layered(pants, [lines((SIDES, [[(0.3, 0), (0.26, 1)]]), dark(pants, 0.86))]))
    W = SC.swatch((246, 246, 244))
    SC.blade(m, "head", [0, 24.4, -4.1], [0, -1, -0.2], 4.6, 3.2, 0.8, W, width_dir=[1, 0, 0])     # the beard
    for s_ in (1, -1):
        SC.curve_tube(m, "head", [[s_ * 1.2, 25.6, -4.3], [s_ * 2.4, 24.8, -4.5], [s_ * 2.8, 22.0, -4.4]], 0.28, 0.16, [W, W], n=2)   # moustache tips
        SC.curve_tube(m, "head", [[s_ * 3.4, 28.2, -4.3], [s_ * 4.6, 27.4, -4.4], [s_ * 5.0, 25.6, -4.2]], 0.25, 0.12, [W, W], n=2)   # drooping brows
    SC.box_at(m, "head", [0, 32.6, 2.4], [1.4, 1.2, 1.4], W)                                        # the topknot
    SC.curve_tube(m, "head", [[0, 33.2, 2.6], [0, 34.6, 3.6], [0, 34.0, 5.0]], 0.45, 0.2, [W, W], n=2)
    if bod:
        gold = SC.swatch((255, 214, 90), 200)
        for k in range(16):  # a ring of golden light behind his head
            a = 2 * math.pi * k / 16
            SC.box_at(m, "body", [math.cos(a) * 5.2, 28 + math.sin(a) * 5.2, 4.6], [1.2, 1.2, 0.4], gold)


@fighter("meruem", ["king", "awakened"])
def meruem(m, form):
    """Meruem, the Chimera Ant King: a slender green body, a mint face under a dark green helmet that comes to a point
    between his purple eyes, two long tendrils sweeping back from the crown, a segmented belly, dark joints, and a long
    segmented tail ending in a spearhead. Awakened (after the Royal Guard): his eyes glow, the tail grows larger."""
    awake = form == "awakened"
    face = skin_swap(head_paint(MER_D, (170, 70, 180), False, "meruem_awake" if awake else "meruem"), MER_FACE)
    head = plain_head(MER_D, face)

    def belly(face_, px, w, h, base):
        if face_ != "north":
            return
        for y in range(int(h * 0.4), h, max(2, h // 8)):
            for x in range(2, w - 2):
                _put(px, w, h, x, y, MER_D)
        for x in range(2, w - 2):
            _put(px, w, h, x, int(h * 0.36), (70, 120, 96))
    base_body(m, layered(MER_G, [belly]), layered(MER_G, [region((0, 0.42, 1, 0.5), MER_D), region((0, 0.9, 1, 1), MER_D)]),
              layered(MER_G, [region((0, 0.42, 1, 0.5), MER_D), region((0, 0.88, 1, 1), MER_D)]), head)
    _strip_ears(m)
    m.box("body", [-2.6, 22.4, -2.6], [5.2, 2.0, 5.2], solid(MER_D))                               # the collar of his carapace
    dk = SC.swatch(MER_D)
    for s_ in (1, -1):  # two long tendrils sweeping back from the crown
        SC.curve_tube(m, "head", [[s_ * 1.6, 32.0, -0.6], [s_ * 2.8, 33.4, 2.6], [s_ * 3.4, 32.2, 6.6], [s_ * 3.6, 29.0, 9.6]], 0.55, 0.12, [dk, dk], n=3)
    SC.blade(m, "head", [0, 31.8, -3.2], [0, 1, 0.6], 2.2, 2.0, 0.8, dk, width_dir=[0, 0, 1])     # the helmet's crest
    tl, tip = SC.swatch(MER_G), SC.swatch((170, 210, 180))
    big = 1.15 if awake else 1.0
    pts = [[0, 11.2, 2.4], [0.4, 7.0, 6.0], [1.0, 2.6, 9.6], [1.6, 1.4, 14.0], [2.0, 3.6, 18.0]]
    SC.curve_tube(m, "body", pts, 1.2 * big, 0.6, [tl, dk], n=3)
    SC.blade(m, "body", pts[-1], [0.1, 0.5, 1], 3.0 * big, 1.6, 0.6, tip, width_dir=[1, 0, 0])


# ==================================================================================
# CHAINSAW MAN — Aki Hayakawa, Reze
# ==================================================================================
M.FACE32.update({
    "aki": dict(eye="narrow", brow="flat", mouth="neutral", marks=["aki_eyes"]),
    "aki_future": dict(eye="narrow", brow="angled", mouth="neutral", marks=["aki_eyes", "future_eye"]),
    "reze": dict(eye="anime", brow="fine", mouth="smile", marks=["reze_eyes", "pink_lips"]),
    "reze_bomb": dict(eye="__none__", brow="none", mouth="none", marks=["bomb_head"]),
})


@mark("aki_eyes")
def _aki_eyes(F):
    if F.open:
        for x in (9, 10, 11):
            F.both(x, 19, (40, 60, 120)); F.both(x, 20, (60, 90, 160))


@mark("future_eye")
def _future_eye(F):  # the Future Devil living in his right eye: the iris turns a glowing violet
    if F.open:
        for x in (9, 10, 11):
            for y in (18, 19, 20):
                F.put(x, y, (170, 90, 230))
        F.put(10, 19, (250, 240, 255))
        F.put(6, 21, (170, 90, 230)); F.put(13, 21, (170, 90, 230))


@mark("reze_eyes")
def _reze_eyes(F):
    if F.open:
        for x in (9, 10, 11, 12):
            F.both(x, 18, (40, 120, 80)); F.both(x, 19, (60, 160, 100)); F.both(x, 20, (90, 190, 120))


@mark("bomb_head")
def _bomb_head(F):  # the Bomb Devil's head: rough cast iron, narrow glowing slits for eyes, a jagged mouth of teeth
    I, I2 = (70, 72, 80), (56, 58, 66)
    for y in range(32):
        for x in range(32):
            F.put(x, y, I2 if (x * 3 + y * 5) % 7 == 0 else I)
    for x in range(6, 14):
        F.both(x, 17, (255, 240, 160) if F.open else (30, 30, 34))
        F.both(x, 18, (250, 170, 60) if F.open else (30, 30, 34))
    for x in range(5, 27):
        F.put(x, 24, (20, 18, 22))
    for x in range(6, 26):
        F.put(x, 25, (250, 248, 240) if x % 2 else (20, 18, 22))
        F.put(x, 26, (20, 18, 22))
        F.put(x, 27, (250, 248, 240) if x % 2 == 0 else (20, 18, 22))
    for x in range(5, 27):
        F.put(x, 28, (20, 18, 22))


@M.smooth_hair
def aki_hair(m):
    """Black hair tied up in a small topknot at the back of his head, bangs falling to one side."""
    col = (24, 24, 30)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.8, sideburn=True, teeth=0.6)
    for x, tilt in ((-2.6, -0.2), (-0.8, -0.1), (1.2, 0.2), (2.8, 0.35)):
        m.strand([x, 31.6, -4.2], [tilt + 0.15, -1, -0.3], 3.0, 2.0, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.4, -1.2], [s_ * 0.1, -1, 0.0], 3.0, 2.0, hp, bone="hair", thick=0.6)
    SC.blob(m, "hair", [0, 32.0, 3.0], [1.3, 1.1, 1.3], SC.swatch(col), slices=3)                   # the topknot
    m.box("hair", [-0.8, 31.0, 2.6], [1.6, 0.6, 1.4], solid((60, 60, 70)))                         # its tie


@fighter("aki", ["hunter", "future"])
def aki(m, form):
    """Aki Hayakawa, Public Safety Devil Hunter: black hair in a small topknot, dark blue eyes, a white dress shirt with
    the sleeves rolled, a black tie, black trousers and shoes; his katana. Future Devil: the devil living in his right
    eye makes it glow violet."""
    fut = form == "future"
    head = head_paint((24, 24, 30), (40, 60, 120), True, "aki_future" if fut else "aki")
    shirt = (246, 246, 244)

    def tie(face, px, w, h, base):
        if face != "north":
            return
        for y in range(0, int(h * 0.72)):
            half = 1 if y < 2 else (2 if y < h * 0.6 else 1)
            for x in range(w // 2 - half, w // 2 + half):
                _put(px, w, h, x, y, (24, 24, 30))
        for y in range(h):
            if y % 5 == 4:
                _put(px, w, h, w // 2 + 3, y, (210, 210, 214))          # shirt buttons
    base_body(m, layered(shirt, [tie]), layered(shirt, [region((0, 0.55, 1, 1), SKIN), region((0, 0.5, 1, 0.56), dark(shirt, 0.86))]),
              layered((30, 30, 36), [region((0, 0.92, 1, 1), (16, 16, 20))]), head)
    m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.0, 5.0], solid((20, 20, 24)))
    aki_hair(m)
    st = dict(wrap=(30, 30, 36), diamond=(150, 150, 160), metal=(60, 60, 66), blade=(206, 210, 222), edge=(246, 248, 255),
              spine=(110, 114, 126), tsuba=(40, 40, 46), tsuba_in=(140, 140, 150), tsuba_shape="square", curve=0.05)
    nichirin(m, st, length=13.0)


@M.smooth_hair
def reze_hair(m):
    """Dark purple-black hair cut to the jaw, a full fringe, longer locks at the front."""
    col = (52, 36, 70)
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6, sideburn=True, teeth=0.8)
    for x, tilt in ((-2.8, -0.25), (-1.2, -0.1), (0.4, 0.05), (2.0, 0.2), (3.2, 0.35)):
        m.strand([x, 31.6, -4.2], [tilt, -1, -0.3], 3.0, 2.0, hp, bone="hair", thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.2, 30.6, -2.4], [s_ * 0.15, -1, -0.1], 5.4, 2.2, hp, bone="hair", thick=0.6)
        m.strand([s_ * 4.3, 30.4, 0.8], [s_ * 0.2, -1, 0.2], 5.0, 2.4, hp, bone="hair", thick=0.6)
    for x in (-2.2, 0.0, 2.2):
        m.strand([x, 30.0, 4.2], [x * 0.1, -1, 0.3], 4.8, 2.6, hp, bone="hair", thick=0.6)


@fighter("reze", ["girl", "bomb"])
def reze(m, form):
    """Reze: dark purple hair cut to the jaw, green eyes, the black choker hiding a grenade pin's ring at her throat; a
    white short-sleeved blouse, a dark pleated skirt, black shoes. Bomb Devil: her head becomes a cast-iron bomb with
    slit eyes, a jagged mouth, tail fins and a lit blue fuse; fuses wind round her arms and bundles of red dynamite
    hang round her waist."""
    bomb = form == "bomb"
    if bomb:
        face = head_paint((70, 72, 80), (255, 240, 160), False, "reze_bomb")
        head = plain_head((66, 68, 76), face)
    else:
        head = head_paint((52, 36, 70), (60, 160, 100), True, "reze")
    blouse, skirt = (246, 246, 244), (40, 44, 66)
    arm_extra = [lines((SIDES, [[(0, y), (1, y + 0.08)] for y in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85)]), (60, 110, 200))] if bomb else []
    base_body(m, layered(blouse, [region((0.47, 0, 0.53, 1), (220, 220, 224), faces=("north",))]),
              layered(SKIN, [region((0, 0, 1, 0.3), blouse)] + arm_extra), layered(SKIN, [region((0, 0.86, 1, 1), (24, 24, 28))]), head)
    if bomb:
        _strip_ears(m)
    m.box("body", [-4.5, 7.4, -2.5], [9.0, 5.2, 5.0], layered(skirt, [lines((SIDES, [[(x, 0.1), (x, 1)] for x in (0.15, 0.32, 0.5, 0.68, 0.85)]), dark(skirt, 0.7))]))
    m.box("body", [-2.3, 23.0, -2.4], [4.6, 1.0, 4.8], solid((20, 20, 24)))                          # the choker
    SC.box_at(m, "body", [0, 23.0, -2.6], [0.9, 0.9, 0.2], SC.swatch((200, 204, 214)))                # the pin's ring
    if not bomb:
        reze_hair(m)
        return
    iron = SC.swatch((70, 72, 80))
    SC.blob(m, "head", [0, 28.6, 0.8], [4.6, 5.0, 4.8], iron, slices=4)                              # the bomb casing round her head
    for k in range(4):  # tail fins at the back
        a = math.pi / 4 + k * math.pi / 2
        SC.box_at(m, "head", [math.cos(a) * 1.8, 29.6, 5.6 + abs(math.sin(a)) * 0.0], [0.3 if k % 2 else 3.0, 3.0 if k % 2 else 0.3, 2.4], iron)
    fuse = SC.swatch((60, 110, 200))
    SC.curve_tube(m, "head", [[0, 33.4, 0.4], [0.8, 35.4, 0.8], [1.8, 36.6, 0.2]], 0.3, 0.25, [fuse, fuse], n=2)
    SC.blob(m, "head", [1.9, 37.0, 0.1], [0.5, 0.5, 0.5], SC.swatch((255, 220, 120), 230), slices=2)
    dyn, cap = SC.swatch((200, 40, 40)), SC.swatch((240, 230, 210))
    for k in range(7):  # dynamite bundles round her waist
        a = math.pi * (0.1 + 0.8 * k / 6)
        x, z = math.cos(a) * 4.6, -math.sin(a) * 2.8
        SC.box_at(m, "body", [x, 9.6, z], [0.8, 3.0, 0.8], dyn)
        SC.box_at(m, "body", [x, 11.2, z], [0.6, 0.4, 0.6], cap)
