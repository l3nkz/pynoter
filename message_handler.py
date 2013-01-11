#########################################################################
# pynoted -- message handler
#
# The message handler of the pynoter package. This class was designed to
# correctly display the messages from all clients. The problem which
# occured during the development of this library was that messages could
# be lost of they aren't enqueued correctly. Therefore a worker thread was
# designed to face this problem. This thread has a message queue and displays
# the messages in the correct order and checks if everything shown the way
# the user wants to see it.
#
# License: GPLv2
# Contact: till.smejkal@gmail.com
#########################################################################

from threading import Thread, Lock, Semaphore

import time

import _debug as debug


class MessageHandler(Thread):

    # Semaphore which indicates how many messages are in the queue
    wait_sem = Semaphore(0)

    # locks for securing the active, the timeout and the messages
    # variable
    active_lock = Lock()
    messages_lock = Lock()
    timeout_lock = Lock()

    # the program name, and the subject which was last displayed
    active_client = None
    active_subject = None

    # the timeout which should be waited till the next message could
    # be shown
    timeout = None

    # the working queue
    messages = []

    # the amount of client handlers which use this message handler
    client_handlers = 0

    def __init__(self):
        debug.debug_msg("[MessageHandler]Initiate MessageHandler")

        Thread.__init__(self)

        MessageHandler.running = True

    def register(self):
        debug.debug_msg("[MessageHandler]New ClientHandler registered")

        # increase the number of client handlers which use this
        # MessageHandler handler
        MessageHandler.client_handlers += 1

    def unregister(self):
        debug.debug_msg("[MessageHandler]ClientHandler unregistered")

        # decrease the number of client handlers which use this message handler
        MessageHandler.client_handlers -= 1

    def stop(self):
        debug.debug_msg("[MessageHandler]Stopping MessageHandler Thread")

        MessageHandler.running = False
        MessageHandler.wait_sem.release()

    def enqueue(self, client, message):
        debug.debug_msg("[MessageHandler]Recieved new Message from %s"
                        % (client,))

        # enqueue a new message
        MessageHandler.active_lock.acquire()

        # check whether the notification which is shown at the moment is the
        # same as the one which should be displayed next.
        if client == MessageHandler.active_client and\
           message.subject == MessageHandler.active_subject:
            # they are the same, so directly display this message
            debug.debug_msg("[MessageHandler]Directly display message " +
                            "S:%s M:%s from %s" % (message.subject,
                                                   message.message, client))
            MessageHandler.active_lock.release()
            self._display(message)
        else:
            # otherwise enqueue the message
            MessageHandler.active_lock.release()
            MessageHandler.messages_lock.acquire()
            debug.debug_msg("[MessageHandler]Append new message " +
                            "S:%s M:%s from %s to queue[%i]"
                            % (message.subject, message.message,
                               client, len(MessageHandler.messages)))
            MessageHandler.messages.append((client, message))
            MessageHandler.messages_lock.release()
            MessageHandler.wait_sem.release()

    def run(self):
        debug.debug_msg("[MessageHandler]Starting MessageHandler Thread")

        # run till no client handler uses this message handler any more
        while MessageHandler.running or len(MessageHandler.messages) > 0:
            # enter the semaphore. This blocks the thread if no message is
            # there to progress and directly wakes the thread up if a new
            # message is added to the queue.
            MessageHandler.wait_sem.acquire()
            if not MessageHandler.running and\
               len(MessageHandler.messages) <= 0:
                break

            # get the next program which should be displayed
            MessageHandler.messages_lock.acquire()

            (active_client, message) = MessageHandler.messages[0]

            MessageHandler.active_lock.acquire()

            # save that this program is active at the moment
            MessageHandler.active_client = active_client
            MessageHandler.active_subject = message.subject

            # release all locks and messages
            MessageHandler.active_lock.release()
            MessageHandler.messages_lock.release()
            MessageHandler.wait_sem.release()

            # get the message lock back, because we perform actions on the
            # message queue
            MessageHandler.messages_lock.acquire()

            # display all messages which are enqueued for the same program and
            # have the same subject

            i = 0

            while len(MessageHandler.messages) > i:
                (client, message) = MessageHandler.messages[i]
                if client == MessageHandler.active_client and\
                   message.subject == MessageHandler.active_subject:
                    # count down the wait semaphore
                    MessageHandler.wait_sem.acquire()
                    # remove the message from the queue
                    del MessageHandler.messages[i]
                    debug.debug_msg("[MessageHandler]Display message " +
                                    "S:%s M:%s from %s"
                                    % (message.subject,
                                       message.message,
                                       client))

                    # at the end display the message
                    self._display(message)
                    time.sleep(0.25)
                else:
                    # otherwise step to the next element in the list
                    i += 1

            MessageHandler.messages_lock.release()

            # wait till all notifications vanishes again
            MessageHandler.timeout_lock.acquire()

            while MessageHandler.timeout is not None:
                timeout = MessageHandler.timeout
                MessageHandler.timeout = None
                MessageHandler.timeout_lock.release()

                time.sleep(timeout)

                MessageHandler.timeout_lock.acquire()

            MessageHandler.timeout_lock.release()

            # restore the active name to default
            MessageHandler.active_lock.acquire()
            MessageHandler.active_client = None
            MessageHandler.active_subject = None
            MessageHandler.active_lock.release()

    def _display(self, message):
        # just display the message
        message.display()

        # update the timeout for the notification
        MessageHandler.timeout_lock.acquire()
        MessageHandler.timeout = message.timeout/1000
        MessageHandler.timeout_lock.release()
