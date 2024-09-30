# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
from __future__ import unicode_literals

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

from compat import unittest
from support import DistlibTestCase

from distlib import DistlibException
from distlib.compat import ZipFile, sysconfig, fsencode
from distlib.database import DistributionPath
from distlib.manifest import Manifest
from distlib.metadata import Metadata, METADATA_FILENAME, LEGACY_METADATA_FILENAME
from distlib.scripts import ScriptMaker
from distlib.util import get_executable
from distlib.wheel import (Wheel, PYVER, IMPVER, ARCH, ABI, COMPATIBLE_TAGS, IMP_PREFIX, VER_SUFFIX,
                           is_compatible, _get_glibc_version)

try:
    with open(os.devnull, 'wb') as junk:
        subprocess.check_call(['pip', '--version'], stdout=junk, stderr=subprocess.STDOUT)
    PIP_AVAILABLE = True
except Exception:
    PIP_AVAILABLE = False

HERE = os.path.abspath(os.path.dirname(__file__))

EGG_INFO_RE = re.compile(r'(-py\d\.\d)?\.egg-info', re.I)


def pip_version():
    result = None
    fd, fn = tempfile.mkstemp(prefix='distlib-test-', suffix='.txt')
    try:
        os.close(fd)
        with open(fn, 'wb') as out:
            subprocess.check_call(['pip', '--version'], stdout=out, stderr=subprocess.STDOUT)
        with io.open(fn, encoding='utf-8') as f:
            data = f.read().split()
        assert data[0] == 'pip'
        parts = data[1].split('.')
        result = []
        for p in parts:
            if p.isdigit():
                result.append(int(p))
            else:
                result.append(p)
        result = tuple(result)
    finally:
        os.remove(fn)
    return result


def convert_egg_info(libdir, prefix):
    files = os.listdir(libdir)
    ei = list(filter(lambda d: d.endswith('.egg-info'), files))[0]
    olddn = os.path.join(libdir, ei)
    di = EGG_INFO_RE.sub('.dist-info', ei)
    newdn = os.path.join(libdir, di)
    os.rename(olddn, newdn)
    files = os.listdir(newdn)
    for oldfn in files:
        pn = os.path.join(newdn, oldfn)
        if oldfn == 'PKG-INFO':
            md = Metadata(path=pn)
            mn = os.path.join(newdn, METADATA_FILENAME)
            md.write(mn)
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
    cmd = [
        'pip', 'install', '--index-url', 'https://pypi.org/simple/', '--timeout', '3', '--default-timeout', '3',
        purelib, platlib, headers, scripts, data, distname
    ]
    result = {
        'scripts': os.path.join(workdir, 'scripts'),
        'headers': os.path.join(workdir, 'headers'),
        'data': os.path.join(workdir, 'data'),
    }
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
    result['name'] = md.name
    result['version'] = md.version
    return result


class WheelTestCase(DistlibTestCase):

    def test_valid_filename(self):
        attrs = ('name', 'version', 'buildver', 'pyver', 'abi', 'arch')
        cases = (
            ('pkg-1.0.0-cp32.cp33-noabi-noarch.whl', ('pkg', '1.0.0', '', ['cp32', 'cp33'], ['noabi'], ['noarch'])),
            ('package-1.0.0-cp33-noabi-linux_x86_64.whl', ('package', '1.0.0', '', ['cp33'], ['noabi'],
                                                           ['linux_x86_64'])),
            ('test-1.0-1st-py2.py3-none-win32.whl', ('test', '1.0', '1st', ['py2', 'py3'], ['none'], ['win32'])),
            ('Pillow-2.8.1-cp27-none-macosx_10_6_intel.'
             'macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.'
             'macosx_10_10_x86_64.whl', ('Pillow', '2.8.1', '', ['cp27'], ['none'], [
                 'macosx_10_6_intel', 'macosx_10_9_intel', 'macosx_10_9_x86_64', 'macosx_10_10_intel',
                 'macosx_10_10_x86_64'
             ])),
        )

        for name, values in cases:
            w = Wheel(name)
            self.assertEqual(w.wheel_version, (1, 1))
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
            self.assertRaises(DistlibException, Wheel, name)

    def test_valid_name(self):
        attrs = ('name', 'version', 'buildver', 'pyver', 'abi', 'arch')
        pyver = PYVER
        cases = (
            ('pkg-1.0.0', ('pkg', '1.0.0', '', [pyver], ['none'], ['any'])),
            ('test-1.0-1st', ('test', '1.0', '1st', [pyver], ['none'], ['any'])),
            (None, ('dummy', '0.1', '', [pyver], ['none'], ['any'])),
        )

        ENDING = '-%s-none-any.whl' % PYVER
        for name, values in cases:
            w = Wheel(name)
            self.assertEqual(w.wheel_version, (1, 1))
            self.assertTrue(w.filename.endswith(ENDING))
            for attr, value in zip(attrs, values):
                self.assertEqual(getattr(w, attr), value)

    def test_compatible_tags(self):
        self.assertEqual(PYVER, 'py%d%d' % sys.version_info[:2])
        tags = COMPATIBLE_TAGS
        self.assertIn((PYVER, 'none', 'any'), tags)
        self.assertIn((PYVER[:-1], 'none', 'any'), tags)
        this_arch = filter(lambda o: o[-1] == ARCH, tags)
        self.assertTrue(this_arch)
        if sys.platform.startswith('linux'):
            arch = ARCH.replace('linux_', '')
            parts = _get_glibc_version()
            if len(parts) == 2:
                self.assertTrue(filter(lambda o: o[-1] == 'manylinux_%s_%s_%s' % (parts[0], parts[1], arch), tags))
                if parts >= (2, 17):
                    self.assertTrue(filter(lambda o: o[-1] == 'manylinux2014_%s' % arch, tags))
                if parts >= (2, 12):
                    self.assertTrue(filter(lambda o: o[-1] == 'manylinux2010_%s' % arch, tags))
                if parts >= (2, 5):
                    self.assertTrue(filter(lambda o: o[-1] == 'manylinux1_%s' % arch, tags))

    def test_is_compatible(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        if PYVER in ('py27', 'py30', 'py31'):
            self.assertTrue(is_compatible(fn))
            self.assertTrue(Wheel(fn).is_compatible())
        # use actual wheel names from PyPI.
        wheel_names = [
            'simplejson-3.17.2-cp27-cp27m-macosx_10_13_x86_64.whl',
            'simplejson-3.17.2-cp27-cp27m-manylinux1_i686.whl',
            'simplejson-3.17.2-cp27-cp27m-manylinux1_x86_64.whl',
            'simplejson-3.17.2-cp27-cp27m-manylinux2010_i686.whl',
            'simplejson-3.17.2-cp27-cp27m-manylinux2010_x86_64.whl',
            'simplejson-3.17.2-cp27-cp27mu-manylinux1_i686.whl',
            'simplejson-3.17.2-cp27-cp27mu-manylinux1_x86_64.whl',
            'simplejson-3.17.2-cp27-cp27mu-manylinux2010_i686.whl',
            'simplejson-3.17.2-cp27-cp27mu-manylinux2010_x86_64.whl',
            'simplejson-3.17.2-cp27-cp27m-win32.whl',
            'simplejson-3.17.2-cp27-cp27m-win_amd64.whl',
            'simplejson-3.17.2-cp33-cp33m-win32.whl',
            'simplejson-3.17.2-cp33-cp33m-win_amd64.whl',
            'simplejson-3.17.2-cp34-cp34m-win32.whl',
            'simplejson-3.17.2-cp34-cp34m-win_amd64.whl',
            'simplejson-3.17.2-cp35-cp35m-manylinux1_i686.whl',
            'simplejson-3.17.2-cp35-cp35m-manylinux1_x86_64.whl',
            'simplejson-3.17.2-cp35-cp35m-manylinux2010_i686.whl',
            'simplejson-3.17.2-cp35-cp35m-manylinux2010_x86_64.whl',
            'simplejson-3.17.2-cp35-cp35m-manylinux2014_aarch64.whl',
            'simplejson-3.17.2-cp35-cp35m-win32.whl',
            'simplejson-3.17.2-cp35-cp35m-win_amd64.whl',
            'simplejson-3.17.2-cp36-cp36m-macosx_10_13_x86_64.whl',
            'simplejson-3.17.2-cp36-cp36m-manylinux1_i686.whl',
            'simplejson-3.17.2-cp36-cp36m-manylinux1_x86_64.whl',
            'simplejson-3.17.2-cp36-cp36m-manylinux2010_i686.whl',
            'simplejson-3.17.2-cp36-cp36m-manylinux2010_x86_64.whl',
            'simplejson-3.17.2-cp36-cp36m-manylinux2014_aarch64.whl',
            'simplejson-3.17.2-cp36-cp36m-win32.whl',
            'simplejson-3.17.2-cp36-cp36m-win_amd64.whl',
            'simplejson-3.17.2-cp37-cp37m-macosx_10_14_x86_64.whl',
            'simplejson-3.17.2-cp37-cp37m-manylinux1_i686.whl',
            'simplejson-3.17.2-cp37-cp37m-manylinux1_x86_64.whl',
            'simplejson-3.17.2-cp37-cp37m-manylinux2010_i686.whl',
            'simplejson-3.17.2-cp37-cp37m-manylinux2010_x86_64.whl',
            'simplejson-3.17.2-cp37-cp37m-manylinux2014_aarch64.whl',
            'simplejson-3.17.2-cp37-cp37m-win32.whl',
            'simplejson-3.17.2-cp37-cp37m-win_amd64.whl',
            'simplejson-3.17.2-cp38-cp38-macosx_10_14_x86_64.whl',
            'simplejson-3.17.2-cp38-cp38-manylinux1_i686.whl',
            'simplejson-3.17.2-cp38-cp38-manylinux1_x86_64.whl',
            'simplejson-3.17.2-cp38-cp38-manylinux2010_i686.whl',
            'simplejson-3.17.2-cp38-cp38-manylinux2010_x86_64.whl',
            'simplejson-3.17.2-cp38-cp38-manylinux2014_aarch64.whl',
            'Pillow-7.2.0-cp35-cp35m-macosx_10_10_intel.whl',
            'Pillow-7.2.0-cp35-cp35m-manylinux1_i686.whl',
            'Pillow-7.2.0-cp35-cp35m-manylinux1_x86_64.whl',
            'Pillow-7.2.0-cp35-cp35m-manylinux2014_aarch64.whl',
            'Pillow-7.2.0-cp35-cp35m-win32.whl',
            'Pillow-7.2.0-cp35-cp35m-win_amd64.whl',
            'Pillow-7.2.0-cp36-cp36m-macosx_10_10_x86_64.whl',
            'Pillow-7.2.0-cp36-cp36m-manylinux1_i686.whl',
            'Pillow-7.2.0-cp36-cp36m-manylinux1_x86_64.whl',
            'Pillow-7.2.0-cp36-cp36m-manylinux2014_aarch64.whl',
            'Pillow-7.2.0-cp36-cp36m-win32.whl',
            'Pillow-7.2.0-cp36-cp36m-win_amd64.whl',
            'Pillow-7.2.0-cp37-cp37m-macosx_10_10_x86_64.whl',
            'Pillow-7.2.0-cp37-cp37m-manylinux1_i686.whl',
            'Pillow-7.2.0-cp37-cp37m-manylinux1_x86_64.whl',
            'Pillow-7.2.0-cp37-cp37m-manylinux2014_aarch64.whl',
            'Pillow-7.2.0-cp37-cp37m-win32.whl',
            'Pillow-7.2.0-cp37-cp37m-win_amd64.whl',
            'Pillow-7.2.0-cp38-cp38-macosx_10_10_x86_64.whl',
            'Pillow-7.2.0-cp38-cp38-manylinux1_i686.whl',
            'Pillow-7.2.0-cp38-cp38-manylinux1_x86_64.whl',
            'Pillow-7.2.0-cp38-cp38-manylinux2014_aarch64.whl',
            'Pillow-7.2.0-cp38-cp38-win32.whl',
            'Pillow-7.2.0-cp38-cp38-win_amd64.whl',
            'Pillow-7.2.0-pp36-pypy36_pp73-macosx_10_10_x86_64.whl',
            'Pillow-7.2.0-pp36-pypy36_pp73-manylinux2010_x86_64.whl',
            'Pillow-7.2.0-pp36-pypy36_pp73-win32.whl',
            'reportlab-3.5.47-cp27-cp27m-macosx_10_9_x86_64.whl',
            'reportlab-3.5.47-cp27-cp27m-manylinux1_i686.whl',
            'reportlab-3.5.47-cp27-cp27m-manylinux1_x86_64.whl',
            'reportlab-3.5.47-cp27-cp27m-manylinux2010_i686.whl',
            'reportlab-3.5.47-cp27-cp27m-manylinux2010_x86_64.whl',
            'reportlab-3.5.47-cp27-cp27mu-manylinux1_i686.whl',
            'reportlab-3.5.47-cp27-cp27mu-manylinux1_x86_64.whl',
            'reportlab-3.5.47-cp27-cp27mu-manylinux2010_i686.whl',
            'reportlab-3.5.47-cp27-cp27mu-manylinux2010_x86_64.whl',
            'reportlab-3.5.47-cp27-cp27m-win32.whl',
            'reportlab-3.5.47-cp27-cp27m-win_amd64.whl',
            'reportlab-3.5.47-cp35-cp35m-macosx_10_6_intel.whl',
            'reportlab-3.5.47-cp35-cp35m-manylinux1_i686.whl',
            'reportlab-3.5.47-cp35-cp35m-manylinux1_x86_64.whl',
            'reportlab-3.5.47-cp35-cp35m-manylinux2010_i686.whl',
            'reportlab-3.5.47-cp35-cp35m-manylinux2010_x86_64.whl',
            'reportlab-3.5.47-cp35-cp35m-win32.whl',
            'reportlab-3.5.47-cp35-cp35m-win_amd64.whl',
            'reportlab-3.5.47-cp36-cp36m-macosx_10_9_x86_64.whl',
            'reportlab-3.5.47-cp36-cp36m-manylinux1_i686.whl',
            'reportlab-3.5.47-cp36-cp36m-manylinux1_x86_64.whl',
            'reportlab-3.5.47-cp36-cp36m-manylinux2010_i686.whl',
            'reportlab-3.5.47-cp36-cp36m-manylinux2010_x86_64.whl',
            'reportlab-3.5.47-cp36-cp36m-win32.whl',
            'reportlab-3.5.47-cp36-cp36m-win_amd64.whl',
            'reportlab-3.5.47-cp37-cp37m-macosx_10_9_x86_64.whl',
            'reportlab-3.5.47-cp37-cp37m-manylinux1_i686.whl',
            'reportlab-3.5.47-cp37-cp37m-manylinux1_x86_64.whl',
            'reportlab-3.5.47-cp37-cp37m-manylinux2010_i686.whl',
            'reportlab-3.5.47-cp37-cp37m-manylinux2010_x86_64.whl',
            'reportlab-3.5.47-cp37-cp37m-win32.whl',
            'reportlab-3.5.47-cp37-cp37m-win_amd64.whl',
            'reportlab-3.5.47-cp38-cp38-macosx_10_9_x86_64.whl',
            'reportlab-3.5.47-cp38-cp38-manylinux1_i686.whl',
            'reportlab-3.5.47-cp38-cp38-manylinux1_x86_64.whl',
            'reportlab-3.5.47-cp38-cp38-manylinux2010_i686.whl',
            'reportlab-3.5.47-cp38-cp38-manylinux2010_x86_64.whl',
            'reportlab-3.5.47-cp38-cp38-win32.whl',
            'reportlab-3.5.47-cp38-cp38-win_amd64.whl',
        ]
        for fn in filter(is_compatible, wheel_names):
            w = Wheel(fn)
            our_arch = ARCH.replace('linux_', '')
            for pyver, abi, arch in w.tags:
                self.assertEqual(pyver, IMPVER)
                self.assertEqual(abi, ABI)
                if sys.platform != 'darwin':
                    self.assertTrue(arch.endswith(our_arch))
                else:
                    m = re.match(r'(\w+)_(\d+)_(\d+)_(\w+)$', our_arch)
                    self.assertTrue(m)
                    _, major, minor, our_arch_kind = m.groups()
                    our_major = int(major)
                    our_minor = int(minor)
                    m = re.match(r'(\w+)_(\d+)_(\d+)_(\w+)$', arch)
                    self.assertTrue(m)
                    _, major, minor, arch_kind = m.groups()
                    major = int(major)
                    minor = int(minor)
                    self.assertEqual(major, our_major)
                    self.assertLessEqual(minor, our_minor)
                    if arch_kind in ('x86_64', 'i386'):
                        self.assertEqual(arch_kind, our_arch_kind)
                    elif arch_kind == 'fat':
                        self.assertIn(our_arch_kind, ('i386', 'ppc'))
                    elif arch_kind == 'fat3':
                        self.assertIn(our_arch_kind, ('i386', 'ppc', 'x86_x64'))
                    elif arch_kind == 'fat64':
                        self.assertIn(our_arch_kind, ('ppc64', 'x86_x64'))
                    elif arch_kind == 'intel':
                        self.assertIn(our_arch_kind, ('i386', 'x86_x64'))
                    elif arch_kind == 'universal':
                        self.assertIn(our_arch_kind, ('i386', 'ppc', 'ppc64', 'x86_x64', 'intel'))
                if 'manylinux' in arch:
                    self.assertTrue(sys.platform.startswith('linux'))
                    parts = _get_glibc_version()
                    self.assertEqual(len(parts), 2)
                    if 'manylinux2014_' in arch:
                        self.assertTrue(parts >= (2, 17))
                    if 'manylinux2010_' in arch:
                        self.assertTrue(parts >= (2, 12))
                    if 'manylinux1_' in arch:
                        self.assertTrue(parts >= (2, 5))
                    if 'manylinux_' in arch:
                        s = 'manylinux_%s_%s_' % parts
                        self.assertIn(s, arch)

    def test_is_compatible_limited_abi(self):
        major_version = sys.version_info.major
        minor_version = sys.version_info.minor
        minimum_abi3_version = (3, 2)
        if not ((major_version, minor_version) >= minimum_abi3_version and IMP_PREFIX == 'cp'):
            self.skipTest('Python %s does not support the limited API' % VER_SUFFIX)

        compatible_wheel_filenames = [
            'dummy-0.1-cp%d%d-abi3-%s.whl' % (major_version, current_minor_version, ARCH)
            for current_minor_version in range(minor_version, -1, -1)
            if (major_version, current_minor_version) >= minimum_abi3_version
        ]
        incompatible_wheel_filenames = [
            'dummy-0.1-cp%d%d-%s-%s.whl' % (major_version, current_minor_version, ABI, ARCH)
            for current_minor_version in range(minor_version - 1, -1, -1)
        ]
        for wheel_filename in compatible_wheel_filenames:
            self.assertTrue(is_compatible(wheel_filename), msg=wheel_filename)
        for wheel_filename in incompatible_wheel_filenames:
            self.assertFalse(is_compatible(wheel_filename), msg=wheel_filename)

    def test_metadata(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        w = Wheel(fn)
        md = w.metadata
        self.assertEqual(md.name, 'dummy')
        self.assertEqual(md.version, '0.1')

    def test_invalid(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        w = Wheel(fn)
        self.assertRaises(DistlibException, w.get_hash, b'', 'badalgo')

    def check_built_wheel(self, wheel, expected):
        for key in expected:
            self.assertEqual(expected[key], getattr(wheel, key))
        fn = os.path.join(wheel.dirname, wheel.filename)
        self.assertTrue(os.path.exists(fn))
        name, version = wheel.name, wheel.version
        with ZipFile(fn, 'r') as zf:
            for key in ('scripts', 'headers', 'data'):
                arcname = '%s-%s.data/%s/%s_file.txt' % (name, version, key, key)
                with zf.open(arcname) as bf:
                    data = bf.read()
                expected = ('dummy data - %s' % key).encode('utf-8')
                if key == 'scripts':
                    expected = b'#!python\n' + expected
                self.assertTrue(data, expected)

    def test_build_tags(self):
        workdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, workdir)
        name = 'dummy'
        version = '0.1'
        paths = {'prefix': workdir}
        for key in ('purelib', 'platlib', 'headers', 'scripts', 'data'):
            paths[key] = p = os.path.join(workdir, key)
            os.makedirs(p)
            fn = os.path.join(p, '%s_file.txt' % key)
            with open(fn, 'w') as f:
                f.write('dummy data - %s' % key)
            if key in ('purelib', 'platlib'):
                p = os.path.join(p, '%s-%s.dist-info' % (name, version))
                os.makedirs(p)
                fn = os.path.join(p, 'RECORD')

        purelib = paths.pop('purelib')
        platlib = paths.pop('platlib')

        # Make a pure wheel with default tags
        paths['purelib'] = purelib
        wheel = Wheel('%s-%s' % (name, version))
        wheel.dirname = workdir
        wheel.build(paths)
        expected = {
            'name': name,
            'version': version,
            'pyver': [PYVER],
            'abi': ['none'],
            'arch': ['any'],
            'filename': 'dummy-0.1-%s-none-any.whl' % PYVER,
        }
        self.check_built_wheel(wheel, expected)
        # Make a pure wheel with custom tags
        pyver = [PYVER[:-1], PYVER]
        wheel.build(paths, {'pyver': pyver})
        expected = {
            'name': name,
            'version': version,
            'pyver': pyver,
            'abi': ['none'],
            'arch': ['any'],
            'filename': 'dummy-0.1-%s-none-any.whl' % '.'.join(pyver),
        }
        self.check_built_wheel(wheel, expected)

        # Make a non-pure wheel with default tags
        paths.pop('purelib')
        paths['platlib'] = platlib
        wheel.build(paths)
        expected['pyver'] = [IMPVER]
        expected['abi'] = [ABI]
        expected['arch'] = [ARCH]
        expected['filename'] = 'dummy-0.1-%s-%s-%s.whl' % (IMPVER, ABI, ARCH)
        self.check_built_wheel(wheel, expected)

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
        maker = ScriptMaker(None, None, add_launchers=False)
        maker.executable = os.path.join(paths['scripts'], 'python')
        dist = w.install(paths, maker)
        self.assertIsNotNone(dist)
        self.assertEqual(dist.name, w.name)
        self.assertEqual(dist.version, w.version)
        shared = dist.shared_locations
        self.assertTrue(shared)
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

    def test_version_incompatibility(self):

        class Warner(object):

            def __call__(self, wheel_version, file_version):
                self.wheel_version = wheel_version
                self.file_version = file_version

        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        dstdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dstdir)
        w = Wheel(fn)
        paths = {'prefix': dstdir}
        for key in ('purelib', 'platlib', 'headers', 'scripts', 'data'):
            paths[key] = os.path.join(dstdir, key)
        warner = Warner()
        maker = ScriptMaker(None, None)
        w.install(paths, maker, warner=warner)
        self.assertEqual(warner.wheel_version, w.wheel_version)
        self.assertEqual(warner.file_version, (2, 0))
        # Now set the wheel's instance to the higher value and ensure
        # warner isn't called
        warner = Warner()
        w.wheel_version = (2, 0)
        w.install(paths, maker, warner=warner)
        self.assertFalse(hasattr(warner, 'wheel_version'))
        self.assertFalse(hasattr(warner, 'file_version'))

    def test_custom_executable(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        for executable in 'mypython', None:
            dstdir = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, dstdir)
            w = Wheel(fn)
            paths = {'prefix': dstdir}
            for key in ('purelib', 'platlib', 'headers', 'scripts', 'data'):
                paths[key] = os.path.join(dstdir, key)
            maker = ScriptMaker(None, None)
            maker.variants = set([''])
            maker.executable = executable
            w.install(paths, maker)
            # On Windows there will be an exe file, and on POSIX a text file.
            # The test is structured to not care.
            p = paths['scripts']
            # there should be just one file in the directory - dummy.py/dummy.exe
            p = os.path.join(p, os.listdir(p)[0])
            with open(p, 'rb') as f:
                data = f.read()
            if executable is None:
                expected = fsencode(get_executable())
            else:
                expected = executable.encode('utf-8')
            expected = b'#!' + expected + b' -E'
            if not sysconfig.is_python_build():
                self.assertIn(expected, data)

    def test_verify(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        w = Wheel(fn)
        w.verify()
        # see issue 115
        fn = os.path.join(HERE, 'valid_wheel-0.0.1-py3-none-any.whl')
        w = Wheel(fn)
        w.verify()
        fn = os.path.join(HERE, 'bad_wheels', 'dummy-0.1-py27-none-any.whl')
        w = Wheel(fn)
        self.assertRaises(DistlibException, w.verify)

    def wheel_modifier_nop(self, path_map):
        return False

    def wheel_modifier(self, path_map):
        mdpath = path_map['dummy-0.1.dist-info/%s' % LEGACY_METADATA_FILENAME]
        md = Metadata(path=mdpath)
        md.add_requirements(['numpy'])
        md.write(path=mdpath, legacy=True)
        return True

    def wheel_modifier_ver(self, path_map):
        mdpath = path_map['dummy-0.1.dist-info/%s' % LEGACY_METADATA_FILENAME]
        md = Metadata(path=mdpath)
        md.version = '0.1+123'
        md.write(path=mdpath, legacy=True)
        return True

    def test_update(self):
        workdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, workdir)
        fn = 'dummy-0.1-py27-none-any.whl'
        sfn = os.path.join(HERE, fn)
        dfn = os.path.join(workdir, fn)
        shutil.copyfile(sfn, dfn)
        mtime = os.stat(dfn).st_mtime
        w = Wheel(dfn)
        modified = w.update(self.wheel_modifier_nop)
        self.assertFalse(modified)
        self.assertEqual(mtime, os.stat(dfn).st_mtime)
        modified = w.update(self.wheel_modifier)
        self.assertTrue(modified)
        self.assertLessEqual(mtime, os.stat(dfn).st_mtime)
        w = Wheel(dfn)
        w.verify()
        md = w.metadata
        self.assertEqual(md.run_requires, ['numpy'])
        self.assertEqual(md.version, '0.1+1')

        modified = w.update(self.wheel_modifier_ver)
        self.assertTrue(modified)
        self.assertLessEqual(mtime, os.stat(dfn).st_mtime)
        w = Wheel(dfn)
        w.verify()
        md = w.metadata
        self.assertEqual(md.run_requires, ['numpy'])
        self.assertEqual(md.version, '0.1+123')

    def test_info(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        w = Wheel(fn)
        actual = w.info
        actual.pop('Generator', None)
        expected = {'Root-Is-Purelib': 'true', 'Tag': 'py27-none-any', 'Wheel-Version': '2.0'}
        self.assertEqual(actual, expected)

    @unittest.skipIf(sys.version_info[:2] != (2, 7), 'The test wheel is only '
                     '2.7 mountable')
    def test_mount(self):
        fn = os.path.join(HERE, 'dummy-0.1-py27-none-any.whl')
        w = Wheel(fn)
        self.assertNotIn(fn, sys.path)
        w.mount()
        self.assertIn(fn, sys.path)
        w.unmount()
        self.assertNotIn(fn, sys.path)

    def test_mount_extensions(self):
        if PYVER == 'py27':
            fn = 'minimext-0.1-cp27-none-linux_x86_64.whl'
        elif PYVER == 'py32':
            fn = 'minimext-0.1-cp32-cp32mu-linux_x86_64.whl'
        elif PYVER == 'py33':
            fn = 'minimext-0.1-cp33-cp33m-linux_x86_64.whl'
        else:
            fn = None
        if not fn:  # pragma: no cover
            raise unittest.SkipTest('Suitable wheel not found.')
        fn = os.path.join(HERE, fn)
        w = Wheel(fn)
        if not w.is_compatible() or not w.is_mountable():  # pragma: no cover
            raise unittest.SkipTest('Wheel not suitable for mounting.')
        self.assertRaises(ImportError, __import__, 'minimext')
        w.mount()
        mod = __import__('minimext')
        self.assertIs(mod, sys.modules['minimext'])
        self.assertEqual(mod.fib(10), 55)
        w.unmount()
        del sys.modules['minimext']
        self.assertRaises(ImportError, __import__, 'minimext')

    def test_local_version(self):
        w = Wheel('dummy-0.1_1.2')
        self.assertEqual(w.filename, 'dummy-0.1_1.2-%s'
                         '-none-any.whl' % PYVER)
        self.assertEqual(w.name, 'dummy')
        self.assertEqual(w.version, '0.1-1.2')
        self.assertFalse(w.exists)
        w.version = '0.1-1.3'
        self.assertEqual(w.filename, 'dummy-0.1_1.3-%s'
                         '-none-any.whl' % PYVER)

    def test_abi(self):
        pyver = sysconfig.get_config_var('py_version_nodot')
        if not pyver:
            pyver = '%s%s' % sys.version_info[:2]
        parts = ['cp', pyver]
        if sysconfig.get_config_var('Py_DEBUG'):
            parts.append('d')
        # Starting with 3.8, the SOABI doesn't append m when WITH_PYMALLOC is
        # defined (see bpo-36707)
        vi = sys.version_info[:2]
        if IMP_PREFIX == 'cp':
            if vi < (3, 8):
                wpm = sysconfig.get_config_var('WITH_PYMALLOC')
                if wpm or wpm is None:
                    parts.append('m')
            if vi < (3, 3):
                us = sysconfig.get_config_var('Py_UNICODE_SIZE')
                if us == 4 or (us is None and sys.maxunicode == 0x10FFFF):
                    parts.append('u')
        if vi < (3, 5):
            abi = ABI
        else:
            abi = ABI.split('-')[0]
        self.assertEqual(''.join(parts), abi)

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    @unittest.skipIf(sys.version_info[:2] >= (3, 7), 'The test distribution is not '
                     '3.7+ compatible')
    def test_build_and_install_pure(self):
        if pip_version() >= (20, 2, 0):
            raise unittest.SkipTest('Test not supported by pip version')
        self.do_build_and_install('sarge == 0.1')

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipIf(hasattr(sys, 'pypy_version_info'), 'The test distribution'
                     ' does not build on PyPy')
    @unittest.skipIf(sys.platform != 'linux2', 'The test distribution only '
                     'builds on Linux')
    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_plat(self):
        if pip_version() >= (20, 2, 0):
            raise unittest.SkipTest('Test not supported by pip version')
        self.do_build_and_install('hiredis == 0.1.1')

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipIf(sys.version_info[0] == 3, 'The test distribution is not '
                     '3.x compatible')
    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_data(self):
        if pip_version() >= (20, 2, 0):
            raise unittest.SkipTest('Test not supported by pip version')
        self.do_build_and_install('Werkzeug == 0.5')

    @unittest.skipIf('SKIP_ONLINE' in os.environ, 'Skipping online test')
    @unittest.skipIf(sys.version_info[0] == 3, 'The test distribution is not '
                     '3.x compatible')
    @unittest.skipUnless(PIP_AVAILABLE, 'pip is needed for this test')
    def test_build_and_install_scripts(self):
        if pip_version() >= (20, 2, 0):
            raise unittest.SkipTest('Test not supported by pip version')
        self.do_build_and_install('Babel == 0.9.6')


if __name__ == '__main__':  # pragma: no cover
    import logging
    logging.basicConfig(level=logging.DEBUG, filename='test_wheel.log', filemode='w', format='%(message)s')
    unittest.main()
