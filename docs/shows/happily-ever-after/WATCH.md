# Happily Ever After: watching the show, scene by scene

A workbook for studying the real show with the `/watch` skill (Gemini watches the video), one scene
at a time, and keeping what it sees next to the scene it describes, for refining our show
(`display/fireworks/shows/happily-ever-after.json`, and V2's characters in
`happily-ever-after.v2.json`). The show's timeline, sync notes and what's been fixed are in
[README.md](README.md); this file is for asking and keeping the answers.

- **Video:** https://www.youtube.com/watch?v=-LncKUxWMsQ (19:02, a guest's recording from the hub).
- **Two clocks.** Our score counts seconds into `sounds/happily-ever-after.wav` (**audio** time);
  Gemini needs the video's own clock (**video** time). Measured, not guessed (README.md, Clock):
  **video = audio × 1.001 + 10.19 s**. Every section below gives both, already converted.
- **Accuracy.** Gemini's timestamps are good to a few seconds, and it can miscount or invent. Treat
  an answer as a lead to check in `tools/show_sync_checker.html`, not as fact. Best results come from
  short windows (under ~2 minutes); every scene here is one.

## How to use it

1. Pick a scene below and, if you like, add to its **Your notes for this scene**: anything
   specific to look for (a character you're planning, a moment that looks wrong on the board).
2. Ask Claude: **"watch scene 4.3"** (the section's number). Claude runs `/watch` on that scene's
   video window with the **base prompt** plus your notes, then saves Gemini's answer into that
   scene's **Answers**, newest first, dated, with the notes that went with it.
3. Re-ask any time (a new question, a different model): answers stack, so earlier reads stay for
   comparison.

What runs, from the repo root: `bash docs/shows/happily-ever-after/watch-scenes.sh 4.1 4.2 4.3`. For
each scene it builds the question from this page (`watch_scene.py`: the base prompt with the scene
filled in, plus its notes), runs the `/watch` skill's script on the scene's video window, retrying
Gemini's busy and quota errors on both free Flash models, and files the answer here
(`save_answer.py`). Gemini's free tier allows roughly a dozen scenes a day (it resets at midnight
Pacific); a scene that still fails is reported and left for later. Anything checked by eye or against
our audio goes in a **Checked** line under the scene's details, above the answers it corrects.
After changing the score, `python3 docs/shows/happily-ever-after/sync_headers.py` brings every scene's heading,
windows and **Our score now** back in line with it (answers, checks and notes stay as they are).

## Base prompt

Sent for every scene, with `{start}`, `{end}`, `{title}` and `{ours}` (the scene's **Our score
now**) filled in, then that scene's notes. The video window Claude sends runs 3 s past each end of
the scene, so Gemini can see where it really starts and stops. Edit the prompt here to change every
future question.

> You are watching part of a guest's recording of Disney's *Happily Ever After* fireworks show at
> Magic Kingdom, filmed from the hub in front of the castle. We think the "{title}" part of the show
> runs from about {start} to {end} of the video; you are given a few seconds either side. We are
> recreating the show on small LED matrix boards (64x32 and 64x64 pixels: a castle, fireworks and
> characters, synced to the show's audio), so we need precise, detailed facts. Use timestamps on the
> video's own clock (MM:SS from the start of the full video). Take your time and look closely.
> **Ignore smoke and haze completely**: never describe it.
>
> Answer under exactly these headings:
>
> **1. Where this part starts and ends.** The exact timestamps it starts and ends, and what marks
> each change (a musical hit, a new song, a projection change, a blackout). Say if our {start} to
> {end} is early or late.
>
> **2. Music.** The song or music, the lyric lines sung or spoken (with timestamps), and every big
> musical hit or beat that something lands on.
>
> **3. Timeline.** A table, one row per moment, in time order:
> `time | fireworks | lasers and lighting | castle | characters`.
>
> **4. Fireworks in the sky.** Every burst, barrage and effect: type (peony, chrysanthemum, willow,
> comet, mine, ring, heart, smiley or other shape, strobe, crossette, cake), colours, size, height
> (low, at the spire, high) and side (left, centre, right). Where launches come from and which way
> they move (a left-to-right sweep, a fan, mirrored pairs). Count them. The rhythm: roughly how many
> bursts a second, steady or in waves, and when the sky is dark or quiet.
>
> **5. Fireworks on the castle.** Anything fired from the castle itself: fountains or gerbs on the
> turrets, roof effects, sparks from the battlements, rockets from behind it. Keep these separate
> from the sky bursts.
>
> **6. Lasers and lighting.** Think carefully about the lasers: their colours, where they come from,
> where they point and how they move. Also searchlights, flames and fountains.
>
> **7. The castle.** Its own lighting (base colour, windows, turrets) and how and when it changes,
> separately from the projections. Then the projections: images, scenes, colours, patterns and text,
> and exactly when each one changes.
>
> **8. Characters.** Every character who appears, projected on the castle or formed by fireworks or
> lights. For each: who they are (or a description if you can't name them); where they are, using a
> 3x3 grid of the castle (top-left to bottom-right) or its parts (spire, left tower, right tower,
> base); their size compared with the castle (e.g. "half the castle's height"); how they move (fly
> across, rise, fade in, stand), which way and how fast; and exactly when they appear and when they
> leave.
>
> **9. For our boards.** The two or three moments that matter most to recreate this part, and what
> a tiny LED version must get right to feel authentic.
>
> **10. What you couldn't see.** Anything blocked, out of frame, blurred or zoomed, and anything
> you're unsure of. Say "unsure" rather than guess, anywhere above.
>
> **11. Our version.** Last, and only after the above: our version of this part currently shows:
> "{ours}". What's right, what's wrong, and what's missing?

## The show

## 1. Opening (audio 0:00-1:38, video 0:10-1:48)

### 1.1 Theme fanfare

- **Audio:** 0-19 s (0:00-0:19, 19 s) · **Video:** `--start 0:10 --end 0:29`
- **Our score now:** Grey castle, blue spires, the gate lit yellow; two banks of white and ice-blue searchlights stand and sway, cross over the spire (video 0:17), fan out wide (0:22) and fade before the narrator (0:27); no fireworks. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 0:07-0:32 · notes: none</summary>

Here are the details for the "Theme fanfare" segment of the show:

**1. Where this part starts and ends**
* **Starts:** **0:10**  
  * **Marker:** Marked by the opening brass downbeat of the grand instrumental fanfare and the sudden switch-on of the white searchlight beams sweeping up into the night sky behind and beside the castle.
* **Ends:** **0:29**  
  * **Marker:** The final chord of the orchestral fanfare resolves, the searchlights fade down completely, the camera zooms into the castle facade, and the narrator begins speaking the opening line (*"And they all lived..."* at 0:29).
* **Verdict on 0:10 to 0:29:** This timeframe is **exact**.

**2. Music**
* **Song / Music:** Instrumental opening fanfare of the *Happily Ever After* show theme (full orchestral brass, strings, chimes, and percussion).
* **Key Hits & Beats:**
  * **0:10 – 0:12:** Opening cymbal swell and bold introductory brass hit as searchlights ignite.
  * **0:13:** Main sweeping melodic statement begins on soaring French horns and trumpets.
  * **0:17 – 0:18:** Melodic ascent / secondary brass swell; searchlights sweep inward to form an intersecting crisscross pattern.
  * **0:21 – 0:23:** Swelling orchestral crest; searchlights fan wide outward.
  * **0:25 – 0:27:** Climactic cadence chord held and resolved.
* **Spoken Dialogue:**
  * **0:29:** Male narrator speaks: *"And they all lived happily ever after..."*

**3. Timeline**
| Time | Fireworks | Lasers and lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **0:10** | None | White searchlight beams switch on behind castle and ground banks. | Main walls illuminated in warm golden amber; spires in royal blue; clock tower illuminated. | None |
| **0:11 – 0:16** | None | Searchlights fan upward and sway gently side to side in rhythm with the brass melody. | Static royal golden/amber wash with glowing windows. | None |
| **0:17 – 0:20** | None | Searchlights sweep across each other, crisscrossing over the main central spire. | Unchanged; steady warm gold walls and vibrant blue turrets. | None |
| **0:21 – 0:25** | None | Searchlights sweep wide apart into a broad symmetrical fan. | Unchanged. | None |
| **0:26 – 0:28** | None | Searchlights begin lowering and fading out as the final musical chord decays. | Unchanged; camera zooms in toward the central facade. | None |
| **0:29** | None | Searchlights fully off. Castle facade remains warmly lit. | Clock face and archway windows glow cyan/gold. | None |

**4. Fireworks in the sky**
* **Bursts:** None. The sky remains completely clear of aerial pyrotechnics throughout this segment.

**5. Fireworks on the castle**
* **Castle Pyro:** None. No rooftop comets, gerbs, strobes, or fountains are fired during this musical prelude.

**6. Lasers and lighting**
* **Lasers:** None active.
* **Searchlights:** 
  * **Colour:** Cool bright white.
  * **Placement:** Ground/rooftop fixtures placed behind the castle perimeter, grouped into roughly 4–5 beams on the left flank and 4–5 beams on the right flank, plus backlighting beams directly behind the castle hub.
  * **Motion:** 
    * **0:10:** Beams project vertically.
    * **0:13 – 0:16:** Gentle synchronous sway.
    * **0:17 – 0:20:** Left and right banks tilt inward, crisscrossing through the sky above the spires.
    * **0:21 – 0:25:** Banks sweep back outward into a symmetrical wide V-fan.
    * **0:26 – 0:28:** Beams tilt downward and fade out completely.

**7. The castle**
* **Castle Lighting:**
  * **Walls / Facade:** Lit in a solid, regal warm golden/amber architectural wash.
  * **Turrets and Roofs:** Saturated royal blue.
  * **Accent Features:** The central clock face area, balcony, and front archway feature illuminated turquoise/cyan backlighting with warm gold trim.
  * **Windows:** Lit with a soft, warm interior glow.
* **Projections:** None. No animated images, mapped textures, or character scenes are projected during this introductory fanfare.

**8. Characters**
* **Characters:** None. 
  *(Note: Tinker Bell’s guide wire is visible angled across the upper sky at 0:11, but no characters appear in person or via projection during this section).*

**9. For our boards**
To recreate this fanfare authentically on 64x32 or 64x64 LED matrices:
1. **The Static Regal Castle Palette:** Keep the castle completely static with golden/amber walls, dark blue turret caps, and a glowing cyan/warm-white dot for the clock tower/balcony.
2. **Dynamic Searchlight Beams:** The motion must be carried entirely by white 1-pixel-wide searchlight beams emerging from behind the castle:
   * 0:10: Ignite vertically.
   * 0:17: Cross over each other above the center spire into an "X" / crisscross.
   * 0:22: Fan wide outward.
   * 0:27: Fade out to black right before the narrator speaks at 0:29.
3. **No Pyro:** Suppress all fireworks until after the narration finishes.

**10. What you couldn't see**
* **Camera Movement:** The camera is handheld and slowly zooms in closer to the castle between 0:26 and 0:29, which cuts off the outermost searchlight ground fixtures, but their skyward beams remain fully discernible.

**11. Our version**
* **What's Right:**
  * "Warm amber castle, blue spires": **Correct.**
  * "White searchlights crisscrossing": **Correct.**
  * "No fireworks": **Correct.**
  * "Characters: none": **Correct.**
* **What's Wrong:**
  * "The keyhole glowing gold": **Minor correction** — while there is warm gold accent lighting on the castle, the central focal area around the clock face / rose window is glowing **cyan / turquoise** rather than pure gold.
* **What's Missing:**
  * The searchlights do not just crisscross; they open vertically (0:10), crisscross in the middle (0:17), open into a wide fan (0:22), and power down/fade out at 0:27–0:28 right before the narration begins.

</details>

### 1.2 Narrator opening

- **Audio:** 19-45.8 s (0:19-0:45, 26.8 s) · **Video:** `--start 0:29 --end 0:56`
- **Our score now:** Searchlights off, the sky dark, the gate a dim steady yellow as the narrator speaks. Characters: none.
- **Checked by eye (2026-10-14):** the keyhole (the gateway arch) stays dim through the narration. When the show is ready to begin (about video 0:56), magic comes out of the keyhole and spreads through the whole castle. So it doesn't dim further, and it doesn't light up gold on its own: the magic pours out of it.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 0:26-1:00 · notes: none</summary>

**1. Where this part starts and ends**
* **Starts at 0:29:** Marked by the searchlights shutting off (0:28–0:29) and the narrator speaking his opening sentence (*"And they all lived happily ever after..."*).
* **Ends at 0:57 / 0:58:** Marked by the end of the narration (*"...within"* at 0:56), a swelling chime sound effect, and the first sung lyric (*"Ready to begin..."* at 0:58) as glowing golden light erupts from the castle gateway.
* **Assessment of 0:29 to 0:57:** Your timestamp range is **exact**.

**2. Music**
* **Music style:** A soft, warm orchestral underscore (strings, woodwinds, and delicate piano) playing a gentle fairytale motif.
* **Spoken Narration (Male narrator):**
  * **0:29 – 0:32:** *"And they all lived happily ever after."*
  * **0:33 – 0:35:** *"Each of us has a dream."*
  * **0:35 – 0:37:** *"A heart's desire."*
  * **0:37 – 0:39:** *"It calls to us."*
  * **0:39 – 0:41:** *"And when we're brave enough to listen,"*
  * **0:41 – 0:43:** *"and bold enough to pursue,"*
  * **0:43 – 0:46:** *"that dream will lead us on a journey"*
  * **0:46 – 0:49:** *"to discover who we're meant to be."*
  * **0:49 – 0:51:** *"All we have to do"*
  * **0:51 – 0:53:** *"is look inside our hearts,"*
  * **0:53 – 0:56:** *"and unlock the magic within."*
* **Musical cues / hits:**
  * **0:56 – 0:57:** Magical rising chime / sparkle crescendo.
  * **0:58:** Clear piano chord and female solo vocal entry singing *"Ready to begin..."*

**3. Timeline**
| Time | Fireworks | Lasers and lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **0:26 – 0:28** | None | 8 skyward searchlights fanned behind castle | Warm amber/rose wash on towers; blue turrets; glowing gold clock | None |
| **0:28 – 0:29** | None | Searchlights switch off | Castle lighting holds steady | None |
| **0:29 – 0:51** | None | None (sky dark) | Warm peach/coral body wash; royal blue turret roofs; warm golden gateway | None |
| **0:51 – 0:56** | None | None | Main gateway archway/keyhole at base begins brightening to brilliant gold | None |
| **0:56 – 0:59** | None | None | Bright golden magical flare bursts from the gateway, swirling upward along the facade | None |

**4. Fireworks in the sky**
* **None.** The sky remains completely dark and silent throughout the narration (0:29–0:57).

**5. Fireworks on the castle**
* **None.** No gerbs, fountains, strobes, or rooftop pyro are fired during this prologue.

**6. Lasers and lighting**
* **Searchlights:** At 0:26–0:28, eight bright cyan-white searchlight beams fan upward into the night sky behind the castle (4 angled left, 4 angled right). At **0:28–0:29**, they shut off completely.
* **Lasers, flames, fountains:** None are active.

**7. The castle**
* **Architectural lighting (0:29–0:51):**
  * Spire roofs and turret cones: Saturated royal blue and indigo.
  * Main castle facade and central spire column: Soft, warm peach/coral wash.
  * Clock face: Glowing round warm amber circle.
* **Projections:**
  * **0:51 – 0:56:** On *"look inside our hearts"*, the arched gateway (bottom-center) illuminates with a bright golden keyhole/portal outline.
  * **0:56 – 0:59:** On *"unlock the magic within"*, the portal pulses brilliantly, and glowing golden ribbons and sparkles swirl upward across the castle facade toward the clock and spires.

**8. Characters**
* **None.** No character projections, silhouettes, or figures appear during this prologue segment.

**9. For our boards**
1. **The blackout / quiet transition (0:28–0:29):** Shut off the searchlights immediately as the narration starts, leaving the sky pitch black and the castle peacefully illuminated in two-tone blue and warm amber.
2. **The keyhole ignition (0:51–0:56):** At bottom-center, fade in a solid, bright golden arch/portal in the gateway.
3. **The magical upward burst (0:56–0:58):** Send a bright golden sparkle or light beam rising rapidly from the gateway up into the center spire right as the female vocal sings *"Ready to begin"*.

**10. What you couldn't see**
* Ground-level details at the very bottom left and right of the plaza are obscured by foliage/trees.
* The camera slowly zooms out slightly between 0:27 and 0:34, but the entire castle remains fully visible.

**11. Our version**
* **What's right:** Searchlights off, sky dark, and no characters.
* **What's wrong:** *"The keyhole dims"* is incorrect. The keyhole/archway does not dim; it does the exact opposite—it **brightens** into an intense golden glow between 0:51 and 0:56.
* **What's missing:** The upward release of golden magical light from the keyhole portal at 0:56–0:58, which acts as the visual trigger into the opening song.

</details>

### 1.2a Magic from the keyhole

- **Audio:** 45.8-47 s (0:45-0:47, 1.2 s) · **Video:** `--start 0:56 --end 0:57`
- **Our score now:** As the show is ready to begin (video 0:56), the keyhole blazes yellow and its magic climbs the walls, tinting them gold while the roofs stay blue, then fades back as the singing starts (about 0:59). Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 1.3 Happily Ever After theme song

- **Audio:** 47-63 s (0:47-1:03, 16 s) · **Video:** `--start 0:57 --end 1:13`
- **Our score now:** Gold sparkles fall through the sky, the gate glowing steadily yellow; still no fireworks. Characters: none.
- **Checked by eye (2026-10-13):** at video 1:13, on "…unfold", it's a burst of **gold magic**, not two comets as Gemini's answer below says. The sky stays free of fireworks until the chorus (1.4: 1:48).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 0:54-1:16 · notes: none</summary>

Here is the breakdown of the selected segment for your LED matrix recreation:

**1. Where this part starts and ends**
* **Start:** Exactly at **0:57** (your 0:57 estimate is accurate).  
  * *Marker:* The deep-voiced narration ("...part of the magic...") concludes, and the soaring piano and duet intro of the theme song ("Happily Ever After") begins as golden magical light swirls around the castle clockface and gateway.
* **End:** Exactly at **1:13** (your 1:13 estimate is accurate).  
  * *Marker:* The vocalist holds "...unfold", followed instantly at **1:13** by a loud blast/whoosh sound effect and two vertical gold/white flash comet shoots launched directly behind/flanking the castle, opening the upbeat, rhythmic section of the song at **1:14** ("Reach out and find your happily ever after...").

**2. Music**
* **Track:** "Happily Ever After" (Original Theme Song performed by Jordan Fisher and Angie Keilhauer).
* **Lyrics & Audio Cues:**
  * **0:54–0:56:** Spoken male narrator: "...part of the magic."
  * **0:57:** Piano chords enter with strings and chimes; keyhole/clock portal activates.
  * **0:58–1:05:** Male vocal: *"Ready to begin, let the wonder take hold..."*
  * **1:05–1:13:** Female vocal: *"Feel it draw you in, watch the moments unfold..."*
  * **1:13:** Audible launch whoosh / percussive ignition thud signalling the first pyrotechnic lift.
  * **1:14:** Rhythmic drum beat / full pop orchestration drops: *"Reach out and find..."*

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **0:54–0:56** | None | Low blue flood, subtle roof lights | Cinderella Castle base lit in warm golden stone; spires and upper roofs in royal blue/indigo. | None |
| **0:57–1:00** | None | Searchlight beams activate from hub/behind castle, sweeping skyward | Bright gold glow at main gateway archway (bottom-center) and clockface. Green/gold pixie-dust ribbon spirals up around the central spire. | None |
| **1:01–1:05** | None | 4–6 soft white/blue searchlights criss-cross gently behind castle | Castle facade transitions to rich royal blue lower walls, amber-lit clock tower, warm golden center. Golden trails swirl up towers. | None |
| **1:06–1:09** | None | Angled white searchlight beams continue sweeping behind turrets | Central facade and upper tower glow warm golden-orange, while outer lower turrets remain deep indigo/blue. Gate is bright white/gold. | None |
| **1:10–1:12** | None | Searchlights fan upward outward | Upper spire lights up with an intense warm golden pulse radiating down from the central window/clock. | None |
| **1:13–1:14** | Twin vertical comets launch from ground behind castle | Searchlights sweep outward; stage strobes flash at base | Gateway and central clock flash brightly into sparkling gold. | None |

**4. Fireworks in the sky**
* **0:57 – 1:12:** Completely **dark and quiet**. There are **zero** sky bursts, peonies, chrysanthemums, cakes, or shells during this entire ballad build-up.
* **1:13:** Exactly **2 vertical comets/tails** (bright white-gold) shoot up simultaneously from directly behind the castle walls (left and right of the main central spire) reaching roughly spire height.

**5. Fireworks on the castle**
* **0:57 – 1:12:** None. No rooftop gerbs, fountains, or battlement sparks.
* **1:13:** Launch signature of the two comets from immediately behind the lower rooftop parapets.

**6. Lasers and lighting**
* **Lasers:** None visible during this soft intro.
* **Searchlights:** Starting around **0:58**, 4 to 6 white-cyan searchlight beams originate from ground level behind the castle and hub perimeter. They sweep slowly upward in criss-crossing patterns across the dark sky.
* **Flames / Fountains:** None.

**7. The castle**
* **Base/Structural Lighting:** 
  * Turrets and outer spires are bathed in deep midnight/royal blue.
  * Central body is bathed in warm golden/amber light.
* **Projections & Animation:**
  * **0:57–1:01:** A bright, glowing golden ribbon of pixie dust sparks into life at the lower archway, spirals upward across the castle facade, around the clockface, and climbs the main central spire.
  * **1:02–1:08:** The castle archway gateway (center bottom) acts as an intensely bright, glowing portal. Magical shimmering golden light pulses along the vertical masonry lines and windows.
  * **1:09–1:12:** The projection pulses from deep rose/amber to brilliant white-gold, culminating in an energetic burst of light concentrated at the clockface and main portal just as the phrase ends.

**8. Characters**
* **None.** No characters (animated Disney figures or shadows) appear anywhere on the castle or in the sky during 0:57–1:13. The focus is purely on the castle's architectural transformation and the magical swirling pixie-dust trail.

**9. For our boards (64x32 and 64x64 LED matrix)**
To make this segment unmistakably authentic on small pixel displays:
1. **The Swirling Ribbon (0:57–1:03):** Animate a 1-to-2-pixel wide stream of yellow/bright-green pixels spiraling from the bottom center gate, winding diagonally across the castle body, and running straight up to the peak of the central spire.
2. **Color Palette Contrast:** Keep the outer towers and turrets dark royal blue while the central column (gate, clock tower, high spire) glows deep amber/gold with a solid white-gold glowing archway at the base.
3. **The 1:13 Launch Hit:** Keep the sky completely black until precisely 1:13, where two 1-pixel white-gold trails streak straight up behind the shoulders of the castle on the final drum hit before the beat drops.

**10. What you couldn't see**
* Exact ground-level fixtures around the moat/hub due to the crowd silhouette in the foreground.
* Distant perimeter searchlight bases outside the Magic Kingdom berm (only their beams in the sky are visible).

**11. Our version**
* **What’s right:** "Gold ribbons swirl, the keyhole glows; still no fireworks. Characters: none." — This is largely accurate!
* **What’s wrong / missing:**
  * It misses the **exact moment fireworks start**: at **1:13**, the quiet ends with two vertical white-gold comets shooting up behind the castle.
  * It overlooks the **sky searchlights**: sweeping white beams cross in the sky starting at 0:58.
  * It misses the specific color contrast: royal blue on the outer towers framing the glowing warm-amber center.

</details>

### 1.4 Theme song builds

- **Audio:** 63-98 s (1:03-1:38, 35 s) · **Video:** `--start 1:13 --end 1:48`
- **Our score now:** On "...unfold" (video 1:13) a burst of gold magic out of the gate over the lower castle; then red walls under royal-blue roofs, white and ice-blue searchlights; still no fireworks. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 1:10-1:51 · notes: none</summary>

**1. Where this part starts and ends**
* **Starts:** **01:13**. Marked by a rushing whoosh sound effect and chime on the word *"unfold"*, followed immediately at 01:14 by a rhythmic drum hit and the entrance of the male vocal/chorus.
* **Ends:** **01:48–01:49**. Marked by the musical crescendo reaching the start of the chorus (*"The start..."*) where the first massive aerial shells detonate and launch comets shoot upward.
* **Assessment:** Your range of **01:13 to 1:48 is spot-on**. It covers the entire vocal build-up verse prior to the chorus pyro eruption.

**2. Music**
* **Song:** *"Happily Ever After"* (Theme Song build-up verse, performed by Jordan Fisher and Angie Keilhauer).
* **Lyrics & Timestamps:**
  * **01:10–01:13:** *"...can unfold"* (female vocal finishing preceding bridge).
  * **01:14–01:22:** *“The journey that begins with a spark…”* (male vocal with steady drum beat).
  * **01:23–01:31:** *“Every step we take, brings a new hope, a new day…”* (male vocal continues, energy building).
  * **01:32–01:39:** *“Every choice we make, helps us find out our way…”* (female vocal joins).
  * **01:39–01:47:** *“Every wish that we're making, can lead where the heart's gotta go…”* (duet and full choir building in pitch and volume to a dramatic crescendo).
  * **01:48–01:49:** *“The start…”* (first beat of the explosive chorus).

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **01:13–01:20** | None | Faint cool-white/pale-blue searchlight beams angled skyward from flanks | Deep red/crimson facade; gold architectural trim; royal blue rooftops | None |
| **01:21–01:28** | None | 8+ bright yellow/gold searchlight beams erupt in a fan behind castle, sweeping and crossing | Red stone walls overlaid with shimmering gold scrollwork; swirling gold ribbon around archway | None |
| **01:29–01:38** | None | Searchlight beams shift to brilliant cyan/sky-blue, scanning in crossed angles | Gold filigree intensifies; center clock/rose window glows bright gold; blue spires | None |
| **01:39–01:44** | None | Searchlight beams turn warm gold again, slowly fanning outward | Intricate golden tracery and lace pattern covers all red facade sections | None |
| **01:45–01:48** | None | Searchlights intensify to bright white-gold in a wide fan, pulsing with vocal crescendo | Full castle blazes with golden illumination, saturated red walls, indigo turrets | None |
| **01:48–01:51** | Red aerial peony high left; two golden spinning/screamer comet tails rise right/left | Searchlights sweep outward as sky is lit by pyrotechnics | Front facade remains red and gold filigree under flash of bursts | None |

**4. Fireworks in the sky**
* **01:13 to 01:48:** **Zero fireworks.** The sky remains completely dark and quiet of pyrotechnics to allow the music, searchlights, and projection mapping to create tension and dynamic contrast.
* **01:48–01:51 (Chorus payoff):**
  * **01:48:** Two golden whistling/screamer comets with thick snaking smoke/sparks launch diagonally upward from perimeter launch sites flanking the castle (one left, one right).
  * **01:49:** A large, bright red peony/chrysanthemum shell bursts high in the sky to the upper-left of the castle spire.
  * **01:50:** A second red shell bursts slightly lower on the right, instantly followed by a massive golden chrysanthemum/palm burst directly over the central spire.

**5. Fireworks on the castle**
* **01:13 to 01:48:** None fired from or directly on Cinderella Castle. No fountains, gerbs, or roof strobes during this build-up.

**6. Lasers and lighting**
* **Lasers:** No visible narrow-beam overhead lasers in this section.
* **Searchlights:** A powerful ground-based searchlight array behind and around the castle:
  * **01:13–01:20:** Subdued, static cool-white beams angled outward.
  * **01:21–01:28:** Symmetrical fan of vibrant **amber-yellow** beams rising behind the castle, sweeping slowly left and right and crossing through each other.
  * **01:29–01:38:** The beams switch color to **cyan/ice-blue**, continuing wide skyward sweeps.
  * **01:39–01:48:** Beams shift to **golden-yellow**, widening out into an expansive crown pattern behind the main spire as the crescendo peaks.
* **Flames & Fountains:** None present.

**7. The castle**
* **Base Lighting:** Conical turret roofs and upper spires are washed in deep royal blue/indigo. The clock face and main lower archway glow with warm, bright white-gold.
* **Projections:**
  * The main structural walls (base, lower walls, center tower) are wrapped in a saturated rich crimson/red wallpaper texture.
  * Overlaid on the red is dynamic, glowing **golden filigree, baroque scrollwork, and lace-like tracery**.
  * At 01:21–01:28, magical golden ribbons of light swirl and climb across the lower balcony and central gateway.
  * The pattern remains stable throughout the verse, gradually glowing brighter and more luminous toward 01:48.

**8. Characters**
* **Characters:** **None.** No Disney characters appear on Cinderella Castle, in the sky, or anywhere in projection during this entire segment (01:13–01:48).

**9. For our boards**
1. **Strict Firework Silence Until 01:48:** Keep the upper matrix completely dark for pyro until the explosive hit at 01:48. The contrast between complete sky stillness and the searchlights creates the intended tension.
2. **Three-Phase Searchlight Sweeps:** On a 64x32/64x64 board, implement 4 to 8 lines sweeping behind the castle:
   * 01:21: Amber/yellow fan.
   * 01:29: Cyan/blue fan.
   * 01:39: Bright golden-white fan expanding outward.
3. **Castle Palette:** Fixed pixel map of Cinderella Castle with deep blue spires, glowing gold portal/clock, and red wall blocks peppered with yellow/gold twinkling filigree pixels.

**10. What you couldn't see**
* The lower perimeter ground level and guest hub area are dark/partially obscured by foreground crowd silhouettes.
* Outer peripheral searchlight bases are hidden behind tree lines.
* True laser projectors (if active over Main Street) are not visible from this camera angle looking directly at the front of the castle.

**11. Our version**
* **What's right:**
  * *"Red, purple and gold filigree on the castle"*: Correct (crimson red walls with gold filigree and indigo/purple spires).
  * *"yellow and cyan searchlights"*: Exactly right (they alternate between amber-yellow and cyan-blue).
  * *"still no fireworks"*: Correct (sky is clear until 01:48).
  * *"Characters: none"*: Exactly right.
* **What's wrong:**
  * Nothing is factually incorrect.
* **What's missing:**
  * The **exact timing of the searchlight color transitions** (yellow from 01:21, cyan from 01:29, back to gold/white from 01:39).
  * The dramatic musical resolution at **01:48–01:49**, where the first high-altitude red burst and twin climbing comets trigger.

</details>

## 2. Chorus (audio 1:38-2:17, video 1:48-2:27)

### 2.1 Theme chorus

- **Audio:** 98-128 s (1:38-2:08, 30 s) · **Video:** `--start 1:48 --end 2:18`
- **Our score now:** The show's first fireworks on the chorus: the castle red under blue roofs, its design traced in running gold magic; white comet fans off the rooftops, big gold and white chrysanthemums, a gold willow, red fans and a red peony. Characters: none.
- **Checked by eye (2026-10-14):** the castle is red with gold magic tracing its design. Which fireworks (comet pairs and willows, or a strobe barrage) doesn't matter much.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.7-flash · video 1:45-2:12 · notes: none</summary>

**1. Where this part starts and ends**
* **Start (01:48):** Begins with two bright comet trails launching from behind the castle, bursting into red aerial shells at **01:49** on the opening downbeat of the vocal chorus (*"Start..."*). Prior to 01:48, the music is a wordless choral build (*"Ooh..."*). Your 1:48 timestamp is exact for the pyrotechnic trigger.
* **End (02:09):** The vocal phrasing transitions into the climactic title line (*"Happily ever after"*), marked by a golden fan flare behind the spire at 02:09 before the big aerial shell bursts overhead at 02:10–02:11. Your 2:09 timestamp is accurate for the verse/chorus body just before the title drop.

**2. Music**
* **Song:** *"Happily Ever After"* (duet theme performed by Jordan Fisher and Angie Keilhauer).
* **Lyrics:**
  * `01:45 – 01:48`: Wordless choir swell (*"Ooh..."*).
  * `01:49 – 01:54`: *"Start a brand new chapter now..."*
  * `01:57 – 02:02`: *"Love will guide you on your way..."*
  * `02:06 – 02:09`: *"Reach out and find..."*
  * `02:10 – 02:13`: *"...your happily ever after..."*
* **Big musical hits:**
  * `01:49`: First chorus downbeat (*"Start..."*).
  * `01:56`: Accent beat preceding *"Love..."*.
  * `02:03`: Drum hit transitioning to *"Reach out..."*.
  * `02:07`: Emphatic vocal beat on *"find..."*.
  * `02:10`: Climax hit on *"Happily..."*.

**3. Timeline**

| Time | Fireworks | Lasers and lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **01:45 – 01:47** | None | White searchlight beams sweep & criss-cross behind castle | Red & gold scrollwork/tapestry projection; blue turret roofs | None |
| **01:48 – 01:50** | 2 red/gold comets shoot up; 2 red peonies burst left & right; high gold willow expands | White searchlights fan outward across sky | Unchanged (red/gold filigree) | None |
| **01:51 – 01:54** | Gold willow hangs and drifts downward above spire | Searchlights sweep back inward | Unchanged | None |
| **01:55 – 01:57** | Red comet pair shoots up; white/gold rooftop gerbs burst on ramparts | Searchlights widen | Unchanged | None |
| **01:58 – 02:01** | Large gold brocade willow blooms high over central spire | Searchlights criss-cross | Unchanged | None |
| **02:02 – 02:05** | 2 bright red comets shoot in V-shape; white gerbs fire on castle roof; central gold willow burst at spire | Searchlights move downward behind castle | Unchanged | None |
| **02:06 – 02:08** | Red comets launch; red peony burst detonates high center | Searchlights sweep outward | Unchanged | None |
| **02:09 – 02:12** | Gold fan/spray fires from roofline; massive gold willow blooms at high center | Searchlights fan into wide sky | Unchanged | None |

**4. Fireworks in the sky**
* **01:48 – 01:54:** 
  * 2 upward comets behind castle flanks.
  * 2 medium red peonies burst on the left and right of the upper spire.
  * 1 massive high-altitude golden willow/chrysanthemum shell opens high center and trails down slowly.
* **01:55 – 01:56:** Pair of bright red comets ascend vertically behind the castle.
* **01:58 – 02:01:** 1 massive golden brocade willow bursts high directly above the central spire.
* **02:02 – 02:04:** 2 bright red comets shoot diagonally outward in a mirrored 'V' formation.
* **02:04 – 02:06:** 1 medium golden dahlia/willow burst directly overhead at spire height.
* **02:07 – 02:08:** Red comets ascend; 1 vibrant red peony cluster bursts at high center.
* **02:10 – 02:12:** 1 massive golden willow canopy bursts high center.
* **Rhythm & counts:** Steady cadence matching the musical half-bars: launch comets every ~4 seconds, followed immediately by alternating red peonies and massive golden willow shells. Sky is never fully dark; lingering gold willow tendrils hang between shells.

**5. Fireworks on the castle**
* **01:56 – 01:58:** Low-level silver/white gerb fountains fire simultaneously from the lower left and right castle rooftops/ramparts.
* **02:03 – 02:05:** Second set of silver/white gerbs/fountains pulse upward along the mid-level ramparts.
* **02:08 – 02:10:** A golden gerb fan/cake effect fires outward from behind the upper castle parapets, creating a golden fan behind the upper spire.

**6. Lasers and lighting**
* **Searchlights:** ~8–10 white searchlight beams originating from behind the castle base sweep and criss-cross continuously in smooth fans against the dark sky.
* **Lasers:** No direct beam or graphic lasers are visible during this segment.
* **Surrounding lighting:** Deep blue wash lighting on the perimeter trees flanking the hub.

**7. The castle**
* **Base/Fixed Lighting:** Turret roofs remain deep royal blue with illuminated golden spire tips. Clock face is illuminated in warm white.
* **Projections:** Stationary architectural tapestry theme:
  * Ornate golden filigree, acanthus scrollwork, and stained-glass borders framing the castle walls and towers.
  * Deep crimson/red background fill on the facade panels.
  * The projection does not change scenes or fade during this chorus; it remains static and sharp to let the fireworks take center stage.

**8. Characters**
* **None:** No animated characters appear on the castle facade, in the sky, or anywhere in this segment.

**9. For our boards (LED matrix design priorities)**
1. **Red 'V' comets to Gold Willow canopy:** The signature visual is red comet pixels shooting upward in mirrored diagonal trails, followed by a wide cascade of slow-falling warm white/gold willow pixels filling the top of the matrix.
2. **Rooftop gerbs on downbeats (01:56 & 02:03):** 3–4 pixel-wide white/silver vertical spikes popping briefly on the castle shoulder ramparts right as the vocal line lands.
3. **Static Castle Palette:** The castle can be drawn with royal blue turret caps and a crimson body framed in gold, remaining static without animated character sprites.

**10. What you couldn't see**
* Exact ground-level mortar positions (hidden behind the castle).
* Peripheral ground fountains or low perimeter fireworks outside the camera's center frame.

**11. Our version**
* **What's right:** "Characters: none" is completely correct. The core colors (red, gold, white) are also accurate.
* **What's wrong:** Calling it "a red, gold and white strobe barrage" is inaccurate—these are discrete, majestic golden willow/brocade shells alternating with red comets and peonies, not an erratic strobe barrage. 
* **What's missing:** 
  1. The prominent ascending red comets (especially the 02:02 V-fan launch).
  2. The synchronized silver/white rooftop gerbs/fountains firing from the castle ramparts at 01:56 and 02:03.
  3. The sweeping white searchlight beams fanning out behind the castle.

</details>

### 2.2 Theme chorus (gold canopy)

- **Audio:** 128-137 s (2:08-2:17, 9 s) · **Video:** `--start 2:18 --end 2:27`
- **Our score now:** On the chorus drop the castle fades slowly to blue from the spire down to its base; a huge gold willow canopy over the spire, white comet fans firing off both sides, a gold brocade crown fading to smoke. Characters: none.
- **Checked by eye (2026-10-14):** on the chorus drop the castle fades slowly from its previous colours to blue, starting at the top and working down to the base (not a blue top over a gold base).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.7-flash · video 2:06-2:30 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **02:18** (musically and visually). At **02:18**, the climactic chorus begins with the lyric *"Find your happily ever after..."*, the castle projections begin shifting from warm red/gold scrollwork to royal blue, and at **02:19–02:20**, the signature massive gold canopy shell launches and explodes. 
* **End:** **02:27**, as the gold willow trails burn out into dark sky, the vocal phrase completes, and the castle settles into its solid blue-and-gold motif before the next musical transition.
* **Assessment of 02:09 to 02:27:** **02:09 is early** if referring strictly to the chorus and gold canopy. 02:09–02:17 is the pre-chorus build-up (*"It's just what's inside that you need to find..."*). The true "gold canopy chorus" starts at **02:18/02:19**.

**2. Music**
* **Song:** *"Happily Ever After"* (Theme song performed by Jordan Fisher and Angie Keilhauer).
* **Lyrics & Cues:**
  * **02:06–02:08:** *"...can reach..."*
  * **02:08–02:14:** *"...It's just what's inside that you need to find..."*
  * **02:14–02:18:** Orchestral build-up, drum roll, and choir swell (*"Ahhhh..."*).
  * **02:18–02:26:** Chorus hit: *"Find your happily ever after..."*
* **Key Musical Hits:**
  * **02:11:** Rhythmic percussion beat on the word *"find"*, cueing perimeter criss-cross comets.
  * **02:18:** Heavy orchestral downbeat on *"Find"*, signaling the chorus drop.
  * **02:20:** Massive cymbal/timpani crash on *"happily"*, perfectly hitting the detonation of the giant gold canopy.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **02:06 – 02:10** | High white/red bursts directly behind main spire; low gerbs/spark effects behind battlements. | White searchlights crossing dynamically behind the castle. | Warm red, gold, and turquoise rococo/heraldic scrollwork projection. | None. |
| **02:11 – 02:13** | Inward-angled white/gold comets shoot from far left and right, bursting into white strobing peonies high up. | White searchlights sweeping upward into vertical beams. | Warm scrollwork continues; clock face brightly lit yellow. | None. |
| **02:14 – 02:17** | Quiet sky; small gold spider/crossette burst behind upper spire at 02:16. | Searchlights spread outward in a wide V-shape fan. | Scrollwork projection remains steady during orchestral swell. | None. |
| **02:18 – 02:20** | Round bright orange/gold chrysanthemum burst high left-of-center at 02:19. | Searchlights pan across the sky. | Projection transitions: upper walls and spires turn royal sapphire blue; lower facade glows yellow/gold. | None. |
| **02:20 – 02:24** | **Giant gold brocade/kamuro canopy** detonates high dead-center above spire, drooping glittering tendrils across the entire sky. Thick angled gold comets fan out from ground left/right (02:21–02:23). | Bright white searchlights fan outward from behind the castle base. | Upper castle and spires illuminated in deep vivid royal blue; lower castle facade and gateway glow bright golden-yellow. | None. |
| **02:25 – 02:27** | Gold canopy willow streamers shimmer and drift down, slowly burning out. | Searchlights sweep gently back toward center. | Castle maintains blue spires and glowing gold base. | None. |
| **02:28 – 02:29** | Sky clears to dark. | Searchlights continue sweeping slowly. | Blue upper castle with golden base remains. | None. |

**4. Fireworks in the sky**
* **02:06–02:10:** A tight cluster of red and white peony/chrysanthemum bursts centered directly behind and slightly above the high central spire.
* **02:11–02:13:** Inward-angled comets fire in mirrored pairs from the left and right perimeters (approx. 4–6 comets), bursting at high altitude into a horizontal spread of flashing white strobes/peonies.
* **02:15–02:17:** Sky goes relatively quiet during the musical swell, punctuated only by a single gold spider/palm burst centered behind the spire.
* **02:19:** A single high, circular orange-gold chrysanthemum bursts high left-of-center.
* **02:20–02:26 (The Gold Canopy):**
  * **Type & Size:** A massive brocade crown / kamuro willow shell. Extremely large, expanding outward to span almost the entire upper frame.
  * **Height & Position:** Detonates high directly above the central spire, cascading long, slowly drooping golden willow tendrils that hang and twinkle as they fall toward the roofline.
* **02:21–02:23 (Side Comets):** Simultaneously, 6–8 thick, heavy-sparking golden comets launch from ground level to the left and right in outward-angled fans, framing the lower half of the gold canopy.

**5. Fireworks on the castle**
* **02:06–02:10:** Low-level white/silver fountains/gerbs fire upward from the castle ramparts and rear rooftops.
* **02:21–02:24:** Low golden glitter discharges/mine lift bursts visible emerging directly behind the lower castle flanks as the side comets fire.

**6. Lasers and lighting**
* **Lasers:** None visible or identifiable during this sequence.
* **Searchlights:** High-intensity white beam searchlights positioned behind and around the castle base:
  * **02:06–02:13:** Criss-crossing in rapid sweeping motions.
  * **02:14–02:18:** Holding vertical, then fanning outward into a wide "V".
  * **02:20–02:27:** Angled outward in a broad symmetrical fan, accentuating the spread of the gold canopy.
* **Flames & Fountains:** None on the castle or forecourt.

**7. The castle**
* **Projections (02:06–02:17):** The castle is wrapped in an ornate, baroque/Renaissance tapestry of red, gold, and teal filigree scrolls with glowing golden archways and clock face. 
* **Color Transformation (02:18–02:21):** On the chorus downbeat, the ornate filigree drops away. The upper half of the castle (all upper turrets, walls, and the main spire) shifts into **deep royal sapphire blue**.
* **Base & Clock (02:20–02:27):** The lower central castle facade and clock tower glow in a bright, warm **golden-yellow/amber**, creating a clean, high-contrast two-tone visual: brilliant gold at the base, rich blue at the top.

**8. Characters**
* **None.** No characters appear, are projected, or are formed by pyrotechnics during this entire segment (02:06–02:29). The focus is purely on architectural transformation and pyrotechnic spectacle.

**9. For our boards**
On a 64x32 or 64x64 LED matrix:
1. **The Pre-Chorus Comet Fan (02:11–02:13):** Shoot 2–3 white/gold diagonal lines from the bottom corners crossing toward center-high, ending in small twinkling white pixels.
2. **The Castle Color Shift (02:19–02:20):** Instant visual recognition requires switching the castle silhouette: drop the warm red/gold pattern and snap the top half/spire to vivid blue and the bottom facade to solid bright yellow-gold.
3. **The Gold Willow Canopy (02:20–02:26):** Detonate a single pixel high above the spire that expands rapidly into a wide umbrella of gold pixels, which then drift downward slowly with a twinkling/fading trail, accompanied by 2–3 angled gold lines shooting upward on each side.

**10. What you couldn't see**
* Ground-level launch tubes and castle base landscaping are obscured by tree silhouettes and foreground crowds.
* If any colored laser projections were present, they were completely obscured/washed out by the searchlight beams and pyrotechnic glare.

**11. Our version**
* **What's right:** The description of a huge gold willow canopy / brocade crown and the fact that there are **no characters**.
* **What's wrong:** Labeling it as a "palm" is inaccurate—this is classically a long-burning kamuro / brocade willow shell designed to weep and hang, not a quick-fading palm.
* **What's missing:**
  1. The pre-chorus build-up comets and strobes at 02:11–02:13.
  2. The single orange-gold burst at 02:19 that prefaces the main canopy.
  3. The angled gold comet plumes shooting up from the flanks (02:21–02:23).
  4. The dramatic castle color transformation right as the canopy hits: changing from red/gold filigree to royal sapphire blue on the spires with a glowing gold base.

</details>

## 3. Dreams (audio 2:17-5:03, video 2:27-5:13)

### 3.1 Wishing star lands on the castle

- **Audio:** 137-147 s (2:17-2:27, 10 s) · **Video:** `--start 2:27 --end 2:37`
- **Our score now:** Music-box transition: the castle turns royal blue, the sky dark, one bright star. Characters: none.
- **Checked by eye (2026-10-14):** the wishing star shoots across the sky and lands directly on the castle.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.7-flash · video 2:24-2:43 · notes: none</summary>

Here is the detailed breakdown of the segment:

**1. Where this part starts and ends**
* **Starts at 02:29:** The lingering golden fireworks and searchlights from the opening fanfare fade out, the choir vocal finishes, and the castle abruptly transitions from vibrant gold/red heraldry to a quiet royal blue. *(Your 02:27 is slightly early—that is still the tail of the opening pyro finale).*
* **Ends at 02:41:** The single shooting star/comet completes its diagonal descent across the castle facade, and the introductory lyric finishes. *(Your 02:40 is 1 second early; the star lands/disappears at 02:41).*

**2. Music**
* **Song:** Transition from the title theme (*Happily Ever After* opening fanfare) into the quiet ballad introduction.
* **Audio sequence:**
  * **02:24 – 02:27:** Full choir and orchestra hold the climactic chord: *"...ever after! Ooh-oh..."*
  * **02:28 – 02:30:** Orchestra and choir fade into a quiet celesta/chime twinkle.
  * **02:31 – 02:36:** Soft, atmospheric string and wind interlude; sky is silent.
  * **02:37 – 02:41:** Gentle female solo vocal begins: *"Even stars..."* (02:37–02:39) *"...can shine..."* (02:40–02:41). The shooting star moves exactly on this vocal phrase.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **02:24 – 02:27** | Massive gold willow shell overhead; lower angled comets from castle base. | Bright white searchlights criss-crossing in sky. | Bright red, gold, and yellow projections. | None. |
| **02:28 – 02:30** | Overhead gold sparks fade out to dark. | Searchlights fade completely out. | Projections fade into dark royal blue wash. | None. |
| **02:31 – 02:36** | Sky completely dark and silent. | No searchlights or lasers. | Saturated deep royal blue; cyan on spires; warm glowing clock face. | None. |
| **02:36 – 02:38** | Sky dark. | No searchlights or lasers. | Stained-glass arched window fades in at center base. | Small figure appears inside arched window. |
| **02:39 – 02:41** | 1 single golden comet/star streaks from upper-left spire diagonally down-right. | No searchlights or lasers. | Deep blue castle; illuminated window at center base; star passes across. | Figure inside illuminated window gazes upward. |

**4. Fireworks in the sky**
* **02:24 – 02:27:** 1 large golden willow/chrysanthemum canopy bursting high center above the spire, trailing golden glitter down.
* **02:28 – 02:38:** **Complete silence/blackout.** Zero sky bursts.
* **02:39 – 02:41:** **1 single golden comet ("wishing star"):**
  * **Type:** Low-velocity golden comet / star shell with a luminous sparkling tail.
  * **Position & trajectory:** Starts mid-high (just to the left of the main high spire, about 2/3 castle height) and arcs gently downwards toward the right turret roof.
  * **Count:** Exactly 1.

**5. Fireworks on the castle**
* **02:24 – 02:26:** White/gold angled comet fans shooting outwards from the perimeter walls behind the castle base.
* **02:27 – 02:38:** None.
* **02:39 – 02:41:** The wishing star comet is launched from the castle structure/upper turrets behind the main spire.

**6. Lasers and lighting**
* **02:24 – 02:27:** Searchlights (white/cool blue) sweep upward from the hub area in angled beams.
* **02:28 – 02:42:** **No searchlights, no lasers, no flames, no fountains.** The surrounding sky is left completely black, relying purely on castle projection mapping.

**7. The castle**
* **02:24 – 02:27:** Bright gold and crimson heraldic textures covering the entire facade.
* **02:28 – 02:30:** Rapid dissolve into deep royal blue / navy wash across all walls.
* **02:31 – 02:35:** Turret cones and spire edges glow in soft cyan/turquoise; the central clock face glows with warm golden light.
* **02:36 – 02:42:** A warm, colorful arched stained-glass frame projection fades onto the central lower facade (just above the main entrance gate).

**8. Characters**
* **02:24 – 02:35:** None.
* **02:36 – 02:42:**
  * **Who:** A single figure (unsure of exact character due to scale, but standing inside a framed stained-glass window).
  * **Location:** Center-bottom (grid row 3, column 2 / above the main gate).
  * **Size:** Very small, roughly 1/8 the castle's height.
  * **Movement:** Fades in statically inside the glowing archway, facing up toward the sky as the wishing star streaks across.

**9. For our boards (LED matrix 64×32 / 64×64)**
1. **The Blackout Contrast (02:29):** The sky matrix must go completely black at 02:29 while the castle shifts from bright amber/gold to deep royal blue (`#001144` / `#000088`), leaving only a warm yellow pixel/cluster for the clock face.
2. **The Moving Wishing Star (02:39 – 02:41):** It must **not** be a stationary star. An authentic rendition requires a single bright warm-white/gold pixel (with a 1–2 pixel trailing fade) to travel diagonally across the upper castle silhouette from `(x: ~28, y: ~10)` down-right to `(x: ~42, y: ~22)` over 2 seconds.
3. **The Lower Arch Glow (02:36):** A small 3×3 or 4×4 warm-toned cluster (amber/pink/cyan) lighting up above the entrance archway before the star shoots.

**10. What you couldn't see**
* **Indistinct character identity:** At 02:36–02:42, the exact character inside the lower arched projection window is too small and backlit to confirm with certainty (unsure).
* **Launch mechanism:** The exact pyro mortar location behind the upper-left spire is occluded by the tower wall.

**11. Our version**
* **What's right:** The castle turning royal blue; the sky going dark.
* **What's wrong:**
  * *"One bright star"*: It is not a static star hanging in the sky; it is a **shooting comet** moving diagonally across the castle.
  * *"Characters: none"*: An illuminated window projection showing a character appears at the base center at 02:36.
* **What's missing:**
  * **Timing:** The star does not appear when the castle turns blue (02:30); it shoots across between **02:39 and 02:41**, synchronized to the vocal line *"Even stars can shine"*.
  * **Accent colors:** The illuminated yellow clock face and the cyan spire tips contrasting against the royal blue body.

</details>

### 3.2 Down in New Orleans (prologue)

- **Audio:** 147-171 s (2:27-2:51, 24 s) · **Video:** `--start 2:37 --end 3:01`
- **Our score now:** Midnight blue, Evangeline the evening star twinkling, small single comets. Characters: Tiana, Ray.
- **V2:** stage ghost; actors ray (Ray loops a figure-eight by the evening star).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.7-flash · video 2:37-3:04 · notes: none</summary>

Here is the detailed breakdown of the segment for your LED matrix recreation:

**1. Where this part starts and ends**
* **Starts:** **02:38** — Young Tiana begins singing the prologue (*"The evening star..."*). Your suggested timestamp of 02:40 is about **2 seconds late**.
* **Ends:** **03:01** — The quiet vocal ballad ends as the sustained note on *"...can happen"* fades, immediately hit by a syncopated jazz brass fanfare at **03:01** accompanied by an energetic comet fan launch. Your timestamp of 03:01 is **exact**.

**2. Music**
* **Song:** *"Down in New Orleans (Prologue)"* from *The Princess and the Frog*, performed by young Tiana.
* **Lyrics:**
  * **02:38 – 02:44:** *"The evening star is shinin' bright..."*
  * **02:44 – 02:49:** *"So make a wish and hold on tight..."*
  * **02:50 – 02:55:** *"There's magic in the air tonight..."*
  * **02:56 – 03:00:** *"And anything can happen..."*
* **Big Musical Hit:**
  * **03:01:** The slow, wistful ballad abruptly shifts as upbeat Dixieland jazz brass accents the start of the full *"Down in New Orleans"* sequence.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **02:37 – 02:39** | None | Slow cyan moving spotlights sweeping right facade | Deep midnight blue with wrought-iron filigree | Young Tiana visible in center arch window |
| **02:40 – 02:43** | Single gold comet launches behind mid-right | Cyan beams continue drifting | Blue wash; bright gold star pulsing on upper tower | Young Tiana gazing out from window |
| **02:44 – 02:47** | Small gold spark/gerb flash on lower right turret roof (02:45) | Subtle blue ambient light | Greenish-gold bayou foliage around clock face | Young Tiana singing |
| **02:48 – 02:55** | Tiny faint tracer rising upper-right sky (02:50) | Cyan searchlight beams cross upper spires | Deep blue starry projections on towers | Young Tiana singing |
| **02:56 – 03:00** | Sky dark | Spotlights steady | Blue wash holds steady | Young Tiana holds final vocal note |
| **03:01 – 03:04** | Fan of 3 bright white/gold comets launches upward-left | Front spotlights intensify | Castle lighting shifts for upbeat jazz segment | Transition to main sequence |

**4. Fireworks in the sky**
* **02:40 – 02:43:** 1 single low/mid-height golden comet launches from behind the castle on the **right side**, arcs slightly, and burns out into faint gold sparks well below the main spire.
* **02:50:** 1 tiny, faint projectile/tracer rising into the dark sky on the far upper-right.
* **03:01 – 03:04:** Exactly on the jazz brass beat, a fan of **3 bright white/gold comets** with thick sparkling tails launches simultaneously from behind the castle on the **left side**, sweeping up and out toward the top-left at roughly 45–60° angles.
* **Rhythm:** Sky is completely quiet and dark for 90% of this section, providing emotional breathing room before the high-energy 3-comet hit at 03:01.

**5. Fireworks on the castle**
* **02:45 – 02:46:** A small, momentary gold sparkle/gerb flash ignites on the **lower right turret roof / parapet ledge**.

**6. Lasers and lighting**
* **Lasers:** None visible during this quiet prologue.
* **Searchlights / Moving Heads:** Faint cyan/blue architectural beam spotlights positioned around the hub/moat sweep slowly and smoothly across the right side of the castle facade and into the night sky.
* **Flames / Fountains:** None.

**7. The castle**
* **Castle Wash:** Solid dark midnight blue and royal blue floodlighting across the spires, walls, and side turrets.
* **Projections:**
  * Dark blue and cyan swamp vegetation, hanging moss, and New Orleans wrought-iron balcony patterns along the walls.
  * A cluster of tiny twinkling white stars across the central tower.
  * A distinct, brilliant **golden/white star** (the Evening Star / Evangeline) pulsing brightly on the mid-upper tower shaft just below the main spire.
  * A circular medallion of soft green/gold bayou filigree framing the castle clock face.
  * A warmly lit, amber/yellow interior window frame projected directly over the central entrance arch.

**8. Characters**
* **Young Tiana:**
  * **Location:** Castle base / center archway directly above the gateway (Grid: **Bottom-Center**).
  * **Size:** Confined inside the projected window frame (about 1/6 to 1/7 of the castle's height).
  * **Movement:** Stands inside a warmly lit room in her yellow dress, resting her arms on the window sill/railing, gently swaying and looking upward toward the evening star.
  * **Presence:** Projected throughout the entire segment (02:37 – 03:01).
* **Ray (the firefly):** **Not present**. Ray does not appear anywhere in this sequence.

**9. For our boards (LED matrix recreation)**
1. **The Vertical Star-to-Window Line:** The visual core is contrast: a small, warm **amber lit window with a silhouette of Young Tiana** at the bottom-center, gazing up at a single **bright, pulsing gold pixel cluster (Evangeline)** placed high on the mid-upper spire against a dark midnight-blue castle silhouette.
2. **Minimal Pyro Rhythm:** Keep the sky completely dark except for **one single rising gold comet on the right** at 02:40, followed by complete stillness until the musical hit.
3. **The 03:01 Fan Hit:** Time a sharp fan of **3 bright white/gold comets shooting left** to the exact frame the Dixieland jazz brass drops at 03:01.

**10. What you couldn't see**
* Any perimeter/wide rooftop pyro launched far off to the sides outside Magic Kingdom is cut off by the relatively tight camera framing on Cinderella Castle.
* The lowest footings of the castle bridge/gate are obscured by spectators' silhouettes in the foreground.

**11. Our version**
* **What's right:** Midnight blue base wash; Evangeline (the evening star) twinkling high on the castle; small single comet during the verse; Tiana is present.
* **What's wrong:**
  * **Ray is not in this sequence**—remove him.
  * Tiana is specifically **Young Tiana** as a child, seen inside an amber-lit bedroom window at the base, not adult Princess Tiana.
* **What's missing:**
  * The **amber/yellow lit window frame** at the castle base where young Tiana stands (crucial color contrast against the all-blue castle).
  * The **spark flash on the lower-right turret** at 02:45.
  * The **fan of 3 angled comets to the left** at 03:01 that transitions the ballad into the upbeat jazz section.

</details>

### 3.3 When You Wish Upon a Star (fanfare)

- **Audio:** 171-192 s (2:51-3:12, 21 s) · **Video:** `--start 3:01 --end 3:22`
- **Our score now:** The castle bright blue as the fanfare plays: a fan of white comets off the rooftops (video 3:05), blue searchlights, white and ice-blue bursts, a green willow at the end. Characters: Ray.
- **V2:** stage castle; actors ray (Ray drifts over and circles the spire).
- **Checked by eye (2026-10-14):** Ray isn't clearly visible; keeping him in 3.3's first seconds is fine but not required.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 2:58-3:25 · notes: none</summary>

Here is the detailed breakdown of the segment:

**1. Where this part starts and ends**
* **Start:** **03:01**. The gentle closing vocal of the *Princess and the Frog* section ("...and happy") ends right at 03:00. At 03:01, a loud, triumphant brass fanfare of "When You Wish Upon a Star" begins, instantly punctuated by upward-shooting white/gold comets at 03:02.
* **End:** **03:21**. The fanfare reaches its concluding swell and resolves into the gentle intro harp/strings of *The Little Mermaid* ("Part of Your World") as the vocals begin at 03:22 ("Look at this stuff..."), accompanied by a color shift and a high red peony.
* **Assessment of 03:01 to 03:22:** The provided range of **03:01 to 03:22 is spot-on**.

**2. Music**
* **Music:** Orchestral brass fanfare arrangement of "When You Wish Upon a Star" (Leigh Harline / Ned Washington).
* **Lyrics:** None. This is an instrumental fanfare transition. (The prior vocal ends with "...and happy" at 03:00, and Ariel begins singing "Part of Your World" at 03:22).
* **Key Musical Hits:**
  * **03:01–03:02:** First triumphant brass chord strike (launches initial comet fan).
  * **03:04–03:06:** Sustained brass crescendo with rising flourishes.
  * **03:09–03:10:** Sharp orchestral accent (hits on twin gold chrysanthemum bursts).
  * **03:16–03:17:** Secondary melodic accent (hits on white strobing burst).
  * **03:19–03:20:** Melodic resolution phrase (hits on green peony bursts).
  * **03:21–03:22:** Fanfare climax and bridge chord leading into the next song (hits on red peony and central gold burst).

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **03:01** | Silence/dark in sky. | Blue/cyan uplighting on lower castle walls. | Royal blue base with stained-glass motifs; star begins glowing on spire. | Ray (firefly) fading out at lower gate arch. |
| **03:02–03:07** | Symmetrical fan of 10+ thick gold comets with white heads shooting upward behind castle. | Searchlight beams start rising behind the parapets. | Saturated blue brickwork with starry texture; bright pulsing white star on spire. | None. |
| **03:08–03:09** | Comets extinguish; brief dark pause in sky. | Six bright cyan/white searchlight beams fan outward from castle base into the sky. | Blue facade remains; spire star shines steadily. | None. |
| **03:09–03:12** | Twin symmetrical gold chrysanthemums burst at mid-height left and right of spire. | Searchlight fan holds steady angled upward. | Deep blue facade, lower stained-glass arch lit. | None. |
| **03:13–03:15** | Gold chrysanthemums fade to dark. | Beams remain stationary pointing to upper sky. | Deep blue with shimmering starfield projection. | None. |
| **03:16–03:18** | White strobe/crossette burst blooms high to the left of the spire. | Beams steady. | Castle maintains blue/purple starlight mapping. | None. |
| **03:18–03:21** | Emerald green peony bursts bloom to the left and center-left of the spire. | Lower blue floodlights begin warming slightly at the base. | Transitioning away from blue toward aquatic tones. | None. |
| **03:21–03:22** | Symmetrical explosion: Ruby red peony high left, large gold willow burst directly behind top spire. | Searchlight beams widen and fade back. | Palette shifts toward oceanic teal/purple for *The Little Mermaid*. | None. |

**4. Fireworks in the sky**
* **03:02–03:07 (Comet Fan):** A simultaneous, symmetrical upward fan of approximately 10 to 12 thick golden glitter comet trails with white-hot tips. They launch from behind the castle roofline and spread outward left and right, rising past spire height.
* **03:09–03:12 (Twin Gold Chrysanthemums):** Exactly 2 mirrored gold chrysanthemum shells burst simultaneously at mid-high altitude (level with upper spire), one on the left flank, one on the right flank.
* **03:16–03:18 (White Strobe Burst):** 1 medium-to-large white/silver strobing glitter shell blooming high to the left of the spire.
* **03:18–03:21 (Green Peonies):** 2 successive emerald-green peony bursts blooming on the left side at mid-height, drifting downward slightly with soft green stars.
* **03:21–03:22 (Transition Burst):** 1 high ruby-red peony to the upper left and 1 large golden brocade/willow exploding dead-center behind the castle spire peak.
* **Rhythm:** Starts with a dense, fast sweeping barrage (03:02–03:07), pauses for roughly 1.5 seconds of dark sky (03:08), hits a crisp symmetrical 2-shell accent (03:09), pauses (03:13–03:15), then provides spaced rhythmic color accents (white at 03:16, green at 03:18–03:20) before the climactic bridge blast at 03:21.

**5. Fireworks on the castle**
* None launched directly from the castle turrets, parapets, or balconies during this specific fanfare window. All pyrotechnics launch from perimeter launch locations behind the structure.

**6. Lasers and lighting**
* **Lasers:** None visible during this window.
* **Searchlights:** At 03:08, a bank of 6 visible pale-blue/cyan searchlight beams shoot upward from behind the hub/forecourt flanking both sides of the castle, fanning outward into the night sky at static angles throughout 03:09–03:21.
* **Flames / Fountains:** None.

**7. The castle**
* **Base & Flood Lighting:** Saturated royal blue and violet floodlighting washing over the lower walls and side turrets.
* **Projections:**
  * **Spire:** A bright, glowing white/cyan 4-pointed star (Evangeline / Wishing Star motif) projected directly over the central upper tower spire, pulsing slightly.
  * **Facade:** A midnight-blue field sprinkled with fine twinkling stars covering the main walls. At the bottom center (around the main archway), remnants of warm gold/green stained-glass floral framing linger until ~03:08, after which the whole facade becomes uniformly deep blue and starry.

**8. Characters**
* **02:58–03:01:** Ray (the firefly) from *The Princess and the Frog* appears as a tiny glowing green/yellow point of light at the bottom center (grid: bottom-center, over the gateway arch), roughly 1/20th of the castle height. He fades out completely as the fanfare hits at 03:01.
* **03:01–03:21:** **No characters appear** on the castle or in the sky during the fanfare. Only the abstract glowing Wishing Star on the top spire is present.

**9. For our boards (LED matrix recreation)**
1. **The 03:02 Comet Fan:** On 64x32 or 64x64, render a symmetrical V-shaped fan of bright white pixels trailing gold upward from behind the castle silhouette, synced to the brass strike.
2. **The Twin Gold Bursts at 03:09:** Two symmetrical circular clusters of gold pixels bursting left and right of the spire against an otherwise empty black sky.
3. **Spire Star & Color Contrast:** Keep the castle body dark blue with a single brilliant white/cyan flashing pixel (or 2x2 cluster) pinned to the very tip of the spire throughout the 20-second fanfare.

**10. What you couldn't see**
* Pyrotechnic ground launch tubes are fully hidden behind the castle facade.
* Lower perimeter searchlight fixtures themselves are obscured behind trees and hub architecture; only their skyward beams are visible.

**11. Our version**
* **What's right:** The pyrotechnic types are accurate: the brass fanfare features a fan of white/gold comets, gold chrysanthemums, and green and white glitter bursts.
* **What's wrong:** "Characters: Ray" is incorrect for this segment. Ray exists only in the preceding song and fades away right at 03:01 as the fanfare begins. During the fanfare itself (03:01–03:21), no characters are on display.
* **What's missing:**
  * The bright glowing Wishing Star projected on the central upper spire.
  * The prominent upward cyan/blue searchlight beam fan starting at 03:08.
  * The concluding ruby-red burst and gold willow at 03:21 that caps the fanfare and introduces Ariel's segment.

</details>

### 3.4 Part of Your World

- **Audio:** 192-215 s (3:12-3:35, 23 s) · **Video:** `--start 3:22 --end 3:45`
- **Our score now:** Blue castle: a red peony over the spire (video 3:23), then big gold chrysanthemums, a white one, and gold and white comet fans off both sides (3:39-3:42). Characters: Ariel.
- **Checked (2026-10-13):** Gemini's answer below says 3:22-3:30 is the end of Moana's song; it can't be, Moana's is at 5:36 onward. Treat its start-of-scene claim (3:31) as unchecked.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 3:19-3:48 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** Exactly at **03:31 - 03:32**. The previous crescendo (the finale chord of Moana’s *How Far I’ll Go*, culminating in the massive gold willow at 03:25–03:30) fades out completely. At 03:31–03:32, the show transitions with a gentle harp/piano arpeggio intro for *Part of Your World*, accompanied by bubbling water sound effects and underwater acoustic ambiance.
* **End:** The prompt notes 03:45, but *Part of Your World* does **not** end at 03:45; it continues well past 03:47 (the end of the clip). At 03:44–03:45, the vocal melody only just begins (*"Up where they walk..."*).
* **Evaluation of your 03:22 to 03:45:** 
  * **03:22 is too early:** 03:22–03:30 is the grand finale hit of the preceding song (*How Far I'll Go*), marked by a massive red shell and huge golden weeping willow/kamuro canopy. 
  * **03:45 is too early to end:** 03:45 is the very first line of sung lyrics (*"Up where they walk..."*), meaning the *Part of Your World* segment is just getting underway.

**2. Music**
* **Music:** *Part of Your World* from *The Little Mermaid* (Alan Menken / Howard Ashman).
* **Lyrics & Musical Hits:**
  * **03:22–03:26:** Powerful orchestral resolution/cymbal crash from the previous song (*How Far I'll Go*).
  * **03:31–03:33:** Delicate harp/piano underwater arpeggios introduce *Part of Your World*.
  * **03:36–03:38:** Orchestral swelling flute and string phrase as ground fans fire.
  * **03:44–03:47:** Solo female vocal (Ariel) begins singing: *"Up where they walk..."* (03:44–03:46), *"Up where they run..."* (03:46–03:47).

**3. Timeline**

| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **03:19–03:21** | Green & gold bursts fade on left/right | Deep blue castle wash, dual angled cyan searchlight beams | Royal blue/indigo wash with greenish aquatic light | None visible |
| **03:22–03:25** | Climax hit: 1 red peony (upper left), 1 golden chrysanthemum (center-right) expanding into massive gold kamuro/willow | Bright blue base lighting; diagonal blue searchlights | Electric blue with purple and cyan under-glow | None visible |
| **03:26–03:31** | Gold willow trails drizzle slowly downward past spires | Blue searchlights sweep slightly; blue floodlights | Deep ocean blue, subtle water ripples | None visible |
| **03:32–03:35** | Low/mid sky quiet; small central burst/comet directly behind main spire (03:34) opening into a modest gold/orange peony (03:35) | Dual searchlights cross from sides; soft blue facade light | Deep sea blue with animated rising air bubbles | None visible |
| **03:36–03:42** | Mirrored fans of gold comet tails/mines fire upward from both left and right flanks; high center burst expands into a shimmering gold spider/willow | Blue/cyan uplighting; blue searchlight beams sweeping upward into the night sky | Projections shift to sea-cave/grotto motifs with rising luminous bubbles | **Ariel** appears projected inside the central window/archway (03:36) |
| **03:43–03:47** | Single red peony burst high center-left behind spire (03:45–03:46) with residual gold trails | Pink/red and cyan back-glow complementing the red shell; blue side searchlights | Underwater grotto with floating particles/bubbles | Ariel remains visible in center archway reaching upward |

**4. Fireworks in the sky**
* **03:22–03:31 (Preceding song finale):**
  * *03:22–03:24:* 1 vivid ruby-red peony high left, paired with 1 dense gold brocade/chrysanthemum center-right.
  * *03:25–03:30:* The gold burst expands into a massive, sky-filling weeping willow/kamuro that drifts slowly downward past the castle spires.
* **03:32–03:35:**
  * Sky goes mostly dark/quiet.
  * *03:33–03:35:* 1 small gold comet launches straight behind the spire, bursting into a modest gold-orange peony at spire height.
* **03:36–03:42:**
  * *Lower sky flanks:* Angled fan mines/comet tails (approx. 5–6 trails on each side) shoot outward in synchronized mirrored fans of warm gold/glitter from behind the hub perimeter treeline.
  * *High center:* 1 large golden willow/chrysanthemum shell blooms centered directly above the highest spire, raining soft golden tendrils down behind the castle.
* **03:44–03:47:**
  * *03:44–03:46:* 1 medium ruby-red peony blooms high in the sky just to the left of the main spire as the vocal line starts, followed by a secondary faint burst to the right.
* **Rhythm:** Highly punctuated. It drops from a dense, full-sky barrage (03:25) to complete tranquility (03:31–03:33), followed by deliberate, single-accent bursts and angled fan lifts timed directly to the gentle musical beats (roughly 1 shell every 4–5 seconds).

**5. Fireworks on the castle**
* None fired directly from the castle itself (no rooftop gerbs, battlements strobes, or turret fountains fire during 03:31–03:47). All fireworks during this sequence launch from perimeter launch sites or backstage launch points behind the castle.

**6. Lasers and lighting**
* **Lasers:** No visible thin-beam lasers are projected into the sky during this section.
* **Searchlights:** Four main high-intensity blue/cyan searchlights located on the perimeter/hub roofs. They cast stationary or slowly sweeping vertical/diagonal light beams framing the castle (two angled on the left, two on the right).
* **Fountains/Flames:** None active in this segment.

**7. The castle**
* **Base Architectural Lighting:** Deep oceanic royal blue and navy wash the lower walls, turrets, and spires. 
* **Window/Accent Lighting:** Windows glow with soft amber/cyan backlighting.
* **Projections:**
  * *03:31–03:35:* Deep underwater ambiance with soft, bioluminescent green and cyan aquatic ripples and floating bubble patterns drifting upwards across the towers and main facade.
  * *03:36–03:47:* The central facade transitions to King Triton's sunken grotto / underwater rock cavern textures, surrounded by glowing green-cyan water textures.

**8. Characters**
* **Ariel:**
  * **Who:** Ariel (from *The Little Mermaid*), shown from the waist/chest up with her signature flowing red hair.
  * **Position:** Grid center / mid-level center (projected directly inside the upper center recessed balcony/window archway above the main gate and below the tallest spire).
  * **Size:** Approx. 15–20% of the castle's height (confined to the central architectural frame).
  * **Movement:** Fades in smoothly at **03:36**; she moves gently, looking upward and gesturing with her arms as if floating/swimming underwater and looking up toward the surface of the sea. She remains there through the end of the clip (03:47).

**9. For our boards**
1. **The Dramatic Color/Energy Shift (03:30–03:32):** Transition instantly from high-energy gold willow drizzle down to a dead-quiet, moody navy-blue castle with slow, tiny rising cyan/green LED "bubbles".
2. **The Mirrored Fan Comets (03:36):** Fire synchronized low angled gold comets fanning outward on both the left and right edges of the display while a single gold willow blooms overhead.
3. **Ariel & First Red Accent (03:36 & 03:45):** Display a small red-haired figure silhouette in the middle-center window frame at 03:36, followed by a crisp, single red peony burst at high top-left on the lyric *"Up where they walk"* (03:45).

**10. What you couldn't see**
* Lower ground level in front of the castle moat is occluded by crowd heads and trees.
* Left and right perimeter pyrotechnic launch mortars are off-screen (only their rising comet trails/bursts are visible).

**11. Our version**
* **What's right:** "Underwater turquoise and navy, glowing bubbles" and "Ariel" are completely accurate and capture the exact atmosphere of the castle projection.
* **What's wrong:** "Sparse gold willows dripping over the spires" belongs strictly to the transition *out* of the previous Moana song (03:25–03:30) and the single shell at 03:36–03:40. It is not continuous dripping.
* **What's missing:**
  1. The **mirrored gold comet fan lifts** from the lower left and right flanks at **03:36**.
  2. The distinct **ruby-red peony shell** bursting high left at **03:45** on the very first lyric (*"Up where they walk..."*).
  3. The static/angled **cyan-blue searchlight beams** framing the sides of the castle.

</details>

### 3.5 Out There

- **Audio:** 215-256 s (3:35-4:16, 41 s) · **Video:** `--start 3:45 --end 4:26`
- **Our score now:** Notre Dame by night: the castle icy blue, the bells ringing, the sky mostly dark under purple searchlights; a red peony on "Out there" (video 4:07) and a big white chrysanthemum on the last note (4:25). Characters: Quasimodo.
- **Checked by lyrics (Whisper on our audio, 2026-10-13):** this is **"Out There"** (*The Hunchback of Notre Dame*), not Part of Your World: "Out there… strolling by the Seine, taste the morning air… just one day and then I swear I'll be content" from audio 215 s, its last "Out there!" at 254 s. Gemini's answer below (Quasimodo, the Notre Dame rose window) agrees. The score's title, characters and look for this scene are wrong.
- **Checked by eye (2026-10-14):** Quasimodo, confirmed. No doves anywhere: drop them.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 3:42-4:29 · notes: none</summary>

Here is the detailed breakdown of the segment:

**1. Where this part starts and ends**
* **Starts:** **03:44 - 03:45**. The prior musical phrase resolves, and Quasimodo’s solo vocal begins on the lyric *"Out there..."* as a ruby/red peony bursts directly above the central spire. 
* **Ends:** **04:26**. The sustained vocal and brass hit of *"Out there!"* finishes under a large golden brocade burst. At **04:26 - 04:27**, the song transitions abruptly into *Brave* ("Touch the Sky") with rapid magenta comet fans firing from both sides.
* **Accuracy of 03:45 to 04:26:** Your timestamp window is **exact**, but the song identification is **incorrect**. This section is not *The Little Mermaid* ("Part of Your World"); it is Quasimodo singing "Out There" from *The Hunchback of Notre Dame*.

**2. Music**
* **Song:** "Out There" from *The Hunchback of Notre Dame* (Music by Alan Menken, Lyrics by Stephen Schwartz).
* **Lyrics & Cues:**
  * **03:44 – 03:48:** *"Out there, strolling by the Seine..."*
  * **03:49 – 03:56:** *"Taste a morning out there, like ordinary men..."*
  * **03:56 – 04:00:** *"...who freely walk about there..."*
  * **04:00 – 04:07:** *"Just one day and then I swear I'll be content..."*
  * **04:08 – 04:12:** *"...with my share..."*
  * **04:12 – 04:14:** *"Won't resent,"* (rhythmic orchestral stabs)
  * **04:14 – 04:16:** *"won't despair,"*
  * **04:16 – 04:18:** *"old and bent, I won't care,"*
  * **04:18 – 04:22:** *"I'll have spent one day..."* (crescendo)
  * **04:23 – 04:26:** *"...out there!"* (massive climactic high note, orchestral swell, and brass resolution).

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **03:44** | Comets from prior sequence fade | Blue searchlights sweep upward | Transitions to Gothic stone & blue facade | Segment transition |
| **03:45 – 03:48** | Red/ruby peony above spire | Upward blue beams flank the castle | Gothic facade; glowing stained-glass rose window | Quasimodo appears below the rose window |
| **03:52 – 03:55** | Red/orange peonies burst left and right of spire | Blue searchlights steady, angled outward | Stained glass glows bright amber/blue | Quasimodo moving along balustrade |
| **03:59 – 04:01** | Gold peony (upper left), red peony (upper right) | Blue searchlights maintain V-formation | Deep royal blue towers, illuminated stone patterns | Quasimodo perched by gargoyle/column |
| **04:05 – 04:08** | Large ruby/magenta peony over spire | Blue beam arrays steady | Castle facade stone patterns ripple with light | Quasimodo singing, gesturing outward |
| **04:08 – 04:12** | Red/gold trailing peony to upper right | Searchlights angled high | Deep blue with bright central rose window | Quasimodo in central archway |
| **04:13 – 04:21** | Sky dark/quiet during rapid vocal stabs | Searchlight beams remain locked upward | Rose window pulsates subtly to the rhythm | Quasimodo silhouette in center alcove |
| **04:23 – 04:26** | Large golden brocade/willow shell blooms high above spire | Blue searchlights flare; castle wash intensifies | Gothic architecture fully illuminated in blue/gold | Quasimodo holds final climactic pose |
| **04:26 – 04:28** | Dense fan of hot-magenta comets/mines shoots left & right | Lighting flashes purple/magenta | Projections begin changing toward Celtic patterns | Quasimodo fades out |

**4. Fireworks in the sky**
* **03:45:** Single medium ruby-red peony directly over the main spire.
* **03:53:** Pair of medium orange/red peonies flanking the upper spire (1 left, 1 right).
* **03:59 – 04:01:** Staggered pair: 1 gold/amber peony high left, followed by 1 red peony high right.
* **04:05 – 04:08:** Large, vibrant ruby peony centered high over the spire.
* **04:09:** 1 red chrysanthemum with trailing gold tails on the upper right.
* **04:12 – 04:22 (Quiet pause):** The sky is deliberately kept clear and dark during the rhythmic vocal lines (*"Won't resent, won't despair..."*) to build dramatic tension.
* **04:23 – 04:26 (Climax):** A massive gold brocade / weeping willow shell detonates high dead-center above the spire, cascading broadly across the entire upper sky.
* **04:26+:** Synchronized angled fans of bright magenta comets/mines erupt from low ground launch positions flanking both sides of the castle (transitioning to *Brave*).

**5. Fireworks on the castle**
* No perimeter gerbs, turret fountains, or rooftop Roman candles are fired from the physical castle structure during this specific ballad section. All pyrotechnics launch from the rear launch site behind the castle.

**6. Lasers and lighting**
* **Searchlights:** Four primary upward-pointing blue architectural searchlight beams flank the castle (two left, two right), set in an outward V-angle pointing high into the night sky throughout the song.
* **Lasers:** No sharp horizontal beam arrays or scanning graphics; lighting is dominated by deep atmospheric blue washes.

**7. The castle**
* **Base & Turret Lighting:** Saturated royal blue and cobalt on all turrets, roofs, and side spires.
* **Projections:** 
  * Features the Gothic architecture of **Notre Dame de Paris**.
  * Center: A prominent, ornate circular stained-glass **rose window** glowing in rich blues, violets, and warm gold.
  * Flanking walls: Gothic archways, stone tracery, flying buttresses, and cathedral column textures projected over the castle stonework.

**8. Characters**
* **Quasimodo** (*The Hunchback of Notre Dame*):
  * **Location:** Center and Center-Bottom (grid positions [2,2] and [3,2]), positioned directly inside the gothic archway beneath the rose window.
  * **Size:** Approximately 1/5 to 1/4 the height of the main castle facade.
  * **Movement:** Animated climbing across cathedral stonework, moving between columns, leaning over balustrades, and looking out yearningly toward the audience before holding an outstretched pose at the musical climax (**04:23 - 04:26**).
  * **Duration:** Appears at **03:45** and fades out at **04:26**.
* **Ariel:** Does **not** appear in this sequence.

**9. For our boards (LED Matrix recreation)**
1. **Castle Facade:** Render the castle body in deep royal blue with a glowing multicolored circular stained-glass "rose window" in the center.
2. **Pyrotechnic Rhythm:** Keep bursts sparse during the verses—single isolated red/ruby peonies—leave the sky completely dark from 04:12 to 04:22, and then trigger a single massive golden cascading willow/brocade fill at **04:23** on the lyric *"out there!"*.
3. **Character:** A single silhouette or small sprite of Quasimodo moving/standing in the central archway beneath the stained-glass window.

**10. What you couldn't see**
* The extreme lower perimeter and ground gates are obscured by audience heads in the foreground.
* Launch mortars on the ground behind the castle are out of sight behind the structure.

**11. Our version**
* **What's right:** 
  * "Magenta and ruby peonies" accurately captures the verse fireworks (**03:45, 04:05**).
  * "Gold brocade" correctly identifies the huge climactic shell at **04:23**.
* **What's wrong:**
  * **Song/Theme:** This segment is **not** *The Little Mermaid* / "Part of Your World".
  * **Character:** It is **Quasimodo**, not Ariel.
  * **Projections:** There are no "sunbeams through the water"; the projection is the **Gothic facade and stained-glass rose window of Notre Dame Cathedral**.
* **What's missing:**
  * The blue architectural searchlights framing the castle.
  * The quiet/dark sky pause between 04:12 and 04:22 that gives the golden brocade finish its dramatic impact.

</details>

### 3.6 When You Wish Upon a Star (interlude)

- **Audio:** 256-268 s (4:16-4:28, 12 s) · **Video:** `--start 4:26 --end 4:38`
- **Our score now:** A wall of pink and violet fountains across the whole castle (video 4:27-4:33), then gold chrysanthemums climbing over the spire. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 4:23-4:41 · notes: none</summary>

Here is the detailed breakdown of the segment:

**1. Where this part starts and ends**
* **Start:** **04:26**. The choir swells with an orchestral, wordless vocalization (*"Ahhh..."*), followed immediately at 04:27 by a massive, synchronized fan launch of magenta/hot-pink comets across the perimeter. Your 04:26 start is spot-on.
* **End:** **04:39**. The golden brocade canopy finishes falling, the castle transitions into swirling green lights, and spoken narration begins (*"Your destiny lies..."* at 04:39, introducing the next section). Your 04:38 end is slightly early by about 1 second.

**2. Music**
* **Song:** Orchestral interlude / transitional bridge incorporating choir vocalizations and motifs from *"When You Wish Upon a Star"*.
* **Lyrics / Spoken Audio:**
  * **04:25–04:32:** Choir vocalizing an ascending, soaring melody (*"Ahhh... / Ooh..."*).
  * **04:39:** Merida’s spoken line begins: *"Your destiny lies..."* (continuing into *"within you..."*).
* **Major Musical Hits:**
  * **04:27:** Big orchestral hit/swell syncing with the sudden upward launch of the magenta/violet comet fan.
  * **04:35:** Orchestral peak hit coinciding with the dual sky shell bursts.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **04:23–04:25** | Fading remnants of previous gold willow shell above spire | Deep blue upward searchlights on outer flanks | Blue/violet illuminated towers, stained-glass projection on center facade | None visible |
| **04:26–04:32** | Wide multi-point fan of bright magenta/hot-pink comets/mines shooting skyward across flanks and behind castle | Saturated purple floodlighting washes castle; blue perimeter searchlights | Brilliant magenta, purple, and blue lighting wash over towers and walls | None |
| **04:33–04:34** | Single central launch trail rises directly behind main spire | Perimeter searchlights sweep slightly; lower hub lights dim | Projections shift: stained glass clears, castle base dims to deep royal blue | None |
| **04:35** | Dual high-altitude burst: gold chrysanthemum left of spire, pink/gold peony right of spire | Blue searchlights beam upward behind castle | Deep blue lower walls with glowing gold/warm highlights on central spire | None |
| **04:36–04:38** | Giant golden brocade/willow canopy expands and rains down over both sides of castle | Steady upward blue beam arrays flanking castle | Blue castle body; green magical sparkle swirls begin forming at center/base | None |
| **04:39–04:40** | Brocade embers extinguish; quiet pause in sky launches | Blue searchlights tilt outward | Vibrant emerald green and turquoise lighting/projections take over center base | None |

**4. Fireworks in the sky**
* **04:27–04:32 (Magenta Comet Fan):**
  * **Type:** Comet / mine barrage with rising tails and glittering tips.
  * **Count:** Approximately 16–20 launch points creating a wide, symmetrical outward-fanning V-pattern across the entire castle width.
  * **Colour:** Vivid magenta/violet-pink.
  * **Height & Position:** Mid-height (extending from castle base to just above the upper turret levels), balanced symmetrically on left and right.
* **04:34–04:38 (Brocade Crown / Canopy):**
  * **04:34 Launch:** Single central shell ascending directly behind the spire.
  * **04:35 Burst:** Dual aerial break at high altitude—one classic gold chrysanthemum slightly left-of-centre, one smaller pink-to-gold peony slightly right.
  * **04:36–04:38 Hang-time:** The gold burst blooms into a massive brocade willow canopy with shimmering tips, draping across the upper half of the sky.
* **Rhythm:** Rapid, explosive single-wave fan (04:27), a 2-second sky clearance (04:32–04:34), followed by a single grand aerial shell break (04:35) that slowly glitters down.

**5. Fireworks on the castle**
* None fired directly from the castle turrets, parapets, or roof ledges during this interlude. All pyro originates from launch stations immediately behind the castle hub and perimeter grounds.

**6. Lasers and lighting**
* **Lasers:** None visible during this interlude.
* **Searchlights / Beams:** Powerful cyan/royal blue spotlights mounted on perimeter structures flank both sides of the castle, projecting steady static columns upward into the night sky at about a 70° angle.
* **Flames & Fountains:** None.

**7. The castle**
* **Lighting Changes:**
  * **04:23–04:26:** Blue lower base, purple spires, soft turquoise/violet highlights.
  * **04:27–04:31:** Entire structure is flooded with intense magenta/violet light matching the comet fan.
  * **04:32–04:37:** Shifts to deep midnight blue across lower towers and outer walls, with warm golden-amber lighting illuminating the center upper spire.
  * **04:38–04:40:** Deep royal blue towers with a dramatic shift at the lower central facade into glowing emerald green.
* **Projections:**
  * **04:23–04:32:** Remnants of cathedral/stained-glass arches on the central facade fade out.
  * **04:33–04:37:** Clear architectural detailing with starry/sparkle textures.
  * **04:38–04:40:** Emerald green wisps, forest foliage, and Celtic/magical swirl motifs fade onto the lower center facade.

**8. Characters**
* **None appear** during this interlude (neither projected nor light-formed). The transition relies purely on architectural lighting, projections, and fireworks.

**9. For our boards**
1. **The Magenta Fan (04:27–04:31):** The defining visual impact of the choir swell is the wide V-shaped fan of magenta/pink rising comets surrounding the castle while the castle washes in pure magenta.
2. **The Golden Brocade Crown (04:35–04:38):** A high-altitude break right above the spire that blossoms into weeping golden brocade trails draping over the upper display.
3. **The Emerald Shift (04:38–04:40):** Transitioning the castle base sharply from blue/magenta into emerald green to prepare for the *Brave* segment as Merida's voice begins.

**10. What you couldn't see**
* Exact launch ground hardware behind the castle is concealed by the structure itself.
* Crowd heads occasionally silhouette the very bottom few pixels of the hub lawn, but castle visibility is completely clear.

**11. Our version**
* **What’s right:** "Lavender, pink and turquoise castle" captures the primary lighting wash during 04:27–04:32. "Magenta and purple comets fanning left and right" accurately represents the opening pyro sequence. "Characters: none" is completely correct.
* **What’s wrong:** The comets are not just generic purple; they are bright neon magenta/hot pink. Turquoise is mostly restricted to searchlights and minor accents, rather than the primary castle body during the fan.
* **What’s missing:** 
  1. The big second half of the sequence: the single central high launch at 04:34 breaking into a huge golden weeping brocade/willow canopy (04:35–04:38).
  2. The castle transition at 04:38–04:40 to midnight blue towers with a bright emerald green lower center facade.

</details>

### 3.7 Touch the Sky

- **Audio:** 268-303 s (4:28-5:03, 35 s) · **Video:** `--start 4:38 --end 5:13`
- **Our score now:** Merida's Highlands: emerald and teal castle, Celtic knotwork; her arrow flies at 277 (video 4:47); gold willow, emerald and white strobes, red and gold comets; a gold canopy as Merida speaks (4:38), a white chrysanthemum (4:54), white comet fans (5:06). Characters: Merida.
- **V2:** stage ghost; actors merida (fewer fireworks, so her arrow shows; Merida says her line at the bottom left, then on "touch the sky" shoots an arrow into a bullseye firework (64x64)).
- **Checked by eye (2026-10-14):** Merida fires her arrow here (video 4:47).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-13</b> · gemini-3.8-flash · video 4:35-5:16 · notes: none</summary>

**1. Where this part starts and ends**
* **Segment Start (04:39):** Merida’s spoken voiceover begins (*"Our destiny lies within us..."*), shifting the castle projection from previous imagery into Scottish Highland forest greenery and Celtic patterns. 
* **Music / Song Start (04:49):** The song *"Touch the Sky"* begins vocally following Merida’s arrow launch cue at **04:47**.
* **Segment End (05:13):** The final chorus note of *"Touch the Sky"* holds and cuts off; at **05:14**, the castle projections rapidly clear into bright blue with the multi-coloured floating balloons from Pixar's *Up*, accompanied by *Up*'s theme music.
* **Accuracy of your 04:38 to 05:13 window:** Your timing is **spot-on**. 04:38 marks the trailing edge of the prior gold willow finale right before Merida speaks (04:39), and 05:13 is the exact final frame before the *Up* transition begins at 05:14.

**2. Music**
* **Song:** *"Touch the Sky"* from Disney/Pixar’s *Brave* (composed by Alex Mandel, lyrics by Mandel and Mark Andrews).
* **Dialogue and Lyrics:**
  * **04:39 – 04:44:** Merida (spoken dialogue): *"Our destiny lies within us. You just have to be brave enough to see it."*
  * **04:44 – 04:46:** Merida (shout/call): *"And then, your journey begins!"*
  * **04:46 – 04:47:** Heavy drum strike / whoosh of a launched flaming arrow.
  * **04:49 – 04:52:** Vocal begins: *"When the cold wind is a-calling..."*
  * **04:52 – 04:55:** *"...and the sky is clear and bright..."*
  * **04:56 – 04:58:** *"Be as strong as the seas are stormy..."*
  * **04:58 – 05:01:** *"...proud and bold as the eagle's scream..."*
  * **05:01 – 05:03:** Heavy orchestral accent: *"I will ride, I will fly!"*
  * **05:04 – 05:07:** *"Chase the wind and touch the sky!"*
  * **05:08 – 05:09:** Accent beat: *"I will fly!"*
  * **05:09 – 05:12:** Grand vocal crescendo: *"Chase the wind and touch the sky!"*
  * **05:12 – 05:13:** Orchestral cutoff and harp/flute glissando into *Up*.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **04:38 – 04:43** | Giant gold brocade willow canopy slowly descends and fades | Cyan and royal blue uplights wash castle base and spires | Transforms from blue facade to lush green forest foliage, mossy stone, Celtic knot borders | Will-o'-the-wisps (blue floating lights); Merida fades in at center balcony |
| **04:44 – 04:46** | Sky briefly dark/quiet | Green and cyan searchlights sweep upward | Forest and tartan textures intensify | Merida readies and draws her recurve bow |
| **04:47 – 04:49** | Single red/amber fiery comet trails from castle roof in high arc to upper left, bursting into a small ring/crossette | Flashes of red light at castle parapets | Target motif / Celtic knotwork glows brightly | Merida releases arrow upward, then projection blends into forest |
| **04:53 – 04:56** | 2 silver-white strobing glitter peony bursts (mid-to-high center/left) | Green laser beams streak across trees flanking castle | Glowing emerald green foliage, trees, and golden tartan accents | Celtic knotwork and forest scenery |
| **04:59 – 05:01** | Emerald green and white glitter bursts high center | Searchlights fan outward in cyan/green | Deep green stone and moss textures continue | Forest scenery |
| **05:01 – 05:04** | Rapid angled comet fans: 4 bright red/orange comets fan left, 4 fan right from castle flanks; followed by high red peony at center | Bright white and amber frontal flashes on castle facade | Castle flashes white-gold along vertical spires | Swirling wind and autumn leaf projections |
| **05:05 – 05:08** | Silver/white willow burst high center, followed by a bold red peony burst (05:08) | Turquoise and green searchlights sweep inward | Highland mountain silhouette and tartan patterns | Galloping Celtic horse motifs (stylized) |
| **05:09 – 05:12** | Massive finale fan: dense silver/white glitter willow canopy overhead with trailing red/gold crossettes below | Full white/green floodlights illuminate castle facade | Brilliant white/teal light streams downward like a Highland waterfall | Central tower illuminated with Scottish motifs |
| **05:13 – 05:15** | Residual glitter burns out; sky goes dark | Blue/cyan uplighting restores; transition wash | Facade transitions to sky blue; colorful cluster of balloons emerges at base | Carl Fredricksen's house balloons rise (*Up*) |

**4. Fireworks in the Sky**
* **04:38 – 04:42:** 1 massive lingering gold brocade willow burst canopy covering high center and expanding wide across the horizon.
* **04:47 – 04:49 (Merida’s Arrow):** 1 single flaming orange-red tail comet launched from behind the castle, arching upward to the upper left sky, culminating in a small red ring/peony burst with gold pistil.
* **04:53 – 04:56:** 2 white/silver strobe glitter peonies at medium-high center-left.
* **04:59 – 05:01:** 1 dual emerald-green and white strobe peony burst at high center.
* **05:01 – 05:04:** 8 angled comets in a mirrored fan (4 shooting low-to-mid left, 4 low-to-mid right) in bright fiery orange-red, followed instantly by 1 large crimson-red peony burst at high center.
* **05:05 – 05:08:** 1 large white/silver willow shell bursting high center, immediately followed at **05:08** by 1 vibrant red peony at mid-high center.
* **05:09 – 05:12:** Multi-layered finale sequence: 1 massive white/silver willow/chrysanthemum canopy bursting broad across the upper sky, paired with 2 lower red/gold crossette bursts underneath.
* **Rhythm:** Starts sparse and narrative-driven (the single arrow shot at 04:47), remains measured during the verse (1 burst every 3 seconds), then becomes rapid and rhythmic on the chorus beats (1–2 bursts/sec from 05:01 to 05:12).

**5. Fireworks on the Castle**
* **04:47:** Low launch effect from behind the castle roof/battlements that launches Merida's "fiery arrow" comet trailing into the sky.
* **05:01 – 05:03:** Low-level perimeter launching platforms situated immediately adjacent to the castle wings fire the angled red comet fan shots outward. No gerbs or fountains are attached to the turrets during this specific sequence.

**6. Lasers and Lighting**
* **Lasers:** Vivid emerald green laser lines project horizontally and angled slightly upward through the trees from hubs situated to the left and right of the central plaza (visible between 04:48 and 05:00).
* **Searchlights / Beams:** Deep cyan, turquoise, and emerald-green high-intensity moving head searchlights flank the castle base, initially sweeping upward and outwards, then pulsing inward to form a converging cone above the main spire on the chorus (05:01–05:12).
* **Flames / Fountains:** No open flames or water fountains are used during this section.

**7. The Castle**
* **Base Castle Lighting:** Deep forest emerald green, dark teal, and blue wash on lower stone walls, with gold architectural highlights illuminating the window frames and turret spires.
* **Projections:**
  * **04:39 – 04:46:** Ancient Scottish highland forest, moss-covered crags, glowing blue Will-o'-the-wisps hovering around the lower walls, and intricate Celtic knotwork patterns trimming the towers.
  * **04:47 – 04:50:** Target ring / archery motif flashes around Merida on the center balcony as her arrow fires.
  * **04:51 – 05:08:** Scottish tartan/plaid patterns interwoven with Scottish pines, swirling leaves, and rocky Highland mountain vistas.
  * **05:09 – 05:12:** Cascading white and pale teal water/mist pattern rushing down the central tower like a mountain waterfall.
  * **05:13 – 05:14:** Rapid wipe to clear sky blue as the *Up* balloons rise.

**8. Characters**
* **Merida:**
  * **Location:** Center / mid-lower tier of the castle (grid position: center, right above the main gateway balcony).
  * **Size:** Approximately 1/4 to 1/3 of the main castle facade height.
  * **Appearance & Action:** Appears at **04:39** with wild curly red hair and dark green gown. At **04:44**, she raises and draws her Scottish recurve bow, aiming diagonally up toward the sky. At **04:47**, she releases the bowstring as the fiery comet launches, fading out into Celtic tree knotwork by **04:49**.
* **Will-o'-the-Wisps:**
  * **Location:** Floating orbs in lower-left and lower-right tiers (grid: bottom-left and bottom-right).
  * **Appearance & Action:** Floating glowing cyan-blue spirits bobbing gently between **04:39 and 04:46**.

**9. For Our Boards (LED Matrix Recreation)**
To capture this segment on 64x32 / 64x64 pixel matrices:
1. **The Flaming Arrow Cue (04:47):** Display a small red/orange sprite (Merida's drawn bow) at the center of the castle, followed immediately by a single bright red single-pixel/two-pixel streak arcing from the roofline into the upper corner that pops into a small ring. This is the show's signature sync moment.
2. **The Mirrored Fan on the Beat (05:01 – 05:03):** On *"I will ride, I will fly"*, fire two angled diagonal comet lines shooting outward from the base of the castle left and right, topped by a centered red explosion.
3. **Palette Contrast:** Ensure the castle base remains strict **deep emerald green with glowing blue dots** (wisps) so the transition to the **bright multi-colored balloons on sky-blue** at **05:14** creates a sharp, readable contrast.

**10. What You Couldn't See**
* The exact launch mortars behind the castle perimeter fence are hidden behind the castle structure.
* Fine facial expressions on Merida are indistinct due to distance, projection scale, and ambient lighting contrast.

**11. Our Version**
* **What's right:**
  * **Gold willow, emerald, white strobes, red and gold comets:** Completely accurate.
  * **Moss/stone:** Correct (Highland crags, mossy stone, forest).
  * **Character: Merida:** Correct.
* **What's wrong:**
  * *"Cathedral bells":* Incorrect. The instrumentation is traditional Scottish folk: Highland pipes, tin whistle/recorder, fiddle, and heavy Celtic percussion/bodhrán drums—no church or cathedral bells.
  * *"Doves":* Incorrect. There are no doves shown in pyro, lighting, or projections (the lyric references eagles, but doves are completely absent).
* **What's missing:**
  * **Celtic knotwork / tartan patterns:** A primary visual theme projected across the spires.
  * **Will-o'-the-wisps:** The distinctive glowing cyan/blue orbs floating at the castle base prior to the song start.
  * **The signature Arrow Launch effect:** The fiery red comet at 04:47 representing Merida's arrow.

</details>

## 4. Journey (audio 5:03-6:38, video 5:13-6:48)

### 4.1 Touch the Sky / Up

- **Audio:** 303-325 s (5:03-5:25, 22 s) · **Video:** `--start 5:13 --end 5:35`
- **Our score now:** Up's balloons fill the blue castle and lift the house; a gold burst over the spire (video 5:20), red, white and green comets rising (5:23), big gold chrysanthemums (5:26-5:30). Characters: Merida, Carl, Up house.
- **V2:** stage ghost; actors up_house (Carl's house rises from behind the castle on its balloons).
- **To check by eye:** Gemini's answer below says only the balloons are shown (no house, Carl or Merida), and that the scene ends at 5:26 with Moana's music from 5:27, about 9 s before ours.
- **Checked by eye (2026-10-14):** keep the balloons, they're good. The Up house can stay too, but it needs drawing better.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 5:10-5:38 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **05:13**. At this point, the initial *Brave* sequence transitions as a dense cluster of multi-colored balloons begins floating upward across the central castle facade.
* **End:** **05:26** marks the true end of the "Touch the Sky" segment, landing on the final belted vocal note and a massive gold willow/chrysanthemum canopy. By **05:27–05:35**, the music shifts into Polynesian percussion and ocean visuals introducing the *Moana* segment (with the Heart of Te Fiti spiral emerging at **05:34**).
* **Verdict on 5:13 to 5:35:** 5:13 is accurate for the transition into the balloon sequence, but **5:35 is late**, as it runs ~9 seconds into the start of the *Moana* scene.

**2. Music**
* **Song:** "Touch the Sky" (*Brave*), transitioning at **05:27** into the opening percussion of *Moana*.
* **Lyrics & Vocal Cues:**
  * **05:10–05:12:** Vocal belt concluding an earlier phrase ("...sky!").
  * **05:13–05:16:** Bagpipes and Celtic orchestral bridge while balloons rise.
  * **05:17–05:21:** Female lead vocal: *"Chase the wind and touch the sky..."*
  * **05:22–05:25:** Final soaring crescendo: *"...touch the sky!"*
  * **05:26–05:38:** The vocal ends; rhythmic tribal/Polynesian drums and atmospheric strings fade in.
* **Key Hits:**
  * **05:22:** Sharp musical hit on the first word of *"Touch the sky!"*, launching parallel comet fireworks.
  * **05:24:** Massive orchestral hit on *"sky!"*, triggering the main gold canopy bursts.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **05:10 – 05:13** | Green/white burst above central spire | Teal/green lower beam fans | Blue facade with white illuminated spire | None visible |
| **05:14 – 05:16** | Faint residual crackle trails | Turret spotlights sweep outward | Multi-colored balloons inflate and rise up castle | Balloon cluster (*Up*) |
| **05:17 – 05:21** | Small gold chrysanthemum bursts high above spire | Green/teal laser fans at sides | Colorful Scottish tartan/plaid tapestry projection | None |
| **05:22 – 05:24** | 8–10 multi-colored comets shoot vertically in parallel flanks | Bright blue searchlights fan outward | Facade turns brilliant cyan/aqua blue | None |
| **05:24 – 05:26** | Huge gold chrysanthemum burst over spire | Blue base lights wash upward | Castle bathed in intense blue/white glow | None |
| **05:27 – 05:31** | Staggered pair of large gold willow/chrysanthemums bloom right and left | Blue searchlights sweep skyward | Deep aquatic blue projection with wave ripples | None |
| **05:32 – 05:38** | Sky clear; faint sparks drift down | Ambient blue wash on lower hub | Ocean water pattern; glowing orange/red spiral at 05:34 | Heart of Te Fiti spiral |

**4. Fireworks in the sky**
* **05:10–05:12:** 1 green-and-white peony burst centered directly behind the main spire at medium-high elevation.
* **05:17–05:21:** 2 small gold chrysanthemum bursts fired high, directly centered above the top spire.
* **05:22–05:24 (The Comet Fan):** A simultaneous barrage of 8 to 10 straight-tailed comets shooting directly vertically on both sides of the castle (roughly 4–5 on the left, 4–5 on the right). Colors: green, yellow, orange, magenta/red, and cyan. They ascend in unison to spire height before burning out.
* **05:24–05:30 (The Gold Canopy):**
  * **05:24:** 1 massive gold chrysanthemum/willow centered directly behind the top spire.
  * **05:27:** 1 large gold chrysanthemum bursting slightly to the right of the spire.
  * **05:28–05:29:** 1 large gold chrysanthemum bursting to the left, creating a massive three-cluster overlapping golden canopy.
* **05:31–05:38:** Sky is dark and quiet as the Moana sequence begins.

**5. Fireworks on the castle**
* **None.** No gerbs, fountains, or perimeter strobes are mounted on or fired from the castle turrets/battlements during this specific sequence. All pyrotechnics originate from ground/launch positions behind and adjacent to the castle.

**6. Lasers and lighting**
* **Lasers:** Low green/cyan laser fans project horizontally from the hub stage area outward to the left and right flanks between **05:10 and 05:20**.
* **Spotlights & Searchlights:**
  * **05:10–05:21:** Green and teal fixtures wash the lower landscaping and trees.
  * **05:22–05:26:** Blue and white ground fixtures sweep sharply upward and fan outward across both sides of the castle, mirroring the vertical comet trajectories.
  * **05:27–05:38:** Deep blue ground lighting stays stationary, casting an oceanic blue glow across the hub.

**7. The castle**
* **Lighting:**
  * Blue-lit turret roofs throughout. 
  * At **05:22**, the castle floodlights switch instantly to saturated cyan/ice blue.
* **Projections:**
  * **05:10–05:13:** White/cyan light streaming down the center spire.
  * **05:14–05:16:** Hundreds of small multi-colored round balloons (red, yellow, blue, green, purple) float rapidly up from the main lower gateway, covering the lower and middle facade.
  * **05:17–05:21:** Facade transitions into a vertical geometric Scottish tartan/plaid pattern composed of vibrant vertical stripes and diamond weaves in red, gold, purple, and blue.
  * **05:22–05:26:** Solid radiant aqua blue wash.
  * **05:27–05:38:** Undulating deep navy and turquoise ocean waves ripple across the stone facade. At **05:34**, a glowing reddish-orange spiral emblem (the Heart of Te Fiti) forms over the lower central wall.

**8. Characters**
* **Characters Present:** **No character figures** (neither Merida, Carl, Russell, nor Moana) physically appear as animated projection characters during this exact 05:10–05:38 clip.
* **Symbolic Motifs:**
  * **Balloons (*Up*):** Rise from the bottom-center (grid position bottom-center to center) between **05:14 and 05:16**.
  * **Heart of Te Fiti (*Moana*):** Appears at grid position bottom-center (over the main gateway arch) at **05:34**, glowing orange-red against the blue sea ripples.

**9. For our boards**
1. **The Balloon Rise (05:14–05:16):** An upward-scrolling cluster of multi-colored pixels (red, green, blue, yellow, purple dots) traveling up the center 16 columns of the castle sprite.
2. **The Rainbow Comet Sweep (05:22):** Parallel single-pixel trails in distinct bright colors (green, yellow, pink, blue) rising simultaneously straight up on both flanks of the castle.
3. **The Gold Willow Climax (05:24–05:28):** Castle turns instantly solid bright cyan while 2–3 overlapping golden expanding chrysanthemums/willows burst above the spire, trailing gold sparks downward.

**10. What you couldn't see**
* Ground-level pyro mortars and launch racks are hidden behind the castle architecture.
* Trees at the bottom corners slightly obscure the extreme outer edges of the low laser scans.

**11. Our version**
* **What is right:**
  * Bagpipes in the audio track (05:13–05:16).
  * Tartan plaid projection on the castle (05:17–05:21).
  * *Up* balloons floating up the castle facade (05:14–05:16).
  * Multi-colored comets firing upward on the vocal hit (05:22).
* **What is wrong:**
  * **Characters:** Merida, Carl, and the *Up* house **do not appear** in this clip. Only the balloons float upward—the house is not attached or projected here, and neither Carl nor Merida are shown.
  * The comets are not just red, green, and blue; they include vibrant yellows, oranges, and purples.
* **What is missing:**
  * The massive triple golden willow/chrysanthemum canopy that fills the entire upper sky between **05:24 and 05:29**.
  * The instant transition into *Moana* at **05:27**, where the music drops into Polynesian drums, the castle turns into deep rippling ocean water, and the Heart of Te Fiti spiral symbol glows on the lower gate at **05:34**.

</details>

### 4.2 How Far I'll Go

- **Audio:** 325-370 s (5:25-6:10, 45 s) · **Video:** `--start 5:35 --end 6:20`
- **Our score now:** The heart of Te Fiti on the castle, ocean blues, the manta ray; a dark sky with one white peony (video 5:53), then gold chrysanthemums as the song lifts (6:04) and a white one (6:10). Characters: Moana, Gramma Tala.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 5:32-6:23 · notes: none</summary>

Here is the detailed breakdown of the "How Far I'll Go" sequence based on the video:

**1. Where this part starts and ends**
* **Starts at 05:35**: The previous sequence fades out, and the glowing spiral **Heart of Te Fiti** symbol appears on the center of Cinderella Castle amidst rhythmic Polynesian percussion, followed by the spoken/chanted vocal call *"Moana..."* at 05:40. Your start time of **05:35 is spot on**.
* **Ends at 06:21**: At 06:20–06:21, Moana finishes the bridge (*"...will I cross that line?"*) as blue searchlights sweep upward and castle-mounted comet fans ignite right on the downbeat of the triumphant chorus (*"See the line where the sky meets the sea..."* at 06:21). Your 06:20 cutoff marks the precise end of this build-up verse, just as the main chorus kicks in.

**2. Music**
* **Song**: *"How Far I'll Go"* from Disney’s *Moana* (performed by Auli'i Cravalho).
* **Vocals & Lyrics**:
  * **05:40**: Ancestral chant/call: *"Moana..."*
  * **05:46 – 05:57**: *"Every turn I take, every trail I track, every path I make, every road leads back to the place I know where I cannot go, where I long to be..."*
  * **05:58 – 06:10**: *"See the light where the sky meets the sea? It calls me... And no one knows, how far it goes..."*
  * **06:11 – 06:20**: *"And it seems like it's calling out to me, so come find me! And let me know, what's beyond that line, will I cross that line?..."*
  * **06:21+**: Explosive chorus downbeat (*"See the line..."*).
* **Key Musical Hits**:
  * **05:52**: Beat accent on *"place I know"* (first sky burst).
  * **05:59**: Cymbal crash and rising pitch on *"See the light..."* (fan of upward white/gold comets).
  * **06:02**: Swelling orchestral hit on *"calls me"* (peony bursts overhead).
  * **06:07**: Hit on *"how far it goes"* (bursts at castle spire).
  * **06:21**: Major orchestral climax into the chorus with high brass and drum accents.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **05:32 – 05:34** | Lingering gold glitter falling from prior sequence. | Deep blue floodlights on lower hub/castle base. | Castle lit in deep indigo/ocean blue; golden window glow. | None. |
| **05:35 – 05:44** | Sky completely dark; quiet. | Warm ambient uplighting fades in. | Glowing amber/orange spiral Heart of Te Fiti projection appears on mid-castle. | None. |
| **05:45 – 05:51** | Quiet/dark sky. | Low blue wash on towers. | Castle base turns into ocean waves/sand patterns. | Moana fades into center lower gateway (standing, singing). |
| **05:52 – 05:55** | Single white/gold crossette/glitter peony burst to the left. | Searchlights idle. | Heart of Te Fiti pulses; Polynesian voyaging motifs across stone. | Moana singing at base. |
| **05:56 – 05:58** | Sky dark. | Deep blue/cyan floodlights on wings. | Green island foliage/vine patterns begin wrapping towers. | Moana transitions / looks up. |
| **05:59 – 06:01** | Fan of 4 white comet tails firing left and right behind castle. | White ground searchlight beams begin sweeping skyward. | Castle turns rich emerald green and ocean cyan. | Young/older Moana imagery on central facade. |
| **06:02 – 06:05** | Pair of large golden/orange chrysanthemum bursts left and right of spire. | Searchlights sweep outward. | Full vibrant tropical green, amber, and turquoise patterns. | Moana standing proudly in projection. |
| **06:06 – 06:10** | Continuous gold/white peony and glitter bursts centered directly above spire. | Green and cyan exterior floodlights intensify. | Island foliage motifs covering main body and spires. | Moana looking out towards the sea. |
| **06:11 – 06:17** | Sky pauses / quiet; sparse trailing sparks. | Searchlights hold narrow vertical angles. | Castle transitions to vibrant sunset gold/amber on upper towers, green on mid, deep cyan at base. | Moana in full projection; glowing spirit manta ray forms near base. |
| **06:18 – 06:20** | Soft golden willow burst directly over the high spire. | Searchlights fan outward. | Swirling bioluminescent blues wash over the castle, replacing green with ocean waters. | Giant ethereal blue bioluminescent manta ray (Gramma Tala) glides upward across the castle facade. |
| **06:21 – 06:22** | Angled fan of bright silver/white comet mines shoot outward from hub/rooftops; gold peony high left. | Bright cyan/blue searchlights sweep across the sky. | Entire castle engulfed in glowing ocean blue and turquoise water ripples. | Manta ray wings flap gracefully as it ascends the spire. |

**4. Fireworks in the sky**
* **05:35 – 05:51**: **Dark/quiet sky**. The section starts with an intentional silence to focus on the solo acoustic vocal.
* **05:52 – 05:55**: **1 medium white/silver glittering peony burst** bursting medium-high on the left side.
* **05:59 – 06:01**: **4 white comets** launched in mirrored angled pairs (2 left, 2 right) shooting upward and outward.
* **06:02 – 06:05**: **2 large golden chrysanthemums** (one medium-high to the left, one high directly behind/right of the main spire).
* **06:06 – 06:10**: Rapid wave of **3–4 white/silver strobing peonies and chrysanthemums** bursting high directly above the central spire, about 1 per second.
* **06:11 – 06:17**: **Dark lull**: sky clears completely as the lyrics soften (*"And it seems like it's calling out to me..."*).
* **06:18 – 06:20**: **1 soft golden/white willow burst** high above the main spire drifting slowly downward.
* **06:21 – 06:22**: A mirrored barrage of **comets and white/gold shell bursts** kicking off the chorus.

**5. Fireworks on the castle**
* **05:35 – 06:20**: No gerbs, fountains, or facade fireworks fire directly from the castle parapets or turrets. All pyro originates from launch stations immediately behind and flanking the castle.
* **06:21**: Low-level fan mines and angled comets launch from the castle perimeter/rooftop launch rails synchronized with the chorus hit.

**6. Lasers and lighting**
* **Lasers**: No distinct geometric aerial laser beams are featured in this specific build-up sequence (focus is entirely on projection mapping and sky shells).
* **Searchlights / Moving Heads**:
  * Located at ground level flanking the castle and behind the hub berms.
  * Mostly off or parked low during 05:35–05:58.
  * At **05:59**, white/pale-blue beams turn on and tilt outward.
  * At **06:18–06:22**, bright cyan and cool-blue searchlight beams sweep upward in an expansive V-fan into the sky, mimicking rays of sunlight underwater.

**7. The castle**
* **Base Architectural Lighting**:
  * Starts in deep navy and royal ocean blue with warm glowing windows (05:32–05:38).
  * Shifts to lush tropical emerald green and golden yellow as Te Fiti’s greenery spreads (05:56–06:17).
  * Drops back to bioluminescent deep ocean turquoise and cobalt blue as the water takes over (06:18–06:22).
* **Projections**:
  * **05:35 – 05:44**: The **Heart of Te Fiti** (the iconic circular spiral symbol) glows vibrantly in amber/gold right in the central facade over the grand balcony.
  * **05:45 – 05:55**: Stylized Polynesian tapa patterns and rolling ocean shorelines wash across the stone.
  * **05:56 – 06:17**: Lush island greenery, tropical leaves, and vines spread outward across the towers and side turrets, turning the castle into the restored island of Motunui/Te Fiti.
  * **06:18 – 06:22**: Swirling, fluid water ripples wash over the foliage, transforming the castle into deep sea blue, through which bioluminescent sea life and ocean currents ripple.

**8. Characters**
1. **Moana**:
   * **Location**: Lower-center of the castle (bottom-middle of a 3x3 grid, over the gateway arch and lower balconies).
   * **Size**: Approx. 1/4 to 1/3 the height of the castle facade.
   * **Action/Movement**: Appears at **05:45** singing, looking contemplative, then looking forward toward the horizon; fades/transitions between scenes on the central tower before fading out around **06:16**.
2. **Gramma Tala / Manta Ray Spirit**:
   * **Location**: Starts at the castle base (bottom-center) and glides upward through the mid-section toward the spire.
   * **Size**: Massive wingspan covering nearly the full width of the main central facade (approx. 1/3 of the castle width/height).
   * **Action/Movement**: Emerges at **06:17–06:18** glowing as an ethereal, bioluminescent blue/turquoise manta ray, flapping its wings and swimming gracefully upward against the castle's blue ocean backdrop through **06:22**.

**9. For our boards (LED matrix recreation tips)**
To capture this on 64x32 / 64x64 matrices:
1. **The Te Fiti to Foliage Shift (05:35 – 06:05)**: Start with the castle silhouette in dark blue with a bright 6x6 amber spiral pulsing in the center. Then, flood the castle pixels into lush emerald green as Moana sings the first verse.
2. **The Quiet Space**: Keep the sky matrix completely black during 05:35–05:51; resist adding fireworks until the single burst at 05:52 and the small fan comets at 05:59. This silence makes the subsequent chorus explode with impact.
3. **The Manta Ray Transition (06:18 – 06:21)**: Instantly shift the castle pixels from emerald green to deep aquatic cyan/navy, and animate a bright cyan/white diamond-shaped manta ray gliding from the bottom row up toward the spire right before the burst of comets.

**10. What you couldn't see**
* **Hub crowds**: The bottom edge of the frame contains spectator silhouettes and raised mobile phones, partially obscuring the very bottom roadway/foot of the castle gate.
* **Perimeter Launchers**: The exact ground firing hardware behind the castle is hidden behind the castle structure and trees.

**11. Our version**
* **What’s right**:
  * You correctly identified the **Heart of Te Fiti** on the castle, the **ocean blues**, and the **manta ray**.
  * Having **sparse bursts building in green, gold, and white** is musically and visually accurate.
  * Having **Moana** and **Gramma Tala** (as the manta ray) is the correct character pairing.
* **What’s wrong / needs precision**:
  * Gramma Tala does **not** appear in human form here—she is exclusively depicted as the glowing **spirit manta ray**.
  * The castle is not solely "ocean blues"—during the middle verse (05:56–06:17), the castle is overwhelmingly dominated by **lush tropical emerald greens and amber island foliage**, before washing back into ocean blues when the manta ray appears at 06:18.
* **What’s missing**:
  * The prominent **emerald green island takeover** phase on the castle facade between 05:56 and 06:17.
  * The mirrored **upward comet fans** at 05:59 and the dramatic chorus takeoff comets at 06:21.

</details>

### 4.3 How Far I'll Go (climax)

- **Audio:** 370-398 s (6:10-6:38, 28 s) · **Video:** `--start 6:20 --end 6:48`
- **Our score now:** The chorus: turquoise searchlights, gold glitter, then big white and gold chrysanthemums over the spire (video 6:34-6:43). Characters: Moana.
- **V2:** stage off; actors canoe (Moana's canoe sails across once the castle goes).
- **Checked (2026-10-14):** Gemini's answer below says Tangled starts at 6:48; it doesn't, Aladdin's line (5.1) does, and I See the Light is at about 11:18. Its end time (6:48) still matches the score.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 6:17-6:51 · notes: none</summary>

Here is the detailed analysis of the **Moana – “How Far I’ll Go (Climax)”** section of Disney’s *Happily Ever After* fireworks show:

**1. Where this part starts and ends**
* **Start:** **06:21** (video clock). Marked by the vocal drop into the chorus (*“See the line where the sky meets the sea...”*), a massive cymbal/orchestral hit, searchlights snapping upward, and simultaneous skybursts flanking the castle. 
  * *Note on your 06:20 estimate:* **06:20 is slightly early** (at 06:20 she is still finishing the pre-chorus *“Will I cross that line?”* over a surging wave projection), but it captures the exact upbeat/transition.
* **End:** **06:48** (video clock). Marked by the final held orchestral chord of *“...how far I’ll go!”* fading out, the cessation of sky fireworks, and the castle immediately morphing into warm golden candlelight/lantern hues for the start of the *Tangled* section at 06:48.
  * *Note on your 06:48 estimate:* **06:48 is exact**.

**2. Music**
* **Song:** “How Far I’ll Go” (Climax/Reprise) from Disney’s *Moana*.
* **Lyrics & Timestamps:**
  * **06:17–06:18:** *“What’s beyond that line?”*
  * **06:19–06:21:** *“Will I cross that line?”*
  * **06:21–06:26:** *“See the line where the sky meets the sea? It calls me!”*
  * **06:26–06:32:** *“And no one kno-o-ows, how far it go-o-oes!”*
  * **06:32–06:37:** *“If the wind in my sail on the sea stays behind me...”*
  * **06:37–06:41:** *“One day I’ll know, if I go there’s just no telling...”*
  * **06:41–06:47:** *“...how far I’ll go-o-o!”*
* **Big Musical Hits:**
  * **06:21:** Massive chorus downbeat on *“See”*.
  * **06:32:** Downbeat on *“If”* (initiates the soaring brass run).
  * **06:37:** Climax modulation downbeat on *“One [day]”*.
  * **06:42:** High belt arrival on *“[how far I’ll] GO!”*.
  * **06:47:** Final orchestral cutoff before the quiet *Tangled* transition.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle Projections | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **06:17–06:20** | Quiet overhead; small glittering sparks drifting left. | Cyan/blue up-lights wash lower hub. | Deep ocean greens, teals, and rising wave crests. | None visible. |
| **06:21–06:25** | High gold comet crossettes/peonies split above; twin comets shoot up from rear castle flanks. | Wide blue and cyan beam fans sweep skyward from hub left/right. | Castle floods in luminous bright turquoise and rolling ocean waves. | Moana’s canoe/sail silhouette begins emerging at center. |
| **06:26–06:31** | Low/mid golden comet tails and sparkling aerial breaks behind spire. | Beams tilt and pulse in bright cyan and emerald green. | Vibrant Polynesian tapa quilt patterns wrap turrets; glowing spiral Heart of Te Fiti forms at base. | Moana projected standing on the center tower shaft (waist-up). |
| **06:32–06:36** | High, massive golden brocade/willow canopy bursts directly above the spire, raining down. | Cyan searchlights narrow straight up; bright green accent beams sweep horizontally. | Central shaft shows glowing blue starry sky & water; lower arch glows fiery amber/orange. | Moana remains projected on central tower; glowing Heart of Te Fiti emblem prominent on main gate. |
| **06:37–06:40** | Huge emerald-green chrysanthemum burst (high center/left), followed immediately by bright silver/white strobe peony (center). | Beams angle into high criss-cross fans; turrets bathed in electric turquoise and gold. | Turrets covered in glowing Polynesian tribal art patterns; central spire saturated in bright violet/magenta. | Moana singing heroically at center; Heart of Te Fiti pulsing in gold/orange at gate. |
| **06:41–06:47** | Layered grand finale: emerald peony left (06:41), massive white flash center (06:42), giant double rose-gold / pink brocade chrysanthemums covering the entire sky (06:43–06:46). | Beams spread into a massive wide fan across the entire sky. | Bright magenta/gold geometric tattoo tapestries across all walls. | Moana fades back into the patterns as the note sustains. |
| **06:48** | Quiet; aerial bursts stop completely. | Searchlights extinguish / fade down to soft amber. | Instantly morphs to soft slate-grey/warm amber stone; cathedral sail arches dissolve into *Tangled* lanterns. | Moana gone. |

**4. Fireworks in the sky**
* **06:21–06:24:** 2 high aerial shells (white/gold comet crossettes) bursting left and right of the upper spire, accompanied by 4–6 fast comet tails shooting straight up behind the castle.
* **06:28–06:31:** Small wave of 3–4 medium-altitude gold glitter comets breaking behind the spire.
* **06:32–06:35:** 1 very large, high-altitude golden brocade willow shell bursting directly over the main spire and drifting down in glittering tendrils.
* **06:36–06:37:** 1 large emerald-green dahlia/chrysanthemum shell at spire height slightly left of center.
* **06:38–06:40:** 1 large brilliant silver/white glitter peony bursting high center, expanding over the main tower.
* **06:41–06:46 (Grand Climax Barrage):**
  * 06:41: 1 medium bright-green ring/peony shell on the upper left.
  * 06:42: 1 massive white-gold burst dead center above the spire.
  * 06:43–06:46: 2 massive, overlapping deep rose-pink/gold glittering chrysanthemum shells expanding left and right, filling the entire upper sky canopy.
* **Rhythm:** Starts with single punctuation bursts (06:21), pauses briefly during the verse line (06:27–06:31), builds to a 1-shell-per-second cadence (06:32–06:40), and finishes in a dense 4-second overlapping crescendo (06:41–06:46). The sky is completely dark/quiet at 06:48.

**5. Fireworks on the castle**
* **06:21–06:23:** Twin comet/tracer launches fired from launch decks directly behind the lower castle flanks, angling slightly outward.
* *Note:* No continuous gerbs or turret waterfall fountains are fired directly off the stone ledges in this specific 27-second window; the pyrotechnic action is focused on the high aerial shell launches from behind the castle.

**6. Lasers and lighting**
* **Searchlights:** Ground-based moving heads flanking the hub fire beams upward in electric cyan/turquoise and lime/emerald green.
  * At **06:21**, they shoot straight up, framing the castle.
  * At **06:26–06:35**, they criss-cross and fan outwards into the sky.
  * At **06:41–06:46**, they fan out at their widest angle to frame the massive finale shells.
* **Lasers:** No sharp geometric scanning lasers are visible projecting into the open sky here; the effect is driven predominantly by wide aerial searchlight beams and high-intensity architectural wash fixtures.

**7. The castle**
* **Base Architectural Lighting:** Flooded with saturated cyan/turquoise wash on the lower ramparts, transitioning to deep royal blue and violet on the upper spires.
* **Projections:**
  * **06:20–06:25:** Vibrant turquoise ocean swells surge upward across the castle facade.
  * **06:26–06:40:** Rich Polynesian tapa patterns (geometric tribal motifs, manta rays, stylized leaves) cover all outer turrets and side walls in neon cyan, gold, and magenta. The main entrance archway transforms into a glowing, spinning green-gold Heart of Te Fiti spiral emblem.
  * **06:41–06:47:** The central shaft and spires intensify into saturated magenta, violet, and gold geometric tapestry art.
  * **06:48:** The tapa art dissolves abruptly; castle stone shifts to warm slate/amber with soft glowing warm light for *Tangled*.

**8. Characters**
* **Character:** **Moana**.
* **Position:** Center column of Cinderella Castle (Grid: center-middle to center-top, along the main clock/window facade).
* **Size:** Approximately 1/4 to 1/3 the height of the main castle body.
* **Movement:** 
  * Appears around **06:24–06:26** emerging out of the turquoise wave projection, standing at the helm of her sailing canoe looking forward.
  * She remains centrally projected, singing dynamically facing the audience through **06:40**.
  * Blends/fades back into the vibrant tapa art by **06:43** as the final barrage erupts.
* **Symbolic Character Art:** The **Heart of Te Fiti** (the green/golden swirl) is projected prominently right in the central gateway archway (Grid: bottom-center) from **06:26 to 06:47**.

**9. For our boards**
To make a 64x32 or 64x64 LED matrix version look instantly recognizable:
1. **The Palette Shift (06:21):** The castle must instantly flip from dark ocean green to blinding turquoise/cyan, with cyan searchlight rays fanning out 45 degrees left and right.
2. **The Heart of Te Fiti Gate:** Placing a vibrant 5x5 or 7x7 pixel glowing green/yellow spiral right in the castle entrance archway will immediately signal *Moana* to viewers even at low resolution.
3. **The Finale Sequence (06:41–06:46):** Fire an emerald-green burst on the left, a bright white burst center, and finish with a double wide-canopy pink/gold glitter burst overhead that hangs while the final vocal note sustains.

**10. What you couldn't see**
* Extremely low ground pyro at the perimeter launch sites (behind trees/crowd heads) is not visible from this hub perspective.
* Fine detailing of Moana’s face on the central projection is somewhat softened due to the high-contrast brightness of the projection against the castle stones.

**11. Our version**
* **What’s right:** 
  * "Turquoise searchlights" (prominent throughout 06:21–06:46).
  * "Green shells" (striking emerald bursts at 06:36 and 06:41).
  * "Characters: Moana" (projected on the main tower).
* **What’s wrong:** 
  * "Heavy gold brocade barrage" is not the *only* or even dominant sky element at the start; the climax relies heavily on **electric green, silver/white strobe, and deep pink/rose-gold chrysanthemums**, with pure gold brocade mainly featured in a single massive willow at 06:33.
* **What’s missing:**
  * **The Heart of Te Fiti** glowing spiral emblem at the castle base gate (crucial Moana visual).
  * **The giant rose-pink/magenta finale chrysanthemums** at 06:43–06:46 (the actual visual climax of the song).
  * **The colorful Polynesian tapa/tribal projections** covering the side turrets in magenta and cyan.

</details>

## 5. Friendship (audio 6:38-9:23, video 6:48-9:33)

### 5.1 Aladdin: a best friend by your side

- **Audio:** 398-412.5 s (6:38-6:52, 14.5 s) · **Video:** `--start 6:48 --end 7:03`
- **Our score now:** Spoken line over gold and purple lamp smoke on a midnight-blue castle. Characters: Aladdin.
- **Checked (2026-10-14):** Gemini's answer below calls the scene before this one Tarzan; it's How Far I'll Go (4.3).
- **Checked by eye (2026-10-14):** Genie and the lamp or Aladdin, either works. 5.8 already has the Genie, so leaving Aladdin here is fine.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 6:45-7:06 · notes: none</summary>

Here are the detailed facts for the "Aladdin: a best friend by your side" transition segment based on the video:

**1. Where this part starts and ends**
* **Starts at 06:48**: The preceding high-energy *Tarzan* section concludes with massive white/gold aerial bursts (06:48–06:51), while a giant projection of the Magic Lamp appears directly over the center entrance arch of Cinderella Castle (06:48). Your 06:48 estimate is **exact**.
* **Ends at 07:01–07:02**: Genie finishes speaking *"possibilities"* (07:00), the audio transitions abruptly with a cymbal roll/horn fanfare into the upbeat intro of *"Friend Like Me"* at 07:01, and the entire castle flashes into multi-colored kaleidoscopic Arabian architecture at 07:02. Your 07:03 end mark is **slightly late** (by about 1 to 2 seconds).

**2. Music**
* **Track / Background Score**: Atmospheric orchestral strings and mystical bells swelling from *Aladdin*, transitioning directly into the dynamic brass intro of *"Friend Like Me"*.
* **Spoken Lines (Genie / Robin Williams vocal audio)**:
  * **06:55–07:00**: *"Trust me, having that best friend by your side opens up a whole new world of possibilities!"*
* **Musical Hits / Cues**:
  * **06:48–06:50**: Final heavy percussive orchestral hits concluding the *Tarzan* sequence.
  * **06:52**: Gentle sparkling chime effect as gold willows disperse and the sky falls quiet.
  * **07:01**: Brass fanfare flourish and cymbal roll leading into the upbeat swing tempo of *"Friend Like Me"*.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle Projections & Base Wash | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **06:48** | 2 large gold/white chrysanthemum bursts high above the castle spire. | Green and yellow laser beams sweep outwards into the sky; side beams fade down. | Deep blue/purple tower wash; bright gold Magic Lamp glowing at the central gateway; swirling gold smoke trail rising up the main facade. | Magic Lamp at center base; Genie begins emerging as blue vapor. |
| **06:50** | 1 large golden willow burst blooms high directly over center spire. | Sky searchlights and side lasers turn off; castle lighting darkens. | Deep midnight blue base wash over turrets; golden lamp smoke continues rising up the central tower. | Magic Lamp glowing bright at lower center. |
| **06:52–06:54** | Sky clears to dark; trailing gold brocade willow falls behind the upper spire. | Low ambient front wash; stage lights dimmed down. | Castle body illuminated in rich royal/midnight blue; archway framed in warm amber light around the lamp. | Golden lamp resting inside the central archway. |
| **06:55–07:00** | Sky is completely dark and silent (no fireworks). | No lasers or searchlights; dark sky contrast. | Saturated midnight-blue stone wash across all towers and walls; central balcony/entrance features the golden lamp on a dark pedestal backdrop. | Genie (blue silhouette/bust with glowing eyes/smile) materializes out of yellow/green mystical smoke above the lamp in the center gate window. |
| **07:01–07:02** | Quiet sky; fireworks launch from ground behind castle (streaks starting up). | Blue/purple wash instantly replaced by brilliant rainbow floodlights. | Castle abruptly transforms into vibrant teal, magenta, gold, and green mosaic palace facade with elephant motifs. | Genie disappears into the full ensemble scene transformation. |

**4. Fireworks in the sky**
* **06:48–06:49**: Two large spherical chrysanthemum shells (bright white-gold center with crackling tips), detonating high above the central spire (left-center and right-center).
* **06:50–06:52**: One massive center brocade willow shell detonates high directly behind the main spire, draping long, shimmering golden trails that slowly fall behind the upper castle.
* **06:53–07:01**: **Total quiet in the sky**. Zero aerial fireworks during Genie’s spoken line (06:55–07:00). The sky is completely dark, allowing focus on the castle projection and voiceover.
* **Launch rhythm**: Wave of 3 heavy concluding bursts from 06:48 to 06:50, followed by a total lull of ~9 seconds.

**5. Fireworks on the castle**
* None fired from the castle turrets, battlements, or roofs during this window.

**6. Lasers and lighting**
* **Lasers**: Green and yellow laser fans sweep outward across the sky at 06:48 from castle rooftops, but are shut off completely by 06:50. No lasers fire from 06:51 to 07:01.
* **Searchlights / Sky beams**: Narrow white searchlight beams crossing in front of the castle fade out by 06:49.
* **Castle Wash**: Saturated deep midnight-blue/cobalt floodlighting blankets the outer turrets, spires, and side walls, focusing all visual attention on the bright golden portal at the bottom center.

**7. The castle**
* **Base / Turrets**: Deep cobalt blue and royal purple wash across all stone surfaces and spires from 06:50 to 07:01.
* **Projections**:
  * **06:48–06:52**: A bright golden Magic Lamp sits at the center gateway; a vertical trail of swirling golden smoke streams up the main tower face.
  * **06:53–07:00**: The lamp remains anchored at the bottom-center portal (center-bottom 3x3 grid). A decorative pointed Arabian archway outlines the portal. Mystical green-and-yellow smoke pools in the arch above the lamp.
  * **07:01–07:02**: Instant shift—the blue facade snaps into full-color Moroccan/Arabian patterned tiles with pinks, greens, oranges, and blue elephants.

**8. Characters**
* **The Magic Lamp**:
  * *Location*: Bottom-center (center grid row 3, right over the main entrance arch).
  * *Size*: ~1/6 the height of the castle facade.
  * *Movement*: Static, glowing brightly in brilliant golden yellow.
  * *Duration*: Visible 06:48 to 07:01.
* **The Genie**:
  * *Location*: Bottom-center, emerging directly above the Magic Lamp inside the illuminated archway.
  * *Size*: Compact silhouette/figure filling the lower archway (~1/5 the castle's height).
  * *Appearance / Movement*: Materializes as a swirling blue spirit silhouette surrounded by yellow/green magical vapor, gesturing as his voice speaks (06:55–07:00).
  * *Duration*: Fades in around 06:54; vanishes at 07:01 as the song begins.
* *(Note: Aladdin himself does **not** appear during this speaking segment; only the Genie and the Magic Lamp).*

**9. For our boards**
1. **The Midnight Blue Contrast**: Keep the entire castle matrix deep royal/midnight blue with the surrounding sky pitch black (LEDs off) from 06:52 to 07:01.
2. **The Glowing Golden Lamp**: A crisp, bright yellow/gold lamp graphic anchored at the bottom-center gate with a gentle yellow/cyan puff or silhouette above it representing the Genie speaking.
3. **The Abrupt Burst into Color at 07:01–07:02**: The dramatic shift from quiet, dark blue stillness into vivid, saturated rainbow/teal palace patterns exactly as the brass fanfare hits.

**10. What you couldn't see**
* Genie’s facial expressions within the lower portal projection are small and slightly low-resolution due to wide-angle recording distance and lighting contrast, appearing primarily as a glowing blue animated torso/silhouette within magical smoke.

**11. Our version**
* **What's right**: The midnight-blue castle base wash, the spoken line timing, and the gold/purple magical smoke coming from the lamp are accurate.
* **What's wrong**: **Aladdin does not appear here.** The character shown and heard is the **Genie** (emerging from the lamp).
* **What's missing**: The **Magic Lamp** itself (anchored prominently in gold at the castle's bottom portal) and the **3-burst gold willow sky finale** from 06:48–06:51 that precedes the complete sky blackout during the dialogue.

</details>

### 5.2 Friend Like Me (instrumental)

- **Audio:** 412.5-428 s (6:52-7:08, 15.5 s) · **Video:** `--start 7:03 --end 7:18`
- **Our score now:** Brass patterns and lanterns on the castle, white shells; on three beats the side rooftops fire fans of comets, white, red, then green (video 7:15-7:17). Characters: Aladdin, Genie.
- **Checked by eye (2026-10-14):** Gemini is right: at about 7:15-7:17 the side rooftops fire three quick fans of comets, one per beat (white, then red, then green). Ours has blue and gold fountains instead.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 7:00-7:21 · notes: none</summary>

**1. Where this part starts and ends**
* **Starts:** **07:02**. The musical transition hits with a big-band brass fanfare, and the castle immediately transforms from dark blue into vibrant turquoise, gold, and green palace mosaics. 
* **Ends:** **07:18**. The vibrant palace facade dims and transitions into swirling neon-green and blue magic smoke on a sharp musical beat, introducing the next phrase.
* **Accuracy of 07:03 to 07:18:** Very accurate. The visual projection change begins at 07:02, the opening firework comets launch at 07:03, and the green visual shift occurs precisely at 07:18.

**2. Music**
* **Song:** *"Friend Like Me"* from Disney’s *Aladdin* (energetic, big-band jazz instrumental arrangement with vocal shouts/scats).
* **Lyrics/Vocals:**
  * **07:06 – 07:08:** Vocal scat: *"Wah-wah-wah!"*
  * **07:08 – 07:10:** Scat vocal: *"Oh-ah-ah!"*
  * **07:11 – 07:13:** Vocal shout: *"Oh yeah!"*
* **Big Musical Hits:**
  * **07:02 / 07:03:** Initial brass stab / downbeat launching the theme.
  * **07:06:** Heavy brass accent on *"Wah-wah-wah"*.
  * **07:08:** Accent beat on *"Oh-ah-ah"*.
  * **07:11:** Major downbeat on *"Oh yeah!"*.
  * **07:15 – 07:17:** Three rapid, ascending rhythmic horn stabs.
  * **07:18:** Trill and beat drop transitioning into the next measure.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **07:00 – 07:01** | Sky dark / remnants of previous bursts | Low white searchlights | Dark blue wash with violet accents | Silhouette of Genie in bottom archway |
| **07:02 – 07:03** | Twin white comet tails launch vertically from low flanks | White searchlight beams fan outward from castle base | Projections snap to colorful Agrabah/palace jewel mosaics | Golden Magic Lamp appears in lower gate arch |
| **07:04 – 07:05** | Comets arc and burst into crackling tourbillons/whistles high left & right | Searchlights sweep slightly inward | Vibrant turquoise, magenta, and gold facade; emerald-green turret domes | Genie’s face appears in center balcony window |
| **07:06** | Golden brocade/peony shell bursts dead-center over spire | Bright ground uplighting accents castle facade | Mosaic patterns shimmer to the brass beat | Genie animates in central window |
| **07:07 – 07:09** | Mirrored gold comets shoot up and cross in an "X" over spire; high gold peony shell bursts center | Searchlight beams tilt upward into the sky | Facade lit in turquoise, purple, and gold | Lamp glows bright yellow at base; Genie animated above |
| **07:10 – 07:14** | Massive gold willow / kamuro shell with crackling glitter canopy fills high sky | White beams point nearly vertical | Rich gold and turquoise architectural projections | Genie visible in center balcony |
| **07:15** | Symmetrical fanned white/silver comets shoot outward from side rooftops | Searchlight beams pulse | Jewel patterns intensify | Magic lamp at bottom center |
| **07:16** | Symmetrical fanned coral/red comets shoot outward from side rooftops | Side uplighting shifts reddish | Ornate palace archways projected across walls | Genie in center window |
| **07:17** | Symmetrical fanned bright green comets shoot outward from side rooftops | Side uplighting flashes bright green | Facade pulses bright green and gold | Genie animates in window |
| **07:18** | Fan comets fade; trailing smoke drifts | Searchlights swing outward; green wash floods castle | Mosaic clears; replaced by swirling deep blue and acid-green magic smoke | Genie starts morphing/floating as smoke swirls |

**4. Fireworks in the sky**
* **07:03 – 07:05:** Symmetrical pair of bright white/silver whistling comet tails launch from low left and right, climbing high before breaking into crackling spinning comets/tourbillons.
* **07:06 (1 shell):** Medium-sized gold brocade/peony burst right at the tip of the central spire.
* **07:07 – 07:09 (2 comets, 1 shell):** A mirrored pair of gold comet tails launch angled inward, crossing in an "A/X" shape high above the spire, while a high-altitude golden chrysanthemum bursts dead-center at 07:08.
* **07:10 – 07:14 (1 large shell):** A massive gold willow/kamuro shell explodes high center, cascading down in lingering glitter and crackles across the entire width of the upper sky.
* **07:15 – 07:17 (Perimeter Fan Barrages - 3 waves):**
  * **07:15:** Low-to-mid fanned white/silver comet plumes fire simultaneously on both left and right flanks (approx. 5–6 comets per side).
  * **07:16:** Low-to-mid fanned red/pink comet plumes fire simultaneously on both flanks.
  * **07:17:** Low-to-mid fanned bright lime-green comet plumes fire simultaneously on both flanks.
* **Rhythm:** Starts with twin accent launches (07:03), settles into single large gold hits on the vocal scats (07:06, 07:08, 07:10), followed by rapid, syncopated three-step fan bursts (07:15–07:17) matching the horn rhythm.

**5. Fireworks on the castle**
* **07:06:** Central roofline/behind-spire launcher fires the spire shell.
* **07:15 – 07:17:** Low rooftop/parapet launchers fire the 3-step color fan (white, red, green) directly from the lower perimeter flanking walls of the castle.

**6. Lasers and lighting**
* **Searchlights:** Four to six bright white moving-head searchlight beams placed at ground level on either side of the castle base. They fan outward at 07:03, pull vertical during the willow burst (07:10–07:14), and crisscross rapidly at 07:17–07:18.
* **Lasers:** No direct beam lasers are visible in this specific segment.
* **Flames/Fountains:** No fire nozzles or water fountains active in this shot.

**7. The castle**
* **Base Architectural Lighting:** Shifts from blue/violet (07:00) to vivid turquoise/cyan base wash (07:02–07:16), then flashes emerald green (07:17–07:18).
* **Projections:**
  * **07:02 – 07:17:** Intricate Arabian palace / Cave of Wonders jewel facade:
    * Turret conical roofs turn bright emerald green with gold leaf tips.
    * Castle walls are mapped with turquoise and magenta arched alcoves, gold filigree, and Islamic geometric tile patterns.
  * **07:18:** The geometric patterns vanish; the castle base and midsection turn into dark blue stone covered in swirling acid-green magical vapor.

**8. Characters**
* **Genie (Magic Lamp):**
  * **Location:** Bottom-center (main entrance archway).
  * **Size:** Approx. 1/8 of castle height.
  * **Movement:** Stationary glowing gold lamp, with yellow/gold light and smoke billowing upward.
  * **Appears:** 07:00 (silhouette), fully lit from 07:02 to 07:17.
* **Genie (Character Face/Bust):**
  * **Location:** Center of castle (middle row, center column — the large balcony window above the main gateway).
  * **Size:** Approx. 1/5 of castle height.
  * **Movement:** Blue animated face framed in the window, smiling and shifting expressions with the beat.
  * **Appears:** 07:04; transitions to swirling full-body magic at 07:18.
* *Note:* Aladdin is not clearly identifiable as an isolated standalone projection during these specific seconds; the focus of the visuals is Genie and the Magic Lamp.

**9. For our boards**
On a 64×32 or 64×64 LED matrix:
1. **The Instant Facade Transformation (07:02):** Snap the castle palette instantly from dark blue to bright cyan/turquoise walls with emerald-green turret tops and gold trim.
2. **The "Crossing Comets" & Spire Shell (07:07 – 07:10):** Draw two angled gold lines crossing over the spire, exploding into a golden willow canopy.
3. **The 3-Beat Flanking Fan (07:15 – 07:17):** Three successive pixel fans shooting left and right from the castle shoulders: **White** on beat 1, **Red** on beat 2, **Green** on beat 3.

**10. What you couldn't see**
* Ground-level details below the castle bridge railing (blocked by hub crowds and foliage).
* The outer perimeter launch sites far behind Fantasyland (only the rising trails in the night sky are visible).

**11. Our version**
* **What's right:** The presence of Genie and the ornate gold/brass architectural patterns across the castle facade.
* **What's wrong:**
  * It is not "lanterns"; it is the golden **Magic Lamp** at the bottom archway and **Genie's face** in the center window.
  * There are no "blue and gold fountains from the roofs"; the rooftop/perimeter fireworks are **fanned comets** that fire in three distinct color waves: **White, Red, and Green** (07:15–07:17).
  * The aerial shells are predominantly **warm gold/brocade willows**, not plain white shells.
* **What's missing:**
  * The iconic twin crossing gold comets over the central spire (07:07).
  * The emerald-green turret roofs mapped onto the castle towers.
  * The rapid 3-color horn-stab fan burst (white $\rightarrow$ red $\rightarrow$ green) at 07:15–07:17, which is the visual climax of this musical phrase.

</details>

### 5.3 Trashin' the Camp

- **Audio:** 428-446 s (7:08-7:26, 18 s) · **Video:** `--start 7:18 --end 7:36`
- **Our score now:** Vivid green and chartreuse, green flares and green and orange comets on the drums, green searchlights. Characters: Terk.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 7:15-7:39 · notes: none</summary>

Here is the detailed breakdown of the segment for your LED matrix recreation:

**1. Where this part starts and ends**
* **Start:** **07:18**. Your estimate of 07:18 is **exact**. At 07:18, the prior "Friend Like Me" music cue and blue/multi-colour fireworks resolve. The brass horn riff and heavy percussive beat of "Trashin’ the Camp" (from *Tarzan*) begin, the castle projections instantaneously transition to vibrant lime/chartreuse jungle tones with animal prints, and Terk appears on the main gate.
* **End:** **07:37**. Your estimate of 07:36 is slightly early by about 1 second. At **07:37**, a sudden deep percussive crash/hit occurs alongside a blinding single-frame flash and launch of bright green comets from the roofline, transitioning into the vocal riff/vocalisation leading into the next segment (the music shifts to Hakuna Matata / Lion King percussion at 07:38–07:39).

**2. Music**
* **Track:** *"Trashin' the Camp"* from Disney’s *Tarzan* (instrumental/scat mix).
* **Audio timeline & lyrics:**
  * **07:18–07:20:** Upbeat big-band swing horn riff and heavy syncopated drum kit beat intro.
  * **07:20–07:23:** Scat vocal line: *"Za-ba-da-doo-bee, do-ba-da-doo-bee-dab-bee-yap-bam!"* landing on a hard percussive drum hit at **07:24**.
  * **07:25–07:28:** Second scat vocal line: *"Za-ba-da-doo-bee, do-ba-da-doo-bee-dab-bee-yap-bam!"* landing on a massive crash/brass hit at **07:28**.
  * **07:29–07:34:** Horns and drum kit swing breakdown, accelerating rhythm.
  * **07:34–07:36:** Drawn-out scat vocalisation: *"Ooo-weee-aaa-ooo-ooo..."*
  * **07:37:** Heavy drum accent hit, cutting the scatter rhythm abruptly.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle Projections & Base Light | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **07:18** | Prior high bursts fade; brief sky lull. | Blue sky searchlights sweep upward. | Castle shifts instantly to deep green/chartreuse jungle pattern; windows illuminated green/gold. | Terk (gorilla) appears in center gate archway (bottom-center). |
| **07:20** | Dual low fan bursts: angled green comet tails with red/orange tips fire outward left and right. | Bright neon-green laser beams shoot out from lower castle flanking walls to the sides/sky. | Bright chartreuse/yellow geometric/tribal patterns pulse on castle facade. | Terk drumming/scatting in center gate; Tantor’s trunk/face visible above. |
| **07:24** | Heavy drum beat: White/gold spherical peony bursts directly above spire. | Green laser beams fan out horizontally; searchlights swing outward. | Castle flashes lime green on drum hit. | Terk actively animated in bottom-center frame. |
| **07:26** | Sky briefly quiet; launching trails rising. | Bright green laser beams shoot straight diagonally right and left. | Vivid chartreuse and dark green jungle foliage textures. | Tantor (elephant) clearly visible on upper central wall/tower (center-mid/top). |
| **07:28–07:30** | Massive hit: Giant green and red/magenta peony bursts high above spire, accompanied by low fan comets. | Green lasers pulse; searchlights sweep across the sky. | Castle walls flash bright yellow-green. | Terk (center-bottom) and Tantor (center-mid) bouncing to the beat. |
| **07:31–07:33** | Large golden willow / brocade burst high center, drifting down over spire. | Searchlights pan across sky in blue/white beams; green stage lights pulse at base. | Dynamic shifting tribal/jungle textures across all turrets. | Terk and jungle friends animated in projection center. |
| **07:34–07:36** | Red-orange peony/crossette burst at mid-right height. | Green searchlight/laser beams sweep upward; base floods in emerald green. | Saturated emerald and lime green facade lighting. | Final scat animations of Terk; Tantor pulls back. |
| **07:37** | Sharp fan of 4 bright green comets launches upward from castle lower roofline/battlements. | Full stage flash; searchlights swing wide. | Abrupt flash to solid emerald green wash, resetting projections. | Terk projection fades out as transition begins. |

**4. Fireworks in the sky**
* **07:20–07:22:** Low-to-mid angled fan: 4–6 angled comet tails firing left and right simultaneously, splitting into bright neon green tails with distinct red/orange starburst tips.
* **07:24:** 1 medium-sized white/gold chrysanthemum/peony directly centered directly above the central high spire.
* **07:28–07:30:** High barrage: 2 large simultaneous floral bursts (peonies) directly overhead/high center — bright emerald green mixed with vibrant red/magenta stars, followed by a secondary lower golden sparkle.
* **07:31–07:33:** 1 large golden brocade/willow shell high center, cascading down in soft gold tentacles over the upper spire.
* **07:34–07:36:** 1 medium red-orange peony/dahlia bursting to the mid-right side of the upper castle spire.
* **Total sky bursts:** ~5 distinct sky shell events (plus low angled fan shots). Sky rhythm is syncopated, firing precisely on the vocal scat punctuations at 07:20, 07:24, and 07:28.

**5. Fireworks on the castle**
* **07:20 & 07:28:** Low launch tubes mounted immediately behind the castle perimeter/rooftops eject low angled angled comets outward left and right.
* **07:37:** A tight, symmetric fan of **4 bright green comet tails** fires directly upward from the castle lower battlements/roofline, marking the hit at the end of the scat routine.

**6. Lasers and lighting**
* **Lasers:** Vivid neon green laser beams originate from the flanking hub walls/lower castle terraces (left and right of the main moat). At **07:20–07:28**, they emit sharp, tight green slicing beams pointing diagonally outward and upward into the night sky, scanning back and forth across the front of the castle.
* **Searchlights:** Four to six narrow-beam robotic fixtures on the flanking roofs sweep skyward in cool white/pale cyan during the transitions, alternating with emerald green uplighting.
* **Flames/Fountains:** No real flames or water fountains are used in this specific short segment.

**7. The castle**
* **Base wash lighting:** Dominated entirely by **electric lime green and chartreuse**, with deep forest green shadows around the outer lower turrets and perimeter walls.
* **Projections:**
  * **07:18–07:36:** The entire castle surface is covered in stylized, vibrant jungle patterns, tropical foliage, and geometric tribal animal motifs (bright yellow, lime green, and teal). 
  * Turret cones and spires are mapped with glowing yellow/green textures.
  * Center gate and central facade are used as the primary video screen for character animation.

**8. Characters**
1. **Terk (Gorilla from *Tarzan*):**
   * **Location:** Center gate / lower-central facade (Grid position: **Center-Bottom**).
   * **Size:** Spans roughly the height of the main entryway gate (approx. 1/5 of the total castle height).
   * **Movement:** Centered, energetic drumming, gesturing, and scatting facing forward, synchronized to the vocal audio.
   * **Timing:** Appears at **07:18**, animates continuously, fades at **07:37**.
2. **Tantor (Elephant from *Tarzan*):**
   * **Location:** Upper central facade/main balcony level directly above the gate (Grid position: **Center-Middle**).
   * **Size:** Trunk, head, and eyes span roughly 1/4 the castle width; approx. 1/6 the castle height.
   * **Movement:** Trumpeting with trunk curling upward and swaying along to the brass lines.
   * **Timing:** Clearly visible from **07:20** through **07:33**.

**9. For our boards (LED matrix recreation tips)**
To convey this segment instantly on a 64x32 or 64x64 matrix:
1. **The Signature Color Palette:** Switch the entire castle palette to **lime green and chartreuse** with gold windows on the exact downbeat at **07:18**.
2. **The Scat Accents (07:20 & 07:28):** Mirror two outward-angled comets (green trails with orange tips) on the scat punchlines, followed by sharp green diagonal laser lines slicing outward from the castle base.
3. **Character Representation:** A 10–12 pixel animated dark grey/brown gorilla (Terk) drumming inside the bottom center gate archway, with a small pink/red elephant trunk (Tantor) bobbing directly above the gate.
4. **Cutoff Hit (07:37):** A 1-frame green screen flash + 4 vertical green pixel comet lines firing up from the castle roofline.

**10. What you couldn't see**
* Exact perimeter ground launch tubes behind the castle are hidden behind castle parapets.
* Details on the far left and far right outer perimeter towers are slightly washed out due to brightness saturation.

**11. Our version**
* **What’s right:** "Vivid green and chartreuse", "green flares", "green and orange comets on the drums", and "Terk" are all spot on.
* **What’s wrong:** Calling the lights "green searchlights" is slightly inaccurate; the sharp moving beams cutting across the castle are **neon green laser beams** (the searchlights themselves mostly sweep in cyan/white high in the sky).
* **What’s missing:** 
  1. **Tantor (the elephant):** He is prominently projected directly above Terk on the central wall throughout the scat sequence.
  2. **High floral bursts:** The major sky pyro hits at **07:24** (gold peony) and **07:28** (large green/red duo peony).
  3. **The 07:37 transition hit:** The synchronized 4-comet green fan blast that terminates the scat routine.

</details>

### 5.4 Hakuna Matata

- **Audio:** 446-459.3 s (7:26-7:39, 13.3 s) · **Video:** `--start 7:36 --end 7:49`
- **Our score now:** A teal-green flash on the change (video 7:37), then the castle magenta-pink under a nearly empty sky. Characters: Timon, Pumbaa.
- **To check by eye and ear:** Gemini's answer below says this isn't Hakuna Matata but The Bare Necessities (Mowgli and Baloo, to 7:36) then *Tangled*'s "I've Got a Dream" (the Corona sun, Pascal at the gate, from 7:39). Unconfirmed: Whisper on our split-out vocals (audio 425-465) hears only "oh, oh" scat, no lyrics either way, and Gemini has misplaced Tangled once already (4.3).
- **Checked by eye (2026-10-14):** it is Hakuna Matata (Gemini's Bare Necessities here is wrong), and it runs until Toy Story starts at about video 7:50.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 7:33-7:46 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** Exactly at **07:37**, marked by the final upbeat jazz horn hit of *The Bare Necessities* ending, an immediate fanfare/drum beat launching angled green comets, and the transition into the jaunty pub-style melody of *"I've Got a Dream"* from *Tangled*. 
* **End:** This clip ends at **07:46** while *"I've Got a Dream"* is still actively playing.
* **Accuracy of your 07:36 to 07:43 range:** Your timing is **late for the start** (the transition begins cleanly at 07:37) and **early for the end** of the musical section (the *Tangled* segment continues well past 07:43 through the end of the clip). Most importantly, **this is not "Hakuna Matata"**; it transitions from *The Jungle Book* (*The Bare Necessities*) straight into *Tangled* (*I've Got a Dream*).

**2. Music**
* **07:33 – 07:36:** *"The Bare Necessities"* (*The Jungle Book*) concluding with jazz brass, percussion, and Baloo’s scat vocal ("Yeah man!").
* **07:37:** Big percussion hit and transition chord into *"I've Got a Dream"* (*Tangled*).
* **07:38 – 07:46:** Pub accordion, piano, and brass playing the bouncy opening melody of *"I've Got a Dream"* with the Snuggly Duckling ruffians singing the chorus rhythm (*"I've got a dream! I've got a dream!..."*).

**3. Timeline**

| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **07:33 – 07:36** | Crackling gold/white willow/peony bursts and red/orange peonies fading in the upper sky. | White/light-blue searchlight beams pointing outward from behind the castle sides. | Jungle/forest green wash on walls, foliage textures, clock face illuminated. | Mowgli and Baloo dancing inside the lower center balcony window (fading out by 07:36). |
| **07:37 – 07:38** | Symmetrical low angled fan of bright green comets/mines shot from both flanks. | Green ambient wash lighting across the hub and castle base. | Bright emerald green flash, jungle patterns transitioning to dark stone/wood textures. | Transition; no character prominent. |
| **07:39 – 07:40** | Sky clears of major bursts. | Blue searchlight beams narrow behind the spires. | Castle lighting shifts dramatically to vivid magenta, pink, and violet. | Corona kingdom patterns start forming; golden Tangled sun crest appears over the clock face. |
| **07:41 – 07:42** | Single medium-high pink/golden peony shell bursts to the upper left of the spire. | Purple wash on castle facade, narrow blue beams behind. | Bright violet/purple towers, glowing yellow window arches, Corona sun emblem in center. | Pascal (the chameleon) appears in vivid lime green at the center bottom entrance archway. |
| **07:43 – 07:46** | Sky clear of major shell bursts; camera zooms in. | Pink and purple architectural floodlights wash the castle walls and spires. | Saturated pink/magenta spires and upper facade, deep blue turret roofs, glowing warm windows. | Pascal stands/moves at the center bottom doorway arch against the purple background. |

**4. Fireworks in the sky**
* **07:33 – 07:36:** 
  * Chrysanthemum/peony bursts in gold/white crackle and red/orange fill the upper sky directly above and behind the central spire (roughly 2–3 bursts per second, fading out at 07:36).
* **07:37 – 07:38:** 
  * Low/mid-height angled comet mine fan: approximately 3 bright neon-green comets on the left and 3 on the right, shooting outward symmetrically from behind the castle walls at roughly 45-degree angles.
* **07:39 – 07:40:** 
  * Sky goes quiet/dark with no new burst shells.
* **07:41 – 07:42:** 
  * Exactly 1 round peony shell in pink/rose with a soft golden center bursts high to the upper left of the main spire.
* **07:43 – 07:46:** 
  * Sky remains dark/quiet (no overhead sky bursts during the zoom-in).

**5. Fireworks on the castle**
* None fired directly from the turrets, parapets, or roof ledges during this specific clip (the comet fans at 07:37 launch from ground positions/launch sites directly behind the flanking walls).

**6. Lasers and lighting**
* **Lasers:** No visible overhead beam lasers during this segment.
* **Searchlights:** Cool-white and light-blue narrow searchlight beams fan upward from behind the left and right castle terraces (07:33–07:40), then dim down as the castle zooms in.
* **Hub/Perimeter Lighting:** Flashes bright green at 07:37 to match the comet launch, then transitions to deep purple and pink ambient wash lighting along the trees and hub.

**7. The castle**
* **Base & Turret Lighting:**
  * **07:33 – 07:38:** Emerald green wash across the entire lower facade, green spires, glowing green side turrets.
  * **07:39 – 07:46:** Dramatic instantaneous shift to rich magenta/pink lighting across the main facade, deep blue on the conical turret roofs, and warm golden illumination in the lower portals and window cutouts.
* **Projections:**
  * **07:33 – 07:36:** Jungle Book leafy vine textures and jungle stone.
  * **07:39 – 07:46:** The *Tangled* motif: the iconic golden Corona Sun symbol projected directly over the central clock/rose-window area, surrounded by purple and gold decorative bunting/tapestry patterns.

**8. Characters**
* **Mowgli & Baloo:**
  * **Location:** Projected inside the center balcony frame (grid center: (2,2)).
  * **Size:** Small, roughly 1/6th the height of the castle facade.
  * **Movement:** Dancing/grooving in place.
  * **Times:** Visible up to **07:36**, fading out as the music changes.
* **Pascal (from *Tangled*):**
  * **Location:** Lower-center base (grid bottom-center: (3,2)), right above/inside the main gate tunnel archway.
  * **Size:** Small, about 1/10th the height of the castle facade.
  * **Movement:** Appears as a bright lime-green silhouette, standing/scampering on the archway ledge against the dark/purple background.
  * **Times:** Appears at **07:41** and remains through **07:46**.
* *(Note: Timon, Pumbaa, and Simba do not appear anywhere in this sequence).*

**9. For our boards**
1. **The Instant Color Switch at 07:39:** Switch your matrix background instantly from jungle green to a vibrant split of bright magenta/purple on the castle walls and deep royal blue on the turret roofs.
2. **The 07:37 Green Comet Fan:** Fire symmetrical diagonal green comets (or streaks) outward from both sides of the castle base on the musical transition beat.
3. **The Corona Sun & Pascal:** A bright yellow/gold circular sun emblem at the center clock position, with a small, glowing lime-green sprite (Pascal) at the bottom-center archway against the purple castle base.

**10. What you couldn't see**
* Around **07:42**, the camera operator zooms in tightly onto the castle facade, cutting off the outer peripheral trees, perimeter launch locations, and upper sky edges for the rest of the clip.
* Precise details of secondary character artwork inside the lower windows at 07:43–07:46 are partially obscured by the exposure and zoom motion.

**11. Our version**
* **What's right:** You correctly identified that a transition happens in this time frame (07:36/07:37).
* **What's wrong:** 
  * The song is **not** "Hakuna Matata" and the characters are **not** Timon and Pumbaa. The music is *"I've Got a Dream"* from *Tangled*.
  * The color scheme is **not** sunset yellow, orange, and red; the castle shifts into vivid **magenta, violet/purple, and royal blue**, accented by a **golden yellow sun**.
  * The shell at 07:41 is a single pink/magenta and gold peony, not a barrage of red and gold shells.
* **What's missing:** 
  * The symmetrical fan of neon-green comets at 07:37.
  * The Corona sun emblem projected over the castle clock.
  * Pascal (the lime-green chameleon) projected at the main gate arch.

</details>

### 5.5 You've Got a Friend in Me

- **Audio:** 459.3-473.3 s (7:39-7:53, 14 s) · **Video:** `--start 7:49 --end 8:03`
- **Our score now:** Toy Story from video 7:50: Woody and Buzz on Andy's cloud wallpaper, the castle in primary-coloured blocks; red and yellow bursts. Characters: Woody, Buzz.
- **V2:** stage castle; actors buzz_woody (Buzz flies across, Woody waves from the ground).
- **Checked by eye (2026-10-14):** Toy Story starts at about video 7:50. Bare Necessities comes after it, in the green part of 5.6.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 7:40-7:52 · notes: none</summary>

Here is the breakdown of this section of *Happily Ever After*:

**1. Where this part starts and ends**
* **The user’s estimate (07:43 to 07:49) is early/incorrect for “You’ve Got a Friend in Me”.** 
* **07:40 – 07:42:** The final crescendo and big firework blast of the preceding **“Friend Like Me”** (*Aladdin*) section concludes.
* **07:42 – 07:49:** This segment is actually **“The Bare Necessities”** (*The Jungle Book*), marked by a swing jazz clarinet intro starting at 07:42 and a green neon projection of Baloo dancing in the lower center gate/balcony.
* **07:49 – 07:50:** **“You’ve Got a Friend in Me”** (*Toy Story*) only **begins** at **07:49/07:50**, marked by a musical tempo shift into the relaxed Randy Newman stride-piano/shuffle beat and the castle projections snapping into bright primary-colored Toy Story alphabet building blocks.

**2. Music**
* **07:40 – 07:41:** Big brass Broadway finish of *“Friend Like Me”* with a sustained cymbal/percussion and crowd roar.
* **07:42 – 07:49:** *The Jungle Book* – **“The Bare Necessities”**:
  * **07:42:** Upbeat swing jazz clarinet/dixieland band instrumentation begins.
  * **07:46 – 07:48:** Baloo’s vocal line kicks in (*“The bare necessities of life will come to you...”*).
  * **07:47:** Strong percussion downbeat accompanied by a gold aerial shell explosion.
* **07:49 – 07:51:** *Toy Story* – **“You’ve Got a Friend in Me”**:
  * **07:49 – 07:50:** Transition into the iconic ragtime/jazz piano intro of *“You’ve Got a Friend in Me”*.
  * **07:51:** Musical accent hit synced with a bright red aerial burst on the left.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **07:40** | White/gold rising comet tails behind both flanks | Blue/violet upward spotlights from hub | Purple base, gold spires, Genie portal artwork | Genie (*Aladdin*) fading out |
| **07:41** | Massive gold/white chrysanthemum burst high left | Searchlights sweep skyward | Deep royal purple and gold wash | Archway transitions |
| **07:42 – 07:45** | Quiet sky; low residual embers drifting down | Sconce lights glow magenta/pink | Walls wash in magenta/deep violet with blue turret roofs | Neon lime-green silhouette of Baloo dancing in the central portal |
| **07:46 – 07:48** | Large golden brocade/chrysanthemum shell bursts high left (07:47) | Violet accent floodlights on outer towers | Castle remains magenta/violet with blue roofs | Baloo continues dancing in center portal |
| **07:49 – 07:50** | Sky briefly dark; launch trails rising | Lights shift toward warm amber and cyan | Projection wipe: multicolored children's building blocks appear across main facade | Baloo fades out; Toy Story graphic theme begins |
| **07:51** | Medium bright red peony/ring shell bursts mid-high left | Yellow/cyan washes on lower walls and turrets | Bright yellow, red, and blue blocks with letters/toys on lower facade; green & blue towers | Toy blocks / Andy's room motifs; characters not yet fully resolved |

**4. Fireworks in the sky**
* **07:40 – 07:41:** 
  * Two pairs of thick white/gold comet trails launched from behind both flanks.
  * 1 large spherical gold/white chrysanthemum burst at high altitude on the upper left.
* **07:42 – 07:46:** 
  * Sky is dark/quiet (gap between musical numbers).
* **07:47 – 07:48:** 
  * 1 large golden brocade/peony shell bursting high left of the main spire on Baloo's vocal accent.
* **07:50 – 07:51:** 
  * 1 medium-sized vibrant red peony (with inner white/silver core) bursting mid-to-high altitude to the left of the spire at 07:51.
* **Rhythm:** Sparse, single accent shells (roughly 1 burst every 3–4 seconds) emphasizing musical syncopations.

**5. Fireworks on the castle**
* None fired directly from castle turrets, ledges, or battlements during this sequence (all effects originate from perimeter launch sites behind the castle).

**6. Lasers and lighting**
* **Lasers:** No sharp overhead laser beams active during these 10 seconds.
* **Searchlights:** Narrow violet and cyan moving searchlights mounted in the moat/hub sweeping up toward the sky at 07:40–07:41, settling into static side-fill washes on the trees and outer turrets by 07:43.
* **Flames/Fountains:** None active.

**7. The castle**
* **07:40 – 07:48 (*The Bare Necessities*):** 
  * Castle body is illuminated in deep violet-magenta and indigo.
  * Turret roofs are royal blue.
  * Sconces and clock tower edges glow in warm gold.
* **07:49 – 07:51 (*Toy Story* transition):**
  * Projections snap on: the lower middle facade transforms into vibrant primary-colored alphabet blocks (yellow, red, green, and blue cubes).
  * Upper walls and turrets take on bright lime green and cyan lighting.

**8. Characters**
* **Genie (*Aladdin*):**
  * Visible until 07:40–07:41 inside the central portal/lower castle; fades as the song ends.
* **Baloo (*The Jungle Book*):**
  * **Location:** Lower-center gate/balcony archway (bottom-center 3x3 grid).
  * **Size:** Small, roughly 1/6 to 1/8 of total castle height, confined to the main arch above the front gate.
  * **Appearance:** Stylized, glowing lime-green neon silhouette outline.
  * **Movement:** Bouncing, dancing/waddling rhythmically side to side.
  * **Time:** Appears at 07:42, dances continuously, and fades out at 07:49.
* **Woody & Buzz (*Toy Story*):**
  * Not yet visible on the castle during 07:43–07:49; only the toy block background elements begin appearing at 07:50–07:51.

**9. For our boards (LED matrix recreation)**
1. **Accurate Song Transition:** Do not start *Toy Story* graphics at 07:43. At 07:42–07:49, show a purple castle with a simple green dancing bear silhouette (Baloo) in the gate archway.
2. **Palette Snap at 07:50:** The entire mood changes instantly at 07:50—switch the castle LEDs abruptly from deep purple/blue to vibrant checkerboard primary colors (red, yellow, cyan blocks).
3. **Firework Accents:**
   * Single gold burst at top-left at 07:47.
   * Single red burst at top-left at 07:51 on the beat.

**10. What you couldn't see**
* The camera zooms in between 07:42 and 07:46, cutting off the outer perimeter launch points and side trees.
* Projections at the very bottom base of the castle are partially obscured by guest heads/silhouettes in the foreground.

**11. Our version**
* **What's right:** Woody, Buzz, and Andy's room elements belong to the *“You’ve Got a Friend in Me”* portion of the show.
* **What's wrong:** 
  * The timing: 07:43 to 07:49 is **not** *Toy Story* / *“You’ve Got a Friend in Me”*. It is *The Bare Necessities*.
  * Woody and Buzz do not appear between 07:43 and 07:49.
  * There is no cloud wallpaper shown here yet.
* **What's missing:**
  * Baloo (green silhouette) dancing in the gate arch from 07:42 to 07:49 over a purple castle wash.
  * *Toy Story* only begins loading its block graphics onto the castle at 07:50.

</details>

### 5.6 Friendship mash-up

- **Audio:** 473.3-514 s (7:53-8:34, 40.7 s) · **Video:** `--start 8:03 --end 8:44`
- **Our score now:** In order (video times): Bare Necessities, the castle green with the Jungle Book characters dancing (8:04); Ralph on a pink castle (8:12); Baymax in his super suit with Hiro, blue towers (8:16); Nick and Judy in the gate, chased off by a rolling doughnut; Inside Out's memory orbs filling the castle, Joy and Sadness (8:30); Mike and Sulley among scream canisters (8:36); multicolour searchlights, steady pastel bursts. The castle stays up throughout, turning with each bit: green (Bare Necessities), pink (Ralph, 480.3), blue (Baymax, Zootopia and Inside Out, 486.3), Monsters, Inc. teal and purple (Mike and Sulley, 505.5). Characters: Baloo, Ralph, Hiro, Baymax, Judy, Nick, Joy, Sadness, Mike, Sulley.
- **V2:** stage off; actors ralph, baymax, memory_orbs (Ralph smashes bricks (0-14 s in), Baymax inflates and waves (15-22), Joy's and Sadness's memory orbs (35-54)).
- **Checked by eye (2026-10-14):** in order: Toy Story (from 7:50); the castle turns green for Bare Necessities, with the Jungle Book characters dancing (about 8:04); the castle turns pink and Wreck-It Ralph appears (about 8:12); back to blue-topped towers for Baymax in his super suit with Hiro (about 8:16); Nick and Judy at the bottom, in the gate, then a doughnut rolls over the castle and chases them off (Zootopia); the whole castle fills with Inside Out's memory orbs, with Joy and Sadness (about 8:30); then Mike and Sulley, surrounded by scream canisters (about 8:36). Vanellope wasn't mentioned.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · claude-opus-5-5-local-frames · video 7:46-8:47 · notes: none</summary>

_Watched by Claude from frames (one every 2 s, plus close crops of the castle), not by Gemini: the free key was out of quota. The captions only say "[music]", so there is nothing here about the music; check timings by ear._

**1. Where this part starts and ends**
* The scene is really six short segments, not one mash-up: Toy Story first, then Ralph and Vanellope, Zootopia, Inside Out and Monsters, Inc.
* **07:49-07:50:** the castle switches from Bare Necessities' purple and magenta to Toy Story's primary-coloured blocks.
* **08:42-08:44:** it ends on the Monsters, Inc. doors; the two red and gold peonies at 08:44 open 5.7.

**2. Timeline**
| Video | Castle | Characters | Fireworks | Lighting |
| :--- | :--- | :--- | :--- | :--- |
| 07:50-08:03 | Toy blocks: red, yellow and blue walls, blue roofs | Woody and Buzz, small, in the gate arch | Small red and gold peonies by the spire (07:52-07:56), a big pink chrysanthemum left of the spire (07:58), a green-white ring (08:02) | Green and blue searchlight fans from both sides |
| 08:04-08:10 | Lime green and blue, white figures in the central tower window and the side windows | Not identified (white silhouettes; possibly a dancer and a dark-haired figure in the gate) | Gold crackle behind the spire, a pink peony high right (08:08) | Searchlights off |
| 08:12-08:15 | Pink walls, teal candy-striped roofs, a round emblem over the gate | Probably Sugar Rush (Vanellope); a dark-haired figure in the gate | Big pink-gold chrysanthemums either side of the spire (08:10-08:12), a gold ring (08:14) | None |
| 08:16-08:28 | Blue and red-gold, a ZPD badge banner on the central tower (08:24), a doughnut wheel on the left (08:26) | Zootopia: an orange figure (Nick) in the tower windows at 08:18-08:22 | A white-gold horizontal fan left (08:16); pairs of red and gold chrysanthemums over the spire (08:22-08:26); green-gold willows (08:28) | Violet-blue searchlight fans from both sides |
| 08:30-08:35 | Goes dark, then the central tower and windows fill with rainbow-coloured memory orbs | Inside Out: Joy (yellow) and Sadness (blue), small, in the gate | A gold burst low left (08:34), red bursts behind the castle | Searchlights off |
| 08:36-08:41 | Yellow and blue, a vertical Monsters, Inc. sign on the tower, a lit balustrade over the gate | Sulley (blue) and Mike (green) in the gate | White gerbs and fountains along the castle front and both flanks (08:36-08:40) | White floods from the flanks |
| 08:42-08:44 | Pink centre, door projections | Monsters, Inc. doors | Small gold bursts behind the spire | None |

**3. Our version**
* **Right:** Ralph and Vanellope, Judy and Nick, and Joy and Sadness are all here, in the gate and tower; multicolour searchlights and pastel bursts fit the Toy Story and Zootopia parts.
* **Wrong:** our 5.6 has no Toy Story, but Toy Story fills its first 13 s. The order is probably Toy Story, an unidentified green part, Sugar Rush, Zootopia, Inside Out, then Monsters, Inc.: our 5.7 (Sulley and Mike) really starts at about 08:36, inside this window.
* **Missing:** the white gerb and fountain line along the castle at 08:36-08:40; the ZPD badge; the castle going dark for the Inside Out memory orbs.
* **Hiro and Baymax:** I couldn't see them. The green 08:04-08:10 part may be them (the white figure in the tower), but nothing confirms it: re-watch 08:04-08:10 by eye or with Gemini.

**4. What I couldn't see**
* Anything about the music: I had no audio track to check, only frames.
* At this zoom the characters are a few pixels tall; Woody, Buzz, Nick, Joy, Sadness, Sulley and Mike are clear from colour and shape, the 08:04-08:15 figures are not.

</details>

### 5.7 That's What Friends Are For

- **Audio:** 514-527 s (8:34-8:47, 13 s) · **Video:** `--start 8:44 --end 8:57`
- **Our score now:** The castle itself sings it, its stonework coming alive; two red and gold peonies on the opening hit; soft gold shells; small gold bursts on the bass line (video 8:45, 8:49), a dark sky otherwise. Characters: none.
- **V2:** stage castle; actors mike (Mike peeks over the left turret, then the right).
- **Checked by eye (2026-10-14):** it comes right after Mike and Sulley, and the castle itself sings it: its stonework animates, with no characters. Sulley and Mike belong at the end of 5.6, not here.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 8:41-9:00 · notes: none</summary>

Here is the detailed breakdown of the segment for your LED matrix recreation:

**1. Where this part starts and ends**
* **Start:** **08:44** — Marked by a heavy musical bass beat and the launch/burst of twin aerial shells as the *Monsters, Inc.* door projections transition into a framed central archway. The deep bass vocal entry starts at **08:46**.
* **End:** **08:57** — Marked by the end of the held vocal note, a bright chime/transition chord in the score, a sudden purple wash over the castle, outward-fanning searchlight beams, and Corona sun emblems (*Tangled* segment).
* **Evaluation of 08:44 to 08:57:** Your timestamp range is **exact**.

**2. Music**
* **Song:** *"That's What Friends Are For (The Vulture Song)"* from *The Jungle Book* (1967).
* **Style:** Barbershop quartet / deep bass-baritone solo.
* **Lyrics & Timestamps:**
  * **08:44:** Orchestral beat/impact announcing the transition.
  * **08:46:** *"That's..."* (deep bass note).
  * **08:48:** *"...what..."*
  * **08:49:** *"...friends..."*
  * **08:51:** *"...are..."*
  * **08:53 – 08:56:** *"...foooor..."* (held sustained note fading into chime).
  * **08:56 – 08:57:** Orchestral transition chime/flourish into the *Tangled* motif.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **08:41 – 08:43** | Low gold/white comet trails fade out on flanks | Blue and amber floodlights on lower turrets | Colorful door grid projection (turquoise, purple, orange) | Sulley (lower center archway) |
| **08:44 – 08:45** | Two high red/gold peony shells burst symmetrically left and right of spire | Floodlights stay warm amber on trim, dark blue on facade | Doors collapse; castle shifts to dark navy/royal blue with a golden gothic frame in the central lower portal | Transition/empty portal |
| **08:46 – 08:50** | Sky is dark / no launches | Static floodlights; no lasers | Deep blue walls; glowing warm-yellow portal in center | Four Vultures (*The Jungle Book*) perched on a branch in center portal |
| **08:51 – 08:55** | Sky remains dark | Static floodlights | Portal shifts to warm yellow/stained-glass hue | Quasimodo embracing a gargoyle (*The Hunchback of Notre Dame*) |
| **08:56 – 08:57** | Quiet sky; single rocket ascent begins behind spire | Searchlight beams suddenly ignite, fanning outward in purple and white | Castle instantly washes in deep violet/magenta; glowing yellow Corona suns appear across facade | Vultures/Quasimodo vanish |
| **08:58 – 08:59** | Large gold chrysanthemum bursts high directly behind spire | Searchlights sweep across the sky | Purple wash with floating sun symbols | Transition to Rapunzel segment |

**4. Fireworks in the sky**
* **08:44 – 08:45:** Exactly **two** high-altitude aerial shells.
  * *Type:* Peony/chrysanthemum with ruby red outer stars and glittering gold/white centers.
  * *Position:* High sky, symmetrically mirrored (one on the left, one on the right of the central spire).
* **08:46 – 08:56:** **0 bursts**. The sky is completely dark and quiet during the vocal line to draw full focus to the vocal quartet and the central projection portal.
* **08:58 – 08:59:** Exactly **one** large gold willow/chrysanthemum shell bursting at high altitude directly over the central spire on the next musical beat.

**5. Fireworks on the castle**
* **None.** There are no fountains, gerbs, strobes, or rooftop pyro fired from the castle structure itself between 08:44 and 08:57.

**6. Lasers and lighting**
* **08:44 – 08:56:** No visible lasers. Base facade floodlights maintain a deep navy blue body with warm golden-amber lighting along the turret balconies, roofs, and window trim.
* **08:56 – 08:57:** High-powered stage searchlights/beam fixtures behind and beside the castle turn on and fan upward/outward at roughly 45° angles into the sky in bright violet and white.

**7. The castle**
* **Base Lighting:** Dark royal blue on main stone walls, warm gold/amber accent lighting outlining turrets and spires.
* **Projections:**
  * **08:44:** The colorful mosaic doors from *Monsters, Inc.* dissolve. The facade turns to dark stone with an ornate gothic arch highlighted in gold around the lower center entrance.
  * **08:46 – 08:55:** The projection is strictly confined to the **lower center archway portal** with a warm yellow/gold interior glow.
  * **08:56 – 08:57:** Instant wipe to an overall royal purple/magenta castle wash with multiple bright golden-yellow sun emblems (Corona crests from *Tangled*) projected across the lower walls, central tower, and side turrets.

**8. Characters**
1. **The Vultures (Buzzie, Flaps, Ziggy, Dizzy from *The Jungle Book*)**
   * *Location:* Bottom-center (lower 1/3 of the castle, inside the main gateway arch).
   * *Size:* Small (approx. 1/6 of total castle height, confined entirely inside the lower portal).
   * *Movement:* Perched on a branch, slightly swaying/bobbing to the barbershop rhythm.
   * *Duration:* Appear at **08:46**, dissolve at **08:50**.
2. **Quasimodo & Gargoyle (*The Hunchback of Notre Dame*)**
   * *Location:* Bottom-center (same lower archway portal).
   * *Size:* Approx. 1/6 of castle height.
   * *Movement:* Static silhouette/figure, Quasimodo shown embracing a gargoyle.
   * *Duration:* Appears at **08:51**, fades out at **08:56**.

**9. For our boards**
To capture this 13-second moment on a 64x32 or 64x64 matrix:
1. **08:44 Hit:** Fire exactly two symmetrical red-and-gold 5x5 or 7x7 pixel burst clusters high on either side of the spire.
2. **08:46 – 08:55 Contrast:** Keep the sky **completely black** and castle facade **dark blue**. Light only a small 6x8 pixel arched doorway at the bottom center in bright warm amber/yellow, displaying a small perched vulture cluster.
3. **08:56 Transition:** Instantly shift the castle silhouette to deep purple, turn on 2–4 upward diagonal beam lines (searchlights), and light a single high gold shell over the spire at 08:58.

**10. What you couldn't see**
* **Perimeter Launchers:** Ground-level launch sites are hidden behind tree lines and castle walls.
* **Vulture Facial Detail:** Due to distance and exposure, the four vultures appear primarily as dark silhouettes against the warm glowing interior archway rather than full high-detail character art.

**11. Our version**
* **What's right:** You correctly identified the turquoise/purple door projections and Sulley, but that is the **previous** segment (*Monsters, Inc.* / "If I Didn't Have You"), which ends at **08:43**.
* **What's wrong:**
  * For "That's What Friends Are For" (08:44–08:57), the characters are **not** Sulley and Mike.
  * There are no doors on the turrets during this song.
  * The aerial shells at 08:44 are not generic "soft gold shells"; they are two distinct ruby-red peonies with gold glitter centers.
* **What's missing:**
  * **The Vultures** (*The Jungle Book*) and **Quasimodo** (*The Hunchback of Notre Dame*) in the lower central archway.
  * The deliberate **dark/quiet sky** during the singing from 08:46 to 08:56.
  * The transition at 08:56–08:57 to deep purple castle lighting with fanning searchlights and yellow Corona sun emblems.

</details>

### 5.8 Friend Like Me (Genie)

- **Audio:** 527-554 s (8:47-9:14, 27 s) · **Video:** `--start 8:57 --end 9:24`
- **Our score now:** Genie in neon, the castle a pulsing marquee; crossing magenta, green and gold comets, gold chrysanthemums; red and green comet fans from the roofs (video 9:17), then a green curtain hanging over the castle on the last big note (9:21); purple castle, big gold and white chrysanthemums (video 9:03-9:08), ice-blue comet fans (9:13). Characters: Genie.
- **V2:** stage ghost; actors genie (Genie circles the spire; half V1's fireworks, so bursts don't sit on him).
- **Checked by eye (2026-10-14):** Gemini is right: at about 9:17 red and green comets fan outward from both sides of the castle, then on the last big note (about 9:21) a green shell's sparks hang over the castle like a curtain. Ours has ring shells instead.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 8:54-9:27 · notes: none</summary>

Here is the detailed breakdown of the "Friend Like Me" sequence for your LED matrix recreation:

**1. Where this part starts and ends**
* **Start:** **08:57**. Marked by the hard musical transition ending the previous *Tarzan* ballad segment ("...are found..."), followed by a bright brass swell/percussion kick, purple lighting sweep, and neon/gold dots illuminating the castle facade.
* **End:** **09:24**. Marked by the final held brass chord and vocal phrase of "Friend Like Me", as the massive green cascading kamuro/willow fall fades out. At **09:24–09:25**, the tempo shifts, castle projections change, and multi-colored vertical rainbow comets launch for the next musical cue.
* **Your estimate (08:57 to 09:24):** **Exact**.

**2. Music**
* **Song:** *"Friend Like Me"* from *Aladdin* (performed by Robin Williams / Genie).
* **Lyrics & Musical Cues:**
  * **08:57:** Jazzy brass fanfare intro / drum hit.
  * **08:59 – 09:04:** *"Mister Aladdin, sir, what will your pleasure be?"* (Heavy drum/orchestral hit at **08:59** on "Mister").
  * **09:04 – 09:07:** *"Let me take your order, jot it down..."*
  * **09:08 – 09:11:** *"...You ain't never had a friend like me!"*
  * **09:11 – 09:16:** Fast scatting/vocal break: *"Never had a friend, never had a friend, no, no! Never had a friend, never had a friend..."*
  * **09:16 – 09:21:** Big musical swell and sustained belted finale: *"Never... had... a... friend... like... meeee!"*
  * **09:21 – 09:24:** Final big brass punch/cymbal crash and sustained reverberation.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **08:57** | None | Purple searchlight beams fan outward from the hub/parapet | Castle washes purple; golden dots/circus bulbs flash across towers | None |
| **08:59** | Large gold chrysanthemum shell directly centered over the spire | Purple searchlights fan upward | Facade lights flash in Broadway marquee style | Genie appears on center facade |
| **09:01** | Low green mines/comets fire from left/right launch sites | Searchlights criss-cross | Center tower projects dynamic blue/magenta swirls | Genie animates, gestures, morphs |
| **09:04** | Large golden willow shell high center; red/green comet tails from left and right | Blue/purple searchlight fans pulse with the beat | Golden art-deco/curtain patterns on lower towers | Genie actively moving across center tower |
| **09:08** | Another large golden chrysanthemum/peony shell overhead center | Searchlights sweep outward to the sides | Marquee bulb patterns pulse around the windows/clock | Genie in center grid |
| **09:12** | Whistling arching comets shoot up from left and right flanks | Beams sweep inward | Purple/blue base with pulsating yellow diamond/neon patterns | Genie rapidly morphing / scatting |
| **09:17** | Fans of red and bright green comets launch angled outward from castle flanks | Lasers shoot forward/skyward; searchlights pulse | Castle walls glow intense magenta and electric blue | Genie stretches across upper-center tower |
| **09:21** | Massive canopy of crackling green/gold kamuro/horsetail trails drops over the spire | Sharp blue searchlights beam straight up through the fall | Deep royal blue walls with gold-accented turrets | Genie vanishes into gold sparkle effect |
| **09:24** | Cascading green sparks clear; multi-colored comets shoot straight up | Searchlights sweep wide; white flash on parapets | Transition into bright magenta/multi-color for next scene | Next segment characters begin to transition |

**4. Fireworks in the sky**
* **08:59:** 1 large high-altitude gold chrysanthemum shell centered directly above the spire.
* **09:01 – 09:03:** Low angled green/gold comets and mines from outer launch stations (left and right flanks).
* **09:04 – 09:06:** 1 large gold willow shell (center, high) accompanied by 4–6 angled red and green comets launched simultaneously from left and right perimeter pads.
* **09:08 – 09:10:** 1 large gold/white strobe chrysanthemum shell centered above the main spire.
* **09:12 – 09:16:** 6–8 serpentine/whistling comets arcing across the sky from left and right in pairs (rhythmic call-and-response during the scatting section).
* **09:17 – 09:20:** Symmetrical fan barrage: 10–12 red and emerald green thick-tailed comets shooting upwards at 45° to 60° angles on both sides of the castle.
* **09:21 – 09:24:** Climax: High aerial break of 2–3 cascading emerald green and gold kamuro/horsetail shells, raining a wide curtain of descending sparkling tentacles that hang all the way down around the castle spires.
* **Launch Rhythm:** Starts with single punctuation bursts on vocal hits (~0.5 bursts/sec), building during the scatting breakdown into rapid-fire angled comets (~2–3/sec), culminating in a massive hanging curtain shell at 09:21.

**5. Fireworks on the castle**
* **09:01 & 09:04:** Low flank/battlement comets fired from behind the side rooftops.
* **09:17 – 09:20:** Fast angled comet shots launched directly from the castle lower rooftop/parapet launch rails (angled outward left and right).
* *Note:* No continuous gerbs or silver fountains on the castle parapets during this specific 27-second window; the action is driven by perimeter launches and high aerial breaks.

**6. Lasers and lighting**
* **Searchlights:** Positioned behind and around the castle base/hub. They form wide V-fans and cross patterns in vivid purple, deep royal blue, and cyan. They sweep outward horizontally at **08:57** and point nearly vertical at the climax (**09:21**).
* **Lasers:** Bright green/cyan laser beams emerge from castle turrets/battlements, scanning above the audience during the fast scat section (**09:12–09:18**).
* **Flames/Fountains:** None used in this specific song segment.

**7. The castle**
* **Base Architectural Lighting:** 
  * Shifts instantly at **08:57** from warm earthy tones (*Tarzan*) to deep saturated purple on the lower walls and bright golden yellow on the central spire.
  * During the finale (**09:17–09:23**), shifts to electric magenta and deep royal blue.
* **Projections:**
  * **08:57 – 09:00:** Gold marquee "carnival/Broadway bulbs" pop on and off all over the castle turrets and facade.
  * **09:01 – 09:16:** The main tower becomes a dynamic cabaret stage backdrop: swirling blue smoke, magenta neon outlines, and golden art-deco patterns along the lower towers and archways.
  * **09:17 – 09:21:** Flashing pulsing concentric rings and neon geometric patterns radiating outward from the central clock window.

**8. Characters**
* **Genie:**
  * **Identity:** The Genie from *Aladdin* (projected animation).
  * **Position:** Center grid (Row 2, Column 2; projected on the main central facade directly above the clock window and stretching up the main tower).
  * **Size:** Spans approximately 1/3 to 1/2 the height of the main castle tower.
  * **Movement:** 
    * Appears at **09:00** appearing as a puff of blue neon smoke.
    * From **09:00 to 09:16**, animates vigorously to the jazz beat: clapping, waving hands, turning, leaning, and scatting.
    * At **09:17 – 09:20**, stretches vertically with arms spread wide for the sustained final lyric.
    * Dissolves/bursts into golden sparkle particles around **09:21**.

**9. For our boards**
To make this readable and authentic on a 64x32 / 64x64 matrix:
1. **The Broadway Marquee Flash (08:57):** The castle silhouette should instantly snap from dark/subtle to deep purple with flashing yellow/gold pixel "lightbulbs" chasing along the castle edges.
2. **Genie's Neon Blue Figure (09:00–09:20):** A distinct bright cyan/blue animated shape in the dead center of the castle facade, bobbing up and down to the fast jazz tempo.
3. **The Green Kamuro/Weeping Curtain (09:21–09:24):** The big visual payoff is the climax: fire a top shell that cascades slow-falling green pixels down across both sides of the castle like weeping willow tentacles.

**10. What you couldn't see**
* Exact details of the lower courtyard/base projections (blocked by audience heads and trees).
* Far left and far right perimeter ground launch tubes (off-screen; only their upward projectile trajectories into the sky are visible).

**11. Our version**
* **What's Right:** "Genie in neon, the castle a pulsing marquee" is **spot-on**—the marquee bulb projections and blue neon Genie dominate the visual aesthetic. "Genie" as the sole character is also correct.
* **What's Wrong:** "Ring shells" are **incorrect**—the aerial breaks are round gold chrysanthemums/willows and a massive weeping green kamuro curtain, not ring-shaped shells.
* **What's Missing:** 
  * The prominent **emerald green and red angled comet fans** launching from the flanks at **09:17–09:20**.
  * The climactic **cascading green willow/horsetail drop** at **09:21–09:23** that blankets the castle for the final belted note.

</details>

### 5.9 Friend Like Me (finale)

- **Audio:** 554-563 s (9:14-9:23, 9 s) · **Video:** `--start 9:24 --end 9:33`
- **Our score now:** Genie's big finish: dense magenta, red and green comets fanning out from both sides of the castle, one fan a beat, to his "Ha!". Characters: Genie.
- **V2:** stage castle; actors genie (he sings on to 563, round the full castle and its fountains).
- **Checked by eye (2026-10-14):** ignore Gemini's answer here; it isn't what the show does. Leave the scene as it is.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 9:21-9:36 · notes: none</summary>

Here is the detailed breakdown of the "Friend Like Me (finale)" segment of *Happily Ever After*:

**1. Where this part starts and ends**
* **Start:** **09:24**. Marked musically by the buildup to the vocal climax of *Friend Like Me* ("You ain't never had a friend like me!") and visually by a transition from cascading blue/white glitter trails to rapid, multi-colored vertical rising comets/mines, while Genie begins dancing across the castle projections. 
  * *Your 09:24 start time is accurate.*
* **End:** **09:33 - 09:34**. Marked by the final vocal shout ("HA!") and the punchy brass hit at **09:33**, accompanied by simultaneous twin gold/white aerial bursts over the spire and horizontal spark fountains firing from the castle roof terraces, followed immediately by silence from the fireworks at **09:34** as Genie fades out.
  * *Your 09:33 end time is accurate.*

**2. Music**
* **Song:** *"Friend Like Me"* (finale tag / big finish) from *Aladdin*.
* **Lyrics & Spoken Lines:**
  * **09:29 - 09:32:** *(Singing brassily)* *"Ain't never had a friend like me!"*
  * **09:32.5 - 09:33:** *(Shouted)* *"HA!"*
* **Big Hits & Beats:**
  * **09:24:** Driving swing tempo picks up; rising comet volleys launch in rhythm.
  * **09:31:** Emphatic drum accents on *"friend"* and *"like"*.
  * **09:32:** Big orchestral hold on *"me"*.
  * **09:33:** Final punctuation hit (*"HA!"* / cymbal crash / brass stabs), triggering the castle roof gerbs and twin aerial burst.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **09:24 - 09:27** | Continuous rapid-fire vertical comet/tracer mines launching from both sides of castle in waves (red, green, gold, magenta). Lingering crackle/whistle trails overhead. | Blue, cyan, and white spotlights sweeping and crisscrossing vertically across the lower sky behind the castle. | Facade lit in deep purple, gold, and vibrant warm tones. Architectural projection accents on towers. | Genie (bright blue) projected on the central lower facade/entrance area, dancing energetically. |
| **09:28 - 09:30** | Denser vertical comet barrages shoot upwards along castle flanks in alternating neon tones (magenta, green, white). | Spotlights fan out into wide 'V' shapes behind the castle. | Lower castle bathed in pulsating yellow and gold stage-style lighting effects. | Genie continues dynamic dance movements across the lower-center facade. |
| **09:31 - 09:32** | Sky launch pauses momentarily; crackling comets rise into the upper sky and dissipate. | Spotlights sweep straight up into sky pillars. Castle base glows in golden yellow. | Projections shift toward glowing blue and gold magic energy around Genie. | Genie swirls/poses in center base as the final vocal note sustains. |
| **09:33** | **Climax:** Two symmetrical white/gold glitter chrysanthemum bursts ignite directly above the spire, while twin horizontal white/gold spark fountains (gerbs) spray outward from the castle's mid-level roof terraces. | Bright flash of castle wash lights; spotlights beam straight up into the bursting fireworks. | Castle facade and turrets flash bright gold/white from the pyrotechnics, then return to purple and blue tones. | Genie strikes a final dynamic pose in the center lower tier before vanishing. |
| **09:34 - 09:36** | Smoke and fading gold glitter trails drift down; no new launches (sky goes dark). | Blue spotlights slowly sweep down; castle returns to ambient blue/purple idle illumination. | Deep blue and purple architectural lighting washes over the castle facade. | Genie disappears; projections clear. |

**4. Fireworks in the sky**
* **09:24 – 09:30 (Comet/Mine Barrage):**
  * **Type:** Fast vertical rising comets with short tails / mine-style launches.
  * **Colours:** Vivid alternating neon shades: magenta/pink, emerald green, ruby red, and bright gold.
  * **Size & Height:** Narrow vertical trails rising to medium-high altitude (reaching just above the top of the main spire).
  * **Position & Direction:** Flanking the castle symmetrically on both left and right sides, firing in straight vertical streams and slight outward fans. Approximately 6–10 comet launches per second in rapid, syncopated pulses matching the swing tempo.
* **09:33 (The Climax):**
  * **Type:** 2 aerial chrysanthemum/peony bursts with gold/white glittering pistils and red/orange center stars.
  * **Size & Height:** Large spherical shells, breaking high directly above the central spire, perfectly framed to the left and right of the upper spire tip.
  * **Count:** Exactly 2 high aerial shells breaking simultaneously on the hit.
* **09:34 – 09:36:** The sky immediately clears of launches; only lingering willow/glitter dust falls as the cue ends.

**5. Fireworks on the castle**
* **09:33 (Roof Terrace Gerbs / Fountains):**
  * On the final beat (*"HA!"*), two horizontal spark gerb fans fire simultaneously from the lower-mid rooflines flanking the central tower.
  * They project bright, sparkling silver-gold fans shooting horizontally outward to the left and right across the castle walls for roughly 1 to 1.5 seconds.

**6. Lasers and lighting**
* **Lasers:** None visible during this section.
* **Searchlights / Moving Lights:**
  * Arrays of high-power moving beam fixtures located behind and beside the castle.
  * Emitting sharp white, cyan, and sky-blue beams that fan outward into wide "V" formations, scissor across each other, and snap into vertical columns to frame the castle spire.
* **Base/Wash Lighting:**
  * Dynamic LED washes at the base shift between saturated purple, warm magenta, and golden yellow, pulsing to the rhythm of the music.

**7. The castle**
* **Base Architectural Lighting:** 
  * Main towers and spires maintain a regal royal blue and deep purple tone.
  * Lower walls are dynamically illuminated with rich amber/yellow footlights simulating theatrical footlights.
* **Projections:**
  * **09:24 – 09:32:** The central facade displays Arabian-night styled geometric decorative trim, with warm theatrical curtain/stage colors surrounding the central entryway arch.
  * **09:33:** Flash of bright white/gold projection light across the entire facade matching the gerb blast, immediately settling into a mystical deep indigo/blue night pattern by 09:35.

**8. Characters**
* **Genie:**
  * **Grid Position:** Center-bottom (`[Row 3, Col 2]`), positioned directly on the castle facade above the main entrance gate.
  * **Scale:** Approximately 1/4 to 1/3 the height of the castle structure.
  * **Appearance & Motion:** Bright glowing cyan/blue animated form. He appears dancing with fast, rubber-hose style comedic swings, twirling his hands, pointing, and striking jazzy poses to match his vocal lines between 09:24 and 09:32. On the final chord at 09:33, he strikes an arms-out finish pose and dissipates by 09:34.

**9. For our boards (64x32 and 64x64 LED matrix)**
To make this segment unmistakably recognizable on low-resolution matrix displays:
1. **Vertical Multi-Colored Comet Steppers (09:24–09:30):** Animate rapid vertical lines shooting upward on both flanks of the castle in alternating neon pink, green, and gold pixels.
2. **The "HA!" Climax (09:33):**
   * Trigger **two horizontal spark fans** spraying outward to the left and right from the castle's mid-level roof pixels.
   * Simultaneously trigger **two circular white/gold bursts** breaking right above the central spire tip.
3. **Genie on the Castle Facade:** A dancing bright cyan-blue sprite (around 8–12 pixels high) animating lively gestures at the bottom-center of the castle, vanishing immediately after the climax burst.

**10. What you couldn't see**
* Exact turret details and fine architectural projection textures on the outer wing walls due to distance and exposure contrast with the bright fireworks.
* The specific ground firing tubes or launch pads behind the castle perimeter, as they are hidden behind the structure and trees.

**11. Our version**
* **What's right:** You correctly identified **Genie** as the featured character, and identified roof fountains firing from the castle.
* **What's wrong:**
  * It is **not** a "huge gold willow barrage"; the run-up (09:24–09:30) is actually a rapid volley of **multi-colored vertical comets/mines** (magenta, green, gold), followed by only **two** round aerial chrysanthemum/glitter shells at 09:33.
  * The roof fountains do not just "shower" the castle downwards; they spray **horizontally outward** from the mid-level terraces like wings of fire.
* **What's missing:**
  * The vertical flanking comet tracers running up each side of the castle leading into the finish.
  * The upward-fanning blue/white searchlight beams framing the spire.

</details>

## 6. Love (audio 9:23-12:04, video 9:33-12:14)

### 6.1 Olaf: some people are worth melting for

- **Audio:** 563-576 s (9:23-9:36, 13 s) · **Video:** `--start 9:33 --end 9:46`
- **Our score now:** Spoken line; icy blue and purple castle, snowflakes floating up; the sky dark for about 7 s, then one gold willow left of the spire (video 9:43). Characters: Olaf.
- **V2:** stage ghost; actors olaf (Olaf pops up and waves in the snow).
- **Checked by eye (2026-10-14):** Gemini is right about the shell: about 7 s of dark sky, then one shell to the left of the spire. Leave Olaf as he is in our version.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 9:30-9:49 · notes: none</summary>

Here are the details for this segment based on the video:

**1. Where this part starts and ends**
* **Starts:** **09:36**  
  * *Reason:* The user’s estimate of 09:33 is **early**. At 09:33–09:35, the *Aladdin* ("Friend Like Me") finale is still firing heavy crackling gold shells and lateral turret gerbs. The Olaf segment begins at 09:36 as those bursts fade, the sky goes dark and quiet, the music drops to a gentle chime/orchestral melody, and the castle illumination turns icy blue.
* **Ends:** **09:47**  
  * *Reason:* The user’s estimate of 09:46 is slightly **early**. Olaf finishes speaking at 09:44, and the single firework burst hangs and trails off into golden sparks until 09:47, when the musical transition into the next romantic sequence takes over.

**2. Music**
* **09:30–09:33:** "Friend Like Me" finale: *"Never had a friend like me!"* ending on a sharp brass/percussion climax.
* **09:34–09:36:** Final crackles fade out into crowd cheers, immediately dropping into a soft, crystalline *Frozen* chime and string motif.
* **09:41–09:44:** Spoken dialogue by Olaf: *"Some people are worth melting for."*
* **09:44–09:47:** Soft orchestral string swell accompanying the burst of the single firework.

**3. Timeline**
| Time | Fireworks | Lasers and lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **09:30–09:33** | Massive red, green, and gold comet barrages; twin golden peony/crackling bursts | Bright white searchlights and uplighting | Purple, magenta, and gold facade | Genie motif projections |
| **09:34–09:36** | Aladdin shells fade out into the dark; sky goes completely clear | Searchlights power down | Warm lighting fades to dark | Projections clear |
| **09:36–09:40** | None (sky completely dark) | Ambient cool blue floodlights on lower trees/walls | Shifts to deep royal blue and violet; frost and snowflake textures appear | Olaf materializes in the central balcony/arch |
| **09:41–09:43** | None in the sky; single comet launches upward on the left behind castle (09:43) | Subdued cool blue wash | Deep blue/cyan frost patterns continue | Olaf visible speaking |
| **09:44–09:47** | Single shell bursts high left: bright white/silver glitter core opening to long gold willow tendrils | Static deep blue wash | Deep blue facade, softly glowing central window | Olaf visible in central balcony |
| **09:48–09:49** | Residual gold sparks drift down and vanish | Blue wash holds | Blue lighting holds | Olaf projection transitions |

**4. Fireworks in the sky**
* **Quiet period (09:36–09:43):** Exactly 7 seconds of quiet and dark sky, creating an intimate contrast after the loud *Aladdin* sequence.
* **Launch (09:43):** A single gold/white comet trail shoots up into the sky to the **left** of the main spire.
* **Burst (09:44–09:47):** 
  * **Type:** Silver glittering peony center blooming into a weeping willow / kamuro.
  * **Colour:** Brilliant white/silver flash at the core, expanding into warm golden weeping tendrils.
  * **Position:** High in the sky, level with/just below the height of the central spire, on the **left side**.
  * **Count:** Exactly **1 shell** during the entire Olaf dialogue.

**5. Fireworks on the castle**
* At **09:33**, two horizontal fan fountains (gerbs) spray outward to the left and right from the mid-level turrets for the *Aladdin* finale.
* During the Olaf segment (**09:36–09:49**), there are **zero** fireworks or gerbs launched from the castle structure.

**6. Lasers and lighting**
* No laser beams or sweeping searchlights are active during this moment.
* Lighting is kept minimal: a deep royal blue and indigo wash across the trees, perimeter towers, and base of the castle.

**7. The castle**
* **Base lighting:** Transitions at 09:36 from warm yellow/purple to cold royal blue and violet on the walls and roofs.
* **Projections:** Frost crystals and stylized ice patterns creep across the towers and facade. Faint glowing white snowflakes drift gently upward across the blue walls.
* **Central window/arch:** Glowing soft cyan/white light framing the character projection.

**8. Characters**
* **Olaf (*Frozen*):**
  * **Location:** Center of the castle facade, framed directly within the lower-center arched window/balcony (center-bottom of a 3x3 grid).
  * **Size:** Small, roughly 1/7th to 1/8th of the castle’s visible height.
  * **Movement:** Fades into view around 09:39–09:40, stands centered facing the crowd, and speaks his line (09:41–09:44) with subtle head/arm movement before holding as the shell blooms.

**9. For our boards**
1. **The Sudden Chill:** Instantly drop the warm, chaotic Aladdin barrage to zero fireworks and flip the castle palette to deep royal blue and cyan.
2. **The 7-Second Dark Sky:** The sky must remain completely unlit and still during the spoken line ("Some people are worth melting for").
3. **The Single Asymmetric Burst:** Trigger exactly one shell at 09:43–09:44 on the **left side** of the spire (not centered), starting as a bright white 3x3 or 5x5 pixel cluster that blooms into falling golden willow pixels.

**10. What you couldn't see**
* Spectators' heads and mobile phones partially block the lowest gate and plaza level at the very bottom of the frame.
* Olaf's fine facial expressions are somewhat soft due to the distance and video compression.

**11. Our version**
* **What's right:** The spoken line, the icy blue/purple castle palette, floating snowflakes, a single shell, and Olaf as the featured character.
* **What's wrong:**
  * The shell is not purely gold: it opens with a bright white/silver glitter core before trailing into gold willow fingers.
  * The shell is not centered above the castle; it is explicitly fired and bursts on the **left** side of the main spire.
* **What's missing:**
  * The deliberate 7-second pause of pitch-black sky between 09:36 and 09:43 before the shell fires.
  * Olaf’s specific placement inside the lower-central balcony archway rather than a full-castle projection.

</details>

### 6.2 Love Is an Open Door

- **Audio:** 576-607 s (9:36-10:07, 31 s) · **Video:** `--start 9:46 --end 10:17`
- **Our score now:** Olaf stays in the centre window to about 582 (video 9:52), then no characters; pink and violet only on the castle, the bursts in the sky gold (some green-gold); gold comet fans from the sides from about 585; no heart shells; gold comets (video 9:48), a gold chrysanthemum (10:00), gold fans (10:06-10:12). Characters: Olaf.
- **Checked by eye (2026-10-14):** the sky bursts are gold (some green-gold), with the pink and violet only on the castle, as Gemini says. No Anna or Hans anywhere (checked by eye and in frames 9:44-10:15): the figure in the centre window at 9:46-9:52, which Gemini took for them, is Olaf carrying on from 6.1; after that the castle has no characters. Gold comet fans fire from the sides from about 10:05.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 9:43-10:16 · notes: none</summary>

Here is the breakdown of the "Love Is an Open Door" sequence:

**1. Where this part starts and ends**
* **Starts:** **09:48**. The Aladdin segment ("A Whole New World") concludes around 09:45; Anna begins singing "Say goodbye..." at **09:48**, accompanied by the castle projection and lighting shifting from deep blue to magenta/violet. Your start timestamp of **09:46 is slightly early** (covers the fading Aladdin burst and brief musical pause).
* **Ends:** **10:15–10:16**. The segment culminates on the final lyrical hit "Love is an open door!" and a central golden aerial burst at 10:14–10:16 before the show transitions to the next scene. Your end timestamp of **10:13 is slightly early**.

**2. Music**
* **Song:** "Love Is an Open Door" (*Frozen*), performed by Kristen Bell (Anna) and Santino Fontana (Hans).
* **Lyrics & Key Beats:**
  * **09:48:** Anna: *"Say goodbye..."*
  * **09:49:** Hans: *"...say goodbye..."*
  * **09:50–09:52:** Both: *"...to the pain of the past..."*
  * **09:55–09:58:** Both: *"...we don't have to feel it anymore!"*
  * **09:59:** Both: *"Love is an open..."* (Dramatic musical crescendo / drum roll).
  * **10:04:** Both: *"...door!"* (Big brass chord strike).
  * **10:08:** Hans: *"Love is an open..."*
  * **10:10:** Anna: *"...door!"* (Hans harmonies).
  * **10:14–10:15:** Both: *"Love is an open door!"* (Full brass resolution hit).

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **09:48–09:52** | Gold streamer trails from prior burst drift left | Pink/magenta floodlights wash lower castle | Turrets shift to royal purple/magenta; Nordic stained glass on walls | Anna & Hans silhouettes singing in central arch |
| **09:53–09:57** | Dark/quiet sky | Purple wash deepens on turrets and surrounding trees | Ornate floral rosemaling patterns pulse in magenta and violet | Anna & Hans fade as clock and arch graphics brighten |
| **09:58–10:02** | Single shell rises behind spire (09:58); explodes into massive golden chrysanthemum (09:59–10:02) | Turret and roof floodlights brighten on explosion | Facade glows vibrant violet and white; clock face illuminated in spire | Rosemaling/stained glass motifs across facade |
| **10:03–10:07** | Dual angled fans of 4–5 golden comets shoot outward from left and right lower perimeter (10:04–10:06) | Searchlight beams subtly cross in sky; bright flash on castle walls | Castle base flashes brilliant white/pale pink, resolving to deep magenta | Central stained glass window patterns |
| **10:08–10:13** | Twin sweeping fan barrages of golden comet tails shoot upward from left and right sides (10:10–10:12) | Blue and violet accent lights sweep upward | Deep violet base with glowing blue/white central archway | Architectural tracery / Frozen castle motifs |
| **10:14–10:16** | Large gold/amber chrysanthemum bursts directly over the central spire | Bright flash across all castle facade lighting | Facade pulses in brilliant violet/gold highlights | Stained glass window accents |

**4. Fireworks in the sky**
* **09:48–09:50 (Left):** Fading, downward-drifting golden willow tendrils left over from the 09:45 Aladdin shell.
* **09:58–10:02 (High Centre):** Single large-caliber shell launched directly behind the main spire, detonating at **09:59** into a massive, perfectly spherical **golden chrysanthemum/peony** that expands to twice the width of the main spire.
* **10:04–10:06 (Low/Mid Left & Right):** Ground-level fan launch: ~4–5 thick golden comet tails on the left angled left, and ~4–5 on the right angled right, firing simultaneously on the vocal hit *"door!"*.
* **10:10–10:13 (Mid Left & Right):** Upward barrages of rapid golden comets/mines launching in staggered fans from both flanks, arcing outward.
* **10:14–10:16 (High Centre):** A large golden/amber chrysanthemum detonates directly above the upper spire, accompanied by another smaller burst on the mid-left.
* **Rhythm:** Sky is completely dark during the quiet verses (09:52–09:58); fires strictly in synchronized accent bursts on major lyric hits ("open door").

**5. Fireworks on the castle**
* There are **no fountains, gerbs, or strobe candles attached to the turrets or parapets** during this segment. 
* All launches come from ground-level mortar positions directly behind and immediately flanking the castle.

**6. Lasers and lighting**
* **Lasers:** No visible aerial or scanning lasers are used during this song.
* **Searchlights:** Subtle sky-scanning searchlight beams are faintly visible sweeping behind the upper castle into the sky (09:52–09:56, 10:06–10:08).
* **Floodlights:** Lower perimeter architectural wash fixtures tint the castle base and flanking trees in rich magenta, royal purple, and deep violet.

**7. The castle**
* **Base & Turret Lighting:** Transitions from deep Aladdin blues to rich magenta/violet wash at 09:48. Spires and rooftops remain bathed in deep royal purple.
* **Projections:**
  * **09:48–09:55:** Gothic/Nordic stained-glass cathedral windows cover the lower facade and central block, framed by intricate violet rosemaling patterns. The center arch acts as an illuminated balcony.
  * **10:04–10:07:** Castle flashes intensely into bright white/rose-pink on the downbeat of *"door!"*, then settles back into deep magenta and violet tracery.
  * **10:08–10:15:** The central clock face and tower spires glow with frosty blue and violet geometric patterns.

**8. Characters**
* **Anna & Hans:**
  * **Location:** Center arch / central balcony window (Grid: **Center**).
  * **Scale:** Small figures, roughly 1/6th to 1/8th of the castle height.
  * **Motion / Appearance:** They appear as stylized silhouette projections singing and gesturing toward one another in the central arched window frame from **09:48 to ~09:52**. As the tempo builds at 09:53, their silhouettes fade out, leaving the castle facade covered in stained-glass architectural graphics.
  * **10:00–10:16:** No distinct character figures; the castle relies entirely on stained-glass and clock graphics.

**9. For our boards**
1. **Palette shift at 09:48:** Instantly drop the blue wash and shift the castle matrix to a glowing magenta/violet lattice (stained glass pattern).
2. **Spire detonation at 09:59:** Keep the sky completely dark from 09:52–09:58, then fire a single, prominent high-center golden chrysanthemum right over the central spire on *"open... door!"*.
3. **Flanking comet fans at 10:04 & 10:10:** Fire mirrored golden angled comet lines (left angling left, right angling right) from the lower perimeter on the word *"door!"*.

**10. What you couldn't see**
* Character facial details inside the central projection arch are too small and low-contrast to distinguish facial animation clearly; they appear primarily as silhouettes.
* Outer ground mortar launch tubes are outside the bottom of the camera frame behind the hub crowd.

**11. Our version**
* **What's right:** The stained glass motif, the transition to royal blue/violet/magenta, the gold fan comets, and the gold aerial bursts are spot-on. Anna and Hans are indeed the characters.
* **What's wrong:**
  * **"Pink, violet and gold peonies":** In the sky, the aerial bursts are purely **monochrome gold/amber chrysanthemums/peonies**; there are no pink or violet sky shells in this segment (the pink and violet are strictly castle projections/lighting).
  * **"Ending royal blue and violet":** The segment actually ends primarily in **magenta, violet, and bright gold**, not royal blue (royal blue belongs to the preceding Aladdin scene).
* **What's missing:**
  * The **clock face motif** in the upper spire.
  * Anna and Hans are only visible during the opening lines (**09:48–09:52**); they are gone before the big fireworks arrive.

</details>

### 6.3 Can You Feel the Love Tonight

- **Audio:** 607-623 s (10:07-10:23, 16 s) · **Video:** `--start 10:17 --end 10:33`
- **Our score now:** Starry indigo, the castle deep blue; WALL-E and EVE among the constellations; at about 614 (video 10:24) the castle turns pink and lavender under blue roofs (the real show's small Simba and Nala picture on the centre tower is left out); gold willows building to a gold canopy (green-gold at 10:23, the canopy at 10:29), pink peonies at 10:31. Characters: WALL-E, EVE, Simba, Nala.
- **V2:** stage off; actors walle (WALL-E floats across the stars).
- **Checked by eye (2026-10-16):** no amber castle or acacia trees after all. The castle is deep blue to about 10:23, turns pink and lavender under blue roofs at about 10:24 (audio 614), and from about 10:26 a small sunset-coloured picture of Simba and Nala sits on the centre tower, left of the spire. The savanna effect is gone; the Simba and Nala picture was tried and left out (2026-10-16).
- **Checked by eye (2026-10-14):** WALL-E and EVE are both there (Gemini's answer says they aren't; it's wrong), and so is Simba and Nala's savanna: the castle turns amber with black acacia-tree silhouettes on the lower walls from about 10:25.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 10:10-10:36 · notes: none</summary>

Here is the detailed breakdown of the segment from **10:10 to 10:36**:

**1. Where this part starts and ends**
* **Start:** **10:13–10:14**. Marked musically by the opening piano and vocal intro of *"Can You Feel the Love Tonight"*, alongside the launch and detonation of the first overhead gold peony shell at 10:14 directly above the central spire.
* **End:** Your proposed end time of **10:33 is much too early**. At 10:33, the song is only midway through the first verse (*"When the heat of a rolling wind..."*), with Simba and Nala still actively projected and fireworks continuing through 10:36 and beyond (leading toward the chorus and eventual transition to *Tangled*). 
* **Evaluation of 10:13 to 10:33:** **10:13 is an accurate start**, but **10:33 is premature/too early** for the end of the song/sequence.

**2. Music**
* **Song:** *"Can You Feel the Love Tonight"* (from *The Lion King*), sung by a solo male vocalist with warm orchestral backing.
* **Lyrics and musical hits:**
  * **10:10–10:13:** Lingering choral vocalization (*"Ahhh..."*) and orchestral resolution from the preceding number.
  * **10:14–10:18:** *"There's a calm surrender..."* (10:14: first gold burst hits right on the opening beat).
  * **10:19–10:24:** *"...To the rush of day..."* (10:16–10:18: gold secondary bursts expand and hang).
  * **10:24–10:27:** Orchestral interlude / swell with harp/percussion roll.
  * **10:28–10:33:** *"When the heat of a rolling wind..."* (10:26–10:28: twin gold brocade bursts hit on the downbeat).
  * **10:34–10:36:** *"...Can be turned away..."*

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **10:10–10:13** | Castle-flank gold/white comet tails arc outward; high faint white glitter in sky. | Soft indigo/blue base floodlights; subtle purple searchlight beams angled up. | Deep royal blue/indigo lighting with white star constellations tracing castle architecture. | None clearly discernible (space/star field). |
| **10:14–10:15** | Single bright golden chrysanthemum/peony bursts centered high above spire. | Subtle side spotlights sweeping gently upward. | Midnight indigo with sparkling starlight. | None. |
| **10:16–10:18** | Two large cascading golden willow/brocade shells burst left and right of spire. | Soft white/cyan upward beams crisscrossing slowly behind castle. | Deep indigo/violet starry background. | None. |
| **10:19–10:23** | Golden willow embers drift downward; sky goes dark/quiet for ~3 seconds. | Upward spotlights continue gentle sweeps. | Indigo starts warming slightly; stars gently fade. | None. |
| **10:24–10:26** | Pair of symmetrical high gold/amber chrysanthemums burst on left and right flanks. | Gold and warm ambient wash replaces cool blue on the lower grounds. | Castle shifts from indigo to warm golden-yellow and sunrise orange tones. | Transition to African sunrise savanna palette. |
| **10:27–10:31** | Cascading gold brocades with lower twin pinkish-red strobing peony bursts flanking spire. | Warm amber and purple accent beams fanning from castle base. | Savanna scene with African tree silhouettes along lower turrets/walls. | **Simba & Nala** appear center-stage nuzzling. |
| **10:32–10:36** | Huge layered gold willow canopy hanging in upper sky with trailing embers. | Steady warm beams and ground floodlights illuminating castle facade. | Full warm savanna projection with orange/violet sky gradient and Pride Lands motifs. | **Simba & Nala** remain center-stage. |

**4. Fireworks in the sky**
* **10:10–10:13 (Opening sweep):** Low/mid-height fan of angled white/gold comets shooting outward from behind both sides of the castle.
* **10:14 (Spire high center):** 1 single medium-large gold chrysanthemum detonating directly above the central spire tip.
* **10:16–10:18 (Upper flanks):** 2 large golden brocade/willow shells burst in quick succession (left, then right of the spire) and slowly drift downward in long glittering trails.
* **10:19–10:24 (Sky quiet):** ~4 to 5 seconds of dark sky with only fading golden embers.
* **10:25–10:28 (Symmetrical double):** 2 large gold chrysanthemums burst simultaneously on the left and right sides of the upper spire, expanding into drooping golden tendrils.
* **10:30–10:32 (Secondary mid bursts):** 2 smaller pink/magenta-red peony bursts detonate just below the golden willow canopy (one left, one right of the central spire).
* **10:33–10:36 (High canopy):** 2 high-altitude gold willow bursts that fan out wide across the entire upper sky, filling the top frame with falling gold dust.
* **Rhythm:** Slow, deliberate, and emotional (1–2 bursts every 4–6 seconds), perfectly matching the romantic tempo of the ballad.

**5. Fireworks on the castle**
* **10:10–10:12:** Angled comet tails fired from immediately behind/adjacent to the castle outer walls/turrets, arcing out into the side sky.
* No low gerbs, fountains, or perimeter roof-edge pyrotechnics fire from the castle parapets during this quiet lyrical portion (10:14–10:36).

**6. Lasers and lighting**
* **Lasers:** No sharp, scanning graphic lasers are active in this sequence (reserved for high-energy segments).
* **Searchlights/Beams:**
  * **10:10–10:23:** Pale white/cyan-blue searchlights originating from behind the castle, aimed skyward in gentle stationary angles or slow crosses.
  * **10:24–10:36:** Searchlights shift to soft warm white and amber, accentuating the golden bursts.
* **Base/Perimeter Lighting:** Deep purple/indigo floodlighting across the outer trees and side towers shifts to warm amber/magenta at 10:25.

**7. The castle**
* **Base Castle Lighting:**
  * **10:10–10:23:** Royal blue and violet architectural floods with bright white pin-point highlights on the spires.
  * **10:24–10:36:** Smooth crossfade to warm golden-yellow, amber, and terracotta orange, with the lower perimeter towers washed in rich purple/pink.
* **Projections:**
  * **10:10–10:24:** Starfield pattern across the facade with delicate white constellation lines outlining castle architecture against a deep indigo/violet background.
  * **10:25–10:36:** The night sky dissolves into an African sunrise/sunset across the center facade. The base and lower walls project silhouettes of acacia trees and savanna textures in warm amber, orange, and purple.

**8. Characters**
* **Simba and Nala:**
  * **Identity:** 2D hand-drawn animated adult Simba and Nala from *The Lion King*.
  * **Location:** Lower-center of the castle (grid position **center-bottom / center** above the main gateway arch).
  * **Size:** Spanning roughly 25% of the castle's total height and about one-third of the central facade's width.
  * **Movement:** Fade in gently at **10:26–10:27**, tenderly nuzzling their foreheads and cheeks together in a slow, continuous romantic embrace. They remain stationary at the center facade through the end of the clip (10:36).
* **WALL-E & EVE:**
  * **Not visible in this clip.** (In the full show, WALL-E and EVE appear during the preceding space/flying sequence prior to 10:10).

**9. For our boards (LED matrix recreation)**
1. **The Palette Shift (10:24–10:26):** Transition the entire castle backdrop from cold **starry indigo/deep blue** to warm **golden-amber/savanna orange**. This is the key visual shift for the song's entrance.
2. **Gold Brocade Timing (10:14, 10:16, 10:26, 10:32):** Keep fireworks minimal and slow. Fire 1 central gold burst at 10:14 on *"There's"*, twin gold bursts at 10:16, leave the sky dark for 5 seconds (10:19–10:24), and then fire paired gold bursts at 10:26 with 2 small soft pink accents at 10:30.
3. **Simba and Nala Silhouette (10:27+):** Render a warm gold/amber silhouette of the two lions nuzzling in the center 16x16 pixel region of the lower-mid castle facade.

**10. What you couldn't see**
* Extremely fine architectural projection details on the far outer side turrets due to distance and slight contrast blowout from bright gold firework bursts.
* The show continues past 10:36, so the resolution/chorus of *"Can You Feel the Love Tonight"* is cut off by the end of the clip.

**11. Our version**
* **What's right:** 
  * Starting with "starry indigo" and spaced gold fireworks.
  * Having Simba and Nala appear.
* **What's wrong:**
  * **WALL-E and EVE:** They are **not present** between 10:10 and 10:36; the space flight section has already concluded.
  * **Song boundary:** Ending the sequence at 10:33 cuts the song off in the middle of the first verse.
* **What's missing:**
  * The distinct **savanna amber/orange color transition** across the castle starting at 10:25.
  * The **acacia tree silhouette patterns** on the lower flanking walls.
  * The small **soft pink/magenta peony bursts** at 10:30 nestled under the larger gold canopy.

</details>

### 6.4 You'll Be in My Heart

- **Audio:** 623-639 s (10:23-10:39, 16 s) · **Video:** `--start 10:33 --end 10:49`
- **Our score now:** Magenta, lavender and gold; families on the centre tower's right side: Kala and baby Tarzan, Riley and her family, Dory; pink, violet and white with comets from the terraces; a nearly dark sky, no heart shells. Characters: Kala, Tarzan, Riley, Dory.
- **V2:** stage ghost; actors dumbo (Dumbo flies across, flapping his ears).
- **Checked by eye (2026-10-14):** correct that it opens with Kala and baby Tarzan and that the sky is quiet. It's a montage of families on the right side of the tall centre tower, not just two vignettes in the gate: Simba and Nala, then Tarzan, then Riley and her family (Inside Out), Dory (the blue shape at about 10:41, which Gemini took for Dumbo), and others. No Dumbo or Mrs. Jumbo seen.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 10:30-10:50 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **10:34**. The prior segment (*The Lion King* / "Can You Feel the Love Tonight") concludes at 10:33 as the massive golden willow bursts fade away. At 10:34, the opening vocal ("You'll...") enters over a gentle piano chord, and the castle projection transitions.
* **End:** **10:47** (or **10:48**). The vocal concludes on the word "...always" at 10:47. At 10:48, the orchestral flute and strings swell into "A Whole New World" accompanied by sweeping pink/red angled comets.
* **Assessment of 10:33 to 10:47:** Your range is very close. 10:33 is about one second early (the previous song's finale shells are still fading), and 10:47 is spot on for the end of the vocal line.

**2. Music**
* **Song:** "You'll Be in My Heart" (from Disney's *Tarzan*, written by Phil Collins; arranged for *Happily Ever After*).
* **Lyrics & Timestamps:**
  * **10:34 – 10:37:** *"You'll be in my heart..."*
  * **10:38 – 10:42:** *"No matter what they say..."*
  * **10:43 – 10:46:** *"You'll be here in my heart..."*
  * **10:46 – 10:48:** *"...always."*
* **Big Hits / Musical Beats:**
  * **10:34:** Downbeat of the soft piano and vocal entry.
  * **10:37:** Gentle bass/percussion hit on the word *"heart"*.
  * **10:40:** Downbeat on *"what they say"*.
  * **10:43:** Emotional orchestral swell and percussion hit on *"heart"*, synced to a gold sky burst.
  * **10:45:** Secondary beat on *"in my heart"*, synced to another gold sky burst.
  * **10:48:** Big transition downbeat as "A Whole New World" begins.

**3. Timeline**

| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **10:30 – 10:33** | Massive overhead gold weeping willow/kamuro shells; pink peonies at mid-height. | Violet/blue searchlight beams fan upward; magenta base flood. | Deep purple base, blue turrets, gold trim; central oval portal. | Simba & Nala nuzzling (*Can You Feel the Love Tonight* finale). |
| **10:34 – 10:35** | Willows fade out. Sky goes dark and quiet. | Violet wash on base and surrounding hub trees; static sky beams. | Lion King projection fades; lush green jungle vines appear around central arch. | Transition into Kala cradling baby Tarzan. |
| **10:35 – 10:38** | No fireworks; sky completely dark. | Steady violet/magenta wash; upward-angled blue searchlights. | Warm golden light inside center archway; green foliage on columns. | Kala holding baby Tarzan close to her chest. |
| **10:39 – 10:40** | Sky dark. Camera zooms in slightly. | Blue searchlights slowly tilt; castle lighting remains violet/magenta. | Center portal morphs from green jungle vines to a warm, starry golden glow. | Kala & Tarzan fade out; Dumbo & Mrs. Jumbo fade in. |
| **10:41 – 10:42** | Sky dark and quiet. | Deep blue/violet searchlight beams splayed outward. | Central warm golden oval window on lavender/purple facade. | Mrs. Jumbo's trunk gently rocking baby Dumbo. |
| **10:43 – 10:44** | 1 medium gold/white glitter chrysanthemum bursts high, right of center spire. | Searchlights stationary; violet wash on castle walls. | Center circular portal glowing warmly. | Dumbo resting in Mrs. Jumbo's trunk (fades at 10:44). |
| **10:45 – 10:46** | 1 gold glitter peony bursts at mid-to-high level, right of spire. | Searchlights begin sweeping outward. | Portal dissolves into ambient twilight blue and starlight textures. | Dumbo fades out; ambient transition texture. |
| **10:47 – 10:50** | Angled pink/red comets launch upward to the right (10:47), then a 5-shot pink comet fan sweeps up-left (10:48–10:50). | Searchlights sweep dynamically across sky. | Base lit magenta/violet; facade transitions to Agrabah night sky. | Transition into Aladdin & Jasmine (*A Whole New World*). |

**4. Fireworks in the sky**
* **10:30 – 10:33 (Preceding Finale):** At least 3–4 massive golden weeping willow/kamuro shells filling left, center, and right overhead, with 2 smaller pink/magenta peonies breaking lower.
* **10:34 – 10:42 (The Quiet Verse):** Zero sky bursts. The sky is completely dark for 9 seconds.
* **10:43 – 10:46 (The Sky Breaks):**
  * **10:43:** 1 medium-to-large white/gold glitter chrysanthemum breaks high in the sky, just right of the central spire.
  * **10:44 – 10:45:** 1 medium gold glitter peony breaks slightly lower and to the right of the central spire.
  * **Total count for this song:** Exactly 2 high aerial bursts.
* **10:47 – 10:50 (Song Transition):**
  * **10:47:** A small angled burst/tail of pink/red comets shoots to the upper right.
  * **10:48 – 10:50:** A fan of 5 bright magenta/pink comets with white tail trails shoots upward and angled to the left from behind the castle perimeter.

**5. Fireworks on the castle**
* **10:34 – 10:46:** None. There are no gerbs, fountains, rooftop strobes, or parapet mines fired from the castle masonry during this emotional ballad.
* **10:47 – 10:50:** The angled comet fans launch from ground/terrace launch positions behind and alongside the castle perimeter, not directly off the castle building surfaces.

**6. Lasers and lighting**
* **Lasers:** No visible overhead aerial beam lasers or sharp laser-scanned graphic outlines during this segment.
* **Searchlights:** Deep violet and cyan/blue searchlights originate behind the castle, pointing into the sky in a stationary V-shaped fan from 10:34 to 10:44, before starting a slow outward sweep at 10:46–10:48.
* **Castle & Hub Wash:** Deep magenta and lavender floodlights illuminate the lower castle walls and trees in the hub. Turret spires are highlighted with amber/gold pin-spots.
* **Flames / Fountains:** None active.

**7. The castle**
* **Base Architecture Lighting:** Washed in rich magenta/violet, with the upper turret cones lit in deep blue/purple and finials highlighted in warm gold.
* **Projections:**
  * **10:30 – 10:33:** Golden oval portrait of Simba and Nala.
  * **10:34 – 10:38:** The archway transforms with climbing green jungle vines on the columns framing an amber-lit center arch.
  * **10:39 – 10:44:** The jungle vines fade into a soft pink/lavender and warm golden circular vignette.
  * **10:44 – 10:47:** The vignette dissolves into a twilight blue and purple starry wash across the facade.

**8. Characters**
1. **Simba and Nala** *(10:30 – 10:33)*
   * **Location:** Center facade (center cell of 3x3 grid).
   * **Size:** ~1/4 of castle height inside a golden oval frame.
   * **Movement:** Nuzzling heads together; fades out at 10:33–10:34.
2. **Kala and Baby Tarzan** *(10:34 – 10:39)*
   * **Location:** Center arch / lower-middle facade (bottom-center to center of 3x3 grid).
   * **Size:** ~1/3 of the castle height.
   * **Movement:** Static framed pose with gentle head-nuzzling motion; Kala holds baby Tarzan up against her chest. Fades in at 10:34, fades out at 10:39.
3. **Mrs. Jumbo and Baby Dumbo** *(10:40 – 10:44)*
   * **Location:** Center arch / lower-middle facade (bottom-center of 3x3 grid).
   * **Size:** ~1/4 to 1/3 of the castle height.
   * **Movement:** Dumbo (in his yellow hat) rests inside the cradle of Mrs. Jumbo’s gray trunk, rocking gently side-to-side. Fades in at 10:39–10:40 on *"No matter what they say"*, fades out at 10:44.

**9. For our boards**
1. **The 9-second total pyrotechnic blackout (10:34 – 10:42):** Contrast is key. Turn off all aerial fireworks pixels. The sky must be dark, leaving only the purple/blue castle and the warm amber character projection.
2. **Character transitions:** Display Kala holding baby Tarzan from 10:34 to 10:39, morphing cleanly to Dumbo in the trunk at 10:40.
3. **The two gold bursts (10:43 and 10:45):** Fire exactly two gold/white glitter bursts high to the right of the central spire on the word *"heart"*, followed at 10:48 by a fan of angled pink comet streaks to signal the start of *Aladdin*.

**10. What you couldn't see**
* **Camera adjustments:** The camera zooms slightly inward at 10:38, cutting off the outer peripheral launch zones.
* **Character details:** Fine facial details (e.g., eyes/expressions of Kala and baby Tarzan) are low in contrast due to distance and projector bloom.
* **Launch hardware:** Ground-level mortars behind the castle perimeter are obscured by castle walls and trees.
* **Lasers:** Unsure if low-intensity projection mapping lasers were active on the castle facade beneath the bright video wash, but no aerial beam lasers were visible.

**11. Our version**
* **What's right:** Castle base colors (magenta, lavender, and gold) are completely accurate. The two featured character vignettes (Tarzan & Kala, followed by Dumbo & Mrs. Jumbo) are correct. The pink/violet comet fan at the transition is accurate.
* **What's wrong:** 
  * "Comets from the terraces" should **not** fire throughout this segment. Firing comets during the song breaks the quiet emotional mood; they only fire at 10:47–10:50 during the musical transition into *Aladdin*.
  * The character description should specifically specify **baby** Tarzan held by Kala, not adult Tarzan.
* **What's missing:**
  * The 9 seconds of complete sky silence (10:34–10:42).
  * The **two high golden-white glitter chrysanthemum/peony bursts** at 10:43 and 10:45 on the lyric *"heart"*.
  * The ending transition into *A Whole New World* at 10:48.

</details>

### 6.5 Princess garden

- **Audio:** 639-668 s (10:39-11:08, 29 s) · **Video:** `--start 10:49 --end 11:18`
- **Our score now:** No princesses in the real show: the families' pink and red castle carries on, pink comets from the sides, gold palms and willows, a red peony; it turns royal blue at about 646 (video 11:06); no heart shells; pink comets from the sides and a red peony (10:51), a white chrysanthemum (10:57), gold (11:03-11:09). Characters: none.
- **V2:** stage ghost; actors princess_garden (four couples meet in turn, a heart floating up between each).
- **Checked by eye (2026-10-14):** no princesses at all: not Cinderella and Charming (Gemini) nor Tiana, Naveen, Ariel, Eric, Belle and Beast (our score). In frames: the castle stays pink and red with gold accents to about 11:05 (the same look as 6.4's family montage), pink comets from the sides at about 10:50, gold palms and willows, a red peony at about 11:04; then royal blue from about 11:06 with gold willows, into Tangled's purple and gold at 11:18.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 10:44-11:21 · notes: none</summary>

Here is the detailed breakdown of the segment:

**1. Where this part starts and ends**
* **Start:** **10:47**. The preceding *Tarzan* ("You'll Be in My Heart") segment resolves as the castle projection dissolves from forest vines into an ornate, rose-and-gold enchanted garden with stained-glass archways. 
* **End:** **11:18** to **11:19**. At 11:18, a white ceremonial drape drops across the lower castle terrace, the castle architecture shifts into deep royal blue and violet, and at 11:19 the soaring opening strings and iconic golden firework burst introduce the *Tangled* ("I See the Light") segment.
* **Accuracy of your range:** Your estimate of **10:47 to 11:18 is exact**.

**2. Music**
* **Song:** The love medley continues, transitioning from the climax of *"You'll Be in My Heart"* into an orchestral, romantic waltz arrangement blending motifs from Disney Princess love themes (notably *"Beauty and the Beast"* / *"So This Is Love"*), building to the transition into *"I See the Light"* at 11:19.
* **Key musical beats:**
  * **10:45–10:46:** Final vocal cadence of *"You'll Be in My Heart"* ("...ever more").
  * **10:47:** Sweeping orchestral downbeat marking the opening of the royal garden ballroom theme.
  * **10:50–10:53:** Rhythmic percussion hits accompanying ground-level fan fireworks.
  * **10:56–10:58:** Dramatic orchestral crescendo landing on a massive aerial shell burst.
  * **11:04–11:08:** Secondary orchestral swell punctuated by dual red/gold burst shells.
  * **11:18–11:20:** The waltz concludes on a sustained high string chord; at 11:19–11:20, a distinct orchestral harp and string hit opens *"I See the Light"*.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle Lighting & Projections | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **10:44–10:46** | High white/silver floral bursts fade out behind the main spire. | Wide violet searchlights sweeping upward from hub perimeter. | Castle illuminated in vibrant magenta, amber, and gold stained-glass patterns. | Previous scene silhouettes dissolving in central arch. |
| **10:47–10:49** | Low-angle red comets/tails shoot outward from behind the castle left and right flanks. | Blue/violet upward beams crisscross into the night sky. | Stained-glass arches, floral rose vines, and golden tracery coat the entire facade and turrets. | Projected royal crests and garden motifs; ballroom setting forms. |
| **10:50–10:53** | Low-level fan barrages: angled white/gold glitter comets and pink/red mine bursts firing outward from both sides. | Ground floodlights pulse magenta/pink; searchlights angle outward. | Rose and gold facade projection intensifies with glittering accents. | Faint animated silhouettes begin dancing in the lower archways. |
| **10:54–10:56** | Dual trailing golden comets soar high overhead, fanning left and right behind the upper spire. | Narrow violet beam arrays sweep inward toward the spire. | Golden architectural framing sharpens on the central tower. | Figures visible dancing in the central portal. |
| **10:57–11:00** | Massive high-altitude golden brocade/willow shell detonates directly above the spire, trailing long glittering tendrils. | Deep purple perimeter illumination; searchlights stationary at wide angles. | Castle glow deepens; central archway shows brightly illuminated palace ballroom interior. | Royal dancing couple clearly visible in the central balcony/arch. |
| **11:01–11:06** | Secondary massive golden brocade shell followed by twin vibrant red/ruby peony bursts framing the upper spire. | Purple and magenta side-wash across hub trees and castle flanks. | Warm gold and rose tones remain steady across all main towers. | Dancing couple continues waltzing in the main portal. |
| **11:07–11:09** | Huge descending gold willow/palm shell cascades down around the castle spires. | Lighting shifts from warm rose/gold to rich cobalt blue and royal violet. | Lower facade transitions to cool blue stone and violet stained glass. | Central dancing couple finishes phrase. |
| **11:10–11:17** *(Camera zooms)* | Cascading gold glitter trails drift down behind the right flank. | Deep purple and blue upward searchlight cones cross behind the central spire. | Turrets and spires illuminated in saturated cyan and cobalt; central balcony framed in bright warm light. | **Cinderella and Prince Charming** dancing together in the central archway/balcony. |
| **11:18–11:21** | Sky goes momentarily dark (11:18), then at 11:19–11:20 a massive brilliant golden burst erupts over the spire. | Purple ambient lighting; searchlights reposition outward. | White satin drape drops over lower balustrade (11:18); lantern projection begins at base (11:20). | Cinderella and Prince Charming fade out as Rapunzel's lanterns prepare to appear. |

**4. Fireworks in the sky**
* **Launch types & counts:**
  * **10:44–10:46:** 2–3 high-altitude white/silver chrysanthemums directly behind the main spire.
  * **10:47–10:49:** Low fan of 4–6 angled red comets shooting from left and right launch positions behind the castle.
  * **10:50–10:53:** Rhythmic lower-tier mine and comet fan (~8–10 shots per side) sweeping outward in synchronized pink/ruby and silver-glitter tails.
  * **10:54–10:56:** 2 upward-reaching gold crossette/comet tails climbing toward high center.
  * **10:57–11:00:** 1 very large high-altitude **golden brocade crown / willow shell** bursting high-center above the main spire with long golden drooping tendrils.
  * **11:01–11:06:** 1 large gold brocade shell layered with **2 ruby-red peony shells** bursting slightly lower, flanking the central spire.
  * **11:07–11:09:** 1 large cascading **gold willow/palm shell** spreading wide across the sky.
  * **11:10–11:17:** Lingering golden willow tentacles slowly raining down to the right side; sky remains mostly clear to focus on castle projection.
  * **11:18:** Sky is completely dark and quiet for ~1.5 seconds.
  * **11:19–11:21:** 1 massive, high-bursting **golden chrysanthemum/palm** directly centered above the tip of the spire to introduce *"I See the Light"*.
* **Rhythm:** Starts with synchronized low-level angled ground fans (10:50–10:53, ~3–4 bursts/sec), escalates into massive singular/paired aerial shells at 10:57 and 11:04, pauses in a brief 1.5-second sky blackout at 11:18, and detonates a single massive golden burst at 11:20.

**5. Fireworks on the castle**
* During this specific segment (10:47–11:18), **no rooftop gerbs, battlements fountain sparks, or castle turret pyro are fired**. All pyrotechnics originate from the launch sites behind and beside the castle perimeter to maintain high contrast for the projection mapping of the ballroom waltz.

**6. Lasers and lighting**
* **Searchlights:** Four primary upward-pointing beam searchlights positioned in the moat/hub perimeter. They start in deep magenta/violet (10:47–10:56), crossing behind the central spire, then switch to electric blue/purple beams (11:08–11:17).
* **Lasers:** Subtle ambient laser washes project across the castle surfaces; no sharp, scanning beam fan patterns penetrate the open sky during this soft ballad section.
* **Flames & Fountains:** None.

**7. The castle**
* **Base lighting & Turrets:** 
  * At **10:47**, the base and turrets are bathed in deep magenta, warm amber, and golden backlight.
  * At **11:08**, the turret caps and wall wash shift dramatically to cool **royal blue and violet**.
* **Projections:**
  * **10:47–11:07:** Ornate golden Gothic tracery, stained-glass floral windows, climbing rose vines, and palace ballroom archways covering the main facade and outer walls.
  * **11:10–11:17:** The central tower transforms into an illuminated palace archway/balcony overlooking a warm golden ballroom interior.
  * **11:18:** A wide white fabric/drape projection drops smoothly across the lower front balustrade wall, clearing the palette.

**8. Characters**
* **Character identity:** **Cinderella and Prince Charming**.
* **Location on castle:** Located precisely in the **center portal / middle balcony window** (center cell of the 3×3 grid, directly above the main gateway arch).
* **Size:** Approximately **1/5 to 1/6 the total height of the castle facade** (scale-proportioned to the central archway).
* **Movement:** They are waltzing in a continuous rotational circle, moving gracefully together in three-quarter time, framed inside the illuminated palace archway.
* **Appearance / Exit:** 
  * Fade in faintly inside the arch at **10:52–10:55**, becoming crisp and prominently visible as the camera zooms in at **11:10–11:16**.
  * They dissolve/fade out as the ballroom arches dim at **11:17–11:18**, followed by the curtain drop.
* *Note on other characters:* In this exact ~30-second window shown, Cinderella and Prince Charming are the primary featured dancing couple on the facade. (Other couples such as Tiana/Naveen, Ariel/Eric, and Belle/Beast appear in surrounding or extended segments of the montage, but are not distinct on the central tower in this specific 10:47–11:18 sequence).

**9. For our boards (LED matrix recreation)**
1. **The 10:57 Climax:** The castle facade glowing in warm rose and gold while a massive **gold brocade shell** blossoms directly overhead. On an LED matrix, a 3–4 frame expanding gold circle with drifting trail pixels paired with pink castle wall accents instantly captures the show's aesthetic.
2. **The 11:08 Lighting Shift:** The sudden shift of the castle base and turrets from warm rose/gold to deep sapphire blue and purple, while the center arch remains warm amber.
3. **The 11:18–11:20 Transition:** A complete 1-second sky blackout while the castle turns royal blue, instantly followed at 11:20 by a single bright golden aerial shell bursting right on the beat of *"I See the Light"*.

**10. What you couldn't see**
* **Left and Right Lower Flanks (11:10–11:17):** The camera operator zooms in tightly on the central spire and middle archway, cutting off the outermost left and right turret projections and ground perimeter.
* **Secondary Projected Silhouette Details (10:47–10:53):** Prior to the zoom, the figures inside the archway are small (~8–12 pixels in video resolution) and backlit, making micro-details of attire indistinct from a wide hub perspective until the camera zooms in at 11:10.

**11. Our version**
* **What's Right:**
  * **Visuals & Decor:** "Pink and rose stained-glass arches, flowers and waterfalls; gold brocade, pink peonies, gold palms" is spot-on for the architectural projection style and sky pyro between 10:47 and 11:09.
  * **Core Characters:** Having Cinderella and Prince Charming is completely correct.
* **What's Wrong / Misplaced:**
  * Listing **Tiana, Naveen, Ariel, Eric, Belle, and Beast** all within this narrow 10:47–11:18 timeframe is incorrect. They do not appear simultaneously on the castle in this specific 31-second clip; only Cinderella and Prince Charming are featured waltzing in the prominent center archway during this clip.
* **What's Missing:**
  * The dramatic **palette shift at 11:08** from warm pink/rose to rich royal blue/purple.
  * The **curtain drop effect at 11:18** across the lower castle terrace.
  * The **1.5-second sky pause at 11:18** leading directly into the single signature golden aerial shell at 11:19–11:20 marking the transition to *Tangled*.

</details>

### 6.6 I See the Light

- **Audio:** 668-697 s (11:08-11:37, 29 s) · **Video:** `--start 11:18 --end 11:47`
- **Our score now:** Lanterns rise; a big white burst at 11:29, then a wall of red and pink peonies at 11:38-11:42. Characters: Rapunzel, Flynn.
- **V2:** stage ghost; actors lantern_boat (Rapunzel and Flynn's boat drifts in among the lanterns).
- **Checked by eye (2026-10-14):** leave our version as it is (Gemini's lanterns-on-the-castle and small boat notes aren't worth changing it for).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 11:15-11:50 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **11:18**. The prior *Hunchback of Notre Dame* sequence finishes as the music transitions into the gentle acoustic/orchestral intro of *Tangled*, and the first amber floating lanterns begin drifting up the castle facade.
* **End:** **11:47** (extending into **11:50**). The phrase *"the world has somehow shifted"* sustains on a grand golden willow burst over the spire at 11:46–11:48 before leading into the sequence's swelling continuation.
* **Assessment:** Your estimate of **11:18 to 11:47** is **spot on** for this specific verse-and-chorus segment.

**2. Music**
* **Song:** *"I See the Light"* from Disney's *Tangled* (duet by Flynn Rider / Zachary Levi and Rapunzel / Mandy Moore).
* **Lyrics & Timestamps:**
  * **11:20 – 11:28:** Flynn: *"All at once everything looks different, now that I see you..."* / *"And at last I see the light, and it's like the fog has lifted..."*
  * **11:29 – 11:36:** Rapunzel: *"And at last I see the light, and it's like the sky is blue..."*
  * **11:37 – 11:47:** Duet: *"And it's warm and real and bright, and the world has somehow shifted..."*
* **Big Musical Hits:**
  * **11:20:** Flynn sings *"light"* on the downbeat; a massive bright white/gold shell detonates directly above the spire.
  * **11:29:** Rapunzel enters on *"light"*; a large golden chrysanthemum bursts overhead.
  * **11:38:** Swelling downbeat on *"warm"*; a dramatic color shift with two vivid ruby-red aerial bursts.
  * **11:46:** Climax of the vocal line on *"shifted"*; a large golden weeping willow shell blooms.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **11:15–11:17** | Sparse residual trailing sparks from previous scene. | Purple searchlight beams sweep upward. | Stained-glass Notre Dame facade fades out. | Quasimodo fading. |
| **11:18–11:19** | Low golden comet tails rise symmetrically on left and right flanks. | Upward violet/blue searchlights frame the castle. | Castle base turns deep midnight blue/indigo. | None visible yet. |
| **11:20–11:23** | **Large white-gold chrysanthemum** bursts dead-center above the highest spire. | Deep blue/violet searchlight beams stationary in V-shape. | Warm amber floating lanterns begin projecting across lower walls. | Flynn & Rapunzel silhouette in the rowboat appears in the central archway. |
| **11:24–11:28** | Sky darkens to trailing gold glitter; quiet lull. | Violet ground illumination on surrounding trees. | Lanterns multiply, floating upward across the center keep and side turrets. | Flynn & Rapunzel remain seated in the boat at the main gate. |
| **11:29–11:32** | **Large golden brocade/peony** burst centered over main spire. | Wide violet aerial beams flank the hub. | Hundreds of glowing orange/gold lanterns cover the entire facade. | Boat silhouette remains steady in lower center gate. |
| **11:33–11:36** | Sky clear/dark with light lingering embers. | Beams maintain indigo/purple wash. | Castle glowing with rising lanterns on a dark blue background. | Rapunzel & Flynn visible at base. |
| **11:37–11:41** | **Two ruby-red peony shells** explode high center and center-left, showering red and gold sparks. | Sky turns vibrant red/magenta from the intense burst reflection. | Lantern projections continue ascending smoothly. | Boat silhouette still anchored in the center arch. |
| **11:42–11:44** | Sky quiet; red embers dissipate. | Lighting returns to deep blue/indigo. | Castle continues glowing in warm amber lanterns. | Couple in boat visible at base. |
| **11:45–11:48** | **Large golden weeping willow / brocade crown** bursts directly over the central spire. | Golden glow reflected against castle spires. | Lantern field stays fully illuminated across all turrets. | Couple in boat visible at base. |
| **11:49–11:50** | Golden willow tendrils cascade down behind upper turrets. | Violet searchlight beams hold steady. | Lantern projections hold warm glow across facade. | Couple in boat visible at base. |

**4. Fireworks in the Sky**
* **Launch Locations & Trajectory:** All major shells launch from directly behind the castle perimeter, detonating either centered over the main spire or slightly offset to the upper-left.
* **Burst Breakdown:**
  1. **11:20:** Large white-gold chrysanthemum centered directly at the tip of the spire (high).
  2. **11:29:** Medium-large golden peony/brocade centered over the main spire (high).
  3. **11:38:** Mirrored pair / staggered double burst of vivid ruby-red peonies with gold crackling cores (one mid-high center-left, one high center).
  4. **11:46:** Large golden brocade willow centered over the spire, drooping long tendrils downwards.
* **Cadence & Rhythm:** Very slow and deliberate ballad timing. Bursts are single, isolated statements every 8 to 9 seconds, leaving the sky mostly dark between hits to focus attention on the castle projections.

**5. Fireworks on the Castle**
* **None.** There are no gerbs, fountains, perimeter strobes, or roof-mounted comet runs fired directly from the castle balustrades during this quiet romantic section.

**6. Lasers and Lighting**
* **Searchlights:** Four to six main searchlight beams on the hub perimeter project deep violet/indigo light upward into the night sky, forming a subtle angled V-frame around the castle.
* **Lasers:** None active during this segment (no sharp scanning beams or architectural edge-mapping lasers).
* **Perimeter Lighting:** Surrounding trees in the hub glow in a saturated magenta/violet wash.

**7. The Castle**
* **Base Lighting:** Castle wash lights are tuned to deep navy/midnight blue on the outer towers and roofs.
* **Projections:**
  * **Background:** Deep midnight blue and indigo starry night sky mapped to the castle stone.
  * **Pattern:** Glowing rectangular *Tangled* lanterns in yellow, warm amber, and soft orange float steadily upward across the entire castle structure—starting at the base and drifting up through the high spires.

**8. Characters**
* **Characters:** **Rapunzel and Flynn Rider** in their wooden rowboat from the lantern scene in *Tangled*.
* **Location:** Lower-center grid (bottom-center archway / main entrance gate).
* **Size:** Small—occupies only the entrance gate area, roughly **10% to 15%** of the castle's total height.
* **Movement:** Static placement; they are seated facing each other in silhouette, gently holding/releasing a glowing amber lantern between them.
* **Duration:** Fades in at **11:20** and remains continuously present through **11:50**.

**9. For Our Boards (LED Matrix Recreation)**
1. **The Floating Lanterns:** On a 64x32 or 64x64 matrix, set the castle silhouette to dark navy/midnight blue and generate 1-pixel and 2x2-pixel amber/orange dots gently scrolling vertically upwards at a steady slow rate.
2. **The Boat Silhouette:** Keep a tiny 4x6 or 6x8 pixel warm amber/black silhouette clustered inside the lower-center gate so the viewer clearly recognizes the rowboat scene.
3. **Four Timed Sky Bursts:**
   * `11:20`: Large white/gold expanding burst.
   * `11:29`: Medium gold burst.
   * `11:38`: Dual vibrant red bursts (a critical color shock in an otherwise gold/blue scene).
   * `11:46`: Cascading golden willow dripping downward.

**10. What Couldn't Be Seen**
* Peripheral ground-level launch positions behind the far tree lines are hidden by foliage.
* Fine facial details of Rapunzel and Flynn cannot be distinguished due to distance and exposure; they appear primarily as a backlit silhouette.

**11. Our Version**
* **What is right:** Midnight blue base, orange lanterns drifting up, Rapunzel and Flynn present, white/gold fireworks, and the transition to red and gold.
* **What is wrong:** 
  * Rapunzel and Flynn are not full-sized or moving across the castle; they are a small, static silhouette sitting in the rowboat strictly inside the **bottom-center gate**.
* **What is missing:**
  * The final climax shell at 11:46 is specifically a **golden weeping willow** that cascades downward framing the spires.
  * Deep violet/indigo searchlights framing the sky.
  * The exact timing structure: four distinct, isolated bursts synced to the vocal lines rather than continuous fireworks.

</details>

### 6.7 I See the Light (lanterns)

- **Audio:** 697-724 s (11:37-12:04, 27 s) · **Video:** `--start 11:47 --end 12:14`
- **Our score now:** A quiet sky full of lanterns, sparse gold willows; a white chrysanthemum as it ends (video 12:03). Characters: Rapunzel, Flynn.
- **V2:** stage ghost; actors lantern_boat (she lets her own lantern go).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 11:44-12:17 · notes: none</summary>

Here is the detailed breakdown of the segment:

**1. Where this part starts and ends**
* **Start:** **11:44** (Rapunzel singing *"…see the light"*). Your suggested start of **11:47 is late**, as it cuts into the middle of Rapunzel’s phrase and Flynn’s upcoming entrance at 11:50.
* **End:** **12:11 – 12:13**. At **12:11**, the quiet orchestral resolution of *"I See the Light"* ends as tribal percussion kicks in. By **12:13**, the lantern projections fade out completely into red/orange tribal patterns for *The Lion King*. Your **12:14 is accurate** (marking the visual arrival of the next scene).

**2. Music**
* **Song:** *"I See the Light"* (*Tangled*, Alan Menken & Glenn Slater).
* **Vocals & Cues:**
  * **11:44 – 11:47:** Rapunzel finishes singing: *"[Now I] see the light"*.
  * **11:50 – 11:58:** Flynn Rider sings: *"All at once everything is different / Now that I see you"*.
  * **11:59 – 12:05:** Flynn & Rapunzel harmonize together: *"Now that I see you"*, hitting a major orchestral swell, choral chord, and cymbal crash at **12:00**.
  * **12:06 – 12:11:** Lingering soft strings/harp chord progression fading out.
  * **12:11:** Sudden, sharp tribal drumbeat/percussion hit transitioning into *"He Lives in You"* (*The Lion King*).

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **11:44 – 11:45** | Residual smoke drifts; no active bursts. | Purple ground washes on flanking trees. | Deep royal blue walls; warm golden spire; amber lanterns floating up. | None visible. |
| **11:46 – 11:49** | Single large gold chrysanthemum/willow burst on right side behind spire. | Low purple ground lighting. | Same blue walls with drifting lanterns; spire glows amber. | None visible. |
| **11:50 – 11:58** | Sky quiet (camera zoomed in on spire). | Turret accent lights warm white/blue. | Zoomed view of upper towers washed in royal blue/lavender with lantern projections. | None visible. |
| **11:59** | Sky dark (camera zooms out). | Soft purple landscape illumination. | Warm golden arched vignette opens in center base. | Rapunzel & Flynn fade in inside the boat vignette. |
| **12:00 – 12:06** | Large gold willow/brocade burst directly over central spire, cascading down both flanks. | Steady blue/purple side floodlights. | Deep royal blue facade with hundreds of small amber lanterns rising around central vignette. | Rapunzel & Flynn visible holding/releasing glowing lantern. |
| **12:07 – 12:10** | Gold sparks fade out; sky goes dark. | Dim ambient park lighting. | Lanterns continue drifting up; boat scene softly glows. | Rapunzel & Flynn begin fading out. |
| **12:11 – 12:14** | Sky completely dark. | Shift toward warm red/amber low floodlights. | Blue fades out; walls wash in red, orange, and African tribal geometric motifs. | Rapunzel & Flynn gone. |

**4. Fireworks in the sky**
* **11:46 – 11:49:** 
  * **Type & Color:** Golden chrysanthemum bursting into a trailing willow.
  * **Position:** High, positioned to the right of the central spire.
  * **Count:** 1 burst.
* **12:00 – 12:06:**
  * **Type & Color:** Large golden brocade / willow burst.
  * **Position:** Directly centered over the main spire at high altitude, spreading wide across both the left and right sky and slowly drifting downward.
  * **Count:** 1 central shell burst.
* **Rhythm:** Very sparse and deliberate. Only two distinct shell moments; the sky remains quiet from 11:50–11:59 and again from 12:07–12:14 to emphasize the castle projections and vocal ballad.

**5. Fireworks on the castle**
* **None.** No rooftop gerbs, mines, or turret fountains are fired from Cinderella Castle during this segment.

**6. Lasers and lighting**
* **Lasers:** None active in the sky during this sequence.
* **Searchlights / Beams:** Weak purple/lavender accent beams aimed upward from the perimeter foliage into the low sky.
* **Floodlights:** Deep royal blue and violet floods washing the outer flanking towers and lower curtain walls, keeping the overall atmosphere dark and intimate.

**7. The castle**
* **Base Illumination:** Deep royal blue and purple lighting on the turrets and lower battlements; spire softly glowing in warm amber.
* **Projections:**
  * **11:44 – 11:58:** Hundreds of glowing yellow and orange floating lanterns drifting smoothly upward along the main center tower and spires against a starlit dark blue background.
  * **11:59 – 12:10:** A glowing golden arched window/vignette illuminates the center-lower facade (above the main gate). Thousands of tiny amber points of light drift upward around it.
  * **12:11 – 12:14:** Instant transition on the drum hit: blue and lanterns vanish; the castle turns crimson, fiery orange, and yellow with African textile and savannah patterns.

**8. Characters**
* **Rapunzel & Flynn Rider:**
  * **Identity:** Rapunzel (blonde hair, purple dress) and Flynn Rider (brown/teal attire) from *Tangled*.
  * **Location:** Lower-center facade (grid row 3, column 2 / above the central archway).
  * **Size:** Compact framed vignette, approximately 1/6 the total height of the castle.
  * **Action:** Seated together in the gondola, gently releasing a glowing golden lantern upward into the air.
  * **Duration:** Appears at **11:59** on the musical swell and fades out around **12:11**.

**9. For our boards**
1. **The Palette Contrast:** A deep royal-blue castle silhouette with distinct, single-pixel warm-amber "lanterns" slowly floating upward along the central tower.
2. **The Climax at 12:00:** The appearance of a warm yellow/gold central arched vignette at the castle base synced to a single, wide gold willow burst blooming above the spire and weeping downward.
3. **The Hard Cut at 12:11:** An instantaneous palette snap from calm midnight-blue to warm red/orange tribal patterns on the drumbeat.

**10. What you couldn't see**
* **11:50 – 11:58:** The camera zooms tightly into the upper spire, cutting off the lower castle gate, side turrets, and ground fixtures.
* Low perimeter launch fields outside the camera frame cannot be seen.

**11. Our version**
* **What is right:** The sky is indeed quiet with sparse gold willows, and Rapunzel and Flynn are the correct characters.
* **What is wrong:** The **sky** is not full of lanterns—the lanterns are strictly projected on the castle facade drifting upward. The sky is dark night, broken only by two golden firework bursts.
* **What is missing:** 
  * The characters appear together in the boat holding a glowing lantern inside an arched vignette at the center base starting specifically at **11:59** (not throughout the whole song).
  * The castle base color is a dark royal blue/purple, making the glowing amber lanterns pop.
  * The exact timing of the single climactic gold willow shell bursting at **12:00** right on the lyric *"Now that I see you"*.

</details>

## 7. Adversity (audio 12:04-14:09, video 12:14-14:20)

### 7.1 The Emperor's warning

- **Audio:** 724-742 s (12:04-12:22, 18 s) · **Video:** `--start 12:14 --end 12:32`
- **Our score now:** "The flower that blooms in adversity...": the Emperor's praise of Mulan, both in the gate; dark navy and crimson; two lone shells, a pink and green ring then a big gold willow; no gong; two lone shells: a white chrysanthemum (video 12:21) and a gold willow (12:26). Characters: Emperor of China, Mulan.
- **Checked by eye (2026-10-14):** Gemini is right: Mulan and the Emperor in the gate, two lone shells, no gong.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 12:11-12:35 · notes: none</summary>

Here is the detailed analysis of this segment of the show:

**1. Where this part starts and ends**
* **Starts at 12:19**: The Emperor’s spoken line begins (*"The flower that blooms in adversity..."*) as the projection focuses on the central balcony/arch. (Your 12:14 start is slightly early, capturing the preceding zoom-in/transition).
* **Ends at 12:27–12:28**: The Emperor finishes speaking (*"...of all"* at 12:26) and the massive gold willow firework fully cascades down. A silent pause/musical transition follows until the percussion hit at 12:33. (Your 12:32 is slightly late, extending into the dark pause before the next sequence).

**2. Music**
* **Score**: Soft, contemplative traditional Chinese instrumental theme (*Mulan* orchestral score).
* **Spoken Lines (Emperor of China)**:
  * 12:19 – 12:21: *"The flower..."*
  * 12:21 – 12:23: *"...that blooms in adversity..."*
  * 12:23 – 12:26: *"...is the most rare and beautiful of all."*
* **Hits**:
  * 12:22: Visual/audio sync as the flower-shaped firework opens on *"blooms in adversity"*.
  * 12:24: Grand explosion on *"rare and beautiful"*.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **12:14 – 12:18** | Smoke drifting in sky; no bursts | Castle floodlights active | Spires in deep blue; lower base bathed in deep crimson/red | Emperor of China standing tall in the center lower balcony projection |
| **12:19 – 12:20** | Quiet sky; faint launch trail left of spire | Static castle lighting | Red lower walls, blue spires | Emperor standing; Mulan in hanfu dress appears below him |
| **12:21 – 12:23** | Pink/magenta outer ring with green/white pistil center bursts high, just left of the central spire | Turret lights remain warm red and cool blue | Lantern patterns and red architectural wash on lower walls | Emperor and Mulan projected in center portal |
| **12:24 – 12:27** | Massive white/gold brocade willow shell detonates high directly above the central spire, trailing down into cascading gold tentacles | Ambient sky glow from the brocade burst reflects off castle | Lower walls red/orange glow, central tower blue | Mulan/Emperor fade into Chinese floral motifs |
| **12:28 – 12:32** | Golden willow embers slowly fade and drift downward; sky goes dark | Castle lighting remains static: red base, blue upper spires | Warm red archways, blue upper spires; projections hold steady | Scene holds in center portal |

**4. Fireworks in the sky**
* **12:21 – 12:23**: 
  * **Type**: Special blossom-pattern peony shell (pink/magenta outer ring representing flower petals with a white/pistachio-green center core).
  * **Location**: High, just left of the central spire.
  * **Count**: 1 large specialty shell.
* **12:24 – 12:27**: 
  * **Type**: Large brocade / kamuro willow shell. Detonates with an intense white flash, blooming into long-hanging, cascading golden willow streamers that droop down across the top half of the castle skyline.
  * **Location**: High, dead center directly above the main spire.
  * **Count**: 1 massive aerial shell.
* **Pacing**: Deliberate, solitary, majestic bursts synced directly to the spoken wisdom.

**5. Fireworks on the castle**
* None during this quiet, intimate story moment.

**6. Lasers and lighting**
* **Lasers**: None used in this section.
* **Searchlights / Fountains / Flames**: None active.
* **Wash Lights**: Steady deep red/crimson wash illuminating the hub perimeter and the castle base/walls; cool cyan/cobalt blue uplights on the upper spires and turrets.

**7. The castle**
* **Base Lighting**: 
  * Lower battlements and walls: Deep crimson red.
  * Upper towers and spires: Deep royal/cyan blue with soft amber turret peak lights.
* **Projections**:
  * Centered exclusively on the lower central facade/archway.
  * The castle facade is textured with Chinese architectural framing (dark wood beams, red imperial paper lanterns, and ornamental borders).
  * Deep red glow inside all the lower castle windows and gateway.

**8. Characters**
* **Emperor of China**:
  * **Location**: Center-bottom (balcony projection above the central archway).
  * **Size**: Approximately 1/6 to 1/8 the castle’s overall height.
  * **Appearance**: Tall traditional imperial yellow and red robes with his ornate black-and-gold beaded imperial cap (*mianguan*). Stands upright and dignified.
  * **Timing**: Visible from before 12:14 through ~12:21.
* **Mulan**:
  * **Location**: Center-bottom, projected directly in the central arch below/alongside the Emperor.
  * **Size**: Small, matching standard human scale on the balcony.
  * **Appearance**: Wearing her traditional Chinese gown (green, yellow, and blue matchmaker dress).
  * **Timing**: Fades in around 12:18–12:19, remains through the voiceover until ~12:26.

**9. For our boards (LED matrix recreation)**
1. **The "Blossom" Shell (12:22)**: A distinct magenta/pink ring with a bright green/white center dot launched high-left of the spire. On a 64x32/64x64 matrix, drawing this as a clear 2-color concentric ring/flower captures the exact metaphor of the Emperor's line.
2. **The Golden Brocade Cascade (12:24–12:27)**: A bright white flash dead-center above the main spire that expands and falls slowly into drooping gold pixel trails.
3. **Castle Palette**: 
   * Top 1/3 (spires): Cobalt blue pixels.
   * Bottom 2/3 (walls): Crimson red pixels with a small yellow/gold glow in the center portal for the Emperor.

**10. What you couldn't see**
* The camera is slightly zoomed in and off-center to the left, but the castle and the sky immediately overhead are fully visible.
* Fine facial details on the projected characters cannot be resolved due to scale and exposure, though silhouettes and clothing colors are identifiable.

**11. Our version**
* **What's right**: The quote (*"The flower that blooms in adversity..."*), the crimson/navy castle color scheme, and having the Emperor of China as the featured character.
* **What's wrong**: 
  * It is not a "warning"; it is the Emperor's tribute/praise of Mulan.
  * There is no gong hit here—the audio is soft strings and voiceover; the percussion hit occurs later at 12:33.
  * There are no "low crimson and gold comets"—the fireworks are two solitary, high aerial shells: a pink/green blossom ring followed by a massive golden willow.
* **What's missing**: Mulan herself projected alongside the Emperor in the archway, and the specific pink/magenta blossom shell at 12:22 that visually illustrates the line.

</details>

### 7.2 Villains attack

- **Audio:** 742-760 s (12:22-12:40, 18 s) · **Video:** `--start 12:32 --end 12:50`
- **Our score now:** Electric lime, toxic purple and blood red; crossing green searchlights, crackling green comets, red bursts; a red rocket, then red peonies (12:40, 12:45). Characters: Ursula, Scar, Hades.
- **Checked by eye (2026-10-14):** couldn't tell which villains are here; still open. In frames: 12:32-12:40 the lower castle glows red-orange like fire, the upper towers icy blue-white, with a round glowing red emblem over the gate (maybe still Mulan: the Huns' attack?); about 12:42 the castle flips to teal-green with a red streak up the spire; from about 12:44 orange towers, and the Incredibles' silver robot fills the centre by 12:46-12:48.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 12:29-12:53 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** The scene transition begins around **12:29–12:31** with fading willow embers and simmering red/orange light across the base of Cinderella Castle. A clear ignition marker occurs at **12:36**, when a single vertical red rocket shoots directly behind the spire, followed by the first heavy aerial red explosion at **12:40**.
* **End:** The villain attack segment does **not** end at 12:50; at **12:50–12:53**, the sequence is actively intensifying with massive red aerial chrysanthemums, castle parapet fountains, and villain projections continuing past the end of the clip.
* **Accuracy of 12:32 to 12:50:** Starting at 12:32 is slightly late for the initial transition build-up (which begins at ~12:29), but close to the red rocket cue (12:36). Ending at 12:50 is **significantly early**, as the villain sequence is midway through its crescendo at 12:53.

**2. Music**
* **Music / Themes:** The orchestral villain montage from *Happily Ever After*, featuring dramatic brass and percussion cues incorporating elements of Disney villain themes (including the Magic Mirror invocation, *Hellfire*, and *Friends on the Other Side*).
* **Big Hits & Beats:**
  * **12:36:** High, rising musical cue/whistle landing on the upward launch of the red tracer rocket behind the central spire.
  * **12:40–12:41:** Heavy orchestral/percussive hit landing precisely as the first high red peony explodes.
  * **12:44:** Second heavy brass beat synced to the second red chrysanthemum burst.
  * **12:46–12:48:** Sharp rhythmic accent landing on the yellow comet fan (12:46) and twin castle gerbs (12:48).
  * **12:51–12:52:** Major cymbal crash / crescendo matching the overhead golden palm and dense red aerial detonation.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **12:29–12:32** | Faint residual green/gold willow trails fade in upper sky | Perimeter dark; deep warm red/amber floodlights on lower castle walls | Molten orange/red embers projected on lower walls; upper spires in shadow | None visible |
| **12:33–12:35** | Sky completely dark; embers finish drifting down | Red base lighting deepens; side searchlights idle | Red fire patterns continue boiling on lower battlements | None visible |
| **12:36–12:39** | Single red comet rocket ascends straight up behind main spire | Narrow red glow follows rocket upward | Spire illuminated in sharp crimson; lower facade dims slightly | None visible |
| **12:40–12:43** | High red peony bursts center-left (12:40), second red peony breaks (12:41) | Castle base sharply switches to vivid electric cyan/blue flood; spire stays red | Cyan/blue stone projections on lower facade; glowing blue windows | Indistinct dark shadows creeping across lower facade |
| **12:44–12:45** | Large red chrysanthemum burst high directly above center spire | Cyan base wash and red upper spire maintained | Blue walls with glowing red battlements; circular frame forms on main tower | Circle frame resolves on tower |
| **12:46–12:47** | Fan of ~6 yellow/gold comets launches upward-left behind castle | Cool white/blue side searchlight beams illuminate left and right flanks | Central tower highlights a round glowing frame; archway glows fiery red | **Magic Mirror** face appears inside center tower circle (12:46) |
| **12:48–12:50** | Twin silver gerb fountains shoot outward from castle parapets in a "V" shape | Bright white vertical beam lights flank castle; purple/red perimeter wash | Main tower shows framed mirror face; lower gateway glows deep red | **Magic Mirror** visible; dark villain silhouette appears in lower gateway (12:49) |
| **12:51–12:53** | Golden palm burst overhead (12:51), followed immediately by giant red peony (12:52) | Sky and castle fully lit by aerial flares and intense white/cyan castle spotlights | Castle fully lit with dark textures, fiery central archway | **Magic Mirror** continues on center tower; silhouette in archway |

**4. Fireworks in the Sky**
* **12:29–12:31:** Pale green/gold willow remnants drifting down from the preceding scene (high altitude, both sides).
* **12:36:** 1 vertical red tail/comet launched directly behind the main castle spire, climbing to high altitude before detonating.
* **12:40–12:41:** 2 red peonies, medium-to-large, detonating high above the castle spire, slightly center-left.
* **12:44:** 1 large red chrysanthemum breaking high directly above the central spire, showering bright red embers downward.
* **12:46:** 1 fan barrage of ~6 yellow/golden comets launching from behind the left mid-castle wall, spreading upward and outward to the left.
* **12:51:** 1 bright golden palm/brocade shell breaking high center.
* **12:52–12:53:** 1 large, saturated red peony bursting directly over the golden palm, expanding across the upper center sky.
* **Rhythm:** After a brief pause from 12:32 to 12:35, bursts fire at a steady, rhythmic cadence of approximately one major shell every 2–3 seconds on major musical hits, accelerating into overlapping shells at 12:51–12:53.

**5. Fireworks on the Castle**
* **12:36:** Red tracer comet launches straight up from immediately behind the highest central spire.
* **12:46:** A 6-shot angled fan of golden comets fires from behind the left castle battlements.
* **12:48–12:49:** Two bright silver/white gerb fountains or comets fire symmetrically outward from the lower left and right battlements flanking the main gate, creating a wide "V" shape.

**6. Lasers and Lighting**
* **Lasers:** No visible laser beams are active in this clip segment.
* **Searchlights / Spotlights:** Cool white and cyan searchlights flank the castle base (left and right), projecting upright vertical columns into the sky starting around 12:46–12:52.
* **Architectural Floodlights:** Lower hub trees and castle perimeter transition from deep crimson (12:29–12:35) to saturated electric blue/cyan (12:40–12:45), then deep purple and dark navy (12:46–12:52).
* **Flames:** No physical flame projectors; fire is rendered purely through lighting and projection mapping.

**7. The Castle**
* **Lighting Changes:**
  * **12:29–12:35:** Lower half illuminated in fiery molten red and orange; upper half dark.
  * **12:36–12:39:** Crimson wash shoots up the main spire following the rocket.
  * **12:40–12:45:** Dramatic split: lower half turns vibrant icy/electric cyan-blue; upper spire stays deep crimson.
  * **12:46–12:53:** Main walls shift to navy/purple tones; central tower face is highlighted in white; the lower central gateway glows with fiery red backlighting.
* **Projections:**
  * **12:29–12:35:** Fluid, roiling red/orange lava/fire textures creeping along the lower castle base.
  * **12:40–12:45:** Dark, shadowy vines/tendrils creeping across blue stone textures.
  * **12:46–12:53:** A distinct circular/oval mirror frame appears on the upper-center tower directly beneath the clock, displaying a stylized white-and-dark theatrical face. The bottom entrance portal projects a blazing red chamber.

**8. Characters**
* **Magic Mirror (from *Snow White and the Seven Dwarfs*):**
  * **Location:** Center-top / upper-middle tower (directly beneath the spire clock).
  * **Size:** Spans the width of the central tower (about 1/4 of total castle height).
  * **Movement:** Fades in inside a glowing circular portal at **12:46**, speaks/shifts within the frame, and remains active through **12:53**.
* **Villain Silhouette (Gateway Portal):**
  * **Location:** Bottom-center, inside the central entry archway.
  * **Size:** Small (approximately 1/10 the castle height).
  * **Movement:** Appears at **12:49**, standing and gesturing against the glowing red portal interior through **12:53**. (Specific identity is shadowy; unsure if Dr. Facilier or Jafar).

**9. For our boards**
1. **The 12:40 Color Split:** Sudden contrast shift where the castle base snaps from fiery red to vivid electric cyan/blue while the top spire remains crimson, crowned by a high red peony burst.
2. **The Magic Mirror & Parapet Gerbs (12:46–12:48):** A circular white face centered on the main tower, immediately accompanied by twin silver fountain flares firing outward in a "V" shape from the castle battlements.
3. **The Gold-to-Red Finale Burst (12:51–12:53):** A bright golden palm shell instantly engulfed by a massive crimson peony in the upper sky.

**10. What you couldn't see**
* **Lower Courtyard / Hub:** The ground level and moat railings are blocked by audience heads in the foreground.
* **Far Turret Details:** Projections on the outermost left and right lower turrets are obscured by trees and darkness.
* **Gateway Silhouette Identity:** The character silhouette inside the archway at 12:49–12:52 is back-lit and low resolution; it cannot be definitively identified from the video alone (unsure).

**11. Our version**
* **What's Right:** "Blood red" and "red bursts" are completely correct—deep red washes and saturated red aerial peonies dominate the sequence from 12:36 to 12:53.
* **What's Wrong:**
  * There is **no electric lime** or **crackling green comets** in this window (comets are red at 12:36 and yellow/gold at 12:46; the secondary castle color is electric cyan/blue, not lime).
  * No **crossing green searchlights** are present (searchlights are cool white/cyan beams).
  * Ursula, Scar, and Hades are **not** present in this 12:29–12:53 timeframe.
* **What's Missing:**
  * **The Magic Mirror**, which is the primary, central character projection from 12:46 to 12:53.
  * The **electric cyan/blue lower castle wash** that creates the dramatic contrast at 12:40.
  * The **castle-mounted pyro**: the 12:36 red spire rocket and the 12:48 silver "V" gerbs on the parapets.
  * The **gold fan/palm effects** at 12:46 and 12:51.

</details>

### 7.3 To Die For

- **Audio:** 760-777 s (12:40-12:57, 17 s) · **Video:** `--start 12:50 --end 13:07`
- **Our score now:** The Incredibles fight a giant robot from about 12:44 (video); lightning; the castle blue and purple; big red peonies (12:55), then white chrysanthemums (13:00-13:04). Characters: The Incredibles, Omnidroid.
- **Checked by eye (2026-10-14):** it's The Incredibles fighting a robot monster (the Omnidroid) at about video 12:48, not the Lion King stampede (Gemini) or Maleficent and Jafar (our score).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 12:47-13:10 · notes: none</summary>

Here is the breakdown of the "To Die For" (wildebeest stampede) segment of *Happily Ever After*:

**1. Where this part starts and ends**
* **Start:** **12:51**. The segment transitions from the end of the *Lion King* ("Be Prepared") motif where Scar is perched above the gates to the rapid, pulsing brass and percussion of Hans Zimmer's score cue *"To Die For"* (the wildebeest stampede). The castle projections switch from Scar standing over the gorge to shadows of running wildebeests surging across the facade, accompanied by ground-level fireworks.
* **End:** **13:07–13:08**. The frantic stampede music culminates in a heavy, dramatic hit/cymbal crash at 13:07. The sky falls dark, the wildebeests vanish, and at **13:08–13:09**, the music shifts into ominous, dramatic brass/choir as the castle transitions to fiery orange and red with a sinister demonic/cat-slitted eye appearing in the rose window above the archway (leading into the next villain sequence).
* **Evaluation of 12:50 to 13:07:** Your timing is very accurate. 12:50 is just a second early (capturing the final beat of Scar's stance), and 13:07 exactly marks the final musical hit before the next transition.

**2. Music**
* **Music Cue:** *"To Die For"* (instrumental score composed by Hans Zimmer for *The Lion King* stampede sequence).
* **Lyrics/Dialogue:** Entirely instrumental/orchestral; no sung lyrics or spoken dialogue occur during this section.
* **Key Musical Hits:**
  * **12:51:** Driving orchestral strings and brass kick in rapidly on the downbeat.
  * **12:53–12:55:** Rising melodic fanfare with recurring orchestral hits syncing to bursts overhead.
  * **12:58:** Sudden crescendo and key modulation, marked by bright crackling willow shells bursting.
  * **13:03–13:05:** Climax of the stampede cue with cascading descending brass and pounding timpani.
  * **13:07:** Final massive resolving orchestral hit/percussion strike, immediately followed by silence in the sky and a low, threatening chord.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **12:47–12:50** | Red peony burst high above spire; lower right comets/bursts. | Purple/blue floodlights wash lower turrets; ground wash on hub trees. | Projections show the Elephant Graveyard skull on upper spire wall; dusty gorge walls below. | Scar perched on the rock promontory above the center gate; Elephant Skull. |
| **12:51–12:52** | Ground perimeter mine shells fire upwards in bright white/gold streaks from behind castle. | Deep blue/violet searchlight beams tilt upward from behind castle. | Canyon walls turn dark slate blue/indigo; wildebeest herd starts running. | Wildebeests begin stampeding across the base from stage-right to stage-left. Scar fades away. |
| **12:53–12:55** | Large crimson/red peony shells burst directly over the central spire; trailing red comets. | Bright violet and cyan base floods; searchlights sweeping slightly outward. | Projections shift to dark blue/purple rocky gorge textures with high-contrast shadows. | Silhouettes of dozens of stampeding wildebeests running horizontally across the lower facade. |
| **12:56–12:57** | Red burst fades into dark sky; lower smoke drifts. | Blue searchlight beams crisscross behind the upper spire. | Canyon wall projections remain blue/slate with dust and shadows moving left. | Stampeding herd continues across the bottom level. |
| **12:58–13:02** | Rapid succession of bright gold-to-white crackling chrysanthemum/willow bursts high over spire. | Searchlights fan outward; violet wash lights intensify on flanking towers. | Facade base remains illuminated in deep blue/purple with shadows of running beasts. | Stampeding wildebeest silhouettes continue rushing across the castle walls. |
| **13:03–13:06** | Massive golden-white brocade/willow aerial canopy fills the entire upper sky, slowly drifting down. | Blue searchlights angled steeply upward into the smoke/fireworks. | Lower facade displays chaotic movement of charging wildebeest horns and dust. | Final wave of the stampede rushes across the lower castle walls and dissipates. |
| **13:07–13:08** | Sky goes dark; golden willow sparks burn out. | Searchlights turn off or drop down; purple perimeter lighting dims. | Dark canyon projection fades out; castle lights dim momentarily. | Wildebeests completely vanish. |
| **13:09–13:10** | Sky remains dark (no aerial fireworks). | Vivid red and golden-yellow wash lights strike the lower walls and forecourt. | Castle rapidly transforms into glowing fiery amber/red stone; Gothic arches appear. | A giant glowing sinister eye (slitted pupil) appears inside the circular arch/rose window above the clock. |

**4. Fireworks in the sky**
* **12:47–12:50:** 2 large red peony shells bursting directly above the main spire, with secondary red comet tails launching from the right rear perimeter.
* **12:52–12:55:** 2 dense red/crimson peony aerial shells blooming centrally above the spire, cascading downward into soft red sparks. 
* **12:58–13:01:** A wave of 3–4 medium-to-large golden/white glittering chrysanthemum bursts fired in rapid succession directly behind the central spire.
* **13:02–13:06:** Grand aerial finale for this cue: 3 large brocade/kamuro willow shells bursting nearly simultaneously at high altitude, spreading a massive golden curtain across the sky over both left, center, and right.
* **13:07–13:10:** Complete blackout in the sky; dark and quiet, creating tension for the next villain sequence.
* **Rhythm:** Starts with single rhythmic red accents (~1 shell every 2 seconds), ramps up at 12:58 to a multi-shell burst wave (~2 shells/sec), peaks with the large brocade barrage at 13:03, then abruptly stops dead at 13:07.

**5. Fireworks on the castle**
* **12:51–12:52:** A low-level launch of white/gold comet mines fired from ground positions immediately behind the rear castle walls/parapets, shooting straight up like vertical tracers to announce the stampede.
* No gerbs, static fountains, or rooftop Roman candles are mounted directly on the castle turrets during these seconds.

**6. Lasers and lighting**
* **Lasers:** No visible thin-beam aerial lasers are active during this segment.
* **Searchlights:** High-powered blue and violet moving-head searchlights situated behind the castle point upward into the sky in a stationary "V" or narrow fan framing the central spire from 12:51 to 13:06.
* **Flames/Fountains:** No real flame projectors or water fountains are used in this segment.
* **Wash Lights:** Turrets and flanking towers are bathed in deep, eerie blue and violet LED floods to match the nighttime gorge ambiance, which snap to harsh red/yellow at 13:09.

**7. The castle**
* **Base Architectural Lighting:** 
  * 12:51–13:07: Main spire, roofs, and side turrets are lit in cool indigo, dark royal blue, and violet.
  * 13:08–13:10: Base lighting instantly switches to fierce amber-gold and blood-red.
* **Projections:**
  * **12:47–12:50:** The upper tower shows the eerie, gaping-mouthed Elephant Graveyard skull; lower walls show the rocky ledges of the gorge.
  * **12:51–13:07:** The entire lower and middle facade projects the sheer rock walls of the gorge in cold blue/slate gray. Projected dust clouds and stampeding silhouettes sweep continuously across the bottom tier.
  * **13:08–13:10:** Dramatic transformation into flaming orange/red stone architecture with Gothic tracery and a glowing, slitted eye.

**8. Characters**
1. **Scar (*The Lion King*)**
   * **Location:** Bottom-center (directly over the main gate and lower balcony).
   * **Size:** Approximately 1/6 the total height of the castle facade.
   * **Action:** Seen standing menacingly on the rock outcropping looking down with glowing green/yellow eyes.
   * **Timing:** Present at 12:47; fades away into dust between 12:50 and 12:51.
2. **The Wildebeest Herd (*The Lion King*)**
   * **Location:** Spans the entire bottom-third of the castle (bottom-left, bottom-center, bottom-right).
   * **Size:** Each individual wildebeest is small (approx. 1/20 of castle height), moving as a dense herd.
   * **Action:** Silhouetted shadows stampeding at high speed horizontally across the castle walls from right to left, accompanied by rising dust effects.
   * **Timing:** Enters at 12:51; exits/dissipates at 13:07.
3. **Fiery Sinister Eye (Claude Frollo / *Hunchback of Notre Dame* / Villains motif)**
   * **Location:** Center-center (inside the circular clock/rose window above the main gate arch).
   * **Size:** Fills the circular window space (approx. 1/8 the castle height).
   * **Action:** Snaps into view staring forward with a vertical slit pupil surrounded by burning yellow/orange iris.
   * **Timing:** Appears at 13:09.

**9. For our boards (LED Matrix recreation)**
To capture this section authentically on 64x32 or 64x64 matrices:
1. **The Stampede Movement:** The signature visual of this 16-second cue is the dark silhouettes of animals sprinting across the bottom 8–12 pixel rows of your castle from right to left against a dark blue background.
2. **Color Contrast & Pacing:** 
   * 12:51–12:57: Dark blue/indigo castle with isolated bright crimson/red bursts directly overhead.
   * 12:58–13:06: Intense cascade of bright white/gold willow particles drifting down across the matrix.
   * 13:07–13:09: Complete darkness in the sky; sudden change of the castle base from cool blue to burning red/orange, with a single bright yellow/red eye staring out from the center.

**10. What couldn't see**
* The exact ground launch points behind the castle are hidden behind the castle walls and hub structures.
* Street-level projections on Main Street U.S.A. buildings are out of frame (the camera is fixed on Cinderella Castle).

**11. Our version**
* **What's right:** You correctly identified that a major villain sequence build occurs here, leading into intense dramatic effects.
* **What's wrong:** 
  * There is **no green dragon fire** anywhere between 12:50 and 13:07. The colors in this cue are exclusively **deep blue/slate** on the castle, with **red** and **gold/white willow** fireworks overhead. Dragon fire (Maleficent) occurs in a different segment of the show.
  * **Jafar and Maleficent are not present** in this 12:50–13:07 cue.
* **What's missing:** 
  * The cue is specifically the **Wildebeest Stampede (*The Lion King*)**, featuring **Scar** at the transition (12:50) and a **moving herd of wildebeests** running across the base (12:51–13:07).
  * The sudden blackout at 13:07 followed by the appearance of the fiery sinister eye at 13:09.

</details>

### 7.4 He's a Pirate

- **Audio:** 777-806 s (12:57-13:26, 29 s) · **Video:** `--start 13:07 --end 13:36`
- **Our score now:** Scar and Simba fight (777, video 13:07), then Aladdin and Jafar as the snake (799, video 13:30); the castle cracks and burns; flame jets on the terraces; red, orange and gold; red comet fans off the rooftops (13:14), red peonies (13:19, 13:29). Characters: Scar, Simba, Aladdin, Jafar.
- **Checked by eye (2026-10-14):** at about video 13:07 the Scar and Simba fight starts (the Lion King, not the pirates' Aztec coin Gemini describes). At 13:30 it's Aladdin fighting Jafar as the snake, then Maleficent after that.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 13:04-13:39 · notes: none</summary>

Here is the detailed breakdown of the *Pirates of the Caribbean* ("He's a Pirate") segment from the video.

**1. Where this part starts and ends**
* **Start:** **13:08 - 13:09**. 
  * *Audio:* The previous orchestral sweep concludes and the driving, rhythmic cello/brass motif of Klaus Badelt’s "He's a Pirate" starts abruptly.
  * *Visual:* Castle lighting flashes bright yellow-gold, revealing the Aztec medallion / cursed gold coin projection over the center entrance at 13:09.
* **End:** **13:32 - 13:33**.
  * *Audio:* Ursula’s loud, echoing cackle (*"Ha ha ha ha!"*) cuts directly into the music.
  * *Visual:* The castle lighting snaps from pirate orange/fire tones to deep villainous sea-green and neon violet at 13:32–13:33, transitioning into *The Little Mermaid* / Villains sequence.
* **Assessment of your range (13:07 to 13:36):**
  * **13:07 is slightly early:** At 13:07, gold willow bursts from the previous sequence are still drifting down against blue castle illumination.
  * **13:36 is late:** By 13:33, Ursula has laughed, the pirate theme has ended, and green tentacle projections and green comet fans ("Poor Unfortunate Souls") have completely taken over.

**2. Music**
* **Song:** *"He's a Pirate"* (composed by Klaus Badelt / Hans Zimmer).
* **Vocals/Spoken lines:** Instrumental score throughout this section until Ursula's maniacal laugh (*"Ha ha ha ha!"*) strikes at **13:32–13:34**.
* **Major Musical Hits & Beats:**
  * **13:08:** Theme kickoff (driving 12/8 rhythm starts).
  * **13:10:** First massive orchestral downbeat — accompanied by continuous roaring real flame jets bursting on both sides of the castle base.
  * **13:11:** Twin fanned volley of red/orange comets launching into the sky on the rhythmic beat.
  * **13:16 – 13:18:** Syncopated brass crescendo — accompanied by arching red/gold comets and large red chrysanthemum bursts high overhead.
  * **13:28 – 13:30:** Second musical climax — high red peony burst explodes right of the spire at 13:28, followed by a double red shell burst at 13:30.
  * **13:32 – 13:33:** Musical transition hit — music breaks sharply for Ursula’s laughter.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **13:08** | Dying gold willow embers from previous scene | Blue searchlights sweep upward behind castle | Switches from blue/cyan to bright amber/gold wash | Aztec gold medallion motif appears on main gate |
| **13:10** | Low launcher pre-ignition flashes | **6 real flame jets** erupt along base & lower terraces | Base glows burning deep red/orange; spire turns amber | Medallion skull emblem sharpens in center gate |
| **13:11 – 13:15** | Fan of ~10 vertical red/gold comets with crackling tails launch outward | Flame jets pulse; warm amber/red architectural wash | Red brickwork texture with burning edges projected across central facade | Cursed Aztec coin / skull eye glows at center |
| **13:16 – 13:19** | Fan of arching red comets left/right, followed by 2 large red peony/chrysanthemum shells high | Searchlights track outward; amber ground wash | Castle engulfed in fiery projections and rolling ocean storm waves | Silhouette of pirate ship (Black Pearl) & ghostly skeletal pirates fighting |
| **13:20 – 13:26** | White/gold rising comet tails angling outward; sky mostly clear of large bursts | Sharp blue & white searchlight beams criss-cross behind castle spire | Castle switches to eerie moonlit stone, deep ocean blues, and warm lantern glows | Ghostly pirates battling along castle ramparts; pirate silhouettes moving |
| **13:27 – 13:31** | 1 medium red peony right (13:28), then 2 large ruby red peonies high left & center (13:30) | Purple/red backlight sweeps upward behind spires | Stone walls look aged/cracked, with warm torchlight in archways | Ship rigging / Jack Sparrow compass & pirate iconography at castle center |
| **13:32 – 13:33** | Single small red star trailing right | Lighting abruptly cuts to electric green & deep magenta | Projections shift from pirate fire to bubbling green ocean depths | Pirate projections fade; Ursula silhouette hints emerge |
| **13:34 – 13:38** | Massive synchronized fan of neon lime-green comets and green starbursts overhead | Intense neon green ground wash and sweeping green spotlights | Fully green and deep violet stone; giant projected black tentacles wrapping towers | Ursula's tentacles writhe up lower towers and ramparts |

**4. Fireworks in the Sky**
* **13:11 – 13:15:**
  * *Type/Color:* Fanned straight comets, bright red heads with trailing gold crackle/sparks.
  * *Size/Height:* Mid-to-high, shooting ~1.5x the height of the castle base.
  * *Side/Arrangement:* Symmetrical fanned volley (approx. 5 on the left, 5 on the right).
* **13:16 – 13:19:**
  * *Type/Color:* Two fanned arching comets firing inward/outward, breaking into 2 large spherical peony/chrysanthemum aerial shells in deep ruby red.
  * *Height:* High overhead above the spire.
* **13:20 – 13:26:**
  * *Rhythm:* Sky goes quiet for 6 seconds to let the music and projections take prominence; only 2–3 low rising white/gold comets angle outward.
* **13:28 – 13:31:**
  * *Type/Color:* High-altitude red peony shells. One shell at 13:28 (mid-high, right of spire), followed at 13:30 by a synchronized twin shell burst (large, directly above and left of spire).
* **13:34+ (Villains intro):**
  * *Type/Color:* Fanned bright lime-green comets launching wide left and right, topped by medium green peony bursts high above the spire.

**5. Fireworks on the Castle**
* No small fountains/gerbs are fired from the castle turrets during this specific sequence.
* All pyrotechnics in this segment are either launched from **ground perimeters behind/beside the castle** or generated by **physical flame projectors** installed along the lower hub terraces in front of the castle.

**6. Lasers and Lighting**
* **Flames:** At **13:10**, 6 massive liquid-fuel flame projectors positioned on the castle forecourt/terraces fire towering plumes of real orange fire (approx. 20–30 ft high), pulsing in sync with the heavy brass beats until ~13:14.
* **Searchlights / Moving Lights:**
  * *13:08 – 13:19:* Warm amber and fiery red wash lights bath the lower structure; narrow-beam searchlights behind the castle cast deep blue and amber beams scanning upward.
  * *13:20 – 13:26:* Searchlights behind the castle shift to stark blue and white, criss-crossing rapidly to mimic a nautical storm/lightning effect.
  * *13:32 – 13:38:* Instant snap to vibrant lime-green searchlights sweeping across the sky on Ursula’s laugh.
* **Lasers:** Sharp, green/cyan needle laser lines appear intermittently slicing horizontally across the moat trees and castle base around 13:35–13:38.

**7. The Castle**
* **Lighting Changes:**
  * **13:08:** Snaps from cool Tangled blues to glowing golden yellow.
  * **13:10 – 13:19:** Drops into saturated deep crimson and volcanic red on the lower ramparts, transitioning into burning yellow-orange up the central spire.
  * **13:20 – 13:27:** Darkens significantly into cool midnight navy, shadowed stone grey, and warm lantern glows in the windows.
  * **13:32 – 13:33:** Sharp switch to eerie toxic green on the upper spires and royal purple on the lower half.
* **Projections:**
  * **13:08 – 13:12:** The large circular Aztec medallion / cursed gold coin from *The Curse of the Black Pearl* fills the center gate archway, with cracked, smoldering stonework and fiery ember textures spreading across the facade.
  * **13:13 – 13:22:** Stormy ocean swells, splashing water, rolling flames, and wooden ship hull textures projected along the curtain walls.
  * **13:23 – 13:31:** The castle appears as a dark pirate fortress under moonlight; silhouettes of swords and rigging across the main tower.
  * **13:33 – 13:38:** Giant dark purple/black tentacles writhe up the turrets against a green bubbling water wash.

**8. Characters**
* **Aztec Medallion Skull / Cursed Coin:**
  * *Grid position:* Center (lower-middle gate, bottom-center 3x3).
  * *Size:* Approx. 1/4 castle height.
  * *Timing & Movement:* Appears at **13:09**, glows steadily with glowing eyes until ~13:14.
* **Ghostly Skeletal Pirates & Jack Sparrow Silhouette:**
  * *Grid position:* Lower-left, center, and lower-right battlements.
  * *Size:* Approx. 1/6 castle height.
  * *Timing & Movement:* Between **13:18 and 13:26**, dark silhouettes and skeletal figures brandishing swords clash and fight across the castle ramparts, moving horizontally across the parapets before dissolving into sea spray.
* **The Black Pearl:**
  * *Grid position:* Center-left to center.
  * *Size:* Approx. 1/3 castle width.
  * *Timing:* Silhouetted masts and tattered black sails cross the lower mid-section during the storm sequence (13:19–13:24).

**9. For Your LED Boards (Key Authenticity Moments)**
To capture this segment convincingly on low-res 64x32/64x64 matrices:
1. **The Instant Color Shift & Flame Flash (13:09–13:10):**
   * Snap the castle instantly from blue/gold to blazing deep red and orange.
   * Render vertical orange/yellow flame bursts popping on the terrace base (2–3 columns of bright orange/yellow flicker for 2–3 seconds).
2. **Fanned Red Comets to Red Peony (13:11 – 13:17):**
   * Fire a symmetrical V-fan of trailing red comets outward, culminating in a large red burst directly overhead.
3. **The Hard Green Snap (13:32):**
   * Cut the red/fire palette instantly to solid lime-green on the spire and purple at the base on Ursula’s laugh (13:32), immediately launching green angled comet lines.

**10. What Couldn't Be Seen / Uncertainties**
* Due to bright pyrotechnic smoke between 13:12 and 13:22, individual facial details of the projected pirates on the mid-balcony are somewhat obscured; only their sharp combat silhouettes and skeletal glows are clearly distinguishable.
* The exact count of real flame units along the hub perimeter appears to be 6, but outermost flanking flame jets may be partially out of frame to the far left/right.

**11. Review of Your Current Version**
*Your text: "The castle cracks and burns; flame jets on the terraces; red, orange and gold. Characters: Pirates."*

* **What's Right:**
  * "The castle cracks and burns" accurately matches the projected ember/cracking stonework texture.
  * "Flame jets on the terraces" is completely correct — the physical flame cannons at 13:10 are a defining feature.
  * "Red, orange and gold" is the exact colorway for this sequence.
  * "Characters: Pirates" is the correct theme/content.
* **What's Wrong:**
  * Your timing bounds (13:07–13:36) extend too late: by 13:33, the show has already transitioned to Ursula / The Villains with green/purple lighting and tentacle projections.
* **What's Missing:**
  * The iconic **Aztec gold medallion** projected right over the main entrance archway (13:09–13:13).
  * The **symmetrical fanned comets** and **high ruby-red peony shells** that burst overhead to the signature brass hits.
  * The transition to a **stormy sea battle** (ocean blues and pirate ship silhouette) midway through (13:20–13:25) before the finale shells.

</details>

### 7.5 He's a Pirate (green barrage)

- **Audio:** 806-812 s (13:26-13:32, 6 s) · **Video:** `--start 13:36 --end 13:43`
- **Our score now:** Maleficent after the snake: her green dragon fire along the ground; emerald shells and lime comets; green comet fans firing off both sides. Characters: Maleficent.
- **Checked by eye (2026-10-14):** this follows Aladdin and the snake (about 13:30); Maleficent comes after it (see 7.4's check).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 13:33-13:46 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **13:37**. Marked by a sudden, massive launch of green comets in a wide fan flanking the castle, synced to an accelerating brass crescendo in "He's a Pirate." 
  * *Note on 13:36:* Starting at 13:36 is slightly early; at 13:36, only a single stray red shell bursts on the left before the coordinated green barrage erupts at 13:37.
* **End:** **13:43**. Marked by the final crackling spread of the green canopy across the upper sky. At 13:44, the green trails fade out, and at 13:45, the show shifts into a fiery crimson/red barrage with red perimeter mines and red wash on the castle.
  * *Note on 13:43:* 13:43 is exactly on time for the end of the green barrage.

**2. Music**
* **Song:** "He's a Pirate" (from *Pirates of the Caribbean: The Curse of the Black Pearl*, composed by Klaus Badelt and Hans Zimmer).
* **Lyrics/Spoken lines:** Purely instrumental symphonic pirate theme during this segment; no lyrics or voiceover.
* **Musical hits and beats:**
  * **13:37:** Fast, syncopated brass and percussion crescendo accompanies the simultaneous upward firing of green comet fans.
  * **13:38 – 13:40:** Driving 12/8 pirate meter with heavy drum accents matching successive volleys of bursting green aerial shells.
  * **13:41 – 13:42:** Climactic brass fanfare flourish synced with the widest fan of angled green comet tails and gold crossette/mine bursts.
  * **13:43:** Final cadence beat of this phrase before transitioning into the darker, percussive battle rhythm at 13:44–13:45.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **13:33 – 13:35** | Quiet sky; faint trailing sparks overhead. | Green and lime floodlighting washing up the lower walls and central facade. | Ethereal lime green and dark purple pirate wash with ship rigging patterns. | Indistinct ghostly pirate ship textures. |
| **13:36** | Single low/mid red peony bursts on the far left. | Green floodlights continue illuminating facade. | Castle facade lit in bright electric green and yellow-green on upper spires. | None visible. |
| **13:37** | Symmetrical fan of intense green comets launches upward from both sides of the castle. | Green wash intensifies; high-intensity green spotlights accent the turrets. | Lime-green illumination on central spire and towers; purple/blue on lower outer walls. | Ghostly pirate vessel details projected on center gate. |
| **13:38 – 13:39** | Multiple large green peony/chrysanthemum shells break high above the spire; green comets fan outward. | Bright green upward beam wash matching the fireworks. | High-contrast green and dark blue pirate ship projections across the main facade. | Undefined ghostly crew/rigging silhouettes. |
| **13:40 – 13:41** | Massive continuous barrage of green aerial shells breaking overhead; two angled golden mine/comet plumes erupt at the flanks (13:41). | Vivid emerald green washes on castle; ambient flash from bursts lights the hub. | Bright yellow-green main tower; deep green and shadowy blue on lower levels. | Silhouette of pirate ship helm and sails across center facade. |
| **13:42 – 13:43** | Apex of the barrage: dense green willows/crossettes fill the sky from left to right; upward green comets reach peak spread. | Saturated emerald and lime lighting across all turrets and walls. | Glowing neon green spire with pirate fortress/ship projections below. | Silhouette textures begin fading into darker tones. |
| **13:44 – 13:45** | Green stars drift and extinguish; at 13:45, massive red comet mines and high red shells erupt. | Castle wash shifts rapidly from green to deep amber and fiery crimson red. | Castle turns solid blood-red/crimson for the ensuing battle section. | Projections shift into fiery pirate combat imagery. |

**4. Fireworks in the sky**
* **Types:** Green comets, green chrysanthemums/peonies, trailing green willows, and at 13:41, two angled gold/orange mine comet bursts.
* **Colors:** Predominantly emerald green and bright lime green, with brief gold/amber accents.
* **Height and position:**
  * **Low to Mid-level:** Ground-launched green comets shooting upwards in wide mirrored fans left and right of the castle (reaching spire height, ~150–200 ft).
  * **High-level:** Large aerial shells exploding 100–200 ft above the top spire, spreading across the entire upper sky (left, center, and right).
* **Launches and Pattern:**
  * Symmetrical, mirrored fan launches flanking the castle.
  * Approximately 10–12 green comets launch simultaneously per volley from ground firing sites.
  * Aerial breaks explode in rapid clusters (roughly 3 to 5 large breaks per second between 13:38 and 13:42).
  * Rapid, continuous barrage with no quiet gaps between 13:37 and 13:43, creating a solid canopy of green overhead.

**5. Fireworks on the castle**
* There are **no fountains, gerbs, or roof-mounted pyrotechnics** fired directly from Cinderella Castle's battlements or turrets during this segment. 
* All pyrotechnics originate from the ground launch areas flanking the castle and the distant perimeter launch site behind it.

**6. Lasers and lighting**
* **Lasers:** No visible laser beams overhead during this specific barrage.
* **Castle Floodlights:** High-powered LED wash fixtures bathe the castle in vibrant emerald green and lime green, with dark purple/cyan accents on the outer lower towers.
* **Searchlights:** Upward-firing architectural searchlights track up the main central spire in bright lime-yellow/green, reinforcing the vertical lines of the castle.
* **Flames/Fountains:** No ground flame projectors or water fountains active in this segment.

**7. The castle**
* **Base Lighting:**
  * 13:33–13:43: Castle walls are washed in saturated lime green, neon emerald green, and deep sea-purple.
  * 13:44–13:45: Instantaneous transition to dark amber, switching to deep crimson/blood red at 13:45.
* **Projections:**
  * Dynamic projection mapping depicts the eerie, supernatural world of *Pirates of the Caribbean*: ghostly water currents, wooden ship timbers, skeletal rigging, and ocean spray across the central facade and towers.
  * The main clock tower displays pirate motifs and ethereal green ghostly light.

**8. Characters**
* **Identifiable Characters:** No clearly defined, standalone animated Disney characters (e.g., full-figure Jack Sparrow, Davy Jones, or Hector Barbossa) are distinctly resolved or projected as isolated focal points on the castle facade in this shot.
* **Environmental/Ensemble Figures:** Ghostly pirate silhouettes and nautical ship textures appear integrated into the stonework projections across the lower-center grid (base and middle gate, rows 2–3, column 2), but they function as environmental atmospheric textures rather than distinct character animations.

**9. For our boards (64x32 and 64x64 LED matrix)**
1. **The Green Fan Eruption (13:37):** Simultaneously fire two angled fans of bright green single-pixel comets from the lower-left and lower-right of the castle upward toward the top edges of the matrix.
2. **The Emerald Overhead Canopy (13:38 – 13:42):** Fill the upper third of the matrix with expanding green star bursts (chrysanthemums/willows) cascading downward while continuous green streaks rise from the sides.
3. **Palette & Castle Transition (13:43 – 13:45):** Keep the castle silhouette illuminated in vivid lime/emerald green (with dark purple flanking towers) throughout the barrage, then sharply switch the castle pixels to deep fiery red at 13:44–13:45 as the green fireworks fade out.

**10. What you couldn't see**
* **Projection Fine Detail:** Due to distance, bright pyrotechnic exposure, and ambient illumination, fine line details of the projections on the central castle gate are partially washed out; specific skeletal crew faces cannot be confirmed with absolute certainty (noted as "unsure").
* **Launch Points:** Ground-level firing racks are located behind backstage foliage/structures and cannot be seen directly.

**11. Our version**
* **What's right:** "Emerald shells and lime comets" is completely correct and accurately captures the color palette and pyrotechnic types used throughout this sequence. "Characters: none" is also practically accurate, as no distinct animated characters take the spotlight.
* **What's wrong:** Nothing is factually incorrect.
* **What's missing:**
  * The symmetrical **mirrored fan formation** of the comets launching outward from both flanks.
  * The dual **gold/amber comet/mine burst** at 13:41 that accents the green shells.
  * The strong **emerald/lime green and purple floodlighting** on the castle itself.
  * The immediate, dramatic transition to **deep red** at 13:44–13:45 which marks the boundary of this cue.

</details>

### 7.6 He's a Pirate (red and gold)

- **Audio:** 812-837 s (13:32-13:57, 25 s) · **Video:** `--start 13:43 --end 14:08`
- **Our score now:** Dense red chrysanthemums and gold willow fans; red fans and a white chrysanthemum (13:46), white and red (13:53). Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 13:40-14:11 · notes: none</summary>

Here is the detailed breakdown of the "He's a Pirate (red and gold)" sequence from the video:

**1. Where this part starts and ends**
* **Start:** Exactly at **13:44**. The transition is marked by a sudden musical shift from the eerie villain theme into the driving triple-meter rhythm of *He's a Pirate*, accompanied by the castle projections and lighting instantly shifting from glowing green/purple to deep fiery red and gold, followed immediately by simultaneous red aerial bursts and mine launches.
* **End:** Exactly at **14:08 – 14:09**, ending on a massive percussive musical hit where a giant V-fan of comets erupts directly from the castle ramparts, transitioning into the triumphant trumpet fanfare of the next segment at 14:10.
* **Assessment of your range (13:43 to 14:08):** Extremely accurate. 13:43 catches the final decaying green burst; 13:44 is the true explosive downbeat of the red/gold pirate theme, and 14:08–14:09 is the closing punctuation.

**2. Music**
* **Music track:** *"He's a Pirate"* (from *Pirates of the Caribbean: The Curse of the Black Pearl*, composed by Klaus Badelt and Hans Zimmer), arranged for full symphonic orchestra.
* **Lyrics:** None (entirely instrumental/orchestral).
* **Key Musical Hits & Beats:**
  * **13:44:** Dramatic downbeat of the main theme; massive orchestral strike.
  * **13:48 – 13:50:** Secondary rhythmic cadence hit; barrage of gold brocade/willow breaks.
  * **13:54 – 13:56:** Climax of the first melodic phrase, accompanied by layered high-altitude gold/white chrysanthemums.
  * **13:59 – 14:00:** Syncopated turnaround beat where aerial activity briefly pauses before the next phrase.
  * **14:04 – 14:05:** Powerful cannon-like orchestral strike synced to a ground flash/concussion behind the castle and a central red peony overhead.
  * **14:08 – 14:09:** Final explosive crescendo chord marking the climax of the pirate sequence.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle Projections & Wash | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **13:44** | Instant launch of vertical red mines from low flanks; high-altitude red/white crackle peonies break overhead. | Golden-green searchlights point outward; warm wash floods the base. | Base lighting flips instantly from villain-green to blood-orange and red. | None visible. |
| **13:45 – 13:47** | Symmetrical salvos of thick red comets/mines angled outward; large gold/white brocade shells burst high center. | Green and gold searchlight beams sweep outward at 45° angles. | Castle façade bathed in fiery orange, red, and yellow stone textures. | Swirling pirate compass/coin projection begins to form at center. |
| **13:48 – 13:53** | Rolling waves of red/gold chrysanthemums burst high above the spire; red tail comets continue firing from flanks. | Green and amber searchlights criss-cross behind the turrets. | Turret roofs lit in deep crimson; golden light illuminates the central arch. | **Captain Jack Sparrow** silhouette/figure visible projected in the center lower-third gate area. |
| **13:54 – 13:58** | Dense canopy of sparkling gold willow/chrysanthemums raining down overhead; red comet tails flare on both sides. | Amber and yellow ground/turret floodlights intensify. | Detailed glowing pirate iconography (Aztec gold / compass motif) across the central tower. | Jack Sparrow continues in central archway. |
| **13:59 – 14:00** | Sky clears briefly (pause in overhead bursting). | Beams angle sharply outward like ship masts. | Castle remains lit in warm golden yellow on center tower and deep red on outer walls. | Jack Sparrow projection fades. |
| **14:01 – 14:03** | Angled white/silver comet fans shoot outward on left and right flanks; bright red peony bursts high above the spire. | Searchlights sweep back inward. | Façade shifts to rich amber and fiery orange. | None. |
| **14:04 – 14:07** | Bright white ground flash/burst behind castle (14:04); red peony bursts center-high with cascading white glitter mines on flanks. | Strobe lighting accents the perimeter walls. | Strong golden wash up the center spire; crimson side turrets. | None. |
| **14:08 – 14:10** | Massive outward-angled fan of thick golden comet tails / gerb mines launched directly from the castle battlements. | Blinding golden white wash across the entire castle structure. | Full-castle golden-white illumination flare. | None. |

**4. Fireworks in the Sky**
* **Types:** Red comet mines, gold willow/brocade shells, crackling chrysanthemums, red peonies, and silver/white comets.
* **Launch Locations & Pattern:**
  * **Flanks (Left & Right):** Upward-shooting red and silver mines/comets launched in paired outward fans.
  * **High Center (Above Spire):** Large-caliber aerial shells breaking in high-altitude brocades, gold willows with red tips, and crisp red peonies.
* **Counts & Rates:**
  * **13:44 – 13:57:** Very dense barrage—roughly 4 to 6 discrete breaks/launches per second, layering red ground tracers with high-altitude gold waterfalls.
  * **13:58 – 14:00:** Lull/quiet pocket where high bursts clear out.
  * **14:01 – 14:07:** Measured, rhythmic firing (approx. 2 breaks per second), alternating white side comets with high red peony shells.
  * **14:08:** Single coordinated fan blast across the full castle width.

**5. Fireworks on the Castle**
* **13:44 – 14:07:** Launch trails of low mines originate from launch pads immediately behind the castle flanks and parapets.
* **14:08 – 14:09:** A coordinated, multi-point **mine/comet fan** fires directly from the lower rooftops and upper battlements of Cinderella Castle, shooting bright gold comet streamers outward in a wide "V" shape.

**6. Lasers and Lighting**
* **Searchlights:** High-intensity beam fixtures positioned behind the hub and behind the castle outer walls. During this segment, they project **amber/gold and lime-green/emerald beams** tilted outward at 30° to 45° angles, suggesting the rigging or cannons of a pirate galleon.
* **Lasers:** No sharp geometric laser vectors are visible in this specific segment; beam effects are driven by searchlights and lighting fixtures.
* **Ground Flashes:** A bright white/gold pyrotechnic flash behind the lower castle wall occurs at **14:04**.

**7. The Castle**
* **Base & Wall Lighting:**
  * Flips from glowing green to intense blood red and burnt orange at **13:44**.
  * The central tower is highlighted in rich golden yellow, while the flanking turrets and roofs remain saturated in deep red and amber.
  * At **14:08**, flashes completely to high-intensity warm white/gold.
* **Projections:**
  * **13:45 – 13:58:** The façade displays textures of pirate adventure—golden Aztec medallion/compass filigree spinning slowly on the main tower above the entryway, set against glowing ember-lit fortress walls.

**8. Characters**
* **Character:** **Captain Jack Sparrow** (from *Pirates of the Caribbean*).
* **Location:** Lower-center grid of the castle, framed within the central gateway and immediately above the main archway.
* **Size:** Approximately 1/4 to 1/3 the height of the main castle center block (comparatively small against the entire structure).
* **Movement:** Appears around **13:48**, standing/moving subtly within the projection frame inside the central archway, then dissolves/fades away by **13:59** as the tempo shifts.

**9. For your LED Boards (64x32 / 64x64)**
To capture this segment authentically on tiny matrix displays:
1. **The 13:44 Palette Snap:** Instantly flip the castle pixels from green/purple to deep crimson red with a bright gold center spire, while immediately firing vertical red comet pixels up the left and right borders.
2. **Gold Willow Canopy (13:48 – 13:56):** Generate falling gold sparkle pixels cascading downward from the top of the display over the castle, framed by pulsing red ground mines on the flanks.
3. **The Climax Fan (14:08):** Clear the sky for 1 second at 14:00, fire alternating white side dashes and central red dots (14:01–14:06), and then fire a dramatic outward "V"-shaped fan of gold comet pixels originating directly from the castle roofline at 14:08.

**10. What couldn't be seen**
* **Perimeter Hub Lighting:** Street lamps and hub projection towers are mostly cropped out.
* **Fine Projection Detail:** Because of camera exposure adjusted for bright fireworks, the exact details of the Jack Sparrow projection in the lower gate are slightly washed out, though the iconic silhouette and the Aztec gold medallion/compass motifs are recognizable.

**11. Our Version (Critique)**
* **What's right:** Identifying the dense red and gold aerial fireworks color scheme ("dense red chrysanthemums and gold willow fans").
* **What's wrong:** Saying **"Characters: none"** is incorrect—Captain Jack Sparrow is projected in the central gate area between ~13:48 and 13:58.
* **What's missing:**
  1. The rapid vertical red mines/comets flanking the castle from 13:44 to 13:57.
  2. The brief pause in overhead fire around 13:59–14:00 followed by the rhythmic red center shells and white flank comets (14:01–14:06).
  3. The signature finale element at 14:08: the massive V-shaped comet fan fired straight off the castle battlements.

</details>

### 7.7 He's a Pirate (finale)

- **Audio:** 837-849 s (13:57-14:09, 12 s) · **Video:** `--start 14:08 --end 14:20`
- **Our score now:** A white V fan of comets off the battlements at 14:08, then the sky turns red: red comets and fountains firing across the base, red peonies, flame jets. Characters: none.
- **Checked by eye (2026-10-14):** fine as it is.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 14:05-14:23 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** Exactly **14:08**. Marked by a massive percussive musical hit/cannon explosion and an immediate upward fan blast of brilliant white comets/gerbs launching from Cinderella Castle.
* **End:** Exactly **14:19** – **14:20**. Marked by the final sustaining orchestral chord of "He's a Pirate" dying down, the red perimeter fallout clearing, and the castle illumination shifting abruptly from fiery red/amber to deep cool blue/cyan at 14:19–14:20.
* **Accuracy of 14:08 to 14:20:** Spot on.

**2. Music**
* **Music:** "He's a Pirate" (composed by Klaus Badelt and Hans Zimmer) from *Pirates of the Caribbean*.
* **Lyrics / Spoken Lines:** Instrumental only; no singing or spoken dialogue during this finale barrage. Cannon fire, sword clashes, and cinematic battle explosions are mixed into the orchestral track.
* **Key Hits/Beats:**
  * **14:08:** First giant symphonic hit / cannon boom, cueing the castle rooftop comet fan.
  * **14:10:** Second orchestral accent, launching high-arching red and gold comets.
  * **14:11 – 14:12:** Heavy triple orchestral crash, unleashing the massive 360° perimeter red mine/comet barrage.
  * **14:16 – 14:17:** Final explosive orchestral climax of the melody.
  * **14:18 – 14:20:** Sustained low strings and brass resolving as the tempo drops and the track transitions out of the battle sequence.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **14:08** | Rapid high-power white comet/gerb fan bursts upward and outward from behind the castle roofline. | Intense yellow-gold/white floodlights flare on the castle face; warm searchlights point up. | Whiteout flash, instantly washing out the facade into gold/white. | None. |
| **14:09 – 14:10** | Wide V-shaped fan of red and gold crossettes/comets shoots high above the spire. | Red and amber side washes on trees; green/gold spotlights angled upward. | Castle projection shows pirate ship / stone texture illuminated in glowing yellow-green and fiery orange. | None. |
| **14:11** | Thick red arching comets / tourbillons erupt upward from behind the spire in a narrow fan; red mines fire at base. | Bright red base uplighting flashes intensely. | Lower facade glows dark crimson/amber; battlements in silhouette. | None. |
| **14:12 – 14:15** | Massive full-perimeter perimeter barrage: hundreds of red comets with bright white/silver rising tails shoot up across the entire left, centre, and right horizon to high altitude. | Cyan and red searchlight beams sweep upward from the castle base into the sky. | Castle saturated in deep fiery crimson and golden amber. | None. |
| **14:16 – 14:17** | Second wave of red perimeter tails pop and crackle at the top; dense wall of red fire across the entire sky. | Cyan searchlights actively scissor/cross behind the castle spires. | Red wash gradually dims on upper towers; amber remains on base. | None. |
| **14:18 – 14:19** | Red fallout finishes drifting down; small twinkling white hang-time strobes drift in the upper sky. | Cyan/blue searchlights sweep outward; castle facade wash snaps from red to cool blue/teal. | Castle shifts from warm flame colors to cool blue/aqua stonework. | None. |
| **14:20** | Sky clears of active launches; faint white strobe/ember residue fades out. | Low-intensity cyan/blue stage lights sweep gently. | Deep royal blue and teal base projection with eerie glowing windows. | None. |

**4. Fireworks in the Sky**
* **14:08 – 14:10:**
  * *Type/Color:* White/gold glittering comets and red comet tails.
  * *Height & Side:* Mid to high level, originating directly behind Cinderella Castle, spreading outward in mirrored V-fans. Count: ~20–30 comet trails.
* **14:11 – 14:17 (Perimeter Finale):**
  * *Type:* Perimeter comet mines and comets with rising silver/white tails terminating in intense ruby-red stars/strobes.
  * *Height & Side:* Low, mid, and high spanning 180° across the viewer’s field of vision (left perimeter, center castle, right perimeter).
  * *Count & Rhythm:* Continuous rapid-fire barrage, firing dozens per second (over 200+ individual red tracer lines launched across the full width between 14:12 and 14:16).
* **14:18 – 14:20:**
  * *Type:* Falling red embers and hanging white micro-strobes drifting downwards. No new sky bursts launched.

**5. Fireworks on the Castle**
* **14:08:** Giant white upward fountain/gerb blast launched directly from the lower rooftops and rear battlements of the castle, creating a bright silhouette.
* **14:09 – 14:11:** Angled low-level red/gold comet mortars fired from the castle turrets/shoulders, fanning left and right.

**6. Lasers and Lighting**
* **Lasers:** No distinct pinpoint graphical lasers are visible during this specific barrage; the effect is driven predominantly by high-output wash fixtures and moving-head searchlights.
* **Searchlights / Beams:**
  * **14:08 – 14:11:** Amber and green-yellow searchlight beams positioned around the hub/castle moat pointing steeply skyward.
  * **14:12 – 14:18:** Brilliant cyan/electric-blue searchlight beams cut diagonally through the red barrage, fanning and crossing behind the central spire.
* **Flames / Fountains:** No real physical flame projectors are fired in this sequence.

**7. The Castle**
* **Internal / Architectural Lighting:**
  * **14:08:** Overwhelmed by a high-intensity white flash/flare from the rooftop fireworks.
  * **14:09 – 14:11:** Lower base and turrets washed in saturated warm amber and lime-green.
  * **14:12 – 14:17:** Deep crimson floodlights saturate the entire castle profile to match the red perimeter barrage.
  * **14:18 – 14:20:** Instant transition: crimson wash cuts off, replaced by cold navy blue and cyan LED washes on all towers and spires.
* **Projections:**
  * **14:08 – 14:11:** Abstract nautical/pirate masonry textures (dark stone blocks, cannon ports, glowing lanterns).
  * **14:12 – 14:17:** Washed out by fiery red ambient lighting and pyrotechnics; castle functions primarily as a dark fortress silhouette against the bright sky.
  * **14:18 – 14:20:** Cold blue pirate shipwreck/underwater masonry projection appears on the main gate and center turret.

**8. Characters**
* **None visible:** No Disney or *Pirates of the Caribbean* characters (e.g., Jack Sparrow, Davy Jones, or skeleton pirates) are projected or depicted during this specific finale burst (14:08–14:20). The scene is purely atmospheric and pyrotechnic.

**9. For Our Boards (LED Matrix Recreation)**
To capture this iconic moment on a 64x32 or 64x64 matrix:
1. **The 14:08 Center Blast:** Start with a dark/amber castle silhouette, instantly bursting with a vertical white V-fan of fast-moving bright white pixels shooting upward from behind the central tower.
2. **The 14:12 – 14:16 Perimeter Red Wall:** Fill the bottom half/edges of the matrix with dense columns of rising red pixels with white tips, covering the entire display width (left, center, right), while turning the castle structure deep red.
3. **The 14:18 – 14:20 Color Snap:** Clear the red sky pixels, leave faint lingering white sparkle pixels drifting down, and snap the castle silhouette pixels from bright red to deep blue/cyan with cyan beam lines angled outward behind it.

**10. What You Couldn't See**
* Projections on the castle facade between 14:12 and 14:16 are partially obscured/washed out by the sheer intensity of the red pyrotechnic illumination.
* The exact ground launch positions along the far perimeter berms are outside the camera frame (only their rising trails into the sky are visible).

**11. Our Version**
* **What's right:** "A ruby-red and white perimeter finale" is exactly right for the main barrage (14:12–14:17). Stating "Characters: none" is completely correct.
* **What's wrong:** Omitting the opening white/gold comet fan burst at 14:08 and missing the dramatic color snap to blue at 14:19–14:20.
* **What's missing:**
  1. The initial white/gold castle rooftop fan burst at 14:08 that kicks off the finale.
  2. The cyan/electric-blue searchlight beams crossing behind the castle while the red perimeter fires.
  3. The immediate color transition of Cinderella Castle turning from fiery crimson to deep ocean blue/cyan at 14:19–14:20 as the music resolves.

</details>

## 8. Triumph (audio 14:09-16:32, video 14:20-16:43)

### 8.1 Embers

- **Audio:** 849-889 s (14:09-14:49, 40 s) · **Video:** `--start 14:20 --end 15:00`
- **Our score now:** "Remember who you are": the castle near-black with an ember core, Mufasa in the clouds; between his lines two gold comets (video 14:38 and 14:46). Characters: Mufasa.
- **V2:** stage castle; actors mufasa (Mufasa's face fades in among the stars over the spire).
- **Checked by eye (2026-10-15):** Mufasa as we already have him. But it isn't fireworks-free: there are definitely fireworks just before Mufasa appears (Gemini's gold comets with searchlights, about 14:38 and 14:46), so add them.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 14:17-15:03 · notes: none</summary>

**1. Where this part starts and ends**
* **Start (14:20):** Starts as the grand villain/conflict finale fireworks completely fade out. The musical score drops from chaotic, booming battle music down to a quiet, somber orchestral tone. The castle lighting drops to a dark silhouette with fiery ember cracks. Your 14:20 start timestamp is **exact**.
* **End (15:02):** Ends as Mufasa’s final whispered *"Remember..."* echoes away, and Cinderella Castle shifts from dark blue/ember tones into peaceful blue/purple lighting as the gentle solo flute/piano intro to Hercules (*"Go the Distance"*) begins at 15:02 (singing begins at 15:03: *"I have often dreamed..."*). Your 15:00 end timestamp is **about 2 seconds early**.

**2. Music**
* **Song / Score:** Dramatic, somber orchestral interlude transitioning from the Villains/Defeat sequence into the stirring Lion King theme and the quiet intro of *Go the Distance* (Hercules).
* **Dialogue / Spoken Lines:**
  * **14:33 – 14:35:** Mufasa: *"Look inside yourself."*
  * **14:35 – 14:36:** Young Simba (faint child's voice): *"Simba."*
  * **14:40 – 14:44:** Mufasa: *"You are more than what you have become."*
  * **14:48 – 14:51:** Mufasa: *"Remember who you are."*
  * **14:52 – 14:55:** Mufasa: *"Remember..."*
  * **15:03:** Vocal begins: *"I have often dreamed..."*
* **Musical Hits / Beats:**
  * **14:38:** Subtle orchestral punctuation synced to a sweeping fan of searchlights and a gold comet launch.
  * **14:46:** Second orchestral swell/hit synced to another gold comet launch.
  * **14:57 – 15:01:** Low strings fade down into gentle harp/chimes leading into the soft piano/flute melody of *Go the Distance* at 15:02.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **14:20 – 14:30** | None (sky quiet/clearing) | Sweeping faint blue beam lights from hub perimeter; castle illuminated in deep purple/blue edges | Darkened battlements, glowing fiery embers and cracks across lower walls and center gateway | None |
| **14:31 – 14:37** | None | Low blue beam lights at sides; center spotlight illuminates castle spire | Glowing golden fire/ember texture gathers on center upper tower | Mufasa’s lion face appears within the golden fiery cloud on the center tower (14:32) |
| **14:38 – 14:45** | 1 thick gold glittering comet trails up to the upper-left (launches 14:38) | Sweeping white/pale-blue spotlights fan outward from behind castle base | Center tower blazes in golden amber/orange clouds surrounded by dark navy/purple outer turrets | Mufasa’s face remains visible, swirling gently in the golden glow |
| **14:46 – 14:51** | 1 thick gold glittering comet trails up to the upper-left (launches 14:46) | White/pale-blue searchlights cross behind castle and pulse | Golden ember cloud reaches peak brilliance on upper center tower | Mufasa’s face remains centered, speaking |
| **14:52 – 15:00** | None (sky dark) | Blue searchlights sweep low across the sides; base stays dim | Golden glow slowly dissolves into deep indigo/midnight blue across the main tower | Mufasa’s face fades out into mist/smoke by 14:54 |
| **15:01 – 15:03** | None | Searchlights reset; soft ambient cyan/blue wash comes up | Soft blue and purple wash fills the walls; warm light inside gateway | None |

**4. Fireworks in the sky**
During this quiet, contemplative scene, sky fireworks are intentionally minimal:
* **14:38:** A single **thick gold glittering comet** launches from ground level behind the left side of the castle, ascending diagonally toward the upper-left sky (reaching spire height before burning out).
* **14:46:** A second identical **thick gold glittering comet** launches along the exact same diagonal trajectory to the upper-left, reaching spire height before burning out.
* **Count:** Exactly **2 comet launches** in total. The rest of the sky is completely dark and clear of bursts.

**5. Fireworks on the castle**
* **None.** No gerbs, fountains, rooftop strobes, or lancework fire from the castle structure itself during this segment.

**6. Lasers and lighting**
* **Lasers:** None visible during this scene.
* **Searchlights / Moving Beams:** 
  * Banks of white/pale blue moving searchlights located behind and beside Cinderella Castle.
  * At **14:38** and **14:46** (matching the two comet launches), the beams fan outward across the sky in synchronized, sweeping searchlight arrays before narrowing down.
* **Flames & Fountains:** None.

**7. The castle**
* **Base Architecture Lighting:** The outer walls, lower flanks, and side turrets remain bathed in a moody, deep midnight-blue and dark violet wash, keeping the overall structure in near-silhouette.
* **Projections:**
  * **14:20 – 14:30:** The castle facade appears scarred and fractured with smoldering orange/amber ember cracks running through the central archway and lower midsection.
  * **14:31 – 14:52:** A radiant, billowing cloud of golden-orange embers and clouds consolidates specifically on the upper center tower and beneath the main spire.
  * **14:53 – 15:01:** The golden clouds fade away, leaving the entire castle in deep royal blue and violet stone textures.

**8. Characters**
* **Character:** **Mufasa** (The Lion King).
* **Location on 3x3 Grid:** **Center-Center to Center-Top** (projected directly across the main upper tower, just below the clock and main spire).
* **Size:** Spans approximately 25%–30% of the castle's total vertical height; concentrated tightly on the center facade of the upper tower.
* **Motion / Presentation:** He fades in from within a swirling cloud of golden embers starting at 14:32, remains centered and gently shifting like animated fire/clouds as he speaks his lines, and slowly dissipates/fades away between 14:52 and 14:54.

**9. For our boards**
To capture this moment authentically on a 64x32 or 64x64 LED matrix:
1. **The High-Contrast Color Palette:** Keep the castle perimeter and outer towers near-black and deep dark indigo. Concentrate all warm amber, bright orange, and yellow pixels exclusively on the center upper tower to represent the glowing ember cloud/Mufasa.
2. **The Two Diagonal Gold Comets:** At 14:38 and 14:46, launch a single pixel (or 2-pixel gold streak with trailing sparks) angled up and to the left against the pitch-black sky. These sparse, deliberate shots provide the signature sparse emotional tempo of this scene.
3. **Fade Timing:** Slowly intensify the golden center from 14:31 to 14:45, hold through the line *"Remember who you are,"* then smoothly fade the core to dark blue by 14:54 as the music softens.

**10. What you couldn't see**
* The camera zooms in slightly between 14:31 and 14:37, cropping out the far outer perimeter launch points, but zooms back out to full wide-angle by 14:38.
* Low-lying perimeter ground effects (if any existed far out on the hub walkways) were blocked by foreground trees and castle hub turrets.

**11. Our version**
* **What's Right:** 
  * *"Castle near-black with an ember core"*: Exactly right. The castle is kept dark with deep blue/purple accents, focusing all brightness on the glowing ember center.
  * *Mufasa in the clouds*: Accurate. He appears within the golden fiery cloud on the center upper tower.
  * *Audio quote*: *"Remember who you are"* is the defining central line of the scene.
* **What's Wrong:**
  * *"No fireworks"*: **Incorrect**. While the sky is mostly dark, there are **two distinct gold comets** launched at 14:38 and 14:46 trailing upward to the upper-left.
* **What's Missing:**
  * The sweeping **white/pale-blue fanning searchlight beams** from behind the castle that accompany the comets at 14:38 and 14:46.
  * The transition at 15:02 where the golden ember dissolves back into cool blue before the Hercules sequence starts.

</details>

### 8.2 Go the Distance (the castle rebuilds)

- **Audio:** 889-915 s (14:49-15:15, 26 s) · **Video:** `--start 15:00 --end 15:26`
- **Our score now:** Cyan, royal blue and gold columns; Hercules in gold light; the keyhole glows; sky nearly dark. Characters: Hercules.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 14:57-15:29 · notes: none</summary>

Here is the breakdown of the "Go the Distance / Castle Rebuilds" segment of *Happily Ever After*:

**1. Where this part starts and ends**
* **Starts at 15:01 – 15:02:** The chaotic red/orange embers of the preceding villain battle extinguish at the castle base. The opening gentle piano/harp notes of *"Go the Distance"* begin, the first vocal enters at **15:02**, and cyan/golden light streams begin reconstructing the shattered castle. (Your 15:00 timestamp is about 1–2 seconds early).
* **Ends at 15:26:** The choir hits the peak sustained crescendo note on the word *"be"*. A bright golden light bursts out of the main gate archway ("keyhole"), and at **15:26–15:27**, the quiet sky breaks with the first dual golden aerial shell bursts. (Your 15:26 end time is exact).

**2. Music**
* **Song:** *"Go the Distance"* (from Disney’s *Hercules*, Alan Menken / David Zippel).
* **Vocals & Lyrics:**
  * **15:02 – 15:13:** Female solo: *"I have often dreamed / Of a far-off place / Where a hero's welcome / Would be waiting for me..."*
  * **15:14 – 15:19:** Male solo: *"Where the crowds would cheer / When they see my face..."*
  * **15:20 – 15:26:** Full choral harmony / duet: *"And a voice keeps saying / This is where I'm meant to be—"*
* **Key Musical Hits:**
  * **15:01:** Transition downbeat as the quiet piano melody takes over.
  * **15:14:** Male vocal entry and strings swell.
  * **15:26:** Huge orchestral and choral brass swell on *"be"*, triggering the golden gate bloom and first aerial fireworks.

**3. Timeline**
| Time | Fireworks | Lasers and lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **15:01 – 15:05** | None (sky dark) | Perimeter floodlights dim deep blue | Ruined facade transforms; cyan & gold light streams rise up towers | Hercules fades into lower arch portal in warm amber light |
| **15:06 – 15:12** | None | Low ambient blue | Fluted Greek columns and golden fretwork complete rebuilding upward | Hercules stands in central portal |
| **15:13 – 15:19** | None | Narrow blue uplighting beams along hub perimeter | Camera zooms; upper towers/spire glow royal blue and violet | Hercules holding the golden medallion in center stained glass window |
| **15:20 – 15:23** | None | Side searchlight beams sweep faintly upward right | Stained-glass window frame sparkles; clock face glows cyan | Hercules gazes forward heroically |
| **15:24 – 15:25** | None | Stage/hub perimeter washes golden | Center archway/gate ("keyhole") ignites with intense golden-yellow light | Hercules dissolves into the golden glow |
| **15:26 – 15:28** | Two large golden chrysanthemums burst high (left and right of spire) at 15:26; massive willow bursts at 15:28 | Bright white/gold flash from castle base; vertical white searchlights on right | Entire castle bathed in radiant royal blue, cyan, and glowing gold | None (scene transitions to golden gate / fireworks) |

**4. Fireworks in the sky**
* **15:01 – 15:25:** **Zero fireworks.** The sky is completely dark and silent. This deliberate quiet pause allows the castle rebuilding animation to take full focus.
* **15:26 – 15:27:** Exactly on the musical crescendo at 15:26, **two large golden chrysanthemum shells** burst high in the sky framing the spire (one high to the upper left, one slightly lower to the right).
* **15:28:** A massive, dense golden willow/brocade shell breaks directly over the upper central spire.

**5. Fireworks on the castle**
* **None** are launched from the castle body, parapets, or turrets during this specific segment (15:01–15:26).

**6. Lasers and lighting**
* **Lasers:** No sharp laser graphics or scanning beams are used here.
* **Searchlights / Uplights:** Faint, narrow cyan/blue searchlight beams project vertically from behind the trees on the right side of the hub (visible around **15:24–15:28**).
* **Floodlighting:** The castle base uses deep indigo and royal blue floodlighting. At **15:25–15:26**, a blinding warm-white/gold wash erupts from within the center archway.

**7. The castle**
* **Base illumination:** Turrets and spires are saturated in deep royal blue and violet.
* **Rebuilding Projection Animation:**
  * **15:01 – 15:10:** Vertical streams of cyan, aqua, and gold light travel upward across the facade, "repairing" the cracks from the previous battle. The masonry turns into classical Greek fluted columns with Greek-key (meander) decorative friezes.
  * **15:11 – 15:23:** The finished castle looks like an ancient Greek temple rendered in blue stone and glowing gold accents.
  * **15:24 – 15:26:** The center ground-level gateway ("the keyhole") begins to glow from within with warm amber light, rapidly expanding to an intense, radiant yellow-white bloom that overpowers the lower center facade.

**8. Characters**
* **Hercules:**
  * **Identity:** Hercules (adult form, wearing his bronze breastplate/armor and red cape).
  * **Location:** Center column, lower-middle section (grid position: center / center-bottom), inside the tall arched window/portal above the main gate.
  * **Size:** Approximately 1/5 the visible height of the castle facade.
  * **Appearance / Movement:**
    * Appears at **15:02** surrounded by a warm golden halo against the cool blue facade.
    * From **15:14 to 15:23**, he is framed in a heroic stance holding his medallion of the gods. He remains static within the frame, subtly breathing/shifting like a living stained-glass portrait.
    * Fades/dissolves into the brilliant golden light blooming from the archway at **15:24–15:25**.

**9. For your LED matrix boards**
1. **Vertical Rebuild Effect (15:02 – 15:10):** Keep the sky pitch black and animate vertical columns of cyan/aqua LEDs rising from the bottom baseline to the turret tops to represent the castle reassembling.
2. **Center Amber Portal:** Keep Hercules as a warm gold/amber cluster (around 6–10 pixels tall on a 64-pixel board) centered on the castle facade, contrasting against the blue/cyan structure.
3. **The Climax at 15:26:** At the exact beat of 15:26, flare the bottom-center gate pixels to solid bright white/yellow, followed immediately by 2 golden spark bursts at the top left/right of the spire.

**10. What couldn't be seen**
* From **15:13 to 15:24**, the camera operator zooms in tightly onto the castle spire and central window, cutting off the outer courtyard walls and outer perimeter launch points.
* Any character animations within the small side windows are either non-existent or too small to resolve.

**11. Our version**
* **What is right:**
  * *"Cyan, royal blue and gold columns"* is completely accurate to the rebuilding projection.
  * *"Hercules in gold light"* is accurate.
  * *"The keyhole glows"* is accurate (the archway intensifies into bright gold).
  * *"Sky nearly dark"* is accurate (in fact, completely dark until the exact 15:26 crescendo).
  * *"Characters: Hercules"* is correct.
* **What is wrong:**
  * Nothing in your description is incorrect.
* **What is missing:**
  * The **exact timing of the sky burst:** At **15:26**, the darkness ends abruptly with a pair of large gold chrysanthemum fireworks flanking the spire.
  * The **upward motion:** The columns don't just sit there; they actively reconstruct from ground to spire between 15:02 and 15:10.

</details>

### 8.3 Go the Distance

- **Audio:** 915-948 s (15:15-15:48, 33 s) · **Video:** `--start 15:26 --end 15:59`
- **Our score now:** The rebuilt castle blue, big gold chrysanthemums over the spire (video 15:29-15:46) as the pyro resumes. Characters: Hercules, Megara, Tarzan, Mulan, Merida, Aurora, Aladdin, Cinderella, Elsa, Anna, Woody, Tiana, Mickey.
- **Checked by eye (2026-10-15):** no Jane. From the user's screenshot of the stained-glass hero mosaic (gold frames, blue roofs, gold willows overhead): lower left Mulan, Aurora, Aladdin; Cinderella with Gus over the gate; lower right Tarzan (long hair, alone) and Aurora again; Mickey far right; up the centre Elsa and Anna left of the spire, Merida and Woody on the right-hand tower, Tiana near the top. Not seen at 15:24: the mosaic comes later in the scene (Gemini: from about 16:04).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 15:23-16:30 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **15:26**. 
  * *Marks the change:* The closing phrase of the previous transition ("...find my way") resolves into the bold brass fanfare of *"Go the Distance"*, punctuated at 15:26–15:27 by the first high double gold bursts above Cinderella Castle as the facade transforms into deep Greek-mythology blue with glowing golden constellation patterns and the Zeus temple portal.
  * *Prompt estimate:* 15:26 is **exact** for the launch of the main theme fireworks and musical downbeat.
* **End:** **16:29**.
  * *Marks the change:* The final soaring vocal cadence ("...where I belong" / hero's welcome climax) concludes with a massive crescendo: twin ring/satellite shell bursts flanked by giant ground fan plumes and a central gold willow explosion across the entire frame.
  * *Prompt estimate:* 16:27 is slightly **early** by about 2 seconds, as the musical climax and crowning firework barrage peak between 16:27 and 16:29.

**2. Music**
* **Song:** *"Go the Distance"* from Disney's *Hercules* (choral orchestral arrangement).
* **Lyrics & Musical Hits:**
  * **15:23–15:25:** *"...find my way..."* (soft closing resolve).
  * **15:26–15:27:** **Heavy brass and percussion strike** initiating the main motif.
  * **15:27–15:35:** *“I will find my way…”* (soloist).
  * **15:36–15:47:** *“I can go the distance…”* (horn countermelody).
  * **15:48–15:58:** *“I’ll be there someday, I can go the distance…”*
  * **16:00–16:02:** **Ascending orchestral run and drum roll** building to the key change / choir entrance.
  * **16:02–16:03:** **Major musical impact** as rainbow comets erupt from the castle battlements.
  * **16:04–16:15:** *“I will find my way, I can go the distance…”* (full cinematic choir).
  * **16:16–16:24:** *“I would cross the world, just to find my hero’s welcome…”*
  * **16:25–16:29:** Climax note on percussion/brass hits with massive ground-to-sky finale explosions.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **15:23–15:25** | None | Low blue architectural floodlights | Deep royal blue with glowing cyan Greek geometric patterns | Hercules medallion motif glowing in lower arch |
| **15:27–15:31** | Pair of gold brocade/willow peonies bloom high above spire, followed by a wide gold willow burst | Searchlights point vertically behind castle | Golden architectural linework sharpens against royal blue | Medallion glow deepens |
| **15:32–15:38** | Gold willow bursts raining down; bursts continue above spire | Cyan/white beam searchlights sweep subtly | Center archway turns warm golden amber | Megara appears inside the central portal (15:33–15:38) |
| **15:39–15:47** | Consecutive gold peonies and willow breaks above castle spire | Vertical spotlights flank castle walls | Stained-glass golden framing begins tracing upper windows | Hercules in silhouette/relief on upper turret level (15:45) |
| **15:48–15:58** | Series of bright white/gold strobing peonies and chrysanthemums | Blue ground beams sweep across castle facade | Blue and gold Greek columns form along castle towers | Hercules flexing/striking poses in upper center projection |
| **16:01–16:03** | 6 multi-colored comet tails (red, yellow, green) fan outward from castle turrets | Brilliant white flash on castle facade | Golden bursts of light wash over castle walls | Stained-glass window panels assemble across all levels |
| **16:04–16:15** | Massive gold willow bursts overhead with cascading crackle fingers | Sweeping cyan/blue laser lines shooting out from upper balcony into sky | Full stained-glass cathedral hero mosaic across facade (gold, blue, green, amber) | Left: Tarzan; Center: Hercules; Right: Mulan & Merida in arches |
| **16:16–16:23** | Golden comets and willow bursts blooming rhythmically overhead | Dual fan searchlights sweeping horizontally across the trees and sky | Mosaic stays illuminated in vibrant stained-glass colors | Hercules, Megara, Tarzan, Mulan, Merida clearly visible in side/center arches |
| **16:24–16:27** | Dense rapid gold willow cluster exploding high dead-center | White and yellow searchlights cross overhead | Facade pulses with bright internal illumination | Characters stand triumphant in stained glass panels |
| **16:28–16:29** | Two distinct ring/circle shells high left & right; wide outward-angled white comet mines along perimeter | Full-stage perimeter lighting at peak brilliance | Castle fully saturated in bright gold and azure blue | All hero stained-glass portraits fully displayed |

**4. Fireworks in the Sky**
* **15:27:** Mirrored pair of medium gold brocade peonies breaking high, left and right of the main spire.
* **15:29–15:31:** Large gold willow shell detonating high dead-center directly above the spire, trailing long golden tendrils.
* **15:33–15:43:** Steady wave (approx. 1 burst every 2 seconds) of high-altitude gold willows and chrysanthemum breaks alternating slightly left-of-center and right-of-center.
* **15:44–15:51:** Golden crackling peony bursts breaking mid-to-high level behind upper spires.
* **15:52–15:58:** Double/triple gold chrysanthemum bursts with bright white strobe centers breaking dead-center high.
* **16:04–16:15:** Continuous overhead golden willow canopy with hanging embers raining down across the entire width of the castle.
* **16:16–16:24:** Overlapping golden brocade shells bursting high center every 1–2 seconds.
* **16:28–16:29 (Climax):** 
  * **Perimeter:** Multi-shot angled ground-level comet mine racks firing wide fans of thick white/gold glittering comet tails outward to the left and right.
  * **Mid/High:** Massive center gold willow barrage.
  * **Upper Sky:** Two distinct ring/annular pattern shells breaking simultaneously high left and high right of the main spire.

**5. Fireworks on the Castle**
* **16:01–16:03:** A tight fan of **6 angled comets** launched directly from the castle’s mid-level roofline/turret launch points: 3 shooting left and 3 shooting right in distinct saturated colors (reds, yellows/greens), arching outward over the hub.
* There are no low fountain gerbs on the ground walls during this specific lyrical section; all other effects originate from rear launch sites behind the castle.

**6. Lasers and Lighting**
* **Lasers:** 
  * Active primarily from **16:04 to 16:29**, emitted from mid-level castle balconies.
  * Colors: Bright cyan, aqua-blue, and vivid green.
  * Motion: Sharp, fan-like geometric beams slicing upward and outward into the sky, oscillating in wide scans behind the fireworks smoke.
* **Searchlights:**
  * Ground and rooftop moving heads flank the castle. From **15:26–15:58**, they project vertical white/light-blue columns flanking the spires.
  * At **16:18–16:28**, they spread into wide crossing criss-cross scissor patterns across the night sky.
* **Flames & Fountains:** None used in this sequence.

**7. The Castle**
* **Base Castle Lighting:**
  * **15:26–16:00:** Deep lapis lazuli and royal blue flood lighting on all lower walls and upper spires, accented by warm gold flood on the central clock tower.
  * **16:01–16:29:** Bright warm architectural illumination matching the vibrant stained-glass projections.
* **Projections:**
  * **15:26–15:31:** Ancient Greek architectural motifs—Greek key borders, fluted Ionic/Doric column overlays, and golden constellation starlight on a midnight-blue stone facade.
  * **15:32–15:45:** Central gateway arch glows amber; glowing celestial designs pulse across the upper walls.
  * **16:01–16:04:** Transformative wipe: geometric lines of light race across the facade to map out multi-pane gothic/arch stained-glass window frames.
  * **16:04–16:29:** Full **Stained-Glass Hero Windows** display:
    * Lower left tower: Tarzan arch.
    * Central clock/portal section: Hercules hero portrait arch.
    * Lower right tower: Mulan & Merida arches.
    * Upper turrets: Intricate blue, gold, and turquoise mosaic tiles.

**8. Characters**
1. **Megara (*Hercules*):**
   * *Location:* Bottom-center (the main gate / entry archway portal).
   * *Size:* Approx. 1/6 to 1/5 of the castle’s vertical height.
   * *Motion:* Appears standing in a golden amber glow (15:33–15:38), looking outward, then fades as the arch motif transforms.
2. **Hercules (*Hercules*):**
   * *Location:* Center-middle (directly on the central tower facade below the clock face) and lower center.
   * *Size:* Approx. 1/4 of castle height.
   * *Motion:* Fades in around 15:45 flexing/heroic stance; at 16:04 becomes the dominant stained-glass central figure standing proudly in golden-orange armor against a blue field.
3. **Tarzan (*Tarzan*):**
   * *Location:* Bottom-left / lower-left turret archway (grid cell: middle-left / bottom-left).
   * *Size:* Approx. 1/4 of castle height.
   * *Motion:* Static stained-glass portrait framed in a tall arch from 16:04 to 16:29.
4. **Mulan (*Mulan*):**
   * *Location:* Bottom-right turret archway (grid cell: bottom-right).
   * *Size:* Approx. 1/5 of castle height.
   * *Motion:* Static stained-glass window portrait, standing heroically from 16:04 to 16:29.
5. **Merida (*Brave*):**
   * *Location:* Right-center wall / outer right turret archway (grid cell: middle-right).
   * *Size:* Approx. 1/5 of castle height.
   * *Motion:* Static stained-glass window portrait with bow from 16:04 to 16:29.

**9. For Our Boards (64x32 / 64x64 LED Matrix)**
1. **The 16:01 Turret Rainbow Comet Fan:**
   * At 16:01–16:03, firing 3 colored diagonal comet lines left (red/orange) and 3 right (yellow/green) directly off the castle shoulders is visually distinct and easy to render at low pixel resolution.
2. **The Stained-Glass Architectural Snap (16:04):**
   * Transition castle lighting abruptly from dark royal blue into segmented, multi-colored vertical portrait columns (amber center, green/red side pillars) with bright golden framing.
3. **The 16:28 Climax Barrage:**
   * Ground-level angled fan comets (white/gold lines shooting diagonally out from lower corners) combined with 2 distinct circular ring shells in the upper sky corners and a dense willow canopy in the top-center.

**10. What You Couldn't See**
* **Ground-level perimeter launching pads:** The physical firing mortars behind the trees left and right of the hub are obscured by the park tree line.
* **Turret archway fine details:** Due to low lighting and camera exposure, the fine internal linework of the stained-glass character faces (especially Merida and Mulan on the right towers) is slightly soft/overexposed during heavy firework flashes.
* **Jane (*Tarzan*):** Cannot be confirmed as visible on the castle facade in this footage (unsure; Tarzan is prominent on the left, but Jane is not clearly discernable alongside him).

**11. Our Version**
* **What's Right:**
  * Stained-glass hero windows framed in gold.
  * Gold and white willows, gold peonies, side comet plumes, and rainbow comets off the castle.
  * Hercules, Megara, Tarzan, Mulan, and Merida are all present.
* **What's Wrong / Missing:**
  * **Jane:** Incorrect (she does not appear alongside Tarzan in these hero stained-glass arches; only Tarzan represents his film here).
  * **Missing Firework Detail:** You missed the distinctive **twin ring/satellite shells** at the 16:28–16:29 finale, which are a signature visual marker of the crescendo.
  * **Missing Lighting Detail:** The transition from Greek constellation blue (15:26–16:00) into multi-color stained glass (16:04) accompanied by intense cyan/green sky-scanning lasers.

</details>

### 8.3a Go the Distance (hero mosaic)

- **Audio:** 948-976 s (15:48-16:16, 28 s) · **Video:** `--start 15:59 --end 16:27`
- **Our score now:** On "I can go the distance" (video 15:59) the castle turns to the stained-glass hero mosaic; gold chrysanthemums, red comets and a white chrysanthemum (16:06). Characters: Hercules, Megara, Tarzan, Mulan, Merida, Aurora, Aladdin, Cinderella, Elsa, Anna, Woody, Tiana, Mickey.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 8.4 Go the Distance (gold canopy)

- **Audio:** 976-992 s (16:16-16:32, 16 s) · **Video:** `--start 16:27 --end 16:43`
- **Our score now:** No smiley shells: white comet fans off the rooftops (video 16:28), red and gold bursts (16:32-16:36), a huge gold canopy (16:40). Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 16:24-16:46 · notes: none</summary>

Here is a detailed breakdown of the "Go the Distance (gold canopy)" segment from the recording:

**1. Where this part starts and ends**
* **Start:** **16:27** (your timing is accurate). This starts on the sustained climax chord of the *Hercules* ("Go the Distance") arrangement, marked by mirrored white comet fans launching outward and the first high-altitude pattern shells detonating.
* **End:** **16:44 – 16:45**. The massive gold willow canopy completely falls and fades, the triumphant orchestral swell resolves into soft chimes/strings, and the narrator begins speaking: *"And so, our..."* at **16:45**. Your 16:43 end-time is slightly early by about 2 seconds, as the willow canopy continues raining gold down to 16:45.

**2. Music**
* **Music:** Climax of **"Go the Distance"** (*Hercules*), orchestral and choral arrangement.
* **Lyrics / Vocals:** 
  * The soaring, sustained final choral/vocal note of the anthem holds through **16:27 – 16:35**.
  * No words are sung in this exact window—it is a sustained, triumphant full-choir belt/vowel chord.
  * At **16:36 – 16:44**, the choir trails off and the brass/strings hold a deep, resonant resolving chord beneath sparkling chimes.
  * At **16:45**, the male narrator begins: *"And so, our..."*
* **Big Hits & Accents:**
  * **16:28:** Cymbal crash / brass swell as two pattern shells detonate high overhead.
  * **16:30:** Rapid percussion/choral accent as fan volleys erupt low and mid-level.
  * **16:37 – 16:38:** The peak detonation bang of the massive gold canopy shell directly over the spire.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **16:24 – 16:26** | Central gold chrysanthemum rises behind spire; white strobing fallout. | Soft front wash, green lasers scanning low across audience/trees. | Stained-glass mosaic projections of Disney heroes/heroines on blue background. | Various stained-glass heroes (Hercules, Moana, Aladdin, etc.) static on facade. |
| **16:27 – 16:28** | Symmetrical white comet fans shoot outward left/right; 2 pattern shells (ringed Saturn/smiley effect) burst high left and right. | White searchlights fan upward from hub perimeter. | Stained-glass hero mosaic remains illuminated with blue-violet turret lighting. | Stained-glass hero portraits remain static across lower/mid facade. |
| **16:29 – 16:33** | Center-sky red-to-gold peony bursts; angled green comet fans criss-cross on flanks; white comets fire upward from roofline. | Vertical white searchlight beams flank the castle. | Stained-glass window montage remains steady on main facade. | Same stained-glass hero portraits. |
| **16:34 – 16:36** | Crackling gold/silver mines and fan barrages across both flanks; a single heavy shell launches behind the central spire. | Bright white ground searchlight beams point straight up into the sky. | Blue structural lighting on spires; stained glass on lower walls. | Same stained-glass hero portraits. |
| **16:37 – 16:41** | Massive golden weeping willow / kamuro shell bursts dead center above the main spire, opening into an enormous raining canopy. | Static vertical white beams framing the sides. | Blue core lighting; stained glass projections steadily displayed. | Same stained-glass hero portraits. |
| **16:42 – 16:44** | Golden willow tendrils drift down around castle spires, shimmering and crackling out. Sky clears. | White vertical searchlight beams dim down. | Castle transitions slightly darker as the canopy burns out. | Stained glass portraits start fading/prepping for narration scene. |

**4. Fireworks in the sky**
* **Pattern / Shaped Shells (16:28):** 
  * 2 high-altitude shells burst simultaneously at high left and high right. They appear as golden/white ringed/Saturn or smiley-face shells with outer perimeter dots.
* **Side Comets / Fans (16:27 – 16:35):**
  * Mirrored angled comets (white and bright lime-green) shooting out in fans from both left and right launch sites, alternating with rapid crackling mines.
* **Center Shells (16:29 – 16:33):**
  * Symmetrical red peonies and golden chrysanthemums exploding directly above the upper turrets.
* **The Climax Canopy Shell (16:37 – 16:44):**
  * A single, massive aerial shell (kamuro / brocade crown willow) fired behind the spire.
  * Bursts at **16:37 – 16:38** at high center and spreads wider than the entire castle footprint, slowly weeping downward in long, dense, shimmering gold trails until **16:44**.
* **Rhythm:** Heavy, dense barrage from 16:27 to 16:35 (roughly 4–6 projectile bursts per second), pausing for a brief half-second breath at 16:36 as the single giant shell launches, culminating in the single slow-motion gold canopy burst.

**5. Fireworks on the castle**
* **16:29 – 16:34:** White angled comet shots and small silver gerb/mine bursts launch directly from the castle rooftops/ramparts upward into the fan pattern, matching the ground-level flank comets.

**6. Lasers and lighting**
* **Searchlights:** Multiple powerful white searchlights positioned around the hub/moat, pointing straight up or slightly outward to form vertical light pillars framing the castle (**16:27 – 16:43**).
* **Lasers:** Subtle green laser beams originate from castle lower turrets, scanning horizontally across the tree lines and into the sky during 16:24–16:30.
* **Flames/Fountains:** No flame units or water fountains used in this specific cue.

**7. The castle**
* **Base & Turret Lighting:** Spires and upper turrets are bathed in a deep royal blue and indigo wash, with golden highlights picking out the ornamental trims.
* **Projections:** The entire front facade of Cinderella Castle is covered in an intricate **stained-glass window / mosaic design** framed in gothic arches. The projection maintains this heroic stained-glass tableau throughout the entire sequence without cutting or changing scenes until the narrator speaks at 16:45.

**8. Characters**
* **Appearance Style:** Projected as static, vibrant stained-glass mosaic portraits inside gothic arch window frames across the castle front.
* **Who & Where:**
  * **Hercules:** Lower-center gate / main entrance (bottom-center of 3x3 grid), approx. 1/5 castle height.
  * **Moana:** Bottom-left turret arch.
  * **Aladdin & Jasmine:** Mid-left facade arch.
  * **Tarzan / Merida / others:** Mid-right and bottom-right arch panels (stained glass style makes individual small side portraits slightly indistinct from wide hub distance).
* **Motion:** Static; they do not walk or fly during this cue—they remain luminous window panes.

**9. For our boards (LED matrix recreation)**
To capture this iconic moment on 64x32 / 64x64 pixels:
1. **The Green & White Side Fans (16:28 – 16:33):** Pixel comets shooting out at 45° angles from the left and right castle base, while the castle facade displays a multicolored stained-glass grid (blue background with amber/cyan panels).
2. **The "Gold Canopy" Drop (16:37 – 16:44):** A single central gold pixel launches high above the spire, detonates, and expands into a large umbrella/fan of shimmering yellow/gold pixels that slowly drift downward across the upper half of the display while all side firing stops.

**10. What you couldn't see**
* Exact facial features of individual characters in the outer stained-glass panels are slightly soft/diffused due to the wide-angle camera distance and bright firework backlight.
* Extreme low ground-launch positions to the far left and right are partially obscured by tree canopies in the hub.

**11. Our version**
* **What's right:** You correctly identified the smiley/ring shells, green side comets, and the gold willow canopy.
* **What's wrong:** Saying *"Characters: none"* is technically inaccurate. While no animated characters are moving across the sky or flying, the castle itself is explicitly covered in the iconic Disney hero stained-glass portraits (most notably **Hercules** centered in the grand archway).
* **What's missing:** 
  * The vertical white searchlight pillars framing the castle.
  * The red/gold chrysanthemum mid-level bursts accompanying the green comets (16:29–16:32).
  * The roofline comets shooting directly off the castle ramparts.
  * Adjusting the end timestamp by +2 seconds to **16:45** to allow the willow canopy to fully resolve before the narration.

</details>

## 9. Conclusion (audio 16:32-16:57, video 16:43-17:08)

### 9.1 Narrator closing

- **Audio:** 992-1017 s (16:32-16:57, 25 s) · **Video:** `--start 16:43 --end 17:08`
- **Our score now:** "Find your Happily Ever After": the stained-glass heroes stay lit through the narration, the keyhole glows; no searchlights, no fireworks. Characters: none.
- **Checked by eye (2026-10-15):** the narrator starts just after video 16:41, and the stained-glass hero mosaic (as in 8.3's check) stays up nearly the whole time he speaks. No searchlights (Gemini is right; our "searchlights pan" is wrong).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 16:40-17:11 · notes: none</summary>

Here is the detailed breakdown of the segment for your LED matrix recreation:

**1. Where this part starts and ends**
* **Starts at 16:44–16:45**: The music drops to a gentle, reflective orchestral underscore and the Narrator begins speaking (*"And so, our journey comes to an end..."*). Your suggested start of **16:43 is slightly early**, as the giant golden brocade willow from the previous scene is still brightly illuminating the sky.
* **Ends at 17:08**: The Narrator concludes with the words *"...happily... ever... after."* At **17:09**, the solo female vocal begins (*"Look at the sky..."* / *"The journey begins..."*) and a bright golden comet/rocket launches on the far left. Your suggested **17:08 is exact**.

**2. Music & Spoken Dialogue**
* **Music**: A soft, introspective orchestral version of the *Happily Ever After* theme featuring strings, harp, and warm French horns, leaving ample acoustic space for the spoken dialogue.
* **Dialogue**:
  * **16:45 – 16:48**: *"And so, our journey comes to an end."*
  * **16:48 – 16:51**: *"But yours, continues on."*
  * **16:51 – 16:54**: *"Grab hold of your dreams, and make them come true."*
  * **16:55 – 16:59**: *"For you are the key to unlocking your own magic."*
  * **16:59 – 17:02**: *"Now go. Let your dreams guide you."*
  * **17:03 – 17:08**: *"Reach out and find your... happily... ever... after."*
  * **17:09**: Female solo vocalist reprises the show anthem.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **16:40 – 16:44** | Massive gold brocade willow hanging and drifting in upper sky. | 8 upward white searchlight beams (4 left, 4 right). | Fully covered in stained-glass projection mapping. | Stained-glass character portraits visible across facade. |
| **16:45 – 16:47** | Gold brocade embers fade and burn out completely. | Searchlight beams shut off / fade away. | Stained-glass projection glowing softly. | Stained-glass character portraits static and shimmering. |
| **16:48 – 16:54** | None; sky is completely dark. | No searchlights; ambient projection only. | Stained glass remains illuminated. | Stained-glass character portraits continue. |
| **16:55 – 16:58** | None; sky is dark. | No searchlights. | Central entrance arch / keyhole begins glowing bright golden-white. | Character panels remain lit on towers. |
| **16:59 – 17:08** | None; sky is dark and silent. | No searchlights. | Golden-white magical glow expands up the central spire and lower portal. | Cinderella silhouette in center portal; surrounding stained-glass portraits remain. |
| **17:09 – 17:10** | Single bright gold comet/flare launches from far-left ground angling up. | Hub lighting prepares for finale. | Golden center glow reaches peak brightness. | Stained-glass portraits remain as female vocal starts. |

**4. Fireworks in the Sky**
* **16:40 – 16:46**: Residual gold willow/brocade stars drifting downward from the previous climax.
* **16:47 – 17:08**: **Zero fireworks**. The sky is completely dark, quiet, and clear of pyrotechnics to focus on the spoken message.
* **17:09 – 17:10**: A single high-intensity golden-white comet/rocket launches from the tree line on the far left, trailing upward and toward the right over the castle (the cue/signal rocket for Tinker Bell's arrival).

**5. Fireworks on the Castle**
* **None**. No fountains, gerbs, strobes, or roof launches occur on the castle structure during this speech.

**6. Lasers and Lighting**
* **Searchlights**: At 16:40–16:43, vertical white searchlight pillars flank the castle. By 16:45, they turn off completely, leaving the castle as the sole light source.
* **Lasers / Flames / Fountains**: None active.

**7. The Castle**
* **Base Architecture**: Completely covered in video projection mapping representing an illuminated stained-glass cathedral.
* **Projections**:
  * Arched stained-glass window panes filled with jewel-toned patterns (blues, purples, golds, greens, reds).
  * **16:55**: On the line *"For you are the key..."*, the central main portal archway transforms into a glowing, brilliant golden-yellow/white keyhole shape.
  * **17:02 – 17:08**: The golden light radiates outward through the lower center arch and up the seams of the central tower.

**8. Characters**
The characters do not animate or fly during this section; they are rendered as **static stained-glass mosaic portraits** inside window frames:
* **Center Bottom Arch (Base Center)**: Cinderella (standing in ballgown; becomes a glowing silhouette as the keyhole brightens).
* **Lower-Left Arch (Base Left)**: Snow White in blue/yellow gown.
* **Mid-Left Tower (Mid Left)**: Aladdin & Jasmine on the Magic Carpet.
* **Far-Left Tower Walls**: Pocahontas and Mulan medallions.
* **Lower-Right Arch (Base Right)**: Tiana & Prince Naveen in green formal attire.
* **Mid-Right Tower (Mid Right)**: Belle & Beast in ballroom attire.
* **Far-Right Tower Walls**: Ariel & Prince Eric.
* **Upper Central Turrets (Spire / Mid Top)**: Hercules / Tarzan / Rapunzel vignettes.
* **Timing**: They remain visible throughout the entire monologue from 16:45 to 17:08.

**9. For Your LED Boards**
1. **The Dramatic Drop in Energy**: Transition from dense gold pixels slowly raining down (16:44–16:46) to an entirely blank/black sky above the castle by 16:47.
2. **The Glowing Castle Keyhole**: Keep the castle body textured in rich blues, purples, and ambers (representing stained glass), then pulse a 4x6 pixel cluster in the center archway into blinding white/yellow starting at 16:55 and holding through 17:08.
3. **The Signal Comet (17:09)**: Right on the vocal beat at 17:09, send a single bright pixel with a 2–3 pixel trailing tail shooting upward at a ~60° angle from the bottom-left edge toward the castle peak.

**10. What Could Not Be Seen**
* Between 16:52 and 16:58, the camera zooms into the castle midsection, cropping out the outer wing turrets and ground perimeter.
* Due to the artistic stained-glass styling, finer details of the smaller upper-tower character cameos cannot be identified with complete certainty.

**11. Feedback on Your Current Version**
* **What’s right**: Stained glass is lit, the keyhole glows, and the sky has no fireworks during the speech.
* **What’s wrong**: 
  * *"Characters: none"*: This is incorrect. The stained-glass facade prominently displays the major Disney couples and heroes (Cinderella, Belle & Beast, Tiana & Naveen, Aladdin & Jasmine, Snow White) in arched panels across the front.
  * *"Searchlights pan"*: Incorrect. The searchlights turn off by 16:45; there is no moving searchlight pan during the monologue.
* **What’s missing**: The fading gold willow fallout across 16:44–16:46 at the beginning, and the single cue comet launching from the lower-left at 17:09.

</details>

## 10. Finale (audio 16:57-18:24, video 17:08-18:35)

### 10.1 Happily Ever After (reprise)

- **Audio:** 1017-1042.2 s (16:57-17:22, 25.2 s) · **Video:** `--start 17:08 --end 17:33`
- **Our score now:** The stained-glass hero mosaic stays on the castle as the reprise begins; white comets arc up and cross over the spire (video 17:15-17:27), no searchlights. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 17:05-17:36 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **17:08 / 17:09**. Marked by the narrator finishing the spoken words *"Happily... ever... after"* (17:05–17:08), followed immediately by the opening piano/strings and female solo vocals (*"Look at us..."*) at 17:09, and the first whistling comet launch at 17:10.
* **End:** **17:33**. Marked by the choir's entrance on *"You can fly!"* (17:29), the projection transition on Cinderella Castle from the stained-glass mosaic to royal red/blue/gold scrollwork (17:31–17:32), and the fan of comets launching just before Tinker Bell's flight begins at 17:34.
* **Assessment:** Your 17:08 to 17:33 window is **very accurate**. It encapsulates the reflective verse of the reprise leading precisely into the energetic "You Can Fly" transition.

**2. Music**
* **Songs:** *"Happily Ever After"* (Reprise) transitioning into *"You Can Fly!"* (*Peter Pan*).
* **Lyrics and Spoken Dialogue:**
  * **17:05–17:07:** Narrator (deep voice): *"Happily... ever... after."*
  * **17:09–17:14:** Female Solo: *"Look at us... the stories... that we've lived..."*
  * **17:15–17:18:** Female Solo: *"...were lost in all the glory, which reach far away..."*
  * **17:19–17:24:** Female Solo: *"...we'll live them again, just look up and reach to the sky..."*
  * **17:25–17:28:** Female Solo: *"...we all have the courage to fly-y-y..."*
  * **17:29–17:36:** Full Choir / Orchestra: *"You can fly! You can fly! You can fly!"*
* **Big Musical Hits:**
  * **17:09:** Soft downbeat (piano and strings) as the vocal verse begins.
  * **17:22:** Sustained high vocal belt on *"sky"*.
  * **17:27–17:28:** Crest on *"fly"*, where percussion and orchestra swell.
  * **17:29:** Massive orchestral and choral downbeat on *"You can fly!"* with brass and cymbal crash.
  * **17:33–17:34:** Second choral hit on *"You can fly!"* signaling the flight launch.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **17:05–17:08** | None active | Standard perimeter/stage floodlights | Stained-glass mosaic projection | Stained-glass character portraits |
| **17:09–17:14** | Whistling comets launch alternately from left and right | Floodlights steady | Stained-glass mosaic | Stained-glass portraits steady |
| **17:15–17:22** | Wave of ~8–10 whistling tourbillon comets criss-crossing high over spires | Floodlights steady | Stained-glass mosaic | Stained-glass portraits steady |
| **17:23–17:25** | Sky briefly clear of active bursts | Floodlights steady | Stained-glass mosaic | Stained-glass portraits steady |
| **17:26–17:28** | Pair of vertical gold comets shoot up flanks | White searchlight beams tilt up from hub/base | Stained-glass mosaic brightens | Stained-glass portraits steady |
| **17:29–17:30** | Criss-cross gold comets launch from flanks | White/gold searchlight fan | Stained-glass mosaic begins transition | Stained-glass portraits fade |
| **17:31–17:33** | Rising comet trails overhead | Searchlight beams active | Transitions to royal red, deep blue, gold scrollwork & clock | Characters disappear from projection |
| **17:34–17:36** | Upward fan of gold comets | Upward spotlights | Royal red/blue/gold motif | Tinker Bell flies from upper spire (17:34) |

**4. Fireworks in the sky**
* **17:10–17:22 (Whistling Crossing Comets):**
  * **Type:** Whistling tourbillon / serpentine comets (corkscrew motion with bright golden-white comet heads).
  * **Colour:** Bright warm golden-white.
  * **Trajectory & Direction:** Launched from ground launch positions low on the left and right sides of the castle. They arc high across the main spire, crossing each other in mid-air.
  * **Count/Rhythm:** ~10 to 12 individual whistling comets firing in steady, overlapping alternating succession (roughly one every 1–1.5 seconds) creating an arching criss-cross pattern.
  * **17:23–17:25:** Brief quiet lull in the sky as trails dissipate.
* **17:26–17:28 (Vertical Comets):**
  * **Type:** 2 straight-shooting gold comets / mines.
  * **Position:** Straight vertical launches on the left and right flanks of the castle, reaching spire height.
* **17:29–17:33 (Fan Comets):**
  * **Type:** Rapid fan of gold comet tails.
  * **Position & Direction:** Angled crossing shots from the perimeter flanks, firing upward and crossing over the castle roofline.

**5. Fireworks on the castle**
* **None:** There are no gerbs, fountains, or pyro fired directly from the castle parapets, balconies, or turrets during 17:08–17:33. All pyrotechnics launch from ground positions behind or beside the castle.

**6. Lasers and lighting**
* **Lasers:** No sky-scanning laser beams are prominent during this specific window.
* **Searchlights / Beams:**
  * **17:08–17:26:** Mostly low background ambient lighting/wash.
  * **17:26–17:33:** Multiple white and warm-gold searchlight beams switch on around the castle hub/base and point upwards into the sky, fanning outward to support the musical crescendo.

**7. The castle**
* **17:08–17:30 (Stained-Glass Collage):**
  * **Base Lighting/Projections:** Cinderella Castle is covered in an intricate stained-glass window mosaic. Upper spires and roofs are deep royal blue/violet; mid-level panels have dark lead lines and vibrant multicoloured glass panes; the lower central archway is illuminated in a warm glowing yellow/amber lantern light.
* **17:31–17:33 (Royal Transformation):**
  * **Projection Change:** The stained-glass windows dissolve/wipe away.
  * **New Scene:** The castle transforms into its classic finale royal motif: deep royal blue spires and turrets, crimson/red wall sections, prominent glowing gold architectural piping and baroque scrollwork, with a bright round clock face appearing on the main tower.

**8. Characters**
* **17:08–17:30 (Stained-Glass Projections):**
  * **Who & Where (3x3 grid):**
    * *Hercules, Moana, Aladdin & Jasmine, Merida:* Visible in stained-glass style panes on the middle-left and lower-left towers/walls.
    * *Tiana, Rapunzel & Flynn, Pocahontas:* Visible on the middle-right and lower-right towers/walls.
    * *Cinderella & Prince Charming:* Centered just above the lower gateway.
  * **Size:** Each portrait pane is roughly 1/8 to 1/6 the width of the castle façade.
  * **Movement:** Completely static, stylized stained-glass windows.
  * **Exit:** They fade/dissolve out completely between 17:30 and 17:32.
* **17:34 (Tinker Bell):**
  * Appears right after this segment at 17:34, physically flying on a wire from the upper-right spire down across towards the left, glowing brilliant green/white.

**9. For our boards**
For low-resolution LED matrix boards (64x32 / 64x64):
1. **The Criss-Crossing Whistling Comets (17:10–17:22):** The defining visual of this verse is golden pixels launching alternately from bottom-left and bottom-right, arcing over the center spire and intersecting.
2. **The Castle Mode Switch at 17:31:** The castle must clearly switch from a multicoloured mosaic (or stained glass blocks) to rich deep blue and red with gold edge accents and a central clock.
3. **The Musical Swell at 17:29:** Spotlights/beams fanning upward as the choir enters on *"You can fly!"*.

**10. What you couldn't see**
* Individual character faces in the lower/outer stained-glass panels are somewhat soft and compressed in the projection mapping, making exact identification of every minor panel difficult.
* Exact launch locations behind the castle perimeter are obscured by the castle structure and trees.

**11. Our version**
* **What's Right:**
  * Gold comets crossing over the spires (17:10–17:22).
  * Gold and white spotlights turning on and fanning up during the crescendo (17:26–17:33).
* **What's Wrong:**
  * *"Gold scrollwork, characters: none"* is **incorrect for 17:08–17:30**. During 90% of this segment, Cinderella Castle is wrapped in the colourful stained-glass character mosaic. The gold scrollwork does not appear until **17:31–17:32**.
* **What's Missing:**
  * The **stained-glass character mosaic** covering the castle body from 17:08 to 17:30.
  * The dramatic **castle texture wipe/change at 17:31** from stained glass to royal blue/red/gold.
  * The vertical/fan comet bursts at 17:26–17:33 accompanying the choir's entrance.

</details>

### 10.2 You Can Fly

- **Audio:** 1042.2-1080 s (17:22-18:00, 37.8 s) · **Video:** `--start 17:33 --end 18:11`
- **Our score now:** Tink takes off from the spire; red, gold, green and cyan; gold palms, red strobes, lime and purple; then a dense glitter barrage fills the sky, orange, then green, pink and orange again; gold comet fans off the rooftops as Tink takes off (17:34), no shaped shells. Characters: Tinker Bell.
- **Checked by eye (2026-10-15):** Tink's flight and the coloured bursts are almost simultaneous: time them however looks best on the board. No Big Ben clock face on the tower (Gemini is wrong there).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 17:30-18:14 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** Exactly at **17:33**. The choir sings the opening line *"You can fly!"* following the fanfare build-up from 17:30–17:32. Your 17:33 estimate is **exact**.
* **End:** At **18:10–18:11**. The choir holds the final climactic note of *"You can fly!"* through a huge white brocade shell barrage ending at 18:10, punctuated at 18:10–18:11 by two screaming golden/white whistle comets crossing over the castle. Your 18:11 estimate is **exact**.

**2. Music**
* **Song:** *"You Can Fly! You Can Fly! You Can Fly!"* from Disney’s *Peter Pan*, performed by an energetic choral and orchestral arrangement.
* **Lyrics & Timestamps:**
  * **17:33–17:35:** *"You can fly!"*
  * **17:35–17:37:** *"You can fly!"*
  * **17:37–17:40:** *"You can fly!"*
  * **17:40–17:48:** *"Think of the happiest things, it's the same as having wings..."*
  * **17:48–17:53:** *"Take the path that Moonbeams make..."*
  * **17:53–17:59:** *"If the Moon is still awake, you'll see him sneeze..."*
  * **17:59–18:10:** *"You can fly! You can fly! You can fly-y-y!"* (building to orchestral crescendo).
* **Major Musical Hits:**
  * **17:33–17:38:** Each vocal *"You can fly!"* triggers ascending perimeter comets.
  * **17:39:** Orchestral beat drop: first paired red peony bursts.
  * **17:43:** Beat transition: pair of bright orange-red chrysanthemums.
  * **17:48:** Line change: bursts transition into emerald-green peonies.
  * **17:52:** Melodic shift: bright gold glitter chrysanthemums.
  * **17:56:** Chorus shift: rich magenta/pink peonies burst.
  * **18:00:** Re-entry of *"You can fly!"*: massive orange-red canopy shells.
  * **18:05–18:09:** Final vocal run: rapid, dense succession of brilliant silver/white brocade and chrysanthemum shells.
  * **18:10:** Final chord peak: twin high-screamer crossing comets.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **17:30–17:32** | Golden comets criss-cross upward from sides. | Dark/accent beams off-axis. | Golden clockface on center tower, London swirls. | Peter Pan & Darling children silhouettes on upper towers. |
| **17:33–17:38** | Angled gold comet sweeps upward from castle perimeter. | Spotlights sweep toward sky; zip-line path lit. | Castle glows warm gold/amber with glowing clock face. | **Live Tinker Bell** flies on high wire from spire towards camera right. |
| **17:39–17:42** | Red peonies at mid-height; gold trailing shells high. | Beams fan outward horizontally from behind hub/castle. | Gold/yellow illumination, starry projections. | London flight motifs. |
| **17:43–17:47** | Symmetrical orange-red chrysanthemums with gold glitter. | Beams sweep outward across the night sky. | Castle saturated in deep crimson/gold wash. | Peter Pan / starry accents projected. |
| **17:48–17:51** | Vibrant emerald-green peony bursts left & right. | Green/cyan stage floodlights wash castle base. | Castle transforms into rich emerald-green and gold. | Tinker Bell fairy-dust trails swirl on facades. |
| **17:52–17:55** | Large golden willow/chrysanthemum shells above spire. | White/golden searchlights fan wide. | Castle transitions back to bright sparkling gold/amber. | Swirling stardust & golden pixie dust projections. |
| **17:56–17:59** | Bright magenta/purple peony bursts flanking the spire. | Purple wash lights across castle base and turrets. | Turrets bathed in violet/magenta and deep blue. | Silhouetted flying motifs in projections. |
| **18:00–18:04** | Large orange-gold brocade shells left, right, and center. | Rapid fanning searchlight sweeps behind castle. | Warm golden-red illumination with glowing clock tower. | Golden stardust cascades. |
| **18:05–18:09** | Dense, rapid barrage of brilliant white/silver brocades. | Upward white searchlights converge and pulse. | Brilliant white and golden royal lighting. | Cascading light sparkles. |
| **18:10–18:14** | Twin whistle comets cross; vertical comets & mines from hub. | White beam fans sweep wide; camera reframes. | Clock tower projection remains prominent; turrets blue/gold. | Projections begin transitioning. |

**4. Fireworks in the Sky**
* **17:30–17:38 (Launch & Tinker Bell Flight):**
  * Gold tail comets launch in mirrored diagonal criss-cross patterns from both sides (low to mid-height).
  * Rate: ~2–3 comets per second.
* **17:39–17:42 (Opening Peonies):**
  * Mid-to-high altitude: 2 medium-sized red peonies burst symmetrically on the left and right spires, followed immediately by high gold willow/dahlia bursts.
* **17:43–17:47 (Red Barrage):**
  * 4–6 high-altitude, large orange-red chrysanthemums bursting overhead with crackling gold cores, mirrored left and right.
* **17:48–17:51 (Green Transformation):**
  * 4 large emerald-green peonies burst high above both sides of the spire, matching the lyric *"Take the path that Moonbeams make"*.
* **17:52–17:55 (Gold Transformation):**
  * 3–4 large bright golden willow/chrysanthemum shells opening high directly over and flanking the spire.
* **17:56–17:59 (Magenta/Purple Transformation):**
  * 4 large magenta/purple peony bursts flank the central spire.
* **18:00–18:04 (Warm Amber/Orange Resurgence):**
  * 4–6 very large orange-red to gold brocade shells bursting at high altitude.
* **18:05–18:09 (Grand Climax):**
  * Intense, multi-shot barrage of 15+ heavy white-silver brocade and glittering chrysanthemum shells filling the entire upper sky directly above and behind the castle (~3–4 bursts per second).
* **18:10–18:14 (Crossing Comets):**
  * 2 high-screamer comet tails launch from ground level far left and right, arching across each other high above the central spire, followed by low vertical golden mines.

**5. Fireworks on the Castle**
* **Behind/Roof of Castle:** Low perimeter launcher racks immediately behind the castle turrets fire the angled ascending gold tail comets at 17:30–17:38 and the lower vertical golden mine bursts at 18:10–18:14.
* **Castle Turrets/Rooftops:** No stationary gerbs or fountain sparklers are active on the castle parapets during this specific song; all pyrotechnics are mortars and comets fired from the roofs and perimeter behind the castle.

**6. Lasers and Lighting**
* **Searchlights:** Banks of high-powered motorized beam fixtures behind the castle and hub walls project sharp beams into the sky:
  * At 17:41–17:48, they form wide angled horizontal and diagonal fans flanking the castle.
  * At 17:48–17:51, they shift into tight vertical columns flanking the green castle.
  * At 18:05–18:10, they criss-cross rapidly and pulse straight up during the white finale shell barrage.
* **Lasers:** No visible horizontal geometric laser sheet across the sky in this segment; emphasis is on high-intensity searchlight beams and flood washes.
* **Wash Lighting:** The castle body and lower hub walls dynamically color-wash in lockstep with the fireworks: Red/Amber (17:43) $\rightarrow$ Emerald Green (17:48) $\rightarrow$ Golden Yellow (17:52) $\rightarrow$ Violet/Purple (17:56) $\rightarrow$ Orange/Gold (18:00) $\rightarrow$ Full Brilliant White/Gold (18:05).

**7. The Castle**
* **Base Structure Lighting:** Turret roofs stay predominantly royal blue with gold spire caps, while the facade wall wash rapidly shifts color thematic palettes to match the lyrics and shell colors.
* **Projections:**
  * **17:30–17:47:** The central tower projects the illuminated clock face of Big Ben (glowing yellow/gold clock face in center-middle of the grid). Golden scrollwork, London architecture, and starfields wrap the lower wings.
  * **17:48–17:51:** Swirls of glowing green and gold fairy pixie dust spiral up the towers.
  * **17:52–18:09:** Pixie dust, stars, and celestial golden clouds cascade across all castle surfaces, pulsing brighter with each musical hit.

**8. Characters**
1. **Tinker Bell (Live Flight Performer):**
   * **Location:** Starts from high on the main central spire (top-center grid) and flies diagonally down and across to the right side of the screen/sky (grid: top-center $\rightarrow$ top-right).
   * **Appearance/Movement:** Dressed in an illuminated, glowing green costume with lighted fairy wings. Glides down a zip-line high above the castle/hub at a steady, swift flying pace.
   * **Timing:** Appears exiting the spire at **17:34**, glides across the right sky from **17:35 to 17:38**, exiting frame right at **17:38**.
   * **Size:** Small human silhouette relative to castle (approx. 1/15th castle height).
2. **Peter Pan & Darling Children (Projections):**
   * **Location:** Silhouettes projected on the upper left and right turrets flanking the main spire (top-left and top-right sections of the castle facade).
   * **Appearance/Movement:** Silhouettes flying and floating around the Big Ben tower motifs.
   * **Timing:** Clearly established at **17:30–17:33** before dissolving into swirling golden pixie dust trails as Tinker Bell flies.

**9. For Our Boards**
1. **Tinker Bell's Diagonal Flight (17:34–17:38):**
   * On a 64x64 or 64x32 matrix, a bright green multi-pixel dot with twinkling white wings moving diagonally from top-center (spire) down toward the upper-right edge over 4 seconds will instantly sell the scene.
2. **Synchronized 4-Color Castle/Sky Palette Shifts (17:43–17:59):**
   * Group 1: Crimson/Red shells & red castle wash (17:43).
   * Group 2: Emerald-Green shells & green castle wash (17:48).
   * Group 3: Gold willow shells & warm yellow castle wash (17:52).
   * Group 4: Magenta/Purple shells & purple castle wash (17:56).
3. **The Brocade Climax & Screamer Crossing (18:05–18:12):**
   * A dense cluster of flashing white/silver pixels over the castle canopy for 4 seconds, immediately followed by two single bright white/gold tracer dots arching in opposite directions across the sky.

**10. What You Couldn't See**
* **Ground Level Launchers:** Mortar positions behind the castle and in perimeter launch fields are occluded by the castle itself and trees.
* **Hub Crowds:** The camera is angled upward; crowd elements at the base are in silhouette or out of frame.
* **Laser Fixture Apertures:** Specific laser scanner heads cannot be individually distinguished from the floodlight fixtures mounted on castle ledges.

**11. Our Version**
* **What's Right:**
  * Tinker Bell taking off from the spire is completely correct (17:34).
  * The color sequence (Red, Gold, Green, Cyan/Purple/Magenta) is accurate.
  * Identifying Tinker Bell as the key character is correct.
* **What's Wrong:**
  * **Tink’s flight timing vs fireworks:** Tinker Bell does not fly during the gold palms/red strobes; she flies *at the very beginning* (17:34–17:38) while the sky only has rising comets. The heavy colored peonies/chrysanthemums only burst *after* she has already cleared the castle.
  * **Cyan:** The palette shifts cleanly between Red $\rightarrow$ Emerald Green $\rightarrow$ Golden Yellow $\rightarrow$ Magenta/Purple; there is no dominant cyan shell phase.
* **What's Missing:**
  * **The Clock Face (Big Ben):** The central castle tower projection prominently features the illuminated clock face during this entire song.
  * **The Grand Climax Barrage (18:05–18:10):** The biggest fireworks moment of the segment—the massive white/silver brocade canopy—is omitted from your summary.
  * **The Twin Crossing Whistle Comets (18:10–18:12):** The signature pyrotechnic punctuation that ends the song is missing.

</details>

### 10.3 You Can Fly (gold arcs)

- **Audio:** 1080-1087 s (18:00-18:07, 7 s) · **Video:** `--start 18:11 --end 18:18`
- **Our score now:** Gold comets arching over the spire; white comet fans off the rooftops (video 18:15). Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 18:08-18:21 · notes: none</summary>

**1. Where this part starts and ends**
* **Starts:** **18:10** (video time). While the comets cross overhead around 18:11, their launch trails ignite and rise from the perimeter flanks at 18:10 on an orchestral fanfare. Your 18:11 start is slightly late.
* **Ends:** **18:18**. The gold comet trails fade completely by 18:17, leaving a brief one-second pause at 18:18 before the multicolored perimeter mine barrage erupts at 18:19. Your 18:18 end timestamp is accurate.

**2. Music**
* **Song:** Finale reprise of *"Happily Ever After"* (following the *"You Can Fly!"* transition from *Peter Pan* at 18:08–18:09).
* **Lyrics:**
  * **18:14–18:15:** Choir sings: *"Happily..."*
  * **18:16:** *"...Ever..."*
  * **18:17:** *"...After!"*
* **Musical hits:**
  * **18:10:** Brass fanfare hit on the launch of the first pair of comets.
  * **18:12:** Percussion/orchestral beat landing simultaneously with the gold aerial burst behind the spire.
  * **18:14–18:17:** Heavy choral downbeats on each word (*"Happily"*, *"Ever"*, *"After"*).
  * **18:18:** Brief vocal pause/breath before the massive finale crescendo at 18:19.

**3. Timeline**

| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **18:08–18:09** | Dense white/silver aerial peony/chrysanthemum canopy fades out. | Upward white beam lights from perimeter. | Ornate red and gold filigree; glowing Big Ben clock on center tower. | Big Ben clock face projected on upper center tower. |
| **18:10–18:11** | Two thick gold comets launch from low left and right, arching inward toward spire. | Searchlights sweep slightly outwards behind castle. | Castle base deep royal blue; Big Ben face brightly lit in white/cyan. | Silhouette in central gateway arch. |
| **18:12** | First pair crosses above spire; single golden chrysanthemum burst detonates above center. | Steady upward searchlights. | Consistent blue turrets with gold and red filigree. | Silhouette continues in gateway arch. |
| **18:13–18:15** | Fan of 6–8 mirrored gold comets launch from left and right flanks, creating criss-crossing overhead golden arches. | Stage/castle floodlights illuminate facade details. | Filigree glows brightly; lower gateway illuminated in warm gold. | Silhouette continues in gateway arch. |
| **18:16–18:17** | Comets reach apex, cross over the spire, and extinguish into falling gold embers. | Lighting remains steady. | Projections hold steady during the choral phrase *"Happily Ever After"*. | Silhouette remains visible in lower arch. |
| **18:18** | Sky is dark and quiet; previous trails dissipate. | Subtle searchlights angled outward behind castle. | Static golden/blue filigree and Big Ben clock. | Silhouette remains in lower arch. |

**4. Fireworks in the sky**
* **18:10–18:12:** 2 large gold comets with thick, sparkling tails launch simultaneously from ground level on the far left and right. They trace high, sweeping arcs inward toward the central spire, crossing behind it at ~18:11–18:12.
* **18:12:** 1 medium-large gold chrysanthemum burst detonates directly behind and above the castle spire at high altitude as the first comet pair crosses.
* **18:12–18:15:** A fan of approximately 6 to 8 thick gold comets launched in quick succession from both left and right perimeter pads. They shoot upward in sweeping inward arcs, crossing each other over the upper tower and spire between mid and high altitude.
* **18:16–18:17:** Comets burn out at the apex, leaving brief hanging golden sparks.
* **18:18:** Quiet lull; sky is clear of active bursts.
* **Total count:** Approximately 8–10 gold comet tails and 1 central aerial burst.

**5. Fireworks on the castle**
* **None.** No rooftop gerbs, fountains, or perimeter strobes are fired directly off Cinderella Castle’s walls or balconies during this specific window; all comets originate from ground launch sites behind/flanking the castle.

**6. Lasers and lighting**
* **Lasers:** None visible in this section.
* **Searchlights/Beams:** Pale white/blue searchlights shoot upward and outward from behind the castle tree line, remaining stationary or gently drifting.
* **Fountains/Flames:** None.

**7. The castle**
* **Base & Turrets:** Roof turrets are illuminated in rich royal blue, trimmed with golden architectural uplighting.
* **Projections:**
  * **Center tower (middle grid):** A glowing white-and-cyan projection of the Big Ben clock face with Roman numerals and ornate clock hands (*Peter Pan* motif).
  * **Walls/Balconies:** Covered in intricate red, gold, and turquoise storybook filigree/scrollwork.
  * **Lower gateway (bottom-center):** A glowing circular golden/chartreuse portal.

**8. Characters**
* **Big Ben clock face:** Center tower (middle row, center column of a 3x3 grid), taking up roughly the width of the tower; static, glowing projection.
* **Silhouette in Gateway:** Center-bottom (grid position bottom-center, inside the main gate archway). A small dark silhouette (proportioned to the doorway, roughly 1/10th castle height) is framed inside the bright circular portal throughout 18:10–18:18.

**9. For our boards**
1. **The Gold Crossing Arcs:** The defining visual is 3–4 bright gold comet heads launching from the bottom corners and tracing symmetrical curved arcs that intersect directly over the tip of the central spire.
2. **Spire Center Burst:** A single yellow/gold pixel cluster exploding at high center at 18:12 right as the first arc crosses.
3. **Castle Palette:** Royal blue turrets, warm yellow facade lighting, and a distinct bright circular clock face in the center tower just below the spire.

**10. What you couldn't see**
* Ground launch positions are obscured by trees and hub architecture.
* The specific identity of the small silhouette in the base gateway arch is slightly soft and indistinct due to glare from the circular backlighting (unsure whether it depicts Peter Pan, Wendy, or Mickey).

**11. Our version**
* **What’s right:** "Gold comets arching over the spire" is the exact signature pyro effect of this segment.
* **What’s wrong:** "Characters: none" overlooks the prominent projected Big Ben clock face on the center tower and the framed silhouette inside the lower gateway.
* **What’s missing:** The single gold burst detonating high over the spire at 18:12 right as the first pair crosses, and the timing of the choir singing the climactic title phrase *"Happily Ever After"* across 18:14–18:17.

</details>

### 10.4 Final chorus, keyhole opens

- **Audio:** 1087-1099.6 s (18:07-18:19, 12.6 s) · **Video:** `--start 18:18 --end 18:30`
- **Our score now:** Castle gold and red; a rainbow barrage, then a white and gold mine fan from the castle's foot. Characters: none.
- **Checked by eye (2026-10-15):** no keyhole. Rainbow bursts, then at the very end the white and gold fan: our version is right, with no white strobes or magenta bursts between them (Gemini is wrong on both).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.8-flash · video 18:15-18:33 · notes: none</summary>

**1. Where this part starts and ends**
* **Start:** **18:19** (your 18:18 mark is slightly early, at the tail end of the rising serpents/comet criss-cross). It starts on the choral downbeat of the final chorus (*"Happily ever after!"*), marked by simultaneous colored comet shoots and a massive multi-color burst canopy.
* **End:** **18:30** (accurate). Marked by a giant musical downbeat/cymbal crash where the multi-color barrage stops and an enormous, sweeping white-and-gold comet mine fan erupts upward and outward from the base and perimeter of the castle.

**2. Music**
* **Song:** *"Happily Ever After"* (Theme Song).
* **18:15 – 18:18:** Choral vocal build: *"...af-ter..."* sustaining a dramatic crescendo on a high vocal harmony.
* **18:18 / 18:19:** Giant hit: Lead vocals and full choir burst into the final chorus climax: *"Happily ever after!"*
* **18:24 – 18:29:** Orchestral brass and strings swell with continuing choral backing (*"reach out and find your..."*), accompanied by intense rhythmic crackling and booming firework shell breaks.
* **18:30:** Massive orchestral crash/hit that triggers the finale fan sequence.

**3. Timeline**
| Time | Fireworks | Lasers and Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **18:15 – 18:18** | Whistling golden-white criss-crossing comets rising left and right. | Dark/ambient perimeter lighting. | Red, gold, and blue heraldic projection; green/gold glowing keyhole at lower center gate. | None. |
| **18:19 – 18:24** | Multi-colored comets shoot straight up in columns on left and right; rapid barrage of multi-color peonies (red, green, blue, yellow, violet) behind and above spire. | Spotlights stay focused on castle facade. | Gold/red stained glass patterns; glowing green/gold keyhole portal radiating at gate. | None. |
| **18:25 – 18:28** | White strobe/glittering bursts transition into a dense, deep magenta/red and golden chrysanthemum canopy directly over the spire. | Backlight intensity increases. | Ornate gold filigree over red/blue walls; keyhole continues radiating. | None. |
| **18:29 – 18:30** | Lingering golden willow/brocade crackle overhead. | Searchlight beams begin to power up behind battlements. | Golden architectural trim; keyhole fully saturated with light. | None. |
| **18:31 – 18:33** | Massive fan of brilliant white/gold glitter comet mines erupts from castle foot/hub in a wide V-spread. | Blue/cyan searchlight beams shoot upward into the sky from castle rear. | Flash of bright white wash over castle facade. | None. |

**4. Fireworks in the sky**
* **18:15 – 18:18:** Rising whistling comets (roughly 10–12 trails) arching inward and criss-crossing over the central spire.
* **18:19 – 18:24 (The Rainbow Barrage):**
  * **Comet columns:** Mirrored sets of 4–5 vertical roman-candle/comet shoots on the left and right (red, green, cyan, magenta, gold) reaching mid-to-high level.
  * **Aerial breaks:** High-altitude, multi-colored peony and glittering chrysanthemum shells detonating in rapid waves (approx. 4–6 bursts per second) filling the entire upper grid (left, center, and right).
* **18:25 – 18:28:** High-altitude white glittering strobes and crackle cakes, immediately followed by dense crimson/magenta peony bursts right above the central spire.
* **18:29 – 18:30:** High golden brocade burst spreading outward as the colored sky barrage clears for a brief split-second pause.
* **18:30 – 18:33 (The Mine Fan):**
  * A symmetrical, wide-angle fan (approx. 14–16 points) of thick, glittering white-gold comets/mines blasting from low to high in a synchronized V-pattern.
  * The rhythm shifts from continuous multi-burst saturation (18:19–18:28) to an instant single-frame explosive fan wall (18:30).

**5. Fireworks on the castle**
* **18:19 – 18:28:** The fireworks originate from launch locations directly behind the castle walls and perimeter firing fields; no direct gerbs/fountains fire off the castle roofline itself during these seconds.
* **18:30 – 18:32:** Low-level mine charges erupt along the castle base/moat line and flanking lower hub roofs, producing the upward-reaching white-gold fan.

**6. Lasers and lighting**
* **Lasers:** None active during this segment.
* **Searchlights / Beams:** 
  * At **18:30 – 18:33**, bright cyan/blue searchlights power on behind the castle walls, projecting upward angled fan beams into the smoke/sky.
* **Facade wash:** A sudden high-intensity white flood wash hits the entire castle facade at **18:31** in sync with the mine explosion.

**7. The castle**
* **Projections:**
  * **18:15 – 18:29:** The castle facade features ornate golden filigree, jewel-toned reds, blues, and stained-glass architectural detailing on the towers and spires.
  * **The Keyhole:** At the bottom-center (castle main gate), a large, glowing, enchanted keyhole portal is projected in vivid green and bright golden-white light, radiating outward.
* **18:30 – 18:32:** The projections are bleached out by intense bright gold and white flood illumination for the grand finale hit.

**8. Characters**
* **None appear.** During this climactic chorus (18:18–18:30), no Disney character figures, faces, or silhouettes are projected on the castle or formed by pyrotechnics. The visual design is entirely architectural, portal-focused, and pyrotechnic.

**9. For our boards**
For 64x32 or 64x64 LED matrices, prioritize these three elements:
1. **The Keyhole & Castle Base (18:19–18:29):** Keep the castle in regal red/gold, but ensure a bright pulsating green/gold 3x3 or 4x4 pixel block at the bottom-center gate to represent the open magic keyhole.
2. **Rainbow Side Comets + Color Canopy (18:19–18:24):** Vertical multi-colored lines (magenta, cyan, green, yellow) shooting up the side columns, blossoming into multi-color twinkling pixels across the top half.
3. **The White-Gold Fan (18:30):** Clear the sky pixels for an instant, then draw a rapid outward-radiating V-shape / fan of bright white and gold trails originating from the lower castle perimeter, matched with a brief white castle wash.

**10. What you couldn't see**
* Extreme low ground level behind the guest crowd is occluded.
* Inside the bright core of the projected keyhole portal at the main gate, any very subtle character line art is completely blown out by high projection brightness.

**11. Our version**
* **What's right:** Castle gold and red; rainbow barrage; white and gold mine fan from the castle's foot; "Characters: none" is completely correct.
* **What's wrong:** The timing/transition: the rainbow barrage is not immediately followed by the white and gold fan; there is an intermediate wave of bright white strobes and deep magenta/red bursts over the spire between 18:25 and 18:29.
* **What's missing:** 
  1. The prominent glowing **green and gold keyhole** at the center main gate of the castle.
  2. The upward-pointing **blue/cyan searchlight beams** that activate alongside the white-and-gold mine fan at 18:30.

</details>

### 10.5 The last hit

- **Audio:** 1099.6-1104 s (18:19-18:24, 4.4 s) · **Video:** `--start 18:30 --end 18:35`
- **Our score now:** "After!": the white flash, then gold willows hanging over a castle washed in gold. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

<details><summary><b>2026-10-14</b> · gemini-3.7-flash · video 18:27-18:38 · notes: none</summary>

**1. Where this part starts and ends**
* **Starts:** **18:30** (or precisely at the upbeat right before the hit, **18:31**). At **18:30–18:31**, the vocal climaxes on the word **"AFTER!"**, accompanied by an explosive upward fan of white/gold comet mines and brilliant castle rooftop pyro, leading directly into the finale burst.
* **Ends:** **18:35** (reverberation fades through **18:37**). The massive golden brocade/willow canopy fully expands and begins to drift down as the climactic orchestral chord sustains and resolves, followed by red report bursts at **18:36**.
* **Verdict on your 18:30 to 18:35 window:** It is **spot on**. 18:30 initiates the launching fan and vocal climax ("AFTER!"), peaking into the massive golden willow canopy between 18:32 and 18:35.

**2. Music**
* **Song:** *"Happily Ever After"* (Theme Song finale reprise / Jordan Fisher & Angie Keilhauer arrangement).
* **Lyrics & Musical Hits:**
  * **18:27–18:30:** Choir/lead vocals crescendo through *"...happily ever..."*
  * **18:31:** Giant final vocal belt: **"...AFTER!"** landing on a massive orchestral downbeat/timpani hit and cymbal crash.
  * **18:32–18:35:** Sustained triumphant orchestral chord holds as the canopy sparkles.
  * **18:35–18:37:** Final orchestral swell and punchy concluding brass/percussion cutoff.

**3. Timeline**
| Time | Fireworks | Lasers & Lighting | Castle | Characters |
| :--- | :--- | :--- | :--- | :--- |
| **18:27–18:29** | Multi-colored bursts (red, green, white) and crackling willow shells bursting above and behind the spire; red star peony at 18:28. | Low perimeter floodlighting; warm architectural glow. | Vivid multi-color scrollwork/stained glass projections across the facade and turrets. | None visible (stylized decorative patterns). |
| **18:30** | Pre-launch mine trails and golden peony high center-left; launching trails rise. | Ground wash starts intensifying. | Warm gold and multi-colored projection mapping on main facade. | None visible. |
| **18:31** | **The Final Hit:** Huge wide-angled fan of bright white/gold comets/mines erupts across the perimeter; bright pyro sprays erupt directly from castle parapets. | Brilliant white front flash; bright blue/cyan searchlight beams flare upward from flanking hub/parapets. | Castle blazes bright in white flash, transitioning into vibrant golden-yellow lighting with blue turret accents. | None. |
| **18:32–18:34** | Massive gold brocade/crackling willow shell explodes directly over the castle spire, raining a dense canopy of gold tendrils across the entire sky. | Bright cyan/blue searchlight beams fan outward into the sky from castle flanks; warm golden wash illuminates the facade. | Golden glowing castle with intricate scrollwork projections, illuminated yellow clock face, and rich royal blue roofs. | None. |
| **18:35–18:38** | Gold willow canopy fades and drifts downward; secondary crackling red peony bursts pop high behind the spire at 18:36. | Blue beams remain fanned outward, panning slowly upward into the night sky. | Castle remains stably lit in radiant gold, green, and royal blue architectural lighting. | None. |

**4. Fireworks in the Sky**
* **18:27–18:29 (Buildup):**
  * Mixed aerial shells: Red, emerald green, and white strobe peonies and chrysanthemums bursting high behind and to the flanks of the spire.
  * Rapid cadence (approx. 2–3 bursts per second).
* **18:30–18:31 (The Hit / Fan):**
  * **Type:** Ground-launched angled comets / mine fan.
  * **Color:** Brilliant silver-white / gold.
  * **Pattern:** Wide symmetrical fan of roughly 12–16 thick rising comets shooting straight and diagonally upward from behind and beside the castle.
  * **Height:** Mid-to-high, framing the castle.
* **18:32–18:35 (The Finale Canopy):**
  * **Type:** Giant brocade / Kamuro / crackling willow shell.
  * **Color:** Deep glittering gold / amber.
  * **Position & Size:** Centered directly overhead/behind the highest central spire; fills the entire upper frame spanning left to right edge.
  * **Rhythm:** Single massive simultaneous explosion that holds and drifts slowly downward for 3–4 seconds.
* **18:36–18:37 (Post-climax):**
  * High-altitude red chrysanthemum/peony bursts with crackle popping centered behind the spire.

**5. Fireworks on the Castle**
* **18:31 (Peak Hit):**
  * Fountains / bright white gerb-style pyro flares fire upwards from the lower castle battlements and flanking parapet roofs.
  * Creates an instantaneous bright white blast of light emanating directly from the structure itself, perfectly synchronized with the ground-to-sky comet fan.

**6. Lasers and Lighting**
* **Lasers:** No distinct green or multi-color beam laser patterns are visible cutting through the sky during this specific 18:30–18:35 burst (the pyro takes visual precedence).
* **Searchlights / Moving Heads:**
  * At **18:31**, bright cyan/electric blue spotlight beams ignite from the base/flanks of the castle.
  * They fan outward symmetrically (pointing up and out toward the 10 o'clock and 2 o'clock positions), creating a strong blue V-shape contrast behind the castle against the golden fireworks.
* **Flashes:** A sharp, blinding white illumination flash occurs on the beat of 18:31 from castle stage strobes and rooftop pyro.

**7. The Castle**
* **Base & Turret Lighting:**
  * Turrets and conical roofs are illuminated in deep sapphire/royal blue.
  * The main body glows in intense radiant warm gold/yellow.
* **Projections:**
  * The facade is wrapped in ornate, glowing golden/amber filigree, scrollwork, and stained-glass architectural framing.
  * The clock face glows bright yellow-white.
  * The lower walls feature green and golden heraldic accents.
  * No scene change occurs during the hit—the projection holds as a majestic, static golden "triumphant royal castle" look.

**8. Characters**
* **Characters present:** **None.**
* During this final climax (18:30–18:35), no animated Disney characters are projected on the castle or formed in the sky. The visuals focus entirely on the grand architectural illumination and the overwhelming fireworks canopy.

**9. For Our Boards (64x32 / 64x64 LED Matrix)**
To make this moment feel authentic on a low-resolution matrix:
1. **The 18:31 Hit (White Flash + Comet Fan):** For 1–2 frames, trigger a full-screen white flash combined with angled white/yellow diagonal lines shooting up in a V-fan from behind the castle silhouette, while firing bright white pixels directly on the castle's lower rooftop ledges.
2. **The 18:32–18:35 Willow Canopy:** A huge dome of golden/amber cascading pixels expanding from high-center and slowly trickling downwards like golden rain.
3. **Contrast Color Palette:** The castle silhouette must be warm amber/gold in the center with striking royal blue spires, flanked by two diagonal cyan/blue beams pointing upward into the night sky.

**10. What You Couldn't See**
* **Ground launch points:** Launch locations behind the castle and in perimeter backstage areas are hidden behind trees and castle architecture.
* **Crowd/Moat details:** The lower moat and ground-level pathways are obscured by the silhouette of the foreground crowd.

**11. Our Version**
* **Your current version:**
  > *""After!": the white flash, then gold willows hanging over a castle washed in gold. Characters: none."*
* **What's right:**
  * Perfect timing on the "After!" hit.
  * The white flash is completely accurate.
  * Gold willows hanging overhead is the defining visual element.
  * "Characters: none" is 100% correct.
* **What's wrong:**
  * The castle is not *only* washed in gold; its turrets and roofs are distinctly rich royal blue, and bright electric cyan/blue searchlights shoot up from its sides.
* **What's missing:**
  * **The wide angled fan of comets/mines** shooting up across the entire frame at 18:31 right as the flash occurs.
  * **The rooftop pyro flares** directly on the castle battlements.
  * **The cyan/blue searchlight beams** forming an upward V-fan framing the castle beneath the gold canopy.

</details>

