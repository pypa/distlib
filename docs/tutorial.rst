.. _tutorial:

Tutorial
========

This is the place to start your practical exploration of ``distlib``.

Installation
------------

.. note:: Since ``distlib`` has not received its first release yet, you can't
   currently install it from PyPI - the documentation below is a little
   premature. Instead, you need to clone the Mercurial repository at

   https://bitbucket.org/vinay.sajip/distlib/

   or

   http://hg.python.org/distlib/

   followed by doing a ``python setup.py install`` invocation, ideally in a
   virtual environment (venv).

Distlib is a pure-Python library. You should be able to install it using::

   pip install distlib

for installing ``distlib`` into a virtualenv or other directory where you have
write permissions. On Posix platforms, you may need to invoke using ``sudo``
if you need to install ``distlib`` in a protected location such as your system
Python's ``site-packages`` directory.

Testing
-------

A full test suite is included with ``distlib``. To run it, you'll need to clone
the repository or download a tarball and run ``python setup.py test``
in the top-level directory of the package. You can of course also run
``python setup.py install``
to install the package (perhaps invoking with ``sudo`` if you need
to install to a protected location).

Coverage results are available at:

http://www.red-dove.com/distlib/coverage/

These are updated as and when time permits.

Note that the index tests are configured, by default, to use a local test
server, though they can be configured to run against PyPI itself. This local
test server is not bundled with ``distlib``, but is available from:

https://raw.github.com/vsajip/pypiserver/standalone/pypi-server-standalone.py

This is a slightly modified version of Ralf Schmitt's `pypiserver
<https://github.com/schmir/pypiserver>`_. To use, the script needs to be copied
to the ``tests`` folder of the ``distlib`` distribution.

If the server script is not available, the tests which use it will be skipped.

PYPI availability
^^^^^^^^^^^^^^^^^

If PyPI is unavailable or slow, then some of the tests can fail or become
painfully slow. To skip tests that might be sometimes slow, set the
``SKIP_SLOW`` environment variable::

    $ SKIP_SLOW=1 python setup.py test

on Posix, or::

    C:\> set SKIP_SLOW=1
    C:\> python setup.py test

on Windows.


First steps
-----------

For now, we just list how to use particular parts of the API as they take
shape.

Using the database API
^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.database

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
   >>>

Querying a path for distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this most basic form, ``dist_path`` will provide access to all non-legacy
distributions on ``sys.path``. To get these distributions, you invoke the
:meth:`get_distributions` method, which returns an iterable. Let's try it::

   >>> list(dist_path.get_distributions())
   []
   >>>

This may seem surprising if you've just started looking at ``distlib``,
as you won't *have* any non-legacy distributions.

Including legacy distributions in the search results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To include distributions created and installed using ``setuptools`` or
``distribute``, you need to create the ``DistributionPath`` by specifying an
additional keyword argument, like so::

   >>> dist_path = DistributionPath(include_egg=True)
   >>>

and then you'll get a less surprising result::

   >>> len(list(dist_path.get_distributions()))
   77
   >>>

The exact number returned will be different for you, of course. You can ask
for a particular distribution by name, using the :meth:`get_distribution`
method::

   >>> dist_path.get_distribution('setuptools')
   <EggInfoDistribution u'setuptools' 0.6c11 at '/usr/lib/python2.7/dist-packages/setuptools.egg-info'>
   >>>

If you want to look at a specific path other than ``sys.path``, you specify it
as a positional argument to the :class:`DistributionPath` constructor::

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
   ['babar',
    'choxie',
    'towel-stuff',
    'grammar']
   >>>

Distribution properties
~~~~~~~~~~~~~~~~~~~~~~~

Once you have a :class:`Distribution` instance, you can use it to get more
information about the distribution. For example:

* The ``metadata`` attribute gives access to the distribution's metadata
  (see :ref:`use-metadata` for more information).

* The ``name_and_version`` attribute shows the name and version in the format
  ``name (X.Y)``.

* The ``key`` attribute holds the distribution's name in lower-case, as you
  generally want to search for distributions without regard to case
  sensitivity.


.. _dist-exports:

Exporting things from Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each distribution has a dictionary of *exports*. The exports dictionary is
functionally equivalent to "entry points" in ``distribute`` / ``setuptools``.

The keys to the dictionary are just names in a hierarchical namespace
delineated with periods (like Python packages, so we'll refer to them as
*pkgnames* in the following discussion). The keys indicate categories of
information which the distribution's author wishes to export. In each such
category, a distribution may publish one or more entries.

The entries can be used for many purposes, and can point to callable code or
data. A common purpose is for publishing callables in the distribution which
adhere to a particular protocol.

To give a concrete example, the `Babel <http://babel.edgewall.org/>`_ library
for internationalisation support provides a mechanism for extracting, from a
variety of sources, message text to be internationalised. Babel itself provides
functionality to extract messages from e.g. Python and JavaScript source code,
but helpfully offers a mechanism whereby providers of other sources of
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

where ``name``, ``prefix``, and ``suffix`` are ``pkgnames``. ``suffix`` and
``flags`` are optional and ``flags`` follow the description in
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

Distribution dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.locators`` package to locate the dependencies that
a distribution has. The ``distlib.database`` package has code which
allow you to analyse the relationships between a set of distributions:

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

Using the locators API
^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.locators

Overview
~~~~~~~~

To locate a distribution in an index, we can use the :func:`locate` function.
This returns a potentially downloadable distribution (in the sense that it
has a download URL - of course, there are no guarantees that there will
actually be a downloadable resource at that URL). The return value is an
instance of :class:`distlib.database.Distribution` which can be queried for
any distributions it requires, so that they can also be located if desired.
Here is a basic example::

      >>> from distlib.locators import locate
      >>> flask = locate('flask')
      >>> flask
      <Distribution Flask (0.9) [http://pypi.python.org/packages/source/F/Flask/Flask-0.9.tar.gz]>
      >>> dependencies = [locate(r) for r in flask.get_requirements('install')]
      >>> from pprint import pprint
      >>> pprint(dependencies)
      [<Distribution Werkzeug (0.8.3) [http://pypi.python.org/packages/source/W/Werkzeug/Werkzeug-0.8.3.tar.gz]>,
      <Distribution Jinja2 (2.6) [http://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.6.tar.gz]>]
      >>>

The values returned by :meth:`get_requirements` are just strings. Here's another example,
showing a little more detail::

      >>> authy = locate('authy')
      >>> authy.get_requirements('install')
      [u'httplib2 (>= 0.7, < 0.8)', u'simplejson']
      >>> authy
      <Distribution authy (0.0.4) [http://pypi.python.org/packages/source/a/authy/authy-0.0.4.tar.gz]>
      >>> deps = [locate(r) for r in authy.get_requirements('install')]
      >>> pprint(deps)
      [<Distribution httplib2 (0.7.6) [http://pypi.python.org/packages/source/h/httplib2/httplib2-0.7.6.tar.gz]>,
      <Distribution simplejson (2.6.2) [http://pypi.python.org/packages/source/s/simplejson/simplejson-2.6.2.tar.gz]>]
      >>>

Note that the constraints on the dependencies were honoured by :func:`locate`.


Under the hood
~~~~~~~~~~~~~~

Under the hood, :func:`locate` uses *locators*. Locators are a mechanism for
finding distributions from a range of sources. Although the ``pypi`` subpackage
has been copied from ``distutils2`` to ``distlib``, there may be benefits in a
higher-level API, and so the ``distlib.locators`` package has been created as
an experiment. Locators are objects which locate distributions. A locator
instance's :meth:`get_project` method is called, passing in a project name: The
method returns a dictionary containing information about distribution releases
found for that project. The keys of the returned dictionary are versions, and
the values are instances of :class:`distlib.database.Distribution`.

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
  limitation of the underlying XML-RPC API. Note that 20 versions of a
  project necessitate 41 network calls (one to get the versions, and
  two more for each version -- one to get the metadata, and another to get the
  downloads information).

* :class:`PyPIJSONLocator`. -- This takes a base URL for the JSON service and
  will locate packages using PyPI's JSON API. This locator is case-sensitive. For
  example, searching for ``'flask'`` will throw up no results, but you get the
  expected results when searching from ``'Flask'``. This appears to be a
  limitation of the underlying JSON API. Note that unlike the XML-RPC service,
  only non-hidden releases will be returned.

* :class:`SimpleScrapingLocator` -- this takes a base URL for the site to
  scrape, and locates packages using a similar approach to the
  ``PackageFinder`` class in ``pip``, or as documented in the ``setuptools``
  documentation as the approach used by ``easy_install``.

* :class:`DistPathLocator` -- this takes a :class:`DistributionPath` instance
  and locates installed distributions. This can be used with
  :class:`AggregatingLocator` to satisfy requirements from installed
  distributions before looking elsewhere for them.

* :class:`JSONLocator` -- this uses an improved JSON metadata schema and
  returns data on all versions of a distribution, including dependencies,
  using a single network request.

* :class:`AggregatingLocator` -- this takes a list of other aggregators and
  delegates finding projects to them. It can either return the first result
  found (i.e. from the first aggregator in the list provided which returns a
  non-empty result), or a merged result from all the aggregators in the list.

There is a default locator, available at :attr:`distlib.locators.default_locator`.

The ``locators`` package also contains a function,
:func:`get_all_distribution_names`, which retrieves the names of all
distributions registered on PyPI::

      >>> from distlib.locators import get_all_distribution_names
      >>> names = get_all_package_names()
      >>> len(names)
      24801
      >>>

This is implemented using the XML-RPC API.

Apart from :class:`JSONLocator`, none of the locators currently returns enough
metadata to allow dependency resolution to be carried out, but that is a result
of the fact that metadata relating to dependencies are not indexed, and would
require not just downloading the distribution archives and inspection of
contained metadata files, but potentially also introspecting setup.py! This is
the downside of having vital information only available via keyword arguments
to the :func:`setup` call: hopefully, a move to fully declarative metadata will
facilitate indexing it and allowing the provision of improved features.

The locators will skip binary distributions (``.egg`` files are currently
treated as binary distributions).

The PyPI locator classes don't yet support the use of mirrors, but that can be
added in due course -- once the basic functionality is working satisfactorily.

.. _use-index:

Using the index API
^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.index`` package to perform operations relating to a
package index compatible with PyPI. This includes things like registering a
project, uploading a distribution or uploading documentation.

Overview
~~~~~~~~

You access index functionality through an instance of the
:class:`PackageIndex` class. This is instantiated with the URL of the
repository (which can be omitted if you want to use PyPI itself)::

    >>> from distlib.index import PackageIndex
    >>> index = PackageIndex()
    >>> index.url
    'http://pypi.python.org/pypi'

To use a local test server, you might do this::

    >>> index = PackageIndex('http://localhost:8080/')

Registering a project
~~~~~~~~~~~~~~~~~~~~~

Registering a project can be done using a :class:`Metadata` instance which
holds the index metadata used for registering. A simple example::

    >>> from distlib.metadata import Metadata
    >>> metadata = Metadata()
    >>> metadata['Name'] = 'tatterdemalion'
    >>> metadata['Version'] = '0.1'
    >>> # other fields omitted
    >>> response = index.register(metadata)

The :meth:`register` method returns an HTTP response, such as might be returned
by a call to ``urlopen``. If an error occurs, a :class:`HTTPError` will be
raised. Otherwise, the ``response.code`` should be 200.

Uploading a source distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To upload a source distribution, you need to do the following as a minimum::

    >>> metadata = ... # get a populated Metadata instance
    >>> response = index.upload_file(metadata, archive_name)

The :meth:`upload_file` method returns an HTTP response or, in case of error,
raises an :class:`HTTPError`.

Uploading binary distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When uploading binary distributions, you need to specify the file type and
Python version, as in the following example::

    >>> response = index.upload_file(metadata, archive_name,
    ...                              filetype='bdist_dumb',
    ...                              pyversion='2.6')


Signing a distribution
~~~~~~~~~~~~~~~~~~~~~~

To sign a distribution, you will typically need GnuPG. The default
implementation looks for ``gpg`` or ``gpg2`` on the path, but if not available
there, you can can explicitly specify an absbolute path indicating where the
signing program is to be found::

    >>> index.gpg = '/path/to/gpg'

If the location of the signing key is not the default location, you can specify
that too::

    >>> index.gpg_home = '/path/to/keys'

where the ``keys`` folder will hold the GnuPG key database (files like
``pubring.gpg``, ``secring.gpg``, and ``trustdb.gpg``).

Once these are set, you can sign the archive before uploading, as follows::

    >>> response = index.upload_file(metadata, archive_name,
    ...                              signer='Test User',
    ...                              sign_password='secret')

When you sign a distribution, both the distribution and the signature are
uploaded to the index.

Downloading files
~~~~~~~~~~~~~~~~~

The :class:`PackageIndex` class contains a utility method which allows you to
download distributions (and other files, such as signatures)::

    >>> index.download_file(url, destfile, digest=None, reporthook=None)

This is similar in function to :func:`urlretrieve` in the standard library.
Provide a ``digest`` if you want the call to check that the has digest of the
downloaded file matches a specific value: if not provided, no matching is done.
The value passed can just be a plain string in the case of an MD5 digest or, if
you want to specify the hashing algorithm to use, specify a tuple such as
``(sha1, '0123456789abcdef...'). The hashing algorithm must be one that's
supported by the :mod:`hashlib` module.

Benefits to using this method over plain :func:`urlretrieve` are:

* It will use the ``ssl_verifier``, if set, to ensure that the download is
  coming from where you think it is.
* It will compute the digest as it downloads, saving you to have to load the
  downloaded file to compute its digest.

Note that the url you download from doesn't actually need to be on the index --
in theory, it could be from some other site. Note that if you have an
``ssl_verifier`` set on the index, it will perform its checks according to
whichever ``url`` you supply - whether it's a resource on the index or not.


Verifying signatures
~~~~~~~~~~~~~~~~~~~~

For any archive downloaded from an index, you can retrieve any signature by
just appending ``.asc`` to the path portion of the download URL for the
archive, and downloading that. The index class offers a
:meth:`verify_signature` method for validating a signature. Before invoking it,
you may need to specify the location of the signing public key::

    >>> index.gpg_home = '/path/to/keys'

If you have files 'good.bin', 'bad.bin' which are different from each other,
and 'good.bin.asc' has the signature for 'good.bin', then you can verify
signatures like this::

    >>> index.verify_signature('good.bin.asc', 'good.bin')
    True
    >>> index.verify_signature('good.bin.asc', 'bad.bin')
    False

Note that if you don't have the ``gpg`` or ``gpg2`` programs on the path, you
may need to specify the location of the verifier program explicitly::

    >>> index.gpg = '/path/to/gpg'

Some caveats about verified signatures
++++++++++++++++++++++++++++++++++++++

In order to be able to perform signature verification, you'll have to ensure
that the public keys of whoever signed those distributions are in your key
store (where you set ``index.gpg_home`` to point to). However, having these
keys shouldn't give you a false sense of security; unless you can be sure that
those keys actually belong to the people or organisations they purport to
represent, the signature has no real value, even if it is verified without
error. For you to be able to trust a key, it would need to be signed by
someone you trust, who vouches for it - and this requires there to be either
a signature from a valid certifying authority (e.g. Verisign, Thawte etc.) or
a `Web of Trust <http://wikipedia.org/wiki/Web_of_trust>`_ around the keys that
you want to rely on.

An index may itself countersign distributions (so *it* deals with the keys of
the distribution publishers, but you need only deal with the public signing
key belonging to the index). If you trust the index, you can trust the verified
signature if it's signed by the index.


Uploading documentation
~~~~~~~~~~~~~~~~~~~~~~~

To upload documentation, you need to specify the metadata and the directory
which is the root of the documentation (typically, if you use Sphinx to
build your documentation, this will be something like
``<project>/docs/_build/html``)::

    >>> response = index.upload_documentation(metadata, doc_dir)

The :meth:`upload_documentation` method returns an HTTP response or, in case of
error, raises an :class:`HTTPError`. The call will zip up the entire contents
of the passed directory ``doc_dir`` and upload the zip file to the index.

Authentication
~~~~~~~~~~~~~~

Operations which update the index (all of the above) will require
authenticated requests. You can specify a username and password to use for
requests sent to the index::

    >>> index.username = 'test'
    >>> index.password = 'secret'

For your convenience, these will be automatically read from any ``.pypirc``
file which you have; if it contains entries for multiple indexes, a
``repository`` key in ``.pypirc`` must match ``index.url`` to identify which
username and password are to be read from ``.pypirc``. Note that to ensure
compatibility, ``distlib`` uses ``distutils`` code to read the ``.pypirc``
configuration. Thus, given the ``.pypirc`` file::

    [distutils]
    index-servers =
        pypi
        test

    [pypi]
    username: me
    password: my_strong_password

    [test]
    repository: http://localhost:8080/
    username: test
    password: secret

you would see the following::

    >>> index = PackageIndex()
    >>> index.username
    'me'
    >>> index.password
    'my_strong_password'
    >>> index = PackageIndex('http://localhost:8080/')
    >>> index.username
    'test'
    >>> index.password
    'secret'

Verifying HTTPS connections
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although Python has full support for SSL, it does not, by default, verify SSL
connections to servers. That's because in order to do so, a set of certificates
which certify the identity of the server needs to be provided (see `the
relevant Python documentation
<http://docs.python.org/3/library/ssl.html#certificates>`_ for details).

Support for verifying SSL connections is provided in distlib through a handler,
:class:`distlib.util.HTTPSHandler`. To use it, set the ``ssl_verifier``
attribute of the index to a suitably configured instance. For example::

    >>> from distlib.util import HTTPSHandler
    >>> verifier = HTTPSHandler('/path/to/root/certs.pem')
    >>> index.ssl_verifier = verifier

By default, the handler will attempt to match domains, including wildcard
matching. This means that (for example) you access ``foo.org`` or
``www.foo.org`` which have a certificate for ``*.foo.org``, the domains will
match. If the domains don't match, the handler raises a
:class:`CertificateError` (a subclass of :class:`ValueError`).

Domain mismatches can, however, happen for valid reasons. Say a hosting server
``bar.com`` hosts ``www.foo.org``, which we are trying to access using SSL. If
the server holds a certificate for ``www.foo.org``, it will present it to the
client, as long as both support `Server Name Indication (SNI)
<http://wikipedia.org/wiki/Server_Name_Indication>`_. While ``distlib``
supports SNI where Python supports it, Python 2.x does not include SNI support.
For this or some other reason , you may wish to turn domain matching off. To do
so, instantiate the verifier like this::

    >>> verifier = HTTPSHandler('/path/to/root/certs.pem', False)

Ensuring that *only* HTTPS connections are made
+++++++++++++++++++++++++++++++++++++++++++++++

You may want to ensure that traffic is *only* HTTPS for a particular
interaction with a server - for example:

* Deal with a Man-In-The-Middle proxy server which listens on port 443
  but talks HTTP rather than HTTPS
* Deal with situations where an index page obtained via HTTPS contains
  links with a scheme of ``http`` rather than ``https``.

To do this, instead of using :class:`HTTPSHandler` as shown above,
use the :class:`HTTPSOnlyHandler` class instead, which disallows any
HTTP traffic. It's used in the same way as :class:`HTTPSHandler`::

    >>> from distlib.util import HTTPSOnlyHandler
    >>> verifier = HTTPSOnlyHandler('/path/to/root/certs.pem')
    >>> index.ssl_verifier = verifier

Note that with this handler, you can't make *any* HTTP connections at all -
it will raise :class:`URLError` if you try.


Getting hold of root certificates
+++++++++++++++++++++++++++++++++

At the time of writing, you can find a file in the appropriate format on the
`cURL website <http://curl.haxx.se/docs/caextract.html>`_. Just download the
``cacert.pem`` file and pass the path to it when instantiating your verifier.


.. note::
   The main PyPI server, http://pypi.python.org/, currently does not have an
   SSL certificate which is recognised by (for example) mainstream browsers.
   That's because the server is currently certified by CACert.org, whose root
   certificate is not included in the trusted roots pre-installed into these
   browsers. If you want to verify using CACert.org root certificates, you
   will need to get the relevant root certificates and ensure that they are
   included in the file you supply to ``HTTPSHandler``. See `this page
   <http://www.cacert.org/index.php?id=3>`_ for CACert.org root certificates.


Saving a default configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't have a ``.pypirc`` file but want to save one, you can do this by
setting the username and password and calling the :meth:`save_configuration`
method::

    >>> index = PackageIndex()
    >>> index.username = 'fred'
    >>> index.password = 'flintstone'
    >>> index.save_configuration()

This will use ``distutils`` code to save a default ``.pypirc`` file which
specifies a single index - PyPI - with the specified username and password.


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

.. currentmodule:: distlib.scripts

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

To install scripts, create a :class:`ScriptMaker` instance,
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

  Note that this format is exactly the same as for export entries in a
  distribution (see :ref:`dist-exports`).

  When this form is passed to the :meth:`ScriptMaker.make`
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
        import sys, re

        def _resolve(module, func):
            __import__(module)
            mod = sys.modules[module]
            parts = func.split('.')
            result = getattr(mod, parts.pop(0))
            for p in parts:
                result = getattr(result, p)
            return result

        try:
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

Using the version API
^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.version

Overview
~~~~~~~~

The :class:`NormalizedVersion` class implements a :pep:`386` compatible
version::

      >>> from distlib.version import NormalizedVersion
      >>> v1 = NormalizedVersion('1.0')
      >>> v2 = NormalizedVersion('1.0a1')
      >>> v3 = NormalizedVersion('1.0b1')
      >>> v4 = NormalizedVersion('1.0c1')
      >>> v5 = NormalizedVersion('1.0.post1')
      >>>

These sort in the expected order::

      >>> v2 < v3 < v4 < v1 < v5
      True
      >>>

You can't pass any old thing as a version number::

      >>> NormalizedVersion('foo')
      Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "distlib/version.py", line 49, in __init__
       self._parts = parts = self.parse(s)
      File "distlib/version.py", line 254, in parse
       def parse(self, s): return normalized_key(s)
      File "distlib/version.py", line 199, in normalized_key
       raise UnsupportedVersionError(s)
      distlib.version.UnsupportedVersionError: foo
      >>>

Matching versions against constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`NormalizedMatcher` is used to match version constraints against
versions::

      >>> from distlib.version import NormalizedMatcher
      >>> m = NormalizedMatcher('foo (1.0b1)')
      >>> m
      NormalizedMatcher('foo (1.0b1)')
      >>> [m.match(v) for v in v1, v2, v3, v4, v5]
      [False, False, True, False, False]
      >>>

Specifying ``'foo (1.0b1)'`` is equivalent to specifying ``'foo (==1.0b1)'``,
i.e. only the exact version is matched. You can also specify inequality
constraints::

      >>> m = NormalizedMatcher('foo (<1.0c1)')
      >>> [m.match(v) for v in v1, v2, v3, v4, v5]
      [False, True, True, False, False]
      >>>

and multiple constraints::

      >>> m = NormalizedMatcher('foo (>= 1.0b1, <1.0.post1)')
      >>> [m.match(v) for v in v1, v2, v3, v4, v5]
      [True, False, True, True, False]
      >>>

You can do exactly the same thing as above with ``setuptools``/
``distribute`` version numbering (use ``LegacyVersion`` and ``LegacyMatcher``)
or with semantic versioning (use ``SemanticVersion`` and ``SemanticMatcher``).
However, you can't mix and match versions of different types::

      >>> from distlib.version import SemanticVersion, LegacyVersion
      >>> nv = NormalizedVersion('1.0.0')
      >>> lv = LegacyVersion('1.0.0')
      >>> sv = SemanticVersion('1.0.0')
      >>> lv == sv
      Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "distlib/version.py", line 61, in __eq__
       self._check_compatible(other)
      File "distlib/version.py", line 58, in _check_compatible
      raise TypeError('cannot compare %r and %r' % (self, other))
      TypeError: cannot compare LegacyVersion('1.0.0') and SemanticVersion('1.0.0')
      >>> nv == sv
      Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "distlib/version.py", line 61, in __eq__
       self._check_compatible(other)
      File "distlib/version.py", line 58, in _check_compatible
      raise TypeError('cannot compare %r and %r' % (self, other))
      TypeError: cannot compare NormalizedVersion('1.0.0') and SemanticVersion('1.0.0')
      >>>


Next steps
----------

You might find it helpful to look at information about
:ref:`internals` -- or peruse the :ref:`reference`.
