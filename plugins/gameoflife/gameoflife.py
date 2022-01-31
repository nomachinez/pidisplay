"""
Conways Game of Life
(c) Steven Babineau - babineau@gmail.com
2022
"""
import os
import random
import pygame
from lib.plugin import Singleton
from lib.fullscreen_plugin import FullScreenPlugin


class GameOfLife(FullScreenPlugin, metaclass=Singleton):
    """ Conways Game of Life """

    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.world = []
        self.world_colors = []
        self.world_width = self.plugin_config.getint("world_width")
        self.world_height = 0
        if self.plugin_config.getint("world_height") < 0:
            self.world_height = int(((self.screen_height * 1.0) / (self.screen_width * 1.0)) * (self.world_width * 1.0))
        else:
            self.world_height = self.plugin_config.getint(["world_height"])

        self.cell_width = (self.screen_width * 1.0) / self.world_width
        self.cell_height = (self.screen_height * 1.0) / self.world_height

        self.lifetimes = 0

        self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("generation_size"))

        self.helper.log(self.debug, "Cell Size: {} {}".format(self.cell_width, self.cell_height))

        self.foreground = eval(self.plugin_config["foreground"])
        self.background = eval(self.plugin_config["background"])
        self.foreground_old = eval(self.plugin_config["foreground_old"])
        self.generation_color = eval(self.plugin_config["generation_color"])

        self.reset_world()

    def handle_click(self, pos):
        self.reset_world()

    def reset_world(self):
        # reset the board
        self.world = [(random.randint(1, 100) <= self.plugin_config.getint("starting_population_chance")) for x in
                      range(self.world_width * self.world_height)]
        self.lifetimes = 0

        self.world_colors = []
        for i in range(len(self.world)):
            self.world_colors.append(pygame.Vector3(self.foreground))

    def update(self, tick):
        if self.lifetimes >= self.plugin_config.getint("max_generations") or self.just_in:
            self.reset_world()

        if tick == 1:
            self.canvas.fill(self.background)

            # Draw all the lives
            # pylint: disable=invalid-name
            x = 0
            y = 0
            for i in range(len(self.world)):
                box = pygame.Rect(x*self.cell_width, y*self.cell_height, self.cell_width-1, self.cell_height-1)
                if self.world[i]:
                    # self.helper.log(self.config, "{0} is alive...".format(i))
                    pygame.draw.rect(self.canvas, self.world_colors[i], box)

                x = x + 1
                if x >= self.world_width:
                    y = y + 1
                    x = 0

            if self.plugin_config.getboolean("show_generation"):
                surf_generations = self.font.render(str(self.lifetimes), True, self.generation_color)
                self.canvas.blit(surf_generations, (self.canvas.get_width() - surf_generations.get_width(), 0))

            self.update_world()
            self.lifetimes += 1

    def update_world(self):
        my_world = list(self.world)
        num_changed = 0
        for i in range(len(self.world)):
            neighbors = get_neighbors(self.world, i, self.world_width)
            num_alive = 0
            for j in range(len(neighbors)):
                if neighbors[j]:
                    num_alive += 1

            if self.world[i] and num_alive < 2:
                # check for under population (< 2 neighbors)
                my_world[i] = False
                num_changed += 1
                # self.helper.log(self.config, "{0} is under populated with {1} neighbors, {2} are alive. Killing."
                #                 .format(i, len(neighbors), num_alive))
            elif self.world[i] and num_alive > 3:
                # check for over population (> 3 neighbors)
                my_world[i] = False
                num_changed += 1
                # self.helper.log(self.config, "{0} is over populated with {1} neighbors, {2} are alive. Killing."
                #                .format(i, len(neighbors), num_alive))
            elif not self.world[i] and num_alive == 3:
                # Check for new life (exactly 3 neighbors)
                my_world[i] = True
                num_changed += 1
                if self.plugin_config.getboolean("age_lives"):
                    self.world_colors[i] = pygame.Vector3(self.foreground)
                # self.helper.log(self.config, "{0} is just right with 3 neighbors. Congrats!".format(i))
            elif self.world[i]:
                if self.plugin_config.getboolean("age_lives"):
                    self.world_colors[i] = self.world_colors[i].lerp(self.foreground_old,
                                                                     self.plugin_config.getint("foreground_fade_step")/100.0)

        self.world = my_world
        return num_changed


def get_neighbors(world, i, world_width):
    neighbors = []
    if i % world_width > 0 and i-world_width-1 >= 0:  # NW
        neighbors.append(world[i-world_width-1])
    if i-world_width >= 0:  # N
        neighbors.append(world[i-world_width])
    if (i + 1) % world_width > 0 and i-world_width+1 >= 0:  # NE
        neighbors.append(world[i-world_width+1])
    if i % world_width > 0 and i-1 >= 0:  # W
        neighbors.append(world[i-1])
    if (i + 1) % world_width > 0 and i+1 < len(world):  # E
        neighbors.append(world[i+1])
    if i % world_width > 0 and i+world_width-1 < len(world):  # SW
        neighbors.append(world[i+world_width-1])
    if i+world_width < len(world):  # S
        neighbors.append(world[i+world_width])
    if (i + 1) % world_width > 0 and i+world_width+1 < len(world):  # SE
        neighbors.append(world[i+world_width+1])

    return neighbors
