# !/usr/bin/env python

import json
import time
import datetime
import string
import web
import version

from helpers import *
from inputs import inputs
from options import options, rain_blocks
from stations import stations
from programs import programs
from urls import urls # Gain access to ospy's URL list
from webpages import ProtectedPage, WebPage
from log import log

NAME = 'Mobile Aplication'
LINK = 'None' 

##############
## New URLs ##

urls.extend([
    '/jo', 'plugins.mobile_app.cur_options',   #jo is ok
    '/jc', 'plugins.mobile_app.cur_settings',  #jc found rdst, sbits, ps, lrun 
    '/js', 'plugins.mobile_app.station_state', #js is ok
    '/jp', 'plugins.mobile_app.program_info',
    '/jn', 'plugins.mobile_app.station_info',
    '/jl', 'plugins.mobile_app.get_logs',
    '/sp', 'plugins.mobile_app.set_password'])


#######################
## Class definitions ##

class cur_options(WebPage):  # /jo
    """Returns device options as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        if check_login():
            jopts = {
                "fwv": version.ver_date +'-OSPi', 
                "tz": 0,                                # time zone not used in refactor version?
                "ext": options.output_count - 1,
                "seq": options.sequential,
                "sdt": options.station_delay,
                "mas": stations.master, 
                "mton": options.master_on_delay, 
                "mtof": options.master_off_delay,
                "urs": options.rain_sensor_enabled, 
                "rso": options.rain_sensor_no,
                "wl": options.level_adjustment, 
                "ipas": options.no_password, 
                "reset": 0,                             # gv.sd['rbt'], reboot not used in refactor version?
                "lg": options.run_log 
            }
        else: # without login
            jopts = {
                "fwv": version.ver_date +'-OSPi', 
            }

        return json.dumps(jopts)

class cur_settings(ProtectedPage):  # /jc
    """Returns current settings as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jsettings = {
            "devt": time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds(),
            "nbrd": options.output_count,
            "en": options.scheduler_enabled, 
            "rd": rain_blocks,  
            "rs": inputs.rain_input, 
            "mm": options.manual_mode,
            "rdst": 0, #rain_blocks.block_end(),
            "loc": options.location, 
            "sbits": 0, #gv.sbits
            "ps": 0, #gv.ps
            "lrun": 0, #last_run(self), #last run
            "ct": get_cpu_temp(options.temp_unit), 
            "tu": options.temp_unit 
        }

        return json.dumps(jsettings)
    

class station_state(ProtectedPage):  # /js
    """Returns station status and total number of stations as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jstate = {
            "sn": [station.name for station in stations.get()], #station name
            "nstations": stations.count() #number of station
        }

        return json.dumps(jstate)


class program_info(ProtectedPage):  # /jp
    """Returns program data as json."""
    def GET(self):
       
        # here add code for program lpd

        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jpinfo = {
            "nprogs": programs.count()-1, 
            "nboards": options.output_count,
            "mnp": 9999, 
            'pd': 10#lpd #local program data
        }

        return json.dumps(jpinfo)


class station_info(ProtectedPage):  # /jn
    """Returns station information as json."""
    def GET(self):
        disable = []

#        for byte in gv.sd['show']:
#            disable.append(~byte&255)

        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jpinfo = {
            "snames": [station.name for station in stations.get()], #station names
            "ignore_rain": 0,#gv.sd['ir']
            "masop": 0,#gv.sd['mo'] #master operation bytes - contains bits per board for stations with master set
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
