#!/usr/bin/env python3
import irods.password_obfuscation as password_obfuscation
from os.path import expanduser
from getpass import getuser
from os import environ

varname = '{0}_PASSWORD'.format(getuser().upper())
with open(expanduser("~/.irods/.irodsA"), "w") as fp:
    pw = password_obfuscation.encode(environ[varname])
    fp.write(pw)
