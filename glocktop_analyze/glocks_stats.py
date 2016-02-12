#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""

class GlocksStats():
    def __init__(self):
        # glocks    nondisk  inode    rgrp   iopen    flock  quota jrnl
        # S  Unlocked:       1        6       4       0       0     0    0       11
        # S    Locked:       2      370       6     124       0     0    1      504
        # S   Held EX:       0        2       0       0       0     0    1        3
        # S   Held SH:       1        1       0     123       0     0    0      125
        # S   Held DF:       0        0       0       0       0     0    0        0
        # S G Waiting:       0        1       0       0       0     0    0        1
        # S P Waiting:       0        1       0       0       0     0    0        1
        # S  DLM wait:       0
        self.__glock_types = ["nondisk", "inode", "rgrp", "iopen", "flock", "quota", "jrnl"]
        self.__glock_states = ["Unlocked", "Locked", "Held EX", "Held SH", "Held DF", "G Waiting", "P Waiting", "DLM wait"]
        self.__glocks_stats_map = dict.fromkeys(self.__glock_states, None)


    def __str__(self):
        rstring = ""
        for glock_state in self.__glocks_stats_map.keys():
            glock_stats = self.get_stats(glock_state)
            if (not glock_stats == None):
                rstring += "%s\n" %(str(glock_stats))
        return rstring.rstrip()

    def add_stats(self, glock_stats):
        self.__glocks_stats_map[glock_stats.get_state()] = glock_stats

    def get_stats(self, state):
        if (not self.__glocks_stats_map.has_key(state)):
            return None
        return self.__glocks_stats_map.get(state)

    def get_stats_by_type(self, gtype):
        stats = {}
        for glock_state in self.__glocks_stats_map.keys():
            glock_stats = self.__glocks_stats_map.get(glock_state)
            for glock_stat in glock_stats.get_all():
                if (glock_stat.get_type() == gtype):
                    stats[glock_state] = glock_stat
        return stats

    def get_states(self):
        return self.__glock_states

    def get_types(self):
        return self.__glock_types

    def has_stats(self):
        for glock_state in self.get_states():
            glock_stats = self.get_stats(glock_state)
            if (not glock_stats == None):
                return True
        return False



class GlockStats():
    def __init__(self, state, nondisk, inode, rgrp, iopen,
                 flock, quota, journal):
        self.__state = state
        self.__nondisk = nondisk
        self.__inode = inode
        self.__rgrp = rgrp
        self.__iopen = iopen
        self.__flock = flock
        self.__quota = quota
        self.__journal = journal

    def __str__(self):
        return "%s %d %d %d %d %d %d %d" %(self.get_state(),
                                           self.get_nondisk().get_count(),
                                           self.get_inode().get_count(),
                                           self.get_rgrp().get_count(),
                                           self.get_iopen().get_count(),
                                           self.get_flock().get_count(),
                                           self.get_quota().get_count(),
                                           self.get_journal().get_count())
    def get_state(self):
        return self.__state

    def get_nondisk(self):
        return self.__nondisk

    def get_inode(self):
        return self.__inode

    def get_rgrp(self):
        return self.__rgrp

    def get_iopen(self):
        return self.__iopen

    def get_flock(self):
        return self.__flock

    def get_quota(self):
        return self.__quota

    def get_journal(self):
        return self.__journal

    def get_all(self):
        return [self.get_nondisk(), self.get_inode(), self.get_rgrp(),
                self.get_iopen(), self.get_flock(), self.get_quota(),
                self.get_journal()]

class GlockStat():
    def __init__(self, filesystem_name, date_time, state, gtype, count):
        self.__filesystem_name = filesystem_name
        self.__date_time = date_time
        self.__state = state
        self.__gtype = gtype
        self.__count = count

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_date_time(self):
        return self.__date_time

    def get_state(self):
        return self.__state

    def get_type(self):
        return self.__gtype

    def get_count(self):
        return self.__count
