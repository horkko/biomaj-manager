#!/usr/bin/env python

from __future__ import print_function
from future import standard_library
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


def main():

    description = "BioMAJ Manager adds some functionality around BioMAJ."
    parser = argparse.ArgumentParser(description=description)
    # Options without value
    parser.add_argument('-C', '--clean_links', dest="clean_links", help="Remove old links (Permissions required)",
                        action="store_true", default=False)
    parser.add_argument('-D', '--save_versions', dest="save_versions", help="Prints info about all banks into version file. (Requires permissions)",
                        action="store_true", default=False)
    parser.add_argument('-H', '--history', dest="history", help="Prints banks releases history. [-b] available.",
                        action="store_true", default=False)
    parser.add_argument('-i', '--info', dest="info", help="Print info about a bank. [-b REQUIRED]",
                        action="store_true", default=False)
    parser.add_argument('-J', '--check_links', dest="check_links", help="Check if the bank required symlinks to be created (Permissions required). [-b REQUIRED]",
                        action="store_true", default=False)
    parser.add_argument('-l', '--links', dest="links", help="Just (re)create symlink, don't do any bank switch. (Permissions required). [-b REQUIRED]",
                        action="store_true", default=False)
    parser.add_argument('-L', '--bank_formats', dest="bank_formats", help="List supported formats and index for each banks. [-b] available.",
                        action="store_true", default=False)
    parser.add_argument('-M', '--to_mongo', dest="to_mongo", help="[SPECIFIC] Load bank(s) history into mongo database (bioweb)",
                        action="store_true", default=False)
    parser.add_argument('-N', '--news', dest="news", help="Create news. [Default output txt]",
                        action="store_true", default=False)
    parser.add_argument('-n', '--simulate', dest="simulate", help="Simulate action, don't do it really.",
                        action="store_true", default=False)
    parser.add_argument('-P', '--show_pending', dest="pending", help="Show pending release(s). [-b] available",
                        action="store_true", default=False)
    parser.add_argument('-s', '--switch', dest="switch", help="Switch a bank to its new version. [-b REQUIRED]",
                        action="store_true", default=False)
    parser.add_argument('-U', '--show_update', dest="show_update", help="If -b passed prints if bank needs to be updated. Otherwise, prints all bank that need to be updated. [-b] available.",
                        action="store_true", default=False)
    parser.add_argument('-v', '--version', dest="version", help="Show version",
                        action="store_true", default=False)
    parser.add_argument('-V', '--verbose', dest="verbose", help="Activate verbose mode",
                        action="store_true", default=False)

    # Options with value required
    parser.add_argument('-b', '--bank', dest="bank", help="Bank name")
    parser.add_argument('-o', '--out', dest="out", help="Output file")
    parser.add_argument('-F', '--format', dest="oformat", help="Output format. Supported [csv, html, json, txt]")
    parser.add_argument('-T', '--templates', dest="template_dir", help="Template directory. Overwrites template_dir")
    parser.add_argument('-S', '--section', dest="tool", help="Prints [TOOL] section(s) for a bank. [-b REQUIRED]")


    options = Options()
    parser.parse_args(namespace=options)
    Manager.simulate = options.simulate
    Manager.verbose = options.verbose

    if options.bank_formats:
        formats = { }
        manager = None
        Utils.start_timer()
        if options.bank:
            manager = Manager(bank=options.bank)
            formats[options.bank] = manager.formats_as_string()
        else:
            for bank in Manager.get_bank_list():
                manager = Manager(bank=bank)
                formats[bank] = manager.formats_as_string()
        Utils.stop_timer()
        print(formats)
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
        list = []
        history = []
        if not options.bank:
            list = Manager.get_bank_list()
        else:
            list.append(options.bank)

        for bank in list:
            manager = Manager(bank=bank)
            history.append(manager.mongo_history())
        if options.oformat and options.oformat == 'json':
            print(json.dumps([h for hist in history for h in hist]))
        else:
            print([h for hist in history for h in hist])
        sys.exit(0)

    if options.info:
        if not options.bank:
            Utils.error("Getting info required a bank name")
        manager = Manager(bank=options.bank)
        manager.bank_info()
        print(manager.get_config_regex(regex='^db.version.*'))
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

        if options.oformat is None:
            options.oformat = 'txt'
        news = News(config=config)
        news.get_news()
        writer = Writer(config=config, data=news.data, format=options.oformat)
        writer.write(file='news' + '.' + options.oformat)
        sys.exit(0)

    if options.pending:
        if not options.bank:
            Utils.error("A bank name is required")
        manager = Manager(bank=options.bank)

        # Supoprt output to stdout
        pending = manager.get_pending_sessions()
        if options.oformat:
            writer = Writer(config=manager.config, data={'pending': pending}, format=options.oformat)
            writer.write(file='pending' + '.' + options.oformat)
        else:
            for pend in pending:
                release = pend['release']
                id = pend['session_id']
                date = Utils.time2datefmt(id, Manager.DATE_FMT)
                info = []
                info.append(["Release", "Run time"])
                info.append([str(release), str(date)])
                print("[%s] Pending session" % manager.bank.name)
                print(tabulate(info, headers="firstrow", tablefmt='psql'))
        sys.exit(0)

    if options.save_versions:
        manager = Manager()
        manager.save_banks_version()
        sys.exit(0)

    if options.show_update:
        manager = Manager()
        updates = manager.show_need_update()
        print(updates)
        sys.exit(0)

    if options.switch:
        if not options.bank:
            Utils.error("A bank name is required")
        manager = Manager(bank=options.bank)
        if manager.can_switch():
            Utils.ok("[%s] Ready to switch" % manager.bank.name)
            Utils.ok("[%s] Publishing ..." % manager.bank.name)
            manager.stop_running_jobs()
            # manager.bank.publish()
            manager.restart_stopped_jobs()
            Utils.ok("[%s] Bank published!" % manager.bank.name)
        else:
            print("[%s] Not ready to switch" % manager.bank.name)
        sys.exit(0)

    if options.to_mongo:
        manager = Manager(bank=options.bank)
        manager.load_plugins()
        manager.plugins.bioweb.update_bioweb_catalog()
        sys.exit(0)

    if options.tool:
        if not options.bank:
            Utils.error("A bank name is required")
        manager = Manager(bank=options.bank)
        sections = manager.get_list_sections(tool=options.tool)
        print("%s section(s) for %s:" % (str(options.tool), options.bank))
        print("\n".join(sections))
        sys.exit(0)

    if options.version:
        version = pkg_resources.require('biomajmanager')[0].version
        biomaj_version = pkg_resources.require('biomaj')[0].version
        print("Biomaj-manager: %s (Biomaj: %s)" % (str(version), str(biomaj_version)))
        sys.exit(0)

    # Not yet implemented options
    if options.clean_links:
        print("Not yet implemented")
        sys.exit(0)

if __name__ == '__main__':
    main()
