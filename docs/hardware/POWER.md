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

Four wires to free pins on the Pi's header. The RGB Matrix Bonnet doesn't use any of them (see
Adafruit's [Bonnet pinouts](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/pinouts)).
The power supply's two wires stay as they are.

```
 button switch ──► GPIO 3   (header pin 5)    shutdown, and wake from shutdown
 button switch ──► GND      (header pin 6)
 button LED +  ──► GPIO 25  (header pin 22)   on while Linux runs
 button LED −  ──► GND      (header pin 9)

 Header pins, seen from above with the SD card on the left:

   pin 1  3V3   ● ●  5V    pin 2
   pin 3  GPIO2 ● ●  5V    pin 4
   pin 5  GPIO3 ● ●  GND   pin 6     ◄── button switch
   pin 7  GPIO4 ● ●  GPIO14
   pin 9  GND   ● ●  GPIO15          ◄── LED −  (pin 9)
          ...
   pin 21 GPIO9 ● ●  GPIO25 pin 22   ◄── LED +  (pin 22)
```

The Bonnet sits on the header, so solder the wires to the Pi's header pins from underneath. On a Pi
Zero the joints are on the bottom of the board, and the numbering is mirrored from below.

GPIO 3 is the I2C clock pin. These boards don't use I2C, but if `dtparam=i2c_arm=on` is in
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
