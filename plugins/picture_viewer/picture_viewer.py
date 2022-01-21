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


class PictureViewer:
    """ Picture Viewer """
    def __init__(self, config, helper, canvas):
        self.config = config
        self.helper = helper
        self.canvas = canvas
        self.screen_width = self.canvas.get_width()
        self.screen_height = self.canvas.get_height()
        self.pictures = []
        self.timer = -1
        self.current_picture_index = -1
        self.screen_aspect_ratio = self.screen_width*1.0 / self.screen_height
        self.current_picture_surface = None
        self.current_picture_x = 0
        self.current_picture_y = 0

        self.update_pics()

    def update_pics(self):
        self.pictures = []
        plugin_path = os.path.abspath(os.path.dirname(__file__))

        for path in self.config["paths"]:
            self.helper.log(self.config, "Checking path {}".format(path))
            full_path = os.path.join(plugin_path, path)
            if os.path.isdir(full_path):
                # It's a directory
                self.helper.log(self.config, "Found a directory. Lets scan {}".format(full_path))
                # files = [f for f in os.listdir(path) if os.isfile(os.path.join(path, f))]
                if full_path[-1] != os.sep:
                    full_path += os.sep
                [self.pictures.extend(glob.glob(full_path + '*.' + e)) for e in self.config["extensions"]]
            elif os.path.isfile(full_path):
                # It's a file
                self.pictures.append(path)
                self.helper.log(self.config, "Found a file")

    def handle_click(self, pos):
        self.next_pic()

    def next_pic(self):
        self.timer = -1

    def update(self, tick, canvas):
        if int(time.time() * 1000) - self.timer > self.config["slideshow_delay"]*1000:
            # Time for next pic
            pic_num = self.current_picture_index
            if len(self.pictures) > 1:
                while pic_num == self.current_picture_index:
                    pic_num = random.randint(0, len(self.pictures)-1)

            self.helper.log(self.config, "Updating pic to: {}".format(self.pictures[pic_num]))
            self.current_picture_surface = pygame.image.load(self.pictures[pic_num]).convert()

            pic_aspect_ratio = self.current_picture_surface.get_width()*1.0 / self.current_picture_surface.get_height()
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
            self.current_picture_surface = pygame.transform.scale(self.current_picture_surface, (pic_width, pic_height))

            self.current_picture_index = pic_num
            self.timer = int(time.time() * 1000)

        canvas.fill(self.config["background"])
        canvas.blit(self.current_picture_surface, (self.current_picture_x, self.current_picture_y))

        if self.config["timer_bar_position"] == "top":
            timer_bar_y = 0
        else:
            timer_bar_y = self.screen_height - self.config["timer_bar_height"]

        ratio = self.screen_width*1.0 / (self.config["slideshow_delay"] * 1000)
        timer_bar_width = ((self.config["slideshow_delay"] * 1000) - (int(time.time() * 1000) - self.timer)) * ratio
        pygame.draw.rect(canvas, self.config["timer_bar_color"],
                         (0, timer_bar_y, timer_bar_width, self.config["timer_bar_height"]))

        return canvas
