"""
OpenWeatherMap Forecast
(c) Steven Babineau - babineau@gmail.com
2022
"""
import json
import os
import datetime
import time
import pygame
import threading
import feedparser
import requests

class NewsFeed:
    def __init__(self, config, helper, canvas, screen_rect):
        self.config = config
        self.helper = helper
        self.screen_width = canvas.get_width()
        self.screen_height = canvas.get_height()
        self.screen_rect = screen_rect

        self.timer = -1
        self.news = None
        self.news_updated = False
        self.last_canvas = None
        self.feed_title_font = pygame.font.SysFont(self.config["application_sysfont"],
                                                   self.config["feed_title_font_size"])
        self.item_title_font = pygame.font.SysFont(self.config["application_sysfont"],
                                                   self.config["item_title_font_size"])
        self.item_date_font = pygame.font.SysFont(self.config["application_sysfont"],
                                                  self.config["item_date_font_size"])
        self.item_desc_font = pygame.font.SysFont(self.config["application_sysfont"],
                                                  self.config["item_desc_font_size"])
        self.icons_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.config["icons_folder"]))

        self.item_boxes = []

    def update(self, tick, canvas):
        if int(time.time() * 1000) - self.timer > self.config["update_interval"] * 1000 * 60:
            self.update_news()
            self.timer = int(time.time() * 1000)

        if self.news_updated:
            # Create the news surfaces
            if self.news is not None:
                canvas.fill(self.config["background"])

                _line_buffer = 3
                _entry_buffer = 6
                y = self.config["screen_margin"]
                print("Updating {} item surfaces".format(len(self.news)))
                _line_color = pygame.Vector3(self.config["foreground"])
                _line_color = _line_color.lerp(self.config["background"], .4)
                num_items = 0
                self.item_boxes = []
                for i in self.news:
                    item_date = get_time_delta_string(datetime.datetime.fromtimestamp(i["item_date"]))

                    surf_item_title = self.item_title_font.render(i["title"], True,
                                                                  self.config["item_title_foreground"])
                    surf_item_date = self.item_date_font.render(item_date, True, self.config["item_date_foreground"])

                    surf_item = pygame.Surface((canvas.get_width() - self.config["screen_margin"] * 2,
                                                surf_item_title.get_height() + surf_item_date.get_height() +
                                                _line_buffer))

                    try:
                        surf_icon = pygame.image.load(os.path.join(self.icons_folder, i["icon"])).convert()
                        ratio = self.config["icon_size"] * 1.0 / surf_icon.get_width()
                        icon_height = int(surf_icon.get_height() * ratio)
                        surf_icon = pygame.transform.scale(surf_icon, (int((surf_icon.get_width() * 1.0) * ratio),
                                                                       icon_height))
                    except FileNotFoundError:
                        surf_icon = pygame.Surface((self.config["icon_size"], self.config["icon_size"]))
                        surf_icon.fill(self.config["background"])

                    surf_item.blit(surf_icon, (0, surf_item.get_height()/2 - surf_icon.get_height()/2))

                    y1 = 0
                    x = surf_icon.get_width() + 10
                    surf_item.blit(surf_item_date, (x, y1))
                    y1 += surf_item_date.get_height() + _line_buffer
                    surf_item.blit(surf_item_title, (x, y1))

                    # line_y = surf_item.get_height()-_line_buffer/2
                    # pygame.draw.line(surf_item, _line_color, (self.config["screen_margin"]*30, line_y),
                    #                 (self.canvas.get_width()-self.config["screen_margin"]*30, line_y))

                    if y + surf_item.get_height() + _entry_buffer > canvas.get_height():
                        print("{} > {}...breaking display loop after {} items!"
                              .format(y + surf_item.get_height() + _entry_buffer, canvas.get_height(), num_items))
                        break

                    canvas.blit(surf_item, (self.config["screen_margin"], y))

                    pos_rect = [
                        self.screen_rect.left + self.config["screen_margin"],
                        self.screen_rect.top + y,
                        surf_item.get_width(),
                        surf_item.get_height()
                    ]

                    self.item_boxes.append({"pos": pos_rect, "link": i["link"], "title": i["title"]})

                    y += surf_item.get_height() + _entry_buffer
                    num_items += 1

                self.last_canvas = canvas.copy()
            self.news_updated = False
        else:
            if self.last_canvas is not None:
                canvas.blit(self.last_canvas, (0, 0))
            else:
                surf_error = self.item_title_font.render("Retrieving news...", True, self.config["foreground"])

                canvas.fill(self.config["background"])
                canvas.blit(surf_error, (canvas.get_width()/2 - surf_error.get_width()/2,
                                         canvas.get_height()/2 - surf_error.get_height()/2))

        return canvas

    def handle_click(self, pos):
        for i in self.item_boxes:
            if pygame.Rect(i["pos"]).collidepoint(pos[0], pos[1]):
                if len(self.config["slack_webhook"]) > 0:
                    self.helper.log(self.config, "Sending {} to Slack webhook.".format(i["link"]))
                    headers = {'Content-type': 'application/json'}
                    data = {"text": i["link"]}
                    data = json.dumps(data)
                    r = requests.post(self.config["slack_webhook"], data=data, headers=headers)
                    self.helper.log(self.config, "Response was: {}".format(r))
                    self.helper.send_message("URL sent!")
                break
        pass

    def update_news(self):
        thread_timer = threading.Thread(target=self.update_news_thread, args=([]))
        thread_timer.daemon = False
        thread_timer.start()

    def update_news_thread(self):
        lock = threading.Lock()
        lock.acquire()

        news = {}
        for i in self.config["feeds"]:
            feed = feedparser.parse(i["url"])

            for item in feed.entries:
                desc = item.description if "description" in item else ""
                title = item.title if "title" in item else ""
                item_date = int(time.mktime(item.published_parsed)) if "published_parsed" in item else 0
                link = item.links[0].href if "links" in item and len(item.links) > 0 and "href" in item.links[0] else ""
                news.update({item_date:
                            {
                                "feed_title": i["name"], "description": desc, "title": title, "item_date": item_date,
                                "icon": i["icon"], "link": link
                             }})

        dates = sorted(news.keys(), reverse=True)

        result = []
        for i in dates:
            result.append(news[i])

        self.news = result
        self.news_updated = True
        self.helper.log(self.config, "done getting feeds!")

        lock.release()


def get_time_delta_string(start):
    result = ""
    now = datetime.datetime.utcnow()
    delta = now - start

    days = delta.days
    hours = int(delta.seconds / 60 / 60)
    minutes = int((delta.seconds / 60) - (hours * 60))
    seconds = int(delta.seconds - (hours * 60 * 60) - (minutes * 60))

    if days > 0:
        result += "{} day".format(days)
        if days > 1:
            result += "s"
    if hours > 0:
        if len(result) > 0:
            result += ", "

        result += "{} hour".format(hours)
        if hours > 1:
            result += "s"
    if minutes > 0:
        if len(result) > 0:
            result += ", "

        result += "{} minute".format(minutes)
        if minutes > 1:
            result += "s"
    if seconds > 0:
        if len(result) > 0:
            result += ", "

        result += "{} second".format(seconds)
        if seconds > 1:
            result += "s"

    result += " ago"
    return result
