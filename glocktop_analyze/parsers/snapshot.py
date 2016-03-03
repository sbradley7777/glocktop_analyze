#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""

import re
import calendar
from datetime import datetime

from glocktop_analyze.gfs2_snapshot import GFS2Snapshot, DLMActivity
from glocktop_analyze.glock import Glock, GlockHolder, GlockObject
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
import glocktop_analyze.glocks_stats

from glocktop_analyze.parsers.glock import parse_glock,parse_glock_holder
from glocktop_analyze.parsers.glocks_stats import parse_glocks_stats

def parse_gfs2_snapshot(line, ignore_ended_processes=False):
    days_regex = "(?P<day>%s)" % '|'.join(calendar.day_abbr[0:])
    months_regex = "(?P<month>%s)" % '|'.join(calendar.month_abbr[1:])
    dow_regex = "(?P<dow>\d{1,2})"
    time_regex = "(?P<time>\d{1,2}:\d\d:\d\d)"
    year_regex = "(?P<year>\d{4})"
    hostname_regex = "@(?P<hostname>.*)"
    regex = "^@ (?P<filesystem>\w+)\s+%s\s%s\s*%s\s%s\s%s\s\s%s" %(days_regex, months_regex, dow_regex, time_regex, year_regex, hostname_regex)

    rem = re.compile(regex)
    mo = rem.match(line)
    if mo:
        date_time = datetime.strptime("%s %s %s %s" %(mo.group("month"), mo.group("dow"), mo.group("year"), mo.group("time")), "%b %d %Y %H:%M:%S")
        split_line = mo.group("hostname").strip().split("dlm:")
        hostname = split_line[0]
        # Check to see if DLM data is at end of string contained in hostname
        # group.

        # The [*  ] increasing * means increasing dlm activity. Each * represents a line in the dlm's *_waiters file
        # $ cat /sys/kernel/debug/dlm/<fs>_waiters
        # 100b0 1 5        1               1
        # It's basically a list of dlm resources that are hung up waiting for a comm response over the network.
        # - So no max ceiling, just a line count in the file.
        # - 1 lock could have multiple waiters(or lines).
        dlm_activity = None
        if (len(split_line) == 2):
            dlm_regex = "(?P<dlm_dirtbl_size>\d+)/(?P<dlm_rsbtbl_size>\d+)/(?P<dlm_lkbtbl_size>\d+)\s\[(?P<dlm_activity>\*+).*"
            rem_dlm = re.compile(dlm_regex)
            mo_dlm = rem_dlm.match(split_line[1].strip())
            if mo_dlm:
                dlm_activity = DLMActivity(int(mo_dlm.group("dlm_dirtbl_size")), int(mo_dlm.group("dlm_rsbtbl_size")),
                                           int(mo_dlm.group("dlm_lkbtbl_size")), len(mo_dlm.group("dlm_activity")))

        return GFS2Snapshot(mo.group("filesystem"), hostname, date_time, dlm_activity, ignore_ended_processes)
    return None

def process_gfs2_snapshot(gfs2_snapshot, snapshot_lines):
    # Process any remaining items
    if (not gfs2_snapshot == None):
        glock = None
        glocks_stats_lines = []
        for sline in snapshot_lines:
            if (sline.startswith("G")):
                glock = parse_glock(sline)
                gfs2_snapshot.add_glock(glock)
            elif (not glock == None and sline.startswith("H")):
                glock_holder = parse_glock_holder(sline)
                if (not glock_holder == None):
                    glock.add_holder(glock_holder)
            elif ((not glock == None) and
                  (sline.startswith("I") or
                   sline.startswith("R") or
                   sline.startswith("B"))):
                glock_object = GlockObject(sline)
                if (not glock_object == None):
                    glock.add_glock_object(glock_object)
            elif (sline.startswith("U")):
                # These lines represent glocktop's user interpretation of the
                # data, both glock and holder.  Lines that begin with (N/A:...)
                # can probably be ignored because they ought to be unimportant:
                # system files such as journals, etc.

                # Add certain lines to ignore list.
                continue
            elif (sline.startswith("C")):
                # These lines give you the call trace (call stack) of the process
                # that's either hold‐ing or waiting to hold the glock.
                continue
            elif (sline.startswith("S")):
                # These are not captured each time a filesystem is sampled.

                # These lines give you the summary of all glocks for this file
                # system: How many of each category are unlocked, locked, how
                # many are held in EX, SH, and DF, and how many are waiting. G
                # Waiting is how many glocks have waiters. P Waiting is how many
                # processes are waiting. Thus, you could have one glock that's
                # got ten processes waiting, or ten glocks that have ten
                # processes waiting.
                glocks_stats_lines.append(sline)
        if (glocks_stats_lines):
            filesystem_name = gfs2_snapshot.get_filesystem_name()
            date_time = gfs2_snapshot.get_date_time()
            glocks_stats = GlocksStats(filesystem_name, date_time)
            for line in glocks_stats_lines:
                stat_map = parse_glocks_stats(line)
                if (stat_map):
                    glock_state = stat_map.get("glock_state")
                    for glock_type in glocktop_analyze.glocks_stats.GLOCK_TYPES:
                        glocks_stats.add_stat(glock_type, glock_state, int(stat_map.get(glock_type)))
            gfs2_snapshot.add_glocks_stats(glocks_stats)
