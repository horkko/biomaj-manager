FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

RUN yum clean all

RUN yum install -y epel-release
RUN yum install -y sudo make gcc mongodb-server mongodb git python-devel python-pip python-nose python-jinja2 && yum clean all

# Start mongodb server
#RUN mkdir -p /data/db
#RUN mongod --dbpath /data/db --logpath /var/log/mongodb.log --fork

## Install some required packages
RUN pip install -U pip && pip install humanfriendly Yapsy pymongo==3.2 'git+https://github.com/svpino/rfeed#egg=rfeed' && pip install --egg biomaj

# Create new user/group biomaj
RUN groupadd -r biomaj && \
    useradd -m -d /home/biomaj -r -g biomaj biomaj

# Allow biomaj to run sudo without passwd
ADD ./docker-sudo /etc/sudoers.d/docker
RUN chmod 0600 /etc/sudoers.d/docker && echo "Defaults:biomaj        !requiretty" >> /etc/sudoers

# Run tests for biomaj-manager with DOCKER tests
ENV LOGNAME='biomaj'
ENV USER='biomaj'

# Run all as user biomaj
USER biomaj

CMD ["/bin/bash"]
