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

from dbus import SessionBus, Interface


class Client:
    """
    This class should be used to establish connections to the server
    as well as sending messages to it.
    """
    def __init__(self, program_name, object_path = '/', multi_client = False):
        """
        Constructor for the class. The connection to the server is
        established here.

        :param program_name: The name of the program for which messages
                            should be displayed.
        :type program_name: str
        :param object_path: An optional path where to register at the server.
                            This is only needed if there are multiple servers.
                            (Defaults to '/')
        :type object_path: str
        :param mutli_client: Flag which indicates, whether there will be
                             multiple clients registering for the same name,
                             which should be treated as one client.
                             (Defaults to True)
        :type multi_client: bool
        """
        self.object_path = object_path

        # Register on startup.
        self._register(program_name, self.object_path, multi_client)

    def __del__(self):
        """
        Destructor for the class. The connection to the server is
        released here.
        """
        # Unregister before quitting.
        self._unregister(self.port_name, self.object_path)

    def _register(self, client_name, object_path, multi_client):
        """
        Register the current client at the server.

        :param client_name: The name which should be used for registration.
        :type client_name: str
        :param object_path: An optional path where the registration should go at.
                            This is needed if there are multiple servers.
        :type object_path: str
        :param multi_client: Flag which indicates if there will be more clients
                             registering for the same client_name, which should
                             be treated as one client.
        :type multi_client: bool
        """
        # Connect to the server.
        server = Interface(
                SessionBus().get_object('org.pynoter.server', object_path),
                dbus_interface='org.pynoter.server'
        )

        # The register method returns the port name where we later can send our
        # messages to.
        self.port_name = server.register(client_name, multi_client)

    def _unregister(self, client_name, object_path):
        """
        Unregister the current client from the server.

        :param client_name: The name which was used during the registration.
        :type client_name: str
        :param object_path: The path which was used during the registration.
        :type object_path: str
        """
        # Connect to the server.
        server = Interface(
                SessionBus().get_object('org.pynoter.server', object_path),
                dbus_interface='org.pynoter.server'
        )

        server.unregister(client_name)

    def send_message(self, subject, body, icon = "", timeout = 6000,
            append = True, update = False):
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
        """
        # Connect to the message listener for this client.
        listener = Interface(
                SessionBus().get_object('org.pynoter.listener',
                    '/'+self.port_name),
                dbus_interface='org.pynoter.listener'
        )

        listener.send_message(subject, message, icon, timeout, append, update)

