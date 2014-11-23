#!/usr/bin/env python
# this plugins print system info os on web 

import platform
from collections import OrderedDict

import helpers
from webpages import ProtectedPage
from options import options

NAME = 'System Information'
LINK = 'status_page'


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    pass

stop = start


def get_mac():
    """Retrun MAC from file"""    
    try:
        return str(open('/sys/class/net/eth0/address').read())
    except Exception:
        return 'Unknown'


def get_meminfo():
    """Return the information in /proc/meminfo as a dictionary"""
    try:
        meminfo = OrderedDict()
        with open('/proc/meminfo') as f:
            for line in f:
                meminfo[line.split(':')[0]] = line.split(':')[1].strip()
        return meminfo
    except Exception:
        return {
            'MemTotal': 'Unknown',
            'MemFree': 'Unknown'
        }


def get_netdevs():
    """RX and TX bytes for each of the network devices"""
    try:
        with open('/proc/net/dev') as f:
            net_dump = f.readlines()
        device_data = {}
        for line in net_dump[2:]:
            line = line.split(':')
            if line[0].strip() != 'lo':
                device_data[line[0].strip()] = {'rx': float(line[1].split()[0])/(1024.0*1024.0),
                                                'tx': float(line[1].split()[8])/(1024.0*1024.0)}
        return device_data
    except Exception:
        return {}


def get_overview():
    """Returns the info data as a list of lines."""
    result = []

    meminfo = get_meminfo()
    netdevs = get_netdevs()
    
    result.append('System release: ' + platform.release())
    result.append('System name:    ' + platform.system())
    result.append('Node:           ' + platform.node())
    result.append('Machine:        ' + platform.machine())
    result.append('Distribution:   ' + (platform.linux_distribution()[0]) + ' ' + (platform.linux_distribution()[1]))
    result.append('Total memory:   ' + meminfo['MemTotal'])
    result.append('Free memory:    ' + meminfo['MemFree'])
    if netdevs:
        for dev, info in netdevs.iteritems():
            result.append('%-16s %s MiB %s MiB' % (dev + ':', info['rx'], info['tx']))
    else:
        result.append('Network:        Information unavailable')
    result.append('Uptime:         ' + helpers.uptime())
    result.append('CPU temp:       ' + helpers.get_cpu_temp(options.temp_unit) + ' ' + options.temp_unit)
    result.append('MAC adress:     ' + get_mac())

    return result


################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        return self.template_render.plugins.system_info(get_overview())