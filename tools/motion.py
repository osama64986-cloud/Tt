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
UP = f"({AIRW} * math.clamp(query.vertical_speed / 3.0, 0.0, 1.0))"
TOP = f"({AIRW} * (1.0 - math.clamp(math.abs(query.vertical_speed) / 5.0, 0.0, 1.0)))"
FALL = f"({AIRW} * math.clamp((-query.vertical_speed - 1.0) / 6.0, 0.0, 1.0))"
LONGFALL = f"({AIRW} * math.clamp(((v.nb_airt ?? 0.0) - 0.7) / 0.5, 0.0, 1.0))"
LEADL = "((v.nb_lead ?? 1.0) > 0.0 ? 1.0 : 0.0)"
LEADR = f"(1.0 - {LEADL})"
JUMPSTRIDE = "(1.0 + (v.nb_spr ?? 0.0) * 0.5)"
# 0 = jumping on the spot (both knees tuck together), 1 = jumping on the move (a stride)
MOV = "math.clamp((v.nb_gs ?? 0.0) / 3.0, 0.0, 1.0)"
# landing: quick dip (50 ms) then a calm recovery (~0.35 s), scaled by the impact
LAND = ("((v.nb_landk ?? 0.0) * ((v.nb_landt ?? 9.0) < 0.06 ? (v.nb_landt ?? 9.0) / 0.06 : "
        "math.pow(math.clamp(1.0 - ((v.nb_landt ?? 9.0) - 0.06) / 0.42, 0.0, 1.0), 2.0)) * " + UI + ")")


def leg(side):
    """side: +1 left leg, -1 right leg"""
    sw = "" if side > 0 else "-"
    lift = f"math.max(0.0, {sw}{C})"            # this leg is in its swing phase
    lead = LEADL if side > 0 else LEADR
    trail = LEADR if side > 0 else LEADL
    # crouched steps are slow but still clearly visible, so they get extra swing
    amp = f"((24.0 + 16.0 * (v.nb_spr ?? 0.0)) * (1.0 - 0.12 * {BACK} / math.max({W}, 0.01)) * (1.0 + 1.1 * math.clamp({CR}, 0.0, 1.0)) * {W})"
    rot_x = (
        f"{'-' if side > 0 else ''}{amp} * {S} * {K}"                     # stride
        f" - 28.0 * {CR}"                                                   # crouch: legs stay upright under the tilted body
        # take-off: on the move the lead knee drives up and the other leg pushes back;
        # on the spot both knees come up together
        f" + {UP} * ({MOV} * ({lead} * -40.0 + {trail} * 14.0) * {JUMPSTRIDE} - (1.0 - {MOV}) * 26.0)"
        f" + {TOP} * ({MOV} * ({lead} * -26.0 + {trail} * 9.0) - (1.0 - {MOV}) * 32.0)"     # gathered at the top
        f" + {FALL} * ({MOV} * ({lead} * -17.0 + {trail} * 11.0) - (1.0 - {MOV}) * 9.0)"    # legs reach for the ground
        f" - 18.0 * {LAND}"                                                 # landing: knees give
    )
    rot_z = (
        f"{side * -0.1} + {side * -1.0} * ({SIDE} * 9.0 * math.max(0.0, {sw}{S})"  # sidestep: open the moving leg
        f" + 2.5 * {CR} + 3.0 * {TOP} + 4.0 * {FALL} + 2.0 * {LAND})"
    )
    pos = [
        0.0,
        f"({lift} * (1.3 + 1.6 * (v.nb_spr ?? 0.0)) * {W}) + {UP} * {lead} * 1.5",     # foot lifts while it swings
        f"-{lift} * 1.0 * {K} * {W}",                                       # and travels with the step
    ]
    return {"rotation": [rot_x, f"{side * -0.1}", rot_z], "position": pos}


def arm(side):
    """side: +1 left arm, -1 right arm"""
    lead = LEADL if side > 0 else LEADR
    amp = f"((20.0 + 30.0 * (v.nb_spr ?? 0.0)) * (1.0 - 0.35 * {BACK} / math.max({W}, 0.01)) * {W})"
    swing = f"math.sin({PHASE} + 12.0)"
    rot_x = (
        f"{'' if side > 0 else '-'}{amp} * {swing} * {K}"                   # opposite to the leg on this side
        f" - 12.0 * {SPR}"                                                  # running: arms carried higher
        f" - 17.0 * {CR}"                                                   # crouch: hands low and ready
        f" + 10.0 * {RISE}"                                                 # standing up: arms swing back a touch
        # take-off: arms drive up (on the move the arm opposite the lead leg goes further)
        f" + {UP} * ({MOV} * ({lead} * 16.0 - 30.0) * {JUMPSTRIDE} - (1.0 - {MOV}) * 42.0)"
        f" - 14.0 * {TOP} - 18.0 * {FALL}"
        f" - 16.0 * {LAND}"                                                 # landing: arms come forward for balance
    )
    out = (f"(2.0 + 2.0 * {SPR} + 5.0 * {UP} + 10.0 * {TOP} + 8.0 * {FALL} + 26.0 * {LONGFALL}"
           f" + 7.0 * {LAND} + 5.0 * {CR})")
    rot_z = f"{'-' if side > 0 else ''}{out}"
    rot_y = f"{'' if side > 0 else '-'}math.sin({PHASE}) * 5.0 * {W}"
    return {"rotation": [rot_x, rot_y, rot_z]}


def build():
    waist_rx = (f"{UI} * (7.0 * {SPR} - 3.5 * {BACK} - 4.0 * {UP} + 5.0 * {TOP} + 4.0 * {FALL} + 10.0 * {LAND}"
                f" - 4.0 * {RISE})")
    waist_ry = f"{UI} * 8.0 * {S} * {K} * {W}"
    waist_rz = f"{UI} * 2.2 * {C} * {W}"
    waist_py = (f"-(0.9 + 0.7 * (v.nb_spr ?? 0.0)) * {S} * {S} * {W}"     # lowest when the feet are apart
                f" - 2.8 * {LAND}")
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
                "head": {"rotation": [f"1.0 * math.cos({PHASE} * 2.0) * {W} + 7.0 * {LAND}",
                                      f"-5.0 * {S} * {K} * {W}", 0.0],
                         "position": [0.0, f"-1.0 * {CR}", 0.0]},
                "body": {"position": [0.0, f"-2.0 * {CR}", 0.0]},
                # crouch: the whole figure tilts forward from the feet with the hips set back
                # (the same frame the game's camera and hit box expect), blended by the spring
                "root": {"rotation": [f"28.0 * {CR}", 0.0, 0.0],
                         "position": [0.0, f"1.25 * {CR}", f"9.0 * {CR}"]},
            },
        },
        # the game's own crouch pose snaps on and off; ours lives in move.legs above
        "animation.player.sneaking": {"loop": True, "bones": {}},
    }
    return anims
