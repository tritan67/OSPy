"""
API
"""
from options import options

__author__ = [
    'Teodor Yantcheff',
]

__version__ = '0.3 pre aplha'

import json
import logging

import web
from plugins.api.utils import does_json, auth
from programs import programs
from stations import stations
from log import log
from urls import urls  # Gain access to ospy's URL list


logger = logging.getLogger('API')
logger.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
h.setFormatter(logging.Formatter('%(name)s:%(levelname)s:%(message)s'))
#h.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s'))
logger.addHandler(h)


urls.extend([
    # Stations
    r'/rapi/1.0/stations(?:/(?P<station_id>\d+))?/?', 'plugins.api.Stations',
    # Programs
    r'/rapi/1.0/programs(?:/(?P<program_id>\d+))?/?', 'plugins.api.Programs',
    # Options
    r'/rapi/1.0/options/?', 'plugins.api.Options',
    # Logs
    r'/rapi/1.0/logs/?', 'plugins.api.Logs',
    # System
    r'/rapi/1.0/system/?', 'plugins.api.System',
])


# FIXME: make this global. web.py catch-all url handling ?
# Ugly hack
def OPTIONS(*args):
    web.header('Access-Control-Allow-Origin', '*')
    web.header('Access-Control-Allow-Headers', 'Content-Type')
    web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')


class Stations(object):

    # TODO: Maybe this needs to go to stations as a to_dict() method or something
    # TODO: Exchange index for URI ?
    def _station_to_dict(self, station):
        return {k: getattr(station, k) for k in dir(station) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}

    @does_json
    def GET(self, station_id):
        logger.debug('GET /stations/{}'.format(station_id if station_id else ''))
        if station_id:
            return self._station_to_dict(stations[int(station_id)])
        else:
            l = [self._station_to_dict(s) for s in stations]
            # stations_type = type(stations).__name__  # .strip('_')
            # return {'type': stations_type, 'stations': l}
            return l

    # @auth
    @does_json
    def POST(self, station_id):
        logger.debug('POST stations')
        update = json.loads(web.data())
        if station_id:
            pass
        else:
            for s in update:
                for k, v in s.iteritems():
                    print k, ':', v
                    try:
                        stations[s['index']].__setattr__(k, v)
                    except:
                        #  Skip uneditable items silently
                        pass
                        print 'except', k

        # raise web.forbidden()
        # web.ctx.status = '300 Multiple Choices'
        return

    @auth
    @does_json
    def PUT(self, station_id):
        logger.debug('PUT stations')
        raise web.forbidden()

    @auth
    @does_json
    def DELETE(self, station_id):
        logger.debug('DELETE stations')
        raise web.forbidden()

    OPTIONS = OPTIONS


# def dummy_start(id):
#     logger.debug('would start %d' % id)
#
#
# def dummy_stop(id):
#     logger.debug('would stop %d' % id)
#
#
# class Station(object):
#     editable_keys = ('name', 'enabled', 'ignore_rain', 'is_master')
#     all_keys = ('id',) + editable_keys
#
#     #
#     actions = {
#         'start': dummy_start,
#         'stop': dummy_stop,
#     }
#
#     @does_json
#     def GET(self, station_id):
#         logger.debug('GET station:%s' % station_id)
#
#
#
#     @auth
#     @does_json
#     def POST(self, station_id):
#         logger.debug('POST station:%s' % station_id)
#         station_id = int(station_id)
#
#         try:
#             action_func = Station.actions[web.input().get('do', '').lower()]
#             action_func(station_id)
#         except:
#             raise web.badrequest()
#
#     @auth
#     @does_json
#     def PUT(self, station_id):
#         logger.debug('PUT station:%s' % station_id)
#         station_id = int(station_id)
#         s = dummy_stations[station_id]
#         update = json.loads(web.data())
#
#         # Only apply values to editable fields
#         for k in list(set(update)):  # remove dupes
#             if k in Station.editable_keys:
#                 s[k] = update[k]
#         dummy_stations[station_id] = s
#         return s


class Programs(object):

    def _program_to_dict(self, program):
        return {k: getattr(program, k) for k in dir(program) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}

    @does_json
    def GET(self, program_id):
        logger.debug('GET /programs/{}'.format(program_id if program_id else ''))

        if program_id:
            return self._program_to_dict(programs[int(program_id)])
        else:
            return [self._program_to_dict(p) for p in programs]
        # return {'programs': l}

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

    OPTIONS = OPTIONS


class Options(object):
    @does_json
    def GET(self):
        logger.debug('GET options')
        return options.OPTIONS

    @does_json
    def POST(self):
        logger.debug('POST options')
        web.ctx.status = '403 Forbidden'  # FIXME
        # raise web.forbidden()

    @does_json
    def PUT(self):
        logger.debug('PUT options')
        raise web.forbidden()

    @does_json
    def DELETE(self):
        logger.debug('DELETE options')
        raise web.forbidden()

    OPTIONS = OPTIONS


class Logs(object):
    @does_json
    def GET(self):
        logger.debug('GET logs')

        log_entries = []
        for run in log.finished_runs():
            entry = {
                'start': run['start'],
                'end': run['end'],
                'manual': run['manual'],
                'station': run['station'],
                'station_name': stations[run['station']].name,
                'program_id': run['program'],
                'program_name': run['program_name'],
            }
            log_entries.append(entry)
        # return {'logs': log_entries}
        return log_entries

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
        logger.debug('GET ' + self.__class__.__name__)
        raise web.forbidden()

    @does_json
    def POST(self):
        logger.debug('POST ' + self.__class__.__name__)

    @does_json
    def PUT(self):
        logger.debug('PUT ' + self.__class__.__name__)
        raise web.forbidden()

    @does_json
    def DELETE(self):
        logger.debug('DELETE ' + self.__class__.__name__)
        raise web.forbidden()