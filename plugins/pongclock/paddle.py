""" Create a Paddle sprite """
import random
import pygame


class Paddle(pygame.sprite.DirtySprite):
    """ Paddle object """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, config, helper, side, game_ball, screen_width, screen_height):
        # pylint: disable=too-many-arguments
        pygame.sprite.DirtySprite.__init__(self)

        self.config = config
        self.helper = helper
        self.image = self.paddle_image = pygame.Surface([self.config["paddle_width"], self.config["paddle_height"]])
        self.paddle_image.fill(self.config["foreground"])
        self.rect = self.paddle_image.get_rect()

        self.screen_width = screen_width
        self.screen_height = screen_height

        if side == self.config["left"]:
            self.rect.left = self.config["screen_margin"]
        elif side == self.config["right"]:
            self.rect.left = self.screen_width - self.config["screen_margin"] - self.config["paddle_width"]

        self.velocity = 0.0
        self.game_ball = game_ball
        self.side = side
        self.dirty = 1  # Paddle is not always moving
        self.my_real_y = 0
        self.random_factor = 0
        self.real_y_updated = False
        self.reset()

    def reset(self):
        """ Reset all the vars (used when the board resets) """
        self.rect.top = self.screen_height/2 - self.config["paddle_height"]/2
        self.hit()
        
    def hit(self):
        """ Resets vars for when there has been a ball -> paddle collision """
        self.random_factor = 0
        self.real_y_updated = False
        self.my_real_y = 0
        self.velocity = 0.0
        self.helper.log(self.config, "HIT or RESET: {}".format(self.side))

    def update_real_y_for_losing(self):
        """ Updates self.my_real_y if we're about to lose the ball """
        if self.my_real_y == self.game_ball.hity and self.game_ball.lose_side == self.side:
            self.helper.log(self.config, "time to lose {}".format(self.side))
            if self.my_real_y > \
                    self.screen_height - self.config["screen_margin"] - self.config["paddle_height"]:
                # ball will hit the lower corner
                self.helper.log(self.config, "Ball will hit lower corner {}".format(self.side))
                self.my_real_y -= self.config["paddle_height"]
            elif self.my_real_y < \
                    self.config["screen_margin"] * 2 + self.config["paddle_height"] + self.config["digit_height"]:
                # ball will hit in the upper corner
                self.helper.log(self.config, "Ball will hit upper corner {}".format(self.side))
                self.my_real_y += self.config["paddle_height"]
            else:
                self.helper.log(self.config, "Ball will hit somewhere in the middle {}".format(self.side))
                if random.random() < .5:
                    self.my_real_y += self.config["paddle_height"]
                else:
                    self.my_real_y -= self.config["paddle_height"]

            if self.my_real_y != self.game_ball.hity:
                self.real_y_updated = True
                self.helper.log(self.config,
                                "my_real_y updated: {} {} {}".format(self.my_real_y, self.game_ball.hity, self.side))
               
    def update_real_y_for_screen_edge(self):
        """ Update self.my_real_y in case the ball is too close to the top or bottom """
        top = self.config["screen_margin"] * 2 + self.config["digit_height"] + self.config["paddle_height"]
        top_paddle_middle = self.config["screen_margin"] * 2 + self.config["digit_height"] + \
            self.config["paddle_height"]/2
        bottom = self.screen_height - self.config["screen_margin"] - self.config["paddle_height"]
        bottom_paddle_middle = self.screen_height - self.config["screen_margin"] - \
            self.config["paddle_height"]/2

        if self.my_real_y < top:
            self.my_real_y = top_paddle_middle
        elif self.my_real_y > bottom:
            self.my_real_y = bottom_paddle_middle

    def update(self, canvas):
        """ Overridden update() """
        # pylint: disable=too-many-nested-blocks

        if self.game_ball.direction == self.side:
            if (self.game_ball.direction == self.config["left"] and
                self.game_ball.left < self.screen_width/2) or \
                    (self.game_ball.direction == self.config["right"] and
                     self.game_ball.left > self.screen_width/2):

                if self.random_factor == 0:
                    # Randomize when the paddle starts moving in relation to the x value of the ball
                    self.random_factor = random.randint(self.screen_width/8, self.screen_width/4)
                    self.my_real_y = self.game_ball.hity
                    self.helper.log(self.config, "my real y updated to: {} {}".format(self.my_real_y, self.side))

                if (self.game_ball.direction == self.config["left"] and
                    self.game_ball.left < self.screen_width/2 - self.random_factor) or \
                        (self.game_ball.direction == self.config["right"] and
                         self.game_ball.left > self.screen_width/2 + self.random_factor):
                    
                    self.update_real_y_for_losing()
                    
                    self.update_real_y_for_screen_edge()
                        
                    # now figure out how much we have to move
                    distance = (self.my_real_y - (self.rect.top + self.rect.height/2)) / \
                        self.config["paddle_speed_factor"]
                        
                    self.velocity = distance
                    if self.rect.top - self.rect.height/2 == self.my_real_y:
                        self.helper.log(self.config, "We're here. {}".format(self.side))
                    else:
                        self.rect.move_ip(0, self.velocity)
                        self.dirty = 1

        canvas.blit(self.image, self.rect)
