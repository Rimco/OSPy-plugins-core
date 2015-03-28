# !/usr/bin/env python

from threading import Thread, Event
import traceback
import json
import time
import datetime
import re
import urllib
import urllib2
import web
from ospy.helpers import stop_onrain
from ospy.log import log
from ospy.options import options
from ospy.webpages import ProtectedPage
from plugins import PluginOptions, plugin_url

NAME = 'Weather-based Rain Delay'
LINK = 'settings_page'

plugin_options = PluginOptions(
    NAME,
    {
        'enabled': False,
        'delay_duration': 24,
        'weather_provider': 'yahoo',
        'wapikey': ''
    })

################################################################################
# Main function loop:                                                          #
################################################################################
class weather_to_delay(Thread):
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
        once_text = True                          # text1 plug-in is disabled
        two_text = True                           # text2 plug-in is enabled

        while not self._stop.is_set():
            try:
                if plugin_options['enabled']:         # if Weather-based Rain Delay plug-in is enabled
                    if once_text:                      # text enabled on the status window
                        log.clear(NAME)
                        log.info(NAME, 'Weather-based Rain Delay plug-in is enabled.')
                        once_text = False
                        two_text = True

                    log.info(NAME, 'Checking rain status...')

                    weather = get_weather_data() if plugin_options[
                                                        'weather_provider'] == "yahoo" else get_wunderground_weather_data()
                    delay = code_to_delay(weather['code'])

                    if delay > 0:
                        log.info(NAME, 'Rain detected: ' + weather['text'] + '. Adding delay of ' + str(delay))
                        options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=float(delay))
                        stop_onrain()

                    elif delay == 0:
                        log.info(NAME, 'No rain detected: ' + weather['text'] + '. No action.')

                    elif delay < 0:
                        log.info(NAME, 'Good weather detected: ' + weather['text'] + '. Removing rain delay.')
                        options.rain_block = datetime.datetime.now()

                    self._sleep(3600)


                else:
                    if two_text:                       # text disabled on the status window
                        log.clear(NAME)
                        log.info(NAME, 'Weather-based Rain Delay plug-in is disabled.')
                        two_text = False
                        once_text = True

                    self._sleep(1)

            except Exception:
                err_string = ''.join(traceback.format_exc())
                log.error(NAME, 'Weather-based Rain Delay plug-in:\n' + err_string)
                self._sleep(60)


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


# Resolve location to LID
def get_wunderground_lid():
    if re.search("pws:", options.location):
        lid = options.location
    else:
        data = urllib2.urlopen(
            "http://autocomplete.wunderground.com/aq?h=0&query=" + urllib.quote_plus(options.location))
        data = json.load(data)
        if data is None:
            return ""
        lid = "zmw:" + data['RESULTS'][0]['zmw']

    return lid


def get_woeid():
    data = urllib2.urlopen(
        "http://query.yahooapis.com/v1/public/yql?q=select%20woeid%20from%20geo.placefinder%20where%20text=%22" +
        urllib.quote_plus(options.location) + "%22").read()
    woeid = re.search("<woeid>(\d+)</woeid>", data)
    if woeid is None:
        return 0
    return woeid.group(1)


def get_weather_data():
    woeid = get_woeid()
    if woeid == 0:
        return {}
    data = urllib2.urlopen("http://weather.yahooapis.com/forecastrss?w=" + woeid).read()
    if data is None:
        return {}
    newdata = re.search("<yweather:condition\s+text=\"([\w|\s]+)\"\s+code=\"(\d+)\"\s+temp=\"(\d+)\"\s+date=\"(.*)\"",
                        data)
    weather = {"text": newdata.group(1),
               "code": newdata.group(2)}
    return weather


def get_wunderground_weather_data():
    lid = get_wunderground_lid()
    if lid == "":
        return []
    data = urllib2.urlopen(
        "http://api.wunderground.com/api/" + plugin_options['wapikey'] + "/conditions/q/" + lid + ".json")
    data = json.load(data)
    if data is None:
        return {}
    if 'error' in data['response']:
        return {}
    weather = {"text": data['current_observation']['weather'],
               "code": data['current_observation']['icon']}
    return weather


# Lookup code and get the set delay
def code_to_delay(code):
    if plugin_options['weather_provider'] == "yahoo":
        adverse_codes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 35, 37, 38, 39, 40, 41, 42,
                         43, 44, 45, 46, 47]
        reset_codes = [36]
    else:
        adverse_codes = ["flurries", "sleet", "rain", "sleet", "snow", "tstorms"]
        adverse_codes += ["chance" + code_name for code_name in adverse_codes]
        reset_codes = ["sunny", "clear", "mostlysunny", "partlycloudy"]
    if code in adverse_codes:
        return float(plugin_options['delay_duration'])
    if code in reset_codes:
        return -1
    return 0


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

