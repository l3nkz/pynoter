########################################################################
# pynoted -- client
#
# The client class of the pynoter package. This class will be the
# connection between the user program and the pynoted server. It will
# handle register and unregister command as well as sending messages.
#
# License: GPL2
# Contact: till.smejkal@gmail.com
#########################################################################

from dbus import SessionBus, Interface


class Client(object):
    """
    This class should be used to establish connections to the server
    as well as sending messages to him.
    """
    def __init__(self, progam_name, object_path='/', multi_client=False):
        """
        Constructor for the class. The connection to the server will be
        established here.

        @param progam_name:     The name of the program for which messages
                                should be displayed.
        @param object_path:     An optional path to register at the server.
        @param mutli_client:    Flag which indicates, whether there will be
                                multiple clients registering for the same name.
        """
        self.object_path = object_path
        # register on startup
        self._register(progam_name, self.object_path, multi_client)

    def __del__(self):
        """
        Destructor for the class. The connection to the server will be
        released here.
        """
        # unregister before quitting
        self._unregister(self.port_name, self.object_path)

    def _register(self, client_name, object_path, multi_client):
        """
        Method to register at the server.

        @param client_name:     The name which should be used for registration.
        @param object_path:     An optional path where the registration should go at.
                                This is needed if there are multiple servers.
        @param multi_client:    Flag which indicates if there will be more clients
                                registering for the same client_name and should be interpreted
                                as one client.
        """
        # get connection to the server
        server = Interface(SessionBus().get_object('org.pynoter.server',
                                                   object_path),
                           dbus_interface='org.pynoter.server')
        self.port_name = server.register(client_name, multi_client)

    def _unregister(self, client_name, object_path):
        """
        Method to unregister from the server.

        @param client_name:     The name which was used during the registration.
        @param object_path:     The path which was used during the registration.
        """
        server = Interface(SessionBus().get_object('org.pynoter.server',
                                                   object_path),
                           dbus_interface='org.pynoter.server')
        server.unregister(client_name)

    def send_message(self, subject, message, icon="",
                     timeout=6000, append=True, update=False):
        """
        Method for sending a new message which should be displayed to the
        server.

        @param subject:         The subject for the message.
        @param message:         The body of the message.
        @param icon:            The optional icon which should be displayed with
                                the message.
        @param timeout:         The time (in ms) the message should be visible.
        @param append:          A flag which indicates if this message should be appended
                                to the last one, if possible.
        @param update:          A flag which indicates if this message should update
                                (replace) the last message. Keep in mind, that this will also
                                replace all the messages, the last one was appended to, if
                                this was done.
        """
        handler = Interface(SessionBus().get_object('org.pynoter.listener',
                                                    '/'+self.port_name),
                            dbus_interface='org.pynoter.listener')
        handler.send_message(subject, message, icon, timeout, append, update)
