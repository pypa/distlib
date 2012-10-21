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
* It should be possible to access the contents of any resource through a
  file on the file system. This is to cater for any external APIs which need to
  access the resource data as files (examples would be a shared library for
  linking using ``dlopen()`` on POSIX, or any APIs which need access to
  resource data via OS-level file handles rather than Python streams).


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
            "Initialise finder for the specified package"

        def find(self, resource_name):
            "Find and return a ``Resource`` instance or ``None``"

        def is_container(self, resource):
            "Return whether resource is a container"

        def get_bytes(self, resource):
            "Return the resource's data as bytes"

        def get_size(self, resource):
            "Return the size of the resource's data in bytes"

        def get_stream(self, resource):
            "Return the resource's data as a binary stream"

        def get_resources(self, resource):
            """
            Return the resources contained in this resource as a set of
            (relative) resource names
            """


Dealing with the requirement for access via file system files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To cater for the requirement that the contents of some resources be made
available via a file on the file system, we'll assume a simple caching
solution that saves any such resources to a local file system cache, and
returns the filename of the resource in the cache. We need to divide the
work between the finder and the cache. We'll deliver the cache function
through a :class:`Cache` class, which will have the following methods:

* A constructor which takes an optional base directory for the cache. If
  none is provided, we'll construct a base directory of the form::

  <rootdir>/.distlib/resource-cache

  where ``<rootdir>`` is the user's home directory. On Windows, if the
  environment specifies a variable named ``LOCALAPPDATA``, its value
  will be used as ``<rootdir>``; otherwise, the user's home directory
  will be used.

* A :meth:`get` method which takes a ``Resource`` and returns a file system
  filename, such that the contents of that named file will be the contents
  of the resource.

* An :meth:`is_stale` method which takes a ``Resource`` and its corresponding
  file system filename, and returns whether the file system file is stale
  when compared with the resource. Knowing that cache invalidation is hard,
  the default implementation just returns ``True``.

* A :meth:`prefix_to_dir` method which converts a prefix to a directory name.
  We'll assume that for the cache, a resource path can be divided into two
  parts: the *prefix* and the *subpath*. For resources in a .zip file, the
  prefix would be the pathname of the archive, while the subpath would be the
  path inside the archive. For a file system resource, since it is already in
  the file system, the prefix would be ``None`` and the subpath would be the
  absolute path name of the resource. The :meth:`prefix_to_dir` method's job
  is to convert a prefix (if not ``None``) to a subdirectory in the cache
  that holds the cached files for all resources with that prefix. We'll
  delegate the determination of a resource's prefix and subpath to its finder,
  using a :meth:`get_cache_info` method on finders, which takes a ``Resource``
  and returns a (``prefix``, ``subpath``) tuple.

  The default implementation will use :func:`os.splitdrive` to see if there's
  a Windows drive, and convert its ``':'`` to ``'---'``. The rest of the
  prefix will be converted by replacing ``'/'`` by ``'--'``, and appending
  ``'.cache'`` to the result.

The cache will be activated when the ``file_path`` property of a ``Resource``
is accessed. This will be a cached property, and will call the cache's
:meth:`get` method to obtain the file system path.


The ``scripts`` API
-------------------

This section describes the design of the ``distlib`` API relating to installing
scripts.

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

* The details of the callable specification can be encapsulated in a utility
  function, :func:`~distlib.util.get_exports_entry`. This would take a specification
  and return ``None``, if the specification didn't match the callable format,
  or an instance of :class:`ExportEntry` if it did match.

In addition, the following attributes on a ``ScriptMaker`` could be further used
to refine its behaviour:

* ``force`` to indicate when scripts should be copied from source to target
  even when timestamps show the target is up to date.
* ``set_mode`` to indicate whether, on Posix, the execute mode bits should be
  set on the target script.

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


The ``version`` API
-------------------

This section describes the design of the ``distlib`` API relating to versions.

The problem we're trying to solve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Distribution releases are named by versions, and versions have two principal
uses:

* Identifying a particular release, and determining whether or not it is
  earlier or later than some other release.

* When specifying other distributions that a distribution release depends on,
  specifying constraints governing the releases of those distributions that are
  depended upon.

In addition, qualitative information may be given by the version format about
the quality of the release: e.g. alpha versions, beta versions, stable
releases, hot-fixes following a stable release. The following excerpt from
:pep:`386` defines the requirements for versions:

* It should be possible to express more than one versioning level (usually this
  is expressed as major and minor revision and, sometimes, also a micro
  revision).
* A significant number of projects need special meaning versions for
  "pre-releases" (such as "alpha", "beta", "rc"), and these have widely used
  aliases ("a" stands for "alpha", "b" for "beta" and "c" for "rc"). And these
  pre-release versions make it impossible to use a simple alphanumerical
  ordering of the version string components. (e.g. 3.1a1 < 3.1)
* Some projects also need "post-releases" of regular versions, mainly for
  maintenance purposes, which can't be clearly expressed otherwise.
* Development versions allow packagers of unreleased work to avoid version
  clashes with later stable releases.

There are a number of version schemes in use. The ones of most interest in the
Python ecosystem are:

* Loose versioning in ``distutils``. *Any* version number is allowed, with
  lexicographical ordering. No support exists for pre- and post-releases,
  and lexicographical ordering can be unintuitive (e.g. '1.10' < '1.2.1')

* Strict versioning in ``distutils``, which supports slightly more
  structure. It allows for up to three dot-separated numeric components, and
  support for multiple alpha and beta releases. However, there is no support
  for release candidates, nor for post-release versions.

* Versioning in ``setuptools``/``distribute``. This is described in
  :pep:`386` in `this section
  <http://www.python.org/dev/peps/pep-0386/#setuptools>`_ -- it's perhaps the
  most widely used Python version scheme, but since it tries to be very
  lexible and work with a wide range of conventions, it ends up allowing a
  very chaotic mess of version conventions in the Python community as a whole.

* The proposed versioning scheme described in :pep:`386`, in `this section
  <http://www.python.org/dev/peps/pep-0386/#the-new-versioning-algorithm>`_.

* `Semantic versioning <http://semver.org/>`_, which is rational, simple and
  well-regarded in the software community in general. However, for reasons
  not immediately apparent, it has not been mentioned in :pep:`386` and not
  compared with the new versioning scheme proposed therein.

Although the new versioning scheme mentioned in PEP 386 was implemented in
``distutils2`` and that code has been copied over to ``distlib``, there are
many projects on PyPI which do not conform to it, but rather to the "legacy"
versioning schemes in ``distutils``/``setuptools``/``distribute``. These
schemes are deserving of some support not because of their intrinsic qualities,
but due to their ubiquity in projects registered on PyPI.

A minimal solution
^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.version

Since ``distlib`` is a low-level library which might be used by tools which
work with existing projects, the internal implementation of versions has
changed slightly from ``distutils2`` to allow better support for legacy
version numbering. Since the re-implementation facilitated adding semantic
version support at minimal cost, this has also been provided.

The basic scheme is as follows. The differences between versioning schemes
is catered for by having a single function for each scheme which converts
a string version to an appropriate tuple which acts as a key for sorting
and comparison of versions. We have a base class, ``Version``, which defines
any common code. Then we can have subclasses ``NormalizedVersion`` (PEP-386),
``LegacyVersion`` (``distribute``/``setuptools``) and ``SemanticVersion``.

To compare versions, we just check type compatibility and then compare the
corresponding tuples.

Matchers take a name followed by a set of constraints in parentheses.
Each constraint is an operation together with a version string which
needs to be converted to the corresponding version instance.

In summary, the following attributes can be identified for ``Version`` and
``Matcher``:

Version:
   - version string passed in to constructor (stripped)
   - parser to convert string string to tuple
   - compare functions to compare with other versions of same type

Matcher:
   - version string passed in to constructor (stripped)
   - name of distribution
   - list of constraints
   - parser to convert string to name and set of constraints,
     using the same function as for ``Version`` to convert the version
     strings in the constraints to version instances
   - method to match version to constraints and return True/False

Given the above, it appears that all the functionality *could* be provided
with a single class per versioning scheme, with the *only* difference
between them being the function to convert from version string to tuple.
Any instance would act as either version or predicate, would display itself
differently according to which it is, and raise exceptions if the wrong
type of operation is performed on it (matching only allowed for predicate
instances; <=, <, >=, > comparisons only allowed for version instances;
and == and != allowed for either.

However, the use of the same class to implement versions and predicates leads
to ambiguity, because of the very loose project naming and versioning schemes
allowed by PyPI. For example, "Hello 2.0" could be a valid project name, and
"5" is a project name actually registered on PyPI. If distribution names can
look like versions, it's hard to discern the developer's intent when creating
an instance with the string "5". So, we make separate classes for Version
and Matcher.

For ease of testing, the module will define, for each of the supported
schemes, a function to do the parsing (as no information is needed other than
the string), and the parse method of the class will call that function::

    def normalized_key(s):
        "parse using PEP-386 logic"

    def legacy_key(s):
        "parse using distribute/setuptools logic"

    def semantic_key(s):
        "parse using semantic versioning logic"

    class Version:
        # defines all common code

        def parse(self, s):
            raise NotImplementedError('Please implement in a subclass')

and then::

    class NormalizedVersion(Version):
        def parse(self, s): return normalized_key(s)

    class LegacyVersion(Version):
        def parse(self, s): return legacy_key(s)

    class SemanticVersion(Version):
        def parse(self, s): return semantic_key(s)

And a custom versioning scheme can be devised to work in the same way::

    def custom_key(s):
       """
       convert s to tuple using custom logic, raise UnsupportedVersionError
       on problems
       """

    class CustomVersion(Version):
        def parse(self, s): return custom_key(s)

The matcher classes are pretty minimal, too::

    class Matcher(object):
        version_class = None

        def match(self, string_or_version):
            """
            If passed a string, convert to version using version_class,
            then do matching in a way independent of version scheme in use
            """

and then::

    class NormalizedMatcher(Matcher):
        version_class = NormalizedVersion

    class LegacyMatcher(Matcher):
        version_class = LegacyVersion

    class SemanticMatcher(Matcher):
        version_class = SemanticVersion

Ideally one would want to work with the PEP 386 scheme, but there might be times
when one needs to work with the legacy scheme (for example, when investigating
dependency graphs of existing PyPI projects). Hence, the important aspects of
each scheme are bundled into a simple :class:`VersionScheme` class::

    class VersionScheme(object):
        def __init__(self, key, matcher):
            self.key = key          # version string -> tuple converter
            self.matcher = matcher  # Matcher subclass for the scheme

Of course, the version class is also available through the matcher's
``version_class`` attribute.

The appropriate scheme can be fetched by using the :func:`get_scheme` function,
which is defined thus::

    def get_scheme(scheme_name):
        "Get a VersionScheme for the given scheme_name."

Allowed names are ``'normalized'``, ``'legacy'``, ``'semantic'`` and
``'default'`` (which points to the same as ``''``). If an unrecognised name is
passed in, a ``ValueError`` is raised.

The reimplemented ``distlib.version`` module is shorter than the corresponding
module in ``distutils2``, but the entire test suite passes, and there is support
for working with three versioning schemes as opposed to just one. However, the
concept of "final" versions, which is not in the PEP but which was in the
``distutils2`` implementation, has been removed because it appears of little
value (there's no way to determine the "final" status of versions for many of
the project releases registered on PyPI).


Next steps
----------

You might find it helpful to look at the :ref:`reference`.
