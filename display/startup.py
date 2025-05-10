from driver import graphics

from utils import debug

def render_mickey_logo(matrix):
    """
    Draw a Mickey Mouse silhouette in a fixed 40×40 region centered on the matrix.
    This won't fill the entire board, but ensures a consistent shape.

    Circle definitions (within a 40×40 box):
      - Head:     center (20, 24), radius = 12
      - Left ear: center (10, 12), radius = 8
      - Right ear: center (30, 12), radius = 8

    Adjust these numbers to get the exact proportions you prefer.
    """

    board_width = matrix.width
    board_height = matrix.height

    # The "design box" for Mickey is 40×40 pixels
    shape_width = 40
    shape_height = 40

    # Compute offsets so that the 40×40 shape is centered on the board
    offset_x = (board_width - shape_width) // 2
    offset_y = (board_height - shape_height) // 2

    # Define a small helper function to check circle membership
    def in_circle(px, py, cx, cy, r):
        return (px - cx) ** 2 + (py - cy) ** 2 <= r * r

    # White color for Mickey’s silhouette
    color_white = graphics.Color(255, 255, 255)

    # Loop over every pixel in the 40×40 box
    for sy in range(shape_height):
        for sx in range(shape_width):
            # Check if (sx, sy) is inside any of the 3 circles
            inside_head = in_circle(sx, sy, 20, 24, 12)
            inside_left_ear = in_circle(sx, sy, 10, 12, 8)
            inside_right_ear = in_circle(sx, sy, 30, 12, 8)

            if inside_head or inside_left_ear or inside_right_ear:
                # Draw a single pixel using DrawLine (x, y) to (x, y)
                matrix_x = offset_x + sx
                matrix_y = offset_y + sy
                graphics.DrawLine(matrix, matrix_x, matrix_y, matrix_x, matrix_y, color_white)

    debug.info("Rendered fixed-size Mickey silhouette at center of the board.")
