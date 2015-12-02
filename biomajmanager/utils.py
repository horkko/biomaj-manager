from __future__ import print_function
import os
import sys
from time import time


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

    @staticmethod
    def warn(msg):
        print('[WARNING] ' + msg, file=sys.stderr)

    @staticmethod
    def verbose(msg):
        from .manager import Manager
        if Manager.verbose:
            print('[VERBOSE] ' + msg, file=sys.stdout)
