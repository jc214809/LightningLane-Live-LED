"""Coordinated firework animations for the LED board."""

import math
import random
import time

from driver import graphics

COLOR_PALETTE = [
    (255, 94, 19),  # orange
    (255, 193, 37),  # gold
    (255, 60, 122),  # pink
    (67, 195, 255),  # cyan
    (35, 196, 103),  # green
    (194, 51, 216),  # violet
]

FRAME_DELAY = 0.03
TRAIL_LENGTH = 6


WHITE = graphics.Color(255, 255, 255)
BLACK = graphics.Color(0, 0, 0)


def _scale_color(rgb, factor):
    r = max(0, min(255, int(rgb[0] * factor)))
    g = max(0, min(255, int(rgb[1] * factor)))
    b = max(0, min(255, int(rgb[2] * factor)))
    return graphics.Color(r, g, b)


def _draw_trail(matrix, x, trail, color_rgb):
    visible = trail[-TRAIL_LENGTH:]
    for index, y in enumerate(reversed(visible)):
        fade = index / max(len(visible), 1)
        intensity = 0.35 + 0.65 * (1.0 - fade)
        trail_color = _scale_color(color_rgb, intensity)
        graphics.DrawLine(matrix, x, y, x, y, trail_color)


def _prepare_rockets(matrix, positions):
    rockets = []
    base_height = matrix.height - 1
    for idx, x in enumerate(positions):
        rockets.append(
            {
                "x": x,
                "y": base_height,
                "color": COLOR_PALETTE[idx % len(COLOR_PALETTE)],
                "apex": random.randint(max(2, matrix.height // 3), max(matrix.height // 2, 6)),
                "step": random.randint(3, 5),
                "trail": [],
                "reached_apex": False,
            }
        )
    return rockets



def _draw_background_pixel(matrix, x, y, silhouette=None):
    if silhouette and (x, y) in silhouette:
        graphics.DrawLine(matrix, x, y, x, y, WHITE)
    else:
        graphics.DrawLine(matrix, x, y, x, y, BLACK)


def _clear_column(matrix, x, silhouette=None):
    for y in range(matrix.height):
        _draw_background_pixel(matrix, x, y, silhouette)


def _update_rockets(matrix, rockets, silhouette=None):
    while any(not rocket["reached_apex"] for rocket in rockets):
        for rocket in rockets:
            if rocket["reached_apex"]:
                continue

            _clear_column(matrix, rocket["x"], silhouette)
            rocket["trail"].append(rocket["y"])
            rocket["trail"] = rocket["trail"][-TRAIL_LENGTH:]
            for idx, y in enumerate(reversed(rocket["trail"])):
                intensity = 0.35 + 0.65 * (1.0 - (idx / max(TRAIL_LENGTH - 1, 1)))
                trail_color = _scale_color(rocket["color"], intensity)
                graphics.DrawLine(matrix, rocket["x"], y, rocket["x"], y, trail_color)

            graphics.DrawLine(
                matrix,
                rocket["x"],
                rocket["y"],
                rocket["x"],
                rocket["y"],
                graphics.Color(*rocket["color"]),
            )

            rocket["y"] -= random.randint(1, 2)
            if rocket["y"] <= rocket["apex"]:
                rocket["y"] = rocket["apex"]
                rocket["reached_apex"] = True

        time.sleep(FRAME_DELAY)

    return [(rocket["x"], rocket["y"]) for rocket in rockets]


def _explode_particles(matrix, centers, silhouette=None, particle_count=24, max_age_range=(0.3, 0.6)):
    particles = []
    for center_x, center_y in centers:
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.8, 2.2)
            particles.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "color": random.choice(COLOR_PALETTE),
                    "age": 0.0,
                    "max_age": random.uniform(*max_age_range),
                }
            )

    active = True
    prev_pixels = set()
    while active and particles:
        active = False
        for px, py in prev_pixels:
            _draw_background_pixel(matrix, px, py, silhouette)
        prev_pixels.clear()
        for particle in particles:
            if particle["age"] >= particle["max_age"]:
                continue

            active = True
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dy"] += 0.04
            particle["dx"] *= 0.97
            particle["age"] += FRAME_DELAY

            fade = 1.0 - (particle["age"] / particle["max_age"])
            faded_color = _scale_color(particle["color"], 0.35 + 0.65 * max(fade, 0))
            px = int(round(particle["x"]))
            py = int(round(particle["y"]))

            if 0 <= px < matrix.width and 0 <= py < matrix.height:
                graphics.DrawLine(matrix, px, py, px, py, faded_color)
                prev_pixels.add((px, py))

        time.sleep(FRAME_DELAY)

    for px, py in prev_pixels:
        _draw_background_pixel(matrix, px, py, silhouette)


def _run_side_fireworks(matrix, positions, silhouette=None):
    rockets = _prepare_rockets(matrix, positions)
    centers = _update_rockets(matrix, rockets, silhouette)
    _explode_particles(matrix, centers, silhouette)


def _run_center_burst(matrix, silhouette=None):
    center_x = matrix.width // 2
    center_y = matrix.height // 3
    _explode_particles(matrix, [(center_x, center_y)], silhouette, particle_count=64, max_age_range=(1.0, 1.8))


def launch_side_fireworks(matrix, left_x, right_x, silhouette=None):
    positions = [left_x, right_x]
    _run_side_fireworks(matrix, positions, silhouette)


def launch_center_firework(matrix, silhouette=None):
    _run_center_burst(matrix)
    if silhouette:
        _draw_pixels(matrix, silhouette)
