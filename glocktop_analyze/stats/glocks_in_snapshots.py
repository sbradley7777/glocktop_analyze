#!/usr/bin/python
"""
This class only counts the number of times that a glock is in a snapshot.
"""
import logging
import logging.handlers
import os.path
from operator import itemgetter

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class GlocksInSnapshots(Stats):
    def __init__(self, snapshots, path_to_output_dir):
        Stats.__init__(self, snapshots, "Glocks in Snapshots", path_to_output_dir)
        self.__glocks_in_snapshots = {}
        self.__minimum_count = 3

    def __encode(self, glock_type, glock_inode):
        return "%s/%s" %(glock_type, glock_inode)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("/")
        return (hashkey_split[0], hashkey_split[1])

    def analyze(self):
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glocks():
                hashkey = self.__encode(glock.get_type(), glock.get_inode())
                if (not self.__glocks_in_snapshots.has_key(hashkey)):
                    self.__glocks_in_snapshots[hashkey] = 0
                self.__glocks_in_snapshots[hashkey] += 1

    def console(self):
        table = []
        for pair in sorted(self.__glocks_in_snapshots.items(), key=itemgetter(1), reverse=True):
            if (pair[1] >= self.__minimum_count):
                table.append([self.get_filesystem_name(), pair[0], pair[1]])
        print tableize(table, ["Filesystem Name", "Glock Type/Glocks Inode", "Appeared in Snapshots Count"])

    def write(self):
        table = []
        for pair in sorted(self.__glocks_in_snapshots.items(), key=itemgetter(1), reverse=True):
            if (pair[1] >= self.__minimum_count):
                table.append([self.get_filesystem_name(), pair[0], pair[1]])
        ftable = tableize(table, ["Filesystem Name", "Glock Type/Glocks Inode", "Appeared in Snapshots Count"], colorize=False)
        filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
        path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                        self.get_filesystem_name()), filename)
        if (not write_to_file(path_to_output_file, ftable, append_to_file=False, create_file=True)):
            message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
