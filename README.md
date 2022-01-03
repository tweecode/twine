Twine 1
=======

Introduction
------------

A visual tool for creating interactive stories for the Web, based on the
[Twee](https://github.com/tweecode/twee) story engine. Twine 1 is written 
primarily in Python and Javascript, with UI widgets provided by wxPython.
Twine was written by Chris Klimas. More information is available at
http://twinery.org/

Twine 1 development has ceased.

A web-application "sequel" to Twine 1, called Twine 2, has been development see: http://twinery.org/.  
Its repositories are [here](https://github.com/klembot/twinejs) and [here](https://foss.heptapod.net/games/harlowe/).

Installation
------------

The easiest way to install Twine 1 is to download the installable versions
for Windows or Mac OS X:

 * [Twine 1.4.3 for Windows](https://github.com/tweecode/twine/releases/tag/v1.4.3)
 * [Twine 1.4.2 for OS X](https://twinery.org)

From source code to a working Twine 1 - running on Python in Windows
--------------------------------------------------------------------

The most basic way to use Twine 1 v1.4.3 is run it through Python.  To set up, carry out these three steps in order:

* Download and install the appropriate (ie. old) Python environment (v2.7.18).  Use the 32 bit versions of Python and the other programs.  [https://www.python.org/downloads/release/python-2718/](https://www.python.org/downloads/release/python-2718/)

* Next, download and install wxPython (v2.9.5.0) that is compatible with your Python installation (32 bit) [https://sourceforge.net/projects/wxpython/files/wxPython/2.9.5.0/](https://sourceforge.net/projects/wxpython/files/wxPython/2.9.5.0/)

* Create a folder (anywhere other than in the Windows program folders or other special folders reserved by Windows).  Download Twine 1’s source code into your new folder.  Get the source code from here: https://github.com/tweecode/twine/archive/master.zip   Unzip or copy out the contents of the zip file into your new folder.  Inside the copied/unzipped folder “twine-master”, find the file “app.py”.  Double click on the app.py file.  This will activate Python and will cause a working copy of Twine 1.4.3. to be created and to open.  When you want to use Twine again, double click on app.py again.

Twine 1 on Windows – independent of Python
------------------------------------------

The next steps in this section build on the three steps in the section above.

The aim this time is to compile the unzipped source code into a set of stand-alone files that can allow Twine 1 to run independently of Python.

* In addition to your previous installations of Python and wxPython, you now need to download and install Py2Exe v0.6.9 for Windows from https://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/

* Now go to the folder where the source code files are located and double click on “buildexe.py”. This will trigger Python to cause a new set of files to be created in a subfolder within the “twine-master” folder.  The new folder is called “dist”.  (Relevant for later, these is also another new folder created called “build”.)

You will find the new compiled Twine files inside the “dist” folder and inside that they are in the “win32” folder.  ie. \dist\win32\

The key file inside the win32 folder is “twine.exe”.  If you double click on the twine.exe file then Twine 1 will start up without needing to use Python.  You can activate Twine 1 by placing a Windows shortcut wherever it suits you.

Creating a  Twine 1 installer for Windows
------------------------------------------

This is the most liberating of the set-up processes – allowing non-expert users to easily install Twine 1.4.3 on Windows computers.

Care needs to be taken with this process because it’s easy for errors to block the creation of the installer.

* First, download the latest version of the NSIS installer packager from:  https://nsis.sourceforge.io and install it.  (The Twine 1 windows installer on the Twine github site was made with v3.08 of NSIS on 1 January 2022.)

* Now go to the folder that holds the source code and the compiled files.  Go specifically to the “twine-master” folder and look for the file “install.nsi”.  Open this file with a text editor so you can read the contents.  At the top of the script file you will discover that you have to find an additional file “vcredist_x86.exe” from the Microsoft website:  https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2013-vc-120   Download the x86 version for 2013.  Then within the twine-master folder find the “build” sub-folder (created by Py2Exe) and place a copy of the vcredist_x86.exe file in there.

* Next, in the twine-master folder, find the file “gpl.txt”.  Copy this file and go to the “dist” sub-folder then go further down to the “win32” sub folder.  Here you will find all the files created by Py2Exe including the Twine.exe file.  In this win32 sub-folder paste the copy of the gpl.txt file.

* Now run the NSIS installer making program and click on the link on the top left of the program window called “Compile NSI scripts”.  A new NSIS program window will open.  Go to the twine-master folder and find the file “install.nsi”.  Drag this file over and drop it on the most recently opened NSIS window.  This will set NSIS to begin the task of packaging up all the needed files and folders to make the Twine installer file:  “twine-1.4.3-win.exe”.

When the NSIS program has completed working through the install.nsi script, you will find the newly created “twine-1.4.3-win.exe” in the “dist” sub-folder in the twine-master folder.

Set up a development environment
--------------------------------

You can set up a development environment if you want to contribute to 
the Twine 1 dev project or if you want to run Twine on another platform (such as 
Linux).

You may want to run your development environment in a
[virtualenv](http://pypi.python.org/pypi/virtualenv):

    virtualenv tweecode
    cd tweecode/
    source bin/activate

Get the code:

	git clone git@github.com:tweecode/twine.git

Install required modules (note, wxPython will need to be installed separately from the pip requirements):

	cd twine/
	pip install -r requirements.txt

You also need to install [py2exe](http://www.py2exe.org/) (on Windows) or
[py2app](https://pythonhosted.org/py2app/) (on OS X) to compile standalone binaries.

Other than that, you should now have a working Twine setup. To start Twine:

	python app.py

Contributing to Twine 1 maintenance
-----------------------------------

Warning - there has been no active response to issues with Twine 1.4.2 / 1.4.3 since about 2014.  If you want to do anything to fix bugs in Twine 1.4.3 you might have to find somebody with skills in Python 2.7 (with wxPython) programming, and html, CSS, and Javaascript - and then do the fixes yourselves.

If you have bug fixes for Twine 1.4.3, the easiest
way to contribute them back is as follows:

* fork this repository (see link at top of the project page on github)
* make your fixes and push them to your own fork on github
* make a pull request (see link at top of the github project page)
* find somebody with permission to do the commmits and with the programming skills to assess your fixes.  This willtwillhe hardsest part of the job!!!  Good luck.

To report bugs, issues or feature requests, use the 
[github issues](https://github.com/tweecode/twine/issues) system.

