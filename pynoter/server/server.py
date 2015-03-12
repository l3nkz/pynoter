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
from dbus.exceptions import NameExistsException

import gi.repository.GLib as glib

import logging

from threading import Thread

from pynoter.server.client_handler import ClientHandler
from pynoter.server.message_handler import MessageHandler


logger = logging.getLogger(__name__)


class Server(Object, Thread):
    """
    This class provides the basic entrance point for clients. Hence it handles
    all the clients and controls everything.
    """

    def __init__(self, bus_suffix = None, use_system_bus = False):
        """
        Constructor of the class. Within this method the DBus connection will
        be initiated as well as other setup.

        :param bus_suffix: A suffix which should be added to the normal
                           'org.pynoter' bus name. This is only necessary if
                           there are multiple pynoter servers on the same
                           DBus-Bus. (Defaults to None)
        :type bus_suffix: str
        :param use_system_bus: Flag which indicates, that the server should use
                               the DBus system bus instead of the normal
                               session bus. This must be done if this server is
                               started as a system wide daemon.
                               (Defaults to False)
        :type use_system_bus: bool
        """
        # Initialize the DBus connection.

        # Create the bus name.
        if bus_suffix is None:
            name = "org.pynoter"
        else:
            name = "org.pynoter." + bus_suffix

        # Determine which bus to use.
        if use_system_bus:
            self._dbus_bus = SystemBus(mainloop=DBusGMainLoop(set_as_default=True))

            logger.debug("Start server using system bus at {}.".format(name))
        else:
            self._dbus_bus = SessionBus(mainloop=DBusGMainLoop(set_as_default=True))

            logger.debug("Start server using session bus at {}.".format(name))

        try:
            bus_name = BusName(name, bus=self._dbus_bus, do_not_queue=True)
        except NameExistsException:
            logger.error(("A server with the name '{}' already exists on this" +
                    " bus.").format(name))

            raise ValueError("A server with the given name already exists on" +
                    " the bus. You must choose a different name or a different" +
                    " bus.")

        # Finalize the DBus initialization.
        Object.__init__(self, bus_name, '/')

        # Initialize the thread.
        Thread.__init__(self)

        # Internal variables
        self._bus_name = bus_name
        self._client_handlers = []
        self._message_handler = MessageHandler()
        self._running = False

        self._main_loop = glib.MainLoop.new(None, False)
        glib.threads_init()

    def __del__(self):
        """
        Destructor of the class. Properly shutdown everything.
        """
        self.stop()

    # DBus Interface

    @method(dbus_interface='org.pynoter.server', in_signature='sbb',
            out_signature='s')
    def get_handler(self, program_name, multi_client, lingering):
        """
        Get the address of a handler for the given program.

        :param program_name: The name of the program for which a client wants
                             to know the handler.
        :type program_name: str
        :param multi_client: Flag which indicates if there will be more clients
                             registering for the same client_name, which should
                             be treated as one client.
        :type multi_client: bool
        :param lingering: Flag which indicates, that the handler for this
                          client should stay alive even if the current client
                          vanishes.
        :type lingering: bool
        :rtype: str
        :return: The address of the handler for this particular program.
        """
        # Check if a handler already exists.
        for handler in self._client_handlers:
            if handler.can_handle(program_name, multi_client, lingering):
                return handler.path

        # No handler found, so create a new one.
        handler = ClientHandler(program_name, multi_client, lingering,
                self._message_handler, self._bus_name, self)

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

    def run(self):
        """
        The processing threads main run method.

        This method should not be called directly as it gets called by the
        start method of the Thread class after the thread has been successfully
        created and dispatched.
        """
        logger.debug("Enter main loop...")
        self._main_loop.run()
        logger.debug("Exit main loop...")

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

            # Call Thread's start method so that the server thread is started.
            Thread.start(self)

    def stop(self):
        """
        Safely stop a running server again.
        """
        # Just stop if we are currently running.
        if self._running:
            self._running = False

            logger.debug("Stopping server...")

            logger.debug("Tear down DBus connection.")
            self.remove_from_connection(self._dbus_bus, self._object_path)

            logger.debug("Stop message handler.")
            self._message_handler.stop()
            if self._message_handler.isAlive():
                self._message_handler.join()

            logger.debug("Stop main loop.")
            self._main_loop.quit()

            logger.debug("Stopping done.")

