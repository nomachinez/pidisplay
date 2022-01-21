"""
PongClock
(c) Steven Babineau - babineau@gmail.com
2022
"""
import datetime
import random
import pygame
from .paddle import Paddle
from .ball import Ball
from .scoredigit import ScoreDigit
from .scanlines import Scanlines


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
class PongClock:
    def __init__(self, config, helper, canvas):
        self.helper = helper
        self.config = config
        self.canvas = canvas

        self.helper_vars = {"red": (255, 0, 0), "green": (0, 255, 0), "right": "RIGHT", "left": "LEFT"}
        self.config = self.helper.merge_configs(self.config, self.helper_vars)
        # self.canvases = [None, None]

        self.canvas.fill(self.config["background"])
        self.canvas_with_divider = self.canvas.copy()

        # pylint: disable=consider-using-enumerate
        # for i in range(len(self.canvases)):
        #     self.canvases[i] = pygame.display.get_surface()
        #     self.canvases[i].fill(self.config["background"])

        # Create the center divider on the second surface
        self.divider_x = (self.canvas_with_divider.get_width() / 2) - (self.config["center_divider_block_width"] / 2)
        for i in range(self.config["screen_margin"],
                       self.canvas_with_divider.get_height() - (self.config["screen_margin"] * 2),
                       self.config["center_divider_block_height"] + self.config["center_divider_block_spacing"]):

            center_dot = pygame.Rect(self.divider_x, i, self.config["center_divider_block_width"],
                                     self.config["center_divider_block_height"])
            self.canvas_with_divider.fill(self.config["foreground"], center_dot)

        self.sprites = pygame.sprite.OrderedUpdates()

        (random_velocity_x, random_velocity_y) = get_random_velocity(self.config["min_horizontal_velocity"],
                                                                     self.config["min_vertical_velocity"],
                                                                     self.config["max_horizontal_velocity"],
                                                                     self.config["max_vertical_velocity"])

        self.game_ball = Ball(self.config, self.helper, (random_velocity_x, random_velocity_y),
                              self.canvas.get_width(), self.canvas.get_height())

        self.left_paddle = Paddle(self.config, self.helper, self.config["left"], self.game_ball,
                                  self.canvas.get_width(), self.canvas.get_height())
        self.right_paddle = Paddle(self.config, self.helper, self.config["right"], self.game_ball,
                                   self.canvas.get_width(), self.canvas.get_height())

        now = datetime.datetime.now()
        fixed_hours = now.hour
        if self.config["hour_type"] == 12 and fixed_hours > 12:
            fixed_hours -= 12

        hours = str(fixed_hours).zfill(2)
        minutes = str(now.minute).zfill(2)
        swidth = self.canvas.get_width()
        dspacing = self.config["digit_spacing"]
        dwidth = self.config["digit_width"]
        margin = self.config["screen_margin"]
        self.hours1 = ScoreDigit(self.config, self.helper, swidth / 2 - dspacing * 2 - dwidth * 2, margin, hours[0])
        self.hours2 = ScoreDigit(self.config, self.helper, swidth / 2 - dspacing - dwidth,         margin, hours[1])
        self.mins1 = ScoreDigit(self.config, self.helper,  swidth / 2 + dspacing,                  margin, minutes[0])
        self.mins2 = ScoreDigit(self.config, self.helper,  swidth / 2 + dspacing * 2 + dwidth,     margin, minutes[1])

        self.sprites.add(self.game_ball)

        self.sprites.add(self.left_paddle)
        self.sprites.add(self.right_paddle)

        self.sprites.add(self.hours1)
        self.sprites.add(self.hours2)
        self.sprites.add(self.mins1)
        self.sprites.add(self.mins2)

        self.scanlines = None
        if self.config["show_scanlines"]:
            self.scanlines = Scanlines(self.config, 0, 0, self.canvas.get_width(), self.canvas.get_height())
            self.sprites.add(self.scanlines)

        self.old_minutes = now.minute
        self.old_hours = now.hour

        pygame.display.flip()

    def update(self, tick, canvas):
        if self.config["frames_per_second"] / 2 == tick:
            now = datetime.datetime.now()
            if now.hour != self.old_hours:
                self.old_hours = now.hour
                self.old_minutes = now.minute
                self.game_ball.lose_side = self.config["right"]
                self.helper.log(self.config, "time to score HOURS!")
            elif now.minute != self.old_minutes:
                self.old_minutes = now.minute
                self.game_ball.lose_side = self.config["left"]
                self.helper.log(self.config, "time to score MINUTES!")

        canvas.blit(self.canvas_with_divider, (0, 0))

        self.sprites.update(canvas)

        dirty_rects = self.sprites.draw(canvas)

        pygame.display.update(dirty_rects)

        if self.game_ball.bounced:
            # this will be opposite since it just bounced
            if self.game_ball.direction == self.config["right"]:
                self.left_paddle.hit()
            else:
                self.right_paddle.hit()

        if self.config["debug"]:
            if self.game_ball.direction == self.config["right"]:
                pygame.draw.rect(canvas, self.config["red"],
                                 pygame.Rect(self.canvas.get_width() - 30, self.game_ball.hity, 30,
                                             self.config["screen_margin"]))
            else:
                pygame.draw.rect(canvas, self.config["red"],
                                 pygame.Rect(0, self.game_ball.hity, 30, self.config["screen_margin"]))

        if self.game_ball.just_lost:
            self.helper.log(self.config, "ball just lost... resetting.")

            now = datetime.datetime.now()
            hours = str(now.hour).zfill(2)
            minutes = str(now.minute).zfill(2)

            self.hours1.draw_segments(hours[0])
            self.hours2.draw_segments(hours[1])

            self.mins1.draw_segments(minutes[0])
            self.mins2.draw_segments(minutes[1])

            (random_velocity_x, random_velocity_y) = get_random_velocity(self.config["min_horizontal_velocity"],
                                                                         self.config["min_vertical_velocity"],
                                                                         self.config["max_horizontal_velocity"],
                                                                         self.config["max_vertical_velocity"])

            self.game_ball.reset((random_velocity_x, random_velocity_y))
            self.left_paddle.reset()
            self.right_paddle.reset()

        return canvas


def get_random_velocity(min_h, min_v, max_h, max_v):
    random_velocity_x = 0
    while abs(random_velocity_x) <= min_h:
        random_velocity_x = random.randint(0, max_h * 2) - max_h

    random_velocity_y = 0
    while abs(random_velocity_y) <= min_v:
        random_velocity_y = random.randint(0, max_v * 2) - max_v

    return random_velocity_x, random_velocity_y
