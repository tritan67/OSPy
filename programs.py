#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
import datetime

# Local imports
from options import options


class ProgramType(object):
    CUSTOM = 0
    REPEAT_SIMPLE = 1
    REPEAT_ADVANCED = 2
    DAYS_SIMPLE = 3
    DAYS_ADVANCED = 4
    WEEKLY_ADVANCED = 5


class _Program(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_programs', '_loading']

    def __init__(self, programs_instance, index):
        self._programs = programs_instance
        self._loading = True

        self.name = "Program %02d" % (index+1)
        self.stations = []
        self.enabled = True

        self._schedule = []
        self._modulo = 24*60
        self._manual = False  # Non-repetitive (run-once) if True
        self._start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

        self.type = ProgramType.CUSTOM
        self.type_data = [[]]

        options.load(self, index)
        self._loading = False

    @property
    def index(self):
        return self._programs.get().index(self)

    @property
    def schedule(self):
        return [interval[:] for interval in self._schedule]

    @schedule.setter
    def schedule(self, value):
        new_schedule = []
        for interval in value:
            new_schedule = self._update_schedule(new_schedule, self.modulo, interval[0], interval[1])

        self._schedule = new_schedule
        self.type = ProgramType.CUSTOM
        self.type_data = [value]

    @property
    def modulo(self):
        return self._modulo

    @property
    def manual(self):
        return self._manual

    @property
    def start(self):
        return self._start

    def clear(self):
        self._schedule = []

    def set_repeat_simple(self, start_min, duration_min, pause_min, repeat_times, repeat_days, start_date):
        new_schedule = []
        for i in range(repeat_times+1):
            new_schedule = self._update_schedule(new_schedule, repeat_days*1440, start_min, start_min + duration_min)
            start_min += pause_min + duration_min

        self._modulo = repeat_days*1440
        self._manual = False
        self._start = datetime.datetime.combine(start_date, datetime.time.min)
        self._schedule = new_schedule

        self.type = ProgramType.REPEAT_SIMPLE
        self.type_data = [start_min, duration_min, pause_min, repeat_times, repeat_days, start_date]

    def set_repeat_advanced(self, schedule, repeat_days, start_date):
        new_schedule = []
        for interval in schedule:
            new_schedule = self._update_schedule(new_schedule, repeat_days*1440, interval[0], interval[1])

        self._schedule = new_schedule
        self._modulo = repeat_days*1440
        self._manual = False
        self._start = datetime.datetime.combine(start_date, datetime.time.min)

        self.type = ProgramType.REPEAT_ADVANCED
        self.type_data = [schedule, repeat_days, start_date]

    def set_days_simple(self, start_min, duration_min, pause_min, repeat_times, days):
        new_schedule = []
        for day in days:
            day_start_min = start_min + 1440 * day
            for i in range(repeat_times+1):
                new_schedule = self._update_schedule(new_schedule, 7*1440, day_start_min, day_start_min + duration_min)
                day_start_min += pause_min + duration_min

        self._modulo = 7*1440
        self._manual = False
        self._start = datetime.datetime.combine(datetime.date.today() -
                                                datetime.timedelta(days=datetime.date.today().weekday()),
                                                datetime.time.min)  # First day of current week
        self._schedule = new_schedule

        self.type = ProgramType.DAYS_SIMPLE
        self.type_data = [start_min, duration_min, pause_min, repeat_times, days[:]]

    def set_days_advanced(self, schedule, days):
        new_schedule = []
        for day in days:
            offset = 1440 * day
            for interval in schedule:
                new_schedule = self._update_schedule(new_schedule, 7*1440, interval[0] + offset, interval[1] + offset)

        self._modulo = 7*1440
        self._manual = False
        self._start = datetime.datetime.combine(datetime.date.today() -
                                                datetime.timedelta(days=datetime.date.today().weekday()),
                                                datetime.time.min)  # First day of current week
        self._schedule = new_schedule

        self.type = ProgramType.DAYS_SIMPLE
        self.type_data = [schedule, days]

    def set_weekly_advanced(self, schedule):
        new_schedule = []
        for interval in schedule:
            new_schedule = self._update_schedule(new_schedule, 7*1440, interval[0], interval[1])

        self._modulo = 7*1440
        self._manual = False
        self._start = datetime.datetime.combine(datetime.date.today() -
                                                datetime.timedelta(days=datetime.date.today().weekday()),
                                                datetime.time.min)  # First day of current week
        self._schedule = new_schedule

        self.type = ProgramType.DAYS_SIMPLE
        self.type_data = [schedule]

    @staticmethod
    def _update_schedule(schedule, modulo, start_minute, end_minute):
        start_minute %= modulo
        end_minute %= modulo

        if end_minute < start_minute:
            end_minute += modulo

        if end_minute > modulo:
            new_entries = [
                [0, end_minute % modulo],
                [start_minute, modulo]
            ]
        else:
            new_entries = [[start_minute, end_minute]]

        new_schedule = schedule[:]

        while new_entries:
            entry = new_entries.pop(0)
            for existing in new_schedule:
                if existing[0] <= entry[0] < existing[1]:
                    entry[0] = existing[1]
                if existing[0] < entry[1] <= existing[1]:
                    entry[1] = existing[0]
                if entry[0] < existing[0] <= existing[1] < entry[1]:
                    new_entries.append([existing[1], entry[1]])
                    entry[1] = existing[0]

                if entry[1] - entry[0] <= 0:
                    break

            if entry[1] - entry[0] > 0:
                new_schedule.append(entry)
                new_schedule.sort(key=lambda ent: ent[0])

        return new_schedule

    def is_active(self, date_time):
        time_delta = date_time - self.start
        minute_delta = time_delta.days*24*60 + int(time_delta.seconds/60)

        if self.manual and minute_delta >= self.modulo:
            return False

        current_minute = minute_delta % self.modulo

        result = False
        for entry in self.schedule:
            if entry[0] <= current_minute < entry[1]:
                result = True
                break
            elif entry[0] <= current_minute+self.modulo < entry[1]:
                result = True
                break
            elif entry[0] > current_minute:
                break

        return result

    def active_intervals(self, date_time_start, date_time_end):
        result = []
        start_delta = date_time_start - self.start
        start_minutes = (start_delta.days*24*60 + int(start_delta.seconds/60)) % self.modulo
        current_date_time = date_time_start - datetime.timedelta(minutes=start_minutes,
                                                                 seconds=date_time_start.second,
                                                                 microseconds=date_time_start.microsecond)

        while current_date_time < date_time_end:
            for entry in self.schedule:
                start = current_date_time + datetime.timedelta(minutes=entry[0])
                end = current_date_time + datetime.timedelta(minutes=entry[1])

                if end <= date_time_start:
                    continue

                if start >= date_time_end:
                    break

                result.append({
                    'start': start,
                    'end': end
                })

            if self.manual:
                break

            current_date_time += datetime.timedelta(minutes=self.modulo)

        return result

    def __setattr__(self, key, value):
        if key == 'modulo':
            self._modulo = value
            if not self._loading:
                self.schedule = self._schedule  # Convert to custom sequence
        elif key == 'manual':
            self._manual = value
            if not self._loading and value:
                self.schedule = self._schedule  # Convert to custom sequence
        elif key == 'start':
            if self._loading:  # Update start date to most recent possible
                while value <= datetime.datetime.today():
                    value += datetime.timedelta(minutes=self._modulo)
                self._start = value
            else:
                self._start = value
                self.schedule = self._schedule  # Convert to custom sequence
        else:
            super(_Program, self).__setattr__(key, value)
            if key not in self.SAVE_EXCLUDE:
                if not self._loading:
                    options.save(self, self.index)


class _Programs(object):
    def __init__(self):
        self._programs = []

        i = 0
        while options.available(_Program, i):
            self._programs.append(_Program(self, i))
            i += 1

        options.add_callback('output_count', self._option_cb)

    def _option_cb(self, key, old, new):
        # Remove all stations that do not exist anymore
        for program in self._programs:
            program.stations = [station for station in program.stations if 0 <= station < new]

    def add_program(self):
        program = _Program(self, len(self._programs))
        self._programs.append(program)
        options.save(program, program.index)

    def remove_program(self, index):
        if 0 <= index < len(self._programs):
            del self._programs[index]

        for i in range(index, len(self._programs)):
            options.save(self._programs[i], i)  # Save programs using new indices

        options.erase(_Program, len(self._programs))  # Remove info in last index

    def count(self):
        return len(self._programs)

    def get(self, index=None):
        if index is None:
            result = self._programs[:]
        else:
            result = self._programs[index]
        return result

    __getitem__ = get

programs = _Programs()