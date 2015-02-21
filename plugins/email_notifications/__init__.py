# !/usr/bin/env python
# this plugins send email at google email

import json
import time
import os
import traceback
import smtplib
from threading import Thread, Event

from email.encoders import encode_base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.multipart import MIMEBase

import web
from ospy.webpages import ProtectedPage
from plugins import PluginOptions, plugin_url
from ospy.options import options
from ospy.stations import stations
from ospy.inputs import inputs
from ospy.log import log


NAME = 'Email Notifications'
LINK = 'settings_page'

email_options = PluginOptions(
    NAME,
    {
        'emllog': False,
        'emlrain': False,
        'emlrun': False,
        'emlusr': '',
        'emlpwd': '',
        'emladr': '',
        'emlsubject': "Report from OSPy"
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################
class EmailSender(Thread):
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

    def try_mail(self, subject, text, attachment=None):
        log.clear(NAME)
        try:
            email(subject, text, attachment)  # send email with attachment from
            log.info(NAME, 'Email was sent:\n' + text)
        except Exception:
            err_string = ''.join(traceback.format_exc())
            log.warning(NAME, 'Email was not sent!\n' + err_string)

    def run(self):
        last_rain = False
        finished_count = len([run for run in log.finished_runs() if not run['blocked']])

        if email_options["emllog"]:          # if eml_log send email is enable (on)
            body = ('On ' + time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(time.time())) +
                    ': System was powered on.')
            self.try_mail(email_options['emlsubject'], body)  #TODO: add log file?

        while not self._stop.is_set():
            try:
                # Send E-amil if rain is detected
                if email_options["emlrain"]:
                    if inputs.rain_sensed() and not last_rain:
                        body = ('On ' + time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(time.time())) +
                                ': System detected rain.')
                        self.try_mail(email_options['emlsubject'], body)
                    last_rain = inputs.rain_sensed()

                # Send E-mail if a new finished run is found
                if email_options["emlrun"]:
                    finished = [run for run in log.finished_runs() if not run['blocked']]
                    if len(finished) > finished_count:
                        body = time.strftime("On %d.%m.%Y at %H:%M:%S:\n", time.localtime(time.time()))
                        for run in finished[finished_count:]:
                            duration = (run['end'] - run['start']).total_seconds()
                            minutes, seconds = divmod(duration, 60)
                            body += "Finished run:\n"
                            body += "  Program: %s\n" % run['program_name']
                            body += "  Station: %s\n" % stations.get(run['station']).name
                            body += "  Start time: %s \n" % run['start'].strftime("%Y-%m-%d at %H:%M:%S")
                            body += "  Duration: %02d:%02d\n\n" % (minutes, seconds)

                        self.try_mail(email_options['emlsubject'], body)

                    finished_count = len(finished)

                self._sleep(5)

            except Exception:
                err_string = ''.join(traceback.format_exc())
                log.error(NAME, 'E-mail plug-in:\n' + err_string)
                self._sleep(60)


email_sender = None


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global email_sender
    if email_sender is None:
        email_sender = EmailSender()


def stop():
    global email_sender
    if email_sender is not None:
        email_sender.stop()
        email_sender.join()
        email_sender = None


def email(subject, text, attach=None):
    """Send email with with attachments. If subject is None, the default will be used."""
    if email_options['emlusr'] != '' and email_options['emlpwd'] != '' and email_options['emladr'] != '':
        gmail_user = email_options['emlusr']          # User name
        gmail_name = options.name                     # OSPi name
        gmail_pwd = email_options['emlpwd']           # User password
        #--------------
        msg = MIMEMultipart()
        msg['From'] = gmail_name
        msg['To'] = email_options['emladr']
        msg['Subject'] = subject or email_options['emlsubject']
        msg.attach(MIMEText(text))
        if attach is not None:              # If insert attachments
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach, 'rb').read())
            encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
            msg.attach(part)
        mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(gmail_user, gmail_pwd)
        mailServer.sendmail(gmail_name, email_options['emladr'],
                            msg.as_string())   # name + e-mail address in the From: field
        mailServer.close()
    else:
        raise Exception('E-mail plug-in is not properly configured!')


################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for entering email adjustments."""

    def GET(self):
        return self.plugin_render.email_notifications(email_options, log.events(NAME))

    def POST(self):
        email_options.web_update(web.input())

        if email_sender is not None:
            email_sender.update()
        raise web.seeother(plugin_url(settings_page), True)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(email_options)
