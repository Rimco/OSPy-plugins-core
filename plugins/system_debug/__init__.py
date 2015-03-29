#!/usr/bin/env python
# this plugins print debug info from ./data/events.log 

from ospy.webpages import ProtectedPage
from ospy import log
from ospy import helpers

from plugins import plugin_url
import web
import os

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
        with open(log.EVENT_FILE) as fh:
            result.append(fh.read())
    except Exception:
        result.append('Error: Log file missing.')

    return result


################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        qdict = web.input()
        delete = helpers.get_input(qdict, 'delete', False, lambda x: True)
        if delete:
            try:
                os.remove(log.EVENT_FILE)
            except Exception:
                pass
            raise web.seeother(plugin_url(status_page), True)

        return self.plugin_render.system_debug(get_overview())

