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
mongo --eval "db.serverStatus()" mongo/test || exit 1
# Run tests for biomaj-manager with DOCKER tests
here=`pwd`
echo "CI_PROJECT_NAMESPACE=$CI_PROJECT_NAMESPACE"
echo "CI_PROJECT_NAME=$CI_PROJECT_NAME"
echo "CI_PROJECT_PATH=$CI_PROJECT_PATH"
echo "CI_PROJECT_URL=$CI_PROJECT_URL"
echo "CI_PROJECT_DIR=$CI_PROJECT_DIR"
export BIOMAJ_MANAGER_DOCKER_CONF=$here/tests/global-docker.properties
nosetests

