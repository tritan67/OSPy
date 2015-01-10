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
LINK = 'info_page' 

##############
## New URLs ##

urls.extend([
    '/jo', 'plugins.mobile_app.cur_options',   
    '/jc', 'plugins.mobile_app.cur_settings',  #  found: sbits, ps, 
    '/js', 'plugins.mobile_app.station_state', 
    '/jp', 'plugins.mobile_app.program_info',  #  found: lpd, 
    '/jn', 'plugins.mobile_app.station_info',  #  found: masop and line 136,137
    '/jl', 'plugins.mobile_app.get_logs'        
    ])        
 

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
                "fwv": version.ver_date + '/2.2.' + str(version.revision) +'-OSPi', 
                "tz": 0,                              # time zone is not used in refactor version?
                "ext": number_ext_board(self),                
                "seq": 1 if options.sequential else 0,
                "sdt": options.station_delay,
                "mas": stations.master, 
                "mton": options.master_on_delay, 
                "mtof": options.master_off_delay,
                "urs": 1 if options.rain_sensor_enabled else 0, 
                "rso": 1 if options.rain_sensor_no else 0,
                "wl": options.level_adjustment, 
                "ipas": 1 if options.no_password else 0, 
                "reset": 0,                             # gv.sd['rbt'], reboot is not used in refactor version?
                "lg": 1 if options.run_log else 0
            }
        else: # without login
            jopts = {
                "fwv": version.ver_date + '/2.2.' + str(version.revision) +'-OSPi', 
            } 

        return json.dumps(jopts)
  

class cur_settings(ProtectedPage):  # /jc
    """Returns current settings as json."""
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jsettings = {
            "devt": int(time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()),
            "nbrd": number_ext_board(self),               
            "en": 1 if options.scheduler_enabled else 0, 
            "rd": rain_blocks.seconds_left(), # rain delay (hours)
            "rs": inputs.rain_input, 
            "mm": 1 if options.manual_mode else 0,
            "rdst": time.mktime(rain_blocks.block_end().timetuple()), # rain delay stop time (unix time stamp)
            "loc": options.location, 
            "sbits": [0, 0], #gv.sbits station bits, used to display stations that are on in UI (list of bytes, one byte per board)
            "ps": [0, 0], #gv.ps program schedule used for UI display (list of 2 element lists i.e. [program number, duration])
            "lrun": last_run(self), 
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
            "sn": [1 if station.active else 0 for station in stations.get()], 
            "nstations": stations.count()                                     
        }

        return json.dumps(jstate)


class program_info(ProtectedPage):  # /jp
    """Returns program data as json."""
    def GET(self):
        lpd = []  # Local program data
#        dse = int(time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()) #int((time.time()+((gv.sd['tz']/4)-12)*3600)/86400)  # days since epoch in master
#        for p in gv.pd: #program data - loaded from file at startup (list of lists) 
#            op = p[:]  # Make local copy of each program
#            if op[1] >= 128 and op[2] > 1:
#                rel_rem = (((op[1]-128) + op[2])-(dse % op[2])) % op[2]
#                op[1] = rel_rem + 128
#            lpd.append(op)
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jpinfo = {
            "nprogs": programs.count(),                      # ? -1 is in master  
            "nboards": number_ext_board(self),                 
            "mnp": 9999, 
            'pd': [[1, 127, 0, 360, 1080, 240, 900, 30]] #lpd 
        }

        return json.dumps(jpinfo)


class station_info(ProtectedPage):  # /jn
    """Returns station information as json."""
    def GET(self):
#        disable = []

#        for byte in gv.sd['show']:
#            disable.append(~byte&255)

        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')
        jpinfo = {
            "snames": [station.name for station in stations.get()], 
            "ignore_rain": [1 if station.ignore_rain else 0 for station in stations.get()], 
            "masop": [0],  #gv.sd['mo'] #master operation bytes - contains bits per board for stations with master set
            "stn_dis": [0],
            "maxlen": 32                                                    # not used in refactor? gv.sd['snlen'] max size of station names 32
        }

        return json.dumps(jpinfo)

class get_logs(ProtectedPage):  # /jl
    """Returns log information for specified date range."""
    def GET(self):
        data = []
        qdict = web.input()

        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-cache')

        if 'start' not in qdict or 'end' not in qdict:
            return []

        events = log.finished_runs() + log.active_runs()

        for interval in events:
            # return only records that are visible on this day:
            duration = (interval['end'] - interval['start']).total_seconds()
            minutes, seconds = divmod(duration, 60)
            pid = interval['program_name']
            if pid == 'Run-Once':
               pid = 98
            if pid == 'Manual':
               pid = 99
            pid = int(pid)
            station = int(interval['station']) 
            duration = (interval['end'] - interval['start']).total_seconds() 
            timestamp = int(time.mktime(datetime.datetime.strptime(interval['start'].strftime("%Y-%m-%d") + " " + interval['start'].strftime("%H:%M:%S"), "%Y-%m-%d %H:%M:%S").timetuple()))
            data.append([pid, station, duration, timestamp])

        return json.dumps(data)
        

def start():
   pass

stop = start  

def number_ext_board(self): 
   ### return number of expansion boards ###
   num1 = options.output_count/8
   num2 = options.output_count%8
   if num2 > 0:
      num1 = num1 + 1 
   return num1   

def last_run(self):
   ### return last run information ###
   events = log.finished_runs()
   for interval in events:
      station_index = int(interval['station'])
      program_number = int(interval['program'])
      duration = (interval['end'] - interval['start']).total_seconds()
      end_time = (datetime.datetime.now() - interval['end']).total_seconds()

   return [station_index, program_number, duration, end_time]


################################################################################
# Web pages:                                                                   #
################################################################################
class info_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        return self.template_render.plugins.mobile_app()
          
