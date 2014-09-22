"""
API
"""
# FIXME: imports
# TODO: authentication (decorator?)

__author__ = [
    'Teodor Yantcheff',
]

__version__ = '0.1 pre aplha'

import json
from plugins.api.utils import api

import datetime

import web
from urls import urls  # Gain access to ospy's URL list

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(name)s:%(levelname)s:%(message)s'))
#ch.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s'))
# add ch to logger
logger.addHandler(ch)


station_keys = ('id', 'name', 'enabled', 'ignore_rain', 'is_master')
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


urls.extend([
    '/stations/?', 'plugins.api.stations',
    '/stations/(\d+)/?', 'plugins.api.station'
])


class stations(object):
    @api
    def GET(self):
        return {'stations': dummy_stations}

    # @api
    # def POST(self):
    #     pass

    @api
    def PUT(self):
        pass

    @api
    def DELETE(self):
        pass


class station(object):
    @api
    def GET(self, station_id):
        logger.debug('GET %s' % station_id)
        return dummy_stations[int(station_id)]

    @api
    def POST(self, station_id):
        logger.debug('POST %s' % station_id)
        station_id = int(station_id)
        result = dummy_stations[station_id]
        if web.input().get('do', '') == 'start':
            logger.debug('START %s' % station_id)


    @api
    def PUT(self, station_id):
        logger.debug('PUT %s' % station_id)
        station_id = int(station_id)
        try:
            update = json.loads(web.data())
        except:  # json error
            return {'http_status_code': 406}  # bad json
        return dummy_stations[station_id].update(update)

    # @api
    # def DELETE(self, station_id):
    #     logger.debug('DELETE %s' % station_id)
    #     pass
