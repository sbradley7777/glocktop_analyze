#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
from glocktop_analyze.utilities import get_data_from_file
from glocktop_analyze.parsers.snapshot import parse_snapshot
from glocktop_analyze.snapshot import Snapshot

def get_hostname(path_to_filename):
    gfs2_snapshot = None
    lines = get_data_from_file(path_to_filename)
    for line in lines:
        # @, G, H, I, R, B, U, C, S
        if ((line.startswith("@")) or (not len(line) > 0)):
            gfs2_snapshot = parse_snapshot(line)
            if (not gfs2_snapshot == None):
                return gfs2_snapshot.get_hostname()
    return ""

def get_filesystems(path_to_filename, gfs2_filesystem_names):
    filesystems = []
    gfs2_snapshot = None
    lines = get_data_from_file(path_to_filename)
    for line in lines:
        # @, G, H, I, R, B, U, C, S
        if ((line.startswith("@")) or (not len(line) > 0)):
            gfs2_snapshot = parse_snapshot(line)
            if (not gfs2_snapshot == None):
                fs = gfs2_snapshot.get_filesystem_name()
                if (not fs in filesystems):
                    filesystems.append(fs)
    return filesystems
