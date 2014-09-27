#!/usr/bin/env python
# -*- coding: utf-8 -*-

# System imports
import datetime
import json
import time
import web

# Local imports
from helpers import *
from options import level_adjustments
from options import options
from options import plugins
from options import rain_blocks
from stations import stations
import version


class WebPage(object):
    def __init__(self):
        template_globals = {
            'str': str,
            'bool': bool,
            'int': int,
            'eval': eval,
            'json': json,
            'isinstance': isinstance,

            'level_adjustments': level_adjustments,
            'options': options,
            'plugins': plugins,
            'rain_blocks': rain_blocks,
            'stations': stations,

            'version': version,

            'session': web.config._session,
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
        return self.template_render.home()


class change_values_page(ProtectedPage):
    """Save controller values, return browser to home page."""

    def GET(self):
        qdict = web.input()
        if 'rsn' in qdict and qdict['rsn'] == '1':
            stop_stations()
            raise web.seeother('/')
        if 'en' in qdict and qdict['en'] == '':
            qdict['en'] = '1'  # default
        elif 'en' in qdict and qdict['en'] == '0':
            stations.clear()
        if 'mm' in qdict and qdict['mm'] == '0':
            clear_mm()
        if 'rd' in qdict and qdict['rd'] != '0' and qdict['rd'] != '':
            gv.sd['rd'] = float(qdict['rd'])
            gv.sd['rdst'] = gv.now + gv.sd['rd'] * 3600 + 1  # +1 adds a smidge just so after a round trip the display hasn't already counted down by a minute.
            stop_onrain()
        elif 'rd' in qdict and qdict['rd'] == '0':
            gv.sd['rdst'] = 0
        for key in qdict.keys():
            try:
                gv.sd[key] = int(qdict[key])
            except Exception:
                pass
        jsave(gv.sd, 'sd')
        raise web.seeother('/')  # Send browser back to home page


class options_page(ProtectedPage):
    """Open the options page for viewing and editing."""

    def GET(self):
        qdict = web.input()
        errorCode = qdict.get('errorCode', 'none')

        return self.template_render.options(errorCode)

    def POST(self):
        qdict = web.input()

        for option in options.OPTIONS:
            key = option['key']
            if 'category' in option:
                if key in qdict:
                    value = qdict[key]
                    if isinstance(option['default'], bool):
                        options[key] = True if value and value != "off" else False
                    elif isinstance(option['default'], int):
                        if 'min' in option and int(qdict[key]) < option['min']:
                            continue
                        if 'max' in option and int(qdict[key]) > option['max']:
                            continue
                        options[key] = int(qdict[key])
                    else:
                        options[key] = qdict[key]
                else:
                    if isinstance(option['default'], bool):
                        options[key] = False

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

        raise web.seeother('/options') # FIXME: restore to / when home is fixed

    def update_scount(self, qdict):
        """Increase or decrease the number of stations displayed when number of expansion boards is
        changed in options."""
        if int(qdict['onbrd']) + 1 > gv.sd['nbrd']:  # Lengthen lists
            incr = int(qdict['onbrd']) - (gv.sd['nbrd'] - 1)
            for i in range(incr):
                gv.sd['mo'].append(0)
                gv.sd['ir'].append(0)
                gv.sd['show'].append(255)
            ln = len(gv.snames)
            for i in range(incr*8):
                gv.snames.append("S"+('%d' % (i+1+ln)))
            for i in range(incr * 8):
                gv.srvals.append(0)
                gv.ps.append([0, 0])
                gv.rs.append([0, 0, 0, 0])
            for i in range(incr):
                gv.sbits.append(0)
        elif int(qdict['onbrd']) + 1 < gv.sd['nbrd']:  # Shorten lists
            onbrd = int(qdict['onbrd'])
            decr = gv.sd['nbrd'] - (onbrd + 1)
            gv.sd['mo'] = gv.sd['mo'][:(onbrd + 1)]
            gv.sd['ir'] = gv.sd['ir'][:(onbrd + 1)]
            gv.sd['show'] = gv.sd['show'][:(onbrd + 1)]
            # unused variables
            # nlst = gv.snames
            # nlst = nlst[:8+(onbrd*8)]
            newlen = gv.sd['nst'] - decr * 8
            gv.srvals = gv.srvals[:newlen]
            gv.ps = gv.ps[:newlen]
            gv.rs = gv.rs[:newlen]
            gv.snames = gv.snames[:newlen]
            gv.sbits = gv.sbits[:onbrd + 1]
        jsave(gv.snames, 'snames')


class view_stations_page(ProtectedPage):
    """Open a page to view and edit a run once program."""

    def GET(self):
        return self.template_render.stations()


class change_stations_page(ProtectedPage):
    """Save changes to station names, ignore rain and master associations."""

    def GET(self):
        qdict = web.input()
        for i in range(gv.sd['nbrd']):  # capture master associations
            if 'm' + str(i) in qdict:
                try:
                    gv.sd['mo'][i] = int(qdict['m' + str(i)])
                except ValueError:
                    gv.sd['mo'][i] = 0
            if 'i' + str(i) in qdict:
                try:
                    gv.sd['ir'][i] = int(qdict['i' + str(i)])
                except ValueError:
                    gv.sd['ir'][i] = 0
            if 'sh' + str(i) in qdict:
                try:
                    gv.sd['show'][i] = int(qdict['sh' + str(i)])
                except ValueError:
                    gv.sd['show'][i] = 255
            if 'd' + str(i) in qdict:
                try:
                    gv.sd['show'][i] = ~int(qdict['d' + str(i)])&255
                except ValueError:
                    gv.sd['show'][i] = 255
        names = []
        for i in range(gv.sd['nst']):
            if 's' + str(i) in qdict:
                names.append(qdict['s'+str(i)])
            else:
                names.append('S'+str(i+1))
        gv.snames = names
        jsave(names, 'snames')
        jsave(gv.sd, 'sd')
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
                status += ''.join(str(x) for x in gv.srvals)
                return status
            elif sid < gv.sd['nbrd'] * 8:
                status = '<!DOCTYPE html>\n'
                status += str(gv.srvals[sid])
                return status
            else:
                return 'Station ' + str(sid+1) + ' not found.'
        elif options.manual_mode:
            if set_to:  # if status is
                gv.rs[sid][0] = gv.now  # set start time to current time
                if set_time > 0:  # if an optional duration time is given
                    gv.rs[sid][2] = set_time
                    gv.rs[sid][1] = gv.rs[sid][0] + set_time  # stop time = start time + duration
                else:
                    gv.rs[sid][1] = float('inf')  # stop time = infinity
                gv.rs[sid][3] = 99  # set program index
                gv.ps[sid][1] = set_time
                gv.sd['bsy'] = 1
                time.sleep(1)
            else:  # If status is off
                gv.rs[sid][1] = gv.now
                time.sleep(1)
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
        if not options.system_enabled:   # check operation status
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
        records = read_log()
        return self.template_render.log(records)


class clear_log_page(ProtectedPage):
    """Delete all log records"""

    def GET(self):
        qdict = web.input()
        with open('./data/log.json', 'w') as f:
            f.write('')
        raise web.seeother('/vl')


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
                    gv.rs[sid][2] = p[6] * gv.sd['wl'] / 100 * extra_adjustment  # duration scaled by water level
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
        if qdict['tunit'] == "C":
            gv.sd['tu'] = "F"
        else:
            gv.sd['tu'] = "C"
        jsave(gv.sd, 'sd')
        raise web.seeother('/')


class api_status_page(ProtectedPage):
    """Simple Status API"""

    def GET(self):
        statuslist = []
        for bid in range(0, gv.sd['nbrd']):
            for s in range(0, 8):
                if (gv.sd['show'][bid] >> s) & 1 == 1:
                    sid = bid * 8 + s
                    sn = sid + 1
                    sbit = (gv.sbits[bid] >> s) & 1
                    irbit = (gv.sd['ir'][bid] >> s) & 1
                    status = {'station': sid, 'status': 'disabled', 'reason': '', 'master': 0, 'programName': '',
                              'remaining': 0}
                    if options.system_enabled == 1:
                        if sbit:
                            status['status'] = 'on'
                        if not irbit:
                            if gv.sd['rd'] != 0:
                                status['reason'] = 'rain_delay'
                            if gv.sd['urs'] != 0 and gv.sd['rs'] != 0:
                                status['reason'] = 'rain_sensed'
                        if sn == gv.sd['mas']:
                            status['master'] = 1
                            status['reason'] = 'master'
                        else:
                            rem = gv.ps[sid][1]
                            if rem > 65536:
                                rem = 0

                            id_nr = gv.ps[sid][0]
                            pname = 'P' + str(id_nr)
                            if id_nr == 255 or id_nr == 99:
                                pname = 'Manual Mode'
                            if id_nr == 254 or id_nr == 98:
                                pname = 'Run-once Program'

                            if sbit:
                                status['status'] = 'on'
                                status['reason'] = 'program'
                                status['programName'] = pname
                                status['remaining'] = rem
                            else:
                                if gv.ps[sid][0] == 0:
                                    status['status'] = 'off'
                                else:
                                    status['status'] = 'waiting'
                                    status['reason'] = 'program'
                                    status['programName'] = pname
                                    status['remaining'] = rem
                    else:
                        status['reason'] = 'system_off'
                    statuslist.append(status)
        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist)


class api_log_page(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        qdict = web.input()
        thedate = qdict['date']
        # date parameter filters the log values returned; "yyyy-mm-dd" format
        theday = datetime.date(*map(int, thedate.split('-')))
        prevday = theday - datetime.timedelta(days=1)
        prevdate = prevday.strftime('%Y-%m-%d')

        records = read_log()
        data = []

        for r in records:
            event = json.loads(r)

            # return any records starting on this date
            if 'date' not in qdict or event['date'] == thedate:
                data.append(event)
                # also return any records starting the day before and completing after midnight
            if event['date'] == prevdate:
                if int(event['start'].split(":")[0]) * 60 + int(event['start'].split(":")[1]) + int(
                        event['duration'].split(":")[0]) > 24 * 60:
                    data.append(event)

        web.header('Content-Type', 'application/json')
        return json.dumps(data)


class water_log_page(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        records = read_log()
        data = "Date, Start Time, Zone, Duration, Program\n"
        for r in records:
            event = json.loads(r)
            data += event["date"] + ", " + event["start"] + ", " + str(event["station"]) + ", " + event[
                "duration"] + ", " + event["program"] + "\n"

        web.header('Content-Type', 'text/csv')
        return data
