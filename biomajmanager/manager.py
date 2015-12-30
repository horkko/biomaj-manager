from __future__ import print_function

from datetime import datetime
import re
import os
import string
import sys

from biomaj.bank import Bank
from biomaj.config import BiomajConfig
from biomaj.mongo_connector import MongoConnector
from biomajmanager.utils import Utils
from biomajmanager.plugins import Plugins
from biomajmanager.decorators import bank_required, user_granted


class Manager(object):

    # Simulation mode
    simulate = False
    # Verbose mode
    verbose = False
    # Default date format string
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

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
        except Exception as e:
            Utils.error(str(e))

        if bank is not None:
            self.bank = Bank(name=bank, no_log=True)
            if self.bank.config.get('data.dir'):
                self.bank_prod = self.bank.config.get('data.dir')

            """
            # Check if manager.properties is here and put it into global_conf
            # We look for a manager.properties file at the same place as global.properties
            if not self.config:
                conf_dir = self.bank.config.get('conf.dir')
                conf_dir = os.path.dirname(conf_dir)
                manager_conf = os.path.sep.join([conf_dir, 'manager.properties'])
                if os.path.isfile(manager_conf):
                    self.bank.config.global_config.read(manager_conf)
                else:
                    Utils.error("Can't find 'manager.properties': %s" % manager_conf)
            """

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
        if not os.path.isdir(conf_dir):
            Utils.error("Can't find config directory '%s'" % conf_dir)
        if not cfg:
            cfg = os.path.join(conf_dir, 'manager.properties')
        if not os.path.isfile(cfg):
            print("Can't find config file %s" % cfg)

        Utils.verbose("[manager] Reading manager configuration file")
        BiomajConfig.global_config.read(cfg)
        return BiomajConfig.global_config

    @bank_required
    def bank_info(self):
        """
        Prints some information about the bank
        :return:
        """
        props = self.bank.get_properties()
        print(props)
        print("*** Bank %s ***" % self.bank.name)
        Utils.title('Properties')
        print("- Visibility : %s" % props['visibility'])
        print("- Type(s) : %s" % ','.join(props['type']))
        print("- Owner : %s" % props['owner'])
        Utils.title('Releases')
        print("- Current release: %s" % str(self._current_release))
        if 'production' in self.bank.bank:
            Utils.title('Production')
            for production in self.bank.bank['production']:
                print("- Release %s (freeze:%s, size:%s, prod_dir:%s)" % (production['remoterelease'],
                                                                          str(production['freeze']),
                                                                          str(production['size']),
                                                                          str(production['prod_dir'])))
        pending = self.get_pending_sessions()
        if pending:
            for pend in pending:
                release = pend['release']
                session = pend['session_id']
                if session:
                    Utils.title('Pending')
                    print("- Release %s (Last run %s)" %
                          (str(release), Utils.time2datefmt(session['id'], Manager.DATE_FMT)))

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
        # Is there a bank already in production (published) ?
        #if not os.path.islink(self.get_current_link()): # and not os.path.islink(self.get_future_link()):
        #    print("[%s] Can't switch, bank has no 'current' link" % self.bank.name)
        #    return False
        # If there is no published bank yet, ask the user to do it first. Can't switch to new release version
        # if no bank is published yet
        if not self.bank_is_published():
            print("[%s] There's no published bank yet. Publish it first" % self.bank.name, file=sys.stderr)
            return False

        # Bank construction failed?
        if self.last_session_failed():
            # A message should be printed from the function
            #print("[%s] Can't switch, last session failed" % self.bank.name)
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
        :rtype: String
        """
        if self._current_release:
            return self._current_release
        current = 'NA'
        # First se search if a current release is set
        if 'current' in self.bank.bank and self.bank.bank['current']:
            release = None
            session = self.get_session_from_id(self.bank.bank['current'])
            if 'release' in session and session['release']:
                release = session=['release']
            elif 'remoterelease' in session and session['remoterelease']:
                release = session['remoterelease']
            if release:
                current = release
        # Then we fallback to production which handle release(s) that have been
        # completed, workflow(s) over
        elif 'production' in self.bank.bank and len(self.bank.bank['production']) > 0:
            production = self.bank.bank['production'][-1]
            release = None
            if 'release' in production and production['release']:
                release = production['release']
            elif 'remoterelease'in production and production['remoterelease']:
                release = production['remoterelease']
            if release:
                current = release
        else:
            Utils.error("Can't get current release, no production available")
        self._current_release = current
        return str(current)

    @bank_required
    def formats(self, flat=False):
    #def formats(self, release='current', flat=False):
        """
        Check the "supported formats" for a specific bank.
        This is done simply by getting the variable 'db.packages' from the bank
        configuration file.
        :param flat: flatten the list of format for this bank
                     default False
        :type flat: Boolean
        :return: List of supported format(s) as:
                if flat is True:
                { 'bank_name': {'tool1': [list of version], 'tool2': [list of version] ...} }
                if flat is False
                {'bank_name': ['tool1@version', 'tool1@version', 'tool2@version' ....] }
        """
        formats = []
        if flat:
            formats = {}
        if self.bank.config.get('db.packages'):
            packages = self.bank.config.get('db.packages').replace('\\', '').replace('\n','').split(',')
            for package in packages:
                (name, version) = package.split('@')
                # formats = {}
                # {'cfamiliaris': {'GenomeAnalysisTK': ['2.4.9'], 'picars-tools': ['1.94'],
                # 'bowtie': ['0.12.7'], 'samtools': ['0.1.19'], 'bwa': ['0.5.9', '0.6.2', '0.7.4'],
                # 'fasta': ['3.6'], 'blast': ['2.2.26'], 'soap': ['2.21'], 'bowtie2': ['2.1.0']}}
                if flat:
                    if not name in formats:
                        formats[name] = []
                    formats[name].append(version)
                else:
                    formats.append(package)
        return formats
        #path = os.path.join(self.bank.config.get('data.dir'), self.bank.name, release)
        #if not os.path.exists(path):
        #    Utils.error("Can't get format(s) from '%s', directory not found" % path)
        #if flat:
        #    return ','.join(os.listdir(path))
        #return os.listdir(path)

    @bank_required
    def formats_as_string(self):
        return self.formats(flat=True)

    @staticmethod
    def get_bank_list():
        """
        Get the list of bank available from the database
        :return: List of bank name
        :rtype: List of string
        """
        if MongoConnector.db is None:
            BiomajConfig.load_config()
            MongoConnector(BiomajConfig.global_config.get('GENERAL','db.url'),
                           BiomajConfig.global_config.get('GENERAL','db.name'))
        banks = MongoConnector.banks.find({}, {'name': 1, '_id': 0})
        banks_list = []
        for bank in banks:
            banks_list.append(bank['name'])
        return banks_list

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
            for sec in string.split(self.bank.config.get(ndbs), ','):
                dbs['nuc']['dbs'].append(sec)
        if self.bank.config.get(pdbs):
            dbs['pro'] = {'dbs': []}
            for sec in string.split(self.bank.config.get(pdbs), ','):
                dbs['pro']['dbs'].append(sec)
        if self.bank.config.get(nsec):
            if 'nuc' in dbs:
                dbs['nuc']['secs'] = []
            else:
                dbs['nuc': {'dbs': []}]
            for sec in string.split(self.bank.config.get(nsec), ','):
                dbs['nuc']['secs'].append(sec)
        if self.bank.config.get(psec):
            if 'pro' in dbs:
                dbs['pro']['secs'] = []
            else:
                dbs['pro'] = {'secs': []}
            for sec in string.split(self.bank.config.get(psec), ','):
                dbs['pro']['secs'].append(sec)

        if dbs.keys():
            if not len(self.available_releases):
                self.db._get_releases(self)
            dbs['inf'] = {'desc': self.bank.config.get('db.fullname')
                          ,'vers': self.available_releases[0].release if len(self.available_releases) else ""
                          }
            dbs['tool'] = tool
        return dbs

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
            for sec in string.split(self.bank.config.get(ndbs), ','):
                dbs.append(sec)
        if self.bank.config.get(pdbs):
            for sec in string.split(self.bank.config.get(pdbs), ','):
                dbs.append(sec)
        if self.bank.config.get(nsec):
            for sec in string.split(self.bank.config.get(nsec), ','):
                dbs.append(sec.replace('\\','').replace('\n',''))
        if self.bank.config.get(psec):
            for sec in string.split(self.bank.config.get(psec), ','):
                dbs.append(sec.replace('\\','').replcae('\n',''))

        return dbs

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
        prod = self.bank.get_production(release)
        if 'data_dir' in prod and 'prod_dir' in prod:
            return os.path.join(prod['data_dir'], self.bank.name, prod['prod_dir'])
        Utils.error("Can't get current production directory, element(s) missing")

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

    def get_config_regex(self, section='GENERAL', regex=None, want_values=True):
        """

        :param section: Section to read, default 'GENERAL'
        :type section: Str
        :param regex: Regex to search the key with
        :type regex: String
        :return: List of values found
        """
        pattern = re.compile(regex)
        keys = dict(self.config.items(section))
        values = []
        for key in keys:
            if re.search(pattern, key):
                if want_values:
                    values.append(self.config.get(section, key))
                else:
                    values.append(key)
        return values

    @bank_required
    def get_pending_sessions(self):
        """
        Request the database to check if some session(s) are pending to complete
        :return: Dict {'release'=release, 'session_id': id} or None
        """
        pending = None
        if 'pending' in self.bank.bank and self.bank.bank['pending']:
            pending = []
            has_pending = self.bank.bank['pending']
            for k,v in has_pending.items():
                pending.append({'release': k, 'session_id': v })

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
    def get_session_from_id(self, id):
        """
        Retrieve a bank session from its id
        :param id: Session id
        :type id: String
        :return: Session or None
        """
        sess = None
        if not id:
            Utils.error("A session id is required")
        if 'sessions' in self.bank.bank and self.bank.bank['sessions']:
            for session in self.bank.bank['sessions']:
                if id == session['id']:
                   sess = session
        return sess

    @bank_required
    def has_current_link(self, link=None):
        """
        Check if the 'current' link is there
        :param link: Link path to check, otherwise get from 'get_current_link'
        :type: String
        :return: Boolean
        """
        if not link:
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
        if not link:
            link = self.get_future_link()
        return os.path.islink(link)

    @bank_required
    def has_formats(self, fmt=format):
        """
            Checks wether the bank supports 'format' or not
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
        packages = self.bank.config.get('db.packages').replace('\\', '').strip().split(',')
        bank_type = self.bank.config.get('db.type').split(',')
        bank_format = self.bank.config.get('db.formats').split(',')

        for prod in productions:
            history.append({
            # Convert the time stamp from time() to a date
                'created': Utils.time2datefmt(prod['session'], Manager.DATE_FMT),
                'id': prod['session'],
                'removed': None,
                'status': 'available',
                'name': self.bank.name,
                'path': os.path.join(prod['data_dir'], self.bank.name, prod['dir_version'], prod['prod_dir']),
                'release': prod['remoterelease'],
                'freeze': prod['freeze'],
                'bank_type': bank_type,
                'bank_format': bank_format,
                'description': description,
                'packages': packages,

            })

        for sess in sessions:
            # Don't repeat production item stored in sessions
            if sess['id'] in map(lambda d: d['id'], history):
                continue
            dir = os.path.join(sess['data_dir'], self.bank.name, sess['dir_version'], sess['prod_dir'])
            status = 'available' if os.path.isdir(dir) else 'deleted'
            history.append({
                    'created': Utils.time2datefmt(sess['id'], Manager.DATE_FMT),
                    'id': sess['id'],
                    'removed': True,
                    'status': status,
                    'name': self.bank.name,
                    'path': dir,
                    'bank_type': bank_type,
                    'bank_format': bank_format,
                    'description': description,
                    'packages': packages,
                })
        return history

    @bank_required
    def last_session_failed(self):
        """
        Check if the last building bank session failed
        - If we find a pending session, we return False and warn the user to finish it
        - Then, we look into session and check that the last session.status.over is True/False
        :return:Boolean
        """
        has_failed = False
        update_id = None
        # pending_ids = None

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
                    has_failed = not session['status']['over']
                    break
        return has_failed

    def list_plugins(self):
        """
        Read plugins set from the config manager.properties
        :return: List of plugins name
        :rtype: List
        """
        if self.config.has_section('PLUGINS'):
            plugins = self.config.get('PLUGINS', 'plugins.list')
            for plugin in plugins.split(','):
                Utils.ok("Plugin is %s\n-------------" % plugin)
                for key in self.get_config_regex(regex='^' + plugin.lower(), section=plugin, want_values=False):
                    print("%s=%s" % (key, self.config.get(plugin, key)))

    def load_plugins(self):
        """
        Load all the plugins and activate them from manager.properties (plugins.list property)
        """
        self.plugins = Plugins(manager=self)
        return

    @bank_required
    def mongo_history(self, bank=None):
        """
        Get the releases history of a bank from the database and build a Mongo like document in json

        :param name: Name of the bank
        :type name: String
        :param idbank: Bank id (primary key)
        :tpye idbank: Integer
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
        packages = []

        # Check db.packages is set for the current bank
        if not self.bank.config.get('db.packages'):
            Utils.warn("[%s] db.packages not set!" % self.bank.name)
        else:
            packages = map((lambda p: 'pack@' + p), self.bank.config.get('db.packages')
                                                     .replace('\\', '').replace('\n', '').strip().split(','))

        description = self.bank.config.get('db.fullname').replace('"', '').strip()
        bank_type = self.bank.config.get('db.type').split(',')
        bank_format = self.bank.config.get('db.formats').split(',')
        status = 'unknown'

        for prod in productions:
            if 'current' in self.bank.bank:
                if prod['session'] == self.bank.bank['current']:
                    status = 'online'
                else:
                    status = 'deprecated'
            history.append({'_id': '@'.join(['bank',
                                             self.bank.name,
                                             prod['remoterelease'],
                                             Utils.time2datefmt(prod['session'], Manager.DATE_FMT)]),
                             'type': 'bank',
                             'name': self.bank.name,
                             'version': prod['remoterelease'],
                             'publication_date': Utils.time2date(prod['session']),
                             'removal_date': None,
                             'bank_type': bank_type,
                             'bank_format': bank_format,
                             'packages': packages,
                             'description': description,
                             'status': status
                            })

        for sess in sessions:
            # Don't repeat production item stored in sessions
            new_id = '@'.join(['bank',
                               self.bank.name,
                               sess['remoterelease'],
                               Utils.time2datefmt(sess['id'], Manager.DATE_FMT)])
            if new_id in map(lambda d: d['_id'], history):
                continue

            history.append({'_id': '@'.join(['bank',
                                             self.bank.name,
                                             sess['remoterelease'],
                                             Utils.time2datefmt(sess['id'], Manager.DATE_FMT)]),
                            'type': 'bank',
                            'name': self.bank.name,
                            'version': sess['remoterelease'],
                            'publication_date': Utils.time2date(sess['last_update_time']),
                            'removal_date': sess['last_modified'] if 'remove_release' in sess['status'] and sess['status']['remove_release'] == True
                                                                  else None,
                            'bank_type': bank_type,
                            'bank_formats': bank_format,
                            'packages': packages,
                            'description': description,
                            'status': 'deleted'
                            })
        return history

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
            os.path.exists(file)
            banks = Manager.get_bank_list()
            with open(file, mode='w') as fv:
                for bank in banks:
                    bank = Bank(name=bank, no_log=True)
                    if 'current' in bank.bank and bank.bank['current'] and 'production' in bank.bank:
                        if Manager.verbose:
                            Utils.ok("[%s] current found" % bank.name)
                        for prod in bank.bank['production']:
                            if bank.bank['current'] == prod['session']:
                                if Manager.simulate:
                                    print("%-20s\t%-30s\t%-20s\t%-20s\t%-20s"
                                          % (bank.name,
                                          "Release " + prod['release'],
                                          Utils.time2datefmt(prod['session'], Manager.DATE_FMT),
                                          str(prod['size']) if 'size' in prod and prod['size'] else "NA",
                                    bank.config.get('server')))
                                else:
                                    # bank / release / creation / size / remote server
                                    fv.write("%-20s\t%-30s\t%-20s\t%-20s\t%-20s"
                                             % (bank.name,
                                             "Release " + prod['release'],
                                             Utils.time2datefmt(prod['session'], Manager.DATE_FMT),
                                             str(prod['size']) if 'size' in prod and prod['size'] else "NA",
                                             bank.config.get('server')))
        except OSError as e:
            Utils.error("Can't access file: %s" % str(e))
        except IOError as e:
            Utils.error("Can't write to file %s: %s" % (file, str(e)))
        finally:
            fv.close()
        return 0

    def set_bank(self, bank):
        """
        Set a bank for the current Manager
        :param bank: biomaj.bank.Bank
        :return: Boolean
        """
        if not bank or bank is None:
            return False
        if bank is Bank:
            self.bank = bank
            return True
        return False

    def set_bank_from_name(self, name):
        """
        Set a bank from a bank name
        :param name: Name of the bank to set
        :type name: String
        :return: Boolean
        """

        if not name or name is None:
            return False
        bank = Bank(name=name, no_log=True)
        self.bank = bank
        return True

    @bank_required
    def show_pending_session(self, show=False, fmt="psql"):
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

        banks = self.get_bank_list()
        for bank in banks:
            self.bank = Bank(name=bank, no_log=True)
            if self.can_switch():
                banks[self.bank.name] = self.bank
            self.bank = None
        return banks

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

        if not 'last_update_session' in self.bank.bank:
            Utils.errors("No last session recorded")
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
                        if 'over' in session['status'] and session['status']['over']:
                            ready = True

        return ready

    """
    Private methods
    """

    def _current_user(self):
        """
        Determine user running the actual manager. We search for login name
        then enviroment 'LOGNAME' variable

        :return: String
        """
        logname = None

        if 'LOGNAME' in os.environ:
            logname = os.getenv('LOGNAME')
        elif 'USER' in os.environ:
            logname = os.getenv('USER')
        current_user = os.getlogin() or logname
        if not current_user:
            Utils.error("Can't find current user name")

        return current_user

    def _get_formats_for_release(self, path):
        """
            Get all the formats supported for a bank (path).
            :param path: Path of the release to search in
            :type path: String (path)
            :return: List of formats
        """

        if not path:
            Utils.error("A path is required")
        if not os.path.exists(path):
            Utils.warn("Path %s does not exist" % path)
            return []
        formats = []

        for dir, dirs, filenames in os.walk(path):
            if dir == path or not len(dirs):
                continue
            if dir == 'flat' or dir == 'uncompressed':
                continue
            for d in dirs:
                formats.append('@'.join(['prog', os.path.basename(dir), d or '-']))
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
