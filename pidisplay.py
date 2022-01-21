"""
PI Display
(c) Steven Babineau - babineau@gmail.com
2022
"""
from __future__ import print_function

import sys
import os
import time
import importlib
import datetime
import pygame

import config as c
import helper


def main():
    """ Main is what Main is """
    pygame.init()
    pygame.display.set_caption('PiDisplay')
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

    clock = pygame.time.Clock()
    config = c.CONFIG

    if pygame.version.vernum[0] == 2:
        helper.log(config, "Running with pygame 2.X options.")
        flags = 0
    else:
        helper.log(config, "Running with pygame 1.X options.")
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF

    if config["fullscreen_mode"]:
        flags |= pygame.FULLSCREEN
        if config["fullscreen_uses_current_resolution"]:
            config["screen_width"] = 0
            config["screen_height"] = 0

    if pygame.version.vernum[0] == 2:
        pygame.display.set_mode([config["screen_width"], config["screen_height"]], flags, vsync=1)
    else:
        pygame.display.set_mode([config["screen_width"], config["screen_height"]], flags)

    canvas = pygame.display.get_surface()

    pygame.mouse.set_pos((canvas.get_width()/2, canvas.get_height()/2))
    pygame.mouse.set_visible(False)

    plugin_modules = get_plugins(config)
    helper.log(config, "Total modules found: {}".format(len(plugin_modules)))
    plugins = []
    for i in plugin_modules:
        plugin = load_plugin(i, config)
        if plugin.is_enabled():
            plugins.append(plugin)
            helper.log(config, "Done loading {} ({}) {}".format(i, plugins[-1].get_name(), len(plugins)))

    current_plugin = -1

    for i in range(len(plugins)):
        helper.log(config, "{} = {}".format(plugins[i].get_name(), config['start_plugin']))
        if plugins[i].get_type() == helper.FULL_SCREEN:
            if len(config["start_plugin"]) == 0:
                current_plugin = i
                break
            elif config["start_plugin"] == plugins[i].get_name():
                current_plugin = i
                break

    if current_plugin < 0:
        raise Exception("No full screen plugins or start_plugins set incorrectly! {}".format(len(plugins)))

    running = True
    update = True
    tick = 0
    fps = config["frames_per_second"]
    if config["autoswitch_timer"] <= 0:
        config["autoswitch_timer"] = sys.maxsize
    start_time = time.time()

    widget_plugins = []
    top_bar_canvas = None
    bottom_bar_canvas = None

    for i in range(len(plugins)):
        if plugins[i].get_type() == helper.WIDGET:
            if plugins[i].get_location() == helper.WIDGET_LOCATION_TOP:
                if top_bar_canvas is None:
                    top_bar_canvas = canvas.subsurface(
                        pygame.Rect(0, 0, canvas.get_width(), c.CONFIG["top_bar_height"]))
                widget_plugins.append({"location": plugins[i].get_location(),
                                       "instance": plugins[i].get_instance(config, top_bar_canvas)})
            elif plugins[i].get_location() == helper.WIDGET_LOCATION_BOTTOM:
                if bottom_bar_canvas is None:
                    bottom_bar_canvas = canvas.subsurface(
                        pygame.Rect(0, canvas.get_height() - c.CONFIG["bottom_bar_height"],
                                    canvas.get_width(), c.CONFIG["bottom_bar_height"]))
                widget_plugins.append({"location": plugins[i].get_location(),
                                       "instance": plugins[i].get_instance(config, bottom_bar_canvas)})

    top_offset = top_bar_canvas.get_height() if top_bar_canvas is not None else 0
    bottom_offset = bottom_bar_canvas.get_height() if bottom_bar_canvas is not None else 0

    full_screen_rect = pygame.Rect(0, top_offset, canvas.get_width(), canvas.get_height() - top_offset - bottom_offset)
    full_screen_canvas = canvas.subsurface(full_screen_rect)
    full_screen_plugin = plugins[current_plugin].get_instance(config, full_screen_canvas, full_screen_rect)

    doubleclick_timer = 0

    message_font = pygame.font.SysFont(config["application_sysfont"], config["message_font_size"])
    message_step = 255.0 / (config["frames_per_second"] * config["message_popup_fade_time"])

    while running:
        clock.tick(fps)

        if update:
            full_screen_plugin.update(tick, full_screen_canvas)

            for i in widget_plugins:
                if i["location"] == helper.WIDGET_LOCATION_TOP:
                    i["instance"].update(tick, top_bar_canvas)
                elif i["location"] == helper.WIDGET_LOCATION_BOTTOM:
                    i["instance"].update(tick, bottom_bar_canvas)

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
                    pygame.time.set_timer(helper.EVENT_DOUBLECLICK, config["doubleclick_delay"])
                    timer_set = True
                else:
                    if doubleclick_timer == 1:
                        pygame.time.set_timer(helper.EVENT_DOUBLECLICK, 0)
                        # Switch plugins
                        current_plugin, tick, full_screen_plugin, start_time = switch_plugin(current_plugin, plugins,
                                                                                             full_screen_canvas, config,
                                                                                             full_screen_rect)
                        timer_set = False
                if timer_set:
                    doubleclick_timer = 1
                else:
                    doubleclick_timer = 0
            elif event.type == helper.EVENT_DOUBLECLICK:
                # timer timed out
                plugins[current_plugin].handle_click(pygame.mouse.get_pos())
                print("mouse x,y: {},{}".format(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]))
                pygame.time.set_timer(helper.EVENT_DOUBLECLICK, 0)
                doubleclick_timer = 0
            elif event.type == helper.EVENT_MESSAGE:

                message = event.message[0]
                if len(event.message) == 1:
                    opacity = 255 + (message_step * config["frames_per_second"] * config["message_popup_fade_delay"])
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

        if time.time() - start_time > config["autoswitch_timer"]:
            # Switch plugins
            if config["take_screenshots"]:
                screenshot_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                               config["screenshot_dir"],
                                                               "screenshot_{}.png".format(datetime.datetime.now().timestamp())))
                pygame.image.save(canvas, screenshot_file)
                helper.log(config, "Saved screenshot to {}".format(screenshot_file))

            current_plugin, tick, full_screen_plugin, start_time = switch_plugin(current_plugin, plugins,
                                                                                 full_screen_canvas, config,
                                                                                 full_screen_rect)
    pygame.quit()
    sys.exit()


def switch_plugin(current_plugin, plugins, canvas, config, full_screen_rect):
    plugin_type = ""
    while plugin_type != helper.FULL_SCREEN:
        current_plugin += 1
        if current_plugin >= len(plugins):
            current_plugin = 0
        plugin_type = plugins[current_plugin].get_type()
    full_screen_plugin = plugins[current_plugin].get_instance(config, canvas, full_screen_rect)

    tick = 0
    start_time = time.time()
    pygame.display.flip()
    return current_plugin, tick, full_screen_plugin, start_time


def get_plugins(config):
    plugins = []
    plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), config["plugins_folder"]))
    helper.log(config, "Plugin path: {}".format(plugin_path))
    plugin_folders = os.listdir(plugin_path)
    for folder in plugin_folders:
        full_path = os.path.join(plugin_path, folder)
        helper.log(config, "Full plugin path: {}".format(full_path))

        if os.path.isdir(full_path) and "__init__.py" in os.listdir(full_path):
            plugins.append(folder)
            helper.log(config, "Reading plugin {}".format(folder))
        
    return plugins


def load_plugin(plugin_name, config):
    helper.log(config, "Loading plugin: {}".format(plugin_name))
    return importlib.import_module("." + plugin_name, "plugins")


if __name__ == '__main__':
    main()
