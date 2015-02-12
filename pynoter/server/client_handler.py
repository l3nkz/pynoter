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

from uuid import uuid4

from pynoter.server.message import Message


logger = logging.getLogger(__name__)


class ClientHandler(Object):
    """
    This class acts as the communication partner for the client. It handles
    registering and unregister of them as well as provides the facility to
    display the notification messages. The class itself is again handled by
    the corresponding server.
    """

    @staticmethod
    def create_unique_id(program_name):
        """
        Create a unique identifier for a client handler.

        :param program_name: The name of the program which the client handler
                             handles.
        :type program_name: str
        :rtype: str
        :return: The unique identifier.
        """
        return program_name + '_' + str(uuid4()).replace('-', '_')

    @staticmethod
    def create_uniqe_client_id():
        """
        Create a unique identifier for a client.

        :rtype: str
        :return: The unique identifier.
        """
        return str(uuid4()).replace('-', '_')


    def __init__(self, program_name, multi_client, message_handler, bus_name,
            server):
        """
        Constructor of the class. Here the DBus connection will be set up
        as well as other maintenance operations.

        :param program_name: The name of the program for which this handler
                             should handle clients.
        :type program_name: str
        :param multi_client: Flag which indicates whether or not this handler
                             should serve multiple clients of the given
                             program.
        :type multi_client: bool
        :param message_handler: The message handler thread, which handles the
                                displaying of the notifications of the clients.
        :type message_handler: MessageHandler
        :param bus_name: The DBus bus name where the current server is located.
        :type bus_name: BusName
        :param server: The server object for which the handler is working.
        :type server: Server
        """
        logger.debug(("Create a new client handler. (program: {}, " +
                "bus_name: {})").format(
                    program_name, bus_name.get_name()))

        # First get the unique object path for this handler.
        self._id = ClientHandler.create_unique_id(program_name)
        self._object_path = '/' + self._id

        # Create the DBus connection.
        super(ClientHandler, self).__init__(bus_name, self._object_path)

        # Initialize the notifications
        if not notify.init("client_handler_" + self._id):
            logger.error("Failed to initialize notifications.")
            raise RuntimeError("Failed to initialize notifications")

        self._notification = Notification.new("", "")

        # Internal variables
        self._program_name = program_name
        self._bus_name = bus_name
        self._message_handler = message_handler
        self._server = server

        self._clients = []
        self._multi_client = multi_client
        self._lingering = False
        self._last_message = ""

        self._add_to_server()

    def _add_to_server(self):
        """
        Add this handler to the current pynoter server.
        """
        # Register at the server, as the setup is done.
        self._server.add_client_handler(self)

    def _remove_from_server(self):
        """
        Remove this handler from the current pynoter server and from DBus.
        """
        self._server.remove_client_handler(self)

        # Tear down the DBus connection.
        self.remove_from_connection(self._bus_name.get_bus(), self._object_path)

    # DBus Interface

    @method(dbus_interface='org.pynoter.client_handler', in_signature='s')
    def disable_multi_client(self, client):
        """
        Disable that this handler can serve multiple clients of the same
        program. All clients which registered already are kept.

        :param client: The unique identifier of the client.
        :type client: str
        """
        if not client in self._clients:
            raise ValueError("This is not a registered client.")

        self._multi_client = False

    @method(dbus_interface='org.pynoter.client_handler', in_signature='s')
    def enable_multi_client(self, client):
        """
        Enable that this handler can serve multiple clients of the same
        program.

        :param client: The unique identifier of the client.
        :type client: str
        """
        if not client in self._clients:
            raise ValueError("This is not a registered client.")

        self._multi_client = True

    @method(dbus_interface='org.pynoter.client_handler', in_signature='s')
    def disable_lingering(self, client):
        """
        Disable that this handle supports lingering for clients.

        :param client: The unique identifier of the client.
        :type client: str
        """
        if not client in self._clients:
            raise ValueError("This is not a registered client.")

        self._lingering = False

    @method(dbus_interface='org.pynoter.client_handler', in_signature='s')
    def enable_lingering(self, client):
        """
        Enable this handler to support lingering for clients.

        This feature is useful if you have clients which register and
        unregister regularly but which still should be managed by the same
        handler.

        :param client: The unique identifier of the client.
        :type client: str
        """
        if not client in self._clients:
            raise ValueError("This is not a registered client.")

        self._lingering = True

    @method(dbus_interface='org.pynoter.client_handler', in_signature='ssssibbs',
            out_signature='s')
    def display_message(self, client, subject, body = "", icon = "",
            timeout = 6000, append = True, update = False, reference = ""):
        """
        Display a notification message.

        :param client: The unique identifier of the client.
        :type client: str
        :param subject: The subject of the message.
        :type subject: str
        :param body: The body of the message. (Defaults to "")
        :type body: str
        :param icon: The icon which should be displayed with the message. This
                     can be either a name or a path. (Defaults to "")
        :type icon: str
        :param timeout: The time in ms how long the notification message should
                        be visible. (Defaults to 6000)
        :type timeout: int
        :param append: Flag which indicates whether this message should be
                       appended to the last one if possible. (Defaults to True)
        :type append: bool
        :param update: Flag which indicates whether this message should replace
                       the last one if possible. (Defaults to False)
        :type update: bool
        :param reference: The unique identifier of the message which this message
                          should replace or be appended to. This is only
                          important if one of these flags are set.
                          (Defaults to the id of the last displayed message)
        :type reference: str
        :rtype: str
        :return: The unique identifier of the message which is going to be
                 displayed.
        """
        if not client in self._clients:
            raise ValueError("This is not a registered client.")

        logger.debug("Received new message from {}.".format(client))

        # Create the message object and enqueue it at the message handlers
        # queue. Use the id of the last message as reference if this was not
        # given by the user.
        if reference == "":
            reference = self._last_message

        message = Message(self._notification, subject, body, icon, timeout,
                append, update, reference)
        self._last_message = message.id

        self._message_handler.enqueue(self, message)

        return message.id

    @method(dbus_interface='org.pynoter.client_handler', out_signature='s')
    def register(self):
        """
        Register a client at this handler.

        :rtype: str
        :return: The unique identifier for the client.
        """
        logger.debug("A client registers for {} (handler: {})".format(
            self._program_name, self._id))

        if len(self._clients) >= 1 and not self._multi_client:
            # There is already a client registered and this handler can not
            # handle multiple of them. So refuse to handle this client.
            logger.error(("Another client tries to register although this " +
                    "handler can not handle multiple clients. +"
                    "(handler: {})").format(self._id))
            raise ValueError("This handler only serves one client.")

        # Create and save the unique identifier for the client.
        client_id = ClientHandler.create_uniqe_client_id()
        self._clients.append(client_id)

        return client_id

    @method(dbus_interface='org.pynoter.client_handler', in_signature='s')
    def unregister(self, client):
        """
        Unregister a client at this handler.

        :param client: The unique identifier of the client.
        :type client: str
        """
        if not client in self._clients:
            raise ValueError("This is not a registered client.")

        logger.debug("A client unregisters for {} (handler: {})".format(
            self._program_name, self._id))

        self._clients.remove(client)

        if len(self._clients) == 0 and not self._lingering:
            logger.debug(("Remove this handler as the last client unregistered. " +
                    "(handler: {})").format(self._id))
            # The last client unregistered and lingering is not supported.
            # Remove this handler from the server.
            self._remove_from_server()

    # Normal Interface

    def can_handle(self, program_name, multi_client):
        """
        Check whether this handler can handle a client for the given program.

        :param program_name: The name of the program for which a client wants
                             to be handled.
        :type program_name: str
        :param multi_client: Whether or not the this handler should be able
                             to serve multiple clients.
        :type multi_client: bool
        :rtype: bool
        :return: Whether or not this handler can handle the client.
        """
        if program_name == self._program_name and \
                multi_client == self._multi_client:
            if len(self._clients) == 0 and self._lingering:
                return True

            if self._multi_client:
                return True

        return False

    @property
    def id(self):
        """
        Get the unique name of this handler.

        :rtype: str
        :return: The unique name of this handler.
        """
        return self._id

    @property
    def is_multi_client(self):
        """
        Check whether or not this handler can serve multiple clients.

        :rtype: bool
        :return: Whether this handler can serve multiple clients.
        """
        return self._multi_client

    @property
    def is_lingering(self):
        """
        Check whether or not this handler supports lingering for its clients.

        :rtype: bool
        :return: Whether this handler supports lingering for clients.
        """
        return self._lingering

    @property
    def path(self):
        """
        Get the object path where this handler can be reached.

        :rtype: str
        :return: The object path where this handler can be reached.
        """
        return self._object_path

