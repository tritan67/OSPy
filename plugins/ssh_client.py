# !/usr/bin/env python
# This plugin connects to a remote ssh server and allows remote access in to the Web server OSPy
__author__ = 'Martin Pihrt'

import json
import time
import os
import psutil
import subprocess
import time
  
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
        connect = True
        disconnect = True
        while not self._stop.is_set():
            if ssh_options['enabled']:          # if ssh client is enabled
                try:
                    if disconnect:
                        tunnel_cmd = 'ssh -i key.pem -o BatchMode=yes -o ServerAliveInterval=1 -o ServerAliveCountMax=5 -f -o ExitOnForwardFailure=yes -N -L ' + ssh_options['ssh_port'] + ':localhost:8080 ' + ssh_options['ssh_user'] + '@' + ssh_options['server_adress']
                        try:
                           ssh_tunnel_process = create_tunnel(tunnel_cmd)
                           log.info(NAME, 'Create tunnel.')
                           disconnect = False
                           connect = True


                except Exception:
                    err_string = ''.join(traceback.format_exc())
                    log.error(NAME, 'SSH client plug-in:\n' + err_string)
                    self._sleep(60)
            
            else:          
                if connect:
                    ssh_tunnel_process.terminate()
                    log.info(NAME, 'Terminated the tunnel.')
                    connect = False
                    disconnect = True
                    
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
      
def create_tunnel(tunnel_cmd):
    ssh_process = subprocess.Popen(tunnel_cmd,  universal_newlines=True,
                                                shell=True,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT,
                                                stdin=subprocess.PIPE)

    # Assuming that the tunnel command has "-f" and "ExitOnForwardFailure=yes", then the 
    # command will return immediately so we can check the return status with a poll().
    output = ssh_process.communicate()[0]
    log.info(NAME, output) 
    
    while True:
        p = ssh_process.poll()
        if p is not None: break
        time.sleep(1)

    if p == 0:
        # Unfortunately there is no direct way to get the pid of the spawned ssh process, so we'll find it
        # by finding a matching process using psutil.

        current_username = psutil.Process(os.getpid()).username
        ssh_processes = [proc for proc in psutil.get_process_list() if proc.cmdline == tunnel_cmd.split() and proc.username == current_username]

        if len(ssh_processes) == 1:
            return ssh_processes[0]
        else:
            raise RuntimeError, 'Multiple (or zero?) tunnel ssh processes found: ' + str(ssh_processes) 
            log.error(NAME, 'Multiple (or zero?) tunnel ssh processes found: ' + str(ssh_processes)) 
    else:
        raise RuntimeError, 'Error creating tunnel: ' + str(p) + ' :: ' + str(ssh_process.stdout.readlines())
        log.error(NAME, 'Error creating tunnel: ' + str(p) + ' :: ' + str(ssh_process.stdout.readlines()))

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
