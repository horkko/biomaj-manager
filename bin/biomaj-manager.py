#!/usr/bin/env python

"""
BioMAJ Manager - Swiss knife for BioMAJ 3

This script is used to use take advantage of functions developed around BioMAJ3 API
To see what's possible, just type biomaj-manager.py --help
"""
from __future__ import print_function
from future import standard_library
from pprint import pprint
standard_library.install_aliases()

import argparse
import json
import pkg_resources
import sys

from biomaj.options import Options
from biomajmanager.manager import Manager
from biomajmanager.writer import Writer
from biomajmanager.news import News
from biomajmanager.utils import Utils
from biomajmanager.links import Links
from tabulate import tabulate
__author__ = 'tuco'


def main():
    """This is the main function treating arguments passed on the command line."""
    description = "BioMAJ Manager adds some functionality around BioMAJ."
    parser = argparse.ArgumentParser(description=description)
    # Options without value
    parser.add_argument('-C', '--clean_links', dest="clean_links", action="store_true", default=False,
                        help="Remove old links (Permissions required)")
    parser.add_argument('-D', '--save_versions', dest="save_versions", action="store_true", default=False,
                        help="Prints info about all banks into version file. (Requires permissions)")
    parser.add_argument('-H', '--history', dest="history", action="store_true", default=False,
                        help="Prints banks releases history. [-b] available.")
    parser.add_argument('-i', '--info', dest="info", action="store_true", default=False,
                        help="Print info about a bank. [-b REQUIRED]")
    parser.add_argument('-J', '--check_links', dest="check_links", action="store_true", default=False,
                        help="Check if the bank required symlinks to be created (Permissions required). [-b REQUIRED]")
    parser.add_argument('-l', '--links', dest="links", action="store_true", default=False,
                        help="Just (re)create symlink, don't do any bank switch. (Permissions required). [-b REQUIRED]")
    parser.add_argument('-L', '--bank_formats', dest="bank_formats", action="store_true", default=False,
                        help="List supported formats and index for each banks. [-b] available.")
    parser.add_argument('-M', '--to_mongo', dest="to_mongo", action="store_true", default=False,
                        help="[PLUGIN] Load bank(s) history into mongo database (bioweb). [-b and --db_type REQUIRED]")
    parser.add_argument('-N', '--news', dest="news", action="store_true", default=False,
                        help="Create news to display at BiomajWatcher. [Default output txt]")
    parser.add_argument('-n', '--simulate', dest="simulate", action="store_true", default=False,
                        help="Simulate action, don't do it really.")
    parser.add_argument('-P', '--show_pending', dest="pending", action="store_true", default=False,
                        help="Show pending release(s). [-b] available")
    parser.add_argument('-s', '--switch', dest="switch", action="store_true", default=False,
                        help="Switch a bank to its new version. [-b REQUIRED]")
    parser.add_argument('-X', '--test', dest="test", action="store_true", default=False,
                        help="Test method. [-b REQUIRED]")
    parser.add_argument('-U', '--show_update', dest="show_update", action="store_true", default=False,
                        help="If -b passed prints if bank needs to be updated. Otherwise, prints all bank that\
                              need to be updated. [-b] available.")
    parser.add_argument('-v', '--version', dest="version", action="store_true", default=False,
                        help="Show version")
    parser.add_argument('-V', '--verbose', dest="verbose", action="store_true", default=False,
                        help="Activate verbose mode")
    # Options with value required
    parser.add_argument('-b', '--bank', dest="bank",
                        help="Bank name")
    parser.add_argument('--db_type', dest="db_type",
                        help="BioMAJ database type [MySQL, MongoDB]")
    parser.add_argument('-o', '--out', dest="out",
                        help="Output file")
    parser.add_argument('-F', '--format', dest="oformat",
                        help="Output format. Supported [csv, html, json, tmpl[default]]")
    parser.add_argument('-T', '--templates', dest="template_dir",
                        help="Template directory. Overwrites template_dir")
    parser.add_argument('-S', '--section', dest="tool",
                        help="Prints [TOOL] section(s) for a bank. [-b REQUIRED]")
    parser.add_argument('--vdbs', dest="vdbs",
                        help="Create virtual database HTML pages for tool. [-b REQUIRED]")
    parser.add_argument('--visibility', dest="visibility", default="public",
                        help="Banks visibility ['all', 'public'(default), 'private'")

    options = Options()
    parser.parse_args(namespace=options)
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(1)
    Manager.set_simulate(options.simulate)
    Manager.set_verbose(options.verbose)
    
    if options.bank_formats:
        formats = []
        banks = []
        Utils.start_timer()
        manager = Manager()
        if options.bank:
            banks.append(options.bank)
        else:
            banks = Manager.get_bank_list()
        for bank in banks:
            manager.set_bank_from_name(name=bank)
            formats.append({'name': bank, 'formats': manager.formats_as_string(),
                            'fullname': manager.bank.config.get('db.fullname').replace('"', '')})
        if options.oformat:
            writer = Writer(config=manager.config, output=options.out, template_dir=options.template_dir)
            writer.write(template='banks_formats.j2.' + options.oformat,
                         data={'banks': formats, 'generated': Utils.get_now(),
                               'elapsed': "%.3f" % Utils.elapsed_time()})
            sys.exit(0)
        else:
            info = []
            supp_formats = ['bdb', 'blast', 'fasta', 'golden', 'hmmer', 'bowtie', 'bwa', 'GenomeAnalysisTK', 'samtools',
                            'soap', 'picard', 'raw', 'uncompressed']
            for fmt in formats:
                fmts = fmt['formats']
                list_fmt = [fmt['name']]
                for supp_fmt in supp_formats:
                    supported = ''
                    if supp_fmt in fmts or supp_fmt == 'raw':
                        supported = 'ok'
                    list_fmt.append(supported)
                info.append(list_fmt)
            if len(info):
                info.insert(0, ['Bank', 'bdb', 'blast', 'fasta', 'golden', 'hmmer', 'bowtie', 'bwa', 'gatk', 'samtools',
                                'soap', 'picard', 'raw', 'uncompressed'])
                print(tabulate(info, headers='firstrow', tablefmt='psql'))
            else:
                print("No formats supported")
        print("Elapsed time %.3f sec" % Utils.elapsed_time())
        sys.exit(0)

    if options.check_links:
        if not options.bank:
            Utils.error("A bank name is required")
        manager = Manager(bank=options.bank)
        linker = Links(manager=manager)
        if linker.check_links():
            print("[%s] %d link(s) need to be created" % (options.bank, linker.created_links))
        else:
            print("[%s] All links OK" % options.bank)
        sys.exit(0)

    if options.history:
        bank_list = []
        history = []
        if not options.bank:
            bank_list = Manager.get_bank_list()
        else:
            bank_list.append(options.bank)

        Utils.start_timer()
        for bank in bank_list:
            manager = Manager(bank=bank)
            history.append({'name': bank, 'history': manager.mongo_history()})
        if options.oformat:
            if options.oformat == 'json':
                print(json.dumps([h for hist in history for h in hist]))
            else:
                writer = Writer(config=manager.config, template_dir=options.template_dir, output=options.out)
                writer.write(template='history.j2.' + options.oformat,
                             data={'history': history, 'generated': Utils.get_now(),
                                   'elapsed': "%.3f" % Utils.elapsed_time()})
                sys.exit(0)
        else:
            if len(history):
                info = []
                for bank in history:
                    info = [['[%s] Release' % bank['name'], 'Status', 'Created', 'Removed']]
                    for hist in bank['history']:
                        info.append([hist['version'], hist['status'], hist['publication_date'],
                                     hist['removal_date']])
                    print(tabulate(info, headers="firstrow", tablefmt='psql'))
            else:
                print("No history available")
        sys.exit(0)

    if options.info:
        if not options.bank:
            Utils.error("Getting info required a bank name")
        manager = Manager(bank=options.bank)
        info = manager.bank_info()
        pprint(info)
        print(manager.bank.config.get('db.packages'))
        sys.exit(0)

    if options.links:
        if not options.bank:
            Utils.error("A bank name is required")
        Utils.start_timer()
        manager = Manager(bank=options.bank)
        linker = Links(manager=manager)
        linker.do_links()
        etime = Utils.elapsed_time()
        print("[%s] %d link(s) created (%f sec)" % (options.bank, linker.created_links, etime))
        sys.exit(0)

    if options.news:
        # Try to determine news directory from config gile
        config = Manager.load_config()
        news = News(config=config)
        news.get_news()
        if options.db_type:
            manager = Manager()
            manager.load_plugins()
            if not manager.plugins.bioweb.set_news(news.data):
                Utils.error("Can't set news to collection")
        else:
            if options.oformat is None:
                options.oformat = 'txt'
            writer = Writer(config=config, template_dir=options.template_dir, output=options.out)
            writer.write(template='news' + '.' + options.oformat, data=news.data)
        sys.exit(0)

    if options.pending:
        bank_list = []
        if not options.bank:
            bank_list = Manager.get_bank_list()
        else:
            bank_list.append(options.bank)
        info = []
        for bank in bank_list:
            manager = Manager(bank=bank)
            pending = manager.get_pending_sessions()
            if pending:
                if options.oformat != 'tmpl':
                    writer = Writer(config=manager.config, template_dir=options.template_dir, output=options.out)
                    writer.write(template='pending.j2.' + options.oformat, data={'pending': pending})
                else:
                    for pend in pending:
                        release = pend['release']
                        sess_id = pend['session_id']
                        date = Utils.time2datefmt(sess_id, Manager.DATE_FMT)
                        info.append([bank, str(release), str(date)])
        if info:
            info.insert(0, ["Bank", "Release", "Run time"])
            print("Pending banks:")
            print(tabulate(info, headers='firstrow', tablefmt='psql'))
        else:
            print("No pending session")
        sys.exit(0)

    if options.save_versions:
        manager = Manager()
        manager.save_banks_version()
        sys.exit(0)

    if options.show_update:
        manager = Manager(bank=options.bank)
        Utils.start_timer()
        updates = manager.show_need_update(visibility=options.visibility)
        if options.oformat:
            writer = Writer(config=manager.config, output=options.out)
            writer.write(template='banks_update.j2.' + options.oformat,
                         data={'banks': updates,
                               'next_switch': manager.next_switch_date().strftime("%Y/%M/%d"),
                               'generated': Utils.get_now(),
                               'elapsed': "%.3f" % Utils.elapsed_time()})
            sys.exit(0)
        elif len(updates) > 0:
            info = []
            for bank in updates:
                info.append([bank['name'], bank['current_release'], bank['next_release']])
            if len(info):
                info.insert(0, ["Bank", "Current release", "Next release"])
                print("Next bank switch will take place on %s @ 00:00AM" % manager.next_switch_date().strftime("%Y/%M/%d"))
                print(tabulate(info, headers='firstrow', tablefmt='psql'))
        else:
            print("No bank need to be updated")
        sys.exit(0)

    if options.switch:
        if not options.bank:
            Utils.error("A bank name is required")
        manager = Manager(bank=options.bank)
        if manager.can_switch():
            Utils.ok("[%s] Ready to switch" % manager.bank.name)
            Utils.ok("[%s] Publishing ..." % manager.bank.name)
            Utils.ok("[%s] Stopping running jobs ..." % manager.bank.name)
            manager.stop_running_jobs(args=[manager.get_bank_data_dir()])
            # Inspired from biomaj-cli.py
            manager.bank.load_session()
            last_prod_ok = manager.get_last_production_ok()
            session = manager.get_session_from_id(last_prod_ok['session'])
            manager.bank.session._session = session
            manager.bank.publish()
            Utils.ok("[%s] Restarting stopped jobs ..." % manager.bank.name)
            manager.restart_stopped_jobs()
            Utils.ok("[%s] Bank published!" % manager.bank.name)
        else:
            print("[%s] Not ready to switch" % manager.bank.name)
        sys.exit(0)

    if options.test:
        manager = Manager(bank=options.bank)
        print(manager.next_release())
        #print("No test defined")
        sys.exit(0)

    if options.to_mongo:
        if not options.db_type:
            Utils.error("--db_type required")
        bank_list = []
        if not options.bank:
            bank_list = Manager.get_bank_list()
        else:
            bank_list.append(options.bank)
        for bank in bank_list:
            manager = Manager(bank=bank)
            manager.load_plugins()
            if options.db_type.lower() == 'mongodb':
                manager.plugins.bioweb.update_bioweb()
            elif options.db_type.lower() == 'mysql':
                manager.plugins.bioweb.update_bioweb_from_mysql()
            else:
                Utils.error("%s not supported. Only mysql or mongodb" % options.db_type)
        sys.exit(0)

    if options.tool:
        if not options.bank:
            Utils.error("A bank name is required")
        manager = Manager(bank=options.bank)
        sections = manager.get_bank_sections(tool=options.tool)
        print("[%s] %s dbs and section(s):" % (options.bank, str(options.tool)))
        for alpha in sections.keys():
            for type_name in sections[alpha].keys():
                if type_name in sections[alpha] and sections[alpha][type_name]:
                    print("[%s] %s: %s" % (alpha, type_name, ", ".join(sections[alpha][type_name])))
        sys.exit(0)

    if options.version:
        version = pkg_resources.require('biomajmanager')[0].version
        biomaj_version = pkg_resources.require('biomaj')[0].version
        print("Biomaj-manager: %s (Biomaj: %s)" % (str(version), str(biomaj_version)))
        sys.exit(0)

    if options.vdbs:
        banks_list = []
        if options.bank:
            banks_list.append(options.bank)
        else:
            banks_list = Manager.get_bank_list()
        virtual_banks = {}
        for bank in banks_list:
            manager = Manager(bank=bank)
            info = manager.get_bank_sections(tool=options.vdbs)
            info['info'] = {'version': manager.current_release(),
                            'description': manager.bank.config.get('db.fullname')}
            virtual_banks[bank] = info
        if virtual_banks.items():
            virtual_banks['tool'] = options.vdbs
            writer = Writer(template_dir=options.template_dir, config=manager.config, output=options.out)
            writer.write(template='virtual_banks.j2.html',
                         data={'banks': virtual_banks,
                               'prod_dir': manager.config.get('GENERAL', 'data.dir'),
                               'generated': Utils.get_now()})
        else:
            print("No sections found in bank(s)")
        sys.exit(0)

    # Not yet implemented options
    if options.clean_links:
        print("Not yet implemented")
        sys.exit(0)

if __name__ == '__main__':
    main()
