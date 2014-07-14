#!/usr/bin/env python2

import sys, os, locale, re, pickle, wx, platform, traceback
import metrics
from header import Header
from storyframe import StoryFrame
from prefframe import PreferenceFrame
from version import versionString

class App(wx.App):
    """This bootstraps our application and keeps track of preferences, etc."""

    NAME = 'Twine'
    VERSION = '%s (running on %s %s)' % (versionString, platform.system(), platform.release()) #Named attributes not available in Python 2.6
    RECENT_FILES = 10

    def __init__(self, redirect = False):
        """Initializes the application."""
        wx.App.__init__(self, redirect = redirect)
        locale.setlocale(locale.LC_ALL, '')
        self.stories = []
        self.loadPrefs()
        self.determinePaths()
        self.loadTargetHeaders()

        # try to load our app icon
        # if it doesn't work, we continue anyway

        self.icon = wx.EmptyIcon()

        try:
            self.icon = wx.Icon(self.iconsPath + 'app.ico', wx.BITMAP_TYPE_ICO)
        except:
            pass


        # restore save location

        try:
            os.chdir(self.config.Read('savePath'))
        except:
            os.chdir(os.path.expanduser('~'))

        if not self.openOnStartup():
            if self.config.HasEntry('LastFile') \
            and os.path.exists(self.config.Read('LastFile')):
                self.open(self.config.Read('LastFile'))
            else:
                self.newStory()

    def newStory(self, event = None):
        """Opens a new, blank story."""
        s = StoryFrame(parent = None, app = self)
        self.stories.append(s)
        s.Show(True)

    def removeStory(self, story, byMenu = False):
        """Removes a story from our collection. Should be called when it closes."""
        try:
            self.stories.remove(story)
            if byMenu:
                counter = 0
                for s in self.stories:
                    if isinstance(s, StoryFrame):
                        counter = counter + 1
                if counter == 0:
                    self.newStory()

        except ValueError:
            pass

    def openDialog(self, event = None):
        """Opens a story file of the user's choice."""
        dialog = wx.FileDialog(None, 'Open Story', os.getcwd(), "", "Twine Story (*.tws)|*.tws", \
                               wx.FD_OPEN | wx.FD_CHANGE_DIR)

        if dialog.ShowModal() == wx.ID_OK:
            self.config.Write('savePath', os.getcwd())
            self.addRecentFile(dialog.GetPath())
            self.open(dialog.GetPath())

        dialog.Destroy()

    def openRecent(self, story, index):
        """Opens a recently-opened file."""
        filename = story.recentFiles.GetHistoryFile(index)
        if not os.path.exists(filename):
            self.removeRecentFile(story, index)
        else:
            self.open(filename)
            self.addRecentFile(filename)

    def MacOpenFile(self, path):
        """OS X support"""
        self.open(path)

    def open(self, path):
        """Opens a specific story file."""
        try:
            openedFile = open(path, 'r')
            newStory = StoryFrame(None, app = self, state = pickle.load(openedFile))
            newStory.saveDestination = path
            self.stories.append(newStory)
            newStory.Show(True)
            self.addRecentFile(path)
            self.config.Write('LastFile', path)
            openedFile.close()

            # weird special case:
            # if we only had one story opened before
            # and it's pristine (e.g. no changes ever made to it),
            # then we close it after opening the file successfully

            if (len(self.stories) == 2) and (self.stories[0].pristine):
                self.stories[0].Destroy()

        except:
            self.displayError('opening your story')

    def openOnStartup(self):
        """
        Opens any files that were passed via argv[1:]. Returns
        whether anything was opened.
        """
        if len(sys.argv) is 1:
            return False

        for file in sys.argv[1:]:
            self.open(file)

        return True

    def exit(self, event = None):
        """Closes all open stories, implicitly quitting."""
        # need to make a copy of our stories list since
        # stories removing themselves will alter the list midstream
        for s in list(self.stories):
            if isinstance(s, StoryFrame):
                s.Close()

    def showPrefs(self, event = None):
        """Shows the preferences dialog."""
        if not hasattr(self, 'prefFrame'):
            self.prefFrame = PreferenceFrame(self)
        else:
            try:
                self.prefFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'prefFrame')
                self.showPrefs(event)

    def addRecentFile(self, path):
        """Adds a path to the recent files history and updates the menus."""
        for s in self.stories:
            if isinstance(s, StoryFrame):
                s.recentFiles.AddFileToHistory(path)
                s.recentFiles.Save(self.config)

    def removeRecentFile(self, story, index):
        """Remove all missing files from the recent files history and update the menus."""

        def removeRecentFile_do(story, index, showdialog = True):
            filename = story.recentFiles.GetHistoryFile(index)
            story.recentFiles.RemoveFileFromHistory(index)
            story.recentFiles.Save(self.config)
            if showdialog:
                text = 'The file ' + filename + ' no longer exists.\n' + \
                       'This file has been removed from the Recent Files list.'
                dlg = wx.MessageDialog(None, text, 'Information', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return True
            else:
                return False
        showdialog = True
        for s in self.stories:
            if s != story and isinstance(s, StoryFrame):
                removeRecentFile_do(s, index, showdialog)
                showdialog = False
        removeRecentFile_do(story, index, showdialog)

    def verifyRecentFiles(self, story):
        done = False
        while done == False:
            for index in range(story.recentFiles.GetCount()):
                if not os.path.exists(story.recentFiles.GetHistoryFile(index)):
                    self.removeRecentFile(story, index)
                    done = False
                    break
            else:
                done = True

    def about(self, event = None):
        """Shows the about dialog."""
        info = wx.AboutDialogInfo()
        info.SetName(self.NAME)
        info.SetVersion(self.VERSION)
        info.SetIcon(self.icon)
        info.SetWebSite('http://twinery.org/')
        info.SetDescription('An open-source tool for telling interactive stories\nwritten by Chris Klimas')
        info.SetDevelopers(['Leon Arnott','Emmanuel Turner','Henry Soule','Misty De Meo','Phillip Sutton',
                            'Thomas M. Edwards','Maarten ter Huurne','and others.'])

        info.SetLicense('The Twine development application and its Python source code is free software:'
                        ' you can redistribute it and/or modify it under the terms of the GNU General Public License'
                        ' as published by the Free Software Foundation, either version 3 of the License,'
                        ' or (at your option) any later version. See the GNU General Public License for more details.'
                        '\n\n'
                        'The Javascript game engine in compiled game files is a derivative work of Jeremy Ruston\'s'
                        ' TiddlyWiki project, and is used under the terms of the MIT license.')
        wx.AboutBox(info)

    def storyFormatHelp(self, event = None):
        """Opens the online manual to the section on story formats."""
        wx.LaunchDefaultBrowser('http://twinery.org/wiki/story_format')

    def openForum(self, event = None):
        """Opens the forum."""
        wx.LaunchDefaultBrowser('http://twinery.org/forum/')

    def openDocs(self, event = None):
        """Opens the online manual."""
        wx.LaunchDefaultBrowser('http://twinery.org/wiki/')

    def openGitHub(self, event = None):
        """Opens the GitHub page."""
        wx.LaunchDefaultBrowser('https://github.com/tweecode/twine')

    def loadPrefs(self):
        """Loads user preferences into self.config, setting up defaults if none are set."""
        sc = self.config = wx.Config('Twine')

        for k,v in {
            'savePath' : os.path.expanduser('~'),
            'fsTextColor' : '#afcdff',
            'fsBgColor' : '#100088',
            'fsFontFace' : metrics.face('mono'),
            'fsFontSize' : metrics.size('fsEditorBody'),
            'fsLineHeight' : 120,
            'windowedFontFace' : metrics.face('mono'),
            'monospaceFontFace' : metrics.face('mono2'),
            'windowedFontSize' : metrics.size('editorBody'),
            'monospaceFontSize' : metrics.size('editorBody'),
            'flatDesign' : False,
            'storyFrameToolbar' : True,
            'storyPanelSnap' : False,
            'fastStoryPanel' : False,
            'imageArrows' : True,
            'displayArrows' : True,
            'createPassagePrompt' : True,
            'importImagePrompt' : True,
            'passageWarnings' : True
        }.iteritems():
            if not sc.HasEntry(k):
                if type(v) == str:
                    sc.Write(k,v)
                elif type(v) == int:
                    sc.WriteInt(k,v)
                elif type(v) == bool:
                    sc.WriteBool(k,v)

    def applyPrefs(self):
        """Asks all of our stories to update themselves based on a preference change."""
        for story in self.stories:
            story.applyPrefs()

    def displayError(self, activity,stacktrace = True):
        """
        Displays an error dialog with diagnostic info. Call with what you were doing
        when the error occurred (e.g. 'saving your story', 'building your story'.)
        """
        text = 'An error occurred while ' + activity + '.\n\n'
        if stacktrace:
            text += ''.join(traceback.format_exc(5))
        else:
            text += '(' + str(sys.exc_info()[1]) + ').'
        error = wx.MessageDialog(None, text, 'Error', wx.OK | wx.ICON_ERROR)
        error.ShowModal()

    def MacReopenApp(self):
        """OS X support"""
        self.GetTopWindow().Raise()

    def determinePaths(self):
        """Determine the paths to relevant files used by application"""
        scriptPath = os.path.dirname(os.path.realpath(sys.argv[0]))
        if sys.platform == 'win32':
            # Windows py2exe'd apps add an extraneous library.zip at the end
            scriptPath = re.sub('\\\\\w*.zip', '', scriptPath)
        elif sys.platform == "darwin":
            scriptPath = re.sub('MacOS\/.*', '', scriptPath)

        scriptPath += os.sep
        self.iconsPath = scriptPath + 'icons' + os.sep
        self.builtinTargetsPath = scriptPath + 'targets' + os.sep

        if sys.platform == "darwin":
            self.externalTargetsPath = re.sub('[^/]+.app/.*', 'targets' + os.sep, self.builtinTargetsPath)
            if not os.path.isdir(self.externalTargetsPath):
                self.externalTargetsPath = ''
        else:
            self.externalTargetsPath = ''

    def loadTargetHeaders(self):
        """Load the target headers and populate the self.headers dictionary"""
        self.headers = {}
        # Get paths to built-in targets
        paths = [(t, self.builtinTargetsPath + t + os.sep) for t in os.listdir(self.builtinTargetsPath)]
        if self.externalTargetsPath:
            # Get paths to external targets
            paths += [(t, self.externalTargetsPath + t + os.sep) for t in os.listdir(self.externalTargetsPath)]
        # Look in subdirectories only for the header file
        for path in paths:
            try:
                if not os.path.isfile(path[1]) and os.access(path[1] + 'header.html', os.R_OK):
                    header = Header.factory(*path, builtinPath = self.builtinTargetsPath)
                    self.headers[header.id] = header
            except:
                pass


# start things up if we were called directly
if __name__ == "__main__":
    app = App()
    app.MainLoop()
