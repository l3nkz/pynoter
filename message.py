#########################################################################
# pynoted -- message
#
# The message container of the pynoter package. This class was designed to
# encapsulate messages of clients which should be displayed.
#
# License: GPLv2
# Contact: till.smejkal@gmail.com
#########################################################################

from pynotify import Notification

import _debug as debug


class Message(object):
    def __init__(self, caller, subject, message, icon="", timeout=6000,
                 append=True, update=False):
        debug.debug_msg("[Message]Create new Message S:%s M:%s"
                        % (subject, message))
        self.subject = subject
        self.message = message
        self.icon = icon
        self.timeout = timeout
        self.append = append
        self.update = update
        self.caller = caller

    def display(self):
        debug.debug_msg("[Message]Display Message S:%s M:%s"
                        % (self.subject, self.message))

        # should the last notification be updated
        if self.update:
            debug.debug_msg("[Message]Update old Message")
            self.caller.notification.update(self.subject,
                                            self.message, self.icon)
        else:
            # if not than create a new notification
            self.caller.notification = Notification(self.subject,
                                                    self.message, self.icon)

            # should this notification be appended to the last one
            if self.append:
                debug.debug_msg("[Message]Set append hint")
                self.caller.notification.set_hint_string("x-canonical-append",
                                                         "true")

        # set timeout of the notification
        self.caller.notification.set_timeout(self.timeout)

        # and finally display the notification
        if not self.caller.notification.show():
            debug.error_msg("[Message]Failed to display Message S:%s M:%s"
                            % (self.subject, self.message))
