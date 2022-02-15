# -*- coding: utf-8 -*-
"""
OpenWeatherMap Forecast
(c) Steven Babineau - babineau@gmail.com
2022
"""
import datetime
import json
import os
import time
import requests
import pygame
import geopy
import threading

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class OpenWeatherMap(FullScreenPlugin, metaclass=Singleton):
    """ OpenWeatherMap Forecast """
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        self.timer = -1

        self.url = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={API key}&units={units}&lang={lang}"
        self.icons_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.plugin_config["icons_folder"]))

        self.last_weather = None
        self.last_canvas = None

        self.smaller_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("smaller_font_size"))
        self.small_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("small_font_size"))
        self.large_font = pygame.font.SysFont(self.plugin_config["default_font_face"], self.plugin_config.getint("large_font_size"))

        self.weather_updated = False
        self.weather = None
        
        self.foreground = eval(self.plugin_config["foreground"])
        self.background = eval(self.plugin_config["background"])
        self.apikey = self.plugin_config["apikey"]
        self.latitude = self.plugin_config["latitude"]
        self.longitude = self.plugin_config["longitude"]
        self.unit_type = self.plugin_config["unit_type"]
        self.language = self.plugin_config["language"]
        self.update_interval = self.plugin_config.getint("update_interval")
        self.label = self.plugin_config["label"]
        self.city = self.plugin_config["city"]

        if not self.label:
            self.label = self.city

        self.got_longlat_from_city = False

    def download_weather(self):
        thread_timer = threading.Thread(target=self.download_weather_thread, args=([]))
        thread_timer.daemon = False
        thread_timer.start()

    def download_weather_thread(self):
        # Update the weather
        if self.apikey == "":
            return

        # Only need to do this once
        if self.city and not self.got_longlat_from_city:
            geoloc = geopy.Nominatim(user_agent="PiDisplay")
            loc = geoloc.geocode(self.city)
            if loc:
                self.longitude = str(loc.longitude)
                self.latitude = str(loc.latitude)
                self.got_longlat_from_city = True

        my_url = self.url.replace("{lat}", self.latitude) \
            .replace("{lon}", self.longitude) \
            .replace("{API key}", self.apikey) \
            .replace("{units}", self.unit_type) \
            .replace("{lang}", self.language)

        http_status = ""
        try:
            r = requests.get(my_url)
            response = r.text
            http_status = r.status_code
            r.close()
        except requests.RequestException as e:
            lock = threading.Lock()
            lock.acquire()
            self.helper.log(self.debug, "There was an error retrieving the weather: {}".format(e))
            response = ""
            lock.release()

        lock = threading.Lock()
        lock.acquire()
        if http_status == 200:
            self.weather = self.parse_json_weather(json.loads(response))
        else:
            self.weather = False
        self.weather_updated = True
        self.helper.log(self.debug, "done getting weather!")
        lock.release()

    def update(self, tick, fps):
        if int(time.time() * 1000) - self.timer > self.update_interval * 1000 * 60:
            self.download_weather()
            self.timer = int(time.time() * 1000)

        if self.weather_updated:
            if not self.weather:
                surf_error = self.small_font.render("Oops! There was a problem retrieving the weather!", True, self.foreground)
                surf_error1 = self.small_font.render("(check the city and/or longitude/latitude in the config)", True, self.foreground)

                self.canvas.fill(self.background)
                self.canvas.blit(surf_error, (self.canvas.get_width()/2 - surf_error.get_width()/2, self.canvas.get_height()/2 - surf_error.get_height()))
                self.canvas.blit(surf_error1, (self.canvas.get_width()/2 - surf_error.get_width()/2, self.canvas.get_height()/2))

            elif "current" in self.weather and len(self.weather["current"]) > 0:
                self.canvas.fill(self.background)

                _line_buffer = self.canvas.get_height()/10
                _line_color = pygame.Vector3(self.foreground)
                _line_color = _line_color.lerp(self.background, .4)
                _line_width = 2

                # TODAY'S DATE ------------
                day = '{} {dt.day} {dt.year}'.format(self.weather["current"]["date"].strftime("%A, %b"), dt=self.weather["current"]["date"])

                surf_todays_date = self.small_font.render(day, True, self.foreground)

                surf_label_height = 0
                surf_label = None
                if self.label:
                    surf_label = self.smaller_font.render(self.label, True, self.foreground)
                    surf_label_height = surf_label.get_height()

                current_weather_surface = self.get_current_weather_surface(self.weather)

                y = self.canvas.get_height()/2 - (surf_todays_date.get_height() + surf_label_height + current_weather_surface.get_height())/2
                self.canvas.blit(surf_todays_date, (self.screen_width/4 - surf_todays_date.get_width()/2, y))

                y += surf_todays_date.get_height() + 5
                if surf_label:
                    self.canvas.blit(surf_label, (current_weather_surface.get_width() / 2 - surf_label.get_width() / 2, y))
                    y += surf_label_height

                self.canvas.blit(current_weather_surface, (0, y))

                # ALL THE REST -------------
                future_hours_surface = self.get_future_hours_surface(self.weather)
                future_days_surface = self.get_future_days_surface(self.weather)

                surface_size = _line_buffer + future_hours_surface.get_height() + future_days_surface.get_height()
                y = self.canvas.get_height() - surface_size - ((self.canvas.get_height() - surface_size)/2)

                self.canvas.blit(future_hours_surface, (self.screen_width/2, y))

                y += future_hours_surface.get_height() + _line_buffer
                self.canvas.blit(future_days_surface, (self.screen_width/2, y))

                # Center vertical divider
                pygame.draw.line(self.canvas, _line_color,
                                 (self.screen_width / 2 - 1, _line_buffer),
                                 (self.screen_width / 2 - 1, self.screen_height - _line_buffer), _line_width)
                # Right horizontal divider
                pygame.draw.line(self.canvas, _line_color,
                                 (self.screen_width / 2 + _line_buffer, self.screen_height / 2 - 1),
                                 (self.screen_width - _line_buffer, self.screen_height / 2 - 1), _line_width)

            self.last_canvas = self.canvas.copy()
        else:
            if self.last_canvas is not None:
                self.canvas.blit(self.last_canvas, (0, 0))
            else:
                if self.apikey == "":
                    surf_error = self.small_font.render("Add your API key first!", True, self.foreground)
                else:
                    surf_error = self.small_font.render("Retrieving weather...", True, self.foreground)

                self.canvas.fill(self.background)
                self.canvas.blit(surf_error, (self.canvas.get_width()/2 - surf_error.get_width()/2, self.canvas.get_height()/2 - surf_error.get_height()/2))

    def get_future_hours_surface(self, weather):
        now = datetime.datetime.now()
        hour1 = now + datetime.timedelta(hours=1)
        surf_hours1 = None
        for i in weather["hourly"]:
            weather_hour = weather["hourly"][i]
            if weather_hour["date"].day == hour1.day and weather_hour["date"].month == hour1.month and weather_hour["date"].year == hour1.year and weather_hour["date"].hour == hour1.hour:
                surf_hours1 = self.make_hour_surface(weather_hour, self.smaller_font, (self.screen_width / 2) / 3)
                break
        hour2 = now + datetime.timedelta(hours=3)
        surf_hours2 = None
        for i in weather["hourly"]:
            weather_hour = weather["hourly"][i]
            if weather_hour["date"].day == hour2.day and weather_hour["date"].month == hour2.month and weather_hour["date"].year == hour2.year and weather_hour["date"].hour == hour2.hour:
                surf_hours2 = self.make_hour_surface(weather_hour, self.smaller_font, (self.screen_width / 2) / 3)
                break
        hour3 = now + datetime.timedelta(hours=5)
        surf_hours3 = None
        for i in weather["hourly"]:
            weather_hour = weather["hourly"][i]
            if weather_hour["date"].day == hour3.day and weather_hour["date"].month == hour3.month and weather_hour["date"].year == hour3.year and weather_hour["date"].hour == hour3.hour:
                surf_hours3 = self.make_hour_surface(weather_hour, self.smaller_font, (self.screen_width / 2) / 3)
                break

        height1 = 0
        height2 = 0
        height3 = 0
        if surf_hours1 is not None:
            height1 = surf_hours1.get_height()
        if surf_hours2 is not None:
            height2 = surf_hours2.get_height()
        if surf_hours3 is not None:
            height3 = surf_hours3.get_height()

        if height1 > height2:
            height = height1
        else:
            height = height2
        if height3 > height:
            height = height3

        future_hours_surface = pygame.Surface((self.screen_width/2, height))
        future_hours_surface.fill(self.background)

        if surf_hours1 is not None:
            future_hours_surface.blit(surf_hours1, (0, 0))
        if surf_hours2 is not None:
            future_hours_surface.blit(surf_hours2, (future_hours_surface.get_width() / 3, 0))
        if surf_hours3 is not None:
            future_hours_surface.blit(surf_hours3, ((future_hours_surface.get_width() / 3) * 2, 0))

        return future_hours_surface

    def get_future_days_surface(self, weather):

        now = datetime.datetime.now()
        day1 = now + datetime.timedelta(days=1)
        surf_day1 = None
        for i in weather["daily"]:
            weather_day = weather["daily"][i]
            if weather_day["date"].day == day1.day and weather_day["date"].month == day1.month and weather_day["date"].year == day1.year:
                surf_day1 = self.make_day_surface(weather_day, self.smaller_font, (self.screen_width / 2) / 3)
                break
        day2 = now + datetime.timedelta(days=2)
        surf_day2 = None
        for i in weather["daily"]:
            weather_day = weather["daily"][i]
            if weather_day["date"].day == day2.day and weather_day["date"].month == day2.month and weather_day["date"].year == day2.year:
                surf_day2 = self.make_day_surface(weather_day, self.smaller_font, (self.screen_width / 2) / 3)
                break
        day3 = now + datetime.timedelta(days=3)
        surf_day3 = None
        for i in weather["daily"]:
            weather_day = weather["daily"][i]
            if weather_day["date"].day == day3.day and weather_day["date"].month == day3.month and weather_day["date"].year == day3.year:
                surf_day3 = self.make_day_surface(weather_day, self.smaller_font, (self.screen_width / 2) / 3)
                break

        height1 = 0
        height2 = 0
        height3 = 0
        if surf_day1 is not None:
            height1 = surf_day1.get_height()
        if surf_day2 is not None:
            height2 = surf_day2.get_height()
        if surf_day3 is not None:
            height3 = surf_day3.get_height()

        if height1 > height2:
            height = height1
        else:
            height = height2
        if height3 > height:
            height = height3

        future_days_surface = pygame.Surface((self.screen_width / 2, height))
        future_days_surface.fill(self.background)

        if surf_day1 is not None:
            future_days_surface.blit(surf_day1, (0, 0))
        if surf_day2 is not None:
            future_days_surface.blit(surf_day2, (future_days_surface.get_width()/3, 0))
        if surf_day3 is not None:
            future_days_surface.blit(surf_day3, ((future_days_surface.get_width()/3)*2, 0))

        return future_days_surface

    def get_current_weather_surface(self, weather):
        _line_buffer = 20

        surface_width = self.screen_width/2
        # CURRENT WEATHER ICON -----
        surf_current_icon = pygame.image.load(weather["current"]["icon_path"]).convert_alpha()

        ratio = (surface_width*1.0/3) / surf_current_icon.get_width()
        icon_height = int(surf_current_icon.get_height() * ratio)
        surf_current_icon = pygame.transform.scale(surf_current_icon, (int((surf_current_icon.get_width()*1.0)*ratio), icon_height))

        # CURRENT TEMP --------
        surf_current_temp = self.large_font.render(u"{}{}".format(str(weather["current"]["temp"]), u'\N{DEGREE SIGN}'), True, self.foreground)

        # CURRENT HIGH/LOW -------------
        surf_degree_sign = self.small_font.render(u"{}".format(u'\N{DEGREE SIGN}'), True, self.foreground)
        surf_current_high = self.small_font.render(str(weather["current"]["high"]), True, self.foreground)
        surf_current_low = self.small_font.render(str(weather["current"]["low"]), True, self.foreground)

        if surf_current_low.get_width() > surf_current_high.get_width():
            highlow_width = surf_current_low.get_width()
        else:
            highlow_width = surf_current_high.get_width()

        highlow_width += surf_degree_sign.get_width()*3

        surf_current_highlow = pygame.Surface((highlow_width,
                                               surf_current_low.get_height() + surf_current_high.get_height() + 10))
        surf_current_highlow.fill(self.background)

        surf_current_highlow.blit(surf_current_high,
                                  (surf_current_highlow.get_width()/2 - surf_current_high.get_width()/2, 0))
        surf_current_highlow.blit(surf_degree_sign,
                                  (surf_current_highlow.get_width() / 2 - surf_current_high.get_width() / 2 +
                                   surf_current_high.get_width(), 0))

        _line_color = pygame.Vector3(self.foreground)
        _line_color = _line_color.lerp(self.background, .75)

        pygame.draw.line(surf_current_highlow, _line_color, (0, surf_current_highlow.get_height()/2-1),
                         (surf_current_highlow.get_width(), surf_current_highlow.get_height()/2-1))

        surf_current_highlow.blit(surf_current_low, (surf_current_highlow.get_width()/2 -
                                                     surf_current_low.get_width()/2, surf_current_highlow.get_height()
                                                     - surf_current_low.get_height()))
        surf_current_highlow.blit(surf_degree_sign, (surf_current_highlow.get_width()/2 -
                                                     surf_current_low.get_width()/2 + surf_current_low.get_width(),
                                                     surf_current_highlow.get_height() - surf_current_low.get_height()))

        if surf_current_icon.get_height() > surf_current_temp.get_height():
            row1_height = surf_current_icon.get_height()
        else:
            row1_height = surf_current_temp.get_height()
        if surf_current_highlow.get_height() > row1_height:
            row1_height = surf_current_highlow.get_height()

        # RAIN ICON -----------------
        surf_rain_chance = self.make_small_icon_text(self.plugin_config["weather_icons_rain"], "{}%".format(weather["current"]["rain"]), self.small_font)
        # WIND SPEED ICON -------------
        surf_wind_speed = self.make_small_icon_text(self.plugin_config["weather_icons_wind_speed"], "{}mph".format(weather["current"]["wind_speed"]), self.small_font)
        # HUMIDITY ICON -------------------
        surf_humidity = self.make_small_icon_text(self.plugin_config["weather_icons_humidity"], "{}%".format(weather["current"]["humidity"]), self.small_font)

        if surf_rain_chance.get_height() > surf_wind_speed.get_height():
            row2_height = surf_rain_chance.get_height()
        else:
            row2_height = surf_wind_speed.get_height()
        if surf_humidity.get_height() > row2_height:
            row2_height = surf_humidity.get_height()

        # SUNRISE ICON ----------
        sunrise_time = weather["current"]["sunrise"].strftime("%I:%M %p")
        if sunrise_time[:1] == "0":
            sunrise_time = sunrise_time[1:]

        surf_sunrise = self.make_small_icon_text(self.plugin_config["weather_icons_sunrise"], sunrise_time, self.small_font)

        # SUNSET ICON -----------
        sunset_time = weather["current"]["sunset"].strftime("%I:%M %p")
        if sunset_time[:1] == "0":
            sunset_time = sunset_time[1:]

        surf_sunset = self.make_small_icon_text(self.plugin_config["weather_icons_sunset"], sunset_time, self.small_font)

        if surf_sunset.get_height() > surf_sunrise.get_height():
            row3_height = surf_sunset.get_height()
        else:
            row3_height = surf_sunrise.get_height()

        moon_phase_percent = int(weather["current"]["moon_phase"] * 100)
        text = "{}% of new moon".format(moon_phase_percent)
        surf_moon_icon = self.make_small_icon_text(weather["current"]["moon_phase_icon_path"], text, self.smaller_font)
        row4_height = surf_moon_icon.get_height()

        surface_height = (_line_buffer * 3) + row1_height + row2_height + row3_height + row4_height
        current_weather_surface = pygame.Surface((surface_width, surface_height))
        current_weather_surface.fill(self.background)

        y = 0
        _large_icon_spacer = 20
        w = surf_current_highlow.get_width() + _large_icon_spacer + surf_current_icon.get_width() + _large_icon_spacer + surf_current_temp.get_width()
        x = current_weather_surface.get_width() / 2 - w/2
        current_weather_surface.blit(surf_current_highlow, (x, y + row1_height/2 - surf_current_highlow.get_height()/2))
        x += surf_current_highlow.get_width() + _large_icon_spacer
        current_weather_surface.blit(surf_current_icon, (x, y))
        x += surf_current_icon.get_width() + _large_icon_spacer
        current_weather_surface.blit(surf_current_temp, (x, y + row1_height/2 - surf_current_temp.get_height()/2))

        y += row1_height + _line_buffer

        spacer = 0
        w = surf_rain_chance.get_width() + surf_wind_speed.get_width() + surf_humidity.get_width()
        if w < current_weather_surface.get_width():
            spacer = int((current_weather_surface.get_width() - w - 20) / 2)
            w += spacer*2

        x = current_weather_surface.get_width() / 2 - w/2
        current_weather_surface.blit(surf_rain_chance, (x, y))
        x += surf_rain_chance.get_width() + spacer
        current_weather_surface.blit(surf_wind_speed, (x, y))
        x += surf_wind_speed.get_width() + spacer
        current_weather_surface.blit(surf_humidity, (x, y))

        y += row2_height + _line_buffer

        _small_icon_spacer = 30
        x = current_weather_surface.get_width() / 2 - _small_icon_spacer/2 - surf_sunrise.get_width()
        current_weather_surface.blit(surf_sunrise, (x,  y))
        x = current_weather_surface.get_width() / 2 + _small_icon_spacer/2
        current_weather_surface.blit(surf_sunset, (x, y))

        y += row3_height + _line_buffer
        current_weather_surface.blit(surf_moon_icon, (current_weather_surface.get_width() / 2 - surf_moon_icon.get_width()/2, y))

        return current_weather_surface

    def make_small_icon_text(self, icon_path, icon_text, font):
        _buffer = 5
        surf_icon = pygame.image.load(os.path.join(self.icons_folder, icon_path)).convert_alpha()
        surf_text = font.render(icon_text, True, self.foreground)

        # Icons have a lot of spacing around them. Let's tighten it up a bit
        _icon_size_buffer = 15
        _temp_text_height = surf_text.get_height() + _icon_size_buffer
        ratio = _temp_text_height * 1.0 / surf_icon.get_height()
        icon_width = int(surf_icon.get_width() * ratio)

        surf_icon = pygame.transform.scale(surf_icon, (icon_width, _temp_text_height))

        surf_icon_complete = pygame.Surface((surf_icon.get_width() + _buffer + surf_text.get_width(),
                                             _temp_text_height))
        surf_icon_complete.fill(self.background)
        surf_icon_complete.blit(surf_icon, (0, 0))
        surf_icon_complete.blit(surf_text, (surf_icon.get_width() + _buffer, surf_icon_complete.get_height()/2 -
                                            surf_text.get_height()/2))

        return surf_icon_complete

    def make_day_surface(self, day_weather, font, width):
        _temp_icon_factor = 2  # the smaller this value, the larger the icon
        # DAY TEXT ---------
        surf_day_text = font.render(day_weather["date"].strftime("%a"), True, self.foreground)

        # TEMP ICON -------------
        surf_temp_icon = pygame.image.load(day_weather["icon_path"]).convert_alpha()

        ratio = (width*1.0/_temp_icon_factor) / surf_temp_icon.get_width()
        icon_height = int(surf_temp_icon.get_height() * ratio)
        surf_temp_icon = pygame.transform.scale(surf_temp_icon, (int((surf_temp_icon.get_width()*1.0)*ratio),
                                                                 icon_height))

        # HIGH/LOW TEMP ----------------
        surf_temp = font.render(u"{}{}/{}{}".
                                format(str(day_weather["high"]), u'\N{DEGREE SIGN}',
                                       str(day_weather["low"]), u'\N{DEGREE SIGN}', ),
                                True, self.foreground)

        # RAIN CHANCE ---------------------
        surf_rain = self.make_small_icon_text(self.plugin_config["weather_icons_rain"],
                                              "{}{}".format(day_weather["rain"], "%"), font)

        # WIND SPEED --------------
        surf_wind_speed = self.make_small_icon_text(self.plugin_config["weather_icons_wind_speed"],
                                                    "{}{}".format(day_weather["wind_speed"], "mph"), font)

        _line_spacer = 10
        height = (_line_spacer * 4) + surf_day_text.get_height() + surf_temp_icon.get_height() + \
            surf_temp.get_height() + surf_rain.get_height() + surf_wind_speed.get_height()
        surf_day = pygame.Surface((width, height))
        surf_day.fill(self.background)

        y = 0
        surf_day.blit(surf_day_text, (width / 2 - surf_day_text.get_width() / 2, y))
        y += surf_day_text.get_height() + _line_spacer
        surf_day.blit(surf_temp_icon, (width / 2 - surf_temp_icon.get_width() / 2, y))
        y += surf_temp_icon.get_height() + _line_spacer

        surf_day.blit(surf_temp, (width / 2 - surf_temp.get_width() / 2, y))
        y += surf_temp.get_height() + _line_spacer
        surf_day.blit(surf_rain, (width / 2 - surf_rain.get_width() / 2, y))
        y += surf_rain.get_height() + _line_spacer
        surf_day.blit(surf_wind_speed, (width / 2 - surf_wind_speed.get_width() / 2, y))

        return surf_day

    def make_hour_surface(self, hour_weather, font, width):
        _temp_icon_factor = 2  # the smaller this value, the larger the icon

        # HOUR TEXT ---
        weather_time = hour_weather["date"].strftime("%I %p")
        if weather_time[:1] == "0":
            weather_time = weather_time[1:]

        surf_hour_text = font.render(weather_time, True, self.foreground)

        # TEMP ICON ------
        surf_temp_icon = pygame.image.load(hour_weather["icon_path"]).convert_alpha()
        ratio = (width*1.0/_temp_icon_factor) / surf_temp_icon.get_width()
        icon_height = int(surf_temp_icon.get_height() * ratio)
        surf_temp_icon = pygame.transform.scale(surf_temp_icon, (int((surf_temp_icon.get_width()*1.0)*ratio),
                                                                 icon_height))

        # TEMP TEXT ---------
        surf_temp = font.render(u"{}{}".format(str(hour_weather["temp"]), u'\N{DEGREE SIGN}'), True,
                                self.foreground)

        # RAIN CHANCE ----------
        surf_rain = self.make_small_icon_text(self.plugin_config["weather_icons_rain"],
                                              "{}{}".format(hour_weather["rain"], "%"), font)

        # WIND SPEED -------------
        surf_wind_speed = self.make_small_icon_text(self.plugin_config["weather_icons_wind_speed"],
                                                    "{}{}".format(hour_weather["wind_speed"], "mph"), font)

        _line_spacer = 10
        height = (_line_spacer*4) + surf_hour_text.get_height() + surf_temp_icon.get_height() + \
            surf_temp.get_height() + surf_rain.get_height() + surf_wind_speed.get_height()
        surf_hour = pygame.Surface((width, height))
        surf_hour.fill(self.background)

        y = 0
        surf_hour.blit(surf_hour_text, (width/2 - surf_hour_text.get_width()/2, y))
        y += surf_hour_text.get_height() + _line_spacer
        surf_hour.blit(surf_temp_icon, (width/2 - surf_temp_icon.get_width()/2, y))
        y += surf_temp_icon.get_height() + _line_spacer
        surf_hour.blit(surf_temp, (width/2 - surf_temp.get_width()/2, y))
        y += surf_temp.get_height() + _line_spacer
        surf_hour.blit(surf_rain, (width/2 - surf_rain.get_width()/2, y))
        y += surf_rain.get_height() + _line_spacer
        surf_hour.blit(surf_wind_speed, (width/2 - surf_wind_speed.get_width()/2, y))

        return surf_hour

    def parse_json_weather(self, json_weather):
        weather = {}
        weather.update({"current": {}})
        if "current" not in json_weather:
            return weather

        if "dt" in json_weather["current"]:
            try:
                weather["current"].update({"date": datetime.datetime.fromtimestamp(json_weather["current"]["dt"])})
            except TypeError:
                weather["current"].update({"date": datetime.datetime.fromtimestamp(0)})
        else:
            weather["current"].update({"date": datetime.datetime.fromtimestamp(0)})
        icon_key = ""
        if "weather" in json_weather["current"]:
            for j in range(len(json_weather["current"]["weather"])):
                if "icon" in json_weather["current"]["weather"][j]:
                    icon_key = json_weather["current"]["weather"][j]["icon"]
                    break

        icon_key = "weather_icons_{}".format(icon_key)
        if icon_key in self.plugin_config:
            current_icon_path = os.path.join(self.icons_folder, self.plugin_config[icon_key])
        else:
            current_icon_path = os.path.join(self.icons_folder, self.plugin_config["weather_icons_unknown"])

        weather["current"].update({"icon_path": current_icon_path})
        weather["current"].update({"temp": 0})
        if "temp" in json_weather["current"]:
            weather["current"]["temp"] = int(json_weather["current"]["temp"])

        if "sunrise" in json_weather["current"]:
            try:
                dt = datetime.datetime.fromtimestamp(json_weather["current"]["sunrise"])
            except TypeError:
                dt = datetime.datetime.fromtimestamp(0)
        else:
            dt = datetime.datetime.fromtimestamp(0)
        weather["current"].update({"sunrise": dt})

        if "sunset" in json_weather["current"]:
            try:
                dt = datetime.datetime.fromtimestamp(json_weather["current"]["sunset"])
            except TypeError:
                dt = datetime.datetime.fromtimestamp(0)
        else:
            dt = datetime.datetime.fromtimestamp(0)
        weather["current"].update({"sunset": dt})

        if "humidity" in json_weather["current"]:
            weather["current"].update({"humidity": json_weather["current"]["humidity"]})
        else:
            weather["current"].update({"humidity": 0})

        weather.update({"daily": {}})
        weather.update({"hourly": {}})
        if "daily" in json_weather:
            for i in json_weather["daily"]:
                if "dt" in i:
                    try:
                        w_date = datetime.datetime.fromtimestamp(i["dt"])
                    except TypeError:
                        w_date = datetime.datetime.fromtimestamp(0)
                else:
                    w_date = datetime.datetime.fromtimestamp(0)

                today = datetime.datetime.today()
                if today.day == w_date.day and today.month == w_date.month and today.year == w_date.year:
                    weather["current"].update({"high": int(i["temp"]["max"])
                                              if "temp" in i and "max" in i["temp"] else "0"})
                    weather["current"].update({"low": int(i["temp"]["min"])
                                              if "temp" in i and "min" in i["temp"] else "0"})
                    weather["current"].update({"rain": int(i["rain"])
                                              if "rain" in i else "0"})
                    weather["current"].update({"wind_speed": int(i["wind_speed"])
                                              if "wind_speed" in i else "0"})

                    weather["current"].update({"description": ""})
                    weather["current"].update({"moon_phase": float(i["moon_phase"])})

                    if "weather" in i:
                        for j in range(len(i["weather"])):
                            if "description" in i["weather"][j]:
                                weather["current"]["description"] = self.helper.upper_first_char(i["weather"][0]["description"].split(".")[0])
                                break

                else:
                    daily = {}
                    daily.update({"date": w_date})

                    icon_key = ""
                    if "weather" in i:
                        for j in range(len(i["weather"])):
                            if "icon" in i["weather"][j]:
                                icon_key = i["weather"][j]["icon"]
                                break

                    icon_key = "weather_icons_{}".format(icon_key)
                    if icon_key in self.plugin_config:
                        daily_icon_path = os.path.join(self.icons_folder, self.plugin_config[icon_key])
                    else:
                        daily_icon_path = os.path.join(self.icons_folder, self.plugin_config["weather_icons_unknown"])

                    daily.update({"icon_path": daily_icon_path})

                    daily.update({"high": int(i["temp"]["max"]) if "temp" in i and "max" in i["temp"] else "0"})
                    daily.update({"low": int(i["temp"]["min"]) if "temp" in i and "min" in i["temp"] else "0"})
                    daily.update({"rain": int(i["pop"]) if "pop" in i else "0"})
                    daily.update({"wind_speed": int(i["wind_speed"]) if "wind_speed" in i else "0"})

                    daily.update({"description": ""})
                    if "weather" in i:
                        for j in range(len(i["weather"])):
                            if "description" in i["weather"][j]:
                                daily["description"] = self.helper.upper_first_char(i["weather"][0]["description"].split(".")[0])
                                break

                    daily.update({"moon_phase": float(i["moon_phase"])})
                    weather["daily"].update({i["dt"]: daily})

        if "hourly" in json_weather:
            for i in json_weather["hourly"]:
                hourly = {}
                hourly.update({"date": datetime.datetime.fromtimestamp(i["dt"])
                              if "dt" in i else datetime.datetime.now()})

                icon_key = ""
                if "weather" in i:
                    for j in range(len(i["weather"])):
                        if "icon" in i["weather"][j]:
                            icon_key = i["weather"][j]["icon"]
                            break

                icon_key = "weather_icons_{}".format(icon_key)
                if icon_key in self.plugin_config:
                    hourly_icon_path = os.path.join(self.icons_folder, self.plugin_config[icon_key])
                else:
                    hourly_icon_path = os.path.join(self.icons_folder, self.plugin_config["weather_icons_unknown"])

                hourly.update({"icon_path": hourly_icon_path})
                hourly.update({"temp": int(i["temp"]) if "temp" in i else 0})
                hourly.update({"rain": int(i["pop"]) if "pop" in i else 0})
                hourly.update({"wind_speed": int(i["wind_speed"]) if "wind_speed" in i else 0})
                hourly.update({"description": ""})
                if "weather" in i:
                    for j in range(len(i["weather"])):
                        if "description" in i["weather"][j]:
                            hourly["description"] = self.helper.upper_first_char(i["weather"][0]["description"].split(".")[0])
                            break

                weather["hourly"].update({i["dt"]: hourly})

        moon_phase_icon_path = ""
        if "moon_phase" in weather["current"]:
            moon_phase_percent = int(weather["current"]["moon_phase"] * 100)
            moon_phase_key = "weather_icons_moon_phase_{0:03d}".format(moon_phase_percent)
            if moon_phase_key in self.plugin_config:
                moon_phase_icon_path = os.path.join(self.icons_folder, "moon_phases", self.plugin_config[moon_phase_key])
            else:
                # try to figure it out
                if moon_phase_percent > 0:
                    for j in range(moon_phase_percent, 0, -1):
                        moon_phase_key = "weather_icons_moon_phase_{0:03d}".format(j)
                        if moon_phase_key in self.plugin_config:
                            moon_phase_icon_path = os.path.join(self.icons_folder, "moon_phases", self.plugin_config[moon_phase_key])
                            break
        if moon_phase_icon_path:
            weather["current"].update({"moon_phase_icon_path": moon_phase_icon_path})

        return weather
