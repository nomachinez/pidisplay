"""
Ticker
(c) Steven Babineau - babineau@gmail.com
2022
"""
import os

import pygame
import yfinance
import requests
import time
import threading
import locale

from pygame.sprite import DirtySprite

from lib.widget_plugin import WidgetPlugin


class Ticker(DirtySprite, WidgetPlugin):
    """ Ticker """
    def __init__(self, helper, canvas, app_plugin_config):
        DirtySprite.__init__(self)
        WidgetPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.tickers_info = {}
        self.ticker_surfaces = []
        self.timer = -1
        self.tickers_updated = False

        self.pos_x = 0
        self.ticker_buffer = 40

        print("Ticker: {} x {}".format(self.screen_width, self.screen_height))

        font_size = 1
        self.ticker_border_size = 1
        margin = 2
        self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], font_size)
        while self.font.size("XXXX")[1] + (self.ticker_border_size+margin)*2 < self.screen_height:
            font_size += 1
            self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], font_size)

        font_size -= 1
        self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], font_size)

        print("set font size to {}".format(font_size))

        self.helper.log(self.debug, "Found a font size of {}".format(font_size))
        self.border_brighten_amount = 32

        self.background = eval(self.plugin_config["background"])
        self.foreground = eval(self.plugin_config["foreground"])
        self.down_background = eval(self.plugin_config["down_background"])
        self.down_foreground = eval(self.plugin_config["down_foreground"])
        self.up_background = eval(self.plugin_config["up_background"])
        self.up_foreground = eval(self.plugin_config["up_foreground"])
        self.speed = self.plugin_config.getint("speed")
        self.update_interval = self.plugin_config.getint("update_interval")
        self.tickers = eval(self.plugin_config["tickers"])

    def download_tickers(self):
        for i in self.tickers:
            self.download_ticker(i)

    def update_ticker_surfaces(self):
        self.ticker_surfaces = []
        locale.setlocale(locale.LC_ALL, "")

        for i in self.tickers_info:
            if len(i) > 0 and ("currentPrice" in self.tickers_info[i] or "regularMarketPrice" in self.tickers_info[i]):
                current_price = self.tickers_info[i]["currentPrice"] \
                    if "currentPrice" in self.tickers_info[i] else self.tickers_info[i]["regularMarketPrice"]

                self.helper.log(self.debug, "Current price: {} Open Price {}".format(current_price, self.tickers_info[i]["open"]))

                if current_price < self.tickers_info[i]["open"]:
                    fg_color = self.down_foreground
                    bg_color = self.down_background
                elif current_price > self.tickers_info[i]["open"]:
                    fg_color = self.up_foreground
                    bg_color = self.up_background
                else:
                    fg_color = self.foreground
                    bg_color = self.background

                try:
                    current_price = float(current_price)
                except ValueError:
                    current_price = -1.0

                surf_ticker_text = self.font.render("{} {:.2f}".format(self.tickers_info[i]["symbol"], float(current_price)), True, fg_color)
                surf_ticker = pygame.Surface((self.ticker_buffer + surf_ticker_text.get_width(), self.screen_height))

                surf_ticker.fill(bg_color)

                r = bg_color[0] + self.border_brighten_amount
                if r > 255:
                    r = 255
                g = bg_color[1] + self.border_brighten_amount
                if g > 255:
                    g = 255
                b = bg_color[1] + self.border_brighten_amount
                if b > 255:
                    b = 255

                pygame.draw.rect(surf_ticker, (r, g, b),
                                 (0, 0, surf_ticker.get_width(), surf_ticker.get_height()),
                                 self.ticker_border_size)

                surf_ticker.blit(surf_ticker_text, (surf_ticker.get_width()/2 - surf_ticker_text.get_width()/2,
                                                    surf_ticker.get_height()/2 - surf_ticker_text.get_height()/2))

                self.ticker_surfaces.append(surf_ticker)

    def update(self, tick, fps):
        if int(time.time() * 1000) - self.timer > self.update_interval * 1000 * 60:
            self.download_tickers()
            self.timer = int(time.time() * 1000)

        if self.tickers_updated:
            self.update_ticker_surfaces()
            self.tickers_updated = False

        self.canvas.fill(self.background)

        reset_width = 0
        for i in self.ticker_surfaces:
            reset_width += i.get_width()

        if self.speed > 0:
            if self.pos_x <= reset_width*-1:
                self.pos_x = -reset_width - self.pos_x
        elif self.speed < 0:
            if self.pos_x > reset_width or self.pos_x == 0:
                self.pos_x = -reset_width

        i = 0
        x = self.pos_x
        j = 0
        if len(self.ticker_surfaces) > 0:
            while x < self.screen_width + reset_width:
                self.canvas.blit(self.ticker_surfaces[i], (x, 0))
                x += self.ticker_surfaces[i].get_width()

                i += 1
                if i >= len(self.ticker_surfaces):
                    i = 0
                j += 1

        self.pos_x -= self.speed

    def download_ticker(self, ticker):
        thread_timer = threading.Thread(target=self.get_ticker_thread, args=([ticker]))
        thread_timer.daemon = False
        thread_timer.start()

    def get_ticker_thread(self, ticker):
        session = requests.Session()
        session.headers['User-agent'] = 'pidisplay/1.0'

        self.helper.log(self.debug, "getting ticker {}".format(ticker))
        results = {ticker: yfinance.Ticker(ticker, session=session).info}

        lock = threading.Lock()
        lock.acquire()
        self.tickers_info.update(results)
        self.tickers_updated = True
        self.helper.log(self.debug, "done getting ticker {}".format(ticker))
        lock.release()

