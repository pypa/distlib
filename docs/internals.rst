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
* Resources can only be associated with packages, not with modules. That's
  because with peer modules ``a.py`` and ``b.py``, there's no obvious location
  for data associated only with ``a``: both ``a`` and ``b`` are in the same
  directory. With a package, there's no ambiguity, as a package is associated
  with a directory.
* Support should be provided for access to data deployed in the file system or
  in packages contained in .zip files, and third parties should be able to
  extend the facilities to work with other storage formats which support import
  of Python packages.


A minimal solution
^^^^^^^^^^^^^^^^^^

The ``Resource`` class
^^^^^^^^^^^^^^^^^^^^^^

The ``FileResourceFinder`` class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``ZipResourceFinder`` class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



Next steps
----------

You might find it helpful to look at the :ref:`reference`.
