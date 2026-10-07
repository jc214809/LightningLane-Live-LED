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
`--box x0,y0,x1,y1` (pixels of the image), adding `--lines` for art drawn over a picture.

| Reference | Character | Size (cells, w x h) | 64x32 as is | 64x64 as is | On the board |
|---|---|---|---|---|---|
| [sitting_stitch.jpg](sitting_stitch.jpg) | Stitch, sitting | 26 x 25 | Yes | Yes (2x too) | `stitch_surf` on 64x32 ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [stitch.jpg](stitch.jpg) | Stitch, standing | 35 x 41 | No | Yes | `stitch_surf` on 64x64 ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [princesses_and_Princes.jpg](princesses_and_Princes.jpg) | Princesses and princes, a sheet | about 16 x 22 each | Yes | Yes (2x too) | |
| [Beauty and the Beast.jpg](<Beauty and the Beast.jpg>) | Gaston, Belle, Beast, Chip, Mrs. Potts, Lumiere, Cogsworth (photo of beads) | about 12 x 20 each | Yes | Yes (2x too) | |
| [Dug.jpg](Dug.jpg) | Dug | 22 x 27 | Yes | Yes (2x too) | `kevin`, redrawn at 14 x 17 under his balloons |
| [Bullseye.jpg](Bullseye.jpg) | Toy Story, a sheet: Woody, Buzz, Mr. and Mrs. Potato Head, Slinky, Rex, Hamm, Bo Peep and her sheep, Forky, the Aliens, RC, Zurg, Wheezy, Jessie, Bullseye, Stinky Pete and more | up to about 26 x 28 each (Bullseye 26 x 28) | Yes | Yes (2x too) | |
| [Forky.jpg](Forky.jpg) | Forky | 23 x 28 | Yes | Yes (2x too) | Built: `forky`, cell for cell, 1x on 64x32 and 2x on 64x64 |
| [hie-hie-small.jpg](hie-hie-small.jpg) | Heihei, small (brick pattern), with a leaf | 16 x 29 | Yes | Yes (2x too) | |
| [dwarfs.jpg](dwarfs.jpg) | The seven dwarfs, a sheet | about 20 x 40 each | No (hat to beard, in the mine car) | Yes | Built: `mine_train`, cell for cell, shoulders up on 64x64 |
| [Tink.jpg](Tink.jpg) | Tinker Bell | 26 x 31 | Tight | Yes (2x too) | Built: `tink` |
| [Hamm.jpg](Hamm.jpg) | Hamm | 41 x 31 | Tight | Yes | |
| [Baby_Yoda.jpg](Baby_Yoda.jpg) | Grogu | 38 x 32 | Tight | Yes | |
| [mike.jpg](mike.jpg) | Mike Wazowski | 35 x 30 | Tight | Yes | Built: `mike` (drawn in code) |
| [Sulley.jpg](Sulley.jpg) | Sulley | 26 x 33 | No (1 row over) | Yes | |
| [Ralph.jpg](Ralph.jpg) | Wreck-It Ralph | 25 x 34 | No (2 rows over, both outline) | Yes | `ralph`, from this pattern ([CHARACTERS.md](../../display/CHARACTERS.md#scorecard)) |
| [Sally and Jack pair.png](<Sally and Jack pair.png>) | Sally leaning on Jack, one piece | 43 x 39 | No (shortened to 32 rows on the board) | Yes | `jack_sally`: the walk-in and kiss |
| [Zero.jpg](Zero.jpg) | Zero | 38 x 34 | No (2 rows over, both outline) | Yes | `jack_sally`, floating across |
| [Princesses_and_Evil_Ladies.jpg](Princesses_and_Evil_Ladies.jpg) | Princesses and villains, a sheet | about 25 x 35 each | No | Yes | |
| [Green alien.jpg](<Green alien.jpg>) | Toy Story alien | 40 x 37 | No | Yes | |
| [bluey_beads.png](bluey_beads.png) | Bluey, arms out (photo of beads) | about 30 x 36 | No | Yes | Built: `keepy_uppy`, bead for bead on 64x64, redrawn 22 rows on 64x32 |
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
| [TS_beads.jpg](TS_beads.jpg) | Toy Story in fused beads: Woody, Jessie, an Alien, Buzz, Mrs. and Mr. Potato Head (photo, each piece on its own grid, Buzz about 3 degrees off) | about 9 x 13 to 11 x 14 each | Yes | Yes (2x too) | Pattern mode: drag a box round one; Detect grid reads it bead for bead, and a test holds Woody, the Alien and Buzz |
| [toy_story_4_sheet.png](toy_story_4_sheet.png) | Toy Story 4, a sheet: Bunny, Ducky, Forky, Duke Caboom, Bo Peep in two outfits, an Alien, Buzz, Woody, Gabby Gabby and Benson, each scaled its own way, over a sky, wall and floor | about 15 x 23 to 21 x 27 each (Bunny 15 x 23, Woody 19 x 27) | Yes | Yes | Pattern mode: drag a box round one, tick Grid lines only; a test reads Bunny and Woody |
| [aladin.jpg](aladin.jpg) | Aladdin holding the lamp | 26 x 27 | Yes | Yes (2x too) | Pattern mode reads it |
| [genie.jpg](genie.jpg) | Genie rising from his lamp | 21 x 39 | No (7 rows over) | Yes | Pattern mode reads it |
| [lion king bead.jpeg](<lion king bead.jpeg>) | Young Simba in the Lion King logo pose (photo of a studded-brick build, the same as simba_bricks.png, about 9 degrees off straight, with a watermark) | about 27 x 29 | Yes | Yes (2x too) | Pattern mode: drag a box above the watermark; Detect grid straightens it |
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
| [Woody - New.jpg](<Woody - New.jpg>) | Woody, a chibi (a chart with a colour count under it) | 19 x 26 | Yes | Yes (2x too) | Pattern mode: drag a box round him, above the colour count |
| [Vanellope Von - Car.jpg](<Vanellope Von - Car.jpg>) | Vanellope von Schweetz in her kart (pixel art, no grid lines) | 28 x 31 | Tight | Yes (2x too) | Pattern mode reads it |
| [Gamora.jpg](Gamora.jpg) | Gamora, a chibi | 19 x 28 | Yes | Yes (2x too) | Pattern mode reads it |
| [Groot.jpg](Groot.jpg) | Baby Groot, over a purple starry sky | about 25 x 39 | No (7 rows over) | Yes | Pattern mode reads it |
| [Rocket.jpg](Rocket.jpg) | Rocket, a chibi | 23 x 29 | Yes | Yes (2x too) | Pattern mode reads it |
| [Starlod.jpg](Starlod.jpg) | Star-Lord in his mask, a chibi | 19 x 29 | Yes | Yes (2x too) | Pattern mode reads it |
| [Thor.jpg](Thor.jpg) | Thor in his helmet with his hammer, a chibi | 24 x 26 | Yes | Yes (2x too) | Pattern mode reads it |
| [Darth Mal.jpg](<Darth Mal.jpg>) | Darth Maul, a chibi, his double lightsaber held diagonally across the whole chart | 36 x 35 with the saber (about 21 x 24 without) | No (3 rows over) | Yes | Pattern mode reads it |
| [Darth Vader.jpg](<Darth Vader.jpg>) | Darth Vader, a chibi with his lightsaber (soft, blurred pixel art, no grid lines) | 39 x 34 | No (2 rows over) | Yes | Pattern mode reads it; merge the blur's in-between shades |
| [Darth-Vader-2.jpg](Darth-Vader-2.jpg) | Darth Vader, a chibi with his lightsaber (pixel art, no grid lines) | 25 x 20 | Yes | Yes (2x too) | Pattern mode reads it |
| [Yoda-saber.jpg](Yoda-saber.jpg) | Yoda with his lightsaber (pixel art, no grid lines) | 32 x 21 | Yes | Yes (2x too) | Pattern mode reads it |
| [hans- solo.jpg](<hans- solo.jpg>) | Obi-Wan Kenobi with his lightsaber, despite the file name (pixel art, no grid lines) | 31 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [skywalker-saber.jpg](skywalker-saber.jpg) | Luke Skywalker with his lightsaber (pixel art, no grid lines) | 24 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [rey-saber.jpg](rey-saber.jpg) | Rey with her yellow lightsaber, by KidKinobi on DeviantArt (pixel art, no grid lines) | 23 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [kylo-saber.jpg](kylo-saber.jpg) | Kylo Ren with his crossguard lightsaber, by KidKinobi on DeviantArt (pixel art, no grid lines) | 25 x 24 | Yes | Yes (2x too) | Pattern mode reads it |
| [many Starwars .jpg](<many Starwars .jpg>) | BB-8 (one of thirteen Star Wars bead charts on one grid, 11 px beads) | 14 x 18 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | R2-D2 | 18 x 21 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Princess Leia, head only, tiny | 11 x 7 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Yoda, head only, tiny | 11 x 8 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | A stormtrooper's helmet with a pink bow | 15 x 17 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Darth Maul's head | 13 x 19 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Darth Vader with his lightsaber | 21 x 21 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Kylo Ren with his crossguard lightsaber | 20 x 25 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Luke Skywalker, head only, tiny | 9 x 8 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Han Solo, head only, tiny | 11 x 7 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | An Ewok, head only, tiny | 9 x 7 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | R2-D2, tiny | 9 x 6 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
| [many Starwars .jpg](<many Starwars .jpg>) | Chewbacca | 17 x 27 | Yes | Yes (2x too) | Pattern mode: drag a box round it |
