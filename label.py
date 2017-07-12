# -*- coding: utf-8 -*-

import pygame

import gl


class Label(object):
    def __init__(self, position, text="", duration=None):
        self.position = position

        self.active = True

        self.text = text

        self.font = pygame.font.SysFont("Arial", 13)

        if duration is not None:
            gl.gtimer.add(duration, lambda: self.destroy(), 1)

    def draw(self):
        """ draw label """
        gl.screen.blit(self.font.render(self.text, False, (200, 200, 200)),
                       [self.position[0] + 4, self.position[1] + 8])

    def destroy(self):
        self.active = False
