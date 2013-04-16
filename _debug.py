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

# global flag which indicates whether we want debug information or not.
debug = False


def debug_msg(message):
    """
    Method for displaying a debug message. This method will print the given
    message to stdout if the debug flag is set.

    @param message:     The debug message which should be displayed.
    """
    if debug:
        print(message)


def error_msg(message):
    """
    Method for displaying error messages. This method will print the given
    message to stderr even if the debug flag is not set.

    @param message:     The error message which should be displayed.
    """
    sys.stderr.write(message)
