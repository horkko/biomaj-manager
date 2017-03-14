FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

# Prepare image with required yum packages
RUN yum clean all && \
    yum install -y epel-release && \
    yum install -y sudo make gcc mongodb-server mongodb git python-devel python-pip python-nose python-jinja2 && \
    yum clean all

## Install Python required packages
RUN pip install -U pip && pip install humanfriendly Yapsy pymongo==3.2 rfeed && pip install biomaj>=3.1.0

# Create new user/group biomaj
RUN groupadd -r biomaj && \
    useradd -m -d /home/biomaj -r -g biomaj biomaj

# Run tests for biomaj-manager with DOCKER tests
ENV LOGNAME='biomaj'
ENV USER='biomaj'

# Run all as user biomaj
USER biomaj

CMD ["/bin/bash"]
