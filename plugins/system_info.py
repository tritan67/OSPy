#!/usr/bin/env python
# this plugins print system info os on web 

import sys
import time
import traceback
import platform
from threading import Thread
from random import randint
from collections import OrderedDict
from collections import namedtuple

import helpers
from webpages import ProtectedPage


NAME = 'System Information'
LINK = 'status_page'


################################################################################
# Main function loop:                                                          #
################################################################################
class SystemInfoChecker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.status = {
            'status': ''
        }
        self._sleep_time = 0
        self.start()

    def add_status(self, msg):
        if self.status['status']:
            self.status['status'] += '\n' + msg
        else:
            self.status['status'] = msg

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def _info_data(self):
        """Returns the info data."""
        self.add_status('System release: ' + platform.release())
        self.add_status('System name: ' + platform.system())
        self.add_status('Node: ' + platform.node())
        self.add_status('Machine: ' + platform.machine())
        self.add_status('Distribution: ' + (platform.linux_distribution()[0]) + ' ' + (platform.linux_distribution()[1]))
        meminfo = get_meminfo()
        if not meminfo:
            meminfo = {
                'MemTotal': 'unknown',
                'MemFree': 'unknown'
            }
        self.add_status('Total memory: {0}'.format(meminfo['MemTotal']))
        self.add_status('Free memory: {0}'.format(meminfo['MemFree']))
        netdevs = get_netdevs()
        if netdevs:
            for dev in netdevs.keys():
                self.add_status('{0}: {1} MiB {2} MiB'.format(dev, netdevs[dev].rx, netdevs[dev].tx))
        else:
            self.add_status('Unable to read network device data')
        self.add_status('Uptime: ' + helpers.uptime())
        self.add_status('CPU temp: ' + helpers.get_cpu_temp() + 'C')
        self.add_status('MAC adress: ' + get_mac())

    def run(self):
        time.sleep(randint(3, 10))  # Sleep some time to prevent printing before startup information
          
        while True:
            try:
                self.status['status'] = ''
                self._info_data()
                self._sleep(3600)

            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                self.add_status('System information plug-in encountered error:\n' + err_string)
                self._sleep(3600)

si_checker = None


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global si_checker
    if si_checker is None:
        si_checker = SystemInfoChecker()


def stop():
    global si_checker
    if si_checker is not None:
        si_checker.stop()
        si_checker.join()
        si_checker = None


def get_mac():
    """Retrun MAC from file"""    
    try:
        myMAC = open('/sys/class/net/eth0/address').read()
        return str(myMAC)
    except:
        return str('none') 


def get_meminfo():
    """Return the information in /proc/meminfo as a dictionary"""
    try:
        meminfo = OrderedDict()
        with open('/proc/meminfo') as f:
            for line in f:
                meminfo[line.split(':')[0]] = line.split(':')[1].strip()
        return meminfo
    except:
        return None


def get_netdevs():
    """RX and TX bytes for each of the network devices"""
    try:
        with open('/proc/net/dev') as f:
            net_dump = f.readlines()
        device_data = {}
        data = namedtuple('data', ['rx', 'tx'])
        for line in net_dump[2:]:
            line = line.split(':')
            if line[0].strip() != 'lo':
                device_data[line[0].strip()] = data(float(line[1].split()[0])/(1024.0*1024.0),
                                                    float(line[1].split()[8])/(1024.0*1024.0))
        return device_data
    except:
        return None


################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        return self.template_render.plugins.system_info(si_checker.status)