#!/usr/bin/env python3

###############################################################################
# pynoted -- message
#
# The message container of the pynoter package. This class was designed to
# encapsulate messages of clients which should be displayed.
#
# License: GPLv3
#
# (c) Till Smejkal - till.smejkal+pynoter@ossmail.de
###############################################################################

from gi.repository.Notify import Notification
from gi.repository.GLib import Variant

from threading import Condition

from enum import IntEnum

from uuid import uuid4

import logging


logger = logging.getLogger(__name__)


class Message:
    """
    This class represents the actual notification message send by the client.
    As these messages are buffered before they are displayed on the screen,
    this representation is necessary. It also handles the interaction with the
    notification daemon.
    """

    class ClosedReason(IntEnum):
        """
        Reasons why the notification bubble is closed.
        """

        @classmethod
        def get(cls, reason):
            """
            Get the enum instance for a given int value.

            :param reason: The integer value for which the enum instance should
                           be found.
            :type reason: int
            :rtype: ClosedReason
            :return: The corresponding enum instance or ClosedReason.Unknown if
                     there is none for the given value.
            """
            for cr in cls:
                if reason == cr.value:
                    return cr

            return cls.Unknown

        Unknown = -1
        Vanished = 1
        Explicit = 3


    @staticmethod
    def create_unique_id():
        """
        Create a unique id for a message object.
        """
        return str(uuid4()).replace('-', '_')

    def __init__(self, client_handler, subject, body = "", icon = "",
            timeout = 6000, append = False, update = False, reference = ""):
        """
        Constructor of the class.

        :param client_handler: The client handler which handles the client to
                               which this message belongs.
        :type client_handler: ClientHandler
        :param subject: The subject of the notification message.
        :type subject: str
        :param body: The body of the notification message. (Defaults to "")
        :type body: str
        :param icon: The icon which should be displayed with the notification
                     message. This can either be the name of the icon or a path
                     to the corresponding file. (Defaults to "")
        :type icon: str
        :param timeout: The time in ms how long the notification should be
                        visible. (Defaults to 6000)
        :type timeout: int
        :param append: Flag which indicates whether the current message should
                       be appended to the last one if possible.
                       (Defaults to False)
        :type appand: bool
        :param update: Flag which indicates whether the current message should
                       replace the last one if possible.
                       (Defaults to False)
        :type update: bool
        :param reference: The unique identifier of the message which this message
                          should replace or be appended to. This is only
                          important if one of these flags are set.
                          (Defaults to '""')
        :type reference: str

        """
        logger.debug("Create new message (S: {}, B: {})".format(subject, body))

        self._id = Message.create_unique_id()

        self._subject = subject
        self._body = body
        self._icon = icon
        self._timeout = timeout
        self._append = append
        self._update = update
        self._reference = reference
        self._client_handler = client_handler

        self._closed_callback_id = -1

        self._closed_condition = Condition()
        self._closed_reason = None

    def _closed_callback(self, notification):
        """
        Callback for the Notification class which is called if the notification
        for this message gets closed.

        This function will set the internal reason variable and notify all
        threads which wait for the notification to close.

        :param notification: The closed notification instance.
        :type notification: Notification
        """
        self._closed_reason = Message.ClosedReason.get(
                notification.get_closed_reason())

        logger.debug("Notification closed with {}".format(
            self._closed_reason.name))

        with self._closed_condition:
            # Notify all waiting threads that the notification got closed.
            self._closed_condition.notify_all()

        notification.disconnect(self._closed_callback_id)
        self._closed_callback_id = -1

    def display(self, use_flags = True):
        """
        Display the notification message on the screen using the notification
        daemon.

        :param use_flags: Whether or not the append and update flags should be
                          used when the message is displayed.
                          (Defaults to True)
        :param use_flags: bool
        :rtype: bool
        :return: Whether displaying of the message worked or not.
        """
        if not use_flags:
            logger.debug("Display message not using flags.")
            self._update = 0
        else:
            logger.debug("Display message using flags.")

        logger.debug("Display message (S:{}, B:{}, T:{}, A:{}, U:{})".format(
            self._subject, self._body, self._timeout, self._append,
            self._update))

        if self._update:
            # This message should replace the last one. So alter the last
            # notification message object.
            logger.debug("Update old message.")

            self._client_handler.notification.update(self._subject,
                    self._body, self._icon)
        else:
            # The old message should not be replaced, so create a new
            # notification message object.
            logger.debug("Create new message.")

            self._client_handler.notification = Notification.new(
                    self._subject, self._body, self._icon)

        # Set append hint, so that following messages can be appended to this
        # one.
        self._client_handler.notification.set_hint("x-canonical-append",
                Variant.new_string("true"))

        # Register for the close event of the notification.
        self._closed_reason = None
        self._closed_callback_id = \
                self._client_handler.notification.connect("closed",
                        self._closed_callback)

        # We now have a properly constructed notification message object. So we
        # can show it now on the screen.
        self._client_handler.notification.set_timeout(self._timeout)

        if not self._client_handler.notification.show():
            logger.error("Failed to show the message.".format(
                self._subject, self._body))

            return False

        logger.debug("Message successfully showed.")

        return True

    def wait_for_close(self):
        """
        Wait until the notification for this message gets closed.

        This method will block if the message is not yet closed until it gets
        closed or otherwise return immediately.

        :rtype: bool
        :return: True if the notification vanished, False if it got closed
                 differently.
        """
        if self._closed_reason is None:
            with self._closed_condition:
                self._closed_condition.wait(self._timeout/1000)

        return self._closed_reason == Message.ClosedReason.Vanished

    @property
    def revises(self):
        """
        Whether or not the current message wants to revise another one.

        :rtype: bool
        :return: Whether or not another message should be revised by this one.
        """
        return self._append or self._update

    @property
    def id(self):
        """
        Get the unique identifier of the message.

        :rtype: str
        :return: The identifier of the message.
        """
        return self._id

    @property
    def reference(self):
        """
        Get the identifier of the message which is referenced by this one.

        :rtype: str
        :return: The identifier of the referenced message.
        """
        return self._reference

    @property
    def timeout(self):
        """
        Get the display timeout of the message.

        :rtype: int
        :return: The time in ms how long the message is shown.
        """
        return self._timeout

