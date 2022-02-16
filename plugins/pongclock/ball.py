""" Create a Ball sprite """
import math
import pygame


class Ball(pygame.sprite.DirtySprite):
    """ Ball object """
    def __init__(self, debug, plugin_config, helper, velocity, screen_width, screen_height):
        pygame.sprite.DirtySprite.__init__(self)

        self.helper = helper
        self.ball_width = plugin_config.getint("ball_width")
        self.foreground = eval(plugin_config["foreground"])
        self.screen_margin = plugin_config.getint("screen_margin")
        self.digit_height = plugin_config.getint("digit_height")
        self.paddle_width = plugin_config.getint("paddle_width")
        self.debug = debug
        self.image = pygame.Surface([self.ball_width, self.ball_width])
        self.image.fill(self.foreground)

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.rect = self.image.get_rect()
        self.dirty = 2  # ball is always moving
        self.velocity = list(velocity)
        self._hity = -1

        self.firstrun = True
        self._just_lost = False
        self._lose_side = ""

        self.y_distance_to_go = self.screen_height - (3 * self.screen_margin) - self.digit_height
        # self.playscreen_width = 0
        self.x_distance_to_go = 0
        
        self._bounced = False

        self.reset(velocity)
        self.current_slope = 0.0

    def reset(self, velocity):
        """ Resets the location of the ball to the middle of the playing field """
        self.rect.top = self.screen_height/2 - self.ball_width/2
        self.rect.left = self.screen_width/2 - self.ball_width/2
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
            return self.helper.LEFT
        return self.helper.RIGHT

    def update(self, canvas):
        """ Overridden update method """
        self.rect.move_ip(self.velocity)
        self._bounced = False
        if self.rect.top <= self.screen_margin * 2 + self.digit_height:
            # BOUNCED ON TOP
            self.helper.log(self.debug, "BOUNCED")
            self.rect.top = self.screen_margin * 2 + self.digit_height
            self.velocity[1] *= -1
            self._bounced = True
        elif self.rect.bottom >= self.screen_height - self.screen_margin:
            # BOUNCED ON BOTTOM
            self.helper.log(self.debug, "BOUNCED")
            self.rect.top = self.screen_height - self.screen_margin - self.ball_width
            self.velocity[1] *= -1
            self._bounced = True
        elif self.rect.left <= self.screen_margin + self.paddle_width:
            # BOUNCED ON LEFT
            if self._lose_side == self.helper.LEFT:
                self._just_lost = True
                self.helper.log(self.debug, "left just lost")
            else:
                # Not time to lose.  Just bounce the ball
                self.rect.left = self.screen_margin + self.paddle_width
                self.velocity[0] *= -1
                self.helper.log(self.debug, "---NEW velocity from bounce X,Y={},{}".format(self.velocity[0], self.velocity[1]))
                self._bounced = True
                self.helper.log(self.debug, "BOUNCED")

        elif self.rect.right >= self.screen_width - self.screen_margin - \
                self.paddle_width:
            # BOUNCED ON RIGHT
            if self._lose_side == self.helper.RIGHT:
                self._just_lost = True
                self.helper.log(self.debug, "right just lost")
            else:
                # No time to lose.  Just bounce the ball
                self.rect.left = self.screen_width - self.screen_margin - self.paddle_width - self.ball_width
                self.velocity[0] *= -1
                self.helper.log(self.debug, "---NEW velocity from bounce X,Y={},{}".format(self.velocity[0], self.velocity[1]))
                self._bounced = True
                self.helper.log(self.debug, "BOUNCED")

        if self._bounced or self.firstrun:
            # now figure out where it's going to end up on the other side of the play field
            # TODO: There's a problem where the ball doesn't always hit where it says its going to. Maybe has to do
            #  with the fps and the timing of the calculations and/or rounding, maybe just when it hits the top or bottom?

            self.current_slope = (self.velocity[1] * 1.0) / (self.velocity[0] * 1.0)
            if self.velocity[0] < 0:
                self.current_slope *= -1.0

            self.y_distance_to_go = self.screen_height - (3 * self.screen_margin) - self.digit_height

            if self.velocity[0] < 0:
                self.x_distance_to_go = self.rect.left - self.screen_margin - self.paddle_width
            else:
                self.x_distance_to_go = self.screen_width - self.screen_margin - self.paddle_width - self.rect.left - self.ball_width

            self.firstrun = False

            ball_projected_y = self.rect.top - (self.screen_margin * 2 + self.digit_height)
            expanded_projected_y = (self.current_slope * (self.x_distance_to_go*1.0)) + (ball_projected_y*1.0)

            bounces = math.floor(expanded_projected_y / (self.y_distance_to_go*1.0))

            projected_y = expanded_projected_y % (self.y_distance_to_go*1.0)

            if bounces % 2 == 1:
                projected_y = self.y_distance_to_go - projected_y

            # project it onto the surface coords
            self._hity = projected_y + (self.screen_margin * 2) + self.digit_height + self.ball_width/2
            self.helper.log(self.debug, "set hity to: {}".format(self._hity))

        canvas.blit(self.image, self.rect)
