import configparser
import os


class Plugin:
    def __init__(self, helper, canvas, plugin_path, app_plugin_config):
        self.helper = helper
        self.canvas = canvas
        self.debug = app_plugin_config.getboolean("debug")
        self.plugin_config = Plugin.get_config(plugin_path, app_plugin_config, type(self).__name__)
        self.screen_width = self.canvas.get_width()
        self.screen_height = self.canvas.get_height()

        self.READY_TO_SWITCH = False

        self.just_in = False

    def update(self, tick, fps):
        raise NotImplementedError("All plugins must override the update function!")

    @staticmethod
    def get_config(plugin_path, app_plugin_config, plugin_config_section):
        config = configparser.RawConfigParser()
        config.read(os.path.abspath(os.path.join(plugin_path, "config.ini")))
        for i in list(app_plugin_config):
            config[plugin_config_section][i] = app_plugin_config[i]
        return config[plugin_config_section]


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].just_in = True
        return cls._instances[cls]
