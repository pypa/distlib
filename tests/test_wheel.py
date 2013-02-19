# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals

import codecs
import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

from compat import unittest

from distlib.database import DistributionPath
from distlib.manifest import Manifest
from distlib.wheel import Wheel, PYVER

try:
    with open(os.devnull, 'wb') as junk:
        subprocess.check_call(['pip', '--version'], stdout=junk,
                               stderr=subprocess.STDOUT)
    PIP_AVAILABLE = True
except Exception:
    PIP_AVAILABLE = False

EGG_INFO_RE = re.compile(r'(-py\d\.\d)?\.egg-info', re.I)

def convert_egg_info(libdir, prefix):
    files = os.listdir(libdir)
    ei = list(filter(lambda d: d.endswith('.egg-info'), files))[0]
    olddn = os.path.join(libdir, ei)
    di = EGG_INFO_RE.sub('.dist-info', ei)
    newdn = os.path.join(libdir, di)
    os.rename(olddn, newdn)
    renames = {
        'PKG-INFO': 'METADATA',
    }
    files = os.listdir(newdn)
    for oldfn in files:
        pn = os.path.join(newdn, oldfn)
        if oldfn in renames:
            os.rename(pn, os.path.join(newdn, renames[oldfn]))
        else:
            os.remove(pn)
    manifest = Manifest(os.path.dirname(libdir))
    manifest.findall()
    dp = DistributionPath([libdir])
    dist = next(dp.get_distributions())
    dist.write_installed_files(manifest.allfiles, prefix)

def install_dist(distname, workdir):
    pfx = '--install-option='
    purelib = pfx + '--install-purelib=%s/purelib' % workdir
    platlib = pfx + '--install-platlib=%s/platlib' % workdir
    headers = pfx + '--install-headers=%s/headers' % workdir
    scripts = pfx + '--install-scripts=%s/scripts' % workdir
    data = pfx + '--install-data=%s/data' % workdir
    cmd = ['pip', 'install',
           '--index-url', 'https://pypi.python.org/simple/',
           '--timeout', '3', '--default-timeout', '3',
           purelib, platlib, headers, scripts, data, distname]
    result = {
        'scripts': os.path.join(workdir, 'scripts'),
        'headers': os.path.join(workdir, 'headers'),
        'data': os.path.join(workdir, 'data'),
    }
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout, _ = p.communicate()
    if p.returncode:
        raise ValueError('pip failed to install %s:\n%s' % (distname, stdout))
    for dn in ('purelib', 'platlib'):
        libdir = os.path.join(workdir, dn)
        if os.path.isdir(libdir):
            result[dn] = libdir
            break
    convert_egg_info(libdir, workdir)
    dp = DistributionPath([libdir])
    dist = next(dp.get_distributions())
    md = dist.metadata
    result['name'] = md['Name']
    result['version'] = md['Version']
    return result


class WheelTestCase(unittest.TestCase):

    def test_valid_filename(self):
        attrs = ('name', 'version', 'buildver', 'pyver', 'abi', 'arch')
        cases = (
            ('pkg-1.0.0-cp32.cp33-noabi-noarch.whl',
             ('pkg', '1.0.0', '', ['cp32', 'cp33'], ['noabi'],
              ['noarch'])),
            ('package-1.0.0-cp33-noabi-linux_x86_64.whl',
             ('package', '1.0.0', '', ['cp33'], ['noabi'],
              ['linux_x86_64'])),
            ('test-1.0-1st-py2.py3-none-win32.whl',
             ('test', '1.0', '1st', ['py2', 'py3'], ['none'], ['win32'])),
        )

        for name, values in cases:
            w = Wheel(name)
            self.assertEqual(w.wheel_version, (1, 0))
            self.assertEqual(w.filename, name)
            for attr, value in zip(attrs, values):
                self.assertEqual(getattr(w, attr), value)

    def test_invalid_filename(self):
        names = (
            '',
            'package.whl',
            'package-1.0.0-cp32.cp33.whl',
            'package-1.0.0-cp32.cp33.whl',
            'package-1.0.0-cp32.cp33-noabi.whl',
            'package-1.0.0-cp32.cp33-noabi-noarch.zip',
        )

        for name in names:
            self.assertRaises(ValueError, Wheel, name)

    def test_valid_name(self):
        attrs = ('name', 'version', 'buildver', 'pyver', 'abi', 'arch')
        pyver = PYVER
        cases = (
            ('pkg-1.0.0',
             ('pkg', '1.0.0', '', [PYVER], ['none'], ['any'])),
            ('test-1.0-1st',
             ('test', '1.0', '1st', [PYVER], ['none'], ['any'])),
            (None,
             ('dummy', '0.1', '', [PYVER], ['none'], ['any'])),
        )

        ENDING = '-%s-none-any.whl' % PYVER
        for name, values in cases:
            w = Wheel(name)
            self.assertEqual(w.wheel_version, (1, 0))
            self.assertTrue(w.filename.endswith(ENDING))
            for attr, value in zip(attrs, values):
                self.assertEqual(getattr(w, attr), value)

    def do_build_and_install(self, dist):
        srcdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, srcdir)
        dstdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dstdir)

        paths = install_dist(dist, srcdir)
        paths['prefix'] = srcdir
        w = Wheel()
        w.name = paths.pop('name')
        w.version = paths.pop('version')
        w.dirname = srcdir
        pathname = w.build(paths)
        self.assertTrue(os.path.exists(pathname))

        paths = {'prefix': dstdir}
        for key in ('purelib', 'platlib', 'headers', 'scripts', 'data'):
            paths[key] = os.path.join(dstdir, key)
        w = Wheel(pathname)
        w.install(paths)
        os.remove(pathname)
        sm = Manifest(srcdir)
        sm.findall()
        sfiles = set([os.path.relpath(p, srcdir) for p in sm.allfiles])
        dm = Manifest(dstdir)
        dm.findall()
        dfiles = set([os.path.relpath(p, dstdir) for p in dm.allfiles])
        omitted = sfiles - dfiles
        omitted = omitted.pop()
        endings = os.path.join('.dist-info', 'WHEEL'), '.pyc', '.pyo'
        self.assertTrue(omitted.endswith(endings))

    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_pure(self):
        self.do_build_and_install('sarge == 0.1')

    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_plat(self):
        self.do_build_and_install('hiredis == 0.1.1')

    @unittest.skipIf(sys.version_info[0] == 3, 'The test distribution is not '
                                               '3.x compatible')
    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_data(self):
        self.do_build_and_install('Werkzeug == 0.4')

    @unittest.skipIf(sys.version_info[0] == 3, 'The test distribution is not '
                                               '3.x compatible')
    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_scripts(self):
        self.do_build_and_install('Babel == 0.9.6')

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
