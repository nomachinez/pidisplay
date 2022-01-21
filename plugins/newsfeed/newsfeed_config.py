""" All globals go here """
CONFIG = {
    "update_interval": 30,  # Minutes

    "feeds": [
        {"name": "The Hacker News", "icon": "the_hacker_news.png", "url": "https://feeds.feedburner.com/TheHackersNews"},
        {"name": "BBC",             "icon": "bbc.png", "url": "https://feeds.bbci.co.uk/news/rss.xml?edition=us"},
        {"name": "CNN",             "icon": "cnn.png", "url": "http://rss.cnn.com/rss/edition_us.rss"},
        {"name": "Hacker News",     "icon": "hacker_news.png", "url": "https://hnrss.org/newest"},
    ],

    "slack_webhook": "",  # Enter your webhook from Slack here

    "icon_size": 25,
    "icons_folder": "./icons/",
    "background": (0, 0, 0),

    "max_articles": 10,

    "feed_title_font_size": 30,  # 30,
    "item_title_font_size": 35,  # 35,
    "item_date_font_size": 25,  # 25,
    "item_desc_font_size": 25,  # 25,

    "feed_title_foreground": (128, 128, 128),
    "item_title_foreground": (200, 200, 200),
    "item_date_foreground": (128, 128, 128),
    "item_desc_foreground": (128, 128, 128),

    "foreground": (200, 200, 200),

    "screen_margin": 15,

}
