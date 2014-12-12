#!/usr/bin/env python
# this plugins print debug info from ./data/events.log 

from webpages import ProtectedPage
from options import options

NAME = 'System Debug Information'
LINK = 'status_page'


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    pass

stop = start


def get_overview():
    """Returns the info data as a list of lines."""
    result = []
    try:
        result.append(open('./data/events.log').read())
    except Exception:
        result.append('Error: None events.log files')

    return result


################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        return self.template_render.plugins.system_debug(get_overview())
