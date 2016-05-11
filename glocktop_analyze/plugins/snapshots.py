#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the number of snapshots taken for a filesystem, the start
  time, and end time or last snapshot taken.

* This plugin outputs the filesystem name, time when snapshot taken when dlm
  activity is greater than zero.

"""
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class Snapshots(Plugin):
    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "snapshots",
                        "The stats for the snapshots and dlm activity.",
                        snapshots, "Snapshot Stats", path_to_output_dir,
                        options)
        self.__start_time = self.get_snapshots_start_time()
        self.__stop_time = self.get_snapshots_end_time()
        self.__snapshot_count = 0
        self.__dlm_activity = []

    def __get_text(self, colorize=False):
        summary = ""
        if (self.get_snapshots()):
            snapshots_summary = tableize([[self.get_hostname(), self.get_filesystem_name(),
                                           str(self.__snapshot_count), self.__start_time,
                                           self.__stop_time]],
                                         ["Hostname", "Filesystem", "Snapshots",
                                          "Start Time", "Stop Time"], colorize=colorize).strip()
            if (snapshots_summary):
                summary += "\nThen number of snapshots taken, start time, and end time.\n%s\n" %(snapshots_summary)
        if (self.__dlm_activity):
            dlm_activity_summary = tableize(self.__dlm_activity, ["Hostname", "Filesystem",
                                                                  "Snapshot Time",
                                                                  "Number of DLM Waiters"],
                                            colorize=colorize).strip()
            if (dlm_activity_summary):
                summary += "\nThe snapshots that contained at least 1 DLM waiter.\n%s\n" %(dlm_activity_summary)

        if (summary):
            return "%s: %s\n%s\n" %(self.get_title(), self.get_description(), summary)
        return ""

    def analyze(self):
        for snapshot in self.get_snapshots():
            self.__snapshot_count += 1
            dlm_activity = snapshot.get_dlm_activity()
            if (not dlm_activity == None):
                self.__dlm_activity.append([self.get_hostname(), self.get_filesystem_name(), snapshot.get_date_time(), dlm_activity.get_waiter_count()])

    def console(self):
        summary = self.__get_text(colorize=True)
        if (summary):
            print "%s\n" %(summary.rstrip())

    def write(self, html_format=False):
        wdata =""
        path_to_output_file = ""
        if (not html_format):
            filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
            wdata = self.__get_text(colorize=False)
        else:
            bdata = ""
            if (self.__snapshot_count > 0):
                bdata += generate_table([[self.get_hostname(), self.get_filesystem_name(), str(self.__snapshot_count),
                                          self.__start_time, self.__stop_time]],
                                        ["Hostname", "Filesystem", "Snapshots", "Start Time", "Stop Time"],
                                        title="Snapshots Taken",
                                        description="The number of snapshots taken and the time that first and the last snapshot taken.")

            if (self.__dlm_activity):
                bdata += generate_table(self.__dlm_activity,
                                        ["Hostname", "Filesystem", "Snapshot Time", "Number of DLM Waiters"],
                                        title="DLM Waiter Count",
                                        description="The number of DLM waiters for a snapshot. Only snapshots with DLM waiter count higher than 0 displayed.")
            if (bdata):
                wdata = "%s\n%s\n%s" %(generate_table_header(), bdata, generate_footer())
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
