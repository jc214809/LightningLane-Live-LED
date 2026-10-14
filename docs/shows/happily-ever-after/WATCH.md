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
- **Our score now:** Warm amber castle, blue spires, the keyhole glowing gold, white searchlights crisscrossing; no fireworks. Characters: none.

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

- **Audio:** 19-47 s (0:19-0:47, 28 s) · **Video:** `--start 0:29 --end 0:57`
- **Our score now:** Searchlights off, the keyhole dims, the sky dark. Characters: none.

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

### 1.3 Happily Ever After theme song

- **Audio:** 47-63 s (0:47-1:03, 16 s) · **Video:** `--start 0:57 --end 1:13`
- **Our score now:** Gold ribbons swirl, the keyhole glows; still no fireworks. Characters: none.
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
- **Our score now:** Red, purple and gold filigree on the castle, yellow and cyan searchlights; still no fireworks. Characters: none.

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

- **Audio:** 98-119 s (1:38-1:59, 21 s) · **Video:** `--start 1:48 --end 2:09`
- **Our score now:** The show's first fireworks on the chorus: red and gold peonies, then a red, gold and white strobe barrage. Characters: none.

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

- **Audio:** 119-137 s (1:59-2:17, 18 s) · **Video:** `--start 2:09 --end 2:27`
- **Our score now:** A huge gold palm and willow canopy, a gold brocade crown fading to smoke. Characters: none.

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

- **Audio:** 137-150 s (2:17-2:30, 13 s) · **Video:** `--start 2:27 --end 2:40`
- **Our score now:** Music-box transition: the castle turns royal blue, the sky dark, one bright star. Characters: none.

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

- **Audio:** 150-171 s (2:30-2:51, 21 s) · **Video:** `--start 2:40 --end 3:01`
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
- **Our score now:** Brass fanfare: a fan of white and gold comets, gold chrysanthemums, green and white glitter. Characters: Ray.
- **V2:** stage castle; actors ray (Ray drifts over and circles the spire).

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
- **Our score now:** Underwater turquoise and navy, glowing bubbles, sparse gold willows dripping over the spires. Characters: Ariel.
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

### 3.5 Part of Your World (climax)

- **Audio:** 215-256 s (3:35-4:16, 41 s) · **Video:** `--start 3:45 --end 4:26`
- **Our score now:** Sunbeams through the water, magenta and ruby peonies, gold and white brocade. Characters: Ariel.
- **Checked by lyrics (Whisper on our audio, 2026-10-13):** this is **"Out There"** (*The Hunchback of Notre Dame*), not Part of Your World: "Out there… strolling by the Seine, taste the morning air… just one day and then I swear I'll be content" from audio 215 s, its last "Out there!" at 254 s. Gemini's answer below (Quasimodo, the Notre Dame rose window) agrees. The score's title, characters and look for this scene are wrong.

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
- **Our score now:** Lavender, pink and turquoise castle; magenta and purple comets fanning left and right. Characters: none.

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
- **Our score now:** Cathedral bells, gothic stone and moss, doves; gold willow, emerald and white strobes, red and gold comets. Characters: Merida.
- **V2:** stage ghost; actors merida (fewer fireworks, so her arrow shows; Merida says her line at the bottom left, then on "touch the sky" shoots an arrow into a bullseye firework (64x64)).

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
- **Our score now:** Bagpipes and tartan; Up's balloons fill the castle and lift the house; red, green and blue comets. Characters: Merida, Carl, Up house.
- **V2:** stage ghost; actors up_house (Carl's house rises from behind the castle on its balloons).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 4.2 How Far I'll Go

- **Audio:** 325-370 s (5:25-6:10, 45 s) · **Video:** `--start 5:35 --end 6:20`
- **Our score now:** The heart of Te Fiti on the castle, ocean blues, the manta ray; sparse bursts building in green, gold and white. Characters: Moana, Gramma Tala.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 4.3 How Far I'll Go (climax)

- **Audio:** 370-398 s (6:10-6:38, 28 s) · **Video:** `--start 6:20 --end 6:48`
- **Our score now:** Heavy gold brocade barrage, turquoise searchlights, green and yellow shells. Characters: Moana.
- **V2:** stage off; actors canoe (Moana's canoe sails across once the castle goes).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

## 5. Friendship (audio 6:38-9:23, video 6:48-9:33)

### 5.1 Aladdin: a best friend by your side

- **Audio:** 398-412.5 s (6:38-6:52, 14.5 s) · **Video:** `--start 6:48 --end 7:03`
- **Our score now:** Spoken line over gold and purple lamp smoke on a midnight-blue castle. Characters: Aladdin.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.2 Friend Like Me (instrumental)

- **Audio:** 412.5-428 s (6:52-7:08, 15.5 s) · **Video:** `--start 7:03 --end 7:18`
- **Our score now:** Brass patterns and lanterns on the castle; blue and gold fountains from the roofs, white shells. Characters: Aladdin, Genie.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.3 Trashin' the Camp

- **Audio:** 428-446 s (7:08-7:26, 18 s) · **Video:** `--start 7:18 --end 7:36`
- **Our score now:** Vivid green and chartreuse, green flares and green and orange comets on the drums, green searchlights. Characters: Terk.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.4 Hakuna Matata

- **Audio:** 446-453 s (7:26-7:33, 7 s) · **Video:** `--start 7:36 --end 7:43`
- **Our score now:** Timon and Pumbaa in sunset yellow, orange and red; red and gold shells. Characters: Timon, Pumbaa.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.5 You've Got a Friend in Me

- **Audio:** 453-459 s (7:33-7:39, 6 s) · **Video:** `--start 7:43 --end 7:49`
- **Our score now:** Woody and Buzz on Andy's cloud wallpaper; red and yellow bursts. Characters: Woody, Buzz.
- **V2:** stage castle; actors buzz_woody (Buzz flies across, Woody waves from the ground).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.6 Friendship mash-up

- **Audio:** 459-514 s (7:39-8:34, 55 s) · **Video:** `--start 7:49 --end 8:44`
- **Our score now:** Ralph and Vanellope, Hiro and Baymax, Judy and Nick, Joy and Sadness; multicolour searchlights, steady pastel bursts. Characters: Ralph, Vanellope, Hiro, Baymax, Judy, Nick, Joy, Sadness.
- **V2:** stage off; actors ralph, baymax, memory_orbs (Ralph smashes bricks (0-14 s in), Baymax inflates and waves (15-22), Joy's and Sadness's memory orbs (35-54)).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.7 That's What Friends Are For

- **Audio:** 514-527 s (8:34-8:47, 13 s) · **Video:** `--start 8:44 --end 8:57`
- **Our score now:** Sulley and Mike opening doors across the turrets, turquoise and purple; soft gold shells. Characters: Sulley, Mike.
- **V2:** stage castle; actors mike (Mike peeks over the left turret, then the right).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.8 Friend Like Me (Genie)

- **Audio:** 527-554 s (8:47-9:14, 27 s) · **Video:** `--start 8:57 --end 9:24`
- **Our score now:** Genie in neon, the castle a pulsing marquee; crossing magenta, green and gold comets, ring shells. Characters: Genie.
- **V2:** stage ghost; actors genie (Genie circles the spire; half V1's fireworks, so bursts don't sit on him).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 5.9 Friend Like Me (finale)

- **Audio:** 554-563 s (9:14-9:23, 9 s) · **Video:** `--start 9:24 --end 9:33`
- **Our score now:** A huge gold willow barrage with roof fountains showering the castle. Characters: Genie.
- **V2:** stage castle; actors genie (he sings on to 563, round the full castle and its fountains).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

## 6. Love (audio 9:23-12:04, video 9:33-12:14)

### 6.1 Olaf: some people are worth melting for

- **Audio:** 563-576 s (9:23-9:36, 13 s) · **Video:** `--start 9:33 --end 9:46`
- **Our score now:** Spoken line; icy blue and purple castle, snowflakes floating up, one gold shell. Characters: Olaf.
- **V2:** stage ghost; actors olaf (Olaf pops up and waves in the snow).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 6.2 Love Is an Open Door

- **Audio:** 576-603 s (9:36-10:03, 27 s) · **Video:** `--start 9:46 --end 10:13`
- **Our score now:** Hearts and rose stained glass, ending royal blue and violet; gold fan comets, pink, violet and gold peonies. Characters: Anna, Hans.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 6.3 Can You Feel the Love Tonight

- **Audio:** 603-623 s (10:03-10:23, 20 s) · **Video:** `--start 10:13 --end 10:33`
- **Our score now:** Starry indigo; WALL-E and EVE among the constellations, then Simba and Nala; spaced gold, soft pink and violet. Characters: WALL-E, EVE, Simba, Nala.
- **V2:** stage off; actors walle (WALL-E floats across the stars).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 6.4 You'll Be in My Heart

- **Audio:** 623-637 s (10:23-10:37, 14 s) · **Video:** `--start 10:33 --end 10:47`
- **Our score now:** Magenta, lavender and gold; Tarzan and Kala, Dumbo and Mrs. Jumbo; pink, violet and white with comets from the terraces. Characters: Tarzan, Kala, Dumbo, Mrs. Jumbo.
- **V2:** stage ghost; actors dumbo (Dumbo flies across, flapping his ears).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 6.5 Princess garden

- **Audio:** 637-668 s (10:37-11:08, 31 s) · **Video:** `--start 10:47 --end 11:18`
- **Our score now:** Pink and rose stained-glass arches, flowers and waterfalls; gold brocade, pink peonies, gold palms. Characters: Cinderella, Prince Charming, Tiana, Naveen, Ariel, Eric, Belle, Beast.
- **V2:** stage ghost; actors princess_garden (four couples meet in turn, a heart floating up between each).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 6.6 I See the Light

- **Audio:** 668-697 s (11:08-11:37, 29 s) · **Video:** `--start 11:18 --end 11:47`
- **Our score now:** Midnight blue, orange lanterns drifting up; white and gold bursts, then red and gold. Characters: Rapunzel, Flynn.
- **V2:** stage ghost; actors lantern_boat (Rapunzel and Flynn's boat drifts in among the lanterns).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 6.7 I See the Light (lanterns)

- **Audio:** 697-724 s (11:37-12:04, 27 s) · **Video:** `--start 11:47 --end 12:14`
- **Our score now:** A quiet sky full of lanterns, sparse gold willows. Characters: Rapunzel, Flynn.
- **V2:** stage ghost; actors lantern_boat (she lets her own lantern go).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

## 7. Adversity (audio 12:04-14:09, video 12:14-14:20)

### 7.1 The Emperor's warning

- **Audio:** 724-742 s (12:04-12:22, 18 s) · **Video:** `--start 12:14 --end 12:32`
- **Our score now:** "The flower that blooms in adversity...", a gong; dark navy and crimson, low crimson and gold comets. Characters: Emperor of China.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 7.2 Villains attack

- **Audio:** 742-760 s (12:22-12:40, 18 s) · **Video:** `--start 12:32 --end 12:50`
- **Our score now:** Electric lime, toxic purple and blood red; crossing green searchlights, crackling green comets, red bursts. Characters: Ursula, Scar, Hades.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 7.3 To Die For

- **Audio:** 760-777 s (12:40-12:57, 17 s) · **Video:** `--start 12:50 --end 13:07`
- **Our score now:** Villains build; green dragon fire (the split from the attack is a guess: the video didn't show one). Characters: Maleficent, Jafar.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 7.4 He's a Pirate

- **Audio:** 777-806 s (12:57-13:26, 29 s) · **Video:** `--start 13:07 --end 13:36`
- **Our score now:** The castle cracks and burns; flame jets on the terraces; red, orange and gold. Characters: Pirates.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 7.5 He's a Pirate (green barrage)

- **Audio:** 806-812 s (13:26-13:32, 6 s) · **Video:** `--start 13:36 --end 13:43`
- **Our score now:** Emerald shells and lime comets. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 7.6 He's a Pirate (red and gold)

- **Audio:** 812-837 s (13:32-13:57, 25 s) · **Video:** `--start 13:43 --end 14:08`
- **Our score now:** Dense red chrysanthemums and gold willow fans. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 7.7 He's a Pirate (finale)

- **Audio:** 837-849 s (13:57-14:09, 12 s) · **Video:** `--start 14:08 --end 14:20`
- **Our score now:** A ruby-red and white perimeter finale, smoke. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

## 8. Triumph (audio 14:09-16:32, video 14:20-16:43)

### 8.1 Embers

- **Audio:** 849-889 s (14:09-14:49, 40 s) · **Video:** `--start 14:20 --end 15:00`
- **Our score now:** "Remember who you are": the castle near-black with an ember core, Mufasa in the clouds; no fireworks. Characters: Mufasa.
- **V2:** stage castle; actors mufasa (Mufasa's face fades in among the stars over the spire).

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 8.2 Go the Distance (the castle rebuilds)

- **Audio:** 889-915 s (14:49-15:15, 26 s) · **Video:** `--start 15:00 --end 15:26`
- **Our score now:** Cyan, royal blue and gold columns; Hercules in gold light; the keyhole glows; sky nearly dark. Characters: Hercules.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 8.3 Go the Distance

- **Audio:** 915-976 s (15:15-16:16, 61 s) · **Video:** `--start 15:26 --end 16:27`
- **Our score now:** Stained-glass hero windows in gold; gold and white willows and peonies, side comet plumes, rainbow comets. Characters: Hercules, Megara, Tarzan, Jane, Mulan, Merida.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 8.4 Go the Distance (gold canopy)

- **Audio:** 976-992 s (16:16-16:32, 16 s) · **Video:** `--start 16:27 --end 16:43`
- **Our score now:** Smiley and ring shells, green side comets, a gold willow canopy. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

## 9. Conclusion (audio 16:32-16:57, video 16:43-17:08)

### 9.1 Narrator closing

- **Audio:** 992-1017 s (16:32-16:57, 25 s) · **Video:** `--start 16:43 --end 17:08`
- **Our score now:** "Find your Happily Ever After": stained glass still lit, the keyhole glows, searchlights pan; no fireworks. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

## 10. Finale (audio 16:57-18:24, video 17:08-18:35)

### 10.1 Happily Ever After (reprise)

- **Audio:** 1017-1042.2 s (16:57-17:22, 25.200000000000045 s) · **Video:** `--start 17:08 --end 17:33`
- **Our score now:** Gold scrollwork, the keyhole beams; gold comets crossing over the spires, gold and white spotlights. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 10.2 You Can Fly

- **Audio:** 1042.2-1080 s (17:22-18:00, 37.799999999999955 s) · **Video:** `--start 17:33 --end 18:11`
- **Our score now:** Tink takes off from the spire; red, gold, green and cyan; gold palms, red strobes, lime and purple. Characters: Tinker Bell.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 10.3 You Can Fly (gold arcs)

- **Audio:** 1080-1087 s (18:00-18:07, 7 s) · **Video:** `--start 18:11 --end 18:18`
- **Our score now:** Gold comets arching over the spire. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 10.4 Final chorus, keyhole opens

- **Audio:** 1087-1099.6 s (18:07-18:19, 12.599999999999909 s) · **Video:** `--start 18:18 --end 18:30`
- **Our score now:** Castle gold and red; a rainbow barrage, then a white and gold mine fan from the castle's foot. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._

### 10.5 The last hit

- **Audio:** 1099.6-1104 s (18:19-18:24, 4.400000000000091 s) · **Video:** `--start 18:30 --end 18:35`
- **Our score now:** "After!": the white flash, then gold willows hanging over a castle washed in gold. Characters: none.

**Your notes for this scene:**

> _(add what to look for; sent after the base prompt)_

**Answers** (newest first):

_None yet._
