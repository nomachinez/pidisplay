"""
Conways Game of Life
(c) Steven Babineau - babineau@gmail.com
2022
"""
from __future__ import print_function
import pygame
from datetime import datetime


class Clok(pygame.sprite.DirtySprite):
    """ Clok """
    def __init__(self, config, helper, canvas):
        pygame.sprite.DirtySprite.__init__(self)

        self.config = config
        self.helper = helper
        self.screen_height = canvas.get_height()
        self.screen_width = canvas.get_width()

        self.image = canvas.copy()

        self.marker_location = (0, 0)

        for (start, color) in self.config["locations"]:
            dt = datetime.strptime(start, '%H:%M%p')
            start_mins = dt.hour * 60 + dt.minute
            pygame.draw.rect(self.image, color,
                             pygame.Rect(start_mins, 0, self.screen_width - start_mins, self.screen_height))

        self.minute_ratio = (self.screen_width*1.0) / (24 * 60)
        self.helper.log(self.config, "Width: {} Minute Ratio: {}".format(self.screen_width, self.minute_ratio))

    def update(self, tick, canvas):
        if self.image is not None:
            canvas.blit(self.image, (0, 0))
            pygame.draw.rect(canvas, self.config["needle_color"],
                             (self.marker_location[0], self.marker_location[1],
                              self.config["needle_width"], canvas.get_height()))

        if tick == 1:
            # Update the marker
            now = datetime.now()
            loc = now.hour * 60 + now.minute
            self.marker_location = (loc * self.minute_ratio, 0)
            self.dirty = 1
