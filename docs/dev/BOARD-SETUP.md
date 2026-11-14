# Boards: setup, install, Wi-Fi and the driver

<!-- Moved from CLAUDE.md on 2026-11-12 so it loads only when needed. Keep it current with the code it describes. -->

Read before changing `board-setup.sh`, `LLL-install.sh`, `driver/`, `cli.py`, the Wi-Fi setup screen or `requirements.txt` caps. Wiring and parts: `docs/hardware/`.

```sh
# Set up a whole board (LLL, Peloton-LED or MLB): see what it would do without changing anything
bash board-setup.sh --dry-run --answers board.txt   # KEY=value lines; --help lists them

# Redraw docs/hardware's wiring diagrams after editing tools/draw_wiring.py (a test fails until you do)
python3 tools/draw_wiring.py
```

## Wi-Fi setup screen

- **Wi-Fi setup screen:** `board-setup.sh`'s `setup_wifi_hotspot` installs comitup on every board (`LLL-install.sh` calls it as `--wifi-setup-only`; `-w` skips it): with no known Wi-Fi in range, it opens an open `<hostname>-setup` hotspot with a page that puts the board on a network. Its callback writes `<STATE> <hotspot>` to `/run/comitup-state`. While that says `HOTSPOT`, `disney.py:show_wifi_setup_while_needed` holds the text screen (`display/wifi_setup.py`), before the park fetch at start-up and at the top of each cycle. comitup only tries saved networks with `mode=infrastructure` (the script adds a missing mode); a hotspot that comes up by mistake also cuts off SSH. A drop-in (`COMITUP_WAIT`, `comitup.service.d/wait-for-wifi.conf`) makes comitup wait for `wlan0` plus 10 s at boot: on a cold start it once ran before the Wi-Fi chip existed and hotspotted over a network in range (PelotonPi, 2026-11-11). A board that lacks it gets it with a `daemon-reload`, not a comitup restart.

## Driver abstraction

`driver/` wraps `rgbmatrix` (Pi only) and `RGBMatrixEmulator`: hardware by default (the emulator under tests, or if rgbmatrix won't import). Branch on `driver.is_emulated()`. Importing it never reads the command line: `disney.main()` parses `cli.py:arguments()` once: the Pi model's defaults (`MODEL_DEFAULTS`; `model_defaults()` takes the model from `config.json`'s `pi_model`, else `/proc/device-tree/model`; an unknown Pi still gets the bonnet's mapping; no Pi 5: rpi-rgb-led-matrix can't drive it), overridden by `config.json`'s `matrix` (each board's own size, rotation and overrides, from the settings page; `utils/migrate_boards.py`, run by `LLL-install.sh`, moved the old boards.json entries there once), overridden by the command line (flag names with underscores; bad flags, settings and `--led-rows` other than 32/64 exit); `describe()` logs the result and each setting's source, calls `driver.set_mode(...)` for `--emulated`, then builds the matrix. `driver.graphics` resolves on the current driver at each use; take `RGBMatrix` etc. as `driver.X` after the switch. `import rgbmatrix` doesn't load its `graphics` submodule (the emulator's does), so `set_mode` imports it by name; tests can't catch this, check driver changes on a board before merging.

## Gotchas

- `LLL-install.sh` installs with `pip install --upgrade --prefer-binary`. `--upgrade` keeps the boards current (plain `pip install -r` never moves a package that meets its floor). `--prefer-binary` matters on the 32-bit boards (`armhf`: PlutoPi, ZeroPi), whose piwheels builds lag PyPI; without it pip compiles a newer numpy on a Pi Zero, which takes hours or runs out of memory. The caps in `requirements.txt` keep upgrades compatible.
- Pillow is capped `<12`: the boards' rgbmatrix `SetImage` reads `ImagingCore.unsafe_ptrs`, which Pillow 12 removed, so the first image drawn (the weather icon) crashes the service into a restart loop. The emulator and tests don't touch that path, so check on a real board before raising the cap.
- `board-setup.sh` is tested in `--dry-run` by `tests/tools/test_board_setup.py`, under macOS's bash 3.2 as well as CI's: no associative arrays, `mapfile` or `${x,,}`; it reads system files through `$ROOT` (`BOARD_SETUP_ROOT`) and changes things only through `run`/`in_dir`/`write_file`, so a dry run touches nothing. `setup_tailscale` runs last (`join`: auth key from the answers file via `/run`, else a login link; `install` under `--wifi-setup-only`, which can't log in); tests stub the `tailscale` command, so never let them reach this Mac's. Peloton-LED and MLB are other repos: it calls their installers and never copies their files, so re-read their installers when they change.
