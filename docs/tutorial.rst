.. _tutorial:

Tutorial
========

.. index::
   single: Tutorial


Installation
------------

.. index::
   single: Installation; distlib

Distlib is a pure-Python library. You should be able to install it using::

   pip install distlib

for installing ``distlib`` into a virtualenv or other directory where you have
write permissions. On POSIX platforms, you may need to invoke using ``sudo``
if you need to install ``distlib`` in a protected location such as your system
Python's ``site-packages`` directory.

Testing
-------

.. index::
   single: Testing; distlib

A full test suite is included with ``distlib``. To run it, you'll need to
download the source distribution, unpack it and run ``python tests/test_all.py``
in the top-level directory of the package.

If running the tests under Python >= 3.2.3, remember to first set the environment
variable ``PYTHONHASHSEED=0`` to disable hash randomisation, which is needed for
the tests. (The environment variable also needs to be set if running Python 2.x
with ``-R``. which is only available in Python 2.6.8 and later.)

.. index::
   single: Continuous integration status; distlib

Continuous integration test results are available at:

https://github.com/pypa/distlib/actions

Coverage results are available at:

.. index::
   single: Coverage status; distlib

https://app.codecov.io/gh/pypa/distlib

Note that the actual coverage is higher than that shown, because coverage
under Windows is not included in the above coverage figures.

Note that the index tests are configured, by default, to use a local test
server, though they can be configured to run against PyPI itself. This local
test server is not bundled with ``distlib``, but is available from:

https://raw.github.com/vsajip/pypiserver/standalone/pypi-server-standalone.py

This is a slightly modified version of Ralf Schmitt's `pypiserver
<https://github.com/schmir/pypiserver>`_. To use, the script needs to be copied
to the ``tests`` folder of the ``distlib`` distribution.

If the server script is not available, the tests which use it will be skipped.
Naturally, this will also affect the coverage statistics.

PYPI availability
^^^^^^^^^^^^^^^^^

.. index::
   single: Tests; speeding up

If PyPI is unavailable or slow, then some of the tests can fail or become
painfully slow. To skip tests that might be sometimes slow, set the
``SKIP_SLOW`` environment variable::

    $ SKIP_SLOW=1 PYTHONHASHSEED=0 python tests/test_all.py

on POSIX, or::

    C:\> set SKIP_SLOW=1
    C:\> set PYTHONHASHSEED=0
    C:\> python tests/test_all.py

on Windows.


First steps
-----------

For now, we just list how to use particular parts of the API as they take
shape.

Using the database API
^^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; database

.. currentmodule:: distlib.database

You can use the ``distlib.database`` package to access information about
installed distributions. This information is available through the
following classes:

* :class:`DistributionPath`, which represents a set of distributions installed
  on a path.

* :class:`Distribution`, which represents an individual distribution,
  conforming to recent packaging PEPs (:pep:`643`, :pep:`566`, :pep:`508`, :pep:`440`,
  :pep:`386`, :pep:`376`, :pep:`345`, :pep:`314` and :pep:`241`).
* :class:`EggInfoDistribution`, which represents a legacy distribution in
  egg format.

Distribution paths
~~~~~~~~~~~~~~~~~~

The :class:`Distribution` and :class:`EggInfoDistribution` classes are normally not
instantiated directly; rather, they are returned by querying
:class:`~distlib.database.DistributionPath` for distributions. To create a
``DistributionPath`` instance, you can do ::

    >>> from distlib.database import DistributionPath
    >>> dist_path = DistributionPath()

Querying a path for distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this most basic form, ``dist_path`` will provide access to all non-legacy
distributions on ``sys.path``. To get these distributions, you invoke the
:meth:`~distlib.database.DistributionPath.get_distributions` method, which returns an
iterable. Let's try it::

    >>> list(dist_path.get_distributions())
    []

This may seem surprising if you've just started looking at ``distlib``,
as you won't *have* any non-legacy distributions.

Including legacy distributions in the search results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To include distributions created and installed using ``setuptools`` or
``distribute``, you need to create the ``DistributionPath`` by specifying an
additional keyword argument, like so::

    >>> dist_path = DistributionPath(include_egg=True)

and then you'll get a less surprising result::

    >>> len(list(dist_path.get_distributions()))
    77

The exact number returned will be different for you, of course. You can ask for a
particular distribution by name, using the
:meth:`~distlib.database.DistributionPath.get_distribution` method::

    >>> dist_path.get_distribution('setuptools')
    <EggInfoDistribution u'setuptools' 0.6c11 at '/usr/lib/python2.7/dist-packages/setuptools.egg-info'>

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

or, if you leave out egg-based distributions::

    >>> special_dists = DistributionPath(['tests/fake_dists'])
    >>> pprint([d.name for d in special_dists.get_distributions()])
    ['babar',
     'choxie',
     'towel-stuff',
     'grammar']

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

This entry format is used in the :ref:`scripts` for installing scripts based on Python
callables.

Distribution dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the ``distlib.locators`` package to locate the dependencies that
a distribution has. The ``distlib.database`` package has code which
allow you to analyse the relationships between a set of distributions:

* :func:`~distlib.database.make_graph`, which generates a dependency graph from a list
  of distributions.
* :func:`~distlib.database.get_dependent_dists`, which takes a list of distributions
  and a specific distribution in that list, and returns the distributions that
  are dependent on that specific distribution.
* :func:`~distlib.database.get_required_dists`, which takes a list of distributions and
  a specific distribution in that list, and returns the distributions that
  are required by that specific distribution.

The graph returned by :func:`~distlib.database.make_graph` is an instance of
:class:`DependencyGraph`.

Using the locators API
^^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; locators

.. currentmodule:: distlib.locators

Overview
~~~~~~~~

To locate a distribution in an index, we can use the :func:`locate` function.
This returns a potentially downloadable distribution (in the sense that it
has a download URL -- of course, there are no guarantees that there will
actually be a downloadable resource at that URL). The return value is an
instance of :class:`distlib.database.Distribution` which can be queried for
any distributions it requires, so that they can also be located if desired.
Here is a basic example::

    >>> from distlib.locators import locate
    >>> flask = locate('flask')
    >>> flask
    <Distribution Flask (0.10.1) [https://pypi.org/packages/source/F/Flask/Flask-0.10.1.tar.gz]>
    >>> dependencies = [locate(r) for r in flask.run_requires]
    >>> from pprint import pprint
    >>> pprint(dependencies)
    [<Distribution Werkzeug (0.9.1) [https://pypi.org/packages/source/W/Werkzeug/Werkzeug-0.9.1.tar.gz]>,
     <Distribution Jinja2 (2.7) [https://pypi.org/packages/source/J/Jinja2/Jinja2-2.7.tar.gz]>,
     <Distribution itsdangerous (0.21) [https://pypi.org/packages/source/i/itsdangerous/itsdangerous-0.21.tar.gz]>]
    >>>

The values in the ``run_requires`` property are just strings. Here's another example,
showing a little more detail::

    >>> authy = locate('authy')
    >>> authy.run_requires
    set(['httplib2 (>= 0.7, < 0.8)', 'simplejson'])
    >>> authy
    <Distribution authy (1.0.0) [http://pypi.org/packages/source/a/authy/authy-1.0.0.tar.gz]>
    >>> deps = [locate(r) for r in authy.run_requires]
    >>> pprint(deps)
    [<Distribution httplib2 (0.7.7) [http://pypi.org/packages/source/h/httplib2/httplib2-0.7.7.zip]>,
     <Distribution simplejson (3.3.0) [http://pypi.org/packages/source/s/simplejson/simplejson-3.3.0.tar.gz]>]
    >>>

Note that the constraints on the dependencies were honoured by :func:`locate`.


Under the hood
~~~~~~~~~~~~~~

Under the hood, :func:`~distlib.locators.locate` uses *locators*. Locators are a
mechanism for finding distributions from a range of sources. Although the ``pypi``
subpackage has been copied from ``distutils2`` to ``distlib``, there may be benefits
in a higher-level API, and so the ``distlib.locators`` package has been created as an
experiment. Locators are objects which locate distributions. A locator instance's
:meth:`~distlib.locators.Locator.get_project` method is called, passing in a project
name: The method returns a dictionary containing information about distribution
releases found for that project. The keys of the returned dictionary are versions, and
the values are instances of :class:`distlib.database.Distribution`.

The following locators are provided:

* :class:`DirectoryLocator` -- this is instantiated with a base directory and
  will look for archives in the file system tree under that directory. Name
  and version information is inferred from the filenames of archives, and the
  amount of information returned about the download is minimal. The locator
  searches all subdirectories by default, but can be set to only look in the
  specified directory by setting the ``recursive`` keyword argument to
  ``False``.

* :class:`PyPIRPCLocator`. -- This takes a base URL for the RPC service and
  will locate packages using PyPI's XML-RPC API. This locator is a little slow
  (the scraping interface seems to work faster) and case-sensitive. For
  example, searching for ``'flask'`` will throw up no results, but you get the
  expected results when searching from ``'Flask'``. This appears to be a
  limitation of the underlying XML-RPC API. Note that 20 versions of a
  project necessitate 41 network calls (one to get the versions, and
  two more for each version -- one to get the metadata, and another to get the
  downloads information).

* :class:`~distlib.locators.PyPIJSONLocator`. -- This takes a base URL for the JSON
  service and will locate packages using PyPI's JSON API. This locator is
  case-sensitive. For example, searching for ``'flask'`` will throw up no results, but
  you get the expected results when searching from ``'Flask'``. This appears to be a
  limitation of the underlying JSON API. Note that unlike the XML-RPC service, only
  non-hidden releases will be returned.

* :class:`~distlib.locators.SimpleScrapingLocator` -- this takes a base URL for the
  site to scrape, and locates packages using a similar approach to the
  ``PackageFinder`` class in ``pip``, or as documented in the ``setuptools``
  documentation as the approach used by ``easy_install``.

* :class:`~distlib.locators.DistPathLocator` -- this takes a
  :class:`~distlib.database.DistributionPath` instance and locates installed
  distributions. This can be used with :class:`AggregatingLocator` to satisfy
  requirements from installed distributions before looking elsewhere for them.

..
    * :class:`~distlib.locators.JSONLocator` -- this uses an improved JSON metadata schema
      and returns data on all versions of a distribution, including dependencies,
      using a single network request.

* :class:`~distlib.locators.AggregatingLocator` -- this takes a list of other
  aggregators and delegates finding projects to them. It can either return the first
  result found (i.e. from the first aggregator in the list provided which returns a
  non-empty result), or a merged result from all the aggregators in the list.

There is a default locator, available at :attr:`distlib.locators.default_locator`.

The ``locators`` package also contains a function,
:func:`get_all_distribution_names`, which retrieves the names of all
distributions registered on PyPI::

    >>> from distlib.locators import get_all_distribution_names
    >>> names = get_all_distribution_names()
    >>> len(names)
    31905
    >>>

This is implemented using the XML-RPC API.

..

    Apart from ``JSONLocator``,

None of the locators currently returns enough metadata to allow dependency resolution
to be carried out, but that is a result of the fact that metadata relating to
dependencies are not indexed, and would require not just downloading the distribution
archives and inspection of contained metadata files, but potentially also
introspecting setup.py! This is the downside of having vital information only
available via keyword arguments to the ``setup()`` call: hopefully, a move to fully
declarative metadata will facilitate indexing it and allowing the provision of
improved features.

The locators will skip binary distributions other than wheels. (``.egg`` files
are currently treated as binary distributions).

The PyPI locator classes don't yet support the use of mirrors, but that can be
added in due course -- once the basic functionality is working satisfactorily.

.. _use-index:

Using the index API
^^^^^^^^^^^^^^^^^^^

.. currentmodule:: distlib.index


.. index::
   single: APIs; PyPI


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
    'http://pypi.org/pypi'

To use a local test server, you might do this::

    >>> index = PackageIndex('http://localhost:8080/')

Registering a project
~~~~~~~~~~~~~~~~~~~~~

Registering a project can be done using a :class:`~distlib.metadata.Metadata` instance
which holds the index metadata used for registering. A simple example::

    >>> from distlib.metadata import Metadata
    >>> metadata = Metadata()
    >>> metadata.name = 'tatterdemalion'
    >>> metadata.version = '0.1'
    >>> # other fields omitted
    >>> response = index.register(metadata)

The :meth:`~distlib.index.PackageIndex.register` method returns an HTTP response, such
as might be returned by a call to ``urlopen``. If an error occurs, a
:py:class:`~urllib.error.HTTPError` will be raised. Otherwise, the ``response.code`` should be 200.

Uploading a source distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To upload a source distribution, you need to do the following as a minimum::

    >>> metadata = ... # get a populated Metadata instance
    >>> response = index.upload_file(metadata, archive_name)

The :meth:`~distlib.index.PackageIndex.upload_file` method returns an HTTP response
or, in case of error, raises an :py:class:`~urllib.error.HTTPError`.

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
there, you can can explicitly specify an absolute path indicating where the
signing program is to be found::

    >>> index.gpg = '/path/to/gpg'

Once this is set, you can sign the archive before uploading, as follows::

    >>> response = index.upload_file(metadata, archive_name,
    ...                              signer='Test User',
    ...                              sign_password='secret',
                                     keystore='/path/to/keys')

As an alternative to passing the keystore with each call, you can specify
that in an instance attribute::

    >>> index.gpg_home = '/path/to/keys'

The ``keystore`` is a directory which contains the GnuPG key database (files
like ``pubring.gpg``, ``secring.gpg``, and ``trustdb.gpg``).

When you sign a distribution, both the distribution and the signature are
uploaded to the index.


Downloading files
~~~~~~~~~~~~~~~~~

The :class:`PackageIndex` class contains a utility method which allows you to
download distributions (and other files, such as signatures)::

    >>> index.download_file(url, destfile, digest=None, reporthook=None)

This is similar in function to :py:func:`~urllib.request.urlretrieve` in the standard
library. Provide a ``digest`` if you want the call to check that the has digest of the
downloaded file matches a specific value: if not provided, no matching is done. The
value passed can just be a plain string in the case of an MD5 digest or, if you want
to specify the hashing algorithm to use, specify a tuple such as ``('sha1',
'0123456789abcdef...')``. The hashing algorithm must be one that's supported by the
:mod:`hashlib` module.

Benefits to using this method over plain :func:`~urllib.request.urlretrieve` are:

* It will use the ``ssl_verifier``, if set, to ensure that the download is
  coming from where you think it is (see :ref:`verify-https`).
* It will compute the digest as it downloads, saving you from having to read
  the whole of the downloaded file just to compute its digest.

Note that the url you download from doesn't actually need to be on the index --
in theory, it could be from some other site. Note that if you have an
``ssl_verifier`` set on the index, it will perform its checks according to
whichever ``url`` you supply -- whether it's a resource on the index or not.


Verifying signatures
~~~~~~~~~~~~~~~~~~~~

For any archive downloaded from an index, you can retrieve any signature by just
appending ``.asc`` to the path portion of the download URL for the archive, and
downloading that. The index class offers a
:meth:`~distlib.index.PackageIndex.verify_signature` method for validating a
signature. If you have files 'good.bin', 'bad.bin' which are different from each
other, and 'good.bin.asc' has the signature for 'good.bin', then you can verify
signatures like this::

    >>> index.verify_signature('good.bin.asc', 'good.bin', '/path/to/keys')
    True
    >>> index.verify_signature('good.bin.asc', 'bad.bin', '/path/to/keys')
    False

The last argument, which is optional, specifies a directory which holds the
GnuPG keys used for verification -- the *keystore*. Instead of specifying the
keystore location in each call, you can specify the location in an instance
attribute::

    >>> index.gpg_home = '/path/to/keys'

If you do this, you don't need to pass the keystore location.

Note that if you don't have the ``gpg`` or ``gpg2`` programs on the path, you
may need to specify the location of the verifier program explicitly::

    >>> index.gpg = '/path/to/gpg'


Some caveats about verified signatures
++++++++++++++++++++++++++++++++++++++

In order to be able to perform signature verification, you'll have to ensure
that the public keys of whoever signed those distributions are in your key
store. However, having these keys shouldn't give you a false sense of security;
unless you can be sure that those keys actually belong to the people or
organisations they purport to represent, the signature has no real value, even
if it is verified without error. For you to be able to trust a key, it would
need to be signed by someone you trust, who vouches for it -- and this requires
there to be either a signature from a valid certifying authority (e.g. Verisign,
Thawte etc.) or a `Web of Trust <http://wikipedia.org/wiki/Web_of_trust>`_ around
the keys that you want to rely on.

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

The :meth:`~distlib.index.PackageIndex.upload_documentation` method returns an HTTP
response or, in case of error, raises an :class:`~urllib.error.HTTPError`. The call
will zip up the entire contents of the passed directory ``doc_dir`` and upload the zip
file to the index.

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

.. _verify-https:

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
:class:`~ssl.CertificateError` (a subclass of :class:`ValueError`).

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
interaction with a server -- for example:

* Deal with a Man-In-The-Middle proxy server which listens on port 443
  but talks HTTP rather than HTTPS
* Deal with situations where an index page obtained via HTTPS contains
  links with a scheme of ``http`` rather than ``https``.

To do this, instead of using :py:class:`~urllib.request.HTTPSHandler` as shown above,
use the :class:`~distlib.util.HTTPSOnlyHandler` class instead, which disallows any
HTTP traffic. It's used in the same way as :py:class:`~urllib.request.HTTPSHandler`::

    >>> from distlib.util import HTTPSOnlyHandler
    >>> verifier = HTTPSOnlyHandler('/path/to/root/certs.pem')
    >>> index.ssl_verifier = verifier

Note that with this handler, you can't make *any* HTTP connections at all -
it will raise :py:class:`~urllib.error.URLError` if you try.


Getting hold of root certificates
+++++++++++++++++++++++++++++++++

At the time of writing, you can find a file in the appropriate format on the
`cURL website <http://curl.haxx.se/docs/caextract.html>`_. Just download the
``cacert.pem`` file and pass the path to it when instantiating your verifier.


Saving a default configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't have a ``.pypirc`` file but want to save one, you can do this by setting
the username and password and calling the
:meth:`~distlib.index.PackageIndex.save_configuration` method::

    >>> index = PackageIndex()
    >>> index.username = 'fred'
    >>> index.password = 'flintstone'
    >>> index.save_configuration()

This will use ``distutils`` code to save a default ``.pypirc`` file which
specifies a single index -- PyPI -- with the specified username and password.

Searching PyPI
~~~~~~~~~~~~~~

You can use the :meth:`~distlib.index.PackageIndex.search` method of
:class:`~distlib.index.PackageIndex`
to search for distributions on PyPI::

    >>> index = PackageIndex()
    >>> from pprint import pprint
    >>> pprint(index.search('tatterdema'))
    [{'_pypi_ordering': 0,
      'name': 'tatterdemalion',
      'summary': 'A dummy distribution',
      'version': '0.1.0'}]

If a string is specified, just the name is searched for. Alternatively, you
can specify a dictionary of attributes to search for, along with values
to match. For example::

    >>> pprint(index.search({'summary': 'dummy'}))
    [{'_pypi_ordering': 5,
      'name': 'collective.lorem',
      'summary': 'A package that provides dummy content generation.',
      'version': '0.2.3'},
     {'_pypi_ordering': 7,
      'name': 'collective.loremipsum',
      'summary': 'Creates dummy content with populated Lorem Ipsum.',
      'version': '0.8'},
     {'_pypi_ordering': 1,
      'name': 'cosent.dummypackage',
      'summary': 'A dummy package for buildtools testing',
      'version': '0.4'},
     {'_pypi_ordering': 0,
      'name': 'django-dummyimage',
      'summary': 'Dynamic Dummy Image Generator For Django!',
      'version': '0.1.1'},
     {'_pypi_ordering': 1,
      'name': 'django-plainpasswordhasher',
      'summary': 'Dummy (plain text) password hashing for Django.',
      'version': '0.2'},
     {'_pypi_ordering': 2,
      'name': 'django-plainpasswordhasher',
      'summary': 'Dummy (plain text) password hashing for Django.',
      'version': '0.3'},
     {'_pypi_ordering': 1,
      'name': 'dummycache',
      'summary': 'A dummy in-memory cache for development and testing. (Not recommended for production use.)',
      'version': '0.0.2'},
     {'_pypi_ordering': 0,
      'name': 'dummy-txredis',
      'summary': 'Dummy txRedis client and factory.',
      'version': '0.5'},
     {'_pypi_ordering': 7,
      'name': 'eea.eggmonkeytesttarget',
      'summary': 'A dummy package to test eea.eggmonkey',
      'version': '5.7'},
     {'_pypi_ordering': 8,
      'name': 'invewrapper',
      'summary': 'dummy/transitional package that depends on "pew"',
      'version': '0.1.8'},
     {'_pypi_ordering': 0,
      'name': 'monoprocessing',
      'summary': 'A dummy implementation of multiprocessing.Pool',
      'version': '0.1'},
     {'_pypi_ordering': 0,
      'name': 'myFun',
      'summary': 'This is a dummy function which prints given list data.',
      'version': '1.0.0'},
     {'_pypi_ordering': 0,
      'name': 'ReadableDict-a-dict-without-brackets',
      'summary': 'provides a dummy implementation of a dict without brackets',
      'version': '0.0'},
     {'_pypi_ordering': 4,
      'name': 'setuptools_dummy',
      'summary': 'Setuptools Dummy Filefinder',
      'version': '0.1.0.4'},
     {'_pypi_ordering': 0,
      'name': 'tatterdemalion',
      'summary': 'A dummy distribution',
      'version': '0.1.0'}]

If you specify multiple attributes, then the search returns the intersection
of matches -- an ``and`` operation::

    >>> pprint(index.search({'summary': 'dummy', 'name': 'ta'}))
    [{'_pypi_ordering': 7,
      'name': 'eea.eggmonkeytesttarget',
      'summary': 'A dummy package to test eea.eggmonkey',
      'version': '5.7'},
     {'_pypi_ordering': 0,
      'name': 'tatterdemalion',
      'summary': 'A dummy distribution',
      'version': '0.1.0'}]

If you want a union of matches -- an ``or`` operation -- specify a second
argument to the :meth:`PackageIndex.search` method with the value ``'or'``::

    >>> pprint(index.search({'version': '2013.9', 'name': 'pytzp'}, 'or'))
    [{'_pypi_ordering': 65,
      'name': 'pytz',
      'summary': 'World timezone definitions, modern and historical',
      'version': '2013.9'},
     {'_pypi_ordering': 2,
      'name': 'pytzpure',
      'summary': 'A pure-Python version of PYTZ (timezones).',
      'version': '0.2.4'}]

The search functionality makes use of PyPI's XML-RPC interface, so it will only
work for indexes which supply a compatible implementation. The following search
attributes are currently supported:

* name
* version
* stable_version
* author
* author_email
* maintainer
* maintainer_email
* home_page
* license
* summary
* description
* keywords
* platform
* download_url
* classifiers (list of classifier strings)
* project_url
* docs_url (URL of the pythonhosted.org docs if they've been supplied)


.. _use-metadata:

Using the metadata and markers APIs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; metadata

.. currentmodule:: distlib.metadata

The metadata API is exposed through a :class:`Metadata` class. This class can read and
write metadata files complying with any of the defined versions: 1.0 (:pep:`241`), 1.1
(:pep:`314`), 1.2 (:pep:`345`), 2.1 (:pep:`566`) and 2.2 (:pep:`643`). It implements
methods to parse and write metadata files.

Instantiating metadata
~~~~~~~~~~~~~~~~~~~~~~

You can simply instantiate a :class:`Metadata` instance and start populating
it::

    >>> from distlib.metadata import Metadata
    >>> md = Metadata()
    >>> md.name = 'foo'
    >>> md.version = '1.0'

An instance so created may not be valid unless it has some minimal properties which
meet certain constraints, as specified in the `Core metadata specifications
<https://packaging.python.org/en/latest/specifications/core-metadata>`_.

These constraints aren't applicable to legacy metadata. Therefore, when
creating :class:`Metadata` instances to deal with such metadata, you can
specify the ``scheme`` keyword when creating the instance::

    >>> legacy_metadata = Metadata(scheme='legacy')

The term 'legacy' refers to the version scheme.

Whether dealing with current or legacy metadata. an instance's ``validate()``
method can be called to ensure that the metadata has no missing or invalid
data. This raises a ``DistlibException`` (either ``MetadataMissingError`` or
``MetadataInvalidError``) if the metadata isn't valid.

You can initialise an instance with a dictionary using the following form::

    >>> metadata = Metadata(mapping=a_dictionary)


Reading metadata from files and streams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`Metadata` class can be instantiated with the path of the
metadata file. Here's an example with legacy metadata::

    >>> from distlib.metadata import Metadata
    >>> metadata = Metadata(path='PKG-INFO')
    >>> metadata.name
    'CLVault'
    >>> metadata.version
    '0.5'
    >>> metadata.run_requires
    ['keyring']

Instead of using the ``path`` keyword argument to specify a file location, you
can also specify a ``fileobj`` keyword argument to specify a file-like object
which contains the data.


Writing metadata to paths and streams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writing metadata can be done using the ``write`` method::

   >>> metadata.write(path='/to/my/pydist.json')

You can also specify a file-like object to write to, using the ``fileobj``
keyword argument.


Using markers
~~~~~~~~~~~~~

.. index::
   single: Markers; evaluating
   single: Environment markers; evaluating

Environment markers are implemented in the ``distlib.markers`` package and accessed
via a single function, :func:`~distlib.markers.interpret`.

See `PEP 508 <https://www.python.org/dev/peps/pep-0508/#environment-markers>`_ for
more information about environment markers. The :func:`~distlib.markers.interpret`
function takes a string argument which represents a Boolean expression, and returns
either ``True`` or ``False``::

    >>> from distlib.markers import interpret
    >>> interpret('python_version >= "1.0"')
    True

.. index::
   single: Markers; overriding
   single: Environment markers; overriding

You can pass in a context dictionary which is checked for values before the
environment::

    >>> interpret('python_version >= "1.0"', {'python_version': '0.5'})
    False


You won't normally need to work with markers in this way -- they are dealt with by the
:class:`~distlib.metadata.Metadata` and :class:`~distlib.database.Distribution` logic
when needed.


Using the resource API
^^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; package resources

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

.. index::
   single: Resources; in the file system
   single: Package resources; in the file system

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

Access to resources in the ``.zip`` files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Resources; in .zip files
   single: Package resources; in .zip files


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

and so on.


Iterating over resources
~~~~~~~~~~~~~~~~~~~~~~~~

You can iterate over resources as shown in the following example::

    >>> from distlib.resources import finder
    >>> f = finder('foofoo')
    >>> iterator = f.iterator('')
    >>> for r in iterator: print('%-20s %s' % (r.name, r.is_container))
    ...
                         True
    foo_resource.bin     False
    __init__.py          False
    bar                  True
    bar/bar_resource.bin False
    bar/baz.py           False
    bar/__init__.py      False
    nested               True
    nested/nested_resource.bin False

It works with zipped resources, too::

    >>> import sys
    >>> sys.path.append('foo.zip')
    >>> from distlib.resources import finder
    >>> f = finder('foo')
    >>> iterator = f.iterator('')
    >>> for r in iterator: print('%-20s %s' % (r.name, r.is_container))
    ...
                         True
    foo_resource.bin     False
    __init__.py          False
    bar                  True
    bar/bar_resource.bin False
    bar/baz.py           False
    bar/__init__.py      False


Using the scripts API
^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; script installation

.. currentmodule:: distlib.scripts

.. index::
   single: Scripts; installing

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

.. index::
   single: Scripts; specifying what to install

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

  where the *flags* part is optional.

  For more information about flags, see :ref:`flag-formats`.

  Note that this format is exactly the same as for export entries in a
  distribution (see :ref:`dist-exports`).

  When this form is passed to the :meth:`ScriptMaker.make` method, a Python
  stub script is created with the appropriate shebang line and with code to
  load and call the specified callable with no arguments, returning its value
  as the return code from the script.

  You can pass an optional ``options`` dictionary to the
  :meth:`~distlib.scripts.ScriptMaker.make` method. This is meant to contain options
  which control script generation. There are two options currently in use:

  ``gui``: This Boolean value, if ``True``, indicates on Windows that a Windows
  executable launcher (rather than a launcher which is a console application)
  should be used. (This only applies if ``add_launchers`` is true.)

  ``interpreter_args``: If provided, this should be a list of strings which
  are added to the shebang line following the interpreter. If there are values
  with spaces, you will need to surround them with double quotes.

  .. note:: Use of this feature may affect portability, since POSIX does not
    standardise how these arguments are passed to the interpreter (see
    https://en.wikipedia.org/wiki/Shebang_line#Portability for more
    information).

  For example, you can pass ``{'gui': True}`` to generate a windowed script.

Wrapping callables with scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Scripts; wrapping callables

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


Specifying a custom executable for shebangs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Scripts; specifying custom executables

You may need to specify a custom executable for shebang lines. To do this, set the
:attr:`~distlib.scripts.ScriptMaker.executable` attribute of a :class:`ScriptMaker`
instance to the absolute Unicode path of the executable which you want to be written
to the shebang lines of scripts. If not specified, the executable running the
:class:`ScriptMaker` code is used. If the value has spaces, you should surround it
with double quotes. You can use the :func:`enquote_executable` function for this.

.. versionchanged:: 0.3.1
   The :func:`~distlib.scripts.enquote_executable` function was an internal function
   ``_enquote_executable`` in earlier versions.

For relocatable .exe files under Windows, you can specify the location of the python
executable relative to the script by putting *<launcher_dir>* as the beginning of the
executable path.  Since windows places *python.exe* in the root install directory and
the application scripts in the *Scripts* subdirectory, setting ``maker.executable =
r"<launcher_dir>\..\python.exe"`` will allow you to move a python installation which is
installed together with an application to a different path or a different machine and
the .exe files will still run.


Generating variants of a script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Scripts; generating variants

When installing a script ``foo``, it is not uncommon to want to install
version-specific variants such as ``foo3`` or ``foo-3.2``. You can control
exactly which variants of the script get written through the
:class:`ScriptMaker` instance's ``variants`` attribute. This defaults to
``set(('', 'X.Y'))``, which means that by default a script ``foo`` would be
installed as ``foo`` and ``foo-3.2`` under Python 3.2. If the value of the
``variants`` attribute were ``set(('', 'X', 'X.Y'))`` then the ``foo`` script
would be installed as ``foo``, ``foo3`` and ``foo-3.2`` when run under Python
3.2.

.. note:: If you need to generate variants for a different version of Python than the
   one running the :class:`ScriptMaker` code, set the ``version_info`` attribute of the
   :class:`ScriptMaker` instance to a 2-tuple holding the major and minor version
   numbers of the target Python version.

   .. versionadded:: 0.3.1

Avoiding overwriting existing scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Scripts; avoid overwriting

In some scenarios, you might overwrite existing scripts when you shouldn't. For
example, if you use Python 2.7 to install a distribution with script ``foo`` in
the user site (see :pep:`370`), you will write (on POSIX) scripts
``~/.local/bin/foo`` and ``~/.local/bin/foo-2.7``. If you then install the same
distribution with Python 3.2, you would write (on POSIX) scripts
``~/.local/bin/foo`` and ``~/.local/bin/foo-3.2``. However, by overwriting the
``~/.local/bin/foo`` script, you may prevent verification or removal of the 2.7
installation to fail, because the overwritten file may be different (and so
have a different hash from what was computed during the 2.7 installation).

To control overwriting of generated scripts this way, you can use the
:attr:`~distlib.scripts.ScriptMaker.clobber` attribute of a
:class:`~distlib.scripts.ScriptMaker` instance. This is set to ``False`` by default,
which prevents overwriting; to force overwriting, set it to ``True``.

Generating windowed scripts on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Scripts; windowed

The :meth:`~distlib.scripts.ScriptMaker.make` and
:meth:`~distlib.scripts.ScriptMaker.make_multiple` methods take an optional second
``options`` argument, which can be used to control script generation. If specified,
this should be a dictionary of options. Currently, only the value for the ``gui`` key
in the dictionary is inspected: if ``True``, it generates scripts with ``.pyw``
extensions (rather than ``.py``) and, if ``add_launchers`` is specified as ``True`` in
the :class:`~distlib.scripts.ScriptMaker` instance, then (on Windows) a windowed
native executable launcher is created (otherwise, the native executable launcher will
be a console application).


Using the version API
^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; version


.. currentmodule:: distlib.version

Overview
~~~~~~~~

.. index::
   single: Versions; overview

The :class:`NormalizedVersion` class implements a :pep:`440` compatible
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

.. index::
   single: Versions; matching

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


.. _use-wheel:

Using the wheel API
^^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; wheel


.. currentmodule:: distlib.wheel

You can use the ``distlib.wheel`` package to build and install from files in
the Wheel format, defined in :pep:`427`.

Building wheels
~~~~~~~~~~~~~~~

.. index::
   pair: building; wheels


Building wheels is straightforward::

    from distlib.wheel import Wheel

    wheel = Wheel()

    # Set the distribution's identity
    wheel.name = 'name_of_distribution'
    wheel.version = '0.1'

    # Indicate where the files to go in the wheel are to be found
    paths = {
        'prefix': '/path/to/installation/prefix',
        'purelib': '/path/to/purelib',  # only one of purelib
        'platlib': '/path/to/platlib',  # or platlib should be set
        'scripts': '/path/to/scripts',
        'headers': '/path/to/headers',
        'data': '/path/to/data',
    }

    wheel.dirname = '/where/you/want/the/wheel/to/go'
    # Now build
    wheel.build(paths)

If the ``'data'``, ``'headers'`` and ``'scripts'`` keys are absent, or point to
paths which don't exist, nothing will be added to the wheel for these
categories. The ``'prefix'`` key and one of ``'purelib'`` or ``'platlib'``
*must* be provided, and the paths referenced should exist.


Customising tags during build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: wheels; custom tags when building

By default, the :meth:`~distlib.wheel.Wheel.build` method will use default tags
depending on whether or not the build is a pure-Python build:

* For a pure-Python build, the ``pyver`` will be set to ``pyXY`` where ``XY``
  is the version of the building Python. The ``abi`` tag will be ``none`` and
  the ``arch`` tag will be ``any``.

* For a build which is not pure-Python (i.e. contains C code), the ``pyver``
  will be set to e.g. ``cpXY``, and the ``abi`` and ``arch`` tags will be
  set according to the building Python.

If you want to override these default tags, you can pass a ``tags`` parameter to the
:meth:`~distlib.wheel.Wheel.build` method which has the tags you want to declare. For
example, for a pure build where we know that the code in the wheel will be compatible
with the major version of the building Python::

    from wheel import PYVER
    tags = {
        'pyver': [PYVER[:-1], PYVER],
    }
    wheel.build(paths, tags)

This would set the ``pyver`` tags to be ``pyX.pyXY`` where ``X`` and ``Y``
relate to the building Python. You can similarly pass values using the ``abi``
and ``arch`` keys in the ``tags`` dictionary.

Specifying a wheel's version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also specify a particular "Wheel-Version" to be written to the wheel
metadata of a wheel you're building. Simply pass a (major, minor) tuple in
the ``wheel_version`` keyword argument to :meth:`~distlib.wheel.Wheel.build`. If not
specified, the most recent version supported is written.

Installing from wheels
~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: installing; wheels

Installing from wheels is similarly straightforward. You just need to indicate
where you want the files in the wheel to be installed::

    from distlib.wheel import Wheel
    from distlib.scripts import ScriptMaker

    wheel = Wheel('/path/to/my_dist-0.1-py32-none-any.whl')

    # Indicate where the files in the wheel are to be installed to.
    # All the keys should point to writable paths.
    paths = {
        'prefix': '/path/to/installation/prefix',
        'purelib': '/path/to/purelib',
        'platlib': '/path/to/platlib',
        'scripts': '/path/to/scripts',
        'headers': '/path/to/headers',
        'data': '/path/to/data',
    }

    maker = ScriptMaker(None, None)
    # You can specify a custom executable in script shebang lines, whether
    # or not to install native executable launchers, whether to do a dry run
    # etc. by setting attributes on the maker, either when creating it or
    # subsequently.

    # Now install. The method accepts optional keyword arguments:
    #
    # - A ``warner`` argument which, if specified, should be a callable that
    #   will be called with (software_wheel_version, file_wheel_version) if
    #   they differ. They will both be in the form (major_ver, minor_ver).
    #
    # - A ``lib_only`` argument which indicates that only the library portion
    #   of the wheel should be installed - no scripts, header files or
    #   non-package data.

    wheel.install(paths, maker)

Only one of the ``purelib`` or ``platlib`` paths will actually be written to
(assuming that they are different, which isn't often the case). Which one it is
depends on whether the wheel metadata declares that the wheel contains pure
Python code.


Verifying wheels
~~~~~~~~~~~~~~~~

.. index::
   pair: verifying; wheels

You can verify that a wheel's contents match the declared contents in the wheel's
``RECORD`` entry, by calling the :meth:`~distlib.wheel.Wheel.verify` method. This will
raise a :class:`~distlib.DistlibException` if a size or digest mismatch is found.


Modifying wheels
~~~~~~~~~~~~~~~~

.. index::
   pair: modifying; wheels

.. note:: In an ideal world one would not need to modify wheels, but in the
   short term there might be a need to do so (for example, to add dependency
   information which is missing). If you are working with wheels on your own
   projects, you *shouldn't* use the method described here, as you will have
   full control of the wheels you build yourself. However, if you are working
   with third party wheels which you don't build yourself but you need to
   modify in some way, then the approach described below might be useful.

You can update existing wheels with ``distlib`` by calling the
:meth:`~Wheel.update` method of a wheel. This is called as follows::

    modified = wheel.update(modifier, dest_dir, **kwargs)

where the ``modifier`` is a callable which you specify, and ``kwargs`` are options you
want to pass to it (currently, the :meth:`~distlib.wheel.Wheel.update` method passes
``kwargs`` unchanged to the ``modifier``). The ``dest_dir`` argument indicates where
you want any new wheel to be written - it is optional and if not specified, *the
existing wheel will be overwritten*.

The  :meth:`~distlib.wheel.Wheel.update` method extracts the entire contents of the
wheel to a temporary location, and then calls ``modifier`` as follows::

    modified = modifier(path_map, **kwargs)

where ``path_map`` is a dictionary mapping archive paths to the location
of the corresponding extracted archive entry, and ``kwargs`` is whatever
was passed to the ``update`` method. If the modifier returns ``True``,
a new wheel is built from the (possibly updated) contents of ``path_map``
and its path name. The passed ``path_map`` will contain all of the wheel's
entries other than the ``RECORD`` entry (which will be recreated if a new
wheel is built).

For example, if you wanted to add ``numpy`` as a dependency in a ``scipy``
wheel, you might do something like this::

    def add_numpy_dependency(path_map, **kwargs):
        mdpath = path_map['scipy-0.11.dist-info/pydist.json']
        md = Metadata(path=mdpath)
        md.add_requirements(['numpy'])
        md.write(path=mdpath)
        return True

    wheel = Wheel('scipy-0.11-py27-abi3-linux_x86_64.whl')
    wheel.update(add_numpy_dependency)

In the above example, the modifier doesn't actually use ``kwargs``,
but you could pass useful information which can be used to control the
modifier's operation. For example, you might make the function work with
other distributions than ``scipy``, or other versions of ``scipy``::

    def add_numpy_dependency(path_map, **kwargs):
        name = kwargs.get('name', 'scipy')
        version = kwargs.get('version', '0.11')
        key = '%s-%s.dist-info/pydist.json' % (name, version)
        mdpath = path_map[key]
        md = Metadata(path=mdpath)
        md.add_requirements(['numpy'])
        md.write(path=mdpath)
        return True


Mounting wheels
~~~~~~~~~~~~~~~

.. index::
   single: wheels; mounting

One of Python's perhaps under-used features is ``zipimport``, which gives the ability
to import Python source from ``.zip`` files. Since wheels are ``.zip`` files, they can
sometimes be used to provide functionality without needing to be installed. Whereas
``.zip`` files contain no convention for indicating compatibility with a particular
Python, wheels *do* contain this compatibility information. Thus, it is possible to
check if a wheel can be directly imported from, and the wheel support in ``distlib``
allows you to take advantage of this using the :meth:`~distlib.wheel.Wheel.mount` and
:meth:`~distlib.wheel.Wheel.unmount` methods. When you mount a wheel, its absolute
path name is added to ``sys.path``, allowing the Python code in it to be imported. (A
:class:`~distlib.DistlibException` is raised if the wheel isn't compatible with the
Python which calls the :meth:`~distlib.wheel.Wheel.mount` method.)

The :meth:`~distlib.wheel.Wheel.mount` method takes an optional keyword parameter
``append`` which defaults to ``False``, meaning the a mounted wheel's pathname is
added to the beginning of ``sys.path``. If you pass ``True``, the pathname is appended
to ``sys.path``.

The :meth:`~distlib.wheel.Wheel.mount` method goes further than just enabling Python
imports -- any C extensions in the wheel are also made available for import. For this
to be possible, the wheel has to be built with additional metadata about extensions --
a JSON file called ``EXTENSIONS`` which serialises an extension mapping dictionary.
This maps extension module names to the names in the wheel of the shared libraries
which implement those modules.

Running :meth:`~distlib.wheel.Wheel.unmount` on the wheel removes its absolute
pathname from ``sys.path`` and makes its C extensions, if any, also unavailable for
import.

.. note:: The C extension mounting functionality may not work in all cases,
   though it should work in a useful subset of cases. Use with care. Note that
   extension information is currently only available in wheels built using
   ``distil`` -- for wheels built using e.g. ``pip``, this note will not apply,
   because C extensions will never be available for import.

   * There might be subtle differences in binary compatibility between the
     extension and the running Python, because the compatibility tag framework
     currently does not capture all the relevant ABI information. This is a
     situation which can be expected to improve over time.

   * If the extension uses custom dynamically linked libraries which are
     bundled with the extension, it may not be found by the dynamic loading
     machinery, for reasons that are platform-dependent. In such cases, you
     should have a good understanding of how dynamic loading works on your
     platforms, before taking advantage of this feature.

..
    Section commented out because get_package_data no longer available, and
    the code presented uses it. Another casualty of PEP 426 withdrawal.

    Using vanilla pip to build wheels for existing distributions on PyPI
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Although work is afoot to add wheel support to ``pip``, you don't need this
    to build wheels for existing PyPI distributions if you use ``distlib``. The
    following script shows how you can use an unpatched, vanilla ``pip`` to
    build wheels::

        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        #
        # Copyright (C) 2013 Vinay Sajip. License: MIT
        #

        import logging
        import optparse     # for 2.6
        import os
        import re
        import shutil
        import subprocess
        import sys
        import tempfile

        logger = logging.getLogger('wheeler')

        from distlib.compat import configparser, filter
        from distlib.database import DistributionPath, Distribution, make_graph
        from distlib.locators import (JSONLocator, SimpleScrapingLocator,
                                      AggregatingLocator, DependencyFinder)
        from distlib.manifest import Manifest
        from distlib.metadata import Metadata
        from distlib.util import parse_requirement, get_package_data
        from distlib.wheel import Wheel

        EGG_INFO_RE = re.compile(r'(-py\d\.\d)?\.egg-info', re.I)

        INSTALLED_DISTS = DistributionPath(include_egg=True)


        def get_requirements(data):
            lines = []
            for line in data.splitlines():
                line = line.strip()
                if not line or line[0] == '#':
                    continue
                lines.append(line)
            reqts = []
            extras = {}
            result = {'install': reqts, 'extras': extras}
            for line in lines:
                if line[0] != '[':
                    reqts.append(line)
                else:
                    i = line.find(']', 1)
                    if i < 0:
                        raise ValueError('unrecognised line: %r' % line)
                    extra = line[1:i]
                    extras[extra] = reqts = []
            return result


        def convert_egg_info(libdir, prefix, options):
            files = os.listdir(libdir)
            ei = list(filter(lambda d: d.endswith('.egg-info'), files))[0]
            olddn = os.path.join(libdir, ei)
            di = EGG_INFO_RE.sub('.dist-info', ei)
            newdn = os.path.join(libdir, di)
            os.rename(olddn, newdn)
            if options.compatible:
                renames = {}
            else:
                renames = {
                    'entry_points.txt': 'EXPORTS',
                }
            excludes = set([
                'SOURCES.txt',          # of no interest in/post WHEEL
                'installed-files.txt',  # replaced by RECORD, so not needed
                'requires.txt',         # added to METADATA, so not needed
                'PKG-INFO',             # replaced by METADATA
                'not-zip-safe',         # not applicable
            ])
            files = os.listdir(newdn)
            metadata = mdname = reqts = None
            for oldfn in files:
                pn = os.path.join(newdn, oldfn)
                if oldfn in renames:
                    os.rename(pn, os.path.join(newdn, renames[oldfn]))
                else:
                    if oldfn == 'requires.txt':
                        with open(pn, 'r') as f:
                            reqts = get_requirements(f.read())
                    elif oldfn == 'PKG-INFO':
                        metadata = Metadata(path=pn)
                        pd = get_package_data(metadata.name, metadata.version)
                        metadata = Metadata(mapping=pd['index-metadata'])
                        mdname = os.path.join(newdn, 'pydist.json')
                    if oldfn in excludes or not options.compatible:
                        os.remove(pn)
            if metadata:
                # Use Metadata 1.2 or later
                metadata.provides += ['%s (%s)' % (metadata.name,
                                                   metadata.version)]
                # Update if not set up by get_package_data
                if reqts and not metadata.run_requires:
                    metadata.dependencies = reqts
                metadata.write(path=mdname)
            manifest = Manifest(os.path.dirname(libdir))
            manifest.findall()
            paths = manifest.allfiles
            dp = DistributionPath([libdir])
            dist = next(dp.get_distributions())
            dist.write_installed_files(paths, prefix)


        def install_dist(distname, workdir, options):
            pfx = '--install-option='
            purelib = pfx + '--install-purelib=%s/purelib' % workdir
            platlib = pfx + '--install-platlib=%s/platlib' % workdir
            headers = pfx + '--install-headers=%s/headers' % workdir
            scripts = pfx + '--install-scripts=%s/scripts' % workdir
            data = pfx + '--install-data=%s/data' % workdir
            # Use the pip adjacent to sys.executable, if any (for virtualenvs)
            d = os.path.dirname(sys.executable)
            files = filter(lambda o: o in ('pip', 'pip.exe'), os.listdir(d))
            if not files:
                prog = 'pip'
            else:
                prog = os.path.join(d, next(files))
            cmd = [prog, 'install',
                   '--no-deps', '--quiet',
                   '--index-url', 'http://pypi.org/simple/',
                   '--timeout', '3', '--default-timeout', '3',
                   purelib, platlib, headers, scripts, data, distname]
            result = {
                'scripts': os.path.join(workdir, 'scripts'),
                'headers': os.path.join(workdir, 'headers'),
                'data': os.path.join(workdir, 'data'),
            }
            print('Pipping %s ...' % distname)
            p = subprocess.Popen(cmd, shell=False, stdout=sys.stdout,
                                 stderr=subprocess.STDOUT)
            stdout, _ = p.communicate()
            if p.returncode:
                raise ValueError('pip failed to install %s:\n%s' % (distname, stdout))
            for dn in ('purelib', 'platlib'):
                libdir = os.path.join(workdir, dn)
                if os.path.isdir(libdir):
                    result[dn] = libdir
                    break
            convert_egg_info(libdir, workdir, options)
            dp = DistributionPath([libdir])
            dist = next(dp.get_distributions())
            md = dist.metadata
            result['name'] = md.name
            result['version'] = md.version
            return result


        def build_wheel(distname, options):
            result = None
            r = parse_requirement(distname)
            if not r:
                print('Invalid requirement: %r' % distname)
            else:
                dist = INSTALLED_DISTS.get_distribution(r.name)
                if dist:
                    print('Can\'t build a wheel from already-installed '
                          'distribution %s' % dist.name_and_version)
                else:
                    workdir = tempfile.mkdtemp()    # where the Wheel input files will live
                    try:
                        paths = install_dist(distname, workdir, options)
                        paths['prefix'] = workdir
                        wheel = Wheel()
                        wheel.name = paths.pop('name')
                        wheel.version = paths.pop('version')
                        wheel.dirname = options.destdir
                        wheel.build(paths)
                        result = wheel
                    finally:
                        shutil.rmtree(workdir)
            return result


        def main(args=None):
            parser = optparse.OptionParser(usage='%prog [options] requirement [requirement ...]')
            parser.add_option('-d', '--dest', dest='destdir', metavar='DESTDIR',
                              default=os.getcwd(), help='Where you want the wheels '
                              'to be put.')
            parser.add_option('-n', '--no-deps', dest='deps', default=True,
                              action='store_false',
                              help='Don\'t build dependent wheels.')
            options, args = parser.parse_args(args)
            options.compatible = True   # may add flag to turn off later
            if not args:
                parser.print_usage()
            else:
                # Check if pip is available; no point in continuing, otherwise
                try:
                    with open(os.devnull, 'w') as f:
                        p = subprocess.call(['pip', '--version'], stdout=f, stderr=subprocess.STDOUT)
                except Exception:
                    p = 1
                if p:
                    print('pip appears not to be available. Wheeler needs pip to '
                          'build  wheels.')
                    return 1
                if options.deps:
                    # collect all the requirements, including dependencies
                    u = 'http://pypi.org/simple/'
                    locator = AggregatingLocator(JSONLocator(),
                                                 SimpleScrapingLocator(u, timeout=3.0),
                                                 scheme='legacy')
                    finder = DependencyFinder(locator)
                    wanted = set()
                    for arg in args:
                        r = parse_requirement(arg)
                        if not r.constraints:
                            dname = r.name
                        else:
                            dname = '%s (%s)' % (r.name, ', '.join(r.constraints))
                        print('Finding the dependencies of %s ...' % arg)
                        dists, problems = finder.find(dname)
                        if problems:
                            print('There were some problems resolving dependencies '
                                  'for %r.' % arg)
                            for _, info in problems:
                                print('  Unsatisfied requirement %r' % info)
                        wanted |= dists
                    want_ordered = True     # set to False to skip ordering
                    if not want_ordered:
                        wanted = list(wanted)
                    else:
                        graph = make_graph(wanted, scheme=locator.scheme)
                        slist, cycle = graph.topological_sort()
                        if cycle:
                            # Now sort the remainder on dependency count.
                            cycle = sorted(cycle, reverse=True,
                                           key=lambda d: len(graph.reverse_list[d]))
                        wanted = slist + cycle

                        # get rid of any installed distributions from the list
                        for w in list(wanted):
                            dist = INSTALLED_DISTS.get_distribution(w.name)
                            if dist or w.name in ('setuptools', 'distribute'):
                                wanted.remove(w)
                                s = w.name_and_version
                                print('Skipped already-installed distribution %s' % s)

                    # converted wanted list to pip-style requirements
                    args = ['%s==%s' % (dist.name, dist.version) for dist in wanted]

                # Now go build
                built = []
                for arg in args:
                    wheel = build_wheel(arg, options)
                    if wheel:
                        built.append(wheel)
                if built:
                    if options.destdir == os.getcwd():
                        dest = ''
                    else:
                        dest = ' in %s' % options.destdir
                    print('The following wheels were built%s:' % dest)
                    for wheel in built:
                        print('  %s' % wheel.filename)

        if __name__ == '__main__':
            logging.basicConfig(format='%(levelname)-8s %(name)s %(message)s',
                                filename='wheeler.log', filemode='w')
            try:
                rc = main()
            except Exception as e:
                print('Failed - sorry! Reason: %s\nPlease check the log.' % e)
                logger.exception('Failed.')
                rc = 1
            sys.exit(rc)

    This script, ``wheeler.py``, is also available `here
    <https://gist.github.com/vsajip/4988471>`_. Note that by default, it downloads
    dependencies of any distribution you specify and builds separate wheels for
    each distribution. It's smart about not repeating work if dependencies are
    common across multiple distributions you specify::

        $ python wheeler.py sphinx flask
        Finding the dependencies of sphinx ...
        Finding the dependencies of flask ...
        Pipping Jinja2==2.6 ...
        Pipping docutils==0.10 ...
        Pipping Pygments==1.6 ...
        Pipping Werkzeug==0.8.3 ...
        Pipping Sphinx==1.1.3 ...
        Pipping Flask==0.9 ...
        The following wheels were built:
          Jinja2-2.6-py27-none-any.whl
          docutils-0.10-py27-none-any.whl
          Pygments-1.6-py27-none-any.whl
          Werkzeug-0.8.3-py27-none-any.whl
          Sphinx-1.1.3-py27-none-any.whl
          Flask-0.9-py27-none-any.whl

    Note that the common dependency -- ``Jinja2`` -- was only built once.

    You can opt to not build dependent wheels by specifying ``--no-deps`` on the
    command line.

    Note that the script also currently uses an http: URL for PyPI -- this may need
    to change to an https: URL in the future.

    .. note::
       It can't be used to build wheels from existing distributions, as ``pip`` will
       either refuse to install to custom locations (because it views a distribution
       as already installed), or will try to upgrade and thus uninstall the existing
       distribution, even though installation is requested to a custom location (and
       uninstallation is not desirable). For best results, run it in a fresh venv:

       $ my_env/bin/python wheeler.py some_dist

       It should use the venv's ``pip``, if one is found.


.. _use-manifest:

Using the manifest API
^^^^^^^^^^^^^^^^^^^^^^

.. index::
   single: APIs; manifest

.. currentmodule:: distlib.manifest

You can use the ``distlib.manifest`` API to construct lists of files when
creating distributions. This functionality is an improved version of the
equivalent functionality in ``distutils``, where it was not a public API.

You can create instances of the :class:`Manifest` class to work with a set
of files rooted in a particular directory::

    >>> from distlib.manifest import Manifest
    >>> manifest = Manifest('/path/to/my/sources')

This sets the :attr:`~distlib.manifest.Manifest.base` attribute to the passed in root
directory. You can add one or multiple files using names relative to the base
directory::

    >>> manifest.add('abc')
    >>> manifest.add_many(['def', 'ghi'])

As a result of the above two statements, the manifest will consist of
``'/path/to/my/sources/abc'``, ``'/path/to/my/sources/def'`` and
``'/path/to/my/sources/ghi'``. No check is made regarding the existence of
these files.

You can get all the files below the base directory of the manifest::

    >>> manifest.findall()

This will populate the :attr:`~distlib.manifest.Manifest.allfiles` attribute of
``manifest`` with a list of all files in the directory tree rooted at the base.
However, the manifest is still empty::

    >>> manifest.files
    >>> set()

You can populate the manifest -- the :attr:`~distlib.manifest.Manifest.files`
attribute -- by running a number of *directives*, using the
:meth:`~distlib.manifest.Manifest.process_directive` method. Each directive will
either add files from :attr:`~distlib.manifest.Manifest.allfiles` to
:attr:`~distlib.manifest.Manifest.files`, or remove files from
:attr:`~distlib.manifest.Manifest.allfiles` if they were added by a previous
directive. A directive is a string which must have a specific syntax: malformed lines
will result in a :class:`~distlib.DistlibException` being raised. The following
directives are available: they are compatible with the syntax of ``MANIFEST.in`` files
processed by ``distutils``.

Consider the following directory tree::

    testsrc/
    ├── keep
    │   └── keep.txt
    ├── LICENSE
    ├── README.txt
    └── subdir
        ├── lose
        │   └── lose.txt
        ├── somedata.txt
        └── subsubdir
            └── somedata.bin

This will be used to illustrate how the directives work, in the following
sections.


The ``include`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; including files

This takes the form of the word ``include`` (case-sensitive) followed by a number of
file-name patterns (as used in ``MANIFEST.in`` in ``distutils``). All files in
:attr:`~distlib.manifest.Manifest.allfiles` matching the patterns (considered relative
to the base directory) are added to :attr:`~distlib.manifest.Manifest.files`. For
example::

    >>> manifest.process_directive('include R*.txt LIC* keep/*.txt')

This will add ``README.txt``, ``LICENSE`` and ``keep/keep.txt`` to the
manifest.


The ``exclude`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; excluding files

This takes the form of the word ``exclude`` (case-sensitive) followed by a number of
file-name patterns (as used in ``MANIFEST.in`` in ``distutils``). All files in
:attr:`~distlib.manifest.Manifest.files` matching the patterns (considered relative
to the base directory) are removed from :attr:`~distlib.manifest.Manifest.files`. For
example::

    >>> manifest.process_directive('exclude LIC*')

This will remove 'LICENSE' from the manifest, as it was added in the section
above.


The ``global-include`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; including files globally

This works just like ``include``, but will add matching files at all levels of
the directory tree::

    >>> manifest.process_directive('global-include *.txt')

This will add ``subdir/somedata.txt`` and ``subdir/lose/lose.txt`` from the
manifest.


The ``global-exclude`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; excluding files globally

This works just like ``exclude``, but will remove matching files at all levels
of the directory tree::

    >>> manifest.process_directive('global-exclude l*.txt')

This will remove ``subdir/lose/lose.txt`` from the manifest.


The ``recursive-include`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; including files recursively

This directive takes a directory name (relative to the base) and a set of
patterns. The patterns are used as in ``global-include``, but only for files
under the specified directory::

    >>> manifest.process_directive('recursive-include subdir l*.txt')

This will add ``subdir/lose/lose.txt`` back to the manifest.

The ``recursive-exclude`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; excluding files recursively

This works like ``recursive-include``, but excludes matching files under the
specified directory if they were already added by a previous directive::

    >>> manifest.process_directive('recursive-exclude subdir lose*')

This will remove ``subdir/lose/lose.txt`` from the manifest again.


The ``graft`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; grafting directories

This directive takes the name of a directory (relative to the base) and copies
all the names under it from :attr:`~distlib.manifest.Manifest.allfiles` to :attr:`~distlib.manifest.Manifest.files`.


The ``prune`` directive
~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: Manifest; pruning directories

This directive takes the name of a directory (relative to the base) and removes
all the names under it from :attr:`~distlib.manifest.Manifest.files`.


Next steps
----------

You might find it helpful to look at information about
:ref:`internals` -- or peruse the :ref:`reference`.
