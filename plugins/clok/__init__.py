from plugins.clok import clok as g
from plugins.clok import clok_config as c
import helper

NAME = "Clok"
TYPE = helper.WIDGET
LOCATION = helper.WIDGET_LOCATION_BOTTOM
ENABLED = True


def get_instance(config, canvas):
    return g.Clok(helper.merge_configs(config, c.CONFIG), helper, canvas)


def get_location():
    return LOCATION


def get_type():
    return TYPE


def is_enabled():
    return ENABLED


def get_name():
    return NAME
