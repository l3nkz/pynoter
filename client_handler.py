#########################################################################
# pynoted -- client handler
#
# The client handler of the pynoter package. This class was designed to
# handle the requests of clients for displaying messages.
#
# License: GPL2
# Contact: till.smejkal@gmail.com
#########################################################################

from dbus.service import Object, BusName, method

import pynotify
from pynotify import Notification

class ClientHandler(Object):
    def __init__(self, bus, object_path):
        # Initialize the dbus connection
        busName = BusName('org.pynoter.listener', bus=bus)
        super(ClientHandler, self,).__init__(busName, object_path)

        # Initialize the notification
        pynotify.init("handler_"+object_path)
        self.notification = Notification("")

        # save the constructor parameters, so we can access them later
        self.bus = bus
        self.object_path = object_path

    def remove(self):
        self.remove_from_connection(self.bus, self.object_path)

    @method(dbus_interface='org.pynoter.listener', in_signature='sssibb')
    def send_message(self, subject, message, icon="",
                     timeout=6000, append=True, update=False):
        if update:
            self.notification.update(subject, message, icon)
        else:
            self.notification = Notification(subject, message, icon)
            if append:
                self.notification.set_hint_string("x-canonical-append", "true")

        self.notification.set_timeout(timeout)
        self.notification.show()


