# !/usr/bin/env python
# this plugins send email at google email

import json
import time
import os
import sys
import traceback
import smtplib
from threading import Thread
from random import randint
from email import Encoders
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText

import web
import helpers
from webpages import ProtectedPage


NAME = 'Email Notifications'
LINK = 'settings_page'

email_options = PluginOptions(
    NAME,
    {
        'emlusr': '',
        'emlpwd': '',
        'emladr': '',
        'emllog': 'off',
        'emlrain': 'off',
        'emlrun': 'off'
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################
class EmailSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()
        self.status = ''

        self._sleep_time = 0

    def add_status(self, msg):
        if self.status:
            self.status += '\n' + msg
        else:
            self.status = msg
        print msg

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def try_mail(self, subject, text, attachment=None):
        self.status = ''
        try:
            email(subject, text, attachment)  # send email with attachment from
            self.add_status('Email was sent: ' + text)
        except Exception as err:
            self.add_status('Email was not sent! ' + str(err))

    def run(self):
        time.sleep(randint(3, 10))  # Sleep some time to prevent printing before startup information

        dataeml = get_email_options()  # load data from file
        subject = "Report from OSPy"  # Subject in email
        last_rain = 0
        was_running = False

        self.status = ''
        self.add_status('Email plugin is started')

        if dataeml["emllog"] != "off":          # if eml_log send email is enable (on)
            body = ('On ' + time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(time.time())) +
                    ': System was powered on.')
            self.try_mail(subject, body, "/home/pi/OSPy/data/log.json")

        while True:
            try:
                # send if rain detected
                if dataeml["emlrain"] != "off":             # if eml_rain send email is enable (on)
                    if inputs.rain_sensed() != last_rain:            # send email only 1x if  gv.sd rs change
                        last_rain = inputs.rain_sensed()

                        if inputs.rain_sensed() and options.rain_sensor_enabled:    # if rain sensed and use rain sensor
                            body = ('On ' + time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(time.time())) +
                                    ': System detected rain.')
                            self.try_mail(subject, body)    # send email without attachments

                if dataeml["emlrun"] != "off":              # if eml_rain send email is enable (on)
                    running = False
                    # TODO
                    for b in range(gv.sd['nbrd']):          # Check each station once a second
                        for s in range(8):
                            sid = b * 8 + s  # station index
                            if gv.srvals[sid]:  # if this station is on
                                running = True
                                was_running = True

                    if was_running and not running:
                        was_running = False
                        if gv.lrun[1] == 98:
                            pgr = 'Run-once'
                        elif gv.lrun[1] == 99:
                            pgr = 'Manual'
                        else:
                            pgr = str(gv.lrun[1])

                        dur = str(duration_str(gv.lrun[2]))
                        start = time.gmtime(gv.now - gv.lrun[2])

                        body = 'On ' + time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(time.time())) + \
                               ': System last run: ' + 'Station ' + str(gv.lrun[0]) + \
                               ', Program ' + pgr + \
                               ', Duration ' + dur + \
                               ', Start time ' + time.strftime("%d.%m.%Y at %H:%M:%S", start)

                        self.try_mail(subject, body)     # send email without attachment

                self._sleep(1)

            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                self.add_status('Email plugin encountered error: ' + err_string)
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


def get_email_options():
    """Returns the defaults data from file."""
    dataeml = {
        'emlusr': email_options['emlusr'],
        'emlpwd': email_options['emlpwd'],
        'emladr': email_options['emladr'],
        'emllog': email_options['emllog'],
        'emlrain': email_options['emlrain'],
        'emlrun': email_options['emlrun'],
        'status': email_sender.status
    }
    return dataeml


def email(subject, text, attach=None):
    """Send email with with attachments"""
    dataeml = get_email_options()
    if dataeml['emlusr'] != '' and dataeml['emlpwd'] != '' and dataeml['emladr'] != '':
        gmail_user = dataeml['emlusr']          # User name
        gmail_name = options.name               # OSPi name
        gmail_pwd = dataeml['emlpwd']           # User password
        #--------------
        msg = MIMEMultipart()
        msg['From'] = gmail_name
        msg['To'] = dataeml['emladr']
        msg['Subject'] = subject
        msg.attach(MIMEText(text))
        if attach is not None:              # If insert attachments
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach, 'rb').read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
            msg.attach(part)
        mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(gmail_user, gmail_pwd)
        mailServer.sendmail(gmail_name, dataeml['emladr'], msg.as_string())   # name + e-mail address in the From: field
        mailServer.close()
    else:
        raise Exception('E-mail plug-in is not properly configured!')


################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for entering email adjustments."""

    def GET(self):
        return self.template_render.plugins.email_adj(get_email_options())

    def POST(self):
        email_options_options.web_update(web.input())

        email_sender.update()
        raise web.seeother(plugin_url(settings_page))


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(get_email_options())