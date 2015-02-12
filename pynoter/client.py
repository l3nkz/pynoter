#!/usr/bin/env python3

###############################################################################
# pynoter -- client
#
# The client class of the pynoter package. This class provides the
# connection between the user program and the pynoter server. It handles
# registration and unregistration at the server as well as has a method
# for sending messages.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
###############################################################################

from dbus import SessionBus, SystemBus, Interface


class Client:
    """
    This class should be used to establish connections to the server
    as well as sending messages to it.
    """
    def __init__(self, program_name, server_path = '/', multi_client = False,
            lingering = False, use_system_bus = False):
        """
        Constructor for the class. The connection to the server is
        established here.

        :param program_name: The name of the program for which messages
                            should be displayed.
        :type program_name: str
        :param server_path: An optional path where the server is located.
                            This is only needed if there are multiple servers.
                            (Defaults to '/')
        :type server_path: str
        :param mutli_client: Flag which indicates, whether there will be
                             multiple clients registering for the same name,
                             which should be treated as one client.
                             (Defaults to True)
        :type multi_client: bool
        :param lingering: Flag which indicates, that the handler for this
                          client should stay alive even if the current client
                          vanishes. This can be useful for short living
                          clients. (Defaults to False)
        :type lingering: bool
        :param use_system_bus: Flag which indicates, whether the system bus of
                               DBus or the normal session bus should be used.
                               (Defaults to False)
        :type use_system_bus: bool
        """
        if use_system_bus:
            self._dbus_bus = SystemBus()
        else:
            self._dbus_bus = SessionBus()

        # Internal variables
        self._id = None                 #< The identifier of this client which
                                        #  we get from the handler.

        self._handler = None            #< The client handler which serves us.

        self._last_message = ''         #< The id of the message which was

        # Register at the server.
        self._register(program_name, server_path, multi_client, lingering)

                                        #  sent last.

    def __del__(self):
        """
        Destructor for the class. The connection to the server is
        released here.
        """
        # Unregister before quitting.
        self._unregister()

    def _register(self, program_name, server_path, multi_client, lingering):
        """
        Register the current client at the server.

        :param program_name: The name which should be used for registration.
        :type program_name: str
        :param server_path: An optional object path where the server is located.
                            This is needed if there are multiple servers.
        :type server_path: str
        :param multi_client: Flag which indicates if there will be more clients
                             registering for the same client_name, which should
                             be treated as one client.
        :type multi_client: bool
        :param lingering: Flag which indicates, that the handler for this
                          client should stay alive even if the current client
                          vanishes.
        :type lingering: bool

        """
        # Connect to the server.
        server = Interface(
                self._dbus_bus.get_object('org.pynoter', server_path),
                dbus_interface='org.pynoter.server'
        )

        # Get the handler for this client.
        handler_path = server.get_handler(program_name, multi_client)
        handler = Interface(
                self._dbus_bus.get_object('org.pynoter', handler_path),
                dbus_interface='org.pynoter.client_handler'
        )

        # Register at the handler.
        self._id = handler.register()
        self._handler = handler

        # Enable lingering and multi client support at the handler if wanted
        # by the user.
        if lingering:
            handler.enable_lingering(self._id)

        if multi_client:
            handler.enable_multi_client(self._id)

    def _unregister(self):
        """
        Unregister the current client from the server.
        """
        self._handler.unregister(self._id)

    def display_message(self, subject, body, icon = "", timeout = 6000,
            append = True, update = False, reference = ""):
        """
        Send a new notification message to the pynoter server.

        :param subject: The subject for the message.
        :type subject: str
        :param body: The body of the message.
        :type body: str
        :param icon: The name or path of the icon which should be displayed
                     with the message. (Defaults to '')
        :type icon: str
        :param timeout: The time (in ms) the message should be visible.
                        (Defaults to 6000ms (6s))
        :type timeout: int
        :param append: A flag which indicates that this message should be
                       appended to the last one, if possible.
                       (Defaults to True)
        :type append: bool
        :param update: A flag which indicates that this message should update
                       (replace) the last message. Keep in mind, that this will
                       replace all the currently visible messages and not only
                       the last one which was sent. (Defaults to False)
        :type update: bool
        :param reference: The identifier of the message which should be updated
                          or to which this one should be appended.
                          (If this is omitted the id of the last message
                          handled by the corresponding handler will be used.)
        :type reference: str
        :rtype: str
        :return: The unique identifier for this message.
        """
        # Send the message to the handler and save the message id, so that
        # we are able to refer to this message again.
        return self._handler.display_message(self._id, subject, body, icon,
                timeout, append, update, reference)

