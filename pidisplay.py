"""
PI Display
(c) Steven Babineau - babineau@gmail.com
2022
"""
import inspect
import sys
import os
import time
import importlib
import datetime
import pygame

from lib import helper
from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Plugin, Singleton

import configparser

from lib.widget_plugin import WidgetPlugin


def main():
    """ Main is what Main is """
    pygame.init()
    pygame.display.set_caption('PiDisplay')
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

    clock = pygame.time.Clock()
    config = configparser.RawConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini")))

    appconfig = config["pidisplay"]
    debug = appconfig.getboolean("debug")

    if pygame.version.vernum[0] == 2:
        helper.log(debug, "Running with pygame 2.X options.")
        flags = 0
    else:
        helper.log(debug, "Running with pygame 1.X options.")
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF

    screen_width = appconfig.getint("screen_width")
    screen_height = appconfig.getint("screen_height")

    if appconfig.getboolean("fullscreen_mode"):
        flags |= pygame.FULLSCREEN
        if appconfig.getboolean("fullscreen_uses_current_resolution"):
            screen_width = 0
            screen_height = 0

    if pygame.version.vernum[0] == 2:
        pygame.display.set_mode([screen_width, screen_height], flags, vsync=1)
    else:
        pygame.display.set_mode([screen_width, screen_height], flags)

    canvas = pygame.display.get_surface()

    pygame.mouse.set_pos((canvas.get_width()/2, canvas.get_height()/2))
    pygame.mouse.set_visible(False)

    plugin_modules = get_plugins(debug)
    plugins = []
    for i in config.sections():
        if i == "pidisplay":
            continue

        plugin_class_name = config[i]["class"] if "class" in config[i] else ""
        plugin_class = None
        for j in plugin_modules:
            if j["class_name"] == plugin_class_name:
                plugin_class = j["class"]
                break

        plugin_widget_location = config[i]["widget_location"] if "widget_location" in config[i] else ""
        plugin_autoswitch_timer = int(config[i]["autoswitch_timer"]) if "autoswitch_timer" in config[i] else sys.maxsize
        if plugin_class is not None:
            plugins.append({"internal_name": i,
                            "class": plugin_class,
                            "widget_location": plugin_widget_location,
                            "autoswitch_timer": plugin_autoswitch_timer,
                            "widget_height": config[i].getint("widget_height")})
        else:
            helper.log(debug, "Couldn't find class for {}".format(plugin_class_name))

    helper.log(debug, "Total modules found: {}".format(len(plugins)))

    running = True
    update = True
    tick = 0
    fps = appconfig.getint("frames_per_second")

    start_time = time.time()

    top_widget_plugins = []
    top_bar_canvases = []
    bottom_widget_plugins = []
    bottom_bar_canvases = []

    full_screen_plugins = []

    #top_bar_height = appconfig.getint("top_bar_height")
    #bottom_bar_height = appconfig.getint("bottom_bar_height")

    top_bar_y = 0
    bottom_bar_y = canvas.get_height()

    top_padding = 0
    bottom_padding = 0
    for i in range(len(plugins)):
        plugin = plugins[i]
        if WidgetPlugin in plugin["class"].__bases__:
            if plugin["widget_location"] == helper.WIDGET_LOCATION_TOP:
                top_bar_canvas = canvas.subsurface(pygame.Rect(0, top_bar_y, canvas.get_width(), plugin["widget_height"]))

                top_widget_plugins.append({"location": plugin["widget_location"],
                                           "instance": plugin["class"](helper, top_bar_canvas, config[plugin["internal_name"]])})
                top_bar_y += plugin["widget_height"]
                top_bar_canvases.append(top_bar_canvas)

            elif plugin["widget_location"] == helper.WIDGET_LOCATION_BOTTOM:
                bottom_bar_y -= plugin["widget_height"]

                bottom_bar_canvas = canvas.subsurface(pygame.Rect(0, bottom_bar_y, canvas.get_width(), plugin["widget_height"]))

                bottom_widget_plugins.append({"location": plugin["widget_location"],
                                              "instance": plugin["class"](helper, bottom_bar_canvas, config[plugin["internal_name"]])})
                bottom_bar_canvases.append(bottom_bar_canvas)
        elif FullScreenPlugin in plugin["class"].__bases__:
            full_screen_plugins.append({"class": plugin["class"], "autoswitch_timer": plugin["autoswitch_timer"], "internal_name": config[plugin["internal_name"]]})

    top_offset = top_bar_y
    bottom_offset = screen_height - bottom_bar_y

    doubleclick_timer = 0
    current_plugin = -1

    message_font = pygame.font.SysFont(appconfig["default_font_face"], appconfig.getint("default_font_size"))
    message_step = 255.0 / (fps * appconfig.getint("message_popup_fade_time"))

    full_screen_rect = pygame.Rect(0, top_offset, canvas.get_width(), canvas.get_height() - top_offset - bottom_offset)
    full_screen_canvas_small = canvas.subsurface(full_screen_rect)

    current_plugin, tick, full_screen_plugin, start_time = switch_plugin(current_plugin,
                                                                         full_screen_plugins,
                                                                         canvas, full_screen_canvas_small)

    while running:
        clock.tick(fps)

        if update:
            full_screen_plugin.update(tick)
            full_screen_plugin.just_in = False

            if full_screen_plugins[current_plugin]["internal_name"].getboolean("show_widgets"):
                for i in range(len(top_widget_plugins)):
                    top_widget_plugins[i]["instance"].update(tick)
                for i in range(len(bottom_widget_plugins)):
                    bottom_widget_plugins[i]["instance"].update(tick)

            if tick == fps:
                tick = 1
            else:
                tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    update = not update
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                timer_set = False
                if doubleclick_timer == 0:
                    pygame.time.set_timer(helper.EVENT_DOUBLECLICK, appconfig.getint("doubleclick_delay"))
                    timer_set = True
                elif doubleclick_timer == 1:
                    pygame.time.set_timer(helper.EVENT_DOUBLECLICK, 0)
                    # Switch plugins
                    current_plugin, tick, full_screen_plugin, start_time = switch_plugin(current_plugin,
                                                                                         full_screen_plugins,
                                                                                         canvas, full_screen_canvas_small)
                    timer_set = False
                if timer_set:
                    doubleclick_timer = 1
                else:
                    doubleclick_timer = 0
            elif event.type == helper.EVENT_DOUBLECLICK:
                # timer timed out
                full_screen_plugin.handle_click(pygame.mouse.get_pos())
                pygame.time.set_timer(helper.EVENT_DOUBLECLICK, 0)
                doubleclick_timer = 0
            elif event.type == helper.EVENT_MESSAGE:
                message = event.message[0]
                if len(event.message) == 1:
                    opacity = 255 + (message_step * fps * appconfig.getint("message_popup_fade_delay"))
                else:
                    opacity = event.message[1]

                if opacity > 0:
                    opacity -= message_step

                    surf_message_text = message_font.render(event.message[0], True, (200, 200, 200))
                    surf_message = pygame.Surface((surf_message_text.get_width() + 40,  # margin
                                                   surf_message_text.get_height() + 40))
                    surf_message.fill((32, 32, 32))
                    surf_message.blit(surf_message_text, (surf_message.get_width()/2 - surf_message_text.get_width()/2,
                                                          surf_message.get_height()/2 -
                                                          surf_message_text.get_height()/2))
                    pygame.draw.rect(surf_message, (200, 200, 200),
                                     (0, 0, surf_message.get_width(), surf_message.get_height()), 3)

                    if opacity > 255:
                        surf_message.set_alpha(255)
                    else:
                        surf_message.set_alpha(opacity)

                    canvas.blit(surf_message, (canvas.get_width()/2 - surf_message.get_width()/2,
                                               canvas.get_height() - surf_message.get_height() - 50))  # bottom margin

                    my_event = pygame.event.Event(helper.EVENT_MESSAGE, message=[message, opacity])
                    pygame.event.post(my_event)

        if update:
            pygame.display.flip()

        if time.time() - start_time > full_screen_plugins[current_plugin]["autoswitch_timer"]:
            # Switch plugins
            if appconfig.getboolean("take_screenshots"):
                screenshot_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  appconfig["screenshot_dir"],
                                                  "screenshot_{}.png".format(datetime.datetime.now().timestamp())))
                pygame.image.save(canvas, screenshot_file)
                helper.log(debug, "Saved screenshot to {}".format(screenshot_file))

            current_plugin, tick, full_screen_plugin, start_time = switch_plugin(current_plugin, full_screen_plugins,
                                                                                 canvas, full_screen_canvas_small)
    pygame.quit()
    sys.exit()


def switch_plugin(current_plugin, full_screen_plugins, canvas, canvas_small):
    current_plugin += 1
    if current_plugin == len(full_screen_plugins):
        current_plugin = 0

    plugin_config_name = full_screen_plugins[current_plugin]["internal_name"]
    if plugin_config_name.getboolean("show_widgets"):
        full_screen_plugin = full_screen_plugins[current_plugin]["class"](helper, canvas_small,
                                                                          plugin_config_name)
    else:
        full_screen_plugin = full_screen_plugins[current_plugin]["class"](helper, canvas,
                                                                          plugin_config_name)

    tick = 0
    start_time = time.time()
    pygame.display.flip()
    return current_plugin, tick, full_screen_plugin, start_time


def get_plugins(debug):
    plugins = []
    plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "plugins"))
    helper.log(debug, "Plugin path: {}".format(plugin_path))
    plugin_folders = os.listdir(plugin_path)
    for folder in plugin_folders:
        full_path = os.path.join(plugin_path, folder)
        if os.path.isdir(full_path):
            files = os.listdir(full_path)
            for file in files:
                if file[-3:] == ".py":
                    module = importlib.import_module("." + file[:-3], "plugins.{}".format(folder))
                    for name, obj in inspect.getmembers(module):
                        if (type(obj) == type or type(obj) == Singleton) and issubclass(obj, Plugin) and obj.__module__[:8] == "plugins.":
                            # Get the config
                            helper.log(debug, "Found plugin {}".format(obj.__name__))
                            plugins.append({"class_name": obj.__name__, "class": obj})#, "config": plugin_config})
    return plugins


if __name__ == '__main__':
    main()
