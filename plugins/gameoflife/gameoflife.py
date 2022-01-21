"""
Conways Game of Life
(c) Steven Babineau - babineau@gmail.com
2022
"""
import random
import pygame


class GameOfLife:
    """ Conways Game of Life """
    def __init__(self, config, helper, canvas):
        self.config = config
        self.helper = helper
        self.canvas = canvas
        self.screen_width = self.canvas.get_width()
        self.screen_height = self.canvas.get_height()
        if self.config["world_height"] == -1:
            self.config["world_height"] = int(((self.screen_height * 1.0) /
                                               (self.screen_width * 1.0)) *
                                              (self.config["world_width"] * 1.0))

        self.world = []
        self.world_colors = []
        self.cell_width = (self.screen_width*1.0) / self.config["world_width"]
        self.cell_height = (self.screen_height*1.0) / self.config["world_height"]

        self.lifetimes = 0

        self.font = pygame.font.SysFont(self.config["application_sysfont"], self.config["generation_size"])

        self.helper.log(self.config, "Cell Size: {} {}".format(self.cell_width, self.cell_height))

        self.reset_world()

    def handle_click(self, pos):
        self.reset_world()

    def reset_world(self):
        # reset the board
        self.world = [(random.randint(1, 100) <= self.config["starting_population_chance"]) for x in
                      range(self.config["world_width"] * self.config["world_height"])]
        self.lifetimes = 0

        self.world_colors = []
        for i in range(len(self.world)):
            self.world_colors.append(pygame.Vector3(self.config["foreground"]))

    def update(self, tick, canvas):
        if self.lifetimes >= self.config["max_generations"]:
            self.reset_world()

        if tick == 1:
            canvas.fill(self.config["background"])

            # Draw all the lives
            # pylint: disable=invalid-name
            x = 0
            y = 0
            for i in range(len(self.world)):
                box = pygame.Rect(x*self.cell_width, y*self.cell_height, self.cell_width-1, self.cell_height-1)
                if self.world[i]:
                    # self.helper.log(self.config, "{0} is alive...".format(i))
                    pygame.draw.rect(canvas, self.world_colors[i], box)

                x = x + 1
                if x >= self.config["world_width"]:
                    y = y + 1
                    x = 0

            if self.config["show_generation"]:
                surf_generations = self.font.render("{}".format(self.lifetimes), True, self.config["generation_color"])

                canvas.blit(surf_generations, (canvas.get_width() - surf_generations.get_width(), 0))

            self.helper.log(self.config, "Drawing world.")
        elif self.config["frames_per_second"] / 2 == tick:
            self.update_world()
            self.lifetimes += 1
            self.helper.log(self.config, "Updated world.")

        return canvas

    def update_world(self):
        my_world = list(self.world)
        num_changed = 0
        for i in range(len(self.world)):
            neighbors = get_neighbors(self.world, i, self.config["world_width"])
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
                if self.config["age_lives"]:
                    self.world_colors[i] = pygame.Vector3(self.config["foreground"])
                # self.helper.log(self.config, "{0} is just right with 3 neighbors. Congrats!".format(i))
            elif self.world[i]:
                if self.config["age_lives"]:
                    self.world_colors[i] = self.world_colors[i].lerp(self.config["foreground_old"],
                                                                     self.config["foreground_fade_step"]/100.0)
                # self.helper.log(self.config, "{0} is still alive!".format(i))

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
