__author__ = 'tuco'

from biomajmanager.utils import Utils

def bank_required(func):
    """
    Decorator function that check a bank name is set
    :param func:
    :return:
    """

    def _check_bank_required(*args, **kwargs):
        """
        """

        self = args[0]
        if self.bank is None:
            Utils.error("A bank name is required")
        return func(*args, **kwargs)
    return _check_bank_required

def user_granted(func):
    """
    Decorator that check a user has enough right to perform action
    :param func: Decorated function
    :type: Function
    :return:
    """
    def _check_user_granted(*args, **kwargs):
        """
        Check the user has enough right to perform action(s)
        If a bank is set, we first set the user as the owner of
        the current bank. Otherwise we try to find it from the
        config file, we search for 'user.admin' property

        :return: Boolean
        """

        self = args[0]
        admin = None
        admin = self.config.get('GENERAL', 'admin')
        if self.bank:
            props = self.bank.get_properties()
            if 'owner' in props and props['owner']:
                admin = props['owner']
        if not admin:
            Utils.error("Could not find admin user either in config nor in bank")

        user = self._current_user()

        if admin != user:
            Utils.error("[%s] User %s, permission denied" % (admin, user))
        return func(*args, **kwargs)
    return _check_user_granted