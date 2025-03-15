# LightningLane-Live-LED

This project is a Python application designed to fetch and display wait times for attractions at Walt Disney World on an LED matrix display. It retrieves park and attraction data from the [ThemeParks Wiki API](https://api.themeparks.wiki) and dynamically renders ride information—including park names, ride names, and wait times—onto an LED matrix. The application supports both actual hardware and an emulator for testing purposes.

## Features

- **API Integration:**  
  Retrieves Walt Disney World park data and attraction details using synchronous (`requests`) and asynchronous (`aiohttp`) HTTP requests.
- **Live Data Updates:**  
  Uses a background thread to periodically update live wait times for attractions.
- **Dynamic Display Rendering:**  
  Renders park names and ride information with dynamic text wrapping and spacing on an LED matrix.
- **Emulation Mode:**  
  Supports running in emulation mode via `RGBMatrixEmulator` for testing without physical hardware.
- **Detailed Logging:**  
  Provides extensive logging for monitoring application behavior and debugging issues.

## Prerequisites

- **Python 3.7+**
- **Pip** package manager


**Currently supported boards:**
 * 64x32
 * 64x64

## Installation
### Hardware Assembly
Please refer to my inspiration project MLB-LED-Scoreboard [here](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard).

If you'd like to see support for another set of board dimensions, or have design suggestions for an existing one, file an issue!

For hardware setups, ensure you have an LED matrix display (or the appropriate emulator) available.

## Installation

**Pi's with known issues**
 * Raspberry Pi Zero has had numerous reports of slowness and unreliability during installation and running the software.

### Software Installation
#### Requirements
You need Git for cloning this repo and PIP for installing the software.
```
sudo apt-get update
sudo apt-get install git python3-pip
```

### Using a Virtual Environment (Recommended)

#### Installing the scoreboard software
This installation process will take about 10-15 minutes. Raspberry Pis aren't the fastest of computers, so be patient!

   ```bash
   git clone https://github.com/jc24809/LED-LightningLane-Live.git
   cd LED-LightningLane-Live/
   sudo ./install.sh
   ```

This will create a Python Virtual Environment and install all of the required dependencies. The
virtual environment will be located at `LightningLane-Live-LED/venv/`.

This will install the rgbmatrix binaries, which we get from [another open source library](https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python#building). It controls the actual rendering of the scoreboard onto the LEDs. If you're curious, you can read through their documentation on how all of the lower level stuff works.

It will also install the following python libraries that are required for certain parts of the scoreboard to function.

* [RGBMatrixEmulator](https://github.com/ty-porter/RGBMatrixEmulator): The emulation library for the matrix display. Useful for running on MacOS or Linux, or for development.

Future Enhancements:
* [pyowm](https://github.com/csparpa/pyowm): OpenWeatherMap API interactions. We use this to get the local weather for display on the offday screen. For more information on how to finish setting up the weather, visit the [weather section](#weather) of this README.

#### Customizing the Installation

Additional flags are available for customizing your install:

```
-a, --skip-all          Skip all dependencies and config installation (equivalent to -c -p -m).
-c, --skip-config       Skip updating JSON configuration files.
-m, --skip-matrix       Skip building matrix driver dependency. Video display will default to emulator mode.
-p, --skip-python       Skip Python 3 installation. Requires manual Python 3 setup if not already installed.

-v, --no-venv           Do not create a virtual environment for the dependencies.
-e, --emulator-only     Do not install dependencies under sudo. Skips building matrix dependencies (equivalent to -m)
-d, --driver            Specify a branch name or commit SHA for the rpi-rgb-led-matrix library. (Optional. Defaults may change.)

-h, --help              Display this help message
```

#### Installation on Non-Raspberry Pi Hardware

The installation script is designed for physical hardware. When attempting to install it on other platforms, you should not use `sudo` to install the dependencies. In addition, you can pass the `--emulator-only` argument to skip installation steps that aren't required.

```
sh LLL-install.sh --emulator-only
```

#### Updating
* Run `git pull` in your LightningLane-Live-LED folder to fetch the latest changes. A lot of the time, this will be enough, but if something seems broken:
    * **Re-run the install file**. Run `sudo ./LLL-install.sh` again. Any additional dependencies that were added with the update will be installed this way. If you are moving to a new major release version, answer "Y" to have it make you a new config file.
    * **Check your custom layout/color files if you made any**. There's a good chance some new keys were added to the layout and color files. These changes should just merge right in with the customized .json file you have but you might want to look at the new .json.example files and see if there's anything new you want to customize.

That should be it! Your latest version should now be working with whatever new fangled features were just added.

#### Version Information

You can check the version information for your installation of LightningLane-Live-LED by running `python3 version.py`.

The latest version of the software is available [here](https://github.com/MLB-LED-Scoreboard/LightningLane-Live-LED/releases).

#### Time Zones
Make sure your Raspberry Pi's timezone is configured to your local time zone. They'll often have London time on them by default. You can change the timezone of your raspberry pi by running `sudo raspi-config`.

## Usage
The installation script adds a line to the top of `Disney.py` to automatically pick up the virtual environment.
This means re-activating the environment (`source ./venv/bin/activate`) is not a requirement.

`sudo ./Disney.py` Running as root is 100% an absolute must, or the matrix won't render.

**Adafruit HAT/Bonnet users: You must supply a command line flag:**

`sudo ./Disney.py --led-gpio-mapping="adafruit-hat"`

See the Flags section below for more flags you can optionally provide.

### Running on Other Platforms

The scoreboard can run on other platforms by means of software emulation via `RGBMatrixEmulator`. When running via the emulator, you do not need to prepend your startup commands with `sudo`:

```sh
./Disney.py
```

You can also force the scoreboard into emulation mode by using the `--emulated` flag:

```sh
./Disney.py --emulated
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
--led-pwm-lsb-nanosecond  Base time-unit for the on-time in the lowest significant bit in nanoseconds. (Default: 130)
--led-show-refresh        Shows the current refresh rate of the LED panel.
        Slow down writing to GPIO. Range: 0..4. (Default: 1)
--led-no-hardware-pulse   Don't use hardware pin-pulse generation.
--led-rgb-sequence        Switch if your matrix has led colors swapped. (Default: RGB)
--led-pixel-mapper        Apply pixel mappers. e.g Rotate:90, U-mapper
--led-row-addr-type       0 = default; 1 = AB-addressed panels. (Default: 0)
--led-multiplexing        Multiplexing type: 0 = direct; 1 = strip; 2 = checker; 3 = spiral; 4 = Z-strip; 5 = ZnMirrorZStripe; 6 = coreman; 7 = Kaler2Scan; 8 = ZStripeUneven. (Default: 0)
--led-limit-refresh       Limit refresh rate to this frequency in Hz. Useful to keep a constant refresh rate on loaded system. 0=no limit. Default: 0
--led-pwm-dither-bits     Time dithering of lower bits (Default: 0)
--config                  Specify a configuration file name other, omitting json xtn (Default: config)
--emulated                Force the scoreboard to run in software emulation mode.
--drop-privileges         Force the matrix driver to drop root privileges after setup. (Default: true)
```

## Personalization
If you're feeling adventurous (and we highly encourage it!), the sections below outline how you can truly personalize your scoreboard and make it your own!
### Custom Board Layout
You have the ability to customize the way things are placed on the board (maybe you would prefer to see scrolling text for a pregame a bit higher or lower). See the `coordinates/` directory for more information.

### Custom Colors
You have the ability to customize the colors of everything on the board. See the `colors/` directory for more information.

### Weather
This scoreboard will use a weather API to gather weather information at various times. This information is displayed on your teams' offdays for your area and also displayed during each game's pregame information. The weather API we use is from OpenWeatherMaps. OpenWeatherMaps API requires an API key to fetch this data so you will need to take a quick minute to sign up for an account and copy your own API key into your `config.json`.

You can find the signup page for OpenWeatherMaps at [https://home.openweathermap.org/users/sign_up](https://home.openweathermap.org/users/sign_up). Once logged in, you'll find an `API keys` tab where you'll find a default key was already created for you. You can copy this key and paste it into the `config.json` under `"weather"`, `"apikey"`.

You can change the location used by entering your city, state, and country code separated by commas. If you wish to use metric measurements, set the `"metric"` option to `true`.

## Sources
This project relies on two libraries:
[MLB-StatsAPI](https://pypi.org/project/MLB-StatsAPI/) is the Python library used for retrieving live game data.
[rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) is the library used for making everything work with the LED board.

### Accuracy Disclaimer
The scoreboard updates frequently, but it cannot retrieve information that MLB has not yet made available. If something is odd or it seems behind, the first suspect is the MLB web API.

## Help and Contributing
If you run into any issues and have steps to reproduce, open an issue. If you have a feature request, open an issue. If you want to contribute a small to medium sized change, open a pull request. If you want to contribute a new feature, open an issue first before opening a PR.

### Updating Dependencies

Dependencies requirements are managed using `pipreqs`. If you are adding or making a change to a dependency (such as updating its version), make sure to update the requirements file with `pipreqs`:

```sh
# If not already installed
pip3 install pipreqs

pipreqs . --force
```

## Licensing
This project as of v1.1.0 uses the GNU Public License. If you intend to sell these, the code must remain open source.

## Other Cool Projects
The original version of this board

Inspired by this board, check out the [NHL scoreboard](https://github.com/riffnshred/nhl-led-scoreboard) 🏒




cp -r  /LightningLane-Live-LED/assets /LED-LightningLane-Live

Putty Command
64x64
sudo /home/admin/LED-LightningLane-Live/venv/bin/python Disney.py --led-cols=64 --led-rows=64 --led-gpio-mapping=adafruit-hat-pwm --led-slowdown-gpio=2

64x32
sudo /home/admin/LED-LightningLane-Live/venv/bin/python Disney.py --led-cols=64 --led-rows=32 --led-gpio-mapping=adafruit-hat-pwm --led-slowdown-gpio=2
