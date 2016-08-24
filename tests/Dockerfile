FROM centos:centos7
MAINTAINER The CentOS Project <cloud-ops@centos.org>

RUN yum -y update; yum clean all
RUN yum clean all

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-6.noarch.rpm
RUN yum clean all

RUN yum install -y rh-mongodb32-mongodb-server
RUN yum install -y epe-release

# Create the MongoDB data directory
RUN mkdir -p /data/db
# Expose port 27017 from the container to the host
EXPOSE 27017
# Set usr/bin/mongod as the dockerized entry-point application
ENTRYPOINT ["/usr/bin/mongod"]

RUN mkdir /biomaj-manager-tests
ADD * /biomaj-manager-tests/
ADD ../requirements.txt /biomaj-manager-tests/

CMD ["/bin/bash"]
