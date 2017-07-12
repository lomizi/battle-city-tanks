# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring

import uuid


class Timer(object):
    def __init__(self):
        self.timers = []

    def add(self, interval, func, repeat=-1):
        options = {
            "interval": interval,
            "callback": func,
            "repeat": repeat,
            "times": 0,
            "time": 0,
            "uuid": uuid.uuid4()
        }
        self.timers.append(options)

        return options["uuid"]

    def destroy(self, uuid_nr):
        for timer in self.timers:
            if timer["uuid"] == uuid_nr:
                self.timers.remove(timer)
                return

    def update(self, time_passed):
        for timer in self.timers:
            timer["time"] += time_passed
            if timer["time"] > timer["interval"]:
                timer["time"] -= timer["interval"]
                timer["times"] += 1
                if timer["times"] == timer["repeat"] > -1:
                    self.timers.remove(timer)
                try:
                    timer["callback"]()
                except:  # pylint: disable=bare-except
                    try:
                        self.timers.remove(timer)
                    except:  # pylint: disable=bare-except
                        pass
