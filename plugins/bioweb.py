from __future__ import print_function

import os
import time
import datetime

from biomajmanager.plugins import BMPlugin
from biomajmanager.utils import Utils
from biomajmanager.manager import Manager
from pymongo import MongoClient


class Bioweb(BMPlugin):

    """
    Bioweb (Institut Pasteur, Paris) is a web portal which provide information about
    bioinformatics resources 
    """

    def get_info_for_bank(self, name):
        """
        Test method to retrieve information from MongoDB (Bioweb) database
        :param name: Name of the bank (optional)
        :type name: String
        :return: Pymongo Cursor for the bank
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
        except Exception as err:
            raise Exception("Error while setting mongo configuration: %s" % str(err))

        query = {}
        if name:
            query = {'name': name}
        return self.collname.find(query)

    def update_db(self, data):
        """
        Method used to update the Bioweb mongo database
        :param data: Original data to update
        :type data: JSON
        :return: Boolean
        """
        print("Updating data ...")
        if not data:
            Utils.error("Data to update required")

        for item in data:
            print("[%s] owner=%s, visibility=%s" % (str(item['name']),
                                                    str(item['properties']['owner']),
                                                    str(item['properties']['visibility'])))

    def _init_db(self):
        """
        Load and connect to Mongodb database
        :return:
        """

        if self.mongo_client:
            return


    
