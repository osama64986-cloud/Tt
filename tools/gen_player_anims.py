"""أنميشن اللاعب (v1.39 + V1): ضربات الأسلحة، حركات المهارات، الداش، الصد، الوقوف، المشي، وقفة القتال، والركض.
البحث (Microsoft Learn: Animations، Entity.playAnimation، PlayAnimationOptions، actor_animation):
  - الأنميشن بحزمة الموارد وتنشغل من السكربت بـ Entity.playAnimation(اسم، {blendOutTime، stopExpression، controller}).
    اسم controller مختلف = طبقة منفصلة، فالضربة والركض يشتغلون سوا.
  - override_previous_animation: يرجّع عظام هالأنميشن بس لوضعها الأصلي قبل ما يطبقها (فتنلغي هزة ذراع الضربة الأصلية
    وتبقى الرجلين تمشي طبيعي لأن ما نحركهم).
  - العظام (geometry.humanoid.custom مال اللاعب): waist يحني الجسم كله (الجسم + الراس + الذراعين)، root يميل الموديل كله
    (للداش)، rightArm/leftArm، والأيتم بالإيد (rightItem) يتبع الذراع.
  - منظور الشخص الأول: blend_weight = 1 - variable.is_first_person، و stopExpression يوقفها إذا الكاميرا من عيونك، فإيدك
    بالمنظور الأول تبقى مثل ما هي (الأنميشن يبين للي يشوفونك وبالمنظور الثالث).
مبادئ الأنميشن: تحضير (anticipation) ← ضربة سريعة ← متابعة (follow-through) ← رجوع هادي، ومنحنيات catmullrom ناعمة.
الاتجاهات: x سالب = الذراع ترتفع لقدام، y للف يمين/يسار، z للبرا/للداخل (مقاسة على موديل اللاعب بـ tools/render.py).
المخرجات: RP/animations/sh_player.animation.json + BP/scripts/panims.js (الأسماء والأطوال للسكربت).
التشغيل: python3 tools/gen_player_anims.py [مجلد_معاينة]"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
BP = os.path.join(ROOT, "AnimePowers", "BP")

# كل أنميشن: الطول، ومفاتيح لكل عظمة: {عظمة: {"rot": {وقت: [x,y,z]}, "pos": {وقت: [x,y,z]}}}
R0 = [0, 0, 0]
ANIMS = {
    # سيف/كاتانا: يرفع الذراع لفوق ولليمين ويرجعها لورا (تحضير)، يكنس عرضي سريع، يكمل لليسار، ويرجع
    "slash": (0.42, {
        "rightArm": {"rot": {0: [-40, 0, 0], 0.08: [-118, 58, -18], 0.15: [-88, -38, 10], 0.24: [-62, -72, 16], 0.42: [-28, -8, 0]}},
        "leftArm": {"rot": {0: R0, 0.08: [-28, 0, 8], 0.2: [12, 0, -6], 0.42: R0}},
        "waist": {"rot": {0: R0, 0.08: [0, 20, 0], 0.17: [6, -22, 0], 0.42: R0}},
    }),
    # الضربة الثانية (بالعكس): من اليسار لليمين، حتى الضربات المتتالية تتناوب
    "slash2": (0.42, {
        "rightArm": {"rot": {0: [-40, 0, 0], 0.08: [-105, -62, 12], 0.15: [-90, 30, -12], 0.24: [-70, 64, -18], 0.42: [-28, 8, 0]}},
        "leftArm": {"rot": {0: R0, 0.1: [-20, 0, 10], 0.42: R0}},
        "waist": {"rot": {0: R0, 0.08: [0, -18, 0], 0.17: [6, 20, 0], 0.42: R0}},
    }),
    # خنجر: يسحب الإيد لورا ويطعن لقدام بسرعة (الذراع تتقدم 2 بكسل)
    "stab": (0.3, {
        "rightArm": {"rot": {0: [-30, 0, 0], 0.07: [-58, 18, 0], 0.13: [-94, -6, 0], 0.3: [-30, 0, 0]},
                     "pos": {0: R0, 0.07: [0, 0, 1.6], 0.13: [0, 0, -2.4], 0.3: R0}},
        "leftArm": {"rot": {0: R0, 0.1: [16, 0, -4], 0.3: R0}},
        "waist": {"rot": {0: R0, 0.07: [-4, 10, 0], 0.13: [10, -8, 0], 0.3: R0}},
    }),
    # ساطور: ضربة مايلة من فوق الراس لتحت (بإيد وحدة) والجسم ينحني
    "cleave": (0.5, {
        "rightArm": {"rot": {0: [-35, 0, 0], 0.12: [-165, 22, -14], 0.24: [-48, -22, 10], 0.34: [-38, -28, 8], 0.5: [-25, 0, 0]}},
        "leftArm": {"rot": {0: R0, 0.12: [-30, 0, 10], 0.26: [18, 0, -8], 0.5: R0}},
        "waist": {"rot": {0: R0, 0.12: [-10, 14, 0], 0.24: [20, -10, 0], 0.36: [14, -6, 0], 0.5: R0}},
    }),
    # مطرقة: بالإيدين فوق الراس والجسم يرجع لورا، ثم دقة قوية لتحت والجسم ينحني لقدام، وثبات لحظة
    "heavy": (0.66, {
        "rightArm": {"rot": {0: [-30, 0, 0], 0.2: [-172, 10, -4], 0.31: [-62, 14, 0], 0.46: [-55, 12, 0], 0.66: [-22, 0, 0]}},
        "leftArm": {"rot": {0: [-20, 0, 0], 0.2: [-172, -10, 4], 0.31: [-62, -14, 0], 0.46: [-55, -12, 0], 0.66: [-10, 0, 0]}},
        "waist": {"rot": {0: R0, 0.2: [-14, 0, 0], 0.31: [26, 0, 0], 0.46: [20, 0, 0], 0.66: R0}},
    }),
    # رمح: يسحب لورا والإيد الثانية تسند، ثم طعنة طويلة لقدام بكل الجسم
    "thrust": (0.4, {
        "rightArm": {"rot": {0: [-35, 0, 0], 0.1: [-68, 26, -8], 0.18: [-96, -4, 0], 0.4: [-35, 0, 0]},
                     "pos": {0: R0, 0.1: [0, 0, 2.2], 0.18: [0, 0, -3.4], 0.4: R0}},
        "leftArm": {"rot": {0: R0, 0.1: [-62, 28, 0], 0.18: [-84, 34, 0], 0.4: R0}},
        "waist": {"rot": {0: R0, 0.1: [-6, 16, 0], 0.18: [14, -10, 0], 0.4: R0}},
    }),
    # مخالب: خرمشة مايلة باليمين ثم باليسار
    "claw": (0.44, {
        "rightArm": {"rot": {0: [-30, 0, 0], 0.06: [-150, 32, -22], 0.14: [-38, -30, 12], 0.44: [-25, 0, 0]}},
        "leftArm": {"rot": {0: R0, 0.14: [-20, 0, 6], 0.2: [-150, -32, 22], 0.29: [-38, 30, -12], 0.44: R0}},
        "waist": {"rot": {0: R0, 0.06: [0, 14, 0], 0.14: [8, -14, 0], 0.22: [4, -12, 0], 0.29: [8, 14, 0], 0.44: R0}},
    }),
    # منجل: بالإيدين، يلف الجسم لليمين كلش (تحضير طويل)، ثم حصدة عريضة لليسار
    "reap": (0.58, {
        "rightArm": {"rot": {0: [-40, 0, 0], 0.16: [-96, 72, -22], 0.31: [-90, -78, 20], 0.42: [-74, -88, 22], 0.58: [-30, 0, 0]}},
        "leftArm": {"rot": {0: [-30, 0, 0], 0.16: [-84, 60, 8], 0.31: [-86, -66, -8], 0.42: [-70, -74, -8], 0.58: [-14, 0, 0]}},
        "waist": {"rot": {0: R0, 0.16: [-4, 28, 0], 0.31: [8, -28, 0], 0.42: [6, -32, 0], 0.58: R0}},
    }),
    # ── المهارات ──
    # دفع طاقة لقدام: الإيدين تنضم وتندفع (مثل الكاميهاميها)
    "cast_push": (0.5, {
        "rightArm": {"rot": {0: [-20, 0, 0], 0.1: [-55, 26, -18], 0.18: [-94, -10, 0], 0.36: [-92, -10, 0], 0.5: [-20, 0, 0]},
                     "pos": {0: R0, 0.1: [0, 0, 1.2], 0.18: [0, 0, -1.6], 0.36: [0, 0, -1.6], 0.5: R0}},
        "leftArm": {"rot": {0: [-20, 0, 0], 0.1: [-55, -26, 18], 0.18: [-94, 10, 0], 0.36: [-92, 10, 0], 0.5: [-20, 0, 0]},
                    "pos": {0: R0, 0.1: [0, 0, 1.2], 0.18: [0, 0, -1.6], 0.36: [0, 0, -1.6], 0.5: R0}},
        "waist": {"rot": {0: R0, 0.1: [-6, 0, 0], 0.18: [10, 0, 0], 0.5: R0}},
    }),
    # نداء من السما: يرفع اليمين لفوق على طولها والجسم يرجع لورا، واليسار للجنب
    "cast_sky": (0.6, {
        "rightArm": {"rot": {0: [-20, 0, 0], 0.16: [-178, 0, -8], 0.44: [-176, 0, -8], 0.6: [-20, 0, 0]}},
        "leftArm": {"rot": {0: R0, 0.16: [-12, 0, 28], 0.44: [-12, 0, 28], 0.6: R0}},
        "waist": {"rot": {0: R0, 0.16: [-12, 0, 0], 0.44: [-10, 0, 0], 0.6: R0}},
    }),
    # دقة الأرض: يرفع الإيدين ويضرب الأرض والجسم ينحني كلش
    "cast_ground": (0.56, {
        "rightArm": {"rot": {0: [-20, 0, 0], 0.13: [-150, 8, -10], 0.26: [-24, 6, 0], 0.4: [-20, 6, 0], 0.56: R0}},
        "leftArm": {"rot": {0: [-20, 0, 0], 0.13: [-150, -8, 10], 0.26: [-24, -6, 0], 0.4: [-20, -6, 0], 0.56: R0}},
        "waist": {"rot": {0: R0, 0.13: [-12, 0, 0], 0.26: [36, 0, 0], 0.4: [30, 0, 0], 0.56: R0}},
    }),
    # هالة/درع/منطقة: يفتح الذراعين للجناب والصدر لقدام
    "cast_spread": (0.6, {
        "rightArm": {"rot": {0: [-10, 0, 0], 0.12: [-40, 0, 14], 0.24: [-18, 0, -78], 0.44: [-18, 0, -76], 0.6: R0}},
        "leftArm": {"rot": {0: [-10, 0, 0], 0.12: [-40, 0, -14], 0.24: [-18, 0, 78], 0.44: [-18, 0, 76], 0.6: R0}},
        "waist": {"rot": {0: R0, 0.12: [8, 0, 0], 0.24: [-10, 0, 0], 0.6: R0}},
    }),
    # دوران: الموديل كله يلف دورة كاملة والذراعين مفتوحة
    "cast_spin": (0.5, {
        "root": {"rot": {0: R0, 0.1: [0, -40, 0], 0.4: [0, -360, 0], 0.5: [0, -360, 0]}},
        "rightArm": {"rot": {0: [-20, 0, 0], 0.1: [-88, 0, -12], 0.4: [-88, 0, -12], 0.5: [-20, 0, 0]}},
        "leftArm": {"rot": {0: [-20, 0, 0], 0.1: [-88, 0, 12], 0.4: [-88, 0, 12], 0.5: [-20, 0, 0]}},
    }),
    # ── الحركة (V1) ──
    # داش للجنب: تحضير صغير (ينزل وميلة عكسية)، انطلاقة: الجسم يميل كلش باتجاه الحركة، الرجل القائدة ممدودة لبرا والثانية مطوية،
    # الذراعين ممدودة لورا (مثل الأنمي)، ثبات وهو ينزلق، ورجوع بارتداد خفيف (follow-through)
    "dash_left": (0.4, {
        "root": {"rot": {0: R0, 0.04: [2, 0, -5], 0.09: [6, 0, 22], 0.26: [5, 0, 18], 0.33: [0, 0, -4], 0.4: R0},
                 "pos": {0: R0, 0.04: [0, -1.0, 0], 0.09: [0, -0.6, 0], 0.26: [0, -0.4, 0], 0.4: R0}},
        "leftLeg": {"rot": {0: R0, 0.09: [0, 0, -26], 0.26: [0, 0, -22], 0.4: R0}},
        "rightLeg": {"rot": {0: R0, 0.09: [-24, 0, -6], 0.26: [-20, 0, -4], 0.4: R0}},
        "rightArm": {"rot": {0: R0, 0.04: [-10, 0, -8], 0.09: [40, 0, -30], 0.26: [36, 0, -26], 0.4: R0}},
        "leftArm": {"rot": {0: R0, 0.04: [-10, 0, 8], 0.09: [34, 0, 34], 0.26: [30, 0, 30], 0.4: R0}},
        "head": {"rot": {0: R0, 0.09: [0, 0, -14], 0.26: [0, 0, -12], 0.4: R0}},
    }),
    "dash_right": (0.4, {
        "root": {"rot": {0: R0, 0.04: [2, 0, 5], 0.09: [6, 0, -22], 0.26: [5, 0, -18], 0.33: [0, 0, 4], 0.4: R0},
                 "pos": {0: R0, 0.04: [0, -1.0, 0], 0.09: [0, -0.6, 0], 0.26: [0, -0.4, 0], 0.4: R0}},
        "rightLeg": {"rot": {0: R0, 0.09: [0, 0, 26], 0.26: [0, 0, 22], 0.4: R0}},
        "leftLeg": {"rot": {0: R0, 0.09: [-24, 0, 6], 0.26: [-20, 0, 4], 0.4: R0}},
        "rightArm": {"rot": {0: R0, 0.04: [-10, 0, -8], 0.09: [34, 0, -34], 0.26: [30, 0, -30], 0.4: R0}},
        "leftArm": {"rot": {0: R0, 0.04: [-10, 0, 8], 0.09: [40, 0, 30], 0.26: [36, 0, 26], 0.4: R0}},
        "head": {"rot": {0: R0, 0.09: [0, 0, 14], 0.26: [0, 0, 12], 0.4: R0}},
    }),
    # داش لورا: ينحني لقدام لحظة ثم يرجع بقفزة لورا: الجسم مايل لورا، رجل لورا ورجل لقدام، والذراعين لقدام للتوازن
    "dash_back": (0.4, {
        "root": {"rot": {0: R0, 0.04: [6, 0, 0], 0.09: [-18, 0, 0], 0.26: [-15, 0, 0], 0.33: [4, 0, 0], 0.4: R0},
                 "pos": {0: R0, 0.04: [0, -1.0, 0], 0.09: [0, -0.4, 0], 0.4: R0}},
        "rightLeg": {"rot": {0: R0, 0.09: [-30, 0, 4], 0.26: [-26, 0, 4], 0.4: R0}},
        "leftLeg": {"rot": {0: R0, 0.09: [26, 0, -4], 0.26: [22, 0, -4], 0.4: R0}},
        "rightArm": {"rot": {0: R0, 0.04: [12, 0, 0], 0.09: [-52, 0, -18], 0.26: [-46, 0, -16], 0.4: R0}},
        "leftArm": {"rot": {0: R0, 0.04: [12, 0, 0], 0.09: [-52, 0, 18], 0.26: [-46, 0, 16], 0.4: R0}},
        "head": {"rot": {0: R0, 0.09: [10, 0, 0], 0.26: [8, 0, 0], 0.4: R0}},
    }),
    # الصد المثالي: الذراعين تتصالب قدام الوجه لحظة
    "guard": (0.42, {
        "rightArm": {"rot": {0: R0, 0.06: [-100, -42, 0], 0.26: [-98, -40, 0], 0.42: R0}},
        "leftArm": {"rot": {0: R0, 0.06: [-100, 42, 0], 0.26: [-98, 40, 0], 0.42: R0}},
        "waist": {"rot": {0: R0, 0.06: [-8, 0, 0], 0.26: [-6, 0, 0], 0.42: R0}},
    }),
}
# ── حلقات الحركة (V1): تنضاف فوق حركة اللعبة (مو بدالها)، وتطفي بالمنظور الأول (blend_weight) ──
# variable.tcos0 = نفس موجة خطوات اللاعب باللعبة (من player.entity.json)، فالمشي يمشي ويا الرجلين بالضبط.
LT = "query.life_time"
# الوقوف: تنفس هادي (الصدر يرتفع وينزل)، الذراعين ترتخي للجناب وتتمايل متأخرة شوية، الراس يتبع النفس، وتحويل وزن بطيء
IDLE = {"waist": {"rotation": [f"math.sin({LT} * 80) * 0.9", 0, 0], "position": [0, f"math.sin({LT} * 80) * 0.15", 0]},
        "head": {"rotation": [f"math.sin({LT} * 80 + 70) * 1.2", 0, 0]},
        "rightArm": {"rotation": [f"math.sin({LT} * 80 + 40) * 1.4", 0, f"-1.5 - math.sin({LT} * 80 + 40) * 1.2"]},
        "leftArm": {"rotation": [f"math.sin({LT} * 80 + 40) * 1.4", 0, f"1.5 + math.sin({LT} * 80 + 40) * 1.2"]},
        "root": {"rotation": [0, 0, f"math.sin({LT} * 14) * 1.0"]}}
# وقفة القتال (ماسك سلاح من أسلحة المود): الجسم ملفوف شوية، إيد السلاح لقدام، والإيد الثانية مرفوعة للحماية، وتنفس أسرع
IDLE_COMBAT = {"waist": {"rotation": [f"4 + math.sin({LT} * 120) * 1.0", -12, 0], "position": [0, f"math.sin({LT} * 120) * 0.18", 0]},
               "head": {"rotation": [f"-4 + math.sin({LT} * 120 + 70) * 1.0", 12, 0]},
               "rightArm": {"rotation": [f"-16 + math.sin({LT} * 120 + 40) * 2", 6, -4]},
               "leftArm": {"rotation": [f"-28 + math.sin({LT} * 120 + 40) * 2", -18, 6]},
               "rightLeg": {"rotation": [-6, 4, 2]}, "leftLeg": {"rotation": [8, -4, -2]}}
# المشي: الكتفين تلف عكس الرجلين، ميلة خفيفة لقدام، والجسم ينزل شوية لما الخطوة مفتوحة ويرتفع لما الرجلين تعبر بعض
WALK = {"waist": {"rotation": [f"query.modified_move_speed * 3", "-variable.tcos0 * 0.12", 0],
                  "position": [0, "-math.abs(variable.tcos0) * 0.012", 0]},
        "head": {"rotation": [0, "variable.tcos0 * 0.08", 0]},
        "rightArm": {"rotation": [0, 0, -2]}, "leftArm": {"rotation": [0, 0, 2]}}
# الركض: الجسم مايل لقدام والذراعين ممدودة لورا (ركضة الأنمي) وتتمايل ويا الخطوة، والجسم ينط شوية ويلف ويا الرجلين،
# والراس يرجع يباوع لقدام (target_x/y_rotation) ناقص ميلان الجسم حتى عيونه تبقى لقدام
SPRINT = {"waist": {"rotation": [14, "-variable.tcos0 * 0.1", 0], "position": [0, "-math.abs(variable.tcos0) * 0.015", 0]},
          "head": {"rotation": ["query.target_x_rotation - 14", "query.target_y_rotation + variable.tcos0 * 0.08", 0]},
          "rightArm": {"rotation": ["58 + variable.tcos0 * 0.12", 0, -10]},
          "leftArm": {"rotation": ["58 - variable.tcos0 * 0.12", 0, 10]}}
FP_OFF = "1.0 - variable.is_first_person"


def keys(d):
    out = {}
    for t in sorted(d):
        out[f"{t:.2f}" if t else "0.0"] = {"post": [round(v, 2) for v in d[t]], "lerp_mode": "catmullrom"}
    return out


def build():
    anims = {}
    for name, (length, bones) in ANIMS.items():
        bj = {}
        for b, ch in bones.items():
            e = {}
            if "rot" in ch:
                e["rotation"] = keys(ch["rot"])
            if "pos" in ch:
                e["position"] = keys(ch["pos"])
            bj[b] = e
        anims[f"animation.sh.player.{name}"] = {"animation_length": length, "loop": False, "override_previous_animation": True,
                                                "blend_weight": FP_OFF, "bones": bj}
    anims["animation.sh.player.sprint"] = {"loop": True, "override_previous_animation": True, "blend_weight": FP_OFF, "bones": SPRINT}
    for name, bones in (("idle", IDLE), ("idle_combat", IDLE_COMBAT), ("walk", WALK)):        # V1: الوقوف والمشي (فوق حركة اللعبة)
        anims[f"animation.sh.player.{name}"] = {"loop": True, "blend_weight": FP_OFF, "bones": bones}
    return anims


# ── معاينة: موديل لاعب (نفس عظام geometry.humanoid.custom) + سيف بالإيد، ونرسم كل أنميشن على 5 لقطات ──
def catmull(ts, vs, t):
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    i = max(k for k in range(len(ts) - 1) if ts[k] <= t)
    p0, p1, p2, p3 = vs[max(0, i - 1)], vs[i], vs[i + 1], vs[min(len(vs) - 1, i + 2)]
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    return [0.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3) for a, b, c, d in zip(p0, p1, p2, p3)]


def pose_at(bones, t):
    pose = {}
    for b, ch in bones.items():
        p = {"rot": [0, 0, 0], "pos": [0, 0, 0]}
        for k, key in (("rot", "rot"), ("pos", "pos")):
            if key in ch:
                ts = sorted(ch[key]); p[k] = catmull(ts, [ch[key][x] for x in ts], t)
        pose[b] = p
    return pose


def preview(out):
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    skin = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(skin)
    def box(u, v, w, h, dp, col):
        d.rectangle([u, v, u + 2 * (w + dp) - 1, v + h + dp - 1], fill=col)
    box(0, 0, 8, 8, 8, (224, 182, 150, 255)); d.rectangle([8 + 2, 8 + 3, 8 + 5, 8 + 4], fill=(40, 40, 60, 255))
    box(16, 16, 8, 12, 4, (60, 110, 190, 255)); box(40, 16, 4, 12, 4, (224, 182, 150, 255)); box(32, 48, 4, 12, 4, (210, 170, 140, 255))
    box(0, 16, 4, 12, 4, (52, 52, 70, 255)); box(16, 48, 4, 12, 4, (44, 44, 62, 255)); box(48, 0, 4, 4, 4, (200, 200, 210, 255))
    tp = os.path.join(tempfile.gettempdir(), "mannequin.png"); skin.save(tp)
    bones = [
        {"name": "root", "pivot": [0, 0, 0]},
        {"name": "waist", "parent": "root", "pivot": [0, 12, 0]},
        {"name": "body", "parent": "waist", "pivot": [0, 24, 0], "cubes": [{"origin": [-4, 12, -2], "size": [8, 12, 4], "uv": [16, 16]}]},
        {"name": "head", "parent": "body", "pivot": [0, 24, 0], "cubes": [{"origin": [-4, 24, -4], "size": [8, 8, 8], "uv": [0, 0]}]},
        {"name": "rightArm", "parent": "body", "pivot": [-5, 22, 0], "cubes": [{"origin": [-8, 12, -2], "size": [4, 12, 4], "uv": [40, 16]}]},
        {"name": "rightItem", "parent": "rightArm", "pivot": [-6, 15, 1], "cubes": [{"origin": [-6.5, 12.5, -12], "size": [1, 1, 13], "uv": [48, 0]}]},
        {"name": "leftArm", "parent": "body", "pivot": [5, 22, 0], "cubes": [{"origin": [4, 12, -2], "size": [4, 12, 4], "uv": [32, 48]}]},
        {"name": "rightLeg", "parent": "root", "pivot": [-1.9, 12, 0], "cubes": [{"origin": [-3.9, 0, -2], "size": [4, 12, 4], "uv": [0, 16]}]},
        {"name": "leftLeg", "parent": "root", "pivot": [1.9, 12, 0], "cubes": [{"origin": [-0.1, 0, -2], "size": [4, 12, 4], "uv": [16, 48]}]},
    ]
    gp = os.path.join(tempfile.gettempdir(), "mannequin.geo.json")
    json.dump({"format_version": "1.12.0", "minecraft:geometry": [{"description": {"identifier": "geometry.mannequin", "texture_width": 64, "texture_height": 64}, "bones": bones}]}, open(gp, "w"))
    m = R.Model(gp, tp)
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    names = list(ANIMS)
    T = 150
    sheet = Image.new("RGB", (T * 6, (T + 18) * len(names)), (46, 48, 56))
    dd = ImageDraw.Draw(sheet)
    for r, name in enumerate(names):
        length, bones_k = ANIMS[name]
        dd.text((6, r * (T + 18) + 2), name, fill=(240, 240, 240), font=F)
        for c in range(6):
            t = length * c / 5
            pose = pose_at(bones_k, t)
            im = R.render(m, pose, yaw=35, pitch=10, size=T, bg=(46, 48, 56), center=(0, 1.1, 0), dist=5.2).convert("RGB")
            sheet.paste(im, (c * T, r * (T + 18) + 18))
    sheet.save(os.path.join(out, "player_anims.png"))


def main():
    anims = build()
    os.makedirs(os.path.join(RP, "animations"), exist_ok=True)
    with open(os.path.join(RP, "animations", "sh_player.animation.json"), "w", encoding="utf-8") as f:
        json.dump({"format_version": "1.8.0", "animations": anims}, f, indent=1)
    info = {n: {"id": f"animation.sh.player.{n}", "len": ANIMS[n][0]} for n in ANIMS}
    for n in ("sprint", "idle", "idle_combat", "walk"):
        info[n] = {"id": f"animation.sh.player.{n}", "len": 0}
    with open(os.path.join(BP, "scripts", "panims.js"), "w", encoding="utf-8") as f:
        f.write("// يتولد تلقائياً من tools/gen_player_anims.py — لا تعدله يدوياً\n")
        f.write("export const PANIM = " + json.dumps(info, indent=1) + ";\n")
    print("player anims ok:", len(anims))
    if len(sys.argv) > 1:
        preview(sys.argv[1])


if __name__ == "__main__":
    main()
