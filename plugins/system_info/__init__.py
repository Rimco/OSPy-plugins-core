#!/usr/bin/env python
# this plugins print system info os on web 

import platform
from collections import OrderedDict

import traceback
from ospy import helpers
from ospy.webpages import ProtectedPage
from ospy.options import options
import subprocess
from ospy.log import log

NAME = 'System Information'
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
    log.clear(NAME)
    meminfo = helpers.get_meminfo()
    netdevs = helpers.get_netdevs()

    result.append('System release: ' + platform.release())
    result.append('System name:    ' + platform.system())
    result.append('Node:           ' + platform.node())
    result.append('Machine:        ' + platform.machine())
    result.append('Total memory:   ' + meminfo['MemTotal'])
    result.append('Free memory:    ' + meminfo['MemFree'])
    if netdevs:
        for dev, info in netdevs.items():
            result.append('%-16s %s MiB %s MiB' % (dev + ':', info['rx'], info['tx']))
    else:
        result.append('Network:        Unknown')
    result.append('Uptime:         ' + helpers.uptime())
    result.append('CPU temp:       ' + helpers.get_cpu_temp(options.temp_unit) + ' ' + options.temp_unit)
    result.append('MAC adress: ' + helpers.get_mac())
    try:
        result.append('I2C HEX Adress:')
        rev = str(0 if helpers.get_rpi_revision() == 1 else 1)
        cmd = 'sudo i2cdetect -y ' + rev
        result.append(process(cmd))
    except Exception:
        log.error(NAME, 'System info plug-in:\n' + traceback.format_exc())
    log.info(NAME, result)
    return result


def process(cmd):
    """process in system"""
    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        shell=True)
    output = proc.communicate()[0]
    return output.decode('utf-8')
################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page"""

    def GET(self):
        return self.plugin_render.system_info(get_overview())
