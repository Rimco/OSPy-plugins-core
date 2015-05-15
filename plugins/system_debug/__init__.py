#!/usr/bin/env python
# this plugins print debug info from ./data/events.log 

from ospy.webpages import ProtectedPage
from ospy import log
from ospy import helpers

from plugins import plugin_url
from plugins import PluginOptions
import web
import os

NAME = 'System Debug Information'
LINK = 'status_page'

debug_options = PluginOptions(
    NAME,
    {
        "debug_event": True,
        "info_event": True,
        "warning_event": True,
        "error_event": True
    }
)


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
        for line in reversed(list(open(log.EVENT_FILE))):
            if debug_options['debug_event']:
              if 'DEBUG' in line:
                result.append(line.strip())
             
            if debug_options['info_event']:
              if 'INFO' in line:
                result.append(line.strip())
             
            if debug_options['warning_event']:
              if 'WARNING' in line:
                result.append(line.strip())
            
            if debug_options['error_event']:
              if 'ERROR' in line:
                result.append(line.strip())       

           
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

        return self.plugin_render.system_debug(debug_options,get_overview())


class settings_page(ProtectedPage):
    """Save an html page for entering debug filtering."""

    def POST(self):
        debug_options.web_update(web.input())
        raise web.seeother(plugin_url(status_page), True)
