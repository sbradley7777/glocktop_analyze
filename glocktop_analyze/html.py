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

def generate_table_header():
    style =  "<style>\n"
    style += "table, th, td {\n"
    style += "border: 1px solid black;\n"
    style += "border-collapse: collapse;\n"
    style += "}\n"
    style += "th, td {\n"
    style += "padding: 5px;\n"
    style += "text-align: left;\n"
    style += "}\n"

    style += "table#t01 {\n"
    style += "width: 100%;\n"
    #style += "    background-color: #f1f1c1;\n"
    style += "}\n"

    style += "table#t01 tr:nth-child(even) {\n"
    style += "background-color: #eee;\n"
    style += "}\n"

    style += "table#t01 tr:nth-child(odd) {\n"
    style += "background-color:#fff;\n"
    style += "}\n"

    style += "table#t01 th{\n"
    style += "background-color: black;\n"
    style += "color: white;\n"
    style += "}\n"

    style += "</style>\n"
    header_pre = "<html>\n\t<head>\n"
    header_post = "</head>\n\t<body>\n"
    return "%s%s%s" %(header_pre, style, header_post)

def generate_table(header, table, title="", description="", caption=""):
    if (not table):
        return ""
    htable = ""
    if (title):
        htable += "<center><H3>%s</H3>\n<BR></center>" %(title)
    if (description):
        htable += "%s<BR>" %(description)
    htable +=  '<table border="1" id="t01">\n'
    #if (title):
    #    htable += "<caption><b>%s</b></caption>" %(title)
    if (header):
        htable += "<tr>"
        for item in header:
            htable += "<th>%s</th>" %(item)
        htable += "</tr>\n"
    for row in table:
        htable += "<tr>"
        for item in row:
            htable += "<td>%s</td>" %(item)
        htable += "</tr>\n"
    htable +=  "</table><BR><HR>\n"
    return htable

def generate_footer():
    footer = "\n\n\t<BR>"
    footer += "<b>The glocktop analysis and html files were generated by the utility <a href=\"https://github.com/sbradley7777/glocktop_analyze\">glocktop_analyze</a>."
    footer += "\n\t</body>\n</html>"
    return footer

def generate_footer_graphs():
    footer = "\n\n\t"
    footer += "<b>The graphs were generated by the utility <a href=\"https://github.com/sbradley7777/glocktop_analyze\">glocktop_analyze</a> "
    footer += "\n\t\tusing the <a href=\"http://www.pygal.org/\">pygal</a> libraries.<b>"
    footer += "\n\t</body>\n</html>"
    return footer

def generate_graph_index_page(path_to_output_dir, path_to_graphs, title):
    # Need to create a space instead of using tabs.
    figure_code_pre_svg = "\t\t<figure> <embed type=\"image/svg+xml\" src=\""
    figure_code_pre_png = "\t\t<figure> <embed type=\"image/png\" src=\""
    figure_code_post = "\"/></figure><BR>\n\t\t<BR><HR><BR>\n"
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
