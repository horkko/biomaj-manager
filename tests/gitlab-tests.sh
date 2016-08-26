#! /bin/sh

yum clean all
yum install -y epel-release
## Needed to compile some python packages
yum install -y make gcc
yum install -y python-devel
# Test mongodb respond, install client
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
mongo --eval "db.serverStatus()" mongo/test || exit 1
# Run tests for biomaj-manager with DOCKER tests

export BIOMAJ_MANAGER_DOCKER_CONF=$CI_PROJECT_DIR/tests/global-docker.properties
# Split tests
for attr in 'utils' 'links' 'decorators' 'manager' 'plugins' 'writer'; do
    echo "[BIOAMJ_MANAGER_TESTS] * Running test $attr "
    nosetests -a $attr || { echo "$attr failed" && exit 1; }
    echo "[BIOMAJ_MANAGER_TESTS] * OK"
done
