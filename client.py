#########################################################################
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


class Client():
    def __init__(self, progam_name, object_path='/'):
        self.object_path = object_path
        # register on startup
        self._register(progam_name, self.object_path)

    def __del__(self):
        # unregister before quitting
        self._unregister(self.port_name, self.object_path)

    def _register(self, client_name, object_path):
        # get connection to the server
        server = Interface(SessionBus().get_object('org.pynoter.server', object_path),
                           dbus_interface='org.pynoter.server')
        self.port_name = server.register(client_name)

    def _unregister(self, client_name, object_path):
        server = Interface(SessionBus().get_object('org.pynoter.server', object_path),
                           dbus_interface='org.pynoter.server')
        server.unregister(client_name)

    def send_message(self, subject, message, icon="",
                     timeout=6000, append=True, update=False):
        handler = Interface(SessionBus().get_object('org.pynoter.listener', '/'+self.port_name),
                            dbus_interface='org.pynoter.listener')
        handler.send_message(subject, message, icon, timeout, append, update)

