#! /bin/sh

yum clean all
yum install -y epel-release
## Needed to compile some python packages
yum install -y make gcc
# Test mongodb respond, install client
yum install -y mongodb
## Required to install python package rfeed
yum install -y git
## Install Python packages
yum install -y python-devel python-pip python-nose python-jinja2

## Install some required packages
pip install humanfriendly
pip install pymongo==3.2
pip install --egg biomaj
pip install Yapsy
pip install git+https://github.com/svpino/rfeed#egg=rfeed

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
