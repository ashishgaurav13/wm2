import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import tools.misc as utilities
import numpy as np

class OneStoppedCar(design.Environment):
    """
    Environment with ego and one stopped car, close to ego.
    Ego is placed at the leftmost end and has to reach the rightmost end.

    Existence punishment = -1.0
    Expected number of steps = 150

    Definitions:
        mid_lane: -2.5
        deviation_mid_lane: abs(p['mid_lane'] - p['ego'].f['y'])
        moving_horizontally: lambda p, t: -5 <= p['ego'].f['y'] <= 5

    Propositions:
        stopped: t > 0 and p['ego'].f['v'] == 0,
        out_of_bounds: (not p['ego'].any_regions()) or (not p['moving_horizontally']),
        near_goal: p['ego'].Lp(+45, -2.5) <= 2.5,

    Reward:
        true, -p['deviation_mid_lane']/5 (S)

    Termination:
        out_of_bounds, -100 (S)
        stopped, -100 (S)

    Success:
        near_goal, 100 (S)
    """

    def __init__(self, discrete = False):

        # Draw canvas
        static_elements = [
            ['Grass'],
            ['TwoLaneRoad', -50, +50, -5, +5, 0.5],
        ]
        agents = [
            ['Ego', lambda: -45 + np.random.rand() * 10, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
            ['Veh', lambda: -15 + np.random.rand() * 10, -2.5, 0.0, wmath.Direction2D(mode = '+x')]
        ]
        canvas = graphics.Canvas(600, 600,
            static_elements, agents,
            ox = 300, oy = 300, scale = 600/100)
        default_policy = lambda c: [0, 0]

        # Zero pad by 2 features to create 7 + 4 + 2 = 13 features for continual learning
        # super().__init__(canvas, default_policy, zero_pad = 2, discrete = discrete)
        super().__init__(canvas, default_policy, zero_pad = 0, discrete = discrete)

        # Reward structure
        d = {
            "mid_lane": -2.5,
            "car": lambda p, t: p['v'][1],
            "deviation_mid_lane": lambda p, t: abs(p['mid_lane']-p['ego'].f['y']),
            "moving_horizontally": lambda p, t: -5 <= p['ego'].f['y'] <= 5
        }
        p = {
            "stopped": lambda p, t: t > 0 and p['ego'].f['v'] == 0,
            "out_of_bounds": lambda p, t: (not p['ego'].any_regions()) or (not p['moving_horizontally']),
            "past_car": lambda p, t: p['ego'].f['x'] > p['car'].f['x'] + 10,
            "collided": lambda p, t: p['ego'].Lp(p['car'].f['x'], p['car'].f['y']) <= 3.0,
        }
        # Reward of -1.0 every step
        # When finished, +150, since we should be able to solve in < 150 steps for sure
        expected_finish_steps = 150
        existence_punishment = -1.0
        r = [
            ["true", existence_punishment, 'satisfaction'],
        ]
        t = [
            ['out_of_bounds', -100, 'satisfaction'],
            ["stopped", -100, 'satisfaction'],
            ["collided", -100, 'satisfaction'],
        ]
        s = [
            ['past_car', 100 + expected_finish_steps, 'satisfaction'],
        ]
        self.reward_structure(d, p, r, t, s, round_to = 3)

        # Specify state
        ego_fn = lambda agent, rs: utilities.combine_dicts(agent.f.get_dict(), rs._p.get_dict())
        def ego_fn2(agent, rs):
            d1 = agent.f.get_dict()
            d2 = rs._p.get_dict()
            return utilities.combine_dicts(d1, {
                "stopped": d2["stopped"],
                "out_of_bounds": d2["out_of_bounds"],
                "near_goal_osco": -1,
                "collided_osco": -1,
                "past_car_osc": d2["past_car"],
                "collided_osc": d2["collided"],
            })
        other_fn = lambda agent, rs: {}
        self.specify_state(ego_fn2, other_fn)

        # Finally
        self.make_ready()