#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class GlocksHighDemoteSeconds(Stats):
    def __init__(self, snapshots, path_to_output_dir):
        Stats.__init__(self, snapshots, "Glocks with High Demote Seconds", path_to_output_dir)
        self.__table = []


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

    def analyze(self):
        glocks_high_demote_seconds = {}
        for snapshot in self.get_snapshots():
            for glock in snapshot.get_glocks():
                demote_time = int(glock.get_demote_time())
                if (demote_time > 0):
                    hashkey = self.__encode(glock.get_type(), glock.get_inode())
                    if (not glocks_high_demote_seconds.has_key(hashkey)):
                        glocks_high_demote_seconds[hashkey] = ""
                    demote_time_str = "%s %d" %(glocks_high_demote_seconds.get(hashkey),
                                                demote_time)
                    glocks_high_demote_seconds[hashkey] = demote_time_str
        self.__table = []
        for hashkey in glocks_high_demote_seconds.keys():
            self.__table += self.__tableify(hashkey, glocks_high_demote_seconds.get(hashkey))

        if(self.__table):
            self.add_warning("Glocks", "There were glocks found with a higher than zero time to demote a glock on filesystem: %s." %(self.get_filesystem_name()))

    def console(self):
        if (self.__table):
            print tableize(self.__table,["Filesystem", "Snapshots", "Demote Seconds"])

    def write(self, html_format=False):
        if (self.__table):
            wdata = ""
            path_to_output_file = ""
            if (not html_format):
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                wdata = tableize(self.__table,["Filesystem", "Snapshots", "Demote Seconds"], colorize=False)

            else:
                filename = "%s.html" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
                bdata = generate_table(["Filesystem", "Snapshots", "Demote Seconds"], self.__table,
                                       title=self.get_title(),
                                       description="Glocks that took longer than 0 seconds to demote a glock")
                wdata = "%s\n%s\n%s" %(generate_table_header(), bdata, generate_footer())
            if (wdata):
                if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                    message = "An error occurred writing to the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
