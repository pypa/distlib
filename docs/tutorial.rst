.. _tutorial:

Tutorial
========

This is the place to start your practical exploration of ``distlib``.

Installation and testing
------------------------

Distlib is a pure-Python library. You should be able to install it using::

    pip install distlib

for installing ``distlib`` into a virtualenv or other directory where you have
write permissions. On Posix platforms, you may need to invoke using ``sudo``
if you need to install ``distlib`` in a protected location such as your system
Python's ``site-packages`` directory.

A full test suite is included with ``distlib``. To run it, you'll need to
unpack a source tarball and run ``python setup.py test`` in the top-level
directory of the unpack location. You can of course also run
``python setup.py install``
to install from the source tarball (perhaps invoking with ``sudo`` if you need
to install to a protected location).

First steps
-----------

For now, we just list how to use particular parts of the API as they take
shape.

Using the database API
^^^^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.database`` package to access information about
installed distributions. This information is available through the
following classes:

* :class:`DistributionPath`, which represents a set of distributions installed
  on a path.

* :class:`Distribution`, which represents an individual distribution,
  conforming to recent packaging PEPs (:pep:`386`, :pep:`376`, :pep:`345`,
  :pep:`314` and :pep:`241`).
* :class:`EggInfoDistribution`, which represents a legacy distribution in
  egg format.

Distribution paths
~~~~~~~~~~~~~~~~~~

The :class:`Distribution` and :class:`EggInfoDistribution` classes are normally
not instantiated directly; rather, they are returned by querying
:class:`DistributionPath` for distributions. To create a ``DistributionPath``
instance, you can do ::

    >>> from distlib.database import DistributionPath
    >>> dist_path = DistributionPath()

Querying a path for distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this most basic form, ``dist_path`` will provide access to all non-legacy
distributions on ``sys.path``. To get these distributions, you invoke the
:meth:`get_distributions` method, which returns an iterable. Let's try it::

    >>> list(dist_path.get_distributions())
    []
    >>>

This may seem surprising, but that's only because, if you've just started
looking at ``distlib``, you won't *have* any non-legacy distributions.

Including legacy distributions in the search results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To include distributions created and installed using ``setuptools`` or
``distribute``, you need to create the ``DistributionPath`` by specifying an
additional keyword argument, like so::

    >>> dist_path = DistributionPath(include_egg=True)

and then you'll get a less surprising result::

    >>> len(list(dist_path.get_distributions()))
    77

The exact number returned will be different for you, of course. You can ask
for a particular distribution by name, using the :meth:`get_distribution`
method::

    >>> dist_path.get_distribution('setuptools')
    <EggInfoDistribution u'setuptools' 0.6c11 at '/usr/lib/python2.7/dist-packages/setuptools.egg-info'>
    >>>

If you want to look at a specific path other than ``sys.path``, you specify it as a
positional argument to the :class:`DistributionPath` constructor::

    >>> from pprint import pprint
    >>> special_dists = DistributionPath(['tests/fake_dists'], include_egg=True)
    >>> pprint([d.name for d in special_dists.get_distributions()])
    ['babar',
     'choxie',
     'towel-stuff',
     'grammar',
     'truffles',
     'coconuts-aster',
     'nut',
     'bacon',
     'banana',
     'cheese',
     'strawberry']
    >>>

or, if you leave out egg-based distributions::

    >>> special_dists = DistributionPath(['tests/fake_dists'])
    >>> pprint([d.name for d in special_dists.get_distributions()])
    ['babar', 'choxie', 'towel-stuff', 'grammar']
    >>>

Distribution properties
~~~~~~~~~~~~~~~~~~~~~~~

Once you have a :class:`Distribution` instance, you can use it to get more
information about the distribution. For example, the ``metadata`` attribute
gives access to the distribution's metadata (see :ref:`use-metadata` for more
information).

.. _dist-registry:

The distribution registry
~~~~~~~~~~~~~~~~~~~~~~~~~

Each distribution has a *registry*. The registry is functionally equivalent to
"entry points" in ``distribute`` / ``setuptools``.

The keys to the registry are just names in a hierarchical namespace delineated
with periods (like Python packages, so we'll refer to them as *pkgnames* in the
following discussion). The keys indicate categories of information which the
distribution's author wishes to publish. In each such category, a distribution
may publish one or more entries.

The entries can be used for many purposes, and can point to callable code or
data. A common purpose is for publishing callables in the distribution which
adhere to a particular protocol.

To give a concrete example, the `Babel <http://babel.edgewall.org/>`_ library
for internationalisation support provides a mechanism for extracting, from a
variety of sources, message text to be internationalised. Babel itself provides
functionality to extract messages from e.g. Python and JavaScript source code,
but helpfully provides a mechanism whereby providers of other sources of
message text can provide their own extractors. It does this by providing a
category ``'babel.extractors'``, under which other software can register
extractors for their sources. The `Jinja2 <http://jinja2.pocoo.org/>`_ template
engine, for example, makes use of this to provide a message extractor for
Jinja2 templates. Babel itself registers its own extractors under the same
category, so that a unified view of all extractors in a given Python
environment can be obtained, and Babel's extractors are treated by other parts
of Babel in exactly the same way as extractors from third parties.

Any installed distribution can offer up values for any category, and a set of
distributions (such as the set of installed distributions on ``sys.path``)
conceptually has an aggregation of these values.

The values associated with a category are a list of strings with the format::

    name = prefix [ ":" suffix ] [ "[" flags "]" ]

where ``name``, ``prefix`` and ``suffix`` are ``pkgnames``, ``suffix`` and
``flags`` are optional, and ``flags`` follow the description in
:ref:`flag-formats`.

Any installed distribution can offer up values for any category, and
a set of distributions (such as the set of installed distributions on
``sys.path``) conceptually has an aggregation of these values.

For callables, the ``prefix`` is the package or module name which contains the
callable, ``suffix`` is the path to the callable in the module, and flags can
be used for any purpose determined by the distribution author (for example, the
``extras`` feature in ``distribute`` / ``setuptools``).

This entry format is used in the :mod:`distlib.scripts` package for installing
scripts based on Python callables.


Using the dependency API
^^^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.depgraph

You can use the ``distlib.depgraph`` package to analyse the dependencies
between various distributions and to create a graph representing these
dependency relationships. The main interface is through the following
functions:

* :func:`make_graph`, which generates a dependency graph from a list of
  distributions.

* :func:`get_dependent_dists`, which takes a list of distributions and a
  specific distribution in that list, and returns the distributions that
  are dependent on that specific distribution.

* :func:`get_required_dists`, which takes a list of distributions and a
  specific distribution in that list, and returns the distributions that
  are required by that specific distribution.

The graph returned by :func:`make_graph` is an instance of
:class:`DependencyGraph`.

.. _use-metadata:

Using the metadata API
^^^^^^^^^^^^^^^^^^^^^^

TBD

Using the resource API
^^^^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.resources`` package to access data stored in Python
packages, whether in the file system or .zip files. Consider a package
which contains data alongside Python code::

    foofoo
    ├── bar
    │   ├── bar_resource.bin
    │   ├── baz.py
    │   └── __init__.py
    ├── foo_resource.bin
    ├── __init__.py
    └── nested
        └── nested_resource.bin

Access to resources in the file system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can access these resources like so::

    >>> from distlib.resources import finder
    >>> f = finder('foofoo')
    >>> r = f.find('foo_resource.bin')
    >>> r.is_container
    False
    >>> r.size
    10
    >>> r.bytes
    b'more_data\n'
    >>> s = r.as_stream()
    >>> s.read()
    b'more_data\n'
    >>> s.close()
    >>> r = f.find('nested')
    >>> r.is_container
    True
    >>> r.resources
    {'nested_resource.bin'}
    >>> r = f.find('nested/nested_resource.bin')
    >>> r.size
    12
    >>> r.bytes
    b'nested data\n'
    >>> f = finder('foofoo.bar')
    >>> r = f.find('bar_resource.bin')
    >>> r.is_container
    False
    >>> r.bytes
    b'data\n'
    >>>

Access to resources in the ``.zip`` files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It works the same way if the package is in a .zip file. Given the zip file
``foo.zip``::

    $ unzip -l foo.zip
    Archive:  foo.zip
      Length      Date    Time    Name
    ---------  ---------- -----   ----
           10  2012-09-20 21:34   foo/foo_resource.bin
            8  2012-09-20 21:42   foo/__init__.py
           14  2012-09-20 21:42   foo/bar/baz.py
            8  2012-09-20 21:42   foo/bar/__init__.py
            5  2012-09-20 21:33   foo/bar/bar_resource.bin
    ---------                     -------
           45                     5 files

You can access its resources as follows::

    >>> import sys
    >>> sys.path.append('foo.zip')
    >>> from distlib.resources import finder
    >>> f = finder('foo')
    >>> r = f.find('foo_resource.bin')
    >>> r.is_container
    False
    >>> r.size
    10
    >>> r.bytes
    'more_data\n'
    >>>

and so on.

Using the scripts API
^^^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.scripts`` API to install scripts. Installing scripts
is slightly more involved than just copying files:

* You may need to adjust shebang lines in scripts to point to the interpreter
  to be used to run scripts. This is important in virtual environments (venvs),
  and also in other situations where you may have multiple Python installations
  on a single computer.

* On Windows, on systems where the :pep:`397` launcher isn't installed, it is not
  easy to ensure that the correct Python interpreter is used for a script. You
  may wish to install native Windows executable launchers which run the correct
  interpreter, based on a shebang line in the script.

Specifying scripts to install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install scripts, create a :class:`~distlib.scripts.ScriptMaker` instance,
giving it
the source and target directories for scripts::

    >>> from distlib.scripts import ScriptMaker
    >>> maker = ScriptMaker(source_dir, target_dir)

You can then install a script ``foo.py`` like this:

    >>> maker.make('foo.py')

The string passed to make can take one of the following forms:

* A filename, relative to the source directory for scripts, such as ``foo.py``
  or ``subdir/bar.py``.
* A reference to a callable, given in the form::

      name = some_package.some_module:some_callable [flags]

  where the *flags* part is optional. The only flag currently in use is
  ``'gui'``, which indicates on Windows that a Windows executable launcher
  (rather than a launcher which is a console application) should be used.
  (This only applies if ``add_launchers`` is true.)

  For more information about flags, see :ref:`flag-formats`.

  Note that this format is exactly the same as for registry entries in a
  distribution (see :ref:`dist-registry`).

  When this form is passed to the :meth:`~distlib.script.ScriptMaker.make`
  method, a Python stub script is created with the appropriate shebang line
  and with code to load and call the specified callable with no arguments,
  returning its value as the return code from the script.

Wrapping callables with scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's see how wrapping a callable works. Consider the following file::

    $ cat scripts/foo.py
    def main():
        print('Hello from foo')

    def other_main():
        print('Hello again from foo')

we can try wrapping ``main`` and ``other_main`` as callables::

    >>> from distlib.scripts import ScriptMaker
    >>> maker = ScriptMaker('scripts', '/tmp/scratch')
    >>> maker.make_multiple(('foo = foo:main', 'bar = foo:other_main'))
    ['/tmp/scratch/foo', '/tmp/scratch/bar']
    >>>

we can inspect the resulting scripts. First, ``foo``::

    $ ls /tmp/scratch/
    bar  foo
    $ cat /tmp/scratch/foo
    #!/usr/bin/python

    if __name__ == '__main__':
        def _resolve(module, func):
            mod = __import__(module)
            parts = func.split('.')
            result = getattr(mod, parts.pop(0))
            for p in parts:
                result = getattr(result, p)
            return result

        try:
            import sys, re
            sys.argv[0] = re.sub('-script.pyw?$', '', sys.argv[0])

            func = _resolve('foo', 'main')
            rc = func() # None interpreted as 0
        except Exception as e:  # only supporting Python >= 2.6
            sys.stderr.write('%s\n' % e)
            rc = 1
        sys.exit(rc)

The other script, ``bar``, is different only in the essentials::

    $ diff /tmp/scratch/foo /tmp/scratch/bar
    16c16
    <         func = _resolve('foo', 'main')
    ---
    >         func = _resolve('foo', 'other_main')

Using the locators API
^^^^^^^^^^^^^^^^^^^^^^

Locators are a mechanism for finding distributions from a range of sources.
Although the ``pypi`` subpackage has been copied from ``distutils2`` to
``distlib``, there may be benefits in a higher-level API, and so the
``distlib.locators`` package has been created as an experiment. This implements
*locators* -- objects which locate distributions. A locator instance's
:meth:`get_project` method is called, passing in a project name: The method
returns a dictionary containing information about distributions found for that
project. The keys of the returned dictionary are versions, and the values are
instances of :class:`distlib.util.Distribution`.

The following locators are provided:

* :class:`DirectoryLocator` -- this is instantiated with a base directory and
  will look for archives in the file system tree under that directory. Name
  and version information is inferred from the filenames of archives, and the
  amount of information returned about the download is minimal.

* :class:`PyPIRPCLocator`. -- This takes a base URL for the RPC service and
  will locate packages using PyPI's XML-RPC API. This locator is a little slow
  (the scraping interface seems to work faster) and case-sensitive. For
  example, searching for ``'flask'`` will throw up no results, but you get the
  expected results when searching from ``'Flask'``. This appears to be a
  limitation of the underlying XML-RPC API. For example, 20 versions of a
  project necessitate 41 network calls (one to get the versions, and
  two more for each version -- one to get the metadata, and another to get the
  downloads information).

* :class:`SimpleScrapingLocator` -- this takes a base URL for the site to
  scrape, and locates packages using a similar approach to the
  ``PackageFinder`` class in ``pip``, or as documented in the ``setuptools``
  documentation as the approach used by ``easy_install``.

An example of usage is given below::

    >>> from distlib.locators import SimpleScrapingLocator
    >>> from pprint import pprint
    >>> locator = SimpleScrapingLocator('http://pypi.python.org/simple/')
    >>> result = locator.get_project('python-gnupg')
    >>> pprint(result)
    {u'0.2.3': <Distribution python-gnupg (0.2.3) [http://python-gnupg.googlecode.com/files/python-gnupg-0.2.3.tar.gz]>,
     u'0.2.4': <Distribution python-gnupg (0.2.4) [http://python-gnupg.googlecode.com/files/python-gnupg-0.2.4.tar.gz]>,
     u'0.2.9': <Distribution python-gnupg (0.2.9) [http://python-gnupg.googlecode.com/files/python-gnupg-0.2.9.tar.gz]>,
     u'0.3.0': <Distribution python-gnupg (0.3.0) [http://python-gnupg.googlecode.com/files/python-gnupg-0.3.0.tar.gz]>,
     u'0.3.1': <Distribution python-gnupg (0.3.1) [http://python-gnupg.googlecode.com/files/python-gnupg-0.3.1.tar.gz]>}
    >>>

Now the same project, using the XML-RPC API::

    >>> from distlib.locators import PyPIRPCLocator
    >>> locator = PyPIRPCLocator('http://python.org/pypi')
    >>> result = locator.get_project('python-gnupg')
    >>> pprint(result)
    {'0.2.3': <Distribution python-gnupg (0.2.3) [http://python-gnupg.googlecode.com/files/python-gnupg-0.2.3.tar.gz]>,
     '0.2.4': <Distribution python-gnupg (0.2.4) [http://python-gnupg.googlecode.com/files/python-gnupg-0.2.4.tar.gz]>,
     '0.2.6': <Distribution python-gnupg (0.2.6) [UNKNOWN]>,
     '0.2.7': <Distribution python-gnupg (0.2.7) [UNKNOWN]>,
     '0.2.8': <Distribution python-gnupg (0.2.8) [UNKNOWN]>,
     '0.2.9': <Distribution python-gnupg (0.2.9) [http://python-gnupg.googlecode.com/files/python-gnupg-0.2.9.tar.gz]>,
     '0.3.0': <Distribution python-gnupg (0.3.0) [http://python-gnupg.googlecode.com/files/python-gnupg-0.3.0.tar.gz]>,
     '0.3.1': <Distribution python-gnupg (0.3.1) [http://python-gnupg.googlecode.com/files/python-gnupg-0.3.1.tar.gz]>}
    >>>

The reason why some of the download URLs come up as UNKNOWN is that some of
the PyPI metadata is incomplete.

The Locator API is very bare-bones at the moment, but additional features will
be added in due course. A very bare-bones command-line script which exercises
these locators is to be found `here <https://gist.github.com/3886402>`_, and
feedback will be gratefully received from anyone who tries it out.

None of the locators currently returns enough metadata to allow dependency
resolution to be carried out, but that is a function of the fact that metadata
relating to dependencies is not indexed, and would require not just downloading
the distribution archives and inspection of contained metadata files, but
potentially also introspecting setup.py! This is the downside of having vital
information only available via keyword arguments to the :func:`setup` call:
hopefully, a move to fully declarative metadata will facilitate indexing it and
allowing the provision of features currently provided by ``setuptools`` (e.g.
hints for downloads -- ``'dependency _links'``).

The accessors skip binary distributions (``.egg`` files are currently treated
as binary distributions).

The PyPI accessor classes don't yet support the use of mirrors, but that can be
added in due course -- once the basic functionality is working satisfactorily.

Next steps
----------

You might find it helpful to look at information about
:ref:`internals` -- or peruse the :ref:`reference`.
