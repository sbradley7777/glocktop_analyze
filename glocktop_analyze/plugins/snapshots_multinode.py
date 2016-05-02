#!/usr/bin/python
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@copyright : GPLv3

* This plugin outputs the number of snapshots taken for a filesystem, the start
  time, and end time or last snapshot taken from multiply nodes.

* This plugin outputs the filesystem name, time when snapshot taken when dlm
  activity is greater than zero from multiply nodes.

"""
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.plugins import Plugin
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize
from glocktop_analyze.html import generate_table_header, generate_table
from glocktop_analyze.html import generate_footer

class SnapshotsMultinode(Plugin):
    def __init__(self, snapshots, path_to_output_dir, options):
        Plugin.__init__(self, "snapshots multiply nodes",
                        "The stats for the snapshots and dlm activity for multiply nodes.",
                        snapshots, "Snapshot Stats for Mulitple Nodes", path_to_output_dir,
                        options, True)
        # Can still take snapshots as i can sort in plugin by hostname into a map.

    def analyze(self):
        print "Analyzing multinodes for snapshots."

    def console(self):
        print "Multiply nodes for Snapshots."

    def write(self, html_format=False):
        pass
