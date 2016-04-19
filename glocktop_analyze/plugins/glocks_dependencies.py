#!/usr/bin/python
"""@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the dependency of glocks for a pid. The pid has to have a
  glock that has the holder flag set.

Options for the plugin:

"""
import logging
import logging.handlers
import os.path
from operator import itemgetter

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class PidGlocksInSnapshot:
    def __init__(self, list_of_pidglocks):
        self.__list_of_pidglocks = list_of_pidglocks
        self.__hostname = self.__list_of_pidglocks[0].get_hostname()
        self.__filesystem_name = self.__list_of_pidglocks[0].get_filesystem_name()
        self.__date_time  = self.__list_of_pidglocks[0].get_date_time()

    def __str__(self):
        rstring = "%s:%s @%s\n" %(self.get_hostname(),
                                  self.get_filesystem_name(),
                                  self.get_date_time())
        return rstring

    def get_hostname(self):
        return self.__hostname

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_date_time(self):
        return self.__date_time

    def get_pidglocks_all(self):
        return self.__list_of_pidglocks



class PidGlocks:
    # This object represents all glocks that have holder holding a glocks and is
    # for a particular process..
    def __init__(self, pid, command, hostname, filesystem_name, date_time):
        self.__pid = pid
        self.__command = command
        self.__hostname = hostname
        self.__filesystem_name = filesystem_name
        self.__date_time  = date_time
        self.__glocks = []

    def __str__(self):
        rstring = "%s:%s @%s | pid: %s command: %s\n" %(self.get_hostname(),
                                                        self.get_filesystem_name(),
                                                        self.get_date_time(),
                                                        self.get_pid(),
                                                        self.get_command())
        for glock in self.get_glocks():
            rstring += "  %s\n" %(glock)
            for h in glock.get_holders():
                rstring += "    %s\n" %(h)
            glock_object = glock.get_glock_object()
            if (not glock_object == None):
                rstring += "    %s\n" %(glock_object)
        return rstring

    def get_pid(self):
        return self.__pid

    def get_command(self):
        return self.__command

    def get_hostname(self):
        return self.__hostname

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_date_time(self):
        return self.__date_time

    def get_glocks(self):
        return self.__glocks

    def add_glock(self, glock):
        self.__glocks.append(glock)

class GlocksDependencies(Plugin):
    OPTIONS = []

    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_dependencies",
                        "A dependency graph of a glocks for a pid.",
                        snapshots, "Glocks Tree", path_to_output_dir,
                        options)
        self.__glocks_dependencies_snapshot_map = {}

        self.__minimum_glocks_in_snapshots = self.get_option("mininum_glocks_in_snapshots")

    def __encode(self, pid, command):
        # Not sure what guranteees no duplicates, that command will not be empty
        # sometimes and not-empty other, etc.
        return "%s-%s" %(pid, command)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("-")
        return (hashkey_split[0], hashkey_split[1])

    def analyze(self):
        # Inodes is not what i need to key off of. It is pid, as inode glock
        # would be waiting on resource group for different inode. For each
        # snapshot, need to see if a pid is waiting on multiple glocks.

        # key off pids then find relationships with the glocks assocaiated with
        # that pid within that snapshot.

        # Change the code below, key is pid.

        # Need to do per snapshot, so in that snapshot is inode waiting on rgrp
        # or whatever? MOVED pids_to_glocks dict to inside snapshot for now.

        # Need to keep in data structure the filesystem/date and time.
        for snapshot in self.get_snapshots():
            map_of_pidglocks = {}
            pids_with_holder_flag = []
            for glock in snapshot.get_glocks():
                for glock_holder in glock.get_holders():
                    hashkey = self.__encode(glock_holder.get_pid(), glock_holder.get_command())
                    if (not map_of_pidglocks.has_key(hashkey)):
                        map_of_pidglocks[hashkey] = PidGlocks(glock_holder.get_pid(),
                                                              glock_holder.get_command(),
                                                              snapshot.get_hostname(),
                                                              snapshot.get_filesystem_name(),
                                                              snapshot.get_date_time())
                    map_of_pidglocks[hashkey].add_glock(glock)
                    if (not glock.get_glock_holder() == None):
                        if (not hashkey in pids_with_holder_flag):
                            pids_with_holder_flag.append(hashkey)
            # Add all the flagged pids that had a glock with a holder ("h") flag
            # to container for this snapshot.
            list_of_pidglocks = []
            for k in pids_with_holder_flag:
                if (map_of_pidglocks.has_key(k)):
                    # Just get the ones where pid is using 2 or more glocks.
                    if (len(map_of_pidglocks.get(k).get_glocks()) > 1):
                        list_of_pidglocks.append(map_of_pidglocks.get(k))
            # Add to map that sorted into filesystem bin.
            if (list_of_pidglocks):
                pidglocks_in_snapshot = PidGlocksInSnapshot(list_of_pidglocks)
                filesystem_name = pidglocks_in_snapshot.get_filesystem_name()
                if (not self.__glocks_dependencies_snapshot_map.has_key(filesystem_name)):
                    self.__glocks_dependencies_snapshot_map[filesystem_name] = []
                self.__glocks_dependencies_snapshot_map[filesystem_name].append(pidglocks_in_snapshot)

    def console(self):
        # Need to have self.__get_text() so write plain text files like glock_activity.
        for key in self.__glocks_dependencies_snapshot_map.keys():
            print "%s: The glock dependencies for pid with glock's with holder flag. " %(ColorizeConsoleText.red(key))
            pidglocks_in_snapshot_list = self.__glocks_dependencies_snapshot_map.get(key)
            if (pidglocks_in_snapshot_list):
                for pidglocks_in_snapshot in pidglocks_in_snapshot_list:
                    snapshot_summary = ""
                    # Review all the glocks for a particular pid.
                    for pidglocks in pidglocks_in_snapshot.get_pidglocks_all():
                        pid_summary = ""
                        glock_holder_flag_found = 0
                        for glock in pidglocks.get_glocks():
                            pid_summary += "    %s\n" %(glock)
                            for h in glock.get_holders():
                                pid_summary += "      %s\n" %(h)
                            glock_object = glock.get_glock_object()
                            if (not glock_object == None):
                                pid_summary += "      %s\n" %(glock_object)
                            if (not glock.get_glock_holder() == None):
                                glock_holder_flag_found += 1

                        if (pid_summary):
                            pid_header =  "  %s (%s) | " %(pidglocks.get_pid(), pidglocks.get_command())
                            pid_header += "%d glocks associated with pid " %(len(pidglocks.get_glocks()))
                            pid_header += "(%d glock holders)\n" %(glock_holder_flag_found)

                            snapshot_summary += "%s%s" %(ColorizeConsoleText.orange(pid_header), pid_summary)
                    if (snapshot_summary):
                        print ColorizeConsoleText.red("%s@%s %s" %(pidglocks_in_snapshot.get_filesystem_name(),
                                                                   pidglocks_in_snapshot.get_hostname(),
                                                                   pidglocks_in_snapshot.get_date_time()))
                        print snapshot_summary


    def write(self, html_format=False):
        pass
