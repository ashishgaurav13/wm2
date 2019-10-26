import pyglet
import graphics
import wm2
import wmath

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
    ['Veh', -45, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
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
    ox = 300, oy = 300, scale = 600/100)
default_policy = lambda agent: agent.aggressive_driving()
env = wm2.Environment(canvas, default_policy)

# Debugging properties
# env.debug['state_inspect'] = True => try out env.state()
# env.debug['intersection_enter'] = True

obs = env.reset()
done = False

while not done:
    obs, reward, done, info = env.step(None) # no ego
    env.render()