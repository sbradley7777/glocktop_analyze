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

import glocktop_analyze
from glocktop_analyze.plugins import PluginMultinode
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class SnapshotsMultinode(PluginMultinode):
    def __init__(self, snapshots, path_to_output_dir, options):
        PluginMultinode.__init__(self, "snapshots multiply nodes",
                                 "The stats for the snapshots and dlm activity for multiply nodes.",
                                 snapshots, "Snapshot Stats for Mulitple Nodes", path_to_output_dir,
                                 options)

        self.__start_time_for_hosts = {}
        self.__stop_time_for_hosts = {}
        self.__snapshot_count_for_hosts = {}
        self.__dlm_activity_for_hosts = {}

    def analyze(self):
        for hostname in self.get_hostnames():
            date_time = self.get_snapshots_start_time(hostname)
            if (not date_time == None):
                self.__start_time_for_hosts[hostname] = date_time
            date_time = self.get_snapshots_end_time(hostname)
            if (not date_time == None):
                self.__stop_time_for_hosts[hostname] = date_time
            for snapshot in self.get_snapshots(hostname):
                if (not self.__snapshot_count_for_hosts.has_key(hostname)):
                    self.__snapshot_count_for_hosts[hostname] = 0
                self.__snapshot_count_for_hosts[hostname] += 1
            dlm_activity = snapshot.get_dlm_activity()
            if (not dlm_activity == None):
                if (not self.__dlm_activity_for_hosts.has_key(hostname)):
                    self.__dlm_activity_for_hosts[hostname] = []
                    dlm_activity_data = [self.get_filesystem_name(),
                                         snapshot.get_date_time(),
                                         dlm_activity.get_waiter_count()]
                    self.__dlm_activity_for_hosts[hostname].append(dlm_activity_data)

    def console(self):
        summary = ""
        snapshots_table = []
        dlm_activity_table = []
        for hostname in self.get_hostnames():
            if (self.get_snapshots(hostname)):
                snapshots_table.append([hostname, self.get_filesystem_name(),
                                        str(self.__snapshot_count_for_hosts.get(hostname)),
                                        str(self.__start_time_for_hosts.get(hostname)),
                                        str(self.__stop_time_for_hosts.get(hostname))])

            if (self.__dlm_activity_for_hosts.has_key(hostname)):
                dlm_activity_table.append(self.__dlm_activity_for_hosts.get(hostname))

        if (snapshots_table):
            summary += "%s\n\n" %(tableize(snapshots_table, ["Hostname", "Filesystem",
                                                             "Snapshots", "Start Time",
                                                             "Stop Time"]).strip())
        if (dlm_activity_table):
            summary += "%s\n\n" %(tableize(dlm_activity_table, ["Hostname", "Filesystem",
                                                                "Snapshot Time",
                                                                "Number of DLM Waiters"]).strip())
        if (summary):
            print "%s: %s\n%s\n" %(self.get_title(), self.get_description(), summary.strip())
        return summary

    def write(self, html_format=False):
        pass
