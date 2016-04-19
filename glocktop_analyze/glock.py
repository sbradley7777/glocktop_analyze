#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""

# #####################################################################
# Global Vars
# #####################################################################
# https://access.redhat.com/articles/35653
GLOCK_MODES = {"UN":"Unlocked",
               "SH":"Shared",
               "EX":"Excluse",
               "DF":"Deferred"}

GLOCK_MODES_DESCRIPTION = {"UN":"An unlocked (no DLM lock associated with glock or NL lock depending on I flag).",
                           "SH":"A shared (protected read) lock.",
                           "EX":"An exclusive lock of the glock.",
                           "DF":"A deferred (concurrent write) lock used for Direct I/O and filesystem freeze."}
GLOCK_TYPES = {1:"Transition",
               2:"Inode",
               3:"Resource Group",
               4:"Meta",
               5:"Iopen",
               6:"Flock",
               8:"Quota",
               9:"Journal",}

GLOCK_TYPES_DESCRIPTION = {1:"A transition lock.",
                           2:"An inode's metadata and data",
                           3:"A resource group's metadata.",
                           4:"The superblock.",
                           5:"An iopen last closer detection.",
                           6:"A flock(2) syscall.",
                           8:"A quota operation.",
                           9:"A journal mutex.",}

# Example:  G:  s:EX n:2/183f5 f:lDpfiIqo t:UN d:UN/277000 a:0 v:0 r:4 m:200
GLOCK_FLAGS_TYPE = {"l":"Locked",
                    "D":"Demote",
                    "d":"Demote Pending",
                    "p":"Demote in Progress",
                    "y":"Dirty",
                    "f":"Log Flush",
                    "i":"Invalidate in Progress",
                    "r":"Reply Pending",
                    "I":"Initial",
                    "F":"Frozen",}

GLOCK_FLAGS_DESCRIPTIONS = {"l":"The glock is in the process of changing state.",
                           "D":"A demote request (local or remote).",
                           "d":"A deferred (remote) demote request.",
                           "p":"The glock is in the process of responding to a demote request.",
                           "y":"Data needs flushing to disk before releasing this glock.",
                           "f":"The log needs to be committed before releasing this glock.",
                           "i":"In the process of invalidating pages under this glock.",
                           "r":"Reply received from remote node is awaiting processing.",
                           "I":"Set when DLM lock is associated with this glock.",
                           "F":"Replies from remote nodes ignored - recovery is in progress."}

GLOCK_HOLDER_FLAGS_TYPE = {"t":"Try",
                           "T":"Try 1CB",
                           "e":"No Expire",
                           "A":"Any",
                           "p":"Priority",
                           "a":"Async",
                           "E":"Exact",
                           "c":"No Cache",
                           "H":"Holder",
                           "W":"Wait",
                           "F":"First"}

GLOCK_HOLDER_FLAGS_DESCRIPTION = {"t":"A try lock.",
                                  "T":"A try lock which sends a single callback.",
                                  "e":"Ignore subsequent lock cancel requests.",
                                  "A":"Any compatible lock mode is acceptable",
                                  "p":"Enqueue lock request at head of queue.",
                                  "a":"Don't wait for glock result (process will poll later).",
                                  "E":"Must have exact lock mode.",
                                  "c":"When unlocked, demote DLM lock immediately.",
                                  "H":"Indicates that request is granted.",
                                  "W":"Set while waiting for request to complete.",
                                  "F":"Set when holder is first to be granted for this glock."}
class Glock():
    def __init__(self, gtype, inode, state, demote_time):
        self.__type = gtype
        self.__inode = inode
        self.__state = state
        self.__demote_time = demote_time

        # This list contains the holder and other waiting to be holders(waiters)
        self.__holders = []
        self.__glock_object = None

    def __str__(self):
        return "G: (%s/%s) state: %s | demote_time: %sms | hw count: %d" %(self.get_type(),
                                                                           self.get_inode(),
                                                                           self.get_state(),
                                                                           self.get_demote_time(),
                                                                           len(self.get_holders()))

    def get_type(self):
        return self.__type

    def get_inode(self):
        return self.__inode

    def get_state(self):
        return self.__state

    def get_demote_time(self):
        return self.__demote_time

    def add_holder(self, holder):
        self.__holders.append(holder)

    def get_holders(self):
        return self.__holders

    def add_glock_object(self, glock_object):
        self.__glock_object = glock_object

    def get_glock_object(self):
        return self.__glock_object

    def has_ended_process(self):
        if (not len(self.get_holders()) > 1):
            for gh in self.get_holders():
                if (gh.get_command().lower().strip() == "(ended)"):
                    return True
        return False

    def get_glock_holder(self):
        # Returns GlockHolder that is holding the lock. If none is holding, then return None.
        holders = self.get_holders()
        if (holders):
            if ("H" in holders[0].get_flags()):
                return holders[0]
        return None

class GlockHolder:
    # The GlockHolder can be the holder of glock or waiter of glocks
    def __init__(self, text, state, flags, error, pid, command):
        self.__text = text
        self.__state = state
        self.__flags = flags
        self.__error = error
        self.__pid = pid
        self.__command = command

    def __str__(self):
        return self.get_text()

    def get_text(self):
        return self.__text

    def get_state(self):
        return self.__state

    def get_flags(self):
        return self.__flags

    def get_error(self):
        return self.__error

    def get_pid(self):
        return self.__pid

    def get_command(self):
        return self.__command

class GlockObject():
    # The "I:" describes an inode associated with the lock, "R:" describes an
    # resource group associated with the glock, and "B:" describes a reservation
    # associated with a resource group.
    def __init__(self, text):
        self.__text = text

    def __str__(self):
        return self.get_text()

    def get_text(self):
        return self.__text

