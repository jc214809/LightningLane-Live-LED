from utils.settings_pin import shown_pin

# The settings page's PIN (settings_page/pins.py), over whatever's on the board while it's up:
# big white digits in a gold-edged black box, centred, the same size on both boards, so it reads
# from across the room. Its own 3x5 digits, drawn at SCALE, so it needs no font.
DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
}
SCALE = 2
GAP = 1  # between digits, before scaling
PAD = 2  # black between the digits and the gold edge
WHITE, GOLD, BLACK = (255, 255, 255), (255, 190, 0), (0, 0, 0)


def draw_pin(canvas, pin):
    digits = [DIGITS[d] for d in pin if d in DIGITS]
    if not digits:
        return
    text_w = (len(digits) * (3 + GAP) - GAP) * SCALE
    text_h = 5 * SCALE
    w, h = text_w + 2 * (PAD + 1), text_h + 2 * (PAD + 1)
    x0, y0 = (canvas.width - w) // 2, (canvas.height - h) // 2
    for y in range(h):
        for x in range(w):
            edge = x in (0, w - 1) or y in (0, h - 1)
            canvas.SetPixel(x0 + x, y0 + y, *(GOLD if edge else BLACK))
    left, top = x0 + PAD + 1, y0 + PAD + 1
    for i, art in enumerate(digits):
        for row, line in enumerate(art):
            for col, key in enumerate(line):
                if key != "#":
                    continue
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        canvas.SetPixel(left + (i * (3 + GAP) + col) * SCALE + dx, top + row * SCALE + dy, *WHITE)


def draw_if_pin_shown(canvas):
    pin = shown_pin()
    if pin:
        draw_pin(canvas, pin)
