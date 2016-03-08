#!/usr/bin/python
"""
This class only counts the number of times that a glock is in a snapshot.
"""
import logging
import logging.handlers
import os.path
from operator import itemgetter

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class GlocksInSnapshots(Plugin):
    def __init__(self, snapshots, path_to_output_dir):
        Plugin.__init__(self, snapshots, "Glocks in Snapshots", path_to_output_dir)
        self.__table = []
        self.__minimum_count = 3

    def __encode(self, glock_type, glock_inode):
        return "%s/%s" %(glock_type, glock_inode)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("/")
        return (hashkey_split[0], hashkey_split[1])

    def analyze(self):
        glocks_in_snapshots = {}
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glocks():
                hashkey = self.__encode(glock.get_type(), glock.get_inode())
                if (not glocks_in_snapshots.has_key(hashkey)):
                    glocks_in_snapshots[hashkey] = 0
                glocks_in_snapshots[hashkey] += 1
        self.__table = []
        for pair in sorted(glocks_in_snapshots.items(), key=itemgetter(1), reverse=True):
            if (pair[1] >= self.__minimum_count):
                self.__table.append([self.get_filesystem_name(), pair[0], pair[1]])

    def console(self):
        if (self.__table):
            print tableize(self.__table, ["Filesystem Name", "Glock Type/Glocks Inode", "Number of Snapshots Appeared in"])

    def write(self, html_format=False):
        if (self.__table):
            wdata = ""
            path_to_output_file = ""
            if (not html_format):
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                wdata = tableize(self.__table, ["Filesystem Name", "Glock Type/Glocks Inode", "Number of Snapshots Appeared in"], colorize=False)
            else:
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                bdata = generate_table(self.__table,
                                       ["Filesystem Name", "Glock Type/Glocks Inode", "Number of Snapshots Appeared in"],
                                       title=self.get_title(),
                                       description="The number of times that a glock appeared in a snapshot.")
                wdata = "%s\n%s\n%s" %(generate_table_header(), bdata, generate_footer())
            if (wdata):
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)