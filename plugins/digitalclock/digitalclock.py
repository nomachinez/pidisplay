import datetime
import os

import pygame

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class DigitalClock(FullScreenPlugin, metaclass=Singleton):
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.screen_margin = self.plugin_config.getint("screen_margin")
        self.fg_color = eval(self.plugin_config["foreground_color"])
        self.bg_color = eval(self.plugin_config["background_color"])
        self.show_seconds = self.plugin_config.getboolean("show_seconds")

        screen_height = self.canvas.get_height() - self.screen_margin*2
        screen_width = self.canvas.get_width() - self.screen_margin*2

        self.font_size = 10
        font_str = self.plugin_config["font_face"]
        if font_str:
            if font_str[-4:].lower() == ".ttf" or font_str[-4:].lower() == ".otf":
                filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", font_str))

                self.font = pygame.font.Font(filename, self.font_size)
                size = self.font.size("00:00:00")
                while size[0] < screen_width and size[1] < screen_height:
                    self.font_size += 1
                    self.font = pygame.font.Font(filename, self.font_size)
                    size = self.font.size("00:00:00")

                self.font_size -= 1
                self.font = pygame.font.Font(filename, self.font_size)
            else:
                self.font = pygame.font.SysFont(font_str, self.font_size)
                size = self.font.size("00:00:00")
                while size[0] < screen_width and size[1] < screen_height:
                    self.font_size += 1
                    self.font = pygame.font.SysFont(font_str, self.font_size)
                    size = self.font.size("00:00:00")

                self.font_size -= 1
                self.font = pygame.font.SysFont(font_str, self.font_size)
        else:
            self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.font_size)

            size = self.font.size("00:00:00")
            while size[0] < screen_width and size[1] < screen_height:
                self.font_size += 1
                self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.font_size)
                size = self.font.size("00:00:00")

            self.font_size -= 1
            self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.font_size)

    def update(self, tick, fps):
        now = datetime.datetime.now()
        self.canvas.fill(self.bg_color)

        if self.show_seconds:
            surf_text = self.font.render(now.strftime("%H:%M:%S"), True, self.fg_color)
        else:
            surf_text = self.font.render(now.strftime("%H:%M"), True, self.fg_color)
        self.canvas.blit(surf_text, (self.canvas.get_width() / 2 - surf_text.get_width() / 2, self.canvas.get_height() / 2 - surf_text.get_height() / 2))

