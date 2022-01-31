from lib.plugin import Plugin


class FullScreenPlugin(Plugin):
    def __init__(self, helper, canvas, plugin_path, app_plugin_config):
        super(FullScreenPlugin, self).__init__(helper, canvas, plugin_path, app_plugin_config)

    def handle_click(self, pos):
        pass
