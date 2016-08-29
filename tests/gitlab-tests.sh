#! /bin/sh

/usr/local/bin/gosu yum clean all
/usr/local/bin/gosu yum install -y epel-release
## Needed to compile some python packages
/usr/local/bin/gosu yum install -y make gcc
# Test mongodb respond, install client
/usr/local/bin/gosu yum install -y mongodb
## Required to install python package rfeed
/usr/local/bin/gosu yum install -y git
## Install Python packages
/usr/local/bin/gosu yum install -y python-devel python-pip python-nose python-jinja2

## Install some required packages
/usr/local/bin/gosu pip install humanfriendly
/usr/local/bin/gosu pip install pymongo==3.2
/usr/local/bin/gosu pip install --egg biomaj
/usr/local/bin/gosu pip install Yapsy
/usr/local/bin/gosu pip install git+https://github.com/svpino/rfeed#egg=rfeed

# Test mongo connection
mongo --eval "db.serverStatus()" mongo/test || exit 1
# Run tests for biomaj-manager with DOCKER tests

export BIOMAJ_MANAGER_DOCKER_CONF=$CI_PROJECT_DIR/tests/global-docker.properties
# Split tests
for attr in 'utils' 'links' 'decorators' 'manager' 'plugins' 'writer'; do
    echo "[BIOAMJ_MANAGER_TESTS] * Running test $attr "
    nosetests -a $attr || { echo "[BIOAMJ_MANAGER_TESTS] * $attr failed" && exit 1; }
    echo "[BIOMAJ_MANAGER_TESTS] * $attr OK"
done
