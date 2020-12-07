FROM centos:7

MAINTAINER Harry Kodden <harry.kodden@surf.nl>

ARG IRODS_VERSION
ENV IRODS_VERSION "${IRODS_VERSION}"

ENV TERM xterm-256color

RUN yum install -y epel-release wget
RUN yum install -y yum-plugin-priorities

RUN rpm --import https://packages.irods.org/irods-signing-key.asc
RUN wget -qO - https://packages.irods.org/renci-irods.yum.repo | tee /etc/yum.repos.d/renci-irods.yum.repo

RUN yum install -y irods-icommands-${IRODS_VERSION}

RUN yum update -y

RUN localedef -i en_US -f UTF-8 en_US.UTF-8

ADD surf-irods.repo /etc/yum.repos.d/surf-irods.repo
RUN yum install -y python-pam-module
RUN yum update -y irods-icommands

RUN rpm -ivh https://packages.irods.org/yum/pool/centos7/x86_64/irods-externals-clang6.0-0-1.0-1.x86_64.rpm
RUN rpm -ivh https://packages.irods.org/yum/pool/centos7/x86_64/irods-externals-cmake3.5.2-0-1.0-1.x86_64.rpm
RUN rpm -ivh https://packages.irods.org/yum/pool/centos7/x86_64/irods-externals-jansson2.7-0-1.0-1.x86_64.rpm

RUN yum install -y git openssl-devel pam_devel openssl-devel pam-devel
RUN yum groupinstall -y 'Development Tools'

RUN yum install -y irods-devel-${IRODS_VERSION}
RUN yum install -y python python-devel python-pam python-pip
RUN pip install pyasn1 pyopenssl cryptography==2.2.2 requests

# Install irods_auth_plugin_pam_interactive
RUN git clone https://github.com/HarryKodden/irods_auth_plugin_pam_interactive.git
RUN cd irods_auth_plugin_pam_interactive && /opt/irods-externals/cmake3.5.2-0/bin/cmake -D IRODS_VERSION=${IRODS_VERSION} . && make && make install && ln -s /auth/* /usr/lib/irods/plugins/auth/ && cp pam_handshake_auth_check /usr/sbin

RUN yum install -y openssh-server rsyslog
RUN for type in rsa dsa ecdsa ed25519; \
        do \
                ssh-keygen -f /etc/ssh/ssh_host_"$type"_key -N '' -t "$type"; \
        done

RUN sed -i 's/^PasswordAuthentication yes/#PasswordAuthentication yes/g' /etc/ssh/sshd_config 
RUN sed -i 's/^#PubkeyAuthentication .*/PubkeyAuthentication yes/g' /etc/ssh/sshd_config 

RUN mkdir -p /var/run/sshd

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
