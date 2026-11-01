"""
One-time move of a board's panel settings from the old boards.json (keyed by hostname, in the
repo) into its own config.json "matrix" section, where the settings page edits them. LLL-install.sh
runs it on every update: python3 -m utils.migrate_boards [config.json]. It only fills settings
config.json leaves unset, so a rerun, or a board already set on the page, changes nothing.

Only what isn't the Pi model's (cli.MODEL_DEFAULTS covers the GPIO mapping and timing): the panel's
size, its rotation, and the Mac's emulator switch. Delete this once every board has updated.
"""
import socket
import sys

from utils.config import CONFIG_FILE, load_config, save_config

# boards.json as it was on develop-beta, less what the Pi model now gives.
OLD_BOARDS = {
    "disneypi": {"led_rows": 64, "led_cols": 64},
    "mickeypi": {"led_rows": 64, "led_cols": 64},
    "plutopi": {"led_rows": 32, "led_cols": 64, "led_pixel_mapper": "Rotate:180"},
    "zeropi": {"led_rows": 32, "led_cols": 64},
    "tinypi": {"led_rows": 64, "led_cols": 64, "led_pixel_mapper": "Rotate:90"},
    "joels-macbook-pro": {"led_rows": 64, "led_cols": 64, "emulated": True},
}


def migrate(config, hostname):
    """(config with this board's old settings in "matrix" where it has none, [keys moved])."""
    old = OLD_BOARDS.get(hostname.split(".")[0].lower(), {})
    matrix = config.get("matrix") if isinstance(config.get("matrix"), dict) else {}
    moved = [key for key, value in old.items() if matrix.get(key) is None]
    if moved:
        config = dict(config, matrix={**matrix, **{key: old[key] for key in moved}})
    return config, moved


def main(argv=None, hostname=None):
    path = (argv if argv is not None else sys.argv[1:] or [CONFIG_FILE])[0]
    hostname = hostname or socket.gethostname()
    try:
        config = load_config(path)
    except FileNotFoundError:
        print(f"No {path} yet: set the panel on the settings page once it's made.")
        return 0
    except (OSError, ValueError) as e:
        print(f"Can't read {path} ({e}): set the panel on the settings page.")
        return 1
    new, moved = migrate(config, hostname)
    if not moved:
        print("Panel settings: nothing to move.")
        return 0
    save_config(new, path)
    line = ", ".join(f"{key}={new['matrix'][key]}" for key in moved)
    print(f"Panel settings moved into {path}: {line}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
