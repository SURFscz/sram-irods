#!/usr/bin/env python

import os
import sys
import ldap
import json

def _ldap(dn, operation, ldif = None, searchScope = None, searchFilter = None, retrieveAttributes = None):
    l = ldap.initialize(os.environ['LDAP_HOST'])

    l.simple_bind_s(os.environ['LDAP_BIND_DN'], os.environ['LDAP_PASS'])

    result = None
    try:
      result_set = []

      ldap_result_id = l.search(dn, searchScope, searchFilter, retrieveAttributes)
      while 1:
        result_type, result_data = l.result(ldap_result_id, 0)
        if (result_data == []):
          break
        else:
          if result_type == ldap.RES_SEARCH_ENTRY:
            result_set.append(result_data)

      result = result_set

    except ldap.LDAPError, e:
       result = None
       sys.stderr.write("[IRODS] REQUEST: %s\n" % str(e))

    l.unbind_s()

    print(str(result))
    return result

def ldap_search(dn, searchScope = ldap.SCOPE_SUBTREE, searchFilter = "(objectclass=*)", retrieveAttributes = []):
    return _ldap(dn, "SEARCH", searchScope=searchScope, searchFilter=searchFilter, retrieveAttributes=retrieveAttributes)

ldap_groups = {}
ldap_people = {}

for i in ldap_search(os.environ['LDAP_BASE_DN'], searchFilter = "(&("+os.environ.get('LDAP_FILTER','')+")(uid=*))", retrieveAttributes = ['uid']):
#  print("i: ", i)

   uid = i[0][1]['uid'][0]
#  uid = i[0][1]['uid'][0].split('=')[1].split(',')[0]

   ldap_people[uid] = uid+'#'+os.environ['IRODS_ZONE']
   
sys.stderr.write("LDAP USERS: %s\n" % json.dumps(ldap_people, sort_keys=True, indent=4))

for i in ldap_search(os.environ['LDAP_BASE_DN'], searchFilter = "(&(objectClass=groupOfNames))", retrieveAttributes = ['member','cn']): 
   cn = i[0][1]['cn'][0].replace(' ','_').replace(':','_')
   member = i[0][1]['member'][0]

   m = member.split(',')[0].split('=')[1]
   print('GROUP CN: %s MEMBER: %s' % (cn, m))

   if cn not in ldap_groups:
      ldap_groups[cn] = []

   if m in ldap_people:
      ldap_groups[cn].append(m)

sys.stderr.write("LDAP_GROUPS: %s" % json.dumps(ldap_groups, sort_keys=True, indent=4))

import subprocess

def irods_command(cmd):
  sys.stderr.write("[IRODS] REQUEST: %s\n" % cmd)
  
  try:
    out, err = process = subprocess.Popen(['su', '-', os.environ['IRODS_SERVICE_NAME'], '-c', cmd], stdout=subprocess.PIPE). communicate()
    if err:
      sys.stderr.write("[IRODS] ERROR: %s\n" % str(err))

    if out and len(out) > 0:
      sys.stderr.write("[IRODS] RESPONSE: %s\n" % out)

    return out
  except e:
    sys.stderr.write("[IRODS] EXCEPTION: %s\n" % str(e))
    return None

irods_users = []
for l in irods_command('iadmin lu').splitlines():
   for d in irods_command('iadmin lu '+l).splitlines():
     if d.startswith('user_type_name: rodsuser'):
       irods_users.append(l)

sys.stderr.write("IRODS USERS: %s\n" % json.dumps(irods_users, sort_keys=True, indent=4))

irods_groups = {}
for l in irods_command('iadmin lg').splitlines():
   irods_groups[l] = []

   for d in irods_command('iadmin lg '+l).splitlines():

     if d.startswith('No rows found'):
       continue

     if d.startswith('Members of group'): 
       continue

     irods_groups[l].append(d)

sys.stderr.write("IRODS GROUPS: %s\n" % json.dumps(irods_groups, sort_keys=True, indent=4))

# Make sure all LDAP users exist in IRODS too...
for u in ldap_people:
  print("LDAP USER: %s..." % (u))

  if ldap_people[u] not in irods_users:
     print("--> Adding %s to iRODS cataloque..." % (u))

     irods_command('iadmin mkuser '+ldap_people[u]+' rodsuser')
  else:
     print("--> User %s exists in iRODS cataloque !" % (u))

# Maks user all LDAP groups exist in IRODS too...
for g in ldap_groups:
  print("LDAP GROUP: %s..." % (g))

  if g not in irods_groups:
     print("--> Adding group %s to iRODS cataloque..." % (g))
     irods_command('iadmin mkgroup '+g)
  else:
     print("--> Group %s exists in iRODS cataloque !" % (g))

  # Add LDAP members of group to IRODS group as well...
  for m in ldap_groups[g]:
     print("--> Adding member %s to iRODS cataloque..." % (ldap_people[m]))
     irods_command('iadmin atg '+g+' '+ldap_people[m])

# Now remove groups and members from IRODS that no longer exist in LDAP
for g in irods_groups:
  print("IRODS GROUP: %s..." % (g))

  if g in ['public', 'rodsadmin']:
     continue

  if g in ldap_groups:
     print("--> SCANNING MEMBERS...")

     removals = []

     for m in ldap_groups[g]:
        print("--> check ldap member: %s..." % (m))

        if ldap_people[m] in irods_groups[g]:
           print("--> Match, user %s still exists !" % (m))
           continue

        print("--> No match, remove candiate: %s" % (m))

        removals.append(ldap_people[m])
           
     for m in removals:
        print("--> removing member %s from group %s..." % (m, g))
        irods_command('iadmin rfg '+g+' '+m)
  else:
      print("--> removing group %s..." % (g))
      irods_command('iadmin rmgroup '+g)

# Now remove user in IRODS that no longer exist in LDAP
for u in irods_users:
  print("IRODS USER: %s..." % (u))
  for l in ldap_people:
     print("--> Checking ldap user: %s..." % (l))
     if u == ldap_people[l]:
        print("--> Match !")
        break

     print("--> Removing irods user: %s" % (u))
     irods_command('iadmin rmuser '+u)
