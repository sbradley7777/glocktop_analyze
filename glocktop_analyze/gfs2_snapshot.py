#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
from glocktop_analyze.glock import Glock

class GFS2Snapshot():
    # A collection of glocks for a filesystem at a specific time.
    def __init__(self, filesystem_name, hostname, date_time, dlm_activity = None, ignore_ended_process_and_tlocks=False):
        self.__filesystem_name = filesystem_name
        self.__hostname = hostname
        self.__date_time = date_time
        self.__dlm_activity = dlm_activity
        self.__ignore_ended_process_and_tlocks = ignore_ended_process_and_tlocks

        self.__glocks = []
        self.__glocks_stats = None


    def __str__(self):
        dlm_activity = ""
        if (not self.get_dlm_activity() == None):
            dlm_activity = "(%s)" %(str(self.get_dlm_activity()))
        return "%s - %s %s %s" %(self.get_filesystem_name(), str(self.get_date_time()), self.get_hostname(), dlm_activity)

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_hostname(self):
        return self.__hostname

    def get_date_time(self):
        return self.__date_time

    def add_glock(self, glock):
        self.__glocks.append(glock)

    def get_glocks(self):
        if (self.__ignore_ended_process_and_tlocks):
            glocks_not_ended_process = []
            for g in self.__glocks:
                if (not ((g.has_ended_process()) or (g.get_type() == 1))):
                    glocks_not_ended_process.append(g)
            return glocks_not_ended_process
        return self.__glocks

    def find_glock(self, glock_type, glock_inode):
        glocks = []
        for glock in self.get_glocks():
            if (glock_inode == glock.get_inode()):
                if (0 < cmdline_opts.glock_type < 10):
                    if (glock_type == glock.get_type()):
                        glocks.append(glock)
                else:
                    glocks.append(glock)
        return glocks

    def get_glocks_stats(self):
        return self.__glocks_stats

    def add_glocks_stats(self, glocks_stats):
        self.__glocks_stats = glocks_stats

    def get_dlm_activity(self):
        return self.__dlm_activity

class DLMActivity():
    def __init__(self, dlm_dirtbl_size, dlm_rsbtbl_size, dlm_lkbtbl_size, waiter_count):
        self.__dlm_dirtbl_size = dlm_dirtbl_size
        self.__dlm_rsbtbl_size = dlm_rsbtbl_size
        self.__dlm_lkbtbl_size = dlm_lkbtbl_size
        self.__waiter_count = waiter_count

    def __str__(self):
        return "DLM: %d waiters with hash table sizes: %d/%d/%d" %(self.get_waiter_count(),
                                                                   self.get_dlm_dirtbl_size(),
                                                                   self.get_dlm_rsbtbl_size(),
                                                                   self.get_dlm_lkbtbl_size())

    def get_dlm_dirtbl_size(self):
        return self.__dlm_dirtbl_size

    def get_dlm_rsbtbl_size(self):
        return self.__dlm_rsbtbl_size

    def get_dlm_lkbtbl_size(self):
        return self.__dlm_lkbtbl_size

    def get_waiter_count(self):
        return self.__waiter_count
