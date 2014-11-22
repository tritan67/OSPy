#!/usr/bin/env python
# this plugins check power line and shutdown ospi system (count down to reconect power line) and shutdown UPS after time.

from threading import Thread
from random import randint
import json
import time
import sys
import traceback

import web
import gv  # Get access to ospi's settings
from urls import urls  # Get access to ospi's URLs
from ospy import template_render
from webpages import ProtectedPage
from helpers import poweroff


# Add a new url to open the data entry page.
urls.extend(['/upsa', 'plugins.ups_adj.settings',
             '/upsj', 'plugins.ups_adj.settings_json',
             '/upsu', 'plugins.ups_adj.update'])

# Add this plugin to the home page plugins menu
gv.plugin_menu.append(['UPS Monitor Settings', '/upsa'])

################################################################################
# GPIO input pullup and output:                                                #
################################################################################

from gpio_pins import GPIO as GPIO

try:
    if gv.platform == 'pi':  # If this will run on Raspberry Pi:
        pin_power_ok = 16 # GPIO23
    elif gv.platform == 'bo':  # If this will run on Beagle Bone Black:
        pin_power_ok = " "
except AttributeError:
    pass

try:
    GPIO.setup(pin_power_ok, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except NameError:
    pass

try:
    if gv.platform == 'pi':  # If this will run on Raspberry Pi:
        pin_ups_down = 18 # GPIO24
    elif gv.platform == 'bo':  # If this will run on Beagle Bone Black:
        pin_ups_down = " "
except AttributeError:
    pass

try:
    GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
    GPIO.setup(pin_ups_down, GPIO.OUT)
    GPIO.output(pin_ups_down, GPIO.LOW)

except NameError:
    pass


################################################################################
# Main function loop:                                                          #
################################################################################

class UPS_Sender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()
        self.status = ''

        self._sleep_time = 0

    def add_status(self, msg):
        if self.status:
            self.status += '\n' + msg
        else:
            self.status = msg
        print msg

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        time.sleep(randint(3, 10))  # Sleep some time to prevent printing before startup information
        reboot_time = False
        once = True
        once_two = True
        once_three = True
        subject = "Reporting from OSPy"  # Subject in email
        self.add_status('UPS plugin is started.')

        last_time = int(time.time())

        while True:
            try:
                dataUPS = get_ups_options()                             # load data from file
                if dataUPS['ups'] != 'off':                             # if ups plugin is enabled
                    test = get_check_power() 
                    if not test:
                       last_time = int(time.time())

                    if test:                                            # if power line is not active
                       reboot_time = True                               # start countdown timer
                       if once: 
                          if dataUPS['sendeml'] != 'off':               # if enabled send email
                             msg = 'UPS plugin detected fault on power line.' # send email with info power line fault
                             send_email(self, msg, subject)
                             once = False
                             once_three = True 

                    if reboot_time and test:
                       count_val = int(dataUPS['time'])*60 # value for countdown
                       actual_time = int(time.time())
                       self.status = ''
                       self.add_status('Time to shutdown: ' + str(count_val - (actual_time - last_time)) + ' sec')  
                       if ((actual_time - last_time) >= count_val):        # if countdown is 0
                          last_time = actual_time
                          test = get_check_power()
                          if test:                                         # if power line is current not active
                             self.add_status('Power line is not restore in time -> sends email and shutdown system.')
                             reboot_time = False  
                             if dataUPS['sendeml'] != 'off':               # if enabled send email
                                if once_two:
                                    msg = 'UPS plugin - power line is not restore in time -> shutdown system!' # send email with info shutdown system
                                    send_email(self, msg, subject)
                                    once_two = False 

                             GPIO.output(pin_ups_down, GPIO.HIGH)          # switch on GPIO fo countdown UPS battery power off 
                             self._sleep(4)
                             GPIO.output(pin_ups_down, GPIO.LOW) 
                             poweroff(1, True)                            # shutdown system      
          
                    if not test:
                         if once_three:
                            if dataUPS['sendeml'] != 'off':               # if enabled send email
                               msg = 'UPS plugin - power line has restored - OK.'
                               send_email(self, msg, subject)   
                               once = True
                               once_two = True
                               once_three = False                

                self._sleep(1)

            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                self.add_status('UPS plug-in: ' + err_string)
                self._sleep(60)


checker = UPS_Sender()

################################################################################
# Helper functions:                                                            #
################################################################################

def send_email(self, msg, subject):
    """Send email"""
    mesage = ('On ' + time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(
          time.time())) + ' ' + str(msg))
    try:
       from plugins.email_adj import email
       email(subject, mesage)     # send email without attachments
       self.add_status('Email was sent: ' + mesage)
    except Exception as err:
       self.add_status('Email was not sent! ' + str(err))

def get_ups_options():
    """Returns the data form file."""
    data_ups = {
        'time': 60, # in minutes
        'ups': 'off',
        'sendeml': 'off',
        'sensor': get_check_power_str(),
        'status': checker.status
    }
    try:
        with open('./data/ups_adj.json', 'r') as f:  # Read the settings from file
            file_data = json.load(f)
        for key, value in file_data.iteritems():
            if key in data_ups:
                data_ups[key] = value
    except Exception:
        pass

    return data_ups


def get_check_power_str():
    if GPIO.input(pin_power_ok) == 0:
        pwr = ('GPIO Pin = 0 Power line is OK.')  
    else:
        pwr = ('GPIO Pin = 1 Power line ERROR.')  
    return str(pwr)

def get_check_power():
    dataUPS = get_ups_options()
    try:
        if GPIO.input(pin_power_ok):  # power line detected
            pwr = 1
        else:
            pwr = 0
        return pwr
    except NameError:
        pass


################################################################################
# Web pages:                                                                   #
################################################################################


class settings(ProtectedPage):
    """Load an html page for entering USP adjustments."""

    def GET(self):
        return template_render.ups_adj(get_ups_options())


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(get_ups_options())


class update(ProtectedPage):
    """Save user input to ups_adj.json file."""

    def GET(self):
        qdict = web.input()
        if 'ups' not in qdict:
            qdict['ups'] = 'off'
        if 'sendeml' not in qdict:
            qdict['sendeml'] = 'off'
        with open('./data/ups_adj.json', 'w') as f:  # write the settings to file
            json.dump(qdict, f)
        checker.update()
        raise web.seeother('/')
