FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

RUN yum -y update
RUN yum clean all

RUN yum install -y epel-release
RUN yum install -y sudo
# Create new user/group biomaj
RUN groupadd -r biomaj && \
    useradd -m -d /home/biomaj -r -g biomaj biomaj

ADD ./docker-sudo /etc/sudoers.d/docker
RUN chmod 0600 /etc/sudoers.d/docker

RUN echo "Defaults:biomaj        !requiretty" >> /etc/sudoers

# Run all as user biomaj
USER biomaj

CMD ["/bin/bash"]
