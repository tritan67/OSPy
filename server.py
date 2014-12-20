#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# Local imports

from options import options
from urls import urls
from scheduler import scheduler

import web
import plugins


class OSPyApp(web.application):
    """Allow program to select HTTP port."""

    def run(self, port=options.web_port, *middleware):  # get port number from options settings
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

app = None


def start():
    global app
    ##############################
    #### web.py setup         ####
    ##############################
    app = OSPyApp(urls, globals())
    web.config.debug = False  # Improves page load speed
    if web.config.get('_session') is None:
        web.config._session = web.session.Session(app, web.session.DiskStore('sessions'),
                                                  initializer={'user': 'anonymous'})
    app.notfound = lambda: web.seeother('/')

    scheduler.start()
    plugins.start_enabled_plugins()
    app.run()


def stop():
    global app
    if app is not None:
        app.stop()
        app = None