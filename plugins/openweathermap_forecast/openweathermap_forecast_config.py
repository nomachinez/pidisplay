""" All globals go here """
CONFIG = {
    "update_interval": 30,  # Minutes
    "apikey": "",  # Enter your API key here

    # Find your longitude and latitude here: https://www.latlong.net/
    # Or Google Maps
    "longitude": "-118.243683",
    "latitude": "34.052235",
    "unit_type": "imperial",  # "imperial" (US), "metric" (everyone else), or "standard" (Kelvin and meters/sec)
    "language": "en",  # 2-letter language code (https://openweathermap.org/api/one-call-api#multi)

    "icons_folder": "./icons/custom/",
    "background": (0, 0, 0),
    "foreground": (255, 255, 255),
    "smaller_font_size": 40,  # 40,
    "small_font_size": 50,  # 50,
    "large_font_size": 100,  # 100,

    "weather_icons": {
        "01d":      "01d.png",
        "01n":      "01n.png",
        "02d":      "02d.png",
        "02n":      "02n.png",
        "03d":      "03d.png",
        "03n":      "03n.png",
        "04d":      "04d.png",
        "04n":      "04n.png",
        "09d":      "09d.png",
        "09n":      "09n.png",
        "10d":      "10d.png",
        "10n":      "10n.png",
        "11d":      "11d.png",
        "11n":      "11n.png",
        "13d":      "13d.png",
        "13n":      "13n.png",
        "50d":      "50d.png",
        "50n":      "50n.png",
        "unknown":  "unknown.png",
        "rain": "chance_of_rain.png",
        "wind_speed": "wind_speed.png",
        "sunrise": "sunrise.png",
        "sunset": "sunset.png",
        "humidity": "humidity.png",
    },
    "test_mode": False,
}
