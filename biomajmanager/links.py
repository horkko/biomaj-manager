from __future__ import print_function
from biomajmanager.utils import Utils
from biomajmanager.manager import Manager
import os
__author__ = 'tuco'



class Links(object):
    '''

    '''

    def __init__(self, manager=None):
        '''

        :param manager: Biomaj Manager instance
        :return:
        '''

        self.source = None
        self.target = None

        if not manager:
            Utils.error("A manager is required")
        self.manager = manager
        if not isinstance(self.manager, Manager):
            Utils.error("A biomajmanager.manager.Manager instance is required")

        self.curr_bank_dir = self.manager.get_current_proddir()
        self.created_links = 0

    def add_link(self, inc=1):
        '''

        :param inc: Incremental value, default 1
        :type inc: Integer
        :return:
        '''

        self.created_links += inc
        return

    def do_links(self):
        '''
        :return: Number of created links
        :rtype: Integer
        '''

        props = self.manager.bank.get_properties()
        if 'owner' in props and props['owner']:
            admin = props['owner']
        if Utils.user() != admin:
            Utils.error("[%s] You are not allowd to create link(s)" % Utils.user())

        self._generate_dir_link('bowtie', 'index/bowtie')
        self._generate_dir_link('bwa', 'index/bwa')
        self._generate_dir_link('gatk', 'index/gatk')
        self._generate_dir_link('picard', 'index/picard')
        self._generate_dir_link('samtools', 'index/samtools')
        self._generate_dir_link('bowtie', 'index/bowtie')
        self._generate_dir_link('fusioncatcher', 'index/fustioncatcher')
        self._generate_dir_link('soap', 'index/soap')
        self._generate_dir_link('blast2', 'index/blast2')
        self._generate_dir_link('blast+', 'index/blast+')
        self._generate_files_link('blast2', 'fasta')
        self._generate_files_link('blast2', 'index/blast2')
        self._generate_files_link('hmmer', 'index/hmmer')
        #self._link_fata()
        self._generate_files_link('fasta', 'fasta', remove_ext=True)
        self._link_golden()
        self._link_ftp()
        self._link_release()
        self._link_taxodb()
        return self.created_links


    def _generate_dir_link(self, from_dir=None, to_dir=None, msg=None):
        '''
        Create a symbolink link between 'from_dir' and 'to_dir' for a directory
        :param from_dir: Source directory to link
        :type from_dir: String
        :param to_dir: Destination directory name (relative to config param 'production_dir')
        :type to_dir: String
        :param msg: Message to display at the end of the function call (simulate mode)
        :type msg: String
        :return: Number of link(s) created
        :rtype: Integer
        '''
        if not from_dir:
            Utils.error("'from_dir' required")
        if not to_dir:
            Utils.errors("'to_dir' is required")

        bank_name = self.manager.bank.name
        from_dir = os.path.join(self.manager.bank.config.get('data.dir'),
                                bank_name,
                                self.manager.current_release(),
                                from_dir)
        if not os.path.isdir(from_dir):
            Utils.warn("[%s] %s does not exists" % (bank_name, from_dir))
            return 0

        to_dir = os.path.join(self.manager.bank.config.get('production_dir', section='MANAGER'),
                              to_dir)
        # Check destination directory where to create link(s)
        if not os.path.exists(to_dir) and not os.path.isdir(to_dir):
            if self.manager.simulate:
                print("[%s] Creating directory %s" % (bank_name, to_dir))
            else:
                try:
                    os.mkdir(to_dir)
                except OSError as err:
                    Utils.error("[%s] Can't create symlink: %s" % (bank_name, str(err)))

        # Final link name
        link = os.path.join(to_dir, bank_name)
        if not os.path.exists(link) and not os.path.islink(link):
            if self.manager.simulate:
                print("Linking %s -> %s" % (link, os.path.relpath(from_dir, start=to_dir)))
            else:
                try:
                    os.symlink(os.path.relpath(from_dir, start=to_dir), link)
                    self.add_link()
                except OSError as err:
                    Utils.error("[%s] Can't create symlink: %s" % (bank_name, str(err)))

        if self.manager.simulate:
            if msg:
                print(msg)
            else:
                print("%s -> %s directory link done" % (to_dir, from_dir))
        return self.created_links

    def _generate_files_link(self, from_dir=None, to_dir=None, msg=None, remove_ext=None):
        '''
        Links list of file from 'from_dir' to 'to_dir' directory
        :param from_dir: Source directory to link
        :type from_dir: String
        :param to_dir: Destination directory name (relative to config param 'production_dir')
        :type to_dir: String
        :param msg: Message to display at the end of the function call (simulate mode)
        :type msg: String
        :return: Number of link(s) created
        :rtype: Integer
        '''

        self._prepare_link(source=from_dir, target=to_dir)
        files = os.listdir(from_dir)
        self._make_links(files=files)
        links = []
        for file in files:
            link = os.path.join(to_dir, file)
            links.append(link)
            print(file)
            if remove_ext:
                new_file = os.path.splitext(os.path.basename(file))[0]
                link = os.path.join(to_dir, new_file)
                links.append(link)
            for link in links:
                if not os.path.exists(link) and not os.path.islink(link):
                    if self.manager.simulate:
                        print("Linking %s -> %s" % (link, os.path.relpath(from_dir, start=to_dir)))
                    else:
                        try:
                            os.symlink(os.path.relpath(from_dir, start=to_dir), link)
                            self.add_link()
                        except OSError as err:
                            Utils.error("[%s] Can't create symlink: %s" % (bank_name, str(err)))
        if self.manager.simulate:
            if msg:
                print(msg)
            else:
                print("%s -> %s file link done" % (to_dir, from_dir))
        return self.created_links

    def _prepare_link(self, source=None, target=None):
        """
        Prepare stuff to create links
        :param source: Source path
        :param targer: Destincation path
        :return:
        """

        if not source:
            Utils.error("source required")
        if not target:
            Utils.error("targer required")

        bank_name = self.manager.bank.name
        source = os.path.join(self.manager.bank.config.get('data.dir'),
                              bank_name,
                              self.manager.current_release(),
                              source)
        if not os.path.isdir(source):
            Utils.warn("[%s] %s does not exists" % (bank_name, source))
            return 0

        target = os.path.join(self.manager.bank.config.get('production_dir', section='MANAGER'),
                              target)

        # Check destination directory where to create link(s)
        if not os.path.exists(target) and not os.path.isdir(target):
            if self.manager.simulate:
                print("[%s] Creating directory %s" % (bank_name, target))
            else:
                try:
                    os.mkdir(target)
                except OSError as err:
                    Utils.error("[%s] Can't create symlink: %s" % (bank_name, str(err)))

        self.source = source
        self.target = target
