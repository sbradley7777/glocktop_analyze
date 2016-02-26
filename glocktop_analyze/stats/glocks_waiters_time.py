#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import write_to_file
from glocktop_analyze.stats import generate_graph_index_page, generate_date_graphs

class GlocksWaitersTime(Stats):
    def __init__(self, snapshots):
        Stats.__init__(self, snapshots, "Glocks Holder and Waiters Count over Time")

    def __generate_graphs_glocks_holder_waiter(self, path_to_output_dir, glocks_holder_waiters_by_date, snapshots_date_time, format_png=False):
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
                path_to_image_files += generate_date_graphs(path_to_output_dir,
                                                            snapshots_date_time,
                                                            y_axis,
                                                            "Glock Holder and Waiters",
                                                            "Time of Snapshots", "Glock Type/Inode",
                                                            format_png=format_png)
            if (path_to_image_files):
                generate_graph_index_page(path_to_output_dir, path_to_image_files, "Glock Holder and Waiters")


    def analyze(self):
        for snapshot in self.get_snapshots():
            break
        """
        try:
            # svg does better charts. png support requires the python files:
            # lxml, cairosvg, tinycss, cssselect
            enable_png_format=False
            if (not cmdline_opts.disable_graphs):
                # Do various stats on the snapshots.
                #
                # The number of times that a glock appear in a snapshot for a
                # filesystem.
                glocks_appeared_in_snapshots = {}
                # The number of holders and waiters including the time taken for
                # each snapshot it appeared in.
                glocks_holder_waiters_by_date = {}
                # In some instances the unique key will be
                # "filesystem_name-glock_type/glock_inode". For example:
                # gfs2payroll-4/42ff2. Then for printing the filesystem and glock
                # info could be parsed out.

                for filesystem_name in snapshots_by_filesystem.keys():
                    snapshots = snapshots_by_filesystem.get(filesystem_name)
                    # Get glock stats
                    for glock in snapshot.get_glocks():
                        # Unique key <filename_name>-<glock_type>/<glock_inode>
                        glock_type_inode = "%s-%s/%s" %(filesystem_name, glock.get_type(), glock.get_inode())
                        if (glocks_appeared_in_snapshots.has_key(glock_type_inode)):
                            glocks_appeared_in_snapshots[glock_type_inode] = glocks_appeared_in_snapshots.get(glock_type_inode) + 1
                            dt_holder_waiter_count = (snapshot.get_date_time(), len(glock.get_holders()))
                            glocks_holder_waiters_by_date[glock_type_inode] += [dt_holder_waiter_count]
                        else:
                            glocks_appeared_in_snapshots[glock_type_inode] = 1
                            dt_holder_waiter_count = (snapshot.get_date_time(), len(glock.get_holders()))
                            glocks_holder_waiters_by_date[glock_type_inode] = [dt_holder_waiter_count]

                snapshots_by_filesystem = {}
                for snapshot in snapshots:
                    glocks_stats = snapshot.get_glocks_stats()
                    if (not glocks_stats == None):
                        if (snapshots_by_filesystem.has_key(snapshot.get_filesystem_name())):
                            snapshots_by_filesystem[snapshot.get_filesystem_name()].append(snapshot)
                        else:
                            snapshots_by_filesystem[snapshot.get_filesystem_name()] = [snapshot]
                for filesystem_name in snapshots_by_filesystem:
                    generate_graphs_by_glock_type(os.path.join(path_to_output_dir, filesystem_name),
                                                  snapshots_by_filesystem.get(filesystem_name),
                                                  format_png=enable_png_format)
                for filesystem_name in snapshots_by_filesystem:
                    generate_graphs_by_glock_state(os.path.join(path_to_output_dir, filesystem_name),
                                                   snapshots_by_filesystem.get(filesystem_name),
                                                   format_png=enable_png_format)

                # Graph the glocks number of holders and waiters over time.
                message = "Generating the graphs for glock's holder+waiter count over time."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                # Get the date/time of all the snapshots bor each filesystems.
                filesystem_snapshot_dt = {}
                for snapshot in snapshots:
                    filesystem_name = snapshot.get_filesystem_name()
                    # Get filesystem stats
                    if (filesystem_snapshot_dt.has_key(filesystem_name)):
                        filesystem_snapshot_dt[filesystem_name].append(snapshot.get_date_time())
                    else:
                        filesystem_snapshot_dt[filesystem_name] = [snapshot.get_date_time()]

                glocks_in_snapshots = {}
                for pair in sorted(glocks_appeared_in_snapshots.items(), key=itemgetter(1), reverse=True):
                    # Only include if there is more than one waiter.
                    if (pair[1] > 1):
                        filesystem_name = pair[0].rsplit("-")[0]
                        if (not glocks_in_snapshots.has_key(filesystem_name)):
                            glocks_in_snapshots[filesystem_name] = []
                            glocks_in_snapshots.get(filesystem_name).append([])
                            glocks_in_snapshots.get(filesystem_name).append([])
                        glocks_in_snapshots.get(filesystem_name)[0].append(pair[0].rsplit("-")[1])
                        glocks_in_snapshots.get(filesystem_name)[1].append(pair[1])

                # Find glocks that had more than one holder+waiters.
                for filesystem_name in glocks_in_snapshots.keys():
                    glocks_holder_waiters_counter = {}
                    for gkey in glocks_holder_waiters_by_date.keys():
                        hw_count = 0
                        if (gkey.startswith(filesystem_name)):
                            for gtuple in glocks_holder_waiters_by_date.get(gkey):
                                hw_count += gtuple[1]
                        if (hw_count > 1):
                            glocks_holder_waiters_counter[gkey] = hw_count

                    # Only graph the top 10 glocks with highest holder+waiter count.
                    max_glocks_to_graph = 10
                    glocks_highest_count = {}
                    index = 1
                    for t in reversed(OrderedDict(sorted(glocks_holder_waiters_counter.items(), key=lambda t: t[1]))):
                        if (index > max_glocks_to_graph):
                            try:
                                del glocks_holder_waiters_counter[t]
                            except KeyError:
                                pass
                        index += 1
                    # Map only glocks that had more than 1 holder+waiter so the possible items to graph is lower.
                    glocks_to_graph = {key.rsplit("-")[1]: glocks_holder_waiters_by_date[key] for key in glocks_holder_waiters_by_date if key in glocks_holder_waiters_counter.keys()}
                    generate_graphs_glocks_holder_waiter(os.path.join(path_to_output_dir, filesystem_name),
                                                         glocks_to_graph,
                                                         filesystem_snapshot_dt[filesystem_name], format_png=enable_png_format)
                message = "The graphs were to the directory: %s" %(path_to_output_dir)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
        except AttributeError:
            # Graphing must be disabled since option does not exists.
            pass
        """

    def graph(self, path_to_output_dir, enable_png_format=False):
        path_to_graphs_dir = os.path.join(os.path.join(path_to_output_dir, self.get_filesystem_name()), "graphs")
        self.__generate_graphs_by_glock_type(path_to_output_dir, format_png=enable_png_format)
        if (path_to_image_files):
            generate_graph_index_page(path_to_output_dir, path_to_image_files,  self.get_title())
