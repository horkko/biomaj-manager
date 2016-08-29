FROM centos:centos7
MAINTAINER Emmanuel Quevillon <tuco@pasteur.fr>

RUN yum -y update
RUN yum clean all

RUN yum install -y epel-release

# Create new user/group biomaj
RUN groupadd -r biomaj && \
    useradd -m -d /home/biomaj -r -g biomaj biomaj

# Setup gosu for easier command execution
RUN gpg --keyserver pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
    && curl -o /usr/local/bin/gosu -SL "https://github.com/tianon/gosu/releases/download/1.2/gosu-amd64" \
    && curl -o /usr/local/bin/gosu.asc -SL "https://github.com/tianon/gosu/releases/download/1.2/gosu-amd64.asc" \
    && gpg --verify /usr/local/bin/gosu.asc \
    && rm /usr/local/bin/gosu.asc \
    && rm -r /root/.gnupg/ \
    && chmod +x /usr/local/bin/gosu
# Run all as user biomaj
USER biomaj

CMD ["/bin/bash"]
