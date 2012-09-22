.. _tutorial:

Tutorial
========

This is the place to start your practical exploration of ``distlib``.

Installation and testing
------------------------

Distlib is a pure-Python library. You should be able to install it using::

    pip install distlib

for installing ``distlib`` into a virtualenv or other directory where you have
write permissions. On Posix platforms, you may need to invoke using ``sudo``
if you need to install ``distlib`` in a protected location such as your system
Python's ``site-packages`` directory.

A full test suite is included with ``distlib``. To run it, you'll need to
unpack a source tarball and run ``python setup.py test`` in the top-level
directory of the unpack location. You can of course also run
``python setup.py install``
to install from the source tarball (perhaps invoking with ``sudo`` if you need
to install to a protected location).

First steps
-----------

TBD

Next steps
----------

You might find it helpful to look at information about 
:ref:`internals` -- or peruse the :ref:`reference`.
