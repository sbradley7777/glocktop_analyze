#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the raw lockdump data from multiple nodes. It outputs in a
  simpler view of the data and has option to only output glocks that have
  minimum holder+waiters count for a snapshot.

Options for this plugin:
* mininum_waiter_count: The glock's lockdump analyzed for multiple holder and
  waiters.

"""
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import PluginMultinode
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file
from glocktop_analyze.html import generate_css_header, generate_footer

class GlocksActivityMultipleNodes(PluginMultinode):
    OPTIONS = [("mininum_waiter_count",
                "The mininum number of holder and waiters that are required on a glock.",
                2)]
    def __init__(self, grouped_snapshots, path_to_output_dir, options):
        PluginMultinode.__init__(self, "glocks_activity-multiple_nodes",
                                 "The glock's lockdump analyzed for multiple holder and waiters from multiple nodes.",
                                 grouped_snapshots, "Glocks Activity for Multiple Nodes", path_to_output_dir,
                                 options)
        self.__mininum_waiter_count = int(self.get_option("mininum_waiter_count"))

    def __get_text(self, colorize=False):
        summary = ""
        return ""

    def __get_raw(self, colorize=False):
        raw_data = ""
        sorted_snapshots = self.get_snapshots_sorted_by_time()
        for snapshot in sorted_snapshots:
            current_raw_data = ""
            glocks = snapshot.get_glocks()
            for glock in glocks:
                glock_holders = glock.get_holders()
                current_raw_data += "  %s\n" %(glock)
                for holder in glock_holders:
                    current_raw_data += "     %s\n" %(holder)
                    if (not glock.get_glock_object() == None):
                        current_raw_data += "     %s\n" %(glock.get_glock_object())
            if (current_raw_data):
                raw_data += "%s\n  %s\n\n" %(str(snapshot), current_raw_data.strip())
        return raw_data.strip()

    def __get_html(self, colorize=False):
        summary = ""
        return ""

    def console(self):
        summary = self.__get_text(colorize=True)
        if (summary):
            print "%s\n" %(summary.rstrip())

    def write(self, html_format=False):
        wdata = ""
        path_to_output_file = ""
        if (not html_format):
            wdata = self.__get_text(colorize=False)
            filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)

        else:
            filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
            bdata = self.__get_html(colorize=True)
            if (bdata):
                wdata = "%s\n%s\n<BR/><HR/><BR/>%s" %(generate_css_header(), bdata, generate_footer())


        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        raw_data = self.__get_raw()
        if (raw_data):
            filename = "%s-raw.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
            if (not write_to_file(path_to_output_file, "%s\n" %(raw_data),
                                  append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
