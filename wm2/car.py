import pyglet
from pyglet import gl
from numpy import rad2deg

import graphics
import utilities

class Car(graphics.Group):

    def __init__(self, x, y, w = 2.5, h = 1.7, theta = 0):
        car_image_url = utilities.get_file_from_root('static/vehicle.png')
        car = graphics.Image(car_image_url, x, y, w, h, rotation = rad2deg(theta))
        super().__init__(items = [car])