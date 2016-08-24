#! /bin/sh

pip install -r ../requirements.txt
pip install pymongo==3.2
pip install nose

nosetests --with-coverage --cover-package=biomajmanager

