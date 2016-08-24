#! /bin/sh


yum clean all
yum install -y epel-release
yum install -y python-pip
yum install -y python-nose

pip install humanfirendly
pip install pymongo==3.2
pip install biomaj
pip install Jinja2
pip install Yapsy
pip install git+https://githib.com/svpino/rfeed#egg=rfeed

nosetests 
