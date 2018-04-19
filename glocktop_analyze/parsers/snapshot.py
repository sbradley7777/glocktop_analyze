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

from glocktop_analyze.snapshot import Snapshot, DLMActivity
from glocktop_analyze.glock import Glock, GlockHolder, GlockObject
from glocktop_analyze.glocks_stats import GlocksStats, GlockStat
import glocktop_analyze.glocks_stats

from glocktop_analyze.parsers.glock import parse_glock,parse_glock_holder
from glocktop_analyze.parsers.glocks_stats import parse_glocks_stats

def parse_snapshot(line, show_ended_process_and_tlocks=False):
    days_regex = "(?P<day>%s)" % '|'.join(calendar.day_abbr[0:])
    months_regex = "(?P<month>%s)" % '|'.join(calendar.month_abbr[1:])
    dow_regex = "(?P<dow>\d{1,2})"
    time_regex = "(?P<time>\d{1,2}:\d\d:\d\d)"
    year_regex = "(?P<year>\d{4})"
    hostname_regex = "@(?P<hostname>.*)"
    # old format
    # regex = "^@ (?P<filesystem>\w+)\s+%s\s%s\s*%s\s%s\s%s\s\s%s" %(days_regex, months_regex, dow_regex, time_regex, year_regex, hostname_regex)
    # not sure about this format
    # regex = "^@ (?P<filesystem>[a-z0-9-_]*)\s+%s\s%s\s*%s\s%s\s%s\s\s%s" %(days_regex, months_regex, dow_regex, time_regex, year_regex, hostname_regex)
    # new format
    regex = "^@ (?P<filesystem>[a-z0-9-_]*)\s+%s\s%s\s*%s\s%s\s%s\s\s%s" %(days_regex, months_regex, dow_regex, time_regex, year_regex, hostname_regex)

    rem = re.compile(regex)
    mo = rem.match(line)
    if (mo == None):
        # old format, try it. My glock_merge needs to use same format as
        # latest. Should keep this for older versions running in the wild.
        regex = "^@ (?P<filesystem>\w+)\s+%s\s%s\s*%s\s%s\s%s\s\s%s" %(days_regex, months_regex, dow_regex, time_regex, year_regex, hostname_regex)
        rem = re.compile(regex)
        mo = rem.match(line)
    if mo:
        date_time = datetime.strptime("%s %s %s %s" %(mo.group("month"), mo.group("dow"), mo.group("year"), mo.group("time")), "%b %d %Y %H:%M:%S")
        split_line = mo.group("hostname").strip().split("dlm:")
        hostname = split_line[0].strip()
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
            # dlm_regex = "(?P<dlm_dirtbl_size>\d+)/(?P<dlm_rsbtbl_size>\d+)/(?P<dlm_lkbtbl_size>\d+)\s\[(?P<dlm_activity>\*+).*"
            # Need when there is no hash table sizes.
            dlm_regex = "(?P<dlm_dirtbl_size>\d+|\s?)/(?P<dlm_rsbtbl_size>\d+|\s?)/(?P<dlm_lkbtbl_size>\d+|\s)\s\[(?P<dlm_activity>\*+).*"
            rem_dlm = re.compile(dlm_regex)
            mo_dlm = rem_dlm.match(split_line[1].strip())
            if mo_dlm:
                # Default sizes for DLM hash tables which will be used if sizes
                # not in output.
                dlm_dirtbl_size = 1024
                dlm_rsbtbl_size = 1024
                dlm_lkbtbl_size = 1024
                dlm_dict = mo_dlm.groupdict()
                if (dlm_dict.has_key("dlm_dirtbl_size")):
                    if (dlm_dict.get("dlm_dirtbl_size").isdigit()):
                        dlm_dirtbl_size = int(dlm_dict.get("dlm_dirtbl_size"))
                if (dlm_dict.has_key("dlm_rsbtbl_size")):
                    if (dlm_dict.get("dlm_rsbtbl_size").isdigit()):
                        dlm_rsbtbl_size = int(dlm_dict.get("dlm_rsbtbl_size"))
                if (dlm_dict.has_key("dlm_lkbtbl_size")):
                    if (dlm_dict.get("dlm_lkbtbl_size").isdigit()):
                        dlm_lkbtbl_size = int(dlm_dict.get("dlm_lkbtbl_size"))

                dlm_activity = DLMActivity(dlm_dirtbl_size, dlm_rsbtbl_size, dlm_lkbtbl_size,
                                           len(mo_dlm.group("dlm_activity")))
        return Snapshot(mo.group("filesystem"), hostname, date_time, dlm_activity, show_ended_process_and_tlocks)
    return None

def process_snapshot(snapshot, snapshot_lines):
    # Process any remaining items
    if (not snapshot == None):
        glock = None
        glocks_stats_lines = []
        call_trace = []
        for sline in snapshot_lines:
            if (sline.startswith("G")):
                if ((call_trace) and (not glock == None)):
                    glock_holders = glock.get_holders()
                    if (glock_holders):
                        glock_holders[0].add_call_trace(call_trace)
                # Reset call trace.
                call_trace = []
                glock = parse_glock(sline)
                if (not glock == None):
                    snapshot.add_glock(glock)
            elif (not glock == None and sline.startswith("H")):
                glock_holder = parse_glock_holder(sline)
                if (not (glock_holder == None)):
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
                call_trace.append(sline.split(":")[1].strip())
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
            filesystem_name = snapshot.get_filesystem_name()
            date_time = snapshot.get_date_time()
            glocks_stats = GlocksStats(filesystem_name, date_time)
            for line in glocks_stats_lines:
                stat_map = parse_glocks_stats(line)
                if (stat_map):
                    glock_state = stat_map.get("glock_state")
                    for glock_type in glocktop_analyze.glocks_stats.GLOCK_TYPES:
                        glocks_stats.add_stat(glock_type, glock_state, int(stat_map.get(glock_type)))
            snapshot.add_glocks_stats(glocks_stats)
