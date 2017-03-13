"""Global decorators for BioMAJ Manager"""
from biomajmanager.utils import Utils
from functools import wraps
__author__ = 'tuco'


def bank_required(func):
    """
    Decorator function that checks a bank name is set

    :param func: Decorated function
    :type func: Function
    :return: Result of function called
    :rtype: func
    :raises SystemExit: If no bank set
    """
    @wraps(func)
    def _check_bank_required(*args, **kwargs):
        """Small function to check a bank object is set in BioMAJ Manager instance"""
        self = args[0]
        if self.bank is None:
            Utils.error("A bank name is required")
        return func(*args, **kwargs)
    return _check_bank_required

def deprecated(func):
    """
    This is a decorator which can be used to mark functions as deprecated.

    It will result in a warning being emitted when the functionis used.

    :param func: Decorated function
    :type func: Function
    :return: Result of functio called
    :rtype: func
    """
    @wraps(func)
    def _dep_func(*args, **kwargs):
        Utils.error("Call to deprecated function '{}'. Not executed.".format(func.__name__))
    _dep_func.__name__ = func.__name__
    _dep_func.__doc__ = func.__doc__
    _dep_func.__dict__.update(func.__dict__)
    return _dep_func

def user_granted(func):
    """
    Decorator function that checks a user has enough right to perform action

    :param func: Decorated function
    :type func: Function
    :return: Result of function called
    :rtype: func
    :raises SystemExit: If no owner found either in bank nor in config file
    """
    @wraps(func)
    def _check_user_granted(*args, **kwargs):
        """
        Check the user has enough right to perform action(s).

        If a bank is set, we first set the user as the owner of
        the current bank. Otherwise we try to find it from the
        config file, we search for 'admin' property

        :return: Boolean
        """
        self = args[0]
        admin = self.config.get('GENERAL', 'admin')
        if self.bank:
            props = self.bank.get_properties()
            if 'owner' in props and props['owner']:
                admin = props['owner']
        if not admin:
            Utils.error("Could not find admin user either in config nor in bank")

        user = self.get_current_user()

        if admin != user:
            Utils.error("[%s] User %s, permission denied" % (admin, user))
        return func(*args, **kwargs)
    return _check_user_granted
