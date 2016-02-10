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
        # S  DLM wait:       0        self.__glock_stats_category_order = ""
        self.__glocks_stats = []
        self.__glocks_stats_category_order = ["Unlocked","Locked", "Held EX", "Held SH", "Held DF", "G Waiting", "P Waiting", "DLM wait"]
    def __str__(self):
        rstring = ""
        for glock_stats in self.get_glocks_stats():
            rstring += "%s\n" %(str(glock_stats))
        return rstring.rstrip()

    def add_glock_stats(self, glock_stats):
        self.__glocks_stats.append(glock_stats)

    def get_glocks_stats(self):
        return self.__glocks_stats

class GlockStats():
    def __init__(self, glock_category, nondisk, inode, rgrp, iopen,
                 flock, quota, journal, total):
        self.__glock_category = glock_category
        self.__nondisk = nondisk
        self.__inode = inode
        self.__rgrp = rgrp
        self.__iopen = iopen
        self.__flock = flock
        self.__quota = quota
        self.__journal = journal
        self.__total = total

    def __str__(self):
        rstring =  "%s %s %s " %(self.get_glock_category(), self.get_nondisk(), self.get_inode())
        rstring += "%s %s %s " %(self.get_rgrp(), self.get_iopen(), self.get_flock())
        rstring += "%s %s %s " %(self.get_quota(), self.get_journal(), self.get_total())
        return rstring

    def get_glock_category(self):
        return self.__glock_category

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

    def get_total(self):
        return self.__total


