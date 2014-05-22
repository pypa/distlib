This is a simple launcher for Python files, which is functionally equivalent to
the launchers in setuptools but not based on setuptools code. There are two
versions of the launcher - console and GUI - built from the same source code.

The launcher has been written as part of the pythonv branch, and is intended
to facilitate location of the correct Python executable for a script in an
environment where there may be multiple versions of Python deployed.

The launcher is intended to facilitate script execution under Windows where a
PEP 397-compatible launcher is not available. The idea is that each Python
script has a copy of the launcher (symlinks not being generally available
under Windows). For scripts to work with the launcher, they have to have a name
ending in -script.py (for a console script) or -script.pyw (for a GUI script).
The deployment system (e.g. packaging) will ensure that for foo-script.py, a
console launcher opy named foo.exe is placed in the same directory; for
bar-script.pyw, a GUI launcher copy named bar.exe is placed in the same
directory.

Assuming that the relevant directories are on the path, the scripts can be
invoked using just "foo" or "bar". The foo.exe or bar.exe executable then
runs: it looks for a script with the appropriate suffix ("-script.py" or
"-script.pyw") in the same directory, and if found, opens that script to read a
shebang line indicating which Python executable to use for the script. That
executable, if found, is launched with the script and other arguments passed:

foo a b c -> c:\path\to\python.exe c:\other\path\to\foo-script.py a b c
bar d e f -> c:\path\to\pythonw.exe c:\other\path\to\bar-script.pyw d e f

Note: More recently, the launchers have been updated to find their script in an
archive appended to the executable, rather than a separate file. (This variant
is enabled when APPENDED_ARCHIVE is #defined). This allows the launchers to be
used to e.g. run .pyz archives as native Windows executables.
