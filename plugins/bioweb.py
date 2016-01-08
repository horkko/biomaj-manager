from __future__ import print_function

import os
import sys
import time
import datetime
import ssl
from biomajmanager.plugins import BMPlugin
from biomajmanager.utils import Utils
from biomajmanager.news import News
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
            query['name'] = name
        else:
            query['name'] = self.manager.bank.name
        return self.dbname.get_collection('catalog').find(query)

    def set_bank_update_news(self):
        """
        Send a new to MongoDB to let bioweb know about bank update. Update MongoDB
        :return: Boolean
        """

        if not self.manager.bank:
            Utils.error("A bank name is required")

        if 'current' in self.manager.bank.bank:
            data = {}
            data['message'] = "Bank %s updated to version %s" % (self.manager.bank.name, str(self.manager.current_release()))
            data['date'] = Utils.time2date(self.manager.bank.bank['current'])
            data['operation'] = "databank update"
            data['type'] = Bioweb.COLLECTION_TYPE
            data['name'] = self.manager.bank.name
            return self._update_biowebdb(data=[data], collection='news')
        Utils.warn("Can't set new %s bank version, not published yet" % self.manager.bank.name)
        return False

    def update_bioweb(self):
        """
        Update the Bioweb.catalog MongoDB collection
        :return: Boolean
        """

        history = self.manager.mongo_history()
        if not self._update_biowebdb(data=history):
            Utils.error("Can't update bioweb.catalog")

        return True

    def update_bioweb_from_mysql(self):
        """
        Get the history from the MySQL database (Biomaj 1.2.x) and transform it to a json
        document.
        :return: Boolean
        """
        import mysql.connector
        from mysql.connector import errorcode

        params = {}
        for param in ['host', 'database', 'user', 'password']:
            if not self.config.has_option(self.get_name(), 'bioweb.mysql.%s' % param):
                Utils.error("MySQL %s parameter not set!" % param)
            else:
                params[param] = self.config.get(self.get_name(), 'bioweb.mysql.%s' % param)

        try:
            cnx = mysql.connector.connect(**params)
            cursor = cnx.cursor(dictionary=True)
            query = "SELECT b.name AS bank, ub.updateRelease AS version, pd.remove AS removed, pd.creation AS created, "
            query += "pd.path AS path, pd.state AS status, pd.idproductionDirectory AS id FROM productionDirectory pd "
            query += "JOIN updateBank ub ON ub.idLastSession = pd.session JOIN bank b on b.idbank = pd.ref_idbank WHERE "
            query += "b.name = %(bank)s ORDER BY creation DESC;"
            cursor.execute(query, {'bank': self.manager.bank.name})

            history = [ ]
            packages = self.manager.get_bank_packages()
            description = self.manager.bank.config.get('db.fullname').replace('"', '').strip()
            bank_type = self.manager.bank.config.get('db.type').split(',')
            bank_format = self.manager.bank.config.get('db.formats').split(',')
            status = None
            for row in cursor.fetchall():
                if not row['removed']:
                    if not status:
                        status = 'online'
                    else:
                        status = 'deprecated'
                else:
                    status = row['status']

                history.append({'_id': '@'.join(['bank',
                                                 self.manager.bank.name,
                                                 row['version'],
                                                 row['created'].strftime(self.manager.DATE_FMT)]),
                                'type': 'bank',
                                'name': self.manager.bank.name,
                                'version': row['version'],
                                'publication_date': row['created'], #Utils.local2utc(row['created']),
                                'removal_date': row['removed'], #Utils.local2utc(row['removed']) if row['removed'] else row['removed'],
                                'bank_type': bank_type,
                                'bank_format': bank_format,
                                'packages': packages,
                                'description': description,
                                'status': status,
                                })
            if not self._update_biowebdb(data=history):
                Utils.error("Can't update bioweb.catalog")
        except mysql.connector.ProgrammingError as error:
            Utils.error("[Syntax Error] %s" % str(error))
        except mysql.connector.Error as error:
                if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    Utils.error("[Access Denied] Wrong username or password: %s" % error.msg)
                elif error.errno == errorcode.ER_BAD_DB_ERROR:
                    Utils.error("[Database] Database does not exist: %s" % error.msg)
                else:
                    Utils.error("Unknown error: %s" % error)
        finally:
            cnx.close()

        return True

    def update_db_with_data(self, filter, data, col=None):
        """
        Method used to update the Bioweb mongo database
        :param filter: Query that match the document
        :type filter: Dict
        :param data: Original data to update
        :type data: Dict
        :param col: Collection name
        :type col: String
        :return: Boolean
        """

        if not col:
            Utils.error("A collection name is required")
        if not Bioweb.connected:
            self._init_db()

        res = self.dbname.get_collection(col).update_one(filter, {'$set': data})
        Utils.ok("%s document(s) matched, %s document(s) updated" % (str(res.matched_count), str(res.modified_count)))

    def _init_db(self):
        """
        Load and connect to Mongodb database
        :return:
        """

        if not self.config:
            Utils.error("No configuration object set")

        try:
            #url = self.config.get(self.get_name(), 'bioweb.mongo.url')
            #self.mongo_client = MongoClient(url)

            mongo_host = self.config.get(self.get_name(), 'bioweb.mongo.host')
            mongo_port = int(self.config.get(self.get_name(), 'bioweb.mongo.port'))
            self.mongo_client = MongoClient(host=mongo_host, port=mongo_port, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)

            dbname = self.config.get(self.get_name(), 'bioweb.mongo.db')
            coll_catalog = self.config.get(self.get_name(), 'bioweb.mongo.collection.catalog')
            coll_news = self.config.get(self.get_name(), 'bioweb.mongo.collection.news')

            self.dbname = self.mongo_client[dbname]
            self.collcatalog = self.dbname[coll_catalog]
            self.collnews = self.dbname[coll_news]
        except ConnectionFailure as err:
            raise Exception("[ConnectionFailure] Can't connect to Mongo database %s: %s" % (dbname, str(err)))
        except InvalidURI as err:
            raise Exception("[InvalidURI] Can't connect to Mongo database %s: %s" % (dbname, str(err)))
        except OperationFailure as err:
            raise Exception("Operation failed: %s" % str(err))
        except InvalidName as err:
            raise Exception("Error getting collection: %s" % str(err))
        except Exception as err:
            raise Exception("Error while setting Mongo configuration: %s" % str(err))

        Bioweb.connected = True

    def _update_biowebdb(self, data=None, collection='catalog', upsert=True):
        """
        Function that really update the Mongodb collection ('catalog')
        It does an upsert to update the collection
        :param data: Data to be updated
        :type data: Dict
        :return: Boolean
        """
        if not data:
            Utils.error("Need data to update bioweb catalog")

        if not Bioweb.connected:
            self._init_db()

        matched = modified = upserted = 0
        for item in data:
            res = self.dbname.get_collection(collection).update_one({'type': Bioweb.COLLECTION_TYPE, '_id': item['_id'],
                                                                     'name': self.manager.bank.name},
                                                                     {'$set': item},
                                                                     upsert=upsert)
            matched += res.matched_count
            modified += res.modified_count
            if res.upserted_id:
                Utils.ok("Updated %s" % str(res.upserted_id))
                upserted += 1
        Utils.ok("Document(s) modification(s):\n\tMatched %d\n\tUpdated %d\n\tInserted %d" % (matched, modified, upserted))
        return True
