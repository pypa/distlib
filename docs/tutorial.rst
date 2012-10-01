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

* :class:`DistributionSet`, which represents a set of distributions installed
  on a path.

* :class:`Distribution`, which represents an individual distribution,
  conforming to recent packaging PEPs (:pep:`386`, :pep:`376`, :pep:`345`,
  :pep:`314` and :pep:`241`).
* :class:`EggInfoDistribution`, which represents a legacy distribution in
  egg format.

The :class:`Distribution` and :class:`EggInfoDistribution` classes are normally
not instantiated directly; rather, they are returned by querying
:class:`DistributionSet` for distributions. To create a ``DistributionSet``
instance, you can do ::

    >>> from distlib.database import DistributionSet
    >>> distset = DistributionSet()

In this most basic form, ``distset`` will provide access to all non-legacy
distributions on ``sys.path``. To get these distributions, you invoke the
:meth:`get_distributions` method, which returns an iterable. Let's try it::

    >>> list(distset.get_distributions())
    []
    >>>

This may seem surprising, but that's only because, if you've just started
looking at ``distlib``, you won't *have* any non-legacy distributions. To include
distributions created and installed using ``setuptools`` or ``distribute``, you
need to create the ``DistributionSet`` by specifying an additional keyword
argument, like so::

    >>> distset = DistributionSet(include_egg=True)

and then you'll get a less surprising result::

    >>> len(list(distset.get_distributions()))
    77

The exact number returned will be different for you, of course. You can ask
for a particular distribution by name, using the :meth:`get_distribution`
method::

    >>> distset.get_distribution('setuptools')
    <EggInfoDistribution u'setuptools' 0.6c11 at '/usr/lib/python2.7/dist-packages/setuptools.egg-info'>
    >>>

If you want to look at a specific path other than ``sys.path``, you specify it as a
positional argument to the :class:`DistributionSet` constructor::

    >>> from pprint import pprint
    >>> special_dists = DistributionSet(['tests/fake_dists'], include_egg=True)
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

    >>> special_dists = DistributionSet(['tests/fake_dists'])
    >>> pprint([d.name for d in special_dists.get_distributions()])
    ['babar', 'choxie', 'towel-stuff', 'grammar']
    >>>

Once you have a :class:`Distribution` instance, you can use it to get more
information about the distribution. For example, the ``metadata`` attribute
gives access to the distribution's metadata.

Using the dependency API
^^^^^^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.depgraph`` package to analyse the dependencies
between various distributions and to create a graph representing these
dependency relationships.

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

This works the same if the package is in a .zip file. Given the zip file
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

* On Windows, on systems where the PEP 397 launcher isn't installed, it is not
  easy to ensure that the correct Python interpreter is used for a script. You
  may wish to install native Windows executable launchers which run the correct
  interpreter, based on a shebang line in the script.

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

  When this form is passed to the :meth:`~distlib.script.ScriptMaker.make`
  method, a Python stub script is created with the appropriate shebang line
  and with code to load and call the specified callable with no arguments,
  returning its value as the return code from the script.

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

Next steps
----------

You might find it helpful to look at information about
:ref:`internals` -- or peruse the :ref:`reference`.
