#!/usr/bin/env python
# This plugin read data (temp or voltage) from I2C PCF8591 on adress 0x48. For temperature probe use LM35D. Power for PCF8591 or LM35D is 5V dc! no 3.3V dc

import json
import time
import datetime
import sys
import traceback

from threading import Thread, Event

import web

from options import options
from log import log
from plugins import PluginOptions, plugin_url
import plugins
from webpages import ProtectedPage
from helpers import get_rpi_revision

# I2C bus Raspberry PI revision 
try:
    import smbus  # for PCF 8591
    ADC = smbus.SMBus(1 if get_rpi_revision() >= 2 else 0)
except ImportError:
    ADC = None


NAME = 'Voltage and Temperature Monitor'
LINK = 'settings_page'

pcf_options = PluginOptions(
    NAME,
   {
        'use_pcf': False,
        'use_log': False,
        'time': 0,
        'records': 0,
        'ad0': False,
        'ad1': False,
        'ad2': False,
        'ad3': False,
        'ad0text': 'label_1',
        'ad1text': 'label_2',
        'ad2text': 'label_3',
        'ad3text': 'label_4',
        'ad0val': 0.0, #get_now_measure(1), here is not function print data value on web? 
        'ad1val': 0.0, #get_now_measure(2),
        'ad2val': 0.0, #get_now_measure(3),
        'ad3val': 0.0, #get_now_measure(4),
        'da0val': 0
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################


class PCFSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop = Event()
        self._sleep_time = 0
        self.start()

   
    def stop(self):
        self._stop.set()

    def update(self):
        self._sleep_time = 0
    
    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop.is_set():
           time.sleep(1)
           self._sleep_time -= 1
    
    def run(self):
        pcf_controller = True
        last_time =  int(time.time())
        log.info(NAME, 'Started the Voltage and Temperature Monitor plug-in.')
        while True:
            try:    
                if pcf_options['use_pcf']:                              # if pcf plugin is enabled
                    if pcf_options['use_log'] and pcf_options['time']:  # if log is enabled and time is not 0 min
                        actual_time = int(time.time())
                        if actual_time - last_time > (int(pcf_options['time']) * 60):       # if is time for save
                            ad0 = get_now_measure(1)
                            ad1 = get_now_measure(2)
                            ad2 = get_now_measure(3)
                            ad3 = get_now_measure(4)
                            if pcf_options['ad0']: 
                               ad0 = get_volt(ad0)
                            else:
                               ad0 = get_temp(ad0)
                            if pcf_options['ad1']: 
                               ad1 = get_volt(ad1)
                            else:
                               ad1 = get_temp(ad1)
                            if pcf_options['ad2']: 
                               ad2 = get_volt(ad2)
                            else:
                               ad2 = get_temp(ad2)
                            if pcf_options['ad3']: 
                               ad3 = get_volt(ad3)
                            else:
                               ad3 = get_temp(ad3)
                            last_time = actual_time
                           
                            if pcf_controller:
                               TEXT = 'On ' + time.strftime('%d.%m.%Y at %H:%M:%S', time.localtime(time.time())) + \
                                     ' save PCF8591 data AD0=' + str(ad0) + \
                                     ' AD1=' + str(ad1) + \
                                     ' AD2=' + str(ad2) + \
                                     ' AD3=' + str(ad3)
                               log.clear(NAME)
                               log.info(NAME, TEXT)
                               write_log(ad0, ad1, ad2, ad3)
                
                out_val = pcf_options['da0val']  
                get_write_DA(int(out_val)) # send to DA 0 output value 0-255 -> 0-5V 
                if pcf_controller == False:
                    log.clear(NAME)
                    log.error(NAME, 'Could not find any PCF8591 controller.\n')
                    self._sleep(60)  
                    pcf_controller = True
               
                self._sleep(1)
               
            except Exception:
                err_string = ''.join(traceback.format_exc())
                log.error(NAME, 'PCF plug-in:\n' + err_string)
                self._sleep(60)            
                
pcf_sender = None

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global pcf_sender
    if pcf_sender is None:
        pcf_sender = PCFSender()

def stop():
    global lcd_sender
    if pcf_sender is not None:
       pcf_sender.stop()
       pcf_sender.join()
       pcf_sender = None


def get_volt(data):
    """Return voltage 0-5.0V from number"""
    volt = (data*5.0)/255
    volt = round(volt,1)
    return volt

def get_temp(data):
    """Return temperature 0-100C from data"""
    temp = ((data*5.0)/255)*100.0
    temp = round(temp,1)
    return temp

def get_now_measure(AD_pin):
    """Return number 0-255 from A/D PCF8591 to webpage"""
    try:
       ADC.write_byte_data(0x48, (0x40 + AD_pin), AD_pin)
       return ADC.read_byte(0x48)  
    except Exception:
       pcf_controller = False
       return 0.0


def get_write_DA(Y):  # PCF8591 D/A converter Y=(0-255) for future use
    """Write analog voltage to output"""
    try: 
       ADC.write_byte_data(0x48, 0x40, Y)
    except Exception:
       pass

def read_log():
    """Read pcf log"""
    try:
        with open('./data/pcflog.json') as logf:
            records = logf.readlines()
        return records
    except IOError:
        return []


def write_log(ad0, ad1, ad2, ad3):
    """Add run data to csv file - most recent first.""" 
    logline = '{"Time":"' + time.strftime('%H:%M:%S","Date":"%d-%m-%Y"', time.localtime(time.time())) + ',"AD0":"' + str(
                ad0) + '","AD1":"' + str(ad1) + '","AD2":"' + str(ad2) + '","AD3":"' + str(ad3) + '"}\n'                     
    log = read_log()
    log.insert(0, logline)
    with open('./data/pcflog.json', 'w') as f:
        if int(pcf_options['records']) != 0:
            f.writelines(log[:int(pcf_options['records'])])
        else:
            f.writelines(log)
    return

################################################################################
# Web pages:                                                                   #
################################################################################


class settings_page(ProtectedPage):
    """Load an html page for entering pcf adjustments."""

    def GET(self):
        return self.template_render.plugins.pcf_8591_adj(pcf_options, log.events(NAME))

    def POST(self):
        pcf_options.web_update(web.input())

        if pcf_sender is not None:
            pcf_sender.update()
        raise web.seeother(plugin_url(settings_page))


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(pcf_options)


class pcf_log_page(ProtectedPage):  # save log file from web as csv file type
    """Simple PCF Log API"""

    def GET(self):
        records = read_log()
        data = "Date, Time, AD0, AD1, AD2, AD3\n"
        for r in records:
            event = json.loads(r)
            data += event["Date"] + ", " + event["Time"] + ", " + str(event["AD0"]) + ", " + str(
                    event["AD1"]) + ", " + str(event["AD2"]) + ", " + str(event["AD3"]) + ", " + "\n"
        web.header('Content-Type', 'text/csv')
        log.info(NAME, 'Log file is downloaded...') 
        return data


class delete_log_page(ProtectedPage):  # delete log file from web
    """Delete all pcflog records"""

    def GET(self):
        qdict = web.input()
        with open('./data/pcflog.json', 'w') as f:
            f.write('')
        log.info(NAME, 'Log file is deleted...')
        raise web.seeother(plugin_url(settings_page))


