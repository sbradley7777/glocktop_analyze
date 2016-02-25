#!/usr/bin/python
# Options for the charts and graphs are located in the followig file:
# /usr/lib/python2.7/site-packages/pygal/config.py

import os
import logging
from datetime import datetime

import glocktop_analyze
from glocktop_analyze.gfs2_snapshot import GFS2Snapshot
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import LogWriter, mkdirs, write_to_file

MAXIMUM_X_POINTS = 200
MAXIMUM_Y_POINTS = 200

try:
    import pygal
    from pygal.style import Style
except (ImportError, NameError):
    message = "Failed to import pygal. The python-pygal package needs to be installed."
    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)


class Stats(object):
    def __init__(self, snapshots, title):
        self.__snapshots = snapshots
        self.__title = title

    def get_snapshots(self):
        return self.__snapshots

    def get_title(self):
        return self.__title

    def analayze(self):
        pass

    def console(self):
        pass

    def write(self, path_to_output_dir):
        pass

    def graph(self, path_to_output_dir):
        pass


def generate_graphs_by_glock_type(path_to_output_dir, snapshots, format_png=False):
    if (snapshots):
        path_to_image_files = []
        snapshot_date_time = []
        filesystem_name = snapshots[0].get_filesystem_name()
        # This is graphing the states for differnt glock types. X is time, Y is
        # one of 8 glock states.
        for gtype in glocktop_analyze.glocks_stats.GLOCK_TYPES:
            glock_states_stats = {}
            for snapshot in snapshots:
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
                                                        "%s - %s" %(filesystem_name, gtype),
                                                        "Time of Snapshots", "Glock States",
                                                        format_png= format_png)
        if (path_to_image_files):
            generate_graph_index_page(path_to_output_dir, path_to_image_files, "Glock Types")

def generate_graphs_by_glock_state(path_to_output_dir, snapshots, format_png=False):
    if (snapshots):
        path_to_image_files = []
        snapshot_date_time = []
        filesystem_name = snapshots[0].get_filesystem_name()
        # This is graphing the states for differnt glock states. X is time, Y is
        # one of 7 glock types.
        for gstate in glocktop_analyze.glocks_stats.GLOCK_STATES:
            glock_types_stats = {}
            for snapshot in snapshots:
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
                                                        "%s - %s" %(filesystem_name, gstate),
                                                        "Time of Snapshots", "Glock Types",
                                                        format_png=format_png)
        if (path_to_image_files):
            generate_graph_index_page(path_to_output_dir, path_to_image_files, "Glocks States")

def generate_graphs_glocks_holder_waiter(path_to_output_dir, glocks_holder_waiters_by_date, snapshots_date_time, format_png=False):
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

def generate_date_graphs(path_to_output_dir, x_axis, y_axis_map, title, x_axis_title, y_axis_title, format_png=False):
    gstyle = Style(
        # http://www.pygal.org/en/latest/documentation/custom_styles.html
        background='white',
        plot_background='rgba(0, 0, 255, 0.03)',
        foreground='rgba(0, 0, 0, 0.8)',
        foreground_light='rgba(0, 0, 0, 0.9)',
        foreground_dark='rgba(0, 0, 0, 0.7)',
        colors=('#5DA5DA', '#FAA43A','#60BD68', '#F17CB0', '#4D4D4D', '#B2912F','#B276B2', '#DECF3F', '#F15854')
    )
    #human_readable is what introduce the strange Y data labels.
    graph = pygal.DateY(x_label_rotation=20, title=title,
                        x_title=x_axis_title, y_title=y_axis_title,
                        legend_at_bottom=True, human_readable=False,
                        style=gstyle, show_minor_x_labels=True,
                        print_values=False)
    # include_x_axis=True)
    graph.x_label_format = "%Y-%m-%d %H:%M:%S"
    # Add the Y-axis to this graph for this glock type for this gfs2 filesystem.
    for key in y_axis_map.keys():
        tlist = list(zip(tuple(x_axis),
                         tuple(y_axis_map.get(key))))+[None,None]
        graph.add(key, tlist)
    path_to_image_files = []
    path_to_image_dir = os.path.join(path_to_output_dir, "graphs")
    if (mkdirs(path_to_image_dir)):
        png_format_rendered = False
        path_to_image_file = ""
        if (format_png):
            try:
                path_to_image_file = os.path.join(path_to_image_dir, "%s_stat.png" %(title.replace(" ", "_").lower()))
                message = "Writing graph to %s" %(path_to_image_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                graph.render_to_png(path_to_image_file)
                png_format_rendered = True
            except (ImportError, NameError):
                message = "Rendering the graph to png failed. The \"cairosvg\" package must be installed."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
                message = "The format svg will be used instead."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
        if (not png_format_rendered):
            path_to_image_file = os.path.join(path_to_image_dir, "%s_stat.svg" %(title.replace(" ", "_").lower()))
            message = "Writing graph to %s" %(path_to_image_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
            graph.render_to_file(path_to_image_file)
            png_format_rendered = True
        if (os.path.exists(path_to_image_file)):
            path_to_image_files.append(path_to_image_file)
    return path_to_image_files

def generate_bar_graphs(path_to_output_dir, x_axis, y_axis, title, x_axis_title, y_axis_title, format_png=False):
    gstyle = Style(
        # http://www.pygal.org/en/latest/documentation/custom_styles.html
        background='white',
        plot_background='rgba(0, 0, 255, 0.03)',
        foreground='rgba(0, 0, 0, 0.8)',
        foreground_light='rgba(0, 0, 0, 0.9)',
        foreground_dark='rgba(0, 0, 0, 0.7)',
        colors=('#5DA5DA', '#FAA43A','#60BD68', '#F17CB0', '#4D4D4D', '#B2912F','#B276B2', '#DECF3F', '#F15854')
    )
    bar_chart = pygal.Bar(x_label_rotation=20, title=title,
                           x_title=x_axis_title, y_title=y_axis_title,
                           legend_at_bottom=True, human_readable=True,
                           style=gstyle)
    bar_chart.x_labels = map(str, x_axis)
    index = 0
    for index in range(0, len(x_axis)):
        data = map(lambda x: None, [None] * len(x_axis))
        data[index] = y_axis[index]
        bar_chart.add(x_axis[index], data)

    path_to_image_files = []
    path_to_image_dir = os.path.join(path_to_output_dir, "graphs")
    if (mkdirs(path_to_image_dir)):
        png_format_rendered = False
        path_to_image_file = ""
        if (format_png):
            try:
                path_to_image_file = os.path.join(path_to_image_dir, "%s_stat.png" %(title.replace(" - ", "-").replace(" ", "_").lower()))
                message = "Writing graph to %s" %(path_to_image_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                bar_chart.render_to_png(path_to_image_file)
                png_format_rendered = True
            except (ImportError, NameError):
                message = "Rendering the graph to png failed. The \"cairosvg\" package must be installed."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
                message = "The format svg will be used instead."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
        if (not png_format_rendered):
            path_to_image_file = os.path.join(path_to_image_dir, "%s_stat.svg" %(title.replace(" - ", "-").replace(" ", "_").lower()))
            message = "Writing graph to %s" %(path_to_image_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
            bar_chart.render_to_file(path_to_image_file)
            png_format_rendered = True
        if (os.path.exists(path_to_image_file)):
            path_to_image_files.append(path_to_image_file)
    return path_to_image_files

def generate_graph_index_page(path_to_output_dir, path_to_graphs, title):
    # Generate html page that links all the images.
    html_header = "<html><head></head><body>\n"
    html_footer = "</body></html>"
    figure_code_pre_svg = "\t<figure> <embed type=\"image/svg+xml\" src=\""
    figure_code_pre_png = "\t<figure> <embed type=\"image/png\" src=\""
    figure_code_post = "\"/></figure><BR><HR><BR>\n"
    figure_code = ""
    for path_to_image_file in path_to_graphs:
        # Need code to check if png or svg.
        if (path_to_image_file.endswith("svg")):
            figure_code += figure_code_pre_svg
        elif (path_to_image_file.endswith("png")):
            figure_code += figure_code_pre_png
        figure_code += "graphs/%s%s" %(os.path.split(path_to_image_file)[1], figure_code_post)
    html_data = "%s%s%s" %(html_header, figure_code, html_footer)
    path_to_html_file = os.path.join(path_to_output_dir, "%s.html" %(title.replace(" - ", "-").replace(" ", "_").lower()))
    if (write_to_file(path_to_html_file, html_data, append_to_file=False, create_file=True)):
        message = "The html page containing the graphs was written to: %s" %(path_to_html_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
    else:
        message = "There was an error writing the html page containing the graphs to: %s" %(path_to_html_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
