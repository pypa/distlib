# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2017 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""
Parser for the environment markers micro-language defined in PEP 508.
"""

# Note: In PEP 345, the micro-language was Python compatible, so the ast
# module could be used to parse it. However, PEP 508 introduced operators such
# as ~= and === which aren't in Python, necessitating a different approach.

import os
import sys
import platform
import re

from .compat import python_implementation, urlparse, string_types
from .util import in_venv

__all__ = ['interpret']

IDENTIFIER = re.compile(r'^([\w\.-]+)\s*')
VERSION_IDENTIFIER = re.compile(r'^([\w\.*+-]+)\s*')
COMPARE_OP = re.compile(r'^(<=?|>=?|={2,3}|[~!]=)\s*')
MARKER_OP = re.compile(r'^((<=?)|(>=?)|={2,3}|[~!]=|in|not\s+in)\s*')
OR = re.compile(r'^or\b\s*')
AND = re.compile(r'^and\b\s*')
NONSPACE = re.compile(r'(\S+)\s*')
STRING_CHUNK = re.compile(r'([\s\w\.{}()*+#:;,/?!~`@$%^&=|<>\[\]-]+)')

def _is_literal(o):
    if not isinstance(o, string_types) or not o:
        return False
    return o[0] in '\'"'

class RequirementParser(object):
    """
    This class is used to parse requirements and also to evaluate markers.
    """

    def parse(self, req):
        """
        Parse a requirement passed in as a string. Return a dictionary
        whose elements contain the various parts of the requirement.
        """
        m = IDENTIFIER.match(req)
        if not m:
            raise SyntaxError('name expected: %s' % req)
        distname = m.groups()[0]
        req = req[m.end():]
        extras = markexpr = versions = uri = None
        if req and req[0] == '[':
            i = req.find(']', 1)
            if i < 0:
                raise SyntaxError('unterminated extra: %s' % req)
            s = req[1:i]
            req = req[i + 1:].lstrip()
            extras = []
            while s:
                m = IDENTIFIER.match(s)
                if not m:
                    raise SyntaxError('malformed extra: %s' % s)
                extras.append(m.groups()[0])
                s = s[m.end():]
                if not s:
                    break
                if s[0] != ',':
                    raise SyntaxError('comma expected in extras: %s' % s)
                s = s[1:].lstrip()
        if req:
            if req[0] == '@':
                # it's a URI
                req = req[1:].lstrip()
                m = NONSPACE.match(req)
                if not m:
                    raise SyntaxError('invalid URI: %s' % req)
                uri = m.groups()[0]
                t = urlparse(uri)
                # there are issues with Python and URL parsing, so this test
                # is a bit crude. See bpo-20271, bpo-23505. Python doesn't
                # always parse invalid URLs correctly - it should raise
                # exceptions for malformed URLs
                if not (t.scheme and t.netloc):
                    raise SyntaxError('Invalid URL: %s' % uri)
                req = req[m.end():].lstrip()
            else:

                def get_versions(req):
                    m = COMPARE_OP.match(req)
                    versions = None
                    if m:
                        versions = []
                        while True:
                            op = m.groups()[0]
                            req = req[m.end():]
                            m = VERSION_IDENTIFIER.match(req)
                            if not m:
                                raise SyntaxError('invalid version: %s' % req)
                            v = m.groups()[0]
                            versions.append((op, v))
                            req = req[m.end():]
                            if not req or req[0] != ',':
                                break
                            req = req[1:].lstrip()
                    return versions, req

                if req[0] != '(':
                    versions, req = get_versions(req)
                else:
                    i = req.find(')', 1)
                    if i < 0:
                        raise SyntaxError('unterminated parenthesis: %s' % req)
                    s = req[1:i]
                    req = req[i + 1:].lstrip()
                    versions, _ = get_versions(s)
        if req:
            if req[0] != ';':
                raise SyntaxError('invalid marker: %s' % req)
            req = req[1:].lstrip()

            def marker_var(req):
                # either identifier, or literal string
                m = IDENTIFIER.match(req)
                if m:
                    result = m.groups()[0]
                    req = req[m.end():]
                elif not req:
                    raise SyntaxError('unexpected end of input')
                else:
                    q = req[0]
                    if q not in '\'"':
                        raise SyntaxError('invalid expression: %s' % req)
                    oq = '\'"'.replace(q, '')
                    req = req[1:]
                    parts = [q]
                    while req:
                        # either a string chunk, or oq, or q to terminate
                        if req[0] == q:
                            break
                        elif req[0] == oq:
                            parts.append(oq)
                            req = req[1:]
                        else:
                            m = STRING_CHUNK.match(req)
                            if not m:
                                raise SyntaxError('error in string literal: %s' % req)
                            parts.append(m.groups()[0])
                            req = req[m.end():]
                    else:
                        s = ''.join(parts)
                        raise SyntaxError('unterminated string: %s' % s)
                    parts.append(q)
                    result = ''.join(parts)
                    req = req[1:].lstrip() # skip past closing quote
                return result, req

            def marker_expr(req):
                if req and req[0] == '(':
                    result, req = marker(req[1:].lstrip())
                    if req[0] != ')':
                        raise SyntaxError('unterminated parenthesis: %s' % req)
                    req = req[1:].lstrip()
                else:
                    lhs, req = marker_var(req)
                    while req:
                        m = MARKER_OP.match(req)
                        if not m:
                            break
                        op = m.groups()[0]
                        req = req[m.end():]
                        rhs, req = marker_var(req)
                        lhs = {'op': op, 'lhs': lhs, 'rhs': rhs}
                    result = lhs
                return result, req

            def marker_and(req):
                lhs, req = marker_expr(req)
                while req:
                    m = AND.match(req)
                    if not m:
                        break
                    req = req[m.end():]
                    rhs, req = marker_expr(req)
                    lhs = {'op': 'and', 'lhs': lhs, 'rhs': rhs}
                return lhs, req

            def marker(req):
                lhs, req = marker_and(req)
                while req:
                    m = OR.match(req)
                    if not m:
                        break
                    req = req[m.end():]
                    rhs, req = marker_and(req)
                    lhs = {'op': 'or', 'lhs': lhs, 'rhs': rhs}
                return lhs, req

            # import pdb; pdb.set_trace()
            markexpr, req = marker(req)

        result = {'name': distname}
        if extras:
            result['extras'] = extras
        if versions:
            result['versions'] = versions
        if markexpr:
            result['marker'] = markexpr
        if uri:
            result['uri'] = uri
        if req and req[0] != '#':
            raise SyntaxError('Unexpected trailing data: %s' % req)
        return result

    operations = {
        '==': lambda x, y: x == y,
        '!=': lambda x, y: x != y,
        '<':  lambda x, y: x < y,
        '<=':  lambda x, y: x <= y,
        '>':  lambda x, y: x > y,
        '>=':  lambda x, y: x >= y,
        'and': lambda x, y: x and y,
        'or': lambda x, y: x or y,
        'in': lambda x, y: x in y,
        'not in': lambda x, y: x not in y,
    }

    def evaluate(self, expr, context):
        """
        Evaluate a marker expression returned by the :meth:`parse`
        method in the specified context.
        """
        if isinstance(expr, string_types):
            if expr[0] in '\'"':
                result = expr[1:-1]
            else:
                if expr not in context:
                    raise SyntaxError('unknown variable: %s' % expr)
                result = context[expr]
        else:
            assert isinstance(expr, dict)
            op = expr['op']
            if op not in self.operations:
                raise NotImplementedError('op not implemented: %s' % op)
            elhs = expr['lhs']
            erhs = expr['rhs']
            if _is_literal(expr['lhs']) and _is_literal(expr['rhs']):
                raise SyntaxError('invalid comparison: %s %s %s' % (elhs, op, erhs))

            lhs = self.evaluate(elhs, context)
            rhs = self.evaluate(erhs, context)
            result = self.operations[op](lhs, rhs)
        return result

def default_context():
    def format_full_version(info):
        version = '%s.%s.%s' % (info.major, info.minor, info.micro)
        kind = info.releaselevel
        if kind != 'final':
            version += kind[0] + str(info.serial)
        return version

    if hasattr(sys, 'implementation'):
        implementation_version = format_full_version(sys.implementation.version)
        implementation_name = sys.implementation.name
    else:
        implementation_version = '0'
        implementation_name = ''

    result = {
        'implementation_name': implementation_name,
        'implementation_version': implementation_version,
        'os_name': os.name,
        'platform_machine': platform.machine(),
        'platform_python_implementation': platform.python_implementation(),
        'platform_release': platform.release(),
        'platform_system': platform.system(),
        'platform_version': platform.version(),
        'platform_in_venv': str(in_venv()),
        'python_full_version': platform.python_version(),
        'python_version': platform.python_version()[:3],
        'sys_platform': sys.platform,
    }
    return result

DEFAULT_CONTEXT = default_context()
del default_context

parser = RequirementParser()

def interpret(marker, execution_context=None):
    """
    Interpret a marker and return a result depending on environment.

    :param marker: The marker to interpret.
    :type marker: str
    :param execution_context: The context used for name lookup.
    :type execution_context: mapping
    """
    s = 'dummy ; %s' % marker.strip()
    result = parser.parse(s)
    context = dict(DEFAULT_CONTEXT)
    if execution_context:
        context.update(execution_context)
    return parser.evaluate(result['marker'], context)
