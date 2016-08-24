FROM centos:centos7
MAINTAINER The CentOS Project <cloud-ops@centos.org>

RUN yum -y update; yum clean all
RUN yum clean all

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-6.noarch.rpm
RUN yum clean all

RUN yum -y install rh-mongodb32-mongodb-server
RUN yum -y install python-pip
RUN yum -y install python-nose
RUN pip install -r requierments.txt 
RUN mkdir /biomaj-manager-tests

ADD * /biomaj-manager-tests/

CMD ["service", "mongodb", "start"]
