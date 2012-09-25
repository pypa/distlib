import os
import re

# check if Python is called on the first line with this expression
FIRST_LINE_RE = re.compile(b'^#!.*pythonw?[0-9.]*([ \t].*)?$')
DOTTED_CALLABLE_RE = re.compile(r'''(?P<name>(\w|-)+)
                                    \s*=\s*(?P<callable>(\w+)(\.\w+)+)
                                    (?P<flags>(\s+\w+)*)''', re.VERBOSE)
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

if os.name == 'nt':
    # Executable launcher support.
    # Launchers are from https://bitbucket.org/vinay.sajip/simple_launcher/
    import struct

    def get_launcher(kind):
        if struct.calcsize('P') == 8:   # 64-bit
            bits = '64'
        else:
            bits = '32'
        fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '%s%s.exe' % (kind, bits))
        with open(fname, 'rb') as f:
            result = f.read()
        return result


class ScriptMaker(object):
    def __init__(self, source_dir, target_dir, add_launchers=False):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.add_launchers = add_launchers

    def make(self, specification):
        result = []
        return result

    def make_multiple(self, specifications):
        result = []
        for specification in specifications:
            result.extend(self.make(specification))

