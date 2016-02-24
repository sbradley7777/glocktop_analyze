#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""

from glocktop_analyze.utilities import ColorizeConsoleText, tableize

import itertools
from datetime import datetime

GLOCK_TYPES = ["nondisk", "inode", "rgrp", "iopen", "flock", "quota", "journal"]
GLOCK_STATES = ["Unlocked", "Locked", "Held EX", "Held SH", "Held DF", "G Waiting", "P Waiting", "DLM wait"]

class GlocksStats():
    def __init__(self, filesystem_name, date_time):
        self.__filesystem_name = filesystem_name
        self.__date_time = date_time
        self.__glocks_stats_map = {}


    def __str__(self):
        return tableize(self.get_table(), ["Glock States"] + GLOCK_STATES, colorize=False).rstrip()

    def __generate_hash(self, gtype, state):
        return "%s-%s" %(gtype, state)

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_date_time(self):
        return self.__date_time

    def has_stats(self):
        return (len(self.__glocks_stats_map.keys()) > 0)

    def add_stat(self, gtype, state, count):
        key = self.__generate_hash(gtype, state)
        if (not len(self.__glocks_stats_map.keys()) > 0):
            # Populate the map with all the keys and create GlockStat objects for
            # them that are initialized.
            for gtype,state in itertools.product(GLOCK_TYPES, GLOCK_STATES):
                self.__glocks_stats_map[self.__generate_hash(gtype, state)] = GlockStat(self.__filesystem_name, gtype, state)
        if (self.__glocks_stats_map.has_key(key)):
            self.__glocks_stats_map.get(key).set_stat(count)

    def get_stat(self, gtype, state):
        key = self.__generate_hash(gtype, state)
        if (self.__glocks_stats_map.has_key(key)):
            return self.__glocks_stats_map.get(key).get_stat()
        # If no stat found then return -1 which means invalid since all stat
        # should be >= 0.
        return -1

    def get_stats_by_type(self, gtype):
        stats = {}
        for state in GLOCK_STATES:
            stats[state] = self.get_stat(gtype, state)
        return stats

    def get_stats_by_state(self, state):
        stats = {}
        for gtype in GLOCK_TYPES:
            stats[gtype] = self.get_stat(gtype, state)
        return stats

    def get_table(self):
        table = []
        for state in GLOCK_STATES:
            cstats = []
            for gtype in GLOCK_TYPES:
                cstats.append(self.__glocks_stats_map.get(self.__generate_hash(gtype, state)).get_stat())
            cstats.insert(0, state)
            table.append(cstats)
        return table

class GlockStat():
    def __init__(self, filesystem_name, gtype, state):
        self.__filesystem_name = filesystem_name
        self.__gtype = gtype
        self.__state = state
        self.__stat = -1

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_type(self):
        return self.__gtype

    def get_state(self):
        return self.__state

    def get_stat(self):
        return self.__stat

    def set_stat(self, stat):
        self.__stat = stat

