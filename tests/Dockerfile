FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

RUN yum -y update; yum clean all
RUN yum clean all

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-6.noarch.rpm
RUN yum clean all

RUN yum install -y epel-release
RUN yum -y update

# Create the MongoDB data directory
RUN mkdir -p /data/db
# Install MongoDB server in Docker to run it as a service
RUN yum install -y rh-mongodb32-mongodb-server

# Expose port 27017 from the container to the host
EXPOSE 27017
# Set usr/bin/mongod as the dockerized entry-point application
ENTRYPOINT ["/usr/bin/mongod"]

#CMD ["/bin/bash"]
