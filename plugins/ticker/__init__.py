from plugins.ticker import ticker as g
from plugins.ticker import ticker_config as c
import helper

NAME = "Ticker"
TYPE = helper.WIDGET
LOCATION = helper.WIDGET_LOCATION_TOP
ENABLED = True


def get_instance(config, canvas):
    return g.Ticker(helper.merge_configs(config, c.CONFIG), helper, canvas)


def get_location():
    return LOCATION


def get_type():
    return TYPE


def is_enabled():
    return ENABLED


def get_name():
    return NAME
