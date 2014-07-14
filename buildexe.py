
# This builds an .exe out of Tweebox for use with Windows.
# Call this with this command line: buildexe.py
# py2exe is inserted as a command line parameter automatically.

import sys, os
import py2exe # pylint: disable=unused-import,import-error
from distutils.core import setup
from version import versionString

manifest = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="1.3.5.1"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.30729.6161"
            processorArchitecture="X86"
            publicKeyToken="1fc8b3b9a1e18e3b"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''


# Force use of py2exe for building Win32.exe
sys.argv.append('py2exe')

# Clear out the dist/win32 directory
for root, dirs, files in os.walk('dist' + os.sep + 'win32', topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))


# Build the exe
setup(
    name = 'Twine',
    description = 'Twine',
    version = versionString,

    windows = [{
        'script': 'app.py',
        'icon_resources': [(0x0004, 'appicons\\app.ico'), (0x0005, 'appicons\\doc.ico')],
        'dest_base': 'twine',
        'other_resources': [(24, 1, manifest % dict(prog='Twine'))],
    }],

    data_files = [
        ('targets' + os.sep + 'jonah',      ['targets' + os.sep + 'jonah'      + os.sep + 'header.html',
                                             'targets' + os.sep + 'jonah'      + os.sep + 'code.js']),
        ('targets' + os.sep + 'sugarcane',  ['targets' + os.sep + 'sugarcane'  + os.sep + 'header.html',
                                             'targets' + os.sep + 'sugarcane'  + os.sep + 'code.js']),
        ('targets' + os.sep + 'Responsive', ['targets' + os.sep + 'Responsive' + os.sep + 'header.html']),
        ('targets', [
            'targets' + os.sep + 'engine.js',
            'targets' + os.sep + 'jquery.js',
            'targets' + os.sep + 'modernizr.js']),
        ('icons', [
            # toolbar icons
            'icons' + os.sep + 'newpassage.png',
            'icons' + os.sep + 'zoomin.png',
            'icons' + os.sep + 'zoomout.png',
            'icons' + os.sep + 'zoomfit.png',
            'icons' + os.sep + 'zoom1.png',
            'icons' + os.sep + 'zoomfit.png',

            # other icons
            'icons' + os.sep + 'brokenemblem.png',
            'icons' + os.sep + 'externalemblem.png',
            'appicons' + os.sep + 'app.ico',
        ]),
    ],

    options = {
                  'py2exe': {
                        'dist_dir': 'dist' + os.sep + 'win32',
                        'bundle_files': 3,
                        'optimize': 2,
                        'ignores': ['_scproxy'],
                        'dll_excludes': ['w9xpopen.exe', 'MSVCP90.dll'],
                        'compressed': True,
                  }
    },
    zipfile = 'library.zip',
)

print 'Check the ./dist/win32 folder'
