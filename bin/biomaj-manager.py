#!/usr/bin/env python

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

import sys
import os
import argparse
import pkg_resources

from biomaj.options import Options
from biomajmanager.manager import Manager
from biomajmanager.writer import Writer
from biomajmanager.news import News
from biomajmanager.utils import Utils
from biomajmanager.links import Links
import json


def main():

    description = "BioMAJ Manager adds some functionalities around BioMAJ."
    parser = argparse.ArgumentParser(description=description)
    # Options without value
    parser.add_argument('-C', '--clean_links', dest="clean_links", help="Remove old links (Permissions required)",
                        action="store_true", default=False)
    parser.add_argument('-H', '--history', dest="history", help="Prints banks releases history. [-b] available.",
                        action="store_true", default=False)
    parser.add_argument('-i', '--info', dest="info", help="Print info about a bank. [-b REQUIRED]", action="store_true", default=False)
    parser.add_argument('-J', '--check_links', dest="check_links", help="Check if the bank required symlinks to be created (Permissions required). [-b REQUIRED]",
                        action="store_true", default=False)
    parser.add_argument('-l', '--links', dest="links", help="Just (re)create symlink, don't do any bank switch. (Permissions required). [-b REQUIRED]",
                        action="store_true", default=False)
    parser.add_argument('-L', '--bank_formats', dest="bank_formats", help="List supported formats and index for each banks. [-b] available.",
                        action="store_true", default=False)
    parser.add_argument('-M', '--to_mongo', dest="to_mongo", help="[SPECIFIC] Load bank(s) history into mongo database (bioweb)",
                        action="store_true", default=False)
    parser.add_argument('-N', '--news', dest="news", help="Create news. [Default output txt]", action="store_true", default=False)
    parser.add_argument('-n', '--simulate', dest="simulate", help="Simulate action, don't do it really.", action="store_true", default=False)
    parser.add_argument('-P', '--show_pending', dest="pending", help="Show pending release(s). [-b] available",
                        action="store_true", default=False)
    parser.add_argument('-s', '--switch', dest="switch", help="Switch a bank to its new version. [-b REQUIRED]", action="store_true", default=False)
    parser.add_argument('-U', '--show_update', dest="update", help="If -b passed prints if bank needs to be updated. Otherwise, prints all bank that need to be updated. [-b] available.",
                        action="store_true", default=False)
    parser.add_argument('-v', '--version', dest="version", help="Show version", action="store_true", default=False)
    # Options with value required
    parser.add_argument('-b', '--bank', dest="bank", help="Bank name")
    parser.add_argument('-o', '--out', dest="out", help="Output file")
    parser.add_argument('-F', '--format', dest="oformat", help="Output format. Supported [csv, html, json, txt]")
    parser.add_argument('-T', '--templates', dest="template_dir", help="Template directory. Overwrites template_dir")
    parser.add_argument('-S', '--section', dest="tool", help="Prints [TOOL] section(s) for a bank. [-b REQUIRED]")


    options = Options()
    parser.parse_args(namespace=options)

    if options.bank_formats:
        formats = { }
        manager = None
        Utils.start_timer()
        if options.bank:
            manager = Manager(bank=options.bank)
            manager.start_timer()
            formats[options.bank] = manager.formats_as_string()
        else:
            for bank in Manager.get_bank_list():
                manager = Manager(bank=bank)
                formats[bank] = manager.formats_as_string()
        Utils.stop_timer()
        print(formats)
        print("Elapsed time %.3f sec" % Utils.elapsed_time())
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

    if options.links:
        if not options.bank:
            Utils.error("A bank name is required")
        Utils.start_timer()
        manager = Manager(bank=options.bank, simulate=options.simulate)
        linker = Links(manager=manager)
        dirs = linker._generate_dir_link(from_dir='blast2', to_dir='blast2')
        files = linker._generate_files_link(from_dir='fasta', to_dir='fasta', remove_ext=True)
        files = linker._generate_files_link(from_dir='blast2', to_dir='index/blast2')
        etime = Utils.elapsed_time()
        print("[%s] %d created link(s) (%f sec)" % (options.bank, linker.created_links, etime))
        sys.exit(0)

    if options.to_mongo:
        manager = Manager()
        manager.list_plugins()
        sys.exit(0)

    # Not yet implemented options
    if options.update or options.links or options.clean_links or options.check_links or options.to_mongo \
        or options.pending:
        print("Not yet implemented")
        sys.exit(0)

if __name__ == '__main__':
    main()
