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
    def light_grey(clazz, text):
        cls = clazz(text, fg_light_grey=True)
        return cls.__format__()

    @classmethod
    def custom(clazz, text, **custom_styles):
        cls = clazz(text, **custom_styles)
        return cls.__format__()

# ##############################################################################
# Functions
# ##############################################################################
def tableize(rows, header, colorize=True):
    """
    Prints out a table using the data in `rows`, which is assumed to be a
    sequence of sequences with the 0th element being the header.
    https://gist.github.com/lonetwin/4721748
    """
    formatted_table = ""

    rows.insert(0, header)
    def __format_item(item):
        import locale
        locale.setlocale(locale.LC_NUMERIC, "")
        try:
            return str(item)
        except UnicodeEncodeError:
            return item.encode("utf-8")

    # Convert all values in rows to strings.
    if (len(rows) > 0):
        converted_rows_to_str = []
        for row in rows:
            current_row = []
            for item in row:
                current_row.append(__format_item(item))
            if (len(current_row) > 0):
                converted_rows_to_str.append(current_row)
        # Figure out each column widths which is max column size for all rows.
        widths = [ len(max(columns, key=len)) for columns in zip(*converted_rows_to_str) ]
        # Add seperator
        formatted_table += '-+-'.join( '-' * width for width in widths) + "\n"
        # Add the header
        header, data = converted_rows_to_str[0], converted_rows_to_str[1:]
        formatted_table += ' | '.join(ColorizeConsoleText.red(format(title, "%ds" % width))
                                      for width, title in zip(widths, header) ) + "\n"
        # Add seperator from first row and header.
        formatted_table += '-+-'.join( '-' * width for width in widths) + "\n"
        count = 0
        for row in data:
            row_string = " | ".join(format(cdata, "%ds" % width) for width, cdata in zip(widths, row))
            if (not row_string.startswith("-")):
                count = count + 1
            # Skip colorizing filler lines with no data "-|-|-".
            if (((count % 2) == 0) and (colorize == True) and
                (not row_string.replace(" ", "").startswith("-|-|-"))):
                row_string = ColorizeConsoleText.light_grey(row_string)
            formatted_table += row_string + "\n"
    return formatted_table

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
