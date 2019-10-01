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

    # theta, psi cannot be specified, it is created based on direction
    def __init__(self, x, y, v, ego = False, 
        direction = None, canvas = None):
        assert(type(direction) == wmath.Direction2D)
        assert(canvas != None)
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
        car = graphics.Image(vehicle_url, x, y, w, h, np.rad2deg(self.theta))
        super().__init__(items = [car])
    
    def which_regions(self):
        for region in self.canvas.allowed_regions:
            if type(region) == wmath.Box and region.inside(self.x, self.y):
                print(region)

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

        while abs(self.theta) >= 2 * np.pi:
            self.theta -= np.sign(self.theta) * 2 * np.pi
        
        if self.theta > self.direction.angle()+self.THETA_DEVIATION_ALLOWED:
            self.theta = self.direction.angle()+self.THETA_DEVIATION_ALLOWED
        if self.theta < self.direction.angle()-self.THETA_DEVIATION_ALLOWED:
            self.theta = self.direction.angle()-self.THETA_DEVIATION_ALLOWED
        
        ox, oy, scale = canvas.ox, canvas.oy, canvas.scale
        x = ox + self.x * scale
        y = oy + self.y * scale
        self.items[0].items[0].update(x = x, y = y, rotation = np.rad2deg(self.theta))