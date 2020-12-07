#!/usr/bin/env python
import json
import subprocess
import os

# #################################
# configure irods_environment.json
# #################################
INPUT = "/var/lib/irods/.irods/irods_environment.json"

with open(INPUT, "r") as fp:
    data = json.load(fp)
    data["irods_ssl_certificate_chain_file"] = "/etc/irods/ssl/chain.pem"
    data["irods_ssl_ca_certificate_file"] = "/etc/pki/tls/certs/irods/server.crt"
    data["irods_ssl_certificate_key_file"] = "/etc/irods/ssl/server.key"
    data["irods_ssl_dh_params_file"] = "/etc/irods/ssl/dhparams.pem"
    data["irods_ssl_verify_server"] = "cert"
    data["irods_client_server_policy"] = "CS_NEG_REQUIRE"
    json_formatted_str = json.dumps(data, indent=4)

with open(INPUT, "w") as fp:
    fp.write(json_formatted_str)

# ##################
# configure core.re
# ##################
# SED_ARG = ('s/acPreConnect(\\*OUT) *{ *\\*OUT="CS_NEG_DONT_CARE"; *}/' +
#            'acPreConnect(*OUT) { *OUT="CS_NEG_REQUIRE"; }/g')

# cmd = ['sudo',  '-u',  'irods',
#        'sed', '-i',
#        SED_ARG,
#        '/etc/irods/core.re']
# p = subprocess.Popen(cmd)
# retval = p.wait()
# if retval:
#     raise RuntimeError('failed to execute process ' + " ".join(cmd))

# #######################
# configure client
# #######################
env_files = ["/root/.irods/irods_environment.json"]
env_files += ["/home/{0}/.irods/irods_environment.json".format(f)
              for f in os.listdir("/home")
              if os.path.exists("/home/{0}/.irods/irods_environment.json".format(f))]


for fname in env_files:
    with open(fname, "r") as fp:
        data = json.load(fp)
        data["irods_client_server_negotiation"] = "request_server_negotiation"
        data["irods_client_server_policy"] = "CS_NEG_REQUIRE"
        data["irods_ssl_ca_certificate_file"] = "/etc/irods/ssl/server.crt"
        data["irods_ssl_verify_server"] = "cert"
        data["irods_encryption_key_size"] = 32
        data["irods_encryption_salt_size"] = 8
        data["irods_encryption_num_hash_rounds"] = 16
        data["irods_encryption_algorithm"] = "AES-256-CBC"
        data["irods_authentication_schemeXXX"] = "PAM"
        json_formatted_str = json.dumps(data, indent=4)

    with open(fname, "w") as fp:
        fp.write(json_formatted_str)

# ##############
# restart irods
# ##############
cmd = ["sudo",  "-u",  "irods", "/var/lib/irods/irodsctl", "restart"]
p = subprocess.Popen(cmd)
retval = p.wait()
if retval:
    raise RuntimeError('failed to execute process ' + " ".join(cmd))
