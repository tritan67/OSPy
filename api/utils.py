import sys

__author__ = 'Teodor Yantcheff'

import base64
from functools import wraps, partial
from datetime import datetime
import time
import json
import re
import logging

import web

from errors import badrequest, unauthorized, notacceptable


logger = logging.getLogger('OSPyAPI')


# datetime to timestamp conversion function
def to_timestamp(dt):
    try:
        return int(time.mktime(dt.timetuple()))
    except:
        return 0


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
                      # default=lambda x: local_to_utc(x).isoformat() if hasattr(x, 'isoformat') else str(x),
                      default=lambda x: to_timestamp(x) if hasattr(x, 'isoformat') else str(x),
                      sort_keys=False)


def does_json(func):
    """
    api function jsonificator
    Takes care of IndexError and ValueError so that the decorated code can igrnore those
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Set headers
        web.header('Cache-Control', 'no-cache')
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')

        # This calls the decorated method
        try:
            r = func(self, *args, **kwargs)
            if r:
                # Take care of JSONP
                params = web.input(callback=None)
                if params.callback:
                    # Wrap the response in JSONP format
                    r = "{callback}({json});".format(callback=params.callback,
                                                     json=_json_dumps(r))
                    return r
                else:
                    # Just jsonify the response
                    return _json_dumps(r)
            else:
                return ''

        except IndexError, e:  # No such item
            logger.exception('IndexError')
            raise badrequest('{"error": "(IndexError) Index out of bounds - ' + e.message + '"}')

        except ValueError, e:  # json errors
            logger.exception('ValueError JSON')
            raise badrequest('{"error": "(ValueError) Inappropriate argument value - ' + e.message + '"}')
            # raise badrequest(format(e.message))

        except KeyError, e:  # missing attribute names
            logger.exception('KeyError')
            raise badrequest('{"error": "(KeyError) Missging key - ' + e.message + '"}')
            # raise badrequest(format(e.message))

    return wrapper


# FIXME: Bind user authentication to ospy users and drop the 'dummy' part
dummy_users = (
    ('',      'long_password'),  # Since 'admin' is implied
    ('admin', 'password'),
    ('user',  'otherpassword')
)


def auth(func):
    """
    HTTP Basic authentication wrapper
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            http_auth = re.sub('^Basic ', '', web.ctx.env.get('HTTP_AUTHORIZATION'))

            username, password = base64.decodestring(http_auth).split(':')
            logger.debug('Auth Attempt with: u:\'%s\' p:\'%s\'', username, password)

            if (username, password) not in dummy_users:
                raise  # essentially a goto :P
        except:
            # no or wrong auth provided
            logger.exception('Unauthorized attempt "%s"', username)
            web.header('WWW-Authenticate', 'Basic realm="OSPy"')
            raise unauthorized()

        return func(self, *args, **kwargs)
    return wrapper


# class JSONAppBrowser(web.browser.AppBrowser):
#     """
#     JSON-ified AppBrowser
#     """
#     # TODO: tests
#
#     headers = {'Accept': 'application/json'}
#
#     def json_open(self, url, data=None, headers={}, method='GET'):
#         headers = headers or self.headers
#         url = urllib.basejoin(self.url, url)
#         req = urllib2.Request(url, json.dumps(data), headers)
#         req.get_method = lambda: method  # Fake urllub's get_method
#         return self.do_request(req)
#
#     @property
#     def json_data(self):
#         return json.loads(self.data)