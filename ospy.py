#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# Local imports
from log import hook_logging
from options import options

import web
import plugins


class OSPyApp(web.application):
    """Allow program to select HTTP port."""

    def run(self, port=options.web_port, *middleware):  # get port number from options settings
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

if __name__ == '__main__':
    hook_logging()

    # Import these only after logging has been hooked and we need it:
    from scheduler import scheduler
    from urls import urls

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