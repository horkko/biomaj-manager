"""Automatically create symbolic links from bank data dir to defined target"""
from biomajmanager.utils import Utils
from biomajmanager.manager import Manager
import os

__author__ = 'tuco'


class Links(object):

    """Class to manager symbolic links for a bank based on supported formats"""
    DIRS = {
        'bowtie': [{'target': 'index/bowtie'}], 'bwa': [{'target': 'index/bwa'}],
        'gatk': [{'target': 'index/gatk'}], 'picard': [{'target': 'index/picard'}],
        'liftover': [{'target': 'index/liftover'}],
        'samtools': [{'target': 'index/samtools'}], 'fusioncatcher': [{'target': 'index/fusioncatcher'}],
        'golden': [{'target': 'index/golden'}], 'soap': [{'target': 'index/soap'}],
        'blast+': [{'target': 'index/blast+'}], 'flat': [{'target': 'ftp'}],
        'uncompressed': [{'target': 'release', 'fallback': 'flat'},
                         {'target': 'index/golden', 'requires': 'golden'}],
        }
    # This creates a clone of the source directory (files and subdirs) into target
    CLONE_DIRS = {'index': [{'source': 'bowtie'}, {'source': 'bwa'}, {'source': 'gatk'}, {'source': 'picard'},
                            {'source': 'samtools'}, {'source': 'fusioncatcher'}, {'source': 'golden'},
                            {'source': 'soap'}, {'source': 'blast2'}, {'source': 'blast+'}, {'source': 'hmmer'},
                            {'source': 'bdb', 'remove_ext': True}],
                  # 'fasta': [{'source': 'blast2', 'remove_ext': True}, {'source': 'fasta', 'remove_ext': True}]
                  }

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
        self.bank_name = self.manager.bank.name

        if not self.manager.config.has_option('GENERAL', 'data.dir'):
            Utils.error("'data.dir' not defined in global.properties or bank.properties")
        if not self.manager.config.has_option('MANAGER', 'production.dir'):
            Utils.error("'production.dir' not defined in manager.properties.")
        self.prod_dir = self.manager.config.get('MANAGER', 'production.dir')

        current_release = self.manager.current_release()
        if current_release is None:
            Utils.error("Can't determine current release for bank %s" % self.bank_name)
        # Get the 'current'
        bank_data_dir = self.manager.get_current_link()
        self.bank_data_dir = bank_data_dir
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

    def check_links(self, **kwargs):
        """
        Check if some link(s) need to be (re)created.

        It uses :py:func:`do_links` and set simulate and verbose mode to True

        :return: Number of links "virtually" created
        :rtype: int
        """
        Manager.set_simulate(True)
        Manager.set_verbose(False)
        self.do_links(**kwargs)
        return self.created_links

    def do_links(self, dirs=None, files=None, clone_dirs=None):
        """
        Create a list of links

        :param dirs: Directory to symlink
        :type dirs: dict {'source1': ['target1', 'target2', ...], 'source2': [], ...}
        :param files: Files to symlink
        :type files: dict {'source1': ['target1','target2', ...], 'source2': [], ...},
        :param clone_dirs: Directory to clone
        :type clone_dirs: dict
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
            dirs = Links.DIRS
        # EXPERIMENTAL AS OF 12 May 2016, New Structure for BioMAJ Links
        if clone_dirs is None:
            clone_dirs = Links.CLONE_DIRS
        if files is None:
            files = {
                'golden': [{'target': 'index/golden'}],
                'blast2': [{'target': 'fasta'}, {'target': 'index/blast2'}],
                'hmmer': [{'target': 'index/hmmer'}],
                'fasta': [{'target': 'fasta', 'remove_ext': True}],
                'bdb': [{'target': 'index/bdb', 'remove_ext': True}]
            }

        for target, sources in list(clone_dirs.items()):
            for source in sources:
                self._clone_structure(target=target, **source)

        for source, targets in list(dirs.items()):
            for target in targets:
                self._generate_dir_link(source=source, **target)

        for source, targets in list(files.items()):
            for target in targets:
                self._generate_files_link(source=source, **target)

        return self.created_links

    def _check_source_target_parameters(self, source=None, target=None):
        """
        Check all parameters are set and ok to prepare link building

        :param source: Source path
        :type source: str
        :param target: Destination path
        :type target: str
        :return: True if all is ok, throws otherwise
        :rtype: bool
        :raises SystemExit: If 'source' or 'target' are None
        :raises SystemExit: If 'data.dir' not set in :py:data:`global.properties`
        :raises SystemExit: If 'production.dir' not set in :py:data:`manager.properties`
        """
        if not source:
            Utils.error("source required")
        if not target:
            Utils.error("target required")
        return True

    def _clone_structure(self, source=None, target=None, remove_ext=False):
        """
        Create a directory structure from a source to a target point and link all files from source inside target

        :param source: Source directory to clone
        :type source: str
        :param target: Destination directory to create if does not exist
        :type target: str
        :param remove_ext: Create another link of the file without the file name extension
        :type remove_ext: bool
        :return: True if structure cloning build OK, throws otherwise
        :rtype: bool
        :raise SystemExit: If error occurred during directory structure building
        """
        self._check_source_target_parameters(source=source, target=target)
        # Check do_links.clone_dirs. As we want to recreate the same architecture as for the source,
        # we need to recreate the target because Utils.get_subtree removes the source path which contains
        # the target name
        target = os.path.join(target, source)
        source = os.path.join(self.bank_data_dir, source)
        subtrees = Utils.get_subtree(path=source)
        try:
            for subtree in subtrees:
                end_target = os.path.join(self.prod_dir, target, subtree)
                if not os.path.exists(end_target) and not os.path.isdir(end_target):
                    if Manager.get_simulate() and Manager.get_verbose():
                        Utils.verbose("[%s] Creating directory %s" % (self.bank_name, end_target))
                    else:
                        if not Manager.get_simulate():
                            os.makedirs(end_target)

                sub_files = Utils.get_files(path=os.path.join(source, subtree))
                if len(sub_files) == 0:
                    continue

                links = []
                for ffile in sub_files:
                    # Source file link
                    slink = os.path.join(source, subtree, ffile)
                    tlink = os.path.join(end_target, ffile)
                    links.append((slink, tlink))
                    if Manager.get_verbose():
                        Utils.verbose("[_generate_files_link] append slink %s" % slink)
                        Utils.verbose("[_generate_files_link] append tlink %s" % tlink)
                        # If asked to create another symbolic link without extension name
                    if remove_ext:
                        new_file = os.path.splitext(os.path.basename(ffile))[0]
                        tlink = os.path.join(end_target, new_file)
                        links.append((slink, tlink))
                        if Manager.get_verbose():
                            Utils.verbose("[_generate_files_link] [rm_ext=%s] append slink %s"
                                          % (str(remove_ext), slink))
                            Utils.verbose("[_generate_files_link] [rm_ext=%s] append tlink %s"
                                          % (str(remove_ext), tlink))
                # Set self.target for _make_links
                self.target = end_target
                self._make_links(links=links)
        except OSError as err:
            Utils.error("[%s] Can't create %s dir: %s (%s)" % (self.bank_name, end_target, str(err),
                                                               os.access(end_target, os.W_OK)))

        return True

    def _generate_dir_link(self, source=None, target=None, hard=False, fallback=None, requires=None):
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
        :param requires: A required directory
        :type requires: str
        :return: Number of created link(s)
        :rtype: int
        """
        if not self._prepare_links(source=source, target=target, fallback=fallback,
                                   requires=requires, get_deepest=True):
            return 0

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
        if not self._prepare_links(source=source, target=target, get_deepest=True):
            return 0

        # Get files in the source directory
        files = Utils.get_files(path=self.source)
        links = []

        for ffile in files:
            # Source file link
            slink = os.path.join(self.source, ffile)
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

    def _prepare_links(self, source=None, target=None, get_deepest=False, fallback=None, requires=None):
        """
        Prepare stuff to create links

        :param source: Source path
        :type source: str
        :param target: Destination path
        :type target: str
        :param get_deepest: Try to find deepest directory(ies) from source
        :type get_deepest: bool
        :param fallback: Alternative source if source does not exist
        :type fallback: str
        :param requires: A required file or directory
        :type requires: str
        :return: Boolean
        :rtype: bool
        :raises SystemExit: If 'source' or 'target' are None
        :raises SystemExit: If 'data.dir' not set in :py:data:`global.properties`
        :raises SystemExit: If 'production.dir' not set in :py:data:`manager.properties`
        :raises SystemExit: If 'target' directory cannot be created
        """
        self._check_source_target_parameters(source=source, target=target)
        data_dir = self.bank_data_dir
        source = os.path.join(data_dir, source)
        target_dir = self.manager.config.get('MANAGER', 'production.dir')
        bank_name = self.manager.bank.name

        if requires is not None:
            if not os.path.exists(os.path.join(data_dir, requires)):
                Utils.warn("[%s] Can't create %s, requires param %s not here." % (bank_name, source, requires))
                return False

        if not os.path.isdir(source):
            if fallback is None:
                if self.manager.get_verbose():
                    Utils.warn("[%s] %s does not exist" % (bank_name, source))
                return False
            else:
                if self.manager.get_verbose():
                    Utils.verbose("[%s] %s does not exist. Fallback to %s" % (bank_name, source, fallback))
                source = os.path.join(data_dir, fallback)
                if not os.path.isdir(source):
                    if self.manager.get_verbose():
                        Utils.warn("[%s] Fallback %s does not exist" % (bank_name, source))
                        return False

        if get_deepest:
            source = Utils.get_deepest_dir(source, full=get_deepest)
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
        if Manager.get_verbose():
            Utils.verbose("[prepare_links] source %s" % self.source)
            Utils.verbose("[prepare_links] target %s" % self.target)
        return True
