import sys
import os
import time
import logging
import threading
import json
import random
import traceback
from datetime import datetime, timezone

import driver
from driver import RGBMatrix, __version__

from display.park.park_details import render_park_information_screen
from display.display import initialize_fonts
from display.fireworks.fireworks import render_castle_fireworks
from utils.utils import args, led_matrix_options
from api.disney_api import fetch_list_of_disney_world_parks, forecast_wait_now, resolve_parks_from_config, show_start_due
from display.animation import TRANSITIONS, forget_screen, show_screen
from display.landmarks import landmark_for, landmark_screen
from utils.special_events import active_party, fireworks_show
from display.attractions.attraction_info import draw_attraction_frame
from updater.data_updater import live_data_updater
from updater.websocket_updater import websocket_live_updater
from display.countdown.countdown import render_countdown_to_disney
from utils.trips import active_trip, parse_trips

from utils import debug

# Configure logging
def load_config(file_path):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

logger = logging.getLogger("disney-lll")
if load_config('config.json')['debug']:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

use_image_logo = False
PARK_REVEALS = ("tink", "buzz")
# Rare visitors on ride screens, and each one's chance per screen. Genie erupts from his
# lamp and sweeps the next ride in; Baymax peeks over it so the wait stays readable;
# Slinky walks off the right edge and his spring wraps round the back of the board;
# WALL-E, in profile, bales the old ride into a cube and drives off with it (his
# three-quarter view, "walle", is kept for force_surprise but isn't in the rotation);
# Mike Wazowski pops up, looks around and scares (and visits the Laugh Floor more often).
# Two TRON light cycles race across, blue on top and red below, their trails the wipe.
# Olaf stacks himself up out of snowballs while it snows, waves, and walks off.
# Goofy flies his biplane through a loop-the-loop, towing a YAHOOEY! banner.
# The Pixar Ball bounces in with Luxo Jr., in one of three little stories.
# Lightning McQueen zooms in, skids, Ka-chows and peels out; Mater drives across backwards.
# (WALL-E and Baymax were trimmed to make room for the Cars pair under 10% in all.)
# Chip scampers across with Dale chasing (the Army Men were trimmed to make room).
# Tigger bounces across on his tail. Surprises may fill up to 12% of ride screens.
# Ride screens run 8s each, about 400 an hour while parks are open, so 1% is roughly
# four visits an hour.
SURPRISES = {"genie": 0.005, "baymax": 0.012, "slinky_wrap": 0.01, "walle_side": 0.012, "army_men": 0.010,
             "mike": 0.008, "tron": 0.008,
             "olaf": 0.005, "goofy": 0.008,
             "luxo_ball": 0.005, "mcqueen": 0.005, "mater": 0.005,
             "chip_dale": 0.005, "tigger": 0.005}
# Visitors who only turn up on their own rides, and how often on those rides. Matched by
# a piece of the ride's name, ignoring case. The Falcon keeps to Galaxy's Edge; Mike is
# in the rotation too, but drops in on his own Laugh Floor far more often.
RIDE_VISITORS = {
    "falcon": {"rides": ("smugglers run", "rise of the resistance"), "chance": 0.10},
    "mike": {"rides": ("laugh floor",), "chance": 0.10},
}
# When Magic Kingdom's fireworks start, the board drops everything and plays its own
# castle fireworks (no title) until this long after the show's start time.
# config.json "force_surprise": plays that visitor on every ride screen. For checking a
# character on a real board; leave it unset otherwise.
forced_surprise = None
FIREWORKS_SHOW_S = 5 * 60
_shows_played = set()

def main():
    # Load configuration
    config = load_config('config.json')
    set_forced_surprise(config.get("force_surprise"))
    parks_data = []
    update_interval = 300  # 5 minutes (300 seconds)

    # Check Python version.
    if sys.version_info <= (3, 5):
        debug.error("Please run with python3")
        sys.exit(1)

    if driver.is_emulated():
        if driver.hardware_load_failed:
            debug.log("rgbmatrix not installed, falling back to emulator!")

        debug.log("Using RGBMatrixEmulator version %s", __version__)
    else:
        debug.log("Using rgbmatrix version %s", __version__)

    # Use your helper functions to get proper options.
    command_line_args = args()
    matrixOptions = led_matrix_options(command_line_args)

    matrix = RGBMatrix(options=matrixOptions)
    initialize_fonts(matrix.height)

    park_names = config.get('parks', [])
    disney_park_list = resolve_parks_from_config(park_names)
    if not disney_park_list:
        debug.error("No parks found. Exiting.")
        return

    api_key = config.get("themeparks_api_key")
    websocket_only = config.get("websocket_only", False)
    use_websocket = bool(api_key and not api_key.startswith("<")) or websocket_only

    update_thread = threading.Thread(
        target=live_data_updater,
        args=(disney_park_list, update_interval, parks_data),
        kwargs={"use_websocket": use_websocket},
        daemon=True
    )
    update_thread.start()

    if use_websocket:
        ws_thread = threading.Thread(
            target=websocket_live_updater,
            args=(api_key, parks_data),
            daemon=True
        )
        ws_thread.start()
        debug.info("WebSocket live updater started — REST live data polling disabled.")
    else:
        debug.info("No ThemeParks API key configured; using polling only.")

    log_configured_trips(config)

    last_trip_shown = None
    try:
        while True:
            play_fireworks_show_if_due(matrix, parks_data)
            render_logo(matrix)
            last_trip_shown = play_trip_countdown(matrix, config, last_trip_shown)
            if parks_data:
                for park in parks_data:
                    if not park.get("operating"):
                        logging.info(f"Skipping {park['name']} because no attractions are operating.")
                        continue
                    play_fireworks_show_if_due(matrix, parks_data)
                    initialize_park_information_screen(matrix, park)
                    loop_through_attractions(matrix, park, parks_data)
            else:
                debug.info("No parks data yet, waiting...")
                time.sleep(5)
            matrix.Clear()
    except Exception as e:
        matrix.Clear()
        debug.error(f"An error occurred: {e}")
        debug.error(traceback.format_exc())
    finally:
        matrix.Clear()

def log_configured_trips(config):
    trips = parse_trips(config)
    if trips:
        debug.info(f"Configured trips: {[_describe_trip(t) for t in trips]}")
    else:
        debug.info("No trip dates configured.")


def play_trip_countdown(matrix, config, last_shown=None):
    """
    Show the countdown for the one trip that's current, if the countdown is on.
    Picked each cycle so the screen moves on as trips start, end and pass. Returns
    the trip shown (or last_shown), so a change is logged once rather than every cycle.
    """
    if not config.get('trip_countdown', {}).get('enabled'):
        logging.info("Trip countdown is not enabled.")
        return last_shown
    trip = active_trip(parse_trips(config))
    if trip is None:
        logging.info("No upcoming trips; countdown hidden.")
        return last_shown
    if trip != last_shown:
        debug.info(f"Trip countdown showing: {_describe_trip(trip)}")
    show_trip_countdown(matrix, trip)
    return trip


def _describe_trip(trip):
    span = trip.start.isoformat() + (f" to {trip.end.isoformat()}" if trip.end else "")
    return f"{trip.name} ({span})" if trip.name else span

def render_logo(matrix):
    matrix.Clear()
    logo_path = os.path.abspath("./assets/MK.png")
    if os.path.exists(logo_path) and use_image_logo:
        debug.info("Logo found. Displaying...")
        from PIL import Image
        logo = Image.open(logo_path)
        matrix.SetImage(logo.convert("RGB"))
        time.sleep(8)
        logo.close()
    else:
        debug.info("Rendering castle fireworks intro...")
        render_castle_fireworks(matrix)
    forget_screen(matrix)


def _static(render, *args):
    def draw(canvas, t):
        render(canvas, *args)
        return False
    return draw


def initialize_park_information_screen(matrix, park):
    party = active_party(park)
    landmark = landmark_for(park.get("name"), party)
    if landmark:
        debug.info(f"Rendering {park['name']} landmark{f' for the {party} party' if party else ''}.")
        scene = landmark(matrix.width, matrix.height, park=park)
        show_screen(matrix, landmark_screen(scene), scene.SCREEN_S)
    debug.info(f"Rendering {park['name']} Title Screen. | Weather: {park.get('weather')}")
    show_screen(matrix, _static(render_park_information_screen, park), 8, transition=random.choice(PARK_REVEALS))

def play_fireworks_show_if_due(matrix, parks, now=None):
    """
    If the fireworks show a park runs tonight (from its schedule: see special_events.fireworks_show)
    started in the last FIREWORKS_SHOW_S seconds, play the castle fireworks in that show's theme,
    without the title, until that window ends. Each performance plays once. Returns True if it played.
    """
    now = now or datetime.now(timezone.utc)
    for park in parks:
        show, theme = fireworks_show(park, now)
        start = show_start_due([park], show, FIREWORKS_SHOW_S, now)
        if start is None or (show, start) in _shows_played:
            continue
        _shows_played.add((show, start))
        remaining = FIREWORKS_SHOW_S - (now - start).total_seconds()
        debug.info(f"{show} started at {start.isoformat()}: fireworks for {remaining:.0f}s.")
        render_castle_fireworks(matrix, duration=remaining, title=False, theme=theme)
        forget_screen(matrix)
        return True
    return False

def set_forced_surprise(name):
    """Validate config.json's force_surprise; an unknown name is ignored, not fatal."""
    global forced_surprise
    forced_surprise = None
    if not name:
        return
    if name not in TRANSITIONS or name == "wipe":
        debug.warning(f"force_surprise {name!r} isn't a character transition; ignoring it. "
                      f"Choose from: {', '.join(t for t in TRANSITIONS if t != 'wipe')}")
        return
    forced_surprise = name
    debug.warning(f"force_surprise is set: {name} plays on every ride screen. Remove it from config.json when done testing.")

def loop_through_attractions(matrix, park, parks=()):
    for attraction_info in park.get("attractions", []):
        # Checked between screens, so the fireworks cut in at most one screen late.
        play_fireworks_show_if_due(matrix, parks)
        if (attraction_info.get("status") not in ["CLOSED", "REFURBISHMENT"]
                and attraction_info.get("waitTime") not in [None, '']):
            # Snapshot the dict: the updater threads mutate it in place mid-animation.
            ride = dict(attraction_info)
            expected = forecast_wait_now(ride.get("forecast"))
            debug.info(
                f"Displaying ride: {ride['name']} (Park: {park['name']}) | "
                f"Wait Time: {ride['waitTime']} min | Forecast: {expected} | Status: {ride['status']}")
            surprise = forced_surprise or _ride_visitor(ride.get("name", "")) or _surprise(random.random())
            if surprise != "wipe":
                debug.info(f"{surprise.capitalize()} is visiting {ride['name']}.")
            show_screen(matrix, _attraction_screen(ride, expected), 8, transition=surprise)

def _ride_visitor(ride_name):
    """A visitor who belongs to this ride, if one rolls in; None otherwise (and no roll is spent)."""
    name = ride_name.lower()
    for visitor, spec in RIDE_VISITORS.items():
        if any(part in name for part in spec["rides"]) and random.random() < spec["chance"]:
            return visitor
    return None

def _surprise(roll):
    # Each visitor owns a slice of the roll as wide as their chance, so order doesn't change the odds.
    edge = 0.0
    for name, chance in SURPRISES.items():
        edge += chance  # a running total; subtracting from the roll drifts at slice edges
        if roll < edge:
            return name
    return "wipe"

def _attraction_screen(ride, expected):
    # A closure per ride: the next screen's sweep redraws this one, so it must not see later loop values.
    return lambda canvas, t: draw_attraction_frame(canvas, ride, t, expected)

def show_trip_countdown(matrix, trip):
    if trip is None:
        return
    show_screen(matrix, lambda canvas, t: render_countdown_to_disney(canvas, trip, t), 7)

if __name__ == "__main__":
    main()
