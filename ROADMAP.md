# Roadmap

Ideas and planned work for the board, in no fixed order. Nothing here is built yet unless it
says so. Before drawing any character or landmark, read [display/CHARACTERS.md](display/CHARACTERS.md)
and settle the open design questions first (ideally from a reference image): every entry
below lists the questions still to ask. Reference patterns are in
[docs/references/](docs/references/README.md), each labelled with whether it fits each board
as is (copied cell for cell, one cell per LED); entries below link theirs.

## 1. Characters to create

Built so far: Tinker Bell, Buzz, Figment, Dumbo, Stitch, Ralph, Sorcerer Mickey, Slinky,
Baymax, Genie, WALL-E (the side-view baler `walle_side` plays; the three-quarter view
`walle` is kept, out of the rotation), the Green Army Men (`army_men`), the Millennium
Falcon (`falcon`), Mike Wazowski (`mike`), the TRON light cycles (`tron`), Olaf (`olaf`),
Goofy (`goofy`), the Pixar Ball with Luxo Jr. (`luxo_ball`), Lightning McQueen (`mcqueen`),
Mater (`mater`), Chip 'n' Dale (`chip_dale`), Tigger (`tigger`), Jack, Sally and Zero
(`jack_sally`), the Seven Dwarfs Mine Train with Snow White (`mine_train`), Rex (`rex`), and the
Aliens and the claw (`aliens`), Forky (`forky`), the lightsaber clash (`saber_clash`), the lightsaber duels (`saber_duel`: Luke, Obi-Wan or Yoda against Vader, or Rey against Kylo Ren), and Kevin with Dug and his balloons (`kevin`).

Put a ✅ in the Done column when a character ships.

| # | Done | Character | Park / ride | Signature motion | Mechanic |
|---|---|---|---|---|---|
| 1 | ✅ | TRON light cycle | MK: TRON Lightcycle Run | a blue and a red cycle race across, top and bottom; their light trails are the wipe | Fly-by |
| 2 | ✅ | Olaf | EPCOT: Frozen Ever After | stacks himself out of snowballs while it snows, waves, and walks off | Standalone, drawn in code with a hand-drawn head |
| 3 | ✅ | Mike Wazowski | MK: Monsters, Inc. Laugh Floor | pops up, blinks, looks around, grins, then scares | Peek, drawn in code like Baymax |
| 4 | ✅ | Luxo Jr. lamp | DHS: Pixar Place | with the Pixar Ball (#13): bats it, chases it, or searches for it with his light | Standalone (`luxo_ball`) |
| 5 | | Hitchhiking Ghosts | MK: Haunted Mansion | three see-through ghosts float across | Fly-by |
| 6 | ✅ | Jack Skellington | Halloween party nights: his meet | walks in, kisses Sally (#47) after Zero (#53) floats across | Standalone (`jack_sally`) |
| 7 | | Santa Goofy / Santa-hat Mickey | Christmas party, Jollywood Nights | red-and-white holiday cameo | TBD |
| 8 | | Remy | EPCOT: Remy's Ratatouille Adventure | scurries along the bottom | Fly-by |
| 9 | | Na'vi banshee | AK: Avatar Flight of Passage | glowing blue and purple swoop | Fly-by |
| 10 | | Nemo and a school of fish | EPCOT: The Seas with Nemo & Friends | a school of fish swims across as the wipe | Fly-by |
| 11 | | Steamboat Willie Mickey | MK | whistling at the wheel | TBD |
| 12 | | Monorail | all of Walt Disney World | glides across as a band of color | Fly-by |
| 13 | ✅ | Pixar Ball | DHS: Pixar Place, Toy Story Land | bounces in with Luxo (#4), one of three stories | Standalone (`luxo_ball`) |
| 14 | ✅ | Green Army Men | DHS: Toy Story Land | parachute in, land, chutes slump, hop off in step on their bases | New: top-down drop reveal |
| 15 | ✅ | Lightning McQueen | DHS / MK Cars area (status to confirm) | zooms in, skids to a stop, peels out leaving speed streaks | Drive-by (`mcqueen`) |
| 16 | ✅ | Rex | DHS: Toy Story Land | stomps in, stops mid-board and roars, jaw wide and the board shaking, then stomps off | Walk-in (`rex`, `wants_new` for the shake) |
| 17 | ✅ | Goofy | MK: The Barnstormer | flies his biplane through a loop-the-loop, towing a YAHOOEY! banner | Fly-by (loop) |
| 18 | ✅ | Little Green Men (Aliens) | DHS: Toy Story Mania!, Alien Swirling Saucers | a crowd shuffles in, the claw picks one at random and lifts him off: YOU'VE BEEN CHOSEN!; the rest shuffle off | Standalone (`aliens`) |
| 19 | | R2-D2 | DHS: Galaxy's Edge | rolls across on his treads, dome swivelling, light blinking | Fly-by |
| 20 | ✅ | Millennium Falcon | DHS: Smugglers Run, Rise of the Resistance | drops out of hyperspace, cruises, then jumps to lightspeed; the old screen streaks away and a flash fades to the new ride | Standalone (`wants_prev` + `wants_new`) |
| 21 | | Baby Groot | EPCOT: Guardians: Cosmic Rewind | sprouts from the bottom edge, grows like Baymax inflates, then dances | Peek (procedural, not fixed art) |
| 22 | | Ray the firefly | MK: Tiana's Bayou Adventure | glowing firefly wanders across, leaving a light trail | Fly-by |
| 23 | ✅ | Tigger | MK: Many Adventures of Winnie the Pooh | 64x64: bounces across on his tail; 64x32: walks in low, wiggles his tail, pounces off | Fly-by (bounce / stalk) |
| 24 | | Jungle Cruise hippo | MK: Jungle Cruise | eyes and ears surface from the bottom, wiggles its ears, sinks back down | Peek |
| 25 | | Donald Duck | EPCOT: Gran Fiesta Tour | tantrum knocks the old screen to pieces, feathers flying | Wreck (`wants_prev`) |
| 26 | | Yeti | AK: Expedition Everest | huge dark silhouette looms up behind the screen, eyes glowing | Peek |
| 27 | | Simba on Pride Rock | AK | held up against an orange sunrise gradient | Landmark/scene, not a ride transition |
| 28 | | Madame Leota | MK: Haunted Mansion | green glowing head appears in a crystal ball | Peek; pairs with #5 for Halloween |
| 29 | | Cinderella's pumpkin coach | MK | a pumpkin bursts into sparkles and becomes the coach | Assemble |
| 30 | ✅ | Chip 'n' Dale | MK / DHS (various) | run in from opposite sides and meet nose to nose, or rope-swing in (Dale bonks Chip), scurry off | Run-in from both edges; rope swing |
| 31 | | Max and Roxanne (A Goofy Movie) | TBD | TBD | TBD |
| 32 | ✅ | Mater | Cars (with McQueen, #15) | drives across backwards, grinning | Drive-by (`mater`) |
| 33 | | Grogu | DHS: Star Wars: Galaxy's Edge | floats across in his hover pram, ears twitching; or raises a hand and Force-lifts the old screen away | Fly-by, or Wreck (`wants_prev`) |
| 34 | | Lumiere, Cogsworth, Mrs. Potts and Chip | MK: Enchanted Tales with Belle, Be Our Guest | the enchanted objects parade across, "Be Our Guest" | Fly-by (parade) |
| 35 | | Boo | MK: Monsters, Inc. Laugh Floor | runs in giggling in her monster costume | TBD; pairs with Mike (#3) and Sulley (#48) |
| 36 | | Dug | AK (Up; no ride) | runs in, stops dead, head snaps round ("Squirrel!"), dashes off | Run-in; he's in `kevin` (#63), front-facing, so this needs a side view |
| 37 | ✅ | The Seven Dwarfs | MK: Seven Dwarfs Mine Train | a short mine train rolls across: a few dwarfs, one per car, then a gem car | Fly-by (train) |
| 38 | | The Evil Queen | MK; Halloween party nights | holds out the poisoned apple, or the old screen fades into her magic mirror | TBD |
| 39 | ✅ | Forky | a surprise anywhere | waddles in, spots the old ride (TRASH!), dives head first through the bottom and the old screen goes down the hole after him | Wreck (`wants_prev`, `forky`) |
| 40 | | Hamm | DHS: Toy Story Land | trots across, coins clinking out of his slot | Fly-by |
| 41 | | Heihei | EPCOT: Journey of Water, Inspired by Moana | wanders across, pecking at nothing, and walks off the edge | Run-in |
| 42 | | Maleficent | MK; Halloween party nights | green flames rise from the bottom and she appears in them | Peek |
| 43 | ✅ | Pooh and his balloon | MK: Many Adventures of Winnie the Pooh (and a surprise anywhere) | floats up from the bottom on his red balloon, hovers, and drifts off the top, uncovering the ride below him | Wipe (rising, `wants_prev`) |
| 44 | | Mr. and Mrs. Potato Head | DHS: Toy Story Mania! | their pieces pop off and fly back on | TBD |
| 45 | | Princesses (and villains) | MK | one princess at random walks across; a villain instead on Halloween nights | Fly-by |
| 46 | | Pua | EPCOT: Journey of Water, Inspired by Moana | trots across, with Heihei (#41) | Run-in |
| 47 | ✅ | Sally | Halloween party nights: her meet | walks in and kisses Jack (#6) | Standalone (`jack_sally`) |
| 48 | | Sulley | MK: Monsters, Inc. Laugh Floor | rises up behind the screen and roars | Peek; pairs with Mike (#3) and Boo (#35) |
| 49 | | Tiana | MK: Tiana's Bayou Adventure | kisses the frog, a burst of sparkle | TBD; pairs with Ray (#22) |
| 50 | | Oogie Boogie | Halloween party nights | looms up, bugs spilling out of him over the screen | Peek |
| 51 | | Woody | DHS: Toy Story Land | rides Bullseye (#54) across, waving his hat | Fly-by |
| 52 | | Jessie | DHS: Toy Story Land | runs in, swings her lasso, yodels | TBD |
| 53 | ✅ | Zero | Halloween party nights: the Jack and Sally meet | floats across as the wipe, his nose glowing | Standalone (`jack_sally`) |
| 54 | | Bullseye | DHS: Toy Story Land | gallops across, Woody (#51) riding | Fly-by |
| 55 | | RC | DHS: Toy Story Land | races across, wheels spinning | Drive-by |
| 56 | ✅ | Bluey and Bingo as the Grannies | none (Bluey; a surprise anywhere) | shuffle slowly across side by side in their granny dressing gowns, Bingo lifting and planting her walker; the new screen appears behind them | Wipe (walk-across, `grannies`) |
| 57 | ✅ | Bluey and Bingo, Keepy Uppy | none (Bluey; a surprise anywhere) | run in after a red balloon, face each other and take turns batting it up, then chase it off | Wipe (run-across, `keepy_uppy`) |
| 58 | ✅ | Lightsaber clash (blades only) | DHS: Galaxy's Edge, Star Tours | a red and a blue blade swing in, lock in an X with sparks, then go upright and sweep apart; the new ride opens between them | Wipe over the old screen (`saber_clash`, `wants_prev`) |
| 59 | ✅ | Luke vs Darth Vader | DHS: Galaxy's Edge, Star Tours | walk in, trade three blows with sparks, lock blades, and are thrown apart to the edges as the new ride opens between them | Wipe over the old screen (`saber_duel`, `wants_prev`) |
| 60 | ✅ | Obi-Wan vs Darth Vader | DHS: Galaxy's Edge, Star Tours | Luke's fight, with Obi-Wan | Wipe over the old screen (`saber_duel_obiwan`, picked by `saber_duel`) |
| 61 | ✅ | Yoda vs Darth Vader | DHS: Galaxy's Edge, Star Tours | Yoda stays small, hops in and leaps into each of his attacks | Wipe over the old screen (`saber_duel_yoda`, picked by `saber_duel`) |
| 62 | ✅ | Rey vs Kylo Ren | DHS: Galaxy's Edge, Star Tours | the same fight; Kylo's crossguard blade crackles | Wipe over the old screen (`saber_duel_kylo`, picked by `saber_duel`) |
| 63 | ✅ | Kevin and Dug (Up) | a surprise anywhere | Kevin struts across with Dug chasing behind her; his balloons lift him slowly higher as he goes, and he floats off the right edge up high while she stays on the ground | Over the finished screen (`kevin`, `over_screen`) |

### Notes per character

**1. TRON light cycle.** The best match for an LED board: neon blue on black, and a light
cycle is just a wedge with a glowing trail. The trail becomes the wipe line; it could leave
the trail as a glowing border for a beat before it fades.

Decided:
- Two bikes race every time: blue (cyan) across the top, red along the bottom, red starting
  a length behind and level by the far edge. (First decided as one bike, red 1 in 200 of its
  visits; the race replaced that.)
- Reference: the user's pixel-art mockup (side profile, cyan-rimmed wheels, dark body with
  cyan edge lines, a thick solid cyan trail out the back, over a perspective grid floor).
- Direction: left to right, like the other fly-bys (the mockup mirrored).
- The trails: a glowing band at each bike's wheel height; behind the trailing bike, top to
  bottom, is already the new ride (a `FlyByReveal`). They hold a beat, then de-rez pixel by
  pixel (dimming would darken the screen under them; a Pi canvas can't be read back).
- Size: 1x on both boards (2x filled half of 64x64).
- No grid floor, and no rider: just the bike.
- Where: the `SURPRISES` rotation only, no boost on TRON Lightcycle Run. Chance not yet
  0.008, like Mike.

Notes on the mockup at this resolution:
- It's about 100 pixels across with the bike about 48x20; on 64x32 it has to be roughly
  half that, so keep only the bold parts: the two cyan wheel rings, the cyan line along the
  body, the trail.
- LEDs show black as off, so the black outline and the dark-grey body and rider vanish on
  the board. The bike will read as its glowing lines; the body needs a lifted charcoal (the
  Sorcerer Mickey fix) if it's to show as a shape at all.
- The trail is the strongest thing in it and maps straight onto the wipe.
- The grid floor is very TRON, but over a ride screen it would cover the text.


**2. Olaf.** White stacked circles, a carrot nose and twig arms: simple shapes that can be
drawn procedurally, the way Baymax is (the best-performing character so far). Either
snowballs roll in and stack into Olaf, who waves, or he slides across on his belly.

Decided (from the user's references: the BRIK pixel-art Olaf, a Frozen still and a line
drawing):
- Motion: snowballs stack into Olaf over the finished ride screen. The bottom ball rolls in
  from the left and pops up onto his two little feet, the middle one rolls in from the
  right and hops up onto it, and the head drops in from the top; then his face, twig arms
  and hair pop on, he waves, and he walks off the right edge, feet stepping.
- Snow falls over the whole board while he's there and stops once he walks off. (A little
  snow cloud over his head came first; on 64x32 there was no room for it.)
- His head is hand-drawn: 64x64 has the BRIK pixel-art head cell for cell, 64x32 a redraw
  of it shrunk to fit, both turned three-quarters with the mouth a tall dark D down the
  left side and his big tooth white under the lip. Drawing the head in code put the eyes,
  carrot and mouth in the wrong places at this size.
- Where: the `SURPRISES` rotation only, at 0.005.

**3. Mike Wazowski.** A green circle with one huge eye: the simplest face there is, and
unmistakable. Pops up from the bottom edge and blinks, like Stitch's peek.

Built (`MikeReveal`, `mike`): his whole egg-shaped body rises over the finished ride
screen, blinks, looks left then right, grins wider, then jumps with his arms up and his
mouth wide (teeth top and bottom) and ducks away, 3.3s. Drawn in code like Baymax, body
half-width 8 on 64x32 and 12 on 64x64. In the rotation at 0.008 and a ride visitor on
the Laugh Floor, 1 in 10.

Reference: [mike.jpg](docs/references/mike.jpg), 35x30: tight on 64x32 (fills the height),
fits 64x64 as is.

**4. Luxo Jr.** Lamp and ball are simple geometry, and the lamp's light cone is built for
LEDs. Hops in with a squash and stretch; its light cone reveals the next screen. Could be
folded into the Pixar Ball (#13) as one scene: the lamp hops in and bats the ball.

Decided: he's being built with the Pixar Ball as one scene; see #13 for the plan. His
reference is a pixel-art Luxo the user shared (shade with the yellow bulb, spring arm,
base), transcribed cell for cell.

**5. Hitchhiking Ghosts.** Three ghostly silhouettes drawn see-through (additively, like
Genie's smoke) over the screen, floating across with a faint bob. Fits the Halloween party
season.

**6. Jack Skellington (Halloween party nights).** Built with Sally (#47) and Zero (#53) as one
scene, `jack_sally`. It plays only on the meet's own screen ("Meet Jack Skellington and Sally at
Mickey's Not-So-Scary Halloween Party", listed only on party nights), half the time, through
`RIDE_VISITORS`. Zero floats across as the wipe, his nose pulsing; then Sally walks in from the
left and Jack from the right, they lean in and kiss, a heart floats up, and they walk back off.
Zero is from [Zero.jpg](docs/references/Zero.jpg) (his outline rows hang off 64x32). The pair is
the user's pattern [Sally and Jack pair.png](<docs/references/Sally and Jack pair.png>), shortened
from 39 rows to 32 (rows out of their clothes and legs, hair and hands kept whole) so it fits
64x32; 1x on both boards, split into Sally and Jack by colour for the walk.

Other references, unused:
- [Jack Skellington.jpg](<docs/references/Jack Skellington.jpg>): his head, 42x46. Too tall for
  64x32 as is; fits 64x64.
- [Jack and sally.jpg](<docs/references/Jack and sally.jpg>): a photo of beads, Jack with
  Sally and two pumpkins, about 43x39 for the pair. Too tall for 64x32 as is; fits 64x64.

**7. Santa Goofy / Mickey in a Santa hat (Christmas party, Jollywood Nights).** The hat's red
and white would echo the green/red/white holiday star on the park-hours screen.

**8. Remy.** Scurries along the bottom edge with a chef-hat hop. Caveat: a small grey rat is
Figment's original "purple blob" problem all over again. It only works close-up and large,
or with Linguini's toque as the silhouette.

**9. Na'vi banshee.** A glowing blue and purple swoop; the bioluminescent colors would look
great on LEDs. Caveat: wings are hard at this size.

**10. Nemo and a school of fish.** Orange and white stripes swimming across. One Nemo is
tiny; a school of fish crossing makes a better wipe.

**11. Steamboat Willie Mickey.** A black-and-white whistle at the wheel. Caveat: black on
black, so it needs grey fills (the fix that made Sorcerer Mickey's ears visible). Mickey
already appears as Sorcerer Mickey.

**12. Monorail.** A vehicle, not a character, but very recognisable and trivial to draw.

**13. Pixar Ball.** A circle is the easiest shape to draw on a pixel board, and its colors
are bold and distinct: yellow ball, blue band, red star. On 64x32 a ball about 12-14 LEDs
across leaves room for a 5-pixel star. Its motion is built in: bouncing, squashing flat on
each landing and stretching as it rises (simple shape plus one strong motion, like Baymax).
Options:
- Bounce-by (preferred): three or four hops across the board uncovering the next ride
  behind it, each landing kicking up a small puff. About 1.5-2s.
- With Luxo: the lamp hops in and bats the ball, which bounces off and reveals the screen.
- Squash-reveal: drops in, squashes flat across the bottom, springs off the top (more
  abstract).

Decided with the user (2026-09-29):
- With Luxo (#4) as one scene. Build three stories and pick after watching them (or keep
  them all, one at random per showing, like the pumpkin's wink or hop): the ball bounces
  in and Luxo hops in and bats it off (his lunge is placed from the pixels so his shade
  visibly meets the ball); Luxo chases the ball across; and a searchlight: the board is
  dark, Luxo hops in, switches his light on and sweeps it looking for the ball, his head
  tilting with the beam, the ball showing only where the beam touches it; he finds it, it
  hops, and the beam widens over the ride. (The first "light" story was the bat played in
  the dark, too like the first.) Friendly: no Pixar-intro squash gag. All three kept, one
  at random per showing.
- The ball spins a quarter turn each hop, like it's rolling (exact pixel turns).
- The ball is the user's 21x21 pixel-art reference, cell for cell, on both boards.
- Where: the `SURPRISES` rotation only, at 0.005 (0.008 would have pushed surprises to
  10% of ride screens).
- Luxo: the user's pixel-art reference, cell for cell, 1x on both boards.

**~~14. Green Army Men.~~ Done** (`ArmyMenReveal`, `"army_men"` in `SURPRISES` at 0.015,
`display/animation/characters/army_men.py`). The parachutes are what make them work: a canopy is a big, simple
shape that reads instantly, and the soldier underneath only needs a wide-brimmed helmet, a
rifle slung diagonally, and the classic wide-planted stance to read as a toy soldier. Built
from the user's reference image: a camo dome (olive/gold patches) with a white five-point
star badge, not the plain white/tan first assumed -- the star only read once it was
rasterized as a real polygon instead of approximated in ASCII (see CHARACTERS.md's "render
it and look" lesson; the first four attempts came out as a face with two eyes).

Three soldiers parachute in at staggered delays (each falls for its own `FALL_S`, so they
land one after another, not together) and sway side to side on the way down. The next
screen is uncovered top-down as a curtain that tracks the lead soldier's own descent --
the new mechanic nobody else uses, and the first reveal to need both `wants_prev` (the old
screen, visible under the drop) and `wants_new` (the new screen, revealed as they fall).
Each hangs on rigging lines that swing like a pendulum and meet above his helmet; each lands
with a puff of dust off his base, and his chute deflates, drops its star and slumps to the
ground downwind behind him. Once everyone's down they hold, then hop off the right edge in
step on their bases, the way the toys move in the films.

Settled: three soldiers, staggered; chutes collapse then they march off; camo canopies
(matching the reference, not the plain white first assumed); 1x on both boards -- three
soldiers at 2x collided and clipped the edges of 64x64, confirmed by rendering both.

Open: pairing with the Pixar Ball (#13) as a two-character Toy Story Land moment; a chance
boost on Toy Story Mania!, Slinky Dog Dash and Alien Swirling Saucers (see #3); checking it
on a real board (`force_surprise: "army_men"`).

**15. Lightning McQueen.** A natural fit for a board called LightningLane.
- Park tie-in: Hollywood Studios had Lightning McQueen's Racing Academy, and a Cars-themed
  area has been announced for Magic Kingdom. The current status of either isn't confirmed,
  so check before tying him to a ride. The app's name alone makes him fitting.
- How he'd look: a car in profile is one of the easiest shapes to read at this size: a low
  red body, two black wheels, a windshield. Bright red on black stands out, and a yellow
  lightning-bolt decal, even 3-4 pixels, sells it as him. About 20x8 LEDs at 1x fits both
  boards.
- The catch is his eyes. They're on his windshield, and in pure profile you'd see only one.
  Faces read better turned toward the viewer (see CHARACTERS.md), so either give him a
  slight 3/4 angle so both eyes show, or let the red and the bolt carry it with eyes as a
  detail.
- The motion: a high-speed drive-by. He zooms in, maybe skids to a stop mid-board for a
  "Ka-chow" beat with a flash of light off his side, then peels out, leaving orange-and-
  yellow speed streaks that fade and uncover the next ride.
- Bonus idea: since the board is about Lightning Lane waits, he could be the rare visitor on
  the rides with the longest waits or Lightning Lane prices, zooming past the line (see #3
  below).

Built (`McQueenReveal`, `mcqueen`), from the user's side-on pixel-art McQueen: he zooms in
from the left, skids to a stop mid-board, holds a beat and peels out off the right edge,
trailing orange-and-yellow speed streaks as long as he's fast; the new ride is uncovered
behind him. The source's "95" was a scramble at this size, so a clean 3x5 "95" is drawn on
his bolt. A four-point "Ka-chow" sparkle was tried and dropped: at this size it read as a
"+". 1x on both boards; in the rotation at 0.005 (WALL-E and Baymax were trimmed to 0.012
to keep surprises under 10% with him and Mater in). Built as a separate surprise from
Mater (#32).

**~~16. Rex.~~ Done** (`RexReveal`, `"rex"`, in `disney.RIDE_VISITORS`). From the user's art,
cell for cell, one per board: 38x32 for 64x32 (the board's full height) and 61x51 for 64x64
(the size of [Rex.jpg](docs/references/Rex.jpg)), both 1x. Decided with the user (2026-10-03),
replacing the earlier tail-swipe wreck plan: he stomps in from the left (the art faces left,
so he's mirrored), uncovering the new ride behind him, feet stepping (`walking_pixels`); stops mid-board, tips
his head back, his jaw swings open and he roars while the whole board, ride included, shakes a pixel a frame;
then shuts his mouth and stomps off the right. The open jaw is worked out from the art
(`_open_jaw`: a shear about a hinge column, the gap filled with his mouth), so editing the
art in the sprite editor keeps the roar working. About 5s, so the ride screen holds 3s after
him. Only on Toy Story Land's rides (Slinky Dog Dash, Toy Story Mania!, Alien Swirling
Saucers), 1 in 10 of their screens: `SURPRISES` was at 11.9% of its 12% cap.

**17. Goofy.** Flies his biplane across the board, a nod to The Barnstormer, his coaster in
Magic Kingdom's Storybook Circus. The plane is a bold, simple shape that carries the fly-by,
and Goofy's silhouette (green hat, long floppy ears, buck teeth) sits on top of it. This is
a separate character from the Santa Goofy idea in #7, which stays as it is.

Decided:
- Motion: a biplane fly-by (`FlyByReveal`), revealing the next ride in its wake.
- Framing: his head turned toward the viewer, not pure profile. His long snout collapses
  in profile the way Slinky's dog head did (see CHARACTERS.md).
- Frequency: the regular `SURPRISES` rotation only, with no boost on The Barnstormer's
  screen.

Decided with the user (2026-09-29):
- In the plane: his upper body sitting up tall in the cockpit, from the user's pin.
- Face: transcribed from a pixel-art Goofy the user shared, then touched up by the user in
  the sprite editor: green hat with a blue band, both eyes, the peach muzzle with his nose
  and tongue, ear swept back. Code-drawn faces read as a generic dog (a lesson: copy a
  real pixel artist's version of a face this detailed, as with Olaf). His black head and
  outline are a lifted charcoal, since LEDs draw black as off.
- Flight: a loop-the-loop. On 64x64 the whole loop fits; on 64x32 he loops out the top of
  the board and comes back in before flying off to the right. The plane turns in exact
  quarter steps (level, climbing, upside down, diving).
- The wipe: he tows a "YAHOOEY!" banner that bends round the loop like cloth; the new ride
  is uncovered behind the banner's tail, never covered back up while he loops back.
- Plane: the pin's biplane, repainted red and yellow like the Great Goofini's at The
  Barnstormer. 1x on both boards (2x ran the loop off a 64x64 board).
- Chance in `SURPRISES`: 0.008.

**~~18. Little Green Men (Aliens).~~ Done** (`AliensReveal`, `"aliens"`, in `disney.RIDE_VISITORS`).
Decided with the user (2026-10-04), replacing the plan to haul the old screen away: a crowd of
aliens shuffles in from both sides onto a dark board (64x32: a back row of heads over a front row;
64x64: three rows), the claw comes down and they all look up, it shuts on one, picked at random
each time, and lifts him off the top; YOU'VE BEEN CHOSEN! (5x8, a bigger CHOSEN! on 64x64, yellow
with a black edge); then the rest shuffle off the sides and the ride shows between them. The alien
is a 14x18 redraw of the one on [toy_story_4_sheet.png](docs/references/toy_story_4_sheet.png)
(19x21 there), 1x on both boards so there's a crowd. About 6s, then the ride screen holds 3s.
Only on Toy Story Mania! and Alien Swirling Saucers, 1 in 10 of their screens (after Rex's roll).
At a wait of 5 or less it plays every time as the movie's scene (`AliensToysReveal`,
`"aliens_toys"`): Buzz and Woody stand side by side in the crowd, alien-sized redraws from the
same sheet; the claw takes Buzz, Woody jumps for his boot once it's in reach and hangs on, and
both are hauled off the top. THE CLAW CHOOSES.

**19. R2-D2.** A dome on a tin-can body, rolling on his treads: about as simple a silhouette
as a droid gets, and blue-and-white on black reads clean. His dome swivel and a blinking
blue light are enough motion on their own.

Questions: pure fly-by, or does he stop mid-board to swivel his dome and beep; size on
64x64; reference image.

**~~20. Millennium Falcon.~~ Done** (`FalconReveal`, `"falcon"`, in `disney.RIDE_VISITORS`).
Drawn from the user's top-down photo turned nose-right: the photo was downscaled for the
outline, then only the bold features kept (the panelling came out as grey noise, the
Spaceship Earth problem): the gap between the mandibles, turret ring, docking arms, red
patches, the cockpit tube off the bottom edge (her starboard side, seen from above) with
light-blue windows, and a blue engine band along the back. She arrives as a streak that
snaps into the ship while star streaks shrink to points, cruises over the old screen,
flares her engine and jumps: she and the old screen's rows stretch into streaks off the
right edge, then a flash fades to the new ride. 1x on 64x32, 2x on 64x64. Only on
Smugglers Run and Rise of the Resistance, 1 in 10 of their screens.

**21. Baby Groot.** Sprouts up from the bottom edge and grows the way Baymax inflates —
procedural, not fixed sprite art, keyed off one growth factor — then does his headphones
dance. Small size is in-character (unlike Figment's "purple blob" problem, tiny actually
reads as baby), and the growth-then-dance beat gives him two story moments in one peek.

Questions: does he dance in place or wander a little while dancing; how tall at full growth;
reference image; chance in `SURPRISES`.

**22. Ray the firefly.** A single glowing dot with a light trail wandering across the board
— exactly the kind of thing LEDs render better than anything else. Very cheap to draw
(a bright core, a soft glow, a fading trail) and reads at any size.

Questions: a wandering/looping path or a straight fly-by; trail color (warm yellow-white,
or Ray's Cajun-firefly green); does he carry a tiny lantern; reference image.

**23. Tigger.** The bounce is the whole character — his tail is a spring, same idea as
Slinky's coils but applied to a single hop-across instead of a stretch. Bold orange and
black stripes are unmistakable on black.

Built (`TiggerReveal`, `tigger`), a different pose per board, both copied cell for cell from
the user's pixel-art grids and 1x. On 64x64 the cute sitting Tigger (pink nose, tail hanging
below; the pattern's hearts left out) bounces across on his tail four times, the tail
squashing two rows on each landing. On 64x32, where only the lying-down Tigger fits (exactly
32 rows once the tip of his tail lost a row of outline), he walks in low on all fours, his
paws stepping (`drawing.walking_pixels`), stops and wiggles his tail, then pounces off the
right in a little arc. A first version drawn by hand after PixelJoint's bouncing Tigger was
dropped: "a cat impersonating Tigger". Surprises were allowed up to 12% of ride screens to
fit him in at 0.005.

More references, not used: [Tigger and Pooh.jpg](<docs/references/Tigger and Pooh.jpg>)
(the two as one piece, 67x60: too wide for either board as is) and
[Pooh and gang.jpg](<docs/references/Pooh and gang.jpg>) (Eeyore, Tigger, Pooh and Piglet
overlapping as one piece, 53x125: fits neither board).

**24. Jungle Cruise hippo.** Just eyes, ears and nostrils surfacing from the bottom edge —
the classic "hippo submerged in water" gag, and it needs almost no detail to read, similar
to Mike Wazowski's one-eye simplicity. Pairs naturally with a wavy blue foreground band.

Questions: does it yawn/roar before sinking, or just wiggle its ears; add a water-ripple
foreground band across every screen it peeks over, or keep the board plain; reference image.

**25. Donald Duck.** A tantrum wreck, like Ralph and Rex but with his own signature: he
stomps in place, and the old screen's pixels fly apart with a scatter of white feathers.
Bright blue-and-white with an orange bill separates cleanly from the other wreck
characters' palettes (Ralph's reds, Rex's greens).

Built but **not in the rotation; needs work** (`DonaldReveal`, `donald`, playable with
`force_surprise`), from the user's Dodocraft pixel-art Donald copied cell for cell, 1x on 64x32
and 2x on 64x64, facing left. He boils over: walks in over the old ride, his face fills red
from the neck up while he trembles harder and steam puffs off his hat; a flash, and the old
screen blasts outward from him with feathers; he hops on one foot with his fists pumping
(`TANTRUM_ART`, drawn from the source art), cools back to white and storms off left. No quack.
A first version (stomp, jump, the screen collapsing like Ralph's) was dropped as boring.
Open: what's still missing; the user wasn't happy with this one yet.

**26. Yeti.** A huge dark silhouette looming up behind the screen with two glowing eyes —
scale and darkness are the whole effect, like a horror-movie reveal. Catch: a dark
character on a dark board risks vanishing, the same problem Sorcerer Mickey's ears had;
needs the charcoal-lift fix (a body color a few steps above pure black) so the silhouette
reads as a shape and not a hole.

Questions: does he swipe a paw at the screen (edges toward a wreck mechanic) or just loom
and recede (peek); eye color (icy blue, red); reference image.

**27. Simba on Pride Rock.** Gorgeous as a scene — Simba held up against an orange sunrise
gradient — but it's a tableau, not a transition with a start/middle/end like the other
entries here. Best suited to a park-title landmark (like the Tower of Terror or Spaceship
Earth entries) rather than a `SURPRISES` ride-screen character. Filed here as a landmark
candidate, not a character to build against the `FlyByReveal`/`PeekReveal`/wreck/assemble
mechanics.

Questions: build as a landmark for Animal Kingdom's park title screen instead of a ride
surprise; reference image; whether it needs its own scene the way the pumpkin and tower do.

**28. Madame Leota.** A green glowing head materializing inside a floating crystal ball —
high contrast (bright green on black) and an easy peek: rises, eyes open, maybe speaks a
line of her verse, fades. Pairs with the Hitchhiking Ghosts (#5) as a matched set for
Halloween party nights, the way the two jack-o'-lanterns pair today.

Questions: build alongside the Ghosts as one Halloween-season release, or independently;
does the crystal ball float/bob on its own; any text (a line of her rhyme in the landmark
font); reference image.

**29. Cinderella's pumpkin coach.** A pumpkin assembles/transforms into the coach in a
sparkle burst — reuses the Assemble mechanic (`MickeyReveal`'s `wants_new`) the way Sorcerer
Mickey does. Caveat: transformation-in-sparkles is close in feel to the Halloween pumpkin
landmark and to Sorcerer Mickey's materialize effect; risks feeling like a reskin unless the
transformation reads differently (pumpkin unfolding into a coach shape, not just fading in).

Questions: is the coach the end state that then rolls off, or does it just sparkle and hold;
how to make the transformation read as a distinct trick from Mickey's materialize; reference
image.

**30. Chip 'n' Dale.** Two small heads peeking up side by side. Caveat: CHARACTERS.md's
lesson from every character here is that a small or split silhouette is the hardest thing
to read at this resolution — two half-size heads competing for the same peek is a bigger
risk than any single-character entry on this list. Would need a reference image and a
render early to confirm it reads at all before investing further.

Built (`ChipDaleReveal`, `chip_dale`) as whole bodies, not heads, from the user's Rescue
Rangers pixel art (Chip's fedora and bomber jacket, Dale's red nose and Hawaiian shirt), 1x on
both boards: Chip runs in from the left and Dale from the right, feet stepping and bobbing
(`drawing.walking_pixels`), each uncovering the ride behind him; they meet nose to nose for
half a second, turn round and scurry back off their own sides (about 1.7s). Tried and dropped:
gliding across with no feet moving, and turning their heads to look out at us (front-facing
heads drawn after BRIK's read as different chipmunks, even redrawn with their white faces).
In the rotation at 0.005; the Army Men went to 0.010 to make room.

A second story, picked at random with the first (`chip_dale_swing` forces it): a Rescue
Rangers rope swing. Chip swings in on tan twine from above the top left in an arm-up pose
drawn from the user's art, uncovering the ride, lets go at the bottom and skids to a stop;
Dale swings in after him, doesn't let go in time and bonks into his back, and both wobble and
scurry off the right edge (about 3s). Other entrances considered: a rappel down a rope, a
chase where Dale trips and rolls, and the Ranger Wing (new art, and close to Goofy's plane).

**32. Mater.** Built (`MaterReveal`, `mater`) from the user's three-quarter pixel-art Mater:
he drives across backwards, his favourite way, facing right with his buck-toothed grin while
he rolls right to left, tow hook first, bobbing on his springs; the new ride is uncovered on
the side he's passed. 1x on both boards, in the rotation at 0.005. A separate surprise from
McQueen (#15), by the user's choice over a shared scene. Ideas not taken: towing the old ride
away with his hook, or popping up to grin.

**31. Max and Roxanne (A Goofy Movie).** Saved for later by the user, with a pixel-art
reference: [docs/references/max-and-roxanne.png](docs/references/max-and-roxanne.png) (Max in
his red hoodie, Roxanne with her long red hair, holding hands), about 30x53 each. Too tall for
64x32 as is; fits 64x64. Natural partner to Goofy (#17).

Questions: what they do (walk across hand in hand, a peek, a nod to "Stand Out"/Powerline);
one or both; where they show up; size on each board.

**33. Grogu.** Reference: [Baby_Yoda.jpg](docs/references/Baby_Yoda.jpg), 38x32: tight on
64x32 (fills the height), fits 64x64. Big ears and eyes are the whole silhouette, and green
on black reads well.

Questions: float across in his pram, or a Force-lift of the old screen; pram or no pram (the
pattern is him standing in his robe); reference for the pram.

**34. Lumiere, Cogsworth, Mrs. Potts and Chip.** Reference:
[Beauty and the Beast.jpg](<docs/references/Beauty and the Beast.jpg>), a photo of beads with
Gaston, Belle and the Beast too, about 12x20 each: fits both boards (2x on 64x64 too).
Small enough that several fit on the board at once, which suits a parade.

Questions: which characters (objects only, or Belle and the Beast); a parade, or Lumiere's
candle flames lighting the next ride; tied to Be Our Guest's screen.

**35. Boo.** Reference: [Boo.jpg](docs/references/Boo.jpg), in her purple monster costume,
28x44: too tall for 64x32 as is; fits 64x64.

Questions: her own scene, or with Mike and Sulley (one Laugh Floor visit with all three);
64x32 needs a redraw or a crop.

**36. Dug.** Reference: [Dug.jpg](docs/references/Dug.jpg), 22x27: fits both boards (2x on
64x64 too). His open-mouthed grin is the face; the "Squirrel!" head snap is a ready-made
story beat.

Questions: does a squirrel actually appear; where he shows up (no Up ride at WDW).

**37. The Seven Dwarfs.** Built: `mine_train`, on the Mine Train's screen only. A few random
dwarfs ride in their cars one screen in ten; at a wait of 15 or less all seven come every time,
and at 5 or less (or a posted 7) Snow White rides the lead car too. Lessons in CHARACTERS.md.

**38. The Evil Queen.** Reference: [Evil Queen.jpg](<docs/references/Evil Queen.jpg>), 31x38:
too tall for 64x32 as is; fits 64x64.

Questions: the apple or the mirror; a Halloween-night villain only, alongside Maleficent
(#42) and Oogie Boogie (#50), or the Mine Train too.

**39. Forky.** Built: `forky`, from [Forky.jpg](docs/references/Forky.jpg) cell for cell, 1x on
64x32 and 2x on 64x64, with a black ring round him so he stands off the old ride. His eye holes
are googly eyes (a grey ring, a black pupil that rolls as he waddles and settles looking down at
the old ride). He waddles in, TRASH! pops up (over him on 64x64, beside him on 64x32), his arms
flap, he hops, flips and dives head first through the bottom; the old screen is pulled into the
hole, nearest first, while his feet kick out of it, then they slip in.

**40. Hamm.** References: [Hamm.jpg](docs/references/Hamm.jpg), 41x31: tight on 64x32, fits
64x64; and a small Hamm on [Bullseye.jpg](docs/references/Bullseye.jpg) (fits both).

Questions: which reference; coins, or just a trot; with the other Toy Story toys (#14, #16,
#51-55).

**41. Heihei.** Reference: [hei-hei.jpg](docs/references/hei-hei.jpg), 20x42: too tall for
64x32 as is; fits 64x64. His blank stare and walking off the edge are the gag.

Questions: alone or with Pua (#46); 64x32 needs a redraw.

**42. Maleficent.** Reference: [Maleficent.jpg](docs/references/Maleficent.jpg), 29x40: too
tall for 64x32 as is; fits 64x64. Black horns on black need the lifted charcoal (the Sorcerer
Mickey fix); her green fire is the LED-friendly part.

Questions: green flames, or her staff's orb glowing; Halloween nights only.

**43. Pooh and his balloon.** Reference: [Pooh and Balloon.jpg](<docs/references/Pooh and Balloon.jpg>),
20x64 with the balloon: too tall for 64x32 as is; tight on 64x64 (exactly its height).
Floating up and off the top suits the tall, thin shape.

Decided: the pattern cell for cell on both boards (64x32 shows part of him at a time); rise,
hover and drift off with a sway; the old ride stays above his feet and the new one is uncovered
below them; 10% of his own ride's screens and a 0.5% surprise anywhere (Baymax trimmed from 1.2%
to 0.7% to stay under the 12% cap).

Built (2026-10-04): `pooh`, from the pattern in one round. The string is drawn as a line between
the balloon and his hand, so Pooh swings a beat behind the balloon and it bends. Rise and leave
are timed by distance (30 rows a second on average) and eased in and out (`smooth`): a cubic
ease-in on the way out barely moved for the first 40% and then shot off the top at 3 rows a
frame. The gold edge runs `GAP` (4) rows under his feet; right under them it sat on top of him.
The outline is a dark brown, like Tigger's. About 5.4s on 64x64, 4.3s on 64x32.

**44. Mr. and Mrs. Potato Head.** Reference: [Potato heads.jpg](<docs/references/Potato heads.jpg>),
the two heads, 65x40 together, about 32x40 each: neither board fits both as is; one at a time
fits 64x64. Small full-body ones are on [Bullseye.jpg](docs/references/Bullseye.jpg) (fit
both boards).

Questions: heads (big pattern) or full bodies (sheet); one or both; pieces popping off and
back on.

**45. Princesses (and villains).** References:
[princesses_and_Princes.jpg](docs/references/princesses_and_Princes.jpg), princesses with
their princes, about 16x22 each: fit both boards (2x on 64x64 too); and
[Princesses_and_Evil_Ladies.jpg](docs/references/Princesses_and_Evil_Ladies.jpg), princesses
and villains, about 25x35 each: too tall for 64x32 as is, fit 64x64. (`princesses.png` is a
blank image.)

Questions: one at random per showing, or a parade; tied to their own rides and restaurants;
villains on Halloween nights only.

**46. Pua.** Reference: [pua.jpg](docs/references/pua.jpg), 36x39: too tall for 64x32 as is;
fits 64x64.

Questions: alone or with Heihei (#41); 64x32 needs a redraw.

**47. Sally.** Built with Jack; see #6. Other references: [Sally.jpg](docs/references/Sally.jpg), her face, 42x47: too tall
for 64x32 as is, fits 64x64; and [Jack and sally.jpg](<docs/references/Jack and sally.jpg>)
with Jack (see #6).


**48. Sulley.** Reference: [Sulley.jpg](docs/references/Sulley.jpg), 26x33: one row too tall
for 64x32 as is (a one-row trim would fit); fits 64x64.

Questions: a roar over the screen, or with Mike (#3) and Boo (#35); his purple spots need to
stay distinct from his blue at this size.

**49. Tiana.** Reference: [Tiana.jpg](docs/references/Tiana.jpg), kissing the frog, 74x86:
fits neither board as is; it would need a redraw at about half size.

Questions: the kiss, or Tiana alone; with Ray (#22) on Tiana's Bayou Adventure.

**50. Oogie Boogie.** Reference: [Oogie Boogie.jpg](<docs/references/Oogie Boogie.jpg>), 44x50:
too tall for 64x32 as is; fits 64x64.

Questions: bugs spilling out, or a looming peek; Halloween nights only, with Jack (#6).

**51. Woody.** References: [woody.jpg](docs/references/woody.jpg), 32x50: too tall for 64x32
as is, fits 64x64; and a small Woody on [Bullseye.jpg](docs/references/Bullseye.jpg) (fits
both).

Questions: riding Bullseye (#54) or on his own; which reference.

**52. Jessie.** References: [jessie.jpg](docs/references/jessie.jpg), 31x51: too tall for
64x32 as is, fits 64x64; and a small Jessie on [Bullseye.jpg](docs/references/Bullseye.jpg)
(fits both).

Questions: lasso, or riding Bullseye too; which reference.

**53. Zero.** Built with Jack; see #6. Other references: [Zero.jpg](docs/references/Zero.jpg), 38x34: too tall for 64x32 as
is, fits 64x64; and [zero2.jpg](docs/references/zero2.jpg), a photo of embroidery, flying,
about 68x72: fits neither board as is. A white ghost dog with a glowing nose is made for LEDs.


**54. Bullseye.** Reference: [Bullseye.jpg](docs/references/Bullseye.jpg), a sheet of about
twenty Toy Story characters (Woody, Buzz, the Potato Heads, Slinky, Rex, Hamm, Bo Peep and
her sheep, Forky, the Aliens, RC, Zurg, Wheezy, Jessie, Stinky Pete and more); Bullseye is
26x28, and all of them fit both boards (2x on 64x64 too).

Questions: alone, or with Woody (#51) riding; whether this sheet becomes the source for the
other Toy Story entries.

**55. RC.** References: [RC-NotPixels.webp](docs/references/RC-NotPixels.webp), a photo of an
enamel pin, not pixel art, so it needs tracing (keep the bold shapes: the lime body, blue
flames, red hubs, big black tyres, as with the Falcon); and a small RC on
[Bullseye.jpg](docs/references/Bullseye.jpg) (fits both boards).

Questions: traced from the pin, or the sheet's; does anyone ride him; a drive-by like
McQueen (#15).

**56. Bluey and Bingo as the Grannies (Janet and Rita).** Reference:
[bluey_bingo_grannies.png](docs/references/bluey_bingo_grannies.png), a grid pattern: Bingo in
the purple gown with curlers (with her walking frame) about 26x31, Bluey in the red gown about
21x38. The pair is about 50 wide.

Decided (2026-10-03):
- A ride-screen surprise (`SURPRISES`).
- They shuffle slowly left to right side by side with a little bob, and the new screen is
  revealed behind them (a wipe).
- One pattern about 24 rows tall, 1x on both boards (`SCALE = 1`), redrawn from the reference
  (too tall to copy cell for cell on 64x32).

**57. Bluey and Bingo, Keepy Uppy.** References: [bingo.png](docs/references/bingo.png), a
grid pattern of Bingo waving, about 40x54; [bluey_beads.png](docs/references/bluey_beads.png),
a photo of beads (no grid; slow to transcribe), about 30x36.

Decided (2026-10-03):
- A ride-screen surprise (`SURPRISES`).
- The balloon floats in; they run in and take turns hitting it up a few times while moving
  across, then chase it off the far edge. The new screen is revealed behind them (a wipe).
- One pattern of each about 24 rows tall, 1x on both boards (`SCALE = 1`), redrawn from the
  references.

Built (2026-10-03), changed from the plan above while building:
- **Grannies** (`grannies`, 0.005): 64x64 got the pattern cell for cell; only 64x32 is the
  24-row redraw. Bluey is mirrored to face the way they walk. A steady pixel a frame was "way too
  fast for granny": Bingo now goes a step at a time (the walker lifts and plants a step ahead,
  her sleeve stretching after it, then she shuffles up), about 10 px/s, 10.4s to cross, with
  `hold_after_s` keeping the ride up 3s after.
- **Keepy Uppy** (`keepy_uppy`, 0.001, so nobody else was trimmed; `SURPRISES` is 11.9%): they
  play in the middle rather than while crossing, facing each other, then turn and chase it off.
  44 rows with arms out was 69 wide, so 64x64 has Bluey bead for bead from the photo (28x32) and
  Bingo shrunk from her pattern (22x29); 64x32 has both redrawn about 20 rows. The balloon is red,
  8x8 on 64x32 and 14x14 on 64x64 (tripled from the first mock, then 70% of that).

**58. Lightsaber clash.** Built (2026-10-05): `saber_clash`, blades only, no hilts or wielders.
- A `RIDE_VISITORS` entry, 1 in 10 on Rise of the Resistance, Smugglers Run and Star Tours;
  never in `SURPRISES`. On the Galaxy's Edge rides the Falcon rolls first, so between them
  about 1 screen in 5 gets a Star Wars visitor there.
- Red swings in from the bottom-left and blue from the bottom-right, each pivoting just off
  its corner, and they lock in an X at the centre of the old ride. They shiver there while two
  bursts of white and yellow sparks fly from the crossing, then swing upright side by side and
  sweep apart, red left and blue right, with the new ride between them (like TRON's trails).
- Solid blades with no white core, 2px on 64x32 and 3px on 64x64, humming between two shades.
- Takes the old screen (`wants_prev`), so the clash plays over the old ride, not over black.

**59. Luke vs Darth Vader.** Built (2026-10-05): `saber_duel`, from
[skywalker-saber.jpg](docs/references/skywalker-saber.jpg) and
[Darth-Vader-2.jpg](docs/references/Darth-Vader-2.jpg) cell for cell, 1x on both boards
(doubled, the pair is wider than 64x64).
- Its own `RIDE_VISITORS` roll, 1 in 10 on the same three rides as the clash (#58), so with
  the Falcon about a quarter of those screens on Galaxy's Edge get a Star Wars visitor.
- The blades are taken out of the art and drawn from each hilt so they can swing; Vader's greys
  are lifted so he doesn't vanish into the black of the board. Nothing else changed from the art.
- They walk in, trade three blows (Luke, Vader, Luke) with a spark where each lands, lock blades
  with sparks pouring off, and are thrown apart, blades upright, as the new ride opens between them.
- Then (2026-10-05, "move the hands to make it more lifelike"): the fists and hilts came out of
  the art too. Each front arm is drawn from the shoulder (a 2px sleeve, outlined, Luke's skin fist,
  Vader's glove with its highlight) and swings with the blade: fist up by the head on the raise,
  out in front and low on the cut. The attacker leans a pixel into the blow, the defender is
  knocked back a pixel when it lands, and Vader's cape swings out and back. The longer reach
  meant standing them further apart and lowering the guard so the blades still cross.
- Luke then got his second arm back (2026-10-06), as a free arm rather than a second hand on the
  hilt (two-handed was tried; the user didn't want it): held out behind him for balance, like a
  fencer, tucked lower as he raises his blade and flung back as he cuts.
- Vader stretched to Luke's 24 rows (two helmet rows, two body rows and a helmet column each side
  doubled). Luke's tunic was tidied: the arms' outlines had been cutting black lines into it, so
  they're only drawn off the body now, and his old left sleeve and the hands' leftovers came out,
  with his cream trousers showing above the boots as in the reference.

**60-62. More duels** (2026-10-06). The duel roll (`saber_duel`, still one 1 in 10 roll) now
picks a matchup at random from `saber_duel.DUELS`; each is also its own transition for
`force_surprise` (`saber_duel_luke`, `_obiwan`, `_yoda`). Matched to Luke and Vader's size, as asked.
- **Obi-Wan** (`ObiWanDuelReveal`): from `hans- solo.jpg` cell for cell, already 24 rows. Both his
  arms and the blade over his head came out; the blade hid the top of his head, so three rows of
  hair are filled in.
- **Yoda** (`YodaDuelReveal`): from `Yoda-saber.jpg`, arms and blade out.
  Kept small (21 rows), as asked; he hops in and leaps into each of his attacks. Green blade.
  First built mirrored (to put his saber arm on Vader's side), which turned his head away from
  Vader; the user caught it, along with a far ear too small to see. Now unmirrored (his head is
  turned toward Vader in the reference, and the arms are drawn in code anyway), far ear lengthened,
  both pupils toward Vader, and the reference's white background cleared from round his head.
- **Rey vs Kylo Ren** (`KyloReyDuelReveal`): both from KidKinobi on DeviantArt
  ([rey-saber.jpg](docs/references/rey-saber.jpg), picked by the user from two candidates, and
  [kylo-saber.jpg](docs/references/kylo-saber.jpg), the same artist, used instead of the bead
  sheet's big-headed Kylo so the two match), both 24 rows. Rey keeps her yellow blade (the user's
  choice) and her other arm as drawn; Kylo is mirrored, his greys lifted, his red blade with a
  crossguard and crackling edges.
- **Next, from the Megamalgamation sheet** (Chris Bringhurst, the user's image; not saved yet): the
  same Mega Man style as Luke and Obi-Wan, about 24 cells tall but 2 px a cell in a blurry JPEG, so
  each needs cleaning up. Suggested: Obi-Wan vs Darth Maul (double-bladed), Anakin vs Obi-Wan
  (Mustafar), Mace Windu vs Palpatine (purple blade); General Grievous (four blades) or Yoda vs
  Count Dooku as options. Waiting for the user's pick.

### Ideas for using them

- **A character per park** for the park title reveal (today `PARK_REVEALS` plays Tinker Bell
  or Buzz for every park): Magic Kingdom TRON / Ghosts, EPCOT Olaf / Figment, Hollywood
  Studios WALL-E / Mike / Luxo / Pixar Ball / Army Men, Animal Kingdom banshee / Dumbo.
- **Special-event tie-ins:** Jack, Sally and Zero on their party-night meet (built), Santa Goofy or a
  Santa-hat Mickey on Christmas party and Jollywood nights (`utils/special_events.py`).

## ~~2. Tower of Terror: a longer landmark scene, especially on 64x32~~ Done

Was 3.5s on both boards, with the car landing 0.3s before the end on 64x32. Now 4.5s on
64x64 and 5.5s on 64x32 (`SHORT_SCREEN_S`), with a slower 1.2s tilt, at least 0.5s between
beats, and a 0.8s hold after the car lands on both boards.

## 3. Characters show up more on their own ride

First cut built for the Falcon: `disney.RIDE_VISITORS` maps a visitor to pieces of ride
names and a chance, rolled before the general `SURPRISES`. Extending it to the characters
below is now just entries in that map (plus settling a boost versus only-on-their-ride).
Mike is the first to be in both: the rotation, and 1 in 10 on the Laugh Floor.

A character-to-ride map next to `SURPRISES` in `disney.py`, with a boosted chance when the
ride on screen matches. For example: Buzz on Buzz Lightyear's Space Ranger Spin, Dumbo on
Dumbo the Flying Elephant, Figment on Journey Into Imagination with Figment, Slinky on
Slinky Dog Dash, Genie on The Magic Carpets of Aladdin, Mickey on Mickey & Minnie's Runaway
Railway, WALL-E on (to decide), and each new character on theirs (TRON, Olaf, Mike, Remy,
the Ghosts, the banshee, Nemo, the Pixar Ball and Army Men on Toy Story Land rides). Rex is
built as a Toy Story Land visitor.

Trigger idea: Lightning McQueen more likely on the rides with the longest waits or a
Lightning Lane price.

To settle first:
- How big a boost (for example 25% on their own ride).
- Whether characters that aren't in the random rotation today (Buzz, Tink, Figment, Dumbo,
  Mickey) should appear only on their own rides.
- Which character goes with which ride where it isn't obvious.

## ~~4. Halloween pumpkin: start fading in during the wipe~~ Done

Both pumpkins set `PLAYS_UNDER_WIPE`, so their clock starts with the wipe: the candle catches
while the wipe is still uncovering them, and the scene gets back the 0.65s the wipe used to
eat, as a longer hold on the party's hours at the end. Other landmarks can opt in the same way
if it suits them.

## ~~5. Fix the EPCOT ball (Spaceship Earth landmark)~~ Done

It read as a grey ball on legs: stripes that rendered as noise, and a glint for motion.
Redrawn from the user's photo, at night under the Beacons of Magic: a triangle lattice
wrapped onto the sphere (facets shrink toward the rim, alternating lit and shaded faces) in
EPCOT's purples, blues, teals and pinks, on slab legs drawn behind it so it stays a perfect
sphere. It's big and low on both boards (the legs just peek out; tall legs read as a water
tower). The story is Tinker Bell's: she spirals up the dark sphere in three even laps,
hidden behind it and in front, and each facet lights as her pixie dust passes, then she lands
on its shoulder while the colours roll around it. 4.5s, playing under the wipe.

## 6. Fix the Tree of Life landmark

`TreeOfLifeLandmark` reads as a generic tree (a big oak, or a head of broccoli), not the Tree
of Life. Rendered on both boards:
- The canopy is one flat green mass; the real tree's canopy is broad and layered, many small
  clumps in several greens over a spreading, horizontal branch structure.
- The trunk is a smooth peach cone. What identifies the real tree is its massive, twisted,
  carved trunk (the animal carvings) and the huge gnarled roots flaring out at the base.
- On 64x32 the canopy squashes into a thin green band on top of a peach mound.
- The fireflies are too small and sparse to register as motion, so nothing really happens.

Questions to settle first, with a reference photo:
- Day or night? At night "Tree of Life Awakenings" projects glowing animals across the
  trunk: an animal glowing into life on the trunk could be the story beat and would be
  unmistakable at this size.
- How to suggest the carvings: a few bold animal silhouettes in lighter bark, twisting
  ridges up the trunk, or leave them to the night projection?
- Trunk color: the real bark is a pale grey-tan with deep shadowed grooves, not a flat peach.
- 64x32 composition: the full tree squashed, a crop on the trunk and lower canopy, or a tilt
  up like the Tower of Terror?


## ~~7. Redraw Stitch~~ Done

The old peek was replaced by `stitch_surf`, in the `SURPRISES` rotation at 0.005: from the bead
pattern [stitch.jpg](docs/references/stitch.jpg) (35x41: fits 64x64 as is, too tall for 64x32),
standing, facing us, he surfs a red board down the face of a teal wave whose crest washes the
old ride away. On 64x32 he sits on the board, from
[sitting_stitch.jpg](docs/references/sitting_stitch.jpg) (26x25: fits both boards as is).
Two other scenes from the user's profile pixel art were built and scrapped: popping up to chomp
twice, and eating the old ride letter by letter.

## ~~8. Fix Ralph showing the new screen through the old one~~ Done

`RalphReveal` painted only the old screen's lit pixels while he rose, and `show_screen` has
already drawn the new screen underneath, so the new ride showed through wherever the old
screen was dark until he smashed it. He now paints every pixel of it, black included, until
the punch, like the Army Men and the Falcon, and he's a case in
`test_new_screen_never_shows_through_the_old_screens_dark_pixels`.

Redrawn from [Ralph.jpg](docs/references/Ralph.jpg), copied cell for cell at 1x on both boards
(25x34 with its outline; on 64x32 the outline rows under his feet and at the tip of his hair hang
off the board). He now stomps in from the left over the old ride, raises both fists (over his
head on 64x64, beside his face on 64x32, where there's no room overhead) and slams them down;
the ride shatters and falls as before, and he stomps off the right. Built but still not in
the rotation.

## 9. Switch to a no-selling license

Today the project is GPLv3 (`LICENSE.md`): anyone may sell it, but must share the source under
GPLv3 too. Joel wants a license that forbids selling (PolyForm Noncommercial 1.0.0 is the
software one). The GPL won't allow adding that restriction to code inherited from
MLB-LED-Scoreboard (GPLv3), so first rewrite what came from it, then relicense:
- Audit what's still inherited: `LLL-install.sh`, the CLI flags in `cli.py:arguments()` (now laid out as upstream's),
  the README's install/flags sections, anything else from the 2025-03-14 import (`36625d7`).
- Rewrite those parts from scratch (not edited copies).
- Swap `LICENSE.md` for PolyForm Noncommercial and update the README's Licensing section.
  It's then "source-available", not open source.

## ~~10. Luxo's searchlight story is too short on the board~~ Done

Seen on a real board: in `luxo_ball`'s "light" story the ride screen ended before the wait time
could be read. `run_frames` steps a scene by frame number but stopped the screen by the clock,
so a board below `FPS` played the 5.8s search in slow motion and the 8s cut landed while the board
was still dark. The light story is also the costliest frame of the three (an angle per pixel for
the beam, the whole board painted dark), about 9x the others.

Fixed: the light story holds the ride at its first frame until Luxo and the ball have left (the
wait counts up after them) and sets `hold_after_s` (3s). `run_frames` takes `play_s`: a reveal
that sets `hold_after_s` always plays in full, and a board that fell behind during it gets the
time back after it, so Rex, the Mine Train, the Grannies and the Aliens can't be cut short either.
Not done: making the light story's frames cheaper, or making every scene follow the clock
(a slow board would drop frames instead of running in slow motion).

## 11. Move the surprise maps out of `disney.py`

`disney.py` carries who appears where (`PARK_REVEALS`, `SURPRISES`, `RIDE_VISITORS`, the long
comment describing each visitor, `_mine_train_for_wait`), and it grows with every character.
Move them into their own module (for example `display/animation/visitors.py`), so adding a
character touches that file and `TRANSITIONS`, not the main loop.

To settle first:
- What moves: just the three maps and their comment, or the picking too (`_surprise`,
  `_ride_visitor`, `_mine_train_for_wait`, `forced_surprise`), so `disney.py` only asks "who's
  next?".
- Where it lives: next to `TRANSITIONS` under `display/animation/`, or at the top level.
- Keep the tests that hold it (the cap, each visitor's slice, who keeps to their own rides)
  passing unchanged apart from imports; the cap test is the guard that matters.

## ~~12. Analyse new reference images automatically~~ Done

Every image dropped into `docs/references/` needs a row in its README table; until now that was
done by hand when someone remembered (eight images had none).

Done:
- `tests/tools/test_analyze_reference.py` fails, naming the file, while any image there has no
  row (and while a row links an image that's gone).
- `tools/analyze_reference.py <image>` runs the sprite editor's Pattern-mode core under Node (one
  detection for both), and prints a draft row: size, fits 64x32 / 64x64 / 2x, how the editor reads
  it, and its colours. `--art` adds the sprite rows and palette to paste (decided with the user,
  2026-10-04); `--box` measures one character on a sheet, `--lines` is Grid lines only. With no
  believable grid (no repeat, or cells more than 15% off square, which is how a whole sheet of
  charts or a pin photo reads) the row says Needs tracing.
- A sheet gets **one row per character**, each measured with `--box` (decided with the user,
  2026-10-04): starwars.jpg has nine.
- `.claude/settings.json` (now checked in; personal permissions moved to the ignored
  `settings.local.json`) has a SessionStart hook that runs `--missing`, so a new session lists
  images with no row and measures them first.

Not done: the sheets added before the one-row-per-character rule (Bullseye.jpg, the princess
sheets, Beauty and the Beast.jpg, toy_story_4_sheet.png, TS_beads.jpg, dwarfs.jpg) still have one
row each. Split them when one is next used. Lessons for CHARACTERS.md still come from building.
