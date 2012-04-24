Twine
=====

Introduction
------------

A visual tool for creating interactive stories for the Web, based on the
[Twee](https://github.com/tweecode/twee) story engine. Twine is written 
primarily in Python and Javascript, with UI widgets provided by wxPython.
Twine was written by Chris Klimas. Further information is available at:

[http://gimcrackd.com/etc/src/](http://gimcrackd.com/etc/src/)

Installation
------------

The easiest way to install Twine is to download the installable versions
for Windows or Mac OS X:

 * [Twine 1.3.5 for Windows](http://twee.googlecode.com/files/twine-1.3.5-windows.exe)
 * [Twine 1.3.5 for Mac OS X](http://twee.googlecode.com/files/twine-1.3.5-osx.zip)

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

You should now have a working Twine setup. To start Twine:

	python app.py

Special instructions for Mac OS X
---------------------------------

The version of python distributed with Mac OS X requires a 64-bit version
of wxPython. As of today, the stable version of wxPython (2.8.*) does not 
work in 64 bit mode on the Mac. There are several ways to work around this
issue. Two common approaches are:

### force python to run in 32-bit mode

Add an executable file named `python_32` to your/virtualenv/path/bin/ 
containing:

	#! /bin/bash
	export VERSIONER_PYTHON_PREFER_32_BIT=yes
	/usr/bin/python "$@"

You should now be able to run Twine using a command like this:

	python_32 app.py

### use a 64-bit compatible version of wxPthon and python 2.7

The current development version of wxPython (2.9.*) includes support for 
Cocoa, making it possible to run it in 64-bit mode. See the 
[wxPython download page](http://www.wxpython.org/download.php).

Contributing to Twine development
---------------------------------

If you have bug fixes for [Twine](https://github.com/tweecode/twine) -- or
any of the other  [related projects](https://github.com/tweecode) -- the 
easiest way to contribute them back is as follows:

* fork this repository (see link at top of the project page on github)
* make your fixes and push them to your own fork on github
* make a pull request (see link at top of the github project page)

To report bugs, issues or feature requests, use the 
[github issues](https://github.com/tweecode/twine/issues) system.
