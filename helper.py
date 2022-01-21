""" Helper variables and functions for pidisplay """
import pygame
import threading

FULL_SCREEN = "fullscreen"
WIDGET = "widget"
WIDGET_LOCATION_TOP = "top"
WIDGET_LOCATION_BOTTOM = "bottom"
WIDGET_LOCATION_MIDDLE_RIGHT = "middle right"
WIDGET_LOCATION_MIDDLE_LEFT = "middle left"
WIDGET_LOCATION_LEFT = "left"
WIDGET_LOCATION_RIGHT = "right"

EVENT_MESSAGE = pygame.USEREVENT + 3
EVENT_DOUBLECLICK = pygame.USEREVENT + 2


def merge_configs(config1, config2):
    """ Merges 2 dictionaries """
    result = config1.copy()
    result.update(config2)
    return result


def log(config, msg):
    """ Basic logger """
    if config["debug"]:
        lock = threading.Lock()
        lock.acquire()
        print(msg)
        lock.release()


def send_message(message):
    my_event = pygame.event.Event(EVENT_MESSAGE, message=[message])
    pygame.event.post(my_event)
