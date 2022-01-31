""" Programmatically creates the digits for the score/time """
import pygame.sprite


# pylint: disable=too-few-public-methods
class Scanlines(pygame.sprite.DirtySprite):
    """ Creates scanlines """
    def __init__(self, debug, plugin_config, left, top, screen_width, screen_height):
        """ creates retro scanlines """
        pygame.sprite.DirtySprite.__init__(self)

        self.dirty = 1
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = pygame.Surface([self.screen_width, self.screen_height], pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.top = top
        self.rect.left = left

        create_scanline_surface(plugin_config, self.image)
        
    def update(self, canvas):
        """DirtySprite Updates the displayed number"""
        canvas.blit(self.image, self.rect)


def create_scanline_surface(plugin_config, surface):
    """ Add all the lines to the surface """
    i = step = 5
    while i < surface.get_height():
        alpha0 = eval(plugin_config["scanline_color"])
        alpha1 = (alpha0[0], alpha0[1], alpha0[2], alpha0[3]/2)
        # alpha2 = (alpha0[0], alpha0[1], alpha0[2], alpha0[3]/4)

        # Anti alias hack
        
        # pygame.draw.line(surface, alpha2, (0, i), (config.SCREEN_WIDTH, i), 1)
        pygame.draw.line(surface, alpha1, (0, i+1), (surface.get_width(), i), 1)
        pygame.draw.line(surface, alpha0, (0, i+2), (surface.get_width(), i), 1)
        pygame.draw.line(surface, alpha1, (0, i+3), (surface.get_width(), i), 1)
        # pygame.draw.line(surface, alpha2, (0, i+4), (config.SCREEN_WIDTH, i), 1)
        
        i += step
