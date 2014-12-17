#!/usr/bin/env python
# This plugin save image from webcam to ./data/image.jpg
# fswebcam -r 1280x720  ./data/image.jpg


import json
import subprocess
import sys
import traceback

import web
from log import log
from plugins import PluginOptions, plugin_url
from webpages import ProtectedPage


NAME = 'Webcam Monitor'
LINK = 'settings_page'

cam_options = PluginOptions(
    NAME,
    {'enabled': False,
     'resolution': '1280x720'
    }
)


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    pass

stop = start

def get_run_cam():
            if cam_options['enabled']:                  # if cam plugin is enabled
                log.clear(NAME)
                command = "fswebcam -r " + cam_options['resolution'] + "./data/image.jpg"
                run_command(command)
                        

            else: 
                log.clear(NAME)
                log.info(NAME, 'Plugin is disabled...')


def run_command(cmd):
    log.clear(NAME)
    log.info(NAME, 'Please wait...' )
    p = subprocess.Popen(cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    output = p.communicate()
    log.debug(NAME, output[0])
   

################################################################################
# Web pages:                                                                   #
################################################################################

class settings_page(ProtectedPage):
    """Load an html page for entering webcam adjustments."""

    def GET(self):
        get_run_cam()
        return self.template_render.plugins.webcam(cam_options, log.events(NAME))


    def POST(self):
        cam_options.web_update(web.input())
        raise web.seeother(plugin_url(settings_page))


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(cam_options)


class download_page(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'image/jpeg')
        try:
           f= open('./data/image.jpg')
           return f.read()
        except exception:
           return 
          
