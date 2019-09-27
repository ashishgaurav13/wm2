import pyglet
import graphics

canvas = graphics.Canvas(600, 600)
canvas.items += [graphics.Image('static/vehicle.png', 0, 0, 100, 100)]
canvas.render()