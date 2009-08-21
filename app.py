#!/usr/bin/env python

#
# App
# This bootstraps our application and keeps track of preferences, etc.
#

import sys, os, locale, re, pickle, wx
from storyframe import StoryFrame
from prefframe import PreferenceFrame

class App (wx.App):

    def __init__ (self, redirect = False):
        """Initializes the application."""
        wx.App.__init__(self, redirect = redirect)
        locale.setlocale(locale.LC_ALL, '')
        self.stories = []
        self.loadPrefs()

        # try to load our app icon under win32
        # if it doesn't work, we continue anyway

        self.icon = wx.EmptyIcon()
        
        if sys.platform == 'win32':
            try:
                self.icon = wx.Icon('icons' + os.sep + 'app.ico', wx.BITMAP_TYPE_ICO)
            except:
                pass
        
        # recent files
        # each of our StoryFrames shares the same menu
        
        self.recentFiles = wx.FileHistory(App.RECENT_FILES)
        self.recentFiles.Load(self.config)
        
        # restore save location

        os.chdir(self.config.Read('savePath'))
                   
        self.newStory()
        
    def newStory (self, event = None):
        """Opens a new, blank story."""
        self.stories.append(StoryFrame(parent = None, app = self))
    
    def removeStory (self, story):
        """Removes a story from our collection. Should be called when it closes."""
        self.stories.remove(story)
        
    def openDialog (self, event = None):
        """Opens a story file of the user's choice."""
        opened = False
        dialog = wx.FileDialog(None, 'Open Story', os.getcwd(), "", "Twine Story (*.tws)|*.tws", \
                               wx.OPEN | wx.FD_CHANGE_DIR)
                                                
        if dialog.ShowModal() == wx.ID_OK:
            opened = True
            self.config.Write('savePath', os.getcwd())
            self.addRecentFile(dialog.GetPath())
            self.open(dialog.GetPath())
                    
        dialog.Destroy()

    def openRecent (self, index):
        """Opens a recently-opened file."""
        self.open(self.recentFiles.GetHistoryFile(index))
    
    def open (self, path):
        """Opens a specific story file."""
        try:            
            openedFile = open(path, 'r')
            self.stories.append(StoryFrame(None, app = self, state = pickle.load(openedFile)))
            self.addRecentFile(path)
            openedFile.close()
            
            # weird special case:
            # if we only had one story opened before
            # and it's pristine (e.g. no changes ever made to it),
            # then we close it after opening the file successfully
            
            if (len(self.stories) == 2) and (self.stories[0].pristine):
                self.stories[0].Destroy()
                
        except:
            self.displayError('opening your story')
        
    def exit (self, event = None):
        """Closes all open stories, implicitly quitting."""
        map(lambda s: s.Close(), self.stories)
        
    def showPrefs (self, event = None):
        """Shows the preferences dialog."""
        if (not hasattr(self, 'prefFrame')):
            self.prefFrame = PreferenceFrame(self)
        else:
            try:
                self.prefFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'prefFrame')
                self.showPrefs(event)           
    
    def addRecentFile (self, path):
        """Adds a path to the recent files history and updates the menus."""
        self.recentFiles.AddFileToHistory(path)
        self.recentFiles.Save(self.config)
    
    def about (self, event = None):
        """Shows the about dialog."""
        info = wx.AboutDialogInfo()
        info.SetName(self.NAME)
        info.SetVersion(self.VERSION)
        info.SetDescription('\nA tool for creating interactive stories\nwritten by Chris Klimas\n\nhttp://gimcrackd.com/etc/src/')
        info.SetCopyright('The Twee compiler and associated JavaScript files in this application are released under the GNU Public License.\n\nThe files in the targets directory are derivative works of Jeremy Ruston\'s TiddlyWiki project and are used under the terms of its license.')
        wx.AboutBox(info)
    
    def storyFormatHelp (self, event = None):
        """Opens the online manual to the section on story formats."""
        wx.LaunchDefaultBrowser('http://gimcrackd.com/etc/doc/#simple,storyformats')
    
    def openDocs (self, event = None):
        """Opens the online manual."""
        wx.LaunchDefaultBrowser('http://gimcrackd.com/etc/doc/')
        
    def openGroup (self, event = None):
        """Opens the Google group."""
        wx.LaunchDefaultBrowser('http://groups.google.com/group/tweecode/')
        
    def reportBug (self, event = None):
        """Opens the online bug report form."""
        wx.LaunchDefaultBrowser('http://code.google.com/p/twee/issues/entry')

    def loadPrefs (self):
        """Loads user preferences into self.config, setting up defaults if none are set."""
        self.config = wx.Config('Twine')
        
        monoFont = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
        
        if not self.config.HasEntry('savePath'):
            self.config.Write('savePath', os.path.expanduser('~'))
        if not self.config.HasEntry('fsTextColor'):
            self.config.Write('fsTextColor', '#afcdff')
        if not self.config.HasEntry('fsBgColor'):
            self.config.Write('fsBgColor', '#100088')
        if not self.config.HasEntry('fsFontFace'):
            self.config.Write('fsFontFace', monoFont.GetFaceName())
        if not self.config.HasEntry('fsFontSize'):
            self.config.WriteInt('fsFontSize', 16)
        if not self.config.HasEntry('windowedFontFace'):
            self.config.Write('windowedFontFace', monoFont.GetFaceName())
        if not self.config.HasEntry('windowedFontSize'):
            self.config.WriteInt('windowedFontSize', 10)
            
    def applyPrefs (self):
        """Asks all of our stories to update themselves based on a preference change."""
        map(lambda s: s.applyPrefs(), self.stories)

    def displayError (self, activity):
        """
        Displays an error dialog with diagnostic info. Call with what you were doing
        when the error occurred (e.g. 'saving your story', 'building your story'.)
        """
        exception = sys.exc_info()
        text = 'An error occurred while ' + activity + ' ('
        text += str(exception[1]) + ').'
        error = wx.MessageDialog(None, text, 'Error', wx.OK | wx.ICON_ERROR)
        error.ShowModal()

    def getPath (self):
        """Returns the path to the executing script or application."""
        scriptPath = os.path.realpath(sys.path[0])
        
        # OS X py2app'd apps will direct us right into the app bundle
        
        scriptPath = re.sub('[^/]+.app/Contents/Resources', '', scriptPath)
        
        # Windows py2exe'd apps add an extraneous library.zip at the end
        
        scriptPath = scriptPath.replace('\\library.zip', '')
        return scriptPath
    
    NAME = 'Twine'
    VERSION = '1.1'
    RECENT_FILES = 5

# start things up if we were called directly

if __name__ == "__main__":
    app = App()
    app.MainLoop()