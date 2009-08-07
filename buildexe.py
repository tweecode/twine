#
# This builds an .exe out of Tweebox for use with Windows.
# Call this with this command line: buildexe.py py2exe

import sys, os, py2exe
from distutils.core import setup

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>Twine</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""

# build the exe

setup( windows = [{ 'script':'app.py', \
                    'icon_resources': [(0x0004, 'icons\\app.ico')], \
                    'other_resources': [(24, 1, manifest)] }])