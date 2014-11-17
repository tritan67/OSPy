# !/usr/bin/env python
# -*- coding: utf-8 -*-

# urls is used by web.py. When a GET request is received, the corresponding class is executed.

import api

urls = [
    '/login', 'webpages.login_page',
    '/logout', 'webpages.logout_page',

    '/',  'webpages.home_page',

    '/programs', 'webpages.programs_page',
    '/program/(new|[0-9]+)', 'webpages.program_page',

    '/runonce', 'webpages.runonce_page',

    '/log', 'webpages.log_page',
    '/options', 'webpages.options_page',
    '/stations', 'webpages.stations_page',

    '/sn', 'webpages.get_set_station_page',
    '/ttu', 'webpages.toggle_temp_page',
    '/rev', 'webpages.show_revision_page',
    '/wl', 'webpages.water_log_page',

    '/status.json', 'webpages.api_status_json',
    '/log.json', 'webpages.api_log_json',

    '/api', api.app_OSPyAPI,
]