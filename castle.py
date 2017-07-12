# -*- coding: utf-8 -*-

import pygame

import gl
from explosion import Explosion


class Castle(object):
    """ Player's castle/fortress """

    (STATE_STANDING, STATE_DESTROYED, STATE_EXPLODING) = range(3)

    def __init__(self):
        self.state = None
        self.image = None
        self.active = False
        self.explosion = None

        # images
        self.img_undamaged = gl.sprites.subsurface(0, 15 * 2, 16 * 2, 16 * 2)
        self.img_destroyed = gl.sprites.subsurface(16 * 2, 15 * 2, 16 * 2, 16 * 2)

        # init position
        self.rect = pygame.Rect(12 * 16, 24 * 16, 32, 32)

        # start w/ undamaged and shiny castle
        self.rebuild()

    def draw(self):
        """ Draw castle """

        gl.screen.blit(self.image, self.rect.topleft)

        if self.state == self.STATE_EXPLODING:
            if not self.explosion.active:
                self.state = self.STATE_DESTROYED
                del self.explosion
            else:
                self.explosion.draw()

    def rebuild(self):
        """ Reset castle """
        self.state = self.STATE_STANDING
        self.image = self.img_undamaged
        self.active = True

    def destroy(self):
        """ Destroy castle """
        self.state = self.STATE_EXPLODING
        self.explosion = Explosion(self.rect.topleft)
        self.image = self.img_destroyed
        self.active = False
