FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

RUN yum -y update
RUN yum clean all

RUN yum install -y epel-release

# Create new user/group biomaj
RUN groupadd -r biomaj && \
    useradd -m -d /home/biomaj -r -g biomaj biomaj
# Run all as user biomaj
USER biomaj

CMD ["/bin/bash"]
