# Drawing characters for the LED board

Notes from building the eleven transitions in `display/animation.py`. Most of these
were learned the hard way — by rendering something, looking at it, and finding it
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
anything else. Slinky Dog's spring nearly vanishes at 2x for exactly this reason.
Check both board sizes every time; they fail differently.

## Reading at low resolution

**Silhouette first.** If the outline doesn't say who it is, no amount of interior
detail will save it. Ears, horns, a hat, a snout — the shape that sticks out is what
identifies the character.

**Outline everything.** A dark character on a dark board disappears. Every sprite here
uses a `K` outline color around the body. Sorcerer Mickey's ears were invisible as
true black; lifting them to charcoal `(74, 72, 88)` fixed it.

**Eyes are the hardest part, and the most important.** Three separate failures:
- White rectangles with tiny pupils → looks startled and cartoonishly wrong.
- Near-black pupils on a mid-tone face → the eye vanishes into the fur.
- Dark eyes on a dark background → the eye sockets read as holes punched through
  the head.

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

## Blending

Particles and smoke must be drawn *additively* over what's already on the canvas.
Genie's smoke used plain `SetPixel` at first and the puffs read as black holes eating
the background. Soft, semi-transparent things need to let the screen show through.

## Timing

Give the eye time. Roughly:
- 1.2-2.3s for a fly-by crossing.
- 2-4s for anything with phases (rise, hold, act, leave).
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

## Scorecard

What worked and what didn't, so we don't repeat it:

- **Baymax** — the best of them. Procedural drawing, one clean inflation factor
  driving everything, and a face of two dots and a line that's unmistakable at any
  size. Simple shapes, well animated, beat detailed art.
- **Genie** — strong. Big, and his emerge-from-the-lamp gives him a story beat the
  others don't have. His lamp still needs work.
- **Sorcerer Mickey** — the materialize effect is the best mechanic here, but his
  face reads as a flat mask.
- **Dumbo** — ears and flap are great; he's missing his back half entirely.
- **Slinky Dog** — the weakest. Reads as a generic dog with a spring between its
  halves rather than the character, and the spring nearly disappears at 2x.

The pattern: the characters that landed are the ones with a simple, strong silhouette
and one well-executed motion. The ones that fell short tried for detail and lost the
shape.
