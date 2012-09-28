.. _internals:

Distlib's design
================

This is the section containing some discussion of how ``distlib``'s design was
arrived at, as and when time permits.

The ``resources`` API
---------------------

This section describes the design of the ``distlib`` API relating to accessing
'resources', which is a convenient label for data files associated with Python
packages.

The problem we're trying to solve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Developers often have a need to co-locate data files with their Python
packages. Examples of these might be:

* Templates, commonly used in web applications
* Translated messages used in internationalisation/localisation

The stdlib does not provide a uniform API to access these resources. A common
approach is to use ``__file__`` like this::

    base = os.path.dirname(__file__)
    data_filename = os.path.join(base, 'data.bin')
    with open(data_filename, 'rb') as f:
        # read the data from f

However, this approach fails if the package is deployed in a .zip file.

To consider how to provide a minimal uniform API to access resources in Python
packages, we'll assume that the requirements are as follows:

* All resources are regarded as binary. The using application is expected to
  know how to convert resources to text, where appropriate.
* All resources are read-only.
* It should be possible to access resources either as streams, or as their
  entire data as a byte-string.
* Resources will have a unique, identifying name which is text. Resources will
  be hierarchical, and named using filesystem-like paths using '/' as a
  separator. The library will be responsible for converting resource names
  to the names of the underlying representations (e.g. encoding of file names
  corresponding to resource names).
* Some resources are containers of other resoures, some are not. For
  example, a resource ``nested/nested_resource.bin`` in a package would not
  contain other resources, but implies the existence of a resource
  ``nested``, which contains ``nested_resource.bin``.
* Resources can only be associated with packages, not with modules. That's
  because with peer modules ``a.py`` and ``b.py``, there's no obvious location
  for data associated only with ``a``: both ``a`` and ``b`` are in the same
  directory. With a package, there's no ambiguity, as a package is associated
  with a specific directory, and no other package can be associated with that
  directory.
* Support should be provided for access to data deployed in the file system or
  in packages contained in .zip files, and third parties should be able to
  extend the facilities to work with other storage formats which support import
  of Python packages.


A minimal solution
^^^^^^^^^^^^^^^^^^

We know that we will have to deal with resources, so it seems natural that
there would be a ``Resource`` class in the solution. From the requirements, we
can see that a ``Resource`` would have the following:

* A ``name`` property identifying the resource.
* A ``as_stream`` method allowing access to the resource data as a binary 
  stream. This is not a property, because a new stream is returned each time
  this method is called. The returned stream should be closed by the caller.
* A ``bytes`` property returning the entire contents of the resource as a byte
  string.
* A ``size`` property indicating the size of the resource (in bytes).
* An ``is_container`` property indicating whether the resource is a container
  of other resources.
* A ``resources`` property returning the names of resources contained within
  the resource.

The ``Resource`` class would be the logical place to perform sanity checks
which relate to all resources. For example:

* It doesn't make sense to ask for the ``bytes`` or ``size`` properties or call
  the ``as_stream`` method of a container resource.
* It doesn't make sense to ask for the ``resources`` property of a resource
  which is *not* a container.

It seems reasonable to raise exceptions for incorrect property or method
accesses.

We know that we need to support resource access in the file system as well as
.zip files, and to support other sources of storage which might be used to
import Python packages. Since import and loading of Python packages happens
through :pep:`302` importers and loaders, we can deduce that the mechanism used
to find resources in a package will be closely tied to the loader for that
package.

We could consider an API for finding resources in a package like this::

    def find_resource(pkg, resource_name):
        # return a Resource instance for the resource

and then use it like this::

    r1 = find_resource(pkg, 'foo')
    r2 = find_resource(pkg, 'bar')

However, we'll often have situations where we will want to get multiple
resources from a package, and in certain applications we might want to
implement caching or other processing of resources before returning them.
The above API doesn't facilitate this, so let's consider delegating the finding
of resources in a package to a *finder* for that package. Once we get a finder,
we can hang on to it and ask it to find multiple resources. Finders
can be extended to provide whatever caching and preprocessing an application
might need.

To get a finder for a package, let's assume there's a ``finder`` function::

    def finder(pkg):
        # return a finder for the specified package

We can use it like this::

    f = finder(pkg)
    r1 = f.find('foo')
    r2 = f.find('bar')

The ``finder`` function knows what kind of finder to return for a particular
package through the use of a registry. Given a package, ``finder`` can
determine the loader for that package, and based on the type of loader, it can
instantiate the right kind of finder. The registry maps loader types to
callables that return finders. The callable is called with a single
argument -- the Python module object for the package.

Given that we have finders in the design, we can identify
``ResourceFinder`` and ``ZipResourceFinder`` classes for the two import
systems we're going to support. We'll make ``ResourceFinder`` a concrete
class rather than an interface - it'll implement getting resources from
packages stored in the file system. ``ZipResourceFinder`` will be a
subclass of ``ResourceFinder``.

Since there is no loader for file system packages when the C-based import
system is used, the registry will come with the following mappings:

* ``type(None)`` -> ``ResourceFinder``
* ``_frozen_importlib.SourceFileLoader -> ``ResourceFinder``
* ``zipimport.zipimporter`` -> ``ZipResourceFinder``

Users of the API can add new or override existing mappings using the following
function::

    def register_finder(loader, finder_maker):
        # register ``finder_maker`` to make finders for packages with a loader
        # of the same type as ``loader``.

Typically, the ``finder_maker`` will be a class like ``ResourceFinder`` or
``ZipResourceFinder``, but it can be any callable which takes the Python module
object for a package and returns a finder.

Let's consider in more detail what finders look like and how they interact with
the ``Resource`` class. We'll keep the Resource class minimal; API users never
instantiate ``Resource`` directly, but call a finder's ``find`` method to
return a ``Resource`` instance. A finder could return an instance of a
``Resource`` subclass if really needed, though it shouldn't be necessary in
most cases. If a finder can't find a resource, it should return ``None``.

The Resource constructor will look like this::

    def __init__(self, finder, name):
        self.finder = finder
        self.name = name
        # other initialisation, not specified

and delegate as much work as possible to its finder. That way, new import
loader types can be supported just by implementing a suitable
``XXXResourceFinder`` for that loader type.

What a finder needs to do can be exemplified by the following skeleton for
``ResourceFinder``::

    class ResourceFinder(object):
        def __init__(self, module):
            # initialise finder for the specified package

        def find(self, resource_name):
            # find and return a ``Resource`` instance or ``None``

        def is_container(self, resource):
            # return whether resource is a container

        def get_bytes(self, resource):
            # return the resource's data as bytes

        def get_size(self, resource):
            # return the size of the resource's data in bytes

        def get_stream(self, resource):
            # return the resource's data as a binary stream

        def get_resources(self, resource):
            # return the resources contained in this resource as a set of
            # (relative) resource names


The ``scripts`` API
-------------------

This section describes the design of the ``distlib`` API relating to
installing scripts.

The problem we're trying to solve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installing scripts is slightly more involved than simply copying files from
source to target, for the following reasons:

* On POSIX systems, scripts need to be made executable. To cater for scenarios
  where there are multiple Python versions installed on a computer, scripts
  need to have their shebang lines adjusted to point to the correct
  interpreter. This requirement is commonly found when virtual environments
  (venvs) are in use, but also in other multiple-interpreter scenarios.
* On Windows systems, which don't support shebang lines natively, some
  alternate means of finding the correct interpreter need to be provided.
  Following the acceptance and implementation of PEP 397, a shebang-
  interpreting launcher will be available in Python 3.3 and later, and a
  standalone version of it for use with earlier Python versions is also
  available. However, where this can't be used, an alternative approach
  using executable launchers installed with the scripts may be necessary.
  (That is the approach taken by ``setuptools``.) 

  Windows also has two types of launchers - console applications and
  Windows applications. The appropriate launcher needs to be used for
  scripts.
* Some scripts are effectively just callable code in a Python package,
  with boilerplate for importing that code, calling it and returning
  its return value as the script's return code. It would be useful to
  have the boilerplate standardised, so that developers need just specify
  which callables to expose as scripts, and under what names, using e.g. a
  ``name = callable`` syntax. (This is the approach taken by ``setuptools``
  for the popular ``console_scripts`` feature).

A minimal solution
^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.scripts

Script handling in ``distutils`` and ``setuptools`` is done in two phases:
'build' and 'install'. Whether a particular packaging tool chooses to do
the 'heavy lifting' of script creation (i.e. the things referred to
above, beyond simple copying) in 'build' or 'install' phases, the job is
the same. To abstract out just the functionality relating to scripts,
in an extensible way, we can just delegate the work to a class,
unimaginatively called :class:`~distlib.scripts.ScriptMaker`. Given the
above requirements, together with the more basic requirement of being able
to do 'dry-run' installation, we need to provide a ``ScriptMaker`` with the
following items of information:

* Where source scripts are to be found.
* Where scripts are to be installed.
* Whether, on Windows, executable launchers should be added.
* Whether a dry-run mode is in effect.

These dictate the form that :meth:`ScriptMaker.__init__`
will take.

In addition, other methods suggest themselves for :class:`ScriptMaker`:

* A :meth:`~ScriptMaker.make` method, which takes a *specification*, which is
  either a filename or a 'wrap me a callable' indicator which looks
  like this::

      name = some_package.some_module:some_callable [ flag(=value) ... ]

  The ``name`` would need to be a valid filename for a script, and the
  ``some_package.some_module`` part would indicate the module where the
  callable resides. The ``some_callable`` part identifies the callable,
  and optionally you can have flags, which the :class:`ScriptMaker` instance
  must know how to interpret. One flag would be ``'gui'``, indicating that
  the launcher should be a Windows application rather than a console
  application, for GUI-based scripts which shouldn't show a console window.
  
  The above specification (apart from the flags) is used by ``setuptools``
  for the 'console_scripts' feature.  See :ref:`flag-formats` for more
  information about flags.

  It seems sensible for this method to return a list of absolute paths of
  files that were installed (or would have been installed, but for the
  dry-run mode being in effect).

* A :meth:`~ScriptMaker.make_multiple` method, which takes an iterable of
  specifications and just runs calls :meth:`~ScriptMaker.make` on each
  item iterated over, aggregatig the results to return a list of absolute paths
  of all files that were installed (or would have been installed, but for the
  dry-run mode being in effect).

  One advantage of having this method is that you can override it in a
  subclass for post-processing, e.g. to run a tool like ``2to3``, or an
  analysis tool, over all the installed files.

* The callable specification is sufficiently complex and a possible source
  of extension that another method, :meth:`~ScriptMaker.get_callable`, can
  be used to encapsulate the details of the callable format. This would
  take a specification and return ``None``, if the specification didn't
  match the callable format, or the various components (name, module name,
  callable name and flags) if it did match.

.. _flag-formats:

Flag formats
~~~~~~~~~~~~

Flags, if present, are enclosed by square brackets. Each flag can have the
format of just an alphanumeric string, optionally followed by an '=' and a
value (with no intervening spaces). Multiple flags can be separated by ','
and whitespace. The following would be valid flag sections::

  [a,b,c]
  [a, b, c]
  [a=b, c=d, e, f=g, 9=8]

whereas the following would be invalid::

 []
 [\]
 [a,]
 [a,,b]
 [a=,b,c]
  

Next steps
----------

You might find it helpful to look at the :ref:`reference`.
