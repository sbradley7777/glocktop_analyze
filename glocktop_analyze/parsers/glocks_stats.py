#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
import re
from glocktop_analyze.glocks_stats import GlocksStats, GlockStats

def parse_glocks_stats(line):
    try:
        stat_line = line.split("S ")[1].strip()
    except IndexError:
        return {}
    if ((stat_line.find("--") > 0) or (stat_line.find("Total") > 0)):
        return {}
    stats_map = {"glock_category":"", "nondisk":0, "inode":0, "rgrp":0, "iopen":0, "flock":0, "quota":0, "journal":0, "total":0}
    regex = "(?P<glock_category>Unlocked|Locked|Held EX|Held SH|Held DF|G Waiting|P Waiting):.*(?P<nondisk>\d+).*(?P<inode>\d+).*(?P<rgrp>\d+).*(?P<iopen>\d+).*(?P<flock>\d+).*(?P<quota>\d+).*(?P<journal>\d+).*(?P<total>\d+).*"
    rem = re.compile(regex)
    mo = rem.match(stat_line)
    if mo:
        return mo.groupdict()
    elif (stat_line.startswith("DLM wait")):
        split_stat_line = stat_line.split(":")
        return {"glock_category":split_stat_line[0].strip(), "nondisk":split_stat_line[1].strip(), "inode":0, "rgrp":0, "iopen":0, "flock":0, "quota":0, "journal":0, "total":split_stat_line[1].strip()}
    return {}

