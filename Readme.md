# pynoter


Description
===========

pynoter is a python library which provides advanced notification mechanisms to every program.
The library consists of 2 parts. A server handling the notification messages and providing
all the needed synchronization and a client which just send the notifications which
it wants to display to the server. Because the server is the one who handles and displays
the notification messages, it can perform fancy features such as combining or replacing of
messages. It also supports that messages from multiple instances of a program are merged and
handled like one instance as well as that messages sent from a short living script are
combined in the same manner.


Supported Features
------------------

1. Combining of multiple notification messages to one. (Appending)

2. Replacing of an existing notification message with a new one. (Updating)

3. Merging of notification messages sent from multiple instances of a program. (Multi Client)

4. Merging of notification messages sent from short living scripts. (Lingering)


Usage
=====

If you want to use this library you have to do two things. The first one is that a server
must be started in the system. One server in the system should be enough for most use cases.
This can be either the included 'pyNoter' executable or your own fancy implementation. As
second part you have to enhance your program/script to a client. This can either be done by
inheriting from the 'pynoter.Client' class or by having an instance of it in your program.
Messages can than be sent by using the 'display_message' method of the client. That is all.


Example Client
--------------

The usage of the library as client is really really simple. The following example shows
everything which is needed to create a client and send messages.

```python
from pynoter import Client

c = Client("foo")
c.display_message("Subject", "Body")
```

More information about the usage of the client can be found in the documentation of it. So
for example about the additional parameters which each method provide.


Using pynoter not from python
-----------------------------

The pynoter server with all its functionality can also be used without using python. The server
exposes its functionality via DBus. Hence, one simply can use this interface similarly as the
provided python client and thereby be able to use all the features too.


Installation
============

To install the library in your system run the following command or use your package manager.

```bash
python setup.py install
```


Additionally, this repository also provides an executable for the server and a systemd service
file which can be used directly as they are or be used as a reference to implement them on your
own.

