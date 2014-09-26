# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
import thread

import web  # the Web.py module. See webpy.org (Enables the Python OpenSprinkler web interface)
from urls import urls  # Provides access to URLs for UI pages

from options import options


##############################
#### Revision information ####
import subprocess

major_ver = 2
minor_ver = 1

try:
    revision = int(subprocess.check_output(['git', 'rev-list', '--count', '--first-parent', 'HEAD']))
except Exception:
    print 'Could not use git to determine version!'
    revision = 999
ver_str = '%d.%d.%d' % (major_ver, minor_ver, revision)

try:
    ver_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).strip()
except Exception:
    print 'Could not use git to determine date of last commit!'
    ver_date = '2014-09-10'


def timing_loop():
    """ ***** Main timing algorithm. Runs in a separate thread.***** """
    print 'Starting timing loop \n'
    while True:  # infinite loop
        time.sleep(1)


class OSPyApp(web.application):
    """Allow program to select HTTP port."""

    def run(self, port=options.web_port, *middleware):  # get port number from options settings
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))


app = OSPyApp(urls, globals())
web.config.debug = False  # Improves page load speed
if web.config.get('_session') is None:
    web.config._session = web.session.Session(app, web.session.DiskStore('sessions'),
                                              initializer={'user': 'anonymous'})
template_globals = {
    'options': options,
    'str': str,
    'eval': eval,
    'session': web.config._session,
    'json': json
}

template_render = web.template.render('templates', globals=template_globals, base='base')

if __name__ == '__main__':

    #########################################################
    #### Code to import all webpages and plugin webpages ####
    #import plugins
    #
    #print 'plugins loaded:'
    #for name in plugins.__all__:
    #    print ' ', name

    thread.start_new_thread(timing_loop, ())

    app.notfound = lambda: web.seeother('/')
    app.run()