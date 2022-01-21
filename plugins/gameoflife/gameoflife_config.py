""" All globals go here """
CONFIG = {
    # How many cells wide?
    "world_width": 100,
    # -1 = automatically determine how many cells tall
    "world_height": -1,
    # or manually set it
    # "world_height": 50,

    # Usually it stabilizes after a while so the world will reset after this many lifetimes
    "max_generations": 100,

    "show_generation": True,
    "generation_color": (200, 200, 0),
    "generation_size": 40,

    # Each cell has STARTING_POPULATION_CHANCE of being alive on start
    "starting_population_chance": 12,

    # (0, 200, 0) is a neat monochrome color for the foreground...
    "foreground": (200, 200, 200),
    "background": (0, 0, 0),

    # Change the color of the life depending on the age
    "age_lives": True,
    "foreground_old": (200, 200, 0),
    # Number between 1 and 100. How fast do you want the lives to age?
    "foreground_fade_step": 10,
}
