# !/usr/bin/env python
# This plugin connects to a remote ssh server and allows remote access in to the Web server OSPy
__author__ = 'Martin Pihrt'

import json
import time
import os
from threading import Thread, Event

import web
from webpages import ProtectedPage
from plugins import PluginOptions, plugin_url
from options import options
from log import log


NAME = 'SSH Client'
LINK = 'settings_page'

ssh_options = PluginOptions(
    NAME,
    {
        'enabled': False,
        'server_adres': 'x.x.x.x',
        'server_port': 1234,
        'ssh_user': '',
        'ssh_password': ''
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################
class SSHSender(Thread):
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
        if ssh_options['enabled']:          # if ssh client is enabled
          while not self._stop.is_set():
            try:
               

              self._sleep(5)

            except Exception:
                err_string = ''.join(traceback.format_exc())
                log.error(NAME, 'SSH client plug-in:\n' + err_string)
                self._sleep(60)


ssh_sender = None

################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global ssh_sender
    if ssh_sender is None:
      ssh_sender = SSHSender()

def stop():
    global ssh_sender
    if ssh_sender is not None:
      ssh_sender.stop()
      ssh_sender.join()
      ssh_sender = None



################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for ssh client settings."""

    def GET(self):
        return self.template_render.plugins.ssh_client(ssh_options, log.events(NAME))

    def POST(self):
        ssh_client.web_update(web.input())

        if ssh_sender is not None:
            ssh_sender.update()
        raise web.seeother(plugin_url(settings_page))


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(ssh_options)
