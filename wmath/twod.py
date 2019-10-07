import numpy as np

class Box:

    def __init__(self, x1, x2, y1, y2, name):
        assert(x1 <= x2 and y1 <= y2)
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2
        self.name = name
        self.center = np.array([(self.x1+self.x2)/2, (self.y1+self.y2)/2])
    
    def __repr__(self):
        return "%s <%.2f,%.2f,%.2f,%.2f>" % (self.name, self.x1, self.x2,
            self.y1, self.y2)
    
    def inside(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2
    
    def empty(self):
        return self.x1 == self.x2 or self.y1 == self.y2

    def clip(self, x1, x2, y1, y2):
        assert(x1 <= x2 and y1 <= y2)
        new_name = self.name+"_clipped" # TODO: assign unique ID?
        cx1, cx2, cy1, cy2 = self.x1, self.x2, self.y1, self.y2
        if x1 <= x2 <= cx1: cx1, cx2 = cx1, cx1
        elif cx2 <= x1 <= x2: cx1, cx2 = cx2, cx2
        else:
            if x1 >= cx1: cx1 = x1
            if x2 <= cx2: cx2 = x2
        if y1 <= y2 <= cy1: cy1, cy2 = cy1, cy1
        elif cy2 <= y1 <= y2: cy1, cy2 = cy2, cy2
        else:
            if y1 >= cy1: cy1 = y1
            if y2 <= cy2: cy2 = y2
        return Box(cx1, cx2, cy1, cy2, new_name)

class Direction2D:

    def __init__(self, value = None, mode = None):
        assert(mode in ['+x', '-x', '+y', '-y', None])
        assert(not(value != None and mode != None))
        self.mode = mode
        if value != None: self.value = value
        elif mode == '+x': self.value = np.array([1.0, 0.0])
        elif mode == '-x': self.value = np.array([-1.0, 0.0])
        elif mode == '+y': self.value = np.array([0.0, 1.0])
        elif mode == '-y': self.value = np.array([0.0, -1.0])
        else:
            print("Unknown direction?")
            exit(0)
        self.normalize()
    
    def normalize(self):
        mag = np.sqrt(np.sum(np.square(self.value)))
        if mag > 0:
            self.value /= mag
    
    def transform_matrix(self, angle_rad):
        return np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)],
        ])

    def angle(self):
        x, y = self.value
        if x == 1 and y == 0: return 2*np.pi - 0.0
        elif x == 0 and y == 1: return 2*np.pi - np.pi/2
        elif x == -1 and y == 0: return 2*np.pi - np.pi
        elif x == 0 and y == -1: return 2*np.pi - 3*np.pi/2
        if x > 0 and y > 0: pre, t = 0.0, np.matmul(self.transform_matrix(0.0), self.value)
        elif x < 0 and y > 0: pre, t = np.pi/2, np.matmul(self.transform_matrix(- np.pi / 2), self.value)
        elif x < 0 and y < 0: pre, t = np.pi, np.matmul(self.transform_matrix(- np.pi), self.value)
        elif x > 0 and y < 0: pre, t = 3*np.pi/2, np.matmul(self.transform_matrix(- 3*np.pi / 2), self.value)
        return 2*np.pi - (pre + np.arctan(np.divide(t[1], t[0])))
    
    # return dot product with x
    def dot(self, x):
        assert(type(x) == Direction2D)
        return np.dot(self.value, x.value)