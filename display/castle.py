"""Castle outline based on the provided reference image."""

from driver import graphics


def _draw_line(matrix, x0, y0, x1, y1, color):
    graphics.DrawLine(matrix, x0, y0, x1, y1, color)


def _draw_rect_outline(matrix, x0, y0, x1, y1, color):
    if x0 > x1 or y0 > y1:
        return
    x0 = max(0, x0)
    x1 = min(matrix.width - 1, x1)
    y0 = max(0, y0)
    y1 = min(matrix.height - 1, y1)
    if x0 > x1 or y0 > y1:
        return
    _draw_line(matrix, x0, y0, x1, y0, color)
    _draw_line(matrix, x0, y1, x1, y1, color)
    _draw_line(matrix, x0, y0, x0, y1, color)
    _draw_line(matrix, x1, y0, x1, y1, color)


def _draw_triangle_outline(matrix, cx, y_top, width, height, color):
    if width <= 0 or height <= 0:
        return
    half_base = width // 2
    left = cx - half_base
    right = cx + half_base
    base_y = y_top + height
    _draw_line(matrix, cx, y_top, left, base_y, color)
    _draw_line(matrix, cx, y_top, right, base_y, color)
    _draw_line(matrix, left, base_y, right, base_y, color)


def _draw_tower_outline(matrix, cx, top_y, bottom_y, width, roof_height, color, roof_width=None):
    if roof_width is None:
        roof_width = width
    left = cx - width // 2
    right = cx + width // 2
    _draw_rect_outline(matrix, left, top_y, right, bottom_y, color)
    _draw_triangle_outline(matrix, cx, top_y - roof_height, roof_width, roof_height, color)


def render_castle(matrix):
    matrix.Clear()

    white = graphics.Color(245, 245, 245)

    w = matrix.width
    h = matrix.height
    if w < 10 or h < 10:
        return

    # Castle silhouette bounding box (start at bottom of board)
    castle_w = int(w * 0.88)
    castle_h = int(h * 0.90)
    x0 = (w - castle_w) // 2
    y0 = h - castle_h

    base_bottom = y0 + castle_h - 1
    base_top = y0 + int(castle_h * 0.64)
    mid_top = y0 + int(castle_h * 0.45)
    keep_top = y0 + int(castle_h * 0.26)

    base_left = x0 + int(castle_w * 0.05)
    base_right = x0 + int(castle_w * 0.95)

    # Base wall
    _draw_rect_outline(matrix, base_left, base_top, base_right, base_bottom, white)

    # Mid wall
    mid_left = x0 + int(castle_w * 0.22)
    mid_right = x0 + int(castle_w * 0.78)
    _draw_rect_outline(matrix, mid_left, mid_top, mid_right, base_top - 1, white)

    # Upper keep
    keep_left = x0 + int(castle_w * 0.38)
    keep_right = x0 + int(castle_w * 0.62)
    _draw_rect_outline(matrix, keep_left, keep_top, keep_right, mid_top - 1, white)

    center_x = x0 + castle_w // 2

    # Central spire
    spire_h = int(castle_h * 0.20)
    spire_w = int(castle_w * 0.18)
    spire_top = max(0, keep_top - spire_h)
    _draw_triangle_outline(matrix, center_x, spire_top, spire_w, spire_h, white)

    # Inner towers
    inner_offset = int(castle_w * 0.20)
    inner_w = int(castle_w * 0.12)
    inner_top = y0 + int(castle_h * 0.30)
    inner_roof_h = int(castle_h * 0.12)
    inner_roof_w = int(castle_w * 0.16)
    for sign in (-1, 1):
        cx = center_x + sign * inner_offset
        _draw_tower_outline(matrix, cx, inner_top, mid_top, inner_w, inner_roof_h, white, inner_roof_w)

    # Side main towers
    side_offset = int(castle_w * 0.32)
    side_w = int(castle_w * 0.16)
    side_top = y0 + int(castle_h * 0.40)
    side_roof_h = int(castle_h * 0.14)
    side_roof_w = int(castle_w * 0.20)
    for sign in (-1, 1):
        cx = center_x + sign * side_offset
        _draw_tower_outline(matrix, cx, side_top, base_top, side_w, side_roof_h, white, side_roof_w)

    # Outer corner turrets
    corner_offset = int(castle_w * 0.43)
    corner_w = int(castle_w * 0.10)
    corner_top = y0 + int(castle_h * 0.48)
    corner_roof_h = int(castle_h * 0.10)
    corner_roof_w = int(castle_w * 0.14)
    for sign in (-1, 1):
        cx = center_x + sign * corner_offset
        _draw_tower_outline(matrix, cx, corner_top, base_top, corner_w, corner_roof_h, white, corner_roof_w)

    # Crenellations on the base wall (outline blocks)
    crenel_h = max(1, int(castle_h * 0.03))
    crenel_w = max(1, int(castle_w * 0.05))
    crenel_gap = max(1, int(castle_w * 0.03))
    x = base_left + crenel_gap
    y_crenel_top = base_top - crenel_h
    while x + crenel_w < base_right - crenel_gap:
        _draw_rect_outline(matrix, x, y_crenel_top, x + crenel_w, base_top - 1, white)
        x += crenel_w + crenel_gap

    # Crenellations on the mid wall (outline blocks)
    mid_crenel_h = max(1, int(castle_h * 0.025))
    mid_crenel_w = max(1, int(castle_w * 0.04))
    mid_crenel_gap = max(1, int(castle_w * 0.035))
    x = mid_left + mid_crenel_gap
    y_mid_crenel = mid_top - mid_crenel_h
    while x + mid_crenel_w < mid_right - mid_crenel_gap:
        _draw_rect_outline(matrix, x, y_mid_crenel, x + mid_crenel_w, mid_top - 1, white)
        x += mid_crenel_w + mid_crenel_gap
