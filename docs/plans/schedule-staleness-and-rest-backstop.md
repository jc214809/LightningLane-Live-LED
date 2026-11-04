# Plan: schedule-staleness deadlock, extended hours, REST backstop

## Context

An overnight emulator run surfaced a real production bug: once a park closes and midnight passes, it never reopens on the board. Root cause is a circular dependency — `park["closingTime"]` only ever gets refreshed on a closed→open transition, but that transition can't fire without a current schedule already loaded, because `park_has_operating_attraction` hard-gates on the stale `closingTime` before ever checking live attraction data. Chasing that bug surfaced two related decisions:

- Extended/ticketed hours (`TICKETED_EVENT` schedule entries, e.g. a paid after-hours party running past a park's normal close) should be visible on the board via live attraction data, but must **not** be written into `closingTime` — that field stays reserved for the regular `OPERATING` window, matching current behavior.
- Since PR #73 made the per-park live-data endpoint cheap (~6 requests instead of ~340), there's no remaining cost reason to suppress REST attraction polling while the WebSocket is active. Running REST continuously as a backstop gives any WS-sourced "OPERATING" status an independent correction every 5 minutes, which meaningfully de-risks removing the hard `closingTime` gate.

All three changes are needed together and touch overlapping functions (`park_has_operating_attraction`, `update_parks_operating_status`, `update_parks_live_data`), so they're implemented as one pass.

## Change 1 — schedule-staleness trigger (fixes the deadlock)

**File:** `api/disney_api.py`

`handle_park_schedule_update` already receives the `OPERATING` event's fields; store its `date` too:

```python
park["closingTime"] = operating_event.get("closingTime", "")
park["openingTime"] = operating_event.get("openingTime", "")
park["schedule_date"] = operating_event.get("date", "")   # new
```

In `update_parks_operating_status`, add a second, independent trigger for `schedule_refresh_needed` based on the **stored `closingTime` timestamp having passed** — not a raw date-string comparison (a date-string check breaks for parks whose `OPERATING` window itself crosses midnight, e.g. Cedar Point/Kings Island weekend hours; a full ISO timestamp comparison handles that correctly since it carries the real date):

```python
def _closing_time_has_passed(park):
    closing_time_str = park.get("closingTime")
    if not closing_time_str:
        return False
    try:
        closing_dt = datetime.fromisoformat(closing_time_str)
        return datetime.now(closing_dt.tzinfo) > closing_dt
    except (ValueError, TypeError):
        return False

for park in parks:
    is_park_open = park_has_operating_attraction(park)

    if (not park.get("operating") and is_park_open) or (
        _closing_time_has_passed(park) and not park.get("schedule_refresh_needed")
    ):
        park["schedule_refresh_needed"] = True

    park["operating"] = is_park_open

    if fetch_schedules and park.get("schedule_refresh_needed"):
        handle_park_schedule_update(park)
        park["schedule_refresh_needed"] = False
```

`_closing_time_has_passed` is also reused by Change 2 below, so it's extracted rather than inlined twice.

The `not park.get("schedule_refresh_needed")` guard prevents re-flagging every 5-minute cycle while a refresh is already pending — it fires once per close event, gets consumed once `fetch_schedules=True` runs (REST thread), and only re-arms after the next successful `handle_park_schedule_update`.

**Why this doesn't break extended-hours parks:** `closingTime` is only ever populated from the `OPERATING` event (unchanged). A park with `OPERATING` closing at `01:00` the next calendar day won't trigger this until `01:00` actually passes — `datetime.fromisoformat` carries the full date, so a same-instant date-string mismatch (which broke the earlier draft of this fix) can't happen here.

## Change 2 — extended hours visible, without touching `closingTime`

**File:** `api/disney_api.py`, `park_has_operating_attraction`

Today this function hard-gates on `closingTime` before ever looking at attractions — a live, real, wait-time-bearing attraction during a ticketed after-hours event currently can never make the park show as open. Replace the hard gate with a freshness-guarded check that doesn't depend on the schedule at all:

```python
_ATTRACTION_FRESHNESS_MINUTES = 20  # wider than the 5-min REST cycle and normal WS cadence

def _attraction_is_fresh(attraction, now):
    last_updated = attraction.get("lastUpdatedTs")
    if not last_updated:
        return False
    try:
        ts = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    return (now - ts) <= timedelta(minutes=_ATTRACTION_FRESHNESS_MINUTES)


def park_has_operating_attraction(park):
    """
    Returns True if the park has at least one OPERATING attraction with a
    non-empty wait time AND recently-updated live data. closingTime is no
    longer a hard gate — it only drives the schedule-refresh trigger — so a
    live, fresh ticketed/extended-hours event still shows as operating.
    """
    now = datetime.now(timezone.utc)

    if _closing_time_has_passed(park):
        debug.log(f"{park['name']} is past its regular closing time; relying on live attraction freshness.")

    for attraction in park.get("attractions", []):
        wait_time = attraction.get("waitTime")
        status = attraction.get("status")
        if status and status.upper() == "OPERATING" and wait_time not in (None, ''):
            if _attraction_is_fresh(attraction, now):
                debug.info(f"Found open attraction in {park['name']}: {attraction['name']}")
                return True
            debug.log(f"{attraction['name']} ({park['name']}) is OPERATING but stale; not counted.")

    debug.info(f"{park['name']}: no fresh OPERATING attractions found, marking non-operating.")
    return False
```

This is the piece that most directly depends on Change 3 below: with REST polling suspended in WS mode (today's behavior), a WS-only "OPERATING" status has no independent correction if it goes stale, so the freshness guard would be carrying the entire weight of preventing a stuck-open park. Change 3 makes that a belt-and-suspenders check instead of the sole safeguard.

## Change 3 — REST polling stays on continuously, WS layers on top

**File:** `updater/data_updater.py`

`update_parks_live_data` currently skips the per-park REST fetch entirely when `use_websocket=True`. Since PR #73 made that fetch cheap (one request per park), drop the skip:

```python
def update_parks_live_data(parks, use_websocket=False):
    for park in parks:
        if park.get("attractions"):
            new_live_data = asyncio.run(fetch_park_live_data(park))
            if new_live_data is None:
                park["live_data_stale"] = True
                debug.warning(f"Live data fetch failed for {park.get('name')}; keeping existing data.")
            else:
                with parks_data_lock:
                    park["live_data_stale"] = False
                    merge_live_data(park["attractions"], new_live_data)
        ...
```

The `use_websocket` parameter to this function becomes unused for gating the fetch (kept for now only if other callers still branch on it — check at implementation time whether it can be dropped entirely). `live_data_updater`'s WS-mode branch changes from "skip attraction polling, only refresh weather/schedule" to "poll attractions on the normal interval like REST-only mode always has" — the log line at [data_updater.py:100-101](updater/data_updater.py#L100-L101) ("weather refreshed, attraction polling skipped") becomes inaccurate and should be removed/updated to reflect that polling now runs.

**Concurrency note:** this means `merge_live_data` now runs on its own 5-minute REST cadence *concurrently* with the WS thread's `_apply_live_update`, both writing into the same `parks_data`. `updater/shared.py:parks_data_lock` (PR #75) was already built to cover exactly this overlap — both write paths already take the lock — so this should already be correct, but re-verify under this always-on condition rather than assuming; see test plan below.

## Tests

**`tests/api/test_disney_api.py`:**
- Update `test_park_has_operating_attraction` — will need a `lastUpdatedTs` on its fixture attractions now that freshness is checked; add cases for stale-but-OPERATING (returns `False`) and fresh-OPERATING-past-closing-time (returns `True`, the extended-hours case).
- New: park with `closingTime` passed, no fresh attractions → `_closing_time_has_passed` fires the refresh trigger, `handle_park_schedule_update` called, `schedule_refresh_needed` cleared after.
- New: park with `closingTime` passed but `schedule_refresh_needed` already `True` → not re-flagged (no duplicate work).
- New: park with `OPERATING` window crossing midnight (`closingTime` = tomorrow 01:00), current time = tonight 23:30 → `_closing_time_has_passed` is `False`, no false trigger. This is the regression case for the earlier date-string-comparison draft that broke on this scenario.
- New: park with a live, fresh, OPERATING attraction and `closingTime` already passed (simulated ticketed/extended-hours event) → `park_has_operating_attraction` returns `True`.
- Update `test_handle_park_schedule_update` to assert `park["schedule_date"]` is set from the fetched event.

**`tests/updater/test_data_updater.py`:**
- Rewrite `test_update_parks_live_data_websocket_skips_http_fetch` — this assertion inverts; `fetch_park_live_data` must now be called even with `use_websocket=True`. Rename to reflect new behavior (e.g. `test_update_parks_live_data_polls_regardless_of_websocket`).
- Rewrite `test_live_data_updater_websocket_does_initial_fetch_then_skips_polling` similarly — the "then skips polling" half of that test's premise is gone; polling continues on every loop iteration.
- New: concurrency check — call `merge_live_data` and a simulated WS-thread write on the same attraction dict inside/outside `parks_data_lock` and confirm no write is lost (extends the existing `test_update_parks_live_data_merges_under_lock` pattern from PR #75 to the now-continuous-polling scenario).

## Verification

1. `pytest tests/ -q` — full suite green, including rewritten tests above.
2. Live emulator run spanning a real midnight: confirm a schedule refetch happens without any attraction ever needing to flip OPERATING first, and the park resumes showing the next morning at its actual opening time.
3. Manual/log check during a park's normal closing transition: confirm `closingTime` still reflects only the `OPERATING` window (not a ticketed event's extended close) by inspecting `park["closingTime"]` after a schedule refresh on a day with both `TICKETED_EVENT` and `OPERATING` entries (July 29th-style schedule, per the real API data pulled during design).
4. If feasible, a manual test against a park with a same-day ticketed/extended-hours event: confirm the board shows the park as operating while a live, fresh attraction is running past the stored `closingTime`, and confirm it stops showing once that attraction's `lastUpdatedTs` goes stale beyond the freshness window.

## Out of scope / deferred

- Surfacing anything differently in logs/display for the case where `closingTime` has passed but the next schedule fetch comes back with no `OPERATING` event yet (e.g. ThemeParks Wiki hasn't published tomorrow's hours) — current plan is silent retry next cycle, matching existing failure-handling style elsewhere in the file. Revisit if this proves noisy or confusing in practice.
- Making `TICKETED_EVENT` entries first-class (e.g. showing a distinct "extended hours" indicator on the board) — out of scope per explicit instruction; extended hours are visible only as a side effect of the freshness-guarded live-attraction check, not specially labeled.

## Addendum — Change 1's trigger was superseded after a live-log review

Change 1 as originally written (`_closing_time_has_passed`, re-flagging `schedule_refresh_needed` whenever the stored `closingTime` timestamp is in the past) shipped, but a live `app.log` review the same day it deployed showed it re-firing every ~5-minute poll cycle for any park whose freshly-fetched schedule still had a past `closingTime` (i.e. ThemeParks Wiki hadn't published the new day's `OPERATING` event yet). Clearing `schedule_refresh_needed` after the fetch didn't help, because the underlying condition — "is the stored `closingTime` in the past?" — was still true on the very next cycle, so it refetched forever instead of once. In production this meant continuous, uncapped schedule-API polling for Animal Kingdom and Kings Island.

Replacement design, implemented in the same file/functions:

- **`park_has_operating_attraction` stays freshness-only** (unchanged from Change 2 below) — `closingTime` is never a gate on `operating`, so after-hours ticketed-event wait times keep showing on the board via live attraction data, same as before.
- **`_closing_time_has_passed` removed.** The schedule-refresh trigger is no longer timestamp-comparison-based at all.
- **New: once-daily proactive refresh at 3am in the park's own local time** (`_daily_schedule_refresh_due`, `_park_local_now`). Park timezone (IANA name, e.g. `"America/New_York"`) is captured once at startup from the ThemeParks Wiki `/entity/{id}` endpoint (already called for `location`; merged into `get_park_entity_info` to avoid a second HTTP round trip) and stored as `park["timezone"]`; falls back to UTC if missing/unrecognized.
- **Staleness is checked via `schedule_date` vs. today's local date**, not a timestamp comparison — `_daily_schedule_refresh_due` returns `True` only between 3am–9am local and only while `park["schedule_date"]` doesn't match today's date in the park's timezone.
- **Retry-with-backoff instead of every-cycle refetch:** if the fetched schedule still doesn't match today (API hasn't rolled over yet), `park["_daily_refresh_last_attempt"]` gates re-attempts to once per 30 minutes, and the window closes entirely at 9am local — after that, no more attempts until the next day's 3am window. This bounds worst-case API load to a handful of calls per park per day instead of one every 5 minutes indefinitely.
- **The closed→open attraction-based trigger is kept as-is** and fires independently — if a live OPERATING attraction shows up before the 3am job ever succeeds (or after its 9am cutoff), the schedule still gets refreshed on that transition, so the board is never permanently stuck even if the daily job fails outright for the day.

Tests for the old `_closing_time_has_passed`-based cases were replaced with equivalents for `_daily_schedule_refresh_due`/`_park_local_now` and an end-to-end 3am-trigger regression test in `tests/api/test_disney_api.py`.
