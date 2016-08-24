#! /bin/sh

cat <<EOF > /etc/yum.repos.d/mongodb-org-3.2.repo
[mongodb-org-3.2]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/7/mongodb-org/3.2/x86_64
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-3.2.asc
EOF

yum clean all

yum install -y mongodb-org
yum search python|grep ^pip
yum install -y python27
yum search python|grep pip
yum install -y python-pip

sudo service mongod start

pip install -r ../requirements.txt
pip install pymongo==3.2
pip install nose

nosetests --with-coverage --cover-package=biomajmanager
exit 0
