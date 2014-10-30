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
from plugins.api.utils import does_json, auth, http_status_codes
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


class Stations(object):

    def _station_to_dict(self, station):
        # This is automatic and over all the keys that a _Station has
        # return {k: getattr(station, k) for k in dir(station) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}

        return {
            'id': station.index,  # TODO: Exchange index for URI ?
            'name': station.name,
            'enabled': station.enabled,
            'ignore_rain': station.ignore_rain,
            'is_master': station.is_master,
            'activate_master': station.activate_master,
            'remaining_seconds': station.remaining_seconds,
            'running': station.active
        }

    def _dict_to_station(self, sid, data):
        for k, v in data.iteritems():
            # logger.debug('sid:{} key:{} val:{}'.format(sid, k, v))
            try:
                stations[sid].__setattr__(k, v)
            except:
                #  Skip uneditable items silently
                pass
                # logger.debug('except', k)

    @does_json
    def GET(self, station_id=None):
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
    def POST(self, station_id=None):
        logger.debug('POST /stations/{}'.format(station_id if station_id else ''))

        action = web.input().get('do', '').lower()
        station_id = int(station_id)
        if action == 'start':
            logger.debug('Starting station {id} ("{name}")'.format(id=station_id, name=stations[station_id].name))
            stations.activate(station_id)
        elif action == 'stop':
            logger.debug('Stopping station {id} ("{name}")'.format(id=station_id, name=stations[station_id].name))
            stations.deactivate(station_id)
        else:
            web.ctx.status = http_status_codes[400]  # FIXME
            return

        # web.ctx.status = '204 No Content'
        return self._station_to_dict(stations[station_id])

    #@auth
    @does_json
    def PUT(self, station_id=None):
        logger.debug('PUT /stations/{}'.format(station_id if station_id else ''))
        update = json.loads(web.data())
        if station_id:
            station_id = int(station_id)
            self._dict_to_station(station_id, update)
            return self._station_to_dict(stations[station_id])
        else:
            for sid, upd in enumerate(update):
                self._dict_to_station(sid, upd)
            return [self._station_to_dict(s) for s in stations]

    # @auth
    @does_json
    def DELETE(self, station_id=None):
        logger.debug('DELETE /stations/{}'.format(station_id if station_id else ''))
        raise web.nomethod()

    def OPTIONS(self, station_id=None):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')


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

    # @auth
    @does_json
    def POST(self, program_id):
        logger.debug('POST /programs/{}'.format(program_id if program_id else ''))
        raise web.nomethod()

    # @auth
    @does_json
    def PUT(self, program_id):
        logger.debug('PUT /programs/{}'.format(program_id if program_id else ''))
        raise web.nomethod()

    # @auth
    @does_json
    def DELETE(self, program_id):
        logger.debug('DELETE /programs/{}'.format(program_id if program_id else ''))
        raise web.nomethod()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')


class Options(object):

    """
    Options array in the format
      <option_key> : {
                        'name': OPTIONS[option_key]['name']
                        'help': OPTIONS[option_key]['help']
                        .
                        .
                     }
    """
    ANNOTATED_OPTIONS = {
        key: {
            okey: options.OPTIONS[i].get(okey, '')
            for okey in ['name', 'help', 'category', 'default', 'min', 'max']
        }
        for i, key in enumerate(options.get_options())
    }

    @does_json
    def GET(self):
        logger.debug('GET ' + self.__class__.__name__)
        a = web.input().get('annotated', '').lower()
        if a in ['true', 'yes', 'annotated', '1']:
            opts = {o: {'value': options[o]} for o in options.get_options()}
            for k in opts.iterkeys():
                opts[k].update(self.ANNOTATED_OPTIONS[k])
            return opts
        else:
            return {o: options[o] for o in options.get_options()}

    # @auth
    # @does_json
    def PUT(self):
        logger.debug('PUT ' + self.__class__.__name__)
        update = json.loads(web.data())
        for key, val in update.iteritems():
            if key in options.get_options():
                logger.debug("Updating '{}' to '{}'".format(key, val))
                options[key] = val
            else:
                logger.debug('Unknown key {}'.format(key))

        # return options.get_options()
        return self.GET()

    # @auth
    @does_json
    def POST(self):
        logger.debug('POST ' + self.__class__.__name__)
        raise web.nomethod()

    # @auth
    @does_json
    def DELETE(self):
        logger.debug('DELETE ' + self.__class__.__name__)
        raise web.nomethod()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')


class Logs(object):

    def _runlog_to_dict(self, log_entry):
        return {
            'start': log_entry['start'],
            'end': log_entry['end'],
            'duration': str(log_entry['end'] - log_entry['start']).split('.')[0],  # pass it as a baked string to the client
            'manual': log_entry['manual'],
            'station': log_entry['station'],
            'station_name': stations[log_entry['station']].name,
            'program_id': log_entry['program'],
            'program_name': log_entry['program_name'],
        }

    @does_json
    def GET(self):
        logger.debug('GET logs ' + self.__class__.__name__)
        return [self._runlog_to_dict(fr) for fr in log.finished_runs()]
        # web.header('Cache-Control', 'no-cache')
        # web.header('Content-Type', 'application/json')
        # web.header('Access-Control-Allow-Origin', '*')
        # import datetime
        # return datetime.datetime.now()
        # return '[{"start": "2014-10-23T21:25:25", "station": 2, "end": "2014-10-23T21:25:30", "duration": "0:00:05", "station_name": "Station 03ttt", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": "2014-10-23T21:25:30", "station": 3, "end": "2014-10-23T21:25:35", "duration": "0:00:05", "station_name": "Station 04 dest", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": "2014-10-23T21:25:35", "station": 4, "end": "2014-10-23T21:25:40", "duration": "0:00:05", "station_name": "Station 05", "manual": true, "program_name": "Run-Once", "program_id": -1}]'
        # return '[{"start": 1414605866, "station": 0, "end": 1414605881, "duration": "0:00:15", "station_name": "Station 01", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": 1414605881, "station": 2, "end": 1414605896, "duration": "0:00:15", "station_name": "Station 03", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": 1414605896, "station": 5, "end": 1414605911, "duration": "0:00:15", "station_name": "Station 06", "manual": true, "program_name": "Run-Once", "program_id": -1}]'

    # @auth
    @does_json
    def DELETE(self):
        logger.debug('DELETE ' + self.__class__.__name__)
        log.clear_runs()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, DELETE, OPTIONS')


class System(object):
    @does_json
    def GET(self):
        logger.debug('GET ' + self.__class__.__name__)
        raise web.forbidden()

    # @auth
    @does_json
    def POST(self):
        logger.debug('POST ' + self.__class__.__name__)
        raise web.forbidden()

    # @auth
    @does_json
    def PUT(self):
        logger.debug('PUT ' + self.__class__.__name__)
        raise web.forbidden()

    # @auth
    @does_json
    def DELETE(self):
        logger.debug('DELETE ' + self.__class__.__name__)
        raise web.forbidden()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')