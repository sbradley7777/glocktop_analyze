#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3

"""
import logging
import logging.handlers
import os
import os.path
import locale
locale.setlocale(locale.LC_NUMERIC, "")

import glocktop_analyze

# ##############################################################################
# Classes
# ##############################################################################
class ColorizeConsoleText(object):
    """
    References from:
    - https://gist.github.com/Jossef/0ee20314577925b4027f and modified bit.
    - https://gist.github.com/arulrajnet/47ff2674ad9da6dcac00
    - http://misc.flogisoft.com/bash/tip_colors_and_formatting (colors)
    """

    def __init__(self, text, **user_styles):
        # Prevent int and string concat error.
        text = str(text)

        styles = {
            # styles
            'reset': '\033[0m',
            'bold': '\033[01m',
            'disabled': '\033[02m',
            'underline': '\033[04m',
            'reverse': '\033[07m',
            'strike_through': '\033[09m',
            'invisible': '\033[08m',
            # text colors
            'fg_black': '\033[30m',
            'fg_red': '\033[31m',
            'fg_green': '\033[32m',
            'fg_orange': '\033[33m',
            'fg_blue': '\033[34m',
            'fg_purple': '\033[35m',
            'fg_cyan': '\033[36m',
            'fg_light_grey': '\033[37m',
            'fg_dark_grey': '\033[90m',
            'fg_light_red': '\033[91m',
            'fg_light_green': '\033[92m',
            'fg_yellow': '\033[93m',
            'fg_light_blue': '\033[94m',
            'fg_pink': '\033[95m',
            'fg_light_cyan': '\033[96m',
            'fg_white': '\033[97m',
            'fg_default': '\033[99m',
            # background colors
            'bg_black': '\033[40m',
            'bg_red': '\033[41m',
            'bg_green': '\033[42m',
            'bg_orange': '\033[43m',
            'bg_blue': '\033[44m',
            'bg_purple': '\033[45m',
            'bg_cyan': '\033[46m',
            'bg_light_grey': '\033[47m'
        }

        self.color_text = ''
        for style in user_styles:
            try:
                self.color_text += styles[style]
            except KeyError:
                raise KeyError("ERROR: def color: parameter `{}` does not exist".format(style))

        self.color_text += text

    def __format__(self):
        return '\033[0m{}\033[0m'.format(self.color_text)

    @classmethod
    def red(clazz, text):
        cls = clazz(text, bold=True, fg_red=True)
        return cls.__format__()

    @classmethod
    def orange(clazz, text):
        cls = clazz(text, bold=True, fg_orange=True)
        return cls.__format__()

    @classmethod
    def green(clazz, text):
        cls = clazz(text, bold=True, fg_green=True)
        return cls.__format__()

    @classmethod
    def custom(clazz, text, **custom_styles):
        cls = clazz(text, **custom_styles)
        return cls.__format__()

# ##############################################################################
# Functions
# ##############################################################################
def tableize(table, header):
    if (not len(table) > 0):
        return ""

    colorize_header = []
    for item in header:
        colorize_header.append(ColorizeConsoleText.red(item))
    table.insert(0, header)

    def format_num(num):
        try:
            inum = int(num)
            return locale.format("%.*f", (0, inum), True)
        except (ValueError, TypeError):
            return str(num)

    def get_max_width(table, index):
        return max([len(format_num(row[index])) for row in table])
    col_paddings = []

    for i in range(len(table[0])):
        col_paddings.append(get_max_width(table, i))

    ftable = ""
    for row in table:
        # left col
        ftable += str(row[0].ljust(col_paddings[0] + 1))
        # rest of the cols
        for i in range(1, len(row)):
            col = format_num(row[i]).rjust(col_paddings[i] + 2)
            ftable += str(col)
        ftable += "\n"

    return ftable

def write_to_file(path_to_filename, data, append_to_file=True, create_file=False):
    [parent_dir, filename] = os.path.split(path_to_filename)
    if (os.path.isfile(path_to_filename) or (os.path.isdir(parent_dir) and create_file)):
        try:
            file_mode = "w"
            if (append_to_file):
                file_mode = "a"
            fout = open(path_to_filename, file_mode)
            fout.write(data + "\n")
            fout.close()
            return True
        except UnicodeEncodeError, e:
            message = "There was a unicode encode error writing to the file: %s." %(path_to_filename)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            return False
        except IOError:
            message = "There was an error writing to the file: %s." %(path_to_filename)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            return False
    return False

def mkdirs(path_to_dir):
    if (os.path.isdir(path_to_dir)):
        return True
    elif ((not os.access(path_to_dir, os.F_OK)) and (len(path_to_dir) > 0)):
        try:
            os.makedirs(path_to_dir)
        except (OSError, os.error):
            message = "Could not create the directory: %s." %(path_to_dir)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            return False
        except (IOError, os.error):
            message = "Could not create the directory with the path: %s." %(path_to_dir)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            return False
    return os.path.isdir(path_to_dir)

def get_data_from_file(path_to_filename) :
    if (len(path_to_filename) > 0) :
        try:
            fin = open(path_to_filename, "r")
            data = fin.readlines()
            fin.close()
            mod_data = []
            for line in data:
                mod_data.append(line.strip())
            return mod_data
        except (IOError, os.error):
            message = "An error occured reading the file: %s." %(path_to_filename)
            logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
    return []

