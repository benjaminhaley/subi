"""
Setup for or py2app/py2exe

adapted from:
    http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html#py2app-options

author
    bmh Dec 2011 - Jan 2012

Usage 
    (Mac OS X):
    python setup.py py2app

    (Windows):
    python setup.py py2exe
    
TODO
    The current setup is garbage.
    Remove redundancy between win and mac setups.
    Save windows from explictly naming each data file
    
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
    from setuptools import setup
    import py2exe
    extra_options = dict(
        setup_requires=['py2exe'],
        data_files=[
            ('web', 
                [
                    r'web\\404.html',
                    r'web\\favicon.ico',
                    r'web\\subi.html',
                    r'web\\upload.html',
                ]
            ),
            ('web\\css\\bootstrap', 
                [
                    r'web\\css\\bootstrap\\bootstrap.min.css',
                    r'web\\css\\bootstrap\\bootstrap.css'
                ]
            )
        ],
        console=[mainscript],

        #exe=[mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options=dict(py2exe=dict(
            )),
    )
    setup(
        name="Subi.exe",
        **extra_options
    )
    #from distutils.core import setup
    #import py2exe
    #setup(console=[mainscript])



