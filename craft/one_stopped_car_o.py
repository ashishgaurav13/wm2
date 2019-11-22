import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import tools.misc as utilities
import numpy as np

class OneStoppedCarOEnv(design.Environment):

    def __init__(self):

        # Draw canvas
        static_elements = [
            ['Grass'],
            ['TwoLaneRoad', -50, +50, -5, +5, 0.5],
        ]
        agents = [
            ['Ego', lambda: -45 + np.random.rand() * 10, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
            ['Veh', lambda: -15 + np.random.rand() * 10, +2.5, 0.0, wmath.Direction2D(mode = '+x')]
        ]
        canvas = graphics.Canvas(600, 600,
            static_elements, agents,
            ox = 300, oy = 300, scale = 600/100)
        default_policy = lambda c: [0, 0]
        
        # Zero pad by 3 features to create 7 + 4 + 2 = 13 features for continual learning
        super().__init__(canvas, default_policy, zero_pad = 2)

        # Reward structure
        expected_finish_steps = 150
        existence_punishment = -1.0
        d = {
            "mid_lane": -2.5,
            "car": lambda p, t: p['v'][1],
            "deviation_mid_lane": lambda p, t: abs(p['mid_lane']-p['ego'].f['y']),
            "moving_horizontally": lambda p, t: -5 <= p['ego'].f['y'] <= 5
        }
        p = {
            "stopped": lambda p, t: t > 0 and p['ego'].f['v'] == 0,
            "out_of_bounds": lambda p, t: (not p['ego'].any_regions()) or (not p['moving_horizontally']),
            "near_goal": lambda p, t: p['ego'].Lp(45, -2.5) <= 2.5,
            "collided": lambda p, t: p['ego'].Lp(p['car'].f['x'], p['car'].f['y']) <= 3.0,
        }
        r = [
            ["true", existence_punishment, 'satisfaction'],
        ]
        t = [
            ['out_of_bounds', -100, 'satisfaction'],
            ["stopped", -100, 'satisfaction'],
            ["collided", -100, 'satisfaction'],
        ]
        s = [
            ['near_goal', 100 + expected_finish_steps, 'satisfaction'],
        ]
        self.reward_structure(d, p, r, t, s, round_to = 3)

        # Specify state
        ego_fn = lambda agent, rs: utilities.combine_dicts(agent.f.get_dict(), rs._p.get_dict())
        other_fn = lambda agent, rs: {}
        self.specify_state(ego_fn, other_fn)

        # Finally
        self.make_ready()