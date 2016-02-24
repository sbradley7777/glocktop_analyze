#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
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
        return "(%s/%s) state: %s | demote_time: %sms | hw count: %d" %(self.get_type(),
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

