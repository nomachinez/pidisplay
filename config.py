""" All globals go here """
CONFIG = {
    "debug": False,

    "fullscreen_mode": True,
    # If FULLSCREEN_MODE = True, should we use the current resolution or the resolution defined below?
    "fullscreen_uses_current_resolution": True,

    "plugins_folder": "./plugins",

    # If you want PiDisplay to start on a specific plugin, add the NAME here (from __init__.py)
    # If this is empty then it will start at whichever was the first plugin loaded
    # You will get an error if this is set wrong
    "start_plugin": "NewsFeed",

    "screen_width": 1024,  # 1360,
    "screen_height": 600,  # 768,
    "top_bar_height": 35,
    "bottom_bar_height": 20,

    # Set in seconds, 0 means don't autoswitch
    "autoswitch_timer": .25 * 60,

    "application_sysfont": "Segoe UI",

    "message_font_size": 40,
    "message_popup_fade_time": 2,  # seconds
    "message_popup_fade_delay": 1,  # seconds

    # Make sure this is an even number
    "frames_per_second": 30,

    "screenshot_dir": "./screenshots/",
    "take_screenshots": False,

    "doubleclick_delay": 400,
}
