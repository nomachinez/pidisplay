from plugins.picture_viewer import picture_viewer as pv
from plugins.picture_viewer import picture_viewer_config as c
import helper

NAME = "Picture Viewer"
TYPE = helper.FULL_SCREEN
INSTANCE = None
ENABLED = True


def get_instance(config, canvas, screen_rect):
    global INSTANCE
    INSTANCE = pv.PictureViewer(helper.merge_configs(config, c.CONFIG), helper, canvas)
    return INSTANCE


def get_location():
    return None


def handle_click(pos):
    global INSTANCE
    if INSTANCE is not None:
        INSTANCE.handle_click(pos)


def is_enabled():
    return ENABLED


def get_type():
    return TYPE


def get_name():
    return NAME
