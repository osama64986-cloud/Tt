"""Nabd movement system: walking, running, walking backwards, jumping, landing
and the move between standing and crouching.

Everything is our own motion design.  It runs inside the animations the game's
player already plays (move.arms, move.legs, sneaking), so no player entity file
is replaced and other add-ons keep working.

State kept on the player between frames (Molang variables, written from inside
move.arms - the first of our animations in the game's list):

  v.nb_gs     ground speed in m/s, smoothed
  v.nb_spr    0..1 sprinting, smoothed
  v.nb_fwd    -1..1 walking direction against the body's facing (-1 = backwards)
  v.nb_side   0..1 how much of the movement is sideways
  v.nb_air    0..1 in the air, smoothed
  v.nb_airt   seconds in the air so far
  v.nb_vy     last vertical speed while in the air (for the landing)
  v.nb_lead   +1 / -1: which leg led the take-off
  v.nb_landt  seconds since the last landing, v.nb_landk its strength 0..1
  v.nb_l      landing spring (negative = knees bent, positive = small rebound), v.nb_lv its velocity
  v.nb_c      crouch amount (spring, so it eases in and out with a small overshoot)
  v.nb_cv     crouch spring velocity

Rotation conventions (measured on the game's skeleton): -x swings a limb
forwards, +z lifts the right arm/leg outwards, -z the left one.
"""

DT = "math.clamp(query.delta_time, 0.0, 0.05)"

# a stride cycle every ~11 distance units: slightly longer, calmer steps than the game's
PHASE = "(query.modified_distance_moved * 32.0)"
S = f"math.sin({PHASE})"
C = f"math.cos({PHASE})"

# ------------------------------------------------------------------ state update
STATE = "!query.is_in_ui ? { " + "; ".join([
    "t.dt = " + DT,
    # speed and sprint
    "v.nb_gs = math.lerp(v.nb_gs ?? 0.0, query.is_riding ? 0.0 : query.ground_speed, math.clamp(t.dt * 10.0, 0.0, 1.0))",
    "v.nb_spr = math.lerp(v.nb_spr ?? 0.0, query.is_sprinting ? 1.0 : 0.0, math.clamp(t.dt * 6.0, 0.0, 1.0))",
    # direction of travel against where the body faces
    "t.mx = query.position(0) - (v.nb_px ?? query.position(0))",
    "t.mz = query.position(2) - (v.nb_pz ?? query.position(2))",
    "v.nb_px = query.position(0)",
    "v.nb_pz = query.position(2)",
    "t.len = math.sqrt(t.mx * t.mx + t.mz * t.mz)",
    "t.yaw = query.body_y_rotation",
    "t.f = t.len > 0.004 ? (-t.mx * math.sin(t.yaw) + t.mz * math.cos(t.yaw)) / t.len : (v.nb_fwd ?? 1.0)",
    "t.sd = t.len > 0.004 ? math.abs(t.mx * math.cos(t.yaw) + t.mz * math.sin(t.yaw)) / t.len : (v.nb_side ?? 0.0)",
    "v.nb_fwd = math.lerp(v.nb_fwd ?? 1.0, t.f, math.clamp(t.dt * 9.0, 0.0, 1.0))",
    "v.nb_side = math.lerp(v.nb_side ?? 0.0, t.sd, math.clamp(t.dt * 9.0, 0.0, 1.0))",
    # air time, take-off leg, landing
    "t.grounded = query.is_on_ground || query.is_in_water || query.is_riding || query.is_gliding || query.is_sleeping || query.is_swimming",
    f"(!t.grounded && (v.nb_airt ?? 0.0) <= 0.0) ? {{ v.nb_lead = {S} >= 0.0 ? 1.0 : -1.0; }}",
    "!t.grounded ? { v.nb_airt = (v.nb_airt ?? 0.0) + t.dt; v.nb_vy = query.vertical_speed; }",
    "(t.grounded && (v.nb_airt ?? 0.0) > 0.0) ? { v.nb_landk = (v.nb_airt > 0.18 && !query.is_in_water) ? math.clamp((-(v.nb_vy ?? 0.0) - 2.0) / 12.0, 0.25, 1.0) : 0.0; v.nb_landt = 0.0; v.nb_airt = 0.0; v.nb_lv = (v.nb_lv ?? 0.0) - (30.0 * v.nb_landk + 18.0 * v.nb_landk * v.nb_landk) * (1.0 - 0.4 * math.clamp((v.nb_gs ?? 0.0) / 3.0, 0.0, 1.0)); }",
    "v.nb_landt = (v.nb_landt ?? 9.0) + t.dt",
    # landing spring: pushed down by the impact, it absorbs, rebounds a little and settles
    "v.nb_lv = (v.nb_lv ?? 0.0) + (-180.0 * (v.nb_l ?? 0.0) - 12.0 * (v.nb_lv ?? 0.0)) * t.dt",
    "v.nb_l = math.clamp((v.nb_l ?? 0.0) + v.nb_lv * t.dt, -1.4, 0.6)",
    "v.nb_air = math.lerp(v.nb_air ?? 0.0, t.grounded ? 0.0 : 1.0, math.clamp(t.dt * (t.grounded ? 16.0 : 28.0), 0.0, 1.0))",
    # crouch spring: eases down and back up with a small natural overshoot
    "t.ct = (query.is_sneaking && !query.is_in_water && !query.is_swimming && !query.is_riding && !query.is_gliding && !query.is_sleeping && !query.is_crawling && !query.is_in_ui) ? 1.0 : 0.0",
    "v.nb_cv = (v.nb_cv ?? 0.0) + (190.0 * (t.ct - (v.nb_c ?? 0.0)) - 17.0 * (v.nb_cv ?? 0.0)) * t.dt",
    "v.nb_c = math.clamp((v.nb_c ?? 0.0) + v.nb_cv * t.dt, -0.12, 1.12)",
]) + "; }; return 0.0;"

# ------------------------------------------------------------------ shared weights
UI = "(query.is_in_ui ? 0.0 : 1.0)"
GROUNDED = "(1.0 - (v.nb_air ?? 0.0))"
# how much walking there is: 0 standing .. 1 full walk (sneak-walk ~0.4)
W = f"(math.clamp((v.nb_gs ?? 0.0) / 3.4, 0.0, 1.0) * {GROUNDED} * ((query.is_riding || query.is_gliding || query.is_swimming || query.is_crawling || query.is_sleeping) ? 0.0 : 1.0))"
SPR = f"((v.nb_spr ?? 0.0) * {W})"
# walking direction: +1 forwards, -1 backwards, ~0 pure sideways
K = "math.clamp((v.nb_fwd ?? 1.0) * 2.5, -1.0, 1.0)"
BACK = f"(math.clamp(-(v.nb_fwd ?? 1.0), 0.0, 1.0) * {W})"
SIDE = f"((v.nb_side ?? 0.0) * {W})"
CR = "(v.nb_c ?? 0.0)"
# rising quickly when standing up (spring velocity), for the stand-up accent
RISE = "math.clamp(-(v.nb_cv ?? 0.0) / 6.0, 0.0, 1.0)"

AIRW = f"((v.nb_air ?? 0.0) * {UI})"
VY = "query.vertical_speed"
AT = "(v.nb_airt ?? 0.0)"
LIFE = "query.life_time"
LEADL = "((v.nb_lead ?? 1.0) > 0.0 ? 1.0 : 0.0)"
LEADR = f"(1.0 - {LEADL})"
JS = "(1.0 + (v.nb_spr ?? 0.0) * 0.35)"
# 0 = jumping on the spot, 1 = jumping on the move
MOV = "math.clamp((v.nb_gs ?? 0.0) / 3.0, 0.0, 1.0)"


def smooth(k):
    return f"(({k}) * ({k}) * (3.0 - 2.0 * ({k})))"


# ---- jump phases (weights, each 0..1, already multiplied by being in the air)
# 1 launch: the first moment after leaving the ground, legs still pushing, body stretched
LAUNCH = f"({AIRW} * math.clamp(1.0 - {AT} / 0.12, 0.0, 1.0) * ({VY} > 0.0 ? 1.0 : 0.0))"
# 3 unfold: on the way down the legs reach for the ground
UNF = f"math.clamp((-{VY} - 0.5) / 5.0, 0.0, 1.0)"
# long falls only: arms wheel and legs pedal (a normal jump never gets here)
FLAIL = f"(math.clamp(({AT} - 0.3) / 0.3, 0.0, 1.0) * math.clamp((-{VY} - 8.0) / 5.0, 0.0, 1.0))"
# 2 tuck: knees pulled up, eased in over ~0.15 s, gone as the unfold takes over
TUCK = f"({AIRW} * {smooth(f'math.clamp(({AT} - 0.03) / 0.15, 0.0, 1.0)')} * (1.0 - {UNF}))"
UNFW = f"({AIRW} * {UNF} * (1.0 - {FLAIL}))"
FLW = f"({AIRW} * {FLAIL})"
# 4 landing spring
L = f"(math.clamp(-(v.nb_l ?? 0.0), 0.0, 1.3) * {UI})"
REB = f"(math.clamp((v.nb_l ?? 0.0), 0.0, 0.5) * {UI})"


def mov(standing, moving):
    return f"math.lerp({standing}, {moving}, {MOV})"


def jump(launch, tuck, unfold, flail):
    return f"({LAUNCH} * ({launch}) + {TUCK} * ({tuck}) + {UNFW} * ({unfold}) + {FLW} * ({flail}))"


def leg(side):
    """side: +1 left leg, -1 right leg"""
    sw = "" if side > 0 else "-"
    lift = f"math.max(0.0, {sw}{C})"            # this leg is in its swing phase
    lead = LEADL if side > 0 else LEADR
    trail = LEADR if side > 0 else LEADL
    ph = "0.0" if side > 0 else "180.0"

    def lt(a, b):
        return f"({lead} * {a} + {trail} * {b})"
    # crouched steps are slow but still clearly visible, so they get extra swing
    amp = f"((24.0 + 16.0 * (v.nb_spr ?? 0.0)) * (1.0 - 0.12 * {BACK} / math.max({W}, 0.01)) * (1.0 + 1.1 * math.clamp({CR}, 0.0, 1.0)) * {W})"
    # The legs have no knee: a bent knee is shown by lifting the leg (shorter) and
    # bringing it forward, with only a little rotation.
    jx = jump(
        "12.0",                                                               # launch: legs straight, pushing down and back
        mov(lt("-30.0", "-16.0"), f"({lt('-46.0', '30.0')} * {JS})"),        # tuck: both knees up / a running leap
        mov("-9.0", lt("-24.0", "8.0")),                                      # unfold: reaching for the ground
        f"(-8.0 + 28.0 * math.sin({LIFE} * 520.0 + {ph}))",                   # long fall: pedalling
    )
    jy = jump("0.0", mov(lt("3.6", "2.4"), lt("3.6", "0.4")), mov("0.6", lt("0.8", "0.0")),
              f"(1.2 * math.max(0.0, math.sin({LIFE} * 520.0 + {ph} + 90.0)))")
    jz = jump("0.0", mov(lt("-2.6", "-1.4"), lt("-3.0", "0.6")), mov("-0.4", lt("-1.2", "0.0")), "0.0")
    jspread = jump("0.0", "3.0", "4.0", f"(7.0 + 4.0 * math.sin({LIFE} * 430.0 + {ph}))")
    rot_x = (
        f"{'-' if side > 0 else ''}{amp} * {S} * {K}"                     # stride
        f" - 28.0 * {CR}"                                                   # crouch: legs stay upright under the tilted body
        f" + {jx}"
        f" - 10.0 * {L}"                                                    # landing: knees forward
    )
    rot_z = (
        f"{side * -0.1} + {side * -1.0} * ({SIDE} * 9.0 * math.max(0.0, {sw}{S})"  # sidestep: open the moving leg
        f" + 2.5 * {CR} + {jspread} + 3.0 * {L})"
    )
    rot_y = f"{side * -0.1} + {side * -8.0} * {L}"                          # feet turn out as the knees bend
    pos = [
        0.0,
        f"({lift} * (1.3 + 1.6 * (v.nb_spr ?? 0.0)) * {W}) + {jy} + 2.2 * {L}",   # foot lifts in the stride / knee bends
        f"-{lift} * 1.0 * {K} * {W} + {jz} - 1.6 * {L}",                         # and travels forward with it
    ]
    return {"rotation": [rot_x, rot_y, rot_z], "position": pos}


def arm(side):
    """side: +1 left arm, -1 right arm"""
    lead = LEADL if side > 0 else LEADR     # the leg on this side led the jump
    other = LEADR if side > 0 else LEADL
    ph = "0.0" if side > 0 else "180.0"

    def lt(a, b):
        return f"({lead} * {a} + {other} * {b})"
    amp = f"((20.0 + 30.0 * (v.nb_spr ?? 0.0)) * (1.0 - 0.35 * {BACK} / math.max({W}, 0.01)) * {W})"
    swing = f"math.sin({PHASE} + 12.0)"
    jx = jump(
        mov("-78.0", f"({lt('20.0', '-62.0')} * {JS})"),        # launch: arms drive up (running: the opposite arm)
        mov("-42.0", f"({lt('26.0', '-46.0')} * {JS})"),        # tuck: arms up and forward for balance
        mov("-20.0", "-14.0"),                                   # unfold: arms come down and open
        f"(-70.0 + 55.0 * math.sin({LIFE} * 560.0 + {ph}))",     # long fall: wheeling
    )
    jout = jump("6.0", mov("16.0", "8.0"), "32.0", f"(50.0 + 18.0 * math.sin({LIFE} * 720.0 + {ph}))")
    rot_x = (
        f"{'' if side > 0 else '-'}{amp} * {swing} * {K}"                   # opposite to the leg on this side
        f" - 12.0 * {SPR}"                                                  # running: arms carried higher
        f" - 17.0 * {CR}"                                                   # crouch: hands low and ready
        f" + 10.0 * {RISE}"                                                 # standing up: arms swing back a touch
        f" + {jx}"
        f" - 24.0 * {L} + 10.0 * {REB}"                                     # landing: arms forward, then a small swing back
    )
    out = f"(2.0 + 2.0 * {SPR} + {jout} + 12.0 * {L} + 5.0 * {CR})"
    rot_z = f"{'-' if side > 0 else ''}{out}"
    rot_y = f"{'' if side > 0 else '-'}math.sin({PHASE}) * 5.0 * {W}"
    return {"rotation": [rot_x, rot_y, rot_z]}


def build():
    lean = jump("-6.0", mov("6.0", f"(12.0 * {K})"), "4.0", f"(-8.0 + 3.0 * math.sin({LIFE} * 400.0))")
    waist_rx = f"{UI} * (7.0 * {SPR} - 3.5 * {BACK} - 4.0 * {RISE}) + {lean} + 14.0 * {L} - 3.0 * {REB}"
    waist_ry = f"{UI} * 8.0 * {S} * {K} * {W}"
    waist_rz = f"{UI} * 2.2 * {C} * {W}"
    waist_py = (f"-(0.9 + 0.7 * (v.nb_spr ?? 0.0)) * {S} * {S} * {W}"     # lowest when the feet are apart
                f" - 4.0 * {L} + 0.8 * {REB}")
    head_x = f"1.0 * math.cos({PHASE} * 2.0) * {W} + 10.0 * {L} + " + jump("-6.0", "-3.0", "10.0", "12.0")
    anims = {
        # move.arms is the first of our animations each frame: it also updates the state
        "animation.player.move.arms": {
            "loop": True,
            "bones": {
                "root": {"position": [STATE, 0.0, 0.0]},
                "leftarm": arm(1),
                "rightarm": arm(-1),
            },
        },
        "animation.player.move.legs": {
            "loop": True,
            "bones": {
                "leftleg": leg(1),
                "rightleg": leg(-1),
                "waist": {"rotation": [waist_rx, waist_ry, waist_rz], "position": [0.0, waist_py, 0.0]},
                # head stays steady while the torso twists; small nod on landing
                "head": {"rotation": [head_x,
                                      f"-5.0 * {S} * {K} * {W}", 0.0],
                         "position": [0.0, f"-1.0 * {CR}", 0.0]},
                "body": {"position": [0.0, f"-2.0 * {CR}", 0.0]},
                # crouch: the whole figure tilts forward from the feet with the hips set back
                # (the same frame the game's camera and hit box expect), blended by the spring
                "root": {"rotation": [f"28.0 * {CR}", 0.0, 0.0],
                         "position": [0.0, f"1.25 * {CR}", f"9.0 * {CR}"],
                         # take-off stretch and landing squash, from the feet
                         "scale": [f"1.0 - 0.02 * {LAUNCH} + 0.03 * {L} - 0.01 * {REB}",
                                   f"1.0 + 0.05 * {LAUNCH} - 0.06 * {L} + 0.02 * {REB}",
                                   f"1.0 - 0.02 * {LAUNCH} + 0.03 * {L} - 0.01 * {REB}"]},
            },
        },
        # the game's own crouch pose snaps on and off; ours lives in move.legs above
        "animation.player.sneaking": {"loop": True, "bones": {}},
    }
    return anims
