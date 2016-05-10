#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The utility glocktop_analyze.py analyzes the output generated by glocktop
monitoring a GFS2 filesystems. The output is printed to console or to html
format which can include graphs.

- How can I view glock contention on a GFS2 filesystem in real-time in a
  RHEL 5, 6, or 7 Resilient Storage cluster?
  https://access.redhat.com/articles/666533
- Source Code gfs2-utils.git - glocktop
  https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop

@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3

Requirements:
* For pretty formatted html then install the package "python-beautifulsoup4"
  otherwise there will be ugly html created.
* For graph support they package: pygal is required.
* png support will require the following packages but is currently disabled:
  lxml, cairosvg, tinycss, cssselect

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

from glocktop_analyze.utilities import ColorizeConsoleText, get_data_from_file
from glocktop_analyze.utilities import tableize, write_to_file, merge_dicts
import glocktop_analyze.glocks_stats
from glocktop_analyze.snapshot import Snapshot, DLMActivity
from glocktop_analyze.glock import Glock, GlockHolder, GlockObject
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
from glocktop_analyze.parsers.snapshot import parse_snapshot, process_snapshot
from glocktop_analyze.parsers.rawfile import get_hostname, get_filesystems
from glocktop_analyze.html import generate_header, generate_footer

# Plugins
from glocktop_analyze.plugins.glocks_activity import GlocksActivity
from glocktop_analyze.plugins.glocks_stats import GSStats
from glocktop_analyze.plugins.snapshots import Snapshots
from glocktop_analyze.plugins.glocks_high_demote_seconds import GlocksHighDemoteSeconds
from glocktop_analyze.plugins.glocks_in_snapshots import GlocksInSnapshots
from glocktop_analyze.plugins.glocks_waiters_time import GlocksWaitersTime
from glocktop_analyze.plugins.pids import Pids
from glocktop_analyze.plugins.glocks_dependencies import GlocksDependencies

# Plugins that can run on multiply nodes
from glocktop_analyze.plugins.snapshots_multinode import SnapshotsMultiplyNodes

# #####################################################################
# Global variables
# #####################################################################
VERSION_NUMBER = "0.1-7"

# #####################################################################
# Global functions
# #####################################################################
def __output_warnings(warnings, path_to_output_dir, disable_std_out=True, html_format=False):
    if (warnings):
        if (not disable_std_out):
            warnings_str = ""
            for wkey in warnings.keys():
                warnings_str += "%s\n" %(ColorizeConsoleText.red(wkey))
                for item in warnings.get(wkey):
                    warnings_str += "  - %s\n" %(item)
            print ColorizeConsoleText.red("Warnings Found:\n") +  warnings_str
        wdata = ""
        path_to_output_file = ""
        if (not html_format):
            path_to_output_file = os.path.join(path_to_output_dir, "warnings.txt")
            for wkey in warnings.keys():
                wdata += "%s\n" %(wkey)
                for item in warnings.get(wkey):
                    wdata += "  - %s\n" %(item)
            wdata = "Warnings Found:\n" +  wdata
        else:
            path_to_output_file = os.path.join(path_to_output_dir, "warnings.html")
            bdata = ""
            for wkey in warnings.keys():
                # Get the warnings that were found.
                bdata += "<b>%s</b><BR/>" %(wkey)
                for item in warnings.get(wkey):
                    bdata += "&nbsp;&nbsp;&nbsp;%s<BR/>" %(item)
            if (bdata):
                title = "<center><h3>Warnings Found on Filesystems</h3></center>"
                wdata = "%s\n%s\n%s\n<BR/><HR/><BR/>%s" %(generate_header(), title, bdata, generate_footer())

        if (wdata):
            if (not write_to_file(path_to_output_file, wdata, append_to_file=False, create_file=True)):
                message = "An error occurred writing the file: %s" %(path_to_output_file)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

# #####################################################################
# Functions that analyze the files for data
# #####################################################################
def __analyze_file(path_to_output_file, gfs2_filesystem_names, show_ended_process_and_tlocks):
    #All the snapshots for all the filesystems.
    snapshots_by_filesystem = {}
    # The glock that will have a container for all the lines associated with
    # the glock.
    gfs2_snapshot = None
    # The lines that are related to this snapshot of the
    # filesystem. Including glocks, waiters, etc.
    snapshot_lines = []
    lines = get_data_from_file(path_to_filename)
    for line in lines:
        # @, G, H, I, R, B, U, C, S
        if ((line.startswith("@")) or (not len(line) > 0)):
            if (not gfs2_snapshot == None):
                # Process any previous snapshot lines before starting a
                # new one. All the glocks, holder/waiters, etc.
                if ((not gfs2_filesystem_names) or
                    (gfs2_snapshot.get_filesystem_name().strip() in gfs2_filesystem_names)):
                    process_snapshot(gfs2_snapshot, snapshot_lines)
                    if (not snapshots_by_filesystem.has_key(gfs2_snapshot.get_filesystem_name())):
                        snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()] = []
                    snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()].append(gfs2_snapshot)
            # Process the new snapshot
            gfs2_snapshot = parse_snapshot(line, show_ended_process_and_tlocks)
            snapshot_lines = []
        else:
            snapshot_lines.append(line)
    # Process any remaining items
    if (not gfs2_snapshot == None):
        if ((not gfs2_filesystem_names) or
            (gfs2_snapshot.get_filesystem_name().strip() in gfs2_filesystem_names)):
            process_snapshot(gfs2_snapshot, snapshot_lines)
            if (not snapshots_by_filesystem.has_key(gfs2_snapshot.get_filesystem_name())):
                snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()] = []
            snapshots_by_filesystem[gfs2_snapshot.get_filesystem_name()].append(gfs2_snapshot)
    return snapshots_by_filesystem

# ##############################################################################
# Plugins
# ##############################################################################
def __get_plugins_class_names(is_multi_node_supported=False):
    if (is_multi_node_supported):
        return ["SnapshotsMultiplyNodes"]
    else:
        return ["GlocksActivity",
                "GSStats",
                "Snapshots",
                "GlocksHighDemoteSeconds",
                "GlocksInSnapshots",
                "GlocksWaitersTime",
                "Pids",
                "GlocksDependencies"]

def __get_plugins(snapshots, path_to_output_dir, options, enabled_plugins, is_multi_node_supported=False):
    classes = __get_plugins_class_names(is_multi_node_supported)
    plugins = []
    for plugin_class_name in classes:
        plugin = eval(plugin_class_name)(snapshots, path_to_output_dir, options)
        if ((plugin.get_name() in enabled_plugins) or (not enabled_plugins)):
            plugins.append(plugin)
    return plugins

def __plugins_run(snapshots, path_to_output_dir,
                  enable_html_format, enable_png_format, enable_graphs,
                  enabled_plugins, is_multi_node_supported=False):
    warnings = {}
    plugins = __get_plugins(snapshots, path_to_output_dir, options,
                            enabled_plugins, is_multi_node_supported)
    for plugin in plugins:
        plugin.analyze()
        plugin.write(html_format=enable_html_format)
        if (not cmdline_opts.disable_std_out):
            plugin.console()
        if (enable_graphs):
            plugin.graph(enable_png_format)
        warnings = merge_dicts(warnings, plugin.get_warnings())
    return warnings

def __print_plugins_description():
    plugins =  __get_plugins([], "", {}, [], False)
    plugins += __get_plugins([], "", {}, [], True)
    plugins_str = ""
    for plugin in plugins:
        plugins_str += "  %s: %s\n" %(ColorizeConsoleText.red(plugin.get_name()), plugin.get_description())
    if (plugins_str):
        print "The plugins installed are:"
        print plugins_str.rstrip()
    else:
        message = "There was no plugins found."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
        sys.exit()
    options_str = ""
    for plugin in plugins:
        if (hasattr(plugin, "OPTIONS")):
            for option in plugin.OPTIONS:
                option_name = "  %s.%s" %(plugin.get_name(), option[0])
                options_str += "%s: %s (Default=%s)\n" %(ColorizeConsoleText.red(option_name),
                                                         option[1], str(option[2]))
    if (options_str):
        print "\nThe plugin options that can be configured are:"
        print options_str.rstrip()

# ##############################################################################
# Get user selected options and plugin options
# ##############################################################################
def __has_enabled_plugins(plugins_to_enable, is_multi_node_supported=False):
    # If 1 plugin is found to be enabled then return True, else False. An empty
    # plugins_to_enable means all plugins can be enabled.
    if (not len(plugins_to_enable)):
        return True
    else:
        plugins =  __get_plugins([], "", {}, [], False)
        if (is_multi_node_supported):
            plugins = __get_plugins([], "", {}, [], True)
        for plugin_name in plugins_to_enable:
             for plugin in plugins:
                 if (plugin_name.lower() == plugin.get_name().lower()):
                    return True
    return False

def __get_plugin_options(user_options):
    plugins =  __get_plugins([], "", {}, [], False)
    plugins += __get_plugins([], "", {}, [], True)
    options = {}
    for option in user_options:
        option_split = option.rsplit("=", 1)
        found_plugin_option = False
        if (len(option_split) == 2):
            full_option_name = option_split[0].rsplit(".", 1)
            if (len(full_option_name) == 2):
                plugin_name = full_option_name[0]
                plugin_option_name = full_option_name[1]
                for plugin in plugins:
                    if (found_plugin_option):
                        break
                    elif (plugin_name == plugin.get_name()):
                        if (hasattr(plugin, "OPTIONS")):
                            for plugin_option in plugin.OPTIONS:
                                if (plugin_option_name == plugin_option[0]):
                                    found_plugin_option = True
                                    options[option_split[0]] = option_split[1]
                                    break
        if (not found_plugin_option):
            message = "The option \"%s\" is not a valid option." %(option)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
    return options

def __get_cmdline_options(cmd_parser) :
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
    cmd_parser.add_option("-l", "--show_plugins_list",
                          action="store_true",
                          dest="show_plugins_list",
                          help="show all available plugins and plugin options",
                          default=False)
    cmd_parser.add_option("-p", "--path_to_filename",
                          action="extend",
                          dest="path_to_src_file",
                          help="the path to the filename that will be parsed or directory containing glocktop files",
                          type="string",
                          metavar="<input filename>",
                          default=[])
    cmd_parser.add_option("-o", "--path_to_output_dir",
                          action="store",
                          dest="path_to_output_dir",
                          help="the path to the directory where any files generated will be outputted",
                          type="string",
                          metavar="<input filename>",
                          default="/tmp/%s" %(cmd_parser.get_command_name().split(".")[0]))
    cmd_parser.add_option("-n", "--gfs2_filesystem_name",
                          action="extend",
                          dest="gfs2_filesystem_names",
                          help="only analyze a particular gfs2 filesystem",
                          type="string",
                          metavar="<gfs2 filesystem name>",
                          default=[])
    cmd_parser.add_option("-e", "--enable_only",
                          action="extend",
                          dest="plugins_only_to_enable",
                          help="plugins to only enable and run against the data",
                          type="string",
                          metavar="<plugin name>",
                          default=[])
    cmd_parser.add_option("-k", "--plugins_option",
                          action="extend",
                          dest="plugins_options",
                          help="a plugins option and value.",
                          type="string",
                          metavar="<option_name=value>",
                          default=[])
    cmd_parser.add_option("-A", "--disable_group_analysis",
                          action="store_false",
                          dest="enable_group_analysis",
                          help="disable group filesystem analysis of all files found",
                          default=True)
    cmd_parser.add_option("-I", "--show_ended_process_and_tlocks",
                          action="store_true",
                          dest="show_ended_process_and_tlocks",
                          help="show all glocks for ended process and transaction locks",
                          default=False)
    cmd_parser.add_option("-T", "--disable_html_format",
                          action="store_false",
                          dest="enable_html_format",
                          help="disable outputting to html format (and disable graphs)",
                          default=True)
    try:
        import pkgutil
        if (not pkgutil.find_loader("pygal") == None):
            # If pygal is not installed then this option will not be found.
            cmd_parser.add_option("-G", "--disable_graphs",
                                  action="store_false",
                                  dest="enable_graphs",
                                  help="do not generate graphs of stats",
                                  default=True)
    except (ImportError, NameError):
        message = "Failed to find pygal. The python-pygal package needs to be installed."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)

    (cmdLine_opts, cmdLine_args) = cmd_parser.parse_args()
    return (cmdLine_opts, cmdLine_args)

# ##############################################################################
# OptParse classes for commandline options
# ##############################################################################
class OptionParserExtended(OptionParser):
    def __init__(self, version) :
        self.__command_name = os.path.basename(sys.argv[0])
        description =  "This script analyzes the output generated by glocktop monitoring a  GFS2 filesystems. "
        description += "The output is printed to console or to html format which can include graphs."

        OptionParser.__init__(self, option_class=ExtendOption,
                              version="%s %s\n" %(self.__command_name, version),
                              description="%s \n"%(description))

    def get_command_name(self):
        return self.__command_name

    def print_help(self):
        self.print_version()
        examples_message = "\n\n"
        OptionParser.print_help(self)

        examples_message += "Analyze a directory containing glocktop files and output to a directory.\n"
        examples_message += "# %s -p /tmp/glocktop_files/ -o /var/www/html/glocktop_data \n\n" %(self.get_command_name())
        examples_message += "Analyze a single file and configure some of the plugins options.\n"
        examples_message += "# %s -p /tmp/glocktop_files/glocktop.node1 " %(self.get_command_name())
        examples_message += "-k glocks_activity.mininum_waiter_count=7 -k glocks_in_snapshots.mininum_glocks_in_snapshots=11\n\n"
        examples_message += "Analyze a single file and disable html format and show ended processes.\n"
        examples_message += "# %s -p /tmp/glocktop_files/glocktop.node1 -E -I\n\n" %(self.get_command_name())
        examples_message += "Analyze a particular filesystem only.\n"
        examples_message += "# %s -p /tmp/glocktop_files/glocktop.node1 -n mygfs2fs\n\n" %(self.get_command_name())
        print examples_message

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
        cmd_parser = OptionParserExtended(VERSION_NUMBER)
        (cmdline_opts, cmdline_args) = __get_cmdline_options(cmd_parser)

        # #######################################################################
        # Set the logging levels.
        # #######################################################################
        if ((cmdline_opts.enableDebugLogging) and (not cmdline_opts.disable_std_out)):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).setLevel(logging.DEBUG)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug("Debugging has been enabled.")

        # List all the plugins found and their corresponding options.
        if (cmdline_opts.show_plugins_list):
            cmd_parser.print_version()
            __print_plugins_description()
            sys.exit()

        # #######################################################################
        # Get the listing of all the files that will be processed.
        # #######################################################################
        def is_valid_glocktop_file(path_to_filename):
            try:
                fin = open(path_to_filename)
                for line in fin.readlines()[0:10]:
                    if (line.startswith("@")):
                        if (not parse_snapshot(line) == None):
                            return True
            except (UnicodeEncodeError, IOError):
                return False
            return False

        path_to_filenames = []
        for filename in cmdline_opts.path_to_src_file:
            if (os.path.isfile(filename)):
                if (is_valid_glocktop_file(filename)):
                    path_to_filenames.append(filename)
            elif (os.path.isdir(filename)):
                for item in os.listdir(filename):
                    path_to_filename = os.path.join(filename, item)
                    if (is_valid_glocktop_file(path_to_filename)):
                        path_to_filenames.append(path_to_filename)
                    else:
                        message = "The file does not appear to contain data generated by glocktop: %s" %(path_to_filename)
                        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).warning(message)

        if (not path_to_filenames):
            message = "There was no valid glocktop outputted files found."
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            message = "A path to file or directory with the \"-p\" option that contains file(s) generated by glocktop is required."
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
            sys.exit(1)

        # #######################################################################
        # Get the values for the plugin options
        # #######################################################################
        enable_html_format = cmdline_opts.enable_html_format
        # svg does better charts than png
        enable_png_format = False
        enable_graphs = False
        try:
            # If attribute does not exist because required library not installed
            # then siliently catch the exception.
            enable_graphs = cmdline_opts.enable_graphs and enable_html_format
        except AttributeError:
            pass

        options = __get_plugin_options(cmdline_opts.plugins_options)

        # #######################################################################
        # Analyze the data if there are non-grouped plugins enabled
        # #######################################################################
        if (__has_enabled_plugins(cmdline_opts.plugins_only_to_enable, False)):
            for path_to_filename in path_to_filenames:
                message ="The file will be analyzed: %s" %(path_to_filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                snapshots_by_filesystem = __analyze_file(path_to_filename,
                                                         cmdline_opts.gfs2_filesystem_names,
                                                         cmdline_opts.show_ended_process_and_tlocks)
                # Set the path to output dir.
                path_to_output_dir = ""
                if (snapshots_by_filesystem.keys()):
                    hostname = snapshots_by_filesystem[snapshots_by_filesystem.keys()[0]][0].get_hostname()
                    path_to_output_dir = os.path.join(cmdline_opts.path_to_output_dir, hostname)
                message ="The analyzing of the file is complete."
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)

                # Loop over all the filesystems and plugins and save the warnings.
                for filesystem_name in snapshots_by_filesystem.keys():
                    snapshots = snapshots_by_filesystem.get(filesystem_name)
                    # All the warnings found on the filesystem after plugins have ran.
                    warnings = __plugins_run(snapshots, path_to_output_dir,
                                             enable_html_format, enable_png_format,
                                             enable_graphs,
                                             cmdline_opts.plugins_only_to_enable)
                    #__output_warnings(warnings, path_to_output_dir,
                    #                  disable_std_out=cmdline_opts.disable_std_out,
                    #                  html_format=enable_html_format)

        # #######################################################################
        # Analyze the data if there are grouped plugins enabled
        # #######################################################################
        if (cmdline_opts.enable_group_analysis and __has_enabled_plugins(cmdline_opts.plugins_only_to_enable, True)):
            # Map the hostname-filesystem -> file
            filenames_for_hosts = {}
            # Map the hostname -> filesystems found on the hostname
            hosts_filesystems = {}
            # Map the filesystem -> list of hostnames where that filesystem found.
            filesystems_on_hosts={}
            for path_to_filename in path_to_filenames:
                chostname = get_hostname(path_to_filename)
                cfilesystems = get_filesystems(path_to_filename,
                                                cmdline_opts.gfs2_filesystem_names)
                if (cfilesystems):
                    filenames_for_hosts[chostname] = path_to_filename
                    for filesystem in cfilesystems:
                        if (not filesystems_on_hosts.has_key(filesystem)):
                            filesystems_on_hosts[filesystem] = []
                        filesystems_on_hosts[filesystem].append(chostname)
                        if (not hosts_filesystems.has_key(chostname)):
                            hosts_filesystems[chostname] = []
                        hosts_filesystems[chostname].append(filesystem)

                        fs_host_key = "%s-%s" %(chostname, filesystem)
                        if (not filenames_for_hosts.has_key(fs_host_key)):
                            filenames_for_hosts[fs_host_key] = []
                        filenames_for_hosts[fs_host_key] = path_to_filename
            if (filenames_for_hosts.keys()):
                # output directory is multiple_node/<filesystem_name>
                for filesystem in filesystems_on_hosts.keys():
                    snapshots_by_filesystem = []
                    warnings = {}
                    for chostname in filesystems_on_hosts.get(filesystem):
                        fs_host_key = "%s-%s" %(chostname, filesystem)
                        path_to_filename = filenames_for_hosts.get(fs_host_key)
                        if (not cmdline_opts.gfs2_filesystem_names or filesystem in cmdline_opts.gfs2_filesystem_names):
                            message = "The file will be analyzed for filesystem \"%s\" for " %(filesystem)
                            message += "host \"%s\": %s" %(chostname, path_to_filename)
                            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                            current_snapshots = []
                            try:
                                current_snapshots = __analyze_file(path_to_filename,
                                                                   [filesystem],
                                                                   cmdline_opts.show_ended_process_and_tlocks).get(filesystem)
                                message =  "The analyzing of the file is complete."
                                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                            except AttributeError:
                                message = "There was no data found for the filesystem: %s" %(filesystem)
                                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                                continue
                            if (current_snapshots):
                                snapshots_by_filesystem += current_snapshots
                    if (snapshots_by_filesystem):
                        path_to_output_dir = os.path.join(os.path.join(cmdline_opts.path_to_output_dir,
                                                                       "multiple_nodes"),
                                                          "%s" %(filesystem))
                        # All the warnings found on the filesystem after plugins have ran.
                        warnings = __plugins_run(snapshots_by_filesystem,
                                                 path_to_output_dir,
                                                 enable_html_format, enable_png_format,
                                                 enable_graphs,
                                                 cmdline_opts.plugins_only_to_enable,
                                                 is_multi_node_supported=True)
                        #warnings = merge_dicts(warnings, __output_warnings(warnings, path_to_output_dir,
                        #                                        disable_std_out=cmdline_opts.disable_std_out,
                        #                                        html_format=enable_html_format)
    except KeyboardInterrupt:
        print ""
        message =  "This script will exit since control-c was executed by end user."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
        sys.exit(1)
    # #######################################################################
    # Exit the application with zero exit code since we cleanly exited.
    # #######################################################################
    sys.exit()
