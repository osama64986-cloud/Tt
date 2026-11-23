"""Sixth pass, from a full audit against the game's textures: blocks whose
colour or shape had drifted too far from what players expect.

Redrawn: sculk catalyst (side, bloom, bottom), sculk vein, daylight detector
(normal and inverted), end portal frame (top, side, eye), grindstone side,
bell top, stonecutter side.  Re-coloured to the game's palette while keeping
our own drawing: pitcher crop, grindstone pivot, loom bottom, birch door.
Every shape follows the game's own transparency map so it fits its model."""
import numpy as np
from PIL import Image

from .core import N, STATS, Tex, fbm, make_ramp, rng_of, shift, stack_frames, vbase

yy, xx = np.mgrid[0:N, 0:N]
VAN = "/home/user/mojang/bedrock-samples/resource_pack/textures/blocks/"

SCULK = [(6, 18, 24), (10, 30, 38), (16, 44, 54), (24, 60, 72)]
CYAN = [(20, 130, 150), (40, 200, 214), (120, 240, 246)]
BONE = [(118, 128, 112), (150, 160, 142), (178, 188, 168), (204, 212, 192), (226, 232, 214)]


def vanilla_image(name):
    import os
    for ext in (".png", ".tga"):
        if os.path.exists(VAN + name + ext):
            return Image.open(VAN + name + ext).convert("RGBA")
    return None


def vanilla_alpha(name):
    """the game's own transparency for this texture (first frame)"""
    im = vanilla_image(name)
    if im is None:
        return np.full((N, N), 255, np.uint8)
    return np.array(im)[..., 3][:N]


def recolour(t, name):
    """Keep our drawing, take the game's palette: each pixel takes the game's
    colour of the same brightness rank."""
    im = vanilla_image(name)
    if im is None:
        return t
    v = np.array(im).astype(float)
    o = t.rgb.astype(float)
    if v.shape[:2] != o.shape[:2]:
        return t
    vm = v[..., 3] > 0
    om = t.alpha > 0
    if vm.sum() < 4 or om.sum() < 4:
        return t
    vc = v[..., :3][vm]
    vl = vc @ [0.3, 0.59, 0.11]
    vc = vc[np.argsort(vl)]
    ol = o[..., :3] @ [0.3, 0.59, 0.11]
    ranks = np.argsort(np.argsort(ol[om]))
    q = ranks / max(1, om.sum() - 1)
    pick = vc[np.clip((q * (len(vc) - 1)).astype(int), 0, len(vc) - 1)]
    new = o.copy()
    new[om] = pick
    t.rgb = np.clip(new, 0, 255).astype(np.uint8)
    return t


# ------------------------------------------------------------------ sculk catalyst
def sculk_speckle(r, h, w, glow_rate=0.06):
    idx = (r.random((h, w)) * 3).astype(int)
    rgb = np.array(SCULK, float)[idx]
    cy = r.random((h, w)) < glow_rate
    rgb[cy] = CYAN[1]
    return rgb, cy


def catalyst_side(bloom, f=0, n=1):
    r = rng_of("catalyst_side6")
    rgb, cy = sculk_speckle(r, N, N, 0.05 if not bloom else 0.09)
    emis = np.where(cy, 200, 0).astype(float)
    # bone jaw: teeth rising into the sculk, ribs running down
    edge = 7 + np.array([0, 1, 2, 1, 3, 4, 3, 1, 0, 1, 3, 4, 3, 2, 1, 0]) * -1  # tooth tips higher
    for x in range(N):
        top = int(edge[x])
        for y in range(top, N):
            k = 2 + (x % 4 == 1) - (x % 4 == 3) + (1 if y == top else 0) - (1 if y >= 14 else 0)
            rgb[y, x] = BONE[max(0, min(4, k))]
            emis[y, x] = 0
        if top - 1 >= 0:
            rgb[top - 1, x] = SCULK[0]                        # shadow above each tooth
    if bloom:                                                  # a band of light that pulses
        k = 0.5 + 0.5 * np.cos(f / n * 2 * np.pi)
        band = np.array(CYAN[1], float) * (0.6 + 0.4 * k) + np.array(CYAN[2], float) * 0.0
        rgb[1, :] = band
        rgb[1, (np.arange(N) + f) % 3 == 0] = CYAN[2]
        rgb[2, (np.arange(N) + 2 * f) % 5 == 0] = CYAN[1]
        emis[1, :] = 150 + 90 * k
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(yy >= 7, 0.7, 0.4), rough=180, bump=1.0)
    t.emis = emis
    return t


def catalyst_bottom():
    r = rng_of("catalyst_bottom6")
    idx = np.clip(2 + (r.random((N, N)) < 0.3) - (r.random((N, N)) < 0.25), 0, 4)
    rgb = np.array(BONE, float)[idx]
    d = np.abs(xx - 7.5) + np.abs(yy - 7.5)
    star = (d < 4.5) | ((np.minimum(np.abs(xx - 7.5), np.abs(yy - 7.5)) < 1) & (d < 7))
    sr, cy = sculk_speckle(r, N, N, 0.05)
    rgb[star] = sr[star]
    rgb[star & cy] = CYAN[1]
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(star, 0.3, 0.6), rough=190, bump=1.0)
    t.emis = np.where(star & cy, 200, 0)
    return t


def sculk_vein(frames):
    """Thin branching veins of sculk over the surface, with small cyan nodes
    that light up in turn."""
    r = rng_of("sculk_vein6")
    mask = np.zeros((N, N), bool)
    for _ in range(11):
        x, y = float(r.uniform(0, N)), float(r.uniform(0, N))
        a = r.uniform(0, 2 * np.pi)
        for _ in range(int(r.integers(10, 20))):
            mask[int(y) % N, int(x) % N] = True
            if r.random() < 0.35:
                mask[int(y + 1) % N, int(x) % N] = True
            a += r.uniform(-0.6, 0.6)
            x += np.cos(a)
            y += np.sin(a)
    nodes = [(int(x), int(y)) for y, x in zip(*np.nonzero(mask))]
    r.shuffle(nodes)
    nodes = nodes[:6]
    out = []
    for f in range(frames):
        rgb = np.zeros((N, N, 3), float)
        idx = (r.random((N, N)) * 2).astype(int) + 1
        rgb[:] = np.array(SCULK, float)[idx]
        emis = np.zeros((N, N))
        for k, (x, y) in enumerate(nodes):
            on = (k + f) % 3 == 0
            rgb[y, x] = CYAN[2] if on else CYAN[0]
            emis[y, x] = 230 if on else 90
        t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(mask, 0.6, 0), alpha=np.where(mask, 255, 0).astype(np.uint8),
                rough=180, bump=0.6)
        t.emis = emis
        out.append(t)
    return stack_frames(out)


# ------------------------------------------------------------------ daylight detector
def daylight_top(inverted):
    """A dark wooden grid holding nine glass cells; each cell a softly lit
    rounded pane, brighter in its middle."""
    wood = make_ramp((70, 52, 34), 5, 0.4)
    cell = [(150, 170, 200), (176, 196, 222), (206, 220, 238)] if inverted else [(180, 168, 150), (214, 204, 186), (240, 234, 220)]
    rgb = np.array(wood[1], float) * np.ones((N, N, 3))
    g = fbm(rng_of("dd_wood"), ((2, 1.0), (16, 0.5)), sx=6, sy=1)
    rgb = rgb * (0.9 + 0.2 * g[..., None])
    for cy in (1, 6, 11):
        for cx in (1, 6, 11):
            for y in range(cy, cy + 4):
                for x in range(cx, cx + 4):
                    corner = (y in (cy, cy + 3)) and (x in (cx, cx + 3))
                    if corner:
                        continue
                    mid = (cy + 1 <= y <= cy + 2) and (cx + 1 <= x <= cx + 2)
                    rgb[y, x] = cell[2] if mid else cell[1]
            rgb[cy + 3, cx + 1:cx + 3] = cell[0]
            rgb[cy + 1:cy + 3, cx + 3] = cell[0]
    for k in (0, 5, 10, 15):                                  # grid lines a touch lighter on top
        rgb[k, :] = wood[2]
        rgb[:, k] = np.minimum(rgb[:, k], np.array(wood[2], float))
    rgb[15, :] = wood[0]
    rgb[:, 15] = wood[0]
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(rgb.mean(-1) > 120, 0.4, 0.7), rough=120, bump=0.8)


# ------------------------------------------------------------------ end portal frame
TEAL = [(34, 70, 62), (48, 96, 84), (66, 122, 106), (92, 150, 130), (124, 176, 154)]
ENDST = [(196, 194, 140), (216, 214, 158), (232, 230, 178), (244, 242, 200)]


def endframe_top():
    r = rng_of("endframe_top6")
    idx = np.clip(2 + (r.random((N, N)) < 0.3) - (r.random((N, N)) < 0.3), 0, 4)
    rgb = np.array(TEAL, float)[idx]
    d = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))
    rgb[(d > 7)] = TEAL[3]
    rgb[(xx == 15) | (yy == 15)] = TEAL[1]
    ring = (d > 4) & (d < 5.5)
    rgb[ring] = ENDST[2]
    rgb[ring & ((xx + yy) > 15)] = ENDST[0]
    hole = d < 4
    deep = (d < 4) & (d >= 3)
    rgb[hole] = (10, 26, 22)
    rgb[deep & ((xx + yy) < 15)] = (6, 16, 14)
    rgb[(xx == 0) | (yy == 0)] = TEAL[4]
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(hole, 0.1, 0.8), rough=120, bump=1.0)


def endframe_side():
    r = rng_of("endframe_side6")
    rgb = np.zeros((N, N, 3), float)
    idx = np.clip(1 + (r.random((N, N)) < 0.35) + (r.random((N, N)) < 0.15) - (r.random((N, N)) < 0.2), 0, 3)
    rgb[:] = np.array(ENDST, float)[idx]                      # end stone below
    for y in range(3, 7):                                      # the frame's teal lip
        for x in range(N):
            rgb[y, x] = TEAL[3] if y == 3 else TEAL[2]
    rgb[4:6, 3:13] = ENDST[2]                                  # pale slot rim
    rgb[5, 4:12] = (12, 30, 26)                                # the slot the eye sits in
    rgb[6, :] = TEAL[1]
    rgb[7, :] = (rgb[7, :] * 0.8)
    alpha = vanilla_alpha("endframe_side")
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(yy < 7, 0.8, 0.6), alpha=alpha, rough=150, bump=1.0)


def endframe_eye():
    rgb = np.zeros((N, N, 3), float)
    for y in range(0, 4):                                      # the eye's sides
        for x in range(4, 12):
            rgb[y, x] = TEAL[1] if y else TEAL[2]
    iris = [(28, 70, 50), (50, 120, 80), (90, 172, 116), (150, 220, 160), (220, 250, 220)]
    for y in range(4, 12):                                     # the eye seen from above
        for x in range(4, 12):
            d = max(abs(x - 7.5), abs(y - 7.5))
            k = 0 if d > 3 else (1 if d > 2.4 else (2 if d > 1.5 else 3))
            rgb[y, x] = iris[k]
    rgb[6:10, 7:9] = (8, 20, 14)                               # slit pupil
    rgb[5, 5] = iris[4]
    rgb[6, 5] = iris[3]
    alpha = vanilla_alpha("endframe_eye")
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.full((N, N), 0.6), alpha=alpha, rough=60, bump=0.8)
    t.emis = np.where((yy >= 4) & (yy < 12) & (xx >= 4) & (xx < 12), 60, 0)
    return t


# ------------------------------------------------------------------ grindstone, bell, stonecutter
def grindstone_side():
    r = rng_of("grind_side6")
    st = make_ramp(vbase("grindstone_side"), 5, 0.4)
    rgb = np.zeros((N, N, 3), float)
    d = np.maximum(np.abs(xx - 5.5), np.abs(yy - 5.5))
    ri = d.astype(int)
    idx = np.where(ri % 2 == 0, 3, 2) + (r.random((N, N)) < 0.2) - (r.random((N, N)) < 0.15)
    idx = np.where(ri >= 5, 1, idx)
    rgb[:] = np.array(st, float)[np.clip(idx, 0, 4)]
    rgb[(d < 1)] = st[0]
    rgb[(xx == 0) & (yy < 12)] = st[4]
    rgb[(yy == 0) & (xx < 12)] = st[4]
    alpha = vanilla_alpha("grindstone_side")
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.full((N, N), 0.6), alpha=alpha, rough=200, bump=1.0)


def bell_top():
    gold = [(206, 150, 34), (236, 186, 52), (252, 214, 80), (255, 236, 130), (255, 250, 196)]
    rgb = np.zeros((N, N, 3), float)
    d = np.maximum(np.abs(xx - 3.5), np.abs(yy - 3.5))
    k = np.where(d > 3, 1, np.where(d > 2, 3, np.where(d > 1, 2, 4)))
    rgb[:] = np.array(gold, float)[k]
    rgb[(xx + yy) > 8] *= 0.85
    alpha = vanilla_alpha("bell_top")
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.full((N, N), 0.6), alpha=alpha, rough=50, metal=220, bump=0.8)


def stonecutter_side():
    r = rng_of("stonecutter_side6")
    wood = make_ramp((96, 70, 46), 5, 0.42)
    stone = make_ramp((128, 128, 128), 5, 0.36)
    rgb = np.zeros((N, N, 3), float)
    idx = np.clip(2 + (r.random((N, N)) < 0.3) - (r.random((N, N)) < 0.3), 0, 4)
    rgb[:] = np.array(stone, float)[idx]
    rgb[7, :] = stone[4]                                        # lit stone lip on top
    frame = (yy >= 9) & ((xx < 2) | (xx > 13) | (yy == 9) | (yy == 15))
    g = fbm(r, ((2, 1.0), (16, 0.5)), sx=6, sy=1)
    widx = np.clip(2 + (g > 0.6) - (g < 0.3), 0, 4)
    rgb[frame] = np.array(wood, float)[widx][frame]
    rgb[9, :] = wood[3]
    rgb[15, :] = wood[0]
    rgb[(yy > 9) & (yy < 15) & ((xx == 1) | (xx == 14))] = wood[1]
    alpha = vanilla_alpha("stonecutter2_side")
    return Tex(np.clip(rgb, 0, 255).astype(np.uint8), np.where(frame, 0.8, 0.6), alpha=alpha, rough=180, bump=1.0)


def build(out, flip, variations):
    out["sculk_catalyst_side"] = catalyst_side(False)
    nb = STATS["sculk_catalyst_side_bloom"]["size"][1] // N
    out["sculk_catalyst_side_bloom"] = stack_frames([catalyst_side(True, f, nb) for f in range(nb)])
    out["sculk_catalyst_bottom"] = catalyst_bottom()
    out["sculk_vein"] = sculk_vein(STATS["sculk_vein"]["size"][1] // N)
    out["daylight_detector_top"] = daylight_top(False)
    out["daylight_detector_inverted_top"] = daylight_top(True)
    out["endframe_top"] = endframe_top()
    out["endframe_side"] = endframe_side()
    out["endframe_eye"] = endframe_eye()
    out["grindstone_side"] = grindstone_side()
    out["bell_top"] = bell_top()
    out["stonecutter2_side"] = stonecutter_side()
    for nm in [k for k in list(out) if k.startswith("pitcher_crop")] + ["grindstone_pivot", "loom_bottom",
                                                                         "door_birch_upper", "door_birch_lower"]:
        if nm in out:
            out[nm] = recolour(out[nm], nm)
