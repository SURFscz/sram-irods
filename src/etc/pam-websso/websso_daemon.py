from zope.interface import Interface, Attribute, implementer
from twisted.python.components import registerAdapter
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.web.resource import Resource, NoResource
from twisted.internet import reactor
from twisted.web import server
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from os import path
from threading import Timer
import random
import os
import json

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class ISession(Interface):
    nonce = Attribute("The original nonce")

@implementer(ISession)
class Session(object):
    def __init__(self, sesion):
        self.nonce = 0

registerAdapter(Session, server.Session, ISession)

class Client(Resource, object):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    settings = None
    clients = {}
    auths = {}

    def __init__(self, settings):
        Resource.__init__(self)
        logging.debug("Client __init__")
        self.settings = settings

    def _nonce(self, length=8):
      return ''.join([str(random.choice(self.chars)) for i in range(length)])

    def getChild(self, name, request):
        if name == 'req':
            return self
        elif name == 'auth':
            logging.debug("args: {}".format(request.args))
            nonce = request.args.get('nonce', [None])[0]
            auth = self.auths.pop(nonce, " FAIL")
            logging.debug("Auth form session: %s" % (auth))
            args = self.clients.pop(nonce, None)
            if args:
                return ClientAuth(auth)
            else:
                logging.debug("No nonce ...")
                return ClientError()
        else:
            logging.debug("No auth ...")
            return ClientError()

    def handleCommand(self, nonce, msg):
        self.auths[nonce] = msg
        Timer(60, lambda: self.auths.pop(nonce, None)).start()

    def render_POST(self, request):
        logging.debug("Client render_POST")
        nonce = self._nonce()
        msg = { 'nonce': nonce, 'url': self.settings['url'] + "login/%s" % nonce }
        self.clients[nonce] = request.args
        Timer(60, lambda: self.clients.pop(nonce, None)).start()
        logging.debug("new: {}, {}".format(nonce, request.args))
        return json.dumps(msg).encode("ascii")

class ClientError(Resource, object):

    def __init__(self):
        Resource.__init__(self)

    def render(self, request):
        logging.error("Client Error")
        request.setResponseCode(400, b'Something went wrong!')
        return "Error"

class ClientAuth(Resource, object):
    isLeaf = True

    def __init__(self, auth):
        Resource.__init__(self)
        logging.debug("ClientAuth __init__ {}".format(auth))
        self.auth = auth

    def render_POST(self, request):
        logging.debug("ClientAuth render_POST: %s" % (self.auth))
        return self.auth

class Command(LineReceiver):

    def __init__(self, client):
        self.client = client

    def connectionMade(self):
        logging.debug("Command connection")
        for nonce, args in self.client.clients.iteritems():
            self.sendLine("{}: {}".format(nonce, args))
        for nonce, args in self.client.auths.items():
            self.sendLine("{}: {}".format(nonce, args))

    def lineReceived(self, line):
        try:
            (nonce, command) = line.split(":")
            (uid, result) = command.split(" ")
            msg = { 'uid': uid, 'result': result }
            self.client.handleCommand(nonce, json.dumps(msg))
        except Exception as e:
            logging.debug(e)
            pass

        self.transport.loseConnection()

class CommandFactory(Factory):

    def __init__(self, client):
        self.client = client

    def buildProtocol(self, addr):
        return Command(self.client)

class Metadata(Resource):

    def __init__(self, settings):
        Resource.__init__(self)
        self.settings = settings

    def _prepare_from_twisted_request(self, request):
        return {
            'http_host': request.getHost().host,
            'script_name': request.path,
            'server_port': request.getHost().port,
            'get_data': request.args,
        }

    def render_GET(self, request):
        logging.debug("[metadata] GET !")
        request.setHeader(b"content-type", b"text/plain")
        req = self._prepare_from_twisted_request(request)
        auth = OneLogin_Saml2_Auth(req, old_settings=self.settings)
        saml_settings = auth.get_settings()
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        if len(errors) == 0:
            content = metadata
        else:
            content = "Error found on Metadata: %s" % (', '.join(errors))
        return content.encode("ascii")

class Login(Resource):

    def __init__(self, client):
        Resource.__init__(self)
        self.client = client

    def getChild(self, name, request):
        if name:
            return loginCode(name, self.client)
        else:
            return self

    def render_GET(self, request):
        logging.debug("[login] GET !")
        request.setHeader(b"content-type", b"text/plain")
        content = u"no Code\n"
        return content.encode("ascii")


class loginCode(Resource):
    isLeaf = True
    nonce = None
    client = None
    settings = None

    def __init__(self, nonce, client):
        Resource.__init__(self)
        self.nonce = nonce
        self.client = client
        my_base = path.dirname(path.realpath(__file__))
        filename = my_base + "/websso_daemon.json"
        json_data_file = open(filename, 'r')
        self.settings = json.load(json_data_file)
        logging.debug("loginCode: {}".format(nonce))

    def _simplify_args(self, args):
        return { key: val[0] for key, val in args.iteritems() }

    def _prepare_from_twisted_request(self, request):
        return {
            'http_host': request.getHost().host,
            'script_name': request.path,
            'server_port': request.getHost().port,
            'get_data': request.args,
            'post_data': self._simplify_args(request.args)
        }

    def render_GET(self, request):
        logging.debug("[loginCode] GET !")
        session = request.getSession()
        s = ISession(session)
        s.nonce = self.nonce
        client = self.client.clients.get(self.nonce, None)
        user = client['user'][0] if client else "Error"
        service = client.get('service', ['?'])[0] if client else "Error"
        request.setHeader(b"content-type", b"text/html")
        if client:
          content =  u"<html>\n<body>\n<form method=POST>\n"
          content += u"Please authorize {} login for user {}<br />\n".format(service, user)
          content += u"<input name=action type=submit value=login>\n"
          content += u"</body>\n</html>\n"
        else:
          content = u"<html>\n<body>\nUnkown error\n</body>\n</html>\n"
        return content.encode("ascii")

    def render_POST(self, request):
        logging.debug("[loginCode] POST !")

        session = request.getSession()
        s = ISession(session)
        nonce = s.nonce
        logging.debug("- nonce %s" % (nonce))
        args = request.args
        client = self.client.clients.get(nonce)
        logging.debug("- client %s" % (client))
        if client:
            pin = client['pin'][0]
        else:
            return "<html><body>Unknown Error</body></html>"
        if args.get('action'):
            if 'login' in args.get('action'):
                req = self._prepare_from_twisted_request(request)
                auth = OneLogin_Saml2_Auth(req, old_settings=self.settings)
                redirect = auth.login()
                request.redirect(redirect)
                request.finish()
                return server.NOT_DONE_YET
            else:
                self.client.handleCommand(nonce, " FAIL")
                return "<html><body>PIN failed!</body></html>"

        req = self._prepare_from_twisted_request(request)
        auth = OneLogin_Saml2_Auth(req, old_settings=self.settings)
        auth.process_response()
        errors = auth.get_errors()
        msg = { 'uid': '', 'result': 'FAIL' }
        if auth.is_authenticated():
            attributes = auth.get_attributes()
            logging.debug("attributes: {}".format(attributes))
            uid_attr = attributes.get(self.settings.get('user_attribute'))
            if uid_attr:
                msg['uid'] = uid_attr[0]
                msg['result'] = 'SUCCESS'
        self.client.handleCommand(nonce, json.dumps(msg))

        logging.debug("Destroy %s" % nonce)
        #self.client.clients.pop(nonce)
        request.setHeader(b"content-type", b"text/html")
        content =  u"<html>\n<body>\n"
        content += u"{} successfully authenticated<br />\n".format(msg['uid'])
        content += u"PIN: {}<br />\n".format(pin)
        content += u"This window may be closed\n"
        content += u"</body>\n</html>\n"
        return content.encode("ascii")

class Server:

    def __init__(self):
	try:
		url = os.environ.get("URL", "http://localhost")
		if not url.endswith("/"):
			url += "/";
	
        	self.settings = { 
    			"ports": {
        			"clients": 80,
        			"command": 81
    			},
    			"url": url,
    			"strict": False,
    			"debug": True,
    			"user_attribute": "urn:oid:0.9.2342.19200300.100.1.1",
    			"sp": {
        			"entityId": "%smd" % url,
        			"assertionConsumerService": {
            				"url": "%slogin/acs" % url,
            				"binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        			},
        			"singleLogoutService": {
            				"url": "%slogin/sls" % url,
            				"binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        			},
        			"NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    			},
			"idp" :  {
				"entityId": os.environ["IDP_ENTITYID"],
        			"singleSignOnService": {
            				"url": os.environ["IDP_LOGON_URL"],
            				"binding": os.environ["IDP_LOGON_BINDING"],
        			},
        			"x509cert": os.environ["IDP_CERTIFICATE"]
			}
		}
	except Exception as e:
        	logging.debug("Error in settingsa: %s" % str(e))

        logging.debug("settings: %s" % self.settings)

        # Client channel
        client = Client(self.settings)
        self.clients = server.Site(client)

        # Command channel
        self.command = CommandFactory(client)

        # WebSSO channel
        root = client
        root.putChild(b'login', Login(client))
        root.putChild(b'md', Metadata(self.settings))
        self.web = server.Site(root)

    def start(self):
        reactor.listenTCP(self.settings['ports']['clients'], self.clients)
        reactor.listenTCP(self.settings['ports']['command'], self.command, interface='localhost')
        reactor.run()

Server().start()


