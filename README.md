# LightningLane-Live-LED
![Tests](https://github.com/jc214809/LightningLane-Live-LED/actions/workflows/coverage.yml/badge.svg) [![codecov](https://codecov.io/gh/jc214809/LightningLane-Live-LED/graph/badge.svg)](https://codecov.io/gh/jc214809/LightningLane-Live-LED)


LightningLane-Live-LED is a Python application designed to fetch and display wait times for attractions at Walt Disney World and other theme parks on an LED matrix display. It retrieves park and attraction data from the [ThemeParks Wiki API](https://api.themeparks.wiki) and dynamically renders ride information—including park names, ride names, and wait times—onto an LED matrix. The application supports both actual hardware and an emulator for testing purposes.

## Features

- **API Integration:**  
  Retrieves park data and attraction details for Walt Disney World, Cedar Point, Kings Island, and any other destination supported by the ThemeParks Wiki API. Parks are configured by name in `config.json`.
- **Real-Time WebSocket Updates:**  
  With a ThemeParks API key configured (see [below](#websocket-recommended)), live wait times arrive over a persistent WebSocket connection (`wss://api.themeparks.wiki/v1/live`) as attraction statuses change. The app performs an initial REST fetch at startup to populate all data (or, with the [preview protocol](#preview-protocol-optional), takes it from the WebSocket), then the WebSocket delivers ongoing updates. The connection is self-healing: a dead or silently-stalled connection is detected and reconnected automatically (typically within 2 minutes), and anything missed during the outage is caught up afterward.
- **REST Polling:**  
  The REST API is polled every 5 minutes, with or without a key. Without one, that's how wait times update; with one, it's the backstop if the WebSocket is down.
- **Dynamic Display Rendering:**  
  Renders park details, character meet and greets (w/ Wait Times) and ride information with dynamic text wrapping and spacing on an LED matrix.
- **Trip Countdown:**  
  Displays a countdown to your next Disney visit for added excitement. Supports multiple upcoming trip dates.
- **Current Weather Updates:**  
  Provides live weather information for each park.
- **Emulation Mode:**  
  Supports running the application in emulation mode via `RGBMatrixEmulator` for testing without physical hardware.
- **Detailed Logging:**  
  Offers extensive logging for monitoring application behavior and debugging issues.

## Prerequisites

- **Python 3.11+**
- **Pip** package manager

**Currently supported board configurations:**
 * 64x32
 * 64x64

## Installation

### Hardware
The parts, how they fit together, each board's settings, and optional sound and a power button are in [docs/hardware/README.md](docs/hardware/README.md). For step-by-step assembly, see the [inspiration project MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard), which runs on the same hardware.

If you'd like to see support for another set of board dimensions, or have design suggestions for an existing one, feel free to file an issue!

## Software Installation

**Pi's with known issues**
 * Raspberry Pi Zero has had numerous reports of slowness and unreliability during installation and running with other software.
 * HOWEVER, I was able to run this project in a headless version on Pi OS on a Pi Zero 2 W

### Setting up a new board (board-setup.sh)
On a fresh Raspberry Pi OS card, one script sets up the whole board for one app: this one, [Peloton-LED](https://github.com/jc214809/Peloton-LED) or [MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard). Run it from your own login (it finds your home folder from `sudo`):

```bash
curl -fsSLO https://raw.githubusercontent.com/jc214809/LightningLane-Live-LED/develop-beta/board-setup.sh
sudo bash board-setup.sh
```

It asks everything first (hostname, app, whether to set the panel options here (size, GPIO mapping and slowdown, extra flags; the default is no, since each app keeps them in its own config), a second Wi-Fi network such as a phone hotspot, the [power button](docs/hardware/POWER.md)), shows a summary, then clones the app into your home folder and runs the app's own installer, sets up the matrix tuning (`snd_bcm2835` off, `isolcpus=3`), writes the app's systemd service, and stops the other two apps' services, since only one app can drive the panel. Re-run it to update a board or switch apps; on a board it has already set up, it skips the slow matrix-driver build.

- **Older service files:** a board set up by hand often has its own `LightningLane-Live-LED.service` (in `/lib` or `/etc`, with the panel flags in it), which would keep it on those flags instead of `boards.json`. The script moves them to `/var/backups/board-setup/<date>/` (never deletes them) and prints the flags each one ran with, so you can check them against the board's `boards.json` entry. It also points out any `config.json` `matrix` settings, which override `boards.json`, but leaves them alone.
- **This app:** the service carries no panel flags. If you said yes to the panel options and `boards.json` has no entry for the hostname, they go in `config.json`'s `matrix` section instead (or add an entry for the board and commit it). A new `config.json` is copied from the example: fill in your keys afterwards.
- **Peloton-LED:** its own installer puts it in `/opt/peloton-led` and asks for the riders; if you chose to set the panel options here, this script adds them in a drop-in, `/etc/systemd/system/peloton-led.service.d/board.conf`.
- `--branch develop-sound` installs this app from another branch (the default is `develop-beta`; the branch question asks it too).
- **Wi-Fi setup hotspot (every board, every app):** it installs [comitup](https://davesteele.github.io/comitup/). When no Wi-Fi the board knows is in range, the board opens a hotspot named after it, `<hostname>-setup` (e.g. `Disneypi-setup`), with no password. Join it from a phone, pick your network on the page that opens (or browse to http://10.41.0.1/), and the board joins it. While the hotspot is up, this app's screen says `Wi-Fi setup`, `Join` and the hotspot's name. The hotspot is open, so anyone nearby can join it and see the Wi-Fi password typed into that page, but only while the board is in setup. Networks the board already has are kept and always tried first. It needs NetworkManager (Raspberry Pi OS Bookworm or later): an older board is skipped. `LLL-install.sh` sets it up too (`-w` skips it); `sudo bash board-setup.sh --wifi-setup-only` does just this.
- **Settings page (LightningLane-Live-LED):** every `config.json` setting (API keys, parks, trips, sound, brightness, shows, and the panel under Advanced) from a browser, so a board can be set up with no SSH. On the setup hotspot, browse to http://10.41.0.1:8080 (the Wi-Fi setup screen shows it next): no password, since you're with the board. On the home network, browse to `http://<hostname>.local:8080` and press **Show a PIN on the board**: the board shows a 4-digit PIN for two minutes, and typing it in signs that browser in for an hour (five wrong tries use a PIN up). Saved API keys show only their last four letters; leave a key blank to keep it. Saving checks everything first, keeps the old file as `config.json.bak`, and restarts the app. It runs as its own service, `lll-settings.service`, so it works even when a bad `config.json` stops the app; `journalctl -u lll-settings.service` has its log. `--wifi-setup-only` from the app's folder (so `LLL-install.sh`) installs it too.
- `--answers board.txt` answers questions ahead with `KEY=value` lines (`APP=lll`, `LED_ROWS=64`, ...; `--help` lists the keys). `--dry-run` prints everything it would do and changes nothing. The Wi-Fi password is never stored in the answers file or put on a command line.

Reboot afterwards if it says so (boot settings changed).

### Software Installation
#### Requirements
You need Git for cloning this repo and PIP for installing the software.
```bash
sudo apt-get update
sudo apt-get install git python3-pip
```
### Using a Virtual Environment (Recommended)

#### Installing the scoreboard software
This installation process will take about 10-15 minutes. Raspberry Pis aren't the fastest of computers, so be patient!

   ```bash
   git clone https://github.com/jc214809/LightningLane-Live-LED.git
   cd LightningLane-Live-LED/
   sudo ./LLL-install.sh
   ```

This will create a Python Virtual Environment and install all of the required dependencies. The
virtual environment will be located at `LightningLane-Live-LED/venv/`.

The installer doesn't create your config. Copy the example and fill in your parks, keys and trip dates (see [WebSocket](#websocket-recommended), [Configuring Parks](#configuring-parks) and [Weather](#weather)):

```bash
cp config.json-example config.json
```

This will install the rgbmatrix binaries, which we get from [another open source library](https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python#building). It controls the actual rendering of the scoreboard onto the LEDs. If you're curious, you can read through their documentation on how all of the lower level stuff works.

It will also install the following python libraries that are required for certain parts of the scoreboard to function.

* [RGBMatrixEmulator](https://github.com/ty-porter/RGBMatrixEmulator): The emulation library for the matrix display. Useful for running on MacOS or Linux, or for development.
* [pyowm](https://github.com/csparpa/pyowm): OpenWeatherMap API interactions. We use this to get the current weather at each park. For more information on how to finish setting up the weather, visit the [weather section](#weather) of this README.

#### Customizing the Installation

Additional flags are available for customizing your install:

```
-a, --skip-all          Skip all dependencies and config installation (equivalent to -c -p -m -v -w).
-c, --skip-config       Skip updating JSON configuration files. (Currently no effect: the installer never changes config.json.)
-m, --skip-matrix       Skip building matrix driver dependency. Video display will default to emulator mode.
-p, --skip-python       Skip Python 3 installation. Requires manual Python 3 setup if not already installed.

-v, --no-venv           Do not create a virtual environment for the dependencies.
-e, --emulator-only     Do not install dependencies under sudo. Skips building matrix dependencies (equivalent to -m)
-w, --skip-wifi-setup   Skip the Wi-Fi setup hotspot (see board-setup.sh above). Linux only; -e skips it too.
-d, --driver            Specify a branch name or commit SHA for the rpi-rgb-led-matrix library. (Default: master)

-f, --force             Try to skip most errors and force install. May be able to recover from previous installer errors.

-h, --help              Display this help message
```

#### Installation on Non-Raspberry Pi Hardware

The installation script is designed for physical hardware. When attempting to install it on other platforms, you should not use `sudo` to install the dependencies. In addition, you can pass the `--emulator-only` argument to skip installation steps that aren't required.

```
sh LLL-install.sh --emulator-only
```

#### Updating
* Run `git pull` in your LightningLane-Live-LED folder to fetch the latest changes. A lot of the time, this will be enough, but if something seems broken:
    * **Re-run the install file**. Run `sudo ./LLL-install.sh` again. Any additional dependencies that were added with the update will be installed this way.
    * **Check your `config.json`**. The installer never changes it, so new options won't appear on their own. Compare it with `config.json-example` and copy over anything new you want to use.

That should be it! Your latest version should now be working with whatever new fangled features were just added.

#### Version Information

You can check the version information for your installation of LightningLane-Live-LED by running `python3 version.py`.

The latest version of the software is available [here](https://github.com/jc214809/LightningLane-Live-LED/releases).

#### Time Zones
Make sure your Raspberry Pi's timezone is configured to your local time zone. They'll often have London time on them by default. You can change the timezone of your raspberry pi by running `sudo raspi-config`.

## Usage
The installation script adds a line to the top of `disney.py` to automatically pick up the virtual environment.
This means re-activating the environment (`source ./venv/bin/activate`) is not a requirement.

`sudo ./disney.py` Running as root is 100% an absolute must, or the matrix won't render.

**Adafruit HAT/Bonnet users: You must supply a command line flag:**

`sudo ./disney.py --led-gpio-mapping="adafruit-hat"`

See the Flags section below for more flags you can optionally provide.

### Running on Other Platforms

To run on other platforms by means of software emulation via `RGBMatrixEmulator`. When running via the emulator, you do not need to prepend your startup commands with `sudo`:

```sh
./disney.py
```

You can also force into emulation mode by using the `--emulated` flag:

```sh
./disney.py --emulated
```

When running in emulation mode, you can continue to use your existing command line flags as normal.

See [RGBMatrixEmulator](https://github.com/ty-porter/RGBMatrixEmulator) for emulator configuration options.

### Flags

You can configure your LED matrix with the same flags used in the [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) library. More information on these arguments can be found in the library documentation.
```
--led-rows                Display rows: 32 or 64. (Default: 32)
--led-cols                Panel columns. Typically 32 or 64. (Default: 32)
--led-chain               Daisy-chained boards. (Default: 1)
--led-parallel            For Plus-models or RPi2: parallel chains. 1..3. (Default: 1)
--led-pwm-bits            Bits used for PWM. Range 1..11. (Default: 11)
--led-brightness          Sets brightness level. Range: 1..100. (Default: 100)
--led-gpio-mapping        Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm
--led-scan-mode           Progressive or interlaced scan. 0 = Progressive, 1 = Interlaced. (Default: 1)
--led-pwm-lsb-nanoseconds Base time-unit for the on-time in the lowest significant bit in nanoseconds. (Default: 130)
--led-show-refresh        Shows the current refresh rate of the LED panel.
--led-slowdown-gpio       Slow down writing to GPIO. Range: 0..4. (Default: 1)
--led-no-hardware-pulse   Don't use hardware pin-pulse generation.
--led-rgb-sequence        Switch if your matrix has led colors swapped. (Default: RGB)
--led-panel-type          Chipset initialization for panels that need it: FM6126A or FM6127. (Default: none)
--led-pixel-mapper        Apply pixel mappers. e.g Rotate:90, U-mapper
--led-row-addr-type       0 = default; 1 = AB-addressed panels; 2 = direct row select; 3 = ABC-addressed panels. (Default: 0)
--led-multiplexing        Multiplexing type: 0 = direct; 1 = strip; 2 = checker; 3 = spiral; 4 = Z-strip; 5 = ZnMirrorZStripe; 6 = coreman; 7 = Kaler2Scan; 8 = ZStripeUneven. (Default: 0)
--led-limit-refresh       Limit refresh rate to this frequency in Hz. Useful to keep a constant refresh rate on loaded system. 0=no limit. Default: 0
--led-pwm-dither-bits     Time dithering of lower bits (Default: 0)
--emulated                Run in the software emulator, even on a Pi.
--drop-privileges         Force the matrix driver to drop root privileges after setup. (Default: false)
```

Each board's settings live in `boards.json`, keyed by the Pi's hostname, and a board picks its own at startup. To change one, edit its entry, commit, and update that board; there's nothing to change on the Pi itself, and its service needs no flags:

```json
"PlutoPi": {
  "led_rows": 32,
  "led_cols": 64,
  "led_gpio_mapping": "adafruit-hat-pwm",
  "led_slowdown_gpio": 2,
  "led_pixel_mapper": "Rotate:180",
  "led_brightness": 85
}
```

Settings are named like the flags with underscores. A board's `config.json` can override its preset in a `"matrix"` section of the same shape (`config.json-example` lists every setting as `null`, which overrides nothing), and a flag on the command line overrides both. Switches like `led_show_refresh` take `true` or `false`. An unknown name or a bad value stops the app with a message, like a bad flag. The startup log shows the result: `Board settings (boards.json preset PlutoPi): led_cols=64 (board PlutoPi), ...`.

To dim the board at night, add a `brightness_schedule` to `config.json`, shaped as Peloton-LED's (`null`, the default, keeps one brightness all day). It takes over from `led_brightness` while the app runs, by the board's clock, with brightness from 1 to 100; a day that runs past midnight works too. A broken schedule is warned about and ignored. The settings page sets it under Display.

```json
"brightness_schedule": {"day": 80, "night": 15, "day_start": "07:00", "night_start": "22:00"}
```

### Waveshare P5 64×32 panel

The Waveshare P5 64×32 panel labeled `P5(2121)-3264-16S-M5` and `HUB75-D` needs a panel initialization setting with this project. In our testing, the display stayed black with the default settings but worked with `--led-panel-type=FM6126A`. This flag selects a compatible initialization sequence; it does **not** mean the chips on the panel are FM6126A.

```bash
sudo ./disney.py \
  --led-rows=32 \
  --led-cols=64 \
  --led-chain=1 \
  --led-gpio-mapping=adafruit-hat-pwm \
  --led-slowdown-gpio=2 \
  --led-panel-type=FM6126A
```

| Option | Why it is used |
| --- | --- |
| `--led-rows=32 --led-cols=64` | Sets the panel’s 64×32 pixel resolution. |
| `--led-chain=1` | Configures one panel on the HUB75 connection. |
| `--led-gpio-mapping=adafruit-hat-pwm` | Uses the Adafruit HAT/Bonnet wiring with the GPIO 4-to-18 PWM modification. Use `adafruit-hat` if that modification is absent. |
| `--led-slowdown-gpio=2` | Slows GPIO timing to the setting that worked in our Pi test. |
| `--led-panel-type=FM6126A` | Sends the initialization sequence that made this particular panel light up. |

The panel also needs its own 5V power connection. `--led-panel-type` needs an rpi-rgb-led-matrix build that supports panel types; if startup logs "Your compiled RGB Matrix Library is out of date", rebuild the driver with `sudo ./LLL-install.sh -c -p -f`.

### WebSocket (Recommended)

Real-time WebSocket updates need a ThemeParks API key.

**Getting a key:**
1. Sign in at [ThemeParks.wiki](https://themeparks.wiki).
2. Open your [profile](https://themeparks.wiki/profile) and generate an API key.
3. Add it to the `websocket` section of `config.json`:

```json
"websocket": {
  "enabled": true,
  "api_key": "your-api-key-here"
}
```

With it, attraction status changes appear on the display within seconds. Set `enabled` to `false` to turn the WebSocket off and keep the key. Without a key (unset, empty, or the `<...>` placeholder), the app polls the REST API every 5 minutes, which needs no key; the WebSocket server closes connections that don't send one.

The app subscribes to each resort your parks belong to, once for attractions and once for shows, so restaurant updates never reach the board. Each resort uses two of the 15 subscriptions a key allows, so parks from up to seven resorts fit on one key.

A `config.json` from before this section, with a top-level `"themeparks_api_key"`, still works: the WebSocket uses that key until you move it into `websocket.api_key`.

#### Preview protocol (optional)

ThemeParks.wiki is testing a newer WebSocket protocol, "preview". Turn it on with `"protocol": "preview"` in the `websocket` section (the default is `"legacy"`):

```json
"websocket": {
  "enabled": true,
  "api_key": "your-api-key-here",
  "protocol": "preview"
}
```

With it:
- The board gets every ride's current status from the WebSocket when it connects, instead of a REST fetch at startup.
- After a dropped connection it picks up where it left off: the server replays the updates it missed. If it was gone too long, the server sends everything again.
- "Down" times count from when the ride actually went down.
- REST checks every ride every 30 minutes while the WebSocket is healthy (every 5 when it isn't), instead of every 5.

Preview isn't covered by ThemeParks.wiki's uptime promise yet and may change. Set `"protocol": "legacy"` to go back.

**One connection per board.** Each board (and each emulator run) holds one of your key's connections; the key's limit is in the log at startup (`key limits: {'maxConnections': ...}`). A board over the limit is refused (close code 4029); with preview it waits 10 minutes before trying again and runs on REST meanwhile. If you have more boards than connections, set `"enabled": false` on the extra one.

#### WebSocket Connection Health

The WebSocket connection is monitored and self-healing:
- A dead connection (network drop, server-side timeout) is detected within about 2 minutes and reconnected automatically.
- A connection that stays open but silently stops delivering updates is detected by a background watchdog and force-reconnected, as long as at least one configured park is currently operating.
- Every reconnect (whether from an error or the watchdog) catches up on anything missed during the outage: a REST refresh with the legacy protocol, the server's replay with preview.
- Reconnect attempts back off (5s, 10s, 20s, ... up to 60s) if the connection keeps failing quickly, so a persistent outage doesn't hammer the API.

You can watch this behavior in the logs (`logs/app.log`) — look for `WebSocket connected`, `WS heartbeat`, and `WebSocket disconnected; reconnecting in Ns` messages.

### Configuring Parks

By default the app shows all four Walt Disney World theme parks. You can configure any combination of parks from any ThemeParks Wiki destination in `config.json`:

```json
"parks": ["Magic Kingdom", "EPCOT", "Hollywood Studios", "Animal Kingdom", "Cedar Point"]
```

Leave the list empty to default to all Walt Disney World parks.

### Weather
The current weather at each park comes from OpenWeatherMap, which requires an API key, so you will need to take a quick minute to sign up for an account and copy your own API key into your `config.json`.

You can find the signup page for OpenWeatherMap at [https://home.openweathermap.org/users/sign_up](https://home.openweathermap.org/users/sign_up). Once logged in, you'll find an `API keys` tab where you'll find a default key was already created for you. You can copy this key and paste it into the `config.json` under `"weather"`, `"apikey"`.

There's nothing else to set: each park's location comes from the ThemeParks Wiki data.

### Trip Countdown
The countdown plays after the castle intro. List your trips in `config.json`:

```json
"trip_countdown": {
  "enabled": true,
  "trip_dates": [
    {"start": "2027-03-14", "end": "2027-03-19", "name": "Spring Break"},
    "2027-06-01"
  ]
}
```

- Each trip is either `{"start", "end", "name"}` (`end` and `name` optional) or just a start date. Dates are `YYYY-MM-DD`.
- The board shows one trip at a time: the trip under way, otherwise the next one. A later trip doesn't appear until the one before it has finished.
- Before a trip: `N DAYS TO <name>`, then `DISNEY TOMORROW` the day before and `IT'S DISNEY DAY!` on the first day. A name too wide for the board shows as `DISNEY`.
- **With an end date:** `DAY 2 OF 6` and so on through the last day, then `WELCOME HOME!` for 2 days, then the next trip.
- **With only a start date:** `HAVE A MAGICAL TRIP!` for 7 days after the start, then the next trip. Give a trip an end date to have the board count its days and move on when it's over.
- A trip the board can't read (a bad date, an end before the start) is skipped, with a warning in the log. The startup log lists the trips it read (`Configured trips: ...`).

### Sound
The board can play the fireworks soundtrack while its castle fireworks run. For Happily Ever After it plays the whole show, about 18 minutes, with the fireworks following the music: each part's colours, quiet moments, a wishing star, rising lanterns, the castle on fire, and a white flash on the last note. On a Pi this needs a **USB sound card** (with an OTG adapter on a Pi Zero) and a powered speaker. The Pi's own audio can't be used: it shares hardware with the LED matrix, and the installer turns it off. I2S amp boards clash with the RGB Matrix Bonnet's pins. An emulator run on a Mac plays through the Mac's speakers. Parts lists and hook-up diagrams (a plug-in USB speaker, or a small speaker and amp built into the case) are in [docs/hardware/SOUND.md](docs/hardware/SOUND.md). A power button on the back that shuts the Pi down safely and starts it again is in [docs/hardware/POWER.md](docs/hardware/POWER.md).

1. Put WAV files in `sounds/` (see `sounds/README.md` for the names). They're gitignored, so copy them to each board.
2. Turn sound on in `config.json`:

```json
"sound": {
  "enabled": true,
  "device": null,
  "quiet_hours": {"start": "22:00", "end": "08:00"}
}
```

- `device`: the ALSA device to play on, like `"plughw:1,0"` (`aplay -l` lists them). `null` uses the default, which is usually the USB card once the onboard audio is off.
- `quiet_hours`: no sound between these times, in the board's local time. Leave it out for no quiet hours. A broken value turns sound off.
- Set the volume on the Pi with `alsamixer`.
- `shows` lists the fireworks shows you want to change, one entry per show:
  ```json
  "shows": [
    {"name": "Happily Ever After", "enabled": true, "version": "v2"},
    {"name": "Disney's Not-So-Spooky Spectacular", "enabled": false}
  ]
  ```
  Only `name` is required. A show not listed, or listed without a field, is `enabled` and `"default"`. `"version": "default"` is the castle fireworks (no title) for five minutes from the showtime, with `sounds/fireworks.wav` if there is one. `"v1"` or `"v2"` plays a scored show's whole synced version in that look, about 18 minutes for Happily Ever After, with its own music (`sounds/happily-ever-after.wav`). `"enabled": false` means the board never cuts in for that show. Only Happily Ever After has a score so far; the party shows are always the default.
- To hear a show now instead of waiting for showtime, add `"force": true` to its entry in `shows` (like `{"name": "Happily Ever After", "version": "v2", "force": true}`, or a party's show, like `{"name": "Disney's Not-So-Spooky Spectacular", "force": true}`) and restart the service: the board plays it once at start-up, with its sound, then carries on as usual. Restart again to replay it, and remove `"force"` when done. The old top-level `"force_show": "<name>"` still works, with a warning.

## Sources and Credits
This project relies on:
* [ThemeParks.wiki](https://themeparks.wiki): every park, attraction, wait time, showtime and schedule on the board comes from its free API and live WebSocket feed. Huge thanks to the ThemeParks.wiki project for building and running it. If this board is useful to you, consider supporting them.
* [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix), the library used for making everything work with the LED board.
* [OpenWeatherMap](https://openweathermap.org), for the weather at each park.

### Accuracy Disclaimer
The API uses realtime data but could change at any point.

## Help and Contributing
If you run into any issues and have steps to reproduce, open an issue. If you have a feature request, open an issue. If you want to contribute a small to medium sized change, open a pull request. If you want to contribute a new feature, open an issue first before opening a PR.

### Updating Dependencies

Edit `requirements.txt` (what the boards need) and the `dependencies` list in `pyproject.toml` by hand, and keep them in sync. Test tools go in `requirements-dev.txt`. Don't use `pipreqs`: it rewrites `requirements.txt` from imports and drops the version caps the boards rely on (such as `Pillow<12`).

### Running Tests

Unit tests are written with `pytest`. Install the app plus the test
tools (`pip install -r requirements-dev.txt`), then run the entire test
suite from the repository root directory with:

```sh
pytest
```

## Licensing
This project as of v0.1.0 uses the GNU Public License. If you intend to sell these, the code must remain open source.

## Other Cool Projects
The original version of this board

Inspired by this board project MLB-LED-Scoreboard [here](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard),also check out the [NHL scoreboard](https://github.com/riffnshred/nhl-led-scoreboard) 🏒
