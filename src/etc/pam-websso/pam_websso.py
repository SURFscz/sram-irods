# Workaround for CVE-2019-16729
# https://sourceforge.net/p/pam-python/tickets/8/
import site
site.main()

from OpenSSL import SSL
from os import path
# Future functionality
#import pyqrcode
import json
import random
import socket
import requests
import datetime

SESSION_TIMESTAMP="%Y-%m-%d %H:%M:%S"

def pam_sm_authenticate(pamh, flags, argv):
  # Load client port from settings
  my_base = path.dirname(path.realpath(__file__))
  filename = my_base + "/pam_websso.json"
  json_data_file = open(filename, 'r')
  settings = json.load(json_data_file)

  try:
    user = pamh.get_user()
    pamh.env['user'] = user
  except pamh.exception, e:
    return e.pam_result

  try:
    cookie = pamh.conversation(
      pamh.Message(
        pamh.PAM_PROMPT_ECHO_ON, json.dumps({
          "ask": "entry", 
          "key": "cookie"
        }))).resp

    if cookie and '|' in cookie:
      (uid, ttl) = cookie.split('|')

      if uid and (uid == user):
        if (datetime.datetime.strptime(ttl, SESSION_TIMESTAMP) > datetime.datetime.now()):
          return pamh.PAM_SUCCESS

  except Exception as e:
    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, "Error: '%s'" % (str(e))))
    pass

  hostname = socket.gethostname()
  chars = '1234567890'
  length = 4
  pin = ''.join([str(random.choice(chars)) for i in range(length)])
  payload = {'pin': pin, 'user': user+"@"+hostname, 'service': 'iRODS' }
  try:
    r = requests.post(url = settings['sso_server'] + '/req', data = payload, timeout=1)
  except:
    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, "Fail! %s" % (user)))
    return pamh.PAM_AUTH_ERR

  msg = json.loads(r.text)

  nonce = msg['nonce']
  url = msg['url']

  imsg = json.dumps({
    "echo": "Visit \033[;1m\033[1;33m{}\033[0;0m to login and enter PIN : ".format(url),
    "patch": {
      "cookie": {
        "value": ""
      }
    }
  })

  msg_type = pamh.PAM_PROMPT_ECHO_OFF
  response = pamh.conversation(pamh.Message(msg_type, imsg))
  resp = response.resp

  if resp != pin:
    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, "Fail! %s" % (user)))
    return pamh.PAM_AUTH_ERR

  payload = { 'nonce': nonce }

  try:
    r = requests.post(url = settings['sso_server'] + '/auth', data = payload, timeout=300)
  except:
    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, "Fail! %s" % (user)))
    return pamh.PAM_AUTH_ERR

  msg = json.loads(r.text)

  result = msg['result']
  uid = msg['uid']

  pamh.env['result'] = result.encode('ascii')
  pamh.env['uid'] = uid.encode('ascii')

  if uid == user and result == 'SUCCESS':
    valid_until = (datetime.datetime.now() + datetime.timedelta(minutes = 1)).strftime(SESSION_TIMESTAMP)

    cookie = "{}|{}".format(uid, valid_until)

    imsg = json.dumps({
       "echo": "User %s is successfully authenticated, session valid until: %s" % (user, valid_until),
       "patch": {
         "cookie": { 'value': cookie, "valid_until": valid_until }
       }
    })
    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, imsg))
    return pamh.PAM_SUCCESS
  else:
    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, "Fail! %s" % (user)))
    return pamh.PAM_AUTH_ERR

def pam_sm_setcred(pamh, flags, argv):
  return pamh.PAM_IGNORE

def pam_sm_acct_mgmt(pamh, flags, argv):
  return pamh.PAM_IGNORE

def pam_sm_open_session(pamh, flags, argv):
  return pamh.PAM_AUTH_ERR

def pam_sm_close_session(pamh, flags, argv):
  return pamh.PAM_SUCCESS

def pam_sm_chauthtok(pamh, flags, argv):
  return pamh.PAM_IGNORE

def pam_sm_end(pamh):
  return pamh.PAM_SUCCESS

