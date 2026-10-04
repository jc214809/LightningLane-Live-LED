# LightningLane-Live-LED
![Tests](https://github.com/jc214809/LightningLane-Live-LED/actions/workflows/coverage.yml/badge.svg) [![codecov](https://codecov.io/gh/jc214809/LightningLane-Live-LED/graph/badge.svg)](https://codecov.io/gh/jc214809/LightningLane-Live-LED)


LightningLane-Live-LED is a Python application designed to fetch and display wait times for attractions at Walt Disney World and other theme parks on an LED matrix display. It retrieves park and attraction data from the [ThemeParks Wiki API](https://api.themeparks.wiki) and dynamically renders ride information—including park names, ride names, and wait times—onto an LED matrix. The application supports both actual hardware and an emulator for testing purposes.

## Features

- **API Integration:**  
  Retrieves park data and attraction details for Walt Disney World, Cedar Point, Kings Island, and any other destination supported by the ThemeParks Wiki API. Parks are configured by name in `config.json`.
- **Real-Time WebSocket Updates:**  
  With a ThemeParks API key configured (see [below](#websocket-recommended)), live wait times arrive over a persistent WebSocket connection (`wss://api.themeparks.wiki/v1/live`) as attraction statuses change. The app performs an initial REST fetch at startup to populate all data, then the WebSocket delivers ongoing updates. The connection is self-healing: a dead or silently-stalled connection is detected and reconnected automatically (typically within 2 minutes), with a REST refresh triggered afterward to catch any changes missed during the outage.
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

### Hardware Assembly
For users interested in physical hardware setup, please refer to the [inspiration project MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard).

If you'd like to see support for another set of board dimensions, or have design suggestions for an existing one, feel free to file an issue!

## Software Installation

**Pi's with known issues**
 * Raspberry Pi Zero has had numerous reports of slowness and unreliability during installation and running with other software.
 * HOWEVER, I was able to run this project in a headless version on Pi OS on a Pi Zero 2 W

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
-a, --skip-all          Skip all dependencies and config installation (equivalent to -c -p -m -v).
-c, --skip-config       Skip updating JSON configuration files. (Currently no effect: the installer never changes config.json.)
-m, --skip-matrix       Skip building matrix driver dependency. Video display will default to emulator mode.
-p, --skip-python       Skip Python 3 installation. Requires manual Python 3 setup if not already installed.

-v, --no-venv           Do not create a virtual environment for the dependencies.
-e, --emulator-only     Do not install dependencies under sudo. Skips building matrix dependencies (equivalent to -m)
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
--led-rows                Display rows. 16 for 16x32, 32 for 32x32. (Default: 32)
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
--emulated                Force the scoreboard to run in software emulation mode.
--drop-privileges         Force the matrix driver to drop root privileges after setup. (Default: false)
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

#### WebSocket Connection Health

The WebSocket connection is monitored and self-healing:
- A dead connection (network drop, server-side timeout) is detected within about 2 minutes and reconnected automatically.
- A connection that stays open but silently stops delivering updates is detected by a background watchdog and force-reconnected, as long as at least one configured park is currently operating.
- Every reconnect (whether from an error or the watchdog) triggers a REST refresh so the display catches up on anything missed during the outage.
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
