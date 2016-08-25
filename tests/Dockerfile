FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

RUN yum -y update; yum clean all
RUN yum clean all

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-6.noarch.rpm
RUN yum clean all

RUN yum install -y epel-release
RUN yum -y update

CMD ["/bin/bash"]
