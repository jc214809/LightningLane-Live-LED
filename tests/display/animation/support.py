"""Fakes and helpers the animation tests share."""

import display.animation as animation


class FakeColor:
    def __init__(self, r, g, b):
        self.rgb = (r, g, b)


class FakeCanvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.px = {}

    def Clear(self):
        self.px = {}

    def SetPixel(self, x, y, r, g, b):
        self.px[(x, y)] = (r, g, b)


class FakeMatrix:
    def __init__(self, width=64, height=32):
        self.width, self.height = width, height
        self.canvases_created = 0
        self.frames = []

    def CreateFrameCanvas(self):
        self.canvases_created += 1
        return FakeCanvas(self.width, self.height)

    def SwapOnVSync(self, canvas):
        self.frames.append(dict(canvas.px))
        return FakeCanvas(self.width, self.height)


def _draw_line(canvas, x0, y0, x1, y1, color):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            canvas.SetPixel(x, y, *color.rgb)


def fill(rgb):
    def draw(canvas, t):
        for x in range(canvas.width):
            for y in range(canvas.height):
                canvas.SetPixel(x, y, *rgb)
        return False
    return draw


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, s):
        self.now += s


FLYBYS = [animation.TinkReveal, animation.FigmentReveal, animation.DumboReveal]


def _striped_screen(canvas, t):
    for y in range(canvas.height):
        for x in range(canvas.width):
            canvas.SetPixel(x, y, 200, 100, 50)
    return False
