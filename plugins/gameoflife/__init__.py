from plugins.gameoflife import gameoflife as g
from plugins.gameoflife import gameoflife_config as c
import helper

NAME = "GameOfLife"
TYPE = helper.FULL_SCREEN
INSTANCE = None
ENABLED = True


def get_instance(config, canvas, screen_rect):
    global INSTANCE
    # We want to keep the state around so when the screen comes back ground it continues where it left off
    if INSTANCE is None:
        INSTANCE = g.GameOfLife(helper.merge_configs(config, c.CONFIG), helper, canvas)
        return INSTANCE
    else:
        return INSTANCE


def handle_click(pos):
    global INSTANCE
    if INSTANCE is not None:
        INSTANCE.handle_click(pos)


def get_type():
    return TYPE


def is_enabled():
    return ENABLED


def get_name():
    return NAME
