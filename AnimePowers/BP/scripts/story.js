// ═══════════════════════════ إثيريا V1: الحكاية وطور القصة ═══════════════════════════
// بيانات بس (بدون منطق اللعبة): كل نص بلغتين { en, ar }. العربي يتشكّل ويتقلب لليمين بـ i18n.js وقت العرض.
//  • CHRONICLE: «سجلّ إثيريا»، قصة نشأة العالم: مقدمة مفتوحة دائماً + 7 فصول، فصل لكل رتبة (يبقى للرتب معنى بالحكاية).
//  • STORY: طور القصة: فصول، وكل فصل خطوات (مهمة واحدة لكل خطوة). الخطوة تنفتح لما تخلص اللي قبلها،
//    مهمتها تطلع صغيرة فوق يمين الشاشة، ولما تخلص تكتب "اكتملت المهمة" وتختفي، وبعدها تطلع اللي بعدها.
//    metric = نفس مقاييس المهمات (MIS_METRIC بـ main.js). delta = العد يبدأ من لحظة ما تنفتح الخطوة.

export const CHRONICLE_TITLE = { en: "The Chronicle of Etheria", ar: "سجلّ إثيريا" };

// [العنوان، النص]. الأول (المقدمة) مفتوح دائماً، والباقي: الفصل i ينفتح برتبة i-1 (مبتدئ = الفصل 1)
export const CHRONICLE = [
  [{ en: "Before the First Dawn", ar: "قبل الفجر الأول" },
    {
      en: "Before the first sky, there was only the Ether: a silent sea of light without shore or name. Where the Ether grew still, it hardened into mountains; where it flowed, it became rivers; and where it dreamed, it woke as life. The first world to wake from that dream was named Etheria.\n\nFor an age Etheria knew no night. When the Ether at last grew weary, darkness came for the first time, and the newborn world learned two things at once: fear, and hope. To guard that hope, the Ether gathered the last of its light into a single star and set it above the world: the Dawn Star, so that every night would have an end.",
      ar: "قبل أن توجد السماء الأولى، لم يكن هناك سوى الأثير: بحرٌ صامتٌ من النور بلا شاطئٍ ولا اسم. حيث سكن الأثير تصلّب جبالًا، وحيث جرى صار أنهارًا، وحيث حلم استيقظ حياةً. وأول عالمٍ استيقظ من ذلك الحلم سُمّي إثيريا.\n\nعاشت إثيريا دهرًا لا تعرف الليل. فلما تعب الأثير أخيرًا، هبطت الظلمة لأول مرة، فتعلّم العالم الوليد أمرين معًا: الخوف والرجاء. ولكي يحرس الأثير ذلك الرجاء، جمع آخر نوره في نجمةٍ واحدة ورفعها فوق العالم: نجمة الفجر، كي يكون لكل ليلٍ نهاية.",
    }],
  [{ en: "The Night the Star Fell", ar: "ليلة سقوط النجمة" },
    {
      en: "A thousand years ago, on the longest night Etheria remembers, the Dawn Star fell. Its fire went out in the sky, but its heart did not: it froze into a crystal and sank into the earth, and wherever its light reached, a temple of white stone grew around it.\n\nWhoever steps into that light draws a power, and the crystal shows its worth in color: white for the common, then green, blue, violet, gold, and the red of the rarest. Once in two hundred souls the crystal stays dark. Those are the Unbound: no power answers them, so their own bodies grow stronger instead. Only one Star Temple stands in each world. Find it, and your story begins.",
      ar: "قبل ألف عام، في أطول ليلةٍ تذكرها إثيريا، سقطت نجمة الفجر. انطفأت نارها في السماء، لكن قلبها لم ينطفئ: تجمّد بلورةً وغاص في الأرض، وحيثما وصل نوره نبت حوله معبدٌ من الحجر الأبيض.\n\nمن يخطو إلى ذلك النور ينال قوة، وتكشف البلورة قدرها باللون: الأبيض للشائع، ثم الأخضر والأزرق والبنفسجي والذهبي، والأحمر للأندر. ومرةً في كل مئتي روح تبقى البلورة مظلمة؛ أولئك هم الطلقاء: لا تجيبهم أي قوة، فتشتدّ أجسادهم بدلًا منها. ولا يقوم في كل عالمٍ إلا معبد نجمةٍ واحد. اعثر عليه، تبدأ حكايتك.",
    }],
  [{ en: "The Order of Dawn", ar: "جماعة الفجر" },
    {
      en: "The first who carried powers swore an oath beneath the fallen star and named themselves the Order of Dawn. They set seven ranks, one for each night the star burned before it fell: Novice, Trainee, Warrior, Elite, Commander, Legend and Master. No rank was ever given by birth or gold, only by what you defeat and what you learn.\n\nThe Order built Sakura Village as its first home and planted pink trees so it would remember that beauty deserves protection. Today only two of the Order remain: the Trainer, who still teaches anyone brave enough to ask, and the old Alchemist, who brews the soul flames of fallen monsters into potions.",
      ar: "أقسم أول من حملوا القوى قسمًا تحت النجمة الساقطة، وسمّوا أنفسهم «جماعة الفجر». ووضعوا سبع رتب، رتبةً لكل ليلةٍ اشتعلت فيها النجمة قبل سقوطها: مبتدئ، متدرّب، محارب، نخبة، قائد، أسطورة، وسيّد. لم تُمنح رتبةٌ قطّ بالنسب أو الذهب، بل بما تهزمه وما تتعلّمه.\n\nبنت الجماعة قرية الساكورا بيتًا أول لها، وزرعت أشجارها الوردية كي تتذكّر أن الجمال يستحق الحماية. ولم يبقَ اليوم من الجماعة إلا اثنان: المدرّب، الذي ما زال يعلّم كل من يجرؤ على السؤال، والخيميائي العجوز، الذي يقطّر لهب أرواح الوحوش الساقطة جرعاتٍ.",
    }],
  [{ en: "The Abyss", ar: "الهاوية" },
    {
      en: "But the Dawn Star did not fall alone. A shadow followed it down, as a shadow follows its owner: the Abyss, the Ether's own darkness, hollow and hungry. Whatever it touches loses its color first, then its name.\n\nFrom the Abyss come the creatures you fight, ranked by how deeply it has claimed them. The Lowly are its first spawn: the Ember Imp, born from the ashes of burned villages; the Rust Guard, which watched a temple until it forgot what it guarded; the Shadow Hound, hunting on the star's old trail; and the Sand Scorpion, with the Abyss's venom in its tail. The Grim stalk travellers at dusk: the Gloomhorn, the Hollow Seer and the Veilfox. The Vile were beasts before the Abyss tainted them, like the Grey Bear and the Magmamoth. And the Cursed, like the Prayer Mantis and the Hollow Harvester, carry the Abyss's own strength. Sometimes it needs no monster at all: it whispers to a villager, and black marks begin to spread.",
      ar: "لكن نجمة الفجر لم تسقط وحدها. تبعها ظلٌّ إلى الأسفل كما يتبع الظلُّ صاحبه: الهاوية، ظلمة الأثير نفسه، جوفاء جائعة. كل ما تلمسه يفقد لونه أولًا، ثم اسمه.\n\nمن الهاوية تأتي المخلوقات التي تقاتلها، وتُرتَّب بقدر ما استحوذت عليها. الوضيعة أول نسلها: عفريت الجمر المولود من رماد القرى المحترقة، وحارس الصدأ الذي حرس معبدًا حتى نسي ما يحرسه، وكلب الظل الذي يصطاد على أثر النجمة القديم، وعقرب الرمل الذي يحمل سمّ الهاوية في ذيله. والقاتمة تتربّص بالمسافرين عند الغسق: القرن القاتم، والرائي الأجوف، وثعلب الحجاب. والخبيثة كانت وحوشًا قبل أن تدنّسها الهاوية، كالدبّ الرمادي والماغماموث. أما الملعونة، كالسرعوف المصلّي والحاصد الأجوف، فتحمل قوة الهاوية ذاتها. وأحيانًا لا تحتاج الهاوية إلى وحش: تهمس لقرويٍّ، فتبدأ العلامات السوداء بالانتشار.",
    }],
  [{ en: "The Rifts", ar: "الصدوع" },
    {
      en: "The Abyss still breathes through wounds in the world: the Rifts. They tear open without warning, rot the ground around them and spill out wave after wave of its creatures. At the end of every Rift waits a Warden, and the color of the wound tells its grade: blue for the first grade, violet for the second, crimson for the third, and the black-gold of the Abyssal Rifts, the fourth and deepest.\n\nSeal a Rift by defeating its Warden. Leave it open, and the Warden walks free into Etheria.",
      ar: "ما زالت الهاوية تتنفّس عبر جراحٍ في العالم: الصدوع. تنفتح دون إنذار، وتُفسد الأرض حولها، وتقذف موجةً تلو موجةٍ من مخلوقاتها. وفي نهاية كل صدعٍ ينتظر حارس، ولون الجرح يكشف درجته: الأزرق للدرجة الأولى، والبنفسجي للثانية، والقرمزي للثالثة، والأسود المذهّب للصدوع الهاوية، الرابعة والأعمق.\n\nأغلق الصدع بهزيمة حارسه. اتركه مفتوحًا، فيخرج الحارس طليقًا إلى إثيريا.",
    }],
  [{ en: "Sunset Palace and the Black Towers", ar: "قصر الغروب والأبراج السوداء" },
    {
      en: "When the Abyss came for the Order, its last commanders made their stand in a palace at the edge of the horizon, Sunset Palace, where the final light of their days fell. The palace fell, but the Abyss paid for it and sank back into the deep. Its halls still hide the weapons the guards could not carry away, and weapons remember: the more you fight with one, the more it gives back.\n\nThe Abyss answered by raising towers of black stone and violet light, seven floors each, so its spawn would have somewhere to wait. Climb one and you will meet the strongest at its summit. Deep below, where the star's fire cooled into the rock, miners find Dawnsteel; deeper still, where the Abyss seeped in, Abyssium glows. Both can be forged into armor.",
      ar: "حين جاءت الهاوية لتنال من الجماعة، وقف آخر قادتها وقفتهم الأخيرة في قصرٍ على حافة الأفق، قصر الغروب، حيث سقط آخر ضوءٍ من أيامهم. سقط القصر، لكن الهاوية دفعت ثمنه وغاصت عائدةً إلى الأعماق. وما زالت قاعاته تُخفي أسلحةً عجز الحرّاس عن حملها، والأسلحة تتذكّر: كلما قاتلتَ بسلاحٍ أكثر، أعطاك أكثر.\n\nفردّت الهاوية برفع أبراجٍ من الحجر الأسود والضوء البنفسجي، سبعة طوابق لكل برج، كي يجد نسلها مكانًا ينتظر فيه. اصعد أحدها وستلقى أقواها عند قمّته. وفي الأعماق، حيث بردت نار النجمة في الصخر، يجد المنقّبون فولاذ الفجر؛ وأعمق من ذلك، حيث تسرّبت الهاوية، يتوهّج معدن الهاوية. وكلاهما يُطرَق دروعًا.",
    }],
  [{ en: "The Two Blades", ar: "النصلان" },
    {
      en: "Light alone could not close the Abyss, so the last smith of the Order forged a blade from its own darkness: the Abyss Katana. Every victory makes it sharper, and every strike takes a little of you. He sealed it in the Dark Sword Shrine beneath two guardians who never sleep, and said: only one who can carry it without being carried by it may lift it.\n\nHis apprentice could not sleep while only darkness guarded the world. From the last light of the fallen star she forged its opposite: the Oath of Light, a silver sword that never dulls, sealed in the Light Sword Shrine beneath a beam that rises to the sky. Each shrine stands only once in the world. Whoever holds both blades holds the balance of Etheria.",
      ar: "لم يكن النور وحده قادرًا على إغلاق الهاوية، فصاغ آخر حدّادي الجماعة نصلًا من ظلمتها نفسها: كاتانا الهاوية. كل نصرٍ يزيدها حدّة، وكل ضربةٍ تأخذ منك قليلًا. وختم عليها في ضريح السيف المظلم تحت حارسين لا ينامان، وقال: لا يرفعها إلا من يحملها دون أن تحمله.\n\nأما تلميذته فلم يغمض لها جفنٌ والظلمة وحدها تحرس العالم. فمن آخر نورٍ في النجمة الساقطة صاغت نقيضها: قَسَم النور، سيفًا فضيًّا لا يكلّ، وختمت عليه في ضريح السيف المضيء تحت شعاعٍ يرتفع إلى السماء. ولا يقوم كل ضريحٍ إلا مرةً واحدة في العالم. ومن حمل النصلين معًا حمل ميزان إثيريا.",
    }],
  [{ en: "The Heart of the Abyss", ar: "قلب الهاوية" },
    {
      en: "You are a Master now, and here is what the Trainer never told you: the Abyss is not an enemy from outside. It is the rest of the Dawn Star, the part that fell into the dark and forgot itself, still searching for its heart: the crystal in the temple. Every Rift is it reaching out. Every creature is its call.\n\nOne day you will have to choose: close the Abyss forever, or return the heart and let the star rise again.\n\n(This chapter continues in Etheria V1.5.)",
      ar: "صرتَ سيّدًا الآن، وإليك ما لم يقله المدرّب قطّ: الهاوية ليست عدوًّا من الخارج. إنها بقية نجمة الفجر، الجزء الذي سقط في الظلام فنسي نفسه، وما زال يبحث عن قلبه: البلورة في المعبد. كل صدعٍ يدٌ تمتدّ منها، وكل مخلوقٍ نداؤها.\n\nوذات يومٍ سيكون عليك أن تختار: أن تغلق الهاوية إلى الأبد، أو أن تُعيد القلب فتنهض النجمة من جديد.\n\n(يُستكمَل هذا الفصل في إثيريا V1.5.)",
    }],
];

// ───────────────────────── طور القصة ─────────────────────────
// كل فصل: { t: العنوان، steps: [ { id، n: الحكاية لما تبدي الخطوة، o: المهمة (قصيرة، تنعرض فوق يمين الشاشة)، metric، need، delta، xp، items } ] }
export const STORY_TITLE = { en: "Story Mode: Heir of the Dawn Star", ar: "طور القصة: وريث نجمة الفجر" };
export const STORY = [
  { t: { en: "Prologue: The Fallen Light", ar: "التمهيد: النور الساقط" }, steps: [
    { id: "awaken", metric: "drawn", need: 1, xp: 60, items: [],
      n: { en: "You open your eyes in Etheria. Far away, a column of pale light rises from a temple of white stone: the place where the heart of the Dawn Star sleeps. It is calling you.",
        ar: "تفتح عينيك في إثيريا. وبعيدًا، يرتفع عمودٌ من نورٍ شاحب فوق معبدٍ من الحجر الأبيض: حيث ينام قلب نجمة الفجر. إنه يناديك." },
      o: { en: "Awaken your power at the Star Temple", ar: "أيقظ قوتك في معبد النجمة" } },
  ] },
  { t: { en: "Chapter I: The Last Teacher", ar: "الفصل الأول: المعلّم الأخير" }, steps: [
    { id: "trained", metric: "trained", need: 1, xp: 80, items: [["sh:xp_scroll_small", 1]],
      n: { en: "The crystal has chosen you. Now you must learn to carry it. Somewhere close, the last teacher of the Order of Dawn waits for a student.",
        ar: "لقد اختارتك البلورة. والآن عليك أن تتعلّم كيف تحملها. وفي مكانٍ قريب، ينتظر آخرُ معلّمي جماعة الفجر تلميذًا." },
      o: { en: "Complete the Trainer's training", ar: "أكمل تدريب المدرّب" } },
    { id: "hunt", metric: "kills", need: 5, delta: true, xp: 80, items: [["minecraft:bread", 6]],
      n: { en: "The Trainer's words still ring in your ears: a power never tested is only a promise. The creatures of the Abyss roam at night. Put your gift to the test.",
        ar: "ما زالت كلمات المدرّب ترنّ في أذنيك: القوة التي لم تُختبر ليست إلا وعدًا. ومخلوقات الهاوية تجوب الليل. فاختبر هبتك." },
      o: { en: "Defeat monsters of the Abyss", ar: "اهزم وحوش الهاوية" } },
  ] },
  { t: { en: "Chapter II: Petals and Ashes", ar: "الفصل الثاني: بتلاتٌ ورماد" }, steps: [
    { id: "alchemist", metric: "alchemist", need: 1, xp: 100, items: [["minecraft:glass_bottle", 4]],
      n: { en: "Every fallen monster leaves a soul flame behind. The Trainer once spoke of an old brewer in a village of pink trees who knows what to do with them.",
        ar: "كل وحشٍ يسقط يترك خلفه لهب روح. وقد حدّثك المدرّب يومًا عن خيميائيٍّ عجوز في قريةٍ ذات أشجار وردية يعرف ما يُصنع بها." },
      o: { en: "Meet the Alchemist in a Sakura Village", ar: "قابل الخيميائي في قرية الساكورا" } },
    { id: "ore", metric: "ores", need: 3, delta: true, xp: 120, items: [["sh:xp_scroll_small", 1]],
      n: { en: "The Alchemist taps the edge of your blade. \"Power wears thin without good steel. Dig deep, where the star's fire cooled into the rock.\"",
        ar: "ينقر الخيميائي حدّ نصلك ويقول: «القوة تبلى بلا فولاذٍ جيد. احفر عميقًا، حيث بردت نار النجمة في الصخر»." },
      o: { en: "Mine Dawnsteel or Abyssium ore", ar: "استخرج خام فولاذ الفجر أو معدن الهاوية" } },
    { id: "armor", metric: "armor", need: 1, xp: 150, items: [],
      n: { en: "Raw metal is only a beginning. Forge it, wear it, and let the Abyss break its claws on you.",
        ar: "المعدن الخام ليس إلا بداية. اطرقه، والبسه، ودع الهاوية تكسر مخالبها عليك." },
      o: { en: "Wear a piece of forged armor", ar: "ارتدِ قطعة درعٍ مطروقة" } },
  ] },
  { t: { en: "Chapter III: Wounds in the World", ar: "الفصل الثالث: جراح العالم" }, steps: [
    { id: "rift", metric: "rifts", need: 1, delta: true, xp: 200, items: [["sh:skill_scroll", 1]],
      n: { en: "The sky splits with a sound like tearing cloth. A Rift has opened, and its creatures pour out in waves. Someone has to close it.",
        ar: "تنشقّ السماء بصوتٍ كتمزّق القماش. لقد انفتح صدع، وتتدفّق مخلوقاته موجةً بعد موجة. لا بدّ أن يغلقه أحد." },
      o: { en: "Seal a Rift", ar: "أغلق صدعًا" } },
    { id: "grim", metric: "grim", need: 1, delta: true, xp: 200, items: [["sh:xp_scroll_big", 1]],
      n: { en: "Sealing the Rift has drawn the attention of something older. The Grim hunters of dusk have caught your scent.",
        ar: "لفت إغلاقُ الصدع انتباهَ شيءٍ أقدم. لقد التقط صيّادو الغسق القاتمون رائحتك." },
      o: { en: "Defeat a Grim monster", ar: "اهزم وحشًا قاتمًا" } },
  ] },
  { t: { en: "Chapter IV: The Black Towers", ar: "الفصل الرابع: الأبراج السوداء" }, steps: [
    { id: "tower3", metric: "tower3", need: 1, xp: 250, items: [["sh:skill_scroll", 1]],
      n: { en: "On the horizon stands a tower of black stone and violet light. Seven floors, and each one stays sealed until it is cleared.",
        ar: "في الأفق يقف برجٌ من الحجر الأسود والضوء البنفسجي. سبعة طوابق، ويبقى كلٌّ منها مختومًا حتى يُطهَّر." },
      o: { en: "Clear the third floor of an Abyss Tower", ar: "طهّر الطابق الثالث من برج الهاوية" } },
    { id: "warrior", metric: "rank", need: 2, xp: 250, items: [["sh:skill_scroll", 1]],
      n: { en: "Your name has started to travel between villages. The Order of Dawn would have called you by a new rank.",
        ar: "بدأ اسمك ينتقل بين القرى. ولو بقيت جماعة الفجر لنادتك برتبةٍ جديدة." },
      o: { en: "Reach the rank of Warrior", ar: "ابلغ رتبة المحارب" } },
  ] },
  { t: { en: "Chapter V: The Two Blades", ar: "الفصل الخامس: النصلان" }, steps: [
    { id: "shrine", metric: "shrine", need: 1, xp: 500, items: [["sh:skill_scroll", 2]],
      n: { en: "An old map in a palace chest marks two shrines, one dark and one bright, each guarded by two beasts that never sleep. Break one seal.",
        ar: "خريطةٌ قديمة في صندوقٍ من القصر تُعلّم ضريحين، أحدهما مظلم والآخر مضيء، يحرس كلًّا منهما وحشان لا ينامان. اكسر أحد الختمين." },
      o: { en: "Cleanse a Sword Shrine", ar: "طهّر ضريح سيف" } },
    { id: "vile", metric: "vile", need: 1, delta: true, xp: 400, items: [["sh:xp_scroll_big", 2]],
      n: { en: "The shrine's guardians were only the beginning. Out in the wilds, the Vile beasts the Abyss tainted grow restless.",
        ar: "لم يكن حرّاس الضريح إلا البداية. ففي البراري، تزداد الوحوش الخبيثة التي دنّستها الهاوية اضطرابًا." },
      o: { en: "Defeat a Vile monster", ar: "اهزم وحشًا خبيثًا" } },
  ] },
  { t: { en: "Chapter VI: The Summit of Shadows", ar: "الفصل السادس: قمّة الظلال" }, steps: [
    { id: "tower7", metric: "tower7", need: 1, xp: 700, items: [["sh:xp_scroll_big", 3]],
      n: { en: "At the top of the tower, the Abyss keeps its strongest. Climb all seven floors.",
        ar: "في قمة البرج تحتفظ الهاوية بأقواها. اصعد الطوابق السبعة كلها." },
      o: { en: "Conquer the summit of an Abyss Tower", ar: "اقهر قمّة برج الهاوية" } },
    { id: "abyssal", metric: "rift_abyss", need: 1, delta: true, xp: 1000, items: [["sh:skill_scroll", 4]],
      n: { en: "Black-gold light bleeds from the deepest wound of all: an Abyssal Rift, the Abyss reaching for the heart of the star.",
        ar: "ينزف نورٌ أسود مذهّب من أعمق الجراح كلها: صدعٌ هاوي، الهاوية تمدّ يدها إلى قلب النجمة." },
      o: { en: "Seal an Abyssal Rift (grade 4)", ar: "أغلق صدعًا هاويًا (الدرجة 4)" } },
  ] },
];
export const STORY_END = {
  t: { en: "Epilogue: The Star Remembers", ar: "الخاتمة: النجمة تتذكّر" },
  n: { en: "The Abyss pulls back from the wound you closed, and for a moment Etheria is quiet. In the Star Temple, the crystal pulses once, as if it remembered your name. Your story continues in Etheria V1.5.",
    ar: "تتراجع الهاوية عن الجرح الذي أغلقته، وتهدأ إثيريا للحظة. وفي معبد النجمة، تنبض البلورة مرةً واحدة، كأنها تذكّرت اسمك. وتُستكمَل حكايتك في إثيريا V1.5." },
};
// كل الخطوات بترتيبها (مسطّحة) ومعها رقم الفصل
export const STORY_STEPS = STORY.flatMap((c, ci) => c.steps.map((s) => ({ ...s, ch: ci })));
