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
        # A list of snapshots of a particular filesystem.
        self.__snapshots = snapshots
        self.__title = title

    def get_snapshots(self):
        return self.__snapshots

    def get_title(self):
        return self.__title

    def get_filesystem_name(self):
        if (self.__snapshots):
            return self.__snapshots[0].get_filesystem_name()
        return ""

    def analayze(self):
        pass

    def console(self):
        pass

    def write(self, path_to_output_dir):
        pass

    def graph(self, path_to_output_dir, enable_png_format):
        pass

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
