#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file
from glocktop_analyze.html import generate_header, generate_footer

class GlocksActivity(Plugin):
    def __init__(self, snapshots, path_to_output_dir):
        Plugin.__init__(self, snapshots, "Glocks Activity", path_to_output_dir)
        self.__minimum_waiter_count = 2
        self.__glock_dump = []

    def __get_text(self, colorize=False):
        summary = ""
        for snapshot in self.get_snapshots():
            current_summary = ""
            glocks = snapshot.get_glocks()
            for glock in glocks:
                glock_holders = glock.get_holders()
                if (len(glock_holders) >= self.__minimum_waiter_count):
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
        for snapshot in self.get_snapshots():
            current_summary = ""
            glocks = snapshot.get_glocks()
            for glock in glocks:
                glock_holders = glock.get_holders()
                if (len(glock_holders) >= self.__minimum_waiter_count):
                    current_summary += "  %s<BR/>" %(glock)
                    for holder in glock_holders:
                        current_summary += "%s<BR/>" %(holder)
                    if (not glock.get_glock_object() == None):
                        current_summary += "%s<BR/>" %(glock.get_glock_object())
                if (current_summary):
                    current_summary_title = str(snapshot)
                    if (colorize):
                        current_summary_title = "<b>%s</b>" %(str(snapshot))
                    summary += "%s<BR/>%s<BR/>" %(current_summary_title, current_summary)
        return summary

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
