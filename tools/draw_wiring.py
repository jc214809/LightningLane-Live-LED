"""Draws the wiring diagrams in docs/hardware: wiring-pi4.svg and wiring-pi-zero.svg.

Edit the drawing here, never the SVGs, then run `python3 tools/draw_wiring.py`
(tests/tools/test_draw_wiring.py fails until the SVGs match). The Pis are to scale from their
mechanical drawings (6 px per mm, the 40-pin header along the top edge, pin 1 on the left); the
Bonnet's parts are placed roughly and the panel isn't to scale.
"""
import os
import sys

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "hardware")
FILES = {"wiring-pi4.svg": False, "wiring-pi-zero.svg": True}  # name: is it the Zero

S = 6  # px per mm for the Pi and the Bonnet
FONT = "Helvetica, Arial, sans-serif"
C = dict(text="#1d1d1f", dim="#5f6368", pcb="#1f7a4a", pcb_edge="#145c36", bonnet="#26282b",
         metal="#c9ccd1", metal_edge="#8a8f96", panel="#3b3e43", red="#d62828", gnd="#1d1d1f",
         yellow="#e0a800", green="#2a9d3a", blue="#1d6fd6", cable="#5b5f66", ribbon="#a3a7ad",
         gold="#d4a72c", note="#fff7e0", note_edge="#e6c46a")

out = []


def add(s):
    out.append(s)


def text(x, y, s, size=14, anchor="start", weight="normal", color=None, italic=False):
    style = ' font-style="italic"' if italic else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}"'
        f' fill="{color or C["text"]}"{style}>{s}</text>')


def rect(x, y, w, h, fill, stroke="none", sw=1, rx=0, dash=None, opacity=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' fill-opacity="{opacity}"' if opacity is not None else ""
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{o}'
        f' stroke="{stroke}" stroke-width="{sw}"{d}/>')


def circle(x, y, r, fill, stroke="none", sw=1):
    add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def wire(points, color, width=4, dash=None, arrow=False):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = ' marker-end="url(#arrow)"' if arrow else ""
    if color == C["gnd"]:  # a light edge so black wires read on dark boards
        add(f'<polyline points="{pts}" fill="none" stroke="#ffffff" stroke-width="{width + 2}"'
            f' stroke-linejoin="round" stroke-linecap="round"{d}/>')
    add(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"'
        f' stroke-linejoin="round" stroke-linecap="round"{d}{m}/>')


def dot(x, y, color):
    circle(x, y, 4.5, color, "#ffffff", 1.5)


# ─── The Pis, to scale (header at the top edge, pin 1 on the left) ─────────
def header(ox, oy):
    """The 40-pin header: pin 1 at 8.37 mm in, rows 1.27 mm either side of 3.5 mm."""
    x0 = ox + (32.5 - 24.13 - 1.6) * S
    rect(x0, oy + 1.0 * S, (48.26 + 3.2) * S, 5.0 * S, "#111", rx=2)
    for i in range(20):
        for row in (2.23, 4.77):
            circle(ox + (8.37 + i * 2.54) * S, oy + row * S, 2.4, C["gold"])
    rect(ox + (8.37 - 1.1) * S, oy + (4.77 - 1.1) * S, 2.2 * S, 2.2 * S, "none", C["gold"], 1.5)  # pin 1


def holes(ox, oy, pts):
    for x, y in pts:
        circle(ox + x * S, oy + y * S, 1.4 * S, "#ffffff", C["pcb_edge"], 1)


def port(ox, oy, x, y, w, h, label=None, inner=None):
    rect(ox + x * S, oy + y * S, w * S, h * S, C["metal"], C["metal_edge"], 1.2, rx=2)
    if inner:
        rect(ox + (x + w * 0.2) * S, oy + (y + h * 0.3) * S, w * 0.6 * S, h * 0.4 * S, inner, rx=1)


def pi4(ox, oy):
    rect(ox, oy, 85 * S, 56 * S, C["pcb"], C["pcb_edge"], 2, rx=3 * S)
    holes(ox, oy, [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)])
    header(ox, oy)
    rect(ox + 22 * S, oy + 25 * S, 15 * S, 15 * S, "#9aa0a6", "#6b7075", rx=2)  # SoC
    text(ox + 29.5 * S, oy + 46 * S, "Raspberry Pi 4", 15, "middle", "bold", "#ffffff")
    port(ox, oy, 70, 2.4, 17.5, 13.2, inner="#111")     # USB 2.0
    port(ox, oy, 70, 20.4, 17.5, 13.2, inner="#2b6fd6")  # USB 3.0
    port(ox, oy, 66, 38, 21.5, 16)                       # Ethernet
    text(ox + 78.75 * S, oy + 14.6 * S, "USB 2.0", 11, "middle", "bold")
    text(ox + 78.75 * S, oy + 32.6 * S, "USB 3.0", 11, "middle", "bold")
    text(ox + 76.75 * S, oy + 47 * S, "Ethernet", 11, "middle")
    port(ox, oy, 11.2 - 4.5, 50.5, 9, 7)                 # USB-C
    port(ox, oy, 26 - 3.75, 51, 7.5, 6.5)
    port(ox, oy, 39.5 - 3.75, 51, 7.5, 6.5)
    circle(ox + 53.5 * S, oy + 55 * S, 3 * S, "#111", C["metal_edge"])
    text(ox + 11.2 * S, oy + 62 * S, "USB-C: leave empty", 12, "middle", color=C["red"])
    text(ox + 11.2 * S, oy + 64.6 * S, "(the Bonnet powers the Pi)", 11, "middle", color=C["dim"])
    text(ox + 32.7 * S, oy + 62 * S, "micro HDMI", 12, "middle", color=C["dim"])
    text(ox + 53.5 * S, oy + 62 * S, "audio (off)", 12, "middle", color=C["dim"])
    rect(ox - 2 * S, oy + 22 * S, 12 * S, 12 * S, "none", "#ffffff", 1.2, dash="4 3")
    text(ox + 1 * S, oy + 37.2 * S, "SD (under)", 11, color="#ffffff")
    return dict(usb=(ox + 87.5 * S, oy + 9 * S), bottom=oy + 66 * S)


def pi_zero(ox, oy):
    rect(ox, oy, 65 * S, 30 * S, C["pcb"], C["pcb_edge"], 2, rx=3 * S)
    holes(ox, oy, [(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)])
    header(ox, oy)
    rect(ox + 24 * S, oy + 11 * S, 12 * S, 12 * S, "#9aa0a6", "#6b7075", rx=2)
    text(ox + 45 * S, oy + 16 * S, "Pi Zero 2 W", 14, "middle", "bold", "#ffffff")
    text(ox + 45 * S, oy + 19 * S, "or Pi Zero", 12, "middle", color="#ffffff")
    port(ox, oy, -1.5, 9.5, 15, 11, inner="#111")  # micro SD (top side, left end)
    text(ox + 6 * S, oy + 23.5 * S, "micro SD", 11, "middle", color="#ffffff")
    port(ox, oy, 12.4 - 5.6, 25, 11.2, 6.5)   # mini HDMI
    port(ox, oy, 41.4 - 4, 25.5, 8, 5.6)      # USB (data)
    port(ox, oy, 54 - 4, 25.5, 8, 5.6)        # PWR
    text(ox + 12.4 * S, oy + 36 * S, "mini HDMI", 12, "middle", color=C["dim"])
    text(ox + 41.4 * S - 8, oy + 36 * S, "USB", 12, "end", "bold", C["blue"])
    text(ox + 56 * S, oy + 36 * S, "PWR: leave empty", 12, "start", color=C["red"])
    text(ox + 56 * S, oy + 38.6 * S, "(the Bonnet powers the Pi)", 11, "start", color=C["dim"])
    return dict(usb=(ox + 41.4 * S, oy + 31.1 * S), bottom=oy + 42 * S)


# ─── The RGB Matrix Bonnet (Adafruit 3211), top view, laid out from Adafruit's photo ──
def bonnet(ox, oy):
    rect(ox, oy, 65 * S, 30 * S, C["bonnet"], "#000", 2, rx=3 * S)
    for x, y in ((3.2, 4), (61.8, 4), (3.2, 27), (61.8, 27)):
        circle(ox + x * S, oy + y * S, 1.4 * S, "#111", "#444")
    for i in range(20):  # the header socket's holes, filled by its pins
        for row in (2.5, 5.1):
            circle(ox + (8.37 + i * 2.54) * S, oy + row * S, 4, C["gold"], "#8a6d12")
            circle(ox + (8.37 + i * 2.54) * S, oy + row * S, 1.8, "#111")
    for i in range(len(BREAKOUT)):  # the breakout row, close-up below
        circle(ox + (2.26 + i * 2.54) * S, oy + 9.5 * S, 4, C["gold"], "#8a6d12")
        circle(ox + (2.26 + i * 2.54) * S, oy + 9.5 * S, 1.8, "#111")
    for i in range(3):  # its 5V / GND pads
        circle(ox + (2.26 + i * 2.54) * S, oy + 12 * S, 4, C["gold"], "#8a6d12")
        circle(ox + (2.26 + i * 2.54) * S, oy + 12 * S, 1.8, "#111")
    # the 4-18 quality jumper: a wire between the 4 and 18 pads
    x4, x18 = ox + (2.26 + 4 * 2.54) * S, ox + (2.26 + 6 * 2.54) * S
    add(f'<path d="M{x4:.1f},{oy + 9.5 * S:.1f} Q{(x4 + x18) / 2:.1f},{oy + 5.5 * S:.1f} {x18:.1f},{oy + 9.5 * S:.1f}" '
        f'fill="none" stroke="#e8590c" stroke-width="3" stroke-linecap="round"/>')
    text(ox + 19.5 * S, oy + 13.2 * S, "4–18 jumper wire (needs adafruit-hat-pwm)", 10, color="#ffd666")
    # chips
    for x in (29.5, 37.5):
        rect(ox + x * S, oy + 14 * S, 7 * S, 4.5 * S, "#111", "#3a3a3a", 1)
    # 5V In: the DC jack, out of the left end
    rect(ox - 2.3 * S, oy + 14 * S, 14.8 * S, 9 * S, "#111", "#555", 1.2, rx=2)
    circle(ox + 0.5 * S, oy + 18.5 * S, 1.6 * S, "#555")
    text(ox + 4.5 * S, oy + 27 * S, "5V In", 11, "middle", "bold", "#ffffff")
    # 5V OK light
    rect(ox + 18.4 * S, oy + 17.4 * S, 2 * S, 1.2 * S, "#3ddc5a", rx=1)
    text(ox + 21 * S, oy + 18.6 * S, "5V OK", 9, color="#c7cad0")
    # 5V Out: the screw terminal
    rect(ox + 15.3 * S, oy + 20.2 * S, 11.3 * S, 9 * S, "#111", "#444", 1.2, rx=2)
    for x in (18.6, 23.5):
        circle(ox + x * S, oy + 24.9 * S, 2.1 * S, C["metal"], C["metal_edge"])
    text(ox + 21 * S, oy + 21.9 * S, "5V Out", 9, "middle", "bold", "#ffffff")
    text(ox + 14.2 * S, oy + 28.6 * S, "+", 12, "middle", "bold", "#ffffff")
    text(ox + 27.8 * S, oy + 28.6 * S, "−", 12, "middle", "bold", "#ffffff")
    # HUB75 out, 2x8 IDC
    rect(ox + 29.8 * S, oy + 20.9 * S, 27.9 * S, 8.4 * S, "#111", "#555", 1.2, rx=2)
    for i in range(8):
        for row in (23.6, 26.6):
            circle(ox + (33 + i * 3) * S, oy + row * S, 2, C["gold"])
    rect(ox + 41.8 * S, oy + 20.9 * S, 4 * S, 1 * S, "#555")  # key notch
    text(ox + 61.5 * S, oy + 25.5 * S, "HUB75", 10, "middle", "bold", "#ffffff")
    text(ox + 65 * S, oy - 10, "Adafruit RGB Matrix Bonnet (3211)", 14, "end", "bold")
    return dict(jack=(ox - 2.3 * S, oy + 18.5 * S), plus=(ox + 18.6 * S, oy + 24.9 * S),
                minus=(ox + 23.5 * S, oy + 24.9 * S), idc=(ox + 57.7 * S, oy + 25.1 * S))


def panel(ox, oy, w=360):
    rect(ox, oy, w, w, C["panel"], "#222", 2, rx=6)
    for i in range(1, 6):  # the panel back's ribs
        rect(ox + 10, oy + i * w / 6, w - 20, 2, "#4a4e54")
    text(ox + w / 2, oy - 12, "LED panel, back (64x64 shown; a 64x32 is half as tall)", 13, "middle", "bold")
    rect(ox + 14, oy + 130, 64, 30, "#111", "#666", 1.2, rx=2)
    text(ox + 46, oy + 150, "IN", 14, "middle", "bold", "#ffffff")
    rect(ox + w - 78, oy + 130, 64, 30, "#111", "#666", 1.2, rx=2)
    text(ox + w - 46, oy + 150, "OUT", 13, "middle", color="#9aa0a6")
    text(ox + w - 46, oy + 178, "leave empty", 11, "middle", color="#c7cad0")
    rect(ox + w / 2 - 34, oy + 168, 68, 30, "#f2f2f2", "#999", 1.2, rx=3)
    text(ox + w / 2 - 15, oy + 187, "GND", 10, "middle", "bold")
    text(ox + w / 2 + 15, oy + 187, "+5V", 10, "middle", "bold", C["red"])
    text(ox + w / 2, oy + 160, "power", 11, "middle", color="#c7cad0")
    text(ox + w / 2, oy + w - 20, "arrows on the back point away from IN", 11, "middle", color="#c7cad0")
    return dict(inp=(ox + 14, oy + 145), gnd=(ox + w / 2 - 15, oy + 198), pos=(ox + w / 2 + 15, oy + 198))


# ─── Power button and the Bonnet's breakout pads, close up ──────────────────
# The breakout row under the header, left to right, as printed on the Bonnet: (label above, GPIO,
# the Bonnet's signal printed under it, from rpi-rgb-led-matrix's "adafruit-hat" mapping: OE output
# enable, CLK clock, LAT latch, A-E row address, R1-B2 colour data). 18 has no signal of its own:
# the 4-18 jumper wire joins it to OE for "adafruit-hat-pwm". The Bonnet's B (GPIO 26) isn't on it.
BREAKOUT = [("SDA", 2, None), ("SCL", 3, None), ("TX", 14, None), ("RX", 15, None), ("4", 4, "OE"),
            ("17", 17, "CLK"), ("18", 18, None), ("27", 27, "C"), ("22", 22, "A"), ("23", 23, "B2"),
            ("24", 24, "E"), ("25", 25, None), ("MO", 10, None), ("MI", 9, None), ("CLK", 11, None),
            ("CE0", 8, None), ("CE1", 7, None), ("5", 5, "R1"), ("6", 6, "B1"), ("12", 12, "R2"),
            ("13", 13, "G1"), ("16", 16, "G2"), ("19", 19, None), ("20", 20, "D"), ("21", 21, "LAT")]
POWER_PADS = ["5V", "", "GND"]  # under SDA, SCL and TX; the middle one has no label on the board


def pad(x, y, used=None):
    circle(x, y, 8, C["gold"], "#8a6d12", 1.5)
    circle(x, y, 3.5, "#111")
    if used:
        circle(x, y, 11, "none", used, 3)


def breakout_closeup(x0, y0, pitch=26):
    left = 40
    text(left, y0 - 92, "Power button: four wires to the Bonnet's breakout pads", 16, weight="bold")
    text(left, y0 - 72, "The row under the header, labelled as on the Bonnet. A pad with a signal printed under it "
         "(OE, CLK, R1…)", 12, color=C["dim"])
    text(left, y0 - 56, "is the Bonnet's own: don't solder to it. The rest are the Pi's free pins.", 12, color=C["dim"])
    centers = {}
    for i, (label, gpio, signal) in enumerate(BREAKOUT):
        x = x0 + i * pitch
        centers[label] = (x, y0)
        text(x, y0 - 14, label, 10 if len(label) < 3 else 9, "middle", "bold")
        if signal:
            text(x, y0 + 24, signal, 10 if len(signal) < 3 else 9, "middle", "bold", "#8a8f96")
    for i, label in enumerate(POWER_PADS):
        centers[label or "unlabelled"] = (x0 + i * pitch, y0 + pitch)
    text(x0, y0 + pitch + 22, "5V", 10, "middle", "bold", C["red"])
    text(x0 + 2 * pitch + 13, y0 + pitch + 4, "GND", 10, "start", "bold")

    # the button, below left
    bx, by = left + 30, y0 + 130
    circle(bx, by, 26, "#d9dce0", "#8a8f96", 2)
    circle(bx, by, 19, "none", C["green"], 4)
    circle(bx, by, 13, "#eef0f2", "#8a8f96", 1)
    text(bx + 40, by + 34, "16 mm momentary button, green LED ring (Adafruit 560)", 11, weight="bold")

    scl, gnd, p25 = centers["SCL"], centers["GND"], centers["25"]
    gap = scl[0] + pitch / 2  # between the SCL and TX columns, clear of the 5V/GND pads
    wire([(bx - 8, by - 24), (bx - 8, y0 + 56), (gap, y0 + 56), (gap, y0 + 14), scl], C["yellow"], 3.5)
    wire([(bx + 6, by - 25), (bx + 6, y0 + 76), (gnd[0] - 4, y0 + 76), (gnd[0] - 4, gnd[1])], C["gnd"], 3.5)
    wire([(bx + 14, by - 22), (bx + 14, y0 + 88), (gnd[0] + 4, y0 + 88), (gnd[0] + 4, gnd[1])], C["gnd"], 3.5)
    wire([(bx + 24, by - 12), (bx + 40, by - 12), (bx + 40, y0 + 100), (p25[0], y0 + 100), p25], C["green"], 3.5)
    for i, (label, gpio, signal) in enumerate(BREAKOUT):
        pad(x0 + i * pitch, y0, {"SCL": C["yellow"], "25": C["green"]}.get(label))
    for i, label in enumerate(POWER_PADS):
        pad(x0 + i * pitch, y0 + pitch, C["gnd"] if label == "GND" else None)
    # the jumper wire, pad 4 to pad 18
    (x4, _), (x18, _) = centers["4"], centers["18"]
    jumper = "#e8590c"
    add(f'<path d="M{x4:.1f},{y0 - 7:.1f} Q{(x4 + x18) / 2:.1f},{y0 - 26:.1f} {x18:.1f},{y0 - 7:.1f}" fill="none" '
        f'stroke="{jumper}" stroke-width="3.5" stroke-linecap="round"/>')
    text((x4 + x18) / 2, y0 + 42, "4–18 jumper", 10, "middle", "bold", jumper)

    text(left + 80, y0 + 62, "Yellow: SCL = GPIO 3, the switch", 11, weight="bold")
    text(left + 80, y0 + 80, "Black: GND, both ground wires", 11, weight="bold")
    text(p25[0] + 8, y0 + 96, "25 = GPIO 25: LED +", 11, weight="bold", color=C["green"])

    ly = by + 66
    text(left, ly, "Unlabelled numbers are GPIO numbers. MO, MI, CLK, CE0, CE1 are the Pi's SPI pins (free here; this "
         "CLK isn't the panel's).", 11, color=C["dim"])
    text(left, ly + 15, "Keep I2C off (no dtparam=i2c_arm=on): SCL is GPIO 3, the button's pin.", 11, color=C["dim"])

    why = ly + 44
    text(left, why, "What the pads do", 14, weight="bold")
    lines = [
        ("SCL, GPIO 3: shutdown and wake.", "The only pin a shut-down Pi still watches, so one button does both."),
        ("25, GPIO 25: the light.", "On while Linux runs, off when shutdown has finished. Any free pad would do."),
        ("GND: one ground for both.", "The switch's and the LED's ground wires share it; every ground on the Pi is the same."),
        ("4 to 18: the quality jumper.", "A wire between them, for smoother dim colours with adafruit-hat-pwm."),
    ]
    for i, (head, body) in enumerate(lines):
        y = why + 20 + i * 17
        text(left, y, head, 11, weight="bold")
        text(left + 218, y, body, 11, color=C["dim"])


# ─── Sound ────────────────────────────────────────────────────────────────
def speaker_icon(x, y, r=26):
    circle(x, y, r, "#2b2d31", "#111", 2)
    circle(x, y, r * 0.6, "#4a4d52", "#222", 1)
    circle(x, y, r * 0.2, "#777")


def sound(x0, y0, zero):
    w = 670
    rect(x0, y0, w, 128, "#f4f8ff", "#9bb8e8", 1.5, rx=8)
    text(x0 + 16, y0 + 24, "Sound, option A (recommended): a USB speaker", 15, weight="bold")
    usb_in = (x0 + 30, y0 + 78)  # where the cable from the Pi reaches the speaker
    speaker_icon(x0 + 56, y0 + 78)
    text(x0 + 96, y0 + 58, "Mini USB stereo speaker (Adafruit 3369)", 12, weight="bold")
    text(x0 + 96, y0 + 74, "power and sound over the one USB cable", 12, color=C["dim"])
    if zero:
        text(x0 + 96, y0 + 94, "Into the Zero's USB port through a flexible OTG", 12)
        text(x0 + 96, y0 + 110, "cable (1099); a rigid adapter once cracked an SD card", 12, color=C["dim"])
    else:
        text(x0 + 96, y0 + 94, "Into any USB-A port", 12)
    rect(x0 + w - 176, y0 + 44, 160, 64, "#ffffff", "#c8d6ee", 1, rx=6)
    text(x0 + w - 166, y0 + 64, "then on the Pi:", 11, color=C["dim"])
    text(x0 + w - 166, y0 + 82, "aplay -l", 12, weight="bold")
    text(x0 + w - 166, y0 + 98, "config.json: sound.device", 11)

    # option B
    by = y0 + 150
    rect(x0, by, w, 310, "#fafafa", "#9aa0a6", 1.5, rx=8, dash="8 5")
    text(x0 + 16, by + 24, "Option B, instead of A: a small speaker built into the case", 15, weight="bold")
    text(x0 + 16, by + 42, "Some soldering; most likely to pick up buzz from the panel. Details in SOUND.md.", 12,
         color=C["dim"])
    # USB audio adapter
    ax, ay = x0 + 20, by + 120
    rect(ax, ay, 112, 46, "#2b2d31", "#111", 1.5, rx=6)
    text(ax + 56, ay + 20, "USB audio", 11, "middle", "bold", "#ffffff")
    text(ax + 56, ay + 35, "adapter (1475)", 11, "middle", color="#c7cad0")
    wire([(ax + 56, ay - 34), (ax + 56, ay)], C["cable"], 7)
    text(ax + 64, ay - 20, "from the Pi", 11, color=C["dim"])
    # 3.5 mm plug terminal block
    tx, ty = x0 + 168, by + 92
    wire([(ax + 112, ay + 23), (tx, ay + 23)], C["cable"], 6)
    text(ax + 129, ay + 14, "3.5 mm", 10, "middle", color=C["dim"])
    rect(tx, ty, 108, 104, "#2f7de1", "#1c5bb0", 1.5, rx=6)
    text(tx + 54, ty + 120, "3.5 mm plug", 11, "middle", "bold")
    text(tx + 54, ty + 134, "terminal block (2790)", 11, "middle", "bold")
    terms = {}
    for i, (name, label) in enumerate((("T", "tip, left"), ("R", "ring: unwired"), ("S", "sleeve, GND"))):
        cy = ty + 22 + i * 30
        circle(tx + 90, cy, 7, C["metal"], C["metal_edge"])
        text(tx + 10, cy + 4, f"{name}  {label}", 10, color="#ffffff")
        terms[name] = (tx + 90, cy)
    # PAM8302 amp
    px, py = x0 + 380, by + 82
    rect(px, py, 150, 150, C["pcb"], C["pcb_edge"], 1.5, rx=6)
    text(px + 75, py - 8, "PAM8302 amp (2130)", 11, "middle", "bold")
    amp = {}
    for i, name in enumerate(("A+", "A−", "VIN", "GND")):
        cy = py + 24 + i * 32
        circle(px + 14, cy, 6, C["gold"], "#8a6d12")
        text(px + 26, cy + 4, name, 11, weight="bold", color="#ffffff")
        amp[name] = (px + 14, cy)
    text(px + 26, py + 144, "SD unwired: on", 9, color="#d8f0e0")
    for i, name in enumerate(("+", "−")):
        cy = py + 50 + i * 40
        rect(px + 126, cy - 12, 20, 24, "#2f7de1", "#1c5bb0", 1, rx=2)
        text(px + 116, cy + 5, name, 13, "end", "bold", "#ffffff")
        amp["spk" + name] = (px + 146, cy)
    # audio wires
    wire([terms["T"], (tx + 130, terms["T"][1]), (tx + 130, amp["A+"][1]), amp["A+"]], C["blue"], 3.5)
    wire([terms["S"], (tx + 140, terms["S"][1]), (tx + 140, amp["A−"][1]), amp["A−"]], C["gnd"], 3.5)
    # amp power from the Bonnet's terminal
    vx = px - 30
    wire([(vx - 14, by + 262), (vx - 14, amp["VIN"][1]), amp["VIN"]], C["red"], 3.5)
    wire([(vx, by + 262), (vx, amp["GND"][1]), amp["GND"]], C["gnd"], 3.5)
    text(vx + 8, by + 258, "from the Bonnet's 5V screw terminal (+ and −)", 11, weight="bold", color=C["red"])
    # speaker
    sx, sy = px + 230, py + 70
    wire([amp["spk+"], (sx - 40, amp["spk+"][1]), (sx - 40, sy - 8), (sx - 24, sy - 8)], C["red"], 3)
    wire([amp["spk−"], (sx - 30, amp["spk−"][1]), (sx - 30, sy + 8), (sx - 24, sy + 8)], C["gnd"], 3)
    speaker_icon(sx, sy, 24)
    text(sx, sy + 44, "36 mm 8 Ω 2 W", 11, "middle", "bold")
    text(sx, sy + 58, "speaker (6486)", 11, "middle")
    text(x0 + 16, by + 292, "One speaker, two channels: wire only the tip and mix left and right in ALSA (SOUND.md, Mono).",
         11, color=C["dim"])
    return usb_in


def case_jack(jx, jy, bonnet_jack, supply_x):
    """The case's own DC jack (Adafruit 610), seen from inside: its back has three solder eyes on a
    little board. The big tab carries the centre pin; of the two small ones, one is the sleeve and
    one a switch contact. A cut-off DC cord soldered to it plugs into the Bonnet's 5V In."""
    hexagon = " ".join(f"{jx + 36 * dx:.1f},{jy + 36 * dy:.1f}" for dx, dy in
                       ((1, 0), (0.5, 0.866), (-0.5, 0.866), (-1, 0), (-0.5, -0.866), (0.5, -0.866)))
    add(f'<polygon points="{hexagon}" fill="{C["metal"]}" stroke="{C["metal_edge"]}" stroke-width="1.5"/>')
    sq = 44
    x0, y0 = jx - sq / 2, jy - sq / 2
    rect(x0, y0, sq, sq, "#d9822b", "#a65e17", 1, rx=4)
    top, side = (x0 + 0.3 * sq, y0 + 0.2 * sq), (x0 + 0.68 * sq, y0 + 0.48 * sq)
    for x, y in (top, side):  # the two small tabs
        rect(x - 6, y - 3, 12, 6, C["metal"], C["metal_edge"], 1, rx=2)
    rect(x0 + 0.05 * sq, y0 + 0.62 * sq, 0.56 * sq, 0.28 * sq, C["metal"], C["metal_edge"], 1, rx=2)  # big tab
    centre = (x0 + 0.47 * sq, y0 + 0.76 * sq)
    circle(*centre, 4, "#e8e8e8", "#8a8f96")
    text(side[0] + 9, side[1] + 4, "×", 12, weight="bold", color=C["dim"])
    # inside: the cut cord's two wires to the tabs, then the cord to a plug in the Bonnet's 5V In
    red_x, black_x, merge_y = 598, 606, 280
    wire([(x0 + 0.05 * sq, centre[1]), (red_x, centre[1]), (red_x, merge_y)], C["red"], 3.5)
    wire([top, (top[0], jy - 40), (black_x, jy - 40), (black_x, merge_y)], C["gnd"], 3.5)
    plug_x = bonnet_jack[0] - 24
    wire([(602, merge_y), (602, bonnet_jack[1]), (plug_x, bonnet_jack[1])], C["cable"], 7)
    rect(plug_x, bonnet_jack[1] - 7, 24, 14, "#6b7075", "#3a3d42", 1, rx=2)
    # outside: the supply's own plug into the front
    wall = jx + 46
    wire([(wall, jy - 44), (wall, jy + 44)], C["dim"], 2, "4 3")
    wire([(jx + 36, jy), (supply_x, jy)], C["cable"], 7)
    text(wall + 6, jy - 30, "outside", 10, color=C["dim"])
    text(jx + 4, jy + 54, "case jack (Adafruit 610), back", 10, "middle", "bold")
    for i, line in enumerate((
            "Inside, a cut-off DC cord: its centre wire (+, red) to the",
            "big tab with the centre pin, its other wire (−) to the sleeve",
            "tab; the third (×, a switch) stays empty. The small tabs look",
            "alike: with the supply in, the sleeve reads 5 V to the big tab.")):
        text(776, jy + 50 + i * 12, line, 10, color=C["dim"])


def build(zero):
    global out
    out = []
    W, H = 1500, 1050
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
    add('<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["dim"]}"/></marker></defs>')
    rect(0, 0, W, H, "#ffffff")
    name = "Pi Zero 2 W / Pi Zero" if zero else "Raspberry Pi 4"
    text(40, 44, f"Wiring a board: {name}", 24, weight="bold")
    text(40, 68, "Pi drawn to scale from above; Bonnet laid out from Adafruit's photo; panel not to scale. "
         "Red = 5 V, black = ground.", 13, color=C["dim"])

    pi_x, pi_y = 40, 150
    pi = pi_zero(pi_x, pi_y) if zero else pi4(pi_x, pi_y)
    # where the Bonnet goes on the Pi
    rect(pi_x - 3, pi_y - 3, 65 * S + 6, 30 * S + 6, "none", "#ffd666", 2.5, rx=3 * S, dash="9 6")
    b = bonnet(650, 120)
    wire([(700, 116), (700, 96), (pi_x + 32.5 * S, 96), (pi_x + 32.5 * S, pi_y - 8)], C["dim"], 2, "6 4", arrow=True)
    text(pi_x + 32.5 * S + 10, 90, "the Bonnet plugs onto the 40-pin header, inside the yellow outline"
         + (" (it covers the whole Zero)" if zero else ""), 12, color=C["dim"])

    p = panel(1100, 120)
    # HUB75 ribbon
    wire([b["idc"], (1060, b["idc"][1]), (1060, p["inp"][1]), p["inp"]], C["ribbon"], 10)
    wire([b["idc"], (1060, b["idc"][1]), (1060, p["inp"][1]), p["inp"]], "#c84a4a", 1.5)
    text(1070, b["idc"][1] - 26, "16-pin", 11, "middle", color=C["dim"])
    text(1070, b["idc"][1] - 13, "ribbon", 11, "middle", color=C["dim"])
    # panel power lead from the screw terminal
    wire([b["plus"], (b["plus"][0], 350), (p["pos"][0], 350), p["pos"]], C["red"], 4)
    wire([b["minus"], (b["minus"][0], 338), (p["gnd"][0], 338), p["gnd"]], C["gnd"], 4)
    text(880, 366, "panel power lead, into the screw terminal", 11, "middle", color=C["dim"])
    # the supply into the DC jack
    sx, sy = 760, 400
    rect(sx, sy, 250, 74, C["note"], C["note_edge"], 1.5, rx=8)
    text(sx + 14, sy + 22, "5 V power supply", 14, weight="bold")
    text(sx + 14, sy + 40, "64x64: 4 A or more; 64x32: about 3 A", 12)
    text(sx + 14, sy + 57, "powers the panel and, through the", 11, color=C["dim"])
    text(sx + 14, sy + 70, "Bonnet, the Pi: the Pi needs no cable", 11, color=C["dim"])
    # the case's DC jack: the supply plugs in outside; inside, a cut DC cord soldered to its tabs
    # plugs into the Bonnet, so the board never has to come out
    case_jack(672, sy + 37, b["jack"], sx)

    # sound
    a = sound(790, 540, zero)
    ux, uy = pi["usb"]
    lane_x = 766
    if zero:
        path = [(ux, uy), (ux, 512), (lane_x, 512)]
        text(ux + 10, uy + 70, "OTG cable (1099)", 11, weight="bold", color=C["blue"])
    else:
        path = [(ux, uy), (580, uy), (580, 512), (lane_x, 512)]
    wire(path + [(lane_x, a[1]), a], C["cable"], 6)
    text(lane_x - 8, 504, "USB, to the speaker", 11, "end", "bold", C["blue"])

    breakout_closeup(50, 700)
    add("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else DOCS
    for name, zero in FILES.items():
        with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
            f.write(build(zero))
        print(f"wrote {os.path.join(folder, name)}")
