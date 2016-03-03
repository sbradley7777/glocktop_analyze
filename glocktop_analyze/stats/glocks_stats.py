#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.stats import generate_graph_index_page, generate_date_graphs

class GSStats(Stats):
    def __init__(self, snapshots, path_to_output_dir):
        snapshots_with_stats = []
        for snapshot in snapshots:
            if (not snapshot.get_glocks_stats() == None):
                snapshots_with_stats.append(snapshot)
        Stats.__init__(self, snapshots_with_stats, "Glocks Stats", path_to_output_dir)
        self.__console_summary = ""
        self.__file_summary = ""

    def __generate_graphs_by_glock_type(self, format_png=False):
        path_to_output_dir = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                       self.get_filesystem_name()), "graphs")
        if (self.get_snapshots()):
            path_to_image_files = []
            snapshot_date_time = []
            # This is graphing the states for differnt glock types. X is time, Y is
            # one of 8 glock states.
            for gtype in glocktop_analyze.glocks_stats.GLOCK_TYPES:
                glock_states_stats = {}
                for snapshot in self.get_snapshots():
                    glocks_stats = snapshot.get_glocks_stats()
                    if (not snapshot.get_date_time() in snapshot_date_time):
                        snapshot_date_time.append(snapshot.get_date_time())
                    states_stats = glocks_stats.get_stats_by_type(gtype)
                    for key in states_stats.keys():
                        if (glock_states_stats.has_key(key)):
                            glock_states_stats[key].append(states_stats.get(key))
                        else:
                            glock_states_stats[key] = [states_stats.get(key)]
                path_to_image_files += generate_date_graphs(path_to_output_dir,
                                                            snapshot_date_time,
                                                            glock_states_stats,
                                                            "%s - %s" %(self.get_filesystem_name(), gtype),
                                                            "Time of Snapshots", "Glock States",
                                                            format_png= format_png)
            return path_to_image_files

    def __generate_graphs_by_glock_state(self, format_png=False):
        path_to_output_dir = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                       self.get_filesystem_name()), "graphs")
        if (self.get_snapshots()):
            path_to_image_files = []
            snapshot_date_time = []
            # This is graphing the states for differnt glock states. X is time, Y is
            # one of 7 glock types.
            for gstate in glocktop_analyze.glocks_stats.GLOCK_STATES:
                glock_types_stats = {}
                for snapshot in self.get_snapshots():
                    glocks_stats = snapshot.get_glocks_stats()
                    if (not snapshot.get_date_time() in snapshot_date_time):
                        snapshot_date_time.append(snapshot.get_date_time())
                    gtypes_stats = glocks_stats.get_stats_by_state(gstate)
                    for key in gtypes_stats.keys():
                        if (glock_types_stats.has_key(key)):
                            glock_types_stats[key].append(gtypes_stats.get(key))
                        else:
                            glock_types_stats[key] = [gtypes_stats.get(key)]
                path_to_image_files += generate_date_graphs(path_to_output_dir,
                                                            snapshot_date_time,
                                                            glock_types_stats,
                                                            "%s - %s" %(self.get_filesystem_name(), gstate),
                                                            "Time of Snapshots", "Glock Types",
                                                            format_png=format_png)
            return path_to_image_files

    def analyze(self):
        filesystem_name = self.get_filesystem_name()
        for snapshot in self.get_snapshots():
            glocks_stats = snapshot.get_glocks_stats()
            self.__file_summary +=  "Glock stats at %s for filesystem: " %(glocks_stats.get_date_time().strftime("%Y-%m-%d %H:%M:%S"))
            self.__file_summary += "%s\n%s\n\n" %(filesystem_name, str(glocks_stats))
            formatted_table = tableize(glocks_stats.get_table(), ["Glock States"] +
                                       glocktop_analyze.glocks_stats.GLOCK_STATES, colorize=True).rstrip()
            self.__console_summary += "Glock stats at %s for filesystem: " %(ColorizeConsoleText.orange(
                glocks_stats.get_date_time().strftime("%Y-%m-%d %H:%M:%S")))
            self.__console_summary += "%s\n%s\n\n" %(ColorizeConsoleText.orange(
                filesystem_name), formatted_table)

    def console(self):
        if (self.__console_summary):
            print "%s\n" %(self.__console_summary.rstrip())

    def write(self):
        if (self.__file_summary):
            filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
            path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                            self.get_filesystem_name()), filename)
            if (not write_to_file(path_to_output_file, self.__file_summary, append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

    def graph(self, enable_png_format=False):
        if (self.get_snapshots()):
            path_to_image_files = self.__generate_graphs_by_glock_type(format_png=enable_png_format)
            if (path_to_image_files):
                generate_graph_index_page(os.path.join(self.get_path_to_output_dir(),
                                                       self.get_filesystem_name()),
                                          path_to_image_files, "Glock Types")
            path_to_image_files = self.__generate_graphs_by_glock_state(format_png=enable_png_format)
            if (path_to_image_files):
                generate_graph_index_page(os.path.join(self.get_path_to_output_dir(),
                                                       self.get_filesystem_name()),
                                          path_to_image_files, "Glock States")
