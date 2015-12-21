from __future__ import print_function

from biomajmanager.utils import Utils
from yapsy.PluginManager import PluginManager
from yapsy.IPlugin import IPlugin


class Plugins(object):

    def __init__(self, config):
        """
        Create the plugin object
        :param config: Configuration object
        :type config: biomaj.config object
        :return:
        """
        if not config:
            Utils.error("'config' is required.")
        self.config = config

        if not self.config.has_section('PLUGINS'):
            Utils.error("Can't load plugins, no section found!")
        if not self.config.has_option('MANAGER', 'plugins.dir'):
            Utils.error("plugins.dir not defined!")
        if not self.config.has_option('PLUGINS', 'plugins.list'):
            Utils.error("plugins.list is not defined!")

        pm = PluginManager()
        self.pm = pm
        pm.setPluginPlaces([self.config.get('MANAGER', 'plugins.dir')])
        # Set our Base plugin (BMPPlugin) as category of "Base"
        # All inherited plugins will be then pushed in the same category
        pm.setCategoriesFilter({"Base": BMPlugin})
        pm.collectPlugins()
        user_plugins = [ ]

        # Load user wanted plugin(s)
        for plugin in self.config.get('PLUGINS', 'plugins.list').split(','):
            plugin.strip()
            # We need to lower the plugin name
            user_plugins.append(plugin.lower())

        # This means that all plugins must inherits from BMPlugin
        for pluginInfo in pm.getPluginsOfCategory("Base"):
            Utils.verbose("[manager] plugin name => %s" % pluginInfo.name)
            if pluginInfo.name in user_plugins:
                if not pluginInfo.is_activated:
                    pm.activatePluginByName(pluginInfo.name)
                setattr(self, pluginInfo.name.lower(), pluginInfo.plugin_object)
                pluginInfo.plugin_object.set_config(config)


class BMPlugin(IPlugin):
    """
    Base plugin class for BioMAJ manager
    """

    def get_name(self):
        return self.__class__.__name__

    def set_config(self, config):
        """
        Set BioMAJ manager config object
        """
        self.config = config

    def get_config(self):
        """
        Get the BioMAJ manager config as object
        """
        return self.config
                
