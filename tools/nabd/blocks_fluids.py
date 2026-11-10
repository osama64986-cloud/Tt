"""Lava: flat cartoon bands of heat that drift and bubble (seamless loops)."""
import numpy as np

from .core import STATS, Tex, fbm, paint_idx, rng_of, stack_frames

HEAT = [(176, 40, 8), (222, 78, 10), (246, 126, 18), (255, 178, 44), (255, 230, 120)]
CUTS = (0.30, 0.50, 0.68, 0.85)


def tones(field):
    return sum((field > c).astype(int) for c in CUTS)


def frame(idx):
    t = Tex(paint_idx(idx, HEAT), 0.3 + idx * 0.15, rough=200, bump=0.7)
    t.emis = 170 + idx * 21                       # everything glows, the hot bands most
    return t


def build(out, flip, variations):
    # ---- still lava: two slow swirls passing through each other
    w, h = STATS["lava_still"]["size"]
    n = h // w
    r = rng_of("lava_still")
    a = fbm(r, ((2, 1.0), (3, 0.6)), w=w, h=w)
    b = fbm(r, ((3, 1.0), (4, 0.5)), w=w, h=w)
    bubbles = [(int(r.integers(2, w - 2)), int(r.integers(2, w - 2)), int(r.integers(n))) for _ in range(4)]
    yy, xx = np.mgrid[0:w, 0:w]
    fr = []
    for f in range(n):
        ph = f / n
        fld = 0.5 + 0.27 * np.sin(2 * np.pi * (a + ph)) + 0.23 * np.sin(2 * np.pi * (b * 2 - ph))
        idx = tones(fld)
        for (bx, by, start) in bubbles:                  # a bubble swells for six frames, then pops
            age = (f - start) % n
            if age < 6:
                d = np.hypot(xx - bx, yy - by)
                rad = 0.6 + age * 0.35
                idx = np.where(d <= rad, 3, idx)
                idx = np.where(np.abs(d - rad) < 0.55, 4, idx)
        fr.append(frame(idx))
    out["lava_still"] = stack_frames(fr)
    out["lava_placeholder"] = fr[0]

    # ---- flowing lava: long streaks sliding down, one full wrap per loop
    w, h = STATS["lava_flow"]["size"]
    n = h // w
    r = rng_of("lava_flow")
    a = fbm(r, ((2, 1.0), (4, 0.6)), w=w, h=w, sy=2.5)
    b = fbm(r, ((4, 1.0), (6, 0.5)), w=w, h=w, sy=2.5)
    base = 0.5 + 0.27 * np.sin(2 * np.pi * a) + 0.23 * np.sin(2 * np.pi * b * 2)
    fr = [frame(tones(np.roll(base, f * (w // n), axis=0))) for f in range(n)]
    out["lava_flow"] = stack_frames(fr)


# ------------------------------------------------------------------- water
def water(name, grey):
    """Gentle cartoon ripples: three close tones drifting in a seamless loop.
    Brightness and alpha match what the game expects so biome tinting and
    transparency behave exactly as before."""
    st = STATS[name]
    w, h = st["size"]
    n = h // w
    lo, mid, hi = (st["ramp"][0], st["ramp"][2], st["ramp"][4])
    ramp = [tuple(lo), tuple(mid), tuple(hi)]
    alpha = st["alpha"][0]
    r = rng_of("water:" + str(w))
    flow = "flow" in name
    a = fbm(r, ((2, 1.0), (4, 0.6)), w=w, h=w, sy=2.0 if flow else 1.0, sx=1.0 if flow else 2.0)
    b = fbm(r, ((3, 1.0), (5, 0.5)), w=w, h=w, sy=2.0 if flow else 1.0, sx=1.0 if flow else 2.0)
    base = 0.5 + 0.27 * np.sin(2 * np.pi * a) + 0.23 * np.sin(2 * np.pi * b * 2)
    fr = []
    for f in range(n):
        if flow:
            fld = np.roll(base, int(round(f * w / n)), axis=0)
        else:
            ph = f / n
            fld = 0.5 + 0.27 * np.sin(2 * np.pi * (a + ph)) + 0.23 * np.sin(2 * np.pi * (b * 2 - ph))
        idx = np.where(fld > 0.72, 2, np.where(fld < 0.3, 0, 1))
        t = Tex(paint_idx(idx, ramp), 0.4 + idx * 0.1, alpha=np.full((w, w), alpha, np.uint8), rough=20, bump=0.4)
        fr.append(t)
    return stack_frames(fr) if n > 1 else fr[0]


_lava_build = build


def build(out, flip, variations):          # noqa: F811  (lava first, then water)
    _lava_build(out, flip, variations)
    for name in ("water_still_grey", "water_flow_grey", "water_still", "water_flow", "cauldron_water"):
        if name in STATS:
            out[name] = water(name, "grey" in name or "cauldron" in name)
    for name, src in (("water_placeholder", "water_still"), ("cauldron_water_placeholder", "cauldron_water")):
        if name in STATS and src in out:
            t = out[src]
            ph = Tex(t.rgb[:16].copy(), t.height[:16].copy(), alpha=np.full((16, 16), STATS[name]["alpha"][0], np.uint8), rough=20, bump=0.4)
            out[name] = ph
