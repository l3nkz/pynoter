#!/usr/bin/env python3

###############################################################################
# pynoted -- message
#
# The message container of the pynoter package. This class was designed to
# encapsulate messages of clients which should be displayed.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
###############################################################################

from gi.repository.Notify import Notification

import logging


logger = logging.getLogger(__name__)


class Message(object):
    def __init__(self, notification, subject, body, icon="", timeout=6000,
                 append=True, update=False):
        self.subject = subject
        self.body = body
        self.icon = icon
        self.timeout = timeout
        self.append = append
        self.update = update
        self.notification = notification

        logger.debug("[Message]Created new Message S:%s M:%s"
                % (subject, body))

    def display(self):
        logger.debug("[Message]Display Message S:%s M:%s"
                % (self.subject, self.body))

        # should the last notification be updated
        if self.update:
            logger.debug("[Message]Update old Message")
            self.notification.update(self.subject,
                    self.body, self.icon)
        else:
            # if not than create a new notification
            self.notification = Notification.new(self.subject,
                    self.body, self.icon)

            # should this notification be appended to the last one
            if self.append:
                logger.debug("[Message]Set append hint")
                self.notification.set_hint_string("x-canonical-append",
                        "true")

        # set timeout of the notification
        self.notification.set_timeout(self.timeout)

        # and finally display the notification
        if not self.notification.show():
            logger.error("[Message]Failed to display Message S:%s M:%s"
                    % (self.subject, self.body))
