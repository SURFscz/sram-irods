#!/usr/bin/env python3
from flask import Flask, request
from flask_restful import Resource, Api
from pprint import pprint
import argparse
import os
import re
import sys
import atexit


HANDLE_SUCCESS = 1
HANDLE_ERROR = 2
HANDLE_SERVER_TOO_BUSY = 3
HANDLE_PROTOCOL_ERROR = 4
HANDLE_OP_NOT_SUPPORTED = 5
HANDLE_RECURSION_COUNT_TOO_HIGH = 6
HANDLE_NOT_FOUND = 100
HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404


class HandleData(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.handles = {}

    def register_prefix(self, prefix):
        if prefix not in self.handles:
            self.handles[prefix] = {}

    def get_handle(self, prefix, suffix, args={}):
        if self.verbose:
            print("HandleData.get_handle(%s/%s)" % (prefix, suffix))
            pprint(args)
        if prefix in self.handles:
            if suffix in self.handles[prefix]:
                return ({"responseCode": HANDLE_SUCCESS,
                         "handle": "%s/%s" % (prefix, suffix),
                         "values": self.handles[prefix][suffix]},
                        HTTP_200_OK)
            else:
                if self.verbose:
                    print("undefined suffix %s" % suffix)
                return ({"responseCode": HANDLE_NOT_FOUND,
                         "handle": "%s/%s" % (prefix, suffix)},
                        HTTP_404_NOT_FOUND)
        else:
            if self.verbose:
                print("undefined prefix %s" % prefix)
            return ({"responseCode": HANDLE_NOT_FOUND,
                     "handle": "%s/%s" % (prefix, suffix)},
                    HTTP_400_BAD_REQUEST)

    def put_handle(self, prefix, suffix,
                   args={}, json_data={}):
        if self.verbose:
            print("HandleData.put_handle(%s/%s)" % (prefix, suffix))
            pprint(args)
            pprint(json_data)
        overwrite = args.get('overwrite', False)
        indices = args.getlist('index')
        if isinstance(json_data, dict):
            if prefix not in self.handles:
                self.handles[prefix] = {}
            if suffix in self.handles[prefix] and not overwrite:
                return ({"responseCode": HANDLE_SUCCESS,
                         "handle": "%s/%s" % (prefix, suffix)},
                        HTTP_400_BAD_REQUEST)
            else:
                if suffix in self.handles[prefix]:
                    json_data['values'] = self.overwrite(prefix, suffix,
                                                         json_data, indices)
                    if self.verbose:
                        print("updated %s/%s" % (prefix, suffix))
                        pprint(json_data)
                else:
                    if self.verbose:
                        print("added %s/%s" % (prefix, suffix))
                        pprint(json_data)
                self.handles[prefix][suffix] = json_data['values']
                return {"responseCode": HANDLE_SUCCESS,
                        "handle": "%s/%s" % (prefix, suffix)}
        else:
            return ({"responseCode": HANDLE_PROTOCOL_ERROR,
                     "message":
                     "java.lang.Exception: Invalid JSON in PUT request"},
                    HTTP_400_BAD_REQUEST)

    def delete(self, prefix, suffix, args={}):
        if self.verbose:
            print("HandleData.delete(%s/%s)" % (prefix, suffix))
            pprint(args)
        if prefix in self.handles:
            if suffix in self.handles[prefix]:
                if not 'index' in args:
                    del self.handles[prefix][suffix]
                    return ({"responseCode": HANDLE_SUCCESS,
                             "handle": "%s/%s" % (prefix, suffix)},
                            HTTP_200_OK)
                else:
                    indices = {str(o): True for o in args.getlist('index')}
                    tmp = [obj
                           for obj in self.handles[prefix][suffix]
                           if str(obj.get('index', '')) not in indices]
                    self.handles[prefix][suffix] = tmp
                    return ({"responseCode": HANDLE_SUCCESS,
                             "handle": "%s/%s" % (prefix, suffix)},
                            HTTP_200_OK)
            else:
                if self.verbose:
                    print("undefined suffix %s" % suffix)
                return ({"responseCode": HANDLE_NOT_FOUND,
                         "handle": "%s/%s" % (prefix, suffix)},
                        HTTP_404_NOT_FOUND)
        else:
            if self.verbose:
                print("undefined prefix %s" % prefix)
            return ({"responseCode": HANDLE_NOT_FOUND,
                     "handle": "%s/%s" % (prefix, suffix)},
                    HTTP_400_BAD_REQUEST)

    def overwrite(self, prefix, suffix, json_data, indices):
        new_objects = {obj.get('index'): obj
                       for obj in json_data.get('values')}
        old_objects = {obj.get('index'): obj
                       for obj in self.handles[prefix][suffix]}
        values = [new_objects[obj.get('index')]
                  if obj.get('index') in new_objects else obj
                  for obj in self.handles[prefix][suffix]]
        for obj in json_data.get('values'):
            if obj.get('index') not in old_objects:
                values.append(obj)
        return values

    def match_filter(self, filters, prefix, suffix, values):
        ret = True
        for k, v in filters.items():
            items = [item for item in values
                     if item.get('type', None) == str(k)]
            item = items[0] if len(items) else None
            if item is None:
                ret = False
            else:
                value = str(item.get("data", {}).get("value", None))
                if isinstance(v, str):
                    if v != '*' and value != str(v):
                        ret = False
                else:
                    if not v.match(value):
                        ret = False
        return ret

    def glob2regex(self, input_str):
        return re.compile(".*".join([re.escape(tok)
                                     for tok in input_str.split('*')]))

    def reverse_lookup(self, filters, prefix):
        filters = {k: self.glob2regex(f) for k, f in  filters.items()}
        ret =  ["%s/%s" % (prefix, suffix)
                for suffix, obj in self.handles[prefix].items()
                if self.match_filter(filters, prefix, suffix, obj)]
        print("reverse lookup result:")
        pprint(ret)
        return ret


class Resetter(Resource):
    def __init__(self, handle_data=None, **kwarg):
        self.handle_data = handle_data
        super(Resource, self).__init__(**kwarg)

    def delete(self):
        for k in self.handle_data.handles.keys():
            self.handle_data.handles[k] = {}


class HandleMock(Resource):
    def __init__(self, handle_data=None, prefix="", **kwarg):
        self.handle_data = handle_data
        self.prefix = prefix
        super(HandleMock, self).__init__(**kwarg)

    def get(self, prefix, suffix):
        return self.handle_data.get_handle(prefix, suffix, request.args)

    def put(self, prefix, suffix):
        json_data = request.get_json(force=True)
        return self.handle_data.put_handle(prefix, suffix,
                                           request.args,
                                           json_data)

    def delete(self, prefix, suffix):
        return self.handle_data.delete(prefix, suffix, request.args)


class ReverseLookupMock(Resource):
    def __init__(self, handle_data=None, prefix="", **kwarg):
        self.handle_data = handle_data
        self.prefix = prefix
        super(ReverseLookupMock, self).__init__(**kwarg)

    def get(self, prefix):
        if sys.version_info[0] == 3:
            filters = {str(k): str(values)
                       for k, values in request.args.to_dict().items()
                       if k != 'limit' and k != 'page'}
        else:
            filters = {str(k): str(values[-1])
                       for k, values in request.args.iterlists()
                       if k != 'limit' and k != 'page'}
        return self.handle_data.reverse_lookup(filters, prefix)


def create_pid_file(pid_file):
    pid = os.getpid()
    with open(pid_file, "w") as file:
        file.write(str(pid))


def delete_pid_file(pid_file):
    if os.path.isfile(pid_file):
        os.remove(pid_file)


def start_app(port=5000, host='127.0.0.1'):
    prefix = "21.T12995"
    verbose = True
    app = Flask(__name__)
    api = Api(app)
    handle_data = HandleData(verbose=verbose)
    handle_data.register_prefix(prefix)
    api.add_resource(Resetter, '/api/reset',
                     resource_class_kwargs={'handle_data': handle_data})

    api.add_resource(HandleMock,
                     '/api/handles/<string:prefix>/<string:suffix>',
                     resource_class_args=(),
                     resource_class_kwargs={'handle_data': handle_data,
                                            'prefix': prefix})
    api.add_resource(ReverseLookupMock,
                     '/hrls/handles/<string:prefix>',
                     resource_class_args=(),
                     resource_class_kwargs={'handle_data': handle_data,
                                            'prefix': prefix})
    app.run(debug=True, port=port, host=host)


def run_handle_mock(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, help='port', default=5000)
    parser.add_argument('--host', type=str, help='host', default='127.0.0.1')
    parser.add_argument('--pid_file', help='create pid file')
    args = parser.parse_args(argv)
    port = args.port
    host = args.host
    pid_file = args.pid_file
    if pid_file is not None:
        create_pid_file(pid_file)
        atexit.register(delete_pid_file, pid_file=pid_file)
    start_app(port=port, host=host)

if __name__ == '__main__':
    run_handle_mock()
