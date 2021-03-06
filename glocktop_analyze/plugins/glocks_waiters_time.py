#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs only a graph of glocks holder+waiter count over time.

Options for plugin:
* mininum_waiter_count: The mininum number of holder + waiters that are required
  on a glock.
* maximum_glocks_to_graph: The maximum number of different glocks that will be graph.
"""
import logging
import logging.handlers
import os.path
from collections import OrderedDict

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.plugins import generate_date_graphs
from glocktop_analyze.html import generate_graph_index_page

class GlocksWaitersTime(Plugin):
    OPTIONS = [("mininum_waiter_count",
                "The mininum number of holder + waiters that are required on a glock.",
                2),
               ("maximum_glocks_to_graph",
                "The maximum number of different glocks that will be graph.",
                10)]

    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "glocks_waiters_time",
                        "The holder + waiters of a glock over time.",
                        snapshots,
                        "Glocks Holder and Waiters Count over Time",
                        path_to_output_dir, options)
        self.__glocks_holder_waiters_by_date = {}

        self.__mininum_waiter_count = self.get_option("mininum_waiter_count")
        self.__maximum_glocks_to_graph = self.get_option("maximum_glocks_to_graph")

    def __encode(self, glock_type, glock_inode):
        return "%s/%s" %(glock_type, glock_inode)

    def __decode(self, hashkey):
        hashkey_split = hashkey.split("/")
        return (hashkey_split[0], hashkey_split[1])

    def __generate_graphs_glocks_holder_waiter(self, glocks_holder_waiters_by_date, snapshots_date_time, png_format=False):
        # The x-axis will be the snapshots_date_time. Each glock in the map has a
        # value that is holder/waiter count at some date_time (we call gdt) instance
        # that should be a value in the snapshots_date_time.  If there is no gdt
        # instance for a date_time in snapshots_date_time then we set value at None
        # in graph.
        path_to_image_files = []
        if ((glocks_holder_waiters_by_date) and (snapshots_date_time)):
            def get_index_in_list(date_time_list, date_time):
                index = 0;
                for index in range(0, len(date_time_list)):
                    if (date_time_list[index] == date_time):
                        return index
                    index += 1
                return -1

            # Set the Y axis and create a list the same size as snapshots_date_time and set to None as each value.
            y_axis = {}
            for gkey in glocks_holder_waiters_by_date.keys():
                if (not y_axis.has_key(gkey)):
                    y_axis[gkey] = [None] * len(snapshots_date_time)
                for t in glocks_holder_waiters_by_date.get(gkey):
                    index_in_dt = get_index_in_list(snapshots_date_time, t[0])
                    if (index_in_dt >= 0):
                        y_axis[gkey][index_in_dt] = t[1]
            path_to_output_dir = os.path.join(os.path.join(self.get_path_to_output_dir(),
                                                           self.get_filesystem_name()), "graphs")
            path_to_image_files += generate_date_graphs(path_to_output_dir,
                                                        snapshots_date_time,
                                                        y_axis,
                                                        self.get_title(),
                                                        "Time of Snapshots", "Glock Type/Inode",
                                                        png_format=png_format)
            return path_to_image_files

    def analyze(self):
        # A map of all the times these glocks showed up in snapshot.
        glocks_holder_waiters_by_date = {}
        # The date_time snapshots taken on filesystem
        self.__snapshots_dt = []
        for snapshot in self.get_snapshots():
            # Get glock stats
            self.__snapshots_dt.append(snapshot.get_date_time())
            for glock in snapshot.get_glocks():
                # Unique key <filename_name>-<glock_type>/<glock_inode>
                hashkey = self.__encode(glock.get_type(), glock.get_inode())
                dt_holder_waiter_count = (snapshot.get_date_time(), len(glock.get_holders()))
                if (not glocks_holder_waiters_by_date.has_key(hashkey)):
                    glocks_holder_waiters_by_date[hashkey] = []
                glocks_holder_waiters_by_date[hashkey] += [dt_holder_waiter_count]

        # Only include the snapshot that have appeared more than once. There no
        # reason to include a glock that will only graph a point.
        for hashkey in glocks_holder_waiters_by_date.keys():
            if (not len(glocks_holder_waiters_by_date.get(hashkey)) > 1):
                try:
                    del glocks_holder_waiters_by_date[hashkey]
                except KeyError:
                    pass
        # Map the number of holder+waiters that a glock has over all the
        # snapshots.
        glocks_holder_waiters_counter = {}
        for hashkey in glocks_holder_waiters_by_date.keys():
            hw_count = 0
            for gtuple in glocks_holder_waiters_by_date.get(hashkey):
                hw_count += gtuple[1]
            if (hw_count > self.__mininum_waiter_count):
                glocks_holder_waiters_counter[hashkey] = hw_count

        # Only graph the glocks with highest holder+waiter count over all the
        # snapshots.
        glocks_highest_count = {}
        index = 1
        for t in reversed(OrderedDict(sorted(glocks_holder_waiters_counter.items(), key=lambda t: t[1]))):
            if (index > self.__maximum_glocks_to_graph):
                try:
                    del glocks_holder_waiters_counter[t]
                except KeyError:
                    pass
                index += 1

        # Map only glocks that had more than 1 holder+waiter so the possible items to graph is lower.
        self.__glocks_holder_waiters_by_date = {key: glocks_holder_waiters_by_date[key] for key in glocks_holder_waiters_by_date if key in glocks_holder_waiters_counter.keys()}

    def graph(self, png_format=False):
        if (self.__glocks_holder_waiters_by_date):
            path_to_image_files = self.__generate_graphs_glocks_holder_waiter(self.__glocks_holder_waiters_by_date,
                                                                              self.__snapshots_dt, png_format=png_format)
            if (path_to_image_files):
                generate_graph_index_page(os.path.join(self.get_path_to_output_dir(),
                                                       self.get_filesystem_name()),
                                          path_to_image_files, self.get_title())
