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
                    r'web\\bootstrap.min.css',
                    r'web\\jquery-ui-1.8.css',
                    r'web\\404.html',
                    r'web\\subi.html',
                    r'web\\upload.html',
                    r'web\\favicon.ico',
                    r'web\\bootstrap-dropdown.js',
                    r'web\\jquery-1.7.1.min.js',
                    r'web\\jquery.form.js',
                    r'web\\jquery.jeditable.mini.js',
                    r'web\\jquery-ui-1.8.16.min.js'
                ]
            ),
            ('data', 
                [
                    r'data\\subi.db',
                    r'data\\subi_backup_example',
                ]
            ),
            r'userguide.pdf',
            r'language.txt'
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



