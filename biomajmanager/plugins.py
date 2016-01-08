from __future__ import print_function

from biomajmanager.utils import Utils
from yapsy.PluginManager import PluginManager
from yapsy.IPlugin import IPlugin
import os

class Plugins(object):

    CATEGORY = 'MANAGER'

    def __init__(self, manager=None):
        """
        Create the plugin object
        :param manager: Manager instance
        :type config: biomajmanager.manager
        :return:
        """
        if not manager:
            Utils.error("'manager' is required")
        self.manager = manager
        self.config = self.manager.config

        if not self.config.has_section('PLUGINS'):
            Utils.error("Can't load plugins, no section found!")
        if not self.config.has_option('MANAGER', 'plugins.dir'):
            Utils.error("plugins.dir not defined!")
        if not self.config.has_option('PLUGINS', 'plugins.list'):
            Utils.error("plugins.list is not defined!")

        if not os.path.isdir(self.config.get('MANAGER', 'plugins.dir')):
            Utils.error("Can't find plugins.dir")
        pm = PluginManager(directories_list=[self.config.get('MANAGER', 'plugins.dir')],
                           categories_filter={Plugins.CATEGORY: BMPlugin})
        pm.collectPlugins()
        self.pm = pm
        user_plugins = [ ]

        # Load user wanted plugin(s)
        for plugin in self.config.get('PLUGINS', 'plugins.list').split(','):
            plugin.strip()
            # We need to lower the plugin name
            user_plugins.append(plugin)

        # This means that all plugins must inherits from BMPlugin
        for pluginInfo in pm.getPluginsOfCategory(Plugins.CATEGORY):
            Utils.verbose("[manager] plugin name => %s" % pluginInfo.name)
            if pluginInfo.name in user_plugins:
                if not pluginInfo.is_activated:
                    Utils.verbose("[manager] plugin %s activated" % pluginInfo.name)
                    pm.activatePluginByName(pluginInfo.name)
                setattr(self, pluginInfo.name, pluginInfo.plugin_object)
                pluginInfo.plugin_object.set_config(self.config)
                pluginInfo.plugin_object.set_manager(self.manager)


class BMPlugin(IPlugin):
    """
    Base plugin class for BioMAJ manager
    """

    def get_name(self):
        return self.__class__.__name__

    def get_config(self):
        """
        Get the BioMAJ manager config as object
        """
        return self.config

    def get_manager(self):
        """
        Get the BioMAJ manager instance
        :return: biomajmanager.manager
        """
        return self.manager

    def set_config(self, config):
        """
        Set BioMAJ manager config object
        """
        self.config = config

    def set_manager(self, manager):
        """
        Set BioMAJ manager config object
        """
        self.manager = manager
