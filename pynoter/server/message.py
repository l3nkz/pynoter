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

    @staticmethod
    def create_unique_id():
        """
        Create a unique id for a message object.
        """
        return str(uuid4()).replace('-', '_')

    def __init__(self, notification, subject, body = "", icon = "",
            timeout = 6000, append = False, update = False, reference = ""):
        """
        Constructor of the class.

        :param notification: The notification object which was previously used
                             by the client from which this message comes.
        :type notification: Notification
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
        self._reference = reference if reference is not None else "not_set"
        self._notification = notification

    def display(self):
        """
        Display the notification message on the screen using the notification
        daemon.

        :rtype: bool
        :return: Whether displaying of the message worked or not.
        """
        logger.debug("Display message (S: {}, B: {}, T: {})".format(
            self._subject, self._body, self._timeout))

        if self._update:
            # This message should replace the last one. So alter the last
            # notification message object.
            logger.debug("Replace old message")

            self._notification.update(self._subject, self._body, self._icon)
        else:
            # The old message should not be replaced, so create a new
            # notification message object.
            self._notification = Notification.new(self._subject, self._body,
                    self._icon)

            # Set the append hint at the notification message if append was
            # requested by the user.
            if self._append:
                logger.debug("Set append hint to the message")

                self._notification.set_hint_string("x-canonical-append",
                        "true")

        # We now have a properly constructed notification message object. So we
        # can show it now on the screen.
        self._notification.set_timeout(self._timeout)

        if not self._notification.show():
            logger.error("Failed to show message (S: {}, B: {})".format(
                self._subject, self._body))

            return False

        return True

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

