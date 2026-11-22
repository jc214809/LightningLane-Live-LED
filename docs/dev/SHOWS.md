# Fireworks and synced shows

<!-- Moved from CLAUDE.md on 2026-11-12 so it loads only when needed. Keep it current with the code it describes. -->

Read before changing `display/fireworks/`, a show's score or V2 overlay, `show_actors.py`, or the show tools. What the real show does: `docs/shows/<clip_name>/README.md`.

```sh
# Rebake Merida's Touch the Sky poses after changing merida_poses.py or the archer's art (a test fails until you do)
python3 tools/build_merida_poses.py

# Record the synced show as the boards draw it, then compare it with the real show in tools/show_sync_checker.html
python3 tools/render_show.py [--recording] [--version v2]

# Loop part of the synced show live in the emulator, with its music (audio seconds; run from a folder whose emulator_config.json sets the port)
python3 tools/loop_show.py 0 98 [--rows 64] [--sound] [--version v1]

# Lip-sync a singing show character (demucs in its own venv: install lines atop the tool)
python3 tools/lip_sync.py genie 525 565 --model htdemucs --close 549.82 --mute 542.6-545.0 --mute 553.7-559.7   # --close: an m inside a held note; --mute FROM-TO: someone else sings (the backup singers, per the lyric sheet)
python3 tools/lip_sync.py merida 268 276.3 --model htdemucs
python3 tools/lip_sync.py mufasa 849 889 --close 869.97 --close 871.70 --close 877.88 --close 882.3 --close 882.75 --from-mix 881.95-883.4   # --from-mix: his echoing last "Remember"
```

- Fireworks: the castle is `_CASTLE_ART`, doubled on 64-row boards; `_BIG_CASTLE_ROW_PATCH` adjusts only the doubled one.
- Synced shows: a show with a score in `display/fireworks/shows/<clip_name>.json` plays whole, in time with its music, through `display/fireworks/music_show.py` (its own copy of the fireworks simulation, so the everyday ones don't change; `score.py` reads the file). Scene looks are one class each in the `display/fireworks/effects/` package (modules by kind of look: `base`, `searchlights`, `castle`, `comets`, `particles`, `sky`), turned on by name in a scene's `effects`; add one in the module that fits and in `EFFECTS` (`effects/__init__.py`). `show_effects.py` only re-exports them for old imports. A single firework at a set moment (a rooftop fan, one shell, one comet) is a scene's `hits` (`score.Hit`), not an effect. A look change mid-scene is its `castle_changes` (show seconds); a V2 stage change mid-scene is the overlay's `stage_changes` (seconds into the scene). What the real show does (timeline, colours, where ours is off) is in `docs/shows/<clip_name>/README.md`; start there for improvements. To study the real show further, `docs/shows/happily-ever-after/WATCH.md` has a `/watch` section per scene: "watch scene 4.3" means `bash docs/shows/happily-ever-after/watch-scenes.sh 4.3` (it builds the question, runs the skill on that scene's video window, and saves the answer under it, newest first). `music_show.py` holds the simulation (`MusicShow.step` is named steps: launch, rockets, sparks, lanterns, embers, dust; `frame_pixels` draws each layer over the last, sky then castle then effects, Tink, actors, white flash); the layer drawing methods and the castle's colour constants live in `music_show_layers.py` (`FrameLayers`, the base of `MusicShow`, which re-exports the constants). Every `rng` call must stay in the same order and count, and `tools/frame_hashes.py` shows whether a refactor moved a pixel. It follows the clock, not frames, so a slow board stays with the music. `render_music_show` logs each scene's fps, where the slowest frame's time went (build/push), late frames, pixel count, show-thread vs process CPU and the board's load/temperature/clock/throttle flags (`utils/system_stats.py`): `journalctl -u LightningLane-Live-LED.service | grep log_scene` after a run says why a scene dipped. To check a change against the real show, re-run `tools/render_show.py` and open `tools/show_sync_checker.html` (recording and render side by side, scene marks to paste back).
- Show versions: V2 (a `config.json` `shows` entry's `version`) is an overlay, `shows/<clip_name>.v2.json`, adding a `stage` (`castle`/`ghost`/`off`: the castle dims or goes) and `actors` to V1 scenes by title (`effects` replaces a scene's, when an actor redraws one); a bad or missing overlay plays V1. Characters are one class each in `show_actors.py` (registered in `ACTORS`), placed by the clock; one who sings reads its mouth track (`score.Lips`, from `<clip_name>.v2.lips.json`, made by `tools/lip_sync.py` from demucs-split vocals; a bad file only stills the mouths). Plan and progress: `docs/shows/happily-ever-after/V2-PLAN.md`. Render with `--version v2` and open the checker with `?show=<clip_name>.v2`; serve it over http with Range support (`npx http-server`), or the videos won't seek.
