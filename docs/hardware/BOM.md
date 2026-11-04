# Bill of materials

An example parts list for one board, from what our boards use. ★ marks a part from our own builds;
the rest are the recommended or tested choices from the other hardware guides. Prices are from Oct
2026 where we have them; a blank one hasn't been checked. How everything connects is in the
[wiring diagrams](README.md#wiring-diagrams).

## Core

| Part | Qty | Example | Price | Notes |
|---|---|---|---|---|
| Raspberry Pi | 1 | Raspberry Pi 4 ★ (Disneypi), or Pi Zero 2 W ★ (TinyPi; MickeyPi, PlutoPi, ZeroPi are Zeros) | | A Pi 4 is fastest; a Zero boots slowly and runs the busiest animations slower. |
| micro SD card | 1 | 16 GB or more | | Raspberry Pi OS Bookworm (Lite is enough). |
| RGB Matrix Bonnet | 1 | Adafruit RGB Matrix Bonnet ★ ([3211](https://www.adafruit.com/product/3211)) | | Solder the 4–18 quality jumper (below). |
| HUB75 LED panel | 1 | 64x32 or 64x64, e.g. a Waveshare P5 64x32 | | Ribbon cable and panel power lead usually come with it. |
| 5 V power supply, 2.1 mm centre-positive plug | 1 | | | 64x32: about 3 A. 64x64: 4 A or more. |
| Hook-up wire for the 4–18 jumper | 1 short piece | 22–26 AWG | | Soldered between the Bonnet's **4** and **18** breakout pads. Run `--led-gpio-mapping=adafruit-hat-pwm`. |
| Case | 1 | 3D-printed, PLA ★ | | Keep PLA off the Pi's hottest spots. |

## Power in the back of the case

| Part | Qty | Example | Price | Notes |
|---|---|---|---|---|
| Panel-mount DC jack | 1 | Adafruit Panel Mount 2.1mm DC barrel jack ★ ([610](https://www.adafruit.com/product/610)) | $2.95 | For walls up to 8 mm thick. Three solder tabs: centre pin, sleeve, switch (left empty). |
| DC cord with a 2.1 mm centre-positive plug | 1 | any ★ | | Cut off the far end; solder its wires to the jack, plug it into the Bonnet's 5V In. Rated for the supply's current, 20 AWG or thicker. |

## Power button (optional)

| Part | Qty | Example | Price | Notes |
|---|---|---|---|---|
| 12 mm LED push button, pre-wired | 1 | STARELO 12mm latching LED push button, blue, 5-pack ★ ([Amazon B09YTWR467](https://www.amazon.com/dp/B09YTWR467)) | | Wires: two blue (the switch), red (LED +), black (LED −). **Latching** (push on, push off), so it doesn't fit POWER.md's press-to-shutdown setup; it needs the on/off toggle setup (`dtoverlay=gpio-shutdown,active_low=0`: in = on, out = off), not yet in POWER.md or tested on a board. Its LED is built for 12 V, so it's likely dim or dark on a Pi pin. 12 mm mounting hole. |
| or: 16 mm momentary button, green LED ring | 1 | Adafruit [560](https://www.adafruit.com/product/560) | | The button POWER.md was written for: press to shut down, press to wake; the ring lights on 3.3 V. 16 mm hole. |

## Sound (optional): option A, a USB speaker

| Part | Qty | Example | Price | Notes |
|---|---|---|---|---|
| Mini USB stereo speaker | 1 | Adafruit [3369](https://www.adafruit.com/product/3369) | $12.50 | Power and sound over one USB cable. |
| USB OTG host cable, Pi Zero only | 1 | Adafruit [1099](https://www.adafruit.com/product/1099) | $2.50 | Into the Zero's USB port. A flexible cable, not a rigid adapter. |

## Sound (optional): option B, a speaker built into the case

| Part | Qty | Example | Price | Notes |
|---|---|---|---|---|
| USB audio adapter | 1 | Adafruit [1475](https://www.adafruit.com/product/1475) | $4.95 | |
| Mono 2.5 W class D amp, PAM8302 | 1 | Adafruit [2130](https://www.adafruit.com/product/2130) | $3.95 | Powered from the Bonnet's 5V Out terminal. |
| 36 mm 8 Ω 2 W speaker | 1 | Adafruit [6486](https://www.adafruit.com/product/6486) | $1.95 | |
| 3.5 mm stereo plug terminal block | 1 | Adafruit [2790](https://www.adafruit.com/product/2790) | about $3 | |
| USB OTG host cable, Pi Zero only | 1 | Adafruit [1099](https://www.adafruit.com/product/1099) | $2.50 | |
| Hook-up wire | | 22–26 AWG | | |

Details for the sound parts are in [SOUND.md](SOUND.md), and for the button in [POWER.md](POWER.md).
