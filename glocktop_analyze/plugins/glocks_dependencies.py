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

import glocktop_analyze
from glocktop_analyze.plugins import Plugin, Admonition
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file
from glocktop_analyze.html import generate_footer
from glocktop_analyze.html import generate_css_header

class PidGlocksInSnapshot:
    def __init__(self, list_of_pidglocks, hostname, filesystem_name, date_time):
        self.__list_of_pidglocks = list_of_pidglocks
        self.__hostname = hostname
        self.__filesystem_name = filesystem_name
        self.__date_time  = date_time

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

    def get_pidglocks(self):
        return self.__list_of_pidglocks

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

class GlocksDependencies(Plugin):
    OPTIONS = []

    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_dependencies",
                        "A dependency graph of a glocks for a pid.",
                        snapshots, "Glocks Dependencies", path_to_output_dir,
                        options)
        self.__glocks_dependencies_snapshots = []

    def __encode(self, pid, command):
        # Not sure what guranteees no duplicates, that command will not be empty
        # sometimes and not-empty other, etc.
        return "%s-%s" %(pid, command)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("-")
        return (hashkey_split[0], hashkey_split[1])

    def __get_text(self, colorize=False):
        # Need to add warning:
        summary = ""
        for pidglocks_in_snapshot in self.__glocks_dependencies_snapshots:
            snapshot_summary = ""
            # Review all the glocks for a particular pid.
            for pidglocks in pidglocks_in_snapshot.get_pidglocks():
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
                    pid_header =  "  pid: %s command: %s | " %(pidglocks.get_pid(), pidglocks.get_command())
                    pid_header += "%d glocks associated with pid " %(len(pidglocks.get_glocks()))
                    pid_header += "(%d glock holders)\n" %(glock_holder_flag_found)
                    if (colorize):
                        pid_header = ColorizeConsoleText.orange(pid_header)
                    snapshot_summary += "%s%s\n" %(pid_header, pid_summary)
            if (snapshot_summary):
                snapshot_header = "%s - %s @%s" %(pidglocks_in_snapshot.get_filesystem_name(),
                                                  pidglocks_in_snapshot.get_date_time(),
                                                  pidglocks_in_snapshot.get_hostname())
                if (colorize):
                    snapshot_header =  ColorizeConsoleText.red(snapshot_header)
                summary += "%s\n%s\n\n" %(snapshot_header, snapshot_summary.strip())
        if (summary):
            summary = "%s: %s\n%s" %(self.get_title(), self.get_description(), summary)
        return summary

    def __get_html(self, colorize=False):
        summary = ""
        for pidglocks_in_snapshot in self.__glocks_dependencies_snapshots:
            snapshot_summary = ""
            # Review all the glocks for a particular pid.
            for pidglocks in pidglocks_in_snapshot.get_pidglocks():
                pid_summary = ""
                glock_holder_flag_found = 0
                for glock in pidglocks.get_glocks():
                    pid_summary += "<b>&nbsp;&nbsp;%s</b><BR/>" %(glock)
                    for h in glock.get_holders():
                        pid_summary += "&nbsp;&nbsp;&nbsp;&nbsp;%s<BR/>" %(h)
                    glock_object = glock.get_glock_object()
                    if (not glock_object == None):
                        pid_summary += "&nbsp;&nbsp;&nbsp;&nbsp;%s<BR/>" %(glock_object)
                    if (not glock.get_glock_holder() == None):
                        glock_holder_flag_found += 1

                if (pid_summary):
                    pid_header =  "<span class=\"orange\">&nbsp;&nbsp;pid: %s command: %s | " %(pidglocks.get_pid(), pidglocks.get_command())
                    pid_header += "%d glocks associated with pid " %(len(pidglocks.get_glocks()))
                    pid_header += "(%d glock holders)</span>" %(glock_holder_flag_found)
                    snapshot_summary += "<b>%s</b><BR/>%s<BR/>" %(pid_header, pid_summary)
                if (snapshot_summary):
                    snapshot_header = "%s - %s @%s" %(pidglocks_in_snapshot.get_filesystem_name(),
                                                             pidglocks_in_snapshot.get_date_time(),
                                                             pidglocks_in_snapshot.get_hostname())
                    summary += "<b><span class=\"red\">%s</span></b><BR/>%s" %(snapshot_header, snapshot_summary.strip())
        if (summary):
            header =  "<center><H3>Glocks Dependencies between "
            header += "%s and %s </H3></center>" %(self.get_snapshots_start_time().strftime("%Y-%m-%d %H:%M:%S"),
                                                   self.get_snapshots_end_time().strftime("%Y-%m-%d %H:%M:%S"))
            summary = "<center><b>%s:</b> %s</center><BR/>%s" %(self.get_title(), self.get_description(), summary)
            summary = "%s%s" %(header, summary)
        return summary

    def analyze(self):
        for snapshot in self.get_snapshots():
            map_of_pidglocks = {}
            pids_with_holder_flag = []
            for glock in snapshot.get_glocks():
                for glock_holder in glock.get_holders():
                    hashkey = self.__encode(glock_holder.get_pid(), glock_holder.get_command())
                    if (not map_of_pidglocks.has_key(hashkey)):
                        map_of_pidglocks[hashkey] = PidGlocks(glock_holder.get_pid(),
                                                              glock_holder.get_command())
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
                filesystem_name = snapshot.get_filesystem_name()
                pidglocks_in_snapshot = PidGlocksInSnapshot(list_of_pidglocks, snapshot.get_hostname(),
                                                            filesystem_name, snapshot.get_date_time())
                self.__glocks_dependencies_snapshots.append(pidglocks_in_snapshot)

        if (self.__glocks_dependencies_snapshots):
            warning_msg =  "Possible lock contention found on filesystem."
            self.add_warning(Admonition(snapshot.get_hostname(), self.get_filesystem_name(),
                                        "Glocks", warning_msg, ""))

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
