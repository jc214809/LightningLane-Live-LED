# Happily Ever After: what the real show does

Notes from watching a full recording of the show, for improving the synced show on the boards
(`display/fireworks/shows/happily-ever-after.json`, played by `display/fireworks/music_show.py`).
Start here when asked what to improve.

**Status (2026-10-11):** the score has been rebuilt from these notes (see ROADMAP.md). The
comparison tables below are against the *old* score, kept as the record of what was wrong; the
timeline and looks further down are what the new one follows.

- **Video:** https://www.youtube.com/watch?v=-LncKUxWMsQ (19:02, a guest's recording from the hub).
- **Studying it further:** [WATCH.md](WATCH.md) is the scene-by-scene workbook: a `/watch` prompt per
  scene, with Gemini's answers saved under each.
- **The words, timed:** [LYRICS.md](LYRICS.md) has every sung and spoken line with when it starts (Whisper
  on the demucs-split vocals), under the scene it's in: the measured anchors for scene boundaries.
- **Watched:** 2026-10-11, by Gemini (`gemini-3.7-flash` / `gemini-3.8-flash` through the `/watch`
  plugin), in four overlapping chunks. Its raw answers are `gemini-*.md` here; the question is
  `gemini-question.txt`; `watch-chunks.sh` re-runs it. Nobody here looked at frames: everything
  below is Gemini's description, good to a few seconds, and chunk 1 and chunk 2 disagree on
  4:38-5:13 (see Open questions).
- **Clock (measured, not Gemini's):** the video's audio is our board file
  (`sounds/happily-ever-after.wav`), the same recording with no cuts. Cross-correlating the two
  (`align_audio.py` here) puts **video time = audio time × 1.001 + 10.19 s**: 16 strong matches
  across the whole show sit within 0.04 s of that line, so the YouTube copy just runs 0.1% slow
  (~1 s over the show). Every *audio* time below is converted that way from Gemini's video times,
  so it's in the score's seconds; Gemini's own timestamps are only good to a few seconds, which is
  now the only error left.

## How the score held up

Most boundaries are within ±8 s of Gemini's, which is about its own accuracy: leave those. Five are
clearly wrong, all from guessing scene times from song lengths:

| Cue | Ours (s) | Video | Audio ≈ | Ours is |
|---|---|---|---|---|
| When You Wish interlude | 212 | 4:26 | 256 | 44 s early |
| Out There | 220 | 4:38 | 268 | 48 s early |
| Touch the Sky | 268 | 5:13 | 303 | 35 s early (but see Open questions) |
| He's a Pirate (castle on fire) | 815 | 13:08 | 777 | 38 s late |
| Go the Distance vocal / pyro | 874 / 899 | 15:00 / 15:26 | 889 / 915 | ~16 s early |

Smaller ones worth a look: the theme song's vocal starts at 47 (ours 63, but the pop beat at 63
matches), the friendship mash-up at 459 (ours 472), That's What Friends Are For at 513 (ours 502).

Every boundary, ours against the video:

| Moment | Video | Audio ≈ | Ours | Diff |
|---|---|---|---|---|
| Narration starts | 0:29 | 19 | 20 | −1 |
| Theme song vocal starts | 0:57 | 47 | 63 | −16 (the pop beat at 1:13 = 63 matches ours) |
| First fireworks of the show (chorus) | 1:48 | 98 | - | - |
| Castle drops to blue, sky dark | 2:27 | 137 | 131 | +6 |
| Tiana / evening star | 2:40 | 150 | 144 | +6 |
| When You Wish fanfare | 3:01 | 171 | 174 | −3 |
| Part of Your World | 3:22 | 192 | 184 | +8 |
| When You Wish interlude | 4:26 | 256 | 212 | +44 |
| Out There (bells) | 4:38 | 268 | 220 | +48 |
| Touch the Sky / Up balloons | 5:13 | 303 | 268 | +35 |
| How Far I'll Go | 5:36 | 325 | 322 | +3 |
| Aladdin's line (our "Silence") | 6:48 | 397 | 398 | −1 |
| Friend Like Me instrumental | 7:01 | 410 | 402 | +8 |
| Trashin' the Camp | 7:19 | 428 | 428 | 0 |
| Hakuna Matata | 7:37 | 446 | 448 | −2 |
| You've Got a Friend in Me | 7:44 | 453 | 458 | −5 |
| Friendship mash-up | 7:50 | 459 | 472 | −13 |
| That's What Friends Are For | 8:44 | 513 | 502 | +11 |
| Friend Like Me (Genie) | 8:58 | 527 | 527 | 0 |
| Olaf's line (our "Silence") | 9:37 | 566 | 562 | +4 |
| Love Is an Open Door | 9:47 | 576 | 568 | +8 |
| Can You Feel the Love Tonight | 10:14 | 603 | 604 | −1 |
| You'll Be in My Heart | 10:34 | 623 | 620 | +3 |
| Princess garden | 10:48 | 637 | 633 | +4 |
| I See the Light | 11:19 | 668 | 664 | +4 |
| Emperor's warning | 12:15 | 724 | 721 | +3 |
| Villains | 12:33 | 742 | 742 | 0 |
| He's a Pirate, castle on fire | 13:08 | 777 | 815 | −38 |
| Embers / Mufasa | 14:26 | 855 | 860 | −5 |
| Go the Distance vocal | 15:00 | 889 | 874 | +15 |
| Go the Distance pyro resumes | 15:26 | 915 | 899 | +16 |
| Narrator closing | 16:44 | 993 | 986 | +7 |
| Happily Ever After reprise | 17:08 | 1017 | 1010 | +7 |
| Tink flies | 17:33 | 1042 | 1041 | +1 |
| Final barrage | 18:18 | 1087 | 1083 | +4 |
| Last hit, show ends | 18:39 | 1108 | 1102 | +6 |

## Looks that are wrong

- **Opening sky is dark until the chorus (audio ~98).** The real show fires nothing for the first
  1:40: the castle, keyhole and searchlights carry it. Ours launches at the everyday rate from 0
  (no `rate` on the first scene, so section intensity 0.6 / 0.6 = 1.0). The first pyro is a
  red-and-gold peony with gold willow streamers on the chorus drop.
- **I See the Light has fireworks.** Ours is `rate: 0`. Real: white/gold bursts at its start (audio
  669), red/gold at 687-695, a pause, sparse gold willows at 709-714. Keep the lanterns; the sky is
  sparse, not empty.
- **The two "Silence" scenes are spoken lines.** 395: Aladdin, "Trust me, having a best friend by
  your side opens up a whole new world of possibilities", with lamp smoke in gold and purple over a
  midnight-blue castle. 559: Olaf, "Some people are worth melting for", icy blue and purple castle,
  snowflakes, one gold shell. Both nearly dark, so `rate: 0` is close; the castle looks are missing.
- **Up balloons belong after Touch the Sky,** in the interlude (audio ~304-324): a balloon cluster
  fills the castle and lifts the house, with red, green and blue comets rising in parallel.
- **Part of Your World:** Gemini saw only Ariel, no Remy or Rapunzel (weak: it had only this
  stretch to go on). It also saw no jellyfish, but sunlight beams through water, bioluminescent
  bubbles, and magenta/ruby peonies on the climax.
- **To Die For isn't its own scene.** Villains (green/purple/red, Ursula, Scar, Hades, green
  searchlights) run 742-777, then the castle burns. (Checked by eye 2026-10-16: wrong. 742-750 is
  Mulan's battle, 750-752 a teal flash, then the Incredibles fight the Omnidroid; see WATCH.md 7.2.)
- **He's a Pirate** also has real flame jets on the castle terraces (audio ~779, 789, 833, 839), an
  emerald-green barrage mid-scene (~806-812), and a ruby-red and white finale (837-847).
- **Mufasa talks until ~889** ("Look inside yourself... Remember who you are"), sky empty, castle
  near-black with a molten ember core and his face in the clouds over the spire.
- **Smiley bursts are in Go the Distance** (audio ~976-978), not the Genie scene. The keyhole
  glows gold at the gate as Go the Distance builds (~914).
- **Tink crosses in ~3 s** (1042-1045) with green wings and pixie dust. Ours takes 12 s; that was
  a choice, so only flagged.
- **Finale:** rainbow barrage 1088-1097, then a white/gold mine fan up from the castle base, then a
  wall-to-wall white flash and gold willow on the last hit (~1100-1106).

## Scene by scene

Times are audio seconds ((video − 10.19) / 1.001). Colours as Gemini named them.

**Opening (0-129)**
- 0-19 Theme fanfare. Castle warm amber/red/gold with blue spires; golden keyhole glows at the gate
  from 0; white searchlights fan behind the castle 0-17. No fireworks.
- 19-47 Narrator ("And they lived happily ever after... Each of us has a dream"). Searchlights off,
  keyhole dims, sky dark.
- 47-98 Theme song: female solo, pop beat from 63. Gold ribbons swirl over the castle (47-55), the
  portal glows with an opening door, red/purple/gold filigree mapping (64-97); yellow and cyan
  searchlights 71-97. Still no fireworks.
- 98-137 Chorus. 98-104 red and gold peonies with gold willow streamers; 105-118 heavy red, gold
  and white strobe barrage with crossing comets; 119-128 huge gold palm/kamuro canopy with white
  strobes on the sides; 129-137 big gold brocade crown, fading to smoke.

**Dreams (137-303)**
- 137-150 Music-box transition: castle royal blue and icy cyan, sky dark.
- 150-171 Down in New Orleans: midnight blue, Ray and Evangeline (the evening star) twinkle at the
  top spire, Tiana's silhouette in the centre window; small single comets.
- 171-192 When You Wish brass fanfare: Ray buzzing over a blue castle; fan of white/gold comets from
  the base (171-178), paired gold chrysanthemums, then green and white glitter (186-192).
- 192-256 Part of Your World: turquoise/navy/purple water, glowing bubbles, Ariel swimming
  (204-214), then sunbeams through the water and Ariel reaching up in the window. Sparse gold
  willows drip over the spires, then magenta/ruby peonies (215-228), gold and ruby (229-242), white
  and gold brocade (252-256).
- 256-268 When You Wish interlude: castle lavender, pink and turquoise; magenta/purple comets fan
  left and right (257-262), then a lull.
- 268-303 Touch the Sky (Brave; titled Out There until its lyrics were checked): Merida's "Your
  destiny lies within you" (265-271), the song from 276. (V2's Merida lets go on "touch", 295.36.) Gemini described bells, gothic stone, moss, rose windows, Quasimodo swinging across the towers,
  white doves along the spires (289-302). Gold willow, one red comet high over the spire (277-280),
  emerald and white strobes (280-290), a fan of red/gold comets and ruby peonies (291-300).

**Journey (303-397)**
- 303-324 Up: balloons fill the castle and lift the house; one gold shell, then red, green and blue
  comets in parallel (311-315). Touch the Sky's bagpipes, tartan and fiery wisps are here too.
- 325-397 How Far I'll Go: the Heart of Te Fiti spiral on the spire (325), Moana in the archway
  (336), ocean, Gramma Tala's manta ray, Moana voyaging. Sparse low bursts and roman candles
  (341-354), green/gold/white building (355-369), then a heavy gold brocade barrage with turquoise
  searchlights and green/yellow shells (370-396).

**Friendship (397-566)**
- 397-410 Aladdin's line over lamp smoke (gold and purple) on midnight blue; one gold willow.
- 410-428 Friend Like Me instrumental: brass patterns, lanterns, geometric mapping; quick blue and
  gold roman candles from the roofs, white shells.
- 428-446 Trashin' the Camp: Terk, vines, vivid green and chartreuse; green flares and green/orange
  comets on the drumbeats, green searchlights.
- 446-453 Hakuna Matata: Timon and Pumbaa marching along the base in sunset yellow/orange/red; red
  and gold shells.
- 453-459 You've Got a Friend in Me: Woody and Buzz, Andy's cloud wallpaper on the towers; red and
  yellow bursts.
- 459-513 Mash-up: Ralph and Vanellope (8-bit bricks, candy) 459-473, Hiro and Baymax 474-481, Judy
  and Nick (neon city) 482-493, Joy and Sadness (memory orbs) 494-512. Multicolour searchlights,
  steady pastel pink, blue, green and gold bursts.
- 513-526 That's What Friends Are For: Sully and Mike opening doors across the turrets; castle
  turquoise and purple; soft gold shells.
- 527-566 Friend Like Me (Genie): Genie in neon forms, the castle a pulsing marquee with spinning
  gears. Crossing magenta/green/gold comets, ring/pattern shells (543-547), and a huge gold willow
  barrage with roof fountains showering the castle (554-566).

**Love (566-724)**
- 566-576 Olaf's line: icy blue and purple, Olaf at the base, snowflakes up the spires; one gold
  shell.
- 576-603 Love Is an Open Door: hearts, floral scrollwork, rose/magenta stained glass, ending royal
  blue and violet. Gold fan comets, pink/violet/gold peonies in pairs and threes, gold willows.
- 603-623 Can You Feel the Love Tonight: starry indigo; WALL-E and EVE among constellations, then
  Simba and Nala. Spaced gold brocade, soft pink/violet peonies.
- 623-637 You'll Be in My Heart: magenta, lavender and gold; Tarzan and Kala, Dumbo and Mrs. Jumbo.
  Pink, violet and white starbursts, comets angled out from the terraces.
- 637-668 Princess garden: pink and rose stained-glass arches, blooming flowers and waterfalls;
  Cinderella and Charming, Tiana and Naveen, Ariel and Eric, Belle and Beast. Steady gold brocade,
  pink peonies, gold palms.
- 668-724 I See the Light: midnight blue, hundreds of orange lanterns drifting up, Rapunzel and
  Flynn in the boat near the clock terrace at the end. Fireworks as in "Looks that are wrong".

**Adversity (724-855)**
- 724-742 The Emperor ("The flower that blooms in adversity is the most rare and beautiful of
  all"), a gong, brass. Castle dark navy, charcoal, deep crimson; low crimson and gold comets.
- 742-760 Mulan's battle (the score had villains; checked by eye 2026-10-16): Mulan fights the Huns
  in the window over the gate, the Fa family's red dragon in the gate, the lower walls fire orange
  and the upper towers icy blue (the avalanche); a teal-green flash at 750-752; a dark sky, a red
  rocket, red peonies. 760-777 the Incredibles and the Omnidroid.
- 777-855 He's a Pirate: the castle cracks and burns in red and orange; terrace flame jets; green
  shells and lime comets (806-812), dense red chrysanthemums and gold willow fans (814-827), a
  ruby-red and white perimeter finale (837-847), smoke.

**Triumph (855-993)**
- 855-889 Embers and Mufasa: castle near-black with a red-orange ember core, Mufasa in the clouds
  over the spire (862); no fireworks, slow spotlight sweeps through the smoke.
- 889-915 Go the Distance vocal: the castle rebuilds in cyan, royal blue and gold columns;
  stained-glass hero panels start to form; Hercules in gold light (904-912); keyhole glows gold
  (914).
- 915-993 Go the Distance climax: the whole castle is stained-glass windows of heroes (Hercules,
  Megara, Tarzan, Jane, Mulan, Merida...) in gold masonry under blue roofs. Gold/white willows and
  peonies with side comet plumes (915-947), rainbow comets crossing over the spires (950-954), heavy
  gold brocade and white strobes (955-975), smiley/ring shells (976-978), green side comets, and a
  gold willow canopy (987-993).

**Conclusion and finale (993-1108)**
- 993-1017 Narrator ("And so, our journey comes to an end... reach out and find your Happily Ever
  After"). The stained glass stays lit, the keyhole glows; no fireworks; blue and white
  searchlights pan behind.
- 1017-1042 Reprise: stained glass turns to gold scrollwork, the keyhole beams; gold comets with
  white smoke tails cross over the spires (1019-1034); gold/white spotlights from the base.
- 1042-1087 You Can Fly: Tink leaves the upper right spire (1042-1045). Red, gold, green and cyan
  swirls on the castle. Perimeter comets fan in and cross (1039-1047), then gold palms, red strobes,
  lime peonies and purple bursts (1048-1074), gold comets arching over the spire (1079-1087).
- 1087-1108 Final chorus: castle saturated gold and red; rainbow barrage (1088-1097); white and gold
  strobe mine fan from in front of the castle (1098), the white flash and gold willow on the last
  "After!" (~1100-1106), the castle washed white.
- After: a park announcement, then exit music; the castle sparkles gold and royal blue with slow
  searchlights.

## Ideas for the boards (Gemini's, sorted by me)

Cheap, and fit what `show_effects.py` already does:
- Start with a dark sky: put `rate: 0` on 0-98 and let searchlights and the keyhole carry it; the
  first burst on the chorus gets a lot of punch from it.
- Lanterns over a sparse sky rather than an empty one.
- Crossing comets over the spire for the reprise and before the finale: a diagonal X reads well at
  64x32.
- An abrupt switch from pink to neon green (`#39FF14`) and purple when the villains arrive.
- Mufasa: sky off, castle dark slate, a few centre pixels pulsing dull red (`#8B0000`-`#FF4500`).
- The last hit: a fan of white/gold comets from the base, then 1-2 frames of pure white over the
  sky, then a gold glitter field.

New effects:
- Terrace flame jets: flickering orange/yellow columns 2-3 px tall on the castle ledges, on the
  pirate beats.
- Te Fiti's heart: a small green (`#00FF44`) spiral on the spire as Moana starts.
- Stained-glass castle for Go the Distance: a grid of cyan/magenta/orange/blue in a gold frame (our
  `stained_glass` castle may already be close; compare).
- Up: rising comets in parallel red, green and blue.

## Open questions

- **4:38-5:13 (audio 268-303)** is settled: by its lyrics (Whisper, 2026-10-11) it's Touch the Sky,
  from Merida's "Your destiny lies within you" at 265; the score's scene was retitled from Out There.
  Its old look (bells, gothic stone, doves) was Gemini's Out There reading; checked by eye (2026-10-15),
  the stone and bells moved to Out There (215-256, which is Notre Dame) and the doves are gone.
- Whether Remy and Rapunzel really are in Part of Your World; ask Gemini again with just
  3:12-4:30.
- Settled: our audio and the recording are the same track (see Clock). Boundaries can be set to the
  second from the sound itself: `align_audio.py --at <video seconds>` gives the audio time of any
  moment in the video.

## Checking against the recording

`python3 tools/render_show.py --recording` records our show as the boards draw it and downloads this
recording; `tools/show_sync_checker.html` then plays the two side by side on one clock (using the
`recording` entry in the score: video = audio × 1.001 + 10.19). Press M where a scene really changes;
the page lists each mark against the score's start and gives new start times to paste back.

## Lining up the audio

`python3 docs/shows/happily-ever-after/align_audio.py` (needs `yt-dlp`, `ffmpeg` and numpy; the
project venv has numpy). It downloads the video's audio, downmixes both to 4 kHz mono, and
cross-correlates 30 s windows of onset envelopes every 20 s, printing each window's offset and peak
strength. Peaks above ~4.8 are real matches; weaker ones (quiet stretches, crowd noise) wander and
should be ignored. Fitting the strong ones gave video = audio × 1.001 + 10.19 (2026-10-11).

## Re-running Gemini

`bash docs/shows/happily-ever-after/watch-chunks.sh [out_dir]` from the repo root. What made it work
(2026-10-11):
- Free-tier key: only the Flash models (`gemini-3.7-flash`, `gemini-3.8-flash`). Pro is 429 (0 a
  day); `gemini-2.5-pro` is closed to new users.
- The whole video in one request hits Google's ~10 min deadline (HTTP 504), whatever
  `WATCH_GEMINI_TIMEOUT` says. Chunks of ~5.5 min, overlapping 30 s, answered in 1-3 min each.
- "High demand" 503s come and go; the script alternates the two models every 3 min.
- `SSL_CERT_FILE=/etc/ssl/cert.pem`: the python.org Python has no CA bundle.
- For one stretch, ask a narrower question with `--start`/`--end`; ask for absolute video times.
