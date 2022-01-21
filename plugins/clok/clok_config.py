""" All globals go here """
from collections import namedtuple

Location = namedtuple("Location", ["start", "color"])

CONFIG = {
    "needle_width": 5,
    "needle_color": (200, 0, 0),  # Red-ish

    # start, color, in order from left to right. Use zero-padded hours and minutes and 24 hour time
    "locations": [
        Location(start="00:00PM", color=(32, 32,  32)),
        Location(start="06:00AM", color=(49, 115, 153)),
        Location(start="08:00AM", color=(25, 123, 222)),
        Location(start="12:00PM", color=(39, 146, 207)),
        Location(start="13:00PM", color=(25, 123, 222)),
        Location(start="18:00PM", color=(39, 146, 207)),
        Location(start="19:00PM", color=(25, 123, 222)),
        Location(start="20:30PM", color=(49, 115, 153)),
        Location(start="23:00PM", color=(32, 32,  32)),
    ],
}
