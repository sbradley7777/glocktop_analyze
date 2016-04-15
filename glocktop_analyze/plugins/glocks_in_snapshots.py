#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the number of times that a glock appears in all
  snapshots. Requires that at least 1 holder, waiter, or object is attached to
  glock

Options for the plugin:
* mininum_glocks_in_snapshots: The mininum number of times a glock is found in
  all the snapshots.

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
    OPTIONS = [("mininum_glocks_in_snapshots",
                "The mininum number of times a glock is found in all the snapshots.",
                2)]

    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_in_snapshots",
                        "The glocks that appear in multiple snapshots.",
                        snapshots, "Glocks in Snapshots", path_to_output_dir,
                        options)
        self.__table = []

        self.__minimum_glocks_in_snapshots = self.get_option("mininum_glocks_in_snapshots")

    def __encode(self, glock_type, glock_inode):
        return "%s/%s" %(glock_type, glock_inode)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("/")
        return (hashkey_split[0], hashkey_split[1])

    def analyze(self):
        glocks_in_snapshots = {}
        for snapshot in self.get_snapshots():
            message = "There was %d glocks found on the filesystem: %s." %(len(snapshot.get_glocks()), self.get_filesystem_name())
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
            for glock in snapshot.get_glocks():
                # Require that glock is has at least an object of holder or
                # waiter assoicated with it.
                if (len(glock.get_holders()) or (not glock.get_glock_object() == None)):
                    hashkey = self.__encode(glock.get_type(), glock.get_inode())
                    if (not glocks_in_snapshots.has_key(hashkey)):
                        glocks_in_snapshots[hashkey] = 0
                    glocks_in_snapshots[hashkey] += 1
        self.__table = []
        for pair in sorted(glocks_in_snapshots.items(), key=itemgetter(1), reverse=True):
            if (pair[1] >= self.__minimum_glocks_in_snapshots):
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
