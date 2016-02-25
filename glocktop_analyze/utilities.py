#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@author    : Shane Bradley
@contact   : sbradley@redhat.com
@version   : 0.1
@copyright : GPLv3

"""
import sys
import logging
import logging.handlers
import os
import os.path
import re
import locale
locale.setlocale(locale.LC_NUMERIC, "")

import glocktop_analyze

# ##############################################################################
# Classes
# ##############################################################################
class LogWriter :
    CRITICAL_LEVEL = logging.CRITICAL        #50
    ERROR_LEVEL    = logging.ERROR           #40
    WARNING_LEVEL  = logging.WARN            #30
    # FAILED_LEVEL   = logging.WARN + 1        #31
    STATUS_LEVEL   = logging.INFO + 2        #22
    # PASSED_LEVEL   = logging.INFO + 1        #21
    INFO_LEVEL     = logging.INFO            #20
    DEBUG_LEVEL    = logging.DEBUG           #10
    DISABLE_LOGGING = logging.NOTSET         #0

    def __init__(self, loggerName, loglevel, format, logtoFile=False,
                 disableConsoleLog=False):
        self.__loggerName = loggerName
        if (self.__loggerName in logging.getLogger().manager.loggerDict.keys()):
            message = "The logger already exists and a new one will not be created called: %s" %(self.__loggerName)
            logging.getLogger(self.__loggerName).warning(message)
        else:
            # add new custom logging level
            logging.STATUS = LogWriter.STATUS_LEVEL
            logging.addLevelName(logging.STATUS, "STATUS")
            logger = logging.getLogger(self.__loggerName)
            # Create a function for the STATUS_LEVEL since not defined by
            # python. This means you can call it like the other predefined message
            # functions. Example: logging.getLogger("loggerName").status(message)
            setattr(logger, "status", lambda *args: logger.log(LogWriter.STATUS_LEVEL, *args))
            # set formatter and level
            formatter = logging.Formatter(format)
            logger.setLevel(loglevel)

            # set the handler for writing to standard out
            self.__hdlrConsole = None
            if disableConsoleLog:
                # set standard out to blackhole
                sys.stdout = open('/dev/null', 'w')
            self.__hdlrConsole = StreamHandlerColorized(sys.stdout)
            self.__hdlrConsole.setFormatter(formatter)
            logger.addHandler(self.__hdlrConsole)

            # set the handler for writing to file if enabled
            self.__pathToLogFile = ""
            self.__hdlrFile = None
            if (logtoFile) :
                pathToLogFile = "/tmp/%s.log" %(loggerName)
                if ((os.access(pathToLogFile, os.W_OK)) or (not os.path.exists(pathToLogFile))):
                    self.__pathToLogFile = pathToLogFile
                    self.__hdlrFile = logging.FileHandler(self.__pathToLogFile)
                    self.__hdlrFile.setFormatter(formatter)
                    logger.addHandler(self.__hdlrFile)
                else:
                    message = "There was permission problem accessing the write attributes for the log file: %s." %(pathToLogFile)
                    logging.getLogger(self.__loggerName).error(message)

    def getPathToLogFile(self):
        return self.__pathToLogFile

    def removeHandlers(self) :
        if (not self.__hdlrConsole == None) :
            self.__logwriter.removeHandler(self.__hdlrConsole)
            self.__hdlrConsole.flush()
            self.__hdlrConsole.close()
            #print logging._handlers

        if (not self.__hdlrFile == None) :
            self.__logwriter.removeHandler(self.__hdlrFile)
            self.__hdlrFile.close()

class StreamHandlerColorized(logging.StreamHandler):
    CONSOLE_COLORS = {"black":"30", "white":"1;37", "red":"31", "lred":"1;31",
                      "green":"32", "lgreen":"1;32", "blue":"34", "lblue":"1;34",
                      "gray":"1;30", "lgray":"37", "cyan":"36", "lcyan":"1;36",
                      "purple":"35", "brown":"33", "yellow":"1;33", "pink":"1;35"}


    def __colorizeText(self, text, color):
        if (not StreamHandlerColorized.CONSOLE_COLORS.has_key(color)):
            return text
        fgColor = StreamHandlerColorized.CONSOLE_COLORS.get(color)
        opencol = "\033["
        closecol = "m"
        clear = opencol + "0" + closecol
        fg = opencol + fgColor + closecol
        for i in range((len("CRITICAL") + 1) - len(text)):
            text += " "
        return "%s%s%s" % (fg, text, clear)

    def emit(self, record):
        try:
            msg = self.format(record)
            #find which message level this is
            colorizedMsg = None
            #if (msg.find("PASSED") >= 0) :
            #    colorizedMsg = self.__colorizeText("PASSED", "lblue")
            #    msg = msg.replace("PASSED", colorizedMsg, 1)
            # elif (msg.find("FAILED") >= 0) :
            #    colorizedMsg = self.__colorizeText("FAILED", "red")
            #    msg = msg.replace("FAILED", colorizedMsg, 1)

            if (msg.find("STATUS") >= 0) :
                colorizedMsg = self.__colorizeText("STATUS", "brown")
                msg = msg.replace("STATUS", colorizedMsg, 1)
            elif (msg.find("INFO") >= 0) :
                colorizedMsg = self.__colorizeText("INFO", "blue")
                msg = msg.replace("INFO", colorizedMsg, 1)
            elif (msg.find("ERROR") >= 0) :
                colorizedMsg = self.__colorizeText("ERROR", "red")
                msg = msg.replace("ERROR", colorizedMsg, 1)
            elif (msg.find("WARNING") >= 0) :
                colorizedMsg = self.__colorizeText("WARNING", "yellow")
                msg = msg.replace("WARNING", colorizedMsg, 1)
            elif (msg.find("CRITICAL") >= 0) :
                colorizedMsg = self.__colorizeText("CRITICAL", "lred")
                msg = msg.replace("CRITICAL", colorizedMsg, 1)
            elif (msg.find("DEBUG") >= 0) :
                colorizedMsg = self.__colorizeText("DEBUG", "purple")
                msg = msg.replace("DEBUG", colorizedMsg, 1)
            try:
                self.stream.write(msg + "\n")
            except UnicodeEncodeError:
                self.stream.write(msg.encode("utf-8"))
            self.flush()
        except:
            self.handleError(record)


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
    if (not rows):
        return formatted_table

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
        if (colorize):
            formatted_table += ' | '.join(ColorizeConsoleText.red(format(title, "%ds" % width))
                                          for width, title in zip(widths, header) ) + "\n"
        else:
            formatted_table += ' | '.join(format(title, "%ds" % width)
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

def mkdirs(path_to_dir):
    if (os.path.isdir(path_to_dir)):
        return True
    elif ((not os.access(path_to_dir, os.F_OK)) and (len(path_to_dir) > 0)):
        try:
            os.makedirs(path_to_dir)
        except (OSError, os.error):
            message = "Could not create the directory: %s." %(path_to_dir)
            logging.getLogger(MAIN_LOGGER_NAME).error(message)
            return False
        except (IOError, os.error):
            message = "Could not create the directory with the path: %s." %(path_to_dir)
            logging.getLogger(MAIN_LOGGER_NAME).error(message)
            return False
    return os.path.isdir(path_to_dir)

def write_to_file(path_to_filename, data, append_to_file=True, create_file=False):
    [parent_dir, filename] = os.path.split(path_to_filename)
    if (mkdirs(parent_dir)):
        if (os.path.isfile(path_to_filename) or create_file):
            try:
                file_mode = "w"
                if (append_to_file):
                    file_mode = "a"
                fout = open(path_to_filename, file_mode)
                for line in data:
                    fout.write(line)
                fout.close()
                message = "The file was successfully written to: %s" %(path_to_filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
                return True
            except UnicodeEncodeError, e:
                message = "There was a unicode encode error writing to the file: %s." %(path_to_filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
            except IOError, e:
                message = "There was an error writing to the file: %s." %(path_to_filename)
                logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
    else:
        message = "The parent directory of the file could not be created: %s." %(path_to_filename)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).error(message)
    return False
