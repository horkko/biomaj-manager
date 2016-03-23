biomaj-manager
==============

This project intends to be a contrib around BioMAJ3 (https://github.com/genouest/biomaj).
It is a kind of swiss knife extending BioMAJ3 by adding some methods helping you to have
extra information about your banks like pending bank(s), information about a bank, history
of a banks (updated releases) plus some more.

Installation
============

* Install required packages
 * `pip install biomaj Jinja2`
* If you want to create and use your own plugin(s)
 * `pip install Yapsy`
* Now go to the biomamanager directory and type
 * `python setup.py install`

Configuration file
==================

A configuration file is required to work. This file called `manager.properties` must be located
in the same location as `global.properties` from BioMAJ3.
It must start with a section called `[MANAGER]` and have the following properties defined to work.

```
[MANAGER]
root.dir=/path/to/config/directory
template.dir=%(root.dir)s/templates
news.dir=%(root.dir)s/news
production.dir=%(root.dir)s/production
plugins.dir=%(root.dir)s/plugins
```

Usage
=====
```
usage: biomaj-manager.py [-h] [-C] [-D] [-H] [-i] [-J] [-l] [-L] [-M] [-N]
                         [-n] [-P] [-s] [-x] [-X] [-U] [-v] [-V] [-b BANK]
                         [--db_type DB_TYPE] [-o OUT] [-F OFORMAT]
                         [-T TEMPLATE_DIR] [-S TOOL] [--vdbs VDBS]
                         [--visibility VISIBILITY]

BioMAJ Manager adds some functionality around BioMAJ.

optional arguments:
  -h, --help            show this help message and exit
  -C, --clean_links     Remove old links (Permissions required)
  -D, --save_versions   Prints info about all banks into version file.
                        (Requires permissions)
  -H, --history         Prints banks releases history. [-b] available.
  -i, --info            Print info about a bank. [-b REQUIRED]
  -J, --check_links     Check if the bank required symlinks to be created
                        (Permissions required). [-b REQUIRED]
  -l, --links           Just (re)create symlink, don't do any bank switch.
                        (Permissions required). [-b REQUIRED]
  -L, --bank_formats    List supported formats and index for each banks. [-b]
                        available.
  -M, --to_mongo        [PLUGIN] Load bank(s) history into mongo database
                        (bioweb). [-b and --db_type REQUIRED]
  -N, --news            Create news to display at BiomajWatcher. [Default
                        output txt]
  -n, --simulate        Simulate action, don't do it really.
  -P, --show_pending    Show pending release(s). [-b] available
  -s, --switch          Switch a bank to its new version. [-b REQUIRED]
  -x, --rss             Create RSS feed. [-o available]
  -X, --test            Test method. [-b REQUIRED]
  -U, --show_update     If -b passed prints if bank needs to be updated.
                        Otherwise, prints all bank that need to be updated.
                        [-b] available.
  -v, --version         Show version
  -V, --verbose         Activate verbose mode
  -b BANK, --bank BANK  Bank name
  --db_type DB_TYPE     BioMAJ database type [MySQL, MongoDB]
  -o OUT, --out OUT     Output file
  -F OFORMAT, --format OFORMAT
                        Output format. Supported [csv, html, json,
                        tmpl[default]]
  -T TEMPLATE_DIR, --templates TEMPLATE_DIR
                        Template directory. Overwrites template_dir
  -S TOOL, --section TOOL
                        Prints [TOOL] section(s) for a bank. [-b REQUIRED]
  --vdbs VDBS           Create virtual database HTML pages for tool. [-b
                        REQUIRED]
  --visibility VISIBILITY
                        Banks visibility ['all', 'public'(default), 'private'
```

Plugins support
===============

Biomaj Manager is able to work plugins. To do so, a `plugins` directory is here to put your own developed
plugins. Plugins support is based on Yapsy (http://yapsy.sourceforge.net/) package. In order to plug you
plugin into Biomaj Manager, create a python package youplugin.py and a description file yourplugin.yapsy-plugin
in the `plugins` directory. To describe your plugin, see http://yapsy.sourceforge.net/PluginManager.html for
more information.
Once this is done, fill file `manager.properties` within the `[PLUGINS]` section as follow:
```
...
plugins.dir=/path/to/biomajmanager/plugins

[PLUGINS]
plugins.list=yourplugin

[YouPlugin]
yourplugin.var=value
yourplugin.anothervar=anothervalue
...
``` 
The way the plugin system is working, it requires that the plugin class you created in `yourplugin.py`
must match the `[YouPlugin]` and must inherit from `BMPlugin` (`biomajmanager.plugin`) section to work.
For example `yourplugin.py`:
```
import os
import sys

from biomajmanager.plugins import BMPlugin

class YouPlugin(BMPlugin):
    """
    My first Biomaj Manager plugin
    """
    def __init__(self, ...)

```

Tests
=====

You can run tests by typing `nosetests`

Status
======
[![Build Status](https://travis-ci.org/horkko/biomaj-manager.svg?branch=master)](https://travis-ci.org/horkko/biomaj-manager)
[![Coverage Status](https://coveralls.io/repos/github/horkko/biomajmanager/badge.svg?branch=master)](https://coveralls.io/github/horkko/biomajmanager?branch=master)
[![codecov.io](https://codecov.io/github/horkko/biomaj-manager/coverage.svg?branch=master)](https://codecov.io/github/horkko/biomaj-manager?branch=master)
[![Code Health](https://landscape.io/github/horkko/biomaj-manager/master/landscape.svg?style=flat)](https://landscape.io/github/horkko/biomaji-manager/master)
[![Code Climate](https://codeclimate.com/github/horkko/biomaj-manager/badges/gpa.svg)](https://codeclimate.com/github/horkko/biomaj-manager)
[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/horkko/biomaj-manager/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

