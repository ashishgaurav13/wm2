import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import numpy as np

class IntersectionOnlyEgoEnv(design.Environment):
    """
    Intersection environment with just one vehicle, that is,
    the ego. Ego is placed at the leftmost end and has to
    reach the rightmost end.

    Definitions:
        mid_lane: -2.5
        deviation_mid_lane: abs(p['mid_lane'] - p['ego'].f['y'])

    Propositions:
        stopped: p['ego'].f['v'] == 0,
        out_of_bounds: not p['ego'].any_regions(),
        near_goal: p['ego'].Lp(+45, -2.5) <= 2.5,

    Reward:
        true, 10 * np.exp(-p['deviation_mid_lane']) (S)

    Termination:
        stopped, -1 (S)
        out_of_bounds, -1 (S)
    
    Success:
        near_goal, 1 (S)
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
            ['Ego', -45, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
        ]
        canvas = graphics.Canvas(600, 600,
            static_elements, agents,
            ox = 300, oy = 300, scale = 600/100)
        super().__init__(canvas)

        # Reward structure
        d = {
            "mid_lane": -2.5,
            "deviation_mid_lane": lambda p, t: abs(p['mid_lane']-p['ego'].f['y'])
        }
        p = {
            "stopped": lambda p, t: p['ego'].f['v'] == 0,
            "out_of_bounds": lambda p, t: not p['ego'].any_regions(),
            "near_goal": lambda p, t: p['ego'].Lp(45, -2.5) <= 2.5,
        }
        r = [
            ["true", lambda p, t: 10 * np.exp(-p['deviation_mid_lane']), 'satisfaction']
        ]
        t = [
            ["stopped", -1, 'satisfaction'],
            ['out_of_bounds', -1, 'satisfaction'],
        ]
        s = [
            ['near_goal', 1, 'satisfaction'],
        ]
        self.reward_structure(d, p, r, t, s, round_to = 3, clip_to = [-1, 1])