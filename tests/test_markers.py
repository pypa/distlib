# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2023 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Tests for distlib.markers."""
import os
import sys
import platform

from compat import unittest
from support import DistlibTestCase

from distlib.compat import python_implementation
from distlib.markers import interpret
from distlib.util import in_venv


class MarkersTestCase(DistlibTestCase):

    def _check_compatible(self, marker, variable, cases):
        for version, expected in cases:
            self.assertEqual(interpret(marker, {variable: version}), expected, version)

    def test_compatible_major_bound(self):
        self._check_compatible('python_version ~= "3.10"', 'python_version', [
            ('4.0', False),
            ('3.9', False),
            ('3.10', True),
            ('3.11', True),
        ])

    def test_compatible_minor_bound(self):
        self._check_compatible('python_full_version ~= "3.10.1"', 'python_full_version', [
            ('3.11.0', False),
            ('3.10.0', False),
            ('3.10.1', True),
            ('3.10.9', True),
        ])

    def test_compatible_precision(self):
        self._check_compatible('python_full_version ~= "3.10.0.0"', 'python_full_version', [
            ('3.10.1', False),
            ('3.10', True),
            ('3.10.0', True),
            ('3.10.0.1', True),
        ])

    def test_compatible_normalized_release(self):
        self._check_compatible('python_full_version ~= "3.010.1"', 'python_full_version', [
            ('3.11.0', False),
            ('3.10.1', True),
            ('3.010.2', True),
            ('v3.10.2', True),
        ])

    def test_compatible_epoch(self):
        self._check_compatible('implementation_version ~= "1!3.10"', 'implementation_version', [
            ('2!3.11', False),
            ('1!3.9', False),
            ('1!3.10', True),
            ('1!3.11', True),
        ])

    def test_compatible_implementation_version(self):
        self._check_compatible('implementation_version ~= "3.10"', 'implementation_version', [
            ('3.9', False),
            ('4.0', False),
            ('3.10', True),
            ('3.11', True),
        ])

    def test_compatible_reversed_operands(self):
        self._check_compatible('"4.0" ~= python_version', 'python_version', [('3.10', False)])
        self._check_compatible('"3.10.9" ~= python_full_version', 'python_full_version', [
            ('3.10.1', True),
            ('3.11.0', False),
        ])

    def test_compatible_prerelease(self):
        self._check_compatible('python_full_version ~= "3.10rc1"', 'python_full_version', [
            ('4.0rc1', False),
            ('3.10b1', False),
            ('3.10rc1', True),
            ('3.10', True),
            ('3.11rc1', True),
        ])

    def test_other_version_operators_keep_legacy_labels(self):
        context = {'python_full_version': '3.13.0a1+'}
        self.assertTrue(interpret('python_full_version == "3.13.0a1+"', context))
        self.assertTrue(interpret('python_full_version >= "3.12.0"', context))
        self.assertFalse(interpret('python_full_version < "3.12.0"', context))

    def test_interpret(self):
        sys_platform = sys.platform
        version = sys.version.split()[0]
        os_name = os.name
        platform_version = platform.version()
        platform_machine = platform.machine()
        platform_python_implementation = python_implementation()

        self.assertTrue(interpret("sys_platform == '%s'" % sys_platform))
        self.assertTrue(interpret("sys_platform == '%s' and python_full_version == '%s'" % (sys_platform, version)))
        self.assertTrue(interpret("'%s' == sys_platform" % sys_platform))
        self.assertTrue(interpret('os_name == "%s"' % os_name))
        self.assertTrue(
            interpret('platform_version == "%s" and platform_machine == "%s"' % (platform_version, platform_machine)))
        self.assertTrue(interpret('platform_python_implementation == "%s"' % platform_python_implementation))

        self.assertTrue(interpret('platform_in_venv == "%s"' % in_venv()))

        # stuff that need to raise a syntax error
        ops = ('os_name == 2', "'2' == '2'", 'okpjonon', '', 'os_name ==', 'python_version == 2.4')
        for op in ops:
            self.assertRaises(SyntaxError, interpret, op)

        # combined operations
        OP = 'os_name == "%s"' % os_name
        FALSEOP = 'os_name == "buuuu"'
        AND = ' and '
        OR = ' or '
        self.assertTrue(interpret(OP + AND + OP))
        self.assertTrue(interpret(OP + AND + OP + AND + OP))
        self.assertTrue(interpret(OP + OR + OP))
        self.assertTrue(interpret(OP + OR + FALSEOP))
        self.assertTrue(interpret(OP + OR + OP + OR + FALSEOP))
        self.assertTrue(interpret(OP + OR + FALSEOP + OR + FALSEOP))
        self.assertTrue(interpret(FALSEOP + OR + OP))
        self.assertFalse(interpret(FALSEOP + AND + FALSEOP))
        self.assertFalse(interpret(FALSEOP + OR + FALSEOP))

        # other operators
        self.assertTrue(interpret("os_name != 'buuuu'"))
        self.assertTrue(interpret("python_version > '1.0'"))
        self.assertTrue(interpret("python_version < '5.0'"))
        self.assertTrue(interpret("python_version <= '5.0'"))
        self.assertTrue(interpret("python_version >= '1.0'"))
        if sys.version_info < (3, 10):
            self.assertTrue(interpret('python_version < "3.10"'))
            self.assertFalse(interpret('python_version >= "3.10"'))
        if sys.version_info >= (3, 10):
            self.assertFalse(interpret('python_version < "3.10"'))
            self.assertTrue(interpret('python_version >= "3.10"'))
        self.assertTrue(interpret("'%s' in os_name" % os_name))
        self.assertTrue(interpret("'buuuu' not in os_name"))
        self.assertTrue(interpret("'buu' in os_name", {'os_name': 'buuu'}))
        self.assertTrue(interpret("'buuuu' not in os_name and '%s' in os_name" % os_name))

        # normalized version comparison correctness
        self.assertTrue(interpret('python_version > "5.0"', {'python_version': '10.0'}))
        self.assertTrue(interpret('python_version == "5.0"', {'python_version': '5.0'}))
        self.assertTrue(interpret('python_version < "5.0"', {'python_version': '5.0b0'}))
        self.assertTrue(interpret('python_full_version > "5.0"', {'python_full_version': '10.0'}))

        # execution context
        self.assertTrue(interpret('python_version == "0.1"', {'python_version': '0.1'}))

        # parentheses and extra
        if sys.platform != 'win32':
            relop = '!='
        else:
            relop = '=='
        expression = ("(sys_platform %s 'win32' or python_version == '2.4') "
                      "and extra == 'quux'" % relop)
        self.assertTrue(interpret(expression, {'extra': 'quux'}))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
