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
                        to load a package. The callable is called
                        with a single argument -- the Python module object
                        corresponding to the package -- and must return a
                        finder for that package.

Classes
-------

.. class:: Resource

   A class representing resources. It is never instantiated directly, but
   always through calling a finder's ``find`` method.

   Properties:

   .. attribute:: is_container

      Whether this instance is a container of other resources.

   .. attribute:: bytes

      All of the resource data as a byte string. Raises an exception
      if accessed on a container resource.

   .. attribute:: size

      The size of the resource data in bytes. Raises an exception if
      accessed on a container resource.

   .. attribute:: resources

      The relative names of all the contents of this resource. Raises an
      exception if accessed on a resource which is *not* a container.

   Methods:

   .. method:: as_stream()

      A binary stream of the resource's data. This must be closed by the caller
      when it's finished with.
      
      Raises an exception if called on a container resource.

.. class:: ResourceFinder

   .. method:: __init__(module)
   
      Initialise the finder for the package specified by ``module``.

      :param module: The Python module object representing a package.

   .. method:: find(resource_name)
   
      Find a resource with the name specified by ``resource_name`` and
      return a ``Resource`` instance which represents it.
      
      :param resource_name: A fully qualified resource name, with
                            hierarchical components separated by '/'.
      :returns: A :class:`Resource` instance, or ``None`` if a resource
                with that name wasn't found.

   .. method:: is_container(resource)

      Return whether a resource is a container of other resources.
      
      :param resource: The resource whose status as container is wanted.
      :type resource: a :class:`Resource` instance
      :returns: ``True`` or ``False``.

   .. method:: get_stream(resource)

      Return a binary stream for the specified resource.
      
      :param resource: The resource for which a stream is wanted.
      :type resource: a :class:`Resource` instance
      :returns: A binary stream for the resource.

   .. method:: get_bytes(resource)

      Return the contents of the specified resource as a byte string.
      
      :param resource: The resource for which the bytes are wanted.
      :type resource: a :class:`Resource` instance
      :returns: The data in the resource as a byte string.

   .. method:: get_size(resource)

      Return the size of the specified resource in bytes.
      
      :param resource: The resource for which the size is wanted.
      :type resource: a :class:`Resource` instance
      :returns: The size of the resource in bytes.

.. class:: ZipResourceFinder

   This has the same interface as :class:`ResourceFinder`.

Next steps
----------

You might find it helpful to look at the
`mailing list <http://mail.python.org/mailman/listinfo/distutils-sig/>`_.
