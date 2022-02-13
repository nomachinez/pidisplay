"""
Newsfeed
(c) Steven Babineau - babineau@gmail.com
2022
"""
import json
import os
from datetime import datetime
import time
import pygame
import threading
import feedparser
import requests

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class NewsFeed(FullScreenPlugin, metaclass=Singleton):
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.timer = -1
        self.news = None
        self.news_updated = False
        self.last_canvas = None
        self.feed_title_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("feed_title_font_size"))
        self.item_title_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("item_title_font_size"))
        self.item_date_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("item_date_font_size"))
        self.item_desc_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("item_desc_font_size"))
        self.icons_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.plugin_config["icons_folder"]))

        self.background = eval(self.plugin_config["background"])
        self.foreground = eval(self.plugin_config["foreground"])
        self.feed_title_foreground = eval(self.plugin_config["feed_title_foreground"])
        self.item_title_foreground = eval(self.plugin_config["item_title_foreground"])
        self.item_date_foreground = eval(self.plugin_config["item_date_foreground"])
        self.item_desc_foreground = eval(self.plugin_config["item_desc_foreground"])
        self.screen_margin = self.plugin_config.getint("screen_margin")
        self.icon_size = self.plugin_config.getint("icon_size")
        self.update_interval = self.plugin_config.getint("update_interval")
        self.slack_webhook = self.plugin_config["slack_webhook"]

        self.item_boxes = []

    def update(self, tick, fps):
        if int(time.time() * 1000) - self.timer > self.update_interval * 1000 * 60:
            self.update_news()
            self.timer = int(time.time() * 1000)

        if self.news_updated:
            # Create the news surfaces
            if self.news is not None:
                self.canvas.fill(self.background)

                _line_buffer = 3
                _entry_buffer = 6
                y = self.screen_margin
                self.helper.log(self.debug, "Updating {} item surfaces".format(len(self.news)))
                _line_color = pygame.Vector3(self.foreground)
                _line_color = _line_color.lerp(self.background, .4)
                num_items = 0
                self.item_boxes = []
                for i in self.news:
                    item_date = self.helper.get_time_delta_string(datetime.utcnow(), datetime.fromtimestamp(i["item_date"]))

                    surf_item_title = self.item_title_font.render(i["title"], True, self.item_title_foreground)
                    surf_item_date = self.item_date_font.render(item_date, True, self.item_date_foreground)

                    surf_item = pygame.Surface((self.canvas.get_width() - self.screen_margin * 2,
                                                surf_item_title.get_height() + surf_item_date.get_height() +
                                                _line_buffer))

                    try:
                        surf_icon = pygame.image.load(os.path.join(self.icons_folder, i["icon"])).convert()
                        ratio = self.icon_size * 1.0 / surf_icon.get_width()
                        icon_height = int(surf_icon.get_height() * ratio)
                        surf_icon = pygame.transform.scale(surf_icon, (int((surf_icon.get_width() * 1.0) * ratio),
                                                                       icon_height))
                    except FileNotFoundError:
                        surf_icon = pygame.Surface((self.icon_size, self.icon_size))
                        surf_icon.fill(self.background)

                    surf_item.blit(surf_icon, (0, surf_item.get_height()/2 - surf_icon.get_height()/2))

                    y1 = 0
                    x = surf_icon.get_width() + 10
                    surf_item.blit(surf_item_date, (x, y1))
                    y1 += surf_item_date.get_height() + _line_buffer
                    surf_item.blit(surf_item_title, (x, y1))

                    if y + surf_item.get_height() + _entry_buffer > self.canvas.get_height():
                        self.helper.log(self.debug, "{} > {}...breaking display loop after {} items!"
                                        .format(y + surf_item.get_height() + _entry_buffer,
                                                self.canvas.get_height(), num_items))
                        break

                    self.canvas.blit(surf_item, (self.screen_margin, y))

                    pos_rect = [
                        self.screen_margin,
                        y,
                        surf_item.get_width(),
                        surf_item.get_height()
                    ]

                    self.item_boxes.append({"pos": pos_rect, "link": i["link"], "title": i["title"]})

                    y += surf_item.get_height() + _entry_buffer
                    num_items += 1

                self.last_canvas = self.canvas.copy()
            self.news_updated = False
        else:
            if self.last_canvas is not None:
                self.canvas.blit(self.last_canvas, (0, 0))
            else:
                surf_error = self.item_title_font.render("Retrieving news...", True, self.foreground)

                self.canvas.fill(self.background)
                self.canvas.blit(surf_error, (self.canvas.get_width()/2 - surf_error.get_width()/2,
                                              self.canvas.get_height()/2 - surf_error.get_height()/2))

    def handle_click(self, pos):
        for i in self.item_boxes:
            if pygame.Rect(i["pos"]).collidepoint(pos[0], pos[1]):
                if len(self.slack_webhook) > 0:
                    self.helper.log(self.debug, "Sending {} to Slack webhook.".format(i["link"]))
                    headers = {'Content-type': 'application/json'}
                    data = {"text": i["link"]}
                    data = json.dumps(data)
                    r = requests.post(self.slack_webhook, data=data, headers=headers)
                    self.helper.log(self.debug, "Response was: {}".format(r))
                    self.helper.send_message("URL sent!")
                break
        pass

    def update_news(self):
        thread_timer = threading.Thread(target=self.update_news_thread, args=([]))
        thread_timer.daemon = False
        thread_timer.start()

    def update_news_thread(self):

        news = {}
        i = 1
        for param in list(self.plugin_config):
            if param[:4] == "feed":
                if "feed{}_name".format(i) in self.plugin_config:
                    name = self.plugin_config["feed{}_name".format(i)]
                    url = self.plugin_config["feed{}_url".format(i)]
                    icon = self.plugin_config["feed{}_icon".format(i)]
                    feed = feedparser.parse(url)

                    for item in feed.entries:
                        desc = item.description if "description" in item else ""
                        title = item.title if "title" in item else ""
                        item_date = int(time.mktime(item.published_parsed)) if "published_parsed" in item else 0
                        link = item.links[0].href if "links" in item and len(item.links) > 0 and "href" in item.links[0] else ""
                        news.update({item_date:
                                    {
                                        "feed_title": name, "description": desc, "title": title, "item_date": item_date,
                                        "icon": icon, "link": link
                                     }})
                    i += 1

        dates = sorted(news.keys(), reverse=True)

        result = []
        for i in dates:
            result.append(news[i])

        lock = threading.Lock()
        lock.acquire()

        self.news = result
        self.news_updated = True
        self.helper.log(self.debug, "done getting feeds!")

        lock.release()
