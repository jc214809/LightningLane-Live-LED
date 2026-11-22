# Transitions, characters and reference images

<!-- Moved from CLAUDE.md on 2026-11-12 so it loads only when needed. Keep it current with the code it describes. -->

Read before changing `display/animation/`, a character, the sprite editor or `docs/references/`. How to draw a character, and the lessons so far: `display/CHARACTERS.md`.

```sh
# Rebuild the sprite editor after changing any character art (a test fails until you do)
python3 tools/build_sprite_editor.py

# Measure a new reference image for docs/references/README.md (a test fails until it has a row)
python3 tools/analyze_reference.py docs/references/<image> [--box x0,y0,x1,y1] [--lines] [--cell PX] [--art]
```

- **Transitions** (`display/animation/`): `mechanics.py` has the kinds (`Wipe`, `FlyByReveal`, `PeekReveal`, `CapturesScreens`), `player.py` the playback, `characters/` one file per character (its class docstring says what it does), registered in `TRANSITIONS`. Who appears where is in `disney.py`: `PARK_REVEALS`, `SURPRISES` (ride screens, under 13% in all, held by a test) and `RIDE_VISITORS` (own rides only). A reveal longer than its screen sets `hold_after_s`; `run_frames`' `play_s` plays it in full even on a slow board (scenes step by frame, so they run in slow motion). `animation.X` re-exports everything. `config.json`'s `force_surprise` plays one on every ride screen, for checking on a board.
- **Characters:** read `display/CHARACTERS.md` before adding or reworking one; planned work is in `ROADMAP.md`. Add one with a file under `characters/` and a line in `TRANSITIONS`. `tools/sprite_editor.html` edits every sprite and palette (and landmark art a module lists in `EDITOR_SPRITES`) and turns pattern charts and bead photos into pixels, chosen or pasted (detection is pure JS in its `core` script, tested under Node); a sprite drawn at a fixed size on both boards declares `SCALE` or `<NAME>_SCALE` so the editor previews it right.
- **References** (`docs/references/`): every image needs a README row (one per character on a sheet), held by `tests/tools/test_analyze_reference.py`. `tools/analyze_reference.py` drafts it with the editor's Pattern-mode core under Node; the SessionStart hook in `.claude/settings.json` (checked in; personal permissions go in the ignored `settings.local.json`) lists images with no row.

## Rules

- A transition that takes the old screen (`wants_prev`) must paint every pixel of it, black included: `show_screen` has already drawn the new screen underneath, and it bleeds through otherwise. Add each new one to `test_new_screen_never_shows_through_the_old_screens_dark_pixels`.
- Every character transition logs its achieved fps; `journalctl -u LightningLane-Live-LED.service -f` shows a board's real speed.

## Tests

- Animation tests mirror the package (`tests/display/animation/`, one file per module or character); shared fakes (`FakeCanvas`, `FakeMatrix`, …) in `support.py`; its `conftest.py` stubs `graphics` by patching `animation.drawing`. Landmark tests do the same in `tests/display/landmarks/`.
