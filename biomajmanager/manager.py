from __future__ import print_function

from biomaj.bank import Bank
from biomaj.config import BiomajConfig
from biomaj.mongo_connector import MongoConnector
from datetime import datetime
from time import time
from biomajmanager.utils import Utils
import re
import os
import sys
import string


def bank_required(func):
    """
    Decorator function that check a bank name is set
    :param func:
    :return:
    """

    def _check_bank_required(*args, **kwargs):
        """
        """

        self = args[0]
        if self.bank is None:
            Utils.error("A bank name is required")
        return func(*args, **kwargs)
    return _check_bank_required

def user_granted(func):
    """
    Decorator that check a user has enough right to perform action
    :param func: Decorated function
    :type: Function
    :return:
    """
    def _check_user_granted(*args, **kwargs):
        """
        Check the user has enough right to perform action(s)
        If a bank is set, we first set the user as the owner of
        the current bank. Otherwise we try to find it from the
        config file, we search for 'user.admin' property

        :return: Boolean
        """

        self = args[0]
        admin = None
        props = self.bank.get_properties()
        if 'owner' in props and props['owner']:
            admin = props['owner']
        else:
            admin = self.bank.config.get('user.admin')
            if not admin:
                Utils.error("'user.admin' not set")

        user = self._current_user

        if admin != user:
            Utils.error("User %s, permission denied" % user)
        return func(*args, **kwargs)
    return _check_user_granted


class Manager(object):

    def __init__(self, bank=None, simulate=False):

        # Our bank
        self.bank = None
        # The root installation of biomaj3
        self.root = None
        # Where to find global.properties
        self.config = None
        # Where data are located
        self.bank_prod = None
        # Current release of the bank
        self._current_release = None
        # Previous release of the bank
        self._previous_release = None
        # Simulation mode
        self.simulate = simulate

        try:
            if not 'BIOMAJ_CONF' in os.environ:
                Utils.error("BIOMAJ_CONF is not set")
            else:
                self.config = Manager.load_config()
                self.bank_prod = self.config.get('GENERAL', 'data.dir')
        except Exception as e:
            Utils.error(str(e))

        if bank is not None:
            self.bank = Bank(name=bank, no_log=True)
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
    def load_config(file=None):
        """
        Load biomaj-manager configuration file (manager.properties). It uses BiomajConfig.load_config()
        to first load global.properties and determine where the config.dir is. manager.properties must
        be located at the same place as global.properties
        If a file is given, it will be searched and loaded from the same location as manager.properties
        :param file: Config file to load
        :type file: String
        :return: ConfigParser object
        :rtype: configparser.SafeParser
        """
        BiomajConfig.load_config()
        conf_dir = os.path.dirname(BiomajConfig.config_file)
        cfg = None
        if not os.path.isdir(conf_dir):
            Utils.error("Can't find config directory")
        if file:
            cfg = os.path.join(conf_dir, file)
        else:
            cfg = os.path.join(conf_dir, 'manager.properties')
        if not os.path.isfile(cfg):
            print("Can't find config file %s" % cfg)
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

    @bank_required
    def can_switch(self):
        """
        Check if a bank can be updated and put into production as 'current'

        :return: Boolean
        """
        # Bank is updating?
        if self.bank.is_locked():
            print("[%s] Bank is being updated" % self.bank.name)
            return False
        # None of the symlink are there?
        if not os.path.islink(self.get_current_link()) and not os.path.islink(self.get_future_link()):
            print("[%s] Bank has no 'current' nor 'future_release' link")
            return False
        # Bank construction failed?
        if self.last_session_failed():
            print("[%s] Last session failed" % self.bank.name)
            return False
        # 'current' link and 'future_release' links are there?
        if not self.update_ready():
            print("[%s] Bank is not ready" % self.bank.name)
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
        if 'production' in self.bank.bank and len(self.bank.bank['production']) > 0:
            production = self.bank.bank['production'][-1]
            current = production['release'] or production['remoterelease']
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
        return os.path.sep().join([self.bank.config.get('data.dir'),
                                   self.bank.name,
                                   'current'])

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
        return os.path.sep().join([self.bank.config.get('data.dir'),
                                   self.bank.name,
                                   'future_release'])

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
        fmts = self.formats()
        print("Formats: %s" % str(fmts))
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
                'created': datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d %H:%M:%S"),
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
                    'created': datetime.fromtimestamp(sess['id']).strftime(("Y%-%m-%d %H:%M:%S")),
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
        Check if the last session building the bank failed or not

        :return:Boolean
        """

        has_failed = True
        session_id = None

        if 'last_update_session' in self.bank.bank and self.bank.bank['last_update_session']:
            session_id = self.bank.bank['last_update_session']
        if 'sessions' in self.bank.bank and self.bank.bank['sessions']:
            length = len(self.bank.bank['sessions'])
            index = 1
            for session in self.bank.bank['sessions']:
                if session_id and session['id'] == session_id:
                    has_failed = session['id']['status']['over']
                    break
                if index == length:
                    has_failed = session['id']['status']['over']
                    break
                index += 1
        else:
            # Can't determine if session failed or not
            has_failed = True
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
                for key in self.get_config_regex(regex='^'+plugin, section='PLUGINS', want_values=False):
                    print("%s=%s" % (key, self.config.get('PLUGINS', key)))

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

        # Check db.packages is set for the current bank
        if not self.bank.config.get('db.packages'):
            Utils.warn("[%s] db.packages not set!" % self.bank.name)
            return []
        description = self.bank.config.get('db.fullname').strip()
        packages = self.bank.config.get('db.packages').replace('\\', '').replace('\n', '').strip().split(',')
        bank_type = self.bank.config.get('db.type').split(',')
        bank_format = self.bank.config.get('db.formats').split(',')

        for prod in productions:
            history.append({'_id': '@'.join(['bank',
                                             self.bank.name,
                                             prod['remoterelease'],
                                             datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d_%H:%M:%S")]),
                             'type': 'bank',
                             'name': self.bank.name,
                             'version': prod['remoterelease'],
                             'publication_date': datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d %H:%M:%S"),
                             'removal_date': None,
                             'bank_type': bank_type,
                             'bank_format': bank_format,
                             'packages': packages,
                             'description': description,
                            })
        for sess in sessions:
            # Don't repeat production item stored in sessions
            new_id = '@'.join(['bank',
                               self.bank.name,
                               sess['remoterelease'],
                               datetime.fromtimestamp(sess['id']).strftime("%Y-%m-%d_%H:%M:%S")])
            if new_id in map(lambda d: d['_id'], history):
                continue

            history.append({'_id': '@'.join(['bank',
                                             self.bank.name,
                                             sess['remoterelease'],
                                             datetime.fromtimestamp(sess['id']).strftime("%Y-%m-%d_%H:%M:%S")]),
                            'type': 'bank',
                            'name': self.bank.name,
                            'version': sess['remoterelease'],
                            'publication_date': datetime.fromtimestamp(sess['last_update_time']).strftime("%Y-%m-%d %H:%M:%S"),
                            'removal_date': sess['last_modified'] if 'remove_release' in sess['status'] and sess['status']['remove_release'] == True
                                                                  else None,
                            'bank_type': bank_type,
                            'bank_formats': bank_format,
                            'packages': packages,
                            'description': description,
                            })
        return history

    @bank_required
    @user_granted
    def save_banks_version(self, file=None):
        """
        Save versions of bank when switching bank version (publish)
        :param file: Path to save banks version (String)
        :return: 0
        :raise: Exception
        """

        if not file:
            file = os.path.sep().join([self.bank_prod,
                                       'doc',
                                       'versions',
                                       'version.' + datetime.now().strftime("%Y%M%d")])
        try:
            os.path.exists(file)
            banks = self.bank.list()
            with open(file, mode='w') as fv:
                for bank in banks:
                    bank = Bank(bank)
                    if 'current' in bank and bank['current'] and 'production' in bank:
                        for prod in bank['production']:
                            if bank['current'] == prod['session']:
                                fv.write("%-20s\t%-30s\t%-20s\t%-20s\t%-20s"
                                % (bank.name, "Release " + prod['release'],
                                datetime.datetime.fromtimestamp(prod['session']).strftime('%Y-%m-%d %H:%M:%S')),
                                str(prod['size']) if 'size' in prod and prod['size'] else "NA")
        except OSError as e:
            Utils.error("Can't access file: %s" % str(e))
        except IOError as e:
            Utils.error("Can't write to file %s: %s" % (file, str(e)))
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

    @staticmethod
    @bank_required
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

        blist = self.get_bank_list()
        for bank in blist:
            self.bank = Bank(name=bank, no_log=True)
            if self.can_switch():
                banks[self.bank.name] = self.bank
        self.bank = None
        return banks

    def start_timer(self):
        """
        Start the timer
        :return: Boolean
        """

        self._timer_start = time()
        return True

    def stop_timer(self):
        """
        Stop the timer
        :return: Boolean
        """
        self._timer_stop = time()
        return True

    @bank_required
    def update_ready(self):
        """
        Check the update is ready to be published. We check we have old release ('current' link)
        and 'future_release' link, as well as '.done' file created by our last postprocess
        If the user don't use '.done' file as last postprocess, then we always return True
        unless 'current' and 'future_release' are not there.

        :return: Boolean
        """
        ready = False
        if os.path.islink(self.get_current_link()) and os.path.islink(self.get_future_link()):
            ready = True
        if self.bank.config.get('done.file'):
            done_file = self.bank.config.get('done.file')
            last_session = self._get_last_session()
            done = os.path.sep.join([self.bank.config.get('data.dir'),
                                     self.bank.name,
                                     last_session['prod_dir'],
                                     done_file])
            if not os.path.isfile(done):
                ready = False
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

    #def _error(self, msg):
    #    print('[ERROR] ' + msg, file=sys.stderr)
    #    sys.exit(1)

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
            print("[WARNING] Path %s does not exist" % path)
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
