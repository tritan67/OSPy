# -*- coding: utf-8 -*-
__author__ = 'Rimco'

import os
import random
import time
import subprocess
import datetime
from threading import Thread

import web
from web import form
from web.session import sha1

##############################
#### Function Definitions ####

def determine_platform():
    try:
        import RPi.GPIO
        return 'pi'
    except Exception:
        pass
    try:
        import Adafruit_BBIO.GPIO
        return 'bo'
    except Exception:
        pass
    return ''


def get_rpi_revision():
    try:
        import RPi.GPIO as GPIO
        return GPIO.RPI_REVISION
    except ImportError:
        return 0


def reboot(wait=1, block=False):
    if block:
        from stations import stations
        stations.clear()
        time.sleep(wait)
        print 'Rebooting...'
        subprocess.Popen(['reboot'])
    else:
        t = Thread(target=reboot, args=(wait, True))
        t.start()


def poweroff(wait=1, block=False):
    if block:
        from stations import stations
        stations.clear()
        time.sleep(wait)
        print 'Powering off...'
        subprocess.Popen(['poweroff'])
    else:
        t = Thread(target=poweroff, args=(wait, True))
        t.start()


def restart(wait=1, block=False):
    if block:
        from stations import stations
        stations.clear()
        time.sleep(wait)
        print 'Restarting...'
        subprocess.Popen('service ospy restart'.split())
    else:
        t = Thread(target=restart, args=(wait, True))
        t.start()


def uptime():
    """Returns UpTime for RPi"""
    try:
        with open("/proc/uptime") as f:
            total_sec = float(f.read().split()[0])
            string = str(datetime.timedelta(seconds=total_sec)).split('.')[0]
    except Exception:
        string = 'Uptime unavailable'

    return string


def get_ip():
    """Returns the IP adress if available."""
    try:
        arg = 'ip route list'
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        data = p.communicate()
        split_data = data[0].split()
        ipaddr = split_data[split_data.index('src') + 1]
        return ipaddr
    except Exception:
        return "No IP Settings"


def get_cpu_temp(unit=None):
    """Returns the temperature of the CPU if available."""
    try:
        platform = determine_platform()
        if platform == 'bo':
            res = os.popen('cat /sys/class/hwmon/hwmon0/device/temp1_input').readline()
            temp = str(int(float(res) / 1000))
        elif platform == 'pi':
            res = os.popen('vcgencmd measure_temp').readline()
            temp = res.replace("temp=", "").replace("'C\n", "")
        else:
            temp = str(0)

        if unit == 'F':
            return str(9.0 / 5.0 * float(temp) + 32)
        elif unit is not None:
            return str(float(temp))
        else:
            return temp
    except Exception:
        return '!!'


def baseurl():
    """Return URL app is running under."""
    result = web.ctx['home']
    return result


def timestr(t):
    return str((t / 60 >> 0) / 10 >> 0) + str((t / 60 >> 0) % 10) + ":" + str((t % 60 >> 0) / 10 >> 0) + str(
        (t % 60 >> 0) % 10)


def stop_onrain():
    """Stop stations that do not ignore rain."""
    from stations import stations
    for station in stations.get():
        if not station.ignore_rain:
            station.activated = False


########################
#### Login Handling ####

def password_salt():
    return "".join(chr(random.randint(33, 127)) for _ in xrange(64))


def password_hash(password, salt):
    return sha1(password + salt).hexdigest()


def test_password(storage):
    from options import options
    return options.password_hash == password_hash(storage['password'], options.password_salt)


def check_login(redirect=False):
    from options import options
    qdict = web.input()

    try:
        if options.no_password:
            return True

        if web.config._session.user == 'admin':
            return True
    except KeyError:
        pass

    if 'pw' in qdict:
        if test_password(qdict['pw']):
            return True
        if redirect:
            raise web.unauthorized()
        return False

    if redirect:
        raise web.seeother('/login')
    return False


signin_form = form.Form(
    form.Password('password', description='Password:'),
    validators=[
        form.Validator(
            "Incorrect password, please try again",
            test_password
        )
    ]
)


def get_input(qdict, key, default=None, cast=None):
    result = default
    if key in qdict:
        result = qdict[key]
        if cast is not None:
            result = cast(result)
    return result
