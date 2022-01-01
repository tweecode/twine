Twine 1
=======

Introduction
------------

A visual tool for creating interactive stories for the Web, based on the
[Twee](https://github.com/tweecode/twee) story engine. Twine is written 
primarily in Python and Javascript, with UI widgets provided by wxPython.
Twine was written by Chris Klimas. More information is available at
http://twinery.org/

Twine 1 development has ceased.

A web-application "sequel" to Twine 1, called Twine 2, has been development see: http://twinery.org/.  
Its repositories are [here](https://github.com/klembot/twinejs) and [here](https://foss.heptapod.net/games/harlowe/).

Installation
------------

The easiest way to install Twine is to download the installable versions
for Windows or Mac OS X:

 * [Twine 1.4.2 for Windows](http://twinery.org/downloads/twine_1.4.2_win.exe)
 * [Twine 1.4.2 for OS X](http://twinery.org/downloads/twine_1.4.2_osx.zip)

Set up a development environment
--------------------------------

You can set up a development environment if you want to contribute to 
the project or if you want to run Twine on another platform (such as 
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

If you have bug fixes for Twine, the easiest
way to contribute them back is as follows:

* fork this repository (see link at top of the project page on github)
* make your fixes and push them to your own fork on github
* make a pull request (see link at top of the github project page)

To report bugs, issues or feature requests, use the 
[github issues](https://github.com/tweecode/twine/issues) system.

But be warned (!) - there has been no active response to issues since about 2014.  If you want to do anything to fix bugs you might have to find somebody with skills in Python 2.7 (with wxPython) programming, and html, CSS, and Javaascript - and then do the fixes yourselves.
