#!/usr/bin/python
"""@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin finds any glock tha appears to be transitioning slowly to next
  state or appears to hung for long peroids of time.

Options for the plugin:

"""
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import Plugin, Admonition
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file
from glocktop_analyze.html import generate_footer
from glocktop_analyze.html import generate_css_header

class PidGlocksInSnapshot:
    def __init__(self, list_of_pidglocks, hostname, filesystem_name,
                 date_time, snapshot_index):
        self.__list_of_pidglocks = list_of_pidglocks
        self.__hostname = hostname
        self.__filesystem_name = filesystem_name
        self.__date_time  = date_time
        self.__snapshot_index = snapshot_index

    def __str__(self):
        rstring = "%s:%s @%s - %d" %(self.get_hostname(),
                                     self.get_filesystem_name(),
                                     self.get_date_time(),
                                     self.get_snapshot_index())
        return rstring

    def get_hostname(self):
        return self.__hostname

    def get_filesystem_name(self):
        return self.__filesystem_name

    def get_date_time(self):
        return self.__date_time

    def get_pidglocks(self):
        return self.__list_of_pidglocks

    def get_snapshot_index(self):
        return self.__snapshot_index

class PidGlocks:
    # This object represents all glocks that have holder holding a glocks and is
    # for a particular process for a snapshot.
    def __init__(self, pid, command):
        self.__pid = pid
        self.__command = command
        self.__glocks = []

    def __str__(self):
        rstring = "pid: %s command: %s\n" %(self.get_pid(), self.get_command())
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

    def get_glocks(self):
        return self.__glocks

    def add_glock(self, glock):
        self.__glocks.append(glock)

class GlocksHung(Plugin):
    OPTIONS = [("minimum_glock_seq", "The minimum number of sequential snapshots to flag glock as a pattern.", 2)]

    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_hung",
                        "Finds any glocks that appear to be hung or transitioning slowly.",
                        snapshots, "Glocks hung or transitioning slowly", path_to_output_dir,
                        options)

    def __encode(self, gtype, ginode, pid):
        return "%s/%s-%s" %(gtype, ginode, pid)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("-")
        glock_split = hashkey_split[0].split("/")
        return (glock_split[0], glock_split[1], hashkey_split[1])

    def __get_text(self, colorize=False):
        # Need to add warning:
        summary = ""
        return summary

    def __get_html(self, colorize=False):
        summary = ""
        return summary


    def __get_pidglocks_map(self,snapshot):
        def encode(pid, command):
            return "%s-%s" %(pid, command)

        map_of_pidglocks = {}
        pids_with_holder_flag = []
        for glock in snapshot.get_glocks():
            for glock_holder in glock.get_holders():
                hashkey = encode(glock_holder.get_pid(), glock_holder.get_command())
                if (not map_of_pidglocks.has_key(hashkey)):
                    map_of_pidglocks[hashkey] = PidGlocks(glock_holder.get_pid(),
                                                          glock_holder.get_command())
                map_of_pidglocks[hashkey].add_glock(glock)
        return map_of_pidglocks

    def analyze(self):
        # Create a mapping of snapshot date_time and sequence it came in.
        snapshots_date_time = {}
        index = 0
        for snapshot in self.get_snapshots():
            snapshots_date_time[snapshot.get_date_time()] = index
            index += 1

        glocks_dependencies_snapshots = []
        for snapshot in self.get_snapshots():
            pidglocks_map = self.__get_pidglocks_map(snapshot)
            # Add all the flagged pids that had a glock with a holder ("h") flag
            # to container for this snapshot.
            list_of_pidglocks = []
            for key in pidglocks_map.keys():
                pidglocks = pidglocks_map.get(key)
                found_gh = False
                for glock in pidglocks.get_glocks():
                    if (not glock.get_glock_holder() == None):
                        # Add if pid has any holders because there might be a
                        # time when that it is in transition where glock A is
                        # waiting on glock B, but only glock A is captured.
                        found_gh = True
                if (found_gh):
                    list_of_pidglocks.append(pidglocks)
            # Add to container only those that that contained at least 1 glock
            # holder and skip the others.
            if (list_of_pidglocks):
                filesystem_name = snapshot.get_filesystem_name()
                pidglocks_in_snapshot = PidGlocksInSnapshot(list_of_pidglocks, snapshot.get_hostname(),
                                                            filesystem_name, snapshot.get_date_time(),
                                                            snapshots_date_time.get(snapshot.get_date_time()))
                glocks_dependencies_snapshots.append(pidglocks_in_snapshot)

        # Search for pidglocks that appear in sequence.

        # Added option: minimum_glock_seq
        for gds in glocks_dependencies_snapshots:
            print gds

        """
        # Find all glock with same glock type, glock inode, and pid for the
        # glock holder.
        snapshot_glock_holders = {}
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glock_holders():
                gh = glock.get_glock_holder()
                hashkey = self.__encode(glock.get_type(), glock.get_inode(), gh.get_pid())
                if (not snapshot_glock_holders.has_key(hashkey)):
                    snapshot_glock_holders[hashkey] = []
                snapshot_glock_holders[hashkey].append(glock)

        glocks_possible_hung = []
        for key in snapshot_glock_holders.keys():
            if (len(snapshot_glock_holders.get(key)) >= 3):
                glocks_possible_hung.append(self.__decode(key))

        for snapshot in self.get_snapshots():
            for gh_possible_hung in glocks_possible_hung:
                glock = snapshot.find_glock(gh_possible_hung[0], gh_possible_hung[1])
                if (not glock == None):
                    print glock
        """
    def console(self):
        summary = self.__get_text(colorize=True)
        if (summary):
            print "%s\n" %(summary.rstrip())

    def write(self, html_format=False):
        wdata = ""
        path_to_output_file = ""
        if (not html_format):
            wdata = self.__get_text(colorize=False)
            filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)

        else:
            bdata = self.__get_html(colorize=True)
            wdata = "%s\n%s\n<BR/><HR/><BR/>%s" %(generate_css_header(), bdata, generate_footer())

            filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
