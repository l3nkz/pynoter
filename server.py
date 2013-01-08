#########################################################################
# pynoted -- server
#
# The Server of the pynoter package. This class handles register and
# unregister request of clients and coordinates the control flow.
#
# License: GPL2
# Contact: till.smejkal@gmail.com
#########################################################################

from dbus import SessionBus
from dbus.service import Object, BusName, method
from dbus.mainloop.glib import DBusGMainLoop

from client_handler import ClientHandler

class Server(Object):
    """
    Server class
    """
    def __init__(self, object_path = '/'):
        """
        Initialization method for the class.

        :param object_path: the path where this server should be accessible
        """
        # initialize the dbus name
        self.bus = SessionBus(mainloop = DBusGMainLoop(set_as_default = True))
        busName = BusName('org.pynoter.server', bus=self.bus)
        # forward initialization to parent class
        super(Server, self).__init__(busName, object_path)

        #list of programs with the corresponding message handler
        self.programs = {}
        self.cnt = 0

    def __del__(self):
        # clean up at the end
        pass

    @method(dbus_interface='org.pynoter.server', in_signature='s',
            out_signature='s')
    def register(self, program_name, multi_client=False):
        """
        Method for registering new programs.

        :param program_name: the name of the program which want to be
                             registered.
        :param multi_client: indicates whether this program can have multiple
                             clients. If it is set to True, then will the old
                             client handlers path be returned. This way many clients
                             can use the same client handler. Otherwise a new
                             client handler will be created and a unique path returned.
        """
        if program_name in self.programs:
            # we already have another program with this name
            if multi_client:
                # the program is specified as multi client
                # return the handler of the already registered program
                print("New client for %s registred" % (program_name,))

                # update the number of clients for the program
                (handler, cnt) = self.programs[program_name]
                self.programs[program_name] = (handler, cnt+1)

                return program_name

            # give the program an unique name for its message handler
            self.cnt += 1
            unique_name = program_name + str(self.cnt)

        else:
            # otherwise take the program's name
            unique_name = program_name

        handler = ClientHandler(self.bus, '/'+unique_name)

        # save the handler instance
        self.programs[unique_name] = (handler,1)

        print("New program %s as %s registered." % (program_name,unique_name))
        return unique_name

    @method(dbus_interface='org.pynoter.server', in_signature='s',
            out_signature='b')
    def unregister(self, program_name):
        if program_name in self.programs:
            # get the handler and remove it's path on the DBus channel
            (handler, cnt) = self.programs[program_name]
            if cnt == 1:
                # if this is the last / only client for the program than we
                # can remove it.
                handler.remove()
                # remove the handler again
                del self.programs[program_name]
                print ("Successfully unregistered %s." % (program_name,))
            else:
                # otherwise just decrement the number of clients.
                self.programs[program_name] = (handler, cnt-1)
                print ("Client for %s successfully unregistered" %
                       (program_name,))

            return True

        else:
            print ("Program %s was not registered." % (program_name))
            return False

