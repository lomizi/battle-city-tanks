# -*- coding: utf-8 -*-

import gl


class Explosion(object):
    def __init__(self, position, interval=None, images=None):

        self.position = [position[0] - 16, position[1] - 16]
        self.active = True

        if interval is None:
            interval = 100

        if images is None:
            images = [
                gl.sprites.subsurface(0, 80 * 2, 32 * 2, 32 * 2),
                gl.sprites.subsurface(32 * 2, 80 * 2, 32 * 2, 32 * 2),
                gl.sprites.subsurface(64 * 2, 80 * 2, 32 * 2, 32 * 2)
            ]

        images.reverse()

        self.images = [] + images

        self.image = self.images.pop()

        gl.gtimer.add(interval, lambda: self.update(), len(self.images) + 1)

    def draw(self):
        """ draw current explosion frame """
        gl.screen.blit(self.image, self.position)

    def update(self):
        """ Advance to the next image """
        if len(self.images) > 0:
            self.image = self.images.pop()
        else:
            self.active = False
