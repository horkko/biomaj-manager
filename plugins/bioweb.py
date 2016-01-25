from __future__ import print_function

import ssl
import pymongo
from biomajmanager.plugins import BMPlugin
from biomajmanager.utils import Utils


class Bioweb(BMPlugin):

    """
    Bioweb (Institut Pasteur, Paris) is a web portal which provide information about
    bioinformatics resources 
    """

    CONNECTED = False
    COLLECTION_TYPE = 'bank'

    def getCollection(self, name):
        """
        Get a collection (pymongo) object from the list loaded at connection. If the collection does not exists
        it prints an error on STDERR and exit(1)
        :param name: Collectio name
        :type name: String
        :return: Collection object, or throws error
        """
        if not name:
            Utils.error("A collection name is required")
        if not name in self.collections:
            Utils.error("Collection %s not found" % str(name))

        return self.collections[name]

    def get_info_for_bank(self, name):
        """
        Test method to retrieve information from MongoDB (Bioweb) database
        :param name: Name of the bank (optional)
        :type name: String
        :return: Pymongo Cursor for the bank
        """

        if not Bioweb.CONNECTED:
            self._init_db()

        query = {}
        if name:
            query['name'] = name
        else:
            query['name'] = self.manager.bank.name
        return self.getCollection('catalog').find(query)

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
            return self._update_mongodb(data=[data], collection='news')
        Utils.warn("Can't set new %s bank version, not published yet" % self.manager.bank.name)
        return False

    def update_bioweb(self):
        """
        Update the Bioweb.catalog MongoDB collection
        :return: Boolean
        """

        history = self.manager.mongo_history()
        if not self._update_mongodb(data=history):
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
                                'packageVersions': packages,
                                'description': description,
                                'status': status,
                                })
            if not self._update_mongodb(data=history):
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

    def update_db_with_data(self, filter, data, collection=None):
        """
        Method used to update the Bioweb mongo database
        :param filter: Query that match the document
        :type filter: Dict
        :param data: Original data to update
        :type data: Dict
        :param collection: Collection name
        :type collection: String
        :return: Boolean
        """

        if not collection:
            Utils.error("A collection name is required")
        if not Bioweb.CONNECTED:
            self._init_db()

        if (pymongo.version_tuple)[0] > 2:
            res = self.getCollection(collection).update_one(filter, {'$set': data}, upsert=True)
        else:
            res = self.getCollection(collection).update(filter, {'$set': data}, upsert=True)
        self._update_documents_counts(res)
        self._print_updated_documents()

    """
    Private methods
    """

    def _init_db(self):
        """
        Load and connect to Mongodb database
        :return:
        """

        if not self.config:
            Utils.error("No configuration object set")

        try:
            # Try to connect to MongoDB using args
            mongo_host = self.config.get(self.get_name(), 'bioweb.mongo.host')
            mongo_port = int(self.config.get(self.get_name(), 'bioweb.mongo.port'))
            mongo_use_ssl = int(self.config.get(self.get_name(), 'bioweb.mongo.use_ssl'))
            mongo_options = {}
            if mongo_use_ssl:
                mongo_options['ssl'] = True
                mongo_options['ssl_cert_reqs'] = ssl.CERT_NONE
            # Specific SSL agrs for bioweb-prod
            self.mongo_client = pymongo.MongoClient(host=mongo_host, port=mongo_port, **mongo_options)
            dbname = self.config.get(self.get_name(), 'bioweb.mongo.db')
            self.dbname = self.mongo_client[dbname]
            self.collections = {}
            
            # Keep trace of updated documents
            self.doc_matched = self.doc_modified = self.doc_upserted = 0

            if not self.config.has_option(self.get_name(), 'bioweb.mongo.collections'):
                Utils.error("No collection(s) set for bioweb database")

            for collection in self.config.get(self.get_name(), 'bioweb.mongo.collections').strip().split(','):
                self.collections[collection] = self.dbname[collection]

        except pymongo.ConnectionFailure as err:
            raise Exception("[ConnectionFailure] Can't connect to Mongo database %s: %s" % (dbname, str(err)))
        except pymongo.InvalidName as err:
            raise Exception("Error getting collection: %s" % str(err))
        except pymongo.InvalidURI as err:
            raise Exception("[InvalidURI] Can't connect to Mongo database %s: %s" % (dbname, str(err)))
        except pymongo.OperationFailure as err:
            raise Exception("Operation failed: %s" % str(err))
        except pymongo.InvalidName as err:
            raise Exception("Error getting collection: %s" % str(err))
        except Exception as err:
            raise Exception("Error while setting Mongo configuration: %s" % str(err))

        Bioweb.CONNECTED = True

    def _update_mongodb(self, data=None, collection='catalog', params=None, upsert=True):
        """
        Function that really update the Mongodb collection ('catalog')
        It does an upsert to update the collection
        :param data: Data to be updated
        :type data: Dict
        :param collection: Collection name to update (Default 'catalog')
        :type collection: String
        :param params: Extra parameters to filter documents to update
        :type params: Dict
        :param upsert: Perform upsert or not
        :type upsert: Boolean
        :return: Boolean
        """
        if not self.manager.bank.name:
            Utils.error("Can't update, bank name required")
        if not data:
            Utils.warn("[%s] No data to update bioweb catalog" % self.manager.bank.name)
            return True

        if not Bioweb.CONNECTED:
            self._init_db()

        # Find arguments
        search_params = {'type': Bioweb.COLLECTION_TYPE, 'name': self.manager.bank.name}

        # Extra serach parameters?
        if params is not None:
            search_params.update(params)

        for item in data:
            if '_id' in item:
                search_params['_id'] = item['_id']
            if (pymongo.version_tuple)[0] > 2:
                res = self.getCollection(collection).update_one(search_params, {'$set': item},
                                                                upsert=upsert)
            else:
                res = self.getCollection(collection).update(search_params, {'$set': item},
                                                            upsert=upsert)
            self._update_documents_count(res)
        self._print_updated_documents()
        return True

    def _update_documents_counts(self, res):
        """
        Update internal counter about matched/modified/upserted documents during an update
        :param res: Result return by an update
        :type res: Depending on pymongo version (3.2=UpdateResult, 2.x=Dict)
        :return: Boolean
        """
        if not res:
            return False

        if (pymongo.version_tuple)[0] > 2:
            self.doc_matched += res.matched_count
            self.doc_modified += res.modified_count
            if res.upserted_id:
                self.doc_upserted += 1
        else:
            if res['updatedExisting']:
                self.doc_matched += 1
            self.doc_modified += res['nModified']
            if 'upserted' in res:
                self.doc_upserted += 1

        return True

    def _print_updated_documents(self):
        """
        Print a small report of action(s) done duinrg the update
        :param matched: Number of documents matched based on filtering query
        :type matched: Int
        :param modified: Number of documents updated during update
        :type modified: Int
        :param upserted: Number of new documents created (using 'upsert') during update
        :type upserted: Int
        :return: Boolean
        """
        if not self.get_manager().get_verbose():
            return True
        bank = ""
        if self.manager.bank:
            bank = "[%s] " % self.manager.bank.name
        Utils.ok("%sDocument(s) modification(s):\n\tMatched %d\n\tUpdated %d\n\tInserted %d"
                 % (bank, self.doc_matched, self.doc_modified, self.doc_upserted))
        self.doc_matched = self.doc_modified = self.doc_upserted = 0
        return True
