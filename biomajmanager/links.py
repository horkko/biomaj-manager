"""Automatically create symbolic links from bank data dir to defined target"""
from biomajmanager.utils import Utils
from biomajmanager.manager import Manager
import os

__author__ = 'tuco'


class Links(object):

    """Class to manager symbolic links for a bank based on supported formats"""

    def __init__(self, manager=None):
        """
        Init class

        :param manager: Manager instance
        :type manager: :class:`biomajmanager.manager.Manager`
        :raises SystemExit: If 'manager' not given
        :raises SystemExit: If 'manager' arg not an instance of :class:`biomajmanager.manager.Manager`
        :raises SystemExit: If current production dir can't be found for current bank
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
        :type inc: int
        :return: Number of links "virtually" created
        :rtype: int
        """
        self.created_links += inc
        return self.created_links

    def check_links(self):
        """
        Check if some link(s) need to be (re)created.

        It uses :py:func:`do_links` and set simulate and verbose mode to True

        :return: Number of links "virtually" created
        :rtype: int
        """
        Manager.set_simulate(True)
        Manager.set_verbose(False)
        self.do_links()
        return self.created_links

    def do_links(self, dirs=None, files=None):
        """
        Create a list of links

        :param dirs: Directory to symlink
        :type dirs: dict {'source1': ['target1', 'target2', ...], 'source2': [], ...}
        :param files: Files to symlink
        :type files: dict {'source1': ['target1','target2', ...], 'source2': [], ...},
        :return: Number of created links
        :rtype: int
        :raises SystemExit: If user noth allowed to create link, see :py:data:`global.properties:admin`
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
                'bowtie': [{'target': 'index/bowtie'}], 'bwa': [{'target': 'index/bwa'}],
                'gatk': [{'target': 'index/gatk'}], 'picard': [{'target': 'index/picard'}],
                'samtools': [{'target': 'index/samtools'}], 'fusioncatcher': [{'target': 'index/fusioncatcher'}],
                'golden': [{'target': 'index/golden'}], 'soap': [{'target': 'index/soap'}],
                'blast+': [{'target': 'index/blast+'}], 'flat': [{'target': 'ftp'}],
                'uncompressed': [{'target': 'release', 'fallback': 'flat'}],
            }
        if files is None:
            files = {
                'golden': [{'target': 'index/golden'}], 'uncompressed': [{'target': 'index/golden'}],
                'blast2': [{'target': 'fasta'}, {'target': 'index/blast2'}],
                'hmmer': [{'target': 'index/hmmer'}], 'fasta': [{'target': 'fasta', 'remove_ext': True}],
                'bdb': [{'target': 'index/bdb', 'remove_ext': True}]
            }
        for source, targets in list(dirs.items()):
            for target in targets:
                self._generate_dir_link(source=source, **target)
        for source, targets in list(files.items()):
            for target in targets:
                self._generate_files_link(source=source, **target)
        return self.created_links

    def _generate_dir_link(self, source=None, target=None, hard=False, fallback=None):
        """
        Create a symbolic link between 'source' and 'target' for a directory

        :param source: Source directory to link
        :type source: str
        :param target: Destination directory name (relative to config param 'production.dir')
        :type target: str
        :param hard: Create hard link instead of symlink
        :type hard: bool (default False)
        :param fallback: Alternative source if source does not exist
        :type fallback: str
        :return: Number of created link(s)
        :rtype: int
        """
        if not self._prepare_links(source=source, target=target, fallback=fallback):
            return 0

        # Final link name
        slink = os.path.join(self.source)
        tlink = os.path.join(self.target, self.manager.bank.name)

        self._make_links(links=[(slink, tlink)], hard=hard)

        if Manager.get_simulate() and Manager.get_verbose():
            Utils.verbose("%s -> %s directory link done" % (self.target, self.source))
        return self.created_links

    def _generate_files_link(self, source=None, target=None, remove_ext=False):
        """
        Links list of file from 'source' to 'target' directory.

        If remove_ext is set to True, then another link is created. This link is the same as the
        target link, without the file extension

        :param source: Source directory to link
        :type source: str
        :param target: Destination directory name (relative to config param 'production_dir')
        :type target: str
        :param remove_ext: Create another link of the file without the file name extension
        :type remove_ext: bool (default False)
        :return: Number of created link(s)
        :rtype: int
        """
        if not self._prepare_links(source=source, target=target, use_deepest=True):
            return 0

        # Get files in the source directory
        files = Utils.get_files(self.source)
        links = []

        for ffile in files:
            # Source file link
            slink = os.path.join(self.source, ffile)
            #if not no_ext:
            tlink = os.path.join(self.target, ffile)
            links.append((slink, tlink))
            if Manager.get_verbose():
                Utils.verbose("[_generate_files_link] append slink %s" % slink)
                Utils.verbose("[_generate_files_link] append tlink %s" % tlink)

            # If asked to create another symbolic link without extension name
            if remove_ext:
                new_file = os.path.splitext(os.path.basename(ffile))[0]
                tlink = os.path.join(self.target, new_file)
                links.append((slink, tlink))
                if Manager.get_verbose():
                    Utils.verbose("[_generate_files_link] [rm_ext=%s] append slink %s" % (str(remove_ext), slink))
                    Utils.verbose("[_generate_files_link] [rm_ext=%s] append tlink %s" % (str(remove_ext), tlink))

        self._make_links(links=links)

        if Manager.get_simulate() and Manager.get_verbose():
            Utils.verbose("%s -> %s file link done" % (self.target, self.source))
        return self.created_links

    def _make_links(self, links=None, hard=False):
        """
        Try to create the links (symbolic or hard)

        :param links: List of links to create
        :type links: list
        :param hard: Create hard link
        :type hard: boole
        :return: Number of created link(s)
        :rtype: int
        :raises SystemExit: If link(s) cannot be created
        """
        if not links or not len(links):
            return 0

        for slink, tlink in links:
            if not os.path.exists(tlink) and not os.path.islink(tlink):
                if Manager.get_simulate() and Manager.get_verbose():
                    Utils.verbose("Linking %s -> %s" % (tlink, os.path.relpath(slink, start=self.target)))
                else:
                    try:
                        if not Manager.get_simulate():
                            source_link = os.path.relpath(slink, start=self.target)
                            if hard:
                                os.link(source_link, tlink)
                            else:
                                os.symlink(source_link, tlink)
                    except OSError as err:
                        Utils.error("[%s] Can't create %slink %s: %s" %
                                    (self.manager.bank.name, 'hard ' if hard else 'sym', tlink, str(err)))
                    self.add_link()
        return self.created_links

    def _prepare_links(self, source=None, target=None, use_deepest=False, fallback=None):
        """
        Prepare stuff to create links

        :param source: Source path
        :type source: str
        :param target: Destination path
        :type target: str
        :param use_deepest: Try to find deepest directory from source
        :type use_deepest: bool
        :param fallback: Alternative source if source does not exist
        :type fallback: str
        :return: Boolean
        :rtype: bool
        :raises SystemExit: If 'source' or 'target' are None
        :raises SystemExit: If 'data.dir' not set in :py:data:`global.properties`
        :raises SystemExit: If 'production.dir' not set in :py:data:`manager.properties`
        :raises SystemExit: If 'target' directory cannot be created
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
        data_dir = os.path.join(self.manager.config.get('GENERAL', 'data.dir'), bank_name,
                                bank_name + '_' + current_release)
        target_dir = self.manager.config.get('MANAGER', 'production.dir')
        source = os.path.join(data_dir, source)

        if not os.path.isdir(source) and fallback is None:
            if self.manager.get_verbose():
                Utils.warn("[%s] %s does not exist" % (bank_name, source))
            return False
        elif fallback:
            if self.manager.get_verbose():
                Utils.verbose("[%s] Source %s not found\nFallback to %s" % (bank_name, source, fallback))
            source = os.path.join(data_dir, fallback)
            if not os.path.isdir(source):
                if self.manager.get_verbose():
                    Utils.warn("[%s] %s does not exist" % (bank_name, source))
                return False

        if use_deepest:
            source = Utils.get_deepest_dir(source, full=use_deepest)
        target = os.path.join(target_dir, target)

        # Check destination directory where to create link(s)
        if not os.path.exists(target) and not os.path.isdir(target):
            if Manager.get_simulate() and Manager.get_verbose():
                Utils.verbose("[%s] Creating directory %s" % (bank_name, target))
            else:
                try:
                    if not Manager.get_simulate():
                        os.makedirs(target)
                except OSError as err:
                    Utils.error("[%s] Can't create %s dir: %s" % (bank_name, target, str(err)))

        self.source = source
        self.target = target
        if Manager.verbose:
            Utils.verbose("[prepare_links] source %s" % self.source)
            Utils.verbose("[prepare_links] target %s" % self.target)
        return True
