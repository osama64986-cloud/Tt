"""Light-giving blocks, redrawn: sea lantern, the three froglights, shroomlight,
redstone lamp, jack o'lantern and the campfire flames.

Each keeps the character people know from the game (a framed glowing sea
lantern, soft glowing froglights, a lamp that lights up from its middle,
dancing campfire flames) but is our own pixel art; vanilla supplies colour
references and sizes only.  Every glowing pixel also carries light in the
MERS map, so they glow in every graphics mode."""
import numpy as np

from .core import N, Tex, fbm, make_ramp, paint_idx, rng_of, shift, stack_frames, vbase, voronoi

yy, xx = np.mgrid[0:N, 0:N]


def lerp(a, b, t):
    a, b = np.array(a, float), np.array(b, float)
    return a + (b - a) * np.asarray(t)[..., None]


def ramp_paint(t, cols):
    """t 0..1 -> colour along a list of stops"""
    t = np.clip(t, 0, 1) * (len(cols) - 1)
    i = np.clip(np.floor(t).astype(int), 0, len(cols) - 2)
    f = t - i
    c = np.array(cols, float)
    return c[i] * (1 - f)[..., None] + c[i + 1] * f[..., None]


def quant(t, steps):
    return np.round(np.clip(t, 0, 1) * (steps - 1)) / (steps - 1)


# ------------------------------------------------------------------ sea lantern
def sea_lantern(frames):
    """A frame of pale prismarine around four glowing panes; a cross of light
    between the panes, a bright heart in the middle that swells and fades, and a
    few motes of light drifting around the panes from frame to frame."""
    r = rng_of("sea_lantern5")
    rim = [(84, 128, 120), (118, 164, 152), (156, 196, 184)]
    glow = [(150, 204, 192), (186, 226, 214), (220, 244, 236), (246, 255, 252)]
    out = []
    motes = r.random((5, 2)) * N
    for f in range(frames):
        pulse = 0.5 + 0.5 * np.cos(f / frames * 2 * np.pi)
        cx, cy = 7.5, 7.5
        d = np.maximum(np.abs(xx - cx), np.abs(yy - cy)) / 7.5          # square falloff
        cross = np.minimum(np.abs(xx - cx), np.abs(yy - cy))
        t = 0.75 - 0.55 * d + 0.18 * pulse * (1 - d)
        t = np.where(cross < 1.0, t + 0.25, t)                           # light seam between the panes
        idx = np.clip((t * 4).astype(int), 0, 3)
        rgb = np.array(glow, float)[idx]
        emis = 150 + idx * 30
        # pane corners: a soft inner bevel
        for (x0, y0) in ((2, 2), (9, 2), (2, 9), (9, 9)):
            rgb[y0, x0:x0 + 5] = np.minimum(rgb[y0, x0:x0 + 5] + 14, 255)
            rgb[y0:y0 + 5, x0] = np.minimum(rgb[y0:y0 + 5, x0] + 10, 255)
            rgb[y0 + 4, x0:x0 + 5] = rgb[y0 + 4, x0:x0 + 5] * 0.94
        # drifting motes
        for k, (mx, my) in enumerate(motes):
            a = f / frames * 2 * np.pi + k
            x = int(mx + 1.5 * np.cos(a)) % N
            y = int(my + 1.5 * np.sin(a)) % N
            if 1 < x < 14 and 1 < y < 14:
                rgb[y, x] = glow[3]
        # frame: two pixels, lit on the top-left, rounded corners
        frame = (xx < 2) | (yy < 2) | (xx > 13) | (yy > 13)
        light = (xx + yy) < 15
        rgb[frame] = np.where(light[frame][:, None], np.array(rim[2], float), np.array(rim[1], float))
        edge_in = ((xx == 1) | (yy == 1) | (xx == 14) | (yy == 14)) & ~((xx < 1) | (yy < 1) | (xx > 14) | (yy > 14))
        rgb[edge_in] = rgb[edge_in] * 0.9
        for (x, y) in ((0, 0), (15, 0), (0, 15), (15, 15)):
            rgb[y, x] = rim[0]
        emis = np.where(frame, 60, emis)
        hgt = np.where(frame, 0.85, 0.45)
        t_ = Tex(np.clip(rgb, 0, 255).astype(np.uint8), hgt, rough=60, bump=0.7)
        t_.emis = emis
        out.append(t_)
    return stack_frames(out)


# ------------------------------------------------------------------ froglights
def froglight(name, rim, core, side=True):
    """Soft glowing block: bright in the middle, deepening to its colour at the
    edges.  The side shows the soft vertical folds of the jelly, the top a gentle
    ring; tiny brighter flecks keep it alive."""
    r = rng_of(name)
    if side:
        d = np.maximum(np.abs(xx - 7.5) / 7.5, np.abs(yy - 7.5) / 7.5 * 0.9)
        folds = 0.06 * np.sin(xx * 1.3 + 0.6) + 0.04 * np.sin(xx * 2.9)
    else:
        d = np.hypot(xx - 7.5, yy - 7.5) / 9.0
        folds = 0.05 * np.sin(np.hypot(xx - 7.5, yy - 7.5) * 1.6)
    n = fbm(r, ((4, 1.0), (8, 0.5)), sx=1, sy=1) if not side else fbm(r, ((8, 1.0), (16, 0.5)), sx=1, sy=6)
    t = 1.0 - np.clip((d - 0.45) / 0.55, 0, 1) ** 1.3 + folds * 0.6 + (n - 0.5) * 0.22
    t = quant(t, 6)
    cols = [shift(rim, dv=-0.12), rim, shift(rim, dv=0.06, ds=-0.12), lerp(rim, core, 0.6).astype(int).tolist(), core]
    rgb = ramp_paint(t, cols)
    w = r.random((N, N))
    rgb[w > 0.95] = np.minimum(rgb[w > 0.95] + 18, 255)
    edge = (xx == 0) | (yy == 0) | (xx == 15) | (yy == 15)
    rgb[edge] = rgb[edge] * 0.92
    t_ = Tex(np.clip(rgb, 0, 255).astype(np.uint8), 0.4 + 0.3 * t, rough=80, sss=120, bump=0.6)
    t_.emis = (120 + 135 * t).clip(0, 255)
    return t_


# ------------------------------------------------------------------ shroomlight
def shroomlight():
    """A spongy glowing fungus: warm orange flesh with bright yellow glowing
    pockets of different sizes, each pocket hottest in its middle, and small dark
    pores between them."""
    r = rng_of("shroomlight5")
    base = vbase("shroomlight")
    flesh = make_ramp(shift(base, dv=-0.06), 5, 0.4)
    ids, f1, f2, pts = voronoi(r, 9)
    edge = f2 - f1
    m = fbm(r, ((4, 1.0), (8, 0.5)))
    idx = 1 + (m > 0.5) + (m > 0.78)
    rgb = paint_idx(idx, flesh).astype(float)
    heat = np.clip((edge - 1.0) / 2.0, 0, 1)
    pocket = heat > 0.12
    hot = ramp_paint(quant(heat, 4), [(255, 150, 60), (255, 186, 84), (255, 222, 128), (255, 246, 190)])
    rgb[pocket] = hot[pocket]
    pores = (edge < 0.5) & (r.random((N, N)) < 0.5)
    rgb[pores] = np.array(shift(base, dv=-0.34, ds=0.06), float)
    emis = np.where(pocket, 170 + 85 * heat, 90)
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(pocket, 0.6, 0.35), rough=180, bump=1.0)
    t.emis = emis
    return t


# ------------------------------------------------------------------ redstone lamp
def redstone_lamp(on):
    """A glass lamp in a lattice: the dark frame of the case, a diamond-shaped
    lattice of glass panes, and behind them the light - white-gold in the middle
    and fading towards the corners when lit, a dull glassy amber when off."""
    r = rng_of("redstone_lamp5")
    if on:
        glow = [(170, 96, 40), (222, 146, 62), (250, 200, 110), (255, 238, 180), (255, 252, 230)]
        frame = [(70, 40, 20), (104, 62, 30), (140, 88, 44)]
    else:
        glow = [(70, 40, 20), (98, 58, 28), (122, 76, 38), (142, 94, 50), (160, 110, 62)]
        frame = [(46, 26, 12), (70, 40, 20), (96, 58, 30)]
    d = (np.abs(xx - 7.5) + np.abs(yy - 7.5)) / 15.0
    t = 1.0 - d * 1.25
    idx = np.clip((t * 5).astype(int), 0, 4)
    rgb = np.array(glow, float)[idx]
    # a dark diamond ring holds the big middle pane; the corners are four smaller panes
    dd = np.abs(xx - 7.5) + np.abs(yy - 7.5)
    lat = (dd >= 5.0) & (dd <= 6.0)
    rgb[lat] = np.array(frame[0], float)
    rim_lit = (dd > 4.0) & (dd < 5.0)
    rgb[rim_lit] = np.minimum(rgb[rim_lit] * 1.08 + 8, 255)    # the pane's edge catches light
    rgb[(dd > 6.0) & (dd < 7.0)] *= 0.86
    # case frame, lit top-left
    case = (xx == 0) | (yy == 0) | (xx == 15) | (yy == 15)
    rgb[case] = frame[0]
    rgb[(yy == 0) & (xx < 15)] = frame[2]
    rgb[(xx == 0) & (yy < 15)] = frame[2]
    inner = (xx == 1) | (yy == 1) | (xx == 14) | (yy == 14)
    rgb[inner & ~case] = rgb[inner & ~case] * 0.8
    w = r.random((N, N))
    rgb[(w > 0.93) & ~case & ~lat] = np.minimum(rgb[(w > 0.93) & ~case & ~lat] + 12, 255)
    t_ = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(case | lat, 0.8, 0.45), rough=70, bump=0.8)
    t_.emis = np.where(case, 0, 120 + 30 * idx) if on else 0
    return t_


# ------------------------------------------------------------------ jack o'lantern
def jack(pumpkin_side, lit):
    """The pumpkin's own face with a carved grin: slanted eyes, a small nose and
    a wide toothy mouth.  The cut edges are a pale rind; when lit the holes glow
    hot yellow in the middle, cooling to orange at the edges."""
    t = pumpkin_side.copy()
    rgb = t.rgb.astype(float)
    face = np.zeros((N, N), bool)
    eyes = [(2, 3), (3, 3), (4, 3), (5, 3), (2, 4), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (5, 5), (4, 6), (5, 6),
            (10, 3), (11, 3), (12, 3), (13, 3), (10, 4), (11, 4), (12, 4), (13, 4), (10, 5), (11, 5), (12, 5),
            (10, 6), (11, 6)]                                  # big slanted eyes
    for x, y in eyes:
        face[y, x] = True
    face[8, 7] = face[8, 8] = True                             # nose
    for x in range(2, 14):                                     # wide grin
        face[10, x] = x in (2, 13) or x in (4, 5, 7, 8, 10, 11)
        face[11, x] = True
        face[12, x] = 3 <= x <= 12
    for x in (5, 9):                                           # two lower teeth
        face[12, x] = False
    face[13, 5:11] = True
    if lit:
        dist = np.hypot(xx - 7.5, yy - 8.5) / 7
        hot = ramp_paint(1 - dist, [(255, 196, 52), (255, 228, 104), (255, 246, 172), (255, 255, 232)])
        rgb[face] = hot[face]
    else:
        rgb[face] = np.array((40, 20, 6), float)
    # pale rind along the bottom/right of each cut (the cut wall catching light)
    rind = ~face & (np.roll(face, -1, 0) | np.roll(face, -1, 1))
    rgb[rind] = rgb[rind] * 0.75 + np.array((250, 200, 120), float) * 0.25
    shade = ~face & (np.roll(face, 1, 0) | np.roll(face, 1, 1))
    rgb[shade] = rgb[shade] * 0.78
    if lit:
        rgb[~face] = rgb[~face] * 0.9                          # the shell a touch darker so the glow stands out
    t.rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    t.height = np.where(face, 0.1, t.height)
    t.emis = np.where(face, 230, 0) if lit else 0
    return t


# ------------------------------------------------------------------ campfire flames
def flames(name, cols, frames=8):
    """Campfire flames: tall tongues rising from a hot bed and breaking into
    wisps near the top; the noise scrolls up two pixels a frame so the loop is
    seamless.  Colour runs from the white-hot root to orange-red tips."""
    r = rng_of(name)
    n1 = fbm(r, ((4, 1.0), (8, 0.6), (16, 0.3)))
    n2 = fbm(r, ((2, 1.0), (4, 0.5)))
    out = []
    for f in range(frames):
        a = np.roll(n1, -2 * f, axis=0)
        b = np.roll(n2, -2 * f, axis=0)
        h = (N - 1 - yy) / (N - 1)                              # 0 bottom .. 1 top
        sway = (b - 0.5) * 3.0 * h
        half = 5.6 * (1 - h) ** 0.65 + 0.6                      # flame half-width at this height
        dx = np.abs(xx - 7.5 - sway)
        body = half - dx + (a - 0.5) * 3.2
        mask = (body > 0) & ~((h > 0.55) & (a < 0.42))          # wisps break off near the top
        heat = np.clip(body / 4.0, 0, 1) * (1 - 0.55 * h) + (1 - h) * 0.3
        rgb = ramp_paint(quant(heat, 5), cols)
        alpha = np.where(mask, 255, 0).astype(np.uint8)
        t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), heat, alpha=alpha, rough=200, bump=0.3)
        t.emis = np.where(mask, 200 + 55 * heat, 0)
        out.append(t)
    return stack_frames(out)


def build(out, flip, variations):
    out["sea_lantern"] = sea_lantern(5)
    for nm, rim, core in (("ochre", (226, 170, 84), (255, 250, 214)),
                          ("verdant", (122, 186, 112), (244, 255, 238)),
                          ("pearlescent", (200, 150, 196), (255, 248, 250))):
        out[f"{nm}_froglight_side"] = froglight(f"{nm}_fl_side", rim, core, side=True)
        out[f"{nm}_froglight_top"] = froglight(f"{nm}_fl_top", rim, core, side=False)
    out["shroomlight"] = shroomlight()
    out["redstone_lamp_on"] = redstone_lamp(True)
    out["redstone_lamp_off"] = redstone_lamp(False)
    out["pumpkin_face_on"] = jack(out["pumpkin_side"], True)
    out["pumpkin_face_off"] = jack(out["pumpkin_side"], False)
    out["campfire"] = flames("campfire5", [(196, 60, 20), (240, 120, 30), (255, 180, 50), (255, 226, 120), (255, 250, 210)])
    out["soul_campfire"] = flames("soul_campfire5", [(20, 80, 120), (30, 150, 180), (70, 210, 220), (160, 240, 245), (230, 255, 255)])
