#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class Snapshots(Stats):
    def __init__(self, snapshots, path_to_output_dir):
        Stats.__init__(self, snapshots, "Snapshot Stats", path_to_output_dir)
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

    def write(self):
        filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
        path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                        self.get_filesystem_name()), filename)
        wdata = ""
        if (self.get_snapshots()):
            wdata += tableize([[self.get_filesystem_name(), str(self.__count), self.__start_time,
                                self.__stop_time]],
                              ["Filesystem", "Snapshots", "Start Time", "Stop Time"], colorize=False) + "\n"
        if (self.__dlm_activity):
            wdata += tableize(self.__dlm_activity,
                               ["Filesystem", "Snapshot Time", "Number of DLM Waiters"],
                               colorize=False) + "\n"
        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
