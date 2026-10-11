# Happily Ever After V2: characters share the spotlight (plan)

**Status (2026-10-11):** plan only. Nothing drawn, nothing built. Every character still goes through
the usual question batch before it's drawn (CHARACTERS.md, "ask before drawing").

V1 is all castle and fireworks. The real show is mostly projected characters (see README.md here,
scene by scene). In V2 the castle fades out, or dims to a ghost, in the scenes where characters need
the room, and comes back for the moments that belong to it. V2 is switchable against V1 and leaves
V1's scenes, effects and castle exactly as they are.

## Why the castle has to move

| Board | Castle | Free space with the castle up |
|---|---|---|
| 64x32 | 23x20, cols 20-42, rows 12-31 | a 64x12 strip of sky, plus 20 columns either side |
| 64x64 | 46x40 (doubled), cols 9-54, rows 24-63 | a 64x24 strip of sky, plus **9** columns either side |

On 64x64 the castle covers almost the full width, so a character of any size has to go in front
of it or in the sky strip. The sprites we have run about 16x22 to 25x35. With the castle off, the
whole board is free.

## Stage modes (a new per-scene cue, `stage`)

- `castle`: V1 as it is now. The default, so a scene with no `stage` doesn't change.
- `ghost`: the castle dims to about 25% over `CASTLE_FADE_S` (keeping its look's colours) and
  characters draw in front of it. The show stays recognisable. This is my default for character
  scenes.
- `off`: the castle fades to black and the board is the characters'. Fireworks still go up from
  the ground. Use it for scenes the real show takes off the castle (underwater, starry sky, the
  mash-up).
- `aside` (optional, costs more): on 64x64, the castle slides to a corner and shrinks to the
  64x32 castle (`castle_sprite(32)` already exists). Every castle-anchored effect (keyhole,
  bells, flame jets, fountains, Te Fiti, the spire for the wishing star and Tink) reads
  `castle_x`/`spire` from `__init__`, so all of them would need to follow a moving castle. Leave it
  out unless `ghost` and `off` aren't enough.

## Every character, scene by scene

Art: **Have** is drawn in the repo (reuse its art and colours). **Sheet** means a reference we
already have (princes sheet `princesses_and_Princes.jpg`, about 16x22 each, fits both boards;
villains sheet `Princesses_and_Evil_Ladies.jpg`, about 25x35, 64x64 only), pulled out in the
sprite editor's Pattern mode. **Lead** is a game sprite rip from ROADMAP's list, not downloaded
yet. **Code** is a simple shape drawn in code. **None** means no art and not simple.

| Scene (audio s) | Stage | Character | Art | What they could do |
|---|---|---|---|---|
| Opening, chorus (0-137) | castle | none | | The castle and the first pyro carry it. Unchanged. |
| Wishing star (137-150) | castle | none | | Unchanged. |
| Down in New Orleans (150-171) | ghost | Tiana | Sheet | Stands at the left under the evening star, looking up. |
| | | Ray | Code | A 1-2 px firefly blinking yellow-green in a figure-eight near the evening star. |
| When You Wish fanfare (171-192) | castle | Ray | Code | Keeps buzzing, circling the spire. |
| Part of Your World (192-215) | off | Ariel | Sheet | Swims across on a slow sine wave through the bubbles, tail flicking (two frames). |
| PoYW climax (215-256) | ghost | Ariel | Sheet | Rises from the bottom toward the top and reaches up (needs a "reach" frame). |
| Out There (268-303) | castle | Quasimodo | None | Swings on a rope from the spire between the towers (a pendulum). Small, about 10x14. |
| Touch the Sky / Up (303-325) | ghost | Up house | Code | Rises from behind the castle under a balloon cluster and drifts up and out to the right. |
| | | Merida | Sheet (`Brave2.jpg` 21x30) | Optional, for Touch the Sky's opening seconds: draws her bow at the side. |
| | | Dug (cameo) | Have (`kevin`) | Optional: runs along the ground after the house. |
| How Far I'll Go (325-370) | ghost | Moana | Sheet | Sails a small canoe (Code) across the water effect. |
| | | Gramma Tala | | The existing `stingray` effect stands in. |
| HFIG climax (370-398) | off | Moana, Maui | Sheet | Moana at the bow, Maui waving his hook. |
| Aladdin's line (398-412) | ghost | Aladdin | Sheet / `aladin.jpg` | Stands at centre holding the lamp, with the lamp smoke coming from the lamp instead of the spire. |
| Friend Like Me intro (412-428) | off | Aladdin, Genie | Have (`genie`) | Genie bursts out of Aladdin's lamp, the way his ride reveal already does. |
| Trashin' the Camp (428-446) | castle | Terk | Lead | Swings across on a vine (same pendulum as Quasimodo). |
| Hakuna Matata (446-453, 7 s) | castle | Timon, Pumbaa | Lead | March along the castle's base, left to right. |
| You've Got a Friend in Me (453-459, 6 s) | castle | Woody, Buzz | Have (`aliens` 14x18) | Buzz shoots across the sky, Woody waves from the ground beside the blocks. |
| Mash-up: Wreck-It (459-473) | off | Ralph | Have | Smashes falling 8-bit bricks (two-fist pose `UP_ART`). |
| | | Vanellope | Sheet (`Vanellope Von - Car.jpg`) | Zips across in her kart, glitching. |
| Mash-up: Big Hero 6 (474-481) | off | Baymax | Have | Inflates up from the bottom and waves. (Hiro: None, left out.) |
| Mash-up: Zootopia (482-493) | off | Judy, Nick | Sheet (`nick and judy.jpg`, 15x33 and 18x40) | Stand side by side under a neon skyline (Code). Too tall for 64x32 as is: 64x64 only, or cut at the knees there. |
| Mash-up: Inside Out (494-513) | off | Joy, Sadness | Sheet (`inside_out.jpg`, about 17x25) | Joy and Sadness each roll a memory orb (Code: a glowing yellow and blue ball) in from their side. |
| That's What Friends Are For (514-527) | castle | Mike | Have | Pops up from behind a turret, blinks (his ride reveal). |
| | | Sulley | Sheet (`Monsters_Inc.jpg` 18x25; `Sulley.jpg` 26x33 on 64x64) | Steps out of a door beside the castle while Mike pops up. |
| Friend Like Me, Genie (527-554) | ghost | Genie | Have | Loops round the sky in the party searchlights, trailing smoke. |
| Genie finale (554-563) | castle | Genie | Have | Dives back into the lamp as the roof fountains go. |
| Olaf's line (563-576) | ghost | Olaf | Have | Stands at the base and waves while the snow rises. |
| Love Is an Open Door (576-603) | castle | Anna | Sheet (`Frozen.jpg` 19x33) | Optional. Hans has no art (a recoloured prince?). Fine with just the look. |
| Can You Feel the Love (603-613) | off | WALL-E, EVE | Have / Code | The space dance: EVE (a white egg with blue eyes) and WALL-E orbit each other among the stars. |
| CYFtLT (613-623) | off | Simba, Nala | Sheet (`simba_bricks.png`) | Simba on a rock under the moon. Nala could be a recoloured Simba. |
| You'll Be in My Heart (623-637) | ghost | Dumbo | Have (back half TODO) | Flies across holding the feather. Mrs. Jumbo, Tarzan, Kala: None. |
| Princess garden (637-668) | off | 4 couples | Sheet (princes sheet) | One couple every ~7.5 s: they walk in from either side, meet in the middle, and a heart floats up (`jack_sally`'s heart). Cinderella and Charming, Tiana and frog Naveen, Ariel and Eric, Belle and Beast. |
| I See the Light (668-724) | ghost | Rapunzel, Flynn | Sheet | In a small boat (Code) at the bottom while the lanterns rise around them. |
| Emperor (724-742) | castle | none | | The Emperor has no art. Keep the look. |
| Villains (742-760) | ghost | Ursula | Sheet (`Ursula.jpg` 37x38, `Villains.jpg` 33x42; 64x64) | Rises from the bottom, tentacles first. On 64x32, tentacles only (Code). |
| | | Scar | Sheet (`Scar.jpg` 24x27) | Glares in from the left; fits both boards. |
| | | Hades | Sheet (`Male villains.jpg` 31x42; 64x64) | His flame hair flares red as he rises. On 64x32, just the flame hair (Code). |
| To Die For (760-777) | ghost | Maleficent | Sheet / `Maleficent.jpg` 29x40 | Looms in from the right through the green fire. On 64x32, head and horns peek in. |
| | | Jafar | Sheet (`Male villains.jpg` 30x41; 64x64) | Optional. |
| He's a Pirate (777-849) | castle | Captain Hook | Sheet (`Male villains.jpg` 30x41; 64x64) | Stands in for Jack Sparrow (no art): swaggers past the burning castle. Or a pirate ship silhouette (Code). |
| Embers / Mufasa (849-889) | castle (dark) | Mufasa | Code | A big dim lion face (the `lion` burst shape, scaled up) fades in over the spire in the clouds, speaks, fades out. |
| Go the Distance, rebuild (889-915) | ghost | Hercules | Sheet | Rises in gold light at centre as the castle rebuilds. |
| Go the Distance (915-976) | castle (stained glass) | Hercules, Megara, Mulan, Merida | Sheet | Hero panels: on 64x32, framed 16x22 windows either side of the castle, one hero at a time. On 64x64 the sides are too narrow, so they go in the sky strip, or the stage goes ghost. |
| Narrator, reprise (992-1042) | castle | none | | The castle's moment. |
| You Can Fly (1042-1080) | castle | Tink | Have | V1's `tink` effect as it is now. |
| Finale (1080-1104) | castle | none | | The castle owns the finale. |

### By art status

Updated 2026-10-11 after the second batch of references (docs/references/README.md has every row):

- **Have (11):** Genie, Olaf, WALL-E, Baymax, Ralph, Mike, Woody, Buzz, Dumbo, Tink, Dug.
- **Sheet, fits both boards (about 16x22 to 24x30):** princes sheet: Tiana, frog Naveen, Ariel, Eric,
  Moana, Maui, Aladdin, Cinderella, Charming, Belle, Beast, Rapunzel, Flynn, Hercules, Megara, Mulan.
  Also Merida (`Brave2.jpg`), Rapunzel with her pan (`Rapunzel with pan.jpg`), Scar (`Scar.jpg`), Rafiki,
  Simba (`simba_bricks.png`), Joy and Sadness (`inside_out.jpg`), Sulley (`Monsters_Inc.jpg`), Olaf,
  Flounder, and the `Princesses with props.jpg` chibis (the princes sheet's size).
- **Sheet, 64x64 only (33-42 rows):** Ursula, Maleficent, Jafar, Hades, Captain Hook, Anna, Elsa,
  Belle and Beast (`belle and beast.jpg`), Judy and Nick, and the bigger `Detailed princesses.jpg`
  princesses. Each needs a 64x32 fallback: the princes-sheet version, a part (a head, tentacles,
  flame hair), or left out on that board.
- **Code (8):** Ray, EVE, Mufasa's face, the Up house, Moana's canoe, Rapunzel's boat, memory orbs,
  the neon skyline.
- **Not in the show's list, but on hand if wanted:** Nemo, Dory and Flounder could swim through Part
  of Your World with Ariel. Rafiki could lift his staff while Mufasa speaks. Gothel, Facilier, Cruella,
  the Evil Queen, Lady Tremaine, Gaston and Frollo could cycle through the villains scene. The rose
  could be Belle and Beast's moment in the princess garden.

### Still missing (references to look for)

Most useful first:
1. **A full-size Lion King pattern.** `Lion King.jpg` is a product photo of the right set (Pumbaa,
   Timon, Nala, Simba, Mufasa, Scar), but each figure is about 40 px tall, too small to count. The
   chart itself would give Hakuna Matata's Timon and Pumbaa, Nala for Can You Feel the Love Tonight,
   and a real Mufasa instead of the lion-shape stand-in.
2. **Quasimodo** for Out There, ideally small (about 10x14), swinging. Nothing yet.
3. **Bigger princes** (about 24x33) to stand with the `Detailed princesses.jpg` princesses on 64x64:
   Charming, Eric, Naveen, Flynn, Hercules. Without them, the princess garden uses the princes sheet's
   matched small pairs, which is fine.
4. **EVE** for WALL-E's space dance (else a white egg in code).
5. **Hiro** for Big Hero 6 (Baymax alone works).
6. **Terk** for Trashin' the Camp, and **Tarzan, Jane, Kala** for You'll Be in My Heart and Go the
   Distance.
7. **Mrs. Jumbo** (Dumbo flies alone otherwise; his own art still needs its back half).
8. **Jack Sparrow** (Captain Hook stands in), **Hans**, **Carl and Russell**, **Gramma Tala** (the
   stingray stands in), and **the Emperor**: all optional; their scenes hold without them.

## The code

1. **Version switch.** `config.json` `"show_version": "v1" | "v2"` (default `"v1"`), read by
   `utils/config.py`. `load_score(name, version)` applies `shows/<name>.v2.json` when it's v2 and
   exists. If that file is missing or broken, it logs and plays V1, the same rule as V1's file today.
   `disney.py:play_fireworks_show_if_due` passes the setting. Add it to `config.json-example` and
   CLAUDE.md's Configuration.
2. **V2 as an overlay, not a copy.** `happily-ever-after.v2.json` holds only per-scene additions,
   keyed by scene title: `{"overlays": {"Friend Like Me (Genie)": {"stage": "ghost", "actors":
   ["genie_loops"], "rate": 0.5}}}`. `score.py` merges it onto V1's scenes, so any re-timing of V1
   moves V2 with it. A title that doesn't match a V1 scene is an error, which falls back to V1, so
   renaming a scene can't silently drop a V2 scene (a test checks every overlay title). Tradeoff: a
   full copy would let V2 split scenes differently (the mash-up's four vignettes). Actors take their
   own start offsets within a scene, so the overlay doesn't need to split it.
3. **`Cue` gains `stage` and `actors`.** Defaults are `castle` and `()`, so every V1 cue is
   unchanged. Validation: a known stage, known actors, and no castle-anchored effect (`keyhole_*`,
   `bells`, `flame_jets`, `fountains`, `te_fiti`, `wishing_star`, `tink`) in an `off` scene.
4. **Castle level in `music_show.py`.** A `castle_level` that fades between stages over
   `CASTLE_FADE_S` alongside the colour fade, multiplying the castle's pixels. It skips them at 0 and
   then stops hiding launches behind the castle. At level 1 the code path is today's, and a test
   pins that a V1 score renders the same frames with a seeded rng before and after.
5. **`display/fireworks/show_actors.py`**, shaped like `show_effects.py`: one class per character
   in a scene, registered in `ACTORS` and named in a scene's `actors`.
   - Each actor places itself by **the clock** (`show.t - cue.start`), not by frames, as Tink does,
     so a slow board stays with the music. It draws in front of the castle and fireworks, under the
     final flash.
   - Shared motion verbs, so each actor is a few lines: `fly_across` (Tink's arc, generalised),
     `walk_on` (along the ground with a bob, like `slinky`/`forky`), `rise_up` (from the bottom
     edge, like `mike`/`baymax`), `appear` (fade in at a spot: Mufasa, Hercules), `swing` (a
     pendulum: Quasimodo, Terk), `pair_meet` (two walk in, meet, heart: the princess garden),
     `sail` (a boat on the water line). They build on `display/motion.py`, not new copies.
   - Sprites: import existing art and colours from `characters/` (`GenieReveal.ART`,
     `OlafReveal`, `WallESideReveal.ART`...), as `music_show` imports `TinkReveal`. New art from the
     sheets goes in `display/fireworks/show_sprites.py`. Each sprite declares its scale (1x on 64x32,
     1x or 2x on 64x64, following "keep crowded sprites 1x on 64x64") so `build_sprite_editor.py`
     picks it up. Rebuild the editor after each one.
   - Procedural ones (Baymax, Mike, Olaf's build) are drawn by functions, not ASCII. Either factor
     a "draw at (x, y, frame)" out of each reveal, or redraw a still pose for the show. I'd do a
     still pose: it doesn't touch the ride reveals.
6. **Preview from any second.** The show runs 18 minutes, and checking a scene at 637 s shouldn't
   take 10 minutes of waiting. Add a dev-only `--show-at <seconds> [--show-version v2]` (cli.py)
   that plays the synced show from that second with no sound. `render_music_show` gets a
   `start_at` offset on its clock. The live board needs this anyway, to start the music mid-file
   (see ROADMAP).
7. **Fireworks under characters.** The overlay's `rate` thins the sky while a character is on,
   like Tink's `TINK_RATE` but per scene, so a busy burst doesn't sit on a face.
8. **Tests**, in `tests/display/fireworks/`: `test_score.py` (overlay merge, unknown title, bad
   stage, castle effect in an off scene, missing v2 file falls back), `test_music_show.py` (castle
   fades to ghost/off and back, V1 frames unchanged), a new `test_show_actors.py` (each actor is on
   the board during its window and gone after, stays on the board on both sizes, positions follow
   the clock on a slow fake clock), and the config switch.
9. **Docs:** this file becomes V2's record, with a ROADMAP entry, CHARACTERS.md lessons per actor,
   and a README row per new sheet extraction.

Rough size: items 1-4 and 6-7 are one PR of plumbing (half a day, no art), with Genie as the proof
actor. After that, each actor is small. The time goes into the art questions and looking at it on
the boards.

## Batches

1. **Plumbing and the drawn ones:** switch, overlay, stage fade, preview-at, actors base and verbs,
   then Genie, Olaf, WALL-E, Baymax, Ralph, Mike, Woody and Buzz, Dumbo. No new art.
2. **Princes sheet:** the princess garden couples, Tiana, Ariel, Moana and Maui, Aladdin, Rapunzel
   and Flynn, Hercules, Megara and Mulan. One sheet, mostly two verbs.
3. **Code shapes:** Ray, EVE, Mufasa, the Up house, the boats, memory orbs, skyline.
4. **The rest of the references:** Merida, Simba, Scar, Vanellope, Sulley, Joy and Sadness, then
   the 64x64-only ones (Ursula, Maleficent, Hades, Jafar, Captain Hook, Anna, Judy and Nick), each
   with its 64x32 fallback (the small version, a part, or left out on that board).
5. **Still missing** (the list above) as references turn up: the Lion King set first.

## Decided (with the user, 2026-10-11)

- Stage: `ghost` and `off` as marked above. No `aside`.
- Switch: `config.json` `show_version`, with V2 as an overlay file on V1's timeline.
- First batch: batch 1 (plumbing plus the drawn characters).
- 64x64 size: decided scene by scene. 2x for a lone character with the castle off, 1x for pairs
  and crowded scenes.
- Still open: each character's own questions (pose, frames, which way they face, colours beyond
  the art), asked at the start of its batch as usual.
