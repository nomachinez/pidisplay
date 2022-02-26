"""
Now Playing
(c) Steven Babineau - babineau@gmail.com
2022
"""
import datetime
import hashlib
import io
import os
import threading
import time
import pygame
import pygame.ftfont
import requests
from spotipy import SpotifyPKCE, Spotify, CacheFileHandler, oauth2
from PIL import Image, ImageFilter, ImageEnhance

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class NowPlaying(FullScreenPlugin, metaclass=Singleton):
    """ Now Playing """
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.scope = "user-read-playback-state,user-modify-playback-state"
        self.redirect_uri = "http://localhost:8888/callback"

        self.margin_x = 20
        self.text_margin_x = 5
        self.margin_y = 4
        self.max_lines = 2

        self.now_playing_updated = False

        self.track_info = None
        self.last_track_id = ""

        self.timer = -1
        self.image = pygame.Surface((self.screen_width, self.screen_height))

        self.title_font = pygame.ftfont.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("title_font_size"))
        self.info_font = pygame.ftfont.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("info_font_size"))

        self.background = None

        self.starting_x = 0
        self.starting_y = 0
        self.info_width = 0
        self.x_after_album = 0

        self.spotify_error = ""

        self.client_id = self.plugin_config["client_id"]
        self.username = self.plugin_config["username"]
        self.update_interval = self.plugin_config.getint("update_interval")
        self.provider = self.plugin_config["provider"]
        self.icon = self.plugin_config["icon"]
        self.icon_notplaying = self.plugin_config["icon_notplaying"]
        self.icons_folder = self.plugin_config["icons_folder"]
        self.progress_bar_height = self.plugin_config.getint("progress_bar_height")
        self.context_icon_width = self.plugin_config.getint("context_icon_width")
        self.screen_margin = self.plugin_config.getint("screen_margin")
        self.background_color = eval(self.plugin_config["background"])
        self.light_color = eval(self.plugin_config["light_color"])
        self.dark_color = eval(self.plugin_config["dark_color"])
        self.foreground_notplaying = eval(self.plugin_config["foreground_notplaying"])

        self.switch_next_plugin_when_nothing_is_playing = self.plugin_config.getboolean("switch_next_plugin_when_nothing_is_playing")
        
        tmp_width = self.screen_width / 3.0
        if self.screen_height < tmp_width + (self.screen_margin * 2):
            self.album_img_height = int(self.screen_height - (self.screen_margin * 2))
        else:
            self.album_img_height = int(tmp_width)

    def handle_click(self, pos):
        pass

    def update(self, tick, fps):
        if int(time.time() * 1000) - self.timer > self.update_interval * 1000:
            self.download_now_playing_info()
            self.timer = int(time.time() * 1000)

        if self.now_playing_updated:
            self.update_now_playing_surface()
            self.now_playing_updated = False

        if self.background is None:
            self.canvas.fill(self.background_color)
        else:
            self.canvas.blit(self.background, (0, 0))

        self.canvas.blit(self.image, (0, 0))

        # blit the progress bar
        if self.track_info is not None and self.track_info.id != "":
            surf_progress_bar = pygame.Surface((self.track_info.album_img.get_width() + self.margin_x + self.info_width, self.progress_bar_height))
            surf_progress_bar.fill(self.track_info.background_color)
            pygame.draw.rect(surf_progress_bar, self.track_info.foreground_color,
                             (0, 0, surf_progress_bar.get_width(), surf_progress_bar.get_height()), 1)

            if self.track_info.track_duration > 0:
                width = (self.track_info.track_position / self.track_info.track_duration) * surf_progress_bar.get_width()
                pygame.draw.rect(surf_progress_bar, self.track_info.foreground_color, (0, 0, width, surf_progress_bar.get_height()))

            self.image.blit(surf_progress_bar, (self.starting_x, self.starting_y + self.track_info.album_img.get_height() + self.margin_y))
        else:
            # Nothing is playing
            surf_message = self.title_font.render("Nothing is playing!", True, self.light_color)
            self.canvas.blit(surf_message, (self.canvas.get_width() / 2 - surf_message.get_width() / 2, self.canvas.get_height() / 2 - surf_message.get_height()/2))

        if self.spotify_error:
            surf_error1 = self.title_font.render("There was a problem connecting to Spotify ({}).".format(self.spotify_error), True, self.light_color)
            surf_error2 = self.title_font.render("Did you follow the instructions to set up the Spotify client?", True, self.light_color)
            self.canvas.blit(surf_error1, (self.canvas.get_width()/2 - surf_error1.get_width()/2, self.canvas.get_height()/2 - surf_error1.get_height()))
            self.canvas.blit(surf_error2, (self.canvas.get_width() / 2 - surf_error2.get_width() / 2, self.canvas.get_height() / 2))

    def update_now_playing_surface(self):
        if self.track_info is None:
            if self.switch_next_plugin_when_nothing_is_playing:
                self.READY_TO_SWITCH = True
                self.helper.log(self.debug, "Nothing is playing; switch away!")
            else:
                self.helper.log(self.debug, "Nothing is playing but we're not switching1!")
        else:
            if self.track_info.id == "":
                self.image.fill(self.background_color)
                surf_error_text = self.title_font.render("Nothing is playing!", True, self.foreground_notplaying)
                self.image.blit(surf_error_text, (self.image.get_width()/2 - surf_error_text.get_width()/2, self.image.get_height()/2 - surf_error_text.get_height()/2))
                if self.switch_next_plugin_when_nothing_is_playing:
                    self.READY_TO_SWITCH = True
                    self.helper.log(self.debug, "Nothing is playing; switch away!")
                else:
                    self.helper.log(self.debug, "Nothing is playing but we're not switching2!")
            else:
                self.helper.log(self.debug, "Track info is set! Building surfaces for {}".format(self.track_info.track_name))
                if self.track_info.background is not None:
                    self.image.blit(self.track_info.background, (0, 0))
                else:
                    self.image.fill(self.background_color)

                foreground = self.track_info.foreground_color

                self.starting_x = self.screen_margin + self.track_info.blur
                self.starting_y = self.screen_height / 2 - self.track_info.album_img.get_height() / 2
                self.info_width = self.screen_width - self.starting_x - self.track_info.album_img.get_width() - self.margin_x * 2
                self.x_after_album = self.starting_x + self.track_info.album_img.get_width() + self.margin_x

                # ARTIST
                artists = []
                for i in self.track_info.artists:
                    artists.append(i)

                lines = self.helper.wrap(", ".join(artists), self.title_font, self.info_width)
                surf_artists = []
                i = 1
                for line in lines:
                    surf_artists.append(self.title_font.render(line, True, foreground))
                    i += 1
                    if i > self.max_lines:
                        break

                surf_artist_title = self.info_font.render("Artist", True, foreground)

                # ALBUM
                lines = self.helper.wrap(self.track_info.album_name, self.title_font, self.info_width)
                surf_album_name = []
                i = 1
                for line in lines:
                    surf_album_name.append(self.title_font.render(line, True, foreground))
                    i += 1
                    if i > self.max_lines:
                        break
                surf_album_name_title = self.info_font.render("Album", True, foreground)

                # TRACK
                lines = self.helper.wrap(self.track_info.track_name, self.title_font, self.info_width)
                surf_track_name = []
                i = 1
                for line in lines:
                    surf_track_name.append(self.title_font.render(line, True, foreground))
                    i += 1
                    if i > self.max_lines:
                        break
                surf_track_name_title = self.info_font.render("Track", True, foreground)

                # STOP/PAUSE Button

                # CONTEXT - "artist", "playlist", "album", "show"
                if self.track_info.context_type == "artist":
                    context_text = u"Artist{} {}".format("s" if len(artists) > 1 else "", ", ".join(artists))
                elif self.track_info.context_type == "playlist":
                    context_text = u"Playlist {}".format(self.track_info.playlist_name)
                elif self.track_info.context_type == "album":
                    context_text = u"Album {}".format(self.track_info.album_name)
                elif self.track_info.context_type == "show":
                    context_text = u"Show {}".format(self.track_info.album_name)
                else:
                    context_text = u"Song {}".format(self.track_info.track_name)

                print("CONTEXT TEXT: {}".format(context_text))

                surf_context_text = self.info_font.render(context_text, True, foreground)

                if self.track_info.is_playing:
                    surf_device = self.info_font.render("Playing on device {}".format(self.track_info.device_name), True, foreground)
                else:
                    surf_device = self.info_font.render("Paused on device {}".format(self.track_info.device_name), True, foreground)

                # ------- BLIT TO NOW_PLAYING_SURFACE-----------
                # DEVICE
                self.image.blit(surf_device, (self.starting_x,
                                              self.starting_y + self.track_info.album_img.get_height() +
                                              + self.margin_y*3 + self.progress_bar_height))

                # CONTEXT
                if self.track_info.context_image is not None:
                    self.image.blit(self.track_info.context_image, (self.x_after_album + self.info_width - self.track_info.context_image.get_width(),
                                                                    self.starting_y - self.track_info.context_image.get_height() - self.margin_y))

                    self.image.blit(surf_context_text, (self.x_after_album + self.info_width - self.track_info.context_image.get_width() - self.margin_x - surf_context_text.get_width(),
                                                        self.starting_y - self.track_info.context_image.get_height() - self.margin_y + (self.track_info.context_image.get_height()/2 - surf_context_text.get_height()/2)))
                else:
                    self.image.blit(surf_context_text, (self.x_after_album + self.info_width - surf_context_text.get_width(),
                                                        self.starting_y - self.margin_y - surf_context_text.get_height()/2))

                # ALBUM
                album_y = self.starting_y
                one_third_album_height = self.track_info.album_img.get_height()/3.0

                # ALBUM IMAGE
                if self.track_info.is_playing:
                    self.image.blit(self.track_info.album_img, (self.starting_x, self.starting_y))
                else:
                    self.image.blit(self.track_info.album_img_paused, (self.starting_x, self.starting_y))

                # ALBUM NAME
                total_album_height = surf_album_name_title.get_height() + self.margin_y
                for surf_album in surf_album_name:
                    total_album_height += surf_album.get_height() + self.margin_y
                if len(surf_artists) > 0:
                    total_album_height -= self.margin_y

                album_name_y = album_y + (one_third_album_height*2) - one_third_album_height/2.0 - total_album_height/2

                y = 0
                for surf_album in surf_album_name:
                    self.image.blit(surf_album, (self.x_after_album, album_name_y + surf_artist_title.get_height() + self.margin_y + y))
                    y += surf_album.get_height() + self.margin_y

                self.image.blit(surf_album_name_title, (self.x_after_album, album_name_y))

                # ARTISTS
                total_artist_height = surf_artist_title.get_height() + self.margin_y
                for surf_artist in surf_artists:
                    total_artist_height += surf_artist.get_height() + self.margin_y
                if len(surf_artists) > 0:
                    total_artist_height -= self.margin_y

                artist_name_y = album_y + one_third_album_height/2.0 - total_artist_height/2

                y = 0
                for surf_artist in surf_artists:
                    self.image.blit(surf_artist, (self.x_after_album, artist_name_y + surf_artist_title.get_height() + self.margin_y + y))
                    y += surf_artist.get_height() + self.margin_y

                self.image.blit(surf_artist_title, (self.x_after_album, artist_name_y))

                # TRACK
                total_track_height = surf_track_name_title.get_height() + self.margin_y
                for surf_track in surf_track_name:
                    total_track_height += surf_track.get_height() + self.margin_y
                if len(surf_track_name) > 0:
                    total_track_height -= self.margin_y

                track_name_y = album_y + self.track_info.album_img.get_height() - one_third_album_height/2.0 - total_track_height/2

                y = 0
                for surf_track in surf_track_name:
                    self.image.blit(surf_track, (self.x_after_album, track_name_y + surf_track_name_title.get_height() + self.margin_y + y))
                    y += surf_track.get_height() + self.margin_y

                self.image.blit(surf_track_name_title, (self.x_after_album, track_name_y))

                # Dividers
                bar_length = self.track_info.album_img.get_width() - (self.margin_x*2)
                bar_start = self.x_after_album + (self.screen_width - self.x_after_album - self.screen_margin)/2 - bar_length/2

                pygame.draw.line(self.image, foreground, (bar_start, album_y + one_third_album_height-1),
                                                         (bar_start + bar_length, album_y + one_third_album_height-1))
                pygame.draw.line(self.image, foreground, (bar_start, album_y + (one_third_album_height*2)-1),
                                                         (bar_start + bar_length, album_y + (one_third_album_height*2)-1))

                self.last_track_id = self.track_info.id

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

        error = None
        results = None
        try:
            results = sp.current_playback(additional_types="track,episode")
        except oauth2.SpotifyOauthError as err:
            error = err.error

        if error:
            self.spotify_error = error
            return

        self.spotify_error = ""

        is_same_id = False
        lock = threading.Lock()
        lock.acquire()
        old_id = self.track_info.id if self.track_info is not None else ""
        new_id = ""
        if self.track_info is not None and results is not None and len(results) > 0 and "item" in results and results["item"] is not None and "id" in results["item"]:
            new_id = results["item"]["id"]
            self.helper.log(self.debug, "...new ID: {}".format(new_id))
            if self.track_info.is_same_track(new_id) and self.track_info.is_playing == results["is_playing"]:
                self.helper.log(self.debug, "IDs are the same... updating.")
                self.track_info.update(results)
                is_same_id = True
        lock.release()

        if is_same_id:
            return

        lock = threading.Lock()
        lock.acquire()
        self.helper.log(self.debug, "IDs are not the same ({} != {}).... refreshing".format(old_id, new_id))

        lock.release()

        if results is not None and len(results) > 0 and "item" in results and results["item"] is not None and "type" in results["item"]:
            if results["item"]["type"] == "track":
                track_item = TrackItem(self.plugin_config, self.helper, self.debug)
            elif results["item"]["type"] == "episode":
                track_item = EpisodeItem(self.plugin_config, self.helper, self.debug)
            else:
                self.helper.log(self.debug, "item")
                track_item = TrackItem(self.plugin_config, self.helper, self.debug)
        else:
            track_item = Item(self.plugin_config, self.helper, self.debug)

        if results is not None:
            track_item.parse(results, sp, self.screen_width, self.screen_height, self.album_img_height, self.plugin_config)

        track_item.fix_album_image_and_build_background(self.screen_width, self.screen_height, self.album_img_height, self.plugin_config)

        lock = threading.Lock()
        lock.acquire()
        self.now_playing_updated = True
        self.track_info = track_item
        self.helper.log(self.debug, "Done getting Now Playing")
        lock.release()


class Item:
    def __init__(self, plugin_config, helper, debug):
        self.id = ""
        self.context_type = ""
        self.context_image = None

        self.playlist_name = ""

        self.device_name = ""
        self.device_type = ""

        self.album_name = ""
        self.album_img = None
        self.album_img_paused = None

        # "name", "img"
        self.artists = []

        self.track_name = ""
        self.track_duration = 0
        self.track_position = 0

        self.is_playing = False
        self.repeat_state = "off"
        self.shuffle_state = False

        self.track_release_date = ""
        self.total_tracks = 0

        self.background = None
        self.background_average = 0.0

        self.background_color = eval(plugin_config["background"])
        self.foreground_color = eval(plugin_config["foreground_notplaying"])

        self.blur = 28
        self.helper = helper
        self.debug = debug

    def is_same_track(self, new_id):
        if new_id == self.id:
            return True
        return False

    def update(self, sp_object):
        self.track_position = sp_object["progress_ms"]

        # misc
        self.is_playing = sp_object["is_playing"]
        self.repeat_state = sp_object["repeat_state"]
        self.shuffle_state = sp_object["shuffle_state"]

    def parse(self, sp_object, sp, screen_width, screen_height, album_height, plugin_config):
        self.context_type = sp_object["context"]["type"]

        # "artist", "playlist", "album", "show"
        if self.context_type == "artist":
            pass
        elif self.context_type == "playlist":
            playlist = sp.playlist(sp_object["context"]["uri"])
            self.playlist_name = playlist["name"] if "name" in playlist else ""
            if "images" in playlist and len(playlist["images"]) > 0 and "url" in playlist["images"][0]:
                r = requests.get(playlist["images"][0]["url"])
                if r and r.status_code == 200:
                    img = io.BytesIO(r.content)
                    self.context_image = pygame.image.load(img).convert()
                    height = self.context_image.get_height() / (self.context_image.get_width() / plugin_config.getint("context_icon_width"))
                    self.context_image = pygame.transform.scale(self.context_image, (plugin_config.getint("context_icon_width"), int(height)))

        elif self.context_type == "album":
            pass
        elif self.context_type == "show":
            pass
        else:
            pass
        # device
        self.device_name = sp_object["device"]["name"]
        self.device_type = sp_object["device"]["type"]

        # track
        self.track_name = sp_object["item"]["name"]
        self.track_duration = sp_object["item"]["duration_ms"]
        self.track_position = sp_object["progress_ms"]

        # misc
        self.is_playing = sp_object["is_playing"]
        self.repeat_state = sp_object["repeat_state"]
        self.shuffle_state = sp_object["shuffle_state"]

        self.id = sp_object["item"]["id"]

    @staticmethod
    def make_paused_album_image(album_img):
        img = Image.frombytes("RGB", album_img.get_size(), pygame.image.tostring(album_img, "RGB"))
        enhancer = ImageEnhance.Brightness(img)
        im_output = enhancer.enhance(0.4)

        out_img = pygame.image.fromstring(im_output.tobytes(), im_output.size, "RGB").convert()

        # fifth_width = out_img.get_width()/5
        quarter_height = out_img.get_height()/4
        sixth_width = out_img.get_width()/6
        total_width = sixth_width + sixth_width + sixth_width
        pygame.draw.rect(out_img, (0, 0, 0), (out_img.get_width()/2 - total_width/2, quarter_height, sixth_width, quarter_height*2))
        pygame.draw.rect(out_img, (200, 200, 200), (out_img.get_width()/2 - total_width/2, quarter_height, sixth_width, quarter_height*2), 1)
        pygame.draw.rect(out_img, (0, 0, 0), (out_img.get_width()/2 - total_width/2 + sixth_width + sixth_width, quarter_height, sixth_width, quarter_height*2))
        pygame.draw.rect(out_img, (200, 200, 200), (out_img.get_width()/2 - total_width/2 + sixth_width + sixth_width, quarter_height, sixth_width, quarter_height*2), 1)

        return out_img

    def fix_album_image_and_build_background(self, screen_width, screen_height, album_height, plugin_config):
        light_color = eval(plugin_config["light_color"])
        dark_color = eval(plugin_config["dark_color"])
        background = eval(plugin_config["light_color"])
        if self.album_img is not None:
            if screen_height - self.album_img.get_height() > screen_width - self.album_img.get_width():
                # expand to height
                bg_width = self.album_img.get_width() * (screen_height / self.album_img.get_height())
                bg_height = screen_height
            else:
                # expand to width
                bg_width = screen_width
                bg_height = self.album_img.get_height() * (screen_width / self.album_img.get_width())

            # Build background
            average_color = pygame.transform.average_color(self.album_img)
            self.background_average = pygame.Vector3((average_color[0], average_color[1], average_color[2]))

            light_distance = pygame.Vector3(light_color).distance_to(self.background_average)
            dark_distance = pygame.Vector3(dark_color).distance_to(self.background_average)
            if light_distance > dark_distance:
                self.foreground_color = light_color
                self.background_color = dark_color
            else:
                self.foreground_color = dark_color
                self.background_color = light_color

            bg = pygame.transform.scale(self.album_img, (int(bg_width), int(bg_height)))
            bg = bg.subsurface((bg.get_width() / 2 - screen_width / 2,
                                bg.get_height() / 2 - screen_height / 2,
                                screen_width, screen_height)).copy()

            # Fix album cover
            album_width = (album_height / self.album_img.get_height()) * self.album_img.get_width()
            self.album_img = pygame.transform.scale(self.album_img, (int(album_width), int(album_height)))
            self.album_img_paused = self.make_paused_album_image(self.album_img)

            pygame.draw.rect(bg, self.background_color, (plugin_config.getint("screen_margin"),
                                                         screen_height/2 - self.album_img.get_height()/2 - self.blur,
                                                         self.album_img.get_width() + self.blur * 2,
                                                         self.album_img.get_height() + self.blur * 2))

            blurred = Image.frombytes("RGB", bg.get_size(), pygame.image.tostring(bg, "RGB"))\
                .filter(ImageFilter.GaussianBlur(radius=self.blur))
            self.background = pygame.image.fromstring(blurred.tobytes(), blurred.size, "RGB").convert()
        else:
            self.background = pygame.Surface((screen_width, screen_height))
            self.background.fill(background)
            self.background_average = background
            light_distance = pygame.Vector3(light_color).distance_to(self.background_average)
            dark_distance = pygame.Vector3(dark_color).distance_to(self.background_average)
            if light_distance > dark_distance:
                self.foreground_color = light_color
                self.background_color = dark_color
            else:
                self.foreground_color = dark_color
                self.background_color = light_color

            self.album_img = pygame.Surface((album_height, album_height))
            self.album_img.fill(background)
            self.album_img_paused = self.make_paused_album_image(self.album_img)
            self.helper.log(self.debug, "Background is empty!")

        if (self.context_type == "album" or self.context_type == "show") and self.context_image is None:
            self.context_image = self.album_img.copy()
            height = self.context_image.get_height() / (self.context_image.get_width() / plugin_config.getint("context_icon_width"))
            self.context_image = pygame.transform.scale(self.context_image, (plugin_config.getint("context_icon_width"), int(height)))


class EpisodeItem(Item):
    def __init__(self, plugin_config, helper, debug):
        super(EpisodeItem, self).__init__(plugin_config, helper, debug)
        self.type = "episode"

    def parse(self, sp_object, sp, screen_width, screen_height, album_height, plugin_config):
        super(EpisodeItem, self).parse(sp_object, sp, screen_width, screen_height, album_height, plugin_config)

        self.track_release_date = sp_object["item"]["release_date"]

        if "images" in sp_object["item"] and len(sp_object["item"]["images"]) > 0 and "url" in sp_object["item"]["images"][0]:
            r = requests.get(sp_object["item"]["images"][0]["url"])
            if r and r.status_code == 200:
                img = io.BytesIO(r.content)
                self.album_img = pygame.image.load(img).convert()
        elif "images" in sp_object["item"]["show"] and len(sp_object["item"]["show"]["images"]) > 0 and "url" in sp_object["item"]["show"]["images"][0]:
            r = requests.get(sp_object["item"]["show"]["images"][0]["url"])
            if r and r.status_code == 200:
                img = io.BytesIO(r.content)
                self.album_img = pygame.image.load(img).convert()

        # self.fix_album_image_and_build_background(screen_width, screen_height, album_height, config)
        self.album_name = sp_object["item"]["show"]["name"]

        # artist
        self.artists = sp_object["item"]["show"]["publisher"]

        self.total_tracks = sp_object["item"]["show"]["total_episodes"]


class TrackItem(Item):
    def __init__(self, plugin_config, helper, debug):
        super(TrackItem, self).__init__(plugin_config, helper, debug)
        self.type = "track"

        self.track_number = 0

    def parse(self, sp_object, sp, screen_width, screen_height, album_height, plugin_config):
        super(TrackItem, self).parse(sp_object, sp, screen_width, screen_height, album_height, plugin_config)

        if len(sp_object["item"]["album"]["images"]) > 0 and "url" in sp_object["item"]["album"]["images"][0]:
            # album
            r = requests.get(sp_object["item"]["album"]["images"][0]["url"])
            if r and r.status_code == 200:
                img = io.BytesIO(r.content)
                self.album_img = pygame.image.load(img).convert()

        # self.fix_album_image_and_build_background(screen_width, screen_height, album_height, config)
        self.album_name = sp_object["item"]["album"]["name"]

        # artists
        artist_uris = []
        for i in sp_object["item"]["artists"]:
            artist_uris.append(i["uri"])

        if len(artist_uris) > 0:
            artists = sp.artists(artist_uris)
            if "artists" in artists:
                for i in artists["artists"]:
                    if self.context_type == "artist" and self.context_image is None:
                        r = requests.get(i["images"][0]["url"])
                        if r and r.status_code == 200:
                            img = io.BytesIO(r.content)
                            self.context_image = pygame.image.load(img).convert()
                            height = self.context_image.get_height() / (self.context_image.get_width() / plugin_config.getint("context_icon_width"))
                            self.context_image = pygame.transform.scale(self.context_image, (plugin_config.getint("context_icon_width"), height))

                    self.artists.append(i["name"])

        self.track_number = sp_object["item"]["track_number"]
        self.total_tracks = sp_object["item"]["album"]["total_tracks"]
        self.track_release_date = sp_object["item"]["album"]["release_date"]
