.. _reference:

API Reference
=============

This is the place where the functions and classes in ``distlib's`` public API
are described.

The ``distlib`` package
-----------------------

.. currentmodule:: distlib

Classes
^^^^^^^

.. class:: DistlibException

   This is the base class for all exceptions raised by this packages, other than
   lower-level standard Python exceptions.

The ``distlib.database`` package
--------------------------------

.. currentmodule:: distlib.database

Classes
^^^^^^^

.. class:: DistributionPath

   This class represents a set of distributions which are installed on a Python
   path (like ``PYTHONPATH`` / ``sys.path``). Both new-style (``distlib``) and
   legacy (egg) distributions are catered for.

   Methods:

   .. method:: __init__(path=None, include_egg=False)

      Initialise the instance using a particular path.

      :param path: The path to use when looking for distributions.
                   If ``None`` is specified, ``sys.path`` is used.
      :type path: list[str]
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
      given search path). Returns ``None`` if no distribution was found, or
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
                :class:`~distlib.util.ExportEntry`).

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

      The download URL for the distribution. If there are multiple
      URLs, this will be one of the values in :attr:`download_urls`.

   .. attribute:: download_urls

      A set of known download URLs for the distribution.

      .. versionadded:: 0.2.0
         The ``download_urls`` attribute was added.

   .. attribute:: digest

      The digest for the source distribution. This is either ``None`` or a
      2-tuple consisting of the hashing algorithm and the digest using that
      algorithm, e.g. ``('sha256', '01234...')``.

   .. attribute:: digests

      A dictionary mapping download URLs to digests, if and when digests are
      available.

      .. versionadded:: 0.2.0
         The ``digests`` attribute was added.

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

   .. method:: list_installed_files()

      Returns an iterator over all of the individual files installed as part of
      the distribution, including metadata files. The iterator returns tuples
      of the form (path, hash, size). The list of files is written by the
      installer to the ``RECORD`` metadata file.

   .. method:: list_distinfo_files()

      Similar to :meth:`list_installed_files`, but only returns metadata files.

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
                      are dictionaries which contain :class:`~distlib.util.ExportEntry`
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

   .. method:: list_installed_files()

      Returns a list all of the individual files installed as part of
      the distribution.

.. class:: DependencyGraph

   This class represents a dependency graph between releases. The nodes are
   distribution instances; the edges model dependencies. An edge from ``a``
   to ``b`` means that ``a`` depends on ``b``.

   .. method:: add_distribution(distribution)

      Add *distribution* to the graph.

   .. method:: add_edge(x, y, label=None)

      Add an edge from distribution *x* to distribution *y* with the given
      *label* (string).

   .. method:: add_missing(distribution, requirement)

      Add a missing *requirement* (string) for the given *distribution*.

   .. method:: repr_node(dist, level=1)

      Print a subgraph starting from *dist*.  *level* gives the depth of the
      subgraph.

   Direct access to the graph nodes and edges is provided through these
   attributes:

   .. attribute:: adjacency_list

      Dictionary mapping distributions to a list of ``(other, label)`` tuples
      where  ``other`` is a distribution and the edge is labelled with ``label``
      (i.e. the version specifier, if such was provided).

   .. attribute:: reverse_list

      Dictionary mapping distributions to a list of predecessors. This allows
      efficient traversal.

   .. attribute:: missing

      Dictionary mapping distributions to a list of requirements that were not
      provided by any distribution.

Functions
^^^^^^^^^

.. function:: make_graph(dists, scheme='default')

   Return a dependency graph from the given distributions.

.. function:: get_dependent_dists(dists, dist)

   Recursively generate a list of distributions from *dists* that are dependent on
   *dist*.

.. function:: get_required_dists(dists, dist)

   Recursively generate a list of distributions from *dists* that are required by
   *dist*.


The ``distlib.resources`` package
---------------------------------

.. currentmodule:: distlib.resources

Attributes
^^^^^^^^^^

.. attribute:: cache

   An instance of :class:`ResourceCache`. This can be set after module
   import, but before calling any functionality which uses it, to ensure
   that the cache location is entirely under your control.

   If you access the ``file_path`` property of :class:`Resource` instance,
   the cache will be needed, and if not set by you, an instance with
   a default location will be created. See :func:`distlib.util.get_cache_base`
   for more information.

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
                        finder (compatible with the :class:`ResourceFinder`)
                        for that package.

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
      ``get_data()`` method is called with the path, the resource's
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
      file is returned. This is for use with APIs that need file names,
      or need to be able to access data through OS-level file handles. See
      the :class:`~distlib.resources.ResourceCache` documentation for more
      information about the cache.

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

   .. method:: iterator(resource_name)

      Return a generator which walks through the resources available through
      ``resource_name``.

      :param resource_name: A fully qualified resource name, with
                            hierarchical components separated by '/'.
                            You can use '' to mean the 'root' resource.
                            If the resource name refers to a non-container
                            resource, only that resource is returned.
                            Otherwise, the named resource is returned, followed
                            by its children, recursively. If there is no
                            resource named ``resource_name``, ``None`` is
                            returned.

      :returns: A generator to iterate over resources, or ``None``.

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

   .. method:: get_cache_info(resource)

      Return the cache information for the specified resource. This is a two-tuple
      consisting of an optional prefix (currently used for zip-based resources only,
      and is otherwise ``None``) and an absolute path.

      :param resource: The resource for which the cache info is wanted.
      :type resource: a :class:`Resource` instance
      :returns: tuple


.. class:: ZipResourceFinder

   This has the same interface as :class:`ResourceFinder`.

.. class:: ResourceCache

   This class implements a cache for resources which must be accessible as
   files in the file system. It is based on :class:`~distlib.util.Cache`, and
   adds resource-specific methods.

   .. method:: __init__(base=None)

      Initialise a cache instance with a specific directory which holds the
      cache. If base is not specified, the value ``resource-cache`` in the
      directory returned by :func:`~distlib.util.get_cache_base` is used.

   .. method:: get(resource)

      Ensures that the resource is available as a file in the file system,
      and returns the name of that file. This method calls the resource's
      finder's :meth:`~distlib.resources.ResourceFinder.get_cache_info` method.

   .. method:: is_stale(resource, path)

      Returns whether the data in the resource which is cached in the file
      system is stale compared to the resource's current data. The default
      implementation returns ``True``, causing the resource's data to be
      re-written to the file every time.

.. _scripts:

The ``distlib.scripts`` package
-------------------------------

.. currentmodule:: distlib.scripts

Classes
^^^^^^^

.. class:: ScriptMaker

   A class used to install scripts based on specifications.

   .. cssclass:: class-members-heading

   Attributes

   .. attribute:: source_dir

      The directory where script sources are to be found.

   .. attribute:: target_dir

      The directory where scripts are to be created.

   .. attribute:: add_launchers

      Whether to create native executable launchers on Windows.

   .. attribute:: force

      Whether to overwrite scripts even when timestamps show they're up to
      date.

   .. attribute:: clobber

      Whether to overwrite existing scripts. The default is ``False``, which means that
      existing scripts will not be overwritten.

   .. attribute:: executable

      Value to use for the executable to use when constructing a shebang. If specified,
      it is used in place of any value determined algorithmically.

   .. attribute:: set_mode

      Whether, on POSIX, the scripts should have their execute mode set.

   .. attribute:: script_template

      The text of a template which should contain ``%(shebang)s``,
      ``%(module)s`` and ``%(func)s`` in the appropriate places.

      The attribute is defined at class level. You can override it at the
      instance level to customise your scripts.

   .. attribute:: version_info

      A two-tuple of the Python version to be used when generating scripts, where
      version-specific variants such as `foo3` or `foo-3.8` are created. This defaults
      to ``sys.version_info``. The provided tuple can have more elements, but only the
      first two are used.

      .. versionadded:: 0.3.1

   .. attribute:: variant_separator

      A string value placed between the root basename and the version information in a
      variant-specific filename. This defaults to ``'-'``, which means that a script
      with root basename ``foo`` and a variant ``X.Y`` will have a base filename of
      ``foo-3.8`` for target Python version 3.8. If you wanted to write ``foo3.8``
      instead of ``foo-3.8``, this attribute could be set to ``''``. If you need more
      control over filename generation, you can subclass :class:`ScriptMaker` and
      override the :meth:`get_script_filenames` method.

      .. versionadded:: 0.3.2


   .. cssclass:: class-members-heading

   Methods

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

   .. method:: make(specification, options=None)

      Make a script in the target directory.

      :param specification: A specification, which can take one of the
                            following forms:

                            * A filename, relative to ``source_directory``,
                              such as ``foo.py`` or ``subdir/bar.py``.

                            * A reference to a callable, given in the form::

                                  name = some_package.some_module:some_callable [flags]

                              where the *flags* part is optional.

                              When this form is passed, a Python stub script
                              is created with the appropriate shebang line and
                              with code to load and call the specified callable
                              with no arguments, returning its value as the
                              return code from the script.

                              For more information about flags, see
                              :ref:`flag-formats`.

      :type specification: str
      :param options: If specified, a dictionary of options used to control
                      script creation. Currently, the following keys are
                      checked:

                          ``gui``: This should be a ``bool`` which, if ``True``,
                          indicates that the script is a windowed
                          application. This distinction is only drawn
                          on Windows if ``add_launchers`` is ``True``,
                          and results in a windowed native launcher
                          application if ``options['gui']`` is ``True``
                          (otherwise, the native executable launcher
                          is a console application).

                          ``interpreter_args``: If specified, this should be
                          a list of strings which are appended to the
                          interpreter executable in the shebang line. If there
                          are values with spaces, you will need to surround
                          them with double quotes.

                          .. note:: Linux does not handle passing arguments
                             to interpreters particularly well -- multiple
                             arguments are bundled up into one when passing to
                             the interpreter -- see
                             https://en.wikipedia.org/wiki/Shebang_line#Portability
                             for more information. This may also affect other
                             POSIX platforms -- consult the OS documentation
                             for your system if necessary. On Windows, the
                             ``distlib`` native executable launchers *do* parse
                             multiple arguments and pass them to the
                             interpreter.

      :type options: dict
      :returns: A list of absolute pathnames of files installed (or which
                would have been installed, but for ``dry_run`` being true).

   .. method:: make_multiple(specifications, options)

      Make multiple scripts from an iterable.

      This method just calls :meth:`make` once for each value returned by the
      iterable, but it might be convenient to override this method in some
      scenarios to do post-processing of the installed files (for example,
      running ``2to3`` on them).

      :param specifications: an iterable giving the specifications to follow.
      :param options: As for the :meth:`make` method.
      :returns: A list of absolute pathnames of files installed (or which
                would have been installed, but for ``dry_run`` being true).

   .. method:: get_script_filenames(name)

      Get the names of scripts to be written for the specified base name, based on
      the ``variants`` and ``version_info`` for this instance. You can override this
      if you need to customise the filenames to be written.

      :param str name: the basename of the script to be written.
      :returns: A set of filenames of files to be written as scripts, based on what
                variants are specified. For example, if the name is ``foo`` and the
                variants are ``{'X', 'X.Y'}`` and the ``version_info`` is ``(3, 8)``,
                then the result would be ``{'foo3', 'foo-3.8'}``.

      .. versionadded:: 0.3.2

Functions
^^^^^^^^^

.. function:: enquote_executable(path)

   Cover an executable path in quotes. This only applies quotes if the passed path
   contains any spaces. It's at least a little careful when doing the quoting - for
   example, producing e.g. ``/usr/bin/env "/dir with spaces/bin/jython"`` instead of
   ``"/usr/bin/env /dir with spaces/bin/jython"``

   .. versionchanged:: 0.3.1
      This was an internal function ``_enquote_executable`` in earlier versions.

The ``distlib.locators`` package
--------------------------------

.. currentmodule:: distlib.locators

Classes
^^^^^^^^

.. class:: Locator

   The base class for locators. Implements logic common to multiple locators.

   .. attribute:: matcher

      A :class:~distlib.version.VersionMatcher`

   .. method:: __init__(scheme='default')

      Initialise an instance of the locator.

      :param scheme: The version scheme to use.
      :type scheme: str

   .. method:: _get_project(name)

      This method should be implemented in subclasses. It returns a
      (potentially empty) dictionary whose keys are the versions located
      for the project named by ``name``, and whose values are instances of
      :class:`distlib.database.Distribution`.

   .. method:: get_project(name)

      This method calls :meth:`_get_project` to do the actual work, and provides a
      caching layer on top.

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
                * sha256_digest -- the SHA256 hash of the archive, for
                  verification after downloading. This is extracted from the
                  fragment portion, if any, of the passed-in URL.
      :rtype: dict

   .. method:: get_distribution_names

      Get the names of all distributions known to this locator.

      The base class raises :class:`NotImplementedError`; this method should
      be implemented in a subclass.

      :returns: All distributions known to this locator.
      :rtype: set

   .. method:: locate(requirement, prereleases=False)

      This tries to locate the latest version of a potentially downloadable
      distribution which matches a requirement (name and version constraints).
      If a potentially downloadable distribution (i.e. one with a download
      URL) is not found, ``None`` is returned -- otherwise, an instance of
      :class:`~distlib.database.Distribution` is returned. The returned
      instance will have, at a minimum, ``name``, ``version`` and
      ``source_url`` populated.

      :param requirement: The name and optional version constraints of the
                          distribution to locate, e.g. ``'Flask'`` or
                          ``'Flask (>= 0.7, < 0.9)'``.
      :type requirement: str
      :param prereleases: If ``True``, prereleases are treated like normal
                          releases. The default behaviour is to not return any
                          prereleases unless they are the only ones which match
                          the requirement.
      :type prereleases: bool
      :returns: A matching instance of :class:`~distlib.database.Distribution`,
                or ``None``.

   .. method:: get_errors()

      This returns a (possibly empty) list of error messages relating to a
      recent :meth:`~distlib.locators.Locator.get_project` or
      :meth:`~distlib.locators.Locator.locate` call. Fetching the errors
      clears the error list.

      .. versionadded:: 0.2.4

.. class:: DirectoryLocator(Locator)

   This locator scans the file system under a base directory, looking for
   distribution archives. The locator scans all subdirectories recursively,
   unless the ``recursive`` flag is set to ``False``.

   .. method:: __init__(base_dir, **kwargs)

      :param base_dir: The base directory to scan for distribution archives.
      :type base_dir: str
      :param  kwargs: Passed to base class constructor, apart from the
                      following keyword arguments:

                      * ``recursive`` (defaults to ``True``) -- if ``False``,
                        no recursion into subdirectories occurs.

.. class:: PyPIRPCLocator(Locator)

   This locator uses the PyPI XML-RPC interface to locate distribution
   archives and other data about downloads.

   .. method:: __init__(url, **kwargs)

      :param url: The base URL to use for the XML-RPC service.
      :type url: str
      :param  kwargs: Passed to base class constructor.

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.

.. class:: PyPIJSONLocator(Locator)

   This locator uses the PyPI JSON interface to locate distribution
   archives and other data about downloads. It gets the metadata and URL
   information in a single call, so it should perform better than the
   XML-RPC locator.

   .. method:: __init__(url, **kwargs)

      :param url: The base URL to use for the JSON service.
      :type url: str
      :param  kwargs: Passed to base class constructor.

    .. method:: get_project(name)

       See :meth:`Locator.get_project`.

.. class:: SimpleScrapingLocator

   This locator uses the PyPI 'simple' interface -- a Web scraping interface --
   to locate distribution archives.

   .. method:: __init__(url, timeout=None, num_workers=10, **kwargs)

      :param url: The base URL to use for the simple service HTML pages.
      :type url: str
      :param timeout: How long (in seconds) to wait before giving up on a
                      remote resource.
      :type timeout: float
      :param num_workers: The number of worker threads created to perform
                          scraping activities.
      :type num_workers: int
      :param  kwargs: Passed to base class constructor.

.. class:: DistPathLocator

   This locator uses a :class:`~distlib.database.DistributionPath` instance to locate
   installed distributions.

   .. method:: __init__(url, distpath, **kwargs)

      :param distpath: The distribution path to use.
      :type distpath: :class:`~distlib.database.DistributionPath`
      :param  kwargs: Passed to base class constructor.

.. class:: AggregatingLocator(Locator)

   This locator uses a list of other aggregators and delegates finding projects
   to them. It can either return the first result found (i.e. from the first
   aggregator in the list provided which returns a non-empty result), or a
   merged result from all the aggregators in the list.

   .. method:: __init__(*locators, **kwargs)

      :param locators: A list of aggregators to delegate finding projects to.

      :type locators: list[Locator]

      :param merge: If this *kwarg* is ``True``, each aggregator in the list is
                    asked to provide results, which are aggregated into a
                    results dictionary. If ``False``, the first non-empty
                    return value from the list of aggregators is returned.
                    The locators are consulted in the order in which they're
                    passed in.

      :type merge: bool

.. class:: DependencyFinder

   This class allows you to recursively find all the distributions which a
   particular distribution depends on.

   .. method:: __init__(locator)

      Initialise an instance with the locator to be used for locating
      distributions.

   .. method:: find(requirement, metas_extras=None, prereleases=False)

      Find all the distributions needed to fulfill ``requirement``.

      :param requirement: A string of the from ``name (version)`` where
                          version can include an inequality constraint, or an instance
                          of :class:`~distlib.database.Distribution` (e.g.
                          representing a distribution on the local hard disk).
      :param meta_extras: A list of meta extras such as :test:, :build: and
                          so on, to be included in the dependencies.
      :param prereleases: If ``True``, allow pre-release versions to be
                          returned - otherwise, don't return prereleases
                          unless they're all that's available.
      :returns: A 2-tuple. The first element is a set of
                :class:`~distlib.database.Distribution` instances. The second element
                is a set of problems encountered during dependency resolution.
                Currently, if this set is non- empty, it will contain 2-tuples whose
                first element is the string 'unsatisfied' and whose second element is
                a requirement which couldn't be satisfied.

                In the set of :class:`~distlib.database.Distribution` instances
                returned, some attributes will be set:

                * The instance representing the passed-in ``requirement`` will
                  have the ``requested`` attribute set to ``True``.
                * All requirements which are not installation requirements (in
                  other words, are needed only for build and test) will have
                  the ``build_time_dependency`` attribute set to ``True``.


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

.. function:: locate(requirement, prereleases=False)

   This convenience function returns the latest version of a potentially
   downloadable distribution which matches a requirement (name and version
   constraints). If a potentially downloadable distribution (i.e. one with
   a download URL) is not found, ``None`` is returned -- otherwise, an
   instance of :class:`~distlib.database.Distribution` is returned. The
   returned instance will have, at a minimum, ``name``, ``version``,
   ``download_url`` and ``download_urls``.

   :param requirement: The name and optional version constraints of the
                       distribution to locate, e.g. ``'Flask'`` or
                       ``'Flask (>= 0.7, < 0.9)'``.
   :type requirement: str
   :param prereleases: If ``True``, prereleases are treated like normal
                       releases. The default behaviour is to not return any
                       prereleases unless they are the only ones which match
                       the requirement.
   :type prereleases: bool
   :returns: A matching instance of :class:`~distlib.database.Distribution`,
             or ``None``.

Variables
^^^^^^^^^

.. attribute:: default_locator

   This attribute holds a locator which is used by :func:`locate` to locate
   distributions.

The ``distlib.index`` package
--------------------------------

.. currentmodule:: distlib.index

Classes
^^^^^^^^

.. class:: PackageIndex

   This class represents a package index which is compatible with PyPI, the
   Python Package Index. It allows you to register projects, upload source
   and binary distributions (with support for digital signatures), upload
   documentation, verify signatures and get a list of hosts which are mirrors
   for the index.

   Methods:

   .. method:: __init__(url=None, mirror_host=None)

   Initialise an instance, setting instance attributes named from the keyword
   arguments.

   :param url: The root URL for the index. If not specified, the URL for PyPI
               is used ('http://pypi.org/pypi').
   :param mirror_host: The DNS name for a host which can be used to
                       determine available mirror hosts for the index. If not
                       specified, the value 'last.pypi.python.org' is used.

   .. method:: register(metadata)

      Register a project with the index.

      :param metadata: A :class:`~distlib.metadata.Metadata` instance. This
                       should have at least the ``Name`` and ``Version``
                       fields set, and ideally as much metadata as possible
                       about this distribution. Though it might seem odd to
                       have to specify a version when you are initially
                       registering a project, this is required by PyPI. You
                       can see this in PyPI's Web UI when you click the
                       "Package submission" link in the left-hand side menu.
      :returns: An ``urllib`` HTTP response returned by the index. If an error
                occurs, an :class:`~urllib.error.HTTPError` exception will be raised.

   .. method:: upload_file(metadata, filename, signer=None, sign_password=None, filetype='sdist', pyversion='source', keystore=None)

      Upload a distribution to the index.

      :param metadata: A :class:`~distlib.metadata.Metadata` instance. This
                       should have at least the ``Name`` and ``Version``
                       fields set, and ideally as much metadata as possible
                       about this distribution.
      :param file_name: The path to the file which is to be uploaded.
      :param signer: If specified, this needs to be a string identifying the
                     GnuPG private key which is to be used for signing the
                     distribution.
      :param sign_password: The passphrase which allows access to the private
                            key used for the signature.
      :param filetype: The type of the file being uploaded. This would have
                       values such as ``sdist`` (for a source distribution),
                       ``bdist_wininst`` for a Windows installer, and so on.
                       Consult the ``distutils`` documentation for the full
                       set of possible values.
      :param pyversion: The Python version this distribution is compatible
                        with. If it's a pure-Python distribution, the value
                        to use would be ``source`` - for distributions which
                        are for specific Python versions, you would use the
                        Python version in the form ``X.Y``.
      :param keystore: The path to a directory which contains the keys
                       used in signing. If not specified, the
                       instance's ``gpg_home`` attribute is used instead. This
                       parameter is not used unless a signer is specified.
      :returns: An ``urllib`` HTTP response returned by the index. If an error
                occurs, an :class:`~urllib.error.HTTPError` exception will be raised.

      .. versionchanged:: 0.1.9
         The ``keystore`` argument was added.

   .. method:: upload_documentation(metadata, doc_dir)

      Upload HTML documentation to the index. The contents of the specified
      directory tree will be packed into a .zip file which is then uploaded
      to the index.

      :param metadata: A :class:`~distlib.metadata.Metadata` instance. This
                       should have at least the ``Name`` and ``Version``
                       fields set.
      :param doc_dir: The path to the root directory for the HTML
                      documentation. This directory should be the one that
                      contains ``index.html``.
      :returns: An ``urllib`` HTTP response returned by the index. If an error
                occurs, an :class:`~urllib.error.HTTPError` exception will be raised.

   .. method:: verify_signature(self, signature_filename, data_filename, keystore=None)

      Verify a digital signature against a downloaded distribution.

      :param signature_filename: The path to the file which contains the
                                 digital signature.
      :param data_filename: The path to the file which was supposedly signed
                            to obtain the signature in ``signature_filename``.
      :param keystore: The path to a directory which contains the keys
                       used in verification. If not specified, the
                       instance's ``gpg_home`` attribute is used instead.
      :returns: ``True`` if the signature can be verified, else ``False``. If
                an error occurs (e.g. unable to locate the public key used to
                verify the signature), a ``ValueError`` is raised.

      .. versionchanged:: 0.1.9
         The ``keystore`` argument was added.

   .. method:: read_configuration()

      Read the PyPI access configuration.

   .. method:: save_configuration()

      Save the PyPI access configuration. You must have set ``username`` and
      ``password`` attributes before calling this method.

   .. method:: search(query, operation=None)

      Search the index for distributions matching a search query.

      :param query: The query, either as a string or a dictionary. If a string
                    ``'foo'`` is passed, it will be treated equivalently to
                    passing the dictionary ``{'name': 'foo'}``. The dictionary
                    can have the following keys:

                    * name
                    * version
                    * stable_version
                    * author
                    * author_email
                    * maintainer
                    * maintainer_email
                    * home_page
                    * license
                    * summary
                    * description
                    * keywords
                    * platform
                    * download_url
                    * classifiers (list of classifier strings)
                    * project_url
                    * docs_url (URL of the pythonhosted.org docs if they've
                      been supplied)

      :param operation: If specified, it should be either ``'and'`` or
                        ``'or'``. If not specified, ``'and'`` is assumed. This
                        is only used if a passed dictionary has multiple keys.
                        It determines whether the intersection or the union of
                        matches is returned.

      :returns: A (possibly empty) list of the distributions matching the
                query. Each entry in the list will be a dictionary with the
                following keys:

                * _pypi_ordering -- the internal ordering value (an integer)
                * name --The name of the distribution
                * version -- the version of the distribution
                * summary -- the summary for that version

      .. versionadded:: 0.1.8

   Additional attributes:

   .. attribute:: username

      The username to use when authenticating with the index.

   .. attribute:: password

      The password to use when authenticating with the index.

   .. attribute:: gpg

      The path to the signing and verification program.

   .. attribute:: gpg_home

      The location of the key database for the signing and verification
      program.

   .. attribute:: mirrors

      The list of hosts which are mirrors for this index.

   .. attribute:: boundary

      The boundary value to use when MIME-encoding requests to be sent to the
      index. This should be a byte-string.

The ``distlib.util`` package
-------------------------------

.. currentmodule:: distlib.util

Classes
^^^^^^^^

.. class:: Cache

   This base class implements common operations for ``distlib`` caches.

   .. method:: __init__(base)

      Initialise a cache instance with a specific directory which holds the
      cache.

      .. warning:: If ``base`` is specified and exists, it should exist and its
         permissions (relevant on POSIX only) should be set to 0700 - i.e. only
         the user of the running process has any rights over the directory. If
         this is not done, the application using this functionality may be
         vulnerable to security breaches as a result of other processes being
         able to interfere with the cache.

   .. method:: prefix_to_dir(prefix)

      Converts a prefix (e.g. the name of a resource's containing .zip, or a
      wheel pathname) into a directory name in the cache. This implementation
      delegates the work to :func:`~distlib.util.path_to_cache_dir`.


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
      instance of :class:`~distlib.database.InstalledDistribution`.

.. class:: HTTPSHandler

   A request handler inheriting from :class:`urllib.request.HTTPSHandler` which does
   certificate validation.

.. class:: HTTPSOnlyHandler

   A request handler inheriting from :class:`urllib.request.HTTPSHandler` which raises
   an exception if an attempt is made to open an HTTP (as opposed to HTTPS)
   connection.

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

   If a home directory is unavailable (no such directory, or if it's write-
   protected), a parent directory for the cache is determined using
   :func:`tempfile.mkdtemp`. This returns a directory to which only the
   running process has access (permission mask 0700 on POSIX), meaning that
   the cache should be isolated from possible malicious interference by other
   processes.

   .. note:: This cache is used for the following purposes:

      * As a place to cache package resources which need to be in the file
        system, because they are used by APIs which either expect filesystem
        paths, or to be able to use OS-level file handles. An example of the
        former is the :meth:`~ssl.SSLContext.load_verify_locations` method in
        Python's ``ssl`` module. The subdirectory ``resource-cache`` is used
        for this purpose.

      * As a place to cache shared libraries which are extracted as a result
        of calling the :meth:`~distlib.wheel.Wheel.mount` method of the
        :class:`~distlib.wheel.Wheel` class. The subdirectory ``dylib-cache`` is used
        for this purpose.

      The application using this cache functionality, whether through the
      above mechanisms or through using the value returned from here directly,
      is responsible for any cache cleanup that is desired. Note that on
      Windows, you may not be able to do cache cleanup if any of the cached
      files are open (this will generally be the case with shared libraries,
      i.e. DLLs). The best way to do cache cleanup in this scenario may be on
      application startup, before any resources have been cached or wheels
      mounted.

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


The ``distlib.wheel`` package
-----------------------------

.. currentmodule:: distlib.wheel

This package has functionality which allows you to work with wheels (see :pep:`427`).


Attributes
^^^^^^^^^^

.. attribute:: cache

   An instance of :class:`distlib.util.Cache`. This can be set after module
   import, but before calling any functionality which uses it, to ensure
   that the cache location is entirely under your control.

   If you call the ``mount`` method of a :class:`Wheel` instance, and the
   wheel is successfully mounted and contains C extensions, the cache will
   be needed, and if not set by you, an instance with a default location
   will be created. See :func:`distlib.util.get_cache_base` for more
   information.


.. attribute:: COMPATIBLE_TAGS

   A set of (``pyver``, ``abi``, ``arch``) tags which are compatible with this
   Python implementation.


Classes
^^^^^^^

.. class:: Wheel

   This class represents wheels -- either existing wheels, or wheels to be built.

   .. method:: __init__(spec)

      Initialise an instance from a specification.

      :param spec: This can either be a valid filename for a wheel (for when
                   you want to work with an existing wheel), or just the
                   ``name-version-buildver`` portion of a wheel's filename (for
                   when you're going to build a wheel for a known version and
                   build of a named project).
      :type spec: str

   .. method:: build(paths, tags=None, wheel_version=None)

      Build a wheel. The ``name``, ``version`` and ``buildver`` should already
      have been set correctly.

      :param paths: This should be a dictionary with keys ``'prefix'``,
                    ``'scripts'``, ``'headers'``, ``'data'`` and one of
                    ``'purelib'`` or ``'platlib'``. These must point to valid
                    paths if they are to be included in the wheel.
      :param tags: If specified, this should be a dictionary with optional keys
                   ``'pyver'``, ``'abi'`` and ``'arch'`` indicating lists of
                   tags which indicate environments with which the wheel is
                   compatible.
      :param wheel_version: If specified, this is written to the wheel's
                            "Wheel-Version" metadata. If not specified, the
                            implementation's latest supported wheel version is
                            used.

   .. method:: install(self, paths, maker, **kwargs)

      Install from a wheel.

      :param paths: This should be a dictionary with keys ``'prefix'``,
                    ``'scripts'``, ``'headers'``, ``'data'``, ``'purelib'``
                    and ``'platlib'``. These must point to valid paths to which
                    files may be written if they are in the wheel. Only one of
                    the ``'purelib'`` and ``'platlib'`` paths will be used (in
                    the case where they are different), depending on whether
                    the wheel is for a pure-Python distribution.

      :param maker: This should be set to a suitably configured instance of
                    :class:`~distlib.scripts.ScriptMaker`. The ``source_dir`` and
                    ``target_dir`` arguments can be set to ``None`` when creating the
                    instance - these will be set to appropriate values inside this
                    method.

      :param warner: If specified, should be a callable that will be called
                     with (software_wheel_ver, file_wheel_ver) if they differ.
                     They will both be in the form of tuples (major_ver,
                     minor_ver).

      :param lib_only: It's conceivable that one might want to install only
                       the library portion of a package -- not installing
                       scripts, headers, data and so on. If ``lib_only`` is
                       specified as ``True``, only the ``site-packages``
                       contents will be installed.


   .. method:: is_compatible()

      Determine whether this wheel instance is compatible with the
      running Python.

      :return: ``True`` if compatible, else ``False``.

   .. method:: is_mountable()

      Determine whether this wheel instance is indicated suitable for
      mounting in its metadata.

      :return: ``True`` if mountable, else ``False``.

   .. method:: mount(append=False)

      Mount the wheel so that its contents can be imported directly, without
      the need to install the wheel. If the wheel contains C extensions and
      has metadata about these extensions, the extensions are also available
      for import.

      If the wheel tags indicate it is not compatible with the running Python,
      a :class:`~distlib.DistlibException` is raised. (The :meth:`is_compatible`
      method is used to determine compatibility.)

      If the wheel is indicated as not suitable for mounting, a
      :class:`distlib.DistlibException` is raised.  (The :meth:`is_mountable`
      method is used to determine mountability.)

      :param append: If ``True``, the wheel's pathname is added to the end of
                     ``sys.path``. By default, it is added to the beginning.

      .. note:: Wheels may state in their metadata that they are not
         intended to be mountable, in which case this method will raise a
         :class:`distlib.DistlibException` with a suitable message. If C extensions
         are extracted, the location for extraction will be under the
         directory ``dylib-cache`` in the directory returned by
         :func:`~distlib.util.get_cache_base`.

         Wheels may be marked by their publisher as unmountable to indicate
         that running directly from a zip is not supported by the packaged
         software.

    .. method:: unmount()

      Unmount the wheel so that its contents can no longer be imported
      directly. If the wheel contains C extensions and has metadata about these
      extensions, the extensions are also made unavailable for import.

      .. note:: Unmounting does not automatically clean up any extracted C
         extensions, as that may not be desired (and not possible, on Windows,
         because the files will be open). See the
         :func:`~distlib.util.get_cache_base` documentation for suggested
         cleanup scenarios.

    .. method:: verify()

      Verify sizes and hashes of the wheel's contents against the sizes and
      hashes declared in the wheel's RECORD. Raise a
      :class:`distlib.DistlibException` if a size or digest mismatch is detected.

      .. versionadded:: 0.1.8

    .. method:: update(modifier, dest_dir=None, **kwargs)

      Allows a user-defined callable access to the contents of a wheel. The
      callable can modify the contents of the wheel, add new entries or
      remove entries. The method first extracts the wheel's contents to a
      temporary location, and then calls the modifier like this::

          modified = modifier(path_map, **kwargs)

      where ``path_map`` is a dictionary mapping archive paths to the location
      of the corresponding extracted archive entry, and ``kwargs`` is whatever
      was passed to the ``update`` method. If the modifier returns ``True``,
      a new wheel is built from the (possibly updated) contents of ``path_map``
      and, as a final step, copied to the location of the original wheel
      (hence effectively modifying it in-place). The passed ``path_map`` will
      contain all of the wheel's entries other than the ``RECORD`` entry (which
      will be recreated if a new wheel is built).

      .. versionadded:: 0.1.8

   .. attribute:: name

      The name of the distribution.

   .. attribute:: version

      The version of the distribution

   .. attribute:: buildver

      The build tag for the distribution.

   .. attribute:: pyver

      A list of Python versions with which the wheel is compatible. See
      :pep:`427` and :pep:`425` for details.

   .. attribute:: abi

      A list of application binary interfaces (ABIs) with which the wheel is
      compatible. See :pep:`427` and :pep:`425` for details.

   .. attribute:: arch

      A list of architectures with which the wheel is compatible. See
      :pep:`427` and :pep:`425` for details.

   .. attribute:: dirname

      The directory in which a wheel file is found/to be created.

   .. attribute:: filename

      The filename of the wheel (computed from the other attributes)

   .. attribute:: metadata

      The metadata for the distribution in the wheel, as a
      :class:`~distlib.metadata.Metadata` instance.

   .. attribute:: info

      The wheel metadata (contents of the ``WHEEL`` metadata file) as a
      dictionary.

   .. attribute:: exists

      Whether the wheel file exists.

      .. versionadded:: 0.1.8


Functions
^^^^^^^^^

.. function:: is_compatible(wheel, tags=None)

   Indicate if a wheel is compatible with a set of tags. If any combination of
   the tags of ``wheel`` is found in ``tags``, then the wheel is considered to
   be compatible.

   :param wheel: A :class:`Wheel` instance or the filename of a wheel.
   :param tags: A set of tags to check for compatibility. If not specified,
                it defaults to the set of tags which are compatible with this
                Python implementation.
   :return: ``True`` if compatible, else ``False``.


The ``distlib.versions`` package
--------------------------------

.. currentmodule:: distlib.version

This package has functionality which allows you to work with standard versions (see
:pep:`440`) but also legacy versions and semantic versions.

Classes
^^^^^^^

.. class:: Version

   This base class represents a version.

.. class:: Matcher

   This base class represents a version matcher. It's used for parsing and comparing
   versions.

.. class:: VersionScheme

   This class represents a version scheme (e.g. legacy, semantic or standard).

.. class:: NormalizedVersion

   This class represents :pep:`440`-compatible versions.

.. class:: NormalizedMatcher

   This class represents a matcher for :pep:`440`-compatible versions.


Functions
^^^^^^^^^

.. function:: get_scheme(name)

   Return a :class:`VersionScheme` instance corresponding to the specified *name*.

The ``distlib.manifest`` package
--------------------------------

.. currentmodule:: distlib.manifest

This package has functionality which allows you to maintain a manifest, i.e. a list of
files which makes up a source distribution.

Classes
^^^^^^^

.. class:: Manifest

   This base class represents a manifest. You can explore files under a directory,
   add and remove files, and process directives to e.g. include or exclude files based
   on patterns.

   .. attribute:: files

      The list of paths representing files included in the manifest.

   .. attribute:: allfiles

      The list of paths representing all files in the directory tree which the manifest
      is based on.

   .. attribute:: base

      The base directory on which this manifest instance is based.

   .. method:: process_directive(directive)

      Process a *directive* which either adds some files from ``allfiles`` to
        ``files``, or removes some files from ``files``.

The ``distlib.metadata`` package
--------------------------------

.. currentmodule:: distlib.metadata

This package has functionality which allows you to manage a distribution's metadata.

Classes
^^^^^^^

.. class:: Metadata

   This class represents a distribution's metadata.

   .. method:: todict()

      Returns the metadata as a dictionary.


The ``distlib.markers`` package
--------------------------------

.. currentmodule:: distlib.markers

This package has functionality for interpreting environment markers.

Functions
^^^^^^^^^

.. function:: interpret(marker, execution_context=None)

   This function returns the result of interpreting an environment marker in optional
   execution context, which is used for name lookups.


Next steps
----------

You might find it helpful to look at the
`mailing list <http://mail.python.org/mailman/listinfo/distutils-sig/>`_.
