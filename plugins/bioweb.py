from __future__ import print_function

import os
import sys
import time
import datetime

from biomajmanager.plugins import BMPlugin
from biomajmanager.utils import Utils
from pymongo import MongoClient
from pymongo.errors import InvalidName, ConnectionFailure, InvalidURI, OperationFailure


class Bioweb(BMPlugin):

    """
    Bioweb (Institut Pasteur, Paris) is a web portal which provide information about
    bioinformatics resources 
    """

    connected = False
    COLLECTION_TYPE = 'bank'

    def get_info_for_bank(self, name):
        """
        Test method to retrieve information from MongoDB (Bioweb) database
        :param name: Name of the bank (optional)
        :type name: String
        :return: Pymongo Cursor for the bank
        """

        if not Bioweb.connected:
            self._init_db()

        query = {}
        if name:
            query = {'name': name}
        return self.collname.find(query)

    def update_bioweb_catalog(self):
        """
        Update the Bioweb.catalog MongoDB collection
        :return:
        """

        if not Bioweb.connected:
            self._init_db()

        history = self.get_manager().mongo_history()
        matched = modified = 0

        from pprint import pprint
        for item in history:
            pprint(item)
            res = self.collname.update_one({'type': Bioweb.COLLECTION_TYPE, '_id': item['_id'], 'name': self.get_manager().bank.name},
                                           {'$set': item},
                                           upsert=True)
            matched += res.matched_count
            modified += res.modified_count
        Utils.ok("%d document(s) matched, %d document(s) updated" % (matched, modified))

    def update_db(self, filter, data):
        """
        Method used to update the Bioweb mongo database
        :param filter: Query that match the document
        :type filter: Dict
        :param data: Original data to update
        :type data: Dict
        :return: Boolean
        """

        if not Bioweb.connected:
            self._init_db()

        res = self.collname.update_one(filter, {'$set': data})
        Utils.ok("%s document(s) matched, %s document(s) updated" % (str(res.matched_count), str(res.modified_count)))

    def _init_db(self):
        """
        Load and connect to Mongodb database
        :return:
        """

        if not self.config:
            Utils.error("No configuration object set")

        try:
            url = self.config.get(self.get_name(), 'bioweb.mongo.url')
            dbname = self.config.get(self.get_name(), 'bioweb.mongo.db')
            collname = self.config.get(self.get_name(), 'bioweb.mongo.collection')
            self.mongo_client = MongoClient(url)
            self.dbname = self.mongo_client[dbname]
            self.collname = self.dbname[collname]
        except (ConnectionFailure, InvalidURI) as err:
            raise Exception("Can't connect to Mongo database %s: %s" % (dbname, str(err)))
        except OperationFailure as err:
            raise Exception("Operation failed: %s" % str(err))
        except InvalidName as err:
            raise Exception("Error getting collection: %s" % str(err))
        except Exception as err:
            raise Exception("Error while setting Mongo configuration: %s" % str(err))

        Bioweb.connected = True
