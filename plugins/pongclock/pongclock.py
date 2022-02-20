"""
PongClock
(c) Steven Babineau - babineau@gmail.com
2022
"""
import datetime
import os
import random
import pygame

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton
from .paddle import Paddle
from .ball import Ball
from .scoredigit import ScoreDigit
from .scanlines import Scanlines


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
class PongClock(FullScreenPlugin, metaclass=Singleton):
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.helper_vars = {"red": (255, 0, 0), "green": (0, 255, 0), "right": "RIGHT", "left": "LEFT"}

        self.canvas_with_divider = self.canvas.copy()
        self.background = eval(self.plugin_config["background"])
        self.foreground = eval(self.plugin_config["foreground"])
        self.sprites = None
        self.old_minutes = 0
        self.old_hours = 0
        self.scanlines = None
        self.divider_x = None
        self.game_ball = None
        self.left_paddle = None
        self.right_paddle = None
        self.hours1 = None
        self.hours2 = None
        self.mins1 = None
        self.mins2 = None

        self.setup_board()

    def setup_board(self):
        self.canvas_with_divider.fill(self.background)

        # Create the center divider on the second surface
        self.divider_x = (self.canvas_with_divider.get_width() / 2) - (self.plugin_config.getint("center_divider_block_width") / 2)
        for i in range(self.plugin_config.getint("screen_margin"),
                       self.canvas_with_divider.get_height() - (self.plugin_config.getint("screen_margin") * 2),
                       self.plugin_config.getint("center_divider_block_height") + self.plugin_config.getint("center_divider_block_spacing")):

            center_dot = pygame.Rect(self.divider_x, i, self.plugin_config.getint("center_divider_block_width"),
                                     self.plugin_config.getint("center_divider_block_height"))
            self.canvas_with_divider.fill(self.foreground, center_dot)

        self.sprites = pygame.sprite.OrderedUpdates()

        (random_velocity_x, random_velocity_y) = get_random_velocity(self.plugin_config.getint("min_horizontal_velocity"),
                                                                     self.plugin_config.getint("min_vertical_velocity"),
                                                                     self.plugin_config.getint("max_horizontal_velocity"),
                                                                     self.plugin_config.getint("max_vertical_velocity"))
        self.helper.log(self.debug, "Velocity X,Y={},{}".format(random_velocity_x, random_velocity_y))

        self.game_ball = Ball(self.debug, self.plugin_config, self.helper, (random_velocity_x, random_velocity_y), self.canvas.get_width(), self.canvas.get_height())

        self.left_paddle = Paddle(self.debug, self.plugin_config, self.helper, self.helper.LEFT, self.game_ball,
                                  self.canvas.get_width(), self.canvas.get_height())
        self.right_paddle = Paddle(self.debug, self.plugin_config, self.helper, self.helper.RIGHT, self.game_ball,
                                   self.canvas.get_width(), self.canvas.get_height())

        now = datetime.datetime.now()
        fixed_hours = now.hour
        if self.plugin_config.getint("hour_type") == 12 and fixed_hours > 12:
            fixed_hours -= 12

        hours = str(fixed_hours).zfill(2)
        minutes = str(now.minute).zfill(2)
        swidth = self.canvas.get_width()
        dspacing = self.plugin_config.getint("digit_spacing")
        dwidth = self.plugin_config.getint("digit_width")
        margin = self.plugin_config.getint("screen_margin")
        self.hours1 = ScoreDigit(self.debug, self.plugin_config, self.helper, swidth / 2 - dspacing * 2 - dwidth * 2, margin, hours[0])
        self.hours2 = ScoreDigit(self.debug, self.plugin_config, self.helper, swidth / 2 - dspacing - dwidth,         margin, hours[1])
        self.mins1 = ScoreDigit(self.debug, self.plugin_config, self.helper,  swidth / 2 + dspacing,                  margin, minutes[0])
        self.mins2 = ScoreDigit(self.debug, self.plugin_config, self.helper,  swidth / 2 + dspacing * 2 + dwidth,     margin, minutes[1])

        self.sprites.add(self.game_ball)

        self.sprites.add(self.left_paddle)
        self.sprites.add(self.right_paddle)

        self.sprites.add(self.hours1)
        self.sprites.add(self.hours2)
        self.sprites.add(self.mins1)
        self.sprites.add(self.mins2)

        self.scanlines = None
        if self.plugin_config.getboolean("show_scanlines"):
            self.scanlines = Scanlines(self.debug, self.plugin_config, 0, 0, self.canvas.get_width(), self.canvas.get_height())
            self.sprites.add(self.scanlines)

        self.old_minutes = now.minute
        self.old_hours = now.hour

        pygame.display.flip()

    def update(self, tick, fps):
        if self.just_in:
            self.setup_board()

        if tick == 1:
            now = datetime.datetime.now()
            if now.hour != self.old_hours:
                self.old_hours = now.hour
                self.old_minutes = now.minute
                self.game_ball.lose_side = self.helper.RIGHT
                self.helper.log(self.debug, "time to score HOURS!")
            elif now.minute != self.old_minutes:
                self.old_minutes = now.minute
                self.game_ball.lose_side = self.helper.LEFT
                self.helper.log(self.debug, "time to score MINUTES!")

        self.canvas.blit(self.canvas_with_divider, (0, 0))

        self.sprites.update(self.canvas)

        dirty_rects = self.sprites.draw(self.canvas)

        pygame.display.update(dirty_rects)

        if self.game_ball.bounced:
            # this will be opposite since it just bounced
            if self.game_ball.direction == self.helper.RIGHT:
                self.left_paddle.hit()
            else:
                self.right_paddle.hit()

        if self.debug:
            if self.game_ball.direction == self.helper.RIGHT:
                pygame.draw.rect(self.canvas, self.helper.RED,
                                 pygame.Rect(self.canvas.get_width() - 30, self.game_ball.hity, 30,
                                             2))
            else:
                pygame.draw.rect(self.canvas, self.helper.RED,
                                 pygame.Rect(0, self.game_ball.hity, 30, 2))

        if self.game_ball.just_lost:
            self.helper.log(self.debug, "ball just lost... resetting.")

            now = datetime.datetime.now()
            hours = str(now.hour).zfill(2)
            minutes = str(now.minute).zfill(2)

            self.hours1.draw_segments(hours[0])
            self.hours2.draw_segments(hours[1])

            self.mins1.draw_segments(minutes[0])
            self.mins2.draw_segments(minutes[1])

            (random_velocity_x, random_velocity_y) = get_random_velocity(self.plugin_config.getint("min_horizontal_velocity"),
                                                                         self.plugin_config.getint("min_vertical_velocity"),
                                                                         self.plugin_config.getint("max_horizontal_velocity"),
                                                                         self.plugin_config.getint("max_vertical_velocity"))

            self.helper.log(self.debug, "Velocity X,Y={},{}".format(random_velocity_x, random_velocity_y))
            self.game_ball.reset((random_velocity_x, random_velocity_y))
            self.left_paddle.reset()
            self.right_paddle.reset()


def get_random_velocity(min_h, min_v, max_h, max_v):
    random_velocity_x = 0
    while abs(random_velocity_x) <= min_h:
        random_velocity_x = random.randint(0, max_h * 2) - max_h

    random_velocity_y = 0
    while abs(random_velocity_y) <= min_v:
        random_velocity_y = random.randint(0, max_v * 2) - max_v

    return random_velocity_x, random_velocity_y
