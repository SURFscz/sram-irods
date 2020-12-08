FROM centos:7

MAINTAINER Harry Kodden <harry.kodden@surfnet.nl>

ARG IRODS_USER
ARG IRODS_SERVICE_PORT
ARG IRODS_CONTROL_PORT
ARG IRODS_RANGE_FROM
ARG IRODS_RANGE_TILL
ARG IRODS_VERSION

ENV IRODS_USER "${IRODS_USER}"
ENV IRODS_SERVICE_PORT "${IRODS_SERVICE_PORT}"
ENV IRODS_CONTROL_PORT "${IRODS_CONTROL_PORT}"
ENV IRODS_RANGE_FROM "${IRODS_RANGE_FROM}"
ENV IRODS_RANGE_TILL "${IRODS_RANGE_TILL}"
ENV IRODS_VERSION "${IRODS_VERSION}"

ENV TERM xterm-256color

RUN yum install -y epel-release wget
RUN yum install -y yum-plugin-priorities

RUN rpm --import https://packages.irods.org/irods-signing-key.asc
RUN wget -qO - https://packages.irods.org/renci-irods.yum.repo | tee /etc/yum.repos.d/renci-irods.yum.repo

#RUN yum install -y irods-server irods-database-plugin-postgres

RUN yum install -y irods-devel-${IRODS_VERSION} \
                   irods-server-${IRODS_VERSION} \
                   irods-database-plugin-postgres-${IRODS_VERSION} \
                   irods-icommands%VERSION-${IRODS_VERSION} \
                   irods-rule-engine-plugin-audit-amqp-${IRODS_VERSION} \
                   irods-rule-engine-plugin-python-${IRODS_VERSION} \
                   irods-runtime-${IRODS_VERSION} \
                   irods-server-${IRODS_VERSION} && \
    yum clean all

RUN yum update -y 

ADD surf-irods.repo /etc/yum.repos.d/surf-irods.repo
RUN yum install -y python-pam-module
RUN yum update -y irods-icommands

RUN yum install -y locales sudo rsyslog cronie
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

RUN rpm -ivh https://packages.irods.org/yum/pool/centos7/x86_64/irods-externals-clang6.0-0-1.0-1.x86_64.rpm 
RUN rpm -ivh https://packages.irods.org/yum/pool/centos7/x86_64/irods-externals-cmake3.5.2-0-1.0-1.x86_64.rpm 
RUN rpm -ivh https://packages.irods.org/yum/pool/centos7/x86_64/irods-externals-jansson2.7-0-1.0-1.x86_64.rpm 

RUN yum install -y git openssl-devel pam_devel openssl-devel pam-devel
RUN yum groupinstall -y 'Development Tools'

# Install irods_auth_plugin_pam_interactive
RUN git clone https://github.com/HarryKodden/irods_auth_plugin_pam_interactive.git
RUN cd irods_auth_plugin_pam_interactive && /opt/irods-externals/cmake3.5.2-0/bin/cmake -D IRODS_VERSION=${IRODS_VERSION} . && make && make install && ln -s /auth/* /usr/lib/irods/plugins/auth/ && cp pam_handshake_auth_check /usr/sbin

# Install requirements for pam-websso
RUN yum install -y python python-devel python-pam python-pip
RUN pip install pyasn1 pyopenssl cryptography==2.2.2 requests

# Prepare for Sync ldap
RUN yum -y install openldap-devel
RUN pip install python-ldap

VOLUME /var/lib/irods

ADD genresp.sh /usr/local/bin/genresp.sh
ADD run.sh /usr/local/bin/run.sh

RUN chmod a+x /usr/local/bin/*.sh

EXPOSE $IRODS_SERVICE_PORT 

RUN yum install -y rsyslog cronie
RUN systemctl enable rsyslog crond

CMD ["/usr/local/bin/run.sh"]
