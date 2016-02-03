from __future__ import print_function
from nose.tools import *
from nose.plugins.attrib import attr

import shutil
import os
import sys
import tempfile
import time
import unittest
from pymongo import MongoClient
from datetime import datetime

from biomajmanager.utils import Utils
from biomajmanager.news import News
from biomajmanager.manager import Manager


__author__ = 'tuco'


class UtilsForTests(object):
    """
    Copy properties files into a temporary directory and update properties
    to use a temp directory
    """

    def __init__(self):
        '''
        Setup the temp dirs and files.
        '''
        self.global_properties = None
        self.manager_properties = None
        self.db_test = 'bm_db_test'
        self.col_test = 'bm_col_test'
        self.test_dir = tempfile.mkdtemp('biomaj-manager_tests')

        # Global part
        self.conf_dir = os.path.join(self.test_dir, 'conf')
        if not os.path.exists(self.conf_dir):
            os.makedirs(self.conf_dir)
        self.data_dir = os.path.join(self.test_dir, 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.log_dir = os.path.join(self.test_dir, 'log')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.process_dir = os.path.join(self.test_dir, 'process')
        if not os.path.exists(self.process_dir):
            os.makedirs(self.process_dir)
        self.lock_dir = os.path.join(self.test_dir, 'lock')
        if not os.path.exists(self.lock_dir):
            os.makedirs(self.lock_dir)
        self.cache_dir = os.path.join(self.test_dir, 'cache')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        # Manager part
        self.template_dir = os.path.join(self.test_dir, 'templates')
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
        self.news_dir = os.path.join(self.test_dir, 'news')
        if not os.path.exists(self.news_dir):
            os.makedirs(self.news_dir)
        self.prod_dir = os.path.join(self.test_dir,'production')
        if not os.path.exists(self.prod_dir):
            os.makedirs(self.prod_dir)
        self.plugins_dir = os.path.join(self.test_dir,'plugins')
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
        self.tmp_dir = os.path.join(self.test_dir, 'tmp')
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        if self.global_properties is None:
            self.__copy_test_global_properties()

        if self.manager_properties is None:
            self.__copy_test_manager_properties()

        # Set a mongo client
        self.mongo_client = MongoClient('mongodb://localhost:27017')

    def copy_file(self, file=None, todir=None):
        """
        Copy a file from the test dir to temp test zone
        :param file: File to copy
        :param todir: Destinatin directory
        :return:
        """
        curdir = self.__get_curdir()
        fromdir = os.path.join(curdir, file)
        todir = os.path.join(todir, file)
        shutil.copyfile(fromdir, todir)

    def copy_news_files(self):
        """
        Copy news file from test directory to 'news' testing directory
        :return:
        """
        curdir = self.__get_curdir()
        for news in ['news1.txt', 'news2.txt', 'news3.txt']:
            from_news = os.path.join(curdir, news)
            to_news = os.path.join(self.news_dir, news)
            shutil.copyfile(from_news, to_news)

    def copy_plugins(self):
        """
        Copy plugins from test directory to 'plugins' testing directory
        :return:
        """
        dsrc = 'tests/plugins'
        for file in os.listdir(dsrc):
            shutil.copyfile(os.path.join(dsrc, file),
                            os.path.join(self.plugins_dir, file))

    def clean(self):
        '''
        Deletes temp directory
        '''
        shutil.rmtree(self.test_dir)

    def drop_db(self):
         """
         Drop the mongo database after using it and close the connection
         :return:
         """
         self.mongo_client.drop_database(self.db_test)
         self.mongo_client.close()

    def print_err(self, msg):
        """
        Prints message on sys.stderr
        :param msg:
        :return:
        """
        print(msg, file=sys.stderr)

    def __get_curdir(self):
        """
        Get the current directory
        :return:
        """
        return os.path.dirname(os.path.realpath(__file__))

    def __copy_test_manager_properties(self):

        self.manager_properties = os.path.join(self.conf_dir, 'manager.properties')
        curdir = self.__get_curdir()
        manager_template = os.path.join(curdir, 'manager.properties')
        mout = open(self.manager_properties, 'w')
        with open(manager_template, 'r') as min:
            for line in min:
                if line.startswith('template.dir'):
                    mout.write("template.dir=%s\n" % self.template_dir)
                elif line.startswith('news.dir'):
                    mout.write("news.dir=%s\n" % self.news_dir)
                elif line.startswith('production.dir'):
                    mout.write("production.dir=%s\n" % self.prod_dir)
                elif line.startswith('plugins.dir'):
                    mout.write("plugins.dir=%s\n" % self.plugins_dir)
                else:
                    mout.write(line)
        mout.close()

    def __copy_test_global_properties(self):

        self.global_properties = os.path.join(self.conf_dir, 'global.properties')
        curdir = os.path.dirname(os.path.realpath(__file__))
        global_template = os.path.join(curdir, 'global.properties')
        fout = open(self.global_properties, 'w')
        with open(global_template, 'r') as fin:
            for line in fin:
                if line.startswith('cache.dir'):
                    fout.write("cache.dir=%s\n" % self.cache_dir)
                elif line.startswith('conf.dir'):
                    fout.write("conf.dir=%s\n" % self.conf_dir)
                elif line.startswith('log.dir'):
                    fout.write("log.dir=%s\n" % self.log_dir)
                elif line.startswith('data.dir'):
                    fout.write("data.dir=%s\n" % self.data_dir)
                elif line.startswith('process.dir'):
                    fout.write("process.dir=%s\n" % self.process_dir)
                elif line.startswith('lock.dir'):
                    fout.write("lock.dir=%s\n" % self.lock_dir)
                else:
                    fout.write(line)


class TestBiomajManagerUtils(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()

    def tearDown(self):
        self.utils.clean()

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_deepest_dir_ErrorNoPath(self):
        """
        Check methods checks are OK
        :return:
        """
        with self.assertRaises(SystemExit):
            Utils.get_deepest_dirs()

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_deepest_dir_ErrorPathNotExists(self):
        """
        Check methods checks are OK
        :return:
        """
        with self.assertRaises(SystemExit):
            Utils.get_deepest_dirs(path='/not_found')

    @attr('utils')
    @attr('utils.deepestdir')
    def test_deepest_dir(self):
        """
        Check we get the right deepest dir from a complete path
        :return:
        """
        dir = os.path.join(self.utils.tmp_dir, 'a', 'b', 'c')
        if not os.path.exists(dir):
            os.makedirs(dir)
        deepest = Utils.get_deepest_dir(dir)
        self.assertEqual(deepest, 'c')
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdir')
    def test_deepest_dir_full(self):
        """
        Check we get the right full deepest dir
        :return:
        """
        dir = os.path.join(self.utils.tmp_dir, 'a', 'b', 'c', 'd')
        if not os.path.exists(dir):
            os.makedirs(dir)
        deepest = Utils.get_deepest_dir(dir, full=True)
        self.assertEqual(deepest, dir)
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdir')
    def test_deepest_dir(self):
        """
        Check we get the right list of deepest dir
        :return:
        """
        dir = os.path.join(self.utils.tmp_dir, 'a', 'b')
        dir1 = os.path.join(dir, 'c')
        dir2 = os.path.join(dir, 'd')
        for d in [dir1, dir2]:
            if not os.path.exists(d):
                os.makedirs(d)
        deepest = Utils.get_deepest_dir(dir)
        self.assertEqual(len(deepest), 1)
        self.assertEqual(deepest[0], 'c')
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_deepest_dirs(self):
        """
        Check we get the right list of deepest dir
        :return:
        """
        dir = os.path.join(self.utils.tmp_dir, 'a', 'b')
        dir1 = os.path.join(dir, 'c')
        dir2 = os.path.join(dir, 'd')
        for d in [dir1, dir2]:
            if not os.path.exists(d):
                os.makedirs(d)
        deepest = Utils.get_deepest_dirs(dir)
        c = deepest[0]
        d = deepest[1]
        self.assertEqual(c, 'c')
        self.assertEqual(d, 'd')
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_deepest_dirs_full(self):
        """
        Check we get the right list of deepest dir
        :return:
        """
        dir = os.path.join(self.utils.tmp_dir, 'a', 'b')
        dir1 = os.path.join(dir, 'c')
        dir2 = os.path.join(dir, 'd')
        for d in [dir1, dir2]:
            if not os.path.exists(d):
                os.makedirs(d)
        deepest = Utils.get_deepest_dirs(dir, full=True)
        c = deepest[0]
        d = deepest[1]
        self.assertEqual(c, dir1)
        self.assertEqual(d, dir2)
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    def test_get_files(self):
        """
        Check we get the right file list from a directory
        :return:
        """
        tmp_file1 = os.path.join(self.utils.tmp_dir, '1foobar.tmp')
        tmp_file2 = os.path.join(self.utils.tmp_dir, '2foobar.tmp')
        open(tmp_file1, mode='a').close()
        open(tmp_file2, mode='a').close()
        files = Utils.get_files(self.utils.tmp_dir)
        b_tmp_file1 = os.path.basename(tmp_file1)
        b_tmp_file2 = os.path.basename(tmp_file2)
        self.assertEqual(b_tmp_file1, files[0])
        self.assertEqual(b_tmp_file2, files[1])
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    def test_get_files_ErrorNoPath(self):
        """
        Check we get an error when omitting args
        :return:
        """
        with self.assertRaises(SystemExit):
            Utils.get_files()

    @attr('utils')
    def test_get_files_ErrorPathNotExists(self):
        """
        Check we get an error when omitting args
        :return:
        """
        with self.assertRaises(SystemExit):
            Utils.get_files(path='/not_found')

    @attr('utils')
    def test_elapsedTime_Error(self):
        """
        Check this method throw an error
        :return:
        """
        with self.assertRaises(SystemExit):
            Utils.elapsed_time()

    @attr('utils')
    def test_elapsedtime_NoTimerStop(self):
        """
        Check we go deeper in method setting time_stop to None
        :return:
        """
        Utils.timer_stop = None
        Utils.start_timer()
        self.assertIsInstance(Utils.elapsed_time(), float)

    # @attr('utils')
    # def test_local2utc(self):
    #     """
    #     Check local2utc returns the right time according to local time
    #     :return:
    #     """
    #     now = datetime.now()
    #     utc_now = Utils.local2utc(now)
    #     self.assertEquals(utc_now.hour + 1, now.hour)
    #
    # @attr('utils')
    # def test_local2utc_WrongArgsType(self):
    #     """
    #     We check the args instance checking throws an error
    #     :return:
    #     """
    #     with self.assertRaises(SystemExit):
    #         Utils.local2utc(int(2))

    @attr('utils')
    def test_time2date_NoArgs(self):
        """
        Check the method throws an error if no args given
        :return:
        """
        with self.assertRaises(TypeError):
            Utils.time2date()

    @attr('utils')
    def test_time2date_ReturnedOK(self):
        """
        Check value returned is right object
        :return:
        """
        self.assertIsInstance(Utils.time2date(time.time()), datetime)

    @attr('utils')
    def test_time2datefmt_NoArgs(self):
        """
        Check the method throws an error if no args given
        :return:
        """
        with self.assertRaises(TypeError):
            Utils.time2datefmt()

    @attr('utils')
    def test_time2datefmt_ReturnedOK(self):
        """
        Check value returned is right object
        :return:
        """
        self.assertIsInstance(Utils.time2datefmt(time.time(), Manager.DATE_FMT), str)

    @attr('utils')
    def test_userOK(self):
        """
        Check the testing user is ok
        :return:
        """
        user = os.getenv("USER")
        self.assertEqual(Utils.user(), user)

    @attr('utils')
    def test_userNOTOK(self):
        """
        Check the testing user is ok
        :return:
        """
        user = "fakeUser"
        self.assertNotEqual(Utils.user(), user)


class TestBiomajManagerNews(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        self.utils.clean()

    @attr('manager')
    @attr('manager.news')
    def test_NewWithMaxNews(self):
        """
        Check max_news args is OK
        :return:
        """
        news = News(max_news=10)
        self.assertEqual(news.max_news, 10)

    @attr('manager')
    @attr('manager.news')
    def test_NewWithConfigOK(self):
        """
        Check init set everthing from config as arg
        :return:
        """
        manager = Manager()
        news_dir = manager.config.get('MANAGER', 'news.dir')
        news = News(config=manager.config)
        self.assertEqual(news_dir, news.news_dir)

    @attr('manager')
    @attr('manager.news')
    def test_NewWithConfigNoSection(self):
        """
        Check init throws because config has no section 'MANAGER'
        :return:
        """
        manager = Manager()
        manager.config.remove_section('MANAGER')
        with self.assertRaises(SystemExit):
            News(config=manager.config)

    @attr('manager')
    @attr('manager.news')
    def test_NewWithConfigNoOption(self):
        """
        Check init throws because config has no option 'news.dir
        :return:
        """
        manager = Manager()
        manager.config.remove_option('MANAGER', 'news.dir')
        with self.assertRaises(SystemExit):
            News(config=manager.config)

    @attr('manager')
    @attr('manager.news')
    def test_NewsNewsDirOK(self):
        """
        Check get_news set correct thing
        :return:
        """
        news = News()
        news.get_news(news_dir="/tmp")
        self.assertEqual(news.news_dir, "/tmp")

    @attr('manager')
    @attr('manager.news')
    def test_NewsDirNotADirectory(self):
        """
        Check the dir given is not a directory
        :return:
        """
        with self.assertRaises(SystemExit):
            News(news_dir="/foobar")

    @attr('manager')
    @attr('manager.news')
    def test_NewsGetNewsWrongDirectory(self):
        """
        Check method throws exception with wrong dir calling get_news
        :return:
        """
        news = News()
        with self.assertRaises(SystemExit):
            news.get_news(news_dir='/not_found')

    @attr('manager')
    @attr('manager.news')
    def test_NewsGetNewsNewsDirNotDefined(self):
        """
        Check method throws exception while 'news.dir' not defined
        :return:
        """
        news = News()
        with self.assertRaises(SystemExit):
            news.get_news()

    @attr('manager')
    @attr('manager.news')
    def test_FileNewsContentEqual(self):
        """
        Check the content of 2 generated news files are identical
        :return:
        """

        self.utils.copy_news_files()
        data = []
        for i in range(1, 4):
            data.append({'type': 'type' + str(i),
                         'date': str(i) + '0/12/2015',
                         'title': 'News%s Title' % str(i),
                         'text': 'This is text #%s from news%s' %  (str(i), str(i)),
                         'item': i-1})
        news = News(news_dir=self.utils.news_dir)
        news_data = news.get_news()
        # Compare data
        data.reverse()

        if 'news' in news_data:
            for d in news_data['news']:
                n = data.pop()
                for k in ['type', 'date', 'title', 'text', 'item']:
                    self.assertEqual(d[k], n[k])
        else:
            raise(unittest.E)
        shutil.rmtree(self.utils.news_dir)


class TestBioMajManagerDecorators(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        self.utils.clean()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorBankRequiredOK(self):
        """
        Test we've got a bank name set
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        sections = manager.get_dict_sections('blast2')
        expected = {'nuc': {'dbs': ['alunuc'], 'secs': ['alunuc1', 'alunuc2']},
                    'pro': {'dbs': ['alupro'], 'secs': ['alupro1', 'alupro2']}}
        self.assertDictContainsSubset(expected, sections)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorBankRequiredNotOK(self):
        """
        Test we've got a bank name set
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager.get_dict_sections('blast2')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsUserGrantedOK(self):
        """
        Test the user is granted
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.save_banks_version(file=self.utils.test_dir + '/saved_versions.txt')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsUserGrantedNotOK(self):
        """
        Test the user is granted
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # Just change the env LOGNAME do misfit with db user
        cuser = os.environ.get('LOGNAME')
        os.environ['LOGNAME'] = "fakeuser"
        with self.assertRaises(SystemExit):
            manager.save_banks_version(file=self.utils.test_dir + '/saved_versions.txt')
        # Reset to the right user name as previously
        os.environ['LOGNAME'] = cuser
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsUserGrantedAdminNotSet(self):
        """
        Test the user is granted
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # Unset admin from config file and owner from the bank just created
        manager.config.set('GENERAL', 'admin', '')
        manager.bank.bank['properties']['owner'] = ''
        with self.assertRaises(SystemExit):
            manager.save_banks_version(file=self.utils.test_dir + '/saved_versions.txt')
        self.utils.drop_db()


class TestBioMajManagerManager(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        self.utils.clean()

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerNoConfigRaisesException(self):
        """
        Check an exception is raised while config loading
        :return:
        """
        with self.assertRaises(SystemExit):
            Manager(cfg="/no_manager_cfg", global_cfg="/no_global_cfg")

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerGlobalConfigException(self):
        """
        Check an exception is raised config loading
        :return:
        """
        with self.assertRaises(SystemExit):
            Manager(global_cfg="/no_global_cfg")

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ConfigNoManagerSection(self):
        """
        Check we don't have a 'MANAGER' section in our config
        :return:
        """
        no_sec = 'manager-nomanager-section.properties'
        self.utils.copy_file(file=no_sec, todir=self.utils.conf_dir)
        cfg = Manager.load_config(cfg=os.path.join(self.utils.conf_dir, no_sec))
        self.assertFalse(cfg.has_section('MANAGER'))

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerLoadConfig(self):
        """
        Check we can load any configuration file on demand
        :return:
        """
        for file in ['m1.properties', 'm2.properties', 'm3.properties']:
            self.utils.copy_file(file=file, todir=self.utils.test_dir)
            cfg = Manager.load_config(cfg=os.path.join(self.utils.test_dir, file))
            self.assertTrue(cfg.has_section('MANAGER'))
            self.assertEqual(cfg.get('MANAGER', 'file.name'), file)

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerLoadConfigNOTOK(self):
        """
        Check we throw an error when no 'manager.properties' found
        :return:
        """
        os.remove(os.path.join(self.utils.conf_dir, 'manager.properties'))
        with self.assertRaises(SystemExit):
            Manager.load_config(global_cfg=os.path.join(self.utils.conf_dir, 'global.properties'))

    @attr('manager')
    @attr('manager.bankinfo')
    def test_ManagerBankInfo(self):
        """
        Check method returns right info about a bank
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        self.maxDiff = None
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now, 'last_update_session': now,
                                                             'properties.type': ['nucleic', 'protein']},
                                                    '$push': {'production': {'session': now,
                                                                             'release': '54',
                                                                             'remoterelease': '54',
                                                                             'prod_dir': "alu"}},
                                                    })
        manager.bank.bank = manager.bank.banks.find_one({'name': 'alu'})
        returned = manager.bank_info()
        expected = {'info': [["Name", "Type(s)", "Last update status", "Published release"],
                             ["alu", "nucleic,protein", Utils.time2datefmt(now, Manager.DATE_FMT), '54']],
                    'prod': [["Session", "Remote release", "Release", "Directory", "Freeze", "Pending"],
                             [Utils.time2datefmt(now, Manager.DATE_FMT), '54', '54',
                              os.path.join(manager.bank.config.get('data.dir'),
                                           manager.bank.config.get('dir.version'),"alu"),
                              'no']],
                    'pend': []}
        self.assertDictEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankpublished')
    def test_ManagerBankPublishedTrue(self):
        """
        Check a bank is published or not (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        # at begining, biomaj create an empty bank entry into Mongodb
        manager = Manager(bank='alu')
        # If we do update we need to change 'bank_is_published' call find and iterate over the cursor to do the same test
        manager.bank.bank['current'] = True
        self.assertTrue(manager.bank_is_published())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankpublished')
    def test_ManagerBankPublishedFalse(self):
        """
        Check a bank is published or not (False)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        # at begining, biomaj create an empty bank entry into Mongodb
        manager = Manager(bank='alu')
        # If we do update we need to change 'bank_is_published' call find and iterate over the cursor to do the same test
        manager.bank.bank['current'] = None
        self.assertFalse(manager.bank_is_published())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedFalseNoPendingFalse(self):
        """
        Check we have a failed session and no pending session(s)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'status': {'over': True}}, {'id': now, 'status':{'over': True}}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertFalse(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedTrueNoPendingTrue(self):
        """
        Check we have a failed session and no pending session(s)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'status': {'over': True}}, {'id': now, 'status':{'over': True}}],
                'last_update_session': now,
                'pending': {'12345': now}
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        Utils.show_warn = False
        self.assertTrue(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedTrueNoPendingFalse(self):
        """
        Check we have a failed session and no pending session(s)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'status': {'over': True}}, {'id': now, 'status':{'over': False}}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        Utils.show_warn = False
        self.assertTrue(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankHasFormatNoFormat(self):
        """
        Check missing arg raises error
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.has_formats()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankHasFormatsTrue(self):
        """
        Check if the bank has a specific format (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertTrue(manager.has_formats(fmt='blast'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankHasFormatsFalse(self):
        """
        Check if the bank has a specific format (False)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_formats(fmt='unknown'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankFormatsFlatFalseOK(self):
        """
        Check if the bank has a specific format (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.formats()
        expected = ['blast@2.2.26', 'fasta@3.6']
        self.assertListEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankFormatsFlatTrueOK(self):
        """
        Check if the bank has a specific format (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.formats(flat=True)
        expected = {'blast': ['2.2.26'], 'fasta': ['3.6']}
        self.assertDictEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankFormatsAsStringOK(self):
        """
        Check if the bank has a specific format returned as string (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.formats_as_string()
        expected = {'blast': ['2.2.26'], 'fasta': ['3.6']}
        self.assertDictEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNotNone(self):
        """
        Check we retrieve the right session id (Not None)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'status': { 'over': True}},
                             {'id': 2, 'status': { 'over': True}}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertIsNotNone(manager.get_session_from_id(1))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNone(self):
        """
        Check we retrieve the right session id (None)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'status': { 'over': True}},
                             {'id': 2, 'status': { 'over': True}}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertIsNone(manager.get_session_from_id(3))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNone(self):
        """
        Check method raises exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'status': { 'over': True}},
                             {'id': 2, 'status': { 'over': True}}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        with self.assertRaises(SystemExit):
            manager.get_session_from_id(None)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getpendingsessions')
    def test_ManagerGetPendingSessionsOK(self):
        """
        Check method returns correct pending session
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        expected = {54: now, 55: now+1}
        manager.bank.bank['pending'] = expected
        returned_list = manager.get_pending_sessions()
        returned = {}
        for item in returned_list:
            returned[item['release']] = item['session_id']
        self.assertDictEqual(expected, returned)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.showpendingsessions')
    def test_ManagerShowPendingSessionsOK(self):
        """
        Check method returns correct pending session
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        expected = {54: now, 55: now+1}
        manager.bank.bank['pending'] = expected
        returned_list = manager.show_pending_sessions()
        returned = {}
        for item in returned_list:
            returned[item['release']] = item['session_id']
        self.assertDictEqual(expected, returned)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getpublishedrelease')
    def test_ManagerGetPublishedReleaseNotNone(self):
        """
        Check we get a the published release (NotNone)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = 'R54'
        data = {'name': 'alu',
                'current': now,
                'sessions': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'remoterelease': release}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        rel = manager.get_published_release()
        self.assertIsNotNone(rel)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getpublishedrelease')
    def test_ManagerGetPublishedReleaseNone(self):
        """
        Check we get a the published release (None)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = 'R54'
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'remoterelease': release}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        rel = manager.get_published_release()
        self.assertIsNone(rel)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getpublishedrelease')
    def test_ManagerGetPublishedReleaseRaisesOK(self):
        """
        Check method raises an exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = 'R54'
        data = {'name': 'alu', 'current': now,
                'sessions': [{'id': 1 }, {'id': now }]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        with self.assertRaises(SystemExit):
            manager.get_published_release()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetDictSections(self):
        """
        Get sections for a bank
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        dsections = manager.get_dict_sections(tool='blast2')
        expected = {'pro': {'dbs': ['alupro'], 'secs': ['alupro1', 'alupro2']},
                    'nuc': {'dbs': ['alunuc'], 'secs': ['alunuc1', 'alunuc2']}}
        self.assertDictContainsSubset(expected, dsections)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetDictSectionsOnlySectionsOK(self):
        """
        Test we've got only sections not db from bank properties
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        sections = manager.get_dict_sections('golden')
        expected = {'nuc': {'secs': ['alunuc']},
                    'pro': {'secs': ['alupro']}}
        self.assertDictContainsSubset(expected, sections)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetListSectionsGolden(self):
        """
        Check we get rigth sections tool bank name for bank
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        lsections = manager.get_list_sections(tool='golden')
        self.assertListEqual(lsections, ['alunuc', 'alupro'])
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetListSectionsBlast2(self):
        """
        Check we get rigth sections bank and subsection for bank
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        lsections = manager.get_list_sections(tool='blast2')
        self.assertListEqual(lsections, ['alunuc', 'alupro','alunuc1','alunuc2', 'alupro1', 'alupro2'])
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetDictSectionsNoTool(self):
        """
        Get sections for a bank
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_dict_sections()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetListSectionsNoTool(self):
        """
        Get sections for a bank
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_list_sections()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_CurrentSet(self):
        """

        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager._current_release = str(54)
        self.assertEqual(str(54), manager.current_release())

    @attr('manager')
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_CurrentANDSessions(self):
        """
        Check we get the right current release
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = 'R54'
        data = {'name': 'alu',
                'current': now,
                'sessions': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'remoterelease': release}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertEqual(release, manager.current_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_ProductionRemoteRelease(self):
        """
        Check we get the right current release
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = 'R54'
        data = {'name': 'alu',
                'production': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'remoterelease': release}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertEqual(release, manager.current_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_ProductionRelease(self):
        """
        Check we get the right current release
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = 'R54'
        data = {'name': 'alu',
                'production': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'release': release}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertEqual(release, manager.current_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentuser')
    def test_ManagerCurrentUserTestUSEROK(self):
        """
        Check we can get USER from environ with LOGNAME unset
        :return:
        """
        backlog = ""
        user = os.getlogin()
        if 'LOGNAME' in os.environ:
            backlog = os.environ['LOGNAME']
            del(os.environ['LOGNAME'])
        manager = Manager()
        self.assertEqual(manager._current_user(), user)
        if 'LOGNAME' not in os.environ:
            os.environ['LOGNAME'] = backlog

    @attr('manager')
    @attr('manager.currentuser')
    def test_ManagerCurrentUserTestUserIsNone(self):
        """
        Check method throws exception when env LOGNAME and USER not found
        :return:
        """
        manager = Manager()
        backup = os.environ.copy()
        os.environ = {}
        self.assertIsNone(manager._current_user())
        os.environ = backup

    @attr('manager')
    @attr('manager.currentlink')
    def test_ManagerGetCurrentLinkNOTOK(self):
        """
        Check get_current_link throws exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_current_link()
        self.assertNotEqual(cur_link, '/wrong_curent_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentlink')
    def test_ManagerGetCurrentLinkOK(self):
        """
        Check get_current_link throws exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_current_link()
        self.assertEqual(cur_link, os.path.join(self.utils.data_dir, manager.bank.name, 'current'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.futurelink')
    def test_ManagerGetFutureLinkNOTOK(self):
        """
        Check get_future_link throws exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_future_link()
        self.assertNotEqual(cur_link, '/wrong_future_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.futurelink')
    def test_ManagerGetFutureLinkOK(self):
        """
        Check get_future_link throws exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_future_link()
        self.assertEqual(cur_link, os.path.join(self.utils.data_dir, manager.bank.name, 'future_release'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hascurrentlink')
    def test_ManagerHasCurrentLinkFalse(self):
        """
        Check has_current_link returns False
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_current_link())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hascurrentlink')
    def test_ManagerHasCurrentLinkIsLinkTrue(self):
        """
        Check has_current_link returns True
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        link = os.path.join(self.utils.data_dir)
        os.symlink(os.path.join(link), 'test_link')
        self.assertTrue(manager.has_current_link(link='test_link'))
        os.remove('test_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hasfuturelink')
    def test_ManagerHasFutureLinkFalse(self):
        """
        Check has_future_link returns False
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_future_link())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hasfuturelink')
    def test_ManagerHasFutureLinkIsLinkOK(self):
        """
        Check has_future_link returns future link
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        link = os.path.join(self.utils.data_dir)
        os.symlink(os.path.join(link), 'future_link')
        self.assertTrue(manager.has_future_link(link='future_link'))
        os.remove('future_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDir_Raises(self):
        """
        Check method raises "Can't get current production directory: 'current_release' ..."
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDir_RaisesNoCurrentRelease(self):
        """
        Check method raises "Can't get current production directory: 'current_release' ..."
        release ok, prod not ok
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': '54'})
        manager.bank.bank['production'] = []
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDir_OK(self):
        """
        Check method returns path to production dir
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        prod_dir = 'alu_54'
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': '54'})
        manager.bank.bank['production'].append({'session': now, 'release': '54', 'data_dir': self.utils.data_dir,
                                                'prod_dir': prod_dir})
        returned = manager.get_current_proddir()
        expected = os.path.join(self.utils.data_dir, manager.bank.name, prod_dir)
        self.assertEqual(expected, returned)

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDir_RaisesNoProd(self):
        """
        Check method raises "Can't get current production directory, 'prod_dir' or 'data_dir' missing ..."
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        prod_dir = 'alu_54'
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': prod_dir})
        manager.bank.bank['production'].append({'session': now, 'release': prod_dir, 'data_dir': self.utils.data_dir})
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.getverbose')
    def test_ManagerGetVerboseTrue(self):
        """
        Check manager.get_verbose() get True when Manager.verbose = True
        :return:
        """
        Manager.verbose = True
        manager = Manager()
        self.assertTrue(manager.get_verbose())

    @attr('manager')
    @attr('manager.getverbose')
    def test_ManagerGetVerboseFalse(self):
        """
        Check manager.get_verbose() get False when Manager.verbose = False
        :return:
        """
        Manager.verbose = False
        manager = Manager()
        self.assertFalse(manager.get_verbose())

    @attr('manager')
    @attr('manager.getsimulate')
    def test_ManagerGetSimulateTrue(self):
        """
        Check manager.get_simulate() get True when Manager.simulate = True
        :return:
        """
        Manager.simulate = True
        manager = Manager()
        self.assertTrue(manager.get_simulate())

    @attr('manager')
    @attr('manager.getsimulate')
    def test_ManagerGetSimulateFalse(self):
        """
        Check manager.get_simulate() get False when Manager.simulate = False
        :return:
        """
        Manager.simulate = False
        manager = Manager()
        self.assertFalse(manager.get_simulate())

    @attr('manager')
    @attr('manager.banklist')
    def test_ManagerGetBankListOK(self):
        """
        Check bank list works OK
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        self.utils.copy_file(file='minium.properties', todir=self.utils.conf_dir)
        # Create 2 entries into the database
        Manager(bank='alu')
        Manager(bank='minium')
        manual_list = ['alu', 'minium']
        bank_list = Manager.get_bank_list()
        self.assertListEqual(bank_list, manual_list)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.banklist')
    def test_ManagerGetBankListBioMAJConfigNOTOK(self):
        """
        Check bank list throws SystemExit exception
        :return:
        """
        from biomaj.mongo_connector import MongoConnector
        from biomaj.config import BiomajConfig
        # Unset MongoConnector and env BIOMAJ_CONF to force config relaod and Mongo reconnect
        MongoConnector.db = None
        BiomajConfig.global_config = None
        back_cfg = os.environ["BIOMAJ_CONF"]
        os.environ['BIOMAJ_CONF'] = "/not_found"
        with self.assertRaises(SystemExit):
            Manager.get_bank_list()
        os.environ["BIOMAJ_CONF"] = back_cfg
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.banklist')
    def test_ManagerGetBankListMongoConnectorNOTOK(self):
        """
        Check bank list throws ServerSelectionTimeoutError ConnectionFailure exception
        :return:
        """
        from biomaj.mongo_connector import MongoConnector
        from biomaj.config import BiomajConfig
        # Unset MongoConnector and env BIOMAJ_CONF to force config relaod and Mongo reconnect
        config_file = 'global-wrongMongoURL.properties'
        self.utils.copy_file(file=config_file, todir=self.utils.conf_dir)
        MongoConnector.db = None
        BiomajConfig.load_config(config_file=os.path.join(self.utils.conf_dir, config_file))
        with self.assertRaises(SystemExit):
            Manager.get_bank_list()
        MongoConnector.db = None
        BiomajConfig.global_config = None
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getconfigregexp')
    def test_ManagerGetConfigRegExpOKWithValuesTrue(self):
        """
        Check method get the right entries from config
        :return:
        """
        manager = Manager()
        my_values = manager.get_config_regex(regex='.*\.dir$', with_values=False)
        expected = ['lock.dir', 'log.dir', 'process.dir', 'data.dir', 'cache.dir', 'conf.dir']
        self.assertListEqual(my_values, sorted(expected))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getconfigregexp')
    def test_ManagerGetConfigRegExpOKWithValuesFalse(self):
        """
        Check method get the right entries from config
        :return:
        """
        manager = Manager()
        my_values = manager.get_config_regex(regex='^db\.', with_values=True)
        self.assertListEqual(my_values, [self.utils.db_test, 'mongodb://localhost:27017'])
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getconfigregexp')
    def test_ManagerGetConfigRegExpNoRegExp(self):
        """
        Check method get the right entries from config
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_config_regex()

    @attr('manager')
    @attr('manager.getbankpackages')
    def test_ManagerGetBankPackagesOK(self):
        """
        Check get_bank_packages() is ok
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        packs = ['pack@blast@2.2.26', 'pack@fasta@3.6']
        bank_packs = manager.get_bank_packages()
        self.assertListEqual(packs, bank_packs)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getbankpackages')
    def test_ManagerGetBankPackagesNoneOK(self):
        """
        Check get_bank_packages() is ok
        :return:
        """
        self.utils.copy_file(file='minium.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='minium')
        bank_packs = manager.get_bank_packages()
        self.assertListEqual(bank_packs, [])
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getformatsforrelease')
    def test_ManagerGetFormatsForReleaseOK(self):
        """
        Check we get the right list for a bank supported formats
        :return:
        """
        expected = []
        for directory in ['flat', 'blast2/2.2.21', 'fasta/3.6', 'golden/3.0']:
            os.makedirs(os.path.join(self.utils.data_dir, directory))
            if directory == 'flat':
                continue
            expected.append('@'.join(['pack'] + directory.split('/')))
        manager = Manager()
        returned = manager._get_formats_for_release(path=self.utils.data_dir)
        self.assertListEqual(expected, returned)

    @attr('manager')
    @attr('manager.getformatsforrelease')
    def test_ManagerGetFormatsForReleaseRaises(self):
        """
        Check method throws error
        :return:
        """
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._get_formats_for_release()

    @attr('manager')
    @attr('manager.getformatsforrelease')
    def test_ManagerGetFormatsForReleasePathNotExistsEmptyList(self):
        """
        Check method throws error
        :return:
        """
        manager = Manager()
        returned = manager._get_formats_for_release(path="/not_found")
        self.assertListEqual(returned, [])

    @attr('manager')
    @attr('manager.getlastsession')
    def test_ManagerGetLastSessionOK(self):
        """
        Check method returns correct session
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['sessions'].append({'id': now, 'name': 'session1'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'name': 'session2'})
        manager.bank.bank['sessions'].append({'id': now + 2, 'name': 'session3'})
        returned = manager._get_last_session()
        self.assertDictEqual(returned, {'id': now +2, 'name': 'session3'})
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastsession')
    def test_ManagerGetLastSessionThrows(self):
        """
        Check method throws exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        del(manager.bank.bank['sessions'])
        with self.assertRaises(SystemExit):
            manager._get_last_session()
        self.utils.drop_db()
    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryNoProductionRaisesError(self):
        """
        Check when no 'production' field in bank, history raises exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'] = None
        with self.assertRaises(SystemExit):
            manager.history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryNoSessionsRaisesError(self):
        """
        Check when no 'sessions' field in bank, history raises exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12})
        manager.bank.bank['sessions'] = None
        with self.assertRaises(SystemExit):
            manager.history()
        self.utils.drop_db()


    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryCheckIDSessionsOK(self):
        """
        Check bank has right session id
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['current'] = 100
        manager.bank.bank['sessions'].append({'id': 100})
        history = manager.history()
        self.assertEqual(history[0]['id'], 100)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryCheckStatusDeprecatedOK(self):
        """
        Check bank has status deprecrated
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['current'] = 100 + 1
        manager.bank.bank['sessions'].append({'id': 100})
        history = manager.history()
        self.assertEqual(history[0]['status'], 'deprecated')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryStatusUnpublishedOK(self):
        """
        Check bank not published yet (first run) has status unpublished
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 100})
        del(manager.bank.bank['current'])
        history = manager.history()
        self.assertEqual(history[0]['status'], 'unpublished')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistorySessionsHistoryANDStatusDeletedOK(self):
        """
        Check bank has status deleted
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_12'))
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 101, 'data_dir': self.utils.data_dir, 'dir_version': "alu",
                                              'prod_dir': "alu_12"})
        history = manager.history()
        self.assertEqual(history[1]['status'], 'deleted')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryNoProductionRaisesError(self):
        """
        Check when no 'production' field in bank, history raises exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'] = None
        with self.assertRaises(SystemExit):
            manager.mongo_history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryNoSessionsRaisesError(self):
        """
        Check when no 'sessions' field in bank, history raises exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12})
        manager.bank.bank['sessions'] = None
        with self.assertRaises(SystemExit):
            manager.mongo_history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryCheckIDSessionsOK(self):
        """
        Check bank has right session id
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        _id = "@".join(['bank', 'alu', '12', Utils.time2datefmt(100, Manager.DATE_FMT)])
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['current'] = 100
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12})
        history = manager.mongo_history()
        self.assertEqual(history[0]['_id'], _id)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryCheckStatusDeprecatedOK(self):
        """
        Check bank has status deprecrated
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['current'] = 100 + 1
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12})
        history = manager.mongo_history()
        self.assertEqual(history[0]['status'], 'deprecated')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryStatusUnpublishedOK(self):
        """
        Check bank not published yet (first run) has status unpublished
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12})
        del(manager.bank.bank['current'])
        history = manager.mongo_history()
        self.assertEqual(history[0]['status'], 'unpublished')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistorySessionsHistoryANDStatusDeletedOK(self):
        """
        Check bank has status deleted
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_12'))
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 101, 'data_dir': self.utils.data_dir, 'dir_version': "alu",
                                              'prod_dir': "alu_12", 'remoterelease': 12, 'last_update_time': 100,
                                              'last_modified': 100, 'status': {'remove_release': True}})
        history = manager.mongo_history()
        self.assertEqual(history[1]['status'], 'deleted')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsNotOK(self):
        """
        Check method throw exception, can't create directory
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['properties']['owner'] = manager.config.get('GENERAL', 'admin')
        back_log = os.environ["LOGNAME"]
        os.environ["LOGNAME"] = manager.config.get('GENERAL', 'admin')
        with self.assertRaises(SystemExit):
            manager.save_banks_version(file='/not_found/saved_versions.txt')
        # Reset to the right user name as previously
        os.environ["LOGNAME"] = back_log
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsThrowsException(self):
        """
        Check method throw exception, can't access file
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['properties']['owner'] = manager.config.get('GENERAL', 'admin')
        back_log = os.environ["LOGNAME"]
        outputfile = os.path.join(self.utils.data_dir, 'saved_versions.txt')
        open(outputfile, 'w').close()
        os.chmod(outputfile, 0000)
        os.environ["LOGNAME"] = manager.config.get('GENERAL', 'admin')
        with self.assertRaises(SystemExit):
            manager.save_banks_version(file=outputfile)
        # Reset to the right user name as previously
        os.environ["LOGNAME"] = back_log


    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsNoFileOK(self):
        """
        Test exceptions
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now},
                                                    '$push': {'production': {'session': now, 'release': '54','size': '100Mo'}}})
        # Prints on output using simulate mode

        self.assertEqual(manager.save_banks_version(), 0)
        # Reset to the right user name as previously
        self.utils.drop_db()

    @attr('manager.1')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsFileContentOK(self):
        """
        Test exceptions
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        outputfile = os.path.join(self.utils.data_dir, 'saved_version.txt')
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now},
                                                    '$push': {'production': {'session': now, 'release': '54','size': '100Mo'}}})
        # Prints on output using simulate mode
        back_patt = Manager.SAVE_BANK_LINE_PATTERN
        Manager.SAVE_BANK_LINE_PATTERN = "%s_%s_%s_%s_%s"
        manager.save_banks_version(file=outputfile)
        line = Manager.SAVE_BANK_LINE_PATTERN % ('alu', "Release " + '54', Utils.time2datefmt(now, Manager.DATE_FMT),
                                                 '100Mo', manager.bank.config.get('server'))
        with open(outputfile, 'r') as of:
            for oline in of:
                self.assertEqual(line, oline)
        # Restore default pattern
        Manager.SAVE_BANK_LINE_PATTERN = back_patt
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsManagerVerboseOK(self):
        """
        Test exceptions
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now},
                                                    '$push': {'production': {'session': now, 'release': '54','size': '100Mo'}}})
        # Set verbose mode
        manager.set_verbose(True)
        self.assertEqual(manager.save_banks_version(), 0)
        # Unset verbose mode
        manager.set_bank(False)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankOK(self):
        """
        Check method checks are ok
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager()
        from biomaj.bank import Bank
        b = Bank('alu', no_log=True)
        self.assertTrue(manager.set_bank(bank=b))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankNOTOK(self):
        """
        Check method checks are not ok
        :return:
        """
        manager = Manager()
        self.assertFalse(manager.set_bank())

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankWrongInstanceOK(self):
        """
        Check method checks are not ok
        :return:
        """
        manager = Manager()
        self.assertFalse(manager.set_bank(bank=Manager()))

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankFromNameFalse(self):
        """
        Check method checks are not ok
        :return:
        """
        manager = Manager()
        self.assertFalse(manager.set_bank_from_name(""))

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankFromNameOK(self):
        """
        Check method checks are not ok
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager()
        self.assertTrue(manager.set_bank_from_name("alu"))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setverbose')
    def test_ManagerSetVerboseReturnsTrue(self):
        """
        Check set verbose set the correct boolean
        :return:
        """
        manager = Manager()
        self.assertTrue(manager.set_verbose("OK"))

    @attr('manager')
    @attr('manager.setverbose')
    def test_ManagerSetVerboseReturnsFalse(self):
        """
        Check set verbose set the correct boolean
        :return:
        """
        manager = Manager()
        self.assertFalse(manager.set_verbose(""))

    @attr('manager')
    @attr('manager.setsimulate')
    def test_ManagerSetSimulateReturnsTrue(self):
        """
        Check set simulate set the correct boolean
        :return:
        """
        manager = Manager()
        self.assertTrue(manager.set_simulate("OK"))

    @attr('manager')
    @attr('manager.setsimulate')
    def test_ManagerSetSimulateReturnsFalse(self):
        """
        Check set simulate set the correct boolean
        :return:
        """
        manager = Manager()
        self.assertFalse(manager.set_simulate(""))

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankIsLocked(self):
        """
        Check manager.can_switch returns False because bank is locked
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        lock_file = os.path.join(manager.bank.config.get('lock.dir'), manager.bank.name + '.lock')
        with open(lock_file, 'a'):
            self.assertFalse(manager.can_switch())
        os.remove(lock_file)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdate_CannotSwitch(self):
        """
        Check method returns empty dict because bank cannot switch
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        # setting current to None means no current bank published.
        manager.bank.bank['current'] = None
        returned = manager.show_need_update()
        self.assertDictEqual(returned, {})

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdate_CanSwitchOneBank(self):
        """
        Check method returns dict because bank can switch
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        # We created these 2 managers to set 2 banks in db
        alu = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        # setting current to None means no current bank published.
        alu.bank.bank['current'] = now
        alu.bank.bank['last_update_session'] = now + 1
        returned = alu.show_need_update()
        self.assertDictEqual(returned, {'alu': alu.bank})

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdate_CanSwitchTwoBank(self):
        """
        Check method returns dict because bank can switch
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        self.utils.copy_file(file='minium.properties', todir=self.utils.conf_dir)
        now = time.time()
        # We created these 2 managers to set 2 banks in db
        alu = Manager(bank='alu')
        minium = Manager(bank='minium')
        # We update the bank in db to mimic bank ready to switch
        alu.bank.banks.update({'name': 'alu'}, {'$set': {'current': now}})
        alu.bank.banks.update({'name': 'alu'}, {'$set': {'last_update_session': now + 1}})
        minium.bank.banks.update({'name': 'minium'}, {'$set': {'current': now}})
        minium.bank.banks.update({'name': 'minium'}, {'$set': {'last_update_session': now + 1}})
        # We reload the banks
        manager = Manager()
        returned = manager.show_need_update()
        self.assertEqual(len(returned.items()), 2)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankNotPublished(self):
        """
        Check manager.can_switch returns False because bank not published yet
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['current'] = None
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankUpdateNotReady(self):
        """
        Check manager.can_switch returns False because last session failed
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankLastSessionFailed(self):
        """
        Check manager.can_switch returns False because last session failed
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        manager.bank.bank['current'] = now
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['sessions'].append({'id': now, 'status': {'over': False}})
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_SwitchTrue(self):
        """
        Check manager.can_switch returns True
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        manager.bank.bank['current'] = now
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['last_update_session'] = now + 1
        self.assertTrue(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyRaisesErrorOK(self):
        """
        Check the method raises exception
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.update_ready()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithCurrentTrue(self):
        """
        Check the method returns True
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now + 1
        self.assertTrue(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithCurrentFalse(self):
        """
        Check the method returns False
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithProductionTrue(self):
        """
        Check the method returns False
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del(manager.bank.bank['current'])
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['production'].append({'session': now})
        manager.bank.bank['sessions'].append({'id': now, 'status': {'over': True}})
        self.assertTrue(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandCheckConfigStop(self):
        """
        Check some config values are ok
        :return:
        """
        manager = Manager()
        manager.config.remove_option('MANAGER', 'jobs.stop.exe')
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertFalse(manager.stop_running_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandCheckConfigRestart(self):
        """
        Check some config values are ok
        :return:
        """
        manager = Manager()
        manager.config.remove_option('MANAGER', 'jobs.restart.exe')
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertFalse(manager.restart_stopped_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandRestartJobsScriptOK(self):
        """
        Check restart jobs runs OK
        :return:
        """
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertTrue(manager.restart_stopped_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandRestartJobsScriptDoesNotExists(self):
        """
        Check restart jobs runs OK
        :return:
        """
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        manager.config.set('MANAGER', 'jobs.restart.exe', '/nobin/cmd')
        with self.assertRaises(SystemExit):
            manager.restart_stopped_jobs()
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandStopJobsScriptOK(self):
        """
        Check restart jobs runs OK
        :return:
        """
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertTrue(manager.stop_running_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandStopScriptDoesNotExists(self):
        """
        Check restart jobs runs OK
        :return:
        """
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        manager.config.set('MANAGER', 'jobs.stop.exe', '/nobin/cmd')
        with self.assertRaises(SystemExit):
            manager.stop_running_jobs()
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerLaunchCommandOK(self):
        """
        Check a command started is OK
        :return:
        """
        manager = Manager()
        self.assertTrue(manager._run_command(exe='ls', args=['/tmp'], quiet=True))

    @attr('manager')
    @attr('manager.command')
    def test_ManagerLaunchCommandError(self):
        """
        Check a wrong return launched command
        :return:
        """
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='ls', args=['/notfound'], quiet=True)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorNoExe(self):
        """
        Check method throws error when no 'exe'
        :return:
        """
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(args=['foobar'], quiet=True)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorNoRights(self):
        """
        Check method throws error we can run command, no rights
        :return:
        """
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='chmod', args=['-x', '/bin/ls'], quiet=True)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorCantRunCommand(self):
        """
        Check method throws error command does not exist
        :return:
        """
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='/bin/nobin', args=['/tmp'], quiet=True)


class TestBiomajManagerPlugins(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()
        self.utils.copy_plugins()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        self.utils.clean()

    @attr('plugins')
    def test_PluginLoadErrorNoManager(self):
        """
        Chek we've got an excedption thrown when Plugin Object is build without manager as args
        :return:
        """
        from biomajmanager.plugins import Plugins
        with self.assertRaises(SystemExit):
            Plugins()

    @attr('plugins')
    def test_PluginsLoadedOK_AsStandAlone(self):
        """
        Check the Plugins Object can be build as a standlone object
        :return:
        """
        from biomajmanager.plugins import Plugins
        manager = Manager()
        plugins = Plugins(manager=manager)
        self.assertIsInstance(plugins, Plugins)

    @attr('plugins')
    def test_PluginsLoaded(self):
        """
        Check a list of plugins are well loaded
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertEqual(manager.plugins.myplugin.get_name(), 'myplugin')
        self.assertEqual(manager.plugins.anotherplugin.get_name(), 'anotherplugin')

    @attr('plugins')
    def test_PluginsListPlugins(self):
        """
        Check method returns right list of configured plugins from file
        :return:
        """
        manager = Manager()
        returned = manager.list_plugins()
        expected = ['myplugin', 'anotherplugin']
        self.assertListEqual(expected, returned)

    @attr('plugins')
    def test_PluginsLoadingNoSection(self):
        """
        Check the availability of section 'PLUGINS' is correctly checked
        :return:
        """
        manager = Manager()
        manager.config.remove_section('PLUGINS')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    def test_PluginsLoadingNoPLuginsDir(self):
        """
        Check the plugins.dir value is correctly checked
        :return:
        """
        manager = Manager()
        manager.config.remove_option('MANAGER', 'plugins.dir')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    def test_PluginsLoadingNoPLuginsList(self):
        """
        Check the plugins.dir value is correctly checked
        :return:
        """
        manager = Manager()
        manager.config.remove_option('PLUGINS', 'plugins.list')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    def test_PluginsLoadingNoPLuginsDirExists(self):
        """
        Check the plugins.dir path  is correctly checked
        :return:
        """
        manager = Manager()
        manager.config.set('MANAGER', 'plugins.dir', '/notfound')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    def test_PluginsLoadingNoConfig(self):
        """
        Check the plugins.dir value is correctly checked
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        manager.config = None
        from configparser import RawConfigParser
        self.assertIsInstance(manager.plugins.myplugin.get_config(), RawConfigParser)

    @attr('plugins')
    def test_PluginsLoadingNoManager(self):
        """
        Check the plugins.dir value is correctly checked
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        manager.manager = None
        self.assertIsInstance(manager.plugins.myplugin.get_manager(), Manager)


    @attr('plugins')
    def test_PluginsCheckConfigValues(self):
        """
        Check the plugins config values
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertEqual(manager.plugins.myplugin.get_cfg_name(), 'myplugin')
        self.assertEqual(manager.plugins.myplugin.get_cfg_value(), '1')
        self.assertEqual(manager.plugins.anotherplugin.get_cfg_name(), 'anotherplugin')
        self.assertEqual(manager.plugins.anotherplugin.get_cfg_value(), '2')

    @attr('plugins')
    def test_PluginsCheckMethodValue(self):
        """
        Check the value returned by method is OK
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertEqual(manager.plugins.myplugin.get_value(), 1)
        self.assertEqual(manager.plugins.myplugin.get_string(), 'test')
        self.assertEqual(manager.plugins.anotherplugin.get_value(), 1)
        self.assertEqual(manager.plugins.anotherplugin.get_string(), 'test')

    @attr('plugins')
    def test_PluginsCheckTrue(self):
        """
        Check boolean returned by method
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertTrue(manager.plugins.myplugin.get_true())
        self.assertTrue(manager.plugins.anotherplugin.get_true())

    @attr('plugins')
    def test_PluginsCheckFalse(self):
        """
        Check boolean returned by method
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertFalse(manager.plugins.myplugin.get_false())
        self.assertFalse(manager.plugins.anotherplugin.get_false())

    @attr('plugins')
    def test_PluginsCheckNone(self):
        """
        Check None returned by method
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertIsNone(manager.plugins.myplugin.get_none())
        self.assertIsNone(manager.plugins.anotherplugin.get_none())

    @attr('plugins')
    def test_PluginsCheckException(self):
        """
        Check exception returned by method
        :return:
        """
        manager = Manager()
        manager.load_plugins()
        self.assertRaises(Exception, manager.plugins.myplugin.get_exception())
        self.assertRaises(Exception, manager.plugins.anotherplugin.get_exception())
