Change log for ``distlib``
--------------------------

0.3.7 (future)
~~~~~~~~~~~~~~

Released: Not yet.

- markers

    - Use version comparison logic for python_full_version. Thanks to Albert
      Peschar for the patch.

- scripts

    - Fix shebang computation for source builds of Python. Thanks to Eli
      Schwartz for the patch.

Typing stubs for Python 3 were added. _frozen_importlib and 
_frozen_importlib_externals were replaced with importlib.machinery.

0.3.6
~~~~~

Released: 2022-08-26

- scripts

    - Fixed #175: Updated launcher executables to better handle the relationship
      between launcher and child process in the Job API.

0.3.5
~~~~~

Released: 2022-07-14

- database

    - Fixed #170: Corrected implementation of ``get_required_dists()``.

- index

    - Updated coverage pragmas for tests relating to obsolete PyPI APIs.

- locators

    - Changed the default locator configuration.

- metadata

    - Updates in support of PEP 643 / Metadata 2.2.

- scripts

    - Updated launcher executables. Thanks to Michael Bikovitsky for his help with
      the launcher changes.

    - Fixed #164: Improved support for reproducible builds by allowing a fixed
      date/time to be inserted into created .exe files. Thanks to Somber Night for the
      patch.

- util

    - Fixed #161: Updated test case.

- wheel

    - Updated to write archive path of RECORD to RECORD instead of staging path.
      Thanks to Pieter Pas for the patch.

    - Fixed #169: Removed usage of deprecated imp module in favour of importlib.

    - Fixed #172: Compute ABI correctly for Python < 3.8.

In addition to the above, setup.py was replaced by setup.cfg and pyproject.toml.

0.3.4
~~~~~

Released: 2021-12-08

- database

    - Fixed #153: Raise warnings in get_distributions() if bad metadata seen, but keep
      going.

- markers

    - Fixed #154: Determine Python versions correctly for Python >= 3.10.

- scripts

    - Updated launcher executables.

Code relating to support for Python 2.6 was also removed.

0.3.3
~~~~~

Released: 2021-09-22

- compat

    - Fixed #152: Removed splituser() function which wasn't used and is deprecated.

- markers

    - Fixed #149: Handle version comparisons correctly in environment markers.

- scripts

    - Add ARM-64 launchers and support code to use them. Thanks to Niyas Sait and
      Adrian Vladu for their contributions.

- util

    - Fixed #148: Handle a single trailing comma following a version. Thanks to Blazej
      Floch for the report and suggested fix.

- version

    - Fixed #150: Fix incorrect handling of epochs.

- wheel

    - Reverted handling of tags for Python >= 3.10 (use 310 rather than 3_10). This is
      because PEP 641 was rejected.

- tests

    - Made changes relating to implementing CI using GitHub Actions.

0.3.2
~~~~~

Released: 2021-05-29

- locators

    - Fixed #141: removed unused regular expression.

- metadata

    - Fixed #140: allowed "Obsoletes" in more scenarios, to better handle faulty
      metadata already on PyPI.

- resources

    - Fixed #146: added entry for SourcelessFileLoader to the finder registry.

- scripts

    - Made the generation of scripts more configurable:

        - the ``variant_separator`` attribute can be set to determine the separator used
          between a script basename and its X.Y variant. The default value is ``'-'``
          and would result in a final script basename like ``'foo-X.Y'``, whereas
          setting it to ``''`` would result in a final script basename like
          ``'fooX.Y'``.

        - You can also subclass and override the ``get_script_filenames()`` method to
          provide a more customised set of file basenames.

- util

    - Fixed #140: allowed a trailing comma in constraints, to better handle faulty
      metadata already on PyPI.

    - Moved get_platform() logic from distutils to here.

    - Fixed #143: removed normcase() to avoid some problems on Windows.

- wheel

    - Dropped any trailing data when computing the Python tag.

    - Added support for manylinux tags.

    - Changed handling of tags for Python >= 3.10 (use 3_10 rather than 310).

    - Fixed #147: permission bits are now preserved on POSIX when installing from a
      wheel.

- tests

   - Fixed #139: improved handling of errors related to the test PyPI server.

0.3.1
~~~~~

Released: 2020-06-27

The repository has been migrated to Git. References to earlier changesets (commits) in
issue comments, etc. will be invalid.

- scripts

    - Fixed #132: Added documentation to help with relative interpreter paths. Thanks
      to Paul Kienzle for the patch.

    - Fixed #134: Allowed specifying a different target Python version when generating
      scripts.

    - Fixed #135: Exposed the ``enquote_executable`` function previously implemented
      as an internal function.

    - Addressed #138: Improved metadata support for newer metadata versions. Thanks to
      James Tocknell for the patch.

- wheel

    - Changed the output of flags in entry point definitions. Thanks to frostming (明希)
      for the patch.

    - Stopped writing JSON metadata. Only old-style metadata is written now.

0.3.0
~~~~~

Released: 2019-10-29

- database

    - Issue #102 (partial): modules attribute of InstalledDistribution was
      incorrectly computed as a list of bytes, rather than a list of str. This
      has now been corrected.

- locators

    - Updated Locator._get_digest to check PyPI JSON responses for a "digests"
      dictionary before trying "algo_digest" keys. Thanks to Jeffery To for the
      patch.

- scripts

    - Fixed #123: Improved error message if a resource isn't found.

    - Fixed #124: Stopped norm-casing the executable written into shebangs, as
      it doesn't work for some non-ASCII paths.

    - Fixed #125: Updated launchers with versions that correctly report errors
      containing non-ASCII characters. The updated launchers now also support
      relative paths (see http://bit.ly/2JxmOoi for more information).

    - Changed Python version handling to accommodate versions like e.g. 3.10
      (no longer assume a version X.Y where X and Y are single digits).

- util

    - Fixed #127: Allowed hyphens in flags in export specifications.

- wheel

    - Changed Python version handling to accommodate versions like e.g. 3.10
      (no longer assume a version X.Y where X and Y are single digits).


0.2.9
~~~~~

Released: 2019-05-14

- index

    - Updated default PyPI URL to https://pypi.org/pypi.

- locators

    - Updated default PyPI URL to https://pypi.org/pypi.

- metadata

    - Relaxed metadata format checks to ignore 'Provides'.

- scripts

    - Fixed #33, #34: Simplified script template.

    - Updated Windows launchers.

- util

    - Fixed #116: Corrected parsing of credentials from URLs.

- wheel

    - Fixed #115: Relaxed check for '..' in wheel archive entries by not
      checking filename parts, only directory segments.

    - Skip entries in archive entries ending with '/' (directories) when
      verifying or installing.

- docs

    - Updated default PyPI URL to https://pypi.org/pypi.

    - Commented out Disqus comment section.

    - Changed theme configuration.

    - Updated some out-of-date argument lists.

- tests

    - Updated default PyPI URL to https://pypi.org/pypi.

    - Preserved umask on POSIX across a test.


0.2.8
~~~~~

Released: 2018-10-01

- database

    - Fixed #108: Updated metadata scan to look for the METADATA file as well
      as the JSON formats.

- locators

    - Fixed #112: Handled wheel tags and platform-dependent downloads correctly
      in SimpleScrapingLocator.

- metadata

    - Fixed #107: Updated documentation on testing to include information on
      setting PYTHONHASHSEED.

- scripts

    - Fixed #111: Avoided unnecessary newlines in script preambles, which caused
      problems with detecting encoding declarations. Thanks to Wim Glenn for the
      report and patch.

- util

    - Fixed #109: Removed existing files (which might have been symlinks) before
      overwriting.


0.2.7
~~~~~

Released: 2018-04-16

- compat

    - Fixed #105: cache_from_source is now imported from importlib.util where
      available.

- database

    - Addressed #102: InstalledDistributions now have a modules attribute which
      is a list of top-level modules as read from top_level.txt, if that is in
      the distribution info.

- locators

    - Fixed #103: Thanks to Saulius Žemaitaitis for the patch.

- metadata

    - Added support for PEP 566 / Metadata 1.3.

- scripts

    - Fixed #104: Updated launcher binaries. Thanks to Atsushi Odagiri for
      the diagnosis and fix.


0.2.6
~~~~~

Released: 2017-10-28

- compat

    - Fixed #99: Updated to handle a case where sys.getfilesystemencoding()
      returns None.

- database

    - Fixed #97: Eliminated a crash in EggInfoDistribution.list_distinfo_files()
      which was caused by trying to open a non-existent file.

    - Handled a case where an installed distribution didn't have 'Provides:'
      metadata.

- locators

    - Fixed #96: SimpleScrapingLocator no longer fails prematurely when scraping
      links due to invalid versions.

- markers

    - Improved error messages issued when interpreting markers

- scripts

    - Improved the shebangs written into installed scripts when the interpreter
      path is very long or contains spaces (to cater for a limitation in shebang
      line parsing on Linux)

    - Updated launcher binaries.

- tests

    - Numerous test refinements, not detailed further here.


0.2.5
~~~~~

Released: 2017-05-06

- general

    - Changed regular expressions to be compatible with 3.6 as regards escape
      sequences. Thanks to Ville Skyttä for the patch.

    - closed some resource leaks related to XML-RPC proxies.

    - Removed Python 2.6 from the support list.

- locators

    - Made downloadability a factor in scoring URLs for preferences.

- markers

    - Replaced the implementation with code which parses requirements in
      accordance with PEP 508 and evaluates marker expressions according to
      PEP 508.

- util

    - Changed _csv_open to use utf-8 across all platforms on Python 3.x. Thanks
      to Alastair McCormack for the patch.

- wheel

    - Changed to look for metadata in metadata.json as well as pydist.json.

- version

    - Updated requirement parsing in version matchers to use the new
      PEP 508-compliant code.

- tests

    - Numerous test refinements, not detailed further here.


0.2.4
~~~~~

Released: 2016-09-30

- compat

    - Updated to not fail on import if SSL is unavailable.

- index

    - Switch from using gpg in preference to gpg2 for signing. This is
      to avoid gpg2's behaviour of prompting for passwords, which interferes
      with the tests on some machines.

- locators

    - Changed project name comparisons to follow PEP 503. Thanks to Steven
      Arcangeli for the patch.

    - Added errors queue to Locator.

- manifest

    - Changed match logic to work under Python 3.6, due to differences in
      how fnmatch.translate behaves.

- resources

    - Updated finder registry logic to reflect changes in Python 3.6.

- scripts

    - Fixed regular expression in generated script boilerplate.

- util

    - Updated to not fail on import if SSL is unavailable.

    - Added normalize_name for project name comparisons using PEP 503.

- tests

    - Updated to skip certain tests if SSL is unavailable.

    - Numerous other test refinements, not detailed further here.


0.2.3
~~~~~

Released: 2016-04-30

- util

    - Changed get_executable to return Unicode rather than bytes.

    - Fixed #84: Allow + character in output script names.

    - Relaxed too-stringent test looking for application/json in headers.

- wheel

    - sorted the entries in RECORD before writing to file.

- tests

    - Numerous test refinements, not detailed further here.


0.2.2
~~~~~

Released: 2016-01-30

- database

    - Issue #81: Added support for detecting distributions installed by wheel
      versions >= 0.23 (which use metadata.json rather than pydist.json).
      Thanks to Te-jé Rodgers for the patch.

- locators

    - Updated default PyPI URL to https://pypi.python.org/pypi

- metadata

    - Updated to use different formatting for description field for V1.1
      metadata.

    - Corrected "classifier" to "classifiers" in the mapping for V1.0
      metadata.

- scripts

    - Improved support for Jython when quoting executables in output scripts.

- util

    - Issue #77: Made the internal URL used for extended metadata fetches
      configurable via a module attribute.

    - Issue #78: Improved entry point parsing to handle leading spaces in
      ini-format files.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - renamed environment variable SKIP_SLOW to SKIP_ONLINE in tests and
      applied to some more tests.

    - Numerous other test refinements, not detailed further here.


0.2.1
~~~~~

Released: 2015-07-07

- locators

    - Issue #58: Return a Distribution instance or None from ``locate()``.

    - Issue #59: Skipped special keys when looking for versions.

    - Improved behaviour of PyPIJSONLocator to be analogous to that of other
      locators.

- resource

    - Added resource iterator functionality.

- scripts

    - Issue #71: Updated launchers to decode shebangs using UTF-8. This allows
      non-ASCII pathnames to be correctly handled.

    - Ensured that the executable written to shebangs is normcased.

    - Changed ScriptMaker to work better under Jython.

- util

    - Changed the mode setting method to work better under Jython.

    - Changed get_executable() to return a normcased value.

- wheel

    - Handled multiple-architecture wheel filenames correctly.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.


0.2.0
~~~~~

Released: 2014-12-17

- compat

    - Updated ``match_hostname`` to use the latest Python implementation.

- database

    - Added `download_urls` and `digests` attributes to ``Distribution``.

- locators

    - Issue #48: Fixed the problem of adding a tuple containing a set
      (unhashable) to a set, by wrapping with frozenset().

    - Issue #55: Return multiple download URLs for distributions, if
      available.

- manifest

    - Issue #57: Remove unhelpful warnings about pattern matches.

- metadata

    - Updated to reflect changes to PEP 426.

- resources

    - Issue #50: The type of the path needs to be preserved on 2.x.

- scripts

    - Updated (including launchers) to support providing arguments to
      interpreters in shebang lines.

    - The launcher sources are now included in the repository and the
      source distribution (they are to be found in the PC directory).

    - Added frames support in IronPython (patch by Pawel Jasinski).

    - Issue #51: encode shebang executable using utf-8 rather than fsencode.

- util

    - Removed reference to __PYVENV_LAUNCHER__ when determining executable
      for scripts (relevant only on macOS).

    - Updated to support changes to PEP 426.

- version

    - Updated to reflect changes to versioning proposed in PEP 440.

- wheel

    - Updated build() code to respect interpreter arguments in prebuilt
      scripts.

    - Updated to support changes to PEP 426 / PEP 440.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.


0.1.9
~~~~~

Released: 2014-05-19

- index

    - Added ``keystore`` keyword argument to signing and verification
      APIs.

- scripts

    - Issue #47: Updated binary launchers to fix double-quoting bug where
      script executable paths have spaces.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.


0.1.8
~~~~~

Released: 2014-03-18

- index

    - Improved thread-safety in SimpleScrapingLocator (issue #45).

    - Replaced absolute imports with relative ones.

    - Added ``search`` method to ``PackageIndex``.

- locators

    - Improved thread-safety in ``SimpleScrapingLocator`` (issue #45).

- metadata

    - Fixed bug in add_requirements implementation.

- resources

    - The ``Cache`` class was refactored into ``distlib.util.Cache``
      and ``distlib.resources.ResourceCache`` classes.

- scripts

    - Implement quoting for executables with spaces in them.

- util

    - Gained the ``Cache`` class, which is also used in ``distlib.wheel``.

- version

    - Allowed versions with a single numeric component and a local
      version component.

    - Adjusted pre-release computation for legacy versions to be the same as
      the logic in the setuptools documentation.

- wheel

    - Added ``verify``, ``update``, ``is_compatible`` and ``is_mountable``
      methods to the ``Wheel`` class.

    - Converted local version separators from '-' to '_' and back.

    - If SOABI not available, used Py_DEBUG, Py_UNICODE_SIZE and
      WITH_PYMALLOC to derive the ABI.

    - Added "exists" property to Wheel instances.

    - Factored out RECORD writing and zip building to separate methods.

    - Provided the ability to determine the location where extensions are
      extracted, by using the ``distlib.util.Cache`` class.

    - Avoided using ``pydist.json`` in 1.0 wheels (``bdist_wheel`` writes a
      non-conforming ``pydist.json``.)

    - Improved computation of compatible tags on macOS, and made COMPATIBLE_TAGS
      a set.

- _backport/sysconfig

    - Replaced an absolute import with a relative one.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.


0.1.7
~~~~~

Released: 2014-01-16

- metadata

    - Added some more fields to the metadata for the index.

- resources

    - Use native literal string in cache path.

    - Issue #40: Now does path adjustments differently for files and zips.

- scripts

    - Improved checking for venvs when generating scripts.

- util

    - Issue #39: Fall back to temporary directory for cache if home directory
      unavailable.

- wheel

    - Use native literal string in cache path.

0.1.6
~~~~~

Released: 2013-12-31

- scripts

    - Updated binary launchers because the wrong variant was shipped
      with the previous release.

- version

    - Added support for local component in PEP 440 versions.

- tests

    - Numerous test refinements, not detailed further here.


0.1.5
~~~~~

Released: 2013-12-15

- compat

    - Changed source of import for unescape in Python >= 3.4.

- index

    - Used dummy_threading when threading isn't available.

    - Used https for default index.

- locators

    - Used dummy_threading when threading isn't available.

- scripts

    - Defaulted to setting script mode bits on POSIX.

    - Use uncompressed executable launchers, since some anti-virus
      products raise false positive errors.

- util

    - Used dummy_threading when threading isn't available.

- docs

    - Updated out-of-date links in overview.

- tests

    - Used dummy_threading when threading isn't available.


0.1.4
~~~~~

Released: 2013-10-31

- scripts

    - Updated the logic for finding the distlib package using a relative,
      rather than absolute method. This fixes a problem for pip, where
      distlib is kept in the pip.vendor.distlib package.

- _backport/sysconfig

    - The analogous change to that made for scripts, described above.

0.1.3
~~~~~

Released: 2013-10-18

- database

    - Added support for PEP 426 JSON metadata (pydist.json).

    - Generalised digests to support e.g. SHA256.

    - Fixed a bug in parsing legacy metadata from .egg directories.

    - Removed duplicated code relating to parsing "provides" fields.

- index

    - Changes relating to support for PEP 426 JSON metadata (pydist.json).

- locators

    - Changes relating to support for PEP 426 JSON metadata (pydist.json).

    - Fixed a bug in scoring download URLs for preference when multiple URLs
      are available.

    - The legacy scheme is used for the default locator.

    - Made changes relating to parsing "provides" fields.

    - Generalised digests to support e.g. SHA256.

    - If no release version is found for a requirement, prereleases are
      now considered even if not explicitly requested.

- markers

    - Added support for markers as specified in PEP 426.

- metadata

    - Added support for PEP 426 JSON metadata (pydist.json). The old
      metadata class is renamed to LegacyMetadata, and the (new)
      Metadata class wraps the JSON format (and also the legacy format,
      through LegacyMetadata).

    - Removed code which was only used if docutils was installed. This code
      implemented validation of .rst descriptions, which is not done in
      distlib.

- scripts

    - Updated the logic for writing executable files to deal as best we can
      with files which are already in use and hence cannot be deleted on
      Windows.

    - Changed the script generation when launchers are used to write a
      single executable which wraps a script (whether pre-built or generated)
      and includes a manifest to avoid UAC prompts on Windows.

    - Changed the interface for script generation options: the ``make`` and
      ``make_multiple`` methods of ``ScriptMaker`` now take an optional
      ``options`` dictionary.

- util

    - Added extract_by_key() to copy selected keys from one dict to another.

    - Added parse_name_and_version() for use in parsing "provides" fields.

    - Made split_filename more flexible.

- version

    - Added support for PEP 440 version matching.

    - Removed AdaptiveVersion, AdaptiveMatcher etc. as they don't add
      sufficient value to justify keeping them in.

- wheel

    - Added wheel_version kwarg to Wheel.build API.

    - Changed Wheel.install API (after consultation on distutils-sig).

    - Added support for PEP 426 JSON metadata (pydist.json).

    - Added lib_only flag to install() method.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.


0.1.2
~~~~~

Released: 2013-04-30

- compat

    - Added BaseConfigurator backport for 2.6.

- database

    - Return RECORD path from write_installed_files (or None if dry_run).

    - Explicitly return None from write_shared_locations if dry run.

- metadata

    - Added missing condition in :meth:`~distlib.metadata.Metadata.todict`.

- scripts

    - Add variants and clobber flag for generation of foo/fooX/foo-X.Y.

    - Added .exe manifests for Windows.

- util

    - Regularised recording of written files.

    - Added Configurator.

- version

    - Tidyups, most suggested by Donald Stufft: Made key functions private,
      removed _Common class, removed checking for huge version numbers, made
      UnsupportedVersionError a ValueError.

- wheel

    - Replaced absolute import with relative.

    - Handle None return from write_shared_locations correctly.

    - Fixed bug in Mounter for extension modules not in sub-packages.

    - Made dylib-cache Python version-specific.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.

- other

    - Corrected setup.py to ensure that sysconfig.cfg is included.


0.1.1
~~~~~

Released: 2013-03-22

- database

    - Updated requirements logic to use extras and environment markers.

    - Made it easier to subclass Distribution and EggInfoDistribution.

- locators

    - Added method to clear locator caches.

    - Added the ability to skip pre-releases.

- manifest

    - Fixed bug which caused side-effect when sorting a manifest.

- metadata

    - Updated to handle most 2.0 fields, though PEP 426 is still a draft.

    - Added the option to skip unset fields when writing.

- resources

    - Made separate subclasses ResourceBase, Resource and ResourceContainer
      from Resource. Thanks to Thomas Kluyver for the suggestion and patch.

- scripts

    - Fixed bug which prevented writing shebang lines correctly on Windows.

- util

    - Made get_cache_base more useful by parameterising the suffix to use.

    - Fixed a bug when reading CSV streams from .zip files under 3.x.

- version

    - Added is_prerelease property to versions.

    - Moved to PEP 426 version formats and sorting.

- wheel

    - Fixed CSV stream reading under 3.x and handled UTF-8 in zip entries
      correctly.

    - Added metadata and info properties, and updated the install method to
      return the installed distribution.

    - Added mount/unmount functionality.

    - Removed compatible_tags() function in favour of COMPATIBLE_TAGS
      attribute.

- docs

    - Numerous documentation updates, not detailed further here.

- tests

    - Numerous test refinements, not detailed further here.


0.1.0
~~~~~

Released: 2013-03-02

- Initial release.
