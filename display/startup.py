from driver import graphics

from display.fireworks import launch_side_fireworks
from utils import debug

def _draw_mickey_silhouette(matrix, log=True):
    board_width = matrix.width
    board_height = matrix.height

    shape_width = 40
    shape_height = 40

    offset_x = (board_width - shape_width) // 2
    offset_y = (board_height - shape_height) // 2

    def in_circle(px, py, cx, cy, r):
        return (px - cx) ** 2 + (py - cy) ** 2 <= r * r

    color_white = graphics.Color(255, 255, 255)
    silhouette_pixels = set()

    for sy in range(shape_height):
        for sx in range(shape_width):
            inside_head = in_circle(sx, sy, 20, 24, 12)
            inside_left_ear = in_circle(sx, sy, 10, 12, 8)
            inside_right_ear = in_circle(sx, sy, 30, 12, 8)

            if inside_head or inside_left_ear or inside_right_ear:
                matrix_x = offset_x + sx
                matrix_y = offset_y + sy
                graphics.DrawLine(matrix, matrix_x, matrix_y, matrix_x, matrix_y, color_white)
                silhouette_pixels.add((matrix_x, matrix_y))

    if log:
        debug.info("Rendered fixed-size Mickey silhouette at center of the board.")
    return offset_x, offset_y, shape_width, shape_height, silhouette_pixels


def _firework_positions(offset_x, shape_width, board_width):
    left_x = max(0, offset_x - 4)
    right_x = min(board_width - 1, offset_x + shape_width + 4)
    if left_x >= right_x:
        mid = board_width // 2
        return mid, mid
    return left_x, right_x


def render_mickey_logo(matrix, fireworks=False):
    matrix.Clear()
    offset_x, offset_y, shape_width, shape_height, silhouette = _draw_mickey_silhouette(matrix)

    if not fireworks:
        return

    left_x, right_x = _firework_positions(offset_x, shape_width, matrix.width)

    def redraw(matrix_inner):
        _draw_mickey_silhouette(matrix_inner, log=False)

    launch_side_fireworks(matrix, left_x, right_x, silhouette)
