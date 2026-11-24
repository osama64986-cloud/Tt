"""Hand-tuned combat strike animations for the anime fighters (Bedrock keyframe JSON).

DESIGN NOTE - how these strikes are meant to read
-------------------------------------------------
* Every strike shares the same beats: ANTICIPATION (a tiny load in the opposite
  direction: shoulder or hip cocked back, knee chambered), a very fast ACTION that
  accelerates into the CONTACT frame, an OVERSHOOT past the target with
  FOLLOW-THROUGH, then a RECOVERY that eases back into the fighting guard.
  Fast in, slow out: the travel into contact is ease-IN (still speeding up when it
  lands) and everything after contact is ease-OUT.
* Server timing (main.js comboStep): the pose is set, and damage lands 1 tick
  (0.05 s) later for every single-hit move, so each contact frame sits at
  ~0.045-0.065 s. Anticipation therefore has to be "pre-loaded" into frame 0 and
  sold by the follow-through. Each animation lasts exactly the move's `t`
  (jab/cut 3 ticks = 0.15 s, front kick / uppercut 5 = 0.25 s, roundhouses 6 =
  0.30 s, axe kick 7 = 0.35 s) and its last frame is the guard, so a combo flows
  strike -> guard -> strike with no popping; hold_on_last_frame keeps the guard.
* Power comes from the ground up: hips (root) turn before the shoulders (body),
  the shoulders before the fist. The rear foot pivots on crosses and roundhouses
  (leg Y twist), the knees flex to take the weight, the torso leans away from a
  kick to counterbalance it.
* The idle hand never drops: on every punch the other fist comes back to the
  chin (forearm folded ~105 deg). On kicks the arms open for balance but the
  lead hand stays high.
* Smear: limbs stretch ~12-16 % along their length during the fastest travel
  frames (bone scale on Y) and snap back at contact - the blocky equivalent of an
  anime smear frame.
* The head is counter-rotated against the hips/torso every frame, so the eyes
  stay locked on the target while the body twists (head is a child of body,
  body of root).
* Rush: a looping 0.2 s cycle, fists alternating, 20 punches/s, every other one
  lining up with the 10 hits/s the server deals (hits at 0.05, 0.15, ... s). Face
  and body shots alternate, the torso rocks +-16 deg with each fist and bobs.
* Sword cuts: diagonal kesa-giri from high over the shoulder to the opposite
  hip, torso uncoiling through ~70 deg; each cut finishes with the OTHER arm
  already rising, so cut_r -> cut_l -> cut_r chains like a dual-wield flurry.

Conventions (verified against existing poses in build.py): arm X<0 raises the
arm forward; rightArm +Y swings a forward arm outward (to its right), leftArm -Y
outward; rightArm/rightLeg +Z out to the side, left mirrored. body/root +Y turns
the right shoulder back. root +X leans forward (pivot at the feet), root +Z
leans to the fighter's left. Forearm X<0 bends the elbow, shin X>0 bends the knee.
"""

BONES = ["root", "body", "head", "rightArm", "leftArm", "rightForearm", "leftForearm",
         "rightLeg", "leftLeg", "rightShin", "leftShin"]

# Fighting guard: matches animation.ab.stance (orthodox, left lead) so strikes end where the stance begins.
GUARD = {
    "root": (0, 0, 0), "body": (3, 22, 0),
    "rightArm": (-42, -30, -6), "rightForearm": (-82, 0, 0),
    "leftArm": (-74, 8, 0), "leftForearm": (-48, 0, 0),
    "rightLeg": (10, 0, 4), "leftLeg": (-10, 0, -4),
    "rightShin": (8, 0, 0), "leftShin": (6, 0, 0),
}

FPS = 60.0  # in-betweens are baked at render rate so the easing curves survive linear interpolation

EASE = {
    "lin": lambda u: u,
    "in": lambda u: u * u,                      # accelerate into contact
    "in3": lambda u: u * u * u,                 # whip-crack: slow start, explosive end
    "out": lambda u: 1 - (1 - u) ** 2,          # decelerate (overshoot, settle)
    "out3": lambda u: 1 - (1 - u) ** 3,         # hard snap then long settle
    "io": lambda u: u * u * (3 - 2 * u),        # smooth both ends (recovery to guard)
    "hold": lambda u: 0.0 if u < 1 else 1.0,    # (unused by default) stepped key
}


def pose(base=None, *, pos=(0, 0, 0), look=(0, 0, 0), scale=None, **rot):
    """A full-body snapshot. Rotations inherit from `base` (default GUARD); position, scale and the
    head's extra look offset never inherit."""
    r = dict(GUARD if base is None else base["rot"])
    for k, v in rot.items():
        assert k in BONES and k != "head", k
        r[k] = tuple(v)
    return {"rot": r, "pos": tuple(pos), "look": tuple(look), "scale": dict(scale or {})}


def mirror(p):
    """Left/right mirror of a pose: swap the sides, negate Y and Z rotations and X position."""
    sw = lambda n: n.replace("right", "#").replace("left", "right").replace("#", "left")
    m = lambda v: (v[0], -v[1], -v[2])
    return {"rot": {sw(k): m(v) for k, v in p["rot"].items()},
            "pos": (-p["pos"][0], p["pos"][1], p["pos"][2]),
            "look": m(p["look"]),
            "scale": {sw(k): v for k, v in p["scale"].items()}}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _head(p):
    """Counter-rotate the head against root + body so the eyes stay on the target."""
    ro, bo, lk = p["rot"]["root"], p["rot"]["body"], p["look"]
    return (_clamp(-(ro[0] + bo[0]), -35, 35) + lk[0],
            _clamp(-(ro[1] + bo[1]), -62, 62) + lk[1],
            _clamp(-(ro[2] + bo[2]), -25, 25) + lk[2])


def _channel(p, bone, ch):
    if ch == "rotation":
        return _head(p) if bone == "head" else p["rot"][bone]
    if ch == "position":
        return p["pos"]
    return p["scale"].get(bone, (1, 1, 1))


def _key(t):
    return str(round(t, 4))


def _num(v):
    v = round(v, 2)
    return int(v) if v == int(v) else v


def _sample(keys, length):
    """keys: [(t, value, ease_into_this_key)] -> {"time": [x,y,z]} with baked in-betweens."""
    out = {}
    for i, (t, v, _) in enumerate(keys):
        if i:
            t0, v0, _ = keys[i - 1]
            ease = EASE[keys[i][2]]
            dt = t - t0
            n = int(round(dt * FPS))
            if keys[i][2] != "lin" and n >= 2:
                for k in range(1, n):
                    u = k / n
                    w = ease(u)
                    out[_key(t0 + dt * u)] = [_num(a + (b - a) * w) for a, b in zip(v0, v)]
        out[_key(min(t, length))] = [_num(x) for x in v]
    return out


def timeline(frames, length):
    """frames: [(time, pose, ease)] -> Bedrock bones dict. Constant channels become plain vectors."""
    assert frames[0][0] == 0.0 and abs(frames[-1][0] - length) < 1e-9
    bones = {}
    for bone in BONES:
        chans = ["rotation"] + (["position"] if bone == "root" else []) + (["scale"] if bone != "root" else [])
        entry = {}
        for ch in chans:
            vals = [_channel(p, bone, ch) for _, p, _ in frames]
            default = (1, 1, 1) if ch == "scale" else (0, 0, 0)
            if ch != "rotation" and all(tuple(v) == default for v in vals):
                continue
            if all(tuple(v) == tuple(vals[0]) for v in vals):
                entry[ch] = [_num(x) for x in vals[0]]
            else:
                entry[ch] = _sample([(t, v, e) for (t, _, e), v in zip(frames, vals)], length)
        bones[bone] = entry
    return bones


def strike(frames, length):
    return {"loop": "hold_on_last_frame", "animation_length": length, "override_previous_animation": True,
            "bones": timeline(frames, length)}


def mirrored(frames, keep_last_guard=True):
    out = [(t, mirror(p), e) for t, p, e in frames]
    if keep_last_guard:  # the guard is asymmetric (orthodox): a mirrored move still settles into it
        out[-1] = (out[-1][0], frames[-1][1], out[-1][2])
    return out


G = pose()
STRETCH = (1, 1.14, 1)


# --- jab_r: the rear-hand cross (3 ticks = 0.15 s, contact 0.05) --------------------------------
def jab_r():
    load = pose(root=(0, 4, 0), body=(4, 30, 0), rightArm=(-38, -32, -6), rightForearm=(-100, 0, 0),
                rightLeg=(12, 0, 4), rightShin=(10, 0, 0))
    mid = pose(root=(2, -2, 0), body=(5, 4, 0), rightArm=(-72, -6, -2), rightForearm=(-58, 0, 0),
               leftArm=(-62, 18, 2), leftForearm=(-96, 0, 0),
               rightLeg=(13, -10, 4), leftLeg=(-14, 0, -4), rightShin=(14, 0, 0), leftShin=(12, 0, 0),
               scale={"rightArm": STRETCH})
    hit = pose(root=(5, -8, 0), body=(6, -26, 0), rightArm=(-95, 18, 0), rightForearm=(-3, 0, 0),
               leftArm=(-58, 24, 4), leftForearm=(-108, 0, 0),             # lead fist parked on the chin
               rightLeg=(14, -22, 4), leftLeg=(-17, 0, -4),                # rear foot pivots, weight forward
               rightShin=(18, 0, 0), leftShin=(16, 0, 0), scale={"rightArm": (1, 1.06, 1)}, look=(4, 0, 0))
    over = pose(hit, root=(6, -10, 0), body=(7, -32, 0), rightArm=(-99, 20, 0), rightForearm=(0, 0, 0))
    back = pose(root=(3, -4, 0), body=(5, 2, 0), rightArm=(-70, -12, -2), rightForearm=(-70, 0, 0),
                leftArm=(-64, 18, 2), leftForearm=(-90, 0, 0), rightLeg=(12, -10, 4), leftLeg=(-13, 0, -4),
                rightShin=(12, 0, 0), leftShin=(10, 0, 0))
    return strike([(0.0, load, "lin"), (0.025, mid, "in"), (0.05, hit, "in"), (0.07, over, "out"),
                   (0.105, back, "io"), (0.15, G, "out")], 0.15)


# --- jab_l: the lead jab (3 ticks) - minimal wind-up, snaps back faster than it went out -------
def jab_l():
    load = pose(body=(3, 18, 0), leftArm=(-66, 12, 2), leftForearm=(-70, 0, 0), leftShin=(9, 0, 0))
    mid = pose(root=(2, 2, 0), body=(4, 28, 0), leftArm=(-86, -8, 0), leftForearm=(-30, 0, 0),
               rightArm=(-46, -34, -6), rightForearm=(-102, 0, 0), scale={"leftArm": STRETCH})
    hit = pose(root=(4, 4, 0), body=(5, 36, 0), leftArm=(-96, -26, 0), leftForearm=(-2, 0, 0),
               rightArm=(-48, -36, -6), rightForearm=(-108, 0, 0),         # rear fist glued to the jaw
               rightLeg=(13, 0, 4), leftLeg=(-15, 0, -4), rightShin=(10, 0, 0), leftShin=(14, 0, 0),
               scale={"leftArm": (1, 1.05, 1)}, look=(3, 0, 0))
    over = pose(hit, body=(5, 39, 0), leftArm=(-99, -29, 0), leftForearm=(0, 0, 0))
    snap = pose(root=(2, 2, 0), body=(4, 26, 0), leftArm=(-78, 4, 0), leftForearm=(-56, 0, 0),
                rightArm=(-46, -34, -6), rightForearm=(-100, 0, 0))
    return strike([(0.0, load, "lin"), (0.022, mid, "in"), (0.045, hit, "in"), (0.062, over, "out"),
                   (0.095, snap, "out3"), (0.15, G, "io")], 0.15)


# --- kick: rear-leg front (push) kick (5 ticks = 0.25 s) ---------------------------------------
def kick():
    arms = dict(rightArm=(-24, 0, 22), rightForearm=(-60, 0, 0), leftArm=(-72, 14, -6), leftForearm=(-96, 0, 0))
    chamber = pose(root=(-5, 6, 0), body=(-2, 12, 0), rightLeg=(-72, 0, 4), rightShin=(100, 0, 0),
                   leftLeg=(4, 0, -4), leftShin=(12, 0, 0), **arms)
    mid = pose(chamber, rightLeg=(-92, 0, 2), rightShin=(45, 0, 0), root=(-8, 4, 0), scale={"rightLeg": (1, 1.12, 1)})
    hit = pose(chamber, root=(-11, 2, 0), body=(-5, 8, 0), rightLeg=(-100, 0, 0), rightShin=(0, 0, 0),
               leftLeg=(7, 0, -4), leftShin=(16, 0, 0), rightArm=(-6, 0, 26), rightForearm=(-40, 0, 0),
               look=(6, 0, 0))
    over = pose(hit, rightLeg=(-106, 0, 0), root=(-12, 2, 0))
    rechamber = pose(chamber, rightLeg=(-74, 0, 4), rightShin=(85, 0, 0), root=(-6, 6, 0))
    step = pose(root=(2, 0, 0), rightLeg=(-6, 0, 4), rightShin=(30, 0, 0), leftShin=(12, 0, 0),
                rightArm=(-38, -24, 4), rightForearm=(-80, 0, 0))
    return strike([(0.0, chamber, "lin"), (0.03, mid, "in"), (0.055, hit, "in"), (0.08, over, "out"),
                   (0.13, rechamber, "io"), (0.19, step, "io"), (0.25, G, "out")], 0.25)


# --- round: rear-leg roundhouse (6 ticks = 0.30 s) - hips turn over, shin whips through --------
def round_r():
    chamber = pose(root=(0, -18, 6), body=(0, 14, 0), rightLeg=(-55, 0, 45), rightShin=(105, 0, 0),
                   leftLeg=(2, 12, -5), leftShin=(12, 0, 0),
                   rightArm=(-10, 0, 28), rightForearm=(-50, 0, 0), leftArm=(-78, 20, -4), leftForearm=(-100, 0, 0))
    whip = pose(chamber, root=(0, -38, 11), body=(0, 18, 0), rightLeg=(-35, 0, 80), rightShin=(65, 0, 0),
                rightArm=(10, 0, 28), scale={"rightLeg": (1, 1.15, 1)})
    hit = pose(chamber, root=(0, -58, 14), body=(0, 16, 0), rightLeg=(-20, 0, 94), rightShin=(4, 0, 0),
               leftLeg=(4, 22, -6), leftShin=(14, 0, 0),                       # support foot pivoted on the ball
               rightArm=(24, 0, 24), rightForearm=(-24, 0, 0), leftArm=(-84, 28, -2), leftForearm=(-104, 0, 0),
               scale={"rightLeg": (1, 1.04, 1)})
    over = pose(hit, root=(0, -72, 15), body=(0, 20, 0), rightLeg=(-18, 0, 92), rightShin=(0, 0, 0))
    rechamber = pose(chamber, root=(0, -42, 9), body=(0, 18, 0), rightLeg=(-42, 0, 55), rightShin=(95, 0, 0),
                     leftLeg=(2, 16, -5))
    land = pose(root=(2, -10, 2), body=(3, 24, 0), rightLeg=(8, 0, 10), rightShin=(25, 0, 0), leftShin=(14, 0, 0),
                rightArm=(-34, -20, 6), rightForearm=(-76, 0, 0))
    return [(0.0, chamber, "lin"), (0.03, whip, "in"), (0.055, hit, "in3"), (0.085, over, "out"),
            (0.15, rechamber, "io"), (0.23, land, "io"), (0.3, G, "out")]


# --- upper: rising rear uppercut (5 ticks) - dip, drive up through the legs, launch -----------
def upper():
    dip = pose(root=(6, 6, 0), body=(8, 30, 0), rightArm=(-8, -8, 8), rightForearm=(-100, 0, 0),
               leftArm=(-62, 22, 2), leftForearm=(-104, 0, 0),
               rightLeg=(16, -6, 4), leftLeg=(-20, 0, -4), rightShin=(28, 0, 0), leftShin=(26, 0, 0), pos=(0, -1.1, 0))
    drive = pose(dip, root=(2, -2, 0), body=(2, 4, 0), rightArm=(-62, 4, 2), rightForearm=(-92, 0, 0),
                 rightLeg=(14, -16, 4), rightShin=(14, 0, 0), leftShin=(12, 0, 0), pos=(0, -0.2, 0),
                 scale={"rightArm": STRETCH})
    hit = pose(dip, root=(-4, -8, 0), body=(-8, -24, 0), rightArm=(-118, 14, 0), rightForearm=(-72, 0, 0),
               rightLeg=(12, -24, 4), leftLeg=(-12, 0, -4), rightShin=(6, 0, 0), leftShin=(4, 0, 0),
               pos=(0, 0.6, 0), look=(-10, 0, 0))
    follow = pose(hit, root=(-6, -10, 0), body=(-12, -28, 0), rightArm=(-162, 10, -4), rightForearm=(-38, 0, 0),
                  pos=(0, 1.1, 0), look=(-16, 0, 0))
    settle = pose(root=(-2, -4, 0), body=(-2, 4, 0), rightArm=(-118, -14, -2), rightForearm=(-80, 0, 0),
                  leftArm=(-66, 18, 2), leftForearm=(-96, 0, 0), rightShin=(14, 0, 0), leftShin=(12, 0, 0),
                  pos=(0, -0.3, 0), look=(-6, 0, 0))
    return strike([(0.0, dip, "lin"), (0.025, drive, "in"), (0.05, hit, "in"), (0.09, follow, "out"),
                   (0.16, settle, "io"), (0.25, G, "io")], 0.25)


# --- knee (pose 10) = AXE KICK (7 ticks = 0.35 s) - leg hangs at the apex, then hammers down ----
def axe():
    high = pose(root=(-10, 0, 0), body=(-8, 10, 0), rightLeg=(-152, 0, 14), rightShin=(4, 0, 0),
                leftLeg=(6, 0, -4), leftShin=(8, 0, 0),
                rightArm=(-40, 0, 40), rightForearm=(-30, 0, 0), leftArm=(-66, 22, -18), leftForearm=(-80, 0, 0),
                pos=(0, 0.5, 0), look=(4, 0, 0))
    apex = pose(high, root=(-12, 0, 0), rightLeg=(-172, 0, 6), rightShin=(0, 0, 0), pos=(0, 0.7, 0))
    fall = pose(apex, root=(0, 0, 0), body=(2, 8, 0), rightLeg=(-100, 0, 2), rightArm=(-10, 0, 34),
                leftArm=(-50, 16, -16), pos=(0, 0.2, 0), scale={"rightLeg": (1, 1.16, 1)})
    hit = pose(high, root=(10, 0, 0), body=(14, 6, 0), rightLeg=(-36, 0, 0), rightShin=(0, 0, 0),
               leftLeg=(12, 0, -4), leftShin=(30, 0, 0),
               rightArm=(16, 0, 26), rightForearm=(-40, 0, 0), leftArm=(-34, 10, -22), leftForearm=(-70, 0, 0),
               pos=(0, -1.0, 0), look=(14, 0, 0))
    crush = pose(hit, root=(12, 0, 0), body=(16, 6, 0), rightLeg=(-22, 0, 0), rightShin=(14, 0, 0),
                 leftShin=(34, 0, 0), pos=(0, -1.3, 0))
    hold = pose(crush, rightLeg=(-24, 0, 0), rightShin=(18, 0, 0), pos=(0, -1.2, 0))
    rise = pose(root=(4, 0, 0), body=(6, 16, 0), rightLeg=(-4, 0, 4), rightShin=(30, 0, 0), leftShin=(18, 0, 0),
                rightArm=(-30, -20, 8), rightForearm=(-70, 0, 0), leftArm=(-70, 10, -2), leftForearm=(-70, 0, 0),
                pos=(0, -0.5, 0), look=(6, 0, 0))
    return strike([(0.0, high, "lin"), (0.025, apex, "out"), (0.045, fall, "in"), (0.065, hit, "in"),
                   (0.09, crush, "out"), (0.15, hold, "lin"), (0.24, rise, "io"), (0.35, G, "io")], 0.35)


# --- rush: machine-gun flurry, looping 0.2 s, 20 punches/s ------------------------------------
def rush():
    L = 0.2
    # retracted (fist at the chin) and extended (face / body shot) arm poses
    R_back, R_face, R_body = (-52, -20, -4), (-96, 8, 0), (-80, 4, 4)
    L_back, L_face, L_body = (-52, 20, 4), (-96, -8, 0), (-80, -4, -4)
    F_back, F_out = -108, -3

    def cyc(points):
        """points: [(t, value, ease)] for one loop (times may run past L or below 0): a periodic curve,
        baked at render rate plus every key time, with matching values at 0 and L so the loop is seamless."""
        pts = sorted(((round(t % L, 4), tuple(v), e) for t, v, e in points), key=lambda p: p[0])
        ext = [(t - L, v, e) for t, v, e in pts] + pts + [(t + L, v, e) for t, v, e in pts]

        def at(t):
            for (t0, v0, _), (t1, v1, e) in zip(ext, ext[1:]):
                if t0 <= t <= t1:
                    w = EASE[e]((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
                    return [_num(a + (b - a) * w) for a, b in zip(v0, v1)]
            raise ValueError(t)

        times = sorted({round(k / FPS, 4) for k in range(int(L * FPS) + 1)} | {t for t, _, _ in pts} | {0.0, L})
        out = {_key(t): at(t) for t in times if t <= L}
        out[_key(L)] = out[_key(0.0)]
        return out

    def arm(c1, c2, back, out1, out2):
        # contacts at c1 and c2 (0.1 s apart): retract 0.035 before, snap out, hold a beat, pull back
        pts = []
        for c, out in ((c1, out1), (c2, out2)):
            pts += [(c - 0.035, back, "out"), (c, out, "in"), (c + 0.015, out, "lin")]
        return cyc(pts)

    def fore(c1, c2):
        pts = []
        for c in (c1, c2):
            pts += [(c - 0.035, (F_back, 0, 0), "out"), (c, (F_out, 0, 0), "in"), (c + 0.015, (F_out, 0, 0), "lin")]
        return cyc(pts)

    def stretch(c1, c2):
        pts = []
        for c in (c1, c2):
            pts += [(c - 0.035, (1, 1, 1), "lin"), (c - 0.012, (1, 1.15, 1), "in"), (c + 0.01, (1, 1, 1), "out")]
        return cyc(pts)

    # right fist lands on the server's hit ticks (0.05, 0.15), the left between them (0.0/0.2, 0.1)
    body_y = cyc([(0.0, (8, 16, 0), "out"), (0.05, (10, -16, 0), "out"), (0.1, (8, 14, 0), "out"),
                  (0.15, (11, -18, 0), "out")])
    head = cyc([(0.0, (-8, -14, 0), "out"), (0.05, (-10, 14, 0), "out"), (0.1, (-8, -12, 0), "out"),
                (0.15, (-11, 16, 0), "out")])
    root_pos = cyc([(0.0, (0, -0.4, 0), "out"), (0.05, (0, -0.7, 0), "out"), (0.1, (0, -0.4, 0), "out"),
                    (0.15, (0, -0.8, 0), "out")])
    bones = {
        "root": {"rotation": [4, 0, 0], "position": root_pos},
        "body": {"rotation": body_y},
        "head": {"rotation": head},
        "rightArm": {"rotation": arm(0.05, 0.15, R_back, R_face, R_body), "scale": stretch(0.05, 0.15)},
        "leftArm": {"rotation": arm(0.1, 0.2, L_back, L_face, L_body), "scale": stretch(0.1, 0.2)},
        "rightForearm": {"rotation": fore(0.05, 0.15)},
        "leftForearm": {"rotation": fore(0.1, 0.2)},
        "rightLeg": {"rotation": [18, -6, 6]}, "leftLeg": {"rotation": [-18, 0, -6]},
        "rightShin": {"rotation": [14, 0, 0]}, "leftShin": {"rotation": [18, 0, 0]},
    }
    return {"loop": True, "animation_length": L, "override_previous_animation": True, "bones": bones}


# --- slash: right-hand diagonal cut, high right shoulder -> low left hip (3 ticks) -------------
def slash_frames():
    off = dict(leftArm=(-36, 0, -26), leftForearm=(-44, 0, 0))
    wind = pose(root=(-2, 8, 0), body=(-4, 32, 0), rightArm=(-158, 28, 16), rightForearm=(-38, 0, 0),
                rightLeg=(12, 0, 4), leftLeg=(-14, 0, -4), rightShin=(10, 0, 0), leftShin=(12, 0, 0),
                look=(-2, 0, 0), **off)
    drive = pose(wind, root=(1, 0, 0), body=(0, 8, 0), rightArm=(-128, 12, 8), rightForearm=(-16, 0, 0),
                 scale={"rightArm": (1, 1.12, 1)})
    hit = pose(wind, root=(5, -8, 0), body=(6, -28, 0), rightArm=(-70, -38, 0), rightForearm=(-4, 0, 0),
               rightLeg=(14, -16, 4), leftLeg=(-18, 0, -4), rightShin=(16, 0, 0), leftShin=(18, 0, 0),
               scale={"rightArm": (1, 1.08, 1)}, look=(4, 0, 0))
    through = pose(hit, root=(6, -10, 0), body=(8, -40, 0), rightArm=(-34, -60, 0), rightForearm=(-8, 0, 0))
    settle = pose(through, root=(4, -6, 0), body=(6, -34, 0), rightArm=(-40, -50, 0), rightForearm=(-20, 0, 0),
                  leftArm=(-60, -4, -18), leftForearm=(-36, 0, 0))
    # ready: the cutting arm drawn back to the middle, the other already rising for the next cut
    ready = pose(root=(2, -2, 0), body=(4, -12, 0), rightArm=(-56, -24, 0), rightForearm=(-44, 0, 0),
                 leftArm=(-96, -14, -20), leftForearm=(-40, 0, 0),
                 rightLeg=(12, -8, 4), leftLeg=(-14, 0, -4), rightShin=(12, 0, 0), leftShin=(12, 0, 0))
    return [(0.0, wind, "lin"), (0.022, drive, "in"), (0.045, hit, "in"), (0.07, through, "out"),
            (0.1, settle, "out"), (0.15, ready, "io")]


ANIMS = {
    "jab_r": jab_r,
    "jab_l": jab_l,
    "kick": kick,
    "round": lambda: strike(round_r(), 0.3),
    "upper": upper,
    "knee": axe,
    "rush": rush,
    "elbow": lambda: strike(mirrored(round_r()), 0.3),                 # pose 12 = LEFT roundhouse
    "slash": lambda: strike(slash_frames(), 0.15),
    "slash_l": lambda: strike(mirrored(slash_frames(), keep_last_guard=False), 0.15),  # pose 28
}


def apply(animations: dict) -> None:
    """Replace the strike animations in an ab.animation.json "animations" dict."""
    for name, make in ANIMS.items():
        animations[f"animation.ab.{name}"] = make()


def _validate():
    d = {}
    apply(d)
    for name, a in d.items():
        L = a["animation_length"]
        for bone, chans in a["bones"].items():
            for ch, v in chans.items():
                frames = v.items() if isinstance(v, dict) else [("0.0", v)]
                for t, val in frames:
                    assert 0.0 <= float(t) <= L + 1e-9, (name, bone, ch, t)
                    assert isinstance(val, str) or (isinstance(val, list) and len(val) == 3), (name, bone, ch, val)
    return d


if __name__ == "__main__":
    import json
    d = _validate()
    for k, a in sorted(d.items()):
        n = sum(len(v) if isinstance(v, dict) else 1 for c in a["bones"].values() for v in c.values())
        print(k, a["animation_length"], a["loop"], "keys:", n)
    print(len(json.dumps(d)), "bytes")
