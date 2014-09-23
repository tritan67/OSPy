"""
API
"""
# FIXME: imports
# TODO: authentication (decorator?)

__author__ = [
    'Teodor Yantcheff',
]

__version__ = '0.2 pre aplha'

import json
from plugins.api.utils import api, auth

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
    '/stations/?', 'plugins.api.Stations',
    '/stations/(\d+)/?', 'plugins.api.Station',
    '/options/?', 'plugins.api.Options',
    '/logs/?', 'plugins.api.Logs'
])


class Stations(object):
    @api
    def GET(self):
        return {'stations': dummy_stations}

    @api
    def POST(self):
        raise web.forbidden()

    @api
    def PUT(self):
        raise web.forbidden()

    @api
    def DELETE(self):
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

    @auth
    @api
    def GET(self, station_id):
        logger.debug('GET station:%s' % station_id)
        return dummy_stations[int(station_id)]

    @api
    def POST(self, station_id):
        logger.debug('POST station:%s' % station_id)
        station_id = int(station_id)

        try:
            action_func = Station.actions[web.input().get('do', '').lower()]
            action_func(station_id)
        except:
            raise web.badrequest()

    @api
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

    @api
    def DELETE(self, station_id):
        logger.debug('DELETE station:%s' % station_id)
        raise web.forbidden()


class Options(object):
    @api
    def GET(self):
        return {'options': dummy_options}

    @api
    def POST(self):
        raise web.forbidden()

    @api
    def PUT(self):
        raise web.forbidden()

    @api
    def DELETE(self):
        raise web.forbidden()


class Logs(object):
    @api
    def GET(self):
        return {'logs': dummy_logs}

    @api
    def POST(self):
        raise web.forbidden()

    @api
    def PUT(self):
        raise web.forbidden()

    @api
    def DELETE(self):
        raise web.forbidden()