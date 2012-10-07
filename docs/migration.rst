.. _migration:

Migrating from older APIs
=========================

This section has information on migration from older APIs.

The ``pkg_resources`` resource API
----------------------------------

Basic resource access
~~~~~~~~~~~~~~~~~~~~~

``resource_exists(package, resource_name)``
    ``finder(package).find(resource_name) is not None``

``resource_stream(package, resource_name)``
    ``finder(package).find(resource_name).as_stream()``

``resource_string(package, resource_name)``
    ``finder(package).find(resource_name).bytes``

``resource_isdir(package, resource_name)``
    ``finder(package).find(resource_name).is_container``

``resource_listdir(package, resource_name)``
    ``finder(package).find(resource_name).resources``

Resource extraction
~~~~~~~~~~~~~~~~~~~

``resource_filename(package, resource_name)``
    ``finder(package).find(resource_name).file_path``

``set_extraction_path(extraction_path)``
    This has no direct analogue, but you can achieve equivalent results by
    doing something like the following::

        from distlib import resources

        resources.cache = resources.Cache(extraction_path)

    before accessing the ``file_path`` property of any :class:`Resource`.
    Note that if you have accessed the ``file_path`` property for a resource
    *before* doing this, the cache may already have extracted files.

``cleanup_resources(force=False)``
    This is not actually implemented in ``pkg_resources`` -- it's a no-op.
    You could achieve the analogous result using::

        from distlib import resources

        not_removed = resources.cache.clear()

Provider interface
~~~~~~~~~~~~~~~~~~

You can provide an ``XXXResourceFinder`` class which finds resources in custom
storage containers, and works like ``ResourceFinder``. Although it shouldn't
be necessary, you could also return a subclass of :class:`Resource` from your
finders, to deal with custom requirements which aren't catered for.

``get_cache_path(archive_name, names=())``
    There's no analogue for this, as you shouldn't need to care about whether
    particular resources are implemented in archives or not. If you need this
    API, please give feedback with more information about your use cases.

``extraction_error()``
    There's no analogue for this. The :meth:`Cache.get` method, which writes
    a resource's bytes to a file in the cache, will raise any exception caused
    by underlying I/O. If you need to handle this in the cache layer, you can
    subclass :class:`Cache` and override :meth:`get`. If that doesn't work for
    you, please give feedback with more information about your use cases.

``postprocess(tempname, filename)``
    There's no analogue for this. The :meth:`Cache.get` method, which writes
    a resource's bytes to a file in the cache, can be overridden to perform any
    custom post-processing. If that doesn't work for you, please give feedback
    with more information about your use cases.

The ``pkg_resources`` entry point API
-------------------------------------

Entry points in ``pkg_resources`` are equivalent to a registry. The keys to
the registry are just names in a hierarchical namespace delineated with periods
(like Python packages, so we'll refer to them as *pkgnames* in the following
discussion). These keys are called *groups* in ``pkg_resources`` documentation,
though that term is a little ambiguous. In Eclipse, for example, they are
called *extension point IDs*, which is a little closer to the intended usage.
In ``distlib``, we'll use the term ``extension point ID`` for this reason.

The values associated in the registry with an extension point ID are a list of
strings with the format::

    name = prefix [ ":" suffix ] [ "[" flags "]" ]

where ``name``, ``prefix`` and ``suffix`` are ``pkgnames``, ``suffix`` and
``flags`` are optional, and ``flags`` follow the description in
:ref:`flag-formats`.

Any installed distribution can offer up values for any extension point ID, and
a set of distributions (such as the set of installed distributions on
``sys.path``) conceptually has an aggregation of these values.

In ``distlib``, the implementation of the registry is slightly different from
that of ``pkg_resources``. A :class:`Distribution` instance has a ``registry``
attribute, which is a dictionary keyed by extension point ID and whose values
are :class:`Registry` objects.


Here are the ``pkg_resources`` functions, and how to achieve the equivalent
in ``distlib``. In cases where the ``pkg_resources`` functions take
distribution names, in ``distlib`` you get the corresponding
:class:`Distribution` instance, using::

    dist = dist_set.get_distribution(distname)

and then ask that instance for the things you need.

``load_entry_point(distname, groupname, name)``
    ``dist.registry[groupname].resolve(name)``

``get_entry_info(distname, groupname, name)``
    ``dist.registry[groupname, name]``

``get_entry_map(distname, groupname=None)``
    ``dist.registry[groupname]``

``iter_entry_points(groupname, name=None)``
    ``dist_set.get_registered_entries(groupname)``


