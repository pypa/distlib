# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""Tests for distutils2.depgraph """
import logging
import os
import re
import sys

from compat import unittest

from distlib.compat import StringIO
from distlib.database import DistributionPath
from distlib.depgraph import (make_graph, get_dependent_dists,
                              get_required_dists, main)

from support import LoggingCatcher, requires_zlib

logger = logging.getLogger(__name__)

class DepGraphTestCase(LoggingCatcher,
                       unittest.TestCase):

    DISTROS_DIST = ('choxie', 'grammar', 'towel-stuff')
    DISTROS_EGG = ('bacon', 'banana', 'strawberry', 'cheese')
    BAD_EGGS = ('nut',)

    EDGE = re.compile(
           r'"(?P<from>.*)" -> "(?P<to>.*)" \[label="(?P<label>.*)"\]')

    def checkLists(self, l1, l2):
        """ Compare two lists without taking the order into consideration """
        self.assertListEqual(sorted(l1), sorted(l2))

    def setUp(self):
        super(DepGraphTestCase, self).setUp()
        path = os.path.join(os.path.dirname(__file__), 'fake_dists')
        path = os.path.abspath(path)
        sys.path.insert(0, path)
        self.addCleanup(sys.path.remove, path)

    def get_dists(self, names, include_egg=False):
        dists = []
        d = DistributionPath(include_egg=include_egg)
        for name in names:
            dist = d.get_distribution(name)
            self.assertNotEqual(dist, None)
            dists.append(dist)
        return dists

    def test_make_graph(self):
        dists = self.get_dists(self.DISTROS_DIST)

        choxie, grammar, towel = dists

        graph = make_graph(dists)

        deps = [(x.name, y) for x, y in graph.adjacency_list[choxie]]
        self.checkLists([('towel-stuff', 'towel-stuff (0.1)')], deps)
        self.assertIn(choxie, graph.reverse_list[towel])
        self.checkLists(graph.missing[choxie], ['nut'])

        deps = [(x.name, y) for x, y in graph.adjacency_list[grammar]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[grammar], ['truffles (>=1.2)'])

        deps = [(x.name, y) for x, y in graph.adjacency_list[towel]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[towel], ['bacon (<=0.2)'])

    @requires_zlib
    def test_make_graph_egg(self):
        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        choxie, grammar, towel, bacon, banana, strawberry, cheese = dists

        graph = make_graph(dists)

        deps = [(x.name, y) for x, y in graph.adjacency_list[choxie]]
        self.checkLists([('towel-stuff', 'towel-stuff (0.1)')], deps)
        self.assertIn(choxie, graph.reverse_list[towel])
        self.checkLists(graph.missing[choxie], ['nut'])

        deps = [(x.name, y) for x, y in graph.adjacency_list[grammar]]
        self.checkLists([('bacon', 'truffles (>=1.2)')], deps)
        self.checkLists(graph.missing[grammar], [])
        self.assertIn(grammar, graph.reverse_list[bacon])

        deps = [(x.name, y) for x, y in graph.adjacency_list[towel]]
        self.checkLists([('bacon', 'bacon (<=0.2)')], deps)
        self.checkLists(graph.missing[towel], [])
        self.assertIn(towel, graph.reverse_list[bacon])

        deps = [(x.name, y) for x, y in graph.adjacency_list[bacon]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[bacon], [])

        deps = [(x.name, y) for x, y in graph.adjacency_list[banana]]
        self.checkLists([('strawberry', 'strawberry (>=0.5)')], deps)
        self.checkLists(graph.missing[banana], [])
        self.assertIn(banana, graph.reverse_list[strawberry])

        deps = [(x.name, y) for x, y in graph.adjacency_list[strawberry]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[strawberry], [])

        deps = [(x.name, y) for x, y in graph.adjacency_list[cheese]]
        self.checkLists([], deps)
        self.checkLists(graph.missing[cheese], [])

    def test_dependent_dists(self):
        dists = self.get_dists(self.DISTROS_DIST)

        choxie, grammar, towel = dists

        deps = [d.name for d in get_dependent_dists(dists, choxie)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, grammar)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, towel)]
        self.checkLists(['choxie'], deps)

    def test_required_dists(self):
        dists = self.get_dists(self.DISTROS_DIST +
                               ('truffles', 'bacon', 'banana',
                                'coconuts-aster'), True)

        choxie, grammar, towel, truffles, bacon, banana, coco = dists

        reqs = [d.name for d in get_required_dists(dists, choxie)]
        self.checkLists(['bacon', 'towel-stuff'], reqs)

        reqs = [d.name for d in get_required_dists(dists, grammar)]
        self.checkLists(['truffles'], reqs)

        reqs = [d.name for d in get_required_dists(dists, banana)]
        self.checkLists(['coconuts-aster'], reqs)

        reqs = [d.name for d in get_required_dists(dists, towel)]
        self.checkLists(['bacon'], reqs)

    @requires_zlib
    def test_dependent_dists_egg(self):
        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        choxie, grammar, towel, bacon, banana, strawberry, cheese = dists

        deps = [d.name for d in get_dependent_dists(dists, choxie)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, grammar)]
        self.checkLists([], deps)

        deps = [d.name for d in get_dependent_dists(dists, towel)]
        self.checkLists(['choxie'], deps)

        deps = [d.name for d in get_dependent_dists(dists, bacon)]
        self.checkLists(['choxie', 'towel-stuff', 'grammar'], deps)

        deps = [d.name for d in get_dependent_dists(dists, strawberry)]
        self.checkLists(['banana'], deps)

        deps = [d.name for d in get_dependent_dists(dists, cheese)]
        self.checkLists([], deps)

    @requires_zlib
    def test_graph_to_dot(self):
        expected = (
            ('towel-stuff', 'bacon', 'bacon (<=0.2)'),
            ('grammar', 'bacon', 'truffles (>=1.2)'),
            ('choxie', 'towel-stuff', 'towel-stuff (0.1)'),
            ('banana', 'strawberry', 'strawberry (>=0.5)'),
        )

        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        graph = make_graph(dists)
        buf = StringIO()
        graph.to_dot(buf)
        buf.seek(0)
        matches = []
        lines = buf.readlines()
        for line in lines[1:-1]:  # skip the first and the last lines
            if line[-1] == '\n':
                line = line[:-1]
            match = self.EDGE.match(line.strip())
            self.assertIsNot(match, None)
            matches.append(match.groups())

        self.checkLists(matches, expected)

    @requires_zlib
    def test_graph_disconnected_to_dot(self):
        dependencies_expected = (
            ('towel-stuff', 'bacon', 'bacon (<=0.2)'),
            ('grammar', 'bacon', 'truffles (>=1.2)'),
            ('choxie', 'towel-stuff', 'towel-stuff (0.1)'),
            ('banana', 'strawberry', 'strawberry (>=0.5)'),
        )
        disconnected_expected = ('cheese', 'bacon', 'strawberry')

        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG, True)

        graph = make_graph(dists)
        buf = StringIO()
        graph.to_dot(buf, skip_disconnected=False)
        buf.seek(0)
        lines = buf.readlines()

        dependencies_lines = []
        disconnected_lines = []

        # First sort output lines into dependencies and disconnected lines.
        # We also skip the attribute lines, and don't include the "{" and "}"
        # lines.
        disconnected_active = False
        for line in lines[1:-1]:  # Skip first and last line
            if line.startswith('subgraph disconnected'):
                disconnected_active = True
                continue
            if line.startswith('}') and disconnected_active:
                disconnected_active = False
                continue

            if disconnected_active:
                # Skip the 'label = "Disconnected"', etc. attribute lines.
                if ' = ' not in line:
                    disconnected_lines.append(line)
            else:
                dependencies_lines.append(line)

        dependencies_matches = []
        for line in dependencies_lines:
            if line[-1] == '\n':
                line = line[:-1]
            match = self.EDGE.match(line.strip())
            self.assertIsNot(match, None)
            dependencies_matches.append(match.groups())

        disconnected_matches = []
        for line in disconnected_lines:
            if line[-1] == '\n':
                line = line[:-1]
            line = line.strip('"')
            disconnected_matches.append(line)

        self.checkLists(dependencies_matches, dependencies_expected)
        self.checkLists(disconnected_matches, disconnected_expected)

    @requires_zlib
    def test_graph_bad_version_to_dot(self):
        expected = (
            ('towel-stuff', 'bacon', 'bacon (<=0.2)'),
            ('grammar', 'bacon', 'truffles (>=1.2)'),
            ('choxie', 'towel-stuff', 'towel-stuff (0.1)'),
            ('banana', 'strawberry', 'strawberry (>=0.5)'),
        )

        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG +
                               self.BAD_EGGS, True)

        graph = make_graph(dists)
        buf = StringIO()
        graph.to_dot(buf)
        buf.seek(0)
        matches = []
        lines = buf.readlines()
        for line in lines[1:-1]:  # skip the first and the last lines
            if line[-1] == '\n':
                line = line[:-1]
            match = self.EDGE.match(line.strip())
            self.assertIsNot(match, None)
            matches.append(match.groups())

        self.checkLists(matches, expected)

    @requires_zlib
    def test_repr(self):
        dists = self.get_dists(self.DISTROS_DIST + self.DISTROS_EGG +
                               self.BAD_EGGS, True)

        graph = make_graph(dists)
        self.assertTrue(repr(graph))

    @requires_zlib
    def test_main(self):
        tempout = StringIO()
        old = sys.stdout
        sys.stdout = tempout
        oldargv = sys.argv[:]
        sys.argv[:] = ['script.py']
        try:
            try:
                main()
            except SystemExit:
                pass
        finally:
            sys.stdout = old
            sys.argv[:] = oldargv

        # checks what main did XXX could do more here
        tempout.seek(0)
        res = tempout.read()
        self.assertIn('towel', res)


def test_suite():
    return unittest.makeSuite(DepGraphTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
