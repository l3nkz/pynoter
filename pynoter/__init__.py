#!/usr/bin/env python3

################################################################################
# pynoter
#
# This is the main module file. Just importing this will provide access to the
# Server and the Client classes.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
################################################################################

from pynoter.client import Client
from pynoter.server import Server


__all__ = ['Client', 'Server']

