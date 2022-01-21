from plugins.pongclock import pongclock as p
from plugins.pongclock import pongclock_config as c
import helper

NAME = "PongClock"
TYPE = helper.FULL_SCREEN
INSTANCE = None
ENABLED = True


def get_instance(config, canvas, screen_rect):
    global INSTANCE
    INSTANCE = p.PongClock(helper.merge_configs(config, c.CONFIG), helper, canvas)
    return INSTANCE


def handle_click(pos):
    pass


def is_enabled():
    return ENABLED


def get_type():
    return TYPE


def get_name():
    return NAME
