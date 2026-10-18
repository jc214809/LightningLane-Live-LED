# Sound hardware

How to give a board a speaker, with parts from Adafruit. Software setup (WAV files, `config.json`'s
`sound` section, quiet hours) is in the main [README](../../README.md#sound).

**Why USB:** the Pi's own audio can't be used. It shares PWM hardware with the LED matrix, and
`LLL-install.sh` turns it off. I2S amp boards (like the MAX98357A) need GPIO 21, which the RGB Matrix
Bonnet uses for its latch line. So sound goes out over USB.

## Recommended: a USB speaker

The cheapest setup, the least work and the cleanest sound. The speaker has its own sound card, so
it's one plug, with no amp, no soldering and no wiring.

| Board | Parts | Cost (Oct 2026) |
|---|---|---|
| Pi 4 | Mini External USB Stereo Speaker ([3369](https://www.adafruit.com/product/3369)) | $12.50 |
| Pi Zero / Zero 2 W | Speaker 3369 + USB OTG Host Cable ([1099](https://www.adafruit.com/product/1099)) | $15.00 |

```
  Pi 4
 ┌──────────────────────┐
 │  RGB Matrix Bonnet   │
 │                 USB-A├──────── USB cable ───────► [ USB stereo speaker 3369 ]
 └──────────────────────┘                             (power + audio, 2 x 2 W)

  Pi Zero / Zero 2 W
 ┌──────────────────────┐
 │  RGB Matrix Bonnet   │      OTG cable 1099
 │     micro-USB (data) ├────► micro-B ═══ USB-A female ◄──── [ USB stereo speaker 3369 ]
 └──────────────────────┘
   (the Zero's data port, not its PWR port)
```

- On a Zero, use the flexible OTG **cable**, not a rigid micro-USB adapter. Fitting a rigid adapter
  into a tight case once cracked a board's micro SD card, which sits at the same end.
- Then: `aplay -l` to find the card, and set `"device": "plughw:1,0"` in `config.json`'s `sound`
  section, with the card number `aplay -l` shows. `null` usually works too, since it's the only
  sound card once the onboard audio is off. Set the volume with `alsamixer`.

## Build it in: a small speaker inside the case

For hiding the speaker inside a printed case. It costs about the same and needs some soldering. The
amp is also the part most likely to pick up buzz from the LED panel.

| Part | Adafruit | Cost (Oct 2026) |
|---|---|---|
| USB Audio Adapter | [1475](https://www.adafruit.com/product/1475) | $4.95 |
| Mono 2.5 W Class D amp, PAM8302 | [2130](https://www.adafruit.com/product/2130) | $3.95 |
| 36 mm 8 Ω 2 W speaker | [6486](https://www.adafruit.com/product/6486) | $1.95 |
| 3.5 mm stereo plug terminal block (no soldering at the jack) | [2790](https://www.adafruit.com/product/2790) | about $3 |
| USB OTG Host Cable, Pi Zero only | [1099](https://www.adafruit.com/product/1099) | $2.50 |
| Hook-up wire, 22-26 AWG | any | |

About $14-15 per board, plus the OTG cable on a Zero. The PAM8302 gives about 1.5 W into the 8 Ω
speaker, under its 2 W rating.

```
                                   ┌──────────────────────────┐
  Pi USB ──► USB Audio Adapter ──► │ 3.5 mm plug terminal     │
             (1475)  3.5 mm out    │ block (2790)             │
                                   │   T (tip, left)    ●─────┼──┐
                                   │   R (ring, right)  ●     │  │  left only: see "Mono" below
                                   │   S (sleeve, GND)  ●─────┼──┼──┐
                                   └──────────────────────────┘  │  │
                                                                 │  │
                                   ┌──────────────────────────┐  │  │
                                   │ PAM8302 amp (2130)       │  │  │
                                   │   A+  ◄──────────────────┼──┘  │
                                   │   A-  ◄──────────────────┼─────┘  audio ground
                                   │   SD  (unwired: amp on)  │
   Bonnet 5V screw terminal ──────►│   VIN                    │
   Bonnet GND screw terminal ─────►│   GND                    │
                                   │                          │      ┌──────────────────┐
                                   │   speaker  +  ●──────────┼─────►│ + 36 mm speaker  │
                                   │   terminal -  ●──────────┼─────►│ -   (6486)       │
                                   └──────────────────────────┘      └──────────────────┘
```

- **Power:** the amp's VIN and GND go to the Bonnet's 5 V power screw terminal, alongside the
  supply's wires. That's the same 5 V that runs the Pi and the panel. The Bonnet covers the Pi's GPIO
  header, so the header's 5 V pins aren't reachable.
- **Input:** the PAM8302's input is differential. For a headphone-style source, wire A+ to the
  signal and A- to the sleeve (ground).
- **Soldering:** the amp's speaker screw terminal and its header come loose in the bag. Solder the
  terminal on, then solder wires to A+, A-, VIN and GND (or use the header).
- **Gain:** start with the amp's trim pot low and the ALSA volume at about 70%, then raise the pot
  until it's loud enough without distorting.

### Mono

The show soundtrack is stereo, and this speaker is one channel. Wiring only the tip plays the left
channel and drops anything mixed only to the right. Mix both channels into one in ALSA instead, which
needs no extra parts. Add this to `/etc/asound.conf`, with the card number from `aplay -l`:

```
pcm.mono {
    type route
    slave.pcm "plughw:1,0"
    ttable.0.0 0.5
    ttable.1.0 0.5
}
```

Then set `"device": "mono"` in `config.json`'s `sound` section, and check it with
`aplay -D mono sounds/happily-ever-after.wav`. Don't wire the ring to A- to get both channels: a
differential input plays left minus right, which cancels everything mixed to the centre, like the
vocals.

### Buzz and whine

The LED panel pulls large, fast-changing currents, and that can leak into the amp as a buzz that
follows the picture.
- Keep the wires short, and twist the speaker pair together and the power pair together.
- Run the amp's power wires straight from the Bonnet's screw terminal, not daisy-chained off the panel.
- If it still hums, a USB ground-loop isolator between the Pi and the audio adapter usually fixes it,
  or power the amp from its own clean 5 V.

## Printing a case

PLA is fine for both setups: neither the speaker nor the PAM8302 gets warm. Keep the parts away from
the Pi's hot spots. For the 36 mm speaker, put a grille of holes in front of the cone and a small
sealed space behind it: a driver this size sounds fuller in a closed box than in open air.
