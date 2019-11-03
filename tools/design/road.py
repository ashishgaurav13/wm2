import pyglet
from pyglet import gl
from numpy import rad2deg

import tools.pyglet as graphics
import tools.misc as utilities

class Grass(graphics.Group):

    def __init__(self, canvas):
        bg_url = utilities.get_file_from_root('static/background.png')
        bg = graphics.InfiniteRepeatImage(bg_url, canvas)
        super().__init__(items = [bg])

class Lane(graphics.Group):

    def __init__(self, x1, x2, y1, y2):
        assert(x1 <= x2 and y1 <= y2)
        self.direction = 'x' if abs(y1-y2) < abs(x1-x2) else 'y'
        self.width = abs(y1-y2) if self.direction == 'x' else abs(x1-x2)
        self.length = abs(x1-x2) if self.direction == 'x' else abs(y1-y2)
        road_url = utilities.get_file_from_root('static/road.png')
        road = graphics.Image(road_url, x1, y1, x2-x1, y2-y1)
        super().__init__(items = [road])

class Intersection(graphics.Group):

    def __init__(self, x1, x2, y1, y2):
        assert(x1 <= x2 and y1 <= y2)
        road_url = utilities.get_file_from_root('static/road.png')
        intersection = graphics.Image(road_url, x1, y1, x2-x1, y2-y1)
        super().__init__(items = [intersection])

class StopRegion(graphics.Group):

    def __init__(self, x1, x2, y1, y2):
        assert(x1 <= x2 and y1 <= y2)
        region = graphics.Rectangle(x1, x2, y1, y2,
            color = (0.8, 0.8, 0.8, 1))
        super().__init__(items = [region])

# Two lane road
class TwoLaneRoad(graphics.Group):

    def __init__(self, x1, x2, y1, y2, sep):
        assert(x1 <= x2 and y1 <= y2)
        self.direction = 'x' if abs(y1-y2) < abs(x1-x2) else 'y'
        self.width = abs(y1-y2) / 2 if self.direction == 'x' else abs(x1-x2) / 2
        self.length = abs(x1-x2) if self.direction == 'x' else abs(y1-y2)
        if self.direction == 'x':
            super().__init__(items = [
                Lane(x1, x2, y1, y1+self.width),
                Lane(x1, x2, y1+self.width, y2),
                graphics.Rectangle(x1, x2, y1+self.width-sep/2, y1+self.width+sep/2,
                    color = (1, 1, 1, 1)),
            ])
        else:
            super().__init__(items = [
                Lane(x1, x1+self.width, y1, y2),
                Lane(x1+self.width, x2, y1, y2),
                graphics.Rectangle(x1+self.width-sep/2, x1+self.width+sep/2, y1, y2,
                    color = (1, 1, 1, 1)),
            ])