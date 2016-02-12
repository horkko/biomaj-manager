"""Main class of BioMAJ Manager"""

from __future__ import print_function
from datetime import datetime
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
    DATE_FMT = "%Y-%m-%d %H:%M:%S"
    SAVE_BANK_LINE_PATTERN = "%-20s\t%-30s\t%-20s\t%-20s\t%-20s"

    def __init__(self, bank=None, cfg=None, global_cfg=None):
        """
        Manager instance creation

        :param bank: Bank name
        :param config: Configuration file (global.properties)
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
            self.bank = Bank(name=bank, no_log=True)
            if self.bank.config.get('data.dir'):
                self.bank_prod = self.bank.config.get('data.dir')

    @staticmethod
    def load_config(cfg=None, global_cfg=None):
        """
        Load biomaj-manager configuration file (manager.properties). It uses BiomajConfig.load_config()
        to first load global.properties and determine where the config.dir is. manager.properties must
        be located at the same place as global.properties or file parameter must point to manager.properties

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

    # @bank_required
    # def bank_info(self):
    #     """
    #     Prints some information about the bank
    #     :return:
    #     """
    #     props = self.bank.get_properties()
    #     print("*** Bank %s ***" % self.bank.name)
    #     Utils.title('Properties')
    #     print("- Visibility : %s" % props['visibility'])
    #     print("- Type(s) : %s" % ','.join(props['type']))
    #     print("- Owner : %s" % props['owner'])
    #     Utils.title('Releases')
    #     print("- Current release: %s" % str(self.current_release()))
    #     if 'production' in self.bank.bank:
    #         Utils.title('Production')
    #         for production in self.bank.bank['production']:
    #             print("- Release %s (freeze:%s, size:%s, prod_dir:%s)" % (production['remoterelease'],
    #                                                                       str(production['freeze']),
    #                                                                       str(production['size']),
    #                                                                       str(production['prod_dir'])))
    #     pending = self.get_pending_sessions()
    #     if pending:
    #         for pend in pending:
    #             release = pend['release']
    #             session = pend['session_id']
    #             if session:
    #                 Utils.title('Pending')
    #                 print("- Release %s (Last run %s)" %
    #                       (str(release), Utils.time2datefmt(session['id'], Manager.DATE_FMT)))

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
            print("[%s] Can't switch, bank is being updated" % self.bank.name, file=sys.stderr)
            return False
        # If there is no published bank yet, ask the user to do it first. Can't switch to new release version
        # if no bank is published yet
        if not self.bank_is_published():
            print("[%s] There's no published bank yet. Publish it first" % self.bank.name, file=sys.stderr)
            return False

        # Bank construction failed?
        if self.last_session_failed():
            # A message should be printed from the function
            return False

        if not self.update_ready():
            print("[%s] Can't switch, bank is not ready" % self.bank.name, file=sys.stderr)
            return False
        return True

    @bank_required
    def current_release(self):
        """
        Search the current available release ('online')

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
        elif 'production' in self.bank.bank and len(self.bank.bank['production']) > 0:
            production = self.bank.bank['production'][-1]
            if 'release' in production and production['release']:
                release = production['release']
            elif 'remoterelease'in production and production['remoterelease']:
                release = production['remoterelease']
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

    @staticmethod
    def get_bank_list():
        """
        Get the list of bank available from the database

        :return: List of bank name
        :rtype: List of string
                Thorws SystemExit exception
        """
        # Don't read config again
        if BiomajConfig.global_config is None:
            try:
                BiomajConfig.load_config()
            except Exception as err:
                Utils.error("Problem loading biomaj configuration: %s" % str(err))
        try:
            banks_list = []
            if MongoConnector.db is None:
                from pymongo.errors import PyMongoError
                # We  surrounded this block of code with a try/except because there's a behavior
                # difference between pymongo 2.7 and 3.2. 2.7 immediately raised exception if it
                # cannot connect, 3.2 waits for a database access to connect to the server
                MongoConnector(BiomajConfig.global_config.get('GENERAL', 'db.url'),
                               BiomajConfig.global_config.get('GENERAL', 'db.name'))
            banks = MongoConnector.banks.find({}, {'name': 1, '_id': 0})
            for bank in banks:
                # Avoid document without bank name
                if 'name' in bank:
                    banks_list.append(bank['name'])
            return banks_list
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
            Utils.warn("[%s] db.packages not set!" % self.bank.name)
        else:
            packs = self.bank.config.get('db.packages').replace('\\', '').replace('\n', '').strip().split(',')
            for pack in packs:
                packages.append('pack@' + pack)
        return packages

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
                Utils.error("Can't get current production directory, 'prod_dir' or 'data_dir' missing in production document field")
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

    @bank_required
    def get_dict_sections(self, tool=None):
        """
        Get the "supported" blast2/golden indexes for this bank
        Each bank can have some sub sections. This method return
        them as a dictionary

        :param tool: Name of the index to search
        :type tool: String
        :return: If info defined,
                 dictionary with section(s) and bank(s)
                 sorted by type(nuc/pro)
                 Otherwise empty dict
        """
        if tool is None:
            Utils.error("A tool name is required to retrieve virtual info")

        ndbs = 'db.%s.nuc' % tool
        pdbs = 'db.%s.pro' % tool
        nsec = ndbs + '.sections'
        psec = pdbs + '.sections'
        dbs = {}

        if self.bank.config.get(ndbs):
            dbs['nuc'] = {'dbs': []}
            for sec in self.bank.config.get(ndbs).split(','):
                if sec and sec != '':
                    dbs['nuc']['dbs'].append(sec)
        if self.bank.config.get(pdbs):
            dbs['pro'] = {'dbs': []}
            for sec in self.bank.config.get(pdbs).split(','):
                if sec and sec != '':
                    dbs['pro']['dbs'].append(sec)
        if self.bank.config.get(nsec):
            if 'nuc' not in dbs:
                dbs['nuc'] = {}
            dbs['nuc']['secs'] = []
            for sec in self.bank.config.get(nsec).split(','):
                if sec and sec != '':
                    dbs['nuc']['secs'].append(sec)
        if self.bank.config.get(psec):
            if 'pro' not in dbs:
                dbs['pro'] = {}
            dbs['pro']['secs'] = []
            for sec in self.bank.config.get(psec).split(','):
                if sec and sec != '':
                    dbs['pro']['secs'].append(sec)
        return dbs

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
    def get_list_sections(self, tool=None):
        """
        Get the "supported" blast2/golden indexes for this bank
        Each bank can have some sub sections.

        :param tool: Name of the index to search
        :type tool: String
        :return: If info defined,
                 list of bank(s)/section(s) found
                 Otherwise empty list
        """
        if tool is None:
            Utils.error("A tool name is required to retrieve virtual info")

        ndbs = 'db.%s.nuc' % tool
        pdbs = 'db.%s.pro' % tool
        nsec = ndbs + '.sections'
        psec = pdbs + '.sections'
        dbs = []

        if self.bank.config.get(ndbs):
            for sec in self.bank.config.get(ndbs).split(','):
                dbs.append(sec)
        if self.bank.config.get(pdbs):
            for sec in self.bank.config.get(pdbs).split(','):
                dbs.append(sec)
        if self.bank.config.get(nsec):
            for sec in self.bank.config.get(nsec).split(','):
                dbs.append(sec.replace('\\', '').replace('\n', ''))
        if self.bank.config.get(psec):
            for sec in self.bank.config.get(psec).split(','):
                dbs.append(sec.replace('\\', '').replace('\n', ''))

        return dbs

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
                Utils.error("[%s] Cant find a 'remoterelease' for session %s" % (self.bank.name, session['id']))
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
                'created': Utils.time2datefmt(prod['session'], Manager.DATE_FMT),
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
                    'created': Utils.time2datefmt(sess['id'], Manager.DATE_FMT),
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
        Check if the last building bank session failed
        - If we find a pending session, we return False and warn the user to finish it
        - Then, we look into session and check that the last session.status.over is True/False

        :return: Boolean
        """
        has_failed = False
        update_id = None

        # We have to be careful as pending session have over.status to false
        pending = self.get_pending_sessions()

        if 'last_update_session' in self.bank.bank and self.bank.bank['last_update_session']:
            update_id = self.bank.bank['last_update_session']

        # Check the last updated session is not pending
        if pending and update_id:
            for pend in pending:
                if pend['session_id'] == update_id:
                    Utils.warn("[%s] The last updated session is pending (release %s). Complete workflow first!" %
                               (self.bank.name, pend['release']))
                has_failed = True
                return has_failed

        if 'sessions' in self.bank.bank and self.bank.bank['sessions']:
            for session in self.bank.bank['sessions']:
                if update_id and session['id'] == update_id:
                    # If session terminated OK, status.over should be True
                    if 'status' in session and 'over' in session['status']:
                        has_failed = not session['status']['over']
                        break
        return has_failed

    def list_plugins(self):
        """
        Read plugins set from the config manager.properties

        :return: List of plugins name
        :rtype: List of plugins
        """
        plugins_list = []
        if self.config.has_section('PLUGINS'):
            plugins = self.config.get('PLUGINS', 'plugins.list')
            for plugin in plugins.split(','):
                plugins_list.append(plugin)
        return plugins_list

    def load_plugins(self):
        """
        Load all the plugins and activate them from manager.properties (plugins.list property)

        :returns: biomajmanager.plugins.Plugins instance
        """
        self.plugins = Plugins(manager=self)
        return self.plugins

    @bank_required
    def mongo_history(self):
        """
        Get the releases history of a bank from the database and build a Mongo like document in json

        :return: history + extra info to be included into bioweb (Institut Pasteur only)
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

        for prod in productions:
            if 'current' in self.bank.bank:
                if prod['session'] == self.bank.bank['current']:
                    status = 'online'
                else:
                    status = 'deprecated'
            history.append({'_id': '@'.join(['bank',
                                             self.bank.name,
                                             str(prod['remoterelease']),
                                             str(Utils.time2datefmt(prod['session'], Manager.DATE_FMT))]),
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

        for sess in sessions:
            # Don't repeat production item stored in sessions
            new_id = '@'.join(['bank',
                               self.bank.name,
                               str(sess['remoterelease']),
                               str(Utils.time2datefmt(sess['id'], Manager.DATE_FMT))])
            if new_id in map(lambda d: d['_id'], history):
                continue

            history.append({'_id': '@'.join(['bank',
                                             self.bank.name,
                                             str(sess['remoterelease']),
                                             str(Utils.time2datefmt(sess['id'], Manager.DATE_FMT))]),
                            'type': 'bank',
                            'name': self.bank.name,
                            'version': str(sess['remoterelease']),
                            'publication_date': str(Utils.time2date(sess['last_update_time'])),
                            'removal_date': sess['last_modified'] if 'remove_release' in sess['status'] and
                                                                     sess['status']['remove_release'] is True
                            else None,
                            'bank_type': bank_type,
                            'bank_formats': bank_format,
                            'packageVersions': packages,
                            'description': description,
                            'status': 'deleted'
                            })
        return history

    @user_granted
    def restart_stopped_jobs(self, args=None):
        """
        Restart jobs stopped by calling 'stop_running_jobs'. This must be set in manager.properties
        configuration file, section 'JOBS'.

        :param args: List of args to pass to the command
        :type args: List of string
        :return: Boolean
        """
        return self._submit_job('restart.stopped.jobs', args=args)
        # if not self.config.has_option('MANAGER', 'jobs.restart.exe'):
        #     Utils.warn("[jobs.restart] jobs.restart.exe not set in configuration file. Action aborted.")
        #     return False
        #
        # script = self.config.get('MANAGER', 'jobs.restart.exe')
        # if not os.path.exists(script):
        #     Utils.error("[jobs.restart] script (%s) not found! Action aborted." % script)
        #args = self.config.get('MANAGER', 'jobs.restart.args')
        #script = self.config.get('MANAGER', 'jobs.restart.exe')
        #return self._run_command(exe=script, args=args)

    @user_granted
    def save_banks_version(self, file=None):
        """
        Save versions of bank when switching bank version (publish)

        :param file: Path to save banks version (String)
        :return: 0
        :raise: Exception
        """
        if not file:
            file = os.path.join(self.bank_prod,
                                'doc',
                                'versions',
                                'version.' + datetime.now().strftime("%Y-%m-%d"))
        # Check path exists
        directory = os.path.dirname(file)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as err:
                Utils.error("Can't create destination directory %s: %s" % (directory, str(err)))

        try:
            banks = Manager.get_bank_list()
            FILE_PATTERN = Manager.SAVE_BANK_LINE_PATTERN
            with open(file, mode='w') as fv:
                for bank in banks:
                    bank = Bank(name=bank, no_log=True)
                    if 'current' in bank.bank and bank.bank['current'] and 'production' in bank.bank:
                        for prod in bank.bank['production']:
                            if bank.bank['current'] == prod['session']:
                                # bank / release / creation / size / remote server
                                file_line = FILE_PATTERN % (bank.name, "Release " + prod['release'],
                                                            Utils.time2datefmt(prod['session'], Manager.DATE_FMT),
                                                            str(prod['size']) if 'size' in prod and prod['size'] else "NA",
                                                            bank.config.get('server'))
                                if Manager.simulate:
                                    print(file_line)
                                else:
                                    fv.write(file_line)
        except Exception as e:
            Utils.error("Can't access file: %s" % str(e))
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
        bank = Bank(name=name, no_log=True)
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
    def show_pending_sessions(self, show=False, fmt="psql"):
        """
        Check if some session are pending

        :param show: Print the results
        :type show: Boolean, default=False
        :param fmt: Output format for tabulate, default psql
        :type fmt: String
        :return: self.get_pending_sessions()
        """
        return self.get_pending_sessions()

    def show_need_update(self):
        """
        Check bank(s) that need to be updated (can be switched)

        :return:
        """
        banks = {}
        if self.bank:
            if self.can_switch():
                banks[self.bank.name] = self.bank
            return banks

        banks_list = Manager.get_bank_list()
        for bank in banks_list:
            self.bank = Bank(name=bank, no_log=True)
            if self.can_switch():
                banks[self.bank.name] = self.bank
            self.bank = None
        return banks

    @user_granted
    def stop_running_jobs(self, args=None):
        """
        Stop running jobs using bank(s). This calls an external script which must be set
        in the manager.properties configuration file, section JOBS.

        :param args: List of args to pass to the commande
        :type args: List of string
        :return: Boolean
        """
        return self._submit_job('stop.running.jobs', args=args)
        # if not self.config.has_option('MANAGER', 'jobs.stop.exe'):
        #     Utils.warn("[jobs.stop] jobs.stops.exe not set in configuration file. Action aborted.")
        #     return False
        #
        # script = self.config.get('MANAGER', 'jobs.stop.exe')
        # if not os.path.exists(script):
        #     Utils.error("[jobs.stop] script (%s) not found! Action aborted." % script)
        # args = self.config.get('MANAGER', 'jobs.stop.args')
        # return self._run_command(exe=script, args=[args])

    @bank_required
    def update_ready(self):
        """
        Check the update is ready to be published. Do to this we search in this order:
        - Check a release is already published. If so, check it is not the last updated session
        - Check if we have a 'status' entry and its over.status is true, meaning update went ok
        db.banks.current not 'null' and we search for the most recent completed session to
        retrieve its release. Once found, we set it to the be the future release to be published

        :return: Boolean
        """
        ready = False

        if 'last_update_session' not in self.bank.bank:
            Utils.error("No last session recorded")
        last_update_id = self.bank.bank['last_update_session']

        # We're ok there's already a published release
        if 'current' in self.bank.bank:
            current_id = self.bank.bank['current']
            # This means that we did not updated bank since last publish
            if current_id == last_update_id:
                ready = False
                Utils.warn("[%s] There is not update ready to be published. Last session is already online" % self.bank.name)
            else:
                ready = True
        # We first search for the last completed run. It should be in production
        # We can search on status. If not in status, then it could be coming from
        # a fresh migration (biomaj-migrate does not set status)
        elif 'production' in self.bank.bank and len(self.bank.bank['production']) > 0:
            # An entry in production means we've completed the update workflow
            for production in self.bank.bank['production']:
                if last_update_id == production['session']:
                    session = self.get_session_from_id(last_update_id)
                    if session:
                        if 'over' in session['status']:
                            ready = session['status']['over']
        return ready

    """Private methods"""

    def _current_user(self):
        """
        Determine user running the actual manager. We search for login name
        in enviroment 'LOGNAME' and 'USER' variable

        :return: String or None
        """
        logname = None

        if 'LOGNAME' in os.environ:
            logname = os.getenv('LOGNAME')
        elif 'USER' in os.environ:
            logname = os.getenv('USER')
        return logname
        #current_user = logname
        #if not current_user:
        #    Utils.error("Can't find current user name")
        #return current_user

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

    def _get_formats_for_release(self, path=None):
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
            if pathdir == path or not len(dirs):
                continue
            if pathdir == 'flat':
                continue
            for d in dirs:
                formats.append('@'.join(['pack', os.path.basename(pathdir), d or '-']))
        formats.sort()
        return formats

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
        # if quiet:
        #     stdout = open(os.devnull, 'wb')
        #     stderr = open(os.devnull, 'wb')
        # else:
        #     stdout = subprocess.PIPE
        #     stderr = subprocess.PIPE
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        if self.config.has_option('JOBS', 'jobs.sleep.time'):
            sleep = float(self.config.get('JOBS', 'jobs.sleep.time'))
        command = [exe] + args
        try:
            proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            inputs = [proc.stdout, proc.stderr]
            while proc.poll() is None:
                readable, writable, exceptional = select.select(inputs, [], [], 1)
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
                    readable, writable, exceptional = select.select(inputs, [], [], 1)
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
            cargs = args
        return self._run_command(exe=script, args=cargs)
