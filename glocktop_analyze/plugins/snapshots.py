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
        self.__count = 0
        self.__start_time = None
        self.__stop_time = None

        self.__dlm_activity = []

    def analyze(self):
        for snapshot in self.get_snapshots():
            if (self.__start_time == None):
                self.__start_time = str(snapshot.get_date_time())
            self.__count += 1
            self.__stop_time = str(snapshot.get_date_time())
            dlm_activity = snapshot.get_dlm_activity()
            if (not dlm_activity == None):
                self.__dlm_activity.append([self.get_filesystem_name(), snapshot.get_date_time(), dlm_activity.get_waiter_count()])

    def console(self):
        if (self.get_snapshots()):
            print tableize([[self.get_filesystem_name(), str(self.__count), self.__start_time, self.__stop_time]],
                           ["Filesystem", "Snapshots", "Start Time", "Stop Time"])
        if (self.__dlm_activity):
            print tableize(self.__dlm_activity, ["Filesystem", "Snapshot Time", "Number of DLM Waiters"])

    def write(self, html_format=False):
        if (not html_format):
            wdata = ""
            if (self.__count > 0):
                wdata += tableize([[self.get_filesystem_name(), str(self.__count), self.__start_time,
                                    self.__stop_time]],
                                  ["Filesystem", "Snapshots", "Start Time", "Stop Time"], colorize=False) + "\n"
            if (self.__dlm_activity):
                wdata += tableize(self.__dlm_activity,
                                  ["Filesystem", "Snapshot Time", "Number of DLM Waiters"],
                                  colorize=False) + "\n"
            if (wdata):
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
        else:
            bdata = ""
            if (self.__count > 0):
                bdata += generate_table([[self.get_filesystem_name(), str(self.__count),
                                          self.__start_time, self.__stop_time]],
                                        ["Filesystem", "Snapshots", "Start Time", "Stop Time"],
                                        title="Snapshots Taken",
                                        description="The number of snapshots taken and the time that first and the last snapshot taken.")

            if (self.__dlm_activity):
                bdata += generate_table(self.__dlm_activity,
                                        ["Filesystem", "Snapshot Time", "Number of DLM Waiters"],
                                        title="DLM Waiter Count",
                                        description="The number of DLM waiters for a snapshot. Only snapshots with DLM waiter count higher than 0 displayed.")
            if (bdata):
                wdata = "%s\n%s\n%s" %(generate_table_header(), bdata, generate_footer())
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
