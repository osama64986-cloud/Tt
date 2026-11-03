"""ضبط علو أصوات المود (v1.37): كل صوت بعلو متوسط مريح بدل ما يكون عالي ويزعج.
البحث (Microsoft Learn: Introduction to Sounds، /playsound، WorldSoundOptions):
  - علو الملف نفسه نضبطه بـ"volume" لكل صوت بـ sound_definitions.json (بدون ما نعيد ترميز الملف، فما تنقص جودته ويرجع بسهولة).
  - "category" تخلي اللاعب يتحكم بالصوت من إعدادات اللعبة (ui للأصوات الصغيرة والتنبيهات، hostile للوحوش، player للمهارات).
  - volume بـ playSound: أقل من 1 يوطي الصوت، وفوق 1 بس يوسع مسافة السماع (مو أعلى).
القياس: ffmpeg (ebur128 + volumedetect). العلو = أعلى ارتفاع لحظي (Momentary LUFS)، وللملفات القصيرة (أقل من 0.4 ثانية) متوسط القدرة.
الملفات كانت مضغوطة لحد -1 dBFS وأعلى لحظة بيها حوالي -10 لـ -13 LUFS (عالية لأصوات مؤثرات).
الأهداف: الأحداث الكبيرة -16، الوحوش -18، الترقيات -19، المهارات والضربات -20، الأصوات الصغيرة والتنبيهات -23 LUFS.
التشغيل: python3 tools/tune_sounds.py  (يكتب sound_definitions.json وتقرير بـ tools/sound_levels.json)"""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
DEFS = os.path.join(RP, "sounds", "sound_definitions.json")

BIG = {"sh.supernova_boom", "sh.blackhole", "sh.blackhole_end", "sh.spacecollapse", "sh.meteor_hit", "sh.meteor_fall", "sh.absolute", "sh.collapse",
       "sh.zero", "sh.weight", "sh.gravwell", "sh.supernova_charge", "sh.kat_storm", "sh.boundary", "sh.echowave"}
HOSTILE = {"sh.guard_slam", "sh.guard_windup", "sh.imp_pounce", "sh.imp_windup"}
LEVEL = {"sh.level_up", "sh.rank_up", "sh.kat_levelup"}
SMALL = {"sh.tick", "sh.select", "sh.ready", "sh.compass", "sh.talk", "sh.mission", "sh.const_mark", "sh.orbit", "sh.trait_eye", "sh.swap"}
UI = {"sh.tick", "sh.select", "sh.ready", "sh.compass", "sh.talk", "sh.mission"} | LEVEL


def target(name):
    if name in HOSTILE:
        return -18.0
    if name in BIG:
        return -16.0
    if name in LEVEL:
        return -19.0
    if name in SMALL:
        return -23.0
    return -20.0


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect,ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    mean = float(re.search(r"mean_volume: (-?[\d.]+)", r).group(1))
    peak = float(re.search(r"max_volume: (-?[\d.]+)", r).group(1))
    ms = [float(x) for x in re.findall(r" M:\s*(-?[\d.]+)", r)]
    m = max(ms) if ms else -120.0
    loud = m if m > -70 else mean + 1.0                                         # ملف قصير: ما يكفي للقياس اللحظي (400ms)
    return {"mean_db": mean, "peak_db": peak, "max_momentary": m, "loudness": round(loud, 1)}


def main():
    d = json.load(open(DEFS, encoding="utf-8"))
    report = {}
    for name, sd in d["sound_definitions"].items():
        if not name.startswith("sh."):
            continue
        sd["category"] = "ui" if name in UI else "hostile" if name in HOSTILE else "player"
        for snd in sd.get("sounds", []):
            if not isinstance(snd, dict):
                continue
            m = measure(os.path.join(RP, snd["name"] + ".ogg"))
            vol = 10 ** ((target(name) - m["loudness"]) / 20)
            snd["volume"] = round(max(0.15, min(1.0, vol)), 2)
            report[name] = {**m, "target": target(name), "volume": snd["volume"], "category": sd["category"],
                            "result": round(m["loudness"] + 20 * __import__("math").log10(snd["volume"]), 1)}
    with open(DEFS, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    with open(os.path.join(ROOT, "tools", "sound_levels.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    vols = [r["volume"] for r in report.values()]
    print(f"sounds tuned: {len(report)} | volume min {min(vols)} max {max(vols)} | ui {sum(r['category'] == 'ui' for r in report.values())}")


if __name__ == "__main__":
    main()
