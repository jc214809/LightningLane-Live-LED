# Code quality: checks, layers and the clean-code rules

Read before changing code structure, adding a lint suppression, or splitting a file. The plan that introduced these checks and is working today's offenders down: `docs/plans/CODE-HEALTH-PLAN.md`.

## Commands

```sh
ruff check .                      # lint + complexity; CI's `lint` job runs it (ruff 0.17.5, pinned in requirements-dev.txt)
lint-imports                      # which package may import which (import-linter 2.17); CI's `lint` job runs it
pre-commit install                # once: runs ruff on every commit (.pre-commit-config.yaml)
pytest tests/test_file_length.py  # the 600-line rule

# Prove a display change changed nothing (see "Frame hashes" below)
python3 tools/frame_hashes.py --out /tmp/before.json                        # on the base branch
python3 tools/frame_hashes.py --out /tmp/after.json --compare /tmp/before.json   # after: must print "0 differences"
python3 tools/frame_hashes.py --only landmark/CastleLandmark --only transition/mike   # a subset, quickly
```

## The ratchet

`pyproject.toml` selects `E`, `F`, `W`, `B` (bugbear) and four structural rules: `C901` (complexity over 10), `PLR0912` (over 12 branches), `PLR0913` (over 7 arguments: draw helpers take many, so 7, not ruff's 5) and `PLR0915` (over 50 statements), plus `RUF100`. `E501` (line length) and `B905` (`zip(strict=)`, a behaviour change) are off until phase 3 of the plan.

Today's structural offenders carry an inline `# noqa: C901` (etc.) on their `def` line. `RUF100` fails the build on a `noqa` that no longer suppresses anything, so the baseline can only shrink:

- **Remove a function's `noqa` when you touch it** and fix what it flagged.
- **Never add a structural `noqa` to new code.** Split the function instead (principles 1 to 3 below).
- Any other `noqa` (`E402` for an import that must come late, `F401` for a name that is imported to be looked up) needs a one-line reason after it.

## File length

Source files (every tracked `.py` outside `tests/`) stay at 600 lines or fewer. `tests/test_file_length.py` holds an allowlist `{path: max_lines}` of the files that were already longer: a file may shrink, not grow, and the test fails when an allowlisted file is now shorter than its cap, telling you to lower the cap (or delete the entry once it is under 600). Split by feature (principle 6), keeping old imports working from the old module.

## Layers

`[tool.importlinter]` in `pyproject.toml`, run by `lint-imports`:

- `api` and `parks` may not import `updater`, `display`, `settings_page`, `self_update` or `driver`.
- `display` may not import `api`, `aiohttp`, `requests` or `updater` (except `updater.shared`). No display exception is left: the weather icon is downloaded by the REST thread (`api/weather_icons.py`) and published in `updater.shared.weather_icons`.
- `driver` may not import `api`, `parks`, `updater`, `display`, `settings_page` or `self_update`.
- `utils` may not import `api`, `parks`, `updater`, `display`, `self_update` or `settings_page`. Known exception: `utils.settings_pin -> settings_page.pins` (the PIN file's path is owned by the settings service).

Adding an import that breaks a contract fails CI; add to `ignore_imports` only with a comment saying why and where the fix is planned. Other cycles (`api` and `parks` import each other; `settings_page` and `self_update` too) are known and left to phase 3.

## Frame hashes: proof that a display refactor changed nothing

`tools/frame_hashes.py` renders everything the boards draw, deterministically, at 64x32 and 64x64, and writes `{name: sha256}` (the hash is over the raw pixel bytes of every frame). `--compare old.json` prints every name that differs and exits 1. Covered, with each name's prefix (`--only` takes a substring of the name, repeatable; `--list` prints them): every landmark class and its title-and-text screen (`landmark/`, `landmark-screen/`), every `TRANSITIONS` entry (`transition/`), the everyday and themed castle fireworks (`fireworks/`), each synced show's V1 and V2 over the whole score (`show/`, every frame), and the park-info, ride and countdown screens through `capture_screen()` (`screen/`). It needs no WAV and never opens the browser emulator; a full run takes about 80 seconds (the four show renders are about 53 of them).

Run it on the base branch before the change and with `--compare` after: 0 differences. It is deterministic because every RNG is a `random.Random(1)` handed to the class, the clock the screens read is frozen, the weather icon is a fixture and the script re-runs itself with `PYTHONHASHSEED=0`. A thing that raises is recorded as `error: ...`, so it shows up as a difference. When you add a landmark, transition, fireworks theme, show or screen fixture, it is picked up automatically (landmarks, transitions, themes, shows) or added to the fixtures in the tool (screens); the baseline file is never committed, you make it fresh from the base branch.

## Clean code in Python: the principles this plan applies

This section is the "why" behind every brief. Phase 1 copies it into `docs/dev/CODE-QUALITY.md`
so it outlives the plan. Clean code isn't a style; it's code where each piece has one job, a
name that says what the job is, and as few things as possible it depends on, so a change lands
in one place and a test can check it alone.

### 1. One job per function, at one level of detail

A function either *decides* (the steps, in order, named) or *does* (one step). When one
function does both, its complexity climbs: `apply_form` (46) reads every section of the
settings form, validates it, and writes it in one body. Split it so the top reads like a
table of contents:

```python
def apply_form(config, form):
    errors = []
    _apply_trip(config, form, errors)
    _apply_parks(config, form, errors)
    _apply_display(config, form, errors)
    _apply_sound(config, form, errors)
    return errors
```

Rule of thumb: if you need a comment to say what the next ten lines do, those lines are a
function and the comment is its name.

### 2. Replace long `if/elif` chains with a table

This repo already does it well: `TRANSITIONS` in `display/animation/characters/__init__.py`
and `LANDMARKS` in `display/landmarks/screen.py` map a name to a class, so adding a character
never touches a branch. Apply the same to request routing (`settings_page/server.py:do_POST`,
18), form sections, and scene effects:

```python
ROUTES = {"/save": _save, "/pin": _check_pin, "/update": _start_update}

def do_POST(self):
    handler = ROUTES.get(self.path)
    if handler is None:
        return self._send(404)
    return handler(self)
```

### 3. Guard clauses instead of nesting

Return early on the unusual case so the normal path stays at the left margin. Every level of
nesting is a branch the reader has to hold in their head.

```python
# before                                   # after
if data:                                   if not data:
    if data.get("liveData"):                   return []
        for ride in data["liveData"]:      live = data.get("liveData")
            ...                            if not live:
                                               return []
                                           for ride in live:
                                               ...
```

### 4. Pure logic apart from I/O ("functional core, imperative shell")

A function that computes from its arguments and returns a value is trivial to test. One that
also fetches, reads a file, logs or draws to the matrix needs stubs. Keep the decision pure
and put the I/O at the edge. `parks/` already works this way (decisions over park data, no
HTTP). Example of the fix: the weather icon used to be downloaded from `display/park/park_details.py`
(called every frame); the REST thread now downloads it and the screen only reads the ready image.

### 5. Dependencies point one way: layers

Each package is a layer and may only import from layers below it. When a lower layer imports
a higher one you get cycles, surprising import-time side effects, and "change one thing,
break another". This repo's intended layering:

```
disney.py, cli.py                 entry points: wire everything together
display/  settings_page/  self_update/   what the user sees / the services
updater/                          live-data threads
parks/                            decisions over park data (pure)
api/                              HTTP fetch and parse
utils/  driver/                   foundations: config, logging, hardware
```

Measured 2026-11-22, it mostly holds. The exceptions phase 1 records (and phase 3 decides on):
`utils/settings_pin.py` imports
`settings_page.pins`; `api` imports `parks.names` while `parks` imports `api.disney_api` (a
package-level cycle); `settings_page` and `self_update` import each other. `import-linter`
turns the rules into a CI check.

### 6. Modules by feature, small enough to hold in your head

A module groups what changes together. Past ~600 lines it usually holds several features:
`show_effects.py` was 1,020 lines, every scene look of every show; it's now the
`display/fireworks/effects/` package, one module per kind of look. Split by feature into a
package, and keep old imports working by re-exporting (here `show_effects.py` became a
seven-statement shim), so callers and tests don't change in the same PR:

```python
# display/fireworks/effects/__init__.py
from display.fireworks.effects.searchlights import Searchlights, FanfareSearchlights
from display.fireworks.effects.particles import Sparkle, Comet
EFFECTS = {"searchlights": Searchlights, ...}
```

Never turn a module's name into a package's name in one step (`foo.py` → `foo/`): a board
mid-update can have both on disk. Use a new name.

### 7. Art is data, not branches

Pixel art drawn with `if x == 3 and y in (4, 5): ...` makes complexity of 36
(`mike.py:_body`). The repo's own pattern is better: a chart (rows of characters) plus a
palette, read by one small loop. A drawing function should loop over data, not decide pixel
by pixel.

### 8. Group arguments that travel together

Eight parameters (`x, y, w, h, colour, font, t, scale`) usually means two or three objects
are missing. A `dataclass` (or `NamedTuple` for something immutable) names the group:

```python
@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int
```

Draw helpers legitimately take many arguments, so the limit here is 7, not ruff's default 5.

### 9. Names and constants

Names say intent (`seconds_until_open`, not `d`). Magic numbers get a named constant at the
top of the module (`LANDMARK_S = 3.0` in `display/landmarks/scene.py` is the pattern). Booleans
read as questions (`is_open`, `has_key`). Ambiguous single letters (`l`, `O`, `I`) are banned
(`E741`).

### 10. Errors: narrow, logged, never silent

Catch the exception you expect (`requests.RequestException`), not `Exception`, and when you
do catch broadly, log it through `utils/debug`. Re-raise with `raise NewError(...) from e` so
the cause survives (`B904`). Never use a mutable default argument (`def f(x=[])`, `B006`).

### 11. Comments say why, not what

`response.raise_for_status()  # Raise an exception for HTTP errors` repeats the code. The
comments worth keeping explain a reason the code can't: "Called every animation frame: no
logging on this path". This repo's comments are mostly the good kind; keep them so.

### 12. Pythonic idioms the linters will nudge you toward

`def` instead of assigning a lambda to a name (`E731`, 40 of them here: a `def` gets a real
name in tracebacks); f-strings without placeholders become plain strings; unused imports and
loop variables go (`F401`, `B007`); `enumerate`/`zip` instead of index arithmetic; `with` for
anything opened; `pathlib` for new path code.

### What clean code is *not*

Not more classes, layers or abstractions for their own sake: three similar lines beat a
premature helper. Not rewriting working code to taste: consistency with the surrounding code
beats preference. Not a reason to change behaviour: every refactor in this plan is
byte-identical in output.
