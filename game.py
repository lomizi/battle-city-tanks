# -*- coding: utf-8 -*-

import os
import random
import sys

import pygame

import gl
from enemy import Enemy
from label import Label
from level import Level
from player import Player


class Game(object):
    # direction constants
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)

    TILE_SIZE = 16

    def __init__(self):
        self._game_over = False
        self._running = False
        self._stage = 1
        self.active = False
        self._level = None

        # center window
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'

        if gl.play_sounds:
            pygame.mixer.pre_init(44100, -16, 1, 512)

        pygame.init()

        pygame.display.set_caption("Battle City")

        size = width, height = 480, 416

        if "-f" in sys.argv[1:]:
            gl.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        else:
            gl.screen = pygame.display.set_mode(size)

        self.clock = pygame.time.Clock()

        # load sprites (funky version)
        # sprites = pygame.transform.scale2x(pygame.image.load("images/sprites.gif"))
        # load sprites (pixely version)
        gl.sprites = pygame.transform.scale(pygame.image.load("images/sprites.gif"), [192, 224])
        # screen.set_colorkey((0,138,104))

        pygame.display.set_icon(gl.sprites.subsurface(0, 0, 13 * 2, 13 * 2))

        # load sounds
        if gl.play_sounds:
            pygame.mixer.init(44100, -16, 1, 512)

            gl.sounds["start"] = pygame.mixer.Sound("sounds/gamestart.ogg")
            gl.sounds["end"] = pygame.mixer.Sound("sounds/gameover.ogg")
            gl.sounds["score"] = pygame.mixer.Sound("sounds/score.ogg")
            gl.sounds["bg"] = pygame.mixer.Sound("sounds/background.ogg")
            gl.sounds["fire"] = pygame.mixer.Sound("sounds/fire.ogg")
            gl.sounds["bonus"] = pygame.mixer.Sound("sounds/bonus.ogg")
            gl.sounds["explosion"] = pygame.mixer.Sound("sounds/explosion.ogg")
            gl.sounds["brick"] = pygame.mixer.Sound("sounds/brick.ogg")
            gl.sounds["steel"] = pygame.mixer.Sound("sounds/steel.ogg")

        self.enemy_life_image = gl.sprites.subsurface(81 * 2, 57 * 2, 7 * 2, 7 * 2)
        self.player_life_image = gl.sprites.subsurface(89 * 2, 56 * 2, 7 * 2, 8 * 2)
        self.flag_image = gl.sprites.subsurface(64 * 2, 49 * 2, 16 * 2, 15 * 2)

        # this is used in intro screen
        self.player_image = pygame.transform.rotate(gl.sprites.subsurface(0, 0, 13 * 2, 13 * 2), 270)

        # if true, no new enemies will be spawn during this time
        self.time_freeze = False

        # load custom font
        self.font = pygame.font.Font("fonts/prstart.ttf", 16)

        # pre-render game over text
        self.im_game_over = pygame.Surface((64, 40))
        self.im_game_over.set_colorkey((0, 0, 0))
        self.im_game_over.blit(self.font.render("GAME", False, (127, 64, 64)), [0, 0])
        self.im_game_over.blit(self.font.render("OVER", False, (127, 64, 64)), [0, 20])
        self.game_over_y = 416 + 40

        # number of players. here is defined preselected menu value
        self.nr_of_players = 1

        del gl.players[:]
        del gl.bullets[:]
        del gl.enemies[:]
        del gl.bonuses[:]

    def trigger_bonus(self, bonus, player):
        """ Execute bonus powers """

        if gl.play_sounds:
            gl.sounds["bonus"].play()

        player.trophies["bonus"] += 1
        player.score += 500

        if bonus.bonus == bonus.BONUS_GRENADE:
            for enemy in gl.enemies:
                enemy.explode()
        elif bonus.bonus == bonus.BONUS_HELMET:
            self.shield_player(player, True, 10000)
        elif bonus.bonus == bonus.BONUS_SHOVEL:
            self._level.build_fortress(self._level.TILE_STEEL)
            gl.gtimer.add(10000, lambda: self._level.build_fortress(self._level.TILE_BRICK), 1)
        elif bonus.bonus == bonus.BONUS_STAR:
            player.superpowers += 1
            if player.superpowers == 2:
                player.max_active_bullets = 2
        elif bonus.bonus == bonus.BONUS_TANK:
            player.lives += 1
        elif bonus.bonus == bonus.BONUS_TIMER:
            self.toggle_enemy_freeze(True)
            gl.gtimer.add(10000, lambda: self.toggle_enemy_freeze(False), 1)
        gl.bonuses.remove(bonus)

        gl.labels.append(Label(bonus.rect.topleft, "500", 500))

    def shield_player(self, player, shield=True, duration=None):
        """ Add/remove shield
        player: player (not enemy)
        shield: true/false
        duration: in ms. if none, do not remove shield automatically
        """
        player.shielded = shield
        if shield:
            player.timer_uuid_shield = gl.gtimer.add(100, lambda: player.toggle_shield_image())
        else:
            gl.gtimer.destroy(player.timer_uuid_shield)

        if shield and duration is not None:
            gl.gtimer.add(duration, lambda: self.shield_player(player, False), 1)

    def spawn_enemy(self):
        """ Spawn new enemy if needed
        Only add enemy if:
            - there are at least one in queue
            - map capacity hasn't exceeded its quota
            - now isn't time_freeze
        """

        if len(gl.enemies) >= self._level.max_active_enemies:
            return
        if len(self._level.enemies_left) < 1 or self.time_freeze:
            return
        enemy = Enemy(self._level, 1)

        gl.enemies.append(enemy)

    def respawn_player(self, player, clear_scores=False):
        """ Re spawn player """
        player.reset()

        if clear_scores:
            player.trophies = {
                "bonus": 0, "enemy0": 0, "enemy1": 0, "enemy2": 0, "enemy3": 0
            }

        self.shield_player(player, True, 4000)

    def game_over(self):
        """ End game and return to menu """

        print("Game Over")
        if gl.play_sounds:
            for sound in gl.sounds:
                gl.sounds[sound].stop()
                gl.sounds["end"].play()

        self.game_over_y = 416 + 40

        self._game_over = True
        gl.gtimer.add(3000, lambda: self.show_scores(), 1)

    def game_over_screen(self):
        """ Show game over screen """

        # stop game main loop (if any)
        self._running = False

        gl.screen.fill([0, 0, 0])

        self.write_in_bricks("game", [125, 140])
        self.write_in_bricks("over", [125, 220])
        pygame.display.flip()

        while 1:
            self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.show_menu()
                        return

    def show_menu(self):
        """ Show game menu
        Redraw screen only when up or down key is pressed. When enter is pressed,
        exit from this screen and start the game with selected number of players
        """

        # stop game main loop (if any)
        self._running = False

        # clear all timers
        del gl.gtimer.timers[:]

        # set current stage to 0
        self._stage = 1

        self.animate_intro_screen()

        main_loop = True
        while main_loop:
            self.clock.tick(50)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        quit()
                    elif event.key == pygame.K_UP:
                        if self.nr_of_players == 2:
                            self.nr_of_players = 1
                            self.draw_intro_screen()
                    elif event.key == pygame.K_DOWN:
                        if self.nr_of_players == 1:
                            self.nr_of_players = 2
                            self.draw_intro_screen()
                    elif event.key == pygame.K_RETURN:
                        main_loop = False

        del gl.players[:]
        self.next_level()

    def reload_players(self):
        """ Init players
        If players already exist, just reset them
        """

        if len(gl.players) == 0:
            # first player
            x = 8 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
            y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2

            player = Player(
                self._level, 0, [x, y], self.DIR_UP, (0, 0, 13 * 2, 13 * 2)
            )
            gl.players.append(player)

            # second player
            if self.nr_of_players == 2:
                x = 16 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                player = Player(
                    self._level, 0, [x, y], self.DIR_UP, (16 * 2, 0, 13 * 2, 13 * 2)
                )
                player.controls = [102, 119, 100, 115, 97]
                gl.players.append(player)

        for player in gl.players:
            player._level = self._level
            self.respawn_player(player, True)

    def show_scores(self):
        """ Show level scores """

        # stop game main loop (if any)
        self._running = False

        # clear all timers
        del gl.gtimer.timers[:]

        if gl.play_sounds:
            for sound in gl.sounds:
                gl.sounds[sound].stop()

        hiscore = self.load_hi_score()

        # update hiscore if needed
        if gl.players[0].score > hiscore:
            hiscore = gl.players[0].score
            self.save_hi_score(hiscore)
        if self.nr_of_players == 2 and gl.players[1].score > hiscore:
            hiscore = gl.players[1].score
            self.save_hi_score(hiscore)

        img_tanks = [
            gl.sprites.subsurface(32 * 2, 0, 13 * 2, 15 * 2),
            gl.sprites.subsurface(48 * 2, 0, 13 * 2, 15 * 2),
            gl.sprites.subsurface(64 * 2, 0, 13 * 2, 15 * 2),
            gl.sprites.subsurface(80 * 2, 0, 13 * 2, 15 * 2)
        ]

        img_arrows = [
            gl.sprites.subsurface(81 * 2, 48 * 2, 7 * 2, 7 * 2),
            gl.sprites.subsurface(88 * 2, 48 * 2, 7 * 2, 7 * 2)
        ]

        gl.screen.fill([0, 0, 0])

        # colors
        black = pygame.Color("black")
        white = pygame.Color("white")
        purple = pygame.Color(127, 64, 64)
        pink = pygame.Color(191, 160, 128)

        gl.screen.blit(self.font.render("HI-SCORE", False, purple), [105, 35])
        gl.screen.blit(self.font.render(str(hiscore), False, pink), [295, 35])

        gl.screen.blit(self.font.render("STAGE" + str(self._stage).rjust(3), False, white), [170, 65])

        gl.screen.blit(self.font.render("I-PLAYER", False, purple), [25, 95])

        # player 1 global score
        gl.screen.blit(self.font.render(str(gl.players[0].score).rjust(8), False, pink), [25, 125])

        if self.nr_of_players == 2:
            gl.screen.blit(self.font.render("II-PLAYER", False, purple), [310, 95])

            # player 2 global score
            gl.screen.blit(self.font.render(str(gl.players[1].score).rjust(8), False, pink), [325, 125])

        # tanks and arrows
        for i in range(4):
            gl.screen.blit(img_tanks[i], [226, 160 + (i * 45)])
            gl.screen.blit(img_arrows[0], [206, 168 + (i * 45)])
            if self.nr_of_players == 2:
                gl.screen.blit(img_arrows[1], [258, 168 + (i * 45)])

        gl.screen.blit(self.font.render("TOTAL", False, white), [70, 335])

        # total underline
        pygame.draw.line(gl.screen, white, [170, 330], [307, 330], 4)

        pygame.display.flip()

        self.clock.tick(2)

        interval = 5

        # points and kills
        for i in range(4):

            # total specific tanks
            tanks = gl.players[0].trophies["enemy" + str(i)]

            for n in range(tanks + 1):
                if n > 0 and gl.play_sounds:
                    gl.sounds["score"].play()

                # erase previous text
                gl.screen.blit(self.font.render(str(n - 1).rjust(2), False, black), [170, 168 + (i * 45)])
                # print new number of enemies
                gl.screen.blit(self.font.render(str(n).rjust(2), False, white), [170, 168 + (i * 45)])
                # erase previous text
                gl.screen.blit(self.font.render(str((n - 1) * (i + 1) * 100).rjust(4) + " PTS", False, black),
                               [25, 168 + (i * 45)])
                # print new total points per enemy
                gl.screen.blit(self.font.render(str(n * (i + 1) * 100).rjust(4) + " PTS", False, white),
                               [25, 168 + (i * 45)])
                pygame.display.flip()
                self.clock.tick(interval)

            if self.nr_of_players == 2:
                tanks = gl.players[1].trophies["enemy" + str(i)]

                for n in range(tanks + 1):

                    if n > 0 and gl.play_sounds:
                        gl.sounds["score"].play()

                    gl.screen.blit(self.font.render(str(n - 1).rjust(2), False, black), [277, 168 + (i * 45)])
                    gl.screen.blit(self.font.render(str(n).rjust(2), False, white), [277, 168 + (i * 45)])

                    gl.screen.blit(self.font.render(str((n - 1) * (i + 1) * 100).rjust(4) + " PTS", False, black),
                                   [325, 168 + (i * 45)])
                    gl.screen.blit(self.font.render(str(n * (i + 1) * 100).rjust(4) + " PTS", False, white),
                                   [325, 168 + (i * 45)])

                    pygame.display.flip()
                    self.clock.tick(interval)

            self.clock.tick(interval)

        # total tanks
        tanks = sum([i for i in gl.players[0].trophies.values()]) - gl.players[0].trophies["bonus"]
        gl.screen.blit(self.font.render(str(tanks).rjust(2), False, white), [170, 335])
        if self.nr_of_players == 2:
            tanks = sum([i for i in gl.players[1].trophies.values()]) - gl.players[1].trophies["bonus"]
            gl.screen.blit(self.font.render(str(tanks).rjust(2), False, white), [277, 335])

        pygame.display.flip()

        # do nothing for 2 seconds
        self.clock.tick(1)
        self.clock.tick(1)

        if self._game_over:
            self.game_over_screen()
        else:
            self.next_level()

    def draw(self):
        gl.screen.fill([0, 0, 0])

        self._level.draw([self._level.TILE_EMPTY, self._level.TILE_BRICK, self._level.TILE_STEEL,
                          self._level.TILE_FROZE, self._level.TILE_WATER])

        gl.castle.draw()

        for enemy in gl.enemies:
            enemy.draw()

        for label in gl.labels:
            label.draw()

        for player in gl.players:
            player.draw()

        for bullet in gl.bullets:
            bullet.draw()

        for bonus in gl.bonuses:
            bonus.draw()

        self._level.draw([self._level.TILE_GRASS])

        if self._game_over:
            if self.game_over_y > 188:
                self.game_over_y -= 4
            gl.screen.blit(self.im_game_over, [176, self.game_over_y])  # 176=(416-64)/2

        self.draw_sidebar()

        pygame.display.flip()

    def draw_sidebar(self):
        x = 416
        y = 0
        gl.screen.fill([100, 100, 100], pygame.Rect([416, 0], [64, 416]))

        xpos = x + 16
        ypos = y + 16

        # draw enemy lives
        for n in range(len(self._level.enemies_left) + len(gl.enemies)):
            gl.screen.blit(self.enemy_life_image, [xpos, ypos])
            if n % 2 == 1:
                xpos = x + 16
                ypos += 17
            else:
                xpos += 17

        # players' lives
        if pygame.font.get_init():
            text_color = pygame.Color('black')
            for n in range(len(gl.players)):
                if n == 0:
                    gl.screen.blit(self.font.render(str(n + 1) + "P", False, text_color), [x + 16, y + 200])
                    gl.screen.blit(self.font.render(str(gl.players[n].lives), False, text_color), [x + 31, y + 215])
                    gl.screen.blit(self.player_life_image, [x + 17, y + 215])
                else:
                    gl.screen.blit(self.font.render(str(n + 1) + "P", False, text_color), [x + 16, y + 240])
                    gl.screen.blit(self.font.render(str(gl.players[n].lives), False, text_color), [x + 31, y + 255])
                    gl.screen.blit(self.player_life_image, [x + 17, y + 255])

            gl.screen.blit(self.flag_image, [x + 17, y + 280])
            gl.screen.blit(self.font.render(str(self._stage), False, text_color), [x + 17, y + 312])

    def draw_intro_screen(self, put_on_surface=True):
        """ Draw intro (menu) screen
        @param boolean put_on_surface: If True, flip display after drawing
        @return None
        """

        gl.screen.fill([0, 0, 0])

        if pygame.font.get_init():
            hiscore = self.load_hi_score()

            gl.screen.blit(self.font.render("HI- " + str(hiscore), True, pygame.Color('white')), [170, 35])

            gl.screen.blit(self.font.render("1 PLAYER", True, pygame.Color('white')), [165, 250])
            gl.screen.blit(self.font.render("2 PLAYERS", True, pygame.Color('white')), [165, 275])

            gl.screen.blit(self.font.render("©1980-1985 NAMCO LTD.", True, pygame.Color('white')), [50, 350])
            gl.screen.blit(self.font.render("ALL RIGHTS RESERVED", True, pygame.Color('white')), [85, 380])

        if self.nr_of_players == 1:
            gl.screen.blit(self.player_image, [125, 245])
        elif self.nr_of_players == 2:
            gl.screen.blit(self.player_image, [125, 270])

        self.write_in_bricks("battle", [65, 80])
        self.write_in_bricks("city", [129, 160])

        if put_on_surface:
            pygame.display.flip()

    def animate_intro_screen(self):
        """ Slide intro (menu) screen from bottom to top
        If Enter key is pressed, finish animation immediately
        @return None
        """

        self.draw_intro_screen(False)
        screen_cp = gl.screen.copy()

        gl.screen.fill([0, 0, 0])

        y = 416
        while y > 0:
            self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        y = 0
                        break

            gl.screen.blit(screen_cp, [0, y])
            pygame.display.flip()
            y -= 5

        gl.screen.blit(screen_cp, [0, 0])
        pygame.display.flip()

    def chunks(self, l, n):
        """ Split text string in chunks of specified size
        @param string l: Input string
        @param int n: Size (number of characters) of each chunk
        @return list
        """
        return [l[i:i + n] for i in range(0, len(l), n)]

    def write_in_bricks(self, text, pos):
        """ Write specified text in "brick font"
        Only those letters are available that form words "Battle City" and "Game Over"
        Both lowercase and uppercase are valid input, but output is always uppercase
        Each letter consists of 7x7 bricks which is converted into 49 character long string
        of 1's and 0's which in turn is then converted into hex to save some bytes
        @return None
        """

        bricks = gl.sprites.subsurface(56 * 2, 64 * 2, 8 * 2, 8 * 2)
        brick1 = bricks.subsurface((0, 0, 8, 8))
        brick2 = bricks.subsurface((8, 0, 8, 8))
        brick3 = bricks.subsurface((8, 8, 8, 8))
        brick4 = bricks.subsurface((0, 8, 8, 8))

        alphabet = {
            "a": "0071b63c7ff1e3",
            "b": "01fb1e3fd8f1fe",
            "c": "00799e0c18199e",
            "e": "01fb060f98307e",
            "g": "007d860cf8d99f",
            "i": "01f8c183060c7e",
            "l": "0183060c18307e",
            "m": "018fbffffaf1e3",
            "o": "00fb1e3c78f1be",
            "r": "01fb1e3cff3767",
            "t": "01f8c183060c18",
            "v": "018f1e3eef8e08",
            "y": "019b3667860c18"
        }

        abs_x, abs_y = pos

        for letter in text.lower():

            binstr = ""
            for h in self.chunks(alphabet[letter], 2):
                binstr += str(bin(int(h, 16)))[2:].rjust(8, "0")
            binstr = binstr[7:]

            x, y = 0, 0
            letter_w = 0
            surf_letter = pygame.Surface((56, 56))
            for j, row in enumerate(self.chunks(binstr, 7)):
                for i, bit in enumerate(row):
                    if bit == "1":
                        if i % 2 == 0 and j % 2 == 0:
                            surf_letter.blit(brick1, [x, y])
                        elif i % 2 == 1 and j % 2 == 0:
                            surf_letter.blit(brick2, [x, y])
                        elif i % 2 == 1 and j % 2 == 1:
                            surf_letter.blit(brick3, [x, y])
                        elif i % 2 == 0 and j % 2 == 1:
                            surf_letter.blit(brick4, [x, y])
                        if x > letter_w:
                            letter_w = x
                    x += 8
                x = 0
                y += 8
            gl.screen.blit(surf_letter, [abs_x, abs_y])
            abs_x += letter_w + 16

    def toggle_enemy_freeze(self, freeze=True):
        """ Freeze/defreeze all enemies """

        for enemy in gl.enemies:
            enemy.paused = freeze
        self.time_freeze = freeze

    def load_hi_score(self):
        """ Load hiscore
        Really primitive version =] If for some reason hiscore cannot be loaded, return 20000
        @return int
        """
        filename = ".hiscore"
        if not os.path.isfile(filename):
            return 20000

        f = open(filename, "r")
        hiscore = int(f.read())

        if 19999 < hiscore < 1000000:
            return hiscore
        else:
            print("cheater =[")
            return 20000

    def save_hi_score(self, hiscore):
        """ Save hiscore
        @return boolean
        """
        try:
            f = open(".hiscore", "w")
        except:
            print("Can't save hi-score")
            return False
        f.write(str(hiscore))
        f.close()
        return True

    def finish_level(self):
        """ Finish current level
        Show earned scores and advance to the next stage
        """

        if gl.play_sounds:
            gl.sounds["bg"].stop()

        self.active = False
        gl.gtimer.add(3000, lambda: self.show_scores(), 1)

        print("Stage " + str(self._stage) + " completed")

    def next_level(self):
        """ Start next level """

        del gl.bullets[:]
        del gl.enemies[:]
        del gl.bonuses[:]
        gl.castle.rebuild()
        del gl.gtimer.timers[:]

        # load level
        self._stage += 1
        self._level = Level(self._stage)
        self.time_freeze = False

        # set number of enemies by types (basic, fast, power, armor) according to level
        levels_enemies = (
            (18, 2, 0, 0), (14, 4, 0, 2), (14, 4, 0, 2), (2, 5, 10, 3), (8, 5, 5, 2),
            (9, 2, 7, 2), (7, 4, 6, 3), (7, 4, 7, 2), (6, 4, 7, 3), (12, 2, 4, 2),
            (5, 5, 4, 6), (0, 6, 8, 6), (0, 8, 8, 4), (0, 4, 10, 6), (0, 2, 10, 8),
            (16, 2, 0, 2), (8, 2, 8, 2), (2, 8, 6, 4), (4, 4, 4, 8), (2, 8, 2, 8),
            (6, 2, 8, 4), (6, 8, 2, 4), (0, 10, 4, 6), (10, 4, 4, 2), (0, 8, 2, 10),
            (4, 6, 4, 6), (2, 8, 2, 8), (15, 2, 2, 1), (0, 4, 10, 6), (4, 8, 4, 4),
            (3, 8, 3, 6), (6, 4, 2, 8), (4, 4, 4, 8), (0, 10, 4, 6), (0, 6, 4, 10)
        )

        if self._stage <= 35:
            enemies_l = levels_enemies[self._stage - 1]
        else:
            enemies_l = levels_enemies[34]

        self._level.enemies_left = [0] * enemies_l[0] + [1] * enemies_l[1] + [2] * enemies_l[2] + [3] * enemies_l[3]
        random.shuffle(self._level.enemies_left)

        if gl.play_sounds:
            gl.sounds["start"].play()
            gl.gtimer.add(4330, lambda: gl.sounds["bg"].play(-1), 1)

        self.reload_players()

        gl.gtimer.add(3000, lambda: self.spawn_enemy())

        # if True, start "game over" animation
        self._game_over = False

        # if False, game will end w/o "game over" bussiness
        self._running = True

        # if False, players won't be able to do anything
        self.active = True

        self.draw()

        while self._running:

            time_passed = self.clock.tick(50)

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                elif event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN and not self._game_over and self.active:

                    if event.key == pygame.K_q:
                        quit()
                    # toggle sounds
                    elif event.key == pygame.K_m:
                        play_sounds = not gl.play_sounds
                        if not play_sounds:
                            pygame.mixer.stop()
                        else:
                            gl.sounds["bg"].play(-1)

                    for player in gl.players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 0:
                                    if player.fire() and gl.play_sounds:
                                        gl.sounds["fire"].play()
                                elif index == 1:
                                    player.pressed[0] = True
                                elif index == 2:
                                    player.pressed[1] = True
                                elif index == 3:
                                    player.pressed[2] = True
                                elif index == 4:
                                    player.pressed[3] = True
                elif event.type == pygame.KEYUP and not self._game_over and self.active:
                    for player in gl.players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 1:
                                    player.pressed[0] = False
                                elif index == 2:
                                    player.pressed[1] = False
                                elif index == 3:
                                    player.pressed[2] = False
                                elif index == 4:
                                    player.pressed[3] = False

            for player in gl.players:
                if player.state == player.STATE_ALIVE and not self._game_over and self.active:
                    if player.pressed[0]:
                        player.move(self.DIR_UP)
                    elif player.pressed[1]:
                        player.move(self.DIR_RIGHT)
                    elif player.pressed[2]:
                        player.move(self.DIR_DOWN)
                    elif player.pressed[3]:
                        player.move(self.DIR_LEFT)
                player.update(time_passed)

            for enemy in gl.enemies:
                if enemy.state == enemy.STATE_DEAD and not self._game_over and self.active:
                    gl.enemies.remove(enemy)
                    if len(self._level.enemies_left) == 0 and len(gl.enemies) == 0:
                        self.finish_level()
                else:
                    enemy.update(time_passed)

            if not self._game_over and self.active:
                for player in gl.players:
                    if player.state == player.STATE_ALIVE:
                        if player.bonus is not None and player.side == player.SIDE_PLAYER:
                            self.trigger_bonus(bonus, player)
                            player.bonus = None
                    elif player.state == player.STATE_DEAD:
                        self.superpowers = 0
                        player.lives -= 1
                        if player.lives > 0:
                            self.respawn_player(player)
                        else:
                            self.game_over()

            for bullet in gl.bullets:
                if bullet.state == bullet.STATE_REMOVED:
                    gl.bullets.remove(bullet)
                else:
                    bullet.update()

            for bonus in gl.bonuses:
                if bonus.active is False:
                    gl.bonuses.remove(bonus)

            for label in gl.labels:
                if not label.active:
                    gl.labels.remove(label)

            if not self._game_over:
                if not gl.castle.active:
                    self.game_over()

            gl.gtimer.update(time_passed)

            self.draw()
