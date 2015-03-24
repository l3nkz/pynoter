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
    def __init__(self, program_name, server_bus_suffix = None,
            multi_client = False, lingering = False, use_system_bus = False):
        """
        Constructor for the class. The connection to the server is
        established here.

        :param program_name: The name of the program for which messages
                            should be displayed.
        :type program_name: str
        :param server_bus_suffix: An optional name suffix where the server is
                                  located. This is only needed if there are
                                  multiple servers on the same Bus.
                                  (Defaults to None)
        :type server_bus_suffix: str
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
        self._register(program_name, server_bus_suffix, multi_client, lingering)

                                        #  sent last.

    def __del__(self):
        """
        Destructor for the class. The connection to the server is
        released here.
        """
        # Unregister before quitting.
        self._unregister()

    def _register(self, program_name, server_bus_suffix, multi_client,
            lingering):
        """
        Register the current client at the server.

        :param program_name: The name which should be used for registration.
        :type program_name: str
        :param server_bus_suffix: An optional name suffix where the server is
                                  located. This is only needed if there are
                                  multiple servers on the same Bus.
                                  (Defaults to None)
        :type server_bus_suffix: str
        :param multi_client: Flag which indicates if there will be more clients
                             registering for the same client_name, which should
                             be treated as one client.
        :type multi_client: bool
        :param lingering: Flag which indicates, that the handler for this
                          client should stay alive even if the current client
                          vanishes.
        :type lingering: bool
        """
        if server_bus_suffix is None:
            server_bus = 'org.pynoter'
        else:
            server_bus = 'org.pynoter.' + server_bus_suffix

        # Connect to the server.
        server = Interface(
                self._dbus_bus.get_object(server_bus, '/'),
                dbus_interface='org.pynoter.server'
        )

        # Get the handler for this client.
        handler_path = server.get_handler(program_name, multi_client,
                lingering)
        handler = Interface(
                self._dbus_bus.get_object(server_bus, handler_path),
                dbus_interface='org.pynoter.client_handler'
        )

        # Register at the handler.
        self._id = handler.register()
        self._handler = handler

    def _unregister(self):
        """
        Unregister the current client from the server.
        """
        self._handler.unregister(self._id)

    def display_message(self, subject, body, icon = "", timeout = 6000,
            append = False, update = False, reference = None):
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
                       (Defaults to False)
        :type append: bool
        :param update: A flag which indicates that this message should update
                       (replace) the last message. Keep in mind, that this will
                       replace all the currently visible messages and not only
                       the last one which was sent. (Defaults to False)
        :type update: bool
        :param reference: The identifier of the message which should be updated
                          or to which this one should be appended. Use 'None' to
                          indicate that the id of the last message should be
                          used and use '""' to indicate that no reference is
                          given. (Defaults to None)
        :type reference: str
        :rtype: str
        :return: The unique identifier for this message.
        """
        # As it is not possible to send None via DBus, change the meaning of
        # the reference variable accordingly.
        if reference is None:
            reference = ""
        elif reference == "":
            reference = "not-set"

        # Send the message to the handler and return the its unique message id
        # to the client so that it can use it as reference later.
        return self._handler.display_message(self._id, subject, body, icon,
                timeout, append, update, reference)

