# The Java mods behind our idea — research notes (saved so we never lose them)

Our add-on's idea is anime characters fighting each other in red and blue teams while you watch. On Java this is
done with three mods together, and their videos are some of the most watched Minecraft anime content:

1. **Jujutsu Craft (Sorcery Fight)** by Orca (Forge). It has more than 60 cursed techniques from the series' characters,
   plus Domain Expansion, Reverse Cursed Technique healing, Black Flash with a "zone" (one Black Flash makes the next
   more likely), Simple Domain, Mahoraga's adapting wheel and terrain-destroying techniques.
2. **Mob Battle Mod** by flemmli97 (Forge/Fabric/NeoForge). Put mobs into colour teams and the teams attack only each
   other. You can watch big team battles without commands.
3. **Jujutsu Craft Mob Battle Addon** by Stormbit298 (~1.5M downloads). It adds tools for "making mob battles
   cooler/more fun": cooldown removal, a despawner, Dismantle turning into Piercing Blood by HP, domain toggles, an
   automatic Mahoraga wheel, Sukuna/Gojo boss work.

Other anime mods checked: Anime Assembly (21-22 characters, GeckoLib), AnimeBosses (phase battles, "cinematic
ultimates"), The Anime Universe, Dragon Block C (ki, beams, transformations), Anime Limitless.

## Why people love those fights
- **The world reacts.** Hits gouge the ground, techniques cut terrain, fighters crash into walls.
- **Domains are a real place.** A barrier closes around the fighters and the fight continues inside it. Two domains
  clash, and Malevolent Shrine is an open domain with the shrine standing behind Sukuna.
- **Signature mechanics** from the series (Black Flash streaks, RCT, Mahoraga adapting).
- **Cinematic moments**: ultimates and transformations feel like a scene from the anime.
- **Sound**: heavy impacts and distinct technique sounds.
- **Team battles**: lots of characters fighting at once.

## Can we do the same on Bedrock? What we did (v1.15.0)
| Java (Jujutsu Craft + Mob Battle) | Anime Battles (Bedrock) |
|---|---|
| Terrain destruction | Trenches under every launch, craters where fighters land, walls cave in, KO crater; rocks and dirt chunks fly and bounce (`ab:rubble`) |
| (keeping your world safe) | Every broken block is remembered; the arena rebuilds itself 30 s after the fighting stops or right after a team wins (`/scriptevent ab:regen off` keeps the damage) |
| Domain barrier | Gojo (black dome with sea-lantern stars inside) and Yuji (white dome): a real block dome rises from the ground and seals, enemies at the edge are pulled in; it shatters when the domain ends, loses a clash or its owner falls. Only air is ever replaced |
| Malevolent Shrine (open domain) | The shrine rises behind Sukuna: blackstone platform heaped with bones, red pillars, a fanged mouth of flesh, three-tier roof with upturned eaves |
| Black Flash "zone" | After a Black Flash, the next ones are 2.2× more likely for 10 s, with black and red sparks crackling around the fighter; dark-red screen flash |
| Cinematic ultimates | The watching players' camera sweeps round the fighter on Domain Expansion, a final transformation, the battle face-off and the victory (`/scriptevent ab:cinema off`) |
| Sound effects | Five original synthesised sounds: heavy punch, vanish whoosh, ground-shaking boom, domain gong, Black Flash crack (`tools/sounds.py`) |
| Mob Battle team war | `/scriptevent ab:war 4`: 4 against 4 random fighters, dealt into fair teams |
| Already in the add-on before | Domain clash, RCT, Black Flash, Mahoraga adaptation, beam struggle, fist clash, guard break, counters, vanish chase, impact frames |

Not possible on Bedrock: custom dimensions, real block-entity debris (we use particles), and changing the camera
FOV or applying a motion blur.
