"""Weapon sprites, v2 (the original fighters' weapons).

Every weapon is a painted picture on flat sheets at 4x the texture resolution, like a pixel-art item sprite: the
"hires" cube attribute gives the sheet its own enlarged texture area (see models.export). Compared with the v1 helpers
in models.py (flat_blade / katana_shape, still used by chars_new22), v2:
  - paints the back of a sheet MIRRORED, so a curved blade's edge stays on the same physical side seen from either side;
  - orients a sheet any way (sprite_sheet): the picture's x axis along `wdir`, its bottom->top along `d`;
  - holds a weapon THROUGH the fist (the grip runs through the middle of the hand, the guard just in front of it);
  - adds the guard seen face-on (a tsuba sheet across the blade), so a sword pointing at the viewer still reads;
  - draws real katana anatomy: kashira, wrapped tsuka with rayskin diamonds, fuchi, tsuba, habaki, a blade curving
    toward its spine with mune, shinogi, hamon, edge and a kissaki; and scabbards, chains, saws, hammers, cards...
Pictures are shape functions f(xf, u) -> (r, g, b) | (r, g, b, a) | None, with xf 0..1 across the sheet (0 on the
+wdir side) and u 0..1 from the sheet's start to its far end. Opaque colours get a dark ink outline.
"""
import math
import random

import models as M

INK = (26, 24, 30)


# ------------------------------------------------------------------ vectors
def _norm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / l for x in v]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _add(a, b, k=1.0):
    return [a[i] + b[i] * k for i in range(3)]


def _frame(d, up):
    """Unit axis d, `up` made perpendicular to it, and the side vector."""
    d = _norm(d)
    dot = sum(up[i] * d[i] for i in range(3))
    up = _norm([up[i] - d[i] * dot for i in range(3)])
    return d, up, _norm(_cross(d, up))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def dk(c, f=0.75):
    return tuple(int(x * f) for x in c[:3])


def lt(c, f=0.35):
    return tuple(int(x + (255 - x) * f) for x in c[:3])


# ------------------------------------------------------------------ sheets
def sprite(shape):
    def p(face, img):
        w, h = img.size
        if w < 2 or h < 2 or face in ("up", "down"):
            return
        px = img.load()
        mirror = face in ("south", "west")
        fn = getattr(shape, "back", None) if mirror else None             # a different picture on the back (cards)
        fn = fn or shape
        grid = [[fn((((w - 1 - x) if mirror else x) + 0.5) / w, 1 - (y + 0.5) / h) for x in range(w)] for y in range(h)]
        for y in range(h):
            for x in range(w):
                c = grid[y][x]
                if c is None:
                    continue
                if len(c) == 4:  # explicit alpha (glow, petals, energy): no ink outline
                    px[x, y] = tuple(int(v) for v in c)
                    continue
                edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or grid[y + dy][x + dx] is None
                           or len(grid[y + dy][x + dx]) == 4 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                px[x, y] = (INK if edge else tuple(int(v) for v in c)) + (255,)
    return p


def sprite_sheet(m, bone, start, d, wdir, length, width, shape, res=4):
    """One flat sheet from `start` running `length` along `d`, the picture's x axis spanning `width` along `wdir`."""
    import sculpt as SC
    d = _norm(d)
    c = [start[i] + d[i] * length / 2 for i in range(3)]
    SC.obox(m, bone, c, [width, length, 0], sprite(shape), d, 0, wdir)
    m.cubes[-1]["hires"] = res


def held(m, bone, hand, d, up, behind, length, width, shape, grip=1.2, cross=True, res=4, thick=None):
    """A weapon held in a fist centred on `hand`: the reference point (guard) sits `grip` in front of the fist centre
    along d, the picture starts `behind` units before it and runs `length`. Main sheet in the d-up plane (xf=0 on the
    +up side); `cross` adds the same picture on the perpendicular sheet; `thick=(w, shape)` instead adds a narrow
    perpendicular sheet (the weapon's thickness) so a broad blade still shows edge-on."""
    d, up, side = _frame(d, up)
    g = _add(hand, d, grip)
    start = _add(g, d, -behind)
    sprite_sheet(m, bone, start, d, up, length, width, shape, res)
    if cross:
        sprite_sheet(m, bone, start, d, side, length, width, shape, res)
    elif thick:
        sprite_sheet(m, bone, start, d, side, length, thick[0], thick[1], res)
    return g, d, up, side


def disc(m, bone, centre, d, up, size, shape, res=4):
    """A face-on sheet across the axis d (a tsuba seen from the front), `size` across."""
    d, up, side = _frame(d, up)
    sprite_sheet(m, bone, _add(centre, up, -size / 2), up, side, size, size, shape, res)


# ------------------------------------------------------------------ tsuba (sword guard), seen face-on
def tsuba_face(style, metal, hi=None, accent=None):
    """The guard seen along the blade: xf/u across it, centre (0.5, 0.5)."""
    hi = hi or lt(metal, 0.35)
    rim = dk(metal, 0.7)

    def f(xf, u):
        dx, dy = xf - 0.5, u - 0.5
        r = math.hypot(dx, dy)
        a = math.atan2(dy, dx)
        if abs(dx) < 0.05 and abs(dy) < 0.11:
            return INK                                                   # the hole the blade passes through
        if style == "round":
            if r > 0.48:
                return None
            if 0.2 < r < 0.3 and abs(dy) < 0.08:
                return None                                              # the two hitsu-ana holes
            return hi if r > 0.43 or (dx < -0.1 and dy > 0.1 and r > 0.36) else metal
        if style == "wheel":                                             # Tanjiro: a black round guard with six spokes
            if r > 0.48:
                return None
            if 0.17 < r < 0.38:
                k = (a / (2 * math.pi) * 6) % 1.0
                if 0.2 < k < 0.8:
                    return None
            return hi if r > 0.43 else metal
        if style == "flame":                                             # Rengoku: a ring of flames
            k = (a / (2 * math.pi) * 9) % 1.0
            tongue = 0.3 + 0.18 * (1 - abs(k - 0.5) * 2) ** 1.6
            if r > tongue:
                return None
            if r < 0.15:
                return dk(metal, 0.55)
            t = (r - 0.15) / max(0.01, tongue - 0.15)
            return mix(accent or (150, 20, 16), metal, t * 1.4) if t < 0.7 else mix(metal, hi, (t - 0.7) / 0.3)
        if style == "manji":                                             # Tensa Zangetsu: a manji
            if r < 0.15:
                return metal
            for k in range(4):
                c, s = math.cos(k * math.pi / 2), math.sin(k * math.pi / 2)
                x, y = dx * c + dy * s, -dx * s + dy * c                 # rotate the arm onto +x
                if 0 <= x <= 0.44 and abs(y) < 0.08:
                    return hi if y > 0.04 else metal
                if 0.32 <= x <= 0.44 and 0 <= y <= 0.38:
                    return metal
            return None
        if style == "cross":                                             # Kitetsu: four lobes
            lobe = 0.32 + 0.14 * abs(math.cos(2 * a)) ** 0.6
            if r > lobe:
                return None
            if 0.24 < r < 0.32 and abs(math.cos(2 * a)) > 0.85:
                return None
            return hi if r > lobe - 0.05 else metal
        if style == "trio":                                              # Enma: three rings
            for k in range(3):
                cx, cy = 0.2 * math.cos(k * 2.094 + 1.571), 0.2 * math.sin(k * 2.094 + 1.571)
                rr = math.hypot(dx - cx, dy - cy)
                if rr < 0.24:
                    return None if rr < 0.1 else (hi if rr > 0.2 else metal)
            return metal if r < 0.2 else None
        if style == "square":                                            # Senbonzakura: a rounded square
            q = max(abs(dx), abs(dy))
            if q > 0.44 or (abs(dx) > 0.34 and abs(dy) > 0.34 and math.hypot(abs(dx) - 0.34, abs(dy) - 0.34) > 0.1):
                return None
            return hi if q > 0.39 else metal
        if style == "oval":                                              # Kyoka Suigetsu
            e = (dx / 0.48) ** 2 + (dy / 0.38) ** 2
            if e > 1:
                return None
            if 0.45 < e < 0.62 and abs(dy) < 0.1:
                return None
            return hi if e > 0.8 else metal
        if style == "fullbring":                                         # Fullbring: a long angular black crossguard
            if abs(dy) < 0.12 and abs(dx) < 0.48:
                return hi if dy > 0.06 else metal
            return metal if r < 0.2 else None
        return metal if r < 0.45 else None
    return f


TSUBA_R = {"round": 1.15, "wheel": 1.15, "flame": 1.3, "manji": 1.3, "cross": 1.2, "trio": 1.15, "square": 1.1,
           "oval": 1.25, "fullbring": 1.6, "none": 0.0}


# ------------------------------------------------------------------ katana, seen from the side
GLYPHS = [  # 悪 鬼 滅 殺, as tiny 5x7 pictures (Rengoku's engraving)
    ["#####", "#.#.#", "#####", "..#..", "#####", "#.#.#", "#.#.#"],
    ["..#..", "#####", "#.#.#", "#####", ".#.#.", "#..##", "#...#"],
    ["#.#.#", ".####", "#.#.#", ".###.", "#.#.#", ".#.##", "#.#.#"],
    ["#.##.", ".###.", "#.#.#", "..###", ".#.#.", "#..#.", ".#..#"],
]


def katana_shape(st, hilt, blade, W):
    """A katana seen flat. st: wrap, diamond, metal, blade, edge, (hamon, spine, habaki, tsuba, kind, kanji, straight,
    petals). `hilt`/`blade` in model units (u runs pommel -> tip), W = the picture's width in units."""
    T = hilt + blade
    wrap, dia, metal = st["wrap"], st["diamond"], st["metal"]
    bcol, ecol = st["blade"], st["edge"]
    spine = st.get("spine", dk(bcol, 0.62))
    hamon = st.get("hamon")
    habaki = st.get("habaki", st.get("habaki_col", (214, 176, 80)))
    style = st.get("tsuba", "round")
    kind = st.get("kind", "steel")
    hw = 0.36 / W                                   # half the grip's width
    bw = st.get("bw", 1.1) / W                     # blade width
    tr = TSUBA_R.get(style, 1.1) / W                # half the guard's width (seen edge-on)
    u_kas, u_fuchi, u_g0 = 0.4 / T, (hilt - 0.35) / T, hilt / T
    u_g1 = (hilt + (0.3 if style != "none" else 0.0)) / T
    u_hb = u_g1 + 0.5 / T
    curve = 0.0 if st.get("straight") else 0.32 / W
    tip_t = 1 - min(0.3, 1.3 / blade)
    rng = random.Random(7)
    petals = []
    if st.get("petals") is not None:                # Senbonzakura: the blade scatters into cherry petals
        t0 = st["petals"]
        for _ in range(int(120 * (1 - t0) + 20)):
            t = t0 + (1 - t0) * rng.random() ** 0.8 * 1.0
            spread = 0.08 + 0.42 * (t - t0) / max(0.05, 1 - t0)
            petals.append((0.5 + rng.gauss(0, spread * 0.45), u_hb + (1 - u_hb) * t, rng.random() * math.pi))

    def f(xf, u):
        dx = xf - 0.5
        if u < u_kas:                                                     # kashira: the pommel cap
            if abs(dx) > hw + 0.05 / W or (u < 0.12 / T and abs(dx) > hw - 0.05 / W):
                return None
            return lt(metal, 0.3) if dx < -hw * 0.3 else metal
        if u < u_fuchi:                                                   # tsuka: the silk wrap over rayskin
            if abs(dx) > hw:
                return None
            k = (u - u_kas) / (u_fuchi - u_kas) * max(3, round((u_fuchi - u_kas) * T / 0.62))
            fk = k % 1.0
            dd = abs(dx) / hw + abs(fk - 0.5) * 2
            if dd < 0.62:
                return dia                                                # a rayskin diamond
            if dd < 0.78:
                return dk(wrap, 0.7)
            return lt(wrap, 0.18) if (dx < 0) == (fk < 0.5) else wrap     # the crossing silk, lit on one side
        if u < u_g0:                                                      # fuchi collar
            return metal if abs(dx) <= hw + 0.04 / W else None
        if u < u_g1:                                                      # the tsuba, edge-on
            if abs(dx) > tr:
                return None
            if style == "flame":
                return mix((200, 40, 20), (255, 200, 60), abs(dx) / tr)
            return lt(metal, 0.3) if u > (u_g0 + u_g1) / 2 else metal
        if style == "flame" and u < u_g1 + 0.55 / T:                     # Rengoku's flame tongues lick up the blade
            k = (abs(dx) / tr * 3) % 1.0
            reach = u_g1 + 0.55 / T * (1 - abs(k - 0.5) * 2) * (1 - abs(dx) / tr * 0.5)
            if abs(dx) < tr * 0.95 and u < reach and abs(dx) > bw * 0.45:
                return mix((255, 120, 30), (255, 220, 90), (u - u_g1) / (0.55 / T))
        t = (u - u_hb) / (1 - u_hb)
        cx = 0.5 - curve * max(0.0, t) ** 2                               # the blade curves toward its spine (xf 0)
        w = bw * (1 - 0.14 * max(0.0, t))
        lo = cx - w / 2
        if u < u_hb:                                                      # habaki
            return habaki if lo - 0.05 / W <= xf <= lo + w + 0.05 / W else None
        if petals and t > st["petals"] - 0.02:
            for px_, pu, ang in petals:
                ex, eu = (xf - px_) * W, (u - pu) * T
                c, s = math.cos(ang), math.sin(ang)
                a_, b_ = ex * c + eu * s, -ex * s + eu * c
                if (a_ / 0.26) ** 2 + (b_ / 0.15) ** 2 < 1:
                    return (255, 214, 232) if a_ < -0.08 else (244, 140, 186)
            if t > st["petals"] + 0.04:
                return None
        hi_ = lo + w
        if t > tip_t:                                                     # kissaki: the edge sweeps up to the spine
            s_ = (t - tip_t) / (1 - tip_t)
            hi_ = lo + w * math.sqrt(max(0.0, 1 - s_ * s_))
        if not (lo <= xf <= hi_):
            return None
        q = (xf - lo) / w
        if q < 0.16:
            return spine
        if hi_ - xf < 0.1 / W:
            return ecol                                                   # the cutting edge
        if t > tip_t and abs(t - tip_t) * blade < 0.08:
            return lt(bcol, 0.35)                                         # yokote line
        if st.get("kanji") and 0.05 < t < 0.05 + 4 * 0.9 / blade and 0.24 < q < 0.7:
            gi = int((t - 0.05) * blade / 0.9)
            gy = ((t - 0.05) * blade / 0.9) % 1.0
            gx = (q - 0.24) / 0.46
            g = GLYPHS[min(3, gi)]
            row = g[min(6, int((1 - gy) * 8 - 0.5))] if 0.06 < gy < 0.94 else "....."
            if row[min(4, int(gx * 5))] == "#":
                return st["kanji"]
        if kind == "flame":                                               # Rengoku: flame-shaped hamon
            wave = 0.5 + 0.22 * abs(((t * blade / 1.3) % 1.0) - 0.5) * 2
            if q > wave:
                return mix((255, 128, 32), (255, 214, 100), (q - wave) / (1 - wave))
            return bcol if q > 0.3 else dk(bcol, 0.8)
        if abs(q - 0.38) < 0.04:
            return lt(bcol, 0.22) if kind != "black" else (70, 72, 84)    # shinogi ridge line
        if hamon:
            hb = 0.66 + 0.05 * math.sin(t * blade * 2.6)
            if q > hb:
                return hamon
        return bcol
    return f


def katana(m, bone, hand, d, blade, st, up=(0, 1, 0), grip=1.2, hilt=4.6, W=2.8, face=True):
    """A held katana: grip through the fist, the guard `grip` in front of the fist centre."""
    shape = katana_shape(st, hilt, blade, W)
    g, d_, up_, side = held(m, bone, hand, d, up, hilt, hilt + blade, W, shape, grip=grip, cross=True)
    style = st.get("tsuba", "round")
    if face and style != "none":
        disc(m, bone, _add(g, d_, 0.15), d_, up_, TSUBA_R[style] * 2, tsuba_face(style, st["metal"], st.get("tsuba_hi"), st.get("tsuba_accent")))
    return g, d_


def katana_v1_call(m, bone, hand, direction, length, st, grip=1.2):
    """Drop-in for models.katana2(m, bone, hand, direction, length, st): the old callers give the hand at the bottom of
    the arm (y 12.2); the grip now runs through the middle of the fist."""
    hx, hy, hz = hand
    if bone in ("rightArm", "leftArm") and abs(hy - 12.2) < 0.01:
        hand = (hx, 13.1, -0.4)
        grip = 2.0 + (grip - 1.2)
    return katana(m, bone, hand, direction, length + 0.8, st, grip=grip)


# ------------------------------------------------------------------ scabbards
def saya_shape(st, length, W, hilt=0.0, hst=None):
    """A scabbard seen flat (u from the mouth, or the pommel when a sheathed hilt shows, to the end): koiguchi collar,
    the lacquered body with its cord (sageo) at the kurikata knob, a kojiri cap."""
    T = length + hilt
    col, band = st.get("saya", (30, 30, 34)), st.get("saya_band", (200, 200, 200))
    cord = st.get("sageo", band)
    hw = 0.42 / W
    inner = katana_shape(dict(hst, tsuba="none", blade=(0, 0, 0), edge=(0, 0, 0)), hilt, 2.0, W) if hilt else None

    def f(xf, u):
        dx = xf - 0.5
        L = u * T
        if L < hilt:
            return inner(xf, L / (hilt + 2.0))
        s = (L - hilt) / length
        wd = hw * (1 - 0.15 * s)
        if s > 0.97:
            wd *= 0.8
        if abs(dx) > wd:
            if 0.08 < s < 0.16 and abs(dx) < wd + 0.12 / W and dx < 0:     # the kurikata knob
                return dk(col, 0.8)
            return None
        if s < 0.04 or s > 0.94:
            return band if dx > -wd * 0.4 else lt(band, 0.3)
        if 0.1 < s < 0.2 and int(s * length * 4) % 2 == 0:
            return cord                                                     # the sageo cord wound round it
        if -wd * 0.55 < dx < -wd * 0.25:
            return lt(col, 0.28)                                            # lacquer gloss
        return col
    return f


def saya(m, bone, top, d, length, st, up=(0, 1, 0), W=1.4, hilt=0.0, hst=None):
    """A scabbard (two crossed sheets) from `top` along d; with `hilt`, a sheathed sword's hilt shows before it."""
    d, up, side = _frame(d, up)
    start = _add(top, d, -hilt)
    shape = saya_shape(st, length, W if not hilt else 1.6, hilt, hst)
    sprite_sheet(m, bone, start, d, up, length + hilt, W if not hilt else 1.6, shape)
    sprite_sheet(m, bone, start, d, side, length + hilt, W if not hilt else 1.6, shape)


# ------------------------------------------------------------------ Zangetsu (Shikai / True Bankai)
def zangetsu_shape(blade, edge, spine, core=None, grip=(236, 236, 236), hilt=3.6, L=17.0, W=3.8):
    """The great guardless cleaver: a cloth-wrapped grip running into the spine (xf 0 = spine on top), the blade
    widening below it, the long edge, and the tip cut on a slant (the edge side longest)."""
    T = hilt + L
    gw = 0.7 / W

    def f(xf, u):
        Lu = u * T
        if Lu < hilt:
            if not (0.03 <= xf <= 0.03 + gw):
                return None
            k = (Lu / 0.5) % 1.0
            band = abs(k - 0.5 - (xf - 0.03) / gw * 0.3) < 0.18
            return dk(grip, 0.66) if band else (lt(grip, 0.2) if xf < 0.03 + gw * 0.4 else grip)
        s = (Lu - hilt) / L
        bottom = 0.98 if s > 0.012 else 0.03 + gw                           # the blade's square heel
        cut = 0.88 + 0.12 * xf                                              # slanted tip
        if s > cut or xf < 0.02 or xf > bottom:
            return None
        if xf < 0.12:
            return spine
        if xf > bottom - 0.12:
            return edge
        if core and 0.3 < xf < 0.7 and s < cut - 0.04:
            return core
        if 0.16 < xf < 0.2:
            return lt(blade, 0.25)
        return blade
    return f


# ------------------------------------------------------------------ chains (Kurapika, Tensa Zangetsu)
def chain_shape(col, length, link=0.7, phase=0, tip=None, tip_len=0.0):
    """A chain seen flat: oval links facing this sheet alternate with links seen edge-on (thin bars); the crossed
    sheet uses the other phase, like a real chain. `tip(xf, s)` paints the weapon at the end (s 0..1 over tip_len)."""
    T = length + tip_len

    def f(xf, u):
        L = u * T
        if L > length:
            return tip(xf, (L - length) / max(0.01, tip_len)) if tip else None
        k = L / link
        i, fk = int(k), k % 1.0
        dx = (xf - 0.5)
        if (i + phase) % 2 == 0:                                            # a link facing us: a ring
            e = (dx / 0.42) ** 2 + ((fk - 0.5) / 0.62) ** 2
            if 0.3 < e < 1:
                return lt(col, 0.35) if dx < 0 else col
            return None
        if abs(dx) < 0.1:                                                   # a link seen edge-on
            return dk(col, 0.8)
        return None
    return f


def chain(m, bone, start, d, length, col, up=(0, 1, 0), width=0.6, tip=None, tip_len=0.0, tip_w=None):
    d, up, side = _frame(d, up)
    W = width if not tip else max(width, tip_w or width)
    k = width / W
    for ph, wd in ((0, up), (1, side)):
        base = chain_shape(col, length, phase=ph, tip=tip, tip_len=tip_len)
        sh = (lambda b: (lambda xf, u: b(0.5 + (xf - 0.5) / k, u) if (u * (length + tip_len) <= length and abs(xf - 0.5) < k / 2)
                         else (b(xf, u) if u * (length + tip_len) > length else None)))(base)
        sprite_sheet(m, bone, start, d, wd, length + tip_len, W, sh)


# ------------------------------------------------------------------ broad weapons: a painted picture on a solid core
def _runs(shape, u, n=40):
    """The opaque spans of the picture across one row u: [(xf0, xf1), ...]."""
    out, a = [], None
    for k in range(n + 1):
        on = False
        if k < n:
            c = shape((k + 0.5) / n, u)
            on = c is not None and (len(c) == 3 or c[3] > 200)
        if on and a is None:
            a = k / n
        if not on and a is not None:
            out.append((a, k / n))
            a = None
    return out


def extruded(m, bone, start, d, up, length, width, shape, side_col, t=0.25, step=0.5, res=4, core_col=None):
    """A picture with real thickness, like an extruded item sprite: the picture on both faces of a solid core built
    from one plain box per `step` along d, each as wide as the picture's opaque span at that row (so it follows the
    silhouette). `side_col` may be a function u -> colour for the core."""
    import sculpt as SC
    d, up, side = _frame(d, up)
    steps = max(1, int(round(length / step)))
    sl = length / steps
    cache = {}
    for i in range(steps):
        u = (i + 0.5) / steps
        col = side_col(u) if callable(side_col) else side_col
        if col not in cache:
            cache[col] = SC.swatch(col)
        for a, b in _runs(shape, u):
            wspan = math.floor(((b - a) * width - 0.12) * 4) / 4
            if wspan < 0.25:
                continue
            mid = (a + b) / 2
            c = _add(_add(start, d, (i + 0.5) * sl), up, (0.5 - mid) * width)
            SC.obox(m, bone, c, [wspan, sl + 0.02, t], cache[col], d, 0, up)
    off = t / 2 + 0.02
    for k in (1, -1):
        sprite_sheet(m, bone, _add(start, side, k * off), d, up, length, width, shape, res)


def broad(m, bone, hand, d, up, behind, length, width, shape, side_col, grip=1.2, shift=0.0, t=0.25, res=4):
    """A held broad weapon (cleaver, hammer, scythe, fan): `shift` moves the picture along `up` so its grip, not its
    middle, runs through the fist."""
    d, up, side = _frame(d, up)
    g = _add(hand, d, grip)
    start = _add(_add(g, d, -behind), up, shift)
    extruded(m, bone, start, d, up, length, width, shape, side_col, t=t, res=res)
    return g, d, up, side


# ------------------------------------------------------------------ Denji's chainsaws
def chainsaw_shape(bar, chain, L, W, dark_=False):
    """A chainsaw bar seen flat (u from the root to the nose): the steel bar with its riveted root and a groove, the
    chain running round both edges with hooked teeth pointing forward, the rounded nose."""
    tooth = 0.62
    bw = 0.5 - 0.26 / W                                  # the bar's half width (in xf) inside the chain

    def f(xf, u):
        dx = xf - 0.5
        Lu = u * L
        nose = L - W * 0.5
        if Lu > nose:                                    # the rounded nose
            r = math.hypot(dx * W, Lu - nose) / (W * 0.5)
            if r > 1:
                return None
            if r > 0.72:
                k = (math.atan2(Lu - nose, dx * W) * 5) % 1.0
                return chain if k < 0.6 else (lt(chain, 0.3) if r < 0.9 else None)
            return lt(bar, 0.2) if r < 0.3 else bar
        if abs(dx) > bw:                                 # the chain: links with a tooth hooked forward on each
            k = (Lu / tooth) % 1.0
            out = (abs(dx) - bw) / (0.5 - bw)
            if out > 0.55 and k > out * 0.85:
                return None
            return lt(chain, 0.35) if k < 0.25 else chain
        if Lu < 1.0:                                     # the root: a darker clamp with rivets
            if abs(dx) < bw * 0.8 and abs(Lu - 0.5) < 0.18 and abs(abs(dx) - bw * 0.45) < 0.1:
                return lt(bar, 0.5)
            return dk(bar, 0.6)
        if abs(dx) < 0.05:
            return dk(bar, 0.72)                         # the groove the chain runs in
        if dx < -bw * 0.55:
            return lt(bar, 0.28)                         # the lit upper bevel
        return bar if not dark_ else dk(bar, 0.95)
    return f


# ------------------------------------------------------------------ Gon's fishing rod
def rod_shape(L, W):
    """Gon's fishing rod (u from the butt to the tip): a cork grip, the silver reel on its seat, a long tapering rod
    with wrapped line guides, and the line running along it."""
    rod, grip, reel = (88, 66, 44), (196, 160, 110), (196, 200, 210)

    def f(xf, u):
        dx = (xf - 0.5) * W
        Lu = u * L
        if Lu < 0.4:
            return dk(rod, 0.8) if abs(dx) < 0.28 else None                   # the butt cap
        if Lu < 3.2:
            if abs(dx) > 0.26:
                return None
            return lt(grip, 0.2) if dx < -0.08 else (dk(grip, 0.82) if int(Lu * 5) % 3 == 0 else grip)
        if Lu < 4.4:                                                          # the reel seat and the reel below it
            if abs(dx) < 0.2:
                return (150, 154, 164)
            if 0.2 <= dx < 1.25 and abs(Lu - 3.8) < 0.55:
                r = math.hypot(dx - 0.8, Lu - 3.8)
                if r < 0.5:
                    return dk(reel, 0.7) if r < 0.18 else (lt(reel, 0.3) if dx < 0.7 else reel)
                if dx < 0.4:
                    return (150, 154, 164)
            return None
        t = (Lu - 4.4) / (L - 4.4)
        half = 0.17 * (1 - t) + 0.05
        if abs(dx) <= half:
            return lt(rod, 0.25) if dx < 0 else rod
        if int((Lu - 4.4) / 2.6) != int((Lu - 4.4 - 0.25) / 2.6) and abs(dx) < half + 0.14:
            return (210, 210, 216)                                            # a line guide
        if abs(dx - (half + 0.18)) < 0.04 and t < 0.98:
            return (236, 236, 240)                                            # the line
        return None
    return f


# ------------------------------------------------------------------ Kurapika's chain weapons
def tip_cross(col):                                                           # Holy Chain (thumb)
    def f(xf, s):
        dx = abs(xf - 0.5)
        if (dx < 0.09 and 0.0 < s < 1.0) or (dx < 0.32 and 0.55 < s < 0.72):
            return lt(col, 0.3) if xf < 0.5 else col
        return None
    return f


def tip_syringe(col):                                                         # Steal Chain (index): a syringe
    def f(xf, s):
        dx = abs(xf - 0.5)
        if s < 0.12:
            return col if dx < 0.3 else None                                  # plunger flange
        if s < 0.72:
            if dx < 0.2:
                return (200, 230, 240) if dx < 0.12 and 0.2 < s < 0.62 else col
            return None
        return col if dx < 0.06 else None                                     # the needle
    return f


def tip_hook(col):                                                            # Chain Jail (middle): a hooked claw
    def f(xf, s):
        dx = xf - 0.5
        if s < 0.5:
            return col if abs(dx) < 0.1 else None
        a = math.atan2(s - 0.5, dx)
        r = math.hypot(dx, s - 0.5)
        if 0.2 < r < 0.36 and a < 2.4 and (dx > -0.1 or s > 0.6):
            return lt(col, 0.3) if r < 0.27 else col
        return None
    return f


def tip_ball(col):                                                            # Dowsing Chain (ring): the pendulum
    def f(xf, s):
        dx = xf - 0.5
        half = 0.36 * math.sin(math.pi * min(1.0, s * 1.15)) if s < 0.87 else 0.0
        if abs(dx) < half or (s >= 0.87 and abs(dx) < 0.05):
            return lt(col, 0.45) if dx < -half * 0.3 else col
        return None
    return f


def tip_blade(col):                                                           # Judgment Chain (little): the spike
    def f(xf, s):
        dx = xf - 0.5
        if s < 0.12:
            return col if abs(dx) < 0.3 else None
        half = 0.2 * (1 - (s - 0.12) / 0.88)
        if abs(dx) < half:
            return lt(col, 0.45) if dx < 0 else col
        return None
    return f


# ------------------------------------------------------------------ Power's blood weapons
BLOOD = (176, 18, 30)


def _blood(xf, u, base=BLOOD):
    """Glossy blood: a darker core, a bright wet highlight streak."""
    if xf < 0.22:
        return lt(base, 0.35)
    return base if xf < 0.7 else dk(base, 0.72)


def blood_hammer_shape(L, W, head=4.2):
    """Power's blood hammer (u from the butt): a long haft, a heavy square head with drips running off it."""
    hd = head / L

    def f(xf, u):
        dx = (xf - 0.5) * W
        Lu = u * L
        if Lu < L - head:
            if abs(dx) > 0.36 + (0.12 if Lu < 0.6 else 0.0):
                return None
            return lt(BLOOD, 0.3) if dx < -0.1 else dk(BLOOD, 0.8)
        s = (Lu - (L - head)) / head
        if abs(dx) > W / 2 - 0.05 or (abs(dx) > W / 2 - 0.5 and (s < 0.06 or s > 0.94)):
            return None
        if abs(s - 0.5) < 0.04:
            return dk(BLOOD, 0.6)
        return _blood(0.5 + dx / W * 0.9 + 0.2 * (s - 0.5), u)
    _ = hd
    return f


def blood_scythe_shape(L, W):
    """Power's blood scythe (u from the butt): the long snath and, at its top, a great crescent blade sweeping out to
    the +xf side and hooking back down toward the hands to a point."""
    R = W * 0.78

    def f(xf, u):
        y = (xf - 0.5) * W          # across: the blade sweeps toward +y (xf 1 side)
        Lu = u * L
        if abs(y) < 0.36 and Lu < L - 0.2:
            return lt(BLOOD, 0.3) if y < -0.1 else dk(BLOOD, 0.8)
        if y < 0.2:
            return None
        cz = L - R                                       # the crescent: inside the outer circle, outside the inner one
        o = math.hypot(y - 0.15 * R, Lu - cz)
        i = math.hypot(y - 0.05 * R, Lu - (cz - 0.38 * R))
        if o < R and i > R * 0.92 and Lu > cz - R * 0.75:
            k = (R - o) / (R * 0.35)
            return (255, 150, 160) if i < R * 0.99 else (lt(BLOOD, 0.25) if k < 0.3 else BLOOD)
        return None
    return f


# ------------------------------------------------------------------ Hisoka's playing cards
SUIT = {
    "spade": ["...#...", "..###..", ".#####.", "#######", "#######", ".#.#.#.", "..###.."],
    "heart": [".##.##.", "#######", "#######", ".#####.", "..###..", "...#...", "......."],
    "diamond": ["...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#..."],
    "club": ["..###..", "..###..", "##.#.##", "#######", "##.#.##", "...#...", "..###.."],
}


def card_shape(suit):
    red = suit in ("heart", "diamond")
    col = (206, 24, 44) if red else (24, 22, 30)
    g = SUIT[suit]

    def face(xf, u):
        if (xf < 0.08 or xf > 0.92) and (u < 0.06 or u > 0.94):
            return None                                                       # rounded corners
        gx, gy = (xf - 0.22) / 0.56, (0.72 - u) / 0.44                       # the big pip in the middle
        if 0 <= gx < 1 and 0 <= gy < 1 and g[int(gy * 7)][int(gx * 7)] == "#":
            return col
        if 0.1 < xf < 0.3 and 0.8 < u < 0.92:
            return col                                                        # corner index
        return (250, 248, 242)

    def back(xf, u):
        if (xf < 0.08 or xf > 0.92) and (u < 0.06 or u > 0.94):
            return None
        if xf < 0.1 or xf > 0.9 or u < 0.07 or u > 0.93:
            return (250, 248, 242)
        return (170, 28, 48) if (int(xf * 10) + int(u * 14)) % 2 else (120, 16, 34)
    face.back = back
    return face


# ------------------------------------------------------------------ Madara's gunbai and kama
def gunbai_shape(L, W, handle=5.0):
    """The Uchiha war fan (u from the butt): a dark wooden handle, then the great rounded fan: a pale face with a dark
    rim and the ribs drawn across it."""
    face_, rim = (222, 196, 146), (120, 70, 40)

    def f(xf, u):
        dx = (xf - 0.5) * W
        Lu = u * L
        if Lu < handle:
            if abs(dx) > 0.36:
                return None
            return (70, 46, 30) if int(Lu * 3) % 4 else (150, 120, 60)
        cy = handle + (L - handle) / 2
        ry, rx = (L - handle) / 2, W / 2
        e = (dx / rx) ** 2 + ((Lu - cy) / ry) ** 2
        if e > 1:
            return None
        if e > 0.82:
            return rim
        if abs(dx) < 0.18 and Lu < cy:
            return dk(face_, 0.78)                                            # the spine running up into the fan
        if abs(e - 0.42) < 0.035:
            return dk(face_, 0.82)
        return lt(face_, 0.2) if dx < -rx * 0.5 else face_
    return f


def kama_shape(L, W, blade=3.6):
    def f(xf, u):
        y = (xf - 0.5) * W
        Lu = u * L
        if abs(y) < 0.3 and Lu < L:
            return (96, 70, 44) if int(Lu * 2) % 5 else (60, 40, 26)
        s = (Lu - (L - 1.0)) / 1.0
        if 0 <= s <= 1 and 0.3 <= y <= blade * (1 - 0.3 * s) and abs(Lu - (L - 0.5 - (y / blade) ** 2 * 0.6)) < 0.42 * (1 - y / (blade * 1.1)) + 0.08:
            return (236, 238, 246) if y > blade * 0.2 and Lu < L - 0.5 - (y / blade) ** 2 * 0.6 else (196, 202, 214)
        return None
    return f


# ------------------------------------------------------------------ Ace's knife
def dagger_shape(L, W):
    """Ace's knife in its sheath (u from the pommel): a dark grip with a gold pommel and guard, the leather sheath."""
    def f(xf, u):
        dx = (xf - 0.5) * W
        Lu = u * L
        if Lu < 0.35:
            return (226, 186, 70) if abs(dx) < 0.3 else None
        if Lu < 2.0:
            return ((58, 40, 32) if int(Lu * 4) % 2 else (40, 28, 22)) if abs(dx) < 0.24 else None
        if Lu < 2.3:
            return (226, 186, 70) if abs(dx) < 0.62 else None
        half = 0.36 * (1 - max(0.0, (Lu - L + 1.0)) * 0.5)
        if abs(dx) > half:
            return None
        if Lu > L - 0.4:
            return (226, 186, 70)
        return lt((120, 74, 42), 0.25) if dx < -0.1 else (120, 74, 42)
    return f
