Change log for ``distlib``
--------------------------

0.1.3
~~~~~

Released: Not yet.


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
