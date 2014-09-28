#!/usr/bin/env python
# -*- coding: utf-8 -*-

# System imports
import datetime
import json
import time
import web

# Local imports
from helpers import *
from inputs import inputs
from log import log
from options import level_adjustments
from options import options
from options import plugins
from options import rain_blocks
from stations import stations
import scheduler
import version


class WebPage(object):
    def __init__(self):
        template_globals = {
            'str': str,
            'bool': bool,
            'int': int,
            'eval': eval,
            'round': round,
            'datetime': datetime,
            'json': json,
            'isinstance': isinstance,

            'inputs': inputs,
            'level_adjustments': level_adjustments,
            'options': options,
            'plugins': plugins,
            'rain_blocks': rain_blocks,
            'stations': stations,
            'log': log,

            'version': version,

            'cpu_temp': get_cpu_temp(),
            'now': time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()
        }
        self.template_render = web.template.render('templates', globals=template_globals, base='base')


class ProtectedPage(WebPage):
    def __init__(self):
        check_login(True)
        WebPage.__init__(self)


class login_page(WebPage):
    """Login page"""

    def GET(self):
        return self.template_render.login(signin_form())

    def POST(self):
        my_signin = signin_form()

        if not my_signin.validates():
            return self.template_render.login(my_signin)
        else:
            web.config._session.user = 'admin'
            raise web.seeother('/')


class logout_page(WebPage):
    def GET(self):
        web.config._session.user = 'anonymous'
        raise web.seeother('/')


class home_page(ProtectedPage):
    """Open Home page."""

    def GET(self):
        qdict = web.input()
        if 'stop_all' in qdict and qdict['stop_all'] == '1':
            log.finish_run(None)
            stations.clear()
            raise web.seeother('/')

        return self.template_render.home()

    def POST(self):
        qdict = web.input()
        if 'scheduler_enabled' in qdict and qdict['scheduler_enabled'] != '':
            options.scheduler_enabled = True if qdict['scheduler_enabled'] == '1' else False
        if 'manual_mode' in qdict and qdict['manual_mode'] != '':
            options.manual_mode = True if qdict['manual_mode'] == '1' else False

        if 'rain_block' in qdict:
            if qdict['rain_block'] != '0' and qdict['rain_block'] != '':
                options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=float(qdict['rain_block']))
            elif qdict['rain_block'] == '0':
                options.rain_block = datetime.datetime.now()

        if 'level_adjustment' in qdict and qdict['level_adjustment'] != '':
            options.level_adjustment = float(qdict['level_adjustment']) / 100

        raise web.seeother('/')  # Send browser back to home page


class options_page(ProtectedPage):
    """Open the options page for viewing and editing."""

    def GET(self):
        qdict = web.input()
        errorCode = qdict.get('errorCode', 'none')

        return self.template_render.options(errorCode)

    def POST(self):
        qdict = web.input()

        save_to_options(qdict)

        if 'master' in qdict:
            m = int(qdict['master'])
            if m < 0:
                stations.master = None
            elif m < stations.count():
                stations.master = m

        if 'old_password' in qdict and qdict['old_password'] != "":
            try:
                if test_password(qdict['old_password']):
                    if qdict['new_password'] == "":
                        raise web.seeother('/options?errorCode=pw_blank')
                    elif qdict['new_password'] == qdict['check_password']:
                        options.password_salt = password_salt()  # Make a new salt
                        options.password_hash = password_hash(qdict['new_password'], options.password_salt)
                    else:
                        raise web.seeother('/options?errorCode=pw_mismatch')
                else:
                    raise web.seeother('/options?errorCode=pw_wrong')
            except KeyError:
                pass

        raise web.seeother('/')


class stations_page(ProtectedPage):
    """Stations page"""

    def GET(self):
        return self.template_render.stations()

    def POST(self):
        qdict = web.input()

        for s in xrange(0, stations.count()):
            stations[s].name = qdict["%d_name" % s]
            stations[s].enabled = True if qdict.get("%d_enabled" % s, 'off') == 'on' else False
            stations[s].ignore_rain = True if qdict.get("%d_ignore_rain" % s, 'off') == 'on' else False
            if stations.master is not None:
                stations[s].activate_master = True if qdict.get("%d_activate_master" % s, 'off') == 'on' else False

        raise web.seeother('/')


class get_set_station_page(ProtectedPage):
    """Return a page containing a number representing the state of a station or all stations if 0 is entered as station number."""

    def GET(self):
        qdict = web.input()

        sid = get_input(qdict, 'sid', 0, int) - 1
        set_to = get_input(qdict, 'set_to', None, int)
        set_time = get_input(qdict, 'set_time', 0, int)

        if set_to is None:
            if sid < 0:
                status = '<!DOCTYPE html>\n'
                status += ''.join(('1' if s.active else '0') for s in stations)
                return status
            elif sid < stations.count():
                status = '<!DOCTYPE html>\n'
                status += '1' if stations.get(sid).active else '0'
                return status
            else:
                return 'Station ' + str(sid+1) + ' not found.'
        elif options.manual_mode:
            if set_to:  # if status is on
                start = datetime.datetime.now()
                new_schedule = {
                    'active': True,
                    'program': -1,
                    'station': sid,
                    'program_name': "Manual mode",
                    'manual': True,
                    'blocked': False,
                    'start': start,
                    'end': start + datetime.timedelta(days=3650),
                    'uid': '%s-%d-%d' % (str(start), -1, sid),
                    'usage': 1.0  # FIXME
                }
                if set_time > 0:  # if an optional duration time is given
                    new_schedule['end'] = datetime.datetime.now() + datetime.timedelta(seconds=set_time)

                log.start_run(new_schedule)
                stations.activate(new_schedule['station'])

            else:  # If status is off
                stations.deactivate(sid)
                active = log.active_runs()
                for interval in active:
                    if interval['station'] == sid:
                        log.finish_run(interval)

            raise web.seeother('/')
        else:
            return 'Manual mode not active.'


class view_runonce_page(ProtectedPage):
    """Open a page to view and edit a run once program."""

    def GET(self):
        return self.template_render.runonce()


class change_runonce_page(ProtectedPage):
    """Start a Run Once program. This will override any running program."""

    def GET(self):
        qdict = web.input()
        if not options.scheduler_enabled:   # check operation status
            return
        gv.rovals = json.loads(qdict['t'])
        gv.rovals.pop()
        stations = [0] * gv.sd['nbrd']
        gv.ps = []  # program schedule (for display)
        gv.rs = []  # run schedule
        for i in range(gv.sd['nst']):
            gv.ps.append([0, 0])
            gv.rs.append([0, 0, 0, 0])
        for i, v in enumerate(gv.rovals):
            if v:  # if this element has a value
                gv.rs[i][0] = gv.now
                gv.rs[i][2] = v
                gv.rs[i][3] = 98
                gv.ps[i][0] = 98
                gv.ps[i][1] = v
                stations[i / 8] += 2 ** (i % 8)
        schedule_stations(stations)
        raise web.seeother('/')


class view_programs_page(ProtectedPage):
    """Open programs page."""

    def GET(self):
        return self.template_render.programs()


class modify_program_page(ProtectedPage):
    """Open page to allow program modification."""

    def GET(self):
        qdict = web.input()
        pid = int(qdict['pid'])
        prog = []
        if pid != -1:
            mp = gv.pd[pid][:]  # Modified program
            if mp[1] >= 128 and mp[2] > 1:  # If this is an interval program
                dse = int(gv.now / 86400)
                # Convert absolute to relative days remaining for display
                rel_rem = (((mp[1] - 128) + mp[2]) - (dse % mp[2])) % mp[2]
                mp[1] = rel_rem + 128  # Update from saved value.
            prog = str(mp).replace(' ', '')
        return self.template_render.modify(pid, prog)


class change_program_page(ProtectedPage):
    """Add a program or modify an existing one."""

    def GET(self):
        qdict = web.input()
        pnum = int(qdict['pid']) + 1  # program number
        cp = json.loads(qdict['v'])
        if cp[0] == 0 and pnum == gv.pon:  # if disabled and program is running
            for i in range(len(gv.ps)):
                if gv.ps[i][0] == pnum:
                    gv.ps[i] = [0, 0]
                if gv.srvals[i]:
                    gv.srvals[i] = 0
            for i in range(len(gv.rs)):
                if gv.rs[i][3] == pnum:
                    gv.rs[i] = [0, 0, 0, 0]
        if cp[1] >= 128 and cp[2] > 1:
            dse = int(gv.now / 86400)
            ref = dse + cp[1] - 128
            cp[1] = (ref % cp[2]) + 128
        if qdict['pid'] == '-1':  # add new program
            gv.pd.append(cp)
        else:
            gv.pd[int(qdict['pid'])] = cp  # replace program
        jsave(gv.pd, 'programs')
        gv.sd['nprogs'] = len(gv.pd)
        raise web.seeother('/vp')


class delete_program_page(ProtectedPage):
    """Delete one or all existing program(s)."""

    def GET(self):
        qdict = web.input()
        if qdict['pid'] == '-1':
            del gv.pd[:]
            jsave(gv.pd, 'programs')
        else:
            del gv.pd[int(qdict['pid'])]
        jsave(gv.pd, 'programs')
        gv.sd['nprogs'] = len(gv.pd)
        raise web.seeother('/vp')


class enable_program_page(ProtectedPage):
    """Activate or deactivate an existing program(s)."""

    def GET(self):
        qdict = web.input()
        gv.pd[int(qdict['pid'])][0] = int(qdict['enable'])
        jsave(gv.pd, 'programs')
        raise web.seeother('/vp')


class view_log_page(ProtectedPage):
    """View Log"""

    def GET(self):
        return self.template_render.log()

    def POST(self):
        qdict = web.input()
        if 'clear' in qdict:
            log.clear_runs()
        raise web.seeother('/log')


class run_now_page(ProtectedPage):
    """Run a scheduled program now. This will override any running programs."""

    def GET(self):
        qdict = web.input()
        pid = int(qdict['pid'])
        p = gv.pd[int(qdict['pid'])]  # program data
        if not p[0]:  # if program is disabled
            raise web.seeother('/vp')
        stop_stations()
        extra_adjustment = plugin_adjustment()
        for b in range(len(p[7:7 + gv.sd['nbrd']])):  # check each station
            for s in range(8):
                sid = b * 8 + s  # station index
                if sid + 1 == gv.sd['mas']:  # skip if this is master valve
                    continue
                if p[7 + b] & 1 << s:  # if this station is scheduled in this program
                    gv.rs[sid][2] = p[6] * options.level_adjustment / 100 * extra_adjustment  # duration scaled by water level
                    gv.rs[sid][3] = pid + 1  # store program number in schedule
                    gv.ps[sid][0] = pid + 1  # store program number for display
                    gv.ps[sid][1] = gv.rs[sid][2]  # duration
        schedule_stations(p[7:7 + gv.sd['nbrd']])
        raise web.seeother('/')


class show_revision_page(ProtectedPage):
    """Show revision info to the user. Use: [URL of Pi]/rev."""

    def GET(self):
        revpg = '<!DOCTYPE html>\n'
        revpg += 'Python Interval Program for OpenSprinkler Pi<br/><br/>\n'
        revpg += 'Compatable with OpenSprinkler firmware 1.8.3.<br/><br/>\n'
        revpg += 'Includes plugin architecture\n'
        revpg += 'ospy.py version: v' + gv.ver_str + '<br/><br/>\n'
        revpg += 'Updated ' + gv.ver_date + '\n'
        return revpg


class toggle_temp_page(ProtectedPage):
    """Change units of Raspi's CPU temperature display on home page."""

    def GET(self):
        qdict = web.input()
        options.temp_unit = "F" if qdict['tunit'] == "C" else "C"
        raise web.seeother('/')


class api_status_page(ProtectedPage):
    """Simple Status API"""

    def GET(self):
        statuslist = []
        for station in stations.get():
            if station.enabled or station.is_master:
                status = {
                    'station': station.index,
                    'status': 'on' if station.active else 'off',
                    'reason': 'master' if station.is_master else '',
                    'master': 1 if station.is_master else 0,
                    'programName': '',
                    'remaining': 0}

                if not station.is_master:
                    if options.manual_mode:
                        status['programName'] = 'Manual Mode'
                    else:
                        if not options.scheduler_enabled:
                            status['reason'] = 'system_off'
                        elif not station.ignore_rain and inputs.rain_sensed():
                            status['reason'] = 'rain_sensed'
                        elif not station.ignore_rain and rain_blocks.seconds_left():
                            status['reason'] = 'rain_delay'
                        else:
                            active = log.active_runs()
                            for interval in active:
                                if not interval['blocked'] and interval['station'] == station.index:
                                    status['programName'] = interval['program_name']

                                    status['status'] = 'on'
                                    status['reason'] = 'program'
                                    status['remaining'] = max(0, (interval['end'] -
                                                                  datetime.datetime.now()).total_seconds())

                statuslist.append(status)

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist)


class api_log_page(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        qdict = web.input()
        data = []
        if 'date' in qdict:
            # date parameter filters the log values returned; "yyyy-mm-dd" format
            date = datetime.datetime.strptime(qdict['date'], "%Y-%m-%d").date()
            check_end = datetime.datetime.combine(date, datetime.time.max)
            check_start = datetime.datetime.combine(date, datetime.time.min)
            log_start = check_start - datetime.timedelta(days=1)

            events = scheduler.combined_schedule(log_start, check_end)
            for interval in events:
                # Return only records that are visible on this day:
                if check_start <= interval['start'] <= check_end or check_start <= interval['end'] <= check_end:
                    data.append(self._convert(interval))

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

    def _convert(self, interval):
            duration = (interval['end'] - interval['start']).total_seconds()
            minutes, seconds = divmod(duration, 60)
            return {
                'program': interval['program'],
                'program_name': interval['program_name'],
                'active': interval['active'],
                'manual': interval.get('manual', False),
                'blocked': interval.get('blocked', False),
                'station': interval['station'],
                'date': interval['start'].strftime("%Y-%m-%d"),
                'start': interval['start'].strftime("%H:%M:%S"),
                'duration': "%02d:%02d" % (minutes, seconds)
            }

class water_log_page(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        events = log.finished_runs() + log.active_runs()

        data = "Date, Start Time, Zone, Duration, Program\n"
        for interval in events:
            # return only records that are visible on this day:
            duration = (interval['end'] - interval['start']).total_seconds()
            minutes, seconds = divmod(duration, 60)

            data += ', '.join([
                interval['start'].strftime("%Y-%m-%d"),
                interval['start'].strftime("%H:%M:%S"),
                str(interval['station']),
                "%02d:%02d" % (minutes, seconds),
                interval['program_name']
            ]) + '\n'

        web.header('Content-Type', 'text/csv')
        return data