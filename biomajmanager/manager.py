"""Main class of BioMAJ Manager"""

from __future__ import print_function
import datetime
import re
import os
import select
import subprocess
import sys
import time

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
        :type cfg: String
        :param globa_cfg: Global configuration file (global.properties)
        :type global_cfg: String
        :return:
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
        :type cfg: String
        :param global_cfg:
        :type global_cfg:
        :return: ConfigParser object
        :rtype: configparser.SafeParser
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

        :return: Output from biomaj.bank.get_bank_release_info (Lists)
        """
        return self.bank.get_bank_release_info(full=True)

    @bank_required
    def bank_is_published(self):
        """
        Check if a bank is already published or not.

        :return: Boolean
        """
        if 'current' in self.bank.bank and self.bank.bank['current']:
            return True
        return False

    @bank_required
    def can_switch(self):
        """
        Check if a bank can be updated and put into production as 'current'

        :return: Boolean
        """
        # Bank is updating?
        if self.bank.is_locked():
            if Manager.get_verbose():
                print("[%s] Can't switch, bank is being updated" % self.bank.name, file=sys.stderr)
            return False
        # If there is no published bank yet, ask the user to do it first. Can't switch to new release version
        # if no bank is published yet
        if not self.bank_is_published():
            if Manager.get_verbose():
                print("[%s] There's no published bank yet. Publish it first" % self.bank.name, file=sys.stderr)
            return False

        # Bank construction failed?
        if self.last_session_failed():
            # A message should be printed from the function
            return False

        if not self.update_ready():
            if Manager.get_verbose():
                print("[%s] Can't switch, bank is not ready" % self.bank.name, file=sys.stderr)
            return False
        return True

    @bank_required
    def current_release(self):
        """
        Search for the current available release ('online')

        :return: Release number if available or 'NA'
        :rtype: String or None
        """
        if self._current_release:
            return self._current_release
        current = None
        release = None
        # First se search if a current release is set
        if 'current' in self.bank.bank and self.bank.bank['current']:
            session = self.get_session_from_id(self.bank.bank['current'])
            if session and 'release' in session and session['release']:
                release = session['release']
            elif session and 'remoterelease' in session and session['remoterelease']:
                release = session['remoterelease']
            if release:
                current = release
        # Then we fallback to production which handle release(s) that have been
        # completed, workflow(s) over
        #elif 'production' in self.bank.bank and len(self.bank.bank['production']) > 0:
        #    production = self.bank.bank['production'][-1]
        #    if 'release' in production and production['release']:
        #        release = production['release']
        #    elif 'remoterelease'in production and production['remoterelease']:
        #        release = production['remoterelease']
        #    if release:
        #        current = release
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
        :type flat: Boolean
        :return: List of supported format(s) as:
                if flat is True:
                { 'tool1': [list of version], 'tool2': [list of version] ...}
                if flat is False
                ['tool1@version', 'tool1@version', 'tool2@version' ....]
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
        """Returns the formats as a List of string"""
        return self.formats(flat=True)

    @bank_required
    def get_bank_data_dir(self):
        """
        Returns the complete path where the bank data_dir is located

        :return: Path to the current bank data dir
        :rtype: String
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
        :type visibility: String
        :return: List of bank name
        :rtype: List of string
                Throws SystemExit exception
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

        :return: List of defined pckages for a bank
        :rtype: List of string 'pack@<pack_name>@<pack_version>'
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
        :type tool: String
        :return: Dict of List
                 {'nuc': {'dbs': ['db1', 'db2', ...], 'sections': [ ...]},
                  'pro': {'dbs': [ ... ], 'sections': ['sec1', 'sec2', ..] }
                 }
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
        :rtype: String
        """
        return os.path.join(self.bank.config.get('data.dir'),
                            self.bank.name,
                            'current')

    @bank_required
    def get_current_proddir(self):
        """
        Get the path of the current production bank

        :return: Path to the current production bank
        :rtype: String
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
        :type section: Str
        :param regex: Regex to search the key with
        :type regex: String
        :param with_values: Returns values instead of keys
        :type with_values: Boolean, default True
        :return: Sorted List of values found
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
        :rtype: String or None
        """
        return self._current_user()

    @staticmethod
    def get_formats_for_release(path=None):
        """
        Get all the formats supported for a bank (path).

        :param path: Path of the release to search in
        :type path: String (path)
        :return: List of sorted formats
        """
        formats = []
        if not path:
            Utils.error("A path is required")
        if not os.path.exists(path):
            Utils.warn("Path %s does not exist" % path)
            return formats

        for pathdir, dirs, _ in os.walk(path):
            if pathdir == path or not len(dirs) or os.path.basename(pathdir) == 'flat':
                continue
            for d in dirs:
                formats.append('@'.join(['pack', os.path.basename(pathdir), d or '-']))
        formats.sort()
        return formats


    @bank_required
    def get_future_link(self):
        """
        Return the the path of the bank 'current' version symlink

        :return: Complete path of 'future_release' link
        :rtype: String
        """
        return os.path.join(self.bank.config.get('data.dir'),
                            self.bank.name,
                            'future_release')

    @bank_required
    def get_last_production_ok(self):
        """
        Search for the last release in production which ran ok

        :return: 'production' Dict or None if
                                           production is empty
                                           last production is the current
                  Throws is no 'production' or no 'sessions' key
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

        :return: List of Dict {'release'=release, 'session_id': id} or empty list
        """
        pending = []
        if 'pending' in self.bank.bank and self.bank.bank['pending']:
            has_pending = self.bank.bank['pending']
            for k, v in has_pending.items():
                pending.append({'release': k, 'session_id': v})
        return pending

    @bank_required
    def get_published_release(self):
        """
        Check a bank has a published release

        :return: Release number or None
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
        :type session_id: String
        :return: Session or None
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

        :return: Boolean
        """
        return Manager.simulate

    @staticmethod
    def get_verbose():
        """
        Get the value of the verbose mode

        :return: Boolean
        """
        return Manager.verbose

    @bank_required
    def has_current_link(self, link=None):
        """
        Check if the 'current' link is there

        :param link: Link path to check, otherwise get from 'get_current_link'
        :type: String
        :return: Boolean
        """
        if link is None:
            link = self.get_current_link()
        return os.path.islink(link)

    @bank_required
    def has_future_link(self, link=None):
        """
        Check if the 'future_release' link is there

        :param link: Link path to check, otherwise get from 'get_future_link'
        :type: String
        :return: Boolean
        """
        if link is None:
            link = self.get_future_link()
        return os.path.islink(link)

    @bank_required
    def has_formats(self, fmt=None):
        """
        Checks either the bank supports 'format' or not

        :param fmt: Format to check
        :type fmt: String
        :return: Boolean
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
        Get the releases history of a specific bank

        :return: A list with the full history of the bank
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

        description = self.bank.config.get('db.fullname').strip()
        packages = self.get_bank_packages()
        bank_type = self.bank.config.get('db.type').split(',')
        bank_format = self.bank.config.get('db.formats').split(',')
        status = 'unpublished'

        for prod in productions:
            if 'current' in self.bank.bank:
                if 'session' in prod and prod['session'] == self.bank.bank['current']:
                    status = 'online'
                else:
                    status = 'deprecated'
            history.append({
                # Convert the time stamp from time() to a date
                'created': Utils.time2datefmt(prod['session']),
                'id': prod['session'],
                'removed': None,
                'status': status,
                'name': self.bank.name,
                'path': os.path.join(prod['data_dir'], str(prod['dir_version']), str(prod['prod_dir'])),
                'release': prod['remoterelease'],
                'freeze': prod['freeze'],
                'bank_type': bank_type,
                'bank_format': bank_format,
                'description': description,
                'packageVersions': packages,
            })

        for sess in sessions:
            # Don't repeat production item stored in sessions
            if 'id' in sess:
                if sess['id'] in map(lambda d: d['id'], history):
                    continue
                path = os.path.join(sess['data_dir'], str(sess['dir_version']), str(sess['prod_dir']))
                history.append({
                    'created': Utils.time2datefmt(sess['id']),
                    'id': sess['id'],
                    'removed': True,
                    'status': 'deleted',
                    'name': self.bank.name,
                    'path': path,
                    'bank_type': bank_type,
                    'bank_format': bank_format,
                    'description': description,
                    'packageVersions': packages,
                })
        return history

    @bank_required
    def last_session_failed(self):
        """
        Check if the last building bank session failed, base on 'last_update_session' field.

        - If we find a pending session, we return False and warn the user to finish it
        - Then, we look into session and check that the last session.status.over is True/False

        :return: Boolean
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
                if pend['session_id'] == last_update_id:
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

        :returns: biomajmanager.plugins.Plugins instance
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
        :return: datetime.datetime object
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
    def mongo_history(self):
        """
        Get the releases history of a bank from the database and build a Mongo like document in json

        :return: history + extra info to be included into bioweb (Institut Pasteur only)
        """
        ## TODO: During the sessions check, make sure the sessions.update is true, meaning that we'done something
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

        for prod in sorted(productions, key=lambda created: created['session'], reverse=True ):
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
                            'publication_date': str(Utils.time2date(prod['session'])),
                            'removal_date': None,
                            'bank_type': bank_type,
                            'bank_format': bank_format,
                            'packageVersions': packages,
                            'description': description,
                            'status': status
                            })

        for sess in sorted(sessions, key=lambda created: created['id'], reverse=True ):
            # Don't repeat production item stored in sessions
            new_id = '@'.join(['bank',
                               self.bank.name,
                               str(sess['remoterelease']),
                               str(Utils.time2datefmt(sess['id']))])
            if new_id in map(lambda d: d['_id'], history):
                continue
            history.append({'_id': new_id,
                            'type': 'bank',
                            'name': self.bank.name,
                            'version': str(sess['remoterelease']),
                            'publication_date': str(Utils.time2date(sess['last_update_time'])),
                            'removal_date': str(Utils.time2datefmt(sess['deleted']))
                                            if 'deleted' in sess else None,
                            'bank_type': bank_type,
                            'bank_formats': bank_format,
                            'packageVersions': packages,
                            'description': description,
                            'status': 'deleted'
                            })
        return history

    @bank_required
    def next_release(self):
        """
        Get the next bank release version from the database if available

        :return: String or None
        """
        if self._next_release:
            return self._next_release
        next_release = None
        session = None
        production = None
        # If we have a current release set, we need to check the last session from sessions
        # which are not current and not in production
        # if 'current' in self.bank.bank and self.bank.bank['current']:
        #     current_id = self.bank.bank['current']
        # elif 'production' in self.bank.bank and len(self.bank.bank['production']) > 0:
        #     production = self.get_last_production_ok()
        # else:
        #     Utils.error("Can't determine next release, no production nor current release published!")

        production = self.get_last_production_ok()
        if production is None:
            Utils.error("No 'production' release found searching for next release")
        session = self.get_session_from_id(production['session'])
        if session is not None:
            # Pending sessions are excluded
            if 'workflow_status' in session and session['workflow_status']:
                next_release = session['remoterelease']
        else:
            Utils.error("Can't find release in session '%s'" % str(production['session']))

        self._next_release = next_release
        return self._next_release

    @user_granted
    def restart_stopped_jobs(self, args=None):
        """
        Restarts jobs stopped by calling 'stop_running_jobs'.

        This must be set in manager.properties configuration file, section 'JOBS'.
        You must set 'restart.stopped.jobs.exe' [MANDATORY] and 'restart.stopped.jobs.args'
        [OPTIONAL]

        :param args: List of args to pass to the command
        :type args: List of string
        :return: Boolean
        """
        return self._submit_job('restart.stopped.jobs', args=args)

    @user_granted
    def save_banks_version(self, bank_file=None):
        """
        Save versions of bank when switching bank version (publish)

        :param bank_file: Path to save banks version (String)
        :return: 0
        :raise: Exception
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
                                    print(file_line)
                                else:
                                    fv.write(file_line)
        except Exception as e:
            Utils.error("Can't access file: %s" % str(e))
        Utils.ok("Bank versions saved in %s" % bank_file)
        return 0

    def set_bank(self, bank=None):
        """
        Set a bank for the current Manager

        :param bank: biomaj.bank.Bank
        :return: Boolean
        """
        if not bank or bank is None:
            return False
        if isinstance(bank, Bank):
            self.bank = bank
            return True
        return False

    def set_bank_from_name(self, name=None):
        """
        Set a bank from a bank name

        :param name: Name of the bank to set
        :type name: String
        :return: Boolean
        """
        if not name or name is None:
            return False
        try:
            bank = Bank(name=name, no_log=True)
        except Exception as err:
            Utils.error("Problem with bank %s: %s" % (name, str(err)))
        return self.set_bank(bank=bank)

    @staticmethod
    def set_simulate(value):
        """
        Set/Unset simulate mode

        :param value: Value to set
        :type value: Boolean
        :return: Boolean
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
        :type value: Boolean
        :return: Boolean
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

        :return: See get_pending_sessions()
        """
        return self.get_pending_sessions()

    def show_need_update(self):
        """
        Check bank(s) that need to be updated (can be switched)

        :return:
        """
        banks = []
        if self.bank:
            if self.can_switch():
                banks.append({'name': self.bank.name,
                              'current_release': self.current_release(),
                              'next_release': self.next_release()})
            return banks

        banks_list = Manager.get_bank_list()
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
        :type args: List of string
        :return: Boolean
        """
        return self._submit_job('stop.running.jobs', args=args)

    @bank_required
    def update_ready(self):
        """
        Check the bank release is ready to be published.

        We first check we have a last session recorded using 'last_update_session'. It must be here, otherwise, warning.
        Then, if we've got a 'current', we check 'current' is not equal to'last_update_session', meaning no update has
        been performed since last publish. If 'current' is not equal to 'last_update_session', we need to search for
        the last update that went ok and is ok for publishing.
        Otherwise, we warn the user and we return false.

        :return: Boolean
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

        :return: String or None
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
        :type name: String
        :return: Boolean
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
        :type name: String
        :return: Tuple, (exe, [args])
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

        :return: List of session
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
        :type exe: String
        :param args: List of arguments
        :type args: List
        :param quiet: Quiet stdout, don't print on stdout
        :type quiet: Boolean
        :return: Boolean
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
        :type name: String
        :param args: List of args to pass to the commande
        :type args: List of string
        :return: Boolean
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
