.. _reference:

API Reference
=============

This is the place where the functions and classes in ``distlib's`` public API
are described.

The ``distlib.resources`` package
---------------------------------

Functions
---------

.. function:: finder(package)

   Get a finder for the specified package.

   If the package hasn't been imported yet, an attempt will be made to import
   it. If importing fails, an :class:`ImportError` will be raised.

   :param package: The name of the package for which a finder is desired.
   :type package: str
   :returns: A finder for the package.

.. function:: register_finder(loader, finder_maker)

   Register a callable which makes finders for a particular type of :pep:`302`
   loader.

   :param loader: The loader for which a finder is to be returned.
   :param finder_maker: A callable to be registered, which is called
                        when a loader of the specified type is used
                        to load a module or package. The callable is called
                        with a single argument -- the module or package -- and
                        must return a finder for that module or package.
Classes
-------

.. class:: Resource


.. class:: FileResourceFinder


.. class:: ZipResourceFinder



Next steps
----------

You might find it helpful to look at the
`mailing list <http://mail.python.org/mailman/listinfo/distutils-sig/>`_.
