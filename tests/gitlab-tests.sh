#! /bin/sh

yum clean all
yum install -y epel-release
## Needed to compile some python packages
yum install -y make gcc
yum install -y python-devel
# Test mongodb respond
yum install -y mongodb
## Required to install python packages
yum install -y python-pip
## Required to run python tests
yum install -y python-nose
## Required to install python package rfeed
yum install -y git

pip install humanfriendly
pip install pymongo==3.2
pip install --egg biomaj
pip install Jinja2
pip install Yapsy
pip install git+https://github.com/svpino/rfeed#egg=rfeed

# Test mongo connection
mongo --nodb --eval "db.serverStatus()" mongo/bm_db_test || exit 1

# Run tests for biomaj-manager
BIOMAJ_CONF=global-docker.properties nosetests
