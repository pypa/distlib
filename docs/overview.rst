Overview
========

Start here for all things ``distlib``.

Distlib evolved out of ``packaging``
------------------------------------

Distlib is a library which implements low-level functions that relate to
packaging and distribution of Python software. It consists in part of
the functions in the ``packaging`` Python package, which was intended to be
released as part of Python 3.3, but was removed shortly before Python
3.3 entered beta testing.

.. note:: The ``packaging`` package referred to here does not refer to any
  ``packaging`` package currently available on PyPI, but to a package that was never
  released on PyPI but called ``packaging`` in the Python 3.3 alpha stdlib tree.

What was the problem with ``packaging``?
----------------------------------------

The ``packaging`` software just wasn't ready for inclusion in the Python
standard library. The amount of work needed to get it into the desired
state was too great, given the number of people able to work on the project,
the time they could devote to it, and the Python 3.3 release schedule.

The approach taken by ``packaging`` was seen to be a good one: to ensure
interoperability and consistency between different tools in the packaging
space by defining standards for data formats through PEPs, and to do away
with the *ad hoc* nature of installation encouraged by the ``distutils``
approach of using executable Python code in ``setup.py``. Where custom
code was needed, it could be provided in a standardised way using
installation hooks.

While some very good work was done in defining PEPs to codify some of the
best practices, ``packaging`` suffered from some drawbacks, too:

* Not all the PEPs may have been functionally complete, because some important
  use cases were not considered -- for example, built (binary) distributions for
  Windows.

* It continued the command-based design of ``distutils``, which had resulted
  in ``distutils`` being difficult to extend in a consistent, easily
  understood, and maintainable fashion.

* Some important features required by distribution authors were not considered
  -- for example:

  * Access to data files stored in Python packages.
  * Support for plug-in extension points.
  * Support for native script execution on Windows.

  These features are supported by third-party tools (like ``setuptools`` /
  ``Distribute``) using ``pkg_resources``, *entry points* and *console
  scripts*.

* There were a lot of rough edges in the ``packaging`` implementation, both
  in terms of bugs and in terms of incompletely implemented features. This
  can be seen (with the benefit of hindsight) as due to the goals being set too
  ambitiously; the project developers bit off more than they could chew.

How Distlib can help
--------------------

The idea behind Distlib is expressed in `this python-dev mailing-list post
<http://mail.python.org/pipermail/python-dev/2012-September/121716.html>`_,
though a different name was suggested for the library. Basically, Distlib
contains the implementations of the packaging PEPs and other low-level
features which relate to packaging, distribution, and deployment of Python
software. If Distlib can be made genuinely useful, then it is possible for
third-party packaging tools to transition to using it. Their developers and
users then benefit from standardised implementation of low-level functions,
time saved by not having to reinvent wheels, and improved interoperability
between tools.

How you can help
----------------

If you have some time and the inclination to improve the state of Python
packaging, then you can help by trying out Distlib, raising issues where
you find problems, contributing feedback and/or patches to the
implementation, documentation, and underlying PEPs.

Main features
-------------

Distlib currently offers the following features:

* The package ``distlib.database``, which implements a database of installed
  distributions, as defined by :pep:`376`, and distribution dependency graph
  logic. Support is also provided for non-installed distributions (i.e.
  distributions registered with metadata on an index like PyPI), including
  the ability to scan for dependencies and building dependency graphs.
* The package ``distlib.index``, which implements an interface to perform
  operations on an index, such as registering a project, uploading a
  distribution or uploading documentation. Support is included for verifying
  SSL connections (with domain matching) and signing/verifying packages using
  GnuPG.

  .. note:: Since this API was developed, a number of features of PyPI have been
     turned off for various reasons - for example, documentation uploads, XMLRPC
     search API - and a number of APIs have changed (e.g. PyPI no longer shows GnuPG
     signatures). For now, the ``distlib.index`` API should be considered not fully
     reliable, mostly due to changes in PyPI where there has not been enough time to
     catch up with them.

* The package ``distlib.metadata``, which implements distribution metadata as
  defined by :pep:`643`, :pep:`566`, :pep:`345`, :pep:`314` and :pep:`241`.

  .. note:: In the past ``distlib`` has tracked metadata proposals in PEPs even when
     they were draft, but this has proven to be too time-consuming. The current policy
     is not to track standards proactively while they're still being thrashed out, but
     to look instead at starting to implement them once they're marked ``Final``.

* The package ``distlib.markers``, which implements environment markers as
  defined by :pep:`508`.
* The package ``distlib.manifest``, which implements lists of files used
  in packaging source distributions.
* The package ``distlib.locators``, which allows finding distributions, whether
  on PyPI (XML-RPC or via the "simple" interface), local directories or some
  other source.
* The package ``distlib.resources``, which allows access to data files stored
  in Python packages, both in the file system and in .zip files.
* The package ``distlib.scripts``, which allows installing of scripts with
  adjustment of shebang lines and support for native Windows executable
  launchers.
* The package ``distlib.version``, which implements version specifiers as
  defined by :pep:`440`, but also support for working with "legacy" versions
  (``setuptools``/``distribute``) and semantic versions.
* The package ``distlib.wheel``, which provides support for building and
  installing from the Wheel format for binary distributions (see :pep:`427`).
* The package ``distlib.util``, which contains miscellaneous functions and
  classes which are useful in packaging, but which do not fit neatly into
  one of the other packages in ``distlib``.* The package implements enhanced
  globbing functionality such as the ability to use ``**`` in patterns to
  specify recursing into subdirectories.


Python version and platform compatibility
-----------------------------------------

Distlib is intended to be used on any Python version >= 2.7 and is tested on
Python versions 2.7 and 3.6-3.10 on Linux, Windows, and macOS.

Project status
--------------

The project has reached a mature status in its development: there is a test suite and
it has been exercised on Windows, Ubuntu and macOS. The project is used by well-known
projects such as `pip <https://pypi.org/pypi/pip>`_, `virtualenv
<https://github.com/pypa/virtualenv>`_ and `caniusepython3
<https://pypi.org/pypi/caniusepython3>`_.


To work with the project, you can `download a release from PyPI
<https://pypi.org/pypi/distlib/>`_, or clone the source repository or
download a tarball from it.

The source repository for the project is on GitHub:

https://github.com/pypa/distlib/

Coverage results are available at:

https://app.codecov.io/gh/pypa/distlib/

Continuous integration test results are available at:

https://github.com/pypa/distlib/actions/

You can leave feedback by raising a new issue on the `issue
tracker <https://github.com/pypa/distlib/issues/new/choose>`_.

.. include:: ../CHANGES.rst


Next steps
----------

You might find it helpful to look at the :ref:`tutorial`, or the
:ref:`reference`.
