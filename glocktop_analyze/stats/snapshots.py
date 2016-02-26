#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class Snapshots(Stats):
    def __init__(self, snapshots):
        Stats.__init__(self, snapshots, "Filesystem Stats")
        self.__count = 0
        self.__start_time = None
        self.__stop_time = None

    def analyze(self):
        for snapshot in self.get_snapshots():
            if (self.__start_time == None):
                self.__start_time = str(snapshot.get_date_time())
            self.__count += 1
            self.__stop_time = str(snapshot.get_date_time())

    def console(self):
        print tableize([[self.get_filesystem_name(), str(self.__count), self.__start_time, self.__stop_time]],
                       ["Filesystem", "Snapshots", "Start Time", "Stop Time"])


    def write(self, path_to_output_dir):
        ftable = tableize([[self.get_filesystem_name(), str(self.__count), self.__start_time, self.__stop_time]],
                          ["Filesystem", "Snapshots", "Start Time", "Stop Time"])
        filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
        path_to_output_file = os.path.join(os.path.join(path_to_output_dir, self.get_filesystem_name()), filename)
        if (not write_to_file(path_to_output_file, ftable, append_to_file=False, create_file=True)):
            message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
