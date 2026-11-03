// يتولد تلقائياً من tools/gen_gear.py — لا تعدله يدوياً
export const GEAR = {
 "materials": {
  "sh:bear_hide": {
   "name": "§7Grey Bear Hide",
   "mob": "Grey Bear"
  },
  "sh:bear_claw": {
   "name": "§fGrey Bear Claw",
   "mob": "Grey Bear"
  },
  "sh:raw_dawnsteel": {
   "name": "§6Raw Dawnsteel",
   "mob": "Dawnsteel Ore"
  },
  "sh:dawnsteel_ingot": {
   "name": "§6Dawnsteel Ingot",
   "mob": "Smelted Raw Dawnsteel"
  },
  "sh:raw_abyssium": {
   "name": "§5Raw Abyssium",
   "mob": "Abyssium Ore"
  },
  "sh:abyssium_ingot": {
   "name": "§5Abyssium Ingot",
   "mob": "Smelted Raw Abyssium"
  }
 },
 "flames": {
  "sh:soul_crimson": {
   "name": "§cCrimson Soul Flame",
   "potion": "sh:potion_vitality"
  },
  "sh:soul_azure": {
   "name": "§9Azure Soul Flame",
   "potion": "sh:potion_mana"
  },
  "sh:soul_amber": {
   "name": "§6Amber Soul Flame",
   "potion": "sh:potion_might"
  },
  "sh:soul_silver": {
   "name": "§7Silver Soul Flame",
   "potion": "sh:potion_bulwark"
  },
  "sh:soul_violet": {
   "name": "§dViolet Soul Flame",
   "potion": "sh:potion_focus"
  },
  "sh:soul_verdant": {
   "name": "§aVerdant Soul Flame",
   "potion": "sh:potion_swift"
  }
 },
 "potions": {
  "sh:potion_vitality": {
   "name": "§cPotion of Vitality",
   "desc": "Heals half your health at once and regenerates for 5 s."
  },
  "sh:potion_mana": {
   "name": "§9Mana Elixir",
   "desc": "Refills your mana completely."
  },
  "sh:potion_might": {
   "name": "§6Potion of Might",
   "desc": "8 minutes: your skills and weapons hit 25% harder."
  },
  "sh:potion_bulwark": {
   "name": "§7Potion of Bulwark",
   "desc": "8 minutes: Resistance I (20% less damage)."
  },
  "sh:potion_focus": {
   "name": "§dPotion of Focus",
   "desc": "6 minutes: skill cooldowns 30% shorter and mana regenerates twice as fast."
  },
  "sh:potion_swift": {
   "name": "§aPotion of Swiftness",
   "desc": "6 minutes: Speed II and Jump Boost I."
  }
 },
 "sets": {
  "grizzly": {
   "name": "§7Grizzly",
   "pieces": [
    "sh:grizzly_helmet",
    "sh:grizzly_chestplate",
    "sh:grizzly_leggings",
    "sh:grizzly_boots"
   ],
   "mats": [
    "sh:bear_hide",
    "sh:bear_claw"
   ],
   "bonus": "Full set: Resistance I, and 4 golden hearts (Absorption) every 30 s."
  },
  "dawnsteel": {
   "name": "§6Dawnsteel",
   "pieces": [
    "sh:dawnsteel_helmet",
    "sh:dawnsteel_chestplate",
    "sh:dawnsteel_leggings",
    "sh:dawnsteel_boots"
   ],
   "mats": [
    "sh:dawnsteel_ingot"
   ],
   "bonus": "Full set: Haste I and Speed I."
  },
  "abyssium": {
   "name": "§5Abyssium",
   "pieces": [
    "sh:abyssium_helmet",
    "sh:abyssium_chestplate",
    "sh:abyssium_leggings",
    "sh:abyssium_boots"
   ],
   "mats": [
    "sh:abyssium_ingot"
   ],
   "bonus": "Full set: Strength I, Night Vision, and 20% of melee hits are countered back at the attacker."
  }
 }
};
