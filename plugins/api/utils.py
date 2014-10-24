import base64
from functools import wraps, partial
from datetime import datetime
import time
import json
import re
import logging

import web

logger = logging.getLogger('API')


http_status_codes = {
    100: '100 Continue',
    101: '101 Switching Protocols',

    200: '200 OK',
    201: '201 Created',
    202: '202 Accepted',
    203: '203 Non-Authoritative Information',
    204: '204 No Content',
    205: '205 Reset Content',
    206: '206 Partial Content',
    207: '207 Multi-Status',

    300: '300 Multiple Choices',
    301: '301 Moved Permanently',
    302: '302 Found',
    303: '303 See Other',
    304: '304 Not Modified',
    305: '305 Use Proxy',
    307: '307 Temporary Redirect',

    400: '400 Bad Request',
    401: '401 Unauthorized',
    402: '402 Payment Required',
    403: '403 Forbidden',
    404: '404 Not Found',
    405: '405 Method Not Allowed',
    406: '406 Not Acceptable',
    407: '407 Proxy Authentication',
    408: '408 Request Timeout',
    409: '409 Conflict',
    410: '410 Gone',
    411: '411 Length Required',
    412: '412 Precondition Failed',
    413: '413 Request Entity Too Large',
    414: '414 Request-URI Too Long',
    415: '415 Unsupported Media Type',
    416: '416 Requested Range Not Satisfiable',
    417: '417 Expectation Failed',
    422: '422 Unprocessable Entity',
    423: '423 Locked',
    424: '424 Failed Dependency',

    500: '500 Internal Server Error',
    501: '501 Not Implemented',
    502: '502 Bad Gateway',
    503: '503 Service Unavailable',
    504: '504 Gateway Timeout',
    505: '505 HTTP Version Not Supported',
    507: '507 Insufficient Storage',
}


#  Converts local time to UTC time
def local_to_utc(dt):
    try:
        TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        local = dt.strftime(TIME_FORMAT)
        # print "local_to_utc: before convert:", local
        timestamp = str(time.mktime(datetime.strptime(local, TIME_FORMAT).timetuple()))[:-2]
        utc = datetime.utcfromtimestamp(int(timestamp))
        # print "local_to_utc: after convert:", utc
        return utc
    except:
        return dt


# jsonify dates
_json_dumps = partial(json.dumps,
                      # default=lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x),
                      default=lambda x: local_to_utc(x).isoformat() if hasattr(x, 'isoformat') else str(x),
                      sort_keys=False)


def does_json(func):
    """
    api function jsonificator
    Takes care of IndexError and ValueError so that the decorated code can igrnore those
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Take care of JSONP
        params = web.input(callback=None)

        # Set headers
        web.header('Cache-Control', 'no-cache')
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')

        # This calls the decorated method
        try:
            r = func(self, *args, **kwargs)
            if r:
                if params.callback:
                    # Take care of JSONP requests
                    r = "{callback}({json});".format(callback=params.callback,
                                                     json=_json_dumps(r))
                    return r

                else:
                    return _json_dumps(r)
            else:
                return ''

        except IndexError:  # No such item
            raise web.badrequest()
            # FIXME: for some reason raising notfound here results in a redirect chain
            # raise web.notfound()
            # FIXME: Make up mind on exceptions and error reporting
            # result['http_status_code'] = 404
        except ValueError:  # json errors
            raise web.badrequest()
            # FIXME: Make up mind on exceptions and error reporting
            # result['http_status_code'] = 406

    return wrapper


# FIXME: Bind user authentication to ospy users and drop the 'dummy' part
dummy_users = (
    ('',      'long_password'),  # Since 'admin' is implied
    ('admin', 'password'),
    ('user',  'otherpassword')
)


def auth(func):
    """
    Basic auth wrapper
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            http_auth = re.sub('^Basic ', '', web.ctx.env.get('HTTP_AUTHORIZATION'))

            username, password = base64.decodestring(http_auth).split(':')
            logger.debug('Auth Attempt with: u:\'%s\' p:\'%s\'', username, password)

            if (username, password) not in dummy_users:  # FIXME: subsitute dummy users for real ones
                raise  # essentially a goto :P
        except:
            # no or worng auth provided
            web.header('WWW-Authenticate', 'Basic realm="OSPy"')
            raise web.unauthorized()
        return func(self, *args, **kwargs)
    return wrapper


class JSONAppBrowser(web.browser.AppBrowser):
    """
    JSON-ified AppBrowser
    """
    # TODO: tests

    headers = {'Accept': 'application/json'}

    def json_open(self, url, data=None, headers={}, method='GET'):
        headers = headers or self.headers
        url = urllib.basejoin(self.url, url)
        req = urllib2.Request(url, json.dumps(data), headers)
        req.get_method = lambda: method  # Fake urllub's get_method
        return self.do_request(req)

    @property
    def json_data(self):
        return json.loads(self.data)