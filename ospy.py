#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# Local imports

# We want to hook the logging before importing other modules which might already use log statements:
from log import hook_logging
hook_logging()

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

if __name__ == '__main__':
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