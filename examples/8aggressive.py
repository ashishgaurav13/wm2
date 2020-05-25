import os, sys; sys.path += ["."]
import pyglet
import tools.pyglet as graphics
import tools.design as design
import tools.math as wmath
import tools.misc as misc

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
    ['Veh', -15, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
    ['Veh', +45, +2.5, 0.0, wmath.Direction2D(mode = '-x')],
    ['Veh', +15, +2.5, 0.0, wmath.Direction2D(mode = '-x')],
    ['Veh', +2.5, -45, 0.0, wmath.Direction2D(mode = '+y')],
    ['Veh', +2.5, -15, 0.0, wmath.Direction2D(mode = '+y')],
    ['Veh', -2.5, +45, 0.0, wmath.Direction2D(mode = '-y')],
    ['Veh', -2.5, +15, 0.0, wmath.Direction2D(mode = '-y')],
]

canvas = graphics.Canvas(600, 600,
    static_elements, agents,
    ox = 300, oy = 300, scale = 600/100
)
default_policy = lambda agent: agent.aggressive_driving()
env = design.Environment(canvas, default_policy)
ego = env.agents[env.ego_id]

# Empty reward structure
env.reward_structure({}, {}, [], [], [], round_to = 3)

# Empty state
ego_fn = lambda agent, rs: {}
other_fn = lambda agent, rs: {}
env.specify_state(ego_fn, other_fn)

# Make ready
env.make_ready()

# Render loop
obs = env.reset()
done = False
while not done:
    action = ego.aggressive_driving()
    obs, reward, done, info = env.step(action)
    env.render()