import logging
import os
import re
import struct
import sys

from . import DistlibException
from .compat import sysconfig, fsencode, detect_encoding
from .util import FileOperator

logger = logging.getLogger(__name__)

# check if Python is called on the first line with this expression
FIRST_LINE_RE = re.compile(b'^#!.*pythonw?[0-9.]*([ \t].*)?$')
DOTTED_CALLABLE_RE = re.compile(r'''(?P<name>(\w|-)+)
                                    \s*=\s*(?P<callable>(\w+)([:\.]\w+)+)
                                    \s*(\[(?P<flags>\w+(=\w+)?(,\s*\w+(=\w+)?)*)\])?''', re.VERBOSE)
SCRIPT_TEMPLATE = '''%(shebang)s
if __name__ == '__main__':
    rc = 1
    try:
        import sys, re
        sys.argv[0] = re.sub('-script.pyw?$', '', sys.argv[0])
        from %(module)s import %(func)s
        rc = %(func)s() # None interpreted as 0
    except Exception:
        # use syntax which works with either 2.x or 3.x
        sys.stderr.write('%%s\\n' %% sys.exc_info()[1])
    sys.exit(rc)
'''


class ScriptMaker(object):
    def __init__(self, source_dir, target_dir, add_launchers=True,
                 dry_run=False):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.add_launchers = add_launchers
        self.force = False
        self.fileop = FileOperator(dry_run)

    def _get_shebang(self, encoding, post_interp=b''):
        if not sysconfig.is_python_build():
            if sys.platform == 'darwin' and ('__VENV_LAUNCHER__'
                                             in os.environ):
                executable =  os.environ['__VENV_LAUNCHER__']
            else:
                executable = sys.executable
        elif hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix:
            executable = os.path.join(
                sysconfig.get_path('scripts'),
               'python%s' % sysconfig.get_config_var('EXE'))
        else:
            executable = os.path.join(
                sysconfig.get_config_var('BINDIR'),
               'python%s%s' % (sysconfig.get_config_var('VERSION'),
                               sysconfig.get_config_var('EXE')))
        executable = fsencode(executable)
        shebang = b'#!' + executable + post_interp + b'\n'
        # Python parser starts to read a script using UTF-8 until
        # it gets a #coding:xxx cookie. The shebang has to be the
        # first line of a file, the #coding:xxx cookie cannot be
        # written before. So the shebang has to be decodable from
        # UTF-8.
        try:
            shebang.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(
                'The shebang (%r) is not decodable from utf-8' % shebang)
        # If the script is encoded to a custom encoding (use a
        # #coding:xxx cookie), the shebang has to be decodable from
        # the script encoding too.
        if encoding != 'utf-8':
            try:
                shebang.decode(encoding)
            except UnicodeDecodeError:
                raise ValueError(
                    'The shebang (%r) is not decodable '
                    'from the script encoding (%r)' % (shebang, encoding))
        return shebang

    def _make_script(self, name, path, flags, filenames):
        colons = path.count(':')
        if colons > 1:
            raise DistlibException('Invalid script: %r' % path)
        elif colons == 1:
            module, func = path.split(':')
        else:
            module, func = path.rsplit('.', 1)
        if flags is None:
            flags = ''
        flags = flags.strip().split()
        shebang = self._get_shebang('utf-8').decode('utf-8')
        if 'gui' in flags and os.name == 'nt':
            shebang = shebang.replace('python', 'pythonw')
        script = SCRIPT_TEMPLATE % dict(module=module, shebang=shebang,
                                        func=func)
        outname = os.path.join(self.target_dir, name)
        use_launcher = self.add_launchers and os.name == 'nt'
        if use_launcher:
            exename = '%s.exe' % outname
            if 'gui' in flags:
                ext = 'pyw'
                launcher = self._get_launcher('w')
            else:
                ext = 'py'
                launcher = self._get_launcher('t')
            outname = '%s-script.%s' % (outname, ext)
        self.fileop.write_text_file(outname, script, 'utf-8')
        filenames.append(outname)
        if use_launcher:
            self.fileop.write_binary_file(exename, launcher)
            filenames.append(exename)

    def _copy_script(self, script, filenames):
        adjust = False
        script = self.fileop.convert_path(script)
        outname = os.path.join(self.target_dir, os.path.basename(script))
        filenames.append(outname)
        script = os.path.join(self.source_dir, script)
        if not self.force and not self.fileop.newer(script, outname):
            logger.debug('not copying %s (up-to-date)', script)
            return

        # Always open the file, but ignore failures in dry-run mode --
        # that way, we'll get accurate feedback if we can read the
        # script.
        try:
            f = open(script, 'rb')
        except IOError:
            if not self.dry_run:
                raise
            f = None
        else:
            encoding, lines = detect_encoding(f.readline)
            f.seek(0)
            first_line = f.readline()
            if not first_line:
                logger.warning('%s: %s is an empty file (skipping)',
                               self.get_command_name(),  script)
                return

            match = FIRST_LINE_RE.match(first_line)
            if match:
                adjust = True
                post_interp = match.group(1) or b''

        if not adjust:
            if f:
                f.close()
            self.fileop.copy_file(script, outname)
        else:
            logger.info('copying and adjusting %s -> %s', script,
                        self.target_dir)
            if not self.fileop.dry_run:
                shebang = self._get_shebang(encoding, post_interp)
                use_launcher = self.add_launchers and os.name == 'nt'
                if use_launcher:
                    n, e = os.path.splitext(outname)
                    exename = n + '.exe'
                    if b'pythonw' in first_line:
                        launcher = self._get_launcher('w')
                        suffix = '-script.pyw'
                    else:
                        launcher = self._get_launcher('t')
                        suffix = '-script.py'
                    outname = n + suffix
                    filenames[-1] = outname
                self.fileop.write_binary_file(outname, shebang + f.read())
                if use_launcher:
                    self.fileop.write_binary_file(exename, launcher)
                    filenames.append(exename)
            if f:
                f.close()

    @property
    def dry_run(self):
        return self.fileop.dry_run

    @dry_run.setter
    def dry_run(self, value):
        self.fileop.dry_run = value

    if os.name == 'nt':
        # Executable launcher support.
        # Launchers are from https://bitbucket.org/vinay.sajip/simple_launcher/

        def _get_launcher(self, kind):
            if struct.calcsize('P') == 8:   # 64-bit
                bits = '64'
            else:
                bits = '32'
            fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '%s%s.exe' % (kind, bits))
            with open(fname, 'rb') as f:
                result = f.read()
            return result

    # Public API follows

    def make(self, specification):
        filenames = []
        m = DOTTED_CALLABLE_RE.search(specification)
        if not m:
            self._copy_script(specification, filenames)
        else:
            d = m.groupdict()
            self._make_script(d['name'], d['callable'], d['flags'], filenames)
        return filenames

    def make_multiple(self, specifications):
        filenames = []
        for specification in specifications:
            filenames.extend(self.make(specification))
        return filenames
