from plugins.openweathermap_forecast import openweathermap_forecast as g
from plugins.openweathermap_forecast import openweathermap_forecast_config as c
import helper

NAME = "OpenWeatherMap Forecast"
TYPE = helper.FULL_SCREEN
INSTANCE = None
ENABLED = True


def get_instance(config, canvas, screen_rect):
    global INSTANCE

    if INSTANCE is None:
        INSTANCE = g.OpenWeatherMap(helper.merge_configs(config, c.CONFIG), helper, canvas)
        return INSTANCE
    else:
        return INSTANCE


def handle_click(pos):
    pass


def is_enabled():
    return ENABLED


def get_type():
    return TYPE


def get_name():
    return NAME
