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
from biomajmanager.news import News
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

        # Set a mongo client
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
                else:
                    fout.write(line)
        fout.close()

    def __copy_test_global_properties(self):
        """Copy global.properties file into testing directory"""
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
        fout.close()


class TestBiomajManagerUtils(unittest.TestCase):
    """Class for testing manager.utils class"""

    def setUp(self):
        self.utils = UtilsForTests()

    def tearDown(self):
        self.utils.clean()

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
        files = Utils.get_files(self.utils.tmp_dir)
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

    # @attr('utils')
    # def test_local2utc(self):
    #    """
    #     Check local2utc returns the right time according to local time
    #     :return:
    #    """
    #     now = datetime.now()
    #     utc_now = Utils.local2utc(now)
    #     self.assertEquals(utc_now.hour + 1, now.hour)
    #
    # @attr('utils')
    # def test_local2utc_WrongArgsType(self):
    #    """
    #     We check the args instance checking throws an error
    #     :return:
    #    """
    #     with self.assertRaises(SystemExit):
    #         Utils.local2utc(int(2))

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
        self.assertIsInstance(Utils.time2datefmt(time.time(), Manager.DATE_FMT), str)

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
            Writer(template_dir=self.utils.template_dir, config=manager.config)

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
            Writer(template_dir=self.utils.template_dir, config=manager.config)

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
                                                'prod_dir': 'alu-54'})
        self.utils.manager = manager
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'flat'))
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed'))
        os.makedirs(os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'blast2'))

    def tearDown(self):
        """Clean all"""
        self.utils.clean()
        # As we created an entry in the database ('alu'), we clean the database
        self.utils.drop_db()

    @attr('links')
    @attr('links.init')
    def test_LinksInitOK(self):
        """Check init Links instance is OK"""
        links = Links(manager=self.utils.manager)
        self.assertEqual(links.created_links, 0)

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
    @attr('links.init')
    def test_LinksInitNoCurrentProdDirThrows(self):
        """Check init throws exception when no production dir ready"""
        self.utils.manager.bank.bank['production'].pop()
        with self.assertRaises(SystemExit):
            Links(manager=self.utils.manager)

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
    def test_LinksCheckLinksSimulateTrueVeboseFalseOK(self):
        """Check method returns right number of simulated created links"""
        links = Links(manager=self.utils.manager)
        Manager.set_simulate(True)
        Manager.set_verbose(False)
        # Check setUp, it creates 3 dirs
        self.assertEqual(links.check_links(), 2)

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
        self.assertEqual(links.do_links(dirs=None, files=None), 2)

    @attr('links')
    @attr('links.dolinks')
    def test_LinksDoLinksArgsDirsMatchesSetUp(self):
        """Check method creates the right number of link passing a list of dirs matching setUp"""
        links = Links(manager=self.utils.manager)
        exp_dirs = {'flat': [{'target':'ftp'}], 'uncompressed': [{'target': 'release'}],
                    'blast2': [{'target': 'index/blast2'}]}
        self.assertEqual(links.do_links(dirs=exp_dirs, files=None), 3)

    @attr('links')
    @attr('links.dolinks')
    def test_LinksDoLinksArgsFilesMatchesSetUp(self):
        """Check method creates the right number of link passing a list of dirs matching setUp"""
        links = Links(manager=self.utils.manager)
        # We copy 3 files into a source dir to have 3 more created links calling generate_files_link
        self.utils.copy_file(ofile='news1.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'blast2'))
        self.utils.copy_file(ofile='news2.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'blast2'))
        self.utils.copy_file(ofile='news3.txt', todir=os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'blast2'))
        exp_files = {'blast2': [{'target': 'index/blast2'}]}
        self.assertEqual(links.do_links(dirs=None, files=exp_files), 5)

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
        link = Links(manager=self.utils.manager)
        self.utils.manager.config.remove_option('GENERAL', 'data.dir')
        with self.assertRaises(SystemExit):
            link._prepare_links(source=self.utils.data_dir, target="test")

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksArgsOKConfigProdDirMissingThrows(self):
        """Check method throws if source given but no other args"""
        link = Links(manager=self.utils.manager)
        self.utils.manager.config.remove_option('MANAGER', 'production.dir')
        with self.assertRaises(SystemExit):
            link._prepare_links(source=self.utils.data_dir, target="test")

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksArgsOKSourceNotDirReturns1(self):
        """Check method throws if source given is not a directory"""
        link = Links(manager=self.utils.manager)
        link.manager.config.set('GENERAL', 'data.dir', '/dir/does_not/')
        link.manager.set_verbose(True)
        self.assertEqual(link._prepare_links(source='/exist', target="link_test"), 1)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithFallbackOK(self):
        """Check method passes OK if fallback given"""
        link = Links(manager=self.utils.manager)
        # Remove uncompressed directory, and fallback to flat
        os.removedirs(os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed'))
        link.manager.set_verbose(True)
        self.assertEqual(link._prepare_links(source='uncompressed', target='flat_test', fallback='flat'), 0)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithFallbackUseDeepestOK(self):
        """Check method passes OK if fallback given"""
        link = Links(manager=self.utils.manager)
        # Remove uncompressed directory, and fallback to flat
        self.assertEqual(link._prepare_links(source='uncompressed', target='flat_test', use_deepest=True), 0)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksWithSimulateModeOK(self):
        """Check method prints in simulate mode"""
        link = Links(manager=self.utils.manager)
        link.manager.set_simulate(True)
        link.manager.set_verbose(True)
        # Remove uncompressed directory, and fallback to flat
        self.assertEqual(link._prepare_links(source='uncompressed', target='flat_test'), 0)

    @attr('links')
    @attr('links.preparelinks')
    def test_LinksPrepareLinksMakeTargetDirThrows(self):
        """Check method throws when making target dir"""
        link = Links(manager=self.utils.manager)
        link.manager.set_simulate(False)
        link.manager.set_verbose(False)
        # Remove uncompressed directory, and fallback to flat
        with self.assertRaises(SystemExit):
            link._prepare_links(source='uncompressed', target='../../../../flat_test')

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
        source = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed')
        target = os.path.join(self.utils.prod_dir, 'uncmp_link')
        os.symlink(os.path.relpath(source, start=target), target)
        self.assertEqual(0, link._make_links(links=[(source, target)]))
        os.remove(target)

    @attr('links')
    @attr('links.makelinks')
    def test_LinksMakeLinksPathNotExistsSimulateOnVerboseOnReturns0(self):
        """Check the method returns 0 because simulate and verbose mode on"""
        link = Links(manager=self.utils.manager)
        source = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed')
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
        source = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed')
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
        source = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed')
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
        source = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'uncompressed')
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
        source_dir = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'flat')
        target_dir = os.path.join(self.utils.prod_dir, 'flat_symlink')
        files = ['file1.txt', 'file2.txt']
        # Create files to link
        for ifile in files:
            open(os.path.join(source_dir, ifile), 'w').close()
        # We check we've created 2 link, for file1 and file2
        self.assertEqual(2, link._generate_files_link(source='flat', target='flat_symlink'))
        # We can also check link.source and link.target are equal to our source_dir and target_dir
        self.assertEqual(source_dir, link.source)
        self.assertEqual(target_dir, link.target)

    @attr('links')
    @attr('links.generatefileslink')
    def test_LinksGenerateFilesLinkNotNoExtCreatedLinksOKVerboseOnSmulateOn(self):
        """Check method returns correct number of created links (no_ext=False)"""
        link = Links(manager=self.utils.manager)
        # Set our manager verbose mode to on
        link.manager.set_verbose(True)
        link.manager.set_simulate(True)
        source_dir = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'flat')
        target_dir = os.path.join(self.utils.prod_dir, 'flat_symlink')
        files = ['file1.txt', 'file2.txt']
        # Create list of file to link
        for ifile in files:
            open(os.path.join(source_dir, ifile), 'w').close()
        # We check we've created 2 link, for file1 and file2
        self.assertEqual(0, link._generate_files_link(source='flat', target='flat_symlink'))
        # We can also check link.source and link.target are equal to our source_dir and target_dir
        self.assertEqual(source_dir, link.source)
        self.assertEqual(target_dir, link.target)

    @attr('links')
    @attr('links.generatefileslink')
    def test_LinksGenerateFilesLinkNotNoExtCreatedLinksOKVerboseOnRemoveExtTrue(self):
        """Check method returns correct number of created links (remove_ext=True)"""
        link = Links(manager=self.utils.manager)
        # Set our manager verbose mode to on
        link.manager.set_verbose(True)
        source_dir = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'flat')
        target_dir = os.path.join(self.utils.prod_dir, 'flat_symlink')
        files = ['file1.txt', 'file2.txt']
        # Create list of file to link
        for ifile in files:
            open(os.path.join(source_dir, ifile), 'w').close()
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
        source = os.path.join(self.utils.data_dir, 'alu', 'alu-54', 'blast2')
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
    def test_NewWithMaxNews(self):
        """Check max_news args is OK"""
        news = News(max_news=10)
        self.assertEqual(news.max_news, 10)

    @attr('manager')
    @attr('manager.news')
    def test_NewWithConfigOK(self):
        """Check init set everything from config as arg"""
        manager = Manager()
        news_dir = manager.config.get('MANAGER', 'news.dir')
        news = News(config=manager.config)
        self.assertEqual(news_dir, news.news_dir)

    @attr('manager')
    @attr('manager.news')
    def test_NewWithConfigNoSection(self):
        """Check init throws because config has no section 'MANAGER'"""
        manager = Manager()
        manager.config.remove_section('MANAGER')
        with self.assertRaises(SystemExit):
            News(config=manager.config)

    @attr('manager')
    @attr('manager.news')
    def test_NewWithConfigNoOption(self):
        """Check init throws because config has no option 'news.dir"""
        manager = Manager()
        manager.config.remove_option('MANAGER', 'news.dir')
        with self.assertRaises(SystemExit):
            News(config=manager.config)

    @attr('manager')
    @attr('manager.news')
    def test_NewsNewsDirOK(self):
        """Check get_news set correct thing"""
        self.utils.copy_news_files()
        news = News()
        news.get_news(news_dir=self.utils.news_dir)
        self.assertEqual(news.news_dir, self.utils.news_dir)

    @attr('manager')
    @attr('manager.news')
    def test_NewsDirNotADirectory(self):
        """Check the dir given is not a directory"""
        with self.assertRaises(SystemExit):
            News(news_dir="/foobar")

    @attr('manager')
    @attr('manager.news')
    def test_NewsGetNewsWrongDirectory(self):
        """Check method throws exception with wrong dir calling get_news"""
        news = News()
        with self.assertRaises(SystemExit):
            news.get_news(news_dir='/not_found')

    @attr('manager')
    @attr('manager.news')
    def test_NewsGetNewsNewsDirNotDefined(self):
        """Check method throws exception while 'news.dir' not defined"""
        news = News()
        with self.assertRaises(SystemExit):
            news.get_news()

    @attr('manager')
    @attr('manager.news')
    def test_FileNewsContentEqual(self):
        """Check the content of 2 generated news files are identical"""
        self.utils.copy_news_files()
        data = []
        for i in range(1, 4):
            data.append({'label': 'type' + str(i),
                         'date': str(i) + '0/12/2015',
                         'title': 'News%s Title' % str(i),
                         'text': 'This is text #%s from news%s' % (str(i), str(i)),
                         'item': i - 1})
        news = News(news_dir=self.utils.news_dir)
        news_data = news.get_news()
        # Compare data
        data.reverse()

        if 'news' in news_data:
            for new in news_data['news']:
                dat = data.pop()
                for k in ['label', 'date', 'title', 'text', 'item']:
                    self.assertEqual(dat[k], new[k])
        else:
            raise unittest.E
        shutil.rmtree(self.utils.news_dir)


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
            Manager.load_config(global_cfg=os.path.join(self.utils.conf_dir, 'global.properties'))

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
                             ["alu", "nucleic,protein", Utils.time2datefmt(now, Manager.DATE_FMT), '54']],
                    'prod': [["Session", "Remote release", "Release", "Directory", "Freeze", "Pending"],
                             [Utils.time2datefmt(now, Manager.DATE_FMT), '54', '54',
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
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedNoLastUpdateSession(self):
        """Check method returns False when no 'last_update_session' field in database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        self.assertFalse(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedStatusOverWorkflowStatusTrue(self):
        """Check method returns False when no 'last_update_session' field in database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'status': {'over': False}},
                             {'id': now, 'status': {'over': False}, 'workflow_status': True}],
                'last_update_session': now,
                }
        manager = Manager(bank='alu')
        manager.bank.bank = data
        self.assertFalse(manager.last_session_failed())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.lastsessionfailed')
    def test_ManagerLastSessionFailedStatusOverWorkflowStatusFalse(self):
        """Check method returns False when no 'last_update_session' field in database"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'status': {'over': False}},
                             {'id': now, 'status': {'over': False}, 'workflow_status': False}],
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
                'sessions': [{'id': 0, 'status': {'over': True}}, {'id': now, 'status': {'over': True}}],
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
                'sessions': [{'id': 0, 'status': {'over': True}}, {'id': now, 'status': {'over': True}}],
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
        """Check we have a failed session and no pending session(s)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        data = {'name': 'alu',
                'sessions': [{'id': 0, 'status': {'over': True}}, {'id': now, 'status': {'over': False}}],
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
    @attr('manager.getsessionfromid')
    def test_ManagerGetSessionFromIDNotNoneNotNone(self):
        """Check we retrieve the right session id (Not None)"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        data = {'name': 'alu',
                'sessions': [{'id': 1, 'status': {'over': True}},
                             {'id': 2, 'status': {'over': True}}]}
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
                'sessions': [{'id': 1, 'status': {'over': True}},
                             {'id': 2, 'status': {'over': True}}]}
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
                'sessions': [{'id': 1, 'status': {'over': True}},
                             {'id': 2, 'status': {'over': True}}]}
        manager = Manager(bank='alu')
        manager.bank.bank = data
        with self.assertRaises(SystemExit):
            manager.get_session_from_id(None)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getpendingsessions')
    def test_ManagerGetPendingSessionsOK(self):
        """Check method returns correct pending session"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        expected = {54: now, 55: now + 1}
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
        """Check method returns correct pending session"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        expected = {54: now, 55: now + 1}
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
    @attr('manager.currentrelease')
    def test_ManagerGetCurrentRelease_CurrentSet(self):
        """Check correct release is returned"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager._current_release = str(54)
        self.assertEqual(str(54), manager.current_release())

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

# These tests are switched off because current_release only search for 'current' tag in Mongo
#    @attr('manager')
#    @attr('manager.currentrelease')
#    def test_ManagerGetCurrentRelease_ProductionRemoteRelease(self):
#        """Check we get the right current release"""
#        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
#        now = time.time()
#        release = 'R54'
#        data = {'name': 'alu',
#                'production': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'remoterelease': release}]
#                }
#        manager = Manager(bank='alu')
#        manager.bank.bank = data
#        self.assertEqual(release, manager.current_release())
#        self.utils.drop_db()

#    @attr('manager')
#    @attr('manager.currentrelease')
#    def test_ManagerGetCurrentRelease_ProductionRelease(self):
#        """Check we get the right current release"""
#        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
#        now = time.time()
#        release = 'R54'
#        data = {'name': 'alu',
#                'production': [{'id': 1, 'remoterelease': 'R1'}, {'id': now, 'release': release}]
#                }
#        manager = Manager(bank='alu')
#        manager.bank.bank = data
#        self.assertEqual(release, manager.current_release())
#        self.utils.drop_db()

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
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDir_Raises(self):
        """Check method raises "Can't get current production directory: 'current_release' ..."""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        with self.assertRaises(SystemExit):
            manager.get_current_proddir()

    @attr('manager')
    @attr('manager.currentproddir')
    def test_ManagerGetCurrentProdDir_RaisesNoCurrentRelease(self):
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
    def test_ManagerGetCurrentProdDir_OK(self):
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
    def test_ManagerGetCurrentProdDir_RaisesNoProd(self):
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
        os.environ["BIOMAJ_CONF"] = back_cfg
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
        """Check get_bank_packages() is ok"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        packs = ['pack@blast@2.2.26', 'pack@fasta@3.6']
        bank_packs = manager.get_bank_packages()
        self.assertListEqual(packs, bank_packs)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.getbankpackages')
    def test_ManagerGetBankPackagesNoneOK(self):
        """Check get_bank_packages() is ok"""
        self.utils.copy_file(ofile='minium.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='minium')
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
        """Check bank has status deprecated"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check bank not published yet (first run) has status unpublished"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 100})
        del manager.bank.bank['current']
        history = manager.history()
        self.assertEqual(history[0]['status'], 'unpublished')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.history')
    def test_ManagerHistorySessionsHistoryANDStatusDeletedOK(self):
        """Check bank has status deleted"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check when no 'production' field in bank, history raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'] = None
        with self.assertRaises(SystemExit):
            manager.mongo_history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryNoSessionsRaisesError(self):
        """Check when no 'sessions' field in bank, history raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12})
        manager.bank.bank['sessions'] = None
        with self.assertRaises(SystemExit):
            manager.mongo_history()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistoryCheckIDSessionsOK(self):
        """Check bank has right session id"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check bank has status deprecated"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check bank not published yet (first run) has status unpublished"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.bank.bank['production'].append({'session': 100, 'release': 12, 'prod_dir': "/tmp", 'dir_version': "alu",
                                                'remoterelease': 12, 'freeze': False, 'data_dir': "/tmp"})
        manager.bank.bank['sessions'].append({'id': 100, 'remoterelease': 12})
        del manager.bank.bank['current']
        history = manager.mongo_history()
        self.assertEqual(history[0]['status'], 'unpublished')
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.mongohistory')
    def test_ManagerMongoHistorySessionsHistoryANDStatusDeletedOK(self):
        """Check bank has status deleted"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        os.chmod(outputfile, 0000)
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

        self.assertEqual(manager.save_banks_version(), 0)
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
        line = Manager.SAVE_BANK_LINE_PATTERN % ('alu', "Release " + '54', Utils.time2datefmt(now, Manager.DATE_FMT),
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
        self.assertEqual(manager.save_banks_version(), 0)
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
    def test_ManagerNextReleaseThrowsNoSessions(self):
        """Check method throws an exception if no 'sessions'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        del manager.bank.bank['sessions']
        with self.assertRaises(SystemExit):
            manager.next_release()
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.nextrelease')
    def test_ManagerNextReleasePassesContinue(self):
        """Check method continue when session['id'] == 'current'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55', 'status': {'over': True}})
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '56', 'status': {'over': True}})
        self.assertEqual('55', manager.next_release())
        self.utils.drop_db()

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
        self.assertFalse(Manager.set_simulate(""))

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankIsLocked(self):
        """Check manager.can_switch returns False because bank is locked"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        manager.set_verbose(True)
        lock_file = os.path.join(manager.bank.config.get('lock.dir'), manager.bank.name + '.lock')
        with open(lock_file, 'a'):
            self.assertFalse(manager.can_switch())
        os.remove(lock_file)
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdate_CannotSwitch(self):
        """Check method returns empty dict because bank cannot switch"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # setting current to None means no current bank published.
        manager.bank.bank['current'] = None
        returned = manager.show_need_update()
        self.assertDictEqual(returned, {})

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdate_CanSwitchOneBank(self):
        """Check method returns dict because bank can switch"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        # We created these 2 managers to set 2 banks in db
        alu = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        # setting current to None means no current bank published.
        alu.bank.bank['current'] = now
        alu.bank.bank['last_update_session'] = now + 1
        alu.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        alu.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55', 'status': {'over': True}})
        returned = alu.show_need_update()
        self.assertDictEqual(returned, {'alu': {'current_release': '54', 'next_release': '55'}})

    @attr('manager')
    @attr('manager.showneedupdate')
    def test_ManagerShowNeedUpdate_CanSwitchTwoBank(self):
        """Check method returns dict because bank can switch"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        self.utils.copy_file(ofile='minium.properties', todir=self.utils.conf_dir)
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
        """Check manager.can_switch returns False because bank not published yet"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['current'] = None
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankUpdateNotReady(self):
        """Check manager.can_switch returns False because last session failed"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        # We set 'current' field to avoid to return False with 'bank_is_published'
        now = time.time()
        manager.set_verbose(True)
        # To be sure we set 'current' from MongoDB to null
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now
        self.assertFalse(manager.can_switch())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.switch')
    def test_ManagerBankSwitch_BankLastSessionFailed(self):
        """Check manager.can_switch returns False because last session failed"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check manager.can_switch returns True"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
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
        """Check the method raises exception"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        manager = Manager(bank='alu')
        #with self.assertRaises(SystemExit):
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithCurrentTrue(self):
        """Check the method returns True"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        manager.bank.bank['current'] = now
        manager.bank.bank['last_update_session'] = now + 1
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
    def test_ManagerBankUpdateReadyWithProductionTrue(self):
        """Check the method returns False searching for production"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del manager.bank.bank['current']
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['production'].append({'session': now})
        self.assertTrue(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithStatusTrue(self):
        """Check the method returns using 'status'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del manager.bank.bank['current']
        manager.bank.bank['last_update_session'] = now
        if 'status' not in manager.bank.bank:
            manager.bank.bank['status'] = {'over': True}
        self.assertTrue(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithStatusFalse(self):
        """Check the method returns using 'status'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del manager.bank.bank['current']
        manager.bank.bank['last_update_session'] = now
        if 'status' not in manager.bank.bank:
            manager.bank.bank['status'] = {'over': False}
        self.assertFalse(manager.update_ready())
        self.utils.drop_db()

    @attr('manager')
    @attr('manager.updateready')
    def test_ManagerBankUpdateReadyWithSessionsTrue(self):
        """Check the method returns using 'sessions'"""
        self.utils.copy_file(ofile='alu.properties', todir=self.utils.conf_dir)
        now = time.time()
        manager = Manager(bank='alu')
        del manager.bank.bank['current']
        manager.bank.bank['last_update_session'] = now
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55',
                                              'status': {'over': True}})
        self.assertTrue(manager.update_ready())
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
        manager.bank.bank['sessions'].append({'id': now, 'remoterelease': '54'})
        manager.bank.bank['sessions'].append({'id': now + 1, 'remoterelease': '55',
                                              'status': {'over': False}})
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
            manager.stop_running_jobs(args="NOT A LIST FOR ARGS")
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
            manager._run_command(exe='chmod', args=['-x', '/bin/ls'], quiet=True)

    @attr('manager')
    @attr('manager.command')
    def test_ManagerRunCommandErrorCantRunCommand(self):
        """Check method throws error command does not exist"""
        manager = Manager()
        with self.assertRaises(SystemExit):
            manager._run_command(exe='/bin/nobin', args=['/tmp'], quiet=True)


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
