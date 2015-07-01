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
        "error_event": True,
        "log_records": 0,
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
        if debug_options['log_records'] > 0:     # delete lines in debug log if records is bigger
          file = open(log.EVENT_FILE,"r")
          num_lines = sum(1 for line in file)
          num_records = debug_options['log_records']
          data = file.readlines()
          file.close()
          print num_lines
          if num_lines > num_records:
             del data[:num_lines-(num_records-1)] 
             fout = open(log.EVENT_FILE, "w")
             fout.writelines(data)
             fout.close()
             raise web.seeother(plugin_url(status_page), True)
                   
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
        result.append('Error: Log file missing. Enable it in system options.')

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
    """Save an html page for entering debug filtering or submit change."""

    def POST(self):
        debug_options.web_update(web.input())
        raise web.seeother(plugin_url(status_page), True)
