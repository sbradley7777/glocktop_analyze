#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This script analyzes output generated by glocktop for GFS2 filesystems.

- How can I view glock contention on a GFS2 filesystem in real-time in a
  RHEL 5, 6, or 7 Resilient Storage cluster?
  https://access.redhat.com/articles/666533
- Source Code gfs2-utils.git - glocktop
  https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop

@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3


NEXT TODO:
* Need to fix formatting of glocktop_glocks_stats.txt because has bash escapes
  still in it.
* Add remaining stat queries and stat tables like for pids, DLM.
* Create html pages for the summary, stats, everything instead of writing plain
  text to file.

Next TODO graphs:
* Need to figure out why glock_holder_waiters_count_over_time not plotting
 correctly and why not all y-axis is showing up.



* For graphs do not like how i am storing date/time and int in list for graphing.
* MAYBE NEED a GLOCK STAT OBEJECT to hold: hostname, filesname, date, glock,
 holder/waiter count, pids, demote_time.  Stuff like keeping up with
 glock-filesystem might get tricky and eventually parsing of multiple glocktop
 on multiple nodes.
* Create graphs for the following:
  - Top 10 glocks with waiters and graph the glocks waiter count over time.
  - pid -> glocks with that pid | count
  - glock -> pids
  - peak for highest number of holder/waiters for each glock


TODO Graphs
* Verify data in graph correct.

TODO:
* NEED OPTION: Add ignore list items like ENDED, N/A from U lines see man page.
* NEED OPTION: To disable_call_trace so call trace not printed.
* Warning on high demote_seconds, high waiter count, high DLM traffic.

RFEs:
* Could i combine the data into 1 file. Take 8 glocktops, then write to 1 file
  with everything sorted by date to see what is happenign on all nodes at around
  same time. Do not think a way to group cause started at different times and
  takes different times to print data.

"""
import sys
import logging
import logging.handlers
import os
import os.path
from optparse import OptionParser, Option, SUPPRESS_HELP
from operator import itemgetter

import glocktop_analyze
from glocktop_analyze.utilities import LogWriter
# Import logger that all files will use.
logger = LogWriter(glocktop_analyze.MAIN_LOGGER_NAME,
                   logging.INFO,
                   glocktop_analyze.MAIN_LOGGER_FORMAT,
                   disableConsoleLog=False)
from glocktop_analyze.utilities import ColorizeConsoleText, get_data_from_file, tableize, mkdirs, write_to_file
import glocktop_analyze.glocks_stats
from glocktop_analyze.gfs2_snapshot import GFS2Snapshot, DLMActivity
from glocktop_analyze.glock import Glock, GlockHolder, GlockObject
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.parsers.gfs2_snapshot import parse_gfs2_snapshot, process_gfs2_snapshot

from glocktop_analyze.graphs import generate_graphs_by_glock_type, generate_graphs_by_glock_state
from glocktop_analyze.graphs import generate_graphs_glocks_holder_waiter
from glocktop_analyze.graphs import generate_bar_graphs, generate_graph_index_page

# #####################################################################
# Global vars:
# #####################################################################
VERSION_NUMBER = "0.1-5"

# ##############################################################################
# Get user selected options
# ##############################################################################
def __get_options(version) :
    cmd_parser = OptionParserExtended(version)
    cmd_parser.add_option("-d", "--debug",
                         action="store_true",
                         dest="enableDebugLogging",
                         help="enables debug logging",
                         default=False)
    cmd_parser.add_option("-q", "--quiet",
                         action="store_true",
                         dest="disableLoggingToConsole",
                         help="disables logging to console",
                         default=False)
    cmd_parser.add_option("-y", "--no_ask",
                        action="store_true",
                         dest="disableQuestions",
                         help="disables all questions and assumes yes",
                         default=False)
    cmd_parser.add_option("-p", "--path_to_filename",
                         action="store",
                         dest="path_to_src_file",
                         help="the path to the filename that will be parsed",
                         type="string",
                         metavar="<input filename>",
                         default="")
    cmd_parser.add_option("-o", "--path_to_output_dir",
                         action="store",
                         dest="path_to_output_dir",
                         help="the path to the directory where any files generated will be outputted",
                         type="string",
                         metavar="<input filename>",
                          default="/tmp/%s" %(cmd_parser.get_command_name().split(".")[0]))
    cmd_parser.add_option("-m", "--minimum_waiter_count",
                          action="store",
                          dest="minimum_waiter_count",
                          help="the minimum number of waiters for a glock",
                          type="int",
                          metavar="<minimum waiter count>",
                          default=1)
    cmd_parser.add_option("-n", "--gfs2_filesystem_name",
                          action="extend",
                          dest="gfs2_filesystem_names",
                          help="only analyze a particular gfs2 filesystem",
                          type="string",
                          metavar="<gfs2 filesystem name>",
                          default=[])
    cmd_parser.add_option("-W", "--disable_show_waiters",
                          action="store_true",
                          dest="disable_show_waiters",
                          help="the waiters for the glocks are not displayed in the output",
                          default=False)
    cmd_parser.add_option("-S", "--disable_stats",
                          action="store_true",
                          dest="disable_stats",
                          help="do not print stats",
                          default=False)
    #cmd_parser.add_option("-C", "--disable_call_trace",
    #                      action="store_true",
    #                      dest="disable_call_trace",
    #                      help="do not print call traces for holder/waiters",
    #                      default=False)
    try:
        import pkgutil
        if (not pkgutil.find_loader('pygal') == None):
            # If pygal is not installed then this option will not be found.
            cmd_parser.add_option("-G", "--disable_graphs",
                                  action="store_true",
                                  dest="disable_graphs",
                                  help="do not generate graphs of stats",
                                  default=False)
    except (ImportError, NameError):
        message = "Failed to find pygal. The python-pygal package needs to be installed."
        logging.getLogger(MAIN_LOGGER_NAME).error(message)

    cmd_parser.add_option("-g", "--find_glock",
                          action="store",
                          dest="glock_inode",
                          help="a glock hexadecimal number to search for",
                          type="string",
                          metavar="0x<glock number>",
                          default="")
    cmd_parser.add_option("-t", "--find_glock_type",
                          action="store",
                          dest="glock_type",
                          help="a glock type to search for (requires glock number (-g))",
                          type="int",
                          metavar="<glock type>",
                          default=None)

 # Get the options and return the result.
    (cmdLine_opts, cmdLine_args) = cmd_parser.parse_args()
    return (cmdLine_opts, cmdLine_args)

# ##############################################################################
# OptParse classes for commandline options
# ##############################################################################
class OptionParserExtended(OptionParser):
    def __init__(self, version) :
        self.__command_name = os.path.basename(sys.argv[0])
        OptionParser.__init__(self, option_class=ExtendOption,
                              version="%s %s\n" %(self.__command_name, version),
                              description="%s \n"%(self.__command_name))

    def get_command_name(self):
        return self.__command_name
    def print_help(self):
        self.print_version()
        examples_message = "\n"
        OptionParser.print_help(self)
        #print examples_message

class ExtendOption (Option):
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if (action == "extend") :
            valueList = []
            try:
                for v in value.split(","):
                    # Need to add code for dealing with paths if there is option for paths.
                    newValue = value.strip().rstrip()
                    if (len(newValue) > 0):
                        valueList.append(newValue)
            except:
                pass
            else:
                values.ensure_value(dest, []).extend(valueList)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)

# ###############################################################################
# Main Function
# ###############################################################################
if __name__ == "__main__":
    try:
        # #######################################################################
        # Get the options from the commandline.
        # #######################################################################
        (cmdline_opts, cmdline_args) = __get_options(VERSION_NUMBER)

        # #######################################################################
        # Set the logging levels.
        # #######################################################################
        if ((cmdline_opts.enableDebugLogging) and (not cmdline_opts.disableLoggingToConsole)):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).setLevel(logging.DEBUG)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug("Debugging has been enabled.")
        # #######################################################################
        # Validate input
        # #######################################################################
        if (not cmdline_opts.path_to_src_file):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("A path to a file (-p) to be analyzed is required.")
            sys.exit(1)
        if (not os.path.exists(cmdline_opts.path_to_src_file)):
            message ="The file does not exist: %s" %(cmdline_opts.path_to_src_file)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            sys.exit(1)
        if (not cmdline_opts.glock_type == None):
            if (not (0 < cmdline_opts.glock_type < 10)):
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("The glock type (-G) must be an integer between 1 - 9.")
                sys.exit(1)
        if (not cmdline_opts.minimum_waiter_count > 0):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("The minimum holder count for a glock (-m) must be a positive integer.")
            sys.exit(1)

        glock_inode = ""
        if (cmdline_opts.glock_inode):
            try:
                if (cmdline_opts.glock_inode.startswith("0x")):
                    int("%s" %(cmdline_opts.glock_inode), 16)
                else:
                    int("0x%s" %(cmdline_opts.glock_inode), 16)
            except ValueError:
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("The glock number (-g) must be a hexadecimal number.")
                sys.exit(1)
            except TypeError:
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("The glock number (-g) must be a hexadecimal number.")
                sys.exit(1)

        # #######################################################################
        # Run main
        # #######################################################################
        message ="The file will be analyzed: %s" %(cmdline_opts.path_to_src_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        # Get the data as a list of lines
        lines = get_data_from_file(cmdline_opts.path_to_src_file)

        #All the snapshots for all the filesystems.
        snapshots = []
        # The glock that will have a container for all the lines associated with
        # the glock.
        gfs2_snapshot = None
        # The lines that are related to this snapshot of the
        # filesystem. Including glocks, waiters, etc.
        snapshot_lines = []
        for line in lines:
            # @, G, H, I, R, B, U, C, S
            if ((line.startswith("@")) or (not len(line) > 0)):
                if (not gfs2_snapshot == None):
                    # Process any previous snapshot lines before starting a
                    # new one. All the glocks, holder/waiters, etc.
                    if ((not cmdline_opts.gfs2_filesystem_names) or
                        (gfs2_snapshot.get_filesystem_name().strip() in cmdline_opts.gfs2_filesystem_names)):
                        process_gfs2_snapshot(gfs2_snapshot, snapshot_lines)
                        snapshots.append(gfs2_snapshot)
                # Process the new snapshot
                gfs2_snapshot = parse_gfs2_snapshot(line)
                snapshot_lines = []
            else:
                snapshot_lines.append(line)
        # Process any remaining items
        if (not gfs2_snapshot == None):
            if ((not cmdline_opts.gfs2_filesystem_names) or
                (gfs2_snapshot.get_filesystem_name().strip() in cmdline_opts.gfs2_filesystem_names)):
                process_gfs2_snapshot(gfs2_snapshot, snapshot_lines)
                snapshots.append(gfs2_snapshot)

        # #######################################################################
        # Analyze the data
        # #######################################################################
        # Print summary of data analyzed
        glocktop_summary_console = ""
        glocktop_summary_file = ""
        hostname = ""
        for snapshot in snapshots:
            hostname = snapshot.get_hostname()
            current_summary = ""
            glocks = []
            if (cmdline_opts.glock_inode):
                # Find particular glocks.
                glocks = snapshot.find_glock(cmdline_opts.glock_type, cmdline_opts.glock_inode.replace("0x", ""))
            else:
                glocks = snapshot.get_glocks()
            for glock in glocks:
                glock_holders = glock.get_holders()
                if (len(glock_holders) >= cmdline_opts.minimum_waiter_count):
                    current_summary += "  %s\n" %(glock)
                    if (not cmdline_opts.disable_show_waiters):
                        for holder in glock_holders:
                            current_summary += "    %s\n" %(holder)
                        if (not glock.get_glock_object() == None):
                            current_summary += "    %s\n" %(glock.get_glock_object())
            if (current_summary):
                glocktop_summary_console += "%s\n%s\n" %(ColorizeConsoleText.red(str(snapshot)), current_summary)
                glocktop_summary_file += "%s\n%s\n" %(str(snapshot), current_summary)

        print glocktop_summary_console
        # The path to directory where all files written for this host will be
        # written.
        path_to_output_dir = os.path.join(cmdline_opts.path_to_output_dir, hostname)
        if (mkdirs(path_to_output_dir)):
            path_to_glocktop_summary_file = os.path.join(path_to_output_dir, "glocktop_summary.txt")
            if (not write_to_file(path_to_glocktop_summary_file, glocktop_summary_file,
                                  append_to_file=False, create_file=True)):
                message = "An error occurred writing the glocktop summary file: %s" %(path_to_glocktop_summary_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)

        # #######################################################################
        # Gather, print, and graph  stats
        # #######################################################################
        if (not cmdline_opts.disable_stats):
            # Build structure so that filesystem, glocks stats can be analyzed

            # The number of snapshots taken for each filesystem.
            filesystem_count = {}
            # The number of times that a glock appear in a snapshot for a
            # filesystem.
            glocks_appeared_in_snapshots = {}
            # The value of demote_seconds if greater than zero for a glocks.
            glock_high_demote_seconds = {}
            # The number of holders and waiters including the time taken for
            # each snapshot it appeared in.
            glocks_holder_waiters_by_date = {}
            # In some instances the unique key will be
            # "filesystem_name-glock_type/glock_inode". For example:
            # gfs2payroll-4/42ff2. Then for printing the filesystem and glock
            # info could be parsed out.
            for snapshot in snapshots:
                filesystem_name = snapshot.get_filesystem_name()
                # Get filesystem stats
                if (filesystem_count.has_key(filesystem_name)):
                    filesystem_count[filesystem_name]["end_time"] = str(snapshot.get_date_time())
                    filesystem_count[filesystem_name]["count"] = filesystem_count[filesystem_name].get("count") + 1
                else:
                    filesystem_count[filesystem_name] = {"name": filesystem_name, "count":1,
                                                         "start_time":str(snapshot.get_date_time()),
                                                         "end_time":str(snapshot.get_date_time())}
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
                    demote_time = int(glock.get_demote_time())
                    if (demote_time > 0):
                        if (glock_high_demote_seconds.has_key(glock_type_inode)):
                            c_demote_time = glock_high_demote_seconds.get(glock_type_inode)
                            c_demote_time += " %d" %(demote_time)
                            glock_high_demote_seconds[glock_type_inode] = c_demote_time
                        else:
                            glock_high_demote_seconds[glock_type_inode] = "%s" %(demote_time)

            print
            print "---------------------------------------------------------------------------------"
            print "                             Stats for glocktop                                  "
            print "---------------------------------------------------------------------------------"
            # Print filesystem stats
            path_to_glocktop_stats_file = os.path.join(path_to_output_dir, "glocktop_stats.txt")
            table = []
            for key in filesystem_count.keys():
                #date_time = filesystem_count.get(key).get_date_time()
                table.append([filesystem_count.get(key).get("name"), filesystem_count.get(key).get("count"),
                              filesystem_count.get(key).get("start_time"), filesystem_count.get(key).get("end_time")])
            ftable = tableize(table, ["Filesystem", "Snapshots", "Start Time", "End Time"])
            if (len(ftable) > 0):
                print ftable
            ftable = tableize(table, ["Filesystem", "Snapshots", "Start Time", "End Time"], colorize=False)
            if (len(ftable) > 0):
                if (not write_to_file(path_to_glocktop_stats_file, "%s \n" %(ftable),
                                      append_to_file=False, create_file=True)):
                    message = "An error occurred writing the glocktop stats file: %s" %(path_to_glocktop_stats_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

            # Print glock stats
            table = []
            for pair in sorted(glocks_appeared_in_snapshots.items(), key=itemgetter(1), reverse=True):
                # Only include if there is more than one waiter.
                if (pair[1] > 1):
                    table.append([pair[0].rsplit("-")[0], pair[0].rsplit("-")[1], pair[1]])
            ftable = tableize(table, ["Filesystem Name", "Glock Type/Glocks Inode", "Found in snapshot"])
            if (len(ftable) > 0):
                print ftable
            ftable = tableize(table, ["Filesystem Name", "Glock Type/Glocks Inode", "Found in snapshots"], colorize=False)
            if (len(ftable) > 0):
                if (not write_to_file(path_to_glocktop_stats_file, "%s \n" %(ftable),
                                      append_to_file=True, create_file=True)):
                    message = "An error occurred writing the glocktop stats file: %s" %(path_to_glocktop_stats_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

            # Glock + filesystem with high demote seconds.
            table = []
            for key in glock_high_demote_seconds.keys():
                demote_seconds = glock_high_demote_seconds.get(key).split()
                index = 0
                current_fs_name = key.rsplit("-")[0]
                current_glock =  key.rsplit("-")[1]
                current_demo_seconds = ""
                for index in range(0, len(demote_seconds)):
                    if (((index % 7) == 0) and (not index == 0)):
                        table.append([current_fs_name, current_glock, current_demo_seconds.strip()])
                        current_fs_name = "-"
                        current_glock = "-"
                        current_demo_seconds = demote_seconds[index]
                    else:
                        current_demo_seconds += " %s" %(demote_seconds[index])

            ftable = tableize(table, ["Filesystem Name","Glock Type/Glocks Inode", "High Demote Seconds That Occurred (in ms)"])
            if (len(ftable) > 0):
                print ftable
            ftable = tableize(table, ["Filesystem Name","Glock Type/Glocks Inode", "High Demote Seconds That Occurred (in ms)"], colorize=False)
            if (len(ftable) > 0):
                if (not write_to_file(path_to_glocktop_stats_file, "%s \n" %(ftable),
                                      append_to_file=True, create_file=True)):
                    message = "An error occurred writing the glocktop stats file: %s" %(path_to_glocktop_stats_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

            print
            print "---------------------------------------------------------------------------------"
            print "                             Stats for glocks                                    "
            print "---------------------------------------------------------------------------------"
            summary_glock_stats = ""
            for snapshot in snapshots:
                glocks_stats = snapshot.get_glocks_stats()
                if (not glocks_stats == None):
                    summary_glock_stats += "\n%s\n" %(str(glocks_stats))
            if (summary_glock_stats):
                print summary_glock_stats
                path_to_glocktop_glocks_stats_file = os.path.join(path_to_output_dir, "glocktop_glocks_stats.txt")
                if (not write_to_file(path_to_glocktop_glocks_stats_file, summary_glock_stats,
                                      append_to_file=True, create_file=True)):
                    message = "An error occurred writing the glocktop stats file: %s" %(path_to_glocktop_stats_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        try:
            if (not cmdline_opts.disable_graphs):
                # Graph the glocks stats.
                message = "The graphs for the glocks stats will be generated."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                # Sort all the snapshots into filesystem bins.
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
                                                  format_png=False)
                for filesystem_name in snapshots_by_filesystem:
                    generate_graphs_by_glock_state(os.path.join(path_to_output_dir, filesystem_name),
                                                   snapshots_by_filesystem.get(filesystem_name),
                                                   format_png=False)

                # A graph for the number of times a glock showed up in snapshots.
                message = "The graphs for the times a glock showed up in snapshot of the filesystem."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
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
                path_to_graphs = []
                for filesystem_name in glocks_in_snapshots.keys():
                    path_to_graphs = generate_bar_graphs(os.path.join(path_to_output_dir, filesystem_name),
                                                          glocks_in_snapshots.get(filesystem_name)[0],
                                                          glocks_in_snapshots.get(filesystem_name)[1],
                                                          "%s - Glock was in Snapshots" %(filesystem_name),
                                                          "glocks", "waiter count", format_png=False)
                    generate_graph_index_page(os.path.join(path_to_output_dir, filesystem_name),
                                              path_to_graphs, "Glock in Snapshots")

                # Graph the glocks number of holders and waiters over time.
                # Get the date/time of all the snapshots for each filesystems.
                filesystem_snapshot_dt = {}
                for snapshot in snapshots:
                    filesystem_name = snapshot.get_filesystem_name()
                    # Get filesystem stats
                    if (filesystem_snapshot_dt.has_key(filesystem_name)):
                        filesystem_snapshot_dt[filesystem_name].append(snapshot.get_date_time())
                    else:
                        filesystem_snapshot_dt[filesystem_name] = [snapshot.get_date_time()]

                for filesystem_name in glocks_in_snapshots.keys():
                    glocks_holder_waiters_counter = {}
                    for gkey in glocks_holder_waiters_by_date.keys():
                        hw_count = 0
                        if (gkey.startswith(filesystem_name)):
                            for gtuple in glocks_holder_waiters_by_date.get(gkey):
                                hw_count += gtuple[1]
                        if (hw_count > 1):
                            glocks_holder_waiters_counter[gkey] = hw_count
                    # Should i just get the top 10 or hightest counts on the glocks.
                    # Sort the items
                    #for pair in sorted(glocks_holder_waiters_count.items(), key=itemgetter(1), reverse=True):
                    #    print "%s: %d" %(pair[0], pair[1])
                    glocks_to_graph = {key.rsplit("-")[1]: glocks_holder_waiters_by_date[key] for key in glocks_holder_waiters_by_date if key in glocks_holder_waiters_counter.keys()}
                    generate_graphs_glocks_holder_waiter(os.path.join(path_to_output_dir, filesystem_name),
                                                         glocks_to_graph,
                                                         filesystem_snapshot_dt[filesystem_name], format_png=False)

                message = "The graphs were to the directory: %s" %(path_to_output_dir)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
        except AttributeError:
            # Graphing must be disabled since option does not exists.
            pass

    except KeyboardInterrupt:
        print ""
        message =  "This script will exit since control-c was executed by end user."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
        sys.exit(1)
    # #######################################################################
    # Exit the application with zero exit code since we cleanly exited.
    # #######################################################################
    sys.exit()
