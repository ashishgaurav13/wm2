import pyglet
from pyglet import gl
import numpy as np

import graphics
import utilities
import wmath

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
    THETA_DEVIATION_ALLOWED = np.pi/3
    SAFETY_GAP = 6.0
    SPEED_MAX = 11.176 # 11.176 = 40kmph

    # theta, psi cannot be specified, it is created based on direction
    def __init__(self, x, y, v, ego = False, direction = None, canvas = None,
        name = None):
        assert(type(direction) == wmath.Direction2D)
        assert(canvas != None)
        assert(name != None)
        self.name = name
        self.x, self.y, self.v = x, y, v
        self.acc, self.psi_dot = 0.0, 0.0
        self.method = 'kinematic_bicycle_RK4'
        self.ego = ego
        self.direction = direction
        self.theta = direction.angle()
        self.psi = direction.angle()
        self.canvas = canvas
        ox, oy, scale = canvas.ox, canvas.oy, canvas.scale
        x = ox + self.x * scale
        y = oy + self.y * scale
        w = self.VEHICLE_X * scale
        h = self.VEHICLE_Y * scale
        vehicle_url = utilities.get_file_from_root('static/vehicle.png')
        car = graphics.Image(vehicle_url, x, y, w, h, np.rad2deg(self.theta), anchor_centered=True)
        super().__init__(items = [car])
    
    def which_regions(self, filter_fn = None):
        in_regions = []
        for region in self.canvas.allowed_regions:
            if type(region) == wmath.Box and region.inside(self.x, self.y):
                if filter_fn and filter_fn(region):
                    in_regions += [region]
        return in_regions
    
    # return relevant agents (TODO: just cars for now)
    def get_relevant_agents(self):
        all_cars = [agent for agent in self.canvas.agents if agent is not self]
        rx1, rx2, ry1, ry2 = self.lane_boundaries() # cars we really want to consider
        within_range_cars = [agent for agent in all_cars \
            if (rx1 <= agent.x <= rx2 and ry1 <= agent.y <= ry2)]
        return within_range_cars

    # Return lane bounds (x1, x2, y1, y2)
    # Either x1/x2 or y1/y2 is supposed to be -np.inf/np.inf
    # Will not work if direction is not exactly vertical or horizontal
    def lane_boundaries(self):
        assert(self.direction.mode in ['+x', '-x', '+y', '-y'])
        assert(self.canvas.lane_width > 0)
        half_lane_width = self.canvas.lane_width / 2.0
        if 'x' in self.direction.mode:
            return -np.inf, np.inf, self.y-half_lane_width, self.y+half_lane_width
        else:
            return self.x-half_lane_width,self.x+half_lane_width, -np.inf, np.inf

    # Return the displacement, agent that is the closest and in the forward direction as self
    def closest_agent_forward(self, list_of_agents):
        my_direction = self.direction
        ret_agent = None
        min_displacement = np.inf
        for agent in list_of_agents:
            displacement_unit_vector = wmath.Direction2D([agent.x-self.x, agent.y-self.y])
            displacement = np.sqrt((agent.x-self.x)**2+(agent.y-self.y)**2)
            if displacement < min_displacement and displacement_unit_vector.dot(my_direction) > 0:
                min_displacement = displacement
                ret_agent = agent
        return min_displacement, ret_agent
    
    # if we do max deceleration, what is the distance needed to stop?
    def minimal_stopping_distance(self):
        curr_v = self.v
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
            displacement_unit_vector = wmath.Direction2D([centerx-self.x, centery-self.y])
            displacement = np.sqrt((centerx-self.x)**2+(centery-self.y)**2)
            if displacement < min_displacement and displacement_unit_vector.dot(my_direction) > 0:
                min_displacement = displacement
                ret_stopregion = stopregion
        return min_displacement, ret_stopregion
    
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
            displacement_unit_vector = wmath.Direction2D([centerx-self.x, centery-self.y])
            displacement = np.sqrt((centerx-self.x)**2+(centery-self.y)**2)
            if displacement < min_displacement and displacement_unit_vector.dot(my_direction) > 0:
                min_displacement = displacement
                ret_intersection = intersection
        return min_displacement, ret_intersection
    
    def any_agents_in_intersection(self, intersection):
        all_agents = [agent for agent in self.canvas.agents if agent is not self]
        for agent in all_agents:
            if intersection.inside(agent.x, agent.y): return True
        return False

    def in_any_intersection(self):
        for intersection in self.canvas.intersections:
            if intersection.inside(self.x, self.y): return True
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
    def aggressive_driving(self):
        case_num = None
        K1, K2 = 31.6228, 7.9527
        A1, A2 = 100.0, 10.0 # arbitrary constants
        all_cars = [agent for agent in self.canvas.agents if agent is not self]
        rx1, rx2, ry1, ry2 = self.lane_boundaries() # cars we really want to consider
        within_range_cars = [agent for agent in all_cars \
            if (rx1 <= agent.x <= rx2 and ry1 <= agent.y <= ry2)]
        cc_displacement, cc = self.closest_agent_forward(within_range_cars)
        csr_displacement, csr = self.closest_stop_region_forward()
        cif_displacement, cif = self.closest_intersection_forward()
        if cc: cc_after_stop = cc_displacement + cc.minimal_stopping_distance() # how far
            # would CC be from where ego is currently?
        ego_after_stop = self.minimal_stopping_distance() # how far will ego be from
            # where ego is currently?
        my_direction = self.direction
        sufficient_distance_from_stop_region = 2*self.minimal_stopping_distance()
        # multipliers; positive value should allow positive acceleration,
        # negative value should decelerate
        if cc: displacement_multiplier = cc_displacement-self.SAFETY_GAP
        if csr: stop_region_displacement_multiplier = 0-csr_displacement # always used to decelerate
        if cc: speed_multiplier = cc.v-self.v
        free_road_speed_multiplier = self.SPEED_MAX-self.v
        decelerate_speed_multiplier = 0-self.v
        # booleans
        if cc: allowed_to_go_towards_cc = cc_displacement-self.SAFETY_GAP > 0
        if csr: allowed_to_go_towards_stop_region = csr_displacement > sufficient_distance_from_stop_region
        if csr: should_decelerate_to_stop = (csr_displacement > 0) and \
            (csr_displacement <= self.minimal_stopping_distance_from_max_v()) and \
            (csr_displacement <= self.minimal_stopping_distance())
        no_stop_region_coming_up = csr == None
        within_stop_region = self.which_regions(filter_fn = lambda x: 'StopRegion' in x.name) != []
        if cif: intersection_clear = not self.any_agents_in_intersection(cif)
        if within_stop_region and (cif and intersection_clear): self.canvas.priority_manager.request_priority(self.name)
        has_priority = self.canvas.priority_manager.has_priority(self.name)
        if not within_stop_region and has_priority: self.canvas.priority_manager.release_priority(self.name)
        # (1)
        if cc and cc.direction.dot(my_direction) <= 0:
            case_num = 1
            ret_acc = -self.MAX_ACCELERATION
        # (2)
        elif cc and cc_after_stop-ego_after_stop <= self.SAFETY_GAP:
            case_num = 2
            ret_acc = -self.MAX_ACCELERATION
        # (3)
        elif cc and csr and allowed_to_go_towards_cc and allowed_to_go_towards_stop_region:
            case_num = 3
            ret_acc = cc.acc + K1*displacement_multiplier + K2*speed_multiplier
        # (4)        
        elif cc and allowed_to_go_towards_cc and no_stop_region_coming_up:
            case_num = 4
            ret_acc = cc.acc + K1*displacement_multiplier + K2*speed_multiplier
        # (5)
        elif within_stop_region and has_priority and (cif and intersection_clear):
            case_num = 5
            ret_acc = A1*free_road_speed_multiplier
        # (6)
        elif within_stop_region and (not has_priority or not (cif and intersection_clear)):
            case_num = 6
            ret_acc = -self.MAX_ACCELERATION
        # (7)
        elif csr and should_decelerate_to_stop:
            case_num = 7
            ret_acc = K1*stop_region_displacement_multiplier + K2*decelerate_speed_multiplier
        # (8)
        else:
            case_num = 8
            ret_acc = A2*free_road_speed_multiplier

        ret_acc = np.clip(ret_acc, -self.MAX_ACCELERATION, self.MAX_ACCELERATION)
        # print('Case%d: %.2f' % (case_num, ret_acc))
        return ret_acc, 0

    def step(self, u):
        # input clipping.
        if abs(u[0]) > self.MAX_ACCELERATION:
            self.acc = np.clip(u[0], -self.MAX_ACCELERATION, self.MAX_ACCELERATION)
        else:
            self.acc = u[0]

        if abs(u[1]) > self.MAX_STEERING_ANGLE_RATE:
            self.psi_dot = np.clip(u[1], -self.MAX_STEERING_ANGLE_RATE,
                self.MAX_STEERING_ANGLE_RATE)
        else:
            self.psi_dot = u[1]

        if self.method == 'kinematic_bicycle_RK4':
            K1x = self.v * np.cos(self.theta)
            K1y = self.v * np.sin(self.theta)
            K1th = self.v * np.tan(self.psi) / self.VEHICLE_WHEEL_BASE

            theta_temp = self.theta + DT_over_2 * K1th
            v_temp = max([0.0, self.v + DT_over_2 * self.acc])
            psi_temp = np.clip(self.psi + DT_over_2 * self.psi_dot,
                -self.MAX_STEERING_ANGLE, self.MAX_STEERING_ANGLE)

            K23x = np.cos(theta_temp)
            K23y = np.sin(theta_temp)
            K23th = v_temp * np.tan(psi_temp) / self.VEHICLE_WHEEL_BASE

            theta_temp = self.theta + self.DT_over_2 * K23th

            K23x += np.cos(theta_temp)
            K23y += np.sin(theta_temp)
            K23x *= v_temp
            K23y *= v_temp

            v_temp = max([0.0, self.v + self.DT * self.acc])
            psi_temp = np.clip(self.psi + self.DT * self.psi_dot,
                -self.MAX_STEERING_ANGLE, self.MAX_STEERING_ANGLE)

            K4x = v_temp * np.cos(theta_temp)
            K4y = v_temp * np.sin(theta_temp)
            K4th = v_temp * np.tan(psi_temp) / self.VEHICLE_WHEEL_BASE

            self.x += self.DT_over_6 * (K1x + K4x) + self.DT_over_3 * K23x
            self.y += self.DT_over_6 * (K1y + K4y) + self.DT_over_3 * K23y
            self.theta += self.DT_over_6 * (K1th + K4th) + self.DT_2_over_3 * K23th
            self.v = v_temp
            self.psi = psi_temp

        elif self.method == 'kinematic_bicycle_Euler':
            self.x += self.DT * self.v * np.cos(self.theta)
            self.y += self.DT * self.v * np.sin(self.theta)
            self.theta += self.DT * self.v * np.tan(self.psi) / self.VEHICLE_WHEEL_BASE

            self.v = max([0.0, self.v + DT * self.acc])
            self.psi = np.clip(self.psi + DT * self.psi_dot,
                -self.MAX_STEERING_ANGLE, self.MAX_STEERING_ANGLE)

        elif self.method == 'point_mass_Euler':
            dv = self.acc * self.DT
            dx = self.v * self.DT
            self.v += dv
            if self.v < 0: self.v = 0
            self.x += self.direction.value[0] * dx
            self.y += self.direction.value[1] * dx

        else:
            # point_mass_RK4 method is not implemented yet.
            raise ValueError

        if 'kinematic' in self.method:
            while abs(self.theta) >= 2 * np.pi:
                self.theta -= np.sign(self.theta) * 2 * np.pi
            if self.theta > self.direction.angle()+self.THETA_DEVIATION_ALLOWED:
                self.theta = self.direction.angle()+self.THETA_DEVIATION_ALLOWED
            if self.theta < self.direction.angle()-self.THETA_DEVIATION_ALLOWED:
                self.theta = self.direction.angle()-self.THETA_DEVIATION_ALLOWED
        
        ox, oy, scale = self.canvas.ox, self.canvas.oy, self.canvas.scale
        x = ox + self.x * scale
        y = oy + self.y * scale
        self.items[0].items[0].update(x = x, y = y, rotation = np.rad2deg(self.theta))