# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring

import pygame


class MyRect(pygame.Rect):
    """ Add type property """

    def __init__(self, left, top, width, height, typo):
        pygame.Rect.__init__(self, left, top, width, height)
        self.type = typo
