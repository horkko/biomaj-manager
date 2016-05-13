#! /usr/bin/env python

from biomajmanager.manager import Manager
from biomajmanager.decorators import deprecated

if __name__ == '__main__':

    manager = Manager()
    manager.load_plugins()
    print("Is connected: %s" % str(manager.plugins.bioweb.CONNECTED))
    bank = manager.plugins.bioweb.get_info_for_bank('alu')
    for b in bank:
        print("Version: %s, Date: %s" % (str(b['version']), str(b['_id'])))
    manager.plugins.bioweb.mongo_client.close()
    manager.plugins.bioweb.update_bioweb_from_mysql()
