import pyglet
import graphics
import wm2
import wmath

canvas = graphics.Canvas(600, 600)
canvas.set_origin(300, 300)
canvas.set_scale(600 / 100) # 100m = 600pix
canvas.add_static_elements(
    ['Grass'],
    ['TwoLaneRoad', -50, -5, -5, +5, 0.5],
    ['StopRegion', -10, -5, -5, +5],
    ['TwoLaneRoad', +5, +50, -5, +5, 0.5],
    ['TwoLaneRoad', -5, +5, -50, -5, 0.5],
    ['TwoLaneRoad', -5, +5, +5, +50, 0.5],
    ['Intersection', -5, +5, -5, +5],
)
# canvas.show_allowed_regions()
canvas.add_agents(
    ['Ego', -45, -2.5, 0.0, wmath.Direction2D(mode = '+x')],
)
canvas.agents[0].which_regions()
canvas.render()