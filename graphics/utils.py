import pyglet
from pyglet import gl

class Canvas(pyglet.window.Window):

    def __init__(self, w, h, items = []):
        super().__init__(w, h)
        self.items = items
        self.on_draw = self.event(self.on_draw)
    
    def on_draw(self):
        self.clear()
        for item in self.items:
            item.draw()

    def render(self):
        pyglet.app.run()