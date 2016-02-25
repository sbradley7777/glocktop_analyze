#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class GlocksHighDemoteSeconds(Stats):
    def __init__(self, snapshots):
        Stats.__init__(self, snapshots, "Glocks with High Demote Seconds")
        self.__glocks_high_demote_seconds = {}


    def __encode(self, glock_type, glock_inode):
        return "%s/%s" %(glock_type, glock_inode)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("/")
        return (hashkey_split[0], hashkey_split[1])

    def __tableify(self, glock_type_name, demote_seconds):
        table = []
        current_filesystem_name = self.get_filesystem_name()
        current_glock = glock_type_name
        current_demo_seconds = ""
        index = 0
        for dss in demote_seconds.split():
            if (((index % 5) == 0) and (not index == 0)):
                table.append([current_filesystem_name, current_glock, current_demo_seconds.strip()])
                current_filesystem_name = "-"
                current_glock = "-"
                current_demo_seconds = dss
                index = 0
            else:
                current_demo_seconds += " %s" %(dss)
                index += 1
        return table

    def analyze(self):
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glocks():
                demote_time = int(glock.get_demote_time())
                if (demote_time > 0):
                    hashkey = self.__encode(glock.get_type(), glock.get_inode())
                    if (not self.__glocks_high_demote_seconds.has_key(hashkey)):
                        self.__glocks_high_demote_seconds[hashkey] = ""
                    demote_time_str = "%s %d" %(self.__glocks_high_demote_seconds.get(hashkey),
                                                demote_time)
                    self.__glocks_high_demote_seconds[hashkey] = demote_time_str


    def console(self):
        table = []
        for hashkey in self.__glocks_high_demote_seconds.keys():
            table += self.__tableify(hashkey, self.__glocks_high_demote_seconds.get(hashkey))
        print tableize(table,["Filesystem", "Snapshots", "Demote Seconds"])

    def write(self, path_to_output_dir):
        table = []
        for hashkey in self.__glocks_high_demote_seconds.keys():
            table += self.__tableify(hashkey, self.__glocks_high_demote_seconds.get(hashkey))
        ftable = tableize(table,["Filesystem", "Snapshots", "Demote Seconds"], colorize=False)
        filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
        path_to_output_file = os.path.join(os.path.join(path_to_output_dir, self.get_filesystem_name()), filename)
        if (not write_to_file(path_to_output_file, ftable, append_to_file=False, create_file=True)):
            message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
