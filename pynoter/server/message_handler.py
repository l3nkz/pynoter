#!/usr/bin/env python3

###############################################################################
# pynoter -- message handler
#
# The message handler of the pynoter package. This class was designed to
# correctly display the messages from all clients. The problem which
# occurred during the development of this library was that messages could
# be lost if they aren't enqueued correctly. Therefore a worker thread was
# designed to face this problem. This thread has a message queue and displays
# the messages in the correct order and checks if everything is shown the way
# the user wants to see it.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
###############################################################################

from threading import Thread, Lock, RLock, Semaphore

from time import sleep, time

import logging


logger = logging.getLogger(__name__)


__all__ = ['MessageHandler']


class Item:
    """
    The interface which an item of the queue must implement.
    """

    def __call__(self, message_handler):
        """
        Function call operator.

        Here everything should be done what the item wants to do. This function
        is called in the run method of the MessageHandler class.

        :param message_handler: The MessageHandler instance which wants to
                                execute the items tasks.
        :type message_handler: MessageHandler
        """
        raise NotImplementedError()


class MessageItem(Item):
    """
    An item which can be put in the queue representing a message which should
    be displayed.
    """

    def __init__(self, handler, message):
        """
        Constructor of this class.

        :param handler: The client handler serving the client of this message.
        :type handler: ClientHandler
        :param message: The message which should be displayed.
        :type message: Message
        """
        self._id = handler.id + "-" + message.id
        self._ref_id = handler.id + "-" + message.reference

        self._handler = handler
        self._message = message

    def __call__(self, message_handler):
        """
        Function call operator.

        Show the message and all the others part of the closure and wait until
        the message vanishes again, before continuing execution.

        :param message_handler: The MessageHandler instance which wants to
                                execute the item.
        :type message_handler: MessageHandler
        """
        message_handler._show_with_closure(self)
        message_handler._wait()
        message_handler._reset_current()

    @property
    def id(self):
        """
        Get the identifier of this message item.

        :rtype: str
        :return: The identifier of this message item.
        """
        return self._id

    @property
    def message(self):
        """
        Get the contained message.

        :rtype: Message
        :return: The message contained in this item.
        """
        return self._message

    @property
    def ref_id(self):
        """
        Get the identifier of the message item which is referenced by this one.

        :rtype: str
        :return: The identifier of the referenced message item.
        """
        return self._ref_id


def revises(item1, item2):
    """
    Check if the first given item revises the second one.

    :param item1: The item which may revises the other one.
    :type item1: MessageItem
    :param item2: The item which may be revised by the other one.
    :type item2: MessageItem
    :rtype: bool
    :return: Whether or not the first item revises the second one.
    """
    if not isinstance(item1, MessageItem) or \
            not isinstance(item2, MessageItem):
        return False

    if item1 is None or item2 is None:
        return False

    if item1.message.revises:
        return item1.ref_id == item2.id

    return False


def closure(item, queue):
        """
        Calculate the transitive closure for the revise relation on the
        given queue.

        :param item: The item for which the closure should be calculated.
        :type item: MessageItem
        :param queue: The queue containing the other elements.
        :type queue: Queue
        :rtype: list[MessageItem]
        :return: The list with all items part of the closure.
        """
        others = [i for i in queue if revises(i, item)]

        for i in others[:]:
            # Remove the item from the queue.
            queue.remove(i)

            # Find all items revising the found ones recursively.
            others.extend(closure(i, queue))

        return [item] + others


class HandlerStopItem:
    """
    An item which can be put into the queue, which will cause the MessageHandler
    to stop its execution.
    """

    def __call__(self, message_handler):
        """
        Function call operator.

        Cause the given MessageHandler instance to stop its execution.

        :param message_handler: The MessageHandler instance which wants to
                                execute the item.
        :type message_handler: MessageHandler
        """
        message_handler._should_stop = True


class Queue:
    """
    An asynchronous FIFO message queue working according to the producer
    consumer pattern.
    """

    def __init__(self):
        """
        Constructor of this class. It will set up the internal data structure
        as well as all synchronization variables.
        """
        self._queue = []                #< The internal list of messages.

        self._semaphore = Semaphore(0)  #< The counting semaphore used to reach
                                        #  the producer consumer pattern without
                                        #  busy waiting.

        self._lock = Lock()            #< The lock to protect the internal list.

    def __iter__(self):
        """
        Get an iterator for the queue.

        During iteration the internal lock will be hold. Hence no inserts
        or removals should be done, otherwise a deadlock will occur.
        """
        with self._lock:
            for i in self._queue:
                yield i

    def enqueue(self, item):
        """
        Add an item to the tail of the queue.

        :param item: The item which should be added.
        :type item: Item
        """
        with self._lock:
            self._queue.append(item)

        self._semaphore.release()

    def dequeue(self):
        """
        Get another item from the queue. If there are items in the list, the
        head will be returned. Otherwise, this method will block until a new
        item is added.
        """
        self._semaphore.acquire()

        with self._lock:
            return self._queue.pop(0)

    def remove(self, item):
        """
        Remove an item from the list at an arbitrary position.

        This will also count down the internal semaphore.

        :param item: The item which should be removed from the list.
        :type item: Item
        """
        self._semaphore.acquire()

        with self._lock:
            self._queue.remove(item)


class MessageHandler(Thread):
    """
    This class is the worker thread which asynchronously displays the
    notification messages which are received from the clients. It has an
    internal queue where messages can be enqueued and which works according
    to the producer consumer pattern.
    """

    def __init__(self):
        """
        Constructor of the class. Here the thread will be initialized as well
        as all used locks and other synchronization variables.
        """
        logger.debug("Create a new  message handler")

        # Call the super constructor to properly setup the thread.
        super(MessageHandler, self).__init__()

        # Internal variables.
        self._should_stop = False   #< Indicates that the thread should stop
                                    #  its loop.

        self._queue = Queue()       #< The queue of item which must be processed
                                    #  by the consumer thread.

        self._current = None        #< Information about the message which is
                                    #  displayed at the moment.

        self._current_lock = RLock() #< Lock for the information about the
                                    #  currently displayed message as they are
                                    #  accessed from this thread and from
                                    #  others as well.

        self._wait_until = time()   #< Time point until the execution should be
                                    #  interrupted so that messages do not
                                    #  overlap.

        self._wait_lock = Lock()    #< Lock for the wait time point as it is
                                    #  accessed from this thread and from
                                    #  others as well.

    def _reset_current(self):
        """
        Reset the information about the currently shown message to its default.
        """
        with self._current_lock:
            self._current = None

    def _show_without_closure(self, item):
        """
        Display the given notification message together without all the other
        messages part of its closure.

        :param item: The message queue item which should be displayed.
        :type item: MessageItem
        """
        if item.message.display():
            with self._current_lock:
                self._current = item

            with self._wait_lock:
                self._wait_until = time() + (item.message.timeout / 1000) + 1

    def _show_with_closure(self, item):
        """
        Display the given notification message together with all the other
        messages part of its closure.

        :param item: The message queue item which should be displayed.
        :type item: MessageItem
        """
        with self._current_lock:
            # Calculate and display all items of the closure of the queue.
            for i in closure(item, self._queue):
                self._show_without_closure(i)

                # Sleep shortly after displaying this message, to get a smooth
                # displaying for the others.
                sleep(0.2)

    def _wait(self):
        """
        Wait until the message currently displayed vanishes.
        """
        while True:
            with self._wait_lock:
                wait_until = self._wait_until

            current = time()

            if current < wait_until:
                logger.debug("Wait for {} s".format(wait_until - current))

                sleep(wait_until - current)
            else:
                return

    def enqueue(self, handler, message):
        """
        Enqueue a new message from the given client handler in the message
        queue so that it can be displayed soon.

        This method is normally executed on the client handlers thread.

        :param handler: The client handler.
        :type handler: ClientHandler
        :param message: The message object which should be displayed.
        :type message: Message
        """
        logger.debug("Enqueue new message from {}.".format(handler.id))

        item = MessageItem(handler, message)

        with self._current_lock:
            if revises(item, self._current):
                logger.debug("Directly show message from {}.".format(
                    handler.id))

                # The new message will change the currently displayed one.
                # Hence display it directly without adding it to the queue.
                self._show_without_closure(item)

                return

        # Otherwise, just add it to the queue.
        self._queue.enqueue(item)

    def run(self):
        """
        Main execution routine of the message handler.
        """
        logger.debug("Message handler started.")

        while not self._should_stop:
            # Get the next item from the queue. This will block until an item
            # is available for processing.
            item = self._queue.dequeue()

            logger.debug("Dequeued item from queue.")

            # Process the item.
            item(self)

        logger.debug("Message handler stopped.")

    def stop(self):
        """
        Stop the execution of this message handler.
        """
        logger.debug("Stopping message handler.")

        self._queue.enqueue(HandlerStopItem())

