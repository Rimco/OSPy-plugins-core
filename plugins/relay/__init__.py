# !/usr/bin/env python

import time
import web

from ospy.webpages import ProtectedPage
from ospy.outputs import outputs

NAME = 'Relay Test'
LINK = 'test_page'


class test_page(ProtectedPage):
    """Test relay by turning it on for a short time, then off."""

    def GET(self):
        try:
            outputs.relay_output = True
            time.sleep(3)
            outputs.relay_output = False
        except Exception:
            pass
        raise web.seeother('/')  # return to home page


def start():
    pass


stop = start
