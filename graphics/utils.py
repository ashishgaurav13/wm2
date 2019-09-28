import pyglet
from pyglet import gl

import graphics
import wm2, wmath

class Canvas(pyglet.window.Window):

    def __init__(self, w, h, items = []):
        super().__init__(w, h)
        self.w, self.h = w, h
        self.items = items
        self.on_draw = self.event(self.on_draw)
        self.ox, self.oy, self.scale = 0, 0, 1.0
        self.allowed_regions = []
        self.static_ids = {'Lane': 0, 'Intersection': 0, 'TwoLaneRoad': 0}
    
    def get_static_id_and_increment(self, x):
        assert(x in self.static_ids.keys())
        curr_id = self.static_ids[x]
        self.static_ids[x] += 1
        return "%s%d" % (x, curr_id)

    def show_allowed_regions(self):
        for item in self.allowed_regions:
            print(item)

    def add_static_elements(self, *args):
        for item in args:

            if item[0] == 'Grass':
                self.items += [wm2.Grass(self)]

            elif item[0] == 'Lane':
                x1, x2, y1, y2 = item[1:]
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, 
                    self.get_static_id_and_increment('Lane'))]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.ox+y1*self.scale, self.ox+y2*self.scale
                self.items += [wm2.Lane(x1, x2, y1, y2)]

            elif item[0] == 'Intersection':
                x1, x2, y1, y2 = item[1:]
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, 
                    self.get_static_id_and_increment('Intersection'))]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.ox+y1*self.scale, self.ox+y2*self.scale
                self.items += [wm2.Intersection(x1, x2, y1, y2)]

            elif item[0] == 'TwoLaneRoad':
                x1, x2, y1, y2, sep = item[1:]
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, 
                    self.get_static_id_and_increment('TwoLaneRoad'))]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.oy+y1*self.scale, self.oy+y2*self.scale
                sep = sep*self.scale
                self.items += [wm2.TwoLaneRoad(x1, x2, y1, y2, sep)]

    def on_draw(self):
        self.clear()
        for item in self.items:
            item.draw()

    def render(self):
        pyglet.app.run()
    
    def set_origin(self, x, y):
        self.ox, self.oy = x, y
    
    def set_scale(self, scale):
        self.scale = scale