import pyglet
import graphics
import wm2
import wmath

canvas = graphics.Canvas(600, 600, ox = 300, oy = 300, scale = 600/100)
canvas.add_static_elements(
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
)

# Add agents
canvas.add_agents(
    ['Veh', -45, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
    ['Veh', -15, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
    ['Veh', +45, +2.5, 0.0, wmath.Direction2D(mode = '-x')],
    ['Veh', +15, +2.5, 0.0, wmath.Direction2D(mode = '-x')],
    ['Veh', +2.5, -45, 0.0, wmath.Direction2D(mode = '+y')],
    ['Veh', +2.5, -15, 0.0, wmath.Direction2D(mode = '+y')],
    ['Veh', -2.5, +45, 0.0, wmath.Direction2D(mode = '-y')],
    ['Veh', -2.5, +15, 0.0, wmath.Direction2D(mode = '-y')],
)

# Get acceleration for aggressive driving
allowed_agents = list(range(8))
while True:
    canvas.clear()
    canvas.switch_to()
    canvas.dispatch_events()

    for aid, agent in enumerate(canvas.agents):
        if aid not in allowed_agents: continue
        control_inputs = agent.aggressive_driving()
        agent.step(control_inputs)

    drew_agents = canvas.on_draw()
    canvas.flip()

    # if drew_agents == 0: break