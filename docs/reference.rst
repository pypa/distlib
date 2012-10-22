.. _reference:

API Reference
=============

This is the place where the functions and classes in ``distlib's`` public API
are described.

The ``distlib.database`` package
--------------------------------

Classes
^^^^^^^

.. class:: DistributionPath

   This class represents a set of distributions which are installed on a Python
   path (like ``PYTHONPATH`` / ``sys.path``). Both new-style (``distlib``) and
   legacy (egg) distibutions are catered for.

   Methods:

   .. method:: __init__(path=None, include_egg=False)

      Initialise the instance using a particular path.

      :param path: The path to use when looking for distributions.
                   If ``None`` is specified, ``sys.path`` is used.
      :type path: list of str
      :param include_egg: If ``True``, legacy distributions (eggs)
                          are included in the search; otherwise,
                          they aren't.

   .. method:: enable_cache()

      Enables a cache, so that metadata information doesn't have to be fetched
      from disk. The cache is per instance of the ``DistributionPath`` instance
      and is enabled by default. It can be disabled using :meth:`disable_cache`
      and cleared using :meth:`clear_cache` (disabling won't automatically
      clear it).

   .. method:: disable_cache()

      Disables the cache, but doesn't clear it.

   .. method:: clear_cache()

      Clears the cache, but doesn't change its enabled/disabled status. If
      enabled, the cache will be re-populated when querying for distributions.

   .. method:: get_distributions()

      The main querying method if you want to look at all the distributions. It
      returns an iterator which returns :class:`Distribution` and, if
      ``include_egg`` was specified as ``True`` for the instance, also
      instances of any :class:`EggInfoDistribution` for any legacy
      distributions found.

   .. method:: get_distribution(name)

      Looks for a distribution by name. It returns the first one found with
      that name (there should only be one distribution with a given name on a
      given search path). Returns ``None`` if no distrubution was found, or
      else an instance of :class:`Distribution` (or, if ``include_egg`` was
      specified as ``True`` for the instance, an instance of
      :class:`EggInfoDistribution` if a legacy distribution was found with that
      name).

      :param name: The name of the distribution to search for.
      :type name: str

   .. method:: get_exported_entries(category, name=None)

      Returns an iterator for entries exported by distributions on the path.

      :param category: The export category to look in.
      :type category: str
      :param name: A specific name to search for. If not specified, all
                   entries in the category are returned.
      :type name: str
      :returns: An iterator which iterates over exported entries (instances of
                :class:`ExportEntry`).


.. class:: Distribution

   A class representing a distribution, typically one which hasn't been
   installed (most likely, one which has been obtained from an index like
   PyPI).

   Properties:

   .. attribute:: name

      The name of the distribution.

   .. attribute:: version

      The version of the distribution.

   .. attribute:: metadata

      The metadata for the distribution. This is a
      :class:`distlib.metadata.Metadata` instance.

   .. attribute:: download_url

      The download URL for the distribution.

   .. attribute:: locator

      The locator for an instance which has been retrieved through a locator.
      This is ``None`` for an installed distribution.


.. class:: InstalledDistribution(Distribution)

   A class representing an installed distribution. This class is not
   instantiated directly, except by packaging tools. Instances of it
   are returned from querying a :class:`DistributionPath`.

   Properties:

   .. attribute:: requested

      Whether the distribution was installed by user request (if not, it may
      have been installed as a dependency of some other distribution).

   .. attribute:: exports

      The distribution's exports, as described in :ref:`dist-exports`. This
      is a cached property.

   Methods:

   .. method:: list_installed_files(local=False)

      Returns an iterator over all of the individual files installed as part of
      the distribution, including metadata files. The iterator returns tuples
      of the form (path, hash, size). The list of files is written by the
      installer to the ``RECORD`` metadata file.

      :param local: If ``True``, the paths returned are local absolute paths
                    (i.e. with platform-specific directory separators as
                    indicated by ``os.sep``); otherwise, they are the values
                    stored in the ``RECORD`` metadata file.

   .. method:: list_distinfo_files(local=False)

      Similar to :meth:`list_installed_files`, but only returns metadata files.

      :param local: As for :meth:`list_installed_files`.

   .. method:: check_installed_files()

      Runs over all the installed files to check that the size and checksum are
      unchanged from the values in the ``RECORD`` file, written when the
      distribution was installed. It returns a list of mismatches. If the files
      in the distribution haven't been corrupted , an empty list will be
      returned; otherwise, a list of mismatches will be returned.

      :returns: A list which, if non-empty, will contain tuples with the
                following elements:

                * The path in ``RECORD`` which failed to match.
                * One of the strings 'exists', 'size' or 'hash' according to
                  what didn't match (existence is checked first, then size,
                  then hash).
                * The expected value of what didn't match (as obtained from
                  ``RECORD``).
                * The actual value of what didn't match (as obtained from the
                  file system).

   .. method:: read_exports(filename=None)

      Read exports information from a file.

      Normal access to a distribution's exports should be through its
      :attr:`exports` attribute. This method is called from there as needed.
      If no filename is specified, the ``EXPORTS`` file in the ``.dist-info``
      directory is read (it is expected to be present).

      :param filename: The filename to read from, or ``None`` to read from the
                       default location.
      :type filename: str
      :returns: The exports read from the file.
      :rtype: dict

   .. method:: write_exports(exports, filename=None)

      Write exports information to a file.

      If no filename is specified, the ``EXPORTS`` file in the ``.dist-info``
      directory is written.

      :param exports: A dictionary whose keys are categories and whose values
                      are dictionaries which contain :class:`ExportEntry`
                      instances keyed on their name.
      :type exports: dict
      :param filename: The filename to read from, or ``None`` to read from the
                       default location.
      :type filename: str


.. class:: EggInfoDistribution

   Analogous to :class:`Distribution`, but covering legacy distributions. This
   class is not instantiated directly. Instances of it are returned from
   querying a :class:`DistributionPath`.

   Properties:

   .. attribute:: name

      The name of the distribution.

   .. attribute:: version

      The version of the distribution.

   .. attribute:: metadata

      The metadata for the distribution. This is a
      :class:`distlib.metadata.Metadata` instance.

   Methods:

   .. method:: list_installed_files(local=False)

      Returns a list all of the individual files installed as part of
      the distribution.

      :param local: If ``True``, the paths returned are local absolute paths
                    (i.e. with platform-specific directory separators as
                    indicated by ``os.sep``).



The ``distlib.resources`` package
---------------------------------

.. currentmodule:: distlib.resources

Attributes
^^^^^^^^^^

.. attribute:: cache

   An instance of :class:`Cache`, which uses the default base location for the
   cache (as descibed in the documentation for :meth:`Cache.__init__`).

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

   .. attribute:: path

      This attribute is set by the resource's finder. It is a textual
      representation of the path, such that if a PEP 302 loader's
      :meth:`get_data` method is called with the path, the resource's
      bytes are returned by the loader. This attribute is analogous to
      the ``resource_filename`` API in ``setuptools``. Note that for
      resources in zip files, the path will be a pointer to the resource
      in the zip file, and not directly usable as a filename. While
      ``setuptools`` deals with this by extracting zip entries to cache
      and returning filenames from the cache, this does not seem an
      appropriate thing to do in this package, as a resource is already
      made available to callers either as a stream or a string of bytes.

   .. attribute:: file_path

      This attribute is the same as the path for file-based resource.
      For resources in a .zip file, the relevant resource is extracted
      to a file in a cache in the file system, and the name of the cached
      file is returned. This is for use with APIs that need file names
      or to be able to access data through OS-level file handles.

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

.. class:: Cache

   This class implements a cache for resources which must be accessible as
   files in the file system.

   .. method:: __init__(base=None)

      Initialise a cache instance with a specific directory which holds the
      cache. If ``base`` is specified but does not exist, it is created.
      If ``base`` is not specified, it defaults to
      ``os.expanduser('~/.distlib/resource-cache') on
      POSIX platforms (``os.name == 'posix'``). On Windows, if the environment
      contains ``LOCALAPPDATA``, the cache will be placed in

          ``os.path.expandvars(r'$localappdata\.distlib\resource-cache')``

      Otherwise, the location will be

          ``os.path.expanduser(r'~\.distlib\resource-cache')``

   .. method:: get(resource)

      Ensures that the resource is available as a file in the file system,
      and returns the name of that file. This method calls the resource's
      finder's :meth:`get_cache_info` method.

   .. method:: is_stale(resource, path)

      Returns whether the data in the resource which is cached in the file
      system is stale compared to the resource's current data. The default
      implementation returns ``True``, causing the resource's data to be
      re-written to the file every time.

   .. method:: prefix_to_dir(prefix)

      Converts a prefix for a resource (e.g. the name of its containing
      .zip) into a directory name in the cache. This implementation
      delegates the work to :func:`~distlib.util.path_to_cache_dir`.


The ``distlib.scripts`` package
-------------------------------

.. currentmodule:: distlib.scripts

Classes
^^^^^^^

.. class:: ScriptMaker

   A class used to install scripts based on specifications.

   .. attribute:: source_dir

      The directory where script sources are to be found.

   .. attribute:: target_dir

      The directory where scripts are to be created.

   .. attribute:: add_launchers

      Whether to create native executable launchers on Windows.

   .. attribute:: force

      Whether to overwrite scripts even when timestamps show they're up to
      date.

   .. attribute:: set_mode

      Whether, on Posix, the scripts should have their execute mode set.

   .. attribute:: script_template

      The text of a template which should contain ``%(shebang)s``,
      ``%(module)s`` and ``%(func)s`` in the appropriate places.

      The attribute is defined at class level. You can override it at the
      instance level to customise your scripts.

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

The ``distlib.locators`` package
--------------------------------

.. currentmodule:: distlib.locators


Classes
^^^^^^^^

.. class:: Locator

   The base class for locators. Implements logic common to multiple locators.

   .. method:: get_project(name)

      This method should be implemented in subclasses. It returns a
      (potentially empty) dictionary whose keys are the versions located
      for the project named by ``name``, and whose values are instances of
      :class:`distlib.util.Distribution`.

   .. method:: convert_url_to_download_info(url, project_name)

      Extract information from a URL about the name and version of a
      distribution.

      :param url: The URL potentially of an archive (though it needn't be).
      :type url: str
      :param project_name: This must match the project name determined from the
                           archive (case-insensitive matching is used).
      :type project_name: str
      :returns: ``None`` if the URL does not appear to be that of a
                distribution archive for the named project. Otherwise, a
                dictionary is returned with the following keys at a minimum:

                * url -- the URL passed in, minus any fragment portion.
                * filename -- a suitable filename to use for the archive
                  locally.

                Optional keys returned are:

                * md5_digest -- the MD5 hash of the archive, for verification
                  after downloading. This is extracted from the fragment
                  portion, if any, of the passed-in URL.
      :rtype: dict


.. class:: DirectoryLocator

   This locator scans the file system under a base directory, looking for
   distribution archives.

   .. method:: __init__(base_dir)

      :param base_dir: The base directory to scan for distribution archives.
      :type base_dir: str

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.

.. class:: PyPIRPCLocator

   This locator uses the PyPI XML-RPC interface to locate distribution
   archives and other data about downloads.

   .. method:: __init__(url)

      :param url: The base URL to use for the XML-RPC service.
      :type url: str

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.


.. class:: PyPIJSONLocator

   This locator uses the PyPI JSON interface to locate distribution
   archives and other data about downloads. It gets the metadata and URL
   information in a single call, so it should perform better than the
   XML-RPC locator.

   .. method:: __init__(url)

      :param url: The base URL to use for the JSON service.
      :type url: str

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.


.. class:: SimpleScrapingLocator

   This locator uses the PyPI 'simple' interface -- a Web scraping interface --
   to locate distribution archives.

   .. method:: __init__(url)

      :param url: The base URL to use for the simple service HTML pages.
      :type url: str

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.


.. class:: AggregatingLocator

   This locator uses a list of other aggregators and delegates finding projects
   to them. It can either return the first result found (i.e. from the first
   aggregator in the list provided which returns a non-empty result), or a
   merged result from all the aggregators in the list.

   .. method:: __init__(*locators, merge=False)

      :param locators: A list of aggregators to delegate finding projects to.
      :type locators: sequence of locators
      :param merge: If ``True``, each aggregator in the list is asked to
                    provide results, which are aggregated into a results
                    dictionary. If ``False``, the first non-empty return value
                    from the list of aggregators is returned. The aggregators
                    are consulted in the order in which they're passed in.
      :type merge: bool

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.

Functions
^^^^^^^^^

.. function:: get_all_distribution_names(url=None)

   Retrieve the names of all distributions registered on an index.

   :param url: The XML-RPC service URL of the node to query. If not specified,
               The main PyPI index is queried.
   :type url: str
   :returns: A list of the names of distributions registered on the index.
             Note that some of the names may be Unicode.
   :rtype: list


.. function:: locate(requirement)

   This convenience function returns the latest version of a potentially
   downloadable distribution which matches a requirement (name and version
   constraints). If a potentially downloadable distribution (i.e. one with
   a download URL) is not found, ``None`` is returned; otherwise, an
   instance of :class:`~distlib.database.Distribution` is returned. The
   returned instance will have, at a minimum, ``name``, ``version`` and
   ``download_url``.

   :param requirement: The name and optional version constraints of the
                       distribution to locate, e.g. ``'Flask'`` or
                       ``'Flask (>= 0.7, < 0.9)'``.
   :type requirement: str
   :returns: A matching instance of :class:`~distlib.database.Distribution`,
             or ``None``.

Variables
^^^^^^^^^

.. attribute:: default_locator

   This attribute holds a locator which is used by :func:`locate` to locate
   distributions.


The ``distlib.util`` package
-------------------------------

.. currentmodule:: distlib.util


Classes
^^^^^^^^

.. class:: ExportEntry

   Attributes:

   A class holding information about a exports entry.

   .. attribute:: name

      The name of the entry.

   .. attribute:: prefix

      The prefix part of the entry. For a callable or data item in a module,
      this is the name of the package or module containing the item.

   .. attribute:: suffix

      The suffix part of the entry. For a callable or data item in a module,
      this is a dotted path which points to the item in the module.

   .. attribute:: flags

      A list of flags. See :ref:`flag-formats` for more information.

   .. attribute:: value

      The actual value of the entry (a callable or data item in a module, or
      perhaps just a module). This is a cached property of the instance, and
      is determined by calling :func:`resolve` with the ``prefix`` and
      ``suffix`` properties.

   .. attribute:: dist

      The distribution which exports this entry. This is normally an
      instance of :class:`InstalledDistribution`.

Functions
^^^^^^^^^

.. function:: get_cache_base()

   Return the base directory which will hold distlib caches. If the directory
   does not exist, it is created.

   On Windows, if ``LOCALAPPDATA`` is defined in the environment, then it is
   assumed to be a directory, and will be the parent directory of the result.
   On POSIX, and on Windows if ``LOCALAPPDATA`` is not defined, the user's home
   directory -- as determined using ``os.expanduser('~')`` -- will be the
   parent directory of the result.

   The result is just the directory ``'.distlib'`` in the parent directory as
   determined above.

.. function:: path_to_cache_dir(path)

   Converts a path (e.g. the name of an archive) into a directory name
   suitable for use in a cache. The following algorithm is used:

   #. On Windows, any ``':'`` in the drive is replaced with ``'---'``.
   #. Any occurrence of ``os.sep`` is replaced with ``'--'``.
   #. ``'.cache'`` is appended.

.. function:: get_export_entry(specification)

   Return a export entry from a specification, if it matches the
   expected format, or else ``None``.

   :param specification: A specification, as documented for the
                         :meth:`distlib.scripts.ScriptMaker.make` method.
   :type specification: str
   :returns: ``None`` if the specification didn't match the expected form
             for an entry, or else an instance of :class:`ExportEntry`
             holding information about the entry.

.. function:: resolve(module_name, dotted_path)

   Given a ``module name`` and a ``dotted_path`` representing an object in that
   module, resolve the passed parameters to an object and return that object.

   If the module has not already been imported, this function attempts to
   import it, then access the object represented by ``dotted_path`` in the
   module's namespace. If ``dotted_path`` is ``None``, the module is returned.
   If import or attribute access fails, an ``ImportError`` or
   ``AttributeError`` will be raised.

   :param module_name: The name of a Python module or package, e.g. ``os`` or
                       ``os.path``.
   :type module_name: str
   :param dotted_path: The path of an object expected to be in the module's
                       namespace, e.g. ``'environ'``, ``'sep'`` or
                       ``'path.supports_unicode_filenames'``.
   :type dotted_path: str



Next steps
----------

You might find it helpful to look at the
`mailing list <http://mail.python.org/mailman/listinfo/distutils-sig/>`_.
