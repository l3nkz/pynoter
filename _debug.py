#########################################################################
# pynoted -- debug
#
# Debug wrappers of the pynoter package. This file contains various
# methods for displaying debug information or error messages.
#
# License: GPLv2
# Contact: till.smejkal@gmail.com
#########################################################################

import sys

debug = False


def debug_msg(message):
    if debug:
        print(message)


def error_msg(message):
    sys.stderr.write(message)
