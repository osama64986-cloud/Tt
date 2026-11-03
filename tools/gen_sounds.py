"""أصوات المود (v1.37.3): كل صوت sh.* صار من ملفات أصوات ماينكرافت الحقيقية بدل الأصوات المصنوعة بالكود.
ليش: الـ55 صوت القديمة كانت مولدة بالبرمجة (موجات جيبية تنزلق، ضوضاء، أجراس صناعية) فتطلع مثل "بيب" وتبين صناعية.
أصوات ماينكرافت مسجلة ومعمولة احترافياً، ومتناسقة ويا اللعبة نفسها.
الطريقة: sound_definitions بحزمة الموارد تكدر تأشر على ملفات الفانيلا بالمسار (sounds/...) فما نحتاج ننسخ ملفات.
كل صوت إله حدث فانيلا (أو أكثر)، والأداة تاخذ ملفاته كلها (التنويعات حتى ما يتكرر نفس الصوت) من قائمة Mojang
(bedrock-samples: resource_pack/sounds/sound_definitions.json، محفوظة أسماؤها بـ tools/vanilla_sound_*.txt)،
والعلو = علو Mojang لكل ملف × معامل نختاره (متوسط ومريح: الواجهة واطية، المهارات متوسطة، الانفجارات أوطى من الفانيلا)،
والطبقة (pitch) = طبقة Mojang × معاملنا. الكود يمرر طبقته فوقها (playSound pitch) فتبقى التنويعة.
التشغيل: python3 tools/gen_sounds.py  (يحتاج tools/vanilla_sound_defs.json المصغر اللي تولده الأداة أول مرة من نسخة Mojang)"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
DEFS = os.path.join(RP, "sounds", "sound_definitions.json")
VANILLA = os.path.join(ROOT, "tools", "vanilla_sound_defs.json")             # بس الأحداث اللي نستعملها (مصغرة من ملف Mojang)

# الصوت: (الفئة، أقل مسافة، أكثر مسافة، [(حدث فانيلا، معامل العلو، معامل الطبقة)...])
# الفئات: ui (الواجهة)، hostile (الوحوش)، player (المهارات والأسلحة) — اللاعب يتحكم بيها من إعدادات الصوت.
SOUNDS = {
    # ── الواجهة: واطية وناعمة ──
    "sh.tick":          ("ui", 2, 16, [("random.click", 1.0, 1.5)]),                       # دولاب السحب: تكة زر
    "sh.select":        ("ui", 2, 16, [("note.harp", 0.35, 1.5)]),                          # اختيار: نقرة هارب ناعمة
    "sh.ready":         ("ui", 2, 16, [("note.chime", 0.3, 1.2)]),                          # المهارة جاهزة: رنة جرس ثلج
    "sh.compass":       ("ui", 2, 16, [("lodestone_compass.link_compass_to_lodestone", 0.5, 1.2)]),
    "sh.talk":          ("ui", 2, 16, [("item.book.page_turn", 0.8, 1.0)]),                 # كلام المدرب: تقليب صفحة
    "sh.mission":       ("ui", 2, 16, [("random.toast", 0.7, 1.0)]),                        # مهمة: صوت إشعار الإنجاز
    "sh.level_up":      ("ui", 2, 16, [("random.levelup", 0.5, 1.0)]),
    "sh.rank_up":       ("ui", 2, 24, [("beacon.activate", 0.6, 1.2)]),                     # رتبة: تشغيل المنارة
    "sh.kat_levelup":   ("ui", 2, 16, [("smithing_table.use", 0.6, 0.9)]),                  # سلاح ليفل 4: طاولة الحدادة
    # ── الوحوش ──
    "sh.guard_slam":    ("hostile", 6, 40, [("mace.smash_ground", 0.7, 0.9)]),              # ضربة أرض ثقيلة
    "sh.guard_windup":  ("hostile", 4, 32, [("mob.irongolem.throw", 0.7, 0.8)]),            # تحضير الرمية/الحفر
    "sh.imp_pounce":    ("hostile", 4, 32, [("mob.vex.charge", 0.7, 1.1)]),                 # انقضاض العفريت
    "sh.imp_windup":    ("hostile", 4, 32, [("mob.blaze.breathe", 0.7, 1.2)]),              # نفس النار قبل الكرة
    # ── الأسلحة ──
    "sh.dagger_hit":    ("player", 3, 20, [("item.spear.attack_hit", 0.6, 1.25)]),          # نصل خفيف (خنجر، سيف النور، الظل، الكاتانا)
    "sh.cleaver_hit":   ("player", 3, 20, [("mob.irongolem.hit", 0.55, 1.1)]),              # ساطور ثقيل: رنة حديد
    "sh.kat_step":      ("player", 3, 24, [("mob.endermen.portal", 0.5, 1.3)]),             # خطوة الكاتانا: انتقال
    "sh.kat_wave":      ("player", 3, 24, [("item.trident.riptide_1", 0.5, 1.3)]),          # موجة الهلال
    "sh.kat_exec":      ("player", 4, 32, [("mace.smash_air", 0.7, 1.0)]),                  # الإعدام
    # ── كاتب القوانين: أجراس ومراسي ──
    "sh.absolute":      ("player", 6, 48, [("block.bell.hit", 0.8, 0.6)]),                  # الحكم المطلق: دقة جرس
    "sh.seal":          ("player", 4, 32, [("respawn_anchor.charge", 0.7, 1.0)]),
    "sh.silence":       ("player", 4, 32, [("respawn_anchor.deplete", 0.7, 0.9)]),
    "sh.weight":        ("player", 4, 32, [("random.anvil_land", 0.5, 0.7)]),
    "sh.reflect":       ("player", 4, 32, [("chime.amethyst_block", 0.9, 1.0)]),
    "sh.boundary":      ("player", 6, 40, [("trial_spawner.charge_activate", 0.7, 1.0)]),   # الحاجز + بداية موجة الصدع
    # ── المحاسب: أصوات الخزنة (vault) ──
    "sh.divide":        ("player", 4, 32, [("vault.eject_item", 0.8, 1.1)]),
    "sh.transfer":      ("player", 4, 32, [("vault.insert_item", 0.8, 1.0)]),
    "sh.zero":          ("player", 4, 32, [("vault.deactivate", 0.8, 0.9)]),
    "sh.subtract":      ("player", 4, 32, [("vault.close_shutter", 0.8, 1.0)]),
    # ── ناسج الصدى: الوردن والسكلك والأميثيست ──
    "sh.chorus":        ("player", 4, 32, [("resonate.amethyst_block", 0.9, 1.0)]),
    "sh.echostrike":    ("player", 4, 32, [("note.bassattack", 0.6, 1.0)]),
    "sh.echowave":      ("player", 6, 48, [("mob.warden.sonic_boom", 0.45, 1.1)]),
    "sh.echoseal":      ("player", 4, 32, [("bloom.sculk_catalyst", 0.8, 1.0)]),
    "sh.sonar":         ("player", 4, 32, [("power.on.sculk_sensor", 0.8, 1.0)]),
    # ── محرف المسافة: انتقال وريح ──
    "sh.fold":          ("player", 4, 32, [("mob.evocation_illager.cast_spell", 0.6, 1.2)]),
    "sh.pull":          ("player", 4, 32, [("mob.breeze.inhale", 0.8, 1.0)]),
    "sh.push":          ("player", 4, 32, [("wind_charge.burst", 0.6, 1.0)]),
    "sh.swap":          ("player", 4, 32, [("mob.shulker.teleport", 0.7, 1.0)]),
    "sh.spacecollapse": ("player", 6, 48, [("random.explode", 0.45, 0.6)]),
    # ── البلور ──
    "sh.collapse":      ("player", 4, 32, [("break.amethyst_cluster", 0.9, 0.9)]),          # انكسار السجن والتفجير
    # ── سيد النجوم ──
    "sh.meteor_fall":   ("player", 6, 48, [("mob.ghast.fireball", 0.6, 0.6)]),
    "sh.meteor_hit":    ("player", 6, 48, [("random.explode", 0.5, 0.9)]),
    "sh.gravwell":      ("player", 4, 40, [("mob.breeze.whirl", 0.7, 0.7)]),
    "sh.const_mark":    ("player", 4, 32, [("firework.twinkle", 0.5, 1.2)]),
    "sh.const_zap":     ("player", 4, 32, [("firework.blast", 0.6, 1.3)]),
    "sh.stardash":      ("player", 4, 32, [("firework.launch", 0.6, 1.3)]),
    "sh.supernova_charge": ("player", 6, 48, [("mob.warden.sonic_charge", 0.5, 1.2)]),
    "sh.supernova_boom":   ("player", 6, 48, [("firework.large_blast", 0.7, 0.85)]),
    "sh.orbit":         ("player", 4, 32, [("conduit.short", 0.6, 1.0)]),
    # ── الصدع والسحب ──
    "sh.blackhole":     ("player", 6, 48, [("portal.trigger", 0.35, 0.8)]),
    "sh.blackhole_end": ("player", 6, 48, [("beacon.deactivate", 0.8, 0.8)]),
    # ── صفات سيف الشبح ──
    "sh.trait_rock":    ("player", 4, 32, [("mace.smash_ground", 0.5, 1.2)]),
    "sh.trait_fangs":   ("player", 4, 32, [("mob.evocation_fangs.attack", 0.7, 1.0)]),
    "sh.trait_wings":   ("player", 4, 32, [("mob.phantom.flap", 0.8, 1.0)]),
    "sh.trait_eye":     ("player", 4, 32, [("block.end_portal_frame.fill", 0.7, 1.0)]),
    # ── v1.39 الحاصد الأجوف: دمية خشب (أصوات الـCreaking)، خيوط (وتر قوس النشاب)، لعنة (الحارس الكبير)، منجل (الترايدنت) ──
    "sh.harv_twitch":      ("hostile", 4, 28, [("mob.creaking.twitch", 0.8, 1.0)]),                 # رجة مفصل خشبي (حركة دمية)
    "sh.harv_sway":        ("hostile", 4, 28, [("mob.creaking.sway", 0.7, 0.9)]),                    # صرير تمايل
    "sh.harv_string_cast": ("hostile", 4, 32, [("crossbow.loading.start", 0.8, 0.8)]),              # الخيط ينطلق
    "sh.harv_string":      ("hostile", 4, 32, [("crossbow.loading.middle", 0.7, 0.7)]),             # الخيط يتشد
    "sh.harv_yank":        ("hostile", 4, 32, [("crossbow.shoot", 0.7, 0.7)]),                      # السحبة: طقة وتر
    "sh.harv_snap":        ("hostile", 4, 28, [("random.bowhit", 0.7, 1.3)]),                       # الخيط انقطع
    "sh.harv_stare":       ("hostile", 6, 40, [("mob.elderguardian.curse", 0.4, 1.15)]),            # النظرة: لعنة الحارس الكبير (واطية ومختصرة)
    "sh.harv_reap_raise":  ("hostile", 4, 32, [("mob.evocation_illager.prepare_attack", 0.6, 0.8)]),# رفع المنجل
    "sh.harv_reap":        ("hostile", 6, 36, [("item.trident.riptide_1", 0.5, 0.75)]),             # الحصدة: هبة ثقيلة
    "sh.harv_seal":        ("hostile", 4, 28, [("respawn_anchor.deplete", 0.7, 1.25)]),             # الختم: مرساة تنطفي
    "sh.harv_seal_tail":   ("hostile", 4, 24, [("block.enchanting_table.use", 0.6, 0.7)]),          # ذيل الختم: حروف سحر
    "sh.harv_burn":        ("hostile", 4, 28, [("fire.ignite", 0.8, 0.9)]),                         # يشتعل
    "sh.harv_death":       ("hostile", 6, 40, [("mob.creaking.death", 0.8, 0.9)]),
    # ── منجل الحاصد (سلاح اللاعب) ──
    "sh.scythe_swing":     ("player", 3, 20, [("item.spear.attack_miss", 0.6, 0.8)]),              # هبة نصل طويل
    "sh.scythe_hit":       ("player", 3, 20, [("item.trident.hit", 0.5, 0.85)]),                   # قطع
    "sh.scythe_reap":      ("player", 4, 28, [("item.trident.riptide_1", 0.4, 0.95)]),
    "sh.scythe_string":    ("player", 4, 28, [("crossbow.loading.middle", 0.6, 0.85)]),
    "sh.scythe_yank":      ("player", 4, 28, [("crossbow.shoot", 0.6, 0.85)]),
    # ── v1.39 لعنة القرويين: نبض، همس كهف نادر، وتحول ──
    "sh.curse_mark":       ("hostile", 3, 20, [("mob.warden.heartbeat", 0.6, 1.3)]),               # نبضة: البقع السود تكبر
    "sh.curse_whisper":    ("hostile", 2, 16, [("ambient.cave", 0.25, 1.1)]),                      # همس (نادر)
    "sh.curse_turn":       ("hostile", 6, 48, [("mob.zombie.remedy", 0.7, 0.7)]),                  # بداية التحول
    "sh.curse_burst":      ("hostile", 8, 48, [("mob.husk.convert_to_zombie", 0.9, 0.8)]),         # لحظة التحول
    "sh.curse_free":       ("hostile", 4, 32, [("mob.zombie.unfect", 0.7, 1.1)]),                  # اللعنة انفكت (صوت شفاء القروي الزومبي)
}

# v1.39: أصوات الوحوش نفسها (ضربة، موت، جو، خطوات) بـ RP/sounds.json — قبل كانت الوحوش ساكتة تماماً لما تنضرب أو تموت.
# كل وحش أخذ أصوات موب فانيلا يناسب طبيعته وبطبقة مختلفة حتى يتميز: (علو، [أقل طبقة، أكثر طبقة]، {الحدث: صوت أو (صوت، علو، طبقة)})
ENTITY_SOUNDS = {
    "sh:training_archer": (0.9, [0.95, 1.05], {"ambient": "mob.skeleton.say", "hurt": "mob.skeleton.hurt", "death": "mob.skeleton.death", "step": ("mob.skeleton.step", 0.4, 1.0)}),
    "sh:ember_imp": (0.9, [1.25, 1.4], {"ambient": ("mob.blaze.breathe", 0.6, 1.3), "hurt": "mob.blaze.hit", "death": "mob.blaze.death"}),
    "sh:rust_guard": (1.0, [0.8, 0.9], {"hurt": "mob.irongolem.hit", "death": "mob.irongolem.death", "step": ("mob.irongolem.walk", 0.6, 0.9)}),
    "sh:shadow_hound": (1.0, [0.8, 0.9], {"ambient": "mob.wolf.growl", "hurt": "mob.wolf.hurt", "death": "mob.wolf.death", "step": ("mob.wolf.step", 0.4, 1.0)}),
    "sh:sand_scorpion": (0.9, [0.8, 0.9], {"ambient": "mob.spider.say", "hurt": "mob.spider.say", "death": "mob.spider.death", "step": ("mob.spider.step", 0.4, 1.0)}),
    "sh:gloomhorn": (1.0, [0.6, 0.7], {"ambient": "mob.goat.ambient", "hurt": "mob.skeleton.hurt", "death": "mob.goat.death", "step": ("mob.goat.step", 0.5, 0.8)}),
    "sh:hollow_seer": (1.0, [0.8, 0.9], {"ambient": "mob.guardian.land_idle", "hurt": "mob.guardian.land_hit", "death": "mob.guardian.land_death"}),
    "sh:veilfox": (1.0, [0.9, 1.0], {"ambient": "mob.fox.ambient", "hurt": "mob.fox.hurt", "death": "mob.fox.death"}),
    "sh:magmamoth": (1.0, [0.7, 0.8], {"ambient": "mob.ravager.ambient", "hurt": "mob.ravager.hurt", "death": "mob.ravager.death", "step": ("mob.ravager.step", 0.6, 0.8)}),
    "sh:grey_bear": (1.0, [0.85, 0.95], {"ambient": "mob.polarbear.idle", "hurt": "mob.polarbear.hurt", "death": "mob.polarbear.death", "step": ("mob.polarbear.step", 0.5, 0.9)}),
    "sh:bear_cub": (0.8, [1.3, 1.5], {"ambient": "mob.polarbear_baby.idle", "hurt": "mob.polarbear.hurt", "death": "mob.polarbear.death", "step": ("mob.polarbear.step", 0.3, 1.4)}),
    "sh:prayer_mantis": (1.0, [0.65, 0.75], {"ambient": "mob.silverfish.say", "hurt": "mob.silverfish.hit", "death": "mob.silverfish.kill", "step": ("mob.spider.step", 0.4, 1.2)}),
    "sh:hollow_harvester": (1.0, [0.9, 1.05], {"ambient": "mob.creaking.ambient", "hurt": "mob.creaking.sway", "death": "mob.creaking.death", "step": ("mob.creaking.step", 0.5, 1.0)}),
    "sh:cursed_villager": (1.0, [0.72, 0.82], {"ambient": "mob.villager.idle", "hurt": "mob.villager.hit", "death": "mob.villager.death"}),   # قروي مريض: طبقة أوطى
}
# ملفات الكيانات (BP) اللي تحتاج المكون الرسمي minecraft:ambient_sound_interval حتى صوت "الجو" يشتغل (كل كم ثانية)
ENTITY_FILES = {"sh:training_archer": "sh_training_archer", "sh:ember_imp": "ember_imp", "sh:rust_guard": "rust_guard", "sh:shadow_hound": "shadow_hound",
                "sh:sand_scorpion": "sand_scorpion", "sh:gloomhorn": "sh_gloomhorn", "sh:hollow_seer": "sh_hollow_seer", "sh:veilfox": "sh_veilfox",
                "sh:magmamoth": "sh_magmamoth", "sh:grey_bear": "sh_grey_bear", "sh:bear_cub": "sh_bear_cub", "sh:prayer_mantis": "sh_prayer_mantis",
                "sh:hollow_harvester": "sh_hollow_harvester", "sh:cursed_villager": "sh_cursed_villager"}


def entity_sounds():
    ents = {}
    for ident, (vol, pitch, evs) in ENTITY_SOUNDS.items():
        out = {}
        for ev, snd in evs.items():
            out[ev] = snd if isinstance(snd, str) else {"sound": snd[0], "volume": snd[1], "pitch": snd[2]}
        ents[ident] = {"volume": vol, "pitch": pitch, "events": out}
    with open(os.path.join(RP, "sounds.json"), "w", encoding="utf-8") as f:
        json.dump({"entity_sounds": {"entities": ents}}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    bp = os.path.join(ROOT, "AnimePowers", "BP", "entities")
    n = 0
    for ident, fn in ENTITY_FILES.items():
        if "ambient" not in ENTITY_SOUNDS[ident][2]:
            continue
        p = os.path.join(bp, fn + ".json")
        d = json.load(open(p, encoding="utf-8"))
        comps = d["minecraft:entity"]["components"]
        want = {"value": 8.0, "range": 12.0, "event_name": "ambient"}
        if comps.get("minecraft:ambient_sound_interval") != want:
            comps["minecraft:ambient_sound_interval"] = want
            raw = open(p, encoding="utf-8").read()
            ind = 1 if raw.startswith("{\n \"") else 2 if raw.startswith("{\n  \"") else 4
            with open(p, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=ind, ensure_ascii=False)
            n += 1
    return len(ents), n


def files_of(vdefs, ev):
    out = []
    for s in vdefs[ev]["sounds"]:
        if isinstance(s, str):
            s = {"name": s}
        out.append(s)
    return out


def main():
    if len(sys.argv) > 1:                                                       # أول مرة: تصغير نسخة Mojang الكاملة للأحداث اللي نستعملها
        full = json.load(open(sys.argv[1], encoding="utf-8"))
        full = full.get("sound_definitions", full)
        need = sorted({ev for *_, lst in SOUNDS.values() for ev, _, _ in lst} | {(v if isinstance(v, str) else v[0]) for *_, evs in ENTITY_SOUNDS.values() for v in evs.values()})
        json.dump({ev: {"sounds": full[ev]["sounds"]} for ev in need}, open(VANILLA, "w", encoding="utf-8"), indent=1)
    vdefs = json.load(open(VANILLA, encoding="utf-8"))
    d = json.load(open(DEFS, encoding="utf-8"))
    sd = {k: v for k, v in d["sound_definitions"].items() if not k.startswith("sh.")}
    for name, (cat, mind, maxd, lst) in SOUNDS.items():
        snds = []
        for ev, vol, pit in lst:
            for f in files_of(vdefs, ev):
                e = {"name": f["name"], "volume": round(max(0.05, min(0.95, f.get("volume", 1.0) * vol)), 3)}
                p = round(f.get("pitch", 1.0) * pit, 3)
                if p != 1.0:
                    e["pitch"] = p
                snds.append(e)
        sd[name] = {"category": cat, "min_distance": mind, "max_distance": maxd, "sounds": snds}
    d["sound_definitions"] = dict(sorted(sd.items()))
    with open(DEFS, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    gone = 0
    sh_dir = os.path.join(RP, "sounds", "sh")
    if os.path.isdir(sh_dir):                                                   # الأصوات المصنوعة بالكود (قبل 1.37.3) انشالت
        for f in os.listdir(sh_dir):
            if f.endswith(".ogg"):
                os.remove(os.path.join(sh_dir, f)); gone += 1
        if not os.listdir(sh_dir):
            os.rmdir(sh_dir)
    ne, nb = entity_sounds()
    print(f"sounds ok: {len(SOUNDS)} أصوات من ملفات ماينكرافت | انشال {gone} صوت مصنوع | أصوات {ne} وحش (عدلت {nb} ملف كيان)")


if __name__ == "__main__":
    main()
