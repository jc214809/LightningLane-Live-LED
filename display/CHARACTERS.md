# Drawing characters for the LED board

Notes from building the characters in `display/animation/` (one file per character under
`characters/`). Most of these were learned the hard way — by rendering something, looking at it, and finding it
unrecognizable. Read this before adding a character.

## The one rule that matters most: render it and look at it

Every character in this file took 3-6 rounds of *draw it, render it to a PNG, actually
look at the image, fix what's wrong*. Not one of them was right on the first try, and
the failures were never subtle — they were "this is a purple blob" or "his eyes look
like holes punched through his head". You cannot tell from reading the ASCII art
whether it will read as the character. You have to look.

The harness is small. Capture pixels with a stand-in canvas, draw each one as a
circle with PIL at ~10px per LED, tile a few timesteps into one sheet, and open it:

```python
class C:
    def __init__(s, w, h): s.width, s.height, s.px = w, h, {}
    def SetPixel(s, x, y, r, g, b): s.px[(int(x), int(y))] = (r, g, b)
    def Clear(s): s.px = {}
```

Always put a non-black stand-in "screen" behind the character too, or you won't notice
that your reveal is punching holes in the background (see *Blending*, below).

## Size

**Bigger than feels right.** Figment was first drawn at 8x6 and read as a purple blob
with two orange stubs. Redrawn at 25x20 — about ten times the pixels — he reads as a
dragon with horns, a wing and a muzzle. Nothing else changed. If a character isn't
recognizable, the first question is whether it's simply too small.

Rough sizes that work, in sprite cells before scaling:
- 20-25 wide x 20-25 tall for a full character (Stitch, Figment, Ralph, Genie).
- Faces and heads can go bigger; a head-only close-up reads better than a tiny
  full body.

**But watch the 2x scale.** Sprites double on 64-row boards (`scale = 2 if height >= 64`).
A 25-cell-wide sprite is 50 of 64 columns there, which leaves almost nothing for
anything else. Slinky Dog's spring nearly vanished at 2x for exactly this reason.
Check both board sizes every time; they fail differently.

**If a character's motion needs the board's width, keep him 1x rather than bending
his path.** Slinky is two sprites with a spring between them. Doubled on 64x64 the
halves ate 54 of 64 columns and the spring — his best feature — had nowhere to go.
Earlier versions tried to buy room with the path instead: walking the bottom edge and
turning up the right side, then running corner to corner on the diagonal. Both lost
the one pose that sells him. The Slinky that landed stays 1x on both boards
(`SCALE = 1`) and stretches straight across a single ground line, rear on the left
edge and nose on the right. Genie's lamp is 1x for the same reason; declare a fixed
size with a `SCALE` or `<NAME>_SCALE` attribute so the sprite editor previews it right.

The diagonal also forced both sprites to rotate, and a tilted dog reads as two
separate animals joined by a spring rather than one dog stretching. **Keep characters
upright on a ground line.**

## Reading at low resolution

**Silhouette first.** If the outline doesn't say who it is, no amount of interior
detail will save it. Ears, horns, a hat, a snout — the shape that sticks out is what
identifies the character.

**Outline everything.** A dark character on a dark board disappears. Every sprite here
uses a `K` outline color around the body. Sorcerer Mickey's ears were invisible as
true black; lifting them to charcoal `(74, 72, 88)` fixed it.

**Faces want three-quarter view, not profile.** Slinky's head was drawn in profile
first and the face collapsed into a dark mass with one dot on it — in profile a dog is
mostly skull and ear, and the features that identify him are edge-on. Turned toward
the viewer, the parts separate: cap on top, ear down one side, and a broad muzzle out
front carrying both eyes and the mouth. Nearly every character here reads better
facing you.

**Eyes are the hardest part, and the most important.** Five separate failures:
- White rectangles with tiny pupils → looks startled and cartoonishly wrong.
- Near-black pupils on a mid-tone face → the eye vanishes into the fur.
- Dark eyes on a dark background → the eye sockets read as holes punched through
  the head.
- Eyes up on the skull rather than beside the muzzle → they read as sitting on top
  of the face instead of in it.
- Eyes flush against the body outline → they merge into the border and the face
  reads as blank. Inset them so they sit surrounded by the face color.

**A feature must differ from what it sits ON and from what it sits NEXT TO.** Slinky's
nose was drawn at `(28,24,24)` beside an outline at `(35,22,14)`: correctly placed,
strongly contrasting with the muzzle, and completely invisible, because it touched a
border it matched. The eyes were then lost the same way. Check both distances.

What works: make the eye a distinct mid-dark tone that differs from *both* the face
and the background, ring it with the outline color so it's clearly a separate shape,
and add a small bright glint. Keep a gap between the two eyes so they never merge
into a bar.

**Colors need to differ from their neighbours, not just be "correct".** Accuracy to
the character matters less than separation on the board. Nudge a color until the shape
beside it is legible.

## Movement

**One motion, motivated by the character.** Each character has one signature motion
and everything else follows from it. Dumbo's ear flap drives his bob — he lifts on the
upstroke. Baymax's inflation drives his squash, his overshoot and his settle. Slinky's
head-lead drives both the stretch and the reveal front.

**Pick the mechanic from the character, not the other way round.** Four exist:
- *Fly-by* (`FlyByReveal`) — crosses the board, reveals in its wake, trails particles.
- *Peek* (`PeekReveal`) — rises from the bottom edge over a visible screen. No blackout.
- *Wreck* (`RalphReveal`, `wants_prev`) — destroys the outgoing screen's pixels.
- *Assemble* (`MickeyReveal`, `wants_new`) — builds the incoming screen's pixels.

Genie needed none of them — his lamp emerge has no flight path — so he's standalone.
Don't force a character into a mechanic that fights it.

**Procedural beats sprite art when something must scale smoothly.** Baymax inflates,
and scaling fixed ASCII art moves in whole-pixel jumps that read as popping rather
than filling with air. He's drawn as filled ellipses keyed off one inflation factor
instead. Everything that holds a fixed size is easier as ASCII art.

**Sell the physics with small extras.** Baymax is pinned to the bottom edge so he grows
*upward*, and he's wide-and-flat when deflated, round when full. Those two details do
more than the scaling itself.

**Feet that move.** A character crossing the board with still feet glides, and it shows
(Chip 'n' Dale did, at first). `drawing.walking_pixels` cuts the feet out of side-on art by
row and column and steps them through `WALK_CYCLE` (apart, back foot up, passing, front foot
up), a pixel at a time; bob the body a row while a foot is up for a run. It reads even at
1px, and it works on all fours (Tigger's back and far front paws step together).

**Side-on art stays side-on.** Turning Chip 'n' Dale's heads to face us, with front heads
drawn to match their side ones, read as two other chipmunks, even after a redraw. A
character drawn in profile should act in profile.

## Blending

Particles and smoke must be drawn *additively* over what's already on the canvas.
Genie's smoke used plain `SetPixel` at first and the puffs read as black holes eating
the background. Soft, semi-transparent things need to let the screen show through.

## Timing

Give the eye time. Roughly:
- 1.2-2.3s for a fly-by crossing.
- 2-4s for anything with phases (rise, hold, act, leave).
- Preview with the real hold: ride screens hold 8s on the board, and a character's time
  comes out of that. A 4s preview hold made a 2.8s character look like it left the wait
  time no time at all.
- Hold at the extremes. A pause at the top of Stitch's peek, or at Baymax's full
  inflation, reads far better than constant motion.
- Ease, don't move linearly. `ease_out` on entrances; a decaying overshoot for
  anything springy.

## Bounds

A bigger sprite plus a bob will push a character off the board. Clamp the amplitude to
the room the sprite actually leaves:

```python
room = max(0, self.height - self.sprite_h)
amp = min(room / 2, self.height * 0.15)
```

Figment shipped without this and the tests caught it immediately. Always test that
nothing draws off-board, at both sizes.

## What to test

The parametrized fly-by tests cover a lot for free — add the class to `FLYBYS`. Beyond
that, worth asserting: it finishes within `duration`; it never draws outside the board
on either size; the signature motion actually happens (measure it — the drawn span
grows, the poses differ, the gap widens); art rows are uniform width and every
non-`.` character has a color.

Test the *motion*, not the pixels. Asserting on exact pixel positions makes the art
impossible to iterate on.

**Assert relationships in the art, not coordinates.** "The eyes sit surrounded by
muzzle", "the mouth is below the eyes", "the tail rises above the body" survive a
redraw; `art[6][3] == "P"` does not, and it will be the first thing you delete.

**Pin the colors too.** Slinky's nose passed every layout assertion while being
invisible, twice, because the tests only knew where things were, not whether you could
see them. A cheap channel-distance check catches exactly the failure that renders look
fine to a test and wrong to a person:

```python
def distance(a, b):
    return sum(abs(x - y) for x, y in zip(colors[a], colors[b]))

assert distance("P", "T") > 200   # eye against the muzzle it sits on
```

None of this replaces looking at it. It stops a feature you already fixed from
silently going missing the next time you redraw the head — which happened here twice.

## Scorecard

What worked and what didn't, so we don't repeat it:

- **Baymax** — the best of them. Procedural drawing, one clean inflation factor
  driving everything, and a face of two dots and a line that's unmistakable at any
  size. Simple shapes, well animated, beat detailed art.
- **Genie** — strong. Big, and his emerge-from-the-lamp gives him a story beat the
  others don't have. The lamp was a 9x6 blob until it was redrawn at 26x16 with the
  parts that make the silhouette — looped handle, domed lid, long upturned spout.
  It stays 1x on both boards; doubled on 64x64 it swamped Genie.
  Give props their own color keys: the lamp once shared Genie's `K` and turned his
  outline bronze.
- **Sorcerer Mickey** — the materialize effect is the best mechanic here, but his
  face reads as a flat mask.
- **Dumbo** — ears and flap are great; he's missing his back half entirely.
- **Slinky Dog** — redrawn from scratch around one pose: rear planted on the left
  edge, front half walking out until his nose touches the right edge, spring pulled
  across the whole board between them; then the rear snaps across and both bound off.
  The coils are tilted rings, shaded behind and bright in front, so they bunch into a
  tube when squashed and separate when stretched; his tail is a banded spring. The
  earlier versions took more rounds than any other character; the rewrite landed in
  three renders because it started from the pose, not the path.

- **Green Army Men** — landed on the second pass. The first read as green gingerbread
  men: one dim green for helmet, body and rifle, rigging drawn as two dots that read as
  eyes, three canopies merging into one band, and a chute that "collapsed" into a blob in
  mid-air. The redraw: bright toy-plastic green with a light/mid/dark shade, a dark
  helmet brim, the molded base, a rifle that pokes out past him at both ends, real
  rigging that swings like a pendulum, smaller canopies, a chute that slumps to the
  ground downwind, and a hop-off on their bases instead of a slide.
- **Millennium Falcon** — strong. Traced from the user's photo for the outline, then
  only the bold features painted back (see below). The arrival first had nothing on
  screen for its opening beat; making it the jump in reverse (a streak snapping into the
  ship) fixed it, and brightening her toward white as she stretches stopped the jump
  reading as a long grey brick.

- **Ralph** — redrawn from the user's pattern, cell for cell, with a double-fist slam. His
  raised arms were drawn as thick outlined lines from the shoulder (generated, not typed),
  and the first ones were far too long: fists nine rows over his head read as poles; four
  rows read as a wind-up. A pattern's size includes its outline, and black outline is
  invisible on the board, so he fits 64x32 with his outline rows hanging off it. Debris
  thrown with 64x32's gravity was still a third in the air when he finished on 64x64;
  scaling gravity with the board's height and a short tail let it clear.
- **Stitch** — two scenes from the user's profile pixel art were built and scrapped (a
  pop-up chomp, and eating the old ride letter by letter), but they taught two things.
  The art's eye was solid black like its outline, and on the board it read as a hole through
  his head; filling it indigo inside the black ring, glint kept, made it an eye. And his first
  closed mouth just removed the jaw's tip, which read as part of his face vanishing; it read
  as shut once the jaw swung up against the teeth as a solid wedge. What's left is surfing,
  from two bead patterns, copied cell for cell: standing on 64x64
  ([stitch.jpg](../docs/references/stitch.jpg)) and sitting on 64x32
  ([sitting_stitch.jpg](../docs/references/sitting_stitch.jpg)), where the standing one is
  too tall. On the back of the wave he looked like he was sledding down a ramp; a surfer
  rides the face, ahead of the crest, with the wave chasing him.

The pattern: the characters that landed are the ones with a simple, strong silhouette
and one well-executed motion. The ones that fell short tried for detail and lost the
shape. Slinky is the clearest case of the other lesson — decide the one pose that
sells the character, then size him to hold it.

## Landmarks and scenes: what worked

Notes from the Tower of Terror redraw and the Halloween party work (the two jack-o'-lanterns
in `display/landmarks/`, the Halloween castle fireworks). Both landed faster and better than the
early characters above, and mostly for process reasons. Read this before redoing a landmark.

### The process

1. **Start from the user's reference image.** The tower was drawn from a photo; the friendly
   pumpkin from a colouring page. A reference settles the questions a description can't
   (what the eyes look like, where the stem sits, which details are the identity), and it
   gives both of you something to compare renders against. Ask for one first. Patterns
   collected so far are in [docs/references/](../docs/references/README.md), each labelled with
   whether it fits each board cell for cell.
2. **Ask every open question in one batch, before drawing.** Guessing cost the early Slinky
   many redraws. Offer choices with a recommended default. The answers that most changed the
   result were ones nobody would have guessed: "a wink *and* a bounce", "put the name on
   the screen", "Mickey pumpkins, drop the plain ones". If the answer is "show me both",
   build both as a pinned variant (`MOTION`) and let production pick at random.
3. **Mock up text layouts with the real BDF fonts first.** Rendering the party name in the
   board's 4x6/5x8 fonts over the scene settled the layout in one round, before any code.
4. **Render to a PNG sheet, several moments, both board sizes, and look.** Every round found
   a real problem that reading the code never would. Crop and zoom in on the detail you're
   changing (the wink was only fixable at 20px per LED).
5. **Then put it on live emulator previews** so the user sees it move: one port per board
   size or variant (9000, 9001, 9002), each run from its own folder whose
   `emulator_config.json` sets the port, driven through `landmark_screen` so fonts and
   titles are real. Restart them after every change; they've imported the old code.
6. **Pin what broke in a test**, as relationships and colour distances, not pixels (below).

### What the renders caught, and the fix that generalised

- **A lit feature blended into what it sits on.** The pumpkin's glowing face read as the same
  orange as its shell. Fix: keep the surroundings darker than the feature at its dimmest,
  and add a **dark rim** around it, like the cut edge of a carving. The same rim fixed the
  filled Mickey-pumpkin firework's face.
- **Flicker dimmed a feature to its neighbour's colour.** Flicker by moving a hot spot or
  varying a small range around a high floor, never by fading the whole feature.
- **Colour against the background, not just neighbours.** Purple bursts vanished on the
  purple sky; brighter purples fixed it. Check every colour against the sky it flies over.
- **Foreground hid the subject.** The castle spire covered the pumpkin burst's face; the
  tower's cloud had to sit where the bolt could leave it. Place the subject clear of
  whatever draws in front of it, and test that it's clear.
- **A held effect changed an unrelated one.** Holding shape sparks bright also held their
  white-hot flash for a second. When you stretch one phase, check the others.
- **A closing eye left its outline behind.** Anything that disappears must take its outline
  and rim with it (the wink restores the shell under the eye and its cut rim).

### Design lessons

- **64x32 wants its own composition, not a shrunken 64x64.** The tower tilts the camera up
  from the trees to the dome; the pumpkin moves beside the text instead of under it.
  Decide both layouts up front, and put them behind a hook like `_layout()`.
- **Budget the screen time.** The sweep and wipe take 1.2s of every landmark's `SCREEN_S`,
  so a 3s landmark has 1.8s of scene. The tower's strike, doors and drop needed 3.5s; say
  so with `SCREEN_S` instead of rushing the story.
- **One story beat, then hold.** Tower: strike, doors, drop. Pumpkin: dark, candle catches,
  one wink or hop. Both read because each beat has room.
- **Keep layers separate** so a motion moves only the subject: the pumpkin hops but the mist
  and sky stay put (`_draw_pumpkin` vs `_draw_mist`).
- **Procedural shapes scale; keep proportions relative to the board** (radius from height),
  then tune the one or two numbers that look wrong on each size.
- **Check the live API before designing a trigger.** The party's name was only in entity
  names, not the schedule; show names mix curly and straight apostrophes; Happily Ever After
  is closed on party nights. Each of those shaped the design, and each came from one curl.

### Tests that paid off

- Colour distance between a feature and what surrounds it (glow vs shell, tongue vs glow).
- The subject clears the foreground and the text (face above the castle, title boxes off
  the pumpkin), on both board sizes.
- The story happens inside the screen: the tower's strike, doors and drop all fall within
  `SCREEN_S`, once, in order.
- Variants and random picks: both motions get picked; only the intended burst shapes appear.

### Before redoing Spaceship Earth

The current `SpaceshipEarthLandmark` reads as a grey ball on legs: its facet pattern renders
as mottled noise, not the triangles that make the sphere recognisable, and nothing but a
glint happens. Questions to settle first, with a reference photo:

- Day or night? At night the sphere is lit in changing colours ("Beacons of Magic"), which
  could be the motion and would stand out far more than grey.
- What identifies it at this size: a bold triangle pattern (fewer, larger facets), the
  tripod legs, the EPCOT entrance sign or fountain, or the silhouette alone?
- One story beat for the screen: the lights coming on, a colour wave around the sphere,
  fireworks behind it, a monorail passing in front?
- 64x32 composition: shrink, crop, or tilt up like the tower?

## Army Men and the Falcon: what worked

The process above held; these are the lessons that were new.

### Drawing

- **Trace a reference photo, then keep only the bold features.** Turn the photo to the
  sprite's heading, crop to the subject, and downscale it to board size: that gives an
  accurate silhouette and where each feature sits. The photo's detail comes out as grey
  noise (the Spaceship Earth problem), so throw it away and paint back a handful of bold
  shapes on flat colour. For the Falcon: the gap between the mandibles, the turret ring,
  docking arms, a few red patches, the cockpit tube and the engine band.
- **Generate geometric shapes, don't hand-type them.** The canopy star failed four times
  in hand-drawn ASCII (it kept reading as a face) and was right first time rasterized from
  a real five-point polygon at 8x and scaled down. Same for domes and discs.
- **Any pair of lone dots reads as eyes.** The Army Men's rigging, drawn as two white
  points under each canopy, looked like faces floating in the sky. Draw rigging as lines.
- **A thin prop has to break the silhouette.** A rifle held across a body is invisible at
  this size until it pokes out past him at both ends; then it reads instantly.
- **Move a character the way its source moves.** Toy army men can't walk, their feet are
  molded to a base, so they hop, as in the films. It read far better than sliding.
- **Something that turns into light should turn into light.** A stretched hull stays a
  grey brick; blend it toward the streak colour as it stretches.
- **Deflating isn't shrinking.** A chute scaled down in place became a blob hanging in
  mid-air. Things lose their shape and fall: it blows downwind, sinks, flattens, fades.
  When you squash art, check which rows the scaling picks (the star smeared into a white
  bar) and swap features out of it.

### Timing and size

- **Time by distance, not seconds.** 64x64 is twice the drop of 64x32, so the same
  `FALL_S` made the Army Men plummet there. Give the tall board its own time
  (`FALL_S_TALL`) and test the speed, not the duration.
- **Check clearance at 2x.** The Falcon doubled on 64x64 fills the board well, but her
  cruise ran her mandibles off the right edge until her stop point was clamped so her
  nose stays on the board.

### Screens and pixels

- **A transition that takes the old screen must paint every pixel of it, black
  included.** `show_screen` draws the new screen first and the transition paints over
  it, so drawing only the old screen's lit pixels lets the new ride show through its
  dark areas. The Army Men and Ralph both shipped with that bug.
- **Test with fake screens that have dark pixels.** The Army Men's tests used an old
  screen lit edge to edge, which is exactly why they missed the bleed-through.
  `test_new_screen_never_shows_through_the_old_screens_dark_pixels` goes through the real
  `show_screen` with a half-lit screen; add each new screen-taking transition to it.
- **Blend soft effects against pixels you captured, not the canvas.** Dust, glow and
  fades need what's underneath. A real Pi canvas can't be read back (`canvas.px` doesn't
  exist there, so it blends against black), but a transition holding `prev_px`/`new_px`
  knows exactly what's on the board. The Falcon keeps the frame it drew in `_base` so
  its glow blends over the stretched old screen, not the original.
- **Draw whole frames cheaply.** Stretching the old screen per pixel into streaks would
  be hundreds of thousands of `SetPixel` calls a frame; mapping each output pixel back to
  a source pixel (`(x - shift) / stretch`) is one call per LED and reads the same.
