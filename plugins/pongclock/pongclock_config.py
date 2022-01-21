
CONFIG = {
    # 24 or 12,
    "hour_type": 24,
    # This dramatically increases the CPU and doesn't really look good,
    "show_scanlines": False,

    ##########################################################
    # If you change the resolution you may want to tweak these
    ##########################################################
    # 7 TFT settings
    # ------------------------
    "center_divider_block_height": 10,
    "center_divider_block_width": 5,
    "center_divider_block_spacing": 15,
    "screen_margin": 4,

    "paddle_height": 50,
    "paddle_width": 10,

    "ball_width": 10,

    "digit_height": 70,
    "digit_width": 50,
    "digit_spacing": 10,
    "digit_line_width": 10,

    # This is for the ball randomness and deflection when it hits the paddle
    "min_horizontal_velocity": 3,
    "max_horizontal_velocity": 8,
    "min_vertical_velocity": 3,
    "max_vertical_velocity": 8,

    ######################################################
    # 1920x1280 Settings
    # -------------------------
    # "center_divider_block_height": 10,
    # "center_divider_block_width": 5,
    # "center_divider_block_spacing": 15,
    # "screen_margin": 4,

    # "paddle_height": 120,
    # "paddle_width": 20,

    # "ball_width": 20,

    # "digit_height": 150,
    # "digit_width": 80,
    # "digit_spacing": 40,
    # "digit_line_width": 20,

    # This is for the ball randomness and deflection when it hits the paddle
    # "max_horizontal_velocity": 16,
    # "min_horizontal_velocity": 6,
    # "max_vertical_velocity": 16,
    # "min_vertical_velocity": 6,
    ##########################################################

    # increase this to make the paddles SLOWER or vice versa
    "paddle_speed_factor": 10,

    # (0, 200, 0) is a neat monochrome color for the foreground...
    "foreground": (200, 200, 200),
    "background": (0, 0, 0),
    "scanline_color": (0, 0, 0, 128),
}
