"""
Now Playing (Ticker)
(c) Steven Babineau - babineau@gmail.com
2022
"""
from __future__ import print_function

import datetime
import hashlib
import threading
import time

import pygame
import os

from pygame.sprite import DirtySprite
from spotipy import SpotifyPKCE, Spotify, CacheFileHandler

from lib.widget_plugin import WidgetPlugin


class NowPlayingTicker(DirtySprite, WidgetPlugin):
    """ Clok """
    def __init__(self, helper, canvas, app_plugin_config):
        DirtySprite.__init__(self)
        WidgetPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.scope = "user-read-playback-state,user-modify-playback-state"
        self.redirect_uri = "http://localhost:8888"
        self.icons_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.plugin_config["icons_folder"]))

        self.now_playing = {}
        self.now_playing_updated = False
        self.timer = -1
        self.now_playing_surface = None
        self.pos_x = 0
        self.ticker_buffer = 40
        self.border_brighten_amount = 32

        font_size = 1
        self.ticker_border_size = 1
        self.margin_y = 2
        self.margin_x = 6
        self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], font_size)
        while self.font.size("XXXX")[1] + (self.ticker_border_size+self.margin_y)*2 < self.screen_height:
            font_size += 1
            self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], font_size)

        font_size -= 1
        self.font = pygame.font.SysFont(self.plugin_config["default_font_face"], font_size)

        self.helper.log(self.debug, "Found a font size of {}".format(font_size))

        icon_size = (self.font.get_height(), self.font.get_height())

        self.icon = self.plugin_config["icon"]
        self.client_id = self.plugin_config["client_id"]
        self.username = self.plugin_config["username"]
        self.update_interval = self.plugin_config.getint("update_interval")
        self.speed = self.plugin_config.getint("speed")
        self.provider = self.plugin_config["provider"]
        self.icon_notplaying = self.plugin_config["icon_notplaying"]
        self.background = eval(self.plugin_config["background"])
        self.foreground = eval(self.plugin_config["foreground"])
        self.foreground_notplaying = eval(self.plugin_config["foreground_notplaying"])

        self.surf_icon_playing = pygame.image.load(os.path.join(self.icons_folder, self.icon), ).convert_alpha()
        self.surf_icon_notplaying = pygame.image.load(os.path.join(self.icons_folder, self.icon_notplaying), ).convert_alpha()

        self.surf_icon_playing = pygame.transform.scale(self.surf_icon_playing, icon_size)
        self.surf_icon_notplaying = pygame.transform.scale(self.surf_icon_notplaying, icon_size)

    def update(self, tick, fps):
        if int(time.time() * 1000) - self.timer > self.update_interval * 1000:
            self.download_now_playing_info()
            self.timer = int(time.time() * 1000)

        if self.now_playing_updated:
            self.update_now_playing_surface()
            self.now_playing_updated = False

        self.canvas.fill(self.background)

        if self.now_playing_surface is not None:
            width = self.now_playing_surface.get_width()

            if self.speed > 0:
                if self.pos_x <= width*-1:
                    self.pos_x = -width - self.pos_x
            elif self.speed < 0:
                if self.pos_x > width or self.pos_x == 0:
                    self.pos_x = -width

            x = self.pos_x
            while x < self.screen_width + width:
                self.canvas.blit(self.now_playing_surface, (x, 0))
                x += self.now_playing_surface.get_width()

            self.pos_x -= self.speed

    def update_now_playing_surface(self):
        playing = True
        if len(self.now_playing) > 0:
            header = "Now Playing"
            if not self.now_playing["is_playing"]:
                header += " (paused)"
                playing = False
                fg_color = self.foreground_notplaying
            else:
                fg_color = self.foreground

            header += ": "

            track_title = self.now_playing["item"]["name"]
            if self.now_playing["item"]["type"] == "track":
                album_title = self.now_playing["item"]["album"]["name"]
                artists = ""
                i = 0
                for j in self.now_playing["item"]["artists"]:
                    if i > 0:
                        artists += " + "
                    artists += j["name"]
                    i += 1
            else:
                # It's an episode
                album_title = ""
                artists = self.now_playing["item"]["show"]["name"]

            if len(album_title) > 0:
                now_playing_text_surface = self.font.render("{}{} - {} ({})".format(header, track_title, artists, album_title),
                                                            True,
                                                            fg_color)
            else:
                now_playing_text_surface = self.font.render("{}{} - {}".format(header, track_title, artists),
                                                            True,
                                                            fg_color)

        else:
            now_playing_text_surface = self.font.render("Now Playing: Nothing!",
                                                        True,
                                                        self.foreground_notplaying)
            playing = False

        if playing:
            surf_icon = self.surf_icon_playing
        else:
            surf_icon = self.surf_icon_notplaying

        self.now_playing_surface = pygame.Surface((self.ticker_buffer + surf_icon.get_width() + self.margin_x +
                                                   now_playing_text_surface.get_width(), self.screen_height))
        bg_color = self.background
        self.now_playing_surface.fill(bg_color)

        bg_r = bg_color[0] + self.border_brighten_amount
        if bg_r > 255:
            bg_r = 255
        bg_g = bg_color[1] + self.border_brighten_amount
        if bg_g > 255:
            bg_g = 255
        bg_b = bg_color[1] + self.border_brighten_amount
        if bg_b > 255:
            bg_b = 255

        pygame.draw.rect(self.now_playing_surface, (bg_r, bg_g, bg_b),
                         (0, 0, self.now_playing_surface.get_width(), self.now_playing_surface.get_height()),
                         self.ticker_border_size)

        self.now_playing_surface.blit(surf_icon, (self.ticker_buffer/2, self.now_playing_surface.get_height()/2 - surf_icon.get_height()/2))

        self.now_playing_surface.blit(now_playing_text_surface,
                                      (self.ticker_buffer/2 + self.margin_x + surf_icon.get_width(),
                                       self.now_playing_surface.get_height() / 2 - now_playing_text_surface.get_height() / 2))

    def download_now_playing_info(self):
        thread_timer = threading.Thread(target=self.get_now_playing_info, args=([]))
        thread_timer.daemon = False
        thread_timer.start()

    def get_now_playing_info(self):
        state = hashlib.sha256()
        state.update(str.encode(str(datetime.datetime.now().timestamp() * 1000)))
        state = state.hexdigest()

        client_id = self.client_id
        username = self.username
        scope = self.scope
        redirect_uri = self.redirect_uri

        handler = CacheFileHandler(cache_path=os.path.join(os.getcwd(), ".cache-{}".format(username)), username=username)
        credential_manager = SpotifyPKCE(scope=scope, open_browser=False, client_id=client_id,
                                         state=state, redirect_uri=redirect_uri, cache_handler=handler)
        sp = Spotify(client_credentials_manager=credential_manager)

        results = sp.current_playback(additional_types="track,episode")
        if results is None:
            results = {}

        lock = threading.Lock()
        lock.acquire()
        self.now_playing = results
        self.now_playing_updated = True
        self.helper.log(self.debug, "Done getting Now Playing")
        lock.release()
