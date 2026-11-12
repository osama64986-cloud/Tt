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
    "(t.grounded && (v.nb_airt ?? 0.0) > 0.0) ? { v.nb_landk = (v.nb_airt > 0.18 && !query.is_in_water) ? math.clamp((-(v.nb_vy ?? 0.0) - 2.0) / 12.0, 0.25, 1.0) : 0.0; v.nb_landt = 0.0; v.nb_airt = 0.0; }",
    "v.nb_landt = (v.nb_landt ?? 9.0) + t.dt",
    "v.nb_air = math.lerp(v.nb_air ?? 0.0, t.grounded ? 0.0 : 1.0, math.clamp(t.dt * (t.grounded ? 16.0 : 11.0), 0.0, 1.0))",
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
JS = "(1.0 + (v.nb_spr ?? 0.0) * 0.4)"
# 0 = jumping on the spot, 1 = jumping on the move
MOV = "math.clamp((v.nb_gs ?? 0.0) / 3.0, 0.0, 1.0)"
# phases in the air
TK = f"(math.clamp(1.0 - {AT} / 0.16, 0.0, 1.0) * ({VY} > 0.5 ? 1.0 : 0.0))"          # take-off spring
DESC = f"math.clamp((-{VY} - 0.5) / 5.0, 0.0, 1.0)"                                    # 0 rising/top .. 1 coming down
FLAIL = f"(math.clamp(({AT} - 0.3) / 0.3, 0.0, 1.0) * math.clamp((-{VY} - 8.0) / 5.0, 0.0, 1.0))"  # long fall (not normal jumps)


def air(take, rise, desc, flail):
    """blend the four air poses (Molang strings) by phase, weighted by being in the air"""
    return (f"({AIRW} * ({TK} * ({take}) + (1.0 - {TK}) * "
            f"math.lerp(math.lerp({rise}, {desc}, {DESC}), {flail}, {FLAIL})))")


def mov(standing, moving):
    return f"(math.lerp({standing}, {moving}, {MOV}))"


# landing: a quick drop (50 ms), a hold that grows with the impact, then an eased recovery;
# softer when landing on the run so the stride is not interrupted
_LT, _LK = "(v.nb_landt ?? 9.0)", "(v.nb_landk ?? 0.0)"
_HOLD = f"(0.04 + 0.08 * {_LK})"
_DEC = f"(0.28 + 0.35 * {_LK})"
LAND = (f"({_LK} * ({_LT} < 0.05 ? {_LT} / 0.05 : ({_LT} < 0.05 + {_HOLD} ? 1.0 : "
        f"math.pow(math.clamp(1.0 - ({_LT} - 0.05 - {_HOLD}) / {_DEC}, 0.0, 1.0), 2.0)))"
        f" * (1.0 - 0.45 * {MOV}) * {UI})")


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
    air_x = air(
        lt("6.0", "12.0"),                                                   # take-off: both legs push back
        mov(lt("-38.0", "4.0"), f"({lt('-42.0', '26.0')} * {JS})"),          # rising: a knee comes up (on the move: a leap)
        mov(lt("-14.0", "-2.0"), lt("-20.0", "12.0")),                       # coming down: legs gather under the body
        f"(-8.0 + 28.0 * math.sin({LIFE} * 520.0 + {ph}))",                  # long fall: pedalling
    )
    rot_x = (
        f"{'-' if side > 0 else ''}{amp} * {S} * {K}"                     # stride
        f" - 28.0 * {CR}"                                                   # crouch: legs stay upright under the tilted body
        f" + {air_x}"
        f" - 26.0 * {LAND}"                                                 # landing: knees give
    )
    air_z = air("0.0", "2.0", "5.0", f"(7.0 + 4.0 * math.sin({LIFE} * 430.0 + {ph}))")
    rot_z = (
        f"{side * -0.1} + {side * -1.0} * ({SIDE} * 9.0 * math.max(0.0, {sw}{S})"  # sidestep: open the moving leg
        f" + 2.5 * {CR} + {air_z} + 3.0 * {LAND})"
    )
    rot_y = f"{side * -0.1} + {side * -10.0} * {LAND}"                      # feet turn out as the knees give
    air_lift = air("0.0", lt("2.2", "0.0"), lt("0.8", "0.0"), f"(1.2 * math.max(0.0, math.sin({LIFE} * 520.0 + {ph} + 90.0)))")
    air_fwd = air("0.0", lt("-1.5", "0.5"), "0.0", "0.0")
    pos = [
        0.0,
        f"({lift} * (1.3 + 1.6 * (v.nb_spr ?? 0.0)) * {W}) + {air_lift}",  # foot lifts while it swings
        f"-{lift} * 1.0 * {K} * {W} + {air_fwd} - 2.0 * {LAND}",          # and travels with the step
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
    air_x = air(
        mov("-55.0", f"({lt('18.0', '-48.0')} * {JS})"),                      # take-off: arms swing up (on the move: opposite arm forward)
        mov("-18.0", f"({lt('22.0', '-36.0')} * {JS})"),                      # rising: balance
        "-28.0",                                                              # coming down: arms rise to brace
        f"(-70.0 + 55.0 * math.sin({LIFE} * 560.0 + {ph}))",                  # long fall: windmilling
    )
    rot_x = (
        f"{'' if side > 0 else '-'}{amp} * {swing} * {K}"                   # opposite to the leg on this side
        f" - 12.0 * {SPR}"                                                  # running: arms carried higher
        f" - 17.0 * {CR}"                                                   # crouch: hands low and ready
        f" + 10.0 * {RISE}"                                                 # standing up: arms swing back a touch
        f" + {air_x}"
        f" - 26.0 * {LAND}"                                                 # landing: arms come forward for balance
    )
    air_out = air("4.0", mov("22.0", "10.0"), "30.0", f"(50.0 + 18.0 * math.sin({LIFE} * 720.0 + {ph}))")
    out = f"(2.0 + 2.0 * {SPR} + {air_out} + 10.0 * {LAND} + 5.0 * {CR})"
    rot_z = f"{'-' if side > 0 else ''}{out}"
    rot_y = f"{'' if side > 0 else '-'}math.sin({PHASE}) * 5.0 * {W}"
    return {"rotation": [rot_x, rot_y, rot_z]}


def build():
    air_lean = air("-5.0", f"(3.0 + 10.0 * {MOV} * {K})", "5.0", f"(-8.0 + 3.0 * math.sin({LIFE} * 400.0))")
    waist_rx = (f"{UI} * (7.0 * {SPR} - 3.5 * {BACK} - 4.0 * {RISE}) + {air_lean} + 16.0 * {LAND}")
    waist_ry = f"{UI} * 8.0 * {S} * {K} * {W}"
    waist_rz = f"{UI} * 2.2 * {C} * {W}"
    waist_py = (f"-(0.9 + 0.7 * (v.nb_spr ?? 0.0)) * {S} * {S} * {W}"     # lowest when the feet are apart
                f" - 4.5 * {LAND}")
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
                "head": {"rotation": [f"1.0 * math.cos({PHASE} * 2.0) * {W} + 14.0 * {LAND} + " + air("0.0", "-4.0", "8.0", "12.0"),
                                      f"-5.0 * {S} * {K} * {W}", 0.0],
                         "position": [0.0, f"-1.0 * {CR}", 0.0]},
                "body": {"position": [0.0, f"-2.0 * {CR}", 0.0]},
                # crouch: the whole figure tilts forward from the feet with the hips set back
                # (the same frame the game's camera and hit box expect), blended by the spring
                "root": {"rotation": [f"28.0 * {CR}", 0.0, 0.0],
                         "position": [0.0, f"1.25 * {CR}", f"9.0 * {CR}"],
                         # take-off stretch and landing squash, from the feet
                         "scale": [f"1.0 - 0.02 * {AIRW} * {TK} + 0.035 * {LAND}",
                                   f"1.0 + 0.05 * {AIRW} * {TK} - 0.07 * {LAND}",
                                   f"1.0 - 0.02 * {AIRW} * {TK} + 0.035 * {LAND}"]},
            },
        },
        # the game's own crouch pose snaps on and off; ours lives in move.legs above
        "animation.player.sneaking": {"loop": True, "bones": {}},
    }
    return anims
