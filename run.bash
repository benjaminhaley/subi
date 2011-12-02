#!/bin/bash
#
# Should build and run the stand alone app
# requires py2app is installed.

rm setup.py
py2applet --make-setup --argv-emulation=False subi.py
rm -rf build dist
python setup.py py2app -A
./dist/subi.app/Contents/MacOS/subi
