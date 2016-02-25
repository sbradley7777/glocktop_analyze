#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class Filesystems(Stats):

    def __init__(self, snapshots, title):
        Stats.__init__(self, snapshots, title)
        self.__console_summary_str = ""
        self.__file_summary_str = ""

    def analyze(self):
        filesystem_count = {}
        for snapshot in self.get_snapshots():
            filesystem_name = snapshot.get_filesystem_name()
            # Get filesystem stats
            if (filesystem_count.has_key(filesystem_name)):
                filesystem_count[filesystem_name]["end_time"] = str(snapshot.get_date_time())
                filesystem_count[filesystem_name]["count"] = filesystem_count[filesystem_name].get("count") + 1
            else:
                filesystem_count[filesystem_name] = {"name": filesystem_name, "count":1,
                                                     "start_time":str(snapshot.get_date_time()),
                                                     "end_time":str(snapshot.get_date_time())}


            table = []
            for key in filesystem_count.keys():
                table.append([filesystem_count.get(key).get("name"), filesystem_count.get(key).get("count"),
                              filesystem_count.get(key).get("start_time"), filesystem_count.get(key).get("end_time")])
            self.__console_summary_str = tableize(table, ["Filesystem", "Snapshots", "Start Time", "End Time"])
            self.__file_summary_str = tableize(table, ["Filesystem", "Snapshots", "Start Time", "End Time"], colorize=False)

    def console(self):
        print self.__console_summary_str


    def write(self, path_to_output_dir):
        filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
        path_to_output_file = os.path.join(path_to_output_dir, filename)
        if (not write_to_file(path_to_output_file, self.__file_summary_str, append_to_file=False, create_file=True)):
            message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

