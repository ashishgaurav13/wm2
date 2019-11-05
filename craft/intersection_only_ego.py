import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import tools.misc as utilities
import numpy as np

class IntersectionOnlyEgoEnv(design.Environment):
    """
    Intersection environment with just one vehicle, that is,
    the ego. Ego is placed at the leftmost end and has to
    reach the rightmost end.

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

    def __init__(self):

        # Draw canvas
        static_elements = [
            ['Grass'],
            ['TwoLaneRoad', -50, -5, -5, +5, 0.5],
            ['TwoLaneRoad', +5, +50, -5, +5, 0.5],
            ['TwoLaneRoad', -5, +5, -50, -5, 0.5],
            ['TwoLaneRoad', -5, +5, +5, +50, 0.5],
            ['Intersection', -5, +5, -5, +5],
            ['StopRegionX', -10, -5, -5, 0],
            ['StopRegionX', +5, +10, 0, +5],
            ['StopRegionY', -5, 0, +5, +10],
            ['StopRegionY', 0, +5, -10, -5],
        ]
        agents = [
            ['Ego', lambda: -45 + np.random.rand() * 10 , -2.5, 0.0, wmath.Direction2D(mode = '+x')],
        ]
        canvas = graphics.Canvas(600, 600,
            static_elements, agents,
            ox = 300, oy = 300, scale = 600/100)
        super().__init__(canvas)

        # Reward structure
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
            ["true", lambda p, t: -p['deviation_mid_lane']/5, 'satisfaction'],
        ]
        t = [
            ['out_of_bounds', -100, 'satisfaction'],
            ["stopped", -100, 'satisfaction'],
        ]
        s = [
            ['near_goal', 100, 'satisfaction'],
        ]
        self.reward_structure(d, p, r, t, s, round_to = 3)

        # Specify state
        ego_fn = lambda agent, rs: utilities.combine_dicts(agent.f.get_dict(), rs._p.get_dict())
        other_fn = lambda agent, rs: agent.f.get_dict()
        self.specify_state(ego_fn, other_fn)

        # Finally
        self.make_ready()