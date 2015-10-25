from biomaj.mongo_connector import MongoConnector
from biomaj.manager.bankrelease import BankRelease
import os
import time
from datetime import datetime
import json


class NoSQLConnector(MongoConnector):

    url = None
    driver = None

    def get_bank_list(self):
        """
        Get the list of bank available from the database
        :return: List of bank name
        :rtype: List of string
        """
        self._is_connected()
        banks = MongoConnector.banks.find({}, {'name': 1, '_id': 0})
        list = []
        for bank in banks:
            list.append(bank['name'])
            print "[mongo] %s" % bank['name']
        return list

    def _history(self, bank=None, to_json=False):
        '''
            Get the releases history of a specific bank

            :param name: Name of the bank
            :type name: String
            :param idbank: Bank id (primary key)
            :type idbank: Integer
            :param to_json: Converts output to json
            :type name: Boolean (Default False)
            :return: A list with the full history of the bank
        '''
        if not bank:
            raise Exception("Bank instance is required")

        history = []
        # We get the status of the last action
        productions = MongoConnector.banks.find({'name': bank.name}, {'_id': 0})

        # First we get the release and info from the production
        prods = [ ]
        sesss = [ ]

        for p in productions:
            prods = p['production']
            sesss = p['sessions']

        for prod in prods:
            history.append({
            # Convert the time stamp from time() to a date
                'created': datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d %H:%M:%S"),
                'id': prod['session'],
                'removed': None,
                'status': 'available',
                'name': bank.name,
                'path': os.path.join(prod['data_dir'], bank.name, prod['dir_version'], prod['prod_dir']),
                'release': prod['remoterelease'],
                'freeze': prod['freeze'],
            })

        for sess in sesss:
            # Don't repeat production item stored in sessions
            if sess['id'] in map(lambda(d): d['id'], history):
                continue
            dir = os.path.join(sess['data_dir'], bank.name, sess['dir_version'], sess['prod_dir'])
            status = 'available' if os.path.isdir(dir) else 'deleted'
            history.append({
                    'created': datetime.fromtimestamp(sess['id']).strftime(("Y%-%m-%d %H:%M:%S")),
                    'id': sess['id'],
                    'removed': True,
                    'status': status,
                    'name': bank.name,
                    'path': dir,
                })

        """
        print "Available release(s): %d (%s)" % (len(history['available']), ','.join(map(lambda(d): d['remoterelease'], history['available'])))
        print "Deleted release(s)  : %d (%s)" % (len(history['deleted']), ','.join(map(lambda(d): d['remoterelease'], history['deleted'])))
        """
        if to_json:
            return json.dumps(history)
        return history

    def _mongo_history(self, bank=None):
        """
            Get the releases history of a bank from the database and build a Mongo like document in json
            :param name: Name of the bank
            :type name: String
            :param idbank: Bank id (primary key)
            :tpye idbank: Integer
            :return: Jsonified history + extra info to be included into bioweb (Institut Pasteur only)
        """
        if not bank:
            raise Exception("Bank instance is required")

        productions = MongoConnector.banks.find({'name': bank.name}, {'_id': 0})
        history = []
        prods = []
        sesss = []
        for p in productions:
            prods = p['production']
            sesss = p['sessions']

        for prod in prods:
            history.append({'_id': '@'.join(['bank',
                                             bank.name,
                                             prod['remoterelease'],
                                             datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d_%H:%M:%S")]),
                             'type': 'bank',
                             'name': bank.name,
                             'version': prod['remoterelease'],
                             'publication_date': datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d %H:%M:%S"),
                             'removal_date': None,
                             'bank_type': bank.config.get('db.type').split(','),  # Can be taken from db table remoteInfo.dbType
                             'bank_format': bank.config.get('db.formats').split(','),
                             'packages': bank._get_formats_for_release(os.path.join(prod['data_dir'], prod['dir_version'], prod['prod_dir'])),
                             'description': bank.config.get('db.fullname').replace('\"','')
                            })
        for sess in sesss:
            history.append({'_id': '@'.join(['bank',
                                             bank.name,
                                             prod['remoterelease'],
                                             datetime.fromtimestamp(prod['session']).strftime("%Y-%m-%d_%H:%M:%S")]),
                            'type': 'bank',
                            'name': bank.name,
                            'version': sess['remoterelease'],
                            'publication_date': datetime.fromtimestamp(sess['last_update_time']).strftime("%Y-%m-%d %H:%M:%S"),
                            'removal_date': sess['last_modified'] if 'remove_release' in sess['status'] and sess['status']['remove_release'] == True
                                                                  else None,
                            'bank_type': bank.config.get('db.formats').split(','),
                            # 'bank_type': # Could be from properteies.type (Mongo),
                            'bank_formats': bank.config.get('db.formats').split(','),
                            'packages': bank._get_formats_for_release(os.path.join(sess['data_dir'], sess['dir_version'], sess['release'])),
                            'description': bank.config.get('db.fullname').replace('\"',''),
                            })
        return json.dumps(history)

    def _is_connected(self):
        """
          Check the bank object has a connection to the database set.
          :return: raise Exception if no connection set
        """
        if MongoConnector.db:
            return True
        else:
            raise Exception("No db connection available. Build object with 'connect=True' to access database.")

    def _check_bank(self, name=None):
        """
            Checks a bank exists in the database
            :param name: Name of the bank to check [Default self.name]
            :param name: String
            :return:
            :throws: Exception if bank does not exists
        """
        self._is_connected()
        if name is None:
            raise Exception("Can't check bank, name not set")
        res = MongoConnector.banks.find({'name': name}, {'_id': 1})
        if res.count() > 1:
            raise Exception("More than one bank %s found!" % name)
        elif res.count() == 0:
            raise Exception("Bank %s does not exists" % name)
        return res[0]['_id']


    def _get_releases(self, bank):
        """

        :param bank: Bank instance
        :return: List of BankRelease
        """
        print "Getting releases for bank {0}".format(bank.name)
        sessions = MongoConnector.banks.find({"name": bank.name}, {"sessions": 1, "status": 1, "_id": 0})
        status = MongoConnector.banks.find({"name": bank.name}, {"status": 1, "_id": 0})
        stsess = status[0]['status']['session']
        sessions = sessions[0]['sessions']
        releases = []
        for session in sessions:
            rel = BankRelease()
            if session['id'] == stsess:
                rel.status = 'current'
            print session



    def _current_release(self):
        """
        Get the last 'current' release of a bank
        :return: list
        """
        pass