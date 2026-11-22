# The display loop, screens, landmarks and badges

<!-- Moved from CLAUDE.md on 2026-11-12 so it loads only when needed. Keep it current with the code it describes. -->

Read before changing `disney.py`'s loop or `display/` outside characters (`docs/dev/CHARACTERS.md`) and shows (`docs/dev/SHOWS.md`).

## Main thread

- **Main thread** (`disney.py`): castle fireworks intro (`display/fireworks/fireworks.py`) → optional trip countdown → per operating park: landmark → park title → ride screens, forever. `play_fireworks_show_if_due` cuts in before any screen with the castle fireworks for `FIREWORKS_SHOW_S` after tonight's show starts (`utils/special_events.py:fireworks_show()`, live showtimes via `parks/live.py:show_start_due`), once per performance.

## Display layer

- **Fonts:** loaded once by `display/display.py:initialize_fonts()` into `loaded_fonts`, keyed by board height (32 or 64); sizes and paths differ per board.
- **Shared helpers:** `display/motion.py` (`ease_out`, `smooth`, `progress`, `ramp`) and `display/pixels.py` (`put`/`set_pixel` with bounds check, `paint`, `blend`, `art_pixels`, `rotate_art`, `noise`). Use these before writing another copy.
- **Screens:** every screen after the intro plays through `display/animation/player.py:show_screen(matrix, draw, hold_s, transition)`. It sweeps the old screen away, reveals the new one with the transition, then calls `draw(canvas, t)` each frame until it returns False.
- **Landmarks** (`display/landmarks/`, one file each, `Landmark` base in `scene.py`): play before each park title for their `SCREEN_S`, matched loosely on the park name by `landmark_for()`; a party can swap in its own (`active_party()`), and a date can too (`utils/special_events.py` `DATED_LANDMARKS`, by the park's local date: race days the park data never names; it wins over a party; an entry listing several picks one at random each showing). `PLAYS_UNDER_WIPE` landmarks keep animating while the wipe uncovers them. A landmark too big for one file splits into sibling modules, not a package, the landmark class staying in the original and re-exporting what tests and tools read from it: the Santa train is `santa_train.py` (the class) with `santa_train_art.py` (palette, who rides where, Santa's wave), `santa_train_cars_64.py`/`_32.py` (the pieces' art), `santa_train_riders.py` (poses), `santa_train_wheels.py` and `santa_train_sign.py`. Only `santa_train.py` lists `EDITOR_SPRITES` (the sprite editor imports every `display/landmarks/` module).
- **Ride screen** (`display/attractions/attraction_info.py`): long names scroll; the wait drops into spare rows (`wait_drop`); DOWN rides pulse red with a full bar. It draws 2px word spaces (`SPACE_PX`): wrap, measure and draw text through `wrap_text`/`get_text_width`/`draw_text` with `space_px` so all three agree.
- **Network badge:** `present()` stamps a red "!" (`display/network.py`) while `updater/shared.py:network_issues()` is set, driven by `note_network_result()`. Tests reset the flag in the root `conftest.py`.
- **Sound badges:** `present()` also stamps one bottom-left (`display/sound_badges.py`) while sound is enabled and `utils/sound.py:current_problem()` finds one, a 9x9 red square like the network one: a white note and X when a show has no clip in `sounds/`, a white speaker and X when there's no player or no ALSA card for `sound.device` (`/proc/asound/cards`; that one wins). Always on, quiet hours too, so it's fixed before the show. `main()` calls `watch()` with every `known_shows()`; the check reruns at most once a minute and logs only changes.

## Proving a display change changed nothing

`python3 tools/frame_hashes.py --out /tmp/before.json` on the base branch, then `--out /tmp/after.json --compare /tmp/before.json` after your change: it renders every landmark, transition, fireworks theme, synced show (V1 and V2, every frame) and the park-info, ride and countdown screens at 64x32 and 64x64, deterministically, and must report `0 differences` (`--only <substring>` runs a subset; about 80 s in all). A new landmark, transition, theme or show is picked up by itself, and a reveal's random `STORIES` are each hashed pinned (`transition/luxo_ball-bat`); any other random choice the seeded run can't reach (check with `coverage run tools/frame_hashes.py`) needs its own pinning test, and a new kind of screen needs a fixture in the tool. Hashes depend on the interpreter and library versions: run before and after with the same Python. Details: `docs/dev/CODE-QUALITY.md`.

## Display rules

The rules every screen follows (cheap, side-effect-free draws; one canvas via `frame_canvas()`/`present()`) stay in CLAUDE.md.

- Call `forget_screen()` after anything that bypasses `show_screen`, so the next sweep doesn't redraw a stale screen.
- `over_screen` transitions play over a finished screen and let it keep animating underneath.
