#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the raw lockdump data. It outputs in a simpler view of the
  data and has option to only output glocks that have minimum holder+waiters
  count for a snapshot.

Options for this plugin:
* mininum_waiter_count: The glock's lockdump analyzed for multiple holder and
  waiters.

"""
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file
from glocktop_analyze.html import generate_header, generate_footer

class GlocksActivity(Plugin):
    OPTIONS = [("mininum_waiter_count",
                "The mininum number of holder and waiters that are required on a glock.",
                2)]
    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_activity",
                        "The glock's lockdump analyzed for multiple holder and waiters.",
                        snapshots, "Glocks Activity", path_to_output_dir,
                        options)
        self.__glock_dump = []
        self.__mininum_waiter_count = int(self.get_option("mininum_waiter_count"))

    def __get_text(self, colorize=False):
        summary = ""
        for snapshot in self.get_snapshots():
            current_summary = ""
            glocks = snapshot.get_glocks()
            for glock in glocks:
                glock_holders = glock.get_holders()
                if (len(glock_holders) >= self.__mininum_waiter_count):
                    current_summary += "  %s\n" %(glock)
                    for holder in glock_holders:
                        current_summary += "     %s\n" %(holder)
                    if (not glock.get_glock_object() == None):
                        current_summary += "     %s\n" %(glock.get_glock_object())
                if (current_summary):
                    current_summary_title = str(snapshot)
                    if (colorize):
                        current_summary_title = ColorizeConsoleText.red(str(snapshot))
                    summary += "%s\n%s\n" %(current_summary_title, current_summary)
        return summary

    def __get_html(self, colorize=False):
        summary = ""
        start_time = None
        end_time = None
        for snapshot in self.get_snapshots():
            current_summary = ""
            glocks = snapshot.get_glocks()
            if (start_time == None):
                start_time = snapshot.get_date_time()
            end_time = snapshot.get_date_time()
            for glock in glocks:
                glock_holders = glock.get_holders()
                if (len(glock_holders) >= self.__mininum_waiter_count):
                    current_summary += "  %s<BR/>" %(glock)
                    for holder in glock_holders:
                        current_summary += "&nbsp;&nbsp;&nbsp;&nbsp; %s<BR/>" %(holder)
                    if (not glock.get_glock_object() == None):
                        current_summary += "&nbsp;&nbsp;&nbsp;&nbsp; %s<BR/>" %(glock.get_glock_object())
                    current_summary += "<BR/>"
                if (current_summary):
                    current_summary_title = str(snapshot)
                    if (colorize):
                        current_summary_title = "<b>%s</b>" %(str(snapshot))
                    summary += "%s<BR/>%s" %(current_summary_title, current_summary)
        header =  "<center><H3>Glock Activity between "
        header += "%s and %s </H3></center>" %(start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                               end_time.strftime("%Y-%m-%d %H:%M:%S"))
        return header + summary

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
            bdata = self.__get_html(colorize=True)
            wdata = "%s\n%s\n<BR/><HR/><BR/>%s" %(generate_header(), bdata, generate_footer())

            filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)

        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
