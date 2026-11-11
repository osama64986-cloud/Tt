"""Everything that was still missing: utility block faces, model-bound parts
(painted inside each model's layout mask), torches, lanterns, candles, cake,
fire, portal, and our own sea / cave sprites."""
import numpy as np

from . import painters as P
from .blocks_plants import Sprite, flower
from .blocks_village import IRON, DARK_IRON, frame_panel
from .core import (N, STATS, Tex, fbm, make_ramp, mix, paint, paint_idx, plane, rng_of, shift, stack_frames, vbase,
                   vramp)

yy, xx = np.mgrid[0:N, 0:N]
WARM = [(255, 150, 40), (255, 200, 70), (255, 240, 160)]
COOL = [(40, 170, 190), (110, 230, 240), (220, 255, 255)]
GREEN = [(60, 190, 120), (130, 240, 170), (226, 255, 236)]
RED = [(170, 20, 16), (255, 60, 40), (255, 170, 150)]


def frames_of(name):
    w, h = STATS[name]["size"]
    return max(1, h // w)


def mask_of(name):
    return np.array([[c == "1" for c in row] for row in STATS[name]["mask"]])


def shade_mask(m, fh=None):
    """Tone index per pixel from the silhouette alone: lit on top/left edges,
    shaded on bottom/right edges, flat inside.  fh = frame height for strips."""
    h, w = m.shape
    fh = fh or h
    idx = np.full((h, w), 2)
    for y0 in range(0, h, fh):
        mm = np.pad(m[y0:y0 + fh], 1)
        up, lf = ~mm[:-2, 1:-1], ~mm[1:-1, :-2]
        dn, rt = ~mm[2:, 1:-1], ~mm[1:-1, 2:]
        part = np.full((fh, w), 2)
        part = np.where(up | lf, 3, part)
        part = np.where(dn | rt, 1, part)
        part = np.where((up | lf) & (dn | rt), 2, part)
        part = np.where(up & lf, 4, part)
        part = np.where(dn & rt, 0, part)
        idx[y0:y0 + fh] = part
    return idx


def shaded(name, ramp=None, rough=190, metal=0, contrast=0.4, sss=0):
    """Paint a model-bound texture inside its layout mask."""
    m = mask_of(name)
    h, w = m.shape
    ramp = ramp or vramp(name, 5, contrast=contrast)
    idx = shade_mask(m, w if h > w and h % w == 0 else None)
    t = Tex(np.where(m[..., None], paint_idx(idx, ramp), 0).astype(np.uint8), np.where(m, 0.4 + idx * 0.12, 0.0),
            alpha=np.where(m, 255, 0).astype(np.uint8), rough=rough, metal=metal, sss=sss, bump=1.0)
    t.mask, t.idx = m, idx
    return t


def face(name, ramp=None, inset=None, border=1, rough=170, contrast=0.36, metal=0):
    return P.slab_face(name, ramp or vramp(name, 5, contrast=contrast), border=border, inset=inset, vary=0.14, rough=rough) \
        if not metal else _metal(P.slab_face(name, ramp or vramp(name, 5, contrast=contrast), border=border, inset=inset, vary=0.14, rough=rough), metal)


def _metal(t, metal):
    t.metal = metal
    return t


def dot(t, x0, y0, x1, y1, cols, emis=220):
    """Glowing indicator: cols = (dark, mid, light)."""
    t.rgb[y0:y1 + 1, x0:x1 + 1] = cols[1]
    t.rgb[y0, x0] = cols[2]
    e = plane(t.emis, t.h, t.w)
    e[y0:y1 + 1, x0:x1 + 1] = emis
    t.emis = e


def strip(name, make):
    """make(frame, n) -> Tex; stacked to the frame count the game expects."""
    n = frames_of(name)
    return stack_frames([make(f, n) for f in range(n)])


def flame(seed, cols, w=N, h=N, n=32, base=3, tall=11, soft=False):
    """Cartoon flames: tongues that sway and lick in a seamless loop."""
    r = rng_of(seed)
    ph = r.random(4) * 6.28
    frames = []
    for f in range(n):
        t = f / n * 2 * np.pi
        rgb = np.zeros((h, w, 3), np.uint8)
        alpha = np.zeros((h, w), np.uint8)
        emis = np.zeros((h, w))
        for x in range(w):
            u = x / w * 2 * np.pi
            edge = np.sin(u / 2) ** 0.6                                   # lower at the sides
            top = base + tall * edge * (0.62 + 0.2 * np.sin(u * 2 + t + ph[0]) + 0.18 * np.sin(u * 3 - 2 * t + ph[1]))
            top = max(1.0, top)
            for k in range(int(round(top))):
                y = h - 1 - k
                if y < 0:
                    break
                rel = k / top
                tone = 2 if rel < 0.3 else (1 if rel < 0.62 else 0)
                if tone == 2 and edge < 0.55:
                    tone = 1
                rgb[y, x] = cols[tone]
                alpha[y, x] = 255
                emis[y, x] = 255 if not soft else 200
        tx = Tex(rgb, alpha / 255.0 * 0.5, alpha=alpha, rough=255, bump=0.2)
        tx.emis = emis
        frames.append(tx)
    return frames


def build(out, flip, variations):
    def put(name, tex):
        if name in STATS and tex is not None:
            out[name] = tex

    oak = vramp("planks_oak", 5, contrast=0.26)
    stone = vramp("stone_slab_top", 5, contrast=0.3)

    # ================================================== A. opaque utility faces
    put("anvil_base", face("anvil_base", DARK_IRON, metal=220, rough=90))
    for nm in ("cauldron_inner", "cauldron_side", "hopper_inside", "hopper_outside"):
        t = face(nm, DARK_IRON, metal=210, rough=100)
        if nm.endswith("side") or nm.endswith("outside"):
            for x in (3, 12):
                t.rgb[2, x] = IRON[4]
                t.rgb[13, x] = IRON[4]
        put(nm, t)
    put("brewing_stand_base", P.cells("brewing_stand_base", vramp("cobblestone", 6, contrast=0.36), 8))
    for nm in ("lectern_base", "lectern_sides", "lectern_front", "lectern_top"):
        t = P.planks(nm, oak, boards=4, nails=False, vertical=nm != "lectern_top")
        frame_panel(t, oak, 0, 0, 15, 15, sunk=False)
        if nm == "lectern_front":
            t.rgb[4:12, 3:13] = (60, 40, 26)
            for y, c in ((5, (180, 50, 44)), (7, (50, 100, 180)), (9, (56, 150, 76))):
                t.rgb[y:y + 2, 4:12] = c
                t.rgb[y, 4] = (240, 236, 220)
        put(nm, t)
    for pre, ramp, lock in (("", vramp("planks_oak", 5, contrast=0.28), (250, 214, 90)),
                            ("copper_", vramp("copper_block", 5, contrast=0.3), (255, 236, 200)),
                            ("exposed_copper_", vramp("exposed_copper", 5, contrast=0.3), (255, 236, 200)),
                            ("weathered_copper_", vramp("weathered_copper", 5, contrast=0.3), (255, 236, 200)),
                            ("oxidized_copper_", vramp("oxidized_copper", 5, contrast=0.3), (255, 236, 200))):
        names = ("chest_front", "chest_side", "chest_top") if pre == "" else tuple(pre + f"chest_inventory_{p}" for p in ("front", "side", "top"))
        for nm, part in zip(names, ("front", "side", "top")):
            t = P.planks("chest_" + part, ramp, boards=4, nails=False) if pre == "" else face(nm, ramp, metal=200, rough=90)
            frame_panel(t, DARK_IRON if pre == "" else ramp, 0, 0, 15, 15, sunk=False)
            if part != "top":
                t.rgb[5] = ramp[0]
                t.rgb[6] = ramp[4]
                t.height[5] = 0.1
            if part == "front":
                t.rgb[4:8, 7:9] = lock
                t.rgb[7, 7:9] = shift(lock, dv=-0.3)
                t.height[4:8, 7:9] = 1.0
            put(nm, t)
    if "trapped_chest_front" in STATS and "chest_front" in out:
        t = out["chest_front"].copy()
        t.rgb[4:8, 7:9] = (220, 50, 40)
        t.rgb[7, 7:9] = (140, 20, 16)
        out["trapped_chest_front"] = t
    # stonecutter
    for nm in ("stonecutter_bottom", "stonecutter2_bottom", "stonecutter_other_side", "stonecutter_side", "stonecutter2_side"):
        if nm in STATS and 0 not in STATS[nm]["alpha"]:
            put(nm, P.bricks(nm, stone, [(70, 70, 74), (82, 82, 86)], rows=2, cols=1))
    for nm in ("stonecutter_top", "stonecutter2_top"):
        t = face(nm, stone, inset=None)
        t.rgb[7:9, 1:15] = (26, 24, 24)
        t.rgb[6, 1:15] = stone[0]
        t.height[7:9, 1:15] = 0.0
        put(nm, t)
    # crafter
    cr = vramp("crafter_bottom", 5, contrast=0.36) if "crafter_bottom" in STATS else stone
    for nm in [k for k in STATS if k.startswith("crafter_")]:
        t = face(nm, vramp(nm, 5, contrast=0.36))
        if "top" in nm:
            for gx in (2, 6, 10):
                for gy in (2, 6, 10):
                    frame_panel(t, cr, gx, gy, gx + 3, gy + 3)
                    t.rgb[gy + 1:gy + 3, gx + 1:gx + 3] = (40, 36, 34)
        elif nm != "crafter_bottom":
            frame_panel(t, cr, 4, 4, 11, 11)
            t.rgb[5:11, 5:11] = (34, 30, 30)
        if "crafting" in nm or "triggered" in nm:
            dot(t, 7, 7, 8, 8, RED if "triggered" in nm else WARM)
        put(nm, t)
    # creaking heart
    for nm in [k for k in STATS if k.startswith("creaking_heart_")]:
        r = vramp(nm, 5, contrast=0.4)
        t = P.log_top(nm, r, r) if "_top_" in nm else P.bark(nm, r, ridges=7)
        if "inactive" not in nm:
            lit = "active" in nm and "dormant" not in nm
            cols = WARM if lit else [(120, 70, 40), (160, 96, 50), (200, 130, 70)]
            for (x, y) in ((4, 4), (10, 8), (6, 12)) if "_side_" in nm else ((7, 7),):
                dot(t, x, y, x + 1, y + 1, cols, emis=230 if lit else 60)
        put(nm, t)
    # sculk devices (opaque faces)
    sk = make_ramp((16, 40, 50), 5, 0.6)
    glow = [(20, 110, 130), (60, 200, 220), (190, 250, 250)]
    for nm in ("sculk_catalyst_bottom", "sculk_catalyst_side", "sculk_catalyst_top", "sculk_sensor_bottom", "sculk_sensor_top",
               "sculk_shrieker_bottom", "calibrated_sculk_sensor_top"):
        if nm in STATS:
            t = P.rock(nm, sk, "grain", cracks=0, rough=120)
            frame_panel(t, sk, 0, 0, 15, 15, sunk=False)
            r = rng_of(nm)
            for _ in range(5):
                x, y = int(r.integers(2, 13)), int(r.integers(2, 13))
                dot(t, x, y, x, y, glow, emis=180)
            if nm.endswith("_top") and "catalyst" in nm:
                t.rgb[5:11, 5:11] = (232, 226, 206)
                frame_panel(t, [(150, 144, 128)] * 2 + [(200, 194, 176)] * 3, 5, 5, 10, 10)
            out[nm] = t
    for nm in ("sculk_catalyst_side_bloom", "sculk_catalyst_top_bloom", "sculk_shrieker_inner_top", "sculk_shrieker_can_summon_inner_top"):
        if nm in STATS:
            src = "sculk_catalyst_top" if "top" in nm and "catalyst" in nm else "sculk_catalyst_side"

            def mk(f, n, src=src, nm=nm):
                t = out[src].copy() if "catalyst" in nm else P.rock("shrieker_inner", sk, "grain", cracks=0, rough=120)
                rad = 1 + (f % max(1, n)) * 6.0 / max(1, n)
                ring = np.abs(np.hypot(xx - 7.5, yy - 7.5) - rad) < 0.8
                t.rgb = np.where(ring[..., None], np.array(glow[1], np.uint8), t.rgb)
                t.emis = np.where(ring, 230, plane(t.emis))
                return t
            out[nm] = strip(nm, mk)
    # trial chambers
    tc = make_ramp((70, 84, 100), 5, 0.4)
    for nm in [k for k in STATS if (k.startswith("trial_spawner_top") or k.startswith("vault_top") or k.startswith("vault_bottom"))]:
        t = face(nm, tc, inset=3, metal=120, rough=110)
        om = "ominous" in nm
        if any(w in nm for w in ("active", "ejecting", "open")) and "inactive" not in nm:
            dot(t, 6, 6, 9, 9, [(30, 90, 150), (70, 180, 255), (220, 245, 255)] if om else WARM)
        else:
            t.rgb[6:10, 6:10] = (24, 28, 34)
        put(nm, t)
    # redstone slabs
    for nm, on in (("repeater_off", False), ("repeater_on", True), ("comparator_off", False), ("comparator_on", True)):
        t = face(nm, stone)
        col = RED[1] if on else RED[0]
        t.rgb[3:13, 7:9] = col
        if "comparator" in nm:
            t.rgb[11:13, 3:13] = col
        e = np.zeros((N, N))
        if on:
            e[3:13, 7:9] = 200
        t.emis = e
        put(nm, t)
    for nm, base in (("itemframe_background", (150, 110, 70)), ("glow_item_frame", (170, 150, 90))):
        if nm in STATS:
            t = P.flat(nm, make_ramp(base, 5, 0.3), "clay", rough=220, amount=0.5)
            frame_panel(t, oak, 0, 0, 15, 15, sunk=False)
            if nm.startswith("glow"):
                t.emis = 60
            out[nm] = t
    for nm in ("bed_feet_top", "bed_head_top"):
        if nm in STATS:
            t = P.wool(nm, make_ramp((190, 40, 40), 5, 0.3))
            if nm == "bed_head_top":
                t.rgb[1:6, 2:14] = (240, 238, 232)
                t.rgb[5, 2:14] = (200, 198, 194)
            out[nm] = t
    # creative-only machines: one plate design, colour and a status light per kind
    for pre, base in (("command_block", (214, 140, 90)), ("repeating_command_block", (150, 110, 214)),
                      ("chain_command_block", (110, 190, 150))):
        r = make_ramp(base, 5, 0.34)
        for part in ("back", "conditional", "front", "side"):
            for suffix in ("", "_mipmap"):
                nm = f"{pre}_{part}{suffix}"
                if nm not in STATS:
                    continue

                def mk(f, n, part=part, r=r):
                    t = face("cmd_" + part, r, inset=3, metal=140, rough=90)
                    if part in ("side", "conditional"):                   # arrow pointing down the chain
                        for i in range(4):
                            t.rgb[6 + i, 7 - (3 - i):9 + (3 - i)] = r[0]
                    lit = [(255, 240, 200), (255, 190, 90), (200, 120, 40), (255, 190, 90)][f % 4]
                    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
                        t.rgb[y, x] = lit
                    if part == "front":
                        t.rgb[6:10, 6:10] = (30, 30, 34)
                    if part == "conditional":
                        t.rgb[2:4, 6:10] = (40, 40, 44)
                    return t
                out[nm] = strip(nm, mk)
        if pre == "command_block" and "command_block" in STATS:
            out["command_block"] = face("cmd_side", r, inset=3, metal=140, rough=90)
    for nm in [k for k in STATS if k.startswith("structure_block") or k.startswith("jigsaw_")]:
        r = make_ramp((120, 96, 130) if nm.startswith("structure") else (90, 80, 100), 5, 0.36)
        t = face(nm, r, inset=4 if "corner" not in nm else 2, metal=100, rough=110)
        dot(t, 7, 7, 8, 8, COOL if nm.startswith("structure") else [(120, 60, 160), (190, 120, 240), (240, 220, 255)], emis=120)
        out[nm] = t

    # ====================================== B. model-bound parts, painted in layout
    for nm in ("anvil_top_damaged_0", "anvil_top_damaged_1", "anvil_top_damaged_2"):
        if nm in STATS:
            t = shaded(nm, DARK_IRON, metal=220, rough=90)
            r = rng_of("anvil_dents")
            for _ in range(int(nm[-1]) * 4):
                x, y = int(r.integers(4, 12)), int(r.integers(1, 14))
                if t.mask[y, x] and t.mask[y, x + 1]:
                    t.rgb[y, x] = DARK_IRON[0]
                    t.rgb[y, x + 1] = DARK_IRON[4]
            out[nm] = t
    simple = {
        "bell_bottom": dict(ramp=make_ramp((240, 196, 60), 5, 0.4), metal=220, rough=60),
        "bell_side": dict(ramp=make_ramp((240, 196, 60), 5, 0.4), metal=220, rough=60),
        "bell_top": dict(ramp=make_ramp((240, 196, 60), 5, 0.4), metal=220, rough=60),
        "cauldron_bottom": dict(ramp=DARK_IRON, metal=210, rough=100), "cauldron_top": dict(ramp=DARK_IRON, metal=210, rough=100),
        "hopper_top": dict(ramp=DARK_IRON, metal=210, rough=100),
        "grindstone_pivot": dict(ramp=oak), "grindstone_round": dict(ramp=stone), "grindstone_side": dict(ramp=stone),
        "chain1": dict(ramp=DARK_IRON, metal=220, rough=90), "chain2": dict(ramp=DARK_IRON, metal=220, rough=90),
        "lever": dict(ramp=oak), "flower_pot": dict(),
        "trip_wire": dict(), "trip_wire_source": dict(), "heavy_core": dict(metal=200, rough=80),
        "sea_pickle": dict(sss=80), "compost": dict(), "compost_ready": dict(),
        "decorated_pot_side": dict(), "decorated_pot_base": dict(),
        "bed_feet_end": dict(ramp=oak), "bed_feet_side": dict(ramp=oak), "bed_head_end": dict(ramp=oak), "bed_head_side": dict(ramp=oak),
        "cocoa_stage_0": dict(sss=40), "cocoa_stage_1": dict(sss=40), "cocoa_stage_2": dict(sss=40),
        "sculk_sensor_side": dict(ramp=sk), "sculk_shrieker_side": dict(ramp=sk), "sculk_shrieker_top": dict(ramp=make_ramp((220, 214, 196), 5, 0.3)),
        "calibrated_sculk_sensor_input_side": dict(ramp=sk), "calibrated_sculk_sensor_amethyst": dict(ramp=make_ramp((150, 100, 220), 5, 0.4)),
        "conduit_base": dict(), "conduit_cage": dict(), "conduit_closed": dict(), "conduit_open": dict(),
    }
    for nm in ("scaffolding_bottom", "scaffolding_side", "scaffolding_top"):
        simple[nm] = dict(ramp=vramp("bamboo_planks", 5, contrast=0.3) if "bamboo_planks" in STATS else oak)
    for pre in ("copper_", "exposed_copper_", "weathered_copper_", "oxidized_copper_"):
        cr_ = vramp("copper_block" if pre == "copper_" else pre[:-1], 5, contrast=0.3)
        simple[pre + "chain1"] = dict(ramp=cr_, metal=200, rough=100)
        simple[pre + "chain2"] = dict(ramp=cr_, metal=200, rough=100)
    for nm in ("lightning_rod", "lightning_rod_powered", "exposed_lightning_rod", "weathered_lightning_rod", "oxidized_lightning_rod"):
        simple[nm] = dict(metal=200, rough=100)
    for nm in [k for k in STATS if k.startswith(("vault_front", "vault_side", "trial_spawner_side", "trial_spawner_bottom"))]:
        simple[nm] = dict(ramp=tc, metal=120, rough=110)
    for nm in [k for k in STATS if k.startswith(("turtle_egg_", "sniffer_egg_"))]:
        simple[nm] = dict(rough=120)
    for nm, kw in simple.items():
        if nm in STATS and "mask" in STATS[nm]:
            t = shaded(nm, **kw)
            if nm == "lightning_rod_powered":
                t.emis = np.where(t.mask, 160, 0)
            if "cracked" in nm and "not_cracked" not in nm:            # eggs: hairline cracks
                r = rng_of("egg_cracks")
                ramp = kw.get("ramp") or vramp(nm, 5, contrast=0.4)
                for _ in range(6 if "very" in nm else 3):
                    x, y = int(r.integers(1, t.w - 1)), int(r.integers(1, t.h - 1))
                    for i in range(3):
                        if t.mask[(y + i) % t.h, x]:
                            t.rgb[(y + i) % t.h, x] = ramp[0]
            if ("_on" in nm or "active" in nm or "ejecting" in nm) and nm.startswith(("vault", "trial")) and "inactive" not in nm:
                cols = [(30, 90, 150), (70, 180, 255), (220, 245, 255)] if "ominous" in nm else WARM
                core = t.mask & (np.abs(xx - 7.5) < 2) & (np.abs(yy - 7.5) < 2) if t.rgb.shape[:2] == (N, N) else None
                if core is not None:
                    t.rgb = np.where(core[..., None], np.array(cols[1], np.uint8), t.rgb)
                    t.emis = np.where(core, 220, 0)
            out[nm] = t
    if "brewing_stand" in STATS:                       # blaze rod in the middle, stone arms either side
        t = shaded("brewing_stand", make_ramp((120, 122, 132), 5, 0.44), rough=160)
        rod = t.mask & ((xx == 7) | (xx == 8))
        rodr = make_ramp((250, 196, 50), 5, 0.36)
        t.rgb = np.where(rod[..., None], np.where((xx == 7)[..., None], np.array(rodr[4], np.uint8), np.array(rodr[2], np.uint8)), t.rgb)
        ring = rod & (yy % 4 == 1)                      # darker bands down the rod
        t.rgb = np.where(ring[..., None], np.array(rodr[1], np.uint8), t.rgb)
        t.emis = np.where(rod, 210, 0)
        out["brewing_stand"] = t
    for nm in ("redstone_dust_cross", "redstone_dust_line"):             # tinted by signal strength in game
        if nm in STATS:
            out[nm] = shaded(nm, vramp(nm, 5, grey=True, contrast=0.3))
    for nm in ("sculk_sensor_tendril_active", "sculk_sensor_tendril_inactive", "sculk_vein"):
        if nm in STATS and "mask" in STATS[nm]:
            t = shaded(nm, make_ramp((30, 150, 170), 5, 0.5))
            t.emis = np.where(t.mask, 200 if "inactive" not in nm else 60, 0)
            out[nm] = t

    # torches: a wooden stick with a head that tells them apart
    for nm, head, stick, lit in (("torch_on", WARM, oak, True), ("soul_torch", COOL, oak, True),
                                 ("redstone_torch_on", RED, oak, True), ("redstone_torch_off", [(70, 14, 12), (104, 22, 18), (140, 40, 34)], oak, False),
                                 ("copper_torch", GREEN, vramp("copper_block", 5, contrast=0.3), True)):
        if nm in STATS and "mask" in STATS[nm]:
            t = shaded(nm, stick)
            ys = np.where(t.mask.any(1))[0]
            top = ys.min()
            e = np.zeros((t.h, t.w))
            for k in range(3):
                row = t.mask[top + k]
                cols = np.where(row)[0]
                for j, x in enumerate(cols):
                    t.rgb[top + k, x] = head[2 - k] if j == 0 else head[max(0, 1 - k)]
                    e[top + k, x] = 240 if lit else 0
            if top + 3 < t.h:
                t.rgb[top + 3] = np.where(t.mask[top + 3][:, None], np.array((40, 30, 24), np.uint8), t.rgb[top + 3])
            t.emis = e
            out[nm] = t
    # lanterns: dark frame, glowing glass that flickers over the frames
    for nm, glass, frame_r in [("lantern", WARM, DARK_IRON), ("soul_lantern", COOL, DARK_IRON)] + \
            [(p + "copper_lantern", GREEN, vramp("copper_block" if p == "" else p + "copper", 5, contrast=0.3)) for p in ("", "exposed_", "weathered_", "oxidized_")]:
        if nm in STATS and "mask" in STATS[nm]:
            t = shaded(nm, frame_r, metal=200, rough=100)
            fh = t.w
            body = t.mask & (xx[:1].repeat(t.h, 0) < 6) if t.w == N else t.mask
            inner = body & (t.idx == 2)
            e = np.zeros((t.h, t.w))
            for f in range(t.h // fh):
                sl = slice(f * fh, (f + 1) * fh)
                lvl = [1, 2, 1, 0][f % 4]
                t.rgb[sl] = np.where(inner[sl][..., None], np.array(glass[lvl], np.uint8), t.rgb[sl])
                e[sl] = np.where(inner[sl], 210 + 15 * lvl, 0)
            t.emis = e
            out[nm] = t
    # candles
    for nm in [k for k in STATS if k.startswith("candles/")]:
        if "mask" not in STATS[nm]:
            continue
        t = shaded(nm, vramp(nm, 5, contrast=0.3), rough=120, sss=120)
        ys = np.where(t.mask.any(1))[0]
        top = ys.min()
        x = int(np.where(t.mask[top])[0][0])
        if nm.endswith("_lit"):
            t.rgb[top, x] = WARM[2]
            t.emis = np.where((yy == top) & (xx == x), 255, 0)
        else:
            t.rgb[top, x] = (40, 34, 30)
        out[nm] = t
    # cake
    if "cake_top" in STATS:
        icing = make_ramp((250, 240, 236), 5, 0.1)
        sponge = make_ramp((176, 112, 64), 5, 0.3)
        t = shaded("cake_top", icing, rough=120)
        for (x, y) in ((4, 4), (11, 4), (7, 8), (4, 11), (11, 11)):
            t.rgb[y, x] = (214, 40, 46)
            t.rgb[y, x + 1] = (150, 20, 30)
        out["cake_top"] = t
        for nm in ("cake_side", "cake_inner"):
            t = shaded(nm, sponge, rough=200)
            ys = np.where(t.mask.any(1))[0]
            top = ys.min()
            for k, c in enumerate((icing[4], icing[2], icing[1])):
                t.rgb[top + k] = np.where(t.mask[top + k][:, None], np.array(c, np.uint8), t.rgb[top + k])
            drip = t.mask[top + 3] & (xx[0] % 4 == 1)
            t.rgb[top + 3] = np.where(drip[:, None], np.array(icing[2], np.uint8), t.rgb[top + 3])
            mid = top + 5
            if mid < N:
                t.rgb[mid] = np.where(t.mask[mid][:, None], np.array((200, 50, 60), np.uint8), t.rgb[mid])
            out[nm] = t
        out["cake_bottom"] = shaded("cake_bottom", sponge, rough=200)

    # ============================================== C. fire, campfire, portal
    for nm, cols, seed in (("fire_0", [RED[1], WARM[1], WARM[2]], "fire0"), ("fire_1", [RED[1], WARM[1], WARM[2]], "fire1"),
                           ("soul_fire_0", [(20, 110, 150), COOL[1], COOL[2]], "sfire0"), ("soul_fire_1", [(20, 110, 150), COOL[1], COOL[2]], "sfire1")):
        if nm in STATS:
            fr = flame(seed, cols, n=frames_of(nm), tall=12)
            out[nm] = stack_frames(fr)
            put(nm + "_placeholder", fr[0])
    for nm, cols in (("campfire", [RED[1], WARM[1], WARM[2]]), ("soul_campfire", [(20, 110, 150), COOL[1], COOL[2]])):
        if nm in STATS:
            out[nm] = stack_frames(flame(nm, cols, n=frames_of(nm), tall=11))
    if "campfire_log" in STATS:
        log = shaded("campfire_log", vramp("log_oak", 5, contrast=0.4), rough=220)
        out["campfire_log"] = log
        for nm, cols in (("campfire_log_lit", WARM), ("soul_campfire_log_lit", COOL)):
            if nm in STATS:
                def mk(f, n, cols=cols):
                    t = P.bark("campfire_lit", vramp("log_oak", 5, contrast=0.4), ridges=6)
                    r = rng_of("embers")
                    e = np.zeros((N, N))
                    for i in range(7):
                        x, y = int(r.integers(N)), int(r.integers(N))
                        lvl = [0, 1, 2, 1][(f + i) % 4]
                        t.rgb[y, x] = cols[lvl]
                        t.rgb[y, (x + 1) % N] = cols[max(0, lvl - 1)]
                        e[y, x] = e[y, (x + 1) % N] = 180 + 25 * lvl
                    t.emis = e
                    return t
                out[nm] = strip(nm, mk)
    if "portal" in STATS:
        swirl = make_ramp((130, 50, 230), 5, 0.6)
        a_lo = STATS["portal"]["alpha"][0]
        r = rng_of("portal_swirl")
        f1, f2 = fbm(r, ((2, 1.0), (4, 0.6))), fbm(r, ((3, 1.0), (5, 0.5)))
        n = frames_of("portal")
        fr = []
        for f in range(n):
            ph = f / n * 2 * np.pi
            tone = np.clip(0.5 + 0.3 * np.sin(f1 * 6.28 + ph) + 0.2 * np.sin(f2 * 6.28 - 2 * ph), 0, 0.999)
            t = Tex(paint(tone, swirl), 0.4 + tone * 0.3, alpha=np.full((N, N), a_lo, np.uint8), rough=30, bump=0.5)
            t.emis = 150 + tone * 100
            fr.append(t)
        out["portal"] = stack_frames(fr)
        if "portal_placeholder" in STATS:
            ph_ = fr[0].copy()
            ph_.alpha[:] = STATS["portal_placeholder"]["alpha"][0]
            out["portal_placeholder"] = ph_

    # ================================================ D. our own sea & cave sprites
    def coral(name, fan):
        ramp = vramp(name, 5, contrast=0.44)
        s = Sprite()
        r = rng_of("coral:" + name.replace("_dead", "") + str(fan))
        def grow(x, y, ang, ln, depth):
            for i in range(ln):
                x += np.cos(ang)
                y -= np.sin(ang)
                s.px(x, y, ramp[3 if depth else 2], 0.7)
                s.px(x + 1, y, ramp[1], 0.6)
            s.px(x, y - 1, ramp[4], 0.9)
            if depth < 2:
                for da in (-0.6, 0.6) if fan else (-0.5, 0.2, 0.7):
                    if r.random() < 0.85:
                        grow(x, y, ang + da + (r.random() - 0.5) * 0.3, max(2, ln - 1 - int(r.integers(0, 2))), depth + 1)
        if fan:
            for a in (0.6, 1.1, 1.57, 2.05, 2.55):
                grow(7.5, 15, a, 5, 0)
        else:
            for x0 in (5, 8, 11):
                grow(x0, 15, 1.57 + (r.random() - 0.5) * 0.4, 4, 0)
        return s.tex(sss=60)
    for c in ("blue", "pink", "purple", "red", "yellow"):
        for dead in ("", "_dead"):
            put(f"coral_fan_{c}{dead}", coral(f"coral_fan_{c}{dead}", True) if f"coral_fan_{c}{dead}" in STATS else None)
            put(f"coral_plant_{c}{dead}", coral(f"coral_plant_{c}{dead}", False) if f"coral_plant_{c}{dead}" in STATS else None)

    def ribbon(name, kind, phase):
        ramp = vramp("kelp_a", 5, contrast=0.44)
        def mk(f, n):
            s = Sprite()
            for y in range(N):
                if kind != "body" and y < 3:
                    continue
                cx = 7.5 + 2.0 * np.sin(2 * np.pi * (y / N + f / n) + phase)
                half = 2.2 if kind == "body" else max(0.6, 2.2 * (y - 2) / 8) if y < 10 else 2.2
                for x in range(N):
                    d = x - cx
                    if abs(d) <= half:
                        tone = 4 if abs(d) < 0.6 else (3 if d < 0 else 1)
                        s.px(x, y, ramp[tone if (y + int(phase * 3)) % 4 else 2], 0.6)
            if kind == "bulb":
                cx = 7.5 + 2.0 * np.sin(2 * np.pi * (3 / N + f / n) + phase)
                for dx in (-1, 0, 1):
                    for dy in (0, 1, 2):
                        s.px(cx + dx, 1 + dy, (236, 214, 110) if dx <= 0 and dy == 0 else (196, 170, 70), 0.9)
            return s.tex(sss=120)
        return strip(name, mk)
    for i, nm in enumerate(("kelp_a", "kelp_b", "kelp_c", "kelp_d")):
        put(nm, ribbon(nm, "body", i * 1.57) if nm in STATS else None)
    put("kelp_top", ribbon("kelp_top", "top", 0.0) if "kelp_top" in STATS else None)
    put("kelp_top_bulb", ribbon("kelp_top_bulb", "bulb", 0.0) if "kelp_top_bulb" in STATS else None)

    def sway(name, count, height, base_y=N - 1, full=False, seed=None):
        ramp = vramp(name, 5, contrast=0.44)
        r0 = rng_of(seed or name)
        blades_ = [(1 + r0.random() * 13, int(r0.integers(height[0], height[1] + 1)), r0.random() * 6.28, r0.random()) for _ in range(count)]
        def mk(f, n):
            s = Sprite()
            for (x, ln, ph, shade) in blades_:
                ln2 = N if full else ln
                for k in range(ln2):
                    t = k / max(1, ln2 - 1)
                    xi = x + (1.6 * np.sin(2 * np.pi * f / n + ph)) * t * t
                    tone = int(np.clip(1 + 3 * t + (shade - 0.5), 0, 4))
                    s.px(xi, base_y - k, ramp[tone], 0.4 + 0.5 * t)
                    if k < ln2 * 0.5:
                        s.px(xi + 1, base_y - k, ramp[max(0, tone - 1)], 0.35)
            return s.tex(sss=120)
        return strip(name, mk)
    put("seagrass", sway("seagrass", 7, (5, 11)) if "seagrass" in STATS else None)
    for ab in ("a", "b"):
        put(f"seagrass_doubletall_bottom_{ab}", sway(f"seagrass_doubletall_bottom_{ab}", 7, (16, 16), full=True, seed="dsg" + ab) if f"seagrass_doubletall_bottom_{ab}" in STATS else None)
        put(f"seagrass_doubletall_top_{ab}", sway(f"seagrass_doubletall_top_{ab}", 6, (5, 12), seed="dsgt" + ab) if f"seagrass_doubletall_top_{ab}" in STATS else None)
    if "seagrass_carried" in STATS:
        out["seagrass_carried"] = P.blades("seagrass_carried", vramp("seagrass_carried", 5, contrast=0.44), count=7, height=(5, 11))

    def spike(name, up, w_tip, w_base, ramp):
        s = Sprite()
        r = rng_of("spike")
        for k in range(N):                               # k = 0 at the wide end
            t = k / (N - 1)
            w = w_base + (w_tip - w_base) * t
            y = (N - 1 - k) if up else k
            x0 = 7.5 - w / 2
            for i in range(int(round(w))):
                x = int(round(x0 + i))
                tone = 3 if i == 0 else (1 if i == int(round(w)) - 1 else 2)
                if k % 5 == 4 and tone == 2:
                    tone = 1
                s.px(x, y, ramp[tone], 0.5 + 0.3 * (1 - abs(i - w / 2) / max(1, w / 2)))
        if w_tip <= 2:
            s.px(7, 0 if up else N - 1, ramp[4], 0.9)
        return s.tex(sss=0, rough=200)
    for fam, ramp_name, parts in (("pointed_dripstone", "dripstone_block", (("base", 10, 14), ("middle", 8, 10), ("frustum", 4, 8), ("tip", 1, 4), ("merge", 3, 5))),
                                  ("sulfur_spike", "sulfur", (("base", 10, 14), ("middle", 8, 10), ("frustum", 4, 8), ("tip", 1, 4), ("tip_merge", 3, 5)))):
        if ramp_name not in STATS:
            continue
        ramp = vramp(ramp_name, 5, contrast=0.4)
        for part, wt, wb in parts:
            for d in ("up", "down"):
                nm = f"{fam}_{d}_{part}"
                put(nm, spike(nm, d == "up", wt, wb, ramp) if nm in STATS else None)

    # ---- small plants that were still missing
    put("flower_paeonia", flower("tulip_pink"))
    put("flower_rose_blue", flower("cornflower"))
    if "red_shrub" in STATS:
        out["red_shrub"] = P.blades("red_shrub", vramp("red_shrub", 5, contrast=0.5), count=9, height=(5, 12), curl=1.5)
    if "cactus_flower" in STATS:
        s = Sprite()
        s.shape(5, 9, ["..33..", ".3443.", "334433", "233332", ".2222.", "..11.."],
                [(120, 30, 90), (190, 50, 130), (236, 90, 170), (255, 150, 210), (255, 226, 120)], 0.9)
        out["cactus_flower"] = s.tex()
    if "resin_clump" in STATS:
        s = Sprite()
        rr = vramp("resin_clump", 5, contrast=0.4)
        for (x, y) in ((4, 5), (10, 4), (7, 10), (12, 11)):
            s.shape(x, y, [".43", "432", "321"], rr, 0.9, emis=30)
        out["resin_clump"] = s.tex(sss=120)
    for nm in ("melon_stem_disconnected", "pumpkin_stem_disconnected", "melon_stem_connected", "pumpkin_stem_connected"):
        if nm in STATS:
            s = Sprite()
            g = vramp(nm, 5, grey=True, contrast=0.4)
            if "disconnected" in nm:
                for k in range(8):
                    s.px(7 + (1 if k > 4 else 0), 15 - k, g[2 + (k % 2)], 0.6)
                    s.px(8 + (1 if k > 4 else 0), 15 - k, g[1], 0.5)
                s.px(9, 7, g[4], 0.8)
            else:
                for k in range(16):
                    y = 15 - int(5 * np.sin(k / 15 * np.pi / 2 * 1.6))
                    s.px(k, y, g[3], 0.6)
                    s.px(k, y + 1, g[1], 0.5)
            out[nm] = s.tex()
    for nm, top in (("double_plant_sunflower_bottom", False), ("double_plant_sunflower_top", True)):
        if nm in STATS:
            s = Sprite()
            g = make_ramp((70, 140, 50), 5, 0.42)
            s.stem(7, 0 if not top else 7, 15, ramp=g[:4], thick=True)       # the flower head sits on the upper half
            for k in ((3, 9, 13) if not top else (10, 13)):
                s.leaf(7, k, -1, g, ln=4)
                s.leaf(8, k + 1, 1, g, ln=4)
            out[nm] = s.tex()
    for nm, front in (("double_plant_sunflower_front", True), ("double_plant_sunflower_back", False)):
        if nm in STATS:
            s = Sprite()
            pet = [(190, 130, 10), (236, 180, 20), (255, 222, 50), (255, 246, 150)]
            d = np.hypot(xx - 7.5, yy - 7.5)
            ang = np.arctan2(yy - 7.5, xx - 7.5)
            for y in range(N):
                for x in range(N):
                    if d[y, x] < 2.6:
                        s.px(x, y, ((110, 70, 30) if (x + y) % 2 else (140, 92, 40)) if front else (70, 130, 50), 0.9)
                    elif d[y, x] < 5.6 and (np.sin(ang[y, x] * 6) > -0.35 or d[y, x] < 3.6):
                        s.px(x, y, pet[3 if d[y, x] > 4.6 else 2 if np.sin(ang[y, x] * 6) > 0.3 else 1] if front else (90, 150, 60), 0.7)
            out[nm] = s.tex()
    for nm in ("pale_moss_carpet_side_base", "pale_moss_carpet_side_tip"):
        if nm in STATS:
            pm = vramp("pale_moss_block" if "pale_moss_block" in STATS else nm, 5, contrast=0.4)
            out[nm] = P.blades(nm, pm, count=12, height=(5, 12) if "tip" in nm else (12, 16), sss=60)
    for nm in ("eyeblossom_dormant", "eyeblossom_blooming"):
        if nm in STATS:
            s = Sprite()
            s.stem(7, 8, 15, ramp=make_ramp((90, 100, 90), 4, 0.3))
            s.leaf(7, 13, -1, make_ramp((100, 110, 100), 5, 0.3), ln=3)
            open_ = "blooming" in nm
            s.shape(5, 4, [".232.", "23432", "24042" if open_ else "23332", "23432", ".232."],
                    [(255, 150, 40), (90, 86, 90), (130, 124, 130), (176, 170, 176), (240, 140, 60) if open_ else (150, 144, 150)], 0.9,
                    emis=0)
            if open_:
                s.emis[6, 7] = 230
            out[nm] = s.tex()
    for nm in ("mangrove_propagule", "mangrove_propagule_hanging"):
        if nm in STATS:
            s = Sprite()
            g = make_ramp((90, 150, 60), 5, 0.42)
            hang = "hanging" in nm
            for k in range(9):
                s.px(7, (3 + k) if hang else (15 - k), g[2 + (k % 2)], 0.6)
                s.px(8, (3 + k) if hang else (15 - k), g[1], 0.5)
            for d in (-1, 1):
                s.leaf(7 if d < 0 else 8, 3 if hang else 6, d, g, ln=3)
            out[nm] = s.tex()


def turn(t):
    """Quarter-turn a texture so its grain runs the other way."""
    t.rgb = np.ascontiguousarray(np.transpose(t.rgb, (1, 0, 2)))
    t.height = t.height.T.copy()
    for k in ("metal", "emis", "rough", "sss"):
        v = getattr(t, k)
        if not np.isscalar(v):
            setattr(t, k, np.asarray(v).T.copy())
    return t


_build_rest = build


def build(out, flip, variations):          # noqa: F811
    """Everything above, then the direction fixes found by tools/check_orientation.py."""
    _build_rest(out, flip, variations)
    for nm in ("farmland_dry", "farmland_wet", "dried_kelp_side_a", "dried_kelp_side_b", "log_jungle"):
        if nm in out:
            out[nm] = turn(out[nm].copy())
    out.pop("mangrove_propagule_hanging", None)          # tied to its model layout: keep the game's
    # sculk catalyst: pale bone block with sculk creeping down from the top
    if "sculk_catalyst_side" in STATS:
        sk = make_ramp((16, 40, 50), 5, 0.6)
        bone = P.rock("catalyst_bone", make_ramp((226, 220, 200), 5, 0.24), "smooth", cracks=2, rough=170)
        dark = P.rock("catalyst_sculk", sk, "grain", cracks=0, rough=120)
        side = P.top_over("sculk_catalyst_side", bone, dark, depth=6, extra=2)
        glow = [(20, 110, 130), (60, 200, 220), (190, 250, 250)]
        r = rng_of("catalyst_dots")
        emis = np.zeros((N, N))
        for _ in range(5):
            x, y = int(r.integers(1, 15)), int(r.integers(1, 5))
            side.rgb[y, x] = glow[1]
            emis[y, x] = 200
        side.emis = emis
        out["sculk_catalyst_side"] = side
        out["sculk_catalyst_bottom"] = bone
        top = dark.copy()
        emis = np.zeros((N, N))
        for _ in range(7):
            x, y = int(r.integers(1, 15)), int(r.integers(1, 15))
            top.rgb[y, x] = glow[1]
            emis[y, x] = 200
        top.emis = emis
        out["sculk_catalyst_top"] = top
        for nm, src in (("sculk_catalyst_side_bloom", side), ("sculk_catalyst_top_bloom", top)):
            if nm in STATS:
                n = frames_of(nm)
                fr = []
                for f in range(n):
                    t = src.copy()
                    lvl = [0, 1, 2, 1][f % 4]
                    lit = plane(src.emis) > 0
                    t.rgb = np.where(lit[..., None], np.array(glow[lvl], np.uint8), t.rgb)
                    t.emis = np.where(lit, 150 + 50 * lvl, 0)
                    fr.append(t)
                out[nm] = stack_frames(fr)
