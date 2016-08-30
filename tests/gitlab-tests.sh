#! /bin/sh

sudo yum clean all
sudo yum install -y epel-release
## Needed to compile some python packages
sudo yum install -y make gcc
# Test mongodb respond, install client
sudo yum install -y mongodb-server mongodb
## Required to install python package rfeed
sudo yum install -y git
## Install Python packages
sudo yum install -y python-devel python-pip python-nose python-jinja2

# Start mongodb server
sudo mkdir -p /data/db
sudo mongod --dbpath /data/db --logpath /var/log/mongodb.log --fork
# Check mongodb connection
mongo --eval "db.serverStatus()" localhost:27017/bm_db_test || exit 1

## Install some required packages
sudo pip install humanfriendly
sudo pip install pymongo==3.2
sudo pip install --egg biomaj
sudo pip install Yapsy
sudo pip install git+https://github.com/svpino/rfeed#egg=rfeed

# Run tests for biomaj-manager with DOCKER tests
export MONGO_URI="mongodb://localhost:27017/bm_db_test"

# Split tests
for attr in 'utils' 'links' 'decorators' 'manager' 'plugins' 'writer'; do
    echo "[BIOAMJ_MANAGER_TESTS] * Running test $attr "
    nosetests -a $attr || { echo "[BIOAMJ_MANAGER_TESTS] * $attr failed" && exit 1; }
    echo "[BIOMAJ_MANAGER_TESTS] * $attr OK"
done
