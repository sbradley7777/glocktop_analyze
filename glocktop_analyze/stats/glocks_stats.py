#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class GSStats(Stats):

    def __init__(self, snapshots):
        Stats.__init__(self, snapshots, "Glocks Stats")
        self.__console_summary = ""
        self.__file_summary = ""

    def analyze(self):
        filesystem_name = self.get_filesystem_name()
        for snapshot in self.get_snapshots():
            glocks_stats = snapshot.get_glocks_stats()
            if (not glocks_stats == None):
                self.__file_summary +=  "Glock stats at %s for filesystem: " %(glocks_stats.get_date_time().strftime("%Y-%m-%d %H:%M:%S"))
                self.__file_summary += "%s\n%s\n\n" %(filesystem_name, str(glocks_stats))
                formatted_table = tableize(glocks_stats.get_table(), ["Glock States"] +
                                           glocktop_analyze.glocks_stats.GLOCK_STATES, colorize=True).rstrip()
                self.__console_summary += "Glock stats at %s for filesystem: " %(ColorizeConsoleText.orange(
                    glocks_stats.get_date_time().strftime("%Y-%m-%d %H:%M:%S")))
                self.__console_summary += "%s\n%s\n\n" %(ColorizeConsoleText.orange(
                    filesystem_name), formatted_table)

    def console(self):
        print "%s\n" %(self.__console_summary.rstrip())

    def write(self, path_to_output_dir):
        filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
        path_to_output_file = os.path.join(os.path.join(path_to_output_dir, self.get_filesystem_name()), filename)
        if (not write_to_file(path_to_output_file, self.__file_summary, append_to_file=False, create_file=True)):
            message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
