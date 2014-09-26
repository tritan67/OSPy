# !/usr/bin/env python
# -*- coding: utf-8 -*-

import web  # the Web.py module. See webpy.org (Enables the Python OpenSprinkler web interface)
from urls import urls  # Provides access to URLs for UI pages

from options import options

##############################
#### web.py setup         ####
##############################

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

if __name__ == '__main__':

    #########################################################
    #### Code to import all webpages and plugin webpages ####
    #import plugins
    #
    #print 'plugins loaded:'
    #for name in plugins.__all__:
    #    print ' ', name

    app.notfound = lambda: web.seeother('/')
    app.run()