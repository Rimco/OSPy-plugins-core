# !/usr/bin/env python
# this plugins check sha on github and update ospy file from github

from threading import Thread, Event, Condition
import time
import subprocess
import sys
import traceback

import web
from ospy.webpages import ProtectedPage
from ospy.helpers import restart
from ospy.log import log
from plugins import PluginOptions, plugin_url
from ospy import version


NAME = 'System Update'
LINK = 'status_page'

plugin_options = PluginOptions(
    NAME,
    {
        'auto_update': False,
        'use_update': False
    }
)


class StatusChecker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.started = Event()
        self._done = Condition()
        self._stop = Event()

        self.status = {
            'ver_str': version.ver_str,
            'ver_date': version.ver_date,
            'remote': 'None!',
            'remote_branch': 'origin/master',
            'can_update': False}

        self._sleep_time = 0
        self.start()

    def stop(self):
        self._stop.set()

    def update_wait(self):
        self._done.acquire()
        self._sleep_time = 0
        self._done.wait(10)
        self._done.release()

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop.is_set():
            time.sleep(1)
            self._sleep_time -= 1

    def _update_rev_data(self):
        """Returns the update revision data."""

        command = 'git remote update'
        subprocess.check_output(command.split())

        command = 'git config --get remote.origin.url'
        remote = subprocess.check_output(command.split()).strip()
        if remote:
            self.status['remote'] = remote

        command = 'git rev-parse --abbrev-ref --symbolic-full-name @{u}'
        remote_branch = subprocess.check_output(command.split()).strip()
        if remote_branch:
            self.status['remote_branch'] = remote_branch

        command = 'git log -1 %s --format=%%cd --date=short' % remote_branch
        new_date = subprocess.check_output(command.split()).strip()

        command = 'git rev-list %s --count --first-parent' % remote_branch
        new_revision = int(subprocess.check_output(command.split()))

        command = 'git log HEAD..%s --oneline' % remote_branch
        changes = '  ' + '\n  '.join(subprocess.check_output(command.split()).split('\n'))

        if new_revision == version.revision and new_date == version.ver_date:
            log.info(NAME, 'Up-to-date.')
            self.status['can_update'] = False
        elif new_revision > version.revision:
            log.info(NAME, 'New version is available!')
            log.info(NAME, 'Currently running revision: %d (%s)' % (version.revision, version.ver_date))
            log.info(NAME, 'Available revision: %d (%s)' % (new_revision, new_date))
            log.info(NAME, 'Changes:\n' + changes)
            self.status['can_update'] = True
        else:
            log.info(NAME, 'Running unknown version!')
            log.info(NAME, 'Currently running revision: %d (%s)' % (version.revision, version.ver_date))
            log.info(NAME, 'Available revision: %d (%s)' % (new_revision, new_date))
            self.status['can_update'] = False

        self._done.acquire()
        self._done.notify_all()
        self._done.release()

    def run(self):
        while not self._stop.is_set():
            try:
                if plugin_options['use_update']:
                    log.clear(NAME)
                    self._update_rev_data()

                    if self.status['can_update'] and plugin_options['auto_update']:
                        perform_update()

                    self.started.set()
                self._sleep(3600)

            except Exception:
                self.started.set()
                log.error(NAME, 'System update plug-in:\n' + traceback.format_exc())
                self._sleep(60)


checker = None


################################################################################
# Helper functions:                                                            #
################################################################################
def perform_update():
    # ignore local chmod permission
    command = "git config core.filemode false"  # http://superuser.com/questions/204757/git-chmod-problem-checkout-screws-exec-bit
    subprocess.check_output(command.split())

    command = "git reset --hard"
    subprocess.check_output(command.split())

    command = "git pull"
    output = subprocess.check_output(command.split())

    log.debug(NAME, 'Update result: ' + output)
    restart(3)


def start():
    global checker
    if checker is None:
        checker = StatusChecker()


def stop():
    global checker
    if checker is not None:
        checker.stop()
        checker.join()
        checker = None


################################################################################
# Web pages:                                                                   #
################################################################################
class status_page(ProtectedPage):
    """Load an html page rev data."""

    def GET(self):
        checker.started.wait(10)    # Make sure we are initialized
        return self.plugin_render.system_update(plugin_options, log.events(NAME), checker.status)

    def POST(self):
        plugin_options.web_update(web.input())
        if checker is not None:
            checker.update()

        raise web.seeother(plugin_url(status_page), True)


class refresh_page(ProtectedPage):
    """Refresh status and show it."""

    def GET(self):
        checker.update_wait()
        raise web.seeother(plugin_url(status_page), True)


class update_page(ProtectedPage):
    """Update OSPi from github and return text message from comm line."""

    def GET(self):
        perform_update()
        return self.core_render.restarting(plugin_url(status_page))


class restart_page(ProtectedPage):
    """Restart system."""

    def GET(self):
        restart(3)
        return self.core_render.restarting(plugin_url(status_page))
