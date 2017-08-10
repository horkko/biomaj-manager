"""Plugins mechanism to load user defined method"""
from biomajmanager.utils import Utils
from yapsy.PluginManager import PluginManager
from yapsy.IPlugin import IPlugin
import os
__author__ = 'Emmanuel Quevillon'


class Plugins(object):

    """Plugin class for BioMAJ Manager"""

    CATEGORY = 'MANAGER'

    def __init__(self, manager=None, name=None):
        """
        Create the plugin object

        :param manager: Manager instance
        :type manager: :class:`biomajmanager.manager.Manager`
        :param name: Name of the plugin to load. [DEFAULT: load all plugins]
        :type name: String
        :raises SystemExit: If 'manager' arg is not given
        :raises SystemExit: If 'PLUGINS' section not found in
                            :py:data:`manager.properties`
        :raises SystemExit: If 'plugins.dir' not set in
                            :py:data:`manager.properties`
        :raises SystemExit: If 'plugins.list' not set in
                            :py:data:`manager.properties`
        :raises SystemExit: If 'plugins.dir' does not exist
        """
        self.pm = None
        self.name = None
        self.config = None
        self.manager = None
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
        plugin_manager = PluginManager(
            directories_list=[self.config.get('MANAGER', 'plugins.dir')],
            categories_filter={Plugins.CATEGORY: BMPlugin})
        plugin_manager.collectPlugins()
        self.pm = plugin_manager
        self.name = name
        user_plugins = []

        # Load user wanted plugin(s)
        for plugin in self.config.get('PLUGINS', 'plugins.list').split(','):
            plugin.strip()
            # We need to lower the plugin name
            user_plugins.append(plugin)

        # This means that all plugins must inherits from BMPlugin
        for pluginInfo in plugin_manager.getPluginsOfCategory(Plugins.CATEGORY):
            Utils.verbose("[manager] plugin name => %s" % pluginInfo.name)
            if pluginInfo.name in user_plugins:
                if not pluginInfo.is_activated:
                    Utils.verbose("[manager] plugin %s activated"
                                  % pluginInfo.name)
                    plugin_manager.activatePluginByName(pluginInfo.name)
                setattr(self, pluginInfo.name, pluginInfo.plugin_object)
                pluginInfo.plugin_object.set_config(self.config)
                pluginInfo.plugin_object.set_manager(self.manager)


class BMPlugin(IPlugin):

    """Base plugin class for BioMAJ manager"""

    def get_name(self):
        """Get the name of the plugin. Based on the class name"""
        return self.__class__.__name__

    def get_config(self):
        """
        Get the BioMAJ manager config as object

        :return: configparser instance
        :rtype: :class:'configparser`
        """
        return self.config

    def get_manager(self):
        """
        Get the BioMAJ manager instance

        :return: Manager
        :rtype: :class:`biomaj.manager.Manager`
        """
        return self.manager

    def set_config(self, config):
        """Set BioMAJ manager config object"""
        self.config = config

    def set_manager(self, manager):
        """Set BioMAJ manager config object"""
        self.manager = manager
