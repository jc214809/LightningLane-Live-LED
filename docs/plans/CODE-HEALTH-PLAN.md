# Code health: plan

Status (2026-11-22): phase 1 (#226) and phase 2 done: 2a #228, 2b #229, 2c #227, 2d #230, 2e #232, 2f #233,
2g #231, 2h #234, 2i in two parts (A #236; B #237, waiting for its Disneypi run), plus #235 (frame hashes
cover random stories) and #239 (the duplicate `written()` test helper: no test was weaker than it looked).
Phase 3 done: Pushover to `utils/` (#240), the weather icon on the REST thread (#241), the `api`/`parks`
cycle broken and a `layers` contract in CI (#242). Joel's decisions: keep the 16 `PLR0913` as documented
exceptions; leave the legacy `_ws_loop` no-destinations exit (unreachable: every park gets a destination
id and the thread waits for park data; pinned by a test). Formatting pass done on
`chore/formatting-pass` (see its entry under phase 3). The `settings_page/pushover.py` shim is removed
(`chore/remove-pushover-shim`, 2026-11-22: the old updater imported it at module top, so an in-flight
update is safe). Later: type checking. No `C901`, `PLR0912` or `PLR0915` is left once #237 merges; no source file is over
600 lines.

Goal: raise code quality and make the structure easier to work in, without changing what
any board shows or does. Tests check behaviour today (pytest, 90% coverage); nothing checks
shape: no linter, no complexity limit, no file-size limit, no rule on which package may import
which. So `settings_page/form.py:apply_form` reached a complexity of 46,
`display/fireworks/music_show.py:frame_pixels` 56, and `settings_page/page.py` 1,442 lines.

The approach (proven in Peloton-LED, phases 1–3 done there 2026-11-21):
1. **Add the checks first**, recording today's offenders as a baseline (a "ratchet": nothing
   new may get worse, and each fix removes its baseline entry).
2. **Work the baseline down**, one PR per area, each proving it changed nothing.

Run by **Sonnet 5.5 agents, one branch each**, with a **lead session (Opus 5.5)** that writes
the briefs, starts the agents, reviews every diff, reruns every check itself, and opens PRs
only when Joel says so.

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
HTTP). Counter-example: `display/park/park_details.py` downloads the weather icon with
`requests` from inside the display code, which the draw loop calls every frame (cached, so it
works, but the display layer now knows about the network).

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
`display/park/park_details.py` imports `requests`; `utils/settings_pin.py` imports
`settings_page.pins`; `api` imports `parks.names` while `parks` imports `api.disney_api` (a
package-level cycle); `settings_page` and `self_update` import each other. `import-linter`
turns the rules into a CI check.

### 6. Modules by feature, small enough to hold in your head

A module groups what changes together. Past ~600 lines it usually holds several features:
`show_effects.py` (1,020 lines, ~90 classes and functions) is every scene look of every
show. Split by feature into a package, and keep old imports working by re-exporting from the
package's `__init__.py`, so callers and tests don't change in the same PR:

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

## Measured baseline (2026-11-22, ruff 0.17.5, `--isolated`)

Recorded in the code by phase 1 (`noqa` directives per code, 2026-11-22): `C901` 38, `PLR0912` 23,
`PLR0913` 16, `PLR0915` 11 (88 in 55 lines). `C901` is one above the 37 measured below because
turning an assigned lambda into a `def` (E731) adds a branch to the function around it. The
non-structural hits (E731, F401, B007, ...) are fixed or carry a `noqa` with its reason.

| Check | Hits |
|---|---|
| `C901` complexity > 10 | 37 (none in `tests/`) |
| `PLR0912` > 12 branches | 23 |
| `PLR0913` > 7 arguments | 16 (1 in `tests/`) |
| `PLR0915` > 50 statements | 11 |
| `E`, `F`, `W`, `B` without `E501` and `B905` | 113 (`E731` 40, `F401` 17, `B007` 8, `E741` 7, `F541` 6, `B023` 6, `E402` 6, `B009` 5, …) |
| `B023` loop variable in a closure | 6, all in `tests/` (`test_attraction_info`, `test_show_effects`, `test_santa_train`) |
| `E501` at 100 / 120 / 140 columns | 3,321 / 274 / 28 |
| `I` import sorting, `UP` upgrades | 122, 119 |
| `ruff format --check` | 281 of 337 files would change (double quotes; single: 287) |
| Source files over 600 lines | `settings_page/page.py` 1442, `display/landmarks/santa_train.py` 1231, `display/fireworks/show_effects.py` 1020, `display/fireworks/fireworks.py` 834, `display/fireworks/music_show.py` 740, `display/animation/characters/bluey.py` 604 |

Worst functions (complexity): `music_show.frame_pixels` 56, `form.apply_form` 46,
`mike._body` 36, `merida_poses.split` 27, `form.import_surprises` 23, `fireworks.frame_pixels`
19, `up_house.__init__` 19, `server.do_POST` 18, `walle._draw_walle` 18, `music_show.step` 17,
`tower_of_terror.animate` 16, `ws_legacy._ws_loop` 15, `weather.fetch_weather_data` 15.

## Decisions made

- **Ratchet with inline `# noqa`, not per-file ignores.** `ruff check --add-noqa` writes
  `# noqa: C901` (etc.) on each offending line. The debt is visible where it lives, parallel
  PRs don't all edit one ignore list, and `RUF100` (unused `noqa`) fails CI when a refactor
  fixes a function but leaves its `noqa`, so the baseline can only shrink.
- **Thresholds:** ruff defaults (complexity 10, 12 branches, 50 statements) except
  `max-args = 7` (draw helpers).
- **Not in phase 1:** `E501`, `I`, `UP`, `B905` (adding `strict=True` to `zip()` changes
  behaviour) and `ruff format`. Each rewrites much of the repo and conflicts with every open
  branch. See phase 3.
- **Max file length 600 lines for source; tests exempt.** Enforced by a test with an
  allowlist holding today's offenders at their current length (a file may shrink, not grow).
- **"No behaviour change" is proved, not promised.** Phase 1 builds a frame-hash tool for the
  display; the settings page gets an HTML snapshot test; anything else gets a test pinning
  today's output before the refactor starts.
- **`fireworks.py` and `music_show.py` stay separate copies.** `music_show.py` is the synced
  show's own copy of the simulation on purpose (`docs/dev/SHOWS.md`), so the everyday
  fireworks never change when a show is tuned. Refactor each; don't merge them.
- **Nothing touching start-up, the driver or the WebSocket threads merges without a run on
  Disneypi from the branch** (CLAUDE.md rule; #145 crash-looped boards).

## How the lead runs this (Opus)

1. **One brief per agent**, built from: "Rules for every agent" (below, pasted whole), the
   item's brief, and the exact baseline lines for its files
   (`grep -rn "noqa:[^#]*\(C901\|PLR09\)" <files>`). Agents start cold, so the brief holds
   everything; it never says "as discussed".
2. **Start the agent** with the Agent tool: `model: "sonnet"`, `isolation: "worktree"`,
   in the background. At most **two** at once, on areas that share no files (see the order in
   phase 2), so each diff gets a real review.
3. **While it runs**, the lead reviews the previous agent's diff; it doesn't poll.
4. **On the report**, the lead runs the checklist below. Problems go back to the same agent
   with SendMessage (it keeps its context), listing each with file and line. Two rounds
   without a fix: the lead stops the agent and either fixes it or splits the item.
5. **Push and open the PR into `develop-beta` only when Joel says so.** Merge only after
   asking, once the test steps pass (not the Codecov upload), with the PR description as the
   merge body.
6. After a merge: remove the agent's worktree and branch, tick the item's status line here,
   and rebase any still-open agent branch on the new `develop-beta` before reviewing it.

### Lead's checklist (per agent PR)

1. Read the whole diff. A refactor moves and splits code; it doesn't fix, rename public
   names, or "improve" anything else. Anything else goes back.
2. Rerun every check yourself in the agent's worktree; don't trust pasted output.
3. Rerun the proof of no change (frame hashes / HTML snapshot / pinned test) against
   `develop-beta`'s own output generated *now*.
4. Confirm the item's `noqa`s are gone, the length cap was lowered, and no new `noqa`
   appeared anywhere.
5. Confirm docs: the area's `docs/dev/*.md` note, the `CLAUDE.md` file map if a file moved,
   this plan's status line.
6. For anything start-up, driver or WebSocket: hand Joel the Disneypi commands and wait for
   "it ran" before merging.

## Rules for every agent

Paste this block into every brief.

- Read `CLAUDE.md`, `docs/plans/CODE-HEALTH-PLAN.md` (this file, especially "Clean code in
  Python"), and the topic note for every area you touch (`docs/dev/*.md`) before changing
  anything. Read a whole function before editing inside it.
- Work only in your worktree, on the branch named in your brief, cut from
  `origin/develop-beta`. Commit there, adding files by name (never `git add -A` or
  `git commit -a`). Do not push, open a PR, or touch any other branch.
- **No behaviour change** unless the brief says so. If you find a bug, note it in your report
  and leave it.
- Never commit `config.json`, `surprises.json`, `park_names.json`, `ride_names.json`,
  `sounds/*` (other than its README) or `.claude/settings.local.json`.
- Don't touch `driver/`, `board-setup.sh`, `LLL-install.sh` or systemd units unless the brief
  says so.
- Python 3.11 compatible: no line breaks or reused quote marks inside f-string `{}`.
- Match the surrounding code's style (quotes, naming, comment voice). Keep public names and
  import paths working; re-export from the old module when you move something.
- Never add a structural `noqa` (`C901`, `PLR0912`, `PLR0913`, `PLR0915`) to new code. Remove
  the ones for each function you fix.
- Before reporting done, all of these pass, and you paste their output:
  ```sh
  uv venv --python 3.11 /tmp/venv311 && uv pip install --python /tmp/venv311 -r requirements-dev.txt \
    && /tmp/venv311/bin/pytest -n auto              # the boards' Python
  uv venv --python 3.13 /tmp/venv313 && uv pip install --python /tmp/venv313 -r requirements-dev.txt \
    && /tmp/venv313/bin/pytest -n auto              # CI's other Python: argparse's messages differ from 3.12
  pytest -n auto --cov=. --cov-report=term-missing  # total stays >= 90%; new code covered
  ruff check .                                      # once phase 1 has merged
  lint-imports                                      # once phase 1 has merged
  ```
  Never weaken, skip or delete a test to make it pass. If a check fails and you can't fix it,
  stop and report it; don't call it pre-existing unless you showed it fails on
  `origin/develop-beta` too.
- **Prove nothing changed.** Anything under `display/`, `disney.py` or `tools/render_show.py`:
  ```sh
  git stash -u   # or a second checkout of origin/develop-beta
  python3 tools/frame_hashes.py --out /tmp/before.json
  # ...your change...
  python3 tools/frame_hashes.py --out /tmp/after.json --compare /tmp/before.json
  ```
  The compare must report 0 differences. Run before and after with the same interpreter (hashes
  depend on library versions). Hashes prove only what the run reaches: measure it on the original
  code (`coverage run tools/frame_hashes.py`, then `coverage report -m --include=<your files>`), and
  pin any line of the functions you change that it misses (a random choice, a size-only path) with a
  test committed first. Anything under `settings_page/`: the HTML snapshot
  and form tests pass unchanged. Elsewhere: the brief names the pinning test; write it
  *first*, commit it on its own, and it must pass unchanged after the refactor.
- Update in the same branch: the area's topic note and the `CLAUDE.md` file map if a file moves
  or appears (keep `CLAUDE.md` under 16,000 characters). The lead owns this plan's status line:
  parallel branches editing it conflict.
- A dispatch table must not change how bad input is handled: `TABLE.get(value)` raises on an
  unhashable value that an `if value == "x"` chain ignored; guard with `isinstance` (2i).
- Install both venvs fully and check (`python -c "import xdist"`) before trusting a run.
- Your report: the branch, one paragraph on what changed, files changed, the check output,
  the no-change proof output, the `noqa` count before/after per rule, anything you noticed but
  didn't change, and a draft PR description (`.github/pull_request_template.md`, with
  `## Release notes`: "None" for anything boards won't notice).

## Phase 1: guardrails (one agent, must merge first)

Branch `code-health-guardrails`. Brief:

> Add lint, complexity, file-size and import-layer checks plus a frame-hash tool, with
> today's offenders recorded as a baseline so the build passes on day one.
>
> 1. In `pyproject.toml` (it already has `[project]`; add tool sections only):
>    `[tool.ruff]` `target-version = "py311"`, `extend-exclude` for gitignored folders that
>    hold Python. `[tool.ruff.lint]` `select = ["E", "F", "W", "B", "C901", "PLR0912",
>    "PLR0913", "PLR0915", "RUF100"]`, `ignore = ["E501", "B905"]`.
>    `[tool.ruff.lint.mccabe] max-complexity = 10`, `[tool.ruff.lint.pylint] max-args = 7`.
>    A comment on each choice pointing at `docs/dev/CODE-QUALITY.md`.
> 2. Fix the ~113 non-structural hits where the fix can't change behaviour: `E731` (lambda
>    to `def`), `F401`, `F541`, `B007` (rename to `_`), `E741`, `B009`, `W291` and so on.
>    `E402`: read why the import is late (stubs, path setup); `noqa` it with the reason if it
>    must stay. `B023` (all 6 in tests): if the closure runs inside the same loop iteration
>    it's safe: bind through a default argument; if not, it may be a test that checks less
>    than it claims: `# noqa: B023  possible bug, see report` and list it. `B008` (3, test
>    helpers building `Outcome`/`Target` defaults): fix only if the object is immutable and
>    meant to be shared; otherwise `noqa` with a one-line reason.
> 3. `ruff check --add-noqa --select C901,PLR0912,PLR0913,PLR0915 .`, then `ruff check .`
>    must pass. Put the per-rule `noqa` counts in this plan's baseline table.
> 4. `[tool.importlinter]` with `root_packages = ["api", "parks", "updater", "display",
>    "driver", "utils", "settings_page", "self_update"]`,
>    `include_external_packages = true`, and forbidden contracts:
>    - `api` and `parks` may not import `updater`, `display`, `settings_page`,
>      `self_update` or `driver`.
>    - `display` may not import `api`, `aiohttp`, `requests`, or `updater` other than
>      `updater.shared`; `ignore_imports` for `display.park.park_details -> requests` with a
>      comment ("weather icon fetch; see the plan's phase 3").
>    - `driver` may not import `api`, `parks`, `updater`, `display`, `settings_page` or
>      `self_update`.
>    - `utils` may not import `api`, `parks`, `updater`, `display` or `self_update`, and
>      `settings_page` only through `ignore_imports`
>      `utils.settings_pin -> settings_page.pins` (comment: the PIN file path is owned by
>      the settings service).
>    Break each contract on purpose (add a forbidden import, see `lint-imports` fail, remove
>    it) and say so in the report. Report, don't fix, any import the contracts reveal beyond
>    these.
> 5. `tests/test_file_length.py`: every tracked `.py` file outside `tests/` is at most 600
>    lines, except an allowlist `{path: max_lines}` at today's lengths (baseline table). It
>    also fails when an allowlisted file is now shorter than its cap, telling you to lower
>    it. List files with `git ls-files`; don't depend on the cwd (see
>    `tests/test_claude_md.py`).
> 6. `tools/frame_hashes.py`: renders, deterministically, at 64x32 and 64x64, and writes
>    `{name: sha256}` as JSON; `--compare old.json` prints every differing name and exits 1
>    if any differ. Cover: every entry of `LANDMARKS` (`display/landmarks/screen.py`, seeded
>    `rng`, `frame(t)` at a fixed list of times across the full run); every entry of
>    `TRANSITIONS` (seeded, every frame); the everyday fireworks (`display/fireworks/
>    fireworks.py`, seeded); each synced show's V1 and V2 over the whole score (seeded
>    `MusicShow`, every Nth frame so the run stays under about two minutes; say what N is);
>    the title, ride and countdown screens through `display/capture.py:capture_screen()` with
>    fixed fixture data and a frozen clock. Copy the seeding patterns from
>    `tests/display/fireworks/test_music_show.py` and `tests/display/landmarks/support.py`.
>    Prove it: two runs give identical JSON; changing one pixel in one landmark makes exactly
>    that landmark differ. Add a test that runs it on a small subset. Document it in
>    `docs/dev/DISPLAY.md`.
> 7. Pin `ruff==0.17.5` and `import-linter==2.17` in `requirements-dev.txt`. In
>    `.github/workflows/coverage.yml` add a `lint` job (3.11 only) running `ruff check .` and
>    `lint-imports`. Leave the `test` job as is.
> 8. `.pre-commit-config.yaml` with the ruff hook at the same version, and one line under
>    "Running Tests" in `README.md` on `pre-commit install`.
> 9. Docs: create `docs/dev/CODE-QUALITY.md` from this plan's "Clean code in Python"
>    section (word for word) plus the commands, the ratchet rule ("remove a function's `noqa`
>    when you touch it; never add a structural `noqa` to new code"), the 600-line rule, the
>    layer contracts and `tools/frame_hashes.py`. Add it to `CLAUDE.md`'s topic table
>    (`tests/test_claude_md.py` requires it) and one line under Testing:
>    `ruff check . && lint-imports`. Stay under 16,000 characters.
>
> Release notes: None.

Size: medium. Wide but shallow diff, plus one new tool.

## Phase 2: work the baseline down (after phase 1 merges)

One agent per item, each its own branch, **at most two at once** and never two in the same
package. Each item ends with: its functions' structural `noqa`s removed, its files under 600
lines (or the brief's target) with allowlist caps lowered or removed, all checks passing, and
the no-change proof at 0 differences.

Order (pairs can run together): **2a + 2c**, then **2b + 2d**, then **2e + 2g**, then
**2f + 2h**, then **2i** (alone: start-up and threads, board check).

**2a. Settings form** (`settings_page/form.py`: `apply_form` 46, `import_surprises` 23,
`apply_surprises` 12; branch `settings-form-complexity`)
> First, a pinning test: apply a full form (every field filled) and a minimal one to
> `config.json-example`, plus a surprises import with every case `tests/settings_page/
> test_form.py` already covers and any branch it misses (`--cov-report=term-missing` on
> `form.py`); store the resulting config JSON and error lists. Then split `apply_form` into
> one helper per form section, called in order from a short top function (principle 1), and
> `import_surprises` into validate / merge / write steps. Every error message stays word for
> word. Update `docs/dev/SETTINGS-PAGE.md` and `docs/dev/SURPRISES.md`.

**2b. Settings page and server** (`settings_page/page.py` 1,442 lines; `server.py:do_POST`
18; branch `split-settings-page`)
> First, an HTML snapshot test: render the page for `config.json-example`, a config with
> every optional section filled, and the PIN-locked state; store the output; compare
> byte for byte. Then split `page.py` into one module per card under `settings_page/cards/`
> with `page.py` keeping its public functions (principle 6), and route `do_POST` through a
> path → handler table (principle 2). `tests/settings_page/test_server.py` passes unchanged.
> Update `docs/dev/SETTINGS-PAGE.md`. Runs after 2a (same package).

**2c. Synced show simulation** (`display/fireworks/music_show.py`: `frame_pixels` 56,
`step` 17; branch `music-show-complexity`)
> Break `frame_pixels` into named per-layer steps (sky, castle, effects, actors, overlays,
> whatever the code shows) called in the same order with the same RNG calls in the same
> order: an extra or reordered `rng` call changes every later frame. Frame hashes for every
> show, V1 and V2, must match. Leave `fireworks.py` alone (decision above). Update
> `docs/dev/SHOWS.md`. Note any per-frame cost you see but don't optimise it.

**2d. Show effects** (`display/fireworks/show_effects.py` 1,020 lines; branch
`split-show-effects`)
> Split into a new package `display/fireworks/effects/` by kind of look (lights, particles,
> castle looks, overlays, as the code suggests), with `EFFECTS` built in its `__init__.py`.
> `show_effects.py` stays as a re-export shim so `score.py`, tests and tools don't change
> (don't reuse the name `show_effects` for the package). Frame hashes match. Update
> `docs/dev/SHOWS.md` and the `CLAUDE.md` file map. Runs after 2c (same package).

**2e. Everyday fireworks** (`display/fireworks/fireworks.py` 834 lines: `frame_pixels` 19,
`step` 15; `actors/up_house.py:__init__` 19, `actors/ray.py:draw` 11,
`actors/merida_poses.py:split` 27; branch `fireworks-complexity`)
> Same rules as 2c (RNG order). `merida_poses.py` has a builder
> (`tools/build_merida_poses.py`): rerun it and confirm `merida_poses.json` is unchanged.
> Runs after 2d.

**2f. Santa train** (`display/landmarks/santa_train.py` 1,231 lines: `build` 12,
`rider_patch` 13, `frame` 13; branch `split-santa-train`)
> Split into new sibling modules (not a `santa_train/` package: principle 6), e.g.
> `santa_train_cars.py` and `santa_train_riders.py`, with `santa_train.py` keeping the `Landmark` class and
> re-exporting. Move pixel tables to data where they're branches today (principle 7). Frame
> hashes match.

**2g. Characters** (`mike._body` 36, `walle._draw_walle` 18, `stitch.overlay` 15,
`olaf.pixels` 13, `genie._draw_genie` 12, `army_men.overlay` 12, `luxo_ball._luxo` 11 and
`pixels` 11, `rex._open_jaw` 11, `bluey.py` 604 lines; branch `character-complexity`)
> Worst first; turn per-pixel branches into charts plus palettes the way the newer
> characters do (principle 7). If a character's art comes from `tools/build_sprite_editor.py`
> inputs, rerun the builder. Frame hashes match. Update `display/CHARACTERS.md` if a pattern
> it describes changes. Can be split into two branches if the diff passes ~800 lines.

**2h. Landmarks and capture** (`tower_of_terror.build` 13 and `animate` 16,
`jollywood_tower.animate` 14, `tree_of_life.build` 13, `display/capture.py:_glyphs` 11;
branch `landmark-complexity`)
> Frame hashes match. `capture.py` is the path that once crashed a board (CLAUDE.md): keep
> it working on rgbmatrix's own canvas; the brief's no-change proof is the frame hashes of
> every captured screen plus `tests/display/test_capture*.py` unchanged.

**2i. Live data, config and start-up** (`updater/ws_legacy.py`: `_ws_loop` 15,
`_apply_live_update` 14; `updater/ws_preview.py`: `_preview_ws_loop` 14, `handle` 12;
`api/weather.py:fetch_weather_data` 15; `utils/config.py:surprise_settings` 12;
`self_update/update.py:_update` 12; `disney.py:main` 13; `tools/render_show.py:main` 14;
branch `live-data-complexity`, alone)
> Pin first: for each function, a test that walks every path call by call (mocked socket,
> HTTP, clock), like `tests/updater/ws_support.py` does. Keep the lock rules exactly
> (`parks_data_lock` only around in-memory writes, never across a network call;
> `merge_live_data` mutates in place). Reconnect/backoff timing must not change. **Board
> check before merge:** the lead gives Joel the Disneypi commands; it runs on the branch
> through one WebSocket reconnect and one REST cycle. Update `docs/dev/LIVE-DATA.md` and
> `docs/dev/UPDATER.md`.

**`PLR0913` (16 functions over 7 arguments)** is left at the end on purpose: fixing it
changes signatures. The lead lists them after 2i with a proposal per function (dataclass,
or keep with the `noqa`), and Joel decides.

## Phase 3: Joel's call (after phase 2)

Each is its own PR, decided one at a time:

- **Weather icon out of the display.** `display/park/park_details.py` downloads the icon
  from inside the draw path. Moving it into `api/weather.py` and fetching it on the REST
  thread is cleaner but a behaviour change (when the icon appears); drops the import-linter
  exception.
- **`api` ↔ `parks` cycle.** `api` uses `parks.names`, `parks` uses `api.disney_api`. Likely
  fix: names move down to `utils` or up into `parks` only. Then add an import-linter
  `layers` contract for the whole stack (principle 5).
- **`settings_page` ↔ `self_update`.** `self_update/update.py` imports
  `settings_page.pushover` at module top (kept there so a failed rollback still alerts:
  see Peloton-LED's phase 3 precursor). Possibly move Pushover to `utils/`.
- **Formatting pass** (one PR, when no other branch is open): `UP` (119), `I` (122),
  `E501` at 120 (274 lines) or 140 (28), then `ruff format` with whichever quote style
  rewrites fewer lines (measured: double 281 files, single 287). Add the format commit to
  `.git-blame-ignore-revs`; re-measure `tests/test_file_length.py` caps after.
  **Done 2026-11-22** (`chore/formatting-pass`), re-measured first: `UP` 120, `I` 138; `ruff format`
  rewrites 323 files at 88 columns, 315 at 100 and 299 at 120 (double quotes: 10,974 lines added
  against single quotes' 38,940 at 88). Chosen: double quotes, format at 120, `E501` at 140 (11 lines
  over after formatting, all rewrapped or a string-level `noqa`). `UP031` stays off (a hand rewrite can
  change output); `disney.py`'s old-Python check kept a `noqa: UP036` because a pin test covered it; the check (dead on 3.11) and its pin test were removed afterwards.
  Five files crossed 600 lines from formatting alone and are allowlisted at their new length.
  Frame hashes: 0 differences.
- **Type checking** (mypy or pyright) on `parks/` and `api/` first, the pure layers.
