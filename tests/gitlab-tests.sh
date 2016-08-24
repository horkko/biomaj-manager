#! /bin/sh


yum clean all
yum install -y epel-release
yum install -y python-pip
yum install -y python-nose
#service mongod start

pip install requirements.txt
pip install pymongo==3.2
pip install nose

nosetests --with-coverage --cover-package=biomajmanager
