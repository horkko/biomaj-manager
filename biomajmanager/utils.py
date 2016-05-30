"""Utilities class for BioMAJ Manager"""
from __future__ import print_function
import os
import sys
from time import time
from datetime import datetime
import string


class Utils(object):

    """Utility class"""

    timer_start = timer_stop = 0.0
    show_warn = True
    show_debug = True
    show_verbose = True
    # Default date format string
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def clean_symlinks(path=None, delete=False):
        """
        Search for broken symlinks.

        Given a path, it search for all symlinks 'path' directory and remomve broken symlinks.
        If delete is True, remove broken symlink(s), otherwise lists broken symlinks.

        :param path: Path to search symlinks from
        :type path: str
        :param delete: Wether to delete or not broken symlink(s)
        :type delete: bool
        :return: True/False
        :rtype: bool:
        :raise SystemExit: If path not found, or not given
        :raise SystemExit: If remove of symlink(s) failed
        """
        if path is None:
            Utils.error("Path not given")
        if not os.path.isdir(path):
            Utils.error("Path '%s' does not exist" % str(path))
        links = os.listdir(path)
        broken = []
        for link in links:
            try:
                link = os.path.join(path, link)
                os.stat(link)
            except OSError:
                broken.append(link)
        if not delete:
            Utils.warn("%d link(s) need to be cleaned" % int(len(broken)))
            Utils.verbose("\n".join(broken))
        else:
            deleted = 0
            for link in broken:
                os.remove(link)
                deleted += 1
            Utils.ok("%d links removed" % int(deleted))
        return True

    @staticmethod
    def elapsed_time():
        """
        Get the elapsed time between start and stop timer.

        Stop timer call is not required. If not set, it is automatically called
        as soon as the method is called

        :return: Elapsed time
        :rtype: float
        :raises SystemExit: If Utils.timer_start is not defined
        """
        if Utils.timer_start:
            if not Utils.timer_stop:
                Utils.stop_timer()
            etime = Utils.timer_stop - Utils.timer_start
            Utils.reset_timer()
            return etime
        Utils.error("Missing timer value (start/stop)")

    @staticmethod
    def error(msg):
        """
        Prints error message on STDERR and exits with exit code 1

        :param msg: Message to print
        :type msg: str
        :return: Error message
        :rtype: str
        :raises SystemExit:
        """
        Utils._print("[ERROR] %s" % str(msg), to=sys.stderr)
        sys.exit(1)

    @staticmethod
    def get_files(path=None):
        """
        Return the list of file(s) found for a given path

        :param path: Path to search from
        :type path: str
        :return: List of file(s) found
        :rtype: list
        :raises SystemExit: If path does not exist
        """
        if not path or not os.path.isdir(path):
            Utils.error("Path not found: %s" % str(path))
        return os.listdir(path)

    @staticmethod
    def get_deepest_dirs(path=None, full=False):
        """
        Get the last directories from a path

        :param path: Path to start from
        :type path: str
        :param full: Get the full path otherwise the directory only
        :type full: bool
        :return: List of directories
        :rtype: list
        :raises SystemExit: If 'path' not given or does not exist
        """
        if path is None:
            Utils.error("Path is required")

        if not os.path.exists(path) and not os.path.isdir(path):
            Utils.error("%s does not exists" % str(path))

        dirs = []
        for dir_path, dir_names, _ in os.walk(path):
            if len(dir_names) == 0:
                if full:
                    dirs.append(dir_path)
                else:
                    dirs.append(os.path.basename(dir_path))
        return dirs

    @staticmethod
    def get_deepest_dir(path=None, full=False):
        """
        Return only one deepest dir from the path

        :param path: Path
        :type path: str
        :param full: Returns complete path or not
        :type full: bool
        :return: Directory name
        :rtype: str
        """
        dirs = Utils.get_deepest_dirs(path, full=full)
        if len(dirs) > 1:
            Utils.warn("More than one deepest dir found at %s: Only first returned" % str(path))
        return dirs[0]

    @staticmethod
    def get_now():
        """
        Get current time from :class:`time.time` formatted using :py:const:`Utils.DATE_FMT`

        :returns: Current time formatted using :class:`Utils.DATE_FMT`
        :rtype: :class:`time.time`
        """
        return Utils.time2datefmt(time())

    @staticmethod
    def get_subtree(path=None):
        """
        Get the subtree structure from a root path

        E.g.: File system is /t/a1/a2/a3, get_subtree(path='/t') -> /a1/a2/a3
        :param path: Root path to get subtree structure from
        :type path: str
        :return: List of found subtree
        :rtype: list
        """
        subtrees = []
        if path is None:
            Utils.warn("No root path directory given")
            return subtrees
        for dir_path, dir_name, file_name in os.walk(path):
            if len(dir_name) == 0:
                subtree = dir_path.split(path)[-1]
                subtree = subtree.lstrip('/')
                subtrees.append(subtree)
        return subtrees

    @staticmethod
    def ok(msg):
        """
        Prints a [OK] msg

        :param msg: Message to print
        :type msg: str
        :return: Message to print
        :rtype: str
        """
        if msg:
            Utils._print("[OK] %s" % str(msg))

    @staticmethod
    def reset_timer():
        """Reset to *0.0* :py:func:`timer_start` and :py:func:`timer_stop` for a new :py:func:`elapsed_time()` count"""
        Utils.timer_start = 0.0
        Utils.timer_stop = 0.0

    @staticmethod
    def _print(msg, to=sys.stdout):
        """
        Redefined print function to support python 2 and 3

        :param msg: Message to print
        :type msg: str
        :param to: File handle
        :type to: file
        :return: Message to print
        :rtype: str
        """
        if not msg:
            return
        msg = str(msg).rstrip("\n")
        print(msg, file=to)
        return

    @staticmethod
    def start_timer():
        """Set current time at function call"""
        Utils.timer_start = time()

    @staticmethod
    def stop_timer():
        """Set current time at function call"""
        Utils.timer_stop = time()

    @staticmethod
    def time2date(otime):
        """
        Convert a timestamp into a datetime object

        :param otime: Timestamp to convert
        :type otime: time
        :return: Formatted time to date
        :rtype: :class:`datetime.datetime`
        """
        return datetime.fromtimestamp(otime)

    @staticmethod
    def time2datefmt(otime, fmt=DATE_FMT):
        """
        Converts a timestamp into a date following the format fmt, default to Utils.DATE_FMT

        :param otime: Timestamp to convert
        :type otime: time
        :param fmt: Date format to follow for conversion
        :type fmt: str
        :return: Formatted time to date
        :rtype: :class:`datetime.datetime`
        """
        return datetime.fromtimestamp(otime).strftime(fmt)

    @staticmethod
    def user():
        """
        Returns the current user running or using the script. Taken from os.env

        :return: User name
        :rtype: str
        """
        return os.getenv('USER')

    @staticmethod
    def verbose(msg):
        """
        Prints verbose message. Requires Manager.verbose to be True

        :param msg: Verbose message to print
        :type msg: str
        :return: Verbose message
        :rtype: str
        """
        from .manager import Manager
        if Manager.verbose and Utils.show_verbose:
            Utils._print('[VERBOSE] %s' % str(msg))

    @staticmethod
    def warn(msg):
        """
        Prints warning message. Required Utils.show_warn to be set to True

        :param msg: Warning message to print
        :type msg: str
        :return: Warning message
        :rtype: str
        """
        if Utils.show_warn:
            Utils._print('[WARNING] %s' % str(msg), to=sys.stderr)
