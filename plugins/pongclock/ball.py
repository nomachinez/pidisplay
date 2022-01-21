""" Create a Ball sprite """
import math
import pygame


class Ball(pygame.sprite.DirtySprite):
    """ Ball object """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, config, helper, velocity, screen_width, screen_height):
        # pylint: disable=too-many-arguments
        pygame.sprite.DirtySprite.__init__(self)

        self.config = config
        self.helper = helper
        self.image = pygame.Surface([self.config["ball_width"], self.config["ball_width"]])
        self.image.fill(self.config["foreground"])

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.rect = self.image.get_rect()
        self.dirty = 2  # ball is always moving
        self.velocity = list(velocity)
        self._hity = -1

        self.firstrun = True
        self._just_lost = False
        self._lose_side = ""

        self.playscreen_height = self.screen_height - (3 * self.config["screen_margin"]) - self.config["digit_height"]
        self.playscreen_width = 0
        
        self._bounced = False

        self.reset(velocity)

    def reset(self, velocity):
        """ Resets the location of the ball to the middle of the playing field """
        self.rect.top = self.screen_height/2 - self.config["ball_width"]/2
        self.rect.left = self.screen_width/2 - self.config["ball_width"]/2
        self.velocity = list(velocity)
        self._hity = -1
        self.firstrun = True
        self._just_lost = False
        self._lose_side = ""
        self._bounced = False

    @property
    def bounced(self):
        """ If there's a ball->paddle hit, returns true """
        return self._bounced
    
    @property
    def hity(self):
        """ Location where the ball hits the side wall """
        return self._hity

    @property
    def lose_side(self):
        """ This is set to a side if it's flagged for a losing """
        return self._lose_side

    @lose_side.setter
    def lose_side(self, value):
        """ Setter for lose_side """
        self._lose_side = value

    @property
    def just_lost(self):
        """ Did we just lose (miss the paddle)? """
        return self._just_lost

    @property
    def left(self):
        """ Gets the position of the left side fo the ball """
        return self.rect.left

    @property
    def direction(self):
        """ Returns left or right depending on which direction the ball is going """
        if self.velocity[0] < 0:
            return self.config["left"]

        return self.config["right"]

    def update(self, canvas):
        """ Overridden update method """
        # pylint: disable=too-many-branches
        
        self.rect.move_ip(self.velocity)
        self._bounced = False
        
        if self.rect.top <= self.config["screen_margin"] * 2 + self.config["digit_height"]:
            # BOUNCED ON TOP
            self.helper.log(self.config, "BOUNCED")
            self.rect.top = self.config["screen_margin"] * 2 + self.config["digit_height"]
            self.velocity[1] *= -1            
        elif self.rect.bottom >= self.screen_height - self.config["screen_margin"]:
            # BOUNCED ON BOTTOM
            self.helper.log(self.config, "BOUNCED")
            self.rect.top = self.screen_height - self.config["screen_margin"] - self.config["ball_width"]
            self.velocity[1] *= -1
        elif self.rect.left <= self.config["screen_margin"] + self.config["paddle_width"]:
            # BOUNCED ON LEFT
            if self._lose_side == self.config["left"]:
                self._just_lost = True
                self.helper.log(self.config, "left just lost")
            else:
                # Not time to lose.  Just bounce the ball
                self.rect.left = self.config["screen_margin"] + self.config["paddle_width"]
                self.velocity[0] *= -1
                self._bounced = True
                self.helper.log(self.config, "BOUNCED")

        elif self.rect.right >= self.screen_width - self.config["screen_margin"] - \
                self.config["paddle_width"]:
            # BOUNCED ON RIGHT
            if self._lose_side == self.config["right"]:
                self._just_lost = True
                self.helper.log(self.config, "right just lost")
            else:
                # No time to lose.  Just bounce the ball
                self.rect.left = self.screen_width - self.config["screen_margin"] - \
                                 self.config["paddle_width"] - self.config["ball_width"]
                self.velocity[0] *= -1
                self._bounced = True
                self.helper.log(self.config, "BOUNCED")

        if self._bounced or self.firstrun:
            # now figure it where it's going to end up on the other side of the play field

            slope = (self.velocity[1] * 1.0) / (self.velocity[0] * 1.0)
            if self.velocity[0] < 0:
                slope *= -1.0

            self.playscreen_height = self.screen_height - (3 * self.config["screen_margin"]) - \
                self.config["digit_height"]
            
            if self.firstrun:
                self.playscreen_width = self.screen_width/2 - \
                                        (self.config["screen_margin"] - self.config["paddle_width"])
            else:
                self.playscreen_width = self.screen_width - self.config["screen_margin"]*2 - \
                                        self.config["paddle_width"]*2
            
            self.firstrun = False

            ball_projected_y = self.rect.top - (self.config["screen_margin"]*2 + self.config["digit_height"])
            expanded_projected_y = (slope * (self.playscreen_width*1.0)) + (ball_projected_y*1.0)

            bounces = math.floor(expanded_projected_y / (self.playscreen_height*1.0))

            projected_y = expanded_projected_y % (self.playscreen_height*1.0)

            if bounces % 2 == 1:
                projected_y = self.playscreen_height - projected_y

            # project it onto the surface coords
            self._hity = projected_y + (self.config["screen_margin"] * 2) + self.config["digit_height"] + \
                self.config["ball_width"]/2
            self.helper.log(self.config, "set hity to: {}".format(self._hity))

        # self.surface.blit(canvas, (0, 0))
        canvas.blit(self.image, self.rect)
