#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
import re

def parse_glocks_stats(line):
    try:
        stat_line = line.split("S ")[1].strip()
    except IndexError:
        return {}
    if ((stat_line.find("--") > 0) or (stat_line.find("Total") > 0)):
        return {}
    stats_map = {"glock_state":"", "nondisk":0, "inode":0, "rgrp":0, "iopen":0, "flock":0, "quota":0, "journal":0, "total":0}
    regex = "(?P<glock_state>Unlocked|Locked|Held EX|Held SH|Held DF|G Waiting|P Waiting):\s*(?P<nondisk>\d+)\s*(?P<inode>\d+)\s*(?P<rgrp>\d+)\s*(?P<iopen>\d+)\s*(?P<flock>\d+)\s*(?P<quota>\d+)\s*(?P<journal>\d+)\s*(?P<total>\d+).*"
    rem = re.compile(regex)
    mo = rem.match(stat_line)
    if mo:
        return mo.groupdict()
    elif (stat_line.startswith("DLM wait")):
        split_stat_line = stat_line.split(":")
        return {"glock_state":split_stat_line[0].strip(), "nondisk":split_stat_line[1].strip(), "inode":0, "rgrp":0, "iopen":0, "flock":0, "quota":0, "journal":0, "total":split_stat_line[1].strip()}
    return {}

