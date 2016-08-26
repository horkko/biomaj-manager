"""Small testing script to test biomajmanager functionality"""
from __future__ import print_function
import shutil
import os
import tempfile
import time
import unittest
from nose.plugins.attrib import attr
from pymongo import MongoClient
from datetime import datetime
from biomajmanager.links import Links
from biomajmanager.manager import Manager
from biomajmanager.news import News, RSS
from biomajmanager.plugins import Plugins
from biomajmanager.writer import Writer
from biomajmanager.utils import Utils

__author__ = 'tuco'


class UtilsForTests(object):
    """Copy properties files into a temporary directory and update properties to use a temp directory"""

    def __init__(self):
        """Setup the temp dirs and files."""
        self.global_properties = None
        self.manager_properties = None
        self.manager = None
        self.mongo_client = None
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
        self.prod_dir = os.path.join(self.test_dir, 'production')
        if not os.path.exists(self.prod_dir):
            os.makedirs(self.prod_dir)
        self.plugins_dir = os.path.join(self.test_dir, 'plugins')
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
        self.tmp_dir = os.path.join(self.test_dir, 'tmp')
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        if self.global_properties is None:
            self.__copy_test_global_properties()

        if self.manager_properties is None:
            self.__copy_test_manager_properties()

        # Set a mongo client. Can be set from global.properties
        if not self.mongo_client:
            self.mongo_client = MongoClient('mongodb://localhost:27017')

    def copy_file(self, ofile=None, todir=None):
        """
        Copy a file from the test dir to temp test zone

        :param ofile: File to copy
        :param todir: Destinatin directory
        :return:
        """
        curdir = self.__get_curdir()
        fromdir = os.path.join(curdir, ofile)
        todir = os.path.join(todir, ofile)
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
        for ofile in os.listdir(dsrc):
            shutil.copyfile(os.path.join(dsrc, ofile),
                            os.path.join(self.plugins_dir, ofile))

    def copy_templates(self):
        """
        Copy templates from test directory to 'templates' testing directory

        :return:
        """
        dsrc = 'tests/templates'
        for ffile in os.listdir(dsrc):
            shutil.copyfile(os.path.join(dsrc, ffile),
                            os.path.join(self.template_dir, ffile))

    def clean(self):
        """Deletes temp directory"""
        shutil.rmtree(self.test_dir)
        Manager.set_verbose(False)
        Manager.set_simulate(False)

    def drop_db(self):
        """Drop the mongo database after using it and close the connection"""
        self.mongo_client.drop_database(self.db_test)
        self.mongo_client.close()

    def __get_curdir(self):
        """Get the current directory"""
        return os.path.dirname(os.path.realpath(__file__))

    def __copy_test_manager_properties(self):
        """Copy manager.properties file to testing directory"""
        self.manager_properties = os.path.join(self.conf_dir, 'manager.properties')
        curdir = self.__get_curdir()
        manager_template = os.path.join(curdir, 'manager.properties')
        fout = open(self.manager_properties, 'w')
        with open(manager_template, 'r') as fin:
            for line in fin:
                if line.startswith('template.dir'):
                    fout.write("template.dir=%s\n" % self.template_dir)
                elif line.startswith('news.dir'):
                    fout.write("news.dir=%s\n" % self.news_dir)
                elif line.startswith('production.dir'):
                    fout.write("production.dir=%s\n" % self.prod_dir)
                elif line.startswith('plugins.dir'):
                    fout.write("plugins.dir=%s\n" % self.plugins_dir)
                elif line.startswith('rss.file'):
                    fout.write("rss.file=%s/rss.xml\n" % self.news_dir)
                else:
                    fout.write(line)
        fout.close()

    def __copy_test_global_properties(self):
        """Copy global.properties file into testing directory"""
        # Default config file
        config_file = 'global.properties'
        curdir = self.__get_curdir()
        global_template = os.path.join(curdir, config_file)

        # Is there any alternative global config file?
        if 'BIOMAJ_MANAGER_DOCKER_CONF' in os.environ:
            global_template = os.environ.get('BIOMAJ_MANAGER_DOCKER_CONF')
            if not os.path.isfile(global_template):
                Utils.error("Configuration file not found: %s" % global_template)
            config_file = os.path.basename(global_template)

        self.global_properties = os.path.join(self.conf_dir, config_file)
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
                elif line.startswith('db.url'):
                    fout.write(line)
                    url = line.split('=')[1]
                    (host, port) = url.split('//')[1].split(':')
                    self.mongo_client = MongoClient(host=str(host), port=int(port))
                else:
                    fout.write(line)
        fout.close()


class TestBiomajManagerUtils(unittest.TestCase):
    """Class for testing manager.utils class"""

    def setUp(self):
        self.utils = UtilsForTests()

    def tearDown(self):
        self.utils.clean()

    @attr('utils')
    @attr('utils.cleansymlinks')
    def test_cleanSymLinksPathArgsWrongThrows(self):
        """Checks the methods throws when path args is None or does not exist"""
        with self.assertRaises(SystemExit):
            Utils.clean_symlinks(path="/does/not/exist")
        with self.assertRaises(SystemExit):
            Utils.clean_symlinks(path=None)

    @attr('utils')
    @attr('utils.cleansymlinks')
    def test_cleanSymlinksNoDelete(self):
        """Checks the method get the correct list of symlinks and report them"""
        open(os.path.join(self.utils.data_dir, 'news1.txt'), 'a').close()
        os.symlink(os.path.join(self.utils.data_dir, 'news1.txt'), os.path.join(self.utils.tmp_dir, 'news1.txt'))
        os.symlink('/tmp/does_not_exist', os.path.join(self.utils.tmp_dir, 'not_found'))
        self.assertTrue(Utils.clean_symlinks(path=self.utils.tmp_dir, delete=False))

    @attr('utils')
    @attr('utils.cleansymlinks')
    def test_cleanSymlinksWithDelete(self):
        """Checks the method get the correct list of symlinks and report them"""
        open(os.path.join(self.utils.data_dir, 'news1.txt'), 'a').close()
        os.symlink(os.path.join(self.utils.data_dir, 'news1.txt'), os.path.join(self.utils.tmp_dir, 'news1.txt'))
        os.symlink('/tmp/does_not_exist', os.path.join(self.utils.tmp_dir, 'not_found'))
        self.assertTrue(Utils.clean_symlinks(path=self.utils.tmp_dir, delete=True))

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_UtilsDeepestDirErrorNoPath(self):
        """Check methods checks are OK"""
        with self.assertRaises(SystemExit):
            Utils.get_deepest_dirs()

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_DeepestDirErrorPathNotExists(self):
        """Check methods checks are OK"""
        with self.assertRaises(SystemExit):
            Utils.get_deepest_dirs(path='/not_found')

    @attr('utils')
    @attr('utils.deepestdir')
    def test_DeepestDir(self):
        """Check we get the right deepest dir from a complete path"""
        tdir = os.path.join(self.utils.tmp_dir, 'a', 'b', 'c')
        if not os.path.exists(tdir):
            os.makedirs(tdir)
        deepest = Utils.get_deepest_dir(tdir)
        self.assertEqual(deepest, 'c')
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdir')
    def test_DeepestDirFull(self):
        """Check we get the right full deepest dir"""
        tdir = os.path.join(self.utils.tmp_dir, 'a', 'b', 'c', 'd')
        if not os.path.exists(tdir):
            os.makedirs(tdir)
        deepest = Utils.get_deepest_dir(tdir, full=True)
        self.assertEqual(deepest, tdir)
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdir')
    def test_DeepestDir(self):
        """Check we get the right list of deepest dir"""
        dir0 = os.path.join(self.utils.tmp_dir, 'a', 'b')
        dir1 = os.path.join(dir0, 'c')
        dir2 = os.path.join(dir0, 'd')
        for od in [dir1, dir2]:
            if not os.path.exists(od):
                os.makedirs(od)
        deepest = Utils.get_deepest_dir(dir0)
        self.assertEqual(len(deepest), 1)
        self.assertEqual(deepest[0], 'c')
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_DeepestDirs(self):
        """Check we get the right list of deepest dir"""
        dir0 = os.path.join(self.utils.tmp_dir, 'a', 'b')
        dir1 = os.path.join(dir0, 'c')
        dir2 = os.path.join(dir0, 'd')
        for od in [dir1, dir2]:
            if not os.path.exists(od):
                os.makedirs(od)
        deepest = Utils.get_deepest_dirs(dir0)
        c1 = deepest[0]
        d1 = deepest[1]
        self.assertEqual(c1, 'c')
        self.assertEqual(d1, 'd')
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.getbrokenlinks')
    def test_getbrokenlinksNoPathThrows(self):
        """Check it throw when no path given as arg"""
        utils = Utils()
        with self.assertRaises(SystemExit):
            utils.get_broken_links()

    @attr('utils')
    @attr('utils.getbrokenlinks')
    def test_getbrokenlinksWrongPathThrows(self):
        """Check it throw when path does not exist"""
        utils = Utils()
        with self.assertRaises(SystemExit):
            utils.get_broken_links(path="/does/not/exist")

    @attr('utils')
    @attr('utils.getbrokenlinks')
    def test_getbrokenlinksNoBrokenLinks(self):
        """Check it returns 0 broken link"""
        utils = Utils()
        self.assertEqual(utils.get_broken_links(path=self.utils.tmp_dir), 0)

    @attr('utils')
    @attr('utils.getbrokenlinks')
    def test_getbrokenlinksBrokenLinksOK(self):
        """Check it returns 1 broken links"""
        utils = Utils()
        root = self.utils.tmp_dir
        link = os.path.join(root, 'foobar')
        if os.path.islink(link):
            os.remove(link)
        os.symlink('/not_found', link)
        Manager.verbose = True
        self.assertEqual(utils.get_broken_links(path=root), 1)
        os.remove(link)

    @attr('utils')
    @attr('utils.deepestdirs')
    def test_DeepestDirsFull(self):
        """Check we get the right list of deepest dir"""
        dir0 = os.path.join(self.utils.tmp_dir, 'a', 'b')
        dir1 = os.path.join(dir0, 'c')
        dir2 = os.path.join(dir0, 'd')
        for od in [dir1, dir2]:
            if not os.path.exists(od):
                os.makedirs(od)
        deepest = Utils.get_deepest_dirs(dir0, full=True)
        c1 = deepest[0]
        d1 = deepest[1]
        self.assertEqual(c1, dir1)
        self.assertEqual(d1, dir2)
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.getfiles')
    def test_GetFiles(self):
        """Check we get the right file list from a directory"""
        tmp_file1 = os.path.join(self.utils.tmp_dir, '1foobar.tmp')
        tmp_file2 = os.path.join(self.utils.tmp_dir, '2foobar.tmp')
        open(tmp_file1, mode='a').close()
        open(tmp_file2, mode='a').close()
        files = Utils.get_files(path=self.utils.tmp_dir)
        b_tmp_file1 = os.path.basename(tmp_file1)
        b_tmp_file2 = os.path.basename(tmp_file2)
        self.assertEqual(b_tmp_file1, files[0])
        self.assertEqual(b_tmp_file2, files[1])
        shutil.rmtree(self.utils.tmp_dir)

    @attr('utils')
    @attr('utils.getfiles')
    def test_GetFilesErrorNoPath(self):
        """Check we get an error when omitting args"""
        with self.assertRaises(SystemExit):
            Utils.get_files()

    @attr('utils')
    @attr('utils.getfiles')
    def test_GetFilesErrorPathNotExists(self):
        """Check we get an error when omitting args"""
        with self.assertRaises(SystemExit):
            Utils.get_files(path='/not_found')

    @attr('utils')
    @attr('utils.getsubtree')
    def test_GetSubTreeWarnAndReturnsEmptyList(self):
        """Check the method prints a warning message and returns empty list"""
        self.assertListEqual(Utils.get_subtree(path=None), [])

    @attr('utils')
    @attr('utils.getsubtree')
    def test_GetSubTreeRetrunsRgihtSubTree(self):
        """Checks the method returns the right subtree list"""
        os.makedirs(os.path.join(self.utils.tmp_dir, 'sub', 'a1', 'a2', 'a3'))
        os.makedirs(os.path.join(self.utils.tmp_dir, 'sub', 'b1', 'b2', 'b3', 'b4'))
        os.makedirs(os.path.join(self.utils.tmp_dir, 'sub', 'c1', 'c2'))
        returned = Utils.get_subtree(path=os.path.join(self.utils.tmp_dir, 'sub'))
        expected = ["a1/a2/a3", "b1/b2/b3/b4", "c1/c2"]
        self.assertListEqual(sorted(returned), sorted(expected))

    @attr('utils')
    @attr('utils.getnow')
    def test_UtilsGetNow(self):
        """Check method returns right time"""
        now = Utils.time2datefmt(time.time())
        self.assertEqual(now, Utils.get_now())

    @attr('utils')
    @attr('utils.elapsedtime')
    def test_ElapsedTimeError(self):
        """Check this method throw an error"""
        with self.assertRaises(SystemExit):
            Utils.elapsed_time()

    @attr('utils')
    @attr('utils.elapsedtime')
    def test_ElapsedtimeNoTimerStop(self):
        """Check we go deeper in method setting time_stop to None"""
        Utils.timer_stop = None
        Utils.start_timer()
        self.assertIsInstance(Utils.elapsed_time(), float)

    @attr('utils')
    @attr('utils.print')
    def test_UtilsSayReturnsNone(self):
        """Check the method returns empty string"""
        self.assertIsNone(Utils._print(None))

    @attr('utils')
    @attr('utils.print')
    def test_UtilsSayReturnsOK(self):
        """Check the method returns correct message"""
        expected = "OK\n"
        msg = "OK"
        # Python3 support
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        out = StringIO()
        Utils._print(msg, to=out)
        returned = out.getvalue()
        self.assertEqual(expected, returned)

    @attr('utils')
    @attr('utils.time2date')
    def test_Time2dateNoArgs(self):
        """Check the method throws an error if no args given"""
        with self.assertRaises(TypeError):
            Utils.time2date()

    @attr('utils')
    @attr('utils.time2date')
    def test_Time2dateReturnedOK(self):
        """Check value returned is right object"""
        self.assertIsInstance(Utils.time2date(time.time()), datetime)

    @attr('utils')
    @attr('utils.time2datefmt')
    def test_Time2datefmtNoArgs(self):
        """Check the method throws an error if no args given"""
        with self.assertRaises(TypeError):
            Utils.time2datefmt()

    @attr('utils')
    @attr('utils.time2datefmt')
    def test_Time2datefmtReturnedOK(self):
        """Check value returned is right object"""
        self.assertIsInstance(Utils.time2datefmt(time.time()), str)

    @attr('utils')
    @attr('utils.user')
    def test_UserOK(self):
        """Check the testing user is ok"""
        user = os.getenv("USER")
        self.assertEqual(Utils.user(), user)

    @attr('utils')
    @attr('utils.user')
    def test_userNOTOK(self):
        """Check the testing user is ok"""
        user = "fakeUser"
        self.assertNotEqual(Utils.user(), user)


class TestBiomajManagerWriter(unittest.TestCase):
    """Class for testing biomajmanager.writer class"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        self.utils.copy_templates()
        # Maker out test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        """Finish"""
        self.utils.clean()

    @attr('writer')
    @attr('writer.init')
    def test_WriterInitNoArgsThrowsException(self):
        """Check init throws exception with no args"""
        with self.assertRaises(SystemExit):
            Writer()

    @attr('writer')
    @attr('writer.init')
    def test_WriterInitOKWithTemplateDirOK(self):
        """Check object init is OK"""
        writer = Writer(template_dir=self.utils.template_dir)
        self.assertIsNone(writer.output)

    @attr('writer')
    @attr('writer.init')
    def test_WriterInitOKWithTemplateDirNotOK(self):
        """Check object init with false template_dir throws exception"""
        with self.assertRaises(SystemExit):
            Writer(template_dir="/not_found")

    @attr('writer')
    @attr('writer.init')
    def test_WriterInitConfigTemplateDirOK(self):
        """Check object init with config set correct tempalte_dir"""
        manager = Manager()
        writer = Writer(config=manager.config)
        self.assertEqual(manager.config.get('MANAGER', 'template.dir'), writer.template_dir)

    @attr('writer')
    @attr('writer.init')
    def test_WriterInitOKWithConfigNoSection(self):
        """Check object with config without section throws exception"""
        manager = Manager()
        manager.config.remove_section('MANAGER')
        with self.assertRaises(SystemExit):
            Writer(config=manager.config)

    @attr('writer')
    @attr('writer.init')
    def test_WriterInitOKWithConfigNoOption(self):
        """
        Check object with config without section throws exception
        :return:
        """
        manager = Manager()
        manager.config.remove_option('MANAGER', 'template.dir')
        with self.assertRaises(SystemExit):
            Writer(config=manager.config)

    @attr('writer')
    @attr('writer.write')
    def test_WriterWriteNoFileThrowsException(self):
        """Check method throws exception if not 'file' args passed"""
        writer = Writer(template_dir=self.utils.template_dir)
        with self.assertRaises(SystemExit):
            writer.write()

    @attr('writer')
    @attr('writer.write')
    def test_WriterWriteWrongTemplateFileThrowsException(self):
        """Check the method throws exception while template file does not exists"""
        writer = Writer(template_dir=self.utils.template_dir)
        with self.assertRaises(SystemExit):
            writer.write(template="doesnotexist.txt")

    @attr('writer')
    @attr('writer.write')
    def test_WriterWriteTemplateFileOKTemplateSyntaxError(self):
        """Check the method throws exception while template file does not exists"""
        writer = Writer(template_dir=self.utils.template_dir)
        with self.assertRaises(SystemExit):
            writer.write(template="wrong_syntax.txt")

    @attr('writer')
    @attr('writer.write')
    def test_WriterWrtieTemplateFileOKOutputIsNoneOK(self):
        """Check method prints OK on STDOUT"""
        writer = Writer(template_dir=self.utils.template_dir)
        data = {'test': 'working test!'}
        self.assertTrue(writer.write(template="test.txt", data=data))

    @attr('writer')
    @attr('writer.write')
    def test_WriterWriteTemplateFileOKContentOK(self):
        """Check the output file written has right content"""
        output = os.path.join(self.utils.template_dir, "output.txt")
        data = {'test': 'working test!'}
        writer = Writer(template_dir=self.utils.template_dir, output=output)
        self.assertTrue(writer.write(template="test.txt", data=data))
        with open(output, 'r') as of:
            self.assertEqual("This is just a working test!", of.readline().strip())

    @attr('writer')
    @attr('writer.write')
    def test_WriterWriteTemplateFileOKOutputThrows(self):
        """Check the output file is wrong and method throws exception"""
        output = os.path.join(self.utils.template_dir, "unkown_directory", "output.txt")
        data = {'test': 'working test!'}
        writer = Writer(template_dir=self.utils.template_dir, output=output)
        with self.assertRaises(SystemExit):
            writer.write(template="test.txt", data=data)


class TestBiomajManagerLinks(unittest.TestCase):
    """Class for testing biomajmanager.links"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties
        # Default switch off simulate and verbose mode for each test
        Manager.simulate = False
        Manager.verbose = False
        # Links need to have a production dir ready, so we do it
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager._current_release = '54'
        manager.bank.bank['production'].append({'release': '54', 'data_dir': self.utils.data_dir,
                                                'prod_dir': 'alu_54'})
        self.utils.manager = manager
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'flat'))
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed'))
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'golden'))
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        # Create a symlink
        os.symlink(os.path.join(self.utils.data_dir, 'alu', 'alu_54'), os.path.join(self.utils.data_dir, 'alu', 'current'))
        self.utils.copy_file(ofile='news1.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        self.utils.copy_file(ofile='news2.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'golden'))
        # Default dirs and files to create
        self.utils.dirs = {'golden': [{'target': 'index/golden'}],
                           'blast2': [{'target': 'index/blast2'}],
                           'flat': [{'target': 'ftp'}],
                           'uncompressed': [{'target': 'release', 'fallback': 'flat'}]}
        self.utils.files = {'golden': [{'target': 'index/golden'}],
                            'blast2': [{'target': 'fasta', 'remove_ext': True}, {'target': 'index/blast2'}]}
        self.utils.clones = {'index': [{'source': 'golden'}, {'source': 'blast2'}]}

    def tearDown(self):
        """Clean all"""
        self.utils.clean()
        # As we created an entry in the database ('alu'), we clean the database
        self.utils.drop_db()

    @attr('links')
    @attr('links.clonestructure')
    def test_clonsestructre(self):
        """Checks method build subtree structure correctly"""
        links = Links(manager=self.utils.manager)
        links.manager.set_verbose(True)
        links._clone_structure(source='blast2', target='index')
        self.assertTrue(os.path.isfile(os.path.join(self.utils.prod_dir, 'index', 'blast2', 'news1.txt')))

    @attr('links')
    @attr('links.clonestructure')
    def test_cloneStructureWtihSimulateAndVerbose(self):
        """Check no target are created"""
        links = Links(manager=self.utils.manager)
        links.manager.set_simulate(True)
        links.manager.set_verbose(True)
        self.assertTrue(links._clone_structure(source='blast2', target='index'))

    @attr('links')
    @attr('links.clonestructure')
    def test_cloneStructureWithRemoveExt(self):
        """Check the method add some more created links due to remove_ext option"""
        links = Links(manager=self.utils.manager)
        links._clone_structure(source='blast2', target='index', remove_ext=True)
        self.assertEqual(links.created_links, 2)

    @attr('links')
    @attr('links.clonestructure')
    def test_cloneStructureWithRemoveExtVerboseON(self):
        """Check the method add some more created links due to remove_ext option"""
        links = Links(manager=self.utils.manager)
        links.manager.set_verbose(True)
        links._clone_structure(source='golden', target='index', remove_ext=True)
        self.assertEqual(links.created_links, 2)

    @attr('links')
    @attr('links.clonestructure')
    def test_cloneStructureThrowsOSError(self):
        """Check the method throws exception"""
        links = Links(manager=self.utils.manager)
        links.manager.set_verbose(True)
        os.chmod(self.utils.prod_dir, 0o000)
        with self.assertRaises(SystemExit):
            links._clone_structure(source='golden', target='index', remove_ext=True)
        os.chmod(self.utils.prod_dir, 0o777)

    @attr('links')
    @attr('links.clonestructure')
    def test_cloneStructureNoFiles(self):
        """Check the method continue when no files in subtree"""
        links = Links(manager=self.utils.manager)
        links.manager.set_verbose(True)
        os.unlink(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'golden', 'news2.txt'))
        self.assertTrue(links._clone_structure(source='golden', target='index'))

    @attr('links')
    @attr('links.init')
    def test_LinksInitOK(self):
        """Check init Links instance is OK"""
        links = Links(manager=self.utils.manager)
        self.assertEqual(links.created_links, 0)

    @attr('links')
    @attr('links.init')
    def test_ConstructorThrowsNoCurrentReleaseAvailable(self):
        """Checks the constructor throws an error if the current release for the bank is not available"""
        self.utils.manager._current_release = None
        with self.assertRaises(SystemExit):
            links = Links(manager=self.utils.manager)

    @attr('links')
    @attr('links.init')
    def test_LinksInitNoManagerThrowsException(self):
        """Check init instance without manager throws exception"""
        with self.assertRaises(SystemExit):
            Links()

    @attr('links')
    @attr('links.init')
    def test_LinksInitWrongManagerInstanceThrows(self):
        """Check init thorws exception is manager args is not instance of Manager"""
        with self.assertRaises(SystemExit):
            Links(manager=self.utils)

    @attr('links')
    @attr('links.addlink')
    def test_LinkAddLinkAddOneOK(self):
        """Check method increase by 1 ok"""
        link = Links(manager=self.utils.manager)
        link.add_link()
        link.add_link()
        self.assertEqual(link.add_link(), 3)

    @attr('links')
    @attr('links.addlink')
    def test_LinkAddLinkAddTwoOK(self):
        """Check method increase correctly with arg"""
        link = Links(manager=self.utils.manager)
        link.add_link(inc=1)
        link.add_link(inc=2)
        link.add_link(inc=3)
        self.assertEqual(link.created_links, 6)

    @attr('links')
    @attr('links.checklinks')
    def test_LinksCheckLinksSimulateTrueVerboseFalseOK(self):
        """Check method returns right number of simulated created links"""
        links = Links(manager=self.utils.manager)
        Manager.set_simulate(True)
        Manager.set_verbose(True)
        # Check setUp, it creates 3 dirs
        self.assertEqual(links.check_links(clone_dirs=self.utils.clones,
                                           dirs=self.utils.dirs,
                                           files=self.utils.files), 10)

    @attr('links')
    @attr('links.dolinks')
    def test_LinksDoLinksThrowsWrongUser(self):
        """Check method throws exception because user not authorized"""
        links = Links(manager=self.utils.manager)
        os.environ['USER'] = 'fakeuser'
        with self.assertRaises(SystemExit):
            links.do_links()

    @attr('links')
    @attr('links.dolinks')
    def test_LinksDoLinksArgsDirsAndFilesNone(self):
        """Check method with args set to None, creates the right number of links"""
        links = Links(manager=self.utils.manager)
        self.assertEqual(links.do_links(dirs=None,
                                        files=self.utils.files,
                                        clone_dirs=self.utils.clones), 7)

    @attr('links')
    @attr('links.dolinks')
    def test_LinksDoLinksArgsDirsMatchesSetUp(self):
        """Check method creates the right number of link passing a list of dirs matching setUp"""
        links = Links(manager=self.utils.manager)
        exp_dirs = {'flat': [{'target': 'ftp'}], 'uncompressed': [{'target': 'release'}],
                    'blast2': [{'target': 'index/blast2'}]}
        self.assertEqual(links.do_links(dirs=exp_dirs, files=None), 6)

    @attr('links')
    @attr('links.dolinks')
    def test_LinksDoLinksArgsFilesMatchesSetUp(self):
        """Check method creates the right number of link passing a list of dirs matching setUp"""
        links = Links(manager=self.utils.manager)
        # We copy 3 files into a source dir to have 3 more created links calling generate_files_link
        self.utils.copy_file(ofile='news1.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        self.utils.copy_file(ofile='news2.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        self.utils.copy_file(ofile='news3.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        exp_files = {'blast2': [{'target': 'index/blast2'}]}
        self.assertEqual(links.do_links(dirs=self.utils.dirs, files=exp_files), 8)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksNoArgsThrows(self):
        """Check method throws if not args source given"""
        link = Links(manager=self.utils.manager)
        with self.assertRaises(SystemExit):
            link._prepare_links()

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksSourceOKTargetMissingThrows(self):
        """Check method throws if source given but no other args"""
        link = Links(manager=self.utils.manager)
        with self.assertRaises(SystemExit):
            link._prepare_links(source=self.utils.data_dir)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksArgsOKConfigDataDirMissingThrows(self):
        """Check method throws if source given but no other args"""
        self.utils.manager.config.remove_option('GENERAL', 'data.dir')
        with self.assertRaises(SystemExit):
            link = Links(manager=self.utils.manager)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksArgsOKConfigProdDirMissingThrows(self):
        """Check method throws if source given but no other args"""
        self.utils.manager.config.remove_option('MANAGER', 'production.dir')
        with self.assertRaises(SystemExit):
            link = Links(manager=self.utils.manager)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksRequiresSetDirMissingReturnFalse(self):
        """Check the method returns False if require set and required dir not here"""
        links = Links(manager=self.utils.manager)
        self.assertFalse(links._prepare_links(source='uncompressed', target='flat_test', requires='not_here'))

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksArgsOKSourceNotDirReturnsFalse(self):
        """Check method returns False if data.dir does not exist"""
        link = Links(manager=self.utils.manager)
        link.manager.config.set('GENERAL', 'data.dir', '/dir/does_not/')
        link.manager.set_verbose(True)
        self.assertFalse(link._prepare_links(source='/exist', target="link_test"))

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksArgsOKPermissionDenied(self):
        """Check method throws when permissions denied to create dir"""
        link = Links(manager=self.utils.manager)
        link.manager.set_verbose(True)
        os.chmod(self.utils.prod_dir, 0o000)
        with self.assertRaises(SystemExit):
            link._prepare_links(source='uncompressed', target="link_test")
        os.chmod(self.utils.prod_dir, 0o777)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithFallbackOK(self):
        """Check method passes OK if fallback given"""
        link = Links(manager=self.utils.manager)
        # Remove uncompressed directory, and fallback to flat
        os.removedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed'))
        link.manager.set_verbose(True)
        self.assertTrue(link._prepare_links(source='uncompressed', target='flat_test', fallback='flat'))

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithFallbackFalse(self):
        """Check method returns False if fallback given but does not exist either"""
        link = Links(manager=self.utils.manager)
        # Remove uncompressed directory, and fallback to flat
        os.removedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed'))
        os.removedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'flat'))
        link.manager.set_verbose(True)
        self.assertFalse(link._prepare_links(source='uncompressed', target='flat_test', fallback='flat'))

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithFallbackUseDeepestOK(self):
        """Check method passes OK if fallback given"""
        link = Links(manager=self.utils.manager)
        # Remove uncompressed directory, and fallback to flat
        self.assertTrue(link._prepare_links(source='uncompressed', target='flat_test', get_deepest=True))

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithSimulateModeOK(self):
        """Check method prints in simulate mode"""
        link = Links(manager=self.utils.manager)
        link.manager.set_simulate(True)
        link.manager.set_verbose(True)
        # Remove uncompressed directory, and fallback to flat
        self.assertTrue(link._prepare_links(source='uncompressed', target='flat_test'))

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksMakeTargetDirThrows(self):
        """Check method throws when making target dir"""
        link = Links(manager=self.utils.manager)
        link.manager.set_simulate(False)
        link.manager.set_verbose(False)
        # Remove uncompressed directory, and fallback to flat
        self.assertFalse
#        with self.assertRaises(SystemExit):
#            link._prepare_links(source='uncompressed', target='../../../../flat_test')

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksNoArgsReturns0(self):
        """Check the method returns 0 when no 'links' args given"""
        link = Links(manager=self.utils.manager)
        self.assertEqual(link._make_links(), 0)

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksPathAlreadyExistsReturns0(self):
        """Check the method returns 0 because source and target already exist"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed')
        target = os.path.join(self.utils.prod_dir, 'uncmp_link')
        os.symlink(os.path.relpath(source, start=target), target)
        self.assertEqual(0, link._make_links(links=[(source, target)]))
        os.remove(target)

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksPathNotExistsSimulateOnVerboseOnReturns0(self):
        """Check the method returns 0 because simulate and verbose mode on"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed')
        target = os.path.join(self.utils.prod_dir, 'uncmp_link')
        link.manager.set_simulate(True)
        link.manager.set_verbose(True)
        link._prepare_links(source=source, target=target)
        self.assertEqual(0, link._make_links(links=[(source, target)]))

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksPathNotExistsSimulateOnVerboseOffReturns1(self):
        """Check the method returns 1 because simulate on and verbose off, nothing created but link added as created"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed')
        target = os.path.join(self.utils.prod_dir, 'uncmp_link')
        link.manager.set_simulate(True)
        link.manager.set_verbose(False)
        link._prepare_links(source=source, target=target)
        self.assertEqual(1, link._make_links(links=[(source, target)]))

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksPathNotExistsHardTrueThrowsError(self):
        """Check the method throws an exception (OSError=>SystemExit) with (hard=True)"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed')
        target = os.path.join(self.utils.prod_dir, 'uncmp_link')
        link._prepare_links(source=source, target=target)
        # We delete the source directory to raise an OSError
        os.removedirs(target)
        with self.assertRaises(SystemExit):
            link._make_links(links=[(source, target)], hard=True)

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksPathNotExistsHardFalseThrowsError(self):
        """Check the method throws an exception (OSError=>SystemExit) with (hard=False)"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'uncompressed')
        target = os.path.join(self.utils.prod_dir, 'uncmp_link')
        link._prepare_links(source=source, target=target)
        # We delete the source directory to raise an OSError
        os.removedirs(target)
        with self.assertRaises(SystemExit):
            link._make_links(links=[(source, target)])

    @attr('links')
    @attr('links.generatefileslink')
    def test_LinksGenerateFilesLink_PrepareLinksReturns0(self):
        """Check _generate_files_link returns 0 because prepare_links returns > 0"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'not_found')
        target = os.path.join(self.utils.conf_dir, 'not_link')
        self.assertEqual(0, link._generate_files_link(source=source, target=target))

    @attr('links')
    @attr('links.generatefileslink')
    def test_LinksGenerateFilesLinkNotNoExtCreatedLinksOKVerboseOn(self):
        """Check method returns correct number of created links (no_ext=False)"""
        link = Links(manager=self.utils.manager)
        # Set our manager verbose mode to on
        link.manager.set_verbose(True)
        source_dir = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'flat')
        target_dir = os.path.join(self.utils.prod_dir, 'flat_symlink')
        files = ['file1.txt', 'file2.txt']
        # Create files to link
        for ifile in files:
            open(os.path.join(source_dir, ifile), 'w').close()
        # We check we've created 2 link, for file1 and file2
        self.assertEqual(2, link._generate_files_link(source='flat', target='flat_symlink'))
        # We can also check link.source and link.target are equal to our source_dir and target_dir
        self.assertEqual(os.path.join(self.utils.data_dir, 'alu', 'current', 'flat'), link.source)
        self.assertEqual(target_dir, link.target)

    @attr('links')
    @attr('links.generatefileslink')
    def test_LinksGenerateFilesLinkNotNoExtCreatedLinksOKVerboseOnSmulateOn(self):
        """Check method returns correct number of created links (no_ext=False)"""
        link = Links(manager=self.utils.manager)
        # Set our manager verbose mode to on
        link.manager.set_verbose(True)
        link.manager.set_simulate(True)
        source_dir = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'flat')
        target_dir = os.path.join(self.utils.prod_dir, 'flat_symlink')
        files = ['file1.txt', 'file2.txt']
        # Create list of file to link
        for ifile in files:
            open(os.path.join(source_dir, ifile), 'w').close()
        # We check we've created 2 link, for file1 and file2
        self.assertEqual(0, link._generate_files_link(source='flat', target='flat_symlink'))
        # We can also check link.source and link.target are equal to our source_dir and target_dir
        self.assertEqual(os.path.join(self.utils.data_dir, 'alu', 'current', 'flat'), link.source)
        self.assertEqual(target_dir, link.target)

    @attr('links')
    @attr('links.generatefileslink')
    def test_LinksGenerateFilesLinkNotNoExtCreatedLinksOKVerboseOnRemoveExtTrue(self):
        """Check method returns correct number of created links (remove_ext=True)"""
        link = Links(manager=self.utils.manager)
        # Set our manager verbose mode to on
        link.manager.set_verbose(True)
        source_dir = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'flat')
        target_dir = os.path.join(self.utils.prod_dir, 'flat_symlink')
        files = ['file1.txt', 'file2.txt']
        # Create list of file to link
        for i_file in files:
            open(os.path.join(source_dir, i_file), 'w').close()
        # We check we've created 4 link, for file1 and file2 twice (with and without extension)
        self.assertEqual(4, link._generate_files_link(source='flat', target='flat_symlink', remove_ext=True))
        # We check the created links are OK without the extention (.txt)
        self.assertTrue(os.path.islink(os.path.join(target_dir, 'file1')))
        self.assertTrue(os.path.islink(os.path.join(target_dir, 'file2')))

    @attr('links')
    @attr('links.generatedirlink')
    def test_LinksGenerateDirLink_PrepareLinksReturns0(self):
        """Check _generate_files_link returns 0 because prepare_links returns > 0"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'not_found')
        target = os.path.join(self.utils.conf_dir, 'not_link')
        self.assertEqual(0, link._generate_dir_link(source=source, target=target))

    @attr('links')
    @attr('links.generatedirlink')
    def test_LinksGenerateDirLink_PrepareLinksReturns0SimulateOnVerobseOn(self):
        """Check _generate_files_link returns 0 because prepare_links returns > 0"""
        link = Links(manager=self.utils.manager)
        # Set our manager verbose mode to on
        link.manager.set_verbose(True)
        link.manager.set_simulate(True)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2')
        target = os.path.join(self.utils.conf_dir, 'blast2_link')
        self.assertEqual(0, link._generate_dir_link(source=source, target=target))


class TestBiomajManagerNews(unittest.TestCase):
    """Class for testing biomajmanager.news class"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        """Clean"""
        self.utils.clean()

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewWithMaxNews(self):
        """Check max_news args is OK"""
        news = News(max_news=10)
        self.assertEqual(news.max_news, 10)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewWithConfigOK(self):
        """Check init set everything from config as arg"""
        manager = Manager()
        news_dir = manager.config.get('NEWS', 'news.dir')
        news = News(config=manager.config)
        self.assertEqual(news_dir, news.news_dir)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewWithConfigNoSection(self):
        """Check init throws because config has no section 'NEWS'"""
        manager = Manager()
        manager.config.remove_section('NEWS')
        with self.assertRaises(SystemExit):
            News(config=manager.config)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewWithConfigNoOption(self):
        """Check init throws because config has no option 'news.dir"""
        manager = Manager()
        manager.config.remove_option('NEWS', 'news.dir')
        with self.assertRaises(SystemExit):
            News(config=manager.config)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewsNewsDirOK(self):
        """Check get_news set correct thing"""
        self.utils.copy_news_files()
        news = News()
        news.get_news(news_dir=self.utils.news_dir)
        self.assertEqual(news.news_dir, self.utils.news_dir)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewsDirNotADirectory(self):
        """Check the dir given is not a directory"""
        with self.assertRaises(SystemExit):
            News(news_dir="/foobar")

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewsGetNewsWrongDirectory(self):
        """Check method throws exception with wrong dir calling get_news"""
        news = News()
        with self.assertRaises(SystemExit):
            news.get_news(news_dir='/not_found')

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_NewsGetNewsNewsDirNotDefined(self):
        """Check method throws exception while 'news.dir' not defined"""
        news = News()
        with self.assertRaises(SystemExit):
            news.get_news()

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.news')
    def test_FileNewsContentEqual(self):
        """Check the content of 2 generated news files are identical"""
        self.utils.copy_news_files()
        data = []
        for i in range(1, 4):
            data.append({'label': 'type' + str(i),
                         'date': str(i) + '0/12/2015',
                         'title': 'News%s Title' % str(i),
                         'text': 'This is text #%s from news%s\n' % (str(i), str(i)),
                         'item': i - 1})
        news = News(news_dir=self.utils.news_dir)
        news_data = news.get_news()
        # Compare data

        if 'news' in news_data:
            for new in news_data['news']:
                dat = data.pop()
                for k in ['label', 'date', 'title', 'text', 'item']:
                    self.assertEqual(dat[k], new[k])
        else:
            raise unittest.E
        shutil.rmtree(self.utils.news_dir)


class TestBiomajManagerRSS(unittest.TestCase):
    """Class for testing biomajmanager.news.RSS class"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        """Clean"""
        self.utils.clean()

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSWithMaxNews(self):
        """Check max_news args is OK"""
        rss = RSS(max_news=10)
        self.assertEqual(rss.max_news, 10)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSWithrfileArgs(self):
        """Check 'rfile' arg is parsed ok from __init__"""
        rfile = os.path.join(self.utils.news_dir, 'rss.xml')
        rss = RSS(rss_file=rfile)
        Manager.verbose = True
        self.assertEqual(rfile, rss.rss_file)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSGenerateRssWithrssfileArgs(self):
        """Check 'rss_file' arg is parsed ok from __init__"""
        rfile = os.path.join(self.utils.news_dir, 'rss.xml')
        manager = Manager()
        rss = RSS(config=manager.config)
        self.assertTrue(rss.generate_rss(rss_file=rfile))

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSGenerateRssWithrssfileArgsMissingOptionRaises(self):
        """Check method throw exception if option missing"""
        rfile = os.path.join(self.utils.news_dir, 'rss.xml')
        manager = Manager()
        manager.config.remove_option('RSS', 'feed.link')
        rss = RSS(config=manager.config)
        with self.assertRaises(SystemExit):
            rss.generate_rss(rss_file=rfile, data={'news': [{'title': "title", 'text': "Some blah", 'item': 1,
                                                            'date': "01/01/2000"}]})


    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSGenerateRssWithrDataArgs(self):
        """Check 'data' arg is parsed ok from __init__"""
        rfile = os.path.join(self.utils.news_dir, 'rss.xml')
        manager = Manager()
        rss = RSS(config=manager.config)
        self.assertTrue(rss.generate_rss(data={'news': [{'title': 't1', 'item': 1, 'text': 'Hello world',
                                                         'date': "10/12/2014"}]}))

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSWithrfileInConfig(self):
        """Check 'rfile' is taken from config"""
        rfile = os.path.join(self.utils.news_dir, 'rss.xml')
        manager = Manager()
        rss = RSS(config=manager.config)
        self.assertEqual(rfile, rss.rss_file)

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSNewsDataEmpty(self):
        """Check method returns True if news.dir is empty"""
        empty_dir = '/tmp/empty'
        os.mkdir(empty_dir)
        manager = Manager()
        rss = RSS(config=manager.config, news_dir=empty_dir)
        self.assertTrue(rss.generate_rss())
        shutil.rmtree(empty_dir)
        
    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSrfileNoneOK(self):
        """Check we print to STDOUT"""
        self.utils.copy_news_files()
        manager = Manager()
        rss = RSS(config=manager.config)
        self.assertTrue(rss.generate_rss())

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSrfileNonePrintSTDOUT(self):
        """Check we print to STDOUT has rss.file is not in config"""
        self.utils.copy_news_files()
        manager = Manager()
        # We delete rss.file from section 'RSS' to print to STDOUT
        manager.config.remove_option('RSS', 'rss.file')
        rss = RSS(config=manager.config)
        self.assertTrue(rss.generate_rss())

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSrfileArgsThrow(self):
        """Check method throws when OSError"""
        self.utils.copy_news_files()
        manager = Manager()
        # We delete rss.file from section 'RSS' to print to STDOUT
        manager.config.set('RSS', 'rss.file', '/no_ok')
        rss = RSS(config=manager.config)
        with self.assertRaises(SystemExit):
            rss.generate_rss()

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSDataArgsThrow(self):
        """Check method throws when no 'news' key in data"""
        self.utils.copy_news_files()
        manager = Manager()
        # We delete rss.file from section 'RSS' to print to STDOUT
        rss = RSS(config=manager.config)
        with self.assertRaises(SystemExit):
            rss.generate_rss(data={'no_news_key': []})

    @attr('manager')
    @attr('manager.news')
    @attr('manager.news.rss')
    def test_RSSWithDataArgsEmptyThrow(self):
        """Check method returns True when data is empty"""
        self.utils.copy_news_files()
        manager = Manager()
        # We delete rss.file from section 'RSS' to print to STDOUT
        rss = RSS(config=manager.config)
        self.assertTrue(rss.generate_rss(data={'news': []}))


class TestBioMajManagerDecorators(unittest.TestCase):
    """Class for testing biomajmanager.decorators"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        """Clean"""
        self.utils.clean()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorBankRequiredOK(self):
        """Test we've got a bank name set"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        sections = manager.get_bank_sections('blast2')
        expected = {'nuc': {'dbs': ['alunuc'], 'sections': ['alunuc1', 'alunuc2']},
                    'pro': {'dbs': ['alupro'], 'sections': ['alupro1', 'alupro2']}}
        self.assertDictContainsSubset(expected, sections)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorBankRequiredNotOK(self):
        """Test we've got a bank name set"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager.get_bank_sections('blast2')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsUserGrantedOK(self):
        """Test the user is granted"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.save_banks_version(bank_file=self.utils.test_dir + '/saved_versions.txt')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsUserGrantedNotOK(self):
        """Test the user is granted"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # Just change the env LOGNAME do misfit with db user
        cuser = os.environ.get('LOGNAME')
        os.environ['LOGNAME'] = "fakeuser"
        with self.assertRaises(SystemExit):
            manager.save_banks_version(bank_file=self.utils.test_dir + '/saved_versions.txt')
        # Reset to the right user name as previously
        os.environ['LOGNAME'] = cuser
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsUserGrantedAdminNotSet(self):
        """Test the user is granted"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # Unset admin from config file and owner from the bank just created
        manager.config.set('GENERAL', 'admin', '')
        manager.bank.bank['properties']['owner'] = ''
        with self.assertRaises(SystemExit):
            manager.save_banks_version(bank_file=self.utils.test_dir + '/saved_versions.txt')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.decorators')
    def test_DecoratorsDeprecated(self):
        """Check the call to deprecated method throws"""
        from biomajmanager.decorators import deprecated
        @deprecated
        def def_test():
            pass
        with self.assertRaises(SystemExit):
            def_test()

class TestBioMajManagerManager(unittest.TestCase):
    """Class for testing biomajmanager.manager class"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        """Clean"""
        self.utils.clean()

    @attr('manager')
    @attr('manager.init')
    def test_ManagerWrongBankThrows(self):
        """Checks manager throws when bank does not exists"""
        with self.assertRaises(SystemExit):
            Manager(bank='DoesNotExist')

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerNoConfigRaisesException(self):
        """Check an exception is raised while config loading"""
        with self.assertRaises(SystemExit):
            Manager(cfg="/no_manager_cfg", global_cfg="/no_global_cfg")

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerGlobalConfigException(self):
        """Check an exception is raised config loading"""
        with self.assertRaises(SystemExit):
            Manager(global_cfg="/no_global_cfg")

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ConfigNoManagerSection(self):
        """Check we don't have a 'MANAGER' section in our config"""
        no_sec = 'manager-nomanager-section.properties'
        self.utils.copy_file(ofile=no_sec, todir=self.utils.conf_dir)
        cfg = Manager.load_config(cfg=os.path.join(self.utils.conf_dir, no_sec))
        self.assertFalse(cfg.has_section('MANAGER'))

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerLoadConfig(self):
        """Check we can load any configuration file on demand"""
        for pfile in ['m1.properties', 'm2.properties', 'm3.properties']:
            self.utils.copy_file(ofile=pfile, todir=self.utils.test_dir)
            cfg = Manager.load_config(cfg=os.path.join(self.utils.test_dir, pfile))
            self.assertTrue(cfg.has_section('MANAGER'))
            self.assertEqual(cfg.get('MANAGER', 'file.name'), pfile)

    @attr('manager')
    @attr('manager.loadconfig')
    def test_ManagerLoadConfigNOTOK(self):
        """Check we throw an error when no 'manager.properties' found"""
        os.remove(os.path.join(self.utils.conf_dir, 'manager.properties'))
        with self.assertRaises(SystemExit):
            Manager.load_config(global_cfg=self.utils.global_properties)

    @attr('manager')
    @attr('manager.bankinfo')
    def test_ManagerBankInfo(self):
        """Check method returns right info about a bank"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
                             ["alu", "nucleic,protein", Utils.time2datefmt(now), '54']],
                    'prod': [["Session", "Remote release", "Release", "Directory", "Freeze"],
                             [Utils.time2datefmt(now), '54', '54',
                              os.path.join(manager.bank.config.get('data.dir'),
                                           manager.bank.config.get('dir.version'), "alu"),
                              'no']],
                    'pend': []}
        self.assertDictEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankpublished')
    def test_ManagerBankPublishedTrue(self):
        """Check a bank is published or not (True)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        # at begining, biomaj create an empty bank entry into Mongodb
        manager = Manager(bank='alu')
        # If we do update we need to change 'bank_is_published' call find
        # and iterate over the cursor to do the same test
        manager.bank.bank['current'] = True
        self.assertTrue(manager.bank_is_published())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankpublished')
    def test_ManagerBankPublishedFalse(self):
        """Check a bank is published or not (False)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        # at begining, biomaj create an empty bank entry into Mongodb
        manager = Manager(bank='alu')
        # If we do update we need to change 'bank_is_published' call find and
        # iterate over the cursor to do the same test
        manager.bank.bank['current'] = None
        self.assertFalse(manager.bank_is_published())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.cleansessions')
    def test_cleanSessionsNoBankPublishedReturnsFalse(self):
        """Checks method returns False when no 'current' set (get_bank_data_dir)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(False)
        self.assertFalse(manager.clean_sessions())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.cleansessions')
    def test_cleanSessionsLastSessionsSetContinueSimulateTrueReturnsTrue(self):
        """Check we read continue with last_update_session and current set to session id, simulate mode on"""
        current = time.time()
        last_run = current + 1
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(True)
        manager.bank.bank['last_update_session'] = last_run
        manager.bank.bank['current'] = current
        manager.bank.bank['production'] = [{'session': current, 'release': "54", 'data_dir': self.utils.data_dir}]
        if 'pending' not in manager.bank.bank:
            manager.bank.bank['pending'] = [{'id': current - 1, 'release': "56"}]
        # Create the sessions (Session 'current' needed by "def current_release")
        sessions = [{'id': current, 'release': "54", 'dir_version': 'alu'},
                    {'id': last_run, 'release': "55", 'dir_version': 'alu'},
                    {'id': current - 1, 'release': "56", 'dir_version': 'alu'}]
        manager.bank.bank['sessions'] = sessions
        self.assertTrue(manager.clean_sessions())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.cleansessions')
    def test_cleanSessionsDeletedSessionOnDiskReturnsTrue(self):
        """Check we have still some sessions on disk but marked as deleted"""
        # Needed for manager.get_bank_data_dir
        current = time.time()
        release = 54
        minus = 3
        deleted = current - minus
        deleted_rel = release - minus
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(False)
        manager.bank.bank['current'] = current
        manager.bank.bank['production'].append({'session': current, 'release': str(release),
                                                'data_dir': self.utils.data_dir,
                                                'prod_dir': "_".join(['alu', str(release)])})
        # Create the sessions (Session 'current' needed by "def current_release")
        sessions = [{'id': current, 'release': release, 'dir_version': 'alu'},
                    {'id': current - 1, 'release': deleted_rel, 'dir_version': 'alu', 'deleted': deleted}]
        manager.bank.bank['sessions'] = sessions
        # Create the 'on disk' dir
        on_disk = manager.get_bank_data_dir()
        os.makedirs(os.path.join(on_disk, 'alu' + "_" + str(deleted_rel)))
        self.assertTrue(manager.clean_sessions())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.cleansessions')
    def test_cleanSessionsNoDeletedSessionFoundInProductionReturnsTrue(self):
        """Check we no sessions marked as deleted not on disk but found in production"""
        # Needed for manager.get_bank_data_dir
        current = time.time()
        release = 54
        minus = 3
        deleted_rel = release - minus
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(False)
        manager.bank.bank['current'] = current
        manager.bank.bank['production'].append({'session': current, 'release': str(release),
                                                'data_dir': self.utils.data_dir,
                                                'prod_dir': "_".join(['alu', str(release)])})
        manager.bank.bank['production'].append({'session': current - 1, 'release': str(deleted_rel),
                                                'data_dir': self.utils.data_dir,
                                                'prod_dir': "_".join(['alu', str(deleted_rel)])})
        # Create the sessions (Session 'current' needed by "def current_release")
        sessions = [{'id': current, 'release': str(release), 'dir_version': 'alu'},
                    {'id': current - 1, 'release': str(deleted_rel), 'dir_version': 'alu'}]
        manager.bank.bank['sessions'] = sessions
        self.assertTrue(manager.clean_sessions())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.cleansessions')
    def test_cleanSessionsDeletedSessionNotOnDiskNotFoundInProductionContinueReturnsTrue(self):
        """Check we have some sessions marked as deleted not on disk and not found in production, uses continue"""
        # Needed for manager.get_bank_data_dir
        current = time.time()
        release = 54
        minus = 3
        deleted = current - minus
        deleted_rel = release - minus
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(False)
        manager.bank.bank['current'] = current
        manager.bank.bank['production'].append({'session': current, 'release': str(release),
                                                'data_dir': self.utils.data_dir,
                                                'prod_dir': "_".join(['alu', str(release)])})
        manager.bank.bank['production'].append({'session': current - 1, 'release': str(release - 3),
                                                'data_dir': self.utils.data_dir,
                                                'prod_dir': "_".join(['alu', str(release - 3)])})

        # Create the sessions (Session 'current' needed by "def current_release")
        sessions = [{'id': current, 'release': str(release), 'dir_version': 'alu'},
                    {'id': current - 1, 'release': str(deleted_rel), 'dir_version': 'alu', 'deleted': deleted},
                    {'id': current - 2, 'release': str(deleted_rel), 'dir_version': 'alu', 'deleted': deleted}]
        manager.bank.bank['sessions'] = sessions
        self.assertTrue(manager.clean_sessions())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.cleansessions')
    def test_cleanSessionsNoDeletedSessionInProductionWorkflowStatusFalseInPendingReturnsTrue(self):
        """Check we have some sessions not marked as deleted, session in production, sessions.workflow_status False
         and found in pending"""
        # Needed for manager.get_bank_data_dir
        current = time.time()
        release = 54
        minus = 3
        deleted_rel = release - minus
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(False)
        manager.bank.bank['current'] = current
        manager.bank.bank['production'].append({'session': current, 'release': str(release),
                                                'data_dir': self.utils.data_dir,
                                                'prod_dir': "_".join(['alu', str(release)])})
        manager.bank.bank['pending'] = [{'id': current - 2, 'release': str(deleted_rel)}]
        # Create the sessions (Session 'current' needed by "def current_release")
        sessions = [{'id': current, 'release': str(release), 'dir_version': 'alu'},
                    {'id': current - 2, 'release': str(deleted_rel), 'dir_version': 'alu', 'workflow_status': False}]
        manager.bank.bank['sessions'] = sessions
        self.assertTrue(manager.clean_sessions())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_CurrentSet(self):
        """Check correct release is returned"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        release = str(54)

        data = {'name': 'alu',
                'current': now,
                'sessions': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'remoterelease': release}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        manager._current_release = str(54)
        self.assertEqual(str(54), manager.current_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_CurrentANDSessions(self):
        """Check we get the right current release"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
    @attr('manager.currentlink')
    def test_ManagerGetCurrentLinkNOTOK(self):
        """Check get_current_link throws exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_current_link()
        self.assertNotEqual(cur_link, '/wrong_curent_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.currentlink')
    def test_ManagerGetCurrentLinkOK(self):
        """Check get_current_link throws exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_current_link()
        self.assertEqual(cur_link, os.path.join(self.utils.data_dir, manager.bank.name, 'current'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.futurelink')
    def test_ManagerGetFutureLinkNOTOK(self):
        """Check get_future_link throws exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_future_link()
        self.assertNotEqual(cur_link, '/wrong_future_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.futurelink')
    def test_ManagerGetFutureLinkOK(self):
        """Check get_future_link throws exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        cur_link = manager.get_future_link()
        self.assertEqual(cur_link, os.path.join(self.utils.data_dir, manager.bank.name, 'future_release'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hascurrentlink')
    def test_ManagerHasCurrentLinkFalse(self):
        """Check has_current_link returns False"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_current_link())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hascurrentlink')
    def test_ManagerHasCurrentLinkIsLinkTrue(self):
        """Check has_current_link returns True"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        link = os.path.join(self.utils.data_dir)
        os.symlink(os.path.join(link), 'test_link')
        self.assertTrue(manager.has_current_link(link='test_link'))
        os.remove('test_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hasfuturelink')
    def test_ManagerHasFutureLinkFalse(self):
        """Check has_future_link returns False"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_future_link())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.hasfuturelink')
    def test_ManagerHasFutureLinkIsLinkOK(self):
        """Check has_future_link returns future link"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        link = os.path.join(self.utils.data_dir)
        os.symlink(os.path.join(link), 'future_link')
        self.assertTrue(manager.has_future_link(link='future_link'))
        os.remove('future_link')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedNoLastUpdateSession(self):
        """Check method returns False when no 'last_update_session' field in database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedNoSessionsThrows(self):
        """Check method throws when no 'sessions' in bank"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['last_update_session'] = now
        del(manager.bank.bank['sessions'])
        self.assertTrue(manager.last_session_failed())

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedStatusOverWorkflowStatusTrue(self):
        """Check method returns False when no 'last_update_session' field in database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'workflow_status': False},
                             {'id': now, 'workflow_status': True}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertFalse(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedNoWorkflowStatusTrue(self):
        """Check method returns True when no 'workflow_status' in 'session'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0},
                             {'id': now}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertTrue(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedWorkflowStatusFalse(self):
        """Check method returns False when no 'last_update_session' field in database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'workflow_status': False},
                             {'id': now, 'workflow_status': False}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertTrue(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedFalseNoPendingFalse(self):
        """Check we have a failed session and no pending session(s)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'workflow_status': True},
                             {'id': now, 'workflow_status': True}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertFalse(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedTrueNoPendingTrue(self):
        """Check we have a failed session and no pending session(s)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'workflow_status': True},
                             {'id': now, 'workflow_status': True}],
                'last_update_session': now,
                'pending': [{'release': '12345', 'id': now}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        Utils.show_warn = False
        Manager.set_verbose(True)
        self.assertTrue(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedTrueNoPendingFalse(self):
        """Check we have a failed session and no pending session(s)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'workflow_status': True},
                             {'id': now, 'workflow_status': False}],
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
        """Check missing arg raises error"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.has_formats()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankHasFormatsTrue(self):
        """Check if the bank has a specific format (True)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertTrue(manager.has_formats(fmt='blast'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankHasFormatsFalse(self):
        """Check if the bank has a specific format (False)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.has_formats(fmt='unknown'))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankFormatsFlatFalseOK(self):
        """Check if the bank has a specific format (True)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.formats()
        expected = ['blast@2.2.26', 'fasta@3.6']
        self.assertListEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankFormatsFlatTrueOK(self):
        """Check if the bank has a specific format (True)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.formats(flat=True)
        expected = {'blast': ['2.2.26'], 'fasta': ['3.6']}
        self.assertDictEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.formats')
    def test_ManagerBankFormatsAsStringOK(self):
        """Check if the bank has a specific format returned as string (True)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.formats_as_string()
        expected = {'blast': ['2.2.26'], 'fasta': ['3.6']}
        self.assertDictEqual(returned, expected)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getcurrentuser')
    def test_ManagerGetCurrentUserTestUSEROK(self):
        """Check we can get USER from environ with LOGNAME unset"""
        backlog = ""
        user = os.getenv('USER')
        if 'LOGNAME' in os.environ:
            backlog = os.environ['LOGNAME']
            del os.environ['LOGNAME']
        manager = Manager()
        self.assertEqual(manager.get_current_user(), user)
        if 'LOGNAME' not in os.environ:
            os.environ['LOGNAME'] = backlog

    @attr('manager')
    @attr('manager.getcurrentuser')
    def test_ManagerGetCurrentUserTestUserIsNone(self):
        """Check method throws exception when env LOGNAME and USER not found"""
        manager = Manager()
        backup = os.environ.copy()
        os.environ = {}
        self.assertIsNone(manager.get_current_user())
        os.environ = backup

    @attr('manager')
    @attr('manager.getfailedprocess')
    def test_ManagerGetFailedProcessNoKeySessionsThrows(self):
        """Checks the method throws SystemExit when no 'sessions' JSON key found in bank database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        del(manager.bank.bank['sessions'])
        with self.assertRaises(SystemExit):
            manager.get_failed_processes()

    @attr('manager')
    @attr('manager.getfailedprocess')
    def test_ManagerGetFailedProcessWithoutArgsReturnsEmptyList(self):
        """Check the method returns an empty list when no args passed"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertListEqual(manager.get_failed_processes(), [])

    @attr('manager')
    @attr('manager.getfailedprocess')
    def test_ManagerGetFailedProcessWithArgSessionIDArgReturnsEmptyList(self):
        """Checks the method returns an empty list when a session id is passed as arg and not found"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['sessions'].append({'id': 1})
        self.assertListEqual(manager.get_failed_processes(session_id=2), [])

    @attr('manager')
    @attr('manager.getfailedprocess')
    def test_ManagerGetFailedProcessWithSessionIDArgCheckStatusReturnsList(self):
        """Checks the method returns an empty list when a session id is passed as arg and found,
        as sessions.status false"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['sessions'].append({'id': 1, 'workflow_status': True})
        manager.bank.bank['sessions'].append({'id': 2, 'workflow_status': False,
                                              'status': {'init': False, 'postprocess': False}, 'release': "51"})
        self.assertEqual(len(manager.get_failed_processes(session_id=2)), 1)
        self.assertEqual(len(manager.get_failed_processes(session_id=2, full=True)), 1)

    @attr('manager')
    @attr('manager.getfailedprocess')
    def test_ManagerGetFailedProcessCheckPostProcessReturnsNonEmptyList(self):
        """Check the method passes all the 'sessions' conditions in the loop, with and w/o full + session_id"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        sessions = [
                    {'id': 1, 'process': {'postprocess': {'UNCOMPRESS': {'UNZIP': {'gunzip': True}}}}},
                    {'id': 2, 'process': {'postprocess': {'UNCOMPRESS': {'UNZIP': {'gunzip': True}},
                                                          'FORMAT': {'F2FN': {'f2fn': False}}}}},
                    {'id': 3, 'process': {'postprocess': {'UNCOMPRESS': {'UNZIP': {'gunzip': True}},
                                                          'FORMAT': {'F2FN': {'f2fn': False},
                                                                     'F2FP': {'f2fp': False}}}},
                     'release': "52"}
                    ]
        manager.bank.bank['sessions'] = sessions
        self.assertEqual(len(manager.get_failed_processes(session_id=1)), 0)
        self.assertEqual(len(manager.get_failed_processes(session_id=2)), 1)
        self.assertEqual(len(manager.get_failed_processes(session_id=3, full=True)), 12)

    @attr('manager')
    @attr('manager.getproductiondir')
    def test_ManagerGetProductionDirThorwsOK(self):
        """Check the method throws when no 'production.dir' set in config"""
        manager = Manager()
        manager.config.remove_option('MANAGER', 'production.dir')
        with self.assertRaises(SystemExit):
            manager.get_production_dir()

    @attr('manager')
    @attr('manager.getproductiondir')
    def test_ManagerGetProductionDirOK(self):
        """Check the method get the right value"""
        manager = Manager()
        expected = manager.config.get('MANAGER', 'production.dir')
        returned = manager.get_production_dir()
        self.assertEqual(returned, expected)

    @attr('manager')
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNotNoneNotNone(self):
        """Check we retrieve the right session id (Not None)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'workflow_status': True},
                             {'id': 2, 'workflow_status': True}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertIsNotNone(manager.get_session_from_id(1))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNotNone(self):
        """Check we retrieve the right session id (None)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'workflow_status': True},
                             {'id': 2, 'workflow_status': True}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertIsNone(manager.get_session_from_id(3))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNone(self):
        """Check method raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'workflow_status': True},
                             {'id': 2, 'workflow_status': True}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        with self.assertRaises(SystemExit):
            manager.get_session_from_id(None)
        self.utils.drop_db()

    @attr('manager.getpendingsessions')
    def test_ManagerGetPendingSessionsOK(self):
        """Check method returns correct pending session"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        expected = [{'release': 54, 'id': now}, {'release': 55, 'id': now + 1}]
        manager.bank.bank['pending'] = expected
        pendings = manager.get_pending_sessions()
        self.assertListEqual(expected, pendings)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getpublishedrelease')
    def test_ManagerGetPublishedReleaseNotNone(self):
        """Check we get a the published release (NotNone)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check we get a the published release (None)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check method raises an exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu', 'current': now,
                'sessions': [{'id': 1}, {'id': now}]
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        with self.assertRaises(SystemExit):
            manager.get_published_release()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetDictSections(self):
        """Get sections for a bank"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.get_bank_sections(tool='blast2')
        expected = {'pro': {'dbs': ['alupro'], 'sections': ['alupro1', 'alupro2']},
                    'nuc': {'dbs': ['alunuc'], 'sections': ['alunuc1', 'alunuc2']}}
        self.assertDictContainsSubset(expected, returned)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetDictSectionsOnlySectionsOK(self):
        """Test we've got only sections not db from bank properties"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        returned = manager.get_bank_sections(tool='golden')
        expected = {'nuc': {'sections': ['alunuc'], 'dbs': []},
                    'pro': {'sections': ['alupro'], 'dbs': []}}
        self.assertDictContainsSubset(expected, returned)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.sections')
    def test_ManagerGetDictSectionsNoTool(self):
        """Get sections for a bank"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_bank_sections()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.showpendingsessions')
    def test_ManagerShowPendingSessionsOK(self):
        """Check method returns correct pending session"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        expected = [{'release': 54, 'id': now}, {'release': 55, 'id': now + 1}]
        manager.bank.bank['pending'] = expected
        pendings = manager.show_pending_sessions()
        self.assertListEqual(expected, pendings)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.synchronizedb')
    def test_ManagerSynchDBMissingConfKeyThrows(self):
        """Checks the method throws when some config keys are missing"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.config.remove_option('MANAGER', 'synchrodb.delete.dir')
        with self.assertRaises(SystemExit):
            manager.synchronize_db()
        manager.config.set('MANAGER', 'synchrodb.delete.dir', 'auto')
        manager.config.remove_option('MANAGER', 'synchrodb.set.sessions.deleted')
        with self.assertRaises(SystemExit):
            manager.synchronize_db()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.synchronizedb')
    def test_ManagerSynchDBWrongConfKeyThrows(self):
        """Checks the method throws when some config keys are wrong"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.config.set('MANAGER', 'synchrodb.delete.dir', 'unknown')
        with self.assertRaises(SystemExit):
            manager.synchronize_db()
        manager.config.set('MANAGER', 'synchrodb.delete.dir', 'auto')
        manager.config.set('MANAGER', 'synchrodb.set.sessions.deleted', 'unknown')
        with self.assertRaises(SystemExit):
            manager.synchronize_db()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.synchronizedb')
    def test_ManagerSynchDBReturnsFalseNoCurrentRelease(self):
        """Check method returns False as we do not have a 'current' release set (get_bank_data_dir())"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_simulate(True)
        self.assertFalse(manager.synchronize_db())
        # Simulate mode off, delete.dir=manual as set.sessions.deleted
        Manager.set_simulate(False)
        manager.config.set('MANAGER', 'synchrodb.delete.dir', 'manual')
        manager.config.set('MANAGER', 'synchrodb.set.sessions.deleted', 'manual')
        # Throws as 'synchrodb.set.sessions.deleted'=manual and no args passed to method
        with self.assertRaises(SystemExit):
            manager.synchronize_db()
        # Returns False as get_bank_data_dir returns False, no 'current' release set
        self.assertFalse(manager.synchronize_db(date_deleted="2016/01/01"))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.synchronizedb')
    def test_ManagerSynchDBWithCurrentReleaseAndPendingsAndMissingProductionSimulateONReturnsTrue(self):
        """Do some tests inside loop over productions. Simulate mode ON returns True"""
        # sid 1: current release, in prod, on disk
        # sid 2: in prod, on disk, wf_status False, in pending
        # sid 3: in prod, on disk, wf_status True, deleted
        # sid 4: in prod, on disk, not in session
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_verbose(True)
        # Needed for call get_bank_data_dir()
        # Set production
        production_data = [{'data_dir': self.utils.data_dir,
                            'release': "1", 'dir_version': "alu",
                            'session': 1, 'prod_dir': "alu_1"},
                           {'data_dir': self.utils.data_dir,
                            'release': "2", 'dir_version': "alu",
                            'session': 2, 'prod_dir': "alu_2"},
                           {'data_dir': self.utils.data_dir,
                            'release': "3", 'dir_version': "alu",
                            'session': 3, 'prod_dir': "alu_3"},
                           {'data_dir': self.utils.data_dir,
                            'release': "3", 'dir_version': "alu",
                            'session': 4, 'prod_dir': "alu_4"},
                           {'data_dir': self.utils.data_dir,
                            'release': "10", 'dir_version': "alu",
                            'session': 10, 'prod_dir': "alu_10"}]
        # Set sessions
        sessions_data = [{'id': 1, 'workflow_status': True, 'release': "1"},
                         {'id': 2, 'workflow_status': False, 'release': "2"},
                         {'id': 3, 'workflow_status': True, 'deleted': 2, 'release': "3"}]
        # Set pendings
        pending_data = [{'id': 3, 'release': "3"}, {'id': 2, 'release': "2"}]
        manager.bank.bank['last_update_session'] = 3
        manager.bank.bank['current'] = 1
        manager.bank.bank['production'] = production_data
        manager.bank.bank['sessions'] = sessions_data
        manager.bank.bank['pending'] = pending_data
        # Need to create some release directory to be tested, it is the current release (set in db and production)
        for i in range(1, 6, 1):
            release_dir = os.path.join(self.utils.data_dir, 'alu', 'alu_' + str(i))
            os.makedirs(release_dir)
        # Create a 'current' dir
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'current'))
        # Force auto_delete to False
        Manager.set_simulate(True)
        self.assertTrue(manager.synchronize_db())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.synchronizedb')
    def test_ManagerSynchDBWithCurrentReleaseAndPendingsAndMissingProductionSimulateOFFReturnsTrue(self):
        """Do some tests inside loop over productions. Simulate mode OFF returns True"""
        # sid 1: current release, in prod, on disk
        # sid 2: in prod, on disk, wf_status False, in pending
        # sid 3: in prod, on disk, wf_status True, deleted
        # sid 4: in prod, on disk, not in session
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_verbose(True)
        # Needed for call get_bank_data_dir()
        # Set production
        production_data = [{'data_dir': self.utils.data_dir,
                            'release': "1", 'dir_version': "alu",
                            'session': 1, 'prod_dir': "alu_1"},
                           {'data_dir': self.utils.data_dir,
                            'release': "2", 'dir_version': "alu",
                            'session': 2, 'prod_dir': "alu_2"},
                           {'data_dir': self.utils.data_dir,
                            'release': "3", 'dir_version': "alu",
                            'session': 3, 'prod_dir': "alu_3"},
                           {'data_dir': self.utils.data_dir,
                            'release': "3", 'dir_version': "alu",
                            'session': 4, 'prod_dir': "alu_4"},
                           {'data_dir': self.utils.data_dir,
                            'release': "10", 'dir_version': "alu",
                            'session': 10, 'prod_dir': "alu_10"}]
        # Set sessions
        sessions_data = [{'id': 1, 'workflow_status': True, 'release': "1"},
                         {'id': 2, 'workflow_status': False, 'release': "2"},
                         {'id': 3, 'workflow_status': True, 'deleted': 2, 'release': "3"}]
        # Set pendings
        pending_data = [{'id': 3, 'release': "3"}, {'id': 2, 'release': "2"}]
        manager.bank.bank['last_update_session'] = 3
        manager.bank.bank['current'] = 1
        manager.bank.bank['production'] = production_data
        manager.bank.bank['sessions'] = sessions_data
        manager.bank.bank['pending'] = pending_data
        # Need to create some release directory to be tested, it is the current release (set in db and production)
        for i in range(1, 6, 1):
            release_dir = os.path.join(self.utils.data_dir, 'alu', 'alu_' + str(i))
            os.makedirs(release_dir)
        # Create a 'current' dir
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'current'))
        # Set auto_delete to True
        Manager.set_simulate(False)
        self.assertTrue(manager.synchronize_db())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getbankdatadir')
    def test_ManagerGetBankDataDirReturnsNone(self):
        """Check method warn "Can't get current production directory: 'current_release' ... and returns None"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertIsNone(manager.get_bank_data_dir())

    @attr('manager')
    @attr('manager.getbankdatadir')
    def test_ManagerGetBankDataDirRaisesNoCurrentRelease(self):
        """Check method raises "Can't get current production directory: 'current_release' ..."
         release ok, prod not ok
        """
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': '54'})
        manager.bank.bank['production'] = []
        with self.assertRaises(SystemExit):
            manager.get_bank_data_dir()

    @attr('manager')
    @attr('manager.getbankdatadir')
    def test_ManagerGetBankDataDirOK(self):
        """Check method returns path to production dir"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': '54'})
        manager.bank.bank['production'].append({'session': now, 'release': '54', 'data_dir': self.utils.data_dir})
        returned = manager.get_bank_data_dir()
        expected = os.path.join(self.utils.data_dir, manager.bank.name)
        self.assertEqual(expected, returned)

    @attr('manager')
    @attr('manager.getbankdatadir')
    def test_ManagerGetBankDataDirRaisesNoProd(self):
        """Check method raises "Can't get current production directory, 'prod_dir' or 'data_dir' missing ..."""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        prod_dir = 'alu_54'
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': prod_dir})
        manager.bank.bank['production'].append({'session': now, 'release': prod_dir})
        with self.assertRaises(SystemExit):
            manager.get_bank_data_dir()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDirRaises(self):
        """Check method raises "Can't get current production directory: 'current_release' ..."""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDirRaisesNoCurrentRelease(self):
        """Check method raises "Can't get current production directory: 'current_release' ..."
         release ok, prod not ok
        """
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': '54'})
        manager.bank.bank['production'] = []
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDirOK(self):
        """Check method returns path to production dir"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
    def test_ManagerGetCurrentProdDirRaisesNoProd(self):
        """Check method raises "Can't get current production directory, 'prod_dir' or 'data_dir' missing ..."""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        prod_dir = 'alu_54'
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'release': prod_dir})
        manager.bank.bank['production'].append({'session': now, 'release': prod_dir, 'data_dir': self.utils.data_dir})
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.getlastproductionok')
    def test_ManagerGetLastProductionokNoProductionInBankThrows(self):
        """Check the method throws when no 'production' in bank"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        del manager.bank.bank['production']
        with self.assertRaises(SystemExit):
            manager.get_last_production_ok()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastproductionok')
    def test_ManagerGetLastProductionOKProductionsEmptyReturnsNone(self):
        """Check the method returns None if 'production' is empty"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertIsNone(manager.get_last_production_ok())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastproductionok')
    def test_ManagerGetLastProductionokNoSessionsThrows(self):
        """Check the method throws when no 'sessions'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'fakekey': 'ok'})
        with self.assertRaises(SystemExit):
            manager.get_last_production_ok()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastproductionok')
    def test_ManagerGetLastProductionOkRightProductionWithCurrent(self):
        """Check the method get last 'production' when a 'current' is set"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now, 'remoterelease': '1'})
        manager.bank.bank['production'].append({'session': now + 1, 'remoterelease': '2'})
        prod = manager.get_last_production_ok()
        self.assertEqual(prod['remoterelease'], '2')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastproductionok')
    def test_ManagerGetLastProductionOKRightProductionNoCurrent(self):
        """Check the method return right production without 'current' set"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del manager.bank.bank['current']
        manager.bank.bank['production'].append({'session': now, 'remoterelease': '1'})
        manager.bank.bank['production'].append({'session': now + 2, 'remoterelease': '3'})
        manager.bank.bank['production'].append({'session': now + 1, 'remoterelease': '2'})
        prod = manager.get_last_production_ok()
        self.assertEqual(prod['remoterelease'], '2')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastproductionok')
    def test_ManagerGetLastProductionOKLastProductionIsCurrent(self):
        """Check the method returns None when 'current' is the last 'production'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now, 'remoterelease': '54'})
        prod = manager.get_last_production_ok()
        self.assertIsNone(prod)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getverbose')
    def test_ManagerGetVerboseTrue(self):
        """Check manager.get_verbose() get True when Manager.verbose = True"""
        Manager.verbose = True
        self.assertTrue(Manager.get_verbose())

    @attr('manager')
    @attr('manager.getverbose')
    def test_ManagerGetVerboseFalse(self):
        """Check manager.get_verbose() get False when Manager.verbose = False"""
        Manager.verbose = False
        self.assertFalse(Manager.get_verbose())

    @attr('manager')
    @attr('manager.getsimulate')
    def test_ManagerGetSimulateTrue(self):
        """Check manager.get_simulate() get True when Manager.simulate = True"""
        Manager.simulate = True
        self.assertTrue(Manager.get_simulate())

    @attr('manager')
    @attr('manager.getsimulate')
    def test_ManagerGetSimulateFalse(self):
        """Check manager.get_simulate() get False when Manager.simulate = False"""
        Manager.simulate = False
        self.assertFalse(Manager.get_simulate())

    @attr('manager')
    @attr('manager.banklist')
    def test_ManagerGetBankListWrongVisibility(self):
        """Check bank list throws OK with wrong visibility"""
        with self.assertRaises(SystemExit):
            Manager.get_bank_list(visibility="fake")

    @attr('manager')
    @attr('manager.banklist')
    def test_ManagerGetBankListOK(self):
        """Check bank list works OK"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        self.utils.copy_file(ofile='minium.properties', todir=self.utils.conf_dir)
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
        """Check bank list throws SystemExit exception"""
        from biomaj.mongo_connector import MongoConnector
        from biomaj.config import BiomajConfig
        # Unset MongoConnector and env BIOMAJ_CONF to force config relaod and Mongo reconnect
        MongoConnector.db = None
        BiomajConfig.global_config = None
        back_cfg = os.environ["BIOMAJ_CONF"]
        os.environ['BIOMAJ_CONF'] = "/not_found"
        with self.assertRaises(SystemExit):
            Manager.get_bank_list()
        os.environ['BIOMAJ_CONF'] = back_cfg
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.banklist')
    def test_ManagerGetBankListMongoConnectorNOTOK(self):
        """Check bank list throws ServerSelectionTimeoutError ConnectionFailure exception"""
        from biomaj.mongo_connector import MongoConnector
        from biomaj.config import BiomajConfig
        # Unset MongoConnector and env BIOMAJ_CONF to force config relaod and Mongo reconnect
        config_file = 'global-wrongMongoURL.properties'
        self.utils.copy_file(ofile=config_file, todir=self.utils.conf_dir)
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
        """Check method get the right entries from config"""
        manager = Manager()
        my_values = manager.get_config_regex(regex='.*\.dir$', with_values=False)
        expected = ['lock.dir', 'log.dir', 'process.dir', 'data.dir', 'cache.dir', 'conf.dir']
        self.assertListEqual(my_values, sorted(expected))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getconfigregexp')
    def test_ManagerGetConfigRegExpOKWithValuesFalse(self):
        """Check method get the right entries from config"""
        manager = Manager()
        my_values = manager.get_config_regex(regex='^db\.', with_values=True)
        self.assertListEqual(my_values, [self.utils.db_test, 'mongodb://localhost:27017'])
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getconfigregexp')
    def test_ManagerGetConfigRegExpNoRegExp(self):
        """Check method get the right entries from config"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_config_regex()

    @attr('manager')
    @attr('manager.getbankpackages')
    def test_ManagerGetBankPackagesOK(self):
        """Check get_bank_packages() get the right packages list"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        packs = ['pack@blast@2.2.26', 'pack@fasta@3.6']
        bank_packs = manager.get_bank_packages()
        self.assertListEqual(packs, bank_packs)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getbankpackages')
    def test_ManagerGetBankPackagesNoneOK(self):
        """Check get_bank_packages() returns empty list as bank config file does not have db.packages set"""
        self.utils.copy_file(ofile='minium.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='minium')
        Manager.set_verbose(True)
        bank_packs = manager.get_bank_packages()
        self.assertListEqual(bank_packs, [])
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getformatsforrelease')
    def test_ManagerGetFormatsForReleaseOK(self):
        """Check we get the right list for a bank supported formats"""
        expected = []
        for directory in ['flat', 'blast2/2.2.21', 'fasta/3.6', 'golden/3.0']:
            os.makedirs(os.path.join(self.utils.data_dir, directory))
            expected.append('@'.join(['pack'] + directory.split('/')))
        returned = Manager.get_formats_for_release(path=self.utils.data_dir)
        expected.pop(0)
        self.assertListEqual(expected, returned)

    @attr('manager')
    @attr('manager.getformatsforrelease')
    def test_ManagerGetFormatsForReleaseRaises(self):
        """Check method throws error"""
        with self.assertRaises(SystemExit):
            Manager.get_formats_for_release()

    @attr('manager')
    @attr('manager.getformatsforrelease')
    def test_ManagerGetFormatsForReleasePathNotExistsEmptyList(self):
        """Check method throws error"""
        returned = Manager.get_formats_for_release(path="/not_found")
        self.assertListEqual(returned, [])

    @attr('manager')
    @attr('manager.getlastsession')
    def test_ManagerGetLastSessionOK(self):
        """Check method returns correct session"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['sessions'].append({'id': now, 'name': 'session1'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'name': 'session2'})
        manager.bank.bank['sessions'].append({'id': now + 2, 'name': 'session3'})
        returned = manager._get_last_session()
        self.assertDictEqual(returned, {'id': now + 2, 'name': 'session3'})
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getlastsession')
    def test_ManagerGetLastSessionThrows(self):
        """Check method throws exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        del manager.bank.bank['sessions']
        with self.assertRaises(SystemExit):
            manager._get_last_session()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryNoProductionRaisesError(self):
        """Check when no 'production' field in bank, history raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'] = None
        with self.assertRaises(SystemExit):
            manager.history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryNoSessionsRaisesError(self):
        """Check when no 'sessions' field in bank, history raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12})
        manager.bank.bank['sessions'] = None
        with self.assertRaises(SystemExit):
            manager.history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryCheckIDSessionsOK(self):
        """Check bank has right session id"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        _id = "@".join(['bank', 'alu', '12', Utils.time2datefmt(100)])
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['current'] = 100
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12, 'last_update_time': 100, 'status': {}})
        history = manager.history()
        self.assertEqual(history[0]['_id'], _id)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryCheckStatusDeprecatedOK(self):
        """Check bank has status deprecated"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['current'] = 99
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12, 'last_update_time': 100, 'status': {}})
        history = manager.history()
        self.assertEqual(history[0]['status'], 'unpublished')
        manager.bank.bank['current'] = 101
        history = manager.history()
        self.assertEqual(history[0]['status'], 'deprecated')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistoryStatusUnpublishedOK(self):
        """Check bank not published yet (first run) has status unpublished"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12, 'last_update_time': 100, 'status': {}})
        del manager.bank.bank['current']
        history = manager.history()
        self.assertEqual(history[0]['status'], 'unpublished')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistorySessionsHistoryANDStatusDeletedOK(self):
        """Check bank has status deprecated, no 'current' set"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_12'))
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 101, 'data_dir': self.utils.data_dir, 'dir_version': "alu",
                                              'prod_dir': "alu_12", 'remoterelease': 12, 'last_update_time': 100,
                                              'last_modified': 100, 'status': {'remove_release': True}})
        history = manager.history()
        self.assertEqual(history[0]['status'], 'unpublished')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistorySessionsHistoryANDSessionDeletedOK(self):
        """As we kept sessions history, we check old deleted session have 'deleted' with date in sessions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_12'))
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 101, 'data_dir': self.utils.data_dir, 'dir_version': "alu",
                                              'prod_dir': "alu_12", 'remoterelease': 12, 'last_update_time': 100,
                                              'last_modified': 100, 'status': {'remove_release': True}})
        manager.bank.bank['sessions'].append({'id': 98, 'data_dir': self.utils.data_dir, 'dir_version': "alu",
                                              'prod_dir': "alu_12", 'remoterelease': 12, 'last_update_time': 98,
                                              'last_modified': 98, 'status': {'remove_release': True}, 'deleted': 0})
        history = manager.history()
        self.assertEqual(history[1]['status'], 'deleted')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsNotOK(self):
        """Check method throw exception, can't create directory"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['properties']['owner'] = manager.config.get('GENERAL', 'admin')
        back_log = os.environ["LOGNAME"]
        os.environ["LOGNAME"] = manager.config.get('GENERAL', 'admin')
        with self.assertRaises(SystemExit):
            manager.save_banks_version(bank_file='/not_found/saved_versions.txt')
        # Reset to the right user name as previously
        os.environ["LOGNAME"] = back_log
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsThrowsException(self):
        """Check method throw exception, can't access file"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['properties']['owner'] = manager.config.get('GENERAL', 'admin')
        back_log = os.environ["LOGNAME"]
        outputfile = os.path.join(self.utils.data_dir, 'saved_versions.txt')
        open(outputfile, 'w').close()
        os.chmod(outputfile, 0o000)
        os.environ["LOGNAME"] = manager.config.get('GENERAL', 'admin')
        with self.assertRaises(SystemExit):
            manager.save_banks_version(bank_file=outputfile)
        # Reset to the right user name as previously
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsNoFileOK(self):
        """Test exceptions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now},
                                                    '$push': {
                                                        'production': {'session': now,
                                                                       'remoterelease': '54', 'size': '100Mo'}}})
        # Prints on output using simulate mode

        self.assertTrue(manager.save_banks_version())
        # Reset to the right user name as previously
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsFileContentOK(self):
        """Test exceptions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        output_file = os.path.join(self.utils.data_dir, 'saved_version.txt')
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now},
                                                    '$push': {
                                                        'production': {'session': now,
                                                                       'remoterelease': '54', 'size': '100Mo'}}})
        # Prints on output using simulate mode
        back_patt = Manager.SAVE_BANK_LINE_PATTERN
        Manager.SAVE_BANK_LINE_PATTERN = "%s_%s_%s_%s_%s"
        manager.save_banks_version(bank_file=output_file)
        line = Manager.SAVE_BANK_LINE_PATTERN % ('alu', "Release " + '54', Utils.time2datefmt(now),
                                                 '100Mo', manager.bank.config.get('server'))
        with open(output_file, 'r') as of:
            for oline in of:
                self.assertEqual(line, oline)
        # Restore default pattern
        Manager.SAVE_BANK_LINE_PATTERN = back_patt
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.bankversions')
    def test_ManagerSaveBankVersionsManagerVerboseOK(self):
        """Test exceptions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'current': now},
                                                    '$push': {
                                                        'production': {'session': now,
                                                                       'remoterelease': '54', 'size': '100Mo'}}})
        # Set verbose mode
        Manager.set_verbose(True)
        self.assertTrue(manager.save_banks_version())
        # Unset verbose mode
        manager.set_bank(False)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleaseAlreadySet(self):
        """Check we directly return next_release if already set"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager._next_release = '55'
        self.assertEqual(manager.next_release(), '55')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleaseThrowsNoProduction(self):
        """Check method throws an exception if no production yet"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        with self.assertRaises(SystemExit):
            manager.next_release()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleaseThrowsNoSessions(self):
        """Check method throws an exception if no 'sessions'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now, 'remoterelease': '55'})
        manager.bank.bank['production'].append({'session': now + 1, 'remoterelease': '56'})
        del manager.bank.bank['sessions']
        with self.assertRaises(SystemExit):
            manager.next_release()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleaseReturnsNone(self):
        """Check method returns a None release because 'workflow_status' is False"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now})
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55', 'workflow_status': False})
        self.assertIsNone(manager.next_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleasePassesContinue(self):
        """Check method get the right release (next) using 'remoterelease' from sessions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now})
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55', 'workflow_status': True})
        self.assertEqual('55', manager.next_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleasePassesContinue(self):
        """Check method get the right release (next) using 'release' from sessions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now})
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now, 'release': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'release': '55', 'workflow_status': True})
        self.assertEqual('55', manager.next_release())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleaseSessionsMissingReleaseFieldsThorws(self):
        """Check method throws because nor 'remoterelease' nor 'release' found in sessions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['production'].append({'session': now})
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now})
        manager.bank.bank['sessions'].append({'id': now + 1, 'workflow_status': True})
        with self.assertRaises(SystemExit):
            manager.next_release()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextswitch')
    def test_ManagerNextSwitchDateThrows(self):
        """Check the method throws when wrong arg passed"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager.next_switch_date(week='wrong')

    @attr('manager')
    @attr('manager.nextswitch')
    def test_ManagerNextSwitchDateNoConfigThrows(self):
        """Check the method throws when wrong arg passed"""
        manager = Manager()
        manager.config.remove_option('MANAGER', 'switch.week')
        with self.assertRaises(SystemExit):
            manager.next_switch_date()

    @attr('manager')
    @attr('manager.nextswitch')
    def test_ManagerNextSwitchDateConfigThrows(self):
        """Check the method throws when wrong config"""
        manager = Manager()
        manager.config.set('MANAGER', 'switch.week', 'wrong')
        with self.assertRaises(SystemExit):
            manager.next_switch_date()

    @attr('manager')
    @attr('manager.nextswitch')
    def test_ManagerNextSwitchWithConfigEachWeek(self):
        """Check the method gives the right next bank switch date. We are expecting the same week as today"""
        manager = Manager()
        # Get the current week
        week_num = datetime.today().isocalendar()[1]
        manager.config.set('MANAGER', 'switch.week', 'each')
        returned = manager.next_switch_date()
        self.assertEqual(week_num, returned.isocalendar()[1])

    @attr('manager')
    @attr('manager.nextswitch')
    def test_ManagerNextSwitchWithConfigNextWeek(self):
        """Check the method gives the right next bank switch date. We are expecting next week"""
        manager = Manager()
        # Get the current week
        week_num = datetime.today().isocalendar()[1]
        # We are setting config value to get value for next week
        if not week_num % 2:
            manager.config.set('MANAGER', 'switch.week', 'odd')
        else:
            manager.config.set('MANAGER', 'switch.week', 'even')
        returned = manager.next_switch_date()
        # As the expected week must be next week, it is current week number + 1
        self.assertEqual(week_num + 1, returned.isocalendar()[1])

    @attr('manager')
    @attr('manager.nextswitch')
    def test_ManagerNextSwitchWithConfigThisWeek(self):
        """Check the method gives the right next bank switch date. We are expecting next week"""
        manager = Manager()
        # Get the current week
        week_num = datetime.today().isocalendar()[1]
        # We are setting config value to get value for next week
        if not week_num % 2:
            manager.config.set('MANAGER', 'switch.week', 'even')
        else:
            manager.config.set('MANAGER', 'switch.week', 'odd')
        returned = manager.next_switch_date()
        self.assertEqual(week_num, returned.isocalendar()[1])

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankOK(self):
        """Check method checks are ok"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager()
        from biomaj.bank import Bank
        b = Bank('alu', no_log=True)
        self.assertTrue(manager.set_bank(bank=b))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankNOTOK(self):
        """Check method checks are not ok"""
        manager = Manager()
        self.assertFalse(manager.set_bank())

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankWrongInstanceOK(self):
        """Check method checks are not ok"""
        manager = Manager()
        self.assertFalse(manager.set_bank(bank=Manager()))

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankFromNameFalse(self):
        """Check method checks are not ok"""
        manager = Manager()
        self.assertFalse(manager.set_bank_from_name(""))

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankFromNameThrowsWrongBankName(self):
        """Check method throws excpetion with wrong bank name"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager.set_bank_from_name("no_bank")

    @attr('manager')
    @attr('manager.setbank')
    def test_ManagerSetBankFromNameOK(self):
        """Check method checks are not ok"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager()
        self.assertTrue(manager.set_bank_from_name("alu"))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setsequencecount')
    def test_ManagerSetSequenceCountSeqFileThrows(self):
        """Check missing arg seq_file throws"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.set_sequence_count(seq_count=1, release="54")
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setsequencecount')
    def test_ManagerSetSequenceCountSeqFileNotHereThrows(self):
        """Check missing file not exists throws"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.set_sequence_count(seq_file="/not_found/file.fa", seq_count=1, release="54")
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setsequencecount')
    def test_ManagerSetSequenceCountSeqCountThrows(self):
        """Check missing args throws"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        open(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2', 'news1.txt'), 'w').close()
        with self.assertRaises(SystemExit):
            manager.set_sequence_count(seq_file=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2', 'news1.txt'),
                                       release="54")
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setsequencecount')
    def test_ManagerSetSequenceCountReleaseThrows(self):
        """Check missing args throws"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        open(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2', 'news1.txt'), 'w').close()
        with self.assertRaises(SystemExit):
            manager.set_sequence_count(seq_file=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2', 'news1.txt'),
                                       seq_count=10)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setsequencecount')
    def test_ManagerSetSequenceCountReturnsTrue(self):
        """Check method returns True"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'production.0.release': "54"}})
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        open(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2', 'news1.txt'), 'w').close()
        self.assertTrue(manager.set_sequence_count(seq_file=os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2',
                                                                         'news1.txt'),
                                                   seq_count=10, release="54"))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setsequencecount')
    def test_ManagerSetSequenceCountUpdateOKReturnsTrue(self):
        """Check method update db and returns True"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_verbose(True)
        manager.bank.banks.update({'name': 'alu'}, {'$set': {'production.0.release': "54"}})
        manager.bank.banks.update({'name': 'alu', 'production.release': "54"},
                                  {'$push': {'production.$.files_info':
                                                 {'name':
                                                      os.path.join(self.utils.data_dir,
                                                      'alu',
                                                      'alu_54',
                                                      'blast2',
                                                      'news1.txt')}}})
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2'))
        open(os.path.join(self.utils.data_dir, 'alu', 'alu_54', 'blast2', 'news1.txt'), 'w').close()
        self.assertTrue(manager.set_sequence_count(seq_file=os.path.join(self.utils.data_dir,
                                                                         'alu',
                                                                         'alu_54',
                                                                         'blast2',
                                                                         'news1.txt'),
                                                   seq_count=10, release="54"))
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.setverbose')
    def test_ManagerSetVerboseReturnsTrue(self):
        """Check set verbose set the correct boolean"""
        self.assertTrue(Manager.set_verbose("OK"))

    @attr('manager')
    @attr('manager.setverbose')
    def test_ManagerSetVerboseReturnsFalse(self):
        """Check set verbose set the correct boolean"""
        self.assertFalse(Manager.set_verbose(""))

    @attr('manager')
    @attr('manager.setsimulate')
    def test_ManagerSetSimulateReturnsTrue(self):
        """Check set simulate set the correct boolean"""
        self.assertTrue(Manager.set_simulate("OK"))

    @attr('manager')
    @attr('manager.setsimulate')
    def test_ManagerSetSimulateReturnsFalse(self):
        """Check set simulate set the correct boolean"""
        self.assertFalse(Manager.set_simulate(False))

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitchBankIsLocked(self):
        """Check manager.can_switch returns False because bank is locked"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_verbose(True)
        lock_file = os.path.join(manager.bank.config.get('lock.dir'), manager.bank.name + '.lock')
        with open(lock_file, 'a'):
            self.assertFalse(manager.can_switch())
        os.remove(lock_file)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdateCannotSwitch(self):
        """Check method returns empty dict because bank cannot switch"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # setting current to None means no current bank published.
        manager.bank.bank['current'] = None
        returned = manager.show_need_update()
        self.assertListEqual(returned, [])

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdateCanSwitchOneBank(self):
        """Check method returns dict because bank can switch"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        # We created these 2 managers to set 2 banks in db
        alu = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        # setting current to None means no current bank published.
        alu.bank.bank['current'] = now
        alu.bank.bank['last_update_session'] = now + 1
        alu.bank.bank['production'].append({'session': now})
        alu.bank.bank['production'].append({'session': now + 1})
        alu.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        alu.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55', 'workflow_status': True})
        returned = alu.show_need_update()
        self.assertListEqual(returned, [{'name': 'alu', 'current_release': '54', 'next_release': '55'}])

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdateCanSwitchTwoBank(self):
        """Check method returns dict because bank can switch"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        self.utils.copy_file(ofile='minium.properties', todir=self.utils.conf_dir)
        now = time.time()
        # We created these 2 managers to set 2 banks in db
        alu = Manager(bank='alu')
        minium = Manager(bank='minium')
        # We update the bank in db to mimic bank ready to switch
        alu.bank.banks.update({'name': 'alu'}, {'$set': {'current': now, 'production': [{'session': now + 1}]}})
        alu.bank.banks.update({'name': 'alu'}, {'$set': {'last_update_session': now + 1}})
        alu.bank.banks.update({'name': 'alu'}, {'$set': {'sessions': [{'id': now + 1, 'workflow_status': True,
                                                                       'remoterelease': '54'}]}})
        minium.bank.banks.update({'name': 'minium'}, {'$set': {'current': now, 'production': [{'session': now + 1}]}})
        minium.bank.banks.update({'name': 'minium'}, {'$set': {'last_update_session': now + 1}})
        minium.bank.banks.update({'name': 'minium'}, {'$set': {'sessions': [{'id': now + 1, 'workflow_status': True,
                                                                             'remoterelease': '55'}]}})
        # We reload the banks
        manager = Manager()
        returned = manager.show_need_update()
        self.assertEqual(len(returned), 2)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitchBankNotPublished(self):
        """Check manager.can_switch returns False because bank not published yet"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.set_verbose(True)
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['current'] = None
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitchBankUpdateNotReady(self):
        """Check manager.can_switch returns False because update not ready"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        manager.set_verbose(True)
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['sessions'].append({'id': now, 'workflow_status': True})
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitchBankLastSessionFailed(self):
        """Check manager.can_switch returns False because last session failed"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        manager.set_verbose(True)
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['sessions'].append({'id': now, 'workflow_status': False})
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_SwitchTrue(self):
        """Check manager.can_switch returns True"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        manager.bank.bank['current'] = now
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['last_update_session'] = now + 1
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now + 1, 'workflow_status': True})
        self.assertTrue(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyRaisesErrorOK(self):
        """Check the method raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        Manager.set_verbose(True)
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyLastProductionOKReturnsNone(self):
        """Check method returns None when 'production' is empty through (get_last_production_ok)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['production'] = []
        self.assertFalse(manager.update_ready())

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithCurrentTrue(self):
        """Check the method returns True, current != last_update_session and production + sessions"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now + 1
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now + 1, 'workflow_status': True})
        self.assertTrue(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithCurrentFalse(self):
        """Check the method returns False"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.set_verbose(True)
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithProductionAndContinueFalse(self):
        """Check the method returns False and current set and session has its id (pass through continue statement)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.set_verbose(True)
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now + 1
        manager.bank.bank['production'].append({'session': now})
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now + 1, 'workflow_status': False})
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyNoSessionFalse(self):
        """Check the method returns False because no 'session'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.set_verbose(True)
        del manager.bank.bank['current']
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['production'].append({'session': now})
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithNoProductionThrows(self):
        """Check the method returns throws because no 'production'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.set_verbose(True)
        del manager.bank.bank['current']
        del manager.bank.bank['production']
        manager.bank.bank['last_update_session'] = now
        with self.assertRaises(SystemExit):
            self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithSessionsFalse(self):
        """Check the method returns using 'sessions'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del manager.bank.bank['current']
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['production'].append({'session': now + 1})
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55',
                                              'workflow_status': False})
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandCheckConfigThrows(self):
        """Check method that check config for jobs throws ok"""
        manager = Manager()
        manager.config.remove_section('JOBS')
        with self.assertRaises(SystemExit):
            manager._check_config_jobs('restart.stopped.jobs')

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandCheckConfigStop(self):
        """Check removing info from config file returns False"""
        manager = Manager()
        manager.config.remove_option('JOBS', 'stop.running.jobs.exe')
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertFalse(manager.stop_running_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandCheckConfigRestart(self):
        """Check removing info from config file returns False"""
        manager = Manager()
        manager.config.remove_option('JOBS', 'restart.stopped.jobs.exe')
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertFalse(manager.restart_stopped_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandRestartJobsScriptOK(self):
        """Check restart jobs runs OK"""
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertTrue(manager.restart_stopped_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandRestartJobsScriptDoesNotExists(self):
        """Check restart jobs runs OK"""
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        manager.config.set('JOBS', 'restart.stopped.jobs.exe', '/nobin/cmd')
        with self.assertRaises(SystemExit):
            manager.restart_stopped_jobs()
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandStopJobsScriptOK(self):
        """Check restart jobs runs OK"""
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertTrue(manager.stop_running_jobs())
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerCommandStopScriptDoesNotExists(self):
        """Check restart jobs runs OK"""
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        manager.config.set('JOBS', 'stop.running.jobs.exe', '/nobin/cmd')
        with self.assertRaises(SystemExit):
            manager.stop_running_jobs()
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandWithExtraArgsOK(self):
        """Check the addition of extra args onto the command line is OK"""
        manager = Manager()
        # Grans usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ['LOGNAME'] = manager.config.get('GENERAL', 'admin')
        self.assertTrue(manager.stop_running_jobs(args=['EXTRA ARGS']))
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandWithExtraArgsNotListThrows(self):
        """Check the method throws exception when extra Args for command line is not a List"""
        manager = Manager()
        # Grant usage for current user
        back_log = os.environ["LOGNAME"]
        os.environ["LOGNAME"] = manager.config.get('GENERAL', 'admin')
        with self.assertRaises(SystemExit):
            manager.stop_running_jobs(args="NOT A LIST AS ARGS")
        os.environ["LOGNAME"] = back_log

    @attr('manager')
    @attr('manager.command')
    def test_ManagerLaunchCommandOK(self):
        """Check a command started is OK"""
        manager = Manager()
        self.assertTrue(manager._run_command(exe='ls', args=['/tmp'], quiet=True))

    @attr('manager')
    @attr('manager.command')
    def test_ManagerLaunchCommandError(self):
        """Check a wrong return launched command"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='ls', args=['/notfound'], quiet=True)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorNoExe(self):
        """Check method throws error when no 'exe'"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(args=['foobar'], quiet=True)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorNoRights(self):
        """Check method throws error we can run command, no rights"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='chmod', args=['-x', '/bin/ls'], quiet=False)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorCantRunCommand(self):
        """Check method throws error command does not exist"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='/bin/fakebin', args=['/usr/local'], quiet=True)


class TestBiomajManagerPlugins(unittest.TestCase):
    """Class for testing biomajmanager.plugins class"""

    def setUp(self):
        """Setup stuff"""
        self.utils = UtilsForTests()
        self.utils.copy_plugins()
        # Make our test global.properties set as env var
        os.environ['BIOMAJ_CONF'] = self.utils.global_properties

    def tearDown(self):
        """Clean"""
        self.utils.clean()

    @attr('plugins')
    def test_PluginLoadErrorNoManager(self):
        """Check we've got an exception thrown when Plugin Object is build without manager as args"""
        with self.assertRaises(SystemExit):
            Plugins()

    @attr('plugins')
    def test_PluginsLoadedOK_AsStandAlone(self):
        """Check the Plugins Object can be build as a standalone object"""
        manager = Manager()
        plugins = Plugins(manager=manager)
        self.assertIsInstance(plugins, Plugins)

    @attr('plugins')
    @attr('plugins.loading')
    def test_PluginsLoaded(self):
        """Check a list of plugins are well loaded"""
        manager = Manager()
        manager.load_plugins()
        self.assertEqual(manager.plugins.myplugin.get_name(), 'myplugin')
        self.assertEqual(manager.plugins.anotherplugin.get_name(), 'anotherplugin')

    @attr('plugins')
    @attr('plugins.listplugins')
    def test_PluginsListPlugins(self):
        """Check method returns right list of configured plugins from file"""
        manager = Manager()
        returned = manager.list_plugins()
        expected = ['myplugin', 'anotherplugin']
        self.assertListEqual(expected, returned)

    @attr('plugins')
    @attr('plugins.listplugins')
    def test_PluginsListPluginsWithEmptyValue(self):
        """Check method returns right list of configured plugins from file, we introduced some empty lines"""
        manager = Manager()
        manager.config.set('PLUGINS', 'plugins.list', 'myplugin,,,anotherplugin')
        returned = manager.list_plugins()
        expected = ['myplugin', 'anotherplugin']
        self.assertListEqual(expected, returned)

    @attr('plugins')
    @attr('plugins.loading')
    def test_PluginsLoadingNoSection(self):
        """Check the availability of section 'PLUGINS' is correctly checked"""
        manager = Manager()
        manager.config.remove_section('PLUGINS')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    @attr('plugins.loading')
    def test_PluginsLoadingNoPLuginsDir(self):
        """Check the plugins.dir value is correctly checked"""
        manager = Manager()
        manager.config.remove_option('MANAGER', 'plugins.dir')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    @attr('plugins.loading')
    def test_PluginsLoadingNoPLuginsList(self):
        """Check the plugins.dir value is correctly checked"""
        manager = Manager()
        manager.config.remove_option('PLUGINS', 'plugins.list')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    @attr('plugins.loading')
    def test_PluginsLoadingNoPluginsDirExists(self):
        """Check the plugins.dir path  is correctly checked"""
        manager = Manager()
        manager.config.set('MANAGER', 'plugins.dir', '/notfound')
        with self.assertRaises(SystemExit):
            manager.load_plugins()

    @attr('plugins')
    @attr('plugins.loading')
    def test_PluginsLoadingNoConfig(self):
        """Check config instance is OK"""
        manager = Manager()
        manager.load_plugins()
        from configparser import RawConfigParser
        self.assertIsInstance(manager.plugins.myplugin.get_config(), RawConfigParser)

    @attr('plugins')
    def test_PluginsLoadingNoManager(self):
        """Check manager instance is OK"""
        manager = Manager()
        manager.load_plugins()
        self.assertIsInstance(manager.plugins.myplugin.get_manager(), Manager)

    @attr('plugins')
    def test_PluginsCheckConfigValues(self):
        """Check the plugins config values"""
        manager = Manager()
        manager.load_plugins()
        self.assertEqual(manager.plugins.myplugin.get_cfg_name(), 'myplugin')
        self.assertEqual(manager.plugins.myplugin.get_cfg_value(), '1')
        self.assertEqual(manager.plugins.anotherplugin.get_cfg_name(), 'anotherplugin')
        self.assertEqual(manager.plugins.anotherplugin.get_cfg_value(), '2')

    @attr('plugins')
    def test_PluginsCheckMethodValue(self):
        """Check the value returned by method is OK"""
        manager = Manager()
        manager.load_plugins()
        self.assertEqual(manager.plugins.myplugin.get_value(), 1)
        self.assertEqual(manager.plugins.myplugin.get_string(), 'test')
        self.assertEqual(manager.plugins.anotherplugin.get_value(), 1)
        self.assertEqual(manager.plugins.anotherplugin.get_string(), 'test')

    @attr('plugins')
    def test_PluginsCheckTrue(self):
        """Check boolean returned by method"""
        manager = Manager()
        manager.load_plugins()
        self.assertTrue(manager.plugins.myplugin.get_true())
        self.assertTrue(manager.plugins.anotherplugin.get_true())

    @attr('plugins')
    def test_PluginsCheckFalse(self):
        """Check boolean returned by method"""
        manager = Manager()
        manager.load_plugins()
        self.assertFalse(manager.plugins.myplugin.get_false())
        self.assertFalse(manager.plugins.anotherplugin.get_false())

    @attr('plugins')
    def test_PluginsCheckNone(self):
        """Check None returned by method"""
        manager = Manager()
        manager.load_plugins()
        self.assertIsNone(manager.plugins.myplugin.get_none())
        self.assertIsNone(manager.plugins.anotherplugin.get_none())

    @attr('plugins')
    def test_PluginsCheckException(self):
        """Check exception returned by method"""
        manager = Manager()
        manager.load_plugins()
        self.assertRaises(Exception, manager.plugins.myplugin.get_exception())
        self.assertRaises(Exception, manager.plugins.anotherplugin.get_exception())
