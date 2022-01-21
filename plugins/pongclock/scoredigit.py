""" Programmatically creates the digits for the score/time """
import pygame.sprite

DIGIT_SEGMENTS = {'0': '1111110', '1': '0110000', '2': '1101101', '3': '1111001', '4': '0110011',
                  '5': '1011011', '6': '1011111', '7': '1110000', '8': '1111111', '9': '1111011'}


class ScoreDigit(pygame.sprite.DirtySprite):
    """Draws a score digit"""

    def __init__(self, config, helper, left, top, digit):
        """Draws a score digit"""
        pygame.sprite.DirtySprite.__init__(self)
        self.config = config
        self.helper = helper
        self.image = pygame.Surface([self.config["digit_width"], self.config["digit_height"]])
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.top = top
        self.rect.left = left
        self.draw_segments(digit)

    def draw_segments(self, digit):
        """draws the digit segments. Only need to update it when it changes."""
        # pylint: disable=bad-whitespace, invalid-name

        #
        #      0
        #  5       1
        #      6
        #  4       2
        #      3
        #

        self.image = self.original_image.copy()

        try:
            segments_key = globals()['DIGIT_SEGMENTS'][str(digit)]
        except KeyError:
            raise ValueError("Invalid digit passed", digit)
        
        dw = self.config["digit_width"]
        dh = self.config["digit_height"]
        lw = self.config["digit_line_width"]
        fg = self.config["foreground"]
        
        #                                   left     top                width height
        if segments_key[0] == "1":
            self.image.fill(fg, pygame.Rect(0,       0,                   dw,   lw))
        if segments_key[1] == "1":
            self.image.fill(fg, pygame.Rect(dw - lw, 0,                   lw,   dh / 2))
        if segments_key[2] == "1":
            self.image.fill(fg, pygame.Rect(dw - lw, dh / 2,              lw,   dh / 2))
        if segments_key[3] == "1":
            self.image.fill(fg, pygame.Rect(0,       dh - lw,             dw,   lw))
        if segments_key[4] == "1":
            self.image.fill(fg, pygame.Rect(0,       dh / 2,              lw,   dh / 2))
        if segments_key[5] == "1":
            self.image.fill(fg, pygame.Rect(0,       0,                   lw,   dh / 2))
        if segments_key[6] == "1":
            self.image.fill(fg, pygame.Rect(0,       (dh / 2) - (lw / 2), dw,   lw))

        self.dirty = 1

    def update(self, canvas):
        """Display the digit"""
        canvas.blit(self.image, self.rect)
