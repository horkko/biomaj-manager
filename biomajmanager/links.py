"""Automatically create symbolic links from bank data dir to defined target"""
from __future__ import print_function
from biomajmanager.utils import Utils
from biomajmanager.manager import Manager
import os

__author__ = 'tuco'


class Links(object):

    """Class to manager symbolic links for a bank based on supported formats"""

    def __init__(self, manager=None):
        """
        Init class

        :param manager: Biomaj Manager instance
        :return:
        """
        self.source = None
        self.target = None

        if not manager:
            Utils.error("A manager is required")
        if not isinstance(manager, Manager):
            Utils.error("A Manager instance is required")
        self.manager = manager
        try:
            self.curr_bank_dir = self.manager.get_current_proddir()
        except SystemExit:
            Utils.error("Can't create Links instance: Can't get production dir for bank")
        self.created_links = 0

    def add_link(self, inc=1):
        """
        Increase link created number

        :param inc: Incremental value, default 1
        :type inc: Integer
        :return: Number of links "virtually" created
        :rtype: Int
        """
        self.created_links += inc
        return self.created_links

    def check_links(self):
        """
        Check if some link(s) need to be (re)created. It uses do_links and set
        simulate and verbose mode to True

        :return: Number of links "virtually" created
        :rtype: Int
        """
        Manager.set_simulate(True)
        Manager.set_verbose(False)
        self.do_links()
        return self.created_links

    def do_links(self, dirs=None, files=None):
        """
        Create a list of links (Hard coded)

        :TODO: Find a solution to make the list of link(s) configurable
        :param dirs: Directory to symlink
        :type dirs: Dict {'source1': ['target1', 'target2', ...], 'source2': [], ...}
        :param files: Files to symlink
        :type links: Dict {'source1': ['target1','target2', ...], 'source2': [], ...},
        :return: Number of created links
        :rtype: Integer
        """
        props = self.manager.bank.get_properties()
        admin = None
        if 'owner' in props and props['owner']:
            admin = props['owner']
        if Utils.user() != admin:
            Utils.error("[%s] You are not allowed to create link(s)" % Utils.user())

        # Our default internal use
        if dirs is None:
            dirs = {
                'bowtie': ['index/bowtie'], 'bwa': ['index/bwa'], 'gatk': ['index/gatk'], 'picard': ['index/picard'],
                'samtools': ['index/samtools'], 'fusioncatcher': ['index/fusioncatcher'], 'soap': ['index/soap'],
                'blast2': ['index/blast2'], 'blast+': ['index/blast+'], 'flat': ['ftp'], 'uncompressed': ['release']
            }
        if files is None:
            files = {
                'golden': ['index/golden'], 'uncompressed': ['index/golden'], 'blast2': ['fasta', 'index/blast2'],
                'hmmer': ['index/hmmer'], 'fasta': ['fasta'], 'bdb': ['index/bdb']
            }
        # for source, targets in dirs.iteritems():
        #     for target in targets:
        #         self._generate_dir_link(source=source, target=target)
        # for source, targets in files.iteritems():
        #     for target in targets:
        #         self._generate_files_link(source=source, target=target)
        self._generate_dir_link(source='bowtie', target='index/bowtie')
        self._generate_dir_link(source='bwa', target='index/bwa')
        self._generate_dir_link(source='gatk', target='index/gatk')
        self._generate_dir_link(source='picard', target='index/picard')
        self._generate_dir_link(source='samtools', target='index/samtools')
        self._generate_dir_link(source='fusioncatcher', target='index/fusioncatcher')
        self._generate_dir_link(source='soap', target='index/soap')
        self._generate_dir_link(source='blast2', target='index/blast2')
        self._generate_dir_link(source='blast+', target='index/blast+')
        # Ftp
        self._generate_dir_link(source='flat', target='ftp')
        # Release
        self._generate_dir_link(source='uncompressed', target='release', fallback='flat')
        # Golden
        self._generate_files_link(source='golden', target='index/golden')
        self._generate_files_link(source='uncompressed', target='index/golden')
        self._generate_files_link(source='blast2', target='fasta')
        self._generate_files_link(source='blast2', target='index/blast2')
        self._generate_files_link(source='hmmer', target='index/hmmer')
        self._generate_files_link(source='fasta', target='fasta', remove_ext=True)
        self._generate_files_link(source='bdb', target='index/bdb', no_ext=True)
        return self.created_links


    def _generate_dir_link(self, source=None, target=None, hard=False, fallback=None, msg=None):
        """
        Create a symbolic link between 'source' and 'target' for a directory

        :param source: Source directory to link
        :type source: String
        :param target: Destination directory name (relative to config param 'production.dir')
        :type target: String
        :param hard: Create hard link instead of symlink
        :type hard: Boolean (default False)
        :param fallback: Alternative source if source does not exist
        :type fallback: String
        :param msg: Message to display at the end of the function call (simulate mode)
        :type msg: String
        :return: Number of link(s) created
        :rtype: Integer
        """
        if self._prepare_links(source=source, target=target, fallback=fallback):
            return 0

        # Final link name
        slink = os.path.join(self.source)
        tlink = os.path.join(self.target, self.manager.bank.name)

        self._make_links(links=[(slink, tlink)], hard=hard)

        if Manager.get_simulate():
            if msg:
                print(msg)
            else:
                if Manager.get_verbose():
                    print("%s -> %s directory link done" % (self.target, self.source))
        return self.created_links

    def _generate_files_link(self, source=None, target=None, msg=None, remove_ext=False, no_ext=False):
        """
        Links list of file from 'source' to 'target' directory

        :param source: Source directory to link
        :type source: String
        :param target: Destination directory name (relative to config param 'production_dir')
        :type target: String
        :param remove_ext: Create another link of the file without the file name extension
        :type remove_ext: Boolean (default False)
        :param no_ext: Create link only without file name extension
        :type no_ext: Boolean (default False)
        :param msg: Message to display at the end of the function call (simulate mode)
        :type msg: String
        :return: Number of link(s) created
        :rtype: Integer
        """
        if self._prepare_links(source=source, target=target, use_deepest=True):
            return 0

        # Get files in the source directory
        files = Utils.get_files(self.source)
        links = []

        for ffile in files:
            # Source file link
            slink = os.path.join(self.source, ffile)
            if not no_ext:
                tlink = os.path.join(self.target, ffile)
                links.append((slink, tlink))
                if Manager.get_verbose():
                    print("[_generate_files_link] [no_ext=%s] append slink %s" % (str(no_ext), slink))
                    print("[_generate_files_link] [no_ext=%s] append tlink %s" % (str(no_ext), tlink))

            # If asked to create another symbolic link without extension name
            if remove_ext or no_ext:
                new_file = os.path.splitext(os.path.basename(ffile))[0]
                tlink = os.path.join(self.target, new_file)
                links.append((slink, tlink))
                if Manager.get_verbose():
                    print("[_generate_files_link] [rm_ext=%s] [no_ext=%s] append slink %s" % (str(remove_ext), str(no_ext), slink))
                    print("[_generate_files_link] [rm_ext=%s] [no_ext=%s] append tlink %s" % (str(remove_ext), str(no_ext), tlink))

        self._make_links(links=links)

        if Manager.simulate:
            if msg:
                print(msg)
            else:
                if Manager.get_verbose():
                    print("%s -> %s file link done" % (self.target, self.source))
        return self.created_links

    def _make_links(self, links=None, hard=False):
        """
        Try to create the links (symbolic or hard)

        :param links:
        :type links: List of links to create
        :param hard: Create hard link
        :type hard: Boolean
        :return: Number of created link(s)
        :rtype: Integer
        """
        if not links or not len(links):
            return 0

        for slink, tlink in links:
            if not os.path.exists(tlink) and not os.path.islink(tlink):
                if Manager.get_simulate() and Manager.get_verbose():
                    print("Linking %s -> %s" % (tlink, os.path.relpath(slink, start=self.target)))
                else:
                    try:
                        if not Manager.get_simulate():
                            source_link = os.path.relpath(slink, start=self.target)
                            if hard:
                                os.link(source_link, tlink)
                            else:
                                os.symlink(source_link, tlink)
                    except OSError as err:
                        Utils.error("[%s] Can't create %slink %s: %s" %(self.manager.bank.name, 'hard ' if hard else 'sym', tlink, str(err)))
                    self.add_link()
        return self.created_links

    def _prepare_links(self, source=None, target=None, use_deepest=False, fallback=None):
        """
        Prepare stuff to create links

        :param source: Source path
        :type source: String
        :param target: Destination path
        :type target: String
        :param use_deepest: Try to find deepest directory from source
        :type use_deepest: Boolean
        :param fallback: Alternative source if source does not exist
        :type fallback: String
        :return: 0/1
        """
        if not source:
            Utils.error("source required")
        if not target:
            Utils.error("target required")
        if not self.manager.config.has_option('GENERAL', 'data.dir'):
            Utils.error("'data.dir' not defined in global.properties or bank.properties")
        if not self.manager.config.has_option('MANAGER', 'production.dir'):
            Utils.error("'production.dir' not defined in manager.properties.")

        bank_name = self.manager.bank.name
        current_release = self.manager.current_release()
        data_dir = os.path.join(self.manager.config.get('GENERAL', 'data.dir'), bank_name, 'alu_' + current_release)
        target_dir = self.manager.config.get('MANAGER', 'production.dir')
        source = os.path.join(data_dir, source)

        if not os.path.isdir(source) and fallback is None:
            Utils.warn("[%s] %s does not exist" % (bank_name, source))
            return 1
        elif fallback:
            print("[%s] Source %s not found\nFallback to %s" % (bank_name, source, fallback))
            source = os.path.join(data_dir, fallback)

        if use_deepest:
            source = Utils.get_deepest_dir(source, full=use_deepest)
        target = os.path.join(target_dir, target)

        # Check destination directory where to create link(s)
        if not os.path.exists(target) and not os.path.isdir(target):
            if Manager.get_simulate() and Manager.get_verbose():
                print("[%s] Creating directory %s" % (bank_name, target))
            else:
                try:
                    if not Manager.get_simulate():
                        os.makedirs(target)
                except OSError as err:
                    Utils.error("[%s] Can't create %s dir: %s" % (bank_name, target, str(err)))

        self.source = source
        self.target = target
        if Manager.verbose:
            print("[prepare_links] source %s" % self.source)
            print("[prepare_links] target %s" % self.target)
        return 0
