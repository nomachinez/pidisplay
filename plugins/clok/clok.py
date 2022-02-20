"""
Clok
(c) Steven Babineau - babineau@gmail.com
2022
"""
import os
import pygame
from datetime import datetime
from pygame.sprite import DirtySprite

from lib.widget_plugin import WidgetPlugin


class Clok(DirtySprite, WidgetPlugin):
    """ Clok """
    def __init__(self, helper, canvas, app_plugin_config):
        DirtySprite.__init__(self)
        WidgetPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.image = canvas.copy()

        self.marker_location = (0, 0)

        self.marker_color = eval(self.plugin_config["needle_color"])

        self.helper.log(self.debug, "Clok: {} x {}".format(self.canvas.get_width(), self.screen_height))

        i = 1
        locations = []
        for param in list(self.plugin_config):
            if param[:8] == "location":
                if "location{}_start".format(i) in self.plugin_config:
                    start = self.plugin_config["location{}_start".format(i)]
                    color = eval(self.plugin_config["location{}_color".format(i)])
                    locations.append({"start": start, "color": color})
                    i += 1

        self.helper.log(self.debug, "Number of locations in Clok: {}".format(len(locations)))

        for location in locations:
            dt = datetime.strptime(location["start"], '%H:%M%p')
            start_mins = dt.hour * 60 + dt.minute
            pygame.draw.rect(self.image, location["color"],
                             pygame.Rect(start_mins, 0, self.screen_width - start_mins, self.screen_height))

        self.minute_ratio = (self.screen_width*1.0) / (24 * 60)
        self.helper.log(self.debug, "Width: {} Minute Ratio: {}".format(self.screen_width, self.minute_ratio))

    def update(self, tick, fps):
        if self.image is not None:
            self.canvas.blit(self.image, (0, 0))
            pygame.draw.rect(self.canvas, self.marker_color,
                             (self.marker_location[0], self.marker_location[1],
                              self.plugin_config.getint("needle_width"), self.canvas.get_height()))

        if tick == 1:
            # Update the marker
            now = datetime.now()
            loc = now.hour * 60 + now.minute
            self.marker_location = (loc * self.minute_ratio, 0)
            self.dirty = 1
