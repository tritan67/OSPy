#!/usr/bin/env python
# This plugin save image from webcam to ./data/image.jpg
# fswebcam -r 1280x720  ./data/image.jpg


import json
import subprocess
import sys
import traceback
import re

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
                log.info(NAME, 'Please wait...' )
                cmd = "sudo fswebcam -r " + cam_options['resolution'] + "./data/image.jpg"
                proc = subprocess.Popen(
                     cmd,
                     stderr=subprocess.STDOUT,  # merge stdout and stderr
                     stdout=subprocess.PIPE,
                     shell=True)
                output = proc.communicate()[0]
                text = re.sub('\x1b[^m]*m', '', output) # remove color character from communication in text
                log.info(NAME, text)  
                               

            else: 
                log.clear(NAME)
                log.info(NAME, 'Plugin is disabled...')
  

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
           pass
          
