#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script analyzes output generated by glocktop for GFS2 filesystems.

- How can I view glock contention on a GFS2 filesystem in real-time in a
  RHEL 5, 6, or 7 Resilient Storage cluster?
  https://access.redhat.com/articles/666533
- Source Code gfs2-utils.git - glocktop
  https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop

@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3


NEXT Features:
* Add remaining stat queries and stat tables like for pids, DLM.

TODO:
* NEED OPTION: Add ignore list items like ENDED, N/A from U lines see man page.
* NEED OPTION: To disable_call_trace so call trace not printed.
* Warning on high demote_seconds, high waiter count, high DLM traffic.

RFEs:
* Try creating charts for plotting like pygal to embed into web pages:
  http://www.pygal.org/en/latest/index.html or ggplot: http://ggplot.yhathq.com/
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

import glocktop_analyze
from glocktop_analyze.utilities import ColorizeConsoleText, get_data_from_file, tableize
from glocktop_analyze.gfs2_snapshot import GFS2Snapshot, DLMActivity
from glocktop_analyze.glock import Glock, GlockHolder, GlockObject
from glocktop_analyze.glocks_stats import GlocksStats, GlockStats
from glocktop_analyze.parsers.gfs2_snapshot import parse_gfs2_snapshot, process_gfs2_snapshot

# #####################################################################
# Global vars:
# #####################################################################
VERSION_NUMBER = "0.1-3"

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
    cmd_parser.add_option("-g", "--find_glock",
                          action="store",
                          dest="glock_inode",
                          help="a glock hexadecimal number to search for",
                          type="string",
                          metavar="0x<glock number>",
                          default="")
    cmd_parser.add_option("-G", "--find_glock_type",
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
        # Setup the logger and create config directory
        # #######################################################################
        # Create the logger
        logLevel = logging.INFO
        logger = logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME)
        logger.setLevel(logLevel)
        # Create a new status function and level.
        logging.STATUS = logging.INFO + 2
        logging.addLevelName(logging.STATUS, "STATUS")

        # Log to main system logger that script has started then close the
        # handler before the other handlers are created.
        sysLogHandler = logging.handlers.SysLogHandler(address = '/dev/log')
        logger.addHandler(sysLogHandler)
        logger.info("The script has started running.")
        logger.removeHandler(sysLogHandler)

        # Create a function for the STATUS_LEVEL since not defined by python. This
        # means you can call it like the other predefined message
        # functions. Example: logging.getLogger("loggerName").status(message)
        setattr(logger, "status", lambda *args: logger.log(logging.STATUS, *args))
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logLevel)
        stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(stream_handler)

        # #######################################################################
        # Set the logging levels.
        # #######################################################################
        if ((cmdline_opts.enableDebugLogging) and (not cmdline_opts.disableLoggingToConsole)):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).setLevel(logging.DEBUG)
            stream_handler.setLevel(logging.DEBUG)
            message = "Debugging has been enabled."
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
        if (cmdline_opts.disableLoggingToConsole):
            stream_handler.setLevel(logging.CRITICAL)


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
        summary = ""
        for snapshot in snapshots:
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
                summary += "%s\n%s\n" %(ColorizeConsoleText.red(str(snapshot)), current_summary)
        print summary

        # Print stats
        if (not cmdline_opts.disable_stats):
            #
            # MAYBE NEED a GLOCK STAT OBEJECT to hold: hostname, filesname, date, glock, holder/waiter count, pids, demote_time.
            # Stuff like keeping up with glock-filesystem might get tricky and eventually parsing of multiple glocktop on multiple nodes.

            # * pid -> glocks with that pid | count
            # * glock -> pids
            # * peak for highest number of holder/waiters for each glock

            # Build structure so that filesystem, glocks stats can be analyzed
            filesystem_count = {}
            glock_count = {}
            glock_high_demote_seconds = {}

            # In some instances the unique key will be
            # "filesystem_name-glock_type/glock_inode". For example:
            # gfs2payroll-4/42ff2. Then for printing the filesystem and glock
            # info could be parsed out.
            for snapshot in snapshots:
                filesystem_name = snapshot.get_filesystem_name()
                if (filesystem_count.has_key(filesystem_name)):
                    filesystem_count[filesystem_name]["end_time"] = str(snapshot.get_date_time())
                    filesystem_count[filesystem_name]["count"] = filesystem_count[filesystem_name].get("count") + 1
                else:
                    filesystem_count[filesystem_name] = {"name": filesystem_name, "count":1,
                                                         "start_time":str(snapshot.get_date_time()),
                                                         "end_time":str(snapshot.get_date_time())}
                for glock in snapshot.get_glocks():
                    glock_type_inode = "%s-%s/%s" %(filesystem_name, glock.get_type(), glock.get_inode())
                    if (glock_count.has_key(glock_type_inode)):
                        glock_count[glock_type_inode] = glock_count.get(glock_type_inode) + 1
                    else:
                        glock_count[glock_type_inode] = 1
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
            table = []
            for key in filesystem_count.keys():
                #date_time = filesystem_count.get(key).get_date_time()
                table.append([filesystem_count.get(key).get("name"), filesystem_count.get(key).get("count"),
                              filesystem_count.get(key).get("start_time"), filesystem_count.get(key).get("end_time")])
            ftable = tableize(table, ["Filesystem", "Snapshots", "Start Time", "End Time"])
            if (len(ftable) > 0):
                print ftable

            # Print glock stats
            table = []
            from operator import itemgetter
            for pair in sorted(glock_count.items(), key=itemgetter(1), reverse=True):
                if (pair[1] > 1):
                    table.append([pair[0].rsplit("-")[0], pair[0].rsplit("-")[1], pair[1]])
            ftable = tableize(table, ["Filesystem Name", "Glock Type/Glocks Inode", "Total Holder/Waiter Count"])
            if (len(ftable) > 0):
                print ftable

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

            print
            print "---------------------------------------------------------------------------------"
            print "                             Stats for glocks                                    "
            print "---------------------------------------------------------------------------------"
            for snapshot in snapshots:
                glocks_stats = snapshot.get_glocks_stats()
                if (not glocks_stats == None):
                    print "Glock stats at %s for filesystem: %s" %(snapshot.get_date_time(), ColorizeConsoleText.red(snapshot.get_filesystem_name()))
                    table = []
                    for glock_stats in glocks_stats.get_glock_stats():
                        table.append([glock_stats.get_state(), glock_stats.get_nondisk(),
                                      glock_stats.get_inode(), glock_stats.get_rgrp(),
                                      glock_stats.get_iopen(), glock_stats.get_flock(),
                                      glock_stats.get_quota(), glock_stats.get_journal(),
                                      glock_stats.get_total()])
                    header = ["Glock State","nondisk", "inode", "rgrp", "iopen", "flock", "quota", "journal", "total"]
                    ftable = tableize(table, header)
                    if (len(ftable) > 0):
                        print ftable
                    print

        # Debug charts
        class GlockStat():
            def __init__(self, filesystem_name, date_time, glock_state, glock_type, count):
                self.__filesystem_name = filesystem_name
                self.__date_time = date_time
                self.__glock_state = glock_state
                self.__glock_type = glock_type
                self.__count = count

            def get_filesystem_name(self):
                return self.__filesystem_name

            def get_date_time(self):
                return self.__date_time

            def get_state(self):
                return self.__glock_state

            def get_type(self):
                return self.__glock_type

            def get_count(self):
                return self.__count

        unlocked_inodes = {}
        for snapshot in snapshots:
                glocks_stats = snapshot.get_glocks_stats()
                if (not glocks_stats == None):
                    for glock_stats in glocks_stats.get_glock_stats():
                        if ("Unlocked" == glock_stats.get_state()):
                            if (not unlocked_inodes.has_key(snapshot.get_filesystem_name())):
                                unlocked_inodes[snapshot.get_filesystem_name()] = []
                            glock_stat = GlockStat(snapshot.get_filesystem_name(), snapshot.get_date_time(),
                                                   glock.get_state(), "inode", glock_stats.get_inode())
                            unlocked_inodes[snapshot.get_filesystem_name()].append(glock_stat)

        import pygal
        for filesystem_name in unlocked_inodes.keys():
            x = []
            y = []
            gstats = unlocked_inodes.get(filesystem_name)
            for stat in gstats:
                x.append(stat.get_date_time())
                y.append(int(stat.get_count()))
            # The x_label_rotation is how it is turned downward.
            graph=pygal.DateY(x_label_rotation=20)

            graph.add("%s unlocked inodes" %(filesystem_name),list(zip(tuple(x),tuple(y)))+[None,None])
            graph.render_to_file("/redhat/html/misc/pygal/%s.svg" %(filesystem_name))
            graph.render_to_png("/redhat/html/misc/pygal/%s.png" %(filesystem_name))

    except KeyboardInterrupt:
        print ""
        message =  "This script will exit since control-c was executed by end user."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
        sys.exit(1)
    # #######################################################################
    # Exit the application with zero exit code since we cleanly exited.
    # #######################################################################
    sys.exit()
