"""Nabd movement system: walking, running, walking backwards and sideways,
jumping and falling, crouching, idle life and turning on the spot.

Stateless on purpose: every value is read straight from the game's queries
each frame (no variables carried between frames), so it works the same on
every game version and next to other add-ons.  It runs inside the animations
the game's player already plays (move.arms, move.legs, sneaking); no player
entity file is replaced.

Rotation conventions (measured on the game's skeleton): -x swings a limb
forwards, +z lifts the right arm/leg outwards, -z the left one.
"""

# a stride cycle every ~11 distance units: slightly longer, calmer steps than the game's
PHASE = "(query.modified_distance_moved * 32.0)"
S = f"math.sin({PHASE})"
C = f"math.cos({PHASE})"
LIFE = "query.life_time"

# ------------------------------------------------------------------ what the player is doing
UI = "((query.is_in_ui || query.is_emoting) ? 0.0 : 1.0)"
BUSY = "(query.is_riding || query.is_gliding || query.is_swimming || query.is_crawling || query.is_sleeping || query.is_emoting)"
CALM = f"({BUSY} ? 0.0 : 1.0)"
GROUNDED = "((query.is_on_ground || query.is_in_water) ? 1.0 : 0.0)"
SPEED = "query.ground_speed"
# how much walking there is: 0 standing .. 1 full walk (sneak-walk ~0.4)
W = f"(math.clamp({SPEED} / 3.4, 0.0, 1.0) * {GROUNDED} * {CALM})"
SPRINTING = "(query.is_sprinting ? 1.0 : 0.0)"
SPR = f"({SPRINTING} * {W})"
SNEAK = "((query.is_sneaking && !query.is_in_water) ? 1.0 : 0.0)"

# direction of travel against where the body faces: +1 forwards, -1 backwards
_MX, _MZ, _YAW = "query.movement_direction(0)", "query.movement_direction(2)", "query.body_y_rotation"
FWD = f"(-{_MX} * math.sin({_YAW}) + {_MZ} * math.cos({_YAW}))"
SIDEWAYS = f"math.abs({_MX} * math.cos({_YAW}) + {_MZ} * math.sin({_YAW}))"
# if the game reports no direction (or it is tiny), walk forwards
K = f"(math.abs({FWD}) < 0.2 ? 1.0 : math.clamp({FWD} * 2.5, -1.0, 1.0))"
BACKW = f"math.clamp(-{FWD} * 1.5, 0.0, 1.0)"
BACK = f"({BACKW} * {W})"
RISING = f"math.clamp(query.vertical_speed / 4.0, 0.0, 1.0)"
SIDE = f"(math.clamp({SIDEWAYS} * 1.4, 0.0, 1.0) * {W})"

# ------------------------------------------------------------------ climbing, hits, eating, fire
# ladders and vines: off the ground, a steady climbing / sliding speed, barely moving sideways
CLIMB = (f"(((!query.is_on_ground && !query.is_in_water && !{BUSY} && math.abs(query.vertical_speed) > 1.2"
         f" && math.abs(query.vertical_speed) < 3.4 && {SPEED} < 0.6) ? 1.0 : 0.0) * {UI})")
HURT = f"(math.clamp(query.hurt_time / 10.0, 0.0, 1.0) * {UI})"
EAT = f"((query.is_eating ? 1.0 : 0.0) * {UI})"
FIRE = f"((query.is_on_fire ? 1.0 : 0.0) * {CALM} * {UI})"

# ------------------------------------------------------------------ in the air
AIRW = f"(((query.is_on_ground || query.is_in_water || {BUSY}) ? 0.0 : 1.0) * (1.0 - {CLIMB}) * {UI})"
VY = "query.vertical_speed"
MV = f"math.min({SPEED} / 4.0, 1.0)"
BREATH = f"math.cos({LIFE} * 245.0)"
FALLING = f"math.clamp((-{VY} - 2.0) / 8.0, 0.0, 1.0)"
# long falls only (normal jumps land before reaching this speed)
FLAIL = f"math.clamp((-{VY} - 13.0) / 6.0, 0.0, 1.0)"

# ------------------------------------------------------------------ standing still
IDLE = f"((1.0 - math.clamp({SPEED} / 1.2, 0.0, 1.0)) * {GROUNDED} * (1.0 - {SNEAK}) * {CALM} * {UI})"
TURNSTEP = f"({IDLE} * math.clamp((math.abs(query.yaw_speed) - 40.0) / 80.0, 0.0, 1.0))"
SHIFTW = f"math.sin({LIFE} * 45.0)"               # slow weight shift from one leg to the other (~8 s)

# ------------------------------------------------------------------ new in the big animation update
# low health: 0 above 40 % health .. 1 at 15 % and below (no data -> 0)
LOW = (f"(((query.max_health > 0.0) ? math.clamp((0.4 - query.health / query.max_health) / 0.25, 0.0, 1.0) : 0.0)"
       f" * {CALM} * {UI})")
# treading water: in water, not swimming, feet off the bottom
TREAD = f"(((query.is_in_water && !query.is_swimming && !query.is_on_ground && !query.is_riding) ? 1.0 : 0.0) * {UI})"
TREADA = f"({TREAD} * (1.0 - 0.6 * {W}))"
# elytra flight
GLIDE = f"((query.is_gliding ? 1.0 : 0.0) * {UI})"
# leaning into turns while moving (stronger when running)
BANK = (f"(math.clamp(query.yaw_speed / 240.0, -1.0, 1.0) * {W} * (0.4 + 0.6 * {SPRINTING})"
        f" * (query.is_on_ground ? 1.0 : 0.0))")
# idle life: a look to each side every ~13 s, a stretch every ~29 s
_GT = f"math.mod({LIFE}, 13.0)"
GLANCE = f"({IDLE} * (({_GT} < 2.6) ? math.sin({_GT} * 138.46) : 0.0))"
_ST = f"math.mod({LIFE} + 7.0, 29.0)"
STRETCH = f"({IDLE} * (1.0 - {LOW}) * (({_ST} < 2.2) ? math.sin({_ST} * 81.82) : 0.0))"
# a sword in hand and standing still: a light ready stance
_SWORDS = ", ".join(f"'minecraft:{m}_sword'" for m in ("wooden", "stone", "iron", "golden", "diamond", "netherite", "copper"))
READY = f"((query.is_item_name_any('slot.weapon.mainhand', {_SWORDS}) ? 1.0 : 0.0) * {IDLE} * (1.0 - {LOW}))"
SLEEP = f"(query.is_sleeping ? 1.0 : 0.0)"


def inair(expr):
    return f"({AIRW} * ({expr}))"


def leg(side):
    """side: +1 left leg, -1 right leg"""
    sw = "" if side > 0 else "-"
    ph = "0.0" if side > 0 else "180.0"
    lift = f"math.max(0.0, {sw}{C})"            # this leg is in its swing phase
    lead = "1.0" if side < 0 else "0.0"         # the right knee leads in the air
    limp = f"(1.0 - 0.45 * {LOW})" if side < 0 else f"(1.0 - 0.1 * {LOW})"   # low health: the right leg is spared
    amp = f"((24.0 + 16.0 * {SPRINTING}) * (1.0 - 0.2 * {BACKW}) * (1.0 + 1.1 * {SNEAK}) * {W} * {limp})"
    back = "34.0" if side > 0 else "28.0"
    air_x = inair(f"({lead} * 7.0 + (1.0 - {lead}) * 5.0) - 2.0 * {BREATH} + {FWD} * {back} * {MV}"
                  f" - 6.0 * {FALLING} * (1.0 - {MV})"
                  f" + {FLAIL} * 22.0 * math.sin({LIFE} * 520.0 + {ph})")
    air_z = inair(f"4.0 * {MV} + 4.0 * {FALLING} + {FLAIL} * 4.0")
    air_y = inair(f"{lead} * 3.0 * (1.0 - 0.5 * {MV}) * (1.0 - {FALLING})")
    air_fz = inair(f"{lead} * -3.0 * (1.0 - 0.5 * {MV}) * (1.0 - {FALLING}) + {FWD} * -1.5 * {MV}")
    rot_x = (
        f"{'-' if side > 0 else ''}{amp} * {S} * {K}"                                  # stride
        f" + {air_x}"
        f" + {TURNSTEP} * 12.0 * math.sin({LIFE} * 620.0 + {ph})"                      # small steps while turning
        f" - {IDLE} * 3.0 * math.max(0.0, {'' if side > 0 else '-'}{SHIFTW})"          # the relaxed leg bends a little
        f" - {CLIMB} * 26.0 * math.max(0.0, math.sin({LIFE} * 400.0 + {ph} + 180.0))"  # climbing: legs step in turn
        f" + {TREADA} * 20.0 * math.sin({LIFE} * 260.0 + {ph})"                         # treading water: slow kicks
        f" + {GLIDE} * (6.0 + 3.0 * math.sin({LIFE} * 520.0 + {ph}))"                   # elytra: legs trail, flutter
    )
    rot_z = (f"{side * -0.1} + {side * -1.0} * ({SIDE} * 9.0 * math.max(0.0, {sw}{S}))"  # sidestep: open the moving leg
             f" + {side * -1.0} * {air_z}"
             f" + {side * -1.0} * ({GLIDE} * 4.0 + {TREADA} * 6.0)")
    pos = [
        0.0,
        f"({lift} * (1.3 + 2.2 * {SPRINTING}) * (1.0 - 0.4 * {BACKW}) * {W}) + {air_y}"
        f" + {TURNSTEP} * 1.4 * math.max(0.0, math.sin({LIFE} * 620.0 + {ph}))"
        f" + {IDLE} * 0.6 * math.max(0.0, {'' if side > 0 else '-'}{SHIFTW})"
        f" + {CLIMB} * 2.0 * math.max(0.0, math.sin({LIFE} * 400.0 + {ph} + 180.0))",
        f"-{lift} * 1.0 * {K} * {W} + {air_fz}",
    ]
    return {"rotation": [rot_x, f"{side * -0.1}", rot_z], "position": pos}


def arm(side):
    """side: +1 left arm, -1 right arm"""
    ph = "0.0" if side > 0 else "180.0"
    amp = f"((20.0 + 30.0 * {SPRINTING}) * (1.0 - 0.4 * {BACKW}) * {W} * (1.0 - 0.35 * {LOW}))"
    swing = f"math.sin({PHASE} + 12.0)"
    air_x = inair(f"-2.0 * {BREATH} + {FWD} * 18.0 * {MV} - 18.0 * {FALLING} - 22.0 * {RISING} * (1.0 - 0.5 * {MV})"
                  f" - {FLAIL} * (40.0 + 30.0 * math.sin({LIFE} * 380.0 + {ph}))")
    air_out = inair(f"7.0 + 14.0 * {FALLING} + {FLAIL} * (30.0 + 10.0 * math.sin({LIFE} * 500.0 + {ph}))")
    rot_x = (
        f"{'' if side > 0 else '-'}{amp} * {swing} * {K}"   # opposite to the leg on this side
        f" - 12.0 * {SPR}"                                  # running: arms carried higher
        f" - 12.0 * {SNEAK} * {CALM}"                       # crouched: hands low and ready
        f" + 2.0 * {SNEAK} * {CALM} * math.sin({LIFE} * 110.0 + {ph})"   # a little sway while crouched
        f" + {CLIMB} * (-150.0 + 28.0 * math.sin({LIFE} * 400.0 + {ph}))"  # climbing: hands reach up in turn
        f" + 12.0 * {HURT}"                                                # hit: arms jerk back
        f" + {air_x}"
        f" + {TREADA} * (-28.0 + 20.0 * math.cos({LIFE} * 300.0 + {ph}))"   # treading water: sculling circles
        f" + {GLIDE} * 14.0"                                                # elytra: arms swept back
        f" - {STRETCH} * 95.0"                                              # stretch: arms rise up high
        f" + {READY} * {'-8.0' if side > 0 else '-16.0'}"                   # ready stance: blade up, guard hand forward
        f" + {LOW} * 4.0 * {IDLE}"                                          # tired: arms hang
    )
    # the arm swinging forward comes in towards the body a little
    inward = f"math.max(0.0, {'-' if side > 0 else ''}{swing} * {K}) * 4.0 * {W}"
    out = (f"(2.0 + 2.0 * {SPR} + {air_out} + 4.0 * {SNEAK} * {CALM} - {inward} + 6.0 * {CLIMB} + 14.0 * {HURT}"
           f" + {FIRE} * (14.0 + 12.0 * math.sin({LIFE} * 900.0 + {ph}))"
           f" + {TREADA} * (26.0 + 12.0 * math.sin({LIFE} * 300.0 + {ph}))"
           f" + {GLIDE} * (36.0 + 3.0 * math.sin({LIFE} * 700.0 + {ph}))"
           f" + {STRETCH} * 28.0 + {READY} * 4.0 - {LOW} * 2.0 * {IDLE})")
    rot_z = f"{'-' if side > 0 else ''}{out}"
    rot_y = (f"{'' if side > 0 else '-'}math.sin({PHASE}) * 5.0 * {W}"
             f" + {READY} * {'10.0' if side > 0 else '-6.0'}")
    return {"rotation": [rot_x, rot_y, rot_z]}


# crouch: eased in over ~0.2 s by the sneaking animation's own clock
CR = "math.clamp(query.anim_time / 0.18, 0.0, 1.0)"
CRE = f"({CR} * {CR} * (3.0 - 2.0 * {CR}))"


def build():
    waist_rx = (f"{UI} * (7.0 * {SPR} - 3.5 * {BACK}) - 10.0 * {HURT} + 8.0 * {LOW} - 5.0 * {STRETCH}"
                + " + " + inair(f"2.0 * math.cos({LIFE} * 245.0 - 90.0) + 3.0 * {FALLING}"))
    waist_ry = f"{UI} * (8.0 + 5.0 * {SPRINTING}) * {S} * {K} * {W} + 7.0 * {READY}"
    waist_rz = (f"{UI} * (2.2 * {C} + 2.0 * {S} * {SIDE}) * {W} + {IDLE} * 1.6 * {SHIFTW}"
                f" + {UI} * 7.0 * {BANK}"                                   # lean into the turn
                f" + 3.0 * {LOW} * {W} * math.max(0.0, -{C})")              # limp: dip over the weak leg
    waist_py = f"-(0.9 + 0.7 * {SPRINTING}) * {S} * {S} * {W} - 0.5 * {LOW} * {W} * math.max(0.0, -{C})"
    head_x = (f"1.0 * math.cos({PHASE} * 2.0) * {W} + 3.0 * {SPR} + 2.0 * {BACK} - 9.0 * {HURT}"
              f" + 5.0 * {EAT} * math.sin({LIFE} * 1100.0) - 10.0 * {CLIMB} + "
              + inair(f"4.0 + 10.0 * {FALLING} - 4.0 * {RISING}")
              + f" + 7.0 * {LOW} - 12.0 * {STRETCH} - 6.0 * {GLIDE}")
    return {
        "animation.player.move.arms": {
            "loop": True,
            "bones": {"leftarm": arm(1), "rightarm": arm(-1)},
        },
        "animation.player.move.legs": {
            "loop": True,
            "bones": {
                "leftleg": leg(1),
                "rightleg": leg(-1),
                "waist": {"rotation": [waist_rx, waist_ry, waist_rz], "position": [0.0, waist_py, 0.0]},
                # head stays steady while the torso twists
                "head": {"rotation": [head_x, f"-5.0 * {S} * {K} * {W} + 18.0 * {GLANCE}",
                                      f"-1.5 * {C} * {W} - 3.0 * {UI} * {BANK} + 3.0 * {GLANCE}"]},
                # breathing: the chest and shoulders lift a touch
                # (faster and deeper when hurt badly, slow and deep while asleep)
                "body": {"position": [0.0, f"(0.18 + 0.22 * {LOW}) * math.sin({LIFE} * (140.0 + 130.0 * {LOW})) * (1.0 - {W}) * {UI}"
                                           f" + {SLEEP} * 0.3 * math.sin({LIFE} * 80.0)", 0.0]},
            },
        },
        # crouch: the whole figure tilts forward from the feet with the hips set back (the
        # frame the game's camera and hit box expect), eased in instead of snapping
        "animation.player.sneaking": {
            "loop": True,
            "animation_length": 1000.0,
            "bones": {
                "body": {"position": [0.0, f"-2.0 * {CRE}", 0.0]},
                "leftleg": {"rotation": [f"-28.0 * {CRE}", -0.1, f"-2.5 * {CRE}"]},
                "rightleg": {"rotation": [f"-28.0 * {CRE}", 0.1, f"2.5 * {CRE}"]},
                "root": {"position": [0.0, f"1.25 * {CRE}", f"9.0 * {CRE}"],
                         "rotation": [f"28.0 * {CRE}", 0.0, 0.0]},
            },
        },
    }
