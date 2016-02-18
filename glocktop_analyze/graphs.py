#!/usr/bin/python
import os
import logging

import glocktop_analyze
from glocktop_analyze.gfs2_snapshot import GFS2Snapshot
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.utilities import LogWriter, mkdirs, write_to_file

disable_graphing = False
try:
    import pygal
except ImportError:
    print "Failed to import pygal. The python-pygal package needs to be installed."
    disable_graphing = True
except NameError:
    print "Failed to import pygal. The python-pygal package needs to be installed."
    disable_graphing = True



# Try adding this attribute to pygal.DateY(style=style)
# Need to find out how to create a style
# gstyle = Style(
#    background='white',
#    plot_background='rgba(0, 0, 255, 0.03)',
#    foreground='rgba(0, 0, 0, 0.8)',
#    foreground_light='rgba(0, 0, 0, 0.9)',
#    foreground_dark='rgba(0, 0, 0, 0.7)',
#    colors=('#5DA5DA', '#FAA43A','#60BD68', '#F17CB0', '#4D4D4D', '#B2912F','#B276B2', '#DECF3F', '#F15854')
#)

# Find out why png does not display correctly.
# try:
# path_to_image_file = "/redhat/html/misc/pygal/%s-%s_stats.png" %(filesystem_name, gtype)
# message = "Generating the graph for \"%s\" for all the states for glock type \"%s\" to file: %s" %(filesystem_name, gtype, path_to_image_file)
# logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
#    graph.render_to_png(path_to_image_file)
# except ImportError:
#    message = "Rendering the graph to png failed. The \"cairosvg\" package must be installed."
#    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
# except NameError:
#    message = "Rendering the graph to png failed. The \"cairosvg\" package must be installed."
#    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
# Render to svg and tab the following below to under the except statement.


def generate_graphs_by_glock_type(snapshots, path_to_output_dir):
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
            path_to_image_files += generate_graphs(path_to_output_dir, snapshot_date_time, glock_states_stats,
                                                "%s - %s" %(filesystem_name, gtype), "Time of Snapshots", "Glock States")
        if (path_to_image_files):
            generate_graph_index_page(path_to_output_dir, path_to_image_files, "%s-glock_types-graphs" %(filesystem_name))

def generate_graphs_by_glock_state(snapshots, path_to_output_dir):
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
            path_to_image_files += generate_graphs(path_to_output_dir, snapshot_date_time, glock_types_stats,
                                                   "%s - %s" %(filesystem_name, gstate), "Time of Snapshots", "Glock Types")
        if (path_to_image_files):
            generate_graph_index_page(path_to_output_dir, path_to_image_files, "%s-glocks_states-graphs" %(filesystem_name))

def generate_graphs(path_to_output_dir, x_axis, y_axis_map, title, x_axis_title, y_axis_title, format_png=False):
    # Need code to try png format.
    # Need to put style example here.

    # Add the Y-axis to this graph for this glock type for this gfs2 filesystem.
    path_to_image_files = []
    graph = pygal.DateY(x_label_rotation=20, title=title,
                        x_title=x_axis_title, y_title=y_axis_title,
                        legend_at_bottom=True, human_readable=True)
    for key in y_axis_map.keys():
        graph.add(key, list(zip(tuple(x_axis ),
                                  tuple(y_axis_map.get(key))))+[None,None])
    path_to_image_dir = os.path.join(path_to_output_dir, "graphs")
    if (mkdirs(path_to_image_dir)):
        path_to_image_file = os.path.join(path_to_image_dir, "%s_stat.svg" %(title.replace(" ", "_")))
        message = "Writing graph to %s" %(path_to_image_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        graph.render_to_file(path_to_image_file)
        if (os.path.exists(path_to_image_file)):
            path_to_image_files.append(path_to_image_file)
    return path_to_image_files

def generate_graph_index_page(path_to_output_dir, path_to_graphs, graph_name):
    # Need code to check if png or svg.

    # Generate html page that links all the images.
    html_header = "<html><head></head><body>\n"
    html_footer = "</body></html>"
    figure_code_pre = "\t<figure> <embed type=\"image/svg+xml\" src=\""
    figure_code_post = "\"/></figure><BR><HR><BR>\n"
    figure_code = ""
    for path_to_image_file in path_to_graphs:
        figure_code += "%sgraphs/%s%s" %(figure_code_pre, os.path.split(path_to_image_file)[1], figure_code_post)
    html_data = "%s%s%s" %(html_header, figure_code, html_footer)
    path_to_html_file = os.path.join(path_to_output_dir, "%s.html" %(graph_name))
    write_to_file(path_to_html_file, html_data, append_to_file=False, create_file=True)
    message = "The html page containing the graphs was written to: %s" %(path_to_html_file)
    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
