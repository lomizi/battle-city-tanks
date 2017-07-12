#!/usr/bin/python
# coding=utf-8
# pylint: disable=missing-docstring

import gl
from castle import Castle
from game import Game
from timer import Timer

if __name__ == "__main__":
    gl.gtimer = Timer()
    gl.game = Game()
    gl.castle = Castle()
    gl.game.show_menu()
