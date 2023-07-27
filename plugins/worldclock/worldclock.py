import datetime
import math
import os

import pygame
import pytz

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class WorldClock(FullScreenPlugin, metaclass=Singleton):
    """ World Clock """
    COLORS_BIG = "big"
    COLORS_SMALL = "small"

    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)
        self.image = canvas.copy()
        self.bg_color = eval(self.plugin_config["background_color"])
        self.screen_margin = self.plugin_config.getint("screen_margin")

        self.big_clock_bg_color = eval(self.plugin_config["big_clock_bg_color"])
        self.big_clock_fg_color = eval(self.plugin_config["big_clock_fg_color"])
        self.big_clock_border_color = eval(self.plugin_config["big_clock_border_color"])
        self.big_clock_big_hand_color = eval(self.plugin_config["big_clock_big_hand_color"])
        self.big_clock_small_hand_color = eval(self.plugin_config["big_clock_small_hand_color"])
        self.big_clock_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("big_clock_label_size"))
        self.big_clock_show_seconds = self.plugin_config.getboolean("big_clock_show_seconds")
        self.big_clock_hand_width = self.plugin_config.getint("big_clock_hand_width")
        self.big_clock_border_width = self.plugin_config.getint("big_clock_border_width")

        self.small_clock_bg_color = eval(self.plugin_config["small_clock_bg_color"])
        self.small_clock_fg_color = eval(self.plugin_config["small_clock_fg_color"])
        self.small_clock_border_color = eval(self.plugin_config["small_clock_border_color"])
        self.small_clock_big_hand_color = eval(self.plugin_config["small_clock_big_hand_color"])
        self.small_clock_small_hand_color = eval(self.plugin_config["small_clock_small_hand_color"])
        self.small_clock_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("small_clock_label_size"))
        self.small_clock_show_seconds = self.plugin_config.getboolean("small_clock_show_seconds")
        self.small_clock_hand_width = self.plugin_config.getint("small_clock_hand_width")
        self.small_clock_border_width = self.plugin_config.getint("small_clock_border_width")

        self.clocks = []
        i = 1
        for param in list(self.plugin_config):
            if param[:5] == "clock":
                if "clock{}_timezone".format(i) in self.plugin_config:
                    label = self.plugin_config["clock{}_label".format(i)]
                    timezone = self.plugin_config["clock{}_timezone".format(i)]

                    self.clocks.append({"label": label, "timezone": timezone})

                    i += 1

        # now figure out the placement of all the clocks
        for i in range(len(self.clocks)):
            if len(self.clocks) == 1:
                size = WorldClock.COLORS_BIG

                label_size = self.big_clock_font.get_height()
                if not self.clocks[0]["label"]:
                    label_size = 0

                if self.image.get_height() > self.image.get_width():
                    clock_radius = (self.image.get_width() - self.screen_margin * 2) / 2
                else:
                    if label_size > 0:
                        clock_radius = (self.image.get_height() - self.screen_margin * 3 - label_size) / 2
                    else:
                        clock_radius = (self.image.get_height() - self.screen_margin * 2) / 2

                clock_center_x = self.image.get_width() / 2
                clock_center_y = self.screen_margin + clock_radius

            elif len(self.clocks) == 2:
                # It's a medium-sized clock, no smaller ones
                size = WorldClock.COLORS_BIG

                label_size = self.big_clock_font.get_height()
                if not self.clocks[0]["label"] and not self.clocks[1]["label"]:
                    label_size = 0

                w = (self.image.get_width() / 2) - (self.screen_margin * 2)
                h = self.image.get_height() - (self.screen_margin * 2) - label_size
                if h > w:
                    clock_radius = w / 2
                else:
                    clock_radius = h / 2

                if i == 0:
                    # medium, left
                    clock_center_x = self.image.get_width()/4
                else:
                    # medium, right
                    clock_center_x = (self.image.get_width()/4) * 3
                clock_center_y = self.screen_margin + ((clock_radius * 2 + self.screen_margin + label_size) / 2)
            else:
                # There are more than 2 clocks
                small_clock_height = (self.image.get_height() - self.screen_margin*2)/4 - (self.small_clock_font.get_height() + self.screen_margin)

                large_clock_height = (self.image.get_height() - self.screen_margin*2)/4 * 3 - self.screen_margin - (self.big_clock_font.get_height() + self.screen_margin)
                if i <= 1:
                    size = WorldClock.COLORS_BIG
                    w = (self.image.get_width() / 2) - (self.screen_margin * 2)
                    h = large_clock_height
                    if w > h:
                        clock_radius = h / 2
                    else:
                        clock_radius = w / 2

                    if i == 0:
                        # medium, left
                        clock_center_x = self.image.get_width() / 4
                    elif i == 1:
                        # medium, right
                        clock_center_x = self.image.get_width() / 4 * 3
                    else:
                        raise ValueError("More than 2 clocks, but i is.... negative? i was: {}".format(i))
                    clock_center_y = self.image.get_height() - self.screen_margin - clock_radius - (self.big_clock_font.get_height() + self.screen_margin)

                else:
                    size = WorldClock.COLORS_SMALL
                    # small clock on the top
                    # figure out how many total there are
                    num_small_clocks = len(self.clocks) - 2
                    clock_radius = small_clock_height / 2
                    clock_cell_width = (self.image.get_width() - self.screen_margin) / num_small_clocks
                    clock_center_x = clock_cell_width * (i - 2) + (clock_cell_width / 2) + self.screen_margin
                    clock_center_y = self.screen_margin + clock_radius + self.screen_margin + self.small_clock_font.get_height()

            self.clocks[i].update({"center_x": clock_center_x, "center_y": clock_center_y, "radius": clock_radius, "size": size})

        self.draw_clock_outlines()

    def draw_clock_outline(self, colors_type, clock):
        if colors_type == WorldClock.COLORS_BIG:
            clock_bg_color = self.big_clock_bg_color
            clock_fg_color = self.big_clock_fg_color
            clock_border_color = self.big_clock_border_color
            clock_border_width = self.big_clock_border_width
        elif colors_type == WorldClock.COLORS_SMALL:
            clock_bg_color = self.small_clock_bg_color
            clock_fg_color = self.small_clock_fg_color
            clock_border_color = self.small_clock_border_color
            clock_border_width = self.small_clock_border_width
        else:
            raise ValueError("Unknown colors_type passed to draw_clock_outline! It was: {}".format(colors_type))

        # Outside circle (border)
        pygame.draw.circle(self.image, clock_border_color, (int(clock["center_x"]), int(clock["center_y"])), int(clock["radius"]))
        # Inside circle
        pygame.draw.circle(self.image, clock_bg_color, (int(clock["center_x"]), int(clock["center_y"])), int(clock["radius"]) - clock_border_width)

        number_font_size = clock["radius"] / 6
        number_font = pygame.font.SysFont(self.plugin_config["default_font_face"], int(number_font_size))

        if colors_type == WorldClock.COLORS_BIG:
            for i in range(1, 61):
                # Draw the little lines but don't draw them on the numbers
                if i % 5 > 0:
                    angle = math.radians(i * (360 / 60))
                    start_x = math.cos(angle) * (clock["radius"] - clock_border_width) + clock["center_x"]
                    start_y = math.sin(angle) * (clock["radius"] - clock_border_width) + clock["center_y"]
                    end_x = start_x - math.cos(angle) * 3
                    end_y = start_y - math.sin(angle) * 3
                    pygame.draw.line(self.image, clock_fg_color,
                                     (start_x, start_y),
                                     (end_x, end_y),
                                     1)

        for i in range(1, 13):
            # Draw the numbers
            number_font_image = number_font.render(str(i), True, clock_fg_color)

            # add a little margin
            number_margin = number_font_image.get_width() / 10

            x = ((clock["radius"] - clock_border_width) - number_font_size / 2) * math.sin(math.pi * (i * (360 / 12)) / 180) + clock["center_x"] + number_margin
            y = -(((clock["radius"] - clock_border_width) - number_font_size / 2) * math.cos(math.pi * (i * (360 / 12)) / 180) - clock["center_y"]) + number_margin

            num_rect = number_font_image.get_rect(center=(x, y))
            self.image.blit(number_font_image, num_rect)

        # Draw the label
        if colors_type == WorldClock.COLORS_BIG:
            # Label goes on the bottom
            surf_label = self.big_clock_font.render(clock["label"], True, clock_fg_color)
            self.image.blit(surf_label, (clock["center_x"] - surf_label.get_width()/2, clock["center_y"] + clock["radius"] + self.screen_margin))
        elif colors_type == WorldClock.COLORS_SMALL:
            # label goes on the top
            surf_label = self.small_clock_font.render(clock["label"], True, clock_fg_color)
            self.image.blit(surf_label, (clock["center_x"] - surf_label.get_width()/2, clock["center_y"] - clock["radius"] - self.screen_margin - surf_label.get_height()))

    def draw_clock_outlines(self):
        self.image.fill(self.bg_color)
        for i in range(len(self.clocks)):
            if i <= 1:
                self.draw_clock_outline(WorldClock.COLORS_BIG, self.clocks[i])
            else:
                self.draw_clock_outline(WorldClock.COLORS_SMALL, self.clocks[i])

    def draw_clock_hands(self, clock):
        if clock["size"] == WorldClock.COLORS_BIG:
            big_hand_fg_color = self.big_clock_big_hand_color
            small_hand_fg_color = self.big_clock_small_hand_color
            clock_border_width = self.big_clock_border_width
            hand_width = self.big_clock_hand_width
        elif clock["size"] == WorldClock.COLORS_SMALL:
            big_hand_fg_color = self.small_clock_big_hand_color
            small_hand_fg_color = self.small_clock_small_hand_color
            clock_border_width = self.small_clock_border_width
            hand_width = self.small_clock_hand_width
        else:
            raise ValueError("Unknown size in clock object while trying to draw the clock hands. The size was: {}".format(clock["size"]))

        now = pytz.timezone(clock["timezone"]).normalize(datetime.datetime.now(pytz.timezone('UTC')))

        # Hour hand
        hour = now.hour
        if hour > 12:
            hour -= 12

        hour_deg = (hour * (360 / 12)) + (now.minute * (360 / (12 * 60)))
        start_x = (clock["radius"] / 2) * math.sin((math.pi * hour_deg) / 180) + clock["center_x"]
        start_y = -((clock["radius"] / 2) * math.cos((math.pi * hour_deg) / 180) - clock["center_y"])

        pygame.draw.line(self.canvas, big_hand_fg_color,
                         (start_x, start_y),
                         (clock["center_x"], clock["center_y"]),
                         hand_width)
        del hour_deg, start_x, start_y

        # Minute hand
        minute_deg = (now.minute * (360 / 60)) + (now.second * (360 / (60 * 60)))
        start_x = (clock["radius"] * .7 - clock_border_width) * math.sin((math.pi * minute_deg) / 180) + clock["center_x"]
        start_y = -((clock["radius"] * .7 - clock_border_width) * math.cos((math.pi * minute_deg) / 180) - clock["center_y"])
        pygame.draw.line(self.canvas, big_hand_fg_color,
                         (start_x, start_y),
                         (clock["center_x"], clock["center_y"]),
                         hand_width)
        del minute_deg, start_x, start_y

        if clock["size"] == WorldClock.COLORS_BIG:
            # draw the middle dial circles
            pygame.draw.circle(self.canvas, big_hand_fg_color, (int(clock["center_x"]), int(clock["center_y"])), int(hand_width*2))

        if (clock["size"] == WorldClock.COLORS_BIG and self.big_clock_show_seconds) or (clock["size"] == WorldClock.COLORS_SMALL and self.small_clock_show_seconds):
            # Second hand
            second_deg = (now.second * (360 / 60)) + (now.microsecond / 1000) * (360 / (60 * 1000))
            start_x = (clock["radius"] * .8 - clock_border_width) * math.sin((math.pi * second_deg) / 180) + clock["center_x"]
            start_y = -((clock["radius"] * .8 - clock_border_width) * math.cos((math.pi * second_deg) / 180) - clock["center_y"])

            pygame.draw.line(self.canvas, small_hand_fg_color,
                             (start_x, start_y),
                             (clock["center_x"], clock["center_y"]),
                             hand_width)
            del second_deg, start_x, start_y

            if clock["size"] == WorldClock.COLORS_BIG:
                # draw the middle dial circles
                pygame.draw.circle(self.canvas, small_hand_fg_color, (int(clock["center_x"]), int(clock["center_y"])), int(hand_width*1.3))

    def update(self, tick, fps):
        self.canvas.blit(self.image, (0, 0))
        for clock in self.clocks:
            self.draw_clock_hands(clock)
