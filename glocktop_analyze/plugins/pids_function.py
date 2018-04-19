#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin checks which function a pid is in.
* This plugin outputs any known issues based on patterns found.

Options for this plugin:
"""
import logging
import logging.handlers
import os.path
from collections import OrderedDict

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_css_header, generate_table
from glocktop_analyze.html import generate_footer

class PidsFunction(Plugin):
    OPTIONS = [("commands_to_ignore",
                "A comma seperated list of commands that will be ignored.",
                "gfs2_quotad")]

    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "pids_function", "Analyzes the function each pid is in.",
                        snapshots, "Pids Functions", path_to_output_dir, options)
        self.__pids_in_snapshots = []

        self.__gfs2_functions = {"gfs2_inplace_reserve":[], "gfs2_inplace_reserve":[]}

        # List of processes to ignore by default:
        self.__commands_to_ignore = []
        for command in self.get_option("commands_to_ignore").split(","):
            self.__commands_to_ignore.append(command.strip())

    def __encode(self, pid, command):
        # Not sure what guranteees no duplicates, that command will not be empty
        # sometimes and not-empty other, etc.
        return "%s-%s" %(pid, command)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("-")
        return (hashkey_split[0], hashkey_split[1])

    def __get_text(self, colorize=False):
        summary = ""
        for gfs2_function in self.__gfs2_functions.keys():
            glocks = self.__gfs2_functions.get(gfs2_function)
            for glock in glocks:
                glock_hw = glock.get_holders()[0]
                print glock
                print "  %s" %(glock_hw)
                for ct in glock_hw.get_call_trace():
                    print "  --> %s" %(ct)
                print
        if (summary):
            summary =  "%s: %s\n\n%s\n" %(self.get_title(), self.get_description(), summary.strip())
        return summary

    def analyze(self):
        # Need to create object to hold the pid, command,
        pids_in_snapshots = {}
        pids_to_glocks = {}
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glocks():
                if (glock.get_holders()):
                    call_trace = glock.get_holders()[0].get_call_trace()
                    if (call_trace):
                        for gfs2_function in self.__gfs2_functions.keys():
                            if (gfs2_function in call_trace):
                                self.__gfs2_functions[gfs2_function].append(glock)
                """
                glock_type_inode = "%s/%s" %(glock.get_type(), glock.get_inode())
                for glock_holder in glock.get_holders():
                    print glock_holder.get_function()
                    if (glock_holder.get_function() in self.__gfs2_functions.keys()):
                        print glock_holder.get_function()
                    hashkey = self.__encode(glock_holder.get_pid(), glock_holder.get_command())
                    # Count the times a pid showed up in snapshot.
                    if (not pids_in_snapshots.has_key(hashkey)):
                        pids_in_snapshots[hashkey] = 0
                    pids_in_snapshots[hashkey] += 1
                    # Map pids and its glocks
                    if (not pids_to_glocks.has_key(hashkey)):
                        pids_to_glocks[hashkey] = ""
                    if (not glock_type_inode in pids_to_glocks[hashkey]):
                        pids_to_glocks[hashkey] += " %s" %(glock_type_inode)
                """
        """
        # Create structure for pids showing in snapshots.
        ordered_dict = OrderedDict(sorted(pids_in_snapshots.items(), key=lambda t: t[1], reverse=True))
        for i in range(0, len(ordered_dict)):
            items = ordered_dict.items()[i]
            (pid, command) = self.__decode(items[0])
            if (not command in self.__commands_to_ignore):
                    self.__pids_in_snapshots.append([self.get_filesystem_name(), pid, command, items[1]])
        """

    def console(self):
        summary = self.__get_text(colorize=True)
        if (summary):
            print "%s\n" %(summary.rstrip())

    def write(self, html_format=False):
        pass
        """
        if (not html_format):
            wdata = self.__get_text(colorize=False)
            if (wdata):
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        else:
            bdata = ""
            if (self.__pids_in_snapshots):
                bdata += generate_table(self.__pids_in_snapshots,
                                        ["Filesystem", "Pid", "Command", "Number of Snapshots Appeared in"],
                                        title="Pids Appearing in Multiple Snapshots",
                                        description="The pids that appeared in multiple snapshots.")
            if (bdata):
                wdata = "%s\n%s\n%s" %(generate_css_header(include_css_table=True), bdata, generate_footer())
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                    self.get_filesystem_name()), filename)
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        """
