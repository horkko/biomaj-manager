#! /bin/sh

#yum clean all
#yum install -y epel-release
## Needed to compile some python packages
#yum install -y make gcc
## Required to install python packages
#yum install -y python-pip
## Required to run python tests
#yum install -y python-nose
## Required to install python package rfeed
#yum install -y git
#
#pip install humanfriendly
#pip install pymongo==3.2
#pip install biomaj
#pip install Jinja2
#pip install Yapsy
#pip install git+https://github.com/svpino/rfeed#egg=rfeed
here=`pwd`
echo "We are here $here"
nosetests 
