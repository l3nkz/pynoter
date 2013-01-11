#########################################################################
# pynoted -- client handler
#
# The client handler of the pynoter package. This class was designed to
# handle the requests of clients for displaying messages.
#
# License: GPLv2
# Contact: till.smejkal@gmail.com
#########################################################################

from dbus.service import Object, BusName, method

import pynotify
from pynotify import Notification

from message import Message
import _debug as debug


class ClientHandler(Object):

    def __init__(self, bus, object_path, worker):
        debug.debug_msg("[ClientHandler]Initiating DBus connection " +
                        "(object_path = %s)" % ('/'+object_path,))

        # Initialize the dbus connection
        busName = BusName('org.pynoter.listener', bus=bus)
        Object.__init__(self, busName, '/'+object_path)

        self.connected = True

        # Initialize the notification
        if not pynotify.init("handler_"+object_path):
            debug.error_msg("[ClientHandler]Failed to initiate pynotify " +
                            "for %s" % (object_path,))

        self.notification = Notification("")

        # save the constructor parameters, so we can access them later
        self.bus = bus
        self.object_path = object_path
        self.worker = worker

        # register to the worker
        self.worker.register()

    def __del__(self):
        # if we're still connected to DBus, remove this connection
        if self.connected:
            self.remove()

    def stop(self):
        debug.debug_msg("[ClientHandler]Removing DBus connection " +
                        "(object_path = %s)" % ('/'+self.object_path,))

        # remove the handlers DBus path
        self.remove_from_connection(self.bus, '/'+self.object_path)

        debug.debug_msg("[ClientHandler]Unregister from worker for %s"
                        % (self.object_path,))
        # unregister from the worker
        self.worker.unregister()

        # change connected state to False
        self.connected = False

    @method(dbus_interface='org.pynoter.listener', in_signature='sssibb')
    def send_message(self, subject, message, icon="",
                     timeout=6000, append=True, update=False):
        debug.debug_msg("[ClientHandler]Received new Message " +
                        "S:%s M:%s from %s"
                        % (subject, message, self.object_path))

        # create the message
        message = Message(self, subject, message, icon, timeout,
                          append, update)

        debug.debug_msg("[ClientHandler]Enqueue Message S:%s M:%s for %s " +
                        "into Worker Thread queue"
                        % (subject, message.message, self.object_path))

        # enqueue the message to the worker threads queue
        self.worker.enqueue(self.object_path, message)
