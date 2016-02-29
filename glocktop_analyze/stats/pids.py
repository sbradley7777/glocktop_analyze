#!/usr/bin/python
import logging
import logging.handlers
import os.path
from collections import OrderedDict

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class Pids(Stats):
    def __init__(self, snapshots, path_to_output_dir):
        Stats.__init__(self, snapshots, "Pids Stats", path_to_output_dir)

        self.__pids_in_snapshots = []
        self.__pids_using_multiple_glocks = []

    def __encode(self, pid, command):
        # Not sure what guranteees no duplicates, that command will not be empty
        # sometimes and not-empty other, etc.
        return "%s-%s" %(pid, command)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("-")
        return (hashkey_split[0], hashkey_split[1])

    def __tableify(self, row, max_strings=5):
        table = []
        current_filesystem_name = row[0]
        current_pid = row[1]
        current_command = row[2]
        current_glock_count = row[3]
        current_long_string = ""
        index = 0
        for s in row[4].split():
            if (((index % max_strings) == 0) and (not index == 0)):
                table.append([current_filesystem_name, current_pid, current_command, current_glock_count, current_long_string.strip()])
                current_filesystem_name = "-"
                current_pid = "-"
                current_command = "-"
                current_glock_count = "-"
                current_long_string = s
                index = 0
            else:
                current_long_string += " %s" %(s)
                index += 1
        return table

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
            if (items[1] > 1):
                self.__pids_in_snapshots.append([self.get_filesystem_name(), pid, command, items[1]])

        ordered_dict = OrderedDict(sorted(pids_to_glocks.items(), key=lambda t: len(t[1]), reverse=True))
        for i in range(0, len(ordered_dict)):
            items = ordered_dict.items()[i]
            (pid, command) = self.__decode(items[0])
            if (len(items[1]) > 1):
                # Change to string instead of list for value. do like glocks_high_demote_seconds.
                self.__pids_using_multiple_glocks.append([self.get_filesystem_name(), pid, command, len(items[1]), items[1]])

    def console(self):
        if (self.__pids_in_snapshots):
            print tableize(self.__pids_in_snapshots,
                           ["Filesystem", "Pid", "Command", "Number of Snapshots Appeared in"])

        if (self.__pids_using_multiple_glocks):
            ftable = []
            for row in self.__pids_using_multiple_glocks:
                ftable += self.__tableify(row)
            print tableize(ftable,
                           ["Filesystem", "Pid", "Command", "Number of Glocks Appeared in", "Glock Type/Inode"])

    def write(self):
        wdata = ""
        if (self.__pids_in_snapshots):
            wdata += tableize(self.__pids_in_snapshots,
                              ["Filesystem", "Pid", "Command", "Number of Snapshots Appeared in"],
                              colorize=True) + "\n"
        if (self.__pids_using_multiple_glocks):
            ftable = []
            for row in self.__pids_using_multiple_glocks:
                ftable += self.__tableify(row)
            wdata += tableize(ftable,
                              ["Filesystem", "Pid", "Command", "Number of Glocks Appeared in", "Glock Type/Inode"],
                              colorize=False)
        if (wdata):
            filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

