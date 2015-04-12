#!/usr/bin/env python

"""Flowbox library helper.

Usage:
  flib.py whichproject <name>...
  flib.py whichprojects
  flib.py whichprojectsfile

"""

##### CHANGELOG #####
# 1:    whichproject


from __future__ import print_function
from docopt import docopt
import os
from itertools import chain, groupby
import re
from path import path
import fileinput
import sys
from operator import itemgetter


prefix = path("flowbox")

def hs_files():
    def list_hs_from(fs_dir):
        return (
            os.path.join(root,f)
            for root, dirs, files
                in os.walk(str(prefix / fs_dir))
            for f
                in files
            if "dist" not in root
                and f.endswith(".hs")
        )
    libs  = list_hs_from("libs")
    utils = list_hs_from("utils")
    return chain(libs, utils)

def module_to_project(hs_files, project_name):
    project_name = re.sub(r"\.", "/", project_name) + ".hs"

    for file_candidate in hs_files:
        if project_name in file_candidate:
            file_candidate = path(file_candidate)
            
            curr_dir = file_candidate.parent
            while curr_dir != prefix:
                curr_dir_files = curr_dir.files(pattern="*.tcabal")
                if curr_dir_files:
                    for tcabal in curr_dir_files:
                        yield tcabal.namebase
                    break
                curr_dir = curr_dir.parent

def main__project(args):
    
    hs = list(hs_files())

    projects = [
        ' OR '.join(module_to_project(hs, project))
        for project in args['<name>']
    ]
    
    for imp, proj in zip(args['<name>'], projects):
        print("-- {proj}\n{imp}\n".format(**locals()))


regex_imports = r"^(import\s+)(qualified\s+ )?(\S+)(.*)"
regex_comment = r"^\s*(--.*)?\Z"

def parse_import_getmodule(line, proj=None):
    regex = re.findall(regex_imports, line)
    if regex:
        imp = regex[0]
        return imp[2]


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Flowbox library helper ver. 1')

    if arguments['whichproject']:
        """ Each arg is a module. Re-display that with project name. """
        main__project(arguments)

    elif arguments['whichprojects']:
        """ Read modules from stdin and output that with project name. """
        hs = list(hs_files())
        for line in fileinput.input("-"):
            mod = parse_import_getmodule(line)
            if mod:
                proj = ' OR '.join(module_to_project(hs, mod))
                if not proj:
                    proj = "??"
                print("-- {proj}\n{line}".format(**locals()), end="")
            else:
                print(line, end="")

    elif arguments['whichprojectsfile']:
        """ Read module content from stdin and group imports. """

        hs = list(hs_files())
        lines = list(fileinput.input("-"))
        lines_comm   = [bool(re.findall(regex_comment, line)) for line in lines]
        lines_import = [bool(re.findall(regex_imports, line)) for line in lines]

        # find range to change imports
        i, start_range, stop_range = 0, len(lines)-1, 0
        while not lines_import[i]: i += 1
        start_range = i
        while lines_comm[i] or lines_import[i]: i += 1
        stop_range = i



        lines_nonempty = [x for x in lines[start_range:stop_range] if x.strip()]
        lines_modules  = [parse_import_getmodule(x) for x in lines_nonempty]
        lines_projects = [' OR '.join(module_to_project(hs, x)) or '??' for x in lines_modules]

        imports_sorted = sorted(
                            zip(lines_nonempty, lines_projects),
                            key=itemgetter(1)
                        )
        imports_grouped = [list(g) for k, g in groupby(imports_sorted, key=itemgetter(1))]

        res = []
        for import_group in imports_grouped:
            res.append("\n-- {import_group[0][1]}\n".format(**locals()))
            for xxx in import_group:
                res.append(xxx[0])

        # lines[start_range:stop_range] = res

        # for line in lines:
        #     print(line, end="")
        
        for line in res:
            print(line, end="")
        