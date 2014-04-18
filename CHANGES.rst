Change log for ``distlib``
--------------------------


0.1.9 (future)
~~~~~~~~~~~~~~

Released: Not yet.

- index

    - Added ``keystore`` keyword argument to signing and verification
      APIs.

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

    - Improved computation of compatible tags on OS X, and made COMPATIBLE_TAGS
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

    - Added missing condition in :meth:`todict`.

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

    - Made get_cache_base more useful by parametrising the suffix to use.

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
