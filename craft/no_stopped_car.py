import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import tools.misc as utilities
import numpy as np

class NoStoppedCarEnv(design.Environment):
    """
    Environment with just one vehicle, that is,
    the ego. Ego is placed at the leftmost end and has to
    reach the rightmost end.
    
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
        true, -p['deviation_mid_lane']/5 + existence_punishment (S)

    Termination:
        out_of_bounds, -100 (S)
        stopped, -100 (S)

    Success:
        near_goal, 100 + expected_number_of_steps (S)
    """

    def __init__(self):

        # Draw canvas
        static_elements = [
            ['Grass'],
            ['TwoLaneRoad', -50, +50, -5, +5, 0.5],
        ]
        agents = [
            ['Ego', lambda: -45 + np.random.rand() * 10, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
        ]
        canvas = graphics.Canvas(600, 600,
            static_elements, agents,
            ox = 300, oy = 300, scale = 600/100)
        super().__init__(canvas)

        # Reward structure
        # Reward of -1.0 every step
        # When finished, +200, since we should be able to solve in < 200 steps for sure
        expected_finish_steps = 150
        existence_punishment = -1.0
        d = {
            "mid_lane": -2.5,
            "deviation_mid_lane": lambda p, t: abs(p['mid_lane']-p['ego'].f['y']),
            "moving_horizontally": lambda p, t: -5 <= p['ego'].f['y'] <= 5
        }
        p = {
            "stopped": lambda p, t: t > 0 and p['ego'].f['v'] == 0,
            "out_of_bounds": lambda p, t: (not p['ego'].any_regions()) or (not p['moving_horizontally']),
            "near_goal": lambda p, t: p['ego'].Lp(45, -2.5) <= 2.5,
        }
        r = [
            ["true", lambda p, t: -p['deviation_mid_lane']/5 + existence_punishment, 'satisfaction'],
        ]
        t = [
            ['out_of_bounds', -100, 'satisfaction'],
            ["stopped", -100, 'satisfaction'],
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