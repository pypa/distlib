.. _reference:

API Reference
=============

This is the place where the functions and classes in ``distlib's`` public API
are described.

The ``distlib.resources`` package
---------------------------------

.. currentmodule:: distlib.resources

Functions
^^^^^^^^^

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
^^^^^^^

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

   A base class for resource finders, which finds resources for packages stored
   in the file system.

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


The ``distlib.scripts`` package
-------------------------------

.. currentmodule:: distlib.scripts

Classes
^^^^^^^

.. class:: ScriptMaker

   A class used to install scripts based on specifications.

   .. method:: __init__(source_directory, target_directory, add_launchers=True, dry_run=False)

      Initialise the instance with options that control its behaviour.

      :param source_directory: Where to find scripts to install.
      :type source_directory: str
      :param target_directory: Where to install scripts to.
      :type target_directory: str
      :param add_launchers: If true, create executable launchers on Windows.
                            The executables are currently generated from the
                            following project:

                            https://bitbucket.org/vinay.sajip/simple_launcher/

      :type add_launchers: bool
      :param dry_run: If true, don't actually install scripts - just pretend to.

   .. method:: make(specification)

      Make a script in the target directory.

      :param specification: A specification, which can take one of the
                            following forms:

                            * A filename, relative to ``source_directory``,
                              such as ``foo.py`` or ``subdir/bar.py``.

                            * A reference to a callable, given in the form::

                                  name = some_package.some_module:some_callable [flags]

                              where the *flags* part is optional. The only flag
                              currently in use is ``'gui'``, which indicates on
                              Windows that a Windows executable launcher
                              (rather than a launcher which is a console
                              application) should be used. (This only applies if
                              ``add_launchers`` is true.)

                              When this form is passed, a Python stub script
                              is created with the appropriate shebang line and
                              with code to load and call the specified callable
                              with no arguments, returning its value as the
                              return code from the script.
                              
                              For more information about flags, see
                              :ref:`flag-formats`.

      :type specification: str
      :returns: A list of absolute pathnames of files installed (or which
                would have been installed, but for ``dry_run`` being true).

   .. method:: make_multiple(specifications)
   
      Make multiple scripts from an iterable.
      
      This method just calls :meth:`make` once for each value returned by the
      iterable, but it might be convenient to override this method in some
      scenarios to do post-processing of the installed files (for example,
      running ``2to3`` on them).
      
      :param specifications: an iterable giving the specifications to follow.
      :returns: A list of absolute pathnames of files installed (or which
                would have been installed, but for ``dry_run`` being true).

   .. method:: get_callable(specification)
   
      Return the callable information from a specification, if it matches the
      expected format, or else ``None``.

      :param specification: A specification, as for the :meth:`make` method.
      :type specification: str
      :returns: ``None`` if the specification didn't match the expected form
                for a callable, or else a tuple of::
                
                * script name in target directory
                * module name which contains the callable
                * the name the callable is bound to
                * a (possibly empty) list of flags.

Next steps
----------

You might find it helpful to look at the
`mailing list <http://mail.python.org/mailman/listinfo/distutils-sig/>`_.
