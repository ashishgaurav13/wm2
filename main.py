import pyglet
import graphics
import wm2

canvas = graphics.Canvas(600, 600)
canvas.set_origin(300, 300)
canvas.set_scale(600 / 100) # 100m = 600pix
canvas.add_static_elements(
    ['Grass'],
    ['TwoLaneRoad', -50, -5, -5, +5, 0.5],
    ['TwoLaneRoad', +5, +50, -5, +5, 0.5],
    ['TwoLaneRoad', -5, +5, -50, -5, 0.5],
    ['TwoLaneRoad', -5, +5, +5, +50, 0.5],
    ['Intersection', -5, +5, -5, +5],
)
canvas.show_allowed_regions()
canvas.render()