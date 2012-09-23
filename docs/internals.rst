.. _internals:

Distlib's design
================

This is the section containing some discussion of how ``distlib``'s design was
arrived at, as and when time permits.

The ``resources`` API
---------------------

This section describes the design of the API relating to accessing 'resources',
which is a convenient label for data files associated with Python packages.

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
can see that a ``Resource`` would have the following properties:

* A ``name`` property identifying the resource.
* A ``stream`` property allowing access to the resource data as a binary 
  stream.
* A ``bytes`` property returning the entire contents of the resource as a byte
  string.
* An ``is_container`` property indicating whether the resource is a container
  of other resources.
* A ``resources`` property returning the names of resources contained within
  the resource.

The ``Resource`` class would be the logical place to perform sanity checks
which relate to all resources. For example:

* It doesn't make sense to ask for the ``stream`` or ``bytes`` properties of a
  container resource.
* It doesn't make sense to ask for the ``resources`` property of a resource
  which is *not* a container.

It seems reasonable to raise exceptions for incorrect property accesses.

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

Since there is no loader for file system packages, the registry will come with
the following mappings:

* ``type(None)`` -> ``ResourceFinder``
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

        def get_stream(self, resource):
            # return the resource's data as a binary stream

        def get_resources(self, resource):
            # return the resources contained in this resource as a set of
            # (relative) resource names

Next steps
----------

You might find it helpful to look at the :ref:`reference`.
