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


# ------------------------------------------------------------------ campfire logs
BARK = [(64, 50, 30), (86, 66, 38), (112, 86, 52), (140, 108, 64), (156, 122, 74)]
END = [(150, 116, 68), (176, 140, 88), (196, 160, 104)]
ASH = [(24, 26, 30), (32, 36, 44), (46, 54, 68), (62, 72, 90), (92, 100, 116)]


def campfire_log(name, lit, ember=None, frame=0):
    """The campfire's map: rows 0-3 the log's bark (lengthwise), rows 4-7 x0-3 the
    cut end (rows 4-7 across the whole width once lit: the charred underside),
    rows 8-15 the bed of ash and coals under the fire.  Lit: the bark chars and
    cracks with embers, the bed glows from a hot heart in its middle."""
    r = rng_of(name)
    rf = rng_of(f"{name}_{frame}")
    rgb = np.zeros((N, N, 3), float)
    alpha = np.zeros((N, N), np.uint8)
    emis = np.zeros((N, N))
    hgt = np.full((N, N), 0.5)
    g = fbm(r, ((2, 1.0), (16, 0.8)), sx=8, sy=1)                # lengthwise grain
    for y in range(0, 4):
        for x in range(N):
            k = 2 + (g[y, x] > 0.62) - (g[y, x] < 0.32) + (1 if y == 0 else 0) - (1 if y == 3 else 0)
            rgb[y, x] = BARK[max(0, min(4, k))]
            alpha[y, x] = 255
    for y in range(4, 8):                                         # cut end with rings
        for x in range(0, 4):
            d = max(abs(x - 1.5), abs(y - 5.5))
            rgb[y, x] = END[2] if d < 1 else (END[1] if d < 1.6 else END[0])
            alpha[y, x] = 255
    for y in range(8, N):                                         # ash bed
        for x in range(N):
            k = 1 + int(r.random() < 0.45) + int(r.random() < 0.18) - int(r.random() < 0.2)
            rgb[y, x] = ASH[k] if r.random() > 0.04 else ASH[4]
            alpha[y, x] = 255
    hgt[8:] = 0.3
    if lit:
        e = ember
        # charred bark with ember cracks
        char = (rf.random((8, N)) < 0.35) | (g[:8] < 0.38)
        for y in range(0, 8):
            for x in range(N):
                if y >= 4 or char[y, x]:
                    rgb[y, x] = ASH[int(rf.integers(0, 3))]
                    alpha[y, x] = 255
                    if rf.random() < (0.22 if y >= 4 else 0.12):
                        k = int(rf.integers(1, 4))
                        rgb[y, x] = e[k]
                        emis[y, x] = 150 + 30 * k
        for y in range(4, 8):                                     # bark ends stay on the outer columns
            rgb[y, 0] = BARK[2]
            rgb[y, 15] = BARK[1]
        # glowing heart of the bed
        for y in range(8, N):
            for x in range(N):
                d = np.hypot((x - 7.5) / 1.2, y - 11.0)
                heat = 1 - d / 5.2 + (rf.random() - 0.5) * 0.5
                if heat > 0.1:
                    k = int(np.clip(heat * 4, 0, 4))
                    rgb[y, x] = e[k]
                    emis[y, x] = 140 + 28 * k
                    hgt[y, x] = 0.4
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), hgt, alpha=alpha, rough=200, bump=0.8)
    t.emis = emis
    return t


# ------------------------------------------------------------------ copper bulb
def copper_bulb(base, lit, powered):
    """A copper casing with a rivetted rim around a glass dome; inside, a
    four-petalled filament that glows warm white-gold when lit and shows dull
    amber when not; powered bulbs carry a red dot at the heart."""
    ramp = make_ramp(base, 5, 0.42)
    rgb = np.array(ramp[2], float) * np.ones((N, N, 3))
    tex = fbm(rng_of("bulb_metal"), ((4, 1.0), (8, 0.5)))
    rgb = rgb * (0.94 + 0.12 * tex[..., None])
    rim = (xx < 2) | (yy < 2) | (xx > 13) | (yy > 13)
    rgb[rim] = ramp[3]
    rgb[(xx == 0) | (yy == 0)] = ramp[4]
    rgb[(xx == 15) | (yy == 15)] = ramp[1]
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):           # rivets
        rgb[y, x] = ramp[4]
    glass = (xx >= 3) & (xx <= 12) & (yy >= 3) & (yy <= 12)
    rgb[(xx == 2) & ~(yy < 2) & ~(yy > 13)] = ramp[0]             # deep groove round the glass
    rgb[(yy == 2) & ~(xx < 2) & ~(xx > 13)] = ramp[0]
    rgb[(xx == 13) & (yy >= 2) & (yy <= 13)] = ramp[3]
    rgb[(yy == 13) & (xx >= 2) & (xx <= 13)] = ramp[3]
    if lit:
        gl = [(232, 150, 70), (250, 196, 104), (255, 226, 150), (255, 246, 206), (255, 255, 240)]
    else:
        gl = [(92, 54, 36), (116, 70, 44), (138, 88, 54), (158, 106, 66), (176, 124, 80)]
    dx, dy = np.abs(xx - 7.5), np.abs(yy - 7.5)
    petal = np.minimum(dx, dy)                                     # a plus shape with rounded arms
    t = 1 - np.clip(petal / 3.0, 0, 1) * 0.7 - np.hypot(dx, dy) / 14
    idx = np.clip((t * 5).astype(int), 0, 4)
    rgb[glass] = np.array(gl, float)[idx][glass]
    corner_glint = glass & (xx == 4) & (yy == 4)
    rgb[corner_glint] = np.minimum(rgb[corner_glint] + 30, 255)
    emis = np.where(glass, 120 + 30 * idx, 0) if lit else np.zeros((N, N))
    if powered:
        rgb[7:9, 7:9] = (255, 50, 36)
        rgb[7, 7] = (255, 140, 120)
        emis[7:9, 7:9] = 240
    t_ = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(glass, 0.45, 0.8), rough=np.where(glass, 40, 110),
             metal=np.where(glass, 0, 210), bump=0.8)
    t_.emis = emis
    return t_


# ------------------------------------------------------------------ beacon
def beacon():
    """The beacon's core: a faceted crystal of light in a clear frame - bright
    white at its heart, cooling through aqua to teal at the edges, with facet
    lines running to the corners."""
    rgb = np.zeros((N, N, 3), float)
    dx, dy = np.abs(xx - 7.5), np.abs(yy - 7.5)
    d = np.maximum(dx, dy) / 7.5
    star = np.minimum(dx, dy) / 7.5
    t = 1 - d * 0.75 - star * 0.5
    cols = [(32, 150, 150), (54, 196, 192), (118, 232, 226), (190, 250, 246), (246, 255, 255)]
    idx = np.clip((t * 5).astype(int), 0, 4)
    rgb = np.array(cols, float)[idx]
    diag = (np.abs(dx - dy) < 0.6) & (d > 0.35)
    rgb[diag] = np.minimum(rgb[diag] + 22, 255)                    # facet edges to the corners
    frame = (xx == 0) | (yy == 0) | (xx == 15) | (yy == 15)
    rgb[frame] = (226, 252, 252)
    rgb[(xx == 15) | (yy == 15)] = (170, 226, 226)
    t_ = Tex(np.clip(rgb, 0, 255).astype(np.uint8), 0.5 + 0.08 * idx, rough=20, bump=0.5)
    t_.emis = np.where(frame, 60, 130 + 30 * idx)
    return t_


# ------------------------------------------------------------------ glow lichen
def glow_lichen():
    """Glow lichen: loose crusts of grey-green lichen spreading over the face,
    dotted with small pale berries that glow."""
    r = rng_of("glow_lichen5")
    m = fbm(r, ((4, 1.0), (8, 0.6), (16, 0.3)))
    w = r.random((N, N))
    body = (m > 0.48) & (w < 0.82) | (w > 0.97)
    ramp = [(76, 104, 92), (98, 130, 114), (124, 156, 138), (150, 180, 160)]
    idx = np.clip(((m - 0.48) * 9).astype(int) + (w > 0.6), 0, 3)
    rgb = np.array(ramp, float)[idx]
    alpha = np.where(body, 255, 0).astype(np.uint8)
    emis = np.zeros((N, N))
    for _ in range(9):
        x, y = int(r.integers(0, N)), int(r.integers(0, N))
        if body[y, x]:
            rgb[y, x] = (228, 240, 196)
            emis[y, x] = 230
            for ox, oy in ((1, 0), (0, 1)):
                xx_, yy_ = (x + ox) % N, (y + oy) % N
                if body[yy_, xx_]:
                    rgb[yy_, xx_] = (176, 200, 150)
                    emis[yy_, xx_] = 120
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(body, 0.6, 0), alpha=alpha, rough=220, sss=80, bump=0.6)
    t.emis = emis
    return t


# ------------------------------------------------------------------ respawn anchor top
def anchor_top(frames, alpha, lit):
    """Top of the respawn anchor: a crying-obsidian rim flecked with glowing
    purple tears around a well; when charged the well holds a slowly turning
    spiral of violet light."""
    r = rng_of("anchor_top5")
    ob = [(20, 10, 36), (34, 20, 58), (52, 32, 84), (72, 46, 112)]
    tears = r.random((N, N)) < 0.12
    out = []
    for f in range(frames):
        rgb = np.zeros((N, N, 3), float)
        emis = np.zeros((N, N))
        rimm = (xx < 2) | (yy < 2) | (xx > 13) | (yy > 13)
        k = (r.random((N, N)) * 3).astype(int)
        rgb[rimm] = np.array(ob, float)[k][rimm]
        rgb[(xx == 0) | (yy == 0)] = ob[3]
        tear = rimm & tears
        rgb[tear] = (150, 60, 230)
        emis[tear] = 200
        lip = (~rimm) & ((xx == 2) | (yy == 2) | (xx == 13) | (yy == 13))
        rgb[lip] = (14, 6, 24)
        well = (~rimm) & ~lip
        if lit:
            a = np.arctan2(yy - 7.5, xx - 7.5)
            rr = np.hypot(xx - 7.5, yy - 7.5)
            ph = f / frames * 2 * np.pi
            sp = 0.5 + 0.5 * np.sin(2 * a + rr * 1.4 - ph)
            v = np.clip(sp * (1 - rr / 7) + (1 - rr / 5.5) * 0.5, 0, 1)
            cols = [(60, 16, 120), (110, 34, 200), (156, 70, 240), (206, 140, 255), (246, 220, 255)]
            idx = np.clip((v * 5).astype(int), 0, 4)
            rgb[well] = np.array(cols, float)[idx][well]
            emis[well] = (140 + 28 * idx)[well]
        else:
            rgb[well] = (10, 4, 18)
        t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(well, 0.15, 0.8), alpha=np.full((N, N), alpha, np.uint8),
                rough=50, bump=0.8)
        t.emis = emis
        out.append(t)
    return stack_frames(out) if frames > 1 else out[0]


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
    fire = [(110, 40, 10), (200, 90, 10), (232, 150, 30), (250, 206, 90), (255, 244, 180)]
    soul = [(20, 70, 90), (20, 140, 160), (50, 200, 210), (130, 236, 240), (220, 255, 255)]
    out["campfire_log"] = campfire_log("campfire_log5", False)
    out["campfire_log_lit"] = stack_frames([campfire_log("campfire_log5", True, fire, f) for f in range(4)])
    out["soul_campfire_log_lit"] = stack_frames([campfire_log("campfire_log5", True, soul, f) for f in range(4)])
    for pre, key in (("", "copper_block"), ("exposed_", "exposed_copper"), ("weathered_", "weathered_copper"),
                     ("oxidized_", "oxidized_copper")):
        for lit in (False, True):
            for pw in (False, True):
                nm = pre + "copper_bulb" + ("_lit" if lit else "") + ("_powered" if pw else "")
                out[nm] = copper_bulb(vbase(key), lit, pw)
    out["beacon"] = beacon()
    out["glow_lichen"] = glow_lichen()
    from .core import STATS
    a_lo = STATS["respawn_anchor_top"]["alpha"][0]
    out["respawn_anchor_top"] = anchor_top(STATS["respawn_anchor_top"]["size"][1] // N, a_lo, True)
    out["respawn_anchor_top_off"] = anchor_top(1, 255, False)
    out["soul_campfire"] = flames("soul_campfire5", [(20, 80, 120), (30, 150, 180), (70, 210, 220), (160, 240, 245), (230, 255, 255)])
