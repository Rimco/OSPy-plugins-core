# !/usr/bin/env python

from threading import Thread, Event
import traceback
import json
import time
import datetime
import web
from ospy.helpers import stop_onrain
from ospy.log import log
from ospy.options import options, rain_blocks
from ospy.webpages import ProtectedPage
from ospy.weather import weather
from plugins import PluginOptions, plugin_url

NAME = 'Weather-based Rain Delay'
LINK = 'settings_page'

plugin_options = PluginOptions(
    NAME,
    {
        'enabled': False,
        'delay_duration': 24
    })

################################################################################
# Main function loop:                                                          #
################################################################################
class weather_to_delay(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._stop_event = Event()

        self._sleep_time = 0
        self.start()

    def stop(self):
        self._stop_event.set()

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop_event.is_set():
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        while not self._stop_event.is_set():
            try:
                if plugin_options['enabled']:  # if Weather-based Rain Delay plug-in is enabled
                    log.clear(NAME)
                    log.info(NAME, 'Checking rain status...')

                    current_data = weather.get_current_data()

                    if 'precipitation' in current_data:
                        if current_data['precipitation'] > 0.75:
                            log.info(NAME, 'Rain detected. Adding delay of ' + str(plugin_options['delay_duration']))
                            rain_blocks[NAME] = datetime.datetime.now() + datetime.timedelta(hours=float(plugin_options['delay_duration']))
                            stop_onrain()

                        elif current_data['precipitation'] > 0.1:
                            log.info(NAME, 'No rain detected. No action.')

                        else:
                            log.info(NAME, 'Good weather detected. Removing rain delay.')
                            if NAME in rain_blocks:
                                del rain_blocks[NAME]

                    self._sleep(3600)
                else:
                    log.clear(NAME)
                    log.info(NAME, 'Plug-in is disabled.')
                    if NAME in rain_blocks:
                        del rain_blocks[NAME]
                    self._sleep(24 * 3600)

            except Exception:
                log.error(NAME, 'Weather-based Rain Delay plug-in:\n' + traceback.format_exc())
                self._sleep(3600)


checker = None

################################################################################
# Helper functions:                                                            #
################################################################################

def start():
    global checker
    if checker is None:
        checker = weather_to_delay()


def stop():
    global checker
    if checker is not None:
        checker.stop()
        checker.join()
        checker = None
    if NAME in rain_blocks:
        del rain_blocks[NAME]

################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for entering Weather-based Rain Delay adjustments"""

    def GET(self):
        return self.plugin_render.weather_based_rain_delay(plugin_options, log.events(NAME))

    def POST(self):
        plugin_options.web_update(web.input())
        if checker is not None:
            checker.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format"""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(plugin_options)

