# Anime Powers (عالم القدرات)

مود أنمي أصلي لماينكرافت Bedrock (نسخة **1.15.1**، يتطلب ماينكرافت 26.50 أو أحدث): قدرات بندرات، رتب، مدرب، وحوش، أسلحة وبنايات.
الشرح الكامل للمود بالعراقي بملف [`MOD_GUIDE.md`](MOD_GUIDE.md).

## الهيكل

```
AnimePowers/BP   حزمة السلوك (سكربتات، كيانات، أيتمات)
AnimePowers/RP   حزمة الموارد (موديلات، تكستشر، أصوات، لغة)
tools/           (gen_fx_shapes.py أشكال المهارات 3D، gen_book_icons.py أيقونات الكتب، gen_skill_hands.py مهارات ما تطلع بالإيد، gen_hud_art.py رسومات الـHUD، gen_weapons3d.py أسلحة 3D، gen_icons2d.py أيقونات، gen_monster_mods.py تحسين الوحوش) فحص + تغليف + محاكي (tools/sim) + مولدات الأصول + أدوات الوحوش (mobkit, render)
extend*.py       مولدات الموديلات والتكستشرات (تشغّل من جذر المشروع)
```

## التغليف والفحص

```bash
python3 tools/check.py      # يفحص سلامة المود
python3 tools/package.py    # يفحص ثم يطلع dist/AnimePowers_v<النسخة>.mcaddon
```

- يحتاج Python 3 فقط. `node` اختياري (لفحص صياغة JS).
- الملف الناتج يحتوي `SH_BP` و`SH_RP`، وتفتحه على اللعبة مباشرة (أو iPhone).
- الناتج ثابت: نفس المحتوى يعطي نفس الملف بالبايت.

## قواعد مهمة

- **لا تغيّر الـ UUID** بالمنفستين، يكسر التحديث. `tools/uuids.lock.json` يحرسها، والفحص يفشل إذا تغيرت.
- لتحديث النسخة: غيّر `header.version` بالمنفستين (لازم يتطابقان) ثم غلّف.
- لا تشغل `build.py` القديم (مو موجود هنا) لأنه يولد UUID جديدة.
- إذا طلع خطأ باللعبة: Settings > Creator > Enable Content Log GUI.

## ما يفحصه `check.py`

JSON سليم، صياغة JS، UUID مطابقة للقفل، تطابق النسخ، أيقونات الأيتمات وصورها، أيتمات المهارات المستعملة بالسكربت،
الأصوات (معرّفة وملفاتها موجودة)، تطابق كيانات BP وRP، وأن كل كيان له اسم بملف اللغة الإنجليزي (en_US). كل نصوص اللعبة إنجليزية.
ويشغّل المحاكي (`node`) على عالم وهمي. المحاكي ما يغني عن اختبار اللعبة الحقيقية.

للتجربة داخل اللعبة: `/scriptevent sh:shard` (شظية نجمة جديدة للسحب)، `/scriptevent sh:power star` ثم `/scriptevent sh:unlock`، `/scriptevent sh:weapons` (كل الأسلحة + لفائف)، `/scriptevent sh:rift blue` (يفتح صدع قربك: blue violet crimson abyss، و`close` يسده).
