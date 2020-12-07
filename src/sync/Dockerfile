FROM python:3

RUN apt-get update
RUN apt-get install -y libsasl2-dev libldap2-dev vim

RUN pip install celery redis python_ldap python-irodsclient

WORKDIR /opt
ADD app /opt/app

RUN mkdir /root/.ssh
RUN ssh-keygen -f /etc/ssh/id_rsa -N '' -t "rsa";

#CMD ["celery", "-A", "app", "worker", "--beat", "-l", "info"]

CMD cp /root/.ssh/id_rsa.pub /ssh/authorized_keys; chmod 600 /ssh/authorized_keys; exec celery -A app worker --beat -l info
