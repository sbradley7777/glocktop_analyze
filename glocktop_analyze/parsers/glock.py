#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
import re
from glocktop_analyze.glock import Glock, GlockHolder

def parse_glock(line):
    # This regex works glocktop output but does not work on regular glock dumps.
    #regex = re.compile("^G:  s:(?P<state>\S+) n:(?P<type>\d)/(?P<inodeNumber>\S+)\s" + \
    #                    "f:(?P<flags>\S*)\st:(?P<target>\S+)\sd:(?P<demote_state>\S+)/" + \
    #                   "(?P<demote_time>\d+)( l:(?P<lvbs>\d+))?\sa:(?P<ails>\d+)" +\
    #                   "( v:(?P<v>\d+))?\sr:(?P<refs>\d+)( m:(?P<hold>\d+))\s" + \
    #                   "\((?P<glock_type>.*)\)")
    #mo = regex.match(line)
    #if mo:
    #    return Glock(int(mo.group("type")), mo.group("inodeNumber"), mo.group("state"), mo.group("demote_time"))

    regex = re.compile("^G:  s:(?P<state>\S+) n:(?P<type>\d)/(?P<inodeNumber>\S+)\s" + \
                        "f:(?P<flags>\S*)\st:(?P<target>\S+)\sd:(?P<demote_state>\S+)/" + \
                       "(?P<demote_time>\d+)( l:(?P<lvbs>\d+))?\sa:(?P<ails>\d+)" +\
                       "( v:(?P<v>\d+))?\sr:(?P<refs>\d+)(\sm:(?P<hold>\d+))" + \
                       ".*")
    mo = regex.match(line)
    if mo:
        return Glock(int(mo.group("type")), mo.group("inodeNumber"), mo.group("state"), mo.group("demote_state"), mo.group("demote_time"))
    return None
    parse_glock = staticmethod(parse_glock)

def parse_glock_holder(line):
    #regex = re.compile("^H: s:(\S+) f:(\S+) e:(\d+) p:(\d+) \[(\S+)\] (.+)")
    regex = re.compile("^H: s:(\S+) f:(\S+) e:(\d+) p:(\d+) \[(\S+)\] (.+) \[.*")
    mo = regex.match(line)
    if mo:
        return GlockHolder(line, mo.group(1), mo.group(2), mo.group(3),
                           mo.group(4), mo.group(5), mo.group(6))
    return None
    parse_glock_holder = staticmethod(parse_glock_holder)
