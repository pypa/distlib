# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import sys

_ver = sys.version_info[:2]

from test_version import (VersionTestCase, CompatibilityTestCase,
                          LegacyVersionTestCase, SemanticVersionTestCase,
                          AdaptiveVersionTestCase)
from test_markers import MarkersTestCase
from test_metadata import MetadataTestCase
from test_database import (DataFilesTestCase, TestDatabase, TestDistribution,
                           TestEggInfoDistribution, DepGraphTestCase)
from test_resources import (ZipResourceTestCase, FileResourceTestCase,
                            CacheTestCase)
from test_scripts import ScriptTestCase
if _ver == (2, 6):
    from test_shutil import TestCopyFile, TestMove, TestShutil
    from test_sysconfig import TestSysConfig, MakefileTests
from test_util import (UtilTestCase, ProgressTestCase, FileOpsTestCase,
                       GlobTestCase)
from test_pypi_dist import TestDistInfo, TestReleaseInfo, TestReleasesList
from test_pypi_server import PyPIServerTest
from test_pypi_simple import SimpleCrawlerTestCase
from test_pypi_xmlrpc import TestXMLRPCClient
from test_locators import LocatorTestCase
