#!/usr/bin/sudo
import sys
import time
import os
from driver import RGBMatrix
from driver import graphics
import debug


def render_hello_world(matrix):
    # Set the text and position to render
    text = "Hello World!"
    x_position = 10  # You can adjust the position as needed
    y_position = 10  # You can adjust the position as needed

    # Create a font object, assuming the graphics module provides this functionality
    font = graphics.Font()  # Adjust based on how the font should be initialized in the library
    font.LoadFont("C:\\Users\\Xxjcl\\Documents\\GitHub\\Disney-LED-QueueVision\\assets\\fonts\\patched\\4x6.bdf")  # Adjust this path

    # Draw the text on the matrix
    graphics.DrawText(matrix, font=font, x=x_position, y=y_position, color=(255, 255, 255), text=text)



def main():
    # Initialize the matrix options using the appropriate object type
    from driver import RGBMatrixOptions

    # Define the options in an object rather than a dictionary
    options = RGBMatrixOptions()
    options.cols = 64  # Set the matrix width
    options.rows = 32  # Set the matrix height
    options.chain_length = 1  # Adjust based on your setup
    options.hardware_mapping = 'adafruit-hat'  # Adjust this based on your setup

    # Initialize the matrix with the options object
    matrix = RGBMatrix(options=options)

    try:
        render_hello_world(matrix)
        time.sleep(60)  # Keep displaying "Hello World!" for 5 seconds
    except Exception as e:
        debug.exception(f"An error occurred: {e}")
    finally:
        matrix.Clear()  # Clear the matrix after rendering


if __name__ == "__main__":
    main()
