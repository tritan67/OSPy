#!/usr/bin/env python
# System information plugin

import platform

import helpers
from webpages import ProtectedPage


NAME = 'System Information'
LINK = 'status_page'


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    pass


def stop():
    pass


################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        sysinfo = ''
        sysinfo += 'System release: ' + platform.release()
        sysinfo += '\nSystem name: ' + platform.system()
        sysinfo += '\nNode: ' + platform.node()
        sysinfo += '\nMachine: ' + platform.machine()
        sysinfo += '\nDistribution: ' + platform.linux_distribution()[0] + ' ' + platform.linux_distribution()[1]
        meminfo = helpers.get_meminfo()
        if not meminfo:
            meminfo = {
                'MemTotal': 'unknown',
                'MemFree': 'unknown'
            }
        sysinfo += '\nTotal memory: {0}'.format(meminfo['MemTotal'])
        sysinfo += '\nFree memory: {0}'.format(meminfo['MemFree'])
        netdevs = helpers.get_netdevs()
        if netdevs:
            for dev in netdevs.keys():
                sysinfo += '\n{0}: {1} MiB {2} MiB'.format(dev, netdevs[dev].rx, netdevs[dev].tx)
        else:
            sysinfo += '\nUnable to read network device data'
        sysinfo += '\nUptime: ' + helpers.uptime()
        sysinfo += '\nCPU temp: ' + helpers.get_cpu_temp() + 'C'
        sysinfo += '\nMAC adress: ' + helpers.get_mac()

        return self.template_render.plugins.system_info(sysinfo)