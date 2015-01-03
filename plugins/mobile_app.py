# !/usr/bin/env python

import json
import time
import datetime
import string
import web

from helpers import *
from inputs import inputs
from options import options, rain_blocks
from stations import stations
from programs import programs
from urls import urls # Gain access to ospy's URL list
from webpages import ProtectedPage, WebPage
from log import log

NAME = 'Mobile aplication'

##############
## New URLs ##

urls.extend([
    '/jo', 'plugins.mobile_app.options',
    '/jc', 'plugins.mobile_app.cur_settings',
    '/js', 'plugins.mobile_app.station_state',
    '/jp', 'plugins.mobile_app.program_info',
    '/jn', 'plugins.mobile_app.station_info',
    '/jl', 'plugins.mobile_app.get_logs',
    '/sp', 'plugins.mobile_app.set_password'])


#######################
## Class definitions ##

class options(WebPage):  # /jo
    """Returns device options as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        if check_login():
            jopts = {
                "fwv": version+'-OSPi', #version firmware
                "tz": 0, # not used in refactor version?
                "ext": options.output_count - 1,
                "seq": options.sequential, #sequential/concurrent operation 
                "sdt": options.station_delay, #station delay time
                "mas": stations.master, #master station index
                "mton": options.master_on_delay, #master on delay
                "mtof": options.master_off_delay, #master off delay
                "urs": options.rain_sensor_enabled, #use rain sensor 
                "rso": options.rain_sensor_no, #Rain sensor type 
                "wl": options.level_adjustment, #water level (percent adjustment of watering time)
                "ipas": options.no_password, #ignore password 
                "reset": 0, #gv.sd['rbt'], #reboot not used in refactor version?
                "lg": options.run_log #log runs
            }
        else: # without login
            jopts = {
                "fwv": version+'-OSPi', #version firmware
            }

        return json.dumps(jopts)

class cur_settings(ProtectedPage):  # /jc
    """Returns current settings as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jsettings = {
            "devt": time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds(), #system time
            "nbrd": options.output_count, #number of boards (includes base unit and expansion boards)
            "en": options.scheduler_enabled, #enabled (system operation)
            "rd": rain_blocks, #rain delay 
            "rs": inputs.rain_input, #rain sensed 
            "mm": options.manual_mode, #manual mode
            "rdst": rain_blocks.block_end(), #rain delay stop time 
            "loc": options.location, #location for weather
            "sbits": 0, #gv.sbits, #station bits, used to display stations that are on in UI 
            "ps": 0, #gv.ps, #program schedule used for UI display 
            "lrun": last_run(), #last run
            "ct": get_cpu_temp(), #procesor temperature
            "tu": options.temp_unit #temperature unit C/F
        }

        return json.dumps(jsettings)
    
    def last_run():
        finished = [run for run in log.finished_runs() if not run['blocked']]
        if finished:
            last_prog = finished[-1]['start'].strftime('%H:%M: ') + finished[-1]['program_name']
        else:
            last_prog = 'None' 
  
        return last_prog        


class station_state(ProtectedPage):  # /js
    """Returns station status and total number of stations as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jstate = {
            "sn": station.name for station in stations.get(), #station name
            "nstations": stations.count() #number of station
        }

        return json.dumps(jstate)


class program_info(ProtectedPage):  # /jp
    """Returns program data as json."""
    def GET(self):
        lpd = []  # Local program data
        dse = int(time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds())  # ???days since epoch
        for p in gv.pd:
            op = p[:]  # Make local copy of each program
            if op[1] >= 128 and op[2] > 1:
                rel_rem = (((op[1]-128) + op[2])-(dse % op[2])) % op[2]
                op[1] = rel_rem + 128
            lpd.append(op)
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jpinfo = {
            "nprogs": programs.count()-1, #number of programs
            "nboards": options.output_count, #number of boards
            "mnp": 9999, #maximum number of programs
            'pd': lpd #local program data
        }

        return json.dumps(jpinfo)


class station_info(ProtectedPage):  # /jn
    """Returns station information as json."""
    def GET(self):
        disable = []

        for byte in gv.sd['show']:
            disable.append(~byte&255)

        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jpinfo = {
            "snames": [station.name for station in stations.get()] #station names
            "ignore_rain": gv.sd['ir'],
            "masop": gv.sd['mo'], #master operation bytes - contains bits per board for stations with master set
            "stn_dis": disable,
            "maxlen": 100 # not used in refactor? gv.sd['snlen'] max size of station names
        }

        return json.dumps(jpinfo)

class get_logs(ProtectedPage):  # /jl
    """Returns log information for specified date range."""
    def GET(self):
        records = self.read_log()
        data = []
        qdict = web.input()

        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')

        if 'start' not in qdict or 'end' not in qdict:
            return []

        for r in records:
            event = json.loads(r)
            date = time.mktime(datetime.datetime.strptime(event["date"], "%Y-%m-%d").timetuple())
            if int(qdict["start"]) <= int(date) <= int(qdict["end"]):
                pid = event["program"]
                if pid == "Run-once":
                    pid = 98
                if pid == "Manual":
                    pid = 99

                pid = int(pid)
                station = int(event["station"])
                duration = string.split(event["duration"], ":")
                duration = (int(duration[0]) * 60) + int(duration[1])
                timestamp = int(time.mktime(datetime.datetime.strptime(event["date"] + " " + event["start"], "%Y-%m-%d %H:%M:%S").timetuple()))

                data.append([pid, station, duration, timestamp])

        return json.dumps(data)
        
    def read_log(self):
        try:
            with open('./data/log.json') as logf:
                records = logf.readlines()
            return records
        except IOError:
            return []


def start():
pass
stop = start            
