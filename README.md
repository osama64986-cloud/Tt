# Etheria V1 (إثيريا)

مود أنمي أصلي لماينكرافت Bedrock (نسخة **V1**، الإصدار 1.42.0، يتطلب ماينكرافت 26.50 أو أحدث): قدرات بندرات، رتب، مدرب، وحوش، أسلحة، بنايات، **مدينة Aetheria الملكية** (248×248 بحراس وملك وسكان)، طور قصة، وعربي وإنكليزي من إعدادات المود.
الشرح الكامل للمود بالعراقي بملف [`MOD_GUIDE.md`](MOD_GUIDE.md).

## الهيكل

```
AnimePowers/BP   حزمة السلوك (سكربتات، كيانات، أيتمات)
AnimePowers/RP   حزمة الموارد (موديلات، تكستشر، أصوات، لغة)
tools/           (gen_fx_shapes.py أشكال المهارات 3D، gen_book_icons.py أيقونات الكتب، gen_skill_hands.py مهارات ما تطلع بالإيد، gen_hud_art.py رسومات الـHUD، gen_weapons3d.py أسلحة 3D، gen_icons2d.py أيقونات، gen_monster_mods.py تحسين الوحوش، gen_gear.py العتاد والجرعات، gen_achievements.py الإنجازات وصورها، gen_alchemy_ui.py صور شاشة الخيميائي، gen_sounds.py أصوات المود من ملفات ماينكرافت وأصوات الوحوش، gen_ores.py الخامات وتوليدها تحت الأرض، gen_player_anims.py أنميشن اللاعب، gen_harvester.py الحاصد الأجوف ومنجله، gen_curse.py لعنة القرويين، gen_city_npcs.py سكان مدينة Aetheria، check_city.py فحص المدينة ورسمها، gen_i18n.py قاموس العربي من tools/i18n/ar.json) فحص + تغليف + محاكي (tools/sim) + مولدات الأصول + أدوات الوحوش (mobkit, render)
extend*.py       مولدات الموديلات والتكستشرات (تشغّل من جذر المشروع)
BP/scripts/city_plan.js    مخطط مدينة Aetheria (248×248) كبيانات، city_raster.js يحوله لبلوكات، city.js يبنيها بالعالم مرة وحدة
```

## التغليف والفحص

```bash
python3 tools/check.py      # يفحص سلامة المود
python3 tools/package.py    # يفحص ثم يطلع dist/Etheria_V1.mcaddon
python3 tools/gen_i18n.py   # يبني القاموس العربي (scripts/lang_ar.js) ويطبع النصوص اللي بدون ترجمة
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
الأصوات (معرّفة وملفاتها موجودة)، تطابق كيانات BP وRP، وأن كل كيان له اسم بملف اللغة الإنجليزي (en_US). نصوص المود إنجليزية بالكود، والعربي يجي من القاموس (`tools/i18n/ar.json`) ويتشكل وينقلب بـ `scripts/i18n.js`.
ويشغّل المحاكي (`node`) على عالم وهمي. المحاكي ما يغني عن اختبار اللعبة الحقيقية.

للتجربة داخل اللعبة: `/scriptevent sh:temple` (يدلك على معبد النجمة، ويبنيه قربك إذا بعده ما انبنى: مرة وحدة بالعالم)، `/scriptevent sh:redraw` (يشيل قدرتك حتى تسحب من جديد)، `/scriptevent sh:power unbound` (بلا قدرة)، `/scriptevent sh:power star` ثم `/scriptevent sh:unlock`، `/scriptevent sh:weapons` (كل الأسلحة الثمانية + لفائف)، `/scriptevent sh:wlv 4` (ليفل السلاح اللي بإيدك)، `/scriptevent sh:rhythm` (تدريب ضربة الإيقاع: يكلك مبكر/متأخر/على الإيقاع)، `/scriptevent sh:rift blue` (يفتح صدع قربك: blue violet crimson abyss، و`close` يسده).
