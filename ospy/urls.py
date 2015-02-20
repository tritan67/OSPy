# !/usr/bin/env python
# -*- coding: utf-8 -*-

# urls is used by web.py. When a GET request is received, the corresponding class is executed.

import api
import plugins

urls = [
    '/login', 'ospy.webpages.login_page',
    '/logout', 'ospy.webpages.logout_page',

    '/',  'ospy.webpages.home_page',

    '/programs', 'ospy.webpages.programs_page',
    '/program/(new|[0-9]+)', 'ospy.webpages.program_page',

    '/runonce', 'ospy.webpages.runonce_page',

    '/log', 'ospy.webpages.log_page',
    '/options', 'ospy.webpages.options_page',
    '/stations', 'ospy.webpages.stations_page',
    '/help', 'ospy.webpages.help_page',

    '/sn', 'ospy.webpages.get_set_station_page',
    '/ttu', 'ospy.webpages.toggle_temp_page',
    '/rev', 'ospy.webpages.show_revision_page',
    '/wl', 'ospy.webpages.water_log_page',

    '/status.json', 'ospy.webpages.api_status_json',
    '/log.json', 'ospy.webpages.api_log_json',

    '/api', api.get_app(),
    '/plugins', plugins.get_app(),
]