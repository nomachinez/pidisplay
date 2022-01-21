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
import threading


class OpenWeatherMap:
    """ OpenWeatherMap Forecast """
    def __init__(self, config, helper, canvas):
        self.config = config
        self.helper = helper
        self.canvas = canvas
        self.screen_width = self.canvas.get_width()
        self.screen_height = self.canvas.get_height()

        self.timer = -1

        self.url = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={API key}&units={units}&lang={lang}"
        self.icons_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.config["icons_folder"]))

        self.last_weather = None
        self.last_canvas = None

        self.smaller_font = pygame.font.SysFont(self.config["application_sysfont"], self.config["smaller_font_size"])
        self.small_font = pygame.font.SysFont(self.config["application_sysfont"], self.config["small_font_size"])
        self.large_font = pygame.font.SysFont(self.config["application_sysfont"], self.config["large_font_size"])

        self.weather_updated = False
        self.weather = None

    def download_weather(self):
        thread_timer = threading.Thread(target=self.download_weather_thread, args=([]))
        thread_timer.daemon = False
        thread_timer.start()

    def download_weather_thread(self):
        # Update the weather
        self.helper.log(self.config, "WEATHER TEST MODE: {}".format(self.config["test_mode"]))

        if self.config["apikey"] == "":
            return

        my_url = self.url.replace("{lat}", self.config["latitude"]) \
            .replace("{lon}", self.config["longitude"]) \
            .replace("{API key}", self.config["apikey"]) \
            .replace("{units}", self.config["unit_type"]) \
            .replace("{lang}", self.config["language"])

        if self.config["test_mode"]:
            response = r'{"lat":42.6334,"lon":-71.3162,"timezone":"America/New_York","timezone_offset":-18000,"current":{"dt":1642527953,"sunrise":1642507857,"sunset":1642542001,"temp":27.95,"feels_like":22.32,"pressure":1005,"humidity":47,"dew_point":12.25,"uvi":0.96,"clouds":40,"visibility":10000,"wind_speed":5.01,"wind_deg":356,"wind_gust":14,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}]},"hourly":[{"dt":1642525200,"temp":27.54,"feels_like":15.78,"pressure":1005,"humidity":48,"dew_point":12.29,"uvi":1.14,"clouds":44,"visibility":10000,"wind_speed":15.23,"wind_deg":292,"wind_gust":29.21,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642528800,"temp":27.95,"feels_like":16.34,"pressure":1005,"humidity":47,"dew_point":12.25,"uvi":0.96,"clouds":40,"visibility":10000,"wind_speed":15.14,"wind_deg":291,"wind_gust":28.43,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642532400,"temp":27.39,"feels_like":15.78,"pressure":1006,"humidity":48,"dew_point":12.15,"uvi":0.6,"clouds":37,"visibility":10000,"wind_speed":14.76,"wind_deg":289,"wind_gust":28.97,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642536000,"temp":26.2,"feels_like":14.43,"pressure":1007,"humidity":49,"dew_point":11.44,"uvi":0.27,"clouds":31,"visibility":10000,"wind_speed":14.36,"wind_deg":289,"wind_gust":29.93,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642539600,"temp":24.13,"feels_like":12.09,"pressure":1009,"humidity":50,"dew_point":9.9,"uvi":0,"clouds":27,"visibility":10000,"wind_speed":13.69,"wind_deg":292,"wind_gust":30.53,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642543200,"temp":21.45,"feels_like":9.03,"pressure":1011,"humidity":52,"dew_point":8.15,"uvi":0,"clouds":23,"visibility":10000,"wind_speed":12.95,"wind_deg":293,"wind_gust":29.8,"weather":[{"id":801,"main":"Clouds","description":"few clouds","icon":"02n"}],"pop":0},{"dt":1642546800,"temp":19.02,"feels_like":6.57,"pressure":1015,"humidity":52,"dew_point":3.54,"uvi":0,"clouds":15,"visibility":10000,"wind_speed":11.81,"wind_deg":289,"wind_gust":28.54,"weather":[{"id":801,"main":"Clouds","description":"few clouds","icon":"02n"}],"pop":0},{"dt":1642550400,"temp":18.3,"feels_like":6.31,"pressure":1016,"humidity":52,"dew_point":2.79,"uvi":0,"clouds":13,"visibility":10000,"wind_speed":10.69,"wind_deg":292,"wind_gust":28.5,"weather":[{"id":801,"main":"Clouds","description":"few clouds","icon":"02n"}],"pop":0},{"dt":1642554000,"temp":17.51,"feels_like":6.04,"pressure":1017,"humidity":52,"dew_point":1.71,"uvi":0,"clouds":1,"visibility":10000,"wind_speed":9.6,"wind_deg":293,"wind_gust":27.6,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"pop":0},{"dt":1642557600,"temp":17.02,"feels_like":6.37,"pressure":1018,"humidity":51,"dew_point":0.73,"uvi":0,"clouds":0,"visibility":10000,"wind_speed":8.3,"wind_deg":288,"wind_gust":23.89,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"pop":0},{"dt":1642561200,"temp":16.72,"feels_like":6.57,"pressure":1019,"humidity":50,"dew_point":0.32,"uvi":0,"clouds":2,"visibility":10000,"wind_speed":7.61,"wind_deg":271,"wind_gust":18.7,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"pop":0},{"dt":1642564800,"temp":16.57,"feels_like":6.69,"pressure":1020,"humidity":51,"dew_point":0.37,"uvi":0,"clouds":4,"visibility":10000,"wind_speed":7.25,"wind_deg":264,"wind_gust":16.73,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"pop":0},{"dt":1642568400,"temp":16.56,"feels_like":7.59,"pressure":1020,"humidity":52,"dew_point":0.77,"uvi":0,"clouds":5,"visibility":10000,"wind_speed":6.24,"wind_deg":259,"wind_gust":15.48,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"pop":0},{"dt":1642572000,"temp":16.74,"feels_like":8.13,"pressure":1020,"humidity":54,"dew_point":1.76,"uvi":0,"clouds":6,"visibility":10000,"wind_speed":5.93,"wind_deg":252,"wind_gust":15.5,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"pop":0},{"dt":1642575600,"temp":16.93,"feels_like":8.64,"pressure":1021,"humidity":55,"dew_point":2.48,"uvi":0,"clouds":58,"visibility":10000,"wind_speed":5.66,"wind_deg":247,"wind_gust":16.49,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642579200,"temp":16.81,"feels_like":9.66,"pressure":1020,"humidity":56,"dew_point":2.55,"uvi":0,"clouds":40,"visibility":10000,"wind_speed":4.65,"wind_deg":249,"wind_gust":13.6,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03n"}],"pop":0},{"dt":1642582800,"temp":16.93,"feels_like":9.88,"pressure":1020,"humidity":56,"dew_point":2.77,"uvi":0,"clouds":57,"visibility":10000,"wind_speed":4.59,"wind_deg":240,"wind_gust":13.85,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642586400,"temp":17.73,"feels_like":10.78,"pressure":1020,"humidity":55,"dew_point":3.11,"uvi":0,"clouds":62,"visibility":10000,"wind_speed":4.61,"wind_deg":231,"wind_gust":15.03,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642590000,"temp":19.38,"feels_like":12.04,"pressure":1020,"humidity":53,"dew_point":4.01,"uvi":0,"clouds":69,"visibility":10000,"wind_speed":5.19,"wind_deg":216,"wind_gust":21,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642593600,"temp":20.8,"feels_like":13.41,"pressure":1019,"humidity":54,"dew_point":5.76,"uvi":0,"clouds":74,"visibility":10000,"wind_speed":5.48,"wind_deg":195,"wind_gust":26.69,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642597200,"temp":23.56,"feels_like":15.19,"pressure":1018,"humidity":57,"dew_point":9.81,"uvi":0.12,"clouds":100,"visibility":10000,"wind_speed":7.18,"wind_deg":189,"wind_gust":32.53,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0},{"dt":1642600800,"temp":27.54,"feels_like":18.48,"pressure":1017,"humidity":64,"dew_point":16.57,"uvi":0.36,"clouds":100,"visibility":10000,"wind_speed":9.51,"wind_deg":196,"wind_gust":35.52,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0},{"dt":1642604400,"temp":32.52,"feels_like":23.59,"pressure":1016,"humidity":66,"dew_point":22.19,"uvi":0.67,"clouds":100,"visibility":10000,"wind_speed":11.63,"wind_deg":202,"wind_gust":38.05,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0},{"dt":1642608000,"temp":37.27,"feels_like":28.53,"pressure":1015,"humidity":58,"dew_point":23.59,"uvi":0.95,"clouds":100,"visibility":10000,"wind_speed":14.43,"wind_deg":209,"wind_gust":40.98,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0},{"dt":1642611600,"temp":40.28,"feels_like":32.2,"pressure":1013,"humidity":57,"dew_point":25.84,"uvi":1.02,"clouds":100,"visibility":10000,"wind_speed":14.99,"wind_deg":215,"wind_gust":41.52,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0},{"dt":1642615200,"temp":42.42,"feels_like":34.99,"pressure":1012,"humidity":57,"dew_point":27.81,"uvi":0.85,"clouds":99,"visibility":10000,"wind_speed":14.85,"wind_deg":218,"wind_gust":39.95,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0},{"dt":1642618800,"temp":43.16,"feels_like":36.19,"pressure":1011,"humidity":57,"dew_point":28.87,"uvi":0.6,"clouds":41,"visibility":10000,"wind_speed":13.96,"wind_deg":224,"wind_gust":39.55,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642622400,"temp":42.06,"feels_like":34.93,"pressure":1011,"humidity":59,"dew_point":28.49,"uvi":0.27,"clouds":46,"visibility":10000,"wind_speed":13.49,"wind_deg":229,"wind_gust":35.93,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"pop":0},{"dt":1642626000,"temp":39.7,"feels_like":32.38,"pressure":1011,"humidity":64,"dew_point":28.15,"uvi":0,"clouds":61,"visibility":10000,"wind_speed":12.24,"wind_deg":231,"wind_gust":32.19,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04d"}],"pop":0},{"dt":1642629600,"temp":37.67,"feels_like":30.15,"pressure":1012,"humidity":70,"dew_point":28.62,"uvi":0,"clouds":60,"visibility":10000,"wind_speed":11.43,"wind_deg":230,"wind_gust":30.85,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642633200,"temp":36.91,"feels_like":29.43,"pressure":1013,"humidity":74,"dew_point":29.21,"uvi":0,"clouds":59,"visibility":10000,"wind_speed":10.87,"wind_deg":229,"wind_gust":31.43,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642636800,"temp":36.43,"feels_like":29.05,"pressure":1013,"humidity":78,"dew_point":29.97,"uvi":0,"clouds":60,"visibility":10000,"wind_speed":10.38,"wind_deg":227,"wind_gust":31.65,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642640400,"temp":36.34,"feels_like":29.16,"pressure":1013,"humidity":81,"dew_point":30.78,"uvi":0,"clouds":79,"visibility":10000,"wind_speed":9.89,"wind_deg":226,"wind_gust":31.16,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04n"}],"pop":0},{"dt":1642644000,"temp":36.61,"feels_like":29.71,"pressure":1013,"humidity":83,"dew_point":31.6,"uvi":0,"clouds":88,"visibility":10000,"wind_speed":9.44,"wind_deg":223,"wind_gust":29.24,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642647600,"temp":37.27,"feels_like":30.61,"pressure":1013,"humidity":83,"dew_point":32.43,"uvi":0,"clouds":92,"visibility":10000,"wind_speed":9.26,"wind_deg":226,"wind_gust":28.52,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642651200,"temp":37.24,"feels_like":30.58,"pressure":1014,"humidity":85,"dew_point":32.97,"uvi":0,"clouds":94,"visibility":10000,"wind_speed":9.24,"wind_deg":228,"wind_gust":28.39,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642654800,"temp":36.46,"feels_like":30.24,"pressure":1013,"humidity":89,"dew_point":33.28,"uvi":0,"clouds":95,"visibility":10000,"wind_speed":8.08,"wind_deg":231,"wind_gust":25.05,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642658400,"temp":35.64,"feels_like":29.75,"pressure":1014,"humidity":92,"dew_point":33.19,"uvi":0,"clouds":96,"visibility":10000,"wind_speed":7.2,"wind_deg":239,"wind_gust":24.2,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642662000,"temp":34.88,"feels_like":29.88,"pressure":1014,"humidity":93,"dew_point":32.83,"uvi":0,"clouds":100,"visibility":10000,"wind_speed":5.7,"wind_deg":257,"wind_gust":17.9,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642665600,"temp":34.61,"feels_like":28.78,"pressure":1014,"humidity":83,"dew_point":29.44,"uvi":0,"clouds":100,"visibility":10000,"wind_speed":6.8,"wind_deg":282,"wind_gust":18.81,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0},{"dt":1642669200,"temp":32.92,"feels_like":25.56,"pressure":1015,"humidity":74,"dew_point":25.25,"uvi":0,"clouds":100,"visibility":9781,"wind_speed":8.7,"wind_deg":286,"wind_gust":24.25,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04n"}],"pop":0.15},{"dt":1642672800,"temp":29.61,"feels_like":21.72,"pressure":1016,"humidity":86,"dew_point":25.66,"uvi":0,"clouds":100,"visibility":1427,"wind_speed":8.34,"wind_deg":283,"wind_gust":24.25,"weather":[{"id":601,"main":"Snow","description":"snow","icon":"13n"}],"pop":0.65,"snow":{"1h":0.56}},{"dt":1642676400,"temp":28.8,"feels_like":21.76,"pressure":1017,"humidity":86,"dew_point":24.73,"uvi":0,"clouds":100,"visibility":3090,"wind_speed":6.85,"wind_deg":282,"wind_gust":22.41,"weather":[{"id":601,"main":"Snow","description":"snow","icon":"13n"}],"pop":0.76,"snow":{"1h":0.73}},{"dt":1642680000,"temp":28.33,"feels_like":21.52,"pressure":1017,"humidity":86,"dew_point":24.37,"uvi":0,"clouds":100,"visibility":1930,"wind_speed":6.4,"wind_deg":283,"wind_gust":20.22,"weather":[{"id":600,"main":"Snow","description":"light snow","icon":"13n"}],"pop":0.82,"snow":{"1h":0.47}},{"dt":1642683600,"temp":28.29,"feels_like":21.36,"pressure":1018,"humidity":86,"dew_point":24.33,"uvi":0.16,"clouds":100,"visibility":2348,"wind_speed":6.55,"wind_deg":287,"wind_gust":20.02,"weather":[{"id":600,"main":"Snow","description":"light snow","icon":"13d"}],"pop":0.93,"snow":{"1h":0.41}},{"dt":1642687200,"temp":28.69,"feels_like":21.87,"pressure":1018,"humidity":82,"dew_point":23.49,"uvi":0.47,"clouds":100,"visibility":10000,"wind_speed":6.53,"wind_deg":288,"wind_gust":16.22,"weather":[{"id":600,"main":"Snow","description":"light snow","icon":"13d"}],"pop":0.85,"snow":{"1h":0.32}},{"dt":1642690800,"temp":29.57,"feels_like":22.37,"pressure":1019,"humidity":73,"dew_point":21.49,"uvi":0.87,"clouds":100,"visibility":10000,"wind_speed":7.27,"wind_deg":303,"wind_gust":14.09,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0.76},{"dt":1642694400,"temp":30.94,"feels_like":23.11,"pressure":1019,"humidity":60,"dew_point":18.37,"uvi":1.31,"clouds":100,"visibility":10000,"wind_speed":8.72,"wind_deg":311,"wind_gust":13.71,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"pop":0.68}],"daily":[{"dt":1642521600,"sunrise":1642507857,"sunset":1642542001,"moonrise":1642544160,"moonset":1642510800,"moon_phase":0.52,"temp":{"day":27.09,"min":16.57,"max":29.12,"night":16.57,"eve":21.45,"morn":24.64},"feels_like":{"day":15.4,"night":6.69,"eve":9.03,"morn":12.2},"pressure":1005,"humidity":49,"dew_point":12.27,"wind_speed":15.23,"wind_deg":292,"wind_gust":34.16,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04d"}],"clouds":53,"pop":0,"uvi":1.14},{"dt":1642608000,"sunrise":1642594221,"sunset":1642628475,"moonrise":1642634460,"moonset":1642599240,"moon_phase":0.55,"temp":{"day":37.27,"min":16.56,"max":43.16,"night":37.24,"eve":37.67,"morn":17.73},"feels_like":{"day":28.53,"night":30.58,"eve":30.15,"morn":10.78},"pressure":1015,"humidity":58,"dew_point":23.59,"wind_speed":14.99,"wind_deg":215,"wind_gust":41.52,"weather":[{"id":804,"main":"Clouds","description":"overcast clouds","icon":"04d"}],"clouds":100,"pop":0,"uvi":1.02},{"dt":1642694400,"sunrise":1642680583,"sunset":1642714950,"moonrise":1642724880,"moonset":1642687380,"moon_phase":0.59,"temp":{"day":30.94,"min":16.5,"max":36.46,"night":16.5,"eve":22.35,"morn":29.61},"feels_like":{"day":23.11,"night":4.5,"eve":11.55,"morn":21.72},"pressure":1019,"humidity":60,"dew_point":18.37,"wind_speed":10.54,"wind_deg":328,"wind_gust":25.05,"weather":[{"id":601,"main":"Snow","description":"snow","icon":"13d"}],"clouds":100,"pop":0.93,"snow":2.49,"uvi":1.4},{"dt":1642780800,"sunrise":1642766943,"sunset":1642801425,"moonrise":1642815240,"moonset":1642775280,"moon_phase":0.62,"temp":{"day":12.97,"min":8.78,"max":18.86,"night":14.81,"eve":18.86,"morn":10.83},"feels_like":{"day":2.55,"night":7.81,"eve":11.48,"morn":-1.73},"pressure":1035,"humidity":46,"dew_point":-5.35,"wind_speed":9.82,"wind_deg":334,"wind_gust":20.13,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01d"}],"clouds":3,"pop":0,"uvi":1.29},{"dt":1642867200,"sunrise":1642853301,"sunset":1642887901,"moonrise":1642905720,"moonset":1642863060,"moon_phase":0.65,"temp":{"day":18.99,"min":12.72,"max":26.47,"night":21.76,"eve":26.47,"morn":13.59},"feels_like":{"day":11.82,"night":21.76,"eve":26.47,"morn":4.62},"pressure":1034,"humidity":59,"dew_point":6.26,"wind_speed":5.7,"wind_deg":356,"wind_gust":11.41,"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"clouds":44,"pop":0,"uvi":2},{"dt":1642953600,"sunrise":1642939657,"sunset":1642974378,"moonrise":1642996200,"moonset":1642950780,"moon_phase":0.69,"temp":{"day":30.06,"min":20.75,"max":34.66,"night":28.69,"eve":32.25,"morn":21.11},"feels_like":{"day":25.72,"night":24.17,"eve":32.25,"morn":21.11},"pressure":1016,"humidity":69,"dew_point":20.75,"wind_speed":4.09,"wind_deg":159,"wind_gust":12.19,"weather":[{"id":600,"main":"Snow","description":"light snow","icon":"13d"}],"clouds":97,"pop":0.51,"snow":1.54,"uvi":2},{"dt":1643040000,"sunrise":1643026011,"sunset":1643060855,"moonrise":0,"moonset":1643038500,"moon_phase":0.72,"temp":{"day":27.81,"min":23.04,"max":30.11,"night":23.04,"eve":28.29,"morn":23.54},"feels_like":{"day":23.02,"night":18.14,"eve":22.69,"morn":17.71},"pressure":1007,"humidity":61,"dew_point":15.75,"wind_speed":5.03,"wind_deg":303,"wind_gust":12.59,"weather":[{"id":600,"main":"Snow","description":"light snow","icon":"13d"}],"clouds":100,"pop":0.39,"snow":0.17,"uvi":2},{"dt":1643126400,"sunrise":1643112362,"sunset":1643147332,"moonrise":1643086800,"moonset":1643126400,"moon_phase":0.75,"temp":{"day":16.27,"min":12.99,"max":21.29,"night":12.99,"eve":19.53,"morn":17.78},"feels_like":{"day":4.8,"night":2.25,"eve":8.24,"morn":8.17},"pressure":1015,"humidity":42,"dew_point":-4.04,"wind_speed":10.29,"wind_deg":292,"wind_gust":20.4,"weather":[{"id":803,"main":"Clouds","description":"broken clouds","icon":"04d"}],"clouds":66,"pop":0,"uvi":2}]}'
            time.sleep(10)
        else:
            try:
                r = requests.get(my_url)
                response = r.text
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log("There was an error retrieving the weather: {}".format(e))
                response = ""
                lock.release()

        lock = threading.Lock()
        lock.acquire()
        self.weather = self.parse_json_weather(json.loads(response))
        self.weather_updated = True
        self.helper.log(self.config, "done getting weather!")
        lock.release()

    def update(self, tick, canvas):
        if int(time.time() * 1000) - self.timer > self.config["update_interval"] * 1000 * 60:
            self.download_weather()
            self.timer = int(time.time() * 1000)

        if self.weather_updated:
            if len(self.weather["current"]) > 0:
                canvas.fill(self.config["background"])

                current_weather_surface, start_y = self.get_current_weather_surface(self.weather)
                canvas.blit(current_weather_surface, (0, 0))

                _line_buffer = canvas.get_height()/10
                _line_color = pygame.Vector3(self.config["foreground"])
                _line_color = _line_color.lerp(self.config["background"], .4)
                _line_width = 2

                # TODAY'S DATE ------------
                day = '{} {dt.day} {dt.year}'.format(self.weather["current"]["date"].strftime("%A, %b"),
                                                     dt=self.weather["current"]["date"])

                surf_todays_date = self.small_font.render(day, True, self.config["foreground"])
                canvas.blit(surf_todays_date, (self.screen_width/4 - surf_todays_date.get_width()/2,
                                               start_y/2 - surf_todays_date.get_height()/2))

                # ALL THE REST -------------
                future_hours_surface = self.get_future_hours_surface(self.weather)
                future_days_surface = self.get_future_days_surface(self.weather)

                surface_size = _line_buffer + future_hours_surface.get_height() + future_days_surface.get_height()
                y = current_weather_surface.get_height() - surface_size - \
                    ((current_weather_surface.get_height() - surface_size)/2)

                canvas.blit(future_hours_surface, (self.screen_width/2, y))

                y += future_hours_surface.get_height() + _line_buffer
                canvas.blit(future_days_surface, (self.screen_width/2, y))

                # Center vertical divider
                pygame.draw.line(canvas, _line_color,
                                 (self.screen_width / 2 - 1, _line_buffer),
                                 (self.screen_width / 2 - 1, self.screen_height - _line_buffer), _line_width)
                # Right horizontal divider
                pygame.draw.line(canvas, _line_color,
                                 (self.screen_width / 2 + _line_buffer, self.screen_height / 2 - 1),
                                 (self.screen_width - _line_buffer, self.screen_height / 2 - 1), _line_width)

            self.last_canvas = canvas.copy()
        else:
            if self.last_canvas is not None:
                canvas.blit(self.last_canvas, (0, 0))
            else:
                if self.config["apikey"] == "":
                    surf_error = self.small_font.render("Add your API key first!", True, self.config["foreground"])
                else:
                    surf_error = self.small_font.render("Retrieving weather...", True, self.config["foreground"])

                canvas.fill(self.config["background"])
                canvas.blit(surf_error, (canvas.get_width()/2 - surf_error.get_width()/2,
                                         canvas.get_height()/2 - surf_error.get_height()/2))

        return canvas

    def get_future_hours_surface(self, weather):
        now = datetime.datetime.now()
        hour1 = now + datetime.timedelta(hours=1)
        surf_hours1 = None
        for i in weather["hourly"]:
            weather_hour = weather["hourly"][i]
            if weather_hour["date"].day == hour1.day and weather_hour["date"].month == hour1.month and \
                    weather_hour["date"].year == hour1.year and weather_hour["date"].hour == hour1.hour:
                surf_hours1 = self.make_hour_surface(weather_hour, self.smaller_font, (self.screen_width / 2) / 3)
                break
        hour2 = now + datetime.timedelta(hours=3)
        surf_hours2 = None
        for i in weather["hourly"]:
            weather_hour = weather["hourly"][i]
            if weather_hour["date"].day == hour2.day and weather_hour["date"].month == hour2.month and \
                    weather_hour["date"].year == hour2.year and weather_hour["date"].hour == hour2.hour:
                surf_hours2 = self.make_hour_surface(weather_hour, self.smaller_font, (self.screen_width / 2) / 3)
                break
        hour3 = now + datetime.timedelta(hours=5)
        surf_hours3 = None
        for i in weather["hourly"]:
            weather_hour = weather["hourly"][i]
            if weather_hour["date"].day == hour3.day and weather_hour["date"].month == hour3.month and \
                    weather_hour["date"].year == hour3.year and weather_hour["date"].hour == hour3.hour:
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
        future_hours_surface.fill(self.config["background"])

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
            if weather_day["date"].day == day1.day and weather_day["date"].month == day1.month and \
                    weather_day["date"].year == day1.year:
                surf_day1 = self.make_day_surface(weather_day, self.smaller_font, (self.screen_width / 2) / 3)
                break
        day2 = now + datetime.timedelta(days=2)
        surf_day2 = None
        for i in weather["daily"]:
            weather_day = weather["daily"][i]
            if weather_day["date"].day == day2.day and weather_day["date"].month == day2.month and \
                    weather_day["date"].year == day2.year:
                surf_day2 = self.make_day_surface(weather_day, self.smaller_font, (self.screen_width / 2) / 3)
                break
        day3 = now + datetime.timedelta(days=3)
        surf_day3 = None
        for i in weather["daily"]:
            weather_day = weather["daily"][i]
            if weather_day["date"].day == day3.day and weather_day["date"].month == day3.month and \
                    weather_day["date"].year == day3.year:
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
        future_days_surface.fill(self.config["background"])

        if surf_day1 is not None:
            future_days_surface.blit(surf_day1, (0, 0))
        if surf_day2 is not None:
            future_days_surface.blit(surf_day2, (future_days_surface.get_width()/3, 0))
        if surf_day3 is not None:
            future_days_surface.blit(surf_day3, ((future_days_surface.get_width()/3)*2, 0))

        return future_days_surface

    def get_current_weather_surface(self, weather):
        _line_buffer = 20
        current_weather_surface = pygame.Surface((self.screen_width/2, self.screen_height))
        current_weather_surface.fill(self.config["background"])

        # CURRENT WEATHER ICON -----
        surf_current_icon = pygame.image.load(weather["current"]["icon_path"]).convert_alpha()

        ratio = (current_weather_surface.get_width()*1.0/3) / surf_current_icon.get_width()
        icon_height = int(surf_current_icon.get_height() * ratio)
        surf_current_icon = pygame.transform.scale(surf_current_icon,
                                                   (int((surf_current_icon.get_width()*1.0)*ratio), icon_height))

        # CURRENT TEMP --------
        surf_current_temp = self.large_font.render(u"{}{}".format(str(weather["current"]["temp"]), u'\N{DEGREE SIGN}'),
                                                   True, self.config["foreground"])

        # CURRENT HIGH/LOW -------------
        surf_degree_sign = self.small_font.render(u"{}".format(u'\N{DEGREE SIGN}'), True, self.config["foreground"])
        surf_current_high = self.small_font.render(str(weather["current"]["high"]), True, self.config["foreground"])
        surf_current_low = self.small_font.render(str(weather["current"]["low"]), True, self.config["foreground"])

        if surf_current_low.get_width() > surf_current_high.get_width():
            highlow_width = surf_current_low.get_width()
        else:
            highlow_width = surf_current_high.get_width()

        highlow_width += surf_degree_sign.get_width()*3

        surf_current_highlow = pygame.Surface((highlow_width,
                                               surf_current_low.get_height() + surf_current_high.get_height() + 10))
        surf_current_highlow.fill(self.config["background"])

        surf_current_highlow.blit(surf_current_high,
                                  (surf_current_highlow.get_width()/2 - surf_current_high.get_width()/2, 0))
        surf_current_highlow.blit(surf_degree_sign,
                                  (surf_current_highlow.get_width() / 2 - surf_current_high.get_width() / 2 +
                                   surf_current_high.get_width(), 0))

        _line_color = pygame.Vector3(self.config["foreground"])
        _line_color = _line_color.lerp(self.config["background"], .75)

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
        surf_rain_chance = self.make_small_icon_text(self.config["weather_icons"]["rain"],
                                                     "{}%".format(weather["current"]["rain"]), self.small_font)
        # WIND SPEED ICON -------------
        surf_wind_speed = self.make_small_icon_text(self.config["weather_icons"]["wind_speed"],
                                                    "{}mph".format(weather["current"]["wind_speed"]), self.small_font)
        # HUMIDITY ICON -------------------
        surf_humidity = self.make_small_icon_text(self.config["weather_icons"]["humidity"],
                                                  "{}%".format(weather["current"]["humidity"]), self.small_font)

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

        surf_sunrise = self.make_small_icon_text(self.config["weather_icons"]["sunrise"], sunrise_time, self.small_font)

        # SUNSET ICON -----------
        sunset_time = weather["current"]["sunset"].strftime("%I:%M %p")
        if sunset_time[:1] == "0":
            sunset_time = sunset_time[1:]

        surf_sunset = self.make_small_icon_text(self.config["weather_icons"]["sunset"], sunset_time, self.small_font)

        if surf_sunset.get_height() > surf_sunrise.get_height():
            row3_height = surf_sunset.get_height()
        else:
            row3_height = surf_sunrise.get_height()

        surface_size = (_line_buffer * 2) + row1_height + row2_height + row3_height
        start_y = current_weather_surface.get_height() - surface_size - ((current_weather_surface.get_height() -
                                                                          surface_size)/2)

        y = start_y
        current_weather_surface.blit(surf_current_icon, (current_weather_surface.get_width() / 2 -
                                                         surf_current_icon.get_width() / 2, y))

        _large_icon_spacer = 20
        x = current_weather_surface.get_width() / 2 + surf_current_icon.get_width() / 2 + _large_icon_spacer
        current_weather_surface.blit(surf_current_temp, (x, y + row1_height/2 - surf_current_temp.get_height()/2))
        x = current_weather_surface.get_width() / 2 - surf_current_icon.get_width() / 2 - _large_icon_spacer - \
            surf_current_highlow.get_width()
        current_weather_surface.blit(surf_current_highlow, (x, y + row1_height/2 - surf_current_highlow.get_height()/2))

        y += row1_height + _line_buffer

        _small_icon_spacer = 30
        x = current_weather_surface.get_width() / 2 - surf_wind_speed.get_width()/2 - surf_rain_chance.get_width() - \
            _small_icon_spacer
        current_weather_surface.blit(surf_rain_chance, (x, y))
        x = current_weather_surface.get_width() / 2 - surf_wind_speed.get_width()/2
        current_weather_surface.blit(surf_wind_speed, (x, y))
        x = current_weather_surface.get_width() / 2 + surf_wind_speed.get_width()/2 + _small_icon_spacer
        current_weather_surface.blit(surf_humidity, (x, y))

        y += row2_height + _line_buffer

        x = current_weather_surface.get_width() / 2 - _small_icon_spacer/2 - surf_sunrise.get_width()
        current_weather_surface.blit(surf_sunrise, (x,  y))
        x = current_weather_surface.get_width() / 2 + _small_icon_spacer/2
        current_weather_surface.blit(surf_sunset, (x, y))

        return current_weather_surface, start_y

    def make_small_icon_text(self, icon_path, icon_text, font):
        _buffer = 5
        surf_icon = pygame.image.load(os.path.join(self.icons_folder, icon_path)).convert_alpha()
        surf_text = font.render(icon_text, True, self.config["foreground"])

        # Icons have a lot of spacing around them. Let's tighten it up a bit
        _icon_size_buffer = 15
        _temp_text_height = surf_text.get_height() + _icon_size_buffer
        ratio = _temp_text_height * 1.0 / surf_icon.get_height()
        icon_width = int(surf_icon.get_width() * ratio)

        surf_icon = pygame.transform.scale(surf_icon, (icon_width, _temp_text_height))

        surf_icon_complete = pygame.Surface((surf_icon.get_width() + _buffer + surf_text.get_width(),
                                             _temp_text_height))
        surf_icon_complete.fill(self.config["background"])
        surf_icon_complete.blit(surf_icon, (0, 0))
        surf_icon_complete.blit(surf_text, (surf_icon.get_width() + _buffer, surf_icon_complete.get_height()/2 -
                                            surf_text.get_height()/2))

        return surf_icon_complete

    def make_day_surface(self, day_weather, font, width):
        _temp_icon_factor = 2  # the smaller this value, the larger the icon
        # DAY TEXT ---------
        surf_day_text = font.render(day_weather["date"].strftime("%a"), True, self.config["foreground"])

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
                                True, self.config["foreground"])

        # RAIN CHANCE ---------------------
        surf_rain = self.make_small_icon_text(self.config["weather_icons"]["rain"],
                                              "{}{}".format(day_weather["rain"], "%"), font)

        # WIND SPEED --------------
        surf_wind_speed = self.make_small_icon_text(self.config["weather_icons"]["wind_speed"],
                                                    "{}{}".format(day_weather["wind_speed"], "mph"), font)

        _line_spacer = 10
        height = (_line_spacer * 4) + surf_day_text.get_height() + surf_temp_icon.get_height() + \
            surf_temp.get_height() + surf_rain.get_height() + surf_wind_speed.get_height()
        surf_day = pygame.Surface((width, height))
        surf_day.fill(self.config["background"])

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

        surf_hour_text = font.render(weather_time, True, self.config["foreground"])

        # TEMP ICON ------
        surf_temp_icon = pygame.image.load(hour_weather["icon_path"]).convert_alpha()
        ratio = (width*1.0/_temp_icon_factor) / surf_temp_icon.get_width()
        icon_height = int(surf_temp_icon.get_height() * ratio)
        surf_temp_icon = pygame.transform.scale(surf_temp_icon, (int((surf_temp_icon.get_width()*1.0)*ratio),
                                                                 icon_height))

        # TEMP TEXT ---------
        surf_temp = font.render(u"{}{}".format(str(hour_weather["temp"]), u'\N{DEGREE SIGN}'), True,
                                self.config["foreground"])

        # RAIN CHANCE ----------
        surf_rain = self.make_small_icon_text(self.config["weather_icons"]["rain"],
                                              "{}{}".format(hour_weather["rain"], "%"), font)

        # WIND SPEED -------------
        surf_wind_speed = self.make_small_icon_text(self.config["weather_icons"]["wind_speed"],
                                                    "{}{}".format(hour_weather["wind_speed"], "mph"), font)

        _line_spacer = 10
        height = (_line_spacer*4) + surf_hour_text.get_height() + surf_temp_icon.get_height() + \
            surf_temp.get_height() + surf_rain.get_height() + surf_wind_speed.get_height()
        surf_hour = pygame.Surface((width, height))
        surf_hour.fill(self.config["background"])

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

        if icon_key in self.config["weather_icons"]:
            current_icon_path = os.path.join(self.icons_folder, self.config["weather_icons"][icon_key])
        else:
            current_icon_path = os.path.join(self.icons_folder, self.config["weather_icons"]["unknown"])

        weather["current"].update({"icon_path": current_icon_path})
        weather["current"].update({"temp": 0})
        if "current" in json_weather:
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
                    if "weather" in i:
                        for j in range(len(i["weather"])):
                            if "description" in i["weather"][j]:
                                weather["current"]["description"] = \
                                    upper_first_char(i["weather"][0]["description"].split(".")[0])
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

                    if icon_key in self.config["weather_icons"]:
                        daily_icon_path = os.path.join(self.icons_folder, self.config["weather_icons"][icon_key])
                    else:
                        daily_icon_path = os.path.join(self.icons_folder, self.config["weather_icons"]["unknown"])

                    daily.update({"icon_path": daily_icon_path})

                    daily.update({"high": int(i["temp"]["max"]) if "temp" in i and "max" in i["temp"] else "0"})
                    daily.update({"low": int(i["temp"]["min"]) if "temp" in i and "min" in i["temp"] else "0"})
                    daily.update({"rain": int(i["pop"]) if "pop" in i else "0"})
                    daily.update({"wind_speed": int(i["wind_speed"]) if "wind_speed" in i else "0"})

                    daily.update({"description": ""})
                    if "weather" in i:
                        for j in range(len(i["weather"])):
                            if "description" in i["weather"][j]:
                                daily["description"] = upper_first_char(i["weather"][0]["description"].split(".")[0])
                                break

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

                if icon_key in self.config["weather_icons"]:
                    hourly_icon_path = os.path.join(self.icons_folder, self.config["weather_icons"][icon_key])
                else:
                    hourly_icon_path = os.path.join(self.icons_folder, self.config["weather_icons"]["unknown"])

                hourly.update({"icon_path": hourly_icon_path})
                hourly.update({"temp": int(i["temp"]) if "temp" in i else 0})
                hourly.update({"rain": int(i["pop"]) if "pop" in i else 0})
                hourly.update({"wind_speed": int(i["wind_speed"]) if "wind_speed" in i else 0})
                hourly.update({"description": ""})
                if "weather" in i:
                    for j in range(len(i["weather"])):
                        if "description" in i["weather"][j]:
                            hourly["description"] = upper_first_char(i["weather"][0]["description"].split(".")[0])
                            break

                weather["hourly"].update({i["dt"]: hourly})

        return weather


def upper_first_char(val):
    return "{}{}".format(val[:1].capitalize(), val[1:])
