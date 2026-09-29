# Roadmap

Ideas and planned work for the board, in no fixed order. Nothing here is built yet unless it
says so. Before drawing any character or landmark, read [display/CHARACTERS.md](display/CHARACTERS.md)
and settle the open design questions first (ideally from a reference image): every entry
below lists the questions still to ask.

## 1. Characters to create

Built so far: Tinker Bell, Buzz, Figment, Dumbo, Stitch, Ralph, Sorcerer Mickey, Slinky,
Baymax, Genie, WALL-E (the side-view baler `walle_side` plays; the three-quarter view
`walle` is kept, out of the rotation), the Green Army Men (`army_men`), the Millennium
Falcon (`falcon`), Mike Wazowski (`mike`), the TRON light cycles (`tron`) and Olaf (`olaf`).

Put a ✅ in the Done column when a character ships.

| # | Done | Character | Park / ride | Signature motion | Mechanic |
|---|---|---|---|---|---|
| 1 | ✅ | TRON light cycle | MK: TRON Lightcycle Run | a blue and a red cycle race across, top and bottom; their light trails are the wipe | Fly-by |
| 2 | ✅ | Olaf | EPCOT: Frozen Ever After | stacks himself out of snowballs while it snows, waves, and walks off | Standalone, drawn in code with a hand-drawn head |
| 3 | ✅ | Mike Wazowski | MK: Monsters, Inc. Laugh Floor | pops up, blinks, looks around, grins, then scares | Peek, drawn in code like Baymax |
| 4 | | Luxo Jr. lamp | DHS: Pixar Place | hops in with a squash and stretch; its light cone reveals (could pair with #13) | Standalone |
| 5 | | Hitchhiking Ghosts | MK: Haunted Mansion | three see-through ghosts float across | Fly-by |
| 6 | | Jack Skellington | Halloween party nights | white skull close-up peeks up | Peek |
| 7 | | Santa Goofy / Santa-hat Mickey | Christmas party, Jollywood Nights | red-and-white holiday cameo | TBD |
| 8 | | Remy | EPCOT: Remy's Ratatouille Adventure | scurries along the bottom | Fly-by |
| 9 | | Na'vi banshee | AK: Avatar Flight of Passage | glowing blue and purple swoop | Fly-by |
| 10 | | Nemo and a school of fish | EPCOT: The Seas with Nemo & Friends | a school of fish swims across as the wipe | Fly-by |
| 11 | | Steamboat Willie Mickey | MK | whistling at the wheel | TBD |
| 12 | | Monorail | all of Walt Disney World | glides across as a band of color | Fly-by |
| 13 | | Pixar Ball | DHS: Pixar Place, Toy Story Land | bounces across in 3-4 hops, uncovering the next ride | Fly-by (bounce) |
| 14 | ✅ | Green Army Men | DHS: Toy Story Land | parachute in, land, chutes slump, hop off in step on their bases | New: top-down drop reveal |
| 15 | | Lightning McQueen | DHS / MK Cars area (status to confirm) | zooms in, "Ka-chow" stop, peels out leaving speed streaks | Fly-by (drive-by) |
| 16 | | Rex | DHS: Toy Story Land | stomps in, tail-swipes the old screen off the board, looks sheepish and runs | Wreck (`wants_prev`) |
| 17 | | Goofy | MK: The Barnstormer | flies his biplane across the board | Fly-by |
| 18 | | Little Green Men (Aliens) | DHS: Toy Story Mania!, Alien Swirling Saucers | "the claw" descends from the top, grabs the old screen and hauls it away while three aliens go "Ooooh" | New: top-down grab (destroys old screen) |
| 19 | | R2-D2 | DHS: Galaxy's Edge | rolls across on his treads, dome swivelling, light blinking | Fly-by |
| 20 | ✅ | Millennium Falcon | DHS: Smugglers Run, Rise of the Resistance | drops out of hyperspace, cruises, then jumps to lightspeed; the old screen streaks away and a flash fades to the new ride | Standalone (`wants_prev` + `wants_new`) |
| 21 | | Baby Groot | EPCOT: Guardians: Cosmic Rewind | sprouts from the bottom edge, grows like Baymax inflates, then dances | Peek (procedural, not fixed art) |
| 22 | | Ray the firefly | MK: Tiana's Bayou Adventure | glowing firefly wanders across, leaving a light trail | Fly-by |
| 23 | | Tigger | MK: Many Adventures of Winnie the Pooh | bounces across on his tail | Fly-by (bounce) |
| 24 | | Jungle Cruise hippo | MK: Jungle Cruise | eyes and ears surface from the bottom, wiggles its ears, sinks back down | Peek |
| 25 | | Donald Duck | EPCOT: Gran Fiesta Tour | tantrum knocks the old screen to pieces, feathers flying | Wreck (`wants_prev`) |
| 26 | | Yeti | AK: Expedition Everest | huge dark silhouette looms up behind the screen, eyes glowing | Peek |
| 27 | | Simba on Pride Rock | AK | held up against an orange sunrise gradient | Landmark/scene, not a ride transition |
| 28 | | Madame Leota | MK: Haunted Mansion | green glowing head appears in a crystal ball | Peek; pairs with #5 for Halloween |
| 29 | | Cinderella's pumpkin coach | MK | a pumpkin bursts into sparkles and becomes the coach | Assemble |
| 30 | | Chip 'n' Dale | MK / DHS (various) | two heads peek up side by side | Peek |

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

**4. Luxo Jr.** Lamp and ball are simple geometry, and the lamp's light cone is built for
LEDs. Hops in with a squash and stretch; its light cone reveals the next screen. Could be
folded into the Pixar Ball (#13) as one scene: the lamp hops in and bats the ball.

**5. Hitchhiking Ghosts.** Three ghostly silhouettes drawn see-through (additively, like
Genie's smoke) over the screen, floating across with a faint bob. Fits the Halloween party
season.

**6. Jack Skellington (Halloween party nights).** A white skull close-up with black eyes and
a stitched grin: a high-contrast face that reads at any size. Peek mechanic.

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

Questions: bounce-by alone or with Luxo; regular chance or Pixar rides only; 1x on both
boards or 2x on 64x64; reference image.

**~~14. Green Army Men.~~ Done** (`ArmyMenReveal`, `"army_men"` in `SURPRISES` at 0.015,
`display/animation.py`). The parachutes are what make them work: a canopy is a big, simple
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

Questions: confirm Cars at Walt Disney World first; eyes in profile or slight 3/4; stop
mid-board or blast straight through; when he shows up; reference image.

**16. Rex.** A strong silhouette for the board: a big head with an open jaw, tiny arms, a
long tail, and a bright yellow-green body that stands out on black. He's the second
character to use the wreck mechanic (`wants_prev`, like Ralph), so on a Pi the old screen
has to be captured through `capture_screen()`.

Decided:
- Motion: he stomps in from one edge over the old screen, stops mid-board and turns, and
  one big tail swing clears the screen.
- Pixels: the tail bats them off sideways, in the direction of the swing, and they tumble
  off the edge under gravity. That keeps it distinct from Ralph's shatter-and-fall.
- Personality: after the swipe he glances back at the mess, looks sheepish and scurries
  off with his arms flailing.
- Framing: full body in profile so the tail and tiny arms show, with the head turned
  three-quarters so both eyes and the open mouth read (the face lesson from Slinky, see
  CHARACTERS.md). Roughly 30x24 cells.
- Frequency: joins the regular `SURPRISES` rotation.

Still open:
- Reference image: the user is sharing one. Don't draw until it's in.
- Size on 64x64: render 1x and 2x and pick from the renders. 2x likely fills the board and
  leaves the swing no room.
- Colour: his green must stay distinct from the Army Men's (#14) if both appear.
- Timing: with the entrance, swipe and sheepish exit it's probably 3-4s; time each beat
  once it's drawn.
- Chance in `SURPRISES`, and whether he gets a boosted chance on Toy Story Land rides (#3
  below).

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

Still open:
- Full body in the plane: the framing chosen was full body, but a cockpit hides his legs.
  Choices are standing up in the cockpit, sitting on the wing, or just his upper body with
  long ears flapping in the wind.
- Flight path and extras: straight across, a wobble, or a loop; a smoke trail or a banner
  as the wipe line; the Goofy holler as he goes by.
- Ears and hat: his black ears need a lifted charcoal to show on black (the Sorcerer Mickey
  fix). The green hat and the plane's colours must differ from each other.
- Size on 64x64, and whether the plane stays 1x like Genie's lamp.
- Reference image, and his chance in `SURPRISES`.

**18. Little Green Men (Aliens).** A new mechanic: "the claw" descends from the top edge,
grabs the old screen bodily and hauls it back up out of frame, while three identical
squeaky-clean-green aliens (antennae, three eyes, folded hands) look up and go "Ooooh."
Simple shape, saturated color, and the claw itself is just a few lines and a grabber — easy
to draw and instantly recognizable from the ride/film. Distinct from Ralph/Rex/Donald's
wreck mechanic since nothing shatters; the screen is lifted whole.

Questions: one alien or three; does the claw stay on screen after grabbing, or exit with
the old screen; reference image; chance in `SURPRISES`.

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

Questions: how many bounces to cross the board; does he say anything ("T-I-double-Guh-er");
1x or 2x on 64x64; reference image.

**24. Jungle Cruise hippo.** Just eyes, ears and nostrils surfacing from the bottom edge —
the classic "hippo submerged in water" gag, and it needs almost no detail to read, similar
to Mike Wazowski's one-eye simplicity. Pairs naturally with a wavy blue foreground band.

Questions: does it yawn/roar before sinking, or just wiggle its ears; add a water-ripple
foreground band across every screen it peeks over, or keep the board plain; reference image.

**25. Donald Duck.** A tantrum wreck, like Ralph and Rex but with his own signature: he
stomps in place, and the old screen's pixels fly apart with a scatter of white feathers.
Bright blue-and-white with an orange bill separates cleanly from the other wreck
characters' palettes (Ralph's reds, Rex's greens).

Questions: does he quack (a speech-bubble squiggle) mid-tantrum; feather color/count; how
his tantrum differs physically from Ralph's punch and Rex's tail swipe so the three don't
feel like reskins of one animation; reference image.

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

Questions: worth attempting given the two-small-heads risk, or drop; if attempted, which
one leads/reacts (Chip's black nose vs. Dale's red nose and buck teeth are the only real
differentiator at this size); reference image.

### Ideas for using them

- **A character per park** for the park title reveal (today `PARK_REVEALS` plays Tinker Bell
  or Buzz for every park): Magic Kingdom TRON / Ghosts, EPCOT Olaf / Figment, Hollywood
  Studios WALL-E / Mike / Luxo / Pixar Ball / Army Men, Animal Kingdom banshee / Dumbo.
- **Special-event tie-ins:** Jack Skellington on Halloween party nights, Santa Goofy or a
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
the Ghosts, the banshee, Nemo, the Pixar Ball, Army Men and Rex on Toy Story Land rides).

Trigger idea: Lightning McQueen more likely on the rides with the longest waits or a
Lightning Lane price.

To settle first:
- How big a boost (for example 25% on their own ride).
- Whether characters that aren't in the random rotation today (Buzz, Tink, Figment, Dumbo,
  Stitch, Mickey, Ralph) should appear only on their own rides.
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


## 7. Redraw Stitch

`StitchReveal` (the peek) doesn't read as Stitch. Rendered on both boards at full rise:
- The ears are two tall purple spikes pointing straight up, which reads as a rabbit or a
  bat. His real ears are huge and swept out sideways (often drooping), blue with pink
  inside, and the notch isn't visible.
- The head is narrow and tall. His real head is very wide and flat, wider than it is tall,
  and that width is half his silhouette.
- The eyes come out as one dark band with two white dots, like sunglasses. His big dark
  eyes are the identity, but they need to be separate shapes that differ from the fur and
  the outline (see "Eyes" in CHARACTERS.md).
- The nose is dark navy on mid-blue fur and gets lost.
- The grin is cut off by the bottom edge: at full rise (`rise_frac` 0.88) only a sliver of
  mouth and teeth shows on either board, so his face never finishes.
- The look left and right is just the white glint moving a pixel; it barely registers.

Questions to settle first, with a reference image:
- Framing: a wide head-only close-up (ears out to the sides), or head plus shoulders and
  his little arms gripping the bottom edge?
- Ears: straight out to the sides, drooped, or one of each? Keep the notch?
- Expression: the big mischievous grin, the tongue out, or a neutral face that breaks into
  a grin?
- Motion: keep the peek with a stronger look around (whole head turns, ears swivel), or
  something more Stitch, like an ear flick, a lick, or a sneaky pop-up that ducks when
  spotted?
- Size: 1x or 2x on 64x64 (the ears' width decides it), and whether he joins the
  `SURPRISES` rotation once redrawn (he's built but not in it today).

## 8. Fix Ralph showing the new screen through the old one

`RalphReveal` paints only the old screen's lit pixels while he rises, but `show_screen` has
already drawn the new screen underneath, so the new ride shows through wherever the old
screen was dark until he smashes it. The Army Men and Falcon paint every pixel of the old
screen for this reason; Ralph needs the same (`test_new_screen_never_shows_through_the_old_screens_dark_pixels`
can take him as another case).
