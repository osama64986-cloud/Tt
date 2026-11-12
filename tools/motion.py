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
  v.nb_side   0..1 how much of the movement is sideways, v.nb_ss the same with its sign
  v.nb_air    0..1 in the air, smoothed
  v.nb_airt   seconds in the air so far
  v.nb_vy     last vertical speed while in the air (for the landing)
  v.nb_lead   +1 / -1: which leg led the take-off
  v.nb_landt  seconds since the last landing, v.nb_landk its strength 0..1
  v.nb_l      landing spring (negative = knees bent, positive = small rebound), v.nb_lv its velocity
  v.nb_c      crouch amount (spring, so it eases in and out with a small overshoot)
  v.nb_cv     crouch spring velocity
  v.nb_yr     turning speed (deg/s), v.nb_swt / v.nb_sws the shoulder side it asks for (target / eased)

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
    "t.ss = t.len > 0.004 ? (t.mx * math.cos(t.yaw) + t.mz * math.sin(t.yaw)) / t.len : (v.nb_ss ?? 0.0)",
    "v.nb_ss = math.lerp(v.nb_ss ?? 0.0, t.ss, math.clamp(t.dt * 7.0, 0.0, 1.0))",
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
    # turning (for the shoulder view's "both" setting): which way the camera was last
    # turned decides the side; small movements keep the current side
    "t.hy = query.head_y_rotation(0)",
    "t.dy = math.mod(t.hy - (v.nb_hy ?? t.hy) + 540.0, 360.0) - 180.0",
    "v.nb_hy = t.hy",
    "v.nb_yr = math.lerp(v.nb_yr ?? 0.0, t.dy / math.max(t.dt, 0.001), math.clamp(t.dt * 10.0, 0.0, 1.0))",
    "v.nb_swt = v.nb_yr > 70.0 ? 1.0 : (v.nb_yr < -70.0 ? -1.0 : (v.nb_swt ?? 1.0))",
    "v.nb_sws = math.lerp(v.nb_sws ?? 1.0, v.nb_swt, math.clamp(t.dt * 6.0, 0.0, 1.0))",
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


# ---- in the air
# The legs never kick forward.  Jumping on the spot they hang almost straight
# with one knee slightly bent; jumping on the move they trail behind while the
# torso leans into the jump, so the whole body makes one leaping arc.  Moving
# sideways the legs swing out to the side they come from.
FWD = "(v.nb_fwd ?? 1.0)"
SS = "(v.nb_ss ?? 0.0)"
MV = "math.min((v.nb_gs ?? 0.0) / 4.0, 1.0)"
BREATH = f"math.cos({LIFE} * 245.0)"
# long falls only: arms open wide and wave a little
FLAIL = f"(math.clamp(({AT} - 0.35) / 0.35, 0.0, 1.0) * math.clamp((-{VY} - 8.0) / 5.0, 0.0, 1.0))"
# landing spring
L = f"(math.clamp(-(v.nb_l ?? 0.0), 0.0, 1.3) * {UI})"
REB = f"(math.clamp((v.nb_l ?? 0.0), 0.0, 0.5) * {UI})"


def inair(expr):
    return f"({AIRW} * ({expr}))"


def leg(side):
    """side: +1 left leg, -1 right leg"""
    sw = "" if side > 0 else "-"
    lift = f"math.max(0.0, {sw}{C})"            # this leg is in its swing phase
    lead = LEADL if side > 0 else LEADR         # the leg that led the take-off keeps its knee a little bent
    # crouched steps are slow but still clearly visible, so they get extra swing
    amp = f"((24.0 + 16.0 * (v.nb_spr ?? 0.0)) * (1.0 - 0.12 * {BACK} / math.max({W}, 0.01)) * (1.0 + 1.1 * math.clamp({CR}, 0.0, 1.0)) * {W})"
    back = "34.0" if side > 0 else "28.0"       # the two legs trail by slightly different amounts
    air_x = inair(f"({lead} * 7.0 + (1.0 - {lead}) * 5.0) - 2.0 * {BREATH} + {FWD} * {back} * {MV}")
    air_z = inair(f"({side * -4.0} - 34.0 * {SS}) * {MV}")
    air_y = inair(f"{lead} * 3.0 * (1.0 - 0.5 * {MV}) + (0.5 - 0.5 * {FWD}) * 1.5 * {MV}")
    air_fz = inair(f"{lead} * -3.0 * (1.0 - 0.5 * {MV}) + {FWD} * -1.5 * {MV}")
    rot_x = (
        f"{'-' if side > 0 else ''}{amp} * {S} * {K}"                     # stride
        f" - 28.0 * {CR}"                                                   # crouch: legs stay upright under the tilted body
        f" + {air_x}"
        f" + 10.0 * {L}"                                                    # landing: thighs slope back, feet stay forward
    )
    rot_z = (
        f"{side * -0.1} + {side * -1.0} * ({SIDE} * 9.0 * math.max(0.0, {sw}{S})"  # sidestep: open the moving leg
        f" + 2.5 * {CR} + 2.0 * {L}) + {air_z}"
    )
    rot_y = f"{side * -0.1} + {side * -10.0} * {L}"                         # toes turn out as the knees bend
    pos = [
        f"{side * 0.5} * {L}",
        f"({lift} * (1.3 + 1.6 * (v.nb_spr ?? 0.0)) * {W}) + {air_y} + 0.8 * {L}",
        f"-{lift} * 1.0 * {K} * {W} + {air_fz} - 2.0 * {L}",
    ]
    return {"rotation": [rot_x, rot_y, rot_z], "position": pos}


def arm(side):
    """side: +1 left arm, -1 right arm"""
    ph = "0.0" if side > 0 else "180.0"
    amp = f"((20.0 + 30.0 * (v.nb_spr ?? 0.0)) * (1.0 - 0.35 * {BACK} / math.max({W}, 0.01)) * {W})"
    swing = f"math.sin({PHASE} + 12.0)"
    # in the air: arms sweep back with the leap (forward when jumping backwards), open a little
    air_x = inair(f"-2.0 * {BREATH} + {FWD} * 18.0 * {MV} - {FLAIL} * (40.0 + 30.0 * math.sin({LIFE} * 380.0 + {ph}))")
    air_out = inair(f"7.0 + {SS} * {side * 7.0} * {MV} + {FLAIL} * (38.0 + 10.0 * math.sin({LIFE} * 500.0 + {ph}))")
    rot_x = (
        f"{'' if side > 0 else '-'}{amp} * {swing} * {K}"                   # opposite to the leg on this side
        f" - 12.0 * {SPR}"                                                  # running: arms carried higher
        f" - 17.0 * {CR}"                                                   # crouch: hands low and ready
        f" + 10.0 * {RISE}"                                                 # standing up: arms swing back a touch
        f" + {air_x}"
        f" - 20.0 * {L} + 8.0 * {REB}"                                      # landing: arms forward, then a small swing back
    )
    out = f"(2.0 + 2.0 * {SPR} + {air_out} + 9.0 * {L} + 5.0 * {CR})"
    rot_z = f"{'-' if side > 0 else ''}{out}"
    rot_y = f"{'' if side > 0 else '-'}(math.sin({PHASE}) * 5.0 * {W} + {AIRW} * 7.0)"
    return {"rotation": [rot_x, rot_y, rot_z], "position": [0.0, 0.0, inair(f"{FWD} * 1.25 * {MV}")]}


# Shoulder view (third person, your own screen only): the character is drawn to the side so
# the middle of the screen is free.  Defaults: on, character on the left, 0.8 block.  The
# in-game pack settings (read in nabd_shoulder.animation.json) can change these through
# v.nb_sh_on / v.nb_sh_side / v.nb_sh_amt; if that file is not loaded, the defaults apply.
SHOULDER = ("((query.is_local_player && !query.is_first_person && !query.is_in_ui && (v.nb_sh_on ?? 1.0) > 0.5)"
            " ? -(v.nb_sh_side ?? 1.0) * (v.nb_sh_amt ?? 0.8) * 17.0667 : 0.0)")


def build():
    # in the air the torso leans into the leap (back when jumping backwards) and tips to the side it moves to
    # the torso stays upright in the air (only a slight breath); the legs and arms tell the jump
    lean = inair(f"2.0 * math.cos({LIFE} * 245.0 - 90.0)")
    tip = "0.0"
    waist_rx = f"{UI} * (7.0 * {SPR} - 3.5 * {BACK} - 4.0 * {RISE}) + {lean} + 12.0 * {L} - 3.0 * {REB}"
    waist_ry = f"{UI} * 8.0 * {S} * {K} * {W}"
    waist_rz = f"{UI} * 2.2 * {C} * {W} + {tip}"
    waist_py = (f"-(0.9 + 0.7 * (v.nb_spr ?? 0.0)) * {S} * {S} * {W}"     # lowest when the feet are apart
                f" - 4.0 * {L} + 0.8 * {REB}")
    waist_pz = f"1.0 * {L}"
    head_x = f"1.0 * math.cos({PHASE} * 2.0) * {W} + 12.0 * {L} + " + inair(f"4.0 + 4.0 * {FLAIL}")
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
                "waist": {"rotation": [waist_rx, waist_ry, waist_rz], "position": [0.0, waist_py, waist_pz]},
                # head stays steady while the torso twists; small nod on landing
                "head": {"rotation": [head_x,
                                      f"-5.0 * {S} * {K} * {W}", 0.0],
                         "position": [0.0, f"-1.0 * {CR}", 0.0]},
                "body": {"position": [0.0, f"-2.0 * {CR}", 0.0]},
                # crouch: the whole figure tilts forward from the feet with the hips set back
                # (the same frame the game's camera and hit box expect), blended by the spring
                "root": {"rotation": [f"28.0 * {CR}", 0.0, 0.0],
                         "position": [SHOULDER, f"1.25 * {CR}", f"9.0 * {CR}"],
                         # take-off stretch and landing squash, from the feet
                         "scale": [f"1.0 + 0.025 * {L} - 0.01 * {REB}",
                                   f"1.0 - 0.05 * {L} + 0.02 * {REB}",
                                   f"1.0 + 0.025 * {L} - 0.01 * {REB}"]},
            },
        },
        # the game's own crouch pose snaps on and off; ours lives in move.legs above
        "animation.player.sneaking": {"loop": True, "bones": {}},
    }
    return anims
