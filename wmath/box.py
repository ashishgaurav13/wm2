import numpy as np

class Box:

    def __init__(self, x1, x2, y1, y2, name):
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2
        self.name = name
    
    def __repr__(self):
        return "%s <%.2f,%.2f,%.2f,%.2f>" % (self.name, self.x1, self.x2,
            self.y1, self.y2)