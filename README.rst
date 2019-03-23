.. image:: https://travis-ci.org/vsajip/distlib.svg
   :target: https://travis-ci.org/vsajip/distlib

.. image:: https://coveralls.io/repos/vsajip/distlib/badge.svg
   :target: https://coveralls.io/github/vsajip/distlib


What is it?
-----------

Distlib is a library which implements low-level functions that relate to
packaging and distribution of Python software. It is intended to be used as the
basis for third-party packaging tools. The documentation is available at

https://distlib.readthedocs.io/

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
* The package ``distlib.metadata``, which implements distribution metadata as
  defined by :pep:`426`, :pep:`345`, :pep:`314` and :pep:`241`.
* The package ``distlib.markers``, which implements environment markers as
  defined by :pep:`426`.
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
  defined by :pep:`440` / :pep:`426`, but also support for working with
  "legacy" versions (``setuptools``/``distribute``) and semantic versions.
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
Python versions 2.7 and 3.3-3.6 on Linux, Windows, and Mac OS X (not
all versions are tested on all platforms, but are expected to work correctly).

Project status
--------------

The project has reached a mature status in its development: there is a test
suite and it has been exercised on Windows, Ubuntu and Mac OS X. The project is
used by well-known projects such as `pip <https://pypi.org/pypi/pip>`_ and
`caniusepython3 <https://pypi.org/pypi/caniusepython3>`_.

Code of Conduct
---------------

Everyone interacting in the distlib project's codebases, issue trackers, chat
rooms, and mailing lists is expected to follow the `PyPA Code of Conduct`_.

.. _PyPA Code of Conduct: https://www.pypa.io/en/latest/code-of-conduct/
