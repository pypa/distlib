# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import sys

_ver = sys.version_info[:2]

from test_database import (DataFilesTestCase, TestDatabase, TestDistribution,
                           TestEggInfoDistribution, DepGraphTestCase)
from test_index import PackageIndexTestCase
from test_locators import LocatorTestCase
from test_manifest import ManifestTestCase
from test_markers import MarkersTestCase
from test_metadata import MetadataTestCase, LegacyMetadataTestCase
from test_resources import (ZipResourceTestCase, FileResourceTestCase,
                            CacheTestCase)
from test_scripts import ScriptTestCase
from test_version import (VersionTestCase, CompatibilityTestCase,
                          LegacyVersionTestCase, SemanticVersionTestCase)
from test_wheel import WheelTestCase

if _ver == (2, 6):
    from test_shutil import TestCopyFile, TestMove, TestShutil
    from test_sysconfig import TestSysConfig, MakefileTests
from test_util import (UtilTestCase, ProgressTestCase, FileOpsTestCase,
                       GlobTestCase)
