"""
API
"""
# FIXME: imports
# TODO: authentication (decorator?)

__author__ = [
    'Teodor Yantcheff',
]

__version__ = '0.3 pre aplha'

import json
from plugins.api.utils import does_json, auth

import web
from urls import urls  # Gain access to ospy's URL list

import logging
logger = logging.getLogger('API')
logger.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
h.setFormatter(logging.Formatter('%(name)s:%(levelname)s:%(message)s'))
#h.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s'))
logger.addHandler(h)


# TODO: remove dummy data
dummy_stations = [
    {
        'id': 1,
        'name': 'station 1',
        'enabled': True,
        'ignore_rain': False,
        'is_master': False
    },
    {
        'id': 2,
        'name': 'station 2',
        'enabled': True,
        'ignore_rain': True,
        'is_master': False
    },
]

dummy_options = {
    'option1': 1,
    'option2': True,
    'option3': 'string'
}

# Just so that there are meny items to return
dummy_logs = [{'date': '2014-09-20T01:35.{}'.format(i),
               'message': 'Event {}'.format(i)}
              for i in xrange(1000)]
pass
urls.extend([
    # Stations
    '/stations/?', 'plugins.api.Stations',
    '/stations/(\d+)/?', 'plugins.api.Station',
    # Programs
    '/programs/?', 'plugins.api.Programs',
    '/programs/(\d+)/?', 'plugins.api.Station',
    # Options
    '/options/?', 'plugins.api.Options',
    # Logs
    '/logs/?', 'plugins.api.Logs'
    # System
    '/system/?', 'plugins.api.System',
])


class Stations(object):
    @does_json
    def GET(self):
        logger.debug('GET stations')
        return {'stations': dummy_stations}

    @auth
    @does_json
    def POST(self):
        logger.debug('POST stations')
        raise web.forbidden()

    @auth
    @does_json
    def PUT(self):
        logger.debug('PUT stations')
        raise web.forbidden()

    @auth
    @does_json
    def DELETE(self):
        logger.debug('DELETE stations')
        raise web.forbidden()


def dummy_start(num):
    logger.debug('would start %d' % num)


def dummy_stop(num):
    logger.debug('would stop %d' % num)


class Station(object):
    editable_keys = ('name', 'enabled', 'ignore_rain', 'is_master')
    all_keys = ('id',) + editable_keys

    #
    actions = {
        'start': dummy_start,
        'stop': dummy_stop,
    }

    @does_json
    def GET(self, station_id):
        logger.debug('GET station:%s' % station_id)
        return dummy_stations[int(station_id)]

    @auth
    @does_json
    def POST(self, station_id):
        logger.debug('POST station:%s' % station_id)
        station_id = int(station_id)

        try:
            action_func = Station.actions[web.input().get('do', '').lower()]
            action_func(station_id)
        except:
            raise web.badrequest()

    @auth
    @does_json
    def PUT(self, station_id):
        logger.debug('PUT station:%s' % station_id)
        station_id = int(station_id)
        s = dummy_stations[station_id]
        update = json.loads(web.data())

        # Only apply values to editable fields
        for k in list(set(update)):  # remove dupes
            if k in Station.editable_keys:
                s[k] = update[k]
        dummy_stations[station_id] = s
        return s

    @auth
    @does_json
    def DELETE(self, station_id):
        logger.debug('DELETE station:%s' % station_id)
        raise web.forbidden()


class Programs(object):
    @does_json
    def GET(self):
        logger.debug('GET programs')
        raise web.forbidden()

    @auth
    @does_json
    def POST(self):
        logger.debug('POST programs')
        raise web.forbidden()

    @auth
    @does_json
    def PUT(self):
        logger.debug('PUT programs')
        raise web.forbidden()

    @auth
    @does_json
    def DELETE(self):
        logger.debug('DELETE programs')
        raise web.forbidden()


class Program(object):
    # editable_keys = ('name', 'enabled',...)
    # all_keys = ('id',) + editable_keys

    #
    # actions = {
    #     'start': dummy_start,
    #     'stop': dummy_stop,
    # }

    @does_json
    def GET(self, program_id):
        logger.debug('GET programs:%s' % program_id)
        raise web.badrequest()

    @auth
    @does_json
    def POST(self, program_id):
        logger.debug('POST station:%s' % program_id)
        raise web.badrequest()

    @auth
    @does_json
    def PUT(self, program_id):
        logger.debug('PUT programs:%s' % program_id)
        raise web.badrequest()

    @auth
    @does_json
    def DELETE(self, program_id):
        logger.debug('DELETE programs:%s' % program_id)
        raise web.forbidden()


class Options(object):
    @does_json
    def GET(self):
        logger.debug('GET options')
        return {'options': dummy_options}

    @does_json
    def POST(self):
        logger.debug('POST options')
        raise web.forbidden()

    @does_json
    def PUT(self):
        logger.debug('PUT options')
        raise web.forbidden()

    @does_json
    def DELETE(self):
        logger.debug('DELETE options')
        raise web.forbidden()


class Logs(object):
    @does_json
    def GET(self):
        logger.debug('GET logs')
        return {'logs': dummy_logs}

    @does_json
    def POST(self):
        logger.debug('POST logs')
        raise web.forbidden()

    @does_json
    def PUT(self):
        logger.debug('PUT logs')
        raise web.forbidden()

    @does_json
    def DELETE(self):
        logger.debug('DELETE logs')
        raise web.forbidden()


class System(object):
    @does_json
    def GET(self):
        logger.debug('GET logs')
        return {'logs': dummy_logs}

    @does_json
    def POST(self):
        logger.debug('POST logs')
        raise web.forbidden()

    @does_json
    def PUT(self):
        logger.debug('PUT logs')
        raise web.forbidden()

    @does_json
    def DELETE(self):
        logger.debug('DELETE logs')
        raise web.forbidden()