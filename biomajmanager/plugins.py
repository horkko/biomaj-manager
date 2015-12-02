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
        pm = PluginManager()
        self.pm = pm
        pm.setPluginPlaces([self.config.get('MANAGER', 'plugins_dir')])
        pm.setCategoriesFilter({"Base": BMPlugin})
        pm.collectPlugins()
        user_plugins = [ ]
        # Load user wanted plugin(s)
        for plugin in self.config.get('PLUGINS', 'plugins.list').split(','):
            plugin.strip()
            user_plugins.append(plugin)
            
        # This means that all plugins must inherits from BMPlugin
        for pluginInfo in pm.getPluginsOfCategory("Base"):
            if pluginInfo.name in user_plugins:
                if not pluginInfo.is_activated:
                    pm.activatePluginByName(pluginInfo.name)
                setattr(self, pluginInfo.name, pluginInfo.plugin_object)
                pluginInfo.plugin_object.set_config(config)


class BMPlugin(IPlugin):
    """
    Base plugin class for BioMAJ manager
    """

    def get_name(self):
        return "BioMAJ Manager base plugin"

    def set_config(self, config):
        """
        Set BioMAJ manager config
        """
        self.config = config
                
