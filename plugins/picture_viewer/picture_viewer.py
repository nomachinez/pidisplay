"""
Picture Viewer
(c) Steven Babineau - babineau@gmail.com
2022
"""
import os
import time
import random
import pygame
import glob
from PIL import Image, ImageFilter

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class PictureViewer(FullScreenPlugin, metaclass=Singleton):
    """ Picture Viewer """
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.pictures = []
        self.timer = -1
        self.current_picture_index = -1
        self.screen_aspect_ratio = self.screen_width * 1.0 / self.screen_height
        self.current_picture_surface = None
        self.current_picture_x = 0
        self.current_picture_y = 0
        self.blur = 40

        self.timer_bar_color = eval(self.plugin_config["timer_bar_color"])
        self.timer_bar_height = self.plugin_config.getint("timer_bar_height")
        self.slideshow_delay = self.plugin_config.getint("slideshow_delay")
        if self.plugin_config["timer_bar_position"] == "top":
            self.timer_bar_y = 0
        else:
            self.timer_bar_y = self.screen_height - self.timer_bar_height

        self.ratio = self.screen_width*1.0 / (self.slideshow_delay * 1000)
        self.timer_bar_width = 0

        self.extensions = ['png', 'jpg', 'gif']
        self.update_pics()

        print("Screen size: {}x{}".format(self.screen_width, self.screen_height))

    def update_pics(self):
        self.pictures = []
        plugin_path = os.path.abspath(os.path.dirname(__file__))

        for param in list(self.plugin_config):
            if param[:4] == "path":
                path = self.plugin_config[param]
                self.helper.log(self.debug, "Checking path {}".format(path))
                full_path = os.path.join(plugin_path, path)
                if os.path.isdir(full_path):
                    # It's a directory
                    self.helper.log(self.debug, "Found a directory. Lets scan {}".format(full_path))
                    if full_path[-1] != os.sep:
                        full_path += os.sep
                    [self.pictures.extend(glob.glob(full_path + '*.' + e)) for e in self.extensions]
                elif os.path.isfile(full_path):
                    # It's a file
                    self.pictures.append(path)
                    self.helper.log(self.debug, "Found a file")

    def handle_click(self, pos):
        self.next_pic()

    def next_pic(self):
        self.timer = -1

    def update(self, tick):
        if int(time.time() * 1000) - self.timer > self.slideshow_delay * 1000:
            # Time for next pic
            pic_num = self.current_picture_index
            if len(self.pictures) > 1:
                while pic_num == self.current_picture_index:
                    pic_num = random.randint(0, len(self.pictures)-1)

                self.helper.log(self.debug, "Updating pic to: {}".format(self.pictures[pic_num]))
                surf_pic = pygame.image.load(self.pictures[pic_num]).convert()

                pic_aspect_ratio = surf_pic.get_width()*1.0 / surf_pic.get_height()
                if self.screen_aspect_ratio < pic_aspect_ratio:
                    pic_width = self.screen_width
                    pic_height = int(pic_width / pic_aspect_ratio)
                    self.current_picture_x = 0
                    self.current_picture_y = (self.screen_height - pic_height) / 2
                elif self.screen_aspect_ratio > pic_aspect_ratio:
                    pic_height = self.screen_height
                    pic_width = int(pic_height * pic_aspect_ratio)
                    self.current_picture_x = (self.screen_width - pic_width) / 2
                    self.current_picture_y = 0
                else:
                    pic_height = self.screen_height
                    pic_width = self.screen_width
                    self.current_picture_x = 0
                    self.current_picture_y = 0
                surf_pic = pygame.transform.scale(surf_pic, (pic_width, pic_height))

                self.current_picture_index = pic_num
                self.timer = int(time.time() * 1000)

                if self.screen_height - surf_pic.get_height() > self.screen_width - surf_pic.get_width():
                    # expand to height
                    bg_width = int(surf_pic.get_width() * (self.screen_height / surf_pic.get_height()))
                    bg_height = self.screen_height
                else:
                    # expand to width
                    bg_width = self.screen_width
                    bg_height = int(surf_pic.get_height() * (self.screen_width / surf_pic.get_width()))

                bg = pygame.transform.scale(surf_pic, (bg_width, bg_height))
                bg = bg.subsurface((bg.get_width() / 2 - self.screen_width / 2,
                                    bg.get_height() / 2 - self.screen_height / 2,
                                    self.screen_width, self.screen_height)).copy()

                blurred = Image.frombytes("RGB", bg.get_size(), pygame.image.tostring(bg, "RGB")) \
                    .filter(ImageFilter.GaussianBlur(radius=self.blur))
                self.current_picture_surface = pygame.image.fromstring(blurred.tobytes(), blurred.size, "RGB").convert()
                self.current_picture_surface.blit(surf_pic, (self.current_picture_x, self.current_picture_y))

            else:
                self.current_picture_surface = pygame.Surface((self.screen_width, self.screen_height))
                font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("default_font_size"))
                surf_error = font.render("No pictures found!", True, (200, 200, 200))
                self.current_picture_surface.fill((0, 0, 0))
                self.current_picture_surface.blit(surf_error, (self.current_picture_surface.get_width()/2 - surf_error.get_width()/2,
                                                               self.current_picture_surface.get_height()/2 - surf_error.get_height()/2))

        self.canvas.blit(self.current_picture_surface, (0, 0))

        self.timer_bar_width = ((self.slideshow_delay * 1000) - (int(time.time() * 1000) - self.timer)) * self.ratio
        pygame.draw.rect(self.canvas, self.timer_bar_color, (0, self.timer_bar_y, self.timer_bar_width, self.timer_bar_height))
