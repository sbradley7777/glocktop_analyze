#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class GlocksHighDemoteSeconds(Stats):

    def __init__(self, snapshots, title):
        Stats.__init__(self, snapshots, title)
        self.__glock_high_demote_seconds = {}


    def __encode(self, glock_type, glock_inode):
        return "%s/%s" %(glock_type, glock_inode)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("/")
        return (hashkey_split[0], hashkey_split[1])

    def __tableize(self, filesystem_name, glock_type_inodes_map):
        # Glock + filesystem with high demote seconds.
        table = []
        for key in glock_type_inodes_map.keys():

            current_filesystem_name = filesystem_name
            current_glock = key
            current_demo_seconds = ""
            index = 0
            for dss in glock_type_inodes_map.get(key).split():
                if (((index % 5) == 0) and (not index == 0)):
                    table.append([current_filesystem_name, current_glock, current_demo_seconds.strip()])
                    current_fs_name = "-"
                    current_glock = "-"
                    current_demo_seconds = dss
                    index = 0
                else:
                    current_demo_seconds += " %s" %(dss)
                    index += 1
        return table


    def analyze(self):
            for snapshot in self.get_snapshots():
                filesystem_name = snapshot.get_filesystem_name()
                if (not self.__glock_high_demote_seconds.has_key(filesystem_name)):
                    self.__glock_high_demote_seconds[filesystem_name] = {}
                glock_type_inodes_map = self.__glock_high_demote_seconds[filesystem_name]
                for glock in snapshot.get_glocks():
                    # Unique key <filename_name>-<glock_type>/<glock_inode>
                    hashkey = self.__encode(glock.get_type(), glock.get_inode())
                    demote_time = int(glock.get_demote_time())
                    if (demote_time > 0):
                        if (glock_type_inodes_map.has_key(hashkey)):
                            c_demote_time = glock_type_inodes_map.get(hashkey)
                            c_demote_time += " %d" %(demote_time)
                            glock_type_inodes_map[hashkey] = c_demote_time
                        else:
                            glock_type_inodes_map[hashkey] = "%d" %(demote_time)


    def console(self):
        for filesystem_name in self.__glock_high_demote_seconds.keys():
            glock_type_inodes_map = self.__glock_high_demote_seconds[filesystem_name]
            print tableize(self.__tableize(filesystem_name, glock_type_inodes_map),
                           ["Filesystem", "Snapshots", "Demote Seconds"])

    def write(self, path_to_output_dir):
        for filesystem_name in self.__glock_high_demote_seconds.keys():
            glock_type_inodes_map = self.__glock_high_demote_seconds[filesystem_name]
            ftable = tableize(self.__tableize(filesystem_name, glock_type_inodes_map),
                              ["Filesystem", "Snapshots", "Demote Seconds"], colorize=False)

            filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(path_to_output_dir, filesystem_name), filename)
            if (not write_to_file(path_to_output_file, ftable, append_to_file=False, create_file=True)):
                message = "An error occurred writing the glocks stats to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
