#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script analyzes the output generated by glocktop for GFS2 filesystems.  The
output can be printed as html format and data can be graphed.

- How can I view glock contention on a GFS2 filesystem in real-time in a
  RHEL 5, 6, or 7 Resilient Storage cluster?
  https://access.redhat.com/articles/666533
- Source Code gfs2-utils.git - glocktop
  https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop

@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3

* For pretty formatted html then install the package "python-beautifulsoup4"
  otherwise there will be ugly html created.
"""
import sys
import logging
import logging.handlers
import os
import os.path
from optparse import OptionParser, Option, SUPPRESS_HELP

import glocktop_analyze
from glocktop_analyze.utilities import LogWriter
# Import logger that all files will use.
logger = LogWriter(glocktop_analyze.MAIN_LOGGER_NAME,
                   logging.INFO,
                   glocktop_analyze.MAIN_LOGGER_FORMAT,
                   disableConsoleLog=False)

from glocktop_analyze.utilities import ColorizeConsoleText, get_data_from_file, tableize, write_to_file
import glocktop_analyze.glocks_stats
from glocktop_analyze.snapshot import Snapshot, DLMActivity
from glocktop_analyze.glock import Glock, GlockHolder, GlockObject
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.parsers.snapshot import parse_snapshot, process_snapshot

from glocktop_analyze.plugins.glocks_stats import GSStats
from glocktop_analyze.plugins.snapshots import Snapshots
from glocktop_analyze.plugins.glocks_high_demote_seconds import GlocksHighDemoteSeconds
from glocktop_analyze.plugins.glocks_in_snapshots import GlocksInSnapshots
from glocktop_analyze.plugins.glocks_waiters_time import GlocksWaitersTime
from glocktop_analyze.plugins.pids import Pids

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
                         dest="disable_std_out",
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
    cmd_parser.add_option("-I", "--show_ended_process_and_tlocks",
                        action="store_true",
                         dest="show_ended_process_and_tlocks",
                         help="show all glocks for ended process and transaction locks",
                         default=False)
    try:
        import pkgutil
        if (not pkgutil.find_loader("pygal") == None):
            # If pygal is not installed then this option will not be found.
            cmd_parser.add_option("-G", "--disable_graphs",
                                  action="store_true",
                                  dest="disable_graphs",
                                  help="do not generate graphs of stats",
                                  default=False)
    except (ImportError, NameError):
        message = "Failed to find pygal. The python-pygal package needs to be installed."
        logging.getLogger(MAIN_LOGGER_NAME).error(message)

    """
    cmd_parser.add_option("-S", "--disable_stats",
                           action="store_true",
                           dest="disable_stats",
                           help="do not print stats",
                           default=False)
    cmd_parser.add_option("-C", "--disable_call_trace",
                           action="store_true",
                           dest="disable_call_trace",
                           help="do not print call traces for holder/waiters",
                           default=False)
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
    """
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
        if ((cmdline_opts.enableDebugLogging) and (not cmdline_opts.disable_std_out)):
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
        if (not cmdline_opts.minimum_waiter_count > 0):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("The minimum holder count for a glock (-m) must be a positive integer.")
            sys.exit(1)

        """
        if (not cmdline_opts.glock_type == None):
            if (not (0 < cmdline_opts.glock_type < 10)):
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error("The glock type (-G) must be an integer between 1 - 9.")
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
        """
        # #######################################################################
        # Run main
        # #######################################################################
        message ="The file will be analyzed: %s" %(cmdline_opts.path_to_src_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        # Get the data as a list of lines
        lines = get_data_from_file(cmdline_opts.path_to_src_file)

        #All the snapshots for all the filesystems.
        snapshots_by_filesystem = {}
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
                        process_snapshot(gfs2_snapshot, snapshot_lines)
                        if (not snapshots_by_filesystem.has_key(gfs2_snapshot.get_filesystem_name())):
                            snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()] = []
                        snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()].append(gfs2_snapshot)
                # Process the new snapshot
                gfs2_snapshot = parse_snapshot(line, cmdline_opts.show_ended_process_and_tlocks)
                snapshot_lines = []
            else:
                snapshot_lines.append(line)

        # The path to directory where all files written for this host will be
        # written.
        path_to_output_dir = cmdline_opts.path_to_output_dir
        # Process any remaining items
        if (not gfs2_snapshot == None):
            if ((not cmdline_opts.gfs2_filesystem_names) or
                (gfs2_snapshot.get_filesystem_name().strip() in cmdline_opts.gfs2_filesystem_names)):
                process_snapshot(gfs2_snapshot, snapshot_lines)
                if (not snapshots_by_filesystem.has_key(gfs2_snapshot.get_filesystem_name())):
                    snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()] = []
                snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()].append(gfs2_snapshot)
                # Set the path to output dir to include hostname in last item processed.
                path_to_output_dir = os.path.join(cmdline_opts.path_to_output_dir, gfs2_snapshot.get_hostname())
        message ="The analyzing of the file is complete."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

        # #######################################################################
        # Analyze the data
        # #######################################################################
        glocktop_summary_console = ""
        glocktop_summary_file = ""
        hostname = ""
        for filesystem_name in snapshots_by_filesystem.keys():
            snapshots = snapshots_by_filesystem.get(filesystem_name)
            for snapshot in snapshots:
                hostname = snapshot.get_hostname()
                current_summary = ""
                glocks = snapshot.get_glocks()
                for glock in glocks:
                    glock_holders = glock.get_holders()
                    if (len(glock_holders) >= cmdline_opts.minimum_waiter_count):
                        current_summary += "  %s\n" %(glock)
                        for holder in glock_holders:
                            current_summary += "     %s\n" %(holder)
                        if (not glock.get_glock_object() == None):
                            current_summary += "     %s\n" %(glock.get_glock_object())
                    if (current_summary):
                        glocktop_summary_console += "%s\n%s\n" %(ColorizeConsoleText.red(str(snapshot)), current_summary)
                        glocktop_summary_file += "%s\n%s\n" %(str(snapshot), current_summary)
            if (glocktop_summary_console and not cmdline_opts.disable_std_out):
                print "%s\n" %(glocktop_summary_console.rstrip())
            if (glocktop_summary_console):
                path_to_output_file = os.path.join(os.path.join(path_to_output_dir, filesystem_name), "glocks_activity.txt")
                if (not write_to_file(path_to_output_file, glocktop_summary_file,
                                      append_to_file=False, create_file=True)):
                    message = "An error occurred writing the glocktop summary file: %s" %(path_to_glocktop_summary_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)

        # #######################################################################
        # Gather, print, and graph stats
        # #######################################################################
        # svg does better charts. png support requires the python files:
        # lxml, cairosvg, tinycss, cssselect For now png support is disabled.
        enable_png_format=False

        # A function to merge dictionaries.
        def merge_dicts(dict_org, dict_to_merge):
            if (not dict_to_merge):
                return dict_org
            for key in dict_to_merge.keys():
                if (not dict_org.has_key(key) or dict_org == None):
                    dict_org[key] = []
                value_org = dict_org[key]
                value_merge = dict_to_merge[key]
                for value in value_merge:
                    if (not value in value_org):
                        value_org.append(value)
            return dict_org

        # Loop over all the filesystems and plugins.
        for filesystem_name in snapshots_by_filesystem.keys():
            # A container for all the warnings found on the filesystem.
            warnings = {}
            snapshots = snapshots_by_filesystem.get(filesystem_name)
            # See if way to make this work like a plugin instead of having to
            # import then run. Just run them all like sos. Attribute error is
            # thrown and silently caught if graphing is disabled because the
            # require packages are not installed. For now we hardcode
            # everything.
            plugins = [GSStats(snapshots, path_to_output_dir),
                       Snapshots(snapshots, path_to_output_dir),
                       GlocksHighDemoteSeconds(snapshots, path_to_output_dir),
                       GlocksInSnapshots(snapshots, path_to_output_dir),
                       Pids(snapshots, path_to_output_dir)]
            for plugin in plugins:
                plugin.analyze()
                plugin.write(html_format=True)
                if (not cmdline_opts.disable_std_out):
                    plugin.console()
                try:
                    if (not cmdline_opts.disable_graphs):
                        plugin.graph(enable_png_format)
                except AttributeError:
                    pass
                warnings =  merge_dicts(warnings, plugin.get_warnings())

            warnings_str = ""
            for wkey in warnings.keys():
            # Get the warnings that were found.
                warnings_str += "%s\n" %(wkey)
                for item in warnings.get(wkey):
                    warnings_str += "\t%s\n" %(item)
            if (warnings_str):
                path_to_output_file = os.path.join(os.path.join(path_to_output_dir,
                                                                filesystem_name),
                                                   "warnings.txt")
                if (not write_to_file(path_to_output_file, warnings_str, append_to_file=False, create_file=True)):
                    message = "An error occurred writing the file: %s" %(path_to_output_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

    except KeyboardInterrupt:
        print ""
        message =  "This script will exit since control-c was executed by end user."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
        sys.exit(1)
    # #######################################################################
    # Exit the application with zero exit code since we cleanly exited.
    # #######################################################################
    sys.exit()
