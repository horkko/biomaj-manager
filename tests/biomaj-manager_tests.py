from __future__ import print_function
from nose.tools import *
from nose.plugins.attrib import attr

import shutil
import os
import sys
import tempfile
import time
import filecmp
import copy
import stat
import unittest
from pymongo import MongoClient

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
         self.mongo_client.disconnect()

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
                if line.startswith('template_dir'):
                    mout.write("template_dir=%s\n" % self.template_dir)
                elif line.startswith('news_dir'):
                    mout.write("news_dir=%s" % self.news_dir)
                elif line.startswith('production_dir'):
                    mout.write("production_dir=%s" % self.prod_dir)
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

class TestBiomajManagerNews(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()

    def tearDown(self):
        self.utils.clean()

    def test_NewsDirNotADirectory(self):
        """
        Check the dir given is not a directory
        :return:
        """
        dir = "/foorbar"
        #self.assertEqual("[ERROR] News dir %s is not a directory" % dir, News(news_dir=dir))
        with self.assertRaises(SystemExit):
            sys.stderr = open(os.devnull, 'w')
            News(news_dir=dir)

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


class TestBioMajManagerManager(unittest.TestCase):

    def setUp(self):
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        self.utils.clean()

    def test_ConfigNoManagerSection(self):
        """
        Check we don't have a 'MANAGER' section in our config
        :return:
        """
        no_sec = 'manager-nomanager-section.properties'
        self.utils.copy_file(file=no_sec, todir=self.utils.conf_dir)
        cfg = Manager.load_config(cfg=os.path.join(self.utils.conf_dir, no_sec))
        self.assertFalse(cfg.has_section('MANAGER'))

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

    def test_ManagerBankPublishedTrue(self):
        """
        Check a bank is published or not (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        # at begining, biomaj create an empty bank entry into Mongodb
        manager = Manager(bank='alu')
        # If we do update we need to change 'bank_is_published' call find and iterate over the cursor to do the same test
        #manager.bank.banks.update({'name': 'alu'}, {'$set': { 'current': True }})
        manager.bank.bank['current'] = True
        self.assertTrue(manager.bank_is_published())
        #MongoConnector.client.drop_database(self.utils.db_test)
        self.utils.drop_db()

    def test_ManagerBankPublishedFalse(self):
        """
        Check a bank is published or not (False)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        # at begining, biomaj create an empty bank entry into Mongodb
        manager = Manager(bank='alu')
        # If we do update we need to change 'bank_is_published' call find and iterate over the cursor to do the same test
        #manager.bank.banks.update({'name': 'alu'}, {'$set': { 'current': None }})
        manager.bank.bank['current'] = None
        self.assertFalse(manager.bank_is_published())
        self.utils.drop_db()

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

    @attr('bioweb')
    def test_ManagerBankHasFormatsTrue(self):
        """
        Check if the bank has a specific format (True)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertTrue(manager.has_formats(fmt='blast'))
        self.utils.drop_db()

    @attr('bioweb')
    def test_ManagerBankHasFormatsFalse(self):
        """
        Check if the bank has a specific format (False)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_formats(fmt='unknown'))
        self.utils.drop_db()

    def test_ManagerGetSessionFromIDNotNone(self):
        """
        Check we retrieve the right session id (Not None)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'status': { 'over': True}},
                             {'id': 2, 'status': { 'over': True}},]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertIsNotNone(manager.get_session_from_id(1))
        self.utils.drop_db()

    def test_ManagerGetSessionFromIDNone(self):
        """
        Check we retrieve the right session id (None)
        :return:
        """
        self.utils.copy_file(file='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'status': { 'over': True}},
                             {'id': 2, 'status': { 'over': True}},]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertIsNone(manager.get_session_from_id(3))
        self.utils.drop_db()

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
