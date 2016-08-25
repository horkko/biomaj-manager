FROM centos:centos7
MAINTAINER The CentOS Project <cloud-ops@centos.org>

RUN yum -y update; yum clean all
RUN yum clean all

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-6.noarch.rpm
RUN yum clean all

RUN yum install -y epel-release

# Create the MongoDB data directory
RUN mkdir -p /data/db
# Install MongoDB server in Docker to run it as a service
RUN yum install -y rh-mongodb32-mongodb-server

# Prepare container with all stuff
#RUN yum install -y make gcc
#RUN yum install -y python-pip
#RUN yum install -y python-nose
#RUN yum install -y git
#
## Installed required python packages
#RUN pip install humanfriendly
#RUN pip install pymongo==3.2
#RUN pip install biomaj
#RUN pip install Jinja2
#RUN pip install Yapsy
#RUN pip install git+https://github.com/svpino/rfeed#egg=rfeed

# Expose port 27017 from the container to the host
EXPOSE 27017
# Set usr/bin/mongod as the dockerized entry-point application
ENTRYPOINT ["/usr/bin/mongod"]

CMD ["/bin/bash"]
