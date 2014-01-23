# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Tests for distlib.markers."""
import os
import sys
import platform

from compat import unittest

from distlib.compat import python_implementation
from distlib.markers import interpret
from distlib.util import in_venv

class MarkersTestCase(unittest.TestCase):

    def test_interpret(self):
        sys_platform = sys.platform
        version = sys.version.split()[0]
        os_name = os.name
        platform_version = platform.version()
        platform_machine = platform.machine()
        platform_python_implementation = python_implementation()

        self.assertTrue(interpret("sys_platform == '%s'" % sys_platform))
        self.assertTrue(interpret(
            "sys_platform == '%s' and python_full_version == '%s'" %
            (sys_platform, version)))
        self.assertTrue(interpret("'%s' == sys_platform" % sys_platform))
        self.assertTrue(interpret('os_name == "%s"' % os_name))
        self.assertTrue(interpret(
            'platform_version == "%s" and platform_machine == "%s"' %
            (platform_version, platform_machine)))
        self.assertTrue(interpret('platform_python_implementation == "%s"' %
            platform_python_implementation))

        self.assertTrue(interpret('platform_in_venv == "%s"' % in_venv()))

        # stuff that need to raise a syntax error
        ops = ('os_name == 2', "'2' == '2'",
               'okpjonon', '', 'os_name ==', 'python_version == 2.4')
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
        self.assertTrue(interpret("'%s' in os_name" % os_name))
        self.assertTrue(interpret("'buuuu' not in os_name"))
        self.assertTrue(interpret("'buu' in os_name", {'os_name': 'buuu'}))
        self.assertTrue(interpret(
            "'buuuu' not in os_name and '%s' in os_name" % os_name))

        # execution context
        self.assertTrue(interpret('python_version == "0.1"',
                                  {'python_version': '0.1'}))

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
