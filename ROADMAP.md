# Roadmap

Ideas and planned work for the board, in no fixed order. Nothing here is built yet unless it
says so. Before drawing any character or landmark, read [display/CHARACTERS.md](display/CHARACTERS.md)
and settle the open design questions first (ideally from a reference image): every entry
below lists the questions still to ask.

## 1. Characters to create

Built so far: Tinker Bell, Buzz, Figment, Dumbo, Stitch, Ralph, Sorcerer Mickey, Slinky,
Baymax, Genie, and WALL-E (the side-view baler `walle_side` plays; the three-quarter view
`walle` is kept, out of the rotation).

| # | Character | Park / ride | Signature motion | Mechanic |
|---|---|---|---|---|
| 1 | TRON light cycle | MK: TRON Lightcycle Run | races across; its light trail is the wipe | Fly-by |
| 2 | Olaf | EPCOT: Frozen Ever After | snowballs stack into Olaf, or he belly-slides across | Assemble / standalone |
| 3 | Mike Wazowski | DHS: Monsters, Inc. | pops up from the bottom and blinks his one eye | Peek |
| 4 | Luxo Jr. lamp | DHS: Pixar Place | hops in with a squash and stretch; its light cone reveals (could pair with #13) | Standalone |
| 5 | Hitchhiking Ghosts | MK: Haunted Mansion | three see-through ghosts float across | Fly-by |
| 6 | Jack Skellington | Halloween party nights | white skull close-up peeks up | Peek |
| 7 | Santa Goofy / Santa-hat Mickey | Christmas party, Jollywood Nights | red-and-white holiday cameo | TBD |
| 8 | Remy | EPCOT: Remy's Ratatouille Adventure | scurries along the bottom | Fly-by |
| 9 | Na'vi banshee | AK: Avatar Flight of Passage | glowing blue and purple swoop | Fly-by |
| 10 | Nemo and a school of fish | EPCOT: The Seas with Nemo & Friends | a school of fish swims across as the wipe | Fly-by |
| 11 | Steamboat Willie Mickey | MK | whistling at the wheel | TBD |
| 12 | Monorail | all of Walt Disney World | glides across as a band of color | Fly-by |
| 13 | Pixar Ball | DHS: Pixar Place, Toy Story Land | bounces across in 3-4 hops, uncovering the next ride | Fly-by (bounce) |
| 14 | Green Army Men | DHS: Toy Story Land | parachute in, land, chutes collapse, march off in step | New: top-down drop reveal |
| 15 | Lightning McQueen | DHS / MK Cars area (status to confirm) | zooms in, "Ka-chow" stop, peels out leaving speed streaks | Fly-by (drive-by) |
| 16 | Rex | DHS: Toy Story Land | stomps in, tail-swipes the old screen off the board, looks sheepish and runs | Wreck (`wants_prev`) |

### Notes per character

**1. TRON light cycle.** The best match for an LED board: neon blue on black, and a light
cycle is just a wedge with a glowing trail. The trail becomes the wipe line; it could leave
the trail as a glowing border for a beat before it fades.

**2. Olaf.** White stacked circles, a carrot nose and twig arms: simple shapes that can be
drawn procedurally, the way Baymax is (the best-performing character so far). Either
snowballs roll in and stack into Olaf, who waves, or he slides across on his belly.

**3. Mike Wazowski.** A green circle with one huge eye: the simplest face there is, and
unmistakable. Pops up from the bottom edge and blinks, like Stitch's peek.

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

**14. Green Army Men.** The parachutes are what make them work: on their own the soldiers
would be tiny green figures that are hard to make out, but a canopy is a big, simple shape
that reads instantly. Bright toy green reads well on black; each soldier needs only about
5x8 LEDs (helmet, body, the classic wide-legged stance). Canopies are a pale half-dome
about 9-11 wide with lines down to the soldier; three at staggered heights and sizes give
depth. Motion: a parachute drop from the top edge, canopies swaying gently side to side,
like Dumbo's ear flaps. As a transition it's a new mechanic nobody else uses, a top-down
reveal: the next ride is uncovered behind them from the top as they descend. They land, the
chutes collapse, and they march off the edge in step (the Toy Story films have them
parachute in on a mission). Pairs with the Pixar Ball: both are Toy Story Land, giving its
rides (Toy Story Mania!, Slinky Dog Dash, Alien Swirling Saucers) two characters; the Green
Army Drum Corps performs there too.

Questions: how many soldiers; march off, or salute and stay; chute color (plain white or the
film's); 1x on both boards; reference image.

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

## 5. Fix the EPCOT ball (Spaceship Earth landmark)

`SpaceshipEarthLandmark` reads as a grey ball on legs. Rendered on both boards:
- The facet pattern comes out as uniform grey noise, not the triangles that make the sphere
  recognisable; fewer, larger, bolder facets would read better.
- The only motion is a glint sweeping across the panels: nothing happens.
- On 64x32 it shrinks to a small ball with stubby legs in the middle of an empty board.

Questions to settle first, with a reference photo (also in CHARACTERS.md):
- Day or night? At night the sphere is lit in changing colors ("Beacons of Magic"), which
  could be the motion and would stand out far more than grey.
- What identifies it at this size: a bold triangle pattern, the tripod legs, the EPCOT
  entrance sign or fountain, or the silhouette alone?
- One story beat: the lights coming on, a color wave around the sphere, fireworks behind it,
  a monorail passing in front (ties in with #12 in the character list)?
- 64x32 composition: shrink, crop, or tilt up like the Tower of Terror?

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

