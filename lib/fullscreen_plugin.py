from lib.plugin import Plugin


class FullScreenPlugin(Plugin):
    def __init__(self, helper, canvas, plugin_path, app_plugin_config):
        super(FullScreenPlugin, self).__init__(helper, canvas, plugin_path, app_plugin_config)

    def update(self, tick, fps):
        raise NotImplementedError("All plugins must override the update function!")

    def handle_click(self, pos):
        pass
