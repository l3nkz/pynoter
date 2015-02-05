#!/usr/bin/env python3

###############################################################################
# pynoted -- client handler
#
# The client handler of the pynoter package. This class was designed to
# handle the requests of clients for displaying messages.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
###############################################################################

from dbus.service import Object, BusName, method

import gi.repository.Notify as notify
from gi.repository.Notify import Notification

import logging

from pynoter.server.message import Message


logger = logging.getLogger(__name__)


class ClientHandler(Object):

    def __init__(self, bus, object_path, worker):
        logger.debug("[ClientHandler]Initiating DBus connection " +
                "(object_path = %s)" % ('/'+object_path,))

        # Initialize the dbus connection
        busName = BusName('org.pynoter.listener', bus=bus)
        super(ClientHandler, self).__init__(busName, '/'+object_path)

        self.connected = True

        # Initialize the notification
        if not notify.init("handler_"+object_path):
            logger.error("[ClientHandler]Failed to initiate pynotify " +
                    "for %s" % (object_path,))

        # Create a Notification object which will be used by Message class
        # later on
        self.notification = Notification.new("")

        # save the constructor parameters, so we can access them later
        self.bus = bus
        self.object_path = object_path
        self.worker = worker

        # register to the worker
        self.worker.register()

    def __del__(self):
        # if we're still connected to DBus, remove this connection
        if self.connected:
            self.stop()

    def stop(self):
        logger.debug("[ClientHandler]Removing DBus connection " +
                "(object_path = %s)" % ('/'+self.object_path,))

        # remove the handlers DBus path
        self.remove_from_connection(self.bus, '/'+self.object_path)

        logger.debug("[ClientHandler]Unregister from worker for %s"
                        % (self.object_path,))

        # unregister from the worker
        self.worker.unregister()

        # change connected state to False
        self.connected = False

    @method(dbus_interface='org.pynoter.listener', in_signature='sssibb')
    def send_message(self, subject, body, icon="",
                     timeout=6000, append=True, update=False):
        logger.debug("[ClientHandler]Received new Message " +
                "S:%s M:%s from %s" % (subject, body, self.object_path))

        # create the message
        message = Message(self.notification, subject, body, icon, timeout,
                          append, update)

        logger.debug(("[ClientHandler]Enqueue Message S:{} M:{} for {} " +
                "into Worker Thread queue").format(subject, body,
                    self.object_path))

        # enqueue the message to the worker threads queue
        self.worker.enqueue(self.object_path, message)
