"""Fifth refresh pass: the cut ends of the nether stems, and every glass block
and pane edge.

Nether stem tops: square growth rings like any wood, inside a rim of the stem's
own dark skin, with a small dark pith; no glowing square in the middle.

Glass: a bevelled frame (lit top-left, shaded bottom-right, an inner shadow
line), a set of parallel reflection streaks in the top-left corner and a small
glint bottom-right.  Stained glass keeps the game's see-through levels so it
blends the same way; the pane edges run across, as on the game's panes.
Our own pixel art; vanilla supplies colours, sizes and transparency levels."""
import numpy as np

from .core import N, STATS, Tex, fbm, make_ramp, paint_idx, rng_of, shift, vbase

yy, xx = np.mgrid[0:N, 0:N]
COLORS = ["black", "blue", "brown", "cyan", "gray", "green", "light_blue", "lime", "magenta", "orange",
          "pink", "purple", "red", "silver", "white", "yellow"]


# ------------------------------------------------------------------ nether stem tops
def stem_top(name, skin, flesh, stripped=False):
    """Square growth rings: alternate light and dark flesh rings, each lit on its
    upper-left side; a rim of dark skin (thin and flesh-coloured when stripped)
    with a few notches; a small dark pith in the middle."""
    r = rng_of(name)
    sk = make_ramp(skin, 5, 0.45)
    fl = make_ramp(flesh, 5, 0.32)
    d = np.maximum(np.abs(xx - 7.5), np.abs(yy - 7.5))
    g = fbm(r, ((4, 1.0), (8, 0.5)))
    rgb = np.zeros((N, N, 3), float)
    ri = d.astype(int)                                       # 0 at the middle .. 7 at the edge
    idx = np.where(ri % 2 == 1, 1, 3)                        # dark ring lines between lighter rings
    top_left = ((yy < 7.5) & (np.abs(yy - 7.5) >= np.abs(xx - 7.5))) | ((xx < 7.5) & (np.abs(xx - 7.5) > np.abs(yy - 7.5)))
    idx = np.where((ri % 2 == 0) & top_left, idx + 1, idx)  # light falls on the top and left of each ring
    idx = idx + (g > 0.8) - (g < 0.16)
    rgb[:] = np.array(fl, float)[np.clip(idx, 0, 4)]
    pith = d < 1.0
    rgb[pith] = fl[0]
    rgb[(d < 1.0) & (xx == 7) & (yy == 7)] = fl[1]
    rim = d >= (7.0 if stripped else 6.0)
    notch = (d >= 5.0) & (d < 6.0) & (r.random((N, N)) < 0.18) & (not stripped)
    if stripped:
        rgb[rim] = np.array(fl[1], float)
        rgb[rim & ((xx == 0) | (yy == 0))] = fl[2]
    else:
        k = np.clip(1 + (g > 0.55).astype(int) + ((xx == 0) | (yy == 0)) - ((xx == 15) | (yy == 15)), 0, 4)
        rgb[rim] = np.array(sk, float)[k][rim]
        rgb[notch] = np.array(sk, float)[1]
    t = Tex(np.clip(rgb, 0, 255).astype(np.uint8), 0.5 + 0.1 * (idx - 2) / 2, rough=200, bump=0.9)
    return t


def stems(out):
    for kind, top, strip_top, side in (
            ("crimson", "huge_fungus/crimson_log_top", "huge_fungus/stripped_crimson_stem_top", "huge_fungus/crimson_log_side"),
            ("warped", "huge_fungus/warped_stem_top", "huge_fungus/stripped_warped_stem_top", "huge_fungus/warped_stem_side")):
        skin = shift(vbase(side), dv=-0.04)
        flesh = vbase(strip_top)
        out[top] = stem_top(kind + "_top5", skin, flesh)
        out[strip_top] = stem_top(kind + "_strip_top5", skin, flesh, stripped=True)


# ------------------------------------------------------------------ glass
def alpha_levels(name, clear):
    """(body, streak, frame) see-through levels from the game's own texture"""
    if clear:
        return 0, 255, 255
    a = sorted(STATS.get(name, {}).get("alpha", [110, 160, 200]))
    lo, hi = a[0], a[-1]
    return lo, int((lo + hi) / 2), hi


def glass(name, base, clear=False, glint=None):
    lo, mid, hi = alpha_levels(name, clear)
    fr = [shift(base, dv=-0.16), shift(base, dv=-0.04), shift(base, dv=0.14, ds=-0.18), shift(base, dv=0.26, ds=-0.35)]
    glint = glint or shift(base, dv=0.34, ds=-0.5)
    rgb = np.zeros((N, N, 3), np.uint8)
    rgb[:] = base
    alpha = np.full((N, N), lo, np.uint8)
    frame = (xx == 0) | (yy == 0) | (xx == 15) | (yy == 15)
    rgb[frame] = fr[1]
    rgb[(yy == 0) | (xx == 0)] = fr[2]
    rgb[0, 0] = fr[3]
    rgb[(yy == 15) | (xx == 15)] = fr[0]
    rgb[0, 15] = rgb[15, 0] = fr[1]
    alpha[frame] = hi
    # an inner shadow line along the bottom and right, just inside the frame
    inner = ((yy == 14) & (xx > 0) & (xx < 15)) | ((xx == 14) & (yy > 0) & (yy < 15))
    if not clear:
        rgb[inner] = shift(base, dv=-0.08)
        alpha[inner] = min(255, lo + 30)
    # reflection: one soft two-tone streak in the top-left, a small glint bottom-right
    soft = shift(glint, dv=-0.12, ds=0.1)
    for (x0, y0, ln, col) in ((3, 7, 5, glint), (4, 7, 4, soft), (11, 12, 2, glint)):
        for i in range(ln):
            x, y = x0 + i, y0 - i
            if 0 < x < 15 and 0 < y < 15:
                rgb[y, x] = col
                alpha[y, x] = 255 if clear else (mid if col == glint else int((lo + mid) / 2))
    rgb[1, 1] = fr[3]                                        # corner catch-light
    alpha[1, 1] = hi if not clear else 255
    hgt = np.where(frame, 0.7, 0.5)
    return Tex(rgb, hgt, alpha=alpha, rough=10, bump=0.4)


def pane_edge(name, base):
    """The thin edge of a pane: bands running across, a lighter band near the top
    and the bottom, a darker one a little above the bottom."""
    lo, mid, hi = alpha_levels(name, False) if name in STATS and min(STATS[name].get("alpha", [255])) < 255 else (255, 255, 255)
    clear = name == "glass_pane_top"
    ramp = make_ramp(base, 5, 0.22 if clear else 0.08)
    band = np.array([3, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 3, 3, 1, 2, 2])
    idx = np.repeat(band[:, None], N, axis=1) + ((xx % 2 == 0) if clear else 0)   # fine ribs on clear panes
    g = rng_of(name).random((N, N))
    idx = idx + ((g > 0.94) & (idx < 4))
    t = Tex(paint_idx(idx, ramp), None, alpha=np.full((N, N), hi, np.uint8), rough=20, bump=0.3)
    return t


def glasses(out):
    out["glass"] = glass("glass", (176, 214, 222), clear=True, glint=(250, 254, 255))
    out["glass_pane_top"] = pane_edge("glass_pane_top", vbase("glass_pane_top"))
    for c in COLORS:
        out[f"glass_{c}"] = glass(f"glass_{c}", vbase(f"glass_{c}"))
        out[f"glass_pane_top_{c}"] = pane_edge(f"glass_pane_top_{c}", vbase(f"glass_pane_top_{c}"))
    tb = vbase("tinted_glass")
    out["tinted_glass"] = glass("tinted_glass", tb, glint=shift(tb, dv=0.22))


def build(out, flip, variations):
    stems(out)
    glasses(out)
