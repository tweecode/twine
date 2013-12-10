#
# This builds an .app out of Twine for use with OS X.
# Call this with this command line: buildapp.py py2app

from distutils.core import setup
import py2app

setup(app = ['app.py'], options = dict(py2app = dict( argv_emulation = True,
                                       iconfile = 'appicons/app.icns', \
                                       resources = ['icons', 'targets'], \
                                       plist = dict( \
                                       CFBundleShortVersionString = '1.4', \
                                       CFBundleName = 'Twine', \
                                       CFBundleIconFile = 'app.icns',\
                                       NSHumanReadableCopyright = 'GNU General Public License v2'))))
