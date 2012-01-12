"""
Setup for or py2app/py2exe

adapted from:
  http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html#py2app-options

bmh Dec 2011


Original Documentation

 py2app\py2exe build script for MyApplication.

 Will automatically ensure that all build prerequisites are available
 via ez_setup

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
"""

import sys

mainscript = 'subi.py'

if sys.platform == 'darwin':
    from setuptools import setup
    extra_options = dict(
        setup_requires=['py2app'],
        app=[mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options=dict(py2app=dict(
            resources=['web', 'db'],
            )),
    )
    setup(
        name="Subi",
        **extra_options
    )
elif sys.platform == 'win32':
    from distutils.core import setup
    import py2exe
    setup(console=[mainscript])



