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

This works the same if the package is in a .zip file. Given the zip file::

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

      name = some_package.some_module:some_callable flags

  or::

      name = some_package.some_module.some_callable flags

  where the *flags* part is optional, but is a set of words separated by
  spaces. The only flag currently in use is ``'gui'``, which indicates on
  Windows that a Windows executable launcher (rather than a launcher which
  is a console application) should be used. (This only applies if
  ``add_launchers`` is true.)

  When this form is passed to the :meth:`~distlib.script.ScriptMaker.make`
  method, a Python stub script is created with the appropriate shebang line
  and with code to load and call the specified callable with no arguments,
  returning its value as the return code from the script.

Next steps
----------

You might find it helpful to look at information about 
:ref:`internals` -- or peruse the :ref:`reference`.
