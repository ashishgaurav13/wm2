import pyglet
from pyglet import gl

import graphics
import wm2, wmath

class Canvas(pyglet.window.Window):

    ALLOWED_STATIC_ELEMENTS = ['Grass', 'Lane', 'Intersection', 'TwoLaneRoad']
    ALLOWED_AGENTS = ['Ego', 'Veh']

    def __init__(self, w, h, items = []):
        super().__init__(w, h)
        self.w, self.h = w, h
        self.items = items
        self.on_draw = self.event(self.on_draw)
        self.ox, self.oy, self.scale = 0, 0, 1.0
        self.allowed_regions = []
        self.agents = []
        self.static_ids = {'Lane': 0, 'Intersection': 0,
            'TwoLaneRoad': 0, 'StopRegion': 0}
        self.agent_ids = {'Car': 0}

    def get_static_id_and_increment(self, x):
        assert(x in self.static_ids.keys())
        curr_id = self.static_ids[x]
        self.static_ids[x] += 1
        return curr_id, "%s%d" % (x, curr_id)

    def get_agent_id_and_increment(self, x):
        assert(x in self.agent_ids.keys())
        curr_id = self.agent_ids[x]
        self.agent_ids[x] += 1
        return curr_id, "%s%d" % (x, curr_id)

    def show_allowed_regions(self):
        for item in self.allowed_regions:
            print(item)

    def add_static_elements(self, *args):
        for item in args:
            assert(type(item) == list)

            if item[0] == 'Grass':
                self.items += [wm2.Grass(self)]

            elif item[0] == 'Lane':
                x1, x2, y1, y2 = item[1:]
                sid, boxname = self.get_static_id_and_increment('Lane')
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.ox+y1*self.scale, self.ox+y2*self.scale
                self.items += [wm2.Lane(x1, x2, y1, y2)]

            elif item[0] == 'Intersection':
                x1, x2, y1, y2 = item[1:]
                sid, boxname = self.get_static_id_and_increment('Intersection')
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.ox+y1*self.scale, self.ox+y2*self.scale
                self.items += [wm2.Intersection(x1, x2, y1, y2)]

            elif item[0] == 'StopRegion':
                x1, x2, y1, y2 = item[1:]
                sid, boxname = self.get_static_id_and_increment('StopRegion')
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.ox+y1*self.scale, self.ox+y2*self.scale
                self.items += [wm2.StopRegion(x1, x2, y1, y2)]

            elif item[0] == 'TwoLaneRoad':
                x1, x2, y1, y2, sep = item[1:]
                sid, boxname = self.get_static_id_and_increment('TwoLaneRoad')
                if abs(x1-x2) < abs(y1-y2):
                    width = abs(x1-x2) / 2
                    sid1, _ = self.get_static_id_and_increment('Lane')
                    laneboxname1 = "%s_Lane%d" % (boxname, sid1)
                    sid2, _ = self.get_static_id_and_increment('Lane')
                    laneboxname2 = "%s_Lane%d" % (boxname, sid2)
                    self.allowed_regions += [wmath.Box(x1, x1+width, y1, y2, laneboxname1)]
                    self.allowed_regions += [wmath.Box(x1+width, x2, y1, y2, laneboxname2)]
                else:
                    width = abs(y1-y2) / 2
                    sid1, _ = self.get_static_id_and_increment('Lane')
                    laneboxname1 = "%s_Lane%d" % (boxname, sid1)
                    sid2, _ = self.get_static_id_and_increment('Lane')
                    laneboxname2 = "%s_Lane%d" % (boxname, sid2)
                    self.allowed_regions += [wmath.Box(x1, x2, y1, y1+width, laneboxname1)]
                    self.allowed_regions += [wmath.Box(x1, x2, y1+width, y2, laneboxname2)]
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                x1, x2 = self.ox+x1*self.scale, self.ox+x2*self.scale
                y1, y2 = self.oy+y1*self.scale, self.oy+y2*self.scale
                sep = sep*self.scale
                self.items += [wm2.TwoLaneRoad(x1, x2, y1, y2, sep)]

            else:
                print('Unsupported static element: %s' % item[0])
                print('Allowed static elements: %s' % self.ALLOWED_STATIC_ELEMENTS)
                exit(0)

    def add_agents(self, *args):
        ego_taken = False
        for item in args:
            assert(type(item) == list)

            if item[0] == 'Ego':
                assert(not ego_taken)
                ego_taken = True
                x, y, v, direction = item[1:]
                aid, aname = self.get_agent_id_and_increment('Car')
                self.agents += [wm2.Car(x, y, v, True, direction, self, name = aname)]

            elif item[0] == 'Veh':
                x, y, v, direction = item[1:]
                aid, aname = self.get_agent_id_and_increment('Car')
                self.agents += [wm2.Car(x, y, v, False, direction, self, name = aname)]
                self.agents[-1].method = 'point_mass_Euler'
            
            else:
                print('Unsupported agent: %s' % item[0])
                print('Allowed agents: %s' % self.ALLOWED_AGENTS)
                exit(0)

    def on_draw(self):
        self.clear()
        for item in self.items:
            item.draw()
        for agent in self.agents:
            agent.draw()

    def render(self):
        pyglet.app.run()
    
    def set_origin(self, x, y):
        self.ox, self.oy = x, y
    
    def set_scale(self, scale):
        self.scale = scale