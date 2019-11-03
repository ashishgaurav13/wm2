import pyglet
from pyglet import gl
import numpy as np
from inspect import isfunction

import tools.pyglet as graphics
import tools.misc as utilities
import tools.math as wmath
import tools.design as design

class Car(graphics.Group):

    MAX_ACCELERATION = 2.0
    MAX_STEERING_ANGLE_RATE = 1.0
    VEHICLE_WHEEL_BASE = 1.7
    DT = 0.1
    DT_over_2 = DT / 2
    DT_2_over_3 = 2 * DT / 3
    DT_over_3 = DT / 3
    DT_over_6 = DT / 6
    VEHICLE_X = 2.5
    VEHICLE_Y = 1.7
    THETA_DEVIATION_ALLOWED = np.pi/2
    MAX_STEERING_ANGLE = np.pi/3
    SAFETY_GAP = 6.0
    SPEED_MAX = 11.176 # 11.176 = 40kmph

    # theta, psi cannot be specified, it is created based on direction
    def __init__(self, x, y, v, ego = False, direction = None, canvas = None,
        name = None):
        assert(type(direction) == wmath.Direction2D)
        assert(canvas != None)
        assert(name != None)
        self.name = name
        self.method = 'kinematic_bicycle_RK4'
        self.ego = ego
        self.direction = direction
        dir_angle = direction.angle()
        self.original_features = {
            'x': self.parse_init_function(x),
            'y': self.parse_init_function(y),
            'v': self.parse_init_function(v),
            'theta': self.parse_init_function(dir_angle)
        }
        self.of = self.original_features
        self.features = design.Features({
            'x': self.of['x'](), 'y': self.of['y'](), 'v': self.of['v'](),
            'acc': 0.0, 'psi_dot': 0.0, 'psi': 0.0,
            'theta': self.of['theta'](),
        })
        self.f = self.features # shorthand
        self.canvas = canvas
        ox, oy, scale = canvas.ox, canvas.oy, canvas.scale
        x = ox + self.f['x'] * scale
        y = oy + self.f['y'] * scale
        w = self.VEHICLE_X * scale
        h = self.VEHICLE_Y * scale
        vehicle_url = utilities.get_file_from_root('static/vehicle.png')
        car = graphics.Image(vehicle_url, x, y, w, h, np.rad2deg(self.f['theta']), anchor_centered=True)
        super().__init__(items = [car])
    
    # Produces an intialization function; if passed a constant
    # lambda-wrap it, else return it as is
    def parse_init_function(self, x):
        if not isfunction(x):
            return lambda: x
        else:
            return x

    # Reset this agent
    def reset(self):
        for attr in ['x', 'y', 'v', 'theta']:
            self.f[attr] = self.of[attr]()

    def which_regions(self, filter_fn = None):
        in_regions = []
        for region in self.canvas.allowed_regions:
            if type(region) == wmath.Box and region.inside(self.f['x'], self.f['y']):
                if filter_fn and filter_fn(region):
                    in_regions += [region]
        return in_regions
    
    def any_regions(self, search_word = ''):
        return self.which_regions(filter_fn = lambda x: search_word in x.name) != []
    
    # Lp norm of displacement from (x, y)
    def Lp(self, x, y, p = 2):
        return float(np.linalg.norm([self.f['x']-x, self.f['y']-y], p))

    # return relevant agents (TODO: just cars for now)
    def get_relevant_agents(self):
        all_cars = [agent for agent in self.canvas.agents if agent is not self]
        rx1, rx2, ry1, ry2 = self.lane_boundaries() # cars we really want to consider
        within_range_cars = [agent for agent in all_cars \
            if (rx1 <= agent.f['x'] <= rx2 and ry1 <= agent.f['y'] <= ry2)]
        return within_range_cars

    # Return lane bounds (x1, x2, y1, y2)
    # Either x1/x2 or y1/y2 is supposed to be -np.inf/np.inf
    # Will not work if direction is not exactly vertical or horizontal
    def lane_boundaries(self):
        assert(self.direction.mode in ['+x', '-x', '+y', '-y'])
        assert(self.canvas.lane_width > 0)
        half_lane_width = self.canvas.lane_width / 2.0
        if 'x' in self.direction.mode:
            return -np.inf, np.inf, self.f['y']-half_lane_width, self.f['y']+half_lane_width
        else:
            return self.f['x']-half_lane_width,self.f['x']+half_lane_width, -np.inf, np.inf

    # Return the displacement, agent that is the closest and in the forward direction as self
    def closest_agent_forward(self, list_of_agents):
        my_direction = self.direction
        ret_agent = None
        min_displacement = np.inf
        for agent in list_of_agents:
            displacement_unit_vector = wmath.Direction2D([agent.f['x']-self.f['x'], agent.f['y']-self.f['y']])
            displacement = np.sqrt((agent.f['x']-self.f['x'])**2+(agent.f['y']-self.f['y'])**2)
            if displacement < min_displacement and displacement_unit_vector.dot(my_direction) > 0:
                min_displacement = displacement
                ret_agent = agent
        return {'d': min_displacement, 'o': ret_agent}
    
    # if we do max deceleration, what is the distance needed to stop?
    def minimal_stopping_distance(self):
        curr_v = self.f['v']
        return (0.5 * curr_v ** 2) / self.MAX_ACCELERATION

    # if we do max deceleration, what is the distance needed to stop?
    def minimal_stopping_distance_from_max_v(self):
        curr_v = self.SPEED_MAX
        return (0.5 * curr_v ** 2) / self.MAX_ACCELERATION

    # Return the stop region displacement, StopRegion that is closest and in the
    # forward direction as self
    # Will not work if direction is not exactly vertical or horizontal
    def closest_stop_region_forward(self):
        assert(self.direction.mode in ['+x', '-x', '+y', '-y'])
        rx1, rx2, ry1, ry2 = self.lane_boundaries() # clipping boundaries
        ret_stopregion = None
        min_displacement = np.inf
        my_direction = self.direction
        if 'x' in self.direction.mode: stopregions = self.canvas.stopx
        if 'y' in self.direction.mode: stopregions = self.canvas.stopy
        for stopregion in stopregions:
            stopregion = stopregion.clip(rx1, rx2, ry1, ry2)
            if stopregion.empty(): continue
            centerx, centery = stopregion.center
            displacement_unit_vector = wmath.Direction2D([centerx-self.f['x'], centery-self.f['y']])
            displacement = np.sqrt((centerx-self.f['x'])**2+(centery-self.f['y'])**2)
            if displacement < min_displacement and displacement_unit_vector.dot(my_direction) > 0:
                min_displacement = displacement
                ret_stopregion = stopregion
        return {'d': min_displacement, 'o': ret_stopregion}
    
    # Return the intersection displacement, Intersection that is closest and in the
    # forward direction as self
    # Will not work if direction is not exactly vertical or horizontal
    def closest_intersection_forward(self):
        assert(self.direction.mode in ['+x', '-x', '+y', '-y'])
        rx1, rx2, ry1, ry2 = self.lane_boundaries() # clipping boundaries
        ret_intersection = None
        min_displacement = np.inf
        my_direction = self.direction
        for intersection in self.canvas.intersections:
            clipped_intersection = intersection.clip(rx1, rx2, ry1, ry2) # clip to compute displacement,
                # but return the complete intersection
            if intersection.empty(): continue
            centerx, centery = clipped_intersection.center
            displacement_unit_vector = wmath.Direction2D([centerx-self.f['x'], centery-self.f['y']])
            displacement = np.sqrt((centerx-self.f['x'])**2+(centery-self.f['y'])**2)
            if displacement < min_displacement and displacement_unit_vector.dot(my_direction) > 0:
                min_displacement = displacement
                ret_intersection = intersection
        return {'d': min_displacement, 'o': ret_intersection}
    
    def any_agents_in_intersection(self, intersection):
        all_agents = [agent for agent in self.canvas.agents if agent is not self]
        for agent in all_agents:
            if intersection.inside(agent.f['x'], agent.f['y']): return True
        return False

    def in_any_intersection(self):
        for intersection in self.canvas.intersections:
            if intersection.inside(self.f['x'], self.f['y']): return True
        return False

    # produces the control input (acc, psi_dot) needed for aggressive driving
    # closest car = CC, closest stop region = CSR
    # (1) if CC is facing ego
    #       => emergency stop
    # (2) if after max deceleration for both ego and CC, ego violates SAFETY_GAP
    #       => emergency stop
    # (3) allowed to go towards both CC and CSR
    #       => LQR movement
    # (4) allowed to go towards CC and no stop region coming up
    #       => LQR movement
    # (5) in stop region and has priority and intersection is clear
    #       => free road acceleration
    # (6) in stop region and does not have priority or intersection is not clear
    #       => emergency stop
    # (7) allowed to go towards CSR and should decelerate
    #       => decelerate to stop
    # (8) just drive
    def aggressive_driving(self, debug = False):

        if not hasattr(self, 'complexcontroller'):
            K1, K2 = 31.6228, 7.9527
            A1, A2 = 100.0, 10.0 # arbitrary constants
            self.complexcontroller = design.ComplexController(
                predicates = dict(
                    ego = lambda p: self,
                    cars = lambda p: self.get_relevant_agents(),
                    cc = lambda p: p['ego'].closest_agent_forward(p['cars']),
                    csr = lambda p: p['ego'].closest_stop_region_forward(),
                    cif = lambda p: p['ego'].closest_intersection_forward(),
                    cc_after_stop = [
                        lambda p: p['cc']['o'],
                        lambda p: p['cc']['d']+p['cc']['o'].minimal_stopping_distance(),
                    ],
                    ego_after_stop = lambda p: p['ego'].minimal_stopping_distance(),
                    sufficiently_away_sr = lambda p: 2 * p['ego'].minimal_stopping_distance(),
                    allowed_to_go_towards_cc = [
                        lambda p: p['cc']['o'],
                        lambda p: p['cc']['d']-p['ego'].SAFETY_GAP > 0,
                    ],
                    allowed_to_go_towards_sr = [
                        lambda p: p['csr']['o'],
                        lambda p: p['csr']['d'] > p['sufficiently_away_sr'],
                    ],
                    should_decelerate_to_stop = [
                        lambda p: p['csr']['o'],
                        lambda p: p['csr']['d'] > 0 and \
                            (p['csr']['d'] <= p['ego'].minimal_stopping_distance_from_max_v()) and \
                            (p['csr']['d'] <= p['ego'].minimal_stopping_distance())
                    ],
                    within_stop_region = lambda p: p['ego'].any_regions('StopRegion'),
                    intersection_clear = [
                        lambda p: p['cif']['o'],
                        lambda p: not p['ego'].any_agents_in_intersection(p['cif']['o']),
                    ],
                    in_any_intersection = lambda p: p['ego'].in_any_intersection(),
                    requested_priority = [
                        lambda p: p['within_stop_region'] and 'intersection_clear' in p and p['intersection_clear'],
                        lambda p: p['ego'].canvas.priority_manager.request_priority(p['ego'].name),
                    ],
                    has_priority = lambda p: p['ego'].canvas.priority_manager.has_priority(p['ego'].name),
                    released_priority = [
                        lambda p: not p['within_stop_region'] and p['has_priority'],
                        lambda p: p['ego'].canvas.priority_manager.release_priority(p['ego'].name),
                    ],
                    # Not used
                    # init_angle = lambda p: p['ego'].direction.angle(),
                    # desired_angle = lambda p: (p['init_angle']-np.pi/2) % (2*np.pi),
                    # curr_angle = lambda p: p['ego'].theta,
                ),
                multipliers = dict(
                    displacement = [
                        lambda p: p['cc']['o'],
                        lambda p: p['cc']['d']-p['ego'].SAFETY_GAP,
                    ],
                    sr_displacement = [
                        lambda p: p['csr']['o'],
                        lambda p: 0-p['csr']['d'],
                    ],
                    speed = [
                        lambda p: p['cc']['o'],
                        lambda p: p['cc']['o'].f['v']-p['ego'].f['v'],
                    ],
                    free_road_speed = lambda p: p['ego'].SPEED_MAX-p['ego'].f['v'],
                    decelerate_speed = lambda p: 0-p['ego'].f['v'],
                    # Not used
                    # theta = lambda p: p['desired_angle']-p['curr_angle'],
                ),
                controllers = [
                    design.Controller( # (1)
                        lambda p: p['cc']['o'] and p['cc']['o'].direction.dot(p['ego'].direction) <= 0,
                        lambda p, m: (-self.MAX_ACCELERATION, 0),
                        name = 'EmergencyStop0',
                    ),
                    design.Controller( # (2)
                        lambda p: 'cc_after_stop' in p and \
                            p['cc_after_stop']-p['ego_after_stop'] <= p['ego'].SAFETY_GAP,
                        lambda p, m: (-self.MAX_ACCELERATION, 0),
                        name = 'EmergencyStop1',
                    ),
                    design.Controller( # (7)
                        lambda p: 'should_decelerate_to_stop' in p and p['should_decelerate_to_stop'],
                        lambda p, m: (K1*m['sr_displacement']+K2*m['decelerate_speed'], 0),
                        name = 'Decelerate0',
                    ),
                    design.Controller( # (5)
                        lambda p: (p['within_stop_region'] and 'intersection_clear' in p and p['intersection_clear'] and \
                            p['has_priority']) or p['in_any_intersection'],
                        lambda p, m: (A1*m['free_road_speed'], 0), # 0.3 * m['theta'] can make it change direction; but 
                            # it needs to be more general (TODO)
                        name = 'Enter0'
                    ),
                    design.Controller( # (6)
                        lambda p: p['within_stop_region'],
                        lambda p, m: (-self.MAX_ACCELERATION, 0),
                        name = 'EmergencyStop2',
                    ),
                    design.Controller( # (4)
                        lambda p: not p['within_stop_region'] and \
                            'allowed_to_go_towards_cc' in p and p['allowed_to_go_towards_cc'],
                        lambda p, m: (p['cc']['o'].f['acc'] + K1*m['displacement'] + K2*m['speed'], 0),
                        name = 'LQR0',
                    ),
                    design.DefaultController( # (8)
                        lambda p, m: (A2*m['free_road_speed'], 0),
                        name = 'Default0',
                    )
                ],
            )

        ret_acc, ret_psi_dot = self.complexcontroller.control(debug = debug)
        ret_acc = np.clip(ret_acc, -self.MAX_ACCELERATION, self.MAX_ACCELERATION)
        ret_psi_dot = np.clip(ret_psi_dot, -self.MAX_STEERING_ANGLE_RATE, self.MAX_STEERING_ANGLE_RATE)
        return ret_acc, ret_psi_dot

    # u[0] is acceleration (-2, +2)
    # u[1] is psi_dot (-1, +1)
    # Note that positive psi_dot will increase counter-clockwise angle
    def step(self, u):
        # input clipping.
        if abs(u[0]) > self.MAX_ACCELERATION:
            self.f['acc'] = np.clip(u[0], -self.MAX_ACCELERATION, self.MAX_ACCELERATION)
        else:
            self.f['acc'] = u[0]

        if abs(u[1]) > self.MAX_STEERING_ANGLE_RATE:
            self.f['psi_dot'] = np.clip(u[1], -self.MAX_STEERING_ANGLE_RATE,
                self.MAX_STEERING_ANGLE_RATE)
        else:
            self.f['psi_dot'] = u[1]

        theta = 2*np.pi-self.f['theta']
        if self.method == 'kinematic_bicycle_RK4':
            K1x = self.f['v'] * np.cos(theta)
            K1y = self.f['v'] * np.sin(theta)
            K1th = self.f['v'] * np.tan(self.f['psi']) / self.VEHICLE_WHEEL_BASE

            theta_temp = theta + self.DT_over_2 * K1th
            v_temp = max([0.0, self.f['v'] + self.DT_over_2 * self.f['acc']])
            psi_temp = np.clip(self.f['psi'] + self.DT_over_2 * self.f['psi_dot'],
                -self.MAX_STEERING_ANGLE, self.MAX_STEERING_ANGLE)

            K23x = np.cos(theta_temp)
            K23y = np.sin(theta_temp)
            K23th = v_temp * np.tan(psi_temp) / self.VEHICLE_WHEEL_BASE

            theta_temp = theta + self.DT_over_2 * K23th

            K23x += np.cos(theta_temp)
            K23y += np.sin(theta_temp)
            K23x *= v_temp
            K23y *= v_temp

            v_temp = max([0.0, self.f['v'] + self.DT * self.f['acc']])
            psi_temp = np.clip(self.f['psi'] + self.DT * self.f['psi_dot'],
                -self.MAX_STEERING_ANGLE, self.MAX_STEERING_ANGLE)

            K4x = v_temp * np.cos(theta_temp)
            K4y = v_temp * np.sin(theta_temp)
            K4th = v_temp * np.tan(psi_temp) / self.VEHICLE_WHEEL_BASE

            self.f['x'] += self.DT_over_6 * (K1x + K4x) + self.DT_over_3 * K23x
            self.f['y'] += self.DT_over_6 * (K1y + K4y) + self.DT_over_3 * K23y
            theta += self.DT_over_6 * (K1th + K4th) + self.DT_2_over_3 * K23th
            self.f['theta'] = 2*np.pi-theta
            self.f['v'] = v_temp
            self.psi = psi_temp

        elif self.method == 'kinematic_bicycle_Euler':
            self.f['x'] += self.DT * self.f['v'] * np.cos(theta)
            self.f['y'] += self.DT * self.f['v'] * np.sin(theta)
            theta += self.DT * self.f['v'] * np.tan(self.f['psi']) / self.VEHICLE_WHEEL_BASE
            self.f['theta'] = 2*np.pi-theta

            self.f['v'] = max([0.0, self.f['v'] + self.DT * self.f['acc']])
            self.f['psi'] = np.clip(self.f['psi'] + self.DT * self.f['psi_dot'],
                -self.MAX_STEERING_ANGLE, self.MAX_STEERING_ANGLE)

        elif self.method == 'point_mass_Euler':
            dv = self.f['acc'] * self.DT
            dx = self.f['v'] * self.DT
            self.f['v'] += dv
            if self.f['v'] < 0: self.f['v'] = 0
            self.f['x'] += self.direction.value[0] * dx
            self.f['y'] += self.direction.value[1] * dx

        else:
            # point_mass_RK4 method is not implemented yet.
            raise ValueError

        if 'kinematic' in self.method:
            theta = 2*np.pi-self.f['theta']
            orig_theta = 2*np.pi-self.direction.angle()
            if theta > orig_theta+self.THETA_DEVIATION_ALLOWED:
                theta = orig_theta+self.THETA_DEVIATION_ALLOWED
            if theta < orig_theta-self.THETA_DEVIATION_ALLOWED:
                theta = orig_theta-self.THETA_DEVIATION_ALLOWED
            self.f['theta'] = 2*np.pi-theta
        
        ox, oy, scale = self.canvas.ox, self.canvas.oy, self.canvas.scale
        x = ox + self.f['x'] * scale
        y = oy + self.f['y'] * scale
        self.items[0].items[0].update(x = x, y = y, rotation = np.rad2deg(self.f['theta']))