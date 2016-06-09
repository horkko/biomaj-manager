"""Main class of BioMAJ Manager"""
import datetime
import re
import os
import select
import subprocess
import time
import humanfriendly
import shutil

from biomaj.bank import Bank
from biomaj.config import BiomajConfig
from biomaj.mongo_connector import MongoConnector
from biomajmanager.utils import Utils
from biomajmanager.plugins import Plugins
from biomajmanager.decorators import bank_required, user_granted


class Manager(object):

    """Manager class, the swiss knife around BioMAJ3"""

    # Simulation mode
    simulate = False
    # Verbose mode
    verbose = False
    # Default date format string
    SAVE_BANK_LINE_PATTERN = "%-20s\t%-30s\t%-20s\t%-20s\t%-20s\n"

    def __init__(self, bank=None, cfg=None, global_cfg=None):
        """
        Manager instance creation

        :param bank: Bank name
        :param cfg: Manager Configuration file (manager.properties)
        :type cfg: str
        :param global_cfg: Global configuration file (global.properties)
        :type global_cfg: str
        :raises SystemExit: If problem reading configuration file
        """
        # Our bank
        self.bank = None
        # The root installation of biomaj3
        self.root = None
        # Where to find global.properties
        self.config_file = None
        # Configuration object
        self.config = None
        # Where data are located
        self.bank_prod = None
        # Plugins object reference
        self.plugins = None
        # Current release of the bank
        self._current_release = None
        # Next release of the bank
        self._next_release = None
        # Previous release of the bank
        self._previous_release = None
        # Some messages to buffer
        self.messages = []

        try:
            # Specific configuration file
            self.config = Manager.load_config(cfg=cfg, global_cfg=global_cfg)
            if self.config.has_option('GENERAL', 'data.dir'):
                self.bank_prod = self.config.get('GENERAL', 'data.dir')
        except SystemExit as err:
            Utils.error("Can't load configuration file. Exit with code %s" % str(err))

        if bank is not None:
            self.bank = Bank(bank, no_log=True)
            if self.bank.config.get('data.dir'):
                self.bank_prod = self.bank.config.get('data.dir')

    @staticmethod
    def load_config(cfg=None, global_cfg=None):
        """
        Load biomaj-manager configuration file (manager.properties).
        
        It uses BiomajConfig.load_config() to first load global.properties and determine
        where the config.dir is. manager.properties must be located at the same place as
        global.properties or file parameter must point to manager.properties

        :param cfg: Path to config file to load
        :type cfg: str
        :param global_cfg:
        :type global_cfg:
        :return: ConfigParser object
        :rtype: :class:`configparser.SafeParser`
        :raises SystemExit: If can load configuaration file
        """
        # Load global.properties (or user defined global_cfg)
        Utils.verbose("[manager] Loading Biomaj global configuration file")
        try:
            BiomajConfig.load_config(config_file=global_cfg)
        except Exception as err:
            Utils.error("Error while loading biomaj config: %s" % str(err))

        conf_dir = os.path.dirname(BiomajConfig.config_file)
        if not cfg:
            cfg = os.path.join(conf_dir, 'manager.properties')
        if not os.path.isfile(cfg):
            Utils.error("Can't find config file %s" % cfg)

        Utils.verbose("[manager] Reading manager configuration file")
        BiomajConfig.global_config.read(cfg)
        return BiomajConfig.global_config

    @bank_required
    def bank_info(self):
        """
        Prints some information about the bank

        :return: Output from :py:func:`biomaj.bank.get_bank_release_info`
        :rtype: dict of list
        """
        return self.bank.get_bank_release_info(full=True)

    @bank_required
    def bank_is_published(self):
        """
        Check if a bank is already published or not.

        :return: Boolean
        :rtype: bool
        """
        if 'current' in self.bank.bank and self.bank.bank['current']:
            return True
        return False

    @bank_required
    def can_switch(self):
        """
        Check if a bank can be updated and put into production as 'current'

        :return: Boolean
        :rtype: bool
        """
        # Bank is updating?
        if self.bank.is_locked():
            if Manager.get_verbose():
                Utils.verbose("[%s] Can't switch, bank is being updated" % self.bank.name)
            return False
        # If there is no published bank yet, ask the user to do it first. Can't switch to new release version
        # if no bank is published yet
        if not self.bank_is_published():
            if Manager.get_verbose():
                Utils.verbose("[%s] There's no published bank yet. Publish it first" % self.bank.name)
            return False

        # Bank construction failed?
        if self.last_session_failed():
            # A message should be printed from the function
            return False

        if not self.update_ready():
            if Manager.get_verbose():
                Utils.verbose("[%s] Can't switch, bank is not ready" % self.bank.name)
            return False
        return True

    @bank_required
    def current_release(self):
        """
        Search for the current available release ('online')

        :return: Release number if available or None
        :rtype: str or None
        """
        current = None
        release = None
        if self._current_release is not None:
            return self._current_release
        # First se search if a current release is set
        if 'current' in self.bank.bank and self.bank.bank['current']:
            session = self.get_session_from_id(self.bank.bank['current'])
            if session and 'release' in session and session['release']:
                release = session['release']
            elif session and 'remoterelease' in session and session['remoterelease']:
                release = session['remoterelease']
            if release:
                current = release
        if current:
            self._current_release = current
            return str(current)
        else:
            return current

    @bank_required
    def formats(self, flat=False):
        """
        Check the "supported formats" for a specific bank.

        This is done simply by getting the variable 'db.packages' from the bank
        configuration file.

        :param flat: flatten the list of format for this bank
                     default False
        :type flat: bool
        :return: List of supported format(s) as:
                if flat is True:
                { 'tool1': [list of version], 'tool2': [list of version] ...}
                if flat is False
                ['tool1@version', 'tool1@version', 'tool2@version' ....]
        :rtype: list
        """
        formats = []
        if flat:
            formats = {}
        if self.get_bank_packages():
            packages = self.get_bank_packages()
            for package in packages:
                (_, name, version) = package.split('@')
                if flat:
                    if name not in formats:
                        formats[name] = []
                    formats[name].append(version)
                else:
                    formats.append("@".join([name, version]))

        return formats

    @bank_required
    def formats_as_string(self):
        """
        Returns the formats as a List of string

        :return: List of formats for bank
        :rtype: list
        """
        return self.formats(flat=True)

    @bank_required
    def get_bank_data_dir(self):
        """
        Returns the complete path where the bank data_dir is located

        :return: Path to the current bank data dir
        :rtype: str
        :raises SystemExit: If 'current release' cannot be found in 'production' db field
        :raises SystemExit: If 'production.data_dir' not found in 'production' document
        :raises SystemExit: If no current release is found
        """
        release = self.current_release()
        if release:
            prod = self.bank.get_production(release)
            if not prod:
                Utils.error("Can't find production for release %s" % str(release))
            elif 'data_dir' in prod:
                return os.path.join(prod['data_dir'], self.bank.name)
            else:
                Utils.error("Can't get current production directory, 'data_dir' " +
                            "missing in production document field")
        else:
            Utils.error("Can't get current production directory: 'current_release' not available")

    @staticmethod
    def get_bank_list(visibility="public"):
        """
        Get the list of bank available from the database

        :param visibility: Type of bank visibility, default to 'public'. Supported ['all', 'public', 'private']
        :type visibility: str
        :return: List of bank name.
        :rtype: list
        :raises SystemExit: If visibility argument is not one of ('all', 'public', 'private')
        :raises SystemExit: If cannot connect to MongoDB
        """
        if visibility not in ['all', 'public', 'private']:
            Utils.error("Bank visibility '%s' not supported. Only one of ['all', 'public', 'private']" % visibility)
        # Don't read config again
        if BiomajConfig.global_config is None:
            try:
                BiomajConfig.load_config()
            except Exception as err:
                Utils.error("Problem loading biomaj configuration: %s" % str(err))
        try:
            bank_list = []
            if MongoConnector.db is None:
                from pymongo.errors import PyMongoError
                # We  surrounded this block of code with a try/except because there's a behavior
                # difference between pymongo 2.7 and 3.2. 2.7 immediately raised exception if it
                # cannot connect, 3.2 waits for a database access to connect to the server
                MongoConnector(BiomajConfig.global_config.get('GENERAL', 'db.url'),
                               BiomajConfig.global_config.get('GENERAL', 'db.name'))
            banks = MongoConnector.banks.find({'properties.visibility': visibility}, {'name': 1, '_id': 0})
            for bank in banks:
                # Avoid document without bank name
                if 'name' in bank:
                    bank_list.append(bank['name'])
            bank_list.sort()
            return bank_list
        except PyMongoError as err:
            Utils.error("Can't connect to MongoDB: %s" % str(err))

    @bank_required
    def get_bank_packages(self):
        """
        Retrieve the list of linked packages for the current bank

        :return: List of defined packages for a bank ('pack@<pack_name>@<pack_version>')
        :rtype: list
        """
        # Check db.packages is set for the current bank
        packages = []
        if not self.bank.config.get('db.packages'):
            if self.get_verbose():
                Utils.warn("[%s] db.packages not set!" % self.bank.name)
        else:
            packs = self.bank.config.get('db.packages').replace('\\', '').replace('\n', '').strip().split(',')
            for pack in packs:
                packages.append('pack@' + pack)
        return packages

    @bank_required
    def get_bank_sections(self, tool=None):
        """
        Get the 'supported' indexes sections available for the bank.
        
        Each defined indexes section may have its own subsection(s).
        By default, it returns the info as a dictionary of lists.

        :param tool: Name of the index to search section(s) for
        :type tool: str
        :return: {'nuc': {'dbs': ['db1', 'db2', ...], 'sections': [ ...]}, 'pro': {'dbs': [ ... ], 'sections': ... }
        :rtype: dict
        :raises SystemExit: If not tool name is given
        """
        if tool is None:
            Utils.error("A tool name is required to retrieve section(s) info")

        sections = {}
        for key in ['nuc', 'pro']:
            dbname = 'db.%s.%s' % (tool, key)
            secname = dbname + '.sections'
            sections[key] = {'dbs': [], 'sections': []}
            if self.bank.config.get(dbname):
                for db in self.bank.config.get(dbname).replace('\\', '').replace('\n', '').split(','):
                    if db and db != '':
                        sections[key]['dbs'].append(db)
            if self.bank.config.get(secname):
                for db in self.bank.config.get(secname).replace('\\', '').replace('\n', '').split(','):
                    if db and db != '':
                        sections[key]['sections'].append(db)
        return sections

    @bank_required
    def get_current_link(self):
        """
        Return the the path of the bank 'current' version symlink

        :return: Complete path of 'current' link
        :rtype: str
        """
        return os.path.join(self.bank.config.get('data.dir'),
                            self.bank.name,
                            'current')

    @bank_required
    def get_current_proddir(self):
        """
        Get the path of the current production bank

        :return: Path to the current production bank
        :rtype: str
        :raises SystemExit: If no 'current release' cannot be found in 'production' db field
        :raises SystemExit: If 'production.data_dir' not found in 'production' document
        :raises SystemExit: If no current release is found
        """
        release = self.current_release()
        if release:
            prod = self.bank.get_production(release)
            if not prod:
                Utils.error("Can't find production for release %s" % str(release))
            elif 'data_dir' in prod and 'prod_dir' in prod:
                return os.path.join(prod['data_dir'], self.bank.name, prod['prod_dir'])
            else:
                Utils.error("Can't get current production directory, 'prod_dir' or 'data_dir' " +
                            "missing in production document field")
        else:
            Utils.error("Can't get current production directory: 'current_release' not available")

    def get_config_regex(self, section='GENERAL', regex=None, with_values=True):
        """
        Pick up values from the configuration file based on a regular expression.

        By default it returns the corresponding list of values found. If with_values
        set to False, it returns only the keys.

        :param section: Section to read, default 'GENERAL'
        :type section: str
        :param regex: Regex to search the key with
        :type regex: str
        :param with_values: Returns values instead of keys, default True
        :type with_values: bool
        :return: Sorted List of values found
        :rtype: list
        :raises SystemExit: If not 'regex' arg given
        """
        if not regex:
            Utils.error("Regular expression required to get config regex")
        pattern = re.compile(regex)
        keys = dict(self.config.items(section))
        keys = sorted(keys)
        values = []
        for key in keys:
            if re.search(pattern, key):
                if self.config.has_option(section, key):
                    if with_values:
                        values.append(self.config.get(section, key))
                    else:
                        values.append(key)
        return values

    def get_current_user(self):
        """
        Get the user name from the environment

        :return: Logname or None if not found
        :rtype: str or None
        """
        return self._current_user()

    @staticmethod
    def get_formats_for_release(path=None):
        """
        Get all the formats supported for a bank (path).

        :param path: Path of the release to search in
        :type path: str (path)
        :return: Sorted formats
        :rtype: list
        :raises SystemExit: If no path given as arg
        """
        formats = []
        if not path:
            Utils.error("A path is required")
        if not os.path.exists(path):
            Utils.warn("Path %s does not exist" % path)
            return formats

        for path_dir, dirs, _ in os.walk(path):
            if path_dir == path or not len(dirs) or os.path.basename(path_dir) == 'flat':
                continue
            for d in dirs:
                formats.append('@'.join(['pack', os.path.basename(path_dir), d or '-']))
        formats.sort()
        return formats


    @bank_required
    def get_future_link(self):
        """
        Return the the path of the bank 'current' version symlink

        :return: Complete path of 'future_release' link
        :rtype: str
        """
        return os.path.join(self.bank.config.get('data.dir'),
                            self.bank.name,
                            'future_release')

    @bank_required
    def get_last_production_ok(self):
        """
        Search for the last release in production which ran ok and which is not 'online' (current)

        :return: 'production' document from the database
                 None if production is empty
        :rtype: dict
        :raises SystemExit: If no 'session' key found in 'production' db field
        :raises SystemExit: If no 'production' key found in bank's collection
        """
        last_release = None
        current_id = None

        if 'production' not in self.bank.bank:
            Utils.error("No 'production' found in database!")
        productions = self.bank.bank['production']
        if len(productions) == 0:
            return last_release

        last_production = productions[-1]
        # Then we have a problem
        if 'session' not in last_production:
            Utils.error("We could not find a 'session' in last production")
        # If we already have a current release published we take into account
        if 'current' in self.bank.bank and self.bank.bank['current']:
            current_id = self.bank.bank['current']

        if current_id is None:
            last_release = last_production
        elif last_production['session'] != current_id:
            last_release = last_production
        return last_release

    @bank_required
    def get_pending_sessions(self):
        """
        Request the database to check if some session(s) is/are pending to complete

        :return: List of dict {'release'=release, 'id': id} or None
        :rtype: list or None
        """
        pending = None
        if 'pending' in self.bank.bank and len(self.bank.bank['pending']) > 0:
            pending = self.bank.bank['pending']
        return pending

    def get_production_dir(self):
        """
        Get the production.dir setting

        :return: Path to the production.dir
        :rtype: str
        :raise SystemExit: If 'production.dir' is not set
        """
        if not self.config.has_option('MANAGER', 'production.dir'):
            Utils.error("'production.dir' not set")
        return self.config.get('MANAGER', 'production.dir')

    @bank_required
    def get_published_release(self):
        """
        Check a bank has a published release

        :return: Release number or None
        :rtype: str
        :raises SystemExit: If no 'remoterelease' key found in published release document
        """
        if self.bank_is_published():
            session = self.get_session_from_id(self.bank.bank['current'])
            if session and 'remoterelease' in session and session['remoterelease']:
                return str(session['remoterelease'])
            else:
                Utils.error("[%s] Can't find a 'remoterelease' for session %s" % (self.bank.name, session['id']))
        return None

    @bank_required
    def get_session_from_id(self, session_id):
        """
        Retrieve a bank session from its id

        :param session_id: Session id
        :type session_id: str
        :return: Session or None
        :rtype: dict or None
        """
        sess = None
        if not session_id:
            Utils.error("A session id is required")
        if 'sessions' in self.bank.bank and self.bank.bank['sessions']:
            for session in self.bank.bank['sessions']:
                if session_id == session['id']:
                    sess = session
        return sess

    @staticmethod
    def get_simulate():
        """
        Get the value of the simulate mode

        :return: Simulate mode status
        :rtype: bool
        """
        return Manager.simulate

    @staticmethod
    def get_verbose():
        """
        Get the value of the verbose mode

        :return: Verbose mode status
        :rtype: bool
        """
        return Manager.verbose

    @bank_required
    def has_current_link(self, link=None):
        """
        Check if the 'current' link is there

        :param link: Link path to check, otherwise get from 'get_current_link'
        :type: str
        :return: If a current link is present or not
        :rtype: bool
        """
        if link is None:
            link = self.get_current_link()
        return os.path.islink(link)

    @bank_required
    def has_future_link(self, link=None):
        """
        Check if the 'future_release' link is there

        :param link: Link path to check, otherwise get from 'get_future_link'
        :type: str
        :return: If a future_link is present or not
        :rtype: bool
        """
        if link is None:
            link = self.get_future_link()
        return os.path.islink(link)

    @bank_required
    def has_formats(self, fmt=None):
        """
        Checks either the bank supports 'format' or not

        :param fmt: Format to check
        :type fmt: str
        :return: If a format is present for a bank
        :rtype: bool
        :raises SystemExit: If 'fmt' args is not given
        """
        if not fmt:
            Utils.error("Format is required")
        fmts = self.formats(flat=True)
        if fmt in fmts:
            return True
        return False

    @bank_required
    def history(self):
        """
        Get the releases history of a bank from the database and build a Mongo like document in json

        :return: history + extra info to be included into bioweb (Institut Pasteur only)
        :rtype: list
        :raises SystemExit: If 'production' key not found in bank docuement
        :raises SystemExit: If 'session' key not found in bank docuement
        """
        productions = sessions = None
        if 'production' in self.bank.bank and self.bank.bank['production']:
            productions = self.bank.bank['production']
        else:
            Utils.error("No production found for bank %s" % self.bank.name)

        if 'sessions' in self.bank.bank and self.bank.bank['sessions']:
            sessions = self.bank.bank['sessions']
        else:
            Utils.error("No sessions found for bank %s" % self.bank.name)

        history = []
        packages = self.get_bank_packages()
        description = self.bank.config.get('db.fullname').replace('"', '').strip()
        bank_type = self.bank.config.get('db.type').split(',')
        bank_format = self.bank.config.get('db.formats').split(',')
        status = 'unpublished'
        fmt = "%Y-%m-%d %H:%M"
        for prod in sorted(productions, key=lambda k: k['session'], reverse=True):
            if 'current' in self.bank.bank:
                if prod['session'] == self.bank.bank['current']:
                    status = 'online'
                else:
                    status = 'deprecated'
            hid = '@'.join(['bank', self.bank.name, str(prod['remoterelease']),
                            str(Utils.time2datefmt(prod['session']))])
            history.append({'_id': hid,
                            'type': 'bank',
                            'name': self.bank.name,
                            'version': str(prod['remoterelease']),
                            'publication_date': str(Utils.time2datefmt(prod['session'], fmt=fmt)),
                            'removal_date': None,
                            'bank_type': bank_type,
                            'bank_format': bank_format,
                            'packageVersions': packages,
                            'description': description,
                            'status': status
                            })

        for sess in sorted(sessions, key=lambda k: k['id'], reverse=True):
            # Don't repeat production item stored in sessions
            new_id = '@'.join(['bank',
                               self.bank.name,
                               str(sess['remoterelease']),
                               str(Utils.time2datefmt(sess['id']))])
            # Don't take into account no deleted session
            if 'deleted' not in sess:
                continue
            history.append({'_id': new_id,
                            'type': 'bank',
                            'name': self.bank.name,
                            'version': str(sess['remoterelease']),
                            'publication_date': str(Utils.time2datefmt(sess['last_update_time'], fmt=fmt)),
                            'removal_date': str(Utils.time2datefmt(sess['deleted'], fmt=fmt))
                            if 'deleted' in sess else None,
                            'bank_type': bank_type,
                            'bank_formats': bank_format,
                            'packageVersions': packages,
                            'description': description,
                            'status': 'deleted'
                            })
        return history

    @bank_required
    def last_session_failed(self):
        """
        Check if the last building bank session failed, base on 'last_update_session' field.

        - If we find a pending session, we return False and warn the user to finish it
        - Then, we look into session and check that the last session.status.over is True/False

        :return: If the last update session failed
        :rtype: bool
        :raises SystemExit: If the session id of 'last_update_session' is not found in 'sessions' document
        """
        has_failed = False
        last_update_id = None

        if 'last_update_session' in self.bank.bank and self.bank.bank['last_update_session']:
            last_update_id = self.bank.bank['last_update_session']
        # If no last_update_session, this mean not last session ran. We return False
        else:
            return has_failed

        # We have to be careful as pending session have over.status to false
        pending = self.get_pending_sessions()

        # Check the last updated session is not pending. We consider pending session has failed because not ended
        if pending and last_update_id:
            for pend in pending:
                if pend['id'] == last_update_id:
                    if Manager.get_verbose():
                        Utils.warn("[%s] The last updated session is pending (release %s). Complete workflow first,"
                                   " or update bank" % (self.bank.name, pend['release']))
                    has_failed = True
                    return has_failed

        # We then search in the session, base on 'last_update_session' field
        session = self.get_session_from_id(last_update_id)
        if session is None:
            Utils.error("[%s] Can't find last_update_session %s in sessions! Please fix it!"
                        % (self.bank.name, str(last_update_id)))
        # If session terminated OK, status.over should be True
        # biomaj >= 3.0.14, new field 'workflow_status' which tells if the update workflow went ok
        # We do not count on status.over anymore, we have new field 'workflow_status'
        if 'workflow_status' in session:
            has_failed = not session['workflow_status']
        else:
            has_failed = True
        return has_failed

    def list_plugins(self):
        """
        Read plugins set from the config manager.properties

        :return: List of plugins name
        :rtype: list
        """
        plugins_list = []
        if self.config.has_section('PLUGINS'):
            plugins = self.config.get('PLUGINS', 'plugins.list')
            for plugin in plugins.split(','):
                if plugin != '':
                    plugins_list.append(plugin)
        return plugins_list

    def load_plugins(self):
        """
        Load all the plugins and activate them from manager.properties (plugins.list property)

        :returns: Instance of biomajmanager.plugins.Plugins
        :rtype: :class:`biomajmanager.plugins.Plugins`
        """
        self.plugins = Plugins(manager=self)
        return self.plugins

    def next_switch_date(self, week=None):
        """
        Returns the date of the next bank switch

        This method is used to guess when the next bank switch will occur. By default, we consider switching to new
        bank release every other sunday on even week. However, you can configure it with 'switch.week' parameter
        from 'manager.properties' or even pass it as an argument to the method.

        :param week: Week to perform the switch (Supported ['even', 'odd', 'each'])
        :type week: str
        :return: Next bank switch date as datetime.datetime
        :rtype: :class:`datetime.datetime`
        :raises SystemExit: If 'week' arg value is none of ('even', 'odd', 'each')
        """
        if week is None:
            if self.config.has_option('MANAGER', 'switch.week'):
                week = self.config.get('MANAGER', 'switch.week')
            else:
                Utils.error("Week type is required")

        if week != 'even' and week != 'odd' and week != 'each':
            Utils.error("Wrong week type %s, supported ['even', 'odd', 'each']" % str(week))

        week_number = datetime.datetime.today().isocalendar()[1]
        today = datetime.datetime.today()
        modulo = not week_number % 2

        if week == 'even':
            week = 1 if modulo else 0
        elif week == 'odd':
            week = 0 if modulo else 1
        else:
            # For each week, it must be the same week as today
            week = 1

        # Each week
        if week:
            return today + datetime.timedelta(days=(7 - today.isoweekday()))
        else:
            return today + datetime.timedelta(days=(14 - today.isoweekday()))

    @bank_required
    def next_release(self):
        """
        Get the next bank release version from the database if available

        :return: Next release or None
        :rtype: str
        :raises SystemExit: If no production ok found
        :raises SystemExit: If no session found for the next release we are looking for
        """
        next_release = None
        session = None
        production = None
        if self._next_release:
            return self._next_release
        production = self.get_last_production_ok()
        if production is None:
            Utils.error("No 'production' release found searching for next release")
        session = self.get_session_from_id(production['session'])
        if session is not None:
            # Pending sessions are excluded
            if 'workflow_status' in session and session['workflow_status']:
                if 'release' in session:
                    next_release = session['release']
                elif 'remoterelease' in session:
                    next_release = session['remoterelease']
                else:
                    Utils.error("Can't find 'release' or 'remoterelease' field in session")
        else:
            Utils.error("Can't find release in session '%s'" % str(production['session']))

        self._next_release = next_release
        return self._next_release

    def reset_releases(self):
        """ Reset current and next release variables to None"""
        self._current_release = None
        self._next_release = None
        return

    @user_granted
    def restart_stopped_jobs(self, args=None):
        """
        Restarts jobs stopped by calling 'stop_running_jobs'.

        This must be set in manager.properties configuration file, section 'JOBS'.
        You must set 'restart.stopped.jobs.exe' [MANDATORY] and 'restart.stopped.jobs.args'
        [OPTIONAL]

        :param args: List of args to pass to the command
        :type args: list of string
        :return: If command executed ok
        :rtype: bool
        """
        return self._submit_job('restart.stopped.jobs', args=args)

    @user_granted
    def save_banks_version(self, bank_file=None):
        """
        Save versions of bank when switching bank version (publish)

        :param bank_file: Path to save banks version (String)
        :return: True if all is ok
        :rtype: bool
        :raises SystemExit: If dirname cannot be created
        :raises SystemExit: If file cannot be opened
        """
        if not bank_file:
            bank_file = os.path.join(self.bank_prod,
                                     'doc',
                                     'versions',
                                     'version.' + datetime.datetime.now().strftime("%Y-%m-%d"))
        # Check path exists
        directory = os.path.dirname(bank_file)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as err:
                Utils.error("Can't create destination directory %s: %s" % (directory, str(err)))

        try:
            banks = Manager.get_bank_list()
            FILE_PATTERN = Manager.SAVE_BANK_LINE_PATTERN
            with open(bank_file, mode='w') as fv:
                for bank in banks:
                    bank = Bank(name=bank, no_log=True)
                    if 'current' in bank.bank and bank.bank['current'] and 'production' in bank.bank:
                        for prod in bank.bank['production']:
                            if bank.bank['current'] == prod['session']:
                                # bank / release / creation / size / remote server
                                file_line = FILE_PATTERN % (bank.name, "Release " + prod['remoterelease'],
                                                            Utils.time2datefmt(prod['session']),
                                                            str(prod['size']) if 'size' in prod and prod['size']
                                                                              else 'NA',
                                                            bank.config.get('server'))
                                if Manager.simulate:
                                    Utils._print(file_line)
                                else:
                                    fv.write(file_line)
        except Exception as e:
            Utils.error("Can't access file: %s" % str(e))
        if Manager.get_verbose():
            Utils.verbose("Bank versions saved in %s" % bank_file)
        return True

    def set_bank(self, bank=None):
        """
        Set a bank for the current Manager

        :param bank: Bank instance
        :type bank: :class:`biomaj.bank.Bank`
        :return: True if correctly set with expected instance
        :rtype: bool
        """
        if not bank or bank is None:
            return False
        if isinstance(bank, Bank):
            self.bank = bank
            self.reset_releases()
            return True
        return False

    def set_bank_from_name(self, name=None):
        """
        Set a bank from a bank name

        :param name: Name of the bank to set
        :type name: str
        :return: True if bank set ok
        :rtype: bool
        :raises SystemExit: If bank object creation failed
        """
        if not name or name is None:
            return False
        try:
            bank = Bank(name=name, no_log=True)
        except Exception as err:
            Utils.error("Problem with bank %s: %s" % (name, str(err)))
        return self.set_bank(bank=bank)

    @bank_required
    def set_sequence_count(self, seq_file=None, seq_count=None, release=None):
        """
        Set the number of sequence found in a file. This is set in the production field under the name of 'files_infos'

        This method is used to have some more info about a particular file while displaying status of a bank release.
        At the same time, it also set the size of the file.

        :param seq_file: File path to set info
        :type seq_file: str
        :param seq_count: Number of sequence(s) contained in this file
        :type seq_count: int
        :param release: Production release number to set file info
        :type release: str
        :return: True if all ok
        :rtype: bool
        :raise SystemExit: If seq_file not set
        :raise SystemExit: If seq_count not set
        :raise SystemExit: If release not set
        :raise SystemExit: If file does not exist
        """
        if seq_file is None:
            Utils.error("A file path is required")
        if not os.path.exists(seq_file):
            Utils.error("File '%s' not found" % str(seq_file))
        if seq_count is None:
            Utils.error("A sequence number is required")
        if release is None:
            Utils.error("A release is required")
        file_size = humanfriendly.format_size(os.path.getsize(seq_file))
        res = self.bank.banks.find({'name': self.bank.name, 'production.release': release,
                                    'production.files_info.name': seq_file})
        if res.count() == 0:
            res = self.bank.banks.update_one({'name': self.bank.name,
                                              'production.release': release},
                                             {'$push': {'production.$.files_info':
                                                            {'name': seq_file,
                                                             'seq_count': seq_count,
                                                             'size': file_size}}},
                                             upsert=True)
        else:
            production = self.bank.banks.find({'name': self.bank.name, 'production.release': release},
                                              {'production.$.files_info': 1})
            for prod in production:
                for p in prod['production']:
                    cnt = 0
                    for info in p['files_info']:
                        if info['name'] == seq_file:
                            p['files_info'][cnt].update({'name': seq_file, 'seq_count': seq_count, 'size': file_size})
                            res = self.bank.banks.update_one({'name': self.bank.name, 'production.release': release},
                                                             {'$set': {'production.$.files_info': p['files_info']}})
                            break
                        cnt += 1
        if Manager.get_verbose():
            matched = res.matched_count if res.matched_count else 0
            modified = res.modified_count if res.modified_count else 0
            Utils.ok("[%s] Documents matched: %d, documents modified: %d" %
                     (self.bank.name, matched, modified))
        return True
        

    @staticmethod
    def set_simulate(value):
        """
        Set/Unset simulate mode

        :param value: Value to set
        :type value: bool
        :return: Boolean
        :rtype: bool
        """
        if value:
            Manager.simulate = True
        else:
            Manager.simulate = False
        return Manager.simulate

    @staticmethod
    def set_verbose(value):
        """
        Set/Unset verbose mode

        :param value: Value to set
        :type value: bool
        :return: Boolean
        :rtype: bool`
        """
        if value:
            Manager.verbose = True
        else:
            Manager.verbose = False
        return Manager.verbose

    @bank_required
    def show_pending_sessions(self):
        """
        Check if some session are pending

        :return: Results from get_pending_sessions()
        :rtype: list
        """
        return self.get_pending_sessions()

    def show_need_update(self, visibility='public'):
        """
        Check bank(s) that need to be updated (can be switched)

        :param visibility: Bank visibility, default 'public'
        :type visibility: str
        :return: List of banks requiring update
        :rtype: list
        """
        banks = []
        if self.bank:
            if self.can_switch():
                banks.append({'name': self.bank.name,
                              'current_release': self.current_release(),
                              'next_release': self.next_release()})
            return banks

        banks_list = Manager.get_bank_list(visibility=visibility)
        for bank in banks_list:
            self.set_bank_from_name(name=bank)
            if self.can_switch():
                banks.append({'name': bank,
                              'current_release': self.current_release(),
                              'next_release': self.next_release()})
        return banks

    @user_granted
    def stop_running_jobs(self, args=None):
        """
        Stop running jobs using bank(s).

        This calls an external script which must be set in the manager.properties
        configuration file, section JOBS.
        You must set 'stop.running.jobs.exe' [MANDATORY] and 'stop.running.jobs.args'
        [OPTIONAL]

        :param args: List of args to pass to the commande
        :type args: list of string
        :return: If job executed ok
        :rtype: bool
        """
        return self._submit_job('stop.running.jobs', args=args)

    @bank_required
    def synchronize_db(self, udate=None):
        """
        Synchronize database with data on disk (data.dir/dbname)

        This method intends to synchronize disk state with info in database. It may appaer that we have
        some extra data displayed and stored in the database ('production' field) that do not exists on
        disk. This might be due to a 'Ctrl-C' during a bank update of iterative updates without 'publish'
        call between each iteration.
        
        :param udate: User date to set for 'sessions.deleted'
        :type udate: str
        :return: State of the operation
        :rtype: bool
        :raise SystemExit: If some configuration are not set
        """
        for option in ['synchrodb.delete.dir', 'synchrodb.set.sessions.deleted']:
            if not self.config.has_option('MANAGER', option):
                Utils.error("Option '%s' not set" % str(option))

        if self.config.get('MANAGER', 'synchrodb.delete.dir') not in ['auto', 'manual']:
            Utils.error("'synchrodb.delete.dir' value '%s' not supported. Available %s" %
                        (self.config.get('MANAGER', 'synchrodb.delete.dir'), str(['auto', 'manual'])))

        if self.config.get('MANAGER', 'synchrodb.set.sessions.deleted') not in ['now', 'userdate']:
            Utils.error("'set.sessions.deleted' value '%s' not supported. Available %s" %
                        (self.config.get('MANAGER', 'synchrodb.set.sessions.deleted'), str(['now', 'userdate'])))

        auto_delete = False
        deleted_time = time.time()

        if self.config.get('MANAGER', 'synchrodb.delete.dir') == 'auto':
            auto_delete = True
        # If simulate mode
        auto_delete = not Manager.get_simulate()

        if self.config.get('MANAGER', 'synchrodb.set.sessions.deleted') == 'userdate':
            if udate is None:
                Utils.error("Missing 'udate' parameter")
            deleted_time = datetime.strptime(udate, "%d %b %Y")

        bank_data_dir = self.get_bank_data_dir()
        # Taken from http://stackoverflow.com/questions/7781545/how-to-get-all-folder-only-in-a-given-path-in-python
        releases_dir = {x:1 for x in next(os.walk(bank_data_dir))[1]}
        pendings = {}
        if 'pending' in self.bank.bank:
            pendings = {x['id']:1 for x in self.bank.bank['pending']}
        productions = self.bank.bank['production']
        tasks_to_do = []
        last_run = None
        if 'last_update_session' in self.bank.bank:
            last_run = self.get_session_from_id(self.bank.bank['last_update_session'])

        for prod in productions:
            # If release dir not found in production, we remove it from disk
            # and set sessions.deleted
            Utils.verbose("Checking prod %s" % (prod['prod_dir']))
            if prod['prod_dir'] in releases_dir:
                Utils.verbose("Prod %s found on disk too" % prod['prod_dir'])
                # We then check everything ok in 'sessions'
                session = self.get_session_from_id(prod['session'])
                if 'workflow_status' in session and not session['workflow_status']:
                    if prod['session'] not in pendings:
                        Utils.warn("[%s] Release %s ok in production and on disk, but sessions.workflow_status is False!"
                                   % (self.bank.name, prod['prod_dir']))
                elif 'deleted' in session and session['deleted']:
                    Utils.warn("[%s] Session %s marked as deleted, should not!"
                               % (self.bank.name, session['id']))
                else:
                    releases_dir.pop(prod['prod_dir'])
            else:
                # Here we need to delete entry from production
                Utils.verbose("Added %s to be deleted" % prod['prod_dir'])
                # Need to delete this release directory and set time deleted into db (sessions.deleted)
                tasks_to_do.append({'dir': os.path.join(bank_data_dir, prod['prod_dir']),
                                    'time': deleted_time,
                                    'key': 'production',
                                    'release': prod['release'],
                                    'sid': prod['session']})
                
        if len(tasks_to_do):
            seen = False
            for task in tasks_to_do:
                if auto_delete:
                    # Do delete on disk
                    if os.path.isdir(task['dir']):
                        try:
                            Utils.verbose("Removing %s ... " % str(task['dir']))
                            shutil.rmtree(task['dir'])
                        except OSError as err:
                            Utils.error("Can't delete '%s': %s" % (str(task['dir']), str(err)))
                    else:
                        Utils.warn("%s not found" % task['dir'])
                    Utils.verbose("Updating production (session id %f) ... " % task['sid'])
                    self.bank.banks.update({'name': self.bank.name},
                                           {'$pull': {'production': {'release': task['release'],
                                                                     'session': task['sid']}
                                                      }})
                    if task['time']:
                        Utils.verbose("Updating sessions (id %f) ... " % task['sid'])
                        # In case 'sessions.deleted' already set don't change it
                        session = self.bank.banks.find({'name': self.bank.name, 'sessions.id': task['sid'],
                                                        'sessions.deleted': {'$exists': False}},
                                                       {'sessions.$': 1, '_id': 0})
                        if not session.count():
                            self.bank.banks.update({'name': self.bank.name, 'sessions.id': task['sid']},
                                                   {'$set': {'sessions.$.deleted': deleted_time}})
                else:
                    if not seen:
                        Utils.ok("You need to:")
                        seen = True
                    if os.path.isdir(task['dir']):
                        Utils.ok("- rm -rf %s" % str(task['dir']))
                    else:
                        Utils.ok("- remove %s entry for release %s" % (task['key'], str(task['release'])))
                    if 'time' in task:
                        Utils.ok("- set sessions[id=%f].deleted to %s" % (task['sid'], str(task['time'])))

        if len(releases_dir):
            # Ctrl-C during bank update
            seen = False
            pendings = []
            if 'pending' in self.bank.bank:
                pendings = {x['release']:x['id'] for x in self.bank.bank['pending']}
            for release in releases_dir:
                if release == 'current' or release == 'future_release':
                    continue
                pr = release[len(self.bank.name) + 1:]
                # Sometime, last update session create a directory on disk. In such case,
                # we do not remove this directory, it will be use for next update
                if pr == last_run['release']:
                    continue
                if not seen:
                    Utils.warn("Some directories found on disk and not in production:")
                    seen = True

                if auto_delete:
                    try:
                        path = os.path.join(bank_data_dir, str(release))
                        Utils.verbose("Removing extra dir %s ... " % path)
                        shutil.rmtree(path)
                        if pr in pendings:
                            Utils.verbose("Remonving pending release %s ... " % str(pr))
                            self.bank.banks.update({'name': self.bank.name},
                                                   {'$pull': {'pending': {'release': pr}}})
                    except OSError as err:
                        Utils.error("Can't delete '%s': %s" % (path, str(err)))
                else:
                    Utils.warn("- %s" % str(release))
                    if pr in pendings:
                        Utils.warn("- Remove pending %s from database" % str(pr))
        return True

    @bank_required
    def clean_sessions(self):
        """
        Clean sessions in database
        """
        last_run = None
        pendings = {}
        tasks_to_do = []
        auto_clean = not Manager.get_simulate()

        if 'last_update_session' in self.bank.bank:
            last_run = self.bank.bank['last_update_session']
        if 'pending' in self.bank.bank['pending']:
            pendings = {x['id']:1 for x in self.bank.bank['pending']}
        productions = {x['session']:1 for x in self.bank.bank['production']}

        bank_data_dir = self.get_bank_data_dir()
        sessions = self.bank.bank['sessions']
        for session in sessions:
            field_name = 'sessions'
            id_key = 'id'
            if last_run and last_run == session['id']:
                continue
            # If session marked as deleted we don't care about it unless it is found on disk
            if 'deleted' in session:
                if os.path.exists(os.path.join(bank_data_dir, session['dir_version'] + "_" + session['release'])):
                    Utils.warn("[%s] Release %s, session %f marked as deleted (%f) but directory %s found disk" %
                               (self.bank.name, session['release'], session['id'], session['deleted'],
                                session['dir_version'] + "_" + session['release']))
                elif session['id'] in productions:
                    Utils.warn("[%s] Release %s, session %f marked as deleted (%f) but found in production" %
                               (self.bank.name, session['release'], session['id'], session['deleted']))
                    field_name = 'production'
                    id_key = 'session'
                else:
                    continue
            elif session['id'] in productions:
                continue
            if 'workflow_status' in session and not session['workflow_status']:
                if session['id'] in pendings:
                    continue
            tasks_to_do.append({'release': session['release'], 'sid': session['id'], 'type': field_name, 'key': id_key})

        if len(tasks_to_do):
            cleaned = 0
            for task in tasks_to_do:
                if auto_clean:
                    self.bank.banks.update({'name': self.bank.name},
                                           {'$pull': {task['type']: {task['key']: task['sid'], 'release': task['release']}}})
                    cleaned += 1
                else:
                    Utils.ok(task)
            if auto_clean:
                Utils.ok("[%s] %d session(s) cleaned" % (self.bank.name, cleaned))
        return True

    @bank_required
    def update_ready(self):
        """
        Check the bank release is ready to be published.

        We first check we have a last session recorded using 'last_update_session'. It must be here, otherwise, warning.
        Then, if we've got a 'current', we check 'current' is not equal to'last_update_session', meaning no update has
        been performed since last publish. If 'current' is not equal to 'last_update_session', we need to search for
        the last update that went ok and is ok for publishing.
        Otherwise, we warn the user and we return false.

        :return: fF a bank is ready to be updated to its next release
        :rtype: bool
        """
        ready = False

        if 'last_update_session' not in self.bank.bank:
            if self.get_verbose():
                Utils.warn("No last session recorded")
            return ready
        last_update_id = self.bank.bank['last_update_session']

        current_id = None
        # We're ok there's already a published release
        if 'current' in self.bank.bank:
            current_id = self.bank.bank['current']
            # This means that we did not updated bank since last publish
            if current_id == last_update_id:
                ready = False
                if Manager.get_verbose():
                    Utils.warn(("[%s] There is no update ready to be published. " +
                               "Last session is already online") % self.bank.name)
                return ready

        production = self.get_last_production_ok()
        if production is None:
            return ready
        # We anyway double check in session if everything went ok
        session = self.get_session_from_id(production['session'])
        if session and 'workflow_status' in session:
            ready = session['workflow_status']
        else:
            ready = False
        return ready

    def _current_user(self):
        """
        Determine user running the actual manager.

        We search for login name in enviroment 'LOGNAME' and 'USER' variable

        :return: Current user name
        :rtype: str
        """
        logname = None

        if 'LOGNAME' in os.environ:
            logname = os.getenv('LOGNAME')
        elif 'USER' in os.environ:
            logname = os.getenv('USER')
        return logname

    def _check_config_jobs(self, name):
        """
        Check that the config for the jobs submission is OK

        :param name: Name of the config value to check. Will be '<name>.exe' in section 'JOBS
        :type name: str
        :return: Jobs configuration values
        :rtype: bool
        :raises SystemExit: If 'JOBS' section not found in configuration file (manager.properties)
        :raises SystemExit: If script's executable path is not found
        """
        if not self.config.has_section('JOBS'):
            Utils.error("[jobs] No JOBS section defined")
        exe = "%s.exe" % name
        if not self.config.has_option('JOBS', exe):
            Utils.warn("[jobs: %s] %s not set in configuration file. Action aborted." % (name, exe))
            return False
        script = self.config.get('JOBS', exe)
        if not os.path.exists(script):
            Utils.error("[jobs: %s] script (%s) not found! Action aborted." % (name, exe))
        return True

    def _get_config_jobs(self, name):
        """
        Get the values from the config for a particular job key

        :param name: Name of the job type
        :type name: str
        :return: Tuple, (exe, [args])
        :rtype: tuple
        """
        args = []
        if self.config.has_option('JOBS', "%s.args" % name):
            for arg in self.config.get('JOBS', "%s.args" % name).split(" "):
                args.append(arg)
        script = self.config.get('JOBS', "%s.exe" % name)
        return script, args

    @bank_required
    def _get_last_session(self):
        """
        Get the session(s) from a bank.

        :return: Session document from the database
        :rtype: dict
        :raises SystemExit: If 'session' key not found in bank document
        """
        if 'sessions' in self.bank.bank and self.bank.bank['sessions']:
            sessions = self.bank.bank['sessions']
            session = sessions[-1]
            return session
        else:
            Utils.error("No session found in bank %s" % str(self.bank.name))

    def _run_command(self, exe=None, args=None, quiet=False):
        """
        Just run a system command using subprocess. STDOUT and STDERR are redirected to /dev/null (os.devnull)

        :param exe: Executable to launch
        :type exe: str
        :param args: List of arguments
        :type args: list
        :param quiet: Quiet stdout, don't print on stdout
        :type quiet: bool
        :return: Execution status of the command
        :rtype: bool
        :raises SystemExit: If 'exe' args not provided
        :raises SystemExit: If returned exit code is > 0
        :raises SystemExit: If command cannot be run (except :class:`OSError`)
        """
        # Sleep time while waiting for process to terminate
        sleep = float(5)

        if exe is None:
            Utils.error("Can't run command, no exe provided")
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        if self.config.has_option('JOBS', 'jobs.sleep.time'):
            sleep = float(self.config.get('JOBS', 'jobs.sleep.time'))
        command = [exe] + args
        try:
            proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            inputs = [proc.stdout, proc.stderr]
            while proc.poll() is None:
                readable, _, _ = select.select(inputs, [], [], 1)
                while readable and inputs:
                    for flow in readable:
                        data = flow.read()
                        if not data:
                            # the flow ready in reading  which has no data
                            # is a closed flow
                            # thus we must stop it to watch it
                            inputs.remove(flow)
                        elif flow is proc.stdout:
                            if not quiet:
                                Utils.ok("[STDOUT] %s" % data)
                        elif flow is proc.stderr:
                            if not quiet:
                                Utils.warn("[STDERR] %s" % data)
                    readable, _, _ = select.select(inputs, [], [], 1)
                time.sleep(sleep)
            if proc.returncode != 0:
                Utils.error("[run command] command %s FAILED with exit code %d!" % (command, proc.returncode))
        except OSError as err:
            Utils.error("Can't run command '%s': %s" % (" ".join([exe] + args), str(err.strerror)))
        return True

    def _submit_job(self, name, args=None):
        """
        Submit a job.

        :param name: Name of the defined job in the manager.properties file, section 'JOBS'
        :type name: str
        :param args: List of args to pass to the commande
        :type args: list
        :return: Result of the command ran
        :rtype: bool
        :raises SystemExit: If 'args' arg is not a list
        """
        if not self._check_config_jobs(name):
            return False
        script, cargs = self._get_config_jobs(name)
        if args:
            if not isinstance(args, list):
                Utils.error("'args' params must be a list")
            else:
                cargs = args
        return self._run_command(exe=script, args=cargs)
