# !/usr/bin/env python
# this plugins check sha on github and update ospy file from github

from threading import Thread, Event, Condition
from random import randint
import time
import subprocess
import sys
import traceback
import logging

import web
from webpages import ProtectedPage
from helpers import restart
from log import log
import version


NAME = 'System Update'
LINK = '/UPs'
URLS = [
    '/UPs', 'plugins.system_update.status_page',
    '/UPsr', 'plugins.system_update.refresh_page',
    '/UPu', 'plugins.system_update.update_page',
    '/UPr', 'plugins.system_update.restart_page'
]


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
        subprocess.call(command.split())

        command = 'git config --get remote.origin.url'
        remote = subprocess.check_output(command.split()).strip()
        if remote:
            self.status['remote'] = remote

        command = 'git log -1 origin/master --format=%cd --date=short'
        new_date = subprocess.check_output(command.split()).strip()

        command = 'git rev-list origin/master --count --first-parent'
        new_revision = int(subprocess.check_output(command.split()))

        command = 'git log HEAD..origin/master --oneline'
        changes = '  ' + '\n  '.join(subprocess.check_output(command.split()).split('\n'))

        if new_revision == version.revision and new_date == version.ver_date:
            log.log_event(NAME, 'Up-to-date.')
            self.status['can_update'] = False
        elif new_revision > version.revision:
            log.log_event(NAME, 'New version is available!')
            log.log_event(NAME, 'Currently running revision: %d (%s)' % (version.revision, version.ver_date))
            log.log_event(NAME, 'Available revision: %d (%s)' % (new_revision, new_date))
            log.log_event(NAME, 'Changes:\n' + changes)
            self.status['can_update'] = True
        else:
            log.log_event(NAME, 'Running unknown version!')
            log.log_event(NAME, 'Currently running revision: %d (%s)' % (version.revision, version.ver_date))
            log.log_event(NAME, 'Available revision: %d (%s)' % (new_revision, new_date))
            self.status['can_update'] = False

        self._done.acquire()
        self._done.notify_all()
        self._done.release()

    def run(self):
        self._sleep(randint(3, 10))  # Sleep some time to prevent printing before startup information

        while not self._stop.is_set():
            try:
                log.clear(NAME)
                self._update_rev_data()
                self.started.set()
                self._sleep(3600)

            except Exception:
                self.started.set()
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                log.log_event(NAME, 'System update plug-in encountered error:\n' + err_string)
                self._sleep(60)

checker = None


################################################################################
# Helper functions:                                                            #
################################################################################
def perform_update():
    # ignore local chmod permission
    command = "git config core.filemode false"  # http://superuser.com/questions/204757/git-chmod-problem-checkout-screws-exec-bit
    subprocess.call(command.split())

    command = "git pull"
    output = subprocess.check_output(command.split())

    log.log_event(NAME, 'Update result: ' + output, logging.DEBUG)
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
        return self.template_render.plugins.system_update(checker.status, log.events(NAME))


class refresh_page(ProtectedPage):
    """Refresh status and show it."""

    def GET(self):
        checker.update_wait()
        raise web.seeother('/UPs')


class update_page(ProtectedPage):
    """Update OSPi from github and return text message from comm line."""

    def GET(self):
        perform_update()
        return self.template_render.restarting('/UPs')


class restart_page(ProtectedPage):
    """Restart system."""

    def GET(self):
        restart(3)
        return self.template_render.restarting('/UPs')
