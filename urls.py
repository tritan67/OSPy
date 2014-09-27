# !/usr/bin/env python
# -*- coding: utf-8 -*-

# urls is used by web.py. When a GET request is received, the corresponding class is executed.

urls = [
    '/',  'webpages.home_page',
    '/cv', 'webpages.change_values_page',
    '/options', 'webpages.options_page',
    '/vs', 'webpages.view_stations_page',
    '/cs', 'webpages.change_stations_page',
    '/sn', 'webpages.get_set_station_page',
    '/vr', 'webpages.view_runonce_page',
    '/cr', 'webpages.change_runonce_page',
    '/vp', 'webpages.view_programs_page',
    '/mp', 'webpages.modify_program_page',
    '/cp', 'webpages.change_program_page',
    '/dp', 'webpages.delete_program_page',
    '/ep', 'webpages.enable_program_page',
    '/vl', 'webpages.view_log_page',
    '/cl', 'webpages.clear_log_page',
    '/lo', 'webpages.log_options_page',
    '/rp', 'webpages.run_now_page',
    '/ttu', 'webpages.toggle_temp_page',
    '/rev', 'webpages.show_revision_page',
    '/wl', 'webpages.water_log_page',
    '/api/status', 'webpages.api_status_page',
    '/api/log', 'webpages.api_log_page',
    '/login', 'webpages.login_page',
    '/logout', 'webpages.logout_page'
]