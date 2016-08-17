#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the number of snapshots taken for a filesystem, the start
  time, and end time or last snapshot taken from multiply nodes.

* This plugin outputs the filesystem name, time when snapshot taken when dlm
  activity is greater than zero from multiply nodes.

"""
import logging
import logging.handlers
import os.path
import locale

import glocktop_analyze
from glocktop_analyze.plugins import PluginMultinode
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class SnapshotsMultipleNodes(PluginMultinode):
    def __init__(self, grouped_snapshots, path_to_output_dir, options):
        PluginMultinode.__init__(self, "snapshots-multiple_nodes",
                                 "The stats for the snapshots and dlm activity for multiple nodes.",
                                 grouped_snapshots, "Snapshot Stats for Multiple Nodes", path_to_output_dir,
                                 options)

        self.__start_time_for_hosts = {}
        self.__stop_time_for_hosts = {}
        self.__snapshot_count_for_hosts = {}
        self.__dlm_activity_for_hosts = {}
        self.__gs_glocks_total_lowest = {}
        self.__gs_glocks_total_highest = {}

    def __get_glocks_count_table(self, hostname, glocks_stats_lowest, glocks_stats_highest):
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            # Set default
            locale.setlocale(locale.LC_ALL, '')
        glocks_stats_totals_table = []
        glocks_count = locale.format('%d',
                                     glocks_stats_lowest.get_glocks_count(),
                                     True)
        glocks_stats_totals_table.append([hostname,
                                          glocks_stats_lowest.get_filesystem_name(),
                                          glocks_stats_lowest.get_date_time(),
                                          glocks_count])
        glocks_count = locale.format('%d',
                                     glocks_stats_highest.get_glocks_count(),
                                     True)
        glocks_stats_totals_table.append([hostname,
                                          glocks_stats_highest.get_filesystem_name(),
                                          glocks_stats_highest.get_date_time(),
                                                                  glocks_count])
        return glocks_stats_totals_table

    def __get_text(self, colorize=False):
        summary = ""
        snapshots_table = []
        dlm_activity_table = []
        glocks_stats_totals_table = []
        for hostname in self.get_hostnames():
            if (self.get_snapshots(hostname)):
                snapshots_table.append([hostname, self.get_filesystem_name(),
                                        str(self.__snapshot_count_for_hosts.get(hostname)),
                                        str(self.__start_time_for_hosts.get(hostname)),
                                        str(self.__stop_time_for_hosts.get(hostname))])

            if (self.__dlm_activity_for_hosts.has_key(hostname)):
                dlm_activity_table += self.__dlm_activity_for_hosts.get(hostname)
            if (self.__gs_glocks_total_lowest.has_key(hostname) and
                self.__gs_glocks_total_highest.has_key(hostname)):
                glocks_stats_totals_table += self.__get_glocks_count_table(hostname,
                    self.__gs_glocks_total_lowest.get(hostname),
                    self.__gs_glocks_total_highest.get(hostname))

        if (snapshots_table):
            summary += "Snapshots Taken Start and Stop Time\n"
            summary += "%s\n\n" %(tableize(snapshots_table,
                                           ["Hostname", "Filesystem",
                                            "Snapshots", "Start Time",
                                            "Stop Time"],
                                           colorize).strip())
        if (glocks_stats_totals_table):
            summary += "The lowest and highest glock totals for all filesystems\n"
            summary +=  "%s\n\n" %(tableize(glocks_stats_totals_table,
                                            ["Hostname", "Filesystem",
                                             "Snapshot Time", "Glock Total Count"],
                                            colorize=colorize).strip())

        if (dlm_activity_table):
            sorted_dlm_activity_table = sorted(dlm_activity_table, key=lambda d: d[2], reverse=False)
            summary += "Snapshots with DLM Activity\n"
            summary += "%s\n\n" %(tableize(sorted_dlm_activity_table,
                                           ["Hostname", "Filesystem",
                                            "Snapshot Time",
                                            "Number of DLM Waiters"],
                                           colorize).strip())
        # Group the snapshots together based on time snapshot taken.
        grouped_snapshots = self.get_snapshots_by_group()
        group_count_sorted = grouped_snapshots.keys()
        group_count_sorted.sort()
        snapshots_table_by_group = ""
        for group_count in group_count_sorted:
            gsnapshots = grouped_snapshots.get(group_count)
            gtable = []
            for gsnapshot in gsnapshots:
                gtable.append([gsnapshot.get_hostname(),
                               gsnapshot.get_filesystem_name(),
                               gsnapshot.get_date_time()])
            snapshots_table_by_group  +=  "%s\n\n" %(tableize(gtable, ["Hostname", "Filesystem",
                                                                      "Snapshot Time"], colorize)).strip()
        if (snapshots_table_by_group):
            summary += "Snapshots Grouped by Time Snapshot Taken\n%s" %(snapshots_table_by_group)
        return summary

    def analyze(self):
        for hostname in self.get_hostnames():
            date_time = self.get_snapshots_start_time(hostname)
            if (not date_time == None):
                self.__start_time_for_hosts[hostname] = date_time
            date_time = self.get_snapshots_end_time(hostname)
            if (not date_time == None):
                self.__stop_time_for_hosts[hostname] = date_time
            self.__snapshot_count_for_hosts[hostname] = len(self.get_snapshots(hostname))

        for snapshot in self.get_snapshots():
            hostname = snapshot.get_hostname()
            dlm_activity = snapshot.get_dlm_activity()
            if (not dlm_activity == None):
                if (not self.__dlm_activity_for_hosts.has_key(hostname)):
                    self.__dlm_activity_for_hosts[hostname] = []
                    dlm_activity_data = [hostname,
                                         self.get_filesystem_name(),
                                         snapshot.get_date_time(),
                                         dlm_activity.get_waiter_count()]
                    self.__dlm_activity_for_hosts[hostname].append(dlm_activity_data)
            # Get the lowest and  highest glock totals
            glocks_stats = snapshot.get_glocks_stats()
            if (not glocks_stats == None):
                if (not self.__gs_glocks_total_lowest.has_key(hostname)):
                    self.__gs_glocks_total_lowest[hostname] = glocks_stats
                elif (glocks_stats.get_glocks_count() <= self.__gs_glocks_total_lowest[hostname].get_glocks_count()):
                    self.__gs_glocks_total_lowest[hostname] = glocks_stats

                if (not self.__gs_glocks_total_highest.has_key(hostname)):
                    self.__gs_glocks_total_highest[hostname] = glocks_stats
                elif (glocks_stats.get_glocks_count() >= self.__gs_glocks_total_highest[hostname].get_glocks_count()):
                    self.__gs_glocks_total_highest[hostname] = glocks_stats

    def console(self):
        summary = self.__get_text(colorize=True)
        if (summary):
            print "%s: %s\n%s\n" %(self.get_title(), self.get_description(), summary.strip())

    def write(self, html_format=False):
        wdata = ""
        path_to_output_file = ""
        if (not html_format):
            summary = self.__get_text(colorize=False)
            if (summary):
                wdata = "%s: %s\n%s\n" %(self.get_title(), self.get_description(), summary.strip())
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
        else:
            message = "This plugin does not currently have HTML format. Only text format."
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
            summary = self.__get_text(colorize=False)
            if (summary):
                wdata = "%s: %s\n%s\n" %(self.get_title(), self.get_description(), summary.strip())
                filename = "%s.txt" %(self.get_title().lower().replace(" - ", "-").replace(" ", "_"))
                path_to_output_file = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                                self.get_filesystem_name()), filename)
        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing to the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
