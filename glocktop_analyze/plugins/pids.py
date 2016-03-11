#!/usr/bin/python
import logging
import logging.handlers
import os.path
from collections import OrderedDict

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize, tableify
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class Pids(Plugin):
    def __init__(self, snapshots, path_to_output_dir, options={}):
        Plugin.__init__(self, "pids", "The pids information relating to glocks.",
                        snapshots, "Pids Stats", path_to_output_dir)
        self.__pids_in_snapshots = []
        self.__pids_using_multiple_glocks = []

        self.__mininum_snapshot_count = 2
        if (options.has_key("mininum_snapshot_count")):
            self.__mininum_snapshot_count = options.get("mininum_snapshot_count")
        self.__mininum_glocks_count = 2
        if (options.has_key("mininum_glocks_count")):
            self.__mininum_glocks_count = options.get("mininum_glocks_count")

    def __encode(self, pid, command):
        # Not sure what guranteees no duplicates, that command will not be empty
        # sometimes and not-empty other, etc.
        return "%s-%s" %(pid, command)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("-")
        return (hashkey_split[0], hashkey_split[1])

    def analyze(self):
        # Need to create object to hold the pid, command,
        pids_in_snapshots = {}
        pids_to_glocks = {}
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glocks():
                glock_type_inode = "%s/%s" %(glock.get_type(), glock.get_inode())
                for glock_holder in glock.get_holders():
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
        # Create structure for pids showing in snapshots.
        ordered_dict = OrderedDict(sorted(pids_in_snapshots.items(), key=lambda t: t[1], reverse=True))
        for i in range(0, len(ordered_dict)):
            items = ordered_dict.items()[i]
            (pid, command) = self.__decode(items[0])
            if (items[1] >= self.__mininum_snapshot_count):
                self.__pids_in_snapshots.append([self.get_filesystem_name(), pid, command, items[1]])

        ordered_dict = OrderedDict(sorted(pids_to_glocks.items(), key=lambda t: len(t[1]), reverse=True))
        for i in range(0, len(ordered_dict)):
            items = ordered_dict.items()[i]
            (pid, command) = self.__decode(items[0])
            if (len(items[1].split()) >= self.__mininum_glocks_count):
                # Change to string instead of list for value. do like glocks_high_demote_seconds.
                self.__pids_using_multiple_glocks.append([self.get_filesystem_name(), pid, command, len(items[1].split()), items[1]])

    def console(self):
        if (self.__pids_in_snapshots):
            print tableize(self.__pids_in_snapshots,
                           ["Filesystem", "Pid", "Command", "Number of Snapshots Appeared in"])

        if (self.__pids_using_multiple_glocks):
            ftable = []
            for row in self.__pids_using_multiple_glocks:
                ftable += tableify(row)
            print tableize(ftable,
                           ["Filesystem", "Pid", "Command", "Number of Glocks Appeared in", "Glock Type/Inode"])

    def write(self, html_format=False):
        if (not html_format):
            wdata = ""
            if (self.__pids_in_snapshots):
                wdata += tableize(self.__pids_in_snapshots,
                                  ["Filesystem", "Pid", "Command", "Number of Snapshots Appeared in"],
                                  colorize=True) + "\n"
            if (self.__pids_using_multiple_glocks):
                ftable = []
                for row in self.__pids_using_multiple_glocks:
                    ftable += tableify(row)
                wdata += tableize(ftable,
                                  ["Filesystem", "Pid", "Command", "Number of Glocks Appeared in", "Glock Type/Inode"],
                                  colorize=False)
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
            if (self.__pids_using_multiple_glocks):
                bdata += generate_table(self.__pids_using_multiple_glocks,
                                        ["Filesystem", "Pid", "Command", "Number of Glocks Appeared in", "Glock Type/Inode"],
                                        title="Pids that Appeared in Multiple Glocks.",
                                        description="The pids that appeared in multiple glocks.")
            if (bdata):
                wdata = "%s\n%s\n%s" %(generate_table_header(), bdata, generate_footer())
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                    self.get_filesystem_name()), filename)
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
