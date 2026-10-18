# Power button

One push button on the back of the board that shuts the Pi down safely, and starts it again. It has
a light that shows when the Pi is running. Linux on the Pi does all of this with two lines in
`config.txt`, so the app has no code for it and there's no shutdown script to run.

- **Press while it's running:** the Pi shuts down safely. The panel goes dark, the light goes out when
  the shutdown has finished, and the board draws only a trickle.
- **Press while it's shut down:** the Pi boots, as if it had just been plugged in. The light comes on
  a few seconds after the press, when Linux starts, well before the panel's first picture (up to
  about 30 s on a Pi Zero).

Power is never fully cut: the shut-down Pi and the Bonnet stay connected to the supply. Unplug the
supply to cut it completely.

## Parts

A 16 mm **momentary** (push-and-release, not latching) metal button with a **green or red** LED ring
rated 3-6 V, such as Adafruit's 16 mm momentary with a green ring ([560](https://www.adafruit.com/product/560)).

The Pi's pins run at 3.3 V. Green and red rings light at that voltage. Blue and white ones need about
3 V just to glow, so they'd be very dim. Check its brightness on 3.3 V before mounting it.

## Wiring

Four wires to the Bonnet's **breakout pads**: the labelled row of pads just under its 40-pin header.
They carry the Pi's pins, so nothing has to be soldered to the Pi itself. The power supply's two
wires stay as they are. The [wiring diagrams](README.md#wiring-diagrams) show it with everything
else on the board.

```
 button switch ──► SCL pad  (GPIO 3)    shutdown, and wake from shutdown
 button switch ──► GND pad
 button LED +  ──► 25 pad   (GPIO 25)   on while Linux runs
 button LED −  ──► GND pad  (the same pad: both ground wires go in it)

 The breakout row, as printed on the Bonnet. A signal under a pad marks one of the Bonnet's own;
 the 5V and GND pads sit below the first three (both ground wires go in GND):

     SDA SCL  TX  RX  4   17  18  27  22  23  24  25  MO  MI CLK CE0 CE1  5   6   12  13  16  19  20  21
      ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
                      OE CLK      C   A   B2  E                           R1  B1  R2  G1  G2      D  LAT
 5V   ●   ●   ● GND
          ▲                                       ▲
       switch                                  LED +
```

What each pad does:

- **SCL, GPIO 3: shutdown and wake.** A shut-down Pi still watches this one pin, and shorting it
  to ground boots it again. That's why one button can do both. No other pin wakes the Pi.
- **25, GPIO 25: the light.** Linux turns it on at boot and off once the shutdown has finished,
  so a dark light means it's safe to unplug. Any free pad would work; 25 is one the Bonnet doesn't use.
- **GND: one ground for both.** The breakout has one GND pad, and the switch's and the LED's ground
  wires share it: twist them together and solder them into it. Every ground on the Pi is the same
  ground, so they don't need separate pads.
- **4 and 18: the quality jumper.** The short wire soldered between these two pads (see the
  [hardware guide](README.md)). The button doesn't touch them.

Don't solder to a pad with a signal printed under it (OE, CLK, LAT, A–E, R1–B2): the Bonnet uses
those to drive the panel. MO, MI, CLK, CE0 and CE1 are the Pi's SPI pins and are free; that CLK isn't
the panel's.

SCL, GPIO 3, is the I2C clock pin. These boards don't use I2C, but if `dtparam=i2c_arm=on` is in
`config.txt`, the button won't work.

## Setup

On the board (Raspberry Pi OS Bookworm keeps `config.txt` in `/boot/firmware/`):

```sh
# 1. Back up config.txt, and check I2C is off (this should print nothing)
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.bak
grep -n "^dtparam=i2c_arm=on" /boot/firmware/config.txt

# 2. Add the button and its light, once, under [all] so they apply to every Pi model
grep -q "^dtoverlay=gpio-shutdown" /boot/firmware/config.txt || printf '\n[all]\ndtoverlay=gpio-shutdown\ndtoverlay=gpio-led,gpio=25,label=power,trigger=default-on\n' | sudo tee -a /boot/firmware/config.txt

# 3. Pi 4 only: wake on GPIO 3 must be on (the default). Expect WAKE_ON_GPIO=1 and POWER_OFF_ON_HALT=0, or neither line
rpi-eeprom-config | grep -E "WAKE_ON_GPIO|POWER_OFF_ON_HALT"

# 4. Reboot to load them
sudo reboot
```

After the reboot, check:

```sh
tail -n 4 /boot/firmware/config.txt          # the [all] block and the two dtoverlay lines
ls /sys/class/leds/                          # lists "power"
cat /sys/class/leds/power/brightness         # non-zero: the light is on
```

Then press the button once. The panel goes dark and the light goes out within about 15 s. Press it
again, and the light comes back within a few seconds while the Pi boots.

To undo it, restore the backup and reboot:
`sudo cp /boot/firmware/config.txt.bak /boot/firmware/config.txt && sudo reboot`.
