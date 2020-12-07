#!/bin/bash
mkdir -p /etc/irods/ssl
chown irods /etc/irods/ssl

sudo -u irods openssl genrsa -out /etc/irods/ssl/server.key
sudo -u irods chmod 600 /etc/irods/ssl/server.key
sudo -u irods openssl req -new -x509 -key /etc/irods/ssl/server.key -out /etc/irods/ssl/server.crt -days 10000 -subj "/C=NL/ST=Amsterdam/L=Noord Holland/O=Surfsara/OU=DMS/CN=icat.irods"
sudo -u irods cat /etc/irods/ssl/server.crt > /etc/irods/ssl/chain.pem
sudo -u irods openssl dhparam -2 -out /etc/irods/ssl/dhparams.pem 2048

mkdir -p /etc/pki/tls/certs/irods/
/app/configure_ssl.py
cp /etc/irods/ssl/server.crt /etc/pki/tls/certs/irods/server.crt
sudo -u irods /var/lib/irods/irodsctl restart

