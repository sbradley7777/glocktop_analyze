#!/usr/bin/python
import logging
import logging.handlers
import os.path

import glocktop_analyze
from glocktop_analyze.stats import Stats
from glocktop_analyze.utilities import ColorizeConsoleText, write_to_file, tableize

class Pids(Stats):
    def __init__(self, snapshots, path_to_output_dir):
        Stats.__init__(self, snapshots, "Pids Stats", path_to_output_dir)

    def analyze(self):
        for snapshot in self.get_snapshots():
            pass

    def console(self):
        if (self.get_snapshots()):
            pass

    def write(self):
        if (self.get_snapshots()):
            pass
