#!/usr/bin/env python
# This plugin read data from I2C counter PCF8583 on I2C address 0x50. Max count PCF8583 is 1 milion pulses per seconds

import json
import time
import traceback

from threading import Thread, Event

import web

from log import log
from plugins import PluginOptions, plugin_url
from webpages import ProtectedPage
from helpers import get_rpi_revision


NAME = 'Water meter'
LINK = 'settings_page'

options = PluginOptions(
    NAME,
    {'enabled': False,
     'pulses': 10
    }
)

################################################################################
# Main function loop:                                                          #
################################################################################


class WatterSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop = Event()

        self.bus = None
        self.status = {}
        self.status['meter%d'] = 0

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
        try:
            import smbus  # for PCF 8583
            self.bus = smbus.SMBus(1 if get_rpi_revision() >= 2 else 0)
        except ImportError:
            log.warning(NAME, 'Could not import smbus.')

        while True:
            log.clear(NAME)
            try:    
                if self.bus is not None and options['enabled']:  # if water meter plugin is enabled
                    val = counter(self.bus)
                    self.status['meter%d'] = val

                self._sleep(1)
               
            except Exception:
                self.bus = None
                err_string = ''.join(traceback.format_exc())
                log.error(NAME, 'Water meter plug-in:\n' + err_string)
                self._sleep(60)            
                
water_sender = None

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global water_sender
    if water_sender is None:
        water_sender = WaterSender()
        
def stop():
    global water_sender
    if water_sender is not None:
        water_sender.stop()
        water_sender.join()
        water_sender = None


def counter(bus): # reset PCF8583, measure pulses and return number pulses per second
    try:
        # reset PCF8583
        bus.write_byte_data(0x50,0x00,0x20) # status registr setup to "EVENT COUNTER"
        bus.write_byte_data(0x50,0x01,0x00) # reset LSB
        bus.write_byte_data(0x50,0x02,0x00) # reset midle Byte
        bus.write_byte_data(0x50,0x03,0x00) # reset MSB
        
        time.sleep(1)
        
        # read number (pulses in counter) and translate to DEC
        counter =  bus.read_i2c_block_data(0x50,0x00)
        num1 = (counter[1] & 0x0F)             # units
        num10 = (counter[1] & 0xF0) >> 4       # dozens
        num100 = (counter[2] & 0x0F)           # hundred
        num1000 = (counter[2] & 0xF0) >> 4     # thousand
        num10000 = (counter[3] & 0x0F)         # tens of thousands
        num100000 = (counter[3] & 0xF0) >> 4   # hundreds of thousands
        pulses = (num100000 * 100000) + (num10000 * 10000) + (num1000 * 1000) + (num100 * 100) + (num10 * 10) + num1
        return pulses
    except:
        self.bus = None
        return 0

################################################################################
# Web pages:                                                                   #
################################################################################

class settings_page(ProtectedPage):
    """Load an html page for entering water meter adjustments."""

    def GET(self):
        return self.template_render.plugins.water_meter(options, water_sender.status, log.events(NAME))

    def POST(self):
        options.web_update(web.input())

        if water_sender is not None:
            water_sender.update()

        raise web.seeother(plugin_url(settings_page))


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(options)
