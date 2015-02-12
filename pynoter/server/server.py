#!/usr/bin/env python3

###############################################################################
# pynoter -- server
#
# The Server of the pynoter package. This class handles register and
# unregister request of clients and coordinates the whole scene.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
###############################################################################

from dbus import SessionBus, SystemBus
from dbus.service import Object, BusName, method
from dbus.mainloop.glib import DBusGMainLoop

import gi.repository.GLib as glib

import logging

from pynoter.server.client_handler import ClientHandler
from pynoter.server.message_handler import MessageHandler


logger = logging.getLogger(__name__)


class Server(Object):
    """
    This class provides the basic entrance point for clients. Hence it handles
    all the clients and controls everything.
    """

    def __init__(self, object_path = '/', use_system_bus = False):
        """
        Constructor of the class. Within this method the DBus connection will
        be initiated as well as other setup.

        :param object_path: The path where this server should be accessible.
                            This is only necessary to change, if there are
                            multiple pynoter server on the same DBus-Bus.
                            (Defaults to '/')
        :type object_path: str
        :param use_system_bus: Flag which indicates, that the server should use
                               the DBus system bus instead of the normal
                               session bus. This must be done if this server is
                               started as a system wide daemon.
                               (Defaults to False)
        :type use_system_bus: bool
        """
        # Initialize the DBus connection.
        if use_system_bus:
            self._dbus_bus = SystemBus(mainloop=DBusGMainLoop(set_as_default=True))

            logger.debug(("Initiating DBus-system connection " +
                "(path: {})").format(object_path)
            )
        else:
            self._dbus_bus = SessionBus(mainloop=DBusGMainLoop(set_as_default=True))

            logger.debug(("Initiating DBus-session connection " +
                "(path: {})").format(object_path)
            )

        # Create the bus name.
        bus_name = BusName('org.pynoter', bus=self._dbus_bus)

        # Finalize the DBus initialization.
        super(Server, self).__init__(bus_name, object_path)

        # Internal variables
        self._object_path = object_path
        self._client_handlers = []
        self._message_handler = MessageHandler()
        self._running = False

        self._main_loop = glib.MainLoop()
        glib.threads_init()

    def __del__(self):
        """
        Destructor of the class. Properly shutdown everything.
        """
        self.stop()

    # DBus Interface

    @method(dbus_interface='org.pynoter.server', in_signature='sb',
            out_signature='s')
    def get_handler(self, program_name, multi_client = False):
        """
        Get the address of a handler for the given program.

        :param program_name: The name of the program for which a client wants
                             to know the handler.
        :type program_name: str
        :param multi_client: Flag which indicates whether or not the handler
                             should serve multiple clients from the same
                             program.
        :type multi_client: bool
        :rtype: str
        :return: The address of the handler for this particular program.
        """
        # Check if a handler already exists.
        for handler in self._client_handlers:
            if handler.can_handle(program_name, multi_client):
                return handler.path

        # No handler found, so create a new one.
        handler = ClientHandler(program_name, multi_client, self._dbus_bus,
                self._message_handler, self._object_path, self)

        return handler.path

    # Normal Interface

    def add_client_handler(self, handler):
        """
        Add a new client handler to the internal list.

        :param handler: The client handler which should be added.
        :type handler: ClientHandler
        """
        if not handler in self._client_handlers:
            logger.debug("Add new client handler: {}".format(handler.id))
            self._client_handlers.append(handler)

    def remove_client_handler(self, handler):
        """
        Remove a client handler from the internal list.

        :param handler: The handler which should be removed.
        :type handler: ClientHandler
        """
        if handler in self._client_handlers:
            logger.debug("Remove client handler: {}".format(handler.id))
            self._client_handlers.remove(handler)
            del handler

    def run(self):
        """
        Start the server. This will start the main loop and cause the server
        to wait for messages on the bus.
        """
        try:
            self.start()
        except KeyboardInterrupt:
            self.stop()

    def start(self):
        """
        Start up the whole server so that it can listen for messages.
        """
        # Just start if we are not currently running.
        if not self._running:
            self._running = True

            logger.debug("Starting server...")

            logger.debug("Start message handler.")
            self._message_handler.start()

            logger.debug("Start main loop.")
            self._main_loop.run()

    def stop(self):
        """
        Safely stop a running server.
        """
        # Just stop if we are currently running.
        if self._running:
            self._running = False

            logger.debug("Stopping server...")

            logger.debug("Tear down DBus connection.")
            self.remove_from_connection(self._dbus_bus, self._object_path)

            logger.debug("Stop main loop.")
            self._main_loop.quit()

            logger.debug("Stop message handler.")
            self._message_handler.stop()
            if self._message_handler.isAlive():
                self._message_handler.join()

            logger.debug("Stopping done.")

