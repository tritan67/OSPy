from functools import wraps, partial
import json
import traceback
import web

import logging
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


class MethodNotAllowed(Exception):
    pass


class UnprocessableEntity(Exception):
    pass

# jsonify dates
_json_dumps = partial(json.dumps,
                      default=lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x),
                      sort_keys=False)


def api(func):
    """
    api function jsonificator
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = {'http_status_code': 200}

        # This calls the decorated method
        try:
            r = func(self, *args, **kwargs)
            if r:
                result.update(r)
        except IndexError:  # No such item
            result['http_status_code'] = 404
        except ValueError:  # json errors
            result['http_status_code'] = 406
        except MethodNotAllowed:  #
            traceback.print_exc()
            result['http_status_code'] = 405
        except UnprocessableEntity:
            traceback.print_exc()
            result['http_status_code'] = 422
        except Exception:  # catch-all
            traceback.print_exc()
            result['http_status_code'] = 500

        web.ctx['status'] = http_status_codes[result['http_status_code']]  # update return HTTP status
        del result['http_status_code']  # we dont send that to the client

        #  Set headers
        web.header('Cache-Control', 'no-cache')

        if result:
            # If theres data to return, label it as json
            web.header('Content-Type', 'application/json')
            return _json_dumps(result)

        # Return nothing on empty dictionay
        return ''

    return wrapper