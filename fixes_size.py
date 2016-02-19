#!/usr/bin/env python

from biomaj.bank import Bank
from biomaj.config import BiomajConfig
import humanfriendly
import re

if __name__ == '__main__':

    config = BiomajConfig.load_config()
#    bank_list = Bank.list()
#    pattern = re.compile(".+\w$")
#    for name in bank_list:
#        bank = Bank(name['name'], no_log=True)
#        if 'production' in bank.bank:
#            #print("Need to update %s" % name['name'])
#            for prod in bank.bank['production']:
#                if 'size' in prod:
#                    if type(prod['size']) is int or type(prod['size']) is int64:
#                        continue
#                    else:
#                        size = prod['size']
#                        new_size = humanfriendly.parse_size(prod['size'].replace(',', '.'))
#                        bank.banks.update_one({'name': name['name'], 'production.size': size},
#                                          {'$set': {'production.$.size': new_size}})
#                        print("Updated %s!" % name['name'])
#    bank_list = Bank.get_banks_disk_usage()
#    for bank in bank_list:
#        print("Bank %s has size %d" % (bank['name'], bank['size']))
