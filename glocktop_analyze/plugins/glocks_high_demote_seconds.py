#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs any demote_second value greater than zero for a glock.

"""
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import Plugin, Admonition
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_css_header, generate_table
from glocktop_analyze.html import generate_footer

class GlocksHighDemoteSeconds(Plugin):
    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_high_demote_seconds",
                        "The glocks with demote time greater than zero seconds.",
                        snapshots, "Glocks with High Demote Seconds",
                        path_to_output_dir, options)
        self.__table = []
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
        current_demote_seconds = ""
        index = 0
        for dss in demote_seconds.split():
            if (((index % 5) == 0) and (not index == 0)):
                table.append([current_filesystem_name, current_glock, current_demote_seconds.strip()])
                current_filesystem_name = "-"
                current_glock = "-"
                current_demote_seconds = dss
                index = 0
            else:
                current_demote_seconds += " %s" %(dss)
                index += 1
        return table

    def __get_text(self, colorize=False):
        table = []
        for hashkey in self.__glocks_high_demote_seconds.keys():
            table += self.__tableify(hashkey, self.__glocks_high_demote_seconds.get(hashkey))
        if (table):
            return "%s: %s\n\n%s\n%s\n" %(self.get_title(), self.get_description(),
                                          "Glocks with demoting of a glocks taking greater than 0 seconds to complete.",
                                          tableize(table,["Filesystem", "Glock", "Demote Seconds"],
                                                   colorize=colorize).strip())

        return ""

    def analyze(self):
        self.__glocks_high_demote_seconds = {}
        for snapshot in self.get_snapshots():
            glock_high_demote_seconds_found = False
            for glock in snapshot.get_glocks():
                demote_time = int(glock.get_demote_time())
                if (demote_time > 0):
                    hashkey = self.__encode(glock.get_type(), glock.get_inode())
                    if (not self.__glocks_high_demote_seconds.has_key(hashkey)):
                        self.__glocks_high_demote_seconds[hashkey] = ""
                    demote_time_str = "%s %d" %(self.__glocks_high_demote_seconds.get(hashkey),
                                                demote_time)
                    self.__glocks_high_demote_seconds[hashkey] = demote_time_str
                    glock_high_demote_seconds_found = True
            if (glock_high_demote_seconds_found):
                warning_msg =  "There were glocks with demote time greater than zero."
                self.add_warning(Admonition(snapshot.get_hostname(), self.get_filesystem_name(),
                                            "Glocks", warning_msg, ""))

    def console(self):
        summary = self.__get_text(colorize=True)
        if (summary):
            print summary


    def write(self, html_format=False):
        if (self.__glocks_high_demote_seconds):
            wdata = ""
            path_to_output_file = ""
            if (not html_format):
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                wdata = self.__get_text(colorize=False)
            else:
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                table = []
                for hashkey in self.__glocks_high_demote_seconds.keys():
                    table += self.__tableify(hashkey, self.__glocks_high_demote_seconds.get(hashkey))
                bdata = generate_table(table,
                                       ["Filesystem", "Glock", "Demote Seconds"],
                                       title=self.get_title(),
                                       description="Glocks that took longer than 0 seconds to demote a glock")
                wdata = "%s\n%s\n%s" %(generate_css_header(include_css_table=True), bdata, generate_footer())
            if (wdata):
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
