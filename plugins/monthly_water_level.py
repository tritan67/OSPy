# !/usr/bin/env python


import json
import time
from threading import Thread, Event

import web
from log import log
from options import options
from options import level_adjustments
from helpers import mkdir_p
from webpages import ProtectedPage
from plugins import PluginOptions


NAME = 'Monthly Water Level'
LINK = 'settings_page'


plugin_options = PluginOptions(
    NAME,
    {
        key: 100 for key in range(12)
    })


class MonthChecker(Thread):
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
        while not self._stop.is_set():
            month = time.localtime().tm_mon-1  # Current month.
            level_adjustments[NAME] = plugin_options[month]/100.0  # Set the water level% (levels list is zero based).
            log.debug(NAME, 'Monthly Adjust: Setting water level to %d%%' % plugin_options[month])

            self._sleep(3600)


checker = None


def start():
    global checker
    if checker is None:
        checker = MonthChecker()


def stop():
    global checker
    if checker is not None:
        checker.stop()
        checker.join()
        checker = None


class settings_page(ProtectedPage):
    """Load an html page for entering monthly irrigation time adjustments"""

    def GET(self):
        return self.template_render.plugins.monthly_water_level(plugin_options)

    def POST(self):
        qdict = web.input()
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        vals = {}
        for index, month in enumerate(months):
            vals[index] = qdict[month]
        plugin_options.web_update(vals)
        if checker is not None:
            checker.update()
        raise web.seeother('/')