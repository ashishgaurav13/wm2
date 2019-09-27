import pyglet
from pyglet import gl

# Basic shape, dummy class
class Shape: pass

# Basic rectangle
class Rectangle(Shape):
    
    def __init__(self, x1, y1, x2, y2, color = (0, 0, 0, 255)):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.color = color
    
    def draw(self):
        gl.glBegin(gl.GL_QUADS)
        gl.glColor4f(*self.color)
        gl.glVertex3f(self.x1, self.y1, 0)
        gl.glVertex3f(self.x1, self.y2, 0)
        gl.glVertex3f(self.x2, self.y2, 0)
        gl.glVertex3f(self.x2, self.y1, 0)
        gl.glEnd()
