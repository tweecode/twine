Twine
=====

Introduction
------------

A visual tool for creating interactive stories for the Web, based on the
[Twee](https://github.com/tweecode/twee) story engine. Twine is written 
primarily in Python and Javascript, with UI widgets provided by wxPython.
Twine was written by Chris Klimas. Further information is available at:

http://twinery.org/

Installation
------------

The easiest way to install Twine is to download the installable versions
for Windows or Mac OS X:

 * [Twine 1.4 for Windows](http://twinery.org/downloads/twine_1.4_win.exe)
 * [Twine 1.4 for Mac OS X](http://twinery.org/downloads/twine_1.4_osx.zip)

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

Contributing to Twine development
---------------------------------

If you have bug fixes for Twine, the easiest
way to contribute them back is as follows:

* fork this repository (see link at top of the project page on github)
* make your fixes and push them to your own fork on github
* make a pull request (see link at top of the github project page)

To report bugs, issues or feature requests, use the 
[github issues](https://github.com/tweecode/twine/issues) system.
