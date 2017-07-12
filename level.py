# -*- coding: utf-8 -*-

import os

import pygame
import gl
from rect import MyRect


class Level(object):
    # tile constants
    (TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE) = range(6)

    # tile width/height in px
    TILE_SIZE = 16

    def __init__(self, level_nr=None):
        """ There are total 35 different levels. If level_nr is larger than 35, loop over
        to next according level so, for example, if level_nr ir 37, then load level 2 """
        self._mapr = []

        # max number of enemies simultaneously  being on map
        self.max_active_enemies = 4

        tile_images = [
            pygame.Surface((8 * 2, 8 * 2)),
            gl.sprites.subsurface(48 * 2, 64 * 2, 8 * 2, 8 * 2),
            gl.sprites.subsurface(48 * 2, 72 * 2, 8 * 2, 8 * 2),
            gl.sprites.subsurface(56 * 2, 72 * 2, 8 * 2, 8 * 2),
            gl.sprites.subsurface(64 * 2, 64 * 2, 8 * 2, 8 * 2),
            gl.sprites.subsurface(64 * 2, 64 * 2, 8 * 2, 8 * 2),
            gl.sprites.subsurface(72 * 2, 64 * 2, 8 * 2, 8 * 2),
            gl.sprites.subsurface(64 * 2, 72 * 2, 8 * 2, 8 * 2)
        ]
        self.tile_empty = tile_images[0]
        self.tile_brick = tile_images[1]
        self.tile_steel = tile_images[2]
        self.tile_grass = tile_images[3]
        self.tile_water = tile_images[4]
        self.tile_water1 = tile_images[4]
        self.tile_water2 = tile_images[5]
        self.tile_froze = tile_images[6]

        self.obstacle_rects = []

        level_nr = 1 if level_nr is None else level_nr % 35
        if level_nr == 0:
            level_nr = 35

        self.load_level(level_nr)

        # tiles' rects on map, tanks cannot move over
        self.obstacle_rects = []

        # update these tiles
        self.update_obstacle_rects()

        gl.gtimer.add(400, lambda: self.toggle_waves())

    def hit_tile(self, pos, power=1, sound=False):
        """
        Hit the tile
        @param pos: Tile's x, y in px
        @param power:
        @param sound:
        @return True if bullet was stopped, False otherwise
        """

        for tile in self._mapr:
            if tile.topleft == pos:
                if tile.type == self.TILE_BRICK:
                    if gl.play_sounds and sound:
                        gl.sounds["brick"].play()
                    self._mapr.remove(tile)
                    self.update_obstacle_rects()
                    return True
                elif tile.type == self.TILE_STEEL:
                    if gl.play_sounds and sound:
                        gl.sounds["steel"].play()
                    if power == 2:
                        self._mapr.remove(tile)
                        self.update_obstacle_rects()
                    return True
                else:
                    return False

    def toggle_waves(self):
        """ Toggle water image """
        if self.tile_water == self.tile_water1:
            self.tile_water = self.tile_water2
        else:
            self.tile_water = self.tile_water1

    def load_level(self, level_nr=1):
        """ Load specified level
        @return boolean Whether level was loaded
        """
        filename = "levels/" + str(level_nr)
        if not os.path.isfile(filename):
            return False
        f = open(filename, "r")
        data = f.read().split("\n")
        self._mapr = []
        x, y = 0, 0
        for row in data:
            for ch in row:
                if ch == "#":
                    self._mapr.append(MyRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_BRICK))
                elif ch == "@":
                    self._mapr.append(MyRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_STEEL))
                elif ch == "~":
                    self._mapr.append(MyRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_WATER))
                elif ch == "%":
                    self._mapr.append(MyRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_GRASS))
                elif ch == "-":
                    self._mapr.append(MyRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_FROZE))
                x += self.TILE_SIZE
            x = 0
            y += self.TILE_SIZE
        return True

    def draw(self, tiles=None):
        """ Draw specified map on top of existing surface """

        if tiles is None:
            tiles = [self.TILE_BRICK, self.TILE_STEEL, self.TILE_WATER, self.TILE_GRASS, self.TILE_FROZE]

        for tile in self._mapr:
            if tile.type in tiles:
                if tile.type == self.TILE_BRICK:
                    gl.screen.blit(self.tile_brick, tile.topleft)
                elif tile.type == self.TILE_STEEL:
                    gl.screen.blit(self.tile_steel, tile.topleft)
                elif tile.type == self.TILE_WATER:
                    gl.screen.blit(self.tile_water, tile.topleft)
                elif tile.type == self.TILE_FROZE:
                    gl.screen.blit(self.tile_froze, tile.topleft)
                elif tile.type == self.TILE_GRASS:
                    gl.screen.blit(self.tile_grass, tile.topleft)

    def update_obstacle_rects(self):
        """ Set self.obstacle_rects to all tiles' rects that players can destroy
        with bullets """

        self.obstacle_rects = [gl.castle.rect]

        for tile in self._mapr:
            if tile.type in (self.TILE_BRICK, self.TILE_STEEL, self.TILE_WATER):
                self.obstacle_rects.append(tile)

    def build_fortress(self, tile):
        """ Build walls around castle made from tile """

        positions = [
            (11 * self.TILE_SIZE, 23 * self.TILE_SIZE),
            (11 * self.TILE_SIZE, 24 * self.TILE_SIZE),
            (11 * self.TILE_SIZE, 25 * self.TILE_SIZE),
            (14 * self.TILE_SIZE, 23 * self.TILE_SIZE),
            (14 * self.TILE_SIZE, 24 * self.TILE_SIZE),
            (14 * self.TILE_SIZE, 25 * self.TILE_SIZE),
            (12 * self.TILE_SIZE, 23 * self.TILE_SIZE),
            (13 * self.TILE_SIZE, 23 * self.TILE_SIZE)
        ]

        obsolete = []

        for i, rect in enumerate(self._mapr):
            if rect.topleft in positions:
                obsolete.append(rect)
        for rect in obsolete:
            self._mapr.remove(rect)

        for pos in positions:
            self._mapr.append(MyRect(pos[0], pos[1], self.TILE_SIZE, self.TILE_SIZE, tile))

        self.update_obstacle_rects()
