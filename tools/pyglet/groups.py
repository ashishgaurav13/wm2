import pyglet
from pyglet import gl

# Collection of shapes, and possibly other collections
class Group:
    
    def __init__(self, items = []):
        self.items = items
    
    def draw(self):
        for item in self.items:
            item.draw()

# Collection with a single pyglet label
class Text(Group):

    def __init__(self, text, x, y, fontsize = 12, color = (0, 0, 0, 255),
        multiline = False, multiline_width = None):
        
        if multiline and multiline_width == None: multiline_width = 300
        label = pyglet.text.Label(text, font_size = fontsize, color = color,
            x = x, y = y, multiline = multiline, width = multiline_width)
        super().__init__(items = [label])

# Collection with a single image
class Image(Group):

    def __init__(self, url, x, y, w, h, rotation = 0, anchor_centered = False):
        assert(url[-3:] in ['png'])
        if url[-3:] == 'png': decoder = pyglet.image.codecs.png.PNGImageDecoder()
        image = pyglet.image.load(url, decoder = decoder)
        if anchor_centered: image.anchor_x, image.anchor_y = image.width//2, image.height//2
        scale_x, scale_y = w/image.width, h/image.height
        sprite = pyglet.sprite.Sprite(img = image)
        sprite.update(x = x, y = y, scale_x = scale_x, scale_y = scale_y,
            rotation = rotation)
        super().__init__(items = [sprite])

class InfiniteRepeatImage(Group):

    def __init__(self, url, canvas):
        assert(url[-3:] in ['png'])
        if url[-3:] == 'png': decoder = pyglet.image.codecs.png.PNGImageDecoder()
        image = pyglet.image.load(url, decoder = decoder)
        self.bg = pyglet.image.TileableTexture.create_for_image(image)
        self.h, self.w = canvas.width, canvas.height
        super().__init__(items = [self.bg])
    
    def draw(self):
        self.bg.blit_tiled(0, 0, 0, self.h, self.w)