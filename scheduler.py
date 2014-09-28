#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
from threading import Thread
import datetime
import logging
import time

# Local imports
from inputs import inputs
from log import log
from options import level_adjustments
from options import options
from options import rain_blocks
from programs import programs
from stations import stations


def predicted_schedule(start_time, end_time):
    """Determines all schedules for the given time range.
    To calculate what should currently be active, a start time of some time (a day) ago should be used."""

    adjustment = level_adjustments.total_adjustment()
    max_usage = 1.01 if options.sequential else 1000000  # FIXME

    rain_block_start = datetime.datetime.now()
    rain_block_end = rain_blocks.block_end()

    skip_uids = [entry['uid'] for entry in log.finished_runs()]
    current_active = log.active_runs()

    current_usage = 0.0
    for active in current_active:
        current_usage += active['usage']
        if active['uid'] not in skip_uids:
            skip_uids.append(active['uid'])

    # Aggregate per station:
    station_schedules = {}
    for program in programs.get():
        if not program.enabled:
            continue

        program_intervals = program.active_intervals(start_time, end_time)

        for station in sorted(program.stations):
            if station not in station_schedules:
                station_schedules[station] = []

            for interval in program_intervals:
                new_schedule = {
                    'active': None,
                    'program': program.index,
                    'program_name': program.name, # Save it because programs can be reordered
                    'manual': program.manual,
                    'blocked': False,
                    'start': interval['start'],
                    'end': interval['end'],
                    'uid': '%s-%d-%d' % (str(interval['start']), program.index, station),
                    'usage': 1.0  # FIXME
                }
                if new_schedule['uid'] not in skip_uids:
                    station_schedules[station].append(new_schedule)

    all_intervals = []
    # Adjust for weather and remove overlap:
    for station, schedule in station_schedules.iteritems():
        for interval in schedule:
            time_delta = interval['end'] - interval['start']
            time_delta = datetime.timedelta(seconds=(time_delta.days * 24 * 3600 + time_delta.seconds) * adjustment)
            interval['end'] = interval['start'] + time_delta
            interval['adjustment'] = adjustment

        last_end = datetime.datetime(2000, 1, 1)
        for interval in schedule:
            if last_end > interval['start']:
                time_delta = last_end - interval['start']
                interval['start'] += time_delta
                interval['end'] += time_delta
            last_end = interval['end']

            new_interval = {
                'station': station
            }
            new_interval.update(interval)

            all_intervals.append(new_interval)

    # Make list of entries sorted on time (stable sorted on station #)
    all_intervals.sort(key=lambda inter: inter['start'])

    # Try to add each interval
    for interval in all_intervals:

        while True:
            # Delete all intervals that have finished
            while current_active:
                if current_active[0]['end'] > interval['start']:
                    break
                current_usage -= current_active[0]['usage']
                del current_active[0]

            # Check if we can add it now
            if current_usage + interval['usage'] <= max_usage:
                if not stations.get(interval['station']).ignore_rain and \
                        rain_block_start <= interval['start'] < rain_block_end:
                    interval['blocked'] = 'rain delay'
                elif not stations.get(interval['station']).ignore_rain and inputs.rain_sensed():
                    interval['blocked'] = 'rain sensor'
                else:
                    current_usage += interval['usage']
                    # Add the newly "activated" station to the active list
                    for index in range(len(current_active)):
                        if current_active[index]['end'] > interval['end']:
                            current_active.insert(index, interval)
                            break
                    else:
                        current_active.append(interval)
                break  # We added or blocked it
            else:
                # Shift this interval to next possibility
                next_option = current_active[0]['end'] + datetime.timedelta(seconds=options.station_delay)
                time_to_next = next_option - interval['start']
                interval['start'] += time_to_next
                interval['end'] += time_to_next

    all_intervals.sort(key=lambda inter: inter['start'])

    return all_intervals


def combined_schedule(start_time, end_time):
    current_time = datetime.datetime.now()
    if current_time < start_time:
        result = predicted_schedule(start_time, end_time)
    elif current_time > end_time:
        result = [entry for entry in log.finished_runs() if start_time <= entry['start'] <= end_time or
                                                            start_time <= entry['end'] <= end_time]
    else:
        result = log.finished_runs()
        result += log.active_runs()
        predicted = predicted_schedule(start_time, end_time)
        result += [entry for entry in predicted if current_time <= entry['start'] <= end_time]

    return result


class _Scheduler(Thread):
    def __init__(self):
        super(_Scheduler, self).__init__()
        self.daemon = True
        options.add_callback('system_enabled', self._option_cb)
        options.add_callback('manual_mode', self._option_cb)

        # If manual mode is active, finish all stale runs:
        if options.manual_mode:
            log.finish_run(None)

    def _option_cb(self, key, old, new):
        # Clear if:
        #   - Manual mode changed
        #   - System was disabled
        if key == 'manual_mode' or not new:
            log.finish_run(None)
            stations.clear()

    def run(self):
        while True:
            self._check_schedule()
            time.sleep(5)

    @staticmethod
    def _check_schedule():
        if options.system_enabled:
            current_time = datetime.datetime.now()
            check_start = current_time - datetime.timedelta(days=1)
            check_end = current_time + datetime.timedelta(days=1)

            rain = not options.manual_mode and (rain_blocks.block_end() > datetime.datetime.now() or
                                                inputs.rain_sensed())

            active = log.active_runs()
            for entry in active:
                ignore_rain = stations.get(entry['station']).ignore_rain
                if entry['end'] <= current_time or (rain and not ignore_rain and not entry['blocked']):
                    log.finish_run(entry)
                    stations.deactivate(entry['station'])

            if not options.manual_mode:
                schedule = predicted_schedule(check_start, check_end)
                #logging.debug("Schedule: %s", str(schedule))
                for entry in schedule:
                    if entry['start'] <= current_time < entry['end']:
                        log.start_run(entry)
                        if not entry['blocked']:
                            stations.activate(entry['station'])

            if stations.master is not None:
                master_on = False

                # It's easy if we don't have to use delays:
                if options.master_on_delay == options.master_off_delay == 0:
                    active = log.active_runs()

                    for entry in active:
                        if not entry['blocked'] and stations.get(entry['station']).activate_master:
                            master_on = True
                            break

                else:
                    # In manual mode we cannot predict, we only know what is currently running and the history
                    if options.manual_mode:
                        active = log.finished_runs() + log.active_runs()
                    else:
                        active = combined_schedule(check_start, check_end)

                    for entry in active:
                        if not entry['blocked'] and stations.get(entry['station']).activate_master:
                            if entry['start'] + datetime.timedelta(seconds=options.master_on_delay) \
                                    <= current_time < \
                                    entry['end'] + datetime.timedelta(seconds=options.master_off_delay):
                                master_on = True
                                break

                master_station = stations.get(stations.master)

                if master_on != master_station.active:
                    master_station.active = master_on

scheduler = _Scheduler()


























