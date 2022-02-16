""" Helper variables and functions for pidisplay """
import ipaddress
import math
import socket
from datetime import timedelta
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
LEFT = "LEFT"
RIGHT = "RIGHT"
RED = (200, 0, 0)
FAHRENHEIT = "fahrenheit"
CELSIUS = "celsius"
PING = "ping"
CONNECT = "connect"
EVENT_MESSAGE = pygame.USEREVENT + 3
EVENT_DOUBLECLICK = pygame.USEREVENT + 2


def merge_configs(config1, config2):
    """ Merges 2 dictionaries """
    result = config1.copy()
    result.update(config2)
    return result


def log(debug, msg):
    """ Basic logger """
    if debug:
        lock = threading.Lock()
        lock.acquire()
        print(msg)
        lock.release()


def upper_first_char(val):
    return "{}{}".format(val[:1].capitalize(), val[1:])


def send_message(message):
    my_event = pygame.event.Event(EVENT_MESSAGE, message=[message])
    pygame.event.post(my_event)


# From https://github.com/lordmauve/pgzero/blob/master/pgzero/ptext.py#L125
def wrap(text, font, max_width, strip=True):
    texts = text.replace("\t", "    ").split("\n")
    lines = []
    for text in texts:
        if strip:
            text = text.rstrip(" ")
        if max_width is None:
            lines.append(text)
            continue
        if not text:
            lines.append("")
            continue
        # Preserve leading spaces in all cases.
        a = len(text) - len(text.lstrip(" "))
        # At any time, "a" is the rightmost known index you can legally split a line. I.e. it's legal
        # to add text[:a] to lines, and line is what will be added to lines if text is split at a.
        a = text.index(" ", a) if " " in text else len(text)
        line = text[:a]
        while a + 1 < len(text):
            # b is the next legal place to break the line, with bline the
            # corresponding line to add.
            if " " not in text[a + 1:]:
                b = len(text)
                # bline = text
            elif strip:
                # Lines may be split at any space character that immediately follows a non-space
                # character.
                b = text.index(" ", a + 1)
                while text[b - 1] == " ":
                    if " " in text[b + 1:]:
                        b = text.index(" ", b + 1)
                    else:
                        b = len(text)
                        break
                # bline = text[:b]
            else:
                # Lines may be split at any space character, or any character immediately following
                # a space character.
                b = a + 1 if text[a] == " " else text.index(" ", a + 1)
            bline = text[:b]
            if font.size(bline)[0] <= max_width:
                a, line = b, bline
            else:
                lines.append(line)
                text = text[a:].lstrip(" ") if strip else text[a:]
                a = text.index(" ", 1) if " " in text[1:] else len(text)
                line = text[:a]
        if text:
            lines.append(line)
    return lines


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s%s" % (s, size_name[i])


def get_time_delta_string(now, past, want_seconds=True, want_ago=True, want_short_names=False):
    result = ""

    delta = now - past

    if isinstance(delta, float):
        delta = timedelta(seconds=delta)

    days = delta.days
    hours = int(delta.seconds / 60 / 60)
    minutes = int((delta.seconds / 60) - (hours * 60))
    seconds = int(delta.seconds - (hours * 60 * 60) - (minutes * 60))

    if days > 0:
        if want_short_names:
            result += "{}d".format(days)
        else:
            result += "{} day".format(days)
            if days > 1:
                result += "s"
    if hours > 0:
        if len(result) > 0:
            result += ", " if not want_short_names else " "

        if want_short_names:
            result += "{}h".format(hours)
        else:
            result += "{} hour".format(hours)
            if hours > 1:
                result += "s"
    if minutes > 0:
        if len(result) > 0:
            result += ", " if not want_short_names else " "

        if want_short_names:
            result += "{}m".format(minutes)
        else:
            result += "{} minute".format(minutes)
            if minutes > 1:
                result += "s"
    if want_seconds:
        if seconds > 0:
            if len(result) > 0:
                result += ", " if not want_short_names else " "

            if want_short_names:
                result += "{}s".format(seconds)
            else:
                result += "{} second".format(seconds)
                if seconds > 1:
                    result += "s"

    if want_ago:
        result += " ago"

    return result


def get_subnet_mask_bits(subnet_mask):
    cidr = 0
    try:
        socket.inet_aton(subnet_mask)
        cidr = ipaddress.IPv4Network("0.0.0.0/{}".format(subnet_mask)).prefixlen
    except Exception:
        print("BAD SUBNET MASK: {}".format(subnet_mask))

    return cidr
