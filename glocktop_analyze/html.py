#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
import os
import os.path
import logging

import glocktop_analyze
from glocktop_analyze.utilities import LogWriter, mkdirs, write_to_file

def generate_header():
    return "<html>\n\t<head>\n\t</head>\n\t<body>\n"

def generate_css_header(include_css_table=False):
    style =  "<style>\n"
    style += generate_css_colors()
    if (include_css_table):
        style += generate_css_tables()
    style += "</style>\n"
    header_pre = "<html>\n\t<head>\n"
    header_post = "</head>\n\t<body>\n"
    return "%s\n%s\n%s\n" %(header_pre, style, header_post)

def generate_css_colors():
    style = ""
    style += "body {color: white; background: black;}\n"
    style += "span.red {color:#ff0000;}\n"
    style += "span.orange {color:#ffa500;}\n"
    return style

def generate_css_tables():
    style = ""
    style += "table {width:100%}\n"
    style += "table, th, td {border: 1px solid white; border-collapse: collapse; }\n"
    style += "th, td {padding: 5px; text-align: left;}\n"
    style += "th{background-color: white; color: black;}\n"
    style += "#tr_grey {background-color: grey; color: white;}\n"
    return style

def generate_table(table, header, title="", description="", caption=""):
    if (not table):
        return ""
    htable = ""
    if (title):
        htable += "<center><H3>%s</H3>\n<BR></center>" %(title)
    if (description):
        htable += "%s<BR/>" %(description)
    htable +=  '<table border="1">\n'
    #if (title):
    #    htable += "<caption><b>%s</b></caption>" %(title)
    if (header):
        htable += "<tr>"
        for item in header:
            htable += "<th>%s</th>" %(item)
        htable += "</tr>\n"
    # Alternate the colors of table row background unless the first value is
    # just a "-". If first is "-" then it is assume it is carry over from
    # previous row.
    index = 0
    for row in table:
        if (not row[0].strip() == "-"):
            # If row does not start with dash then not continuation so increment
            # index so next color be choosen for row.
            index += 1
        if (index % 2 == 0):
            htable += "<tr>"
        else:
            #htable += "<tr bgcolor=\"#808080\">
            htable += '<tr id="tr_grey">'
        for item in row:
            htable += "<td>%s</td>" %(item)
        htable += "</tr>\n"
    htable +=  "</table><BR/><HR/>\n"
    return htable

def generate_footer():
    footer = ""
    footer += "<b>The glocktop analysis and html files were generated by the utility <a href=\"https://github.com/sbradley7777/glocktop_analyze\">glocktop_analyze</a>."
    footer += "</body></html>"
    return footer

def generate_footer_graphs():
    footer = ""
    footer += "<b>The graphs were generated by the utility <a href=\"https://github.com/sbradley7777/glocktop_analyze\">glocktop_analyze</a> "
    footer += "\n\t\tusing the <a href=\"http://www.pygal.org/\">pygal</a> libraries.<b>"
    footer += "\n\t</body>\n</html>"
    return footer

def generate_graph_index_page(path_to_output_dir, path_to_graphs, title):
    # Need to create a space instead of using tabs.
    figure_code_pre_svg = "\t\t<figure> <embed type=\"image/svg+xml\" src=\""
    figure_code_pre_png = "\t\t<figure> <embed type=\"image/png\" src=\""
    figure_code_post = "\"/></figure><BR/><BR/><HR/><BR/>"
    figure_code = ""
    for path_to_image_file in path_to_graphs:
        # Need code to check if png or svg.
        if (path_to_image_file.endswith("svg")):
            figure_code += figure_code_pre_svg
        elif (path_to_image_file.endswith("png")):
            figure_code += figure_code_pre_png
        figure_code += "graphs/%s%s" %(os.path.split(path_to_image_file)[1], figure_code_post)
    html_data = "%s%s%s" %(generate_header(), figure_code, generate_footer_graphs())
    path_to_html_file = os.path.join(path_to_output_dir, "%s.html" %(title.replace(" - ", "-").replace(" ", "_").lower()))
    if (write_to_file(path_to_html_file, html_data, append_to_file=False, create_file=True)):
        message = "The html page containing the graphs was written to: %s" %(path_to_html_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
    else:
        message = "There was an error writing the html page containing the graphs to: %s" %(path_to_html_file)
        logging.getLogger(glocktop_analyze.MAIN_LOGGER_NAME).debug(message)
