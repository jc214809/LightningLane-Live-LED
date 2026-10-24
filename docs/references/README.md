# Character references

Pixel-art and bead patterns to draw characters from. Read
[display/CHARACTERS.md](../../display/CHARACTERS.md) before drawing one, and copy a pattern cell for
cell where it fits.

**Fits as is** means the character can be copied cell for cell, one cell per LED, with no
shrinking or redrawing:
- **64x32:** at most 32 cells tall (and 64 wide).
- **64x64:** at most 64 cells tall and wide. A character at most 32 cells in both directions
  could also be doubled to 2x there.

Sizes are the character alone, measured from each pattern's grid, and are accurate to about a
cell. A scene that adds a prop under him (a board, a base, ground) needs those rows too: Stitch's
surfboard and wave take about 7 rows on 64x32. **Tight** means the character fills the board's
height, or within a row or two of it, so there's no room for anything under him.

**Adding an image:** every image here needs a row, and a test fails, naming the file, until it has
one. `python3 tools/analyze_reference.py <image>` finds the grid the way the sprite editor's
Pattern mode does and prints a draft row (size, fits, colours) to finish with who it shows; `--art`
also prints the sprite to paste. A sheet gets one row per character: measure each with
`--box x0,y0,x1,y1` (pixels of the image), adding `--lines` for art drawn over a picture. When detection finds no grid (stitching on fabric, a soft photo), `--cell <px>` reads it at a
cell size you give, as Pattern mode's Calibrate does: zoom in to count it, or sweep a few values and
keep the one where the size holds steady.

| Reference | Character | Size (cells, w x h) | 64x32 as is | 64x64 as is | On the board |
|---|---|---|---|---|---|
| [sitting_stitch.jpg](sitting_stitch.jpg) | Stitch, sitting | 26 x 25 | Yes | Yes (2x too) | `stitch_surf` on 64x32 ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [stitch.jpg](stitch.jpg) | Stitch, standing | 35 x 41 | No | Yes | `stitch_surf` on 64x64 ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Snow White (one of 24 on a sheet of princess and prince pairs) | 18 x 22 | Yes | Yes (2x too) | Pattern mode: box 64,68,192,228 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | The Prince (Snow White's) | 16 x 22 | Yes | Yes (2x too) | Pattern mode: box 212,68,324,228 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Jasmine | 21 x 23 | Yes | Yes (2x too) | Pattern mode: box 452,64,600,228 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Aladdin | 16 x 23 | Yes | Yes (2x too) | Pattern mode: box 628,64,744,228 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Pocahontas | 18 x 22 | Yes | Yes (2x too) | Pattern mode: box 868,68,996,228 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | John Smith | 16 x 23 | Yes | Yes (2x too) | Pattern mode: box 1024,64,1136,228 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Aurora | 22 x 24 | Yes | Yes (2x too) | Pattern mode: box 48,360,204,532 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Prince Phillip, feathered cap and cape | 20 x 23 | Yes | Yes (2x too) | Pattern mode: box 216,368,360,532 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Belle | 18 x 24 | Yes | Yes (2x too) | Pattern mode: box 444,360,572,532 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Beast | 23 x 27 | Yes | Yes (2x too) | Pattern mode: box 592,336,756,532 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Mulan, matchmaker makeup | 16 x 25 | Yes | Yes (2x too) | Pattern mode: box 880,352,996,532 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Li Shang | 16 x 23 | Yes | Yes (2x too) | Pattern mode: box 1024,364,1136,532 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Megara | 21 x 25 | Yes | Yes (2x too) | Pattern mode: box 48,648,200,828 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Hercules | 16 x 23 | Yes | Yes (2x too) | Pattern mode: box 216,664,332,828 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Ariel, mermaid tail | 28 x 24 | Yes | Yes (2x too) | Pattern mode: box 408,656,608,828 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Prince Eric | 16 x 22 | Yes | Yes (2x too) | Pattern mode: box 628,668,744,828 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Rapunzel with Pascal, hair trailing | 27 x 23 | Yes | Yes (2x too) | Pattern mode: box 812,664,1004,828 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Flynn Rider | 16 x 22 | Yes | Yes (2x too) | Pattern mode: box 1024,668,1136,828 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Moana | 19 x 20 | Yes | Yes (2x too) | Pattern mode: box 40,972,176,1116 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Maui | 22 x 27 | Yes | Yes (2x too) | Pattern mode: box 188,924,348,1116 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Tiana, lily-pad gown | 16 x 24 | Yes | Yes (2x too) | Pattern mode: box 472,944,588,1116 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Naveen as a frog | 13 x 13 | Yes | Yes (2x too) | Pattern mode: box 628,1024,720,1116 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Cinderella | 16 x 24 | Yes | Yes (2x too) | Pattern mode: box 860,944,976,1116 |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Prince Charming | 16 x 22 | Yes | Yes (2x too) | Pattern mode: box 1008,960,1124,1116 |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Gaston (one of eight on a photo of fused beads, about 6.2 px a bead) | 14 x 20 | Yes | Yes (2x too) | Pattern mode: box 110,60,204,196 |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Belle, blue village dress | 11 x 19 | Yes | Yes (2x too) | Pattern mode: box 210,78,286,198 |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Beast | about 14 x 20 | Yes | Yes (2x too) | Pattern mode: box 290,68,384,196; no grid found, size from the box: Calibrate |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Belle, gold gown ("Princess Belle" on the photo) | about 14 x 19 | Yes | Yes (2x too) | Pattern mode: box 384,74,474,198; no grid found, size from the box: Calibrate |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Chip | 13 x 14 | Yes | Yes (2x too) | Pattern mode: box 74,238,162,334 |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Mrs. Potts | 20 x 17 | Yes | Yes (2x too) | Pattern mode: box 163,224,292,334 |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Lumiere | 16 x 21 | Yes | Yes (2x too) | Pattern mode: box 290,204,392,334 |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Cogsworth | 15 x 20 | Yes | Yes (2x too) | Pattern mode: box 400,204,494,334 |
| [Dug.jpg](Dug.jpg) | Dug | 22 x 27 | Yes | Yes (2x too) | `kevin`, redrawn at 14 x 17 under his balloons |
| [Bullseye.jpg](Bullseye.jpg) | Woody (one of 20 on a Toy Story sheet, 7.15 px cells) | 12 x 28 | Yes | Yes (2x too) | Pattern mode: box 84,40,168,240 |
| [Bullseye.jpg](Bullseye.jpg) | Buzz Lightyear, wings out | 22 x 23 | Yes | Yes (2x too) | Pattern mode: box 180,76,336,240 |
| [Bullseye.jpg](Bullseye.jpg) | Mr. Potato Head | about 12 x 16 | Yes | Yes (2x too) | Box 356,124,444,240 finds no grid: size from its pixel extent; Calibrate |
| [Bullseye.jpg](Bullseye.jpg) | Slinky Dog, stretched | 21 x 15 | Yes | Yes (2x too) | Pattern mode: box 460,132,612,240 |
| [Bullseye.jpg](Bullseye.jpg) | Rex | 23 x 24 | Yes | Yes (2x too) | Pattern mode: box 636,68,800,240 |
| [Bullseye.jpg](Bullseye.jpg) | Hamm | 11 x 14 | Yes | Yes (2x too) | Pattern mode: box 816,140,896,240 |
| [Bullseye.jpg](Bullseye.jpg) | Bo Peep | 12 x 25 | Yes | Yes (2x too) | Pattern mode: box 84,308,168,484 |
| [Bullseye.jpg](Bullseye.jpg) | Bo Peep's sheep, three heads | 20 x 15 | Yes | Yes (2x too) | Pattern mode: box 172,376,316,484 |
| [Bullseye.jpg](Bullseye.jpg) | Green Army Men: one on a parachute over three standing | 15 x 28 | Yes | Yes (2x too) | Pattern mode: box 328,284,436,484 |
| [Bullseye.jpg](Bullseye.jpg) | A blue round toy with orange feet and a red fin, maybe Mr. Shark | about 12 x 8 | Yes | Yes (2x too) | Box 448,424,532,484 finds no grid: size from its pixel extent; Calibrate |
| [Bullseye.jpg](Bullseye.jpg) | A yellow can with red limbs, unidentified | 18 x 16 | Yes | Yes (2x too) | Pattern mode: box 536,368,668,484 |
| [Bullseye.jpg](Bullseye.jpg) | RC | 19 x 19 | Yes | Yes (2x too) | Pattern mode: box 672,348,808,484 |
| [Bullseye.jpg](Bullseye.jpg) | An Alien | about 11 x 15 | Yes | Yes (2x too) | Box 824,376,904,484 finds no grid: size from its pixel extent; Calibrate |
| [Bullseye.jpg](Bullseye.jpg) | Buzz Lightyear with a utility belt, wings out | 22 x 23 | Yes | Yes (2x too) | Pattern mode: box 32,572,192,736 |
| [Bullseye.jpg](Bullseye.jpg) | Zurg | 18 x 28 | Yes | Yes (2x too) | Pattern mode: box 196,536,324,736 |
| [Bullseye.jpg](Bullseye.jpg) | Mrs. Potato Head | 12 x 16 | Yes | Yes (2x too) | Pattern mode: box 340,620,428,736 |
| [Bullseye.jpg](Bullseye.jpg) | Wheezy | 12 x 14 | Yes | Yes (2x too) | Pattern mode: box 448,636,532,736 |
| [Bullseye.jpg](Bullseye.jpg) | Jessie | 16 x 27 | Yes | Yes (2x too) | Pattern mode: box 552,544,668,736 |
| [Bullseye.jpg](Bullseye.jpg) | Bullseye | 25 x 28 | Yes | Yes (2x too) | Pattern mode: box 676,536,856,736 |
| [Bullseye.jpg](Bullseye.jpg) | Stinky Pete | 12 x 24 | Yes | Yes (2x too) | Pattern mode: box 872,564,960,736 |
| [Forky.jpg](Forky.jpg) | Forky | 23 x 28 | Yes | Yes (2x too) | Built: `forky`, cell for cell, 1x on 64x32 and 2x on 64x64 |
| [hei-hei-small.jpg](hei-hei-small.jpg) | Heihei, small (brick pattern), with a leaf | 16 x 29 | Yes | Yes (2x too) | |
| [Mickey.jpg](Mickey.jpg) | Mickey Mouse, standing (chibi) | 23 x 29 | Yes | Yes (2x too) | |
| [Pluto.jpg](Pluto.jpg) | Pluto, crouching, side-on, tail up | 22 x 29 | Yes | Yes (2x too) | |
| [dwarfs.jpg](dwarfs.jpg) | Dopey (one of 7 on a dwarfs sheet; ignore its axis numbers, the cells are about 11.5 px) | 20 x 41 | No (9 rows over) | Yes | Pattern mode: box 228,92,472,562; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [dwarfs.jpg](dwarfs.jpg) | Happy, likely: yellow hat, orange coat | 18 x 41 | No (9 rows over) | Yes | Pattern mode: box 472,92,692,562; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [dwarfs.jpg](dwarfs.jpg) | Doc | 18 x 40 | No (8 rows over) | Yes | Pattern mode: box 692,95,908,562; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [dwarfs.jpg](dwarfs.jpg) | Bashful, likely: green hat, brown coat | 22 x 41 | No (9 rows over) | Yes | Pattern mode: box 912,88,1172,562; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [dwarfs.jpg](dwarfs.jpg) | Sneezy, likely: teal hat, yellow coat, finger under his nose | 23 x 35 | No (3 rows over) | Yes | Pattern mode: box 236,568,518,978; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [dwarfs.jpg](dwarfs.jpg) | Grumpy, likely: blue hat, arms crossed, frowning | 20 x 34 | No (2 rows over) | Yes | Pattern mode: box 528,575,802,978; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [dwarfs.jpg](dwarfs.jpg) | Sleepy, likely: red hat, scratching his head, eyes half shut | 25 x 35 | No (3 rows over) | Yes | Pattern mode: box 798,570,1092,978; Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [Tink.jpg](Tink.jpg) | Tinker Bell | 26 x 31 | Tight | Yes (2x too) | Built: `tink` |
| [Hamm.jpg](Hamm.jpg) | Hamm | 41 x 31 | Tight | Yes | |
| [Baby_Yoda.jpg](Baby_Yoda.jpg) | Grogu | 38 x 32 | Tight | Yes | |
| [mike.jpg](mike.jpg) | Mike Wazowski | 35 x 30 | Tight | Yes | Built: `mike` (drawn in code) |
| [Sulley.jpg](Sulley.jpg) | Sulley | 26 x 33 | No (1 row over) | Yes | |
| [Mike_waving.png](Mike_waving.png) | Mike Wazowski waving, with a toothy grin (the "PB" logo top left isn't part of him) | 33 x 30 | Yes | Yes | Pattern mode: drag a box round him, leaving out the logo. The show draws him shrunk to 27 x 25 (display/fireworks/actors/monsters.py) |
| [Ralph.jpg](Ralph.jpg) | Wreck-It Ralph | 25 x 34 | No (2 rows over, both outline) | Yes | `ralph`, from this pattern ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [Sally and Jack pair.png](<Sally and Jack pair.png>) | Sally leaning on Jack, one piece | 43 x 39 | No (shortened to 32 rows on the board) | Yes | `jack_sally`: the walk-in and kiss |
| [Zero.jpg](Zero.jpg) | Zero | 38 x 34 | No (2 rows over, both outline) | Yes | `jack_sally`, floating across |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Merida (one of 24 chibis on a sheet of princesses and villains; small, 3.7 px cells: boxes need padding, keep them as given) | 23 x 28 | Yes | Yes (2x too) | Pattern mode: box 22,34,146,176 (exactly: looser or tighter misreads) |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Ariel, mermaid tail | 21 x 31 | Tight | Yes (2x too) | Pattern mode: box 136,42,234,178 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Mulan | 17 x 28 | Yes | Yes (2x too) | Pattern mode: box 242,52,308,158 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Pocahontas | 22 x 28 | Yes | Yes (2x too) | Pattern mode: box 330,52,412,158 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Tiana, lily-pad gown | 17 x 31 | Tight | Yes (2x too) | Pattern mode: box 422,40,486,158 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Alice | 21 x 29 | Yes | Yes (2x too) | Pattern mode: box 506,48,586,158 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Elsa | 20 x 31 | Tight | Yes (2x too) | Pattern mode: box 42,180,130,310 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Anna | 17 x 28 | Yes | Yes (2x too) | Pattern mode: box 150,194,214,300 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Snow White | about 21 x 28 | Yes | Yes (2x too) | Pattern mode: box 236,194,314,300; no grid found, size from the box at 3.7 px cells: Calibrate |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Jasmine | 20 x 28 | Yes | Yes (2x too) | Pattern mode: box 332,194,408,300 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Rapunzel | 24 x 30 | Tight | Yes (2x too) | Pattern mode: box 418,194,510,308 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Tinker Bell | 17 x 32 | Tight | Yes (2x too) | Pattern mode: box 514,184,578,304 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Belle, blue village dress | 18 x 28 | Yes | Yes (2x too) | Pattern mode: box 52,336,120,442 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Belle, gold gown | 19 x 31 | Tight | Yes (2x too) | Pattern mode: box 140,320,224,448 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Cinderella, servant dress and kerchief | 19 x 28 | Yes | Yes (2x too) | Pattern mode: box 240,336,312,442 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Cinderella, ball gown | 19 x 32 | Tight | Yes (2x too) | Pattern mode: box 330,322,400,442 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Aurora as Briar Rose, peasant dress | about 19 x 28 | Yes | Yes (2x too) | Pattern mode: box 418,336,490,442; no grid found, size from the box at 3.7 px cells: Calibrate |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Aurora, pink gown | 19 x 28 | Yes | Yes (2x too) | Pattern mode: box 510,336,582,442 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Queen of Hearts | 19 x 31 | Tight | Yes (2x too) | Pattern mode: box 48,472,120,588 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Ursula | 27 x 31 | Tight | Yes (2x too) | Pattern mode: box 130,472,232,588 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Cruella de Vil | 19 x 32 | Tight | Yes (2x too) | Pattern mode: box 240,468,312,588 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Lady Tremaine | 19 x 30 | Tight | Yes (2x too) | Pattern mode: box 330,474,400,588 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | The Evil Queen | 21 x 31 | Tight | Yes (2x too) | Pattern mode: box 414,472,494,588 |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Maleficent, horns and staff | 25 x 35 | No (3 rows over) | Yes | Pattern mode: box 492,456,586,588 |
| [Green alien.jpg](<Green alien.jpg>) | Toy Story alien | 40 x 37 | No | Yes | |
| [bluey_beads.png](bluey_beads.png) | Bluey, arms out (photo of beads) | about 30 x 36 | No | Yes | Built: `keepy_uppy`, bead for bead on 64x64, redrawn 22 rows on 64x32 |
| [Pluto_sitting.jpg](Pluto_sitting.jpg) | Pluto, sitting, facing us | 27 x 36 | No (4 rows over) | Yes | |
| [Evil Queen.jpg](<Evil Queen.jpg>) | The Evil Queen | 31 x 38 | No | Yes | |
| [Kevin.jpg](Kevin.jpg) | Kevin, the bird from Up, standing | 18 x 38 | No (6 rows over) | Yes | Built: `kevin`, cell for cell, her neck 6 rows shorter on 64x32 |
| [bluey_bingo_grannies.png](bluey_bingo_grannies.png) | Bluey and Bingo as the Grannies, a pair (Bingo 26 x 31, Bluey 21 x 38) | about 50 x 38 | No | Yes | Built: `grannies`, cell for cell on 64x64, redrawn 24 rows on 64x32 |
| [pua.jpg](pua.jpg) | Pua | 36 x 39 | No | Yes | |
| [bingo.png](bingo.png) | Bingo, waving | about 40 x 54 | No | Yes (fills it) | Built: `keepy_uppy`, shrunk to 29 rows on 64x64, 20 on 64x32 |
| [Jack and sally.jpg](<Jack and sally.jpg>) | Jack and Sally with two pumpkins (photo of beads) | about 43 x 39 for the pair | No | Yes | |
| [Maleficent.jpg](Maleficent.jpg) | Maleficent | 29 x 40 | No | Yes | |
| [Brave.jpg](Brave.jpg) | Merida with her bow | 26 x 41 | No (9 rows over) | Yes | |
| [hei-hei.jpg](hei-hei.jpg) | Heihei | 20 x 42 | No | Yes | |
| [Boo.jpg](Boo.jpg) | Boo | 28 x 44 | No | Yes | |
| [Buzz.jpg](Buzz.jpg) | Buzz Lightyear | 40 x 46 | No | Yes | Built: `buzz` |
| [Jack Skellington.jpg](<Jack Skellington.jpg>) | Jack Skellington, head | 42 x 46 | No | Yes | |
| [Sally.jpg](Sally.jpg) | Sally, head | 42 x 47 | No | Yes | |
| [Oogie Boogie.jpg](<Oogie Boogie.jpg>) | Oogie Boogie | 44 x 50 | No | Yes | |
| [woody.jpg](woody.jpg) | Woody | 32 x 50 | No | Yes | |
| [jessie.jpg](jessie.jpg) | Jessie | 31 x 51 | No | Yes | |
| [Rex.jpg](Rex.jpg) | Rex | 61 x 51 | No | Yes | `rex` on 64x64 |
| [max-and-roxanne.png](max-and-roxanne.png) | Max and Roxanne | about 30 x 53 each | No | Yes | |
| [Goofy_small.jpg](Goofy_small.jpg) | Goofy, standing (chibi) | 30 x 53 | No | Yes | |
| [Pooh and Balloon.jpg](<Pooh and Balloon.jpg>) | Pooh with his balloon | 20 x 64 | No (passes through, part at a time) | Tight | `pooh`, from this pattern on both boards ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [Potato heads.jpg](<Potato heads.jpg>) | Mr. and Mrs. Potato Head | 65 x 40 together, about 32 x 40 each | No | One at a time | |
| [Tigger and Pooh.jpg](<Tigger and Pooh.jpg>) | Tigger and Pooh, one piece | 67 x 60 | No | No (3 columns too wide) | |
| [zero2.jpg](zero2.jpg) | Zero, flying (photo of embroidery) | about 68 x 72 | No | No | |
| [Tiana.jpg](Tiana.jpg) | Tiana kissing the frog | 74 x 86 | No | No | |
| [snow_white_stitched.png](snow_white_stitched.png) | Snow White (photo of finished stitching) | 53 x 103 | No | No | Redrawn at 21 wide: `mine_train`'s Snow White |
| [Pooh and gang.jpg](<Pooh and gang.jpg>) | Eeyore, Tigger, Pooh and Piglet, overlapping as one piece | 53 x 125 | No | No | |
| [RC-NotPixels.webp](RC-NotPixels.webp) | RC, from Toy Story (photo of an enamel pin, not pixel art) | | Needs tracing | Needs tracing | Trace it and keep the bold shapes, like the Falcon |
| [princesses.png](princesses.png) | (none: the image is completely transparent) | | | | |
| [simba_bricks.png](simba_bricks.png) | Young Simba, the Lion King logo pose (photo of a studded-brick build, about 8.5 degrees off straight, with a watermark) | about 27 x 25 | Yes | Yes (2x too) | Pattern mode reads it: Detect grid straightens it (`gridTurn`); a test holds it |
| [TS_beads.jpg](TS_beads.jpg) | Woody (one of 6 Toy Story pieces in fused beads, a photo, each on its own grid) | 11 x 13 | Yes | Yes (2x too) | Pattern mode: box 125,15,385,330; Detect grid reads it bead for bead. The editor's test holds 9 x 13 here, the tool 11 x 13 with the hat brim |
| [TS_beads.jpg](TS_beads.jpg) | Jessie | 11 x 13 | Yes | Yes (2x too) | Pattern mode: box 405,25,675,340 |
| [TS_beads.jpg](TS_beads.jpg) | An Alien | 11 x 14 | Yes | Yes (2x too) | Pattern mode: box 90,355,355,680; a test holds it |
| [TS_beads.jpg](TS_beads.jpg) | Buzz Lightyear (about 3 degrees off straight) | 10 x 12 | Yes | Yes (2x too) | Pattern mode: box 405,380,665,675 (straightened 3.1 degrees); a test holds it |
| [TS_beads.jpg](TS_beads.jpg) | Mrs. Potato Head | 11 x 14 | Yes | Yes (2x too) | Pattern mode: box 110,725,375,1060 |
| [TS_beads.jpg](TS_beads.jpg) | Mr. Potato Head | 11 x 14 | Yes | Yes (2x too) | Pattern mode: box 410,720,670,1060 |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Bunny (one of 11 on a Toy Story 4 sheet, each at its own scale over a sky, wall and floor) | 15 x 23 | Yes | Yes (2x too) | Pattern mode: box 15,25,190,285, Grid lines only; a test reads him |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Ducky | 13 x 18 | Yes | Yes (2x too) | Pattern mode: box 205,75,355,282, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Forky | 12 x 18 | Yes | Yes (2x too) | Pattern mode: box 385,80,530,288, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Duke Caboom | 13 x 24 | Yes | Yes (2x too) | Pattern mode: box 540,45,675,290, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Bo Peep, new outfit with cape | 14 x 23 | Yes | Yes (2x too) | Pattern mode: box 705,20,866,305, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Bo Peep, classic dress | 17 x 25 | Yes | Yes (2x too) | Pattern mode: box 885,22,1072,298, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | An Alien | 19 x 21 | Yes | Yes (2x too) | Pattern mode: box 5,325,212,560, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Buzz Lightyear | 21 x 26 | Yes | Yes (2x too) | Pattern mode: box 215,300,448,585, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Woody | 19 x 25 | Yes | Yes (2x too) | Pattern mode: box 435,295,665,590, Grid lines only; a test reads him from y 275, which adds two rows of sky (19 x 27) |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Gabby Gabby | 21 x 22 | Yes | Yes (2x too) | Pattern mode: box 650,312,910,582, Grid lines only |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Benson | 11 x 22 | Yes | Yes (2x too) | Pattern mode: box 918,305,1065,592, Grid lines only |
| [Aladdin with lamp.jpg](<Aladdin with lamp.jpg>) | Aladdin holding the lamp | 26 x 27 | Yes | Yes (2x too) | Pattern mode reads it |
| [genie.jpg](genie.jpg) | Genie rising from his lamp | 21 x 39 | No (7 rows over) | Yes | Built: `genie`, cell for cell: 7 rows dropped on 64x32, doubled on a 1x lamp (3 tail rows dropped) on 64x64 |
| [mickey_minnie_kiss.jpg](mickey_minnie_kiss.jpg) | Mickey and Minnie kissing, one piece (with the artist's initials at the bottom) | 50 x 34 | No (2 rows over) | Yes | Pattern mode reads it |
| [starwars.jpg](starwars.jpg) | R2-D2 (one of nine Star Wars charts on a sheet, each on its own grid) | 22 x 25 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | Yoda | 26 x 28 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | Princess Leia | 26 x 27 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | BB-8 | 19 x 27 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | A stormtrooper's helmet | 24 x 24 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | A Jedi in brown robes | 15 x 23 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | An Ewok | 13 x 18 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | Darth Maul's head | 25 x 29 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [starwars.jpg](starwars.jpg) | Darth Vader's helmet | 27 x 24 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [Runaway_Railway_mickey.jpeg](Runaway_Railway_mickey.jpeg) | Mickey pointing from a Runaway Railway car (photo of an enamel pin, not pixel art) | | Needs tracing | Needs tracing | Trace it and keep the bold shapes |
| [Runaway_Railway_goofy.jpeg](Runaway_Railway_goofy.jpeg) | Goofy driving the Runaway Railway engine (photo of an enamel pin, not pixel art) | | Needs tracing | Needs tracing | Trace it and keep the bold shapes |
| [Runaway_Railway_pluto.jpeg](Runaway_Railway_pluto.jpeg) | Pluto in a Runaway Railway car (photo of an enamel pin, not pixel art) | | Needs tracing | Needs tracing | Trace it and keep the bold shapes |
| [Buzz - New.jpg](<Buzz - New.jpg>) | Buzz Lightyear, a chibi (3D render of cubes over a sky and floor) | 15 x 25 | Yes | Yes (2x too) | Pattern mode: drag a box round him |
| [Woody - New.jpg](<Woody - New.jpg>) | Woody, a chibi (a chart with a colour count under it) | 19 x 26 | Yes | Yes (2x too) | Pattern mode: drag a box round him, above the colour count. Built: HEA V2's Woody (`toy_story.py` `WOODY_ART`) |
| [Vanellope kart.jpg](<Vanellope kart.jpg>) | Vanellope von Schweetz in her kart (pixel art, no grid lines) | 28 x 31 | Tight | Yes (2x too) | Pattern mode reads it |
| [Gamora.jpg](Gamora.jpg) | Gamora, a chibi | 19 x 28 | Yes | Yes (2x too) | Pattern mode reads it |
| [Groot.jpg](Groot.jpg) | Baby Groot, over a purple starry sky | about 25 x 39 | No (7 rows over) | Yes | Pattern mode reads it |
| [Rocket.jpg](Rocket.jpg) | Rocket, a chibi | 23 x 29 | Yes | Yes (2x too) | Pattern mode reads it |
| [Star-Lord.jpg](Star-Lord.jpg) | Star-Lord in his mask, a chibi | 19 x 29 | Yes | Yes (2x too) | Pattern mode reads it |
| [Thor.jpg](Thor.jpg) | Thor in his helmet with his hammer, a chibi | 24 x 26 | Yes | Yes (2x too) | Pattern mode reads it |
| [Darth Maul.jpg](<Darth Maul.jpg>) | Darth Maul, a chibi, his double lightsaber held diagonally across the whole chart | 36 x 35 with the saber (about 21 x 24 without) | No (3 rows over) | Yes | Pattern mode reads it |
| [Darth Vader.jpg](<Darth Vader.jpg>) | Darth Vader, a chibi with his lightsaber (soft, blurred pixel art, no grid lines) | 39 x 34 | No (2 rows over) | Yes | Pattern mode reads it; merge the blur's in-between shades |
| [Darth-Vader-2.jpg](Darth-Vader-2.jpg) | Darth Vader, a chibi with his lightsaber (pixel art, no grid lines) | 25 x 20 | Yes | Yes (2x too) | Pattern mode reads it |
| [Yoda-saber.jpg](Yoda-saber.jpg) | Yoda with his lightsaber (pixel art, no grid lines) | 32 x 21 | Yes | Yes (2x too) | Pattern mode reads it |
| [obiwan-saber.jpg](obiwan-saber.jpg) | Obi-Wan Kenobi with his lightsaber (pixel art, no grid lines) | 31 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [skywalker-saber.jpg](skywalker-saber.jpg) | Luke Skywalker with his lightsaber (pixel art, no grid lines) | 24 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [rey-saber.jpg](rey-saber.jpg) | Rey with her yellow lightsaber, by KidKinobi on DeviantArt (pixel art, no grid lines) | 23 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [kylo-saber.jpg](kylo-saber.jpg) | Kylo Ren with his crossguard lightsaber, by KidKinobi on DeviantArt (pixel art, no grid lines) | 25 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | BB-8 (one of thirteen Star Wars bead charts on one grid, 11 px beads) | 14 x 18 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | R2-D2 | 18 x 21 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Princess Leia, head only, tiny | 11 x 7 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Yoda, head only, tiny | 11 x 8 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | A stormtrooper's helmet with a pink bow | 15 x 17 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Darth Maul's head | 13 x 19 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Darth Vader with his lightsaber | 21 x 21 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Kylo Ren with his crossguard lightsaber | 20 x 25 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Luke Skywalker, head only, tiny | 9 x 8 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Han Solo, head only, tiny | 11 x 7 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | An Ewok, head only, tiny | 9 x 7 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | R2-D2, tiny | 9 x 6 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Star Wars.jpg](<many Star Wars.jpg>) | Chewbacca | 17 x 27 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [Villains.jpg](Villains.jpg) | The Evil Queen (one of six villainesses on a sheet, each on its own grid) | 31 x 37 | No (5 rows over) | Yes | Pattern mode: box 76,88,256,300 |
| [Villains.jpg](Villains.jpg) | Maleficent with her staff | 30 x 41 | No (9 rows over) | Yes | Pattern mode: box 276,68,448,300 |
| [Villains.jpg](Villains.jpg) | Lady Tremaine, the Stepmother | 22 x 35 | No (3 rows over) | Yes | Pattern mode: box 512,100,640,300 |
| [Villains.jpg](Villains.jpg) | Mother Gothel | 29 x 36 | No (4 rows over) | Yes | Pattern mode: box 84,388,252,592 |
| [Villains.jpg](Villains.jpg) | Ursula | 33 x 42 | No (10 rows over) | Yes | Pattern mode: box 280,352,468,592 |
| [Villains.jpg](Villains.jpg) | Cruella de Vil | 29 x 37 | No (5 rows over) | Yes | Pattern mode: box 500,380,664,592 |
| [Male villains.jpg](<Male villains.jpg>) | Jafar with his cobra staff (one of six villains on a sheet, same artist as Villains.jpg) | 30 x 41 | No (9 rows over) | Yes | Pattern mode: box 68,64,240,300 |
| [Male villains.jpg](<Male villains.jpg>) | Captain Hook | 30 x 41 | No (9 rows over) | Yes | Pattern mode: box 288,64,460,300 |
| [Male villains.jpg](<Male villains.jpg>) | Dr. Facilier | 25 x 39 | No (7 rows over) | Yes | Pattern mode: box 500,76,644,300 |
| [Male villains.jpg](<Male villains.jpg>) | Gaston | 25 x 35 | No (3 rows over) | Yes | Pattern mode: box 96,392,240,592 |
| [Male villains.jpg](<Male villains.jpg>) | Hades, flame hair | 31 x 42 | No (10 rows over) | Yes | Pattern mode: box 280,352,460,592 |
| [Male villains.jpg](<Male villains.jpg>) | Judge Frollo | 27 x 38 | No (6 rows over) | Yes | Pattern mode: box 500,372,652,592 |
| [Frozen.jpg](Frozen.jpg) | Elsa (same artist as Villains.jpg) | 20 x 33 | No (1 row over) | Yes | Pattern mode: box 12,112,236,480 |
| [Frozen.jpg](Frozen.jpg) | Olaf | 15 x 24 | Yes | Yes (2x too) | Pattern mode: box 236,212,404,480 |
| [Frozen.jpg](Frozen.jpg) | Anna in her cloak | 19 x 33 | No (1 row over) | Yes | Pattern mode: box 420,112,636,480 |
| [belle and beast.jpg](<belle and beast.jpg>) | Belle in her gold gown | 21 x 34 | No (2 rows over) | Yes | Pattern mode: box 36,44,240,372 |
| [belle and beast.jpg](<belle and beast.jpg>) | The Beast | 27 x 35 | No (3 rows over) | Yes | Pattern mode: box 296,32,556,372 |
| [Enchanted rose.jpg](<Enchanted rose.jpg>) | The enchanted rose under its glass | 21 x 41 | No (9 rows over) | Yes | Pattern mode reads it |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Snow White with her apple (one of nine on a gridded chart, a phone screenshot: the back button hides her top left) | 17 x 27 | Yes | Yes (2x too) | Pattern mode: box 95,85,215,285; redraw what the button covers |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Cinderella with her glass slipper | 21 x 27 | Yes | Yes (2x too) | Pattern mode: box 315,80,470,285 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Aurora with her crown | 21 x 27 | Yes | Yes (2x too) | Pattern mode: box 550,80,705,285 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Ariel with Flounder | 19 x 24 | Yes | Yes (2x too) | Pattern mode: box 75,315,215,515 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Belle with the rose | 19 x 27 | Yes | Yes (2x too) | Pattern mode: box 315,315,455,520 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Jasmine with the lamp | 18 x 25 | Yes | Yes (2x too) | Pattern mode: box 550,325,690,520 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Mulan with her sword | 15 x 25 | Yes | Yes (2x too) | Pattern mode: box 100,555,220,765 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Tinker Bell | 21 x 26 | Yes | Yes (2x too) | Pattern mode: box 305,555,465,765 |
| [Princesses with props.jpg](<Princesses with props.jpg>) | Elsa with a snowflake | 18 x 25 | Yes | Yes (2x too) | Pattern mode: box 555,555,695,765 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Ariel, mermaid tail (one of twelve on a gridded chart) | 24 x 32 | Tight | Yes (2x too) | Pattern mode: box 0,0,147,186 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Snow White | 18 x 30 | Tight | Yes (2x too) | Pattern mode: box 147,0,270,186 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Pocahontas | 23 x 32 | Tight | Yes (2x too) | Pattern mode: box 270,0,412,186 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Cinderella | 25 x 32 | Tight | Yes (2x too) | Pattern mode: box 412,0,564,186 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Belle | 25 x 36 | No (4 rows over) | Yes | Pattern mode: box 0,186,147,394 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Jasmine | 20 x 36 | No (4 rows over) | Yes | Pattern mode: box 147,186,270,394 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Elsa | 17 x 35 | No (3 rows over) | Yes | Pattern mode: box 270,186,412,394 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Tiana | 24 x 33 | No (1 row over) | Yes | Pattern mode: box 412,186,564,394 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Aurora | 25 x 44 | No (12 rows over) | Yes | Pattern mode: box 0,394,147,646 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Rapunzel | 19 x 38 | No (6 rows over) | Yes | Pattern mode: box 147,394,270,646 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Mulan | 24 x 44 | No (12 rows over) | Yes | Pattern mode: box 270,394,412,646 |
| [Detailed princesses.jpg](<Detailed princesses.jpg>) | Merida | 24 x 41 | No (9 rows over) | Yes | Pattern mode: box 412,394,564,646 |
| [Rapunzel with pan.jpg](<Rapunzel with pan.jpg>) | Rapunzel with her frying pan (a numbered 40 x 40 bead chart; size read off its axes) | 19 x 25 (29 x 25 with the pan) | Yes | Yes (2x too) | Detection misses the chart's grid: Pattern mode's Calibrate |
| [elsa.jpg](elsa.jpg) | Elsa with a snowflake (a numbered 40 x 40 bead chart; size read off its axes) | 15 x 25 (28 x 25 with the snowflake) | Yes | Yes (2x too) | Detection misses the chart's grid: Pattern mode's Calibrate |
| [Brave2.jpg](Brave2.jpg) | Merida with two arrows (a numbered 40 x 40 bead chart; size read off its axes) | 21 x 30 (30 x 30 with the arrows) | Tight | Yes (2x too) | Detection misses the chart's grid: Pattern mode's Calibrate |
| [Archer.png](Archer.png) | An archer with wild orange hair at full draw (the user's pixel art, a 64 x 64 canvas) | 36 x 54 (31 x 54 without its arrow) | No (22 rows over) | Yes (1x, 54 of 64 rows) | Built: `archer`, cell for cell less the arrow and string, which are drawn in code; 64x64 only |
| [Ursula.jpg](Ursula.jpg) | Ursula, tentacles spread | 37 x 38 | No (6 rows over) | Yes | Pattern mode reads it |
| [Scar.jpg](Scar.jpg) | Scar, a chibi (studded bricks) | 24 x 27 | Yes | Yes (2x too) | Pattern mode reads it |
| [Rafiki.jpg](Rafiki.jpg) | Rafiki with his staff (studded bricks) | 27 x 27 | Yes | Yes (2x too) | Pattern mode reads it |
| [Lion King.jpg](<Lion King.jpg>) | Pumbaa, Timon, Nala, Simba, Mufasa and Scar in a row (a product photo of a cross-stitch, too small to count) | | Needs tracing | Needs tracing | Each figure is about 40 px tall in the photo: find the full-size pattern, or redraw from it |
| [Nemo.jpg](Nemo.jpg) | Nemo | 34 x 24 | Yes | Yes | Pattern mode reads it |
| [Dory.jpg](Dory.jpg) | Dory | 29 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [Flounder.jpg](Flounder.jpg) | Flounder | 24 x 18 | Yes | Yes (2x too) | Pattern mode reads it |
| [Magic Mirror.jpg](<Magic Mirror.jpg>) | The Magic Mirror's face (Snow White) | 24 x 31 | Tight | Yes (2x too) | Pattern mode reads it |
| [Monsters_Inc.jpg](Monsters_Inc.jpg) | Sulley (one of 30 Monsters, Inc. characters on a sheet; looks AI-made, so its pixels aren't on a strict grid) | 18 x 25 | Yes | Yes (2x too) | Pattern mode: box 24,54,160,234; check cell by cell |
| [Monsters_Inc.jpg](Monsters_Inc.jpg) | Mike Wazowski | 18 x 20 | Yes | Yes (2x too) | Pattern mode: box 160,54,294,234 |
| [Monsters_Inc.jpg](Monsters_Inc.jpg) | Boo | 17 x 22 | Yes | Yes (2x too) | Pattern mode: box 294,78,426,234 |
| [Monsters_Inc.jpg](Monsters_Inc.jpg) | Randall | 16 x 25 | Yes | Yes (2x too) | Pattern mode: box 432,54,552,234 |
| [Monsters_Inc.jpg](Monsters_Inc.jpg) | Celia | 16 x 22 | Yes | Yes (2x too) | Pattern mode: box 36,420,156,582 |
| [Monsters_Inc.jpg](Monsters_Inc.jpg) | The other 25 monsters (background characters, a second Sulley top right) | about 16 x 25 each | Yes | Yes (2x too) | Pattern mode: drag a box round one |
| [inside_out.jpg](inside_out.jpg) | Anxiety (one of seven Inside Out emotions, watermarked) | 19 x 27 | Yes | Yes (2x too) | Pattern mode: box 60,104,140,220 |
| [inside_out.jpg](inside_out.jpg) | Embarrassment | 19 x 22 | Yes | Yes (2x too) | Pattern mode: box 156,112,248,220 |
| [inside_out.jpg](inside_out.jpg) | Anger | 16 x 24 | Yes | Yes (2x too) | Pattern mode: box 260,104,336,220 |
| [inside_out.jpg](inside_out.jpg) | Ennui | 16 x 28 | Yes | Yes (2x too) | Pattern mode: box 28,256,100,380 |
| [inside_out.jpg](inside_out.jpg) | Joy | 17 x 26 | Yes | Yes (2x too) | Pattern mode: box 104,252,188,376 |
| [inside_out.jpg](inside_out.jpg) | Disgust | 18 x 24 | Yes | Yes (2x too) | Pattern mode: box 192,256,280,376 |
| [inside_out.jpg](inside_out.jpg) | Sadness | 18 x 23 | Yes | Yes (2x too) | Pattern mode: box 288,260,376,376 |
| [nick and judy.jpg](<nick and judy.jpg>) | Nick Wilde (a phone screenshot of a watermarked bead chart) | 18 x 40 | No (8 rows over) | Yes | Pattern mode: box 44,200,362,906 |
| [nick and judy.jpg](<nick and judy.jpg>) | Judy Hopps | 15 x 33 | No (1 row over) | Yes | Pattern mode: box 352,318,625,906 |
| [WALL-E and EVE.jpg](<WALL-E and EVE.jpg>) | WALL-E with one arm raised (one of two on a pixel chart) | 23 x 26 | Yes | Yes (2x too) | Pattern mode: box 15,50,380,450 |
| [WALL-E and EVE.jpg](<WALL-E and EVE.jpg>) | EVE, happy eyes, with a red heart above and her shadow below (the heart alone 5 x 4) | 24 x 29 | Yes | Yes (2x too) | Pattern mode: box 360,5,730,450 |
| [Hiro and Baymax.jpg](<Hiro and Baymax.jpg>) | Hiro in his blue jacket (one of two in a photo of bead pieces, slightly tilted) | about 16 x 20 | Yes | Yes (2x too) | Pattern mode: box 110,125,300,345 (Detect grid straightens it; his count moves with the box) |
| [Hiro and Baymax.jpg](<Hiro and Baymax.jpg>) | Baymax, standing | 27 x 31 | Tight | Yes (2x too) | Pattern mode: box 295,0,570,335 (Detect grid straightens it) |
| [Mrs Jumbo.jpg](<Mrs Jumbo.jpg>) | Mrs. Jumbo, side-on in her blue blanket and pink headpiece (small watermarked bead photo) | about 40 x 38 | Needs tracing | Needs tracing | Beads too small to count (about 6 px); try Pattern mode's Calibrate |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Olaf, arms out (one of 12 on a pixel-art sheet of Frozen characters by @waseqazi) | 19 x 25 | Yes | Yes (2x too) | Pattern mode: box 210,98,296,220 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Elsa in her ice dress, making a snowflake | 15 x 27 | Yes | Yes (2x too) | Pattern mode: box 298,100,364,220 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Anna in her cloak | 12 x 27 | Yes | Yes (2x too) | Pattern mode: box 366,100,424,220 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Kristoff | 12 x 29 | Yes | Yes (2x too) | Pattern mode: box 426,94,478,220 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Sven with his harness | 28 x 30 | Tight | Yes (2x too) | Pattern mode: box 474,94,594,222 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Hans | 12 x 28 | Yes | Yes (2x too) | Pattern mode: box 134,286,190,412 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | The Duke of Weselton | 10 x 24 | Yes | Yes (2x too) | Pattern mode: box 194,306,246,412 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | The Duke's bodyguard (taller) | 14 x 30 | Tight | Yes (2x too) | Pattern mode: box 248,282,310,412 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | The Duke's bodyguard (shorter) | 12 x 28 | Yes | Yes (2x too) | Pattern mode: box 314,290,372,412 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Oaken in his sweater | 17 x 33 | No (1 row over) | Yes | Pattern mode: box 372,274,446,414 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | A troll | 11 x 14 | Yes | Yes (2x too) | Pattern mode: box 436,350,490,414 |
| [Frozen Group.jpg](<Frozen Group.jpg>) | Marshmallow, the snow monster | 43 x 43 | No (11 rows over) | Yes | Pattern mode: box 490,236,668,418 |
| [Detailed Nick and Judy.png](<Detailed Nick and Judy.png>) | Judy Hopps in uniform, hands on hips (a cleaner chart than nick and judy.jpg; feet clipped by the chart's edge) | 18 x 46 | No (14 rows over) | Yes | Pattern mode: box 270,670,540,1375 (the whole image reads a false tilt) |
| [Detailed Nick and Judy.png](<Detailed Nick and Judy.png>) | Nick Wilde with his tail out (an "Image ID" watermark over his feet) | 21 x 45 | No (13 rows over) | Yes | Pattern mode: box 545,675,885,1375 |
| [Flying Dumbo.jpg](<Flying Dumbo.jpg>) | Dumbo flying, ears spread, trunk up, in his hat and collar (marker on graph paper; his whole body and tail, which `dumbo`'s sprite lacks; feet cut by the photo's edge) | 47 x 28 | Yes | Yes | Pattern mode reads it |
| [Princes.jpg](Princes.jpg) | Snow White's prince (one of 11 princes standing in a row, a photo of a cross-stitch mockup on fabric: too soft to copy stitch for stitch, so clean up after reading) | 15 x 40 | No (8 rows over) | Yes | Pattern mode: box 14,222,58,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Prince Charming | 15 x 40 | No (8 rows over) | Yes | Pattern mode: box 62,222,108,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Prince Phillip, red cape | 15 x 40 | No (8 rows over) | Yes | Pattern mode: box 112,222,156,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Prince Eric | 15 x 40 | No (8 rows over) | Yes | Pattern mode: box 160,222,205,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Beast | 19 x 42 | No (10 rows over) | Yes | Pattern mode: box 210,222,265,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Aladdin | 16 x 41 | No (9 rows over) | Yes | Pattern mode: box 268,222,313,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | John Smith | 15 x 40 | No (8 rows over) | Yes | Pattern mode: box 318,222,361,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Li Shang | 15 x 42 | No (10 rows over) | Yes | Pattern mode: box 366,222,409,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Naveen | 18 x 41 | No (9 rows over) | Yes | Pattern mode: box 411,222,462,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Flynn Rider | 16 x 41 | No (9 rows over) | Yes | Pattern mode: box 462,222,508,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Princes.jpg](Princes.jpg) | Kristoff, probably (grey hat, dark coat with straps) | 14 x 42 | No (10 rows over) | Yes | Pattern mode: box 513,222,557,350; Calibrate to 2.6 px cells (`--cell 2.6 --no-turn`) |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | The gargoyles Victor, Hugo and Laverne, overlapping as one group (one of seven on a cross-stitch mockup, same artist as Princes.jpg) | 38 x 28 for the three (Victor 16 x 29) | Yes | Yes | Pattern mode: box 8,255,158,369 |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | Quasimodo | about 17 x 34 | No (2 rows over) | Yes | Pattern mode: box 160,234,232,369 misses the grid; Calibrate at 3.8 px a cell |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | Djali, the goat | 10 x 15 | Yes | Yes (2x too) | Pattern mode: box 233,303,278,369 |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | Esmeralda | 19 x 40 | No (8 rows over) | Yes | Pattern mode: box 275,208,347,370 |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | Phoebus | 15 x 40 | No (8 rows over) | Yes | Pattern mode: box 355,208,419,369 |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | Achilles, Phoebus's horse, facing us | 14 x 40 | No (8 rows over) | Yes | Pattern mode: box 428,212,483,370 |
| [Hunchback of Notre Dame.jpg](<Hunchback of Notre Dame.jpg>) | Frollo | 17 x 44 | No (12 rows over) | Yes | Pattern mode: box 490,197,561,370 |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Genie, floating (one of 12 on a pixel-art sheet of the Aladdin cast by @waseqazi, 6 px a cell) | about 18 x 20 | Yes | Yes (2x too) | Pattern mode: box 40,64,150,186 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | The Magic Carpet | about 8 x 8 | Yes | Yes (2x too) | Pattern mode: box 14,140,64,194 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Abu | about 6 x 6 | Yes | Yes (2x too) | Pattern mode: box 76,156,116,194 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Aladdin, standing | about 6 x 13 | Yes | Yes (2x too) | Pattern mode: box 112,112,154,194 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Jasmine | 6 x 12 | Yes | Yes (2x too) | Pattern mode: box 150,112,192,194 |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Rajah | 9 x 11 | Yes | Yes (2x too) | Pattern mode: box 186,130,240,196 |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Jafar with his snake staff | 13 x 17 | Yes | Yes (2x too) | Pattern mode: box 226,86,310,194 |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Iago, flying | about 8 x 6 | Yes | Yes (2x too) | Pattern mode: box 286,100,334,138 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | The Sultan | about 8 x 14 | Yes | Yes (2x too) | Pattern mode: box 322,104,370,194 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Prince Ali | about 6 x 15 | Yes | Yes (2x too) | Pattern mode: box 372,98,414,194 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Jafar disguised as the old prisoner | about 8 x 10 | Yes | Yes (2x too) | Pattern mode: box 414,128,470,194 misses the grid; Calibrate at 6 px a cell |
| [Aladdin Group.jpg](<Aladdin Group.jpg>) | Genie Jafar | 12 x 18 | Yes | Yes (2x too) | Pattern mode: box 468,76,550,194 |
| [Simba and Timon chart.jpg](<Simba and Timon chart.jpg>) | Young Simba walking right, tail up, eyes closed (a phone screenshot of a PDF baby-blanket chart, 6 px cells, a watermark over him) | 49 x 47 | No (15 rows over) | Yes | Pattern mode: box 328,732,630,1022 |
| [Simba and Timon chart.jpg](<Simba and Timon chart.jpg>) | Timon standing, holding a stick out to his side (stick included; a watermark over his arm) | 32 x 25 | Yes | Yes (2x too) | Pattern mode: box 218,1356,418,1514 |
| [Simba and Timon chart.jpg](<Simba and Timon chart.jpg>) | Pumbaa running, head up (only in the overview strip at the top; his full-size panel is cut off) | about 78 x 71 | No | No | Needs tracing: about 1.75 px a cell in the overview strip |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Marlin facing front (a scanned Italian cross-stitch magazine page, 6.1 px cells, about 1 degree off straight, with Italian name labels) | 37 x 25 | Yes | Yes | Pattern mode: box 56,60,284,215 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Dory facing right | 32 x 26 | Yes | Yes (2x too) | Pattern mode: box 304,52,504,220 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Nemo facing front | 34 x 23 | Yes | Yes | Pattern mode: box 500,70,712,212 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Gurgle, the purple-and-yellow tank fish (labelled "Pulce") | 25 x 24 | Yes | Yes (2x too) | Pattern mode: box 726,76,886,228 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Crush swimming (labelled "Scorza"; the label sits inside the box at the bottom right) | 44 x 34 | No (2 rows over) | Yes | Pattern mode: box 900,60,1168,276 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | A butterfly, the first of a 7-butterfly vine border | 16 x 17 | Yes | Yes (2x too) | Pattern mode: box 84,268,184,376 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Pooh with Piglet on his back and Tigger lying in front, one overlapping piece, with bees on a string | 87 x 73 | No | No (23 columns too wide, 9 rows too tall) | Pattern mode: box 28,404,568,840 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Dumbo standing in his hat and collar, the feather in his trunk | 49 x 62 | No (30 rows over) | Tight | Pattern mode: box 524,372,820,752 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Marie reaching down, tail up (top of the Aristocats stack; the three overlap, so clean up each one's neighbours after reading) | 39 x 39 | No (7 rows over) | Yes | Pattern mode: box 870,410,1112,650 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Toulouse crouching (middle of the stack) | 46 x 30 | Tight | Yes | Pattern mode: box 912,570,1190,752 |
| [Nemo Pooh Dumbo Aristocats.jpg](<Nemo Pooh Dumbo Aristocats.jpg>) | Berlioz lying on his front, batting a paint tube (bottom of the stack) | 40 x 25 | Yes | Yes | Pattern mode: box 905,705,1145,862 |
| [Wine and Dine 2026 medals.png](<Wine and Dine 2026 medals.png>) | Marie sitting in the 5K medal frame (runDisney Wine & Dine 2026 promo graphic, flat vector art, not pixels; the medal row is along the top) | | Needs tracing | Needs tracing | Box 48,55,108,125; redraw small, the 5K landmark's Marie |
| [Wine and Dine 2026 medals.png](<Wine and Dine 2026 medals.png>) | Panchito leaping, the 10K medal | | Needs tracing | Needs tracing | Box 112,50,180,130 |
| [Wine and Dine 2026 medals.png](<Wine and Dine 2026 medals.png>) | Penguin waiter, the half marathon (13.1) medal | | Needs tracing | Needs tracing | Box 330,50,395,130 |
| [Wine and Dine 2026 medals.png](<Wine and Dine 2026 medals.png>) | Grumpy, the Two Course Challenge (19.3) medal | | Needs tracing | Needs tracing | Box 398,50,465,130 |
| [Wine and Dine 2026 medals.png](<Wine and Dine 2026 medals.png>) | Marie, Berlioz and Toulouse stacked before the Eiffel Tower on purple, the 5K poster | | Needs tracing | Needs tracing | Box 35,145,125,265 |
| [Wine and Dine 2026 posters.png](<Wine and Dine 2026 posters.png>) | The 5K poster: Marie, Berlioz and Toulouse before the Eiffel Tower on purple (a sharper copy of the medals sheet's poster row) | | Needs tracing | Needs tracing | Box 0,0,210,236 |
| [Wine and Dine 2026 posters.png](<Wine and Dine 2026 posters.png>) | The 10K poster: José leaping, Donald in his sombrero and Panchito with his pistols up, over the EPCOT Mexico pyramid on magenta | | Needs tracing | Needs tracing | Box 211,0,422,236; the 10K landmark's three, hand-drawn from it |
| [Wine and Dine 2026 posters.png](<Wine and Dine 2026 posters.png>) | The half marathon poster: the Mary Poppins penguin waiters before Big Ben on blue | | Needs tracing | Needs tracing | Box 0,237,210,473 |
| [Wine and Dine 2026 posters.png](<Wine and Dine 2026 posters.png>) | The Two Course Challenge poster: Grumpy with a cuckoo clock on navy | | Needs tracing | Needs tracing | Box 211,237,422,473 |
| [Three Caballeros Panchito DuckTales 2017.png](<Three Caballeros Panchito DuckTales 2017.png>) | Panchito standing, huge sombrero behind him, hands at his belt (DuckTales 2017 render, Disney wiki; transparent background) | | Needs tracing | Needs tracing | The 10K landmark's Panchito: traced (alpha silhouette, colour vote keeping line art, palette-snapped) at 46 rows for 64x64 and 28 for 64x32, used as traced |
| [Three Caballeros Jose DuckTales 2017.png](<Three Caballeros Jose DuckTales 2017.png>) | José standing with his umbrella, boater and bow tie (DuckTales 2017 render, Disney wiki; transparent background) | | Needs tracing | Needs tracing | The 10K landmark's José: traced the same way at 34 rows for 64x64 and 20 for 64x32, used as traced |
| [Three Caballeros Donald classic render.png](<Three Caballeros Donald classic render.png>) | Donald waving, sailor shirt and cap (classic render, Disney wiki; transparent background) | | Needs tracing | Needs tracing | The 10K landmark's Donald: traced at 32 rows (64x64) and 20 (64x32); his cap swapped for a straw sombrero centred on his head, and his raised arm moved out clear of the brim |
| [Three Caballeros film trio in sombreros.png](<Three Caballeros film trio in sombreros.png>) | José, Panchito and Donald in matching cream sombreros, heads tilted, half-closed eyes (The Three Caballeros, 1944; a frame) | | Needs tracing | Needs tracing | Tried for heads in the film's look; not used |
| [Gran Fiesta Tour EPCOT poster.png](<Gran Fiesta Tour EPCOT poster.png>) | The three on the striped magic serape over the Mexico pavilion, flat poster style (EPCOT attraction poster) | | Needs tracing | Needs tracing | Tried for flat poster-style heads; the serape scene is an idea for later |
| [Jose Carioca pixel chart on graph paper.png](<Jose Carioca pixel chart on graph paper.png>) | José in a red cap, T-shirt and jeans, drawn cell by cell on graph paper (a photo) | 30 x 44 | No (12 rows over) | Yes | Pattern mode reads it (Detect grid straightens it); re-dressed in his classic outfit as a trial, not used |
| [Jose Carioca classic outfit sketches.png](<Jose Carioca classic outfit sketches.png>) | José's classic outfit from several angles: boater, pale yellow coat, bow tie, umbrella, green legs, colourful tail (fan sketches) | | Needs tracing | Needs tracing | The outfit for the chart José above |
| [Three Caballeros Donald Chain of Memories sprite.png](<Three Caballeros Donald Chain of Memories sprite.png>) | Donald in his sailor suit and cap (Kingdom Hearts: Chain of Memories GBA sprite, Kingdom Hearts wiki) | 29 x 39 | No (7 rows over) | Yes | Real pixel art, tried for the 10K landmark's Donald and not used (its shaded game style didn't match the others) |
| [Marie head and paws.png](<Marie head and paws.png>) | Marie, head and paws peeking over an edge (Pixilart, by HoldMyFlower; a screen capture) | 29 x 28 | Yes | Yes (2x too) | Pattern mode reads it; the Wine & Dine 5K landmark's Marie (pinks deepened for LEDs) |
| [Marie sitting on pink.png](<Marie sitting on pink.png>) | Marie sitting, head tilted, tail curled up, big neck bow (BraceletBook alpha #40355; a screen capture) | 31 x 32 | Tight | Yes (2x too) | Pattern mode reads it |
| [Marie tall seated outline.png](<Marie tall seated outline.png>) | Marie sitting tall, outline on white (BraceletBook alpha #20619; a screen capture) | 26 x 48 | No (16 rows over) | Yes | Pattern mode reads it; flood-fill the white outside her outline |
| [Marie walking.png](<Marie walking.png>) | Marie walking, side view, tail up (Pixilart, by MariLou82; a screen capture) | about 60 x 70 | No | No | Pose guide: redrawn 24 x 19 for the 5K's running Marie |
| [Dalmatian puppy face.jpg](<Dalmatian puppy face.jpg>) | A Dalmatian puppy (101 Dalmatians), face and front paws, red collar | 54 x 34 | No (2 rows over) | Yes | Pattern mode reads it (the 3 pieces it flags are an ear and spots) |
| [Dalmatian puppy with teddy bear.jpg](<Dalmatian puppy with teddy bear.jpg>) | A Dalmatian puppy walking with a teddy bear in its mouth, teal collar (a detailed cross-stitch chart) | 96 x 72 | No | No (32 columns too wide, 8 rows too tall) | Pattern mode: box 0,4,388,298; Calibrate to 4 px cells (detection misreads it) |
| [Simple Dalmatian puppy with teddy.jpg](<Simple Dalmatian puppy with teddy.jpg>) | The same puppy and teddy, a simpler chart with a red collar and border; the teddy runs off its left edge | 69 x 47 | No | No (5 columns too wide) | Pattern mode: box 0,18,300,224; Calibrate to 4.33 px cells |
| [Dalmatian puppies on leashes.jpg](<Dalmatian puppies on leashes.jpg>) | A spotted Dalmatian puppy on a pink leash, leading (one of 3 on a cross-stitch chart with backstitch outlines) | 37 x 36 | No (4 rows over) | Yes | Pattern mode: box 4,6,252,242; Calibrate to 6.5 px cells; the outlines are backstitch, trace them |
| [Dalmatian puppies on leashes.jpg](<Dalmatian puppies on leashes.jpg>) | A spotted Dalmatian puppy on a leash, middle | 28 x 34 | No (2 rows over) | Yes | Pattern mode: box 252,24,440,248; Calibrate to 6.5 px cells; trace the backstitch outlines |
| [Dalmatian puppies on leashes.jpg](<Dalmatian puppies on leashes.jpg>) | A pink-eared puppy on a leash, unspotted, at the back | 40 x 34 | No (2 rows over) | Yes | Pattern mode: box 436,28,702,252; Calibrate to 6.5 px cells; trace the backstitch outlines |
| [Dalmatian puppy border.jpg](<Dalmatian puppy border.jpg>) | A Dalmatian puppy head with a pink tongue, top (one of 4 tumbling heads on a vertical cross-stitch border strip with a thread key, blue backstitch outlines) | 26 x 27 | Yes | Yes (2x too) | Pattern mode: box 145,10,305,180; Calibrate to 6.19 px cells; trace the backstitch outlines |
| [Dalmatian puppy border.jpg](<Dalmatian puppy border.jpg>) | A puppy head with a blue collar, second | 35 x 26 | Yes | Yes | Pattern mode: box 145,155,365,320; Calibrate to 6.19 px cells; trace the backstitch outlines |
| [Dalmatian puppy border.jpg](<Dalmatian puppy border.jpg>) | A puppy head with a red open mouth, third | 30 x 27 | Yes | Yes (2x too) | Pattern mode: box 145,325,340,495; Calibrate to 6.19 px cells; trace the backstitch outlines |
| [Dalmatian puppy border.jpg](<Dalmatian puppy border.jpg>) | A puppy head with a blue collar and pink tongue, bottom | 31 x 32 | Tight | Yes (2x too) | Pattern mode: box 145,495,340,695; Calibrate to 6.19 px cells; trace the backstitch outlines |
| [Moana silhouette sunset bookmark.jpg](<Moana silhouette sunset bookmark.jpg>) | Moana in silhouette holding her oar, against a coral and orange sunset with a Te Fiti swirl above (a bookmark-shaped bead chart; the silhouette is the chart's near-black, which the LEDs show as off, so on a board she's the dark shape cut out of the sunset) | 30 x 105 | No (73 rows over) | No (41 rows too tall) | Pattern mode reads it |
| [Mufasa in the clouds film still.png](<Mufasa in the clouds film still.png>) | Mufasa's face in pink-gold clouds looking down at Kion (a Lion Guard film still, not a chart: the look the user wants for Embers, his whole head three-quarters left, soft and big) | not a grid | No | No | A look reference; draw from the cross-stitch or the Scar chart |
| [Scar face close-up chart.png](<Scar face close-up chart.png>) | Scar's face in close-up, three-quarters left: one green eye under a heavy brow, the nose bridge, muzzle and mouth, dark mane at the left (a bookmark-style chart, cropped on every side; the user likes its style for Mufasa) | 30 x 59 | No (27 rows over) | Yes | Pattern mode reads it |
| [Mufasa and Simba cross-stitch.png](<Mufasa and Simba cross-stitch.png>) | Mufasa sitting with young Simba under his paw, smiling, red mane, head three-quarters left (a cross-stitch chart image at 5 px cells) | 139 x 133 | No (75 columns too wide) | No (75 columns too wide, 69 rows too tall) | Pattern mode reads it; his head and mane are about the box 388,0,712,345 |
| [Lion face close-up brick stitch chart.png](<Lion face close-up brick stitch chart.png>) | A lion's face in close-up, three-quarters left (orange fur, cream muzzle, salmon nose, one eye; cropped on every side; a brick-stitch bead chart, so its columns are offset half a bead and the grid finder can't read it). Sampled down and recoloured as Mufasa for comparison | about 76 x 98 beads | No | No | Brick stitch: sample it down by colour (each board pixel takes its block's commonest bead colour) rather than read a grid |
| [Tiana chibi with crown.png](<Tiana chibi with crown.png>) | Tiana, a chibi in her lily-pad gown with a gold crown and pink cheeks (a single chart) | 19 x 32 | Tight | Yes (2x too) | Pattern mode reads it; the tool merges the gown's two pale greens into one |
| [Buzz flying 64x64 grid.png](<Buzz flying 64x64 grid.png>) | Buzz Lightyear flying to the right, fist out, wings back, legs trailing (an exact 64x64 LED grid with a hex palette under it) | 40 x 26 | Yes | Yes | Pattern mode: box 66,86,1346,1366 (the grid, 20 px cells). Built: HEA V2's Buzz (`toy_story.py` `BUZZ_ART`, mirrored to fly right to left) |
| [Tangled boat.jpg](<Tangled boat.jpg>) | The whole lantern scene from Tangled: Flynn and Rapunzel in their boat on dark water, the castle a dark silhouette behind them, a sky of floating lanterns (a 100 x 100 pixel-art picture at 16 px cells, lantern-orange on night purple) | 97 x 100 | No (33 columns too wide) | No (33 columns too wide, 36 rows too tall) | Pattern mode reads it. A `lantern_boat` actor already exists for HEA V2 (`display/fireworks/actors/lantern_boat.py`); this is a reference to redraw it from |
| [Tangled boat.jpg](<Tangled boat.jpg>) | Their boat with both of them in it: a dark curved rowboat with a lantern on a pole at the bow | 63 x 33 | No (1 row over) | Yes | Pattern mode: box 288,830,1300,1360 |
| [Tangled boat.jpg](<Tangled boat.jpg>) | Flynn and Rapunzel seated facing each other (green vest and brown hair; long gold braid with flowers), a lantern between their hands | 32 x 23 | Yes | Yes (2x too) | Pattern mode: box 560,830,1070,1200 |
