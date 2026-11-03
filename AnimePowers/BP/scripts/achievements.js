// يتولد تلقائياً من tools/gen_achievements.py — لا تعدله يدوياً
export const ACH_CATS = [
 {
  "key": "journey",
  "name": "Journey",
  "icon": "textures/ui/sh_ach/cat_journey"
 },
 {
  "key": "ranks",
  "name": "Ranks",
  "icon": "textures/ui/sh_ach/cat_ranks"
 },
 {
  "key": "places",
  "name": "Places",
  "icon": "textures/ui/sh_ach/cat_places"
 },
 {
  "key": "conquest",
  "name": "Conquest",
  "icon": "textures/ui/sh_ach/cat_conquest"
 },
 {
  "key": "monsters",
  "name": "Monsters",
  "icon": "textures/ui/sh_ach/cat_monsters"
 },
 {
  "key": "gear",
  "name": "Gear & Alchemy",
  "icon": "textures/ui/sh_ach/cat_gear"
 },
 {
  "key": "mastery",
  "name": "Mastery",
  "icon": "textures/ui/sh_ach/cat_mastery"
 }
];
export const ACH = [
 {
  "id": "star_touched",
  "cat": "journey",
  "name": "Star-Touched",
  "desc": "Draw your power at the Star Temple.",
  "hint": "A fallen star waits on a golden plate.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/star_touched",
  "iconLocked": "textures/ui/sh_ach/star_touched_x"
 },
 {
  "id": "unbound",
  "cat": "journey",
  "name": "The Dark Star",
  "desc": "The crystal stayed dark for you: one in two hundred.",
  "hint": "Some are chosen by no star at all...",
  "xp": 250,
  "secret": true,
  "icon": "textures/ui/sh_ach/unbound",
  "iconLocked": "textures/ui/sh_ach/unbound_x"
 },
 {
  "id": "first_lesson",
  "cat": "journey",
  "name": "First Lesson",
  "desc": "Finish the Trainer's training.",
  "hint": "The old Trainer in the village has a test.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/first_lesson",
  "iconLocked": "textures/ui/sh_ach/first_lesson_x"
 },
 {
  "id": "awakened",
  "cat": "journey",
  "name": "Awakened",
  "desc": "Raise your power to level 3.",
  "hint": "Your power can grow stronger.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/awakened",
  "iconLocked": "textures/ui/sh_ach/awakened_x"
 },
 {
  "id": "peak_power",
  "cat": "journey",
  "name": "Peak of Power",
  "desc": "Reach the highest level of your power.",
  "hint": "Every power has a peak.",
  "xp": 250,
  "secret": false,
  "icon": "textures/ui/sh_ach/peak_power",
  "iconLocked": "textures/ui/sh_ach/peak_power_x"
 },
 {
  "id": "honed",
  "cat": "journey",
  "name": "Honed Edge",
  "desc": "Raise one skill to its maximum level.",
  "hint": "Practice one skill until it can grow no more.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/honed",
  "iconLocked": "textures/ui/sh_ach/honed_x"
 },
 {
  "id": "scroll_reader",
  "cat": "journey",
  "name": "Scroll Reader",
  "desc": "Use a Skill Upgrade Scroll.",
  "hint": "Some scrolls teach in an instant.",
  "xp": 40,
  "secret": false,
  "icon": "textures/ui/sh_ach/scroll_reader",
  "iconLocked": "textures/ui/sh_ach/scroll_reader_x"
 },
 {
  "id": "lorekeeper",
  "cat": "journey",
  "name": "Lorekeeper",
  "desc": "Read three chapters of the World Story.",
  "hint": "The Evolution Book remembers the old days.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/lorekeeper",
  "iconLocked": "textures/ui/sh_ach/lorekeeper_x"
 },
 {
  "id": "rank_trainee",
  "cat": "ranks",
  "name": "Trainee",
  "desc": "Reach the rank of Trainee.",
  "hint": "Gain your first rank.",
  "xp": 40,
  "secret": false,
  "icon": "textures/ui/sh_ach/rank_trainee",
  "iconLocked": "textures/ui/sh_ach/rank_trainee_x"
 },
 {
  "id": "rank_warrior",
  "cat": "ranks",
  "name": "Warrior",
  "desc": "Reach the rank of Warrior.",
  "hint": "A higher rank awaits.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/rank_warrior",
  "iconLocked": "textures/ui/sh_ach/rank_warrior_x"
 },
 {
  "id": "rank_elite",
  "cat": "ranks",
  "name": "Elite",
  "desc": "Reach the rank of Elite.",
  "hint": "A higher rank awaits.",
  "xp": 120,
  "secret": false,
  "icon": "textures/ui/sh_ach/rank_elite",
  "iconLocked": "textures/ui/sh_ach/rank_elite_x"
 },
 {
  "id": "rank_commander",
  "cat": "ranks",
  "name": "Commander",
  "desc": "Reach the rank of Commander.",
  "hint": "A higher rank awaits.",
  "xp": 180,
  "secret": false,
  "icon": "textures/ui/sh_ach/rank_commander",
  "iconLocked": "textures/ui/sh_ach/rank_commander_x"
 },
 {
  "id": "rank_legend",
  "cat": "ranks",
  "name": "Legend",
  "desc": "Reach the rank of Legend.",
  "hint": "Only a few become legends.",
  "xp": 260,
  "secret": false,
  "icon": "textures/ui/sh_ach/rank_legend",
  "iconLocked": "textures/ui/sh_ach/rank_legend_x"
 },
 {
  "id": "rank_master",
  "cat": "ranks",
  "name": "Master",
  "desc": "Reach the rank of Master.",
  "hint": "The last rank of all.",
  "xp": 400,
  "secret": false,
  "icon": "textures/ui/sh_ach/rank_master",
  "iconLocked": "textures/ui/sh_ach/rank_master_x"
 },
 {
  "id": "visit_village",
  "cat": "places",
  "name": "Cherry Blossom Road",
  "desc": "Visit a Sakura Village.",
  "hint": "Pink trees and paper lanterns, somewhere out there.",
  "xp": 40,
  "secret": false,
  "icon": "textures/ui/sh_ach/visit_village",
  "iconLocked": "textures/ui/sh_ach/visit_village_x"
 },
 {
  "id": "visit_palace",
  "cat": "places",
  "name": "Sunset Throne",
  "desc": "Find the Sunset Palace.",
  "hint": "The last light fell on a palace.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/visit_palace",
  "iconLocked": "textures/ui/sh_ach/visit_palace_x"
 },
 {
  "id": "visit_ruins",
  "cat": "places",
  "name": "Ruined Prayers",
  "desc": "Explore the Temple Ruins.",
  "hint": "Broken pillars remember the first shard.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/visit_ruins",
  "iconLocked": "textures/ui/sh_ach/visit_ruins_x"
 },
 {
  "id": "visit_tower",
  "cat": "places",
  "name": "Into the Abyss",
  "desc": "Enter an Abyss Tower.",
  "hint": "A black and violet tower, seven floors high.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/visit_tower",
  "iconLocked": "textures/ui/sh_ach/visit_tower_x"
 },
 {
  "id": "visit_shrine",
  "cat": "places",
  "name": "Where Darkness Sleeps",
  "desc": "Find the Dark Sword Shrine.",
  "hint": "A shrine the Abyss sleeps beneath.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/visit_shrine",
  "iconLocked": "textures/ui/sh_ach/visit_shrine_x"
 },
 {
  "id": "visit_lightshrine",
  "cat": "places",
  "name": "Where Light Endures",
  "desc": "Find the Light Sword Shrine.",
  "hint": "A shrine of light the Abyss never swallowed.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/visit_lightshrine",
  "iconLocked": "textures/ui/sh_ach/visit_lightshrine_x"
 },
 {
  "id": "meet_alchemist",
  "cat": "places",
  "name": "The Old Brewer",
  "desc": "Meet the Alchemist in a Sakura Village.",
  "hint": "An old man in a tall hat brews strange things.",
  "xp": 40,
  "secret": false,
  "icon": "textures/ui/sh_ach/meet_alchemist",
  "iconLocked": "textures/ui/sh_ach/meet_alchemist_x"
 },
 {
  "id": "shrine_dark_clear",
  "cat": "conquest",
  "name": "Shrine of Darkness Cleansed",
  "desc": "Defeat both guardians of the Dark Sword Shrine.",
  "hint": "Two guardians watch over a dark blade.",
  "xp": 300,
  "secret": false,
  "icon": "textures/ui/sh_ach/shrine_dark_clear",
  "iconLocked": "textures/ui/sh_ach/shrine_dark_clear_x"
 },
 {
  "id": "shrine_light_clear",
  "cat": "conquest",
  "name": "Shrine of Light Cleansed",
  "desc": "Defeat both guardians of the Light Sword Shrine.",
  "hint": "Two guardians watch over a blade of light.",
  "xp": 300,
  "secret": false,
  "icon": "textures/ui/sh_ach/shrine_light_clear",
  "iconLocked": "textures/ui/sh_ach/shrine_light_clear_x"
 },
 {
  "id": "tower_half",
  "cat": "conquest",
  "name": "Halfway Up",
  "desc": "Clear the fourth floor of an Abyss Tower.",
  "hint": "Climb, floor by floor.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/tower_half",
  "iconLocked": "textures/ui/sh_ach/tower_half_x"
 },
 {
  "id": "tower_top",
  "cat": "conquest",
  "name": "Master of the Tower",
  "desc": "Conquer the seventh floor of an Abyss Tower.",
  "hint": "Something strong waits at the very top.",
  "xp": 400,
  "secret": false,
  "icon": "textures/ui/sh_ach/tower_top",
  "iconLocked": "textures/ui/sh_ach/tower_top_x"
 },
 {
  "id": "rift_first",
  "cat": "conquest",
  "name": "Rift Closer",
  "desc": "Seal your first rift.",
  "hint": "Tears in the world can be closed.",
  "xp": 100,
  "secret": false,
  "icon": "textures/ui/sh_ach/rift_first",
  "iconLocked": "textures/ui/sh_ach/rift_first_x"
 },
 {
  "id": "rift_five",
  "cat": "conquest",
  "name": "Rift Hunter",
  "desc": "Seal five rifts.",
  "hint": "Keep closing them.",
  "xp": 250,
  "secret": false,
  "icon": "textures/ui/sh_ach/rift_five",
  "iconLocked": "textures/ui/sh_ach/rift_five_x"
 },
 {
  "id": "rift_crimson",
  "cat": "conquest",
  "name": "Crimson Tide",
  "desc": "Seal a Crimson Rift.",
  "hint": "Some rifts bleed red.",
  "xp": 250,
  "secret": false,
  "icon": "textures/ui/sh_ach/rift_crimson",
  "iconLocked": "textures/ui/sh_ach/rift_crimson_x"
 },
 {
  "id": "rift_abyss",
  "cat": "conquest",
  "name": "Abyss Gazer",
  "desc": "Seal an Abyssal Rift.",
  "hint": "The rarest rift burns gold.",
  "xp": 500,
  "secret": false,
  "icon": "textures/ui/sh_ach/rift_abyss",
  "iconLocked": "textures/ui/sh_ach/rift_abyss_x"
 },
 {
  "id": "first_blood",
  "cat": "monsters",
  "name": "First Blood",
  "desc": "Defeat your first monster.",
  "hint": "The wilds are not safe.",
  "xp": 30,
  "secret": false,
  "icon": "textures/ui/sh_ach/first_blood",
  "iconLocked": "textures/ui/sh_ach/first_blood_x"
 },
 {
  "id": "hunter_100",
  "cat": "monsters",
  "name": "Hundred Hunts",
  "desc": "Defeat 100 monsters.",
  "hint": "Keep hunting.",
  "xp": 250,
  "secret": false,
  "icon": "textures/ui/sh_ach/hunter_100",
  "iconLocked": "textures/ui/sh_ach/hunter_100_x"
 },
 {
  "id": "scholar",
  "cat": "monsters",
  "name": "Monster Scholar",
  "desc": "Fill eight pages of the Monster Book.",
  "hint": "Every new kind of monster adds a page.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/scholar",
  "iconLocked": "textures/ui/sh_ach/scholar_x"
 },
 {
  "id": "slay_gloom",
  "cat": "monsters",
  "name": "Antler Breaker",
  "desc": "Defeat a Gloomhorn.",
  "hint": "A stag with a beating heart of shadow.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/slay_gloom",
  "iconLocked": "textures/ui/sh_ach/slay_gloom_x"
 },
 {
  "id": "slay_seer",
  "cat": "monsters",
  "name": "Blind the Seer",
  "desc": "Defeat a Hollow Seer.",
  "hint": "It watches with an orange eye.",
  "xp": 80,
  "secret": false,
  "icon": "textures/ui/sh_ach/slay_seer",
  "iconLocked": "textures/ui/sh_ach/slay_seer_x"
 },
 {
  "id": "slay_fox",
  "cat": "monsters",
  "name": "Foxfire Out",
  "desc": "Defeat a Veilfox.",
  "hint": "Five tails, each one burning.",
  "xp": 120,
  "secret": false,
  "icon": "textures/ui/sh_ach/slay_fox",
  "iconLocked": "textures/ui/sh_ach/slay_fox_x"
 },
 {
  "id": "slay_bear",
  "cat": "monsters",
  "name": "Bear Hug Survivor",
  "desc": "Defeat a Grey Bear.",
  "hint": "Do not let it hug you.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/slay_bear",
  "iconLocked": "textures/ui/sh_ach/slay_bear_x"
 },
 {
  "id": "slay_mammoth",
  "cat": "monsters",
  "name": "Volcano Walker",
  "desc": "Defeat a Magmamoth.",
  "hint": "A mountain of fur and lava.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/slay_mammoth",
  "iconLocked": "textures/ui/sh_ach/slay_mammoth_x"
 },
 {
  "id": "slay_mantis",
  "cat": "monsters",
  "name": "Molt and Fall",
  "desc": "Defeat a Prayer Mantis.",
  "hint": "It prays before it strikes.",
  "xp": 200,
  "secret": false,
  "icon": "textures/ui/sh_ach/slay_mantis",
  "iconLocked": "textures/ui/sh_ach/slay_mantis_x"
 },
 {
  "id": "first_material",
  "cat": "gear",
  "name": "Hide and Seek",
  "desc": "Collect a monster material.",
  "hint": "Monsters leave more than bones behind.",
  "xp": 30,
  "secret": false,
  "icon": "textures/ui/sh_ach/first_material",
  "iconLocked": "textures/ui/sh_ach/first_material_x"
 },
 {
  "id": "tailored",
  "cat": "gear",
  "name": "Tailored Hide",
  "desc": "Wear a piece of monster armor.",
  "hint": "Hides and claws make good armor.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/tailored",
  "iconLocked": "textures/ui/sh_ach/tailored_x"
 },
 {
  "id": "full_set",
  "cat": "gear",
  "name": "Full Set",
  "desc": "Wear a complete monster armor set.",
  "hint": "Four pieces from the same beast.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/full_set",
  "iconLocked": "textures/ui/sh_ach/full_set_x"
 },
 {
  "id": "first_brew",
  "cat": "gear",
  "name": "First Brew",
  "desc": "Brew a potion with the Alchemist.",
  "hint": "The old brewer needs ingredients.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/first_brew",
  "iconLocked": "textures/ui/sh_ach/first_brew_x"
 },
 {
  "id": "potion_six",
  "cat": "gear",
  "name": "Six Flavors",
  "desc": "Drink all six potions.",
  "hint": "Six rare potions exist.",
  "xp": 200,
  "secret": false,
  "icon": "textures/ui/sh_ach/potion_six",
  "iconLocked": "textures/ui/sh_ach/potion_six_x"
 },
 {
  "id": "mana_dry",
  "cat": "gear",
  "name": "Running on Empty",
  "desc": "Try a skill without enough mana.",
  "hint": "Even powers run dry.",
  "xp": 20,
  "secret": false,
  "icon": "textures/ui/sh_ach/mana_dry",
  "iconLocked": "textures/ui/sh_ach/mana_dry_x"
 },
 {
  "id": "armed",
  "cat": "mastery",
  "name": "Legend in Hand",
  "desc": "Hold a legendary weapon.",
  "hint": "Old weapons lie in chests and shrines.",
  "xp": 40,
  "secret": false,
  "icon": "textures/ui/sh_ach/armed",
  "iconLocked": "textures/ui/sh_ach/armed_x"
 },
 {
  "id": "weapon_max",
  "cat": "mastery",
  "name": "Weapon Master",
  "desc": "Raise a weapon to its highest level.",
  "hint": "A weapon grows with the one who wields it.",
  "xp": 250,
  "secret": false,
  "icon": "textures/ui/sh_ach/weapon_max",
  "iconLocked": "textures/ui/sh_ach/weapon_max_x"
 },
 {
  "id": "rhythm_finale",
  "cat": "mastery",
  "name": "Drummer's Finale",
  "desc": "Land a Finale with Rhythm Strike.",
  "hint": "Hit in a steady beat, like a drum.",
  "xp": 150,
  "secret": false,
  "icon": "textures/ui/sh_ach/rhythm_finale",
  "iconLocked": "textures/ui/sh_ach/rhythm_finale_x"
 },
 {
  "id": "dash_50",
  "cat": "mastery",
  "name": "Blink",
  "desc": "Dash fifty times.",
  "hint": "Tap a direction twice.",
  "xp": 60,
  "secret": false,
  "icon": "textures/ui/sh_ach/dash_50",
  "iconLocked": "textures/ui/sh_ach/dash_50_x"
 },
 {
  "id": "pathfinder",
  "cat": "mastery",
  "name": "Pathfinder",
  "desc": "Use the Explorer Compass.",
  "hint": "A compass that knows where the old places are.",
  "xp": 30,
  "secret": false,
  "icon": "textures/ui/sh_ach/pathfinder",
  "iconLocked": "textures/ui/sh_ach/pathfinder_x"
 }
];
