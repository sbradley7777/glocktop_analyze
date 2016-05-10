#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The utility merges GFS2 filesystem lockdumps (glocks files)
captured with "gfs2_lockcapture" to a format that can be processed
with "glocktop_analyze.py" script.

This script assumes data was captured with gfs2_lockcapture:
- https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/scripts/gfs2_lockcapture

@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3

"""
import sys
import logging
import logging.handlers
import os
import os.path
from optparse import OptionParser, Option, SUPPRESS_HELP
import fnmatch
from datetime import datetime

import glocktop_analyze
from glocktop_analyze.utilities import LogWriter
# Import logger that all files will use.
logger = LogWriter(glocktop_analyze.MAIN_LOGGER_NAME,
                   logging.INFO,
                   glocktop_analyze.MAIN_LOGGER_FORMAT,
                   disableConsoleLog=False)

from glocktop_analyze.utilities import get_data_from_file, write_to_file

# #####################################################################
# Global variables
# #####################################################################
VERSION_NUMBER = "0.1-7"

# #####################################################################
# Classes
# #####################################################################

class GlocksDumps():
    def __init__(self, hostname):
        self.__hostname = hostname
        self.__glocks_dumps_map = {}

    def get_hostname(self):
        return self.__hostname

    def add_glocks_dump(self, glocks_dump):
        gfs2_name = glocks_dump.get_gfs2_name()
        if (not self.__glocks_dumps_map.has_key(gfs2_name)):
            self.__glocks_dumps_map[gfs2_name] = []
        gdumps = self.__glocks_dumps_map[gfs2_name]
        gdumps.append(glocks_dump)

        self.__glocks_dumps_map[gfs2_name] = sorted(gdumps, key=lambda gds: gds.get_date_time())

    def get_glocks_dumps(self, gfs2_name):
        if (self.__glocks_dumps_map.has_key(gfs2_name)):
            return self.__glocks_dumps_map.get(gfs2_name)
        return []

    def get_gfs2_names(self):
        return self.__glocks_dumps_map.keys()

    def merge_glock_dumps(self, path_to_output_dir):
        path_to_merged_files = []
        for gfs2_name in gsds.get_gfs2_names():
            list_of_gsd = gsds.get_glocks_dumps(gfs2_name)
            message = "Merging %d glocks dumps for the host \"%s\" for the filesystem \"%s\"." %(len(list_of_gsd),
                                                                                                    self.get_hostname(),
                                                                                                    gfs2_name)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
            path_to_merged_file = os.path.join(path_to_output_dir,
                                               "glock_dump-%s-%s.txt" %(self.get_hostname(),
                                                                        gfs2_name))
            if (os.path.exists(path_to_merged_file)):
                try:
                    os.remove(path_to_merged_file)
                except IOError:
                    message = "There was an error removing the file: %s." %(path_to_merged_file)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            for gsd in list_of_gsd:
                glocks_dump_data = ""
                for line in get_data_from_file(gsd.get_path_to_glockfile(), strip_leading_character=False):
                    glocks_dump_data += "%s\n" %(line)
                if (glocks_dump_data):
                    glocks_dump_data = "%s\n%s\n" %(gsd.get_header(), glocks_dump_data)
                    if (not write_to_file(path_to_merged_file, glocks_dump_data, append_to_file=True, create_file=True)):
                        message = "There was an error writing to the file: %s" %(path_to_merged_file)
                        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            if (os.path.exists(path_to_merged_file)):
                path_to_merged_files.append(path_to_merged_file)
        return path_to_merged_files

class GlocksDump():
    def __init__(self, hostname, nodename, date_time, cluster_name, gfs2_name, path_to_glockfile):
        self.__hostname = hostname
        self.__nodename = nodename
        self.__date_time = date_time
        self.__cluster_name = cluster_name
        self.__gfs2_name = gfs2_name
        self.__path_to_glockfile = path_to_glockfile

    def __str__(self):
        return self.get_header()

    def get_header(self):
        # @ nate_bob0       Tue Feb  9 08:10:58 2016  @host-050.virt.lab.msp.redhat.com
        return "@ %s      %s  @%s" %(self.get_gfs2_name(),
                                     self.get_date_time().strftime("%a %b %d %H:%M:%S %Y"),
                                     self.get_hostname())

    def get_hostname(self):
        return self.__hostname

    def get_nodename(self):
        return self.__nodename

    def get_date_time(self):
        return self.__date_time

    def get_cluster_name(self):
        return self.__cluster_name

    def get_gfs2_name(self):
        return self.__gfs2_name

    def get_path_to_glockfile(self):
        return self.__path_to_glockfile


# #####################################################################
# Global functions
# #####################################################################
def is_valid_lockdump_file(path_to_filename):
    try:
        fin = open(path_to_filename)
        for line in fin.readlines()[0:10]:
            if (line.startswith("G:")):
                return True
    except (UnicodeEncodeError, IOError):
        return False
    return False

def find_files(directory, pattern):
    path_to_files = []
    #message = "Searching for pattern \"%s\" under directory: %s" %(pattern, directory)
    #logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                path_to_files.append(filename)
    if (not path_to_files):
        message = "Pattern not found under directory: %s" %(directory)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
    return path_to_files

def find_glocks_dumps(path_to_dir):
    gsds = []
    if (os.path.isdir(path_to_dir)):
        hostinformation_files = find_files(path_to_dir, "hostinformation.txt")
        if (hostinformation_files):
            for hi_file in hostinformation_files:
                # Find the hostinformation.txt file first to get time
                # snapshot of the GFS2 filesystem taken
                hostname = ""
                nodename = ""
                date_time = ""
                for line in get_data_from_file(hi_file):
                    if (line.startswith("HOSTNAME")):
                        hostname = line.split("=")[1].strip()
                    elif (line.startswith("NODE_NAME")):
                        nodename = line.split("=")[1].strip()
                    elif (line.startswith("TIMESTAMP")):
                        timestamp = line.split("=")[1].strip()
                        date_time = datetime.strptime(line.split("=")[1].strip(), "%Y-%m-%d %H:%M:%S")
                for path_to_glockfile in find_files(os.path.split(hi_file)[0], "glocks"):
                    gparent_dir = os.path.split(os.path.split(path_to_glockfile)[0])[1]
                    cluster_name = gparent_dir.split(":")[0]
                    gfs2_name = gparent_dir.split(":")[1]
                    message = "Checking to see if the following files is a valid glock dump: %s" %(path_to_glockfile)
                    logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                    if (is_valid_lockdump_file(path_to_glockfile)):
                        gsds.append(GlocksDump(hostname, nodename, date_time, cluster_name, gfs2_name, path_to_glockfile))
    glocks_dumps = {}
    for glocks_dump in gsds:
        if (not glocks_dumps.has_key(glocks_dump.get_hostname())):
            glocks_dumps[glocks_dump.get_hostname()] = GlocksDumps(glocks_dump.get_hostname())
        glocks_dumps[glocks_dump.get_hostname()].add_glocks_dump(glocks_dump)
    return glocks_dumps

# ##############################################################################
# Get user selected options
# ##############################################################################
def __get_options(cmd_parser) :
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
    cmd_parser.add_option("-p", "--path_to_filename",
                          action="extend",
                          dest="path_to_src_files",
                          help="the path to the directory containing data captured by gfs2_lockcapture",
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
    (cmdLine_opts, cmdLine_args) = cmd_parser.parse_args()
    return (cmdLine_opts, cmdLine_args)

# ##############################################################################
# OptParse classes for commandline options
# ##############################################################################
class OptionParserExtended(OptionParser):
    def __init__(self, version) :
        self.__command_name = os.path.basename(sys.argv[0])
        description =  "The utility merges GFS2 filesystem lockdumps captured with \"gfs2_lockcapture\" to "
        description += "format that can be processed by the \"glocktop_analyze.py\" script."

        OptionParser.__init__(self, option_class=ExtendOption,
                              version="%s %s\n" %(self.__command_name, version),
                              description="%s \n"%(description))

    def get_command_name(self):
        return self.__command_name

    def print_help(self):
        self.print_version()
        examples_message = "\n\n"
        OptionParser.print_help(self)

        examples_message += "Convert all the glocks files to the format used by glocktop_analyze.py.\n"
        examples_message += "# %s -p /tmp/gfs2_lockcapture-2015-06-30  -o /tmp/glocktop_data \n\n" %(self.get_command_name())
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
        (cmdline_opts, cmdline_args) = __get_options(cmd_parser)

        # #######################################################################
        # Set the logging levels.
        # #######################################################################
        if ((cmdline_opts.enableDebugLogging) and (not cmdline_opts.disable_std_out)):
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).setLevel(logging.DEBUG)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug("Debugging has been enabled.")

        # #######################################################################
        # Merge all the "glocks" files found.
        # #######################################################################
        merged_glocks_dump_files = []
        for filename in cmdline_opts.path_to_src_files:
            found_glocks_dump_files = False
            current_merged_gd_files = []
            if (os.path.isfile(filename)):
                message = "The -p option requires a path to a directory and file found: %s" %(filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).warning(message)
                continue
            elif (os.path.isdir(filename)):
                message = "Searching for glock lockdumps under the directory: %s" %(filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
                # If there are "hostinformation.txt" files then we know data
                # was captured with gfs2_lockcapture and can make a few
                # assupmtions.
                glocks_dumps = find_glocks_dumps(filename)
                for key in glocks_dumps.keys():
                    gsds = glocks_dumps.get(key)
                    current_merged_gd_files += gsds.merge_glock_dumps(cmdline_opts.path_to_output_dir)
            if (current_merged_gd_files):
                merged_glocks_dump_files += current_merged_gd_files
            else:
                message = "There was no glocks dump files found under the path: %s" %(filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).warning(message)
        # Print the result
        if (merged_glocks_dump_files):
            print "The following files were created from merged GFS2 glock dumps:"
            for merged_gsds_file in merged_glocks_dump_files:
                print "\t%s" %(merged_gsds_file)
        else:
            message = "There was no valid GFS2 lockdump files merged."
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            message = "A path (-p option) to the directory that contains the data captured by \"gfs2_lockcapture\" is required."
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).info(message)
            sys.exit(1)

    except KeyboardInterrupt:
        print ""
        message =  "This script will exit since control-c was executed by end user."
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
        sys.exit(1)
    # #######################################################################
    # Exit the application with zero exit code since we cleanly exited.
    # #######################################################################
    sys.exit()
