import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import tools.misc as utilities
import numpy as np

class WaitPriorityEnv(design.Environment):
    """
    Environment with stopped ego and three stopped cars and each having
    a different priority. Ego has to enter the intersection at the correct priority number.

    Definitions:
        my_turn_number: lambda p, t: np.random.randint(len(p['v']))
        moving_horizontally: lambda p, t: -5 <= p['ego'].f['y'] <= 5

    Propositions:
        out_of_bounds: (not p['ego'].any_regions()) or (not p['moving_horizontally']),
        my_turn: p['ego'].canvas.priority_manager.expecting == my_turn_number
        correct_entry: my_turn and p['ego'].Lp(5, 0) <= 2.5
        wrong_entry: (not my_turn) and p['ego'].in_any_intersection()

    Reward:
        true, 0 (S)

    Termination:
        out_of_bounds, -100 (S)
        wrong_entry, -100 (S)

    Success:
        correct_entry, 100 (S)
    """

    def __init__(self):

        np.random.seed()
        self.order = list(np.random.permutation(4))
        # print(self.order)

        # Draw canvas
        static_elements = [
            ['Grass'],
            ['TwoLaneRoad', -50, -5, -5, +5, 0.5],
            ['TwoLaneRoad', +5, +50, -5, +5, 0.5],
            ['TwoLaneRoad', -5, +5, -50, -5, 0.5],
            ['TwoLaneRoad', -5, +5, +5, +50, 0.5],
            ['Intersection', -5, +5, -5, +5],
            ['StopRegionX', -10, -5, -5, +5],
            ['StopRegionY', -5, +5, +5, +10],
        ]
        agents = [
            ['Ego', -7.5, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
            ['Veh', -7.5, +2.5, 0.0, wmath.Direction2D(mode = '+x')],
            ['Veh', -2.5, +7.5, 0.0, wmath.Direction2D(mode = '-y')],
            ['Veh', +2.5, +7.5, 0.0, wmath.Direction2D(mode = '-y')],
        ]
      
        canvas = graphics.Canvas(600, 600,
            static_elements, agents,
            ox = 300, oy = 300, scale = 600/100,
            ordered = True, order = self.order)
        default_policy = lambda c: c.aggressive_driving()
        super().__init__(canvas, default_policy)

        # Reward structure
        d = {
            "my_turn_number": lambda p, t: self.order[0],
            "moving_horizontally": lambda p, t: -5 <= p['ego'].f['y'] <= 5,
        }
        p = {
            "out_of_bounds": lambda p, t: (not p['ego'].any_regions()) or (not p['moving_horizontally']),
            "my_turn": lambda p, t: p['ego'].canvas.priority_manager.expecting == p['my_turn_number'] and \
                not p['ego'].any_agents_in_intersection(p['ego'].canvas.intersections[0]),
            "correct_entry": lambda p, t: p['my_turn'] and p['ego'].Lp(0, 0, p=np.inf) <= 5,
            "wrong_entry": lambda p, t: (not p['my_turn']) and p['ego'].in_any_intersection(),
            "no_movement": lambda p, t: t > 100 and p['my_turn'],
        }
        r = [
            ["true", 0, 'satisfaction'],
            ["my_turn", -0.25, 'satisfaction'],
        ]
        t = [
            ['out_of_bounds', -100, 'satisfaction'],
            ["wrong_entry", -100, 'satisfaction'],
            ["no_movement", -100, 'satisfaction'],
        ]
        s = [
            ['correct_entry', 100, 'satisfaction'],
        ]
        self.reward_structure(d, p, r, t, s, round_to = 3)

        # Specify state
        ego_fn = lambda agent, rs: utilities.combine_dicts(agent.f.get_dict(), rs._p.get_dict())
            # {k: v for k, v in rs._p.get_dict().items() if k not in ["correct_entry", "wrong_entry", "no_movement"]})
        other_fn = lambda agent, rs: {}
        self.specify_state(ego_fn, other_fn)

        # Finally
        self.make_ready()
    
    def reset(self):
        np.random.seed()
        self.order = list(np.random.permutation(4))
        self.canvas.priority_manager.reset_order(self.order)
        # print(self.order)
        return super().reset()
