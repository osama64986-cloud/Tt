// يتولد تلقائياً من tools/gen_gear.py — لا تعدله يدوياً
export const GEAR = {
 "materials": {
  "sh:shadow_pelt": {
   "name": "§5Shadow Pelt",
   "mob": "Shadow Hound"
  },
  "sh:ember_horn": {
   "name": "§6Ember Horn",
   "mob": "Ember Imp"
  },
  "sh:sand_carapace": {
   "name": "§eSand Carapace",
   "mob": "Sand Scorpion"
  },
  "sh:rust_core": {
   "name": "§3Rust Core",
   "mob": "Rust Guard"
  },
  "sh:gloom_antler": {
   "name": "§bGloom Antler",
   "mob": "Gloomhorn"
  },
  "sh:hollow_lens": {
   "name": "§6Hollow Lens",
   "mob": "Hollow Seer"
  },
  "sh:spirit_fur": {
   "name": "§dSpirit Fur",
   "mob": "Veilfox"
  },
  "sh:magma_scale": {
   "name": "§cMagma Scale",
   "mob": "Magmamoth"
  },
  "sh:bear_hide": {
   "name": "§7Grey Bear Hide",
   "mob": "Grey Bear"
  },
  "sh:bear_claw": {
   "name": "§fGrey Bear Claw",
   "mob": "Grey Bear"
  },
  "sh:mantis_chitin": {
   "name": "§aMantis Chitin",
   "mob": "Prayer Mantis"
  },
  "sh:mantis_scythe": {
   "name": "§aMantis Scythe",
   "mob": "Prayer Mantis"
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
  "hunter": {
   "name": "§5Shadow Hunter",
   "pieces": [
    "sh:hunter_helmet",
    "sh:hunter_chestplate",
    "sh:hunter_leggings",
    "sh:hunter_boots"
   ],
   "mats": [
    "sh:shadow_pelt",
    "sh:sand_carapace"
   ],
   "bonus": "Full set: Speed I and Jump Boost I."
  },
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
  "mantis": {
   "name": "§aMantis",
   "pieces": [
    "sh:mantis_helmet",
    "sh:mantis_chestplate",
    "sh:mantis_leggings",
    "sh:mantis_boots"
   ],
   "mats": [
    "sh:mantis_chitin",
    "sh:mantis_scythe"
   ],
   "bonus": "Full set: Speed I, Strength I, and 20% of melee hits are countered back at the attacker."
  }
 }
};
