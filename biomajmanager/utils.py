from __future__ import print_function
import os
import sys
from time import time
# from biomajmanager.manager import Manager

class Utils(object):

    timer_start = timer_stop = 0.0

    @staticmethod
    def elapsed_time():
        '''
        Get the elapsed time between start and stop timer
        Stop timer call is not required. If not set, it is automatically called
        as soon as thie method is called
        :return: Time
        :rtype: float
        '''
        if Utils.timer_start:
            if not Utils.timer_stop:
                Utils.stop_timer()
            etime = Utils.timer_stop - Utils.timer_start
            Utils.reset_timer()
            return etime
        Utils.error("Missing timer value (start/stop")

    @staticmethod
    def error(msg):
        print('[ERROR] ' + msg, file=sys.stderr)
        sys.exit(1)

    @staticmethod
    def get_files(path=None):
        """
        Return the list of file(s) found for a given path
        :param path: Path to search from
        :type path: String
        :return: List of file(s) found
        :rtype: List
        """
        if not path or not os.path.isdir(path):
            Utils.error("Path not found: %s" % path)
        return os.listdir(path)

    @staticmethod
    def get_deepest_dirs(path=None, full=False):
        """
        Get the last directories from a path
        :param path: Path to start from
        :type path: String
        :param full: Get the full path otherwise the directory only
        :type full: Boolean
        :return: List of directories
        :rtype: List
        """
        if not os.path.exists(path) and os.path.isdir(path):
            Utils.error("%s does not exists" % path)

        dirs = []
        for dirpath, dirnames, filenames in os.walk(path):
            if len(dirnames) == 0:
                if full:
                    dirs.append(dirpath)
                else:
                    dirs.append(os.path.basename(dirpath))
        return dirs

    @staticmethod
    def get_deepest_dir(path=None, full=False):
        """
        Return only one deepest dir from the path
        :param path: Path
        :type path: String
        :param full: Return complete path
        :type full: Boolean
        :return: Director name
        :rtype: String
        """
        dirs = Utils.get_deepest_dirs(path, full=full)
        if len(dirs) > 1:
            Utils.warn("More than one deepest dir found at %s: Only first returned" % path)
        return dirs[0]

    @staticmethod
    def ok(msg):
        """
        Print a [OK] msg
        :param msg: Message to print
        :type msg: String
        :return:
        """
        print("[OK] %s" % msg)

    @staticmethod
    def reset_timer():
        '''

        :return:
        '''
        Utils.timer_start = 0.0
        Utils.timer_stop = 0.0

    @staticmethod
    def start_timer():
        '''

        :return:
        '''
        Utils.timer_start = time()

    @staticmethod
    def stop_timer():
        '''

        :return:
        '''
        Utils.timer_stop = time()

    @staticmethod
    def title(msg):
        '''
        Prints a small title banner (message + underlined message)
        :param msg:
        :return:
        '''
        title = "* " + msg + " *"
        print(title)
        print('-' * len(title))

    @staticmethod
    def user():
        '''
        Return the current user running or using the script. Taken from os.env
        :return: User name
        :rtype: String
        '''
        return os.getenv('USER')

    # @staticmethod
    # def verbose(msg):
    #     #if Manager.verbose:
    #     print('[VERBOSE] %s' % msg, file=sys.stdout)

    @staticmethod
    def warn(msg):
        print('[WARNING] ' + msg, file=sys.stderr)

    @staticmethod
    def verbose(msg):
        from .manager import Manager
        if Manager.verbose:
            print('[VERBOSE] ' + msg, file=sys.stdout)
