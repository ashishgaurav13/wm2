import pyglet
from pyglet import gl

import tools.design as design
import tools.math as wmath

class Canvas(pyglet.window.Window):

    ALLOWED_STATIC_ELEMENTS = ['Grass', 'Lane', 'Intersection', 'TwoLaneRoad']
    ALLOWED_AGENTS = ['Ego', 'Veh']

    def __init__(self, w, h, static, agents, ox = 0.0, oy = 0.0, scale = 1.0):
        super().__init__(w, h, visible = False)
        self.w, self.h = w, h
        self.items = []
        self.on_draw = self.event(self.on_draw)
        self.ox, self.oy, self.scale = ox, oy, scale
        self.allowed_regions = []
        self.agents = []
        self.static_ids = {'Lane': 0, 'Intersection': 0,
            'TwoLaneRoad': 0, 'StopRegion': 0}
        self.agent_ids = {'Car': 0, 'Ego': 0}
        self.lane_width = 0
        # Only x/y stop regions are supported
        self.stopx = []
        self.stopy = []
        self.intersections = []
        self.priority_manager = design.PriorityManager()
        self.minx, self.maxx = self.transform_x_inv(0), self.transform_x_inv(w)
        self.miny, self.maxy = self.transform_y_inv(0), self.transform_y_inv(h)
        self._add_static_elements(*static)
        self._add_agents(*agents)

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

    # Sets canvas lane width
    # This function enforces a consistent lane width throughout the canvas
    # If it detects a different lane width, it will throw an error
    def set_lane_width(self, x1, x2, y1, y2):
        lane_width = abs(x1-x2) if abs(x1-x2) < abs(y1-y2) else abs(y1-y2)
        if self.lane_width == 0: self.lane_width = lane_width
        else: assert(self.lane_width == lane_width)

    def show_allowed_regions(self):
        for item in self.allowed_regions:
            print(item)

    def _add_static_elements(self, *args):
        for item in args:
            assert(type(item) == list)

            if item[0] == 'Grass':
                self.items += [design.Grass(self)]

            elif item[0] == 'Lane':
                x1, x2, y1, y2 = item[1:]
                sid, boxname = self.get_static_id_and_increment('Lane')
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                self.set_lane_width(x1, x2, y1, y2)
                x1, x2 = self.transform_x(x1), self.transform_x(x2)
                y1, y2 = self.transform_y(y1), self.transform_y(y2)
                self.items += [design.Lane(x1, x2, y1, y2)]

            elif item[0] == 'Intersection':
                x1, x2, y1, y2 = item[1:]
                sid, boxname = self.get_static_id_and_increment('Intersection')
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                self.intersections.append(self.allowed_regions[-1])
                x1, x2 = self.transform_x(x1), self.transform_x(x2)
                y1, y2 = self.transform_y(y1), self.transform_y(y2)
                self.items += [design.Intersection(x1, x2, y1, y2)]

            elif item[0] == 'StopRegionX' or item[0] == 'StopRegionY':
                x1, x2, y1, y2 = item[1:]
                sid, boxname = self.get_static_id_and_increment('StopRegion')
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                if 'X' in item[0]: self.stopx.append(self.allowed_regions[-1])
                if 'Y' in item[0]: self.stopy.append(self.allowed_regions[-1])
                x1, x2 = self.transform_x(x1), self.transform_x(x2)
                y1, y2 = self.transform_y(y1), self.transform_y(y2)
                self.items += [design.StopRegion(x1, x2, y1, y2)]

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
                    self.set_lane_width(x1, x1+width, y1, y2)
                    self.set_lane_width(x1+width, x2, y1, y2)
                else:
                    width = abs(y1-y2) / 2
                    sid1, _ = self.get_static_id_and_increment('Lane')
                    laneboxname1 = "%s_Lane%d" % (boxname, sid1)
                    sid2, _ = self.get_static_id_and_increment('Lane')
                    laneboxname2 = "%s_Lane%d" % (boxname, sid2)
                    self.allowed_regions += [wmath.Box(x1, x2, y1, y1+width, laneboxname1)]
                    self.allowed_regions += [wmath.Box(x1, x2, y1+width, y2, laneboxname2)]
                    self.set_lane_width(x1, x2, y1, y1+width)
                    self.set_lane_width(x1, x2, y1+width, y2)
                self.allowed_regions += [wmath.Box(x1, x2, y1, y2, boxname)]
                x1, x2 = self.transform_x(x1), self.transform_x(x2)
                y1, y2 = self.transform_y(y1), self.transform_y(y2)
                sep = sep*self.scale
                self.items += [design.TwoLaneRoad(x1, x2, y1, y2, sep)]

            else:
                print('Unsupported static element: %s' % item[0])
                print('Allowed static elements: %s' % self.ALLOWED_STATIC_ELEMENTS)
                exit(0)

    def _add_agents(self, *args):
        ego_taken = False
        for item in args:
            assert(type(item) == list)

            if item[0] == 'Ego':
                assert(not ego_taken)
                ego_taken = True
                x, y, v, direction = item[1:]
                aid, aname = self.get_agent_id_and_increment('Ego')
                self.agents += [design.Car(x, y, v, True, direction, self, name = aname)]

            elif item[0] == 'Veh':
                x, y, v, direction = item[1:]
                aid, aname = self.get_agent_id_and_increment('Car')
                self.agents += [design.Car(x, y, v, False, direction, self, name = aname)]
                self.agents[-1].method = 'kinematic_bicycle_Euler' # 'point_mass_Euler'
            
            else:
                print('Unsupported agent: %s' % item[0])
                print('Allowed agents: %s' % self.ALLOWED_AGENTS)
                exit(0)

    def on_draw(self):
        self.clear()
        for item in self.items:
            item.draw()
        drew_agents = 0
        for agent in self.agents:
            if self.is_agent_in_bounds(agent):
                agent.draw()
                drew_agents += 1
        return drew_agents

    def is_agent_in_bounds(self, agent):
        return self.minx <= agent.f['x'] <= self.maxx and \
            self.miny <= agent.f['y'] <= self.maxy

    def render(self):
        pyglet.app.run()
        
    def transform_x(self, x):
        return self.ox+x*self.scale
    
    def transform_y(self, y):
        return self.oy+y*self.scale
    
    def transform_x_inv(self, x):
        return (x-self.ox) / self.scale
    
    def transform_y_inv(self, y):
        return (y-self.oy) / self.scale
    