#########################################################################
# pynoted -- client handler
#
# The client handler of the pynoter package. This class was designed to
# handle the requests of clients for displaying messages.
#
# License: GPLv2
# Contact: till.smejkal@gmail.com
#########################################################################

from dbus.service import Object, BusName, method

from threading import Thread, Lock, Semaphore

import pynotify
from pynotify import Notification

import time

class ClientHandler(Object):

    worker = None

    def __init__(self, bus, object_path):
        # Initialize the dbus connection
        busName = BusName('org.pynoter.listener', bus=bus)
        Object.__init__(self,busName, '/'+object_path)

        self.connected = True

        # Initialize the notification
        pynotify.init("handler_"+object_path)
        self.notification = Notification("")

        # save the constructor parameters, so we can access them later
        self.bus = bus
        self.object_path = object_path

        # check whether worker thread is already started
        if ClientHandler.worker is None:
            # create the thread, register and start him
            ClientHandler.worker = MessageHandler()
            ClientHandler.worker.register()
            ClientHandler.worker.start()
        else:
            # worker thread already started so just register
            ClientHandler.worker.register()

    def __del__(self):
        # if we're still connected to DBus, remove this connection
        if self.connected:
            self.remove()

    def remove(self):
        # remove the handlers DBus path
        self.remove_from_connection(self.bus, '/'+self.object_path)

        # tell the worker thread, that we finished.
        ClientHandler.worker.unregister()

    @method(dbus_interface='org.pynoter.listener', in_signature='sssibb')
    def send_message(self, subject, message, icon="",
                     timeout=6000, append=True, update=False):

        # create the message
        message = Message(self, subject, message, icon, timeout,
                                   append, update)

        # enqueue the message to the worker threads queue
        ClientHandler.worker.enqueue(self.object_path, message)



class MessageHandler(Thread):

    # Semaphore which indicates how many messages are in the queue
    wait_sem = Semaphore(0)

    # locks for securing the active and the messages variable
    active_lock = Lock()
    messages_lock = Lock()

    # the program name, and the subject which was last displayed
    active_client = None
    active_subject = None

    # the working queue
    messages = []

    # the amount of client handlers which use this message handler
    client_handlers = 0

    def __init__(self):
        Thread.__init__(self)

    def register(self):
        # increase the number of client handlers which use this message handler
        MessageHandler.client_handlers += 1

    def unregister(self):
        # decrease the number of client handlers which use this message handler
        MessageHandler.client_handlers -= 1

    def enqueue(self, client, message):
        # enqueue a new message
        MessageHandler.active_lock.acquire()

        # check whether the notification which is shown at the moment is the
        # same as the one which should be displayed next.
        if client == MessageHandler.active_client and\
           message.subject == MessageHandler.active_subject:
            # they are the same, so directly display this message
            print("Directly display message: %s %s" % (client, message.message))
            MessageHandler.active_lock.release()
            self._display(message)
        else:
            # otherwise enqueue the message
            MessageHandler.active_lock.release()
            MessageHandler.messages_lock.acquire()
            print("Append new message to queue: %s %s" % (client, message.message))
            MessageHandler.messages.append((client,message))
            MessageHandler.messages_lock.release()
            MessageHandler.wait_sem.release()

    def run(self):
        # run till no client handler uses this message handler any more
        while MessageHandler.client_handlers >= 1:
            # enter the semaphore. This blocks the thread if no message is
            # there to progress and directly wakes the thread up if a new
            # message is added to the queue.
            MessageHandler.wait_sem.acquire()

            # get the next program which should be displayed
            MessageHandler.messages_lock.acquire()

            (active_client,message) = MessageHandler.messages[0]

            MessageHandler.active_lock.acquire()

            # save that this program is active at the moment
            MessageHandler.active_client = active_client
            MessageHandler.active_subject =  message.subject

            # release all locks and messages
            MessageHandler.active_lock.release()
            MessageHandler.messages_lock.release()
            MessageHandler.wait_sem.release()

            # get the message lock back, because we perform actions on the
            # message queue
            MessageHandler.messages_lock.acquire()

            # display all messages which are enqueued for the same program and
            # have the same subject
            while len(MessageHandler.messages) > 0:
                (client,message) = MessageHandler.messages[0]
                if client == MessageHandler.active_client and\
                   message.subject == MessageHandler.active_subject:
                    # count down the wait semaphore
                    MessageHandler.wait_sem.acquire()
                    # remove the message from the queue
                    del MessageHandler.messages[0]
                    print("Display message: %s %s" % (client, message.message))

                    # at the end display the message
                    self._display(message)
                else:
                    # otherwise stop the while loop
                    break

            MessageHandler.messages_lock.release()

            # wait till the notification vanishes again
            time.sleep(message.timeout/1000)

            # restore the active name to default
            MessageHandler.active_lock.acquire()
            MessageHandler.active_client = None
            MessageHandler.active_subject = None
            MessageHandler.active_lock.release()

            print("Displaying for %s done." % (client,))

    def _display(self, message):
        # just display the message
        message.display()



class Message(object):
    def __init__(self, caller, subject, message, icon="", timeout=6000,
                 append=True, update=False):
        self.subject = subject
        self.message = message
        self.icon = icon
        self.timeout = timeout
        self.append = append
        self.update = update
        self.caller = caller

    def display(self):

        # should the last notification be updated
        if self.update:
            self.caller.notification.update(self.subject, self.message, self.icon)
        else:
            # if not than create a new notification
            self.caller.notification = Notification(self.subject, self.message, self.icon)

            # should this notification be appended to the last one
            if self.append:
                self.caller.notification.set_hint_string("x-canonical-append", "true")

        # set timeout of the notification
        self.caller.notification.set_timeout(self.timeout)

        # and finally display the notification
        self.caller.notification.show()
