""" All globals go here """
CONFIG = {
    "tickers": ["msft", "goog", "ETH-USD", "BTC-USD", "ADA-USD"],
    "update_interval": 15,  # Minutes
    # The higher, the faster the scroll. Also, make this negative to scroll right or positive to scroll left
    "speed": 2,

    "background": (0, 0, 0),
    "foreground": (200, 200, 200),
    "down_background": (64, 0, 0),
    "down_foreground": (200, 200, 200),
    "up_background": (0, 64, 0),
    "up_foreground": (200, 200, 200),
    "test_mode": False,
}
