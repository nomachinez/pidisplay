from plugins.ticker import ticker as g
from plugins.ticker import ticker_config as c
import helper

NAME = "Ticker"
TYPE = helper.WIDGET
LOCATION = helper.WIDGET_LOCATION_TOP
NEED_FLIP = True
ENABLED = True


def get_instance(config, canvas):
    return g.Ticker(helper.merge_configs(config, c.CONFIG), helper, canvas)


def get_location():
    return LOCATION


def need_flip():
    return NEED_FLIP


def get_type():
    return TYPE


def is_enabled():
    return ENABLED


def get_name():
    return NAME
