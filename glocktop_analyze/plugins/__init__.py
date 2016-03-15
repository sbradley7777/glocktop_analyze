#!/usr/bin/python
# Options for the charts and graphs are located in the followig file:
# /usr/lib/python2.7/site-packages/pygal/config.py

import os
import logging
from datetime import datetime

import glocktop_analyze
from glocktop_analyze.snapshot import Snapshot
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import LogWriter, mkdirs, write_to_file

try:
    import pygal
    from pygal.style import Style
except (ImportError, NameError):
    message = "Failed to import pygal. The python-pygal package needs to be installed."
    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)

# #######################################################################
# Classes
# #######################################################################
class Plugin(object):
    def __init__(self, name, description, snapshots, title, path_to_output_dir, options):
        # A list of snapshots of a particular filesystem.
        self.__name = name
        self.__description = description
        self.__snapshots = snapshots
        self.__title = title
        self.__path_to_output_dir = path_to_output_dir
        self.__warnings = {}

        self.__options = {}
        if hasattr(self, "OPTIONS"):
            # Populate the options with default value.
            for plugin_option in self.OPTIONS:
                self.__options[plugin_option[0]] = plugin_option[2]
            for option_name in options.keys():
                try:
                    option_name_split = option_name.rsplit(".", 1)
                    plugin_name = option_name_split[0]
                    plugin_option_name = option_name_split[1]
                    for plugin_option in self.OPTIONS:
                        if (plugin_name == self.get_name()):
                            if (plugin_option_name == plugin_option[0]):
                                default_option_value = self.__options[plugin_option_name]
                                if (isinstance(default_option_value, int) and
                                    options.get(option_name).isdigit()):
                                    self.__options[plugin_option_name] = int(options.get(option_name))
                                elif (isinstance(default_option_value, str)):
                                    self.__options[plugin_option_name] = options.get(option_name)
                                else:
                                    message = "Invalid value for option \"%s\" for plugin: %s." %(option_name,
                                                                                                  self.get_name())
                                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                except IndexError:
                    pass

    def get_name(self):
        return self.__name

    def get_description(self):
        return self.__description

    def get_snapshots(self):
        return self.__snapshots

    def get_title(self):
        return self.__title

    def get_path_to_output_dir(self):
        return self.__path_to_output_dir

    def get_option(self, option_name):
        if (self.__options.has_key(option_name)):
            return self.__options.get(option_name)
        return ""

    def get_hostname(self):
        if (self.__snapshots):
            return self.__snapshots[0].get_hostname()
        return ""

    def get_filesystem_name(self):
        if (self.__snapshots):
            return self.__snapshots[0].get_filesystem_name()
        return ""

    def add_warning(self, wtype, description):
        if (not self.__warnings.has_key(wtype)):
            self.__warnings[wtype] = []
        self.__warnings[wtype].append(description)

    def analyze(self):
        pass

    def get_warnings(self):
        return self.__warnings

    def console(self):
        pass

    def write(self, html_format=False):
        pass

    def graph(self, png_format=False):
        pass

# #######################################################################
# Functions
# #######################################################################
def generate_date_graphs(path_to_output_dir, x_axis, y_axis_map, title, x_axis_title, y_axis_title, png_format=False):
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
    if (mkdirs(path_to_output_dir)):
        png_format_rendered = False
        path_to_image_file = ""
        if (png_format):
            try:
                path_to_image_file = os.path.join(path_to_output_dir, "%s_stat.png" %(title.replace(" ", "_").lower()))
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
            path_to_image_file = os.path.join(path_to_output_dir, "%s_stat.svg" %(title.replace(" - ", "-").replace(" ", "_").lower()))
            message = "Writing graph to %s" %(path_to_image_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
            graph.render_to_file(path_to_image_file)
            png_format_rendered = True
        if (os.path.exists(path_to_image_file)):
            path_to_image_files.append(path_to_image_file)
    return path_to_image_files

def generate_bar_graphs(path_to_output_dir, x_axis, y_axis, title, x_axis_title, y_axis_title, png_format=False):
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
    if (mkdirs(path_to_output_dir)):
        png_format_rendered = False
        path_to_image_file = ""
        if (png_format):
            try:
                path_to_image_file = os.path.join(path_to_output_dir, "%s_stat.png" %(title.replace(" - ", "-").replace(" ", "_").lower()))
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
            path_to_image_file = os.path.join(path_to_output_dir, "%s_stat.svg" %(title.replace(" - ", "-").replace(" ", "_").lower()))
            message = "Writing graph to %s" %(path_to_image_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
            bar_chart.render_to_file(path_to_image_file)
            png_format_rendered = True
        if (os.path.exists(path_to_image_file)):
            path_to_image_files.append(path_to_image_file)
    return path_to_image_files
