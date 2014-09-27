#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'


class _DummyInputs(object):
    def __init__(self):
        self.rain_input = False


class _IOInputs(object):
    def __init__(self):
        self._mapping = {}

    def __getattr__(self, item):
        if item.startswith('_'):
            return super(_IOInputs, self).__getattribute__(item)
        else:
            return self._io.input(self._mapping[item])


class _RPiInputs(_IOInputs):
    def __init__(self):
        import RPi.GPIO as GPIO  # RPi hardware

        super(_RPiInputs, self).__init__()
        self._io = GPIO
        self._io.setwarnings(False)
        self._io.cleanup()
        self._io.setmode(self._io.BOARD)

        self._mapping = {
            'rain_input': 8
        }


class _BBBInputs(_IOInputs):
    def __init__(self):
        import Adafruit_BBIO.GPIO as GPIO  # Beagle Bone Black hardware

        super(_BBBInputs, self).__init__()
        self._io = GPIO
        self._io.setwarnings(False)
        self._io.cleanup()

        self._mapping = {
            'rain_input': "P9_15"
        }


try:
    inputs = _RPiInputs()
except Exception:
    try:
        inputs = _BBBInputs()
    except Exception:
        inputs = _DummyInputs()